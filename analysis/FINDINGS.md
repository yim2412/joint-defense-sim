# 발견 대장 (FINDINGS) — 정본

> 규약: `analysis/00_PROTOCOL.md` · 항목 형식은 3.2절 고정(검사기가 파싱한다).
> **기준 커밋**: `daa7ce8` (2026-09-20) · 인용한 파일:라인은 이 시점 기준.
> 발견은 판 도중 **즉시** 여기 flush 한다(1.7).

---

### F-001 · 축: 위생 · 상태: 미처리
- 위치: CLAUDE.md:18 `| 파일 | 역할 |`
- 근거: [실측]
- 이력: [신규]
- 심각도: 중간
- 반증조건: 표가 "주요 파일만" 싣겠다고 선언했다면 누락이 아니다. 실제로는 `CLAUDE.md`
  자신이 *"파일 구조 표 (파일 → 역할). 어디를 고쳐야 하는지가 여기서 나온다"* 를
  필수 항목으로 규정하고 *"안 고칠 거면 애초에 적지 않는다"* 고 적었다 → 반증 안 됨
- 재현: 아래 근거본문의 명령 (대조 스크립트)
- 수정비용: 중
- 회귀위험: 골든 영향 없음(문서)
- 실행주체: 나 단독
- 뿌리: F-002 의 뿌리(표에 없으니 죽은 모듈이 있어도 안 보인다)
- 요약: `CLAUDE.md` 파일 구조 표가 루트 `.py` 70개 중 30개만 등재 — 40개 누락(57%)
- 근거본문:
  README는 `chk_readme_coverage` 가 전수 커버를 강제하는데 **`CLAUDE.md` 표에는 검사가
  없다.** 그래서 한쪽만 자라고 다른 쪽은 v12 시절 30개에서 멈췄다.
  누락분은 도구뿐이 아니다 — **엔진·워커가 실제로 import 하는 런타임 모듈**이 들어 있다:
  `db_terrain`(engine_combat) · `db_ocean_acoustic`/`db_ocean_environment` ·
  `forecast_features`(engine_campaign) · `ai_policy_infer`(app_workers).
  ```
  $ python - <<'PY'   # git ls-files 의 루트 .py 와 CLAUDE.md 표 대조
  루트 .py 실제: 70 · CLAUDE.md 표 등재: 30
  표에 없는 실제 파일 (40): _ai_export_policy.py … db_terrain.py, forecast_features.py,
    ai_policy_infer.py, db_ocean_acoustic.py, db_ocean_environment.py, db_ground_threat.py …
  표에는 있는데 없는 파일 (0)
  PY
  ```
  **B단계 후보**: S형식 — `chk_claude_md_coverage` 를 `audit_static_scan.py` 에 신설하면
  `chk_readme_coverage` 와 같은 방식으로 영구 봉인된다.

### F-002 · 축: 부채 · 상태: 미처리
- 위치: db_ground_threat.py:2 `db_ground_threat.py — 한반도 군사 배치 데이터베이스`
- 근거: [실측]
- 이력: [신규]
- 심각도: 중간
- 반증조건: 동적 로딩(`importlib`·`getattr`)으로 쓰이면 죽은 게 아니다. 확인 결과
  이 저장소의 `importlib` 사용처는 `audit_static_scan.py` 의 `engine_core`·`engine_combat`
  둘뿐이라 반증되지 않는다
- 재현: 아래 근거본문의 grep
- 수정비용: 소(삭제) / 대(배선)
- 회귀위험: 골든 영향 없음(아무도 안 쓰므로) — 그 사실 자체가 발견의 내용이다
- 실행주체: **사용자 결정 필요** (삭제할 것인가, 육군 층에 배선할 것인가)
- 뿌리: 증상
- 요약: `db_ground_threat.py`(415줄, 한반도 군사 배치 DB)를 **어디서도 import 하지 않는다**
- 근거본문:
  ```
  $ grep -rn "db_ground_threat\|GROUND_THREAT" --include=*.py . | grep -v "^./dist/" \
      | grep -v "^./db_ground_threat.py"
  (출력 없음)
  ```
  공개 출처(GlobalSecurity·CSIS·FAS·RAND RRA619-1)를 달아 2026-06-01에 수집한
  **실측 데이터**라 그냥 지우기 아깝다. v20 지상 작전급(`engine_army`)을 위해 만들어
  두고 배선하지 않은 것으로 보인다 — `engine_army` 는 자체 프리셋을 쓴다.
  → 4.5(도메인 판단은 내 몫이 아니다)에 따라 **결정 요청 목록**으로 올린다.

