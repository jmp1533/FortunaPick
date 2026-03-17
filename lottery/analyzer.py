import os
import re
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter

try:
    import pandas as pd  # type: ignore
except Exception:
    pd = None


class LotteryAnalyzer:
    def __init__(self, excel_filename='winningNumbers.xlsx'):
        self.excel_path = os.path.join(os.path.dirname(__file__), excel_filename)
        self.df = self._load_data()
        self.analysis_results = {}
        if not self.df.empty:
            self._perform_analysis()

    def _resolve_excel_path(self):
        if os.path.exists(self.excel_path):
            return self.excel_path
        potential_path = os.path.join('/var/task/lottery', os.path.basename(self.excel_path))
        if os.path.exists(potential_path):
            self.excel_path = potential_path
            return potential_path
        return self.excel_path

    def _load_data(self):
        try:
            self._resolve_excel_path()
            if pd is not None:
                return self._load_with_pandas()
            return self._load_with_builtin_parser()
        except Exception as e:
            print(f"Error loading or parsing Excel data: {e}")
            return self._empty_frame()

    def _empty_frame(self):
        if pd is not None:
            return pd.DataFrame(columns=['회차', 'winning_numbers', 'bonus_number'])
        return SimpleFrame([])

    def _load_with_pandas(self):
        df = pd.read_excel(self.excel_path, engine='openpyxl')
        df['회차'] = pd.to_numeric(
            df['회차'].astype(str).str.replace(',', '').str.replace('회', '').str.strip(),
            errors='coerce'
        )
        df.dropna(subset=['회차'], inplace=True)
        df = df[df['회차'] > 0]

        num_cols = [col for col in df.columns if '번호' in str(col) and col != '보너스']
        if len(num_cols) < 6:
            num_cols = df.columns[2:8].tolist()

        for col in num_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')

        df.dropna(subset=num_cols, inplace=True)
        for col in num_cols:
            df = df[(df[col] >= 1) & (df[col] <= 45)]

        df['winning_numbers'] = df[num_cols].apply(lambda x: sorted(int(v) for v in x.tolist()), axis=1)
        df['bonus_number'] = pd.to_numeric(df['보너스'], errors='coerce').fillna(0).astype(int)
        return df.sort_values(by='회차', ascending=False).reset_index(drop=True)

    def _load_with_builtin_parser(self):
        rows = self._read_xlsx_rows(self.excel_path)
        parsed_rows = []

        for row in rows[1:]:
            if len(row) < 9:
                continue
            round_num = self._safe_int(row[1])
            numbers = [self._safe_int(value) for value in row[2:8]]
            bonus = self._safe_int(row[8])

            if not round_num or any(n is None or not (1 <= n <= 45) for n in numbers) or bonus is None:
                continue

            parsed_rows.append({
                '회차': int(round_num),
                'winning_numbers': sorted(int(n) for n in numbers),
                'bonus_number': int(bonus),
            })

        parsed_rows.sort(key=lambda x: x['회차'], reverse=True)
        return SimpleFrame(parsed_rows)

    def _read_xlsx_rows(self, path):
        ns = {'main': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
        with zipfile.ZipFile(path) as zf:
            shared_strings = []
            if 'xl/sharedStrings.xml' in zf.namelist():
                root = ET.fromstring(zf.read('xl/sharedStrings.xml'))
                for si in root.findall('main:si', ns):
                    text = ''.join(node.text or '' for node in si.iterfind('.//main:t', ns))
                    shared_strings.append(text)

            sheet_root = ET.fromstring(zf.read('xl/worksheets/sheet1.xml'))
            rows = []
            for row in sheet_root.findall('.//main:sheetData/main:row', ns):
                values = []
                for cell in row.findall('main:c', ns):
                    cell_type = cell.attrib.get('t')
                    raw = cell.find('main:v', ns)
                    value = raw.text if raw is not None else ''
                    if cell_type == 's' and value != '':
                        value = shared_strings[int(value)]
                    values.append(value)
                rows.append(values)
            return rows

    def _safe_int(self, value):
        if value is None:
            return None
        text = str(value).replace(',', '').replace('회', '').strip()
        if not text:
            return None
        match = re.match(r'^-?\d+(?:\.0+)?$', text)
        if not match:
            return None
        return int(float(text))

    def _perform_analysis(self):
        if self.df.empty:
            return

        all_numbers = [num for sublist in self.df['winning_numbers'] for num in sublist]
        self.analysis_results['number_frequencies'] = Counter(all_numbers)

        recent_draws_count = min(100, len(self.df))
        recent_numbers = [num for sublist in self.df.head(recent_draws_count)['winning_numbers'] for num in sublist]
        self.analysis_results['hot_cold_numbers'] = Counter(recent_numbers)

        sums = [sum(nums) for nums in self.df['winning_numbers']]
        ac_values = [self._calculate_ac(nums) for nums in self.df['winning_numbers']]
        self.analysis_results['sum_distribution'] = describe_numbers(sums)
        self.analysis_results['ac_distribution'] = describe_numbers(ac_values)
        self.analysis_results['odd_even_distribution'] = Counter(self.df['winning_numbers'].apply(self._get_odd_even_ratio))
        self.analysis_results['high_low_distribution'] = Counter(self.df['winning_numbers'].apply(self._get_high_count))
        self.analysis_results['consecutive_pairs_count'] = sum(1 for nums in self.df['winning_numbers'] if self._check_consecutive_pair(nums))
        self.analysis_results['consecutive_triplets_count'] = sum(1 for nums in self.df['winning_numbers'] if self._check_consecutive_triplet(nums))
        self.analysis_results['same_ending_counts'] = Counter(self.df['winning_numbers'].apply(self._get_same_ending_max_count))

        last_seen = {num: -1 for num in range(1, 46)}
        for idx, row in self.df.iterrows():
            for num in row['winning_numbers']:
                if last_seen[num] == -1:
                    last_seen[num] = idx
        self.analysis_results['last_seen_draws_ago'] = last_seen
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
        return sum(1 for n in numbers if n >= 23)

    def _check_consecutive_pair(self, numbers):
        sorted_nums = sorted(numbers)
        for i in range(1, len(sorted_nums)):
            if sorted_nums[i] == sorted_nums[i - 1] + 1:
                return True
        return False

    def _check_consecutive_triplet(self, numbers):
        sorted_nums = sorted(numbers)
        consecutive = 1
        for i in range(1, len(sorted_nums)):
            if sorted_nums[i] == sorted_nums[i - 1] + 1:
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
            '41-45': sum(1 for n in numbers if 41 <= n <= 45),
        }
        return '-'.join(str(decades[key]) for key in sorted(decades.keys()))

    def get_analysis_results(self):
        return self.analysis_results

    def get_latest_draws(self, count=10):
        if self.df.empty:
            return []
        return self.df.head(count)[['회차', 'winning_numbers', 'bonus_number']].to_dict(orient='records')


