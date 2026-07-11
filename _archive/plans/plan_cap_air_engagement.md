# 계획: CAP 공대공 요격 정상화 (B) — 나중에 실행

> **상태**: 규명 완료 · 구현 착수(미커밋) · **검증/골든/기준값 대기**. 2026-07-10 세션에서
> `aircraft_sorties=0` 조사가 밸런스 변경으로 커져 계획으로 분리. 밸런스 영향 커서 별도 처리.

## 배경 — 규명 완료 (이게 핵심 자산)
`aircraft_sorties`가 항상 0인 근본 원인은 **CAP 공대공 요격이 죽은 경로**였고, 원인이 2겹이다:

1. **계상 누락**: `_aircraft_cap`(engine_combat.py ~4276)이 AAM 발사 시 `ac.sorties`를 안 올림
   (헬기는 `_asw_detect_check` 4121에서 계상). → aircraft_sorties = CAP 기여 0.
2. **발사 자체가 발현 0** (200회 탐색 전부 0): 진짜 원인.
   - CAP 전투기(F-35A·KF-21·FA-50)만 `_AIRCRAFT_V7_SORTIE`(전시 긴급발진 오버라이드)에서
     **누락** → `t_available = sortie_time_s`(평시 900~1800s) 그대로.
   - 헬기·초계기·드론은 전시값(60~600s)으로 단축됐는데 CAP만 빠짐 = 일관성 버그.
   - 그마저 QRA 5분(300s)으로도 **부족**: 공중전 교전 창이 매우 짧다. 적기 600m/s로
     200km 스폰 → CAP 사거리(120km) 진입 ~135s, 발사·이탈(`is_retreating`) ~236s.
     CAP이 236s 전에 떠 있어야 교전 가능 → **상시 공중초계(on-station) 가정 필요**(~60s).

## 미커밋 구현 (engine_combat.py, 2026-07-10 세션)
> ⚠ 이 세션 종료 시 working tree에 남아있을 수 있음. B 재개 시 시작점으로 쓰거나,
> `git checkout -- engine_combat.py`로 되돌리고 이 계획대로 처음부터.

1. `_aircraft_cap` 4276: `ac.sorties += 1` 추가 (BVR 교전 = 출격 계상, 헬기 4121과 대칭).
2. `_AIRCRAFT_V7_SORTIE`에 CAP 3기종 추가: `F-35A 라이트닝 II`·`KF-21 보라매`·`FA-50 파이팅이글` = **60s**.

## 남은 작업 (B 실행 시)
1. **발현 확인**: t_available=60s에서 CAP AAM 발사(sorties>0)가 실제 나오는 편성·시드 탐색
   (분류기 불가로 미확인 상태에서 중단). 안 나오면 값·조건 재검토(4273 aam_range·4264 retreating).
2. **골든 케이스 추가**: CAP 발현 시나리오를 `audit_verify_regression.py` CASES에 추가
   (A 원칙 — "안 밟히는 경로는 골든에 넣어 감시"). CAP 공대공 격추 경로 봉인.
3. **회귀 골든 대거 갱신**: CAP 편성 케이스들의 intercept_rate·enemy_ships_destroyed·
   aircraft_sorties 변화 → `--update`. 의도된 밸런스 변경.
4. **ON/OFF 기준값 측정**: CAP 발현이 요격률을 얼마나 개선하는지 MC로. `project-baseline-cap` 신설.
5. **밸런스 타당성**: 60s(상시 공중초계)가 과한지 검토. 교리 근거(항모전단 CAP 24/7 on-station)
   문서화. 값 튜닝 여지.
6. **위생**: changelog·헤더·APP_VERSION(v18.01.17 예약)·빌드·커밋·푸시. 이 plan 파일 아카이브.

## 주의
- **밸런스 변경**이라 기존 기준값([[project-baseline-*]]) 영향 가능 — 측정·기록 필수.
- `enable_kf21` 등 CAP 3종세트는 기존과 동일(플래그 무변경). OFF면 CAP 무영향 유지.
- 관련: [[patch-queue]]. 규명 출처 = 이 세션 aircraft_sorties 조사.
