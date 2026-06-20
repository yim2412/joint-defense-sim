"""표적 우선순위(auto/nearest/fastest/leakers) 레버 효과 재측정 — seed 고정.
v15.11.02 효과 측정이 seed 미고정(노이즈)이었어 재검증. sim_seed + range(1,5).
"""
import numpy as np
from engine import normalize_enemy_db
from engine_v7 import run_battle_simulation

normalize_enemy_db()

_PRESETS = ['전면전 포화', '중국 3축 동시 공격', '러시아 해군 입체',
            '쓰시마 봉쇄 돌파', '북한 포화 공격 (40발)', '수상함 편대전']
_BASE = dict(fleet_region='동해 북부', season='summer', weather='맑음 (주간)',
             enable_munition_limit=True, enable_battle_mode=True,
             enable_ship_evasion=True, enemy_fleet_mode='preset',
             fleet_preset='이지스 기동전단', tactical_interval=30,
             n_threads=4, cd_time_s=10, confirm_time_s=3)


def _cb(tp):
    def cb(state):
        return {'weapon_priority': 'auto', 'max_salvo': 2, 'radar': 'on',
                'maneuver': 'normal', 'target_priority': tp}
    return cb


def run(preset, tp, seed):
    cfg = dict(_BASE, enemy_fleet_preset=preset, sim_seed=seed)
    r = run_battle_simulation(cfg, tactical_cb=_cb(tp))
    return r.get('friendly_score', 0.0)


for preset in _PRESETS:
    print(f'\n=== {preset} ===')
    base = None
    for tp in ('auto', 'nearest', 'fastest', 'leakers'):
        scores = [run(preset, tp, s) for s in range(1, 5)]
        m = np.mean(scores)
        if tp == 'auto':
            base = m
        delta = f'  (Δauto {m-base:+.3f})' if tp != 'auto' else ''
        print(f'  {tp:9s} score={m:.3f}{delta}')
