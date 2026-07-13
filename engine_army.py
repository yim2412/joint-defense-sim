# -*- coding: utf-8 -*-
"""
engine_army.py — 지상군 작전급 층 (v20.2b)

v18 해군 캠페인(engine_campaign) + v19 공군 층(engine_airforce) 위에 얹는 **지상 층**.
범위는 해상 작전의 접점만 — **연안 방공 포대(CoastalSAMSite)**. 전면 지상전(전차·야포·
지형 기동)은 범위 밖(설계 결정, plan_v20_army.md §8).

핵심 가치: 연안 방공망이 **함대 상공·대함탄도탄(ASBM)을 함께 막는 우산**이 된다.
  - 구역별 4계층 요격 자산(어쇼어 SM-3·THAAD·L-SAM·천궁-II)을 편성.
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
    '연안 방공 강화': {   # 4계층 완편 — 한·미 통합 BMD
        'SM-3 (어쇼어)': 16, 'THAAD 요격탄': 16, 'L-SAM': 16, '천궁-II': 32,
    },
    '한국형 BMD (KAMD)': {   # 국산 계층만(어쇼어·THAAD 없이 자주 방어)
        'L-SAM': 16, '천궁-II': 32,
    },
}

# 포대 자산 → 전술 cfg 키(재고 주입용). v18.03 _ashore_defense가 소비하는 키와 1:1.
_ASSET_CFG_KEY: dict[str, tuple[str, str]] = {
    # 자산명: (enable 플래그, stock 키)
    'SM-3 (어쇼어)': ('enable_ashore',   'ashore_sm3_stock'),
    'THAAD 요격탄':  ('enable_thaad',    'thaad_stock'),
    'L-SAM':         ('enable_lsam',     'lsam_stock'),
    '천궁-II':       ('enable_chungung', 'chungung_stock'),
}

# 전술 결과의 발사 통계 키 → 자산명(재고 차감용)
_FIRED_STAT_KEY: dict[str, str] = {
    'ashore_sm3_fired': 'SM-3 (어쇼어)',
    'thaad_fired':      'THAAD 요격탄',
    'lsam_fired':       'L-SAM',
    'chungung_fired':   '천궁-II',
}

# 대리모델(비정밀) 교전에서 연안 방공이 주는 승률 가산 — 잔여 재고 비율에 비례.
# 정밀 교전은 전술 엔진이 실측하므로 이 가산을 쓰지 않는다(이중 계상 방지).
_DEFENSE_BONUS_MAX = 0.15   # 완편 포대가 대리모델 win_p·score에 주는 최대 가산


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
        # v20.4 예약 — 적 SEAD 제압도. v20.2b에선 0 고정(정적 방어).
        self.suppression = 0.0
        self.recovery_h  = 0

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
        """전술 cfg에 이 포대의 4계층 자산을 어쇼어 자산으로 주입(잔여 재고 기준).
        재고 0인 자산은 enable을 켜지 않는다 → 전술 엔진이 그 계층을 건너뜀.

        ⚠ 먼저 지상 BMD 관련 키를 **전부 걷어낸다**. 사용자가 단발용으로 켜 둔 BMD 토글
        (예: enable_ashore + ashore_sm3_stock=24)이 tcfg에 묻어 오면, 포대가 보유하지 않은
        자산이 매 교전 공짜로 발사되고 재고 차감도 안 돼(차감은 포대 보유분만) 연안 방공
        효과가 과대평가된다. 캠페인에서 지상 BMD의 유일한 권위는 이 포대다."""
        for en_key, stock_key in _ASSET_CFG_KEY.values():
            tcfg[en_key]    = False
            tcfg[stock_key] = 0
        for asset, stock in self.assets.items():
            key = _ASSET_CFG_KEY.get(asset)
            if not key or stock <= 0:
                continue
            en_key, stock_key = key
            tcfg[en_key]    = True
            tcfg[stock_key] = int(stock)

    def consume_abstract(self, n_threats: int) -> int:
        """대리모델(비정밀) 교전에서의 요격탄 소모 — 하층(싼 것)부터 차감.
        정밀 경로는 실측 발사 수를 쓰지만, 대리모델 경로는 발사 수를 알 수 없으므로
        '위협 1개당 요격탄 1발'로 근사한다. 이게 없으면 포대가 재고를 한 발도 안 쓰면서
        전역 내내 최대 방공 가산을 주는 비일관이 생긴다(readiness가 영원히 1.0).
        결정론 — rng 미사용."""
        need = max(0, int(n_threats))
        used = 0
        for asset in ('천궁-II', 'L-SAM', 'THAAD 요격탄', 'SM-3 (어쇼어)'):   # 하층 → 상층
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

    # ── 틱 ────────────────────────────────────────────────────────────────
    def tick(self, zone_threats: dict | None = None, air_sups: dict | None = None):
        """1시간 틱. v20.2b는 정적 방어(재고는 교전에서만 소모) → 상태 갱신 없음.
        v20.4에서 적 SEAD 제압도(suppression) 증가·복구가 여기 들어온다(그때 인자 사용)."""
        return

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
        """정밀 교전 tcfg에 구역 포대 자산 주입. 주입했으면 True."""
        site = self.site_in(zone)
        if site is None:
            return False
        site.inject_into(tcfg)
        return True

    def consume(self, zone: str, result: dict):
        """정밀 교전 결과의 실제 발사분을 구역 포대 재고에서 차감."""
        site = self.sites.get(zone)
        if site is None:
            return
        self.n_intercepts += site.consume_from_result(result)

    def consume_surrogate(self, zone: str, n_threats: int):
        """대리모델 교전에서 방공 가산을 준 만큼 요격탄도 소모(위협당 1발 근사)."""
        site = self.sites.get(zone)
        if site is None:
            return
        self.n_intercepts += site.consume_abstract(n_threats)

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
        return {
            'coastal_sites': {
                z: {'assets': dict(s.assets), 'initial': dict(s.initial),
                    'readiness': round(s.readiness, 3)}
                for z, s in self.sites.items()
            },
            'n_asbm_precise': self.n_asbm_precise,
            'coastal_intercepts': self.n_intercepts,
        }
