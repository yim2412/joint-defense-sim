#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
audit_dead_toggle.py — 죽은 토글 스캐너 (종합 감사 전용, 빌드 제외 도구)

죽은 기능 방지 체계 ④ (정본 plan_dead_feature_prevention.md · [[project-dead-feature-prevention]]).
① 커밋 게이트의 EFFECT_DEBT 유예 목록(현재 43개)을 **전수로 돌려 상환 여부를 판정**한다.
각 토글을 대표 시나리오 여러 개 × 시드 여러 개에서 ON/OFF 2회 실행해:
  · ON/OFF 결과 **델타**(어느 지표든 바뀌는가)
  · ② 발현 카운터 feature_fires **발동 횟수**(그 기능 코드 경로가 실제로 돌았는가)
를 동시에 수집한다. 이 둘의 조합이 곧 진단(계획서 핵심):

  ✅ 델타≠0            → 살아 있음 → EFFECT_DEBT에서 제거(부채 상환)
  🟠 델타0 · 발동N     → 발동했으나 결과 무영향 = 진짜 음성 후보(종결 판단)
  🔴 델타0 · 발동0     → 무대 없음/게이트 막힘 = 발현 조건부터 규명
  ⚪ 델타0 · 카운터없음 → 원인 불명 → ② 발현 카운터를 그 기능에 먼저 시딩해야 판정 가능

⚠ 필수 가드 (v18.05.08에서 실제로 당한 함정 — 정본 규칙):
  · cfg는 audit_verify_regression._BASE를 import해 쓴다(직접 조립 금지 → 적 편대 미생성 오판).
  · total_threats==0 이면 그 측정은 **무효**로 버린다(모든 지표 0을 '죽음'으로 오독 방지).
  · 시나리오를 **여러 개** 쓴다(하나만 쓰면 멀쩡한 토글이 그 무대에 안 맞아 죽은 걸로 오판).

