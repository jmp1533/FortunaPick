from __future__ import annotations

import heapq
import json
import time
from typing import Dict, List, Sequence

from lottery.analyzer import LotteryAnalyzer
from lottery.engine import (
    build_or_load_repository,
    build_overdue_numbers,
    calculate_ac,
    get_high_count,
    get_odd_count,
    get_sum,
    mask_to_combo,
    normalize_rules,
    score_combination,
)
from lottery.paths import get_report_path
from lottery.score_presets import SCORE_PRESETS

TOP_PICKS_FILENAME = 'weekly_top_picks.json'
DEFAULT_TOP_COUNT = 5
DEFAULT_BUCKET_SIZE = 8000
DEFAULT_COMPOSITE_LIMIT = 15000
DEFAULT_MODE_BUCKET_SIZE = 5000
DEFAULT_MAX_NUMBER_FREQUENCY = 2


def combo_overlap(a: Sequence[int], b: Sequence[int]) -> int:
    return len(set(a) & set(b))


def consecutive_runs(nums: Sequence[int]) -> List[List[int]]:
    nums = sorted(nums)
    runs = []
    run = [nums[0]]
    for n in nums[1:]:
        if n == run[-1] + 1:
            run.append(n)
        else:
            runs.append(run)
            run = [n]
    runs.append(run)
    return runs


def mirror_pairs(nums: Sequence[int]) -> List[tuple[int, int]]:
    s = set(nums)
    pairs = []
    for n in sorted(nums):
        m = 46 - n
        if n < m and m in s:
            pairs.append((n, m))
    return pairs


def ending_max_count(nums: Sequence[int]) -> int:
    counts: Dict[int, int] = {}
    for n in nums:
        key = n % 10
        counts[key] = counts.get(key, 0) + 1
    return max(counts.values()) if counts else 0


def elite_pattern_adjustment(combo: Sequence[int]) -> tuple[float, List[str]]:
    adjustment = 0.0
    reasons: List[str] = []

    runs = [r for r in consecutive_runs(combo) if len(r) >= 2]
    max_run = max((len(r) for r in runs), default=1)
    run_groups = len(runs)
    mirrors = len(mirror_pairs(combo))
    ending_max = ending_max_count(combo)
    low_count = sum(1 for n in combo if n <= 9)

    if max_run >= 3:
        adjustment -= 18
        reasons.append('3연번 이상')
    elif run_groups >= 2:
        adjustment -= 10
        reasons.append('연번 구간 2개')

    if mirrors >= 2:
        adjustment -= 12
        reasons.append('거울수 2쌍+')

    if ending_max >= 3:
        adjustment -= 10
        reasons.append('끝수 몰림')

    if low_count >= 3:
        adjustment -= 8
        reasons.append('저숫자 3개+')

    if max_run == 2 and run_groups == 1:
        adjustment += 1.5
    if mirrors == 1:
        adjustment += 1.0

    return adjustment, reasons


def classify_sum_band(total: int) -> str:
    if total < 100:
        return 'low'
    if total <= 145:
        return 'mid'
    return 'high'


def classify_profile(combo: Sequence[int]) -> Dict[str, object]:
    total = get_sum(combo)
    odd = get_odd_count(combo)
    high = get_high_count(combo)
    runs = [r for r in consecutive_runs(combo) if len(r) >= 2]
    return {
        'sum': total,
        'sum_band': classify_sum_band(total),
        'odd_count': odd,
        'high_count': high,
        'run_groups': len(runs),
        'has_pair_run': any(len(r) == 2 for r in runs),
        'max_run': max((len(r) for r in runs), default=1),
    }


