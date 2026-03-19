# Essential Context for Future OpenClaw Sessions

## User Preferences
- 중요한 대화와 결정은 기억해둬야 함.
- 진행이 길어지면 침묵하지 말고 중간 진행상황을 짧게 공유하는 걸 선호함.
- FortunaPick 관련 작업에서는 실제 성능 향상이 가장 중요함.

## Project Intent
- FortunaPick는 단순 분석 사이트가 아니라 **당첨 가능성이 더 높은 번호 조합 추출**이 핵심 목적임.
- 사용자는 매주 엑셀의 회차별 당첨번호를 업데이트할 수 있지만, 매주 항상 즉시 하지 못할 수도 있음.
- 그래서 최신 회차 반영은 **UI 버튼으로 내부 업데이트** 가능한 구조를 선호함.

## Important Decisions Already Made
- 추천 모드는 두 가지로 운영:
  - 안정형 = `balanced_distribution`
  - 고적중형 = `sum_relaxed`
- 프리셋 비교는 30회차 / 100회차 기준으로 수행했고, 위 두 모드가 제품 반영 대상으로 선정됨.
- 회차가 누락될 수 있으므로, `업데이트 반영하기` 버튼은 여러 누락 회차를 한 번에 증분 반영해야 함.

## Recovery Instruction
새 서버/새 OpenClaw 세션에서 이 저장소를 열었다면:
1. `backup/PROJECT_STATE.md` 확인
2. `backup/ESSENTIAL_CONTEXT.md` 확인
3. `lottery/winningNumbers.xlsx`와 `backup/*.json` 리포트 존재 확인
4. 이후 FortunaPick 운영 상태를 이어받아 작업 시작
