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
                # Read Excel file
                # Header is at row 0 (first row).
                # Columns based on user description:
                # Index 0: No
                # Index 1: 회차
                # Index 2~7: 당첨번호 (6개)
                # Index 8: 보너스
                # Index 9: 순위
                # Index 10: 당첨게임수
                # Index 11: 1게임당 당첨금액

                # Note: The user mentioned merged cells in the header row for "당첨번호".
                # Pandas read_excel handles merged cells by filling the value in the top-left cell
                # and leaving others as NaN or empty, but since we are accessing by index (iloc),
                # the header structure matters less as long as the data rows are consistent.
                # However, if the header row is complex (merged cells), it might be safer to skip the header
                # or read without header and manually process.
                # Let's try reading with header=1 (skipping the first row which might be the complex header)
                # or just read normally and iterate carefully.

                # Given the description:
                # Row 0: Header (with merged cells)
                # Row 1+: Data

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
                    # Access by position (integer location) to avoid column name issues
                    # Ensure we have enough columns
                    if len(row) < 9:
                        continue

                    # Parse Round (Index 1)
                    # The value might be a string like "1,210" or an integer
                    raw_round = row.iloc[1]
                    if pd.isna(raw_round):
                        continue

                    # Clean up the round string (remove commas, spaces)
                    round_str = str(raw_round).replace(',', '').replace('회', '').strip()
                    if not round_str.isdigit():
                         continue
                    round_num = int(round_str)

                    # Parse Numbers (Index 2-7)
                    numbers = []
                    for i in range(2, 8):
                        val = row.iloc[i]
                        # Handle potential non-numeric values or floats
                        if pd.isna(val):
                            raise ValueError(f"Missing number at index {i}")
                        numbers.append(int(val))

                    # Parse Bonus (Index 8)
                    bonus_val = row.iloc[8]
                    if pd.isna(bonus_val):
                         raise ValueError("Missing bonus number")
                    bonus = int(bonus_val)

                    # Date is missing in the provided format description.
                    # We'll set it to a placeholder.
                    date_str = ""

                    history_data.append({
                        'round': round_num,
                        'date': date_str,
                        'numbers': sorted(numbers),
                        'bonus': bonus
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