비용: 43토글 × 4시나리오 × 2(ON/OFF) × 2시드 ≈ 700회 시뮬(수 분). **매 커밋 금지** —
종합 감사(③층)에서만. 사용: python audit_dead_toggle.py [--seeds N] [--only enable_xxx,...]
"""
import sys, time, argparse
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

from engine_combat import run_v7_simulation
from audit_verify_regression import _BASE
from audit_static_scan import EFFECT_DEBT

# ② 발현 카운터가 시딩된 토글 → feature_fires 키 매핑(enable_ 접두 제거 규칙과 일치).
# 여기 없는 토글은 '카운터 미시딩'으로 분류(델타0이면 ⚪ = 카운터 추가 대상).
_SEEDED = {'enable_radar_off', 'enable_sonar_emcon', 'enable_laser_dew'}

# 대표 시나리오 4종 — total_threats>0 이 보장되는 프리셋만(가드). 도메인을 서로 다르게 골라
# '시나리오 복수' 가드를 충족(한 무대에만 맞는 토글이 다른 무대에서 죽은 걸로 오판되는 것 방지).
# 대잠은 짝 기능(함재 헬기·초계기)을 켜야 sonar_emcon류가 발현하는 무대가 된다.
# 지상 BMD 5자산 발현 짝 = 토글 + **재고(stock)**. ⚠ enable_xxx 토글만으론 발사 안 함 —
# ground_inv가 cfg의 *_stock으로 채워지고(engine_combat 1677), 발사 조건이 재고>0을 본다.
# app_main UI는 체크박스 ON 시 재고를 자동 부여(10029~10039). 스캐너도 같은 경로를 재현해야
# 발현한다(안 그러면 토글만 켜고 재고 0 → 발사 0 → 델타0을 '죽음'으로 오판, v18.05.08 유형).
_BMD_GROUND = dict(
    enable_ashore=True,  enable_thaad=True, enable_lsam=True,
    enable_chungung=True, enable_patriot=True,
    ashore_sm3_stock=24, thaad_stock=24, lsam_stock=16, chungung_stock=32, patriot_stock=16,
)

SCENARIOS = [
    ('대공포화', dict(_BASE, fleet_preset='이지스 기동전단', enemy_fleet_preset='입체 포화 (최강)')),
    ('수상함',   dict(_BASE, fleet_preset='이지스 기동전단', enemy_fleet_preset='수상함 편대전')),
    ('SEAD',     dict(_BASE, fleet_preset='이지스 기동전단', enemy_fleet_preset='전자전 SEAD 제압')),
    ('대잠',     dict(_BASE, fleet_preset='대잠전단',        enemy_fleet_preset='잠수함 복합 포화',
                      enable_helo=True, enable_p8a=True, enable_p3c=True)),
    # BMD 5계층·탄도 종말강하·HGV 활공은 탄도 표적이 있어야 발현 — 지상 BMD 자산+재고를 켠다.
    ('BMD탄도',  dict(_BASE, fleet_preset='이지스 기동전단', enemy_fleet_preset='BMD 탄도 포화',
                      **_BMD_GROUND)),
    # ── 부채17 청소 A+B(2026-07-15) 발현 무대 추가 ────────────────────────────
    # A. BMD 하위계층은 20발 BMD탄도에선 상위층(SM-3·THAAD)이 흡수해 안 내려옴 → 40발 대량
    #    포화라야 patriot/lsam/chungung까지 샌다(v18.04.07서 확인). ballistic_descent·isa 발현 무대.
    ('대량탄도', dict(_BASE, fleet_preset='이지스 기동전단', enemy_fleet_preset='북한 포화 공격 (40발)',
                      **_BMD_GROUND)),
    # A. hgv_glide는 극초음속 활공체(DF-17·YJ-21)가 있어야 단계별 고도강하 발현.
    ('극초음속', dict(_BASE, fleet_preset='이지스 기동전단', enemy_fleet_preset='극초음속 포화 공격',
                      **_BMD_GROUND)),
    # B. terrain(지형 레이더 음영)은 저고도 위협(alt<1000m)이라야 탐지거리 페널티가 결과에 드러남.
    #    _BASE fleet_region='동해 북부'=EAST_SEA(페널티 0.78 최강). 연안 자폭드론·로켓·고속정 다수.
    ('연안저고도', dict(_BASE, fleet_preset='이지스 기동전단', enemy_fleet_preset='연안 포화 공격')),
]

# ON/OFF 델타를 관찰할 지표(광범위 — 어느 하나라도 움직이면 '살아 있음'). 다양한 도메인 커버.
METRICS = [
    'intercept_rate', 'friendly_hits', 'enemy_hits', 'friendly_ships_lost',
    'enemy_ships_destroyed', 'total_missiles_fired', 'total_cost',
    'mines_struck', 'ships_lost_to_mine', 'recon_losses', 'unmanned_lost',
    'laser_kills', 'ashore_sm3_fired', 'thaad_fired', 'lsam_fired',
    'chungung_fired', 'patriot_fired', 'iff_failures', 'iff_fratricide',
    'ras_missiles_resupplied',
]
_EPS = 1e-6

# 단발 교전으로는 원리상 발현 못 하는 토글(전장·캠페인 전용) — 델타0이어도 '무대없음'이 정상.
# 스캐너가 이들을 🔴로 몰아세우지 않도록 별도 표시(오판 방지). 진짜 판정은 전장 스모크에서.
_BATTLE_ONLY = {'enable_ras_rearm', 'enable_munition_limit', 'enable_battle_mode'}


def _run(cfg):
    return run_v7_simulation(dict(cfg))


def _delta(off, on):
    """관찰 지표 중 절대 델타가 임계를 넘는 것들의 {지표: 델타}. 비면 결과 무변."""
    d = {}
    for m in METRICS:
        v = (on.get(m, 0) or 0) - (off.get(m, 0) or 0)
        if abs(v) > _EPS:
            d[m] = v
    return d


def scan(toggles, seeds):
    rows = []   # (toggle, verdict, delta_info, fired, note)
    for flag in toggles:
        seeded = flag in _SEEDED
        short  = flag[len('enable_'):]
        any_delta, best_delta, fired_sum, valid_runs = {}, 0.0, 0, 0
        for scen_name, scen_cfg in SCENARIOS:
            for sd in seeds:
                cfg = dict(scen_cfg, sim_seed=sd)
                off = _run(dict(cfg, **{flag: False}))
                on  = _run(dict(cfg, **{flag: True}))
                # 가드: 적 편대 미생성이면 측정 무효(모든 지표 0을 죽음으로 오독 방지)
                if (on.get('total_threats', 0) or 0) == 0 or (off.get('total_threats', 0) or 0) == 0:
                    continue
                valid_runs += 1
                d = _delta(off, on)
                mag = sum(abs(v) for v in d.values())
                if mag > best_delta:
                    best_delta, any_delta = mag, {'scen': scen_name, 'seed': sd, **d}
                if seeded:
                    fired_sum += on.get('feature_fires', {}).get(short, 0)
        # ── 판정 ──────────────────────────────────────────────────────────
        if valid_runs == 0:
            verdict, note = '무효', '모든 조합에서 total_threats==0 (측정 실패 — 시나리오 부적합)'
        elif any_delta:
            verdict = '살아있음'
            note = f"[{any_delta['scen']}/seed{any_delta['seed']}] 최대델타 {best_delta:.4g} · " + \
                   ' '.join(f"{k}{v:+.3g}" for k, v in any_delta.items() if k not in ('scen', 'seed'))
        elif seeded and fired_sum > 0:
            verdict, note = '진짜음성후보', f'발동 {fired_sum}회했으나 어느 지표도 무변 → 종결 판단 대상'
        elif seeded:
            verdict, note = '무대없음', '발동 0회 + 델타 0 → 발현 조건(짝 기능·거리·편성)부터 규명'
        elif flag in _BATTLE_ONLY:
            verdict, note = '전장전용', '단발서 델타0은 정상 — 전장 스모크에서 판정(단발 스캐너 대상 밖)'
        else:
            verdict, note = '카운터필요', '델타0이나 ② 발현 카운터 미시딩 → 원인불명, 카운터 먼저 심어야 판정'
        rows.append((flag, verdict, fired_sum if seeded else None, valid_runs, note))
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=2, help='토글·시나리오당 시드 수(기본 2)')
    ap.add_argument('--only', type=str, default='', help='쉼표구분 특정 토글만')
    args = ap.parse_args()

    seeds = list(range(3, 3 + args.seeds))
    toggles = sorted(EFFECT_DEBT)
    if args.only:
        want = set(args.only.split(','))
        toggles = [t for t in toggles if t in want]

    n_sim = len(toggles) * len(SCENARIOS) * len(seeds) * 2
    print(f"죽은 토글 스캐너 — EFFECT_DEBT {len(toggles)}개 × 시나리오 {len(SCENARIOS)} × "
          f"시드 {len(seeds)} × ON/OFF = 약 {n_sim}회 시뮬")
    t0 = time.time()
    rows = scan(toggles, seeds)
    el = time.time() - t0

    # 분류별 집계
    order = ['살아있음', '진짜음성후보', '무대없음', '카운터필요', '전장전용', '무효']
    icon  = {'살아있음': '✅', '진짜음성후보': '🟠', '무대없음': '🔴',
             '카운터필요': '⚪', '전장전용': '⬛', '무효': '❓'}
    print("=" * 78)
    for flag, verdict, fired, valid, note in sorted(rows, key=lambda r: order.index(r[1])):
        f = f" 발동{fired}" if fired is not None else ""
        print(f"{icon[verdict]} {verdict:8} {flag:28}{f}  ({note})")
    print("-" * 78)
    from collections import Counter
    tally = Counter(r[1] for r in rows)
    summary = ' · '.join(f"{icon[k]}{k} {tally[k]}" for k in order if tally[k])
    print(f"집계: {summary}")
    alive = [r[0] for r in rows if r[1] == '살아있음']
    if alive:
        print(f"\n💰 부채 상환 대상(살아있음 {len(alive)}개) — audit_static_scan.EFFECT_DEBT에서 제거 검토:")
        print("   " + ', '.join(alive))
    print(f"\n소요 {el:.0f}초. (판정은 사람이 검토 — 🔴/🟠/⚪는 발현 조건·카운터 시딩 후 재확인)")


if __name__ == '__main__':
    main()
