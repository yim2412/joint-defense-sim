# 합동 통합방어 시뮬레이터 — 프로젝트 규칙

## 프로젝트 개요

한국 해군 이지스 기동전단의 다층 방어 시뮬레이터. 대공·대함·대잠 위협에 대한 교전 시뮬레이션, 몬테카를로 분석, 요구조건(REQ) 판정, Excel/PNG 보고서 생성을 수행한다.

### 파일 구조

| 파일 | 역할 |
|------|------|
| `engine.py` | 핵심 DB (ENEMY_DB·FRIENDLY_DB·SHIP_DB 등), 물리모델, 탐지·교전 로직 |
| `engine_v7.py` | 시간 스텝 기반 양방향 교전 엔진. engine.py DB를 import해서 사용 |
| `launcher.py` | PyQt6 런처 — UI, 시뮬 워커, 결과 탭, DB 탭, 향후 계획 탭 등 전체 앱 |
| `spec_db.py` | DB 탭 스펙시트 패널용 상세 설명 (origin, categories, note) |
| `changelog.json` | 패치 이력 (배열, 버전 번호 순서) |
| `launcher.spec` | PyInstaller 빌드 스펙 |
| `_make_bg.py` | 홈 배경 이미지 생성 스크립트 (src_kf21_source.jpg → home_bg.jpg). 빌드 제외, 수동 실행용 |

### 실행 방법

```powershell
# 런처 실행 (개발 중)
python launcher.py

# exe 빌드
python -m PyInstaller launcher.spec --noconfirm
```

### 필수 패키지

```
pip install matplotlib numpy scipy openpyxl pillow pandas PyQt6 PyQt6-WebEngine psutil SALib
```

---

## 버전 관리 규칙

### 버전 체계

```
v{major}.{minor}.{seq}   (minor·seq는 항상 두 자리, 한 자리면 0을 채움)

major : 아키텍처 전환 시에만 증가 (예: v7=PyQt6 도입, v12=현재). 패딩 안 함
minor : 신기능/대규모 패치 묶음의 계열 (v12.01, v12.02, 두 자리도: v12.11)
seq   : 같은 minor 계열 안에서 변경 1건마다 붙는 일련번호 (.01, .02, .03 …)
```

- **changelog는 변경(추가/수정/삭제) 1건당 버전 1개**로 분리해 기록한다.
- 같은 minor 계열(기능 추가분 + 그 후속 버그수정)은 seq를 **연속**으로 잇는다.
  예: v12.05 계열 = v12.05.01(동적 기상) + v12.05.02(버그 수정).
- **'patch'라는 단어는 쓰지 않는다** — `vX.YY.ZZ` 3단계 번호가 그 역할을 대신한다.
- `APP_VERSION`·헤더 버전은 항상 **가장 최신 변경 번호**로 갱신한다.

### 버전 번호 갱신 규칙

`launcher.py` 최상단 헤더와 `APP_VERSION` 상수를 **패치 완료 시 수동으로 직접 수정**한다.

### 헤더 주석 규칙

`launcher.py` 최상단 헤더에 현재 버전과 최근 변경 내용을 기록한다.

```python
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   합동 통합방어 시뮬레이터  vX.YY.ZZ — PyQt6 런처                          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  [vX.YY.ZZ — 변경 내용 한 줄 요약]                                          ║
║  NEW-A  추가 기능                                                            ║
║  BUG-1  버그 수정                                                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
```

**파일 하단 패치 이력 블록은 작성하지 않는다.** 변경 이력은 git 커밋 메시지로 관리한다.

코드 내 인라인 주석은 "왜 이렇게 했는지" 비직관적인 수치·결정에만 단다.

```python
# BUG-5: SAM 근접 신관 실제 범위 (기존 2000m 과대)
INTERCEPT_DIST_M = 200
```

### 용어 작성 규칙 (exe 표시 텍스트 전용)

**앱 화면(exe)에 보이는 텍스트는 군사용어로 쓰되, 코드 명칭은 절대 쓰지 않는다.**
대상: `changelog.json`(패치 내역 탭), `_PLANS`(향후 계획 탭).

