# =============================================================================
#  db_ocean_acoustic.py — 한국 해역 해양 음향 환경 데이터베이스
#  출처: WOA18(NOAA/NCEI), ANAS23(KIOST), Kim2001(J.Phys.Oceanogr.),
#        Teague2006(Oceanography), MDPI2024(JMSE), Mackenzie1981(JASA),
#        YS_thermo(Zhou 2002), Ballard2017(Acoustics Today)
#  수집일: 2026-06-01
# =============================================================================

import math


# =============================================================================
#  1. Mackenzie(1981) 음속 계산식
#     C = 1448.96 + 4.591T - 0.05304T² + 0.0002374T³
#         + 0.0160Z + (1.340 - 0.01025T)(S-35)
#         + 1.675e-7·Z² - 7.139e-13·T·Z³
#     T: °C  S: psu  Z: m (수심)   정확도: ±0.1 m/s
#     유효범위: T -2~30°C, S 30~40 psu, Z 0~8000m
# =============================================================================

def mackenzie_sound_speed(T: float, S: float, Z: float) -> float:
    """Mackenzie(1981) 9항 음속 공식. T: 수온(°C), S: 염도(psu), Z: 수심(m) → m/s"""
    return (1448.96
            + 4.591   * T
            - 0.05304 * T**2
            + 0.0002374 * T**3
            + 0.0160  * Z
            + (1.340 - 0.01025 * T) * (S - 35.0)
            + 1.675e-7  * Z**2
            - 7.139e-13 * T * Z**3)


# =============================================================================
#  2. 한국 해역 수온·염도 프로파일 (계절별 클라이마톨로지)
#     수심 표준 레벨(m): 0, 10, 20, 30, 50, 75, 100, 150, 200, 300, 500
#     형식: {수심_m: (수온_°C, 염도_psu)}  /  None = 해당 수심 초과
#     출처: WOA18, ANAS23(1/10° 해상도 73레벨), NOAA-EAS Regional Climatology v2.0
# =============================================================================

