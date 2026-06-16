# 지속 전장 엔진 설계 문서 (Phase 0)

> 아키텍처 전환 — 단발 살보 교전 모델을 **양측이 목표를 두고 시간에 걸쳐 겨루는 지속 전장 모델**로 전면 교체.
> 최종적으로 RL 기반 방어 정책 학습(self-play)까지 확장.
> 본 문서는 Phase 0 산출물(설계 합의). 합의 후 Phase 1 구현 착수.

---

## 1. 목적 · 배경

현재 엔진(`TimeStepEngine`)은 **단발 살보 전술 교전 해결기**다. 적은 접근→발사→`is_retreating`→재공격 한도 소진 시 `et.alive=False`("전장 이탈")로 사라진다(`engine_v7.py:2256-2267`). 적에게 "쏘고 빠진다" 외의 목표가 없고, `_is_over`가 위협 소진 시 조기 종료한다(`:4119`). 그래서 "요격하고 도망"처럼 느껴진다.

빠진 것은 화력(양방향 화력은 `_friendly_strike`·`_aircraft_aas`로 이미 존재)이 아니라 **① 양측의 목표·승리조건 ② 시간에 걸친 기동·자원 관리 ③ 적의 목표지향 의사결정**이다.

이 셋을 채우면 "완전한 전장"이 되고, 적이 목표지향 AI가 되는 순간 **아군 방어 정책 + 적 정책을 둘 다 학습시키는 self-play 반복학습**이 성립한다.

## 2. 범위 · 끝 상태

**끝 상태 (전면 교체):**
- 단발 살보 모델 **삭제**. 지속 전장 모델이 유일한 엔진 경로.
- 승리조건 4종 전부 지원: **자산 방어 · 해역 통제(돌파 저지) · 소모전(전력 비율) · 자원 지속성**.
- 적은 목표지향 의사결정(Phase 1 규칙기반 → Phase 4 학습).
- 출력은 요격률이 아니라 **승/패/무 + 목표 달성도 + 전력·자원 시계열**.
- 다운스트림(결과·판정·MC·비용·편대추천) 전부 새 지표로 재작성.

**실행 원칙 (점진 컷오버 — 빅뱅 금지):**
- 새 엔진을 옆에 짓고 검증 → 다운스트림 적응 → **그 시점에 옛 모델 삭제**.
- 구축 중 `v15.04.01`은 안정 fallback으로 동결.
- 결과적으로 전면 교체, 방법은 병행+하드컷오버.

## 3. 재사용 vs 재작성

| 물리층 — **그대로 재사용** | 오케스트레이션층 — **재작성** |
|---|---|
| 무기 Pk(Beta `pk_dist`), RCS 탐지, 소나 방정식, 침수 모델, 미사일 비행(PNG), ECM, IFF, 해류, 지형 차폐 | 시간 지평·종료조건(`_is_over`), 양측 목표 상태머신, 적 목표지향 AI, 자원 소모 동역학, 결과 지표(`_compile`), RL 행동 API |
| DB 전체 (`ENEMY_DB`·`FRIENDLY_DB`·`SHIP_DB`·`FRIENDLY_STRIKE_DB`·`*_FLEET_PRESETS`·`FRIENDLY_AIRCRAFT_DB`) | 시나리오 정의(목표·초기 배치·웨이브·재보급) |
| 객체 모델 (`MissileObj`·`FriendlyShipObj`·`EnemyThreatObj`·`FriendlyAircraftObj`) 의 **물리 필드** | 위 객체의 **행동 의도/목표 필드** 신규 추가 |

핵심: "어떻게 맞고 어떻게 가라앉나"는 검증된 코드 그대로, "무엇을 두고 얼마나 오래 싸우나"만 신규.

## 4. 목표 상태머신 (Objective State Machine)

전장은 **양측의 목표 집합 + 각 목표의 진행 상태**로 정의된다. 매 틱 목표 상태를 갱신하고, 종료조건은 목표 달성/실패/시간초과로 판정한다.

### 4.1 목표 타입 (4종)

각 목표는 `{type, side, params, progress, status}` 구조. `status ∈ {진행, 달성, 실패}`.