### F-003 · 축: 검증체계 · 상태: 미처리
- 위치: BLIND_SPOTS.md:1 `# 감사 사각지대 레지스트리 (BLIND_SPOTS)`
- 근거: [실측]
- 이력: [신규]
- 심각도: 중간
- 반증조건: 수동 도구가 종합 감사(major 전환)마다 **실제로 돌았다는 기록**이 있으면
  반증된다. 감사보고서에 `audit_pairwise`·`audit_fuzz` 실행 출력이 붙어 있는지 확인 필요
  → 이 판에서는 미확인. 다만 "돌았다"가 확인돼도 **major 당 1회**라는 사실은 남는다
- 재현: 아래 근거본문의 추출 스크립트
- 수정비용: 소(훅 배선) ~ 중(무거운 것은 별도 주기)
- 회귀위험: 골든 영향 없음
- 실행주체: 나 단독
- 뿌리: 증상
- 요약: 감사 도구 20개 중 **훅이 자동 실행하는 것은 8개** — "메웠다"고 선언된 사각 일부가
  사람이 기억해야 도는 수동 도구에 걸려 있다
- 근거본문:
  ```
  훅 자동 8개: audit_static_scan, check_protocol, audit_verify_regression,
               audit_property, audit_effect, _audit_roundtrip, _audit_ui_shot, _audit_render_smoke
  수동 13개  : _audit_campaign_smoke, _audit_compat, _audit_gui_smoke, _audit_load_guard,
               _audit_make_pdf, _audit_mc_stability, _audit_scenario_smoke, _audit_smoke_util,
               audit_db_consistency, audit_dead_toggle, audit_fuzz, audit_pairwise, audit_perf
  ```
  `BLIND_SPOTS.md` 는 **pairwise 조합**(열린 사각 1번)과 **수치 키 극단값**(7번)을
  `audit_pairwise.py`·`audit_fuzz.py` 로 "해소"했다고 적었는데, 둘 다 수동이다.
  종합 감사는 CLAUDE.md 감사 3층 정책상 **major 전환 때만** 도므로 실질 **major 당 1회**다.
  → **"도구가 있다"와 "돌고 있다"는 다르다.** 레지스트리가 낙관적으로 거짓말을 한다.
  **B단계 후보**: S형식 — 훅 배선(가벼운 것) + `BLIND_SPOTS.md` 에 *실행 주기* 컬럼 추가,
  또는 `chk_` 검사로 "해소 선언된 항목의 도구가 훅에 있는가" 대조.

### F-004 · 축: 뼈대 · 상태: 미처리
- 위치: engine_combat.py:6747 `def _compile(self) -> dict:`
- 근거: [실측]
- 이력: [신규]
- 심각도: 중간
- 반증조건: 본문 대부분이 데이터 리터럴·포맷 문자열이면 길이만 길 뿐 복잡도는 낮다.
  실측하니 **if/elif 81 · for/while 62 · 결과 키 215개**로 분기 로직이다 → 반증 안 됨
- 재현: 아래 근거본문의 계수 스크립트
- 수정비용: 대
- 회귀위험: **골든 영향 큼** — 결과 dict 를 만드는 함수라 32지표 전부가 여기서 나온다
- 실행주체: 나 단독(분할 설계는 사용자 확인 필요)
- 뿌리: **지표 정의 문제(v22 1순위·자폭 집계)가 전부 이 함수 안에 있다**
- 요약: `_compile()` 한 메서드가 **1,802줄**(engine_combat 의 20%) — 결과 지표 32종의 정의가
  분기 143개와 뒤섞여 한 함수에 모여 있다
- 근거본문:
  ```
  engine_combat.py 8,899줄 · 클래스 13 · 메서드 238
  최장 메서드:  _compile 1802줄 / _dome 263 / _build_enemies 238 / __init__ 236
  _compile 내부:  if·elif 81 · for·while 62 · try 4 · 결과 키 대입 215 · 주석/빈줄 334
  ```
  2단계(모델 타당성) **D. 지표·집계 정의**의 무대가 정확히 이 함수다.
  `total_threats` / `intercepted_threats` / `enemy_ships_destroyed` 의 비대칭(`be4e8b9` 로
  되돌린 그 문제)도, 항모 함재기 무한 생산으로 분모가 통제 안 되는 v22 1순위도
  모두 여기서 결정된다. **2단계 판을 짤 때 이 함수 하나에 판 하나를 배정해야 한다.**

