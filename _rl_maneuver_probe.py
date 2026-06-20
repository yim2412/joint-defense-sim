"""함대 기동 자세(passive/normal/aggressive) 레버 효과 측정 — 빌드 제외 도구.
각 균형 시나리오에서 자세를 고정한 채 friendly_score를 비교. 자세별로 점수가
갈리면(특히 자산방어↑ vs 자원지속성↓ 트레이드오프) RL 학습 신호가 있다는 뜻.
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


def _cb(posture):
    # 무기·살보·레이더·표적은 auto/기본 고정, 자세만 변화시켜 격리 측정.
    def cb(state):
        return {'weapon_priority': 'auto', 'max_salvo': 2, 'radar': 'on',
                'target_priority': 'auto', 'maneuver': posture}
    return cb


def run(preset, posture, seed):
    cfg = dict(_BASE, enemy_fleet_preset=preset, sim_seed=seed)
    r = run_battle_simulation(cfg, tactical_cb=_cb(posture))
    tl = r.get('timeline', {})
    return (r.get('friendly_score', 0.0), r.get('outcome'),
            min(tl.get('resource_min', [1.0]) or [1.0]))


for preset in _PRESETS:
    print(f'\n=== {preset} ===')
    for posture in ('passive', 'normal', 'aggressive'):
        scores, rmins = [], []
        for seed in range(1, 5):   # seed 0은 엔진서 미적용(if seed:) → 1부터
            s, oc, rmin = run(preset, posture, seed)
            scores.append(s); rmins.append(rmin)
        print(f'  {posture:11s} score={np.mean(scores):.3f}  '
              f'min_resource={np.mean(rmins):.3f}')
