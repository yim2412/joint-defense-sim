# -*- coding: utf-8 -*-
"""
engine_army.py — 지상군 작전급 층 (v20.2b)

v18 해군 캠페인(engine_campaign) + v19 공군 층(engine_airforce) 위에 얹는 **지상 층**.
범위는 해상 작전의 접점만 — **연안 방공 포대(CoastalSAMSite)**. 전면 지상전(전차·야포·
지형 기동)은 범위 밖(설계 결정, plan_v20_army.md §8).

핵심 가치: 연안 방공망이 **함대 상공·대함탄도탄(ASBM)을 함께 막는 우산**이 된다.
  - 구역별 BMD 요격 자산(어쇼어 SM-3·THAAD·L-SAM·패트리엇 PAC-3·천궁-II)을 편성.
  - ASBM(DF-21D 등) 위협 구역 교전은 **전술 정밀 교전으로 강제**하고, 이 포대 재고를
    전술 cfg에 주입 → v18.03의 검증된 4계층 요격 로직이 실측한다(새 물리 추가 없음).
  - 발사한 만큼 재고를 **틱 간 차감**(CampaignShip.ammo 패턴) → 소진 시 방어 저하.

아키텍처 규약(v18·v19 계승):
  - CampaignEngine이 이 모듈을 **조합**(compose)만 한다. 전술 엔진(engine_combat) 무수정.
  - `enable_army_campaign` OFF면 생성조차 안 됨 → v19 캠페인과 bit-identical.
  - 결정론: rng 미사용(재고 차감·가산은 전부 결정론).

v20.4 예약: CoastalSAMSite.suppression(적 SEAD 제압도) — 지금은 0 고정(정적 방어 자산).
"""
from __future__ import annotations

from engine_core import ENEMY_DB

# ── 구역별 연안 방공 포대 프리셋 ────────────────────────────────────────────
# 자산 구성 = v18.03의 지상 BMD 4계층. 값은 요격탄 재고(발).
# 실제 편제 근사: 천궁-II 포대 = 발사대 4기 × 8셀 = 32발 · L-SAM은 상층이라 소량.
COASTAL_SAM_PRESETS: dict[str, dict] = {
    '없음': {},
    '연안 방공 기본': {   # 하층 위주 — 저비용 점방어
        '천궁-II': 32, 'L-SAM': 8,
    },
    '연안 방공 강화': {   # 5계층 완편 — 한·미 통합 BMD
        'SM-3 (어쇼어)': 16, 'THAAD 요격탄': 16, 'L-SAM': 16,
        'PAC-3 MSE': 16, '천궁-II': 32,          # v20.1: 패트리엇(종말 중층) 추가
    },
    '한국형 BMD (KAMD)': {   # 국산 계층만(어쇼어·THAAD·패트리엇 없이 자주 방어)
        'L-SAM': 16, '천궁-II': 32,
    },
    '한미 연합 종말방어': {   # v20.1: 미측 종말 자산 위주(THAAD + 패트리엇)
        'THAAD 요격탄': 16, 'PAC-3 MSE': 16, '천궁-II': 32,
    },
}

# 포대 자산 → 전술 cfg 키(재고 주입용). v18.03 _ashore_defense가 소비하는 키와 1:1.
_ASSET_CFG_KEY: dict[str, tuple[str, str]] = {
    # 자산명: (enable 플래그, stock 키)
    'SM-3 (어쇼어)': ('enable_ashore',   'ashore_sm3_stock'),
    'THAAD 요격탄':  ('enable_thaad',    'thaad_stock'),
    'L-SAM':         ('enable_lsam',     'lsam_stock'),
    'PAC-3 MSE':     ('enable_patriot',  'patriot_stock'),   # v20.1
    '천궁-II':       ('enable_chungung', 'chungung_stock'),
}

# 전술 결과의 발사 통계 키 → 자산명(재고 차감용)
_FIRED_STAT_KEY: dict[str, str] = {
    'ashore_sm3_fired': 'SM-3 (어쇼어)',
    'thaad_fired':      'THAAD 요격탄',
    'lsam_fired':       'L-SAM',
    'patriot_fired':    'PAC-3 MSE',   # v20.1
    'chungung_fired':   '천궁-II',
}