### F-005 · 축: 모델타당성 · 상태: 미처리
- 위치: engine_combat.py:2306 `self.stats['total_threats'] += 1`
- 근거: [코드]
- 이력: [기존] (같은 뿌리를 `be4e8b9` 가 한 번 건드렸다가 되돌림 — 그때는 초기 편성 쪽만 봤다)
- 심각도: 중간
- 반증조건: 파도 스폰 플랫폼이 `intercepted_threats` 에도 집계되면 대칭이라 문제없다.
  실측하니 L5120 주석이 *"MissileObj만 intercepted_threats에 집계 (항공기 플랫폼 격추는
  enemy_ships_destroyed로)"* 라고 명시 → 반증 안 됨. 또는 파도 스폰이 미사일만 만든다면
  무해하나, L2301 `else:` 가지가 `_new_threat()` 으로 **플랫폼을 만든다** → 반증 안 됨
- 재현: (없음) — 2단계에서 프로브화 예정
- 수정비용: 중
- 회귀위험: **골든 영향 큼** (요격률이 32지표에 들어 있다)
- 실행주체: 실측·승인 필요
- 뿌리: F-004 의 증상 · [[project-fleet-metric-flaw]] 와 같은 축
- 요약: `total_threats`(요격률 분모)가 **스폰 경로에 따라 다르게 센다** — 초기 편성은
  미사일만, 파도 스폰은 **플랫폼도** 센다. 분자는 어느 쪽이든 미사일만 센다
- 근거본문:
  ```
  L2172  초기 편성:  if (미사일) → missiles.append(m); total_threats += 1
         L2176 else: et = _new_threat(...)            ← 플랫폼은 분모에 안 들어간다
  L2301  파도 스폰:  else: et = _new_threat(...); enemy_threats.append(et)
  L2306              self.stats['total_threats'] += 1 ← if/else **밖**이라 플랫폼도 센다
  L5120  분자:       "MissileObj만 intercepted_threats에 집계
                      (항공기 플랫폼 격추는 enemy_ships_destroyed로)"
  ```
  결과: **같은 항공기가 초기 편성으로 오면 분모에 없고, 파도로 오면 분모에 있다.**
  파도로 온 쪽은 격추해도 분자에 안 잡히므로 *"때리는데 분모엔 있고 막아도 분자엔 없는"*
  위협이 된다 — `be4e8b9` 가 *"한쪽만 고치는 게 안 고치는 것보다 나쁘다"* 며 되돌린
  바로 그 상태가, **파도 스폰 경로에는 이미 존재한다.**
  → 2.2 D(지표·집계 정의)의 1순위 대상. `total_threats`·`intercepted_threats`·
  `enemy_ships_destroyed` 세 정의를 **함께** 설계해야 한다(짝).

---

## 낮음 집계 (개별 등재하지 않음 — 규약 3.1)

**L-1. 문서의 stale 수치 3곳** `[실측]` — 전부 "도구 출력이 정본, 문서는 손으로 적음"에서 온다.

| 위치 | 적힌 값 | 실제 |
|------|---------|------|
| `CLAUDE.md:200` | 고정 **8개 시나리오** | **42케이스** (골든 실행 출력) |
| `CLAUDE.md:248` | **8케이스·26지표** | **42케이스·32지표** |
| `CLAUDE.md:528` | 회귀 **38×29** | **42×32** |
| `audit_dead_toggle.py:7` | EFFECT_DEBT 유예 **현재 43개** | **0개** (`EFFECT_DEBT = set()` — 완전 청산) |

`chk_readme_counts` 가 README의 DB 수치·단계 버전은 APP_VERSION·실제 DB와 대조하는데,
**`CLAUDE.md` 안의 수치는 아무도 대조하지 않는다**(F-001과 같은 뿌리 — CLAUDE.md에는
검사가 없다). B단계에서 F-001을 고칠 때 같은 묶음으로 처리하는 것이 자연스럽다.

> 부수 관찰: `audit_dead_toggle.py` 는 *"유예 목록 43개를 전수로 돌려 상환 여부를 판정"*
> 하는 도구인데 유예 목록이 0개다. 도구가 죽었다는 뜻은 아니다(EFFECT_ALIVE 재확증에 쓰인다).
> 다만 **목적 문장이 현재 상태와 안 맞는다** — 다음에 이 도구를 볼 사람이 오해한다.
