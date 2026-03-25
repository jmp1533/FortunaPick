from __future__ import annotations

import argparse
import itertools
import json
import os
import statistics
import sys
import time
from collections import Counter, defaultdict, deque
from typing import Dict, List, Optional

CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from lottery.analyzer import LotteryAnalyzer
from lottery.engine import build_or_load_repository, recommend_from_repository, normalize_rules, cache_key_for_rules, normalize_score_config
from lottery.score_presets import SCORE_PRESETS
from lottery.paths import get_checkpoint_dir, get_report_path
from lottery.top_picks import DEFAULT_EXTRACT_MAX_CARRYOVER

MILESTONE_KEYS = [
    'had_3_plus', 'had_4_plus', 'had_5_plus', 'had_6',
    'had_3_plus_bonus', 'had_4_plus_bonus', 'had_5_plus_bonus', 'had_bonus_match'
]


def top_frequency_baseline(draws, recommend_count=10):
    counter = Counter()
    for draw in draws:
        for num in draw['winning_numbers']:
            counter[num] += 1

    ranked = sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    ordered_numbers = [num for num, _ in ranked]
    pool = ordered_numbers[:12] if len(ordered_numbers) >= 12 else ordered_numbers[:]

    if len(pool) < 6:
        for num in range(1, 46):
            if num not in pool:
                pool.append(num)
            if len(pool) == 6:
                break

    combos = []
    for combo in itertools.combinations(pool, 6):
        combos.append(tuple(sorted(combo)))
        if len(combos) >= recommend_count:
            break
    return combos


class SlidingWindowStats:
    def __init__(self, window_draws=None, window_size=30):
        self.window_size = max(1, int(window_size))
        self.draws = deque(maxlen=self.window_size)
        self.counts = Counter()
        self.last_seen = {num: -1 for num in range(1, 46)}
        if window_draws:
            for draw in window_draws:
                self.append(draw)

    def append(self, draw):
        if len(self.draws) == self.window_size:
            oldest = self.draws.popleft()
            for num in oldest['winning_numbers']:
                self.counts[num] -= 1
                if self.counts[num] <= 0:
                    del self.counts[num]

        self.draws.append(draw)
        for num in draw['winning_numbers']:
            self.counts[num] += 1
        self._rebuild_last_seen()

    def _rebuild_last_seen(self):
        self.last_seen = {num: -1 for num in range(1, 46)}
        reversed_draws = list(reversed(self.draws))
        for idx, draw in enumerate(reversed_draws):
            for num in draw['winning_numbers']:
                if self.last_seen[num] == -1:
                    self.last_seen[num] = idx

    def overdue_numbers(self, threshold=25):
        return {num for num, seen in self.last_seen.items() if seen >= threshold or seen == -1}

    def baseline_recommendations(self, recommend_count=10):
        ranked = sorted(self.counts.items(), key=lambda item: (-item[1], item[0]))
        ordered_numbers = [num for num, _ in ranked]
        pool = ordered_numbers[:12] if len(ordered_numbers) >= 12 else ordered_numbers[:]

        if len(pool) < 6:
            for num in range(1, 46):
                if num not in pool:
                    pool.append(num)
                if len(pool) == 6:
                    break

        combos = []
        for combo in itertools.combinations(pool, 6):
            combos.append(tuple(sorted(combo)))
            if len(combos) >= recommend_count:
                break
        return combos

    def snapshot_draws(self):
        return list(self.draws)


