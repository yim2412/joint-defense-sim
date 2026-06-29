# v16.7 기뢰전(MIW) — 추상 기뢰 노출 모델 (설계)

## 개념
함대가 기뢰 위협 해역(협수로·항만 입구)에서 작전할 때, 시뮬 진입 단계에서 함정별로
**확률적 기뢰 접촉**을 판정한다. 소해 자산(소해함·UUV) 보유 시 접촉 확률이 경감되고,
기뢰 3종(계류·해저·자항)이 차등 위협을 준다. 통합 방식=**추상 노출**(사용자 합의):
함대 이동·기뢰원 통과 동역학은 통계로 추상화하고, 기존 함정 피해(`take_hit`)·침수
(`_take_flood_damage`) 인프라를 재활용해 현 교전 엔진에 가볍게 얹는다.

## 구현
- 토글 `enable_mine_threat`(실험적, 기본 OFF) + `mine_density`(0~1, 기뢰 위협도, 기본 0.3)
  + `enable_minesweeping`(소해 지원 보유 → 접촉 확률 경감).
- **`_apply_mine_exposure()`** — 엔진 진입 1회(틱 루프 시작 전, `_id_counter` 리셋 부근).
  각 생존 수상함(잠수함 제외)에:
  - 접촉 확률 `p = mine_density × 함정 취약도 × (소해 시 ×_SWEEP_FACTOR)`.
    - 함정 취약도: 흘수/배수량 기반 — 대형함일수록 감응(해저)기뢰에 취약, 소형함은 회피 유리.
  - `random() < p`면 접촉 → 기뢰 3종 확률 선택, 종류별 피해:
    - **계류기뢰**: `take_hit` ×1 + 침수 중(breach 0.30). 흘수 무관.
    - **해저(감응)기뢰**: `take_hit` ×1 + 침수 대(breach 0.50). 대형함(흘수 깊음) 접촉 확률 가산.
    - **자항기뢰**: `take_hit` ×2 + 침수(breach 0.40). 능동 추적 — 명중 위력 최고.
  - 소형함은 HP 낮아 1접촉에도 침몰 가능(현실적). 침수는 `enable_flooding` ON일 때만 누적.
- **stats 신규**: `mines_struck`(기뢰 접촉 함정 수)·`ships_lost_to_mine`(기뢰로 침몰).
  **MC 3경로 동시 추가**(monte_carlo_v7·_mc_batch_worker·monte_carlo_lhs) — 누락 시 MC 소실.

## 호출 위치
`run_v7_simulation` 진입부 — 엔진 생성·`reset_counter` 직후, 틱 루프 시작 전 1회.
(기뢰는 작전 해역 진입 시 이미 노출된 위협 → 교전 시작 상태에 반영.)

## 하위호환 / 회귀
- `enable_mine_threat` OFF → `_apply_mine_exposure` 무동작·random 미소비 → **회귀 8×26 bit-identical**.
- 플래그명 고정(`enable_mine_threat`·`mine_density`·`enable_minesweeping`).
- 신규 stats 키는 OFF 시 0(기존 케이스 영향 없음, 골든에 0으로 추가 가능).

## 검증 (전술 옵션 유형)
- 회귀 PASS(OFF bit-identical).
- ON/OFF MC: 기뢰 위협 ON 시 함정 손상·손실 증가, 소해 지원 ON 시 경감 입증(역효과 없음).
  소형함 편대(연안)·대형함 편대 차등 확인. 기준값 메모리.
- `/code-review medium`.

## 범위
- C-RAM(v16.5)에서 미룬 '기뢰 차단 구역'을 본 항목에서 정식화(추상 노출로).
- 소해 자산은 1차로 cfg 토글(`enable_minesweeping`)로 추상 — 별도 소해함 SHIP_DB는 후속 선택.
- 기뢰 부설(아군이 적에 기뢰 설치)은 범위 외(방어 관점 — 아군이 받는 기뢰 위협만).

## 미결(구현 중 확정)
- `mine_density` 기본값·`_SWEEP_FACTOR`(소해 경감)·종류별 피해(breach·take_hit 횟수) —
  ON/OFF 측정으로 과하지 않게(소형함 전멸 방지) 튜닝.
- 함정 취약도 산식(흘수/배수량) — `SHIP_SURVIVABILITY`의 displacement_t 재활용.
