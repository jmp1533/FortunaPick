"use client";
import { useState, useEffect, useCallback } from 'react';
import { 
  getBallColor, 
  FILTER_DEFINITIONS, 
  calculateAC, 
  getOddEvenRatio, 
  getDecadeDistribution,
  getSum
} from './utils/constants';

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
  Chart: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/>
    </svg>
  ),
  Grid: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/>
    </svg>
  ),
  X: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
    </svg>
  )
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
  const percentage = (value / total) * 100;
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

// 번호 선택 모달 컴포넌트
const NumberModal = ({ 
  isOpen, 
  onClose, 
  title, 
  selectedNumbers, 
  disabledNumbers, 
  onToggle 
}) => {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="number-modal" onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <span className="modal-title">{title}</span>
          <button className="modal-close" onClick={onClose}>
            <Icons.X />
          </button>
        </div>
        <div className="modal-content">
          <div className="number-grid">
            {Array.from({ length: 45 }, (_, i) => i + 1).map(n => (
              <button
                key={n}
                className={`grid-number ${selectedNumbers.includes(n) ? 'selected' : ''} ${disabledNumbers.includes(n) ? 'disabled' : ''}`}
                onClick={() => onToggle(n)}
                disabled={disabledNumbers.includes(n)}
              >
                {n}
              </button>
            ))}
          </div>
        </div>
        <div className="modal-footer">
          <button className="modal-btn secondary" onClick={() => {
            selectedNumbers.forEach(n => onToggle(n));
          }}>
            초기화
          </button>
          <button className="modal-btn primary" onClick={onClose}>
            확인
          </button>
        </div>
      </div>
    </div>
  );
};

export default function Home() {
  // 상태 관리
  const [includeNumbers, setIncludeNumbers] = useState([]);
  const [excludeNumbers, setExcludeNumbers] = useState([]);
  const [minAc, setMinAc] = useState(5);
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const [activeModal, setActiveModal] = useState(null);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [savedCombinations, setSavedCombinations] = useState([]);
  const [toast, setToast] = useState({ visible: false, message: '' });
  const [activeTab, setActiveTab] = useState('results');
  
  const [filters, setFilters] = useState({
    f1: true, f2: true, f3: true, f4: true, 
    f5: true, f6: true, f7: true, f8: true
  });

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
          min_ac: minAc, 
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
    <div className="app-container">
      {/* 헤더 */}
      <header className="header">
        <div className="logo">
          <div className="logo-icon">
            <Icons.Logo />
          </div>
          <h1 className="brand-name">Fortuna<span>Pick</span></h1>
        </div>
        <p className="tagline">스마트 번호 조합 추천 서비스</p>
      </header>

      {/* 메인 그리드 */}
      <div className="main-grid">
        {/* 설정 패널 */}
        <aside className="settings-panel">
          {/* 번호 선택 카드 */}
          <div className="card">
            <div className="card-content">
              {/* 필수 포함 번호 */}
              <div className="input-group">
                <div className="input-label">
                  <span className="input-label-text">필수 포함 번호</span>
                  {includeNumbers.length > 0 && (
                    <button className="clear-btn" onClick={() => setIncludeNumbers([])}>
                      초기화
                    </button>
                  )}
                </div>
                <div 
                  className="selector-box"
                  onClick={() => setActiveModal('include')}
                >
                  {includeNumbers.length ? (
                    includeNumbers.map(n => (
                      <span key={n} className="number-tag include">{n}</span>
                    ))
                  ) : (
                    <span className="selector-placeholder">클릭하여 번호 선택...</span>
                  )}
                </div>
              </div>

              {/* 제외 번호 */}
              <div className="input-group" style={{ marginTop: 18 }}>
                <div className="input-label">
                  <span className="input-label-text">제외 대상 번호</span>
                  {excludeNumbers.length > 0 && (
                    <button className="clear-btn" onClick={() => setExcludeNumbers([])}>
                      초기화
                    </button>
                  )}
                </div>
                <div 
                  className="selector-box"
                  onClick={() => setActiveModal('exclude')}
                >
                  {excludeNumbers.length ? (
                    excludeNumbers.map(n => (
                      <span key={n} className="number-tag exclude">{n}</span>
                    ))
                  ) : (
                    <span className="selector-placeholder">클릭하여 번호 선택...</span>
                  )}
                </div>
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
                        min={1}
                        max={10}
                        onChange={(e) => setMinAc(Math.max(1, Math.min(10, parseInt(e.target.value) || 5)))}
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
                        {combo.map(num => {
                          const colors = getBallColor(num);
                          return (
                            <span 
                              key={num} 
                              className="ball"
                              style={{ 
                                backgroundColor: colors.bg, 
                                color: colors.text,
                                width: 30,
                                height: 30,
                                fontSize: '0.75rem'
                              }}
                            >
                              {num}
                            </span>
                          );
                        })}
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
                        <div key={idx} className="result-item">
                          <div className="result-rank">{idx + 1}</div>
                          <div className="result-balls">
                            {combo.map(num => {
                              const colors = getBallColor(num);
                              return (
                                <span 
                                  key={num} 
                                  className="ball"
                                  style={{ 
                                    backgroundColor: colors.bg, 
                                    color: colors.text 
                                  }}
                                >
                                  {num}
                                </span>
                              );
                            })}
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

      {/* 번호 선택 모달 */}
      <NumberModal
        isOpen={activeModal === 'include'}
        onClose={() => setActiveModal(null)}
        title="필수 포함 번호 선택"
        selectedNumbers={includeNumbers}
        disabledNumbers={excludeNumbers}
        onToggle={toggleInclude}
      />
      
      <NumberModal
        isOpen={activeModal === 'exclude'}
        onClose={() => setActiveModal(null)}
        title="제외 대상 번호 선택"
        selectedNumbers={excludeNumbers}
        disabledNumbers={includeNumbers}
        onToggle={toggleExclude}
      />

      {/* 토스트 */}
      <Toast {...toast} />
    </div>
  );
}