def build_analysis_snapshot(window_draws, previous_draw=None):
    last_seen = {num: -1 for num in range(1, 46)}
    reversed_draws = list(reversed(window_draws))
    for idx, draw in enumerate(reversed_draws):
        for num in draw['winning_numbers']:
            if last_seen[num] == -1:
                last_seen[num] = idx

    frequency_windows = {}
    for window in (10, 30, 50, 100):
        counter = Counter()
        for draw in window_draws[-window:]:
            counter.update(draw['winning_numbers'])
        frequency_windows[str(window)] = {num: int(counter.get(num, 0)) for num in range(1, 46)}

    carryover_numbers = previous_draw['winning_numbers'] if previous_draw else []
    bonus_carryover_numbers = [int(previous_draw['bonus_number'])] if previous_draw else []

    hot_cold_profile = {}
    number_features = {}
    for num in range(1, 46):
        score = (int(frequency_windows['10'].get(num, 0)) * 3) + int(frequency_windows['30'].get(num, 0))
        if score >= 12:
            label = 'hot'
        elif score <= 3:
            label = 'cold'
        else:
            label = 'neutral'
        hot_cold_profile[num] = {'score': score, 'label': label}
        number_features[num] = {
            'number': num,
            'freq_10': int(frequency_windows['10'].get(num, 0)),
            'freq_30': int(frequency_windows['30'].get(num, 0)),
            'freq_50': int(frequency_windows['50'].get(num, 0)),
            'freq_100': int(frequency_windows['100'].get(num, 0)),
            'last_seen': int(last_seen.get(num, -1)),
            'is_carryover': num in carryover_numbers,
            'is_bonus_carryover': num in bonus_carryover_numbers,
            'hot_cold_label': label,
            'hot_score': score,
        }

    return {
        'last_seen_draws_ago': last_seen,
        'number_frequency_windows': frequency_windows,
        'hot_cold_profile': hot_cold_profile,
        'number_features': number_features,
        'carryover_metrics': {
            'latest': {
                'carryover_numbers': carryover_numbers,
                'bonus_carryover_numbers': bonus_carryover_numbers,
            }
        },
    }


def evaluate_round(recommendations, target_numbers, bonus_number=None):
    hit_counts = []
    full_target = set(target_numbers)
    detailed_results = []

    for combo in recommendations:
        combo_set = set(combo)
        main_hits = len(combo_set & full_target)
        bonus_hit = bonus_number in combo_set if bonus_number is not None else False
        hit_counts.append(main_hits)
        detailed_results.append({
            'combo': list(combo),
            'main_hits': main_hits,
            'bonus_hit': bonus_hit,
        })

    best_hit = max(hit_counts) if hit_counts else 0
    distribution = Counter(hit_counts)
    bonus_distribution = Counter()
    for item in detailed_results:
        if item['bonus_hit']:
            bonus_distribution[f"{item['main_hits']}+bonus"] += 1

    return {
        'best_hit': best_hit,
        'distribution': dict(sorted(distribution.items())),
        'bonus_distribution': dict(sorted(bonus_distribution.items())),
        'had_3_plus': any(hit >= 3 for hit in hit_counts),
        'had_4_plus': any(hit >= 4 for hit in hit_counts),
        'had_5_plus': any(hit >= 5 for hit in hit_counts),
        'had_6': any(hit == 6 for hit in hit_counts),
        'had_3_plus_bonus': any(item['main_hits'] >= 3 and item['bonus_hit'] for item in detailed_results),
        'had_4_plus_bonus': any(item['main_hits'] >= 4 and item['bonus_hit'] for item in detailed_results),
        'had_5_plus_bonus': any(item['main_hits'] >= 5 and item['bonus_hit'] for item in detailed_results),
        'had_bonus_match': any(item['bonus_hit'] for item in detailed_results),
    }


