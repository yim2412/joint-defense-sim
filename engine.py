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
    '093형 잠수함 (위안급)':      -350,
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
        {'category':'대공','type':'전투기','speed_ms':450,'altitude_m':11000,
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
         'missile_name':'P-800 오닉스 (야혼트)','missile_speed_ms':2000,'missile_range_km':300,
         'can_fire_missile':True,'rcs_m2':1800.0,
         'missile_salvo_min':4,'missile_salvo_max':8,
         'missile_terminal_evasion':0.82,
         'evasion_profile':{'speed_boost_min':0.04,'speed_boost_max':0.08,'alt_change_m':0,'max_attempts':1},
         'self_defense_pk':0.28,'enemy_ciws_pk':0.25},

    '슬라바급 순양함':
        {'category':'대함','type':'구축함','speed_ms':17.0,'altitude_m':30,
         'missile_name':'P-1000 (벌칸)','missile_speed_ms':2000,'missile_range_km':700,
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
        {'speed_ms':720,'range_km':15,'cost_usd':180000,'stock':0,
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
        {'detect_range_factor':0.75,'radar_factor':0.82,'sonar_factor':0.40,
         'intercept_prob_delta':-0.08,'cd_time_factor':1.25},
    '태풍 (9~12등급)':
        {'detect_range_factor':0.55,'radar_factor':0.62,'sonar_factor':0.22,
         'intercept_prob_delta':-0.15,'cd_time_factor':1.50},
    '농무 (시정 200m 이하)':
        # LOW-12: radar_factor 0.96→0.80 (농무는 레이더 흡수·산란 심각)
        {'detect_range_factor':0.88,'radar_factor':0.80,'sonar_factor':0.94,
         'intercept_prob_delta':-0.03,'cd_time_factor':1.10},
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
        'sensor_km':    {'대공': 800, '대함': 45, '대잠': 50},
        'max_channels': 18,
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
        'sensor_km':    {'대공': 800, '대함': 45, '대잠': 50},
        'max_channels': 24,
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
        'sensor_km':    {'대공': 120, '대함': 40, '대잠': 40},
        'max_channels': 12,
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
        'sensor_km':    {'대공': 120, '대함': 38, '대잠': 48},
        'max_channels': 10,
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
        'sensor_km':    {'대공': 150, '대함': 40, '대잠': 50},
        'max_channels': 12,
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
        'sensor_km':    {'대공': 850, '대함': 50, '대잠': 50},
        'max_channels': 24,
        'role':         ['대공', '대함', '대잠', 'BMD'],
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
        'sensor_km':    {'대공': 850, '대함': 50, '대잠': 55},
        'max_channels': 32,
        'role':         ['대공', '대함', '대잠', 'BMD'],
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
        'role':         ['대공', '대잠'],
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
        e.setdefault('self_defense_pk',   0.0)
        e.setdefault('enemy_ciws_pk',     0.0)
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
}
# P-3C 날씨 제한 (태풍만 불가, 계기비행 가능)
_P3C_WX  = {
    '맑음 (주간)':True,'맑음 (야간)':True,'흐림 (박무)':True,
    '황사 (봄철 황사)':True,'풍랑 (7~8등급)':True,
    '폭풍 (해상 악화)':True,'태풍 (9~12등급)':False,
    '농무 (시정 200m 이하)':True,
}

FRIENDLY_AIRCRAFT_DB = {
    'AW-159 와일드캣': {
        'speed_ms':78,'range_km':140,'sortie_time_s':300,  # LOW-10: 100→78 m/s (Wildcat 실제 순항속도 ~150 kts)
        'payload_wpn':'청상어 (경어뢰)','payload_cnt':2,
        'cost_usd':HELO_SORTIE_COST_USD,'pk_bonus':0.05,'on_deck':True,
        'base_type':'ship','weather_limits':_HELO_WX,
    },
    'MH-60R 시호크': {
        'speed_ms':110,'range_km':200,'sortie_time_s':240,
        'payload_wpn':'청상어 (경어뢰)','payload_cnt':2,
        'cost_usd':int(HELO_SORTIE_COST_USD*1.2),'pk_bonus':0.08,'on_deck':False,
        'base_type':'ship','weather_limits':_HELO_WX,
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
        {'preset': '093형 잠수함 (위안급)', 'count': 1},
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
        {'preset': '093형 잠수함 (위안급)', 'count': 1},
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
        {'preset': '093형 잠수함 (위안급)', 'count': 1},
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
                 '093형 잠수함 (위안급)'],
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


def build_enemy_threat_list(cfg):
    """cfg에서 적군 위협 목록 생성 — [(enemy_preset, enemy_info), ...]"""
    mode = cfg.get('enemy_fleet_mode', 'single')

    if mode == 'single':
        # 기존 방식: 단일 종류 × num_threats
        ei = ENEMY_DB[cfg['enemy_preset']].copy()
        ei['speed_ms'] = cfg.get('enemy_speed_ms', ei.get('speed_ms', 300))
        return [(cfg['enemy_preset'], {**ei}) for _ in range(cfg['num_threats'])]

    elif mode == 'preset':
        preset_name = cfg.get('enemy_fleet_preset', 'A2/AD 항공 포화')
        fleet_spec   = ENEMY_FLEET_PRESETS.get(preset_name, [])

    elif mode == 'custom':
        fleet_spec = cfg.get('enemy_fleet_custom', [])

    elif mode == 'random':
        fleet_spec = generate_random_enemy_fleet(
            difficulty=cfg.get('enemy_fleet_difficulty', '보통'),
            seed=cfg.get('enemy_fleet_seed', None))

    elif mode == 'mixed':
        # NEW-A: 혼합 공격 시나리오 — 파도별 위협 + wave_offset_s 부착
        scenario_name = cfg.get('mixed_scenario', '')
        scenario = MIXED_ATTACK_SCENARIOS.get(scenario_name, {})
        threats = []
        for wave in scenario.get('waves', []):
            wave_delay = wave.get('delay_s', 0)
            for spec in wave.get('threats', []):
                p = spec['preset']
                cnt = spec.get('count', 1)
                if p not in ENEMY_DB:
                    continue
                for _ in range(cnt):
                    ei = ENEMY_DB[p].copy()
                    ei['wave_offset_s'] = wave_delay
                    threats.append((p, ei))
        return threats[:24]

    else:
        fleet_spec = []

    # fleet_spec → [(preset, enemy_info), ...] 펼치기
    threats = []
    for spec in fleet_spec:
        p = spec['preset']
        cnt = spec.get('count', 1)
        if p not in ENEMY_DB:
            continue
        ei = ENEMY_DB[p].copy()
        ei['speed_ms'] = ei['speed_ms']  # 커스텀 속도는 single 모드에서만 적용
        for _ in range(cnt):
            threats.append((p, ei.copy()))  # v6.8: 각자 독립 copy

    # 최대 24개 제한 (채널 한계)
    return threats[:24]

def assign_bearings(threat_list, enable_multibearing=False, seed=None):
    # v6.8: 전방위 공격 ON/OFF — False=기존 정면(0도) 방식
    if not enable_multibearing:
        for _, ei in threat_list:
            ei['bearing_deg'] = 0
        return threat_list
    rng = random.Random(seed)
    n = len(threat_list)
    base_angles = [i * 360 / max(n, 1) for i in range(n)]
    rng.shuffle(base_angles)
    for (_, ei), base in zip(threat_list, base_angles):
        jitter = rng.uniform(-20, 20)
        ei['bearing_deg'] = (base + jitter) % 360
    return threat_list



# ════════════════════════════════════════════════════════════════════════════
#  NEW-M: 시나리오 저장/불러오기 (v6.5)
# ════════════════════════════════════════════════════════════════════════════
# cfg에서 직렬화 불가 항목을 제거하고 JSON 저장
_CFG_SKIP_KEYS = {'inventory', 'enemy_speed_ms'}  # 저장 제외 키

def save_scenario(cfg, filepath):
    """현재 시뮬레이션 설정을 JSON 파일로 저장"""
    import json, pathlib
    save_data = {k: v for k, v in cfg.items() if k not in _CFG_SKIP_KEYS}
    pathlib.Path(filepath).parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2)
    return True


def load_scenario(filepath):
    """JSON 파일에서 시나리오 설정 불러오기
    반환값: cfg dict (inventory 등 누락 키는 기본값으로 채워야 함)
    """
    import json
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data


def list_scenarios(directory='.'):
    """지정 폴더의 .json 시나리오 파일 목록 반환"""
    import pathlib
    p = pathlib.Path(directory)
    return sorted([str(f) for f in p.glob('*.json') if f.is_file()])



# ════════════════════════════════════════════════════════════════════════════
#  NEW-N: A vs B 시나리오 비교 함수 (v6.6)
# ════════════════════════════════════════════════════════════════════════════
def run_comparison(cfg_a, cfg_b):
    """두 시나리오를 각각 실행하고 비교 결과 반환"""
    results = {}
    for label, cfg in [('A', cfg_a), ('B', cfg_b)]:
        try:
            (max_cd, t_arrive, t_fly, mc, min_d,
             all_events, active_events, verdicts, details,
             sc_results, dm_eff, weather_delta, cd_eff,
             total_cost, global_inv, ch_mgr,
             ship_status) = run_full_simulation(cfg)

            ok_cnt  = sum(1 for e in active_events if e.intercepted)
            tot_cnt = len(active_events)
            mc_full = float((mc == 1.0).mean() * 100)
            mc_avg  = float(mc.mean() * 100)

            results[label] = {
                'cfg':            cfg,
                'ok_cnt':         ok_cnt,
                'tot_cnt':        tot_cnt,
                'intercept_rate': ok_cnt / tot_cnt * 100 if tot_cnt else 0,
                'mc_full':        mc_full,
                'mc_avg':         mc_avg,
                'total_cost':     total_cost,
                'dm_eff_km':      dm_eff / 1000,
                'verdicts':       verdicts,
                'ship_status':    ship_status,
                'all_events':     all_events,
                'active_events':  active_events,
                'sc_results':     sc_results,
                'error':          None,
            }
        except Exception as e:
            results[label] = {'error': str(e)}
    return results

def build_fleet(cfg):
    """cfg에서 Fleet 객체 생성 — 매 시뮬레이션마다 호출해 독립 인스턴스 보장
    fleet_mode: 'preset' (기본) | 'custom' (직접 구성)
    """
    fleet_mode = cfg.get('fleet_mode', 'preset')

    if fleet_mode == 'custom':
        # NEW-L: 커스텀 구성 — fleet_custom_ships = [{'name':str,'type':str}, ...]
        custom_ships = cfg.get('fleet_custom_ships', [])
        if not custom_ships:
            # 커스텀 비어있으면 단독 작전으로 폴백
            custom_ships = [{'name': '정조대왕함', 'type': 'KDX-III'}]
        preset = custom_ships
    else:
        preset_name = cfg.get('fleet_preset', '기동전단 기본')
        preset      = FLEET_PRESETS.get(preset_name, FLEET_PRESETS['기동전단 기본'])

    ships = []
    for idx, spec in enumerate(preset):
        # 1번 함정(지휘함, KDX-III)은 cfg의 재고 설정 사용
        if idx == 0 and spec['type'] == 'KDX-III':
            inv = cfg.get('inventory', SHIP_DB['KDX-III']['default_inventory']).copy()
        else:
            inv = SHIP_DB[spec['type']]['default_inventory'].copy()
        ship = Ship(spec['name'], spec['type'], inv,
                    decoy_stock=cfg.get('decoy_stock', 4))
        ships.append(ship)
    return Fleet(ships)


def run_fleet_sim_core(cfg, dm_eff, weather_delta, cd_eff, fleet, silent=False):
    """편대 단위 시뮬레이션 코어 — run_single_sim의 편대 버전"""
    queue = []
    ThreatEvent._id_counter = 0
    HeloEvent._id_counter   = 0

    enemy_info_base = ENEMY_DB[cfg['enemy_preset']].copy()
    enemy_info_base['speed_ms'] = cfg['enemy_speed_ms']

    # ── 위협 생성 + 편대 TEWA 배정 (NEW-L + v6.8: 다방위 지원) ─────────
    threat_list = build_enemy_threat_list(cfg)
    threat_list = assign_bearings(
        threat_list,
        enable_multibearing=cfg.get('enable_multibearing', False),
        seed=cfg.get('bearing_seed', None))
    for i,(ep,enemy_info) in enumerate(threat_list):
        spawn_t    = i * cfg['launch_interval_s']

        # 편대 TEWA: 위협에 최적 함정 배정
        ship = fleet.assign_threat(enemy_info, dm_eff)

        t1 = ThreatEvent(
            f"{ep} #{i+1}", spawn_t, dm_eff,
            enemy_info, cfg, weather_delta, cd_eff,
            ship.inventory, ship.ch_mgr, ship.ill_mgr,
            ship_status=ship.status, is_missile=False,
            silent=silent, assigned_ship=ship.name)
        heapq.heappush(queue, (t1.spawn_t, -t1.threat_score, id(t1), t1))

        # ── 적 미사일/어뢰 발사 처리 ──────────────────────────────────
        if enemy_info.get('can_fire_missile') and cfg.get('enemy_fires_missile'):
            mname      = enemy_info.get('missile_name') or ''
            fire_frac  = random.uniform(0.50, 0.95)
            fire_m     = min(enemy_info.get('missile_range_km', 150)*1000*fire_frac,
                             dm_eff * 0.90)
            if dm_eff > fire_m and enemy_info.get('missile_speed_ms'):
                s_mode = cfg.get('missile_salvo_mode', 'RANDOM')
                s_min  = enemy_info.get('missile_salvo_min', 1)
                s_max  = enemy_info.get('missile_salvo_max', 2)
                if   s_mode == 'FIXED': n_sal = min(max(cfg.get('missile_salvo_fixed',1),s_min),s_max)
                elif s_mode == 'MAX':   n_sal = s_max
                else:                   n_sal = random.randint(s_min, s_max)

                if '어뢰' in mname: m_cat,m_type,m_alt='대잠','어뢰',0
                elif '탄도' in mname or 'SLBM' in mname: m_cat,m_type,m_alt='대공','탄도미사일',80000
                else: m_cat,m_type,m_alt='대공','순항미사일',15

                t_fire = spawn_t + (dm_eff - fire_m) / max(enemy_info['speed_ms'],1)
                for k in range(n_sal):
                    term_ev = (enemy_info.get('missile_terminal_evasion',1.0)
                               if cfg.get('enable_missile_evasion',True) else 1.0)
                    m_info  = {
                        'category': m_cat, 'type': m_type,
                        'speed_ms': enemy_info['missile_speed_ms'],
                        'altitude_m': m_alt, 'rcs_m2': 0.05,
                        'terminal_evasion_factor': term_ev,
                        'self_defense_pk': 0.0, 'enemy_ciws_pk': 0.0,
                    }
                    m_ship = fleet.assign_threat(m_info, fire_m)
                    sfx = 'ABCDEFGHIJKL'[k] if k < 12 else str(k)
                    t2 = ThreatEvent(
                        f"{mname} #{i+1}{sfx}",
                        t_fire + k * 3.0,
                        max(500, fire_m - enemy_info['missile_speed_ms']*k*3.0*0.5),
                        m_info, cfg, weather_delta*1.2, cd_eff*0.6,
                        m_ship.inventory, m_ship.ch_mgr, m_ship.ill_mgr,
                        ship_status=m_ship.status, parent_event=t1,
                        is_missile=True, silent=silent, assigned_ship=m_ship.name)
                    heapq.heappush(queue, (t2.spawn_t, -t2.threat_score, id(t2), t2))

    # ── CEC 사전 동시 배정 (v6.8) ─────────────────────────────────────────
    _cec_pairs = []
    if cfg.get('enable_cec_preassign', False) and len(fleet.ships) > 1:
        LAYER_PRE = ['KDX-III', 'KDX-II', 'FFX']
        for _, _, _, ev in list(queue):
            if getattr(ev,'is_missile',False): continue  # v6.8.4: HeloEvent 안전
            curr = next((s for s in fleet.ships
                         if s.name == getattr(ev,'assigned_ship','')), None)
            if curr is None: continue
            cidx = LAYER_PRE.index(curr.ship_type) if curr.ship_type in LAYER_PRE else -1
            backup = None
            for btype in LAYER_PRE[cidx+1:]:
                cands = [s for s in fleet.operational_ships() if s.ship_type==btype]
                if cands:
                    backup = min(cands, key=lambda s: s.assigned_count)
                    break
            if backup:
                _cec_pairs.append((ev, backup))

    # ── 교전 실행 ──────────────────────────────────────────────────────
    all_events = []
    while queue:
        _, _, _, ev = heapq.heappop(queue)
        ev.run()
        all_events.append(ev)
        # CEC 사전 배정: 1차 실패 시 즉시 2차 발사
        if cfg.get('enable_cec_preassign', False):
            for pev, backup_ship in _cec_pairs:
                if pev is ev and not ev.intercepted and ev.is_active:
                    max_r = backup_ship.max_weapon_range_m(ev.enemy_info)
                    if max_r >= 5000:
                        layer_dm = min(max_r*0.85, ev.detect_m*0.60)
                        cec_ev = ThreatEvent(
                            ev.label+' [CEC2차]', ev.spawn_t,
                            max(layer_dm, 5000),
                            ev.enemy_info, cfg, weather_delta*1.05, cd_eff*0.45,
                            backup_ship.inventory, backup_ship.ch_mgr,
                            backup_ship.ill_mgr,
                            ship_status=backup_ship.status,
                            is_missile=False, silent=silent,
                            assigned_ship=backup_ship.name)
                        cec_ev._layered = True
                        cec_ev.run()
                        all_events.append(cec_ev)
                        if cec_ev.intercepted:
                            ev.is_active = False
                            backup_ship.total_cost += cec_ev.total_cost

    # ── 항공기 운용 (편대 내 대잠 전담 함정 우선) ─────────────────────
    def _try_aircraft_fleet(preset_key, enable_key, default_name):
        hn = cfg.get(preset_key, default_name)
        hi = FRIENDLY_AIRCRAFT_DB.get(hn, {})
        if not (cfg.get(enable_key, False) and hi.get('on_deck', False)):
            return
        base_m = hi.get('base_dist_km',0)*1000 if hi.get('base_type')=='land' else 0
        for ev in list(all_events):
            if not (getattr(ev,'is_active',False) and ev.enemy_info.get('type')=='잠수함'
                    and not getattr(ev,'intercepted',True)):
                continue
            fly_t = (base_m + ev.detect_m) / max(hi['speed_ms'],1)
            if hi['sortie_time_s'] + fly_t >= (ev.t_impact - ev.spawn_t):
                continue
            # 대잠 전담 함정 선택 (FFX 우선 → KDX-III)
            asw = next((s for s in fleet.operational_ships()
                        if s.ship_type == 'FFX'), None) or fleet.ships[0]
            h_ev = HeloEvent(hn, ev.spawn_t+5.0, ev, cfg,
                             asw.inventory, asw.status, weather_delta, silent)
            h_ev.run()
            all_events.append(h_ev)

    _try_aircraft_fleet('helo_preset', 'enable_helo', 'AW-159 와일드캣')
    _try_aircraft_fleet('p3c_preset',  'enable_p3c',  'P-3C 오라이온')
    _try_aircraft_fleet('p8a_preset',  'enable_p8a',  'P-8A 포세이돈')

    # ── 함정별 비용 집계 ───────────────────────────────────────────────
    for ev in all_events:
        # BUG-FIX v6.8.3: HeloEvent는 assigned_ship 없음 → getattr 사용
        _ev_ship = getattr(ev, 'assigned_ship', None)
        if _ev_ship:
            for ship in fleet.ships:
                if ship.name == _ev_ship:
                    ship.total_cost += ev.total_cost
                    break

    # ── 다층 방어 (Layered Defense) — 한국 해군 CEC 교리 기반 ──────────
    # 1차 교전 실패 시 → 다음 레이어 함정이 자동 인계
    LAYER_ORDER = ['KDX-III', 'KDX-II', 'FFX']

    if cfg.get('enable_fleet', False) and len(fleet.ships) > 1:
        for layer_num in range(1, 3):   # 최대 2차 추가 교전
            layer_pairs = []
            for ev in all_events:
                # 활성·미요격·플랫폼 이벤트만 대상
                # v6.8.4: HeloEvent 속성 없음 → getattr 안전 접근
                if not getattr(ev,'is_active',False): continue
                if getattr(ev,'intercepted',True): continue
                if getattr(ev,'is_missile',False): continue
                if getattr(ev,'_layered',False): continue  # 이미 레이어 생성된 이벤트 제외
                curr_ship = next((s for s in fleet.ships
                                  if s.name == getattr(ev, 'assigned_ship', '')), None)
                if curr_ship is None:
                    continue
                curr_idx = LAYER_ORDER.index(curr_ship.ship_type)                            if curr_ship.ship_type in LAYER_ORDER else -1

                # 다음 레이어 함정 선택
                next_ship = None
                for ntype in LAYER_ORDER[curr_idx + 1:]:
                    cands = [s for s in fleet.operational_ships()
                             if s.ship_type == ntype]
                    if cands:
                        next_ship = min(cands, key=lambda s: len(s.ch_mgr.schedules))
                        break
                if next_ship is None:
                    continue

                max_r = next_ship.max_weapon_range_m(ev.enemy_info)
                if max_r < 5000:   # 5km 미만이면 교전 불가
                    continue

                # 2차 교전 탐지거리 = min(무기 사거리 85%, 1차 거리 60%)
                layer_dm = min(max_r * 0.85, ev.detect_m * 0.60)
                layer_ev = ThreatEvent(
                    ev.label + f' [L{layer_num + 1}차]',
                    ev.spawn_t,
                    max(layer_dm, 5000),
                    ev.enemy_info, cfg,
                    weather_delta * (1.0 + 0.08 * layer_num),
                    cd_eff * max(0.3, 0.5 - 0.1 * layer_num),
                    next_ship.inventory, next_ship.ch_mgr, next_ship.ill_mgr,
                    ship_status=next_ship.status,
                    is_missile=False, silent=silent,
                    assigned_ship=next_ship.name)
                layer_ev._layered = True
                ev._layered = True   # 중복 레이어 생성 방지
                layer_pairs.append((ev, layer_ev))

            if not layer_pairs:
                break

            for primary_ev, layer_ev in layer_pairs:
                layer_ev.run()
                all_events.append(layer_ev)
                # 2차 교전 성공 시 — 1차 이벤트 화면에서 숨기고 2차로 대체
                if layer_ev.intercepted:
                    primary_ev.is_active = False

            # 비용 집계
            for _, lev in layer_pairs:
                for ship in fleet.ships:
                    if ship.name == getattr(lev,'assigned_ship',''):
                        ship.total_cost += lev.total_cost
                        break

    active = [e for e in all_events if e.is_active]
    ok     = sum(1 for e in active if e.intercepted)
    sr     = (ok / len(active)) if active else 1.0

    fleet_status = FleetStatus(fleet)
    global_inv   = fleet.global_inventory_summary()
    fleet_ch_mgr = FleetChannelManager(fleet.ships)

    return sr, all_events, active, global_inv, fleet_ch_mgr, fleet_status


def monte_carlo(cfg, weather, n=1000, desc='', save_nth=0):
    w=WEATHER_DB[weather]
    dm_eff_w=cfg['detect_km']*1000*w['detect_range_factor']
    cd_eff_w=cfg['cd_time_s']*w['cd_time_factor']
    results=[]; hit_counts=[]; mc_sample_logs=[]; step=max(1,n//5)
    if desc: print(f"    [{desc}] {n}회 시작... ",end='',flush=True)
    for i in range(n):
        use_s=(i+1!=save_nth)
        if cfg.get('enable_fleet', False):
            _fl=build_fleet(cfg)
            sr,evs,_,_,_,ss=run_fleet_sim_core(cfg,dm_eff_w,w['intercept_prob_delta'],cd_eff_w,_fl,silent=use_s)
        else:
            sr,evs,_,_,_,ss=run_single_sim(cfg,dm_eff_w,w['intercept_prob_delta'],cd_eff_w,silent=use_s)
        results.append(sr); hit_counts.append(ss.hit_count)
        if not use_s:
            mc_sample_logs=sorted([e for ev in evs for e in ev.log],key=lambda x:x['t'])
        if desc and (i+1)%step==0: print(f"{(i+1)*100//n}%",end=' ',flush=True)
    if desc: print("완료")
    class MCArray(np.ndarray):
        pass
    arr=np.array(results).view(MCArray)
    arr.mc_hit_avg=float(np.mean(hit_counts))
    arr.mc_sample_logs=mc_sample_logs
    return arr


def scenario_comparison(cfg):
    res={}
    for label,wk in [('최선(맑음)','맑음 (주간)'),('평균(흐림)','흐림 (박무)'),('최악(폭풍)','폭풍 (해상 악화)')]:
        mc=monte_carlo(cfg,wk,n=300,desc=f'시나리오: {label}')
        res[label]={'mean':mc.mean()*100,'full_pass':(mc==1.0).mean()*100,'mc_array':mc}
    return res


def evaluate_requirements(cfg, max_cd, mc, min_d, dm_eff, cd_eff, global_inv):
    spec=SHIP_SPEC[cfg['category']]; mc_pass=(mc==1.0).mean()*100; dm_km=dm_eff/1000
    rem_cd=enemy_pos(cd_eff,dm_eff,cfg['enemy_speed_ms'])
    t_i,_=intercept_time(cd_eff,dm_eff,cfg['enemy_speed_ms'],cfg['weapon_speed_ms'])
    req3=rem_cd>0 and t_i is not None and (cd_eff+t_i)<=dm_eff/cfg['enemy_speed_ms']
    rf_t=cd_eff+cfg['confirm_time_s']+cd_eff
    rem_rf=enemy_pos(rf_t+cd_eff,dm_eff,cfg['enemy_speed_ms'])
    t_i2,_=intercept_time(rf_t+cd_eff,dm_eff,cfg['enemy_speed_ms'],cfg['weapon_speed_ms'])
    req6=rem_rf>0 and t_i2 is not None and (rf_t+cd_eff+t_i2)<=dm_eff/cfg['enemy_speed_ms']
    req7=any(global_inv.get(w,0)>0 for w in global_inv if w!='CIWS-II (Phalanx)')
    verdicts=[dm_km<=spec['detect_km_max'],cfg['cd_time_s']<=max_cd,req3,mc_pass>=90.0,
              dm_km>=min_d/1000 if min_d else True,req6,req7,cfg['num_threats']<=MAX_ENGAGEMENT_CHANNELS]
    details=[
        f"유효 탐지거리 {dm_km:.1f}km <= 센서한계 {spec['detect_km_max']}km",
        f"C&D {cfg['cd_time_s']}s <= 최대허용 {max_cd:.1f}s",
        f"C&D 후 잔거리 {rem_cd/1000:.1f}km | {'가능' if req3 else '불가'}",
        f"전탄 성공률 {mc_pass:.1f}% >= 90%",
        f"탐지거리 {dm_km:.1f}km >= 최소필요 {min_d/1000:.1f}km" if min_d else "계산불가",
        f"재교전 잔거리 {rem_rf/1000:.1f}km | {'가능' if req6 else '불가'}",
        f"잔여 주요 무기 {'확보됨' if req7 else '전량 소진!'}",
        f"위협 {cfg['num_threats']}개 <= 채널 {MAX_ENGAGEMENT_CHANNELS}개",
    ]
    return verdicts,details


# ════════════════════════════════════════════════════════════════════════════
#  메인 시뮬레이션 실행기
# ════════════════════════════════════════════════════════════════════════════
def run_full_simulation(cfg):
    if cfg.get('missile_salvo_mode')=='FIXED':
        _et=ENEMY_DB[cfg['enemy_preset']]
        _sf=cfg.get('missile_salvo_fixed',1)
        _mn=_et.get('missile_salvo_min',1); _mx=_et.get('missile_salvo_max',2)
        _cl=min(max(_sf,_mn),_mx)
        if _sf!=_cl: print(f'  [경고] salvo_fixed={_sf} 범위({_mn}~{_mx}) 초과 → {_cl}발 조정')

    enemy=ENEMY_DB[cfg['enemy_preset']]; friend=FRIENDLY_DB[cfg['friendly_preset']]
    cfg['enemy_speed_ms']=(cfg['custom_enemy_speed'] if cfg.get('use_custom_enemy') else enemy['speed_ms'])
    # NEW-L: enemy_fleet_mode 기본값 보장
    if 'enemy_fleet_mode' not in cfg:
        cfg['enemy_fleet_mode'] = 'single'
    cfg['detect_km']     =(cfg['custom_detect_km']   if cfg.get('use_custom_enemy')
                           else min(calculate_detect_range_by_rcs(enemy),1200.0))
    cfg['weapon_speed_ms']=friend['speed_ms']; cfg['req_weapon_name']=cfg['friendly_preset']

    dm_eff,weather_delta,cd_eff=apply_weather(cfg,cfg['weather'])

    if cfg['combat_mode']=='AUTO':
        trial_inv={k:v for k,v in cfg['inventory'].items()}
        e_info={'category':enemy['category'],'type':enemy['type'],
                'is_hgv':enemy.get('is_hgv',False),'is_qbm':enemy.get('is_qbm',False)}
        for td in [max(1000,enemy_pos(cd_eff,dm_eff,cfg['enemy_speed_ms'])),240000,170000,9000,2000]:
            aw=select_weapon(e_info,td,trial_inv,'AUTO')
            if aw and aw in FRIENDLY_DB:
                cfg['weapon_speed_ms']=FRIENDLY_DB[aw]['speed_ms']
                cfg['req_weapon_name']=aw; break

    wpn_range_m=FRIENDLY_DB[cfg['req_weapon_name']]['range_km']*1000
    max_cd,t_arrive_base,t_fly_min=max_allowed_cd(dm_eff,cfg['enemy_speed_ms'],cfg['weapon_speed_ms'],wpn_range_m)
    min_d=min_detect_distance(cd_eff,cfg['enemy_speed_ms'],cfg['weapon_speed_ms'],wpn_range_m)

    # NEW-F: 자체방어 파라미터 출력
    sdpk   = enemy.get('self_defense_pk',0.0)
    civspk = enemy.get('enemy_ciws_pk',0.0)

    print("\n"+"="*88)
    print("  이지스 기동전단 통합 방어 시뮬레이터 v6.8")
    print("="*88)
    print(f"  적 위협       : {cfg['enemy_preset']}")
    print(f"  날씨          : {cfg['weather']}")
    print(f"  유효 탐지거리 : {dm_eff/1000:.1f}km")
    print(f"  REQ 기준 무기 : {cfg['req_weapon_name']} ({cfg['weapon_speed_ms']}m/s)")
    print(f"  최대 허용 C&D : {max_cd:.1f}s")
    print(f"  다발 발사 모드: {cfg.get('missile_salvo_mode','RANDOM')}  |  "
          f"적 회피기동: {'ON' if cfg.get('enable_enemy_evasion',True) else 'OFF'}  |  "
          f"기만기: {'ON' if cfg.get('enable_acoustic_decoy',True) else 'OFF'} "
          f"({cfg.get('decoy_stock',4)}발)")
    print(f"  [NEW-F] 적 자체방어: {'ON' if cfg.get('enable_enemy_self_defense',True) else 'OFF'}  |  "
          f"채프·플레어(self_def_pk)={sdpk:.0%}  |  CIWS요격확률={civspk:.0%}")
    print(f"  [BUG-1 FIX] 수상함·잠수함 미사일 발사 보장 (fire_m = min(desired, dm×0.90))")
    print(f"  [NEW-G] ECM: {'ON' if cfg.get('enable_ecm',True) else 'OFF'} | ecm_power={enemy.get('ecm_power',0.0):.2f}")
    _hn=cfg.get('helo_preset','AW-159 와일드캣')
    print(f"  [NEW-H] 헬기: {'ON' if cfg.get('enable_helo',False) else 'OFF'} | {_hn} ({'탑재중' if FRIENDLY_AIRCRAFT_DB.get(_hn,{}).get('on_deck',False) else '미탑재'})")
    print("-"*88)

    # NEW-K: 편대 모드 ON/OFF 분기
    if cfg.get('enable_fleet', False):
        _fleet=build_fleet(cfg)
        sr,all_events,active_events,global_inv,ch_mgr,ship_status=run_fleet_sim_core(cfg,dm_eff,weather_delta,cd_eff,_fleet)
    else:
        sr,all_events,active_events,global_inv,ch_mgr,ship_status=run_single_sim(cfg,dm_eff,weather_delta,cd_eff)

    all_logs=sorted([e for ev in all_events for e in ev.log],key=lambda x:x['t'])
    print(f"\n  [타임라인 교전 로그]")
    print(f"  {'─'*84}\n  {'시각':>7}  {'ID':<8}  {'위협명':<22}  메시지\n  {'─'*84}")
    for e in all_logs:
        print(f"  [t={e['t']:>5.0f}s]  {e['uid']:<8}  {e['label'][:22]:<22}  {e['icon']} {e['msg']}")
    print(f"  {'─'*84}")

    total_cost=sum(ev.total_cost for ev in all_events)
    ok=sum(1 for e in active_events if e.intercepted); tot=len(active_events)
    total_ciws_blocks=sum(ev.enemy_ciws_blocks for ev in all_events)
    total_sd_apps    =sum(ev.enemy_self_def_apps for ev in all_events)

    print(f"\n  [교전 결과 요약]")
    print(f"  실제 발생 위협: {tot}개  |  결과: {ok}/{tot} 방어 {'성공' if ok==tot and tot>0 else '실패'}")
    print(f"  총 교전 비용  : ${total_cost:,.0f} (약 {total_cost*1350/1e8:.1f}억원)")
    print(f"  최대 동시채널 : {ch_mgr._peak}/{MAX_ENGAGEMENT_CHANNELS}")
    print(f"  음향 기만기   : {ship_status.decoys_fired}발 발사 / {ship_status.decoy_success_count}회 성공 "
          f"/ 잔여 {ship_status.decoy_stock}발")
    print(f"  [NEW-F] 적 CIWS 격추: {total_ciws_blocks}발  |  "
          f"채프·플레어 Pk감소 적용: {total_sd_apps}발  |  CIWS확률={civspk:.0%}")
    print(f"  [NEW-G] ECM: {'ON' if cfg.get('enable_ecm',True) else 'OFF'}")
    print(f"  [NEW-H] 헬기: 출격 {ship_status.helo_sorties}회 | 요격 {ship_status.helo_intercepts}회")
    # NEW-K: 편대 모드 시 함정별 생존 현황 출력
    if getattr(ship_status, 'is_fleet', False):
        print(f"  [NEW-K 편대] {ship_status.survival_count}/{ship_status.ship_count}척 생존 "
              f"(생존율 {ship_status.survival_rate*100:.0f}%)")
        for sr_info in ship_status.ship_results:
            stat = '✓ 작전중' if sr_info['operational'] else '✗ 전투불능'
            print(f"    {sr_info['name']:<16} [{sr_info['type']:<7}]  {stat}  "
                  f"피격:{sr_info['hit_count']}회  비용:{sr_info['cost']/1e6:.1f}M$")
    elif not ship_status.operational:
        print(f"  [경고] 함정 피격 {ship_status.hit_count}회 — 전투 불능 (t={ship_status.hit_time:.0f}s)")

    print("\n  [무기 재고 현황]")
    # BUG-1 수정(v6.6.1): 편대 모드에서 초기 재고를 편대 합산으로 계산
    if cfg.get('enable_fleet', False):
        _tmp = build_fleet(cfg)
        _init_inv = _tmp.global_inventory_summary()
    else:
        _init_inv = cfg['inventory'].copy()
    for wn,ini in _init_inv.items():
        if wn=='CIWS-II (Phalanx)': continue
        used=ini-global_inv.get(wn,0)
        if used>0 or ini>0: print(f"  - {wn:<15}: 남은 {global_inv.get(wn,0):>2}발 / 사용 {used:>2}발")

    print(f"\n  [몬테카를로(Monte Carlo) 1000회]")
    mc=monte_carlo(cfg,cfg['weather'],n=1000,desc='메인 시뮬레이션',save_nth=cfg.get('mc_save_nth',0))
    print(f"  평균 {mc.mean()*100:.1f}%  |  전탄 성공 {(mc==1.0).mean()*100:.1f}%  |  표준편차 {mc.std()*100:.1f}%p")

    print(f"\n  [날씨별 시나리오 비교 — 각 300회]")
    sc_results=scenario_comparison(cfg)
    for label,res in sc_results.items():
        print(f"  {label:<16}: 평균 {res['mean']:.1f}% | 전탄 {res['full_pass']:.1f}%")

    verdicts,details=evaluate_requirements(cfg,max_cd,mc,min_d,dm_eff,cd_eff,global_inv)
    print(f"\n  [REQ(요구조건) 추적표]")
    print(f"  {'ID':<8} {'요구조건':<22} {'판정':<8} 상세\n  {'-'*78}")
    for req,v,d in zip(REQ_ITEMS,verdicts,details):
        print(f"  {req['id']:<8} {req['name']:<22} {'PASS' if v else 'FAIL':<9} {d}")
    print(f"\n  전체: {sum(verdicts)}/{len(verdicts)} 충족")

    print(f"\n  {'═'*84}\n  [교전 상황 서술]\n  {'─'*84}")
    print(f"  {'ID':<7} {'위협명':<24} {'탐지거리':>9}  교전 결과\n  {'─'*84}")
    for ev in all_events:
        if not ev.is_active: continue
        det=f"{ev.detect_m/1000:>6.1f}km"
        if ev.enemy_info.get('category')=='어뢰':
            res="[기만/회피] 어뢰 무력화" if ev.intercepted else "[피격] 어뢰 명중"
        elif ev.intercepted and ev.intercept_km is not None:
            evn=f" (회피기동 {ev.evasion_count}회)" if ev.evasion_count>0 else ""
            sd_n=(f" [적CIWS격추{ev.enemy_ciws_blocks}발]" if ev.enemy_ciws_blocks>0 else "")
            res=f"[요격] {ev.intercept_km:>5.1f}km | {ev.intercept_weapon}{evn}{sd_n}"
        else:
            evn=f" (회피기동 {ev.evasion_count}회)" if ev.evasion_count>0 else ""
            sd_n=(f" [적CIWS격추{ev.enemy_ciws_blocks}발]" if ev.enemy_ciws_blocks>0 else "")
            res=f"[피격] 방어망 돌파{evn}{sd_n}"
        print(f"  {ev.uid:<7} {ev.label[:22]:<24} {det}  {res}")
    print(f"  {'─'*84}")
    ok_evs=[e for e in all_events if e.is_active and e.intercepted and e.intercept_km]
    if ok_evs:
        print(f"  ▶ 요격 {len(ok_evs)}건 | 평균 {np.mean([e.intercept_km for e in ok_evs]):.1f}km | "
              f"최근접 {min(e.intercept_km for e in ok_evs):.1f}km | "
              f"최원거리 {max(e.intercept_km for e in ok_evs):.1f}km")
    if not ship_status.operational:
        print(f"  ▶ [경고] 함정 피격 — {ship_status.hit_by}")
    print(f"  ▶ [NEW-F] 적 자체방어 통계: CIWS격추 {total_ciws_blocks}발, "
          f"Pk감소 {total_sd_apps}회")
    print(f"  {'═'*84}\n")

    return (max_cd,t_arrive_base,t_fly_min,mc,min_d,
            all_events,active_events,verdicts,details,sc_results,
            dm_eff,weather_delta,cd_eff,total_cost,global_inv,
            ch_mgr,ship_status)


# ════════════════════════════════════════════════════════════════════════════
#  전술 교전도
# ════════════════════════════════════════════════════════════════════════════

# ════════════════════════════════════════════════════════════════════════════
#  v6.8: Top-down 2D 전술교전도 (다방위 공격 시각화)
# ════════════════════════════════════════════════════════════════════════════
def draw_topdown_tactical(ax, cfg, all_events, dm_eff, ship_status=None):
    ax.set_facecolor('#0a0e1a')
    ax.set_aspect('equal')
    detect_km = dm_eff / 1000

    # 탐지 범위 원
    circle = plt.Circle((0,0), detect_km, color='#5D6D7E', fill=False,
                         lw=1.0, ls='--', alpha=0.6)
    ax.add_patch(circle)
    ax.text(0, detect_km+detect_km*0.03, f'레이더 ({detect_km:.0f}km)',
            ha='center', fontsize=8, color='#5D6D7E')

    # 무기 사거리 링
    WPN_RINGS = [('SM-3',500,'#8E44AD'),('SM-6',370,'#2980B9'),
                 ('SM-2',170,'#27AE60'),('RAM',9,'#E67E22')]
    for wn,r_km,wc in WPN_RINGS:
        if r_km > detect_km: continue
        c2 = plt.Circle((0,0), r_km, color=wc, fill=False, lw=0.8,
                         ls=':', alpha=0.5)
        ax.add_patch(c2)
        ax.text(r_km*0.707+1, r_km*0.707+1, wn, fontsize=7, color=wc, alpha=0.8)

    # 아군 함정 (중앙)
    ax.scatter(0, 0, s=200, color='#1ABC9C', marker='s', zorder=8,
               edgecolors='white', linewidths=1.5)
    ax.text(0.5, -detect_km*0.06, '정조대왕함', ha='center',
            fontsize=8, color='#1ABC9C', fontweight='bold')

    # 위협 경로 (방위각 기반)
    import math
    col_ok = '#2ECC71'; col_fail = '#E74C3C'; col_mis = '#E67E22'
    active_evs = [e for e in all_events if e.is_active]
    for ev in active_evs:
        bearing = ev.enemy_info.get('bearing_deg', 0)
        rad = math.radians(90 - bearing)  # 북=0도 기준
        # 탐지 위치 (원 위)
        sx = detect_km * math.cos(rad)
        sy = detect_km * math.sin(rad)
        # 요격 지점
        if ev.intercepted and ev.intercept_km:
            ix = (detect_km - ev.intercept_km) / detect_km * sx
            iy = (detect_km - ev.intercept_km) / detect_km * sy
            col = col_ok
            ax.annotate('', xy=(ix,iy), xytext=(sx,sy),
                        arrowprops=dict(arrowstyle='->', color=col,
                                        lw=1.2, alpha=0.8))
            ax.scatter(ix, iy, s=60, color=col, marker='*', zorder=7)
        else:
            col = col_fail if not ev.is_missile else col_mis
            ax.annotate('', xy=(0,0), xytext=(sx,sy),
                        arrowprops=dict(arrowstyle='->', color=col,
                                        lw=1.5, alpha=0.9))
        ax.scatter(sx, sy, s=70, color=col, marker='^', zorder=6,
                   edgecolors='white', linewidths=0.5)
        ax.text(sx*1.05, sy*1.05, ev.label[:10], fontsize=6.5,
                color=col, ha='center')

    # 방위각 눈금 (N/E/S/W)
    for deg, lbl in [(90,'N'),(0,'E'),(270,'S'),(180,'W')]:
        r2 = math.radians(90-deg)
        ax.text(detect_km*1.08*math.cos(r2),
                detect_km*1.08*math.sin(r2),
                lbl, ha='center', va='center',
                fontsize=9, color='#BDC3C7', fontweight='bold')

    lim = detect_km * 1.15
    ax.set_xlim(-lim, lim); ax.set_ylim(-lim, lim)
    ax.set_xlabel('동-서 (km)', fontsize=8, color='#BDC3C7')
    ax.set_ylabel('남-북 (km)', fontsize=8, color='#BDC3C7')
    ax.set_title('Top-down 전술교전도 (다방위 공격)', fontsize=10,
                 fontweight='bold', color='white')
    ax.tick_params(colors='#BDC3C7', labelsize=7)
    for sp in ax.spines.values(): sp.set_color('#444')
    # 범례
    from matplotlib.lines import Line2D
    legend_items = [
        Line2D([0],[0],color='#2ECC71',lw=2,label='요격 성공'),
        Line2D([0],[0],color='#E74C3C',lw=2,label='피격'),
    ]
    ax.legend(handles=legend_items, loc='lower right', fontsize=8,
              labelcolor='white', facecolor='#0a0e1a', edgecolor='#444')

def draw_janes_tactical(ax, cfg, all_events, dm_eff, threat_nums, ship_status=None,
                        # NEW-M: 전술교전도 레이어 ON/OFF (v6.5)
                        show_fleet_positions=True,   # 레이어1: 편대 함정 위치·담당 구역
                        show_threat_paths=True,      # 레이어2: 위협 경로·요격 지점
                        show_radar_range=True,       # 레이어3: 레이더 탐지 범위
                        show_timeline=True,          # 레이어4: 교전 타임라인
                        show_weapon_range=True):     # 레이어5: 무기 사거리 링
    category=cfg['category']; detect_km=dm_eff/1000
    cp=CAT_PARAMS.get(category,CAT_PARAMS['대공'])
    Y_VIS_MAX=detect_km*0.62; Y_VIS_SEA=0.0
    Y_VIS_MIN=(-detect_km*0.08 if category=='대공' else -detect_km*0.10 if category=='대함' else -detect_km*0.24)
    ruler_y=Y_VIS_MIN*0.28; SUMMARY_Y=Y_VIS_MIN*0.80

    def a2v(alt_m):
        m=float(alt_m)
        if m>=0: return min((m/cp['max_m'])*Y_VIS_MAX,Y_VIS_MAX*0.96)
        else:    return max((m/abs(cp['min_m']))*abs(Y_VIS_MIN),Y_VIS_MIN*0.96)

    x_max=detect_km*1.12
    ax.fill_between([0,x_max],Y_VIS_SEA,Y_VIS_MAX,color='#C0D8EC',zorder=0)
    ax.fill_between([-detect_km*0.04,x_max],Y_VIS_MIN,Y_VIS_SEA,color='#154360',zorder=0)
    if category=='대잠':
        ax.fill_between([-detect_km*0.04,x_max],a2v(-200),Y_VIS_SEA,color='#1A5276',alpha=0.5,zorder=0)
        ax.fill_between([-detect_km*0.04,x_max],a2v(-400),a2v(-200),color='#154360',alpha=0.5,zorder=0)
        ax.fill_between([-detect_km*0.04,x_max],Y_VIS_MIN,a2v(-400),color='#0B2545',alpha=0.6,zorder=0)
    ax.axhline(Y_VIS_SEA,color='#0D3050',lw=2.5,zorder=1)

    theta=np.linspace(0.008,np.pi-0.008,500)
    if cp['use_arcs']:
        Y_ARC=0.55
        xr=detect_km*np.cos(theta); yr=detect_km*np.sin(theta)*Y_ARC
        ax.plot(xr[xr>=-detect_km*0.02],yr[xr>=-detect_km*0.02],color='#5D6D7E',lw=1.3,ls='--',alpha=0.55,zorder=2)
        for i,L in enumerate(TACTICAL_LAYERS):
            r=L['km']
            if r>detect_km*1.02: continue
            xa=r*np.cos(theta); ya=r*np.sin(theta)*Y_ARC; mask=xa>=-r*0.05
            ax.plot(xa[mask],ya[mask],color=L['color'],lw=L['lw'],alpha=0.82,zorder=3)
            ax.plot([r,r],[Y_VIS_MIN*0.12,0],color=L['color'],lw=1.0,ls=':',alpha=0.45,zorder=2)
            ang=np.radians([86,78,64,57,50][i] if i<5 else 48)
            lx,ly=r*np.cos(ang),r*np.sin(ang)*Y_ARC
            if lx>detect_km*0.015 and ly>0:
                ax.text(lx+detect_km*0.01,ly+detect_km*0.008,L['name'],fontsize=8,color=L['color'],fontweight='bold',zorder=7,
                        bbox=dict(boxstyle='round,pad=0.22',fc='white',alpha=0.82,ec='none'))
        ax.text(detect_km*np.cos(np.radians(42))+detect_km*0.01,detect_km*np.sin(np.radians(42))*Y_ARC,
                f'레이더 ({detect_km:.0f}km)',fontsize=7.5,color='#5D6D7E',zorder=7,
                bbox=dict(boxstyle='round,pad=0.22',fc='white',alpha=0.75,ec='none'))

        # ── 레이어 3: 함정별 레이더 탐지 범위 (편대 모드) ─────────────
        if show_radar_range and getattr(ship_status,'is_fleet',False):
            radar_colors = {'KDX-III':'#1ABC9C','KDX-II':'#F39C12','FFX':'#9B59B6'}
            for sr_info in ship_status.ship_results[1:]:
                stype = sr_info['type']
                r_km  = SHIP_DB.get(stype,{}).get('sensor_km',{}).get('대공',0)
                if r_km <= 0: continue
                rc = radar_colors.get(stype,'#BDC3C7')
                xa2 = r_km*np.cos(theta); ya2 = r_km*np.sin(theta)*Y_ARC
                mask2 = xa2 >= -r_km*0.05
                ax.plot(xa2[mask2],ya2[mask2],color=rc,lw=1.0,ls='-.',alpha=0.5,zorder=3)
                ax.text(r_km*np.cos(np.radians(75))+detect_km*0.01,
                        r_km*np.sin(np.radians(75))*Y_ARC,
                        f'{sr_info["name"][:3]}({r_km}km)',
                        fontsize=6.5,color=rc,alpha=0.8,zorder=4)

        # ── 레이어 5: 무기 사거리 링 ──────────────────────────────────
        if show_weapon_range and cp.get('use_arcs',False):
            WPN_RANGE = [
                ('SM-3',  500, '#8E44AD', '━'),
                ('SM-6',  370, '#2980B9', '━'),
                ('SM-2',  170, '#27AE60', '--'),
                ('RAM',     9, '#E67E22', ':'),
            ]
            for wn, r_km, wc, wls in WPN_RANGE:
                if r_km > detect_km * 1.05: continue
                xw = r_km*np.cos(theta); yw = r_km*np.sin(theta)*Y_ARC
                mw = xw >= -r_km*0.05
                ax.plot(xw[mw], yw[mw], color=wc, lw=1.2,
                        ls='--' if wls=='--' else ':' if wls==':' else '-',
                        alpha=0.6, zorder=3)
                ang_w = np.radians(30 if wn=='RAM' else 22)
                ax.text(r_km*np.cos(ang_w), r_km*np.sin(ang_w)*Y_ARC,
                        f'{wn} ({r_km}km)', fontsize=7, color=wc,
                        fontweight='bold', alpha=0.85, zorder=4,
                        bbox=dict(boxstyle='round,pad=0.15',fc='white',alpha=0.7,ec='none'))
        for alt_m,lbl in [(2000,'2km'),(5000,'5km'),(10000,'10km'),(15000,'15km')]:
            vy=a2v(alt_m); ax.axhline(vy,color='gray',lw=0.6,ls=':',alpha=0.35,zorder=2)
            ax.text(-detect_km*0.025,vy,lbl,fontsize=7,color='gray',ha='right',va='center')
    else:
        layers=SURFACE_LAYERS if category=='대함' else SUB_LAYERS
        for j,L in enumerate(layers):
            r=L['km']
            if r>detect_km*1.02: continue
            ax.axvline(r,color=L['color'],lw=1.8,ls='--',alpha=0.75,zorder=3)
            ax.axvspan(0,r,alpha=0.04*(len(layers)-j),color=L['color'],zorder=2)
            ax.text(r,Y_VIS_MAX*0.91,L['name'],fontsize=8,color=L['color'],fontweight='bold',ha='center',
                    bbox=dict(boxstyle='round,pad=0.22',fc='white',alpha=0.82,ec='none'),zorder=7)
        ref_alts=([(15,'수면+15m'),(-100,'수심 100m'),(-300,'수심 300m')] if category=='대함'
                  else [(0,'해수면'),(-100,'수심 100m'),(-300,'수심 300m'),(-500,'수심 500m')])
        for alt_m,lbl in ref_alts:
            vy=a2v(alt_m); ax.axhline(vy,color='lightcyan',lw=0.7,ls=':',alpha=0.5,zorder=2)
            ax.text(-detect_km*0.025,vy,lbl,fontsize=7,color='lightcyan',ha='right',va='center')

    ship_col='#8B0000' if (ship_status and not ship_status.operational) else '#1C2833'
    sw,sh=detect_km*0.055,detect_km*0.038
    ax.add_patch(patches.FancyBboxPatch((-sw*0.35,-sh*0.18),sw,sh*0.55,boxstyle='round,pad=0.002',fc=ship_col,ec='#0A1A28',lw=0.8,zorder=6))
    ax.add_patch(patches.FancyBboxPatch((-sw*0.18,sh*0.36),sw*0.52,sh*0.55,boxstyle='round,pad=0.001',fc=ship_col,ec='#0A1A28',lw=0.6,zorder=6))
    ax.plot([0,0],[sh*0.9,sh*1.55],color=ship_col,lw=1.8,zorder=6)
    ax.plot([-sw*0.12,sw*0.12],[sh*1.2,sh*1.2],color=ship_col,lw=1.3,zorder=6)
    ship_lbl='정조대왕함 [전투불능]' if (ship_status and not ship_status.operational) else '정조대왕함'
    ax.text(sw*0.05,Y_VIS_MIN*0.35,ship_lbl,fontsize=9,color='white',fontweight='bold',ha='center',zorder=7)

    # ── 레이어 1: 편대 함정 위치·담당 구역 ───────────────────────────
    if show_fleet_positions and getattr(ship_status,'is_fleet',False):
        fleet_colors = ['#1ABC9C','#F39C12','#9B59B6','#E74C3C','#3498DB','#27AE60']
        n_ships = len(ship_status.ship_results)
        for fi, sr_info in enumerate(ship_status.ship_results):
            if fi == 0:
                continue  # 지휘함(정조대왕함)은 기존 아이콘 사용
            fc = fleet_colors[fi % len(fleet_colors)]
            # 편대 함정은 x=-1~-3km 위치에 세로로 배치
            fx = -detect_km * 0.045 * (fi + 0.5)
            fy = 0
            fsw, fsh = detect_km*0.035, detect_km*0.025
            ax.add_patch(patches.FancyBboxPatch(
                (fx-fsw*0.35, fy-fsh*0.18), fsw, fsh*0.55,
                boxstyle='round,pad=0.002',
                fc=fc if sr_info['operational'] else '#7F8C8D',
                ec='#0A1A28', lw=0.7, zorder=6))
            ax.text(fx+fsw*0.15, fy-detect_km*0.06,
                    f"{sr_info['name'][:5]}\n({sr_info['type']})",
                    fontsize=6.5, color='white', fontweight='bold',
                    ha='center', zorder=7)
            # 담당 구역 표시 (담당 위협 방향 점선)
            assigned = [ev for ev in all_events
                        if ev.is_active and getattr(ev,'assigned_ship','') == sr_info['name']]
            for aev in assigned[:2]:
                ax.plot([fx, aev.detect_m/1000*0.15], [fy, 0],
                        color=fc, lw=0.8, ls=':', alpha=0.5, zorder=3)

    ev_palette=['#C0392B','#8E44AD','#D35400','#1C5B8C','#7F8C8D','#A93226','#117864','#784212']
    label_offsets={}; active_idx=0

    # ── 레이어 2: 위협 경로·요격 지점 ─────────────────────────────────
    for ev in all_events if show_threat_paths else []:
        if not ev.is_active: continue
        col=ev_palette[active_idx%len(ev_palette)]; disp_off=(active_idx%3-1)*detect_km*0.016; active_idx+=1
        num_label=threat_nums.get(ev.uid,f"#{active_idx}")
        raw_alt_m=ev.enemy_info.get('altitude_m',0)
        is_ballistic=(ev.enemy_info.get('type') in['탄도미사일','극초음속활공체','저고도기동탄도'])
        is_torpedo=(ev.enemy_info.get('category')=='어뢰')
        if ev.enemy_info.get('type')=='잠수함': raw_alt_m=getattr(ev,'current_depth',SUB_DEPTH_M.get(cfg['enemy_preset'],-250))
        if ev.enemy_info.get('type')=='어뢰': raw_alt_m=-50

        if is_ballistic and raw_alt_m>cp['max_m']:
            ev_vis_y=Y_VIS_MAX*0.88+disp_off
            stag=(' [HGV·극초음속]' if ev.enemy_info.get('is_hgv') else
                  ' [QBM·저고도기동]' if ev.enemy_info.get('is_qbm') else '')
            ax.annotate(f'v {num_label}  최고고도 {raw_alt_m/1000:.0f}km{stag}',
                        xy=(ev.detect_m/1000,Y_VIS_MAX*0.98),xytext=(ev.detect_m/1000,ev_vis_y),
                        fontsize=8.5,color=col,fontweight='bold',ha='center',
                        bbox=dict(boxstyle='round,pad=0.3',fc='white',alpha=0.85,ec=col,lw=0.8),
                        arrowprops=dict(arrowstyle='->',color=col,lw=1.5),zorder=8)
        else:
            ev_vis_y=a2v(raw_alt_m)+disp_off

        ls='--' if ev.is_missile else '-'
        if is_torpedo:
            tc='#16A085' if ev.intercepted else '#8B0000'
            ax.plot([ev.detect_m/1000,0],[ev_vis_y,a2v(-50)],color=tc,lw=1.8,ls=':',alpha=0.7,zorder=4)
            lbl='[기만/회피 성공]' if ev.intercepted else '[어뢰 명중]'
            ax.text(detect_km*0.04,a2v(-50)+detect_km*0.02,lbl,fontsize=8.5,color=tc,fontweight='bold',zorder=9)
        elif ev.intercepted and ev.intercept_km is not None:
            ix_km=ev.intercept_km; progress=ix_km/max(ev.detect_m/1000,0.001)
            iy_vis=a2v(raw_alt_m*progress)+disp_off*progress
            ax.plot([ev.detect_m/1000,ix_km],[ev_vis_y,iy_vis],color=col,lw=1.8,ls=ls,alpha=0.82,zorder=4)
            ax.annotate('',xy=(ix_km,iy_vis),xytext=(min(ev.detect_m/1000,ix_km+detect_km*0.06),ev_vis_y*0.9+iy_vis*0.1),
                        arrowprops=dict(arrowstyle='->',color=col,lw=1.5),zorder=4)
            wpn_col=WPN_COLOR.get(ev.intercept_weapon,'#2C3E50')
            bx,by=bezier_q((0,0),(ix_km*0.42,max(iy_vis+detect_km*0.04,ix_km*0.55*0.5)),(ix_km,iy_vis))
            ax.plot(bx,by,color=wpn_col,lw=2.3,zorder=5,solid_capstyle='round')
            ax.scatter(ix_km,iy_vis,s=130,color=wpn_col,marker='*',zorder=8,edgecolors='white',lw=0.9)
            bx_l=ix_km+detect_km*0.025; by_l=iy_vis+detect_km*0.045
            key_x=round(ix_km,0)
            if key_x in label_offsets: by_l+=label_offsets[key_x]; label_offsets[key_x]+=detect_km*0.09
            else: label_offsets[key_x]=detect_km*0.09
            wpn_s=(ev.intercept_weapon or '?').split(' ')[0]
            ev_tag=(' [HGV]' if ev.enemy_info.get('is_hgv') else ' [QBM]' if ev.enemy_info.get('is_qbm') else '')
            ciws_tag=f' [적CIWS{ev.enemy_ciws_blocks}발격추]' if ev.enemy_ciws_blocks>0 else ''
            # BUG-FIX v6.5.1: 담당 함정명 표시
            ax.annotate(f'{wpn_s}{ev_tag}{ciws_tag}\n[요격] {ix_km:.1f}km',
                        xy=(ix_km,iy_vis),xytext=(bx_l,by_l),fontsize=9,fontweight='bold',color=wpn_col,zorder=9,
                        bbox=dict(boxstyle='round,pad=0.3',fc='white',alpha=0.88,ec=wpn_col,lw=0.9),
                        arrowprops=dict(arrowstyle='-',color=wpn_col,lw=0.9))
        else:
            ax.plot([ev.detect_m/1000,0],[ev_vis_y,0],color='#C0392B',lw=2.0,ls=ls,alpha=0.9,zorder=4)
            ax.scatter(0,detect_km*0.015,s=120,color='red',marker='X',zorder=8,lw=2.5)
            ax.text(detect_km*0.04,detect_km*0.045,'[피격]',fontsize=10,color='red',fontweight='bold',zorder=9)

        if not (is_ballistic and raw_alt_m>cp['max_m']) and not is_torpedo:
            ax.scatter(ev.detect_m/1000,ev_vis_y,s=85,color=col,marker='^',zorder=6,edgecolors='black',lw=0.7)
            ax.text(ev.detect_m/1000,ev_vis_y+detect_km*0.025,num_label,fontsize=12,color=col,fontweight='bold',ha='center',zorder=7)

    ax.axhline(ruler_y,color='#2C3E50',lw=1.5,zorder=5)
    raw_t=sorted(set(k for k in [2,9,50,100,170,200,240,300,400,500,int(detect_km)] if 0<k<=detect_km*1.01))
    tc_map={L['km']:L['color'] for L in TACTICAL_LAYERS}
    for km in raw_t:
        tc=tc_map.get(km,'#2C3E50'); fw='bold' if km in tc_map else 'normal'
        ax.plot([km,km],[ruler_y-detect_km*0.012,ruler_y+detect_km*0.012],color=tc,lw=1.8 if fw=='bold' else 1.0,zorder=5)
        ax.text(km,ruler_y-detect_km*0.032,f'{km}km',fontsize=7.5,ha='center',color=tc,fontweight=fw,zorder=6)

    ax.spines['right'].set_visible(False); ax.spines['top'].set_visible(False)
    ax.spines['bottom'].set_visible(False); ax.spines['left'].set_color('#5D6D7E'); ax.spines['left'].set_alpha(0.6)
    ax.set_yticks([a2v(m) for m in cp['ticks_m']])
    ax.set_yticklabels([f"{m}m" if abs(m)<2000 else f"{m//1000}km" for m in cp['ticks_m']],fontsize=8,color='#2C3E50')
    ax.tick_params(axis='y',colors='#5D6D7E',length=4); ax.tick_params(axis='x',bottom=False,labelbottom=False)
    ax.set_ylabel(cp['ylabel'],fontsize=9,color='#5D6D7E',labelpad=4)

    active_evs=[e for e in all_events if e.is_active]
    if active_evs:
        lines=[]
        for ev in active_evs:
            num=threat_nums.get(ev.uid,'?'); det=f"{ev.detect_m/1000:.0f}km"
            ev_t=(' [HGV]' if ev.enemy_info.get('is_hgv') else ' [QBM]' if ev.enemy_info.get('is_qbm') else '')
            if ev.enemy_info.get('category')=='어뢰':
                res='[기만/회피 성공]' if ev.intercepted else '[어뢰 명중]'
            elif ev.intercepted and ev.intercept_km is not None:
                # 발사 함정 표시 추가
                wpn_short = (ev.intercept_weapon or '?').split(' ')[0]
                ship_short = getattr(ev,'assigned_ship','정조대왕함')
                res=f"[요격 {ev.intercept_km:.1f}km]  {ship_short} → {wpn_short}"
            else: res='[피격]'
            ev_evn=f" 회피{ev.evasion_count}회" if ev.evasion_count>0 else ""
            sd_n=f" [CIWS격추{ev.enemy_ciws_blocks}발]" if ev.enemy_ciws_blocks>0 else ""
            lines.append(f"{num} {ev.label[:13]}{ev_t}  탐지 {det:>6}  {res}{ev_evn}{sd_n}")
        ship_n=' [전투불능]' if (ship_status and not ship_status.operational) else ''
        decoy_n=f" | 기만기 {ship_status.decoy_success_count}/{ship_status.decoys_fired}회" if ship_status else ""
        ax.text(x_max*0.98,SUMMARY_Y,f"[ 위협 목록{ship_n}{decoy_n} ]\n"+"\n".join(lines),
                fontsize=8.5,va='bottom',ha='right',zorder=10,color='#1C2833',
                bbox=dict(boxstyle='round,pad=0.5',fc='white',alpha=0.90,ec='#5D6D7E',lw=0.8))

    # ── 레이어 4: 교전 타임라인 ────────────────────────────────────────
    if show_timeline:
        active_evs_tl = sorted([e for e in all_events if e.is_active],
                                key=lambda e: e.spawn_t)
        if active_evs_tl:
            tl_x0 = detect_km * 0.02
            tl_y  = Y_VIS_MIN * 0.55
            tl_h  = abs(Y_VIS_MIN) * 0.12
            t_max = max(e.t_impact for e in active_evs_tl if hasattr(e,'t_impact'))
            ax.text(tl_x0, tl_y + tl_h*1.6, '교전 타임라인',
                    fontsize=7.5, color='#2C3E50', fontweight='bold', zorder=10)
            ax.axhline(tl_y, xmin=0.01, xmax=0.97,
                       color='#2C3E50', lw=1.0, alpha=0.5, zorder=9)
            tl_colors = ['#C0392B','#8E44AD','#D35400','#1C5B8C','#7F8C8D','#117864']
            for ti, ev in enumerate(active_evs_tl[:8]):
                tc  = tl_colors[ti % len(tl_colors)]
                t0  = ev.spawn_t
                t1  = getattr(ev, 't_impact', t0 + 30)
                x0_ = tl_x0 + (t0 / max(t_max,1)) * (x_max * 0.88)
                x1_ = tl_x0 + (t1 / max(t_max,1)) * (x_max * 0.88)
                bar_y = tl_y - tl_h * (0.4 + ti * 0.22)
                ax.barh(bar_y, x1_-x0_, left=x0_, height=tl_h*0.18,
                        color=tc, alpha=0.75, zorder=10)
                mark = '★' if ev.intercepted else '✕'
                ax.text(x1_ + detect_km*0.01, bar_y,
                        f"{mark}{threat_nums.get(ev.uid,'?')}",
                        fontsize=6.5, color=tc, va='center', zorder=11)

    ax.set_xlim(-detect_km*0.05,x_max); ax.set_ylim(Y_VIS_MIN,Y_VIS_MAX)
    cat_label={'대공':'대공 방어','대함':'대함 방어','대잠':'대잠 방어'}.get(category,category)
    ax.set_title(
        f'전술 교전도 [{cat_label}]'
        f'  |  x축: 거리(km) | y축: {cp["ylabel"]} | ★ 요격 | X 피격 | [HGV] | [QBM] | 어뢰 기만/회피',
        fontsize=9.5, fontweight='bold', pad=6)


# ════════════════════════════════════════════════════════════════════════════
#  그래프 출력
# ════════════════════════════════════════════════════════════════════════════
def plot_all(cfg, max_cd, t_arrive_base, t_fly_min, mc, min_d,
             all_events, active_events, verdicts, details, sc_results,
             dm_eff, weather_delta, cd_eff, total_cost, global_inv,
             ch_mgr, ship_status=None,
             # NEW-M: 전술교전도 레이어 파라미터
             show_fleet_positions=True, show_threat_paths=True,
             show_radar_range=True, show_timeline=True, show_weapon_range=True,
             return_fig=False):   # NEW: True 시 fig 반환 (대시보드용)

    active_evs=[e for e in all_events if e.is_active]
    threat_nums={ev.uid:CIRCLE_NUMS[i] for i,ev in enumerate(active_evs) if i<len(CIRCLE_NUMS)}

    total_ciws_blocks=sum(ev.enemy_ciws_blocks for ev in all_events)
    total_sd_apps    =sum(ev.enemy_self_def_apps for ev in all_events)
    enemy=ENEMY_DB[cfg['enemy_preset']]
    sdpk  =enemy.get('self_defense_pk',0.0)
    civspk=enemy.get('enemy_ciws_pk',0.0)

    fig=plt.figure(figsize=(24,18))
    fig.suptitle(
        f"이지스 기동전단 통합 방어 시뮬레이션  v6.8.2  |  "
        f"위협: {cfg['enemy_preset']}  |  날씨: {cfg['weather']}  |  "
        f"탐지거리: {dm_eff/1000:.1f}km  |  "
        f"자체방어: {'ON' if cfg.get('enable_enemy_self_defense',True) else 'OFF'}  "
        f"(채프{sdpk:.0%} / CIWS{civspk:.0%})",
        fontsize=10.5, fontweight='bold', y=0.98)

    gs=gridspec.GridSpec(3,4,figure=fig,height_ratios=[3.5,1.8,1.8],hspace=0.42,wspace=0.38)
    fig.subplots_adjust(top=0.93,bottom=0.04)

    # v6.8: 다방위 공격 ON 시 측면도 + Top-down 2분할
    if cfg.get('enable_multibearing', False):
        gs2 = gridspec.GridSpecFromSubplotSpec(1, 2, subplot_spec=gs[0,:], wspace=0.3)
        ax2 = fig.add_subplot(gs2[0])
        ax_td = fig.add_subplot(gs2[1])
        draw_topdown_tactical(ax_td, cfg, all_events, dm_eff, ship_status)
    else:
        ax2 = fig.add_subplot(gs[0,:])
    draw_janes_tactical(ax2,cfg,all_events,dm_eff,threat_nums,ship_status,
        show_fleet_positions=show_fleet_positions, show_threat_paths=show_threat_paths,
        show_radar_range=show_radar_range, show_timeline=show_timeline,
        show_weapon_range=show_weapon_range)

    ax3=fig.add_subplot(gs[1,0]); ax3.axis('off')
    tbl=ax3.table(cellText=[[r['id'],r['name'][:11],'OK' if v else 'NG'] for r,v in zip(REQ_ITEMS,verdicts)],
                  colLabels=['ID','요구조건','판정'],cellLoc='center',loc='center')
    tbl.auto_set_font_size(False); tbl.set_fontsize(8.5); tbl.scale(1,1.5)
    for (r_idx,c_idx),cell in tbl.get_celld().items():
        if r_idx==0: cell.set_facecolor('#2c3e50'); cell.set_text_props(color='white',fontweight='bold')
        elif c_idx==2 and r_idx>0: cell.set_facecolor('#d5f5e3' if verdicts[r_idx-1] else '#fadbd8')
    ax3.set_title(f'RTM — 요구조건 추적표  ({sum(verdicts)}/{len(verdicts)})',fontsize=9.5,fontweight='bold')

    ax4=fig.add_subplot(gs[1,1:3]); gantt_rows=[]
    for ev in all_events:
        row_label=(f"{threat_nums.get(ev.uid,'')} {ev.label[:13]}" if ev.is_active else ev.label[:15])
        if ev.evasion_count>0 and ev.is_active: row_label+=f" [회피{ev.evasion_count}]"
        if ev.enemy_ciws_blocks>0 and ev.is_active: row_label+=f" [CIWS{ev.enemy_ciws_blocks}]"
        gantt_rows.append(row_label)
        for bar in ev.gantt_bars:
            ax4.barh(len(gantt_rows)-1,max(bar[2]-bar[1],0.5),left=bar[1],height=0.5,color=bar[3],edgecolor='white',linewidth=0.8,alpha=0.85)
        ax4.axvline(ev.t_impact,color='gray',lw=0.7,ls=':',alpha=0.4)
    ax4b=ax4.twinx()
    if ch_mgr.history:
        t_pts=sorted(set([r['t_start'] for r in ch_mgr.history]+[r.get('t_end',r['t_start']) for r in ch_mgr.history]))
        ch_c=[sum(1 for r in ch_mgr.history if r['t_start']<=t<r.get('t_end',t)) for t in t_pts]
        ax4b.step(t_pts,ch_c,where='post',color='purple',lw=1.5,ls='--',alpha=0.7)
        ax4b.set_ylabel('채널 수',color='purple',fontsize=8); ax4b.set_ylim(0,MAX_ENGAGEMENT_CHANNELS)
    if ship_status and ship_status.hit_time:
        ax4.axvline(ship_status.hit_time,color='red',lw=2,ls='-.',alpha=0.8,label=f'피격 t={ship_status.hit_time:.0f}s')
        ax4.legend(fontsize=8,loc='upper right')
    ax4.set_yticks(range(len(gantt_rows))); ax4.set_yticklabels(gantt_rows,fontsize=7)
    ax4.set_xlabel('시간 (초)')
    ax4.set_title('교전 타임라인  (녹색: 요격  빨강: 실패  청록: 기만/회피  회색: 중단  [CIWS N]: 적 CIWS N발 격추)')
    ax4.grid(True,alpha=0.2,axis='x'); ax4.invert_yaxis()

    ax6=fig.add_subplot(gs[1,3]); ax6.axis('off')
    used_info="\n".join([f"{k}: {cfg['inventory'][k]-global_inv.get(k,0)}발"
                         for k in cfg['inventory'] if k!='CIWS-II (Phalanx)' and cfg['inventory'][k]-global_inv.get(k,0)>0])
    ok_evs2=[e for e in all_events if e.is_active and e.intercepted and e.intercept_km]
    dist_s=(f"\n[요격 거리]\n평균 {np.mean([e.intercept_km for e in ok_evs2]):.1f}km\n최근접 {min(e.intercept_km for e in ok_evs2):.1f}km") if ok_evs2 else ""
    decoy_s=(f"\n[기만기]\n{ship_status.decoy_success_count}/{ship_status.decoys_fired}회 성공\n잔여 {ship_status.decoy_stock}발") if ship_status else ""
    ship_s=f"\n[함정] 피격 {ship_status.hit_count}회 전투불능" if (ship_status and not ship_status.operational) else ""
    sd_s=(f"\n[NEW-F 자체방어]\nCIWS격추:{total_ciws_blocks}발\nPk감소:{total_sd_apps}회") if cfg.get('enable_enemy_self_defense',True) else ""
    ax6.text(0.05,0.97,f"[ 비용 & 재고 ]\n\n${total_cost:,}\n({total_cost*1350/1e8:.1f}억원)\n\n[사용량]\n{used_info or '없음'}{dist_s}{decoy_s}{ship_s}{sd_s}\n\n최대채널: {ch_mgr._peak}/{MAX_ENGAGEMENT_CHANNELS}",
             transform=ax6.transAxes,fontsize=8,va='top',bbox=dict(boxstyle='round,pad=0.5',fc='#eaf4fb',ec='steelblue'))
    ax6.set_title('비용 & 재고',fontsize=10,fontweight='bold')

    # ⑦ 속도×고도 2D 산점도 (v6.7: 기존 속도 바차트 교체)
    ax9=fig.add_subplot(gs[2,0:2])
    cat_scatter=ENEMY_DB[cfg['enemy_preset']]['category']
    e_all=[k for k,v in ENEMY_DB.items() if v['category']==cat_scatter]
    sc_colors={'대공':'#e74c3c','대함':'#3498db','대잠':'#2ecc71'}
    for ek in e_all:
        ev_data=ENEMY_DB[ek]
        spd=ev_data.get('speed_ms',0); alt=ev_data.get('altitude_m',0)
        is_cur=(ek==cfg['enemy_preset'])
        ax9.scatter(spd,alt,
                    s=140 if is_cur else 60,
                    color='#f39c12' if is_cur else sc_colors.get(cat_scatter,'#95a5a6'),
                    edgecolors='white' if is_cur else 'none',
                    linewidths=1.5 if is_cur else 0,
                    zorder=5 if is_cur else 3,alpha=0.9 if is_cur else 0.65)
        if is_cur:
            ax9.annotate(ek[:14],(spd,alt),textcoords='offset points',
                         xytext=(6,4),fontsize=7.5,color='#f39c12',fontweight='bold')
    ax9.axvline(cfg.get('weapon_speed_ms',1000),color='steelblue',lw=1.5,
                ls='--',label=f"기준 무기 {cfg.get('weapon_speed_ms',1000)}m/s",alpha=0.8)
    ax9.set_xlabel('속도 (m/s)',fontsize=8); ax9.set_ylabel('고도 (m)',fontsize=8)
    ax9.set_title(f'{cat_scatter} 위협 속도×고도 분포',fontsize=9,fontweight='bold')
    ax9.legend(fontsize=8); ax9.grid(True,alpha=0.2)
    ax9.tick_params(labelsize=7.5)

    ax_sum=fig.add_subplot(gs[2,2:4]); ax_sum.axis('off')
    all_ok=(sum(1 for e in active_events if e.intercepted)==len(active_events)
            and len(active_events)>0 and (not ship_status or ship_status.operational))
    bg_col='#d5f5e3' if all_ok else '#fadbd8'
    result_str=('[전탄요격] 완벽 방어' if all_ok
                else f"[피격] {sum(1 for e in active_events if not e.intercepted)}건 / 함정 {'전투불능' if (ship_status and not ship_status.operational) else '정상'}")
    evasion_evs=[e for e in all_events if e.is_active and e.evasion_count>0]
    summary=(f"[ 핵심 수치 요약 — v6.8.1 ]\n\n"
             f"최종 결과         : {result_str}\n"
             f"전탄 성공률(MC)   : {(mc==1.0).mean()*100:.1f}%\n"
             f"평균 성공률(MC)   : {mc.mean()*100:.1f}%\n"
             f"REQ(요구조건)     : {sum(verdicts)}/{len(verdicts)} 충족\n\n"
             f"음향 기만기       : {ship_status.decoy_success_count if ship_status else 0}/{ship_status.decoys_fired if ship_status else 0}회 성공\n"
             f"적 회피 기동      : {len(evasion_evs)}개 위협 ({sum(e.evasion_count for e in evasion_evs)}회 실시)\n"
             f"[NEW-F] 적 자체방어 : {'ON' if cfg.get('enable_enemy_self_defense',True) else 'OFF'}\n"
             f"  채프·플레어(sdpk): {sdpk:.0%} → Pk감소 {total_sd_apps}회\n"
             f"  적 CIWS 요격     : {civspk:.0%} → {total_ciws_blocks}발 격추\n"
             f"[BUG-1 FIX] 수상함·잠수함 발사 보장\n\n"
             f"최대 허용 C&D     : {max_cd:.1f}s\n"
             f"총 교전 비용      : ${total_cost:,.0f}\n"
             f"최대 동시채널     : {ch_mgr._peak}/{MAX_ENGAGEMENT_CHANNELS}\n\n"
             f"날씨별 비교 (300회)\n"
             +"\n".join([f"  {lbl}: 평균 {res['mean']:.1f}% / 전탄 {res['full_pass']:.1f}%"
                         for lbl,res in sc_results.items()]))
    ax_sum.text(0.05,0.97,summary,transform=ax_sum.transAxes,fontsize=8.5,va='top',
                bbox=dict(boxstyle='round,pad=0.6',fc=bg_col,ec='gray',alpha=0.9))
    ax_sum.set_title('시뮬레이션 핵심 수치',fontsize=10,fontweight='bold')

    img_path='이지스_기동전단_요구조건_분석_v6_8_4.png'
    plt.savefig(img_path,dpi=150,bbox_inches='tight')
    print(f"\n  그래프 저장: '{img_path}'")
    if not return_fig:
        plt.show()
        return img_path
    else:
        return img_path, fig   # 대시보드용: fig 객체 반환


# ════════════════════════════════════════════════════════════════════════════
#  엑셀 보고서 (8개 시트)
# ════════════════════════════════════════════════════════════════════════════
def save_excel_report(cfg, max_cd, mc, min_d, verdicts, details, sc_results,
                      dm_eff, weather_delta, cd_eff, total_cost, global_inv,
                      ch_mgr, all_events, img_path, ship_status=None):
    wb=Workbook()
    tb=Border(**{s:Side(style='thin',color='CCCCCC') for s in ['left','right','top','bottom']})

    def cs(ws,r,c,v,bold=False,bg=None,center=True):
        cell=ws.cell(row=r,column=c,value=v); cell.font=Font(bold=bold,size=10,name='Arial')
        cell.alignment=Alignment(horizontal='center' if center else 'left',vertical='center',wrap_text=True)
        cell.border=tb
        if bg: cell.fill=PatternFill('solid',start_color=bg)

    def title_row(ws,r,t,cols='A:E',bg='1A252F'):
        ws.merge_cells(f'A{r}:{cols.split(":")[1]}{r}')
        c=ws.cell(row=r,column=1,value=t)
        c.font=Font(bold=True,size=13,color='FFFFFF',name='Arial'); c.fill=PatternFill('solid',start_color=bg)
        c.alignment=Alignment(horizontal='center',vertical='center'); ws.row_dimensions[r].height=28

    # Sheet1: RTM
    ws1=wb.active; ws1.title='RTM 요구조건 추적표'; ws1.sheet_view.showGridLines=False
    for col,w in zip('ABCDE',[10,22,30,10,46]): ws1.column_dimensions[col].width=w
    title_row(ws1,1,f'정조대왕급 v6.0 — {cfg["enemy_preset"]} 대응 RTM')
    for j,h in enumerate(['ID','요구조건','검증 기준','판정','상세'],1):
        c=ws1.cell(row=2,column=j,value=h); c.font=Font(bold=True,size=10,color='FFFFFF',name='Arial')
        c.fill=PatternFill('solid',start_color='2C3E50'); c.alignment=Alignment(horizontal='center',vertical='center'); c.border=tb
    for i,(req,v,d) in enumerate(zip(REQ_ITEMS,verdicts,details)):
        bg='D5F5E3' if v else 'FADBD8'
        cs(ws1,i+3,1,req['id'],bold=True,bg=bg); cs(ws1,i+3,2,req['name'],bg=bg,center=False)
        cs(ws1,i+3,3,req['desc'],bg=bg,center=False); cs(ws1,i+3,4,'PASS' if v else 'FAIL',bold=True,bg='2ECC71' if v else 'E74C3C')
        cs(ws1,i+3,5,d,bg=bg,center=False)

    # Sheet2: 교전 상황 서술
    ws2=wb.create_sheet('교전 상황 서술'); ws2.sheet_view.showGridLines=False
    for col,w in zip('ABCDEFGHI',[10,26,13,16,22,10,10,14,14]): ws2.column_dimensions[col].width=w
    title_row(ws2,1,'교전 상황 서술 — v6.8.1 (BUG-1수정 + NEW-F 적 자체방어)',cols='A:I')
    for j,h in enumerate(['ID','위협명','탐지(km)','요격(km)','사용무기','특수플래그','회피횟수','CIWS격추','결과'],1):
        c=ws2.cell(row=2,column=j,value=h); c.font=Font(bold=True,size=10,color='FFFFFF',name='Arial')
        c.fill=PatternFill('solid',start_color='2C3E50'); c.alignment=Alignment(horizontal='center',vertical='center'); c.border=tb
    for i,ev in enumerate(e for e in all_events if e.is_active):
        if ev.enemy_info.get('category')=='어뢰': result_str='기만/회피 성공' if ev.intercepted else '어뢰 명중'; bg='D5EFE3' if ev.intercepted else 'FADBD8'
        elif ev.intercepted: result_str='요격 성공'; bg='D5F5E3'
        else: result_str='피격'; bg='FADBD8'
        flag=('HGV(극초음속)' if ev.enemy_info.get('is_hgv') else 'QBM(저고도기동)' if ev.enemy_info.get('is_qbm') else '-')
        cs(ws2,i+3,1,ev.uid,bold=True,bg=bg); cs(ws2,i+3,2,ev.label[:24],bg=bg,center=False)
        cs(ws2,i+3,3,f"{ev.detect_m/1000:.1f}",bg=bg); cs(ws2,i+3,4,f"{ev.intercept_km:.1f}" if ev.intercept_km else '-',bg=bg)
        cs(ws2,i+3,5,ev.intercept_weapon or '-',bg=bg,center=False); cs(ws2,i+3,6,flag,bg=bg)
        cs(ws2,i+3,7,ev.evasion_count,bg=bg); cs(ws2,i+3,8,ev.enemy_ciws_blocks,bg=bg)
        cs(ws2,i+3,9,result_str,bold=True,bg='2ECC71' if ev.intercepted else 'FFC300' if ev.enemy_info.get('category')=='어뢰' else 'E74C3C')

    # Sheet3: 교전 로그
    ws3=wb.create_sheet('교전 타임라인 로그'); ws3.sheet_view.showGridLines=False
    for col,w in zip('ABCDE',[10,12,26,8,60]): ws3.column_dimensions[col].width=w
    title_row(ws3,1,'타임라인 교전 로그 (v6.8.1 — BUG-1수정 + NEW-F 적자체방어)',cols='A:E')
    for j,h in enumerate(['시각(s)','ID','위협명','아이콘','메시지'],1):
        c=ws3.cell(row=2,column=j,value=h); c.font=Font(bold=True,size=10,color='FFFFFF',name='Arial')
        c.fill=PatternFill('solid',start_color='2C3E50'); c.alignment=Alignment(horizontal='center',vertical='center'); c.border=tb
    for i,e in enumerate(sorted([e for ev in all_events for e in ev.log],key=lambda x:x['t'])):
        bg=('D5F5E3' if 'OK' in e['msg'] or '성공' in e['msg'] else
            'FADBD8' if any(w in e['msg'] for w in ['피격','NG','명중','CIWS 격추']) else
            'FEF9E7' if 'NEW-F' in e['msg'] or '자체방어' in e['msg'] else 'FDFEFE')
        cs(ws3,i+3,1,f"{e['t']:.0f}",bg=bg); cs(ws3,i+3,2,e['uid'],bg=bg)
        cs(ws3,i+3,3,e['label'][:24],bg=bg,center=False); cs(ws3,i+3,4,e['icon'],bg=bg); cs(ws3,i+3,5,e['msg'],bg=bg,center=False)

    # Sheet4: 시뮬레이션 설정
    ws4=wb.create_sheet('시뮬레이션 설정'); ws4.sheet_view.showGridLines=False
    for col,w in zip('ABC',[34,32,22]): ws4.column_dimensions[col].width=w
    title_row(ws4,1,'시뮬레이션 입력 파라미터 (v6.8.1)',cols='A:C')
    enemy=ENEMY_DB[cfg['enemy_preset']]
    total_ciws_blocks2=sum(ev.enemy_ciws_blocks for ev in all_events)
    total_sd_apps2    =sum(ev.enemy_self_def_apps for ev in all_events)
    params=[
        ('적 위협 프리셋',cfg['enemy_preset'],''),
        ('적 속도',cfg['enemy_speed_ms'],'m/s'),
        ('유효 탐지거리',f"{dm_eff/1000:.1f}",'km'),
        ('전투 모드',cfg['combat_mode'],''),
        ('REQ 기준 무기',cfg.get('req_weapon_name',''),'TEWA 실제 선택'),
        ('날씨',cfg['weather'],''),
        ('위협 수',cfg['num_threats'],'개'),
        ('C&D 시간',cfg['cd_time_s'],'s'),
        ('── BUG-1 수정 (v6.8.1) ──','',''),
        ('수상함·잠수함 발사 보장','fire_m = min(desired, dm×0.90)','항상 적용'),
        ('── NEW-C: 다발 발사 설정 ──','',''),
        ('발사 모드',cfg.get('missile_salvo_mode','RANDOM'),'RANDOM/FIXED/MAX'),
        ('고정 발사 수',cfg.get('missile_salvo_fixed',2),'FIXED 모드 시'),
        ('── NEW-B: 기만기 설정 ──','',''),
        ('음향 기만기 재고',cfg.get('decoy_stock',4),'발 (AN/SLQ-25 기준)'),
        ('기만기 성공 확률',f"{DECOY_PK*100:.0f}%",'실제 시뮬레이션 값'),
        ('── NEW-F: 적 자체방어 (v6.8.1) ──','',''),
        ('자체방어 활성화','ON' if cfg.get('enable_enemy_self_defense',True) else 'OFF',''),
        ('채프·플레어(self_defense_pk)',f"{enemy.get('self_defense_pk',0):.0%}",'Pk 감소 계수'),
        ('적 CIWS 요격(enemy_ciws_pk)',f"{enemy.get('enemy_ciws_pk',0):.0%}",'수상함 전용'),
        ('── 교전 결과 (NEW-F 통계) ──','',''),
        ('적 CIWS 격추',f"{total_ciws_blocks2}발",'아군 미사일 격추됨'),
        ('채프·플레어 Pk감소 적용',f"{total_sd_apps2}회",''),
        ('── 기타 계산 결과 ──','',''),
        ('최대 허용 C&D',f"{max_cd:.1f}",'s [사거리반영]'),
        ('전탄 성공률',f"{(mc==1.0).mean()*100:.1f}%",''),
        ('총 교전 비용',f"${total_cost:,}",''),
    ]
    for i,(k,v,u) in enumerate(params):
        if '──' in k:
            ws4.merge_cells(f'A{i+2}:C{i+2}'); c=ws4.cell(row=i+2,column=1,value=k)
            c.font=Font(bold=True,color='FFFFFF',name='Arial')
            bg_color=('154360' if 'NEW-F' in k else '2C3E50')
            c.fill=PatternFill('solid',start_color=bg_color)
            c.alignment=Alignment(horizontal='center',vertical='center'); c.border=tb
        else:
            cs(ws4,i+2,1,k,bold=True,bg='EBF5FB',center=False)
            cs(ws4,i+2,2,v,bg='FDFEFE',center=False)
            cs(ws4,i+2,3,u,bg='FDFEFE')

    # Sheet5: 몬테카를로 통계
    ws5=wb.create_sheet('몬테카를로 통계'); ws5.sheet_view.showGridLines=False
    for col,w in zip('ABCDE',[22,16,16,16,16]): ws5.column_dimensions[col].width=w
    title_row(ws5,1,f'몬테카를로(Monte Carlo) 1000회 통계 — {cfg["weather"]}',cols='A:E')
    for j,h in enumerate(['항목','값','단위','기준','판정'],1):
        c=ws5.cell(row=2,column=j,value=h); c.font=Font(bold=True,size=10,color='FFFFFF',name='Arial')
        c.fill=PatternFill('solid',start_color='2C3E50'); c.alignment=Alignment(horizontal='center',vertical='center'); c.border=tb
    mc_full=(mc==1.0).mean()*100
    for i,(nm,val,unit,crit,jdg) in enumerate([
        ('전탄 요격 성공률',f"{mc_full:.1f}",'%','>= 90%','PASS' if mc_full>=90 else 'FAIL'),
        ('평균 요격 성공률',f"{mc.mean()*100:.1f}",'%','참고','-'),
        ('표준편차',f"{mc.std()*100:.1f}",'%p','참고','-'),
        ('10 퍼센타일',f"{float(np.percentile(mc,10)*100):.1f}",'%','참고','-'),
        ('90 퍼센타일',f"{float(np.percentile(mc,90)*100):.1f}",'%','참고','-'),
        ('시뮬레이션 횟수','1000','회','-','-'),
    ]):
        row=i+3; bg=('D5F5E3' if jdg=='PASS' else 'FADBD8' if jdg=='FAIL' else 'FDFEFE')
        cs(ws5,row,1,nm,bold=True,bg=bg,center=False); cs(ws5,row,2,val,bg=bg)
        cs(ws5,row,3,unit,bg=bg); cs(ws5,row,4,crit,bg=bg)
        cs(ws5,row,5,jdg,bold=(jdg in['PASS','FAIL']),bg='2ECC71' if jdg=='PASS' else 'E74C3C' if jdg=='FAIL' else bg)

    # Sheet6: 시나리오 비교
    ws6=wb.create_sheet('시나리오 비교'); ws6.sheet_view.showGridLines=False
    for col,w in zip('ABCDE',[18,18,18,18,12]): ws6.column_dimensions[col].width=w
    title_row(ws6,1,'날씨별 시나리오 비교 — 각 300회 (v6.8.1)',cols='A:E')
    for j,h in enumerate(['날씨 시나리오','평균 성공률(%)','전탄 성공률(%)','표준편차(%p)','판정'],1):
        c=ws6.cell(row=2,column=j,value=h); c.font=Font(bold=True,size=10,color='FFFFFF',name='Arial')
        c.fill=PatternFill('solid',start_color='2C3E50'); c.alignment=Alignment(horizontal='center',vertical='center'); c.border=tb
    for i,(label,res) in enumerate(sc_results.items()):
        mc_arr=res.get('mc_array',np.array([res['mean']/100])); std=mc_arr.std()*100; fp=res['full_pass']
        bg='D5F5E3' if fp>=90 else 'FFF9C4' if fp>=70 else 'FADBD8'
        cs(ws6,i+3,1,label,bold=True,bg=bg,center=False); cs(ws6,i+3,2,f"{res['mean']:.1f}",bg=bg)
        cs(ws6,i+3,3,f"{fp:.1f}",bg=bg); cs(ws6,i+3,4,f"{std:.1f}",bg=bg)
        cs(ws6,i+3,5,'PASS' if fp>=90 else 'FAIL',bold=True,bg='2ECC71' if fp>=90 else 'E74C3C')

    # Sheet7: 무기 재고 및 비용
    ws7=wb.create_sheet('무기 재고 및 비용'); ws7.sheet_view.showGridLines=False
    for col,w in zip('ABCDEFG',[20,12,12,16,16,16,12]): ws7.column_dimensions[col].width=w
    title_row(ws7,1,'무기 재고 및 교전 비용 상세 (v6.8.1)',cols='A:G')
    for j,h in enumerate(['무기명','초기재고','잔여재고','사용량','단가(USD)','소계(USD)','비고'],1):
        c=ws7.cell(row=2,column=j,value=h); c.font=Font(bold=True,size=10,color='FFFFFF',name='Arial')
        c.fill=PatternFill('solid',start_color='2C3E50'); c.alignment=Alignment(horizontal='center',vertical='center'); c.border=tb
    grand_total=0
    for i,(wn,ini) in enumerate(cfg['inventory'].items()):
        if wn=='CIWS-II (Phalanx)':
            used_cnt=sum(1 for ev in all_events for wpn in ev.used_weapons if wpn==wn)
            cost_sub=used_cnt*CIWS_BURST_COST_USD; note=f"점사 {used_cnt}회"
        else:
            used_cnt=ini-global_inv.get(wn,0); cost_sub=used_cnt*FRIENDLY_DB[wn]['cost_usd']; note=''
        grand_total+=cost_sub; bg='FDFEFE' if used_cnt==0 else 'FFF9C4'
        cs(ws7,i+3,1,wn,bold=True,bg=bg,center=False); cs(ws7,i+3,2,ini if wn!='CIWS-II (Phalanx)' else '-',bg=bg)
        cs(ws7,i+3,3,global_inv.get(wn,ini) if wn!='CIWS-II (Phalanx)' else '-',bg=bg)
        cs(ws7,i+3,4,used_cnt if wn!='CIWS-II (Phalanx)' else '-',bg=bg)
        cs(ws7,i+3,5,f"${FRIENDLY_DB[wn]['cost_usd']:,}",bg=bg,center=False)
        cs(ws7,i+3,6,f"${cost_sub:,}",bg=bg,center=False); cs(ws7,i+3,7,note,bg=bg,center=False)
    last=len(cfg['inventory'])+3; ws7.merge_cells(f'A{last}:E{last}')
    c=ws7.cell(row=last,column=1,value='총 교전 비용'); c.font=Font(bold=True,size=11,name='Arial')
    c.fill=PatternFill('solid',start_color='2C3E50'); c.alignment=Alignment(horizontal='right',vertical='center'); c.border=tb
    cs(ws7,last,6,f"${grand_total:,}",bold=True,bg='FCF3CF'); cs(ws7,last,7,f"약 {grand_total*1350/1e8:.1f}억원",bg='FCF3CF',center=False)

    # Sheet8: 그래프 이미지
    if os.path.exists(img_path) and _CAN_IMG:
        try:
            ws8=wb.create_sheet('종합 그래프'); ws8.sheet_view.showGridLines=False
            title_row(ws8,1,'시뮬레이션 종합 분석 그래프 v6.1',cols='A:N')
            img=XLImage(img_path); img.anchor='A2'; img.width=1400; img.height=950; ws8.add_image(img)
        except Exception as e:
            print(f"  [경고] 이미지 삽입 실패: {e}")
    elif not _CAN_IMG:
        print("  [안내] pillow 미설치 → 엑셀 이미지 생략 (pip install pillow)")

    mc_logs=getattr(mc,'mc_sample_logs',[])
    if mc_logs:
        ws9=wb.create_sheet('MC 샘플 로그'); ws9.sheet_view.showGridLines=False
        for col,ww in zip('ABCDE',[10,12,26,8,60]): ws9.column_dimensions[col].width=ww
        title_row(ws9,1,f'MC 샘플 로그 (save_nth={cfg.get("mc_save_nth",0)}회차)',cols='A:E')
        for j,h in enumerate(['시각(s)','ID','위협명','아이콘','메시지'],1):
            c=ws9.cell(row=2,column=j,value=h)
            c.font=Font(bold=True,size=10,color='FFFFFF',name='Arial')
            c.fill=PatternFill('solid',start_color='2C3E50')
            c.alignment=Alignment(horizontal='center',vertical='center'); c.border=tb
        for i,e in enumerate(mc_logs[:500]):
            bg=('D5F5E3' if 'OK' in e.get('msg','') or '성공' in e.get('msg','')
                else 'FADBD8' if any(w in e.get('msg','') for w in ['피격','NG','명중'])
                else 'FDFEFE')
            cs(ws9,i+3,1,f"{e['t']:.0f}",bg=bg); cs(ws9,i+3,2,e.get('uid',''),bg=bg)
            cs(ws9,i+3,3,e.get('label','')[:24],bg=bg,center=False)
            cs(ws9,i+3,4,e.get('icon',''),bg=bg); cs(ws9,i+3,5,e.get('msg',''),bg=bg,center=False)

    xlsx_path='이지스_기동전단_요구조건_보고서_v6_8_4.xlsx'
    wb.save(xlsx_path); print(f"  엑셀 보고서 저장: '{xlsx_path}'")


# ════════════════════════════════════════════════════════════════════════════
#
#  ██╗   ██╗███████╗███████╗██████╗      ██████╗███████╗ █████╗
#  ██║   ██║██╔════╝██╔════╝██╔══██╗    ██╔════╝██╔════╝██╔══██╗
#  ██║   ██║███████╗█████╗  ██████╔╝    ██║     █████╗  ███████║
#  ██║   ██║╚════██║██╔══╝  ██╔══██╗    ██║     ██╔══╝  ██╔══██║
#  ╚██████╔╝███████║███████╗██║  ██║    ╚██████╗██║     ██║  ██║
#
#  ★★★ 사용자 설정 구역 ★★★
#  이 구역만 수정하면 됩니다. 절대 삭제 금지.
#  아래 각 항목의 주석에서 선택 가능한 값 목록을 확인하고 원하는 값으로 변경하세요.
#
# ════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":


    # ╔═════════════════════════════════════════════════════════════════════
    # ║  [설정 1]  적군 위협 프리셋
    # ╟─────────────────────────────────────────────────────────────────────
    # ║  시뮬레이션할 적 플랫폼을 아래 32종 중 하나의 이름을 정확히 복사해
    # ║  enemy_preset_name 에 붙여넣으세요.
    # ║
    # ║  ── 대공위협 : 전투기 / 전폭기 (11종) ───────────────────────────
    # ║
    # ║  'MiG-29 (풀크럼)'
    # ║      속도 765 m/s | 고도 10,000 m | 탐지 ~244 km
    # ║      미사일 : YJ-91 초음속 대함미사일 1~2발 | 채프 자체방어 10%
    # ║      특징 : 구소련제 주력 전투기, 북한·시리아 등 운용
    # ║
    # ║  'MiG-23 (플로거)'
    # ║      속도 797 m/s | 고도 10,000 m | 탐지 ~259 km
    # ║      미사일 : YJ-83K 주력 대함미사일 1~2발 | 채프 자체방어 8%
    # ║      특징 : 가변익 전투기, 현존 최고령 플랫폼
    # ║
    # ║  'J-7 (섬광)'
    # ║      속도 680 m/s | 고도 10,000 m | 탐지 ~218 km
    # ║      미사일 : YJ-8K 대함미사일 1발(고정) | 채프 자체방어 5%
    # ║      특징 : 구형 경전투기, 낮은 위협도, 소진재고로 테스트에 적합
    # ║
    # ║  'J-10A (비맹)'
    # ║      속도 700 m/s | 고도 16,000 m | 탐지 ~193 km
    # ║      미사일 : YJ-91 대함미사일 1~2발 | 채프 자체방어 12%
    # ║      특징 : 중국 독자개발 4세대+, 고고도 침투 능력
    # ║
    # ║  'J-11B (플랭커-B)'
    # ║      속도 830 m/s | 고도 19,000 m | 탐지 ~350 km
    # ║      미사일 : YJ-83K 2~4발 (포화 공격 가능) | 채프 자체방어 12%
    # ║      특징 : Su-27 개량형, 장거리 대함 작전 핵심
    # ║
    # ║  'J-15 (비상어)'
    # ║      속도 750 m/s | 고도 15,000 m | 탐지 ~315 km
    # ║      미사일 : YJ-83K 2~4발 | 채프 자체방어 12%
    # ║      특징 : 항공모함 탑재 전투기, 랴오닝·산둥함 운용
    # ║
    # ║  'J-16 (플랭커-D)'
    # ║      속도 780 m/s | 고도 17,000 m | 탐지 ~315 km
    # ║      미사일 : YJ-12 초음속 2~4발 | 채프 자체방어 15%
    # ║      특징 : 쌍발 다목적 공격기, 장거리 타격 최강
    # ║
    # ║  'J-20 (위룡)'         ⭐ 스텔스 — 탐지거리 극히 짧음 (~67 km)
    # ║      속도 750 m/s | 고도 20,000 m | 탐지 ~67 km (RCS 0.001 ㎡)
    # ║      미사일 : YJ-12 1~4발 | ECM 자체방어 18% (5세대 최고)
    # ║      특징 : 탐지거리 극히 짧아 C&D 시간 부족 → CIWS 최후 방어 시험
    # ║
    # ║  'Su-35 (플랭커-E)'
    # ║      속도 830 m/s | 고도 18,000 m | 탐지 ~238 km
    # ║      미사일 : Kh-31A 1~2발 | 채프+ECM 자체방어 15%
    # ║      특징 : 러시아제 4.5세대, 고기동+강력한 레이더
    # ║
    # ║  'JH-7A (날치)'
    # ║      속도 500 m/s | 고도 15,200 m | 탐지 ~259 km
    # ║      미사일 : YJ-91 2~4발 | 채프 자체방어 10%
    # ║      특징 : 전폭기 계열, 속도 느리나 다발 발사 위협
    # ║
    # ║  'H-6 (폭격기)'
    # ║      속도 290 m/s | 고도 12,000 m | 탐지 ~630 km (RCS 40 ㎡)
    # ║      미사일 : YJ-12 4~6발 (최다 동시 발사) | 채프 자체방어 8%
    # ║      특징 : 느리지만 포화공격 6발, 채널 포화 시험에 최적
    # ║
    # ║  ── 대공위협 : 탄도미사일 / 특수 (6종) ─────────────────────────
    # ║
    # ║  'DF-11A (단거리 탄도)'
    # ║      속도 1,500 m/s | 최고고도 50 km | 사거리 300 km
    # ║      특징 : 가장 느린 탄도미사일, SM-6/SM-2로 요격 가능
    # ║
    # ║  'DF-15 (단거리 탄도)'
    # ║      속도 2,000 m/s | 최고고도 80 km | 사거리 600 km
    # ║      특징 : 준중거리, SM-3/SM-6 혼용 요격 테스트
    # ║
    # ║  'DF-21D (대함 탄도)'
    # ║      속도 3,400 m/s | 최고고도 150 km | 사거리 1,500 km
    # ║      특징 : 항모 킬러, SM-3 외 요격 어려움
    # ║
    # ║  'DF-26 (중장거리 탄도)'
    # ║      속도 6,000 m/s | 최고고도 300 km | 사거리 4,000 km
    # ║      특징 : 최고속 탄도 위협, SM-3 Pk 크게 저하됨
    # ║
    # ║  'DF-17 (극초음속 활공)'    ⭐ HGV 특수처리
    # ║      속도 2,000 m/s | 고도 60 km | 사거리 2,500 km
    # ║      특징 : SM-3만 교전 가능(Pk 25%), 나머지 무기 무력화
    # ║
    # ║  'KN-23 (북한 이스칸데르)'  ⭐ QBM 특수처리
    # ║      속도 600 m/s | 고도 2,000 m | 사거리 700 km
    # ║      특징 : 저고도 기동탄도 → SM-3 무력화(Pk 15%), SM-6 우선
    # ║
    # ║  ── 대공위협 : 순항미사일 (5종) ────────────────────────────────
    # ║
    # ║  'CJ-10 (순항미사일)'
    # ║      속도 270 m/s | 고도 10 m | 사거리 1,500 km | 탐지 ~36 km
    # ║      특징 : 저고도 침투, 탐지 어려움, 가장 긴 사거리
    # ║
    # ║  'YJ-12 (초음속 순항)'
    # ║      속도 1,000 m/s | 고도 15 m | 사거리 400 km | 탐지 ~51 km
    # ║      특징 : 초음속+저고도, 종말회피 0.72로 요격 난이도 높음
    # ║
    # ║  'P-800 오닉스 (야혼트)'
    # ║      속도 750 m/s | 고도 15 m | 사거리 300 km | 탐지 ~52 km
    # ║      특징 : 러시아제, 아음속~초음속 전환, 종말회피 0.75
    # ║
    # ║  'Kh-31A (항공기발사 대함)'
    # ║      속도 1,000 m/s | 고도 20 m | 사거리 70 km | 탐지 ~54 km
    # ║      특징 : 항공기 발사, 종말회피 0.68로 전 순항미사일 중 최강
    # ║
    # ║  'YJ-100 (장거리 순항)'
    # ║      속도 300 m/s | 고도 10 m | 사거리 800 km | 탐지 ~36 km
    # ║      특징 : 장거리 저고도, CJ-10과 유사하나 속도 소폭 상승
    # ║
    # ║  ── 대함위협 : 수상함 (5종) — NEW-F 자체방어 강력 ──────────────
    # ║
    # ║  '022형 미사일 고속정'
    # ║      속도 22 m/s | 탐지 ~45 km | 미사일 YJ-83 4~8발
    # ║      자체방어 : 채프 15% + CIWS 12% | 특징 : 고속 포화 공격
    # ║
    # ║  '056형 초계함'
    # ║      속도 14 m/s | 탐지 ~45 km | 미사일 YJ-83 2~4발
    # ║      자체방어 : 채프 20% + CIWS 15% | 특징 : 중형 수상함 기준
    # ║
    # ║  '054A형 호위함'
    # ║      속도 14 m/s | 탐지 ~45 km | 미사일 YJ-83 4~8발
    # ║      자체방어 : 채프 28% + CIWS 22% | 특징 : 중국 주력 호위함
    # ║
    # ║  '052D형 구축함'
    # ║      속도 15 m/s | 탐지 ~45 km | 미사일 YJ-18 4~8발
    # ║      자체방어 : 채프 32% + CIWS 28% | 특징 : HHQ-9B VLS 64셀
    # ║
    # ║  '055형 대형 구축함'     ⭐ 중국 최강 자체방어
    # ║      속도 17 m/s | 탐지 ~45 km | 미사일 YJ-18 6~12발
    # ║      자체방어 : 채프 38% + CIWS 33% | 특징 : 1130 CIWS×2, 112셀
    # ║
    # ║  ── 대잠위협 : 잠수함 (5종) ────────────────────────────────────
    # ║  ※ BUG-1 수정(v6.8.1)으로 잠수함도 이제 정상적으로 어뢰 발사됨
    # ║
    # ║  '039형 잠수함 (송급)'
    # ║      속도 11 m/s | 잠항 -250 m | 어뢰 Yu-6 2~4발
    # ║      소음기동 자체방어 5% | 특징 : 구형 재래식, 기본 운용
    # ║
    # ║  '041형 잠수함 (위안급 개량)'
    # ║      속도 12 m/s | 잠항 -280 m | 어뢰 Yu-6 2~4발
    # ║      소음기동 자체방어 5% | 특징 : AIP 추진, 저소음 개량형
    # ║
    # ║  '093형 잠수함 (위안급)'
    # ║      속도 15 m/s | 잠항 -350 m | 어뢰+미사일 2~6발
    # ║      소음기동 자체방어 5% | 특징 : 어뢰+잠대함 미사일 혼용
    # ║
    # ║  '094형 잠수함 (진급)'     ⭐ SSBN 탄도미사일
    # ║      속도 12 m/s | 잠항 -400 m | SLBM JL-2 1~2발
    # ║      소음기동 자체방어 5% | 특징 : 전략 핵잠수함, SM-3 필수
    # ║
    # ╚═════════════════════════════════════════════════════════════════════
    enemy_preset_name = 'MiG-23 (플로거)'   # ← 위 목록에서 선택하여 교체하세요


    # ╔═════════════════════════════════════════════════════════════════════
    # ║  [설정 1-1]  적 미사일 발사 여부
    # ╟─────────────────────────────────────────────────────────────────────
    # ║  적 플랫폼이 함정을 향해 미사일 또는 어뢰를 발사할지 결정합니다.
    # ║
    # ║  True  → 적이 접근하면서 미사일/어뢰를 발사 (실전 환경, 권장)
    # ║           아군은 플랫폼과 미사일을 동시에 상대해야 함
    # ║  False → 플랫폼 자체만 위협 (미사일 없이 돌진)
    # ║           단순 방어 테스트 또는 탐지 거리 검증 시 사용
    # ╚═════════════════════════════════════════════════════════════════════
    enemy_fires_missile = True   # True / False


    # ╔═════════════════════════════════════════════════════════════════════
    # ║  [설정 1-2]  다발 발사 모드 (NEW-C)
    # ╟─────────────────────────────────────────────────────────────────────
    # ║  적이 한 번의 공격에 몇 발을 발사할지 결정합니다.
    # ║  각 플랫폼은 ENEMY_DB에 missile_salvo_min / max 가 내장되어 있습니다
    # ║
    # ║  'RANDOM' → 플랫폼별 최솟값~최댓값 사이 무작위 발사 (권장)
    # ║              예) H-6 폭격기: 4~6발 중 랜덤
    # ║  'FIXED'  → missile_salvo_fixed 에 지정한 수량으로 고정 발사
    # ║              모든 플랫폼이 동일한 수를 발사 (비교 시험 용도)
    # ║  'MAX'    → 각 플랫폼의 최대 발사 수량으로 고정
    # ║              최악의 포화공격 시나리오 시뮬레이션
    # ╚═════════════════════════════════════════════════════════════════════
    missile_salvo_mode  = 'RANDOM'   # 'RANDOM' / 'FIXED' / 'MAX'
    missile_salvo_fixed = 2          # FIXED 모드일 때만 사용 (정수)


    # ╔═════════════════════════════════════════════════════════════════════
    # ║  [설정 1-3]  전술 기능 ON/OFF
    # ╟─────────────────────────────────────────────────────────────────────
    # ║
    # ║  enable_enemy_evasion (NEW-E: 적 회피 기동)
    # ║    True  → 요격 실패 시 적이 속도 증가 + 고도/수심 변경 (권장)
    # ║    False → 적이 일직선으로만 접근 (단순화 시험)
    # ║
    # ║  enable_missile_evasion (NEW-D: 미사일 종말 회피)
    # ║    True  → 아군 미사일이 20 km 이내 진입 시 Pk 감소 (권장)
    # ║    False → 종말 회피 없음 (낙관적 시나리오)
    # ║
    # ║  enable_acoustic_decoy (NEW-B: 음향 기만기 AN/SLQ-25 Nixie)
    # ║    True  → 어뢰 탐지 시 기만기 자동 전개, 성공률 60% (권장)
    # ║    False → 기만기 미사용 (함정 회피 기동만 작동)
    # ║
    # ║  enable_ship_torpedo_evasion (함정 회피 기동)
    # ║    True  → 기만기 실패 후 2차 회피 기동, 성공률 30% (권장)
    # ║    False → 기만기만으로 방어 (회피 기동 없음)
    # ║
    # ║  decoy_stock (기만기 초기 재고)
    # ║    실제 AN/SLQ-25 Nixie 기준 탑재 수: 4발
    # ║    권장 범위: 2 ~ 8 | 최소 1, 0 이면 기만기 없이 시작
    # ╚═════════════════════════════════════════════════════════════════════
    enable_enemy_evasion        = True   # True / False
    enable_missile_evasion      = True   # True / False
    enable_acoustic_decoy       = True   # True / False
    enable_ship_torpedo_evasion = True   # True / False
    decoy_stock                 = 4      # 정수 (AN/SLQ-25 기준 4발)


    # ╔═════════════════════════════════════════════════════════════════════
    # ║  [설정 1-4]  NEW-F: 적 자체 방어 시스템 (v6.8.1 신규)
    # ╟─────────────────────────────────────────────────────────────────────
    # ║  적 플랫폼이 아군 미사일에 대해 자체 방어를 수행합니다.
    # ║
    # ║  True  → 적 자체방어 활성화 (권장, 현실적 교전 환경)
    # ║    간단 방식 — self_defense_pk (채프·플레어·ECM 발동)
    # ║      아군 미사일의 effective_pk = pk × (1 - self_defense_pk)
    # ║      예: Pk=0.90, sdpk=0.15 → effective_pk=0.765 로 감소
    # ║    중간 방식 — enemy_ciws_pk (수상함 CIWS 요격)
    # ║      아군 미사일 1발당 CIWS 요격 판정 → 성공 시 해당 발 즉시 격추
    # ║      예: CIWS=0.28 → 아군 미사일 28% 확률로 격추됨
    # ║
    # ║  False → 자체방어 비활성화 (v5.14 이하와 동일한 결과)
    # ║
    # ║  ※ 수치는 ENEMY_DB에 플랫폼별로 내장, 별도 수정 불필요
    # ║  ※ 수상함 위협 선택 시 CIWS 격추로 인해 소모 발수가 크게 증가함
    # ╚═════════════════════════════════════════════════════════════════════
    enable_enemy_self_defense = True

    # ╔══[ 설정 1-5 ]  NEW-G: ECM 재밍 (v5.16.1)
    # ║  True  → 거리 반비례 ECM (50km 기준, Pk 최대 50% 감소)
    # ║  False → ECM 비활성화
    # ╚════════════════════════════════════════════
    enable_ecm = True

    # ╔══[ 설정 1-6 ]  NEW-H: 함재 헬기 (v5.16.1, 대잠 전용)
    # ║  enable_helo  True → 잠수함 탐지 시 자동 출격
    # ║  helo_preset  'AW-159 와일드캣' (on_deck=True, 기본 탑재)
    # ║               'MH-60R 시호크'   (on_deck=False, 코드 수정 필요)
    # ║  mc_save_nth  0=사용안함 / 1~1000=해당 MC 회차 로그 Sheet9 저장
    # ╚════════════════════════════════════════════
    enable_helo  = False
    helo_preset  = 'AW-159 와일드캣'

    # ╔══[ 설정 1-7 ]  NEW-I: P-3C 오라이온 해상초계기 (v6.1)
    # ║  enable_p3c  True  → 대잠 시나리오에서 P-3C 출격
    # ║              포항기지 출격, 풍랑에서도 운용 가능
    # ║              헬기 사거리 밖 잠수함 공격 가능
    # ║  p3c_preset  'P-3C 오라이온' (현재 지원 기종)
    # ╚════════════════════════════════════════════════

    # ╔══[ 설정 1-8 ]  NEW-J: P-8A 포세이돈 해상초계기 (v6.2)
    # ║  enable_p8a  True  → 대잠 시나리오에서 P-8A 출격
    # ║              P-3C 후속, 포항기지 출격
    # ║              준비 30분 (P-3C보다 10분 빠름)
    # ║              Mk.46 경어뢰 5발 탑재
    # ║              소노부이 탐지 보너스 +18km (P-3C +15km보다 우수)
    # ║              태풍 외 전천후 운용 가능 (P-3C와 동일)
    # ╚════════════════════════════════════════════════
    enable_p3c   = False
    p3c_preset   = 'P-3C 오라이온'
    enable_p8a   = False
    p8a_preset   = 'P-8A 포세이돈'

    # ╔══[ 설정 1-9 ]  NEW-K: 아군 편대 모드 (v6.3)
    # ║  enable_fleet  False → 단일 함정 (기존 방식)
    # ║                True  → 편대 모드
    # ║  fleet_mode    'preset'  → fleet_preset 프리셋 사용
    # ║                'custom' → fleet_custom_ships 직접 지정
    # ║  fleet_preset  '단독 작전' / '기동전단 기본' / 'BMD 중점'
    # ║                '대잠 중점' / '최대 편대'
    # ║  fleet_custom_ships (커스텀 예시):
    # ║    [{'name':'정조대왕함','type':'KDX-III'},
    # ║     {'name':'충무공이순신함','type':'KDX-II'}]
    # ╚════════════════════════════════════════════════════════════════
    enable_fleet      = False
    fleet_mode        = 'preset'         # 'preset' 또는 'custom'
    fleet_preset      = '기동전단 기본'
    fleet_custom_ships= [                # fleet_mode='custom' 시 사용
        {'name': '정조대왕함',     'type': 'KDX-III'},
        {'name': '충무공이순신함', 'type': 'KDX-II'},
    ]

    # ╔══[ 설정 1-10 ]  NEW-L: 적군 편대 모드 (v6.4)
    # ║  enemy_fleet_mode  'single'  → 기존 단일 적군 방식 (기본)
    # ║                    'preset'  → PLA 교리 프리셋 5종
    # ║                    'custom'  → 직접 구성
    # ║                    'random'  → 난이도 기반 자동 생성
    # ║  enemy_fleet_preset  'A2/AD 항공 포화' / '항모 킬 체인'
    # ║                      '수상함 편대전' / '대잠 복합' / '전면전 포화'
    # ║  enemy_fleet_difficulty  '쉬움' / '보통' / '어려움' / '극한'
    # ║  enemy_fleet_seed  None → 매번 다름 | 숫자 → 재현 가능
    # ║  enemy_fleet_custom (커스텀 예시):
    # ║    [{'preset':'J-20 (위룡)','count':2},
    # ║     {'preset':'DF-17 (극초음속 활공)','count':1}]
    # ╚════════════════════════════════════════════════════════════════
    # ╔══[ 설정 1-11 ]  v6.8: 다방위 공격
    # ║  enable_multibearing  False=정면(기존) / True=전방위 랜덤
    # ║  bearing_seed         None=매번 랜덤 | 숫자=재현 가능
    # ╚════════════════════════════════════════════════════════════════
    enable_multibearing = False
    bearing_seed        = None

    # ╔══[ 설정 1-12 ]  v6.8: CEC 사전 동시 배정 (편대 모드 전용)
    # ║  enable_cec_preassign  False=사후 인계(기존) / True=사전 동시 배정
    # ╚════════════════════════════════════════════════════════════════
    enable_cec_preassign = False

    enemy_fleet_mode       = 'single'
    enemy_fleet_preset     = 'A2/AD 항공 포화'
    enemy_fleet_difficulty = '보통'
    enemy_fleet_seed       = None       # None=랜덤 | 숫자=재현
    enemy_fleet_custom     = [
        {'preset': 'J-16 (플랭커-D)', 'count': 2},
        {'preset': 'DF-11A (단거리 탄도)', 'count': 1},
    ]
    mc_save_nth  = 0


    # ╔═════════════════════════════════════════════════════════════════════
    # ║  [설정 2]  커스텀 적 제원 오버라이드
    # ╟─────────────────────────────────────────────────────────────────────
    # ║  ENEMY_DB의 기본 제원 대신 사용자가 직접 속도와 탐지거리를
    # ║  지정하고 싶을 때 사용합니다.
    # ║
    # ║  use_custom_enemy
    # ║    False → enemy_preset_name의 기본 제원 그대로 사용 (권장)
    # ║    True  → custom_enemy_speed / custom_detect_km 값으로 덮어쓰기
    # ║
    # ║  custom_enemy_speed (단위: m/s)
    # ║    적 플랫폼의 접근 속도를 임의로 설정
    # ║    참고: 음속 = 340 m/s | 마하 2 = 680 m/s | 마하 5 = 1700 m/s
    # ║    권장 범위: 50 m/s (잠수함) ~ 6,000 m/s (DF-26 급)
    # ║
    # ║  custom_detect_km (단위: km)
    # ║    레이더 탐지 거리를 임의로 설정
    # ║    권장 범위: 10 km ~ 1,200 km (센서 최대 한계)
    # ╚═════════════════════════════════════════════════════════════════════
    use_custom_enemy   = False   # True / False
    custom_enemy_speed = 3400    # 단위: m/s (use_custom_enemy=True 시 적용)
    custom_detect_km   = 1200    # 단위: km (use_custom_enemy=True 시 적용)


    # ╔═════════════════════════════════════════════════════════════════════
    # ║  [설정 3]  전투 모드
    # ╟─────────────────────────────────────────────────────────────────────
    # ║  아군이 어떤 방식으로 무기를 선택할지 결정합니다.
    # ║
    # ║  'AUTO'   → TEWA(위협평가 및 무기할당) 자동 선택 (권장)
    # ║             위협 유형·거리·재고를 고려해 최적 무기 자동 배정
    # ║             HGV → SM-3만 사용 / QBM → SM-6 우선 / 어뢰 → 홍상어
    # ║
    # ║  'MANUAL' → friendly_preset_name(설정 4)의 무기만 강제 사용
    # ║             단일 무기의 단독 요격 성능 검증 시 사용
    # ║             해당 무기 사거리/카테고리 범위를 벗어나면 교전 불가
    # ╚═════════════════════════════════════════════════════════════════════
    combat_mode = 'AUTO'   # 'AUTO' / 'MANUAL'


    # ╔═════════════════════════════════════════════════════════════════════
    # ║  [설정 4]  아군 기준 무기
    # ╟─────────────────────────────────────────────────────────────────────
    # ║  MANUAL 모드에서 사용할 무기이자, REQ 요구조건 계산의 기준 무기입니다
    # ║  AUTO 모드에서도 TEWA가 선택하지 못할 때 최후 기준으로 사용됩니다.
    # ║
    # ║  ┌──────────────────┬───────┬──────┬──────────┬──────────────────┐
    # ║  │ 무기명           │속도   │사거리│ 발당비용 │ 주요 용도        │
    # ║  ├──────────────────┼───────┼──────┼──────────┼──────────────────┤
    # ║  │'SM-3 Block IIA'  │4,500  │1,200 │$25,000,000│외기권·HGV 요격  │
    # ║  │                  │ m/s   │ km   │(약 337억) │탄도미사일 전용  │
    # ║  ├──────────────────┼───────┼──────┼──────────┼──────────────────┤
    # ║  │'SM-6'            │1,000  │ 370  │$4,200,000 │장거리·QBM 우선  │
    # ║  │                  │ m/s   │ km   │(약 57억)  │탄도+대공 겸용   │
    # ║  ├──────────────────┼───────┼──────┼──────────┼──────────────────┤
    # ║  │'SM-2 Block IIIB' │1,190  │ 170  │$400,000   │주력 함대공 미사일│
    # ║  │                  │ m/s   │ km   │(약 5.4억) │조사기 필요      │
    # ║  ├──────────────────┼───────┼──────┼──────────┼──────────────────┤
    # ║  │'RIM-116 RAM'     │ 680   │   9  │$150,000   │근접 방어 미사일 │
    # ║  │                  │ m/s   │ km   │(약 2억)   │대공·대함 겸용   │
    # ║  ├──────────────────┼───────┼──────┼──────────┼──────────────────┤
    # ║  │'홍상어 (대잠)'   │  28.3 │  19  │$500,000   │대잠 어뢰 전용   │
    # ║  │                  │ m/s   │ km   │(약 6.8억) │10 km 초과 시 우선│
    # ║  ├──────────────────┼───────┼──────┼──────────┼──────────────────┤
    # ║  │'청상어 (경어뢰)' │  28.3 │   9  │$200,000   │경어뢰 (근접 대잠)│
    # ║  │                  │ m/s   │ km   │(약 2.7억) │10 km 이하 사용  │
    # ║  ├──────────────────┼───────┼──────┼──────────┼──────────────────┤
    # ║  │'CIWS-II (Phalanx)│1,100  │   2  │$3,000/점사│최종 방어 기관포 │
    # ║  │                  │ m/s   │ km   │          │재고 무제한 설정  │
    # ║  └──────────────────┴───────┴──────┴──────────┴──────────────────┘
    # ║
    # ║  ※ 대잠 위협 시 → 홍상어 또는 청상어 선택 권장
    # ║  ※ 탄도미사일 위협 시 → SM-3 Block IIA 선택 권장
    # ║  ※ AUTO 모드에서는 TEWA가 자동 선택하므로 참고용으로만 사용됨
    # ╚═════════════════════════════════════════════════════════════════════
    friendly_preset_name = 'SM-3 Block IIA'   # ← 위 표에서 선택하여 교체하세요


    # ╔═════════════════════════════════════════════════════════════════════
    # ║  [설정 5]  초기 무기 재고
    # ╟─────────────────────────────────────────────────────────────────────
    # ║  각 무기의 출격 전 탑재 수량입니다. 시뮬레이션 중 소모되며
    # ║  완전 소진 시 해당 무기는 사용 불가 상태가 됩니다.
    # ║
    # ║  실제 정조대왕급 이지스 구축함 기준 탑재량 (참고)
    # ║  ┌──────────────────────┬───────┬──────────────────────────────┐
    # ║  │ 무기명               │권장수 │ 비고                          │
    # ║  ├──────────────────────┼───────┼──────────────────────────────┤
    # ║  │ SM-3 Block IIA       │  8    │ VLS Mk-41 (고가, 소수 운용)   │
    # ║  │ SM-6                 │ 32    │ VLS Mk-41                    │
    # ║  │ SM-2 Block IIIB      │ 48    │ VLS Mk-41 (주력)             │
    # ║  │ RIM-116 RAM          │ 21    │ 21발들이 발사기 1기           │
    # ║  │ 홍상어 (대잠)        │ 16    │ VLS 탑재                     │
    # ║  │ 청상어 (경어뢰)      │ 12    │ 어뢰 발사관 탑재             │
    # ║  │ CIWS-II (Phalanx)    │ 9999  │ 기관포 — 실질 무제한         │
    # ║  └──────────────────────┴───────┴──────────────────────────────┘
    # ║
    # ║  ※ 원하는 무기만 재고를 줄이거나 0으로 설정해 성능 비교 가능
    # ║  ※ 대잠 시나리오 시: 홍상어·청상어 재고를 충분히, 나머지는 유지
    # ╚═════════════════════════════════════════════════════════════════════
    inventory = {
        'SM-3 Block IIA':     8,      # 발 (외기권 BMD 전용, 고가)
        'SM-6':              32,      # 발 (장거리·탄도 겸용)
        'SM-2 Block IIIB':   48,      # 발 (주력 함대공)
        'RIM-116 RAM':       21,      # 발 (근접 방어)
        '홍상어 (대잠)':     16,      # 발 (대잠 어뢰 — 장거리)
        '청상어 (경어뢰)':   12,      # 발 (대잠 어뢰 — 근거리)
        'Mk.46 경어뢰':       8,       # 발 (P-8A/P-3C 항공투하용)
        'CIWS-II (Phalanx)': 9999,    # 발 (기관포 최후방어 — 사실상 무제한)
    }


    # ╔═════════════════════════════════════════════════════════════════════
    # ║  [설정 6]  날씨 조건
    # ╟─────────────────────────────────────────────────────────────────────
    # ║  날씨는 탐지 거리, 요격 확률(Pk), C&D 시간 세 가지에 영향을 줍니다.
    # ║  아래 8종 중 하나를 정확히 복사해 weather 에 붙여넣으세요.
    # ║
    # ║  ┌────────────────────────┬──────┬─────────┬──────┬─────────────┐
    # ║  │ 날씨 이름              │탐지  │ Pk 보정 │C&D   │ 특징        │
    # ║  │                        │배율  │ (±)     │배율  │             │
    # ║  ├────────────────────────┼──────┼─────────┼──────┼─────────────┤
    # ║  │'맑음 (주간)'           │×1.00 │ ±0.00  │×1.00 │ 기준 조건   │
    # ║  │'맑음 (야간)'           │×0.97 │ -0.01  │×1.05 │ 야간 가시도 │
    # ║  │'흐림 (박무)'           │×0.90 │ -0.03  │×1.10 │ 박무/연무   │
    # ║  │'황사 (봄철 황사)'      │×0.93 │ -0.02  │×1.10 │ 봄철 황사   │
    # ║  │'풍랑 (7~8등급)'        │×0.85 │ -0.06  │×1.20 │ 파고 4~6 m  │
    # ║  │'폭풍 (해상 악화)'      │×0.75 │ -0.08  │×1.25 │ 파고 6~9 m  │
    # ║  │'태풍 (9~12등급)'       │×0.55 │ -0.15  │×1.50 │ 최악 조건   │
    # ║  │'농무 (시정 200m 이하)' │×0.88 │ -0.03  │×1.10 │ 짙은 안개   │
    # ║  └────────────────────────┴──────┴─────────┴──────┴─────────────┘
    # ║
    # ║  탐지 배율: 기본 탐지거리 × 배율 = 실제 유효 탐지거리
    # ║  Pk 보정  : 요격 확률에 해당 수치를 가감 (태풍 시 -0.15 대폭 감소)
    # ║  C&D 배율 : 기본 C&D 시간 × 배율 = 실제 처리 시간 (긴 것이 불리)
    # ╚═════════════════════════════════════════════════════════════════════
    weather = '맑음 (주간)'   # ← 위 표에서 선택하여 교체하세요


    # ╔═════════════════════════════════════════════════════════════════════
    # ║  [설정 7]  교전 시나리오 수치
    # ╟─────────────────────────────────────────────────────────────────────
    # ║
    # ║  num_threats (동시 위협 수)
    # ║    시뮬레이션에 투입할 동일 적 플랫폼의 총 수
    # ║    최대 24개 (교전 채널 한계) | 권장: 3 ~ 10
    # ║    NEW-C 다발 발사로 실제 이벤트 수는 더 많아질 수 있습니다
    # ║
    # ║  launch_interval_s (발진 간격, 초)
    # ║    각 위협이 몇 초 간격으로 순차 발진하는지 설정
    # ║    작을수록 동시 채널 포화 확률 증가 (교전 채널 시험 시 줄이세요)
    # ║    권장: 30 ~ 300초 | 60초 = 1분 간격
    # ║
    # ║  cd_time_s (C&D 시간 = 탐지·추적·교전결심 소요 시간, 초)
    # ║    적 탐지 후 첫 교전 명령까지 걸리는 기준 시간
    # ║    REQ-02 판정 기준: 이 값 ≤ 최대 허용 C&D 이면 PASS
    # ║    권장: 10 ~ 45초 | 실전 이지스: 약 15~25초
    # ║
    # ║  cd_jitter_s (C&D 시간 랜덤 편차, 초)
    # ║    C&D 시간에 ±이 값만큼 무작위 오차를 추가해 현실감 부여
    # ║    0 → 항상 동일한 C&D 시간 (결정론적 시뮬레이션)
    # ║    권장: 2 ~ 10초
    # ║
    # ║  confirm_time_s (교전 확인 시간, 초)
    # ║    요격 실패 후 결과 확인 및 재교전 결심까지 걸리는 시간
    # ║    이 값이 클수록 재교전 기회가 줄어들어 방어 난이도 상승
    # ║    권장: 10 ~ 30초 | 실전 이지스: 약 15초
    # ╚═════════════════════════════════════════════════════════════════════
    num_threats       = 1    # 개 (1 ~ 24, 교전 채널 최대 24)
    launch_interval_s = 60   # 초 (위협 간 발진 간격)
    cd_time_s         = 20   # 초 (탐지→교전결심 소요 시간)
    cd_jitter_s       = 5    # 초 (C&D 시간 랜덤 편차 ±)
    confirm_time_s    = 15   # 초 (요격 후 확인 및 재교전 준비 시간)

    # ════════════════════════════════════════════════════════════════════════
    #  [실행부]
    # ════════════════════════════════════════════════════════════════════════
    cfg = {
        'enemy_preset':                enemy_preset_name,
        'friendly_preset':             friendly_preset_name,
        'category':                    ENEMY_DB[enemy_preset_name]['category'],
        'weather':                     weather,
        'enemy_fires_missile':         enemy_fires_missile,
        'missile_salvo_mode':          missile_salvo_mode,
        'missile_salvo_fixed':         missile_salvo_fixed,
        'enable_enemy_evasion':        enable_enemy_evasion,
        'enable_missile_evasion':      enable_missile_evasion,
        'enable_acoustic_decoy':       enable_acoustic_decoy,
        'enable_ship_torpedo_evasion': enable_ship_torpedo_evasion,
        'decoy_stock':                 decoy_stock,
        'enable_enemy_self_defense':   enable_enemy_self_defense,
        'enable_ecm':                  enable_ecm,
        'enable_helo':                 enable_helo,
        'helo_preset':                 helo_preset,
        'enable_p3c':                  enable_p3c,
        'p3c_preset':                  p3c_preset,
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
        'mc_save_nth':                 mc_save_nth,
        'num_threats':                 num_threats,
        'launch_interval_s':          launch_interval_s,
        'cd_time_s':                   cd_time_s,
        'cd_jitter_s':                 cd_jitter_s,
        'confirm_time_s':              confirm_time_s,
        'combat_mode':                 combat_mode,
        'inventory':                   inventory,
        'use_custom_enemy':            use_custom_enemy,
        'custom_enemy_speed':          custom_enemy_speed,
        'custom_detect_km':            custom_detect_km,
    }

    # BUG-3 수정(v6.8.1): enable_missile_evasion=False 시 ENEMY_DB를 전역으로 수정하던
    # 기존 코드를 제거. 이제 run_single_sim 내부 m_info 생성 시점에 직접 반영되므로
    # ENEMY_DB 원본이 영구 변조되지 않음 (재실행 시에도 설정이 정상 복원됨)

    (max_cd,t_arrive_base,t_fly_min,mc,min_d,
     all_events,active_events,verdicts,details,sc_results,
     dm_eff,weather_delta,cd_eff,total_cost,global_inv,
     ch_mgr,ship_status) = run_full_simulation(cfg)

    img_path=plot_all(cfg,max_cd,t_arrive_base,t_fly_min,mc,min_d,
                      all_events,active_events,verdicts,details,sc_results,
                      dm_eff,weather_delta,cd_eff,total_cost,global_inv,
                      ch_mgr,ship_status)

    save_excel_report(cfg,max_cd,mc,min_d,verdicts,details,sc_results,
                      dm_eff,weather_delta,cd_eff,total_cost,global_inv,
                      ch_mgr,all_events,img_path,ship_status)

    print("\n  v6.1 분석 완료. PNG / XLSX 파일을 확인하세요.")
    print("  ※ BUG-1 수정: 수상함·잠수함 미사일 발사 보장 (fire_m = min(desired, dm×0.90))")
    print("  ※ NEW-F 간단: self_defense_pk → 아군 미사일 effective_pk = pk × (1 - sdpk)")
    print("  ※ NEW-F 중간: enemy_ciws_pk  → 수상함 CIWS로 아군 미사일 1발당 독립 요격 판정")
    print("  ※ 총 Monte Carlo: 메인 1,000회 + 시나리오 3종×300회 = 1,900회")
    print("  ※ NEW-C 다발 발사로 실제 위협 수는 num_threats보다 많을 수 있습니다.")
    print("  ※ NEW-G ECM: enable_ecm=True 시 거리 반비례 재밍 적용 (50km 기준)")
    print("  ※ NEW-H 헬기: enable_helo=True + 대잠 시나리오 선택 시 활성화")
    print("  ※ NEW-I P-3C: enable_p3c=True → 포항기지 출격 광역 대잠 (태풍 외 출격 가능)")
    print("  ※ NEW-J P-8A: enable_p8a=True → P-3C 후속 포세이돈, 준비 30분, 소노부이 +18km")
    print("  ※ 대시보드: streamlit run Dashboard_v6_8_4.py 로 실행")
    print("  ※ mc_save_nth>0: 해당 MC 회차 교전 로그를 Sheet9에 저장")
    print("  필수 패키지: pip install matplotlib numpy scipy openpyxl pillow")


