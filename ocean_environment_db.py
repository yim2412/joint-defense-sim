"""
한반도 주변 해양 환경 데이터베이스
Korean Peninsula Maritime Environment Database

출처 (Sources):
  [1] Teague et al. (2006) "Korea/Tsushima Strait" — Oceanography 19(3)
      https://tos.org/oceanography/assets/docs/19-3_teague.pdf
  [2] Shin et al. (2022) "Long-term variation in volume transport of TWC"
      https://www.sciencedirect.com/science/article/abs/pii/S0924796322000513
  [3] Kim et al. (2023) "Intensified EKWC summer 2021"
      https://www.frontiersin.org/journals/marine-science/articles/10.3389/fmars.2023.1252302/full
  [4] Wikipedia / NOAA — North Korea Cold Current
      https://en.wikipedia.org/wiki/North_Korea_Cold_Current
  [5] He et al. (2008) "Yellow Sea Warm Current seasonal variability"
      https://link.springer.com/article/10.1016/S1001-6058(08)60133-X
  [6] Blain (2001) "Seasonal mean circulation in the Yellow Sea"
      https://www7320.nrlssc.navy.mil/pubs/2001/blain-2001.pdf
  [7] Park et al. (2024) "West Korea Coastal Current summer observation"
      https://link.springer.com/article/10.1007/s12601-024-00176-9
  [8] Kim (2008) "Seasonal/Interannual variability of NKCC" — Ocean and Polar Research
      https://koreascience.kr/article/JAKO200827651796020.page
  [9] Universal Encyclopaedia "Yellow Sea" tidal range
      https://universalium.en-academic.com/234739/Yellow_Sea
 [10] ScienceDirect "Tidal current simulation Korea Strait"
      https://www.sciencedirect.com/science/article/pii/S2092678218300128
 [11] oceanclimate.kr — 유의파고 분석정보 (2026)
      https://oceanclimate.kr/swh/
 [12] KMA 기상자료개방포털 — 안개일수 통계
      https://data.kma.go.kr/climate/fog/selectFogChart.do
 [13] Wikipedia "Typhoons in the Korean Peninsula"
      https://en.wikipedia.org/wiki/Typhoons_in_the_Korean_Peninsula
 [14] Wenz (1962) / Dahl (2010) "Underwater Ambient Noise" — IntechOpen
      https://www.intechopen.com/chapters/72750
 [15] MathWorks "Maritime Radar Sea Clutter Modeling"
      https://www.mathworks.com/help/radar/ug/maritime-radar-sea-clutter-modeling.html
 [16] FLIR — Thermal imaging fog penetration
      https://www.flir.com/discover/rd-science/can-thermal-imaging-see-through-fog-and-rain/
 [17] KMA 해양기상기후정보포털
      https://www.weather.go.kr/marine/marine_08/pdf/data_202605.pdf
"""

# =============================================================================
# 1. 해류 데이터 (Ocean Currents)
# =============================================================================

