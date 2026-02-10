"""
FortunaPick API - Premium Lotto Combination Engine
Vercel Serverless Function (Python)
"""

from http.server import BaseHTTPRequestHandler
import json
import itertools
from collections import Counter
import random


def calculate_ac(numbers):
    """
    AC (Arithmetic Complexity) 값 계산
    모든 두 수의 차의 절대값 집합 크기에서 5를 뺀 값
    """
    nums = sorted(list(numbers))
    diffs = set()
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            diffs.add(abs(nums[j] - nums[i]))
    return len(diffs) - 5


def get_sum(numbers):
    """번호 합계 계산"""
    return sum(numbers)


def get_odd_count(numbers):
    """홀수 개수 계산"""
    return sum(1 for n in numbers if n % 2 != 0)


def get_high_count(numbers):
    """고번호(23 이상) 개수 계산"""
    return sum(1 for n in numbers if n >= 23)


def check_consecutive(numbers, count=3):
    """
    연속된 번호가 count개 이상인지 확인
    """
    sorted_nums = sorted(numbers)
    consecutive = 1
    for i in range(1, len(sorted_nums)):
        if sorted_nums[i] == sorted_nums[i-1] + 1:
            consecutive += 1
            if consecutive >= count:
                return True
        else:
            consecutive = 1
    return False


def check_same_ending(numbers, count=4):
    """
    같은 끝수가 count개 이상인지 확인
    """
    endings = [n % 10 for n in numbers]
    counter = Counter(endings)
    return any(c >= count for c in counter.values())


