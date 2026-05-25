# download_images.py
# 스펙시트 패널용 유닛 이미지 자동 다운로드
# 방식: Wikimedia Commons 검색+imageinfo 복합 API → 정확한 썸네일 URL → 저장
#
# 실행: python download_images.py
# 결과: assets/images/{유닛명}.jpg  (이미 존재하면 스킵)

import os, sys, time, json
import urllib.request, urllib.parse, urllib.error

# 콘솔 인코딩 보정 (Windows cp949)
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ── 저장 폴더 ─────────────────────────────────────────────────────────────────
SAVE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'assets', 'images')

_UA = 'AegisSimulator/1.0 (educational; contact: yimdlawns@gmail.com)'
_COMMONS_API = 'https://commons.wikimedia.org/w/api.php'
THUMB_WIDTH = 320

# ══════════════════════════════════════════════════════════════════════════════
#  유닛별 검색어  (키 = spec_db.py / ENEMY_DB 키와 정확히 일치)
#  전략: 서구 무기(미국/NATO)는 액션 쿼리, 비서구는 단순 명칭 쿼리
# ══════════════════════════════════════════════════════════════════════════════
SEARCH_QUERIES = {
    # ── 중국 전투기 ──────────────────────────────────────────────────────────
    'J-20 (위룡)':           'Chengdu J-20 aircraft',
    'J-35 (백상어)':          'FC-31 stealth fighter China fifth generation',     # 유저 제공
    'J-10A (비맹)':           'Chengdu J-10 aircraft',
    'J-10C (맹룡 개량)':      'J-10C multirole fighter China PLAAF',              # 유저 제공
    'J-11B (플랭커-B)':       'Shenyang J-11 aircraft China',
    'J-15 (비상어)':          'Shenyang J-15 carrier fighter',
    'J-16 (플랭커-D)':        'Shenyang J-16 aircraft',
    'Su-35 (플랭커-E)':       'Su-35 Flanker E Russia fighter aircraft',
    'JH-7A (날치)':           'Xian JH-7 Flying Leopard aircraft',
    'MiG-29 (풀크럼)':        'MiG-29 Fulcrum fighter aircraft',
    'MiG-23 (플로거)':        'MiG-23 Flogger fighter aircraft',
    'J-7 (섬광)':             'Chengdu J-7 aircraft China',
    # ── 폭격기 ───────────────────────────────────────────────────────────────
    'H-6 (폭격기)':           'H-6K bomber China PLAAF Xian',
    'H-6N (폭격기 개량)':     'Xian H-6 China strategic bomber',                  # 유저 제공
    'Tu-22M3 (백파이어)':     'Tu-22M3 Backfire bomber Russia',
    'Su-57 (펠론)':           'Su-57 PAK FA stealth fighter Russia',
    # ── 탄도미사일 ───────────────────────────────────────────────────────────
    'DF-11A (단거리 탄도)':   'Dong Feng 11 ballistic missile China',
    'DF-15 (단거리 탄도)':    'DF-15 ballistic missile China',
    'DF-21D (대함 탄도)':     'DF-21D anti-ship ballistic missile China',
    'DF-26 (중장거리 탄도)':  'Dong-Feng 26 ballistic missile China',
    'DF-17 (극초음속 활공)':  'DF-17 hypersonic glide vehicle China',
    'YJ-21 (극초음속 대함)':  'YJ-21 hypersonic anti-ship China Type 055',        # 유저 제공 예정
    'KN-23 (북한 이스칸데르)':'KN-23 North Korea short range ballistic missile',  # 유저 제공
    # ── 순항미사일 ───────────────────────────────────────────────────────────
    'CJ-10 (순항미사일)':     'CJ-10A DH-10 Changjian cruise missile China parade', # 유저 제공 예정
    'YJ-12 (초음속 순항)':    'YJ-12 anti-ship missile China',
    'P-800 오닉스 (야혼트)':  'P-800 Onyx Yakhont anti-ship missile Russia',
    'Kh-31A (항공기발사 대함)':'Kh-31 anti-ship missile Russia aircraft',
    'YJ-100 (장거리 순항)':   'YJ-100 long range cruise missile PLAAF 2019',      # 유저 제공
    'YJ-18 (초음속 대함)':    'YJ-18 anti-ship missile China PLAN',               # 유저 제공
    'Kalibr (3M14 순항미사일)':'Kalibr 3M14 cruise missile Russia',
    # ── 대함 수상함 ──────────────────────────────────────────────────────────
    '022형 미사일 고속정':    'Type 022 Houbei missile boat China PLAN',
    '056형 초계함':           'Type 056 corvette China PLAN patrol frigate',       # 유저 제공
    '054A형 호위함':          'Type 054A Jiangkai frigate China PLAN',
    '052D형 구축함':          'Luyang III destroyer China',
    '055형 대형 구축함':      'Type 055 destroyer China PLAN Nanchang',
    '052C형 구축함 (HHQ-9)':  'Type 052C Luyang II destroyer China PLAN',
    '071형 상륙함':           'Type 071 amphibious transport dock China PLAN',
    # ── 잠수함 ───────────────────────────────────────────────────────────────
    '039형 잠수함 (송급)':    'Song class submarine Type 039 diesel China',        # 유저 제공
    '041형 잠수함 (위안급 개량)':'Yuan class submarine diesel China',
    '093형 잠수함 (상급)':    'Shang class submarine China',
    '094형 잠수함 (진급)':    'Type 094 Jin SSBN China submarine',
    # ── 북한 ────────────────────────────────────────────────────────────────
    '화성-15 (북한 ICBM급)':  'Hwasong-15 North Korea ICBM ballistic missile',
    '화성-17 (북한 ICBM 개량)':'Hwasong-17 North Korea ICBM parade',              # 유저 제공 예정
    '화성-12 (IRBM)':         'Hwasong-12 North Korea IRBM ballistic missile',
    '화성-18 (ICBM 고체연료)': 'Hwasong-18 ICBM North Korea 2023',                # 유저 제공
    '북한 순항미사일 (화살-2)': 'Hwasal-2 cruise missile North Korea',
    'KN-24 (단거리 기동탄도)': 'KN-24 North Korea ballistic missile',
    '신포급 잠수함 (SLBM)':    'Sinpo-C submarine SLBM DPRK North Korea',
    '해성-3 (잠수함발사 순항)': 'Korean submarine launched cruise missile SLCM',  # 유저 제공
    # ── 러시아 ───────────────────────────────────────────────────────────────
    '킨잘 (극초음속 탄도)':   'Kh-47M2 Kinzhal hypersonic missile Russia',
    '지르콘 (극초음속 순항)':  '3M22 Zircon hypersonic missile Russia',
    'Kh-101 (스텔스 순항)':   'Kh-101 Kh-102 cruise missile Russia',
    '우달로이급 구축함':       'Udaloy destroyer Russia Pacific Navy',
    '슬라바급 순양함':         'Slava class cruiser Russia Navy',
    '킬로급 잠수함 (Project 636)':'Kilo submarine Russia diesel-electric Project 636',
    '오스카-II급 SSGN':        'Oscar II SSGN submarine Russia',
    '야센급 SSGN':             'Yasen submarine Russia nuclear attack',
    # ── 드론 ────────────────────────────────────────────────────────────────
    # ── 아군 함정 ────────────────────────────────────────────────────────────
    'KDX-III':   'ROKS Sejong Great Aegis destroyer Korea Navy',
    'KDX-II':    'Chungmugong Yi Sun-sin destroyer Korea Navy',
    'FFX':       'ROKS Incheon FFG frigate Korea Navy underway',
    'PKG':       'Korea Navy patrol killer guided missile boat',                   # 유저 제공
    'PCC':       'ROKS Pohang corvette Korea Navy patrol',
    'PKX-B':     'Republic of Korea Navy PKX patrol boat',
    'LPH':       'ROKS Dokdo amphibious assault ship Korea Navy',
    'AOE':       'ROKS Cheonji replenishment ship Korea',
    'DDG-51':    'USS Arleigh Burke destroyer underway firing',
    'CG-47':     'USS Ticonderoga cruiser underway sea',
    'CVN':       'USS Ronald Reagan aircraft carrier underway flight deck',
    'LPD':       'USS San Antonio LPD amphibious ship underway',
    'SSN':       'USS Virginia submarine surfaced underway',
    'LST':       'Korea Navy landing ship tank LST',
    'AO':        'replenishment oiler underway Navy fuel',
    # ── 아군 무기 ────────────────────────────────────────────────────────────
    'SM-3 Block IIA':         'Standard Missile 3 SM-3 launch fire ship',
    'SM-6':                   'Standard Missile 6 SM-6 launch fire',
    'SM-2 Block IIIB':        'Standard Missile 2 SM-2 launch fire ship',
    'RIM-116 RAM':             'RIM-116 RAM Rolling Airframe Missile launch fire',
    '홍상어 (대잠)':           'VL-ASROC vertical launch anti-submarine rocket',
    '청상어 (경어뢰)':         'lightweight torpedo anti-submarine aerial helicopter', # 유저 제공
    'CIWS-II (Phalanx)':      'Phalanx CIWS firing close-in weapon system',
    'Mk.46 경어뢰':            'Mark 46 torpedo anti-submarine lightweight',
    '해성-I (대함순항)':       'Korean anti-ship cruise missile surface launched',  # 유저 제공
    '하푼 Block II (AGM-84)':  'Harpoon AGM-84 anti-ship missile launch aircraft',
    'ESSM Block II':           'ESSM Evolved Sea Sparrow missile launch fire',
    'SM-6 Block IB':           'Standard Missile 6 SM-6 Block IB vertical launch',
    'Tomahawk Block V':        'Tomahawk cruise missile launch ship fire',
}


