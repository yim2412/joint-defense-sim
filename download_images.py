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
# ══════════════════════════════════════════════════════════════════════════════
SEARCH_QUERIES = {
    # ── 중국 전투기 ──────────────────────────────────────────────────────────
    'J-20 (위룡)':           'J-20 fighter aircraft China',
    'J-35 (백상어)':          'FC-31 stealth fighter China fifth generation two engine',
    'J-10A (비맹)':           'Chengdu J-10 fighter jet',
    'J-10C (맹룡 개량)':      'J-10 C multirole fighter China PLAAF',
    'J-11B (플랭커-B)':       'Shenyang J-11 Flanker China fighter',
    'J-15 (비상어)':          'Shenyang J-15 carrier fighter Liaoning',
    'J-16 (플랭커-D)':        'J-16 China fighter PLAAF',
    'Su-35 (플랭커-E)':       'Sukhoi Su-35 flanker Russia fighter',
    'JH-7A (날치)':           'Xian JH-7 FBC-1 Flying Leopard',
    'MiG-29 (풀크럼)':        'Mikoyan MiG-29 Fulcrum fighter',
    'MiG-23 (플로거)':        'Mikoyan MiG-23 variable sweep wing',
    'J-7 (섬광)':             'Chengdu J-7 MiG-21 China',
    # ── 폭격기 ───────────────────────────────────────────────────────────────
    'H-6 (폭격기)':           'Xian H-6K bomber Chinese Air Force',
    'H-6N (폭격기 개량)':     'Xian H-6 China strategic bomber nuclear',
    'Tu-22M3 (백파이어)':     'Tupolev Tu-22M3 Backfire bomber',
    'Su-57 (펠론)':           'Sukhoi Su-57 PAK FA stealth fighter',
    # ── 탄도미사일 ───────────────────────────────────────────────────────────
    'DF-11A (단거리 탄도)':   'Dongfeng 16 ballistic missile parade China DF-16',
    'DF-15 (단거리 탄도)':    'Dongfeng-15 DF-15 ballistic missile China',
    'DF-21D (대함 탄도)':     'Dongfeng-21D anti-ship ballistic missile parade',
    'DF-26 (중장거리 탄도)':  'Dong-Feng 26 ballistic missile China',
    'DF-17 (극초음속 활공)':  'Dongfeng-17 DF-17 hypersonic glide vehicle',
    'YJ-21 (극초음속 대함)':  'YJ-21 hypersonic anti-ship China Type 055',
    'KN-23 (북한 이스칸데르)':'KN-23 North Korea short range ballistic missile',
    # ── 순항미사일 ───────────────────────────────────────────────────────────
    'CJ-10 (순항미사일)':     'CJ-10A DH-10 Changjian cruise missile China military parade',
    'YJ-12 (초음속 순항)':    'YJ-12 supersonic anti-ship missile China',
    'P-800 오닉스 (야혼트)':  'Yakhont P-800 Onyx anti-ship missile',
    'Kh-31A (항공기발사 대함)':'Kh-31 missile aircraft Russia',
    'YJ-100 (장거리 순항)':   'YJ-100 long range cruise missile PLAAF 2019',
    'YJ-18 (초음속 대함)':    'YJ-18 ASCM submarine launched China PLAN',
    'Kalibr (3M14 순항미사일)':'Kalibr 3M14 cruise missile Russia',
    # ── 대함 수상함 ──────────────────────────────────────────────────────────
    '022형 미사일 고속정':    'Type 022 Houbei missile boat China fast attack',
    '056형 초계함':           'Type 056 corvette China patrol vessel PLAN frigate',
    '054A형 호위함':          'Type 054A Jiangkai II frigate PLAN',
    '052D형 구축함':          'Type 052D Luyang III destroyer China',
    '055형 대형 구축함':      'Type 055 Nanchang DDG-101 destroyer PLAN',
    '052C형 구축함 (HHQ-9)':  'Type 052C Luyang II destroyer China',
    '071형 상륙함':           'Type 071 Yuzhao amphibious transport dock',
    # ── 잠수함 ───────────────────────────────────────────────────────────────
    '039형 잠수함 (송급)':    'Song class submarine Type 039 diesel China surfaced',
    '041형 잠수함 (위안급 개량)':'Yuan class submarine Type 041 China',
    '093형 잠수함 (상급)':    'Shang class submarine Type 093 China nuclear',
    '094형 잠수함 (진급)':    'Type 094 Jin class ballistic missile submarine',
    # ── 북한 ────────────────────────────────────────────────────────────────
    '화성-15 (북한 ICBM급)':  'Hwasong-15 intercontinental ballistic missile North Korea',
    '화성-17 (북한 ICBM 개량)':'Hwasong-17 DPRK intercontinental ballistic missile parade 2022',
    '화성-12 (IRBM)':         'Hwasong-12 ballistic missile North Korea',
    '화성-18 (ICBM 고체연료)': 'Hwasong-18 ICBM North Korea 2023',
    '북한 순항미사일 (화살-2)': 'Hwasal-2 cruise missile DPRK',
    'KN-24 (단거리 기동탄도)': 'KN-24 North Korea ballistic missile',
    '신포급 잠수함 (SLBM)':    'Pukguksong ballistic missile North Korea submarine launch',
    '해성-3 (잠수함발사 순항)': 'submarine launched cruise missile torpedo tube Korea',
    # ── 러시아 ───────────────────────────────────────────────────────────────
    '킨잘 (극초음속 탄도)':   'Kh-47M2 Kinzhal hypersonic aero-ballistic missile',
    '지르콘 (극초음속 순항)':  '3M22 Tsirkon Zircon hypersonic Russia missile',
    'Kh-101 (스텔스 순항)':   'Kh-101 Kh-102 cruise missile Russia',
    '우달로이급 구축함':       'Marshal Shaposhnikov destroyer Russia Udaloy',
    '슬라바급 순양함':         'Slava class cruiser Russia Moskva',
    '킬로급 잠수함 (Project 636)':'Kilo class submarine Project 636 Varshavyanka',
    '오스카-II급 SSGN':        'Oscar II class submarine Project 949A SSGN Russia',
    '야센급 SSGN':             'Yasen class submarine Russia nuclear',
    # ── 드론 ────────────────────────────────────────────────────────────────
    '소형 자폭 드론 (UAV)':    'Shahed-136 Iranian loitering munition kamikaze drone',
    '드론 떼 (Swarm-12)':      'military drone swarm unmanned aerial',
    # ── 아군 함정 ────────────────────────────────────────────────────────────
    'KDX-III':   'ROKS Sejong the Great DDG-991 Aegis destroyer Korea',
    'KDX-II':    'ROKS Chungmugong Yi Sun-sin DDH-975 destroyer Korea',
    'FFX':       'ROKS Incheon FFG frigate Republic of Korea Navy',
    'PKG':       'ROKS Yoon Young-ha patrol killer guided missile boat Korea',
    'PCC':       'ROKS Pohang class corvette Korean patrol',
    'PKX-B':     'Republic of Korea Navy patrol boat Chamsuri',
    'LPH':       'ROKS Dokdo LPH-6111 amphibious assault ship Korea',
    'AOE':       'ROKS Soyang AOE combat support ship Korea',
    'DDG-51':    'USS Arleigh Burke Flight III DDG-51 destroyer US Navy',
    'CG-47':     'USS Ticonderoga CG cruiser Aegis US Navy',
    'CVN':       'USS Ronald Reagan CVN aircraft carrier US Navy',
    'LPD':       'USS San Antonio LPD-17 amphibious ship US Navy',
    'SSN':       'USS Virginia SSN-774 nuclear submarine US Navy',
    'LST':       'Republic of Korea Navy landing ship tank LST',
    'AO':        'Republic of Korea Navy replenishment oiler ship',
    # ── 아군 무기 ────────────────────────────────────────────────────────────
    'SM-3 Block IIA':         'Standard Missile 3 Block IIA SM-3 launch',
    'SM-6':                   'Standard Missile 6 SM-6 ERAM launch',
    'SM-2 Block IIIB':        'Standard Missile 2 SM-2 Block III launch',
    'RIM-116 RAM':             'RIM-116 Rolling Airframe Missile RAM launcher',
    '홍상어 (대잠)':           'RUM-139 VL-ASROC vertical launch anti-submarine rocket',
    '청상어 (경어뢰)':         'lightweight torpedo anti-submarine aerial drop helicopter',
    'CIWS-II (Phalanx)':      'Phalanx close-in weapon system Block 1B',
    'Mk.46 경어뢰':            'Mark 46 Mod 5 lightweight torpedo US Navy',
    '해성-I (대함순항)':       'Korean anti-ship cruise missile surface launched frigate',
    '하푼 Block II (AGM-84)':  'AGM-84 Harpoon anti-ship missile',
    'ESSM Block II':           'Evolved Sea Sparrow RIM-162 missile launch',
    'SM-6 Block IB':           'Standard Missile 6 RIM-174 ERAM launch guided',
    'Tomahawk Block V':        'Tomahawk cruise missile BGM-109 launch',
}


# ══════════════════════════════════════════════════════════════════════════════
#  API 헬퍼
# ══════════════════════════════════════════════════════════════════════════════
_IMG_EXT = {'.jpg', '.jpeg', '.png', '.gif', '.svg', '.JPG', '.PNG'}


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
        save_path = os.path.join(SAVE_DIR, f'{name}.jpg')

        if os.path.exists(save_path):
            kb = os.path.getsize(save_path) // 1024
            print(f"[SKIP {i:02d}/{total}] {name}  ({kb} KB)")
            skipped += 1
            continue

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
