# -*- coding: utf-8 -*-
"""
engine_airforce.py — v19.1 공군 작전급 층 (제공권 격자 + 공군 전력 관리)

작전급 캠페인 엔진(engine_campaign.py) 위에 얹는 **공군 층**. CampaignEngine이
`enable_air_campaign` ON일 때만 AirCampaign을 생성해 1시간 틱마다 호출한다.

핵심 = **제공권(air superiority)을 한반도 격자 지도로 시뮬**:
  · 격자 셀별 제공권 0~1, 셀 그룹이 SLOC 교통로(서해·대한해협·동해)에 매핑.
  · 아군 제공권(CAP) 출격 밀도 vs 적 위협 → 셀 target, 관성 갱신(SLOC 통제도 선례).

전술 엔진(engine_combat.py)·해군 캠페인 로직은 **무수정** — 이 모듈은 관측용 산출만
낸다(v19.1). 제공권→해군 교전 패널티 연동은 v19.2. 따라서 enable_air_campaign OFF는
물론, ON이어도 v19.1에서는 해군 outcome을 바꾸지 않는다(독립 산출). 정본 = plan_v19_airforce.md.
"""
from __future__ import annotations

from engine_core import AIR_FORCE_DB

# SLOC 교통로 — engine_campaign.SLOC_ZONES와 동일해야 함(순서·명칭). 순환 import 방지 위해 로컬 정의.
SLOC_ZONES = ['서해', '대한해협', '동해']

# ── 한반도 전역 격자 (coarse — false precision 경계, plan §9) ──────────────────
# 제공권은 "확률장(0~1)"의 추상화지 실제 항적이 아니다. 격자를 촘촘히 하면 없는 정밀도를
# 있는 것처럼 보이게 하므로 의도적으로 성글게(5×6=30셀) 둔다.
THEATER   = {'lat_min': 33.0, 'lat_max': 43.0, 'lon_min': 124.0, 'lon_max': 132.0}
GRID_ROWS = 5
GRID_COLS = 6

# ── 튜닝 상수 (v19.2에서 ON/OFF 기준값 측정 후 조정) ───────────────────────────
_SUP_ALPHA       = 0.30    # 제공권 관성 계수 — 한 틱에 급변 방지(SLOC control α 선례)
_AEW_MULT_PER    = 0.30    # E-737 조기경보기 1대당 CAP 효율 승수(직접 격추 아닌 통제 이득)
_STEALTH_BONUS   = 1.4     # 스텔스기(F-35A) 제공권 기여 배율(생존·침투 우위)
# 적 대공 위협 = 기저(상시 적 전투기·SAM 공역 방어) + 웨이브 규모 환산.
# 기저가 없으면 위협 없는 zone이 자동 제공권 1.0이 되어 열세 편성도 우세로 오판됨.
_BASE_AIR_THREAT = 6.0     # SLOC zone당 상시 적 대공 위협(peer 각축 기준)
_WAVE_AIR_SCALE  = 1.0     # 적 해군 웨이브 규모 → 추가 대공 위협 환산


def _spec(atype: str) -> dict:
    return AIR_FORCE_DB.get(atype, {})


def _cell_zone(lat: float, lon: float) -> str | None:
    """격자 셀 중심 좌표를 SLOC 교통로에 매핑. 해당 없으면 None(내륙·기타 공역)."""
    if lon < 126.0 and 34.0 <= lat <= 38.5:
        return '서해'
    if lat < 35.0:
        return '대한해협'
    if lon > 129.5 and 35.5 <= lat <= 41.5:
        return '동해'
    return None


