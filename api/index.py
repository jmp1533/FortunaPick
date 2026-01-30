from http.server import BaseHTTPRequestHandler
import json
import itertools
from collections import Counter
import random

def calculate_ac(numbers):
    nums = sorted(list(numbers))
    diffs = set()
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            diffs.add(nums[j] - nums[i])
    return len(diffs) - 5

def check_filters(combo, rules):
    f = rules.get('filters', {})
    # 활성화된 필터만 작동
    if f.get('f1', True) and sum(1 for n in combo if n <= 9) >= 3: return False
    if f.get('f2', True):
        sorted_c = sorted(combo)
        if any(sorted_c[i+2] == sorted_c[i]+2 for i in range(4)): return False
    if f.get('f3', True) and any(c >= 4 for c in Counter([n%10 for n in combo]).values()): return False
    if f.get('f4', True) and any(c >= 4 for c in Counter([(n-1)//7 for n in combo]).values()): return False
    if f.get('f5', True) and any(c >= 4 for c in Counter([(n-1)%7 for n in combo]).values()): return False
    if f.get('f6', True) and min(combo) >= 21: return False
    if f.get('f7', True) and sum(1 for n in combo if n >= 40) >= 3: return False
    if f.get('f8', True) and calculate_ac(combo) <= rules.get('min_ac', 5): return False
    return True

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        data = json.loads(self.rfile.read(content_length).decode('utf-8'))

        fixed = set(data.get('fixed_nums', []))
        exclude = set(data.get('exclude_nums', []))
        pool = [n for n in range(1, 46) if n not in fixed and n not in exclude]

        valid = []
        rules = {'min_ac': int(data.get('min_ac', 5)), 'filters': data.get('filters', {})}

        for p in itertools.combinations(pool, 6 - len(fixed)):
            combo = tuple(sorted(list(p) + list(fixed)))
            if check_filters(combo, rules): valid.append(combo)

        # 8:2 전략 추출
        target = [c for c in valid if sum(1 for n in c if n%2!=0) in [2,3,4] and 7<=calculate_ac(c)<=10]
        others = [c for c in valid if c not in target]

        recommend = random.sample(target, min(8, len(target))) + random.sample(others, min(2, len(others)))

        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"total": len(valid), "list": [list(c) for c in recommend]}).encode())