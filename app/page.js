"use client";
import { useState, useEffect, useRef } from 'react';

export default function Home() {
    const [fixed, setFixed] = useState([]);
    const [exclude, setExclude] = useState([]);
    const [minAc, setMinAc] = useState(5);
    const [isFilterOpen, setIsFilterOpen] = useState(false);
    const [activeSelector, setActiveSelector] = useState(null);
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);

    // 필터 상세 설명 매핑
    const filterLabels = {
        f1: "9 이하의 수가 3개 이상인 조합 제외",
        f2: "3개 이상의 연속 번호 포함 조합 제외",
        f3: "동일한 끝수가 4개 이상인 조합 제외",
        f4: "가로 한 줄(7칸 기준)에 4개 이상 집중 제외",
        f5: "세로 한 줄(7칸 기준)에 4개 이상 집중 제외",
        f6: "가장 낮은 수가 21 이상인 조합 제외",
        f7: "40 이상의 수가 3개 이상인 조합 제외",
        f8: "설정한 AC값 이하 조합 제외"
    };

    const [filters, setFilters] = useState({
        f1: true, f2: true, f3: true, f4: true, f5: true, f6: true, f7: true, f8: true
    });

    const selectorRef = useRef(null);

    useEffect(() => {
        const handleClickOutside = (e) => {
            if (selectorRef.current && !selectorRef.current.contains(e.target)) {
                setActiveSelector(null);
            }
        };
        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const handleFetch = async () => {
        setLoading(true);
        try {
            const res = await fetch('/api/index', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ fixed_nums: fixed, exclude_nums: exclude, min_ac: minAc, filters })
            });
            setResult(await res.json());
        } finally { setLoading(false); }
    };

    const renderGrid = (selected, onToggle, disabledList) => (
        <div className="number-grid">
            {Array.from({ length: 45 }, (_, i) => i + 1).map(n => (
                <button key={n}
                        className={`grid-item ${selected.includes(n) ? 'active' : ''} ${disabledList.includes(n) ? 'disabled' : ''}`}
                        onClick={() => {
                            if(disabledList.includes(n)) return;
                            onToggle(selected.includes(n) ? selected.filter(x => x !== n) : [...selected, n].sort((a,b)=>a-b));
                        }}
                >{n}</button>
            ))}
        </div>
    );

    return (
        <div className="container">
            <header className="brand-header">
                <h1>FortunaPick</h1>
                <p>프리미엄 알고리즘 조합 엔진</p>
            </header>

            <div className="main-layout" ref={selectorRef}>
                <div className="config-section">
                    <div className="input-group">
                        <label>필수 포함 번호</label>
                        <div className={`combo-box ${activeSelector === 'fixed' ? 'open' : ''}`} onClick={() => setActiveSelector('fixed')}>
                            {fixed.length ? fixed.map(n => <span key={n} className="tag">{n}</span>) : "번호를 선택하세요..."}
                        </div>
                        {activeSelector === 'fixed' && <div className="dropdown">{renderGrid(fixed, setFixed, exclude)}</div>}
                    </div>

                    <div className="input-group">
                        <label>제외 대상 번호</label>
                        <div className={`combo-box ${activeSelector === 'exclude' ? 'open' : ''}`} onClick={() => setActiveSelector('exclude')}>
                            {exclude.length ? exclude.map(n => <span key={n} className="tag secondary">{n}</span>) : "번호를 선택하세요..."}
                        </div>
                        {activeSelector === 'exclude' && <div className="dropdown">{renderGrid(exclude, setExclude, fixed)}</div>}
                    </div>

                    <div className="accordion-section">
                        <button className="accordion-trigger" onClick={() => setIsFilterOpen(!isFilterOpen)}>
                            <span>정밀 필터링 조건 설정</span>
                            <span>{isFilterOpen ? '−' : '+'}</span>
                        </button>
                        <div className={`accordion-content ${isFilterOpen ? 'visible' : ''}`}>
                            <div className="filter-list">
                                {Object.keys(filters).map((key) => (
                                    <label key={key} className="check-label">
                                        <input type="checkbox" checked={filters[key]} onChange={() => setFilters({...filters, [key]: !filters[key]})} />
                                        {filterLabels[key]}
                                    </label>
                                ))}
                                {filters.f8 && (
                                    <div className="ac-input">
                                        <span>최소 AC값 설정 (미입력 시 5)</span>
                                        <input type="number" value={minAc} onChange={e => setMinAc(e.target.value)} />
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>

                    <button className="generate-btn" onClick={handleFetch} disabled={loading}>
                        {loading ? "조합 분석 중..." : "최적 조합 추출"}
                    </button>
                </div>

                <div className="display-section">
                    {result ? (
                        <div className="result-card">
                            <h3>분석 결과 요약</h3>
                            <p>총 <strong>{result.total.toLocaleString()}</strong>개의 유효 조합이 검색되었습니다.</p>
                            <div className="recommendations">
                                {result.list.map((row, i) => (
                                    <div key={i} className="row-item">
                                        <span className="row-idx">{i+1}</span>
                                        <div className="balls">
                                            {row.map(num => <span key={num} className="ball">{num}</span>)}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    ) : (
                        <div className="empty-view">분석 조건을 설정하고 추출 버튼을 눌러주세요.</div>
                    )}
                </div>
            </div>
        </div>
    );
}