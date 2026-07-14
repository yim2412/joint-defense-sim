# -*- coding: utf-8 -*-
"""DB 내부 모순 탐지기 — 공개 제원 없이도 '스스로 앞뒤가 안 맞는 값'을 잡는다.

왜 필요한가 (v20.5에서 터진 오류들이 기존 감사에 하나도 안 걸렸다):
  · SM-3 최소 요격고도 40km  — 실제는 외기권 100km. 하위 BMD 계층의 표적을 가로챘다.
  · KN-23 정점고도 2km       — 실제 30~50km. 순항미사일 수준으로 잡혀 있었다.
  · MQ-9B 해상 탐지 120km    — 실제 SeaVue 200해리(370km).
  · 052D가 사거리 540km YJ-18을 싣고 44km까지 접근해 발사(스폰 거리 = 아군 탐지거리).
회귀는 '이전과 같은가'만 보고, 정적 스캔은 구조만 본다 — **값이 그럴듯하나 틀린 경우**는
둘 다 못 잡는다. 이 도구는 DB 항목들 사이의 **논리적 모순**을 찾는다(외부 제원 불필요).

사용: python audit_db_consistency.py
"""
from __future__ import annotations
import io, sys

if hasattr(sys.stdout, 'buffer'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from engine_core import ENEMY_DB, FRIENDLY_DB, FRIENDLY_AIRCRAFT_DB
from engine_combat import FRIENDLY_STRIKE_DB

FINDINGS: list[tuple[str, str, str]] = []   # (심각도, 검사명, 내용)


def flag(sev: str, chk: str, msg: str):
    FINDINGS.append((sev, chk, msg))


# ── ① 마하 표기 ↔ 실제 속도 정합 ──────────────────────────────────────────
# 이름·설명에 '마하 N'이라 써놓고 speed_ms가 딴판이면 둘 중 하나가 거짓말이다.
_MACH_MS = 340.0

def _mach_check(label: str, txt: str, v: float):
    """이름에 '초음속/극초음속'이라 써 있으면 그 속도가 실제로 그런지 본다."""
    if not v:
        return
    if '극초음속' in txt:
        if v < _MACH_MS * 5.0:
            flag('HIGH', '마하표기↔속도',
                 f"{label}: '극초음속'인데 {v:.0f} m/s (마하 {v/_MACH_MS:.1f}) < 마하 5")
    elif '초음속' in txt:          # '극초음속'을 먼저 걸러야 오탐이 없다
        if v < _MACH_MS:
            flag('HIGH', '마하표기↔속도',
                 f"{label}: '초음속'인데 {v:.0f} m/s (마하 {v/_MACH_MS:.2f}) = 아음속")


def chk_mach_vs_speed():
    for name, info in ENEMY_DB.items():
        # 플랫폼(함정·항공기) 자체의 이름과 속도
        _mach_check(name, name, info.get('speed_ms') or 0)
        # ★ 탑재 미사일은 **미사일 속도**와 비교해야 한다.
        #   (함정 speed_ms와 비교하면 '052D형 구축함이 아음속'이라는 오탐이 난다 —
        #    첫 실행에서 실제로 그 오탐이 나왔고, 그래서 여기서 분리한다)
        mname = info.get('missile_name', '')
        if mname:
            _mach_check(f"{name} 탑재 {mname}", mname, info.get('missile_speed_ms') or 0)


# ── ② 요격체 교전창 ↔ 실제 위협 고도 (죽은 계층 / 요격 불가 위협) ─────────
# SM-3 문턱 버그가 이 검사에 걸린다: 요격창이 어떤 위협도 못 덮거나,
# 반대로 자기 것이 아닌 저고도 표적까지 덮으면 모순.
def chk_engage_window():
    alts = {n: (i.get('altitude_m') or 0) for n, i in ENEMY_DB.items()}
    if not alts:
        return
    for wname, w in FRIENDLY_DB.items():
        lo = w.get('alt_min_m')
        hi = w.get('alt_max_m')
        if lo is None and hi is None:
            continue
        lo = lo or 0
        hi = hi if hi is not None else float('inf')
        covered = [n for n, a in alts.items() if lo <= a <= hi]
        if not covered:
            flag('HIGH', '요격창↔위협고도',
                 f"{wname}: 교전 고도창 {lo/1000:.0f}~{hi/1000:.0f}km 안에 드는 위협이 "
                 f"**하나도 없다** → 이 요격 계층은 영원히 발사되지 않는다(죽은 계층)")


# ── ③ 아군 무기 사거리 ↔ 그 표적을 볼 수 있는 탐지거리 ───────────────────
# ★ 이번 세션의 핵심 발견: 해성-II는 250km를 날아가는데 대함 탐지는 44km였다.
#   무기 사거리가 탐지거리보다 훨씬 길면 그 사거리는 **영원히 쓰이지 않는다**.
_SURF_DETECT_KM_TYPICAL = 45.0   # 수상 레이더 수평선 한계(코드 기본값과 동일 계열)

_LAND_ATTACK = ('Tomahawk', '현무-3C', '현무-4')   # 지상 타격용 — 해상 탐지와 무관(오탐 제외)

def chk_weapon_vs_detect():
    for wname, w in FRIENDLY_STRIKE_DB.items():
        if any(k in wname for k in _LAND_ATTACK):
            continue
        rng = w.get('range_km') or 0
        if rng > _SURF_DETECT_KM_TYPICAL * 2:
            flag('MED', '무기사거리↔탐지',
                 f"{wname}: 사거리 {rng:.0f}km인데 수상 탐지는 약 {_SURF_DETECT_KM_TYPICAL:.0f}km "
                 f"({rng/_SURF_DETECT_KM_TYPICAL:.1f}배) → 표적을 볼 수 없어 사거리의 "
                 f"{100-100*_SURF_DETECT_KM_TYPICAL/rng:.0f}%가 사장된다(광역 정찰 자산 필요)")


# ── ④ 적 함정 미사일 사거리 ↔ 교전 개시 거리 ─────────────────────────────
# 052D가 540km 미사일을 싣고 44km까지 다가와 쏘던 문제. 스탠드오프(v18.05.11)로 고쳤으나,
# 누군가 그 기능을 끄거나 되돌리면 다시 비물리가 된다 → 상시 감시.
def chk_enemy_standoff():
    from engine_combat import TimeStepEngine   # noqa: F401  (플래그 기본값 확인용)
    import inspect, re
    src = inspect.getsource(TimeStepEngine.__init__)
    m = re.search(r"enable_standoff_spawn['\"],\s*(True|False)", src)
    default_on = (m.group(1) == 'True') if m else False
    if not default_on:
        flag('HIGH', '적 스탠드오프',
             "적 수상함 스탠드오프 발사가 기본 OFF다 → 적이 자기 미사일 사거리를 버리고 "
             "아군 탐지거리까지 접근해 발사한다(052D: 사거리 540km인데 44km서 발사)")
    # 사거리를 갖고도 접근해야만 쏘는 구조가 남았는지: 사거리 대비 스폰거리 비율 점검
    for name, info in ENEMY_DB.items():
        if not info.get('can_fire_missile'):
            continue
        rng = info.get('missile_range_km') or 0
        if rng >= 300 and info.get('category') == '대함' and not default_on:
            flag('MED', '적 스탠드오프',
                 f"{name}: 사거리 {rng}km 대함미사일 보유 — 스탠드오프 OFF면 44km까지 접근")


# ── ⑤ 정찰 자산 탐지 확장 ↔ 적 발사 거리 (확장이 무의미한 규모인가) ──────
def chk_recon_vs_threat():
    max_bonus = max((a.get('recon_detect_bonus_km', 0) or 0)
                    for a in FRIENDLY_AIRCRAFT_DB.values())
    eff = _SURF_DETECT_KM_TYPICAL + max_bonus
    far = [(n, i.get('missile_range_km', 0)) for n, i in ENEMY_DB.items()
           if (i.get('missile_range_km') or 0) * 0.9 > eff and i.get('category') == '대함']
    if far:
        worst = max(far, key=lambda x: x[1])
        flag('LOW', '정찰↔적 발사거리',
             f"최대 정찰 확장 포함 탐지 {eff:.0f}km < 일부 적의 발사 거리 "
             f"(예: {worst[0]} {worst[1]*0.9:.0f}km) → 그 적은 끝까지 안 보인다")


def main():
    for fn in (chk_mach_vs_speed, chk_engage_window, chk_weapon_vs_detect,
               chk_enemy_standoff, chk_recon_vs_threat):
        try:
            fn()
        except Exception as e:
            flag('ERR', fn.__name__, f'검사 자체 실패: {type(e).__name__}: {e}')

    print('=' * 70)
    print(' DB 내부 모순 탐지 (공개 제원 없이 앞뒤가 안 맞는 값 찾기)')
    print('=' * 70)
    if not FINDINGS:
        print('✅ 모순 없음')
        return 0
    order = {'ERR': 0, 'HIGH': 1, 'MED': 2, 'LOW': 3}
    for sev, chk, msg in sorted(FINDINGS, key=lambda f: order.get(f[0], 9)):
        icon = {'HIGH': '🔴', 'MED': '🟠', 'LOW': '🟡', 'ERR': '⚠'}.get(sev, '·')
        print(f'{icon} [{sev:4s}] {chk}\n        {msg}')
    print('-' * 70)
    print(f'발견 {len(FINDINGS)}건 — 각 항목은 사람이 판정(의도된 설계일 수도 있다)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
