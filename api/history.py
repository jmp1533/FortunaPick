from http.server import BaseHTTPRequestHandler
import json
import pandas as pd
import os
import datetime

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            # Define potential paths for the Excel file to handle different environments (Local vs Vercel)
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

            # Check if the file exists
            if not excel_path:
                self.send_response(404)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                # Include checked paths for debugging purposes
                self.wfile.write(json.dumps({
                    'error': 'Excel file not found.',
                    'checked_paths': checked_paths,
                    'cwd': os.getcwd(),
                    'script_dir': os.path.dirname(__file__)
                }).encode())
                return

            # Read the Excel file
            # Assuming columns: '회차', '추첨일', '번호1', '번호2', '번호3', '번호4', '번호5', '번호6', '보너스'
            df = pd.read_excel(excel_path, engine='openpyxl')

            # Process the DataFrame into the desired JSON format
            history_data = []
            for index, row in df.iterrows():
                try:
                    numbers = [
                        int(row['번호1']), int(row['번호2']), int(row['번호3']),
                        int(row['번호4']), int(row['번호5']), int(row['번호6'])
                    ]

                    # Handle date format
                    date_val = row['추첨일']
                    if isinstance(date_val, (datetime.date, datetime.datetime)):
                        date_str = date_val.strftime('%Y-%m-%d')
                    else:
                        date_str = str(date_val)

                    history_data.append({
                        'round': int(row['회차']),
                        'date': date_str,
                        'numbers': sorted(numbers),
                        'bonus': int(row['보너스'])
                    })
                except Exception as e:
                    # Skip rows with errors
                    continue

            # Sort history by round in descending order
            history_data.sort(key=lambda x: x['round'], reverse=True)

            latest_round = history_data[0]['round'] if history_data else 0

            response_data = {
                'latestRound': latest_round,
                'history': history_data
            }

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*') # Allow CORS
            self.end_headers()
            self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
