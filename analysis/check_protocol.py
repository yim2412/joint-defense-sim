# -*- coding: utf-8 -*-
"""
analysis/check_protocol.py — 전면 분석 규약(00_PROTOCOL.md) 기계 검사기

왜 있나: 규약은 전부 '내가 스스로 지켜야 하는 것'이라, 판이 길어지면 조용히 샌다.
        근거 등급 누락·심각도 인플레·유령 커버리지를 사람 성실성이 아니라 도구로 막는다.

사용:
    python analysis/check_protocol.py              # 검사 (판 끝마다)
    python analysis/check_protocol.py --final      # 종합 판 전용 (우선순위 검사 포함)
    python analysis/check_protocol.py --selftest   # 검사기가 실제로 잡는지 확인

★ 이 스크립트는 분석 시작 '전에' 만들어 커밋했다.
  발견이 나온 뒤에 검사기를 느슨하게 고치지 않는다. 고쳐야 하면 이유를 커밋 메시지에.
"""
import argparse
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)

FINDINGS = "FINDINGS.md"
COVERAGE = "COVERAGE.md"

GRADES = ("[실측]", "[코드]", "[추정]", "[미확인]")
HIGH_SEV = ("치명", "높음")
VALID_SEV = ("치명", "높음", "중간", "낮음")
REQUIRED_FIELDS = ("위치", "근거", "이력", "심각도", "반증조건", "재현",
                   "수정비용", "회귀위험", "실행주체", "뿌리", "요약")
MAX_FINDINGS = 50

HEADER_RE = re.compile(r"^###\s+(F-\d+)\s*·\s*축:\s*(.+?)\s*·\s*상태:\s*(.+?)\s*$")
FIELD_RE = re.compile(r"^-\s*([^:]{1,20}):\s*(.*)$")
LOC_RE = re.compile(r"^(?P<path>[^\s:]+):(?P<line>\d+)(?:\s+`(?P<anchor>[^`]+)`)?")
FENCE_RE = re.compile(r"```")
EMPTY_REPRO = ("", "없음", "(없음)", "-", "—")


def _read(path):
    """읽기는 항상 utf-8-sig — 이 저장소엔 BOM 붙은 소스가 있다(app_main·engine_combat)."""
    with open(path, "r", encoding="utf-8-sig", errors="replace") as f:
        return f.read()


class Report(object):
    def __init__(self):
        self.fails = []
        self.warns = []
        self.notes = []

    def fail(self, check, msg):
        self.fails.append((check, msg))

    def warn(self, check, msg):
        self.warns.append((check, msg))

    def note(self, msg):
        self.notes.append(msg)

    def dump(self):
        for m in self.notes:
            print("       " + m)
        for c, m in self.warns:
            print("[WARN] %-22s %s" % (c, m))
        for c, m in self.fails:
            print("[FAIL] %-22s %s" % (c, m))
        print("-" * 72)
        if self.fails:
            print("[FAIL] 위반 %d건 · 경고 %d건 — 이 판은 끝난 게 아니다."
                  % (len(self.fails), len(self.warns)))
        else:
            print("[OK]   위반 0건 · 경고 %d건" % len(self.warns))
        return 1 if self.fails else 0


# ---------------------------------------------------------------- 파싱

def parse_findings(text):
    """### F-NNN 블록을 dict 목록으로. 형식은 00_PROTOCOL.md 3.2절 고정."""
    items, cur = [], None
    for lineno, raw in enumerate(text.splitlines(), 1):
        m = HEADER_RE.match(raw)
        if m:
            if cur:
                items.append(cur)
            cur = {"id": m.group(1), "axis": m.group(2), "state": m.group(3),
                   "lineno": lineno, "fields": {}, "body": []}
            continue
        if cur is None:
            continue
        cur["body"].append(raw)
        fm = FIELD_RE.match(raw)
        if fm:
            key = fm.group(1).strip()
            if key in REQUIRED_FIELDS or key in ("근거본문",) or key in B_FIELDS:
                cur["fields"][key] = fm.group(2).strip()
    if cur:
        items.append(cur)
    return items


# ---------------------------------------------------------------- 검사 1·2·3·7·8

def check_findings(items, rep):
    if len(items) > MAX_FINDINGS:
        rep.fail("3.1 대장 상한", "본문 항목 %d개 > %d개 — 묶거나 뿌리로 통합할 것"
                 % (len(items), MAX_FINDINGS))

    seen = set()
    for it in items:
        tag = "%s(L%d)" % (it["id"], it["lineno"])
        f = it["fields"]

        if it["id"] in seen:
            rep.fail("ID 중복", "%s 가 두 번 나온다" % it["id"])
        seen.add(it["id"])

        missing = [k for k in REQUIRED_FIELDS if k not in f]
        if missing:
            rep.fail("3.2 필수 항목", "%s 누락: %s" % (tag, ", ".join(missing)))

        # 1) 근거 등급
        grade = f.get("근거", "")
        if not any(g in grade for g in GRADES):
            rep.fail("1.1 근거 등급", "%s 근거 등급 없음 (%s 중 하나 필수)"
                     % (tag, "/".join(GRADES)))

        # 2) [실측]인데 명령·출력 블록이 없다
        if "[실측]" in grade:
            body = "\n".join(it["body"])
            if len(FENCE_RE.findall(body)) < 2:
                rep.fail("1.1 실측 증거", "%s [실측]인데 명령·출력 블록(```)이 없다 — "
                                          "요약해 옮기면 [추정]이다" % tag)

        # 3) 심각도 인플레
        sev = f.get("심각도", "").strip()
        if sev and sev not in VALID_SEV:
            rep.fail("3.4 심각도 값", "%s 알 수 없는 심각도 '%s'" % (tag, sev))
        if sev in HIGH_SEV:
            repro = f.get("재현", "").strip()
            if repro in EMPTY_REPRO:
                rep.fail("3.4 심각도 상한",
                         "%s 심각도 '%s' 인데 재현 근거 없음 — 재현 없으면 최대 '중간'"
                         % (tag, sev))
            elif "[실측]" not in grade:
                rep.warn("3.4 심각도 상한",
                         "%s 심각도 '%s' 인데 근거가 %s — 재현을 실측으로 올릴 것"
                         % (tag, sev, grade))
        if not f.get("반증조건", "").strip():
            rep.fail("3.4 반증조건", "%s 반증조건이 비었다 — "
                                     "'이 판단이 틀리려면 무엇이 참이어야 하는가'" % tag)

        # 8) 기각 사유
        state = it["state"]
        if state.startswith("기각") and not re.search(r"[(（].+[)）]", state):
            rep.fail("3.6 기각 사유", "%s 기각인데 사유가 없다 "
                                      "(의도적 단순화/비용대비/이미 음성/오탐)" % tag)


