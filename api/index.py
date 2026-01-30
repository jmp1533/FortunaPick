from http.server import BaseHTTPRequestHandler
import json
import itertools
from collections import Counter
import random

# --- 유틸리티 및 필터링 로직 ---

def calculate_ac(numbers):
    """AC 값 계산: 두 수의 차이들의 고유 개수 - 5"""
    nums = sorted(list(numbers))
    diffs = set()
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            diffs.add(nums[j] - nums[i])
    return len(diffs) - 5

def check_filters(combo, rules):
    """모든 제외/필터링 조건 검사"""
    # 1. 9 이하의 수가 3개 이상 제외
    if sum(1 for n in combo if n <= 9) >= 3:
        return False

    # 2. 연속된 수가 3개 이상 제외 (예: 1,2,3)
    sorted_combo = sorted(combo)
    consecutive_count = 0
    for i in range(len(sorted_combo) - 1):
        if sorted_combo[i+1] == sorted_combo[i] + 1:
            consecutive_count += 1
            if consecutive_count >= 2: # 2번 연속 = 숫자 3개
                return False
        else:
            consecutive_count = 0

    # 3. 같은 끝수 4개 이상 제외
    last_digits = [n % 10 for n in combo]
    if any(count >= 4 for count in Counter(last_digits).values()):
        return False

    # 4. 가로(Row) 4개 이상 제외 (7열 기준)
    rows = [(n-1) // 7 for n in combo]
    if any(count >= 4 for count in Counter(rows).values()):
        return False

    # 5. 세로(Col) 4개 이상 제외 (7열 기준)
    cols = [(n-1) % 7 for n in combo]
    if any(count >= 4 for count in Counter(cols).values()):
        return False

    # 6. 가장 낮은 수가 21 이상인 조합 제외
    if min(combo) >= 21:
        return False

    # 7. 40 이상의 수가 3개 이상 제외
    if sum(1 for n in combo if n >= 40) >= 3:
        return False

    # 8. AC 값 필터링 (입력값 이하 제외)
    ac = calculate_ac(combo)
    if ac <= rules['min_ac']:
        return False

    return True

# --- Vercel Serverless Handler ---

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        try:
            data = json.loads(post_data.decode('utf-8'))
        except:
            self.send_error(400, "Invalid JSON")
            return

        # 입력 데이터 파싱
        try:
            fixed_num = int(data.get('fixed_num'))
            exclude_nums = set(data.get('exclude_nums', []))
            min_ac = int(data.get('min_ac', 5)) # 미입력시 5이하 제외 (즉 6부터)
        except (ValueError, TypeError):
            self.send_error(400, "Invalid Input Data")
            return

        # 1. 전체 풀 생성 (고정수와 제외수 뺀 나머지)
        pool = [n for n in range(1, 46) if n != fixed_num and n not in exclude_nums]

        valid_combinations = []
        rules = {'min_ac': min_ac}

        # 2. 조합 생성 및 필터링
        # 고정수 1개 + 나머지 5개 뽑기 (약 100만 건 연산)
        for p in itertools.combinations(pool, 5):
            full_combo = tuple(sorted(list(p) + [fixed_num]))

            if check_filters(full_combo, rules):
                valid_combinations.append(full_combo)

        # 3. 결과 그룹화 (비율 맞추기용)
        target_group = [] # 비율 조건(홀짝, AC) 맞는 그룹
        other_group = []  # 나머지 그룹

        for combo in valid_combinations:
            odd_cnt = sum(1 for n in combo if n % 2 != 0)
            ac = calculate_ac(combo)

            # 조건: 홀짝 2:4, 3:3, 4:2 AND AC 7~10
            is_target_ratio = (odd_cnt in [2, 3, 4])
            is_target_ac = (7 <= ac <= 10)

            if is_target_ratio and is_target_ac:
                target_group.append(combo)
            else:
                other_group.append(combo)

        # 4. 최종 추출 (10게임 추천, 8:2 비율)
        recommend_count = 10
        final_result = []

        target_pick_cnt = int(recommend_count * 0.8)
        other_pick_cnt = recommend_count - target_pick_cnt

        # Target Group 샘플링
        if len(target_group) >= target_pick_cnt:
            final_result.extend(random.sample(target_group, target_pick_cnt))
        else:
            final_result.extend(target_group)
            other_pick_cnt += (target_pick_cnt - len(target_group))

        # Other Group 샘플링
        if len(other_group) >= other_pick_cnt:
            final_result.extend(random.sample(other_group, other_pick_cnt))
        else:
            final_result.extend(other_group)

        # 응답 구성
        response = {
            "total_valid_count": len(valid_combinations),
            "recommendations": [list(c) for c in final_result],
            "debug_info": {
                "target_ratio_count": len(target_group),
                "other_ratio_count": len(other_group)
            }
        }

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))