def summarize_backtest_run(summaries, aggregate_hits, aggregate_bonus_hits, baseline_aggregate_hits, baseline_aggregate_bonus_hits, milestone_counts, baseline_milestone_counts, started):
    best_hits = [item['best_hit'] for item in summaries]
    baseline_best_hits = [item['baseline']['best_hit'] for item in summaries]
    return {
        'tested_rounds': len(summaries),
        'average_best_hit': round(statistics.mean(best_hits), 4) if best_hits else 0,
        'max_best_hit': max(best_hits) if best_hits else 0,
        'min_best_hit': min(best_hits) if best_hits else 0,
        'rounds_with_3_plus': milestone_counts['had_3_plus'],
        'rounds_with_4_plus': milestone_counts['had_4_plus'],
        'rounds_with_5_plus': milestone_counts['had_5_plus'],
        'rounds_with_6': milestone_counts['had_6'],
        'rounds_with_bonus_match': milestone_counts['had_bonus_match'],
        'rounds_with_3_plus_bonus': milestone_counts['had_3_plus_bonus'],
        'rounds_with_4_plus_bonus': milestone_counts['had_4_plus_bonus'],
        'rounds_with_5_plus_bonus': milestone_counts['had_5_plus_bonus'],
        'hit_distribution': {str(k): aggregate_hits[k] for k in sorted(aggregate_hits)},
        'bonus_hit_distribution': {str(k): aggregate_bonus_hits[k] for k in sorted(aggregate_bonus_hits)},
        'baseline': {
            'strategy': 'top_frequency',
            'average_best_hit': round(statistics.mean(baseline_best_hits), 4) if baseline_best_hits else 0,
            'max_best_hit': max(baseline_best_hits) if baseline_best_hits else 0,
            'min_best_hit': min(baseline_best_hits) if baseline_best_hits else 0,
            'rounds_with_3_plus': baseline_milestone_counts['had_3_plus'],
            'rounds_with_4_plus': baseline_milestone_counts['had_4_plus'],
            'rounds_with_5_plus': baseline_milestone_counts['had_5_plus'],
            'rounds_with_6': baseline_milestone_counts['had_6'],
            'rounds_with_bonus_match': baseline_milestone_counts['had_bonus_match'],
            'rounds_with_3_plus_bonus': baseline_milestone_counts['had_3_plus_bonus'],
            'rounds_with_4_plus_bonus': baseline_milestone_counts['had_4_plus_bonus'],
            'rounds_with_5_plus_bonus': baseline_milestone_counts['had_5_plus_bonus'],
            'hit_distribution': {str(k): baseline_aggregate_hits[k] for k in sorted(baseline_aggregate_hits)},
            'bonus_hit_distribution': {str(k): baseline_aggregate_bonus_hits[k] for k in sorted(baseline_aggregate_bonus_hits)},
        },
        'comparison': {
            'average_best_hit_delta': round((statistics.mean(best_hits) - statistics.mean(baseline_best_hits)), 4) if best_hits and baseline_best_hits else 0,
            'rounds_with_3_plus_delta': milestone_counts['had_3_plus'] - baseline_milestone_counts['had_3_plus'],
            'rounds_with_4_plus_delta': milestone_counts['had_4_plus'] - baseline_milestone_counts['had_4_plus'],
            'rounds_with_5_plus_delta': milestone_counts['had_5_plus'] - baseline_milestone_counts['had_5_plus'],
            'rounds_with_bonus_match_delta': milestone_counts['had_bonus_match'] - baseline_milestone_counts['had_bonus_match'],
        },
        'elapsed_seconds': round(time.time() - started, 2),
    }


def _normalize_main_hit_distribution(mapping):
    normalized = Counter()
    for key, value in (mapping or {}).items():
        normalized[int(key)] += int(value)
    return normalized


def _normalize_bonus_hit_distribution(mapping):
    normalized = Counter()
    for key, value in (mapping or {}).items():
        normalized[str(key)] += int(value)
    return normalized


def update_aggregates(evaluation, aggregate_hits, aggregate_bonus_hits, milestone_counts):
    aggregate_hits.update(_normalize_main_hit_distribution(evaluation.get('distribution', {})))
    aggregate_bonus_hits.update(_normalize_bonus_hit_distribution(evaluation.get('bonus_distribution', {})))
    for key in MILESTONE_KEYS:
        if evaluation[key]:
            milestone_counts[key] += 1


