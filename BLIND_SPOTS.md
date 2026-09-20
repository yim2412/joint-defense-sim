# 감사 사각지대 레지스트리 (BLIND_SPOTS)

> **목적**: 감사가 **현재 못 보는 것**을 명시적으로 목록화한다. "모르는 사각(unknown
> unknowns)"을 "아는 사각(known unknowns)"으로 바꾸는 것이 감사 완결성의 핵심 —
> 갭이 보여야 메운다. 새 사각을 발견하면 여기 추가하고, 메우면 ✅로 옮긴다.
> 정본 규칙: `CLAUDE.md` 종합 감사 · 도구: `audit_static_scan.py`(정적) ·
> `audit_verify_regression.py`(회귀 오라클) · `audit_property.py`(불변식 제2 오라클).

## 감사 계층 (무엇으로 무엇을 잡나)
| 도구 | 오라클 종류 | 잡는 것 | 못 잡는 것 |
|------|-------------|---------|------------|
| `audit_verify_regression.py` | 자기참조(골든) | 의도치 않은 동작 변화 | 골든 자체가 틀렸을 때 |
| `audit_property.py` | 독립 불변식 | 확률범위·합=1·NaN/Inf·outcome 유효 | 값이 "그럴듯하나 틀린" 경우 |
| `audit_static_scan.py` | 구조 정합 | 3종세트·복원·버전·문서·vacuous | 런타임 동작 |
| GUI 스모크 | 실제 실행 | exe/GUI 전용 버그 | 클릭 안 한 경로 |

---

## 감사 도구 실행 주기 — **"있다"와 "돈다"는 다르다** (2026-09-20 신설)

> 전면 분석 F-003: 감사 도구 20개 중 **훅이 자동으로 돌리는 것은 8개**였고, 이 문서가
> *"메웠다"* 고 선언한 사각 둘(pairwise 조합·수치 fuzz)이 **수동 목록**에 있었다.
> 종합 감사는 major 전환 때만 돌므로 실질 **major 당 1회**다. 레지스트리가 낙관적으로
> 거짓말하지 않도록 **모든 도구의 주기를 여기 적는다.**
> `audit_static_scan.chk_audit_tool_cadence` 가 미등재 도구를 FAIL 로 잡는다.

| 도구 | 주기 | 비고 |
|------|------|------|
| `audit_static_scan.py` · `audit_verify_regression.py` · `analysis/check_protocol.py` | **pre-commit 자동** | 합계 약 41초 |
| `audit_property.py` · `audit_effect.py` · `_audit_roundtrip.py` · `_audit_ui_shot.py` · `_audit_render_smoke.py` | **pre-push 자동** | 합계 **181초**(property 혼자 133초) |
| `audit_pairwise.py` | **종합 감사(major 전환)** | **26분 30초**(토글 51개 → 1,275쌍) — 훅에 넣기엔 너무 무겁다 |
| `audit_fuzz.py` | 종합 감사 | 수치 키 33개 × 극단값 3종 |
| `audit_perf.py` | 종합 감사 ④ | wall-time 회귀 가드 |
| `_audit_compat.py` | 종합 감사 ⑦ | 구버전 cfg 하위호환 |
| `_audit_mc_stability.py` | 종합 감사 ④ | MC 수치 안정성 |
| `_audit_gui_smoke.py` · `_audit_campaign_smoke.py` · `_audit_scenario_smoke.py` | 종합 감사 ⑤ · 빌드 후 | 모드별 GUI 자동화 |
| `_audit_smoke_util.py` · `_audit_load_guard.py` | 위 스모크의 **보조 모듈** | 단독 실행 대상 아님 |
| `audit_db_consistency.py` · `audit_dead_toggle.py` | **보고 도구(수동)** | **exit 0 고정** — 사람이 판정한다. **훅에 넣으면 안 된다**(항상 통과) |
| `_audit_make_pdf.py` | 감사 보고서 생성 | 감사 종료 시 1회 |

> **읽는 법**: '종합 감사' 주기는 **major 전환 때만**이라는 뜻이다. 그 주기의 도구가
> 지키는 사각은 *"메웠다"* 가 아니라 **"major 당 1회 확인한다"** 가 정확한 표현이다.

---

## 🔴 열린 사각 (메울 것)

