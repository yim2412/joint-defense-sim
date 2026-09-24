# -*- coding: utf-8 -*-
"""p019 — Pk 불확실성이 MC 산포에 얼마를 더하는가 (D5, F-013 후속)

p013 은 '토글이 살아 있는가'(델타 != 0)만 본다. 승격 판단에 필요한 것은 **크기**다:
기준 산포(seed 만 바꿨을 때의 표준편차)에 Pk 표집이 얼마를 더하는가.

측정: 같은 seed 집합으로 OFF/ON 을 각각 N회 → 평균·표준편차·분산 증가분.
분산 차이는 표본 오차가 커서 부트스트랩 95% 구간을 같이 낸다 — 구간이 0을 품으면
"더해지는 산포가 N회로는 구분되지 않는다"가 정직한 결론이다.

사용: python analysis/probes/p019_pk_uncertainty_spread.py [N] [workers]
"""
import os
import random
import statistics as st
import sys
import time
from concurrent.futures import ProcessPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

BASE = dict(enemy_fleet_mode='preset', fleet_preset='이지스 기동전단',
            enemy_fleet_preset='랴오닝 항모전단', weather='흐림')
N_DEFAULT = 60
BOOT = 2000
PROGRESS = os.path.join(os.path.expanduser('~'), '.claude', 'bg-progress.txt')


def _one(args):
    seed, on = args
    from engine_combat import run_v7_simulation
    r = run_v7_simulation(dict(BASE, sim_seed=seed, enable_pk_uncertainty=on))
    return seed, on, float(r.get('intercept_rate', 0) or 0)


def _boot_var_diff(off, on, rng):
    d = []
    for _ in range(BOOT):
        a = [rng.choice(off) for _ in off]
        b = [rng.choice(on) for _ in on]
        d.append(st.pvariance(b) - st.pvariance(a))
    d.sort()
    return d[int(0.025 * BOOT)], d[int(0.975 * BOOT)]


def _progress(done, total, t0):
    try:
        el = time.time() - t0
        rem = el / done * (total - done) if done else 0
        with open(PROGRESS, 'w', encoding='utf-8') as f:
            f.write('p019 Pk 산포 %d/%d (%d%%) · 남음 약 %d분\n'
                    % (done, total, 100 * done // total, round(rem / 60)))
    except OSError:
        pass


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else N_DEFAULT
    w = int(sys.argv[2]) if len(sys.argv) > 2 else max(1, (os.cpu_count() or 2) // 2)
    jobs = [(s, on) for s in range(1, n + 1) for on in (False, True)]
    res = {False: [], True: []}
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=w) as ex:
        for i, (_, on, v) in enumerate(ex.map(_one, jobs), 1):
            res[on].append(v)
            _progress(i, len(jobs), t0)
    try:
        os.remove(PROGRESS)
    except OSError:
        pass
    off, on = res[False], res[True]
    lo, hi = _boot_var_diff(off, on, random.Random(0))
    print('무대: 이지스 기동전단 vs 랴오닝 항모전단 · 흐림 · seed 1..%d · %.0f초' % (n, time.time() - t0))
    print('  OFF 요격률 평균 %.4f  표준편차 %.4f' % (st.mean(off), st.pstdev(off)))
    print('  ON  요격률 평균 %.4f  표준편차 %.4f' % (st.mean(on), st.pstdev(on)))
    add = st.pvariance(on) - st.pvariance(off)
    print('  분산 증가 %.6f  (부트스트랩 95%% %.6f ~ %.6f)' % (add, lo, hi))
    print('  Pk 표집이 더하는 표준편차 ≈ %.4f' % (add ** 0.5 if add > 0 else 0.0))
    print('  평균 이동 %+.4f' % (st.mean(on) - st.mean(off)))
    if lo > 0:
        print('[결론] 산포 증가가 %d회로 구분된다.' % n)
    else:
        print('[결론] 구간이 0을 품는다 — %d회로는 산포 증가가 구분되지 않는다.' % n)
    return 0


if __name__ == '__main__':
    sys.exit(main())