# ══════════════════════════════════════════════════════════════════════════════
#  API 헬퍼
# ══════════════════════════════════════════════════════════════════════════════
_IMG_EXT = {'.jpg', '.jpeg', '.png', '.gif', '.svg', '.JPG', '.PNG'}
_SKIP_EXT = ('.jpg', '.jpeg', '.png', '.webp')  # 스킵 판정에 사용할 확장자


def _api_get(params: dict) -> dict:
    url = _COMMONS_API + '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'User-Agent': _UA})
    with urllib.request.urlopen(req, timeout=12) as r:
        return json.loads(r.read())


def find_thumb_url(query: str, width: int = THUMB_WIDTH) -> tuple[str | None, str | None]:
    """
    1) generator=search 로 이미지 파일 검색
    2) prop=imageinfo + iiurlwidth 로 실제 썸네일 URL 가져오기
    반환: (thumb_url, filename)  또는  (None, None)
    """
    params = {
        'action': 'query',
        'generator': 'search',
        'gsrsearch': query,
        'gsrnamespace': '6',
        'gsrlimit': '8',
        'prop': 'imageinfo',
        'iiprop': 'url|mime',
        'iiurlwidth': str(width),
        'format': 'json',
    }
    data = _api_get(params)
    pages = data.get('query', {}).get('pages', {})
    if not pages:
        return None, None

    for page in sorted(pages.values(), key=lambda p: p.get('index', 99)):
        title = page.get('title', '')
        fname = title[5:] if title.startswith('File:') else title
        ext = os.path.splitext(fname)[1]
        if ext not in _IMG_EXT:
            continue
        ii_list = page.get('imageinfo', [])
        if not ii_list:
            continue
        thumb = ii_list[0].get('thumburl') or ii_list[0].get('url')
        if thumb:
            return thumb, fname

    return None, None