# 대리모델(비정밀) 교전에서 연안 방공이 주는 승률 가산 — 잔여 재고 비율에 비례.
# 정밀 교전은 전술 엔진이 실측하므로 이 가산을 쓰지 않는다(이중 계상 방지).
_DEFENSE_BONUS_MAX = 0.15   # 완편 포대가 대리모델 win_p·score에 주는 최대 가산

# ── v20.3 상륙작전 ──────────────────────────────────────────────────────────
# 상륙 가능 함정(SHIP_DB) → 수송 능력(대대 상당). 독도함급이 가장 크다.
AMPHIB_SHIP_LIFT: dict[str, float] = {
    'LPH': 3.0,   # 강습상륙함(독도함급) — 헬기·공기부양정 동시 운용
    'LPD': 2.0,   # 상륙함(San Antonio급)
    'LST': 1.0,   # 상륙함(천왕봉급)
}
_EMBARK_H          = 6      # 적재 소요(시간)
_TRANSIT_H         = 6      # 목표 해안까지 항해(시간)
_ASSAULT_RATE      = 0.20   # 상륙 단계 틱당 기본 진척(3단계 곱을 곱해 실제 진척 산출)
_BEACHHEAD_THRESH  = 1.0    # 진척 누적이 이 값에 도달하면 교두보 확보
# 3단계 각각의 성공 확률 하한/기울기 — 곱연산이라 한 단계만 무너져도 상륙이 정체된다.
_P_TRANSIT_BASE    = 0.15   # 교통로가 완전히 막혀도 최소 잠입 가능성
_P_TRANSIT_SLOPE   = 0.85   # SLOC 통제도에 비례
_P_AIRCOVER_BASE   = 0.20   # 제공권 0이어도 최소 엄호(함대 방공)
_P_AIRCOVER_SLOPE  = 0.80   # 제공권에 비례
_P_ASSAULT_BASE    = 0.10   # 무호위 강행 상륙(대안 상륙)
_P_ASSAULT_SLOPE   = 0.90   # 호위 함대 함포 지원에 비례
_ESCORT_FULL       = 3.0    # 호위 함정 3척이면 함포 지원 만점
# 진척이 이 시간(h) 동안 임계 미만이면 상륙 실패(작전 중지) — 무한 정체 방지
_ASSAULT_TIMEOUT_H = 48
_ASSAULT_MIN_RATE  = 0.01   # 이 미만 진척은 '정체'로 계산

# ── v20.4 도미노: 연안 방공 ↔ 제공권 ↔ 해상 교통로 ─────────────────────────
# 도미노가 성립하려면 연안 방공망이 **제공권에 기여**해야 한다 — 살아있는 연안 SAM은
# 적 항공기의 접근을 억제하기 때문. 그 연결이 있어야 비로소:
#   적 SEAD → 연안 SAM 제압 → 방공 기여 상실 → 제공권↓ → 해상 교통로 압박
# 의 연쇄가 돈다(v19.3 아군 SEAD → 적 IADS 제압의 정확한 거울).
_COASTAL_AIRDEF_POWER = 4.0   # 완편·무피해 포대가 그 구역 아군 제공권 전력에 더하는 값
                              #  (engine_airforce._BASE_AIR_THREAT=6.0과 같은 척도)
# 적 SEAD — 적이 제공권을 쥘수록 우리 연안 방공망을 제압한다(결정론).
#   제압/복구의 균형이 도미노의 성립 조건이다. 아군이 하늘을 쥐면(적 제공권 낮음) 제압이
#   복구를 못 이겨 방공망이 버티고, 제공권을 내주면 제압이 축적돼 연쇄가 시작된다.
#   손익분기: 적 제공권 ≈ 복구율/계수 = (1/48)/0.10 ≈ 0.21 — 적이 20% 이상 하늘을 잡아야 뚫린다.
_ENEMY_SEAD_PER_EFFORT = 0.10   # 적 제공권 1.0당 틱당 제압 증가(보수적 — 과대평가 방지)
_COASTAL_SUPPRESS_CAP  = 0.85   # 제압 상한 — 완전 무력화는 못 한다(v19.3과 동일한 보수 BDA)
_COASTAL_RECOVERY_H    = 48     # 무대응 시 완전 복구까지 시간(포대 재전개·정비 — 항공기 재출격보다 느리다)

