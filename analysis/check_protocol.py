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
        check_stage_b_items(items, rep)
        check_stage_b_diff(items, rep, repo)

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
    (r"^engine_(campaign|airforce|army|joint)\.py$", "C"),
    (r"^(app_workers|mixin_simlifecycle)\.py$", "W"),
    (r"^app_utils\.py$", "UB"),          # 리소스 경로(_res)가 있어 번들 반경도 걸린다
    (r"^(ui_.*|mixin_.*|app_main|app_launcher|app_theme|app_engine)\.py$", "U"),
    (r"^(audit_|_audit_|_build_|_bg_|_changelog_|_asset_|improve_|check_).*\.py$", "T"),
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
B_FIELDS = ("대상", "예측", "결과")
MAX_BATCH_FILES = 3
MAX_BATCH_LINES = 200
LEDGER_PREFIX = "analysis/"          # 대장 자신은 범위 선언 대상이 아니다

DIRECTION_RE = re.compile(r"(↑|↓|오른|내린|증가|감소|늘|줄|상승|하락|빨라|느려)")
MAGNITUDE_RE = re.compile(r"[+\-±]?\d+(?:\.\d+)?\s*(?:%p|%|배|발|척|초|s|ms|km|점|회)")
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
        out = subprocess.run(["git"] + list(args), cwd=repo, capture_output=True,
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


def check_stage_b_items(items, rep):
    """9.10 검사 1~4 — 대장 항목만 본다(git 불필요)."""
    for it in items:
        if not it["state"].startswith(("수정중", "수정됨")):
            continue
        tag = "%s(L%d)" % (it["id"], it["lineno"])
        f = it["fields"]
        body = "\n".join(it["body"])
        repro = f.get("재현", "")
        has_p = bool(PROBE_RE.search(repro))
        has_s = bool(STATIC_RE.search(repro))
        has_r = "예측" in f

        if not (has_p or has_s or has_r):
            rep.fail("9.2 착수 게이트",
                     "%s 상태가 '%s' 인데 P/S/R 판정이 없다 — 재현:에 프로브 경로(P)나 "
                     "검사함수(S), 아니면 예측: 줄(R)이 있어야 한다" % (tag, it["state"]))

        if has_r:
            pred = f.get("예측", "")
            miss = []
            if len(pred.split()) < 3:
                miss.append("지표명")
            if not DIRECTION_RE.search(pred):
                miss.append("방향")
            if not MAGNITUDE_RE.search(pred):
                miss.append("최소 크기")
            if not SCENARIO_RE.search(pred):
                miss.append("측정 시나리오")
            if miss:
                rep.fail("9.2 R 예측 형식",
                         "%s 예측에 %s 누락 — '요격률이 변한다' 류는 무엇이 나와도 맞는 "
                         "문장이라 판정이 아니다" % (tag, "·".join(miss)))
            if not URL_RE.search(body):
                rep.fail("9.2 R 외부 앵커",
                         "%s 예측이 있는데 출처 URL이 없다 — 못 달면 [미확인]으로 두고 "
                         "고치지 않는다(4.4 결정 요청)" % tag)

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

    declared = set()
    for it in items:
        if it["state"].startswith("수정중"):
            for p in re.split(r"[,\s]+", it["fields"].get("대상", "")):
                if p.strip():
                    declared.add(p.strip().replace("\\", "/"))
    if declared:
        if len(declared) > MAX_BATCH_FILES:
            rep.fail("9.1 묶음 상한", "대상 선언 %d개 파일 > %d개 — 묶음을 쪼갤 것"
                     % (len(declared), MAX_BATCH_FILES))
        extra = [p for p in code if p not in declared]
        if extra:
            rep.fail("9.3 범위 확대",
                     "선언(대상:)에 없는 파일이 바뀌었다: %s — 넓히려면 선언을 고쳐 "
                     "커밋할 것(조용한 확대 금지)" % ", ".join(extra[:5]))
    elif code:
        rep.warn("9.3 착수 선언",
                 "코드 변경 %d개 파일이 있는데 '수정중' 항목의 대상: 선언이 없다" % len(code))

    n = changed_lines(repo)
    if n > MAX_BATCH_LINES:
        rep.fail("9.1 묶음 상한",
                 "변경 %d라인 > %d라인 — 실패 시 원인 분리가 안 된다. 쪼갤 것"
                 % (n, MAX_BATCH_LINES))
    else:
        rep.note("코드 변경 %d라인 (상한 %d · analysis/·*.md 제외)"
                 % (n, MAX_BATCH_LINES))


def selftest_b():
    """B 검사도 일부러 깨뜨려 본다. 통과는 증거가 아니다."""
    ok = True
    cases = [
        ("판정 없음", "9.2 착수 게이트", """### F-901 · 축: 모델타당성 · 상태: 수정중
- 재현: (없음)
- 요약: 판정 없이 수정에 들어갔다
"""),
        ("느슨한 예측", "9.2 R 예측 형식", """### F-902 · 축: 모델타당성 · 상태: 수정중
- 재현: (없음)
- 예측: 요격률이 변한다
- 근거본문: https://example.org/spec
"""),
        ("앵커 없음", "9.2 R 외부 앵커", """### F-903 · 축: 모델타당성 · 상태: 수정중
- 재현: (없음)
- 예측: 기준 시나리오 MC 200회 요격률이 오른다 최소 +2%p
- 요약: 출처가 없다
"""),
        ("결과 없음", "9.2 R 결과", """### F-904 · 축: 모델타당성 · 상태: 수정됨
- 재현: analysis/probes/p904_x.py
- 요약: 결과를 안 적었다
"""),
    ]
    for name, expect, block in cases:
        rep = Report()
        items = parse_findings(block)
        check_stage_b_items(items, rep)
        if any(c == expect for c, _ in rep.fails):
            print("[OK]   %-18s -> %s 로 잡음" % (name, expect))
        else:
            got = ", ".join(sorted(set(c for c, _ in rep.fails))) or "(위반 0건)"
            print("[FAIL] %-18s -> '%s' 를 못 잡음. 잡은 것: %s" % (name, expect, got))
            ok = False

    # 정상 R 항목은 통과해야 한다 (오탐 검사)
    good = """### F-905 · 축: 모델타당성 · 상태: 수정됨
- 재현: (없음)
- 예측: 기준 시나리오 MC 200회 요격률이 오른다, 최소 +2%p
- 결과: 14.2% -> 17.1% (+2.9%p) — 예측 부합
- 근거본문: 출처 https://www.navy.mil/example
"""
    rep = Report()
    check_stage_b_items(parse_findings(good), rep)
    if rep.fails:
        print("[FAIL] %-18s -> 정상 R 항목인데 위반: %s"
              % ("B 오탐 검사", ", ".join(c for c, _ in rep.fails)))
        ok = False
    else:
        print("[OK]   %-18s -> 정상 R 항목은 통과" % "B 오탐 검사")

    # 반경 분류: 알려진 파일은 분류되고, 낯선 파일은 미분류로 걸려야 한다
    hit, unknown = classify_radius(["engine_combat.py", "ui_charts.py", "app_main.spec",
                                    "analysis/FINDINGS.md", "낯선파일_zzz.xyz"])
    if set(hit) == {"E", "U", "B", "T"} and unknown == ["낯선파일_zzz.xyz"]:
        print("[OK]   %-18s -> 분류 %s · 미분류 %s" % ("반경 분류", sorted(hit), unknown))
    else:
        print("[FAIL] %-18s -> 분류 %s · 미분류 %s (기대와 다름)"
              % ("반경 분류", sorted(hit), unknown))
        ok = False
    return ok


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
