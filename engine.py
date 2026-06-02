"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   이지스 기동전단 통합 방어 시뮬레이터  v6.8.4                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  [v6.8.4 — HeloEvent is_missile 오류 완전 수정·MH-60R 제거]                 ║
║                                                                              ║
║  BUG-1~3  v6.8.1 패치 유지                                                   ║
║  BUG-4  normalize_enemy_db() 로 플랫폼 terminal_evasion_factor 자동 설정    ║
║  BUG-5  missile_salvo_fixed 범위 초과 경고 추가                              ║
║  BUG-6  monte_carlo 독립 ShipStatus 집계 (mc_hit_avg / save_nth)            ║
║  NEW-F  적 자체 방어 v6.8.1 유지                                              ║
║  NEW-G  ECM 재밍 시스템 (ecm_power, 거리 반비례, enable_ecm)                ║
║  NEW-H  함재 헬기 (AW-159/MH-60R, HeloEvent, 날씨 출격제한, enable_helo)    ║
║  미구현-1~5 구현 완료: 종말회피 인수·current_depth·MC 샘플 로그             ║
║  v6.8.1의 모든 기능 유지 (NEW-A~F, BUG-1~3)                                  ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import random, heapq, os
import matplotlib, matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec, matplotlib.ticker
import matplotlib.patches as patches, matplotlib.font_manager as fm
import numpy as np
from scipy.stats import beta as beta_dist
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
try:
    from openpyxl.drawing.image import Image as XLImage
    _CAN_IMG = True
except Exception:
    _CAN_IMG = False

for _fp in ['C:/Windows/Fonts/malgun.ttf', 'C:/Windows/Fonts/malgunbd.ttf']:
    if os.path.exists(_fp): fm.fontManager.addfont(_fp)
matplotlib.rcParams['font.family'] = 'Malgun Gothic'
matplotlib.rcParams['axes.unicode_minus'] = False

CIRCLE_NUMS = ['①','②','③','④','⑤','⑥','⑦','⑧','⑨','⑩',
               '⑪','⑫','⑬','⑭','⑮','⑯','⑰','⑱','⑲','⑳',
               '㉑','㉒','㉓','㉔']

# ── 시스템 상수 ───────────────────────────────────────────────────────────────
CIWS_BURST_COST_USD     = 3000
MAX_ENGAGEMENT_CHANNELS = 24
ECM_REF_RANGE_M         = 25000  # MED-9: 기준 25km (기존 50km 과대, 실 AN/SLQ-32 교란 유효거리)
HELO_SORTIE_COST_USD    = 50000

# ── NEW-B: 음향 기만기 / 함정 회피 ──────────────────────────────────────────
DECOY_PK        = 0.50  # LOW-7: 0.60→0.50 (AN/SLQ-25 실전 기만 성공률)
SHIP_EVASION_PK = 0.20  # LOW-8: 0.30→0.20 (회피 기동 성공률 과대 → 현실화)

WPN_COLOR = {
    'SM-3 Block IIA':    '#1A7A3C',
    'SM-6':              '#7D3C98',
    'SM-2 Block IIIB':   '#1A5FA0',
    'RIM-116 RAM':       '#CA6F1E',
    '홍상어 (대잠)':     '#17A589',
    '청상어 (경어뢰)':   '#1A9980',
    'CIWS-II (Phalanx)': '#B03030',
    '음향 기만기':        '#16A085',
    'AW-159 와일드캣':   '#E67E22',
    'MH-60R 시호크':     '#D35400',
}

CAT_PARAMS = {
    '대공': {'max_m':15000,'min_m':-300,
             'ticks_m':[0,2000,5000,8000,10000,12000,15000],
             'use_arcs':True,'ylabel':'고도 (m)'},
    '대함': {'max_m':300,'min_m':-100,
             'ticks_m':[-100,-50,0,50,100,200,300],
             'use_arcs':False,'ylabel':'고도 (m)'},
    '대잠': {'max_m':50,'min_m':-600,
             'ticks_m':[-600,-500,-400,-300,-200,-100,0,50],
             'use_arcs':False,'ylabel':'수심 (m)'},
}

SUB_DEPTH_M = {
    '039형 잠수함 (송급)':        -250,
    '041형 잠수함 (위안급 개량)': -280,
    '093형 잠수함 (상급)':        -350,
    '094형 잠수함 (진급)':        -400,
}

TACTICAL_LAYERS = [
    {'name':'CIWS (2km)',   'km':2,  'color':'#B03030','lw':2.6},
    {'name':'RAM (9km)',    'km':9,  'color':'#CA6F1E','lw':2.2},
    {'name':'SM-2 (170km)','km':170,'color':'#1A5FA0','lw':1.9},
    {'name':'SM-6 (370km)','km':370,'color':'#7D3C98','lw':1.8},
    {'name':'SM-3 (500km)','km':500,'color':'#1A7A3C','lw':1.8},
]
SURFACE_LAYERS = [
    {'name':'CIWS (2km)',   'km':2,  'color':'#B03030'},
    {'name':'RAM (9km)',    'km':9,  'color':'#CA6F1E'},
    {'name':'SM-2 (170km)','km':170,'color':'#1A5FA0'},
    {'name':'SM-6 (370km)','km':370,'color':'#7D3C98'},
]
SUB_LAYERS = [
    {'name':'청상어 (9km)', 'km':9, 'color':'#17A589'},
    {'name':'홍상어 (19km)','km':19,'color':'#1A7A3C'},
]


