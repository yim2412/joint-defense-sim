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
THRESH = 1.5    # 기준 대비 배율 임계(급증 = 성능 회귀)
THRESH_LOW = 0.5  # 기준 대비 급감 임계(= 측정 오류 의심)

# ── 기준선 하한 가드 (2026-09-12 신설, v21 감사 메타 회고) ──────────────────
# **시간만 재면 잘못된 기준선을 못 잡는다.** v21 감사에서 전장 기준이 89ms로 저장돼
# 있었는데, 1200초 지평 전장 시뮬이 89ms일 수 없다(0.074ms/초). 그런데도 오래
# 방치된 이유는 기준선에 **"얼마나 일했는가"가 없었기** 때문이다 — 89ms라는 숫자만
# 봐서는 빠른 건지 시뮬이 안 돈 건지 구별할 방법이 없었다.
# → 실행시간과 **일감(work)** 을 함께 저장·대조한다. 일감 단위당 시간이 하한 미만이면
#   "빠르다"가 아니라 **"측정이 틀렸다"** 로 판정한다.
_WORK_KEY = {'single': 'sim_time', 'battle': 'sim_time', 'campaign': 'end_h'}
# 일감 1단위당 최소 실행시간(ms). 실측(single 667ms/3334s=0.20 · battle 570/1200=0.475
# · campaign 32/26h=1.23)의 약 1/4을 하한으로 잡았다 — 정상 변동은 통과시키고
# 물리적으로 불가능한 값만 걸러낸다. 89ms 사례(battle 0.074)는 이 하한에 걸린다.
_MIN_MS_PER_WORK = {'single': 0.05, 'battle': 0.10, 'campaign': 0.30}


def _time(fn, cfg, work_key=None, n=N):
    """(중앙값 실행시간, 일감) 반환. 일감을 함께 재야 '안 돈 것'과 '빠른 것'이 구별된다."""
    ts, work = [], None
    for _ in range(n):
        t = time.perf_counter()
        res = fn(dict(cfg))
        ts.append(time.perf_counter() - t)
        if work is None and isinstance(res, dict):
            work = res.get(work_key) if work_key else None
    return statistics.median(ts), work


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

    raw = {
        'single':   _time(run_v7_simulation, single, _WORK_KEY['single']),
        'battle':   _time(run_battle_simulation, battle, _WORK_KEY['battle']),
        'campaign': _time(lambda c: run_campaign(c, model=model), camp,
                          _WORK_KEY['campaign']),
    }
    cur = {k: {'sec': v[0], 'work': v[1]} for k, v in raw.items()}
    print(f"실행시간(중앙값 of {N}회) · 일감 대비 단가:")
    for k, d in cur.items():
        per = (d['sec'] * 1000 / d['work']) if d['work'] else float('nan')
        print(f"  {k:9s} {d['sec']*1000:8.1f} ms   일감 {d['work']}  "
              f"({per:.3f} ms/단위, 하한 {_MIN_MS_PER_WORK[k]})")

    # ── 하한 가드: 저장 전에 **타당성부터** 본다 ──────────────────────────────
    # 이 검사가 없어서 89ms가 기준으로 굳었다. 말이 안 되는 값은 기준이 될 수 없다.
    implausible = []
    for k, d in cur.items():
        if not d['work']:
            implausible.append(f"{k}: 일감을 못 읽음(결과 키 '{_WORK_KEY[k]}' 부재)")
            continue
        per = d['sec'] * 1000 / d['work']
        if per < _MIN_MS_PER_WORK[k]:
            implausible.append(
                f"{k}: {per:.3f} ms/단위 < 하한 {_MIN_MS_PER_WORK[k]} "
                f"({d['sec']*1000:.1f}ms에 일감 {d['work']} 소화 — 물리적으로 불가)")
    if implausible:
        print("=" * 56)
        print("🔴 측정 오류 의심 — 시뮬이 실제로 돌지 않았을 수 있다:")
        for x in implausible:
            print(f"  🔴 {x}")
        print("  → 원인을 규명하기 전에는 기준선으로 저장하지 않는다"
              "(v21 감사 '전장 89ms' 사례).")
        return 1

    if update or not os.path.exists(BASELINE):
        with open(BASELINE, 'w', encoding='utf-8') as f:
            json.dump(cur, f, ensure_ascii=False, indent=2)
        print(f"✅ 성능 기준 저장 → {os.path.basename(BASELINE)}")
        return 0

    with open(BASELINE, encoding='utf-8') as f:
        base = json.load(f)
    bad, warn = [], []
    for k, d in cur.items():
        b = base.get(k)
        if not b:
            continue
        # 구형식(float = 초) 하위호환 — 일감 없이 저장된 옛 기준선도 읽는다.
        bs = b['sec'] if isinstance(b, dict) else b
        bw = b.get('work') if isinstance(b, dict) else None
        v = d['sec']
        # ① 일감 불일치 = 같은 이름으로 **다른 것을 재고 있다**(시나리오·설정 변경).
        #    시간 비교 자체가 무의미해지므로 급증보다 먼저 본다.
        if bw is not None and d['work'] is not None and d['work'] != bw:
            bad.append(f"{k}: 일감 {bw} → {d['work']} (다른 것을 재고 있다 — "
                       f"시나리오/설정이 바뀌었는지 확인)")
            continue
        if v > bs * THRESH:
            bad.append(f"{k}: {v*1000:.1f}ms > 기준 {bs*1000:.1f}ms (×{v/bs:.2f}) 성능 회귀")
        elif v < bs * THRESH_LOW:
            # ② 급감 — 진짜 최적화일 수도, 측정 오류일 수도. 위 타당성 가드를
            #    통과했으므로 FAIL은 아니고 '확인 요구'로 남긴다.
            warn.append(f"{k}: {v*1000:.1f}ms < 기준 {bs*1000:.1f}ms (×{v/bs:.2f}) — "
                        f"의도된 최적화면 --update, 아니면 측정 조건 확인")
    print(f"{'='*56}")
    for x in warn:
        print(f"  🟡 {x}")
    if bad:
        print(f"⚠ 성능 이상 {len(bad)}건:")
        for x in bad:
            print(f"  🔴 {x}")
        return 1
    print(f"✅ 성능 PASS — 전 경로 기준 대비 {THRESH_LOW}~{THRESH}배 이내 · 일감 일치"
          + (f" (급감 경고 {len(warn)}건)" if warn else ""))
    return 0


if __name__ == '__main__':
    sys.exit(main())
