# -*- coding: utf-8 -*-
"""analysis/refresh_anchors.py — 발견 대장의 인용 라인 번호 재조정 (제안 → 사람 확인)

왜 있나: B단계에서 코드를 고칠 때마다 **다른 발견의 인용 라인이 밀린다.**
2026-09-20 하루에만 네 번 손으로 고쳤다(F-005·F-007·F-008·F-013·F-004).
규약 1.2 는 *"코드가 바뀌어 앵커가 안 맞으면 자동 갱신하지 않는다 — 그 발견이 아직
유효한지는 사람이 판단할 일"* 이라고 정했다. 그래서 이 도구는 **고치지 않고 제안만** 한다:

  · 앵커 텍스트가 **파일 어딘가에 그대로 있으면**  → 단순 라인 이동으로 보고 새 번호를 제안
  · 앵커 텍스트가 **사라졌으면**                    → `[판단 필요]` 로 표시하고 건드리지 않는다
    (그 줄을 고쳤다는 뜻이므로 발견이 아직 유효한지 사람이 봐야 한다)
  · 같은 앵커가 **여러 줄에 있으면**                → `[모호]` 로 표시하고 후보를 전부 보여 준다

사용:
    python analysis/refresh_anchors.py            # 제안만 출력(기본)
    python analysis/refresh_anchors.py --apply    # 단순 이동만 반영(판단 필요·모호는 제외)
"""
import argparse
import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
FINDINGS = os.path.join(HERE, 'FINDINGS.md')
LOC_RE = re.compile(r"^- 위치: (?P<path>[^\s:]+):(?P<line>\d+) `(?P<anchor>[^`]+)`(?P<rest>.*)$")


def main():
    ap = argparse.ArgumentParser(description='발견 대장 인용 라인 재조정(제안)')
    ap.add_argument('--apply', action='store_true',
                    help='단순 이동만 반영 — 판단 필요·모호 항목은 손대지 않는다')
    args = ap.parse_args()

    if not os.path.isfile(FINDINGS):
        print('FINDINGS.md 없음 — 할 일 없음')
        return 0

    lines = io.open(FINDINGS, encoding='utf-8').read().split('\n')
    cache = {}
    moved, gone, ambig, ok = [], [], [], 0
    fid = '?'

    for idx, raw in enumerate(lines):
        m = re.match(r'^### (F-\d+)', raw)
        if m:
            fid = m.group(1)
        m = LOC_RE.match(raw)
        if not m:
            continue
        path, line, anchor = m.group('path'), int(m.group('line')), m.group('anchor')
        full = os.path.join(REPO, path)
        if not os.path.isfile(full):
            gone.append((fid, path, line, anchor, '파일 없음'))
            continue
        if path not in cache:
            cache[path] = io.open(full, encoding='utf-8-sig', errors='replace').read().split('\n')
        src = cache[path]

        if 1 <= line <= len(src) and anchor.strip() in src[line - 1]:
            ok += 1
            continue
        hits = [i + 1 for i, l in enumerate(src) if anchor.strip() in l]
        if not hits:
            gone.append((fid, path, line, anchor, '앵커 텍스트가 사라졌다'))
        elif len(hits) > 1:
            ambig.append((fid, path, line, anchor, hits))
        else:
            moved.append((idx, fid, path, line, hits[0], anchor, m.group('rest')))

    print('인용 %d건 — 정상 %d · 이동 %d · 판단 필요 %d · 모호 %d'
          % (ok + len(moved) + len(gone) + len(ambig), ok, len(moved), len(gone), len(ambig)))
    for _, fid_, path, old, new, anchor, _r in moved:
        print('  [이동]      %-7s %s:%d → %d  `%s`' % (fid_, path, old, new, anchor[:44]))
    for fid_, path, old, anchor, why in gone:
        print('  [판단 필요] %-7s %s:%d  %s  `%s`' % (fid_, path, old, why, anchor[:40]))
    for fid_, path, old, anchor, hits in ambig:
        print('  [모호]      %-7s %s:%d  후보 %s  `%s`' % (fid_, path, old, hits[:5], anchor[:36]))

    if not args.apply:
        if moved:
            print('\n--apply 로 [이동] %d건만 반영한다(판단 필요·모호는 손대지 않는다).' % len(moved))
        return 0

    for idx, fid_, path, old, new, anchor, rest in moved:
        lines[idx] = '- 위치: %s:%d `%s`%s' % (path, new, anchor, rest)
    io.open(FINDINGS, 'w', encoding='utf-8', newline='\n').write('\n'.join(lines))
    print('\n[이동] %d건 반영. 판단 필요 %d · 모호 %d 는 그대로 두었다.'
          % (len(moved), len(gone), len(ambig)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