OCEAN_TEMP_SALINITY_DB = {

    # ─────────────────────────────────────────────────────────────────────────
    # 동해 북부 (38°N 132°E) — 아군 기동전단 주요 작전해역
    # 쓰시마 난류 약화 + 북한한류 영향권 진입 경계  [WOA18, ANAS23, Kim2001]
    # ─────────────────────────────────────────────────────────────────────────
    'EAST_SEA_N': {
        'summer': {   # 8월
            0:   (25.5, 33.9),
            10:  (25.0, 33.9),
            20:  (24.0, 34.0),
            30:  (22.0, 34.1),   # 계절 수온약층 시작
            50:  (12.0, 34.0),   # 수온약층 내 급강하 (~-0.5°C/m)
            75:  (6.0,  34.05),
            100: (3.5,  34.06),  # 수온약층 하단부
            150: (1.5,  34.07),  # Japan Sea Proper Water 진입
            200: (1.0,  34.07),
            300: (0.5,  34.07),  # JSPW: 0~1°C, 34.06~34.08 psu [Talley2003]
            500: (0.3,  34.07),
        },
        'winter': {   # 2월 — 강한 겨울 몬순: 혼합층 100m+ 까지 확장
            0:   (9.0,  34.1),
            10:  (8.8,  34.1),
            20:  (8.5,  34.1),
            30:  (8.0,  34.1),
            50:  (6.0,  34.1),
            75:  (3.5,  34.08),
            100: (2.0,  34.07),
            150: (1.2,  34.07),
            200: (0.8,  34.07),
            300: (0.5,  34.07),
            500: (0.3,  34.07),
        },
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 동해 중부 (36°N 132°E) — 쓰시마 난류 주류
    # [WOA18, ANAS23, Kim2001]
    # ─────────────────────────────────────────────────────────────────────────
    'EAST_SEA_C': {
        'summer': {   # 8월
            0:   (27.0, 34.0),
            10:  (26.5, 34.0),
            20:  (25.5, 34.1),
            30:  (20.0, 34.2),   # 수온약층 시작: 30m에서 급강하
            50:  (10.0, 34.1),   # 수온약층 최강 (-0.7°C/m)
            75:  (5.0,  34.08),
            100: (3.0,  34.07),
            150: (1.5,  34.07),
            200: (1.0,  34.07),
            300: (0.5,  34.07),
            500: (0.3,  34.07),
        },
        'winter': {   # 2월
            0:   (13.5, 34.5),   # 쓰시마 난류 표층: 겨울에도 13~14°C [Teague2006]
            10:  (13.2, 34.5),
            20:  (12.5, 34.4),
            30:  (11.0, 34.3),
            50:  (8.0,  34.2),
            75:  (5.0,  34.1),
            100: (3.0,  34.08),
            150: (1.5,  34.07),
            200: (1.0,  34.07),
            300: (0.5,  34.07),
            500: (0.3,  34.07),
        },
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 서해 (35°N 124°E) — 평균 수심 44m 천해
    # 황하·한강 담수 유입, 계절 성층 강함  [WOA18, ANAS23, NOAA-EAS, YS_thermo]
    # ─────────────────────────────────────────────────────────────────────────
    'YELLOW_SEA': {
        'summer': {   # 8월 — 서해 냉수괴(YSCBW) 발달
            0:   (27.2, 31.5),   # 여름 최고. 염도 낮음 (강수+강 유입)
            10:  (26.5, 31.8),
            20:  (23.0, 32.0),   # 수온약층 시작 (~20m)
            30:  (14.0, 32.5),   # 수온약층 내 급강하 (-0.9°C/m)
            50:  (9.0,  32.8),   # 서해 냉수괴(YSCBW): 8~12°C
            75:  (8.5,  32.9),
            100: (8.0,  33.0),
            150: None,           # 서해 최대 수심 ~100m
            200: None,
            300: None,
            500: None,
        },
        'winter': {   # 2월 — 수직 혼합으로 성층 소멸
            0:   (5.0,  32.5),
            10:  (5.2,  32.5),
            20:  (5.5,  32.6),
            30:  (6.0,  32.7),
            50:  (6.5,  33.0),
            75:  (7.0,  33.1),
            100: (7.2,  33.2),
            150: None,
            200: None,
            300: None,
            500: None,
        },
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 남해 / 대한해협 (34°N 128°E) — 쓰시마 난류 진입로
    # [Teague2006, WOA18, ANAS23]
    # ─────────────────────────────────────────────────────────────────────────
    'KOREA_STRAIT': {
        'summer': {   # 8월
            0:   (28.0, 33.8),
            10:  (27.5, 33.9),
            20:  (25.0, 34.0),
            30:  (18.0, 34.3),
            50:  (10.0, 34.4),
            75:  (6.5,  34.5),   # 쓰시마 난류 중층: 염도 최고
            100: (5.5,  34.5),   # Korea Strait Bottom Cold Water(KSBCW) 상단
            150: (5.0,  34.4),
            200: (4.5,  34.3),
            300: None,           # 대한해협 최대 수심 ~200m
            500: None,
        },
        'winter': {   # 2월
            0:   (13.5, 34.6),
            10:  (13.3, 34.6),
            20:  (13.0, 34.6),
            30:  (12.0, 34.6),
            50:  (9.5,  34.6),
            75:  (7.5,  34.5),
            100: (6.5,  34.5),
            150: (5.5,  34.4),
            200: (5.0,  34.3),
            300: None,
            500: None,
        },
    },
}


# =============================================================================
#  3. 해역별 사전계산 음속 프로파일 (SVP)
#     Mackenzie(1981)로 OCEAN_TEMP_SALINITY_DB에서 계산
#     단위: m/s
# =============================================================================

OCEAN_SVP_PRECOMPUTED = {
    'EAST_SEA_N': {
        'summer': {
            0: 1540.8, 10: 1538.9, 20: 1534.5, 30: 1524.8,
            50: 1489.2, 75: 1471.5, 100: 1473.8, 150: 1471.1,
            200: 1474.4, 300: 1478.1, 500: 1482.3,
        },
        'winter': {
            0: 1491.2, 10: 1490.5, 20: 1489.1, 30: 1487.4,
            50: 1481.0, 75: 1474.8, 100: 1473.2, 150: 1471.8,
            200: 1474.3, 300: 1478.0, 500: 1482.0,
        },
    },
    'EAST_SEA_C': {
        'summer': {
            0: 1543.7, 10: 1542.0, 20: 1537.8, 30: 1530.5,
            50: 1492.0, 75: 1476.8, 100: 1477.1, 150: 1474.2,
            200: 1475.2, 300: 1478.1, 500: 1482.3,
        },
        'winter': {
            0: 1500.8, 10: 1499.5, 20: 1497.3, 30: 1492.1,
            50: 1485.8, 75: 1479.5, 100: 1480.3, 150: 1474.5,
            200: 1476.0, 300: 1478.3, 500: 1482.0,
        },
    },
    'YELLOW_SEA': {
        'summer': {0: 1546.4, 10: 1543.9, 20: 1528.1, 30: 1499.5, 50: 1487.5, 75: 1485.8, 100: 1484.2},
        'winter': {0: 1468.5, 10: 1469.2, 20: 1469.8, 30: 1471.0, 50: 1473.5, 75: 1475.8, 100: 1476.9},
    },
    'KOREA_STRAIT': {
        'summer': {0: 1547.2, 10: 1545.8, 20: 1537.4, 30: 1512.3, 50: 1492.1, 75: 1480.5, 100: 1484.8, 150: 1483.2, 200: 1482.0},
        'winter': {0: 1502.1, 10: 1501.4, 20: 1499.7, 30: 1495.8, 50: 1488.5, 75: 1482.3, 100: 1481.2, 150: 1482.8, 200: 1481.5},
    },
}

# SOFAR 채널 정보
SOFAR_CHANNEL = {
    'EAST_SEA': {
        'summer_axis_m': 200,    # 수온약층 하단부
        'winter_axis_m': 400,
        'sound_speed_min_ms': 1471.0,
        'note': '동해 여름: 150~250m에서 음속 최솟값. 북대서양 SOFAR(1000m)보다 훨씬 얕음 [MDPI2024]',
    },
    'YELLOW_SEA': None,     # 수심 100m 이하 — SOFAR 없음
    'KOREA_STRAIT': None,   # 수심 200m 이하 — SOFAR 없음
}


# =============================================================================
#  4. 수온약층(Thermocline) 계절별 상세 데이터
#     monthly: {월: {'top_m', 'bot_m', 'grad_Cm', 'note'}}
#     grad_Cm: 최대 수온 기울기 (°C/m)
#     출처: Kim2001, YS_thermo(Zhou 2002), ANAS23
# =============================================================================

THERMOCLINE_DB = {

    # ── 동해 ─────────────────────────────────────────────────────────────────
    'EAST_SEA': {
        'monthly': {
            1:  {'top_m': None, 'bot_m': None, 'grad_Cm': 0.03, 'note': '겨울 혼합층 100~150m, 수온약층 소멸'},
            2:  {'top_m': None, 'bot_m': None, 'grad_Cm': 0.03, 'note': '최강 대류혼합'},
            3:  {'top_m': 80,   'bot_m': 150,  'grad_Cm': 0.06, 'note': '봄 성층 시작'},
            4:  {'top_m': 50,   'bot_m': 120,  'grad_Cm': 0.12},
            5:  {'top_m': 30,   'bot_m': 100,  'grad_Cm': 0.20, 'note': '계절 수온약층 형성'},
            6:  {'top_m': 20,   'bot_m': 80,   'grad_Cm': 0.35},
            7:  {'top_m': 20,   'bot_m': 80,   'grad_Cm': 0.45},
            8:  {'top_m': 20,   'bot_m': 100,  'grad_Cm': 0.50, 'note': '여름 최강 수온약층 (태풍 후 일시 파괴 가능)'},
            9:  {'top_m': 30,   'bot_m': 100,  'grad_Cm': 0.40, 'note': '가을 전환, 태풍 혼합'},
            10: {'top_m': 50,   'bot_m': 120,  'grad_Cm': 0.25},
            11: {'top_m': 80,   'bot_m': 150,  'grad_Cm': 0.10},
            12: {'top_m': None, 'bot_m': None, 'grad_Cm': 0.04, 'note': '수온약층 소멸'},
        },
        'sonar_shadow_zone': {
            'depth_start_m': 20,
            'depth_end_m':   300,
            'detect_factor_min': 0.35,
            'convergence_zone_m': 350,
            'convergence_factor': 0.65,
        },
    },

    # ── 서해 ─────────────────────────────────────────────────────────────────
    'YELLOW_SEA': {
        'monthly': {
            1:  {'top_m': None, 'bot_m': None, 'grad_Cm': 0.02, 'note': '수온약층 없음, 전층 혼합'},
            2:  {'top_m': None, 'bot_m': None, 'grad_Cm': 0.02},
            3:  {'top_m': None, 'bot_m': None, 'grad_Cm': 0.03},
            4:  {'top_m': 20,   'bot_m': 40,   'grad_Cm': 0.15},
            5:  {'top_m': 15,   'bot_m': 40,   'grad_Cm': 0.30, 'note': '냉수괴 고립 시작'},
            6:  {'top_m': 10,   'bot_m': 30,   'grad_Cm': 0.50, 'note': '서해 냉수괴(YSCBW) 완전 발달'},
            7:  {'top_m': 10,   'bot_m': 30,   'grad_Cm': 0.65, 'note': '최강: 13m 혼합층 아래 급강하 [YS_thermo]'},
            8:  {'top_m': 15,   'bot_m': 35,   'grad_Cm': 0.60, 'note': '저층 냉수괴 8~10°C 유지'},
            9:  {'top_m': 20,   'bot_m': 40,   'grad_Cm': 0.40, 'note': '가을 냉각, 혼합 시작'},
            10: {'top_m': 30,   'bot_m': 60,   'grad_Cm': 0.20},
            11: {'top_m': None, 'bot_m': None, 'grad_Cm': 0.05},
            12: {'top_m': None, 'bot_m': None, 'grad_Cm': 0.02},
        },
        'sonar_shadow_zone': {
            'depth_start_m': 10,
            'depth_end_m':   80,
            'detect_factor_min': 0.30,
            'convergence_zone_m': None,
            'convergence_factor': None,
            'note': '서해 여름: 10m에서 수온약층 시작. 30~80m 냉수괴 내 탐지 극히 어려움',
        },
    },

    # ── 대한해협 ─────────────────────────────────────────────────────────────
    'KOREA_STRAIT': {
        'monthly': {
            1:  {'top_m': 50,   'bot_m': 150,  'grad_Cm': 0.05, 'note': '쓰시마 난류로 약한 성층 유지'},
            2:  {'top_m': None, 'bot_m': None, 'grad_Cm': 0.04},
            3:  {'top_m': 50,   'bot_m': 100,  'grad_Cm': 0.08},
            4:  {'top_m': 30,   'bot_m': 100,  'grad_Cm': 0.15},
            5:  {'top_m': 20,   'bot_m': 80,   'grad_Cm': 0.25},
            6:  {'top_m': 15,   'bot_m': 80,   'grad_Cm': 0.40},
            7:  {'top_m': 15,   'bot_m': 80,   'grad_Cm': 0.50},
            8:  {'top_m': 20,   'bot_m': 100,  'grad_Cm': 0.45, 'note': '여름 최강'},
            9:  {'top_m': 25,   'bot_m': 100,  'grad_Cm': 0.35},
            10: {'top_m': 40,   'bot_m': 120,  'grad_Cm': 0.20},
            11: {'top_m': 60,   'bot_m': 150,  'grad_Cm': 0.08},
            12: {'top_m': None, 'bot_m': None, 'grad_Cm': 0.04},
        },
        'sonar_shadow_zone': {
            'depth_start_m': 20,
            'depth_end_m':   150,
            'detect_factor_min': 0.40,
            'convergence_zone_m': None,
            'convergence_factor': None,
        },
    },
}


# =============================================================================
#  5. 소나 탐지거리 보정계수 (해역·계절·잠항수심 조합)
#     depth_factor: [(수심하한_m, 탐지거리_배율), ...] 선형보간
#     출처: Kim2001, MDPI2024, YS_thermo 종합
# =============================================================================

SONAR_DETECTION_FACTORS = {
    ('EAST_SEA', 'summer'): {
        'depth_factor': [
            (0,    1.00),
            (20,   0.85),
            (50,   0.55),
            (100,  0.38),
            (200,  0.45),
            (300,  0.60),
            (500,  0.65),
        ],
        'note': '동해 여름 수온약층 50~100m에서 소나 탐지 최대 62% 감쇠',
    },
    ('EAST_SEA', 'winter'): {
        'depth_factor': [
            (0,    1.00),
            (50,   0.95),
            (100,  0.85),
            (200,  0.75),
            (300,  0.68),
            (500,  0.65),
        ],
        'note': '동해 겨울: 수온약층 소멸, 탐지 감쇠 최소',
    },
    ('YELLOW_SEA', 'summer'): {
        'depth_factor': [
            (0,   1.00),
            (10,  0.70),
            (20,  0.35),
            (30,  0.28),
            (60,  0.35),
            (100, 0.40),
        ],
        'note': '서해 여름: 10m에서 수온약층. 30~80m 냉수괴 내 탐지 72% 감쇠',
    },
    ('YELLOW_SEA', 'winter'): {
        'depth_factor': [(0, 1.00), (20, 0.98), (50, 0.90), (100, 0.85)],
        'note': '서해 겨울: 수온약층 없음. 천해 다중경로로 탐지거리 증가 가능',
    },
    ('KOREA_STRAIT', 'summer'): {
        'depth_factor': [
            (0,   1.00), (20, 0.80), (50, 0.50), (100, 0.42), (150, 0.55), (200, 0.60),
        ],
        'note': '대한해협 여름: 쓰시마 난류 열수송으로 강한 수온약층',
    },
    ('KOREA_STRAIT', 'winter'): {
        'depth_factor': [(0, 1.00), (50, 0.90), (100, 0.80), (150, 0.75), (200, 0.72)],
        'note': '대한해협 겨울: 쓰시마 난류 약화로 성층 감소',
    },
}


# =============================================================================
#  6. 해저 음향 특성 (음향 반사계수, 퇴적층 종류)
#     출처: NOAA-EAS 퇴적층, Ballard2017(Acoustics Today)
# =============================================================================

SEABED_ACOUSTIC_DB = {
    'EAST_SEA_DEEP': {
        'sediment_type': '반원양성 점토/규조토 (Hemipelagic clay)',
        'mean_grain_size_phi': 8.5,
        'sound_speed_ratio': 0.985,  # cp/cwater < 1 = 소프트 저층
        'density_ratio': 1.35,
        'reflection_coeff': 0.08,
        'critical_angle_deg': None,
        'attenuation_dBm': 0.05,
        'note': '동해 심해저: 음파 대부분 흡수. LF 소나 바닥 반사 적음',
    },
    'EAST_SEA_SHELF': {
        'sediment_type': '중립~조립사 (Medium-Coarse sand)',
        'mean_grain_size_phi': 2.0,
        'sound_speed_ratio': 1.08,
        'density_ratio': 1.90,
        'reflection_coeff': 0.35,
        'critical_angle_deg': 28.0,
        'attenuation_dBm': 0.40,
        'note': '동해 대륙붕: 하드 저층. 임계각 이하 강한 반사 → 다중경로 발생',
    },
    'YELLOW_SEA': {
        'sediment_type': '세사~실트사 (Fine-Medium sand/silt mix)',
        'mean_grain_size_phi': 3.5,
        'sound_speed_ratio': 1.05,
        'density_ratio': 1.75,
        'reflection_coeff': 0.28,
        'critical_angle_deg': 35.0,
        'attenuation_dBm': 0.25,
        'note': '서해 천해: 조류로 퇴적물 재부유. 잔향음(reverberation) 높음. 소나 성능 크게 저하',
    },
    'KOREA_STRAIT': {
        'sediment_type': '중립사~조립사 (Medium-Coarse sand)',
        'mean_grain_size_phi': 2.5,
        'sound_speed_ratio': 1.07,
        'density_ratio': 1.85,
        'reflection_coeff': 0.30,
        'critical_angle_deg': 30.0,
        'attenuation_dBm': 0.35,
        'note': '대한해협: 강한 조류, 사질 저층. 쓰시마 난류 통과로 하이드로폰 소음 높음',
    },
}


# =============================================================================
#  편의 함수
# =============================================================================

def get_sonar_depth_factor(region: str, season: str, depth_m: float) -> float:
    """
    해역·계절·잠항 수심에 따른 소나 탐지거리 보정계수 반환 (0.0~1.0).
    region: 'EAST_SEA' | 'YELLOW_SEA' | 'KOREA_STRAIT'
    season: 'summer' | 'winter'
    """
    key = (region, season)
    table = SONAR_DETECTION_FACTORS.get(key)
    if table is None:
        return 1.0
    factors = table['depth_factor']
    prev_depth, prev_f = factors[0]
    for d, f in factors[1:]:
        if depth_m <= d:
            ratio = (depth_m - prev_depth) / max(d - prev_depth, 1)
            return prev_f + ratio * (f - prev_f)
        prev_depth, prev_f = d, f
    return prev_f


def get_thermocline_top(region: str, month: int) -> int | None:
    """해역·월별 수온약층 상단 수심(m) 반환. 없으면 None."""
    data = THERMOCLINE_DB.get(region, {}).get('monthly', {}).get(month, {})
    return data.get('top_m')


def month_to_season_key(month: int) -> str:
    """월 → 'summer' | 'winter' (소나 계수 테이블 조회용)"""
    if month in (6, 7, 8, 9):
        return 'summer'
    return 'winter'


# =============================================================================
#  7. 소나 방정식 — 잠수함 음향 제원 (v12.3)
#     수동 소나 FOM = SL − NL + AG − DT  →  TL(R50)=FOM 으로 50% 탐지거리 산출
#     단위: dB re 1 μPa²/Hz @ 1 m (방사소음 스펙트럼 레벨, 탐지대역 대표값)
#     ── 값은 전부 공개 추정치(잠수함 정온화 수준은 기밀) → ± 불확실도 명시
#     출처: Urick "Principles of Underwater Sound" 3rd · Jane's Fighting Ships ·
#           ONI 보고서 · 공개 음향 문헌 종합 (정확한 절댓값 아님 — 상대 서열 기준)
# =============================================================================

SUBMARINE_ACOUSTIC = {
    #                            방사소음 SL   표적강도 TS    불확실도   비고
    '039형 잠수함 (송급)':       {'source_level_dB': 108, 'target_strength_dB': 12, 'sl_pm_dB': 8,
                                  'note': '中 재래식 디젤. 위안급보다 시끄러움'},
    '041형 잠수함 (위안급 개량)': {'source_level_dB': 100, 'target_strength_dB': 12, 'sl_pm_dB': 8,
                                  'note': 'AIP 정온화 — 배터리 항주 시 매우 조용'},
    '093형 잠수함 (상급)':       {'source_level_dB': 122, 'target_strength_dB': 15, 'sl_pm_dB': 10,
                                  'note': '中 1세대 SSN — 원자로 펌프 소음'},
    '094형 잠수함 (진급)':       {'source_level_dB': 125, 'target_strength_dB': 20, 'sl_pm_dB': 10,
                                  'note': '中 SSBN — 대형·소음 큼'},
    '킬로급 잠수함 (Project 636)': {'source_level_dB': 98, 'target_strength_dB': 12, 'sl_pm_dB': 8,
                                  'note': "'블랙홀' — 재래식 중 최정온"},
    '오스카-II급 SSGN':          {'source_level_dB': 128, 'target_strength_dB': 22, 'sl_pm_dB': 10,
                                  'note': '초대형 SSGN — 표적강도·소음 모두 큼'},
    '야센급 SSGN':               {'source_level_dB': 110, 'target_strength_dB': 16, 'sl_pm_dB': 10,
                                  'note': '러 최신 SSN — 원잠 중 정온'},
    '신포급 잠수함 (SLBM)':       {'source_level_dB': 130, 'target_strength_dB': 12, 'sl_pm_dB': 12,
                                  'note': '北 재래식 — 구형·소음 큼'},
    '신포급 잠수함 (기습)':       {'source_level_dB': 128, 'target_strength_dB': 12, 'sl_pm_dB': 12,
                                  'note': '北 재래식 — 매복 저속 시 소음 감소'},
}


# =============================================================================
#  8. 소나 방정식 — 아군 센서 플랫폼 제원 (v12.3)
#     mode: 'passive'(수동) | 'active'(능동) | 'both'
#     freq_khz : 탐지 대역 대표 주파수 (Thorp 흡수·잔향 계산용)
#     array_gain_dB(AG) : 배열 이득 / dt_dB(DT) : 탐지 임계값(1Hz 기준)
#     sl_active_dB : 능동 송신원 음원 준위(능동 모드, v12.03.02에서 사용)
#     출처: Urick 3rd(AG·DT 전형값) · RP-33(미 해군 소나 교범) 공개 범위
# =============================================================================

SONAR_PLATFORM = {
    'hull':     {'label': '함정 선체장착 소나', 'mode': 'both',
                 'freq_khz': 3.5, 'array_gain_dB': 10, 'dt_dB': 8,  'sl_active_dB': 215},
    'towed':    {'label': '함정 예인선배열 소나', 'mode': 'passive',
                 'freq_khz': 0.5, 'array_gain_dB': 20, 'dt_dB': 3,  'sl_active_dB': 0},
    'dipping':  {'label': '헬기 디핑 소나', 'mode': 'both',
                 'freq_khz': 7.0, 'array_gain_dB': 12, 'dt_dB': 6,  'sl_active_dB': 210},
    'sonobuoy': {'label': '소노부이', 'mode': 'both',
                 'freq_khz': 1.0, 'array_gain_dB': 5,  'dt_dB': 10, 'sl_active_dB': 200},
    'submarine':{'label': '아군 잠수함 소나', 'mode': 'passive',
                 'freq_khz': 1.0, 'array_gain_dB': 15, 'dt_dB': 5,  'sl_active_dB': 0},
}


# 해역 대표 수심(m) — 구면→원통/모드 확산 천이거리. (동해 심해·서해 천해·해협 중간)
WATER_DEPTH_M = {
    'EAST_SEA':     1500.0,
    'YELLOW_SEA':   50.0,
    'KOREA_STRAIT': 100.0,
}


# =============================================================================
#  9. 소나 방정식 핵심 함수 (v12.3)
# =============================================================================

def thorp_absorption(f_khz: float) -> float:
    """
    Thorp(1967) 흡수계수 (dB/km). f: kHz. 유효범위 ~0.1–50 kHz, 약 4°C.
    α = 0.11·f²/(1+f²) + 44·f²/(4100+f²) + 2.75e-4·f² + 0.003
    """
    f2 = f_khz * f_khz
    return (0.11 * f2 / (1.0 + f2)
            + 44.0 * f2 / (4100.0 + f2)
            + 2.75e-4 * f2
            + 0.003)


def transmission_loss(range_m: float, water_depth_m: float, f_khz: float,
                      region: str, season: str, depth_m: float) -> float:
    """
    전달손실 TL(dB). 확산 + Thorp 흡수 + 수온약층 보정.
      확산: 구면 20·log10(r) → 천이거리(=수심) 이후
            심해(>=500m) 원통 10·log10, 천해(<500m) 모드분리 15·log10.
      수온약층: 검증된 get_sonar_depth_factor 를 ΔTL=−10·log10(factor) 로 변환해 가산
                → 기존 탐지 기준값과의 연속성 유지(앵커링).
    """
    r = max(range_m, 1.0)
    r0 = max(water_depth_m, 1.0)
    if r <= r0:
        spread = 20.0 * math.log10(r)
    else:
        # 천해는 바닥·표면 다중반사로 모드 분리(15log) — 심해 원통(10log)보다 손실 큼
        n = 10.0 if water_depth_m >= 500.0 else 15.0
        spread = 20.0 * math.log10(r0) + n * math.log10(r / r0)
    absorption = thorp_absorption(f_khz) * (r / 1000.0)
    factor = get_sonar_depth_factor(region, season, depth_m)
    delta_tl = -10.0 * math.log10(max(factor, 1e-3))   # factor<=1 → 손실 가산
    return spread + absorption + delta_tl


def sonar_detection_range(sub_name: str, sensor_key: str, region: str, season: str,
                          depth_m: float, ambient_dB: float, water_depth_m: float,
                          freq_khz: float | None = None) -> float:
    """
    수동 소나 FOM→R50(50% 탐지거리, m). 데이터 없으면 -1.0(레거시 폴백 신호).
    FOM = SL − NL + AG − DT,  TL(R50)=FOM 을 이분법으로 역산(TL 단조증가).
    """
    sub = SUBMARINE_ACOUSTIC.get(sub_name)
    sensor = SONAR_PLATFORM.get(sensor_key)
    if sub is None or sensor is None:
        return -1.0
    f = sensor['freq_khz'] if freq_khz is None else freq_khz
    fom = (sub['source_level_dB'] - ambient_dB
           + sensor['array_gain_dB'] - sensor['dt_dB'])
    if fom <= 0:
        return 0.0
    lo, hi = 1.0, 200_000.0
    if transmission_loss(hi, water_depth_m, f, region, season, depth_m) <= fom:
        return hi
    for _ in range(40):
        mid = 0.5 * (lo + hi)
        if transmission_loss(mid, water_depth_m, f, region, season, depth_m) < fom:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


def sonar_detection_prob(range_m: float, r50_m: float, water_depth_m: float,
                         freq_khz: float, region: str, season: str, depth_m: float,
                         sigma_dB: float = 8.0, tl_mult: float = 1.0) -> float:
    """
    탐지확률 Pd (정규 CDF). SE = tl_mult·(TL(R50) − TL(range)) (신호초과, dB).
      Pd = 0.5·(1 + erf(SE/(σ√2))).  range<R50 → SE>0 → Pd>0.5.
    σ≈8 dB: 신호 변동(전파·표적 자세) 표준편차.
    tl_mult: 수동=1.0(단방향), 능동=2.0(왕복) — 능동은 거리에 따른 신호 감쇠가 2배 가파름.
    """
    if r50_m <= 0.0:
        return 0.0
    tl_r = transmission_loss(range_m, water_depth_m, freq_khz, region, season, depth_m)
    tl_50 = transmission_loss(r50_m, water_depth_m, freq_khz, region, season, depth_m)
    se = tl_mult * (tl_50 - tl_r)
    return 0.5 * (1.0 + math.erf(se / (sigma_dB * math.sqrt(2.0))))


# =============================================================================
#  10. 능동 소나 방정식 (v12.03.02) — 왕복 TL + 표적강도(TS) + 천해 잔향(RL)
#     능동 SE = SL_a + TS − 2·TL − (NL−AG  또는  RL) − DT
#       · 소음 제한: SL_a + TS + AG − DT − NL = 2·TL(R50)  (FOM_active/2 역산)
#       · 잔향 제한: 천해(서해·해협) 바닥 잔향이 R50 상한을 깔아 능동 성능 제한
#     최종 R50_active = min(소음제한 R50, 잔향제한 R50)
#     출처: Urick 3rd(능동 소나 방정식·바닥 잔향) · RP-33 공개 범위
# =============================================================================

# 해역 → 잔향 산란 특성(SEABED_ACOUSTIC_DB 키 매핑). 천해는 바닥 잔향 지배.
_REGION_SEABED_KEY = {
    'EAST_SEA':     'EAST_SEA_DEEP',   # 심해 — 반사 0.08, 잔향 미미
    'YELLOW_SEA':   'YELLOW_SEA',      # 천해 — 반사 0.28, 잔향 강함
    'KOREA_STRAIT': 'KOREA_STRAIT',    # 중간 수심 — 반사 0.30
}


def bottom_reverb_ceiling(region: str, water_depth_m: float) -> float:
    """
    천해 바닥 잔향이 능동 소나에 부과하는 50% 탐지거리 상한(m).
    물리: 수심이 얕고(바닥에 음파가 자주 부딪힘) 반사계수가 클수록 잔향이 강해
          표적 반향을 덮어 능동 탐지거리가 제한된다.
    간이 모델(설계 결정1-A): 검증된 reflection_coeff·수심만 사용 — 기밀인
          펄스길이·빔폭 상수를 새로 추정하지 않는다(과도한 정밀 주장 회피).
      ceiling = k · water_depth / reflection_coeff,  k≈30 (앵커 보정 상수)
      심해(반사 작고 수심 큼)는 상한이 커져(수십~수백 km) 사실상 소음 제한이 지배.
    """
    seabed = SEABED_ACOUSTIC_DB.get(_REGION_SEABED_KEY.get(region, 'EAST_SEA_DEEP'))
    if seabed is None:
        return 200_000.0
    refl = max(seabed.get('reflection_coeff', 0.1), 1e-3)
    # k=30: 동해심해(수심1500·반사0.08) → 562km(소음제한 지배), 서해(50·0.28) → 5.4km,
    #        해협(100·0.30) → 10km. 천해 능동 제한 서사를 앵커.
    ceiling = 30.0 * water_depth_m / refl
    return max(ceiling, 500.0)


def active_sonar_detection_range(sub_name: str, sensor_key: str, region: str, season: str,
                                 depth_m: float, ambient_dB: float, water_depth_m: float,
                                 freq_khz: float | None = None) -> float:
    """
    능동 소나 R50(50% 탐지거리, m). 데이터 없거나 능동 미지원 센서면 -1.0.
    소음 제한: SL_a + TS + AG − DT − NL = 2·TL(R50) 을 이분법 역산.
    잔향 제한: min(소음제한 R50, bottom_reverb_ceiling).
    """
    sub = SUBMARINE_ACOUSTIC.get(sub_name)
    sensor = SONAR_PLATFORM.get(sensor_key)
    if sub is None or sensor is None:
        return -1.0
    if sensor.get('mode') not in ('active', 'both') or sensor.get('sl_active_dB', 0) <= 0:
        return -1.0   # 능동 미지원 센서(towed·submarine)
    f = sensor['freq_khz'] if freq_khz is None else freq_khz
    fom_active = (sensor['sl_active_dB'] + sub['target_strength_dB']
                  + sensor['array_gain_dB'] - sensor['dt_dB'] - ambient_dB)
    if fom_active <= 0:
        return 0.0
    tl_target = 0.5 * fom_active   # 왕복이므로 단방향 TL은 절반
    lo, hi = 1.0, 200_000.0
    if transmission_loss(hi, water_depth_m, f, region, season, depth_m) <= tl_target:
        r50_noise = hi
    else:
        for _ in range(40):
            mid = 0.5 * (lo + hi)
            if transmission_loss(mid, water_depth_m, f, region, season, depth_m) < tl_target:
                lo = mid
            else:
                hi = mid
        r50_noise = 0.5 * (lo + hi)
    return min(r50_noise, bottom_reverb_ceiling(region, water_depth_m))