# ════════════════════════════════════════════════════════════════════════════
#  적군 데이터베이스 (32종)
#
#  v6.8.1 NEW-F 추가 필드:
#    self_defense_pk   (float) : 아군 미사일 Pk 감소 계수 (채프·플레어·ECM)
#                                effective_pk = pk_s × (1 - self_defense_pk)
#    enemy_ciws_pk     (float) : 적 함정 CIWS 요격 확률 (수상함만 > 0)
#                                CIWS 요격 성공 시 해당 발 격추 (Pk 무효)
#
#  자체 방어 수치 근거:
#    항공기 (채프·플레어·기동) : J-7 0.05 ~ J-20(ECM) 0.18
#    탄도·순항 미사일          : 0.00 (플랫폼 아님, terminal_evasion이 대신)
#    수상함 (함대공·CIWS)      : 022형 0.15 ~ 055형 0.38
#    잠수함 (소음기동)          : 0.05
# ════════════════════════════════════════════════════════════════════════════
ENEMY_DB = {

    # ════ 대공: 전투기 (기존 3종) ════════════════════════════════════════════
    # ── 고도 기준: 미사일 발사 시 실제 접근 고도 (서비스 실링 아님) ──────────
    'MiG-29 (풀크럼)':
        {'category':'대공','type':'전투기','speed_ms':765,'altitude_m':8000,
         # 전술 교전 고도 8km (서비스 실링 18km)
         # MED-7: MiG-29는 Kh-31A 사용 (YJ-91은 중국제, MiG-29 탑재 불가)
         'missile_name':'Kh-31A 대함미사일','missile_speed_ms':680,'missile_range_km':70,
         'can_fire_missile':True,'rcs_m2':5.0,
         'missile_salvo_min':1,'missile_salvo_max':2,
         'missile_terminal_evasion':0.78,
         'evasion_profile':{'speed_boost_min':0.10,'speed_boost_max':0.18,'alt_change_m':2500,'max_attempts':2},
         'self_defense_pk':0.10,'enemy_ciws_pk':0.0},

    'MiG-23 (플로거)':
        {'category':'대공','type':'전투기','speed_ms':797,'altitude_m':7000,
         # 전술 고도 7km (구형 4세대, 중고도)
         # MiG-23는 소련/북한 계열 기체 — 중국제 YJ-83K 탑재 불가. 대함 임무 없음(can_fire_missile=False).
         'missile_name':'Kh-23 (AS-7) 공대지 미사일','missile_speed_ms':300,'missile_range_km':10,
         'can_fire_missile':False,'rcs_m2':6.0,
         'missile_salvo_min':1,'missile_salvo_max':2,
         'missile_terminal_evasion':0.88,
         'evasion_profile':{'speed_boost_min':0.08,'speed_boost_max':0.15,'alt_change_m':2000,'max_attempts':2},
         'self_defense_pk':0.08,'enemy_ciws_pk':0.0},

    'J-7 (섬광)':
        {'category':'대공','type':'전투기','speed_ms':680,'altitude_m':5000,
         # 구형 MiG-21 계열, 저중고도 5km
         'missile_name':'YJ-8K 대함미사일','missile_speed_ms':300,'missile_range_km':50,
         'can_fire_missile':True,'rcs_m2':3.0,
         'missile_salvo_min':1,'missile_salvo_max':1,
         'missile_terminal_evasion':0.90,
         'evasion_profile':{'speed_boost_min':0.06,'speed_boost_max':0.12,'alt_change_m':1500,'max_attempts':1},
         'self_defense_pk':0.05,'enemy_ciws_pk':0.0},

    # ════ 대공: 전투기 (NEW-2 추가 7종) ══════════════════════════════════════
    'J-10A (비맹)':
        {'category':'대공','type':'전투기','speed_ms':700,'altitude_m':10000,
         # 4.5세대, 전술 고도 10km
         # LOW-1: YJ-91 속도 900→680 m/s (Mach 2 at 고고도, 실제 공개 제원)
         'missile_name':'YJ-91 대함미사일','missile_speed_ms':680,'missile_range_km':120,
         'can_fire_missile':True,'rcs_m2':2.0,
         'missile_salvo_min':1,'missile_salvo_max':2,
         'missile_terminal_evasion':0.78,
         'evasion_profile':{'speed_boost_min':0.10,'speed_boost_max':0.20,'alt_change_m':3000,'max_attempts':2},
         'self_defense_pk':0.12,'enemy_ciws_pk':0.0},

    'J-11B (플랭커-B)':
        {'category':'대공','type':'전투기','speed_ms':800,'altitude_m':11000,  # MED-14: 830→800 m/s (Su-27 계열 실 최고속도)
         # Su-27 계열, 전술 고도 11km
         'missile_name':'YJ-83K 주력 대함미사일','missile_speed_ms':300,'missile_range_km':180,
         'can_fire_missile':True,'rcs_m2':10.0,
         'missile_salvo_min':2,'missile_salvo_max':4,
         'missile_terminal_evasion':0.88,
         'evasion_profile':{'speed_boost_min':0.12,'speed_boost_max':0.22,'alt_change_m':3500,'max_attempts':2},
         'self_defense_pk':0.12,'enemy_ciws_pk':0.0},

    'J-15 (비상어)':
        {'category':'대공','type':'전투기','speed_ms':680,'altitude_m':9000,  # MED-15: 750→680 m/s (함재기 중고도 작전 속도)
         # 함재기, 중고도 9km (항모 작전 특성상 중간 고도)
         'missile_name':'YJ-83K 주력 대함미사일','missile_speed_ms':300,'missile_range_km':160,
         'can_fire_missile':True,'rcs_m2':8.0,
         'missile_salvo_min':2,'missile_salvo_max':4,
         'missile_terminal_evasion':0.88,
         'evasion_profile':{'speed_boost_min':0.10,'speed_boost_max':0.20,'alt_change_m':3000,'max_attempts':2},
         'self_defense_pk':0.12,'enemy_ciws_pk':0.0},

    'J-16 (플랭커-D)':
        {'category':'대공','type':'전투기','speed_ms':680,'altitude_m':10000,  # MED-15: 780→680 m/s
         # 다역할 전폭기, 전술 고도 10km
         # MED-2: YJ-12 속도 1000→1400 m/s (Mach 4 말단 단계)
         'missile_name':'YJ-12 초음속 대함미사일','missile_speed_ms':1400,'missile_range_km':400,
         'can_fire_missile':True,'rcs_m2':8.0,
         'missile_salvo_min':2,'missile_salvo_max':4,
         'missile_terminal_evasion':0.72,
         'evasion_profile':{'speed_boost_min':0.12,'speed_boost_max':0.22,'alt_change_m':3000,'max_attempts':2},
         'self_defense_pk':0.15,'enemy_ciws_pk':0.0},

    # v8.26: J-16 기반 전자전 전용기 — 강력한 재밍 파드로 편대 전체 엄호. 공격 무장 없음.
    'J-16D (전자전기)':
        {'category':'대공','type':'전폭기','speed_ms':620,'altitude_m':9000,
         'missile_name':'없음','missile_speed_ms':0,'missile_range_km':0,
         'can_fire_missile':False,'rcs_m2':8.0,
         'missile_salvo_min':0,'missile_salvo_max':0,
         'missile_terminal_evasion':0.78,
         'evasion_profile':{'speed_boost_min':0.10,'speed_boost_max':0.18,'alt_change_m':2500,'max_attempts':2},
         'self_defense_pk':0.12,'enemy_ciws_pk':0.0},

    'J-20 (위룡)':
        # ⭐ 5세대 스텔스 RCS=0.001㎡ → 탐지거리 ~67km + ECM 자체방어 높음
        {'category':'대공','type':'전투기','speed_ms':750,'altitude_m':12000,
         # 5세대 스텔스, 고고도 12km (고고도 활동 선호)
         # MED-2: YJ-12 속도 1000→1400 m/s
         'missile_name':'YJ-12 초음속 대함미사일','missile_speed_ms':1400,'missile_range_km':400,
         'can_fire_missile':True,'rcs_m2':0.001,
         'missile_salvo_min':1,'missile_salvo_max':4,
         'missile_terminal_evasion':0.72,
         'evasion_profile':{'speed_boost_min':0.08,'speed_boost_max':0.15,'alt_change_m':4000,'max_attempts':3},
         'self_defense_pk':0.18,'enemy_ciws_pk':0.0},

    'Su-35 (플랭커-E)':
        {'category':'대공','type':'전투기','speed_ms':765,'altitude_m':11000,  # MED-14: 830→765 m/s (Mach 2.25 실 전투 속도)
         # 슈퍼 플랭커, 전술 고도 11km
         # MED-13: Kh-31A 속도 1000→680 m/s (Mach 2.0 at sea level)
         'missile_name':'Kh-31A 대함미사일','missile_speed_ms':680,'missile_range_km':70,
         'can_fire_missile':True,'rcs_m2':4.0,
         'missile_salvo_min':1,'missile_salvo_max':2,
         'missile_terminal_evasion':0.68,
         'evasion_profile':{'speed_boost_min':0.12,'speed_boost_max':0.25,'alt_change_m':3500,'max_attempts':3},
         'self_defense_pk':0.15,'enemy_ciws_pk':0.0},

    'JH-7A (날치)':
        {'category':'대공','type':'전폭기','speed_ms':596,'altitude_m':2000,  # MED-16: 500→596 m/s (Mach 1.75 실제 최고속도)
         # 공격기: 저고도 침투 2km (해면 근접 돌파 → RAM 위협)
         # LOW-1: YJ-91 속도 900→680 m/s
         'missile_name':'YJ-91 대함미사일','missile_speed_ms':680,'missile_range_km':120,
         'can_fire_missile':True,'rcs_m2':6.0,
         'missile_salvo_min':2,'missile_salvo_max':4,
         'missile_terminal_evasion':0.78,
         'evasion_profile':{'speed_boost_min':0.05,'speed_boost_max':0.12,'alt_change_m':500,'max_attempts':1},
         'self_defense_pk':0.10,'enemy_ciws_pk':0.0},

    # ════ 대공: 폭격기 ════════════════════════════════════════════════════════
    'H-6 (폭격기)':
        {'category':'대공','type':'폭격기','speed_ms':269,'altitude_m':10000,  # MED-10: 290→269 m/s (H-6K Mach 0.79 순항)
         # Tu-16 계열 개량형, 순항 고도 10km
         # MED-2: YJ-12 속도 1000→1400 m/s
         'missile_name':'YJ-12 초음속 대함미사일','missile_speed_ms':1400,'missile_range_km':400,
         'can_fire_missile':True,'rcs_m2':40.0,
         'missile_salvo_min':4,'missile_salvo_max':6,
         'missile_terminal_evasion':0.72,
         'evasion_profile':{'speed_boost_min':0.03,'speed_boost_max':0.08,'alt_change_m':800,'max_attempts':1},
         'self_defense_pk':0.08,'enemy_ciws_pk':0.0},   # NEW-F (구형 폭격기, ECM 취약)

    # ════ 대공: 탄도미사일 ══════════════════════════════════════════════════════
    'DF-11A (단거리 탄도)':
        {'category':'대공','type':'탄도미사일','speed_ms':900,'altitude_m':50000,  # LOW-4: 1500→900 m/s (Scud급 종말 속도)
         'missile_name':None,'missile_speed_ms':None,'missile_range_km':300,
         'can_fire_missile':False,'rcs_m2':0.1,
         'evasion_profile':{'speed_boost_min':0,'speed_boost_max':0,'alt_change_m':0,'max_attempts':0},
         'self_defense_pk':0.0,'enemy_ciws_pk':0.0},    # NEW-F (미사일은 자체방어 없음)

    'DF-15 (단거리 탄도)':
        {'category':'대공','type':'탄도미사일','speed_ms':2000,'altitude_m':80000,
         'missile_name':None,'missile_speed_ms':None,'missile_range_km':600,
         'can_fire_missile':False,'rcs_m2':0.1,
         'evasion_profile':{'speed_boost_min':0,'speed_boost_max':0,'alt_change_m':0,'max_attempts':0},
         'self_defense_pk':0.0,'enemy_ciws_pk':0.0},    # NEW-F

    'DF-21D (대함 탄도)':
        {'category':'대공','type':'탄도미사일','speed_ms':3400,'altitude_m':150000,
         'missile_name':None,'missile_speed_ms':None,'missile_range_km':1500,
         'can_fire_missile':False,'rcs_m2':0.1,
         'evasion_profile':{'speed_boost_min':0,'speed_boost_max':0,'alt_change_m':0,'max_attempts':0},
         'self_defense_pk':0.0,'enemy_ciws_pk':0.0},    # NEW-F

    'DF-26 (중장거리 탄도)':
        {'category':'대공','type':'탄도미사일','speed_ms':5000,'altitude_m':300000,  # LOW-3: 6000→5000 m/s (MRBM 종말 재진입)
         'missile_name':None,'missile_speed_ms':None,'missile_range_km':4000,
         'can_fire_missile':False,'rcs_m2':0.05,
         'evasion_profile':{'speed_boost_min':0,'speed_boost_max':0,'alt_change_m':0,'max_attempts':0},
         'self_defense_pk':0.0,'enemy_ciws_pk':0.0},    # NEW-F

    # ⭐ HGV: SM-3만 요격 가능
    'DF-17 (극초음속 활공)':
        {'category':'대공','type':'극초음속활공체','speed_ms':3000,'altitude_m':60000,  # LOW-5: 2000→3000 m/s (Mach 9+ 활공 단계)
         'missile_name':None,'missile_speed_ms':None,'missile_range_km':2500,
         'can_fire_missile':False,'rcs_m2':0.05,'is_hgv':True,
         'evasion_profile':{'speed_boost_min':0,'speed_boost_max':0,'alt_change_m':0,'max_attempts':0},
         'self_defense_pk':0.0,'enemy_ciws_pk':0.0},    # NEW-F

    # NEW-X: YJ-21 — 함발 극초음속 대함탄도미사일 (055형 탑재, Mach 10+, 사거리 1500km)
    # BUG-ref: is_hgv=True → SM-3만 요격 가능, Pk 최대 0.45
    'YJ-21 (극초음속 대함)':
        {'category':'대공','type':'극초음속활공체','speed_ms':3400,'altitude_m':40000,  # Mach 10+ 활공 단계 (종말 급강하)
         'missile_name':None,'missile_speed_ms':None,'missile_range_km':1500,
         'can_fire_missile':False,'rcs_m2':0.05,'is_hgv':True,
         'evasion_profile':{'speed_boost_min':0,'speed_boost_max':0,'alt_change_m':0,'max_attempts':0},
         'self_defense_pk':0.0,'enemy_ciws_pk':0.0},

    # ⭐ QBM: SM-3 거의 무력화
    'KN-23 (북한 이스칸데르)':
        {'category':'대공','type':'저고도기동탄도','speed_ms':1800,'altitude_m':2000,
         'missile_name':None,'missile_speed_ms':None,'missile_range_km':700,
         'can_fire_missile':False,'rcs_m2':0.15,'is_qbm':True,
         'evasion_profile':{'speed_boost_min':0,'speed_boost_max':0,'alt_change_m':0,'max_attempts':0},
         'self_defense_pk':0.0,'enemy_ciws_pk':0.0},    # NEW-F

    # ════ 대공: 순항미사일 ════════════════════════════════════════════════════
    'CJ-10 (순항미사일)':
        {'category':'대공','type':'순항미사일','speed_ms':270,'altitude_m':100,
         # 지형추적 순항 100m (종말 단계에서 해면 밀착, 평균 순항은 100m)
         'missile_name':None,'missile_speed_ms':None,'missile_range_km':1500,
         'can_fire_missile':False,'rcs_m2':0.01,
         'evasion_profile':{'speed_boost_min':0,'speed_boost_max':0.03,'alt_change_m':5,'max_attempts':1},
         'self_defense_pk':0.0,'enemy_ciws_pk':0.0},

    'YJ-12 (초음속 순항)':
        {'category':'대공','type':'순항미사일','speed_ms':1400,'altitude_m':15,  # MED-2: 1000→1400 m/s (Mach 4 말단 단계)
         'missile_name':None,'missile_speed_ms':None,'missile_range_km':400,
         'can_fire_missile':False,'rcs_m2':0.05,
         'evasion_profile':{'speed_boost_min':0,'speed_boost_max':0.03,'alt_change_m':5,'max_attempts':1},
         'self_defense_pk':0.0,'enemy_ciws_pk':0.0},    # NEW-F

    'P-800 오닉스 (야혼트)':
        {'category':'대공','type':'순항미사일','speed_ms':824,'altitude_m':15,  # LOW-2: 750→824 m/s (Mach 2.5 해면 근접)
         'missile_name':None,'missile_speed_ms':None,'missile_range_km':300,
         'can_fire_missile':False,'rcs_m2':0.10,
         'evasion_profile':{'speed_boost_min':0,'speed_boost_max':0.03,'alt_change_m':5,'max_attempts':1},
         'self_defense_pk':0.0,'enemy_ciws_pk':0.0},    # NEW-F

    'Kh-31A (항공기발사 대함)':
        {'category':'대공','type':'순항미사일','speed_ms':680,'altitude_m':20,  # MED-13: 1000→680 m/s (Mach 2.0 at sea level)
         'missile_name':None,'missile_speed_ms':None,'missile_range_km':70,
         'can_fire_missile':False,'rcs_m2':0.05,
         'evasion_profile':{'speed_boost_min':0,'speed_boost_max':0.03,'alt_change_m':8,'max_attempts':1},
         'self_defense_pk':0.0,'enemy_ciws_pk':0.0},    # NEW-F

    'YJ-100 (장거리 순항)':
        {'category':'대공','type':'순항미사일','speed_ms':300,'altitude_m':50,
         # 장거리 지형추적 순항 50m (CJ-10보다 낮은 스텔스 비행 프로파일)
         'missile_name':None,'missile_speed_ms':None,'missile_range_km':800,
         'can_fire_missile':False,'rcs_m2':0.01,
         'evasion_profile':{'speed_boost_min':0,'speed_boost_max':0.03,'alt_change_m':5,'max_attempts':1},
         'self_defense_pk':0.0,'enemy_ciws_pk':0.0},

    # NEW-X: 해성-3 — 북한 잠수함발사 순항미사일 (아음속, 사거리 1500km+)
    # 실제 스텔스 설계로 RCS 극소 (CJ-10 수준), 잠수함에서 발사 후 해면 밀착 순항
    '해성-3 (잠수함발사 순항)':
        {'category':'대공','type':'순항미사일','speed_ms':250,'altitude_m':50,  # 아음속 지형추적
         'missile_name':None,'missile_speed_ms':None,'missile_range_km':1500,
         'can_fire_missile':False,'rcs_m2':0.01,
         'evasion_profile':{'speed_boost_min':0,'speed_boost_max':0.03,'alt_change_m':5,'max_attempts':1},
         'self_defense_pk':0.0,'enemy_ciws_pk':0.0},

    # ════ 대함: 수상함 (5종) ══════════════════════════════════════════════════
    # NEW-F: 수상함은 함대공미사일 + CIWS 자체방어 현실적 수치
    #  022형 고속정  : HHQ-10 CIWS 장착, 근접방어 중심
    #  056형 초계함  : HHQ-10 + FL-3000N
    #  054A형 호위함 : HHQ-16 VLS + HHQ-10 CIWS 다층
    #  052D형 구축함 : HHQ-9B VLS 64셀 + 1130 CIWS × 1 → 강력한 자체방어
    #  055형 대형구축함: HHQ-9B × 112셀 + 1130 CIWS × 2 → 최강 자체방어
    '022형 미사일 고속정':
        {'category':'대함','type':'고속정','speed_ms':18.5,'altitude_m':10,  # MED-6: 22→18.5 m/s (35-36 kts 실제 최고속)
         'missile_name':'YJ-83 대함미사일','missile_speed_ms':300,'missile_range_km':180,
         'can_fire_missile':True,'rcs_m2':50.0,
         'missile_salvo_min':4,'missile_salvo_max':8,
         'missile_terminal_evasion':0.88,
         'evasion_profile':{'speed_boost_min':0.10,'speed_boost_max':0.22,'alt_change_m':0,'max_attempts':1},
         'self_defense_pk':0.15,'enemy_ciws_pk':0.12},  # NEW-F

    '056형 초계함':
        {'category':'대함','type':'초계함','speed_ms':14.0,'altitude_m':15,
         'missile_name':'YJ-83 대함미사일','missile_speed_ms':300,'missile_range_km':180,
         'can_fire_missile':True,'rcs_m2':300.0,
         'missile_salvo_min':2,'missile_salvo_max':4,
         'missile_terminal_evasion':0.88,
         'evasion_profile':{'speed_boost_min':0.05,'speed_boost_max':0.12,'alt_change_m':0,'max_attempts':1},
         'self_defense_pk':0.20,'enemy_ciws_pk':0.15},  # NEW-F

    '054A형 호위함':
        {'category':'대함','type':'호위함','speed_ms':14.0,'altitude_m':20,
         'missile_name':'YJ-83 대함미사일','missile_speed_ms':300,'missile_range_km':180,
         'can_fire_missile':True,'rcs_m2':800.0,
         'missile_salvo_min':4,'missile_salvo_max':8,
         'missile_terminal_evasion':0.88,
         'evasion_profile':{'speed_boost_min':0.05,'speed_boost_max':0.10,'alt_change_m':0,'max_attempts':1},
         'self_defense_pk':0.28,'enemy_ciws_pk':0.22},  # NEW-F

    '052D형 구축함':
        {'category':'대함','type':'구축함','speed_ms':15.0,'altitude_m':25,
         'missile_name':'YJ-18 초음속 대함미사일','missile_speed_ms':1000,'missile_range_km':500,
         'can_fire_missile':True,'rcs_m2':1500.0,
         'missile_salvo_min':4,'missile_salvo_max':8,
         'missile_terminal_evasion':0.75,
         'evasion_profile':{'speed_boost_min':0.05,'speed_boost_max':0.10,'alt_change_m':0,'max_attempts':1},
         'self_defense_pk':0.32,'enemy_ciws_pk':0.28},  # NEW-F

    '055형 대형 구축함':
        {'category':'대함','type':'구축함','speed_ms':15.4,'altitude_m':30,  # MED-18: 17→15.4 m/s (30 kts 실제 최고속)
         'missile_name':'YJ-18 초음속 대함미사일','missile_speed_ms':1000,'missile_range_km':500,
         'can_fire_missile':True,'rcs_m2':2000.0,
         'missile_salvo_min':6,'missile_salvo_max':12,
         'missile_terminal_evasion':0.75,
         'evasion_profile':{'speed_boost_min':0.04,'speed_boost_max':0.08,'alt_change_m':0,'max_attempts':1},
         'self_defense_pk':0.38,'enemy_ciws_pk':0.33},  # NEW-F (중국 최강 자체방어)

    # ── 중국 항모 (3종) ───────────────────────────────────────────────────────
    # hp=5: 항모는 5발 이상 피격 시 격침 (호위함대 포함 집단 방어 반영)
    # self_defense_pk: 호위 전단 방어 + 항모 자체 CIWS 합산 (높게 설정)
    # carrier_wave_interval: 함재기 발진 주기 (초)
    '랴오닝 (항모)':
        {'category':'대함','type':'항모','speed_ms':15.4,'altitude_m':30,
         'missile_name':'YJ-18 초음속 대함미사일','missile_speed_ms':1000,'missile_range_km':500,
         'can_fire_missile':True,'rcs_m2':50000.0,
         'missile_salvo_min':4,'missile_salvo_max':8,
         'missile_terminal_evasion':0.75,
         'evasion_profile':{'speed_boost_min':0.03,'speed_boost_max':0.06,'alt_change_m':0,'max_attempts':1},
         'self_defense_pk':0.45,'enemy_ciws_pk':0.40,
         'hp':5,'high_value_target':True,
         'carrier_aircraft':'J-15 (비상어)','carrier_wave_interval':90},

    '산둥 (항모)':
        {'category':'대함','type':'항모','speed_ms':15.4,'altitude_m':30,
         'missile_name':'YJ-18 초음속 대함미사일','missile_speed_ms':1000,'missile_range_km':500,
         'can_fire_missile':True,'rcs_m2':55000.0,
         'missile_salvo_min':4,'missile_salvo_max':8,
         'missile_terminal_evasion':0.75,
         'evasion_profile':{'speed_boost_min':0.03,'speed_boost_max':0.06,'alt_change_m':0,'max_attempts':1},
         'self_defense_pk':0.47,'enemy_ciws_pk':0.42,
         'hp':5,'high_value_target':True,
         'carrier_aircraft':'J-15 (비상어)','carrier_wave_interval':90},

    '푸젠 (항모)':
        {'category':'대함','type':'항모','speed_ms':15.4,'altitude_m':30,
         'missile_name':'YJ-18 초음속 대함미사일','missile_speed_ms':1000,'missile_range_km':500,
         'can_fire_missile':True,'rcs_m2':60000.0,
         'missile_salvo_min':6,'missile_salvo_max':10,
         'missile_terminal_evasion':0.75,
         'evasion_profile':{'speed_boost_min':0.03,'speed_boost_max':0.06,'alt_change_m':0,'max_attempts':1},
         'self_defense_pk':0.50,'enemy_ciws_pk':0.45,
         'hp':5,'high_value_target':True,
         'carrier_aircraft':'J-35 (백상어)','carrier_wave_interval':80},

    # ════ 대잠: 잠수함 (5종) ══════════════════════════════════════════════════
    # altitude_m = 잠항 수심 (음수 = 수면 아래)
    # 수온약층(thermocline): 100~300m 구간 소나 탐지 가장 어려움
    # 회피 기동: depth_change_m으로 더 깊이 잠항
    '039형 잠수함 (송급)':
        {'category':'대잠','type':'잠수함','speed_ms':11.0,'altitude_m':-150,
         # Song급 SSK: 최대 잠항 300m, 작전 수심 150m (수온약층 내)
         # MED-17: Yu-6 속도 33→21 m/s, 사거리 45→18 km (실 Yu-6: 40 kts, 18km)
         'missile_name':'Yu-6 중어뢰','missile_speed_ms':21.0,'missile_range_km':18,
         'can_fire_missile':True,'rcs_m2':None,
         'missile_salvo_min':2,'missile_salvo_max':4,
         'missile_terminal_evasion':0.90,
         'evasion_profile':{'speed_boost_min':0.05,'speed_boost_max':0.15,'depth_change_m':-80,'max_attempts':2},
         'self_defense_pk':0.05,'enemy_ciws_pk':0.0},

    '041형 잠수함 (위안급 개량)':
        {'category':'대잠','type':'잠수함','speed_ms':12.0,'altitude_m':-200,
         # Yuan급 AIP SSK: 최대 잠항 350m, 작전 수심 200m (수온약층 깊은 곳)
         # MED-17: Yu-6 속도 33→21 m/s, 사거리 45→18 km
         'missile_name':'Yu-6 중어뢰','missile_speed_ms':21.0,'missile_range_km':18,
         'can_fire_missile':True,'rcs_m2':None,
         'missile_salvo_min':2,'missile_salvo_max':4,
         'missile_terminal_evasion':0.90,
         'evasion_profile':{'speed_boost_min':0.06,'speed_boost_max':0.16,'depth_change_m':-80,'max_attempts':2},
         'self_defense_pk':0.05,'enemy_ciws_pk':0.0},

    '093형 잠수함 (상급)':
        {'category':'대잠','type':'잠수함','speed_ms':15.0,'altitude_m':-280,
         # Shang급 SSN: 최대 잠항 400m, 작전 수심 280m (수온약층 하부)
         'missile_name':'YJ-18B 잠대함미사일','missile_speed_ms':1000,'missile_range_km':500,
         'can_fire_missile':True,'rcs_m2':None,
         'missile_salvo_min':2,'missile_salvo_max':6,
         'missile_terminal_evasion':0.75,
         'evasion_profile':{'speed_boost_min':0.08,'speed_boost_max':0.18,'depth_change_m':-90,'max_attempts':2},
         'self_defense_pk':0.05,'enemy_ciws_pk':0.0},

    '094형 잠수함 (진급)':
        {'category':'대잠','type':'잠수함','speed_ms':12.0,'altitude_m':-200,
         # Jin급 SSBN: 전략 핵잠수함. JL-2 SLBM은 전술 교전에서 사용하지 않음.
         # 아군 대잠전 목표: SLBM 발사 전 격침. 교전 중 자기방어용 어뢰만 사용.
         'missile_name':'Yu-6 중어뢰 (자기방어)','missile_speed_ms':21.0,'missile_range_km':18,
         'can_fire_missile':True,'rcs_m2':None,
         'missile_salvo_min':1,'missile_salvo_max':2,
         'missile_terminal_evasion':0.85,
         'evasion_profile':{'speed_boost_min':0.05,'speed_boost_max':0.12,'depth_change_m':-80,'max_attempts':1},
         'self_defense_pk':0.05,'enemy_ciws_pk':0.0},

    # ════ 북한 위협 ══════════════════════════════════════════════════════════
    '화성-15 (북한 ICBM급)': {
        'type':'탄도미사일','category':'대공','altitude_m':1200000,
        'speed_ms':7400,  # 재진입 단계 최대속도
        'range_km':13000, 'is_ballistic':True, 'is_hgv':False, 'is_qbm':False,
        'rcs_m2':0.5, 'cost_usd':0},
    '화성-17 (북한 ICBM 개량)': {
        'type':'탄도미사일','category':'대공','altitude_m':1200000,
        'speed_ms':7700,
        'range_km':15000, 'is_ballistic':True, 'is_hgv':False, 'is_qbm':False,
        'rcs_m2':0.5, 'cost_usd':0},
    '북한 순항미사일 (화살-2)': {
        'type':'순항미사일','category':'대공','altitude_m':50,
        'speed_ms':250, 'range_km':1500,
        'rcs_m2':0.03, 'cost_usd':0,
        'missile_terminal_evasion':0.82},

    # ════ 러시아 위협 ════════════════════════════════════════════════════════
    '킨잘 (극초음속 탄도)': {
        'type':'극초음속활공체','category':'대공','altitude_m':20000,
        'speed_ms':3500,  # Mach 10
        'range_km':2000, 'is_ballistic':False, 'is_hgv':True, 'is_qbm':False,
        'rcs_m2':0.1, 'cost_usd':0,
        'missile_terminal_evasion':0.92},
    '지르콘 (극초음속 순항)': {
        'type':'순항미사일','category':'대공','altitude_m':10000,
        'speed_ms':2700,  # Mach 8
        'range_km':1000, 'is_ballistic':False, 'is_hgv':True, 'is_qbm':False,
        'rcs_m2':0.05, 'cost_usd':0,
        'missile_terminal_evasion':0.90},
    'Kh-101 (스텔스 순항)': {
        'type':'순항미사일','category':'대공','altitude_m':100,
        'speed_ms':250,   # 아음속 스텔스
        'range_km':5500,
        'rcs_m2':0.01,    # 매우 낮은 RCS (스텔스)
        'cost_usd':0,
        'missile_terminal_evasion':0.78},

    # ════ 중국 신규 추가 (7종) ═══════════════════════════════════════════════
    # J-35: Type 003 탑재 5세대 스텔스 함재기
    'J-35 (백상어)':
        {'category':'대공','type':'전투기','speed_ms':640,'altitude_m':11000,
         'missile_name':'YJ-12 초음속 대함미사일','missile_speed_ms':1400,'missile_range_km':400,
         'can_fire_missile':True,'rcs_m2':0.002,
         'missile_salvo_min':2,'missile_salvo_max':4,
         'missile_terminal_evasion':0.72,
         'evasion_profile':{'speed_boost_min':0.08,'speed_boost_max':0.15,'alt_change_m':4000,'max_attempts':3},
         'self_defense_pk':0.20,'enemy_ciws_pk':0.0},

    'J-10C (맹룡 개량)':
        {'category':'대공','type':'전투기','speed_ms':540,'altitude_m':9000,
         'missile_name':'YJ-12 초음속 대함미사일','missile_speed_ms':1400,'missile_range_km':400,
         'can_fire_missile':True,'rcs_m2':3.0,
         'missile_salvo_min':1,'missile_salvo_max':4,
         'missile_terminal_evasion':0.72,
         'evasion_profile':{'speed_boost_min':0.08,'speed_boost_max':0.14,'alt_change_m':3500,'max_attempts':3},
         'self_defense_pk':0.14,'enemy_ciws_pk':0.0},

    # H-6N: 공중발사 탄도미사일(DF-21D) 운용 전략폭격기
    'H-6N (폭격기 개량)':
        {'category':'대공','type':'폭격기','speed_ms':270,'altitude_m':9000,
         'missile_name':'DF-21D (공중발사)','missile_speed_ms':3000,'missile_range_km':1500,
         'can_fire_missile':True,'rcs_m2':45.0,
         'missile_salvo_min':1,'missile_salvo_max':2,
         'missile_terminal_evasion':0.92,
         'evasion_profile':{'speed_boost_min':0.03,'speed_boost_max':0.06,'alt_change_m':600,'max_attempts':1},
         'self_defense_pk':0.06,'enemy_ciws_pk':0.0,
         'is_qbm':True},

    '052C형 구축함 (HHQ-9)':
        {'category':'대함','type':'구축함','speed_ms':15.0,'altitude_m':30,
         'missile_name':'YJ-12 초음속 대함미사일','missile_speed_ms':1400,'missile_range_km':400,
         'can_fire_missile':True,'rcs_m2':1600.0,
         'missile_salvo_min':4,'missile_salvo_max':8,
         'missile_terminal_evasion':0.75,
         'evasion_profile':{'speed_boost_min':0.04,'speed_boost_max':0.08,'alt_change_m':0,'max_attempts':1},
         'self_defense_pk':0.30,'enemy_ciws_pk':0.28},

    '071형 상륙함':
        {'category':'대함','type':'구축함','speed_ms':12.0,'altitude_m':30,
         'missile_name':'YJ-12 초음속 대함미사일','missile_speed_ms':1400,'missile_range_km':400,
         'can_fire_missile':True,'rcs_m2':3500.0,
         'missile_salvo_min':2,'missile_salvo_max':4,
         'missile_terminal_evasion':0.75,
         'evasion_profile':{'speed_boost_min':0.03,'speed_boost_max':0.06,'alt_change_m':0,'max_attempts':1},
         'self_defense_pk':0.18,'enemy_ciws_pk':0.20},

    'YJ-18 (초음속 대함)':
        {'category':'대함','type':'순항미사일','speed_ms':1000,'altitude_m':12,
         'missile_name':None,'missile_speed_ms':None,'missile_range_km':540,
         'can_fire_missile':False,'rcs_m2':0.04,
         'evasion_profile':{'speed_boost_min':0,'speed_boost_max':0.04,'alt_change_m':5,'max_attempts':1},
         'self_defense_pk':0.0,'enemy_ciws_pk':0.0,
         'terminal_evasion_factor':0.88,'missile_terminal_evasion':1.0},

    # ════ 러시아 신규 추가 (8종) ═════════════════════════════════════════════
    'Su-57 (펠론)':
        {'category':'대공','type':'전투기','speed_ms':594,'altitude_m':12000,
         'missile_name':'Kh-31A 대함미사일','missile_speed_ms':680,'missile_range_km':70,
         'can_fire_missile':True,'rcs_m2':0.005,
         'missile_salvo_min':2,'missile_salvo_max':4,
         'missile_terminal_evasion':0.72,
         'evasion_profile':{'speed_boost_min':0.10,'speed_boost_max':0.18,'alt_change_m':4000,'max_attempts':3},
         'self_defense_pk':0.22,'enemy_ciws_pk':0.0},

    # Tu-22M3: Kh-32 극초음속 대함미사일 탑재 (마하 5, 고고도 강하)
    'Tu-22M3 (백파이어)':
        {'category':'대공','type':'폭격기','speed_ms':480,'altitude_m':11000,
         'missile_name':'Kh-32 극초음속','missile_speed_ms':1500,'missile_range_km':600,
         'can_fire_missile':True,'rcs_m2':30.0,
         'missile_salvo_min':2,'missile_salvo_max':3,
         'missile_terminal_evasion':0.88,
         'evasion_profile':{'speed_boost_min':0.05,'speed_boost_max':0.12,'alt_change_m':2000,'max_attempts':2},
         'self_defense_pk':0.08,'enemy_ciws_pk':0.0,
         'is_hgv':True},

    '우달로이급 구축함':
        {'category':'대함','type':'구축함','speed_ms':16.0,'altitude_m':30,
         'missile_name':'P-800 오닉스 (야혼트)','missile_speed_ms':824,'missile_range_km':300,
         'can_fire_missile':True,'rcs_m2':1800.0,
         'missile_salvo_min':4,'missile_salvo_max':8,
         'missile_terminal_evasion':0.82,
         'evasion_profile':{'speed_boost_min':0.04,'speed_boost_max':0.08,'alt_change_m':0,'max_attempts':1},
         'self_defense_pk':0.28,'enemy_ciws_pk':0.25},

    '슬라바급 순양함':
        {'category':'대함','type':'구축함','speed_ms':17.0,'altitude_m':30,
         'missile_name':'P-1000 (벌칸)','missile_speed_ms':824,'missile_range_km':700,
         'can_fire_missile':True,'rcs_m2':4000.0,
         'missile_salvo_min':8,'missile_salvo_max':16,
         'missile_terminal_evasion':0.82,
         'evasion_profile':{'speed_boost_min':0.03,'speed_boost_max':0.07,'alt_change_m':0,'max_attempts':1},
         'self_defense_pk':0.35,'enemy_ciws_pk':0.32},

    '킬로급 잠수함 (Project 636)':
        {'category':'대잠','type':'잠수함','speed_ms':10.0,'altitude_m':-250,
         'missile_name':'Kalibr 3M54 잠대함','missile_speed_ms':1000,'missile_range_km':660,
         'can_fire_missile':True,'rcs_m2':None,
         'missile_salvo_min':2,'missile_salvo_max':6,
         'missile_terminal_evasion':0.75,
         'evasion_profile':{'speed_boost_min':0.08,'speed_boost_max':0.18,'depth_change_m':-80,'max_attempts':2,'alt_change_m':0},
         'self_defense_pk':0.05,'enemy_ciws_pk':0.0},

    # 오스카-II: P-700 그라니트 24발 포화 공격 특화 SSGN
    '오스카-II급 SSGN':
        {'category':'대잠','type':'잠수함','speed_ms':13.0,'altitude_m':-400,
         'missile_name':'P-700 그라니트','missile_speed_ms':2500,'missile_range_km':550,
         'can_fire_missile':True,'rcs_m2':None,
         'missile_salvo_min':8,'missile_salvo_max':24,
         'missile_terminal_evasion':0.82,
         'evasion_profile':{'speed_boost_min':0.08,'speed_boost_max':0.16,'depth_change_m':-100,'max_attempts':2,'alt_change_m':0},
         'self_defense_pk':0.05,'enemy_ciws_pk':0.0},

    '야센급 SSGN':
        {'category':'대잠','type':'잠수함','speed_ms':14.0,'altitude_m':-400,
         'missile_name':'Kalibr 3M54 잠대함','missile_speed_ms':1000,'missile_range_km':660,
         'can_fire_missile':True,'rcs_m2':None,
         'missile_salvo_min':6,'missile_salvo_max':16,
         'missile_terminal_evasion':0.75,
         'evasion_profile':{'speed_boost_min':0.10,'speed_boost_max':0.18,'depth_change_m':-120,'max_attempts':3,'alt_change_m':0},
         'self_defense_pk':0.05,'enemy_ciws_pk':0.0},

    'Kalibr (3M14 순항미사일)':
        {'category':'대함','type':'순항미사일','speed_ms':250,'altitude_m':50,
         'missile_name':None,'missile_speed_ms':None,'missile_range_km':1500,
         'can_fire_missile':False,'rcs_m2':0.05,
         'evasion_profile':{'speed_boost_min':0,'speed_boost_max':0.03,'alt_change_m':5,'max_attempts':1},
         'self_defense_pk':0.0,'enemy_ciws_pk':0.0,
         'terminal_evasion_factor':0.88,'missile_terminal_evasion':1.0},

    # ════ 북한 신규 추가 (4종) ═══════════════════════════════════════════════
    '화성-12 (IRBM)':
        {'category':'대공','type':'탄도미사일','speed_ms':4000,'altitude_m':80000,
         'missile_name':None,'missile_speed_ms':None,'missile_range_km':5000,
         'can_fire_missile':False,'rcs_m2':0.5,
         'evasion_profile':{'speed_boost_min':0,'speed_boost_max':0,'alt_change_m':0,'max_attempts':0},
         'self_defense_pk':0.0,'enemy_ciws_pk':0.0},

    '화성-18 (ICBM 고체연료)':
        {'category':'대공','type':'탄도미사일','speed_ms':7000,'altitude_m':150000,
         'missile_name':None,'missile_speed_ms':None,'missile_range_km':15000,
         'can_fire_missile':False,'rcs_m2':0.5,
         'evasion_profile':{'speed_boost_min':0,'speed_boost_max':0,'alt_change_m':0,'max_attempts':0},
         'self_defense_pk':0.0,'enemy_ciws_pk':0.0},

    # KN-24: ATACMS 유사 QBM, 종말단계 불규칙 기동
    'KN-24 (단거리 기동탄도)':
        {'category':'대공','type':'저고도기동탄도','speed_ms':2000,'altitude_m':50000,
         'missile_name':None,'missile_speed_ms':None,'missile_range_km':450,
         'can_fire_missile':False,'rcs_m2':0.4,
         'evasion_profile':{'speed_boost_min':0,'speed_boost_max':0.05,'alt_change_m':10000,'max_attempts':2},
         'self_defense_pk':0.0,'enemy_ciws_pk':0.0,
         'is_qbm':True},

    '신포급 잠수함 (SLBM)':
        {'category':'대잠','type':'잠수함','speed_ms':8.0,'altitude_m':-150,
         'missile_name':'북극성-1 (SLBM)','missile_speed_ms':2000,'missile_range_km':1200,
         'can_fire_missile':True,'rcs_m2':None,
         'missile_salvo_min':1,'missile_salvo_max':2,
         'missile_terminal_evasion':0.88,
         'evasion_profile':{'speed_boost_min':0.06,'speed_boost_max':0.12,'depth_change_m':-60,'max_attempts':2,'alt_change_m':0},
         'self_defense_pk':0.03,'enemy_ciws_pk':0.0},

    # v9.6: 신포급 기습 특화 — 수온약층 내 잠복 후 어뢰+해성-3 동시 기습 발사
    # 은닉 120초 후 탐지, 탐지 즉시 어뢰(Yu-6 ×2~4) + 해성-3(×1~2) 동시 발사
    '신포급 잠수함 (기습)':
        {'category':'대잠','type':'잠수함','speed_ms':6.0,'altitude_m':-200,
         'missile_name':'Yu-6 중어뢰','missile_speed_ms':21.0,'missile_range_km':18,
         'can_fire_missile':True,'rcs_m2':None,
         'missile_salvo_min':2,'missile_salvo_max':4,
         'missile_terminal_evasion':0.90,
         'evasion_profile':{'speed_boost_min':0.04,'speed_boost_max':0.10,'depth_change_m':-80,'max_attempts':2,'alt_change_m':0},
         'self_defense_pk':0.03,'enemy_ciws_pk':0.0,
         # 기습 파라미터
         'is_ambush':True,'ambush_hidden_s':120,'ambush_start_km':20,
         # 어뢰와 동시에 해성-3 순항미사일도 발사 (이중 위협)
         'dual_weapon':True,
         'dual_missile_name':'해성-3 (잠수함발사 순항)',
         'dual_missile_speed_ms':250,'dual_missile_range_km':1500,
         'dual_salvo_min':1,'dual_salvo_max':2},

    # ════ 대방사미사일(ARM) — 레이더 전파 추적 대방사 미사일 ═══════════════════
    # 레이더 전파(전자기파)를 역추적해 레이더 자체를 파괴. ECM 무효 (역으로 재밍이 표적이 됨).
    # 아군 레이더가 활성화 상태일수록 ARM Pk 높음.
    'Kh-31P 대방사미사일':
        {'category':'대공','type':'대방사미사일','speed_ms':1000,'altitude_m':8000,
         # 러시아제 ARM. MiG-29/Su-30 탑재. 사거리 110km, 마하 3 초음속.
         'missile_name':None,'missile_speed_ms':None,'missile_range_km':110,
         'can_fire_missile':False,'rcs_m2':0.02,'is_arm':True,
         'evasion_profile':{'speed_boost_min':0,'speed_boost_max':0.05,'alt_change_m':500,'max_attempts':1},
         'self_defense_pk':0.0,'enemy_ciws_pk':0.0,
         'missile_terminal_evasion':1.0},

    'LD-10 대방사미사일':
        {'category':'대공','type':'대방사미사일','speed_ms':850,'altitude_m':7000,
         # 중국제 ARM. J-16/JH-7A 탑재. AGM-88 HARM 대응 개발. 사거리 100km, 마하 2.5.
         'missile_name':None,'missile_speed_ms':None,'missile_range_km':100,
         'can_fire_missile':False,'rcs_m2':0.02,'is_arm':True,
         'evasion_profile':{'speed_boost_min':0,'speed_boost_max':0.05,'alt_change_m':500,'max_attempts':1},
         'self_defense_pk':0.0,'enemy_ciws_pk':0.0,
         'missile_terminal_evasion':1.0},

    'Kh-58U 대방사미사일':
        {'category':'대공','type':'대방사미사일','speed_ms':1200,'altitude_m':10000,
         # 러시아제 장거리 ARM. Su-57/Su-35 탑재. 사거리 250km, 마하 3.6 초음속.
         'missile_name':None,'missile_speed_ms':None,'missile_range_km':250,
         'can_fire_missile':False,'rcs_m2':0.02,'is_arm':True,
         'evasion_profile':{'speed_boost_min':0,'speed_boost_max':0.05,'alt_change_m':600,'max_attempts':1},
         'self_defense_pk':0.0,'enemy_ciws_pk':0.0,
         'missile_terminal_evasion':1.0},
}

