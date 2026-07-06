# v18 작전급 캠페인 엔진 — 설계 문서 (Phase 0)

> 며칠 단위 전역(캠페인)을 다루는 **작전급 엔진**. 전술 교전(초~분)을 해결기로 호출하고,
> 나머지는 즉시예측(v15.2)으로 빠르게 계산해 **72시간 전역을 수초에** 돌린다.
> 정본 = 이 문서. 로드맵_상세 문서는 이 계열을 'v17'로 표기(번호 stale) — **_PLANS·이 문서 = v18 정본**.

---

## 1. 목적 · 배경
현재 엔진은 **단발/지속 전장 = 교전 1회 해결기**(초~30분). 실제 작전은 며칠간
▸함정 이동·초계·귀항·수리·재보급 ▸여러 교전의 누적 ▸해상 교통로 통제 ▸적 위치 불확실성.
이 층을 **별도 엔진**으로 얹어, 전술 엔진은 "교전이 났을 때만" 호출한다.

**핵심 가치 = 속도**: 캠페인 1회에 교전 수십 회 → 정밀 엔진(~5s/교전)이면 수분·MC 불가.
**즉시예측(featurize+forecast_model, ~ms)**으로 교전을 해결해 캠페인 1회를 수초, 1000회 MC를 수분에.

## 2. 범위 · 끝 상태
- **별도 `engine_campaign.py`** — 전술 엔진(`engine_combat.py`)을 **import해 호출만**. 전술 엔진 **무수정**
  (`BattleEngine(TimeStepEngine)`이 부모 무수정으로 성공한 선례 그대로). → 전술 회귀 bit-identical.
- 1시간 틱 × 72(기본). 승패 = 해상 교통로(SLOC) 통제 상태.
- 교전 해결 = **즉시예측 우선**. 정밀 엔진(`run_battle_simulation`)은 후속 옵션('결정적 교전만').
- **MVP는 코어 루프만** (아래 Phase 1). 임무 배정·전장의 안개·수리 상세는 후속 Phase.

## 3. 재사용 vs 신규
| 그대로 재사용 | 신규(engine_campaign) |
|---|---|
| `featurize()`+`forecast_model` (교전 즉시 추정) | 캠페인 시간 루프(1h 틱) |
| `run_battle_simulation()` (정밀 교전, 후속 옵션) | ForcePool(함정 상태머신) |
| `SHIP_DB`·`FLEET_PRESETS`·`ENEMY_FLEET_PRESETS` | 구역(zone) 지리 모델 |
| `SHIP_ENDURANCE`(항속)·`ENEMY_PROCUREMENT`(전력가치) | SLOC 통제·캠페인 승패 판정 |

## 4. 핵심 데이터 구조 (MVP)

### 4.1 구역(zone) 모델 — 격자 대신 추상 노드
```
ZONES = ['서해', '대한해협', '동해', '모항(기지)']
```
각 zone: 위협도(적 존재), SLOC 여부(서해·대한해협·동해는 교통로, 모항은 안전). 격자는 과함 — 노드로 시작.

### 4.2 ForcePool — 함정 상태머신
```
CampaignShip: { ship_type, zone, state, hp_frac, fuel_frac, ammo_frac, repair_eta_h }
state ∈ {초계(patrol), 교전(engaged), 귀항(return), 수리(repair)}
```
- 매 틱: 상태 전이(초계 중 적 조우→교전, 손상→귀항→수리, 수리 완료→가용).
- MVP 수리: 손상도 비례 고정 시간(상세 1~14일은 v18.2).

### 4.3 EnemyForce — 적 전개
- 적 편대(ENEMY_FLEET_PRESETS)가 시간에 걸쳐 zone에 진입(웨이브). MVP는 고정 스케줄(진입 시각·zone).
- 전장의 안개(위치 확률)는 v18.4 — MVP는 위치 확정(안개 없음).

### 4.4 교전 트리거 · 해결 (MVP 핵심)
- **트리거**: 같은 zone에 아군 초계 전력 + 적 전력 동시 존재 → 교전 1건 생성.
- **해결(즉시예측)**:
  ```
  vec = featurize(fleet_ships=교전 참가 아군 함종, enemy_fleet=적 편성, weather)
  win_p, score, cost = forecast_model.predict(vec)   # win/score [0,1], cost USD
  승패 = (rng.random() < win_p)                       # 베르누이 샘플
  아군 피해 = f(1 - score)                            # score↓ = 피해↑ (MVP 근사)
  ```
