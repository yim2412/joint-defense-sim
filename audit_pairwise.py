#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
audit_pairwise.py — 토글 쌍(pairwise) 조합 상호작용 감사 (자동 오류 탐지 그물 D).

audit_property는 토글을 40% 확률로 랜덤 조합해 표본만 본다 → 특정 토글 쌍의
상호작용 버그는 잠재(BLIND_SPOTS 1번). 이 도구는 enable_ 토글 전수 쌍(C(N,2))을
각각 ON(나머지 기본)으로 1회 돌려 ▸크래시 ▸NaN/Inf ▸보존식 위반(요격>총·
확률값∉[0,1])을 전수 탐지한다.

경로 커버리지(v18.02): 단발(run_v7_simulation)뿐 아니라 **전장(run_battle_simulation)**·
**캠페인(run_campaign)** 경로도 pairwise. 각 경로가 소비하는 토글을 그 엔진 파일에서
자동 추출한다(전장·단발=engine_combat/core, 캠페인=engine_campaign/airforce).

사용:
    python audit_pairwise.py              # 단발 pairwise (발견 있으면 exit 1)
    python audit_pairwise.py --mode battle    # 전장 pairwise
    python audit_pairwise.py --mode campaign  # 캠페인 pairwise(공군 토글 포함)
    python audit_pairwise.py --mode all       # 세 경로 모두
"""
import sys, io, os, re, itertools

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_combat import run_v7_simulation, run_battle_simulation   # noqa: E402
from engine_campaign import run_campaign, load_forecast_model         # noqa: E402
from audit_property import _finite_scan   # noqa: E402 (NaN/Inf 스캐너 재사용)

_MODEL = None   # 캠페인 forecast 모델(1회 로드 공유)


def toggles_from(files):
    """지정 엔진 파일들이 실제 소비하는 enable_ 토글 전수 자동추출."""
    keys = set()
    for fn in files:
        with open(fn, encoding='utf-8') as f:
            txt = f.read()
        keys |= set(re.findall(r"\.get\(['\"](enable_\w+)", txt))
        keys |= set(re.findall(r"cfg\[['\"](enable_\w+)", txt))
    return sorted(keys)


def _campaign_run(cfg):
    global _MODEL
    if _MODEL is None:
        _MODEL = load_forecast_model()
    return run_campaign(cfg, model=_MODEL)


# 가벼운 고정 시나리오(빠른 1회) — 위협 수가 적어 1쌍당 빠르게 끝남
_LIGHT = dict(enemy_fleet_preset='랴오닝 항모전단', enemy_fleet_mode='preset',
              weather='맑음 (주간)')

MODES = {
    'single': dict(label='단발', run=run_v7_simulation,
                   files=['engine_combat.py', 'engine_core.py'],
                   base=dict(_LIGHT, fleet_preset='기동전단 기본', sim_seed=1)),
    'battle': dict(label='전장', run=run_battle_simulation,
                   files=['engine_combat.py', 'engine_core.py'],
                   base=dict(_LIGHT, fleet_preset='기동전단 기본', sim_seed=1,
                             battle_horizon_s=1200)),
    'campaign': dict(label='캠페인', run=_campaign_run,
                     files=['engine_campaign.py', 'engine_airforce.py'],
                     base=dict(_LIGHT, fleet_preset='기동전단 기본', campaign_seed=1,
                               enable_air_campaign=True)),   # 공군층 활성(sead/strike 발현)
}


def check(cfg, run_fn):
    probs = []
    try:
        r = run_fn(dict(cfg))
    except Exception as e:
        return [f"CRASH {type(e).__name__}: {e}"]
    for b in _finite_scan(r):
        probs.append(f"NaN/Inf@{b}")
    for pk in ('intercept_rate', 'friendly_score', 'mean_control'):
        pv = r.get(pk)
        if isinstance(pv, (int, float)) and not (-1e-9 <= pv <= 1.0 + 1e-9):
            probs.append(f"{pk}={pv}(범위)")
    tt = r.get('total_threats', 0) or 0
    it = r.get('intercepted_threats', 0) or 0
    if it > tt:
        probs.append(f"요격{it}>총{tt}(보존식)")
    return probs[:5]


def run_pairwise(m):
    spec = MODES[m]
    label, run_fn, base = spec['label'], spec['run'], spec['base']
    toggles = toggles_from(spec['files'])
    pairs = list(itertools.combinations(toggles, 2))
    print(f"\n── {label} 경로: 토글 {len(toggles)}개 → pairwise {len(pairs)}쌍 × 1회 검사 ──")

    if check(dict(base), run_fn):
        print(f"❌ {label} baseline(토글 없음) 자체가 문제 — 시나리오 재검토 필요")
        return None
    findings = []
    for a, b in pairs:
        cfg = dict(base); cfg[a] = True; cfg[b] = True
        probs = check(cfg, run_fn)
        if probs:
            findings.append((a, b, probs))
            print(f"  🔴 [{a} + {b}]: {'|'.join(probs)}")
    return findings


def main():
    argv = sys.argv[1:]
    mode = 'single'
    if '--mode' in argv:
        mode = argv[argv.index('--mode') + 1]
    modes = ['single', 'battle', 'campaign'] if mode == 'all' else [mode]

    total = []
    for m in modes:
        if m not in MODES:
            print(f"❌ 알 수 없는 모드: {m} (single|battle|campaign|all)")
            return 2
        res = run_pairwise(m)
        if res is None:
            return 1
        total.extend((m,) + f for f in res)

    print(f"\n{'='*56}")
    if total:
        print(f"⚠ pairwise 발견 {len(total)}건 — 위 토글 쌍 상호작용 점검 필요")
        return 1
    print(f"✅ pairwise PASS — 경로 {modes} 전부 크래시·NaN·보존식 위반 0")
    return 0


if __name__ == '__main__':
    sys.exit(main())
