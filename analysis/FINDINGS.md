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
- 실행주체: 나 단독 — **판정 완료(2026-09-20)**: `_archive/data/` 로 이동.
  배선 불가(`engine_army.py:6` 이 *"전면 지상전은 범위 밖(설계 결정 plan_v20_army.md §8)"*
  이라 명시하고, 실제로 좌표를 안 쓰고 추상 구역 프리셋을 쓴다) · 삭제는 아깝다(공개 출처
  달린 실측 수집물). 저장소에 이미 `_archive/plans/` 관례가 있고 CLAUDE.md ⑥위생이
  *"완료 잔재는 삭제 또는 `_archive/` 로 이동"* 을 규정한다. **죽은 코드가 아니라
  범위 밖으로 밀려난 자산**이다
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

### F-004 · 축: 뼈대 · 상태: 오탐
- 위치: engine_combat.py:6747 `def _compile(self) -> dict:`
- 근거: [실측]
- 이력: [신규]
- 심각도: 중간
- 반증조건: 본문 대부분이 데이터 리터럴이면 복잡도는 낮다 — **그 전에 길이 측정 자체가
  틀렸다.** 아래 참조
- 재현: `python -c "import ast; ..."` (AST 실측)
- 수정비용: 소
- 회귀위험: 없음
- 실행주체: 나 단독
- 뿌리: 증상
- 요약: ~~`_compile()` 이 1,802줄~~ → **오탐. 실제 13줄(`BattleEngine`)·109줄(`TimeStepEngine`)**
- 근거본문:
  **왜 틀렸나** — 첫 계측이 메서드 끝을 *"다음 `    def` 가 나오는 줄"* 로 잡았는데,
  `BattleEngine._compile()`(L6747) 다음부터는 **모듈 수준 함수**(`run_battle_simulation`·
  `monte_carlo_v7` 등, 들여쓰기 0)가 이어진다. 그래서 그 1,789줄이 통째로 메서드 길이에
  합산됐다. 분기 143개·결과 키 215개도 같은 구간을 센 것이라 **전부 무효**다.
  ```
  AST 실측(end_lineno 기준):
    _compile  : 13줄(L6747 BattleEngine) · 109줄(L5636 TimeStepEngine)
    최장 메서드: _build_enemies 237 · __init__ 233 · _friendly_strike 230 ·
                 _friendly_defense 221 · build_czml 200 · _check_hits 179
  ```
  **교훈(지우지 않고 남기는 이유 — 규약 3.5)**: 라인수 계측을 정규식으로 하면
  *같은 들여쓰기의 다음 정의* 가정이 깨지는 순간 조용히 틀린다. **AST 를 쓸 것.**
  이 오탐은 대장뿐 아니라 **판 구성 결론까지 흔들었다**(*"2단계를 `_compile` 전용 판으로
  쪼갠다"* 의 근거였다) — 잘못된 측정 하나가 계획을 바꾼다.

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

### F-006 · 축: 뼈대 · 상태: 미처리
- 위치: analysis/00_PROTOCOL.md:1 `# 전면 분석 규약 (00_PROTOCOL)`
- 근거: [실측]
- 이력: [신규]
- 심각도: 중간
- 반증조건: 정적 스캔으로 짝을 뽑을 수 있으면 이 판단은 틀린다. 실측하니 엔진 5개 파일에서
  *"한 줄에 토글 2개 이상"* 은 **6건**뿐이고 그중 3건은 주석·테스트 케이스였다.
  실제 짝(레이더 침묵 ↔ 회피 기동)은 **한 줄에 같이 등장하지 않는다** → 반증 안 됨
- 재현: (없음) — 방법론 항목이라 프로브가 아니라 대체 절차로 닫는다(9.2 S/R 참조)
- 수정비용: 소(규약 문구) / 중(측정 절차 구현)
- 회귀위험: 골든 영향 없음
- 실행주체: 나 단독
- 뿌리: 증상
- 요약: 규약 2.1-7 *"기능 간 의존(짝) 지도"* 를 **정적 방법으로는 만들 수 없다** —
  짝은 구문이 아니라 **의미·물리 의존**이라 grep 에 안 걸린다
- 근거본문:
  ```
  엔진 5파일 · 한 줄에 enable_* 2개 이상 = 6건
    cec_jammed+cec_preassign(테스트 케이스) · campaign 플래그 나열(루프) ·
    helo/p3c/p8a(docstring) · cec+cec_preassign(폴백) · decoy+evasion(주석)
  ```
  반면 실제 짝은 *"레이더 침묵은 회피 기동이 OFF면 죽는다(함대 정지→조준 좌표 이격 0)"*
  처럼 **두 기능이 코드에서 만나지 않는데 물리적으로 얽힌** 경우다.
  **실행 가능한 대체 절차**(규약에 반영할 것):
  1. `audit_effect.py` 가 각 토글의 **단독 ON/OFF 델타**를 이미 잰다 → 델타 0 인 것만 추린다.
  2. 그 토글만 **다른 토글과 2×2**(둘 다 OFF / A만 / B만 / 둘 다)로 재측정한다.
     단독 0 인데 조합에서 델타가 나면 **그 둘이 짝**이다.
  3. 후보가 적어 비용이 작다 — 현재 `EFFECT_ALIVE` 18개는 단독 델타가 확증됐고,
     `EFFECT_DEAD` 는 `enable_anti_sam` **1개**뿐이다(체크박스는 v21.07.10에 제거,
     엔진 코드만 보존). 즉 **2×2 측정 대상은 사실상 1개**다.
  → 짝 지도는 *"만들 수 없다"* 가 아니라 **"효과 측정의 부산물로만 만들 수 있다"** 가 정답.

### F-007 · 축: 뼈대 · 상태: 미처리
- 위치: engine_combat.py:6426 `def _apply_ship_evasion(self):`
- 근거: [코드]
- 이력: [신규]
- 심각도: 중간
- 반증조건: 인자를 넘기는 호출부가 하나도 없으면 **현재는** 안전하다. 실측하니 호출부는
  `self._apply_ship_evasion()`(L2796, 무인자)과 자식 내부의 `super()._apply_ship_evasion(...)`
  둘뿐이라 **지금은 터지지 않는다** → 심각도를 `중간` 으로 낮춘다. 다만 계약 위반 자체는
  반증되지 않는다(부모의 두 파라미터를 외부에서 쓸 수 없게 됐다)
- 재현: (없음) — S형식으로 닫는다: `chk_subclass_signature` 를 신설하면 영구 검출된다
- 수정비용: 소
- 회귀위험: 골든 영향 없음(시그니처만 맞추고 동작은 유지 가능)
- 실행주체: 나 단독
- 뿌리: 증상
- 요약: `BattleEngine._apply_ship_evasion(self)` 가 부모
  `TimeStepEngine._apply_ship_evasion(self, evade_r_base=15_000, evade_speed_ms=...)` 의
  **파라미터를 없앴다** — `CLAUDE.md` ①영역이 점검 항목으로 명시한 *"부모 무수정"* 위반
- 근거본문:
  ```
  L2722  부모: def _apply_ship_evasion(self, evade_r_base: float = 15_000,
                                       evade_speed_ms: float = _SHIP_EVADE_SPEED_MS)
  L6426  자식: def _apply_ship_evasion(self):            ← 파라미터 소거
  L6437        super()._apply_ship_evasion(evade_r_base=22_000)
  L2796  호출: self._apply_ship_evasion()                ← 유일한 외부 호출, 무인자
  ```
  `BattleEngine` 인스턴스에 `evade_r_base=` 를 넘기면 **TypeError** 다. 전장 모드는
  자세(`_evasion_posture`)로 값을 정하겠다는 설계 의도가 있고 주석에도 적혀 있으므로
  **의도적 좁힘**으로 보이지만, 그렇다면 부모 시그니처를 유지한 채 인자를 무시하거나
  `**kwargs` 를 받는 편이 계약을 깨지 않는다.
  **이 항목이 중요한 이유**: `CLAUDE.md` 감사 ①이 *"부모 무수정(BattleEngine 상속이
  TimeStepEngine 시그니처 변경 안 함)"* 을 **점검 항목으로 적어 두었는데 실제로는 변경돼
  있다.** 즉 이 점검이 수동이라 안 돌았거나, 돌았는데 놓쳤다 — **F-003(도구가 없으면
  사람 기억에 의존)의 실증 사례**다.

