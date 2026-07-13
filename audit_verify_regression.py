#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
회귀 검증 스크립트 — 엔진 동작이 의도치 않게 바뀌었는지 자동 점검.

고정 시나리오 × 고정 seed의 결과를 골든값(audit_regression_golden.json)과 대조한다.
같은 seed면 엔진은 결정론적이므로, 결과가 한 지표라도 다르면 동작이 바뀐 것.

사용법:
    python audit_verify_regression.py            # 골든값과 비교 (PASS/FAIL)
    python audit_verify_regression.py --update   # 현재 결과를 새 골든값으로 저장 (의도된 변경 후)

언제 쓰나 (CLAUDE.md 감사 정책):
    engine_core.py / engine_combat.py 의 교전·물리·로직 변경 시 빌드·커밋 전에 실행.
    - PASS  → 동작 보존됨, 안전.
    - FAIL  → 의도한 변경이면 --update로 골든 갱신, 아니면 버그(원인 추적).

주의: 결정론 의존(random/numpy seed 고정). 신규 random 호출 추가·순서 변경은
      정상 변경이어도 FAIL이 날 수 있다 → 의도 확인 후 --update.
주의: --smoke는 엔진 직접 호출이므로 GUI 워커 경로(시그널 emit 등)를 검증하지 않는다.
      GUI 경로 확인은 exe에서 테스트 모드 체크박스를 켜고 직접 실행해야 한다.
