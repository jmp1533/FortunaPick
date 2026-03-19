# FortunaPick Project State

## Current Goal

최종 목표는 **매주 `조합 추출하기` 버튼으로 당첨 가능성이 더 높은 번호 조합을 추출**하는 것입니다.

## Current Recommendation Modes

### 1. 안정형
- 내부 preset: `balanced_distribution`
- 의도: 평균 성과, 3개 이상 적중 회차 수, 보너스 적중 안정성 중시

### 2. 고적중형
- 내부 preset: `sum_relaxed`
- 의도: 4개 이상 / 5개 이상 같은 고적중 가능성 쪽 신호 중시

## Data Source
- 핵심 원본: `lottery/winningNumbers.xlsx`
- 회차별 당첨번호와 보너스 번호를 이 파일에서 읽음
- 회차가 추가되면 엑셀을 최신화한 뒤 반영함

## Update Flow
1. 사용자가 `winningNumbers.xlsx`를 최신화 후 커밋/푸시
2. 사이트 UI에서 **업데이트 반영하기** 버튼 클릭
3. 시스템이:
   - 최신 엑셀 회차 확인
   - 안정형/고적중형 리포트의 마지막 반영 회차 확인
   - 누락된 회차가 여러 개면 전부 순차 증분 반영
   - summary 재계산

## Backtest Reports
- 안정형 리포트: `lottery/backtest_stable_report.json`
- 고적중형 리포트: `lottery/backtest_high_hit_report.json`
- 이 폴더에는 복구용 스냅샷으로 각각 `backup/stable_report.json`, `backup/high_hit_report.json`도 보관함

## Important Technical Notes
- 추천은 **전체 조합 기반**으로 동작해야 함
- 임의 후보 축소가 아니라 필터/점수화로 선별하는 구조를 유지
- 백테스트는 성능 최적화를 위해 슬라이딩 윈도우, checkpoint/resume, mode 분리를 도입함
- 신규 회차 반영은 전체 재실행보다 **증분 반영**을 우선함

## Current Useful Files
- `api/index.py` — 추천 API
- `api/update.py` — 최신 회차 반영 상태 조회/증분 업데이트 API
- `lottery/engine.py` — 조합 엔진 / score_config
- `lottery/score_presets.py` — 추천 프리셋 모음
- `lottery/backtest.py` — 백테스트 및 증분 업데이트 로직
- `app/page.js` — 추천 UI / 업데이트 버튼

## Deployment Reminder
- GitHub repo: `https://github.com/jmp1533/FortunaPick`
- 서비스는 Vercel 배포 기준으로 운영 중
