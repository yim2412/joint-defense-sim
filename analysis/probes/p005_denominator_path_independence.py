# -*- coding: utf-8 -*-
"""p005 — 요격률 분모가 스폰 경로에 독립인가 (F-005 / F-008)

**정의**: `total_threats` 는 **발사체(미사일류)만** 센다.
플랫폼(항공기·함정·자폭정)은 `suicide_threats`(자폭) 또는 `enemy_ships_destroyed`(격침)로
센다. 그래야 ①분모가 스폰 경로에 독립이고 ②무력화율 분모가 자폭 플랫폼을 두 번 세지 않는다.

현재는 두 곳이 다르다:
  초기 편성(L2183)  `if(미사일)` 가지 안에서 += 1   ← 플랫폼 제외 (정의대로)
  파도 스폰(L2317)  `if/else` **밖**에서 += 1        ← 플랫폼 포함 (정의 위반)

판정은 **S형식(구조 불변식)** 이다 — 수치 임계값은 교전 타이밍에 흔들리지만 구조는 안 흔들린다.
`_spawn_pending_threat` 안의 `total_threats += 1` 이 **미사일 가지 안에** 있어야 한다.

증거(골든 실측): `파도-시차공격#2` total_threats=44 vs 같은 편성 파도 없음 32 —
차이 **12 = 파도로 스폰된 플랫폼 수**(022형 4 + 연안 자폭 드론 8).

사용: python analysis/probes/p005_denominator_path_independence.py
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SRC = os.path.join(ROOT, 'engine_combat.py')
INC = "self.stats['total_threats'] += 1"


def _indent(line):
    return len(line) - len(line.lstrip())


def main():
    lines = io.open(SRC, encoding='utf-8-sig').read().split('\n')

    # 1) 파도 스폰 함수 구간
    start = next(i for i, l in enumerate(lines) if 'def _spawn_pending_threat' in l)
    end = next(i for i in range(start + 1, len(lines))
               if lines[i].strip().startswith('def ') and _indent(lines[i]) <= _indent(lines[start]))
    body = lines[start:end]

    # 2) 그 안의 증가 지점과, 그 위의 else: 위치
    inc = [i for i, l in enumerate(body) if INC in l]
    els = [i for i, l in enumerate(body) if l.strip() == 'else:']
    if not inc:
        print('[FAIL] _spawn_pending_threat 안에서 %s 를 못 찾았다 — 구조가 바뀌었다.' % INC)
        return 1

    i_inc = inc[0]
    i_else = max([e for e in els if e < i_inc], default=None)
    print('engine_combat.py  _spawn_pending_threat (L%d~L%d)' % (start + 1, end))
    print('  증가 지점  L%-6d 들여쓰기 %d  %s' % (start + i_inc + 1, _indent(body[i_inc]), INC))
    if i_else is not None:
        print('  직전 else  L%-6d 들여쓰기 %d' % (start + i_else + 1, _indent(body[i_else])))

    # 3) 판정: 증가가 else 블록보다 **얕으면** if/else 밖 = 플랫폼도 센다
    if i_else is None:
        print('\n[FAIL] 미사일/플랫폼 분기(else:)를 못 찾았다 — 판정 불가.')
        return 1
    if _indent(body[i_inc]) <= _indent(body[i_else]):
        print('\n[FAIL] 증가가 if/else **밖**에 있다 — 파도 스폰된 플랫폼도 분모에 들어간다.')
        print('       초기 편성(L2183)은 미사일 가지 안에서만 세므로 **정의가 경로마다 다르다.**')
        print('       골든 증거: 파도-시차공격#2 total=44 vs 파도 없음 32 (차이 12 = 파도 플랫폼 수)')
        return 1
    print('\n[PASS] 증가가 미사일 가지 안에 있다 — 분모는 발사체만 센다(경로 독립).')
    return 0


if __name__ == '__main__':
    sys.exit(main())
