# ASW 전진 초계 (대잠전 균형 실효화)

> v16.1 능동 소나 핑 역탐지의 효과를 임무 결과로 드러내기 위한 대잠 균형 작업. 난이도 중간~높음(엔진 동역학) → 설계 먼저.

## 1. 문제 (진단 완료)
`_asw_detect_range`(engine_v7:3538)가 ASW 항공기를 **기함(primary) 위치 기준**으로 잠수함 거리를 측정 → ASW기가 함대에 수동 대기하며 잠수함이 탐지권(~20km, 수온층 적용 후)에 올 때까지 기다린다. 결과:
- 이탈 잠수함(발사 후 반대 방향 잠항) = 탐지권 밖 구조적으로 못 잡음
- 접근 잠수함(11~15m/s 저속) = 함대 근처 올 때까지 1750s(전장 거의 끝) 소요
- ASW 전개 사거리(헬기 140·초계기 2000+km)는 충분하나 탐지권이 함대 고정이라 무용

## 2. 설계
`FriendlyAircraftObj`는 실제 위치(pos) 없이 기지(home_pos)만 가지므로, ASW기 위치를 새로 만들지 않고 **transit(전진 비행) 단계**로 추상화한다.

- **`enable_asw_forward`** 플래그 3종세트, **기본 OFF**(회귀 bit-identical 보존).
- `_aircraft_asw` idle 탐색에서 ON이면:
  - 잠수함이 전개 사거리(`range_km`) 안 + 탐지권(`detect_m + bonus`) **밖**이면 → `_asw_phase='transit'`(전진 비행). transit 시간 = `(dist_to_sub - detect_m) / ac.speed_ms`(탐지권 가장자리까지 비행).
  - 탐지권 안이면 현행대로 즉시 탐지(변경 없음).
- `transit` 단계 처리(hovering/cooldown과 동급): 만기 전엔 비행 중(continue), 만기 시 표적 생존 확인 후 탐지 단계(dipping→hovering / sonobuoy→detect_check) 진입. 도착했으므로 탐지권 재확인 없이 진행.
- **부모 무수정**: 플래그 OFF면 idle 분기가 현행(탐지권 밖이면 패스) 그대로 → 회귀 PASS.

## 3. 효과 검증 (ARM 교훈 — 결과 반영 조기 측정)
대잠 시나리오(대잠 복합·잠수함 복합 포화) + `enable_asw_forward` + `enable_sonar_emcon` ON에서:
- ASW기가 잠수함으로 전진 → 일찍·많이 교전 → **잠격침↑**(현재 ~0) + **능동소나 역탐지 발동·효과가 임무 결과에 반영**.
- ON/OFF 기준값 측정으로 효과가 실제 결과로 나타나는지 확인 후에야 검증 완료. 또 다른 병목(어뢰 Pk·격침 판정)이 드러나면 정직히 기록·후속.

## 4. 주의
- transit 단계 추가는 ASW 상태머신 변경 → 회귀 위험. 플래그 기본 OFF + verify_regression PASS 필수.
- 잠수함이 transit 중 이동(이탈)하면 도착 시 거리 차 발생 → 만기 시 표적 생존만 확인(거리 재확인은 현행 cooldown 로직 참고). 이탈 잠수함은 `_asw_detect_range`의 ×0.3 패널티로 여전히 어려움(의도 — 이탈=은밀).
