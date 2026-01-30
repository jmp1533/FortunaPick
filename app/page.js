"use client";
import { useState } from 'react';

// --- 컴포넌트: 숫자 선택기 (드롭다운 스타일) ---
const NumberSelector = ({ label, selected, onToggle, excludeList = [] }) => {
    const [isOpen, setIsOpen] = useState(false);

    const toggleNumber = (num) => {
        onToggle(num);
    };

    return (
        <div className="selector-container">
            <label className="input-label">{label}</label>
            <div className="selector-box" onClick={() => setIsOpen(!isOpen)}>
                {selected.length === 0 ? (
                    <span className="placeholder">번호를 선택하세요</span>
                ) : (
                    <div className="chip-container">
                        {selected.map(n => <span key={n} className="chip">{n}</span>)}
                    </div>
                )}
                <span className="arrow">{isOpen ? '▲' : '▼'}</span>
            </div>

            {isOpen && (
                <div className="number-grid-dropdown">
                    {Array.from({ length: 45 }, (_, i) => i + 1).map(num => {
                        const isSelected = selected.includes(num);
                        const isDisabled = excludeList.includes(num);
                        return (
                            <button
                                key={num}
                                onClick={(e) => { e.stopPropagation(); toggleNumber(num); }}
                                disabled={isDisabled}
                                className={`grid-btn ${isSelected ? 'active' : ''} ${isDisabled ? 'disabled' : ''}`}
                            >
                                {num}
                            </button>
                        )
                    })}
                </div>
            )}
        </div>
    );
};

export default function Home() {
    // 상태 관리
    const [fixedNums, setFixedNums] = useState([]);
    const [excludeNums, setExcludeNums] = useState([]);
    const [minAc, setMinAc] = useState(5);

    // 필터 체크박스 상태 (기본값 True)
    const [filters, setFilters] = useState({
        under_10_limit: true,
        consecutive_limit: true,
        same_end_limit: true,
        row_limit: true,
        col_limit: true,
        min_num_limit: true,
        high_num_limit: true,
        ac_limit: true,
    });

    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);

    // 필터 토글 핸들러
    const toggleFilter = (key) => {
        setFilters(prev => ({ ...prev, [key]: !prev[key] }));
    };

    // 숫자 토글 핸들러
    const handleFixedToggle = (num) => {
        if (fixedNums.includes(num)) setFixedNums(fixedNums.filter(n => n !== num));
        else {
            if (fixedNums.length >= 5) return alert("필수 숫자는 최대 5개까지만 선택 가능합니다.");
            setFixedNums([...fixedNums, num].sort((a,b)=>a-b));
        }
    };

    const handleExcludeToggle = (num) => {
        if (excludeNums.includes(num)) setExcludeNums(excludeNums.filter(n => n !== num));
        else setExcludeNums([...excludeNums, num].sort((a,b)=>a-b));
    };

    const handleSubmit = async () => {
        setLoading(true);
        setResult(null);

        try {
            const res = await fetch('/api/index', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    fixed_nums: fixedNums,
                    exclude_nums: excludeNums,
                    min_ac: parseInt(minAc),
                    filters: filters
                })
            });
            const data = await res.json();
            setResult(data);
        } catch (e) {
            alert("오류가 발생했습니다.");
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
        <main className="main-container">
            <header className="header">
                <h1 className="brand-logo">FortunaPick</h1>
                <p className="subtitle">AI 기반 프리미엄 로또 분석기</p>
            </header>

            <div className="content-wrapper">
                {/* --- 왼쪽: 설정 패널 --- */}
                <div className="control-panel">
                    <section className="section-card">
                        <h3 className="section-title">🔢 번호 설정</h3>
                        <NumberSelector
                            label="필수 포함 숫자 (최대 5개)"
                            selected={fixedNums}
                            onToggle={handleFixedToggle}
                            excludeList={excludeNums}
                        />
                        <div style={{height: '15px'}}></div>
                        <NumberSelector
                            label="제외할 숫자"
                            selected={excludeNums}
                            onToggle={handleExcludeToggle}
                            excludeList={fixedNums}
                        />
                    </section>

                    <section className="section-card">
                        <h3 className="section-title">⚡ 필터링 조건</h3>
                        <div className="filter-grid">
                            <label className="checkbox-item">
                                <input type="checkbox" checked={filters.under_10_limit} onChange={() => toggleFilter('under_10_limit')} />
                                <span>9이하 숫자 3개 이상 제외</span>
                            </label>
                            <label className="checkbox-item">
                                <input type="checkbox" checked={filters.consecutive_limit} onChange={() => toggleFilter('consecutive_limit')} />
                                <span>연속수 3개 이상 제외</span>
                            </label>
                            <label className="checkbox-item">
                                <input type="checkbox" checked={filters.same_end_limit} onChange={() => toggleFilter('same_end_limit')} />
                                <span>동일 끝수 4개 이상 제외</span>
                            </label>
                            <label className="checkbox-item">
                                <input type="checkbox" checked={filters.row_limit} onChange={() => toggleFilter('row_limit')} />
                                <span>가로 4개 이상 제외</span>
                            </label>
                            <label className="checkbox-item">
                                <input type="checkbox" checked={filters.col_limit} onChange={() => toggleFilter('col_limit')} />
                                <span>세로 4개 이상 제외</span>
                            </label>
                            <label className="checkbox-item">
                                <input type="checkbox" checked={filters.min_num_limit} onChange={() => toggleFilter('min_num_limit')} />
                                <span>최소수 21 이상 제외</span>
                            </label>
                            <label className="checkbox-item">
                                <input type="checkbox" checked={filters.high_num_limit} onChange={() => toggleFilter('high_num_limit')} />
                                <span>40대 숫자 3개 이상 제외</span>
                            </label>
                            <label className="checkbox-item">
                                <input type="checkbox" checked={filters.ac_limit} onChange={() => toggleFilter('ac_limit')} />
                                <span>AC값 필터 적용</span>
                            </label>
                        </div>
                        {filters.ac_limit && (
                            <div style={{marginTop: '10px'}}>
                                <label className="input-label" style={{fontSize: '12px'}}>AC 최소값 (이하 제외)</label>
                                <input
                                    type="number"
                                    value={minAc}
                                    onChange={(e) => setMinAc(e.target.value)}
                                    className="simple-input"
                                />
                            </div>
                        )}
                    </section>

                    <button onClick={handleSubmit} disabled={loading} className="action-btn">
                        {loading ? 'Fortuna 분석 중...' : '조합 추출 시작'}
                    </button>
                </div>

                {/* --- 오른쪽: 결과 패널 --- */}
                <div className="result-panel">
                    {result ? (
                        <div className="result-content">
                            <h2 className="result-title">✨ 분석 결과</h2>
                            <p className="result-summary">
                                Fortuna 알고리즘이 <strong>{result.total_valid_count.toLocaleString()}</strong>개의 조합 중 최적의 10개를 선별했습니다.
                            </p>
                            <div className="lotto-list">
                                {result.recommendations.map((combo, idx) => (
                                    <div key={idx} className="lotto-row">
                                        <span className="row-badge">PICK {idx + 1}</span>
                                        <div className="balls">
                                            {combo.map(num => (
                                                <span key={num} className="ball" style={{backgroundColor: getBallColor(num)}}>{num}</span>
                                            ))}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ) : (
                        <div className="empty-state">
                            <div className="logo-placeholder">FP</div>
                            <p>조건을 설정하고 추출 버튼을 눌러주세요.</p>
                        </div>
                    )}
                </div>
            </div>
        </main>
    );
}