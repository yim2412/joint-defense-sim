# -*- coding: utf-8 -*-
"""p009 — 시차 공격(stagger)의 첫 편성 항목 중복 스폰 (F-009)

주장: `ai_tactic='stagger'` 에서 **모든 위협이 저속**이면 `new_fleet` 이 비고,
전부 `_pending_threats` 로 들어간 뒤 `fleet_cfg[:1]` 이 **즉시 한 번 더** 스폰된다
(pending 에서 빼지 않는다) → 첫 편성 항목만 수량이 두 배가 된다.

  engine_combat.py:2038  fleet_cfg = new_fleet if new_fleet else fleet_cfg[:1]

판정: 편성표 수량과 실제 생성된 객체 수를 이름별로 대조한다.
  수정 전: 자폭 USV 12 -> 24 (FAIL, exit 1)
  수정 후: 편성표와 일치        (PASS, exit 0)

사용: python analysis/probes/p009_stagger_duplicate_spawn.py
"""
import collections
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from engine_combat import run_v7_simulation          # noqa: E402
from engine_core import ENEMY_FLEET_PRESETS          # noqa: E402

PRESET = '항만 침투 복합'      # 전부 저속(USV 14 · 022형 18.5 · 드론 28 m/s) → stagger 폴백 경로


def main():
    want = collections.Counter()
    for spec in ENEMY_FLEET_PRESETS[PRESET]:
        want[spec['preset']] += spec.get('count', 1)

    cfg = dict(enemy_fleet_mode='preset', enemy_fleet_preset=PRESET,
               weather='맑음 (주간)', sim_seed=7, ai_tactic='stagger')
    r = run_v7_simulation(cfg)
    got = collections.Counter(getattr(e, 'name', '?') for e in (r.get('enemy_ships') or []))

    print('편성 %s · ai_tactic=stagger' % PRESET)
    print('  %-24s %8s %8s' % ('위협', '편성표', '실제'))
    bad = []
    for name in sorted(set(want) | set(got)):
        w, g = want[name], got[name]
        mark = '' if w == g else '   <-- 불일치'
        if w != g:
            bad.append((name, w, g))
        print('  %-24s %8d %8d%s' % (name, w, g, mark))

    print()
    if bad:
        print('[FAIL] 편성표와 실제가 다르다: %s'
              % ', '.join('%s %d->%d' % (n, w, g) for n, w, g in bad))
        print('       stagger 가 도착 시점만 흩어야 하는데 전력을 늘렸다.')
        return 1
    print('[PASS] 편성표와 실제 생성 수가 일치한다 — stagger 는 도착 시점만 흩는다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
