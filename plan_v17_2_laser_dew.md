# v17.2 지향성 에너지 무기(레이저·DEW) — 설계

**상태**: 설계 합의 대기 → 구현 (2026-07-04 착수)
**난이도**: 높음 (새 물리모델 + 함정 통합 전력 budget). Opus/high, 점진 컷오버(빅뱅 금지).
**정본 진단**: [[patch-queue]] Phase 4. read-only 진단 결과 아래 '0. 진단 요약' 반영.

---

## 0. 진단 요약 (착수 전 read-only 조사 결과)

- **레이저/DEW 코드 = 없음** (계획 텍스트만). 전기 power 모델 = 없음(코드의 "전력"은 전부 force value·조달가·ecm_power).
- **CIWS/RAM 근접방어 = 이미 구현**. `CIWS-II (Phalanx)` 2km·`RIM-116 RAM` 9km, **CIWS 탄약 stock=9999(무제한)**. 동시교전 채널 모델 정교(`max_channels`/`channels_used`, 1130-CIWS channels=1).
- **레이저 주 표적(드론·보트)은 이미 CIWS·함포로 요격 중**. 드론 스웜 병목은 **탄약이 아니라 동시교전 채널**(baseline: 20→80대 요격률 0.81→0.34, CIWS 무한탄인데도 하락).
- **⚠️ 중복 리스크**: 단순 "추가 요격 채널"로 넣으면 "CIWS 채널 +1"과 동형 → 신규 무기 클래스 정당성 없음(ARM·HGV式 실효 미미/중복 패턴).

## 1. 차별화 원리 (중복 회피의 핵심)

레이저는 CIWS와 **다른 제약축·다른 교전특성**을 가져야만 의미가 생긴다.

| | CIWS/RAM (기존) | 레이저 (신규) |
|---|---|---|
| 탄약 | 무한(9999) | 무한 |
| 교전 | 순간 사격, 다채널 | **표적당 조사시간(dwell) 필요 → 사실상 1채널** |
| 병목 | 동시교전 채널 → **포화 취약** | **전력 한도**(조사 중 잉여전력 소진, 고속기동 시 추진이 잠식) |
| 대상 | 전 위협 | **드론·소형보트·아음속만** (초음속·탄도·HGV 불가) |

**실효 타깃** = 드론 스웜 채널 포화(0.34). 레이저가 CIWS 채널과 **독립된 별도 경로**로 저속 표적을 1개씩 태워 포화를 완화하되, 전력 한도가 "동시 다표적엔 약함"을 만들어 CIWS와 구별.

## 2. 설계 결정 (사용자 합의 완료 2026-07-04)

1. **전력 모델 = 함정 통합 전력 budget** — 총 발전량을 추진·레이더·레이저가 나눔. 고속 기동 시 레이저 출력 저하(트레이드오프).
2. **표적 범위 = 드론·자폭정 + 아음속 순항미사일**(speed_ms ≲ 340). 초음속·탄도·HGV 제외.
3. **dwell = 거리·출력 비례** — 조사시간 = 필요에너지 / 도달출력, 도달출력 ∝ laser_kw/거리²(대기감쇠·회절). 표적 접근 중 거리↓ → 출력↑ → 후반 가속.

## 3. 데이터 모델

### 3-1. 함정 통합 전력 (신규 DB `SHIP_POWER` — engine_core.py, 실측 우선 [[feedback-real-data]])
공개 제원 기반 함정별 총 발전량(kW). 실측값 확보(예: KDX-III MT30/디젤 발전, Burke급 Gas Turbine Generator 3×3MW 등). 확보 곤란 함종은 배수량 비례 추정 + 주석 명기.

```
SHIP_POWER = {
  'KDX-III Batch-II': {'gen_kw': ..., 'radar_kw': ..., 'prop_ref_kw': ...},
  ...
}
```
- `power_avail_kw(speed)` = gen_kw − radar_kw − prop_kw(speed) ; prop_kw ∝ speed³(순항 대비). 고속일수록 잉여 축소.
- 미장착·비전투함은 레이저 무관(gen만 참고).