1. **조합 커버리지 = 2^N 미검증 (pairwise 해소)** — `audit_property.py`는 40% 랜덤 조합
   표본만. **`audit_pairwise.py`(2026-07-10 신설)가 엔진 소비 토글 전수 쌍(43개→903쌍)을
   각각 ON으로 단발 실행해 크래시·NaN·보존식 위반을 전수 탐지** → pairwise 보장. 남은
   미커버: **3개 이상 동시(triple+) 조합**과 **전장·캠페인 경로 pairwise**는 아직(단발만).
2. **단조성 불변식 미구현** — 보존식(요격≤총·rate=요격/총)은 property에 도입했으나
   "적↑→요격률↓" 단조성은 **노이즈(시드 분산)로 신뢰도 낮아 보류**. 평균 다수 시드
   필요 → 비용 대비 가치 낮음.
3. **골든 오라클 자기참조** — 회귀는 "이전과 같은가"만. 골든 갱신 시 "왜 바뀌었나"는
   사람 판단이 유일 오라클. property 스위트가 독립 오라클로 보강하나 완전 대체 불가
   (오라클 문제는 원리적으로 미해결 — 관리 대상).
4. **UI 시각적 깨짐·안 눌러본 경로 크래시(부분 해소)** — 탭 렌더 크래시는
   `_audit_render_smoke.py`, 안 보이는 체크박스는 `_audit_roundtrip.py`가 잡는다.
   2026-09-19 **`_audit_ui_shot.py` 신설로 범위를 넓혔다** — `WA_DontShowOnScreen` +
   `widget.grab()`으로 **화면을 점유하지 않고** QLabel `&&` 표기·텍스트 잘림(가로/세로)·
   12px 미만 글씨를 검사한다(pre-push 자동 실행, 결함 3종 주입으로 검출 확인).
   묶음 C·A·B에서 이 방식으로 실제로 잡은 것: `C&&D` 표기 · 버튼 세로 잘림 70건 ·
   스크롤바가 글자를 덮는 문제 · 정밀도 안내 문구 stale · 실험적 레이블 수 오카운트.
   - **남은 사각**: 색 대비·레이아웃 미학·3D(QWebEngine은 실제 창 필요)·애니메이션은
     여전히 사람 눈 몫이다. 잘림 판정 여유(세로 12px)는 **이모지 폰트 대체로 sizeHint가
     과대 보고되는 실측 사례** 때문에 둔 것이라, 그보다 작은 잘림은 놓친다.
5. **GUI abort(중단) 실제 클릭 미자동화** — 전파는 헤드리스로 확인하나, MC 실행 중
   중단 버튼 클릭→워커 잔존 0 시나리오는 스모크에 없음(GUI 타이밍 난도).
6. **프리셋 편성 count ↔ 표기(changelog/주석) 정합** — 자유텍스트 파싱이라 자동화
   난도 높음(v16.05서 ARM 20 vs 표기 24 수동 발견). 미해소.
7. **비-enable_ 수치 키 전수 미점검 (부분 해소)** — 경계 5케이스는 property에 있고,
   **단발 경로는 `audit_fuzz.py`가 수치 키 33개×극단값 3종(0·음수·거대값) 전수 주입해
   크래시·NaN·확률범위 위반 자동 탐지**(2026-07-10 신설, 무거워 종합감사·수동 실행). 남은
   미커버: **전장(run_battle)·캠페인 경로의 수치 키** fuzzing은 아직(단발만).

## ✅ 메운 사각 (이력)
- **재할당 전역을 이름 import (목록에 없던 사각)**(2026-09-20) → `chk_global_name_import`
  신설. `global X` 로 재대입되는 전역을 `from mod import X` 하면 import 시점 값이 복사돼
  **py_compile·정적·회귀가 전부 PASS인데 기능만 조용히 죽는다.** 이 저장소가 두 번 당했고
  (`_GLOBAL_POOL` 예열 풀 · `CHART_DPI` DPI 자동감지), `CLAUDE.md`에는 "옮기기 전에 grep 하라"는
  **사람 규칙으로만** 있었다. 분석 규약 B단계 **역사 대조**에서 발견 — 과거 실제 결함 형태를
  주입해 FAIL로 잡히는 것을 확인했다. **이 항목은 열린 사각 목록에 아예 없었다**(모르는 사각).
