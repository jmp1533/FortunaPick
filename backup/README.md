# FortunaPick Backup & Recovery

이 폴더는 **서버 이전 / OpenClaw 재설치 / 텔레그램 봇 재연결** 시 FortunaPick 운영 상태를 빠르게 복구하기 위한 백업 자료 모음입니다.

## 이 폴더에 있는 것

- `stable_report.json` — 안정형 증분 백테스트 리포트 스냅샷
- `high_hit_report.json` — 고적중형 증분 백테스트 리포트 스냅샷
- `compare_presets_30_summary.json` — 30회차 프리셋 비교 요약
- `compare_presets_100_summary.json` — 100회차 프리셋 비교 요약
- `PROJECT_STATE.md` — 현재 추천 정책 / 운영 방식 / 복구 지침
- `ESSENTIAL_CONTEXT.md` — OpenClaw가 다시 이어받아야 할 핵심 기억 요약

## 복구 절차 요약

1. 새 서버에 OpenClaw 설치
2. 텔레그램 봇 연결
3. 이 저장소 클론
4. 작업 폴더에서 `backup/PROJECT_STATE.md` 와 `backup/ESSENTIAL_CONTEXT.md` 확인
5. OpenClaw에게 다음처럼 지시:

> 이 repo의 `backup/` 폴더를 확인해서 이전 기억과 운영 상태를 반영해줘.

## 참고

- 최신 회차 원본 데이터는 `lottery/winningNumbers.xlsx`
- UI에는 안정형 / 고적중형 추천 모드가 있음
- UI의 "업데이트 반영하기" 버튼은 누락 회차를 안정형/고적중형 리포트에 증분 반영하도록 설계됨
