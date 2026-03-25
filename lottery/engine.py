"""Shared combination engine for FortunaPick.

This module centralizes the filtering, scoring, recommendation, and
backtesting primitives so the API and offline scripts use the same rules.
"""

from __future__ import annotations

import itertools
import math
import os
import pickle
import random
import json
import hashlib
from array import array
from collections import Counter
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Set, Tuple

from lottery.paths import get_cache_dir

DEFAULT_FILTERS = {
    'f1': True,
    'f2': True,
    'f3': True,
    'f4': True,
    'f5': True,
    'f6': True,
    'f7': True,
    'f8': True,
}

DEFAULT_SCORE_CONFIG = {
    'overdue_weight': 15,
    'carryover_weight': 12,
    'bonus_carryover_weight': 4,
    'frequency_window_weights': {
        10: 3,
        30: 2,
        50: 1,
        100: 1,
    },
    'last_seen_weights': [
        {'min': 8, 'max': 15, 'score': 2},
        {'min': 16, 'max': 24, 'score': 5},
        {'min': 25, 'max': 99, 'score': 8},
    ],
    'last_seen_default_score': 0,
    'hot_score_weights': {
        'hot': 1,
        'cold': 2,
    },
    'carryover_count_scores': {
        1: 12,
        2: 18,
        3: -6,
        4: -18,
        5: -32,
        6: -48,
    },
    'carryover_default_score': 0,
    'bonus_carryover_count_scores': {
        1: 4,
    },
    'bonus_carryover_default_score': 0,
    'ac_ranges': [
        {'min': 8, 'max': 10, 'score': 30},
        {'min': 7, 'max': 7, 'score': 25},
        {'min': 6, 'max': 6, 'score': 15},
    ],
    'ac_default_score': 5,
    'odd_count_scores': {
        3: 25,
        4: 25,
        2: 20,
    },
    'odd_default_score': 5,
    'high_count_scores': {
        2: 20,
        3: 20,
        4: 20,
    },
    'high_default_score': 5,
    'sum_ranges': [
        {'min': 110, 'max': 170, 'score': 25},
        {'min': 100, 'max': 180, 'score': 15},
    ],
    'sum_default_score': 5,
    'max_concentration_scores': {
        2: 20,
        3: 10,
    },
    'concentration_default_score': 0,
}

CACHE_DIR = get_cache_dir()


@dataclass
class ComboRepository:
    masks: array
    static_scores: array
    total_valid: int
    rules: Dict

    def iter_entries(self):
        for idx in range(self.total_valid):
            yield self.masks[idx], self.static_scores[idx]


def normalize_filters(filters: Dict | None) -> Dict[str, bool]:
    merged = DEFAULT_FILTERS.copy()
    if filters:
        merged.update(filters)
    return merged


def normalize_score_config(score_config: Dict | None = None) -> Dict:
    merged = {
        'overdue_weight': DEFAULT_SCORE_CONFIG['overdue_weight'],
        'carryover_weight': DEFAULT_SCORE_CONFIG['carryover_weight'],
        'bonus_carryover_weight': DEFAULT_SCORE_CONFIG['bonus_carryover_weight'],
        'frequency_window_weights': dict(DEFAULT_SCORE_CONFIG['frequency_window_weights']),
        'last_seen_weights': [dict(item) for item in DEFAULT_SCORE_CONFIG['last_seen_weights']],
        'last_seen_default_score': DEFAULT_SCORE_CONFIG['last_seen_default_score'],
        'hot_score_weights': dict(DEFAULT_SCORE_CONFIG['hot_score_weights']),
        'carryover_count_scores': dict(DEFAULT_SCORE_CONFIG['carryover_count_scores']),
        'carryover_default_score': DEFAULT_SCORE_CONFIG['carryover_default_score'],
        'bonus_carryover_count_scores': dict(DEFAULT_SCORE_CONFIG['bonus_carryover_count_scores']),
        'bonus_carryover_default_score': DEFAULT_SCORE_CONFIG['bonus_carryover_default_score'],
        'ac_ranges': [dict(item) for item in DEFAULT_SCORE_CONFIG['ac_ranges']],
        'ac_default_score': DEFAULT_SCORE_CONFIG['ac_default_score'],
        'odd_count_scores': dict(DEFAULT_SCORE_CONFIG['odd_count_scores']),
        'odd_default_score': DEFAULT_SCORE_CONFIG['odd_default_score'],
        'high_count_scores': dict(DEFAULT_SCORE_CONFIG['high_count_scores']),
        'high_default_score': DEFAULT_SCORE_CONFIG['high_default_score'],
        'sum_ranges': [dict(item) for item in DEFAULT_SCORE_CONFIG['sum_ranges']],
        'sum_default_score': DEFAULT_SCORE_CONFIG['sum_default_score'],
        'max_concentration_scores': dict(DEFAULT_SCORE_CONFIG['max_concentration_scores']),
        'concentration_default_score': DEFAULT_SCORE_CONFIG['concentration_default_score'],
    }
    if not score_config:
        return merged

    for key, value in score_config.items():
        if key in ['odd_count_scores', 'high_count_scores', 'max_concentration_scores', 'carryover_count_scores', 'bonus_carryover_count_scores', 'frequency_window_weights', 'hot_score_weights']:
            merged[key] = {int(k) if str(k).isdigit() else str(k): int(v) for k, v in value.items()}
        elif key in ['ac_ranges', 'sum_ranges', 'last_seen_weights']:
            merged[key] = [dict(item) for item in value]
        else:
            merged[key] = value
    return merged