def check_row_concentration(numbers, count=4):
    """
    7열 기준 가로 한 줄에 count개 이상 집중되어 있는지 확인
    1-7: 0행, 8-14: 1행, 15-21: 2행, 22-28: 3행, 29-35: 4행, 36-42: 5행, 43-45: 6행
    """
    rows = [(n - 1) // 7 for n in numbers]
    counter = Counter(rows)
    return any(c >= count for c in counter.values())


def check_column_concentration(numbers, count=4):
    """
    7열 기준 세로 한 줄에 count개 이상 집중되어 있는지 확인
    """
    cols = [(n - 1) % 7 for n in numbers]
    counter = Counter(cols)
    return any(c >= count for c in counter.values())


def check_filters(combo, rules):
    """
    필터링 조건 검사
    모든 조건을 통과하면 True 반환
    """
    f = rules.get('filters', {})
    
    # f1: 9 이하의 수가 3개 이상인 조합 제외
    if f.get('f1', True):
        if sum(1 for n in combo if n <= 9) >= 3:
            return False
    
    # f2: 연속된 번호 3개 이상인 조합 제외
    if f.get('f2', True):
        if check_consecutive(combo, 3):
            return False
    
    # f3: 동일한 끝수가 4개 이상인 조합 제외
    if f.get('f3', True):
        if check_same_ending(combo, 4):
            return False
    
    # f4: 가로 한 줄에 4개 이상 집중 제외
    if f.get('f4', True):
        if check_row_concentration(combo, 4):
            return False
    
    # f5: 세로 한 줄에 4개 이상 집중 제외
    if f.get('f5', True):
        if check_column_concentration(combo, 4):
            return False
    
    # f6: 가장 낮은 수가 21 이상인 조합 제외
    if f.get('f6', True):
        if min(combo) >= 21:
            return False
    
    # f7: 40 이상의 수가 3개 이상인 조합 제외
    if f.get('f7', True):
        if sum(1 for n in combo if n >= 40) >= 3:
            return False
    
    # f8: AC값이 설정값 미만인 조합 제외
    if f.get('f8', True):
        min_ac = rules.get('min_ac', 5)
        if calculate_ac(combo) < min_ac:
            return False
    
    return True


def score_combination(combo):
    """
    조합의 품질 점수 계산 (높을수록 좋음)
    다양한 통계적 특성을 고려하여 점수 부여
    """
    score = 0
    
    # AC 값 점수 (7-10이 이상적)
    ac = calculate_ac(combo)
    if 7 <= ac <= 10:
        score += 30
    elif 6 <= ac <= 11:
        score += 20
    else:
        score += 10
    
    # 홀짝 비율 점수 (3:3 또는 2:4, 4:2가 이상적)
    odd_count = get_odd_count(combo)
    if odd_count in [3]:
        score += 25
    elif odd_count in [2, 4]:
        score += 20
    else:
        score += 5
    
    # 고저 비율 점수 (균형잡힌 것이 좋음)
    high_count = get_high_count(combo)
    if high_count in [2, 3, 4]:
        score += 20
    else:
        score += 5
    
    # 합계 점수 (115-185가 통계적으로 좋음)
    total = get_sum(combo)
    if 121 <= total <= 180:
        score += 25
    elif 100 <= total <= 200:
        score += 15
    else:
        score += 5
    
    # 번호대 분포 점수 (고르게 분포되어 있을수록 좋음)
    decades = {
        '1-10': sum(1 for n in combo if 1 <= n <= 10),
        '11-20': sum(1 for n in combo if 11 <= n <= 20),
        '21-30': sum(1 for n in combo if 21 <= n <= 30),
        '31-40': sum(1 for n in combo if 31 <= n <= 40),
        '41-45': sum(1 for n in combo if 41 <= n <= 45)
    }
    
    # 최대 편중도 계산 (낮을수록 좋음)
    max_concentration = max(decades.values())
    if max_concentration <= 2:
        score += 20
    elif max_concentration <= 3:
        score += 10
    
    return score


def recommend_combinations(valid_combos, count=10):
    """
    유효한 조합 중에서 최적의 조합을 추천
    """
    if len(valid_combos) <= count:
        return valid_combos
    
    # 모든 조합에 점수 부여
    scored = [(combo, score_combination(combo)) for combo in valid_combos]
    
    # 점수순 정렬
    scored.sort(key=lambda x: x[1], reverse=True)
    
    # 상위 80%에서 랜덤하게 8개 선택
    top_pool_size = max(int(len(scored) * 0.2), count * 2)
    top_pool = scored[:top_pool_size]
    
    # 다양성을 위해 랜덤 셔플 후 선택
    random.shuffle(top_pool)
    
    # 상위 8개와 나머지에서 2개 선택
    primary_picks = top_pool[:min(8, len(top_pool))]
    
    # 나머지 풀에서 2개 추가 (다양성 확보)
    remaining = scored[top_pool_size:]
    if remaining:
        random.shuffle(remaining)
        secondary_picks = remaining[:min(2, len(remaining))]
    else:
        secondary_picks = []
    
    result = [combo for combo, _ in primary_picks + secondary_picks]
    
    # 최종 결과를 점수순으로 정렬
    result.sort(key=lambda c: score_combination(c), reverse=True)
    
    return result[:count]


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        """CORS preflight 요청 처리"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_POST(self):
        """조합 생성 요청 처리"""
        try:
            # 요청 데이터 파싱
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                raw_data = self.rfile.read(content_length)
                data = json.loads(raw_data.decode('utf-8'))
            else:
                data = {}
            
            # 파라미터 추출
            fixed_nums = set(data.get('fixed_nums', []))
            exclude_nums = set(data.get('exclude_nums', []))
            min_ac = int(data.get('min_ac', 5))
            # AC 값 범위 제한 (0~10)
            min_ac = max(0, min(10, min_ac))
            filters = data.get('filters', {})
            
            # 사용 가능한 번호 풀 생성
            pool = [n for n in range(1, 46) if n not in fixed_nums and n not in exclude_nums]
            
            # 필요한 추가 번호 개수
            needed = 6 - len(fixed_nums)
            
            if needed < 0 or needed > len(pool):
                # 잘못된 요청
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'error': 'Invalid parameters',
                    'total': 0,
                    'list': []
                }).encode())
                return
            
            # 규칙 설정
            rules = {
                'min_ac': min_ac,
                'filters': filters
            }
            
            # 유효한 조합 생성
            valid_combos = []
            
            for additional in itertools.combinations(pool, needed):
                combo = tuple(sorted(list(fixed_nums) + list(additional)))
                if check_filters(combo, rules):
                    valid_combos.append(combo)
            
            # 추천 조합 선택
            recommendations = recommend_combinations(valid_combos, count=10)
            
            # 응답 생성
            response = {
                'total': len(valid_combos),
                'list': [list(c) for c in recommendations],
                'stats': {
                    'fixed_count': len(fixed_nums),
                    'excluded_count': len(exclude_nums),
                    'pool_size': len(pool),
                    'filtered_ratio': f"{(1 - len(valid_combos) / max(1, len(list(itertools.combinations(pool, needed))))) * 100:.1f}%"
                }
            }
            
            # 응답 전송
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            # 오류 처리
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'error': str(e),
                'total': 0,
                'list': []
            }).encode())
