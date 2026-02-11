from http.server import BaseHTTPRequestHandler
import json
import pandas as pd
import os
import datetime

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Define potential paths for the Excel file
            possible_paths = [
                os.path.join(os.path.dirname(__file__), '..', 'lottery', 'winningNumbers.xlsx'),
                os.path.join(os.getcwd(), 'lottery', 'winningNumbers.xlsx'),
                os.path.join(os.path.dirname(__file__), 'lottery', 'winningNumbers.xlsx'),
                '/var/task/lottery/winningNumbers.xlsx'
            ]

            excel_path = None
            checked_paths = []
            for path in possible_paths:
                full_path = os.path.abspath(path)
                checked_paths.append(full_path)
                if os.path.exists(full_path):
                    excel_path = full_path
                    break

            if not excel_path:
                self.send_response(404)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'error': 'Excel file not found.',
                    'checked_paths': checked_paths
                }).encode())
                return

            try:
                df = pd.read_excel(excel_path, engine='openpyxl')
            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': f'Failed to read Excel file: {str(e)}'}).encode())
                return

            history_data = []
            parsing_errors = []

            # Iterate through rows
            for index, row in df.iterrows():
                try:
                    if len(row) < 9:
                        continue

                    # Parse Round (Index 1)
                    raw_round = row.iloc[1]
                    if pd.isna(raw_round):
                        continue

                    round_str = str(raw_round).replace(',', '').replace('회', '').strip()
                    if not round_str.isdigit():
                         continue
                    round_num = int(round_str)

                    # Parse Numbers (Index 2-7)
                    numbers = []
                    for i in range(2, 8):
                        val = row.iloc[i]
                        if pd.isna(val):
                            raise ValueError(f"Missing number at index {i}")
                        numbers.append(int(val))

                    sorted_numbers = sorted(numbers)

                    # Parse Bonus (Index 8)
                    bonus_val = row.iloc[8]
                    if pd.isna(bonus_val):
                         raise ValueError("Missing bonus number")
                    bonus = int(bonus_val)

                    # Calculate Stats
                    # 1. Sum
                    total_sum = sum(sorted_numbers)

                    # 2. Odd/Even Ratio
                    odd_count = sum(1 for n in sorted_numbers if n % 2 != 0)
                    even_count = 6 - odd_count
                    odd_even = f"{odd_count}:{even_count}"

                    # 3. AC Value
                    # AC = (Unique differences between pairs) - (N - 1)
                    diffs = set()
                    for i in range(len(sorted_numbers)):
                        for j in range(i + 1, len(sorted_numbers)):
                            diffs.add(abs(sorted_numbers[i] - sorted_numbers[j]))
                    ac_value = len(diffs) - 5

                    # Date is missing in the provided format description.
                    date_str = ""

                    history_data.append({
                        'round': round_num,
                        'date': date_str,
                        'numbers': sorted_numbers,
                        'bonus': bonus,
                        'stats': {
                            'sum': total_sum,
                            'oddEven': odd_even,
                            'ac': ac_value
                        }
                    })
                except Exception as e:
                    if len(parsing_errors) < 5:
                        parsing_errors.append(f"Row {index}: {str(e)}")
                    continue

            if not history_data:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'error': 'No valid data parsed from Excel file.',
                    'parsing_errors_sample': parsing_errors,
                    'columns': df.columns.tolist(),
                    'first_row': str(df.iloc[0].tolist()) if not df.empty else 'Empty'
                }, ensure_ascii=False).encode('utf-8'))
                return

            # Sort history by round in descending order
            history_data.sort(key=lambda x: x['round'], reverse=True)

            latest_round = history_data[0]['round'] if history_data else 0

            response_data = {
                'latestRound': latest_round,
                'history': history_data
            }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': f'Unexpected error: {str(e)}'}).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
