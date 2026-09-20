# -*- coding: utf-8 -*-
"""p006 — 짝(기능 간 의존) 지도를 정적으로 만들 수 있는가 (F-006)

규약 2.1-7 은 *"기능 간 의존(짝) 지도"* 를 만들라고 했는데 **방법을 안 적었다.**
정적 방법(코드에서 함께 등장하는 토글 찾기)으로 되는지 재현한다.

판정: 정적으로 뽑히는 '짝 후보'가 **실제 짝을 담고 있는가**.
  실제 짝의 표본: 레이더 침묵(enable_radar_off) ↔ 회피 기동(enable_evasion)
  — v20.5 에서 *"회피 기동이 OFF면 레이더 침묵이 죽는다"* 로 확인된 물리적 의존이다.

결과(2026-09-20): 후보 6건 중 절반이 주석·테스트이고, **위 실제 짝은 한 줄에 함께
등장하지 않는다** → 정적 방법은 부적합. 규약을 '효과 측정의 부산물' 로 고쳤다.
"""
import collections
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
REAL_PAIR = ('enable_radar_off', 'enable_evasion')


def main():
    pairs = collections.Counter()
    for f in sorted(os.listdir(ROOT)):
        if not (f.startswith('engine_') and f.endswith('.py')):
            continue
        for line in io.open(os.path.join(ROOT, f), encoding='utf-8-sig',
                            errors='replace').read().split('\n'):
            fl = set(re.findall(r'enable_\w+', line))
            if len(fl) >= 2:
                pairs[tuple(sorted(fl))] += 1

    print('엔진에서 한 줄에 토글 2개 이상 등장 = 정적 "짝 후보" %d종' % len(pairs))
    for k, c in pairs.most_common():
        print('   x%-3d %s' % (c, ' + '.join(x.replace('enable_', '') for x in k)))

    found = any(set(REAL_PAIR) <= set(k) for k in pairs)
    print()
    print('실제 짝 %s 가 후보에 있는가: %s' % (' ↔ '.join(REAL_PAIR), '예' if found else '**아니오**'))
    if found:
        print('[PASS] 정적 방법이 실제 짝을 잡는다.')
        return 0
    print('[확인] 정적 방법으로는 실제 짝을 못 잡는다 — 규약 2.1-7 을')
    print('       "효과 측정의 부산물로만 만든다"로 고친 근거다(F-006).')
    return 0


if __name__ == '__main__':
    sys.exit(main())
