"""
engine_v7.py — 이지스 기동전단 통합 방어 시뮬레이터 v7.0
시간 스텝 기반 양방향 교전 엔진

v7.0 핵심 변경:
  · 이벤트 기반 → 시간 스텝(1초 단위) 시뮬레이션
  · 양방향 교전: 아군 공격(해성/하푼) + 적 SAM/CIWS 방어
  · 2D 위치 좌표계 (모든 엔티티 실시간 위치 추적)
  · SimFrame 단위 상태 기록 (애니메이션 지원)

v7.0 패치 이력:
  · 1단계: 시간 스텝 루프 + 위치 모델 + 기본 교전 판정
  · 2단계: 양방향 교전 검증
    - SAM alive=False 조기 설정 버그 수정 (요격 판정 스킵 문제)
    - INTERCEPT_DIST_M 300m → 2000m (1초 스텝 해상도 반영)
    - 대함 탐지 거리 수정 (자함 레이더 45km → 전술 인식 detect_km 병용)
    - 적 함정 시작 위치 수정 (1.8x → 1.0x, 교전 즉시 개시)
    - 적 함정 재발사 허용 (비행 중 미사일 소진 후 재장전)
  · 3단계: ENEMY_DB 전 32종 위협 지원
    - EnemyShipObj → EnemyThreatObj (항공기/함정/잠수함/독립미사일 통합)
    - 항공기: 접근 → 사거리 내 발사 → 이탈 행동 패턴
    - 탄도/순항/HGV/QBM 독립 미사일: _build_enemies()에서 MissileObj로 직접 생성
    - 대잠전: 홍상어/청상어 ASW 운용, 소나 탐지 범위 반영
    - _select_defense_wpn(): 고도/유형 인식 (SM-3 HGV/탄도, SM-6 QBM)
    - _friendly_strike(): 수상함(해성/하푼) + 잠수함(홍상어/청상어) 분리
  · 4단계: 몬테카를로 분석 + 보고서 생성
    - matplotlib 한글 폰트 설정 (Malgun Gothic)
    - monte_carlo_v7(): N회 반복 통계 집계 (요격률/피격/격침/비용)
    - plot_v7(): 6개 서브플롯 PNG 차트 (히스토그램·무기소모·수치요약)
    - save_excel_report_v7(): 4시트 Excel 보고서 (MC요약/무기소모/교전로그/차트)
    - __main__ 인수: python engine_v7.py [시나리오] [MC횟수]
  · 포팅 A: 방어 무기 재고 수동 설정 + 적군 편대 모드
    - _build_friendly(): sm3/sm6/sm2/ram/홍상어/청상어/mk46 수동 재고 지원 (cfg 키로 설정)
    - _build_enemies(): enemy_fleet_mode 4종 지원 (single/preset/custom/random)
    - ENEMY_FLEET_PRESETS / ENEMY_FLEET_RANDOM_CFG / generate_random_enemy_fleet 연동
  · 포팅 B: 전술 기능 — ECM·종말회피·음향기만기·함정회피·적 자체방어
    - ECM_REF_RANGE_M=50km 기준 거리 반비례 Pk 감소, Pk 하한 50% (탄도/HGV 제외)
    - 종말 회피: 20km 이내 terminal_evasion_factor 적용 (ENEMY_DB missile_terminal_evasion)
    - 음향 기만기: DECOY_PK=0.60, 어뢰 전용, decoy_stock 소모
    - 함정 회피 기동: SHIP_EVASION_PK=0.30, 어뢰 전용
    - 적 자체방어: CIWS(enemy_ciws_pk) 요격 → 채프/플레어(self_defense_pk) Pk 감소
  · 포팅 C: 항공 자산 대잠 운용 (FriendlyAircraftObj + _aircraft_asw())
    - AW-159 와일드캣: 함재 헬기, 청상어 2발, 사거리 140km, 폭풍/태풍/농무 불가
    - P-3C 오라이온: 포항기지 출격(+300km), Mk.46 4발, 소노부이 탐지+15km
    - P-8A 포세이돈: 포항기지 출격(+300km), Mk.46 5발, 소노부이 탐지+18km
  · 포팅 D: 분석 기능 — REQ 판정 + 날씨 비교 + A vs B + 저장/불러오기
    - evaluate_req_v7(): REQ-01~08 8항목 시간스텝 기반 판정
    - scenario_comparison_v7(): 날씨 3종(맑음/흐림/폭풍) MC 비교
    - compare_ab_v7(): 두 cfg MC 결과 대비 (Δ요격률·Δ비용)
    - save_scenario_v7() / load_scenario_v7(): JSON 시나리오 저장/불러오기
    - _compile(): remaining_inventory·total_channels·peak_concurrent_threats·t_first_fire 추가
"""

import math, random, os
from typing import List, Optional

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import matplotlib.font_manager as fm
import numpy as np
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
try:
    from openpyxl.drawing.image import Image as XLImage
    _CAN_IMG = True
except Exception:
    _CAN_IMG = False

for _fp in ['C:/Windows/Fonts/malgun.ttf', 'C:/Windows/Fonts/malgunbd.ttf']:
    if os.path.exists(_fp):
        fm.fontManager.addfont(_fp)
matplotlib.rcParams['font.family'] = 'Malgun Gothic'
matplotlib.rcParams['axes.unicode_minus'] = False

from engine import (
    ENEMY_DB, FRIENDLY_DB, FRIENDLY_AIRCRAFT_DB, WEATHER_DB,
    SHIP_DB, FLEET_PRESETS,
    ENEMY_FLEET_PRESETS, ENEMY_FLEET_RANDOM_CFG, generate_random_enemy_fleet,
    calculate_detect_range_by_rcs,
)

# ── 시뮬레이션 상수 ──────────────────────────────────────────────────────────
DT               = 1.0    # 시간 스텝 (초)
MAX_SIM_TIME     = 700    # 최대 시뮬 시간 (초)
INTERCEPT_DIST_M = 2000   # SAM 요격 판정 거리 (m)
ECM_REF_RANGE_M  = 50_000 # 포팅 B: ECM 재밍 기준 거리 (m)
DECOY_PK         = 0.60   # 포팅 B: 음향 기만기 유인 성공률
SHIP_EVASION_PK  = 0.30   # 포팅 B: 함정 회피 기동 성공률
MAX_RESPONSE_TIME_S = 120  # 포팅 D: REQ-02 최대 허용 응답시간 (초)

# 다층 방어 레이어 순서: 가장 먼저 교전하는 함정 유형부터
LAYER_ORDER    = ['KDX-III', 'KDX-II', 'FFX']
SHIP_LAYER_PRI = {t: i for i, t in enumerate(LAYER_ORDER)}  # KDX-III=0, KDX-II=1, FFX=2

# 포팅 C: v7 시뮬 시간 스케일 맞춤 출격 준비 시간 (전시 긴급 출격 기준)
# FRIENDLY_AIRCRAFT_DB의 sortie_time_s(평시)를 v7 700초 시뮬에 맞게 단축
_AIRCRAFT_V7_SORTIE = {
    'AW-159 와일드캣': 300,   # 5분 (평시 동일)
    'P-3C 오라이온':   600,   # 10분 (평시 40분 → 전시 긴급 출격)
    'P-8A 포세이돈':   480,   # 8분 (평시 30분 → 전시 긴급 출격)
}

# ════════════════════════════════════════════════════════════════════════════
#  새 DB: 아군 대함 공격 무기
# ════════════════════════════════════════════════════════════════════════════
FRIENDLY_STRIKE_DB = {
    '해성-I': {
        'speed_ms': 300,
        'range_km': 180,
        'cost_usd': 800_000,
        'pk_base':  0.80,
    },
    '해성-II': {
        'speed_ms': 300,
        'range_km': 250,
        'cost_usd': 1_200_000,
        'pk_base':  0.82,
    },
    '하푼 Block II': {
        'speed_ms': 278,
        'range_km': 280,
        'cost_usd': 1_500_000,
        'pk_base':  0.78,
    },
}

# ════════════════════════════════════════════════════════════════════════════
#  새 DB: 적 함정 SAM 시스템
# ════════════════════════════════════════════════════════════════════════════
ENEMY_SAM_DB = {
    'HHQ-9B':    {'range_km': 200, 'speed_ms': 1400, 'pk': 0.82, 'channels': 6},
    'HHQ-16':    {'range_km':  50, 'speed_ms': 1000, 'pk': 0.75, 'channels': 4},
    'HHQ-10':    {'range_km':   9, 'speed_ms':  680, 'pk': 0.70, 'channels': 2},
    '1130-CIWS': {'range_km':   3, 'speed_ms': 1100, 'pk': 0.65, 'channels': 1},
}

ENEMY_SHIP_SAM_LOADOUT = {
    '055형 대형 구축함': [
        {'name': 'HHQ-9B',    'stock': 112},
        {'name': 'HHQ-10',    'stock':  24},
        {'name': '1130-CIWS', 'stock': 9999},
    ],
    '052D형 구축함': [
        {'name': 'HHQ-9B',    'stock': 64},
        {'name': 'HHQ-10',    'stock': 24},
        {'name': '1130-CIWS', 'stock': 9999},
    ],
    '054A형 호위함': [
        {'name': 'HHQ-16',    'stock': 32},
        {'name': 'HHQ-10',    'stock': 24},
        {'name': '1130-CIWS', 'stock': 9999},
    ],
    '056형 초계함': [
        {'name': 'HHQ-10',    'stock':  8},
        {'name': '1130-CIWS', 'stock': 9999},
    ],
    '022형 미사일 고속정': [
        {'name': '1130-CIWS', 'stock': 9999},
    ],
}

# 독립 미사일 유형 (EnemyThreatObj 대신 MissileObj로 직접 생성)
_STANDALONE_MISSILE_TYPES = ('탄도미사일', '순항미사일', '극초음속활공체', '저고도기동탄도')


# ════════════════════════════════════════════════════════════════════════════
#  Vec2
# ════════════════════════════════════════════════════════════════════════════
class Vec2:
    __slots__ = ('x', 'y')

    def __init__(self, x: float = 0.0, y: float = 0.0):
        self.x = float(x)
        self.y = float(y)

    def dist_to(self, other: 'Vec2') -> float:
        return math.hypot(self.x - other.x, self.y - other.y)

    def bearing_to(self, other: 'Vec2') -> float:
        return math.atan2(other.y - self.y, other.x - self.x)

    def move_toward(self, target: 'Vec2', speed_ms: float, dt: float) -> bool:
        """target 방향으로 이동. 도달했으면 True 반환."""
        d = self.dist_to(target)
        step = speed_ms * dt
        if d <= step:
            self.x, self.y = target.x, target.y
            return True
        angle = self.bearing_to(target)
        self.x += math.cos(angle) * step
        self.y += math.sin(angle) * step
        return False

    def copy(self) -> 'Vec2':
        return Vec2(self.x, self.y)

    def __repr__(self) -> str:
        return f"Vec2({self.x/1000:.1f}km, {self.y/1000:.1f}km)"