- **결과 반영**: 승=적 전력 격퇴·아군 소량 손상 / 패=아군 손상↑·적 zone 침투 지속.
  피해받은 함정 → hp_frac↓ → 귀항→수리. 적 격퇴 시 해당 적 전력 제거.
- ⚠ **설계 포인트**: forecast_model은 win/score/cost만 추정(**함정 손실 수는 미추정**).
  MVP는 score로 **추상 피해**(손상 함정 비율) 근사. 정밀 손실은 정밀 엔진 옵션(후속)에서.

### 4.5 SLOC 통제 · 승패
- 매 틱 각 교통로 zone의 통제 = f(그 zone 아군 vs 적 전력). 적 우세 지속 → 교통로 차단.
- 캠페인 종료(72h) 시: 교통로 3개 중 통제 유지 수 → outcome(승/무/패). 조기종료(전 교통로 차단 or 아군 전력 소진).

## 5. 인터페이스
```python
def run_campaign(cfg: dict, step_cb=None) -> dict:
    """작전급 캠페인 1회. cfg: fleet_preset/fleet_custom·enemy 전개·weather·campaign_horizon_h.
    반환: {outcome, sloc_control(교통로별), force_timeline, engagements[], surviving_force, cost_total}"""
```
- cfg는 기존 키 재사용(fleet_preset·fleet_custom·weather) + 신규(campaign_horizon_h·enemy_schedule).
- `enable_campaign_mode` 3종세트(체크박스+cfg빌드+cfg로드). 기본 OFF. 전술/전장 경로 무영향.

## 6. Phase 분할
| Phase | 내용 | 산출 |
|---|---|---|
| **v18.1 코어 루프 MVP** | zone·ForcePool·교전 트리거·즉시예측 해결·SLOC 승패·1h 틱×72. 최소 UI(모드 토글+결과 요약). **엔진 무수정→회귀 bit-identical** | 돌아가는 캠페인 |
| v18.2 전력 관리 상세 | 수리 기간(피해별 1~14일)·탄약/연료 재보급·가용전력 | ForcePool 정교화 |
| v18.3 임무 배정 | 가용전력→초계·호위·타격·대잠 우선순위 그리디 | MissionQueue |
| v18.4 전장의 안개 | 적 위치 가우시안 belief·탐지 갱신·불확실성 확산 | Intel |
| v18.5 SLOC 정교화 | 위협도 맵·우회로·보급 완충 | SLOC v2 |
| v18.6 캠페인 MC | 1000회 반복 통계(잔존 전력·통제율·비용·민감도) | 캠페인 분석 |
| v18.7 보고서·시각화 | 전역 타임라인·결정적 순간·3D 경로 | 보고서 |

## 6-A. 진행 상태 (2026-07-06)
- **✅ v18.1 코어 루프**(v17.01.01~02): zone·ForcePool·교전 트리거·즉시예측 해결·SLOC 승패. exe 버그 2건 수정(step_cb 타입·모델 경로).
- **✅ v18.2 전력 관리**(v17.01.03): 수리 기간 차등(1~14일)·탄약/연료 소모·모항 재보급.
- **✅ v18.3 임무 배정**(v17.01.04): 위협 기반 동적 재배정(6h 주기, 아래 6-B). 강한 함정→고위협 방어집중·약한 함정→calm 초계, 이동 1틱(transit). 헤드리스 검증: 배치 정확·조기종료 완화·교전 수↑·회귀 bit-identical.
- **▶ 다음 = v18.4 전장의 안개** (적 위치 가우시안 belief·탐지 갱신·불확실성 확산).

## 6-B. v18.3 임무 배정 — ✅ 구현 완료 (v17.01.04, 2026-07-06)
**확정 설계**(4개 결정포인트 사용자 합의): ①재배정 6h 주기 + 이동 1틱(transit) ②임무 2종(초계/방어집중) ③위협도=적규모×임박, tier 비례 그리디 ④캠페인 내부 기본 동작(별도 플래그 없음).
**구현**: `_assign_missions()`(run 루프 `_tick_fuel` 후·`_tick_engagements` 전) — 위협 없는 교통로에 약한 함정 1척씩 초계 보강 후, 강한 함정(`_ship_strength`=max_channels)을 '위협 대비 배치 부족' 최대 zone에 그리디(방어집중). zone 변경분만 `transit` 상태 1틱. `_zone_threat`(도착 규모+임박×0.5)·`_return_zone`(복귀 최고위협). `CampaignShip`에 transit 상태·dest_zone·transit_eta_h. 결과에 n_transit·n_reassign.
**검증 교훈**: 초기 단순 그리디는 위협 한 곳 집중 시 **전원 집결→초계 임무 실종·동시 소진 조기종료** → calm 교통로 초계 보강으로 2종 임무 취지 충족. 헤드리스에서 조기종료 완화(38h→72h 완주)·교전 수↑·outcome 다양화 확인.