def build_pick_tags(
    combo: Sequence[int],
    stable_score: float,
    high_score: float,
    overdue_numbers: set[int],
    carryover_numbers: set[int],
    bonus_carryover_numbers: set[int],
) -> List[str]:
    tags = []
    ac = calculate_ac(combo)
    odd = get_odd_count(combo)
    high = get_high_count(combo)
    total = get_sum(combo)
    overdue_count = sum(1 for n in combo if n in overdue_numbers)
    carryover_count = sum(1 for n in combo if n in carryover_numbers)
    bonus_carryover_count = sum(1 for n in combo if n in bonus_carryover_numbers)
    profile = classify_profile(combo)

    if 8 <= ac <= 10:
        tags.append('AC 우수')
    if odd in (3, 4):
        tags.append('홀짝 균형')
    if high in (2, 3, 4):
        tags.append('고저 균형')
    if 110 <= total <= 170:
        tags.append('합계 안정')
    elif profile['sum_band'] == 'low':
        tags.append('저합계 변동형')
    if profile['has_pair_run']:
        tags.append('연번 포함형')
    if overdue_count >= 1:
        tags.append(f'미출현 {overdue_count}개')
    if carryover_count >= 1:
        tags.append(f'이월수 {carryover_count}개')
    elif bonus_carryover_count >= 1:
        tags.append('보너스 이월형')

    if stable_score >= high_score + 5:
        tags.append('안정형 우세')
    elif high_score >= stable_score + 5:
        tags.append('고적중형 우세')
    else:
        tags.append('균형 후보')

    return tags[:2]


def push_topk(heap, score: float, mask: int, k: int):
    entry = (score, mask)
    if len(heap) < k:
        heapq.heappush(heap, entry)
    elif entry > heap[0]:
        heapq.heapreplace(heap, entry)


def collect_candidate_masks(
    repository,
    overdue_numbers: set[int],
    carryover_numbers: set[int],
    bonus_carryover_numbers: set[int],
    stable_rules: Dict,
    high_rules: Dict,
    bucket_size: int,
):
    overdue_mask = 0
    for n in overdue_numbers:
        overdue_mask |= 1 << (n - 1)

    stable_heap = []
    high_heap = []
    neutral_heap = []

    for mask, _static_score in repository.iter_entries():
        combo = mask_to_combo(mask)
        stable_score = score_combination(
            combo,
            overdue_numbers=overdue_numbers,
            carryover_numbers=carryover_numbers,
            bonus_carryover_numbers=bonus_carryover_numbers,
            score_config=stable_rules['score_config'],
        )
        high_score = score_combination(
            combo,
            overdue_numbers=overdue_numbers,
            carryover_numbers=carryover_numbers,
            bonus_carryover_numbers=bonus_carryover_numbers,
            score_config=high_rules['score_config'],
        )
        neutral_score = stable_score + high_score

        push_topk(stable_heap, float(stable_score), mask, bucket_size)
        push_topk(high_heap, float(high_score), mask, bucket_size)
        push_topk(neutral_heap, float(neutral_score), mask, bucket_size)

    candidate_masks = {mask for _, mask in stable_heap}
    candidate_masks.update(mask for _, mask in high_heap)
    candidate_masks.update(mask for _, mask in neutral_heap)
    return candidate_masks


def build_composite_candidates(
    candidate_masks: set[int],
    overdue_numbers: set[int],
    carryover_numbers: set[int],
    bonus_carryover_numbers: set[int],
    stable_rules: Dict,
    high_rules: Dict,
):
    candidates = []
    for mask in candidate_masks:
        combo = list(mask_to_combo(mask))
        stable_score = score_combination(
            combo,
            overdue_numbers=overdue_numbers,
            carryover_numbers=carryover_numbers,
            bonus_carryover_numbers=bonus_carryover_numbers,
            score_config=stable_rules['score_config'],
        )
        high_score = score_combination(
            combo,
            overdue_numbers=overdue_numbers,
            carryover_numbers=carryover_numbers,
            bonus_carryover_numbers=bonus_carryover_numbers,
            score_config=high_rules['score_config'],
        )

        composite_score = (stable_score * 0.55) + (high_score * 0.45)
        composite_score += min(stable_score, high_score) * 0.15
        composite_score -= abs(stable_score - high_score) * 0.08
        elite_adjustment, elite_reasons = elite_pattern_adjustment(combo)
        composite_score += elite_adjustment

        tags = build_pick_tags(
            combo,
            stable_score,
            high_score,
            overdue_numbers,
            carryover_numbers,
            bonus_carryover_numbers,
        )
        if elite_reasons:
            tags = [tag for tag in tags if tag not in {'균형 후보', '안정형 우세', '고적중형 우세'}]
            tags.extend(elite_reasons[:1])

        profile = classify_profile(combo)

        candidates.append({
            'combo': combo,
            'stable_score': stable_score,
            'high_hit_score': high_score,
            'composite_score': round(composite_score, 4),
            'elite_adjustment': round(elite_adjustment, 2),
            'tags': tags[:2],
            'profile': profile,
        })

    candidates.sort(key=lambda item: (item['composite_score'], item['stable_score'], item['high_hit_score']), reverse=True)
    return candidates