OCEAN_CURRENTS = {

    # ── 대마난류 (Tsushima Warm Current, TWC) ──────────────────────────────
    # 쿠로시오 분지. 대한해협을 통해 동해로 유입되는 한반도 주변 주요 난류.
    # 출처: [1][2]
    "tsushima_warm_current": {
        "name_ko": "대마난류",
        "name_en": "Tsushima Warm Current (TWC)",
        "origin": "쿠로시오 분지 (동중국해 경유)",
        "direction": "남서→북동 (대한해협 통과 후 동해 북상)",

        # 연평균 수송량 (1997-2013 ADCP 17년 관측) [2]
        "annual_mean_transport_Sv": 2.64,
        "transport_std_Sv": 0.41,

        # 계절별 수송량 Sv [2]
        "transport_by_month_Sv": {
            "Jan": 1.74,  # 연중 최소
            "Feb": 1.85,
            "Mar": 2.10,
            "Apr": 2.50,
            "May": 2.80,
            "Jun": 2.90,
            "Jul": 3.00,
            "Aug": 3.05,
            "Sep": 3.00,
            "Oct": 3.10,  # 연중 최대
            "Nov": 2.70,
            "Dec": 2.00,
        },

        # 대한해협 동·서수도 분류 [2]
        "western_channel_fraction": 0.58,   # 서수도 58%
        "eastern_channel_fraction": 0.42,   # 동수도 42%
        "western_channel_transport_Sv": 1.53,
        "eastern_channel_transport_Sv": 1.11,

        # 유속 [1][2]
        "max_speed_cms": 50,        # 최대 50 cm/s 초과 (대한해협 내)
        "typical_speed_cms": 20,    # 전형적 유속 20-30 cm/s

        # 저층 냉수 (Korea Strait Bottom Cold Water) [1]
        "bottom_cold_water_mean_speed_cms": 24,
        "bottom_cold_water_temp_threshold_C": 8,  # 수온 8-10℃ 이하

        # 해협 통과 후 동해에서 두 갈래로 분리
        "branches": ["동한난류 (EKWC)", "쓰시마 방향 동행류"],
    },

    # ── 동한난류 (East Korea Warm Current, EKWC) ──────────────────────────
    # 대마난류의 동쪽 분지. 한국 동해안을 따라 북상.
    # 출처: [3]
    "east_korea_warm_current": {
        "name_ko": "동한난류",
        "name_en": "East Korea Warm Current (EKWC)",
        "origin": "대마난류 동지류",
        "direction": "남→북 (동해안 연안 북상, 약 37-40°N에서 동쪽으로 이탈)",

        # 유속 — 기후학적 평균 [3]
        "climatological_speed_cms": 50,     # 여름 평균 ~50 cm/s
        "max_observed_speed_cms": 116,       # 2021년 8월 1일 관측 최대값
        "max_instantaneous_cms": 189,        # 순간 최대 (계류 관측)

        # 계절별 유속 [3]
        "speed_by_season_cms": {
            "spring": 30,
            "summer": 50,   # 여름에 최강
            "autumn": 35,
            "winter": 20,
        },

        # 위치 [3]
        "latitude_range_deg_N": (36.3, 40.0),
        "separation_latitude_deg_N": (37, 38),  # 북한한류와 만나 이탈
        "peak_velocity_longitude_deg_E": 129.6,
    },

    # ── 북한한류 (North Korea Cold Current, NKCC) ─────────────────────────
    # 오호츠크해 → 라만(Liman)류 분지. 동해안을 따라 남하.
    # 출처: [4][8]
    "north_korea_cold_current": {
        "name_ko": "북한한류",
        "name_en": "North Korea Cold Current (NKCC)",
        "origin": "오호츠크해 라만류(Liman Current) 분지, 블라디보스톡 인근",
        "direction": "북→남 (동해안 연안 남하)",

        # 유속 [4]
        "typical_speed_knots": 0.5,     # 약 0.5 knot (~26 cm/s)
        "typical_speed_cms": 26,

        # 수송량 — 계절 변화 [8]
        "transport_seasonal_Sv": {
            "winter_min": 0.45,   # 12-1월 최소
            "summer_max": 0.80,   # 8-9월 최대
        },
        "interannual_variation_Sv": 1.0,  # 계절 변화보다 큼

        # 형태 [8]
        "width_km": 35,                  # 동해안 인근 폭 ~35km
        "position": "동한난류 하층에 위치",

        # 경계 [4][8]
        "meets_ekwc_lat_deg_N": (37, 38),   # 동한난류와 조우 → 육지 이탈
        "meets_twc_lat_deg_N": 40,           # 대마난류와 경계
    },

    # ── 황해난류 (Yellow Sea Warm Current, YSWC) ──────────────────────────
    # 서해(황해) 중앙 해저 계곡을 따라 북상하는 겨울 난류.
    # 출처: [5][6]
    "yellow_sea_warm_current": {
        "name_ko": "황해난류",
        "name_en": "Yellow Sea Warm Current (YSWC)",
        "origin": "쿠로시오 분지 (동중국해 북부)",
        "direction": "남→북 (황해 중앙 해저곡 50-70m 등수심선 따라)",

        # 유속 [5][6]
        "typical_speed_cms": 10,        # 평균 ~10 cm/s
        "max_speed_cms": 25,            # 발원부 최대
        "trough_speed_cms": 5,          # 해저곡 구간 ~5 cm/s

        # 계절성 [5][6]
        "seasonality": {
            "winter": "겨울 강화 — 황해 심부까지 북상 (강한 북풍 몬순에 의해 유발)",
            "summer": "여름 약화 — 남부 해저곡에만 한정, 존재감 미약",
        },

        # 경로 [5]
        "path": "황해 해저곡 50-70m 등수심선, 보하이(渤海)까지 연장",
    },

    # ── 황해 연안류 (West Korea Coastal Current) ─────────────────────────
    # 황해 동측 한국 연안을 따라 흐르는 연안류. 계절 반전.
    # 출처: [7]
    "west_korea_coastal_current": {
        "name_ko": "서한연안류 / 황해 동연안류",
        "name_en": "West Korea Coastal Current",
        "direction_summer": "남→북 (5-8월 북상)",
        "direction_winter": "북→남 (9월-4월 남하)",

        # 유속 [7]
        "speed_cms_may_jun": (6.4, 8.6),    # 연안 관측소 월평균
        "speed_cms_jul_aug": 11.4,           # 7-8월 연안 최대
        "offshore_speed_cms": (3, 5),        # 외해 측

        # 특성
        "driving_force": "계절풍(몬순) — 겨울 북풍 시 남향, 여름 남풍 시 북향",
    },
}


