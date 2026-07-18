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


# ── 작전급 캠페인 전용 토글 (v21.2 신설) ─────────────────────────────────────
# 캠페인 층(engine_campaign·airforce·army·joint) 토글은 **단발 전술 프로브로 못 잡는다**
# — run_v7_simulation이 아니라 run_campaign을 타기 때문. 부채 청소 E에서 battle_mode·
# ras_rearm이 겪은 것과 같은 상황이다.
#
# ⚠ 게이트 사각: audit_static_scan.chk_effect_coverage는 engine_combat.py가 소비하는
#    플래그만 검사한다 → 캠페인 층 토글은 **자동 면제**돼 죽은 채 태어날 수 있다.
#    그래서 여기에 캠페인 프로브를 둬 수동 측정이 아니라 **도구로 재현**되게 한다.
_CAMPAIGN_BASE = dict(
    enable_campaign_mode=True, campaign_horizon_h=72, campaign_seed=0,
    enemy_fleet_mode='preset',
    enemy_fleet_preset='입체 포화 (최강)',   # ⚠ 키 오타 시 웨이브 0 = 측정 무효(v16.12.03)
)
CAMPAIGN_PROBES = {
    # 합동 화력 — 육해공이 같은 적 기지를 협조 타격.
    #  ▸짝 기능(필수): enable_strategic_strike(표적인 적 기지가 생긴다) +
    #    enable_air_campaign(기지 손상 → 적 출항능력 환산 통로). 하나만 빠져도 층 미생성.
    #  ▸발현 무대: 한미 기동전단 강화(현무-3C 48 + 토마호크 32 = 지상공격 80발) +
    #    최소 방공(전략폭격기 없음) → 폭격기 없이 해군·육군 화력만으로 적 항구 무력화.
    #    이 무대에서 OFF는 적 기지를 때릴 수단이 아예 없어 출항능력 1.0(무손상)이다.
    'enable_joint_fires': (
        dict(_CAMPAIGN_BASE, fleet_preset='한미 기동전단 강화',
             air_force_preset='최소 방공 (제공권 열세)',
             army_fire_preset='현무 여단 (증강)',
             enable_air_campaign=True, enable_strategic_strike=True,
             enable_army_campaign=True),
        ['enemy_output_factor', 'mean_control']),

    # 게이트 캠페인 확장(2026-07-19) — 나머지 9개 캠페인 토글. chk_effect_coverage를
    # engine_campaign·airforce·army·joint까지 보게 넓히면서, 그 4파일이 소비하는
    # enable_* 11개 중 이미 커버된 2개(enable_joint_fires 위, enable_ballistic_descent는
    # EFFECT_ALIVE)를 뺀 9개 전부에 프로브를 채웠다.

    # 지상 작전급 층 자체 — OFF면 self.army가 아예 None(어떤 지상 하위 지표도 안 생김).
    # 짝 기능: enable_coastal_sam을 켜둬야 층이 생겼을 때 실제로 뭔가(포대) 생긴다 —
    # 안 그러면 army는 있어도 sites={}라 "층 존재"와 "coastal_sam 존재"가 안 갈린다.
    'enable_army_campaign': (
        dict(_CAMPAIGN_BASE, fleet_preset='이지스 기동전단', enable_coastal_sam=True),
        ['_n_coastal_sites']),

    # 연안 방공 포대 — army 층은 있어도(enable_army_campaign) OFF면 self.sites={}.
    'enable_coastal_sam': (
        dict(_CAMPAIGN_BASE, fleet_preset='이지스 기동전단', enable_army_campaign=True),
        ['_n_coastal_sites']),

    # 상륙작전 — OFF면 self.landing=None → amphib_* 키 자체가 결과에 없음(=0 취급).
    'enable_amphibious': (
        dict(_CAMPAIGN_BASE, fleet_preset='독도함 상륙전단', enable_army_campaign=True),
        ['amphib_progress']),

    # 적 SEAD 도미노(연안 SAM 제압) — ①enable_army_campaign+enable_coastal_sam(제압 대상인
    # 포대가 있어야) ②enable_air_campaign(제공권 개념 자체가 없으면 무동작, engine_army.py
    # _tick_enemy_sead 주석 "공군 작전급과 함께 켜야 의미가 있다") ③아군 제공권 열세 무대
    # (최소 방공)라야 적 제공권이 높아 제압이 실제로 쌓인다.
    'enable_enemy_sead': (
        dict(_CAMPAIGN_BASE, fleet_preset='이지스 기동전단',
             enable_army_campaign=True, enable_coastal_sam=True,
             enable_air_campaign=True, air_force_preset='최소 방공 (제공권 열세)'),
        ['coastal_suppression']),

    # 공군 작전급 층 자체 — OFF면 self.air가 None → 제공권 지표 전부 결과에서 사라진다.
    'enable_air_campaign': (
        dict(_CAMPAIGN_BASE, fleet_preset='한미 기동전단 강화',
             air_force_preset='한미 연합 공군 패키지'),
        ['mean_air_superiority']),

    # SEAD/DEAD(적 방공망 제압) — enable_air_campaign이 먼저 있어야 self.sead_enabled가
    # 뜻을 갖는다(공군 층 자체가 없으면 검사 대상이 없음).
    'enable_sead': (
        dict(_CAMPAIGN_BASE, fleet_preset='한미 기동전단 강화',
             air_force_preset='한미 연합 공군 패키지', enable_air_campaign=True),
        ['n_ad_sites']),

    # 전략폭격(적 기지 타격) — enable_air_campaign 선행 필요(폭격기가 날 공군 층 자체).
    'enable_strategic_strike': (
        dict(_CAMPAIGN_BASE, fleet_preset='한미 기동전단 강화',
             air_force_preset='한미 연합 공군 패키지', enable_air_campaign=True),
        ['n_enemy_bases']),

    # A1 정밀 교전 — zone 대리모델 대신 실제 전술 단발로 해결한 교전 수(n_precise).
    'enable_precise_engagement': (
        dict(_CAMPAIGN_BASE, fleet_preset='이지스 기동전단'),
        ['n_precise']),
}