### F-008 · 축: 모델타당성 · 상태: 미처리
- 위치: engine_combat.py:5674 `_n_tot = self.stats['total_threats'] + self.stats['suicide_threats']`
- 근거: [실측]
- 이력: [신규]
- 심각도: 높음
- 반증조건: 파도 스폰 플랫폼이 `total_threats` 에 안 들어가면 이중이 아니다.
  실측: 같은 편성에서 파도 없음 `total_threats=32`, stagger(전부 파도) `=56` —
  **차이 24 = 편성 객체 수(12+8+4)와 정확히 일치** → 플랫폼이 분모에 들어간다. 반증 안 됨
- 재현: analysis/probes/p008_denominator_double_count.py
- 수정비용: 중 (세 지표 정의를 함께 설계해야 한다)
- 회귀위험: **골든 영향 큼** — `neutralization_rate` 가 32지표에 있다
- 실행주체: 실측·승인 필요
- 뿌리: F-005 의 증상
- 요약: `neutralization_rate` 분모가 **파도 스폰된 자폭 플랫폼을 두 번 센다**
  (`total_threats` 에 한 번, `suicide_threats` 로 또 한 번)
- 근거본문:
  ```
  $ python analysis/probes/p008_denominator_double_count.py none
    total_threats 32 · suicide_threats 20 · neutralization_rate 0.6731 (= 35/52)
  $ python analysis/probes/p008_denominator_double_count.py stagger
    total_threats 56 · suicide_threats 32 · neutralization_rate 0.2841 (= 25/88)
  ```
  파도 없음일 때는 초기 편성 플랫폼이 `total_threats` 에 안 들어가 **분모 52가 정당**하다.
  stagger 로 같은 플랫폼이 파도가 되면 `total_threats` 에 들어가고(+24),
  `suicide_threats` 가 **또** 더해져 분모가 부푼다.
  → `is_suicide_platform` 의 docstring(L1259)이 *"두 곳이 갈리면 지표가 거짓말을 한다"* 고
  경고한 바로 그 일이, **술어가 아니라 분모 합성에서** 일어났다.
  세 정의(`total_threats`·`intercepted_threats`·`suicide_*`)를 **함께** 고쳐야 한다(짝).