# ════════════════════════════════════════════════════════════════════════════
#  MissileObj
# ════════════════════════════════════════════════════════════════════════════
class MissileObj:
    """
    mtype:
      'enemy_strike'   — 적 대함/대지 공격 (아군 함정 또는 독립 미사일 위협)
      'friendly_strike'— 아군 대함/대잠 공격
      'friendly_sam'   — 아군 SAM (적 미사일·항공기 요격)
      'enemy_sam'      — 적 SAM (아군 미사일 요격)
    """
    _id_counter = 0

    def __init__(self, mtype: str, name: str, pos: Vec2,
                 target,
                 speed_ms: float, pk_base: float,
                 owner_id: int, t_spawn: float = 0.0):
        MissileObj._id_counter += 1
        self.uid       = f"M{MissileObj._id_counter:04d}"
        self.mtype     = mtype
        self.name      = name
        self.pos       = pos.copy()
        self.target    = target
        self.speed_ms  = speed_ms
        self.pk_base   = pk_base
        self.owner_id  = owner_id
        self.t_spawn   = t_spawn

        self.alive       = True
        self.intercepted = False
        self.hit         = False
        self.t_intercept: Optional[float] = None
        self.t_hit:       Optional[float] = None

        # 독립 미사일 위협 속성 (탄도/HGV/QBM 등 — _build_enemies에서 설정)
        self.altitude_m:   float = 0.0
        self.is_hgv:       bool  = False
        self.is_qbm:       bool  = False
        self.is_ballistic: bool  = False

        # 포팅 B: 전술 속성
        self.terminal_evasion_factor: float = 1.0  # 종말 회피 계수 (< 20km 적용)
        self.is_torpedo:              bool  = False # 어뢰 여부 (기만기/회피 판정용)

    def update(self, dt: float) -> bool:
        """1 tick 이동. alive=False 설정 금지 — 요격/피격 판정은 엔진이 담당."""
        if not self.alive:
            return False
        arrived = self.pos.move_toward(self.target.pos, self.speed_ms, dt)
        if arrived:
            self.hit = True
        return arrived

    @classmethod
    def reset_counter(cls):
        cls._id_counter = 0


# ════════════════════════════════════════════════════════════════════════════
#  EnemyThreatObj — 적 플랫폼 위협 통합 (항공기 / 수상함 / 잠수함)
#  독립 미사일(탄도/순항/HGV/QBM)은 _build_enemies()에서 MissileObj로 생성.
# ════════════════════════════════════════════════════════════════════════════
class EnemyThreatObj:
    _id_counter = 0

    _HP_MAP = {
        '전투기': 1, '폭격기': 1, '전폭기': 1,
        '잠수함': 3,
        '고속정': 2, '초계함': 2,
        '호위함': 3, '구축함': 4,
    }

    def __init__(self, preset_name: str, pos: Vec2):
        EnemyThreatObj._id_counter += 1
        self.uid         = f"ET{EnemyThreatObj._id_counter:03d}"
        self.preset_name = preset_name
        self.name        = preset_name   # 요격 로그 호환
        self.info        = ENEMY_DB[preset_name].copy()
        self.pos         = pos
        self.speed_ms    = self.info['speed_ms']
        self.altitude_m  = self.info.get('altitude_m', 0)

        cat   = self.info.get('category', '대함')
        ttype = self.info.get('type', '')
        self.category    = cat
        self.threat_type = ttype
        self.is_aircraft = ttype in ('전투기', '폭격기', '전폭기')
        self.is_ship     = cat == '대함'
        self.is_sub      = cat == '대잠'

        self.hp = self._HP_MAP.get(ttype, 2)

        if self.is_ship:
            loadout = ENEMY_SHIP_SAM_LOADOUT.get(preset_name, [])
            self.sam_inventory = {item['name']: item['stock'] for item in loadout}
            self.sam_max_channels = sum(
                ENEMY_SAM_DB[n]['channels']
                for n in self.sam_inventory if n in ENEMY_SAM_DB
            )
        else:
            self.sam_inventory    = {}
            self.sam_max_channels = 0
        self.sam_channels_used = 0

        self.alive        = True
        self.intercepted  = False
        self.hit_count    = 0
        self.hit_by: list = []
        self.has_fired    = False
        self.t_intercept: Optional[float] = None

        # 항공기 이탈 상태
        self.is_retreating             = False
        self.retreat_pos: Optional[Vec2] = None

    def take_hit(self, weapon_name: str, t: float):
        self.hit_count += 1
        self.hit_by.append((weapon_name, t))
        self.hp -= 1
        if self.hp <= 0:
            self.alive = False

    def select_sam(self, missile_dist_m: float) -> Optional[str]:
        """수상함용: 사거리 내 SAM 선택 (장거리 우선)"""
        for sam_name in ['HHQ-9B', 'HHQ-16', 'HHQ-10', '1130-CIWS']:
            if self.sam_inventory.get(sam_name, 0) <= 0:
                continue
            sam = ENEMY_SAM_DB.get(sam_name)
            if sam and missile_dist_m <= sam['range_km'] * 1000:
                return sam_name
        return None

    @classmethod
    def reset_counter(cls):
        cls._id_counter = 0


# ════════════════════════════════════════════════════════════════════════════
#  FriendlyShipObj
# ════════════════════════════════════════════════════════════════════════════
class FriendlyShipObj:
    def __init__(self, name: str, ship_type: str, pos: Optional[Vec2] = None):
        self.name        = name
        self.ship_type   = ship_type
        spec             = SHIP_DB[ship_type]
        self.display     = spec['display']
        self.sensor_km   = spec['sensor_km']
        self.max_channels= spec['max_channels']
        self.pos         = pos or Vec2(0, 0)

        self.inventory   = spec['default_inventory'].copy()

        self.strike_inventory: dict = {}

        self.hp            = 5
        self.alive         = True
        self.hit_count     = 0
        self.total_cost    = 0.0
        self.channels_used = 0
        self.decoy_stock   = 4  # 포팅 B: AN/SLQ-25 음향 기만기 기본 재고

    @property
    def operational(self) -> bool:
        return self.alive

    def take_hit(self, weapon_name: str, t: float):
        self.hit_count += 1
        self.hp -= 1
        if self.hp <= 0:
            self.alive = False


# ════════════════════════════════════════════════════════════════════════════
#  포팅 C: FriendlyAircraftObj — 항공 자산 (헬기 / 해상초계기)
# ════════════════════════════════════════════════════════════════════════════
class FriendlyAircraftObj:
    """
    함재 헬기(base_type='ship') / 육상초계기(base_type='land') 통합 클래스.
    매 tick _aircraft_asw()에서 잠수함 표적 확인 후 어뢰 투하.
    """
    def __init__(self, name: str, home_pos: 'Vec2'):
        self.name              = name
        self.info              = FRIENDLY_AIRCRAFT_DB[name]
        self.home_pos          = home_pos.copy()
        self.t_available       = float(self.info['sortie_time_s'])  # 초기 출격 준비 시간
        self.payload_remaining = self.info['payload_cnt']
        self.sorties           = 0
        self.total_cost        = 0.0


# ════════════════════════════════════════════════════════════════════════════
#  SimFrame
# ════════════════════════════════════════════════════════════════════════════
class SimFrame:
    __slots__ = ('t', 'friendly_ships', 'enemy_ships', 'missiles', 'events',
                 'ship_channels')

    def __init__(self, t: float):
        self.t              = t
        self.friendly_ships = []  # [(name, x, y, alive, hp)]
        self.enemy_ships    = []  # [(uid, preset, x, y, alive, hp)]
        self.missiles       = []  # [(uid, x, y, mtype, name)]
        self.events         = []  # [str]
        self.ship_channels  = []  # [(name, channels_used, max_channels)]


