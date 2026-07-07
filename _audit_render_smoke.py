# -*- coding: utf-8 -*-
"""
_audit_render_smoke.py — 결과 탭 렌더 크래시 테스트 (헤드리스, 빌드 제외 도구)

UIA 탭 순회는 이 앱의 커스텀 스타일 위젯이 TabItem으로 노출 안 돼 막힌다(BLIND_SPOTS).
탭 크래시는 거의 다 차트 렌더 함수(_render_*)에서 나므로, 그 함수들을 **실제 시뮬 결과 +
엣지(빈 데이터)**로 헤드리스 호출해 예외 없이 그림이 나오는지 검증한다. UIA보다 견고·빠름.

탭 '빌더'(DB·계획·changelog·도움말·설정)는 offscreen MainWindow 생성(_audit_roundtrip)이
이미 커버 — 생성자가 전 페이지를 build하므로 빌더 크래시는 그쪽이 잡는다.
시각적 깨짐(레이아웃·색상)은 사람 눈 몫 — 이 도구는 '렌더하면 죽는' 크래시 전용.

사용:  python _audit_render_smoke.py     # 렌더 크래시 있으면 exit 1
"""
import os, sys
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
import matplotlib
matplotlib.use('Agg')
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

RENDERS = ['_render_engagement_funnel', '_render_engagement_gantt',
           '_render_battle_timeline', '_render_campaign_report',
           '_render_fleet_chart', '_render_mc_chart', '_render_ci_chart',
           '_render_stress_test', '_render_sobol_chart']


def main():
    import app_main
    from engine_combat import run_v7_simulation, run_battle_simulation, monte_carlo_v7
    from engine_campaign import run_campaign, monte_carlo_campaign, load_forecast_model

    # 실제 결과 확보
    scfg = dict(fleet_preset='이지스 기동전단', enemy_fleet_preset='북한 포화 공격 (40발)',
                enemy_fleet_mode='preset', weather='흐림', sim_seed=1)
    single = run_v7_simulation(dict(scfg))
    mc = monte_carlo_v7(dict(scfg), n=12)   # _render_mc_chart·_ci_chart는 실제 MC로만 호출됨
    battle = run_battle_simulation(dict(fleet_preset='이지스 기동전단',
        enemy_fleet_preset='입체 포화 (최강)', enemy_fleet_mode='preset',
        enable_battle_mode=True, weather='흐림', sim_seed=1))
    model = load_forecast_model()
    camp = run_campaign(dict(fleet_preset='이지스 기동전단',
        enemy_fleet_preset='입체 포화 (최강)', enable_campaign_mode=True,
        campaign_horizon_h=72, campaign_seed=0), model=model)
    camp['campaign_mc'] = monte_carlo_campaign(dict(fleet_preset='이지스 기동전단',
        enemy_fleet_preset='입체 포화 (최강)', enable_campaign_mode=True), n=20, model=model)
    ev = single.get('active_events', [])

    # (렌더함수, [인자셋들]) — 실제 + 엣지(빈/None). 각 인자셋마다 호출해 예외 없나 확인.
    fn = {r: getattr(app_main, r) for r in RENDERS}
    calls = [
        ('_render_engagement_funnel', [(ev,), ([],)]),
        ('_render_engagement_gantt',  [(ev,), ([],)]),
        ('_render_battle_timeline',   [(battle,), (single,), ({},)]),
        ('_render_campaign_report',   [(camp,), (single,), ({},), ({'mode': 'campaign'},)]),
        ('_render_fleet_chart',       [({},)]),
        ('_render_mc_chart',          [(single, mc, scfg)]),           # 실제 MC(완전 dict)로만
        ('_render_ci_chart',          [(mc,)]),
        ('_render_stress_test',       [({},)]),                        # 정밀모드 아니면 {} (현실적)
        ('_render_sobol_chart',       [({},)]),
    ]

    fails, n_ok = [], 0
    for name, argsets in calls:
        for args in argsets:
            try:
                out = fn[name](*args)
                if out is None:
                    fails.append(f"{name}{_short(args)} → None 반환")
                else:
                    n_ok += 1
            except Exception as e:
                import traceback
                fails.append(f"{name}{_short(args)} → {e!r}\n{traceback.format_exc()[-400:]}")

    covered = {name for name, _ in calls}
    print(f"렌더 함수 {len(covered)}/{len(RENDERS)}개 · 호출 {n_ok}건 성공 · 크래시 {len(fails)}건")
    # vacuous 가드 — 전 렌더 함수를 실제로 호출했는지(빠지면 검사 무력화)
    missing = [r for r in RENDERS if r not in covered]
    if missing:
        print(f"❌ 렌더 함수 커버 누락(검사 무력화): {missing}")
        return 1
    if fails:
        print("\n❌ 렌더 크래시:")
        for f in fails:
            print(f"  {f}")
        return 1
    print("\n✅ PASS — 전 결과 탭 렌더 함수가 실제+엣지 데이터에서 크래시 0")
    return 0


def _short(args):
    parts = []
    for a in args:
        if isinstance(a, dict):
            parts.append('{...}' if a else '{}')
        elif isinstance(a, list):
            parts.append(f'[{len(a)}]')
        else:
            parts.append(type(a).__name__)
    return '(' + ', '.join(parts) + ')'


if __name__ == '__main__':
    sys.exit(main())
