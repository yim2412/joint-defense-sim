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
