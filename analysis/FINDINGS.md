# 발견 대장 (FINDINGS) — 정본

> 규약: `analysis/00_PROTOCOL.md` · 항목 형식은 3.2절 고정(검사기가 파싱한다).
> **기준 커밋**: `daa7ce8` (2026-09-20) · 인용한 파일:라인은 이 시점 기준.
> 발견은 판 도중 **즉시** 여기 flush 한다(1.7).

---

> **정렬 기준**: 5단계 종합(`00_SUMMARY.md` 2절)의 우선순위 —
> 의존 → 묶음 → 심각도 → 회귀위험. **대장 순서가 곧 작업 순서다.**
> (오탐·기각은 맨 뒤. 지우지 않는다 — 규약 3.5·3.6)

### F-009 · 축: 모델타당성 · 상태: 수정됨
- 위치: engine_combat.py:2041 `if new_fleet:`  (F-009 수정 후. 원래 `fleet_cfg = new_fleet if new_fleet else fleet_cfg[:1]` 한 줄이었다)
- 근거: [실측]
- 이력: [신규]
- 심각도: 높음
- 반증조건: 즉시 스폰된 첫 항목이 `_pending_threats` 에서 제거되면 중복이 아니다.
  실측: 코드에 제거가 없고, 실행 결과 자폭 USV 가 **12 → 24** 로 정확히 두 배가 됐다 → 반증 안 됨
- 재현: analysis/probes/p009_stagger_duplicate_spawn.py  ← **판정 P** (착수 시 FAIL 확인)
- 수정비용: 소 (한 줄 — 즉시 스폰한 spec 을 pending 에서 빼면 된다)
- 회귀위험: 골든에 stagger 케이스가 있으면 영향. 없으면 **회귀 사각**이라는 뜻이라 그것도 발견
- 실행주체: 나 단독
- 대상: engine_combat.py, app_main.py, app_changelog.json
  (선언 확대 2026-09-20: exe 체감 변화가 있어 9.8 대로 버전 번호를 부여했고,
   `CLAUDE.md` 필수 체크리스트가 `APP_VERSION`·헤더·changelog 갱신을 요구한다.
   검사기가 *'선언에 없는 파일이 바뀌었다'* 로 잡아 **조용한 확대를 막았다** —
   규약 9.3 이 의도한 대로 이력에 남긴다. 3파일로 상한 내)
- 짝: 없음(단독 성립) — `_pending_threats` 소비처는 `_spawn_pending_threat` 하나뿐이고,
  즉시 스폰 경로와 파도 경로가 같은 spec 을 공유하는 것이 결함 자체다. 함께 바꿀 정의 없음
- 무대: `항만 침투 복합`(전부 저속: USV 14 · 022형 18.5 · 드론 28 m/s) + `ai_tactic='stagger'`.
  **고속 위협이 하나라도 있으면 `new_fleet` 이 안 비어 발동하지 않는다** — 그래서 지금껏 안 보였다
- 뿌리: 독립
- 결과: 프로브 p009 **FAIL(자폭 USV 12→24) → PASS(12→12)** 전환 확인 `[실측]`.
  회귀 42×32 **PASS(골든 무변동)** · 정적 56/56 PASS.
  **9.4④ 골든 무변동 규명**: 골든에 `ai_tactic='stagger'` 케이스가 **0건**이라
  이 경로는 애초에 감시 밖이었다 — **무대 부재**이고, 이것이 곧 **F-011 의 실증**이다.
  (`grep -c stagger audit_verify_regression.py` → 0). 남는 사각: stagger 경로 전체.
  → 3번 묶음(F-003·F-011)에서 골든 케이스를 추가할 때 **이 시나리오를 넣는다.**
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

- 위치: engine_combat.py:2318 `self.stats['total_threats'] += 1`  (파도 스폰 쪽 — 수정 후 미사일 가지 안)
- 근거: [코드]
- 이력: [기존] (같은 뿌리를 `be4e8b9` 가 한 번 건드렸다가 되돌림 — 그때는 초기 편성 쪽만 봤다)
- 심각도: 중간
- 반증조건: 파도 스폰 플랫폼이 `intercepted_threats` 에도 집계되면 대칭이라 문제없다.
  실측하니 L5120 주석이 *"MissileObj만 intercepted_threats에 집계 (항공기 플랫폼 격추는
  enemy_ships_destroyed로)"* 라고 명시 → 반증 안 됨. 또는 파도 스폰이 미사일만 만든다면
  무해하나, L2301 `else:` 가지가 `_new_threat()` 으로 **플랫폼을 만든다** → 반증 안 됨
- 재현: analysis/probes/p005_denominator_path_independence.py  ← **판정 S**(구조 불변식)
- 수정비용: 중
- 회귀위험: **골든 영향 큼** (요격률이 32지표에 들어 있다)
- 실행주체: 나 단독 (정의 확정은 아래 '짝' 에 명시 — 사용자 결정 불필요)
- 대상: engine_combat.py, app_main.py, app_changelog.json
- 짝: **F-008 과 한 묶음.** 분모 정의를 고치면 무력화율 이중 계산도 함께 사라진다.
  세 정의를 함께 확정한다 — `total_threats`=**발사체(미사일류)만** ·
  `intercepted_threats`=**발사체 요격만**(현행 유지) · `suicide_threats`=**자폭 플랫폼**.
  플랫폼 격침은 `enemy_ships_destroyed` 가 이미 센다. **한쪽만 고치면 안 되는**
  자리다(`be4e8b9` 가 되돌린 이유)