# ⚠ enable_campaign_fog는 여기 없다 — 단일 프로브로 재현 시도했으나 재현 실패:
#   소함대(1~2척)는 belief 갱신 전에 자원소진(_all_ships_down)으로 조기 종료돼 안개
#   효과(zone 미탐지 누적)가 발현할 시간이 안 나오고, 전 구역을 커버하는 함대(3척+,
#   교통로 3개에 순환분산)는 애초에 안 놓치는 zone이 없어 fog ON/OFF가 bit-identical.
#   진짜 효과 무대(대형 함대·장기 horizon·부분 커버)를 못 찾음 — 수동 검증 대상으로 이관.


def _run(cfg):
    return run_v7_simulation(dict(cfg))


def _run_campaign(cfg):
    from engine_campaign import run_campaign
    r = run_campaign(dict(cfg))
    # 파생 지표 — dict형 결과(coastal_sites 등)는 delta 계산이 안 되므로 카운트로 환산.
    r['_n_coastal_sites'] = len(r.get('coastal_sites') or {})
    return r


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

    for flag, (cfg, metrics) in CAMPAIGN_PROBES.items():
        off = _run_campaign(dict(cfg, **{flag: False}))
        on = _run_campaign(dict(cfg, **{flag: True}))
        # ⚠ 측정 유효성 자가검사(v18.05.09): "모든 지표 0"은 결론이 아니라 측정 실패 신호.
        #    프리셋 키가 한 글자만 틀려도 적 웨이브가 0개라 교전이 안 일어난다.
        if not off.get('n_ships') or not off.get('n_engagements'):
            print(f"  ★★ {flag}: 측정 무효 — 무대 미생성"
                  f"(함정={off.get('n_ships')} 교전={off.get('n_engagements')})")
            sys.exit(1)
        deltas = {m: (on.get(m, 0) or 0) - (off.get(m, 0) or 0) for m in metrics}
        if any(abs(d) > 1e-9 for d in deltas.values()):
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
              'enable_asw_forward',
              'enable_campaign_fog(캠페인 전용 — 효과 무대 재현 실패, 위 주석 참조)']
    print(f"  ⓘ 수동 검증 대상(효과 엣지케이스·시나리오 의존, BLIND_SPOTS): {', '.join(manual)}")

    if dead:
        print(f"\n❌ 죽은 토글 {len(dead)}개 — 코드 경로 미도달 or 회귀")
        sys.exit(1)
    print(f"\n✅ 등재 토글 {len(ok)}개 전부 효과 확인")


if __name__ == '__main__':
    main()
