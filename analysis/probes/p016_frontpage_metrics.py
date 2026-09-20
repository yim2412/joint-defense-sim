# -*- coding: utf-8 -*-
"""p016 — 1면 카드가 '편성 비교가 성립하는 지표'를 담고 있는가 (F-016 / D1)

재측정 근거(로드맵 2026-09-20): 같은 적에 대해 함정 1척 45.8% vs 6척 47.0% —
**요격률은 1면 헤드라인인데 편성을 1.2%p 로밖에 구분하지 못한다.** 분모(총 위협)가
편성마다 달라서다(62 vs 122). 반면 **교환비·요격당 비용·방어 포화도**는 분모가
편대 자신이거나 비용이라 편성이 달라도 같은 기준으로 비교된다.

판정(S — 정적 구성 검사):
  ① 1면 카드(`card_defs`)에 교환비·요격당 비용이 있는가
  ② 요격률 카드가 **분모를 함께 보여주는가**(값 옆 또는 툴팁에 '중 N발')

사용: python analysis/probes/p016_frontpage_metrics.py
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, 'mixin_resultpanel.py')


def main():
    s = io.open(SRC, encoding='utf-8-sig').read()
    m = re.search(r'card_defs = \[(.*?)\]', s, re.S)
    if not m:
        print('[FAIL] card_defs 를 못 찾았다 — 구조가 바뀌었다.')
        return 1
    block = m.group(1)
    keys = re.findall(r"\(\s*'([^']+)'\s*,\s*'(\w+)'\s*\)", block)
    print('1면 카드 %d개: %s' % (len(keys), ', '.join(k for _, k in keys)))

    bad = []
    have = {k for _, k in keys}
    if 'exchange' not in have:
        bad.append('피아 교환비(exchange)가 1면에 없다')
    if 'cost_per_kill' not in have:
        bad.append('요격당 비용(cost_per_kill)이 1면에 없다')
    # 요격률 분모 표기
    if not re.search(r"_intercept_denom|중 \{|발 중", s):
        bad.append('요격률에 분모 표기가 없다(= "미사일 N발 중 M발")')

    print()
    if bad:
        print('[FAIL] 편성 비교가 성립하지 않는 1면:')
        for b in bad:
            print('   · %s' % b)
        print('       근거: 1척 45.8%% vs 6척 47.0%% — 요격률만으로는 편성을 고를 수 없다.')
        return 1
    print('[PASS] 분모가 편성에 안 걸리는 지표가 1면에 있고, 요격률은 분모를 함께 보여준다.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
