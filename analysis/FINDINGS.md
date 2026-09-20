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
