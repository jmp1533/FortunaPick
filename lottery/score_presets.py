from __future__ import annotations

from lottery.engine import DEFAULT_SCORE_CONFIG, normalize_score_config


def deep_merge_score(base, override):
    merged = normalize_score_config(base)
    for key, value in (override or {}).items():
        if key in ['odd_count_scores', 'high_count_scores', 'max_concentration_scores']:
            merged[key] = {int(k): int(v) for k, v in value.items()}
        elif key in ['ac_ranges', 'sum_ranges']:
            merged[key] = [dict(item) for item in value]
        else:
            merged[key] = value
    return normalize_score_config(merged)


SCORE_PRESETS = {
    'baseline_default': deep_merge_score(DEFAULT_SCORE_CONFIG, {}),
    'overdue_light': deep_merge_score(DEFAULT_SCORE_CONFIG, {
        'overdue_weight': 8,
    }),
    'overdue_medium': deep_merge_score(DEFAULT_SCORE_CONFIG, {
        'overdue_weight': 10,
    }),
    'ac_emphasis': deep_merge_score(DEFAULT_SCORE_CONFIG, {
        'overdue_weight': 10,
        'ac_ranges': [
            {'min': 8, 'max': 10, 'score': 40},
            {'min': 7, 'max': 7, 'score': 28},
            {'min': 6, 'max': 6, 'score': 18},
        ],
        'ac_default_score': 3,
    }),
    'balanced_distribution': deep_merge_score(DEFAULT_SCORE_CONFIG, {
        'overdue_weight': 10,
        'carryover_weight': 12,
        'bonus_carryover_weight': 4,
        'odd_count_scores': {
            3: 28,
            4: 24,
            2: 18,
        },
        'high_count_scores': {
            2: 22,
            3: 22,
            4: 18,
        },
        'max_concentration_scores': {
            2: 25,
            3: 12,
        },
    }),
    'sum_relaxed': deep_merge_score(DEFAULT_SCORE_CONFIG, {
        'overdue_weight': 10,
        'carryover_weight': 14,
        'bonus_carryover_weight': 5,
        'sum_ranges': [
            {'min': 105, 'max': 175, 'score': 25},
            {'min': 95, 'max': 185, 'score': 15},
        ],
    }),
    'conservative_hotcold': deep_merge_score(DEFAULT_SCORE_CONFIG, {
        'overdue_weight': 6,
        'ac_ranges': [
            {'min': 8, 'max': 10, 'score': 32},
            {'min': 7, 'max': 7, 'score': 24},
            {'min': 6, 'max': 6, 'score': 14},
        ],
        'odd_count_scores': {
            3: 24,
            4: 22,
            2: 18,
        },
        'high_count_scores': {
            2: 20,
            3: 20,
            4: 16,
        },
    }),
}
