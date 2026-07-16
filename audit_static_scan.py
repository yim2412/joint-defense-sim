#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
audit_static_scan.py — 종합 감사 정적 스캐너 (빌드 제외 도구)

CLAUDE.md '종합 감사' 9영역 중 **정적 Grep으로 굳힐 수 있는 점검**을 자동화한다.
audit_verify_regression.py(엔진 동작 무결성)와 짝 — 이쪽은 코드를 실행하지 않고 소스만 본다.

처음 v15 블록 종합 감사(2026-06-23) 실전에서 손으로 친 Grep을 추출해 제작.
엔진/app_main 구조가 바뀌면 휴리스틱이 어긋날 수 있으니, FAIL은 항상 사람이 검토한다.

사용:  python audit_static_scan.py        # 전체 점검, 하나라도 FAIL이면 exit 1
점검 영역(약칭): ⑥위생(버전정합·gitignore·_PLANS stale·README 파일전수커버·README DB수치/단계버전 정합·파일명 stale버전스탬프)
              ①코드(_log가드·_record_frame가드·enable 3종세트·MC 3경로) ②DB(db_specsheet 정합) ⑧수치(전장 분모 가드)
"""
import os, re, sys, subprocess, json

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

def guard_count(area, label, n, floor):
    """vacuous-pass 방지 — 자동추출 검사가 기대 하한 미만을 추출하면 정규식/구조가
    깨진 것으로 간주해 FAIL. (추출 0개 → 위반 0개 → 조용히 PASS 하는 함정 차단.
    '감사가 스스로 깨졌는데 통과'가 '버그를 못 잡음'보다 위험 — 거짓 안심을 준다.)"""
    check(area, f'추출 sanity: {label}', n >= floor,
          f"{n}개 추출(하한 {floor}) — 정규식/소스 구조 변경 의심, 검사 무력화 위험"
          if n < floor else f"{n}개 추출 OK(≥{floor})")

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
             'enable_hgv_glide',  # v16.2 극초음속 활공 궤적
             # (enable_recon_drone은 _restore_cfg가 for-루프 복원이라 이 정규식과 불일치 — 제외)
             'enable_unmanned_assets',  # v16.12 트랙 A-2 무인 함정
             'enable_autonomous_engagement',  # v16.13.02 트랙 C 함정 자율 교전
             'enable_ras_rearm',  # v16.13.05 RAS 탄약 재보급(전장 전용)
             'enable_laser_dew']  # v16.13.08~09 지향성 에너지 무기(레이저)
    for f in flags:
        build   = bool(re.search(rf"['\"]{f}['\"]\s*:\s*[^\n,}}]*isChecked", lau))
        restore = bool(re.search(rf"setChecked\(\s*cfg\.get\(['\"]{f}", lau))
        engread = f in ev
        ok = build and restore and engread
        check('①', f'3종세트 {f}', ok,
              f"build={build} restore={restore} engine_core={engread}")
    # v18 캠페인 계열 — 소비처가 engine_combat이 아니라 engine_campaign(fog) / app_main 라우팅(mode)
    # 이라 위 engread가 오탐 → 소비처를 명시해 별도 검사(3종세트 무결성은 동일하게 요구).
    camp = rd('engine_campaign.py')
    air  = rd('engine_airforce.py')
    army = rd('engine_army.py')
    camp_flags = {'enable_army_campaign': camp,   # v20.2b engine_campaign __init__에서 소비(지상 층)
                  'enable_coastal_sam':   army,   # v20.2b engine_army ArmyCampaign에서 소비(연안 포대)
                  'enable_amphibious':    army,   # v20.3 engine_army ArmyCampaign에서 소비(상륙작전)
                  'enable_enemy_sead':    army,   # v20.4 engine_army 적 SEAD 제압(도미노)
                  'enable_campaign_mode': lau,   # app_main SimWorker 라우팅에서 소비
                  'enable_campaign_fog': camp,   # engine_campaign _tick_intel에서 소비
                  'enable_air_campaign': camp,   # v19.1 engine_campaign __init__에서 소비(공군 층)
                  'enable_precise_engagement': camp,  # A1 engine_campaign __init__/_tick_engagements에서 소비(정밀 교전)
                  'enable_sead': air,            # v19.3 engine_airforce AirCampaign에서 소비(방공망 제압)
                  'enable_strategic_strike': air}  # v19.4 engine_airforce AirCampaign에서 소비(전략폭격)
    for f, consumer in camp_flags.items():
        build    = bool(re.search(rf"['\"]{f}['\"]\s*:\s*[^\n,}}]*isChecked", lau))
        restore  = bool(re.search(rf"setChecked\(\s*cfg\.get\(['\"]{f}", lau))
        consumed = bool(re.search(rf"\.get\(['\"]{f}['\"]", consumer))
        ok = build and restore and consumed
        check('①', f'3종세트 {f}', ok,
              f"build={build} restore={restore} consumed={consumed}")

# ── ② DB: db_specsheet 항목수 == 엔티티 DB 항목수 합 ──────────────────────────────
def chk_spec_count():
    # v21.2: 개수 비교 → **집합 비교**로 교체. 개수만 보면 "A 누락 + B 유령"이 서로
    # 상쇄돼 통과하는 사각이 있었다(실제로 현무-3C 스펙 추가 시 처음 드러남).
    #
    # 필수/허용을 나눈다:
    #   · 필수(required) = DB 탭이 **화면에 나열**하는 DB. 스펙이 없으면 사용자가 빈
    #     설명을 본다 → 반드시 커버.
    #   · 허용(allowed)  = 위 + FRIENDLY_STRIKE_DB(engine_combat). 이 DB는 DB 탭이
    #     나열하지 않으므로 스펙이 **없어도 무해**하지만, 있어도 유령이 아니다
    #     (현무-3C처럼 지상공격 DB에만 있는 무기).
    eng = rd('engine_core.py'); cmb = rd('engine_combat.py'); spec = rd('db_specsheet.py')
    def topnames(src, name):
        mm = re.search(rf"^{name}\s*[:=].*?\{{(.*?)^\}}", src, re.S | re.M)
        return set(re.findall(r"^\s{4}['\"]([^'\"]+)['\"]", mm.group(1), re.M)) if mm else set()
    required = set()
    for n in ['ENEMY_DB', 'FRIENDLY_DB', 'SHIP_DB', 'FRIENDLY_AIRCRAFT_DB']:
        required |= topnames(eng, n)
    allowed = required | topnames(cmb, 'FRIENDLY_STRIKE_DB')
    sd = topnames(spec, 'SPEC_DETAIL_DB')
    guard_count('②', 'DB 항목 파싱(엔티티/스펙)', min(len(required), len(sd)), 50)  # vacuous 방지
    missing = sorted(required - sd)   # 화면에 나오는데 스펙 없음 → 설명이 빈다
    ghost   = sorted(sd - allowed)    # 어느 DB에도 없는 스펙 → 삭제된 항목의 잔재
    check('②', 'db_specsheet 항목 = 엔티티 DB 항목(집합)', not missing and not ghost,
          f"스펙누락={missing or '없음'} / 유령스펙={ghost or '없음'} "
          f"(스펙 {len(sd)} · 필수 {len(required)} · 허용 {len(allowed)})")

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


def chk_readme_counts():
    # ⑥ 위생: README에 명시된 DB 항목수·현재 단계 버전이 실제와 일치하는지 자동 검출.
    # (수동 갱신 누락으로 stale해지는 것을 사람 기억이 아니라 도구로 잡는다 — 2026-07-03)
    readme = rd('README.md')
    try:
        import importlib
        ec    = importlib.import_module('engine_core')
        ecomb = importlib.import_module('engine_combat')
    except Exception as e:
        check('⑥', 'README DB 항목수 = 실제 DB', True, f'(스킵: 엔진 import 실패 {e})')
        return
    actual = {
        '적군':        len(ec.ENEMY_DB),
        '아군 방어':   len(ec.FRIENDLY_DB),
        '대함 타격':   len(ecomb.FRIENDLY_STRIKE_DB),
        '함정':        len(ec.SHIP_DB),
        '항공 자산':   len(ec.FRIENDLY_AIRCRAFT_DB),
        '편대 프리셋': len(ec.FLEET_PRESETS) + len(ec.ENEMY_FLEET_PRESETS),
    }
    mism = []
    for label, n in actual.items():
        m = re.search(rf"{label}\s*(\d+)\s*종", readme)
        if m and int(m.group(1)) != n:
            mism.append(f"{label} README={m.group(1)}≠실제={n}")
    # 현재 단계 버전(major.minor)이 APP_VERSION과 일치하는지
    av = re.search(r'APP_VERSION\s*=\s*["\']v(\d+\.\d+)', rd('app_main.py'))
    if av:
        for sm in re.finditer(r'(?:현재 단계|Current stage)[^\n]*?\(v(\d+\.\d+)\)', readme):
            if sm.group(1) != av.group(1):
                mism.append(f"현재 단계 README=v{sm.group(1)}≠APP=v{av.group(1)}")
    check('⑥', 'README DB 항목수·단계 버전 = 실제', not mism,
          '; '.join(mism) if mism else 'DB 수치·단계 버전 일치')


def chk_stale_filename():
    # ⑥ 위생: 버전 스탬프(_v7 등) 잔존 파일명 — stale 명칭 재발 방지 (engine_v7 사례)
    stale = [f for f in _tracked()
             if f.endswith('.py') and '/' not in f and re.search(r'_v\d+', os.path.basename(f))]
    check('⑥', '파일명 stale 버전스탬프(_v<N>) 없음', not stale,
          f"stale 명칭={stale}" if stale else 'OK')


def chk_completed_plans():
    # ⑥ 위생: 구현완료 설계문서(plan_v<N>_<M>_*.md)가 루트에 잔존 — _archive/plans/로 가야 함.
    # 숫자 마이너를 가진 plan은 특정 마이너 구현 설계문서 → 구현되면 아카이브 대상.
    # 진행 중 메이저 plan(plan_battle_engine.md 등 숫자 마이너 없는 것)은 자동 제외.
    # (v16 종합감사 메타회고: plan_v16_4~8 루트 잔존을 수동 발견 → 자동검사로 굳힘)
    root_plans = [f for f in _tracked()
                  if '/' not in f and re.match(r'plan_v\d+_\d+.*\.md$', f)]
    check('⑥', '구현완료 plan_v<N>_<M> 루트 잔존 없음(→ _archive/plans/)', not root_plans,
          f"루트 잔존(아카이브 필요)={root_plans}" if root_plans else 'OK')


def chk_resource_paths():
    # ⑤ exe·빌드: 번들 소스가 리소스 파일(pkl/npz/model 등)을 '기본인자 리터럴 상대경로'로
    # 로드하면 exe(_internal/sys._MEIPASS)에서 못 찾아 조용히 폴백/실패한다.
    # (v17.01.02 캠페인 예측모델 폴백 버그를 메타회고로 굳힘 — 상대경로 joblib.load가 원인)
    # 경로를 '인자로 받는' 모듈(ai_policy_infer 등)은 호출측이 _res로 넘기므로 기본인자 패턴에 안 걸림.
    BUNDLED = ['app_main.py', 'engine_core.py', 'engine_combat.py', 'engine_campaign.py',
               'forecast_features.py', 'ai_policy_infer.py', 'db_specsheet.py']
    dflt = re.compile(r"""def\s+\w+\([^)]*=\s*['"][^'"/\\]+\.(?:pkl|npz|joblib|h5|model)['"]""")
    bad = []
    for fn in BUNDLED:
        try:
            src = rd(fn)
        except Exception:
            continue
        if dflt.search(src) and '_MEIPASS' not in src and '_res(' not in src:
            bad.append(fn)
    check('⑤', 'exe 리소스 로더 기본경로 _MEIPASS 경유(상대경로 폴백 방지)', not bad,
          f"상대경로 기본인자 로더(_MEIPASS 미경유)={bad}" if bad else 'OK')


def chk_flag_restore_auto():
    """자동 추출 전수 검사 — 하드코딩 목록 없이 app_main의 **모든** 체크박스 빌드 플래그
    ('enable_xxx': self.chk_*.isChecked())가 _restore_cfg에서 복원되는지 확인.
    복원은 개별 setChecked(cfg.get('enable_xxx')) 또는 for-루프 튜플 ('chk_x','enable_xxx')
    둘 다 인정. chk_flag_triplet의 하드코딩 목록(14개)이 놓치던 사각을 원천 제거 —
    새 토글이 추가돼도 자동으로 검사 대상이 된다(strike·thaad·ashore 복원 누락을 이 검사가 잡음)."""
    lau = rd('app_main.py')
    built = set(re.findall(r"['\"](enable_\w+)['\"]\s*:\s*self\.\w+\.isChecked\(\)", lau))
    restored = set(re.findall(r"setChecked\(\s*\w*\.?get\(['\"](enable_\w+)", lau))
    restored |= set(re.findall(r"\(['\"]chk_\w+['\"]\s*,\s*['\"](enable_\w+)['\"]\s*[,)]", lau))  # for-루프 튜플(2·3튜플 무관)
    guard_count('①', '체크박스 빌드 플래그(복원검사 기반)', len(built), 30)  # vacuous 방지(현 44개)
    missing = sorted(built - restored)
    check('①', f'플래그 복원 전수(자동추출 {len(built)}개 체크박스)', not missing,
          f"복원 누락(시나리오 로드 시 초기화): {missing}" if missing else '체크박스 빌드 전부 복원 확인')


def chk_flag_consume_auto():
    """자동 추출 — 엔진(engine_combat·engine_campaign)이 소비하는 enable_ 플래그 중
    체크박스 빌드도 없고(사용자 제어 불가) 문서화 의도(_ALWAYS_ON 화이트리스트)도 없는
    '숨은 플래그'를 경고. 상시 ON이 의도된 내부 물리/기본값은 화이트리스트로 명시(오탐 방지)."""
    lau = rd('app_main.py'); ev = rd('engine_combat.py') + rd('engine_campaign.py')
    consumed = set(re.findall(r"\.get\(['\"](enable_\w+)", ev)) | set(re.findall(r"cfg\[['\"](enable_\w+)", ev))
    built_any = set(re.findall(r"['\"](enable_\w+)['\"]\s*:", lau))
    guard_count('①', '엔진 소비 플래그(숨은플래그 검사 기반)', len(consumed), 30)  # vacuous 방지(현 40+)
    # 상시 ON이 의도된 내부 기능(사용자 토글 불필요) — 명시적 화이트리스트
    ALWAYS_ON = {'enable_cec_preassign', 'enable_subsystem_damage', 'enable_decoy',
                 'enable_ecm', 'enable_evasion', 'enable_layered_defense',
                 'enable_random_placement', 'enable_selfdefense'}
    hidden = sorted(consumed - built_any - ALWAYS_ON)
    check('①', '숨은 플래그 없음(소비O·UI빌드X·화이트리스트X)', not hidden,
          f"엔진 소비하나 UI/화이트리스트 없음: {hidden}" if hidden else 'OK(상시ON은 화이트리스트로 명시)')


# ── ① 죽은 기능 방지 커밋 게이트 (plan_dead_feature_prevention.md) ──────────────
# 신규 enable_* 토글이 '효과 프로브(audit_effect.py) 없이' 커밋되는 걸 pre-commit에서 차단.
# v20.5에서 죽어 있던 기능들(레이더 침묵·EMCON·레이저·정찰 드론)은 전부 '메커니즘 구현→
# OFF면 기존과 동일→회귀 PASS→실험적·OFF 커밋' 경로로 태어났다. 그 관문은 '안 깨뜨린다'만
# 보고 '실제로 뭔가 한다'는 안 봤다. 이 게이트가 그 강제 장치다.
#
# 커버 집합 = PROBES(정밀 효과 프로브) ∪ EFFECT_ALIVE(스캐너 확증) ∪ EFFECT_DEBT(미검증 유예).
# 신규 enable_* 는 이 셋 중 하나에 들어야 커밋 통과 — 아니면 '프로브 없이 태어난 죽은 기능 후보'로 FAIL.
#
# EFFECT_DEBT(부채): 게이트 도입 시점(2026-07-16) 미커버였고 아직 상환 안 된 토글. **줄기만 한다.**
#   ④ audit_dead_toggle.py가 '살아있음' 판정하면 EFFECT_ALIVE로 옮긴다(상환). 새 토글 추가 금지.
# EFFECT_ALIVE(상환 완료): ④ 스캐너 전수 실행이 ON/OFF 델타로 '살아있음' 입증한 토글.
#   2026-07-16 첫 전수 스캔(636초)에서 26개 확증 → 부채 43→17. 이 목록은 늘어도 됨(검증 완료라서).
# (초안 '33개'는 추정치. 실측 = engine_combat `.get()`/`cfg[]` 소비 50개 − PROBES 7 = 43.)
# 항공기 자산 토글(f35a·kf21·helo 등)·캠페인/공군/육군 토글은 engine_combat 미소비라 자동 제외.
# ✅ 전부 상환·종결(2026-07-16). 초기 부채 43 → A/B/C/D/E 청소로 0. 이 집합은 다시 채우지
#    않는다(새 토글은 PROBES 또는 EFFECT_ALIVE로 검증하고 태어난다 — 부채는 늘 수 없다).
EFFECT_DEBT = set()

# ④ 스캐너가 살아있음 입증한 상환 완료 토글. 첫 전수 스캔 2026-07-16 + A+B/A 재스캔 2026-07-15
#    (부채 청소: ballistic_descent·hgv_glide·isa·terrain 발현무대 + BMD 5자산 ashore/thaad/lsam/
#     chungung/patriot는 토글+**재고(*_stock)** 짝을 줘야 발현). 재현: python audit_dead_toggle.py
#    C 청소 2026-07-16: cec_preassign은 **enable_cec(이미 상환)의 레거시 폴백 별칭** — engine_combat
#    3601 `get('enable_cec', get('enable_cec_preassign', True))`로 같은 cec_base 경로 공유. UI는
#    enable_cec만 빌드(app_main 9991), preassign은 구버전 cfg 로드 폴백뿐. 별칭 상환으로 이관.
#    selfdefense는 카운터 시딩 후 재스캔서 발동43·델타(friendly_hits+4·손실+1) 확증 → 상환.
#    D 청소 2026-07-16: asw_contact_limit(datum 성장)는 sonar_emcon(핑 역탐지 회피) 짝을 켠
#    대잠EMCON 무대서 델타(intercept_rate+0.198) 확증 → 상환. 접촉 단절 이벤트가 있어야 발현.
#    decoy(어뢰 기만)는 매복(is_ambush) 잠수함 '북한 잠수함 선제 기습'+대잠 항공 OFF 무대서
#    발동3·델타 확증(원거리 발사 잠수함 무대선 어뢰 미도달이었다). minesweeping(기뢰 소해)은
#    mine_density 0.8 기뢰전 무대서 mines_struck-2 델타 확증(0.5 접촉 2발은 시드편차에 묻힘).
#    E 청소 2026-07-16(전장 전용, 단발 스캐너 대상 밖 → run_battle_simulation 프로브로 확증):
#    battle_mode는 _mc_run_one 라우터로 전장 엔진(전장 전용 지표 friendly_score·outcome 산출)을
#    타는 걸 확인. ras_rearm은 소양함(AOE 화물 40발) 든 '이지스 기동전단'+대량 포화+3600s 전장서
#    OFF=0→ON=40 재보급·friendly_score+0.05 확증. 부채 43→0 완전 상환(anti_sam만 EFFECT_DEAD).
EFFECT_ALIVE = {
    'enable_ashore', 'enable_asw_contact_limit', 'enable_asw_forward', 'enable_autonomous_engagement', 'enable_ballistic_descent',
    'enable_cec', 'enable_cec_jammed', 'enable_cec_preassign', 'enable_chungung',
    'enable_current', 'enable_decoy', 'enable_ecm', 'enable_esm_arm', 'enable_evap_duct', 'enable_evasion',
    'enable_flooding', 'enable_hgv_glide', 'enable_iff', 'enable_isa', 'enable_laser_dew',
    'enable_layered_defense', 'enable_lsam', 'enable_minesweeping',
    'enable_multibearing', 'enable_munition_limit', 'enable_patriot', 'enable_radar_off',
    'enable_random_placement',
    'enable_recon_drone', 'enable_selfdefense', 'enable_ship_evasion', 'enable_sonar_emcon', 'enable_sonar_equation',
    'enable_standoff_spawn', 'enable_strike', 'enable_subsystem_damage', 'enable_target_difficulty',
    'enable_terrain', 'enable_thaad', 'enable_weather_dynamics',
    # E 청소 2026-07-16: 전장 전용(단발 스캐너 대상 밖, 전장 프로브로 확증) —
    'enable_battle_mode', 'enable_ras_rearm',
}

# 종결(원리상 발동 불가로 규명 → 죽은 기능 확정). 레이저와 달리 '메커니즘 살아있음'이 아니라
# **요격 대상이 엔진에 존재하지 않아** 발현 경로 자체가 없다. 코드는 미래 짝 기능이 생기면
# 되살릴 수 있게 보존(삭제 아님) → EFFECT_DEBT(줄여야 할 부채)도 EFFECT_ALIVE(검증완료)도 아닌
# 별도 상태. 게이트는 이 집합을 uncovered에서 면제(종결 규명이 곧 검증).
#   anti_sam(2026-07-16 C 청소): _enemy_anti_sam은 friendly_sam이 적 함정(is_ship)을 target하는
#   경우만 요격하는데, 아군 SAM은 대공 전용이라 적 함정을 target하는 경로가 엔진에 전혀 없다
#   (적 함정 공격은 friendly_strike). `m.target is et`가 영원히 거짓 → 발동0 확정. 노린 현실
#   교전(적 함정의 대함미사일 방어)은 이미 enable_selfdefense가 담당(중복). 되살리려면 '아군
#   SAM의 대함 2차 교전'(SM-6 대함 모드 등)이 선행돼야 하나 로드맵·교리 근거 없어 종결.
EFFECT_DEAD = {
    'enable_anti_sam',
}


def chk_effect_coverage():
    """① 커밋 게이트 — engine_combat이 소비하는 신규 enable_* 토글은 커버(PROBES 정밀 프로브
    ∪ EFFECT_ALIVE 스캐너 확증)가 있어야 한다. 없고 EFFECT_DEBT 유예에도 없으면 FAIL
    (= 검증 없이 태어난 죽은 기능 후보). 부채(EFFECT_DEBT)는 줄기만 하고 늘 수 없다."""
    ev = rd('engine_combat.py')
    consumed = set(re.findall(r"\.get\(['\"](enable_\w+)", ev)) | set(re.findall(r"cfg\[['\"](enable_\w+)", ev))
    guard_count('①', '엔진 소비 플래그(효과커버 검사 기반)', len(consumed), 40)
    ae = rd('audit_effect.py')
    probes  = set(re.findall(r"^\s*'(enable_\w+)'\s*:\s*\(", ae, re.M))  # PROBES 딕셔너리 키
    guard_count('①', '효과 프로브 등재(PROBES)', len(probes), 5)
    covered = probes | EFFECT_ALIVE                                     # 검증 완료 = 커버
    # (1) 신규 미커버 = 소비하나 커버(프로브·상환)도, 부채 유예도, 종결(발동불가 규명)도 아님 → 위반
    uncovered = sorted(consumed - covered - EFFECT_DEBT - EFFECT_DEAD)
    check('①', f'신규 토글 검증 필수(부채 {len(EFFECT_DEBT & consumed)}·상환 {len(EFFECT_ALIVE & consumed)}·종결 {len(EFFECT_DEAD & consumed)})',
          not uncovered,
          f"검증 없는 신규 토글 — PROBES 추가 or audit_dead_toggle 스캔으로 EFFECT_ALIVE 등재: {uncovered}"
          if uncovered else f'OK(프로브 {len(probes)}·상환 {len(EFFECT_ALIVE & consumed)}·부채 {len(EFFECT_DEBT & consumed)}·종결 {len(EFFECT_DEAD & consumed)})')
    # (2) 부채 상환 위생 — 이미 커버(프로브·상환·종결)됐는데 부채에 잔류하면 제거하라고 안내
    repaid = sorted(EFFECT_DEBT & (covered | EFFECT_DEAD))
    check('①', '부채 상환 반영(커버되면 EFFECT_DEBT서 제거)', not repaid,
          f"이미 커버됨 — EFFECT_DEBT에서 제거: {repaid}" if repaid else 'OK(중복 없음)')
    # (3) 삭제된 토글 위생 — 부채·상환·종결에 있으나 이제 소비 안 함 → 목록 청소 안내
    stale = sorted((EFFECT_DEBT | EFFECT_ALIVE | EFFECT_DEAD) - consumed)
    check('①', 'EFFECT_DEBT/ALIVE 유효성(삭제된 토글 잔류 없음)', not stale,
          f"이제 engine_combat이 소비 안 함 — 목록서 제거: {stale}" if stale else 'OK')


def chk_widget_dup():
    """① 위젯 attr 이름 충돌 — 같은 self.chk_XXX가 QCheckBox로 2번+ 정의되면 나중 정의가
    이겨 앞 위젯이 orphan(화면엔 보이나 참조 상실)이 된다. v19.4 chk_strike 충돌
    (전략폭격 위젯이 '공격 임무' 위젯에 묶여 기본 OFF 계약 위반)을 잡은 검사. 3종세트
    정규식은 문자열 존재만 봐서 이 충돌을 놓쳤다 → 위젯 정의 중복을 직접 검출."""
    lau = rd('app_main.py')
    defs = re.findall(r'self\.(chk_\w+)\s*=\s*QCheckBox', lau)
    dups = sorted({n for n in defs if defs.count(n) > 1})
    check('①', '체크박스 위젯 attr 중복정의 없음(orphan 방지)', not dups,
          f"같은 이름으로 2번+ 정의된 위젯(하나가 orphan): {dups}" if dups
          else f'OK({len(set(defs))}개 위젯 전부 고유명)')


def chk_memory_freshness():
    """⑥ 위생: 로컬 메모리(patch_queue.md) 재개지점 APP_VERSION vs 실제 코드 APP_VERSION.
    메모리는 수동 갱신이라 감사·패치를 커밋한 뒤 갱신을 빠뜨리면 stale → 다음 세션의 자동
    브리핑이 옛 상태를 정본처럼 보고한다(2026-07-09: v18.01.07 감사 완료를 patch_queue가
    v18.01.06으로 방치→브리핑이 '감사 아직 안 함' 오보). 메모리 파일이 없는 환경(CI·
    빌드 등)에서는 조용히 SKIP — 이 검사는 개발 머신 로컬 정합용이다."""
    import glob
    lau = rd('app_main.py')
    m = re.search(r'APP_VERSION\s*=\s*["\']([^"\']+)', lau)
    appv = m.group(1) if m else None
    cands = glob.glob(os.path.expanduser('~/.claude/projects/*/memory/patch_queue.md'))
    if not cands or not appv:
        return  # 로컬 메모리 없음(비-개발 환경) → SKIP
    path = max(cands, key=os.path.getmtime)   # 여러 프로젝트면 최근 수정본
    txt = open(path, encoding='utf-8').read()
    pm = re.search(r'APP_VERSION\s+(v[\d.]+)', txt)   # 첫 매치=최상단 재개지점
    memv = pm.group(1) if pm else None
    check('⑥', '메모리 patch_queue 재개지점 버전 == 코드 APP_VERSION', memv == appv,
          f"patch_queue={memv} vs 코드={appv} — 메모리 stale 의심(패치·감사 커밋 후 갱신 누락)"
          if memv != appv else f"OK({memv})")


def chk_session_log_fresh():
    """⑥ 위생: SESSION_LOG.md(세션 재개 저널) 최신 항목의 HEAD 해시가 실제 git HEAD에서
    너무 멀면(커밋 THRESH개+) 세션 매듭 갱신이 밀린 것 → 세션 완전 종료 시 새 세션 재개
    맥락이 stale. 세션 중단 대비 3층 방어의 stale 검출층(2026-07-10 사용자 "무거워도 확실히").
    파일 없으면 SKIP."""
    THRESH = 10   # 세션 매듭당 갱신이라 넉넉히 — 이보다 밀리면 저널 방치
    p = os.path.join(ROOT, 'SESSION_LOG.md')
    if not os.path.exists(p):
        return
    txt = open(p, encoding='utf-8').read()
    m = re.search(r'HEAD:\s*([0-9a-f]{7,40})', txt)   # 첫 매치 = 최신 항목
    if not m:
        check('⑥', 'SESSION_LOG 최신 항목 HEAD 해시 표기', False,
              '(HEAD: <해시>) 표기 없음 — 정합 검사 불가')
        return
    logh = m.group(1)
    try:
        r = subprocess.run(['git', 'rev-list', f'{logh}..HEAD', '--count'],
                           cwd=ROOT, capture_output=True, text=True, timeout=10)
        cnt = int(r.stdout.strip()) if r.returncode == 0 else -1
    except Exception:
        cnt = -1
    if cnt < 0:
        check('⑥', 'SESSION_LOG 최신 해시가 git 이력에 존재', False,
              f'{logh} rev-list 실패 — 해시 오타·조작 의심')
    else:
        check('⑥', f'SESSION_LOG 세션 저널 최신성(HEAD 거리 <{THRESH})', cnt < THRESH,
              f'저널 이후 커밋 {cnt}개 — 세션 매듭 갱신 밀림(재개 맥락 stale)'
              if cnt >= THRESH else f'OK(이후 {cnt}커밋)')


def chk_golden_coverage():
    """③ 회귀: 골든 지표가 어느 케이스에서도 발현 안 하면(전 케이스 동일값) 회귀 사각.
    새 stats 키를 추가했는데 8케이스가 그 경로를 안 밟으면, 그 키가 바뀌어도 회귀가
    못 잡는다(CAP aircraft_sorties·IFF 사각 재발 방지). 골든이 의도적으로 미커버하는
    지표(한국 단독이라 usa_*=0·THAAD/C-RAM/IFF 시나리오 부재)는 KNOWN 화이트리스트로 제외 —
    새로 항상-동일 지표가 생기면(=새 stats 키 미발현) FAIL로 골든 케이스 추가를 유도."""
    from collections import defaultdict
    p = os.path.join(ROOT, 'audit_regression_golden.json')
    if not os.path.exists(p):
        return
    g = json.load(open(p, encoding='utf-8'))
    vals = defaultdict(set)
    cnt = defaultdict(int)
    for rec in g.values():
        for k, v in rec.items():
            vals[k].add(round(v, 4) if isinstance(v, float) else v)
            cnt[k] += 1
    # 골든이 의도적으로 미커버하는 알려진 사각(한국 단독·미편성 시나리오)
    KNOWN = {'ashore_sm3_fired', 'thaad_fired', 'usa_cost', 'usa_shots',
             'iff_failures', 'iff_fratricide'}
    # 케이스 3개 미만에만 등장하는 지표(예: 소수 캠페인 보조 케이스의 _CKEYS)는 표본이
    # 부족해 '전 케이스 동일=vacuous' 판정이 불가(2케이스가 우연히 같을 수 있음). 그 지표의
    # 회귀 안전망은 골든 값 비교(do_check)가 이미 제공하므로 vacuous 판정에서만 제외한다.
    dead = sorted(k for k, s in vals.items()
                  if len(s) == 1 and k not in KNOWN and cnt[k] >= 3)
    check('③', '골든 커버리지(전 케이스 동일값 지표=회귀 사각)', not dead,
          f'미발현 지표 {dead} — 골든 8케이스가 이 경로를 안 밟음'
          f'(새 stats 키면 발현 케이스 추가, 아니면 KNOWN 등재)'
          if dead else f'OK(알려진 사각 {len(KNOWN)}개 제외 전 지표 케이스 간 변별)')


def chk_preset_desc():
    """⑥ 위생: 적 편대 프리셋의 UI 툴팁 설명에 적힌 수량 == 실제 편성 수량.

    편성을 상향하면서 툴팁 텍스트를 함께 고치지 않으면, 사용자는 화면에서 실제와 다른
    편성을 본다(2026-07-14 감사 후속에서 3건 적발: 'A2/AD 항공 포화' 설명 J-16×4인데
    실제 6 · '항모 킬 체인' 설명이 YJ-21 4발을 통째로 누락 · '전면전 포화' 설명 6발인데
    실제 20발). 사람 기억이 아니라 도구로 잡는다.

    툴팁이 '이름 × N' 형태로 수량을 밝힌 항목만 대조한다. 설명은 축약·별칭 표기라
    ('052D형 구축함'을 '052D'로, 'DF-17 (극초음속 활공)'을 'DF-17 (HGV)'로) 이름 전체가
    아니라 **식별 토큰**으로 느슨하게 매칭한다:
      · 설명을 '+'로 잘라 세그먼트(예 '055형 × 1')로 만들고, '×'가 없는 세그먼트는
        수량 미표기(예 항모 '랴오닝(CV-16)')이므로 대조 대상에서 뺀다.
      · DB 키의 선두 토큰(→ 없으면 괄호 안 별칭. '북한 순항미사일 (화살-2)'는 설명에
        '화살-2'로 적힌다)을 세그먼트에서 찾는다.
      · '형'·'급' 접미와 공백은 표기 흔들림이라 양쪽 모두 지우고 비교한다('052D형'↔'052D').
    """
    try:
        import importlib
        ec = importlib.import_module('engine_core')
    except Exception as e:
        check('⑥', '적 편대 프리셋 설명 = 실제 편성', True, f'(스킵: 엔진 import 실패 {e})')
        return
    src = rd('app_main.py')
    m = re.search(r'_ENEMY_PRESET_TIPS\s*=\s*\{(.*?)\n    \}', src, re.S)
    if not m:
        check('⑥', '적 편대 프리셋 설명 = 실제 편성', True, '(스킵: 툴팁 dict 미발견)')
        return
    tips_src = m.group(1)

    def norm(s):
        return s.replace('형', '').replace('급', '').replace(' ', '').upper()

    mism = []
    for name, comp in ec.ENEMY_FLEET_PRESETS.items():
        dm = re.search(r"'" + re.escape(name) + r"':\s*\n((?:\s*'[^']*'\s*\n?)+)", tips_src)
        if not dm:
            continue
        desc = ' '.join(re.findall(r"'([^']*)'", dm.group(1)))
        if '×' not in desc:
            continue          # 수량을 밝히지 않은 설명 — 대조 대상 아님
        segs = []             # [(정규화 세그먼트, 수량)] — 수량을 밝힌 것만
        for seg in re.split(r'\+', desc.replace('\\n', ' ')):
            q = re.search(r'×\s*(\d+)', seg)
            if q:
                segs.append((norm(seg), int(q.group(1))))
        for c in comp:
            head = re.split(r'[ (]', c['preset'])[0]                  # '055형 대형 구축함' → '055형'
            am = re.search(r'\(([^)]+)\)', c['preset'])               # '(화살-2)' 같은 별칭
            alias = am.group(1) if am else None
            # 별칭은 식별자일 때만 쓴다 — '(항모)'·'(상급)' 같은 일반명사를 후보로 삼으면
            # 설명의 산문 문장('항모 전력 포함…')에 헛매칭한다.
            if alias and not re.search(r'[\d\-]', alias):
                alias = None
            hit = None
            for cand in (head, alias):
                if not cand:
                    continue
                for seg, n in segs:
                    if norm(cand) in seg:
                        hit = n
                        break
                if hit is not None:
                    break
            if hit is None:
                # 이름은 나오는데 수량이 없으면(항모 '푸젠(CV-18) +' 처럼) 대조 대상이 아니다.
                if norm(head) in norm(desc):
                    continue
                mism.append(f"[{name}] 설명에 {head} 누락(실제 ×{c['count']})")
            elif hit != c['count']:
                mism.append(f"[{name}] {head} 설명×{hit}≠실제×{c['count']}")
    check('⑥', '적 편대 프리셋 설명 = 실제 편성', not mism,
          '; '.join(mism) if mism else '수량 표기 프리셋 전부 실제 편성과 일치')


def main():
    for fn in (chk_version, chk_gitignore, chk_log_guard, chk_frame_guard,
               chk_flag_triplet, chk_widget_dup, chk_flag_restore_auto, chk_flag_consume_auto,
               chk_effect_coverage,
               chk_spec_count, chk_div_guards, chk_mc_paths, chk_golden_coverage,
               chk_plans_stale, chk_readme_coverage, chk_readme_counts, chk_preset_desc,
               chk_stale_filename, chk_completed_plans, chk_resource_paths,
               chk_memory_freshness, chk_session_log_fresh):
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
    # 커버리지 리포트 — "무엇을 보나/안 보나"를 수치로 가시화(사각 관리, BLIND_SPOTS.md)
    try:
        lau = rd('app_main.py')
        built = set(re.findall(r"['\"](enable_\w+)['\"]\s*:\s*self\.\w+\.isChecked\(\)", lau))
        nblind = 0
        try:
            nblind = sum(1 for _ in re.finditer(r'^\s*\d+\.\s', rd('BLIND_SPOTS.md'), re.M))
        except Exception:
            pass
        print(f"커버리지: 정적검사 {len(results)}항목 · 체크박스 플래그 복원 자동추출 {len(built)}개 "
              f"· 회귀 8×26 · property 불변식(별도 audit_property.py) · 열린 사각 {nblind}건(BLIND_SPOTS.md)")
        print("-" * 64)
    except Exception:
        pass
    npass = sum(1 for r in results if r[2])
    print(f"{npass}/{len(results)} PASS")
    if npass != len(results):
        print("⚠ FAIL 항목은 사람이 검토 — 휴리스틱 오탐일 수도, 실제 회귀일 수도 있다.")
        sys.exit(1)
    print("✅ 정적 스캔 전부 PASS")


if __name__ == '__main__':
    main()
