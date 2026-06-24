# -*- coding: utf-8 -*-
"""
_emcon_probe.py — v16.01.01 ESM→ARM 역탐지 메커니즘 단위 검증 (빌드 제외 도구)

ESM/ARM stale 유도의 핵심 거동을 단위로 검증한다. 시나리오 평균 측정은 의도적으로
생략 — ARM은 어느 실전 프리셋에도 편성돼 있지 않고(ENEMY_DB에만 정의), standalone
미사일이 함정 대공 탐지거리(~880km)에서 스폰돼 사거리(110km)의 8배 먼 곳에서 출발 →
이지스급 함정이 거의 100% 요격해 기함 도달이 드물다([[project_battle_engine]] v15.11.01
"ARM 약해 레이더 OFF 열등"과 동일한 구조적 한계). 따라서 시나리오 평균 효과는 미미하며,
실효를 보려면 ARM 스폰 거리 현실화 + ARM 편대 편성이 동반돼야 한다(후속 과제). 여기서는
메커니즘 자체의 정확성만 입증한다.
"""
import warnings; warnings.filterwarnings('ignore')
import math
from engine_v7 import BattleEngine, MissileObj, FriendlyShipObj, LatLon

class _Stub: pass
e = _Stub(); e._emcon_arm = True; e.t = 100.0

ship = FriendlyShipObj.__new__(FriendlyShipObj)
ship.pos = LatLon.from_xy(0.0, 0.0); ship.radar_off_until = 0.0; ship.alive = True; ship.name = '테스트함'

def arm(x_km):
    m = MissileObj(mtype='enemy_strike', name='Kh-31P', pos=LatLon.from_xy(x_km*1000.0, 0.0),
                   target=ship, speed_ms=1000.0, pk_base=0.85, owner_id=-1, t_spawn=0.0)
    m.is_arm = True
    return m

ok = True

# (1) 레이더 ON → ESM 실시간 포착 → aim = 함정 현재 위치
m = arm(10); e.missiles = [m]
BattleEngine._arm_esm_update(e)
c1 = abs(m.arm_aim_pos.x) < 1 and abs(m.arm_aim_pos.y) < 1
print(f"[1] 레이더 ON → arm_aim_pos=({m.arm_aim_pos.x:.0f},{m.arm_aim_pos.y:.0f}) == 함정(0,0)  {'PASS' if c1 else 'FAIL'}")
ok &= c1

# (2) 함정 2km 이동 + 레이더 OFF → aim 갱신 안 됨(stale, 옛 위치 유지)
ship.pos = LatLon.from_xy(0.0, 2000.0); ship.radar_off_until = 200.0
BattleEngine._arm_esm_update(e)
c2 = abs(m.arm_aim_pos.y) < 1
print(f"[2] 레이더 OFF → arm_aim_pos.y={m.arm_aim_pos.y:.0f} == 옛위치 유지(stale)  {'PASS' if c2 else 'FAIL'}")
ok &= c2

# (3) stale 이격 → Pk 급감(레이더 OFF로 ARM 무력화)
miss_d = m.arm_aim_pos.dist_to(ship.pos); pk = m.pk_base * math.exp(-miss_d/150.0)
c3 = pk < 0.01
print(f"[3] 이격 {miss_d:.0f}m → Pk {m.pk_base:.0%}→{pk:.1%}  {'PASS' if c3 else 'FAIL'}")
ok &= c3

# (4) 레이더 ON 유지 → 이격 0 → Pk 거의 그대로(정확 명중, EMCON 딜레마 반대편)
ship.pos = LatLon.from_xy(0.0, 0.0); ship.radar_off_until = 0.0
m2 = arm(10); e.missiles = [m2]
BattleEngine._arm_esm_update(e)
miss2 = m2.arm_aim_pos.dist_to(ship.pos); pk2 = m2.pk_base * math.exp(-miss2/150.0)
c4 = pk2 > 0.8
print(f"[4] 레이더 ON 유지 → 이격 {miss2:.0f}m → Pk {pk2:.0%}(정확 명중)  {'PASS' if c4 else 'FAIL'}")
ok &= c4

print("=== 메커니즘 단위 검증", "전부 PASS ===" if ok else "FAIL ===")

# ── 시나리오 측정 (v16.01.02 ARM 실효화 후) ──
# ARM 실효화 = ①standalone 스폰 거리를 대공탐지(~880km)→ARM 사거리 90%로 현실화
#             ②ARM을 '전자전 SEAD 제압' 편대로 편성(이전엔 ENEMY_DB에만 정의·미편성).
# → ARM이 비로소 약한 함정에 도달(0→다수 명중)하며 레이더 방사 상태에 민감해진다.
# EMCON 딜레마: 레이더 ON=ARM 명중(탐지 우위) / 레이더 OFF+함정 기동=ARM 회피(탐지 손실).
import numpy as np
from engine import ENEMY_FLEET_PRESETS, FLEET_PRESETS
from engine_v7 import run_battle_simulation
ENEMY_FLEET_PRESETS['_ARM_ONLY'] = [   # ARM만(레이더만 손상, 격침 없음) → 효과 격리
    {'preset': 'Kh-31P 대방사미사일', 'count': 8},
    {'preset': 'LD-10 대방사미사일',  'count': 6},
]
FLEET_PRESETS['_KDX2_SOLO'] = [{'name': '충무공이순신함', 'type': 'KDX-II'}]
def radar_off_cb(state): return {'radar': 'off', 'evade': 'aggressive'}  # 레이더 끄고 기동(EMCON)
def measure(radar_cb, em):
    h = []
    for s in range(1, 9):
        cfg = dict(enable_battle_mode=True, fleet_preset='_KDX2_SOLO', enemy_fleet_mode='preset',
                   enemy_fleet_preset='_ARM_ONLY', weather='맑음 (주간)', battle_horizon_s=1800,
                   sim_seed=s, enable_esm_arm=em, enable_ship_evasion=True)
        h.append(run_battle_simulation(cfg, tactical_cb=radar_cb).get('friendly_hits', 0))
    return np.mean(h)
print("\n=== v16.01.02 ARM 실효화 — EMCON 딜레마 (KDX-II 단독, ARM 사거리 스폰) ===")
print(f"  레이더 ON 유지   → ARM 피격 {measure(None, True):.2f}발 (탐지 우위, ARM에 노출)")
print(f"  레이더 OFF+기동  → ARM 피격 {measure(radar_off_cb, True):.2f}발 (ARM 회피, 탐지 손실)")
print("  ※ enable_esm_arm 토글 ON/OFF 결과 차이는 '레이더 OFF+함정 정지' 엣지케이스에 한정")
print("    (기존=비현실적 회피, EMCON ON=현실적 명중). 토글은 유도 모델 정밀화 성격.")