def load_checkpoint(path: Optional[str]):
    if not path or not os.path.exists(path):
        return None
    with open(path, encoding='utf-8') as fh:
        payload = json.load(fh)

    def _normalize_counter_map(mapping):
        normalized = {}
        for key, value in mapping.items():
            try:
                normalized[int(key)] = value
            except (ValueError, TypeError):
                normalized[str(key)] = value
        return normalized

    for field in ['aggregate_hits', 'baseline_aggregate_hits']:
        if field in payload:
            payload[field] = _normalize_counter_map(payload[field])
    for field in ['aggregate_bonus_hits', 'baseline_aggregate_bonus_hits']:
        if field in payload:
            payload[field] = {str(k): v for k, v in payload[field].items()}
    return payload


def save_checkpoint(path: Optional[str], payload: Dict):
    if not path:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_path = f"{path}.tmp"
    with open(tmp_path, 'w', encoding='utf-8') as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)


def recalculate_summary_from_rounds(summaries):
    aggregate_hits = Counter()
    aggregate_bonus_hits = Counter()
    baseline_aggregate_hits = Counter()
    baseline_aggregate_bonus_hits = Counter()
    milestone_counts = defaultdict(int)
    baseline_milestone_counts = defaultdict(int)

    for item in summaries:
        update_aggregates(item, aggregate_hits, aggregate_bonus_hits, milestone_counts)
        update_aggregates(item['baseline'], baseline_aggregate_hits, baseline_aggregate_bonus_hits, baseline_milestone_counts)

    started = time.time()
    return summarize_backtest_run(
        summaries,
        aggregate_hits,
        aggregate_bonus_hits,
        baseline_aggregate_hits,
        baseline_aggregate_bonus_hits,
        milestone_counts,
        baseline_milestone_counts,
        started,
    )


def execute_backtest_pass(repository, chronological, targets, recommend_count, seed_base, recent_window, checkpoint_path=None, variant_label='main'):
    started = time.time()
    summaries = []
    aggregate_hits = Counter()
    aggregate_bonus_hits = Counter()
    baseline_aggregate_hits = Counter()
    baseline_aggregate_bonus_hits = Counter()
    milestone_counts = defaultdict(int)
    baseline_milestone_counts = defaultdict(int)

    checkpoint = load_checkpoint(checkpoint_path)
    start_index = 0
    if checkpoint and checkpoint.get('variant_label') == variant_label and checkpoint.get('recent_window') == recent_window:
        start_index = checkpoint.get('next_index', 0)
        summaries = checkpoint.get('summaries', [])
        aggregate_hits.update(checkpoint.get('aggregate_hits', {}))
        aggregate_bonus_hits.update(checkpoint.get('aggregate_bonus_hits', {}))
        baseline_aggregate_hits.update(checkpoint.get('baseline_aggregate_hits', {}))
        baseline_aggregate_bonus_hits.update(checkpoint.get('baseline_aggregate_bonus_hits', {}))
        milestone_counts.update(checkpoint.get('milestone_counts', {}))
        baseline_milestone_counts.update(checkpoint.get('baseline_milestone_counts', {}))

    target_start = len(chronological) - len(targets)
    if start_index > len(targets):
        start_index = 0

    initial_history_end = target_start + start_index
    initial_window_start = max(0, initial_history_end - recent_window)
    initial_window_draws = chronological[initial_window_start:initial_history_end]
    window_stats = SlidingWindowStats(initial_window_draws, window_size=recent_window)

    for relative_idx in range(start_index, len(targets)):
        target = targets[relative_idx]
        overdue_numbers = window_stats.overdue_numbers(threshold=25)
        previous_draw = chronological[target_start + relative_idx - 1] if (target_start + relative_idx - 1) >= 0 else None
        carryover_numbers = set(previous_draw['winning_numbers']) if previous_draw else set()
        bonus_carryover_numbers = {int(previous_draw['bonus_number'])} if previous_draw else set()
        analysis_snapshot = build_analysis_snapshot(window_stats.snapshot_draws(), previous_draw=previous_draw)
        recommendations = recommend_from_repository(
            repository,
            overdue_numbers=overdue_numbers,
            carryover_numbers=carryover_numbers,
            bonus_carryover_numbers=bonus_carryover_numbers,
            analysis=analysis_snapshot,
            count=recommend_count,
            seed=seed_base + target['회차'],
            max_carryover_count=DEFAULT_EXTRACT_MAX_CARRYOVER,
        )
        baseline_recommendations = window_stats.baseline_recommendations(recommend_count=recommend_count)

        evaluation = evaluate_round(recommendations, target['winning_numbers'], target['bonus_number'])
        baseline_evaluation = evaluate_round(baseline_recommendations, target['winning_numbers'], target['bonus_number'])

        update_aggregates(evaluation, aggregate_hits, aggregate_bonus_hits, milestone_counts)
        update_aggregates(baseline_evaluation, baseline_aggregate_hits, baseline_aggregate_bonus_hits, baseline_milestone_counts)

        summaries.append({
            'round': int(target['회차']),
            'target_numbers': target['winning_numbers'],
            'bonus_number': int(target['bonus_number']),
            'carryover_source_numbers': sorted(carryover_numbers),
            'bonus_carryover_source_numbers': sorted(bonus_carryover_numbers),
            'recommendations': [list(combo) for combo in recommendations],
            'baseline_recommendations': [list(combo) for combo in baseline_recommendations],
            **evaluation,
            'baseline': baseline_evaluation,
        })

        save_checkpoint(checkpoint_path, {
            'variant_label': variant_label,
            'recent_window': recent_window,
            'next_index': relative_idx + 1,
            'summaries': summaries,
            'aggregate_hits': dict(aggregate_hits),
            'aggregate_bonus_hits': dict(aggregate_bonus_hits),
            'baseline_aggregate_hits': dict(baseline_aggregate_hits),
            'baseline_aggregate_bonus_hits': dict(baseline_aggregate_bonus_hits),
            'milestone_counts': dict(milestone_counts),
            'baseline_milestone_counts': dict(baseline_milestone_counts),
        })

        if target_start + relative_idx < len(chronological):
            window_stats.append(chronological[target_start + relative_idx])

    return {
        'summaries': summaries,
        'summary': summarize_backtest_run(
            summaries,
            aggregate_hits,
            aggregate_bonus_hits,
            baseline_aggregate_hits,
            baseline_aggregate_bonus_hits,
            milestone_counts,
            baseline_milestone_counts,
            started,
        )
    }


