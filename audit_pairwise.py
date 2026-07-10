#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
audit_pairwise.py — 토글 쌍(pairwise) 조합 상호작용 감사 (자동 오류 탐지 그물 D).

audit_property는 토글을 40% 확률로 랜덤 조합해 표본만 본다 → 특정 토글 쌍의
상호작용 버그는 잠재(BLIND_SPOTS 1번). 이 도구는 enable_ 토글 전수 쌍(C(N,2))을
각각 ON(나머지 기본)으로 단발 1회 돌려 ▸크래시 ▸NaN/Inf ▸보존식 위반(요격>총·
intercept_rate∉[0,1])을 전수 탐지한다.

사용: python audit_pairwise.py        # 발견 있으면 exit 1
"""
import sys, io, os, re, itertools

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_combat import run_v7_simulation          # noqa: E402
from audit_property import _finite_scan               # noqa: E402 (NaN/Inf 스캐너 재사용)


def all_engine_toggles():
    """엔진이 실제 소비하는 enable_ 토글 전수 자동추출(property의 수동 8개가 아니라 전부).
    소비하지 않는 UI 전용 플래그는 pairwise 대상에서 자연 제외된다."""
    keys = set()
    for fn in ('engine_combat.py', 'engine_core.py'):
        with open(fn, encoding='utf-8') as f:
            txt = f.read()
        keys |= set(re.findall(r"\.get\(['\"](enable_\w+)", txt))
        keys |= set(re.findall(r"cfg\[['\"](enable_\w+)", txt))
    return sorted(keys)

# 가벼운 고정 시나리오(빠른 단발) — 위협은 생성되되 위협 수가 적어 1쌍당 빠르게 끝남
BASE = dict(fleet_preset='기동전단 기본', enemy_fleet_preset='랴오닝 항모전단',
            enemy_fleet_mode='preset', weather='맑음 (주간)', sim_seed=1)


def check(cfg):
    probs = []
    try:
        r = run_v7_simulation(dict(cfg))
    except Exception as e:
        return [f"CRASH {type(e).__name__}: {e}"]
    for b in _finite_scan(r):
        probs.append(f"NaN/Inf@{b}")
    ir = r.get('intercept_rate')
    if isinstance(ir, (int, float)) and not (-1e-9 <= ir <= 1.0 + 1e-9):
        probs.append(f"intercept_rate={ir}(범위)")
    tt = r.get('total_threats', 0) or 0
    it = r.get('intercepted_threats', 0) or 0
    if it > tt:
        probs.append(f"요격{it}>총{tt}(보존식)")
    return probs[:5]


def main():
    toggles = all_engine_toggles()
    pairs = list(itertools.combinations(toggles, 2))
    print(f"토글 {len(toggles)}개 → pairwise {len(pairs)}쌍 × 단발 1회 검사")

    # baseline 정상 확인
    if check(dict(BASE)):
        print("❌ baseline(토글 없음) 자체가 문제 — 시나리오 재검토 필요")
        return 1

    findings = []
    for i, (a, b) in enumerate(pairs):
        cfg = dict(BASE)
        cfg[a] = True
        cfg[b] = True
        probs = check(cfg)
        if probs:
            findings.append((a, b, probs))
            print(f"  🔴 [{a} + {b}]: {'|'.join(probs)}")

    print(f"\n{'='*56}")
    if findings:
        print(f"⚠ pairwise 발견 {len(findings)}건 — 위 토글 쌍 상호작용 점검 필요")
        return 1
    print(f"✅ pairwise PASS — {len(pairs)}쌍 전부 크래시·NaN·보존식 위반 0")
    return 0


if __name__ == '__main__':
    sys.exit(main())
