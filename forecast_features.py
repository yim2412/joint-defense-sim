# -*- coding: utf-8 -*-
"""
forecast_features.py — v15.2 즉시예측 대리모델 특징화 (빌더·GUI 공유, exe 번들).

featurize(fleet_ships, enemy_fleet, weather) → np.ndarray (고정 길이).
함대(함종 리스트)·적(편성 리스트)·날씨를 수치 벡터로. 순수 함수(엔진·회귀 무관).
"""
from __future__ import annotations
import numpy as np

from engine_core import SHIP_DB, ENEMY_DB, WEATHER_DB, ENEMY_FLEET_PRESETS

# ── 함종 tier 분류 ──────────────────────────────────────────────────────────
_AEGIS    = {'KDX-III-B1', 'KDX-III-B2', 'DDG-51', 'CG-47'}
_DDG      = {'KDX-II'}
_FFX      = {'FFX-I', 'FFX-II', 'FFX-III'}
_SMALL    = {'PKG', 'PCC', 'PKX-B'}
_SUPPORT  = {'LPH', 'AOE', 'LST', 'AO', 'LPD', 'CVN'}
_SUBMAR   = {'KSS-I', 'KSS-II', 'KSS-III', 'SSN'}
_SHORE    = {'CRAM', 'CSAM'}
_UNMANNED = {'USV', 'UUV'}

_SAM_KEYS = ['SM-3 Block IIA', 'SM-6', 'SM-6 Block IB', 'SM-2 Block IIIB',
             'ESSM Block II', '해궁 (K-SAAM)', 'RIM-116 RAM']

# FriendlyShipObj._hp_map와 동일(내탄성 프록시)
_HP_MAP = {
    'KDX-III-B2': 5, 'KDX-III-B1': 5, 'KDX-II': 4,
    'FFX-I': 3, 'FFX-II': 3, 'FFX-III': 3,
    'DDG-51': 5, 'CG-47': 5, 'CVN': 8,
    'LPD': 3, 'SSN': 3, 'LST': 3, 'AO': 2,
    'KSS-I': 2, 'KSS-II': 2, 'KSS-III': 3,
    'USV': 2, 'UUV': 1,
}

# 적 type 분류
_MISSILE_TYPES  = {'탄도미사일', '대방사미사일', '극초음속활공체', '저고도기동탄도', '순항미사일'}
_AIRCRAFT_TYPES = {'전투기', '전폭기', '폭격기'}
_SHIP_TYPES     = {'고속정', '구축함', '초계함', '호위함', '항모', '상륙함'}
_SUB_TYPES      = {'잠수함'}
_BALLISTIC      = {'탄도미사일', '저고도기동탄도'}

_WX_KEYS = ['detect_range_factor', 'radar_factor', 'sonar_factor',
            'intercept_prob_delta', 'cd_time_factor']

FEATURE_NAMES = [
    # 함대(15)
    'n_aegis', 'n_ddg', 'n_ffx', 'n_small', 'n_support', 'n_sub', 'n_shore',
    'n_unmanned', 'n_ships_total', 'sum_channels', 'sum_sam', 'has_bmd',
    'max_air_sensor_km', 'sum_hp', 'n_us',
    # 적(11)
    'e_total', 'e_missile', 'e_aircraft', 'e_ship', 'e_sub',
    'e_supersonic', 'e_ballistic', 'e_hgv', 'e_max_speed', 'e_total_salvo',
    'e_has_carrier',
    # 환경(5)
    *(f'wx_{k}' for k in _WX_KEYS),
]
N_FEATURES = len(FEATURE_NAMES)


def _resolve_enemy(enemy_fleet=None, enemy_preset: str | None = None) -> list:
    """적 편성을 [{'preset','count'}] 리스트로 정규화."""
    if enemy_fleet:
        return enemy_fleet
    if enemy_preset:
        return ENEMY_FLEET_PRESETS.get(enemy_preset, [])
    return []