def run_filter_impact(rules, chronological, targets, recommend_count, seed_base, recent_window, force_rebuild=False, checkpoint_dir=None):
    filter_impact = {}
    base_filters = rules['filters'].copy()
    for filter_key, enabled in base_filters.items():
        if not enabled:
            continue
        test_filters = base_filters.copy()
        test_filters[filter_key] = False
        variant_rules = normalize_rules(min_ac=rules['min_ac'], filters=test_filters)
        variant_repository = build_or_load_repository(variant_rules, force_rebuild=force_rebuild)
        checkpoint_path = None
        if checkpoint_dir:
            os.makedirs(checkpoint_dir, exist_ok=True)
            checkpoint_path = os.path.join(checkpoint_dir, f'filter-impact-{filter_key}.json')
        variant_result = execute_backtest_pass(
            variant_repository,
            chronological,
            targets,
            recommend_count,
            seed_base,
            recent_window,
            checkpoint_path=checkpoint_path,
            variant_label=f'filter-impact-{filter_key}',
        )
        filter_impact[filter_key] = {
            'disabled': True,
            'summary': variant_result['summary'],
        }
    return filter_impact


def update_backtest_report_incrementally(report_path, min_ac=5, filters=None, recommend_count=10, seed_base=1000, recent_window=30, score_config=None):
    analyzer = LotteryAnalyzer()
    if analyzer.df.empty:
        raise RuntimeError('No lottery data available for incremental update.')

    latest_round = analyzer.get_latest_round_number()
    all_draws_desc = analyzer.get_all_draws()
    chronological = list(reversed(all_draws_desc))

    existing = None
    if os.path.exists(report_path):
        with open(report_path, encoding='utf-8') as fh:
            existing = json.load(fh)

    if not existing:
        initial_rounds = min(100, max(1, len(chronological) - 1))
        generated = run_backtest(
            test_rounds=initial_rounds,
            min_ac=min_ac,
            filters=filters,
            recommend_count=recommend_count,
            seed_base=seed_base,
            force_rebuild=False,
            include_filter_impact=False,
            recent_window=recent_window,
            checkpoint_dir=None,
            mode='main-only',
            score_config=score_config,
            run_label='initial-generate',
        )
        with open(report_path, 'w', encoding='utf-8') as fh:
            json.dump(generated, fh, ensure_ascii=False, indent=2)
        return {
            'status': 'initialized',
            'latest_round': latest_round,
            'missing_rounds': [],
            'applied_rounds': [int(item['round']) for item in generated.get('rounds', [])],
            'report': generated,
        }

    existing_rounds = existing.get('rounds', [])
    existing_round_numbers = {int(item['round']) for item in existing_rounds}
    existing_latest_round = max(existing_round_numbers) if existing_round_numbers else None
    available_round_numbers = sorted(int(item['회차']) for item in all_draws_desc)

    if existing_latest_round is None:
        missing_rounds = available_round_numbers
    else:
        missing_rounds = [round_no for round_no in available_round_numbers if round_no > existing_latest_round]

    if not missing_rounds:
        return {
            'status': 'up_to_date',
            'latest_round': latest_round,
            'existing_latest_round': existing_latest_round,
            'missing_rounds': [],
            'report': existing,
        }

    rules = normalize_rules(min_ac=min_ac, filters=filters, score_config=score_config)
    repository = build_or_load_repository(rules, force_rebuild=False)

    new_round_entries = []
    for target_round in sorted(missing_rounds):
        target_index = next((idx for idx, draw in enumerate(chronological) if int(draw['회차']) == target_round), None)
        if target_index is None or target_index == 0:
            continue

        history_before_target = chronological[:target_index]
        window_draws = history_before_target[-recent_window:]
        window_stats = SlidingWindowStats(window_draws, window_size=recent_window)
        target = chronological[target_index]

        overdue_numbers = window_stats.overdue_numbers(threshold=25)
        previous_draw = chronological[target_index - 1] if target_index > 0 else None
        carryover_numbers = set(previous_draw['winning_numbers']) if previous_draw else set()
        bonus_carryover_numbers = {int(previous_draw['bonus_number'])} if previous_draw else set()
        analysis_snapshot = build_analysis_snapshot(window_stats.snapshot_draws(), previous_draw=previous_draw)
        recommendations = recommend_from_repository(
            repository,
            overdue_numbers=overdue_numbers,
            carryover_numbers=carryover_numbers,
            bonus_carryover_numbers=bonus_carryover_numbers,
            analysis=analysis_snapshot,
            count=recommend_count,
            seed=seed_base + target_round,
            max_carryover_count=DEFAULT_EXTRACT_MAX_CARRYOVER,
        )
        baseline_recommendations = window_stats.baseline_recommendations(recommend_count=recommend_count)
        evaluation = evaluate_round(recommendations, target['winning_numbers'], target['bonus_number'])
        baseline_evaluation = evaluate_round(baseline_recommendations, target['winning_numbers'], target['bonus_number'])

        new_round_entries.append({
            'round': int(target['회차']),
            'target_numbers': target['winning_numbers'],
            'bonus_number': int(target['bonus_number']),
            'carryover_source_numbers': sorted(carryover_numbers),
            'bonus_carryover_source_numbers': sorted(bonus_carryover_numbers),
            'recommendations': [list(combo) for combo in recommendations],
            'baseline_recommendations': [list(combo) for combo in baseline_recommendations],
            **evaluation,
            'baseline': baseline_evaluation,
        })

    combined_rounds = existing_rounds + new_round_entries
    combined_rounds.sort(key=lambda item: int(item['round']))

    existing['generatedAt'] = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    existing['rules'] = rules
    existing['score_config'] = rules.get('score_config')
    existing['repository'] = {
        'total_valid_combinations': repository.total_valid,
        'cacheKey': cache_key_for_rules(rules)
    }
    existing.setdefault('settings', {})
    existing['settings']['recent_window'] = recent_window
    existing['settings']['recommend_count'] = recommend_count
    existing['settings']['seed_base'] = seed_base
    existing['settings']['incremental_update'] = True
    existing['settings']['latest_excel_round'] = latest_round
    existing['rounds'] = combined_rounds
    existing['summary'] = recalculate_summary_from_rounds(combined_rounds)
    existing['incremental_update'] = {
        'applied_rounds': [int(item['round']) for item in new_round_entries],
        'latest_round': latest_round,
        'existing_round_count': len(existing_rounds),
        'updated_round_count': len(combined_rounds),
    }

    with open(report_path, 'w', encoding='utf-8') as fh:
        json.dump(existing, fh, ensure_ascii=False, indent=2)

    return {
        'status': 'updated',
        'latest_round': latest_round,
        'existing_latest_round': existing_latest_round,
        'missing_rounds': missing_rounds,
        'applied_rounds': [int(item['round']) for item in new_round_entries],
        'report': existing,
    }


