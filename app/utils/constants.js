// 로또 번호 색상 (한국 로또 기준)
export const getBallColor = (num) => {
  if (num <= 10) return { bg: 'var(--ball-yellow)', text: '#000' };
  if (num <= 20) return { bg: 'var(--ball-blue)', text: '#fff' };
  if (num <= 30) return { bg: 'var(--ball-red)', text: '#fff' };
  if (num <= 40) return { bg: 'var(--ball-gray)', text: '#fff' };
  return { bg: 'var(--ball-green)', text: '#fff' };
};

// 필터 정의
export const FILTER_DEFINITIONS = {
  f1: {
    id: 'f1',
    name: '저번대 제한',
    description: '1~9 범위 숫자가 3개 이상인 조합 제외',
    icon: '🔢'
  },
  f2: {
    id: 'f2',
    name: '연번 제한',
    description: '3개 이상 연속된 번호 포함 조합 제외',
    icon: '📊'
  },
  f3: {
    id: 'f3',
    name: '끝수 제한',
    description: '동일 끝자리 숫자 4개 이상 조합 제외',
    icon: '🔄'
  },
  f4: {
    id: 'f4',
    name: '가로 집중 제한',
    description: '7열 배열 기준 가로 한 줄에 4개 이상 집중 제외',
    icon: '➡️'
  },
  f5: {
    id: 'f5',
    name: '세로 집중 제한',
    description: '7열 배열 기준 세로 한 줄에 4개 이상 집중 제외',
    icon: '⬇️'
  },
  f6: {
    id: 'f6',
    name: '최소값 제한',
    description: '6개 중 최솟값이 21 이상인 조합 제외',
    icon: '⬆️'
  },
  f7: {
    id: 'f7',
    name: '고번대 제한',
    description: '40~45 범위 숫자가 3개 이상인 조합 제외',
    icon: '📈'
  },
  f8: {
    id: 'f8',
    name: 'AC값 제한',
    description: '설정한 AC값 이하인 조합 제외',
    icon: '🎯'
  }
};

// AC값 계산
export const calculateAC = (numbers) => {
  const nums = [...numbers].sort((a, b) => a - b);
  const diffs = new Set();
  for (let i = 0; i < nums.length; i++) {
    for (let j = i + 1; j < nums.length; j++) {
      diffs.add(Math.abs(nums[j] - nums[i]));
    }
  }
  return diffs.size - 5;
};

// 홀수/짝수 비율 계산
export const getOddEvenRatio = (numbers) => {
  const odd = numbers.filter(n => n % 2 !== 0).length;
  return { odd, even: numbers.length - odd };
};

// 고/저 비율 계산
export const getHighLowRatio = (numbers) => {
  const high = numbers.filter(n => n >= 23).length;
  return { high, low: numbers.length - high };
};

// 번호대 분포 계산
export const getDecadeDistribution = (numbers) => {
  const ranges = {
    '1-10': 0,
    '11-20': 0,
    '21-30': 0,
    '31-40': 0,
    '41-45': 0
  };
  numbers.forEach(n => {
    if (n <= 10) ranges['1-10']++;
    else if (n <= 20) ranges['11-20']++;
    else if (n <= 30) ranges['21-30']++;
    else if (n <= 40) ranges['31-40']++;
    else ranges['41-45']++;
  });
  return ranges;
};

// 합계 계산
export const getSum = (numbers) => numbers.reduce((a, b) => a + b, 0);

// 연속번호 개수 계산
export const getConsecutiveCount = (numbers) => {
  const sorted = [...numbers].sort((a, b) => a - b);
  let maxConsec = 1;
  let current = 1;
  for (let i = 1; i < sorted.length; i++) {
    if (sorted[i] === sorted[i-1] + 1) {
      current++;
      maxConsec = Math.max(maxConsec, current);
    } else {
      current = 1;
    }
  }
  return maxConsec;
};
