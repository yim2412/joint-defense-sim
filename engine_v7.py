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
    ENEMY_DB, FRIENDLY_DB, WEATHER_DB,
    SHIP_DB, FLEET_PRESETS,
    calculate_detect_range_by_rcs,
)

# ── 시뮬레이션 상수 ──────────────────────────────────────────────────────────
DT               = 1.0    # 시간 스텝 (초)
MAX_SIM_TIME     = 700    # 최대 시뮬 시간 (초)
INTERCEPT_DIST_M = 2000   # SAM 요격 판정 거리 (m)

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

    @property
    def operational(self) -> bool:
        return self.alive

    def take_hit(self, weapon_name: str, t: float):
        self.hit_count += 1
        self.hp -= 1
        if self.hp <= 0:
            self.alive = False


# ════════════════════════════════════════════════════════════════════════════
#  SimFrame
# ════════════════════════════════════════════════════════════════════════════
class SimFrame:
    __slots__ = ('t', 'friendly_ships', 'enemy_ships', 'missiles', 'events')

    def __init__(self, t: float):
        self.t              = t
        self.friendly_ships = []  # [(name, x, y, alive, hp)]
        self.enemy_ships    = []  # [(uid, preset, x, y, alive, hp)]
        self.missiles       = []  # [(uid, x, y, mtype, name)]
        self.events         = []  # [str]


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
            'total_threats':         0,
            'intercepted_threats':   0,
            'friendly_hits':         0,
            'enemy_hits':            0,
            'friendly_ships_lost':   0,
            'enemy_ships_destroyed': 0,
            'total_cost':            0.0,
        }
        weather = cfg.get('weather', '맑음 (주간)')
        self.wx = WEATHER_DB.get(weather, WEATHER_DB['맑음 (주간)'])

        self.friendly_ships: List[FriendlyShipObj] = self._build_friendly()
        self.missiles:       List[MissileObj]       = []
        self.enemy_threats:  List[EnemyThreatObj]   = self._build_enemies()
        self.frames:         List[SimFrame]          = []

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
            ships.append(s)
        return ships

    def _build_enemies(self) -> List[EnemyThreatObj]:
        """
        플랫폼(항공기/수상함/잠수함) → EnemyThreatObj
        독립 미사일(탄도/순항/HGV/QBM) → MissileObj (self.missiles에 직접 추가)
        """
        fleet_cfg  = self.cfg.get('enemy_fleet', [])
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
                    m.altitude_m   = float(info.get('altitude_m', 0))
                    m.is_hgv       = bool(info.get('is_hgv', False))
                    m.is_qbm       = bool(info.get('is_qbm', False))
                    m.is_ballistic = (ttype == '탄도미사일')
                    self.missiles.append(m)
                    self.stats['total_threats'] += 1
                else:
                    threats.append(EnemyThreatObj(name, pos))

                idx += 1

        return threats

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
        if category == '대함':
            tactical_km = self.cfg.get('detect_km', 200)
            base_km = max(ship.sensor_km.get('대함', 45), tactical_km)
        elif category == '대잠':
            base_km = ship.sensor_km.get('대잠', 50)
        else:
            base_km = ship.sensor_km.get(category, 200)
        return base_km * 1000 * self.wx.get('detect_range_factor', 1.0)

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
                self.missiles.append(MissileObj(
                    mtype    = 'enemy_strike',
                    name     = m_name,
                    pos      = offset,
                    target   = primary,
                    speed_ms = m_speed,
                    pk_base  = 0.80,
                    owner_id = id(et),
                    t_spawn  = self.t,
                ))

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
        for ship in self.friendly_ships:
            if not ship.alive:
                continue

            # (A) 적 대함 미사일 요격 (MissileObj enemy_strike)
            for m in self.missiles:
                if not m.alive or m.mtype != 'enemy_strike':
                    continue
                already = any(
                    s.alive and s.target is m and s.mtype == 'friendly_sam'
                    for s in self.missiles
                )
                if already:
                    continue
                dist_m = ship.pos.dist_to(m.pos)
                wpn = self._select_defense_wpn(ship, m, dist_m)
                if not wpn or ship.channels_used >= ship.max_channels:
                    continue
                if ship.inventory.get(wpn, 0) <= 0:
                    continue
                self._launch_friendly_sam(ship, wpn, m, dist_m, is_aa=False)

            # (B) 적 항공기 직접 요격 (EnemyThreatObj is_aircraft)
            for et in self.enemy_threats:
                if not et.alive or not et.is_aircraft or et.is_retreating:
                    continue
                already = any(
                    s.alive and s.target is et and s.mtype == 'friendly_sam'
                    for s in self.missiles
                )
                if already:
                    continue
                dist_m = ship.pos.dist_to(et.pos)
                wpn = self._select_aa_wpn(ship, et, dist_m)
                if not wpn or ship.channels_used >= ship.max_channels:
                    continue
                if ship.inventory.get(wpn, 0) <= 0:
                    continue
                self._launch_friendly_sam(ship, wpn, et, dist_m, is_aa=True)

    def _launch_friendly_sam(self, ship: FriendlyShipObj, wpn: str, target,
                              dist_m: float, is_aa: bool):
        wpn_info = FRIENDLY_DB[wpn]
        ship.inventory[wpn]   -= 1
        ship.channels_used    += 1
        ship.total_cost       += wpn_info['cost_usd']
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

            if random.random() < sam.pk_base:
                tgt.alive       = False
                tgt.intercepted = True
                tgt.t_intercept = self.t

                if sam.mtype == 'friendly_sam':
                    self._log(f"[요격 성공] {sam.name} -> {tgt_name} 격추 ({self.t:.0f}s)")
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
                    if random.random() < m.pk_base:
                        tgt.take_hit(m.name, self.t)
                        self.stats['friendly_hits'] += 1
                        self._log(f"[피격] {tgt.name} <- {m.name} 명중! (HP {tgt.hp})")
                    else:
                        self._log(f"[피격 실패] {m.name} -> {tgt.name} 근접 불발")

            elif m.mtype == 'friendly_strike':
                tgt = m.target
                if isinstance(tgt, EnemyThreatObj) and tgt.alive:
                    if random.random() < m.pk_base:
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
            self._enemy_defense()
            self._check_intercepts()
            self._check_hits()

            self.missiles = [m for m in self.missiles
                             if m.alive and not m.intercepted]

            self._record_frame()

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
        self.stats['total_cost']            = sum(s.total_cost for s in self.friendly_ships)

        intercept_rate = (
            self.stats['intercepted_threats'] / self.stats['total_threats']
            if self.stats['total_threats'] > 0 else 1.0
        )

        return {
            **self.stats,
            'intercept_rate':  intercept_rate,
            'sim_time':        self.t,
            'frames':          self.frames,
            'log':             self._log_entries,
            'friendly_ships':  self.friendly_ships,
            'enemy_ships':     self.enemy_threats,   # 하위 호환 키 유지
        }


# ════════════════════════════════════════════════════════════════════════════
#  외부 API
# ════════════════════════════════════════════════════════════════════════════

def run_v7_simulation(cfg: dict) -> dict:
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