- 무대: 파도 스폰이 일어나는 편성 — 골든 `파도-시차공격`·`파도-혼합시나리오`(직전 묶음에서
  신설). 파도가 없으면 초기 편성 경로만 타서 **현재도 정의가 맞아** 변화가 안 보인다
- 뿌리: **F-008 의 뿌리** (집계 정의 축 — [[project-fleet-metric-flaw]] 와 같은 축). ~~F-004 의 증상~~ — F-004 가 오탐으로 종결돼 링크 철회
- 결과: 판정 S(p005) **FAIL→PASS** · p008 재실행에서 **이중 계산 소멸** 확인 `[실측]`.
  회귀 **24건 변화, 전부 규명**(9.4③) — 바뀐 지표는 `total_threats`·`intercept_rate`·
  `neutralization_rate` **셋뿐**, 8케이스 × 3지표:
  ```
  항모 계열 6건  −8   랴오닝-기본#1 114→106 · 공격+CAP#7 107→99 · CAP상시초계#2 118→110
                      원인: 항모가 함재기를 2기씩 주기적으로 _pending_threats 로 발진한다
                      (engine_combat.py:5553). 그 플랫폼 8기가 분모에 있었다
  파도 계열 2건  −12  파도-시차공격#2·#7 44→32 (022형 4 + 연안 자폭 드론 8)
  분자 무변동 → 요격률 상승은 **순수 분모 효과**(예: 0.4737→0.5094 = 54/114→54/106)
  나머지 38케이스·29지표 전부 무변동
  ```
  property 불변식 45케이스 위반 0. 골든 46×32 재PASS.
  **v22 1순위와의 관계**: [[project-fleet-metric-flaw]] 가 지목한 *"항모 함재기 무한
  생산으로 분모가 통제되지 않는다"* 의 **분모 쪽이 이 수정으로 닫혔다.** 생산 자체
  (단발 모드에서 `_enforce_wing_cap` 이 꺼져 무한 발진)는 **아직 열려 있다** → 별도 항목.
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

### F-008 · 축: 모델타당성 · 상태: 수정됨
- 위치: engine_combat.py:5691 `_n_tot = self.stats['total_threats'] + self.stats['suicide_threats']`  (F-009 수정으로 +11 이동)
- 근거: [실측]
- 이력: [신규]
- 심각도: 높음
- 반증조건: 파도 스폰 플랫폼이 `total_threats` 에 안 들어가면 이중이 아니다.
  실측: 같은 편성에서 파도 없음 `total_threats=32`, stagger(전부 파도) `=56` —
  **차이 24 = 편성 객체 수(12+8+4)와 정확히 일치** → 플랫폼이 분모에 들어간다. 반증 안 됨
- 재현: analysis/probes/p008_denominator_double_count.py · p005(구조 판정)
- 수정비용: 중 (세 지표 정의를 함께 설계해야 한다)
- 회귀위험: **골든 영향 큼** — `neutralization_rate` 가 32지표에 있다
- 실행주체: 나 단독
- 대상: engine_combat.py, app_main.py, app_changelog.json
- 짝: **F-005 와 한 묶음** (분모 정의를 고치면 이중 계산이 함께 사라진다)
- 무대: 골든 `파도-시차공격`·`파도-혼합시나리오`
- 뿌리: F-005 의 증상
- 결과: 판정 S(p005) **FAIL→PASS** · p008 재실행에서 **이중 계산 소멸** 확인 `[실측]`.
  회귀 **24건 변화, 전부 규명**(9.4③) — 바뀐 지표는 `total_threats`·`intercept_rate`·
  `neutralization_rate` **셋뿐**, 8케이스 × 3지표:
  ```
  항모 계열 6건  −8   랴오닝-기본#1 114→106 · 공격+CAP#7 107→99 · CAP상시초계#2 118→110
                      원인: 항모가 함재기를 2기씩 주기적으로 _pending_threats 로 발진한다
                      (engine_combat.py:5553). 그 플랫폼 8기가 분모에 있었다
  파도 계열 2건  −12  파도-시차공격#2·#7 44→32 (022형 4 + 연안 자폭 드론 8)
  분자 무변동 → 요격률 상승은 **순수 분모 효과**(예: 0.4737→0.5094 = 54/114→54/106)
  나머지 38케이스·29지표 전부 무변동
  ```
  property 불변식 45케이스 위반 0. 골든 46×32 재PASS.
  **v22 1순위와의 관계**: [[project-fleet-metric-flaw]] 가 지목한 *"항모 함재기 무한
  생산으로 분모가 통제되지 않는다"* 의 **분모 쪽이 이 수정으로 닫혔다.** 생산 자체
  (단발 모드에서 `_enforce_wing_cap` 이 꺼져 무한 발진)는 **아직 열려 있다** → 별도 항목.
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

### F-003 · 축: 검증체계 · 상태: 수정됨
- 위치: BLIND_SPOTS.md:1 `# 감사 사각지대 레지스트리 (BLIND_SPOTS)`
- 근거: [실측]
- 이력: [신규]
- 심각도: 중간
- 반증조건: 수동 도구가 종합 감사(major 전환)마다 **실제로 돌았다는 기록**이 있으면
  반증된다. 감사보고서에 `audit_pairwise`·`audit_fuzz` 실행 출력이 붙어 있는지 확인 필요
  → 이 판에서는 미확인. 다만 "돌았다"가 확인돼도 **major 당 1회**라는 사실은 남는다