"""
import sys
import io
import json
import os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from engine_combat import run_v7_simulation  # noqa: E402

GOLDEN_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           'audit_regression_golden.json')

# 모든 신모델 ON + 날짜 의존(해류) 제외 → 결정론 보장
_BASE = dict(
    fleet_region='동해 북부', season='summer', weather='맑음 (주간)',
    enable_ecm=True, enable_evasion=True, enable_decoy=True, enable_selfdefense=True,
    enable_layered_defense=True, enable_cec=True, enable_radar_off=True,
    enable_png=True, enable_sonar_equation=True, enable_flooding=True,
    enable_terrain=True, enable_evap_duct=True, enable_isa=True,
    enable_weather_dynamics=False, enable_iff=False,
    enable_current=False,   # datetime.today 의존 제거 (결정론)
    enemy_fleet_mode='preset',
    n_threads=4, cd_time_s=10, confirm_time_s=3,
)

# 다양한 교전 경로를 자극: 항공기 이탈/재공격·적함 SAM·항모 파도·CAP 격추·자폭·잠수함
CASES = [
    ('랴오닝-기본',     dict(_BASE, fleet_preset='기동전단 기본',   enemy_fleet_preset='랴오닝 항모전단'),   [1, 2, 3]),
    ('입체포화-이지스', dict(_BASE, fleet_preset='이지스 기동전단', enemy_fleet_preset='입체 포화 (최강)'),  [1, 2]),
    ('공격+CAP',        dict(_BASE, fleet_preset='기동전단 기본',   enemy_fleet_preset='랴오닝 항모전단',
                             enable_strike=True, haesong2_stock=16, harpoon_stock=8,
                             enable_kf21=True, enable_helo=True),                                            [7]),
    ('잠수함복합',      dict(_BASE, fleet_preset='대잠전단',        enemy_fleet_preset='잠수함 복합 포화'),  [4, 5]),
    # CAP(KF-21)+잠수함 동시 편성 — CAP기가 ASW 순회에 잘못 들어가 공대공 무장을 어뢰로
    # 조회하던 KeyError 크래시(v18.01.16)를 회귀가 앞으로 자동 차단하도록 커버(크래시 재현 시드).
    ('3축+CAP잠수함',   dict(_BASE, fleet_preset='이지스 기동전단', enemy_fleet_preset='중국 3축 동시 공격',
                             enable_kf21=True, enable_helo=True),                                         [2, 5]),
    # v18.01.18: CAP 공대공 상시초계(60s) 정상화로 aircraft_sorties 발현 — 죽어있던
    # 공대공 격추 경로를 골든에 봉인(sorties>0·적기 격추 반영). 랴오닝 항모전단 vs
    # 이지스 기동전단 + F-35A/KF-21/FA-50 3기종에서 항공 요격이 확실히 발현하는 시드.
    ('CAP상시초계',     dict(_BASE, fleet_preset='이지스 기동전단', enemy_fleet_preset='랴오닝 항모전단',
                             enable_f35a=True, enable_kf21=True, enable_fa50=True, enable_helo=True),     [2, 3]),
    # v20.2a: 지상 BMD 4계층(SM-3·THAAD·L-SAM·천궁-II) + 탄도 종말 강하. 강하 모델이 없으면
    # 탄도가 고도 1200km를 유지해 종말 계층이 영구 미발현하므로 두 기능을 함께 봉인한다.
    # 북한 포화(40발)는 4계층이 모두 발사되는 시드 — 계층별 발사수가 골든에 박혀
    # 요격 고도창·사거리·사격통제 상한이 조용히 바뀌면 회귀가 잡는다.
    ('BMD4계층-강하',   dict(_BASE, fleet_preset='이지스 기동전단',
                             enemy_fleet_preset='북한 포화 공격 (40발)',
                             enable_ballistic_descent=True, enable_hgv_glide=True,
                             enable_ashore=True, ashore_sm3_stock=24,
                             enable_thaad=True,  thaad_stock=24,
                             enable_lsam=True,   lsam_stock=16,
                             enable_chungung=True, chungung_stock=32),                                  [3, 15]),
]

# 결정론적이고 의미 있는 지표만 비교 (시각화·로그 등 비결정 요소 제외)
_KEYS = ['total_threats', 'intercepted_threats', 'friendly_hits', 'enemy_hits',
         'friendly_ships_lost', 'enemy_ships_destroyed', 'total_cost', 'aircraft_sorties',
         'peak_concurrent_threats', 't_first_fire', 'total_missiles_fired',
         'kor_shots', 'usa_shots', 'kor_cost', 'usa_cost',
         'ashore_sm3_fired', 'thaad_fired', 'lsam_fired', 'chungung_fired',
         'iff_failures', 'iff_fratricide',
         'ships_sunk_by_flood', 'intercept_rate', 'sim_time', 'total_channels']

# 캠페인 정밀 교전(enable_precise_engagement) 회귀 — 전술 골든(위 CASES)은 정밀 OFF
# 대리모델 경로만 보증하므로, 캠페인 zone 교전을 실제 전술 단발로 해결하는 _resolve_precise
# 경로가 무감시였다(사각). 정밀 ON 캠페인은 결정론적(같은 campaign_seed→동일)이라 고정 seed
# 스냅샷으로 골든에 봉인 → 향후 정밀 교전 로직이 조용히 바뀌면 회귀가 잡는다.
_CAMPAIGN_BASE = dict(weather='맑음 (주간)', enable_campaign_mode=True,
                      enable_precise_engagement=True, campaign_horizon_h=72)
CAMPAIGN_CASES = [
    ('정밀ON-항모킬체인', dict(_CAMPAIGN_BASE, fleet_preset='이지스 기동전단',
                              enemy_fleet_preset='항모 킬 체인'), [1, 2]),
    # v20.2b: 지상 층(연안 방공망). ASBM(DF-21D) 구역은 규모와 무관하게 전술 정밀로 강제되고
    # 연안 포대 4계층 자산이 tcfg에 주입돼 실측 요격 → 재고가 틱 간 차감된다. 이 케이스가
    # 라우팅 트리거·자산 주입·재고 차감을 한꺼번에 봉인한다(기동전단 기본 = 포대 유무가
    # 전멸↔완승을 가르는 편성 — 연안 방공 효과가 binding인 시드).
    ('연안방공-ASBM', dict(weather='맑음 (주간)', enable_campaign_mode=True,
                           campaign_horizon_h=72,
                           fleet_preset='기동전단 기본', enemy_fleet_preset='항모 킬 체인',
                           enable_army_campaign=True, enable_coastal_sam=True,
                           coastal_sam_preset='한국형 BMD (KAMD)'), [3, 11]),
    # 위 캠페인 케이스가 전부 win이라 패배 경로(전멸·통제 붕괴)가 골든에 없었다(정적 스캔
    # chk_golden_coverage가 'outcome 전 케이스 동일값'으로 검출). 연안 포대가 있어도 위협이
    # 압도해 무너지는 케이스를 넣어 loss 분기까지 봉인한다.
    ('연안방공-포화패배', dict(weather='맑음 (주간)', enable_campaign_mode=True,
                              campaign_horizon_h=72,
                              fleet_preset='기동전단 기본', enemy_fleet_preset='전면전 포화',
                              enable_army_campaign=True, enable_coastal_sam=True,
                              coastal_sam_preset='한국형 BMD (KAMD)'), [3]),
    # 순수 대리모델 캠페인(정밀 0회) — 골든의 캠페인 케이스가 전부 정밀 3회라 대리모델
    # 교전 경로(_apply_engagement·추상 피해)가 무감시였다. n_precise=0 분기를 봉인한다.
    ('캠페인-대리모델', dict(weather='맑음 (주간)', enable_campaign_mode=True,
                            campaign_horizon_h=72,
                            fleet_preset='이지스 기동전단',
                            enemy_fleet_preset='랴오닝 항모전단'), [5]),
    # v20.3: 상륙작전 — 3단계 곱연산(수송·엄호·상륙)이 교두보 확보로 이어지는 성공 경로를
    # 봉인. 공군 ON(제공권=엄호 단계)이라야 교두보에 도달하므로 함께 켠다.
    ('상륙-교두보확보', dict(weather='맑음 (주간)', enable_campaign_mode=True,
                            campaign_horizon_h=72,
                            fleet_preset='이지스 기동전단',
                            enemy_fleet_preset='랴오닝 항모전단',
                            enable_army_campaign=True, enable_air_campaign=True,
                            enable_amphibious=True, amphib_zone='서해'), [3]),
    # 상륙 실패 경로(교통로 차단 → 수송 단계 붕괴)도 봉인 — 성공만 있으면 게이팅이 조용히
    # 풀려도 회귀가 못 잡는다.
    ('상륙-교통로차단', dict(weather='맑음 (주간)', enable_campaign_mode=True,
                            campaign_horizon_h=72,
                            fleet_preset='기동전단 기본',
                            enemy_fleet_preset='전면전 포화',
                            enable_army_campaign=True, enable_air_campaign=True,
                            enable_amphibious=True, amphib_zone='서해'), [3]),
    # v20.4 도미노 — 제공권 열세(최소 방공)에서 적 SEAD가 연안 방공망을 제압 상한(0.85)까지
    # 밀어붙여 방공 기여가 무너지는 연쇄를 봉인. 제압/복구 균형이 조용히 바뀌면 회귀가 잡는다.
    ('도미노-제공권열세', dict(weather='맑음 (주간)', enable_campaign_mode=True,
                              campaign_horizon_h=72,
                              fleet_preset='기동전단 기본', enemy_fleet_preset='전면전 포화',
                              enable_army_campaign=True, enable_coastal_sam=True,
                              coastal_sam_preset='연안 방공 강화',
                              enable_air_campaign=True, enable_enemy_sead=True,
                              air_force_preset='최소 방공 (제공권 열세)'), [3]),
    # 대조군: 같은 도미노 ON인데 제공권 우세(한미 연합)면 방공망이 버틴다(제압 ≈ 0).
    ('도미노-제공권우세', dict(weather='맑음 (주간)', enable_campaign_mode=True,
                              campaign_horizon_h=72,
                              fleet_preset='기동전단 기본', enemy_fleet_preset='전면전 포화',
                              enable_army_campaign=True, enable_coastal_sam=True,
                              coastal_sam_preset='연안 방공 강화',
                              enable_air_campaign=True, enable_enemy_sead=True), [3]),
]
# 캠페인 결정론 지표 (float은 스냅샷·검사 양쪽 동일 라운딩이라 정확 일치)
# mean_control 등은 소수3자리로 봉인 — 1자리면 4%p대 통제도 변화가 골든을 통과해 민감도 저하.
_CKEYS = ['outcome', 'n_precise', 'n_engagements', 'surviving_ships',
          'cost_total', 'mean_control', 'n_reassign', 'end_h',
          # v20.2b: 연안 방공 — ASBM 정밀 강제 횟수·포대가 실제로 쏜 요격탄 수(재고 차감)
          'n_asbm_precise', 'coastal_intercepts',
          # v20.3: 상륙 — 최종 상태·교두보 진척(3단계 곱연산 결과)
          'amphib_state', 'amphib_progress', 'amphib_success',
          # v20.4: 도미노 — 연안 방공망 제압도(적 SEAD)
          'coastal_suppression']
_CROUND = 3   # 캠페인 float 지표 라운딩 자리수(회귀 민감도)


def snapshot() -> dict:
    """전 케이스를 돌려 결과 지표를 dict로 반환 (전술 CASES + 캠페인 정밀 CAMPAIGN_CASES)."""
    out = {}
    for cname, cfg, seeds in CASES:
        for s in seeds:
            r = run_v7_simulation(dict(cfg, sim_seed=s))
            rec = {k: r.get(k) for k in _KEYS}
            rec['n_alive_ships'] = sum(1 for sh in r.get('friendly_ships', []) if sh.alive)
            rec['n_alive_threats'] = sum(1 for et in r.get('enemy_ships', []) if et.alive)
            rec['n_threats_total'] = len(r.get('enemy_ships', []))
            out[f'{cname}#{s}'] = rec
    # 캠페인 정밀 교전 케이스 (모델 1회 로드 공유)
    from engine_campaign import run_campaign, load_forecast_model
    _cmodel = load_forecast_model()
    for cname, cfg, seeds in CAMPAIGN_CASES:
        for s in seeds:
            r = run_campaign(dict(cfg, campaign_seed=s), model=_cmodel)
            rec = {}
            for k in _CKEYS:
                v = r.get(k)
                rec[k] = round(v, _CROUND) if isinstance(v, float) else v
            out[f'{cname}#{s}'] = rec
    return out


def do_update():
    snap = snapshot()
    with open(GOLDEN_PATH, 'w', encoding='utf-8') as f:
        json.dump(snap, f, ensure_ascii=False, indent=2)
    print(f'✅ 골든값 갱신: {len(snap)}개 케이스 → audit_regression_golden.json')
    for k, v in snap.items():
        if 'intercepted_threats' in v:   # 전술 케이스
            print(f'  {k}: 요격={v["intercepted_threats"]}/{v["total_threats"]}, '
                  f'아군손실={v["friendly_ships_lost"]}, 비용=${v["total_cost"]/1e6:.2f}M')
        else:                             # 캠페인 정밀 케이스(_CKEYS)
            print(f'  {k}: outcome={v.get("outcome")}, n_precise={v.get("n_precise")}, '
                  f'생존={v.get("surviving_ships")}, 비용=${v.get("cost_total",0)/1e6:.2f}M')


def do_check() -> int:
    if not os.path.exists(GOLDEN_PATH):
        print('❌ audit_regression_golden.json 없음 — 먼저 `python audit_verify_regression.py --update` 실행')
        return 2
    with open(GOLDEN_PATH, encoding='utf-8') as f:
        golden = json.load(f)
    snap = snapshot()
    diffs = 0
    for key in golden:
        if key not in snap:
            print(f'  [누락] 케이스 {key} 가 현재 결과에 없음')
            diffs += 1
            continue
        for fld, gval in golden[key].items():
            nval = snap[key].get(fld)
            if gval != nval:
                print(f'  [불일치] {key}.{fld}: 골든={gval} → 현재={nval}')
                diffs += 1
    # 골든에 없는 새 케이스
    for key in snap:
        if key not in golden:
            print(f'  [신규] 케이스 {key} (골든에 없음 — --update 필요)')
            diffs += 1
    n_metrics = len(_KEYS) + 3
    if diffs == 0:
        print(f'✅ PASS — {len(golden)}개 케이스 × {n_metrics}개 지표 모두 골든값과 일치 (동작 보존)')
        return 0
    print(f'❌ FAIL — {diffs}건 불일치.')
    print('   의도한 변경이면: python audit_verify_regression.py --update')
    print('   의도치 않았으면: 동작이 바뀐 버그 — 원인 추적 필요')
    return 1


def do_smoke() -> int:
    """엔진 레벨 빠른 동작 확인 — MC 10회·LHS 10회·스트레스 셀당 3회.
    GUI 워커 경로는 검증하지 않음 (exe 테스트 모드와 역할 분리).
    """
    from engine_combat import monte_carlo_v7, monte_carlo_lhs, stress_test_grid
    cfg = dict(_BASE, fleet_preset='기동전단 기본',
               enemy_fleet_preset='랴오닝 항모전단', sim_seed=1)
    errors = []

    print('── 엔진 레벨 스모크 테스트 ──')

    # 1. 단일 시뮬
    try:
        r = run_v7_simulation(cfg)
        rate = r.get('intercept_rate', -1)
        print(f'  [1/4] 단일 시뮬       ✅  요격률={rate:.1%}')
    except Exception as e:
        print(f'  [1/4] 단일 시뮬       ❌  {e}')
        errors.append(str(e))

    # 2. MC 10회
    try:
        mc = monte_carlo_v7(cfg, n=10)
        print(f'  [2/4] MC 10회         ✅  평균={mc["mean_intercept"]:.1%}')
    except Exception as e:
        print(f'  [2/4] MC 10회         ❌  {e}')
        errors.append(str(e))

    # 3. LHS 10회
    try:
        lhs = monte_carlo_lhs(cfg, n=10)
        print(f'  [3/4] LHS 10회        ✅  평균={lhs["mean_intercept"]:.1%}')
    except Exception as e:
        print(f'  [3/4] LHS 10회        ❌  {e}')
        errors.append(str(e))

    # 4. 스트레스 테스트 셀당 3회
    try:
        st = stress_test_grid(cfg, n_per_cell=3)
        print(f'  [4/4] 스트레스 테스트 ✅  그리드 {len(st["grid"])}×{len(st["grid"][0])}')
    except Exception as e:
        print(f'  [4/4] 스트레스 테스트 ❌  {e}')
        errors.append(str(e))

    if errors:
        print(f'\n❌ FAIL — {len(errors)}건 오류')
        return 1
    print('\n✅ PASS — 엔진 4개 경로 모두 정상')
    return 0


if __name__ == '__main__':
    if '--update' in sys.argv:
        do_update()
    elif '--smoke' in sys.argv:
        sys.exit(do_smoke())
    else:
        sys.exit(do_check())