# 상륙 성공/실패가 전역 승패에 기여하는 가중치. outcome은 (1-W)·교통로통제 + W·상륙점수.
# 상륙 임무를 안 걸면 이 항 자체가 없다(기존 판정 그대로).
AMPHIB_OUTCOME_W   = 0.35
# 전역 종료 시점에 상륙이 아직 진행 중(assault)이면 진척을 그대로 인정하지 않는다.
# 상륙의 작전 목표는 '교두보 확보'라는 이진 성과 — 90% 진척한 미완 상륙을 성공에 준하게
# 쳐주면 교두보를 못 얻고도 승리 판정이 나온다(감사 발견). 미완은 절반만 인정.
_AMPHIB_PARTIAL_CREDIT = 0.5


def scrub_ground_bmd(tcfg: dict):
    """전술 cfg에서 지상 BMD 관련 키를 전부 걷어낸다(비활성·재고 0).

    연안 방공이 켜진 캠페인에서 **지상 BMD의 유일한 권위는 연안 포대**다. 사용자가 단발
    탭에서 켜 둔 BMD 토글(예: enable_ashore + ashore_sm3_stock=24)이 캠페인 cfg에 실려
    전술 교전으로 새어 들어가면, 포대가 보유하지도 않은 자산이 매 교전 공짜로 발사되고
    재고 차감도 안 된다(차감은 포대 보유분만).

    ⚠ 세척은 **포대 유무·재고 유무와 무관하게** 수행해야 한다. 포대가 없는 구역이나
    재고가 소진된 포대의 구역만 골라 세척을 건너뛰면, 정작 '방어가 사라져야 할 상황'에서
    UI 토글이 부활해 요격탄이 무한 리필된 것처럼 동작한다 — 재고 소진이 방어 저하로
    이어진다는 v20.2b의 핵심 가치가 조용히 무력화된다(종합 감사 발견)."""
    for en_key, stock_key in _ASSET_CFG_KEY.values():
        tcfg[en_key]    = False
        tcfg[stock_key] = 0


def zone_has_asbm(enemy_fleet: list) -> bool:
    """구역 적 편성에 대함 탄도미사일(ASBM)이 있는가 — 정밀 교전 라우팅 트리거.
    enemy_fleet 원소 = {'preset': <ENEMY_DB 키>, 'count': n}."""
    for e in enemy_fleet:
        info = ENEMY_DB.get(e.get('preset', ''), {})
        if info.get('is_asbm'):
            return True
    return False


