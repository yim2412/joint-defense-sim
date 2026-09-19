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
            if key in REQUIRED_FIELDS or key in ("근거본문",):
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

def run(final=False, base=HERE, repo=REPO):
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
    print("[OK]   자기검증 전부 통과" if ok else "[FAIL] 자기검증 실패 — 검사기를 믿을 수 없다")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="전면 분석 규약 검사기")
    ap.add_argument("--final", action="store_true",
                    help="종합 판 전용 — 우선순위·필수 산출물까지 검사")
    ap.add_argument("--selftest", action="store_true",
                    help="검사기가 실제로 위반을 잡는지 확인")
    args = ap.parse_args()
    return selftest() if args.selftest else run(final=args.final)


if __name__ == "__main__":
    sys.exit(main())
