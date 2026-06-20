"""
_rl_scenario_probe.py — RL 균형 학습 시나리오 진단 (임시 스크립트, 빌드 제외).

목적: 적 편대 프리셋별로 '약한 정책' vs '강한 정책'에서 friendly_score 분포를
측정해, 행동에 따라 보상이 갈리는(=학습 신호가 있는) 매치업을 찾는다.
  · 약한 정책: weapon_priority=auto, max_salvo=1
  · 강한 정책: weapon_priority=SM-3 Block IIA, max_salvo=4
민감도(strong - weak)가 클수록 RL이 배울 게 많은 균형 시나리오.
"""
from __future__ import annotations
import sys, io, statistics
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from engine import normalize_enemy_db, ENEMY_FLEET_PRESETS
from engine_v7 import run_battle_simulation

normalize_enemy_db()

BASE = dict(
    fleet_region='동해 북부', season='summer', weather='맑음 (주간)',
    enable_munition_limit=True, enable_battle_mode=True,
    enemy_fleet_mode='preset', fleet_preset='이지스 기동전단',
    n_threads=4, cd_time_s=10, confirm_time_s=3, tactical_interval=30,
)

WEAK = {'weapon_priority': 'auto', 'max_salvo': 1}
STRONG = {'weapon_priority': 'SM-3 Block IIA', 'max_salvo': 4}


def fixed_cb(choice):
    def cb(state):
        return dict(choice)
    return cb


def run(preset, choice, seed):
    cfg = dict(BASE)
    cfg['enemy_fleet_preset'] = preset
    cfg['seed'] = seed
    r = run_battle_simulation(cfg, tactical_cb=fixed_cb(choice))
    return float(r.get('friendly_score', 0.0)), r.get('outcome')


SEEDS = [0, 1, 2]
presets = list(ENEMY_FLEET_PRESETS.keys())
if len(sys.argv) > 1:
    presets = presets[:int(sys.argv[1])]

print(f"{'적 편대':28} {'약정책':>8} {'강정책':>8} {'민감도':>8}  outcome(약/강)")
print('-' * 80)
rows = []
for p in presets:
    wsc = [run(p, WEAK, s) for s in SEEDS]
    ssc = [run(p, STRONG, s) for s in SEEDS]
    wm = statistics.mean(x[0] for x in wsc)
    sm = statistics.mean(x[0] for x in ssc)
    wo = wsc[0][1]
    so = ssc[0][1]
    rows.append((sm - wm, p, wm, sm, wo, so))

for sens, p, wm, sm, wo, so in sorted(rows, reverse=True):
    print(f"{p[:28]:28} {wm:8.3f} {sm:8.3f} {sens:8.3f}  {wo}/{so}")
