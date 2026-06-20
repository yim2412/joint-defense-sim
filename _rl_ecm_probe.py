"""ECM 자세(off/normal/strong) 레버 효과 측정 — seed 고정. 빌드 제외 도구.
ECM은 적 대함미사일 Pk만 낮춤(탄도·HGV·ARM 무효) → 미사일 위주 시나리오서 신호 기대.
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


def _cb(ecm):
    def cb(state):
        return {'weapon_priority': 'auto', 'max_salvo': 2, 'radar': 'on',
                'target_priority': 'auto', 'maneuver': 'normal',
                'cap_posture': 'normal', 'ecm': ecm}
    return cb


def run(preset, ecm, seed):
    cfg = dict(_BASE, enemy_fleet_preset=preset, sim_seed=seed)
    r = run_battle_simulation(cfg, tactical_cb=_cb(ecm))
    return r.get('friendly_score', 0.0)


for preset in _PRESETS:
    print(f'\n=== {preset} ===')
    base = np.mean([run(preset, 'normal', s) for s in range(1, 5)])
    print(f'  normal  score={base:.3f}')
    for ecm in ('off', 'strong'):
        m = np.mean([run(preset, ecm, s) for s in range(1, 5)])
        print(f'  {ecm:7s} score={m:.3f}  (Δnormal {m-base:+.3f})')
