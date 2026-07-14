# -*- coding: utf-8 -*-
"""빌드 진척 표시기 — PyInstaller 로그에서 '실제 단계'를 뽑아 보여준다.

왜 만들었나: PyInstaller 로그는 훅 처리 줄이 수백 개 흐르다가 몇 분씩 정체되는 구간이
있어, 밖에서 보면 '멈춘 것'과 '느린 것'이 구분되지 않는다(v18.05.11 빌드가 평소 6분에서
12분으로 늘었을 때 실제로 그렇게 보였다). 경과 시간만 반복해 찍는 대신, **어느 단계에
있고 각 단계가 얼마나 걸렸는지**를 보여주면 정체 구간에서도 진척이 눈에 보인다.

사용법:
  python _build_progress.py --replay <로그파일>   # 끝난 빌드의 단계 타임라인 출력
  python _build_progress.py --watch  <로그파일>   # 빌드 중 실시간 추적(로그가 자라는 동안)
"""
from __future__ import annotations
import argparse, io, os, re, sys, time

# Windows 콘솔 기본 인코딩(cp949)이 박스·블록 문자를 못 찍는다 → UTF-8로 고정
if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 단계 경계 (표시명, 정규식, 도달 시 진척률, **기준선 도달시각(초)**).
# 기준선은 v18.05.11 실측 빌드(총 384s)에서 뽑았다 — 추측이 아니라 로그 타임스탬프 실측치.
# 이 값이 있어야 "느린가?"를 감이 아니라 **기준 대비**로 판정할 수 있다.
STAGES = [
    ('의존성 분석 시작',   re.compile(r'Analyzing .*app_main\.py|Initializing module'), 5,    9),
    ('모듈 훅 처리',       re.compile(r"Processing (standard )?module hook"),           15,  11),
    ('그래프 분석 완료',   re.compile(r'Looking for ctypes DLLs|Analyzing run-time'),   60, 352),
    ('바이너리 수집',      re.compile(r'Looking for dynamic libraries'),                70, 353),
    ('PYZ 생성',           re.compile(r'Building PYZ'),                                 80, 369),
    ('PKG 생성',           re.compile(r'Building PKG'),                                 88, 373),
    ('EXE 생성',           re.compile(r'Building EXE'),                                 94, 373),
    ('COLLECT 조립',       re.compile(r'Building COLLECT'),                             98, 377),
    ('완료',               re.compile(r'Building COLLECT .* completed successfully'),  100, 384),
]
_BASELINE_TOTAL = 384.0   # 기준 총 소요(초) — 실측
_SLOW_FACTOR    = 1.5     # 기준의 1.5배를 넘으면 '이상'으로 본다(감이 아닌 임계)
_TS = re.compile(r'^(\d+)\s+(INFO|WARNING|ERROR)')   # PyInstaller가 줄머리에 찍는 ms 타임스탬프
_HOOK = re.compile(r"hook-([\w\.]+)\.py")


def _scan(lines):
    """로그 줄들을 훑어 단계별 첫 등장 시각(초)과 훅 개수를 모은다."""
    seen, hooks, last_ms, last_hook = {}, 0, 0, ''
    for ln in lines:
        m = _TS.match(ln)
        if m:
            last_ms = int(m.group(1))
        h = _HOOK.search(ln)
        if h:
            hooks += 1
            last_hook = h.group(1)
        for name, pat, _pct, _base in STAGES:
            if name not in seen and pat.search(ln):
                seen[name] = last_ms / 1000.0
    return seen, hooks, last_ms / 1000.0, last_hook


def _bar(pct, w=22):
    f = int(w * pct / 100)
    return '█' * f + '░' * (w - f)


