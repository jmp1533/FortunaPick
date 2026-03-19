"""
FortunaPick Update API
Checks latest Excel round and incrementally updates backtest reports.
"""

import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from http.server import BaseHTTPRequestHandler
import json
from lottery.analyzer import LotteryAnalyzer
from lottery.backtest import update_backtest_report_incrementally
from lottery.score_presets import SCORE_PRESETS
from lottery.paths import get_report_path

REPORT_TARGETS = {
    'stable': {
        'report_path': get_report_path('backtest_stable_report.json'),
        'score_config': SCORE_PRESETS['balanced_distribution'],
    },
    'high_hit': {
        'report_path': get_report_path('backtest_high_hit_report.json'),
        'score_config': SCORE_PRESETS['sum_relaxed'],
    },
}


def build_status_payload():
    analyzer = LotteryAnalyzer()
    latest_excel_round = analyzer.get_latest_round_number()
    targets = {}

    for mode, config in REPORT_TARGETS.items():
        report_path = os.path.abspath(config['report_path'])
        report_exists = os.path.exists(report_path)
        latest_report_round = None
        if report_exists:
            with open(report_path, encoding='utf-8') as fh:
                report = json.load(fh)
            rounds = report.get('rounds', [])
            latest_report_round = max((int(item['round']) for item in rounds), default=None)

        missing_rounds = []
        if latest_excel_round is not None:
            if latest_report_round is None:
                missing_rounds = analyzer.get_round_numbers()
            else:
                missing_rounds = [r for r in analyzer.get_round_numbers() if r > latest_report_round]

        targets[mode] = {
            'report_path': report_path,
            'report_exists': report_exists,
            'latest_report_round': latest_report_round,
            'missing_rounds': missing_rounds,
        }

    return {
        'latest_excel_round': latest_excel_round,
        'targets': targets,
    }


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        try:
            payload = build_status_payload()
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(payload).encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            data = {}
            if content_length > 0:
                raw_data = self.rfile.read(content_length)
                data = json.loads(raw_data.decode('utf-8'))

            mode = data.get('mode', 'all')
            recent_window = int(data.get('recent_window', 30))
            recommend_count = int(data.get('recommend_count', 10))
            seed_base = int(data.get('seed_base', 1000))

            selected_modes = list(REPORT_TARGETS.keys()) if mode == 'all' else [mode]
            invalid_modes = [m for m in selected_modes if m not in REPORT_TARGETS]
            if invalid_modes:
                raise ValueError(f"Invalid update mode: {', '.join(invalid_modes)}")

            results = {}
            for selected_mode in selected_modes:
                config = REPORT_TARGETS[selected_mode]
                result = update_backtest_report_incrementally(
                    report_path=os.path.abspath(config['report_path']),
                    recent_window=recent_window,
                    recommend_count=recommend_count,
                    seed_base=seed_base,
                    score_config=config['score_config'],
                )
                results[selected_mode] = {
                    'status': result['status'],
                    'latest_round': result.get('latest_round'),
                    'missing_rounds': result.get('missing_rounds', []),
                    'applied_rounds': result.get('applied_rounds', []),
                }

            response = build_status_payload()
            response['update_results'] = results

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
            self.wfile.write(json.dumps({'error': str(e)}).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())