# ── 아군 무기 DB ─────────────────────────────────────────────────────────────
FRIENDLY_DB = {
    'SM-3 Block IIA':
        {'speed_ms':4500,'range_km':500,'cost_usd':25000000,'stock':8,
         'category':['대공','탄도미사일'],
         'pk_dist':{'alpha':18,'beta':2,'mean':0.900},'requires_illuminator':False},
    'SM-6':
        {'speed_ms':1000,'range_km':370,'cost_usd':4200000,'stock':32,  # 370 km (RIM-174 ERAM Block IB 공개 사거리)
         'category':['대공','탄도미사일'],
         # LOW-6: Pk mean 0.905→0.75 (SM-6 실전 교전 Pk 과대 평가 수정)
         'pk_dist':{'alpha':9,'beta':3,'mean':0.750},'requires_illuminator':False},
    'SM-2 Block IIIB':
        {'speed_ms':1190,'range_km':170,'cost_usd':400000,'stock':48,
         'category':['대공','대함'],
         'pk_dist':{'alpha':16,'beta':4,'mean':0.800},'requires_illuminator':True},
    'RIM-116 RAM':
        {'speed_ms':680,'range_km':9,'cost_usd':150000,'stock':21,
         'category':['대공','대함','근접'],
         'pk_dist':{'alpha':9,'beta':3,'mean':0.750},'requires_illuminator':False},
    '홍상어 (대잠)':
        {'speed_ms':25.0,'range_km':19,'cost_usd':500000,'stock':16,  # MED-4: 28.3→25 m/s
         'category':['대잠'],
         # LOW-16: Pk mean 0.700→0.65 (실전 수중 유도 탐지 성공률 반영)
         'pk_dist':{'alpha':13,'beta':7,'mean':0.650},'requires_illuminator':False},
    '청상어 (경어뢰)':
        {'speed_ms':23.0,'range_km':9,'cost_usd':200000,'stock':12,  # MED-4: 28.3→23 m/s
         'category':['대잠'],
         # LOW-17: Pk mean 0.700→0.65
         'pk_dist':{'alpha':13,'beta':7,'mean':0.650},'requires_illuminator':False},
    'CIWS-II (Phalanx)':
        {'speed_ms':1100,'range_km':2,'cost_usd':5000,'stock':9999,
         'category':['대공','대함','근접'],
         'pk_dist':{'alpha':6,'beta':4,'mean':0.600},'requires_illuminator':False},
    # NEW-I: P-3C 탑재 어뢰
    'Mk.46 경어뢰':
        {'speed_ms':21.0,'range_km':11,'cost_usd':150000,'stock':8,  # MED-4: 28.3→21 m/s (Mk.46 Mod5 ~40 kts)
         'category':['대잠'],
         'pk_dist':{'alpha':7,'beta':3,'mean':0.700},'requires_illuminator':False},
    # NEW-X: 한국 해군 대함 무기 (PKG·PCC 탑재)
    '해성-I (대함순항)':
        {'speed_ms':300,'range_km':150,'cost_usd':600000,'stock':0,
         'category':['대함'],
         'pk_dist':{'alpha':8,'beta':2,'mean':0.800},'requires_illuminator':False},
    '하푼 Block II (AGM-84)':
        {'speed_ms':270,'range_km':280,'cost_usd':1200000,'stock':0,
         'category':['대함'],
         'pk_dist':{'alpha':7,'beta':3,'mean':0.700},'requires_illuminator':False},
    # NEW-B2: 국산 단거리 함대공 해궁 (K-SAAM, KVLS 탑재 — FFX-II/III 전용)
    '해궁 (K-SAAM)':
        {'speed_ms':720,'range_km':20,'cost_usd':180000,'stock':0,
         'category':['대공','근접'],
         'pk_dist':{'alpha':10,'beta':3,'mean':0.769},'requires_illuminator':False},
    # NEW-P1: 미국 해군 무기 추가 (한미 연합 작전용)
    'ESSM Block II':
        {'speed_ms':1050,'range_km':50,'cost_usd':1500000,'stock':0,
         'category':['대공','근접'],
         'pk_dist':{'alpha':12,'beta':3,'mean':0.800},'requires_illuminator':False},
    'SM-6 Block IB':
        {'speed_ms':1190,'range_km':370,'cost_usd':4800000,'stock':0,
         'category':['대공','탄도미사일'],
         'pk_dist':{'alpha':10,'beta':2,'mean':0.833},'requires_illuminator':False},
    'Tomahawk Block V':
        {'speed_ms':250,'range_km':1700,'cost_usd':2000000,'stock':0,
         'category':['대함'],
         'pk_dist':{'alpha':16,'beta':4,'mean':0.800},'requires_illuminator':False},
}

WEATHER_DB = {
    # radar_factor : 레이더 탐지거리 배율 (대공·대함)
    # sonar_factor : 소나 탐지거리 배율 (대잠)  — 황사는 소나 영향 없음, 풍랑/폭풍은 해상 소음으로 급감
    '맑음 (주간)':
        {'detect_range_factor':1.00,'radar_factor':1.00,'sonar_factor':1.00,
         'intercept_prob_delta': 0.00,'cd_time_factor':1.00},
    '맑음 (야간)':
        # LOW-14: radar_factor 0.97→0.95 (야간 레이더 성능 소폭 저하)
        {'detect_range_factor':0.97,'radar_factor':0.95,'sonar_factor':0.98,
         'intercept_prob_delta':-0.01,'cd_time_factor':1.05},
    '흐림 (박무)':
        # LOW-13: sonar_factor 0.92→0.85 (박무 시 해상 소음 증가)
        {'detect_range_factor':0.90,'radar_factor':0.90,'sonar_factor':0.85,
         'intercept_prob_delta':-0.03,'cd_time_factor':1.10},
    '황사 (봄철 황사)':
        {'detect_range_factor':0.93,'radar_factor':0.72,'sonar_factor':1.00,
         'intercept_prob_delta':-0.02,'cd_time_factor':1.10},
    '풍랑 (7~8등급)':
        {'detect_range_factor':0.85,'radar_factor':0.92,'sonar_factor':0.60,
         'intercept_prob_delta':-0.06,'cd_time_factor':1.20},
    '폭풍 (해상 악화)':
        {'detect_range_factor':0.75,'radar_factor':0.55,'sonar_factor':0.40,
         'intercept_prob_delta':-0.08,'cd_time_factor':1.25},
    '태풍 (9~12등급)':
        {'detect_range_factor':0.55,'radar_factor':0.62,'sonar_factor':0.22,
         'intercept_prob_delta':-0.15,'cd_time_factor':1.50},
    '농무 (시정 200m 이하)':
        # LOW-12: radar_factor 0.96→0.80 (농무는 레이더 흡수·산란 심각)
        {'detect_range_factor':0.88,'radar_factor':0.80,'sonar_factor':0.94,
         'intercept_prob_delta':-0.03,'cd_time_factor':1.10},
    # ── v9.2: 야간·악천후 복합 시나리오 ──────────────────────────────────────
    # 야간 modifier: detect_range×0.88 / radar×0.95 / cd_time×1.10 / delta-0.02
    '폭풍 (야간)':
        # 폭풍(레이더 교란·해상 악화) + 야간(광학 불가·식별 지연) 복합
        {'detect_range_factor':0.66,'radar_factor':0.52,'sonar_factor':0.40,
         'intercept_prob_delta':-0.10,'cd_time_factor':1.38},
    '태풍 (야간)':
        # 최악 기상 + 야간 — 레이더·광학 모두 극한 저하
        {'detect_range_factor':0.48,'radar_factor':0.59,'sonar_factor':0.22,
         'intercept_prob_delta':-0.17,'cd_time_factor':1.65},
    '농무 (야간)':
        # 농무(시정 0) + 야간(광학 불가) — 사실상 레이더만 의존
        {'detect_range_factor':0.62,'radar_factor':0.76,'sonar_factor':0.94,
         'intercept_prob_delta':-0.05,'cd_time_factor':1.27},
    '황사 (새벽)':
        # 황사(레이더 흡수) + 새벽(광학 저하) — 봄철 황해 전형적 복합 환경
        {'detect_range_factor':0.86,'radar_factor':0.70,'sonar_factor':1.00,
         'intercept_prob_delta':-0.03,'cd_time_factor':1.16},
}