def run_backtest(test_rounds=30, min_ac=5, filters=None, recommend_count=10, seed_base=1000, force_rebuild=False, include_filter_impact=False, recent_window=30, checkpoint_dir=None, mode='full', score_config=None, run_label='main'):
    started = time.time()
    rules = normalize_rules(min_ac=min_ac, filters=filters, score_config=score_config)
    repository = build_or_load_repository(rules, force_rebuild=force_rebuild)

    analyzer = LotteryAnalyzer()
    if analyzer.df.empty:
        raise RuntimeError('No lottery data available for backtest.')

    records = analyzer.get_latest_draws(count=len(analyzer.df))
    chronological = list(reversed(records))
    if len(chronological) < 2:
        raise RuntimeError('Not enough history for backtest.')

    available_tests = len(chronological) - 1
    test_rounds = min(test_rounds, available_tests)
    targets = chronological[-test_rounds:]

    result = {
        'generatedAt': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'rules': rules,
        'score_config': rules.get('score_config'),
        'repository': {
            'total_valid_combinations': repository.total_valid,
            'cacheKey': cache_key_for_rules(rules)
        },
        'settings': {
            'test_rounds': test_rounds,
            'recommend_count': recommend_count,
            'seed_base': seed_base,
            'include_filter_impact': include_filter_impact,
            'recent_window': recent_window,
            'checkpoint_dir': checkpoint_dir,
            'mode': mode,
            'run_label': run_label,
        },
    }

    main_result = None
    if mode in ('full', 'main-only', 'filter-impact-only'):
        main_checkpoint = os.path.join(checkpoint_dir, f'{run_label}.json') if checkpoint_dir else None
        main_result = execute_backtest_pass(
            repository,
            chronological,
            targets,
            recommend_count,
            seed_base,
            recent_window,
            checkpoint_path=main_checkpoint,
            variant_label=run_label,
        )
        result['summary'] = main_result['summary']
        result['rounds'] = main_result['summaries']

    if include_filter_impact and mode in ('full', 'filter-impact-only'):
        filter_impact = run_filter_impact(
            rules,
            chronological,
            targets,
            recommend_count,
            seed_base,
            recent_window,
            force_rebuild=force_rebuild,
            checkpoint_dir=checkpoint_dir,
        )
        if main_result is not None:
            for filter_key, payload in filter_impact.items():
                payload['delta_vs_current'] = {
                    'average_best_hit_delta': round(payload['summary']['average_best_hit'] - result['summary']['average_best_hit'], 4),
                    'rounds_with_3_plus_delta': payload['summary']['rounds_with_3_plus'] - result['summary']['rounds_with_3_plus'],
                    'rounds_with_4_plus_delta': payload['summary']['rounds_with_4_plus'] - result['summary']['rounds_with_4_plus'],
                    'rounds_with_5_plus_delta': payload['summary']['rounds_with_5_plus'] - result['summary']['rounds_with_5_plus'],
                    'rounds_with_bonus_match_delta': payload['summary']['rounds_with_bonus_match'] - result['summary']['rounds_with_bonus_match'],
                }
        result['filter_impact'] = filter_impact

    result['total_elapsed_seconds'] = round(time.time() - started, 2)
    return result


