# -*- coding: utf-8 -*-
"""종합감사 ⑦ 하위호환 + ④ 통합 MC 수치 안정성 (A1/E1 통합 상태)."""
import sys, math
sys.stdout.reconfigure(encoding='utf-8')
from engine_campaign import run_campaign, monte_carlo_campaign, load_forecast_model
from engine_combat import run_v7_simulation

def finite(x):
    return isinstance(x, (int, float)) and math.isfinite(x)

def main():
    m = load_forecast_model()
    fails = []

    # ⑦ 구버전 cfg — A1/E1 이전 형태(precise/parallel 키 없음)
    old = dict(fleet_preset='이지스 기동전단', enemy_fleet_preset='항모 킬 체인',
               weather='맑음 (주간)', enable_campaign_mode=True, campaign_horizon_h=72)
    r = run_campaign(dict(old, campaign_seed=1), model=m)
    if r.get('n_precise', 0) != 0:
        fails.append(f"⑦ 구버전 cfg인데 정밀 교전 발동(n_precise={r['n_precise']})")
    if r['outcome'] not in ('win', 'draw', 'loss'):
        fails.append(f"⑦ outcome 무효: {r['outcome']}")
    print(f"⑦ 구버전 캠페인 단발: outcome={r['outcome']} n_precise={r['n_precise']} (기대 0)")

    # ⑦ 구버전 단발 교전(precise 무관)
    rv = run_v7_simulation(dict(old, enable_campaign_mode=False))
    ir = rv.get('intercept_rate')
    if not (finite(ir) and 0 <= ir <= 1):
        fails.append(f"⑦ 단발 요격률 범위 벗어남: {ir}")
    print(f"⑦ 구버전 단발 교전: intercept_rate={ir:.3f}")

    # ⑦ 구버전 캠페인 MC(proxy 임계=64 → n=20은 순차)
    mc = monte_carlo_campaign(old, n=20, model=m)
    for k in ('win_rate', 'draw_rate', 'loss_rate', 'mean_control_avg'):
        v = mc.get(k)
        if not (finite(v) and 0 <= v <= 1):
            fails.append(f"⑦ MC {k} 범위/유한 위반: {v}")
    s = mc['win_rate'] + mc['draw_rate'] + mc['loss_rate']
    if abs(s - 1.0) > 1e-6:
        fails.append(f"⑦ MC 승/무/패 합≠1: {s}")
    print(f"⑦ 구버전 캠페인 MC(n=20): win={mc['win_rate']} draw={mc['draw_rate']} loss={mc['loss_rate']} 합={s:.3f} parallel={mc['parallel']}")

    # ④ 통합 MC — 정밀 ON 병렬 수치 안정성(NaN/범위)
    mc2 = monte_carlo_campaign(dict(old, enable_precise_engagement=True), n=16, model=m)
    for k in ('win_rate', 'mean_control_avg', 'surviving_avg', 'cost_avg', 'n_precise_avg'):
        v = mc2.get(k)
        if not finite(v):
            fails.append(f"④ 정밀 MC {k} NaN/Inf: {v}")
    if not (0 <= mc2['win_rate'] <= 1):
        fails.append(f"④ 정밀 MC win_rate 범위: {mc2['win_rate']}")
    print(f"④ 정밀 ON 캠페인 MC(n=16): win={mc2['win_rate']} surviving={mc2['surviving_avg']} n_precise_avg={mc2['n_precise_avg']} cost={mc2['cost_avg']:.0f} parallel={mc2['parallel']}")

    print()
    if fails:
        print("🔴 하위호환/MC 감사 FAIL:")
        for f in fails: print("  -", f)
        sys.exit(1)
    print("✅ ⑦ 하위호환 + ④ 통합 MC 수치 안정성 PASS")

if __name__ == '__main__':
    main()