| 쓴다 ✅ | 안 쓴다 ❌ |
|---------|-----------|
| 군사용어 (종말 회피 기동, BVR 교전, CIWS, ARM, 살보, SEAD, 제공권) | 함수명 (`_aircraft_cap()`, `_friendly_defense()`) |
| 무기·장비 정식명 (SM-3, 해성-II, KF-21, 이지스) | 클래스·필드명 (`MissileObj`, `cec_relay`, `pk_base`) |
| 수치 변화 (사거리 650km로 상향) | 변수·인자명 (`sobol_npp`, `_tactical_max_salvo`) |

**한 줄 원칙: "군사 보고서처럼 읽히게, 코드 주석처럼 읽히지 않게."**

군사용어는 이 분야의 정확한 표현이므로 **적극 사용**한다. 길게 풀어 쓰기보다 제대로 된 용어로 조인다. (예: "적의 근접 방어 화기로 막는 시스템" → "적 CIWS 근접 방어 요격") 단, 코드 명칭은 절대 쓰지 않는다.

```
❌ "_aircraft_cap(): 적 항공기 BVR 요격 로직 (즉시 Pk, 60s cooldown)"
✅ "한국 공군 CAP 전투기가 적 항공기를 BVR 교전으로 요격"
```

함수명·클래스명 등 코드 명칭이 꼭 필요하면 **git 커밋 메시지·launcher.py 헤더 주석·개발 문서(로드맵_상세*.md)**에 적는다. 이들은 exe에 안 보이므로 제약 없음.

`_PLANS`의 구현 세부(클래스 구조·함수명)는 설명에 넣지 말고 `로드맵_상세_v11-v20.md`로 보낸다.

#### changelog 항목 유형별 작성법

| 구분 | 작성법 |
|------|--------|
| `추가` (신기능) | 주어 + 동작을 일상어로. 함수명·클래스명 금지 |
| `수정` (수치) | "무엇을 얼마로" (예: SM-3 사거리 650km로 상향) |
| `수정` (버그) | "어떤 증상이 고쳐졌는지" (코드 위치 아님) |

```
❌ 추가  _aircraft_cap() 신설 — 적 항공기 BVR 요격 로직
✅ 추가  한국 공군 CAP 전투기가 적 항공기를 BVR 교전으로 요격
❌ 수정  _select_defense_wpn() range_km 기본값 0 → 500
✅ 수정  전술 모드에서 지정 무기가 사거리 밖으로 잘못 판정되던 문제 해결
```

### 레이블 규칙

| 레이블 | 의미 |
|--------|------|
| `NEW-A`, `NEW-B`, ... | 신기능 (같은 버전 내 알파벳 순서로 누적) |
| `BUG-1`, `BUG-2`, ... | 버그 수정 (버전 내 번호 재시작) |
| `DEL-A`, `DEL-B`, ... | 기능 자체를 제거할 때만 사용. 버그 수정으로 코드가 삭제되는 건 BUG 레이블 |

### Git 커밋 규칙

기능 단위로 완성 후 커밋한다. 작업 중간 상태는 커밋하지 않는다.

```
커밋 메시지 형식 (변경 1건 = 버전 1개):
v12.06.01: [변경 내용 한 줄 요약]
```
한 작업에서 변경이 여러 건이면 changelog는 건별로 분리(v12.06.01, v12.06.02 …)하되,
커밋은 묶어서 하고 메시지 제목엔 대표 번호 범위(예: `v12.06.01~v12.06.03`)를 쓴다.

### 감사 정책 (마이너 버전마다 — 빌드·커밋 전 수행)

**모든 마이너 버전(vXX.Y) 완료 시, 변경 유형에 맞는 감사를 빌드 직전에 1회 수행한다.**
유형이 맞지 않는 감사는 생략한다(UI만 바꿨는데 수치 감사 금지).