- 재현: `chk_audit_tool_cadence` (S형식 — 착수 시 FAIL: 주기 미명시 11개)
- 수정비용: 소(훅 배선) ~ 중(무거운 것은 별도 주기)
- 회귀위험: 골든 영향 없음
- 실행주체: 나 단독
- 대상: audit_static_scan.py, BLIND_SPOTS.md
- 짝: **F-010 과 한 묶음** — 둘 다 *"안전망이 낡는 것을 아무도 안 본다"* 의 같은 부류이고
  같은 파일을 건드린다. F-011 잔여(골든 10토글)·F-007(부모 계약)은 파일이 달라 분리
- 무대: 저장소의 감사 도구 **20개** 중 훅 자동 8개 — 나머지 12개의 실행 주기가
  어디에도 적혀 있지 않다(종합 감사는 major 전환 때만 = 실질 major 당 1회)
- 뿌리: **F-007,F-010,F-011 의 뿌리** (안전망이 '있다'와 '돈다'가 다르다)
- 기준선(착수 시 FAIL 출력, 2026-09-20) `[실측]`:
  ```
  [FAIL] ⑥ 감사 도구 실행 주기 명시(훅 자동 or BLIND_SPOTS 주기표)
         주기 미명시 11개: _audit_campaign_smoke · _audit_compat · _audit_gui_smoke ·
         _audit_load_guard · _audit_make_pdf · _audit_mc_stability · _audit_scenario_smoke ·
         _audit_smoke_util · audit_db_consistency · audit_dead_toggle · audit_perf
  [FAIL] ③ KNOWN 사각 목록 최신(변별되면 빼야 한다)
         ashore_sm3_fired(고유값 4) · thaad_fired(2)
  ```
  ⚠ **절차 마찰(규약에 반영할 것)**: S형식은 *"검사 함수를 먼저 추가해 FAIL 을 확인"* 하는데,
  **FAIL 나는 검사는 pre-commit 이 막아 단독 커밋이 안 된다.** P형식(프로브 파일)은
  훅이 안 돌려서 가능하지만 S형식은 구조적으로 불가능하다.
  → 이 묶음은 **기준선 출력을 대장에 증거로 박고** 검사+수정을 한 커밋으로 올린다.
- 결과: `chk_audit_tool_cadence` **FAIL(11개) → PASS(0개)** `[실측]`.
  `BLIND_SPOTS.md` 에 **감사 도구 실행 주기 표**를 신설해 20개 전부의 주기를 명시했다.
  표가 밝힌 것: pre-commit 3종(41초) · pre-push 5종(181초) · **종합 감사(major 전환) 9종**
  (`audit_pairwise` 26분 30초는 훅에 넣기엔 너무 무겁다) · **보고 도구 2종은 exit 0 고정이라
  훅에 넣으면 안 된다**(항상 통과). 문서에 *"'메웠다' 가 아니라 'major 당 1회 확인한다'* 가
  정확한 표현"* 을 못박았다.
  **T반경 필수 검증(일부러 깨뜨리기)**: 표에서 `audit_perf.py` 한 줄을 지우니
  `[FAIL] 주기 미명시 1개: audit_perf.py` 로 잡혔다. 복구 후 PASS.
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
  **⚠ 배선 단서(3단계 실측)**: `audit_db_consistency` · `audit_dead_toggle` 은
  FAIL 문구만 찍고 **exit 0** 이다(코드에 *"각 항목은 사람이 판정"* 이라 명시된 **의도된
  보고 도구**). 이 둘을 훅에 물리면 **항상 통과하는 게이트**가 된다 — 배선 대상에서 제외하거나
  먼저 종료코드를 주어야 한다. 그리고 `audit_db_consistency` 는 지금 **미검토 발견 6건**을
  내놓고 있다(HIGH 1: Kh-32 '극초음속'인데 마하 4.4) — 수동이라 아무도 안 본 것이다.

### F-011 · 축: 검증체계 · 상태: 수정됨
- 위치: audit_verify_regression.py:50 `CASES = [`
- 근거: [실측]
- 이력: [신규]
- 심각도: 중간
- 반증조건: ① 그 토글들이 기본 ON 이면 골든이 암묵적으로 밟는다 → 실측하니 **11개는 기본
  `False`** 다. ② `audit_effect.py` 가 대신 회귀를 본다면 사각이 아니다 → `audit_effect` 는
  **같은 실행 안에서 ON/OFF 델타가 0이 아닌지**만 보고 **저장된 기준값과 대조하지 않는다**.
  즉 *"효과가 있다"* 는 지키지만 *"결과가 이전과 같다"* 는 안 본다 → 반증 안 됨.
  ③ 높음 부여는 보류한다 — 실제로 깨뜨려 PASS 나는 것을 **재현하지 않았다**(3.4 준수)
