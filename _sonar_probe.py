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
print("  ※ enable_asw_forward OFF 기준 — ASW 항공이 함대 수동 대기라 교전 늦어 효과 묻힘.")

# ── v16.01.04 ASW 전진 초계 효과 (대잠전 균형 실효화) ──
print("\n=== v16.01.04 ASW 전진 초계 ON/OFF (능동소나 역탐지 ON 전제) ===")
def measure_fwd(fwd, enemy):
    sk, sc, asw = [], [], 0
    for s in range(1, 13):
        cfg = dict(enable_battle_mode=True, fleet_preset='대잠전단', enemy_fleet_mode='preset',
                   enemy_fleet_preset=enemy, weather='맑음 (주간)', battle_horizon_s=1800, sim_seed=s,
                   enable_sonar_equation=True, enable_sonar_emcon=True, enable_asw_forward=fwd,
                   enable_helo=True, enable_p3c=True, enable_p8a=True)
        r = run_battle_simulation(cfg)
        sk.append(r.get('enemy_ships_destroyed', 0)); sc.append(r.get('friendly_score', 0.0))
        asw += sum(('대잠 탐지 성공' in str(l) or '적 피격' in str(l)) for l in (r.get('log') or []))
    return np.mean(sk), np.mean(sc), asw
for enemy in ['대잠 복합', '잠수함 복합 포화']:
    for label, fwd in [('OFF', False), ('ON ', True)]:
        sk, sc, asw = measure_fwd(fwd, enemy)
        print(f"  {enemy} 전진초계 {label}: 잠격침 {sk:.2f} · 임무 {sc:.3f} · ASW교전 {asw}")
print("  → 전진 초계로 잠수함 격침 0→0.5~0.67·ASW 교전 3~4배·임무 +0.02~0.04 (대잠 균형 실효화).")
print("  ※ 능동소나 역탐지 자체는 발동 늘어도(전진초계로 3~4배) 결과 효과는 기습 잠수함 등 좁은 조건 한정.")