class CoastalSAMSite:
    """연안 고정 방공 포대 — 불침·기동 없음(고정 자산). 구역당 1개."""
    __slots__ = ('zone', 'assets', 'initial', 'suppression', 'recovery_h')

    def __init__(self, zone: str, assets: dict):
        self.zone        = zone
        self.assets      = dict(assets)    # {자산명: 잔여 재고}
        self.initial     = dict(assets)    # 초기 재고(잔여율 계산용)
        # v20.4: 적 SEAD 제압도(0=완전 활성 / 1=완전 제압). 무대응 시 recovery_h에 걸쳐 복구.
        self.suppression = 0.0
        self.recovery_h  = _COASTAL_RECOVERY_H

    @property
    def total_remaining(self) -> int:
        return sum(self.assets.values())

    @property
    def readiness(self) -> float:
        """잔여 재고 비율 0~1 (초기 재고 대비). 소진될수록 방어력 저하."""
        init = sum(self.initial.values())
        if init <= 0:
            return 0.0
        return max(0.0, min(1.0, self.total_remaining / init)) * (1.0 - self.suppression)

    def inject_into(self, tcfg: dict):
        """전술 cfg에 이 포대의 BMD 계층 자산을 어쇼어 자산으로 주입(잔여 재고 기준).
        재고 0인 자산은 enable을 켜지 않는다 → 전술 엔진이 그 계층을 건너뜀.

        ⚠ 먼저 지상 BMD 관련 키를 **전부 걷어낸다**. 사용자가 단발용으로 켜 둔 BMD 토글
        (예: enable_ashore + ashore_sm3_stock=24)이 tcfg에 묻어 오면, 포대가 보유하지 않은
        자산이 매 교전 공짜로 발사되고 재고 차감도 안 돼(차감은 포대 보유분만) 연안 방공
        효과가 과대평가된다. 캠페인에서 지상 BMD의 유일한 권위는 이 포대다.

        ⚠ v20.4: 제압(suppression)된 만큼 **실제 교전 가용 재고도 줄인다**. 제압을 제공권에만
        반영하고 요격에는 안 쓰면, 방공망이 85% 제압당해도 ASBM 정밀 교전에선 요격탄이 그대로
        나가는 불일치가 생긴다(감사 발견)."""
        scrub_ground_bmd(tcfg)   # 세척은 호출부(inject_tactical)에서도 항상 수행 — 여기선 멱등
        usable = 1.0 - max(0.0, min(1.0, self.suppression))
        for asset, stock in self.assets.items():
            key = _ASSET_CFG_KEY.get(asset)
            if not key or stock <= 0:
                continue
            avail = int(stock * usable)   # 제압된 포대는 그만큼 사격통제를 잃는다
            if avail <= 0:
                continue
            en_key, stock_key = key
            tcfg[en_key]    = True
            tcfg[stock_key] = avail

    def consume_abstract(self, n_threats: int) -> int:
        """대리모델(비정밀) 교전에서의 요격탄 소모 — 하층(싼 것)부터 차감.
        정밀 경로는 실측 발사 수를 쓰지만, 대리모델 경로는 발사 수를 알 수 없으므로
        '위협 1개당 요격탄 1발'로 근사한다. 이게 없으면 포대가 재고를 한 발도 안 쓰면서
        전역 내내 최대 방공 가산을 주는 비일관이 생긴다(readiness가 영원히 1.0).
        결정론 — rng 미사용."""
        need = max(0, int(n_threats))
        used = 0
        for asset in ('천궁-II', 'PAC-3 MSE', 'L-SAM',
                      'THAAD 요격탄', 'SM-3 (어쇼어)'):   # 하층(싼 것) → 상층
            if need <= 0:
                break
            have = self.assets.get(asset, 0)
            take = min(have, need)
            if take > 0:
                self.assets[asset] -= take
                need -= take
                used += take
        return used

    def consume_from_result(self, result: dict) -> int:
        """전술 교전 결과의 실제 발사 수만큼 재고를 차감(틱 간 유지). 반환=총 소모 발수."""
        used = 0
        for stat_key, asset in _FIRED_STAT_KEY.items():
            fired = int(result.get(stat_key, 0) or 0)
            if fired <= 0 or asset not in self.assets:
                continue
            take = min(fired, self.assets[asset])
            self.assets[asset] -= take
            used += take
        return used


