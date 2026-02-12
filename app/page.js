"use client";
import { useState, useEffect, useRef, useCallback } from 'react';
// import AdBanner from './components/AdBanner'; // AdSense temporarily disabled
// import { ADSENSE_CONFIG } from './utils/ads'; // AdSense temporarily disabled
import { 
  FILTER_DEFINITIONS, 
  calculateAC, 
  getOddEvenRatio, 
  getDecadeDistribution,
  getSum
} from './utils/constants';

// 공 색상 클래스 반환
const getBallColorClass = (num) => {
  if (num <= 10) return 'ball-yellow';
  if (num <= 20) return 'ball-blue';
  if (num <= 30) return 'ball-red';
  if (num <= 40) return 'ball-gray';
  return 'ball-green';
};

// SVG 아이콘 컴포넌트들
const Icons = {
  Logo: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="10"/>
      <path d="M12 6v6l4 2"/>
    </svg>
  ),
  Check: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="20,6 9,17 4,12" />
    </svg>
  ),
  Settings: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"/>
    </svg>
  ),
  Sparkle: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 3l1.5 4.5L18 9l-4.5 1.5L12 15l-1.5-4.5L6 9l4.5-1.5L12 3z"/>
      <path d="M5 19l1 3 1-3 3-1-3-1-1-3-1 3-3 1 3 1z"/>
    </svg>
  ),
  Star: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
    </svg>
  ),
  StarFilled: () => (
    <svg viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" strokeWidth="2">
      <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
    </svg>
  ),
  Copy: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
    </svg>
  ),
  List: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/>
    </svg>
  ),
  Grid: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
    </svg>
  ),
  Chart: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>
    </svg>
  ),
  Search: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
    </svg>
  )
};

// 동행복권 스타일 로또 공 컴포넌트
const LottoBall = ({ number, small = false, isCarryOver = false }) => {
  const colorClass = getBallColorClass(number);
  return (
    <span className={`lotto-ball ${colorClass} ${small ? 'small' : ''} ${isCarryOver ? 'carry-over' : ''}`}>
      {number}
      {isCarryOver && (
        <span className="carry-over-star">
          <svg viewBox="0 0 24 24" fill="currentColor" stroke="none">
            <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
          </svg>
        </span>
      )}
    </span>
  );
};

// 토스트 컴포넌트
const Toast = ({ message, visible }) => (
  <div className={`toast ${visible ? 'visible' : ''}`}>
    <span className="toast-message">{message}</span>
  </div>
);

// 통계 카드 컴포넌트
const StatCard = ({ value, label }) => (
  <div className="stat-card">
    <div className="stat-value">{value}</div>
    <div className="stat-label">{label}</div>
  </div>
);

// 도넛 차트 컴포넌트
const DonutChart = ({ value, total, label, primaryLabel, secondaryLabel }) => {
  const percentage = total > 0 ? (value / total) * 100 : 0;
  const circumference = 2 * Math.PI * 40;
  const offset = circumference - (percentage / 100) * circumference;
  
  return (
    <div className="donut-container">
      <div className="donut-chart">
        <svg width="100" height="100" viewBox="0 0 100 100">
          <circle className="donut-bg" cx="50" cy="50" r="40" />
          <circle 
            className="donut-fill" 
            cx="50" 
            cy="50" 
            r="40"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
          />
        </svg>
        <div className="donut-center">
          <div className="donut-value">{value}:{total - value}</div>
          <div className="donut-label">{label}</div>
        </div>
      </div>
      <div className="donut-legend">
        <div className="legend-item">
          <div className="legend-dot primary"></div>
          <span>{primaryLabel}: {value}</span>
        </div>
        <div className="legend-item">
          <div className="legend-dot secondary"></div>
          <span>{secondaryLabel}: {total - value}</span>
        </div>
      </div>
    </div>
  );
};

// 막대 차트 컴포넌트
const BarChart = ({ data, maxValue }) => (
  <div className="bar-chart">
    {Object.entries(data).map(([label, value]) => (
      <div className="bar-row" key={label}>
        <div className="bar-label">{label}</div>
        <div className="bar-track">
          <div 
            className="bar-fill"
            style={{ width: `${Math.max((value / maxValue) * 100, 12)}%` }}
          >
            {value}
          </div>
        </div>
      </div>
    ))}
  </div>
);

