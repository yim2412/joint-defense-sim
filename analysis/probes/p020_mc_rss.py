# -*- coding: utf-8 -*-
"""p020 — MC 워커가 장시간 돌면 메모리가 쌓이는가 (D5, 규약 2.4-5)

`_mc_batch_worker` 는 한 프로세스에서 수백 회를 gc 호출 없이 돈다. 회차마다 RSS 가
쌓이면 워커 수만큼 곱해져 MC 가 길수록 메모리가 터진다.

판정 두 단계 — 측정 도구를 먼저 의심한다:
  ① 대조: mc_mode=False(프레임·로그 누적)는 순환 참조 쓰레기로 RSS 가 **늘어야 한다**.
     안 늘면 이 측정이 증가를 볼 수 없는 것이라 ②의 PASS 도 의미가 없다.
  ② 본판: mc_mode=True(MC 워커 경로)는 첫 회 이후 증가가 문턱 이하여야 한다.

2026-09-24 실측(120회): MC 모드 138→143MB, 매회 gc.collect() 시 137MB 고정, gc 소요 7.0초/257초(2.7%).
비-MC 모드는 30회 만에 313→385MB — 앞서 p019 가 병렬로 돌며 본 5.4GB 는 이쪽이었다.

사용: python analysis/probes/p020_mc_rss.py [MC회차]
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)

import psutil                                          # noqa: E402
from engine_combat import run_v7_simulation            # noqa: E402

BASE = dict(enemy_fleet_mode='preset', fleet_preset='이지스 기동전단',
            enemy_fleet_preset='랴오닝 항모전단', weather='흐림')
N_MC = 60
N_CONTROL = 20
MC_GROWTH_MAX_MB = 30      # 실측 증가 +5MB(60·120회 모두)의 6배 — 흔들림 여유
CONTROL_GROWTH_MIN_MB = 30  # 대조군 실측 20회 +233MB. 이보다 작으면 측정 불능


def _grow(n, mc_mode):
    p = psutil.Process()
    run_v7_simulation(dict(BASE, sim_seed=1, mc_mode=mc_mode))   # 임포트·캐시 워밍업
    start = p.memory_info().rss
    for s in range(2, n + 2):
        run_v7_simulation(dict(BASE, sim_seed=s, mc_mode=mc_mode))
    return (p.memory_info().rss - start) / 2 ** 20


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else N_MC
    mc = _grow(n, True)            # 본판 먼저 — 대조군 쓰레기가 시작 RSS 를 오염시키지 않게
    ctl = _grow(N_CONTROL, False)
    print('① 대조 mc_mode=False %d회: RSS %+.0fMB (최소 %dMB 늘어야 측정 가능)'
          % (N_CONTROL, ctl, CONTROL_GROWTH_MIN_MB))
    if ctl < CONTROL_GROWTH_MIN_MB:
        print('[FAIL] 대조군이 안 늘었다 — 이 측정은 증가를 못 본다.')
        return 1
    print('② 본판 mc_mode=True  %d회: RSS %+.0fMB (문턱 %dMB)' % (n, mc, MC_GROWTH_MAX_MB))
    if mc > MC_GROWTH_MAX_MB:
        print('[FAIL] MC 워커 경로에서 메모리가 쌓인다.')
        return 1
    print('[PASS] MC 워커 경로는 장시간 실행에도 평탄하다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
