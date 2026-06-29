# v16.5 C-RAM — 연안 작전 해안 방어 자산 (설계)

## 개념
연안 작전 시 아군 편대에 **해안 고정 방어 자산**(C-RAM 근접방어 포대·해안 SAM 포대)을
추가 배치한다. 함대+해안의 협동 다층방어. 적은 기존 대함/항공 위협에 더해 **연안 드론
스웜·로켓** 포화로 항만에 접근한다. 통합 방식 = **연안 작전 자산 추가**(사용자 합의):
기존 교전·MC·결과·비용 파이프라인을 그대로 재활용하고, 함정 인프라(`FriendlyShipObj`,
`_friendly_defense`)를 최대한 재사용해 신규 코드를 최소화한다.

## 신규 자산 (SHIP_DB, engine_core.py)
- **해안 C-RAM 포대** (type `CRAM`): 고정·불침. 근접방어무기(팰렁스급) 다수 채널.
  드론·로켓·박격포 종말 요격 특화. 저비용·단거리.
- **해안 SAM 포대** (type `CSAM`): 고정·불침. 중거리 SAM(천궁/패트리어트급).
  연안 접근 대함미사일·항공 요격.
- 두 타입 모두 `default_inventory`에 RAM/CIWS·중거리 SAM 탑재. db_specsheet 동기화.

## 신규 위협 (ENEMY_DB, engine_core.py)
- **연안 자폭 드론 스웜**: 다수 소형 무인기. 자폭(기존 `NEW-B` 드론 200m 도달 피격
  메커니즘 재활용). 저속·저고도·소형 RCS → CIWS/C-RAM 종말 요격 대상.
- **연안 공격 로켓**: 단거리 로켓/유도탄 포화(방사포급). 저고도 다발.
- `normalize_enemy_db()` 누락 필드 자동 보완 확인. db_specsheet 동기화.

## 엔진 변경 (최소 — 함정 인프라 재활용)
- `FriendlyShipObj`에 `is_shore_battery` 플래그(SHIP_DB type이 CRAM/CSAM이면 True).
  - **침수 면제**: 격실 침수 메서드(engine_combat:1196, `is_sub_hull` 분기 옆)에서
    `is_shore_battery`도 early return — 육상 포대는 침몰 안 함.
  - **회피 면제**: `_apply_ship_evasion`(2349) — 고정 포대는 지그재그 회피 안 함.
  - **HP 파괴는 유지**: 피격 누적 시 포대 무력화(침몰 아닌 파괴). 집계 동일.
- 그 외 `_friendly_defense`(SAM/CIWS 요격)·탐지·교전은 함정과 동일하게 작동.

## 프리셋 (engine_core.py)
- `FLEET_PRESETS` **"연안 방어 전대"**: 함정 일부(FFX·PKX) + 해안 C-RAM 포대 + 해안 SAM 포대.
- `ENEMY_FLEET_PRESETS` **"연안 포화 공격"**: 연안 드론 스웜 + 로켓 + 022형 고속정 다축.
- 시나리오 해역은 기존 `fleet_region`(서해/남해/동해) 재활용 — 인천·부산·동해 항만 맥락.

## 하위호환 / 회귀
- 새 SHIP_DB/ENEMY_DB 항목·프리셋은 기존 시나리오에 무영향(선택 안 하면 미등장).
- `is_shore_battery` 기존 함정 전부 False → 침수·회피 경로 불변. **회귀 8×26 PASS 예상**.
- `battle_surrogate`/forecast 키는 신규 프리셋 미포함이라 graceful(기존 동작).

## 검증
- 회귀 PASS(기존 무영향).
- **연안 방어 시나리오 MC**: C-RAM 포대가 드론·로켓을 실제 요격하는지, 함대+해안
  협동으로 요격률·생존이 단독 함대 대비 향상되는지(효과 입증). 기준값 메모리.
- db_specsheet 항목수 = DB 항목수(정적 스캔 ⑥).
- `/code-review medium`.

## 범위 (이번 블록)
- C-RAM 핵심(고정 해안 방어 자산 + 연안 드론·로켓 위협 + 협동방어)만.
- **기뢰 차단 구역은 제외** → v16.7 정식 기뢰전(MIW)으로 미룸(중복 방지).
- 지형(v14.1) 연동 시각화는 후속 선택.

## 단계
1. 신규 자산 2종(SHIP_DB) + `is_shore_battery` 플래그·면제 로직.
2. 신규 위협 2종(ENEMY_DB) + normalize + db_specsheet 4항목.
3. 프리셋 2종 + 검증(회귀·MC·정적)·코드감사.
