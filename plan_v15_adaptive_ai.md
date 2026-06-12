# v15.1 — 적응형 전술 AI 설계

> 상태: **설계 합의 완료 (2026-06-12)** · 난이도 **매우 높음** · 모델 Opus 4.8 · 코드리뷰 `/code-review high`
> 접근: **규칙기반 적응** (MCTS 보류 — _PLANS "완벽한 적은 비현실" 권장)

## 1. 목표

적 지휘관이 교전 중 전장 상태를 주기적으로 평가해 전술을 **동적 전환**한다. 현재는 `ai_tactic`으로 전술 1개를 시작 시 고정 선택 → "적응형(자동)" 모드 신설.

전환 순서(_PLANS): **포화 → 분산 → 기만**.

## 2. 현재 구조 (기반)

| 요소 | 위치 | 동작 |
|------|------|------|
| 편대 구성 전술 `ai_tactic` | engine_v7.py:1516 전처리 | saturation(위협 수 증폭)·stagger(속도별 등장 지연)·exploit_weakness(단일 방위) — **시작 1회 고정** |
| 발사 전술 `_enemy_fire` | engine_v7.py:2342 | salvo=random(min,max), 표적=`_pick_target` |
| 표적 선택 `_pick_target` | engine_v7.py:1722 | 어뢰=기함(`_primary`), 대함=max_hp 가중 랜덤(분산) |
| UI 콤보 `cmb_ai_tactic` | launcher.py:6520 | 없음/채널 포화/시차 공격/약점 공략 |

## 3. v15.1 적응형 모드

**enable = `ai_tactic == 'adaptive'`** → 기존 고정 전술/None은 경로 완전 불변 → **회귀 PASS 보장**.

### 상태 지표 (이미 stats/구조에 존재)
- `sat`  = 비행 중 위협 수 / 아군 총 교전 채널 (채널 포화도)
- `irate`= intercepted / fired (누적 요격률, fired>0)
- `losses` = 격침된 적 플랫폼 수

### 전술 모드 & 전환 규칙
| 모드 | 진입 조건 | `_enemy_fire`가 바꾸는 것 |
|------|-----------|--------------------------|
| **SATURATION**(포화) | 초기 / irate 낮음(잘 뚫림) | salvo=max, 동시 발사, 표적=기함 집중(`_primary`) |
| **DISPERSAL**(분산) | irate 높음(>0.5) & 채널 여유(sat<0.7) | salvo=중, 일부 시차(pending), 표적=HP가중 분산 |
| (기만) | **v15.01.02** | ECM 동반·시차 극대 — 1단계 제외 |

> "방위 분산"은 적 함정 위치가 발사 시점 고정이라 발사 방위를 직접 틀지 않고 **표적 분산 + 시차**로 채널을 분할(여러 함정이 여러 방향에서 위협 → 실질 방위 분산). 물리적으로 자연스러움.

### 통합 지점
- 신규 `_adaptive_tactic_update()`: 주기(20초)마다 상태 평가 → `self._adaptive_mode` 갱신. 전환 시 교전 로그 기록("왜 바꿨는지").
- `_enemy_fire`: `self._adaptive_mode` 분기 (salvo 배율·동시/시차·표적). adaptive 아니면 기존 random 경로 그대로.
- run 틱 루프에서 `_adaptive_tactic_update()` 주기 호출.
- `__init__`에 `self._adaptive_mode`, `self._adaptive_last_t` 초기화. `_id_counter`처럼 run 진입부 리셋 불필요(인스턴스 단위).

## 4. 단계 분리

| 버전 | 범위 |
|------|------|
| **v15.01.01** | ✅ 완료 (2026-06-12) — 적응 컨트롤러(`_adaptive_tactic_update`, 20초 주기) + 포화↔분산 전환(salvo·표적 집중/분산) + 전환 로그. `_enemy_fire` 분기, `ai_tactic='adaptive'` 가드로 회귀 무영향. 검증: '전 이지스 vs 대잠 복합'서 요격률 83% 시점 분산 전환 확인. |
| v15.01.02 | ✅ 완료 (2026-06-12) — **기만 침투**(deception) 모드. 진입 irate>0.7(분산도 못 뚫음). 효과: 종말 회피 강화(`terminal_evasion_factor ×0.6`, 하한 0.2)+살보 최소(시차 극대)+표적 분산. ECM/디코이는 적 항공기 속성/신메커니즘이라 보류, 미사일 종말 회피로 기만 표현. 회귀 PASS. |
| v15.01.03 | 난이도별 적응 민감도 조정 + 전환 시각화(교전 로그 강조) |

> **1단계 구현 노트**: `_pick_target`(random.choices)을 `offset`(random.uniform)보다 먼저 호출하면 비-adaptive 경로의 random 순서가 깨져 회귀 FAIL → 표적 선택을 offset 뒤로 배치해 순서 보존(중요). 전환은 누적 요격률 기반이라 관성이 큼 — 요격률 낮은 강한 적 시나리오에선 saturation 유지가 정상(전환 드묾). 더 민감하게 하려면 v15.01.03에서 슬라이딩 윈도우 검토.

## 5. 하위 호환 / 회귀

- `ai_tactic='adaptive'` 외 모든 경로 불변. 신규 `random` 호출은 adaptive 모드에서만 → 비-adaptive 회귀 영향 0.
- `self._adaptive_mode`는 새 인스턴스 속성. `_compile`·MC 경로 무관(stats 키 추가 시 MC 3경로 동시 반영 — 1단계는 stats 키 추가 없음, 로그만).
- 3종 세트: 콤보 항목 '적응형(자동)' 추가 + cfg 빌드(`.get(...)` 매핑에 'adaptive') + cfg 로드(restore).

## 6. 검증

- adaptive OFF: `verify_regression.py` PASS (변경 전·후).
- adaptive ON: 단발 시뮬에서 전환 로그 발생·모드 변화 확인. 요격률 변화 관찰.
- 코드리뷰 high (엔진 교전 분기 신설).
- exe 스모크: 콤보 '적응형(자동)' 선택 → 시뮬 → 교전 로그에 전술 전환 표시.
