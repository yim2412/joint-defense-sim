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

## 🔴 열린 사각 (메울 것)

1. **조합 커버리지 = 2^N 미검증** — `audit_property.py`가 토글을 40% 확률로 랜덤 조합해
   40+케이스 돌리므로 **표본 커버리지는 있으나** 모든 쌍(pairwise) 보장은 아니다. 특정
   토글 쌍의 상호작용 버그는 잠재.
2. **단조성 불변식 미구현** — 보존식(요격≤총·rate=요격/총)은 property에 도입했으나
   "적↑→요격률↓" 단조성은 **노이즈(시드 분산)로 신뢰도 낮아 보류**. 평균 다수 시드
   필요 → 비용 대비 가치 낮음.
3. **골든 오라클 자기참조** — 회귀는 "이전과 같은가"만. 골든 갱신 시 "왜 바뀌었나"는
   사람 판단이 유일 오라클. property 스위트가 독립 오라클로 보강하나 완전 대체 불가
   (오라클 문제는 원리적으로 미해결 — 관리 대상).
4. **GUI abort(중단) 실제 클릭 미자동화** — 전파는 헤드리스로 확인하나, MC 실행 중
   중단 버튼 클릭→워커 잔존 0 시나리오는 스모크에 없음(GUI 타이밍 난도).
5. **프리셋 편성 count ↔ 표기(changelog/주석) 정합** — 자유텍스트 파싱이라 자동화
   난도 높음(v16.05서 ARM 20 vs 표기 24 수동 발견). 미해소.
6. **비-enable_ 수치 키 전수 미점검** — 경계 5케이스(horizon 0/음수/거대·salvo 0·
   drone_swarm 999)는 property에 도입했으나, 수치 키 **전수** 자동 추출·경계 검사는 아직.

## ✅ 메운 사각 (이력)
- **효과 검증(죽은 토글)**(v17.01.10) → `audit_effect.py` — 효과 입증 시나리오에서 ON/OFF
  델타로 7종 효과 확인(전장전용·엣지케이스는 수동 목록 명시).
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
정적 33항목 · 체크박스 플래그 복원 자동추출 44/44 · 회귀 8×26 · property 불변식 45케이스
· effect 7토글 · round-trip 44토글 · 열린 사각 6건(위).
