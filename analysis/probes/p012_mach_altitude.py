# -*- coding: utf-8 -*-
"""p012 — 마하 판정의 고도 의존성 (F-012)

주장: `audit_db_consistency` 가 마하를 **해수면 음속 340 m/s 고정**으로 환산해
고고도 무기를 '표기 과장'으로 오판한다.

  audit_db_consistency.py  _MACH_MS = 340.0
  engine_combat.py:318     isa_atmosphere(alt_m)  ← 엔진은 고도별 대기를 쓴다
  engine_core.py:658       Tu-22M3 altitude_m = 11000, missile_speed_ms = 1500

사용: python analysis/probes/p012_mach_altitude.py
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from engine_core import ENEMY_DB                     # noqa: E402

MACH_SEA = 340.0            # 도구가 쓰는 상수
GAMMA, R = 1.4, 287.05      # ISA


def sound_speed(alt_m):
    """ICAO 표준대기 음속(m/s)."""
    if alt_m < 11000:
        T = 288.15 - 0.0065 * alt_m
    elif alt_m < 20000:
        T = 216.65
    else:
        T = 216.65 + 0.001 * (alt_m - 20000)
    return math.sqrt(GAMMA * R * T)


def main():
    name = 'Tu-22M3 (백파이어)'
    info = ENEMY_DB[name]
    v = info['missile_speed_ms']
    alt = info['altitude_m']

    print('%s — %s' % (name, info['missile_name']))
    print('  DB: missile_speed_ms=%s · altitude_m=%s' % (v, alt))
    print()
    print('  %-22s %6s  %s' % ('기준', '음속', '마하수'))
    print('  %-22s %6.0f  %.2f   <- 도구의 판정 근거' % ('해수면(도구 상수 340)', MACH_SEA, v / MACH_SEA))
    for a in (11000, 20000, 40000):
        s = sound_speed(a)
        mark = '   <- DB 가 명시한 순항 고도' if a == alt else ''
        print('  %-22s %6.0f  %.2f%s' % ('ISA %dm' % a, s, v / s, mark))

    m_db = v / sound_speed(alt)
    print()
    if m_db >= 5.0 > v / MACH_SEA:
        print('[판정] 확인됨 — 순항 고도(%dm)에서 마하 %.2f 로 극초음속 문턱(5)을 넘는다.' % (alt, m_db))
        print('       도구의 HIGH 판정은 해수면 고정 환산이 만든 **오탐**이다.')
        return 0
    print('[판정] 재현 실패 — 주장 철회 필요 (고도 반영해도 마하 %.2f)' % m_db)
    return 1


if __name__ == '__main__':
    sys.exit(main())
