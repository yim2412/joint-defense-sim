"""
app_engine — 엔진·스펙DB import 계층 (폴백 포함).

app_main.py에서 분리. engine_* 모듈과 db_specsheet를 try/except로 물어오고, 실패 시
앱이 죽지 않도록 빈 폴백을 세운다(`_V7_OK`·`_SPEC_DB_OK`가 성공 여부).

이 모듈을 따로 뺀 이유: app_workers(SimWorker 등)가 `_V7_OK`·`monte_carlo_v7` 같은 엔진
심볼을 직접 쓰는데, 그 import가 app_main에 있으면 app_workers→app_main 순환이 된다.
엔진 계층을 최하층으로 내려 app_main·app_workers가 나란히 참조하게 한다.

**여기서 앱 모듈(app_main·ui_*)을 import하지 말 것** — 순환.
"""

# v15.2 즉시예측 특징화 (없어도 앱 동작 — 룩업 폴백)
try:
    from forecast_features import featurize as _forecast_featurize
except Exception:
    _forecast_featurize = None


# ── 엔진 import ──────────────────────────────────────────────────────────────
# _V7_ERR 기본값 — 원래는 except 절에서만 정의돼, 분리 후 app_main이 이름 import하면
# 로드 성공 시(정상 상황) ImportError가 난다. 실패 시 아래 except가 str(e)로 덮는다.
_V7_ERR = ''

try:
    from engine_combat import (
        run_v7_simulation, run_battle_simulation, monte_carlo_v7, plot_v7, save_excel_report_v7,
        build_czml, BATTLE_HORIZON_S,
        FLEET_PRESETS as V7_FLEET_PRESETS,
        ENEMY_DB as V7_ENEMY_DB,
        WEATHER_DB,
        ENEMY_FLEET_PRESETS as V7_ENEMY_FLEET_PRESETS,
        ENEMY_FLEET_RANDOM_CFG as V7_RANDOM_CFG,
        MIXED_ATTACK_SCENARIOS as V7_MIXED_SCENARIOS,
        evaluate_req_v7, REQ_ITEMS_V7, evaluate_req_battle_v7,
        diagnose_vulnerabilities_v7,
        scenario_comparison_v7,
        save_json_report_v7,
        _mc_batch_worker, _mc_lhs_batch_worker, _heatmap_cell_worker,
        FRIENDLY_DB as V7_FRIENDLY_DB,
        SHIP_DB as V7_SHIP_DB,
        FRIENDLY_AIRCRAFT_DB as V7_AIRCRAFT_DB,
        normalize_enemy_db as _normalize_enemy_db,
        monte_carlo_lhs, stress_test_grid, sobol_analysis, compute_cvar,
        _LHS_PARAM_DEFS, STRESS_DIMS,
        recommend_fleet_v7, _FLEET_CANDIDATES_KR, _FLEET_CANDIDATES_COMBINED,
        compare_ab_v7,
        cec_comparison_v7,
        generate_briefing,
        WEATHER_TRANSITION_DB, WEATHER_INTENSITY_LADDER,
    )
    from engine_army import COASTAL_SAM_PRESETS   # v20.2b: 연안 방공 포대 편성(UI 콤보)
    from engine_army import ARMY_FIRE_PRESETS     # v21.2: 육군 지대지 화력 편성(UI 콤보)
    from engine_campaign import SLOC_ZONES        # v20.3: 상륙 목표 해안(UI 콤보)
    _V7_OK = True
except ImportError as e:
    _V7_OK = False
    _V7_ERR = str(e)
    V7_ENEMY_FLEET_PRESETS = {}
    V7_RANDOM_CFG          = {}
    V7_MIXED_SCENARIOS     = {}
    COASTAL_SAM_PRESETS    = {}
    ARMY_FIRE_PRESETS      = {}      # v21.2
    SLOC_ZONES             = []

# ── 스펙 DB import ────────────────────────────────────────────────────────────
try:
    from db_specsheet import SPEC_DETAIL_DB as _SPEC_DETAIL_DB
    _SPEC_DB_OK = True
except ImportError:
    _SPEC_DETAIL_DB = {}
    _SPEC_DB_OK = False