### F-009 · 축: 모델타당성 · 상태: 미처리
- 위치: engine_combat.py:2038 `fleet_cfg = new_fleet if new_fleet else fleet_cfg[:1]`
- 근거: [실측]
- 이력: [신규]
- 심각도: 높음
- 반증조건: 즉시 스폰된 첫 항목이 `_pending_threats` 에서 제거되면 중복이 아니다.
  실측: 코드에 제거가 없고, 실행 결과 자폭 USV 가 **12 → 24** 로 정확히 두 배가 됐다 → 반증 안 됨
- 재현: analysis/probes/p008_denominator_double_count.py stagger (이름별 집계 출력)
- 수정비용: 소 (한 줄 — 즉시 스폰한 spec 을 pending 에서 빼면 된다)
- 회귀위험: 골든에 stagger 케이스가 있으면 영향. 없으면 **회귀 사각**이라는 뜻이라 그것도 발견
- 실행주체: 나 단독
- 뿌리: 독립
- 요약: `ai_tactic='stagger'`(UI **"시차 공격"**)에서 **모든 위협이 저속이면 첫 편성 항목이
  중복 스폰**된다 — 즉시 1회 + 파도 1회
- 근거본문:
  ```
  L2027~2036  모든 spec 이 느리면 new_fleet 이 비고, 전부 _pending_threats 로 들어간다
  L2038       fleet_cfg = new_fleet if new_fleet else fleet_cfg[:1]
              ↑ 첫 항목을 즉시 스폰하지만 **pending 에서 빼지 않는다**

  실측(항만 침투 복합, 전부 저속: USV 14 · 022형 18.5 · 드론 28 m/s):
    파도 없음 : {'자폭 USV': 12, '022형': 4, '연안 자폭 드론': 8}  = 24
    stagger  : {'자폭 USV': 24, '022형': 4, '연안 자폭 드론': 8}  = 36
  ```
  적 편대가 **편성표보다 커진다**(첫 항목 수만큼). "시차 공격"은 도착 시점을 흩는
  전술인데 **전력을 늘려 버린다** — 전술 비교·편대 추천이 그만큼 왜곡된다.
  UI 정규 옵션이다(`mixin_configpanel.py:1459` `'시차 공격': 'stagger'`).

