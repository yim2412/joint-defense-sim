"""CAP 전개 자세(forward/normal/defensive) 레버 효과 측정 — 빌드 제외 도구.
각 균형 시나리오에서 CAP 자세만 고정·변화시켜 friendly_score와 요격수를 비교.
요격수가 자세 무관하게 동일하면 그 시나리오엔 CAP 전투기가 없는 것(레버 무효).
"""
import numpy as np
from engine import normalize_enemy_db
from engine_v7 import run_battle_simulation

normalize_enemy_db()

_PRESETS = ['전면전 포화', '중국 3축 동시 공격', '러시아 해군 입체',
            '쓰시마 봉쇄 돌파', '북한 포화 공격 (40발)', '수상함 편대전']
_BASE = dict(fleet_region='동해 북부', season='summer', weather='맑음 (주간)',
             enable_munition_limit=True, enable_battle_mode=True,
             enable_ship_evasion=True, enable_kf21=True,  # 한국 공군 CAP ON
             enemy_fleet_mode='preset',
             fleet_preset='이지스 기동전단', tactical_interval=30,
             n_threads=4, cd_time_s=10, confirm_time_s=3)


def _cb(cap):
    def cb(state):
        return {'weapon_priority': 'auto', 'max_salvo': 2, 'radar': 'on',
                'target_priority': 'auto', 'maneuver': 'normal', 'cap_posture': cap}
    return cb


def run(preset, cap, seed):
    cfg = dict(_BASE, enemy_fleet_preset=preset, sim_seed=seed)
    r = run_battle_simulation(cfg, tactical_cb=_cb(cap))
    log = r.get('log') or []
    cap_engagements = sum(1 for l in log if 'CAP' in str(l))
    # 통계는 result 최상위에 펼쳐져 있음(r['stats'] 아님).
    return r.get('friendly_score', 0.0), cap_engagements


for preset in _PRESETS:
    print(f'\n=== {preset} ===')
    for cap in ('forward', 'normal', 'defensive'):
        scores, engs = [], []
        for seed in range(1, 5):   # seed 0은 엔진서 미적용(if seed:) → 1부터
            s, e = run(preset, cap, seed)
            scores.append(s); engs.append(e)
        print(f'  {cap:10s} score={np.mean(scores):.3f}  '
              f'CAP교전={np.mean(engs):.1f}')