| 변경 유형 | 감사 종류 | 방법 |
|-----------|-----------|------|
| 엔진 로직·새 클래스·교전 흐름 변경 | **회귀 검증 + 코드/로직 감사** | `python verify_regression.py` (PASS 필수) + `/code-review medium` (난이도 높음↑이면 high) |
| DB 수치·물리 파라미터 변경 | **회귀 검증 + 현실성 수치 감사** | `python verify_regression.py` + 공개 제원·교리와 대조 (수동 또는 Explore 에이전트) |
| UI·시각화·문서만 변경 | **회귀 확인** | 빌드 성공 + 스모크 실행만 (엔진 미변경 시 회귀 스크립트 생략 가능) |
| 아키텍처 전환(난이도 매우 높음) | **회귀 검증 + 코드 감사 + 로직 트레이스** | `python verify_regression.py` + `/code-review high` + 핵심 경로 수동 추적 |
| **신기능(`추가`) 포함** | **용어 확인** | 새 군사용어가 생겼는지 changelog·_PLANS 검토 |

신기능이 없는 버그·수치·UI 변경은 용어 확인 생략. `추가` 항목이 하나라도 있을 때만 확인.

> **스모크 실행** 정의: exe 실행 → 기본 시나리오 단일 시뮬 1회 → 결과 탭 정상 표시 확인. **exe는 `CloseMainWindow()`로 정상 종료** — `Stop-Process -Force` 금지(시작 시 워커 풀 예열 중 강제종료하면 멀티프로세싱 자식이 WinError 87 에러창을 띄움. 코드 버그 아닌 강제종료 아티팩트).
>
> **스모크 실행 대체 금지**: exe에서 시뮬레이션 버튼을 실제로 클릭하는 데 실패하면, 엔진 직접 호출(`run_v7_simulation()`)로 우회하지 않는다. 엔진 직접 호출은 GUI 워커 경로(step_cb, 시그널 emit 등)를 거치지 않아 exe 전용 버그를 놓친다. 자동화 실패 시 **BLOCKED로 보고하고 사용자에게 직접 시뮬 1회 실행을 요청**한다.

> **회귀 검증(`verify_regression.py`) 정의**: 고정 8개 시나리오×고정 seed 결과를 `regression_golden.json`(repo 저장)과 대조. **엔진 동작이 의도치 않게 바뀌면 FAIL** (C&D id 버그처럼 조용한 변화를 잡음). 사용: 검사 `python verify_regression.py` / 의도된 변경 후 갱신 `python verify_regression.py --update`. **엔진·DB·교전 로직을 고치면 변경 전 PASS 확인 → 변경 후 재실행**이 기본. FAIL이면 의도된 변경인지 판단(맞으면 `--update`, 아니면 버그). 결정론 의존(seed 고정)이라 신규 `random` 호출 추가는 정상 변경이어도 FAIL 가능 → 의도 확인 후 갱신.

**메이저 블록 완료 시(v11, v12 … 각 묶음의 마지막 마이너 직후):**
전체 회귀 MC(기준 시나리오) + 누적 수치 감사 1회 — 블록 통합 후 상호작용 버그 점검.

감사에서 발견한 항목은 **그 자리에서 수정 후 커밋**한다(다음 일련번호 부여). 감사 결과는 커밋 메시지에 1줄 요약.

### 패치 완료 시 필수 체크리스트 (매번 반드시 수행)

**어떤 코드를 수정하든 패치 완료 후 아래를 반드시 처리한다.**

0. **감사 수행** (위 '감사 정책' 표 — 변경 유형에 맞는 감사를 빌드 전에)

1. **launcher.py 헤더 버전 번호 갱신** + **`APP_VERSION` 상수 갱신** (현재 버전으로)

2. **changelog.json 갱신**: 새 항목을 배열 마지막에 추가
   ```json
   {
     "version": "vX.YY.ZZ",
     "date": "YYYY-MM-DD",
     "title": "변경 내용 제목",
     "changes": ["추가  ...", "수정  ...", "삭제  ..."]
   }
   ```
   `version` 필드는 변경 1건마다 `vX.YY.ZZ` 3단계 번호를 사용한다. 'patch' 표기 금지.

3. **향후 계획 탭 갱신** (`launcher.py` → `_build_plan_tab()` 내 `_PLANS`):
   - 구현 완료된 항목은 **즉시 삭제**한다.
   - 새 계획 생기면 추가한다.
   - **`_PLANS` 변경(추가·삭제 모두) 후에는 반드시 전체 빌드**한다. `_PLANS`는 `.py` 코드이므로 빌드 없이는 exe에 반영되지 않는다.