SHIP_SPEC = {
    '대공': {'sensor':'AN/SPY-1D(V) Baseline 9.C2','detect_km_max':800},  # MED-3: 1200→800 km (실 SPY-1D 공중 탐지 최대 800km)
    '대함': {'sensor':'AN/SPY-1D(V) Baseline 9.C2','detect_km_max':45},
    '대잠': {'sensor':'국산 첨단 통합소나체계',       'detect_km_max':50},
}


# ════════════════════════════════════════════════════════════════════════════
#  NEW-K: 함정 DB + 편대 프리셋 (v6.3)
# ════════════════════════════════════════════════════════════════════════════
SHIP_DB = {
    # ── 이지스 구축함 Batch I (KDX-III 세종대왕급: 세종대왕·율곡이이·서애류성룡) ──
    # SPY-1D(V) / Mk.41 VLS 80셀 / SM-3 미탑재 (BMD 불가)
    'KDX-III-B1': {
        'display':      '이지스 구축함 KDX-III Batch I (세종대왕급)',
        'sensor_km':    {'대공': 900, '대함': 45, '대잠': 50},
        'max_channels': 18,
        'eccm_factor':  0.65,  # AN/SLQ-32E SEWIP Block 2
        'role':         ['대공', '대함', '대잠'],
        'default_inventory': {
            'SM-2 Block IIIB':   64,   # Mk.41 VLS 80셀 위주 탑재
            'RIM-116 RAM':       42,   # 21셀 × 2기
            '홍상어 (대잠)':     16,
            '청상어 (경어뢰)':   12,
            'Mk.46 경어뢰':       8,
            'CIWS-II (Phalanx)': 9999,
        },
    },
    # ── 이지스 구축함 Batch II (KDX-III 정조대왕급: 정조대왕함) ──────────────
    # 개량형 SPY-1D(V) / VLS 증설 / SM-3 Block IIA 32셀 / BMD 가능
    'KDX-III-B2': {
        'display':      '이지스 구축함 KDX-III Batch II (정조대왕급)',
        'sensor_km':    {'대공': 900, '대함': 45, '대잠': 50},
        'max_channels': 24,
        'eccm_factor':  0.70,  # AN/SLQ-32E SEWIP Block 3 (최신)
        'role':         ['대공', '대함', '대잠', 'BMD'],
        'default_inventory': {
            'SM-3 Block IIA':    32,   # Batch II: 전방 VLS 32셀 SM-3 전담
            'SM-6':              32,
            'SM-2 Block IIIB':   48,
            'RIM-116 RAM':       21,
            '홍상어 (대잠)':     16,
            '청상어 (경어뢰)':   12,
            'Mk.46 경어뢰':       8,
            'CIWS-II (Phalanx)': 9999,
        },
    },
    # ── 구축함 (KDX-II 충무공이순신급) ──────────────────────────────────────
    'KDX-II': {
        'display':      '구축함 (KDX-II 충무공이순신급)',
        'sensor_km':    {'대공': 250, '대함': 40, '대잠': 40},
        'max_channels': 12,
        'eccm_factor':  0.50,  # SLQ-200 SONATA
        'role':         ['대공', '대함', '대잠'],
        'default_inventory': {
            'SM-2 Block IIIB':  32,
            'RIM-116 RAM':      21,
            '청상어 (경어뢰)':  12,
            'Mk.46 경어뢰':      4,
            'CIWS-II (Phalanx)': 9999,
        },
    },
    # ── 호위함 Batch I (FFX-I 인천급: 인천·전북·강원·경기·부산·서울) ─────────
    # SPS-520K 레이더 / Mk.41 VLS 16셀 / SM-2 × 16 + RAM × 21
    'FFX-I': {
        'display':      '호위함 FFX Batch I (인천급)',
        'sensor_km':    {'대공': 100, '대함': 35, '대잠': 45},
        'max_channels': 8,
        'eccm_factor':  0.40,
        'role':         ['대공', '대함', '대잠'],
        'default_inventory': {
            'SM-2 Block IIIB':   16,
            'RIM-116 RAM':       21,
            '청상어 (경어뢰)':    8,
            'Mk.46 경어뢰':       4,
            'CIWS-II (Phalanx)': 9999,
        },
    },
    # ── 호위함 Batch II (FFX-II 대구급: 대구·경남·전남·광주·진주 등) ─────────
    # SPS-550K AESA 레이더 / KVLS 32셀 해궁 추가 / 채널 개선
    'FFX-II': {
        'display':      '호위함 FFX Batch II (대구급)',
        'sensor_km':    {'대공': 100, '대함': 38, '대잠': 48},
        'max_channels': 10,
        'eccm_factor':  0.45,  # SPS-550K AESA + EW
        'role':         ['대공', '대함', '대잠'],
        'default_inventory': {
            'SM-2 Block IIIB':   16,
            '해궁 (K-SAAM)':     32,   # KVLS 32셀 국산 단거리 함대공
            'RIM-116 RAM':       21,
            '청상어 (경어뢰)':    8,
            'Mk.46 경어뢰':       4,
            'CIWS-II (Phalanx)': 9999,
        },
    },
    # ── 호위함 Batch III (FFX-III 충남급: 충남·충북·울산 등, 건조 중) ─────────
    # 개량형 AESA + 확장 VLS / 해궁 블록 II / 채널 추가
    'FFX-III': {
        'display':      '호위함 FFX Batch III (충남급)',
        'sensor_km':    {'대공': 120, '대함': 40, '대잠': 50},
        'max_channels': 12,
        'eccm_factor':  0.50,  # 개량형 AESA
        'role':         ['대공', '대함', '대잠'],
        'default_inventory': {
            'SM-2 Block IIIB':   16,
            '해궁 (K-SAAM)':     48,   # 확장 KVLS 48셀
            'RIM-116 RAM':       21,
            '청상어 (경어뢰)':   12,
            'Mk.46 경어뢰':       4,
            'CIWS-II (Phalanx)': 9999,
        },
    },
    # ── 유도탄 고속함 (PKG 윤영하급) ─────────────────────────────────────────
    # 570톤 / 40노트+ / 대함 특화 — 해성-I × 4, 40mm CIWS × 1
    # 방공 SAM 없음 → 채널 2 (CIWS 우선 자체방어 수준)
    'PKG': {
        'display':      '유도탄 고속함 (PKG 윤영하급)',
        'sensor_km':    {'대공': 50, '대함': 30, '대잠': 10},
        'max_channels': 2,
        'eccm_factor':  0.25,
        'role':         ['대함'],
        'default_inventory': {
            '해성-I (대함순항)':  4,
            'CIWS-II (Phalanx)': 9999,
        },
    },
    # ── 초계함 (PCC 포항급) ───────────────────────────────────────────────────
    # 1,200톤 / 32노트 / 연안 초계 — 하푼 × 4, 40mm CIWS × 2, Mk.46 × 6
    'PCC': {
        'display':      '초계함 (PCC 포항급)',
        'sensor_km':    {'대공': 80, '대함': 35, '대잠': 35},
        'max_channels': 4,
        'eccm_factor':  0.25,
        'role':         ['대공', '대함', '대잠'],
        'default_inventory': {
            '하푼 Block II (AGM-84)': 4,
            'CIWS-II (Phalanx)':     9999,
            'Mk.46 경어뢰':           6,
        },
    },
    # ── 유도탄 고속정 (PKX-B 참수리-II) ──────────────────────────────────────
    # 200톤 / 40노트+ / 연안 급속 대응 — 해성-I × 2, 40mm × 1
    'PKX-B': {
        'display':      '유도탄 고속정 (PKX-B 참수리-II)',
        'sensor_km':    {'대공': 30, '대함': 20, '대잠': 5},
        'max_channels': 1,
        'eccm_factor':  0.20,
        'role':         ['대함'],
        'default_inventory': {
            '해성-I (대함순항)':  2,
            'CIWS-II (Phalanx)': 9999,
        },
    },
    # ── 강습상륙함 (LPH 독도함급 / 마라도함) ─────────────────────────────────
    # 14,500톤 / 22노트 / 헬기 모함·지휘함 — RAM × 42, CIWS × 2, 헬기 15대
    'LPH': {
        'display':      '강습상륙함 (LPH 독도함급)',
        'sensor_km':    {'대공': 100, '대함': 40, '대잠': 55},
        'max_channels': 6,
        'eccm_factor':  0.45,
        'role':         ['대공', '대잠'],
        'default_inventory': {
            'RIM-116 RAM':       42,   # RAM 21셀 × 2기
            'CIWS-II (Phalanx)': 9999,
            '홍상어 (대잠)':     12,   # 탑재 헬기(AW-101·와일드캣) 운용
            '청상어 (경어뢰)':   12,
            'Mk.46 경어뢰':       8,
        },
    },
    # ── 고속전투지원함 (AOE 소양함) ──────────────────────────────────────────
    # 23,000톤 / 22노트 / 전단 보급·연료·탄약 지원 — 전투력 없음
    'AOE': {
        'display':      '고속전투지원함 (AOE 소양함)',
        'sensor_km':    {'대공': 60, '대함': 30, '대잠': 20},
        'max_channels': 0,
        'eccm_factor':  0.20,
        'role':         ['보급'],
        'default_inventory': {
            'CIWS-II (Phalanx)': 9999,   # 자체방어 최소 CIWS
        },
    },

    # ── 아군 잠수함 (KSS-I/II/III) ──────────────────────────────────────────
    # KSS-I 장보고급 (209형): 1,200톤, 어뢰관 8문, 청상어 + UGM-84 하푼
    'KSS-I': {
        'display':      '잠수함 (KSS-I 장보고급)',
        'sensor_km':    {'대공': 0, '대함': 0, '대잠': 25},
        'max_channels': 0,
        'eccm_factor':  0.20,
        'role':         ['대잠', '대함'],
        'is_submarine': True,
        'default_inventory': {
            '청상어 (경어뢰)': 8,
        },
        'default_strike_inventory': {
            '하푼 Block II': 4,   # UGM-84 잠수함발사 하푼 (어뢰관 발사)
        },
    },
    # KSS-II 류관순급 (214형 AIP): 1,800톤, 저소음 AIP 추진, 청상어 전담
    'KSS-II': {
        'display':      '잠수함 (KSS-II 류관순급)',
        'sensor_km':    {'대공': 0, '대함': 0, '대잠': 30},
        'max_channels': 0,
        'eccm_factor':  0.25,
        'role':         ['대잠'],
        'is_submarine': True,
        'default_inventory': {
            '청상어 (경어뢰)': 8,
        },
        'default_strike_inventory': {},
    },
    # KSS-III 도산안창호급: 3,000톤, VLS 6셀, 현무-3C 순항미사일
    'KSS-III': {
        'display':      '잠수함 (KSS-III 도산안창호급)',
        'sensor_km':    {'대공': 0, '대함': 0, '대잠': 35},
        'max_channels': 0,
        'eccm_factor':  0.35,
        'role':         ['대잠', '대함'],
        'is_submarine': True,
        'default_inventory': {
            '청상어 (경어뢰)': 12,
        },
        'default_strike_inventory': {
            '현무-3C': 6,   # VLS 6셀 순항미사일 (사거리 1,500km)
        },
    },

    # ════ 미국 해군 함정 (한미 연합 작전용) ══════════════════════════════════
    # DDG-51 Flight III: SPY-6 AMDR 탑재, MK-41 96셀
    'DDG-51': {
        'display':      '이지스 구축함 (DDG-51 Arleigh Burke Flight III)',
        'sensor_km':    {'대공': 1000, '대함': 50, '대잠': 50},
        'max_channels': 24,
        'eccm_factor':  0.75,  # AN/SLQ-32E SEWIP Block 3 (최신)
        'role':         ['대공', '대함', '대잠', 'BMD'],
        'nation':       'USA',
        'default_inventory': {
            'SM-3 Block IIA':    32,
            'SM-6 Block IB':     32,
            'SM-2 Block IIIB':   48,
            'ESSM Block II':     32,
            'RIM-116 RAM':       21,
            'Mk.46 경어뢰':       8,
            'CIWS-II (Phalanx)': 9999,
            'Tomahawk Block V':   8,
        },
    },
    # CG-47 Ticonderoga: SPY-1B, MK-41 122셀 — 최대 채널 32
    'CG-47': {
        'display':      '이지스 순양함 (CG-47 Ticonderoga)',
        'sensor_km':    {'대공': 450, '대함': 50, '대잠': 55},
        'max_channels': 32,
        'eccm_factor':  0.70,
        'role':         ['대공', '대함', '대잠', 'BMD'],
        'nation':       'USA',
        'default_inventory': {
            'SM-3 Block IIA':    40,
            'SM-6 Block IB':     40,
            'SM-2 Block IIIB':   60,
            'ESSM Block II':     24,
            'RIM-116 RAM':       21,
            'Mk.46 경어뢰':       8,
            'CIWS-II (Phalanx)': 9999,
            'Tomahawk Block V':  16,
        },
    },
    # CVN Nimitz: 항모 자체 방어 (함재기 방어는 별도), RAM × 4기
    'CVN': {
        'display':      '항공모함 (CVN Nimitz급)',
        'sensor_km':    {'대공': 500, '대함': 60, '대잠': 80},
        'max_channels': 12,
        'eccm_factor':  0.65,
        'role':         ['대공', '대잠'],
        'nation':       'USA',
        'default_inventory': {
            'RIM-116 RAM':       84,   # RAM 21셀 × 4기
            'CIWS-II (Phalanx)': 9999,
        },
    },
    # LPD San Antonio: MH-60S·MV-22 탑재 상륙함
    'LPD': {
        'display':      '상륙함 (LPD San Antonio급)',
        'sensor_km':    {'대공': 120, '대함': 45, '대잠': 40},
        'max_channels': 6,
        'eccm_factor':  0.45,
        'role':         ['대공', '대잠'],
        'default_inventory': {
            'ESSM Block II':     16,
            'RIM-116 RAM':       21,
            'Mk.46 경어뢰':       4,
            'CIWS-II (Phalanx)': 9999,
        },
    },
    # SSN Virginia Block V: VPM Tomahawk 65발 + Mk.48 ADCAP 대잠
    'SSN': {
        'display':      '핵잠수함 (SSN Virginia Block V)',
        'sensor_km':    {'대공': 0, '대함': 0, '대잠': 80},
        'max_channels': 4,
        'eccm_factor':  0.45,
        'role':         ['대잠', '대함'],
        'default_inventory': {
            'Mk.46 경어뢰':      26,   # Mk.48 ADCAP 근사
            'Tomahawk Block V':  65,
        },
    },
    # ════ 한국 해군 지원 함정 ══════════════════════════════════════════════════
    'LST': {
        'display':      '상륙함 (LST 천왕봉급)',
        'sensor_km':    {'대공': 60, '대함': 30, '대잠': 15},
        'max_channels': 2,
        'eccm_factor':  0.25,
        'role':         ['보급'],
        'default_inventory': {
            'RIM-116 RAM':       21,
            'CIWS-II (Phalanx)': 9999,
        },
    },
    'AO': {
        'display':      '군수지원함 (AO 천지함)',
        'sensor_km':    {'대공': 40, '대함': 25, '대잠': 10},
        'max_channels': 0,
        'eccm_factor':  0.20,
        'role':         ['보급'],
        'default_inventory': {
            'CIWS-II (Phalanx)': 9999,
        },
    },
}

# ── 편대 프리셋 (한국 해군 기동전단 교리 기반) ──────────────────────────────
# KDX-III Batch I (세종대왕·율곡이이·서애류성룡) → 'KDX-III-B1'  (SM-3 없음)
# KDX-III Batch II (정조대왕함)                 → 'KDX-III-B2'  (SM-3 × 32)
# FFX Batch I  (인천·전북·강원·경기·부산·서울)  → 'FFX-I'
# FFX Batch II (대구·경남·전남·광주·진주 등)    → 'FFX-II'
# FFX Batch III (충남·충북·울산 등, 건조 중)    → 'FFX-III'
FLEET_PRESETS = {
    # 단독 작전 (현재 방식과 동일 — 정조대왕함 1척)
    '단독 작전': [
        {'name': '정조대왕함', 'type': 'KDX-III-B2'},
    ],
    # 기동전단 기본 (균형 편대 — 이지스1 + 구축함1 + 호위함1)
    '기동전단 기본': [
        {'name': '정조대왕함',     'type': 'KDX-III-B2'},
        {'name': '충무공이순신함', 'type': 'KDX-II'},
        {'name': '대구함',         'type': 'FFX-II'},
    ],
    # BMD 중점 (탄도·HGV 방어 특화 — 이지스2 + 구축함1)
    'BMD 중점': [
        {'name': '정조대왕함',     'type': 'KDX-III-B2'},
        {'name': '세종대왕함',     'type': 'KDX-III-B1'},
        {'name': '충무공이순신함', 'type': 'KDX-II'},
    ],
    # 대잠 중점 (잠수함 위협 대응 — 이지스1 + 호위함2)
    '대잠 중점': [
        {'name': '정조대왕함', 'type': 'KDX-III-B2'},
        {'name': '대구함',     'type': 'FFX-II'},
        {'name': '인천함',     'type': 'FFX-I'},
    ],
    # 대잠전단 (수중 위협 집중 대응 — 이지스1 + 호위함2 + KSS-II × 2)
    '대잠전단': [
        {'name': '정조대왕함',   'type': 'KDX-III-B2'},
        {'name': '대구함',       'type': 'FFX-II'},
        {'name': '인천함',       'type': 'FFX-I'},
        {'name': '이순신함(SS)', 'type': 'KSS-II'},
        {'name': '안중근함(SS)', 'type': 'KSS-II'},
    ],
    # 최대 편대 (전면전 — 이지스2 + 구축함2 + 호위함2)
    '최대 편대': [
        {'name': '정조대왕함',     'type': 'KDX-III-B2'},
        {'name': '세종대왕함',     'type': 'KDX-III-B1'},
        {'name': '충무공이순신함', 'type': 'KDX-II'},
        {'name': '문무대왕함',     'type': 'KDX-II'},
        {'name': '대구함',         'type': 'FFX-II'},
        {'name': '인천함',         'type': 'FFX-I'},
    ],

    # ════ 현실 기반 편대 (한국 해군 실 교리 기반) ════════════════════════════
    # 이지스 기동전단 — 정조대왕함 중심, KDX-II 2·FFX 2·보급함 1
    '이지스 기동전단': [
        {'name': '정조대왕함',     'type': 'KDX-III-B2'},
        {'name': '충무공이순신함', 'type': 'KDX-II'},
        {'name': '문무대왕함',     'type': 'KDX-II'},
        {'name': '인천함',         'type': 'FFX-I'},
        {'name': '대구함',         'type': 'FFX-II'},
        {'name': '소양함',         'type': 'AOE'},
    ],
    # 이지스 기동전단 (강화) — 이지스 2척 체제, 전시 확장 편성
    '이지스 기동전단 (강화)': [
        {'name': '정조대왕함',     'type': 'KDX-III-B2'},
        {'name': '세종대왕함',     'type': 'KDX-III-B1'},
        {'name': '충무공이순신함', 'type': 'KDX-II'},
        {'name': '문무대왕함',     'type': 'KDX-II'},
        {'name': '인천함',         'type': 'FFX-I'},
        {'name': '대구함',         'type': 'FFX-II'},
        {'name': '소양함',         'type': 'AOE'},
    ],
    # 전 이지스 기동전단 — 이지스 4척 완전 편성 (최강 방공)
    '전 이지스 기동전단': [
        {'name': '정조대왕함',     'type': 'KDX-III-B2'},
        {'name': '세종대왕함',     'type': 'KDX-III-B1'},
        {'name': '율곡이이함',     'type': 'KDX-III-B1'},
        {'name': '서애류성룡함',   'type': 'KDX-III-B1'},
        {'name': '충무공이순신함', 'type': 'KDX-II'},
        {'name': '대구함',         'type': 'FFX-II'},
        {'name': '소양함',         'type': 'AOE'},
    ],
    # 독도함 상륙전단 — 상륙기동전단, 헬기 대잠 특화
    '독도함 상륙전단': [
        {'name': '독도함',         'type': 'LPH'},
        {'name': '충무공이순신함', 'type': 'KDX-II'},
        {'name': '인천함',         'type': 'FFX-I'},
        {'name': '대구함',         'type': 'FFX-II'},
    ],
    # 동해 해역방어 (1함대) — 구축함 1·호위함 2·고속함 4·초계함 2
    '동해 해역방어 (1함대)': [
        {'name': '대조영함',  'type': 'KDX-II'},
        {'name': '인천함',    'type': 'FFX-I'},
        {'name': '강원함',    'type': 'FFX-I'},
        {'name': '윤영하함',  'type': 'PKG'},
        {'name': '한상국함',  'type': 'PKG'},
        {'name': '조천형함',  'type': 'PKG'},
        {'name': '황도현함',  'type': 'PKG'},
        {'name': '포항함',    'type': 'PCC'},
        {'name': '군산함',    'type': 'PCC'},
    ],
    # 서해 해역방어 (2함대) — 호위함 2·고속함 4·초계함 2
    '서해 해역방어 (2함대)': [
        {'name': '부산함',    'type': 'FFX-I'},
        {'name': '전주함',    'type': 'FFX-I'},
        {'name': '서후원함',  'type': 'PKG'},
        {'name': '박동혁함',  'type': 'PKG'},
        {'name': '이희완함',  'type': 'PKG'},
        {'name': '김두찬함',  'type': 'PKG'},
        {'name': '경주함',    'type': 'PCC'},
        {'name': '목포함',    'type': 'PCC'},
    ],

    # ════ 한미 연합 프리셋 ═══════════════════════════════════════════════════
    # 한미 기동전단 기본 — KDX-III-B2 + DDG-51 × 2 + KDX-II + FFX-II + FFX-I
    '한미 기동전단 기본': [
        {'name': '정조대왕함',     'type': 'KDX-III-B2'},
        {'name': 'USS John Finn',  'type': 'DDG-51'},
        {'name': 'USS Fitzgerald', 'type': 'DDG-51'},
        {'name': '충무공이순신함', 'type': 'KDX-II'},
        {'name': '대구함',         'type': 'FFX-II'},
        {'name': '인천함',         'type': 'FFX-I'},
    ],
    # 한미 기동전단 강화 — KDX-III-B2/B1 × 2 + DDG-51 × 2 + CG-47 + KDX-II × 2 + AOE
    '한미 기동전단 강화': [
        {'name': '정조대왕함',      'type': 'KDX-III-B2'},
        {'name': '세종대왕함',      'type': 'KDX-III-B1'},
        {'name': 'USS John Finn',   'type': 'DDG-51'},
        {'name': 'USS Fitzgerald',  'type': 'DDG-51'},
        {'name': 'USS Bunker Hill', 'type': 'CG-47'},
        {'name': '충무공이순신함',  'type': 'KDX-II'},
        {'name': '문무대왕함',      'type': 'KDX-II'},
        {'name': '소양함',          'type': 'AOE'},
    ],
    # 한미 항모전단 지원 — CVN + DDG-51 × 3 + CG-47 + KDX-III-B2 + KDX-II × 2
    '한미 항모전단 지원': [
        {'name': 'USS Ronald Reagan', 'type': 'CVN'},
        {'name': 'USS John Finn',     'type': 'DDG-51'},
        {'name': 'USS Fitzgerald',    'type': 'DDG-51'},
        {'name': 'USS Milius',        'type': 'DDG-51'},
        {'name': 'USS Bunker Hill',   'type': 'CG-47'},
        {'name': '정조대왕함',        'type': 'KDX-III-B2'},
        {'name': '충무공이순신함',    'type': 'KDX-II'},
        {'name': '문무대왕함',        'type': 'KDX-II'},
    ],
}

