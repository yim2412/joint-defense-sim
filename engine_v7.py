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
"""

import math, random
from typing import List, Optional

# 기존 엔진에서 DB / 유틸 재사용
from engine import (
    ENEMY_DB, FRIENDLY_DB, WEATHER_DB,
    SHIP_DB, FLEET_PRESETS,
    calculate_detect_range_by_rcs,
)

# ── 시뮬레이션 상수 ──────────────────────────────────────────────────────────
DT          = 1.0    # 시간 스텝 (초)
MAX_SIM_TIME = 700   # 최대 시뮬 시간 (초)
INTERCEPT_DIST_M = 2000  # SAM 요격 판정 거리 (m) — 1초 스텝 해상도 반영

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

# 적 함정별 SAM 탑재 현황 (실제 PLA 해군 기준)
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

# ════════════════════════════════════════════════════════════════════════════
#  Vec2 — 2D 위치/속도 벡터
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
#  MissileObj — 공중의 미사일 (아군/적 모두)
# ════════════════════════════════════════════════════════════════════════════
class MissileObj:
    """
    mtype:
      'enemy_strike'   — 적 대함미사일 (아군 함정 향함)
      'friendly_strike'— 아군 대함미사일 (적 함정 향함)
      'friendly_sam'   — 아군 SAM (적 미사일 요격)
      'enemy_sam'      — 적 SAM (아군 미사일 요격)
    """
    _id_counter = 0

    def __init__(self, mtype: str, name: str, pos: Vec2,
                 target,          # 목표 엔티티 (pos 속성 보유)
                 speed_ms: float, pk_base: float,
                 owner_id: int, t_spawn: float = 0.0):
        MissileObj._id_counter += 1
        self.uid        = f"M{MissileObj._id_counter:04d}"
        self.mtype      = mtype
        self.name       = name
        self.pos        = pos.copy()
        self.target     = target      # 동적 추적용 참조
        self.speed_ms   = speed_ms
        self.pk_base    = pk_base
        self.owner_id   = owner_id
        self.t_spawn    = t_spawn

        self.alive        = True
        self.intercepted  = False
        self.hit          = False
        self.t_intercept  = None
        self.t_hit        = None

    def update(self, dt: float) -> bool:
        """1 tick 이동. 목표 도달 시 True.
        alive=False는 설정하지 않음 — 요격/피격 판정은 엔진이 담당.
        """
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
#  EnemyShipObj — 적 함정
# ════════════════════════════════════════════════════════════════════════════
class EnemyShipObj:
    _id_counter = 0

    def __init__(self, preset_name: str, pos: Vec2):
        EnemyShipObj._id_counter += 1
        self.uid         = f"ES{EnemyShipObj._id_counter:03d}"
        self.preset_name = preset_name
        self.info        = ENEMY_DB[preset_name].copy()
        self.pos         = pos
        self.speed_ms    = self.info['speed_ms']

        # SAM 재고
        loadout = ENEMY_SHIP_SAM_LOADOUT.get(preset_name, [])
        self.sam_inventory = {item['name']: item['stock'] for item in loadout}

        # 교전 채널 (동시 요격 가능 수)
        self.sam_max_channels = sum(
            ENEMY_SAM_DB[n]['channels']
            for n in self.sam_inventory if n in ENEMY_SAM_DB
        )
        self.sam_channels_used = 0

        # 피해
        self.hp        = 3
        self.alive     = True
        self.hit_count = 0
        self.hit_by: list = []

        # 미사일 발사 여부
        self.has_fired = False

    def take_hit(self, weapon_name: str, t: float):
        self.hit_count += 1
        self.hit_by.append((weapon_name, t))
        self.hp -= 1
        if self.hp <= 0:
            self.alive = False

    def update(self, target_pos: Vec2, dt: float):
        if self.alive:
            self.pos.move_toward(target_pos, self.speed_ms, dt)

    def select_sam(self, missile_dist_m: float) -> Optional[str]:
        """사거리 내 가장 적합한 SAM 선택 (원거리 우선)"""
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
#  FriendlyShipObj — 아군 함정
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

        # 방어 무기 재고
        self.inventory = spec['default_inventory'].copy()

        # 공격 무기 재고 (cfg에서 주입)
        self.strike_inventory: dict = {}

        # 상태
        self.hp          = 5
        self.alive       = True
        self.hit_count   = 0
        self.total_cost  = 0.0
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
#  SimFrame — 1 tick 상태 스냅샷 (애니메이션용)
# ════════════════════════════════════════════════════════════════════════════
class SimFrame:
    __slots__ = ('t', 'friendly_ships', 'enemy_ships', 'missiles', 'events')

    def __init__(self, t: float):
        self.t              = t
        self.friendly_ships = []  # [(name, x, y, alive, hp)]
        self.enemy_ships    = []  # [(uid, preset, x, y, alive, hp)]
        self.missiles       = []  # [(uid, x, y, mtype, name)]
        self.events         = []  # [str] 이 tick에 발생한 이벤트 메시지


# ════════════════════════════════════════════════════════════════════════════
#  TimeStepEngine — v7.0 메인 시뮬레이션 루프
# ════════════════════════════════════════════════════════════════════════════
class TimeStepEngine:
    """
    매 DT(1초)마다 실행 순서:
      1. 위치 갱신 (적 함정 접근, 미사일 비행)
      2. 적 함정 미사일 발사 조건 확인
      3. 아군 TEWA — 방어 (적 미사일 요격)
      4. 아군 TEWA — 공격 (적 함정에 대함미사일)
      5. 적 TEWA   — SAM 방어 (아군 대함미사일 요격)
      6. 교전 결과 판정 (SAM vs 미사일, 미사일 vs 함정)
      7. 프레임 기록
    """

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.t   = 0.0
        self._log_entries: list = []   # [(t, msg)]
        self._tick_events:  list = []   # 현재 tick 이벤트 (프레임용)

        # 엔티티 카운터 리셋
        MissileObj.reset_counter()
        EnemyShipObj.reset_counter()

        self.friendly_ships: List[FriendlyShipObj] = self._build_friendly()
        self.enemy_ships:    List[EnemyShipObj]     = self._build_enemies()
        self.missiles:       List[MissileObj]        = []
        self.frames:         List[SimFrame]           = []

        # 날씨
        weather = cfg.get('weather', '맑음 (주간)')
        self.wx = WEATHER_DB.get(weather, WEATHER_DB['맑음 (주간)'])

        # 결과 집계
        self.stats = {
            'total_threats':          0,
            'intercepted_threats':    0,
            'friendly_hits':          0,
            'enemy_hits':             0,
            'friendly_ships_lost':    0,
            'enemy_ships_destroyed':  0,
            'total_cost':             0.0,
        }

    # ── 편대 구성 ─────────────────────────────────────────────────────────────

    def _build_friendly(self) -> List[FriendlyShipObj]:
        preset_name = self.cfg.get('fleet_preset', '단독 작전')
        preset = FLEET_PRESETS.get(preset_name, FLEET_PRESETS['단독 작전'])
        ships = []
        for spec in preset:
            s = FriendlyShipObj(spec['name'], spec['type'])
            s.strike_inventory = {
                '해성-II':      self.cfg.get('haesong2_stock', 8),
                '해성-I':       self.cfg.get('haesong1_stock', 0),
                '하푼 Block II': self.cfg.get('harpoon_stock', 4),
            }
            ships.append(s)
        return ships

    def _build_enemies(self) -> List[EnemyShipObj]:
        fleet_cfg = self.cfg.get('enemy_fleet', [])
        detect_km = self.cfg.get('detect_km', 200)
        ships = []
        total = sum(s.get('count', 1) for s in fleet_cfg)
        idx = 0
        for spec in fleet_cfg:
            name  = spec['preset']
            count = spec.get('count', 1)
            if name not in ENEMY_DB:
                continue
            for c in range(count):
                # 방위각 균등 배분 (전방위 접근)
                bearing_deg = (idx / max(total, 1)) * 360
                bearing_rad = math.radians(bearing_deg)
                start_m = detect_km * 1000 * 1.8  # 탐지거리 1.8배 밖에서 시작
                pos = Vec2(
                    math.cos(bearing_rad) * start_m,
                    math.sin(bearing_rad) * start_m,
                )
                ships.append(EnemyShipObj(name, pos))
                idx += 1
        return ships

    # ── 헬퍼 ─────────────────────────────────────────────────────────────────

    def _primary(self) -> FriendlyShipObj:
        """KDX-III 우선, 없으면 생존한 첫 함정"""
        for s in self.friendly_ships:
            if s.alive and s.ship_type == 'KDX-III':
                return s
        return next((s for s in self.friendly_ships if s.alive), self.friendly_ships[0])

    def _log(self, msg: str):
        self._log_entries.append((self.t, msg))
        self._tick_events.append(msg)

    def _detect_range_m(self, ship: FriendlyShipObj, category: str) -> float:
        base_km = ship.sensor_km.get(category, 200)
        return base_km * 1000 * self.wx.get('detect_range_factor', 1.0)

    # ── 1단계: 위치 갱신 ──────────────────────────────────────────────────────

    def _update_positions(self):
        primary_pos = self._primary().pos
        for es in self.enemy_ships:
            es.update(primary_pos, DT)
        for m in self.missiles:
            m.update(DT)

    # ── 2단계: 적 함정 미사일 발사 ────────────────────────────────────────────

    def _enemy_fire(self):
        primary = self._primary()
        for es in self.enemy_ships:
            if not es.alive or es.has_fired:
                continue
            if not es.info.get('can_fire_missile'):
                continue

            dist_m      = es.pos.dist_to(primary.pos)
            fire_range_m = es.info.get('missile_range_km', 0) * 1000 * 0.85

            if dist_m > fire_range_m:
                continue

            # 일제 사격
            salvo   = random.randint(
                es.info.get('missile_salvo_min', 1),
                es.info.get('missile_salvo_max', 2)
            )
            m_speed = es.info.get('missile_speed_ms') or 300
            m_name  = es.info.get('missile_name') or '대함미사일'

            for k in range(salvo):
                offset = Vec2(
                    es.pos.x + random.uniform(-500, 500),
                    es.pos.y + random.uniform(-500, 500),
                )
                m = MissileObj(
                    mtype    = 'enemy_strike',
                    name     = m_name,
                    pos      = offset,
                    target   = primary,
                    speed_ms = m_speed,
                    pk_base  = 0.80,
                    owner_id = id(es),
                    t_spawn  = self.t,
                )
                self.missiles.append(m)

            es.has_fired = True
            self.stats['total_threats'] += salvo
            self._log(f"[적 발사] {es.preset_name} → {m_name} {salvo}발 (거리 {dist_m/1000:.0f}km)")

    # ── 3단계: 아군 방어 TEWA ─────────────────────────────────────────────────

    def _friendly_defense(self):
        """접근 중인 적 미사일에 아군 SAM 발사"""
        for ship in self.friendly_ships:
            if not ship.alive:
                continue

            for m in self.missiles:
                if not m.alive or m.mtype != 'enemy_strike':
                    continue

                # 이미 이 미사일을 향한 아군 SAM 있으면 skip
                already = any(
                    s.alive and s.target is m and s.mtype == 'friendly_sam'
                    for s in self.missiles
                )
                if already:
                    continue

                dist_m = ship.pos.dist_to(m.pos)
                wpn = self._select_defense_wpn(ship, dist_m)
                if not wpn:
                    continue

                if ship.channels_used >= ship.max_channels:
                    continue

                wpn_info = FRIENDLY_DB[wpn]
                if ship.inventory.get(wpn, 0) <= 0:
                    continue

                ship.inventory[wpn]  -= 1
                ship.channels_used   += 1
                ship.total_cost      += wpn_info['cost_usd']

                sam = MissileObj(
                    mtype    = 'friendly_sam',
                    name     = wpn,
                    pos      = ship.pos,
                    target   = m,
                    speed_ms = wpn_info['speed_ms'],
                    pk_base  = wpn_info['pk_dist']['mean'],
                    owner_id = id(ship),
                    t_spawn  = self.t,
                )
                self.missiles.append(sam)
                self._log(f"[방어] {ship.name} → {wpn} 발사 (거리 {dist_m/1000:.1f}km)")

    def _select_defense_wpn(self, ship: FriendlyShipObj, dist_m: float) -> Optional[str]:
        inv = ship.inventory
        if dist_m <= 2_000   and inv.get('CIWS-II (Phalanx)', 0) > 0: return 'CIWS-II (Phalanx)'
        if dist_m <= 9_000   and inv.get('RIM-116 RAM',       0) > 0: return 'RIM-116 RAM'
        if dist_m <= 170_000 and inv.get('SM-2 Block IIIB',   0) > 0: return 'SM-2 Block IIIB'
        if dist_m <= 240_000 and inv.get('SM-6',              0) > 0: return 'SM-6'
        if dist_m <= 1_200_000 and inv.get('SM-3 Block IIA',  0) > 0: return 'SM-3 Block IIA'
        return None

    # ── 4단계: 아군 공격 TEWA ─────────────────────────────────────────────────

    def _friendly_strike(self):
        """탐지한 적 함정에 대함미사일 발사"""
        for ship in self.friendly_ships:
            if not ship.alive:
                continue

            for es in self.enemy_ships:
                if not es.alive:
                    continue

                dist_m = ship.pos.dist_to(es.pos)
                category = es.info.get('category', '대함')
                if dist_m > self._detect_range_m(ship, category):
                    continue

                # 이미 이 목표에 미사일 2발 이상 비행 중이면 skip
                en_route = sum(
                    1 for m in self.missiles
                    if m.alive and m.target is es and m.mtype == 'friendly_strike'
                )
                if en_route >= 2:
                    continue

                wpn = self._select_strike_wpn(ship, dist_m)
                if not wpn:
                    continue

                wpn_info = FRIENDLY_STRIKE_DB[wpn]
                ship.strike_inventory[wpn] -= 1
                ship.total_cost += wpn_info['cost_usd']

                strike = MissileObj(
                    mtype    = 'friendly_strike',
                    name     = wpn,
                    pos      = ship.pos,
                    target   = es,
                    speed_ms = wpn_info['speed_ms'],
                    pk_base  = wpn_info['pk_base'],
                    owner_id = id(ship),
                    t_spawn  = self.t,
                )
                self.missiles.append(strike)
                self._log(f"[공격] {ship.name} → {wpn} 발사 → {es.preset_name} (거리 {dist_m/1000:.0f}km)")

    def _select_strike_wpn(self, ship: FriendlyShipObj, dist_m: float) -> Optional[str]:
        for wpn in ['해성-II', '해성-I', '하푼 Block II']:
            if ship.strike_inventory.get(wpn, 0) <= 0:
                continue
            if dist_m <= FRIENDLY_STRIKE_DB[wpn]['range_km'] * 1000:
                return wpn
        return None

    # ── 5단계: 적 SAM 방어 ────────────────────────────────────────────────────

    def _enemy_defense(self):
        """적 함정이 접근 중인 아군 대함미사일을 SAM으로 요격"""
        for es in self.enemy_ships:
            if not es.alive:
                continue

            for m in self.missiles:
                if not m.alive or m.mtype != 'friendly_strike':
                    continue
                if m.target is not es:
                    continue

                # 이미 이 미사일을 향한 적 SAM 있으면 skip
                already = any(
                    s.alive and s.target is m and s.mtype == 'enemy_sam'
                    for s in self.missiles
                )
                if already:
                    continue

                # 채널 한계
                if es.sam_channels_used >= es.sam_max_channels:
                    continue

                dist_m   = es.pos.dist_to(m.pos)
                sam_name = es.select_sam(dist_m)
                if not sam_name:
                    continue

                sam_info = ENEMY_SAM_DB[sam_name]
                es.sam_inventory[sam_name] -= 1
                es.sam_channels_used       += 1

                sam = MissileObj(
                    mtype    = 'enemy_sam',
                    name     = sam_name,
                    pos      = es.pos,
                    target   = m,
                    speed_ms = sam_info['speed_ms'],
                    pk_base  = sam_info['pk'],
                    owner_id = id(es),
                    t_spawn  = self.t,
                )
                self.missiles.append(sam)
                self._log(f"[적 방어] {es.preset_name} → {sam_name} 발사 (거리 {dist_m/1000:.1f}km)")

    # ── 6단계: 교전 결과 판정 ─────────────────────────────────────────────────

    def _check_intercepts(self):
        """SAM 요격 판정.
        - sam.hit=True (목표 위치 도달) 또는
        - 목표까지 거리 <= INTERCEPT_DIST_M
        둘 중 하나면 요격 판정 실행. SAM은 판정 후 소모.
        """
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

            sam.alive = False  # SAM 소모

            # 요격 판정
            if random.random() < sam.pk_base:
                tgt.alive       = False
                tgt.intercepted = True
                tgt.t_intercept = self.t

                if sam.mtype == 'friendly_sam':
                    self._log(f"[요격 성공] {sam.name} -> {tgt.name} 격추 ({self.t:.0f}s)")
                    self.stats['intercepted_threats'] += 1
                    for ship in self.friendly_ships:
                        if id(ship) == sam.owner_id:
                            ship.channels_used = max(0, ship.channels_used - 1)
                else:
                    self._log(f"[적 요격 성공] {sam.name} -> {tgt.name} 격추 ({self.t:.0f}s)")
                    for es in self.enemy_ships:
                        if id(es) == sam.owner_id:
                            es.sam_channels_used = max(0, es.sam_channels_used - 1)
            else:
                if sam.mtype == 'friendly_sam':
                    self._log(f"[요격 실패] {sam.name} -> {tgt.name} 통과")
                else:
                    self._log(f"[적 요격 실패] {sam.name} -> {tgt.name} 통과")
                    for es in self.enemy_ships:
                        if id(es) == sam.owner_id:
                            es.sam_channels_used = max(0, es.sam_channels_used - 1)

    def _check_hits(self):
        """미사일이 목표 함정에 도달(hit=True) 시 피해 처리"""
        for m in self.missiles:
            if not m.hit:
                continue

            if m.mtype == 'enemy_strike':
                tgt = m.target
                if isinstance(tgt, FriendlyShipObj) and tgt.alive:
                    if random.random() < m.pk_base:
                        tgt.take_hit(m.name, self.t)
                        self.stats['friendly_hits'] += 1
                        self._log(f"[피격] {tgt.name} ← {m.name} 명중! (HP {tgt.hp})")
                    else:
                        self._log(f"[피격 실패] {m.name} → {tgt.name} 근접 폭발 불발")

            elif m.mtype == 'friendly_strike':
                tgt = m.target
                if isinstance(tgt, EnemyShipObj) and tgt.alive:
                    if random.random() < m.pk_base:
                        tgt.take_hit(m.name, self.t)
                        self.stats['enemy_hits'] += 1
                        status = '격침' if not tgt.alive else f'손상 (HP {tgt.hp})'
                        self._log(f"[적 피격] {tgt.preset_name} ← {m.name} 명중! {status}")
                    else:
                        self._log(f"[적 피격 실패] {m.name} → {tgt.preset_name} 회피")

    # ── 7단계: 프레임 기록 ────────────────────────────────────────────────────

    def _record_frame(self):
        frame = SimFrame(self.t)

        for s in self.friendly_ships:
            frame.friendly_ships.append((s.name, s.pos.x, s.pos.y, s.alive, s.hp))

        for es in self.enemy_ships:
            frame.enemy_ships.append(
                (es.uid, es.preset_name, es.pos.x, es.pos.y, es.alive, es.hp))

        for m in self.missiles:
            if m.alive:
                frame.missiles.append((m.uid, m.pos.x, m.pos.y, m.mtype, m.name))

        frame.events = list(self._tick_events)
        self.frames.append(frame)
        self._tick_events.clear()

    # ── 종료 조건 ─────────────────────────────────────────────────────────────

    def _is_over(self) -> bool:
        if all(not es.alive for es in self.enemy_ships):
            self._log("[종료] 모든 적 함정 격침/제압")
            return True
        if all(not s.alive for s in self.friendly_ships):
            self._log("[종료] 아군 전멸")
            return True
        # 날아다니는 위협 없고 적 함정도 발사 완료 → 교전 종료
        active_threats = [m for m in self.missiles
                          if m.alive and m.mtype == 'enemy_strike']
        all_fired = all(es.has_fired or not es.alive for es in self.enemy_ships)
        if not active_threats and all_fired:
            self._log("[종료] 교전 종료 - 위협 소진")
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

            # 소모된 미사일 제거 (alive=False 또는 hit 처리 완료)
            self.missiles = [m for m in self.missiles
                             if m.alive and not m.intercepted]

            self._record_frame()

            if self._is_over():
                break

            self.t += DT

        return self._compile()

    def _compile(self) -> dict:
        self.stats['friendly_ships_lost']   = sum(1 for s in self.friendly_ships if not s.alive)
        self.stats['enemy_ships_destroyed'] = sum(1 for es in self.enemy_ships if not es.alive)
        self.stats['total_cost']            = sum(s.total_cost for s in self.friendly_ships)

        intercept_rate = (
            self.stats['intercepted_threats'] / self.stats['total_threats']
            if self.stats['total_threats'] > 0 else 1.0
        )

        return {
            **self.stats,
            'intercept_rate':    intercept_rate,
            'sim_time':          self.t,
            'frames':            self.frames,
            'log':               self._log_entries,
            'friendly_ships':    self.friendly_ships,
            'enemy_ships':       self.enemy_ships,
        }


# ════════════════════════════════════════════════════════════════════════════
#  외부 API
# ════════════════════════════════════════════════════════════════════════════

def run_v7_simulation(cfg: dict) -> dict:
    """v7.0 시뮬레이션 실행 진입점"""
    engine = TimeStepEngine(cfg)
    return engine.run()


# ════════════════════════════════════════════════════════════════════════════
#  단독 실행 테스트
# ════════════════════════════════════════════════════════════════════════════
if __name__ == '__main__':
    cfg = {
        'fleet_preset':    '기동전단 기본',
        'weather':         '맑음 (주간)',
        'detect_km':       200,
        'haesong2_stock':  8,
        'haesong1_stock':  0,
        'harpoon_stock':   4,
        'enemy_fleet': [
            {'preset': '055형 대형 구축함', 'count': 1},
            {'preset': '052D형 구축함',     'count': 2},
        ],
    }

    print("=" * 62)
    print("  이지스 기동전단 통합 방어 시뮬레이터 v7.0  [시간 스텝]")
    print("=" * 62)

    result = run_v7_simulation(cfg)

    print(f"  시뮬 종료 시각  : {result['sim_time']:.0f}s")
    print(f"  총 위협 수      : {result['total_threats']}발")
    print(f"  요격 성공       : {result['intercepted_threats']}발")
    print(f"  요격률          : {result['intercept_rate']:.1%}")
    print(f"  아군 피격       : {result['friendly_hits']}회")
    print(f"  적 피격         : {result['enemy_hits']}회")
    print(f"  적 함정 격침    : {result['enemy_ships_destroyed']}척")
    print(f"  아군 함정 손실  : {result['friendly_ships_lost']}척")
    print(f"  총 비용         : ${result['total_cost']:,.0f}")
    print("-" * 62)
    print("  교전 로그 (전체):")
    for t, msg in result['log']:
        print(f"  [{t:5.0f}s] {msg}")
    print("=" * 62)