**(이하 원본 착수 설계 — 이력)**
**현 상태**: `_build_force`(engine_campaign.py)가 함정을 `SLOC_ZONES`에 순환 분산(`i % 3`) **고정 배치**하고, 이후 재배치 없음. 수리·재보급 복귀 시 랜덤 zone.
**목표**: 가용 함정을 **위협 기반으로 동적 재배정**(그리디). 강한 함정을 고위협 교통로에.

**설계 초안**:
- 신규 `_assign_missions()` — `run` 루프에서 `_tick_logistics` 후·`_tick_engagements` 전 호출(주기는 결정 필요).
- **zone별 위협도** = 그 zone 활성 적 웨이브 규모(편성 수) × 임박도. `_active_enemy_in(zone)` 재사용.
- **함정 강도** = featurize tier(`_AEGIS`>`_DDG`>`_FFX`>`_SMALL`) 또는 SHIP_DB `max_channels`/hp. 강→고위협 zone 그리디 매칭.
- **임무 유형**(MVP 2종): 초계(위협 없는 교통로 감시)·방어집중(고위협 교통로 호위). 타격·대잠은 후속.
- `_build_force`는 초기 배치만, 재배정은 `_assign_missions`가 담당.

**결정 포인트(착수 시 사용자 합의)**:
1. **재배정 주기**: 매 틱 vs N틱(예 6h)마다 — 잦으면 비현실(함정 순간이동), 드물면 대응 느림. **이동 시간**(zone 간 transit 상태에 틱 소요)을 넣을지.
2. **임무 유형 범위**: MVP 초계/방어 2종 vs 초계·호위·타격·대잠 4종.
3. **그리디 기준**: 위협도 = 적 규모 × 임박, 함정 강도 매칭 방식(1:1 vs 비례).
4. **하위호환**: 재배정이 기본 동작(캠페인 항상)인지, 별도 플래그인지. (캠페인 자체가 실험적이라 내부 로직으로 충분할 듯)

**공통**: 전술 엔진 무수정 유지 · 회귀 bit-identical · 난이도 높음 → **에포트 high 권장, 설계 먼저 합의**.

## 7. UI (MVP 최소)
- 설정에 `enable_campaign_mode` 토글(실험적). ON 시 워커가 `run_campaign` 라우팅(단발/전장/캠페인 3분기).
- 결과: 캠페인 요약(교통로 통제·잔존 전력·교전 수·outcome). 상세 타임라인은 v18.7.
- 새 결과 패널 or 기존 확장은 v18.1 구현 시 결정.

## 8. 하위호환 · 회귀
- 전술 엔진(`engine_combat.py`) **무수정** → 단발·전장 회귀 8×26 bit-identical.
- `enable_campaign_mode` OFF(기본) → 기존 경로 완전 무영향.
- 구버전 cfg(campaign 키 없음) 정상.

## 9. 리스크
- **아키텍처 결정이 이후 전부 좌우**(이벤트/틱 시간 모델·교전 해결 추상화). MVP서 검증 후 확장.
- **즉시예측 정확도**(R² win 0.78·score 0.84): 캠페인 누적으로 오차 전파 가능 → v18.6 MC로 분포 확인, 필요 시 정밀 엔진 혼용.
- **손실 추정 공백**: forecast_model이 손실 수 미추정 → MVP는 score 기반 추상 피해. 정밀화는 후속(모델에 손실 헤드 추가 or 정밀 엔진).
- 난이도 매우 높음 → **Opus/high, code-review high, 설계 먼저 합의**.

## 10. 번호 정합 위생 (착수 시)
로드맵_상세_v11-v20.md가 이 계열을 'v17 해군 작전급'으로 표기 → _PLANS(v18)와 한 칸 어긋남.
v18.1 착수 시 문서 번호를 v18로 정정(또는 _PLANS를 문서에 맞춤 — **_PLANS가 정본이므로 문서 수정**).
