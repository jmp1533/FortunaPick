from __future__ import annotations

import argparse
import itertools
import json
import os
import statistics
import sys
import time
from collections import Counter, defaultdict

CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from lottery.analyzer import LotteryAnalyzer
from lottery.engine import build_or_load_repository, recommend_from_repository, normalize_rules, cache_key_for_rules


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


def build_last_seen(draws):
    last_seen = {num: -1 for num in range(1, 46)}
    for idx, draw in enumerate(draws):
        for num in draw['winning_numbers']:
            if last_seen[num] == -1:
                last_seen[num] = idx
    return last_seen


def overdue_numbers_from_draws(draws, threshold=25):
    last_seen = build_last_seen(draws)
    return {num for num, seen in last_seen.items() if seen >= threshold or seen == -1}


def evaluate_round(recommendations, target_numbers, bonus_number=None):
    hit_counts = []
    full_target = set(target_numbers)
    bonus_hit_counts = []
    detailed_results = []

    for combo in recommendations:
        combo_set = set(combo)
        main_hits = len(combo_set & full_target)
        bonus_hit = bonus_number in combo_set if bonus_number is not None else False
        hit_counts.append(main_hits)
        bonus_hit_counts.append(1 if bonus_hit else 0)
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


def run_backtest(test_rounds=30, min_ac=5, filters=None, recommend_count=10, seed_base=1000, force_rebuild=False, include_filter_impact=False):
    started = time.time()
    rules = normalize_rules(min_ac=min_ac, filters=filters)
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

    summaries = []
    aggregate_hits = Counter()
    aggregate_bonus_hits = Counter()
    baseline_aggregate_hits = Counter()
    baseline_aggregate_bonus_hits = Counter()
    milestone_counts = defaultdict(int)
    baseline_milestone_counts = defaultdict(int)

    for idx, target in enumerate(targets, start=1):
        history_before_target = chronological[:len(chronological) - test_rounds + idx - 1]
        overdue_numbers = overdue_numbers_from_draws(list(reversed(history_before_target)), threshold=25)
        recommendations = recommend_from_repository(
            repository,
            overdue_numbers=overdue_numbers,
            count=recommend_count,
            seed=seed_base + target['회차'],
        )
        baseline_recommendations = top_frequency_baseline(history_before_target, recommend_count=recommend_count)

        evaluation = evaluate_round(recommendations, target['winning_numbers'], target['bonus_number'])
        baseline_evaluation = evaluate_round(baseline_recommendations, target['winning_numbers'], target['bonus_number'])

        aggregate_hits.update(evaluation['distribution'])
        aggregate_bonus_hits.update(evaluation['bonus_distribution'])
        baseline_aggregate_hits.update(baseline_evaluation['distribution'])
        baseline_aggregate_bonus_hits.update(baseline_evaluation['bonus_distribution'])

        for key in ['had_3_plus', 'had_4_plus', 'had_5_plus', 'had_6', 'had_3_plus_bonus', 'had_4_plus_bonus', 'had_5_plus_bonus', 'had_bonus_match']:
            if evaluation[key]:
                milestone_counts[key] += 1
            if baseline_evaluation[key]:
                baseline_milestone_counts[key] += 1

        summaries.append({
            'round': int(target['회차']),
            'target_numbers': target['winning_numbers'],
            'bonus_number': int(target['bonus_number']),
            'recommendations': [list(combo) for combo in recommendations],
            'baseline_recommendations': [list(combo) for combo in baseline_recommendations],
            **evaluation,
            'baseline': baseline_evaluation,
        })

    result = {
        'generatedAt': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'rules': rules,
        'repository': {
            'total_valid_combinations': repository.total_valid,
            'cacheKey': cache_key_for_rules(rules)
        },
        'settings': {
            'test_rounds': test_rounds,
            'recommend_count': recommend_count,
            'seed_base': seed_base,
            'include_filter_impact': include_filter_impact,
        },
        'summary': summarize_backtest_run(
            summaries,
            aggregate_hits,
            aggregate_bonus_hits,
            baseline_aggregate_hits,
            baseline_aggregate_bonus_hits,
            milestone_counts,
            baseline_milestone_counts,
            started,
        ),
        'rounds': summaries,
    }

    if include_filter_impact:
        filter_impact = {}
        base_filters = rules['filters'].copy()
        for filter_key, enabled in base_filters.items():
            if not enabled:
                continue

            test_filters = base_filters.copy()
            test_filters[filter_key] = False
            variant_rules = normalize_rules(min_ac=min_ac, filters=test_filters)
            variant_repository = build_or_load_repository(variant_rules, force_rebuild=force_rebuild)

            variant_summaries = []
            variant_aggregate_hits = Counter()
            variant_aggregate_bonus_hits = Counter()
            variant_baseline_aggregate_hits = Counter()
            variant_baseline_aggregate_bonus_hits = Counter()
            variant_milestone_counts = defaultdict(int)
            variant_baseline_milestone_counts = defaultdict(int)
            variant_started = time.time()

            for idx, target in enumerate(targets, start=1):
                history_before_target = chronological[:len(chronological) - test_rounds + idx - 1]
                overdue_numbers = overdue_numbers_from_draws(list(reversed(history_before_target)), threshold=25)
                variant_recommendations = recommend_from_repository(
                    variant_repository,
                    overdue_numbers=overdue_numbers,
                    count=recommend_count,
                    seed=seed_base + target['회차'],
                )
                baseline_recommendations = top_frequency_baseline(history_before_target, recommend_count=recommend_count)

                variant_evaluation = evaluate_round(variant_recommendations, target['winning_numbers'], target['bonus_number'])
                baseline_evaluation = evaluate_round(baseline_recommendations, target['winning_numbers'], target['bonus_number'])

                variant_aggregate_hits.update(variant_evaluation['distribution'])
                variant_aggregate_bonus_hits.update(variant_evaluation['bonus_distribution'])
                variant_baseline_aggregate_hits.update(baseline_evaluation['distribution'])
                variant_baseline_aggregate_bonus_hits.update(baseline_evaluation['bonus_distribution'])

                for key in ['had_3_plus', 'had_4_plus', 'had_5_plus', 'had_6', 'had_3_plus_bonus', 'had_4_plus_bonus', 'had_5_plus_bonus', 'had_bonus_match']:
                    if variant_evaluation[key]:
                        variant_milestone_counts[key] += 1
                    if baseline_evaluation[key]:
                        variant_baseline_milestone_counts[key] += 1

                variant_summaries.append({
                    'round': int(target['회차']),
                    'best_hit': variant_evaluation['best_hit'],
                    'baseline': baseline_evaluation,
                })

            variant_summary = summarize_backtest_run(
                variant_summaries,
                variant_aggregate_hits,
                variant_aggregate_bonus_hits,
                variant_baseline_aggregate_hits,
                variant_baseline_aggregate_bonus_hits,
                variant_milestone_counts,
                variant_baseline_milestone_counts,
                variant_started,
            )

            filter_impact[filter_key] = {
                'disabled': True,
                'summary': variant_summary,
                'delta_vs_current': {
                    'average_best_hit_delta': round(variant_summary['average_best_hit'] - result['summary']['average_best_hit'], 4),
                    'rounds_with_3_plus_delta': variant_summary['rounds_with_3_plus'] - result['summary']['rounds_with_3_plus'],
                    'rounds_with_4_plus_delta': variant_summary['rounds_with_4_plus'] - result['summary']['rounds_with_4_plus'],
                    'rounds_with_5_plus_delta': variant_summary['rounds_with_5_plus'] - result['summary']['rounds_with_5_plus'],
                    'rounds_with_bonus_match_delta': variant_summary['rounds_with_bonus_match'] - result['summary']['rounds_with_bonus_match'],
                }
            }

        result['filter_impact'] = filter_impact

    return result


