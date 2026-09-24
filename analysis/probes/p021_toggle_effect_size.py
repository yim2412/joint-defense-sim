# -*- coding: utf-8 -*-
"""p021 — 실험적 전술 토글의 효과 크기 (규약 2.2C, D5 → D3 승격 근거)

`audit_effect`·`audit_dead_toggle` 은 고정 seed 한 번으로 '델타가 있나'만 본다.
승격 게이트는 **크기**를 요구한다 — 같은 seed 로 OFF/ON 을 짝지어 N회 돌리고,
짝 차이의 평균과 95% 구간을 낸다. 구간이 0을 품으면 'N회로는 효과가 구분 안 됨'이다.

무대는 `audit_dead_toggle.SCENARIOS` 의 발현 무대를 그대로 쓴다(짝 기능 포함) —
무대를 여기서 새로 정하면 스캐너와 측정이 서로 다른 것을 잰다.

사용: python analysis/probes/p021_toggle_effect_size.py [N] [workers]
"""
import math
import os
import statistics as st
import sys
import time
from concurrent.futures import ProcessPoolExecutor

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

# 토글 → audit_dead_toggle 무대 이름. cyber 는 그 목록에 없어 audit_effect 무대를 쓴다.
TARGETS = [
    ('enable_esm_arm',           'SEAD'),
    ('enable_sonar_emcon',       '대잠'),
    ('enable_asw_contact_limit', '대잠EMCON'),
    ('enable_hgv_glide',         '극초음속'),
    # 레이저: 11개 무대 중 발동은 '대잠'(2)·'어뢰근접'(8)뿐(seed 7). 연안저고도는 발동 0 —
    # 드론이 근접권에 오기 전에 함포·SAM 이 다 잡는다([[project-laser-efficacy-finding]]).
    ('enable_laser_dew',         '어뢰근접'),
    ('enable_cyber_warfare',     '@audit_effect'),
]
METRICS = ('intercept_rate', 'friendly_hits', 'friendly_ships_lost',
           'enemy_ships_destroyed', 'total_cost', 'laser_kills')
N_DEFAULT = 100
Z95 = 1.96
PROGRESS = os.path.join(os.path.expanduser('~'), '.claude', 'bg-progress.txt')


def _stage(toggle, name):
    if name == '@audit_effect':
        from audit_effect import PROBES
        return dict(PROBES[toggle][0])
    from audit_dead_toggle import SCENARIOS
    return dict(dict(SCENARIOS)[name])


def _one(args):
    toggle, name, seed, on = args
    from engine_combat import run_v7_simulation
    cfg = _stage(toggle, name)
    cfg.update(sim_seed=seed, mc_mode=True)     # mc_mode 는 결과 불변(p020 확인), 메모리만 평탄
    cfg[toggle] = on
    r = run_v7_simulation(cfg)
    return toggle, seed, on, {k: float(r.get(k, 0) or 0) for k in METRICS}


def _progress(done, total, t0):
    try:
        el = time.time() - t0
        with open(PROGRESS, 'w', encoding='utf-8') as f:
            f.write('p021 토글 효과 크기 %d/%d (%d%%) · 남음 약 %d분\n'
                    % (done, total, 100 * done // total,
                       round(el / done * (total - done) / 60) if done else 0))
    except OSError:
        pass


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else N_DEFAULT
    w = int(sys.argv[2]) if len(sys.argv) > 2 else max(1, (os.cpu_count() or 2) - 2)
    jobs = [(t, s, seed, on) for t, s in TARGETS for seed in range(1, n + 1) for on in (False, True)]
    res = {}
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=w) as ex:
        for i, (t, seed, on, m) in enumerate(ex.map(_one, jobs, chunksize=4), 1):
            res[(t, seed, on)] = m
            _progress(i, len(jobs), t0)
    try:
        os.remove(PROGRESS)
    except OSError:
        pass
    print('seed 1..%d 짝 비교 · %d회 실행 · %.0f초' % (n, len(jobs), time.time() - t0))
    for t, s in TARGETS:
        print('\n%s  (무대: %s)' % (t, s))
        for k in METRICS:
            off = [res[(t, i, False)][k] for i in range(1, n + 1)]
            d = [res[(t, i, True)][k] - res[(t, i, False)][k] for i in range(1, n + 1)]
            mu, sd = st.mean(d), st.pstdev(d)
            half = Z95 * sd / math.sqrt(n)
            nz = sum(1 for x in d if abs(x) > 1e-12)
            tag = '구분됨' if (mu - half > 0 or mu + half < 0) else ('델타 0' if nz == 0 else '0 포함')
            print('  %-22s OFF평균 %-12.4g 델타 %+.4g ±%.3g  [%s · 달라진 seed %d/%d]'
                  % (k, st.mean(off), mu, half, tag, nz, n))
    return 0


if __name__ == '__main__':
    sys.exit(main())
