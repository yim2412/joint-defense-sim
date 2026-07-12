# -*- coding: utf-8 -*-
"""사각④: 캠페인 MC 대규모 안정성 + OFF/정밀ON 기준값 측정.
대규모 n으로 NaN·확률범위·꼬리거동을 확인하고, 정밀 OFF↔ON 효과를 기준값으로 남긴다.
정밀 OFF는 대리모델(빠름)이라 n 크게, ON은 전술 단발 반복(무거움)이라 병렬 필수."""
import sys, math, time
sys.stdout.reconfigure(encoding='utf-8')
from engine_campaign import monte_carlo_campaign, load_forecast_model


def finite(x):
    return isinstance(x, (int, float)) and math.isfinite(x)


def check(mc, label):
    fails = []
    # 확률 [0,1] + 합=1
    for k in ('win_rate', 'draw_rate', 'loss_rate'):
        v = mc.get(k)
        if not (finite(v) and 0 <= v <= 1):
            fails.append(f"{label} {k} 범위/유한: {v}")
    s = mc.get('win_rate', 0) + mc.get('draw_rate', 0) + mc.get('loss_rate', 0)
    if abs(s - 1.0) > 1e-6:
        fails.append(f"{label} 승/무/패 합≠1: {s}")
    # 전 float 지표 NaN/Inf 없음
    for k, v in mc.items():
        if isinstance(v, float) and not math.isfinite(v):
            fails.append(f"{label} {k} NaN/Inf: {v}")
    return fails


def main():
    m = load_forecast_model()
    base = dict(fleet_preset='이지스 기동전단', enemy_fleet_preset='항모 킬 체인',
                weather='맑음 (주간)', enable_campaign_mode=True, campaign_horizon_h=72)
    all_fails = []

    # 정밀 OFF 대규모 (대리모델, n=300)
    t0 = time.time()
    off = monte_carlo_campaign(base, n=300, model=m)
    t_off = time.time() - t0
    all_fails += check(off, 'OFF')
    print(f"[OFF n=300] {t_off:.1f}s win={off['win_rate']} draw={off['draw_rate']} "
          f"loss={off['loss_rate']} ctrl={off.get('mean_control_avg')} "
          f"surv={off.get('surviving_avg')} cost={off.get('cost_avg'):.0f} "
          f"n_precise_avg={off.get('n_precise_avg')} parallel={off.get('parallel')}")

    # 정밀 ON 대규모 (전술 단발, n=200 병렬)
    t0 = time.time()
    on = monte_carlo_campaign(dict(base, enable_precise_engagement=True), n=200, model=m)
    t_on = time.time() - t0
    all_fails += check(on, 'ON')
    print(f"[ON  n=200] {t_on:.1f}s win={on['win_rate']} draw={on['draw_rate']} "
          f"loss={on['loss_rate']} ctrl={on.get('mean_control_avg')} "
          f"surv={on.get('surviving_avg')} cost={on.get('cost_avg'):.0f} "
          f"n_precise_avg={on.get('n_precise_avg')} parallel={on.get('parallel')}")

    print()
    if all_fails:
        print("🔴 안정성 FAIL:")
        for f in all_fails:
            print("  -", f)
        sys.exit(1)
    print("✅ 대규모 MC 안정성 PASS (NaN/Inf 0·확률범위·합=1)")
    print(f"기준값: OFF win={off['win_rate']} surv={off.get('surviving_avg')} | "
          f"ON win={on['win_rate']} surv={on.get('surviving_avg')} n_precise={on.get('n_precise_avg')}")


if __name__ == '__main__':
    main()