def main():
    parser = argparse.ArgumentParser(description='Run FortunaPick backtests against historical draws.')
    parser.add_argument('--rounds', type=int, default=30, help='How many most recent rounds to backtest.')
    parser.add_argument('--recent-window', type=int, default=30, help='How many prior draws to use per target round.')
    parser.add_argument('--min-ac', type=int, default=5, help='Minimum AC threshold.')
    parser.add_argument('--recommend-count', type=int, default=10, help='Recommendations per round.')
    parser.add_argument('--seed-base', type=int, default=1000, help='Base seed for deterministic shuffling.')
    parser.add_argument('--force-rebuild', action='store_true', help='Rebuild the valid combination cache.')
    parser.add_argument('--include-filter-impact', action='store_true', help='Run per-filter impact comparisons by disabling filters one at a time.')
    parser.add_argument('--mode', choices=['full', 'main-only', 'filter-impact-only'], default='full', help='Run main backtest only, filter impact only, or both.')
    parser.add_argument('--checkpoint-dir', default=get_checkpoint_dir(), help='Directory for resumable checkpoint files.')
    parser.add_argument('--run-label', default='main', help='Unique label for checkpoint isolation per run.')
    parser.add_argument('--score-preset', default=None, choices=sorted(SCORE_PRESETS.keys()), help='Named score preset to use.')
    parser.add_argument('--score-config-json', default=None, help='Inline JSON string for score_config overrides.')
    parser.add_argument('--output', default=get_report_path('backtest_report.json'), help='Output JSON path.')
    parser.add_argument('--incremental-update', action='store_true', help='Append only newly detected rounds to an existing backtest report.')
    args = parser.parse_args()

    score_config = None
    if args.score_preset:
        score_config = normalize_score_config(SCORE_PRESETS[args.score_preset])
    if args.score_config_json:
        inline_override = normalize_score_config(json.loads(args.score_config_json))
        score_config = normalize_score_config(inline_override if score_config is None else {**score_config, **inline_override})

    run_label = args.run_label or 'main'
    if run_label == 'main':
        if args.score_preset:
            run_label = f'compare-{args.score_preset}'
        elif score_config is not None:
            run_label = 'custom-score-config'

    if args.incremental_update:
        result = update_backtest_report_incrementally(
            report_path=args.output,
            min_ac=args.min_ac,
            filters=None,
            recommend_count=args.recommend_count,
            seed_base=args.seed_base,
            recent_window=args.recent_window,
            score_config=score_config,
        )
        print(json.dumps({
            'status': result['status'],
            'latest_round': result.get('latest_round'),
            'missing_rounds': result.get('missing_rounds', []),
            'applied_rounds': result.get('applied_rounds', []),
        }, ensure_ascii=False, indent=2))
        print(f"Updated report: {args.output}")
        return

    result = run_backtest(
        test_rounds=args.rounds,
        recent_window=args.recent_window,
        min_ac=args.min_ac,
        recommend_count=args.recommend_count,
        seed_base=args.seed_base,
        force_rebuild=args.force_rebuild,
        include_filter_impact=args.include_filter_impact,
        checkpoint_dir=args.checkpoint_dir,
        mode=args.mode,
        score_config=score_config,
        run_label=run_label,
    )

    with open(args.output, 'w', encoding='utf-8') as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)

    print(json.dumps(result['summary'], ensure_ascii=False, indent=2))
    print(f"Saved detailed report to: {args.output}")


if __name__ == '__main__':
    main()