# ════════════════════════════════════════════════════════════════════════════
#  TimeStepEngine
# ════════════════════════════════════════════════════════════════════════════
class TimeStepEngine:
    """
    매 DT(1초)마다 실행 순서:
      1. 위치 갱신 (적 위협 접근/이탈, 미사일 비행)
      2. 적 발사 조건 확인 (함정/항공기/잠수함)
      3. 아군 TEWA — 방어 (적 미사일·항공기 요격)
      4. 아군 TEWA — 공격 (수상함: 해성/하푼, 잠수함: 홍상어/청상어)
      5. 적 TEWA   — SAM 방어 (수상함만, 아군 미사일 요격)
      6. 교전 결과 판정
      7. 프레임 기록
    """

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.t   = 0.0
        self._log_entries: list = []
        self._tick_events:  list = []

        MissileObj.reset_counter()
        EnemyThreatObj.reset_counter()

        # stats / wx 먼저 초기화 (build 함수에서 참조 가능)
        self.stats = {
            'total_threats':           0,
            'intercepted_threats':     0,
            'friendly_hits':           0,
            'enemy_hits':              0,
            'friendly_ships_lost':     0,
            'enemy_ships_destroyed':   0,
            'total_cost':              0.0,
            'aircraft_sorties':        0,
            # 포팅 D: REQ 판정용
            'peak_concurrent_threats': 0,
            't_first_fire':            -1.0,
            'total_missiles_fired':    0,
        }
        weather = cfg.get('weather', '맑음 (주간)')
        self.wx = WEATHER_DB.get(weather, WEATHER_DB['맑음 (주간)'])

        self.friendly_ships: List[FriendlyShipObj]    = self._build_friendly()
        self.missiles:       List[MissileObj]         = []
        self.enemy_threats:  List[EnemyThreatObj]     = self._build_enemies()
        self.aircraft:       List[FriendlyAircraftObj] = self._build_aircraft()
        self.frames:         List[SimFrame]            = []

    # ── 편대 구성 ─────────────────────────────────────────────────────────────

    def _build_friendly(self) -> List[FriendlyShipObj]:
        preset_name = self.cfg.get('fleet_preset', '단독 작전')
        preset = FLEET_PRESETS.get(preset_name, FLEET_PRESETS['단독 작전'])
        ships = []
        for spec in preset:
            s = FriendlyShipObj(spec['name'], spec['type'])
            s.strike_inventory = {
                '해성-II':       self.cfg.get('haesong2_stock', 8),
                '해성-I':        self.cfg.get('haesong1_stock', 0),
                '하푼 Block II': self.cfg.get('harpoon_stock',  4),
            }
            # 포팅 A: 방어 무기 재고 수동 설정 (설정 없으면 SHIP_DB 기본값 유지)
            _def_map = [
                ('SM-3 Block IIA',  'sm3_stock'),
                ('SM-6',            'sm6_stock'),
                ('SM-2 Block IIIB', 'sm2_stock'),
                ('RIM-116 RAM',     'ram_stock'),
                ('홍상어 (대잠)',    'hongsango_stock'),
                ('청상어 (경어뢰)', 'cheongsango_stock'),
                ('Mk.46 경어뢰',    'mk46_stock'),
            ]
            for wpn, cfg_key in _def_map:
                if cfg_key in self.cfg and wpn in s.inventory:
                    s.inventory[wpn] = self.cfg[cfg_key]
            # 포팅 B: 기만기 재고 수동 설정
            if 'decoy_stock' in self.cfg:
                s.decoy_stock = self.cfg['decoy_stock']
            ships.append(s)
        return ships

    def _build_enemies(self) -> List[EnemyThreatObj]:
        """
        플랫폼(항공기/수상함/잠수함) → EnemyThreatObj
        독립 미사일(탄도/순항/HGV/QBM) → MissileObj (self.missiles에 직접 추가)
        """
        # 포팅 A: 적군 편대 모드 (단일/프리셋/커스텀/랜덤)
        mode = self.cfg.get('enemy_fleet_mode', 'custom')
        if mode == 'preset':
            fleet_cfg = ENEMY_FLEET_PRESETS.get(
                self.cfg.get('enemy_fleet_preset', ''), [])
        elif mode == 'random':
            fleet_cfg = generate_random_enemy_fleet(
                difficulty=self.cfg.get('enemy_fleet_difficulty', '보통'),
                seed=self.cfg.get('enemy_fleet_seed', None))
        else:
            fleet_cfg = self.cfg.get('enemy_fleet', [])

        detect_km  = self.cfg.get('detect_km', 200)
        sub_det_km = self.cfg.get('sub_detect_km', 50)
        primary    = self._primary()  # 독립 미사일 표적

        threats: List[EnemyThreatObj] = []
        total = sum(s.get('count', 1) for s in fleet_cfg)
        idx = 0

        for spec in fleet_cfg:
            name  = spec['preset']
            count = spec.get('count', 1)
            if name not in ENEMY_DB:
                continue
            info  = ENEMY_DB[name]
            ttype = info.get('type', '')

            for _ in range(count):
                bearing_rad = math.radians((idx / max(total, 1)) * 360)

                if info.get('category') == '대잠':
                    start_m = sub_det_km * 1000
                else:
                    start_m = detect_km * 1000

                pos = Vec2(
                    math.cos(bearing_rad) * start_m,
                    math.sin(bearing_rad) * start_m,
                )

                if ttype in _STANDALONE_MISSILE_TYPES:
                    # 독립 미사일 위협: MissileObj로 직접 생성
                    m = MissileObj(
                        mtype    = 'enemy_strike',
                        name     = name,
                        pos      = pos,
                        target   = primary,
                        speed_ms = info['speed_ms'],
                        pk_base  = 0.80,
                        owner_id = -1,
                        t_spawn  = 0.0,
                    )
                    m.altitude_m             = float(info.get('altitude_m', 0))
                    m.is_hgv                 = bool(info.get('is_hgv', False))
                    m.is_qbm                 = bool(info.get('is_qbm', False))
                    m.is_ballistic           = (ttype == '탄도미사일')
                    m.terminal_evasion_factor = info.get('missile_terminal_evasion', 1.0)
                    m.is_torpedo             = False
                    self.missiles.append(m)
                    self.stats['total_threats'] += 1
                else:
                    threats.append(EnemyThreatObj(name, pos))

                idx += 1

        return threats

    def _build_aircraft(self) -> List[FriendlyAircraftObj]:
        """포팅 C: enable_helo / enable_p3c / enable_p8a cfg 키로 항공 자산 등록."""
        aircraft = []
        primary_pos = self._primary().pos
        for en_key, preset_key, default in [
            ('enable_helo', 'helo_preset', 'AW-159 와일드캣'),
            ('enable_p3c',  'p3c_preset',  'P-3C 오라이온'),
            ('enable_p8a',  'p8a_preset',  'P-8A 포세이돈'),
        ]:
            if not self.cfg.get(en_key, False):
                continue
            name = self.cfg.get(preset_key, default)
            if name not in FRIENDLY_AIRCRAFT_DB:
                continue
            aircraft.append(FriendlyAircraftObj(name, primary_pos))
        return aircraft

    # ── 헬퍼 ─────────────────────────────────────────────────────────────────

    def _primary(self) -> FriendlyShipObj:
        for s in self.friendly_ships:
            if s.alive and s.ship_type == 'KDX-III':
                return s
        return next((s for s in self.friendly_ships if s.alive), self.friendly_ships[0])

    def _log(self, msg: str):
        self._log_entries.append((self.t, msg))
        self._tick_events.append(msg)

    def _detect_range_m(self, ship: FriendlyShipObj, category: str) -> float:
        if category == '대잠':
            base_km = ship.sensor_km.get('대잠', 50)
            factor  = self.wx.get('sonar_factor', self.wx.get('detect_range_factor', 1.0))
        else:
            # 대공/대함: 데이터링크 적용 — cfg에 사전 계산된 detect_km 사용
            if category == '대함':
                base_km = max(ship.sensor_km.get('대함', 45),
                              self.cfg.get('detect_km', 200))
            else:
                base_km = ship.sensor_km.get(category, self.cfg.get('detect_km', 200))
            factor = self.wx.get('radar_factor', self.wx.get('detect_range_factor', 1.0))
        return base_km * 1000 * factor

    # ── 1단계: 위치 갱신 ──────────────────────────────────────────────────────

    def _update_positions(self):
        primary_pos = self._primary().pos
        for et in self.enemy_threats:
            if not et.alive:
                continue
            if et.is_retreating and et.retreat_pos:
                arrived = et.pos.move_toward(et.retreat_pos, et.speed_ms, DT)
                if arrived:
                    et.alive = False
                    self._log(f"[이탈] {et.preset_name} 전장 이탈 완료")
            else:
                et.pos.move_toward(primary_pos, et.speed_ms, DT)
        for m in self.missiles:
            m.update(DT)

    # ── 2단계: 적 발사 ────────────────────────────────────────────────────────

    def _enemy_fire(self):
        primary = self._primary()
        for et in self.enemy_threats:
            if not et.alive or et.is_retreating:
                continue
            if not et.info.get('can_fire_missile'):
                continue

            in_flight = sum(
                1 for m in self.missiles
                if m.alive and m.owner_id == id(et) and m.mtype == 'enemy_strike'
            )
            if in_flight > 0:
                continue

            dist_m       = et.pos.dist_to(primary.pos)
            fire_range_m = et.info.get('missile_range_km', 0) * 1000 * 0.85
            if dist_m > fire_range_m:
                continue

            salvo   = random.randint(
                et.info.get('missile_salvo_min', 1),
                et.info.get('missile_salvo_max', 2),
            )
            m_speed = et.info.get('missile_speed_ms') or 300
            m_name  = et.info.get('missile_name') or '대함미사일'

            for _ in range(salvo):
                offset = Vec2(
                    et.pos.x + random.uniform(-500, 500),
                    et.pos.y + random.uniform(-500, 500),
                )
                _m = MissileObj(
                    mtype    = 'enemy_strike',
                    name     = m_name,
                    pos      = offset,
                    target   = primary,
                    speed_ms = m_speed,
                    pk_base  = 0.80,
                    owner_id = id(et),
                    t_spawn  = self.t,
                )
                # 포팅 B: 전술 속성 설정
                _m.terminal_evasion_factor = et.info.get('missile_terminal_evasion', 1.0)
                _m.is_torpedo = '어뢰' in m_name
                self.missiles.append(_m)

            et.has_fired = True
            self.stats['total_threats'] += salvo

            if et.is_aircraft:
                et.is_retreating = True
                # 이탈 방향: 함대 반대 방향 500km
                angle = et.pos.bearing_to(primary.pos) + math.pi
                et.retreat_pos = Vec2(
                    et.pos.x + math.cos(angle) * 500_000,
                    et.pos.y + math.sin(angle) * 500_000,
                )
                self._log(
                    f"[적 발사+이탈] {et.preset_name} -> {m_name} {salvo}발 "
                    f"(거리 {dist_m/1000:.0f}km), 이탈 개시"
                )
            else:
                self._log(
                    f"[적 발사] {et.preset_name} -> {m_name} {salvo}발 "
                    f"(거리 {dist_m/1000:.0f}km)"
                )

    # ── 3단계: 아군 방어 TEWA ─────────────────────────────────────────────────

    def _friendly_defense(self):
        """
        다층 방어 (enable_layered_defense=True, 기본 ON):
          KDX-III → KDX-II → FFX 순서로 위협당 1발씩 배정.
          함정 우선순위 정렬 후 첫 번째 가용 함정이 교전.

        CEC 사전 동시 배정 (enable_cec_preassign=True, 기본 OFF):
          탐지 즉시 1차+2차 함정 동시 발사. 위협당 최대 2발 허용.
          1차 성공 시 2차 SAM은 표적 소멸로 자동 종료.
        """
        cec     = self.cfg.get('enable_cec_preassign', False)
        max_sams = 2 if cec else 1

        # 다층 방어 우선순위 정렬 (KDX-III=0, KDX-II=1, FFX=2, 나머지=99)
        sorted_ships = sorted(
            [s for s in self.friendly_ships if s.alive],
            key=lambda s: SHIP_LAYER_PRI.get(s.ship_type, 99)
        )

        # (A) 적 대함 미사일 요격 (MissileObj enemy_strike)
        for m in self.missiles:
            if not m.alive or m.mtype != 'enemy_strike':
                continue
            sams_on = sum(
                1 for s in self.missiles
                if s.alive and s.target is m and s.mtype == 'friendly_sam'
            )
            if sams_on >= max_sams:
                continue

            shots = 0
            for ship in sorted_ships:
                if sams_on + shots >= max_sams:
                    break
                dist_m = ship.pos.dist_to(m.pos)
                wpn    = self._select_defense_wpn(ship, m, dist_m)
                if not wpn or ship.channels_used >= ship.max_channels:
                    continue
                if ship.inventory.get(wpn, 0) <= 0:
                    continue
                self._launch_friendly_sam(ship, wpn, m, dist_m, is_aa=False)
                shots += 1

        # (B) 적 항공기 직접 요격 (EnemyThreatObj is_aircraft)
        for et in self.enemy_threats:
            if not et.alive or not et.is_aircraft or et.is_retreating:
                continue
            sams_on = sum(
                1 for s in self.missiles
                if s.alive and s.target is et and s.mtype == 'friendly_sam'
            )
            if sams_on >= max_sams:
                continue

            shots = 0
            for ship in sorted_ships:
                if sams_on + shots >= max_sams:
                    break
                dist_m = ship.pos.dist_to(et.pos)
                wpn    = self._select_aa_wpn(ship, et, dist_m)
                if not wpn or ship.channels_used >= ship.max_channels:
                    continue
                if ship.inventory.get(wpn, 0) <= 0:
                    continue
                self._launch_friendly_sam(ship, wpn, et, dist_m, is_aa=True)
                shots += 1

    def _launch_friendly_sam(self, ship: FriendlyShipObj, wpn: str, target,
                              dist_m: float, is_aa: bool):
        wpn_info = FRIENDLY_DB[wpn]
        ship.inventory[wpn]   -= 1
        ship.channels_used    += 1
        ship.total_cost       += wpn_info['cost_usd']
        # 포팅 D: 발사 통계
        self.stats['total_missiles_fired'] += 1
        if self.stats['t_first_fire'] < 0:
            self.stats['t_first_fire'] = self.t
        sam = MissileObj(
            mtype    = 'friendly_sam',
            name     = wpn,
            pos      = ship.pos,
            target   = target,
            speed_ms = wpn_info['speed_ms'],
            pk_base  = wpn_info['pk_dist']['mean'],
            owner_id = id(ship),
            t_spawn  = self.t,
        )
        self.missiles.append(sam)
        prefix = '[대공 방어]' if is_aa else '[방어]'
        tgt_name = target.name if hasattr(target, 'name') else target.preset_name
        self._log(f"{prefix} {ship.name} -> {wpn} 발사 -> {tgt_name} (거리 {dist_m/1000:.1f}km)")

    def _select_defense_wpn(self, ship: FriendlyShipObj, m: MissileObj,
                            dist_m: float) -> Optional[str]:
        """미사일 위협 요격 무기 선택. 고도·유형 인식."""
        inv = ship.inventory
        alt          = m.altitude_m
        is_hgv       = m.is_hgv
        is_qbm       = m.is_qbm
        is_ballistic = m.is_ballistic

        # HGV / 고고도 탄도 중간단계 → SM-3
        if (is_hgv or (is_ballistic and alt >= 40_000)) and dist_m <= 1_200_000:
            if inv.get('SM-3 Block IIA', 0) > 0:
                return 'SM-3 Block IIA'

        # QBM (저고도 기동탄도) → SM-6 우선 (SM-3 무효)
        if is_qbm and dist_m <= 240_000:
            if inv.get('SM-6', 0) > 0:
                return 'SM-6'

        # 근거리→원거리 표준 다층
        if dist_m <= 2_000   and inv.get('CIWS-II (Phalanx)', 0) > 0: return 'CIWS-II (Phalanx)'
        if dist_m <= 9_000   and inv.get('RIM-116 RAM',        0) > 0: return 'RIM-116 RAM'
        if dist_m <= 170_000 and inv.get('SM-2 Block IIIB',    0) > 0: return 'SM-2 Block IIIB'
        if dist_m <= 240_000 and inv.get('SM-6',               0) > 0: return 'SM-6'
        if dist_m <= 1_200_000 and inv.get('SM-3 Block IIA',   0) > 0: return 'SM-3 Block IIA'
        return None

    def _select_aa_wpn(self, ship: FriendlyShipObj, et: EnemyThreatObj,
                       dist_m: float) -> Optional[str]:
        """항공기 목표 대공 무기 선택 (고도 반영)."""
        inv = ship.inventory
        alt = et.altitude_m

        if alt >= 10_000:
            if dist_m <= 170_000 and inv.get('SM-2 Block IIIB', 0) > 0: return 'SM-2 Block IIIB'
            if dist_m <= 240_000 and inv.get('SM-6',            0) > 0: return 'SM-6'
        if dist_m <= 9_000   and inv.get('RIM-116 RAM',        0) > 0: return 'RIM-116 RAM'
        if dist_m <= 170_000 and inv.get('SM-2 Block IIIB',    0) > 0: return 'SM-2 Block IIIB'
        if dist_m <= 240_000 and inv.get('SM-6',               0) > 0: return 'SM-6'
        if dist_m <= 1_200_000 and inv.get('SM-3 Block IIA',   0) > 0: return 'SM-3 Block IIA'
        return None

    # ── 4단계: 아군 공격 TEWA ─────────────────────────────────────────────────

    def _friendly_strike(self):
        """
        수상함 → 해성/하푼 (strike_inventory)
        잠수함 → 홍상어/청상어 (inventory)
        """
        for ship in self.friendly_ships:
            if not ship.alive:
                continue

            for et in self.enemy_threats:
                if not et.alive:
                    continue
                if not (et.is_ship or et.is_sub):
                    continue

                dist_m   = ship.pos.dist_to(et.pos)
                category = et.category
                if dist_m > self._detect_range_m(ship, category):
                    continue

                if et.is_ship:
                    en_route = sum(
                        1 for m in self.missiles
                        if m.alive and m.target is et and m.mtype == 'friendly_strike'
                    )
                    if en_route >= 2:
                        continue
                    wpn = self._select_strike_wpn(ship, dist_m)
                    if not wpn:
                        continue
                    wpn_info = FRIENDLY_STRIKE_DB[wpn]
                    ship.strike_inventory[wpn] -= 1
                    ship.total_cost += wpn_info['cost_usd']
                    self.missiles.append(MissileObj(
                        mtype    = 'friendly_strike',
                        name     = wpn,
                        pos      = ship.pos,
                        target   = et,
                        speed_ms = wpn_info['speed_ms'],
                        pk_base  = wpn_info['pk_base'],
                        owner_id = id(ship),
                        t_spawn  = self.t,
                    ))
                    self._log(
                        f"[공격] {ship.name} -> {wpn} -> {et.preset_name} "
                        f"(거리 {dist_m/1000:.0f}km)"
                    )

                elif et.is_sub:
                    en_route = sum(
                        1 for m in self.missiles
                        if m.alive and m.target is et and m.mtype == 'friendly_strike'
                    )
                    if en_route >= 1:
                        continue
                    wpn = self._select_asw_wpn(ship, dist_m)
                    if not wpn:
                        continue
                    wpn_info = FRIENDLY_DB[wpn]
                    ship.inventory[wpn] -= 1
                    ship.total_cost += wpn_info['cost_usd']
                    self.missiles.append(MissileObj(
                        mtype    = 'friendly_strike',
                        name     = wpn,
                        pos      = ship.pos,
                        target   = et,
                        speed_ms = wpn_info['speed_ms'],
                        pk_base  = wpn_info['pk_dist']['mean'],
                        owner_id = id(ship),
                        t_spawn  = self.t,
                    ))
                    self._log(
                        f"[대잠 공격] {ship.name} -> {wpn} -> {et.preset_name} "
                        f"(거리 {dist_m/1000:.1f}km)"
                    )

    # ── 4.5단계: 항공 자산 대잠 (포팅 C) ─────────────────────────────────────

    def _aircraft_asw(self):
        """
        등록된 항공 자산(헬기/초계기)이 잠수함 탐지 범위 내 목표를 확인하고
        sortie 준비 완료 시 어뢰를 투하한다.
        - 날씨·사거리·탑재량·쿨다운 체크
        - 어뢰는 목표 근방(±300m)에서 스폰 (항공기가 직접 투하하는 방식)
        - 소노부이: 탐지 거리에 sonobuoy_detect_bonus_km 추가
        """
        primary = self._primary()
        for ac in self.aircraft:
            if ac.payload_remaining <= 0:
                continue
            if self.t < ac.t_available:
                continue
            wx_limits = ac.info.get('weather_limits', {})
            if not wx_limits.get(self.cfg.get('weather', '맑음 (주간)'), True):
                continue

            for et in self.enemy_threats:
                if not et.alive or not et.is_sub:
                    continue
                # 이미 어뢰가 이 잠수함으로 향하고 있으면 패스
                already = any(
                    m.alive and m.target is et and m.mtype == 'friendly_strike'
                    for m in self.missiles
                )
                if already:
                    continue

                # 사거리 체크 (육상기지: 기지→작전해역 거리 추가)
                dist_to_sub = primary.pos.dist_to(et.pos)
                total_dist  = dist_to_sub
                if ac.info.get('base_type') == 'land':
                    total_dist += ac.info.get('base_dist_km', 0) * 1000
                if total_dist > ac.info['range_km'] * 1000:
                    continue

                # 소나 탐지 + 소노부이 보너스
                detect_m = self._detect_range_m(primary, '대잠')
                bonus_m  = ac.info.get('sonobuoy_detect_bonus_km', 0) * 1000
                if dist_to_sub > detect_m + bonus_m:
                    continue

                # 어뢰 투하 (목표 근방 스폰 — 항공기 직접 투하)
                wpn_name = ac.info['payload_wpn']
                wpn_info = FRIENDLY_DB[wpn_name]
                pk       = min(wpn_info['pk_dist']['mean'] + ac.info.get('pk_bonus', 0.0), 0.98)

                ac.payload_remaining -= 1
                ac.sorties           += 1
                ac.total_cost        += ac.info['cost_usd']

                drop_pos = Vec2(
                    et.pos.x + random.uniform(-300, 300),
                    et.pos.y + random.uniform(-300, 300),
                )
                m = MissileObj(
                    mtype    = 'friendly_strike',
                    name     = f"{wpn_name}({ac.name})",
                    pos      = drop_pos,
                    target   = et,
                    speed_ms = wpn_info['speed_ms'],
                    pk_base  = pk,
                    owner_id = id(ac),
                    t_spawn  = self.t,
                )
                m.is_torpedo = True
                self.missiles.append(m)

                # 다음 출격 가능 시각 = 지금 + 준비시간 + 비행시간
                fly_s            = total_dist / max(ac.info['speed_ms'], 1)
                ac.t_available   = self.t + ac.info['sortie_time_s'] + fly_s

                craft_type = '초계기' if ac.info.get('base_type') == 'land' else '헬기'
                self._log(
                    f"[항공 대잠] {ac.name}({craft_type}) 출격 → {et.preset_name} "
                    f"(거리 {dist_to_sub/1000:.0f}km) | {wpn_name} Pk={pk:.2f} 투하 "
                    f"| 잔여 {ac.payload_remaining}발"
                )
                break  # 한 tick당 한 표적만 공격

    def _select_strike_wpn(self, ship: FriendlyShipObj, dist_m: float) -> Optional[str]:
        for wpn in ['해성-II', '해성-I', '하푼 Block II']:
            if ship.strike_inventory.get(wpn, 0) <= 0:
                continue
            if dist_m <= FRIENDLY_STRIKE_DB[wpn]['range_km'] * 1000:
                return wpn
        return None

    def _select_asw_wpn(self, ship: FriendlyShipObj, dist_m: float) -> Optional[str]:
        for wpn in ['홍상어 (대잠)', '청상어 (경어뢰)', 'Mk.46 경어뢰']:
            if ship.inventory.get(wpn, 0) <= 0:
                continue
            if dist_m <= FRIENDLY_DB[wpn]['range_km'] * 1000:
                return wpn
        return None

    # ── 5단계: 적 SAM 방어 (수상함 전용) ─────────────────────────────────────

    def _enemy_defense(self):
        for et in self.enemy_threats:
            if not et.alive or not et.is_ship or not et.sam_inventory:
                continue

            for m in self.missiles:
                if not m.alive or m.mtype != 'friendly_strike':
                    continue
                if m.target is not et:
                    continue

                already = any(
                    s.alive and s.target is m and s.mtype == 'enemy_sam'
                    for s in self.missiles
                )
                if already:
                    continue
                if et.sam_channels_used >= et.sam_max_channels:
                    continue

                dist_m   = et.pos.dist_to(m.pos)
                sam_name = et.select_sam(dist_m)
                if not sam_name:
                    continue

                sam_info = ENEMY_SAM_DB[sam_name]
                et.sam_inventory[sam_name]  -= 1
                et.sam_channels_used        += 1

                self.missiles.append(MissileObj(
                    mtype    = 'enemy_sam',
                    name     = sam_name,
                    pos      = et.pos,
                    target   = m,
                    speed_ms = sam_info['speed_ms'],
                    pk_base  = sam_info['pk'],
                    owner_id = id(et),
                    t_spawn  = self.t,
                ))
                self._log(
                    f"[적 방어] {et.preset_name} -> {sam_name} 발사 "
                    f"(거리 {dist_m/1000:.1f}km)"
                )

    # ── 6단계: 교전 결과 판정 ─────────────────────────────────────────────────

    def _check_intercepts(self):
        for sam in list(self.missiles):
            if not sam.alive:
                continue
            if sam.mtype not in ('friendly_sam', 'enemy_sam'):
                continue

            tgt = sam.target
            if not tgt.alive:
                sam.alive = False
                continue

            in_range = sam.hit or (sam.pos.dist_to(tgt.pos) <= INTERCEPT_DIST_M)
            if not in_range:
                continue

            sam.alive = False
            tgt_name  = tgt.name if hasattr(tgt, 'name') else str(tgt)

            # 포팅 B: ECM 재밍 + 종말 회피 Pk 보정 (아군 SAM vs 적 미사일)
            eff_pk = sam.pk_base
            if sam.mtype == 'friendly_sam' and isinstance(tgt, MissileObj):
                remaining_m = sam.pos.dist_to(tgt.pos)
                if self.cfg.get('enable_ecm', True) and not tgt.is_ballistic and not tgt.is_hgv:
                    eff_ecm = 0.30  # 아군 함정 ECM 표준 효과
                    ecm_f = 1.0 - eff_ecm * (ECM_REF_RANGE_M / max(remaining_m, 5_000))
                    eff_pk *= max(0.50, min(1.0, ecm_f))
                if self.cfg.get('enable_evasion', True) and remaining_m < 20_000:
                    eff_pk *= tgt.terminal_evasion_factor

            if random.random() < eff_pk:
                tgt.alive       = False
                tgt.intercepted = True
                tgt.t_intercept = self.t

                if sam.mtype == 'friendly_sam':
                    self._log(f"[요격 성공] {sam.name} -> {tgt_name} 격추 ({self.t:.0f}s)")
                    # MissileObj만 intercepted_threats에 집계 (BUG 수정: 항공기 플랫폼 격추는 enemy_ships_destroyed로)
                    if isinstance(tgt, MissileObj):
                        self.stats['intercepted_threats'] += 1
                    for ship in self.friendly_ships:
                        if id(ship) == sam.owner_id:
                            ship.channels_used = max(0, ship.channels_used - 1)
                else:
                    self._log(f"[적 요격 성공] {sam.name} -> {tgt_name} 격추 ({self.t:.0f}s)")
                    for et in self.enemy_threats:
                        if id(et) == sam.owner_id:
                            et.sam_channels_used = max(0, et.sam_channels_used - 1)
            else:
                if sam.mtype == 'friendly_sam':
                    self._log(f"[요격 실패] {sam.name} -> {tgt_name} 통과")
                    for ship in self.friendly_ships:
                        if id(ship) == sam.owner_id:
                            ship.channels_used = max(0, ship.channels_used - 1)
                else:
                    self._log(f"[적 요격 실패] {sam.name} -> {tgt_name} 통과")
                    for et in self.enemy_threats:
                        if id(et) == sam.owner_id:
                            et.sam_channels_used = max(0, et.sam_channels_used - 1)

    def _check_hits(self):
        for m in self.missiles:
            # hit=True: 목표 위치 도달. alive=False 또는 intercepted=True면 이미 처리된 미사일.
            if not m.hit or not m.alive or m.intercepted:
                continue

            m.alive = False  # 도달 미사일 소모 (결과 무관)

            if m.mtype == 'enemy_strike':
                tgt = m.target
                if isinstance(tgt, FriendlyShipObj) and tgt.alive:
                    # 포팅 B: 음향 기만기 AN/SLQ-25 — 어뢰 전용
                    if m.is_torpedo and self.cfg.get('enable_decoy', True):
                        if tgt.decoy_stock > 0:
                            tgt.decoy_stock -= 1
                            if random.random() < DECOY_PK:
                                self._log(
                                    f"[기만기] {tgt.name} 기만기 성공 — {m.name} 회피 "
                                    f"(잔여 {tgt.decoy_stock}발)")
                                continue
                    # 포팅 B: 함정 회피 기동 — 어뢰 전용
                    if m.is_torpedo and self.cfg.get('enable_evasion', True):
                        if random.random() < SHIP_EVASION_PK:
                            self._log(f"[회피] {tgt.name} 회피 기동 성공 — {m.name}")
                            continue
                    if random.random() < m.pk_base:
                        tgt.take_hit(m.name, self.t)
                        self.stats['friendly_hits'] += 1
                        self._log(f"[피격] {tgt.name} <- {m.name} 명중! (HP {tgt.hp})")
                    else:
                        self._log(f"[피격 실패] {m.name} -> {tgt.name} 근접 불발")

            elif m.mtype == 'friendly_strike':
                tgt = m.target
                if isinstance(tgt, EnemyThreatObj) and tgt.alive:
                    # 포팅 B: 적 자체방어 — CIWS 요격 → 채프/플레어
                    eff_pk = m.pk_base
                    if self.cfg.get('enable_selfdefense', True):
                        ciws_pk = tgt.info.get('enemy_ciws_pk', 0.0)
                        if ciws_pk > 0 and random.random() < ciws_pk:
                            self._log(f"[적 CIWS] {tgt.preset_name} CIWS 요격 — {m.name}")
                            continue
                        sdpk   = tgt.info.get('self_defense_pk', 0.0)
                        eff_pk = m.pk_base * (1.0 - sdpk)
                    if random.random() < eff_pk:
                        tgt.take_hit(m.name, self.t)
                        self.stats['enemy_hits'] += 1
                        status = '격침' if not tgt.alive else f'손상 (HP {tgt.hp})'
                        self._log(f"[적 피격] {tgt.preset_name} <- {m.name} 명중! {status}")
                    else:
                        self._log(f"[적 피격 실패] {m.name} -> {tgt.preset_name} 회피")

    # ── 7단계: 프레임 기록 ────────────────────────────────────────────────────

    def _record_frame(self):
        frame = SimFrame(self.t)
        for s in self.friendly_ships:
            frame.friendly_ships.append((s.name, s.pos.x, s.pos.y, s.alive, s.hp))
            frame.ship_channels.append((s.name, s.channels_used, s.max_channels))
        for et in self.enemy_threats:
            frame.enemy_ships.append(
                (et.uid, et.preset_name, et.pos.x, et.pos.y, et.alive, et.hp))
        for m in self.missiles:
            if m.alive:
                frame.missiles.append((m.uid, m.pos.x, m.pos.y, m.mtype, m.name))
        frame.events = list(self._tick_events)
        self.frames.append(frame)
        self._tick_events.clear()

    # ── 종료 조건 ─────────────────────────────────────────────────────────────

    def _is_over(self) -> bool:
        active_threats = [m for m in self.missiles if m.alive and m.mtype == 'enemy_strike']
        # 이탈 중인 항공기는 이미 발사 완료 → 위협 종료로 간주
        enemy_active   = [et for et in self.enemy_threats
                          if et.alive and not (et.is_aircraft and et.is_retreating)]

        if not active_threats and not enemy_active:
            self._log("[종료] 교전 종료 - 모든 위협 소진/격침/이탈")
            return True
        if all(not s.alive for s in self.friendly_ships):
            self._log("[종료] 아군 전멸")
            return True
        return False

    # ── 메인 루프 ─────────────────────────────────────────────────────────────

    def run(self) -> dict:
        while self.t <= MAX_SIM_TIME:
            self._update_positions()
            self._enemy_fire()
            self._friendly_defense()
            self._friendly_strike()
            self._aircraft_asw()        # 포팅 C: 항공 대잠
            self._enemy_defense()
            self._check_intercepts()
            self._check_hits()

            self.missiles = [m for m in self.missiles
                             if m.alive and not m.intercepted]

            self._record_frame()

            # 포팅 D: 동시 위협 수 peak 추적
            alive_count = sum(
                1 for et in self.enemy_threats
                if et.alive and not (et.is_aircraft and et.is_retreating)
            )
            if alive_count > self.stats['peak_concurrent_threats']:
                self.stats['peak_concurrent_threats'] = alive_count

            if self._is_over():
                break

            self.t += DT

        return self._compile()

    def _compile(self) -> dict:
        self.stats['friendly_ships_lost']   = sum(1 for s in self.friendly_ships if not s.alive)
        # 이탈 항공기(alive=False, is_retreating=True, intercepted=False)는 "격침" 아님
        self.stats['enemy_ships_destroyed'] = sum(
            1 for et in self.enemy_threats
            if not et.alive and (et.intercepted or not et.is_aircraft)
        )
        # 포팅 C: 항공 자산 출격 횟수 + 비용 합산
        self.stats['aircraft_sorties'] = sum(ac.sorties for ac in self.aircraft)
        self.stats['total_cost']       = (
            sum(s.total_cost for s in self.friendly_ships)
            + sum(ac.total_cost for ac in self.aircraft)
        )

        intercept_rate = (
            self.stats['intercepted_threats'] / self.stats['total_threats']
            if self.stats['total_threats'] > 0 else 1.0
        )

        # 포팅 D: 잔여 재고 합산 (REQ-07), 총 채널 수 (REQ-08)
        remaining_inv: dict = {}
        for s in self.friendly_ships:
            for wpn, cnt in s.inventory.items():
                remaining_inv[wpn] = remaining_inv.get(wpn, 0) + cnt
        total_channels = sum(s.max_channels for s in self.friendly_ships)

        return {
            **self.stats,
            'intercept_rate':    intercept_rate,
            'sim_time':          self.t,
            'frames':            self.frames,
            'log':               self._log_entries,
            'friendly_ships':    self.friendly_ships,
            'enemy_ships':       self.enemy_threats,   # 하위 호환 키 유지
            'remaining_inventory': remaining_inv,
            'total_channels':      total_channels,
        }


