#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
audit_local_edit.py — 로컬 모델(aider) 세션 이후 실제로 뭘 했는지 확인하는 방화벽.

plan_local_llm.md 1-e/1-f 실측 결론: 로컬 모델(qwen3-coder:30b 등)은 ①상태가 언제
리셋되는지 추론 못 함 ②요청과 구현의 불일치를 자각 못 함 ③**아무것도 안 하고 "했다"고
보고**한다 — 이 셋은 정적 스캔·회귀 골든 같은 기존 게이트로 못 잡는다(게이트는 "기존을
안 깨뜨렸나"만 보지 "맞게 새로 만들었나·실제로 하긴 했나"는 안 본다).

이 스크립트는 "모델이 뭐라고 말했나"가 아니라 **git diff가 실제로 뭘 바꿨나**를 정본으로
삼아 보여주고, 건드린 파일 종류에 맞는 게이트(정적 스캔·회귀·round-trip)를 자동으로
돌린다. **PASS가 나와도 "맞게 만들었다"의 증명은 아니다** — 상태 리셋 누락형 버그
(v1-d B층: army_fire_unused 패턴을 절반만 베껴 플래그가 영구 True로 박힘)처럼 게이트를
전부 통과하면서 틀린 코드가 있었다. 그래서 이 스크립트는 마지막에 항상
"diff를 사람이 읽어라"로 끝난다 — 이건 자동화할 수 없는 부분이다.

사용법:
    python audit_local_edit.py                 # 워킹트리 변경 전체(스테이지+비스테이지) 확인
    python audit_local_edit.py --staged        # git add 된 것만
    python audit_local_edit.py --since <ref>   # 특정 커밋 이후 변경(예: HEAD~1)

무엇을 하나:
    1. 실제로 바뀐 파일 목록 + diff 통계를 보여준다(모델의 말이 아니라 git이 본 사실).
    2. 바뀐 파일 종류에 따라 필요한 게이트만 골라 돌린다:
       - 아무 .py나 바뀌면: py_compile 구문 검사
       - engine_*.py/app_engine.py/mixin_*.py/app_workers.py 등 엔진 소비 경로가 바뀌면:
         audit_verify_regression.py
       - app_main.py/mixin_*.py/app_launcher.py/ui_*.py가 바뀌면: _audit_roundtrip.py
       - 아무 거나 바뀌면 항상: audit_static_scan.py
    3. "상태 리셋 누락" 휴리스틱 — diff에 `self.X = True`(또는 `= False`)가 새로 생겼는데
       같은 파일 안에 반대값 대입이 전혀 없으면 경고(1-d B층 버그와 동일 패턴 — 완벽한
       탐지는 아니고 사람이 봐야 할 지점을 좁혀주는 용도).
    4. 마지막에 항상 "게이트 PASS와 무관하게 diff를 읽어라" 재확인 문구 출력.
"""
import argparse
import os
import re
import subprocess
import sys

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

ROOT = os.path.dirname(os.path.abspath(__file__))


def sh(args):
    return subprocess.run(args, cwd=ROOT, capture_output=True, text=True, encoding='utf-8')


def changed_files(staged: bool, since: str | None):
    if since:
        r = sh(['git', 'diff', '--name-only', since])
    elif staged:
        r = sh(['git', 'diff', '--name-only', '--cached'])
    else:
        # 스테이지+비스테이지 전부 (untracked 신규 파일은 add 안 됐으면 diff에 안 잡히니
        # 별도로 확인)
        r = sh(['git', 'diff', '--name-only', 'HEAD'])
    files = [f for f in r.stdout.splitlines() if f.strip()]
    return files


def diff_stat(staged: bool, since: str | None):
    if since:
        r = sh(['git', 'diff', '--stat', since])
    elif staged:
        r = sh(['git', 'diff', '--stat', '--cached'])
    else:
        r = sh(['git', 'diff', '--stat', 'HEAD'])
    return r.stdout


def diff_full(staged: bool, since: str | None, path: str):
    if since:
        r = sh(['git', 'diff', since, '--', path])
    elif staged:
        r = sh(['git', 'diff', '--cached', '--', path])
    else:
        r = sh(['git', 'diff', 'HEAD', '--', path])
    return r.stdout


def check_state_reset_heuristic(files, staged, since):
    """'self.X = True'만 새로 생기고 'self.X = False'(또는 그 반대)가 diff 안에
    전혀 없는 파일을 경고. army_fire_unused류 영구-플래그 버그를 좁혀서 잡는 용도."""
    warnings = []
    for f in files:
        if not f.endswith('.py'):
            continue
        d = diff_full(staged, since, f)
        added = [l[1:] for l in d.splitlines() if l.startswith('+') and not l.startswith('+++')]
        added_text = '\n'.join(added)
        names_true = set(re.findall(r'self\.(\w+)\s*=\s*True\b', added_text))
        names_false = set(re.findall(r'self\.(\w+)\s*=\s*False\b', added_text))
        one_sided = (names_true - names_false) | (names_false - names_true)
        # 흔한 오탐 방지: 생성자에서 초기값 한 번만 대입하는 건 정상(리셋 경로가 없는 게
        # 아니라 애초에 상태를 안 되돌리는 값 — 예: _initialized). 대입이 __init__ 밖에서도
        # 일어나는지까지는 구분 못 하므로, 결과는 '검토 후보'로만 출력한다.
        if one_sided:
            warnings.append((f, sorted(one_sided)))
    return warnings


def run(cmd):
    print(f"\n$ {' '.join(cmd)}")
    r = subprocess.run(cmd, cwd=ROOT)
    return r.returncode == 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--staged', action='store_true', help='git add 된 변경만 확인')
    ap.add_argument('--since', default=None, help='특정 커밋/브랜치 이후 변경과 비교(예: HEAD~1)')
    args = ap.parse_args()

    print("=" * 70)
    print("audit_local_edit.py — 로컬 모델 세션 사후 검증 (모델 말 대신 git diff가 정본)")
    print("=" * 70)

    files = changed_files(args.staged, args.since)
    stat = diff_stat(args.staged, args.since)

    if not files:
        print("\n🔴 실제로 바뀐 파일이 0개다.")
        print("   모델이 '수정했습니다'라고 말했다면 — 그 보고는 거짓이다(1-e 실측 사례와")
        print("   동일 패턴: 도구 호출 0회로 아무것도 안 하고 완료 보고). 아무 게이트도 돌리지")
        print("   않는다 — 돌려봐야 '변경 없음'을 재확인할 뿐이다.")
        sys.exit(1)

    print(f"\n실제로 바뀐 파일 {len(files)}개 (git이 본 사실 — 모델 주장이 아님):")
    for f in files:
        print(f"  - {f}")
    print("\n--- diff --stat ---")
    print(stat)

    py_files = [f for f in files if f.endswith('.py') and os.path.exists(os.path.join(ROOT, f))]

    ok = True

    if py_files:
        print("\n[1/4] py_compile 구문 검사")
        import py_compile
        for f in py_files:
            try:
                py_compile.compile(os.path.join(ROOT, f), doraise=True)
                print(f"  OK   {f}")
            except py_compile.PyCompileError as e:
                print(f"  FAIL {f}: {e}")
                ok = False

    engine_touch = any(
        re.match(r'^(engine_\w+\.py|app_engine\.py|mixin_\w+\.py|app_workers\.py)$', f)
        for f in files
    )
    ui_touch = any(
        re.match(r'^(app_main\.py|mixin_\w+\.py|app_launcher\.py|ui_\w+\.py)$', f)
        for f in files
    )

    if engine_touch:
        print("\n[2/4] 엔진 소비 경로 변경 감지 → audit_verify_regression.py")
        ok &= run([sys.executable, 'audit_verify_regression.py'])
    else:
        print("\n[2/4] 엔진 소비 경로 미변경 → 회귀 검증 스킵")

    if ui_touch:
        print("\n[3/4] UI/MainWindow 경로 변경 감지 → _audit_roundtrip.py")
        ok &= run([sys.executable, '_audit_roundtrip.py'])
    else:
        print("\n[3/4] UI 경로 미변경 → round-trip 스킵")

    print("\n[4/4] audit_static_scan.py (항상 실행)")
    ok &= run([sys.executable, 'audit_static_scan.py'])

    print("\n--- 상태 리셋 누락 휴리스틱 (v1-d B층 army_fire_unused류 버그 패턴) ---")
    warns = check_state_reset_heuristic(files, args.staged, args.since)
    if warns:
        print("🟡 검토 후보 (True/False 중 한쪽만 diff에 새로 생김 — 오탐 가능, 사람이 확인):")
        for f, names in warns:
            print(f"  - {f}: {names}")
    else:
        print("해당 없음(단, 이 휴리스틱은 diff 안에서만 보므로 기존 코드에 있던 리셋")
        print("경로가 삭제된 경우는 못 잡는다).")

    print("\n" + "=" * 70)
    print("✅ 게이트 전부 PASS" if ok else "❌ 게이트 중 하나 이상 FAIL — 위 로그에서 원인 확인")
    print("=" * 70)
    print("⚠️  PASS라도 '맞게 만들었다'의 증명이 아니다. 게이트는 '기존을 안 깨뜨렸나'만")
    print("    본다 — 요청과 다르게 구현됐는지, 주석과 코드가 다른 말을 하는지는 사람이")
    print("    위 diff를 직접 읽어야 잡는다. 특히 이 세션이 aider/로컬 모델 결과라면")
    print("    'Applied edit to X'라는 로그를 봤어도 diff 내용 자체를 반드시 읽을 것.")
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
