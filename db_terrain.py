# =============================================================================
#  db_terrain.py — 한반도 주변 지형·해양 데이터베이스
#  출처: GEBCO_2023, NOAA, KHOA, SRTM, Wikipedia(한/영), 나무위키,
#        한국민족문화대백과, GlobalSecurity, CSIS Beyond Parallel, FAS NTI
#  수집일: 2026-06-01
#  주의: 군사 기지 좌표는 공개 위성분석·공개자료 기반. 시뮬레이션 전용.
# =============================================================================

# =============================================================================
#  Part 1. 해저 수심 데이터 (BATHYMETRY_DB)
#  출처: GEBCO_2023, NOAA, KHOA, Wikipedia, 한국민족문화대백과
# =============================================================================

BATHYMETRY_DB = {

    # ─────────────────────────────────────────────────────────────────────────
    # 서해 (황해, Yellow Sea)
    # ─────────────────────────────────────────────────────────────────────────
    "yellow_sea": {
        "name_ko": "서해(황해)",
        "area_km2": 380_000,
        "depth_avg_m": 44,       # KHOA, 한국민족문화대백과, UNDP 일치
        "depth_max_m": 103,      # 제주도 북서쪽 (국내 기준)
        "depth_typical_range_m": (20, 80),
        "depth_by_zone": {
            "north_yellow_sea_m": 20,
            "central_trough_m": 90,
            "south_yellow_sea_trough_m": 80,
            "near_jeju_m": 103,
            "jiangsu_coast_china_m": 50,
        },
        "depth_distribution_pct": {
            "below_10m": 8,
            "below_20m": 20,
            "below_50m": 55,
            "below_100m": 97,
        },
        "submarine_ops": {
            "max_practical_depth_m": 80,
            "thermocline_possible": False,
            "thermocline_min_depth_m": None,
            "notes": (
                "평균 44m — 현대 잠수함 운용 사실상 불가. "
                "수온약층 미형성. 최대 103m 구역에서도 재래식 잠수함 저속 운용만 가능."
            ),
        },
        "sources": [
            "Wikipedia Yellow Sea (avg 44m, max 103m)",
            "한국민족문화대백과 황해",
            "KHOA, UNDP/GEF YSLME",
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 동해 (East Sea)
    # ─────────────────────────────────────────────────────────────────────────
    "east_sea": {
        "name_ko": "동해",
        "area_km2": 1_007_300,
        "depth_avg_m": 1_684,    # KHOA 공식값
        "depth_max_m": 3_762,    # KHOA 공식값
        "deep_area_km2": 300_000,  # 수심 3,000m 이상
        "basins": {
            "japan_basin": {
                "location": "동해 북부",
                "depth_avg_m": 3_300,
                "depth_max_m": 3_742,
                "notes": "동해 최심·최대 분지. 동해고유수(JSPW) 형성 핵심.",
            },
            "ulleung_basin": {
                "location": "동해 남서부 (울릉도·독도 남측)",
                "center_coord": (37.0, 130.83),
                "extent_ns_km": 100,
                "extent_ew_km": 150,
                "depth_avg_m": 2_000,
                "depth_max_m": 2_300,
                "depth_min_m": 1_500,
                "sill_korea_gap_m": 2_000,
            },
            "yamato_basin": {
                "location": "동해 남동부",
                "depth_avg_m": 2_000,
                "depth_max_m": 2_966,
                "notes": "야마토 해령(대화퇴)으로 울릉분지와 분리",
            },
        },
        "ridges": {
            "yamato_ridge": {
                "name_ko": "대화퇴",
                "depth_min_m": 285,
                "depth_avg_m": 1_500,
                "notes": "야마토·울릉 분지 분리. 대화퇴 해양과학기지.",
            },
        },
        "submarine_ops": {
            "max_depth_terrain_limit_m": 3_700,
            "thermocline_possible": True,
            "thermocline_data": {
                "summer": {
                    "seasonal_thermocline_top_m": 20,
                    "seasonal_thermocline_bottom_m": 100,
                    "gradient_max_degC_per_m": 0.36,
                    "notes": "SPF 남쪽: 25~100m 폭 넓은 약층. 북쪽: 20~40m 얕고 날카로움.",
                },
                "winter": {
                    "permanent_thermocline_top_m": 100,
                    "permanent_thermocline_bottom_m": 250,
                    "gradient_degC_per_m": 0.05,
                    "notes": "SPF 북쪽 1~3월 소실. 남쪽에서만 영구 약층 잔존.",
                },
                "thermocline_min_viable_depth_m": 150,
            },
            "east_sea_deep_water": {
                "temp_degC": 0.05,
                "depth_range_m": (200, 2_300),
                "salinity_psu": 34.06,
                "notes": "동해 고유수: 연중 균일 저온, 소나 전파 특이 환경",
            },
        },
        "sources": [
            "KHOA 동해소개 (avg 1,684m, max 3,762m)",
            "Wikipedia Sea of Japan",
            "ScienceDirect — Thermocline splitting near East Sea shelf break",
            "NPS Calhoun — Japan/East Sea circulation",
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 남해 (Korea South Sea)
    # ─────────────────────────────────────────────────────────────────────────
    "south_sea": {
        "name_ko": "남해",
        "depth_avg_m": 71,
        "depth_max_m": 198,      # 마라도 북서 2.3km
        "depth_typical_range_m": (20, 150),
        "submarine_ops": {
            "max_practical_depth_m": 150,
            "thermocline_possible": True,
            "thermocline_min_depth_m": 100,
            "notes": "마라도 주변 최심부(198m)에서만 소형 잠수함 잠항 가능.",
        },
        "sources": ["한국 해역 수심 비교 통계", "제주환경일보"],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 대한해협 (Korea Strait)
    # ─────────────────────────────────────────────────────────────────────────
    "korea_strait": {
        "name_ko": "대한해협",
        "total_width_km": 200,
        "depth_avg_m": 95,
        "western_channel": {
            "name_ko": "서수도",
            "width_km": 40,
            "depth_max_m": 227,
            "sill_depth_m": 130,
            "depth_avg_m": 160,
            "notes": "두 수도 중 더 깊음. 쓰시마 난류 서쪽 지류 주통로.",
        },
        "eastern_channel": {
            "name_ko": "동수도(쓰시마해협)",
            "width_km": 140,
            "depth_max_m": 120,
            "sill_depth_m": 115,
            "depth_avg_m": 90,
            "depth_range_m": (50, 130),
        },
        "submarine_ops": {
            "western_passable": True,   # 임계수심 130m
            "eastern_passable": True,   # 임계수심 115m — 소형만
            "notes": "냉전 시 소련 잠수함은 주로 서수도 이용.",
        },
        "sources": [
            "Wikipedia Korea Strait",
            "Teague et al. (2006) Oceanography 19-3",
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 제주해협
    # ─────────────────────────────────────────────────────────────────────────
    "jeju_strait": {
        "name_ko": "제주해협",
        "width_km": 80,
        "depth_avg_m": 70,
        "depth_max_m": 140,
        "submarine_ops": {
            "max_practical_depth_m": 120,
            "thermocline_possible": False,
            "notes": "평균 70m 천해로 잠수함 작전 극히 제한적.",
        },
        "sources": ["Wikipedia Jeju Strait", "NamuWiki 제주해협"],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 이어도(소코트라 암초)
    # ─────────────────────────────────────────────────────────────────────────
    "ieodo": {
        "name_ko": "이어도(소코트라 암초)",
        "coord": (32.123, 125.182),
        "rock_depth_m": 4.6,
        "platform_anchor_depth_m": 40,
        "surrounding_depth_m": 40,
        "reef_extent_at_40m": {"ns_m": 600, "ew_m": 750},
        "distance_from_marado_km": 149,
        "distance_from_china_km": 287,
        "sources": ["Wikipedia Socotra Rock", "KHOA Ieodo Ocean Research Station"],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 독도 주변 해저 지형
    # ─────────────────────────────────────────────────────────────────────────
    "dokdo": {
        "name_ko": "독도 주변 해저 지형",
        "coord_approx": (37.242, 131.865),
        "above_sea": {
            "dongdo_peak_m": 98.6,
            "seodo_peak_m": 168.5,
        },
        "seamount": {
            "base_depth_m": 2_100,
            "height_total_m": 2_300,
            "base_diameter_km": 28,
            "origin": "동해 후호 분지 화산 활동",
        },
        "regional_depth_m": 2_000,
        "sources": ["BioOne — Detailed Bathymetry Dokdo Volcano", "KSEEG 2023"],
    },
}


# =============================================================================
#  Part 2. 한반도 육상 지형 (TERRAIN_DB)
#  출처: SRTM, 국토지리정보원, Wikipedia(한/영), 나무위키, 한국민족문화대백과
#  좌표계: WGS84 (도 단위 십진수)
# =============================================================================

TERRAIN_DB = {

    # =========================================================================
    # 산맥
    #   ridge_width_km: 주능선 폭 범위 (레이더 음영 계산 참고용)
    #   avg_ridge_elev_m: 평균 능선 고도
    # =========================================================================
    "mountain_ranges": {

        "taebaek": {
            "name_ko": "태백산맥",
            "length_km": 500,
            "direction": "N-S",
            "lat_range": (35.0, 38.6),
            "lon_approx": 128.5,
            "avg_ridge_elev_m": 900,
            "ridge_width_km": (20, 50),
            "east_coast_dist_km": (5, 30),
            "peaks": [
                ("설악산 대청봉", 1708, 38.119, 128.466),
                ("금강산 비로봉", 1638, 38.657, 128.104),
                ("오대산 비로봉", 1563, 37.796, 128.543),
                ("함백산",        1573, 37.185, 128.901),
                ("태백산 장군봉", 1567, 37.100, 128.915),
                ("보현산",        1124, 36.157, 128.965),
                ("팔공산",        1193, 35.990, 128.693),
            ],
            "major_passes": [
                ("진부령",  529),
                ("미시령",  826),
                ("한계령", 1004),
                ("대관령",  832),
                ("구룡령", 1013),
            ],
        },

        "sobaek": {
            "name_ko": "소백산맥",
            "length_km": 350,
            "direction": "NE-SW",
            "lat_range": (34.8, 37.1),
            "lon_range": (127.0, 128.9),
            "avg_ridge_elev_m": 800,
            "ridge_width_km": (20, 40),
            "south_sea_dist_km": (30, 80),
            "peaks": [
                ("지리산 천왕봉", 1915, 35.337, 127.731),
                ("덕유산 향적봉", 1594, 35.858, 127.746),
                ("소백산 비로봉", 1421, 36.960, 128.489),
                ("속리산 천왕봉", 1057, 36.559, 127.868),
                ("가야산 칠불봉", 1433, 35.820, 128.110),
            ],
            "major_passes": [
                ("문경새재(조령)", 642),
                ("추풍령",         221),
                ("육십령",         734),
                ("팔량치",         513),
            ],
        },

        "nangnim": {
            "name_ko": "낭림산맥",
            "length_km": 370,
            "direction": "N-S",
            "lat_range": (39.0, 41.5),
            "lon_approx": 127.0,
            "avg_ridge_elev_m": 1470,  # 위키백과 기재값
            "ridge_width_km": (30, 60),
            "peaks": [
                ("와갈봉",   2262, 40.30, 126.90),  # 낭림산맥 최고봉
                ("맹부산",   2217, 40.10, 126.80),
                ("낭림산",   2186, 40.40, 126.70),
                ("희색봉",   2185, 40.50, 126.60),
                ("대홍산",   2152, 40.20, 126.85),
                ("소백산",   2184, 39.90, 126.95),
                ("동백산",   2096, 39.80, 127.00),
            ],
            "major_passes": [
                ("오가산령",  1119),
                ("불개미령", 1386),
                ("가릉령",   1324),
                ("황수령",   1475),
                ("덕유대령", 1501),
                ("설한령",   1433),
            ],
        },

        "hamgyong": {
            "name_ko": "함경산맥",
            "length_km": 320,
            "direction": "NE-SW",
            "lat_range": (40.5, 42.5),
            "lon_range": (128.5, 130.5),
            "avg_ridge_elev_m": 1800,
            "ridge_width_km": (20, 40),
            "east_coast_dist_km": (10, 50),
            "peaks_above_2000m_count": 72,
            "peaks": [
                ("관모봉",   2541, 41.95, 129.30),
                ("차일봉",   2506, 42.00, 129.20),
                ("북수백산", 2522, 41.10, 128.70),
                ("두류산",   2309, 41.30, 128.90),
                ("만탑산",   2205, 41.15, 129.10),
            ],
        },

        "masikryong": {
            "name_ko": "마식령산맥",
            "length_km": 200,
            "direction": "NW-SE",
            "lat_range": (38.5, 39.8),
            "lon_range": (126.5, 127.8),
            "avg_ridge_elev_m": 1000,
            "peaks": [
                ("동백년산", 1246, 39.20, 127.20),
                ("화개산",   1187, 39.10, 127.10),
            ],
        },

        "noryong": {
            "name_ko": "노령산맥",
            "length_km": 200,
            "direction": "NE-SW",
            "lat_range": (35.2, 36.5),
            "lon_range": (126.5, 127.8),
            "avg_ridge_elev_m": 500,
            "peaks": [
                ("운장산",        1126, 35.990, 127.387),
                ("내장산 신선봉",  763, 35.487, 126.885),
                ("방장산",         734, 35.426, 126.826),
            ],
        },
    },

    # =========================================================================
    # 주요 고봉 (좌표: WGS84 도 단위)
    # =========================================================================
    "major_peaks": {

        # 북한
        "baekdusan":   {"name_ko": "백두산 장군봉",  "elev_m": 2744, "lat": 42.005, "lon": 128.058, "coast_dist_km": 280, "notes": "한반도 최고봉"},
        "gwanmobong":  {"name_ko": "관모봉",          "elev_m": 2541, "lat": 41.95,  "lon": 129.30,  "coast_dist_km": 35,  "notes": "함경산맥 최고봉"},
        "chailbong":   {"name_ko": "차일봉",          "elev_m": 2506, "lat": 42.00,  "lon": 129.20,  "coast_dist_km": 60},
        "buksubaek":   {"name_ko": "북수백산",        "elev_m": 2522, "lat": 41.10,  "lon": 128.70,  "coast_dist_km": 80},
        "wagalbong":   {"name_ko": "와갈봉",          "elev_m": 2262, "lat": 40.30,  "lon": 126.90,  "coast_dist_km": 200, "notes": "낭림산맥 최고봉"},
        "myohyangsan": {"name_ko": "묘향산 비로봉",   "elev_m": 1909, "lat": 40.019, "lon": 126.333, "coast_dist_km": 80},
        "geumgangsan": {"name_ko": "금강산 비로봉",   "elev_m": 1638, "lat": 38.657, "lon": 128.104, "coast_dist_km": 22},

        # 남한
        "seoraksan":   {"name_ko": "설악산 대청봉",  "elev_m": 1708, "lat": 38.119, "lon": 128.466, "coast_dist_km": 12},
        "jirisan":     {"name_ko": "지리산 천왕봉",  "elev_m": 1915, "lat": 35.337, "lon": 127.731, "coast_dist_km": 45},
        "hallasan":    {"name_ko": "한라산 백록담",   "elev_m": 1947, "lat": 33.362, "lon": 126.529, "coast_dist_km": 20, "notes": "남한 최고봉"},
        "deogyusan":   {"name_ko": "덕유산 향적봉",  "elev_m": 1614, "lat": 35.858, "lon": 127.746, "coast_dist_km": 60},
        "odaesan":     {"name_ko": "오대산 비로봉",  "elev_m": 1563, "lat": 37.796, "lon": 128.543, "coast_dist_km": 40},
        "taebaeksan":  {"name_ko": "태백산 장군봉",  "elev_m": 1567, "lat": 37.100, "lon": 128.915, "coast_dist_km": 45},
    },

    # =========================================================================
    # 주요 평야 및 분지
    # =========================================================================
    "plains": {
        "honam":         {"name_ko": "호남평야",         "area_km2": 3500, "avg_elev_m": 10,  "center": (35.85, 127.00), "notes": "한반도 최대 평야"},
        "gimhae":        {"name_ko": "김해평야",         "area_km2": 800,  "avg_elev_m": 5,   "center": (35.23, 128.89)},
        "naju":          {"name_ko": "나주평야",         "area_km2": 1610, "avg_elev_m": 15,  "center": (35.02, 126.71)},
        "hangang_basin": {"name_ko": "한강 유역 (서울-인천)", "area_km2": 2500, "avg_elev_m": 20, "center": (37.55, 126.90), "notes": "군사 핵심 기동로"},
        "nakdong_basin": {"name_ko": "낙동강 유역",     "area_km2": 2300, "avg_elev_m": 15,  "center": (35.80, 128.60)},
        "gwanseo":       {"name_ko": "관서평야 (북한)",  "area_km2": 5000, "avg_elev_m": 30,  "center": (39.50, 125.80), "notes": "북한 최대 평야. 평양 일대."},
        "hamheung":      {"name_ko": "함흥평야 (북한)",  "area_km2": 1300, "avg_elev_m": 21,  "center": (39.92, 127.55)},
    },

    # =========================================================================
    # 북한 해안선 주요 지점
    # =========================================================================
    "nk_coastline": {
        "east": {
            "wonsan":   {"lat": 39.153, "lon": 127.435, "bay": "영흥만", "port_depth_m": 10},
            "heungnam": {"lat": 39.831, "lon": 127.630, "bay": "함흥만"},
            "chongjin": {"lat": 41.767, "lon": 129.723, "bay": "경성만", "port_depth_m": 12},
            "najin":    {"lat": 42.248, "lon": 130.305, "notes": "나진-선봉 자유경제지대"},
        },
        "west": {
            "sinuiju":  {"lat": 40.100, "lon": 124.398, "notes": "압록강 하구"},
            "nampho":   {"lat": 38.737, "lon": 125.408, "notes": "대동강 하구, 평양 외항"},
            "haeju":    {"lat": 37.978, "lon": 125.699, "notes": "서해 NLL 인근"},
        },
    },

    # =========================================================================
    # 해군 작전 관련 주요 섬
    # =========================================================================
    "key_islands": {
        "dokdo": {
            "name_ko": "독도",
            "dongdo": {"lat": 37.2408, "lon": 131.8696, "elev_m": 98.6},
            "seodo":  {"lat": 37.2418, "lon": 131.8652, "elev_m": 168.5},
            "dist_from_ulleung_km": 87.4,
            "dist_from_japan_oki_km": 157.5,
        },
        "ieodo":        {"name_ko": "이어도",    "lat": 32.123,  "lon": 125.182, "elev_m": -4.6, "notes": "수중 암초, 영토 아님"},
        "baengnyeongdo": {"name_ko": "백령도",   "lat": 37.966,  "lon": 124.630, "max_elev_m": 184, "dist_from_nk_km": 17},
        "daecheongdo":  {"name_ko": "대청도",    "lat": 37.838,  "lon": 124.715, "max_elev_m": 343},
        "yeonpyeongdo": {"name_ko": "연평도",    "lat": 37.638,  "lon": 125.667, "max_elev_m": 130},
        "hongdo":       {"name_ko": "홍도",      "lat": 34.685,  "lon": 125.183, "max_elev_m": 365, "peak": "깃대봉"},
        "gageodo":      {"name_ko": "가거도",    "lat": 34.073,  "lon": 125.117, "max_elev_m": 639, "peak": "독실산", "notes": "대한민국 최서남단"},
        "ulleungdo":    {"name_ko": "울릉도",    "lat": 37.493,  "lon": 130.866, "max_elev_m": 984, "peak": "성인봉"},
        "jejudo":       {"name_ko": "제주도",    "lat": 33.362,  "lon": 126.529, "max_elev_m": 1947, "area_km2": 1848},
    },

    # =========================================================================
    # 주요 하천 (지상군 도하 장애물)
    # =========================================================================
    "major_rivers": {
        "nakdong": {"name_ko": "낙동강", "length_km": 521, "basin_area_km2": 23860},
        "han":     {"name_ko": "한강",   "length_km": 514, "basin_area_km2": 34428, "notes": "수도권 관통, 군사 자연장애물"},
        "geum":    {"name_ko": "금강",   "length_km": 401, "basin_area_km2": 9859},
        "daedong": {"name_ko": "대동강 (북한)", "length_km": 450, "notes": "평양 관통"},
        "imjin":   {"name_ko": "임진강", "length_km": 254, "notes": "DMZ 인근, 도하 장애물"},
    },

    # =========================================================================
    # 레이더 음영 계산용 참조값
    #   shadow_angle = arctan(ridge_elev_m / (coast_to_ridge_km * 1000))  (도)
    # =========================================================================
    "radar_shadow_reference": {
        "taebaek_east": {
            "desc": "동해 함정 레이더 ← 태백산맥",
            "coast_to_ridge_km": 15,
            "ridge_elev_m": 900,
            "shadow_angle_deg": 3.4,
        },
        "sobaek_south": {
            "desc": "남해 함정 레이더 ← 소백산맥",
            "coast_to_ridge_km": 50,
            "ridge_elev_m": 800,
            "shadow_angle_deg": 0.9,
        },
        "nangnim_west": {
            "desc": "서해 함정 레이더 ← 낭림산맥 (북한 내륙)",
            "coast_to_ridge_km": 200,
            "ridge_elev_m": 1470,
            "shadow_angle_deg": 0.4,
        },
        "seoraksan_east": {
            "desc": "동해 근해 함정 레이더 ← 설악산",
            "coast_to_ridge_km": 12,
            "ridge_elev_m": 1708,
            "shadow_angle_deg": 8.1,
        },
        "note": (
            "지구 곡률 보정: 실제 구현 시 4/3 지구반경 등가 모델 적용 권장. "
            "단순 arctan 계산값보다 실제 탐지 거리 약 15% 증가."
        ),
    },
}


# =============================================================================
#  Part 3. 주변국 지형·군사 인프라 (REGIONAL_TERRAIN_DB)
#  출처: Wikipedia, GlobalSecurity, CSIS Beyond Parallel, FAS NTI, 나무위키
# =============================================================================

REGIONAL_TERRAIN_DB = {

    # =========================================================================
    # 일본 측 지형
    # =========================================================================
    "japan": {
        "kyushu_peaks": {
            "kuju_nakadake": {"name_ko": "구주산 나카다케", "elev_m": 1791, "lat": 33.087, "lon": 131.252, "notes": "규슈 최고봉"},
            "aso_takadake":  {"name_ko": "아소산 다카다케", "elev_m": 1592, "lat": 32.884, "lon": 131.104, "caldera_ew_km": 16, "caldera_ns_km": 27},
            "sakurajima":    {"name_ko": "사쿠라지마",       "elev_m": 1117, "lat": 31.585, "lon": 130.657},
        },
        "tsushima": {
            "name_ko": "대마도",
            "coord": (34.4, 129.4),
            "length_ns_km": 82,
            "width_ew_km": 18,
            "area_km2": 696,
            "highest_peak": {"name": "시라다케(白嶽)", "elev_m": 519},
            "dist_from_busan_km": 49.5,
            "dist_from_kyushu_km": 82,
        },
        "okinawa": {
            "name_ko": "오키나와 본섬",
            "coord": (26.5, 127.9),
            "length_km": 120,
            "main_island_highest_m": 503,   # 야에다케
            "prefecture_highest_m": 526,    # 이시가키섬 오모토산
        },
        "daisen": {
            "name_ko": "다이센 (주고쿠 지방 최고봉)",
            "elev_m": 1729,
            "lat": 35.370,
            "lon": 133.537,
            "notes": "산인 해안. 동해 방향 레이더 차폐 주요 지형.",
        },
    },

    # =========================================================================
    # 중국 측 지형
    # =========================================================================
    "china": {
        "shandong_peninsula": {
            "name_ko": "산둥반도",
            "length_ew_km": 290,
            "width_ns_km": (50, 190),
            "area_km2": 73000,
            "highest_peak": {"name": "라오산(嶗山)", "elev_m": 1132, "lat": 36.17, "lon": 120.62},
        },
        "liaodong_peninsula": {
            "name_ko": "랴오둥반도",
            "area_km2": 12573,
            "main_range": {"name": "첸산산맥", "avg_elev_m": 500, "max_elev_approx_m": 1000},
        },
        "bohai_sea": {
            "name_ko": "보하이해",
            "avg_depth_m": 20,
            "strait_width_km": 90,
        },
    },

    # =========================================================================
    # 러시아 측 지형 (동해 북부)
    # =========================================================================
    "russia": {
        "sikhote_alin": {
            "name_ko": "시호테알린 산맥",
            "extent_km": 1200,
            "width_km": 250,
            "avg_elevation_m": 900,
            "peaks": {
                "tordoki_yani": {"elev_m": 2077, "notes": "시호테알린 최고봉"},
                "anik":         {"elev_m": 1933, "notes": "연해주 내 최고봉"},
            },
            "notes": "동해 해안과 평행. 해안 평야 극히 협소.",
        },
        "vladivostok": {
            "city_highest_m": 258,
            "notes": "무라비요프-아무르스키 반도 구릉. 페트르 대제만 리아스식 해안.",
        },
    },
}


# =============================================================================
#  Part 4. 북한 군사 인프라 (NK_MILITARY_DB)
#  출처: Wikipedia, GlobalSecurity, CSIS Beyond Parallel, FAS NTI
#  주의: 교육·시뮬레이션 전용. 실제 작전 정보와 다를 수 있음.
# =============================================================================

NK_MILITARY_DB = {

    # ─────────────────────────────────────────────────────────────────────────
    # 미사일 기지
    # ─────────────────────────────────────────────────────────────────────────
    "missile_bases": {
        "dongchangri": {
            "name_ko": "동창리 서해위성발사장",
            "lat": 39.660, "lon": 124.705,
            "province": "평안북도 철산군",
            "type": "우주발사체/ICBM",
            "source": "Wikipedia 서해위성발사장",
        },
        "musudan_ri": {
            "name_ko": "무수단리 동해위성발사장",
            "lat": 40.855, "lon": 129.666,
            "province": "함경북도 화대군",
            "type": "로켓발사장 (비활성)",
            "source": "Wikipedia Tonghae Satellite Launching Ground",
        },
        "hwangju": {
            "name_ko": "황주 미사일기지 (삿갓몰)",
            "lat": 38.72,  "lon": 125.95,
            "province": "황해북도 연탄군",
            "type": "스커드 SRBM, 노동 MRBM",
            "distance_to_seoul_km": 140,
            "source": "Wikipedia 황주 미사일기지",
        },
        "sangnam_ni": {"name_ko": "상남리",  "lat": 40.839, "lon": 128.542, "source": "CSIS Beyond Parallel"},
        "sino_ri":    {"name_ko": "신오리",  "lat": 39.645, "lon": 125.355, "source": "CSIS Beyond Parallel"},
        "hwajil_li":  {"name_ko": "화질리",  "lat": 39.198, "lon": 125.399, "source": "NTI"},
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 해군 기지
    # ─────────────────────────────────────────────────────────────────────────
    "naval_bases": {
        "mayang_do": {
            "name_ko": "마양도 잠수함기지 (신포)",
            "lat": 39.995, "lon": 128.195,
            "fleet": "동해함대",
            "type": "최대 규모 잠수함기지",
            "notes": "신포조선소 포함. SLBM 연구시설. 싱글-헐 SSBN 건조.",
            "source": "GlobalSecurity Sinpo/Mayang-do, CSIS",
        },
        "chaho": {
            "name_ko": "차호 잠수함기지",
            "lat": 40.210, "lon": 128.649,
            "fleet": "동해함대",
            "type": "동굴 엄폐형 잠수함기지",
            "source": "GlobalSecurity Ch'aho Naval Base",
        },
        "wonsan": {
            "name_ko": "원산 해군기지",
            "lat": 39.342, "lon": 127.423,
            "fleet": "동해함대",
            "source": "GlobalSecurity",
        },
        "nampo": {
            "name_ko": "남포 해군기지",
            "lat": 38.730, "lon": 125.390,
            "fleet": "서해함대",
            "notes": "서해함대 사령부 인근",
            "source": "Wikipedia Korean People's Navy",
        },
        "najin": {
            "name_ko": "나진 해군기지",
            "lat": 42.260, "lon": 130.320,
            "fleet": "동해함대 북부",
            "notes": "러시아 국경 ~30km",
            "source": "GlobalSecurity Najin Naval Base",
        },
        "haeju": {
            "name_ko": "해주 해군기지",
            "lat": 37.978, "lon": 125.699,
            "fleet": "서해함대",
            "source": "GlobalSecurity",
        },
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 공군 기지
    # ─────────────────────────────────────────────────────────────────────────
    "air_bases": {
        "sunan":   {"name_ko": "순안비행장 (평양국제공항)",  "lat": 39.409, "lon": 125.895, "notes": "민군 겸용"},
        "onchon":  {"name_ko": "온천비행장",                 "lat": 38.891, "lon": 125.238, "notes": "동굴형 활주로 연결"},
        "hwangju": {"name_ko": "황주공군기지",               "lat": 38.654, "lon": 125.789},
        "sunchon": {"name_ko": "순천비행장",                 "lat": 39.744, "lon": 125.928},
        "wonsan_ab":{"name_ko": "원산 갈마비행장",           "lat": 39.166, "lon": 127.486},
        "uiju":    {"name_ko": "의주비행장",                 "lat": 40.152, "lon": 124.481, "notes": "중국 국경 인근"},
    },
}


# =============================================================================
#  Part 5. 주요 해협 종합 (STRAITS_DB)
# =============================================================================

STRAITS_DB = {
    "korea_west":   {"name_ko": "대한해협 서수도", "width_km": 49.5, "depth_max_m": 227, "sill_m": 130},
    "korea_east":   {"name_ko": "대한해협 동수도", "width_km": 98,   "depth_max_m": 120, "sill_m": 115},
    "jeju":         {"name_ko": "제주해협",         "width_km": 85,   "depth_max_m": 140},
    "tsugaru":      {"name_ko": "쓰가루해협",       "width_km": 20,   "depth_max_m": 450, "notes": "러시아 태평양함대 주요 통로"},
    "soya":         {"name_ko": "소야해협",         "width_km": 40,   "depth_range_m": (30, 70), "notes": "동해↔오호츠크해"},
    "bohai":        {"name_ko": "보하이 해협",      "width_km": 90,   "depth_avg_m": 20},
}


# =============================================================================
#  편의 함수
# =============================================================================

def get_max_submarine_depth(sea_key: str) -> int:
    """해역별 지형 제한 잠수함 최대 잠항 수심(m) 반환"""
    ops = BATHYMETRY_DB.get(sea_key, {}).get("submarine_ops", {})
    return ops.get("max_practical_depth_m") or ops.get("max_depth_terrain_limit_m", 0)


def thermocline_viable(sea_key: str) -> bool:
    """해역에서 수온약층 형성으로 잠수함 소나 회피가 가능한지 여부"""
    ops = BATHYMETRY_DB.get(sea_key, {}).get("submarine_ops", {})
    return bool(ops.get("thermocline_possible", False))


def get_radar_shadow_angle(range_name: str) -> float:
    """레이더 음영각(도) 반환"""
    ref = TERRAIN_DB["radar_shadow_reference"]
    return ref.get(range_name, {}).get("shadow_angle_deg", 0.0)