class SimpleSeries(list):
    def apply(self, func):
        return [func(item) for item in self]


class SimpleSubset:
    def __init__(self, rows, columns):
        self.rows = rows
        self.columns = columns

    def to_dict(self, orient='records'):
        if orient != 'records':
            raise ValueError('Only records orient is supported.')
        return [{col: row[col] for col in self.columns} for row in self.rows]


class SimpleFrame:
    def __init__(self, rows):
        self.rows = rows

    @property
    def empty(self):
        return len(self.rows) == 0

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, key):
        if isinstance(key, list):
            return SimpleSubset(self.rows, key)
        return SimpleSeries([row[key] for row in self.rows])

    def head(self, count):
        return SimpleFrame(self.rows[:count])

    def iterrows(self):
        for idx, row in enumerate(self.rows):
            yield idx, row


def describe_numbers(values):
    if not values:
        return {'count': 0, 'mean': 0, 'min': 0, 'max': 0}
    count = len(values)
    mean = sum(values) / count
    variance = sum((v - mean) ** 2 for v in values) / count
    std = variance ** 0.5
    ordered = sorted(values)

    def percentile(p):
        if count == 1:
            return ordered[0]
        index = (count - 1) * p
        lower = int(index)
        upper = min(lower + 1, count - 1)
        weight = index - lower
        return ordered[lower] * (1 - weight) + ordered[upper] * weight

    return {
        'count': count,
        'mean': mean,
        'std': std,
        'min': ordered[0],
        '25%': percentile(0.25),
        '50%': percentile(0.5),
        '75%': percentile(0.75),
        'max': ordered[-1],
    }
