"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   이지스 기동전단 통합 방어 시뮬레이터 — 실시간 대시보드  v6.8.4 / v7.0   ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  [5단계 — engine_v7 연동 + 전장 애니메이션]                                 ║
║                                                                              ║
║  NEW-A  사이드바 엔진 선택 라디오 (v6 / v7)                                 ║
║  NEW-B  v7 설정 패널 (적군 편대·아군 편대·공격 무기 재고·MC 횟수)           ║
║  NEW-C  v7 실행 분기 (run_v7_simulation + monte_carlo_v7)                   ║
║  NEW-D  전장 애니메이션 탭 — SimFrame 슬라이더 재생                         ║
║  NEW-E  v7 MC 통계·교전 로그·Excel/PNG 다운로드 탭                          ║
║                                                                              ║
║   실행 방법:  python -m streamlit run dashboard.py                           ║
║   필수 패키지: pip install streamlit pandas matplotlib numpy scipy openpyxl  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import io, os, sys, time
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')   # Streamlit에서 GUI 팝업 방지
import matplotlib.pyplot as plt
import streamlit as st

# ── 시뮬레이션 엔진 import ───────────────────────────────────────────────────
_DIR = os.path.dirname(os.path.abspath(__file__))
if _DIR not in sys.path:
    sys.path.insert(0, _DIR)

try:
    from engine import (
        ENEMY_DB, FRIENDLY_DB, FRIENDLY_AIRCRAFT_DB,
        WEATHER_DB, REQ_ITEMS, FLEET_PRESETS, SHIP_DB, ENEMY_FLEET_PRESETS, ENEMY_FLEET_RANDOM_CFG,
        save_scenario, load_scenario, list_scenarios, run_comparison,
        run_full_simulation, plot_all, save_excel_report,
    )
    _ENGINE_OK = True
except ImportError as e:
    _ENGINE_OK = False
    _ENGINE_ERR = str(e)

try:
    from engine_v7 import (
        run_v7_simulation, monte_carlo_v7, plot_v7, save_excel_report_v7,
        FLEET_PRESETS as V7_FLEET_PRESETS,
        ENEMY_DB as V7_ENEMY_DB,
    )
    _V7_OK = True
except ImportError as e:
    _V7_OK = False
    _V7_ERR = str(e)

