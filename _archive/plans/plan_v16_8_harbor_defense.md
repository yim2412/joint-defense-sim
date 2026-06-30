# v16.8 (APP_VERSION v16.11.01) — 항만·기지 방어 시나리오

## 목표
새 화력을 더하는 게 아니라 v16.5(해안 포대 CRAM/CSAM)·v16.7(기뢰전)·기존 자산을
**"거점 방어 상황"으로 통합**하는 복합 시나리오. 로드맵 v16.8.

v16.5(연안 포화=공중 자폭드론+로켓, 대공 위주)와 차별:
v16.8 = **수상 무인정(자폭 USV) + 침투 고속정 + 기뢰** 복합 (수상·근접·수중).

## 핵심 리스크와 해결
- 자폭 도달 로직(`engine_combat.py:2426~2438`)이 `et.is_aircraft` 조건에 묶임 →
  공중 자폭드론만 작동. 수상 자폭정은 신규 처리 필요.
- **해결**: 자폭 USV를 `is_ship`(type=고속정)으로 만들고, 자폭 조건을
  `is_aircraft or info['is_suicide']`로 일반화. 요격은 **기존 `_friendly_strike`의
  Mk.45 5인치 함포(재고 무한·근거리 최후 레이어) 재활용** — 신규 CIWS 경로 불필요.
  자폭 USV는 미사일 미발사라 `is_retreating` 항상 False → 계속 돌진 → 200m 자폭.

## 변경 파일

### engine_core.py
1. **ENEMY_DB**: `'자폭 무인수상정(USV)'` 신설 — category=대함, type=고속정(→is_ship),
   speed~14m/s, altitude_m=5, can_fire_missile=False, **is_suicide=True**, rcs~5,
   hp=1(소형·함포 1발 격침), high_value_target=False, self_defense_pk=0, enemy_ciws_pk=0.
2. **normalize_enemy_db**: `e.setdefault('is_suicide', False)` 추가 (하위호환).
3. **ENEMY_FLEET_PRESETS**: `'항만 침투 복합'` 신설 — 자폭 USV 12 + 022형 침투 고속정 4
   + 연안 자폭 드론 8 (무인정·근접 돌파 중심).

### engine_combat.py
4. **자폭 도달 로직(2429)**: `not et.is_aircraft` → `not (et.is_aircraft or et.info.get('is_suicide'))`.
   수상 자폭정도 200m 도달 시 자폭.
5. **함포 우선 격퇴(`_friendly_strike` is_ship 블록)**: `et.info.get('is_suicide')`면
   고가 해성 대신 Mk.45 함포 강제(소형 자폭정에 해성 낭비 방지). 함포 사거리 밖이면 skip.

### app_main.py
6. **SCENARIO_LIBRARY**: `'항만 거점 방어'` 신설 — `연안 방어 전대`(함정+CRAM/CSAM) +
   `항만 침투 복합` 적편대 + **enable_mine_threat: True**(기뢰 복합) + 적정 해역·날씨.
7. 헤더 버전·`APP_VERSION` → v16.11.01. `_PLANS` v16.8 항목 삭제.

### db_specsheet.py
8. `'자폭 무인수상정(USV)'` 스펙 추가 (엔티티 DB 수 +1 정합).

### app_changelog.json
9. v16.11.01 항목 추가 (추가: 항만·기지 방어 — 자폭 무인수상정·기뢰 복합 거점 방어).

## 하위호환·회귀
- 신규 `enable_xxx` 토글 **없음** (기뢰=기존 enable_mine_threat 재활용).
- `is_suicide`는 새 DB 필드지만 기존 위협엔 setdefault False → 자폭 조건 변화 없음 → **bit-identical**.
- 새 위협/편대/시나리오는 회귀 골든 8케이스 미포함 → 회귀 PASS 예상.
- 자폭 로직 조건 변경: 기존 위협은 is_aircraft 기준 동일, is_suicide 위협만 신규 → 골든 무영향.

## 검증
- 변경 전 회귀 PASS 확인 완료 → 변경 후 재실행 (bit-identical 기대).
- ON/OFF 효과 측정: '항만 거점 방어' 시나리오 단발 — 자폭 USV 자폭/함포 격퇴, 기뢰 손실.
- 정적 스캔 + 빌드 + GUI 스모크.
