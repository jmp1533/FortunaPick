from __future__ import annotations

from lottery.analyzer import LotteryAnalyzer
from lottery.engine import DEFAULT_SCORE_CONFIG, normalize_score_config


def deep_merge_score(base, override):
    merged = normalize_score_config(base)
    for key, value in (override or {}).items():
        if key in ['odd_count_scores', 'high_count_scores', 'max_concentration_scores', 'carryover_count_scores', 'bonus_carryover_count_scores', 'frequency_window_weights', 'hot_score_weights']:
            merged[key] = {int(k) if str(k).isdigit() else str(k): int(v) for k, v in value.items()}
        elif key in ['ac_ranges', 'sum_ranges', 'last_seen_weights']:
            merged[key] = [dict(item) for item in value]
        else:
            merged[key] = value
    return normalize_score_config(merged)


_ANALYZER = LotteryAnalyzer()
_CARRYOVER_METRICS = _ANALYZER.get_analysis_results().get('carryover_metrics', {})
_EMPIRICAL_CARRYOVER_SCORES = {
    int(k): int(v)
    for k, v in _CARRYOVER_METRICS.get('carryover_count_score_table', DEFAULT_SCORE_CONFIG['carryover_count_scores']).items()
}
_EMPIRICAL_BONUS_CARRYOVER_SCORES = {
    int(k): int(v)
    for k, v in _CARRYOVER_METRICS.get('bonus_carryover_count_score_table', DEFAULT_SCORE_CONFIG['bonus_carryover_count_scores']).items()
}


SCORE_PRESETS = {
    'baseline_default': deep_merge_score(DEFAULT_SCORE_CONFIG, {}),
    'overdue_light': deep_merge_score(DEFAULT_SCORE_CONFIG, {
        'overdue_weight': 8,
        'frequency_window_weights': {10: 2, 30: 1, 50: 1, 100: 0},
    }),
    'overdue_medium': deep_merge_score(DEFAULT_SCORE_CONFIG, {
        'overdue_weight': 10,
        'frequency_window_weights': {10: 2, 30: 2, 50: 1, 100: 1},
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
        'overdue_weight': 9,
        'carryover_weight': 9,
        'bonus_carryover_weight': 2,
        'frequency_window_weights': {10: 2, 30: 2, 50: 1, 100: 1},
        'last_seen_weights': [
            {'min': 8, 'max': 15, 'score': 2},
            {'min': 16, 'max': 24, 'score': 4},
            {'min': 25, 'max': 99, 'score': 6},
        ],
        'hot_score_weights': {
            'hot': 1,
            'cold': 2,
        },
        'carryover_count_scores': _EMPIRICAL_CARRYOVER_SCORES,
        'bonus_carryover_count_scores': _EMPIRICAL_BONUS_CARRYOVER_SCORES,
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
        'overdue_weight': 9,
        'carryover_weight': 10,
        'bonus_carryover_weight': 3,
        'frequency_window_weights': {10: 3, 30: 2, 50: 1, 100: 1},
        'last_seen_weights': [
            {'min': 8, 'max': 15, 'score': 2},
            {'min': 16, 'max': 24, 'score': 4},
            {'min': 25, 'max': 99, 'score': 7},
        ],
        'hot_score_weights': {
            'hot': 1,
            'cold': 2,
        },
        'carryover_count_scores': _EMPIRICAL_CARRYOVER_SCORES,
        'bonus_carryover_count_scores': _EMPIRICAL_BONUS_CARRYOVER_SCORES,
        'sum_ranges': [
            {'min': 105, 'max': 175, 'score': 25},
            {'min': 95, 'max': 185, 'score': 15},
        ],
    }),
    'conservative_hotcold': deep_merge_score(DEFAULT_SCORE_CONFIG, {
        'overdue_weight': 6,
        'carryover_weight': 8,
        'bonus_carryover_weight': 2,
        'frequency_window_weights': {10: 2, 30: 1, 50: 1, 100: 1},
        'hot_score_weights': {
            'hot': 0,
            'cold': 3,
        },
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
