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

## 10. RL 통합 + LLM 자가개선 루프 (Phase 4 — 본설계)

> **착수 합의(2026-06-20)**: 갈래 B(컷오버) 멈추고 Phase 4 진입. **속도 스파이크 통과** —
> 전장 에피소드 ~2,944틱/s(단일 프로세스), 1M PPO 스텝 ≈ 6분(로그·frames OFF·벡터 env면 더↓).
> 학습 속도는 병목 아님(초기 "며칠" 우려 철회). 무료 스택: Ollama(qwen2.5-coder:14b, 로컬)+SB3+torch CUDA(RTX 3080).
> **방식: 작게 시작(기존 레버) → 파이프라인 검증 → 행동공간 확장.** 전체 행동공간은 아래 박아둠.

**환경 아키텍처 (엔진 무변경 — 새 파일 `rl_env.py` 격리)**:
- `BattleEnv(gym.Env)` = **스레드 기반 cb-주도** 래퍼. `run_battle_simulation`을 백그라운드 스레드로 돌리고,
  엔진의 `_tactical_pause_cb`(원래 사람 GUI 입력 대기용 블로킹 훅)에 **RL 행동 주입**.
  `reset()`→첫 결정 지점 obs / `step(action)`→action 큐 put→cb 언블록→다음 결정까지 진행→obs·보상·done.
- 결정 빈도 = `_tactical_interval`초(현재 cb 호출 주기). 에피소드=1 전장. **engine_v7.py 한 줄도 안 고침.**

**관측(obs)** — `_make_tactical_state`(engine_v7:4195) → 고정 크기 숫자 벡터:
- 1단계(집계, ~15피처): 생존 위협 수·최근접/평균 거리·위협 총HP·생존 함정 수·함대 HP비·요격률·발사 수·목표 4종 진행도·t/horizon.
- 확장: 위협별 패딩 행렬(거리/HP/방위/유형), 자원(탄약·연료), 채널 포화.

**행동(action)** — 신규 비블로킹 API(`choice` dict, `_apply_tactical_choice` 확장):
- **1단계(기존 레버)**: `weapon_priority`(이산)·`max_salvo`. ← 파이프라인 증명용.
- **확장(plan 본설계 — 전부 박아둠)**: 방어전술 전환(포화↔분산↔기만)·표적 우선순위·레이더 ON/OFF(ARM 트레이드오프)·함대 기동(회피/진형)·CAP 전개·SAM 채널 배분·디코이/ECM 타이밍.
- 기존 블로킹 `_tactical_pause_cb`(사람 GUI용)는 유지 — RL은 같은 훅에 다른 cb 주입.

**보상(reward)** — 5절 `friendly_score`(0~1) 종료 시 + 결정마다 목표 진행도 델타 중간 shaping. **보상 해킹 감시**(과도 보수화·무의미 반복 점검).

**변수 다양화**: 적 시나리오 고정 + 살보·방위·혼합·ECM·타이밍 랜덤 → 강건 정책(과적합 방지). ← 사용자 "변수 여러 개" 요구.

**학습/추론 분리**: 학습 torch(개발 PC), exe는 `policy_weights.npz` numpy 추론만. v15.2 즉시예측과 동일 패턴.

**마일스톤**: ✅**①rl_env.py+랜덤롤아웃+PPO 학습배선 검증 완료(2026-06-20, 53스텝/s CPU, 커밋 af1555d)** → ②**균형 학습 시나리오**(현 이지스vs랴오닝 전패→학습신호 약함, 이기고 지는 게 갈리는 매치업 필요) → ③**벡터 env 가속**(SubprocVecEnv 8코어, ~6배) → ④행동공간 확장(위 레버) → ⑤본학습+강건화 → ⑥exe numpy 추론 통합 → ⑦LLM 자가개선 루프(10-B). **사용자 합의: ②③④ 순서 권장, 그 후 본학습.** 갈래 B(컷오버 판정·비용·편대)는 보류—RL 일단락 후 복귀 가능.

### 10-B. LLM 자가개선 루프 (Ollama qwen2.5-coder:14b — 사람 승인 게이트)

> **핵심 결정(2026-06-20)**: **무인 코드 자가수정 금지.** 검증 없는 엔진 자동수정은 회귀·골든·"부모 무수정"으로
> 막아온 조용한 손상을 AI가 스스로 주입 → 십중팔구 엔진 파손·보상 해킹. **제안 경로를 2단계로 가른다.**

