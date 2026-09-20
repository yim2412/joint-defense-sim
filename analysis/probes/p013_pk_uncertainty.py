# -*- coding: utf-8 -*-
"""p013 — Pk 불확실성 토글이 실제로 발현하는가 (F-013)

`enable_pk_uncertainty` 는 요격 확률을 실행당 Beta 표집으로 뽑는다.
발현 조건은 **요격이 실제로 일어나는 무대**다 — 요격 0이면 Pk 를 바꿔도 결과가 같다.

판정: 같은 seed·같은 편성에서 ON/OFF 결과가 달라야 한다(델타 != 0).
  기본 OFF 라 이 프로브가 '죽은 토글' 여부를 지키는 유일한 실행 검사다.

사용: python analysis/probes/p013_pk_uncertainty.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from engine_combat import run_v7_simulation          # noqa: E402

BASE = dict(enemy_fleet_mode='preset', fleet_preset='이지스 기동전단',
            enemy_fleet_preset='랴오닝 항모전단', weather='흐림', sim_seed=7)
KEYS = ('intercept_rate', 'intercepted_threats', 'total_threats')


def main():
    off = run_v7_simulation(dict(BASE))
    on = run_v7_simulation(dict(BASE, enable_pk_uncertainty=True))
    print('무대: 이지스 기동전단 vs 랴오닝 항모전단 · seed 7')
    delta = {}
    for k in KEYS:
        a, b = off.get(k, 0) or 0, on.get(k, 0) or 0
        delta[k] = b - a
        print('  %-22s OFF %-10s ON %-10s 델타 %+.4g' % (k, round(a, 4), round(b, 4), b - a))
    print()
    if any(abs(v) > 1e-9 for v in delta.values()):
        print('[PASS] ON/OFF 델타가 있다 — 토글이 살아 있다.')
        return 0
    print('[FAIL] bit-identical — 죽은 토글이다(발현 무대가 없거나 게이트 버그).')
    return 1


if __name__ == '__main__':
    sys.exit(main())
