"use client";
import { useState } from 'react';

export default function Home() {
    const [fixedNum, setFixedNum] = useState('');
    const [excludeInput, setExcludeInput] = useState('');
    const [minAc, setMinAc] = useState(5);
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);

    const handleSubmit = async () => {
        if (!fixedNum || fixedNum < 1 || fixedNum > 45) {
            alert("필수 포함 숫자(1~45)를 입력해주세요.");
            return;
        }
        setLoading(true);
        setResult(null);

        const excludeNums = excludeInput
            .split(/[\s,]+/)
            .map(n => parseInt(n))
            .filter(n => !isNaN(n) && n >= 1 && n <= 45);

        try {
            const res = await fetch('/api/index', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    fixed_num: parseInt(fixedNum),
                    exclude_nums: excludeNums,
                    min_ac: parseInt(minAc)
                })
            });
            const data = await res.json();
            setResult(data);
        } catch (e) {
            alert("오류가 발생했습니다. 다시 시도해주세요.");
        } finally {
            setLoading(false);
        }
    };

    const getBallColor = (num) => {
        if (num <= 10) return '#fbc400';
        if (num <= 20) return '#69c8f2';
        if (num <= 30) return '#ff7272';
        if (num <= 40) return '#aaaaaa';
        return '#b0d840';
    };

    return (
        <main className="container">
            <h1 className="title">🎱 로또 조합 분석기</h1>

            <div className="card">
                <div className="input-group">
                    <label>필수 포함 숫자 (1개)</label>
                    <input
                        type="number"
                        value={fixedNum}
                        onChange={(e) => setFixedNum(e.target.value)}
                        placeholder="예: 14"
                    />
                </div>

                <div className="input-group">
                    <label>제외할 숫자 (쉼표로 구분)</label>
                    <input
                        type="text"
                        value={excludeInput}
                        onChange={(e) => setExcludeInput(e.target.value)}
                        placeholder="예: 25, 30, 41"
                    />
                </div>

                <div className="input-group">
                    <label>AC 필터 (이 값 이하는 제외)</label>
                    <input
                        type="number"
                        value={minAc}
                        onChange={(e) => setMinAc(e.target.value)}
                        placeholder="기본값: 5"
                    />
                </div>

                <button onClick={handleSubmit} disabled={loading} className="btn">
                    {loading ? '분석 중입니다...' : '조합 추출하기'}
                </button>
            </div>

            {result && (
                <div className="result-area">
                    <h2>분석 결과</h2>
                    <p className="summary">
                        조건 만족 조합: <strong>{result.total_valid_count.toLocaleString()}</strong>개
                    </p>

                    <div className="recommendations">
                        {result.recommendations.map((combo, idx) => (
                            <div key={idx} className="lotto-row">
                                <span className="row-num">{idx + 1}</span>
                                {combo.map(num => (
                                    <span key={num} className="ball" style={{backgroundColor: getBallColor(num)}}>
                    {num}
                  </span>
                                ))}
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </main>
    );
}