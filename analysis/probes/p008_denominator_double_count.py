# -*- coding: utf-8 -*-
"""p008 — 무력화율 분모(_n_tot)의 이중 계산 재현 프로브 (F-008)

주장: `neutralization_rate` 의 분모 `total_threats + suicide_threats` 에서,
**파도 스폰된 자폭 플랫폼은 양쪽에 모두 들어가 두 번 세어진다.**

  engine_combat.py:2306  파도 스폰 -> total_threats += 1   (if/else 밖이라 플랫폼도 증가)
  engine_combat.py:5655  suicide_threats = len([자폭 플랫폼])
  engine_combat.py:5675  _n_tot = total_threats + suicide_threats

초기 편성 자폭 플랫폼은 L2172 의 `if(미사일)` 가지에서만 +1 하므로 이중이 아니다
→ **같은 위협이 스폰 경로에 따라 분모 기여가 1 또는 2가 된다.**

사용: python analysis/probes/p008_denominator_double_count.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from engine_combat import run_v7_simulation          # noqa: E402
from engine_core import ENEMY_FLEET_PRESETS          # noqa: E402

PRESET = '항만 침투 복합'      # 자폭 USV 12 + 022형 4 + 연안 자폭 드론 …


def main():
    comp = ENEMY_FLEET_PRESETS[PRESET]
    n_sui_spec = sum(c.get('count', 1) for c in comp
                     if '자폭' in str(c.get('preset', '')))
    print('편성 %s' % PRESET)
    print('  편성표의 자폭 계열 수: %d' % n_sui_spec)

    base = dict(enemy_fleet_mode='preset', enemy_fleet_preset=PRESET,
                weather='맑음 (주간)', sim_seed=7)
    tag = sys.argv[1] if len(sys.argv) > 1 else 'none'
    if tag == 'stagger':
        base['ai_tactic'] = 'stagger'
    print('  전술: %s' % tag)
    r = run_v7_simulation(base)

    tot = r.get('total_threats', 0)
    sui = r.get('suicide_threats', 0)
    itc = r.get('intercepted_threats', 0)
    sui_n = r.get('suicide_neutralized', 0)
    n_tot = tot + sui
    n_itc = itc + sui_n

    print('  total_threats        = %d' % tot)
    print('  suicide_threats      = %d' % sui)
    print('  intercepted_threats  = %d' % itc)
    print('  suicide_neutralized  = %d' % sui_n)
    print('  intercept_rate       = %.4f  (= %d / %d)' % (r.get('intercept_rate', 0), itc, tot))
    print('  neutralization_rate  = %.4f  (= %d / %d)' % (r.get('neutralization_rate', 0), n_itc, n_tot))

    # 판정: 분모에서 자폭 플랫폼이 두 번 세어졌는가.
    # enemy_ships 목록에서 실제 자폭 플랫폼 수를 세어 대조한다.
    ships = r.get('enemy_ships', []) or []
    real_sui = [et for et in ships
                if getattr(et, 'is_aircraft', False) or et.info.get('is_suicide')]
    print('  실제 생성된 자폭 계열 객체 수 = %d' % len(real_sui))
    import collections
    print('  전체 객체 %d · 이름별: %s' % (len(ships),
          dict(collections.Counter(getattr(e, 'name', '?') for e in ships))))

    print()
    if sui > 0 and tot > 0:
        print('[판정] 분모 %d = total_threats %d + suicide_threats %d' % (n_tot, tot, sui))
        print('       total_threats 안에 이미 파도 스폰 플랫폼이 들어 있으면 그만큼 이중이다.')
        print('       위 수치를 편성표(%d)·실제 객체(%d)와 대조해 판정할 것.'
              % (n_sui_spec, len(real_sui)))
    else:
        print('[판정] 이 편성에서는 자폭 집계가 0 — 다른 편성으로 재시도할 것.')


if __name__ == '__main__':
    main()