# =============================================================================
# 2. 조류 데이터 (Tidal Currents)
# =============================================================================

TIDAL_DATA = {

    # ── 서해 조수간만차 ──────────────────────────────────────────────────────
    # 출처: [9], tide-forecast.com, 국립해양조사원
    "west_sea_tidal_range": {
        "description": "서해(황해) 주요 항구 조수간만차",
        "locations": {
            "인천": {
                "spring_tide_range_m": 9.0,   # 최대 대조차 ~9m [9]
                "mean_spring_range_m": 7.9,
                "mean_neap_range_m":  3.0,
                "note": "세계 최대급 조수간만차 지역",
            },
            "군산": {
                "spring_tide_range_m": 6.5,
                "mean_spring_range_m": 5.7,
                "mean_neap_range_m":  2.5,
            },
            "목포": {
                "spring_tide_range_m": 4.2,
                "mean_spring_range_m": 3.5,
                "mean_neap_range_m":  1.5,
            },
            "평택": {
                "spring_tide_range_m": 7.5,
                "mean_spring_range_m": 6.5,
                "mean_neap_range_m":  2.8,
                "note": "인천과 유사, 북부 서해 대조차",
            },
        },
    },

    # ── 서해 최대 조류 속도 ─────────────────────────────────────────────────
    # 출처: [9]
    "west_sea_tidal_current": {
        "open_sea_speed_ms":  0.41,       # 외해 중앙부 ~1 knot = 0.51 m/s 이하
        "open_sea_speed_knots": 0.8,
        "coastal_strait_max_ms": 1.8,     # 연안·해협 최대 ~3.5 mph = 1.8 m/s [9]
        "coastal_strait_max_knots": 3.5,
        "note": "조류 방향은 해저 지형에 평행 (타원 장축이 등수심선 방향)",
    },

    # ── 대한해협 조류 ────────────────────────────────────────────────────────
    # 출처: [1][10]
    "korea_strait_tidal_current": {
        "description": "대한해협 동·서수도 조류 특성",
        "west_channel": {
            "spring_tide_max_knots": 1.5,   # 대조기 최대 1-1.5 knot [10]
            "neap_tide_max_knots": 0.5,
            "summer_max_knots": 3.0,         # 하계 최대 3 knot [10]
            "spring_tide_max_ms": 0.77,
            "summer_max_ms": 1.54,
            "dominant_direction": "북동-남서",
            "note": "동수도보다 조류 강함 (지형적 협착)",
        },
        "east_channel": {
            "spring_tide_max_knots": 1.0,
            "neap_tide_max_knots": 0.5,
            "spring_tide_max_ms": 0.51,
            "dominant_direction": "북동-남서",
        },
        "general": {
            "spring_tide_range_m": 1.5,     # 대한해협 대조차 (~1.5m 소규모)
            "tidal_period_hr": 12.4,        # 반일주조 우세
        },
    },

    # ── 동해 조수간만차 ──────────────────────────────────────────────────────
    # 출처: [1], 국립해양조사원
    "east_sea_tidal_range": {
        "description": "동해는 서해에 비해 조수간만차 극소",
        "mean_range_m": 0.3,     # 전형적 30cm
        "max_range_m": 0.5,      # 최대 50cm (부산·울산 인근)
        "note": "반폐쇄 내해로 조석 에너지 매우 약함. 해류·파도 영향이 지배적.",
    },

    # ── 조류가 기뢰·어뢰 표류에 미치는 영향 ────────────────────────────────
    "drift_effects": {
        "description": "조류 / 해류에 의한 수중 물체 표류 추산",

        # 표류 속도 = 조류 속도 × drift_factor (수중 저항 고려)
        "mine_drift_factor": 0.8,       # 계류 기뢰 표류: 조류 속도의 ~80%
        "torpedo_drift_factor": 0.6,    # 어뢰(수중 정지 상태): 조류의 ~60%

        # 서해 대조기 기뢰 표류 예시
        "west_sea_spring_mine_drift_ms": 1.44,   # 1.8 × 0.8
        "korea_strait_mine_drift_ms":    0.62,   # 서수도 0.77 × 0.8
        "east_sea_mine_drift_ms":        0.04,   # 0.05 × 0.8 (조류 미약)

        # 24시간 표류 거리 (nm)
        "west_sea_24h_drift_nm": 37,     # 1.44 m/s × 86400 s ÷ 1852
        "korea_strait_24h_drift_nm": 16,
        "east_sea_24h_drift_nm": 1,
    },
}


# =============================================================================
# 3. 해역별 기상 통계 (Weather Statistics by Sea Area)
# =============================================================================

# ── 유의파고 (Significant Wave Height, Hs) ────────────────────────────────
# 출처: [11] oceanclimate.kr (1981-2026 ERA5 기반 분석)
# 단위: m