def _can_add_candidate(
    candidate: Dict,
    selected: List[Dict],
    number_usage: Dict[int, int],
    sum_band_usage: Dict[str, int],
    max_overlap: int,
    max_number_frequency: int,
    max_sum_band_frequency: int,
) -> bool:
    combo = candidate['combo']
    if not all(combo_overlap(combo, picked['combo']) <= max_overlap for picked in selected):
        return False

    if any(number_usage.get(n, 0) >= max_number_frequency for n in combo):
        return False

    profile = candidate.get('profile') or classify_profile(combo)
    sum_band = str(profile.get('sum_band', 'mid'))
    if sum_band_usage.get(sum_band, 0) >= max_sum_band_frequency:
        return False

    return True


def select_diversified_top_picks(
    candidates: List[Dict],
    target_count: int = DEFAULT_TOP_COUNT,
    max_overlap: int = 4,
    max_number_frequency: int = DEFAULT_MAX_NUMBER_FREQUENCY,
    max_sum_band_frequency: int = 2,
) -> List[Dict]:
    selected: List[Dict] = []
    number_usage: Dict[int, int] = {}
    sum_band_usage: Dict[str, int] = {}

    desired_bands = ['low', 'mid', 'high'] if target_count >= 3 else ['mid']
    for band in desired_bands:
        band_candidates = [
            candidate for candidate in candidates
            if (candidate.get('profile') or classify_profile(candidate['combo'])).get('sum_band') == band
        ]
        for candidate in band_candidates:
            if candidate in selected:
                continue
            if _can_add_candidate(candidate, selected, number_usage, sum_band_usage, max_overlap, max_number_frequency, max_sum_band_frequency):
                selected.append(candidate)
                for n in candidate['combo']:
                    number_usage[n] = number_usage.get(n, 0) + 1
                profile = candidate.get('profile') or classify_profile(candidate['combo'])
                sum_band = str(profile.get('sum_band', 'mid'))
                sum_band_usage[sum_band] = sum_band_usage.get(sum_band, 0) + 1
                break
        if len(selected) >= target_count:
            break

    for candidate in candidates:
        if candidate in selected:
            continue
        if _can_add_candidate(candidate, selected, number_usage, sum_band_usage, max_overlap, max_number_frequency, max_sum_band_frequency):
            selected.append(candidate)
            for n in candidate['combo']:
                number_usage[n] = number_usage.get(n, 0) + 1
            profile = candidate.get('profile') or classify_profile(candidate['combo'])
            sum_band = str(profile.get('sum_band', 'mid'))
            sum_band_usage[sum_band] = sum_band_usage.get(sum_band, 0) + 1
        if len(selected) >= target_count:
            break

    if len(selected) < target_count:
        for candidate in candidates:
            if candidate not in selected:
                selected.append(candidate)
            if len(selected) >= target_count:
                break

    return selected