// 콤보박스 드롭다운 컴포넌트
const NumberComboBox = ({ 
  label, 
  selectedNumbers, 
  disabledNumbers, 
  onToggle, 
  onClear,
  tagClass,
  isOpen,
  onToggleOpen
}) => {
  const wrapperRef = useRef(null);
  const [position, setPosition] = useState('bottom');

  // 드롭다운 위치 계산
  useEffect(() => {
    if (isOpen && wrapperRef.current) {
      const rect = wrapperRef.current.getBoundingClientRect();
      const dropdownHeight = 220;
      const spaceBelow = window.innerHeight - rect.bottom - 20;
      const spaceAbove = rect.top - 20;
      
      if (spaceBelow < dropdownHeight && spaceAbove > spaceBelow) {
        setPosition('top');
      } else {
        setPosition('bottom');
      }
    }
  }, [isOpen]);

  return (
    <div className="input-group">
      <div className="input-label">
        <span className="input-label-text">{label}</span>
        {selectedNumbers.length > 0 && (
          <button className="clear-btn" onClick={(e) => { e.stopPropagation(); onClear(); }}>
            초기화
          </button>
        )}
      </div>
      <div className="combo-wrapper" ref={wrapperRef}>
        <div 
          className={`selector-box ${isOpen ? 'active' : ''}`}
          onClick={onToggleOpen}
        >
          {selectedNumbers.length ? (
            selectedNumbers.map(n => (
              <span key={n} className={`number-tag ${tagClass}`}>{n}</span>
            ))
          ) : (
            <span className="selector-placeholder">클릭하여 번호 선택...</span>
          )}
        </div>
        
        {isOpen && (
          <div className={`dropdown-panel position-${position}`}>
            <div className="number-grid">
              {Array.from({ length: 45 }, (_, i) => i + 1).map(n => (
                <button
                  key={n}
                  className={`grid-number ${selectedNumbers.includes(n) ? 'selected' : ''} ${disabledNumbers.includes(n) ? 'disabled' : ''}`}
                  onClick={(e) => {
                    e.stopPropagation();
                    if (!disabledNumbers.includes(n)) {
                      onToggle(n);
                    }
                  }}
                  disabled={disabledNumbers.includes(n)}
                >
                  {n}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// 분석 화면 컴포넌트
const AnalysisView = ({ historyData, loading, error }) => {
  const [activeTab, setActiveTab] = useState('cold'); // 'cold' or 'history'
  const [searchTerm, setSearchTerm] = useState('');
  const [searchNumberInput, setSearchNumberInput] = useState('');
  const [searchNumbers, setSearchNumbers] = useState([]);
  const [searchIncludeBonus, setSearchIncludeBonus] = useState(true);
  const [filteredHistory, setFilteredHistory] = useState([]);
  
  const [coldPeriod, setColdPeriod] = useState(10);
  const [coldIncludeBonus, setColdIncludeBonus] = useState(true);
  const [coldNumbers, setColdNumbers] = useState([]);

  // 검색 필터링 및 이월 번호 계산
  useEffect(() => {
    if (historyData && historyData.history) {
      let newFilteredHistory = historyData.history;

      // 1. 회차 검색
      if (searchTerm) {
        const term = searchTerm.toLowerCase();
        newFilteredHistory = newFilteredHistory.filter(item => 
          item.round.toString().includes(term)
        );
      }

      // 2. 번호 검색
      if (searchNumbers.length > 0) {
        newFilteredHistory = newFilteredHistory.filter(item => {
          const numbersToSearch = new Set(item.numbers);
          if (searchIncludeBonus) {
            numbersToSearch.add(item.bonus);
          }
          return searchNumbers.every(num => numbersToSearch.has(num));
        });
      }

      // 이월 번호 계산 (이전 회차 번호와 비교)
      // historyData.history는 내림차순 정렬되어 있으므로, 현재 인덱스 + 1이 이전 회차임
      const historyWithCarryOver = newFilteredHistory.map((item) => {
        // 전체 히스토리에서 현재 아이템의 인덱스를 찾음 (필터링 전 원본 데이터 기준)
        const originalIndex = historyData.history.findIndex(h => h.round === item.round);
        
        // 이전 회차 데이터가 있는지 확인 (마지막 회차가 아니면 존재)
        let carryOverNumbers = new Set();
        
        if (originalIndex < historyData.history.length - 1) {
          const prevRound = historyData.history[originalIndex + 1];
          const prevNumbers = new Set([...prevRound.numbers, prevRound.bonus]);
          
          // 현재 회차 번호 중 이전 회차에 포함된 번호 찾기
          item.numbers.forEach(num => {
            if (prevNumbers.has(num)) carryOverNumbers.add(num);
          });
          if (prevNumbers.has(item.bonus)) carryOverNumbers.add(item.bonus);
        }
        
        return {
          ...item,
          carryOverNumbers
        };
      });

      setFilteredHistory(historyWithCarryOver);
    }
  }, [searchTerm, searchNumbers, searchIncludeBonus, historyData]);

  // 미출현 번호 계산
  useEffect(() => {
    if (historyData && historyData.history) {
      const recentRounds = historyData.history.slice(0, coldPeriod);
      const appearedNumbers = new Set();
      
      recentRounds.forEach(round => {
        round.numbers.forEach(num => appearedNumbers.add(num));
        if (coldIncludeBonus) {
          appearedNumbers.add(round.bonus);
        }
      });
      
      const missing = Array.from({ length: 45 }, (_, i) => i + 1)
        .filter(num => !appearedNumbers.has(num));
        
      setColdNumbers(missing);
    }
  }, [historyData, coldPeriod, coldIncludeBonus]);

  const handleSearchNumberAdd = () => {
    if (!searchNumberInput.trim()) return;
    
    const nums = searchNumberInput.split(',')
      .map(n => parseInt(n.trim()))
      .filter(n => !isNaN(n) && n > 0 && n <= 45);
      
    if (nums.length > 0) {
      setSearchNumbers(prev => {
        const newSet = new Set([...prev, ...nums]);
        return Array.from(newSet).sort((a, b) => a - b);
      });
      setSearchNumberInput('');
    }
  };

  const removeSearchNumber = (num) => {
    setSearchNumbers(prev => prev.filter(n => n !== num));
  };

  if (loading) {
    return (
      <div className="loading-container">
        <span className="loading-spinner"></span>
        <p>당첨 이력을 불러오는 중...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-container">
        <p>{error}</p>
        {error.includes('JSON') && <p className="text-sm text-gray-500 mt-2">서버 응답 형식이 올바르지 않습니다.</p>}
      </div>
    );
  }

  if (!historyData) return null;

  return (
    <div className="analysis-view">
      {/* 최신 회차 정보 */}
      <div className="hero-section">
        <div className="hero-content">
          <div className="hero-badge">최신 회차</div>
          <h2 className="hero-title">{historyData.latestRound}회 당첨결과</h2>
          <div className="hero-balls">
            {historyData.history[0]?.numbers.map(num => (
              <LottoBall key={num} number={num} />
            ))}
            <span className="plus-sign">+</span>
            <LottoBall number={historyData.history[0]?.bonus} />
          </div>
        </div>
      </div>

      {/* 광고 영역 (상단) - Temporarily Disabled */}
      {/* <AdBanner slotId={ADSENSE_CONFIG.SLOTS.BANNER_TOP} /> */}

      {/* 분석 탭 네비게이션 */}
      <div className="tabs">
        <button 
          className={`tab-btn ${activeTab === 'cold' ? 'active' : ''}`}
          onClick={() => setActiveTab('cold')}
        >
          미출현 번호 분석
        </button>
        <button 
          className={`tab-btn ${activeTab === 'history' ? 'active' : ''}`}
          onClick={() => setActiveTab('history')}
        >
          회차별 당첨 이력
        </button>
      </div>

      {/* 미출현 번호 분석 탭 */}
      {activeTab === 'cold' && (
        <div className="analysis-grid">
          <div className="chart-card" style={{ gridColumn: '1 / -1' }}>
            <div className="chart-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem', flexWrap: 'wrap', gap: '10px' }}>
              <div className="chart-title" style={{ marginBottom: 0 }}>미출현 번호</div>
              <div className="chart-controls" style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
                <select 
                  value={coldPeriod} 
                  onChange={(e) => setColdPeriod(Number(e.target.value))}
                  style={{ padding: '6px 10px', borderRadius: '6px', border: '1px solid #ddd', fontSize: '0.9rem' }}
                >
                  {[5, 10, 15, 20, 25, 30].map(p => (
                    <option key={p} value={p}>최근 {p}회</option>
                  ))}
                </select>
                <label className="checkbox-label" style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.9rem', cursor: 'pointer', userSelect: 'none' }}>
                  <input 
                    type="checkbox" 
                    checked={coldIncludeBonus} 
                    onChange={(e) => setColdIncludeBonus(e.target.checked)} 
                    style={{ width: '16px', height: '16px' }}
                  />
                  보너스 포함
                </label>
              </div>
            </div>
            <div className="cold-numbers">
              {coldNumbers.length > 0 ? (
                coldNumbers.map(num => (
                  <span key={num} className="cold-number-tag">{num}</span>
                ))
              ) : (
                <span className="empty-text">해당 기간 동안 모든 번호가 출현했습니다.</span>
              )}
            </div>
          </div>
          
          {/* 광고 영역 (중간) - Temporarily Disabled */}
          {/* <div style={{ gridColumn: '1 / -1' }}>
            <AdBanner slotId={ADSENSE_CONFIG.SLOTS.BANNER_MIDDLE} />
          </div> */}
        </div>
      )}

      {/* 회차별 당첨 이력 탭 */}
      {activeTab === 'history' && (
        <div className="card history-list-card">
          <div className="card-header">
            <div className="card-title">
              <Icons.List />
              회차별 당첨 이력
            </div>
          </div>
          
          {/* 검색 컨트롤 영역 */}
          <div style={{ padding: '16px', borderBottom: '1px solid var(--border)', background: 'var(--bg-elevated)' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {/* 회차 검색 */}
              <div className="search-box" style={{ background: 'white' }}>
                <Icons.Search />
                <input 
                  type="text" 
                  placeholder="회차 검색 (예: 1000)" 
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  style={{ width: '100%' }}
                />
              </div>
              
              {/* 번호 검색 */}
              <div style={{ display: 'flex', gap: '8px' }}>
                <div className="search-box" style={{ background: 'white', flex: 1 }}>
                  <Icons.Search />
                  <input 
                    type="text" 
                    placeholder="번호 입력 (예: 1, 7, 45)"
                    value={searchNumberInput}
                    onChange={(e) => setSearchNumberInput(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter') handleSearchNumberAdd();
                    }}
                    style={{ width: '100%' }}
                  />
                </div>
                <button 
                  onClick={handleSearchNumberAdd}
                  style={{
                    padding: '0 16px',
                    background: 'var(--primary)',
                    color: 'white',
                    border: 'none',
                    borderRadius: '8px',
                    fontWeight: '600',
                    cursor: 'pointer'
                  }}
                >
                  추가
                </button>
              </div>

              {/* 선택된 검색 번호 태그들 */}
              {searchNumbers.length > 0 && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px', alignItems: 'center' }}>
                  {searchNumbers.map(num => (
                    <div key={num} style={{ 
                      display: 'flex', 
                      alignItems: 'center', 
                      gap: '4px', 
                      background: 'var(--primary-bg)', 
                      color: 'var(--primary)', 
                      padding: '4px 8px', 
                      borderRadius: '6px',
                      fontSize: '0.85rem',
                      fontWeight: '600'
                    }}>
                      <span>{num}</span>
                      <button 
                        onClick={() => removeSearchNumber(num)}
                        style={{ border: 'none', background: 'transparent', color: 'inherit', cursor: 'pointer', padding: 0, display: 'flex' }}
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                  <button 
                    onClick={() => setSearchNumbers([])}
                    style={{ fontSize: '0.8rem', color: 'var(--text-muted)', background: 'transparent', border: 'none', cursor: 'pointer', textDecoration: 'underline' }}
                  >
                    전체 삭제
                  </button>
                </div>
              )}

              {/* 옵션 */}
              <label className="checkbox-label" style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '0.9rem', cursor: 'pointer', userSelect: 'none' }}>
                <input 
                  type="checkbox" 
                  checked={searchIncludeBonus} 
                  onChange={(e) => setSearchIncludeBonus(e.target.checked)} 
                  style={{ width: '16px', height: '16px' }}
                />
                검색 시 보너스 번호 포함
              </label>
            </div>
          </div>

          <div className="history-list">
            <div className="history-header-row">
              <span className="col-round">회차</span>
              <span className="col-numbers">당첨번호</span>
              <span className="col-bonus">보너스</span>
              <span className="col-stats">통계 (합/홀짝/AC)</span>
            </div>
            <div className="history-items">
              {filteredHistory.length > 0 ? (
                filteredHistory.map((item, index) => (
                  <div key={item.round}>
                    {/* 10개 항목마다 광고 삽입 - Temporarily Disabled */}
                    {/* {index > 0 && index % 10 === 0 && (
                      <AdBanner 
                        slotId={ADSENSE_CONFIG.SLOTS.IN_FEED_LIST} 
                        format="fluid"
                        layoutKey={ADSENSE_CONFIG.LAYOUT_KEYS.IN_FEED_LIST}
                        style={{ margin: '10px 0' }} 
                      />
                    )} */}
                    <div className="history-item">
                      <span className="col-round">{item.round}회</span>
                      <div className="col-numbers">
                        {item.numbers.map(num => (
                          <LottoBall 
                            key={num} 
                            number={num} 
                            small 
                            isCarryOver={item.carryOverNumbers && item.carryOverNumbers.has(num)} 
                          />
                        ))}
                      </div>
                      <span className="col-bonus">
                        <LottoBall 
                          number={item.bonus} 
                          small 
                          isCarryOver={item.carryOverNumbers && item.carryOverNumbers.has(item.bonus)} 
                        />
                      </span>
                      <div className="col-stats">
                        {item.stats ? (
                          <>
                            <span className="meta-badge">합 {item.stats.sum}</span>
                            <span className="meta-badge">{item.stats.oddEven}</span>
                            <span className="meta-badge highlight">AC {item.stats.ac}</span>
                          </>
                        ) : (
                          <span className="text-muted">-</span>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              ) : (
                <div style={{ padding: '40px', textAlign: 'center', color: 'var(--text-muted)' }}>
                  검색 결과가 없습니다.
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default function Home() {
  // 상태 관리
  const [activeView, setActiveView] = useState('recommend'); // 'recommend' or 'analysis'
  
  // 추천 관련 상태
  const [includeNumbers, setIncludeNumbers] = useState([]);
  const [excludeNumbers, setExcludeNumbers] = useState([]);
  const [minAc, setMinAc] = useState(5);
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const [openCombo, setOpenCombo] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [savedCombinations, setSavedCombinations] = useState([]);
  const [toast, setToast] = useState({ visible: false, message: '' });
  const [activeTab, setActiveTab] = useState('results');
  
  // 분석 관련 상태
  const [historyData, setHistoryData] = useState(null);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState(null);
  
  const [filters, setFilters] = useState({
    f1: true, f2: true, f3: true, f4: true, 
    f5: true, f6: true, f7: true, f8: true
  });

  const mainRef = useRef(null);

  // 로컬 스토리지에서 저장된 조합 불러오기
  useEffect(() => {
    const saved = localStorage.getItem('fortunapick_saved');
    if (saved) {
      try {
        setSavedCombinations(JSON.parse(saved));
      } catch (e) {
        console.error('Failed to load saved combinations');
      }
    }
  }, []);

  // 저장된 조합 로컬 스토리지에 저장
  useEffect(() => {
    localStorage.setItem('fortunapick_saved', JSON.stringify(savedCombinations));
  }, [savedCombinations]);

  // 당첨 이력 데이터 로드 (메인 페이지 접속 시 백그라운드 로드)
  useEffect(() => {
    // 이미 데이터가 있거나 로딩 중이면 스킵
    if (historyData || historyLoading) return;

    const fetchHistory = async () => {
      setHistoryLoading(true);
      try {
        const res = await fetch('/api/history');
        const data = await res.json();
        
        if (!res.ok) {
          throw new Error(data.error || '데이터를 불러오는데 실패했습니다.');
        }
        
        setHistoryData(data);
      } catch (err) {
        console.error("Failed to load history data in background:", err);
        setHistoryError(err.message);
      } finally {
        setHistoryLoading(false);
      }
    };

    // 백그라운드에서 조용히 실행
    fetchHistory();
  }, []); // 빈 의존성 배열로 마운트 시 한 번만 실행

  // 외부 클릭 감지하여 드롭다운 닫기
  useEffect(() => {
    const handleClickOutside = (e) => {
      if (mainRef.current && !e.target.closest('.combo-wrapper')) {
        setOpenCombo(null);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  // 토스트 표시 함수
  const showToast = useCallback((message) => {
    setToast({ visible: true, message });
    setTimeout(() => setToast(prev => ({ ...prev, visible: false })), 2500);
  }, []);

  // API 호출
  const handleGenerate = async () => {
    setLoading(true);
    try {
      const res = await fetch('/api/index', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          fixed_nums: includeNumbers, 
          exclude_nums: excludeNumbers, 
          min_ac: minAc === '' ? 0 : minAc, 
          filters 
        })
      });
      const data = await res.json();
      setResult(data);
      setActiveTab('results');
      showToast(`${data.total.toLocaleString()}개의 유효 조합 발견`);
    } catch (error) {
      showToast('조합 생성 중 오류가 발생했습니다');
    } finally {
      setLoading(false);
    }
  };

  // 조합 저장
  const handleSave = (combo) => {
    const key = combo.join('-');
    const exists = savedCombinations.some(s => s.join('-') === key);
    
    if (exists) {
      setSavedCombinations(prev => prev.filter(s => s.join('-') !== key));
      showToast('조합이 삭제되었습니다');
    } else {
      setSavedCombinations(prev => [...prev, combo]);
      showToast('조합이 저장되었습니다');
    }
  };

  // 조합 복사
  const handleCopy = (combo) => {
    navigator.clipboard.writeText(combo.join(', '));
    showToast('클립보드에 복사되었습니다');
  };

  // 번호 선택 토글
  const toggleInclude = (num) => {
    if (excludeNumbers.includes(num)) return;
    setIncludeNumbers(prev => 
      prev.includes(num) 
        ? prev.filter(n => n !== num)
        : [...prev, num].sort((a, b) => a - b)
    );
  };

  const toggleExclude = (num) => {
    if (includeNumbers.includes(num)) return;
    setExcludeNumbers(prev => 
      prev.includes(num) 
        ? prev.filter(n => n !== num)
        : [...prev, num].sort((a, b) => a - b)
    );
  };

  // 필터 토글
  const toggleFilter = (key) => {
    setFilters(prev => ({ ...prev, [key]: !prev[key] }));
  };

  // 콤보박스 토글
  const handleComboToggle = (comboName) => {
    setOpenCombo(prev => prev === comboName ? null : comboName);
  };

  // 조합이 저장되었는지 확인
  const isSaved = (combo) => {
    return savedCombinations.some(s => s.join('-') === combo.join('-'));
  };

  // 평균 AC 값 계산
  const getAverageAC = () => {
    if (!result?.list?.length) return 0;
    const total = result.list.reduce((sum, combo) => sum + calculateAC(combo), 0);
    return (total / result.list.length).toFixed(1);
  };

  // 전체 홀짝 분포
  const getOverallOddEven = () => {
    if (!result?.list?.length) return { odd: 0, even: 0 };
    let totalOdd = 0;
    result.list.forEach(combo => {
      totalOdd += combo.filter(n => n % 2 !== 0).length;
    });
    const avgOdd = Math.round(totalOdd / result.list.length);
    return { odd: avgOdd, even: 6 - avgOdd };
  };

  // 전체 번호대 분포
  const getOverallDecadeDistribution = () => {
    if (!result?.list?.length) return { '1-10': 0, '11-20': 0, '21-30': 0, '31-40': 0, '41-45': 0 };
    const totals = { '1-10': 0, '11-20': 0, '21-30': 0, '31-40': 0, '41-45': 0 };
    
    result.list.forEach(combo => {
      const dist = getDecadeDistribution(combo);
      Object.keys(dist).forEach(key => {
        totals[key] += dist[key];
      });
    });
    
    return totals;
  };

  // 활성 필터 수 계산
  const activeFilterCount = Object.values(filters).filter(Boolean).length;

  return (
    <div className="app-container" ref={mainRef}>
      {/* 헤더 */}
      <header className="header">
        <div className="header-content">
          <div className="logo">
            <div className="logo-icon">
              <Icons.Logo />
            </div>
            <h1 className="brand-name">Fortuna<span>Pick</span></h1>
          </div>
          
          {/* 메인 네비게이션 탭 */}
          <nav className="main-nav">
            <button 
              className={`nav-item ${activeView === 'recommend' ? 'active' : ''}`}
              onClick={() => setActiveView('recommend')}
            >
              <Icons.Sparkle />
              <span>번호 추천</span>
            </button>
            <button 
              className={`nav-item ${activeView === 'analysis' ? 'active' : ''}`}
              onClick={() => setActiveView('analysis')}
            >
              <Icons.Chart />
              <span>당첨 분석</span>
            </button>
          </nav>
        </div>
      </header>

      {/* 메인 컨텐츠 영역 */}
      <div className="content-area">
        {activeView === 'recommend' ? (
          <div className="main-grid">
            {/* 설정 패널 */}
            <aside className="settings-panel">
              {/* 번호 선택 카드 */}
              <div className="card">
                <div className="card-content">
                  <NumberComboBox
                    label="필수 포함 번호"
                    selectedNumbers={includeNumbers}
                    disabledNumbers={excludeNumbers}
                    onToggle={toggleInclude}
                    onClear={() => setIncludeNumbers([])}
                    tagClass="include"
                    isOpen={openCombo === 'include'}
                    onToggleOpen={() => handleComboToggle('include')}
                  />

                  <div style={{ marginTop: 18 }}>
                    <NumberComboBox
                      label="제외 대상 번호"
                      selectedNumbers={excludeNumbers}
                      disabledNumbers={includeNumbers}
                      onToggle={toggleExclude}
                      onClear={() => setExcludeNumbers([])}
                      tagClass="exclude"
                      isOpen={openCombo === 'exclude'}
                      onToggleOpen={() => handleComboToggle('exclude')}
                    />
                  </div>
                </div>
              </div>

              {/* 필터 설정 */}
              <div className="filter-section">
                <div className="filter-header" onClick={() => setIsFilterOpen(!isFilterOpen)}>
                  <div className="filter-header-left">
                    <div className="filter-icon">
                      <Icons.Settings />
                    </div>
                    <div className="filter-header-text">
                      <h4>필터링 조건 설정</h4>
                      <span>{activeFilterCount}개 필터 활성화</span>
                    </div>
                  </div>
                  <div className={`filter-toggle ${isFilterOpen ? 'open' : ''}`}>
                    ▼
                  </div>
                </div>
                
                <div className={`filter-content ${isFilterOpen ? 'visible' : ''}`}>
                  <div className="filter-list">
                    {Object.entries(FILTER_DEFINITIONS).map(([key, filter]) => (
                      <div 
                        key={key}
                        className={`filter-item ${filters[key] ? 'active' : ''}`}
                        onClick={() => toggleFilter(key)}
                      >
                        <div className="filter-checkbox">
                          <Icons.Check />
                        </div>
                        <div className="filter-info">
                          <div className="filter-name">{filter.name}</div>
                          <div className="filter-desc">{filter.description}</div>
                        </div>
                      </div>
                    ))}
                    
                    {/* AC 값 입력 */}
                    {filters.f8 && (
                      <div className="ac-input-section">
                        <div className="ac-input-row">
                          <span className="ac-label">최소 AC 값 설정</span>
                          <input 
                            type="number" 
                            className="ac-input"
                            value={minAc}
                            min={0}
                            max={10}
                            onChange={(e) => {
                              const val = e.target.value;
                              if (val === '') {
                                setMinAc('');
                              } else {
                                const numVal = parseInt(val);
                                if (!isNaN(numVal)) {
                                  setMinAc(Math.max(0, Math.min(10, numVal)));
                                }
                              }
                            }}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* 생성 버튼 */}
              <button 
                className="generate-btn" 
                onClick={handleGenerate}
                disabled={loading || includeNumbers.length === 0}
              >
                {loading ? (
                  <>
                    <span className="loading-spinner" style={{ width: 20, height: 20, borderWidth: 2 }}></span>
                    <span>분석 중...</span>
                  </>
                ) : (
                  <>
                    <Icons.Sparkle />
                    <span>조합 추출하기</span>
                  </>
                )}
              </button>

              {/* 광고 영역 (사이드바 하단) - Temporarily Disabled */}
              {/* <AdBanner slotId={ADSENSE_CONFIG.SLOTS.SIDEBAR_BOTTOM} format="autorelaxed" style={{ marginTop: '20px' }} /> */}

              {/* 저장된 조합 */}
              {savedCombinations.length > 0 && (
                <div className="card">
                  <div className="card-header">
                    <div className="card-title">
                      <div className="card-title-icon">
                        <Icons.Star />
                      </div>
                      저장된 조합
                    </div>
                    <span className="saved-count">{savedCombinations.length}</span>
                  </div>
                  <div className="card-content" style={{ padding: 14 }}>
                    <div className="saved-list">
                      {savedCombinations.map((combo, idx) => (
                        <div key={idx} className="saved-item">
                          <div className="saved-balls">
                            {combo.map(num => (
                              <LottoBall key={num} number={num} small />
                            ))}
                          </div>
                          <button 
                            className="remove-btn"
                            onClick={() => handleSave(combo)}
                            title="삭제"
                          >
                            ✕
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </aside>

            {/* 결과 패널 */}
            <main className="results-panel">
              {/* 광고 영역 (결과 패널 상단) - Temporarily Disabled */}
              {/* <AdBanner slotId={ADSENSE_CONFIG.SLOTS.BANNER_TOP} /> */}

              {result ? (
                <>
                  {/* 통계 요약 */}
                  <div className="stats-grid">
                    <StatCard value={result.total.toLocaleString()} label="유효 조합" />
                    <StatCard value={result.list.length} label="추천 조합" />
                    <StatCard value={getAverageAC()} label="평균 AC" />
                    <StatCard value={savedCombinations.length} label="저장됨" />
                  </div>

                  {/* 탭 네비게이션 */}
                  <div className="tabs">
                    <button 
                      className={`tab-btn ${activeTab === 'results' ? 'active' : ''}`}
                      onClick={() => setActiveTab('results')}
                    >
                      추천 조합
                    </button>
                    <button 
                      className={`tab-btn ${activeTab === 'analysis' ? 'active' : ''}`}
                      onClick={() => setActiveTab('analysis')}
                    >
                      통계 분석
                    </button>
                  </div>

                  {/* 결과 목록 */}
                  {activeTab === 'results' && (
                    <div className="card">
                      <div className="card-header">
                        <div className="card-title">
                          <div className="card-title-icon">
                            <Icons.List />
                          </div>
                          추천 번호 조합
                        </div>
                      </div>
                      <div className="result-list">
                        {result.list.map((combo, idx) => {
                          const ac = calculateAC(combo);
                          const oddEven = getOddEvenRatio(combo);
                          const saved = isSaved(combo);
                          
                          return (
                            <div key={idx}>
                              {/* 5번째 결과마다 광고 삽입 - Temporarily Disabled */}
                              {/* {idx > 0 && idx % 5 === 0 && (
                                <AdBanner 
                                  slotId={ADSENSE_CONFIG.SLOTS.IN_FEED_LIST} 
                                  format="fluid"
                                  layoutKey={ADSENSE_CONFIG.LAYOUT_KEYS.IN_FEED_LIST}
                                  style={{ margin: '10px 0' }} 
                                />
                              )} */}
                              <div className="result-item">
                                <div className="result-rank">{idx + 1}</div>
                                <div className="result-balls">
                                  {combo.map(num => (
                                    <LottoBall key={num} number={num} />
                                  ))}
                                </div>
                                <div className="result-meta">
                                  <span className="meta-badge highlight">AC {ac}</span>
                                  <span className="meta-badge">홀 {oddEven.odd}:짝 {oddEven.even}</span>
                                </div>
                                <div className="result-actions">
                                  <button 
                                    className={`action-btn ${saved ? 'saved' : ''}`}
                                    onClick={() => handleSave(combo)}
                                    title={saved ? '저장 취소' : '저장'}
                                  >
                                    {saved ? <Icons.StarFilled /> : <Icons.Star />}
                                  </button>
                                  <button 
                                    className="action-btn"
                                    onClick={() => handleCopy(combo)}
                                    title="복사"
                                  >
                                    <Icons.Copy />
                                  </button>
                                </div>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* 분석 탭 */}
                  {activeTab === 'analysis' && (
                    <div className="analysis-grid">
                      {/* 홀짝 분포 */}
                      <div className="chart-card">
                        <div className="chart-title">홀짝 분포 (평균)</div>
                        <DonutChart 
                          value={getOverallOddEven().odd}
                          total={6}
                          label="비율"
                          primaryLabel="홀수"
                          secondaryLabel="짝수"
                        />
                      </div>

                      {/* 번호대 분포 */}
                      <div className="chart-card">
                        <div className="chart-title">번호대 분포</div>
                        <BarChart 
                          data={getOverallDecadeDistribution()}
                          maxValue={Math.max(...Object.values(getOverallDecadeDistribution()), 1)}
                        />
                      </div>

                      {/* AC 분포 */}
                      <div className="chart-card">
                        <div className="chart-title">AC 값 분포</div>
                        <BarChart 
                          data={(() => {
                            const acDist = {};
                            result.list.forEach(combo => {
                              const ac = calculateAC(combo);
                              const key = `AC ${ac}`;
                              acDist[key] = (acDist[key] || 0) + 1;
                            });
                            return acDist;
                          })()}
                          maxValue={result.list.length}
                        />
                      </div>

                      {/* 합계 분포 */}
                      <div className="chart-card">
                        <div className="chart-title">합계 범위</div>
                        <BarChart 
                          data={(() => {
                            const sumRanges = {
                              '~100': 0,
                              '101-130': 0,
                              '131-160': 0,
                              '161-190': 0,
                              '191~': 0
                            };
                            result.list.forEach(combo => {
                              const sum = getSum(combo);
                              if (sum <= 100) sumRanges['~100']++;
                              else if (sum <= 130) sumRanges['101-130']++;
                              else if (sum <= 160) sumRanges['131-160']++;
                              else if (sum <= 190) sumRanges['161-190']++;
                              else sumRanges['191~']++;
                            });
                            return sumRanges;
                          })()}
                          maxValue={result.list.length}
                        />
                      </div>
                    </div>
                  )}
                </>
              ) : (
                <div className="card">
                  <div className="empty-state">
                    <div className="empty-icon">
                      <Icons.Grid />
                    </div>
                    <div className="empty-title">번호 조합을 생성해보세요</div>
                    <div className="empty-desc">
                      필수 포함 번호를 선택하고 필터링 조건을 설정한 후
                      '조합 추출하기' 버튼을 클릭하세요.
                    </div>
                  </div>
                </div>
              )}
            </main>
          </div>
        ) : (
          <AnalysisView 
            historyData={historyData} 
            loading={historyLoading} 
            error={historyError} 
          />
        )}
      </div>

      {/* 토스트 */}
      <Toast {...toast} />
    </div>
  );
}