### F-010 · 축: 검증체계 · 상태: 미처리
- 위치: audit_static_scan.py:574 `KNOWN = {'ashore_sm3_fired', 'thaad_fired', 'usa_cost', 'usa_shots',`
- 근거: [실측]
- 이력: [신규]
- 심각도: 중간
- 반증조건: 화이트리스트가 *"한 번 등재하면 유지"* 를 의도했다면 낡은 게 아니다. 그러나
  같은 파일의 `EFFECT_DEBT` 는 **"줄기만 한다"** 를 명문화했고, 이 검사의 docstring 도
  *"새로 항상-동일 지표가 생기면 FAIL 로 골든 케이스 추가를 유도"* 라며 **커버리지를 늘리는
  방향**을 목적으로 밝힌다 → 줄어야 하는 목록이 맞다. 반증 안 됨
- 재현: (없음) — S형식으로 닫는다: KNOWN 항목이 실제로 상수인지 검사에 추가
- 수정비용: 소
- 회귀위험: 골든 영향 없음(도구)
- 실행주체: 나 단독
- 뿌리: F-003 과 같은 부류(안전망이 낡는 것을 아무도 안 본다)
- 요약: `chk_golden_coverage` 의 `KNOWN` 사각 화이트리스트 6개 중 **2개가 이미 변별되는데도
  그대로 남아 있다** — 그 2개가 다시 상수로 퇴행해도 이제 안 잡힌다
- 근거본문:
  ```
  KNOWN 6개의 골든 내 고유값 수:
    ashore_sm3_fired   4  **변별됨 → 등재 불필요**
    thaad_fired        2  **변별됨 → 등재 불필요**
    iff_failures       1  상수(등재 정당)
    iff_fratricide     1  상수(등재 정당)
    usa_cost           1  상수(등재 정당)
    usa_shots          1  상수(등재 정당)
  ```
  **화이트리스트는 면제 목록이라 낡으면 조용히 감시가 빈다.** `EFFECT_DEBT` 에는
  *"줄기만 한다 · 새 토글 추가 금지"* 규율이 붙어 있는데 `KNOWN` 에는 없다.
  → **고칠 것 둘**: ① 변별되는 2개를 목록에서 제거 ② **KNOWN 항목이 실제로 상수인지
  검증하는 검사를 추가**(변별되면 FAIL → 목록에서 빼도록 강제). 그래야 목록이 자동으로 줄어든다.

  **부수 확인**: 남은 4개는 정당한 사각이고, 그중 IFF 둘은
  [[project-experimental-promotion]] 의 *"IFF 는 CAP 교전 0이라 미검증 보류"* 를
  **골든 데이터가 독립적으로 뒷받침**한다(30케이스 전부 0).

