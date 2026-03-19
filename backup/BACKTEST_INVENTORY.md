# Backtest Inventory

FortunaPick에서 백테스트/검증 자료는 아래 기준으로 관리합니다.

## 1. 운영 기준으로 계속 유지할 자료

이 자료들은 현재 서비스/운영 기준을 설명하거나, 다음 업데이트 작업의 참고 자료로 계속 남겨둡니다.

- `lottery/backtest_stable_report.json`
  - 안정형 기준 백테스트 리포트
- `lottery/backtest_high_hit_report.json`
  - 고적중형 기준 백테스트 리포트
- `lottery/compare_presets_30_summary.json`
  - 30회차 프리셋 비교 요약
- `lottery/compare_presets_100_summary.json`
  - 100회차 프리셋 비교 요약
- `lottery/weekly_top_picks.json`
  - 메인화면에 노출하는 사전 계산형 TOP5 결과

## 2. 백업/이전용 스냅샷 자료

서버 이전 및 복구를 위해 `backup/` 폴더에 별도 보관합니다.

- `backup/stable_report.json`
- `backup/high_hit_report.json`
- `backup/compare_presets_30_summary.json`
- `backup/compare_presets_100_summary.json`
- `backup/PROJECT_STATE.md`
- `backup/ESSENTIAL_CONTEXT.md`
- `backup/README.md`

## 3. 단발성/임시 실험 산출물

아래 성격의 파일은 서비스 운영 기준 파일이 아니며, 필요 없으면 정리하거나 `.gitignore`로 제외합니다.

- `backtest_report_30_main.json`
- `backtest_report_50_main.json`
- `backtest_report_100_main.json`
- `backtest_report.json`
- smoke / mode test / preset test / scoreconfig test 류 결과 파일
- 개별 preset별 비교 JSON (`compare_<preset>_<rounds>.json`)

이 파일들은 최종 요약본이 존재한다면 재현 가능성이 높아, 루트에 계속 둘 필요는 낮습니다.

## 운영 원칙

- 서비스가 참조하는 결과 파일은 최소화한다.
- 실험 히스토리는 요약본 또는 `backup/` 스냅샷으로 남긴다.
- 원본 데이터는 항상 `lottery/winningNumbers.xlsx`를 기준으로 한다.