오케스트레이터 루프(`auto_improve_loop.py`): `학습 → 약점 분석(구조화 리포트) → Ollama 호출(HTTP localhost:11434) → 게이트 적용 → 반복`.
- **Tier 1 (설정값 변경 → 완전 자동, 밤새 무인 OK)**: 보상 가중치·하이퍼파라미터·학습 시나리오 선택. config 숫자만 바뀜, 엔진 코드 무수정, 되돌리기 쉬움 = LLM 안내 보상·하이퍼파라미터 탐색.
- **Tier 2 (엔진 코드 변경 → 승인 게이트)**: 제안을 큐에 쌓고 `verify_regression.py` 자동 실행 → 통과해도 **사람 검토 후 적용**.
- "자동 제시"의 실체 = 루프가 평가 체크포인트마다 로컬 Ollama에 HTTP 1회. **약점을 숫자로 정의하는 분석(②)이 LLM보다 더 중요·어려움.**

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
- ✅ **적 항공 재접근 검증 완료 → Phase 1 종료** (2026-06-16): 항공 위협 중심(A2/AD 항공 포화) vs 강한 편대(이지스/전 이지스 기동전단)에서 적기가 발사→이탈→재접근을 반복(`[재공격] J-16 재접근 개시 1/3`, 회당 8회), **작전 시간 1800s 풀 지평까지 지속 후 승리**(자산 방어 성공). 옛 단발(~40s 쏘고 도망)과 명확히 대비. 압도적 입체 포화(최강)는 기함 격침으로 패배(325~402s) — 시나리오 강도별 판별력 확인.

## Phase 1 종료 요약 (v15.06.01~03)

지속 전장 모드가 엔진→토글→단일/MC 승패→결과 배너→자동 착지→지속 압박 검증까지 일관 작동. 기존 단발 모델과 공존(병행 구축). **다음 = Phase 2** — 승리조건 3종(해역 통제·소모전·자원 지속성) + 자원(탄약·연료) 시간 소모·기동 동역학.

## 다음 행동

- 코드/로직 감사(`/code-review`) — 새 엔진 클래스(아키텍처 전환) 정책상 필수.
- 이후 UI 통합 착수 (전장 모드 진입점 + 승/패 결과 표시).

---

# Phase 2 설계 합의 (2026-06-16 확정)

> 승리조건 3종(sea_control·attrition·sustainment) + 자원·기동 동역학.
> **합의된 3대 결정**: ①지표 3종 먼저(저위험) → 동역학 ②sustainment = 탄약+연료(연료 신규) ③웨이브·재보급은 Phase 3로 이관.

## 분할 (2개 마이너 블록)

### v15.07.x — 승리조건 3종 (출력 지표, 엔진 교전 로직 무변경 → 저위험)

세 목표 모두 "매 틱 기존 상태를 읽어 progress 계산"이라 물리·교전 코드를 안 건드린다.
`BattleEngine.objectives`에 추가하고 `_update_objectives`에서 갱신, `_score_outcome`이 자동 흡수.
종료 시 `_compile`에 `timeline` 추가.

**v15.07.01 — `sea_control` (해역 통제)**
- 보호점 = 함대 중심(기함 pos). 돌파선 `battle_sea_control_line_km`(기본 50km, cfg 조정).
- 매 틱: `closest` = 생존 적 위협 + 생존 `enemy_strike` 미사일의 보호점까지 최단거리.
- `penetration_km = clamp(line - closest, 0, line)`. **작전 전체 최악(최대 침투)** 누적 기록.
- `progress_friendly = 1 - max_penetration/line` (한 번이라도 자산 도달 시 0).
  `progress_enemy = 1 - progress_friendly`.
- status: 달성=돌파 0 유지(저지), 실패=완전 돌파(자산 도달).
- timeline `frontline_km`: `[(t, deepest_penetration_km), ...]`.

**v15.07.02 — `attrition` (소모전)**
- 전력 가치: 아군 = 생존 함정 `SHIP_PROCUREMENT_USD` 합(없으면 HP가중 fallback).
  적 = 생존 위협 수 기반 프록시(Phase 2; 적 자산 조달가 미보유라 count·표적가치 근사. 후속 정밀화).