def build_mode_top_picks(
    mode: str,
    top_count: int = DEFAULT_TOP_COUNT,
    min_ac: int = 5,
    filters: Dict | None = None,
    bucket_size: int = DEFAULT_MODE_BUCKET_SIZE,
):
    analyzer = LotteryAnalyzer()
    analysis = analyzer.get_analysis_results()
    overdue_numbers = build_overdue_numbers(analysis.get('last_seen_draws_ago', {}), threshold=25)
    latest_draw = analyzer.get_latest_draws(count=1)
    carryover_numbers = set(latest_draw[0]['winning_numbers']) if latest_draw else set()
    bonus_carryover_numbers = {int(latest_draw[0]['bonus_number'])} if latest_draw else set()

    preset_name = 'balanced_distribution' if mode == 'stable' else 'sum_relaxed'
    rules = normalize_rules(min_ac=min_ac, filters=filters, score_config=SCORE_PRESETS[preset_name])
    repository = build_or_load_repository(rules, force_rebuild=False)

    top_heap = []
    for mask, _ in repository.iter_entries():
        combo = mask_to_combo(mask)
        score = score_combination(
            combo,
            overdue_numbers=overdue_numbers,
            carryover_numbers=carryover_numbers,
            bonus_carryover_numbers=bonus_carryover_numbers,
            score_config=rules['score_config'],
        )
        push_topk(top_heap, float(score), mask, bucket_size)

    scored = []
    for score, mask in sorted(top_heap, key=lambda item: (item[0], item[1]), reverse=True):
        combo = list(mask_to_combo(mask))
        scored.append({
            'combo': combo,
            'score': int(score),
            'tags': build_pick_tags(
                combo,
                score if mode == 'stable' else 0,
                score if mode == 'high_hit' else 0,
                overdue_numbers,
                carryover_numbers,
                bonus_carryover_numbers,
            ),
            'profile': classify_profile(combo),
        })

    return [
        {k: v for k, v in item.items() if k != 'profile'}
        for item in select_diversified_top_picks(scored, target_count=top_count, max_overlap=4)
    ]


def generate_weekly_top_picks(
    top_count: int = DEFAULT_TOP_COUNT,
    bucket_size: int = DEFAULT_BUCKET_SIZE,
    composite_limit: int = DEFAULT_COMPOSITE_LIMIT,
    min_ac: int = 5,
    filters: Dict | None = None,
):
    analyzer = LotteryAnalyzer()
    latest_round = analyzer.get_latest_round_number()
    analysis = analyzer.get_analysis_results()
    overdue_numbers = build_overdue_numbers(analysis.get('last_seen_draws_ago', {}), threshold=25)
    latest_draw = analyzer.get_latest_draws(count=1)
    carryover_numbers = set(latest_draw[0]['winning_numbers']) if latest_draw else set()
    bonus_carryover_numbers = {int(latest_draw[0]['bonus_number'])} if latest_draw else set()

    stable_rules = normalize_rules(min_ac=min_ac, filters=filters, score_config=SCORE_PRESETS['balanced_distribution'])
    high_rules = normalize_rules(min_ac=min_ac, filters=filters, score_config=SCORE_PRESETS['sum_relaxed'])
    repository = build_or_load_repository(stable_rules, force_rebuild=False)

    candidate_masks = collect_candidate_masks(
        repository,
        overdue_numbers,
        carryover_numbers,
        bonus_carryover_numbers,
        stable_rules,
        high_rules,
        bucket_size=bucket_size,
    )
    composite_candidates = build_composite_candidates(
        candidate_masks,
        overdue_numbers,
        carryover_numbers,
        bonus_carryover_numbers,
        stable_rules,
        high_rules,
    )
    weekly_top = select_diversified_top_picks(composite_candidates[:composite_limit], target_count=top_count, max_overlap=4)

    stable_top = build_mode_top_picks('stable', top_count=top_count, min_ac=min_ac, filters=filters)
    high_top = build_mode_top_picks('high_hit', top_count=top_count, min_ac=min_ac, filters=filters)

    def _public_pick(item: Dict) -> Dict:
        return {k: v for k, v in item.items() if k != 'profile'}

    payload = {
        'generatedAt': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'latestRound': latest_round,
        'targetRound': (int(latest_round) + 1) if latest_round is not None else None,
        'carryoverContext': {
            'source_round': int(latest_draw[0]['회차']) if latest_draw else None,
            'carryover_numbers': sorted(carryover_numbers),
            'bonus_carryover_numbers': sorted(bonus_carryover_numbers),
            'latest_observed_repeat': analysis.get('carryover_metrics', {}).get('latest', {}),
        },
        'topCount': top_count,
        'bucketSize': bucket_size,
        'compositeLimit': composite_limit,
        'candidatePoolSize': len(candidate_masks),
        'weeklyTopPicks': [_public_pick(item) for item in weekly_top],
        'stableTopPicks': [_public_pick(item) for item in stable_top],
        'highHitTopPicks': [_public_pick(item) for item in high_top],
    }
    return payload


def save_weekly_top_picks(payload: Dict, path: str | None = None) -> str:
    output_path = path or get_report_path(TOP_PICKS_FILENAME)
    with open(output_path, 'w', encoding='utf-8') as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    return output_path