def download_url(url: str, save_path: str) -> int:
    """URL 다운로드 → 파일 저장. 반환: 파일 크기(bytes)."""
    req = urllib.request.Request(url, headers={'User-Agent': _UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = r.read()
    if len(data) < 1500:
        raise ValueError(f"파일 너무 작음 ({len(data)} bytes)")
    with open(save_path, 'wb') as f:
        f.write(data)
    return len(data)


# ══════════════════════════════════════════════════════════════════════════════
#  메인
# ══════════════════════════════════════════════════════════════════════════════
def main():
    os.makedirs(SAVE_DIR, exist_ok=True)
    total   = len(SEARCH_QUERIES)
    ok      = 0
    skipped = 0
    failed  = []

    print(f"저장 폴더: {SAVE_DIR}")
    print(f"대상 유닛: {total}종  |  썸네일 너비: {THUMB_WIDTH}px")
    print("-" * 64)

    for i, (name, query) in enumerate(SEARCH_QUERIES.items(), 1):
        # .jpg / .png / .webp 모두 체크 (유저 제공 파일 포함)
        img_base = os.path.join(SAVE_DIR, name)
        existing = next(
            (img_base + ext for ext in _SKIP_EXT if os.path.exists(img_base + ext)),
            None
        )
        if existing:
            kb = os.path.getsize(existing) // 1024
            ext_label = os.path.splitext(existing)[1]
            print(f"[SKIP {i:02d}/{total}] {name}  ({kb} KB{ext_label})")
            skipped += 1
            continue

        save_path = img_base + '.jpg'

        # 1) 검색 + imageinfo (한 번의 API 호출)
        try:
            thumb_url, fname = find_thumb_url(query)
            time.sleep(0.3)
        except Exception as e:
            print(f"[FAIL {i:02d}/{total}] {name}  → API 오류: {str(e)[:60]}")
            failed.append(name)
            continue

        if not thumb_url:
            print(f"[FAIL {i:02d}/{total}] {name}  → 이미지 없음")
            failed.append(name)
            continue

        # 2) 썸네일 다운로드
        try:
            nbytes = download_url(thumb_url, save_path)
            kb = nbytes // 1024
            print(f"[ OK  {i:02d}/{total}] {name}  ({kb} KB)  [{fname}]")
            ok += 1
            time.sleep(0.35)
        except urllib.error.HTTPError as e:
            print(f"[FAIL {i:02d}/{total}] {name}  → HTTP {e.code}  ({fname})")
            failed.append(name)
        except Exception as e:
            print(f"[FAIL {i:02d}/{total}] {name}  → {str(e)[:70]}")
            failed.append(name)

    # 요약
    print()
    print("=" * 64)
    print(f"완료  : {ok}개 다운로드 성공")
    print(f"스킵  : {skipped}개 이미 존재")
    print(f"실패  : {len(failed)}개")
    if failed:
        print()
        print("실패 항목 (SEARCH_QUERIES 검색어 수정 후 재실행):")
        for n in failed:
            print(f"  {n!r}: {SEARCH_QUERIES[n]!r}")
    print()
    pct = (ok + skipped) / total * 100
    if len(failed) == 0:
        print("모든 이미지 준비 완료.")
    else:
        print(f"진행률 {pct:.0f}% — 나머지는 아이콘으로 대체 표시됩니다.")


if __name__ == '__main__':
    main()