# ---------------------------------------------------------------- 검사 4

def check_locations(items, rep, repo=REPO):
    for it in items:
        loc = it["fields"].get("위치", "").strip()
        tag = "%s(L%d)" % (it["id"], it["lineno"])
        if not loc:
            continue
        m = LOC_RE.match(loc)
        if not m:
            rep.fail("1.2 인용 형식", "%s 위치 형식 불일치: %r "
                                      "(path:line `앵커`)" % (tag, loc))
            continue
        path, line = m.group("path"), int(m.group("line"))
        anchor = m.group("anchor")
        full = os.path.join(repo, path.replace("/", os.sep))
        if not os.path.isfile(full):
            rep.fail("1.2 인용 대상", "%s 파일 없음: %s" % (tag, path))
            continue
        lines = _read(full).splitlines()
        if not (1 <= line <= len(lines)):
            rep.fail("1.2 인용 라인", "%s %s 는 %d줄인데 :%d 를 가리킨다"
                     % (tag, path, len(lines), line))
            continue
        if anchor is None:
            rep.warn("1.2 앵커 누락", "%s 앵커 텍스트 없음 — 코드가 바뀌면 "
                                      "엉뚱한 곳을 가리킨다" % tag)
            continue
        if anchor.strip() not in lines[line - 1]:
            # 수정 중·수정된 항목은 그 줄을 '일부러 바꾼' 것이라 앵커가 안 맞는 게 정상이다.
            # FAIL 로 두면 B단계의 모든 수정이 커밋 불가가 된다(모의 실행 2026-09-20 발견).
            if it["state"].startswith(("수정중", "수정됨")):
                rep.warn("1.2 앵커 이동(수정중)",
                         "%s %s:%d — 고친 줄이라 앵커가 안 맞는다. 수정 완료 시 "
                         "위치·앵커를 새 코드로 갱신할 것" % (tag, path, line))
            else:
                rep.fail("1.2 앵커 불일치",
                         "%s %s:%d 에 앵커가 없다 (라인 이동됨 — 자동 갱신하지 말 것)"
                         % (tag, path, line))


# ---------------------------------------------------------------- 검사 5