| 목표 타입 | 보유측 | 달성 조건 | 진행 지표 |
|---|---|---|---|
| **자산 방어** `defend_asset` | 아군 | 지정 자산(기함·항모) 종료 시점 생존 | 자산 HP 비율 |
| **자산 격침** `destroy_asset` | 적 | 지정 아군 자산 격침 | 동일 자산 HP (반대편 관점) |
| **해역 통제** `sea_control` | 양측 | 적이 방어선(거리/구역) 돌파 여부 | 최근접 침투 위협의 방어선 대비 위치 |
| **소모전** `attrition` | 양측 | 종료 시 전력비(잔존 가치/초기 가치) 비교 | 양측 잔존 전력 가치 비율 |
| **자원 지속성** `sustainment` | 아군 | 작전 종료까지 탄약·연료 소진 없이 지속 | 잔여 탄약·연료 최저치 |

> 자산 방어와 자산 격침은 **같은 자산을 두 관점에서** 본 것(아군은 지키고 적은 부순다). 시나리오는 이 둘을 쌍으로 정의한다.

### 4.2 시나리오 = 목표 묶음

시나리오가 양측 목표 집합·가중치·종료조건을 정의한다. 예:

```
시나리오: "항모전단 자산 방어"
  아군 목표: defend_asset(항모, w=0.6) + sustainment(w=0.2)
  적   목표: destroy_asset(항모, w=0.6) + sea_control(돌파선 50km, w=0.4)
  종료: 어느 목표든 확정 OR t >= horizon(예 1800s)
```

Phase 1 MVP는 **`defend_asset`/`destroy_asset` 한 쌍만** 구현(나머지 3종은 Phase 2).

## 5. 승패 점수식

종료 시 양측 점수를 계산해 승/패/무를 가른다. 요격률을 대체하는 **단일 스칼라 + 세부 항목**.

```
side_score = Σ_objectives ( w_i * progress_i_normalized )     # 0..1
outcome:
    win   if  friendly_score - enemy_score >  margin
    loss  if  enemy_score - friendly_score >  margin
    draw  otherwise
```

- `progress_normalized`: 목표별 0(완전 실패)~1(완전 달성)로 정규화.
  - `defend_asset`: 자산 생존=1, 격침=0, 손상 시 HP 비율.
  - `sea_control`: 돌파 0, 완전 저지 1, 부분 침투 비례.
  - `attrition`: 교환비를 로지스틱으로 0..1 사상.
  - `sustainment`: 잔여 자원 최저 비율.
- 편대 추천·MC 가중치와 **일관성 유지**: 기존 `요격0.6+생존0.4`를 목표 가중치 체계로 흡수.
- `margin`: 무승부 판정 폭(설계 시 튜닝, 초기 0.1 제안).

## 6. 새 출력 스키마

`_compile` 반환 dict를 다음으로 교체(기존 물리 통계는 유지하되 **중심 지표를 outcome로 이동**).

```python
{
    # ── 신규 핵심 ──
    'outcome':          'win' | 'loss' | 'draw',
    'friendly_score':   float,            # 0..1
    'enemy_score':      float,
    'objectives': [                       # 목표별 결과
        {'type', 'side', 'status', 'progress', 'weight'}, ...
    ],
    'timeline': {                         # 시계열 (단일 시뮬만)
        'force_ratio':  [(t, friendly_value, enemy_value), ...],
        'resource_min': [(t, ammo_frac, fuel_frac), ...],
        'frontline_km': [(t, deepest_penetration_km), ...],
    },
    # ── 유지 (물리 통계, 하위 분석·디버그용) ──
    'sim_time', 'frames', 'log', 'friendly_ships', 'enemy_ships',
    'remaining_inventory', 'total_channels', 'total_cost',
    'ship_subsystem_damage', 'used_seed',
    # intercept_rate: 보조 지표로 강등(삭제 아님 — 디버그·연속성)
    'intercept_rate':   float,
}
```

> `frames`·`build_czml`(3D 전장)은 그대로 동작 — 위치 히스토리 기반이라 출력 스키마 변경 무관.

## 7. 컷오버 전략 (다운스트림 영향)

`intercept_rate`를 소비하는 곳이 `launcher.py` 18곳 + MC 3경로. 컷오버는 **다운스트림별로 새 지표 매핑**이 필요하다.

| 다운스트림 | 현재 | 교체 후 |
|---|---|---|
| 결과 탭 | 요격률 게이지·교전 로그·MC CI | **승/패 배지 + 목표 달성판 + 전력·자원 시계열 + 교전 로그** |
| 판정 탭 (REQ) | "요격률 ≥ X" 류 판정 | **목표 기반 REQ** ("기함 생존률 ≥ X", "돌파 저지율 ≥ Y") |
| MC (`monte_carlo_v7`·`_mc_batch_worker`·`monte_carlo_lhs`) | 요격률 분포 | **승률·목표 달성률·교환비 분포** (3경로 동시 갱신 — CLAUDE.md 체크리스트 7) |
| 비용효과 | 요격당 비용 | **승리당 비용 / 목표 달성당 비용** |
| 편대 추천 (`recommend_fleet_v7`) | 요격률+생존 점수 | **승률+목표 점수** (5절 점수식 재사용) |
| 회귀 (`verify_regression.py`) | 요격률 골든 | **새 모델 골든 전면 재생성** (`--update`) |
| 기준값 메모리 | `baseline_v11/png/sonar/flooding/v12_combined` | **새 엔진 기준값 재측정** |