WAVE_STATISTICS = {

    "east_sea": {
        "name_ko": "동해",
        "hs_monthly_m": {
            # 월별 평균 유의파고 (ERA5 재분석 기반)
            "Jan": 2.3,  "Feb": 2.1,  "Mar": 1.9,  "Apr": 1.5,
            "May": 1.3,  "Jun": 1.1,  "Jul": 1.2,  "Aug": 1.3,
            "Sep": 1.5,  "Oct": 1.8,  "Nov": 2.0,  "Dec": 2.3,
        },
        "hs_seasonal_m": {
            "winter": 2.2,   # DJF
            "spring": 1.6,   # MAM
            "summer": 1.2,   # JJA
            "autumn": 1.8,   # SON
        },
        "annual_mean_hs_m": 1.7,
        "extreme_hs_typhoon_m": 8.0,   # 태풍 통과 시 최대 (Maemi 2003 등)

        # 월별 평균 풍속 (m/s, 해상 부이 기반)
        "wind_speed_monthly_ms": {
            "Jan": 9.5,  "Feb": 9.0,  "Mar": 7.5,  "Apr": 6.0,
            "May": 5.0,  "Jun": 4.5,  "Jul": 5.5,  "Aug": 5.0,
            "Sep": 6.0,  "Oct": 7.0,  "Nov": 8.5,  "Dec": 9.5,
        },

        # 시정 (visibility, km — 안개 포함)
        "visibility_km_clear": 20,
        "visibility_km_fog_avg": 0.5,
        "fog_days_annual": 20,   # 동해 연안 안개일수 (서해 대비 적음)
        "fog_season": "5-8월 집중 (해무, 오호츠크 기단)",
    },

    "west_sea": {
        "name_ko": "서해 (황해)",
        "hs_monthly_m": {
            "Jan": 1.2,  "Feb": 1.1,  "Mar": 1.0,  "Apr": 0.8,
            "May": 0.7,  "Jun": 0.6,  "Jul": 0.7,  "Aug": 0.8,
            "Sep": 0.9,  "Oct": 1.0,  "Nov": 1.1,  "Dec": 1.2,
        },
        "hs_seasonal_m": {
            "winter": 1.2,
            "spring": 0.8,
            "summer": 0.7,
            "autumn": 1.0,
        },
        "annual_mean_hs_m": 0.9,
        "extreme_hs_typhoon_m": 4.0,

        "wind_speed_monthly_ms": {
            "Jan": 8.5,  "Feb": 8.0,  "Mar": 7.0,  "Apr": 5.5,
            "May": 4.5,  "Jun": 4.0,  "Jul": 5.0,  "Aug": 5.5,
            "Sep": 5.5,  "Oct": 6.5,  "Nov": 7.5,  "Dec": 8.5,
        },

        # 황사 (Yellow Dust / Asian Dust)
        "yellow_dust_days_annual": 15,      # 연평균 15일 (3-5월 집중)
        "yellow_dust_peak_months": [3, 4, 5],
        "yellow_dust_visibility_km": 2.0,   # 황사 발생 시 시정 ~2km

        # 안개
        "fog_days_annual": 40,              # 서해가 동해의 약 2배 [12]
        "fog_peak_months": [6, 7],           # 여름 해무 집중
        "fog_visibility_km": 0.3,
    },

    "korea_strait": {
        "name_ko": "대한해협",
        "hs_monthly_m": {
            "Jan": 1.8,  "Feb": 1.7,  "Mar": 1.5,  "Apr": 1.2,
            "May": 1.0,  "Jun": 0.9,  "Jul": 1.0,  "Aug": 1.2,
            "Sep": 1.5,  "Oct": 1.6,  "Nov": 1.7,  "Dec": 1.9,
        },
        "hs_seasonal_m": {
            "winter": 1.8,
            "spring": 1.2,
            "summer": 1.0,
            "autumn": 1.6,
        },
        "annual_mean_hs_m": 1.4,

        # 안개 [12]
        "fog_days_annual": 50,              # 대한해협·남해 안개 빈번
        "fog_peak_months": [4, 5, 6, 7],    # 봄-여름 해무
        "fog_visibility_km": 0.3,
    },

    # ── 태풍 통계 ─────────────────────────────────────────────────────────
    # 출처: [13] JTWC / KMA 1951-2020 통계
    "typhoon": {
        "annual_approach_count": 3.4,   # 한반도 영향 태풍 연평균 3.4개
                                         # (300km 내 17m/s 이상 기준, 1951-2020)
        "annual_influence_count": 7,    # 직간접 영향 포함 시 연간 ~7회
        "peak_months": [8, 9],           # 8-9월 최다 내습
        "season_range": "4-11월",
        "main_tracks": [
            "서해 북상 (황해→한반도)",
            "동해 북상 (일본 서쪽→동해→한반도)",
            "남해 관통 (대한해협 북상)",
        ],
        "max_wave_height_m": 10.0,       # 초강력 태풍 (카테고리 4-5) 통과 시
        "max_wind_speed_ms": 55.0,
    },
}