### 3-2. 레이저 무기 (FRIENDLY_DB 또는 함정 속성)
- `laser_kw`: 무기 정격출력(예 60kW). 장착함만 >0.
- `laser_range_km`: 유효 교전거리(예 ~5km, 회절·대기감쇠로 근거리 한정).
- 표적별 `E_kill_kj`: 격추 소요 에너지(드론 낮음 → 아음속미사일 높음).

### 3-3. FriendlyShipObj 신규 필드
- `laser_kw`(0=미장착), `_laser_target_uid`(현재 조사 표적), `_laser_dwell_acc`(누적 에너지 kJ).
- 전력은 함정 통합이라 별도 heat 필드 대신 `power_avail_kw(현재속도)`로 매 틱 계산.

## 4. 교전 로직 (`_friendly_defense` 내 신규 단계)

`enable_laser_dew` ON & 레이저 장착 생존함마다, 매 틱:
1. 현재 조사 표적 있으면 유지(lock). 없으면 사거리 내 **유효 표적**(드론·자폭정·아음속미사일, is_alive) 중 최근접 1개 lock.
2. 도달출력 `P = laser_kw × (ref_km/dist)²` (상한 laser_kw). 잉여전력 부족 시 `min(P, power_avail_kw)`.
3. 누적 `_laser_dwell_acc += P × dt`. `≥ E_kill_kj` → 격추(intercepted=True), lock 해제, 다음 표적.
4. 표적이 사거리 이탈/타 무기 격추 시 lock 해제·누적 리셋.
- **CIWS 채널과 독립**(channels_used 미사용) → 채널 포화 우회.
- 단발+전장 공통. MC 3경로 신규 stats(`laser_kills`) 동시 추가.

## 5. 하위호환·3종세트

- `enable_laser_dew` **3종세트**(체크박스 + cfg 빌드 isChecked + cfg 로드 hasattr), 기본 **OFF**, **실험적** 레이블.
- OFF면 레이저 단계 skip → **회귀 bit-identical**(골든 무영향).
- 부모 무수정: 레이저 로직은 신규 메서드(`_laser_defense`)로, `_friendly_defense`에서 플래그 가드 호출. `FriendlyShipObj` 신규 필드는 기본 0.
- 신규 stats `laser_kills` → `monte_carlo_v7`·`_mc_batch_worker`·`monte_carlo_lhs` 3경로 동시.
- db_specsheet: 레이저 무기·SHIP_POWER 신규 항목 스펙 설명 추가.

## 6. 검증 계획 (승격 게이트 = 전술 옵션)

- 회귀 PASS(OFF bit-identical) + 정적 스캔 + 코드리뷰 high.
- **ON/OFF 기준값 측정**(드론 스웜 시나리오): 레이저 ON이 채널 포화(0.34)를 실제로 완화하는가. 완화하면 실효 입증(ARM式 미미 회피 확인).
- **전력 트레이드오프 확인**: 고속 기동 시 레이저 출력 저하 발현. 동시 다표적 시 1채널 한계로 CIWS와 차별 확인.
- 기준값 → `project-baseline-laser-dew` 메모리.

## 7. 구현 순서 (마이너 분할, 빅뱅 금지)

- **v17.2.01**: SHIP_POWER DB + `power_avail_kw` + FriendlyShipObj 필드 (데이터·전력만, 교전 무변경 → 회귀 PASS).
- **v17.2.02**: `_laser_defense` 교전 로직 + `enable_laser_dew` 3종세트 + MC 3경로 stats + db_specsheet.
- **v17.2.03**: 드론 스웜 ON/OFF 기준값 측정 + 튜닝(E_kill·ref_km) + 코드리뷰 high + 기준값 메모리.

## 8. 리스크·주의

- **중복 재발 감시**: 구현 후에도 "레이저 효과 = CIWS 채널 늘린 것과 동형"이면 실패. 전력 트레이드오프·1채널 dwell이 실제로 CIWS와 다른 거동을 내는지 v17.2.03에서 반드시 확인. 안 나오면 P1처럼 **음성 결과로 보류** 판단.
- **v18.2 "전력 관리 모델"과 이름만 겹침**(그건 force management). 혼동 금지.
- 실측 발전량 확보 곤란 시 추정 명기(과대 금지).
