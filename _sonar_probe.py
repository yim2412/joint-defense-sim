# -*- coding: utf-8 -*-
"""
_sonar_probe.py — v16.01.03 능동 소나 핑 역탐지 발동·효과 측정 (빌드 제외 도구)

능동 소나(헬기 디핑/소노부이)로 적 잠수함 탐지 시 역탐지(은닉 해제·어뢰 반격 앞당김·회피)가
트리거되는지 확인한다. enable_sonar_emcon ON/OFF + enable_sonar_equation ON + ASW 항공 활성.

결과 해석: 역탐지는 정상 발동(아래 발동 횟수)하나, 현 대잠전 밸런스에서 잠수함 교전이
1800초 안에 결판나지 않아(잠격침≈0·아군피격≈0) 효과가 임무 결과에 잘 드러나지 않는다.
ARM과 동일 패턴 — 메커니즘은 작동하되 실효는 대잠전 균형 실효화(후속, _PLANS v16.1)에 의존.
"""
import warnings; warnings.filterwarnings('ignore')
import numpy as np
from engine_v7 import run_battle_simulation

def measure(emcon, enemy, fleet='대잠전단'):
    sk, sh, sc, rev = [], [], [], 0
    for s in range(1, 13):
        cfg = dict(enable_battle_mode=True, fleet_preset=fleet, enemy_fleet_mode='preset',
                   enemy_fleet_preset=enemy, weather='맑음 (주간)', battle_horizon_s=1800, sim_seed=s,
                   enable_sonar_equation=True, enable_sonar_emcon=emcon,
                   enable_helo=True, enable_p3c=True, enable_p8a=True)
        r = run_battle_simulation(cfg)
        sk.append(r.get('enemy_ships_destroyed', 0))
        sh.append(r.get('friendly_hits', 0))
        sc.append(r.get('friendly_score', 0.0))
        if emcon:
            rev += sum('역탐지' in str(l) for l in (r.get('log') or []))
    return np.mean(sk), np.mean(sh), np.mean(sc), rev

print("=== v16.01.03 능동 소나 핑 역탐지 — 발동·효과 (대잠전단, 소나방정식+ASW항공 ON) ===")
for enemy in ['북한 잠수함 선제 기습', '대잠 복합']:
    for label, em in [('OFF', False), ('ON ', True)]:
        sk, sh, sc, rev = measure(em, enemy)
        tail = f" · 역탐지 발동 {rev}회" if em else ""
        print(f"  {enemy} 역탐지 {label}: 잠격침 {sk:.2f} · 아군피격 {sh:.2f} · 임무 {sc:.3f}{tail}")
print("  ※ 역탐지는 정상 발동하나 현 대잠전 밸런스(잠수함 교전 미결판)로 결과 효과는 미미.")
print("    실효는 대잠전 균형 실효화(_PLANS v16.1) 후 발현 — ARM 실효화와 동일 패턴.")
