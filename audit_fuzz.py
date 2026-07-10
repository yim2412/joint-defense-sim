#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
audit_fuzz.py — 수치 cfg 키 경계값 fuzzing (자동 오류 탐지 그물 B).

engine_combat/engine_core에서 `cfg.get('key', <숫자>)` 형태의 수치 키를 자동 추출해
극단값(0·음수·거대값)을 하나씩 주입, run_v7_simulation을 실제로 돌려
▸크래시(예외) ▸NaN/Inf ▸확률값 범위 위반(intercept_rate ∉ [0,1])을 자동 탐지한다.

배경: dmo_spread_km=0 → 0나눗셈 같은 "경계값에서만 터지는" 버그는 정적 스캔·회귀가
못 잡는다(아무도 그 값을 안 넣어봐서). 이 도구가 수치 키를 전수 극단 주입해 발굴한다.
(BLIND_SPOTS 7번 대응 — 비-enable_ 수치 키 경계 자동 점검.)

사용: python audit_fuzz.py            # 발견 있으면 exit 1
"""
import sys, io, os, re, math

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_combat import run_v7_simulation          # noqa: E402
from audit_verify_regression import _BASE            # noqa: E402

# 주입 극단값 — 0(0나눗셈)·음수(부호 가정 위반)·거대값(오버플로·무한루프 유발)
EXTREMES = [0, -1, 1_000_000_000]

# 극단 주입이 의미상 무해가 아닌(=시뮬을 왜곡할 뿐 버그 아님) 키는 제외 화이트리스트.
# 여기 없는 키에서 크래시/NaN이 나면 진짜 방어 부재로 본다.
SKIP_KEYS = set()


def extract_numeric_keys():
    keys = set()
    for fn in ('engine_combat.py', 'engine_core.py'):
        with open(fn, encoding='utf-8') as f:
            txt = f.read()
        for m in re.finditer(r"cfg\.get\((['\"])([a-z_]+)\1,\s*(-?[0-9][0-9.]*)", txt):
            key = m.group(2)
            if key.startswith('enable_') or key in SKIP_KEYS:
                continue
            keys.add(key)
    return sorted(keys)


def scan_result(r):
    """결과에서 NaN/Inf·확률 범위 위반 탐지. 반환: 문제 문자열 리스트(최대 5)."""
    probs = []

    def walk(o, path=''):
        if len(probs) >= 5:
            return
        if isinstance(o, dict):
            for k, v in o.items():
                walk(v, f"{path}.{k}")
        elif isinstance(o, (list, tuple)):
            for i, v in enumerate(o[:20]):
                walk(v, f"{path}[{i}]")
        elif isinstance(o, float):
            if math.isnan(o):
                probs.append(f"NaN@{path}")
            elif math.isinf(o):
                probs.append(f"Inf@{path}")

    walk(r)
    ir = r.get('intercept_rate')
    if isinstance(ir, (int, float)) and not (-1e-9 <= ir <= 1.0 + 1e-9):
        probs.append(f"intercept_rate={ir}(범위위반)")
    return probs[:5]


def main():
    keys = extract_numeric_keys()
    base = dict(_BASE, fleet_preset='이지스 기동전단',
                enemy_fleet_preset='입체 포화 (최강)', sim_seed=1)
    print(f"수치 cfg 키 {len(keys)}개 × 극단값 {len(EXTREMES)}종 = {len(keys)*len(EXTREMES)}회 fuzzing (단발)")

    try:
        run_v7_simulation(dict(base))
    except Exception as e:
        print(f"❌ baseline 크래시(fuzzing 이전) — {type(e).__name__}: {e}")
        return 1

    findings = []
    for key in keys:
        for ext in EXTREMES:
            cfg = dict(base)
            cfg[key] = ext
            try:
                r = run_v7_simulation(cfg)
            except Exception as e:
                findings.append((key, ext, f"CRASH {type(e).__name__}: {e}"))
                print(f"  🔴 {key}={ext}: CRASH {type(e).__name__}: {e}")
                continue
            probs = scan_result(r)
            if probs:
                findings.append((key, ext, '|'.join(probs)))
                print(f"  🟡 {key}={ext}: {'|'.join(probs)}")

    print(f"\n{'='*56}")
    if findings:
        print(f"⚠ fuzzing 발견 {len(findings)}건 — 위 키의 극단값 방어 점검 필요")
        return 1
    print(f"✅ fuzzing PASS — 수치 키 {len(keys)}개 극단값 전부 크래시·NaN·범위위반 0")
    return 0


if __name__ == '__main__':
    sys.exit(main())
