
import pandas as pd
import os
from collections import Counter

class LotteryAnalyzer:
    def __init__(self, excel_filename='winningNumbers.xlsx'):
        # analyzer.py와 같은 폴더에 있는 winningNumbers.xlsx를 정확히 참조
        self.excel_path = os.path.join(os.path.dirname(__file__), excel_filename)
        self.df = self._load_data()
        self.analysis_results = {}
        if not self.df.empty:
            self._perform_analysis()

    def _load_data(self):
        try:
            # Vercel 환경에서는 파일 시스템 구조가 다를 수 있음. 
            # 하지만 __file__ 기반 경로가 가장 안전함.
            if not os.path.exists(self.excel_path):
                # fallback for some environments
                potential_path = os.path.join('/var/task/lottery', 'winningNumbers.xlsx')
                if os.path.exists(potential_path):
                    self.excel_path = potential_path
            
            df = pd.read_excel(self.excel_path, engine='openpyxl')
            
            # Filter out rows with missing or invalid '회차' (Round) or numbers
            df['회차'] = pd.to_numeric(df['회차'].astype(str).str.replace(',', '').str.replace('회', '').str.strip(), errors='coerce')
            df.dropna(subset=['회차'], inplace=True)
            df = df[df['회차'] > 0] # Ensure round number is positive

            # Extract winning numbers (Assuming columns '번호1' through '번호6')
            num_cols = [col for col in df.columns if '번호' in col and col != '보너스']
            if len(num_cols) < 6:
                raise ValueError("Could not find 6 winning number columns (e.g., '번호1' to '번호6')")
            
            # Ensure numbers are integers and within range 1-45
            for col in num_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Drop rows with any NaN in number columns or outside 1-45
            df.dropna(subset=num_cols, inplace=True)
            for col in num_cols:
                df = df[(df[col] >= 1) & (df[col] <= 45)]

            df['winning_numbers'] = df[num_cols].apply(lambda x: sorted(x.tolist()), axis=1)
            df['bonus_number'] = pd.to_numeric(df['보너스'], errors='coerce').fillna(0).astype(int) # Handle bonus number

            return df.sort_values(by='회차', ascending=False).reset_index(drop=True) # Latest rounds first
        except Exception as e:
            print(f"Error loading or parsing Excel data: {e}")
            return pd.DataFrame()

    def _perform_analysis(self):
        if self.df.empty:
            return

        all_numbers = [num for sublist in self.df['winning_numbers'] for num in sublist]
        
        # 1. Number Frequencies
        self.analysis_results['number_frequencies'] = Counter(all_numbers)
        
        # 2. Hot/Cold Numbers (e.g., last 100 draws)
        recent_draws_count = min(100, len(self.df))
        recent_numbers = [num for sublist in self.df.head(recent_draws_count)['winning_numbers'] for num in sublist]
        self.analysis_results['hot_cold_numbers'] = Counter(recent_numbers)

        # 3. Sum Distribution
        self.analysis_results['sum_distribution'] = self.df['winning_numbers'].apply(sum).describe().to_dict()
        
        # 4. AC Distribution
        self.analysis_results['ac_distribution'] = self.df['winning_numbers'].apply(self._calculate_ac).describe().to_dict()

        # 5. Odd/Even Distribution
        self.analysis_results['odd_even_distribution'] = Counter(self.df['winning_numbers'].apply(self._get_odd_even_ratio))
        
        # 6. High/Low Distribution (High >= 23)
        self.analysis_results['high_low_distribution'] = Counter(self.df['winning_numbers'].apply(self._get_high_count))

        # 7. Consecutive Number Frequencies
        self.analysis_results['consecutive_pairs_count'] = sum(1 for nums in self.df['winning_numbers'] if self._check_consecutive_pair(nums))
        self.analysis_results['consecutive_triplets_count'] = sum(1 for nums in self.df['winning_numbers'] if self._check_consecutive_triplet(nums))
        
        # 8. Same Ending Frequencies
        self.analysis_results['same_ending_counts'] = Counter(self.df['winning_numbers'].apply(self._get_same_ending_max_count))

        # 9. Last Seen (for each number)
        last_seen = {num: -1 for num in range(1, 46)}
        for idx, row in self.df.iterrows():
            for num in row['winning_numbers']:
                if last_seen[num] == -1: # Only record the most recent
                    last_seen[num] = idx # index represents draws ago (0 is latest, 1 is prev, etc)
        self.analysis_results['last_seen_draws_ago'] = last_seen

        # 10. Number Group Concentrations (1-10, 11-20, etc.)
        self.analysis_results['group_concentration_distribution'] = Counter(self.df['winning_numbers'].apply(self._get_group_concentration_key))


    def _calculate_ac(self, numbers):
        nums = sorted(list(numbers))
        diffs = set()
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                diffs.add(abs(nums[j] - nums[i]))
        return len(diffs) - 5

    def _get_odd_even_ratio(self, numbers):
        odd_count = sum(1 for n in numbers if n % 2 != 0)
        return f"{odd_count}:{6 - odd_count}"

    def _get_high_count(self, numbers):
        return sum(1 for n in numbers if n >= 23) # High number definition from index.py

    def _check_consecutive_pair(self, numbers):
        sorted_nums = sorted(numbers)
        for i in range(1, len(sorted_nums)):
            if sorted_nums[i] == sorted_nums[i-1] + 1:
                return True
        return False
    
    def _check_consecutive_triplet(self, numbers):
        sorted_nums = sorted(numbers)
        consecutive = 1
        for i in range(1, len(sorted_nums)):
            if sorted_nums[i] == sorted_nums[i-1] + 1:
                consecutive += 1
                if consecutive >= 3:
                    return True
            else:
                consecutive = 1
        return False

    def _get_same_ending_max_count(self, numbers):
        endings = [n % 10 for n in numbers]
        counter = Counter(endings)
        return max(counter.values()) if counter else 0

    def _get_group_concentration_key(self, numbers):
        decades = {
            '1-10': sum(1 for n in numbers if 1 <= n <= 10),
            '11-20': sum(1 for n in numbers if 11 <= n <= 20),
            '21-30': sum(1 for n in numbers if 21 <= n <= 30),
            '31-40': sum(1 for n in numbers if 31 <= n <= 40),
            '41-45': sum(1 for n in numbers if 41 <= n <= 45)
        }
        # Create a string representation of the concentration for counting
        return "-".join(str(decades[key]) for key in sorted(decades.keys()))


    def get_analysis_results(self):
        return self.analysis_results

    def get_latest_draws(self, count=10):
        if self.df.empty:
            return []
        return self.df.head(count)[['회차', 'winning_numbers', 'bonus_number']].to_dict(orient='records')
