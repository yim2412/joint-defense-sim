# -*- coding: utf-8 -*-
"""p011 — 회귀 골든이 '파도 스폰' 경로를 감시하는가 (F-011 / F-003)

주장: 골든 42케이스 중 위협이 **파도(지연) 스폰**되는 케이스가 하나도 없다.
그래서 `_spawn_pending_threat` 경로(L2308~)의 동작이 바뀌어도 회귀가 PASS 한다.
F-009(stagger 중복 스폰)가 오래 살아 있었던 이유이기도 하다.

파도를 유발하는 경로는 둘:
  · `ai_tactic='stagger'`          — 저속 위협을 +30/+60초로 미룬다
  · `enemy_fleet_mode='mixed'`     — 1파만 즉시, 나머지는 지연

판정: `CASES`/`CAMPAIGN_CASES` 의 cfg 에 위 둘 중 하나라도 있는가.
  수정 전: 0건 (FAIL, exit 1)
  수정 후: 1건 이상 (PASS, exit 0)

사용: python analysis/probes/p011_golden_wave_coverage.py
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, 'audit_verify_regression.py')


def main():
    with open(SRC, encoding='utf-8') as f:
        src = f.read()

    stagger = len(re.findall(r"ai_tactic\s*=\s*'stagger'|'ai_tactic'\s*:\s*'stagger'", src))
    mixed = len(re.findall(r"enemy_fleet_mode\s*=\s*'mixed'|'enemy_fleet_mode'\s*:\s*'mixed'", src))
    total = stagger + mixed

    print('audit_verify_regression.py — 파도 스폰 유발 cfg')
    print('  ai_tactic=stagger      : %d건' % stagger)
    print('  enemy_fleet_mode=mixed : %d건' % mixed)
    print()
    if total == 0:
        print('[FAIL] 골든이 파도 스폰 경로를 한 번도 밟지 않는다.')
        print('       _spawn_pending_threat 이하의 동작 변화를 회귀가 못 잡는다.')
        return 1
    print('[PASS] 파도 스폰 경로가 골든에 %d건 포함돼 있다.' % total)
    return 0


if __name__ == '__main__':
    sys.exit(main())
