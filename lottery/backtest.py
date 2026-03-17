from __future__ import annotations

import argparse
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


def evaluate_round(recommendations, target_numbers):
    hit_counts = []
    full_target = set(target_numbers)
    for combo in recommendations:
        hit_counts.append(len(set(combo) & full_target))

    best_hit = max(hit_counts) if hit_counts else 0
    distribution = Counter(hit_counts)
    return {
        'best_hit': best_hit,
        'distribution': dict(sorted(distribution.items())),
        'had_3_plus': any(hit >= 3 for hit in hit_counts),
        'had_4_plus': any(hit >= 4 for hit in hit_counts),
        'had_5_plus': any(hit >= 5 for hit in hit_counts),
        'had_6': any(hit == 6 for hit in hit_counts),
    }


def run_backtest(test_rounds=30, min_ac=5, filters=None, recommend_count=10, seed_base=1000, force_rebuild=False):
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
    milestone_counts = defaultdict(int)

    for idx, target in enumerate(targets, start=1):
        history_before_target = chronological[:len(chronological) - test_rounds + idx - 1]
        overdue_numbers = overdue_numbers_from_draws(list(reversed(history_before_target)), threshold=25)
        recommendations = recommend_from_repository(
            repository,
            overdue_numbers=overdue_numbers,
            count=recommend_count,
            seed=seed_base + target['회차'],
        )
        evaluation = evaluate_round(recommendations, target['winning_numbers'])

        aggregate_hits.update(evaluation['distribution'])
        for key in ['had_3_plus', 'had_4_plus', 'had_5_plus', 'had_6']:
            if evaluation[key]:
                milestone_counts[key] += 1

        summaries.append({
            'round': int(target['회차']),
            'target_numbers': target['winning_numbers'],
            'bonus_number': int(target['bonus_number']),
            'recommendations': [list(combo) for combo in recommendations],
            **evaluation,
        })

    best_hits = [item['best_hit'] for item in summaries]
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
        },
        'summary': {
            'tested_rounds': len(summaries),
            'average_best_hit': round(statistics.mean(best_hits), 4) if best_hits else 0,
            'max_best_hit': max(best_hits) if best_hits else 0,
            'min_best_hit': min(best_hits) if best_hits else 0,
            'rounds_with_3_plus': milestone_counts['had_3_plus'],
            'rounds_with_4_plus': milestone_counts['had_4_plus'],
            'rounds_with_5_plus': milestone_counts['had_5_plus'],
            'rounds_with_6': milestone_counts['had_6'],
            'hit_distribution': {str(k): aggregate_hits[k] for k in sorted(aggregate_hits)},
            'elapsed_seconds': round(time.time() - started, 2),
        },
        'rounds': summaries,
    }
    return result


def main():
    parser = argparse.ArgumentParser(description='Run FortunaPick backtests against historical draws.')
    parser.add_argument('--rounds', type=int, default=30, help='How many most recent rounds to backtest.')
    parser.add_argument('--min-ac', type=int, default=5, help='Minimum AC threshold.')
    parser.add_argument('--recommend-count', type=int, default=10, help='Recommendations per round.')
    parser.add_argument('--seed-base', type=int, default=1000, help='Base seed for deterministic shuffling.')
    parser.add_argument('--force-rebuild', action='store_true', help='Rebuild the valid combination cache.')
    parser.add_argument('--output', default=os.path.join(CURRENT_DIR, 'backtest_report.json'), help='Output JSON path.')
    args = parser.parse_args()

    result = run_backtest(
        test_rounds=args.rounds,
        min_ac=args.min_ac,
        recommend_count=args.recommend_count,
        seed_base=args.seed_base,
        force_rebuild=args.force_rebuild,
    )

    with open(args.output, 'w', encoding='utf-8') as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)

    print(json.dumps(result['summary'], ensure_ascii=False, indent=2))
    print(f"Saved detailed report to: {args.output}")


if __name__ == '__main__':
    main()
