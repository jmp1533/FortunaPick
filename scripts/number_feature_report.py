from __future__ import annotations

import json
import os
import sys

CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.abspath(os.path.join(CURRENT_DIR, '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from lottery.analyzer import LotteryAnalyzer
from lottery.top_picks import get_current_draw_context


def main():
    analyzer = LotteryAnalyzer()
    context = get_current_draw_context(analyzer)
    analysis = context['analysis']
    features = analysis.get('number_features', {})

    ranked = sorted(
        features.values(),
        key=lambda item: (
            item['is_carryover'],
            item['is_bonus_carryover'],
            item['freq_10'],
            item['freq_30'],
            -item['last_seen'],
            item['number'],
        ),
        reverse=True,
    )

    payload = {
        'latestRound': analyzer.get_latest_round_number(),
        'carryover_numbers': sorted(context['carryover_numbers']),
        'bonus_carryover_numbers': sorted(context['bonus_carryover_numbers']),
        'top15': ranked[:15],
        'cold15': sorted(features.values(), key=lambda item: (item['last_seen'], item['freq_10'], item['freq_30'], -item['number']))[-15:],
        'all': [features[num] for num in range(1, 46)],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