4. **dist 폴더 갱신 (빠뜨리지 말 것)**:

   | 변경 파일 | 처리 |
   |-----------|------|
   | `.py` 파일 변경 | **전체 빌드** `python -m PyInstaller launcher.spec --noconfirm` |
   | `changelog.json`만 변경 | `_internal` 폴더에 복사만 |
   | `spec_db.py`만 변경 | `_internal` 폴더에 복사만 |
   | `.py` + json 동시 변경 | **전체 빌드** 후 복사 불필요 (빌드 시 자동 포함) |

   ```powershell
   # .py 변경 시 — 전체 빌드
   python -m PyInstaller launcher.spec --noconfirm

   # json/spec_db만 변경 시 — 복사만
   Copy-Item changelog.json "dist\이지스_기동전단_시뮬레이터\_internal\" -Force
   Copy-Item spec_db.py "dist\이지스_기동전단_시뮬레이터\_internal\" -Force
   ```

4-b. **UI·시각화 변경 시**: 빌드 후 커밋 전 exe 동작 확인 (스모크 실행).

5. **git push** (원격 joint-defense-sim)

빌드 후 git 커밋은 소스 파일만 한다. `dist/`, `build/` 폴더는 커밋하지 않는다.

---

## 개발 워크플로우

### 모델 및 에포트 선택 기준

모델 자동 전환은 불가능하므로, 전환이 필요할 때 Claude가 먼저 알리고 `/model` 명령어로 직접 변경한다.

| 상황 | 모델 | 코드리뷰 에포트 |
|------|------|----------------|
| 일반 패치·버그픽스·UI 변경 | Sonnet (기본) | medium |
| 새 물리 모델·엔진 클래스 추가 | Sonnet | medium |
| 복잡한 아키텍처 설계·교전 흐름 전면 변경 | Opus | high |
| 같은 유형 실수 2~3회 반복 패턴 감지 | Opus로 전환 제안 | — |
| numpy 전면 재설계 등 매우 높음 난이도 | Opus | high |

### 난이도별 작업 방식

| 난이도 | 방식 |
|--------|------|
| 낮음 | 설계 없이 바로 구현 |
| 중간 이상 | 설계 먼저 → 합의 후 구현 → plan 파일에 기록 |

### 중간 이상 설계 포함 항목

- 수정할 파일 목록
- 핵심 변경 내용 (함수명, 반환값 변경 등)
- 의존성 / 주의사항 (하위 호환 등)
- 필요 시 핵심 코드 스니펫

---

## 코드 규칙

### DB 구조 원칙

- `ENEMY_DB` (engine.py): 적군 위협. `normalize_enemy_db()` 호출 시 누락 필드 자동 보완.
- `FRIENDLY_DB` (engine.py): 아군 방어 무기. `pk_dist`는 Beta 분포 파라미터.
- `FRIENDLY_STRIKE_DB` (engine_v7.py): 아군 공격 무기 (해성·하푼·현무-3C 등).
- `SHIP_DB` / `FLEET_PRESETS` (engine.py): 아군 함정·편대 프리셋.
- `ENEMY_FLEET_PRESETS` (engine.py): 적군 편대 프리셋.
- `FRIENDLY_AIRCRAFT_DB` (engine.py): CAP 전투기·함재 헬기·해상초계기.
- `SPEC_DETAIL_DB` (spec_db.py): DB 탭 스펙시트 표시용 상세 설명.

> 각 DB의 정확한 항목 수는 코드에서 직접 확인한다.

### 신기능 추가 시 체크리스트