# =============================================================================
# 4. 해면 상태별 탐지 영향 (Environmental Effects on Sensors)
# =============================================================================

# ── Beaufort Scale ↔ 파고 / 풍속 ──────────────────────────────────────────
# 출처: WMO Douglas Scale, 기상청 해상예보 기준
BEAUFORT_SCALE = {
    # BN: (wind_speed_ms_low, wind_speed_ms_high, Hs_m, description_ko)
    0: (0.0,  0.2,  0.0,  "고요"),
    1: (0.3,  1.5,  0.1,  "잔잔"),
    2: (1.6,  3.3,  0.2,  "실바람"),
    3: (3.4,  5.4,  0.6,  "산들바람"),
    4: (5.5,  7.9,  1.0,  "건들바람"),
    5: (8.0, 10.7,  2.0,  "흔들바람"),
    6: (10.8, 13.8, 3.0,  "된바람"),
    7: (13.9, 17.1, 4.0,  "센바람"),
    8: (17.2, 20.7, 5.5,  "큰바람"),
    9: (20.8, 24.4, 7.0,  "큰센바람"),
    10: (24.5, 28.4, 9.0, "노대바람"),
    11: (28.5, 32.6, 11.5,"왕바람"),
    12: (32.7, 99.0, 14.0,"싹쓸바람"),
}

# ── 레이더 클러터 (Radar Sea Clutter) ────────────────────────────────────
# X-band (9-10 GHz), S-band (3 GHz), 저고도 입사각 기준
# sigma0 단위: dBm²/m² (normalized RCS)
# 출처: [15], Nathanson 클러터 테이블 참고
RADAR_CLUTTER = {
    "description": "Beaufort 등급별 레이더 해상 클러터 특성",

    # (X-band sigma0_dB, S-band sigma0_dB, 클러터 영향 등급)
    # 저고도 3° 입사각, 수평편파(HH) 기준
    "by_beaufort": {
        0: {"xband_sigma0_dB": -70, "sband_sigma0_dB": -75, "impact": "무시 가능"},
        1: {"xband_sigma0_dB": -65, "sband_sigma0_dB": -70, "impact": "무시 가능"},
        2: {"xband_sigma0_dB": -58, "sband_sigma0_dB": -63, "impact": "경미"},
        3: {"xband_sigma0_dB": -50, "sband_sigma0_dB": -55, "impact": "경미"},
        4: {"xband_sigma0_dB": -43, "sband_sigma0_dB": -48, "impact": "보통"},
        5: {"xband_sigma0_dB": -37, "sband_sigma0_dB": -42, "impact": "보통-강"},
        6: {"xband_sigma0_dB": -30, "sband_sigma0_dB": -35, "impact": "강"},
        7: {"xband_sigma0_dB": -25, "sband_sigma0_dB": -30, "impact": "매우 강"},
        8: {"xband_sigma0_dB": -20, "sband_sigma0_dB": -25, "impact": "심각"},
        9: {"xband_sigma0_dB": -17, "sband_sigma0_dB": -22, "impact": "심각"},
       10: {"xband_sigma0_dB": -15, "sband_sigma0_dB": -20, "impact": "극심"},
       11: {"xband_sigma0_dB": -13, "sband_sigma0_dB": -18, "impact": "극심"},
       12: {"xband_sigma0_dB": -12, "sband_sigma0_dB": -17, "impact": "탐지 불능 수준"},
    },

    # 탐지거리 감소 비율 (기준 거리 대비) — Beaufort 등급별
    # 계산 기준: SNR 필요값 15 dB, 대기 전파 손실 포함
    "detection_range_factor": {
        0: 1.00,  # 100%
        1: 1.00,
        2: 0.98,
        3: 0.95,
        4: 0.90,
        5: 0.82,
        6: 0.73,
        7: 0.62,
        8: 0.50,
        9: 0.40,
       10: 0.32,
       11: 0.25,
       12: 0.18,
    },
}