# ── 페이지 기본 설정 ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="이지스 기동전단 통합 방어 시뮬레이터 v6.8.4",
    page_icon="⚓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── 커스텀 CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .metric-card {
        background: #1e2d3d; border-radius:10px; padding:16px 20px;
        border-left: 4px solid #3498db; margin-bottom:8px;
    }
    .metric-label { color:#7fb3d3; font-size:13px; margin-bottom:4px; }
    .metric-value { color:#ecf0f1; font-size:26px; font-weight:700; }
    .pass-badge  { background:#27ae60; color:white; border-radius:4px; padding:2px 8px; font-size:12px; }
    .fail-badge  { background:#c0392b; color:white; border-radius:4px; padding:2px 8px; font-size:12px; }
    .section-title { color:#3498db; font-size:18px; font-weight:700; margin:12px 0 8px; }
    div[data-testid="stSidebar"] { background:#0f1923; }
</style>
""", unsafe_allow_html=True)

# ── 엔진 로드 실패 시 ────────────────────────────────────────────────────────
if not _ENGINE_OK:
    st.error(f"⚠️ 시뮬레이션 엔진 로드 실패\n\n"
             f"`import_matplotlib_v6_2.py` 가 같은 폴더에 있는지 확인하세요.\n\n"
             f"오류: {_ENGINE_ERR}")
    st.stop()

# ════════════════════════════════════════════════════════════════════════════
#  사이드바 — 설정 패널
# ════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.image("https://img.shields.io/badge/정조대왕급-이지스구축함-003366?style=for-the-badge",
             use_container_width=True)
    st.title("⚓ 이지스 기동전단 v6.8 / v7.0")
    st.caption("파라미터를 설정한 뒤 실행 버튼을 누르세요.")

    # ── 엔진 선택 ────────────────────────────────────────────────────────────
    st.markdown("### ⚙️ 엔진 버전")
    _engine_choice = st.radio(
        "시뮬레이션 엔진",
        ["v6 — 이벤트 기반 (기존)", "v7 — 시간스텝 양방향 (신규)"],
        horizontal=True,
        help="v6: 기존 이벤트 기반 엔진 (REQ 판정·비교 지원)\nv7: 시간 스텝 양방향 교전 엔진 (SimFrame 애니메이션·MC 통계)",
    )
    use_v7 = (_engine_choice.startswith("v7")) and _V7_OK
    if _engine_choice.startswith("v7") and not _V7_OK:
        st.error(f"v7 엔진 로드 실패: {_V7_ERR}")
    st.divider()

    # ── v7 전용 설정 ─────────────────────────────────────────────────────────
    if use_v7:
        st.markdown("### 🔴 [v7] 적군 편대")
        _all_enemy_keys = list(V7_ENEMY_DB.keys())
        _n_etypes = int(st.number_input("위협 종류 수", 1, 8, 3, step=1, key="v7_ne"))
        v7_enemy_fleet = []
        for _idx in range(_n_etypes):
            _c1, _c2 = st.columns([3, 1])
            with _c1:
                _ep = st.selectbox(f"위협 #{_idx+1}", _all_enemy_keys,
                                   key=f"v7_ep_{_idx}")
            with _c2:
                _ec = int(st.number_input("수", 1, 8, 1, step=1,
                                          key=f"v7_ec_{_idx}"))
            v7_enemy_fleet.append({'preset': _ep, 'count': _ec})

        st.divider()
        st.markdown("### 🔵 [v7] 아군 편대")
        v7_fleet_preset = st.selectbox("편대 프리셋", list(V7_FLEET_PRESETS.keys()), key="v7_fp")
        v7_weather      = st.selectbox("날씨", list(WEATHER_DB.keys()), key="v7_wx")
        v7_detect_km    = int(st.number_input("탐지 거리 (km)", 50, 500, 200, step=10, key="v7_dk"))
        v7_sub_detect   = int(st.number_input("대잠 탐지 거리 (km)", 10, 100, 50, step=5, key="v7_sdk"))

        st.divider()
        st.markdown("### 🚀 [v7] 공격 무기 재고")
        _sc1, _sc2, _sc3 = st.columns(3)
        with _sc1: v7_haesong2 = int(st.number_input("해성-II", 0, 20, 8, key="v7_hs2"))
        with _sc2: v7_haesong1 = int(st.number_input("해성-I",  0, 20, 0, key="v7_hs1"))
        with _sc3: v7_harpoon  = int(st.number_input("하푼",    0, 20, 4, key="v7_hp"))

        st.divider()
        st.markdown("### 📊 [v7] 몬테카를로")
        v7_mc_n = int(st.number_input("MC 반복 횟수", 50, 1000, 200, step=50, key="v7_mcn"))

    # ── [1] 적군 위협 ─────────────────────────────────────────────────────
    st.markdown("### 🔴 [1] 적군 위협 / 편대")

    # NEW-L: 적군 편대 모드
    enemy_fleet_mode_label = st.radio(
        "적군 편대 모드", ['단일 (기존)', '프리셋', '커스텀', '랜덤'],
        horizontal=True,
        help="단일(기존) / 프리셋(PLA 교리 5종) / 커스텀(직접 선택) / 랜덤(난이도 기반)")
    enemy_fleet_mode_map  = {'단일 (기존)':'single','프리셋':'preset','커스텀':'custom','랜덤':'random'}
    enemy_fleet_mode      = enemy_fleet_mode_map[enemy_fleet_mode_label]
    enemy_fleet_preset    = list(ENEMY_FLEET_PRESETS.keys())[0]
    enemy_fleet_difficulty= '보통'
    enemy_fleet_seed      = None
    enemy_fleet_custom    = []

    if enemy_fleet_mode == 'preset':
        enemy_fleet_preset = st.selectbox(
            "PLA 편대 프리셋", list(ENEMY_FLEET_PRESETS.keys()),
            help="A2/AD(J-16×4+H-6×2) / 항모킬체인(DF-21D×2+DF-17×1+J-20×2) / 수상함(055×1+052D×2+022×4) / 대잠(095+093) / 전면전(전카테고리)")
        specs = ENEMY_FLEET_PRESETS.get(enemy_fleet_preset, [])
        st.caption(" | ".join(f"{s['preset'].split('(')[0].strip()}×{s['count']}" for s in specs))
    elif enemy_fleet_mode == 'custom':
        st.caption("위협 종류와 수량 직접 입력 (최대 5종)")
        n_etypes = int(st.number_input("위협 종류 수", 1, 5, 2, step=1))
        all_enemy_keys = list(ENEMY_DB.keys())
        for idx in range(n_etypes):
            c1, c2 = st.columns([3, 1])
            with c1:
                ep = st.selectbox(f"위협 #{idx+1}", all_enemy_keys, key=f"ep_{idx}")
            with c2:
                ec = int(st.number_input("수량", 1, 8, 1, step=1, key=f"ec_{idx}"))
            enemy_fleet_custom.append({'preset': ep, 'count': ec})
    elif enemy_fleet_mode == 'random':
        c1, c2 = st.columns([1, 1])
        with c1:
            enemy_fleet_difficulty = st.selectbox(
                "난이도", list(ENEMY_FLEET_RANDOM_CFG.keys()), index=1,
                help="쉬움(2-4개) / 보통(4-8개) / 어려움(8-14개) / 극한(14-24개)")
        with c2:
            seed_val = int(st.number_input("시드 (0=매번 랜덤)", 0, 99999, 0, step=1,
                                            help="같은 시드 → 동일 편대 재현"))
            enemy_fleet_seed = None if seed_val == 0 else seed_val

    st.divider()
    st.markdown("##### 단일 모드 기준 위협 선택")
    enemy_preset = st.selectbox(
        "적 위협 프리셋 (32종)",
        list(ENEMY_DB.keys()),
        index=list(ENEMY_DB.keys()).index('MiG-23 (플로거)'),
        help="ENEMY_DB 32종 중 선택")

    _ep = ENEMY_DB[enemy_preset]
    st.caption(f"카테고리: **{_ep['category']}** | 속도: **{_ep['speed_ms']} m/s** | "
               f"고도: **{_ep.get('altitude_m',0)} m**")

    enemy_fires_missile = st.toggle("적 미사일/어뢰 발사", value=True,
        help="ON: 적이 접근하면서 미사일·어뢰 동시 발사 (실전 환경)\nOFF: 플랫폼 자체만 위협 (단순 테스트용)")
    missile_salvo_mode  = st.radio(
        "다발 발사 모드", ['RANDOM','FIXED','MAX'],
        horizontal=True, index=0,
        help="RANDOM: 플랫폼별 최소~최대 사이 무작위 발사 (권장)\nFIXED: 아래 고정 수량으로 발사\nMAX: 각 플랫폼 최대 발사 수량 (최악 시나리오)")
    if missile_salvo_mode == 'FIXED':
        missile_salvo_fixed = st.number_input(
            "고정 발사 수", min_value=1, max_value=12, value=2, step=1)
    else:
        missile_salvo_fixed = 2

    st.divider()

    # ── [2] 날씨 ──────────────────────────────────────────────────────────
    st.markdown("### 🌤️ [2] 날씨 조건")
    weather = st.selectbox("날씨", list(WEATHER_DB.keys()), index=0)
    _wx = WEATHER_DB[weather]
    st.caption(f"탐지 ×{_wx['detect_range_factor']:.2f} | "
               f"Pk {_wx['intercept_prob_delta']:+.2f} | "
               f"C&D ×{_wx['cd_time_factor']:.2f}")

    st.divider()

    # ── [3] 시나리오 수치 ─────────────────────────────────────────────────
    st.markdown("### 📋 [3] 시나리오")
    col1, col2 = st.columns(2)
    with col1:
        num_threats = st.number_input("위협 수", 1, 24, 5, step=1)
        cd_time_s   = st.number_input("C&D 시간 (s)", 5, 120, 20, step=5,
            help="탐지→교전 결심까지 소요 시간. 실전 이지스 기준 15~25초\n이 값이 최대 허용 C&D보다 크면 REQ-02 FAIL")
    with col2:
        launch_interval_s = st.number_input("발진 간격 (s)", 10, 600, 60, step=10,
            help="각 위협이 몇 초 간격으로 순차 발진하는지\n짧을수록 동시 채널 포화 확률 증가 (채널 한계 시험 시 줄이세요)")
        confirm_time_s    = st.number_input("확인 시간 (s)", 5, 60, 15, step=5,
            help="요격 실패 후 결과 확인 및 재교전 결심까지 걸리는 시간\n클수록 재교전 기회 감소 → 방어 난이도 상승")
    cd_jitter_s = st.slider("C&D 지터 ±(s)", 0, 30, 5, step=1,
        help="C&D 시간에 ±이 값만큼 무작위 오차 추가 (현실감 부여)\n0: 항상 동일한 C&D 시간 (결정론적 시뮬레이션)")

    st.divider()

    # ── [4] 전투 모드 & 무기 ──────────────────────────────────────────────
    st.markdown("### 🎯 [4] 전투 설정")
    combat_mode = st.radio("전투 모드", ['AUTO','MANUAL'], horizontal=True,
        help="AUTO: TEWA 자동 무기 할당 (위협·거리·재고 고려, 권장)\nMANUAL: 아래 기준 무기만 강제 사용 (단일 무기 성능 검증용)")
    friendly_preset = st.selectbox("기준 무기", list(FRIENDLY_DB.keys()), index=0,
        help="MANUAL 모드에서 사용할 무기. AUTO 모드에서는 TEWA가 자동 선택하므로 참고용\nSM-3: 탄도·HGV 전용 | SM-6: 장거리·QBM | SM-2: 주력 대공\nRAM: 근접 방어 | 홍상어·청상어: 대잠 전용")

    st.markdown("**초기 재고**")
    inv_col1, inv_col2 = st.columns(2)
    with inv_col1:
        sm3_stock  = st.number_input("SM-3",    0, 32, 8,  step=1)
        sm6_stock  = st.number_input("SM-6",    0, 96, 32, step=4)
        sm2_stock  = st.number_input("SM-2",    0, 96, 48, step=4)
        ram_stock  = st.number_input("RAM",     0, 42, 21, step=1)
    with inv_col2:
        hong_stock = st.number_input("홍상어",  0, 32, 16, step=1)
        chung_stock= st.number_input("청상어",  0, 24, 12, step=1)
        mk46_stock = st.number_input("Mk.46",   0, 16, 8,  step=1)

    st.divider()

    # ── [5] 전술 기능 ─────────────────────────────────────────────────────
    st.markdown("### ⚙️ [5] 전술 기능")
    enable_ecm              = st.toggle("NEW-G: ECM 재밍",          value=True,
            help="적 전자전 재밍으로 아군 미사일 Pk 감소\n거리 반비례 적용 (50km 기준), J-20·Su-35 등 고성능 ECM 보유 기체에 효과적")
    enable_enemy_evasion    = st.toggle("NEW-E: 적 회피 기동",      value=True,
            help="요격 실패 시 적이 속도 증가 + 고도/수심 변경 후 재접근\nOFF: 적이 일직선으로만 접근 (단순화 시험용)")
    enable_missile_evasion  = st.toggle("NEW-D: 종말 회피",         value=True,
            help="아군 미사일이 20km 이내 진입 시 적 기동으로 Pk 감소\nOFF: 종말 회피 없음 (낙관적 시나리오)")
    enable_acoustic_decoy   = st.toggle("NEW-B: 음향 기만기",       value=True,
            help="대잠: AN/SLQ-25 기만기 자동 전개, 성공률 60%\n실패 시 함정 회피 기동(30%) 2차 방어")
    enable_self_defense     = st.toggle("NEW-F: 적 자체방어",       value=True,
            help="채프·플레어: 아군 미사일 Pk 감소 (항공기·수상함)\n적 CIWS: 수상함이 아군 미사일을 직접 요격 (055형 최대 33%)")
    decoy_stock             = st.number_input("기만기 재고", 0, 16, 4, step=1,
            help="AN/SLQ-25 Nixie 음향 기만기 초기 탑재 수\n실제 기준 4발. 소진 시 함정 회피 기동만 작동")

    st.divider()

    # ── [6] 항공 자산 ─────────────────────────────────────────────────────
    st.markdown("### 🚁 [6] 항공 자산 (대잠 전용)")
    enable_helo = st.toggle("NEW-H: 함재 헬기", value=False,
                             help="대잠 시나리오에서만 효과 있음")
    helo_preset = 'AW-159 와일드캣'
    if enable_helo:
        # v6.8.4: on_deck=True인 함재 헬기만 표시 (MH-60R 등 미운용 기체 제외)
        _avail_helos = [k for k,v in FRIENDLY_AIRCRAFT_DB.items()
                        if v.get('base_type','ship')=='ship' and v.get('on_deck',False)]
        helo_preset = st.selectbox(
            "헬기 기종",
            _avail_helos,
            index=0)
        _h = FRIENDLY_AIRCRAFT_DB[helo_preset]
        st.caption(f"속도 {_h['speed_ms']}m/s | 항속 {_h['range_km']}km | 탑재 중")

    enable_p3c = st.toggle("NEW-I: P-3C 오라이온", value=False,
                            help="포항기지 출격, 풍랑에서도 운용 가능")
    p3c_preset = 'P-3C 오라이온'
    if enable_p3c:
        _p = FRIENDLY_AIRCRAFT_DB.get('P-3C 오라이온', {})
        st.caption(f"포항기지 출격 | 준비 {_p.get('sortie_time_s',2400)//60}분 | "
                   f"어뢰 {_p.get('payload_cnt',4)}발 | 태풍만 불가")

    enable_p8a = st.toggle("NEW-J: P-8A 포세이돈", value=False,
                            help="P-3C 후속기, 준비 30분, 소노부이 성능 향상")
    p8a_preset = 'P-8A 포세이돈'
    if enable_p8a:
        _p8 = FRIENDLY_AIRCRAFT_DB.get('P-8A 포세이돈', {})
        st.caption(f"포항기지 출격 | 준비 {_p8.get('sortie_time_s',1800)//60}분 | "
                   f"어뢰 {_p8.get('payload_cnt',5)}발 | 소노부이+18km | 태풍만 불가")

    st.divider()
    st.subheader("🚢 NEW-K: 아군 편대")
    enable_fleet = st.toggle("편대 모드", value=False,
                              help="ON: 한국 해군 교리 기반 편대 시뮬레이션\nOFF: 기존 단일 함정 방식 (정조대왕함 1척)")
    fleet_mode        = 'preset'
    fleet_preset      = '기동전단 기본'
    fleet_custom_ships= []
    if enable_fleet:
        fleet_mode = st.radio("구성 방식", ['프리셋', '커스텀'],
                              horizontal=True,
                              help="프리셋: 교리 기반 편대 선택\n커스텀: 함정 종류·수량 직접 지정")
        fleet_mode = 'preset' if fleet_mode == '프리셋' else 'custom'

        if fleet_mode == 'preset':
            fleet_preset = st.selectbox(
                "편대 프리셋", list(FLEET_PRESETS.keys()), index=1,
                help="단독 작전: 1척 | 기동전단 기본: KDX-III+KDX-II+FFX\nBMD 중점: KDX-III×2+KDX-II | 대잠 중점: KDX-III+FFX×2\n최대 편대: KDX-III×2+KDX-II×2+FFX×2")
            preset_ships = FLEET_PRESETS.get(fleet_preset, [])
            st.caption(" | ".join(f"{s['name']}({s['type']})" for s in preset_ships))
        else:
            st.caption("추가할 함정을 선택하세요 (최대 6척)")
            fleet_custom_ships = []
            n_custom = st.number_input("함정 수", 1, 6, 2, step=1)
            ship_type_opts = list(SHIP_DB.keys())
            name_defaults  = {
                'KDX-III': ['정조대왕함','세종대왕함','율곡이이함','서애류성룡함'],
                'KDX-II':  ['충무공이순신함','문무대왕함','대조영함','왕건함'],
                'FFX':     ['대구함','인천함','경남함','전남함'],
            }
            for idx in range(int(n_custom)):
                c1, c2 = st.columns([1, 1])
                with c1:
                    stype = st.selectbox(f"#{idx+1} 함종",
                                         ship_type_opts, key=f"cst_{idx}",
                                         help="KDX-III: 이지스 구축함\nKDX-II: 구축함\nFFX: 호위함")
                with c2:
                    default_name = name_defaults[stype][idx % len(name_defaults[stype])]
                    sname = st.text_input(f"#{idx+1} 함명", value=default_name,
                                          key=f"csn_{idx}")
                fleet_custom_ships.append({'name': sname, 'type': stype})

    st.divider()

    # ── [7] MC 설정 ───────────────────────────────────────────────────────
    st.markdown("### 📊 [7] 몬테카를로")
    mc_save_nth = st.number_input("샘플 로그 저장 회차 (0=저장안함)",
                                  0, 1000, 0, step=1,
                                  help="MC 1000회 중 특정 회차의 교전 로그를 엑셀 Sheet9에 저장\n0: 저장 안 함 | 예) 500: 500번째 회차 로그 저장")

    # ── 실행 버튼 ──────────────────────────────────────────────────────────
    st.divider()
    # NEW-M: 시나리오 저장/불러오기
    st.subheader("💾 시나리오 관리")
    sc_col1, sc_col2 = st.columns([3, 1])
    with sc_col1:
        sc_name = st.text_input("파일명", value="scenario_1",
                                 help="확장자 없이 입력. 저장 시 .json 자동 추가")
    with sc_col2:
        st.write("")
        st.write("")
        save_btn = st.button("💾 저장")

    sc_files = list_scenarios('.')
    if sc_files:
        load_file = st.selectbox("불러오기", ['선택 안 함'] + sc_files,
                                  help="저장된 시나리오 파일 선택 후 불러오기")
        load_btn = st.button("📂 불러오기")
    else:
        load_btn = False; load_file = None
        st.caption("저장된 시나리오 없음")

    st.divider()
    # NEW-N: A vs B 비교 모드
    st.subheader("📊 A vs B 비교 모드")
    enable_comparison = st.toggle("A vs B 비교 활성화", value=False,
        help="ON: 현재 설정(A)과 별도 설정(B)을 동시 실행하여 결과 비교")
    if enable_comparison:
        with st.expander("시나리오 B 설정", expanded=True):
            enemy_preset_b = st.selectbox("적 위협 (B)", list(ENEMY_DB.keys()),
                index=list(ENEMY_DB.keys()).index('J-20 (위룡)'),
                key='ep_b')
            weather_b = st.selectbox("날씨 (B)", list(WEATHER_DB.keys()),
                index=0, key='wx_b')
            fleet_preset_b = st.selectbox("아군 편대 (B)", list(FLEET_PRESETS.keys()),
                index=1, key='fp_b')
            enemy_fleet_mode_b = st.radio("적군 편대 모드 (B)",
                ['단일','프리셋'], horizontal=True, key='efm_b')
            enemy_fleet_preset_b = st.selectbox("적군 프리셋 (B)",
                list(ENEMY_FLEET_PRESETS.keys()), key='efp_b')                 if enemy_fleet_mode_b == '프리셋' else None
            st.caption("나머지 설정(무기 재고·채널 등)은 A와 동일")

    st.divider()
    # v6.8: 다방위 공격 + CEC 설정
    with st.expander("🌐 v6.8 교리 설정", expanded=False):
        enable_multibearing = st.toggle("다방위 공격 (전방위 랜덤)",
            value=False, key="multibearing",
            help="ON: 위협이 사방에서 무작위로 접근 (Top-down 뷰 자동 추가)\nOFF: 정면 단일 방향 (기존)")
        if enable_multibearing:
            bearing_seed_val = int(st.number_input("방위각 시드 (0=매번 랜덤)", 0, 99999, 0,
                key="bseed", help="같은 시드 = 동일 방위각 재현"))
            bearing_seed = None if bearing_seed_val == 0 else bearing_seed_val
        else:
            bearing_seed = None
        st.divider()
        enable_cec_preassign = st.toggle("CEC 사전 동시 배정 (편대 모드 전용)",
            value=False, key="cec_pre",
            help="ON: 위협 탐지 시 1차+2차 함정 동시 배정·대기\n→ 1차 성공 시 2차 취소, 1차 실패 시 2차 자동 발사\nOFF: 기존 사후 인계 방식")

    st.divider()
    # BUG-FIX v6.5.1: 레이어 토글을 사이드바로 이동 (항상 표시)
    with st.expander("🗺️ 전술교전도 레이어", expanded=False):
        lc1,lc2 = st.columns(2)
        with lc1:
            show_fleet_positions = st.toggle("함정 위치·구역",   value=True,
                key='layer_fleet',
                help="편대 모드 ON 시 각 함정 위치와 담당 구역 표시")
            show_threat_paths    = st.toggle("위협 경로·요격점", value=True,
                key='layer_threat',
                help="적 접근 경로와 요격 성공/실패 지점 표시")
            show_radar_range     = st.toggle("레이더 탐지 범위", value=True,
                key='layer_radar',
                help="편대 함정별 레이더 탐지 반경 표시")
        with lc2:
            show_timeline        = st.toggle("교전 타임라인",    value=True,
                key='layer_timeline',
                help="하단에 시간축 기반 교전 순서 표시")
            show_weapon_range    = st.toggle("무기 사거리 링",   value=True,
                key='layer_wpn',
                help="SM-3/SM-6/SM-2/RAM 각 사거리 링 표시")

    st.divider()
    if use_v7:
        st.caption("v7 설정은 상단 **[v7]** 섹션에서 입력하세요.")
        run_btn = st.button("🚀 v7 시뮬레이션 실행", type="primary",
                            use_container_width=True)
    else:
        run_btn = st.button("🚀 시뮬레이션 실행", type="primary",
                            use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════
#  메인 영역 — 헤더
# ════════════════════════════════════════════════════════════════════════════
st.markdown(
    "<h1 style='text-align:center;color:#3498db;'>⚓ 이지스 기동전단 통합 방어 시뮬레이터</h1>"
    "<p style='text-align:center;color:#7f8c8d;'>v6.8.4 — HeloEvent is_missile 완전 수정·MH-60R 제거</p>",
    unsafe_allow_html=True)
st.divider()

# ════════════════════════════════════════════════════════════════════════════
#  시뮬레이션 실행
# ════════════════════════════════════════════════════════════════════════════

# NEW-M: 시나리오 저장 처리
if save_btn:
    try:
        _fp = f"{sc_name.strip() or 'scenario'}.json"
        _cfg_preview = {
            'enemy_preset': enemy_preset, 'friendly_preset': friendly_preset,
            'weather': weather, 'num_threats': num_threats,
            'enable_fleet': enable_fleet, 'fleet_preset': fleet_preset,
            'enemy_fleet_mode': enemy_fleet_mode,
        }
        save_scenario(_cfg_preview, _fp)
        st.sidebar.success(f"저장 완료: {_fp}")
    except Exception as _e:
        st.sidebar.error(f"저장 실패: {_e}")

# NEW-M: 시나리오 불러오기 처리
if load_btn and load_file and load_file != '선택 안 함':
    try:
        st.session_state['loaded_scenario'] = load_scenario(load_file)
        st.sidebar.success(f"불러오기 완료: {load_file}")
    except Exception as _e:
        st.sidebar.error(f"불러오기 실패: {_e}")

if run_btn and use_v7:
    _v7_cfg = {
        'fleet_preset':    v7_fleet_preset,
        'weather':         v7_weather,
        'detect_km':       v7_detect_km,
        'sub_detect_km':   v7_sub_detect,
        'haesong2_stock':  v7_haesong2,
        'haesong1_stock':  v7_haesong1,
        'harpoon_stock':   v7_harpoon,
        'enemy_fleet':     v7_enemy_fleet,
    }
    with st.spinner("⚙️ v7 시뮬레이션 실행 중..."):
        try:
            _t0 = time.time()
            _v7_result = run_v7_simulation(_v7_cfg)
            _v7_mc     = monte_carlo_v7(_v7_cfg, n=v7_mc_n)
            _v7_elapsed = time.time() - _t0
        except Exception as _e:
            st.error(f"❌ v7 오류: {_e}")
            st.exception(_e)
            st.stop()
    st.session_state['v7_sim_data'] = {
        'result':  _v7_result,
        'mc':      _v7_mc,
        'cfg':     _v7_cfg,
        'elapsed': _v7_elapsed,
    }
    st.success(f"✅ v7 완료 ({_v7_elapsed:.1f}초) — MC {v7_mc_n}회")

if run_btn and not use_v7:
    cfg = {
        'enemy_preset':               enemy_preset,
        'friendly_preset':            friendly_preset,
        'category':                   ENEMY_DB[enemy_preset]['category'],
        'weather':                    weather,
        'enemy_fires_missile':        enemy_fires_missile,
        'missile_salvo_mode':         missile_salvo_mode,
        'missile_salvo_fixed':        missile_salvo_fixed,
        'enable_enemy_evasion':       enable_enemy_evasion,
        'enable_missile_evasion':     enable_missile_evasion,
        'enable_acoustic_decoy':      enable_acoustic_decoy,
        'enable_ship_torpedo_evasion':True,
        'decoy_stock':                int(decoy_stock),
        'enable_enemy_self_defense':  enable_self_defense,
        'enable_ecm':                 enable_ecm,
        'enable_helo':                enable_helo,
        'helo_preset':                helo_preset,
        'enable_p3c':                 enable_p3c,
        'p3c_preset':                 p3c_preset,
        'enable_p8a':                  enable_p8a,
        'p8a_preset':                  p8a_preset,
        'enable_fleet':                enable_fleet,
        'fleet_mode':                  fleet_mode,
        'fleet_preset':                fleet_preset,
        'fleet_custom_ships':          fleet_custom_ships,
        'enable_multibearing':         enable_multibearing,
        'bearing_seed':                bearing_seed,
        'enable_cec_preassign':        enable_cec_preassign,
        'enemy_fleet_mode':            enemy_fleet_mode,
        'enemy_fleet_preset':          enemy_fleet_preset,
        'enemy_fleet_difficulty':      enemy_fleet_difficulty,
        'enemy_fleet_seed':            enemy_fleet_seed,
        'enemy_fleet_custom':          enemy_fleet_custom,
        'mc_save_nth':                int(mc_save_nth),
        'num_threats':                int(num_threats),
        'launch_interval_s':          int(launch_interval_s),
        'cd_time_s':                  int(cd_time_s),
        'cd_jitter_s':                int(cd_jitter_s),
        'confirm_time_s':             int(confirm_time_s),
        'combat_mode':                combat_mode,
        'inventory': {
            'SM-3 Block IIA':     int(sm3_stock),
            'SM-6':               int(sm6_stock),
            'SM-2 Block IIIB':    int(sm2_stock),
            'RIM-116 RAM':        int(ram_stock),
            '홍상어 (대잠)':      int(hong_stock),
            '청상어 (경어뢰)':    int(chung_stock),
            'Mk.46 경어뢰':       int(mk46_stock),
            'CIWS-II (Phalanx)':  9999,
        },
        'use_custom_enemy':   False,
        'custom_enemy_speed': 1000,
        'custom_detect_km':   300,
    }

    # ── 실행 ──────────────────────────────────────────────────────────────
    with st.spinner("⚙️ 시뮬레이션 실행 중..."):
        t0 = time.time()
        try:
            (max_cd, t_arrive, t_fly, mc, min_d,
             all_events, active_events, verdicts, details,
             sc_results, dm_eff, weather_delta, cd_eff,
             total_cost, global_inv, ch_mgr,
             ship_status) = run_full_simulation(cfg)
            elapsed = time.time() - t0
        except Exception as e:
            st.error(f"❌ 시뮬레이션 오류: {e}")
            st.exception(e)
            st.stop()

    # BUG-FIX v6.5.1: 결과를 session_state에 저장 → 레이어 토글 변경 시에도 유지
    st.session_state['sim_data'] = dict(
        max_cd=max_cd, t_arrive=t_arrive, t_fly=t_fly, mc=mc, min_d=min_d,
        all_events=all_events, active_events=active_events,
        verdicts=verdicts, details=details, sc_results=sc_results,
        dm_eff=dm_eff, weather_delta=weather_delta, cd_eff=cd_eff,
        total_cost=total_cost, global_inv=global_inv, ch_mgr=ch_mgr,
        ship_status=ship_status, elapsed=elapsed, cfg=cfg,
    )
    st.success(f"✅ 완료 ({elapsed:.1f}초)")

    # NEW-N: A vs B 비교 실행
    if enable_comparison:
        with st.spinner("📊 시나리오 B 실행 중..."):
            cfg_b = {**cfg,
                'enemy_preset':       enemy_preset_b,
                'weather':            weather_b,
                'fleet_preset':       fleet_preset_b,
                'enemy_fleet_mode':   'preset' if enemy_fleet_mode_b == '프리셋' else 'single',
                'enemy_fleet_preset': enemy_fleet_preset_b or cfg.get('enemy_fleet_preset','A2/AD 항공 포화'),
            }
            cmp_results = run_comparison(cfg, cfg_b)
            st.session_state['comparison_results'] = cmp_results
        st.success("📊 A vs B 비교 완료 — 'A vs B 비교' 탭에서 확인하세요.")

# ════════════════════════════════════════════════════════════════════════════
#  v7 결과 표시
# ════════════════════════════════════════════════════════════════════════════
if 'v7_sim_data' in st.session_state and use_v7:
    _vd      = st.session_state['v7_sim_data']
    _vr      = _vd['result']
    _vm      = _vd['mc']
    _vcfg    = _vd['cfg']
    _velapsed= _vd['elapsed']

    # ── 핵심 지표 카드 ──────────────────────────────────────────────────────
    def _vcard(col, label, value, color="#3498db"):
        col.markdown(
            f"<div class='metric-card' style='border-color:{color}'>"
            f"<div class='metric-label'>{label}</div>"
            f"<div class='metric-value'>{value}</div></div>",
            unsafe_allow_html=True)

    _vc1,_vc2,_vc3,_vc4,_vc5 = st.columns(5)
    _vcard(_vc1, "MC 평균 요격률",
           f"{_vm['mean_intercept']:.1%}",
           "#27ae60" if _vm['mean_intercept'] >= 0.9 else "#e74c3c")
    _vcard(_vc2, "완전 요격 비율", f"{_vm['full_pass_rate']:.1%}")
    _vcard(_vc3, "아군 피격 (단일)", f"{_vr['friendly_hits']}회",
           "#27ae60" if _vr['friendly_hits'] == 0 else "#e74c3c")
    _vcard(_vc4, "적 격침 (단일)", f"{_vr['enemy_ships_destroyed']}기/척")
    _vcard(_vc5, "총 비용 (단일)", f"${_vr['total_cost']:,.0f}")

    st.divider()
    st.caption(f"v7 시뮬 종료: {_vr['sim_time']:.0f}s | "
               f"총 위협: {_vr['total_threats']}발/기 | "
               f"요격: {_vr['intercepted_threats']}발/기 | "
               f"실행시간: {_velapsed:.1f}s")

    # ── 탭 구성 ─────────────────────────────────────────────────────────────
    _vt1, _vt2, _vt3, _vt4 = st.tabs(
        ["🗺️ 전장 애니메이션", "📊 MC 통계", "📜 교전 로그", "⬇️ 다운로드"])

    # ── Tab 1: 전장 애니메이션 ──────────────────────────────────────────────
    with _vt1:
        _frames = _vr.get('frames', [])
        if not _frames:
            st.info("프레임 데이터 없음")
        else:
            _t_max = len(_frames) - 1
            _fi = st.slider("시각 (프레임)", 0, _t_max, 0,
                            help="슬라이더를 움직여 전장 상황을 재생하세요")
            _frame = _frames[_fi]
            st.caption(f"t = {_frame.t:.0f}s")

            import matplotlib
            matplotlib.use('Agg')
            import matplotlib.pyplot as plt
            _fig, _ax = plt.subplots(figsize=(9, 9),
                                     facecolor='#0a0e1a')
            _ax.set_facecolor('#0a0e1a')
            _ax.tick_params(colors='#aab', labelsize=8)
            for _sp in _ax.spines.values():
                _sp.set_color('#1e2a3a')

            # 배경 바다
            _ax.set_xlim(-320_000, 320_000)
            _ax.set_ylim(-320_000, 320_000)
            _ax.set_xlabel('X (km)', color='#aab', fontsize=8)
            _ax.set_ylabel('Y (km)', color='#aab', fontsize=8)
            _ax.xaxis.set_major_formatter(
                plt.FuncFormatter(lambda v, _: f'{v/1000:.0f}'))
            _ax.yaxis.set_major_formatter(
                plt.FuncFormatter(lambda v, _: f'{v/1000:.0f}'))
            _ax.set_title(f'전장 상황 — t={_frame.t:.0f}s',
                          color='#dde', fontsize=10, fontweight='bold')
            _ax.grid(color='#1e2a3a', linewidth=0.5)

            # 아군 함정
            for _sname, _sx, _sy, _salive, _shp in _frame.friendly_ships:
                _color = '#2ecc71' if _salive else '#7f8c8d'
                _ax.scatter(_sx, _sy, s=120, c=_color,
                            marker='^', zorder=5)
                _ax.annotate(_sname, (_sx, _sy),
                             xytext=(4, 4), textcoords='offset points',
                             color=_color, fontsize=6)

            # 적 위협
            for _euid, _epname, _ex, _ey, _ealive, _ehp in _frame.enemy_ships:
                _color = '#e74c3c' if _ealive else '#7f8c8d'
                _ax.scatter(_ex, _ey, s=100, c=_color,
                            marker='v', zorder=5)
                _ax.annotate(_epname[:8], (_ex, _ey),
                             xytext=(4, -10), textcoords='offset points',
                             color=_color, fontsize=6)

            # 미사일
            _mtype_colors = {
                'enemy_strike':    '#ff6b6b',
                'friendly_strike': '#3498db',
                'friendly_sam':    '#2ecc71',
                'enemy_sam':       '#e67e22',
            }
            for _muid, _mx, _my, _mtype, _mname in _frame.missiles:
                _mc = _mtype_colors.get(_mtype, '#aab')
                _ax.scatter(_mx, _my, s=20, c=_mc,
                            marker='o', alpha=0.8, zorder=4)

            # 범례
            from matplotlib.lines import Line2D
            _legend = [
                Line2D([0],[0], marker='^', color='w',
                       markerfacecolor='#2ecc71', markersize=9,
                       label='아군 함정'),
                Line2D([0],[0], marker='v', color='w',
                       markerfacecolor='#e74c3c', markersize=9,
                       label='적 위협'),
                Line2D([0],[0], marker='o', color='w',
                       markerfacecolor='#ff6b6b', markersize=6,
                       label='적 미사일'),
                Line2D([0],[0], marker='o', color='w',
                       markerfacecolor='#2ecc71', markersize=6,
                       label='아군 SAM'),
                Line2D([0],[0], marker='o', color='w',
                       markerfacecolor='#3498db', markersize=6,
                       label='아군 대함'),
            ]
            _ax.legend(handles=_legend, loc='upper right', fontsize=7,
                       facecolor='#0a0e1a', labelcolor='white',
                       edgecolor='#1e2a3a')

            st.pyplot(_fig, use_container_width=True)
            plt.close(_fig)

            # 해당 프레임 이벤트
            if _frame.events:
                st.markdown("**이벤트:**")
                for _ev in _frame.events:
                    st.caption(f"▶ {_ev}")

    # ── Tab 2: MC 통계 ──────────────────────────────────────────────────────
    with _vt2:
        import io as _io
        _mc_fig_buf = _io.BytesIO()
        _mc_img = plot_v7(_vr, _vm, _vcfg, img_path='_v7_tmp_chart.png')
        with open('_v7_tmp_chart.png', 'rb') as _f:
            st.image(_f.read(), use_container_width=True)

        import pandas as _pd
        _mc_df = _pd.DataFrame({
            '회차': range(1, _vm['n'] + 1),
            '요격률': [f"{v:.1%}" for v in _vm['intercept_rates']],
            '아군피격': _vm['friendly_hits'],
            '적격침': _vm['enemy_destroyed'],
            '함정손실': _vm['friendly_lost'],
            '비용(USD)': [f"${c:,.0f}" for c in _vm['total_costs']],
        })
        st.dataframe(_mc_df, use_container_width=True, height=300)

    # ── Tab 3: 교전 로그 ────────────────────────────────────────────────────
    with _vt3:
        _log_df = _pd.DataFrame(
            [(f"{t:.0f}s", msg) for t, msg in _vr.get('log', [])],
            columns=['시각', '이벤트'],
        )
        st.dataframe(_log_df, use_container_width=True,
                     height=500)

    # ── Tab 4: 다운로드 ─────────────────────────────────────────────────────
    with _vt4:
        _dc1, _dc2 = st.columns(2)
        with _dc1:
            if st.button("📄 v7 Excel 보고서 생성", use_container_width=True):
                with st.spinner("Excel 생성 중..."):
                    _xp = save_excel_report_v7(
                        _vr, _vm, _vcfg,
                        img_path='_v7_tmp_chart.png',
                        xlsx_path='v7_보고서.xlsx',
                    )
                with open(_xp, 'rb') as _f:
                    st.download_button(
                        "⬇️ Excel 다운로드", _f.read(),
                        file_name='이지스_v7_보고서.xlsx',
                        mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    )
        with _dc2:
            if st.button("🖼️ PNG 차트 다운로드", use_container_width=True):
                import os as _os
                if _os.path.exists('_v7_tmp_chart.png'):
                    with open('_v7_tmp_chart.png', 'rb') as _f:
                        st.download_button(
                            "⬇️ PNG 다운로드", _f.read(),
                            file_name='이지스_v7_분석.png',
                            mime='image/png',
                        )

# BUG-FIX v6.5.1: session_state에 데이터 있으면 레이어 토글 변경 시에도 결과 표시
if 'sim_data' in st.session_state and not use_v7:
    _d = st.session_state['sim_data']
    max_cd=_d['max_cd']; t_arrive=_d['t_arrive']; t_fly=_d['t_fly']
    mc=_d['mc']; min_d=_d['min_d']; all_events=_d['all_events']
    active_events=_d['active_events']; verdicts=_d['verdicts']
    details=_d['details']; sc_results=_d['sc_results']
    dm_eff=_d['dm_eff']; weather_delta=_d['weather_delta']; cd_eff=_d['cd_eff']
    total_cost=_d['total_cost']; global_inv=_d['global_inv']; ch_mgr=_d['ch_mgr']
    ship_status=_d['ship_status']; elapsed=_d['elapsed']; cfg=_d['cfg']

    # ════════════════════════════════════════════════════════════════════
    #  핵심 지표 카드
    # ════════════════════════════════════════════════════════════════════
    ok_cnt  = sum(1 for e in active_events if e.intercepted)
    tot_cnt = len(active_events)
    all_ok  = (ok_cnt == tot_cnt and tot_cnt > 0
               and (not ship_status or ship_status.operational))
    mc_full = float((mc == 1.0).mean() * 100)
    mc_avg  = float(mc.mean() * 100)

    c1,c2,c3,c4,c5 = st.columns(5)
    def _card(col, label, value, color="#3498db"):
        col.markdown(
            f"<div class='metric-card' style='border-color:{color}'>"
            f"<div class='metric-label'>{label}</div>"
            f"<div class='metric-value'>{value}</div></div>",
            unsafe_allow_html=True)

    _card(c1,"최종 결과",
          f"{'✅ 완벽방어' if all_ok else '❌ 피격'}",
          "#27ae60" if all_ok else "#c0392b")
    _card(c2,"요격 성공",f"{ok_cnt}/{tot_cnt}")
    _card(c3,"MC 전탄 성공률",f"{mc_full:.1f}%",
          "#27ae60" if mc_full>=90 else "#e74c3c")
    _card(c4,"총 교전 비용",f"${total_cost:,.0f}")
    _card(c5,"REQ 충족",f"{sum(verdicts)}/{len(verdicts)}")

    st.divider()

    # ════════════════════════════════════════════════════════════════════
    #  탭 구성
    # ════════════════════════════════════════════════════════════════════
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
        ["📡 전술 교전도", "📋 RTM 요구조건", "📜 교전 로그", "📊 MC 통계", "⬇️ 다운로드", "📊 A vs B 비교", "📈 상세 분석"])

    # ── Tab 1: 전술 교전도 ───────────────────────────────────────────────
    with tab1:
        st.markdown("<div class='section-title'>전술 교전도</div>",
                    unsafe_allow_html=True)
        with st.spinner("그래프 생성 중..."):
            try:
                active_evs = [e for e in all_events if e.is_active]
                from import_matplotlib_v6_8_4 import CIRCLE_NUMS
                threat_nums = {ev.uid: CIRCLE_NUMS[i]
                               for i,ev in enumerate(active_evs)
                               if i < len(CIRCLE_NUMS)}
                plt.close('all')
                result = plot_all(
                    cfg, max_cd, t_arrive, t_fly, mc, min_d,
                    all_events, active_events, verdicts, details,
                    sc_results, dm_eff, weather_delta, cd_eff,
                    total_cost, global_inv, ch_mgr,
                    ship_status,
                    show_fleet_positions=show_fleet_positions,
                    show_threat_paths=show_threat_paths,
                    show_radar_range=show_radar_range,
                    show_timeline=show_timeline,
                    show_weapon_range=show_weapon_range,
                    return_fig=True)
                if isinstance(result, tuple):
                    _img_path, _fig = result
                    st.pyplot(_fig, use_container_width=True)
                    plt.close(_fig)
                else:
                    st.info("그래프가 파일로 저장되었습니다.")
            except Exception as e:
                st.warning(f"그래프 생성 오류: {e}")

        # 교전 상황 서술 표
        st.markdown("<div class='section-title'>교전 상황 서술</div>",
                    unsafe_allow_html=True)
        rows = []
        for ev in all_events:
            if not ev.is_active: continue
            cat = ev.enemy_info.get('category','')
            if cat == '어뢰':
                res = "기만/회피 성공" if ev.intercepted else "어뢰 명중"
            elif ev.intercepted and ev.intercept_km is not None:
                res = f"요격 {ev.intercept_km:.1f}km"
            else:
                res = "피격"
            rows.append({
                'ID':    ev.uid,
                '위협명': ev.label[:20],
                '탐지(km)': f"{ev.detect_m/1000:.1f}",
                '사용 무기': (
                    f"{getattr(ev,'assigned_ship','정조대왕함')}\n{ev.intercept_weapon}"
                    if ev.intercept_weapon else '-'
                ),
                '회피 횟수': ev.evasion_count,
                '결과': res,
            })
        if rows:
            df = pd.DataFrame(rows)
            def _color_result(val):
                if '요격' in val or '성공' in val:
                    return 'background-color:#1a4a2e;color:#2ecc71'
                elif '피격' in val or '명중' in val:
                    return 'background-color:#4a1a1a;color:#e74c3c'
                return ''
            st.dataframe(
                df.style.map(_color_result, subset=['결과']),
                use_container_width=True, hide_index=True)

    # ── Tab 6: A vs B 비교 ──────────────────────────────────────────────
    with tab6:
        if not enable_comparison:
            st.info("사이드바에서 'A vs B 비교 활성화'를 켜고 시뮬레이션을 실행하세요.")
        elif 'comparison_results' not in st.session_state:
            st.info("시뮬레이션 실행 버튼을 눌러 비교를 시작하세요.")
        else:
            cmp = st.session_state['comparison_results']
            if cmp.get('A',{}).get('error') or cmp.get('B',{}).get('error'):
                st.error(f"비교 오류: A={cmp.get('A',{}).get('error')} / B={cmp.get('B',{}).get('error')}")
            else:
                ra, rb = cmp['A'], cmp['B']
                st.subheader("📊 시나리오 A vs B 핵심 지표 비교")

                # 비교 카드
                cc1,cc2,cc3,cc4 = st.columns(4)
                def _cmp_card(col, label, va, vb, higher_is_better=True):
                    delta = va - vb
                    a_better = (delta > 0) == higher_is_better
                    col.markdown(
                        f"<div style='background:#1a1a2e;padding:12px;border-radius:8px;text-align:center'>"
                        f"<div style='color:#aaa;font-size:12px'>{label}</div>"
                        f"<div style='color:#3498db;font-size:18px;font-weight:bold'>A: {va:.1f}</div>"
                        f"<div style='color:#e74c3c;font-size:18px;font-weight:bold'>B: {vb:.1f}</div>"
                        f"<div style='color:{'#2ecc71' if a_better else '#e74c3c'};font-size:13px'>"
                        f"{'A 우위 ▲' if a_better else 'B 우위 ▼'} {abs(delta):.1f}</div></div>",
                        unsafe_allow_html=True)
                _cmp_card(cc1, "요격률 (%)",      ra['intercept_rate'], rb['intercept_rate'])
                _cmp_card(cc2, "MC 전탄 성공 (%)", ra['mc_full'],         rb['mc_full'])
                _cmp_card(cc3, "MC 평균 요격 (%)", ra['mc_avg'],          rb['mc_avg'])
                _cmp_card(cc4, "교전 비용 ($M)",   ra['total_cost']/1e6,  rb['total_cost']/1e6, False)

                st.divider()

                # REQ 충족 비교표
                st.subheader("REQ 요구조건 충족 현황")
                req_names = ['REQ-01 탐지거리','REQ-02 C&D시간','REQ-03 1차요격','REQ-04 생존율≥90%','REQ-05 최소탐지']
                req_data = []
                for i, rname in enumerate(req_names):
                    va2 = '✅' if i < len(ra['verdicts']) and ra['verdicts'][i] else '❌'
                    vb2 = '✅' if i < len(rb['verdicts']) and rb['verdicts'][i] else '❌'
                    req_data.append({'요구조건': rname, '시나리오 A': va2, '시나리오 B': vb2})
                import pandas as pd
                st.dataframe(pd.DataFrame(req_data), use_container_width=True, hide_index=True)

                st.divider()

                # 시나리오별 요격 결과 비교
                st.subheader("교전 결과 상세 비교")
                rc1, rc2 = st.columns(2)
                with rc1:
                    st.markdown("**시나리오 A**")
                    a_rows = []
                    for ev in ra['active_events']:
                        res = f"요격 {ev.intercept_km:.1f}km" if ev.intercepted and ev.intercept_km else "피격"
                        a_rows.append({'위협': ev.label[:18], '결과': res,
                                       '무기': (ev.intercept_weapon or '-')})
                    if a_rows:
                        st.dataframe(pd.DataFrame(a_rows), use_container_width=True, hide_index=True)
                with rc2:
                    st.markdown("**시나리오 B**")
                    b_rows = []
                    for ev in rb['active_events']:
                        res = f"요격 {ev.intercept_km:.1f}km" if ev.intercepted and ev.intercept_km else "피격"
                        b_rows.append({'위협': ev.label[:18], '결과': res,
                                       '무기': (ev.intercept_weapon or '-')})
                    if b_rows:
                        st.dataframe(pd.DataFrame(b_rows), use_container_width=True, hide_index=True)


    # ── Tab 7: 📈 상세 분석 (v6.8.1 개편 — 기동전단 관점) ────────────────
    with tab7:
        if 'sim_data' not in st.session_state:
            st.info("시뮬레이션을 먼저 실행하세요.")
        else:
            import matplotlib.pyplot as _plt
            import matplotlib.gridspec as _gs
            import matplotlib.patches as _mpatches
            import numpy as _np
            import pandas as _pd
            import re as _re

            _d        = st.session_state['sim_data']
            _cfg      = _d['cfg']
            _all_e    = _d['all_events']
            _act_e    = _d['active_events']
            _mc       = _d['mc']
            _sc       = _d['sc_results']
            _ginv     = _d['global_inv']
            _cost     = _d['total_cost']
            _ss       = _d['ship_status']
            _is_fleet = _cfg.get('enable_fleet', False) and getattr(_ss,'is_fleet',False)

            # ── ① 편대 생존 현황 (계층 구조) ─────────────────────────
            st.subheader("① 편대 생존 현황")
            if _is_fleet:
                _srs = _ss.ship_results
                _type_order = {'KDX-III': 0, 'KDX-II': 1, 'FFX': 2}
                _type_label = {'KDX-III':'이지스 구축함','KDX-II':'구축함','FFX':'호위함'}
                _type_color = {'KDX-III':'#3498db','KDX-II':'#2ecc71','FFX':'#f39c12'}
                _type_icon  = {'KDX-III':'🛡️','KDX-II':'⚓','FFX':'🚢'}

                # 함종별 그룹화
                _grouped = {}
                for _sr in _srs:
                    _t = _sr['type']
                    _grouped.setdefault(_t, []).append(_sr)

                for _ttype in ['KDX-III','KDX-II','FFX']:
                    if _ttype not in _grouped: continue
                    _tc = _type_color[_ttype]
                    st.markdown(
                        f"<div style='background:linear-gradient(90deg,{_tc}22,transparent);"
                        f"border-left:3px solid {_tc};padding:6px 12px;margin-bottom:4px;"
                        f"border-radius:4px'><b style='color:{_tc}'>"
                        f"{_type_icon[_ttype]} {_type_label[_ttype]}</b></div>",
                        unsafe_allow_html=True)
                    _cols = st.columns(len(_grouped[_ttype]))
                    for _col, _sr in zip(_cols, _grouped[_ttype]):
                        _op = _sr['operational']
                        _bc = '#2ecc71' if _op else '#e74c3c'
                        _col.markdown(
                            f"<div style='background:#1a1a2e;padding:10px;border-radius:8px;"
                            f"border:1.5px solid {_bc};text-align:center;margin:2px'>"
                            f"<div style='color:white;font-weight:bold;font-size:12px'>{_sr['name']}</div>"
                            f"<div style='color:{_bc};font-size:13px;margin:4px 0'>"
                            f"{'✅ 작전중' if _op else '❌ 전투불능'}</div>"
                            f"<div style='color:#aaa;font-size:11px'>피격 {_sr['hit_count']}회</div>"
                            f"<div style='color:#3498db;font-size:11px'>${_sr['cost']/1e6:.1f}M</div>"
                            f"</div>", unsafe_allow_html=True)

                # 전체 생존율 바
                _sv = _ss.survival_rate * 100
                _sc2 = '#2ecc71' if _sv >= 66 else '#f39c12' if _sv >= 33 else '#e74c3c'
                st.markdown(
                    f"<div style='margin-top:8px;background:#111;border-radius:6px;padding:8px'>"
                    f"<div style='color:#aaa;font-size:12px'>편대 생존율</div>"
                    f"<div style='background:#333;border-radius:4px;height:12px;margin-top:4px'>"
                    f"<div style='background:{_sc2};width:{_sv:.0f}%;height:12px;border-radius:4px'></div></div>"
                    f"<div style='color:{_sc2};font-weight:bold'>{_ss.survival_count}/{_ss.ship_count}척  {_sv:.0f}%</div>"
                    f"</div>", unsafe_allow_html=True)
            else:
                _op = _ss.operational if _ss else True
                st.info(f"단독 작전 모드 — 정조대왕함 {'✅ 작전중' if _op else '❌ 전투불능'}")
            st.divider()

            # ── ② MC 통계 강화 ───────────────────────────────────────
            st.subheader("② MC 통계 강화")
            _fig2, _axes2 = _plt.subplots(1, 3, figsize=(15, 4))
            _fig2.patch.set_facecolor('#0e1117')
            for _ax in _axes2: _ax.set_facecolor('#1a1a2e')

            _hits = [1 if e.intercepted else 0 for e in _act_e]
            _labels_t = [f"T{i+1:02d}" for i in range(len(_act_e))]
            _colors_b = ['#2ecc71' if h else '#e74c3c' for h in _hits]
            _axes2[0].bar(_labels_t, _hits, color=_colors_b, edgecolor='white', lw=0.4)
            _axes2[0].set_ylim(0,1.3); _axes2[0].set_yticks([0,1])
            _axes2[0].set_yticklabels(['실패','성공'], color='white')
            _axes2[0].set_title('위협별 요격 결과', color='white', fontsize=10)
            _axes2[0].tick_params(colors='white', labelsize=7)
            for _sp in _axes2[0].spines.values(): _sp.set_color('#444')

            _mc_pct = _mc * 100
            _axes2[1].hist(_mc_pct, bins=20, color='#3498db', edgecolor='#1a1a2e', alpha=0.85)
            _axes2[1].axvline(_mc_pct.mean(), color='#f39c12', lw=2, ls='--', label=f'평균 {_mc_pct.mean():.1f}%')
            _axes2[1].axvline(90, color='#e74c3c', lw=1.5, ls=':', label='기준 90%')
            _axes2[1].set_title('MC 요격률 분포', color='white', fontsize=10)
            _axes2[1].set_xlabel('요격률 (%)', color='white', fontsize=9)
            _axes2[1].tick_params(colors='white', labelsize=8)
            _axes2[1].legend(fontsize=8, labelcolor='white', facecolor='#1a1a2e')
            for _sp in _axes2[1].spines.values(): _sp.set_color('#444')

            _ev_costs = [e.total_cost/1e6 for e in _act_e if e.total_cost > 0]
            if _ev_costs:
                _axes2[2].boxplot(_ev_costs, patch_artist=True,
                    boxprops=dict(facecolor='#8e44ad',alpha=0.7),
                    medianprops=dict(color='#f1c40f',lw=2),
                    whiskerprops=dict(color='white'),
                    capprops=dict(color='white'),
                    flierprops=dict(marker='o',color='#e74c3c',ms=5))
                _axes2[2].set_title('위협당 교전 비용 분포', color='white', fontsize=10)
                _axes2[2].set_ylabel('비용 ($M)', color='white', fontsize=9)
                _axes2[2].tick_params(colors='white', labelsize=8)
            for _sp in _axes2[2].spines.values(): _sp.set_color('#444')

            _plt.tight_layout(); st.pyplot(_fig2); _plt.close(_fig2)
            st.divider()

            # ── ③ 교전 타임라인 ─────────────────────────────────────
            st.subheader("③ 교전 타임라인 (함정별 시퀀스)")
            _fig3, _ax3 = _plt.subplots(figsize=(14, max(3, len(_act_e)*0.6+1)))
            _fig3.patch.set_facecolor('#0e1117'); _ax3.set_facecolor('#1a1a2e')
            _ship_colors = {'정조대왕함':'#3498db','충무공이순신함':'#2ecc71','대구함':'#f39c12',
                            '세종대왕함':'#9b59b6','문무대왕함':'#1abc9c','인천함':'#e67e22'}
            _sorted_evs = sorted(_act_e, key=lambda e: e.spawn_t)
            for _yi, _ev in enumerate(_sorted_evs):
                _t0 = _ev.spawn_t; _t1 = getattr(_ev,'t_impact',_t0+30)
                _ship = getattr(_ev,'assigned_ship','정조대왕함')
                _bc = _ship_colors.get(_ship, '#95a5a6')
                _ax3.barh(_yi, _t1-_t0, left=_t0, height=0.6,
                          color=_bc, alpha=0.7, edgecolor='white', lw=0.3)
                _mark = '★' if _ev.intercepted else '✕'
                _ax3.text(_t1+2, _yi, f"{_mark} {_ev.label[:14]}",
                          va='center', fontsize=7, color='#2ecc71' if _ev.intercepted else '#e74c3c')
                _ax3.text(_t0-2, _yi, _ship[:5], va='center', ha='right',
                          fontsize=6.5, color=_bc)
            _layer_evs = [e for e in _all_e if '[L' in getattr(e,'label','') or 'CEC' in getattr(e,'label','')]
            for _le in _layer_evs:
                _t0l = _le.spawn_t; _t1l = getattr(_le,'t_impact',_t0l+10)
                _ax3.axvspan(_t0l, _t1l, alpha=0.12, color='#f39c12')
            _ax3.set_yticks(range(len(_sorted_evs)))
            _ax3.set_yticklabels([f"T{i+1:02d}" for i in range(len(_sorted_evs))], color='white', fontsize=8)
            _ax3.set_xlabel('시간 (s)', color='white', fontsize=9)
            _ax3.set_title('함정별 교전 시퀀스 타임라인', color='white', fontsize=11)
            _ax3.tick_params(colors='white')
            for _sp in _ax3.spines.values(): _sp.set_color('#444')
            _plt.tight_layout(); st.pyplot(_fig3); _plt.close(_fig3)
            st.divider()

            # ── ④ 비용 분석 (함정별 분담 포함) ─────────────────────
            st.subheader("④ 비용 분석")
            _fig4, (_ax4a, _ax4b, _ax4c) = _plt.subplots(1, 3, figsize=(15, 4))
            _fig4.patch.set_facecolor('#0e1117')
            for _ax in (_ax4a, _ax4b, _ax4c): _ax.set_facecolor('#1a1a2e')

            _wpn_cost = {}
            for _ev in _act_e:
                if _ev.intercept_weapon and _ev.total_cost > 0:
                    _wn = _ev.intercept_weapon.split(' ')[0]
                    _wpn_cost[_wn] = _wpn_cost.get(_wn, 0) + _ev.total_cost
            if _wpn_cost:
                _pc = ['#3498db','#2ecc71','#e74c3c','#f39c12','#9b59b6','#1abc9c','#e67e22']
                _ax4a.pie(list(_v/1e6 for _v in _wpn_cost.values()),
                          labels=list(_wpn_cost.keys()), autopct='%1.0f%%',
                          colors=_pc[:len(_wpn_cost)],
                          textprops={'color':'white','fontsize':9},
                          wedgeprops={'edgecolor':'#1a1a2e','lw':1.5})
            _ax4a.set_title('무기별 비용 구성', color='white', fontsize=10)

            # 함정별 비용 분담 (기동전단 핵심 지표)
            if _is_fleet:
                _ship_cost = {sr['name']: sr['cost'] for sr in _ss.ship_results}
                _snames = list(_ship_cost.keys())
                _scosts = [_ship_cost[s]/1e6 for s in _snames]
                _sc3 = [_type_color.get(
                    next((sr['type'] for sr in _ss.ship_results if sr['name']==s),'KDX-III'),
                    '#95a5a6') for s in _snames]
                _ax4b.bar(_snames, _scosts, color=_sc3, edgecolor='white', lw=0.5)
                _ax4b.set_title('함정별 비용 분담', color='white', fontsize=10)
                _ax4b.set_ylabel('비용 ($M)', color='white', fontsize=9)
                _ax4b.tick_params(colors='white', labelsize=8)
            else:
                _ax4b.text(0.5,0.5,'편대 모드에서 표시됩니다',ha='center',va='center',
                           color='#aaa',transform=_ax4b.transAxes,fontsize=10)
            for _sp in _ax4b.spines.values(): _sp.set_color('#444')

            _tc_data = [(e.label[:12], e.total_cost/1e6) for e in _act_e if e.total_cost>0]
            if _tc_data:
                _tl, _tv = zip(*_tc_data)
                _tc2 = ['#2ecc71' if e.intercepted else '#e74c3c' for e in _act_e if e.total_cost>0]
                _ax4c.barh(_tl, _tv, color=_tc2, edgecolor='white', lw=0.3)
                _ax4c.axvline(sum(_tv)/len(_tv), color='#f39c12', ls='--', lw=1.5,
                               label=f'평균 ${sum(_tv)/len(_tv):.1f}M')
                _ax4c.set_title('위협당 교전 비용', color='white', fontsize=10)
                _ax4c.set_xlabel('비용 ($M)', color='white', fontsize=9)
                _ax4c.tick_params(colors='white', labelsize=7)
                _ax4c.legend(fontsize=8, labelcolor='white', facecolor='#1a1a2e')
            for _sp in _ax4c.spines.values(): _sp.set_color('#444')

            _plt.tight_layout(); st.pyplot(_fig4); _plt.close(_fig4)
            st.divider()

            # ── ⑤ 카테고리별 요격률 ──────────────────────────────────
            st.subheader("⑤ 위협 카테고리별 요격률")
            _cat_stats = {}
            for _ev in _act_e:
                _cat = _ev.enemy_info.get('category','기타')
                _cat_stats.setdefault(_cat, {'total':0,'ok':0,'cost':0})
                _cat_stats[_cat]['total'] += 1
                if _ev.intercepted: _cat_stats[_cat]['ok'] += 1
                _cat_stats[_cat]['cost'] += _ev.total_cost
            if _cat_stats:
                _fig5, (_ax5a,_ax5b) = _plt.subplots(1,2,figsize=(12,4))
                _fig5.patch.set_facecolor('#0e1117')
                for _ax in (_ax5a,_ax5b): _ax.set_facecolor('#1a1a2e')
                _cats = list(_cat_stats.keys())
                _rates = [_cat_stats[c]['ok']/_cat_stats[c]['total']*100 for c in _cats]
                _cat_clrs = {'대공':'#3498db','대함':'#e74c3c','대잠':'#2ecc71','기타':'#95a5a6'}
                _bc5 = [_cat_clrs.get(c,'#95a5a6') for c in _cats]
                _bars5 = _ax5a.bar(_cats, _rates, color=_bc5, edgecolor='white', lw=0.5)
                _ax5a.axhline(90, color='#f39c12', ls='--', lw=1.5, label='기준 90%')
                _ax5a.set_ylim(0,115); _ax5a.set_ylabel('요격률 (%)', color='white', fontsize=9)
                _ax5a.set_title('카테고리별 요격률', color='white', fontsize=10)
                _ax5a.tick_params(colors='white'); _ax5a.legend(fontsize=8,labelcolor='white',facecolor='#1a1a2e')
                for _b,_r,_c in zip(_bars5,_rates,[_cat_stats[c]['total'] for c in _cats]):
                    _ax5a.text(_b.get_x()+_b.get_width()/2, _r+2,
                               f'{_r:.0f}% ({_c}건)', ha='center', color='white', fontsize=9)
                for _sp in _ax5a.spines.values(): _sp.set_color('#444')
                _costs5 = [_cat_stats[c]['cost']/1e6 for c in _cats]
                _ax5b.bar(_cats, _costs5, color=_bc5, edgecolor='white', lw=0.5)
                _ax5b.set_ylabel('총 비용 ($M)', color='white', fontsize=9)
                _ax5b.set_title('카테고리별 총 교전 비용', color='white', fontsize=10)
                _ax5b.tick_params(colors='white')
                for _sp in _ax5b.spines.values(): _sp.set_color('#444')
                _plt.tight_layout(); st.pyplot(_fig5); _plt.close(_fig5)
                _tbl5 = _pd.DataFrame([{'카테고리':c,'위협 수':_cat_stats[c]['total'],
                    '요격 성공':_cat_stats[c]['ok'],
                    '요격률':f"{_cat_stats[c]['ok']/_cat_stats[c]['total']*100:.1f}%",
                    '총 비용':f"${_cat_stats[c]['cost']/1e6:.1f}M"} for c in _cats])
                st.dataframe(_tbl5, use_container_width=True, hide_index=True)
            st.divider()

            # ── ⑥ 채널 포화도 (함정별) ───────────────────────────────
            st.subheader("⑥ 채널 포화도 히트맵")
            if _is_fleet:
                _ship_list = [sr['name'] for sr in _ss.ship_results]
                _n_ships   = len(_ship_list)
                _fig6, _axes6 = _plt.subplots(_n_ships, 1,
                    figsize=(14, 2.0*_n_ships+0.5), squeeze=False)
                _fig6.patch.set_facecolor('#0e1117')
                _t_end6 = max((getattr(e,'t_impact',e.spawn_t+30) for e in _all_e), default=600)
                _n_bins6 = min(60, max(10, int(_t_end6/10)))
                _bins6   = _np.linspace(0, _t_end6, _n_bins6+1)
                _ship_max_ch = {'KDX-III':24,'KDX-II':12,'FFX':8}
                for _si, _sr in enumerate(_ss.ship_results):
                    _ax6 = _axes6[_si][0]; _ax6.set_facecolor('#1a1a2e')
                    _stype = _sr['type']; _max_ch = _ship_max_ch.get(_stype, 8)
                    _ch_cnt = []
                    for _ti in range(_n_bins6):
                        _cnt = sum(1 for e in _all_e
                                   if e.spawn_t <= _bins6[_ti+1]
                                   and getattr(e,'t_impact',e.spawn_t) >= _bins6[_ti]
                                   and e.is_active
                                   and getattr(e,'assigned_ship','') == _sr['name'])
                        _ch_cnt.append(min(_cnt, _max_ch))
                    _im6 = _ax6.imshow([_ch_cnt], aspect='auto', cmap='YlOrRd',
                                        vmin=0, vmax=_max_ch, extent=[0,_t_end6,-0.5,0.5])
                    _ax6.set_yticks([]); _ax6.tick_params(colors='white', labelsize=7)
                    _ax6.set_ylabel(f"{_sr['name'][:5]}/{_max_ch}", color='white', fontsize=8)
                    for _sp in _ax6.spines.values(): _sp.set_color('#444')
                    _plt.colorbar(_im6, ax=_ax6, shrink=0.8)
                _axes6[-1][0].set_xlabel('시간 (s)', color='white', fontsize=9)
                _fig6.suptitle('함정별 채널 포화도', color='white', fontsize=11)
                _plt.tight_layout(); st.pyplot(_fig6); _plt.close(_fig6)
            else:
                _t_end6 = max((getattr(e,'t_impact',e.spawn_t+30) for e in _all_e), default=600)
                _n_bins6 = min(60, max(10, int(_t_end6/10)))
                _bins6   = _np.linspace(0, _t_end6, _n_bins6+1)
                _ch_cnt6 = [sum(1 for e in _all_e
                    if e.spawn_t<=_bins6[i+1] and getattr(e,'t_impact',e.spawn_t)>=_bins6[i]
                    and e.is_active) for i in range(_n_bins6)]
                _fig6s, _ax6s = _plt.subplots(figsize=(14,2.5))
                _fig6s.patch.set_facecolor('#0e1117'); _ax6s.set_facecolor('#1a1a2e')
                _ax6s.imshow([_ch_cnt6], aspect='auto', cmap='YlOrRd', vmin=0, vmax=24,
                              extent=[0,_t_end6,-0.5,0.5])
                _ax6s.set_xlabel('시간 (s)',color='white',fontsize=9); _ax6s.set_yticks([])
                _ax6s.set_title('채널 포화도 히트맵',color='white',fontsize=10)
                _ax6s.tick_params(colors='white')
                _plt.tight_layout(); st.pyplot(_fig6s); _plt.close(_fig6s)
            st.divider()

            # ── ⑧ 편대 함정별 교전 기여도 레이더 ─────────────────────
            if _is_fleet:
                st.subheader("⑧ 편대 함정별 교전 기여도")
                _contrib = {}
                for _ev in _all_e:
                    if not _ev.is_missile:
                        _sn = getattr(_ev,'assigned_ship','정조대왕함')
                        _contrib.setdefault(_sn,{'요격':0,'실패':0,'발사':0,'비용':0,'ch':0})
                        if _ev.is_active:
                            if _ev.intercepted: _contrib[_sn]['요격'] += 1
                            else: _contrib[_sn]['실패'] += 1
                        _contrib[_sn]['비용'] += _ev.total_cost
                if _contrib:
                    _fig8, (_ax8a,_ax8b) = _plt.subplots(1,2,figsize=(13,4))
                    _fig8.patch.set_facecolor('#0e1117')
                    for _ax in (_ax8a,_ax8b): _ax.set_facecolor('#1a1a2e')
                    _snames8 = list(_contrib.keys())
                    _sc8 = ['#3498db','#2ecc71','#f39c12','#e74c3c','#9b59b6','#1abc9c']
                    _ok8 = [_contrib[s]['요격'] for s in _snames8]
                    _fl8 = [_contrib[s]['실패'] for s in _snames8]
                    _x8  = _np.arange(len(_snames8))
                    _ax8a.bar(_x8, _ok8, color='#2ecc71', label='요격', edgecolor='white', lw=0.5)
                    _ax8a.bar(_x8, _fl8, bottom=_ok8, color='#e74c3c', label='실패', edgecolor='white', lw=0.5)
                    _ax8a.set_xticks(_x8); _ax8a.set_xticklabels([s[:6] for s in _snames8],color='white',fontsize=8)
                    _ax8a.set_title('함정별 교전 건수', color='white', fontsize=10)
                    _ax8a.legend(fontsize=8,labelcolor='white',facecolor='#1a1a2e')
                    _ax8a.tick_params(colors='white')
                    for _sp in _ax8a.spines.values(): _sp.set_color('#444')

                    # 기여도 레이더 차트
                    _metrics = ['요격률','비용효율','채널활용','교전건수']
                    _N8 = len(_metrics)
                    _ang8 = _np.linspace(0,2*_np.pi,_N8,endpoint=False).tolist()+[0]
                    _ax8b.remove(); _ax8b = _fig8.add_subplot(122, projection='polar')
                    _ax8b.set_facecolor('#1a1a2e')
                    for _si8, _sn8 in enumerate(_snames8[:4]):
                        _total8 = max(1, _contrib[_sn8]['요격']+_contrib[_sn8]['실패'])
                        _max_ok = max(1, max(c['요격'] for c in _contrib.values()))
                        _max_c  = max(1, max(c['비용'] for c in _contrib.values()))
                        _vals8  = [
                            _contrib[_sn8]['요격']/_total8,
                            1 - _contrib[_sn8]['비용']/_max_c if _max_c>0 else 0,
                            min(1.0, _total8/8),
                            _contrib[_sn8]['요격']/_max_ok,
                        ] + [_contrib[_sn8]['요격']/_total8]
                        _ax8b.plot(_ang8, _vals8, 'o-', lw=2, color=_sc8[_si8],
                                   label=_sn8[:6], markersize=4)
                        _ax8b.fill(_ang8, _vals8, alpha=0.1, color=_sc8[_si8])
                    _ax8b.set_xticks(_ang8[:-1]); _ax8b.set_xticklabels(_metrics,color='white',fontsize=9)
                    _ax8b.set_ylim(0,1); _ax8b.tick_params(colors='white')
                    _ax8b.grid(color='#444',alpha=0.5)
                    _ax8b.legend(loc='upper right',bbox_to_anchor=(1.3,1.1),
                                 fontsize=8,labelcolor='white',facecolor='#1a1a2e',edgecolor='#444')
                    _ax8b.set_title('기여도 레이더', color='white', fontsize=10, pad=15)
                    _plt.tight_layout(); st.pyplot(_fig8); _plt.close(_fig8)
                st.divider()

            # ── ⑨ 재교전 횟수 분포 ──────────────────────────────────
            st.subheader("⑨ 재교전 횟수 분포")
            _reeng = {}
            for _ev in _act_e:
                if not _ev.intercepted: _key='피격'
                else:
                    _rnd=1
                    for _lg in getattr(_ev,'log',[]):
                        _m=_re.search(r'(\d+)차\)',str(_lg.get('msg','')))
                        if _m and 'OK' in str(_lg.get('msg','')): _rnd=int(_m.group(1))
                    _key=f'{_rnd}차 성공'
                _reeng[_key]=_reeng.get(_key,0)+1
            if _reeng:
                _fig9,_ax9=_plt.subplots(figsize=(10,3.5))
                _fig9.patch.set_facecolor('#0e1117'); _ax9.set_facecolor('#1a1a2e')
                _rk=sorted(_reeng.keys(),key=lambda x:(1 if '피격' in x else int(x[0])))
                _rv=[_reeng[k] for k in _rk]
                _rc=['#e74c3c' if '피격' in k else ('#2ecc71' if '1차' in k else
                     '#f39c12' if '2차' in k else '#e67e22') for k in _rk]
                _bars9=_ax9.bar(_rk,_rv,color=_rc,edgecolor='white',lw=0.5)
                for _b,_v in zip(_bars9,_rv):
                    _ax9.text(_b.get_x()+_b.get_width()/2,_v+0.1,str(_v),
                              ha='center',color='white',fontsize=10,fontweight='bold')
                _ax9.set_ylabel('위협 수',color='white',fontsize=9)
                _ax9.set_title('요격까지 교전 횟수 분포',color='white',fontsize=10)
                _ax9.tick_params(colors='white'); _ax9.set_ylim(0,max(_rv)*1.3)
                for _sp in _ax9.spines.values(): _sp.set_color('#444')
                _plt.tight_layout(); st.pyplot(_fig9); _plt.close(_fig9)
                _1st=sum(_reeng.get(f'1차 성공',0) for _ in [1])
                _tot=sum(_v for _k,_v in _reeng.items() if '피격' not in _k)
                if _tot>0: st.caption(f"1차 성공률: {_1st/_tot*100:.1f}% ({_1st}/{_tot}건)")
            st.divider()

            # ── 신규 A: 다층 방어 흐름도 ──────────────────────────────
            st.subheader("🔄 다층 방어 흐름 분석")
            _layer_evs_a = [e for e in _all_e if
                            '[L' in getattr(e,'label','') or 'CEC' in getattr(e,'label','')]
            _primary_fail = sum(1 for e in _act_e if not e.is_missile
                                and not e.intercepted
                                and not any(getattr(le,'intercepted',False)
                                            for le in _layer_evs_a
                                            if getattr(le,'label','').startswith(e.label[:8])))
            _layer_intercept = sum(1 for e in _layer_evs_a if e.intercepted)
            _primary_ok  = sum(1 for e in _act_e if e.intercepted and not e.is_missile
                               and not any(e.label[:8] in getattr(le,'label','')
                                           for le in _layer_evs_a))

            _la1, _la2, _la3 = st.columns(3)
            _la1.metric("1차 요격 성공", f"{_primary_ok}건", delta=f"{_primary_ok/max(1,len([e for e in _act_e if not e.is_missile]))*100:.0f}%")
            _la2.metric("다층 방어 인계", f"{len(_layer_evs_a)}건", delta=f"성공 {_layer_intercept}건")
            _la3.metric("최종 방어 실패", f"{sum(1 for e in _act_e if not e.intercepted and not e.is_missile)}건")

            if _layer_evs_a:
                st.caption("다층 방어 발동 이벤트")
                _ltbl = _pd.DataFrame([{
                    '이벤트': e.label[:25],
                    '담당 함정': getattr(e,'assigned_ship','-'),
                    '결과': '요격 ✅' if e.intercepted else '실패 ❌',
                    '무기': e.intercept_weapon or '-'
                } for e in _layer_evs_a])
                st.dataframe(_ltbl, use_container_width=True, hide_index=True)
            else:
                st.info("이 시나리오에서는 다층 방어 인계가 발생하지 않았습니다.")
            st.divider()

            # ── 신규 C: 편대 재고 소모 추이 ──────────────────────────
            st.subheader("📦 편대 재고 소모 현황")
            _key_wpns = ['SM-3 Block IIA','SM-6','SM-2 Block IIIB','RIM-116 RAM','홍상어 (대잠)','청상어 (경어뢰)']
            if _cfg.get('enable_fleet', False):
                from import_matplotlib_v6_8_4 import build_fleet as _bf, SHIP_DB as _SDB
                _tmp = _bf(_cfg)
                _init_inv = _tmp.global_inventory_summary()
            else:
                _init_inv = _cfg.get('inventory', {})
            _wpn_rows = []
            for _wk in _key_wpns:
                _ini = _init_inv.get(_wk, 0)
                _rem = _ginv.get(_wk, 0)
                _used = _ini - _rem
                if _ini == 0: continue
                _pct = _used / _ini * 100 if _ini > 0 else 0
                _warn = '⚠️' if _pct >= 70 else '🟡' if _pct >= 40 else '🟢'
                _wpn_rows.append({'무기':_wk,'초기':_ini,'잔여':_rem,
                                   '사용':_used,'소모율':f"{_pct:.0f}%",'상태':_warn})
            if _wpn_rows:
                _fig_c, _ax_c = _plt.subplots(figsize=(12,4))
                _fig_c.patch.set_facecolor('#0e1117'); _ax_c.set_facecolor('#1a1a2e')
                _wnames_c = [r['무기'].split(' ')[0] for r in _wpn_rows]
                _ini_c    = [r['초기'] for r in _wpn_rows]
                _rem_c    = [r['잔여'] for r in _wpn_rows]
                _used_c   = [r['사용'] for r in _wpn_rows]
                _x_c      = _np.arange(len(_wnames_c))
                _ax_c.bar(_x_c, _ini_c, color='#2c3e50', edgecolor='#444', lw=0.5, label='초기')
                _ax_c.bar(_x_c, _used_c, color='#e74c3c', edgecolor='white', lw=0.5, alpha=0.8, label='사용')
                _ax_c.bar(_x_c, _rem_c, bottom=_used_c, color='#2ecc71', edgecolor='white', lw=0.5, alpha=0.8, label='잔여')
                for _xi, (_u,_r) in enumerate(zip(_used_c,_rem_c)):
                    if _u > 0:
                        _ax_c.text(_xi, _u+_r+0.3, f'-{_u}', ha='center', color='#e74c3c', fontsize=9)
                _ax_c.set_xticks(_x_c); _ax_c.set_xticklabels(_wnames_c, color='white', fontsize=9)
                _ax_c.set_ylabel('발수', color='white', fontsize=9)
                _ax_c.set_title('주요 무기 재고 소모 현황', color='white', fontsize=11)
                _ax_c.legend(fontsize=8,labelcolor='white',facecolor='#1a1a2e')
                _ax_c.tick_params(colors='white')
                for _sp in _ax_c.spines.values(): _sp.set_color('#444')
                _plt.tight_layout(); st.pyplot(_fig_c); _plt.close(_fig_c)
                st.dataframe(_pd.DataFrame(_wpn_rows), use_container_width=True, hide_index=True)

            # ── ⑩ 날씨별 성능 레이더 차트 ──────────────────────────
            st.divider()
            st.subheader("⑩ 날씨별 성능 레이더 차트")
            if _sc:
                _fig10 = _plt.figure(figsize=(10,4.5))
                _fig10.patch.set_facecolor('#0e1117')
                _ax10  = _fig10.add_subplot(111, projection='polar')
                _ax10.set_facecolor('#1a1a2e')
                _metrics10 = ['평균 요격률','전탄 성공률','안정성(1-σ)']
                _ang10 = _np.linspace(0,2*_np.pi,3,endpoint=False).tolist()+[0]
                _wc10 = {'최선(맑음)':'#3498db','평균(흐림)':'#f39c12','최악(폭풍)':'#e74c3c'}
                for _wk10,_wv10 in _sc.items():
                    _arr10 = _np.asarray(_wv10['mc_array'] if isinstance(_wv10,dict) else _wv10,dtype=float)
                    _v10 = [float(_arr10.mean()),float((_arr10==1.0).mean()),
                            max(0,1-float(_arr10.std())*2)] + [float(_arr10.mean())]
                    _ax10.plot(_ang10,_v10,'o-',lw=2,color=_wc10.get(_wk10,'#95a5a6'),
                               label=f"{_wk10} ({float(_arr10.mean())*100:.1f}%)",markersize=5)
                    _ax10.fill(_ang10,_v10,alpha=0.1,color=_wc10.get(_wk10,'#95a5a6'))
                _ax10.set_xticks(_ang10[:-1]); _ax10.set_xticklabels(_metrics10,color='white',fontsize=9)
                _ax10.set_ylim(0,1); _ax10.tick_params(colors='white')
                _ax10.grid(color='#444',alpha=0.5)
                _ax10.legend(loc='upper right',bbox_to_anchor=(1.35,1.1),
                             fontsize=9,labelcolor='white',facecolor='#1a1a2e',edgecolor='#444')
                _ax10.set_title('날씨별 방어 성능 레이더',color='white',fontsize=11,pad=15)
                _plt.tight_layout(); st.pyplot(_fig10); _plt.close(_fig10)

    # ── Tab 2: RTM ───────────────────────────────────────────────────────
    with tab2:
        st.markdown("<div class='section-title'>RTM 요구조건 추적표</div>",
                    unsafe_allow_html=True)
        rtm_rows = []
        for req, v, d in zip(REQ_ITEMS, verdicts, details):
            rtm_rows.append({
                'ID':     req['id'],
                '요구조건': req['name'],
                '검증 기준': req['desc'][:40],
                '판정':   '✅ PASS' if v else '❌ FAIL',
                '상세':   d,
            })
        df_rtm = pd.DataFrame(rtm_rows)
        def _color_pass(val):
            if 'PASS' in val: return 'color:#2ecc71;font-weight:700'
            if 'FAIL' in val: return 'color:#e74c3c;font-weight:700'
            return ''
        st.dataframe(
            df_rtm.style.map(_color_pass, subset=['판정']),
            use_container_width=True, hide_index=True)

        st.markdown(f"**전체: {sum(verdicts)}/{len(verdicts)} 충족**")

        # 날씨별 비교
        st.markdown("<div class='section-title'>날씨별 시나리오 비교 (각 300회)</div>",
                    unsafe_allow_html=True)
        sc_rows = []
        for lbl, res in sc_results.items():
            sc_rows.append({
                '시나리오': lbl,
                '평균 성공률': f"{res['mean']:.1f}%",
                '전탄 성공률': f"{res['full_pass']:.1f}%",
                '판정': '✅ PASS' if res['full_pass']>=90 else '❌ FAIL',
            })
        st.dataframe(pd.DataFrame(sc_rows).style.map(
            _color_pass, subset=['판정']),
            use_container_width=True, hide_index=True)

    # ── Tab 3: 교전 로그 ─────────────────────────────────────────────────
    with tab3:
        st.markdown("<div class='section-title'>타임라인 교전 로그</div>",
                    unsafe_allow_html=True)
        all_logs = sorted(
            [e for ev in all_events for e in ev.log],
            key=lambda x: x['t'])

        log_rows = []
        for e in all_logs:
            log_rows.append({
                '시각(s)': f"{e['t']:.0f}",
                'ID':      e.get('uid',''),
                '위협명':  e.get('label','')[:18],
                '아이콘':  e.get('icon',''),
                '메시지':  e.get('msg',''),
            })
        if log_rows:
            df_log = pd.DataFrame(log_rows)
            # 필터
            filter_col1, filter_col2 = st.columns([2,3])
            with filter_col1:
                keyword = st.text_input("메시지 필터 (빈칸=전체)", "")
            with filter_col2:
                uid_filter = st.multiselect(
                    "위협 ID 필터",
                    options=df_log['ID'].unique().tolist(),
                    default=[])
            if keyword:
                df_log = df_log[df_log['메시지'].str.contains(keyword, na=False)]
            if uid_filter:
                df_log = df_log[df_log['ID'].isin(uid_filter)]

            def _color_log(val):
                if 'OK' in val or '성공' in val: return 'color:#2ecc71'
                if 'NG' in val or '피격' in val or '명중' in val: return 'color:#e74c3c'
                if 'ECM' in val or 'CIWS' in val or '자체방어' in val: return 'color:#f39c12'
                if '헬기' in val or '출격' in val or 'P-3C' in val: return 'color:#3498db'
                return ''
            st.dataframe(
                df_log.style.map(_color_log, subset=['메시지']),
                use_container_width=True, hide_index=True, height=500)
            st.caption(f"총 {len(df_log)} / {len(log_rows)} 항목 표시")

    # ── Tab 4: MC 통계 ───────────────────────────────────────────────────
    with tab4:
        st.markdown("<div class='section-title'>몬테카를로 통계 (1000회)</div>",
                    unsafe_allow_html=True)

        cc1, cc2, cc3, cc4 = st.columns(4)
        _card(cc1,"전탄 성공률",f"{mc_full:.1f}%",
              "#27ae60" if mc_full>=90 else "#e74c3c")
        _card(cc2,"평균 성공률",f"{mc_avg:.1f}%")
        _card(cc3,"표준편차",f"{mc.std()*100:.1f}%p")
        _card(cc4,"평균 피격 횟수",
              f"{getattr(mc,'mc_hit_avg',0):.2f}회")

        # 히스토그램
        fig_mc, ax_mc = plt.subplots(figsize=(10,4), facecolor='#1a2332')
        ax_mc.set_facecolor('#1a2332')
        ax_mc.hist(mc*100, bins=20, color='#3498db', edgecolor='#1a2332',
                   alpha=0.85, rwidth=0.9)
        ax_mc.axvline(90, color='#e74c3c', lw=2, ls='--', label='90% 기준선')
        ax_mc.axvline(mc_avg, color='#2ecc71', lw=2, ls='-',
                      label=f'평균 {mc_avg:.1f}%')
        ax_mc.set_xlabel('요격 성공률 (%)', color='white')
        ax_mc.set_ylabel('빈도', color='white')
        ax_mc.tick_params(colors='white')
        ax_mc.legend(facecolor='#2c3e50', labelcolor='white')
        ax_mc.set_title('MC 1000회 요격 성공률 분포', color='white')
        for spine in ax_mc.spines.values():
            spine.set_edgecolor('#2c3e50')
        st.pyplot(fig_mc, use_container_width=True)
        plt.close(fig_mc)

        # 분위수 표
        pct_rows = [
            {'분위': '10%', '값': f"{float(np.percentile(mc,10)*100):.1f}%"},
            {'분위': '25%', '값': f"{float(np.percentile(mc,25)*100):.1f}%"},
            {'분위': '50%', '값': f"{float(np.percentile(mc,50)*100):.1f}%"},
            {'분위': '75%', '값': f"{float(np.percentile(mc,75)*100):.1f}%"},
            {'분위': '90%', '값': f"{float(np.percentile(mc,90)*100):.1f}%"},
        ]
        st.dataframe(pd.DataFrame(pct_rows), use_container_width=True,
                     hide_index=True)

        # MC 샘플 로그 (save_nth > 0 시)
        mc_logs = getattr(mc, 'mc_sample_logs', [])
        if mc_logs:
            st.markdown(f"<div class='section-title'>MC 샘플 로그 ({mc_save_nth}회차)</div>",
                        unsafe_allow_html=True)
            sl_rows = [{'시각(s)':f"{e['t']:.0f}",'위협':e.get('label','')[:16],
                        '아이콘':e.get('icon',''),'메시지':e.get('msg','')}
                       for e in mc_logs[:200]]
            st.dataframe(pd.DataFrame(sl_rows), use_container_width=True,
                         hide_index=True, height=400)

    # ── Tab 5: 다운로드 ──────────────────────────────────────────────────
    with tab5:
        st.markdown("<div class='section-title'>보고서 다운로드</div>",
                    unsafe_allow_html=True)

        # XLSX 생성 (메모리)
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            if st.button("📄 엑셀 보고서 생성", use_container_width=True):
                with st.spinner("엑셀 보고서 생성 중..."):
                    try:
                        xlsx_path = '이지스_기동전단_요구조건_보고서_v6_8_4.xlsx'
                        img_path  = '이지스_기동전단_요구조건_분석_v6_8_4.png'
                        save_excel_report(
                            cfg, max_cd, mc, min_d, verdicts, details,
                            sc_results, dm_eff, weather_delta, cd_eff,
                            total_cost, global_inv, ch_mgr,
                            all_events, img_path,
                            ship_status)
                        with open(xlsx_path,'rb') as f:
                            st.download_button(
                                "⬇️ XLSX 다운로드",
                                data=f.read(),
                                file_name=xlsx_path,
                                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                                use_container_width=True)
                    except Exception as e:
                        st.error(f"엑셀 생성 오류: {e}")

        with col_d2:
            # PNG 다운로드
            img_path = '정조대왕급_요구조건_분석_v6_2.png'
            if os.path.exists(img_path):
                with open(img_path,'rb') as f:
                    st.download_button(
                        "⬇️ PNG 그래프 다운로드",
                        data=f.read(),
                        file_name=img_path,
                        mime='image/png',
                        use_container_width=True)

        # 무기 재고 현황
        st.markdown("<div class='section-title'>무기 재고 현황</div>",
                    unsafe_allow_html=True)
        inv_rows = []
        for wn, ini in cfg['inventory'].items():
            if wn == 'CIWS-II (Phalanx)': continue
            used = ini - global_inv.get(wn, 0)
            remaining = global_inv.get(wn, ini)
            inv_rows.append({
                '무기명': wn,
                '초기': ini,
                '사용': used,
                '잔여': remaining,
                '상태': '🟡 소진 중' if remaining == 0 else '🟢 보유 중',
            })
        st.dataframe(pd.DataFrame(inv_rows), use_container_width=True,
                     hide_index=True)

        # 항공 통계
        # NEW-K: 편대 모드 생존 현황
        if enable_fleet and getattr(ship_status, 'is_fleet', False):
            st.subheader("🚢 편대 생존 현황")
            cols_fleet = st.columns(len(ship_status.ship_results))
            for col, sr_info in zip(cols_fleet, ship_status.ship_results):
                with col:
                    icon = "✅" if sr_info['operational'] else "❌"
                    st.metric(
                        label=f"{icon} {sr_info['name']}",
                        value="작전중" if sr_info['operational'] else "전투불능",
                        delta=f"{sr_info['type']} | 피격:{sr_info['hit_count']}회"
                    )
            st.info(f"편대 생존율: **{ship_status.survival_count}/{ship_status.ship_count}척** "
                    f"({ship_status.survival_rate*100:.0f}%)")

        if enable_helo or enable_p3c or enable_p8a:
            st.markdown("<div class='section-title'>항공 작전 통계</div>",
                        unsafe_allow_html=True)
            st.info(
                f"🚁 헬기 출격: **{ship_status.helo_sorties}회** | "
                f"요격 성공: **{ship_status.helo_intercepts}회**")

elif not use_v7:
    # ── 초기 화면 (실행 전, v6) ─────────────────────────────────────────
    st.info("👈 왼쪽 사이드바에서 파라미터를 설정한 뒤 **🚀 시뮬레이션 실행** 버튼을 누르세요.")
elif 'v7_sim_data' not in st.session_state:
    # ── 초기 화면 (실행 전, v7) ─────────────────────────────────────────
    st.info("👈 상단 **[v7]** 섹션에서 편대·적군·무기 재고를 설정한 뒤 **🚀 v7 시뮬레이션 실행** 버튼을 누르세요.")

    cinfo1, cinfo2, cinfo3 = st.columns(3)
    with cinfo1:
        st.markdown("""
        **🔴 적군 위협 32종**
        - 대공: 전투기·폭격기·탄도·순항미사일
        - 대함: 수상함 5종
        - 대잠: 잠수함 5종
        - HGV(DF-17) / QBM(KN-23) 특수처리
        """)
    with cinfo2:
        st.markdown("""
        **⚙️ 신규 기능 (v6.5)**
        - NEW-G: ECM 거리 반비례 재밍
        - NEW-H: AW-159 와일드캣 함재 헬기
        - NEW-I: P-3C 오라이온 해상초계기
        - NEW-K: 다중 함정 편대 엔진
        - NEW-L: 적군 편대 + 아군 커스텀
        - NEW-M: 시나리오 저장/불러오기 + 전술교전도 레이어
        - NEW-J: P-8A 포세이돈 해상초계기
        """)
    with cinfo3:
        st.markdown("""
        **📊 분석 출력**
        - Monte Carlo 1000회 통계
        - RTM 요구조건 8항목 판정
        - 날씨별 3종 시나리오 비교
        - 엑셀 9시트 + PNG 다운로드
        """)

# ── 5단계 패치 (dashboard.py) ─────────────────────────────────────────────────
# · NEW-A: 사이드바 상단 엔진 선택 라디오 (v6 이벤트 기반 / v7 시간스텝 양방향)
# · NEW-B: v7 전용 설정 패널 — 적군 편대·아군 편대·공격 무기 재고·MC 횟수
# · NEW-C: run_btn use_v7 분기 — run_v7_simulation() + monte_carlo_v7() 실행
# · NEW-D: 전장 애니메이션 탭 — SimFrame 슬라이더로 함정·미사일 위치 재생
# · NEW-E: MC 통계 / 교전 로그 / Excel·PNG 다운로드 탭 (v7 전용)