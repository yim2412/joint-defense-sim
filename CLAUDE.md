# 합동 통합방어 시뮬레이터 — 프로젝트 규칙

## 프로젝트 개요

한국 해군 이지스 기동전단의 다층 방어 시뮬레이터. 대공·대함·대잠 위협에 대한 교전 시뮬레이션, 몬테카를로 분석, 요구조건(REQ) 판정, Excel/PNG 보고서 생성을 수행한다.

### 파일 구조

| 파일 | 역할 |
|------|------|
| `engine_core.py` | 핵심 DB (ENEMY_DB·FRIENDLY_DB·SHIP_DB 등), 물리모델, 탐지·교전 로직 |
| `engine_combat.py` | 시간 스텝 기반 양방향 교전 엔진. engine_core.py DB를 import해서 사용 |
| `engine_campaign.py` | 작전급 캠페인 엔진 (v18) — 며칠 전역을 1시간 틱으로 진행, 교전은 즉시예측(forecast_model)으로 해결. 전술 엔진(engine_combat) 무수정 호출. `CampaignEngine`·`run_campaign`·`monte_carlo_campaign` |
| `engine_airforce.py` | 공군 작전급 층 (v19) — 제공권 격자·CAP·SEAD·전략폭격·CAS. 캠페인이 조합 호출. `AirCampaign` |
| `engine_army.py` | 지상 작전급 층 (v20) — 연안 방공 포대(BMD 5계층 자산·재고 틱간 추적)·상륙작전(3단계 곱연산)·적 SEAD 도미노·지대지 화력(v21.2 `ARMY_FIRE_PRESETS`·`fire_rounds`). 캠페인이 조합 호출. `ArmyCampaign`·`CoastalSAMSite`·`AmphibiousForce` |
| `engine_joint.py` | 합동 화력 층 (v21) — 육해공이 공유 표적(v19.4 `EnemyBase`)을 협조 타격. 표적 소유권은 캠페인이 갖고 공군 층과 공유. 짝 3중(`enable_joint_fires`+`enable_strategic_strike`+`enable_air_campaign`) 전부 ON이어야 생성. 캠페인이 조합 호출. `JointFires`·`build_land_stock` |
| `app_main.py` | PyQt6 런처 — UI, 시뮬 워커, 결과 탭, DB 탭, 향후 계획 탭 등 전체 앱 |
| `app_utils.py` | 런처의 비-GUI 유틸 계층 (GPU·CPU 계측, 워커 풀, Job Object, 리소스 경로, 로그·SQLite). **PyQt6를 import하지 않는다** — app_main→app_utils 단방향 유지용. `_GLOBAL_POOL`은 재할당 전역이라 이름 import 금지, `app_utils._GLOBAL_POOL`로 참조 |
| `app_engine.py` | engine_*·db_specsheet import 계층(try/except 폴백, `_V7_OK`·`_SPEC_DB_OK`). **app_workers와 공유해 순환을 끊는 최하층** — 워커가 엔진 심볼을 쓰는데 import가 app_main에 있으면 app_workers→app_main 순환이 된다 |
| `app_workers.py` | 백그라운드 워커(`SimWorker`·`FleetRecommendWorker`·`ShowcaseCompareWorker`·`CounterfactualWorker`·`_SysDataWorker`). 의존은 app_engine·app_utils·PyQt6뿐. `_GLOBAL_POOL`은 `app_utils._GLOBAL_POOL`로 참조 |
| `ui_charts.py` | 차트 렌더·교전 분석 탭(`MplCanvas`·`ChartRenderWorker`·`ChartPageWidget`·`EngagementAnalysisTab`·`_render_engagement_*`·`_render_battle_timeline`·`_render_campaign_report`). `_render_*`는 `_audit_render_smoke`가 `getattr(app_main, ...)`로 꺼내므로 **app_main이 반드시 재노출 import**할 것 |
| `app_theme.py` | 색상 팔레트·`_wire_chk_color`·**`CHART_DPI`**. 모든 UI 모듈이 참조 → **여기서 앱 모듈 import 금지**(즉시 순환). ⚠ `CHART_DPI`는 main()이 화면 크기로 재할당하는 전역 — 읽는 쪽·쓰는 쪽 모두 `app_theme.CHART_DPI`로 **모듈 경유**(이름 import하면 150 고정, DPI 자동감지가 조용히 죽음) |
| `ui_widgets.py` | 재사용 위젯(`NoScrollComboBox`·`GaugeWidget`·`ConvergenceWidget`·`RateHistogramWidget`·`_TaskbarProgress`)+`STYLE_MAIN`. 의존은 PyQt6·numpy·`app_utils._res`·app_theme뿐 |
| `scenarios.py` | `SCENARIO_LIBRARY` — 원클릭 추천 시나리오 프리셋(순수 데이터, 의존 없음). UI 표시 문자열이므로 exe 용어 규칙 적용 |
| `db_specsheet.py` | DB 탭 스펙시트 패널용 상세 설명 (origin, categories, note) |
| `app_changelog.json` | 패치 이력 (배열, 버전 번호 순서) |
| `app_main.spec` | PyInstaller 빌드 스펙 |
| `_asset_make_bg.py` | 홈 배경 이미지 생성 스크립트 (src_kf21_source.jpg → home_bg.jpg). 빌드 제외, 수동 실행용 |
| `_changelog_export.py` | app_changelog.json → `변경이력/` 유형별 정리 문서 생성기. 빌드 제외, changelog 갱신 시 재실행 |

### 실행 방법