1. `ENEMY_DB` / `FRIENDLY_DB` 등 DB 수정 시 `normalize_enemy_db()` 확인
2. 새 클래스 추가 시 `_id_counter` 리셋 로직 필수 (`run_v7_simulation` 진입부)
3. 신기능은 `enable_xxx` 플래그로 ON/OFF 가능하게 만든다 (하위 호환 유지)
4. engine_v7.py 새 심볼은 launcher.py import 목록에 추가
5. spec_db.py에 없는 신규 DB 항목은 동시에 스펙 설명 추가. 기존 항목 수치 변경 시 해당 설명도 갱신.
6. `enable_xxx` 신규 추가 시 **3종 세트** 필수: launcher 체크박스 + cfg 빌드(`isChecked()`) + cfg 로드(`hasattr` 패턴)
7. 신규 `stats` 키 추가 시 **MC 3개 경로에 동시 추가**: `monte_carlo_v7` · `_mc_batch_worker` · `monte_carlo_lhs` (누락 시 MC 모드에서 해당 통계 완전 소실)
8. 신규 PyQt6 위젯 클래스 사용 시 `launcher.py` 상단 import 목록 확인 (누락 시 exe 실행 즉시 NameError로 창 소실)

### 하위 호환 원칙

- 전역 DB를 시뮬레이션 실행 중 직접 수정하지 않는다. 로컬 사본(`dict(enemy_info)`)을 만들어 사용한다.
- `run_v7_simulation()` 진입부에서 항상 `cfg = dict(cfg)` 처리. 시뮬 내부에서 cfg를 직접 수정하면 MC 반복 간 상태가 오염된다.
- `_mc_batch_worker` 반환 tuple 인덱스 변경 시 `monte_carlo_v7` / `monte_carlo_lhs` 수신부도 함께 수정한다.
- `enable_xxx` 플래그명은 한 번 정하면 변경하지 않는다. (저장된 시나리오 파일 호환)
- `FriendlyAircraftObj` 비활성화 시 `payload_remaining`과 `strike_payload_remaining`을 **모두** 0으로 설정한다. (`_aircraft_cap`과 `_aircraft_aas`가 각각 다른 필드를 체크하기 때문)

### 코드 작성 원칙

- 엔진 내 `self._log()` 호출은 반드시 `if not self._mc_mode:` 안에 작성한다. (MC 1000회 반복 시 과도한 출력 방지)
- 콤보박스는 항상 `NoScrollComboBox` 사용. `QComboBox` 직접 사용 금지. (스크롤 휠로 값이 의도치 않게 바뀌는 것을 방지)
- 틱 루프에서 여러 번 호출되는 메서드 내 `enemy_threats` 전체 순회는 틱 시작 시 캐싱해 사용한다. (`_active_ecm`, `_n_alive_threats` 패턴 참조)

### CLAUDE.md 유지보수 원칙

- engine_v7.py 주요 클래스·함수 테이블은 클래스명·함수명 추가/변경 시 즉시 갱신한다.
- 헤더·changelog 예시의 버전 번호(`vX.YY.ZZ`)는 형식 설명용이므로 업데이트하지 않는다. 실제 현재 버전은 `launcher.py` 헤더와 `APP_VERSION`에서 확인한다.

### engine.py 주요 유틸 함수 (v7에서 import해서 사용)

| 함수 | 역할 |
|------|------|
| `normalize_enemy_db()` | ENEMY_DB 누락 필드 자동 설정 (파일 로드 시 1회 실행) |
| `calculate_detect_range_by_rcs()` | RCS 기반 탐지거리 계산 |
| `generate_random_enemy_fleet()` | 랜덤 적군 편대 생성 |

### engine_v7.py 주요 클래스·함수

| 항목 | 역할 |
|------|------|
| `TimeStepEngine` | 메인 시뮬레이션 클래스 |
| `_friendly_defense()` | 아군 SAM/CIWS로 적 미사일·항공기 요격 |
| `_friendly_strike()` | 아군 함정/잠수함 → 적 수상함 공격 |
| `_enemy_defense()` | 적 수상함 SAM/CIWS로 아군 미사일 요격 |
| `_aircraft_asw()` | 함재 헬기·초계기 대잠 공격 |
| `_aircraft_cap()` | 아군 CAP 전투기 적 항공기 BVR 요격 |
| `_aircraft_aas()` | CAP 전투기 해성-II 등으로 적 수상함 공격 (항모 우선) |
| `_arm_radar_off_check()` | ARM 탐지 시 레이더 OFF 전술 |
| `monte_carlo_v7()` | 표준 MC 분석 |
| `monte_carlo_lhs()` | LHS 샘플링 기반 고속 MC |
| `_compile()` | 시뮬 결과 dict 반환 |