def normalize_rules(min_ac: int = 5, filters: Dict | None = None, score_config: Dict | None = None) -> Dict:
    min_ac = max(0, min(10, int(min_ac)))
    return {
        'min_ac': min_ac,
        'filters': normalize_filters(filters),
        'score_config': normalize_score_config(score_config),
    }


def json_signature(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(',', ':'))


def combo_to_mask(numbers: Sequence[int]) -> int:
    mask = 0
    for n in numbers:
        mask |= 1 << (n - 1)
    return mask


def mask_to_combo(mask: int) -> Tuple[int, ...]:
    return tuple(i + 1 for i in range(45) if mask & (1 << i))


def calculate_ac(numbers: Sequence[int]) -> int:
    nums = sorted(numbers)
    diffs = set()
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            diffs.add(nums[j] - nums[i])
    return len(diffs) - 5


def get_sum(numbers: Sequence[int]) -> int:
    return sum(numbers)


def get_odd_count(numbers: Sequence[int]) -> int:
    return sum(1 for n in numbers if n % 2 != 0)


def get_high_count(numbers: Sequence[int]) -> int:
    return sum(1 for n in numbers if n >= 23)


def check_consecutive(numbers: Sequence[int], count: int = 3) -> bool:
    sorted_nums = sorted(numbers)
    consecutive = 1
    for i in range(1, len(sorted_nums)):
        if sorted_nums[i] == sorted_nums[i - 1] + 1:
            consecutive += 1
            if consecutive >= count:
                return True
        else:
            consecutive = 1
    return False


def check_same_ending(numbers: Sequence[int], count: int = 4) -> bool:
    endings = [n % 10 for n in numbers]
    counter = Counter(endings)
    return any(c >= count for c in counter.values())