class AirSuperiorityGrid:
    """한반도 격자 제공권 지도. 셀별 제공권 0~1, SLOC zone에 매핑."""

    def __init__(self):
        self.cells = []
        dlat = (THEATER['lat_max'] - THEATER['lat_min']) / GRID_ROWS
        dlon = (THEATER['lon_max'] - THEATER['lon_min']) / GRID_COLS
        for r in range(GRID_ROWS):
            lat = THEATER['lat_min'] + (r + 0.5) * dlat
            for c in range(GRID_COLS):
                lon = THEATER['lon_min'] + (c + 0.5) * dlon
                self.cells.append({
                    'r': r, 'c': c, 'lat': round(lat, 2), 'lon': round(lon, 2),
                    'zone': _cell_zone(lat, lon), 'sup': 0.5,   # 초기 = 각축(contested)
                })

    def update(self, zone_target: dict):
        """zone_target: {zone: 목표 제공권 0~1}. 관성 갱신. zone 없는 셀은 0.5 유지."""
        for cell in self.cells:
            z = cell['zone']
            if z is None:
                continue
            tgt = zone_target.get(z, 0.5)
            cell['sup'] = min(1.0, max(0.0, cell['sup'] + _SUP_ALPHA * (tgt - cell['sup'])))

    def zone_superiority(self) -> dict:
        """SLOC zone별 평균 제공권."""
        agg = {}
        for z in SLOC_ZONES:
            vals = [cell['sup'] for cell in self.cells if cell['zone'] == z]
            agg[z] = round(sum(vals) / len(vals), 3) if vals else 0.5
        return agg


class AirUnit:
    """공군 자산 — 작전급 추상(물리 필드 아님). v19.1은 소티율 가중 지속 airpower로
    모델링(모든 정적 필드는 init에서 캐시). 정비·재무장 downtime 상태는 v19.2 정교화 대상."""
    __slots__ = ('aircraft_type', 'side', 'role', 'missions', 'sortie_rate',
                 'zone', 'mission')

    def __init__(self, aircraft_type: str, zone: str | None):
        spec = _spec(aircraft_type)
        self.aircraft_type = aircraft_type
        self.side          = spec.get('side', 'ROK')
        self.role          = spec.get('role', 'multirole')
        self.missions      = spec.get('missions', [])
        self.sortie_rate   = float(spec.get('sortie_rate', 1.0))
        self.zone          = zone
        self.mission       = None


# ── 공군 편성 프리셋 (기본 패키지) ─────────────────────────────────────────────
AIR_FORCE_PRESETS = {
    '한국 공군 단독': [
        ('KF-21 보라매', 8), ('KF-16 파이팅팰컨', 8), ('F-35A 라이트닝 II', 4),
        ('F-15K 슬램이글', 6), ('E-737 피스아이', 1), ('RQ-4 글로벌호크', 1),
    ],
    '한미 연합 공군 패키지': [
        ('KF-21 보라매', 8), ('KF-16 파이팅팰컨', 8), ('F-35A 라이트닝 II', 6),
        ('F-15K 슬램이글', 6), ('F-16 파이팅팰컨', 12), ('B-1B 랜서', 2),
        ('E-737 피스아이', 1), ('RQ-4 글로벌호크', 2),
    ],
    '최소 방공 (제공권 열세)': [
        ('KF-16 파이팅팰컨', 4), ('KF-21 보라매', 2),
    ],
}
_DEFAULT_AIR_PRESET = '한미 연합 공군 패키지'


def build_air_force(cfg: dict) -> list:
    """cfg → AirUnit 리스트. air_force_custom 우선, 없으면 air_force_preset(기본 한미 연합)."""
    custom = cfg.get('air_force_custom')
    if custom:
        types = [(t['type'], int(t.get('count', 1))) for t in custom]
    else:
        preset = cfg.get('air_force_preset', _DEFAULT_AIR_PRESET)
        types = AIR_FORCE_PRESETS.get(preset, AIR_FORCE_PRESETS[_DEFAULT_AIR_PRESET])
    units = []
    for atype, cnt in types:
        if atype not in AIR_FORCE_DB:
            continue
        for _ in range(max(0, cnt)):
            units.append(AirUnit(atype, SLOC_ZONES[len(units) % len(SLOC_ZONES)]))
    return units