```powershell
# 런처 실행 (개발 중)
python app_main.py

# exe 빌드
python -m PyInstaller app_main.spec --noconfirm
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

`app_main.py` 최상단 헤더와 `APP_VERSION` 상수를 **패치 완료 시 수동으로 직접 수정**한다.

### 헤더 주석 규칙

`app_main.py` 최상단 헤더에 현재 버전과 최근 변경 내용을 기록한다.

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
대상: `app_changelog.json`(패치 내역 탭), `_PLANS`(향후 계획 탭).

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

함수명·클래스명 등 코드 명칭이 꼭 필요하면 **git 커밋 메시지·app_main.py 헤더 주석·개발 문서(로드맵_상세*.md)**에 적는다. 이들은 exe에 안 보이므로 제약 없음.

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
| 엔진 로직·새 클래스·교전 흐름 변경 | **회귀 검증 + 코드/로직 감사** | `python audit_verify_regression.py` (PASS 필수) + `/code-review medium` (난이도 높음↑이면 high) |
| DB 수치·물리 파라미터 변경 | **회귀 검증 + 현실성 수치 감사** | `python audit_verify_regression.py` + 공개 제원·교리와 대조 (수동 또는 Explore 에이전트) |
| UI·시각화·문서만 변경 | **회귀 확인** | 빌드 성공 + 스모크 실행만 (엔진 미변경 시 회귀 스크립트 생략 가능) |
| 아키텍처 전환(난이도 매우 높음) | **회귀 검증 + 코드 감사 + 로직 트레이스** | `python audit_verify_regression.py` + `/code-review high` + 핵심 경로 수동 추적 |
| **신기능(`추가`) 포함** | **용어 확인** | 새 군사용어가 생겼는지 changelog·_PLANS 검토 |

신기능이 없는 버그·수치·UI 변경은 용어 확인 생략. `추가` 항목이 하나라도 있을 때만 확인.

> **스모크 실행** 정의: exe 실행 → 기본 시나리오 단일 시뮬 1회 → 결과 탭 정상 표시 확인. **exe는 `CloseMainWindow()`로 정상 종료** — `Stop-Process -Force` 금지(시작 시 워커 풀 예열 중 강제종료하면 멀티프로세싱 자식이 WinError 87 에러창을 띄움. 코드 버그 아닌 강제종료 아티팩트).
>
> **스모크 실행 대체 금지**: exe에서 시뮬레이션 버튼을 실제로 클릭하는 데 실패하면, 엔진 직접 호출(`run_v7_simulation()`)로 우회하지 않는다. 엔진 직접 호출은 GUI 워커 경로(step_cb, 시그널 emit 등)를 거치지 않아 exe 전용 버그를 놓친다. **무인 감사에서는 GUI 자동화(pywinauto/UIA)로 버튼 클릭을 자동 수행**하고, 그 GUI 자동화마저 실패할 때만 **BLOCKED로 보고**한다(이때도 엔진 직접 호출 우회는 금지). 무인 모드가 아닌 일반 패치에서는 자동화 실패 시 사용자에게 직접 시뮬 1회 실행을 요청한다.

> **회귀 검증(`audit_verify_regression.py`) 정의**: 고정 8개 시나리오×고정 seed 결과를 `audit_regression_golden.json`(repo 저장)과 대조. **엔진 동작이 의도치 않게 바뀌면 FAIL** (C&D id 버그처럼 조용한 변화를 잡음). 사용: 검사 `python audit_verify_regression.py` / 의도된 변경 후 갱신 `python audit_verify_regression.py --update`. **엔진·DB·교전 로직을 고치면 변경 전 PASS 확인 → 변경 후 재실행**이 기본. FAIL이면 의도된 변경인지 판단(맞으면 `--update`, 아니면 버그). 결정론 의존(seed 고정)이라 신규 `random` 호출 추가는 정상 변경이어도 FAIL 가능 → 의도 확인 후 갱신.

감사에서 발견한 항목은 **그 자리에서 수정 후 커밋**한다(다음 일련번호 부여). 감사 결과는 커밋 메시지에 1줄 요약.

---

### 감사 3층 구조 (무게별 — 빈도 과다 방지)

감사는 **무게별 3층**으로 운영한다. 핵심 원칙: **싼 안전망(회귀·정적 스캔)은 자주, 비싼 절차(에이전트 spawn·MC·GUI 자동화)는 드물게.** 마이너 묶음을 닫을 때마다 9영역 풀 종합 감사를 붙이지 않는다 — 그건 비용 대비 과하고, 실제로 발견되는 건 대부분 정적 스캐너·회귀가 잡는 것들이다.

| 층 | 언제 | 무엇을 | 비용 |
|----|------|--------|------|
| **① 마이너 감사** | 마이너 버전마다 (위 '감사 정책' 표) | 회귀 검증 + 변경 유형 맞는 것(코드/수치) | 가벼움 |
| **② 경량 점검** | **마이너 묶음 완료 시** (재고 현실화 묶음 등 '✅완성' 선언) | `python audit_static_scan.py` + `python audit_verify_regression.py` + 빌드·스모크 **자동만**. 에이전트 spawn·MC·Explore 팬아웃 **생략** | 중간(자동) |
| **③ 종합 9영역** | **major 전환 직전 1회** OR 아키텍처 변경 OR 누적 위험 크다고 Claude 판단(사용자 승인) | 아래 9영역 풀 (code-review high·Explore 팬아웃·MC·GUI 스모크) | 무거움 |

> **마이너 묶음 완료 ≠ 종합 감사 트리거.** 묶음을 닫을 땐 ②경량 점검으로 충분하다. 무거운 ③종합 9영역은 major 블록을 통째로 닫을 때(예: v16→v17) 누적분을 한 번에 본다 — 종합 감사의 본질 가치(상호작용·하위호환을 통합 상태에서 점검)는 블록 끝 1회가 가장 효율적이다. 같은 major 안에서 종합 감사를 여러 번 돌리지 않는다.

---

### 종합 감사 (③층 — major 블록 완료 시 코드·데이터·exe 한 번에)

마이너 감사가 "변경 1건"을 보는 것과 달리, **종합 감사는 누적된 블록 전체를 통합 상태에서 한 번에 점검**한다(상호작용·하위호환·수치 안정성). 9개 영역을 점검하고 **사람이 읽는 감사 보고서 파일**을 남긴다.

#### 0) 무인 모드 (기본 — 사용자 단계별 동의 없이 자동 수행)

종합 감사는 **무인(autonomous)으로 수행**한다. 사용자가 감사를 승인(트리거)하면 그 승인이 **9영역 전체에 대한 포괄 동의**로 간주되어, 각 단계마다 다시 묻지 않는다 — 백그라운드 실행([[feedback-no-background-without-consent]]의 사전 동의는 감사 승인으로 충족), 빌드, 에이전트 spawn(`/code-review high`·Explore 팬아웃), 발견 항목 **그 자리 수정·커밋·푸시**까지 Claude가 끝까지 진행하고 **결과(감사보고서 + 발견·조치 요약)만 보고**한다.

- **⑤ exe 스모크는 GUI 자동화로 무인 처리**: pywinauto/UIA 등으로 exe를 띄워 시뮬 버튼을 실제 클릭→결과 탭 표시까지 자동 검증한다. **엔진 직접 호출(`run_v7_simulation`) 우회는 여전히 금지**(GUI 워커 경로 전용 버그를 놓침). GUI 자동화 자체가 실패하면 **그 ⑤영역만 BLOCKED로 보고**하고 나머지 8영역은 무인으로 끝까지 완료한다(전체 중단 금지).
- 무인 진행 중에도 [[feedback-verbose-background]]에 따라 **단계별로 투명하게 보고**한다(자동 진행 ≠ 침묵). 장시간 단계(code-review·빌드·전장 MC)는 약 1분 간격 박스 UI.
- **사용자 판단이 갈리는 발견**(예: 의도된 변경인지 버그인지 모호, 비가역 삭제)은 무인으로 강행하지 않고 보고서에 '판단 필요'로 남겨 마지막에 함께 제시한다.

#### 1) 트리거 — 아래 경우 (빌드·커밋 전 1회)

종합 9영역은 **드물게** 돈다(위 '감사 3층 구조' 참조). 마이너 묶음 완료는 ②경량 점검으로 처리하고, 종합 9영역은 아래일 때만:

1. **major 숫자 증가 직전**: 아키텍처 전환(예: v16→v17)으로 major가 바뀌기 전 — **주 트리거**. 그 major에서 누적된 모든 블록을 한 번에 본다.
2. **아키텍처 전환·대규모 교전 흐름 변경**: major가 안 바뀌어도 엔진 구조를 갈아엎는 큰 변경이 있을 때.
3. **Claude 추천 시**: 누적 변경량·상호작용 위험이 크다고 판단되면 Claude가 먼저 종합 감사를 제안 → **사용자 승인 후 수행**.

> 과거 '큰 기능 묶음 ✅완성마다 종합 감사' 트리거는 같은 major 안에서 9영역을 여러 번 돌게 만들어 과했다(v16에서 3회). 이제 **묶음 완료는 ②경량 점검**, 종합은 major 전환 위주.

#### 2) 9개 감사 영역 (각 영역 **PASS** 또는 **해당 없음**)

| # | 영역 | 무엇을 | 방법 (에이전트 적극 활용) |
|---|------|--------|------|
| ① | **코드·로직** | 블록 누적 diff의 상호작용·하위호환 버그(플래그 OFF 시 기존 결과 동일) + **신기능 체크리스트 8항목 재검증**(아래) + **전역 상태 오염**(전역 DB `ENEMY_DB`/`FRIENDLY_DB`/`SHIP_DB`를 `.copy()` 없이 참조 후 mutate / `cfg = dict(cfg)` 미복사) + **부모 무수정**(`BattleEngine` 상속이 `TimeStepEngine` 시그니처 변경 안 함·훅 기본인자 동작보존) + **cfg 키 오타**(`enable_xxx` 문자열 오타가 조용히 무시) + **UI 인덱스 정합**(탭·스택·색상 컬럼 밀림, `NoScrollComboBox` 준수) + `FriendlyAircraftObj` 비활성화 시 payload 양쪽 0 + **순회 필터 누락**(잘못된 객체가 잘못된 경로로 — 예: CAP기가 대잠 순회에 진입해 공대공 무장을 어뢰로 조회 KeyError, v18.01.16) | `/code-review high` + Grep 스캔 + **`_audit_deep_review.md` 4팬아웃 레시피**(에이전트 병렬 정독, 도구가 못 잡는 의미 로직) |
| ② | **DB·수치** | 바뀐 DB 값을 공개 제원·교리와 대조 + **DB 전수 현실성 스윕**(변경분뿐 아니라 전 항목을 공개 제원과 대조 — 속도/사거리가 ▸동급 무기와 정합하는지 ▸마하·kts 환산이 맞는지 ▸과대·과소 **이상치**(예: 동일 기체군이 다른 속도, 아음속 무기가 초음속으로 오편성, 비전투 함정에 대함미사일 탑재). 발견 시 회귀 골든 영향 확인 후 정정 — [[project-db-realism]]) + **재고·편성 규모 현실성**(제원=속도·사거리뿐 아니라 ▸아군 함정 VLS 셀 수·미사일 재고가 실제 탑재량과 정합하는지(재고 과다 시 비현실적 압도) ▸적 편대 규모가 실제 교리와 정합하는지 — **단일 소량 위협은 비현실, 실제 교리는 다축 대량 동시 포화(saturation)**. 정밀무기 1발 편성(ARM·HGV 등)이 실제 포화 규모와 어긋나는지 점검 — [[project-db-realism]]) + **`db_specsheet` 항목수 = DB 항목수**(신규 DB 누락 시 스펙 빔) + `normalize_enemy_db` 누락 필드 + **DB 키 일관**(편대명·적명이 preset/`battle_surrogate` 키와 일치) | **Explore 에이전트 팬아웃** (또는 수동) |
| ③ | **회귀** | 엔진 동작 무결성 + **결정론**(`sim_seed` 키 사용·신규 `random`/`numpy.random`이 RNG 순서 깨는지) + **골든 커버리지**(새 기능·새 `stats` 키가 8케이스·26지표에 실제 반영되는지 — 없으면 회귀 사각) | `python audit_verify_regression.py` 전체 PASS (FAIL이면 의도 확인 → 갱신 또는 수정) |
| ④ | **통합 MC + 성능** | 기준 시나리오 전체 회귀 MC의 수치 안정성 + **wall-time 회귀 가드**(단발 1회·전장 1회 실행시간 이전 블록 대비 급증 1.5배+면 원인 규명) | 기준값 메모리(`project-baseline-*`) 대조 + 시간 측정·기록 |
| ⑤ | **exe·빌드** | 전체 빌드 성공 + **번들 무결성**(`spec datas`·`hiddenimports` 완전성, 데이터 파일 포함) + 스모크 + **리소스 로드 절대경로**(pkl·npz 등 `sys._MEIPASS` 경유 — 상대경로는 exe서 조용히 폴백, `chk_resource_paths` 자동검사) + **MC 중단(abort) 후 워커 잔존·풀 정리** + **외부 의존**(Cesium CDN 끊겨도 graceful) + `_internal` 복사 누락 | 빌드 + **모드별 GUI 자동화 스모크**(무인, pywinauto/UIA; 단발=`_audit_gui_smoke.py` · 캠페인=`_audit_campaign_smoke.py` · **새 실행 모드/화면 추가 시 전용 스모크 신설**; 조작은 invoke/toggle 우선=게임 포그라운드에도 동작; 자동화 실패 시 그 영역만 BLOCKED — 엔진 직접 호출 우회는 금지 [[feedback-smoke-run]]) + 중단 1회 테스트 |
| ⑥ | **위생** | changelog·`_PLANS` 코드명/완료항목 잔류, **`_PLANS` 완료분 반영**(현재 작업한 항목뿐 아니라 **상위 '진행 중'·'보류' 메이저 항목**도 — 완료된 작업이 '다음/예정/보류 중'으로 잔류하는지. 예: 전장 엔진·self-play 완료 후 '보류' 라벨·'다음: self-play' stale), 헤더·`APP_VERSION`·changelog 정합·연속성, **죽은 코드(호출처 0)**, **불필요 파일 정리**(완료된 1회용 진단 프로브·검증 끝난 PoC 잔재(`poc_*`)·구현 완료 설계문서(`plan_*`)는 삭제 또는 `_archive/plans/`로 이동, **참조 0인 orphan 스크립트**, 단 `military_db`·`download_images`처럼 의도적 유지 파일은 제외) + **파일명 정합**(역할이 드러나는 이름인지·`v7` 같은 stale 명칭 잔존·README 파일구조 표가 실제 파일 전수 커버), **상수·임계값 교차 정합**(예: `MAX_SIM_TIME` vs `BATTLE_HORIZON_S`), **보안**(개인키 미커밋·`.gitignore` 커버리지: `dist`/`build`·모델 zip·로그·`_rl_*` 산출물), CLAUDE.md engine_combat 함수표 정합 | **Grep + `audit_static_scan.py`**(`chk_plans_stale`: changelog 구현된 minor의 _PLANS stale 미래형·'보류' 라벨 자동 검출) ([[feedback-plans-changelog-hygiene]]) |
| ⑦ | **하위호환** | 저장된 **구버전 시나리오 cfg**(과거 `enable_xxx` 누락 dict)로 로드·실행 시 정상 동작 | 구버전 cfg dict로 `run_v7_simulation`/`run_battle_simulation` 1회 호출 |
| ⑧ | **수치 안정성·단위** | **NaN/Inf 가드**(0 나눗셈·`log`/`sqrt` 음수·빈 리스트 평균) + **확률값 [0,1] clamp**(Pk·progress·win_rate) + **단위 혼동**(km↔m·ms↔s·USD raw↔`/1e6`) + Beta 분포 `pk_dist` 파라미터 유효성 | Grep(`/`·`np.log`·`sqrt`) + 경계값 수동 점검 |
| ⑨ | **리소스 누수** | **`frames` 누적 `if not _mc_mode` 가드**(MC 1000회 메모리 폭발) + **matplotlib figure close**(탭 재렌더 누수) + **`self._log` mc_mode 가드**(MC 과출력) + 결과 히스토리 상한(5개) + QWebEngine 정리 | Grep 스캔 + MC 장시간 1회 메모리 관찰 |

> 사람은 에이전트 결과를 **검토·승인**한다. 영역이 그 블록과 무관하면(예: UI만 바뀐 블록의 ②DB·③회귀) '해당 없음'으로 명시 후 생략 — 9영역 전부를 매번 풀로 도는 게 아니라, 블록 성격에 맞는 영역만 PASS시키고 나머지는 '해당 없음'으로 빠르게 처리한다.

**①의 '신기능 체크리스트 8항목 블록 재검증'** — 마이너마다 빠뜨린 게 누적되므로 블록 단위로 한 번 훑는다 (정본은 '신기능 추가 시 체크리스트'):
1. `enable_xxx` **3종 세트** 무결성 — 블록에서 추가된 모든 플래그가 체크박스 + cfg 빌드(`isChecked()`) + cfg 로드(`hasattr`)를 갖췄는지
2. 신규 `stats` 키가 **MC 3경로**(`monte_carlo_v7`·`_mc_batch_worker`·`monte_carlo_lhs`)에 모두 있는지
3. engine_combat 신규 심볼이 app_main import 목록에 있는지 + 신규 PyQt6 위젯 import 누락(→exe NameError 창 소실) 없는지
4. 새 클래스 `_id_counter` 리셋, `normalize_enemy_db()` 보완, db_specsheet 동기화(새 DB 항목·수치 변경)
5. 죽은 코드(④위생과 교차) — 블록에서 추가했으나 호출처 없는 함수

#### 3) 발견 항목 처리

그 자리에서 수정 후 커밋(다음 일련번호). 커밋 메시지에 1줄 요약. 수정 후 해당 영역 **재감사**.

#### 4) 산출물 — 감사 보고서 (`감사보고서.md` 텍스트 누적 + `감사보고서/` 폴더 PDF)

두 형태로 남긴다:
- **`감사보고서.md`** (repo 루트) — 모든 블록 감사를 **최신순 텍스트로 누적**(단일 파일, 메모장 열람용). 아래 형식.
- **블록별 PDF** — **감사를 할 때마다 새로 생성**해 `감사보고서/감사보고서_{BLOCK}.pdf`로 저장(블록당 1개 누적). 생성기 `_audit_make_pdf.py`의 `BLOCK` 상수와 본문을 그 블록에 맞게 갱신 후 `python _audit_make_pdf.py` 실행(reportlab + 맑은 고딕, 군 보고서 양식). 텍스트 .md가 정본이고 PDF는 그 블록 결과의 보기 좋은 사본이다.


블록마다 **최신이 위로 오도록** 섹션을 누적한다(단일 파일, 텍스트 에디터·메모장으로 바로 열람 가능). 각 섹션은:

```markdown
## [날짜] vXX 블록 종합 감사 — <블록명> (트리거: 1/2/3)
범위: vXX.YY.ZZ ~ vXX.YY.ZZ

