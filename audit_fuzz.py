#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
audit_fuzz.py — 수치 cfg 키 경계값 fuzzing (자동 오류 탐지 그물 B).

engine_combat/engine_core에서 `cfg.get('key', <숫자>)` 형태의 수치 키를 자동 추출해
극단값(0·음수·거대값)을 하나씩 주입, 시뮬을 실제로 돌려
▸크래시(예외) ▸NaN/Inf ▸확률값 범위 위반(intercept_rate·friendly_score ∉ [0,1])을 자동 탐지한다.

배경: dmo_spread_km=0 → 0나눗셈 같은 "경계값에서만 터지는" 버그는 정적 스캔·회귀가
못 잡는다(아무도 그 값을 안 넣어봐서). 이 도구가 수치 키를 전수 극단 주입해 발굴한다.
(BLIND_SPOTS 7번 대응 — 비-enable_ 수치 키 경계 자동 점검.)

경로 커버리지(v18.02): 단발(run_v7_simulation)뿐 아니라 **전장(run_battle_simulation)**
경로도 fuzzing. 전장은 BattleEngine 고유 틱 루프·목표 판정 등 단발과 다른 코드라
경계값 버그가 별도로 잠재할 수 있다.

v20 확장: **캠페인(run_campaign) 경로 추가**. 과거엔 "캠페인은 수치 cfg 키가 없다"는
전제로 pairwise에만 맡겼으나, v20 지상군 층이 들어오며 그 전제가 깨졌다
(engine_army의 amphib_coastal_defense 등). 수치 키 추출 대상도 경로별 엔진 파일로
분리해, 새 엔진이 늘 때 그 파일만 등록하면 자동으로 fuzzing되게 한다.

사용:
    python audit_fuzz.py                  # 단발 fuzzing (발견 있으면 exit 1)
    python audit_fuzz.py --mode battle    # 전장 fuzzing
    python audit_fuzz.py --mode campaign  # 캠페인 fuzzing(지상군·공군층 포함)
    python audit_fuzz.py --mode all       # 셋 다