- `friendly_frac = friendly_value_now / init`, `enemy_frac` 동일.
- 교환비 progress: `progress_friendly = logistic(k·(enemy_loss_frac - friendly_loss_frac))` → 아군이 적을 더 깎을수록 1.
  `progress_enemy = 1 - progress_friendly` (대칭).
- timeline `force_ratio`: `[(t, friendly_frac, enemy_frac), ...]`.

**v15.07.03 — `sustainment` (자원 지속성, 아군)**
- 잔여 자원 최저 비율 = `min(탄약_잔여비, 연료_잔여비)`.
  - 탄약 = `Σ remaining_inventory / Σ initial` (기존 추적값).
  - 연료 = v15.08.01 도입 전까지 탄약만, 도입 후 `min(fuel_frac)` 합산.
- `progress = 최저 비율`. status 실패 = 0(완전 고갈).
- timeline `resource_min`: `[(t, ammo_frac, fuel_frac), ...]`.

> **목표 가중치(cfg 조정)**: attrition은 양측 대칭 1쌍, sustainment는 아군 전용(표 4.1).
> 따라서 friendly = defend_asset 0.5 + sea_control 0.3 + attrition 0.2 + sustainment 0.2 = 1.2,
> enemy = destroy_asset 0.5 + sea_control(돌파) 0.3 + attrition 0.2 = 1.0.
> `_score_outcome`이 각 측 가중치 합으로 정규화하므로 합이 1이 아니어도 점수는 0~1 유지(v15.07.03 확정).
> Phase 1의 defend/destroy 0.6은 위 0.5로 재배분(점수식 일관성 — 5절).
> 결과 배너(`_fill_battle_panel`)에 목표 4종 전부 + timeline 미니 표시.

### v15.08.x — 동역학 (엔진 물리 변경 → 회귀 위험 ↑, Opus·/code-review high)

**v15.08.01 — 연료 소모 모델**
- 신규 필드 `FriendlyShipObj.fuel`/`fuel_max`. 매 틱 소모(기동량·speed_factor 반영).
- 기본값: horizon 1800s에선 여유, 장시간·고기동 시 압박되게 튜닝.
- sustainment 연료 항목 활성화. **회귀 영향**(신규 상태) → 변경 후 골든 재확인.

**✅ v15.08.04 — 적 목표지향 기동 AI (완료 2026-06-19, 커밋 cbba0e2)**
- (번호: 분석8종 제거가 08.02, 무장유한화 08.03 차지 → 기동AI는 08.04)
- 임시 레버(`battle_air_reattacks`) 제거. 이탈 대신 **무장 남는 한 압박 유지**(재접근 무한, max_reattacks 캡 폐지).
- 부모 무수정: `_on_retreat_arrived` 훅 추출(행동보존, 단발 회귀 PASS), BattleEngine 오버라이드.
- 손실 임계 철수(`_enemy_withdraw_check`): **전투 격침(intercepted)** 전력가치 ≥`battle_enemy_withdraw_loss`(0.5) 시 생존 세력 전면 egress. 재무장 복귀·자발 이탈은 손실 제외(/code-review high 발견 수정).
- **A안 합의**: egress 유지(현실적), 재출격 지연·웨이브 파상공격은 **Phase 3 이관**. sea_control 돌파선 지향 기동도 Phase 3.

**v15.08.03 — (Phase 3 이관) 웨이브·재보급** — Phase 2 범위에서 제외 확정.

## Phase 2 출력 스키마 증분 (`_compile`)

```python
result['timeline'] = {
    'frontline_km': [(t, deepest_penetration_km), ...],   # v15.07.01
    'force_ratio':  [(t, friendly_frac, enemy_frac), ...], # v15.07.02
    'resource_min': [(t, ammo_frac, fuel_frac), ...],      # v15.07.03
}
# objectives 4종으로 확장, friendly_score/enemy_score 가중치 재배분
```

> 단일 시뮬만 timeline 누적(`if not self._mc_mode` 가드 — frames와 동일 패턴). MC는 outcome·score만.

## Phase 2 감사

각 마이너 빌드 전 `verify_regression.py`(단발 모드 무영향 확인) + v15.07은 /code-review medium,
v15.08(엔진 물리)은 high. timeline은 단일 시뮬 전용이라 MC 3경로 영향 없음(스키마 키 추가만).