def _report(seen, hooks, elapsed, last_hook, live: bool, wall: float | None = None):
    """진척 보고. **모든 수치는 로그 타임스탬프·실제 시계에서만 나온다**(추정 금지)."""
    cur, pct, cur_base = '시작 전', 0, 0
    for name, _pat, p, base in STAGES:
        if name in seen:
            cur, pct, cur_base = name, p, base

    done = '완료' in seen
    # ETA·판정: 기준선 대비로만 계산한다(감으로 만든 퍼센트 금지)
    eta  = max(0.0, _BASELINE_TOTAL - elapsed)
    slow = elapsed > _BASELINE_TOTAL * _SLOW_FACTOR
    if done:
        verdict = f'✅ 완료 ({elapsed:.0f}s · 기준 {_BASELINE_TOTAL:.0f}s)'
    elif slow:
        verdict = f'🔴 기준의 {elapsed/_BASELINE_TOTAL:.1f}배 — 이상 의심(원인 확인 필요)'
    else:
        verdict = f'🟢 기준 범위 내 ({elapsed/_BASELINE_TOTAL*100:.0f}% 지점)'

    print('┌─ 빌드 진척 ' + ('(실시간)' if live else '(로그 재생)') + ' ────────────────────')
    print(f'│ 현재 단계 : {cur}   [{_bar(pct)}] {pct}%')
    print(f'│ 빌드 경과 : {elapsed:6.1f}s  (기준 {_BASELINE_TOTAL:.0f}s' +
          (f' · 남음 약 {eta:.0f}s)' if not done else ')'))
    if wall is not None:
        print(f'│ 실제 시계 : {wall:6.1f}s  ← 폴링 횟수로 추정하지 않고 시계로 측정')
    print(f'│ 훅 처리   : {hooks}개' + (f' (최근 {last_hook})' if last_hook else ''))
    print(f'│ 판정      : {verdict}')
    print('│')
    print('│ 단계별 도달 시각 (구간 소요 / 기준)')
    prev_t = 0.0
    for name, _pat, _p, base in STAGES:
        if name not in seen:
            print(f'│   ·  {name:<14s}      —          (기준 {base:>3.0f}s)')
            continue
        t   = seen[name]
        dur = t - prev_t
        tag = ' ← 여기서 대부분의 시간을 쓴다(정상)' if dur >= 60 else ''
        print(f'│   ✔  {name:<14s} {t:7.1f}s  (구간 {dur:6.1f}s / 기준 {base:>3.0f}s){tag}')
        prev_t = t
    print('└────────────────────────────────────────────────────')


def _run_build(log_path: str) -> int:
    """PyInstaller를 직접 띄우고 로그를 파일로 흘린다(호출부가 따로 리다이렉트할 필요 없음)."""
    import subprocess
    with io.open(log_path, 'w', encoding='utf-8', errors='replace') as f:
        p = subprocess.Popen(
            [sys.executable, '-m', 'PyInstaller', 'app_main.spec', '--noconfirm'],
            stdout=f, stderr=subprocess.STDOUT, cwd=os.path.dirname(os.path.abspath(__file__)))
        return p.pid


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('log')
    ap.add_argument('--watch', action='store_true', help='빌드 중 실시간 추적')
    ap.add_argument('--build', action='store_true',
                    help='PyInstaller를 직접 실행하고 그 로그를 감시(--watch와 함께)')
    ap.add_argument('--interval', type=float, default=30.0)
    a = ap.parse_args()

    if not a.watch:
        with io.open(a.log, encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        _report(*_scan(lines), live=False)
        return

    t0 = time.time()          # ★ 실제 시계 — 폴링 횟수로 시간을 추정하지 않는다
    if a.build:
        pid = _run_build(a.log)
        print(f'[build] PyInstaller 시작 (PID {pid}) → {a.log}')
        sys.stdout.flush()

    while True:
        if not os.path.exists(a.log):
            time.sleep(2); continue
        with io.open(a.log, encoding='utf-8', errors='replace') as f:
            lines = f.readlines()
        seen, hooks, elapsed, last_hook = _scan(lines)
        _report(seen, hooks, elapsed, last_hook, live=True, wall=time.time() - t0)
        sys.stdout.flush()
        if '완료' in seen:
            print(f'✅ 빌드 완료 — 빌드 {elapsed:.0f}s · 실제 시계 {time.time()-t0:.0f}s')
            return
        time.sleep(a.interval)


if __name__ == '__main__':
    main()