"""
import sys, io, os, re, math

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_combat import run_v7_simulation, run_battle_simulation   # noqa: E402
from engine_campaign import run_campaign, load_forecast_model        # noqa: E402
from audit_verify_regression import _BASE                            # noqa: E402

# 주입 극단값 — 0(0나눗셈)·음수(부호 가정 위반)·거대값(오버플로·무한루프 유발)
EXTREMES = [0, -1, 1_000_000_000]

# 극단 주입이 의미상 무해가 아닌(=시뮬을 왜곡할 뿐 버그 아님) 키는 제외 화이트리스트.
# 여기 없는 키에서 크래시/NaN이 나면 진짜 방어 부재로 본다.
SKIP_KEYS = set()

# 거대값 주입 시 전장 시뮬 시간 지평이 폭발하는 키 — 0·-1만 주입(1e9 제외).
# 전장은 위협 소진 시 조기 종료하나 무한 재생성 시나리오에서 안전판.
HUGE_SKIP_KEYS = {'battle_horizon_s'}


def extract_numeric_keys(files):
    keys = set()
    for fn in files:
        with open(fn, encoding='utf-8') as f:
            txt = f.read()
        for m in re.finditer(r"cfg\.get\((['\"])([a-z_]+)\1,\s*(-?[0-9][0-9.]*)", txt):
            key = m.group(2)
            if key.startswith('enable_') or key in SKIP_KEYS:
                continue
            keys.add(key)
    return sorted(keys)


def scan_result(r):
    """결과에서 NaN/Inf·확률 범위 위반 탐지. 반환: 문제 문자열 리스트(최대 5)."""
    probs = []

    def walk(o, path=''):
        if len(probs) >= 5:
            return
        if isinstance(o, dict):
            for k, v in o.items():
                walk(v, f"{path}.{k}")
        elif isinstance(o, (list, tuple)):
            for i, v in enumerate(o[:20]):
                walk(v, f"{path}[{i}]")
        elif isinstance(o, float):
            if math.isnan(o):
                probs.append(f"NaN@{path}")
            elif math.isinf(o):
                probs.append(f"Inf@{path}")

    walk(r)
    for pk in ('intercept_rate', 'friendly_score'):
        pv = r.get(pk)
        if isinstance(pv, (int, float)) and not (-1e-9 <= pv <= 1.0 + 1e-9):
            probs.append(f"{pk}={pv}(범위위반)")
    return probs[:5]


_MODEL = None


def _campaign_run(cfg):
    global _MODEL
    if _MODEL is None:
        _MODEL = load_forecast_model()
    return run_campaign(cfg, model=_MODEL)


# 전술 엔진 파일 — 단발·전장이 공유
_TACTICAL_FILES = ['engine_combat.py', 'engine_core.py']
# 작전급 엔진 파일 — 캠페인이 조합 호출(공군·지상군 층 포함)
_CAMPAIGN_FILES = ['engine_campaign.py', 'engine_airforce.py', 'engine_army.py']


# ── 모드 정의: (라벨, 진입함수, base cfg, 수치키 추출 대상 파일) ────────────
def _bases():
    single_base = dict(_BASE, fleet_preset='이지스 기동전단',
                       enemy_fleet_preset='입체 포화 (최강)', sim_seed=1)
    battle_base = dict(_BASE, fleet_preset='기동전단 기본',
                       enemy_fleet_preset='랴오닝 항모전단', sim_seed=1,
                       battle_horizon_s=1200)
    # 캠페인은 공군·지상군 층을 켜야 그 층의 수치 키가 실제 코드 경로를 지난다
    # (OFF면 amphib_coastal_defense 등이 읽히지도 않아 fuzzing이 공회전).
    campaign_base = dict(_BASE, fleet_preset='기동전단 기본',
                         enemy_fleet_preset='랴오닝 항모전단', campaign_seed=1,
                         enable_air_campaign=True, enable_army_campaign=True,
                         enable_coastal_sam=True, enable_amphibious=True,
                         enable_enemy_sead=True)
    return {
        'single':   ('단발', run_v7_simulation, single_base, _TACTICAL_FILES),
        'battle':   ('전장', run_battle_simulation, battle_base, _TACTICAL_FILES),
        'campaign': ('캠페인', _campaign_run, campaign_base, _CAMPAIGN_FILES),
    }


def fuzz_mode(label, run_fn, base, keys):
    print(f"\n── {label} 경로 fuzzing ──")
    try:
        run_fn(dict(base))
    except Exception as e:
        print(f"❌ {label} baseline 크래시(fuzzing 이전) — {type(e).__name__}: {e}")
        return None   # baseline 실패
    findings = []
    for key in keys:
        for ext in EXTREMES:
            if ext == 1_000_000_000 and key in HUGE_SKIP_KEYS:
                continue   # 시간 폭발 방지
            cfg = dict(base)
            cfg[key] = ext
            try:
                r = run_fn(cfg)
            except Exception as e:
                findings.append((key, ext, f"CRASH {type(e).__name__}: {e}"))
                print(f"  🔴 {key}={ext}: CRASH {type(e).__name__}: {e}")
                continue
            probs = scan_result(r)
            if probs:
                findings.append((key, ext, '|'.join(probs)))
                print(f"  🟡 {key}={ext}: {'|'.join(probs)}")
    return findings


def main():
    argv = sys.argv[1:]
    mode = 'single'
    if '--mode' in argv:
        mode = argv[argv.index('--mode') + 1]
    modes = ['single', 'battle', 'campaign'] if mode == 'all' else [mode]

    bases = _bases()
    total = []
    for m in modes:
        if m not in bases:
            print(f"❌ 알 수 없는 모드: {m} (single|battle|campaign|all)")
            return 2
        label, run_fn, base, files = bases[m]
        keys = extract_numeric_keys(files)   # 경로별 엔진 파일에서 수치 키 추출
        print(f"\n[{label}] 수치 cfg 키 {len(keys)}개 × 극단값 {len(EXTREMES)}종 "
              f"≈ {len(keys) * len(EXTREMES)}회 fuzzing  (추출: {', '.join(files)})")
        res = fuzz_mode(label, run_fn, base, keys)
        if res is None:
            return 1
        total.extend((m,) + f for f in res)

    print(f"\n{'='*56}")
    if total:
        print(f"⚠ fuzzing 발견 {len(total)}건 — 위 키의 극단값 방어 점검 필요")
        return 1
    print(f"✅ fuzzing PASS — 경로 {modes} 수치 키 극단값 전부 크래시·NaN·범위위반 0")
    return 0


if __name__ == '__main__':
    sys.exit(main())