**컷오버 순서**: 새 엔진 + 결과 탭(승/패 표시) 먼저 → MC 3경로 → 판정/비용/편대 → 골든·기준값 재생성 → **옛 단발 모델·요격률 중심 코드 삭제**.

## 8. Phase 분할

```
Phase 0  설계 합의 (본 문서)
Phase 1  코어 MVP
         - 종료조건을 목표 상태머신으로 교체 (_is_over → 목표 판정)
         - defend_asset / destroy_asset 한 쌍
         - 적 목표지향 AI (규칙기반): 이탈 대신 자산 압박·기동
         - outcome 출력 + 결과 탭 승/패 표시
         - 물리층 무수정. 단일 시뮬로 "전장이 말이 되는지" 검증
Phase 2  승리조건 확장 + 동역학
         - sea_control · attrition · sustainment 3종
         - 자원(탄약·연료) 시간 소모, 재배치 기동, 웨이브·재보급
Phase 3  다운스트림 재작성 + 컷오버 완료
         - 결과·판정·MC(3경로)·비용·편대추천 새 지표화
         - 새 골든·기준값 측정 → 옛 모델 삭제 (= 전면 교체 완성)
Phase 4  RL 통합
         - 행동 API (run() 루프에 비블로킹 obs→action 주입)
         - 방어 정책 학습(오프라인 torch) → exe엔 가중치만(numpy 추론)
         - self-play: 적 규칙기반 → 학습 정책으로 교체
```

각 Phase는 자체 마이너 버전들로 쪼개 진행. Phase 경계마다 회귀·감사.

## 9. 적 AI 설계 (Phase 1 규칙기반)

현재 `_enemy_fire` + v15.1 적응형(`_adaptive_tactic_update`: 포화↔분산↔기만)을 **목표지향 행동 트리**로 확장:

```
적 목표 = destroy_asset(아군 기함/항모)
매 재평가 주기:
  1. 목표 자산까지 접근/침투 (이탈 로직 제거 — 목표 미달 시 압박 유지)
  2. 방어 포화 평가 → 살보 집중 vs 분산 (기존 적응형 재사용)
  3. 손실 임계 초과 시에만 후퇴/재편 (자원 보존), 목표 포기는 시나리오 조건부
  4. sea_control 목표 시 돌파선 지향 기동
```

**규칙기반으로 전장 안정화 후** Phase 4에서 학습 정책으로 교체. 처음부터 self-play 금지(환경·학습 동시 불안정 → 디버깅 불가).

## 10. RL 통합 지점 (Phase 4 — 미리 설계만)

- **환경**: 지속 전장 엔진을 gymnasium 규격으로 래핑. 에피소드 = 1 전장.
- **관측**: `_make_tactical_state` 확장 → 숫자 벡터(위협 거리/HP/방위, 함정 HP/자원, 목표 진행).
- **행동**: 신규 비블로킹 행동 API(방어전술 전환·표적 우선·레이더 ON/OFF·기동·CAP 전개). 기존 블로킹 `_tactical_pause_cb`는 사람용으로 유지.
- **보상**: 5절 `friendly_score`(목표 달성도) — 종료 시 + 중간 shaping.
- **변수 다양화**: 적 시나리오 고정 + 살보·방위·혼합·ECM·타이밍 랜덤 → 강건 정책(과적합 방지). ← 사용자 "변수 여러 개" 요구 반영.
- **학습/추론 분리**: 학습 torch(개발 PC), exe는 `policy_weights.npz` numpy 추론만. v15.2 즉시예측과 동일 패턴.

## 11. 리스크 · 회귀 전략

| 리스크 | 대응 |
|---|---|
| 빅뱅 재작성으로 프로젝트 정지 | 병행 구축 + 하드 컷오버. v15.04.01 fallback 동결 |
| 다운스트림 광범위 파손 | 컷오버 순서(7절) 따라 단계 교체, 단계마다 빌드·스모크 |
| 골든·기준값 무효화 | 새 모델 안정 후 일괄 재생성, 메모리 기준값 재측정 |
| 적 AI·승패식 밸런스 붕괴 | 규칙기반 우선, 다수 시나리오 스모크로 "말이 되는지" 검증 후 RL |
| MVP 과욕(4목표 동시) | Phase 1 = defend/destroy 1쌍만 |

