# -*- coding: utf-8 -*-
"""
app_changelog.json → 유형별 정리 문서 생성기 (빌드 제외 도구).

변경이력/ 폴더에 유형별 마크다운을 생성한다:
  README.md          — 통계 + 인덱스
  00_전체연표.md      — 전 버전 시간순(최신 위)
  01_기능추가.md      — '추가' 항목
  02_버그수정.md      — '수정' 중 버그성
  03_수치·밸런스.md   — '수정' 중 수치·밸런스성
  04_개선.md          — '개선·변경' 항목
  05_삭제.md          — '삭제' 항목

changelog 갱신 후 재실행하면 문서가 최신화된다:
    python _changelog_export.py
"""
import json
import io
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, '변경이력')

# '수정' 항목을 버그 vs 수치·밸런스로 가르는 휴리스틱 키워드
_NUMERIC_HINTS = (
    '→', '상향', '하향', '증강', '감소', '조정', '확대', '축소', '강화', '규모',
    'km', '발', '%', '×', '배', '셀', '재고', '사거리', '속도', '마하', 'kts',
    '반경', '확률', '편성', '준수', '현실화', '정합', 'VLS', '톤',
)
# 버그도 수치도 아닌 메타성 수정(기능 승격·계획 갱신 등) → 개선으로 보냄
_META_HINTS = (
    '승격', '향후 계획', "'실험적'", '정규 기능', '정규 옵션', '로드맵', '레이블',
)


def _classify_mod(text: str) -> str:
    """'수정' 항목을 'imp'(메타)·'num'(수치)·'bug'(버그)로 분류."""
    if any(k in text for k in _META_HINTS):
        return 'imp'
    if any(k in text for k in _NUMERIC_HINTS):
        return 'num'
    return 'bug'


def _bucket(change: str) -> str:
    head = change.strip()[:2]
    if head == '추가':
        return 'add'
    if head == '삭제':
        return 'del'
    if head == '수정':
        return _classify_mod(change)
    return 'imp'   # 개선·변경 등


def _body(change: str) -> str:
    """접두어(추가/수정/삭제/개선/변경) 떼고 본문만."""
    s = change.strip()
    for pre in ('추가', '수정', '삭제', '개선', '변경'):
        if s.startswith(pre):
            return s[len(pre):].strip()
    return s


def main():
    data = json.load(open(os.path.join(ROOT, 'app_changelog.json'), encoding='utf-8'))
    os.makedirs(OUT, exist_ok=True)

    # 유형별 수집: (version, date, title, body)
    buckets = {'add': [], 'bug': [], 'num': [], 'imp': [], 'del': []}
    for e in data:
        ver, date, title = e.get('version', ''), e.get('date', ''), e.get('title', '')
        for c in e.get('changes', []):
            buckets[_bucket(c)].append((ver, date, title, _body(c)))

    meta = {
        'add': ('01_기능추가.md', '🆕 기능 추가', '새로 도입된 기능·시스템'),
        'bug': ('02_버그수정.md', '🐞 버그 수정', '증상·오류가 고쳐진 변경'),
        'num': ('03_수치·밸런스.md', '⚖️ 수치·밸런스 조정', '제원·재고·편성·확률 등 수치 변경'),
        'imp': ('04_개선.md', '✨ 개선', 'UI·표시·성능 개선 + 기능 승격·계획 갱신 등'),
        'del': ('05_삭제.md', '🗑️ 삭제', '제거된 기능·항목'),
    }

    def write_section(fname, heading, desc, rows):
        # 최신 위로: changelog는 오래된→최신이므로 역순
        lines = [f'# {heading}', '', f'> {desc} · 총 **{len(rows)}건**',
                 '', '| 버전 | 날짜 | 내용 |', '|------|------|------|']
        for ver, date, _title, body in reversed(rows):
            safe = body.replace('|', '\\|').replace('\n', ' ')
            lines.append(f'| `{ver}` | {date} | {safe} |')
        lines.append('')
        open(os.path.join(OUT, fname), 'w', encoding='utf-8').write('\n'.join(lines))

    for key, (fname, heading, desc) in meta.items():
        write_section(fname, heading, desc, buckets[key])

    # 전체 연표 — 버전별 묶음(최신 위)
    chrono = ['# 📜 전체 변경 연표', '',
              f'> 전 버전 시간순(최신 위) · 총 **{len(data)}개 버전** '
              f'({data[0]["date"]} ~ {data[-1]["date"]})', '']
    for e in reversed(data):
        chrono.append(f'## `{e.get("version","")}` · {e.get("date","")} — {e.get("title","")}')
        for c in e.get('changes', []):
            chrono.append(f'- {c.strip()}')
        chrono.append('')
    open(os.path.join(OUT, '00_전체연표.md'), 'w', encoding='utf-8').write('\n'.join(chrono))

    # README — 통계·인덱스
    counts = {k: len(v) for k, v in buckets.items()}
    rm = [
        '# 변경이력 정리', '',
        f'`app_changelog.json`을 유형별로 자동 분류한 문서입니다. '
        f'changelog 갱신 후 `python _changelog_export.py`로 재생성합니다.', '',
        '## 통계', '',
        f'- 총 버전: **{len(data)}개** ({data[0]["date"]} ~ {data[-1]["date"]})',
        f'- 🆕 기능 추가: **{counts["add"]}건**',
        f'- 🐞 버그 수정: **{counts["bug"]}건**',
        f'- ⚖️ 수치·밸런스: **{counts["num"]}건**',
        f'- ✨ 개선: **{counts["imp"]}건**',
        f'- 🗑️ 삭제: **{counts["del"]}건**', '',
        '## 문서', '',
        '- [전체 연표](00_전체연표.md) — 전 버전 시간순',
        '- [기능 추가](01_기능추가.md)',
        '- [버그 수정](02_버그수정.md)',
        '- [수치·밸런스](03_수치·밸런스.md)',
        '- [개선](04_개선.md)',
        '- [삭제](05_삭제.md)', '',
        '> 분류는 changelog 접두어(추가/수정/삭제/개선)와 수치 키워드 휴리스틱 기반입니다. '
        "'수정'은 수치 키워드(→·km·발·재고 등) 포함 여부로 버그/수치를 가릅니다.", '',
    ]
    open(os.path.join(OUT, 'README.md'), 'w', encoding='utf-8').write('\n'.join(rm))

    print(f'생성 완료 → {OUT}')
    print(f'  버전 {len(data)} · 추가{counts["add"]} 버그{counts["bug"]} '
          f'수치{counts["num"]} 개선{counts["imp"]} 삭제{counts["del"]}')


if __name__ == '__main__':
    main()