def featurize(fleet_ships: list, enemy_fleet=None, weather: str = '맑음 (주간)',
              enemy_preset: str | None = None) -> np.ndarray:
    """함대(함종 문자열 리스트)·적 편성·날씨 → 특징 벡터(np.ndarray, 길이 N_FEATURES)."""
    # ── 함대 ──
    n = {k: 0 for k in ('aegis', 'ddg', 'ffx', 'small', 'support', 'sub', 'shore', 'unmanned')}
    sum_ch = sum_sam = has_bmd = max_sensor = sum_hp = n_us = 0
    for st in fleet_ships:
        spec = SHIP_DB.get(st)
        if not spec:
            continue
        if   st in _AEGIS:    n['aegis'] += 1
        elif st in _DDG:      n['ddg'] += 1
        elif st in _FFX:      n['ffx'] += 1
        elif st in _SMALL:    n['small'] += 1
        elif st in _SUPPORT:  n['support'] += 1
        elif st in _SUBMAR:   n['sub'] += 1
        elif st in _SHORE:    n['shore'] += 1
        elif st in _UNMANNED: n['unmanned'] += 1
        sum_ch += spec.get('max_channels', 0)
        inv = spec.get('default_inventory', {})
        sum_sam += sum(inv.get(w, 0) for w in _SAM_KEYS)
        if inv.get('SM-3 Block IIA', 0) > 0 or 'BMD' in spec.get('role', []):
            has_bmd = 1
        max_sensor = max(max_sensor, spec.get('sensor_km', {}).get('대공', 0))
        sum_hp += _HP_MAP.get(st, 4)
        if spec.get('nation') == 'USA':
            n_us += 1
    n_ships_total = sum(n.values())

    # ── 적 ──
    enemy = _resolve_enemy(enemy_fleet, enemy_preset)
    e_total = e_missile = e_aircraft = e_ship = e_sub = 0
    e_supersonic = e_ballistic = e_hgv = e_salvo = e_carrier = 0
    e_max_speed = 0.0
    for spec in enemy:
        name = spec.get('preset', '')
        cnt  = int(spec.get('count', 1))
        info = ENEMY_DB.get(name, {})
        if not info:
            continue
        ttype = info.get('type', '')
        spd   = float(info.get('speed_ms', 300))
        e_total += cnt
        if   ttype in _MISSILE_TYPES:  e_missile += cnt
        elif ttype in _AIRCRAFT_TYPES: e_aircraft += cnt
        elif ttype in _SHIP_TYPES:     e_ship += cnt
        elif ttype in _SUB_TYPES:      e_sub += cnt
        if spd >= 600:                 e_supersonic += cnt
        if ttype in _BALLISTIC:        e_ballistic += cnt
        if ttype == '극초음속활공체':   e_hgv += cnt
        if ttype == '항모':            e_carrier = 1
        e_max_speed = max(e_max_speed, spd)
        # 살보: 미사일 발사 위협은 count×평균살보, 직접 미사일은 count
        salvo = info.get('missile_salvo_max', 1) if info.get('can_fire_missile', False) else 1
        e_salvo += cnt * max(1, int(salvo))

    # ── 환경 ──
    wx = WEATHER_DB.get(weather, WEATHER_DB.get('맑음 (주간)', {}))
    wx_vals = [float(wx.get(k, 1.0 if k != 'intercept_prob_delta' else 0.0)) for k in _WX_KEYS]

    return np.array([
        n['aegis'], n['ddg'], n['ffx'], n['small'], n['support'], n['sub'],
        n['shore'], n['unmanned'], n_ships_total, sum_ch, sum_sam, has_bmd,
        max_sensor, sum_hp, n_us,
        e_total, e_missile, e_aircraft, e_ship, e_sub,
        e_supersonic, e_ballistic, e_hgv, e_max_speed, e_salvo, e_carrier,
        *wx_vals,
    ], dtype=float)


def fleet_ships_from_preset(preset: list) -> list:
    """FLEET_PRESETS 항목([{name,type}]) → 함종 문자열 리스트."""
    return [spec['type'] for spec in preset]