# ════════════════════════════════════════════════════════════════════════════
#  탐지거리 자동 계산 (함대 편성 + 날씨 + 데이터링크)
# ════════════════════════════════════════════════════════════════════════════

def calculate_fleet_detect_ranges(fleet_preset_name: str, weather: str) -> dict:
    """
    함대 편성과 날씨를 기반으로 탐지거리를 자동 계산한다.

    데이터링크 원칙:
      - 한국 해군 Link-16/Link-11 적용 — 편대 내 최고 성능 센서 기준 공유
      - 대공·대함 : 편대 내 max(sensor_km['대공'/'대함']) × radar_factor
      - 대잠       : 편대 내 max(sensor_km['대잠']) × sonar_factor
        (황사는 소나에 영향 없음, 풍랑·폭풍은 해상 소음으로 급감)

    반환 예시:
      {'대공': 1140, '대함': 41, '대잠': 30,
       'leading_ship': 'KDX-III', 'radar_factor': 0.95, 'sonar_factor': 0.60}
    """
    preset = FLEET_PRESETS.get(fleet_preset_name, [])
    w = WEATHER_DB.get(weather, WEATHER_DB['맑음 (주간)'])
    rf = w.get('radar_factor', w.get('detect_range_factor', 1.0))
    sf = w.get('sonar_factor', w.get('detect_range_factor', 1.0))

    max_air = 0; max_surface = 0; max_sub = 0
    leading = '(없음)'
    for ship in preset:
        spec = SHIP_DB.get(ship['type'], {})
        s = spec.get('sensor_km', {})
        air = s.get('대공', 0)
        if air > max_air:
            max_air = air
            leading = ship.get('name', ship['type'])
        max_surface = max(max_surface, s.get('대함', 0))
        max_sub     = max(max_sub,     s.get('대잠', 0))

    return {
        '대공':         max(1, round(max_air     * rf)),
        '대함':         max(1, round(max_surface * rf)),
        '대잠':         max(1, round(max_sub     * sf)),
        'leading_ship': leading,
        'radar_factor': rf,
        'sonar_factor': sf,
    }


