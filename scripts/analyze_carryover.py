from __future__ import annotations

import json
import os
import sys
from collections import Counter

CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from lottery.analyzer import LotteryAnalyzer


def main():
    analyzer = LotteryAnalyzer()
    draws_desc = analyzer.get_all_draws()
    chronological = list(reversed(draws_desc))
    if len(chronological) < 2:
        print(json.dumps({'error': 'not enough draws'}, ensure_ascii=False, indent=2))
        return

    repeat_counter = Counter()
    bonus_aug_counter = Counter()
    rows = []
    for idx in range(1, len(chronological)):
        prev_draw = chronological[idx - 1]
        cur_draw = chronological[idx]
        prev_numbers = set(prev_draw['winning_numbers'])
        cur_numbers = set(cur_draw['winning_numbers'])
        carryover_numbers = sorted(prev_numbers & cur_numbers)
        bonus_carryover_numbers = sorted(({int(prev_draw['bonus_number'])} & cur_numbers) - set(carryover_numbers))
        repeat_counter[len(carryover_numbers)] += 1
        bonus_aug_counter[len((prev_numbers | {int(prev_draw['bonus_number'])}) & cur_numbers)] += 1
        rows.append({
            'round': int(cur_draw['회차']),
            'previous_round': int(prev_draw['회차']),
            'carryover_numbers': carryover_numbers,
            'carryover_count': len(carryover_numbers),
            'bonus_carryover_numbers': bonus_carryover_numbers,
            'bonus_carryover_count': len(bonus_carryover_numbers),
        })

    payload = {
        'draw_count': len(chronological),
        'pair_count': len(rows),
        'repeat_distribution': dict(sorted(repeat_counter.items())),
        'bonus_augmented_repeat_distribution': dict(sorted(bonus_aug_counter.items())),
        'average_repeat_count': round(sum(item['carryover_count'] for item in rows) / len(rows), 4),
        'average_bonus_augmented_repeat_count': round(sum(item['carryover_count'] + item['bonus_carryover_count'] for item in rows) / len(rows), 4),
        'latest': rows[-1],
        'recent_pairs': rows[-10:],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
