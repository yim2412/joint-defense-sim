#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
audit_effect.py — 토글 효과 검증 (죽은 토글 탐지, 빌드 제외 도구)

BLIND_SPOTS: "토글이 복원되는가"는 정적 감사가 보나 "실제로 결과를 바꾸는가"는 못 봤다.
이 스크립트는 **각 토글을 그 토글이 효과를 내야 하는 시나리오에서** 고정 시드로 ON/OFF
2회 실행해, 어떤 결과 지표도 안 바뀌면 '죽은 토글(코드 경로 미도달·회귀)'로 경고한다.

핵심: 시나리오 의존성 오경보를 피하려고 **토글마다 효과가 입증된 시나리오를 명시**한다
(baselines·쇼케이스 카드 근거). 그 시나리오에서조차 효과 0이면 진짜 회귀다.
지표는 여기 나열한 것 중 하나라도 델타가 임계 이상이면 '효과 있음'.

사용:  python audit_effect.py     # 죽은 토글 있으면 exit 1
한계:  여기 등재 안 된 토글(효과 시나리오 불명확)은 수동 검증 대상 — 목록 하단 출력.
"""
import sys
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass
from engine_combat import run_v7_simulation

# 토글 → (효과 입증 시나리오 cfg, 관찰 지표들). baselines/쇼케이스 근거.
_BASE = dict(enemy_fleet_mode='preset', weather='흐림', sim_seed=7)
PROBES = {
    # ⚠ 적 편대는 드론이 **없는** 것을 쓴다. 종전엔 '무인기 군집 포화'(이미 자폭 드론 48대를
    # 포함)를 썼는데, 이 토글은 편대 말미에 드론을 **추가로** 얹으므로 ON/OFF가 '48대 vs
    # 96대'였다 — 이미 포화된 상태의 미세 델타라, 아군 생존이 조금만 좋아져도(v20.5 회피 기동
    # 기본 ON) 델타가 0으로 무너져 멀쩡한 토글이 '죽은 토글'로 오판됐다. 드론 없는 편대에서
    # '0대 vs 48대'를 재야 이 토글이 실제로 군집을 만드는지 검사할 수 있다.
    'enable_drone_swarm': (
        dict(_BASE, fleet_preset='이지스 기동전단', enemy_fleet_preset='수상함 편대전',
             drone_swarm_size=48),
        ['intercept_rate', 'friendly_hits']),
    'enable_dmo': (
        dict(_BASE, fleet_preset='이지스 기동전단', enemy_fleet_preset='입체 포화 (최강)'),
        ['intercept_rate', 'friendly_hits']),
    'enable_coord_deception': (
        dict(_BASE, fleet_preset='이지스 기동전단', enemy_fleet_preset='수상함 편대전'),
        ['friendly_hits', 'intercept_rate']),
    'enable_png': (
        dict(_BASE, fleet_preset='이지스 기동전단', enemy_fleet_preset='북한 포화 공격 (40발)'),
        ['intercept_rate']),
    'enable_mine_threat': (
        dict(_BASE, fleet_preset='이지스 기동전단', enemy_fleet_preset='항만 침투 복합',
             enable_mine_threat=True, mine_density=0.5),
        ['mines_struck', 'ships_lost_to_mine', 'friendly_ships_lost']),
    'enable_unmanned_assets': (
        # UUV 소해 효과는 기뢰가 있어야 발현 — enable_mine_threat 커플링 필수
        dict(_BASE, fleet_preset='이지스 기동전단', enemy_fleet_preset='항만 침투 복합',
             enable_mine_threat=True, mine_density=0.6),
        ['friendly_ships_lost', 'unmanned_lost', 'mines_struck']),
    'enable_cyber_warfare': (
        dict(_BASE, fleet_preset='이지스 기동전단', enemy_fleet_preset='전면전 포화'),
        ['intercept_rate', 'friendly_hits']),
}


def _run(cfg):
    return run_v7_simulation(dict(cfg))


def main():
    dead, ok = [], []
    for flag, (cfg, metrics) in PROBES.items():
        off = _run(dict(cfg, **{flag: False}))
        on = _run(dict(cfg, **{flag: True}))
        deltas = {m: (on.get(m, 0) or 0) - (off.get(m, 0) or 0) for m in metrics}
        changed = any(abs(d) > 1e-9 for d in deltas.values())
        if changed:
            ok.append((flag, deltas))
        else:
            dead.append((flag, cfg.get('enemy_fleet_preset')))

    print("토글 효과 검증 (효과 입증 시나리오에서 ON/OFF 델타)")
    for flag, deltas in ok:
        ds = ' '.join(f"{m}{v:+.3g}" for m, v in deltas.items() if abs(v) > 1e-9)
        print(f"  ✅ {flag:26} 효과 있음 — {ds}")
    for flag, scen in dead:
        print(f"  ❌ {flag:26} 효과 0 (시나리오 '{scen}') — 죽은 토글/회귀 의심")

    # 등재 안 된 실험적 토글(효과 시나리오 불명확 → 수동 검증) 안내
    # 효과가 전장 모드·장기전에서만(단발 40틱 미발현) 또는 엣지케이스라 단발 probe 부적합
    manual = ['enable_munition_limit(전장전용)', 'enable_ras_rearm(전장전용)',
              'enable_esm_arm', 'enable_sonar_emcon', 'enable_hgv_glide', 'enable_iff',
              'enable_laser_dew', 'enable_recon_drone', 'enable_autonomous_engagement',
              'enable_asw_forward']
    print(f"  ⓘ 수동 검증 대상(효과 엣지케이스·시나리오 의존, BLIND_SPOTS): {', '.join(manual)}")

    if dead:
        print(f"\n❌ 죽은 토글 {len(dead)}개 — 코드 경로 미도달 or 회귀")
        sys.exit(1)
    print(f"\n✅ 등재 토글 {len(ok)}개 전부 효과 확인")


if __name__ == '__main__':
    main()