| 영역 | 판정 | 발견 항목 | 조치 |
|------|------|-----------|------|
| ① 코드·로직 | PASS / 발견N | 신기능 체크리스트 8항목 포함 | vXX.YY.ZZ에서 수정 |
| ② DB·수치   | PASS/해당없음 | ... | ... |
| ③ 회귀      | PASS | — | — |
| ④ 통합 MC+성능 | PASS | 기준값 대조: 요격률 NN%±N (기준 NN%) · 단발 N.Ns/전장 N.Ns (이전 N.Ns) | — |
| ⑤ exe·빌드  | PASS | 번들 무결성 OK·스모크 OK·중단 후 워커 잔존 0 | — |
| ⑥ 위생      | PASS/발견N | 죽은 코드·상수정합·보안·문서 포함 | ... |
| ⑦ 하위호환  | PASS | 구버전 cfg 로드 OK | — |
| ⑧ 수치·단위 | PASS/발견N | NaN·clamp·단위 | ... |
| ⑨ 리소스 누수 | PASS | frames·figure·log 가드 OK | — |

종합 판정: 통과 / 미통과(재감사 필요)
```

#### 5) 통과 기준

**9영역 전부 PASS 또는 '해당 없음'**이어야 블록 종료를 선언한다. 미통과 영역이 있으면 수정·재감사 후 다시 판정. 통과 시 보고서 종합 판정에 '통과' 기록 + 커밋·푸시.

#### 6) 메타 회고 — 감사 자체를 개선 (매 종합 감사 끝에 1회)

종합 감사를 마치면 **감사 과정 자체의 약점**을 회고해 다음 감사가 더 촘촘해지게 만든다 (코드가 아니라 *감사 절차*를 점검하는 단계). 각 감사 끝에:

1. **약점 식별**: 이번에 ▸돌리지 못한/대체한 점검(예: 병합된 블록이라 `/code-review` 타깃 diff 부재) ▸헛돈 수동 추측(키 구조 오가정 등) ▸생략한 케이스(abort 클릭 등) ▸시간 과다 단계를 적는다.
2. **개선 귀속**: 약점마다 **어디로 굳힐지** 정한다 — 반복 정적 점검이면 `audit_static_scan.py`에 함수 추가, GUI 시나리오면 `_audit_gui_smoke.py`에 추가, 절차/판단 규칙이면 이 CLAUDE.md 또는 [[feedback-audit-self-improve]] 메모리에.
3. **즉시 반영**: 가능한 개선은 그 자리에서 도구·규칙에 반영하고 커밋. 다음 블록까지 미룰 건 [[patch-queue]]에 '감사 개선' 항목으로 남긴다.
4. **보고서에 기록**: 감사보고서 해당 섹션 끝에 `메타 회고:` 한 줄로 이번에 무엇을 개선했는지/다음 숙제가 무엇인지 남긴다.

> 핵심: 감사는 **고정 체크리스트가 아니라 매번 자라는 도구**다. 같은 약점을 두 번 겪지 않도록, 발견한 빈틈을 사람 기억이 아니라 `audit_static_scan.py`·`_audit_gui_smoke.py`·`_audit_campaign_smoke.py`·규칙·메모리에 박는다. 알려진 빈틈(상시 갱신): ▸병합 후 감사는 `/code-review`가 빈 diff → 누적 diff(`첫커밋^..HEAD`)를 에이전트에 직접 먹이거나 **마이너마다 병합 전 리뷰를 미리** 돌려 둔다(shift-left). ▸**헤드리스가 못 잡는 GUI/exe 전용 버그**(step_cb 시그널 타입·리소스 상대경로 폴백 등) → 새 실행 모드마다 전용 GUI 스모크를 만들어 매 감사에서 실제 실행(v17.01 캠페인에서 확립).

### 실험적 기능 → 정규 기능 승격 기준

새 기능은 도입 시 **실험적(experimental)** 상태로 시작해, 검증 게이트를 통과하면 **정규(regular)** 기능으로 승격한다. 메이저 단계를 기다리지 않는다 — 검증이 끝나는 그 패치(또는 직후 위생 패치)에서 승격 처리한다.

#### 1단계 — 실험적 도입 (기능 추가 시)

신기능은 항상 이 형태로 들어온다.

- `enable_xxx` 플래그 **3종 세트** 필수: app_main 체크박스 + cfg 빌드(`isChecked()`) + cfg 로드(`hasattr` 패턴). 플래그명은 한 번 정하면 변경 금지(저장된 시나리오 파일 호환).
- 기본값 **OFF** (하위 호환 — 기존 결과와 동일).
- UI에 `(실험적)` 레이블 표기: 체크박스 텍스트 `"기능명 (실험적)"` + 툴팁 끝줄 `"기본값 OFF — 기존 결과와 동일 (실험적 기능)"`.

> **⚠ '실험적·기본 OFF로 커밋'은 완성이 아니라 미완성 상태다 ([[project-dead-feature-prevention]]).**
> `enable_xxx` 신규 토글을 커밋하려면 **발현 증거 3종**을 함께 제시해야 한다(커밋 메시지·plan 파일에 기록). 이것은 v20.5에서 죽어 있던 기능들(레이더 침묵·EMCON·레이저·정찰 드론)이 **전부 같은 경로로 태어난** 문제 — 메커니즘 구현→단위 검증→OFF면 동일→회귀 PASS→실험적·OFF 커밋 — 를 막기 위한 것이다. 이 관문은 **"기존 걸 안 깨뜨린다"만 보장하고 "이 기능이 실제로 뭔가 한다"는 전혀 보장하지 않았다.**
>
> | 증거 | 답해야 할 질문 | 죽었던 반례 |
> |------|----------------|-------------|
> | **① 발현 델타** | 어떤 시나리오에서 ON/OFF 결과가 **얼마나 다른가**(구체 수치) | 레이더 침묵: bit-identical이었다 |
> | **② 짝 기능** | 값을 하려면 **무엇이 함께 켜져 있어야** 하는가 | 레이더 침묵은 **회피 기동**이 OFF면 죽는다(함대 정지→조준 좌표 이격 0) |
> | **③ 발현 무대** | 어떤 편성·거리·조건에서 **발동**하는가 | 레이저: 드론이 5km에 와야 하는데 함포가 23km서 다 잡는다 |
>
> **셋 중 하나라도 못 쓰면 그 기능은 완성된 게 아니다.** '메커니즘 구현 + 단위 검증'은 필요조건일 뿐 충분조건이 아니다. ON/OFF 델타가 bit-identical이면 **그 커밋에서 원인(무대 부재/짝 기능 OFF/게이트 버그)을 규명**하거나, 규명 불가면 **음성으로 정직하게 종결**한다 — 죽은 채 커밋하지 않는다.
> **커밋 게이트(`chk_effect_coverage`)가 pre-commit에서 이를 강제**한다: 효과 프로브(`audit_effect.py`) 없는 신규 `enable_*`는 커밋 자체가 막힌다. 기존 미커버 토글만 `EFFECT_DEBT` 유예 목록에 있고, 그 목록은 **줄어들 수만 있다**(새 토글 추가 금지).

#### 2단계 — 검증 게이트 (변경 유형에 맞는 감사를 통과해야 승격 가능)

위 '감사 정책' 표의 해당 유형 감사를 **모두** 통과해야 한다. 유형별 합격 기준:

| 기능 유형 | 승격 합격 기준 |
|-----------|----------------|
| **수치·물리 모델** (소나·침수·연료 등) | 회귀 PASS + **ON/OFF 기준값 측정**(MC) + **공개 제원·교리와 대조 일치**(예: 소나=Thorp 문헌, 침수=배수량 공개값). 기준값은 메모리에 `project-baseline-xxx`로 보존. |
| **전술 옵션** (PNG·동적기상·IFF 등) | 회귀 PASS + **ON/OFF 기준값 측정**으로 효과가 의도대로(역효과·버그 없음) 확인 + 코드 감사(`/code-review`). |
| **엔진 로직·아키텍처** (지속 전장 등) | 회귀 PASS + 코드 감사(high) + **다운스트림이 그 기능의 출력을 정상 소비**(결과·판정·MC·비용·편대추천이 해당 기능 기준으로 동작)할 것. |

검증 기록(기준값·감사 결과)이 없으면 승격 불가 — 정직하게 **미검증**으로 남긴다.

#### 3단계 — 정규 승격 처리 (게이트 통과 시 그 패치에서)

1. **UI `(실험적)` 레이블 제거**: 체크박스 텍스트 + 툴팁 끝줄에서 '실험적' 문구 삭제.
2. **기본값 결정** (성격에 따라):
   - **항상 존재하는 환경물리**(지형·덕팅·ISA·소나·침수 등): **기본 ON**으로 전환 ([[feedback-default-on-policy]]). 토글은 비교·디버그용으로 유지.
   - **선택적 전술 옵션**(PNG·동적기상·IFF·전장모드 등): **기본 OFF 유지**(시나리오 선택지). 레이블만 떼서 '정규 옵션'으로.
3. **헤더·changelog 정리**: 과거 버전 헤더의 '(실험적)' 문구는 이력이므로 건드리지 않되, 승격을 changelog 1건(`수정 ...을 정규 기능으로 승격`)으로 남긴다.
4. 회귀 PASS 재확인 + (기본값을 ON으로 바꿨다면) 골든 갱신 여부 판단.

> **현재 미정리 항목**(승격 점검 시 참고): PNG=검증 완료·레이블 stale(즉시 승격 가능), 지속 전장 모드=엔진 검증됐으나 다운스트림 컷오버(갈래 B) 완료가 승격 시점, 동적기상·IFF=기준값 미측정(검증부터).

### 패치 완료 시 필수 체크리스트 (매번 반드시 수행)

**어떤 코드를 수정하든 패치 완료 후 아래를 반드시 처리한다.**

0. **감사 수행** (위 '감사 정책' 표 — 변경 유형에 맞는 감사를 빌드 전에)

1. **app_main.py 헤더 버전 번호 갱신** + **`APP_VERSION` 상수 갱신** (현재 버전으로)

2. **app_changelog.json 갱신**: 새 항목을 배열 마지막에 추가
   ```json
   {
     "version": "vX.YY.ZZ",
     "date": "YYYY-MM-DD",
     "title": "변경 내용 제목",
     "changes": ["추가  ...", "수정  ...", "삭제  ..."]
   }
   ```
   `version` 필드는 변경 1건마다 `vX.YY.ZZ` 3단계 번호를 사용한다. 'patch' 표기 금지.

2-b. **변경이력 문서 재생성**: changelog를 갱신했으면 `python _changelog_export.py`를 실행해
   `변경이력/` 폴더(유형별 정리 + 전체 연표)를 최신화한다. (json만 바뀌어도 재실행 — 안 하면 stale.)

3. **향후 계획 탭 갱신** (`app_main.py` → `_build_plan_tab()` 내 `_PLANS`):
   - 구현 완료된 항목은 **즉시 삭제**한다.
   - 새 계획 생기면 추가한다.
   - **`_PLANS` 변경(추가·삭제 모두) 후에는 반드시 전체 빌드**한다. `_PLANS`는 `.py` 코드이므로 빌드 없이는 exe에 반영되지 않는다.

3-b. **README.md 최신화** (DB/기능/버전이 바뀌었으면 — GitHub 공개 문서):
   - **DB 항목수**(적군·함정·항공·편대 프리셋 등)가 바뀌면 README '주요 기능' 수치를 갱신한다(한·영 양쪽). → `audit_static_scan.py`의 `chk_readme_counts`가 실제 DB와 대조해 **자동 검출**하므로, 마이너 감사에서 정적 스캔을 돌리면 stale이 잡힌다.
   - **헤드라인 기능**(새 도메인·무기 계열)이 추가되면 README '주요 기능' 목록에 1줄 추가(한·영). 자잘한 seq 패치는 불필요 — 새 계열/도메인일 때만.
   - **현재 단계 버전**(`현재 단계: … (vXX.YY)`)은 major.minor가 오르면 갱신(한·영). 이것도 `chk_readme_counts`가 APP_VERSION과 대조해 자동 검출.

4. **dist 폴더 갱신 (빠뜨리지 말 것)**:

   | 변경 파일 | 처리 |
   |-----------|------|
   | `.py` 파일 변경 | **전체 빌드** `python -m PyInstaller app_main.spec --noconfirm` |
   | `app_changelog.json`만 변경 | `_internal` 폴더에 복사만 |
   | `db_specsheet.py`만 변경 | `_internal` 폴더에 복사만 |
   | `.py` + json 동시 변경 | **전체 빌드** 후 복사 불필요 (빌드 시 자동 포함) |

   ```powershell
   # .py 변경 시 — 전체 빌드 (★ 반드시 진척 표시기와 함께)
   python _build_progress.py <로그경로> --watch --build --interval 45

   # json/db_specsheet만 변경 시 — 복사만
   Copy-Item app_changelog.json "dist\이지스_기동전단_시뮬레이터\_internal\" -Force
   Copy-Item db_specsheet.py "dist\이지스_기동전단_시뮬레이터\_internal\" -Force
   ```

   > **★ 빌드 진행 보고 규칙 (`_build_progress.py` — 추측 금지)**
   >
   > 빌드는 **반드시 `_build_progress.py`로 감시**한다. 맨 PyInstaller 호출 금지.
   > 폴링할 때는 `python _build_progress.py <로그>`(재생 모드)를 실행해 **그 출력을 그대로**
   > 사용자에게 보여준다 — 경과·단계·판정을 **내가 지어내지 않는다**.
   >
   > **왜**: v18.05.11 빌드에서 나는 폴링 횟수로 시간을 추정해 "12분·평소의 2배"라고
   > **틀리게** 보고했다(실제 384초=6.4분). 진행바 퍼센트도 내가 만든 허구였다. 사용자는
   > 같은 박스가 반복되는 것만 보고 "멈춘 줄 알고 당황"했다. 원인은 두 가지다 —
   > ①**시간을 시계로 재지 않고 추측**했다 ②PyInstaller 로그는 **그래프 분석 구간(전체의
   > ~90%)에서 수 분간 정체**하는데, 그게 정상인지 이상인지 판단할 **기준선이 없었다**.
   >
   > **도구가 주는 것**: ▸로그 타임스탬프 기반 **실제 경과** ▸단계별 도달 시각·구간 소요
   > ▸**기준선(384초, 실측) 대비 판정** — 기준의 1.5배를 넘으면 🔴로 이상 표시
   > ▸훅 처리 개수(정상 107개). **정체 = 정상**임을 기준선이 증명하므로 불안한 추측이 필요 없다.
   >
   > **정체 구간에서 하지 말 것**: 죽었다고 단정하고 **빌드를 겹쳐 띄우기**(같은 dist에 두
   > 프로세스가 써서 산출물 신뢰 불가 — 실제로 한 번 겪었다). 생존은 `tasklist`로 확인한다.

4-b. **UI·시각화 변경 시**: 빌드 후 커밋 전 exe 동작 확인 (스모크 실행).

5. **git push** (원격 joint-defense-sim)

빌드 후 git 커밋은 소스 파일만 한다. `dist/`, `build/` 폴더는 커밋하지 않는다.

---

## 개발 워크플로우

### 세션 중단 대비 (완전 종료 후 재개 3층 방어)

세션이 의도치 않게 **완전히 닫혀도**(크래시·사용량 한도·창 닫힘) 새 세션이 이어가게 하는 3층. 핵심 원리: **새 세션은 대화 기억이 0 — 디스크에 쓴 것(git 커밋+워킹트리 파일+메모리 .md+plan/SESSION_LOG .md)만 살아남는다.**

| 층 | 무엇 | 도구/파일 |
|----|------|-----------|
| ① **진입점** | 새 세션 SessionStart 브리핑이 `git status`(미커밋)+`git log`+`SESSION_LOG.md`를 읽어 자동 복원. **미커밋 있으면 최우선 재개 지점**(워킹트리는 세션이 죽어도 디스크에 남음). | SessionStart 훅(`.claude/settings.local.json`) |
| ② **맥락 저장** | `SESSION_LOG.md`(루트)에 세션 매듭마다 최신 위로 **무엇을·왜·다음·미커밋 주의** 누적. git/plan이 담는 *결과*가 아니라 **판단 맥락**. 각 항목 `(HEAD: <해시>)`. | `SESSION_LOG.md` |
| ③ **stale 방어** | `audit_static_scan.chk_session_log_fresh`가 SESSION_LOG 최신 해시와 git HEAD 거리(커밋<10) 검사 → 저널 갱신 밀리면 경고. patch_queue 버전 정합(`chk_memory_freshness`)과 짝. | `audit_static_scan.py` |

**습관(맥락 손실 최소화)**: ▸`Edit`/`Write`는 즉시 디스크라 코드는 미커밋이어도 살아남음 — *왜/다음* 맥락만 자주 flush하면 손실 최소. ▸긴 작업은 **완결 단위마다 커밋·푸시**(원격에 있으면 무엇이든 안전). ▸세션 매듭·중요 결정·규명마다 **SESSION_LOG + patch_queue 갱신**([[feedback-memory-git-source-of-truth]]). 규명은 plan 파일에.

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

### 작업 추적 (다단계 작업은 TaskList 사용)

**3단계 이상·다트랙 작업은 착수 시 TaskList로 단계를 등록**하고 in_progress/completed로 갱신한다.
세션이 끊겨도 **미완 Task가 곧 재개 지점**이 되어 세션 중단 대비([[세션 중단 대비]])와 시너지.

- 착수 전: 트랙/단계를 `TaskCreate`로 등록(대트랙 수준, 과하게 잘게 쪼개지 말 것).
- 진행 중: 시작하는 Task는 `TaskUpdate status=in_progress`, 끝나면 `completed`.
- 완결 단위마다 커밋·푸시(원격에 있으면 세션이 죽어도 안전) + patch_queue·SESSION_LOG 갱신.
- 단발 1건·자명한 작업은 TaskList 없이 바로 구현(오버헤드만).

---

## 코드 규칙

### DB 구조 원칙

- `ENEMY_DB` (engine_core.py): 적군 위협. `normalize_enemy_db()` 호출 시 누락 필드 자동 보완.
- `FRIENDLY_DB` (engine_core.py): 아군 방어 무기. `pk_dist`는 Beta 분포 파라미터.
- `FRIENDLY_STRIKE_DB` (engine_combat.py): 아군 공격 무기 (해성·하푼·현무-3C 등).
- `SHIP_DB` / `FLEET_PRESETS` (engine_core.py): 아군 함정·편대 프리셋.
- `ENEMY_FLEET_PRESETS` (engine_core.py): 적군 편대 프리셋.
- `FRIENDLY_AIRCRAFT_DB` (engine_core.py): CAP 전투기·함재 헬기·해상초계기.
- `SPEC_DETAIL_DB` (db_specsheet.py): DB 탭 스펙시트 표시용 상세 설명.

> 각 DB의 정확한 항목 수는 코드에서 직접 확인한다.

### 신기능 추가 시 체크리스트

1. `ENEMY_DB` / `FRIENDLY_DB` 등 DB 수정 시 `normalize_enemy_db()` 확인
2. 새 클래스 추가 시 `_id_counter` 리셋 로직 필수 (`run_v7_simulation` 진입부)
3. 신기능은 `enable_xxx` 플래그로 ON/OFF 가능하게 만든다 (하위 호환 유지)
4. engine_combat.py 새 심볼은 app_main.py import 목록에 추가
5. db_specsheet.py에 없는 신규 DB 항목은 동시에 스펙 설명 추가. 기존 항목 수치 변경 시 해당 설명도 갱신.
6. `enable_xxx` 신규 추가 시 **3종 세트** 필수: app_main 체크박스 + cfg 빌드(`isChecked()`) + cfg 로드(`hasattr` 패턴)
7. 신규 `stats` 키 추가 시 **MC 3개 경로에 동시 추가**: `monte_carlo_v7` · `_mc_batch_worker` · `monte_carlo_lhs` (누락 시 MC 모드에서 해당 통계 완전 소실)
8. 신규 PyQt6 위젯 클래스 사용 시 `app_main.py` 상단 import 목록 확인 (누락 시 exe 실행 즉시 NameError로 창 소실)
9. **신규 `enable_xxx` 토글은 발현 증거 3종(발현 델타·짝 기능·발현 무대) 없이 커밋 금지** — 효과 프로브(`audit_effect.py`)를 함께 만든다(없으면 pre-commit `chk_effect_coverage`가 FAIL). 정본 [[project-dead-feature-prevention]] · '실험적 도입' 절 참조. **죽은 채 커밋된 기능이 v20.5의 최대 부채였다.**

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

- engine_combat.py 주요 클래스·함수 테이블은 클래스명·함수명 추가/변경 시 즉시 갱신한다.
- 헤더·changelog 예시의 버전 번호(`vX.YY.ZZ`)는 형식 설명용이므로 업데이트하지 않는다. 실제 현재 버전은 `app_main.py` 헤더와 `APP_VERSION`에서 확인한다.

### engine_core.py 주요 유틸 함수 (v7에서 import해서 사용)

| 함수 | 역할 |
|------|------|
| `normalize_enemy_db()` | ENEMY_DB 누락 필드 자동 설정 (파일 로드 시 1회 실행) |
| `calculate_detect_range_by_rcs()` | RCS 기반 탐지거리 계산 |
| `generate_random_enemy_fleet()` | 랜덤 적군 편대 생성 |

### engine_combat.py 주요 클래스·함수

| 항목 | 역할 |
|------|------|
| `TimeStepEngine` | 메인 시뮬레이션 클래스 |
| `_friendly_defense()` | 아군 SAM/CIWS로 적 미사일·항공기 요격 |
| `_friendly_strike()` | 아군 함정/잠수함 → 적 수상함 공격 |
| `_enemy_defense()` | 적 수상함 SAM/CIWS로 아군 미사일 요격 |
| `_aircraft_asw()` | 함재 헬기·초계기 대잠 공격 |
| `_aircraft_cap()` | 아군 CAP 전투기 적 항공기 BVR 요격 |
| `_aircraft_aas()` | CAP 전투기 해성-II 등으로 적 수상함 공격 (항모 우선) |
| `_aircraft_recon()` | 무인 정찰 드론 OTH 탐지 확장(`enable_recon_drone`) + 확률적 격추 |
| `_unmanned_picket_update()` | 무인 함정(USV·UUV) 전방 피켓 탐지 확장(`enable_unmanned_assets`) |
| `_arm_radar_off_check()` | ARM 탐지 시 레이더 OFF 전술 |
| `monte_carlo_v7()` | 표준 MC 분석 |
| `monte_carlo_lhs()` | LHS 샘플링 기반 고속 MC |
| `_compile()` | 시뮬 결과 dict 반환 |
