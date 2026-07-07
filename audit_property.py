#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
audit_property.py — 속성 기반(property) 런타임 감사 (빌드 제외 도구)

회귀(audit_verify_regression)가 "이전과 같은가"만 보는 자기참조 오라클인 데 반해,
이 스크립트는 **입력이 무엇이든 항상 참이어야 할 불변식**을 랜덤 입력 수십~수백 개로
검증하는 **제2의 독립 오라클**이다. 골든값이 틀려도, 새 코드가 골든을 갱신해도,
불변식 위반(확률 범위 이탈·합≠1·NaN/Inf)은 이쪽이 잡는다.

검사 불변식:
  · 모든 확률/비율/통제도 ∈ [0,1]
  · outcome ∈ {win, draw, loss}
  · 캠페인 MC: win_rate + draw_rate + loss_rate = 1
  · 결과 dict 어디에도 NaN/Inf 없음(깊은 스캔)
  · 개수 지표 ≥ 0

사용:  python audit_property.py [N]     # N=케이스 수(기본 40), 위반 있으면 exit 1
재현:  위반 시 (모드, seed, cfg 요약)을 출력 — 그 seed로 재현 가능.
"""
import sys, math, random, argparse

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from engine_core import FLEET_PRESETS, ENEMY_FLEET_PRESETS
from engine_combat import run_v7_simulation, run_battle_simulation
from engine_campaign import run_campaign, monte_carlo_campaign, load_forecast_model

WEATHERS = ['맑음 (주간)', '맑음 (야간)', '흐림', '비', '폭풍']
FLEETS = list(FLEET_PRESETS.keys())
ENEMIES = list(ENEMY_FLEET_PRESETS.keys())
# OFF/ON을 섞어 넣을 대표 전술 토글(엔진이 소비하는 것 중 안전한 것)
TOGGLES = ['enable_png', 'enable_dmo', 'enable_terrain', 'enable_weather_dynamics',
           'enable_munition_limit', 'enable_coord_deception', 'enable_cyber_warfare',
           'enable_campaign_fog']

violations = []   # (모드, seed, 불변식, 상세)


def _finite_scan(obj, path=''):
    """결과 dict를 깊이 순회하며 NaN/Inf 탐지 → 위반 경로 리스트."""
    bad = []
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            bad.append(f"{path}={obj}")
    elif isinstance(obj, dict):
        for k, v in obj.items():
            bad += _finite_scan(v, f"{path}.{k}" if path else str(k))
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj[:200]):        # 대형 timeline은 앞 200개만
            bad += _finite_scan(v, f"{path}[{i}]")
    return bad


def _prob(mode, seed, name, v):
    if v is None:
        return
    if not (0.0 - 1e-9 <= v <= 1.0 + 1e-9):
        violations.append((mode, seed, f"{name}∈[0,1]", f"{name}={v}"))


def _base_cfg(seed, rng):
    cfg = dict(fleet_preset=rng.choice(FLEETS),
               enemy_fleet_preset=rng.choice(ENEMIES),
               weather=rng.choice(WEATHERS), sim_seed=seed)
    for t in TOGGLES:
        if rng.random() < 0.4:
            cfg[t] = True
    return cfg


def check_single(seed, rng):
    cfg = _base_cfg(seed, rng)
    r = run_v7_simulation(dict(cfg))
    _prob('단발', seed, 'intercept_rate', r.get('intercept_rate'))
    for b in _finite_scan(r):
        violations.append(('단발', seed, 'NaN/Inf 없음', b))


def check_battle(seed, rng):
    cfg = _base_cfg(seed, rng); cfg['enable_battle_mode'] = True
    r = run_battle_simulation(dict(cfg))
    if r.get('outcome') not in ('win', 'draw', 'loss'):
        violations.append(('전장', seed, "outcome∈{win,draw,loss}", f"outcome={r.get('outcome')}"))
    _prob('전장', seed, 'friendly_score', r.get('friendly_score'))
    _prob('전장', seed, 'enemy_score', r.get('enemy_score'))
    for b in _finite_scan(r):
        violations.append(('전장', seed, 'NaN/Inf 없음', b))


def check_campaign(seed, rng, model):
    cfg = _base_cfg(seed, rng)
    cfg['enable_campaign_mode'] = True
    cfg['campaign_horizon_h'] = rng.choice([1, 24, 72, 168])
    r = run_campaign(dict(cfg), model=model)
    if r.get('outcome') not in ('win', 'draw', 'loss'):
        violations.append(('캠페인', seed, "outcome∈{win,draw,loss}", f"outcome={r.get('outcome')}"))
    _prob('캠페인', seed, 'mean_control', r.get('mean_control'))
    for z, v in (r.get('control') or {}).items():
        _prob('캠페인', seed, f'control[{z}]', v)
    for b in _finite_scan(r):
        violations.append(('캠페인', seed, 'NaN/Inf 없음', b))


def check_campaign_mc(seed, rng, model):
    cfg = _base_cfg(seed, rng)
    cfg['enable_campaign_mode'] = True
    mc = monte_carlo_campaign(dict(cfg), n=rng.choice([20, 50]), model=model)
    for k in ('win_rate', 'draw_rate', 'loss_rate', 'mean_control_avg',
              'mean_control_min', 'mean_control_max'):
        _prob('캠페인MC', seed, k, mc.get(k))
    s = mc['win_rate'] + mc['draw_rate'] + mc['loss_rate']
    if abs(s - 1.0) > 1e-6:
        violations.append(('캠페인MC', seed, 'win+draw+loss=1', f"합={s}"))
    if not (mc['mean_control_min'] <= mc['mean_control_avg'] + 1e-9
            and mc['mean_control_avg'] <= mc['mean_control_max'] + 1e-9):
        violations.append(('캠페인MC', seed, 'min≤avg≤max',
                           f"{mc['mean_control_min']}/{mc['mean_control_avg']}/{mc['mean_control_max']}"))
    if mc['n_runs'] <= 0:
        violations.append(('캠페인MC', seed, 'n_runs>0', f"n_runs={mc['n_runs']}"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('n', nargs='?', type=int, default=40, help='케이스 수(모드당 n/4)')
    args = ap.parse_args()
    per = max(1, args.n // 4)
    rng = random.Random(20260707)
    model = load_forecast_model()
    print(f"속성 기반 감사 — 모드당 {per}케이스 (단발·전장·캠페인·캠페인MC)")
    print(f"  예측모델 로드: {model is not None}")

    ran = 0
    for i in range(per):
        try:
            check_single(1000 + i, rng); ran += 1
        except Exception as e:
            violations.append(('단발', 1000 + i, '실행 예외', repr(e)))
    for i in range(per):
        try:
            check_battle(2000 + i, rng); ran += 1
        except Exception as e:
            violations.append(('전장', 2000 + i, '실행 예외', repr(e)))
    for i in range(per):
        try:
            check_campaign(3000 + i, rng, model); ran += 1
        except Exception as e:
            violations.append(('캠페인', 3000 + i, '실행 예외', repr(e)))
    for i in range(per):
        try:
            check_campaign_mc(4000 + i, rng, model); ran += 1
        except Exception as e:
            violations.append(('캠페인MC', 4000 + i, '실행 예외', repr(e)))

    print(f"  실행 {ran}케이스 · 불변식 위반 {len(violations)}건")
    if violations:
        print("\n❌ 불변식 위반 (재현: 해당 seed로 재실행):")
        for mode, seed, inv, detail in violations[:40]:
            print(f"  [{mode}] seed={seed} · {inv} · {detail}")
        sys.exit(1)
    print("\n✅ PASS — 모든 불변식 성립(확률[0,1]·합=1·NaN/Inf 0·outcome 유효)")


if __name__ == '__main__':
    main()