def check_row_concentration(numbers: Sequence[int], count: int = 4) -> bool:
    rows = [(n - 1) // 7 for n in numbers]
    counter = Counter(rows)
    return any(c >= count for c in counter.values())


def check_column_concentration(numbers: Sequence[int], count: int = 4) -> bool:
    cols = [(n - 1) % 7 for n in numbers]
    counter = Counter(cols)
    return any(c >= count for c in counter.values())


def check_filters(combo: Sequence[int], rules: Dict) -> bool:
    filters = normalize_filters(rules.get('filters'))

    if filters.get('f1', True) and sum(1 for n in combo if n <= 9) >= 3:
        return False
    if filters.get('f2', True) and check_consecutive(combo, 3):
        return False
    if filters.get('f3', True) and check_same_ending(combo, 4):
        return False
    if filters.get('f4', True) and check_row_concentration(combo, 4):
        return False
    if filters.get('f5', True) and check_column_concentration(combo, 4):
        return False
    if filters.get('f6', True) and min(combo) >= 21:
        return False
    if filters.get('f7', True) and sum(1 for n in combo if n >= 40) >= 3:
        return False
    if filters.get('f8', True) and calculate_ac(combo) < rules.get('min_ac', 5):
        return False
    return True


def _get_decade_counts(combo: Sequence[int]) -> Tuple[int, int, int, int, int]:
    counts = [0, 0, 0, 0, 0]
    for n in combo:
        if n <= 10:
            counts[0] += 1
        elif n <= 20:
            counts[1] += 1
        elif n <= 30:
            counts[2] += 1
        elif n <= 40:
            counts[3] += 1
        else:
            counts[4] += 1
    return tuple(counts)


def _score_from_ranges(value: int, ranges: Sequence[Dict], default_score: int) -> int:
    for rule in ranges:
        minimum = rule.get('min', float('-inf'))
        maximum = rule.get('max', float('inf'))
        if minimum <= value <= maximum:
            return int(rule.get('score', default_score))
    return int(default_score)


def _score_from_map(value: int, score_map: Dict[int, int], default_score: int) -> int:
    return int(score_map.get(value, default_score))


def build_number_feature_map(analysis: Dict | None = None) -> Dict[int, Dict]:
    analysis = analysis or {}
    existing = analysis.get('number_features', {}) or {}
    if existing:
        normalized = {}
        for raw_num, raw_item in existing.items():
            num = int(raw_num)
            item = dict(raw_item or {})
            normalized[num] = {
                'number': num,
                'freq_10': int(item.get('freq_10', 0)),
                'freq_30': int(item.get('freq_30', 0)),
                'freq_50': int(item.get('freq_50', 0)),
                'freq_100': int(item.get('freq_100', 0)),
                'last_seen': int(item.get('last_seen', -1)),
                'is_carryover': bool(item.get('is_carryover', False)),
                'is_bonus_carryover': bool(item.get('is_bonus_carryover', False)),
                'hot_cold_label': str(item.get('hot_cold_label', 'neutral')),
                'hot_score': int(item.get('hot_score', item.get('hot_cold_score', 0))),
            }
        return normalized

    frequency_windows = analysis.get('number_frequency_windows', {})
    last_seen = analysis.get('last_seen_draws_ago', {})
    carryover_latest = analysis.get('carryover_metrics', {}).get('latest', {})
    hot_cold = analysis.get('hot_cold_profile', {})

    features = {}
    carryover_numbers = set(carryover_latest.get('carryover_numbers', []))
    bonus_carryover_numbers = set(carryover_latest.get('bonus_carryover_numbers', []))

    for num in range(1, 46):
        item = {
            'number': num,
            'freq_10': int((frequency_windows.get('10') or frequency_windows.get(10) or {}).get(num, 0)),
            'freq_30': int((frequency_windows.get('30') or frequency_windows.get(30) or {}).get(num, 0)),
            'freq_50': int((frequency_windows.get('50') or frequency_windows.get(50) or {}).get(num, 0)),
            'freq_100': int((frequency_windows.get('100') or frequency_windows.get(100) or {}).get(num, 0)),
            'last_seen': int(last_seen.get(num, -1)),
            'is_carryover': num in carryover_numbers,
            'is_bonus_carryover': num in bonus_carryover_numbers,
            'hot_cold_label': 'neutral',
            'hot_score': 0,
        }
        profile = hot_cold.get(str(num)) or hot_cold.get(num) or {}
        if profile:
            item['hot_cold_label'] = str(profile.get('label', 'neutral'))
            item['hot_score'] = int(profile.get('score', 0))
        features[num] = item
    return features


def score_number_signals(
    combo: Sequence[int],
    overdue_numbers: Set[int] | None = None,
    carryover_numbers: Set[int] | None = None,
    bonus_carryover_numbers: Set[int] | None = None,
    analysis: Dict | None = None,
    score_config: Dict | None = None,
) -> Dict:
    overdue_numbers = overdue_numbers or set()
    carryover_numbers = carryover_numbers or set()
    bonus_carryover_numbers = bonus_carryover_numbers or set()
    config = normalize_score_config(score_config)
    number_features = build_number_feature_map(analysis)

    breakdown = {
        'overdue': 0,
        'frequency': 0,
        'last_seen': 0,
        'hot_cold': 0,
        'carryover': 0,
        'bonus_carryover': 0,
    }

    for n in combo:
        feat = number_features.get(int(n), {})
        if n in overdue_numbers:
            breakdown['overdue'] += int(config['overdue_weight'])
        if n in carryover_numbers:
            breakdown['carryover'] += int(config['carryover_weight'])
        if n in bonus_carryover_numbers:
            breakdown['bonus_carryover'] += int(config['bonus_carryover_weight'])

        for window, weight in config.get('frequency_window_weights', {}).items():
            key = f'freq_{int(window)}'
            breakdown['frequency'] += int(feat.get(key, 0)) * int(weight)

        breakdown['last_seen'] += _score_from_ranges(
            int(feat.get('last_seen', -1)),
            config.get('last_seen_weights', []),
            int(config.get('last_seen_default_score', 0)),
        )

        label = str(feat.get('hot_cold_label', 'neutral'))
        breakdown['hot_cold'] += int(config.get('hot_score_weights', {}).get(label, 0))

    breakdown['count_adjustments'] = _dynamic_signal_bonus_from_counts(
        sum(1 for n in combo if n in overdue_numbers),
        sum(1 for n in combo if n in carryover_numbers),
        sum(1 for n in combo if n in bonus_carryover_numbers),
        config,
    ) - breakdown['overdue'] - breakdown['carryover'] - breakdown['bonus_carryover']

    breakdown['total'] = sum(int(v) for v in breakdown.values() if isinstance(v, int))
    return breakdown


def score_combo_signals(combo: Sequence[int], score_config: Dict | None = None) -> Dict:
    config = normalize_score_config(score_config)
    breakdown = {}

    ac = calculate_ac(combo)
    breakdown['ac'] = _score_from_ranges(ac, config['ac_ranges'], config['ac_default_score'])

    odd_count = get_odd_count(combo)
    breakdown['odd_even'] = _score_from_map(odd_count, config['odd_count_scores'], config['odd_default_score'])

    high_count = get_high_count(combo)
    breakdown['high_low'] = _score_from_map(high_count, config['high_count_scores'], config['high_default_score'])

    total = get_sum(combo)
    breakdown['sum'] = _score_from_ranges(total, config['sum_ranges'], config['sum_default_score'])

    max_concentration = max(_get_decade_counts(combo))
    concentration_score = config['concentration_default_score']
    for threshold, threshold_score in sorted(config['max_concentration_scores'].items()):
        if max_concentration <= threshold:
            concentration_score = threshold_score
            break
    breakdown['decade_balance'] = int(concentration_score)
    breakdown['total'] = sum(int(v) for v in breakdown.values())
    return breakdown


def _dynamic_signal_bonus_from_counts(
    overdue_count: int,
    carryover_count: int,
    bonus_carryover_count: int,
    config: Dict,
) -> int:
    score = overdue_count * int(config['overdue_weight'])
    if config.get('carryover_count_scores'):
        score += _score_from_map(carryover_count, config['carryover_count_scores'], int(config.get('carryover_default_score', 0)))
    else:
        score += carryover_count * int(config['carryover_weight'])
    if config.get('bonus_carryover_count_scores'):
        score += _score_from_map(bonus_carryover_count, config['bonus_carryover_count_scores'], int(config.get('bonus_carryover_default_score', 0)))
    else:
        score += bonus_carryover_count * int(config['bonus_carryover_weight'])
    return int(score)


def score_combination(
    combo: Sequence[int],
    overdue_numbers: Set[int] | None = None,
    carryover_numbers: Set[int] | None = None,
    bonus_carryover_numbers: Set[int] | None = None,
    analysis: Dict | None = None,
    score_config: Dict | None = None,
    return_breakdown: bool = False,
) -> int | Dict:
    config = normalize_score_config(score_config)
    number_signal = score_number_signals(
        combo,
        overdue_numbers=overdue_numbers,
        carryover_numbers=carryover_numbers,
        bonus_carryover_numbers=bonus_carryover_numbers,
        analysis=analysis,
        score_config=config,
    )
    combo_signal = score_combo_signals(combo, score_config=config)
    total_score = int(number_signal['total']) + int(combo_signal['total'])
    if return_breakdown:
        return {
            'total': total_score,
            'number_signal': number_signal,
            'combo_signal': combo_signal,
        }
    return total_score


def compute_static_score(combo: Sequence[int], score_config: Dict | None = None) -> int:
    return int(score_combo_signals(combo, score_config=score_config)['total'])


def cache_key_for_rules(rules: Dict) -> str:
    filters = normalize_filters(rules.get('filters'))
    filter_bits = ''.join('1' if filters[f'f{i}'] else '0' for i in range(1, 9))
    score_config = normalize_score_config(rules.get('score_config'))
    score_signature = hashlib.sha256(json_signature(score_config).encode('utf-8')).hexdigest()[:16]
    return f"minac{rules.get('min_ac', 5)}_filters{filter_bits}_score{score_signature}"


def cache_path_for_rules(rules: Dict) -> str:
    os.makedirs(CACHE_DIR, exist_ok=True)
    return os.path.join(CACHE_DIR, f"combo_cache_{cache_key_for_rules(rules)}.pkl")


def build_or_load_repository(rules: Dict, force_rebuild: bool = False) -> ComboRepository:
    normalized_rules = normalize_rules(rules.get('min_ac', 5), rules.get('filters'), rules.get('score_config'))
    cache_path = cache_path_for_rules(normalized_rules)

    if not force_rebuild and os.path.exists(cache_path):
        with open(cache_path, 'rb') as fh:
            payload = pickle.load(fh)
        return ComboRepository(
            masks=payload['masks'],
            static_scores=payload['static_scores'],
            total_valid=payload['total_valid'],
            rules=payload['rules'],
        )

    masks = array('Q')
    static_scores = array('H')

    for combo in itertools.combinations(range(1, 46), 6):
        if check_filters(combo, normalized_rules):
            masks.append(combo_to_mask(combo))
            static_scores.append(compute_static_score(combo, normalized_rules.get('score_config')))

    payload = {
        'masks': masks,
        'static_scores': static_scores,
        'total_valid': len(masks),
        'rules': normalized_rules,
    }
    with open(cache_path, 'wb') as fh:
        pickle.dump(payload, fh, protocol=pickle.HIGHEST_PROTOCOL)

    return ComboRepository(
        masks=masks,
        static_scores=static_scores,
        total_valid=len(masks),
        rules=normalized_rules,
    )


def build_overdue_numbers(last_seen_draws_ago: Dict[int, int], threshold: int = 25) -> Set[int]:
    return {int(n) for n, seen in last_seen_draws_ago.items() if seen >= threshold or seen == -1}


def recommend_from_repository(
    repository: ComboRepository,
    overdue_numbers: Set[int] | None = None,
    carryover_numbers: Set[int] | None = None,
    bonus_carryover_numbers: Set[int] | None = None,
    analysis: Dict | None = None,
    count: int = 10,
    seed: int | None = None,
    max_carryover_count: int | None = None,
) -> List[Tuple[int, ...]]:
    overdue_numbers = overdue_numbers or set()
    carryover_numbers = carryover_numbers or set()
    bonus_carryover_numbers = bonus_carryover_numbers or set()
    overdue_mask = combo_to_mask(sorted(overdue_numbers)) if overdue_numbers else 0
    carryover_mask = combo_to_mask(sorted(carryover_numbers)) if carryover_numbers else 0
    bonus_carryover_mask = combo_to_mask(sorted(bonus_carryover_numbers)) if bonus_carryover_numbers else 0
    config = normalize_score_config(repository.rules.get('score_config'))

    if repository.total_valid == 0 or count <= 0:
        return []

    scored_entries = []
    for mask, static_score in repository.iter_entries():
        overdue_count = (mask & overdue_mask).bit_count() if overdue_mask else 0
        carryover_count = (mask & carryover_mask).bit_count() if carryover_mask else 0
        bonus_carryover_count = (mask & bonus_carryover_mask).bit_count() if bonus_carryover_mask else 0
        if max_carryover_count is not None and carryover_count > max_carryover_count:
            continue
        combo = mask_to_combo(mask)
        number_breakdown = score_number_signals(
            combo,
            overdue_numbers=overdue_numbers,
            carryover_numbers=carryover_numbers,
            bonus_carryover_numbers=bonus_carryover_numbers,
            analysis=analysis,
            score_config=config,
        )
        dynamic_bonus = int(number_breakdown['total'])
        total_score = int(static_score) + dynamic_bonus
        scored_entries.append((total_score, mask))

    if not scored_entries:
        return []

    scored_entries.sort(key=lambda item: item[0], reverse=True)
    cutoff_index = min(count, len(scored_entries)) - 1
    cutoff_score = scored_entries[cutoff_index][0]

    guaranteed = []
    tie_pool = []
    for entry in scored_entries:
        total_score, mask = entry
        if total_score > cutoff_score:
            guaranteed.append(entry)
        elif total_score == cutoff_score:
            tie_pool.append(entry)
        else:
            break

    rng = random.Random(seed)
    rng.shuffle(tie_pool)

    selected = guaranteed[:]
    remaining_slots = max(0, count - len(selected))
    selected.extend(tie_pool[:remaining_slots])
    selected.sort(key=lambda item: (-item[0], item[1]))

    return [mask_to_combo(mask) for _, mask in selected[:count]]


def count_total_combinations(pool_size: int, needed: int) -> int:
    if needed < 0 or needed > pool_size:
        return 0
    return math.comb(pool_size, needed)


def recommend_with_constraints(
    fixed_nums: Iterable[int] | None = None,
    exclude_nums: Iterable[int] | None = None,
    min_ac: int = 5,
    filters: Dict | None = None,
    overdue_numbers: Set[int] | None = None,
    carryover_numbers: Set[int] | None = None,
    bonus_carryover_numbers: Set[int] | None = None,
    analysis: Dict | None = None,
    count: int = 10,
    seed: int | None = None,
    score_config: Dict | None = None,
    max_carryover_count: int | None = None,
):
    fixed_nums = sorted(set(fixed_nums or []))
    exclude_nums = sorted(set(exclude_nums or []))
    rules = normalize_rules(min_ac=min_ac, filters=filters, score_config=score_config)
    overdue_numbers = overdue_numbers or set()
    carryover_numbers = carryover_numbers or set()
    bonus_carryover_numbers = bonus_carryover_numbers or set()

    pool = [n for n in range(1, 46) if n not in fixed_nums and n not in exclude_nums]
    needed = 6 - len(fixed_nums)
    total_space = count_total_combinations(len(pool), needed)
    if needed < 0 or needed > len(pool):
        raise ValueError('Invalid parameters')

    valid_masks = []
    static_scores = []
    for additional in itertools.combinations(pool, needed):
        combo = tuple(sorted(fixed_nums + list(additional)))
        if max_carryover_count is not None and carryover_numbers is not None:
            carryover_count = sum(1 for n in combo if n in carryover_numbers)
            if carryover_count > max_carryover_count:
                continue
        if check_filters(combo, rules):
            valid_masks.append(combo_to_mask(combo))
            static_scores.append(compute_static_score(combo, rules.get('score_config')))

    repository = ComboRepository(
        masks=array('Q', valid_masks),
        static_scores=array('H', static_scores),
        total_valid=len(valid_masks),
        rules=rules,
    )
    recommendations = recommend_from_repository(
        repository,
        overdue_numbers=overdue_numbers,
        carryover_numbers=carryover_numbers,
        bonus_carryover_numbers=bonus_carryover_numbers,
        analysis=analysis,
        count=count,
        seed=seed,
        max_carryover_count=max_carryover_count,
    )
    filtered_ratio = f"{(1 - len(valid_masks) / max(1, total_space)) * 100:.1f}%"

    return {
        'total': len(valid_masks),
        'list': [list(c) for c in recommendations],
        'stats': {
            'fixed_count': len(fixed_nums),
            'excluded_count': len(exclude_nums),
            'pool_size': len(pool),
            'overdue_count': len(overdue_numbers),
            'carryover_count': len(carryover_numbers),
            'bonus_carryover_count': len(bonus_carryover_numbers),
            'filtered_ratio': filtered_ratio,
            'total_combination_space': total_space,
            'max_carryover_count': max_carryover_count,
        }
    }