REQ_ITEMS = [
    {'id':'REQ-01','name':'탐지거리 충족',         'desc':'날씨보정 유효 탐지거리 <= 센서 최대 탐지거리'},
    {'id':'REQ-02','name':'C&D 시간 충족',         'desc':'설정 C&D 시간 <= 무기사거리 반영 최대 허용 시간'},
    {'id':'REQ-03','name':'1차 요격 가능',          'desc':'C&D 후 남은 거리 기준 요격 가능 여부'},
    {'id':'REQ-04','name':'다층 방어 생존율>=90%',  'desc':'몬테카를로 전탄 요격 성공률 >= 90%'},
    {'id':'REQ-05','name':'최소 탐지거리 충족',     'desc':'설정 탐지거리 >= 역산 최소 필요 탐지거리'},
    {'id':'REQ-06','name':'재교전 가능',            'desc':'재교전 소요시간 <= 최대 허용 판단시간'},
    {'id':'REQ-07','name':'재고 충분',              'desc':'교전 후 주요 무기 잔여 재고 1발 이상'},
    {'id':'REQ-08','name':'채널 한계 미초과',       'desc':f'동시 위협 수 <= 교전 채널 ({MAX_ENGAGEMENT_CHANNELS}개)'},
]

# ════════════════════════════════════════════════════════════════════════════
#  NEW-G / 미구현-3·4: ENEMY_DB 정규화 (ENEMY_DB 정의 이후 위치)
# ════════════════════════════════════════════════════════════════════════════
def normalize_enemy_db():
    TYPE_TEV = {
        '전투기':0.88,'전폭기':0.90,'폭격기':0.95,
        '탄도미사일':1.00,'극초음속활공체':1.00,'저고도기동탄도':1.00,
        '순항미사일':0.87,'고속정':0.98,'초계함':0.98,
        '호위함':0.97,'구축함':0.97,'잠수함':0.95,'어뢰':0.95,
        '대방사미사일':0.85,  # ARM: 레이더 전파 역추적, 요격 어려움
    }
    TYPE_ECM = {
        '전투기':0.10,'전폭기':0.10,'폭격기':0.05,
        '탄도미사일':0.00,'극초음속활공체':0.00,'저고도기동탄도':0.00,
        '순항미사일':0.05,'고속정':0.08,'초계함':0.10,
        '호위함':0.15,'구축함':0.20,'잠수함':0.00,'어뢰':0.00,
        '대방사미사일':0.00,  # ARM: ECM 재밍이 오히려 표적이 됨 — 무효
    }
    for _, e in ENEMY_DB.items():
        et = e.get('type','')
        e.setdefault('is_hgv', False)
        e.setdefault('is_qbm', False)
        e.setdefault('is_arm', False)
        e.setdefault('terminal_evasion_factor', TYPE_TEV.get(et, 1.0))
        e.setdefault('ecm_power',               TYPE_ECM.get(et, 0.0))
        e.setdefault('self_defense_pk',      0.0)
        e.setdefault('enemy_ciws_pk',        0.0)
        e.setdefault('hp',                   None)   # None → EnemyThreatObj._HP_MAP 사용
        e.setdefault('high_value_target',    False)
        e.setdefault('carrier_aircraft',     None)
        e.setdefault('carrier_wave_interval', 0)
        # v6.8: ECM 취약도 (seeker 유형별 차등)
        # radar=레이더 유도(full), ir=적외선 유도(약), combined=복합(중간), none=무효
        TYPE_ECM_SUSC = {
            '전투기':'radar','전폭기':'radar','폭격기':'radar',
            '탄도미사일':'none','극초음속활공체':'none','저고도기동탄도':'none',
            '순항미사일':'radar','고속정':'radar','초계함':'radar',
            '호위함':'combined','구축함':'combined','잠수함':'none','어뢰':'none',
            '대방사미사일':'none',  # ARM: 레이더 전파 역추적 — 일반 ECM 무효
        }
        e.setdefault('ecm_susceptibility', TYPE_ECM_SUSC.get(et, 'radar'))
        # v8.26: 채프/플레어/DRFM 세분화 — ecm_susceptibility 기반 자동 분배
        susc = e.get('ecm_susceptibility', 'radar')
        sdpk = e.get('self_defense_pk', 0.0)
        if susc == 'radar':
            e.setdefault('chaff_pk', sdpk)
            e.setdefault('flare_pk', sdpk * 0.10)
            e.setdefault('drfm_pk',  sdpk * 0.30)
        elif susc == 'ir':
            e.setdefault('chaff_pk', sdpk * 0.10)
            e.setdefault('flare_pk', sdpk)
            e.setdefault('drfm_pk',  sdpk * 0.30)
        elif susc == 'combined':
            e.setdefault('chaff_pk', sdpk * 0.50)
            e.setdefault('flare_pk', sdpk * 0.50)
            e.setdefault('drfm_pk',  sdpk * 0.70)
        else:  # none (탄도·HGV·어뢰·ARM)
            e.setdefault('chaff_pk', 0.0)
            e.setdefault('flare_pk', 0.0)
            e.setdefault('drfm_pk',  0.0)
        # v6.8: 방위각 (0~360°, 0=정면) — 시뮬 실행 시 동적 할당
        e.setdefault('bearing_deg', 0)
        e.setdefault('missile_terminal_evasion', 1.0)
        ep = e.setdefault('evasion_profile', {})
        for k, v in [('speed_boost_min',0),('speed_boost_max',0),
                     ('alt_change_m',0),('depth_change_m',0),('max_attempts',0)]:
            ep.setdefault(k, v)

normalize_enemy_db()

_ECM_OVR = {
    'J-20 (위룡)':0.35,'Su-35 (플랭커-E)':0.25,'J-16 (플랭커-D)':0.22,
    'J-16D (전자전기)':0.55,  # v8.26: 전자전 전용기 (강력한 재밍 파드)
    'J-15 (비상어)':0.18,'J-11B (플랭커-B)':0.15,'J-10A (비맹)':0.15,
    'JH-7A (날치)':0.12,'MiG-29 (풀크럼)':0.08,'MiG-23 (플로거)':0.06,
    'J-7 (섬광)':0.03,'H-6 (폭격기)':0.05,
    '055형 대형 구축함':0.28,'052D형 구축함':0.22,'054A형 호위함':0.18,
    '056형 초계함':0.12,'022형 미사일 고속정':0.08,
    'P-800 오닉스 (야혼트)':0.08,'YJ-12 (초음속 순항)':0.06,
    # NEW-P1: 신규 추가 항목
    'J-35 (백상어)':0.32,'J-10C (맹룡 개량)':0.18,'H-6N (폭격기 개량)':0.05,
    '052C형 구축함 (HHQ-9)':0.20,'071형 상륙함':0.10,
    'Su-57 (펠론)':0.30,'Tu-22M3 (백파이어)':0.08,
    '우달로이급 구축함':0.18,'슬라바급 순양함':0.22,
}
for _n, _v in _ECM_OVR.items():
    if _n in ENEMY_DB: ENEMY_DB[_n]['ecm_power'] = _v

# ════════════════════════════════════════════════════════════════════════════
#  NEW-H: 함재 헬기 + 날씨 출격 제한
# ════════════════════════════════════════════════════════════════════════════
# 헬기 날씨 제한 (풍랑↑ 출격 불가) — 인라인 dict 정의
_HELO_WX = {
    '맑음 (주간)':True,'맑음 (야간)':True,'흐림 (박무)':True,
    '황사 (봄철 황사)':True,'풍랑 (7~8등급)':False,
    '폭풍 (해상 악화)':False,'태풍 (9~12등급)':False,
    '농무 (시정 200m 이하)':False,
    # v9.2 복합 환경
    '폭풍 (야간)':False,'태풍 (야간)':False,
    '농무 (야간)':False,'황사 (새벽)':True,
}
# P-3C 날씨 제한 (태풍만 불가, 계기비행 가능)
_P3C_WX  = {
    '맑음 (주간)':True,'맑음 (야간)':True,'흐림 (박무)':True,
    '황사 (봄철 황사)':True,'풍랑 (7~8등급)':True,
    '폭풍 (해상 악화)':True,'태풍 (9~12등급)':False,
    '농무 (시정 200m 이하)':True,
    # v9.2 복합 환경
    '폭풍 (야간)':True,'태풍 (야간)':False,
    '농무 (야간)':True,'황사 (새벽)':True,
}

FRIENDLY_AIRCRAFT_DB = {
    'AW-159 와일드캣': {
        'speed_ms':78,'range_km':140,'sortie_time_s':300,  # LOW-10: 100→78 m/s (Wildcat 실제 순항속도 ~150 kts)
        'payload_wpn':'청상어 (경어뢰)','payload_cnt':2,
        'cost_usd':HELO_SORTIE_COST_USD,'pk_bonus':0.05,'on_deck':True,
        'base_type':'ship','weather_limits':_HELO_WX,
        # v9.8: 디핑소나 탐지 모델
        'asw_mode':         'dipping',  # 디핑소나 방식
        'dip_hover_s':      60,         # 호버링+소나 전개 시간(초)
        'detect_base_prob': 0.60,       # 탐지 기본 확률
        'max_attempts':     3,          # 최대 재탐색 횟수
        'retry_s':          90,         # 탐지 실패 후 재시도 대기(초)
    },
    'MH-60R 시호크': {
        'speed_ms':110,'range_km':200,'sortie_time_s':240,
        'payload_wpn':'청상어 (경어뢰)','payload_cnt':2,
        'cost_usd':int(HELO_SORTIE_COST_USD*1.2),'pk_bonus':0.08,'on_deck':False,
        'base_type':'ship','weather_limits':_HELO_WX,
        # v9.8: 디핑소나 탐지 모델 (MH-60R이 AW-159보다 우수한 AN/AQS-22)
        'asw_mode':         'dipping',
        'dip_hover_s':      45,         # 더 빠른 소나 전개
        'detect_base_prob': 0.70,       # MH-60R 고성능 소나
        'max_attempts':     3,
        'retry_s':          75,
    },
    # NEW-I: P-3C 오라이온 — 육상기지(포항) 출격 해상초계기
    # 헬기 사거리(70km) 밖 잠수함 공격 / 소노부이 광역 탐색
    'P-3C 오라이온': {
        'speed_ms':     180,          # 순항속도 648 km/h
        'range_km':     2000,         # 편도 작전반경
        'sortie_time_s':2400,         # 출격 준비 40분
        'payload_wpn':  'Mk.46 경어뢰',
        'payload_cnt':  4,
        'cost_usd':     300000,       # 출격 비용 (연료+정비)
        'pk_bonus':     0.10,         # 소노부이 정밀화 보너스
        'on_deck':      True,
        'base_type':    'land',       # 육상기지 출격
        'base_name':    '포항기지',
        'base_dist_km': 300,          # 포항 → 작전해역 기본거리
        'sonobuoy_detect_bonus_km': 8,   # MED-11: 15→8 km (실 AN/SSQ-53F 부이 탐지 보정)
        'weather_limits':_P3C_WX,
        # v9.8: 소노부이 탐지 모델
        'asw_mode':         'sonobuoy', # 소노부이 투하 방식
        'detect_base_prob': 0.68,       # AN/SSQ-53F 소노부이 탐지율
        'retry_s':          120,        # 소노부이 재투하 간격
        'max_attempts':     4,
    },
    # NEW-J: P-8A 포세이돈 — 미 해군/한국 해군 도입 추진 중
    # P-3C 후속 기종. 737 기반 고속 순항, 소노부이 성능 향상
    # 포항기지 출격, 태풍 외 전천후 운용 가능
    'P-8A 포세이돈': {
        'speed_ms':     230,          # 순항속도 828 km/h
        'range_km':     2200,         # 편도 작전반경
        'sortie_time_s':1800,         # 출격 준비 30분 (P-3C 40분보다 빠름)
        'payload_wpn':  'Mk.46 경어뢰',
        'payload_cnt':  5,
        'cost_usd':     450000,       # 출격 비용 (연료+정비)
        'pk_bonus':     0.13,         # 소노부이 정밀화 보너스 (P-3C 0.10보다 우수)
        'on_deck':      True,
        'base_type':    'land',       # 육상기지 출격
        'base_name':    '포항기지',
        'base_dist_km': 300,          # 포항 → 작전해역 기본거리
        'sonobuoy_detect_bonus_km': 10,  # MED-11: 18→10 km (실 AN/SSQ-62 DICASS 탐지 보정)
        'weather_limits':_P3C_WX,    # 태풍만 불가 (P-3C와 동일)
        # v9.8: 소노부이 탐지 모델 (AN/SSQ-62 DICASS — P-3C 대비 성능 우수)
        'asw_mode':         'sonobuoy',
        'detect_base_prob': 0.80,       # P-3C 대비 +12%p
        'retry_s':          100,        # 더 빠른 재투하
        'max_attempts':     5,          # 탑재량 많아 더 많이 시도 가능
    },
}