def repo_files(repo=REPO):
    """git ls-files — quotepath=false + encoding 명시(전역 규칙: 자식 인코딩은 부모가 정한다)."""
    try:
        done = subprocess.run(
            ["git", "-c", "core.quotepath=false", "ls-files"],
            cwd=repo, capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
    except OSError as e:
        return None, "git 실행 실패: %s" % e
    if done.returncode != 0:
        return None, "git ls-files 실패: %s" % (done.stderr or "").strip()
    return set(p.strip() for p in (done.stdout or "").splitlines() if p.strip()), None


def check_coverage(cov_text, rep, repo=REPO):
    listed = set()
    for raw in cov_text.splitlines():
        m = re.match(r"^\|\s*`?([^`|]+?)`?\s*\|", raw)
        if not m:
            continue
        cand = m.group(1).strip()
        if cand in ("파일", "경로", "---") or set(cand) <= set("-: "):
            continue
        listed.add(cand.replace("\\", "/"))

    actual, err = repo_files(repo)
    if actual is None:
        rep.warn("7.1 커버리지", err)
        return
    actual = set(p for p in actual
                 if p.split("/")[0] not in ("analysis", "_archive", "변경이력", "감사보고서"))

    ghost = sorted(listed - actual)
    missing = sorted(actual - listed)
    if ghost:
        rep.fail("7.1 유령 항목", "커버리지에 있으나 저장소에 없는 파일 %d개: %s"
                 % (len(ghost), ", ".join(ghost[:5]) + (" …" if len(ghost) > 5 else "")))
    if missing:
        rep.warn("7.1 미등재", "저장소에 있으나 커버리지에 없는 파일 %d개: %s"
                 % (len(missing), ", ".join(missing[:5]) + (" …" if len(missing) > 5 else "")))
    rep.note("커버리지 등재 %d개 / 저장소 %d개" % (len(listed), len(actual)))


# ---------------------------------------------------------------- 검사 6

def check_priority(items, rep):
    """4.2 회피 경보 — 상위 5개가 전부 국소 수정이면 무서운 걸 피한 것이다.
    대장 순서를 우선순위로 본다(5단계 종합에서 정렬된 상태 전제)."""
    live = [it for it in items if not it["state"].startswith(("기각", "오탐"))]
    top = live[:5]
    if len(top) < 5:
        rep.note("살아 있는 발견 %d개 — 우선순위 검사 생략(5개 미만)" % len(top))
        return
    structural = [it["id"] for it in top if "뿌리" in it["fields"].get("뿌리", "")]
    if len(structural) < 2:
        rep.fail("4.2 회피 경보",
                 "상위 5개 중 구조적 항목 %d개 (<2) — 쉬운 것만 골랐는지 확인하고, "
                 "그게 맞다면 이유를 명시할 것" % len(structural))
    else:
        rep.note("상위 5개 중 구조적 %d개: %s" % (len(structural), ", ".join(structural)))


# ---------------------------------------------------------------- 실행

def run(final=False, base=HERE, repo=REPO, stage_b=False):
    rep = Report()
    fpath = os.path.join(base, FINDINGS)
    cpath = os.path.join(base, COVERAGE)

    print("=" * 72)
    print(" 전면 분석 규약 검사 — 00_PROTOCOL.md")
    print("=" * 72)

    if not os.path.isfile(fpath):
        if final:
            rep.fail("3. 대장 부재", "%s 가 없다 — 종합 판인데 발견 대장이 없을 수 없다" % FINDINGS)
        else:
            rep.note("%s 아직 없음 (분석 시작 전) — 발견 검사 생략" % FINDINGS)
        items = []
    else:
        items = parse_findings(_read(fpath))
        rep.note("발견 %d개 파싱" % len(items))
        check_findings(items, rep)
        check_locations(items, rep, repo)

    if os.path.isfile(cpath):
        check_coverage(_read(cpath), rep, repo)
    elif final:
        rep.fail("7.1 커버리지 부재", "%s 가 없다 — 어디까지 봤는지 알 수 없다" % COVERAGE)
    else:
        rep.note("%s 아직 없음 (0단계에서 생성)" % COVERAGE)

    if final:
        check_priority(items, rep)
    else:
        rep.note("우선순위 검사는 --final 에서만 (대장이 정렬된 뒤)")

    if stage_b:
        print("-" * 72)
        print(" B단계 검사 (9.10) — 착수 게이트·예측 형식·범위·영향 반경")
        # 이 검사기는 pre-commit 에 물려 있다. 검사기 자신의 예외가 traceback 으로
        # 터지면 저장소 전체 커밋이 막히고 원인도 안 보인다 — audit_static_scan 관례대로
        # 예외를 FAIL 로 흡수해 무엇이 터졌는지 보이게 한다(우회는 --no-verify).
        for fn in (check_stage_b_items, check_stage_b_diff):
            try:
                fn(items, rep, repo)
            except Exception as e:
                rep.fail("9.10 검사기 예외", "%s: %s" % (fn.__name__, e))

    return rep.dump()


# ---------------------------------------------------------------- 자기검증

SELFTEST_CASES = [
    ("근거 등급 누락", "1.1 근거 등급", """### F-901 · 축: 테스트 · 상태: 미처리
- 위치: analysis/check_protocol.py:1 `# -*- coding: utf-8 -*-`
- 근거: 그냥 봤음
- 이력: [신규]
- 심각도: 중간
- 반증조건: 없을 리 없다
- 재현: (없음)
- 수정비용: 소
- 회귀위험: 없음
- 실행주체: 나 단독
- 뿌리: 증상
- 요약: 근거 등급이 없는 항목
"""),
    ("재현 없는 높음", "3.4 심각도 상한", """### F-902 · 축: 테스트 · 상태: 미처리
- 위치: analysis/check_protocol.py:1 `# -*- coding: utf-8 -*-`
- 근거: [코드]
- 이력: [신규]
- 심각도: 높음
- 반증조건: 반증 조건
- 재현: (없음)
- 수정비용: 소
- 회귀위험: 없음
- 실행주체: 나 단독
- 뿌리: 증상
- 요약: 재현 없이 높음을 매긴 항목
"""),
    ("앵커 불일치", "1.2 앵커 불일치", """### F-903 · 축: 테스트 · 상태: 미처리
- 위치: analysis/check_protocol.py:1 `존재하지_않는_앵커_텍스트`
- 근거: [코드]
- 이력: [신규]
- 심각도: 중간
- 반증조건: 반증 조건
- 재현: (없음)
- 수정비용: 소
- 회귀위험: 없음
- 실행주체: 나 단독
- 뿌리: 증상
- 요약: 앵커가 그 줄에 없는 항목
"""),
    ("없는 파일 인용", "1.2 인용 대상", """### F-904 · 축: 테스트 · 상태: 미처리
- 위치: 없는파일_xyz.py:10 `무엇이든`
- 근거: [코드]
- 이력: [신규]
- 심각도: 중간
- 반증조건: 반증 조건
- 재현: (없음)
- 수정비용: 소
- 회귀위험: 없음
- 실행주체: 나 단독
- 뿌리: 증상
- 요약: 존재하지 않는 파일을 인용
"""),
    ("기각 사유 없음", "3.6 기각 사유", """### F-905 · 축: 테스트 · 상태: 기각
- 위치: analysis/check_protocol.py:1 `# -*- coding: utf-8 -*-`
- 근거: [코드]
- 이력: [신규]
- 심각도: 중간
- 반증조건: 반증 조건
- 재현: (없음)
- 수정비용: 소
- 회귀위험: 없음
- 실행주체: 나 단독
- 뿌리: 증상
- 요약: 사유 없이 기각
"""),
    ("실측인데 출력 없음", "1.1 실측 증거", """### F-906 · 축: 테스트 · 상태: 미처리
- 위치: analysis/check_protocol.py:1 `# -*- coding: utf-8 -*-`
- 근거: [실측]
- 이력: [신규]
- 심각도: 중간
- 반증조건: 반증 조건
- 재현: analysis/probes/p906.py
- 수정비용: 소
- 회귀위험: 없음
- 실행주체: 나 단독
- 뿌리: 증상
- 요약: 실측이라면서 명령·출력이 없다
"""),
    ("반증조건 공란", "3.4 반증조건", """### F-907 · 축: 테스트 · 상태: 미처리
- 위치: analysis/check_protocol.py:1 `# -*- coding: utf-8 -*-`
- 근거: [코드]
- 이력: [신규]
- 심각도: 중간
- 반증조건:
- 재현: (없음)
- 수정비용: 소
- 회귀위험: 없음
- 실행주체: 나 단독
- 뿌리: 증상
- 요약: 반증조건이 비었다
"""),
    ("필수 항목 누락", "3.2 필수 항목", """### F-908 · 축: 테스트 · 상태: 미처리
- 위치: analysis/check_protocol.py:1 `# -*- coding: utf-8 -*-`
- 근거: [코드]
- 요약: 나머지 항목이 통째로 없다
"""),
]


def selftest():
    """일부러 위반한 가짜 항목을 넣어 검사기가 잡는지 확인한다. 통과는 증거가 아니다."""
    print("=" * 72)
    print(" 검사기 자기검증 — 일부러 깨뜨려 잡히는지 본다")
    print("=" * 72)
    ok = True

    for name, expect, block in SELFTEST_CASES:
        rep = Report()
        items = parse_findings(block)
        if not items:
            print("[FAIL] %-18s 파싱 자체가 안 됨" % name)
            ok = False
            continue
        check_findings(items, rep)
        check_locations(items, rep, REPO)
        hit = [c for c, _ in rep.fails if c == expect]
        if hit:
            print("[OK]   %-18s -> %s 로 잡음" % (name, expect))
        else:
            got = ", ".join(sorted(set(c for c, _ in rep.fails))) or "(위반 0건)"
            print("[FAIL] %-18s -> '%s' 를 못 잡음. 잡은 것: %s" % (name, expect, got))
            ok = False

    # 정상 항목은 통과해야 한다 (오탐 검사)
    clean = SELFTEST_CASES[1][2].replace("심각도: 높음", "심각도: 중간")
    rep = Report()
    items = parse_findings(clean)
    check_findings(items, rep)
    check_locations(items, rep, REPO)
    if rep.fails:
        print("[FAIL] %-18s -> 정상 항목인데 위반 발생: %s"
              % ("오탐 검사", ", ".join(c for c, _ in rep.fails)))
        ok = False
    else:
        print("[OK]   %-18s -> 정상 항목은 통과" % "오탐 검사")

    # 대장 상한
    rep = Report()
    check_findings([dict(id="F-%03d" % i, axis="t", state="미처리", lineno=i,
                         fields=dict((k, "x") for k in REQUIRED_FIELDS), body=[])
                    for i in range(MAX_FINDINGS + 1)], rep)
    if any(c == "3.1 대장 상한" for c, _ in rep.fails):
        print("[OK]   %-18s -> 3.1 대장 상한 으로 잡음" % "대장 51개")
    else:
        print("[FAIL] %-18s -> 상한 초과를 못 잡음" % "대장 51개")
        ok = False

    # 유령 커버리지
    rep = Report()
    with tempfile.TemporaryDirectory() as td:
        check_coverage("| 파일 | 상태 |\n|---|---|\n| `유령파일_zzz.py` | 안봄 |\n", rep, REPO)
    if any(c == "7.1 유령 항목" for c, _ in rep.fails):
        print("[OK]   %-18s -> 7.1 유령 항목 으로 잡음" % "유령 커버리지")
    else:
        print("[FAIL] %-18s -> 유령 항목을 못 잡음" % "유령 커버리지")
        ok = False

    print("-" * 72)
    print(" B단계 검사 자기검증 (9.10)")
    if not selftest_b():
        ok = False

    print("-" * 72)
    print(" 절차 전체 모의 실행 (묶음 하나를 끝까지)")
    if not selftest_lifecycle():
        ok = False

    print("-" * 72)
    print("[OK]   자기검증 전부 통과" if ok else "[FAIL] 자기검증 실패 — 검사기를 믿을 수 없다")
    return 0 if ok else 1


# ---------------------------------------------------------------- B단계 (9절)
# 왜 여기 있나: B(수정 단계)의 규칙도 전부 '내가 스스로 지켜야 하는 것'이다.
# 특히 범위 확대(9.3)와 "회귀 PASS면 안 깨졌겠지"(9.4)는 문서 규칙으로 안 막힌다.
# A와 같은 원칙으로 B 작업을 시작하기 전에 만들어 커밋했다.

RADIUS_TABLE = [
    (r"^analysis/.*$", "T"),
    (r"^\.githooks/.*$", "D"),
    (r"^변경이력/.*$", "D"),
    (r"^감사보고서/.*$", "D"),
    (r"^_archive/.*$", "D"),
    (r"^engine_(core|combat)\.py$", "E"),
    # 엔진이 직접 import 하는 데이터 모듈 — 바꾸면 교전 결과가 바뀐다(회귀 필수).
    # engine_combat -> db_terrain / engine_campaign -> forecast_features 실측 확인.
    (r"^db_(terrain|ocean_\w+|ground_threat)\.py$", "E"),
    (r"^forecast_features\.py$", "C"),
    (r"^ai_policy_infer\.py$", "W"),          # app_workers 가 런타임에 import
    (r"^engine_(campaign|airforce|army|joint)\.py$", "C"),
    (r"^(app_workers|mixin_simlifecycle)\.py$", "W"),
    (r"^app_utils\.py$", "UB"),          # 리소스 경로(_res)가 있어 번들 반경도 걸린다
    (r"^(ui_.*|mixin_.*|app_main|app_launcher|app_theme|app_engine)\.py$", "U"),
    (r"^(audit_|_audit_|_build_|_bg_|_changelog_|_asset_|improve_|check_).*\.py$", "T"),
    (r"^(_ai_|ai_|asset_|_forecast_).*\.py$", "T"),   # 학습·생성 도구(런타임 아님)
    (r"^.*\.(sh|bat|cmd|html)$", "T"),
    (r"^(assets|images)/.*$", "B"),
    (r"^(docs|변경이력|감사보고서|_archive)/.*$", "D"),
    (r"^.*\.pdf$", "D"),
    (r"^(scenarios|db_specsheet)\.py$", "D"),
    (r"^.*\.spec$", "B"),
    (r"^.*\.(jpg|jpeg|png|ico|pkl|npz|ttf|otf|zip)$", "B"),
    (r"^.*\.(md|json|txt|csv|cfg|toml|yml|yaml)$", "D"),
    (r"^(LICENSE|\.gitignore|\.gitattributes)$", "D"),
]
RADIUS_NAME = {"E": "엔진", "C": "작전급", "W": "워커·수명주기", "U": "UI·렌더",
               "B": "빌드·번들·리소스", "T": "도구·감사", "D": "문서·데이터"}
RADIUS_EXTRA = {
    "E": "훅: 회귀·property·effect / 추가: R형식이면 ON/OFF MC 델타",
    "C": "훅: 회귀(캠페인 6케이스)·property / 추가: _audit_campaign_smoke.py",
    "W": "훅: roundtrip / 추가: GUI 스모크 — 실제 버튼 클릭(엔진 직접 호출 우회 금지)",
    "U": "훅: roundtrip·UI shot·render smoke / 추가: 없음",
    "B": "훅: 정적(chk_resource_paths) / 추가: 전체 빌드 + exe 스모크",
    "T": "훅: 없음 / 추가: 일부러 깨뜨려 FAIL 나는지 확인 — 통과는 증거가 아니다",
    "D": "훅: 정적 / 추가: changelog가 바뀌었으면 _changelog_export.py 재실행",
}
B_FIELDS = ("대상", "예측", "결과", "짝", "무대")
MAX_BATCH_FILES = 3
MAX_BATCH_LINES = 200
LEDGER_PREFIX = "analysis/"          # 대장 자신은 범위 선언 대상이 아니다

DIRECTION_RE = re.compile(r"(↑|↓|오른|내린|증가|감소|늘|줄|상승|하락|빨라|느려)")
MAGNITUDE_RE = re.compile(r"[+\-±]?\d*[1-9]\d*(?:\.\d+)?|0\.\d*[1-9]\d*")
MAG_UNIT_RE = re.compile(r"\d(?:\.\d+)?\s*(?:%p|%|배|발|척|초|s|ms|km|점|회)")
# '최소 0%p' 는 예측이 아니다 — 무엇이 나와도 맞는다. 0이 아닌 크기를 요구한다.
NONZERO_MAG_RE = re.compile(r"(?<![\d.])(?:[1-9]\d*|0?\.\d*[1-9])(?:\.\d+)?\s*(?:%p|%|배|발|척|초|s|ms|km|점)")
# 'MC 200회' 의 200을 효과 크기로 오인했다 — 표본수 단위(회)는 크기가 아니다.
ZERO_MAG_RE = re.compile(r"최소\s*[+\-±]?0(?![.\d])|최소\s*0\.0+(?![1-9])")
# 판정 가능성: 고정 seed 결정론 대조이거나, 확률 경로면 표본수+산포를 적어야 한다.
DECIDABLE_RE = re.compile(r"(seed|시드|결정론|bit-identical|±\s*\d|표준편차|산포)")
SCENARIO_RE = re.compile(r"(시나리오|MC\s*\d+|케이스|프리셋|캠페인|기준|골든)")
URL_RE = re.compile(r"https?://\S+")
VERDICT_RE = re.compile(r"(부합|불일치|빗나감|어긋)")
PROBE_RE = re.compile(r"probes/\S+\.py")
STATIC_RE = re.compile(r"(chk_\w+|audit_\w+)")


def classify_radius(paths):
    """파일 경로 -> 영향 반경. 미분류는 FAIL 재료로 돌려준다(기본 안전)."""
    hit, unknown = {}, []
    for p in paths:
        base = p.replace("\\", "/")
        letters = ""
        for pat, r in RADIUS_TABLE:
            if re.match(pat, base) or re.match(pat, os.path.basename(base)):
                letters = r
                break
        if not letters:
            unknown.append(base)
            continue
        for ch in letters:
            hit.setdefault(ch, []).append(base)
    return hit, unknown


def _git(repo, *args):
    """CLAUDE.md 인코딩 규칙: capture_output 에는 반드시 encoding= 을 준다."""
    try:
        # core.quotepath=false — 안 주면 한글 파일명이 "ë³…" octal 로 나와
        # 반경 분류·선언 대조가 조용히 어긋난다(이 저장소엔 한글 경로가 많다).
        out = subprocess.run(["git", "-c", "core.quotepath=false"] + list(args),
                             cwd=repo, capture_output=True,
                             encoding="utf-8", errors="replace")
    except OSError:
        return None
    return out.stdout if out.returncode == 0 else None


def changed_files(repo):
    out = _git(repo, "status", "--porcelain")
    if out is None:
        return None
    files = []
    for ln in out.splitlines():
        p = ln[3:].strip()
        if " -> " in p:
            p = p.split(" -> ")[-1]
        p = p.strip().strip('"')
        if p:
            files.append(p)
    return files


def is_code(path):
    """라인 상한(9.1)이 걸리는 대상인가.
    analysis/ 산출물과 .md 문서는 제외한다 — 분석 판의 산출물이고 회귀 위험이 다르다.
    도구(audit_*)는 제외하지 않는다. 그것도 고치면 깨질 수 있는 코드다."""
    q = path.replace(chr(92), "/")
    # 생성 데이터는 제외한다. 골든은 케이스 수에 비례해 커질 뿐이고, 상한의 취지는
    # **코드 변경의 원인 분리**다 — 케이스 6개를 추가하면 JSON 이 200줄을 넘어
    # 정당한 묶음이 막힌다(2026-09-20 F-011 잔여에서 221줄로 실제로 막혔다).
    if q.endswith("audit_regression_golden.json"):
        return False
    return not q.startswith(LEDGER_PREFIX) and not q.endswith(".md")


def changed_lines(repo):
    """코드 파일의 추가+삭제 라인 합. 문서·대장은 세지 않는다."""
    tot = 0
    for args in (("diff", "--numstat"), ("diff", "--cached", "--numstat")):
        for ln in (_git(repo, *args) or "").splitlines():
            parts = ln.split(chr(9))
            if len(parts) >= 3 and is_code(parts[2]):
                for n in parts[:2]:
                    if n.isdigit():
                        tot += int(n)
    return tot


def _probe_exists(repo, repro):
    """P: 프로브 파일이 실제로 있는가. 경로만 적어 두고 안 만드는 것을 막는다."""
    m = PROBE_RE.search(repro)
    if not m:
        return None
    rel = m.group(0)
    for cand in (os.path.join(repo, rel), os.path.join(repo, "analysis", rel)):
        if os.path.isfile(cand):
            return True
    return False


def _static_check_exists(repo, repro):
    """S: chk_xxx 가 감사 도구에 실제로 정의돼 있는가.
    'chk_추후에만들것' 처럼 문자열만 적어 통과시키는 것을 막는다."""
    names = set(re.findall(r"chk_\w+", repro))
    if not names:
        return None
    defined = set()
    for f in os.listdir(repo):
        if f.startswith("audit_") and f.endswith(".py"):
            try:
                defined |= set(re.findall(r"^def (chk_\w+)", _read(os.path.join(repo, f)), re.M))
            except OSError:
                pass
    return bool(names & defined)


def _git_ok(repo, *args):
    try:
        r = subprocess.run(["git"] + list(args), cwd=repo, capture_output=True,
                           encoding="utf-8", errors="replace")
    except OSError:
        return None
    return r.returncode == 0


def _batch_code_commits(repo, fid):
    """이 발견의 묶음 커밋 = 메시지에 발견 ID가 들어가고 코드를 건드린 커밋(9.8).
    대상 파일의 '전체 과거 이력'과 비교하면 파일 생성 커밋까지 걸려 오탐이 난다
    (모의 실행 2026-09-20에서 규약을 정확히 지켰는데 FAIL 났다)."""
    out = _git(repo, "log", "--format=%H", "--grep", fid) or ""
    hits = []
    for sha in out.split():
        files = _git(repo, "show", "--name-only", "--format=", sha) or ""
        if any(is_code(x) for x in files.split()):
            hits.append(sha)
    return hits


def _declared_before_code(repo, text, targets=(), fid=None):
    """R/9.3: 예측·선언이 코드보다 먼저 들어갔는가.
    그 문자열이 처음 들어간 커밋이 코드 파일을 건드렸으면 사후 작성이다."""
    if not text.strip():
        return None
    out = _git(repo, "log", "--format=%H", "-S", text.strip()[:80], "--", "analysis/" + FINDINGS)
    if not out or not out.strip():
        return None                      # 아직 커밋 안 됨 — 판정 보류
    sha = out.strip().splitlines()[-1]   # 가장 오래된 = 도입 커밋
    files = _git(repo, "show", "--name-only", "--format=", sha) or ""
    touched = [p for p in files.split() if is_code(p)]
    if touched:
        return (False, sha, touched)
    # 도입 커밋에 코드가 없어도, 그게 '이 묶음의 코드 커밋' 뒤면 사후 작성이다.
    for code_sha in (_batch_code_commits(repo, fid) if fid else []):
        if code_sha == sha:
            continue
        if _git_ok(repo, "merge-base", "--is-ancestor", sha, code_sha) is False:
            return (False, sha, ["묶음 코드 커밋 %s 뒤에 끼워넣음" % code_sha[:7]])
    return (True, sha, [])


def check_stage_b_items(items, rep, repo=REPO):
    """9.10 검사 1~4 + 짝·무대·판정 실재·선행성."""
    for it in items:
        if not it["state"].startswith(("수정중", "수정됨")):
            continue
        tag = "%s(L%d)" % (it["id"], it["lineno"])
        f = it["fields"]
        body = "\n".join(it["body"])
        repro = f.get("재현", "")
        has_p = bool(PROBE_RE.search(repro))
        has_s = bool(re.search(r"chk_\w+", repro))
        has_r = "예측" in f

        if not (has_p or has_s or has_r):
            rep.fail("9.2 착수 게이트",
                     "%s 상태가 '%s' 인데 P/S/R 판정이 없다 — 재현:에 프로브 경로(P)나 "
                     "검사함수(S), 아니면 예측: 줄(R)이 있어야 한다" % (tag, it["state"]))

        # 판정이 실재하는가 (경로·함수명만 적어 두는 것 차단)
        if has_p and _probe_exists(repo, repro) is False:
            rep.fail("9.2 판정 실재", "%s 재현: 프로브 파일이 없다 — 경로만 적어 둔 것"
                     % tag)
        if has_s and _static_check_exists(repo, repro) is False:
            rep.fail("9.2 판정 실재",
                     "%s 재현: 의 chk_ 함수가 감사 도구에 정의돼 있지 않다 — "
                     "검사 함수를 먼저 만들고 FAIL 나는 것을 확인할 것" % tag)

        # 짝 — be4e8b9(분모만 고쳐 지표가 더 거짓말)·v20.5(레이더 침묵) 부류
        if "짝" not in f or not f.get("짝", "").strip():
            rep.fail("9.2 짝 선언",
                     "%s 에 짝: 이 없다 — 이 수정이 성립하려면 무엇이 함께 참이어야/바뀌어야 "
                     "하는가. 한쪽만 고치는 게 안 고치는 것보다 나쁠 수 있다" % tag)
        stage = f.get("무대", "")
        if stage.strip() and not re.search(r"\d", stage):
            rep.warn("9.2 무대 구체성",
                     "%s 무대에 수치(거리·규모·시간)가 없다 — '적정 편성' 같은 서술은 "
                     "발동 조건을 특정하지 못한다" % tag)
        # 무대 — 레이저(v17.2) 부류: 메커니즘은 맞는데 발동 조건이 안 만들어짐
        if "무대" not in f or not f.get("무대", "").strip():
            rep.fail("9.2 무대 선언",
                     "%s 에 무대: 가 없다 — 어떤 편성·거리·조건에서 발동하는가. "
                     "무대가 없으면 고쳐도 아무 데서도 안 나타난다" % tag)

        if has_r:
            pred = f.get("예측", "")
            miss = []
            if len(pred.split()) < 3:
                miss.append("지표명")
            if not DIRECTION_RE.search(pred):
                miss.append("방향")
            if ZERO_MAG_RE.search(pred) or not NONZERO_MAG_RE.search(pred):
                miss.append("0이 아닌 최소 크기")
            if not SCENARIO_RE.search(pred):
                miss.append("측정 시나리오")
            if miss:
                rep.fail("9.2 R 예측 형식",
                         "%s 예측에 %s 누락 — '요격률이 변한다'·'최소 0%%p' 류는 무엇이 "
                         "나와도 맞는 문장이라 판정이 아니다" % (tag, "·".join(miss)))
            if not DECIDABLE_RE.search(pred):
                rep.fail("9.2 R 판정 가능성",
                         "%s 예측이 노이즈와 구분되지 않는다 — 고정 seed 결정론 대조이거나, "
                         "확률 경로면 표본수와 산포(±)를 적을 것. 기준 시나리오 요격률의 "
                         "시드 산포는 ±4.0%%p 다(project-baseline-v11)" % tag)
            if not URL_RE.search(body):
                rep.fail("9.2 R 외부 앵커",
                         "%s 예측이 있는데 출처 URL이 없다 — 못 달면 [미확인]으로 두고 "
                         "고치지 않는다(4.4 결정 요청)" % tag)
            targets = [t.strip() for t in re.split(r"[,\s]+", f.get("대상", "")) if t.strip()]
            pre = _declared_before_code(repo, pred, targets, it["id"])
            if pre is not None and pre[0] is False:
                rep.fail("9.2 R 선행성",
                         "%s 예측이 코드와 같은 커밋(%s)에 들어갔다 — 예측은 코드를 "
                         "건드리기 전에 문서만 커밋해야 사후 조작이 막힌다 (코드: %s)"
                         % (tag, pre[1][:7], ", ".join(pre[2][:3])))

        if it["state"].startswith("수정됨"):
            res = f.get("결과", "")
            if not res:
                rep.fail("9.2 R 결과", "%s 가 '수정됨' 인데 결과: 가 없다" % tag)
            elif has_r and not VERDICT_RE.search(res):
                rep.fail("9.2 R 결과",
                         "%s 결과에 부합/불일치 판정이 없다 — 어긋난 것도 결과다" % tag)



def check_stage_b_diff(items, rep, repo=REPO):
    """9.10 검사 5~6 — 워킹트리 diff 를 선언·반경 표와 대조."""
    ch = changed_files(repo)
    if ch is None:
        rep.note("git 을 못 읽음 — 9.3/9.4 diff 검사 생략 [미확인]")
        return
    code = [p for p in ch if is_code(p)]
    if not ch:
        rep.note("워킹트리 변경 0건 — 9.3 범위·9.4 반경 검사 생략")
        return

    hit, unknown = classify_radius(ch)
    if unknown:
        rep.fail("9.4 반경 미분류",
                 "반경 표에 없는 파일 %d개: %s — 분류를 추가할 것(미분류는 사각이므로 FAIL)"
                 % (len(unknown), ", ".join(unknown[:5])))
    if hit:
        rep.note("영향 반경: " + " · ".join("%s(%s)" % (k, RADIUS_NAME[k]) for k in sorted(hit)))
        for k in sorted(hit):
            rep.note("   %s -> %s" % (k, RADIUS_EXTRA[k]))

    tracked = (_git(repo, "ls-files") or "").splitlines()
    if tracked:
        _, unk_all = classify_radius(tracked)
        if unk_all:
            rep.warn("9.4 반경 표 커버리지",
                     "저장소 %d개 중 %d개가 반경 미분류 — 표가 낡고 있다(예: %s)"
                     % (len(tracked), len(unk_all), ", ".join(unk_all[:3])))
        else:
            rep.note("반경 표가 추적 파일 %d개를 전부 분류" % len(tracked))

    declared = set()
    for it in items:
        # 9.1: 묶음 커밋은 '코드 + 대장 상태·결과' 를 함께 담는다. 그 커밋 시점엔 상태가
        # 이미 '수정됨' 이므로 '수정중' 만 선언으로 인정하면 **규약대로 닫는 순간 FAIL**
        # 이 난다(2026-09-20 F-009 실작업에서 드러남 — 5라운드 리허설은 코드를 먼저
        # 커밋하고 상태를 나중에 바꿔서 이 자리를 안 지났다).
        if it["state"].startswith(("수정중", "수정됨")):
            for p in re.split(r"[,\s]+", it["fields"].get("대상", "")):
                if p.strip():
                    declared.add(p.strip().replace("\\", "/"))
    if declared:
        # 9.1 상한은 **묶음(항목) 하나**에 대한 것이다. 여러 항목의 대상을 합쳐서 재면
        # 이미 닫힌 묶음이 다음 묶음의 예산을 잡아먹는다(2026-09-20 F-011 착수에서 드러남:
        # 닫힌 F-009 3파일 + 새 F-011 2파일 = 5로 FAIL). 항목별로 잰다.
        for it in items:
            if not it["state"].startswith(("수정중", "수정됨")):
                continue
            own = {t.strip().replace("\\", "/")
                   for t in re.split(r"[,\s]+", it["fields"].get("대상", "")) if t.strip()}
            own = {t for t in own if "/" in t or t.endswith((".py", ".json", ".spec", ".md"))}
            if len(own) > MAX_BATCH_FILES:
                rep.fail("9.1 묶음 상한", "%s 대상 %d개 파일 > %d개 — 묶음을 쪼갤 것"
                         % (it["id"], len(own), MAX_BATCH_FILES))
        extra = [p for p in code if p not in declared]
        if extra:
            rep.fail("9.3 범위 확대",
                     "선언(대상:)에 없는 파일이 바뀌었다: %s — 넓히려면 선언을 고쳐 "
                     "커밋할 것(조용한 확대 금지)" % ", ".join(extra[:5]))
    elif code:
        # B판 밖(대장 자체가 없음)이면 규약이 적용되지 않는다 — 평소 패치를 막지 않는다.
        if not items:
            rep.note("FINDINGS.md 없음 — B판 밖이므로 9.3 착수 선언 검사 생략")
        else:
            chit, _ = classify_radius(code)
            hard = [k for k in chit if k in ("E", "C", "W", "U", "B")]
            msg = ("코드 변경 %d개 파일이 있는데 '수정중' 항목의 대상: 선언이 없다 — "
                   "규약 밖에서 고치는 중" % len(code))
            if hard:
                rep.fail("9.3 착수 선언", msg + " (반경 %s)" % ",".join(sorted(hard)))
            else:
                rep.warn("9.3 착수 선언", msg + " (도구·문서 반경)")

    n = changed_lines(repo)
    if n > MAX_BATCH_LINES:
        rep.fail("9.1 묶음 상한",
                 "변경 %d라인 > %d라인 — 실패 시 원인 분리가 안 된다. 쪼갤 것"
                 % (n, MAX_BATCH_LINES))
    else:
        rep.note("코드 변경 %d라인 (상한 %d · analysis/·*.md 제외)"
                 % (n, MAX_BATCH_LINES))


def selftest_b():
    """B 검사도 일부러 깨뜨려 본다. 통과는 증거가 아니다.
    케이스는 전부 '적대적 테스트에서 실제로 뚫렸던 것' 이다(2026-09-20 실측)."""
    ok = True
    OKF = "- 짝: 없음(단독 성립)\n- 무대: 기준 시나리오 포화 편성 20~40km\n"
    cases = [
        ("판정 없음", "9.2 착수 게이트",
         "### F-901 · 축: 모델 · 상태: 수정중\n" + OKF + "- 재현: (없음)\n"),
        ("느슨한 예측", "9.2 R 예측 형식",
         "### F-902 · 축: 모델 · 상태: 수정중\n" + OKF +
         "- 예측: 요격률이 변한다\n- 근거본문: https://e.org/x\n"),
        ("최소 0%p (표본수 오인)", "9.2 R 예측 형식",
         "### F-903 · 축: 모델 · 상태: 수정중\n" + OKF +
         "- 예측: 기준 시나리오 MC 200회 요격률이 오른다, 최소 0%p (고정 seed)\n"
         "- 근거본문: https://e.org/x\n"),
        ("노이즈와 구분 불가", "9.2 R 판정 가능성",
         "### F-904 · 축: 모델 · 상태: 수정중\n" + OKF +
         "- 예측: 기준 시나리오 MC 200회 요격률이 오른다, 최소 2%p\n"
         "- 근거본문: https://e.org/x\n"),
        ("외부 앵커 없음", "9.2 R 외부 앵커",
         "### F-905 · 축: 모델 · 상태: 수정중\n" + OKF +
         "- 예측: 기준 시나리오 고정 seed 요격률이 오른다, 최소 5%p\n"),
        ("가짜 chk_ 문자열", "9.2 판정 실재",
         "### F-906 · 축: 구조 · 상태: 수정중\n" + OKF + "- 재현: chk_추후에만들것\n"),
        ("없는 프로브 경로", "9.2 판정 실재",
         "### F-907 · 축: 구조 · 상태: 수정중\n" + OKF +
         "- 재현: analysis/probes/p907_없는파일.py\n"),
        ("짝 미선언", "9.2 짝 선언",
         "### F-908 · 축: 모델 · 상태: 수정중\n"
         "- 무대: 기준 시나리오 20km\n- 재현: chk_version\n"),
        ("무대 미선언", "9.2 무대 선언",
         "### F-909 · 축: 모델 · 상태: 수정중\n"
         "- 짝: 회피 기동 ON 필요\n- 재현: chk_version\n"),
        ("결과 없음", "9.2 R 결과",
         "### F-910 · 축: 구조 · 상태: 수정됨\n" + OKF + "- 재현: chk_version\n"),
    ]
    for name, expect, block in cases:
        rep = Report()
        check_stage_b_items(parse_findings(block), rep)
        if any(c == expect for c, _ in rep.fails):
            print("[OK]   %-20s -> %s 로 잡음" % (name, expect))
        else:
            got = ", ".join(sorted(set(c for c, _ in rep.fails))) or "(위반 0건)"
            print("[FAIL] %-20s -> '%s' 를 못 잡음. 잡은 것: %s" % (name, expect, got))
            ok = False

    # 정상 항목은 통과해야 한다 (오탐 검사) — S형식과 R형식 각각
    good_s = ("### F-920 · 축: 구조 · 상태: 수정중\n" + OKF +
              "- 재현: chk_global_name_import\n")
    good_r = ("### F-921 · 축: 모델 · 상태: 수정됨\n"
              "- 짝: 회피 기동(enable_ship_evasion) ON 이어야 발현\n"
              "- 무대: 드론 없는 포화 편성, 20~40km\n"
              "- 예측: 기준 시나리오 고정 seed 단발 요격률이 오른다, 최소 3%p\n"
              "- 결과: 11.5% -> 15.2% (+3.7%p) — 예측 부합\n"
              "- 근거본문: 출처 https://www.navy.mil/example\n")
    for nm, blk in (("S 오탐 검사", good_s), ("R 오탐 검사", good_r)):
        rep = Report()
        check_stage_b_items(parse_findings(blk), rep)
        if rep.fails:
            print("[FAIL] %-20s -> 정상 항목인데 위반: %s"
                  % (nm, ", ".join(c for c, _ in rep.fails)))
            ok = False
        else:
            print("[OK]   %-20s -> 정상 항목은 통과" % nm)

    # 반경 분류: 알려진 파일은 분류되고, 낯선 파일은 미분류로 걸려야 한다
    hit, unknown = classify_radius(["engine_combat.py", "ui_charts.py", "app_main.spec",
                                    "analysis/FINDINGS.md", "낯선파일_zzz.xyz"])
    if set(hit) == {"E", "U", "B", "T"} and unknown == ["낯선파일_zzz.xyz"]:
        print("[OK]   %-20s -> 분류 %s · 미분류 %s" % ("반경 분류", sorted(hit), unknown))
    else:
        print("[FAIL] %-20s -> 분류 %s · 미분류 %s (기대와 다름)"
              % ("반경 분류", sorted(hit), unknown))
        ok = False

    # 선언 없는 코드 변경은 B판 안에서 FAIL, B판 밖(대장 없음)에선 생략
    rep = Report()
    check_stage_b_diff([], rep)
    if any(c == "9.3 착수 선언" for c, _ in rep.fails):
        print("[FAIL] %-20s -> B판 밖인데 착수 선언을 요구했다" % "B판 밖 생략")
        ok = False
    else:
        print("[OK]   %-20s -> B판 밖에서는 평소 패치를 막지 않는다" % "B판 밖 생략")
    return ok



_REHEARSAL_ENTRY = """### F-001 · 축: 모델타당성 · 상태: {state}
- 위치: engine_core.py:1 `PK_BASE = {anchor}`
- 근거: [코드]
- 이력: [신규]
- 심각도: 중간
- 반증조건: 공개 제원이 그 값을 지지하면 틀린 판단이다
- 재현: (없음)
- 수정비용: 소
- 회귀위험: 골든 영향 있음
- 실행주체: 나 단독
- 뿌리: 증상
- 대상: engine_core.py
- 짝: 없음(단독 성립 — 소비처는 pk() 뿐)
- 무대: 기준 시나리오 20~40km 교전
- 예측: 기준 시나리오 고정 seed pk 값이 내린다, 최소 0.1점
{result}- 요약: PK_BASE 가 공개 제원보다 높다
- 근거본문: 출처 https://www.navy.mil/example-spec
"""


def selftest_lifecycle():
    """B 묶음 하나를 규약대로 **끝까지** 돌려 본다 — 부품 테스트로는 안 나오는 것 전용.

    2026-09-20 모의 실행에서 치명 오탐 2건이 여기서 나왔다:
    (a) 선행성 검사가 대상 파일의 전체 과거 이력과 비교해, 규약을 지켜도 FAIL
    (b) 고친 줄의 앵커 불일치가 FAIL 이라 B단계의 모든 수정이 커밋 불가
    둘 다 '성실히 따르는 사람만 만나는 오탐' 이라, 실전이면 --no-verify 로 이어져
    규약 전체가 무력화된다. 그래서 절차 전체를 자동 검사로 박아 둔다.
    """
    import shutil

    def g(cwd, *a):
        subprocess.run(["git"] + list(a), cwd=cwd, capture_output=True,
                       encoding="utf-8", errors="replace")

    def fails(base):
        rep = Report()
        items = parse_findings(_read(os.path.join(base, "analysis", FINDINGS)))
        # A쪽(3.2 필수 필드·3.4 심각도)도 함께 본다 — A와 B의 접합부 점검.
        # 이게 빠져 있어서 'B는 통과하는데 A가 거부하는 항목'을 검사할 방법이 없었다.
        check_findings(items, rep)
        check_locations(items, rep, base)
        check_stage_b_items(items, rep, base)
        check_stage_b_diff(items, rep, base)
        return sorted(set(c for c, _ in rep.fails))

    ok = True
    td = tempfile.mkdtemp(prefix="proto_rehearse_")
    try:
        os.makedirs(os.path.join(td, "analysis", "probes"))
        shutil.copy(os.path.join(HERE, "check_protocol.py"), os.path.join(td, "analysis"))
        w = lambda n, t: io_write(os.path.join(td, n), t)
        w("engine_core.py", "PK_BASE = 0.7\n\ndef pk(x):\n    return PK_BASE * x\n")
        w("audit_static_scan.py", "def chk_dummy():\n    pass\n")
        g(td, "init", "-q", ".")
        g(td, "config", "user.email", "t@t")
        g(td, "config", "user.name", "t")
        g(td, "add", "-A")
        g(td, "commit", "-qm", "base")

        # ① 선언 커밋(문서만) — 위반 0건이어야 한다
        w("analysis/" + FINDINGS, _REHEARSAL_ENTRY.format(state="수정중", anchor="0.7", result=""))
        g(td, "add", "-A")
        g(td, "commit", "-qm", "F-001 착수 선언 (문서만)")
        f1 = fails(td)
        ok &= _expect("① 선언 커밋", not f1, f1)

        # ② 코드 수정 — 앵커는 경고여야 하고 FAIL 은 없어야 한다
        w("engine_core.py", "PK_BASE = 0.55\n\ndef pk(x):\n    return PK_BASE * x\n")
        f2 = fails(td)
        ok &= _expect("② 코드 수정", not f2, f2)
        g(td, "add", "-A")
        g(td, "commit", "-qm", "분석 F-001: PK_BASE 를 공개 제원에 맞춤")

        # ③ 결과 기입 + 앵커 갱신
        w("analysis/" + FINDINGS, _REHEARSAL_ENTRY.format(
            state="수정됨", anchor="0.55",
            result="- 결과: pk(1.0) 0.70 -> 0.55 (-0.15점) — 예측 부합\n"))
        f3 = fails(td)
        ok &= _expect("③ 결과 기입", not f3, f3)

        # ④ 예측을 사후에 고쳐 쓰면 여전히 걸려야 한다
        g(td, "add", "-A")
        g(td, "commit", "-qm", "결과 기입 (문서만)")
        w("analysis/" + FINDINGS, _read(os.path.join(td, "analysis", FINDINGS))
          .replace("최소 0.1점", "최소 0.4점"))
        g(td, "add", "-A")
        g(td, "commit", "-qm", "예측 살짝 수정 (문서만)")
        f4 = fails(td)
        ok &= _expect("④ 사후 조작 차단", "9.2 R 선행성" in f4, f4)
    finally:
        shutil.rmtree(td, ignore_errors=True)
    return ok


def io_write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def _expect(name, cond, got):
    if cond:
        print("[OK]   %-20s -> 기대대로" % name)
        return True
    print("[FAIL] %-20s -> 위반: %s" % (name, ", ".join(got) or "(없음)"))
    return False


def main():
    ap = argparse.ArgumentParser(description="전면 분석 규약 검사기")
    ap.add_argument("--final", action="store_true",
                    help="종합 판 전용 — 우선순위·필수 산출물까지 검사")
    ap.add_argument("--selftest", action="store_true",
                    help="검사기가 실제로 위반을 잡는지 확인")
    ap.add_argument("--stage", choices=("a", "b"), default="a",
                    help="b = 수정 단계 검사(9.10)까지 — 착수 게이트·범위·영향 반경")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    return run(final=args.final, stage_b=(args.stage == "b"))


if __name__ == "__main__":
    sys.exit(main())
