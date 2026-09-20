# -*- coding: utf-8 -*-
"""p011b — 엔진이 소비하는 토글을 회귀 골든이 켜는가 (F-011 잔여)

주장(착수 시): `EFFECT_ALIVE`(효과가 확증된 토글) 중 **골든이 한 번도 켜지 않는 것**이
있으면 그 경로의 동작 변화를 회귀가 못 잡는다. 기본 True 라 암묵적으로 밟히는 것은
제외하고, **기본 False 인데 골든이 안 켜는 것**만 센다.

  수정 전: 11개 미커버 (asw_forward · autonomous_engagement · battle_mode ·
           campaign_fog · cec_jammed · laser_dew · minesweeping · multibearing ·
           random_placement · ras_rearm · recon_drone)
  수정 후: 남은 것만 (전장·캠페인 전용 경로는 별도 스모크가 본다)

사용: python analysis/probes/p011b_golden_toggle_coverage.py
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 전장(run_battle)·캠페인 전용 경로는 단발 골든이 아니라 전용 케이스·스모크가 본다.
OTHER_PATH = {'enable_battle_mode', 'enable_campaign_fog'}


def main():
    scan = io.open(os.path.join(ROOT, 'audit_static_scan.py'), encoding='utf-8').read()
    m = re.search(r'EFFECT_ALIVE = \{(.*?)\n\}', scan, re.S)
    alive = set(re.findall(r"'(\w+)'", m.group(1))) if m else set()

    eng = ''
    for f in os.listdir(ROOT):
        if f.startswith('engine_') and f.endswith('.py'):
            eng += io.open(os.path.join(ROOT, f), encoding='utf-8-sig', errors='replace').read()

    gold = io.open(os.path.join(ROOT, 'audit_verify_regression.py'), encoding='utf-8').read()
    used = set(re.findall(r'enable_\w+', gold))

    missing = []
    for t in sorted(alive - used - OTHER_PATH):
        # 기본 True 면 골든이 명시하지 않아도 ON 상태로 밟힌다 → 미커버가 아니다
        if re.search(r"get\('%s',\s*True\)" % t, eng):
            continue
        missing.append(t)

    print('EFFECT_ALIVE %d개 · 골든이 켜는 토글 %d개' % (len(alive), len(used)))
    print('전장·캠페인 전용(별도 경로) 제외: %s' % ', '.join(sorted(OTHER_PATH)))
    print()
    if missing:
        print('[FAIL] 기본 OFF 인데 골든이 한 번도 안 켜는 토글 %d개:' % len(missing))
        for t in missing:
            print('   %s' % t)
        print('       이 경로의 동작이 바뀌어도 회귀가 PASS 한다.')
        return 1
    print('[PASS] 단발 경로의 EFFECT_ALIVE 토글을 골든이 전부 밟는다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