# ════════════════════════════════════════════════════════════════════════════
#  NEW-L: 적군 편대 프리셋 + 랜덤 난이도 설정 (v6.4)
# ════════════════════════════════════════════════════════════════════════════
# PLA 해군·공군 교리 기반 5종 프리셋
ENEMY_FLEET_PRESETS = {
    # A2/AD 항공 포화 공격 — 전투기+폭격기 장거리 타격
    'A2/AD 항공 포화': [
        {'preset': 'J-16 (플랭커-D)',  'count': 4},
        {'preset': 'H-6 (폭격기)',     'count': 2},
    ],
    # 항모 킬 체인 — 탄도+HGV+스텔스 복합
    '항모 킬 체인': [
        {'preset': 'DF-21D (대함 탄도)',    'count': 2},
        {'preset': 'DF-17 (극초음속 활공)', 'count': 1},
        {'preset': 'J-20 (위룡)',           'count': 2},
    ],
    # 수상함 편대전 — 함포·미사일 집중
    '수상함 편대전': [
        {'preset': '055형 대형 구축함', 'count': 1},
        {'preset': '052D형 구축함',     'count': 2},
        {'preset': '022형 미사일 고속정','count': 4},
    ],
    # 대잠 복합 — 잠수함 2척 동시 위협
    '대잠 복합': [
        {'preset': '093형 잠수함 (상급)', 'count': 1},
        {'preset': '039형 잠수함 (송급)',   'count': 1},
    ],
    # BMD 탄도 포화 — 순수 탄도·HGV 방어 전용 (SM-3/SM-6 BMD 성능 평가)
    'BMD 탄도 포화': [
        {'preset': 'KN-23 (북한 이스칸데르)',   'count': 2},   # QBM: SM-3 무력화, SM-6/ESSM 대응
        {'preset': 'DF-15 (단거리 탄도)',       'count': 2},   # SRBM: SM-3 주 요격
        {'preset': 'DF-21D (대함 탄도)',        'count': 2},   # MRBM: SM-3 필수
        {'preset': 'DF-17 (극초음속 활공)',     'count': 1},   # HGV: SM-3만 가능, 최고 난이도
    ],
    # 전면전 포화 — 모든 카테고리 혼합 (최고 난이도)
    '전면전 포화': [
        {'preset': 'J-20 (위룡)',           'count': 2},
        {'preset': 'DF-17 (극초음속 활공)', 'count': 1},
        {'preset': '055형 대형 구축함',     'count': 1},
        {'preset': 'DF-21D (대함 탄도)',    'count': 1},
        {'preset': '093형 잠수함 (상급)', 'count': 1},
    ],
    # 북한 탄도 포화 — 화성 계열 + 순항
    '북한 탄도 포화': [
        {'preset': 'KN-23 (북한 이스칸데르)',      'count': 3},
        {'preset': '화성-15 (북한 ICBM급)',        'count': 1},
        {'preset': '북한 순항미사일 (화살-2)',      'count': 2},
    ],
    # 러시아 극초음속 — 킨잘·지르콘·스텔스 순항
    '러시아 극초음속': [
        {'preset': '킨잘 (극초음속 탄도)',    'count': 2},
        {'preset': '지르콘 (극초음속 순항)', 'count': 2},
        {'preset': 'Kh-101 (스텔스 순항)', 'count': 2},
    ],
    # 잠수함 복합 — 다중 잠수함 대잠 압박
    '잠수함 복합 포화': [
        {'preset': '039형 잠수함 (송급)',   'count': 3},
        {'preset': '093형 잠수함 (상급)', 'count': 1},
    ],
    # 중국 항모전단 — 랴오닝 전단 (PLAN CV-16 전단)
    '랴오닝 항모전단': [
        {'preset': '랴오닝 (항모)',     'count': 1},
        {'preset': '055형 대형 구축함', 'count': 1},
        {'preset': '052D형 구축함',     'count': 2},
        {'preset': '054A형 호위함',     'count': 2},
        {'preset': '093형 잠수함 (상급)', 'count': 1},
    ],
    # 중국 항모전단 — 산둥 전단 (PLAN CV-17 전단)
    '산둥 항모전단': [
        {'preset': '산둥 (항모)',       'count': 1},
        {'preset': '055형 대형 구축함', 'count': 1},
        {'preset': '052D형 구축함',     'count': 3},
        {'preset': '039형 잠수함 (송급)', 'count': 1},
    ],
    # 중국 항모전단 — 푸젠 전단 (PLAN CV-18 전단, 최강 전력)
    '푸젠 항모전단': [
        {'preset': '푸젠 (항모)',       'count': 1},
        {'preset': '055형 대형 구축함', 'count': 2},
        {'preset': '052D형 구축함',     'count': 3},
        {'preset': '093형 잠수함 (상급)', 'count': 2},
    ],
    # 북한 포화 공격 20발 — 화성·KN 계열 대규모 일제 발사 (SM-3 재고 한계 시험)
    '북한 포화 공격 (20발)': [
        {'preset': 'KN-23 (북한 이스칸데르)',  'count': 8},
        {'preset': 'KN-24 (단거리 기동탄도)', 'count': 4},
        {'preset': '화성-12 (IRBM)',          'count': 4},
        {'preset': '화성-15 (북한 ICBM급)',   'count': 4},
    ],
    # 북한 포화 공격 40발 — 전면전 수준 포화 공격 (최고 난이도)
    '북한 포화 공격 (40발)': [
        {'preset': 'KN-23 (북한 이스칸데르)',  'count': 16},
        {'preset': 'KN-24 (단거리 기동탄도)', 'count': 8},
        {'preset': '화성-12 (IRBM)',          'count': 8},
        {'preset': '화성-15 (북한 ICBM급)',   'count': 4},
        {'preset': '화성-18 (ICBM 고체연료)', 'count': 4},
    ],
    # ── v9.1: 다층 동시 위협 프리셋 ──────────────────────────────────────────
    # 공중·수상·수중 3개 영역이 동시에 들어오는 복합 시나리오
    # 중국 3축 동시 공격 — 항공+수상함+잠수함 동시 (중간 난이도)
    '중국 3축 동시 공격': [
        {'preset': 'J-16 (플랭커-D)',          'count': 2},  # 공중: YJ-12 초음속 대함
        {'preset': '052D형 구축함',            'count': 2},  # 수상: YJ-18 초음속 대함
        {'preset': '039형 잠수함 (송급)',       'count': 2},  # 수중: 어뢰+YJ-82
    ],
    # 입체 포화 (최강) — 공중+HGV+수상+수중 4차원 동시 (최고 난이도)
    '입체 포화 (최강)': [
        {'preset': 'J-20 (위룡)',              'count': 2},  # 공중: 스텔스 전투기
        {'preset': 'DF-17 (극초음속 활공)',    'count': 1},  # 공중: HGV (SM-3 필수)
        {'preset': '055형 대형 구축함',        'count': 1},  # 수상: VLS 112셀 YJ-21
        {'preset': '093형 잠수함 (상급)',      'count': 1},  # 수중: 핵잠 어뢰
    ],
    # 북한 입체 공격 — 항공+탄도+잠수함 3축 (중간 난이도)
    '북한 입체 공격': [
        {'preset': 'MiG-29 (풀크럼)',          'count': 2},  # 공중: Kh-31A 대함
        {'preset': 'KN-23 (북한 이스칸데르)', 'count': 2},  # 탄도: QBM THAAD 교란
        {'preset': '신포급 잠수함 (SLBM)',     'count': 1},  # 수중: 어뢰+북극성-1
    ],
    # 러시아 해군 입체 — 폭격기+순양함+잠수함 3축 (높은 난이도)
    '러시아 해군 입체': [
        {'preset': 'Tu-22M3 (백파이어)',       'count': 1},  # 공중: Kh-32 초음속 대함
        {'preset': '슬라바급 순양함',          'count': 1},  # 수상: P-1000 × 16 + S-300F
        {'preset': '킬로급 잠수함 (Project 636)', 'count': 1},  # 수중: Kalibr 대함
    ],
    # ── v9.6: 북한 잠수함 선제 기습 프리셋 ──────────────────────────────────────
    # 신포급(기습) — 수온약층 내 잠복 120초 후 어뢰+해성-3 동시 기습 발사
    '북한 잠수함 선제 기습': [
        {'preset': '신포급 잠수함 (기습)',  'count': 2},  # 수중: 기습 어뢰+해성-3
        {'preset': '039형 잠수함 (송급)',   'count': 3},  # 수중: 어뢰 압박
    ],
    '북한 잠수함 기습 (소형)': [
        {'preset': '신포급 잠수함 (기습)',  'count': 1},  # 수중: 기습
        {'preset': '039형 잠수함 (송급)',   'count': 2},  # 수중: 어뢰
    ],
    # ── v9.14: 해협 통과 방어 전용 프리셋 ────────────────────────────────────────
    # 이어도 방어전 — 중국 이어도 분쟁 시나리오 (제주 서남방, 서수도 접근)
    '이어도 방어전': [
        {'preset': 'J-10C (맹룡 개량)',    'count': 3},  # 공중: YJ-12K 대함
        {'preset': '054A형 호위함',        'count': 2},  # 수상: YJ-18 + HHQ-16
        {'preset': '039형 잠수함 (송급)',  'count': 1},  # 수중: 어뢰 (서수도 천해 제한)
    ],
    # 대한해협 통과 저지 — 동·서수도 동시 돌파 시도 (최협착 고밀도 수상함)
    '대한해협 통과 저지': [
        {'preset': '022형 미사일 고속정',  'count': 6},  # 수상: YJ-12 × 6 고속 돌파
        {'preset': 'J-11B (플랭커-B)',     'count': 2},  # 공중: Kh-31AD 초음속 엄호
        {'preset': '039형 잠수함 (송급)',  'count': 1},  # 수중: 어뢰 (동수도 통과)
    ],
    # 쓰시마 봉쇄 돌파 — 러시아 동수도 강제 통과 (일본해→남해 전략이동)
    '쓰시마 봉쇄 돌파': [
        {'preset': 'Tu-22M3 (백파이어)',               'count': 2},  # 공중: Kh-32 고고도 초음속
        {'preset': '킬로급 잠수함 (Project 636)',       'count': 2},  # 수중: Kalibr 대함
        {'preset': '슬라바급 순양함',                  'count': 1},  # 수상: P-1000 × 16
    ],
}

# ── 혼합 공격 시나리오 (NEW-A: v7.12) ────────────────────────────────────────
# 각 시나리오는 파도(wave)별로 위협을 정의한다.
# delay_s: 시뮬레이션 시작 후 해당 파도가 출현하는 시각 (초)
MIXED_ATTACK_SCENARIOS = {
    '순항미사일 + 탄도탄 복합': {
        'description': '1파: 순항미사일 4발로 SM-2 재고 소모 → 2파: 탄도탄으로 SM-3 강요 — 재고 연속 압박',
        'waves': [
            {'delay_s':   0, 'threats': [{'preset': 'CJ-10 (순항미사일)', 'count': 4}]},
            {'delay_s':  60, 'threats': [{'preset': 'DF-21D (대함 탄도)', 'count': 2}]},
        ],
    },
    '잠수함 어뢰 + 대함미사일 병행': {
        'description': '잠수함 어뢰로 대잠 전력 분산 + 수상함 대함미사일 동시 공격 — 채널 양분 강요',
        'waves': [
            {'delay_s':  0, 'threats': [{'preset': '039형 잠수함 (송급)', 'count': 2}]},
            {'delay_s':  0, 'threats': [{'preset': '022형 미사일 고속정', 'count': 4}]},
        ],
    },
    '항모 킬 체인 (스텔스→HGV→초음속)': {
        'description': 'J-20 스텔스로 방공망 혼란 → DF-17 극초음속으로 방어 돌파 → YJ-18 초음속 마무리',
        'waves': [
            {'delay_s':  0, 'threats': [{'preset': 'J-20 (위룡)', 'count': 2}]},
            {'delay_s': 30, 'threats': [{'preset': 'DF-17 (극초음속 활공)', 'count': 1}]},
            {'delay_s': 50, 'threats': [{'preset': 'YJ-18 (초음속 대함)', 'count': 3}]},
        ],
    },
    '전방위 포화 공격 (채널 포화)': {
        'description': '전투기·탄도탄·순항미사일이 동시 출현 — 모든 교전 채널 동시 포화 테스트',
        'waves': [
            {'delay_s':  0, 'threats': [
                {'preset': 'J-16 (플랭커-D)',     'count': 3},
                {'preset': 'DF-21D (대함 탄도)',  'count': 2},
                {'preset': 'CJ-10 (순항미사일)',  'count': 4},
            ]},
        ],
    },
    '러시아 살라미 공격': {
        'description': '킨잘로 BMD 재고 소모 → 지르콘 마하 9 돌파 → Kh-101 스텔스 잔여 목표 타격',
        'waves': [
            {'delay_s':  0, 'threats': [{'preset': '킨잘 (극초음속 탄도)', 'count': 2}]},
            {'delay_s': 40, 'threats': [{'preset': '지르콘 (극초음속 순항)', 'count': 2}]},
            {'delay_s': 70, 'threats': [{'preset': 'Kh-101 (스텔스 순항)', 'count': 3}]},
        ],
    },
    '북한 전면 도발': {
        'description': 'KN-23 + 화성-15 탄도탄으로 BMD 강요 → 화살-2 순항미사일 후속 타격',
        'waves': [
            {'delay_s':  0, 'threats': [
                {'preset': 'KN-23 (북한 이스칸데르)', 'count': 3},
                {'preset': '화성-15 (북한 ICBM급)',   'count': 1},
            ]},
            {'delay_s': 30, 'threats': [{'preset': '북한 순항미사일 (화살-2)', 'count': 4}]},
        ],
    },
    '대잠·대공 동시 압박': {
        'description': '잠수함·전투기 동시 접근으로 대잠/대공 채널 분리 강요, 초음속 대함 마무리',
        'waves': [
            {'delay_s':  0, 'threats': [
                {'preset': '093형 잠수함 (상급)', 'count': 1},
                {'preset': 'J-15 (비상어)',       'count': 3},
            ]},
            {'delay_s': 45, 'threats': [{'preset': 'YJ-12 (초음속 순항)', 'count': 4}]},
        ],
    },
}

# 랜덤 적군 편대 난이도 설정
ENEMY_FLEET_RANDOM_CFG = {
    '쉬움':   {
        'total_count': (2, 4),
        'pool': ['MiG-29 (풀크럼)', 'J-10A (비맹)', 'J-11B (플랭커-B)',
                 'CJ-10 (순항미사일)', '056형 초계함', '039형 잠수함 (송급)'],
        'max_types': 2,
    },
    '보통':   {
        'total_count': (4, 8),
        'pool': ['J-16 (플랭커-D)', 'Su-35 (플랭커-E)', 'J-15 (비상어)',
                 'YJ-12 (초음속 순항)', 'DF-11A (단거리 탄도)',
                 '052D형 구축함', '054A형 호위함', '041형 잠수함 (위안급 개량)'],
        'max_types': 3,
    },
    '어려움': {
        'total_count': (8, 14),
        'pool': ['J-20 (위룡)', 'H-6 (폭격기)', 'DF-15 (단거리 탄도)',
                 'DF-21D (대함 탄도)', 'DF-17 (극초음속 활공)',
                 '055형 대형 구축함', '022형 미사일 고속정',
                 '093형 잠수함 (상급)'],
        'max_types': 4,
    },
    '극한':   {
        'total_count': (14, 24),
        'pool': list({  # 전 32종 사용
            'J-20 (위룡)', 'H-6 (폭격기)', 'DF-26 (중장거리 탄도)',
            'DF-17 (극초음속 활공)', 'KN-23 (북한 이스칸데르)',
            '055형 대형 구축함', '022형 미사일 고속정',
            '094형 잠수함 (진급)',
        }),
        'max_types': 6,
    },
}

# ════════════════════════════════════════════════════════════════════════════
#  함정 전투 상태
# ════════════════════════════════════════════════════════════════════════════
class ShipStatus:
    def __init__(self, decoy_stock=4):
        self.operational         = True
        self.hit_count           = 0
        self.hit_time            = None
        self.hit_by              = []
        self.decoy_stock         = decoy_stock
        self.decoys_fired        = 0
        self.decoy_success_count = 0
        # NEW-F: 적 자체방어 통계
        self.enemy_ciws_intercept  = 0   # 적 CIWS 요격 성공 횟수
        self.helo_sorties    = 0
        self.helo_intercepts = 0   # self_defense_pk 적용으로 Pk 감소된 발 수

    def register_hit(self, label, t):
        self.hit_count += 1
        self.hit_by.append(label)
        if self.hit_time is None: self.hit_time = t
        self.operational = False

    def try_decoy(self):
        if self.decoy_stock <= 0:
            return False, '기만기 소진'
        self.decoy_stock -= 1
        self.decoys_fired += 1
        if random.random() < DECOY_PK:
            self.decoy_success_count += 1
            return True, f'기만 성공 (잔여 {self.decoy_stock}개)'
        return False, f'기만 실패 (잔여 {self.decoy_stock}개)'


# ════════════════════════════════════════════════════════════════════════════
#  NEW-K: 편대 클래스 — Ship / Fleet / FleetStatus / FleetChannelManager
# ════════════════════════════════════════════════════════════════════════════
class Ship:
    """편대 내 개별 함정 — 자체 재고·채널·조명기·상태를 보유"""
    def __init__(self, name, ship_type, inventory=None, decoy_stock=4):
        self.name        = name
        self.ship_type   = ship_type
        spec             = SHIP_DB[ship_type]
        self.display     = spec['display']
        self.sensor_km   = spec['sensor_km']
        self.max_channels= spec['max_channels']
        self.role        = spec['role']
        self.inventory   = (inventory or spec['default_inventory']).copy()
        self.status      = ShipStatus(decoy_stock=decoy_stock)
        self.ch_mgr      = ChannelManager(self.max_channels)
        self.ill_mgr     = IlluminatorManager()
        self.total_cost   = 0.0
        self.assigned_count = 0   # TEWA 배정 횟수 (부하 분산용)

    @property
    def operational(self):
        return self.status.operational

    def can_engage(self, enemy_info, dist_m):
        """이 함정이 해당 위협을 교전 가능한지 판단
        BUG-FIX v6.5.1: 센서 범위 대신 무기 사거리 기준으로 수정
        → 편대 내 Link-16 데이터 링크로 KDX-III 탐지 정보 공유
        → KDX-II/FFX는 자신의 무기 사거리 내에서 교전 가능
        """
        etype = enemy_info.get('type', '')
        # BMD 위협(탄도·HGV·QBM)은 KDX-III(SM-3 보유)만 1차 대응
        if etype in ['탄도미사일', '극초음속활공체', '저고도기동탄도']:
            if self.ship_type != 'KDX-III':
                return False
        # 무기 최대 사거리 기준으로 체크 (Link-16 데이터 링크 공유)
        # 위협이 접근하면서 무기 사거리 안에 들어오는 시점에 교전
        max_wpn_km = max(
            (FRIENDLY_DB[w].get('range_km', 0)
             for w in self.inventory if w in FRIENDLY_DB and self.inventory[w] > 0),
            default=0)
        check_dist = min(dist_m, max_wpn_km * 1000) if max_wpn_km > 0 else dist_m
        return select_weapon(enemy_info, check_dist, self.inventory, 'AUTO') is not None

    def max_weapon_range_m(self, enemy_info):
        """해당 위협에 대한 이 함정의 최대 무기 사거리 반환 (다층 방어용)"""
        max_r = 0
        for wpn_name, count in self.inventory.items():
            if count <= 0 or wpn_name not in FRIENDLY_DB:
                continue
            wpn  = FRIENDLY_DB[wpn_name]
            cats = wpn.get('category', [])
            ecat = enemy_info.get('category', '')
            # 무기 카테고리가 적 카테고리와 일치하는지 확인
            if ecat in cats or '대공' in cats and ecat == '대공'                     or '대함' in cats and ecat == '대함'                     or '대잠' in cats and ecat == '대잠':
                r = wpn.get('range_km', 0) * 1000
                if r > max_r:
                    max_r = r
        return max_r


class Fleet:
    """함정 편대 — TEWA(위협·교전·무기 배분) 관리"""
    def __init__(self, ships):
        self.ships = ships

    def operational_ships(self):
        return [s for s in self.ships if s.operational]

    def assign_threat(self, enemy_info, dist_m):
        """편대 TEWA: 위협에 가장 적합한 함정 반환
        BUG-4 수정(v6.6.1): assigned_count 기반 부하 분산 추가
        → KDX-II/FFX도 실제로 교전에 참여하도록 균등 배분
        """
        cat   = enemy_info.get('category', '')
        etype = enemy_info.get('type', '')

        candidates = [s for s in self.operational_ships()
                      if s.can_engage(enemy_info, dist_m)]
        if not candidates:
            ops = self.operational_ships()
            return ops[0] if ops else self.ships[0]

        # ── 우선순위 규칙 ──────────────────────────────────────────────
        # BMD/HGV/QBM → KDX-III 전담 (SM-3 전용)
        if etype in ['탄도미사일', '극초음속활공체', '저고도기동탄도']:
            kdx3 = [s for s in candidates if s.ship_type == 'KDX-III']
            if kdx3:
                chosen = min(kdx3, key=lambda s: s.assigned_count)
                chosen.assigned_count += 1
                return chosen

        # 대잠 위협 → FFX 우선
        if cat == '대잠' or etype == '잠수함':
            ffx = [s for s in candidates if s.ship_type == 'FFX']
            if ffx:
                chosen = min(ffx, key=lambda s: s.assigned_count)
                chosen.assigned_count += 1
                return chosen

        # 대공/대함: assigned_count 기준 균등 분산 (부하율 = 배정수/최대채널)
        chosen = min(candidates,
                     key=lambda s: s.assigned_count / s.max_channels)
        chosen.assigned_count += 1
        return chosen

    @property
    def total_cost(self):
        return sum(s.total_cost for s in self.ships)

    @property
    def survival_count(self):
        return sum(1 for s in self.ships if s.operational)

    @property
    def survival_rate(self):
        return self.survival_count / len(self.ships) if self.ships else 0.0

    def global_inventory_summary(self):
        """전 함정 잔여 재고 합산 (REQ 판정·출력용)"""
        result = {}
        for ship in self.ships:
            for k, v in ship.inventory.items():
                result[k] = result.get(k, 0) + v
        return result


class FleetChannelManager:
    """여러 함정의 채널 정보를 합산해 Gantt·그래프에 표시"""
    def __init__(self, ships):
        self.max_ch    = sum(s.ch_mgr.max_ch for s in ships)
        self._peak     = max((s.ch_mgr._peak for s in ships), default=0)
        self.history   = [h for s in ships for h in s.ch_mgr.history]
        self.schedules = [sc for s in ships for sc in s.ch_mgr.schedules]


