"""
FortunaPick API - Premium Lotto Combination Engine
Vercel Serverless Function (Python)
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from http.server import BaseHTTPRequestHandler
import json
from lottery.analyzer import LotteryAnalyzer
from lottery.engine import build_overdue_numbers, recommend_with_constraints


def get_analyzer():
    return LotteryAnalyzer()


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                raw_data = self.rfile.read(content_length)
                data = json.loads(raw_data.decode('utf-8'))
            else:
                data = {}

            fixed_nums = data.get('fixed_nums', [])
            exclude_nums = data.get('exclude_nums', [])
            min_ac = int(data.get('min_ac', 5))
            filters = data.get('filters', {})

            analyzer = get_analyzer()
            last_seen = analyzer.get_analysis_results().get('last_seen_draws_ago', {})
            overdue_numbers = build_overdue_numbers(last_seen, threshold=25)

            response = recommend_with_constraints(
                fixed_nums=fixed_nums,
                exclude_nums=exclude_nums,
                min_ac=min_ac,
                filters=filters,
                overdue_numbers=overdue_numbers,
            )

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())

        except ValueError as e:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'error': str(e),
                'total': 0,
                'list': []
            }).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({
                'error': str(e),
                'total': 0,
                'list': []
            }).encode())
