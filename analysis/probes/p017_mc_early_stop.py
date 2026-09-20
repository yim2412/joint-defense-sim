# -*- coding: utf-8 -*-
"""p017 — MC 가 수렴하면 멈추는가 (F-017 / D2)

로드맵 근거 3: *"조기 수렴 종료 없음(`ConvergenceWidget` 은 표시 전용)."*
반복 질의가 본질인 트레이드 스터디에서 **수렴한 뒤에도 끝까지 도는 것**은 낭비다.
MC 실행량 축소(10,000→1,000, 묶음 C-4)로 절반은 해결됐고 남은 절반이 이것이다.

판정: 평균이 충분히 안정된 뒤 남은 회차를 건너뛰는가.
  `monte_carlo_v7(..., n=big)` 을 돌려 **실제 수행 회차 `n_runs`** 가 n 보다 작으면 PASS.
  (수렴 판정은 요격률 누적 평균의 표준오차가 문턱 이하로 유지되는지로 본다)

사용: python analysis/probes/p017_mc_early_stop.py
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from engine_combat import monte_carlo_v7             # noqa: E402
from app_utils import sim_mode_preset                # noqa: E402

# UI 의 '표준' 모드가 실제로 넘기는 문턱으로 잰다 — 엔진 기본값(0=끄기)이 아니라
# **사용자가 실제로 밟는 경로**를 검증해야 한다(F-017 배선: mixin_simlifecycle).
TOL = sim_mode_preset(1).get('conv_tol', 0.0)
CFG = dict(enemy_fleet_mode='preset', fleet_preset='이지스 기동전단',
           enemy_fleet_preset='랴오닝 항모전단', weather='맑음 (주간)', sim_seed=7,
           mc_converge_tol=TOL)
N = 200


def main():
    t0 = time.time()
    mc = monte_carlo_v7(dict(CFG), n=N)
    el = time.time() - t0
    ran = mc.get('n_runs', N)
    print('표준 모드 문턱 tol=%s · 요청 %d회 · 실제 수행 %s회 · %.1fs' % (TOL, N, ran, el))
    print('  평균 요격률 %.4f · 표준편차 %.4f'
          % (mc.get('mean_intercept', 0), mc.get('std_intercept', 0)))
    print()
    if ran < N:
        print('[PASS] 수렴 후 조기 종료했다 — %d회 절약(%.0f%%).' % (N - ran, (N - ran) / N * 100))
        return 0
    print('[FAIL] 요청한 %d회를 전부 돌았다 — 표준 모드 문턱(%s)에서도 안 멈춘다.' % (N, TOL))
    return 1


if __name__ == '__main__':
    sys.exit(main())