**감사**: 아키텍처 전환(난이도 매우 높음) → Phase별 `verify_regression.py`(새 골든) + `/code-review high` + 핵심 경로 로직 트레이스. 모델 Opus.

## 12. 합의된 결정 기록

- **방식**: 전면 교체(끝 상태) + 점진 컷오버(방법). 빅뱅 금지.
- **승리조건**: 4종 전부(자산 방어·해역 통제·소모전·자원 지속성). MVP는 자산 방어 1쌍부터.
- **적 AI**: Phase 1 규칙기반 → Phase 4 학습(self-play).
- **버전**: 다음 메이저(아키텍처 전환). 기존 v15.3~v21 기능 로드맵 **일시 중지**. v15.04.01 동결.
- **로드맵 재편**: v15.2 즉시예측 **연기**(새 엔진 위 재작성), v18 캠페인 **흡수**(전장 엔진의 작전급 확장).

---

## 확정된 결정 (Phase 1 착수)

1. **시간 지평**: `BATTLE_HORIZON_S = 1800`초(30분). cfg `battle_horizon_s`로 조정 가능.
2. **MVP 시나리오**: 기준 시나리오(`기동전단 기본` vs `랴오닝 항모전단`) — `baseline_v12_combined` 기준값 보유로 즉시 검증 가능.
3. **새 엔진 배치**: `BattleEngine(TimeStepEngine)` **상속** — 물리층 재사용, 오케스트레이션만 오버라이드, **부모 무수정**(골든·fallback 안전). 컷오버 시 부모 삭제하며 독립.

## Phase 1 진행 현황

- ✅ **코어 골격 완료** (engine_v7.py): `Objective` + `BattleEngine` + `run_battle_simulation`.
  - `_is_over` 오버라이드 — 위협 소진 종료 → **목표 기반 종료**(자산 격침=적승 / 시간 지평·적 격멸=방어성공 / 아군 전멸=적승).
  - `_compile` 오버라이드 — `outcome(win/loss/draw)`·`friendly_score`·`enemy_score`·`objectives` 추가. `intercept_rate`는 보조 지표로 유지.
  - 적 지속 압박 — 항공 위협 `max_reattacks` 상향(임시 레버, Phase 2서 목표지향 AI로 교체).
  - **회귀 PASS**(부모 무변경) + 스모크 실행(기준 시나리오 3시드 outcome 산출 확인).
- ✅ **UI 통합 완료** (launcher.py, v15.06.01): `enable_battle_mode` 토글 3종 세트(환경 묶음 체크박스 + cfg 빌드 + cfg 로드) + 워커 단일 시뮬 라우팅(`run_battle_simulation`) + 결과 상태줄 승/패 표시(⚔ 전장 결과) + `run_battle_simulation`에서 진행바 총량을 horizon으로 보고(step_cb 래핑). 회귀 PASS·빌드 성공.
- ✅ **MC 전장 승률 집계 완료** (engine_v7+launcher, v15.06.02): `_mc_run_one`(전장/단발 라우팅) + `_battle_agg`(승/패/무 승률·평균 임무점수). 4개 시뮬 호출부(`monte_carlo_v7`·`_mc_batch_worker`·`_mc_lhs_batch_worker`·`monte_carlo_lhs` 폴백) + 병렬 조립부는 `extra_stats` 경유(튜플 인덱스 무변경). 상태줄 'MC 승률' 표시. 회귀 PASS(단발 무영향)·전장 MC 집계 검증(기동전단 vs 랴오닝 승률 0%/패 100%).
- ✅ **결과 탭 목표 달성판 완료** (v15.06.03): 교전 분석 탭 상단 작전 결과 배너(승/패/무·아군·적 임무 점수·작전 시간·목표별 달성도). `EngagementAnalysisTab._fill_battle_panel`, 전장 모드만 표시·단발은 숨김. 회귀 PASS·빌드.
- ⬜ **남은 Phase 1**: 적 항공 재접근(`max_reattacks` 상향)이 실제로 드러나는 강한 방어 시나리오 검증 → 이후 Phase 1 종료, Phase 2 착수.

## 다음 행동

- 코드/로직 감사(`/code-review`) — 새 엔진 클래스(아키텍처 전환) 정책상 필수.
- 이후 UI 통합 착수 (전장 모드 진입점 + 승/패 결과 표시).