class FleetStatus:
    """편대 전체 상태 — ShipStatus와 인터페이스 호환 (Dashboard·plot_all 무수정 연동)"""
    def __init__(self, fleet):
        self.fleet     = fleet
        self.is_fleet  = True
        # ── ShipStatus 호환 필드 (합산) ───────────────────────────────
        self.operational     = fleet.survival_count > 0
        self.hit_count       = sum(s.status.hit_count for s in fleet.ships)
        self.hit_time        = min(
            (s.status.hit_time for s in fleet.ships if s.status.hit_time),
            default=None)
        self.hit_by          = [h for s in fleet.ships for h in s.status.hit_by]
        self.decoy_stock     = sum(s.status.decoy_stock for s in fleet.ships)
        self.decoys_fired    = sum(s.status.decoys_fired for s in fleet.ships)
        self.decoy_success_count = sum(s.status.decoy_success_count for s in fleet.ships)
        self.enemy_ciws_intercept = sum(s.status.enemy_ciws_intercept for s in fleet.ships)
        self.helo_sorties    = sum(s.status.helo_sorties for s in fleet.ships)
        self.helo_intercepts = sum(s.status.helo_intercepts for s in fleet.ships)
        # ── 편대 전용 필드 ────────────────────────────────────────────
        self.ship_count      = len(fleet.ships)
        self.survival_count  = fleet.survival_count
        self.survival_rate   = fleet.survival_rate
        self.ship_results    = [
            {'name': s.name, 'type': s.ship_type,
             'operational': s.operational,
             'hit_count': s.status.hit_count,
             'cost': s.total_cost}
            for s in fleet.ships
        ]


# ════════════════════════════════════════════════════════════════════════════
#  물리 · 수학 모듈
# ════════════════════════════════════════════════════════════════════════════
def calculate_radar_horizon(target_alt_m, radar_alt_m=35.0):
    return 4.12*(np.sqrt(radar_alt_m)+np.sqrt(target_alt_m))

def calculate_detect_range_by_rcs(enemy_info):
    cat=enemy_info['category']; alt=enemy_info.get('altitude_m',10)
    rcs=enemy_info.get('rcs_m2'); etype=enemy_info.get('type')
    if cat=='대잠':          return 30.0
    if etype=='탄도미사일':  return 1200.0
    if rcs is None:          return 100.0
    return min(500.0*((rcs/3.0)**0.25), calculate_radar_horizon(alt))

def dynamic_kinematic_pk(base_pk, target_speed_ms, weapon_speed_ms,
                          target_alt_m=0, is_ballistic=False, is_sm3=False,
                          is_hgv=False, is_qbm=False,
                          terminal_evasion_factor=1.0, remaining_m=None,
                          ecm_power=0.0, ecm_susceptibility='radar'):
    if weapon_speed_ms <= 0: return 0.0

    # NEW-G: ECM 재밍 (거리 반비례, 50km 기준)
    # v6.8: seeker 유형별 ECM 효과 차등 적용
    if ecm_power > 0 and remaining_m is not None:
        ECM_SUSC_MULT = {'radar':1.0,'combined':0.5,'ir':0.15,'none':0.0}
        susc_mult = ECM_SUSC_MULT.get(ecm_susceptibility, 1.0)
        eff_ecm = ecm_power * susc_mult
        if eff_ecm > 0:
            ecm_f = 1.0 - eff_ecm*(ECM_REF_RANGE_M/max(remaining_m,5000))
            base_pk *= max(0.50, min(1.0, ecm_f))

    # NEW-D: 미사일 종말 회피 기동
    if (terminal_evasion_factor < 1.0 and
            remaining_m is not None and remaining_m < 20000):
        base_pk = base_pk * terminal_evasion_factor

    if is_hgv:
        return min(0.45, base_pk*(0.25 if is_sm3 else 0.10))
    if is_qbm:
        return min(0.99, base_pk*(0.15 if is_sm3 else 0.70))
    if is_sm3 and is_ballistic:
        return min(0.99, base_pk*max(0.2,1.0-(target_speed_ms/weapon_speed_ms)*0.3))
    sp=max(0.1,1.0-(target_speed_ms/weapon_speed_ms)*0.5)
    ap=(0.85 if (is_ballistic and target_alt_m>50000) else 0.90 if target_alt_m<=20 else 1.0)
    return min(0.99, base_pk*sp*ap)

def sample_pk(pk_dist_cfg, weather_delta=0.0):
    a,b=pk_dist_cfg['alpha'],pk_dist_cfg['beta']
    return float(np.clip(beta_dist.rvs(a,b)+weather_delta,0.05,0.99))

def pk_stats(pk_dist_cfg, weather_delta=0.0):
    a,b=pk_dist_cfg['alpha'],pk_dist_cfg['beta']
    return (float(np.clip(a/(a+b)+weather_delta,0.05,0.99)),
            float(np.sqrt((a*b)/((a+b)**2*(a+b+1)))))

def apply_weather(cfg, weather):
    w=WEATHER_DB[weather]
    return (cfg['detect_km']*1000*w['detect_range_factor'],
            w['intercept_prob_delta'],
            cfg['cd_time_s']*w['cd_time_factor'])

def enemy_pos(t, detect_m, speed_ms):
    return max(0.0, detect_m-t*speed_ms)

def max_allowed_cd(detect_m, enemy_speed_ms, weapon_speed_ms, weapon_range_m=None):
    """최대 허용 C&D 시간 계산
    BUG-5 수정(v6.6.1): 수상함/잠수함처럼 느린 위협이 이미 무기 사거리 내에 있을 때
    d_last = detect_m → max_cd = 0 이 되는 버그 수정
    → 이 경우 CIWS 최소 교전 거리(2km)까지 도달하는 시간으로 대체
    """
    esp = max(enemy_speed_ms, 0.01)
    t_arrive = detect_m / esp
    if weapon_range_m and weapon_speed_ms > 0:
        d_last = weapon_range_m * (weapon_speed_ms + esp) / weapon_speed_ms
        if d_last >= detect_m:
            # 위협이 이미 무기 사거리 내 — CIWS 최소 교전 거리(2km)로 계산
            MIN_M = max(2000.0, detect_m * 0.05)
            t_cd  = max(0.0, (detect_m - MIN_M) / esp)
            t_fly = MIN_M / weapon_speed_ms
            return t_cd, t_arrive, t_fly
        return (detect_m - d_last) / esp, t_arrive, d_last / (weapon_speed_ms + esp)
    t_fly = detect_m / (weapon_speed_ms + esp)
    return max(0.0, t_arrive - t_fly), t_arrive, t_fly

def min_detect_distance(cd_s, enemy_speed_ms, weapon_speed_ms, weapon_range_m=None):
    if weapon_range_m and weapon_speed_ms>0:
        d_last=weapon_range_m*(weapon_speed_ms+enemy_speed_ms)/weapon_speed_ms
        return d_last+cd_s*enemy_speed_ms
    return cd_s*enemy_speed_ms*(weapon_speed_ms+enemy_speed_ms)/weapon_speed_ms

def intercept_time(t_fire, detect_m, enemy_speed_ms, weapon_speed_ms):
    remaining=enemy_pos(t_fire,detect_m,enemy_speed_ms)
    if remaining<=0: return None,None
    t_fly=remaining/(weapon_speed_ms+enemy_speed_ms)
    return t_fire+t_fly, max(0.0,remaining-t_fly*enemy_speed_ms)

def bezier_q(p0,cp,p1,n=120):
    t=np.linspace(0,1,n)
    return ((1-t)**2*p0[0]+2*(1-t)*t*cp[0]+t**2*p1[0],
            (1-t)**2*p0[1]+2*(1-t)*t*cp[1]+t**2*p1[1])


# ════════════════════════════════════════════════════════════════════════════
#  TEWA
# ════════════════════════════════════════════════════════════════════════════
def select_weapon(threat_info, dist_m, global_inv, mode, manual_wpn=None):
    cat=threat_info['category']; etype=threat_info.get('type','')
    alt=threat_info.get('altitude_m',0)  # v6.8: SM-3 미드코스 조건용
    if cat=='어뢰': return None
    if mode=='MANUAL':
        if manual_wpn and global_inv.get(manual_wpn,0)>0:
            if cat not in FRIENDLY_DB[manual_wpn]['category']: return None
            if manual_wpn in ['SM-6','SM-2 Block IIIB','SM-3 Block IIA'] and dist_m<=3000: return None
            return manual_wpn
        return None
    if cat=='대잠':
        if dist_m>10000 and global_inv.get('홍상어 (대잠)',0)>0: return '홍상어 (대잠)'
        if global_inv.get('청상어 (경어뢰)',0)>0: return '청상어 (경어뢰)'
        return None
    if dist_m<=2000 and global_inv.get('CIWS-II (Phalanx)',0)>0: return 'CIWS-II (Phalanx)'
    if dist_m<=9000:
        if global_inv.get('RIM-116 RAM',0)>0: return 'RIM-116 RAM'
        if dist_m>3000 and global_inv.get('SM-2 Block IIIB',0)>0: return 'SM-2 Block IIIB'
        return None
    if etype=='극초음속활공체':
        # v6.8: SM-3는 고고도(50km↑) 미드코스 단계에서만 교전
        alt_ok = (alt >= 50000)
        if alt_ok and global_inv.get('SM-3 Block IIA',0)>0: return 'SM-3 Block IIA'
        if dist_m<=370000 and global_inv.get('SM-6',0)>0: return 'SM-6'
        return None
    if etype=='저고도기동탄도':
        if dist_m<=370000 and global_inv.get('SM-6',0)>0: return 'SM-6'
        if dist_m<=170000 and global_inv.get('SM-2 Block IIIB',0)>0: return 'SM-2 Block IIIB'
        return None
    if etype=='탄도미사일':
        # v6.8: SM-3는 미드코스(dist>200km + alt>40km) 조건 추가
        midcourse = (dist_m > 200000 and alt >= 40000)
        if midcourse and global_inv.get('SM-3 Block IIA',0)>0: return 'SM-3 Block IIA'
        if dist_m<=370000 and global_inv.get('SM-6',0)>0: return 'SM-6'
        if dist_m<=170000 and global_inv.get('SM-2 Block IIIB',0)>0: return 'SM-2 Block IIIB'
        return None
    if dist_m<=170000 and global_inv.get('SM-2 Block IIIB',0)>0: return 'SM-2 Block IIIB'
    if dist_m<=370000 and global_inv.get('SM-6',0)>0: return 'SM-6'
    return None


class IlluminatorManager:
    def __init__(self,max_channels=4,ill_time=10.0):
        self.max_ch,self.ill_time,self.schedules=max_channels,ill_time,[]
    def try_allocate(self,t_intercept):
        s,e=t_intercept-self.ill_time,t_intercept
        if sum(1 for a,b in self.schedules if max(s,a)<min(e,b))<self.max_ch:
            self.schedules.append((s,e)); return True
        return False

class ChannelManager:
    def __init__(self,max_ch=MAX_ENGAGEMENT_CHANNELS):
        self.max_ch,self.schedules,self._peak,self.history=max_ch,[],0,[]
    def try_assign(self,t_start,t_end,tid=None):
        ov=sum(1 for s,e in self.schedules if max(t_start,s)<min(t_end,e))
        if ov<self.max_ch:
            sc=[t_start,t_end]; self.schedules.append(sc)
            self._peak=max(self._peak,ov+1)
            hr={'t_start':t_start,'t_end':t_end,'threat_id':tid}
            self.history.append(hr); return True,sc,hr
        return False,None,None



# ════════════════════════════════════════════════════════════════════════════
#  NEW-H: HeloEvent — 함재 헬기 대잠 교전
# ════════════════════════════════════════════════════════════════════════════
class HeloEvent:
    _id_counter = 0
    def __init__(self,helo_name,spawn_t,target_event,cfg,
                 global_inv,ship_status,weather_delta,silent=False):
        self.helo_name=helo_name; self.spawn_t=spawn_t
        self.target=target_event; self.cfg=cfg
        self.global_inv=global_inv; self.ship_status=ship_status
        self.weather_delta=weather_delta; self.silent=silent
        self.log=[]; self.intercepted=False; self.total_cost=0
        self.is_active=True; self.gantt_bars=[]; self.used_weapons=[]
        self.evasion_count=0; self.enemy_ciws_blocks=0
        HeloEvent._id_counter+=1
        self.uid=f"H{HeloEvent._id_counter:03d}"; self.label=f"{helo_name}(항공)"
        h=FRIENDLY_AIRCRAFT_DB[helo_name]
        self.t_arrive=spawn_t+h['sortie_time_s']+target_event.detect_m/h['speed_ms']
        self.t_impact=target_event.t_impact
        self.detect_m=target_event.detect_m
        self.intercept_km=None; self.intercept_weapon=None
        self.enemy_info=target_event.enemy_info

    def _log(self,t,icon,msg):
        if not self.silent:
            self.log.append({'t':t,'icon':icon,'msg':msg,'uid':self.uid,'label':self.label})

    def run(self):
        h=FRIENDLY_AIRCRAFT_DB[self.helo_name]
        h_wx_map = FRIENDLY_AIRCRAFT_DB[self.helo_name].get('weather_limits', _HELO_WX)
        if not h_wx_map.get(self.cfg.get('weather','맑음 (주간)'),True):
            self._log(self.spawn_t,'🌪️','날씨 불량 → 출격 불가')
            self.is_active=False; return False
        if self.ship_status and not self.ship_status.operational:
            self._log(self.spawn_t,'🚫','함정 전투불능 → 귀환'); self.is_active=False; return False
        if self.target.intercepted:
            self._log(self.spawn_t,'✅','목표 기요격 → 귀환'); self.is_active=False; return False
        fly_s=self.t_arrive-self.spawn_t-h['sortie_time_s']
        craft_icon = '✈️' if h.get('base_type')=='land' else '🚁'
        base_info  = f"({h.get('base_name','기지')} 출격)" if h.get('base_type')=='land' else ''
        self._log(self.spawn_t,craft_icon,
                  f'{self.helo_name} 출격 {base_info}| 준비{h["sortie_time_s"]}s + 비행{fly_s:.0f}s')
        if self.ship_status: self.ship_status.helo_sorties+=1
        if self.t_arrive>=self.t_impact:
            self._log(self.t_impact,'⏰','도착 전 목표 도달 → 공격 불가')
            self.gantt_bars.append((self.label,self.spawn_t,self.t_impact,'#95a5a6'))
            return False
        wpn=h['payload_wpn']
        if self.global_inv.get(wpn,0)<=0:
            self._log(self.t_arrive,'❌',f'{wpn} 재고 없음'); return False
        self.global_inv[wpn]-=1
        self.total_cost+=h['cost_usd']+FRIENDLY_DB[wpn]['cost_usd']
        base_pk=sample_pk(FRIENDLY_DB[wpn]['pk_dist'],self.weather_delta)
        eff_pk=min(0.99,base_pk+h['pk_bonus'])
        self.used_weapons.append(wpn)
        if random.random()<eff_pk:
            self.intercepted=True
            self.target.intercepted=True
            self.target.intercept_weapon=f'{wpn}({self.helo_name}투하)'
            self.target.intercept_km=max(0.1,self.detect_m/1000*0.25)
            self.intercept_km=self.target.intercept_km
            self.intercept_weapon=self.target.intercept_weapon
            if self.ship_status: self.ship_status.helo_intercepts+=1
            self._log(self.t_arrive,'🎯',f'어뢰 투하 성공({wpn} Pk={eff_pk:.2f})')
            self.gantt_bars.append((self.label,self.spawn_t,self.t_arrive,'#2ecc71'))
            return True
        else:
            self._log(self.t_arrive,'💧',f'어뢰 투하 실패({wpn} Pk={eff_pk:.2f})')
            self.gantt_bars.append((self.label,self.spawn_t,self.t_arrive,'#e74c3c'))
            return False

