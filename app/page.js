"use client";
import { useState, useEffect, useRef } from 'react';

export default function Home() {
    const [fixed, setFixed] = useState([]);
    const [exclude, setExclude] = useState([]);
    const [minAc, setMinAc] = useState(5);
    const [isFilterOpen, setIsFilterOpen] = useState(false);
    const [activeSelector, setActiveSelector] = useState(null); // 'fixed' | 'exclude' | null
    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [filters, setFilters] = useState({
        f1: true, f2: true, f3: true, f4: true, f5: true, f6: true, f7: true, f8: true
    });

    const selectorRef = useRef(null);

    // 외부 클릭 시 콤보박스 닫기
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
                <p>Advanced Mathematical Combination Engine</p>
            </header>

            <div className="main-layout" ref={selectorRef}>
                {/* 설정 영역 */}
                <div className="config-section">
                    <div className="input-group">
                        <label>Required Elements</label>
                        <div className={`combo-box ${activeSelector === 'fixed' ? 'open' : ''}`} onClick={() => setActiveSelector('fixed')}>
                            {fixed.length ? fixed.map(n => <span key={n} className="tag">{n}</span>) : "Select numbers..."}
                        </div>
                        {activeSelector === 'fixed' && <div className="dropdown">{renderGrid(fixed, setFixed, exclude)}</div>}
                    </div>

                    <div className="input-group">
                        <label>Excluded Elements</label>
                        <div className={`combo-box ${activeSelector === 'exclude' ? 'open' : ''}`} onClick={() => setActiveSelector('exclude')}>
                            {exclude.length ? exclude.map(n => <span key={n} className="tag secondary">{n}</span>) : "Select numbers..."}
                        </div>
                        {activeSelector === 'exclude' && <div className="dropdown">{renderGrid(exclude, setExclude, fixed)}</div>}
                    </div>

                    {/* 아코디언 필터 영역 */}
                    <div className="accordion-section">
                        <button className="accordion-trigger" onClick={() => setIsFilterOpen(!isFilterOpen)}>
                            Filtering Constraints {isFilterOpen ? '−' : '+'}
                        </button>
                        <div className={`accordion-content ${isFilterOpen ? 'visible' : ''}`}>
                            <div className="filter-list">
                                {Object.keys(filters).map((key, idx) => (
                                    <label key={key} className="check-label">
                                        <input type="checkbox" checked={filters[key]} onChange={() => setFilters({...filters, [key]: !filters[key]})} />
                                        Condition {idx + 1}
                                    </label>
                                ))}
                                <div className="ac-input">
                                    <span>Minimum AC Value</span>
                                    <input type="number" value={minAc} onChange={e => setMinAc(e.target.value)} />
                                </div>
                            </div>
                        </div>
                    </div>

                    <button className="generate-btn" onClick={handleFetch} disabled={loading}>
                        {loading ? "Analyzing..." : "Generate Selection"}
                    </button>
                </div>

                {/* 결과 영역 */}
                <div className="display-section">
                    {result ? (
                        <div className="result-card">
                            <h3>Selection Overview</h3>
                            <p>Analyzed <strong>{result.total.toLocaleString()}</strong> viable combinations.</p>
                            <div className="recommendations">
                                {result.list.map((row, i) => (
                                    <div key={i} className="row-item">
                                        {row.map(num => <span key={num} className="ball">{num}</span>)}
                                    </div>
                                ))}
                            </div>
                        </div>
                    ) : (
                        <div className="empty-view">Waiting for generation...</div>
                    )}
                </div>
            </div>
        </div>
    );
}