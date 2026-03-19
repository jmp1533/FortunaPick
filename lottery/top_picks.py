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


def combo_overlap(a: Sequence[int], b: Sequence[int]) -> int:
    return len(set(a) & set(b))


def build_pick_tags(combo: Sequence[int], stable_score: float, high_score: float, overdue_numbers: set[int]) -> List[str]:
    tags = []
    ac = calculate_ac(combo)
    odd = get_odd_count(combo)
    high = get_high_count(combo)
    total = get_sum(combo)
    overdue_count = sum(1 for n in combo if n in overdue_numbers)

    if 8 <= ac <= 10:
        tags.append('AC 우수')
    if odd in (3, 4):
        tags.append('홀짝 균형')
    if high in (2, 3, 4):
        tags.append('고저 균형')
    if 110 <= total <= 170:
        tags.append('합계 안정')
    if overdue_count >= 1:
        tags.append(f'미출현 {overdue_count}개')

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


def collect_candidate_masks(repository, overdue_numbers: set[int], stable_rules: Dict, high_rules: Dict, bucket_size: int):
    overdue_mask = 0
    for n in overdue_numbers:
        overdue_mask |= 1 << (n - 1)

    stable_heap = []
    high_heap = []
    neutral_heap = []

    for mask, _static_score in repository.iter_entries():
        combo = mask_to_combo(mask)
        stable_score = score_combination(combo, overdue_numbers=overdue_numbers, score_config=stable_rules['score_config'])
        high_score = score_combination(combo, overdue_numbers=overdue_numbers, score_config=high_rules['score_config'])
        neutral_score = stable_score + high_score

        push_topk(stable_heap, float(stable_score), mask, bucket_size)
        push_topk(high_heap, float(high_score), mask, bucket_size)
        push_topk(neutral_heap, float(neutral_score), mask, bucket_size)

    candidate_masks = {mask for _, mask in stable_heap}
    candidate_masks.update(mask for _, mask in high_heap)
    candidate_masks.update(mask for _, mask in neutral_heap)
    return candidate_masks


def build_composite_candidates(candidate_masks: set[int], overdue_numbers: set[int], stable_rules: Dict, high_rules: Dict):
    candidates = []
    for mask in candidate_masks:
        combo = list(mask_to_combo(mask))
        stable_score = score_combination(combo, overdue_numbers=overdue_numbers, score_config=stable_rules['score_config'])
        high_score = score_combination(combo, overdue_numbers=overdue_numbers, score_config=high_rules['score_config'])

        composite_score = (stable_score * 0.55) + (high_score * 0.45)
        composite_score += min(stable_score, high_score) * 0.15
        composite_score -= abs(stable_score - high_score) * 0.08

        candidates.append({
            'combo': combo,
            'stable_score': stable_score,
            'high_hit_score': high_score,
            'composite_score': round(composite_score, 4),
            'tags': build_pick_tags(combo, stable_score, high_score, overdue_numbers),
        })

    candidates.sort(key=lambda item: (item['composite_score'], item['stable_score'], item['high_hit_score']), reverse=True)
    return candidates


def select_diversified_top_picks(candidates: List[Dict], target_count: int = DEFAULT_TOP_COUNT, max_overlap: int = 4) -> List[Dict]:
    selected = []
    for candidate in candidates:
        combo = candidate['combo']
        if all(combo_overlap(combo, picked['combo']) <= max_overlap for picked in selected):
            selected.append(candidate)
        if len(selected) >= target_count:
            break

    if len(selected) < target_count:
        for candidate in candidates:
            if candidate not in selected:
                selected.append(candidate)
            if len(selected) >= target_count:
                break

    return selected


def build_mode_top_picks(mode: str, top_count: int = DEFAULT_TOP_COUNT, min_ac: int = 5, filters: Dict | None = None):
    analyzer = LotteryAnalyzer()
    analysis = analyzer.get_analysis_results()
    overdue_numbers = build_overdue_numbers(analysis.get('last_seen_draws_ago', {}), threshold=25)

    preset_name = 'balanced_distribution' if mode == 'stable' else 'sum_relaxed'
    rules = normalize_rules(min_ac=min_ac, filters=filters, score_config=SCORE_PRESETS[preset_name])
    repository = build_or_load_repository(rules, force_rebuild=False)

    scored = []
    for mask, _ in repository.iter_entries():
        combo = list(mask_to_combo(mask))
        score = score_combination(combo, overdue_numbers=overdue_numbers, score_config=rules['score_config'])
        scored.append({
            'combo': combo,
            'score': score,
            'tags': build_pick_tags(combo, score if mode == 'stable' else 0, score if mode == 'high_hit' else 0, overdue_numbers),
        })

    scored.sort(key=lambda item: item['score'], reverse=True)
    return select_diversified_top_picks(scored, target_count=top_count, max_overlap=4)


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

    stable_rules = normalize_rules(min_ac=min_ac, filters=filters, score_config=SCORE_PRESETS['balanced_distribution'])
    high_rules = normalize_rules(min_ac=min_ac, filters=filters, score_config=SCORE_PRESETS['sum_relaxed'])
    repository = build_or_load_repository(stable_rules, force_rebuild=False)

    candidate_masks = collect_candidate_masks(repository, overdue_numbers, stable_rules, high_rules, bucket_size=bucket_size)
    composite_candidates = build_composite_candidates(candidate_masks, overdue_numbers, stable_rules, high_rules)
    weekly_top = select_diversified_top_picks(composite_candidates[:composite_limit], target_count=top_count, max_overlap=4)

    stable_top = build_mode_top_picks('stable', top_count=top_count, min_ac=min_ac, filters=filters)
    high_top = build_mode_top_picks('high_hit', top_count=top_count, min_ac=min_ac, filters=filters)

    payload = {
        'generatedAt': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'latestRound': latest_round,
        'topCount': top_count,
        'bucketSize': bucket_size,
        'compositeLimit': composite_limit,
        'candidatePoolSize': len(candidate_masks),
        'weeklyTopPicks': weekly_top,
        'stableTopPicks': stable_top,
        'highHitTopPicks': high_top,
    }
    return payload


def save_weekly_top_picks(payload: Dict, path: str | None = None) -> str:
    output_path = path or get_report_path(TOP_PICKS_FILENAME)
    with open(output_path, 'w', encoding='utf-8') as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)
    return output_path
