from http.server import BaseHTTPRequestHandler
import json
import itertools
from collections import Counter
import random

# --- AC 계산 함수 ---
def calculate_ac(numbers):
    nums = sorted(list(numbers))
    diffs = set()
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            diffs.add(nums[j] - nums[i])
    return len(diffs) - 5

# --- 필터링 로직 (ON/OFF 가능) ---
def check_filters(combo, rules):
    filters = rules.get('filters', {})

    # 1. 9 이하의 수가 3개 이상 제외
    if filters.get('under_10_limit', True):
        if sum(1 for n in combo if n <= 9) >= 3:
            return False

    # 2. 연속된 수가 3개 이상 제외 (예: 1,2,3)
    if filters.get('consecutive_limit', True):
        sorted_combo = sorted(combo)
        consecutive_count = 0
        for i in range(len(sorted_combo) - 1):
            if sorted_combo[i+1] == sorted_combo[i] + 1:
                consecutive_count += 1
                if consecutive_count >= 2:
                    return False
            else:
                consecutive_count = 0

    # 3. 같은 끝수 4개 이상 제외
    if filters.get('same_end_limit', True):
        last_digits = [n % 10 for n in combo]
        if any(count >= 4 for count in Counter(last_digits).values()):
            return False

    # 4. 가로(Row) 4개 이상 제외 (7열 기준)
    if filters.get('row_limit', True):
        rows = [(n-1) // 7 for n in combo]
        if any(count >= 4 for count in Counter(rows).values()):
            return False

    # 5. 세로(Col) 4개 이상 제외 (7열 기준)
    if filters.get('col_limit', True):
        cols = [(n-1) % 7 for n in combo]
        if any(count >= 4 for count in Counter(cols).values()):
            return False

    # 6. 가장 낮은 수가 21 이상인 조합 제외
    if filters.get('min_num_limit', True):
        if min(combo) >= 21:
            return False

    # 7. 40 이상의 수가 3개 이상 제외
    if filters.get('high_num_limit', True):
        if sum(1 for n in combo if n >= 40) >= 3:
            return False

    # 8. AC 값 필터링
    if filters.get('ac_limit', True):
        ac = calculate_ac(combo)
        if ac <= rules.get('min_ac', 5):
            return False

    return True

# --- 메인 핸들러 ---
class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)

        try:
            data = json.loads(post_data.decode('utf-8'))

            fixed_nums = set(data.get('fixed_nums', []))   # 필수 숫자 (여러개 가능)
            exclude_nums = set(data.get('exclude_nums', [])) # 제외 숫자
            min_ac = int(data.get('min_ac', 5))
            active_filters = data.get('filters', {})       # 체크된 필터 목록

        except:
            self.send_error(400, "Invalid JSON")
            return

        # 유효성 검사
        if len(fixed_nums) > 5:
             # 필수 숫자가 6개면 경우의 수는 1개뿐이므로, 여기선 5개까지만 허용 (원하시면 6개도 가능)
            pass

        # 1. 전체 풀 생성 (1~45 중 필수와 제외를 뺀 나머지)
        pool = [n for n in range(1, 46) if n not in fixed_nums and n not in exclude_nums]

        # 필수 숫자가 이미 6개를 넘거나, 풀이 부족하면 에러 처리 필요하지만 여기선 생략하고 진행
        pick_count = 6 - len(fixed_nums)

        valid_combinations = []
        rules = {
            'min_ac': min_ac,
            'filters': active_filters
        }

        # 2. 조합 생성
        # itertools.combinations(나머지 숫자풀, 뽑아야할 개수)
        for p in itertools.combinations(pool, pick_count):
            full_combo = tuple(sorted(list(p) + list(fixed_nums)))

            if check_filters(full_combo, rules):
                valid_combinations.append(full_combo)

        # 3. 결과 추출 (비율 로직 적용)
        # 만약 필터링 된 결과가 너무 적으면 비율 무시하고 전체 반환

        target_group = []
        other_group = []

        for combo in valid_combinations:
            odd_cnt = sum(1 for n in combo if n % 2 != 0)
            ac = calculate_ac(combo)

            is_target_ratio = (odd_cnt in [2, 3, 4])
            is_target_ac = (7 <= ac <= 10)

            if is_target_ratio and is_target_ac:
                target_group.append(combo)
            else:
                other_group.append(combo)

        recommend_count = 10
        final_result = []

        target_pick_cnt = int(recommend_count * 0.8)
        other_pick_cnt = recommend_count - target_pick_cnt

        if len(target_group) >= target_pick_cnt:
            final_result.extend(random.sample(target_group, target_pick_cnt))
        else:
            final_result.extend(target_group)
            other_pick_cnt += (target_pick_cnt - len(target_group))

        if len(other_group) >= other_pick_cnt:
            final_result.extend(random.sample(other_group, other_pick_cnt))
        else:
            final_result.extend(other_group)

        response = {
            "total_valid_count": len(valid_combinations),
            "recommendations": [list(c) for c in final_result]
        }

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode('utf-8'))