- **죽은 기능 게이트가 캠페인 층을 안 봄**(2026-07-16 발견 → 2026-07-19 해소, 2026-09-19
  재확인) → `chk_effect_coverage`의 `consumed` 스캔을 `engine_campaign`·`airforce`·`army`·
  `joint`까지 확장. **v20.5 부채 43개를 만든 바로 그 구멍**이 캠페인 층에 열려 있었다.
  2026-09-19 실측 재확인: 엔진이 소비하는 `enable_*` **61개 전부 커버**(캠페인 층 계열
  10개도 미커버 0). 스캐너 출력 기준 **부채 0 · 상환 43 · 종결 1**.
  ⚠ 이 항목은 **해소된 뒤에도 두 달간 '열린 사각'으로 남아 있었다** — 문서가 코드보다
  늦으면 이미 메운 구멍을 다시 파게 된다. 사각을 메우면 그 자리에서 여기로 옮길 것.
- **안 보이는 체크박스(시각 버그의 검출가능 부분집합)**(v17.01.11) → `_audit_roundtrip.py`에
  인디케이터 스타일 검사 추가. `_wire_chk_color` 목록에서 빠진 체크박스는 네모가 어두운
  배경에 안 보이는데, styleSheet에 'indicator' 있는지로 헤드리스 탐지(사용자가 눈으로 발견한
  실험적 토글 9개 미표시 버그를 수정하고 자동 검출로 봉인). **시각적 버그도 일부는 도구화 가능.**
- **UI 탭 렌더 크래시**(v17.01.10) → `_audit_render_smoke.py` — 9개 차트 함수를 실제+엣지
  데이터로 헤드리스 호출(UIA 취약성 회피). UIA 탭 클릭 순회가 커스텀 위젯으로 막힌 걸
  렌더 크래시 테스트로 우회(입력 보정: mc_chart는 실제 MC dict, stress/sobol은 {} 현실적).
- **효과 검증(죽은 토글)**(v17.01.10) → `audit_effect.py` — 효과 입증 시나리오에서 ON/OFF
  델타로 효과 확인(전장전용·엣지케이스는 수동 목록 명시). v21.2에서 **캠페인 전용 토글도
  잴 수 있게 `CAMPAIGN_PROBES` 추가**(단발 8종 + 캠페인 1종).
- **복원 누락 정규식 취약**(v17.01.10) → `_audit_roundtrip.py` — offscreen Qt로 토글
  뒤집기→복원→재빌드 실행 대조(정규식 무관, 44개 전수). strike·thaad·ashore 근본 차단.
- **보존식·경계 불변식**(v17.01.10) → `audit_property.py`에 요격≤총·rate정합·개수≥0·
  축퇴 수치(horizon 0/음수) 추가 + property 자체 vacuous 가드(단발 총위협=0 시 FAIL).
- **상시 ON 8종 의도** → `ALWAYS_ON` 화이트리스트로 명시(chk_flag_consume_auto·roundtrip
  공통) — 체크박스 없는 내부 기본값(cfg 리터럴 True)으로 문서화. round-trip이 이들을
  뒤집기 불가로 자동 식별해 정적 분석과 교차 확인.
- **3종세트 하드코딩 목록 → 자동추출**(v17.01.10) — enable_ 전수 44개 복원 자동검사.
- **vacuous-pass(0개 추출→조용히 통과)** → `guard_count` 하한 assert(v17.01.10).
- **캠페인 3종세트 미등록**(engine_campaign 소스) → 소비처 명시 검사(v17.01.09).
- **리소스 상대경로 폴백** → `chk_resource_paths`(v18.1). **_PLANS stale** → `chk_plans_stale`.

## 자동 실행 (사람 기억이 아니라 도구가 강제)
- **pre-commit**(`.githooks/pre-commit`) — 커밋마다 정적 스캔 + 회귀(싼 안전망).
- **pre-push**(`.githooks/pre-push`) — 푸시마다 property + effect + round-trip(런타임).
- 설치: `git config core.hooksPath .githooks` · 우회: `--no-verify`.

## 커버리지 수치 (audit_static_scan 말미 자동 출력)
정적 51항목 · 체크박스 플래그 복원 자동추출 60개 · 회귀 38×29 · property 불변식 45케이스
· effect 8토글(단발 7 + 캠페인 1) · round-trip 44토글 · 열린 사각 8건(위).