class AirCampaign:
    """공군 작전 층 — 격자 제공권 + 공군 전력. CampaignEngine이 매 틱 tick() 호출.

    v19.1은 제공권을 **산출만** 한다(해군 교전 무영향, 연동은 v19.2). 지속 CAP 제공권을
    소티율 가중 airpower로 모델링 — 각 CAP기가 매 틱 sortie_rate 만큼 제공권에 기여하고,
    누적 소티는 sortie_rate/24로 집계(실제 일일 출격수 규모). 정비·재무장 downtime은 v19.2."""

    def __init__(self, cfg: dict):
        self.units    = build_air_force(cfg)
        self.grid     = AirSuperiorityGrid()
        self._cap_acc   = 0.0   # 누적 CAP 소티(sortie-equivalent)
        self._recon_acc = 0.0   # 누적 정찰 소티
        self._tl_sup    = []    # 틱별 평균 제공권 시계열(단일 실행 시각화용)

    def tick(self, zone_threat: dict):
        """1시간 공군 틱. zone_threat: {zone: truth 위협도}(해군 캠페인이 제공)."""
        # 1) 임무 배정(CAP를 고위협 SLOC zone에 라운드로빈)
        self._assign(zone_threat)
        # 2) 조기경보 승수(체공 중인 E-737 수)
        aew_mult = 1.0 + _AEW_MULT_PER * sum(1 for u in self.units if 'AEW' in u.missions)
        # 3) zone별 아군 제공권 전력 + 소티 집계
        zone_power = {z: 0.0 for z in SLOC_ZONES}
        for u in self.units:
            if u.mission == 'CAP' and u.zone in zone_power:
                p = u.sortie_rate * (_STEALTH_BONUS if 'stealth' in u.role else 1.0)
                zone_power[u.zone] += p * aew_mult
                self._cap_acc += u.sortie_rate / 24.0
            elif u.mission == 'recon':
                self._recon_acc += u.sortie_rate / 24.0
        # 4) 제공권 격자 갱신 — target = 아군 제공권 / (아군 + 적 대공위협)
        zone_target = {}
        for z in SLOC_ZONES:
            fp = zone_power[z]
            et = _BASE_AIR_THREAT + float(zone_threat.get(z, 0.0)) * _WAVE_AIR_SCALE
            zone_target[z] = 1.0 if (fp + et) <= 0 else fp / (fp + et)
        self.grid.update(zone_target)
        zs = self.grid.zone_superiority()
        self._tl_sup.append(round(sum(zs.values()) / len(SLOC_ZONES), 3))

    def _assign(self, zone_threat: dict):
        """임무 배정 — CAP기는 고위협 SLOC zone 우선(라운드로빈), 정찰기는 ISR,
        전략폭격기는 대기(v19.4), 조기경보기는 전역 통제(승수로만 반영)."""
        zones_by_threat = sorted(SLOC_ZONES, key=lambda z: zone_threat.get(z, 0.0), reverse=True)
        ci = 0
        for u in self.units:
            ms = u.missions
            if u.role == 'isr' and 'recon' in ms:
                u.mission = 'recon'; u.zone = None
            elif u.role == 'aew':
                u.mission = None                 # 통제 이득은 aew_mult로 반영
            elif 'CAP' in ms:
                u.zone = zones_by_threat[ci % len(zones_by_threat)]
                u.mission = 'CAP'; ci += 1
            elif 'strike' in ms:
                u.mission = 'strike'; u.zone = None   # v19.4 전략폭격 대기
            else:
                u.mission = None

    def zone_superiority(self) -> dict:
        """SLOC zone별 평균 제공권 — v19.2 해군 교전 연동(_tick_engagements)이 호출."""
        return self.grid.zone_superiority()

    def summary(self) -> dict:
        """CampaignEngine._compile이 결과 dict에 병합할 공군 지표."""
        zs = self.grid.zone_superiority()
        return {
            'air_enabled':          True,
            'air_superiority':      zs,                                   # zone별 제공권 0~1
            'mean_air_superiority': round(sum(zs.values()) / len(zs), 3) if zs else 0.0,
            'air_units':            len(self.units),
            'air_sorties':          int(self._cap_acc + self._recon_acc),
            'air_cap_sorties':      int(self._cap_acc),
            'air_recon_sorties':    int(self._recon_acc),
            'air_timeline':         {'superiority': self._tl_sup},
        }