# ── 수중 소나 주변 소음 (Underwater Sonar Ambient Noise) ─────────────────
# Wenz 곡선 기반. 단위: dB re 1 μPa²/Hz (spectral level)
# 출처: [14] Wenz(1962)/IntechOpen 재구성, 한반도 주변 해역 보정 적용
SONAR_AMBIENT_NOISE = {
    "description": (
        "Beaufort/Sea State → 수중 주변 소음 스펙트럼 레벨 (dB re 1 μPa²/Hz). "
        "Wenz 곡선 기반. 동해·대한해협 선박 교통량 보정 포함."
    ),

    # 풍속 의존 Knudsen noise (500 Hz - 25 kHz 구간 지배)
    # 각 항목: (100Hz_dB, 500Hz_dB, 1kHz_dB, 5kHz_dB)
    "by_beaufort_spectral_dB": {
        0: (35, 25, 20, 15),
        1: (40, 32, 28, 22),
        2: (45, 38, 34, 28),
        3: (50, 44, 40, 34),
        4: (55, 50, 46, 40),
        5: (60, 55, 52, 46),
        6: (64, 60, 57, 51),
        7: (67, 64, 62, 56),
        8: (70, 68, 66, 60),
        9: (72, 71, 69, 63),
       10: (74, 73, 72, 66),
       11: (75, 75, 74, 68),
       12: (77, 77, 76, 70),
    },

    # 저주파 (10-100 Hz) 선박 소음 기여 — 해역별
    "shipping_noise_100Hz_dB": {
        "east_sea":     65,  # 비교적 낮음 (선박 교통 보통)
        "west_sea":     70,  # 보하이·황해 선박 교통 조밀
        "korea_strait": 75,  # 국제 항로 통과량 최다
    },

    # 비 소음 보정
    "rain_noise_broadband_dB_addition": {
        "light_rain_mm_hr_2": 10,    # 2.5 mm/hr 이하
        "moderate_rain_mm_hr_7": 20, # 7.5 mm/hr
        "heavy_rain_mm_hr_20": 35,   # >20 mm/hr
    },

    # 소나 탐지거리 감소 비율 (기준 BN=2 대비)
    "sonar_range_factor": {
        0: 1.10,  # 고요 → 오히려 소음 감소, 탐지 유리
        1: 1.05,
        2: 1.00,  # 기준
        3: 0.92,
        4: 0.82,
        5: 0.70,
        6: 0.58,
        7: 0.48,
        8: 0.38,
        9: 0.30,
       10: 0.24,
       11: 0.20,
       12: 0.16,
    },
}

# ── EO/IR 센서 탐지거리 감소 (Electro-Optical / Infrared) ─────────────────
# 출처: [16] FLIR, IDA EO/IR Tutorial
EOIR_DEGRADATION = {
    "description": "기상 조건별 EO/IR 센서 탐지거리 감소율",

    # 시정(km) → (가시광 감소율, MWIR 감소율, LWIR 감소율)
    # 수치는 청명 조건(20km 시정) 대비 비율
    "by_visibility_km": {
        20.0: (1.00, 1.00, 1.00),   # 청명
        10.0: (0.80, 0.90, 0.92),
         5.0: (0.60, 0.75, 0.80),
         2.0: (0.35, 0.55, 0.65),   # 황사 수준
         1.0: (0.18, 0.40, 0.52),   # 짙은 안개 / 황사
         0.5: (0.08, 0.28, 0.40),   # 해무 (서해 여름)
         0.3: (0.03, 0.18, 0.28),   # 농무
         0.1: (0.01, 0.08, 0.12),   # 극농무 (대한해협 봄)
    },

    # 강우 강도(mm/hr) → 탐지거리 감소율
    "by_rain_mm_hr": {
         0:   (1.00, 1.00, 1.00),
         2.5: (0.90, 0.92, 0.93),
         7.5: (0.70, 0.75, 0.80),
        20.0: (0.45, 0.55, 0.65),
        50.0: (0.20, 0.35, 0.45),   # 폭우
    },

    # 황사 발생 시 추가 감소
    "yellow_dust_factor": {
        "light":   (0.60, 0.80, 0.85),  # PM10 < 150 μg/m³
        "moderate":(0.35, 0.60, 0.70),  # PM10 150-300 μg/m³
        "heavy":   (0.15, 0.40, 0.55),  # PM10 > 300 μg/m³
    },
}


# =============================================================================
# 5. 수중 소음 환경 (Underwater Acoustic Environment)
# =============================================================================

