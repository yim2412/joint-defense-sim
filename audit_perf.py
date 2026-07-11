#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
audit_perf.py — 실행시간 회귀 가드 (성능 자동 측정).

CLAUDE.md 종합 감사 ④의 'wall-time 급증 1.5배+면 원인 규명' 규칙을 자동화한다.
단발·전장·캠페인 각 경로의 1회 실행시간(중앙값)을 측정해 저장된 기준
(audit_perf_baseline.json)과 대조 — 급증하면 경고(엔진 성능 회귀·비효율 도입 조기 포착).

주의: 실행시간은 머신 부하에 민감 → **다른 무거운 작업과 겹치지 않을 때**(야간 러너 단독
실행 권장) 측정해야 신뢰. 임계 1.5배는 부하 변동을 흡수할 만큼 넉넉히 잡았다.

사용:
    python audit_perf.py            # 기준 대조(급증 시 exit 1)
    python audit_perf.py --update   # 현재 측정치를 새 기준으로 저장(의도된 변경 후)
"""
import sys, io, os, json, time, statistics

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_combat import run_v7_simulation, run_battle_simulation   # noqa: E402
from engine_campaign import run_campaign, load_forecast_model         # noqa: E402
from audit_verify_regression import _BASE                            # noqa: E402

BASELINE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        'audit_perf_baseline.json')
N = 5           # 회당 반복(중앙값으로 이상치 완화)
THRESH = 1.5    # 기준 대비 배율 임계


def _time(fn, cfg, n=N):
    ts = []
    for _ in range(n):
        t = time.perf_counter()
        fn(dict(cfg))
        ts.append(time.perf_counter() - t)
    return statistics.median(ts)


def main():
    update = '--update' in sys.argv
    single = dict(_BASE, fleet_preset='이지스 기동전단',
                  enemy_fleet_preset='입체 포화 (최강)', sim_seed=1)
    battle = dict(_BASE, fleet_preset='기동전단 기본',
                  enemy_fleet_preset='랴오닝 항모전단', sim_seed=1,
                  battle_horizon_s=1200)
    model = load_forecast_model()
    camp = dict(fleet_preset='기동전단 기본', enemy_fleet_preset='랴오닝 항모전단',
                enemy_fleet_mode='preset', weather='맑음 (주간)', campaign_seed=1)

    cur = {
        'single':   _time(run_v7_simulation, single),
        'battle':   _time(run_battle_simulation, battle),
        'campaign': _time(lambda c: run_campaign(c, model=model), camp),
    }
    print(f"실행시간(중앙값 of {N}회):")
    for k, v in cur.items():
        print(f"  {k:9s} {v*1000:8.1f} ms")

    if update or not os.path.exists(BASELINE):
        with open(BASELINE, 'w', encoding='utf-8') as f:
            json.dump(cur, f, ensure_ascii=False, indent=2)
        print(f"✅ 성능 기준 저장 → {os.path.basename(BASELINE)}")
        return 0

    with open(BASELINE, encoding='utf-8') as f:
        base = json.load(f)
    bad = []
    for k, v in cur.items():
        b = base.get(k)
        if b and v > b * THRESH:
            bad.append(f"{k}: {v*1000:.1f}ms > 기준 {b*1000:.1f}ms (×{v/b:.2f})")
    print(f"{'='*56}")
    if bad:
        print(f"⚠ 성능 회귀 {len(bad)}건 — 기준 대비 {THRESH}배 초과:")
        for x in bad:
            print(f"  🔴 {x}")
        return 1
    print(f"✅ 성능 PASS — 전 경로 기준 대비 {THRESH}배 이내")
    return 0


if __name__ == '__main__':
    sys.exit(main())