- 재현: analysis/probes/p011_golden_wave_coverage.py  ← **판정 P** (착수 시 FAIL: 파도 경로 0건)
- 수정비용: 중 (골든 케이스 추가 = 골든 갱신)
- 회귀위험: 골든 케이스를 늘리면 실행시간 증가(현재 38초)
- 실행주체: 나 단독 (범위를 **파도 스폰 경로 1건**으로 한정 — 토글 11개 전체는 후속)
- 대상: audit_verify_regression.py, audit_regression_golden.json
- 짝: **F-005·F-008 과 짝이다.** 이 묶음이 *무대* 를 만들고 그 다음 묶음이 *정의* 를 고친다.
  순서를 뒤집으면 집계 정의를 고쳐도 골든이 안 움직여 **변화를 관측할 수 없다**
  (F-009 에서 실제로 그랬다 — 9.4④ 규명이 '골든에 stagger 0건'이었다).
  저장소 선례: 분석 03 의 A↔B 순서 교체(*"비교가 성립하는 무대가 없으면 B의 효과를
  확인할 수 없다"*)와 같은 논리
- 무대: `ai_tactic='stagger'`(저속 위협 +30/+60초 지연) 또는 `enemy_fleet_mode='mixed'`
  (1파만 즉시). 둘 다 `_spawn_pending_threat` 을 거친다
- 뿌리: F-003 의 증상 (안전망의 *범위* 쪽)
- 결과: 프로브 p011 **FAIL(파도 경로 0건) → PASS(4건)** 전환 `[실측]`.
  골든 **42 → 46 케이스**(`파도-시차공격` #2·#7 · `파도-혼합시나리오` #1·#3).
  **기존 42케이스는 전 지표 무변동** — 회귀 출력이 신규 4건만 `[신규]` 로 표시했고
  `--update` 후 46×32 PASS. 9.4③ 요구(바뀐 지표를 하나씩 설명)를 **설명할 변화가
  없는 형태로** 충족했다.
  봉인된 값 예: `파도-시차공격#2` total_threats=44 · intercept_rate=0.7273.
  **남은 범위**: 이 묶음은 파도 스폰 경로만 덮었다. F-011 이 지적한 **토글 11개 중
  나머지 10개**(asw_forward·autonomous_engagement·battle_mode·campaign_fog·cec_jammed·
  laser_dew·minesweeping·multibearing·random_placement·ras_rearm·recon_drone)는
  → **2026-09-20 잔여분도 종결.** 골든 **46 → 52 케이스**(`미커버-무인자율`·
  `미커버-대잠소해`·`미커버-레이저배치`, 각 2시드)로 단발 경로 토글 9개를 봉인했다.
  판정 `analysis/probes/p011b_golden_toggle_coverage.py` **PASS** —
  *"기본 OFF 인데 골든이 안 켜는 토글 0개"*. 남은 둘(`battle_mode`·`campaign_fog`)은
  전장·캠페인 **별도 경로**라 전용 스모크가 본다(프로브가 그 사실을 명시적으로 제외).
  한 케이스에 여러 토글을 묶은 이유: 목적이 *그 코드 경로를 골든에 들이는 것*이지
  토글별 독립 효과 측정이 아니다(독립 효과는 `audit_effect` 가 ON/OFF 델타로 따로 본다).
  기존 46케이스 전 지표 무변동 — 신규 6건만 추가됐다 `[실측]`
- 요약: 엔진이 소비하는 토글 중 **11개를 회귀 골든이 한 번도 켜지 않는다** — 그 경로의
  동작이 바뀌어도 회귀는 PASS 한다
- 근거본문:
  ```
  골든이 명시적으로 켜는 토글 40개 · EFFECT_ALIVE 43개 중 골든 미사용 16개
    기본 True (ON 상태만 감시, OFF 대조 없음) 5개:
      cec_preassign · munition_limit · ship_evasion · standoff_spawn · subsystem_damage
    기본 False (아예 안 밟음) 11개:
      asw_forward · autonomous_engagement · battle_mode · campaign_fog · cec_jammed ·
      laser_dew · minesweeping · multibearing · random_placement · ras_rearm · recon_drone
  ```
  **이 11개 중 다수가 기준값 메모리로 검증을 마친 기능이다** —
  [[project-baseline-ras-rearm]] · [[project-baseline-unmanned-isr]] ·
  [[project-baseline-autonomous]] · [[project-baseline-mine-warfare]] ·
  [[project-laser-efficacy-finding]]. **검증은 했는데 그 결과를 지키는 장치가 없다.**
  기준값은 메모리(사람이 읽는 문서)에 있고 골든(기계가 읽는 파일)에는 없다.
  → B단계 설계의 약점 **나**(*"회귀 PASS 는 안 깨뜨렸다의 증거가 아니다"*)에 대한
  **이 저장소의 구체적 실측 증거**다. 영향 반경 표가 반경 E 에 회귀를 소환해도,
  **그 회귀가 보는 범위 밖**이면 소용이 없다.

### F-010 · 축: 검증체계 · 상태: 수정됨
- 위치: audit_static_scan.py:577 `KNOWN = {'usa_cost', 'usa_shots', 'iff_failures', 'iff_fratricide'}`  (수정 후 — 6→4)
- 근거: [실측]
- 이력: [신규]
- 심각도: 중간
- 반증조건: 화이트리스트가 *"한 번 등재하면 유지"* 를 의도했다면 낡은 게 아니다. 그러나
  같은 파일의 `EFFECT_DEBT` 는 **"줄기만 한다"** 를 명문화했고, 이 검사의 docstring 도
  *"새로 항상-동일 지표가 생기면 FAIL 로 골든 케이스 추가를 유도"* 라며 **커버리지를 늘리는
  방향**을 목적으로 밝힌다 → 줄어야 하는 목록이 맞다. 반증 안 됨
- 재현: `chk_known_whitelist_fresh` (S형식 — 착수 시 FAIL: ashore_sm3_fired·thaad_fired)
- 수정비용: 소
- 회귀위험: 골든 영향 없음(도구)
- 실행주체: 나 단독
- 대상: audit_static_scan.py
- 짝: **F-003 과 한 묶음**
- 무대: 골든 46케이스에서 `ashore_sm3_fired` 고유값 4 · `thaad_fired` 2 — 이미 변별되는데
  면제 목록에 남아 있다
- 뿌리: F-003 의 증상 (면제 목록이 낡는 것을 아무도 안 본다)
- 결과: `chk_known_whitelist_fresh` **FAIL(2개) → PASS** `[실측]`.
  `KNOWN` 면제 목록 **6 → 4**(`ashore_sm3_fired`·`thaad_fired` 제거). 이제 목록이
  `EFFECT_DEBT` 와 같은 규율을 갖는다 — **줄기만 하고, 변별되기 시작하면 검사가 뺄 것을 요구**한다.
  `chk_golden_coverage` 도 PASS 유지(제거한 둘은 실제로 변별되므로 사각이 아니다).
  **T반경 필수 검증**: `KNOWN` 에 변별되는 `total_cost` 를 넣으니
  `[FAIL] total_cost(고유값 30)` 로 잡혔다. 복구 후 PASS.
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

### F-007 · 축: 뼈대 · 상태: 수정됨
- 위치: engine_combat.py:6443 `def _apply_ship_evasion(self, evade_r_base: float | None = None,`  (수정 후 — 부모 계약 복원된 시그니처)
- 근거: [코드]
- 이력: [신규]
- 심각도: 중간
- 반증조건: 인자를 넘기는 호출부가 하나도 없으면 **현재는** 안전하다. 실측하니 호출부는
  `self._apply_ship_evasion()`(L2796, 무인자)과 자식 내부의 `super()._apply_ship_evasion(...)`
  둘뿐이라 **지금은 터지지 않는다** → 심각도를 `중간` 으로 낮춘다. 다만 계약 위반 자체는
  반증되지 않는다(부모의 두 파라미터를 외부에서 쓸 수 없게 됐다)
- 재현: `chk_subclass_signature` (S형식 — 착수 시 FAIL, 수정 후 PASS)
- 수정비용: 소
- 회귀위험: 골든 영향 없음(시그니처만 맞추고 동작은 유지 가능)
- 실행주체: 나 단독
- 대상: engine_combat.py, audit_static_scan.py
- 짝: 없음(단독 성립) — 동작을 바꾸지 않고 계약만 복원하므로 함께 고칠 정의가 없다
- 무대: `BattleEngine` 인스턴스에 `evade_r_base=` 를 넘기는 호출. 현재 그런 호출이
  없어서 **터지지 않았을 뿐**이고, 하나만 생기면 TypeError 다
- 결과: `chk_subclass_signature` **FAIL → PASS** `[실측]`. 부모의 두 파라미터를
  `None` 기본값으로 **받아 두고**, 명시적으로 넘어오면 자세 분기보다 **우선**하게 했다
  (호출자가 일부러 지정한 값이므로). 회귀 **46×32 PASS — 동작 보존**(순수 계약 복원).
  **주입 검증**: 시그니처를 다시 좁히니 즉시 `[FAIL] _apply_ship_evasion(부모 2개 인자
  → 자식 0개)` 로 잡혔다. 정적 스캔 **61/61 PASS**.
  → `CLAUDE.md` 종합 감사 ①의 *"부모 무수정"* 이 **수동 점검이라 놓쳤던 것**을
  이제 도구가 강제한다(F-003 이 지적한 부류의 해소 사례)
- 뿌리: F-003 의 증상 (수동 점검이라 실제로 놓쳤다)
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

### F-012 · 축: 모델타당성 · 상태: 수정됨
- 위치: audit_db_consistency.py:38 `_MACH_MS = 340.0`
- 근거: [실측]
- 이력: [신규]
- 심각도: 중간
- 반증조건: 이 저장소가 마하를 **해수면 기준으로만** 정의하기로 했다면 도구가 옳다.
  그러나 엔진에는 `isa_atmosphere()`(engine_combat.py:318, ICAO 표준대기)가 있고
  고도별 온도·굴절을 실제로 쓴다(L2423 `_isa_refraction_factor`) → 저장소 자신이
  고도 의존을 인정한다. 반증 안 됨
- 재현: analysis/probes/p012_mach_altitude.py
- 수정비용: 소
- 회귀위험: 골든 영향 없음(감사 도구)
- 실행주체: 나 단독
- 대상: audit_db_consistency.py
- 짝: 없음(단독) — DB 는 건드리지 않는다. 고칠 곳은 도구다
- 무대: `altitude_m` 이 명시된 고고도 무기. Tu-22M3(11km)·Kh-32 1500 m/s
- 결과: `_sound_speed(alt_m)`(ICAO 표준대기)를 도입하고 탑재 미사일 판정에 모기의
  `altitude_m` 을 넘겼다. **HIGH 오탐 소멸** — 발견 6건 → 5건(HIGH 0). `[실측]`
  프로브 `p012_mach_altitude.py` 가 근거(11km 음속 295 → 마하 5.08).
  고도 미상이면 해수면 340 으로 **보수적** 판정을 유지한다
- 뿌리: 증상
- 요약: `audit_db_consistency` 가 마하를 **해수면 음속 340 m/s 고정**으로 환산해,
  **고고도 무기를 '표기 과장'으로 오판**한다 — Kh-32(1500 m/s)는 순항 고도에서 마하 5.08 이다
- 근거본문:
  ```
  audit_db_consistency.py:32  _MACH_MS = 340.0        ← 해수면 고정
  engine_combat.py:318        def isa_atmosphere(alt_m)  ← 엔진은 고도별 대기를 쓴다

  ISA 음속과 1500 m/s 의 마하수:
     0 m   340 m/s → 마하 4.41   (도구의 판정 근거)
    11 km  295 m/s → 마하 5.08   ← Kh-32 순항 고도대
    20 km  295 m/s → 마하 5.08
    40 km  317 m/s → 마하 4.73
  ```
  `engine_core.py:656` 주석이 *"Kh-32 극초음속 대함미사일 탑재 (마하 5, 고고도 강하)"* 라고
  **고도를 명시**한다. 즉 DB 는 처음부터 고고도 기준으로 적었고, **도구가 그 전제를 모른다.**
  → 도구의 `HIGH` 1건은 **오탐**이다. 고치는 방향은 DB 가 아니라 도구 —
  속도 판정에 **기준 고도**(또는 `cruise_alt_m`)를 반영하거나, 고고도 무기를 예외로 둔다.
  **이게 중요한 이유**: 이 오탐을 믿고 DB 를 "고쳤으면" 실제 제원과 멀어졌을 것이다.
  감사 도구의 판정도 **근거를 확인하고 받아야 한다**(규약 1.5 — 이전 판정은 재검토 대상).

### F-001 · 축: 위생 · 상태: 수정됨
- 위치: CLAUDE.md:18 `| 파일 | 역할 |`
- 근거: [실측]
- 이력: [신규]
- 심각도: 중간
- 반증조건: 표가 "주요 파일만" 싣겠다고 선언했다면 누락이 아니다. 실제로는 `CLAUDE.md`
  자신이 *"파일 구조 표 (파일 → 역할). 어디를 고쳐야 하는지가 여기서 나온다"* 를
  필수 항목으로 규정하고 *"안 고칠 거면 애초에 적지 않는다"* 고 적었다 → 반증 안 됨
- 재현: `chk_claude_md_coverage` (S형식 — 착수 시 FAIL: 런타임 5개 누락)
- 수정비용: 중
- 회귀위험: 골든 영향 없음(문서)
- 대상: CLAUDE.md, audit_static_scan.py, audit_dead_toggle.py (L-1 stale 문구 동반 정정)
- 짝: **F-002·L-1 과 한 묶음** — 셋 다 *"문서가 코드보다 늦다"* 의 같은 뿌리이고,
  F-002 를 아카이브하면 표에서도 빼야 하므로 함께 움직인다
- 무대: 루트 `.py` 중 **도구가 아닌 런타임 모듈**. 도구·실험 스크립트는 표 대상이 아니다
  (README 파일구조 표와 같은 기준)
- 실행주체: 나 단독
- 뿌리: F-002 의 뿌리(표에 없으니 죽은 모듈이 있어도 안 보인다)
- 결과: `chk_claude_md_coverage` 신설 **FAIL(런타임 5개 누락) → PASS** `[실측]`.
  표에 `db_terrain`·`db_ocean_acoustic`·`db_ocean_environment`·`forecast_features`·
  `ai_policy_infer` 를 역할과 함께 추가했다(전부 엔진·워커가 실제로 import 하는 모듈).
  도구·실험 스크립트는 README 파일구조 표와 같은 기준으로 제외한다.
  **이제 README 와 `CLAUDE.md` 양쪽에 전수 커버 강제가 걸린다** — 한쪽만 자라던 원인 제거
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

### F-002 · 축: 부채 · 상태: 수정됨
- 위치: _archive/data/db_ground_threat.py:2 `db_ground_threat.py — 한반도 군사 배치 데이터베이스`  (이동 후)
- 근거: [실측]
- 이력: [신규]
- 심각도: 중간
- 반증조건: 동적 로딩(`importlib`·`getattr`)으로 쓰이면 죽은 게 아니다. 확인 결과
  이 저장소의 `importlib` 사용처는 `audit_static_scan.py` 의 `engine_core`·`engine_combat`
  둘뿐이라 반증되지 않는다
- 재현: `chk_claude_md_coverage` (S형식 — 아카이브 후 '표에는 있으나 없는 파일' 로 검출)
- 수정비용: 소(삭제) / 대(배선)
- 회귀위험: 골든 영향 없음(아무도 안 쓰므로) — 그 사실 자체가 발견의 내용이다
- 대상: db_ground_threat.py → _archive/data/db_ground_threat.py, CLAUDE.md
- 짝: **F-001 과 한 묶음** — 아카이브하면 `CLAUDE.md` 표에서도 빼야 한다
  (`chk_claude_md_coverage` 가 *"표에는 있으나 없는 파일"* 로 실제로 잡았다)
- 무대: 해당 없음 — 런타임 경로가 아니라 **배선되지 않은 데이터 모듈**이다
- 실행주체: 나 단독 — **판정 완료(2026-09-20)**: `_archive/data/` 로 이동.
  배선 불가(`engine_army.py:6` 이 *"전면 지상전은 범위 밖(설계 결정 plan_v20_army.md §8)"*
  이라 명시하고, 실제로 좌표를 안 쓰고 추상 구역 프리셋을 쓴다) · 삭제는 아깝다(공개 출처
  달린 실측 수집물). 저장소에 이미 `_archive/plans/` 관례가 있고 CLAUDE.md ⑥위생이
  *"완료 잔재는 삭제 또는 `_archive/` 로 이동"* 을 규정한다. **죽은 코드가 아니라
  범위 밖으로 밀려난 자산**이다
- 뿌리: 증상
- 결과: `_archive/data/db_ground_threat.py` 로 이동(`git mv`, 415줄 보존) `[실측]`.
  `CLAUDE.md` 파일 구조 표에서 빼고 **아카이브 사유를 문서에 남겼다** — 지우지 않은 이유
  (공개 출처 달린 실측 수집물)와 배선하지 않은 이유(`engine_army` 가 전면 지상전을
  범위 밖으로 선언, `plan_v20_army.md §8`)를 함께. `chk_claude_md_coverage` 가
  *"표에는 있으나 없는 파일"* 로 잡아 준 덕에 표 정리도 빠뜨리지 않았다
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

### F-013 · 축: 모델타당성 · 상태: 미처리
- 위치: engine_combat.py:4036 `pk_base  = wpn_info['pk_dist']['mean'],`  (F-005 수정으로 이동)
- 근거: [실측]
- 이력: [신규]
- 심각도: 중간
- 반증조건: `alpha`·`beta` 를 어디선가 쓰면 살아 있다. 실측: **참조 0회** ·
  `betavariate`/`np.random.beta` **0회** · `pk_dist` 는 항상 `['mean']` 으로만 접근(5곳).
  또는 *"평균만 쓰는 것이 의도"* 라면 결함이 아니다 — 그렇다면 **`alpha`·`beta` 를
  DB에 둘 이유가 없고**, `CLAUDE.md` 가 *"`pk_dist` 는 Beta 분포 파라미터"* 라고
  선언한 것과 종합 감사 ⑧의 *"Beta 분포 `pk_dist` 파라미터 유효성"* 점검 항목이
  가리키는 바와 어긋난다 → 반증 안 됨(판단은 4.5로 넘긴다)
- 재현: (없음) — 정적 사실이라 S형식으로 닫는다(`chk_pk_dist_used` 신설 가능)
- 수정비용: 소(파라미터 삭제) / 중(표집 도입 — 결정론·골든에 영향)
- 회귀위험: **표집을 도입하면 골든 전면 갱신**(신규 `random` 호출이 RNG 순서를 바꾼다)
- 실행주체: **사용자 결정 필요** (분산을 모델에 넣을 것인가, 파라미터를 뺄 것인가)
- 뿌리: 증상
- 요약: `FRIENDLY_DB` 14개 무기 전부가 **Beta 분포 파라미터(`alpha`·`beta`)를 갖고 있는데
  한 번도 표집되지 않는다** — 항상 `mean` 상수만 쓴다
- 근거본문:
  ```
  pk_dist 보유 무기 14 / FRIENDLY_DB 14
    SM-3 Block IIA  alpha=17 beta=3  mean=0.85   Beta 표준편차 0.078
    SM-6            alpha=9  beta=3  mean=0.75   표준편차 0.120
    SM-2 Block IIIB alpha=16 beta=4  mean=0.80   표준편차 0.087
    RIM-116 RAM     alpha=9  beta=3  mean=0.75   표준편차 0.120
  코드 참조:  alpha 0회 · beta 0회 · mean 5회 · betavariate/np.random.beta 0회
  ```
  **모델이 요격 확률의 불확실성을 선언해 놓고 쓰지 않는다.** 표준편차 0.08~0.12 는
  작지 않다 — MC 산포가 그만큼 과소평가된다(현재 산포는 교전 전개의 무작위성에서만 온다).
  기댓값은 `mean` = Beta 평균이라 **평균은 정확하고 분산만 0**이다.
  → 이것이 [[project-baseline-v11]] 의 *"요격률 11.5% ± 4.0%"* 같은 산포 수치의
  **해석에 영향**을 준다(그 ±4.0%p 에 Pk 불확실성은 포함돼 있지 않다).

### F-014 · 축: 성능 · 상태: 미처리
- 위치: engine_combat.py:1098 `def _get(self):`
- 근거: [실측]
- 이력: [기존] ([[plan-v12-numpy]] 가 *"PNG substep 이 진짜 병목"* 이라 프로파일했던 그 자리)
- 심각도: 중간
- 반증조건: 프로파일러 오버헤드가 이 함수에 편중됐다면 과대 계상이다. `_get` 은 두 줄짜리
  `getattr(...)[i]` 라 호출당 비용이 작고, **호출 수 자체가 1,174,130회**라 오버헤드를
  빼도 순위가 바뀌기 어렵다. 다만 **절대 수치는 오버헤드 포함**이므로 `높음` 은 주지 않는다
- 재현: `python analysis/probes/p014_profile_single.py` (프로파일 재실행)
- 수정비용: 대 (v12.7 단계2 = 위협 배열화 본편)
- 회귀위험: **골든 영향 없음이어야 한다**(순수 성능) — 단계1이 bit-identical 이었던 것처럼
- 실행주체: 실측·승인 필요
- 뿌리: 증상
- 요약: v12.7 numpy 이행의 **프록시 계층(`_et_col._get`)이 단발 1회에서 117만 회 호출**되어
  누적 시간의 **약 22%** 를 쓴다
- 근거본문:
  ```
  단발 1회(랴오닝 항모전단·seed 7) wall 1.34s(프로파일러 포함) · sim_time 1652s
    cumtime  ncalls
    1.345         1  run_v7_simulation
    0.375      1653  _friendly_defense        (28%)
    0.292   1174130  _et_col.<locals>._get    (22%)   ← 프록시 속성 위임
    0.279      1653  _update_positions        (21%)
    0.145      1653  _friendly_strike
    0.137      1653  _enemy_fire
    0.117   1298792  builtins.getattr                  ← 위 _get 이 부른 것
  ```
  `_et_col()` 은 *"데이터는 엔진 컬럼에 있고 객체는 (엔진, 행 i)만 든다"* 는
  **v12.7 단계1의 호환 shim** 이다. 배열로 옮기는 중간 상태라 **속성 접근 한 번이
  `getattr` + 인덱싱 두 번**이 된다. 단계2(위협 배열화 본편)가 끝나면 사라질 비용이지만,
  **지금은 그 값을 치르고 있고 이득은 아직 없다.**
  → [[plan-v12-numpy]] 는 *"PNG substep 이 진짜 병목"* 이라 판단했는데, **현재 프로파일
  상위에 PNG 가 없다.** 병목이 옮겨갔다(또는 그때와 시나리오가 다르다) — 규약 2.4-4 가
  요구한 *"추측한 병목과 실측 병목이 다르면 그 차이를 명시하라"* 에 해당한다.
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
### F-004 · 축: 뼈대 · 상태: 오탐
- 위치: engine_combat.py:6777 `def _compile(self) -> dict:`  (BattleEngine 쪽)
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


---

## 낮음 집계 (개별 등재하지 않음 — 규약 3.1)

**L-1. 문서의 stale 수치 — ✅ 정정 완료(2026-09-20)** `[실측]` — 전부 "도구 출력이 정본, 문서는 손으로 적음"에서 온다.

| 위치 | 적힌 값 | 실제 |
|------|---------|------|
| `CLAUDE.md:200` | 고정 **8개 시나리오** | **42케이스** (골든 실행 출력) |
| `CLAUDE.md:248` | **8케이스·26지표** | **42케이스·32지표** |
| `CLAUDE.md:528` | 회귀 **38×29** | **42×32** |
| `audit_dead_toggle.py:7` | EFFECT_DEBT 유예 **현재 43개** | **0개** (`EFFECT_DEBT = set()` — 완전 청산) |
| `BLIND_SPOTS.md` 1번 | pairwise **43개→903쌍** | **51개→1,275쌍** (이 판에서 실행한 출력) |

**정정 내역**: `CLAUDE.md` 8개 시나리오→46케이스 · 8케이스·26지표→46케이스·32지표 ·
회귀 38×29→61·46×32 · `audit_dead_toggle` docstring 'EFFECT_DEBT 43개'→'0개(전부 상환)'.
`BLIND_SPOTS` 의 903쌍/43개는 실행 주기 표 신설 때 함께 정리했다.

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

**함수 18개 중 7개 · 상수 29개 중 6개**가 어디서도 안 쓰인다.

**판정(2026-09-20) — 지우지 않는다.** F-002(모듈 전체 미사용)와 성격이 다르다:
이 모듈들은 **살아 있고**(`db_terrain.STRAITS_DB` 를 `engine_combat` 이,
`db_ocean_acoustic.sonar_detection_range` 를 소나 방정식이 쓴다) 일부 심볼만 남는다.
그중 `OCEAN_SVP_PRECOMPUTED`(해역별 음속 프로파일)·`mackenzie_sound_speed` 는
**2-A 가 못 한 소나 검산의 대조군**이 될 수 있다 — 2.2C(왜곡의 크기)를 측정할 때
문헌값 대신 쓸 수 있는 실측 자료다. **측정 전에 지우면 그 기회가 사라진다.**
→ `plan_roadmap.md` 의 *남은 일*(2.2C 왜곡 크기 측정)에 **선행 조건으로 연결**하고,
그 측정이 끝난 뒤 *쓸 것 / 지울 것* 을 가른다. **보류가 아니라 순서다**(규약 4.2). [[feedback-real-data]] 로
*"추정값 대신 실측값을 코드에 내장"* 한 데이터인데 **절반 가까이 배선되지 않았다.**
F-002(모듈 통째)와 같은 부류이고, 4단계(부채)에서 *배선할 것 / 지울 것*을 가른다.

> **방법 메모(중요)**: 첫 스캔은 `호출처 0` 후보를 **100건** 냈는데 표본 4건을 확인하니
> `_build_home_page`(리스트에 콜백으로 등록) · `_pool_map`(`map_fn=` 인자로 전달) 처럼
> **호출 괄호가 없는 참조**를 놓친 거짓 양성이었다. 파일 **내부 호출**도 미사용으로
> 오판했다(`thorp_absorption` 은 `sonar_detection_range` 가 부른다).
> 걸러내니 13건. 규약 2.4-2 *"grep 히트 수만 세지 않는다 — 각 히트를 읽어 참/거짓 판정"*
> 이 실제로 **87건의 거짓 양성**을 막았다.