class AmphibiousForce:
    """상륙군 부대 — 상륙함에 적재돼 목표 해안으로 이동, 교두보를 확보한다.
    (v18 CampaignShip 상태머신 복제: 상태 + ETA + 진척)

    3단계 순차 곱연산(로드맵 지침): **수송 → 항공 엄호 → 상륙**.
    각 단계 성공 확률을 캠페인 상태에서 도출해 곱한 값이 그 틱의 진척률이 된다.
    한 단계만 무너져도(교통로 차단·제공권 상실·호위 전멸) 상륙이 정체된다 —
    이게 상륙작전이 해·공 협조의 정점인 이유를 모델로 드러낸다.

    결정론: rng 미사용(진척은 상태에서 결정론적으로 계산).
    """
    __slots__ = ('name', 'zone', 'state', 'lift', 'progress', 'eta_h',
                 'stalled_h', 'p_transit', 'p_aircover', 'p_assault')

    def __init__(self, name: str, zone: str, lift: float):
        self.name      = name
        self.zone      = zone      # 목표 해안(SLOC 구역)
        self.state     = 'embark'  # embark → transit → assault → beachhead / failed
        self.lift      = lift      # 수송 능력(대대 상당) — 상륙함 편성에서 산출
        self.progress  = 0.0       # 교두보 확보 진척 0~1
        self.eta_h     = _EMBARK_H
        self.stalled_h = 0         # 진척이 멈춘 누적 시간
        # 마지막 틱의 단계별 확률(보고서·투명성)
        self.p_transit = self.p_aircover = self.p_assault = 0.0

    @property
    def done(self) -> bool:
        return self.state in ('beachhead', 'failed')

    def tick(self, control: float, air_sup: float, escort_n: int, coastal_def: float):
        """1시간 틱.
        control     — 목표 구역 SLOC 통제도(0~1): 상륙함이 해안에 도달할 수 있는가
        air_sup     — 목표 구역 제공권(0~1): 상륙 선단을 엄호할 수 있는가
        escort_n    — 목표 구역 호위 함정 수: 함포 지원(대안 상륙 제압)
        coastal_def — 적 연안 방어 강도(0~1): 상륙 저항
        """
        if self.done:
            return
        if self.state == 'embark':
            self.eta_h -= 1
            if self.eta_h <= 0:
                self.state = 'transit'
                self.eta_h = _TRANSIT_H
            return
        if self.state == 'transit':
            # 수송 단계 — 교통로가 막혀 있으면 항해가 지연된다(통제도에 반비례).
            self.p_transit = _P_TRANSIT_BASE + _P_TRANSIT_SLOPE * max(0.0, min(1.0, control))
            self.eta_h -= 1
            if self.eta_h <= 0:
                if self.p_transit < 0.35:
                    # 교통로가 사실상 차단 — 선단이 접근하지 못하고 회항(작전 실패)
                    self.state = 'failed'
                else:
                    self.state = 'assault'
            return
        # assault — 3단계 곱연산으로 교두보 진척
        self.p_transit  = _P_TRANSIT_BASE  + _P_TRANSIT_SLOPE  * max(0.0, min(1.0, control))
        self.p_aircover = _P_AIRCOVER_BASE + _P_AIRCOVER_SLOPE * max(0.0, min(1.0, air_sup))
        escort = min(1.0, escort_n / _ESCORT_FULL)
        self.p_assault  = (_P_ASSAULT_BASE + _P_ASSAULT_SLOPE * escort) \
                          * (1.0 - max(0.0, min(1.0, coastal_def)))
        rate = _ASSAULT_RATE * self.p_transit * self.p_aircover * self.p_assault
        self.progress = min(1.0, self.progress + rate)
        if self.progress >= _BEACHHEAD_THRESH:
            self.state = 'beachhead'
            return
        # 정체 감시 — 진척이 사실상 멈춘 채 오래 끌면 작전 중지(무한 정체 방지)
        if rate < _ASSAULT_MIN_RATE:
            self.stalled_h += 1
            if self.stalled_h >= _ASSAULT_TIMEOUT_H:
                self.state = 'failed'
        else:
            self.stalled_h = 0