def main():
    parser = argparse.ArgumentParser(description='Run FortunaPick backtests against historical draws.')
    parser.add_argument('--rounds', type=int, default=30, help='How many most recent rounds to backtest.')
    parser.add_argument('--min-ac', type=int, default=5, help='Minimum AC threshold.')
    parser.add_argument('--recommend-count', type=int, default=10, help='Recommendations per round.')
    parser.add_argument('--seed-base', type=int, default=1000, help='Base seed for deterministic shuffling.')
    parser.add_argument('--force-rebuild', action='store_true', help='Rebuild the valid combination cache.')
    parser.add_argument('--include-filter-impact', action='store_true', help='Run per-filter impact comparisons by disabling filters one at a time.')
    parser.add_argument('--output', default=os.path.join(CURRENT_DIR, 'backtest_report.json'), help='Output JSON path.')
    args = parser.parse_args()

    result = run_backtest(
        test_rounds=args.rounds,
        min_ac=args.min_ac,
        recommend_count=args.recommend_count,
        seed_base=args.seed_base,
        force_rebuild=args.force_rebuild,
        include_filter_impact=args.include_filter_impact,
    )

    with open(args.output, 'w', encoding='utf-8') as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)

    print(json.dumps(result['summary'], ensure_ascii=False, indent=2))
    print(f"Saved detailed report to: {args.output}")


if __name__ == '__main__':
    main()
