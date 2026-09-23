# -*- coding: utf-8 -*-
"""p018 — 위협 추적표의 '격추거리'가 실제로 채워지는가 (D4)

로드맵 D4 근거: *"격추거리 기본 설정에서 75% 공백"*. 유형(`?`)·탐지거리(0)는 v21.07.06~07 에서
이미 고쳐졌고, 남은 것이 격추거리였다. 원인은 기록 기준 — 요격탄↔표적 거리를 적었는데
근접신관 판정(≤200m) 순간이라 늘 0.0~0.2km, 표에서 '—' 로 보였다.
격추거리는 *"얼마나 멀리서 막았는가"* 라 **방어 함정↔표적** 거리여야 한다.

판정(P — 실행):
  ① 무기로 요격한 위협(기만기·회피 제외) 중 격추거리가 빈 것 0건
     (0.0km 도 값이다 — 함정 직상공 CIWS 격추를 '—' 로 지우던 것도 잡는다)
  ② 구역방공 요격(CIWS·RAM 제외) 중 격추거리 1km 미만 ≤ 5% — 근접신관 거리(≤0.2km)를
     적던 옛 기준이면 100% 가 된다
  ③ 요격된 위협 중 격추 무기가 빈 것 0건

사용: python analysis/probes/p018_threat_table_fill.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from engine_combat import run_v7_simulation           # noqa: E402

PRESETS = ['랴오닝 항모전단', '북한 탄도 포화', '입체 포화 (최강)']
NON_SAM = ('음향 기만기', '회피 기동')
POINT = ('CIWS', 'RAM', '골키퍼', 'Goalkeeper')   # 근접방어 — 1km 안이 정상
MIN_KM = 1.0         # 근접신관 거리(0.2km)와 확실히 구분되는 하한
MAX_BLANK = 0.05


def main():
    bad = []
    for efp in PRESETS:
        cfg = dict(enemy_fleet_mode='preset', fleet_preset='이지스 기동전단',
                   enemy_fleet_preset=efp, weather='맑음 (주간)', sim_seed=7)
        evs = run_v7_simulation(cfg)['active_events']
        ok = [e for e in evs if e.intercepted]
        sam = [e for e in ok if e.intercept_weapon not in NON_SAM]
        blank = [e for e in sam if e.intercept_km is None]
        area = [e for e in sam if not any(k in e.intercept_weapon for k in POINT)]
        near = [e for e in area if e.intercept_km is not None and e.intercept_km < MIN_KM]
        no_wpn = [e for e in ok if not e.intercept_weapon]
        rate = len(near) / len(area) if area else 0.0
        kms = sorted(e.intercept_km for e in sam if e.intercept_km is not None)
        med = kms[len(kms) // 2] if kms else 0.0
        print('%-14s 위협 %3d · 요격 %3d · 격추거리 공백 %d · 구역방공 1km 미만 %d/%d (%.0f%%) · 무기 공백 %d · 중앙 %.1fkm'
              % (efp, len(evs), len(ok), len(blank), len(near), len(area), rate * 100, len(no_wpn), med))
        if blank:
            bad.append('%s: 격추거리 공백 %d건' % (efp, len(blank)))
        if rate > MAX_BLANK:
            bad.append('%s: 구역방공 격추거리 1km 미만 %.0f%%(근접신관 거리를 적고 있다)' % (efp, rate * 100))
        if no_wpn:
            bad.append('%s: 격추 무기 공백 %d건' % (efp, len(no_wpn)))
    print()
    if bad:
        print('[FAIL] 위협 추적표에 빈칸이 남았다:')
        for b in bad:
            print('   · %s' % b)
        return 1
    print('[PASS] 요격된 위협마다 격추 무기·격추거리(함정 기준)가 채워진다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