# ════════════════════════════════════════════════════════════════════════════
#  위협 이벤트 클래스 — v6.8.1: NEW-F 적 자체 방어 추가
# ════════════════════════════════════════════════════════════════════════════
class ThreatEvent:
    _id_counter=0
    def __init__(self,label,spawn_t,detect_m,enemy_info,cfg,
                 weather_delta,cd_eff,global_inv,ch_mgr,ill_mgr,
                 ship_status=None,parent_event=None,is_missile=False,
                 silent=False,assigned_ship=None):
        ThreatEvent._id_counter+=1
        self.uid=f"T{ThreatEvent._id_counter:03d}"
        self.label,self.spawn_t,self.detect_m=label,spawn_t,detect_m
        self.enemy_info,self.speed_ms=enemy_info,enemy_info['speed_ms']
        self.cfg,self.weather_delta,self.cd_eff=cfg,weather_delta,cd_eff
        self.confirm_t=cfg['confirm_time_s']; self.cd_jitter=cfg.get('cd_jitter_s',0)
        self.global_inv,self.ch_mgr,self.ill_mgr=global_inv,ch_mgr,ill_mgr
        self.ship_status=ship_status
        self.parent_event,self.is_missile,self.silent=parent_event,is_missile,silent
        self.assigned_ship=assigned_ship  # NEW-K: 편대 모드에서 담당 함정명
        self.is_active=True
        self.threat_score=self.speed_ms/(self.detect_m+1.0)*(2.0 if is_missile else 1.0)
        self.log,self.intercepted,self.t_intercepted=[],False,None
        self.t_impact=spawn_t+detect_m/self.speed_ms
        self.total_cost,self.gantt_bars,self.used_weapons,self.weapon_attempts=0,[],[],{}
        self.channel_record,self.hist_record=None,None
        self.intercept_km,self.intercept_weapon=None,None
        self.evasion_count=0
        # NEW-F 통계
        self.enemy_ciws_blocks   = 0   # 적 CIWS에 격추된 아군 미사일 수
        self.enemy_self_def_apps = 0   # self_defense_pk 적용 횟수

    def _log(self,t,icon,msg):
        if not self.silent: self.log.append({'t':t,'icon':icon,'msg':msg,'uid':self.uid,'label':self.label})
    def _add_gantt(self,label,start,end,color):
        if not self.silent: self.gantt_bars.append((label,start,end,color))

    def run(self):
        """
        교전 루프
        NEW-A: 개별 미사일 Pk 판정
        NEW-B: 어뢰 → 기만기·회피 2단계
        NEW-E: 요격 실패 시 적 회피 기동
        NEW-F: 아군 미사일 발사 시 적 자체 방어 (CIWS + self_defense_pk)
        """
        if self.is_missile and self.parent_event and self.parent_event.t_intercepted is not None:
            if self.parent_event.t_intercepted<=self.spawn_t:
                self._log(self.spawn_t,'🚫',"모함 조기 파괴 → 미사일 발사 무효화")
                self.is_active=False; return False

        # ── NEW-B: 어뢰 2단계 방어 ──────────────────────────────────────────
        if self.enemy_info.get('category')=='어뢰':
            decoyed=False; decoy_used=False
            if (self.ship_status and self.ship_status.decoy_stock>0 and
                    self.cfg.get('enable_acoustic_decoy',True)):
                ok,msg=self.ship_status.try_decoy()
                decoy_used=True
                self._log(self.spawn_t,'🎭',f"음향 기만기 전개 — {msg}")
                if ok: decoyed=True
            if not decoyed and self.cfg.get('enable_ship_torpedo_evasion',True):
                if random.random()<SHIP_EVASION_PK:
                    decoyed=True
                    self._log(self.spawn_t,'🔄',"함정 회피 기동 성공 — 어뢰 회피")
                else:
                    self._log(self.spawn_t,'⚠️',"함정 회피 기동 실패")
            if decoyed:
                self.intercepted=True
                self.t_intercepted=self.spawn_t+5.0
                self.intercept_km=self.detect_m/1000*0.7
                self.intercept_weapon='음향 기만기 (AN/SLQ-25)' if decoy_used else '함정 회피 기동'
                self._add_gantt(self.label,self.spawn_t,self.t_intercepted,'#16A085')
                return True
            else:
                self._log(self.t_impact,'💥',"어뢰 명중!")
                self._add_gantt(self.label,self.spawn_t,self.t_impact,'#8B0000')
                if self.ship_status: self.ship_status.register_hit(self.label,self.t_impact)
                return False

        # ── 일반 교전 루프 ────────────────────────────────────────────────────
        es=self.speed_ms; dm=self.detect_m; t_elapsed=0.0
        detect_start=self.spawn_t
        self._log(self.spawn_t,'🔴',f"탐지 | 거리 {dm/1000:.1f}km | 속도 {es:.0f}m/s")
        first_attempt=True

        # NEW-F: 적 자체방어 파라미터
        enable_self_def = self.cfg.get('enable_enemy_self_defense', True)
        enemy_sdpk      = self.enemy_info.get('self_defense_pk', 0.0) if enable_self_def else 0.0
        enemy_ciws_pk_v = self.enemy_info.get('enemy_ciws_pk', 0.0)   if enable_self_def else 0.0

        while True:
            if self.ship_status and not self.ship_status.operational:
                t_chk=self.spawn_t+t_elapsed
                self._log(t_chk,'🚫',"함정 전투 불능 — 교전 강제 중단")
                self._add_gantt(self.label,detect_start,t_chk,'#808080')
                return False

            jitter=random.uniform(-self.cd_jitter,self.cd_jitter)
            if first_attempt: t_elapsed+=max(5.0,self.cd_eff+jitter)

            t_abs     = self.spawn_t+t_elapsed
            remaining = enemy_pos(t_elapsed,dm,es)

            if remaining<=0 or t_abs>=self.t_impact:
                self._log(self.t_impact,'💥',"피격")
                self._add_gantt(self.label,detect_start,self.t_impact,'#e74c3c')
                if self.channel_record is not None:
                    self.channel_record[1]=self.t_impact; self.hist_record['t_end']=self.t_impact
                if self.ship_status: self.ship_status.register_hit(self.label,self.t_impact)
                return False

            if first_attempt:
                ok,self.channel_record,self.hist_record=self.ch_mgr.try_assign(t_abs,self.t_impact,self.uid)
                if not ok:
                    self._log(t_abs,'⚠️',"교전 채널 포화")
                    self._add_gantt(self.label,detect_start,t_abs,'#95a5a6'); return False
                first_attempt=False

            wpn_name=select_weapon(self.enemy_info,remaining,self.global_inv,
                                    self.cfg['combat_mode'],self.cfg['friendly_preset'])
            if not wpn_name:
                has_any=(sum(v for k,v in self.global_inv.items() if k!='CIWS-II (Phalanx)')>0
                         or self.global_inv.get('CIWS-II (Phalanx)',0)>0)
                if has_any: t_elapsed+=2.0; continue
                self._log(t_abs,'❌',"모든 무기 재고 고갈")
                self._add_gantt(self.label,detect_start,t_abs,'#f39c12')
                if self.channel_record is not None:
                    self.channel_record[1]=t_abs; self.hist_record['t_end']=t_abs
                return False

            w_info=FRIENDLY_DB[wpn_name]; ws=w_info['speed_ms']
            t_int,_=intercept_time(t_elapsed,dm,es,ws)
            if t_int is None: t_elapsed+=2.0; continue
            t_int_abs=self.spawn_t+t_int
            if w_info['requires_illuminator'] and not self.ill_mgr.try_allocate(t_int_abs):
                self._log(t_abs,'⏳',"조사기 채널 포화 (5초 대기)"); t_elapsed+=5.0; continue

            self.weapon_attempts[wpn_name]=self.weapon_attempts.get(wpn_name,0)+1
            base_pk=sample_pk(w_info['pk_dist'],self.weather_delta)
            etype=self.enemy_info.get('type','')
            is_bal=(etype in['탄도미사일','극초음속활공체','저고도기동탄도'])
            tef=(self.enemy_info.get('terminal_evasion_factor',1.0)
                 if self.cfg.get('enable_missile_evasion',True) else 1.0)
            ecm=(self.enemy_info.get('ecm_power',0.0)
                 if self.cfg.get('enable_ecm',True) else 0.0)
            ecm_susc=self.enemy_info.get('ecm_susceptibility','radar')
            pk_s=dynamic_kinematic_pk(
                base_pk,es,ws,self.enemy_info.get('altitude_m',0),
                is_bal,wpn_name=='SM-3 Block IIA',
                self.enemy_info.get('is_hgv',False),
                self.enemy_info.get('is_qbm',False),
                terminal_evasion_factor=tef,
                remaining_m=remaining,ecm_power=ecm,
                ecm_susceptibility=ecm_susc)

            # ── NEW-F: 적 자체 방어 처리 ─────────────────────────────────────
            # [중간] 적 CIWS 요격 판정 (수상함만, 발사 전 선행 판정)
            # [간단] self_defense_pk로 effective_pk 감소
            # CIWS와 self_defense_pk는 독립 이벤트 (CIWS 성공 시 self_def 무의미)
            if enable_self_def and (enemy_sdpk > 0 or enemy_ciws_pk_v > 0):
                self._log(t_abs,'🛡️',
                          f"[NEW-F] 적 자체방어 발동 | CIWS확률={enemy_ciws_pk_v:.0%} "
                          f"| 채프·플레어={enemy_sdpk:.0%}")

            # ── NEW-A + NEW-F 통합: 발수별 판정 ──────────────────────────────
            if wpn_name=='CIWS-II (Phalanx)':
                self.total_cost+=CIWS_BURST_COST_USD
                salvo_str="기관포 점사"
                # CIWS 점사: 자체방어 Pk 감소만 적용 (CIWS 대상은 수상함 아님이 대부분)
                eff_pk=pk_s*(1-enemy_sdpk) if enable_self_def else pk_s
                success=random.random()<eff_pk

            elif wpn_name in['홍상어 (대잠)','청상어 (경어뢰)']:
                salvo=min(1,self.global_inv[wpn_name])
                salvo_str=f"{salvo}발"
                if salvo>0:
                    self.global_inv[wpn_name]-=salvo
                    self.total_cost+=w_info['cost_usd']*salvo
                eff_pk=pk_s*(1-enemy_sdpk) if enable_self_def else pk_s
                shot_hit=random.random()<eff_pk if salvo>0 else False
                success=shot_hit
                if enable_self_def and enemy_sdpk>0:
                    self.enemy_self_def_apps+=1
                self._log(t_abs,' ',
                          f"  └ 어뢰 1발: {'명중' if shot_hit else '빗나감'} "
                          f"(Pk={eff_pk:.2f} ← 기본{pk_s:.2f} × 자체방어{1-enemy_sdpk:.2f})")

            else:
                # 대공 미사일: NEW-A(개별Pk) + NEW-F(적 자체방어) 통합
                salvo=min(2,self.global_inv[wpn_name])
                salvo_str=f"{salvo}발 (개별 판정)"
                if salvo>0:
                    self.global_inv[wpn_name]-=salvo
                    self.total_cost+=w_info['cost_usd']*salvo
                success=False

                for shot_i in range(max(salvo,1)):
                    # [중간] 적 CIWS 요격 — 1발당 독립 판정
                    if enable_self_def and enemy_ciws_pk_v>0:
                        if random.random()<enemy_ciws_pk_v:
                            self.enemy_ciws_blocks+=1
                            if self.ship_status: self.ship_status.enemy_ciws_intercept+=1
                            self._log(t_abs,'🛡️',
                                      f"  └ {shot_i+1}발: [적 CIWS 격추] 아군 미사일 요격 "
                                      f"(CIWS Pk={enemy_ciws_pk_v:.0%})")
                            continue  # 이 발은 격추됨 → 다음 발로

                    # [간단] self_defense_pk → effective_pk 계산
                    eff_pk=pk_s*(1-enemy_sdpk) if enable_self_def else pk_s
                    if enable_self_def and enemy_sdpk>0:
                        self.enemy_self_def_apps+=1

                    shot_hit=random.random()<eff_pk
                    sd_str=(f" [자체방어 Pk감소: {pk_s:.2f}→{eff_pk:.2f}]"
                            if (enable_self_def and enemy_sdpk>0) else "")
                    self._log(t_abs,' ',
                              f"  └ {shot_i+1}발: {'명중' if shot_hit else '빗나감'} "
                              f"(eff_Pk={eff_pk:.2f}){sd_str}")
                    if shot_hit:
                        success=True
                        break



            self.used_weapons.append(wpn_name)
            w_att=(f"{self.weapon_attempts[wpn_name]}차" if wpn_name!='CIWS-II (Phalanx)' else "지속")
            self._log(t_abs,'🎯',
                      f"{'OK 요격 성공' if success else 'NG 요격 실패'} "
                      f"({wpn_name} {w_att}) | {salvo_str}")

            if success:
                self.intercepted,self.t_intercepted=True,t_int_abs
                self._add_gantt(self.label,detect_start,t_int_abs,'#2ecc71')
                if self.channel_record is not None:
                    self.channel_record[1]=t_int_abs; self.hist_record['t_end']=t_int_abs
                t_since=self.t_intercepted-self.spawn_t
                self.intercept_km=max(0.0,dm-t_since*es)/1000
                self.intercept_weapon=wpn_name
                return True

            # ── NEW-E: 적 회피 기동 ──────────────────────────────────────────
            evasion=self.enemy_info.get('evasion_profile')
            if (evasion and not self.silent and
                    self.evasion_count<evasion.get('max_attempts',0) and
                    self.cfg.get('enable_enemy_evasion',True)):
                boost=random.uniform(evasion['speed_boost_min'],evasion['speed_boost_max'])
                new_speed=self.speed_ms*(1+boost)
                log_parts=[f"[회피기동 {self.evasion_count+1}차] 속도 {new_speed:.0f}m/s"]
                alt_d=evasion.get('alt_change_m',0)
                if alt_d>0:
                    direction=random.choice([-1,1])
                    new_alt=max(200,self.enemy_info.get('altitude_m',0)+direction*alt_d)
                    self.enemy_info=dict(self.enemy_info)
                    self.enemy_info['altitude_m']=new_alt
                    log_parts.append(f"고도 {new_alt:.0f}m")
                dep_d=evasion.get('depth_change_m',0)
                if dep_d<0 and self.enemy_info.get('type')=='잠수함':
                    # BUG-2 수정(v6.8.1): 수심 변화를 altitude_m 에 실제 반영
                    self.enemy_info=dict(self.enemy_info)
                    new_depth=min(-10, self.enemy_info.get('altitude_m',0)+dep_d)
                    self.enemy_info['altitude_m']=new_depth
                    self.current_depth=new_depth
                    log_parts.append(f"잠항 심화 → {new_depth:.0f}m ({dep_d:+.0f}m)")
                dm=remaining; es=new_speed; t_elapsed=0.0
                self.speed_ms=new_speed; self.spawn_t=t_abs
                self.detect_m=remaining; self.t_impact=t_abs+remaining/new_speed
                self.evasion_count+=1
                self._log(t_abs,'↗',"  ".join(log_parts))
                continue

            wait=2.0 if wpn_name=='CIWS-II (Phalanx)' else self.confirm_t
            t_elapsed+=wait+(3.0 if w_info['requires_illuminator'] else 0.0)


# ════════════════════════════════════════════════════════════════════════════
#  시뮬레이션 엔진 — v6.8.1: BUG-1 수정 (수상함·잠수함 미사일 발사 보장)
# ════════════════════════════════════════════════════════════════════════════
def run_single_sim(cfg, dm_eff, weather_delta, cd_eff, silent=False):
    global_inv={k:v for k,v in cfg['inventory'].items()}
    ch_mgr=ChannelManager(MAX_ENGAGEMENT_CHANNELS); ill_mgr=IlluminatorManager()
    ship_status=ShipStatus(decoy_stock=cfg.get('decoy_stock',4))
    queue=[]; ThreatEvent._id_counter=0; HeloEvent._id_counter=0

    enemy=ENEMY_DB[cfg['enemy_preset']].copy(); enemy['speed_ms']=cfg['enemy_speed_ms']

    # NEW-L + v6.8: 적군 편대 + 다방위 공격
    threat_list = build_enemy_threat_list(cfg)
    threat_list = assign_bearings(
        threat_list,
        enable_multibearing=cfg.get('enable_multibearing', False),
        seed=cfg.get('bearing_seed', None))
    # NEW-A: wave_offset_s per 파도, 파도 내부는 launch_interval_s로 순차 스폰
    _wave_ctrs: dict = {}
    for i,(ep,ei) in enumerate(threat_list):
        wo = ei.get('wave_offset_s', 0)
        wc = _wave_ctrs.get(wo, 0); _wave_ctrs[wo] = wc + 1
        spawn_t = wo + wc * cfg['launch_interval_s']
        t1=ThreatEvent(f"{ep} #{i+1}",spawn_t,dm_eff,ei,
                       cfg,weather_delta,cd_eff,global_inv,ch_mgr,ill_mgr,
                       ship_status=ship_status,is_missile=False,silent=silent)
        heapq.heappush(queue,(t1.spawn_t,-t1.threat_score,id(t1),t1))

        if ei['can_fire_missile'] and cfg.get('enemy_fires_missile'):
            mname=ei.get('missile_name') or ''
            fire_frac=random.uniform(0.50,0.95)

            # ── BUG-1 수정 (v6.8.1) ──────────────────────────────────────────
            # 원인: fire_m_desired > dm_eff → 탐지거리 초과로 발사 조건 불충족
            # 수정: fire_m = min(fire_m_desired, dm_eff * 0.90)
            # 효과: 수상함·잠수함이 탐지 즉시 90% 지점에서 반드시 발사
            fire_m_desired = ei['missile_range_km']*1000*fire_frac
            fire_m         = min(fire_m_desired, dm_eff * 0.90)   # BUG-1 FIX ★

            if dm_eff>fire_m and enemy.get('missile_speed_ms'):
                salvo_mode=cfg.get('missile_salvo_mode','RANDOM')
                s_min=ei.get('missile_salvo_min',1); s_max=ei.get('missile_salvo_max',2)
                if salvo_mode=='FIXED':
                    n_sal=min(max(cfg.get('missile_salvo_fixed',1),s_min),s_max)
                elif salvo_mode=='MAX':
                    n_sal=s_max
                else:
                    n_sal=random.randint(s_min,s_max)

                if '어뢰' in mname: m_cat,m_type,m_alt='어뢰','어뢰',0
                elif 'SLBM' in mname or '탄도' in mname: m_cat,m_type,m_alt='대공','탄도미사일',80000
                else: m_cat,m_type,m_alt='대공','순항미사일',15

                t_fire=spawn_t+(dm_eff-fire_m)/enemy['speed_ms']
                SALVO_INTERVAL=3.0

                for k in range(n_sal):
                    # BUG-3 수정(v6.8.1): terminal_evasion을 m_info 생성 시점에 직접 결정
                    # → ENEMY_DB 전역 변조 없이 cfg 설정이 즉시 반영됨
                    term_ev = (
                        enemy.get('missile_terminal_evasion', 1.0)
                        if cfg.get('enable_missile_evasion', True)
                        else 1.0
                    )
                    m_info={
                        'category':m_cat,'type':m_type,
                        'speed_ms':ei['missile_speed_ms'],
                        'altitude_m':m_alt,'rcs_m2':0.05,
                        'terminal_evasion_factor': term_ev,   # BUG-3 수정
                        # NEW-F: 미사일 자체는 자체방어 없음
                        'self_defense_pk':0.0,'enemy_ciws_pk':0.0,
                    }
                    sfx='ABCDEFGHIJKL'[k] if k<12 else str(k)
                    t2=ThreatEvent(
                        f"{mname} #{i+1}{sfx}",
                        t_fire+k*SALVO_INTERVAL,
                        max(500,fire_m-enemy['missile_speed_ms']*k*SALVO_INTERVAL*0.5),
                        m_info,cfg,weather_delta*1.2,cd_eff*0.6,
                        global_inv,ch_mgr,ill_mgr,ship_status=ship_status,
                        parent_event=t1,is_missile=True,silent=silent)
                    heapq.heappush(queue,(t2.spawn_t,-t2.threat_score,id(t2),t2))

    all_events=[]
    while queue:
        _,_,_,ev=heapq.heappop(queue); ev.run(); all_events.append(ev)

    # NEW-H 헬기 + NEW-I P-3C 대잠 항공기
    def _try_aircraft(preset_key, enable_key, default_name):
        hn = cfg.get(preset_key, default_name)
        hi = FRIENDLY_AIRCRAFT_DB.get(hn, {})
        if not (cfg.get(enable_key, False) and hi.get('on_deck', False)): return
        base_m = hi.get('base_dist_km', 0) * 1000 if hi.get('base_type') == 'land' else 0
        for ev in list(all_events):
            if not (ev.is_active and ev.enemy_info.get('type') == '잠수함'
                    and not ev.intercepted): continue
            fly_t = (base_m + ev.detect_m) / max(hi['speed_ms'], 1)
            if hi['sortie_time_s'] + fly_t < (ev.t_impact - ev.spawn_t):
                h_ev = HeloEvent(hn, ev.spawn_t + 5.0, ev, cfg,
                                 global_inv, ship_status, weather_delta, silent)
                h_ev.run(); all_events.append(h_ev)

    _try_aircraft('helo_preset',  'enable_helo', 'AW-159 와일드캣')
    _try_aircraft('p3c_preset',   'enable_p3c',  'P-3C 오라이온')
    _try_aircraft('p8a_preset',   'enable_p8a',  'P-8A 포세이돈')

    active=[e for e in all_events if e.is_active]
    ok=sum(1 for e in active if e.intercepted)
    sr=(ok/len(active)) if active else 1.0
    return sr,all_events,active,global_inv,ch_mgr,ship_status


# ════════════════════════════════════════════════════════════════════════════
#  NEW-K: 편대 시뮬레이션 — build_fleet / run_fleet_sim_core
# ════════════════════════════════════════════════════════════════════════════

# ════════════════════════════════════════════════════════════════════════════
#  NEW-L: 적군 편대 생성 함수
# ════════════════════════════════════════════════════════════════════════════
def generate_random_enemy_fleet(difficulty='보통', seed=None):
    """난이도 기반 랜덤 적군 편대 생성 — 시드값으로 재현 가능
    BUG-3 수정(v6.6.1): n_types 최솟값을 난이도별로 보장
    """
    rng = random.Random(seed)
    dcfg = ENEMY_FLEET_RANDOM_CFG.get(difficulty, ENEMY_FLEET_RANDOM_CFG['보통'])
    pool = dcfg['pool']
    total_min, total_max = dcfg['total_count']
    max_types = dcfg['max_types']

    total = rng.randint(total_min, total_max)
    # 난이도별 최소 종류 보장 (쉬움=1, 보통=2, 어려움=3, 극한=4)
    min_types_map = {'쉬움': 1, '보통': 2, '어려움': 3, '극한': 4}
    min_types = min(min_types_map.get(difficulty, 1), len(pool))
    n_types = min(max(rng.randint(1, max_types), min_types), len(pool))
    chosen_types = rng.sample(pool, n_types)

    # 총 수를 각 타입에 무작위 분배
    fleet = []
    remaining = total
    for idx, preset in enumerate(chosen_types):
        if idx == len(chosen_types) - 1:
            cnt = remaining
        else:
            cnt = rng.randint(1, max(1, remaining - (len(chosen_types) - idx - 1)))
        remaining -= cnt
        if cnt > 0:
            fleet.append({'preset': preset, 'count': cnt})
        if remaining <= 0:
            break

    return fleet


# ════════════════════════════════════════════════════════════════════════════
#  v6 시뮬레이션 코드 (build_enemy_threat_list, HeloEvent, ThreatEvent,
#  run_single_sim, monte_carlo, save_excel 등) 제거됨
#  engine_v7.py 가 이 파일의 DB/유틸만 import해서 사용함
# ════════════════════════════════════════════════════════════════════════════