UNDERWATER_ACOUSTICS = {

    "east_sea": {
        "name_ko": "동해",
        "depth_m": 2000,            # 평균 수심 ~2000m (최대 3742m)
        "sound_speed_surface_ms": 1520,
        "sound_speed_deep_ms":    1500,
        "SOFAR_depth_m": 800,       # 동해 SOFAR 채널 심도

        # 주변 소음 (배경 소음) 수준 — 계절 평균, dB re 1μPa²/Hz
        "ambient_noise_dB": {
            "Hz_10":   75,   # 지진·원격 수송 → 저주파
            "Hz_100":  65,   # 선박 기여 (보통)
            "Hz_500":  52,
            "kHz_1":   48,
            "kHz_5":   42,
            "kHz_10":  38,
        },

        # 계절 변화 (여름 수온약층 발달로 소나 성능 저하)
        "seasonal_sonar_effect": {
            "summer": "수온약층 10-50m 발달 → 음파 굴절, 탐지거리 30-50% 감소",
            "winter": "혼합층 깊어짐 → 소나 성능 향상 (15-20% 증가)",
        },
    },

    "west_sea": {
        "name_ko": "서해 (황해)",
        "depth_m": 44,              # 평균 수심 44m (매우 얕음)
        "sound_speed_surface_ms": 1505,
        "sound_speed_deep_ms":    1510,   # 얕아서 상하차 미미
        "SOFAR_depth_m": None,      # 얕은 해역 — SOFAR 채널 형성 안 됨

        # 주변 소음 — 선박 교통 많아 전반적 높음
        "ambient_noise_dB": {
            "Hz_10":   80,
            "Hz_100":  70,
            "Hz_500":  60,
            "kHz_1":   55,
            "kHz_5":   48,
            "kHz_10":  42,
        },

        # 음파 전파 특성
        "propagation_note": (
            "평균 수심 44m 얕은 해역. 음파 다중반사(수면-해저) 심각. "
            "저주파 탐지 유리하나 반향(Reverberation) 잡음 크다. "
            "겨울 등온층 형성 시 음파 수직 혼합 — 소나 성능 季節 역전."
        ),

        # 황해 음속 모니터링 (ARGO 부이 10개월 데이터 기반) [논문]
        "sound_channel_seasonal": {
            "winter": "표면 음속 채널 형성 (등온층, 음파 표면 집중)",
            "spring_onwards": "수온약층 발달 → 음속 채널 두께 감소, 음파 아래로 굴절",
        },
    },

    "korea_strait": {
        "name_ko": "대한해협",
        "depth_m": 150,             # 평균 수심 ~150m (최대 228m)
        "sound_speed_surface_ms": 1510,
        "sound_speed_deep_ms":    1500,

        # 선박 교통 밀집 → 소음 최고 수준
        "ambient_noise_dB": {
            "Hz_10":   85,   # 국제 항로 → 저주파 선박 소음 높음
            "Hz_100":  75,
            "Hz_500":  63,
            "kHz_1":   58,
            "kHz_5":   50,
            "kHz_10":  44,
        },

        "shipping_density": "극도로 밀집 (세계 최다 통항 해협 중 하나)",
        "biological_noise": "봄철 멸치·고등어 산란 군집 생물 소음 기여",
    },

    # ── 생물 소음 계절 특성 ─────────────────────────────────────────────────
    "biological_noise": {
        "spring_peak_months": [4, 5, 6],
        "species": ["멸치", "고등어", "갈치", "새우류"],
        "snapping_shrimp_dB_at_1m": 189,   # peak-to-peak [14]
        "whale_low_freq_dB": 190,           # 10-25 Hz [14]
        "seasonal_dB_addition": 5,          # 봄철 +5 dB (참고값)
    },
}


# =============================================================================
# 6. 시뮬레이터 통합 환경 함수
# =============================================================================