---

## 낮음 집계 (개별 등재하지 않음 — 규약 3.1)

**L-1. 문서의 stale 수치 3곳** `[실측]` — 전부 "도구 출력이 정본, 문서는 손으로 적음"에서 온다.

| 위치 | 적힌 값 | 실제 |
|------|---------|------|
| `CLAUDE.md:200` | 고정 **8개 시나리오** | **42케이스** (골든 실행 출력) |
| `CLAUDE.md:248` | **8케이스·26지표** | **42케이스·32지표** |
| `CLAUDE.md:528` | 회귀 **38×29** | **42×32** |
| `audit_dead_toggle.py:7` | EFFECT_DEBT 유예 **현재 43개** | **0개** (`EFFECT_DEBT = set()` — 완전 청산) |
| `BLIND_SPOTS.md` 1번 | pairwise **43개→903쌍** | **51개→1,275쌍** (이 판에서 실행한 출력) |

`chk_readme_counts` 가 README의 DB 수치·단계 버전은 APP_VERSION·실제 DB와 대조하는데,
**`CLAUDE.md` 안의 수치는 아무도 대조하지 않는다**(F-001과 같은 뿌리 — CLAUDE.md에는
검사가 없다). B단계에서 F-001을 고칠 때 같은 묶음으로 처리하는 것이 자연스럽다.

> 부수 관찰: `audit_dead_toggle.py` 는 *"유예 목록 43개를 전수로 돌려 상환 여부를 판정"*
> 하는 도구인데 유예 목록이 0개다. 도구가 죽었다는 뜻은 아니다(EFFECT_ALIVE 재확증에 쓰인다).
> 다만 **목적 문장이 현재 상태와 안 맞는다** — 다음에 이 도구를 볼 사람이 오해한다.

**L-2. `db_*` 실측 데이터 모듈의 미배선 심볼 13개** `[실측]`

| 모듈 | 완전 미사용 |
|------|-------------|
| `db_ocean_acoustic.py` | `mackenzie_sound_speed` · `get_thermocline_top` · `month_to_season_key` / `OCEAN_TEMP_SALINITY_DB` · `OCEAN_SVP_PRECOMPUTED` · `SOFAR_CHANNEL` |
| `db_terrain.py` | `get_max_submarine_depth` · `thermocline_viable` · `get_radar_shadow_angle` |
| `db_ocean_environment.py` | `TIDAL_DATA` · `EOIR_DEGRADATION` · `UNDERWATER_ACOUSTICS` |
| `db_ground_threat.py` | `get_base_coords` (모듈 전체가 미사용 — **F-002**) |

**함수 18개 중 7개 · 상수 29개 중 6개**가 어디서도 안 쓰인다. [[feedback-real-data]] 로
*"추정값 대신 실측값을 코드에 내장"* 한 데이터인데 **절반 가까이 배선되지 않았다.**
F-002(모듈 통째)와 같은 부류이고, 4단계(부채)에서 *배선할 것 / 지울 것*을 가른다.

> **방법 메모(중요)**: 첫 스캔은 `호출처 0` 후보를 **100건** 냈는데 표본 4건을 확인하니
> `_build_home_page`(리스트에 콜백으로 등록) · `_pool_map`(`map_fn=` 인자로 전달) 처럼
> **호출 괄호가 없는 참조**를 놓친 거짓 양성이었다. 파일 **내부 호출**도 미사용으로
> 오판했다(`thorp_absorption` 은 `sonar_detection_range` 가 부른다).
> 걸러내니 13건. 규약 2.4-2 *"grep 히트 수만 세지 않는다 — 각 히트를 읽어 참/거짓 판정"*
> 이 실제로 **87건의 거짓 양성**을 막았다.
