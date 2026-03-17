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
from array import array
from collections import Counter
from dataclasses import dataclass
from typing import Dict, Iterable, List, Sequence, Set, Tuple

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

CACHE_DIR = os.path.join(os.path.dirname(__file__), '.cache')


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


def normalize_rules(min_ac: int = 5, filters: Dict | None = None) -> Dict:
    min_ac = max(0, min(10, int(min_ac)))
    return {
        'min_ac': min_ac,
        'filters': normalize_filters(filters),
    }


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


def score_combination(combo: Sequence[int], overdue_numbers: Set[int] | None = None) -> int:
    overdue_numbers = overdue_numbers or set()
    score = 0
    overdue_count = sum(1 for n in combo if n in overdue_numbers)
    score += overdue_count * 15

    ac = calculate_ac(combo)
    if 8 <= ac <= 10:
        score += 30
    elif ac == 7:
        score += 25
    elif ac == 6:
        score += 15
    else:
        score += 5

    odd_count = get_odd_count(combo)
    if odd_count in [3, 4]:
        score += 25
    elif odd_count == 2:
        score += 20
    else:
        score += 5

    high_count = get_high_count(combo)
    if high_count in [2, 3, 4]:
        score += 20
    else:
        score += 5

    total = get_sum(combo)
    if 110 <= total <= 170:
        score += 25
    elif 100 <= total <= 180:
        score += 15
    else:
        score += 5

    max_concentration = max(_get_decade_counts(combo))
    if max_concentration <= 2:
        score += 20
    elif max_concentration <= 3:
        score += 10

    return score


def compute_static_score(combo: Sequence[int]) -> int:
    return score_combination(combo, overdue_numbers=set())


def cache_key_for_rules(rules: Dict) -> str:
    filters = normalize_filters(rules.get('filters'))
    filter_bits = ''.join('1' if filters[f'f{i}'] else '0' for i in range(1, 9))
    return f"minac{rules.get('min_ac', 5)}_filters{filter_bits}"


def cache_path_for_rules(rules: Dict) -> str:
    os.makedirs(CACHE_DIR, exist_ok=True)
    return os.path.join(CACHE_DIR, f"combo_cache_{cache_key_for_rules(rules)}.pkl")


def build_or_load_repository(rules: Dict, force_rebuild: bool = False) -> ComboRepository:
    normalized_rules = normalize_rules(rules.get('min_ac', 5), rules.get('filters'))
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
            static_scores.append(compute_static_score(combo))

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
    count: int = 10,
    seed: int | None = None,
) -> List[Tuple[int, ...]]:
    overdue_numbers = overdue_numbers or set()
    overdue_mask = combo_to_mask(sorted(overdue_numbers)) if overdue_numbers else 0

    if repository.total_valid == 0 or count <= 0:
        return []

    score_counts = Counter()
    for mask, static_score in repository.iter_entries():
        overdue_bonus = ((mask & overdue_mask).bit_count() * 15) if overdue_mask else 0
        total_score = static_score + overdue_bonus
        score_counts[total_score] += 1

    cumulative = 0
    cutoff_score = None
    for score in sorted(score_counts.keys(), reverse=True):
        cumulative += score_counts[score]
        cutoff_score = score
        if cumulative >= count:
            break

    if cutoff_score is None:
        return []

    guaranteed = []
    tie_pool = []
    for mask, static_score in repository.iter_entries():
        overdue_bonus = ((mask & overdue_mask).bit_count() * 15) if overdue_mask else 0
        total_score = static_score + overdue_bonus
        entry = (total_score, mask)
        if total_score > cutoff_score:
            guaranteed.append(entry)
        elif total_score == cutoff_score:
            tie_pool.append(entry)

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
    count: int = 10,
    seed: int | None = None,
):
    fixed_nums = sorted(set(fixed_nums or []))
    exclude_nums = sorted(set(exclude_nums or []))
    rules = normalize_rules(min_ac=min_ac, filters=filters)
    overdue_numbers = overdue_numbers or set()

    pool = [n for n in range(1, 46) if n not in fixed_nums and n not in exclude_nums]
    needed = 6 - len(fixed_nums)
    total_space = count_total_combinations(len(pool), needed)
    if needed < 0 or needed > len(pool):
        raise ValueError('Invalid parameters')

    valid_masks = []
    static_scores = []
    for additional in itertools.combinations(pool, needed):
        combo = tuple(sorted(fixed_nums + list(additional)))
        if check_filters(combo, rules):
            valid_masks.append(combo_to_mask(combo))
            static_scores.append(compute_static_score(combo))

    repository = ComboRepository(
        masks=array('Q', valid_masks),
        static_scores=array('H', static_scores),
        total_valid=len(valid_masks),
        rules=rules,
    )
    recommendations = recommend_from_repository(repository, overdue_numbers=overdue_numbers, count=count, seed=seed)
    filtered_ratio = f"{(1 - len(valid_masks) / max(1, total_space)) * 100:.1f}%"

    return {
        'total': len(valid_masks),
        'list': [list(c) for c in recommendations],
        'stats': {
            'fixed_count': len(fixed_nums),
            'excluded_count': len(exclude_nums),
            'pool_size': len(pool),
            'overdue_count': len(overdue_numbers),
            'filtered_ratio': filtered_ratio,
            'total_combination_space': total_space,
        }
    }
