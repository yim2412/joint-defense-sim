#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
audit_static_scan.py — 종합 감사 정적 스캐너 (빌드 제외 도구)

CLAUDE.md '종합 감사' 9영역 중 **정적 Grep으로 굳힐 수 있는 점검**을 자동화한다.
audit_verify_regression.py(엔진 동작 무결성)와 짝 — 이쪽은 코드를 실행하지 않고 소스만 본다.

처음 v15 블록 종합 감사(2026-06-23) 실전에서 손으로 친 Grep을 추출해 제작.
엔진/app_main 구조가 바뀌면 휴리스틱이 어긋날 수 있으니, FAIL은 항상 사람이 검토한다.

사용:  python audit_static_scan.py        # 전체 점검, 하나라도 FAIL이면 exit 1
점검 영역(약칭): ⑥위생(버전정합·gitignore·_PLANS stale·README 파일전수커버·파일명 stale버전스탬프)
              ①코드(_log가드·_record_frame가드·enable 3종세트·MC 3경로) ②DB(db_specsheet 정합) ⑧수치(전장 분모 가드)
"""
import os, re, sys, subprocess

# cp949 기본 콘솔(Windows)에서 '—'(em-dash) 등 출력 시 UnicodeEncodeError 방지
# (수동 PYTHONIOENCODING=utf-8 의존 제거 — v16.05 종합 감사 메타회고 반영)
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

ROOT = os.path.dirname(os.path.abspath(__file__))
def rd(name):
    with open(os.path.join(ROOT, name), encoding='utf-8') as f:
        return f.read()

results = []  # (영역, 이름, ok, 상세)
def check(area, name, ok, detail=''):
    results.append((area, name, bool(ok), detail))

# ── ⑥ 위생: APP_VERSION == 헤더 버전 == changelog 마지막 ──────────────────────
def chk_version():
    lau = rd('app_main.py')
    m = re.search(r'APP_VERSION\s*=\s*["\']([^"\']+)', lau)
    appv = m.group(1) if m else None
    hm = re.search(r'시뮬레이터\s+(v[\d.]+)', lau[:3000])
    hdr = hm.group(1) if hm else None
    import json
    cl = json.load(open(os.path.join(ROOT, 'app_changelog.json'), encoding='utf-8'))
    last = cl[-1]['version'] if cl else None
    ok = appv and appv == hdr == last
    check('⑥', '버전 정합(APP_VERSION=헤더=changelog 마지막)', ok,
          f"APP={appv} 헤더={hdr} changelog={last}")

# ── ⑥ 위생: gitignore 커버리지 + 민감 산출물 미추적 ──────────────────────────
def chk_gitignore():
    gi = rd('.gitignore')
    need = ['_rl_ppo_model', '_rl_ckpt/', 'cesium_token.txt', 'dist/', 'build/']
    miss = [p for p in need if p not in gi]
    check('⑥', 'gitignore 필수 패턴 커버', not miss, f"누락={miss}" if miss else 'OK')
    try:
        tracked = subprocess.check_output(['git', 'ls-files'], cwd=ROOT, text=True)
        bad = [l for l in tracked.splitlines()
               if re.search(r'_rl_ppo|_rl_ckpt|cesium_token|\.zip$|^dist/|^build/', l)]
        check('⑥', '민감 산출물 미추적', not bad, f"추적중={bad[:5]}" if bad else 'OK')
    except Exception as e:
        check('⑥', '민감 산출물 미추적', False, f'git 실패: {e}')

# ── ① 코드: self._log 내부 mc_mode 가드 ──────────────────────────────────────
def chk_log_guard():
    ev = rd('engine_combat.py')
    m = re.search(r'def _log\(self[^)]*\):\s*\n((?:\s+.*\n){1,4})', ev)
    body = m.group(1) if m else ''
    ok = 'self._mc_mode' in body and 'return' in body
    check('①', '_log() 내부 _mc_mode 가드', ok,
          'def _log에 if self._mc_mode: return 확인' if ok else '가드 누락 — MC 과출력 위험')

# ── ① 코드: _record_frame 호출이 if not _mc_mode 가드 ─────────────────────────
def chk_frame_guard():
    ev = rd('engine_combat.py').split('\n')
    bad = []
    for i, l in enumerate(ev):
        if re.search(r'\bself\._record_frame\(\)', l):
            # 위 3줄 내 if not self._mc_mode 가 있어야
            ctx = '\n'.join(ev[max(0, i-3):i])
            if 'if not self._mc_mode' not in ctx:
                bad.append(i + 1)
    check('⑨', '_record_frame 호출 _mc_mode 가드', not bad,
          f"미가드 라인={bad}" if bad else 'OK (frames MC 누적 폭발 방지)')

# ── ① 코드: v15 신규 enable 플래그 3종 세트 ──────────────────────────────────
def chk_flag_triplet():
    lau = rd('app_main.py'); ev = rd('engine_combat.py')
    # 블록에서 추가된 핵심 전장/전자전 플래그(추가 시 이 목록에 1줄 더한다)
    flags = ['enable_battle_mode', 'enable_munition_limit', 'enable_ship_evasion',
             'enable_esm_arm', 'enable_sonar_emcon', 'enable_asw_forward',  # v16.1 EMCON 3종
             'enable_cyber_warfare',  # v16.3 사이버전
             'enable_hgv_glide']  # v16.2 극초음속 활공 궤적
    for f in flags:
        build   = bool(re.search(rf"['\"]{f}['\"]\s*:\s*[^\n,}}]*isChecked", lau))
        restore = bool(re.search(rf"setChecked\(\s*cfg\.get\(['\"]{f}", lau))
        engread = f in ev
        ok = build and restore and engread
        check('①', f'3종세트 {f}', ok,
              f"build={build} restore={restore} engine_core={engread}")

# ── ② DB: db_specsheet 항목수 == 엔티티 DB 항목수 합 ──────────────────────────────
def chk_spec_count():
    eng = rd('engine_core.py'); spec = rd('db_specsheet.py')
    def topcount(src, name):
        mm = re.search(rf"^{name}\s*[:=].*?\{{(.*?)^\}}", src, re.S | re.M)
        return len(re.findall(r"^\s{4}['\"]", mm.group(1), re.M)) if mm else None
    entity = sum(topcount(eng, n) or 0 for n in
                 ['ENEMY_DB', 'FRIENDLY_DB', 'SHIP_DB', 'FRIENDLY_AIRCRAFT_DB'])
    sd = topcount(spec, 'SPEC_DETAIL_DB')
    check('②', 'db_specsheet 항목수 = 엔티티 DB 합', sd == entity,
          f"SPEC_DETAIL_DB={sd} vs ENEMY+FRIENDLY+SHIP+AIRCRAFT={entity}")

# ── ⑧ 수치: 전장 분모 변수 0 가드(max(1.0,..) / or 1.0) ──────────────────────
def chk_div_guards():
    ev = rd('engine_combat.py')
    pats = {
        '_fr_value_init': r"_fr_value_init\s*=\s*max\(\s*1\.0",
        '_en_value_init': r"_en_value_init\s*=\s*max\(\s*1\.0",
        '_ammo_init':     r"_ammo_init\s*=\s*max\(\s*1\.0",
        'fw(or 1.0)':     r"fw\s*=\s*sum\(.*?\)\s*or\s*1\.0",
        'ew(or 1.0)':     r"ew\s*=\s*sum\(.*?\)\s*or\s*1\.0",
    }
    miss = [k for k, p in pats.items() if not re.search(p, ev)]
    check('⑧', '전장 progress/score 분모 0 가드', not miss,
          f"가드 미검출={miss}" if miss else '모든 분모 max(1.0,..)/or 1.0')

# ── ⑥ 위생: _PLANS 완료분 반영(이미 구현된 항목이 미래형으로 잔류) ───────────
def chk_plans_stale():
    """changelog에 이미 구현된 minor 계열(v16.02.01 → v16.2)이 _PLANS에 '완료/잔여'
    반영 없이 순수 미래형으로 남았는지, '보류' 라벨 항목이 잔존하는지 검사.
    (v16.x 작업 항목만 보고 상위 '진행 중'·'보류' 완료분을 놓친 빈틈에서 굳힘.)"""
    import json
    lau = rd('app_main.py')
    cl = json.load(open(os.path.join(ROOT, 'app_changelog.json'), encoding='utf-8'))
    # 진행 중 블록(changelog 최신 major)만 검사 — v15 이전은 로드맵 재편으로
    # changelog minor(전장 엔진)와 _PLANS 버전(미구현 AI 계획)이 번호만 같고 내용이
    # 달라 오탐. 과거 major는 이미 완료·삭제됨.
    majors = [int(re.match(r'v(\d+)', c['version']).group(1)) for c in cl
              if re.match(r'v(\d+)', c['version'])]
    latest_major = max(majors) if majors else 0
    # changelog 버전(v16.02.01) → _PLANS 표기(v16.2)로 정규화, 최신 major만.
    # minor별 changelog 제목도 모은다(번호만 같고 내용 다른 로드맵 항목 오탐 차단용).
    cl_minors = set()
    cl_titles: dict = {}
    for c in cl:
        m = re.match(r'v(\d+)\.(\d+)\.\d+', c['version'])
        if m and int(m.group(1)) == latest_major:
            key = f"v{m.group(1)}.{int(m.group(2))}"
            cl_minors.add(key)
            cl_titles.setdefault(key, []).append(c.get('title', ''))
    pm = re.search(r'_PLANS\s*=\s*\[(.*?)\n        \]\s*\n', lau, re.S)
    plans = pm.group(1) if pm else lau
    # 흔한 도메인 불용어 — 우연히 1개 겹쳐 번호충돌 오탐 차단이 뚫리는 것 방지
    # (예: changelog v16.8 'C-RAM 방어 포대' vs _PLANS v16.8 '항만 방어 시나리오'의 '방어')
    _STOP = {'방어', '시나리오', '공격', '작전', '전술', '모드', '통합', '강화',
             '기능', '체계', '지원', '대응', '시스템', '도입', '확장'}
    def _toks(s):
        return set(re.findall(r'[가-힣A-Za-z0-9]{2,}', s)) - _STOP
    stale = []
    for ver in sorted(cl_minors):
        m = re.search(rf'\(\s*["\']({re.escape(ver)})["\']\s*,', plans)
        if not m:
            continue   # _PLANS에 항목 없음(완전 완료돼 삭제) — 정상
        # _PLANS 항목 제목(3번째 요소)이 그 minor의 changelog 제목과 핵심어를 공유하는지
        # 확인. 안 겹치면 APP_VERSION seq와 로드맵 번호가 번호만 충돌한 것(예: changelog
        # v16.04=극초음속 활공 vs _PLANS v16.4=분산 해양작전) → 오탐, 건너뜀.
        thdr = re.match(
            r'\s*\(\s*["\'][^"\']*["\']\s*,\s*["\'][^"\']*["\']\s*,\s*["\']([^"\']*)["\']',
            plans[m.start():])
        plan_title = thdr.group(1) if thdr else ''
        ctoks = set()
        for t in cl_titles.get(ver, []):
            ctoks |= _toks(t)
        if plan_title and len(_toks(plan_title) & ctoks) < 2:
            continue   # 핵심어 2개 미만 겹침 → 번호만 충돌, 내용 무관(미래 로드맵, 정상)
        rest = plans[m.end():]
        nxt = re.search(r'\n\s*\(\s*["\'](?:v[\d.]+|📋|진행|보류)', rest)
        block = rest[:nxt.start()] if nxt else rest[:1200]
        if not re.search(r'완료|구현|잔여|남은', block):
            stale.append(ver)   # 이미 구현 시작됐는데 미래형만 → stale 의심
    boryu = bool(re.search(r'\(\s*["\']보류["\']', plans))
    detail = ''
    if stale: detail += f"완료분 미반영 의심={stale} "
    if boryu: detail += "'보류' 라벨 항목 잔존(전장 엔진 완료 후 검토 필요)"
    check('⑥', '_PLANS 완료분 반영(구현된 항목 stale 미래형·보류 잔존)',
          not stale and not boryu, detail or 'OK')

# ── ① 코드: MC 3경로 + 라우터/집계 존재 ──────────────────────────────────────
def chk_mc_paths():
    ev = rd('engine_combat.py')
    need = ['monte_carlo_v7', '_mc_batch_worker', 'monte_carlo_lhs', '_mc_run_one', '_battle_agg']
    miss = [n for n in need if not re.search(rf'def {n}\b', ev)]
    check('①', 'MC 3경로+라우터+집계 존재', not miss, f"누락={miss}" if miss else 'OK')


def _tracked():
    out = subprocess.check_output(['git', 'ls-files'], cwd=ROOT, text=True, encoding='utf-8')
    return out.splitlines()


def chk_readme_coverage():
    # ⑥ 위생: README 파일구조 표가 실제 루트 코드/데이터 파일을 전수 커버하는지 (문서 drift 방지)
    readme = rd('README.md')
    exts = ('.py', '.json', '.npz', '.html', '.spec')
    code_files = [f for f in _tracked() if '/' not in f and f.endswith(exts)]
    missing = [f for f in code_files if f not in readme]
    check('⑥', 'README 파일구조 = 실제 코드/데이터 파일 전수 커버', not missing,
          f"README 미기재={missing}" if missing else f'{len(code_files)}개 전수 기재 OK')


def chk_stale_filename():
    # ⑥ 위생: 버전 스탬프(_v7 등) 잔존 파일명 — stale 명칭 재발 방지 (engine_v7 사례)
    stale = [f for f in _tracked()
             if f.endswith('.py') and '/' not in f and re.search(r'_v\d+', os.path.basename(f))]
    check('⑥', '파일명 stale 버전스탬프(_v<N>) 없음', not stale,
          f"stale 명칭={stale}" if stale else 'OK')


def main():
    for fn in (chk_version, chk_gitignore, chk_log_guard, chk_frame_guard,
               chk_flag_triplet, chk_spec_count, chk_div_guards, chk_mc_paths,
               chk_plans_stale, chk_readme_coverage, chk_stale_filename):
        try:
            fn()
        except Exception as e:
            check('?', fn.__name__, False, f'스캐너 예외: {e}')

    npass = sum(1 for *_, ok, _ in [(0, 0, r[2], r[3]) for r in results] if ok)
    nfail = len(results) - sum(1 for r in results if r[2])
    print("=" * 64)
    print("audit_static_scan.py — 종합 감사 정적 스캔")
    print("=" * 64)
    for area, name, ok, detail in results:
        mark = 'PASS' if ok else 'FAIL'
        print(f"[{mark}] {area} {name}")
        if detail and (not ok or os.environ.get('AUDIT_VERBOSE')):
            print(f"        {detail}")
    print("-" * 64)
    npass = sum(1 for r in results if r[2])
    print(f"{npass}/{len(results)} PASS")
    if npass != len(results):
        print("⚠ FAIL 항목은 사람이 검토 — 휴리스틱 오탐일 수도, 실제 회귀일 수도 있다.")
        sys.exit(1)
    print("✅ 정적 스캔 전부 PASS")


if __name__ == '__main__':
    main()