class ArmyCampaign:
    """지상 층 진입점 (v19 AirCampaign 대칭). CampaignEngine이 조합해 호출."""

    def __init__(self, cfg: dict, zones: list):
        self.cfg   = dict(cfg)
        self.zones = list(zones)
        self.coastal_enabled = bool(cfg.get('enable_coastal_sam', False))
        self.sites: dict[str, CoastalSAMSite] = {}
        if self.coastal_enabled:
            self._build_sites()
        self.n_asbm_precise = 0    # ASBM 때문에 정밀 교전으로 강제된 횟수(투명성)
        self.n_intercepts   = 0    # 연안 포대가 발사한 총 요격탄 수
        # v20.4 도미노 — 적 SEAD가 연안 방공망을 제압(OFF면 suppression 0 유지)
        self.enemy_sead = bool(cfg.get('enable_enemy_sead', False))
        # v20.3 상륙작전 — enable_amphibious ON일 때만 편성(OFF면 상륙 항 자체가 없다)
        self.amphib_enabled = bool(cfg.get('enable_amphibious', False))
        self.landing: AmphibiousForce | None = None
        if self.amphib_enabled:
            self.landing = self._build_landing()
        self.landing_log: list = []   # 상륙 임무 타임라인(보고서)

    def _build_sites(self):
        """구역별 포대 편성. cfg['coastal_sam_zones'] = {zone: 프리셋명} 이면 구역별 지정,
        없으면 cfg['coastal_sam_preset']을 전 구역에 동일 배치."""
        per_zone = self.cfg.get('coastal_sam_zones')
        default  = self.cfg.get('coastal_sam_preset', '연안 방공 기본')
        for z in self.zones:
            name = (per_zone or {}).get(z, default)
            assets = COASTAL_SAM_PRESETS.get(name, {})
            if assets:
                self.sites[z] = CoastalSAMSite(z, assets)

    def _build_landing(self) -> 'AmphibiousForce | None':
        """상륙 선단 편성 — 아군 함대의 상륙함(LPH·LPD·LST)에서 수송 능력을 산출.
        cfg['amphib_ships'] = {'LPH': 1, 'LST': 2} 형태로 직접 지정 가능(없으면 기본 선단).
        목표 해안은 cfg['amphib_zone'](없으면 첫 구역)."""
        ships = self.cfg.get('amphib_ships') or {'LPH': 1, 'LST': 2}
        lift = sum(AMPHIB_SHIP_LIFT.get(t, 0.0) * int(n) for t, n in ships.items())
        if lift <= 0:
            return None    # 상륙함이 없으면 상륙작전 불가
        zone = self.cfg.get('amphib_zone') or (self.zones[0] if self.zones else '')
        return AmphibiousForce('상륙 선단', zone, lift)

    # ── 틱 ────────────────────────────────────────────────────────────────
    def tick(self, t_h: int = 0, control: dict | None = None,
             air_sups: dict | None = None, escorts: dict | None = None):
        """1시간 틱.
        v20.4: 적 SEAD가 연안 방공망을 제압(복구 → 제압 순, v19.3 아군 SEAD와 동형).
        v20.3: 상륙작전 3단계 곱연산 진척.
        연안 포대 재고는 교전에서만 소모(여기선 안 건드림).

        air_sups는 **직전 틱의 제공권**이다(캠페인이 army → air 순으로 틱해 순환을 끊는다).
        1틱 지연이 곧 도미노의 시간 구조 — 제공권을 잃고 나서 방공망이 제압당한다.
        """
        self._tick_enemy_sead(air_sups)
        lf = self.landing
        if lf is None or lf.done:
            return
        z = lf.zone
        prev = lf.state
        lf.tick(control=(control or {}).get(z, 1.0),
                air_sup=(air_sups or {}).get(z, 0.5),
                escort_n=(escorts or {}).get(z, 0),
                coastal_def=float(self.cfg.get('amphib_coastal_defense', 0.4)))
        if lf.state != prev:
            self.landing_log.append({
                't_h': t_h, 'state': lf.state, 'zone': z,
                'progress': round(lf.progress, 3),
                'p_transit': round(lf.p_transit, 3),
                'p_aircover': round(lf.p_aircover, 3),
                'p_assault': round(lf.p_assault, 3),
            })

    def _tick_enemy_sead(self, air_sups: dict | None):
        """v20.4: 적 SEAD/DEAD — 적이 제공권을 쥘수록 아군 연안 방공망을 제압한다.
        v19.3(아군 SEAD → 적 IADS)의 정확한 거울: 결정론·제압 상한·무대응 복구.
        enable_enemy_sead OFF면 무동작(suppression 0 유지 → v20.3 bit-identical)."""
        if not self.sites:
            return
        # 공군 층이 없으면(air_sups=None) 제공권 개념 자체가 없다 → 도미노가 성립하지 않는다.
        # 이때 제압만 돌리면 2단계(제공권 하락)가 없는 채로 포대가 이유 없이 무력화된다
        # (감사 발견). 적 SEAD는 공군 작전급과 함께 켜야 의미가 있다.
        for site in self.sites.values():
            # 0) 복구 먼저 — 적이 손을 놓으면 포대가 재전개된다(v19.3과 같은 순서)
            if site.suppression > 0:
                site.suppression = max(0.0, site.suppression - 1.0 / site.recovery_h)
            if not self.enemy_sead or air_sups is None:
                continue
            # 1) 제압 — 적 제공권(= 1 - 아군 제공권)에 비례. 아군이 하늘을 쥐면 제압 없음.
            enemy_air = 1.0 - max(0.0, min(1.0, air_sups.get(site.zone, 0.5)))
            if enemy_air > 0:
                site.suppression = min(_COASTAL_SUPPRESS_CAP,
                                       site.suppression + _ENEMY_SEAD_PER_EFFORT * enemy_air)

    def air_defense(self) -> dict:
        """v20.4: 구역별 연안 방공망이 아군 제공권에 더하는 전력.
        살아있는(재고 있고 제압 안 된) 포대가 적 항공기 접근을 억제한다 —
        **이 연결이 도미노의 첫 고리**다. 포대가 없거나 소진·제압되면 0.
        공군 층(engine_airforce)이 제공권 격자를 갱신할 때 아군 전력에 가산한다."""
        return {z: _COASTAL_AIRDEF_POWER * s.readiness for z, s in self.sites.items()}

    def mean_suppression(self) -> float:
        """연안 방공망 평균 제압도(0~1) — 도미노 진행 정도(보고서·결과)."""
        if not self.sites:
            return 0.0
        return sum(s.suppression for s in self.sites.values()) / len(self.sites)

    # ── 상륙 조회 API ──────────────────────────────────────────────────────
    def landing_outcome_weight(self) -> float | None:
        """전역 승패에 결합할 상륙 점수(0~1). 상륙 임무가 없으면 None → 기존 판정 그대로.

        - beachhead(교두보 확보) = 1.0 — 작전 목표 달성
        - failed(회항·작전 중지)  = 0.0 — 진척을 전혀 인정하지 않음
        - 그 외(전역 종료 시 아직 진행 중) = 진척 × 0.5 — 미완은 절반만 인정.
          진척을 그대로 주면 교두보를 못 얻고도 승리 판정이 난다(감사 발견).
        """
        lf = self.landing
        if lf is None:
            return None
        if lf.state == 'beachhead':
            return 1.0
        if lf.state == 'failed':
            return 0.0
        return max(0.0, min(1.0, lf.progress)) * _AMPHIB_PARTIAL_CREDIT

    def outcome_blend(self, mean_control: float) -> float:
        """전역 승패 점수 = (1-W)·교통로 통제 + W·상륙 점수.
        상륙 임무가 없으면 교통로 통제 그대로(기존 판정 bit-identical)."""
        w = self.landing_outcome_weight()
        if w is None:
            return mean_control
        return (1.0 - AMPHIB_OUTCOME_W) * mean_control + AMPHIB_OUTCOME_W * w

    # ── 캠페인이 쓰는 조회 API ────────────────────────────────────────────
    def site_in(self, zone: str) -> CoastalSAMSite | None:
        site = self.sites.get(zone)
        if site is None or site.total_remaining <= 0:
            return None    # 재고 소진 포대는 방어 기여 없음
        return site

    def force_precise(self, zone: str, enemy_fleet: list) -> bool:
        """이 구역 교전을 전술 정밀로 강제할 것인가.
        = ASBM 위협이 있고 그걸 요격할 연안 포대가 실제로 있을 때.
        (포대 없으면 정밀로 돌려도 함대 자체 방어뿐 → 대리모델 유지가 경제적)"""
        if not self.coastal_enabled:
            return False
        return self.site_in(zone) is not None and zone_has_asbm(enemy_fleet)

    def inject_tactical(self, zone: str, tcfg: dict) -> bool:
        """정밀 교전 tcfg에 구역 포대 자산 주입. 주입했으면 True.

        연안 방공이 켜져 있으면 **주입 여부와 무관하게 먼저 세척**한다. 포대가 없는 구역·
        재고가 소진된 포대는 지상 BMD 기여가 0이어야 하는데, 세척을 건너뛰면 사용자의 단발
        BMD 토글이 tcfg에 남아 그 구역에서 요격이 되살아난다(scrub_ground_bmd 참조).
        연안 방공 OFF면 지상 BMD를 포대가 관장하지 않으므로 기존 동작(UI 토글 존중)을 유지."""
        if not self.coastal_enabled:
            return False
        scrub_ground_bmd(tcfg)
        site = self.site_in(zone)
        if site is None:
            return False        # 세척만 하고 주입 없음 → 이 구역 지상 BMD 기여 0
        site.inject_into(tcfg)
        return True

    def consume(self, zone: str, result: dict):
        """정밀 교전 결과의 실제 발사분을 구역 포대 재고에서 차감."""
        site = self.sites.get(zone)
        if site is None:
            return
        self.n_intercepts += site.consume_from_result(result)

    def consume_surrogate(self, zone: str, n_threats: int):
        """대리모델 교전에서 방공 가산을 준 만큼 요격탄도 소모(위협당 1발 근사).

        제압분만큼 가용 재고를 깎는 정밀 경로(inject_into)와 'usable' 정의를 맞춘다.
        제압을 무시하고 위협 수만큼 만발 차감하면, 사격통제를 잃어 가산은 거의 0인 포대가
        요격탄만 태우는 불일치가 생긴다(종합 감사 발견)."""
        site = self.sites.get(zone)
        if site is None:
            return
        usable = 1.0 - max(0.0, min(1.0, site.suppression))
        self.n_intercepts += site.consume_abstract(int(n_threats * usable))

    def zone_defense_bonus(self, zone: str) -> float:
        """대리모델(비정밀) 교전에 주는 승률·점수 가산 (0~_DEFENSE_BONUS_MAX).
        연안 포대가 함대 방공을 보강하는 효과의 작전급 추상 — 잔여 재고에 비례.
        정밀 경로에선 실제 요격이 계산되므로 호출하지 않는다(이중 계상 방지)."""
        site = self.site_in(zone)
        if site is None:
            return 0.0
        return _DEFENSE_BONUS_MAX * site.readiness

    def status(self) -> dict:
        """보고서·결과 집계용."""
        out = {
            'coastal_sites': {
                z: {'assets': dict(s.assets), 'initial': dict(s.initial),
                    'readiness': round(s.readiness, 3)}
                for z, s in self.sites.items()
            },
            'n_asbm_precise': self.n_asbm_precise,
            'coastal_intercepts': self.n_intercepts,
            # v20.4 도미노 — 연안 방공망 제압도(적 SEAD)와 제공권 기여
            'coastal_suppression': round(self.mean_suppression(), 3),
            'coastal_airdef': {z: round(v, 2) for z, v in self.air_defense().items()},
        }
        lf = self.landing
        if lf is not None:   # v20.3 상륙작전
            out.update({
                'amphib_enabled':  True,
                'amphib_zone':     lf.zone,
                'amphib_state':    lf.state,
                'amphib_progress': round(lf.progress, 3),
                'amphib_success':  1 if lf.state == 'beachhead' else 0,
                'amphib_lift':     lf.lift,
                'amphib_timeline': self.landing_log,
                # 마지막 틱의 3단계 확률(어느 단계가 상륙을 막았는지 진단)
                'amphib_p_transit':  round(lf.p_transit, 3),
                'amphib_p_aircover': round(lf.p_aircover, 3),
                'amphib_p_assault':  round(lf.p_assault, 3),
            })
        return out