# ════════════════════════════════════════════════════════════════════════════
#  외부 API
# ════════════════════════════════════════════════════════════════════════════

def run_v7_simulation(cfg: dict) -> dict:
    # 탐지거리 자동 계산 (함대 + 날씨 기반, 수동 override 없을 때)
    if not cfg.get('detect_km_manual', False):
        ranges = calculate_fleet_detect_ranges(
            cfg.get('fleet_preset', '단독 작전'),
            cfg.get('weather', '맑음 (주간)'))
        cfg = dict(cfg)
        cfg['detect_km']     = ranges['대공']
        cfg['sub_detect_km'] = ranges['대잠']
    return TimeStepEngine(cfg).run()


# ════════════════════════════════════════════════════════════════════════════
#  몬테카를로 분석
# ════════════════════════════════════════════════════════════════════════════

def monte_carlo_v7(cfg: dict, n: int = 200, desc: str = '') -> dict:
    """
    run_v7_simulation을 n회 반복해 통계를 집계한다.

    반환 dict 키:
      intercept_rates   : list[float]   — 회차별 요격률
      friendly_hits     : list[int]
      enemy_destroyed   : list[int]
      friendly_lost     : list[int]
      total_costs       : list[float]
      mean_intercept    : float
      std_intercept     : float
      full_pass_rate    : float          — 요격률 1.0 비율
    """
    rates, f_hits, e_dest, f_lost, costs = [], [], [], [], []

    step = max(1, n // 5)
    if desc:
        print(f'  [{desc}] {n}회 MC 시작... ', end='', flush=True)

    for i in range(n):
        r = run_v7_simulation(cfg)
        rates.append(r['intercept_rate'])
        f_hits.append(r['friendly_hits'])
        e_dest.append(r['enemy_ships_destroyed'])
        f_lost.append(r['friendly_ships_lost'])
        costs.append(r['total_cost'])
        if desc and (i + 1) % step == 0:
            print(f'{(i + 1) * 100 // n}%', end=' ', flush=True)

    if desc:
        print('완료')

    arr = np.array(rates)
    return {
        'intercept_rates':  rates,
        'friendly_hits':    f_hits,
        'enemy_destroyed':  e_dest,
        'friendly_lost':    f_lost,
        'total_costs':      costs,
        'mean_intercept':   float(arr.mean()),
        'std_intercept':    float(arr.std()),
        'full_pass_rate':   float((arr == 1.0).mean()),
        'n':                n,
    }


# ════════════════════════════════════════════════════════════════════════════
#  포팅 D: REQ 요구조건 판정
# ════════════════════════════════════════════════════════════════════════════

REQ_ITEMS_V7 = [
    {'id': 'REQ-01', 'name': '전탄 요격 (단일)',   'desc': '단일 시뮬에서 모든 위협 요격'},
    {'id': 'REQ-02', 'name': '응답시간 충족',      'desc': f'첫 SAM 발사 ≤ {MAX_RESPONSE_TIME_S}s'},
    {'id': 'REQ-03', 'name': '요격 가능성 확인',   'desc': 'MC 평균 요격률 > 0%'},
    {'id': 'REQ-04', 'name': '생존율 ≥ 90%',       'desc': 'MC 완전 요격 성공률 ≥ 90%'},
    {'id': 'REQ-05', 'name': '아군 무피격 (단일)', 'desc': '단일 시뮬에서 아군 피격 0회'},
    {'id': 'REQ-06', 'name': '다층 방어 확인',     'desc': '발사 미사일 수 ≥ 위협 수 (재교전 여력)'},
    {'id': 'REQ-07', 'name': '재고 충분',          'desc': '교전 후 주요 무기 잔여 ≥ 1발'},
    {'id': 'REQ-08', 'name': '채널 한계 미초과',   'desc': '최대 동시 위협 ≤ 편대 총 채널'},
]


def evaluate_req_v7(result: dict, mc: dict) -> tuple:
    """REQ_ITEMS_V7 8항목 판정. (verdicts: list[bool], details: list[str]) 반환."""
    ir       = result['intercept_rate']
    tfirst   = result.get('t_first_fire', -1.0)
    fired    = result.get('total_missiles_fired', 0)
    threats  = result['total_threats']
    f_hits   = result['friendly_hits']
    peak_et  = result.get('peak_concurrent_threats', 0)
    tot_ch   = result.get('total_channels', 16)
    rem_inv  = result.get('remaining_inventory', {})

    req1 = ir >= 1.0
    req2 = 0 <= tfirst <= MAX_RESPONSE_TIME_S
    req3 = mc['mean_intercept'] > 0.0
    req4 = mc['full_pass_rate'] >= 0.90
    req5 = f_hits == 0
    req6 = (fired >= threats) if threats > 0 else True
    req7 = any(v > 0 for v in rem_inv.values())
    req8 = peak_et <= tot_ch

    verdicts = [req1, req2, req3, req4, req5, req6, req7, req8]
    details  = [
        f"요격률 {ir:.1%} {'≥' if req1 else '<'} 100%",
        f"첫 발사 {tfirst:.0f}s ≤ {MAX_RESPONSE_TIME_S}s" if tfirst >= 0 else "발사 없음",
        f"MC 평균 요격률 {mc['mean_intercept']:.1%}",
        f"MC 완전 성공률 {mc['full_pass_rate']:.1%} {'≥' if req4 else '<'} 90%",
        f"아군 피격 {f_hits}회",
        f"발사 {fired}발 / 위협 {threats}개",
        f"잔여 {'확보됨' if req7 else '전량 소진!'} ({sum(rem_inv.values())}발)",
        f"최대 동시 위협 {peak_et} ≤ 채널 {tot_ch}",
    ]
    return verdicts, details


# ════════════════════════════════════════════════════════════════════════════
#  포팅 D: 날씨별 시나리오 비교
# ════════════════════════════════════════════════════════════════════════════

_SCENARIO_WEATHERS = [
    ('최선 (맑음)',  '맑음 (주간)'),
    ('평균 (흐림)',  '흐림 (박무)'),
    ('최악 (폭풍)',  '폭풍 (해상 악화)'),
]


def scenario_comparison_v7(cfg: dict, n: int = 200) -> dict:
    """날씨 3종 MC 비교. {label: {'mean_intercept', 'full_pass_rate', 'mean_cost', 'n'}} 반환."""
    results = {}
    for label, weather in _SCENARIO_WEATHERS:
        c = dict(cfg)
        c['weather'] = weather
        mc = monte_carlo_v7(c, n=n, desc=f'시나리오: {label}')
        results[label] = {
            'mean_intercept': mc['mean_intercept'],
            'full_pass_rate': mc['full_pass_rate'],
            'mean_cost':      float(np.mean(mc['total_costs'])),
            'n':              n,
        }
    return results


# ════════════════════════════════════════════════════════════════════════════
#  포팅 D: A vs B 시나리오 비교
# ════════════════════════════════════════════════════════════════════════════

def compare_ab_v7(cfg_a: dict, cfg_b: dict, n: int = 200) -> dict:
    """
    두 cfg로 MC를 각각 실행해 비교 dict를 반환.
    반환: {'a': mc_dict, 'b': mc_dict, 'delta_intercept': float, 'delta_cost': float}
    """
    mc_a = monte_carlo_v7(cfg_a, n=n, desc='A 시나리오')
    mc_b = monte_carlo_v7(cfg_b, n=n, desc='B 시나리오')
    return {
        'a':               mc_a,
        'b':               mc_b,
        'delta_intercept': mc_b['mean_intercept'] - mc_a['mean_intercept'],
        'delta_cost':      float(np.mean(mc_b['total_costs'])) - float(np.mean(mc_a['total_costs'])),
    }


# ════════════════════════════════════════════════════════════════════════════
#  포팅 D: 시나리오 저장 / 불러오기
# ════════════════════════════════════════════════════════════════════════════

import json as _json


def save_scenario_v7(cfg: dict, path: str):
    """cfg를 JSON으로 저장. 직렬화 불가능한 값은 제외."""
    serializable = {}
    for k, v in cfg.items():
        try:
            _json.dumps(v)
            serializable[k] = v
        except (TypeError, ValueError):
            pass
    with open(path, 'w', encoding='utf-8') as f:
        _json.dump(serializable, f, ensure_ascii=False, indent=2)


def load_scenario_v7(path: str) -> dict:
    """JSON 파일에서 cfg를 불러온다."""
    with open(path, 'r', encoding='utf-8') as f:
        return _json.load(f)


# ════════════════════════════════════════════════════════════════════════════
#  PNG 차트 생성
# ════════════════════════════════════════════════════════════════════════════

_BG   = '#0a0e1a'
_GRID = '#1e2a3a'
_ACC  = '#3498db'

def _ax_style(ax, title: str):
    ax.set_facecolor(_BG)
    ax.tick_params(colors='#aab', labelsize=8)
    for sp in ax.spines.values():
        sp.set_color(_GRID)
    ax.set_title(title, color='#dde', fontsize=9, fontweight='bold', pad=6)


def plot_v7(result: dict, mc: dict, cfg: dict,
            img_path: str = '이지스_기동전단_v7_분석.png') -> str:
    """
    단일 시뮬 결과(result) + MC 통계(mc)를 6개 서브플롯으로 시각화.
    img_path에 저장 후 경로 반환.
    """
    fig = plt.figure(figsize=(16, 10), facecolor=_BG)
    fig.suptitle(
        f"이지스 기동전단 통합 방어 시뮬레이터 v7.0\n"
        f"시나리오: {cfg.get('fleet_preset','?')} | "
        f"날씨: {cfg.get('weather','?')} | "
        f"MC {mc['n']}회",
        color='white', fontsize=13, fontweight='bold', y=0.98,
    )

    gs = gridspec.GridSpec(2, 3, figure=fig, hspace=0.45, wspace=0.35,
                           left=0.07, right=0.97, top=0.90, bottom=0.08)

    # ── (0,0) 요격률 히스토그램 ──────────────────────────────────────────────
    ax0 = fig.add_subplot(gs[0, 0])
    _ax_style(ax0, '요격률 분포 (MC)')
    ax0.hist(mc['intercept_rates'], bins=20, color=_ACC, edgecolor='#0a0e1a', alpha=0.85)
    ax0.axvline(mc['mean_intercept'], color='#e74c3c', lw=1.5, ls='--',
                label=f"평균 {mc['mean_intercept']:.1%}")
    ax0.set_xlabel('요격률', color='#aab', fontsize=8)
    ax0.set_ylabel('빈도', color='#aab', fontsize=8)
    ax0.legend(fontsize=7, facecolor=_BG, labelcolor='white', edgecolor=_GRID)
    ax0.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{v:.0%}'))

    # ── (0,1) 아군 피격 분포 ─────────────────────────────────────────────────
    ax1 = fig.add_subplot(gs[0, 1])
    _ax_style(ax1, '아군 피격 횟수 분포 (MC)')
    ax1.hist(mc['friendly_hits'], bins=range(0, max(mc['friendly_hits']) + 2),
             color='#e74c3c', edgecolor='#0a0e1a', alpha=0.85, align='left')
    ax1.set_xlabel('피격 횟수', color='#aab', fontsize=8)
    ax1.set_ylabel('빈도', color='#aab', fontsize=8)

    # ── (0,2) 적 격침 분포 ───────────────────────────────────────────────────
    ax2 = fig.add_subplot(gs[0, 2])
    _ax_style(ax2, '적 플랫폼 격침 수 분포 (MC)')
    max_dest = max(mc['enemy_destroyed']) if mc['enemy_destroyed'] else 1
    ax2.hist(mc['enemy_destroyed'], bins=range(0, max_dest + 2),
             color='#2ecc71', edgecolor='#0a0e1a', alpha=0.85, align='left')
    ax2.set_xlabel('격침 수', color='#aab', fontsize=8)
    ax2.set_ylabel('빈도', color='#aab', fontsize=8)

    # ── (1,0) 무기 소모 현황 (단일 시뮬) ─────────────────────────────────────
    ax3 = fig.add_subplot(gs[1, 0])
    _ax_style(ax3, '무기 소모 현황 (단일 시뮬)')
    ships = result.get('friendly_ships', [])
    wpn_used: dict = {}
    for s in ships:
        spec = SHIP_DB.get(s.ship_type, {})
        default_inv = spec.get('default_inventory', {})
        for wpn, orig in default_inv.items():
            used = orig - s.inventory.get(wpn, orig)
            if used > 0:
                wpn_used[wpn] = wpn_used.get(wpn, 0) + used
    if wpn_used:
        labels = list(wpn_used.keys())
        values = [wpn_used[k] for k in labels]
        colors = [_ACC if i % 2 == 0 else '#5dade2' for i in range(len(labels))]
        bars = ax3.barh(labels, values, color=colors, edgecolor='#0a0e1a')
        ax3.bar_label(bars, padding=3, color='white', fontsize=7)
        ax3.set_xlabel('발사 수', color='#aab', fontsize=8)
        ax3.tick_params(axis='y', labelsize=7)
    else:
        ax3.text(0.5, 0.5, '발사 없음', color='#aab', ha='center', va='center',
                 transform=ax3.transAxes)

    # ── (1,1) 비용 분포 ──────────────────────────────────────────────────────
    ax4 = fig.add_subplot(gs[1, 1])
    _ax_style(ax4, '총 교전 비용 분포 (MC)')
    costs_m = [c / 1_000_000 for c in mc['total_costs']]
    ax4.hist(costs_m, bins=20, color='#f39c12', edgecolor='#0a0e1a', alpha=0.85)
    mean_m = np.mean(costs_m)
    ax4.axvline(mean_m, color='#e74c3c', lw=1.5, ls='--',
                label=f'평균 ${mean_m:.1f}M')
    ax4.set_xlabel('비용 (백만 USD)', color='#aab', fontsize=8)
    ax4.set_ylabel('빈도', color='#aab', fontsize=8)
    ax4.legend(fontsize=7, facecolor=_BG, labelcolor='white', edgecolor=_GRID)

    # ── (1,2) 핵심 수치 요약 ────────────────────────────────────────────────
    ax5 = fig.add_subplot(gs[1, 2])
    ax5.set_facecolor(_BG)
    ax5.axis('off')
    _ax_style(ax5, '핵심 수치 요약')

    enemy_count = sum(s.get('count', 1) for s in cfg.get('enemy_fleet', []))
    summary_lines = [
        ('적 편대 규모',     f"{enemy_count}기/척"),
        ('시뮬 종료 시각',   f"{result['sim_time']:.0f}s"),
        ('총 위협 수',       f"{result['total_threats']}발/기"),
        ('요격 성공 (단일)', f"{result['intercepted_threats']}발/기"),
        ('', ''),
        ('MC 평균 요격률',   f"{mc['mean_intercept']:.1%}"),
        ('MC 표준편차',      f"±{mc['std_intercept']:.1%}"),
        ('완전요격 비율',    f"{mc['full_pass_rate']:.1%}"),
        ('', ''),
        ('아군 피격 (단일)', f"{result['friendly_hits']}회"),
        ('적 격침 (단일)',   f"{result['enemy_ships_destroyed']}기/척"),
        ('아군 손실 (단일)', f"{result['friendly_ships_lost']}척"),
        ('총 비용 (단일)',   f"${result['total_cost']:,.0f}"),
    ]
    y = 0.97
    for label, val in summary_lines:
        if not label:
            y -= 0.04
            continue
        ax5.text(0.04, y, label, color='#7fb3d3', fontsize=8, transform=ax5.transAxes, va='top')
        ax5.text(0.96, y, val,   color='white',   fontsize=8, transform=ax5.transAxes, va='top', ha='right', fontweight='bold')
        y -= 0.072

    plt.savefig(img_path, dpi=150, bbox_inches='tight', facecolor=_BG)
    plt.close(fig)
    print(f"  그래프 저장: '{img_path}'")
    return img_path


# ════════════════════════════════════════════════════════════════════════════
#  Excel 보고서 생성
# ════════════════════════════════════════════════════════════════════════════

def save_excel_report_v7(result: dict, mc: dict, cfg: dict,
                          img_path: str = '',
                          xlsx_path: str = '이지스_기동전단_v7_보고서.xlsx'):
    """
    Sheet1: MC 통계 요약
    Sheet2: 무기 소모 현황
    Sheet3: 교전 로그
    Sheet4: PNG 차트 삽입 (이미지 있을 때)
    """
    wb = Workbook()
    tb = Border(**{s: Side(style='thin', color='CCCCCC')
                   for s in ('left', 'right', 'top', 'bottom')})

    def cs(ws, r, c, v, bold=False, bg=None, center=True, color='000000'):
        cell = ws.cell(row=r, column=c, value=v)
        cell.font      = Font(bold=bold, size=10, name='Arial', color=color)
        cell.alignment = Alignment(
            horizontal='center' if center else 'left',
            vertical='center', wrap_text=True,
        )
        cell.border = tb
        if bg:
            cell.fill = PatternFill('solid', start_color=bg)

    def title_row(ws, r, text, cols='A:F', bg='1A252F'):
        end_col = cols.split(':')[1]
        ws.merge_cells(f'A{r}:{end_col}{r}')
        cell = ws.cell(row=r, column=1, value=text)
        cell.font      = Font(bold=True, size=13, color='FFFFFF', name='Arial')
        cell.fill      = PatternFill('solid', start_color=bg)
        cell.alignment = Alignment(horizontal='center', vertical='center')
        ws.row_dimensions[r].height = 28

    def hdr(ws, r, headers, bg='2C3E50'):
        for j, h in enumerate(headers, 1):
            cell = ws.cell(row=r, column=j, value=h)
            cell.font      = Font(bold=True, size=10, color='FFFFFF', name='Arial')
            cell.fill      = PatternFill('solid', start_color=bg)
            cell.alignment = Alignment(horizontal='center', vertical='center')
            cell.border    = tb

    # ── Sheet1: MC 통계 요약 ─────────────────────────────────────────────────
    ws1 = wb.active
    ws1.title = 'MC 통계 요약'
    ws1.sheet_view.showGridLines = False
    for col, w in zip('ABCDEF', [20, 20, 18, 18, 18, 18]):
        ws1.column_dimensions[col].width = w

    title_row(ws1, 1, f'이지스 기동전단 v7.0 — MC {mc["n"]}회 통계 요약')
    hdr(ws1, 2, ['항목', '단일 시뮬', 'MC 평균', 'MC 표준편차', 'MC 최솟값', 'MC 최댓값'])

    rows = [
        ('요격률',
         f"{result['intercept_rate']:.1%}",
         f"{mc['mean_intercept']:.1%}",
         f"±{mc['std_intercept']:.1%}",
         f"{min(mc['intercept_rates']):.1%}",
         f"{max(mc['intercept_rates']):.1%}"),
        ('아군 피격',
         result['friendly_hits'],
         f"{np.mean(mc['friendly_hits']):.1f}",
         f"±{np.std(mc['friendly_hits']):.1f}",
         min(mc['friendly_hits']),
         max(mc['friendly_hits'])),
        ('적 격침',
         result['enemy_ships_destroyed'],
         f"{np.mean(mc['enemy_destroyed']):.1f}",
         f"±{np.std(mc['enemy_destroyed']):.1f}",
         min(mc['enemy_destroyed']),
         max(mc['enemy_destroyed'])),
        ('아군 함정 손실',
         result['friendly_ships_lost'],
         f"{np.mean(mc['friendly_lost']):.1f}",
         f"±{np.std(mc['friendly_lost']):.1f}",
         min(mc['friendly_lost']),
         max(mc['friendly_lost'])),
        ('총 비용 (USD)',
         f"${result['total_cost']:,.0f}",
         f"${np.mean(mc['total_costs']):,.0f}",
         f"±${np.std(mc['total_costs']):,.0f}",
         f"${min(mc['total_costs']):,.0f}",
         f"${max(mc['total_costs']):,.0f}"),
        ('완전 요격 비율',
         '—',
         f"{mc['full_pass_rate']:.1%}",
         '—', '—', '—'),
    ]
    for i, row in enumerate(rows):
        bg = 'D5F5E3' if i % 2 == 0 else 'EBF5FB'
        for j, val in enumerate(row, 1):
            cs(ws1, i + 3, j, val, bg=bg, center=(j > 1))

    # 시나리오 파라미터 블록
    ws1.cell(row=len(rows) + 5, column=1, value='【시나리오 파라미터】').font = Font(bold=True, size=11)
    params = [
        ('편대 프리셋',   cfg.get('fleet_preset', '?')),
        ('날씨',          cfg.get('weather', '?')),
        ('탐지 거리',     f"{cfg.get('detect_km', '?')} km"),
        ('해성-II 재고',  cfg.get('haesong2_stock', 0)),
        ('해성-I  재고',  cfg.get('haesong1_stock', 0)),
        ('하푼 재고',     cfg.get('harpoon_stock', 0)),
    ]
    for k, (label, val) in enumerate(params):
        cs(ws1, len(rows) + 6 + k, 1, label, center=False)
        cs(ws1, len(rows) + 6 + k, 2, val,   center=False)

    # ── Sheet2: 무기 소모 현황 ───────────────────────────────────────────────
    ws2 = wb.create_sheet('무기 소모 현황')
    ws2.sheet_view.showGridLines = False
    for col, w in zip('ABCDE', [24, 16, 16, 16, 16]):
        ws2.column_dimensions[col].width = w

    title_row(ws2, 1, '함정별 무기 소모 현황 (단일 시뮬)')
    hdr(ws2, 2, ['함정명', '무기', '초기 재고', '소모량', '잔여량'])

    row_idx = 3
    for s in result.get('friendly_ships', []):
        spec        = SHIP_DB.get(s.ship_type, {})
        default_inv = spec.get('default_inventory', {})
        for wpn, orig in default_inv.items():
            remaining = s.inventory.get(wpn, orig)
            used      = orig - remaining
            bg = 'FADBD8' if used > 0 else 'F2F3F4'
            cs(ws2, row_idx, 1, s.name,      bg=bg, center=False)
            cs(ws2, row_idx, 2, wpn,         bg=bg, center=False)
            cs(ws2, row_idx, 3, orig,        bg=bg)
            cs(ws2, row_idx, 4, used,        bg='E74C3C' if used > 0 else bg,
               color='FFFFFF' if used > 0 else '000000', bold=(used > 0))
            cs(ws2, row_idx, 5, remaining,   bg=bg)
            row_idx += 1

    # ── Sheet3: 교전 로그 ────────────────────────────────────────────────────
    ws3 = wb.create_sheet('교전 로그')
    ws3.sheet_view.showGridLines = False
    for col, w in zip('AB', [12, 80]):
        ws3.column_dimensions[col].width = w

    title_row(ws3, 1, '교전 로그 (단일 시뮬)', cols='A:B')
    hdr(ws3, 2, ['시각 (s)', '이벤트'])

    for i, (t, msg) in enumerate(result.get('log', [])):
        bg = 'EBF5FB' if i % 2 == 0 else 'FDFEFE'
        cs(ws3, i + 3, 1, f'{t:.0f}', bg=bg)
        cs(ws3, i + 3, 2, msg,        bg=bg, center=False)

    # ── Sheet4: PNG 차트 ─────────────────────────────────────────────────────
    if img_path and _CAN_IMG and os.path.exists(img_path):
        ws4 = wb.create_sheet('분석 차트')
        ws4.sheet_view.showGridLines = False
        title_row(ws4, 1, 'MC 분석 차트', cols='A:L')
        img_obj = XLImage(img_path)
        img_obj.anchor = 'A2'
        ws4.add_image(img_obj)

    wb.save(xlsx_path)
    print(f"  엑셀 보고서 저장: '{xlsx_path}'")
    return xlsx_path


# ════════════════════════════════════════════════════════════════════════════
#  단독 실행 테스트 — 32종 혼합 시나리오
# ════════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    import sys

    scenario = sys.argv[1] if len(sys.argv) > 1 else 'mixed'

    SCENARIOS = {
        # 수상함 대결
        'surface': {
            'fleet_preset': '기동전단 기본',
            'weather':      '맑음 (주간)',
            'detect_km':    200,
            'haesong2_stock': 8,
            'haesong1_stock': 0,
            'harpoon_stock':  4,
            'enemy_fleet': [
                {'preset': '055형 대형 구축함', 'count': 1},
                {'preset': '052D형 구축함',     'count': 2},
            ],
        },
        # 항공 위협
        'air': {
            'fleet_preset': 'BMD 중점',
            'weather':      '맑음 (주간)',
            'detect_km':    300,
            'haesong2_stock': 0,
            'haesong1_stock': 0,
            'harpoon_stock':  0,
            'enemy_fleet': [
                {'preset': 'J-20 (위룡)',    'count': 2},
                {'preset': 'J-16 (플랭커-D)', 'count': 2},
                {'preset': 'H-6 (폭격기)',    'count': 1},
            ],
        },
        # 탄도/순항 미사일
        'missile': {
            'fleet_preset': 'BMD 중점',
            'weather':      '맑음 (주간)',
            'detect_km':    400,
            'haesong2_stock': 0,
            'haesong1_stock': 0,
            'harpoon_stock':  0,
            'enemy_fleet': [
                {'preset': 'DF-21D (대함 탄도)',        'count': 2},
                {'preset': 'DF-17 (극초음속 활공)',     'count': 1},
                {'preset': 'KN-23 (북한 이스칸데르)',   'count': 2},
                {'preset': 'YJ-12 (초음속 순항)',       'count': 3},
            ],
        },
        # 잠수함
        'sub': {
            'fleet_preset': '대잠 중점',
            'weather':      '맑음 (주간)',
            'detect_km':    200,
            'sub_detect_km': 50,
            'haesong2_stock': 0,
            'haesong1_stock': 0,
            'harpoon_stock':  0,
            'enemy_fleet': [
                {'preset': '095형 잠수함 (차세대 SSN)', 'count': 1},
                {'preset': '093형 잠수함 (위안급)',     'count': 2},
            ],
        },
        # 32종 혼합
        'mixed': {
            'fleet_preset': '최대 편대',
            'weather':      '맑음 (주간)',
            'detect_km':    300,
            'sub_detect_km': 50,
            'haesong2_stock': 12,
            'haesong1_stock': 4,
            'harpoon_stock':  8,
            'enemy_fleet': [
                {'preset': '055형 대형 구축함',         'count': 1},
                {'preset': '052D형 구축함',             'count': 1},
                {'preset': 'J-20 (위룡)',               'count': 1},
                {'preset': 'H-6 (폭격기)',              'count': 1},
                {'preset': 'DF-21D (대함 탄도)',        'count': 1},
                {'preset': 'DF-17 (극초음속 활공)',     'count': 1},
                {'preset': 'KN-23 (북한 이스칸데르)',   'count': 1},
                {'preset': 'YJ-12 (초음속 순항)',       'count': 2},
                {'preset': '095형 잠수함 (차세대 SSN)', 'count': 1},
            ],
        },
    }

    cfg = SCENARIOS.get(scenario, SCENARIOS['mixed'])

    MC_N = int(sys.argv[2]) if len(sys.argv) > 2 else 200

    print("=" * 66)
    print(f"  이지스 기동전단 통합 방어 시뮬레이터 v7.0  [시나리오: {scenario}]")
    print("=" * 66)

    result = run_v7_simulation(cfg)

    print(f"  시뮬 종료 시각  : {result['sim_time']:.0f}s")
    print(f"  총 위협 수      : {result['total_threats']}발/기")
    print(f"  요격 성공       : {result['intercepted_threats']}발/기")
    print(f"  요격률          : {result['intercept_rate']:.1%}")
    print(f"  아군 피격       : {result['friendly_hits']}회")
    print(f"  적 피격         : {result['enemy_hits']}회")
    print(f"  적 위협 격침    : {result['enemy_ships_destroyed']}기/척")
    print(f"  아군 함정 손실  : {result['friendly_ships_lost']}척")
    print(f"  총 비용         : ${result['total_cost']:,.0f}")
    print("-" * 66)
    print("  교전 로그:")
    for t, msg in result['log']:
        print(f"  [{t:5.0f}s] {msg}")
    print("=" * 66)

    # ── MC 분석 + 보고서 생성 ────────────────────────────────────────────────
    print(f"\n  몬테카를로 분석 ({MC_N}회) 시작...")
    mc = monte_carlo_v7(cfg, n=MC_N, desc=scenario)

    print(f"  MC 평균 요격률 : {mc['mean_intercept']:.1%}  "
          f"(±{mc['std_intercept']:.1%})")
    print(f"  완전 요격 비율 : {mc['full_pass_rate']:.1%}")

    img_path  = f'이지스_기동전단_v7_{scenario}_분석.png'
    xlsx_path = f'이지스_기동전단_v7_{scenario}_보고서.xlsx'

    plot_v7(result, mc, cfg, img_path=img_path)
    save_excel_report_v7(result, mc, cfg,
                         img_path=img_path, xlsx_path=xlsx_path)

    print("\n  ※ 실행 방법:")
    print(f"     python engine_v7.py [시나리오] [MC횟수]")
    print(f"     예) python engine_v7.py mixed 500")
    print("=" * 66)

# ── v7.0 1단계 패치 ───────────────────────────────────────────────────────────
# · NEW-A: 시간 스텝(1초) 루프 + Vec2 2D 위치 모델
# · NEW-B: 아군 방어 SAM (SM-3/SM-6/SM-2/RAM/CIWS)
# · NEW-C: 아군 공격 (해성-I/II·하푼) — FRIENDLY_STRIKE_DB 신규
# · NEW-D: 적 SAM 방어 (HHQ-9B/HHQ-16/HHQ-10/1130-CIWS) — ENEMY_SAM_DB 신규
# · NEW-E: SimFrame 단위 상태 기록 (애니메이션 준비)

# ── v7.0 2단계 패치 ───────────────────────────────────────────────────────────
# · BUG-1: SAM alive=False 조기 설정 → 요격 판정 스킵 문제 수정
# · BUG-2: INTERCEPT_DIST_M 300m → 2000m (1초 스텝 해상도 반영)
# · BUG-3: 대함 탐지 거리 수정 (자함 레이더 45km → detect_km 병용)
# · BUG-4: 적 함정 시작 위치 1.8x → 1.0x (교전 즉시 개시)
# · BUG-5: 적 함정 재발사 허용 (미사일 소진 후 재장전)

# ── v7.0 3단계 패치 ───────────────────────────────────────────────────────────
# · NEW-F: EnemyShipObj → EnemyThreatObj 통합 (항공/함정/잠수함/독립미사일)
# · NEW-G: 항공기 접근→발사→이탈 행동 패턴
# · NEW-H: 탄도/순항/HGV/QBM 독립 미사일 MissileObj 직접 생성
# · NEW-I: 대잠전 홍상어/청상어 ASW + 소나 탐지 범위
# · NEW-J: _select_defense_wpn() 고도·유형 인식 (SM-3 HGV/탄도, SM-6 QBM)

# ── v7.0 4단계 패치 ───────────────────────────────────────────────────────────
# · NEW-K: matplotlib 한글 폰트 설정 (Malgun Gothic)
# · NEW-L: monte_carlo_v7() — N회 반복 통계 집계
# · NEW-M: plot_v7() — 6개 서브플롯 PNG 차트
# · NEW-N: save_excel_report_v7() — 4시트 Excel 보고서
# · NEW-O: __main__ 인수 확장 (python engine_v7.py [시나리오] [MC횟수])

# ── v7.0 포팅 A 패치 ──────────────────────────────────────────────────────────
# · NEW-P: ENEMY_FLEET_PRESETS / ENEMY_FLEET_RANDOM_CFG / generate_random_enemy_fleet 임포트
# · NEW-Q: _build_enemies() — enemy_fleet_mode 4종 (custom/preset/random) 지원
# · NEW-R: _build_friendly() — SM-3/SM-6/SM-2/RAM/홍상어/청상어/Mk.46 수동 재고 설정
# · BUG-6: intercept_rate 계산 오류 수정 — 항공기 플랫폼 격추가 intercepted_threats에 집계되어
#           미사일 미발사 항공기 격추 시 intercept_rate > 1.0 발생하던 문제 제거
#           (MissileObj만 intercepted_threats 카운트, 플랫폼 격추는 enemy_ships_destroyed)

# ── v7.0 포팅 B 패치 ──────────────────────────────────────────────────────────
# · NEW-S: ECM_REF_RANGE_M / DECOY_PK / SHIP_EVASION_PK 상수 추가
# · NEW-T: MissileObj.terminal_evasion_factor / is_torpedo 속성 추가
# · NEW-U: FriendlyShipObj.decoy_stock (기본 4발) 추가
# · NEW-V: _check_intercepts() — ECM 재밍 (50km 기준 Pk 감소, 하한 50%, 탄도/HGV 제외)
# · NEW-W: _check_intercepts() — 종말 회피 (< 20km, terminal_evasion_factor 적용)
# · NEW-X: _check_hits() — 음향 기만기 AN/SLQ-25 (어뢰 전용, DECOY_PK=0.60)
# · NEW-Y: _check_hits() — 함정 회피 기동 (어뢰 전용, SHIP_EVASION_PK=0.30)
# · NEW-Z: _check_hits() — 적 자체방어 (CIWS 요격 → 채프/플레어 eff_pk 감소)

# ── v7.0 포팅 C 패치 ──────────────────────────────────────────────────────────
# · NEW-AA: FRIENDLY_AIRCRAFT_DB 임포트 추가 (engine.py)
# · NEW-AB: FriendlyAircraftObj 클래스 — 항공 자산 상태 (t_available, payload_remaining)
# · NEW-AC: _build_aircraft() — enable_helo/p3c/p8a cfg 키로 항공 자산 등록
# · NEW-AD: _aircraft_asw() — 매 tick 잠수함 탐지 후 어뢰 투하 (날씨·사거리·소노부이·쿨다운)
#           어뢰는 목표 근방(±300m) 스폰 — 항공기 직접 투하 방식
#           소노부이: 탐지거리 + sonobuoy_detect_bonus_km (P-3C +15km, P-8A +18km)
# · NEW-AE: _compile() — aircraft_sorties 집계 + 항공 비용 total_cost 합산

# ── v7.0 포팅 D 패치 ──────────────────────────────────────────────────────────
# · NEW-AF: MAX_RESPONSE_TIME_S=120s 상수 추가
# · NEW-AG: stats — peak_concurrent_threats / t_first_fire / total_missiles_fired 추가
# · NEW-AH: _launch_friendly_sam() — total_missiles_fired / t_first_fire 추적
# · NEW-AI: run() 루프 — peak_concurrent_threats 매 tick 갱신
# · NEW-AJ: _compile() — remaining_inventory / total_channels 반환
# · NEW-AK: REQ_ITEMS_V7 — 8항목 정의 (시간스텝 기반 재설계)
# · NEW-AL: evaluate_req_v7() — (verdicts, details) 반환
# · NEW-AM: scenario_comparison_v7() — 날씨 3종 MC 비교
# · NEW-AN: compare_ab_v7() — A vs B MC 비교 (Δ요격률·Δ비용)
# · NEW-AO: save_scenario_v7() / load_scenario_v7() — JSON 시나리오 저장/불러오기

# ── v7.0 포팅 E 패치 ──────────────────────────────────────────────────────────
# · NEW-AP: LAYER_ORDER / SHIP_LAYER_PRI 상수 추가 (KDX-III=0, KDX-II=1, FFX=2)
# · NEW-AQ: SimFrame.ship_channels 필드 추가 [(name, channels_used, max_channels)]
# · NEW-AR: _record_frame() — ship_channels 매 tick 기록
# · NEW-AS: _friendly_defense() 전면 재설계 — 위협 우선 루프 + 함정 우선순위 정렬
#   - 다층 방어: KDX-III → KDX-II → FFX 순서 고정 (SHIP_LAYER_PRI 정렬)
#     위협당 가장 고성능 함정이 항상 1차 교전, 부재 시 다음 레이어 자동 인계
#   - CEC 사전 동시 배정(enable_cec_preassign): 위협당 최대 2발 동시 허용
#     1차 SAM 성공 시 2차 SAM은 표적 소멸로 자동 종료
