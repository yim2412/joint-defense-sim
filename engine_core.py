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

    # ── 연안 자폭 드론 스웜 (항만 근접 자폭 무인기) ──────────────────────────
    # 다수 소형 자폭 드론. 미사일 미발사·저속 저고도로 표적에 직접 돌진 자폭(200m 도달).
    # 소형 RCS로 원거리 탐지 어려움 → C-RAM/CIWS 근접 종말 요격 대상.
    '연안 자폭 드론':
        {'category':'대함','type':'전투기','speed_ms':28,'altitude_m':150,
         'can_fire_missile':False,'rcs_m2':0.3,
         'self_defense_pk':0.05,'enemy_ciws_pk':0.0,
         'hp':None,'high_value_target':False},

    # ── 자폭 무인수상정 (USV — 항만 근접 수상 자폭 보트) ──────────────────────
    # 소형 무인 고속보트가 수상으로 표적에 직접 돌진해 자폭(200m 도달). 미사일 미발사.
    # 공중 자폭 드론(연안 자폭 드론)의 수상 대응물 — is_suicide로 수상 자폭 처리.
    # 소형 RCS·저속, hp 1(함포 1발 격침) → Mk.45 5인치 함포 근접 격퇴 대상.
    '자폭 무인수상정(USV)':
        {'category':'대함','type':'고속정','speed_ms':14,'altitude_m':5,
         'can_fire_missile':False,'is_suicide':True,'rcs_m2':5.0,
         'self_defense_pk':0.0,'enemy_ciws_pk':0.0,
         'hp':1,'high_value_target':False},

    # ── 자폭 드론 군집 (Swarm — 원거리 일방향 공격 무인기 포화) ────────────────
    # v16.12: 저가·저RCS·저속 자폭 무인기(Shahed-136급) 수십~수백 대가 다축 분산 접근.
    # 미사일 미발사·직접 돌진 자폭(200m 도달, is_aircraft 경로). 개별 요격을 강제해
    # 함대 SAM·CIWS 교전 채널을 포화시키고 요격탄을 급소모시킨다(비대칭 소모전).
    # 연안 자폭 드론(항만 근접)의 원해 기동전단 대응물 — 더 높은 순항고도·긴 사거리.
    '자폭 드론 군집':
        {'category':'대함','type':'전투기','speed_ms':50,'altitude_m':1000,
         'can_fire_missile':False,'rcs_m2':0.15,
         'self_defense_pk':0.03,'enemy_ciws_pk':0.0,
         'hp':None,'high_value_target':False},

    # ── 연안 공격 로켓 (단거리 유도로켓 포화) ─────────────────────────────────
    # 방사포급 단거리 유도로켓. 저고도 다발 포화 → 해안 SAM·CIWS 종말 요격.
    '연안 공격 로켓':
        {'category':'대함','type':'순항미사일','speed_ms':250,'altitude_m':50,
         'missile_range_km':80,'rcs_m2':0.5,
         'self_defense_pk':0.0,'enemy_ciws_pk':0.0,
         'hp':None,'high_value_target':False},

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
         'missile_name':'YJ-18 초음속 대함미사일','missile_speed_ms':1250,'missile_range_km':540,  # PHY-2: 속도 1000→1250m/s(Mach3.5 종말), 사거리 500→540km
         'can_fire_missile':True,'rcs_m2':1500.0,
         'missile_salvo_min':4,'missile_salvo_max':8,
         'missile_terminal_evasion':0.75,
         'evasion_profile':{'speed_boost_min':0.05,'speed_boost_max':0.10,'alt_change_m':0,'max_attempts':1},
         'self_defense_pk':0.32,'enemy_ciws_pk':0.28},  # NEW-F

    '055형 대형 구축함':
        {'category':'대함','type':'구축함','speed_ms':15.4,'altitude_m':30,  # MED-18: 17→15.4 m/s (30 kts 실제 최고속)
         'missile_name':'YJ-18 초음속 대함미사일','missile_speed_ms':1250,'missile_range_km':540,  # PHY-2: 속도 1000→1250m/s(Mach3.5 종말), 사거리 500→540km
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
         'missile_name':'YJ-18 초음속 대함미사일','missile_speed_ms':1250,'missile_range_km':540,  # PHY-2: 속도 1000→1250m/s(Mach3.5 종말), 사거리 500→540km
         'can_fire_missile':True,'rcs_m2':50000.0,
         'missile_salvo_min':4,'missile_salvo_max':8,
         'missile_terminal_evasion':0.75,
         'evasion_profile':{'speed_boost_min':0.03,'speed_boost_max':0.06,'alt_change_m':0,'max_attempts':1},
         'self_defense_pk':0.45,'enemy_ciws_pk':0.40,
         'hp':5,'high_value_target':True,
         'carrier_aircraft':'J-15 (비상어)','carrier_wave_interval':90,'carrier_air_wing':24},  # Type 001 J-15 ~24기

    '산둥 (항모)':
        {'category':'대함','type':'항모','speed_ms':15.4,'altitude_m':30,
         'missile_name':'YJ-18 초음속 대함미사일','missile_speed_ms':1250,'missile_range_km':540,  # PHY-2: 속도 1000→1250m/s(Mach3.5 종말), 사거리 500→540km
         'can_fire_missile':True,'rcs_m2':55000.0,
         'missile_salvo_min':4,'missile_salvo_max':8,
         'missile_terminal_evasion':0.75,
         'evasion_profile':{'speed_boost_min':0.03,'speed_boost_max':0.06,'alt_change_m':0,'max_attempts':1},
         'self_defense_pk':0.45,'enemy_ciws_pk':0.40,  # PHY-6: 0.47/0.42→0.45/0.40 (항모 기준값 상한)
         'hp':5,'high_value_target':True,
         'carrier_aircraft':'J-15 (비상어)','carrier_wave_interval':90,'carrier_air_wing':36},  # Type 002 J-15 ×36 (스펙시트 일치)

    '푸젠 (항모)':
        {'category':'대함','type':'항모','speed_ms':15.4,'altitude_m':30,
         'missile_name':'YJ-18 초음속 대함미사일','missile_speed_ms':1250,'missile_range_km':540,  # PHY-2: 속도 1000→1250m/s(Mach3.5 종말), 사거리 500→540km
         'can_fire_missile':True,'rcs_m2':60000.0,
         'missile_salvo_min':6,'missile_salvo_max':10,
         'missile_terminal_evasion':0.75,
         'evasion_profile':{'speed_boost_min':0.03,'speed_boost_max':0.06,'alt_change_m':0,'max_attempts':1},
         'self_defense_pk':0.48,'enemy_ciws_pk':0.43,  # PHY-7: 0.50/0.45→0.48/0.43 (최신 항모 상한 유지)
         'hp':5,'high_value_target':True,
         'carrier_aircraft':'J-35 (백상어)','carrier_wave_interval':80,'carrier_air_wing':40},  # Type 003 J-35/J-15T ~40기

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
        {'category':'대공','type':'전투기','speed_ms':700,'altitude_m':9000,  # 동일 기체군 J-10A(700)와 정합 — 기존 540은 과소
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
         'self_defense_pk':0.06,'enemy_ciws_pk':0.0},

    '052C형 구축함 (HHQ-9)':
        {'category':'대함','type':'구축함','speed_ms':15.0,'altitude_m':30,
         # 052C 실제 주력 대함은 YJ-62 아음속 순항(사거리 ~400km) — 기존 YJ-12 초음속은 오편성
         'missile_name':'YJ-62 대함미사일','missile_speed_ms':250,'missile_range_km':400,
         'can_fire_missile':True,'rcs_m2':1600.0,
         'missile_salvo_min':4,'missile_salvo_max':8,
         'missile_terminal_evasion':0.88,
         'evasion_profile':{'speed_boost_min':0.04,'speed_boost_max':0.08,'alt_change_m':0,'max_attempts':1},
         'self_defense_pk':0.30,'enemy_ciws_pk':0.28},

    '071형 상륙함':
        {'category':'대함','type':'상륙함','speed_ms':12.0,'altitude_m':30,
         # Type 071 LPD는 상륙수송함 — 대함미사일 미탑재(76mm 함포 + AK-630 CIWS 자체방어만)
         'missile_name':'없음','missile_speed_ms':0,'missile_range_km':0,
         'can_fire_missile':False,'rcs_m2':3500.0,
         'missile_salvo_min':0,'missile_salvo_max':0,
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
         'self_defense_pk':0.08,'enemy_ciws_pk':0.0},

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
         'missile_name':'P-700 그라니트','missile_speed_ms':850,'missile_range_km':550,  # 종말 Mach 2.5 (~850 m/s, P-800 오닉스급) — 기존 2500은 Mach 7.3 비현실
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
        # PHY-1: range 500→650km (실효 요격거리 700~900km 하한), Pk 0.900→0.850 (실전 단발 Pk 조정)
        {'speed_ms':4500,'range_km':2500,'cost_usd':25000000,'stock':8,  # 2,500km (SM-3 Block IIA 공개 교전 사거리)
         'category':['대공','탄도미사일'],
         'pk_dist':{'alpha':17,'beta':3,'mean':0.850},'requires_illuminator':False},
    'SM-6':
        {'speed_ms':1190,'range_km':370,'cost_usd':4200000,'stock':32,  # 370km / Mach 3.5(~1190 m/s) RIM-174 ERAM
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
        {'speed_ms':25.0,'range_km':19,'cost_usd':1800000,'stock':16,  # PHY-8: $500K→$1.8M (실제 개발·단가 반영), MED-4: 28.3→25 m/s
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
        {'speed_ms':240,'range_km':140,'cost_usd':1200000,'stock':0,  # RGM-84 Block II ~140km / Mach 0.71
         'category':['대함'],
         'pk_dist':{'alpha':7,'beta':3,'mean':0.700},'requires_illuminator':False},
    # NEW-B2: 국산 단거리 함대공 해궁 (K-SAAM, KVLS 탑재 — FFX-II/III 전용)
    '해궁 (K-SAAM)':
        {'speed_ms':720,'range_km':20,'cost_usd':180000,'stock':0,
         'category':['대공','근접'],
         'pk_dist':{'alpha':10,'beta':3,'mean':0.769},'requires_illuminator':False},
    # NEW-P1: 미국 해군 무기 추가 (한미 연합 작전용)
    'ESSM Block II':
        {'speed_ms':1050,'range_km':50,'cost_usd':2200000,'stock':0,  # PHY-9: $1.5M→$2.2M (2024년 기준 단가)
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
        # 실제 VLS 88셀 = Mk.41 48(SM-2/3/6) + KVLS-I 16(해궁·홍상어·현무) + KVLS-II 24(현무 탄도/순항).
        # 장거리 SAM(SM-2/3/6)은 Mk.41 48셀에만 탑재 → 합 48 준수. 과거 112발은 셀의 2.3배 비현실
        # (어떤 포화도 압도). 대잠·순항은 KVLS 자리 → 홍상어 KVLS-I.
        'default_inventory': {
            'SM-3 Block IIA':    16,   # Mk.41 48셀: BMD 16
            'SM-6':              12,   # Mk.41: 장거리 방공·대함 12
            'SM-2 Block IIIB':   20,   # Mk.41: 중거리 방공 20 (계 48 = Mk.41 전량)
            'RIM-116 RAM':       21,   # 별도 21셀 RAM 발사대
            '홍상어 (대잠)':      8,   # KVLS-I
            '청상어 (경어뢰)':   12,   # 어뢰발사관
            'Mk.46 경어뢰':       8,   # 어뢰발사관
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
    # SPS-520K 레이더 / 함대공 VLS 미탑재 — RAM 점방어만 (실제 Batch-I은 SM-2 등 함대공 미사일 없음)
    'FFX-I': {
        'display':      '호위함 FFX Batch I (인천급)',
        'sensor_km':    {'대공': 100, '대함': 35, '대잠': 45},
        'max_channels': 8,
        'eccm_factor':  0.40,
        'role':         ['대공', '대함', '대잠'],
        'default_inventory': {
            'RIM-116 RAM':       21,   # 함대공은 RAM 점방어 전용(VLS 미탑재)
            '청상어 (경어뢰)':    8,
            'Mk.46 경어뢰':       4,
            'CIWS-II (Phalanx)': 9999,
        },
    },
    # ── 호위함 Batch II (FFX-II 대구급: 대구·경남·전남·광주·진주 등) ─────────
    # SPS-550K AESA 레이더 / KVLS-I 16셀 — 해궁 quad-pack(SM-2·ESSM 미탑재, KVLS만 보유)
    'FFX-II': {
        'display':      '호위함 FFX Batch II (대구급)',
        'sensor_km':    {'대공': 100, '대함': 38, '대잠': 48},
        'max_channels': 10,
        'eccm_factor':  0.45,  # SPS-550K AESA + EW
        'role':         ['대공', '대함', '대잠'],
        'default_inventory': {
            '해궁 (K-SAAM)':     32,   # KVLS-I quad-pack(국산 단거리 함대공) — 장거리 SAM 없음
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
            '해궁 (K-SAAM)':     48,   # 확장 KVLS quad-pack(장거리 SAM 미탑재)
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
    # ── 해안 C-RAM 근접방어 포대 (고정·불침, 연안 작전) ──────────────────────
    # 항만·해안 고정 배치. 연안 드론 스웜·로켓·박격포 종말 요격 특화 (팰렁스 + RAM).
    # 침몰 없음(육상) — HP 누적 시 무력화. 회피 기동 없음(고정).
    'CRAM': {
        'display':      '해안 C-RAM 근접방어 포대',
        'sensor_km':    {'대공': 40, '대함': 20, '대잠': 0},
        'max_channels': 4,
        'eccm_factor':  0.30,
        'role':         ['대공'],
        'default_inventory': {
            'CIWS-II (Phalanx)': 9999,
            'RIM-116 RAM':       21,
        },
    },
    # ── 해안 SAM 방공 포대 (고정·불침, 연안 작전) ─────────────────────────────
    # 항만·해안 고정 배치. 연안 접근 대함미사일·항공 중거리 요격 (ESSM·SM-2).
    'CSAM': {
        'display':      '해안 SAM 방공 포대',
        'sensor_km':    {'대공': 150, '대함': 60, '대잠': 0},
        'max_channels': 6,
        'eccm_factor':  0.35,
        'role':         ['대공', '대함'],
        'default_inventory': {
            'ESSM Block II':   32,
            'SM-2 Block IIIB': 16,
            'RIM-116 RAM':     21,
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
        # 실제 Mk.41 96셀. 장거리 SAM(SM류)은 1셀 1발, ESSM은 quad-pack(1셀 4발).
        # SM류 72(72셀)+ESSM 32(8셀)+토마호크 8(8셀)=88셀(96 내). 과거 SM류 112는 셀 초과.
        'default_inventory': {
            'SM-3 Block IIA':    24,
            'SM-6 Block IB':     16,
            'SM-2 Block IIIB':   32,   # SM류 계 72 = 96셀 중 72
            'ESSM Block II':     32,   # quad-pack 8셀
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
        # 실제 Mk.41 122셀. SM류 104(104셀)+ESSM 24(6셀)+토마호크 16(16셀)=126셀급 →
        # SM류 104로 현실화(과거 140은 셀 초과). ESSM quad-pack(1셀 4발).
        'default_inventory': {
            'SM-3 Block IIA':    32,
            'SM-6 Block IB':     24,
            'SM-2 Block IIIB':   48,   # SM류 계 104 = 122셀 중 104
            'ESSM Block II':     24,   # quad-pack 6셀
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
    # ── v16.12: 아군 무인 함정 (USV·UUV) — is_unmanned: 인명손실 0·저비용·저생존 ──
    # enable_unmanned_assets ON 시 함대에 전방 피켓으로 편성. 무인이라 손실 시 인명피해 0.
    'USV': {
        'display':      '무인 수상정 (USV 해검급)',
        'sensor_km':    {'대공': 30, '대함': 45, '대잠': 25},  # 전방 수상 피켓 — 대함 감시 특화
        'max_channels': 2,
        'eccm_factor':  0.30,
        'role':         ['대함', '정찰'],
        'is_unmanned':  True,
        'picket_surface_bonus_km': 35,  # 전방 배치 → 함대 실효 대함 탐지 확장
        'default_inventory': {
            'RIM-116 RAM':       11,    # 근접 자기방어 + 자폭정 등 소형 위협 점방어(경장 USV라 CIWS 미탑재)
        },
    },
    'UUV': {
        'display':      '무인 잠수정 (UUV 소해·정찰)',
        'sensor_km':    {'대공': 0, '대함': 10, '대잠': 40},   # 수중 정찰 — 대잠 특화
        'max_channels': 1,
        'eccm_factor':  0.20,
        'role':         ['대잠', '소해'],
        'is_unmanned':  True,
        'is_minesweeper':       True,   # 편성 시 소해 활성화(기뢰 접촉 확률 경감)
        'picket_asw_bonus_km':  30,     # 전방 수중 배치 → 함대 실효 대잠 탐지 확장
        'default_inventory': {},        # 무장 없음(소해·정찰 전용)
    },
}


# ════════════════════════════════════════════════════════════════════════════
#  함정 생존성 — 동적 침수·복원력 모델 (v12.4, enable_flooding ON 경로)
#  displacement_t : 만재 배수량(톤, 공개 제원)
#  reserve_buoyancy : 침수 허용 한계(0~1). 침수율이 이를 넘으면 침몰.
#                     대형·다격실함일수록 높음. ★설계 기밀 → 추정치(상대 서열 기준)
#  compartments   : 수밀 격실 수(배수량 파생). 단일 피격 침수량 = 위력계수/격실수
#  dc_rating      : 손상통제 효율(/초). 침수 속도를 매 틱 이만큼 차단(복구팀·펌프)
#  출처: Jane's Fighting Ships(배수량) · 해군 함정 손상통제 일반 교범(복원력은 추정)
# ════════════════════════════════════════════════════════════════════════════

SHIP_SURVIVABILITY = {
    # ── 한국 해군 ──────────────────────────────────────────────────────────
    'KDX-III-B1': {'displacement_t': 11000, 'reserve_buoyancy': 0.45, 'compartments': 14, 'dc_rating': 0.0016},
    'KDX-III-B2': {'displacement_t': 12000, 'reserve_buoyancy': 0.46, 'compartments': 15, 'dc_rating': 0.0017},
    'KDX-II':     {'displacement_t': 5500,  'reserve_buoyancy': 0.40, 'compartments': 12, 'dc_rating': 0.0014},
    'FFX-I':      {'displacement_t': 3200,  'reserve_buoyancy': 0.32, 'compartments': 9,  'dc_rating': 0.0011},
    'FFX-II':     {'displacement_t': 3600,  'reserve_buoyancy': 0.33, 'compartments': 10, 'dc_rating': 0.0012},
    'FFX-III':    {'displacement_t': 4300,  'reserve_buoyancy': 0.35, 'compartments': 10, 'dc_rating': 0.0013},
    'PKG':        {'displacement_t': 570,   'reserve_buoyancy': 0.22, 'compartments': 5,  'dc_rating': 0.0007},
    'PCC':        {'displacement_t': 1200,  'reserve_buoyancy': 0.26, 'compartments': 7,  'dc_rating': 0.0009},
    'PKX-B':      {'displacement_t': 250,   'reserve_buoyancy': 0.18, 'compartments': 4,  'dc_rating': 0.0006},
    'LPH':        {'displacement_t': 18800, 'reserve_buoyancy': 0.40, 'compartments': 16, 'dc_rating': 0.0012},
    'AOE':        {'displacement_t': 23000, 'reserve_buoyancy': 0.30, 'compartments': 12, 'dc_rating': 0.0008},
    # ── 미 해군 ────────────────────────────────────────────────────────────
    'DDG-51':     {'displacement_t': 9700,  'reserve_buoyancy': 0.46, 'compartments': 14, 'dc_rating': 0.0018},
    'CG-47':      {'displacement_t': 9800,  'reserve_buoyancy': 0.43, 'compartments': 13, 'dc_rating': 0.0016},
    'CVN':        {'displacement_t': 100000,'reserve_buoyancy': 0.55, 'compartments': 23, 'dc_rating': 0.0020},
    'LPD':        {'displacement_t': 25000, 'reserve_buoyancy': 0.38, 'compartments': 15, 'dc_rating': 0.0011},
    'LST':        {'displacement_t': 4900,  'reserve_buoyancy': 0.30, 'compartments': 9,  'dc_rating': 0.0009},
    'AO':         {'displacement_t': 9000,  'reserve_buoyancy': 0.28, 'compartments': 11, 'dc_rating': 0.0008},
    # ── 잠수함(KSS-I/II/III·SSN)은 침수=즉시 압괴 물리가 달라 침수 모델 제외 ──
    #    (enable_flooding 무관하게 기존 HP 경로 유지 — is_submarine/타입으로 분기)
}

# ════════════════════════════════════════════════════════════════════════════
#  함정 통합 전력 모델 (v17.2 지향성 에너지 무기·레이저용, enable_laser_dew ON 경로)
#  gen_kw      : 함정 총 발전량(kW, 공개 제원). SSGTG·디젤발전기 정격 합.
#  radar_kw    : 주 탐지 레이더 상시 전기 부하(kW). SPY-6/1 등.
#  prop_ref_kw : 순항 상한(_POWER_REF_SPEED_MS)에서의 추진연동 보조·냉각 증분 부하(kW).
#                고속 기동 시 speed³로 증가해 레이저 가용 전력 마진을 잠식(트레이드오프).
#  laser_kw    : 장착 레이저 정격출력(kW). 0=미장착. 실측·공개계획 기반.
#
#  ⚠ 추상화 주의: KDX-III·Burke는 기계식 추진(가스터빈 축직결)이라 실제로는 발전-추진
#     전력이 분리돼 있다. 여기선 '고속 기동 시 냉각·보조 부하 증가 → 통합 전력 마진 축소'를
#     단일 budget 잠식으로 추상화(설계 합의 2026-07-04). prop_ref_kw는 축마력(75MW급)이
#     아니라 속도 연동 전기·냉각 증분(수백~수천 kW)임에 유의.
#  출처: 발전량=Rolls-Royce/GE 제원·Jane's, 레이저=HELIOS 60kW(USS Preble 실배치)·
#        한화 천광 블록-I 20kW(실전배치)·블록-III 함정용 목표 100kW(계획).
# ════════════════════════════════════════════════════════════════════════════
_POWER_REF_SPEED_MS = 15.0   # 순항 상한 기준속도(≈29kt). 이 속도에서 prop_ref_kw 부하.

SHIP_POWER = {
    # ── 한국 해군 ──────────────────────────────────────────────────────────
    # KDX-III: 발전 3×Rolls-Royce AG9140RF(~3MW급)≈9MW / 추진 COGAG 4×LM2500(75MW 축·별계통)
    'KDX-III-B1': {'gen_kw': 9000, 'radar_kw': 1200, 'prop_ref_kw': 2500, 'laser_kw': 0},
    # B2 정조대왕급: 개량 SPY-1D(V). 국산 레이저 블록-III(함정용 목표 100kW) 탑재 계획 반영.
    'KDX-III-B2': {'gen_kw': 9000, 'radar_kw': 1300, 'prop_ref_kw': 2500, 'laser_kw': 100},
    'KDX-II':     {'gen_kw': 4500, 'radar_kw': 600,  'prop_ref_kw': 1500, 'laser_kw': 0},
    'FFX-I':      {'gen_kw': 2800, 'radar_kw': 250,  'prop_ref_kw': 900,  'laser_kw': 0},
    'FFX-II':     {'gen_kw': 3200, 'radar_kw': 400,  'prop_ref_kw': 1000, 'laser_kw': 0},
    'FFX-III':    {'gen_kw': 3600, 'radar_kw': 450,  'prop_ref_kw': 1100, 'laser_kw': 0},
    'PKG':        {'gen_kw': 800,  'radar_kw': 80,   'prop_ref_kw': 400,  'laser_kw': 0},
    'PCC':        {'gen_kw': 1000, 'radar_kw': 100,  'prop_ref_kw': 400,  'laser_kw': 0},
    'PKX-B':      {'gen_kw': 400,  'radar_kw': 40,   'prop_ref_kw': 200,  'laser_kw': 0},
    # 해안 고정 포대(prop_ref=0, 추진 없음). 천광 블록-I 20kW 대드론 레이저 실배치 반영(CRAM).
    'CRAM':       {'gen_kw': 2000, 'radar_kw': 200,  'prop_ref_kw': 0,    'laser_kw': 20},
    'CSAM':       {'gen_kw': 3000, 'radar_kw': 500,  'prop_ref_kw': 0,    'laser_kw': 0},
    'LPH':        {'gen_kw': 6000, 'radar_kw': 400,  'prop_ref_kw': 2000, 'laser_kw': 0},
    'AOE':        {'gen_kw': 5000, 'radar_kw': 200,  'prop_ref_kw': 1800, 'laser_kw': 0},
    'LST':        {'gen_kw': 2500, 'radar_kw': 150,  'prop_ref_kw': 800,  'laser_kw': 0},
    'AO':         {'gen_kw': 2000, 'radar_kw': 100,  'prop_ref_kw': 700,  'laser_kw': 0},
    'USV':        {'gen_kw': 200,  'radar_kw': 50,   'prop_ref_kw': 100,  'laser_kw': 0},
    # ── 미 해군 ────────────────────────────────────────────────────────────
    # DDG-51 Flight III: 발전 3×4MW=12MW(SPY-6 대응 증설). HELIOS 60kW(USS Preble DDG-88 실배치).
    'DDG-51':     {'gen_kw': 12000, 'radar_kw': 4000, 'prop_ref_kw': 3000, 'laser_kw': 60},
    # CG-47: 발전 3×2.5MW≈7.5MW(Allison 501-K34). 레이저 개장 상정.
    'CG-47':      {'gen_kw': 7500,  'radar_kw': 1200, 'prop_ref_kw': 2500, 'laser_kw': 60},
    'CVN':        {'gen_kw': 64000, 'radar_kw': 1500, 'prop_ref_kw': 8000, 'laser_kw': 0},
    'LPD':        {'gen_kw': 5000,  'radar_kw': 500,  'prop_ref_kw': 1500, 'laser_kw': 0},
    # ── 잠수함(KSS·SSN)·UUV = 레이저 무관(잠항·소형). SHIP_POWER 미등재 → power_avail 0 ──
}


def power_avail_kw(ship_type: str, speed_ms: float = 0.0) -> float:
    """함정 레이저 가용 전력(kW) = 발전량 − 레이더 상시부하 − 속도연동 추진·냉각 증분.
    고속(speed_ms↑)일수록 잉여 축소(트레이드오프). 미등재 함종은 0."""
    p = SHIP_POWER.get(ship_type)
    if not p:
        return 0.0
    frac = (max(0.0, speed_ms) / _POWER_REF_SPEED_MS) ** 3
    prop = p.get('prop_ref_kw', 0.0) * frac
    return max(0.0, p['gen_kw'] - p.get('radar_kw', 0.0) - prop)


# ════════════════════════════════════════════════════════════════════════════
#  함정 조달가 (USD) — 적정 편대 추천(v15.1) 비용효과 산출용
#  공개 조달가(척당 건조비) 기반. 한국함은 원화 공개값 ÷ 1,350원/달러 환산(반올림).
#  출처: 방위사업청 사업 공개자료·해군 예산서·언론 보도(한국함) / FY 예산서·CRS(미국함).
#  편대 조달비용 = Σ(함정 조달가) + Σ(탑재 무기 재고비, CIWS 무한재고 제외).
# ════════════════════════════════════════════════════════════════════════════
SHIP_PROCUREMENT_USD = {
    # ── 한국 해군 ──────────────────────────────────────────────────────────
    'KDX-III-B1': 760_000_000,    # 세종대왕급 ~1조 300억원
    'KDX-III-B2': 950_000_000,    # 정조대왕급 ~1조 2,800억원 (개량형)
    'KDX-II':     300_000_000,    # 충무공이순신급 ~4,000억원
    'FFX-I':      230_000_000,    # 인천급 ~3,000억원
    'FFX-II':     260_000_000,    # 대구급 ~3,500억원
    'FFX-III':    330_000_000,    # 충남급 ~4,500억원
    'PKG':        42_000_000,     # 윤영하급 ~570억원
    'PCC':        60_000_000,     # 포항급 (현가 근사) ~800억원
    'PKX-B':      22_000_000,     # 참수리-II ~300억원
    'CRAM':       40_000_000,     # 해안 C-RAM 근접방어 포대 (팰렁스+RAM 1포대 근사) ~550억원
    'CSAM':       180_000_000,    # 해안 SAM 방공 포대 (천궁/패트리어트급 1포대 근사) ~2,400억원
    'LPH':        300_000_000,    # 독도함급 ~4,000억원
    'AOE':        356_000_000,    # 소양함 ~4,800억원
    'LST':        111_000_000,    # 천왕봉급 ~1,500억원
    'AO':         74_000_000,     # 천지함 ~1,000억원
    'KSS-I':      148_000_000,    # 장보고급(209형) ~2,000억원
    'KSS-II':     370_000_000,    # 손원일급(214형) ~5,000억원
    'KSS-III':    740_000_000,    # 도산안창호급 ~1조원
    'USV':        15_000_000,     # v16.12 무인 수상정 (중형 USV 근사) ~200억원
    'UUV':        8_000_000,      # v16.12 무인 잠수정 (대형 UUV 근사) ~110억원
    # ── 미 해군 ────────────────────────────────────────────────────────────
    'DDG-51':     2_200_000_000,  # Arleigh Burke Flight III
    'CG-47':      1_500_000_000,  # Ticonderoga (현역 가치 근사)
    'CVN':        9_000_000_000,  # Nimitz급 (현가 근사)
    'LPD':        1_800_000_000,  # San Antonio급
    'SSN':        3_500_000_000,  # Virginia Block V
}

# 함정 항속거리·순항속도 (실측 공개 제원) — 자원 지속성(연료) 모델용.
# 값 = (range_nm 항속거리[해리], cruise_kt 순항속도[노트]). 작전가능시간 T = range/cruise.
# 원자력 추진(CVN·SSN)은 None = 사실상 무제한(연료 평가 제외).
# 절대 시간이 아니라 1800s 표준 작전을 기준으로 정규화해 쓴다(engine_combat 연료 모델 참조).
SHIP_ENDURANCE = {
    # ── 한국 해군 ──────────────────────────────────────────────────────────
    'KDX-III-B1': (5500, 18),   # 세종대왕급
    'KDX-III-B2': (5500, 18),   # 정조대왕급
    'KDX-II':     (4500, 18),   # 충무공이순신급
    'FFX-I':      (4000, 15),   # 인천급
    'FFX-II':     (4500, 15),   # 대구급
    'FFX-III':    (4500, 15),   # 충남급
    'PKG':        (2000, 15),   # 윤영하급 유도탄고속함
    'PCC':        (4000, 15),   # 포항급 초계함
    'PKX-B':      (1500, 15),   # 검독수리-B 고속정
    'LPH':        (10000, 18),  # 독도급 강습상륙함
    'AOE':        (10000, 20),  # 소양급 군수지원함
    'LST':        (5000, 15),   # 천왕봉급 상륙함
    'AO':         (7000, 18),   # 천지급 군수지원함
    'KSS-I':      (11000, 10),  # 장보고급(209형) 디젤
    'KSS-II':     (12000, 10),  # 손원일급(214형) AIP
    'KSS-III':    (10000, 10),  # 도산안창호급 AIP
    'USV':        (2000, 25),   # v16.12 무인 수상정 — 소형 고속·장기 작전
    'UUV':        (1000, 6),    # v16.12 무인 잠수정 — 저속 수중 작전
    # ── 미 해군 ────────────────────────────────────────────────────────────
    'DDG-51':     (4400, 20),   # Arleigh Burke Flight III
    'CG-47':      (6000, 20),   # Ticonderoga
    'CVN':        None,         # Nimitz급 원자력 — 무제한
    'LPD':        (8000, 18),   # San Antonio급
    'SSN':        None,         # Virginia Block V 원자력 — 무제한
}

# 적 플랫폼 조달가(USD) — 소모전(attrition) 전력가치 교환비 산정용.
# 함정·잠수함·항공기만(미사일류는 소모품이라 전력가치에서 제외). 공개 추정 단가 근사.
# 키는 ENEMY_DB 키와 동일하게 유지(이름 변경 시 동반 수정).
ENEMY_PROCUREMENT_USD = {
    # ── 항공기 ────────────────────────────────────────────────────────────────
    'J-7 (섬광)':            10_000_000,    # 구형 MiG-21 계열
    'MiG-23 (플로거)':       15_000_000,
    'MiG-29 (풀크럼)':       30_000_000,
    'JH-7A (날치)':          30_000_000,
    'J-10A (비맹)':          40_000_000,
    'J-10C (맹룡 개량)':     40_000_000,
    'J-11B (플랭커-B)':      45_000_000,
    'Su-57 (펠론)':          45_000_000,
    'Su-35 (플랭커-E)':      50_000_000,
    'J-16 (플랭커-D)':       50_000_000,
    'J-16D (전자전기)':      55_000_000,
    'J-15 (비상어)':         60_000_000,    # 함재기(항모 발진 포함)
    'J-35 (백상어)':         100_000_000,   # 5세대 스텔스 함재기
    'J-20 (위룡)':           110_000_000,   # 5세대 스텔스
    'H-6 (폭격기)':          120_000_000,
    'H-6N (폭격기 개량)':    130_000_000,
    'Tu-22M3 (백파이어)':    130_000_000,
    # ── 수상함 ────────────────────────────────────────────────────────────────
    '022형 미사일 고속정':    40_000_000,
    '056형 초계함':          160_000_000,
    '071형 상륙함':          300_000_000,
    '054A형 호위함':         350_000_000,
    '052C형 구축함 (HHQ-9)': 700_000_000,
    '우달로이급 구축함':     750_000_000,
    '슬라바급 순양함':       900_000_000,
    '052D형 구축함':         920_000_000,
    '055형 대형 구축함':     1_000_000_000,
    '랴오닝 (항모)':         3_000_000_000,
    '산둥 (항모)':           4_000_000_000,
    '푸젠 (항모)':           5_500_000_000,
    # ── 잠수함 ────────────────────────────────────────────────────────────────
    '신포급 잠수함 (SLBM)':         80_000_000,
    '신포급 잠수함 (기습)':         80_000_000,
    '039형 잠수함 (송급)':          200_000_000,
    '킬로급 잠수함 (Project 636)':  300_000_000,
    '041형 잠수함 (위안급 개량)':   350_000_000,
    '093형 잠수함 (상급)':          750_000_000,
    '오스카-II급 SSGN':             1_500_000_000,
    '094형 잠수함 (진급)':          1_800_000_000,
    '야센급 SSGN':                  2_700_000_000,
}

# 적 공격 무장 탑재량(발) — 무장 유한화(enable_munition_limit)용. 공개 제원 기반.
# 대상은 can_fire_missile=True 위협(발사형)만. CIWS 등 방어 무장·1발성 미사일 위협은 제외(무제한).
# 발사 시 살보 수만큼 차감, 소진 시 발사 중단. 여기 없는 위협은 무제한 취급.
ENEMY_MUNITION = {
    # ── 항공기(공대함 미사일 탑재발수) ──────────────────────────────────────
    'J-7 (섬광)':            2,
    'MiG-29 (풀크럼)':       4,
    'J-10A (비맹)':          4,
    'J-10C (맹룡 개량)':     4,
    'J-11B (플랭커-B)':      4,
    'J-15 (비상어)':         4,
    'J-16 (플랭커-D)':       6,
    'J-20 (위룡)':           4,
    'J-35 (백상어)':         4,
    'JH-7A (날치)':          4,
    'Su-35 (플랭커-E)':      6,
    'Su-57 (펠론)':          4,
    'H-6 (폭격기)':          6,
    'H-6N (폭격기 개량)':    2,
    'Tu-22M3 (백파이어)':    3,
    # ── 수상함(대함미사일 발사관/VLS) ───────────────────────────────────────
    '022형 미사일 고속정':   8,
    '056형 초계함':          4,
    '054A형 호위함':         8,
    '052C형 구축함 (HHQ-9)': 8,
    '052D형 구축함':         16,
    '055형 대형 구축함':     24,
    '071형 상륙함':          4,
    '랴오닝 (항모)':         16,
    '산둥 (항모)':           16,
    '푸젠 (항모)':           16,
    '우달로이급 구축함':     8,
    '슬라바급 순양함':       16,
    # ── 잠수함(어뢰+잠대함미사일) ───────────────────────────────────────────
    '039형 잠수함 (송급)':           12,
    '041형 잠수함 (위안급 개량)':    12,
    '093형 잠수함 (상급)':           16,
    '094형 잠수함 (진급)':           6,
    '킬로급 잠수함 (Project 636)':   18,
    '오스카-II급 SSGN':              24,
    '야센급 SSGN':                   32,
    '신포급 잠수함 (SLBM)':          2,
    '신포급 잠수함 (기습)':          8,
}

# 침수 모델 튜닝 상수 (전술급 빠른 침수 — 700초 시뮬 실효 반영)
#   파공 크기 breach = FLOOD_WARHEAD_FACTOR / sqrt(compartments)
#     └ sqrt로 함정 크기 스케일링: 소형함은 어뢰 1발 즉사, 항모는 1발 견딤(중상)
#   초기 침수속도 flood_rate += breach · FLOOD_INFLOW_K (/초), 매 틱 dc_rating(펌프)과 경쟁
FLOOD_WARHEAD_FACTOR = {   # 무기 종류별 침수 위력 계수
    'torpedo': 2.2,        # 어뢰 — 용골 아래 폭발, 선체 절단급(가장 치명적)
    'heavy':   1.0,        # 중대형·초음속 대함미사일(대형 탄두)
    'medium':  0.7,        # 일반 아음속 대함미사일
    'light':   0.4,        # 소형·경량 탄두
}
FLOOD_BELOW_WL_PROB = {    # 수선하(침수 유발) 명중 확률
    'torpedo':   0.80,     # 어뢰는 본질적으로 수선하
    'missile':   0.30,     # 대함미사일 대부분 sea-skimming 상부 명중
    'ballistic': 0.10,     # 탄도·극초음속은 상부 수직 강하 — 수선하 드묾
    'arm':       0.05,     # ARM은 레이더(상부) 직격
}
FLOOD_INFLOW_K = 0.004     # 파공당 초기 침수 속도 계수(/초) — breach 1당 이 비율로 유입

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
    # 연안 방어 전대 (v16.5 — 항만 방어: 함정 + 해안 고정 방어 포대)
    # 연안 작전 시 함대에 해안 C-RAM·SAM 포대가 가세하는 함대+해안 협동 다층방어.
    '연안 방어 전대': [
        {'name': '대구함',          'type': 'FFX-II'},
        {'name': '참수리-211',      'type': 'PKX-B'},
        {'name': '인천 C-RAM 포대', 'type': 'CRAM'},
        {'name': '부산 C-RAM 포대', 'type': 'CRAM'},
        {'name': '동해 SAM 포대',   'type': 'CSAM'},
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
        e.setdefault('is_suicide', False)   # v16.8: 수상 자폭정(USV) — 200m 도달 직접 자폭
        e.setdefault('terminal_evasion_factor', TYPE_TEV.get(et, 1.0))
        e.setdefault('ecm_power',               TYPE_ECM.get(et, 0.0))
        e.setdefault('self_defense_pk',      0.0)
        e.setdefault('enemy_ciws_pk',        0.0)
        e.setdefault('hp',                   None)   # None → EnemyThreatObj._HP_MAP 사용
        e.setdefault('high_value_target',    False)
        e.setdefault('carrier_aircraft',     None)
        e.setdefault('carrier_wave_interval', 0)
        e.setdefault('carrier_air_wing',     0)   # 함재 전투기 항공단 규모(0=무제한, 전장 모드서 발진 총량 상한)
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
# v10.5: CAP 전투기 날씨 제한 (태풍·황사새벽만 제한 — 계기비행 + 제트엔진 전천후)
_CAP_WX = {
    '맑음 (주간)':True,'맑음 (야간)':True,'흐림 (박무)':True,
    '황사 (봄철 황사)':True,'풍랑 (7~8등급)':True,
    '폭풍 (해상 악화)':True,'태풍 (9~12등급)':False,
    '농무 (시정 200m 이하)':True,
    '폭풍 (야간)':True,'태풍 (야간)':False,
    '농무 (야간)':True,'황사 (새벽)':False,
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
    # ── v10.5: 한국 공군 CAP 항공기 ───────────────────────────────────────────
    # aircraft_role='cap': 공대공 교전 전용 (ASW 기능 없음)
    # cap_aam_range_km: 유효 교전 사거리 / cap_aam_pk: 단발 Pk / payload_cnt: 탑재 미사일 수
    'F-35A 라이트닝 II': {
        'speed_ms':     490,          # Mach 1.6 순항 (스텔스 구성, 내부 무장창)
        'range_km':     2200,
        'sortie_time_s':1800,         # 출격 준비 30분
        'payload_wpn':  'AIM-120D',
        'payload_cnt':  4,            # 내부 무장창 AIM-120D 4발 (스텔스 구성)
        'cost_usd':     600000,       # 출격 + AIM-120D 소모 비용
        'on_deck':      True,
        'base_type':    'land',
        'base_name':    '청주기지',
        'base_dist_km': 300,
        'aircraft_role':'cap',
        'cap_aam_range_km': 160,      # AIM-120D 실효 BVR 사거리 (~160km 공개 추정)
        'cap_aam_pk':   0.65,         # AMRAAM 단발 교전 Pk (실전 추정값)
        'cap_patrol_radius_km': 600,  # 이지스 함대로부터 CAP 패트롤 반경
        'weather_limits': _CAP_WX,
    },
    'KF-21 보라매': {
        'speed_ms':     430,          # Mach 1.8 최대, ~Mach 1.4 순항
        'range_km':     1900,
        'sortie_time_s':1200,         # 출격 준비 20분
        'payload_wpn':  'IRIS-T SL',
        'payload_cnt':  6,            # IRIS-T 4발 + AIM-120C 2발
        'cost_usd':     400000,
        'on_deck':      True,
        'base_type':    'land',
        'base_name':    '대구기지',
        'base_dist_km': 250,
        'aircraft_role':'cap',
        'cap_aam_range_km': 120,      # PHY-3: AIM-120C 중심 설계 80→120km (IRIS-T 보조)
        'cap_aam_pk':   0.55,
        'cap_patrol_radius_km': 500,
        'weather_limits': _CAP_WX,
        # v10.6: 공대함 타격 모드 (해성-II 2발 탑재 가능)
        'cap_strike_wpn':       '해성-II',
        'cap_strike_payload_cnt': 2,
        'cap_strike_range_km':  200,  # 해성-II 사거리 200km
        'cap_strike_pk':        0.55, # 호위함 방어 관통 후 명중 추정
        'cap_strike_cost_usd':  2_200_000,  # PHY-10 연동: 해성-II 단가 $2.2M
    },
    'FA-50 파이팅이글': {
        'speed_ms':     340,          # Mach 1.5 경전투기
        'range_km':     1800,
        'sortie_time_s': 900,         # 출격 준비 15분 (소형 경량)
        'payload_wpn':  'AIM-9X',
        'payload_cnt':  4,
        'cost_usd':     200000,
        'on_deck':      True,
        'base_type':    'land',
        'base_name':    '원주기지',
        'base_dist_km': 350,
        'aircraft_role':'cap',
        'cap_aam_range_km': 45,       # PHY-4: AIM-9X 실효 BVR 35→45km (35~50km 중앙값)
        'cap_aam_pk':   0.45,
        'cap_patrol_radius_km': 400,  # 항속거리 제한으로 패트롤 반경 좁음
        'weather_limits': _CAP_WX,
    },
    # ── v16.12: 아군 무인 정찰 드론 (ISR 전용, 무장 없음) ──────────────────────
    # aircraft_role='recon': 수평선 너머(OTH) 표적 탐지·유도 정보를 함대 데이터링크로
    # 중계 → 함대 실효 탐지거리 확장(recon_detect_bonus_km). 무장 없음.
    # 저생존성 — 적 항공위협 존재 시 확률적 격추(survive_prob, recon_roll_s 주기).
    'RQ-101 송골매': {
        'speed_ms':     42,           # 순항 ~150 km/h 전술 UAV
        'range_km':     100,          # 전술 작전반경
        'sortie_time_s':600,          # 전개 준비 10분
        'payload_wpn':  '(무장 없음)',
        'payload_cnt':  0,
        'cost_usd':     40000,        # 출격 비용 (저가 전술 UAV)
        'on_deck':      True,
        'base_type':    'land',
        'base_name':    '전방기지',
        'base_dist_km': 150,
        'aircraft_role':'recon',
        'recon_detect_bonus_km': 40,  # 저고도 전술 UAV OTH 중계 (수평선 확장 제한적)
        'survive_prob':          0.88, # 저고도·비스텔스 → 피격 취약
        'recon_roll_s':          300,  # 격추 판정 주기(초)
        'weather_limits': _CAP_WX,
    },
    'MQ-9B 시가디언': {
        'speed_ms':     90,           # 순항 ~325 km/h MALE UAV
        'range_km':     2000,         # 장기체공 광역 작전반경
        'sortie_time_s':1200,         # 전개 준비 20분
        'payload_wpn':  '(무장 없음)',
        'payload_cnt':  0,
        'cost_usd':     250000,       # 출격 비용 (MALE급 해상초계 UAV)
        'on_deck':      True,
        'base_type':    'land',
        'base_name':    '군산기지',
        'base_dist_km': 300,
        'aircraft_role':'recon',
        'recon_detect_bonus_km': 120, # 고고도 MALE 해상 레이더 광역 OTH 중계
        'survive_prob':          0.96, # 고고도 체공 — 장거리 SAM엔 취약하나 상대적 우수
        'recon_roll_s':          300,
        'weather_limits': _P3C_WX,    # 태풍만 불가
    },
}

# ── v19.1: 공군 작전급 전력 DB (AIR_FORCE_DB) ──────────────────────────────────
# 작전급 캠페인(engine_airforce.py)용 — 일일 소티율·전투행동반경·수행 임무로 기술한다.
# 전술 교전용 FRIENDLY_AIRCRAFT_DB(소티 1회당 Pk·BVR 사거리)와 도메인이 다르다:
#   · FRIENDLY_AIRCRAFT_DB = 단발/전장 엔진의 CAP 교전 1회 해결(초~분)
#   · AIR_FORCE_DB         = 캠페인 엔진의 며칠 소티 생성·제공권 기여(1h 틱)
# 기체명은 두 DB에서 겹칠 수 있으나(KF-21·F-35A 등) 필드 규약이 다르므로 별도 유지.
# 제원은 공개값(전투행동반경·순항속도)·교리 표준(임무 유형) 기준. sortie_rate=지속 출격/일/기.
AIR_FORCE_DB = {
    # ── 한국 공군 (ROK) ──────────────────────────────────────────────────────
    'KF-21 보라매': {
        'side': 'ROK', 'role': 'multirole',
        'missions': ['CAP', 'CAS', 'SEAD', 'strike', 'recon'],
        'combat_radius_km': 1000,   # 내부연료 전투행동반경 ~1000~1100km(공개제원, 페리 ~2900km)
        'cruise_ms': 250,           # ~Mach 0.85 순항
        'sortie_rate': 2.0,         # 지속 출격/일/기
        'sortie_cost_usd': 400_000,
    },
    'F-35A 라이트닝 II': {
        'side': 'ROK', 'role': 'stealth_multirole',
        'missions': ['CAP', 'SEAD', 'strike', 'recon'],
        'combat_radius_km': 1090,   # 공식 >590 nmi(내부연료)
        'cruise_ms': 250,
        'sortie_rate': 1.5,         # 정비 소요 큼(스텔스 도장·저관측 유지)
        'sortie_cost_usd': 600_000,
    },
    'F-15K 슬램이글': {
        'side': 'ROK', 'role': 'strike',
        'missions': ['strike', 'SEAD', 'CAP'],
        'combat_radius_km': 1200,   # CFT/증조 장착 타격반경(페리 ~1800km 이상)
        'cruise_ms': 250,
        'sortie_rate': 1.5,
        'sortie_cost_usd': 500_000,
    },
    'KF-16 파이팅팰컨': {
        'side': 'ROK', 'role': 'multirole',
        'missions': ['CAP', 'CAS', 'SEAD', 'strike'],
        'combat_radius_km': 550,    # F-16C/D Block52 전투행동반경
        'cruise_ms': 240,
        'sortie_rate': 2.5,         # 정비 부담 낮아 고소티
        'sortie_cost_usd': 250_000,
    },
    'E-737 피스아이': {
        'side': 'ROK', 'role': 'aew',
        'missions': ['AEW'],        # 조기경보·통제 — CAP 효율 승수(직접 격추 아님)
        'combat_radius_km': 1800,   # 체공 반경(임무시간 ~9h)
        'cruise_ms': 230,
        'sortie_rate': 1.0,         # 장기 체공 1소티
        'sortie_cost_usd': 350_000,
    },
    'RQ-4 글로벌호크': {
        'side': 'ROK', 'role': 'isr',
        'missions': ['recon'],      # 고고도 장기체공 ISR — 전장의 안개 belief 갱신
        'combat_radius_km': 5500,   # 초장거리(체공 32h+)
        'cruise_ms': 175,           # ~630 km/h
        'sortie_rate': 0.7,
        'sortie_cost_usd': 300_000,
    },
    # ── 미국 공군 (US) ───────────────────────────────────────────────────────
    'F-16 파이팅팰컨': {
        'side': 'US', 'role': 'multirole',
        'missions': ['CAP', 'CAS', 'SEAD', 'strike'],
        'combat_radius_km': 550,
        'cruise_ms': 240,
        'sortie_rate': 2.5,
        'sortie_cost_usd': 250_000,
    },
    'B-1B 랜서': {
        'side': 'US', 'role': 'strategic_bomber',
        'missions': ['strike'],     # 전략폭격·대함(LRASM) — 적 기지 타격(v19.4)
        'combat_radius_km': 5500,   # 무급유 항속 ~9400km
        'cruise_ms': 270,           # 고아음속 순항(M~0.92)
        'sortie_rate': 0.5,         # 장거리 출격 저소티
        'sortie_cost_usd': 1_500_000,
    },
    'B-52 스트래토포트리스': {
        'side': 'US', 'role': 'strategic_bomber',
        'missions': ['strike'],
        'combat_radius_km': 7200,   # 항속 ~14000km
        'cruise_ms': 230,
        'sortie_rate': 0.5,
        'sortie_cost_usd': 1_200_000,
    },
}

# ════════════════════════════════════════════════════════════════════════════
#  NEW-L: 적군 편대 프리셋 + 랜덤 난이도 설정 (v6.4)
# ════════════════════════════════════════════════════════════════════════════
# PLA 해군·공군 교리 기반 5종 프리셋
ENEMY_FLEET_PRESETS = {
    # A2/AD 항공 포화 공격 — 전투기+폭격기 장거리 타격
    # 항공 대함 포화 — 단일 기동전단 돌파엔 25~40발 동시 포화 교리. 과거 6기(대함 8~12발)는 과소.
    'A2/AD 항공 포화': [
        {'preset': 'J-16 (플랭커-D)',  'count': 6},
        {'preset': 'H-6 (폭격기)',     'count': 4},
    ],
    # 전자전 SEAD 제압 — 대방사미사일(ARM) 포화로 함대 레이더 무력화 시도.
    # 레이더를 켜면 ESM이 ARM을 정확 유도(EMCON 딜레마), 끄면 ARM 회피하나 대공 탐지 손실.
    # ARM 24발 포화 — 실제 SEAD는 아군 레이더(SPY·SPS 등) 5~6개에 각 3~4발 할당.
    # 과거 12발은 표적당 2발 미만으로 과소(포화 불가).
    '전자전 SEAD 제압': [
        {'preset': 'Kh-31P 대방사미사일', 'count': 12},
        {'preset': 'LD-10 대방사미사일',  'count': 8},
        {'preset': 'Kh-58U 대방사미사일', 'count': 4},
        {'preset': 'J-16 (플랭커-D)',      'count': 4},
    ],
    # 항모 킬 체인 — 탄도+극초음속+스텔스 다축 포화 (실제 PLA 대항모 킬체인 교리).
    # 극초음속 8발(DF-17 4+YJ-21 4)이 SM-3 채널을 분산 → 일부 종말 강하 누출 →
    # 고고도 SM-3 → 강하 SM-6 Block IB 다층요격 발현(한미 항모전단 대상).
    # 과거 5발(DF-17 1)은 단발이라 HGV 다층요격 미발현.
    '항모 킬 체인': [
        {'preset': 'DF-21D (대함 탄도)',    'count': 4},
        {'preset': 'DF-17 (극초음속 활공)', 'count': 4},
        {'preset': 'YJ-21 (극초음속 대함)', 'count': 4},
        {'preset': 'J-20 (위룡)',           'count': 3},
    ],
    # 연안 포화 공격 (v16.5 — 항만 근접: 자폭 드론 스웜 + 단거리 로켓 + 고속정)
    # 소형 자폭 드론·저고도 로켓이 다발로 항만에 접근 → C-RAM 근접방어·해안 SAM 시험.
    '연안 포화 공격': [
        {'preset': '연안 자폭 드론',      'count': 30},
        {'preset': '연안 공격 로켓',      'count': 20},
        {'preset': '022형 미사일 고속정', 'count': 4},
    ],
    # 항만 침투 복합 (v16.8 — 거점 방어: 무인 수상정 + 침투 고속정 + 공중 자폭드론)
    # 수상 자폭 USV가 근접 돌진(함포 격퇴), 침투 고속정이 대함미사일 살보, 공중 드론 가세.
    # 기뢰(enable_mine_threat)와 조합해 항만 거점 방어 시나리오를 구성.
    '항만 침투 복합': [
        {'preset': '자폭 무인수상정(USV)', 'count': 12},
        {'preset': '022형 미사일 고속정',  'count': 4},
        {'preset': '연안 자폭 드론',       'count': 8},
    ],
    # v16.12 무인기 군집 포화 — 저가 자폭 드론 수십 대 다축 동시 접근으로 함대 방어망 포화.
    # 개별 요격 강제 → SAM·CIWS 채널·요격탄 급소모(비대칭 소모전). 소수 미사일 혼성으로
    # 요격 우선순위 교란. 다방위 공격(multibearing) 병용 시 360° 포화 효과가 극대화된다.
    '무인기 군집 포화': [
        {'preset': '자폭 드론 군집', 'count': 48},
        {'preset': 'YJ-18 (초음속 대함)', 'count': 4},
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
    # 전면전 포화 — 전 도메인(공중·탄도·극초음속·수상·수중) 플랫폼 총동원 (최고 난이도).
    # 항모 킬 체인이 '대항모 미사일 다축'이라면, 전면전 포화는 '모든 플랫폼 동시 교전'이 정체성.
    # 공중 스텔스/대함기 8기 + 탄도·극초 8발 + 수상함 2척(YJ-21 다발) + 핵잠 2척의 입체 동시 포화.
    # 과거 각 1~2발 편성은 '최고 난이도' 라벨과 달리 포화가 아니었음(다축이되 표적당 1발 미만).
    '전면전 포화': [
        {'preset': 'J-20 (위룡)',           'count': 4},
        {'preset': 'J-16 (플랭커-D)',       'count': 4},
        {'preset': 'DF-21D (대함 탄도)',    'count': 4},
        {'preset': 'DF-17 (극초음속 활공)', 'count': 4},
        {'preset': '055형 대형 구축함',     'count': 2},
        {'preset': '093형 잠수함 (상급)', 'count': 2},
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
    # 극초음속 포화 공격 — DF-17 육상 HGV + YJ-21 함발 극초음속 다발 일제 발사.
    # 고고도 활공체 다발로 SM-3 채널을 분산시켜 일부가 종말 강하까지 누출 → 활공 궤적
    # 다층 요격(고고도 SM-3 → 강하 SM-6 Block IB)을 시험한다. 한미 편대(SM-6 Block IB 보유) 대상.
    '극초음속 포화 공격': [
        {'preset': 'DF-17 (극초음속 활공)', 'count': 12},
        {'preset': 'YJ-21 (극초음속 대함)', 'count': 8},
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
#  engine_combat.py 가 이 파일의 DB/유틸만 import해서 사용함
# ════════════════════════════════════════════════════════════════════════════
