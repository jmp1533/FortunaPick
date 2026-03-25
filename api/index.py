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
from lottery.engine import recommend_with_constraints
from lottery.score_presets import SCORE_PRESETS
from lottery.top_picks import DEFAULT_EXTRACT_MAX_CARRYOVER, EXTRACT_SELECTION_POLICY, get_current_draw_context

RECOMMENDATION_MODES = {
    'stable': 'balanced_distribution',
    'high_hit': 'sum_relaxed',
}


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
            recommendation_mode = data.get('recommendation_mode', 'stable')
            score_preset = data.get('score_preset')

            if score_preset is None:
                score_preset = RECOMMENDATION_MODES.get(recommendation_mode, RECOMMENDATION_MODES['stable'])

            if score_preset not in SCORE_PRESETS:
                raise ValueError('Invalid score preset')

            analyzer = get_analyzer()
            context = get_current_draw_context(analyzer)
            analysis = context['analysis']
            overdue_numbers = context['overdue_numbers']
            latest_draw = context['latest_draw']
            carryover_numbers = context['carryover_numbers']
            bonus_carryover_numbers = context['bonus_carryover_numbers']
            carryover_latest = analysis.get('carryover_metrics', {}).get('latest', {})

            response = recommend_with_constraints(
                fixed_nums=fixed_nums,
                exclude_nums=exclude_nums,
                min_ac=min_ac,
                filters=filters,
                overdue_numbers=overdue_numbers,
                carryover_numbers=carryover_numbers,
                bonus_carryover_numbers=bonus_carryover_numbers,
                analysis=analysis,
                score_config=SCORE_PRESETS[score_preset],
                max_carryover_count=DEFAULT_EXTRACT_MAX_CARRYOVER,
            )
            response['recommendation_mode'] = recommendation_mode
            response['carryover_metrics'] = {
                'carryover_numbers': sorted(carryover_numbers),
                'bonus_carryover_numbers': sorted(bonus_carryover_numbers),
                'source_previous_round': int(latest_draw[0]['회차']) if latest_draw else None,
                'latest_observed_repeat': carryover_latest,
            }
            response['score_preset'] = score_preset
            response['selection_policy'] = EXTRACT_SELECTION_POLICY

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