def get_sea_state(region: str, month: int) -> dict:
    """
    해역과 월을 입력하면 시뮬레이터에서 쓸 환경 파라미터 딕셔너리 반환.

    Args:
        region: "east_sea" | "west_sea" | "korea_strait"
        month:  1-12

    Returns:
        {
            "hs_m": float,          유의파고 (m)
            "wind_ms": float,       평균 풍속 (m/s)
            "beaufort": int,        보퍼트 등급 (추정)
            "visibility_km": float, 평균 시정 (km)
            "fog_probability": float, 안개 확률 (0-1)
            "yellow_dust_probability": float,
            "tidal_current_ms": float, 대표 조류 (m/s)
            "radar_range_factor": float,
            "sonar_range_factor": float,
            "ambient_noise_1kHz_dB": float,
        }
    """
    w = WAVE_STATISTICS.get(region, WAVE_STATISTICS["east_sea"])
    month_str = [None,"Jan","Feb","Mar","Apr","May","Jun",
                 "Jul","Aug","Sep","Oct","Nov","Dec"][month]

    hs = w["hs_monthly_m"].get(month_str, w["annual_mean_hs_m"])
    wind = w.get("wind_speed_monthly_ms", {}).get(month_str, 6.0)

    # Beaufort 추정 (풍속 기반)
    bf = 0
    for bn, (lo, hi, _, _) in BEAUFORT_SCALE.items():
        if lo <= wind <= hi:
            bf = bn
            break

    # 안개 확률
    fog_days = w.get("fog_days_annual", 20)
    fog_peak = w.get("fog_peak_months", [6, 7])
    base_fog_prob = fog_days / 365
    fog_prob = base_fog_prob * (2.5 if month in fog_peak else 0.5)

    # 황사 확률 (서해만)
    yd_prob = 0.0
    if region == "west_sea":
        yd_peak = w.get("yellow_dust_peak_months", [3, 4, 5])
        yd_days = w.get("yellow_dust_days_annual", 15)
        base_yd = yd_days / 365
        yd_prob = base_yd * (3.0 if month in yd_peak else 0.1)

    # 시정
    if fog_prob > 0.3:
        vis_km = w.get("fog_visibility_km", 0.5)
    elif yd_prob > 0.2:
        vis_km = w.get("yellow_dust_visibility_km", 2.0)
    else:
        vis_km = w.get("visibility_km_clear", 20.0)

    # 탐지거리 팩터
    radar_f = RADAR_CLUTTER["detection_range_factor"].get(bf, 1.0)
    sonar_f = SONAR_AMBIENT_NOISE["sonar_range_factor"].get(bf, 1.0)

    # 1kHz 주변소음
    noise_table = SONAR_AMBIENT_NOISE["by_beaufort_spectral_dB"]
    _, _, noise_1khz, _ = noise_table.get(bf, noise_table[5])
    # 해역별 선박 소음 보정
    shipping_add = {
        "east_sea": 0, "west_sea": 5, "korea_strait": 10
    }.get(region, 0)
    noise_1khz += shipping_add

    # 조류 (대표값)
    tidal_ms = {
        "east_sea":     0.05,
        "west_sea":     0.50,
        "korea_strait": 0.77,
    }.get(region, 0.3)

    return {
        "hs_m":                    round(hs, 2),
        "wind_ms":                 round(wind, 1),
        "beaufort":                bf,
        "visibility_km":           round(vis_km, 1),
        "fog_probability":         round(min(fog_prob, 0.9), 3),
        "yellow_dust_probability": round(min(yd_prob, 0.6), 3),
        "tidal_current_ms":        tidal_ms,
        "radar_range_factor":      radar_f,
        "sonar_range_factor":      sonar_f,
        "ambient_noise_1kHz_dB":   noise_1khz,
    }


def get_current_vector(region: str, month: int) -> dict:
    """
    해역·월별 대표 해류 벡터 반환.

    Returns:
        {"speed_cms": float, "direction_deg": float}
        direction_deg: 해류 흐르는 방향 (진북 기준, 도)
    """
    if region == "east_sea":
        # 동한난류 (북상) 우세
        speed = OCEAN_CURRENTS["east_korea_warm_current"]["speed_by_season_cms"]
        season_map = {1:"winter",2:"winter",3:"spring",4:"spring",5:"spring",
                      6:"summer",7:"summer",8:"summer",9:"autumn",
                      10:"autumn",11:"autumn",12:"winter"}
        spd = speed.get(season_map[month], 30)
        return {"speed_cms": spd, "direction_deg": 0}   # 북향

    elif region == "west_sea":
        # 황해 연안류: 여름 북향, 겨울 남향
        if 5 <= month <= 8:
            spd = OCEAN_CURRENTS["west_korea_coastal_current"]["speed_cms_jul_aug"]
            return {"speed_cms": spd, "direction_deg": 0}
        else:
            return {"speed_cms": 6.0, "direction_deg": 180}  # 남향

    elif region == "korea_strait":
        # 대마난류 북동향
        twc = OCEAN_CURRENTS["tsushima_warm_current"]
        month_str = [None,"Jan","Feb","Mar","Apr","May","Jun",
                     "Jul","Aug","Sep","Oct","Nov","Dec"][month]
        transport = twc["transport_by_month_Sv"].get(month_str, 2.64)
        # 수송량 → 유속 근사 (단면적 40km × 100m 기준)
        spd = transport / 2.64 * twc["typical_speed_cms"]
        return {"speed_cms": round(spd, 1), "direction_deg": 45}  # 북동향

    return {"speed_cms": 10.0, "direction_deg": 0}


if __name__ == "__main__":
    import json

    print("=== 해역별 환경 파라미터 샘플 ===\n")
    for region in ["east_sea", "west_sea", "korea_strait"]:
        print(f"[{region}]")
        for month in [1, 6, 9]:
            env = get_sea_state(region, month)
            print(f"  {month:2d}월: Hs={env['hs_m']}m  BF={env['beaufort']}  "
                  f"Fog={env['fog_probability']:.2f}  "
                  f"Radar_f={env['radar_range_factor']:.2f}  "
                  f"Sonar_f={env['sonar_range_factor']:.2f}  "
                  f"Noise={env['ambient_noise_1kHz_dB']}dB")
        print()

    print("=== 대마난류 월별 수송량 ===")
    twc = OCEAN_CURRENTS["tsushima_warm_current"]
    for m, v in twc["transport_by_month_Sv"].items():
        print(f"  {m}: {v} Sv")
