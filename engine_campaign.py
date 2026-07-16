# -*- coding: utf-8 -*-
"""
engine_campaign.py — v18 작전급 캠페인 엔진 (v18.1 코어 루프 MVP)

며칠 단위 전역을 1시간 틱으로 진행하고, 교전이 발생할 때만 v15.2 즉시예측
(forecast_model + featurize)으로 결과를 추정한다. 72시간 전역이 수초에 끝난다.

전술 엔진(engine_combat.py)은 **호출/재사용만** 하고 수정하지 않는다
(BattleEngine이 부모 무수정으로 성공한 선례). → 전술·전장 회귀 bit-identical.

정본 설계 = plan_v18_campaign.md.
"""
from __future__ import annotations
import random
import numpy as np

from engine_core import (SHIP_DB, FLEET_PRESETS, ENEMY_FLEET_PRESETS)
from engine_joint import build_land_stock          # v21.2 함정 지상공격 재고
from forecast_features import featurize, fleet_ships_from_preset

# ── 상수 ──────────────────────────────────────────────────────────────────────
SLOC_ZONES        = ['서해', '대한해협', '동해']   # 해상 교통로 3개 (승패 판정 기준)
HOME_ZONE         = '모항'                          # 기지(안전·수리)
CAMPAIGN_HORIZON_H_DEFAULT = 72                     # 기본 전역 시간(시간)
_HP_RETREAT_FRAC  = 0.4                             # 이 아래로 손상되면 귀항→수리
_DMG_WIN_K        = 0.30                            # 승리 시 아군 피해 계수 (× (1-score))
_DMG_LOSS_K       = 0.60                            # 패배 시 아군 피해 계수
# v18.2 전력 관리 — 수리 기간 차등 + 탄약·연료 재보급
_REPAIR_DAYS_MIN  = 1                               # 경상 최소 수리(일)
_REPAIR_DAYS_MAX  = 14                              # 대파 최대 수리(일) — 교리상 전역 중 복귀 불가 수준
_AMMO_PER_ENGAGEMENT = 0.28                         # 교전 1회당 탄약 소모 비율(추상)
_AMMO_RESUPPLY_FRAC  = 0.20                         # 이 아래로 소진되면 재보급 귀항
_FUEL_PER_TICK       = 0.010                        # 초계 1시간당 연료 소모(72h ≈ 0.72)
_FUEL_RESUPPLY_FRAC  = 0.25                         # 이 아래면 재보급 귀항
_RESUPPLY_AMMO_H     = 48                           # 모항 탄약 재보급 소요(2일)
_RESUPPLY_FUEL_H     = 24                           # 모항 연료 재보급 소요(1일)
# v18.3 임무 배정 — 위협 기반 동적 재배정(그리디)
_REASSIGN_PERIOD_H   = 6                             # 재배정 주기(시간) — 매 틱은 순간이동 비현실
_TRANSIT_H           = 1                             # zone 간 이동 소요(틱) — 이동 중 비가용
# v18.4 전장의 안개 — 적 위치 belief(불완전 정보) + 탐지 갱신 + 시간 감쇠
_FOG_HALFLIFE_H      = 12                            # 미탐지 zone belief 반감기(시간)
_ISR_AIRCRAFT_DEFAULT = 1                            # 초계기 ISR 기본 대수(cfg로 override)
_SAT_INTERVAL_H      = 24                            # 위성 전역 스캔 주기(시간)
_SAT_TRUST           = 0.5                           # 위성 저신뢰 부분 갱신 계수(광역·저해상)
# v18.5 SLOC 정교화 — 연속 통제도 + 통제→보급 피드백 + 우회 보급
_CONTROL_ALPHA         = 0.30    # 통제도 관성 계수 — 한 틱에 급변 방지(적 우세 지속 시에만 붕괴)
_CONTROL_WIN_THRESH    = 0.70    # 평균 통제도 승리 임계
_CONTROL_DRAW_THRESH   = 0.30    # 평균 통제도 무승부 임계(미만은 패배)
_RESUPPLY_CONTROL_FLOOR = 0.20   # 보급선 통제도 하한 — 통제 붕괴 시 재보급 최대 5배(1/0.2) 지연
_REROUTE_EPS           = 0.05    # 우회 보급 판정 최소 통제도 격차(자기 교통로가 이만큼 더 나쁠 때만)
# v19.2 제공권→해군 교전 연동 — factor = BASE + SLOPE·제공권. 각축(0.5)에서 1.0(중립),
# 완전 우세(1.0)→1.4·완전 열세(0.0)→0.6. win_p·score 둘 다 곱연산(사용자 합의 2026-07-08).
_AIR_ENGAGE_BASE  = 0.60
_AIR_ENGAGE_SLOPE = 0.80
# A1 정밀 교전(enable_precise_engagement) — zone 교전을 대리모델 근사 대신 실제 전술
# 단발 시뮬(run_v7_simulation)로 해결해 손실·요격·비용을 진짜 계산(추상 피해 제거).
# 하이브리드: 적 규모 ≥ 임계값인 교전만 정밀, 소규모는 대리모델 유지(성능 예산제).
_PRECISE_MIN_THREATS_DEFAULT = 3   # 이 미만 규모 교전은 대리모델(성능 절약)


def _ship_strength(ship_type: str) -> float:
    """함정 방공 강도 프록시 = 동시교전 채널 수(max_channels).
    이지스>구축함>호위함>소형, 지원·무인함은 낮음 — 강한 함정을 고위협 교통로에 우선 배치."""
    return float(SHIP_DB.get(ship_type, {}).get('max_channels', 0))


def load_forecast_model(path: str | None = None):
    """즉시예측 대리모델 로드. 부재/의존성 없으면 None(호출측이 폴백 처리).
    exe 번들(sys._MEIPASS)·개발환경(__file__ 옆)·cwd 순으로 탐색 — 상대경로만
    쓰면 exe에서 _internal 안의 pkl을 못 찾아 조용히 폴백되므로 반드시 절대경로 해석."""
    import os, sys
    try:
        import joblib
    except Exception:
        return None
    cands = []
    if path:
        cands.append(path)
    else:
        base = getattr(sys, '_MEIPASS', None)
        if base:
            cands.append(os.path.join(base, 'forecast_model.pkl'))
        cands.append(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                  'forecast_model.pkl'))
        cands.append('forecast_model.pkl')
    for p in cands:
        try:
            if os.path.exists(p):
                return joblib.load(p)
        except Exception:
            continue
    return None


def _predict_engagement(model, fleet_ships: list, enemy_fleet: list,
                        weather: str) -> tuple:
    """즉시예측 — (승률, 임무점수, 비용USD). app_main._forecast_predict와 동일 규약."""
    vec = featurize(fleet_ships, enemy_fleet=enemy_fleet, weather=weather).reshape(1, -1)
    models = model['models']
    win   = float(np.clip(models[0].predict(vec)[0], 0.0, 1.0))
    score = float(np.clip(models[1].predict(vec)[0], 0.0, 1.0))
    raw   = float(models[2].predict(vec)[0])
    cost  = float(np.expm1(raw)) if model.get('cost_is_log1p') else raw
    return win, score, max(0.0, cost)


class CampaignShip:
    """캠페인 함정 상태 — 전술 FriendlyShipObj의 작전급 추상(물리 필드 아님).
    v18.2: 탄약·연료 재보급 상태 추가."""
    __slots__ = ('ship_type', 'zone', 'state', 'hp_frac', 'repair_eta_h',
                 'ammo_frac', 'fuel_frac', 'resupply_eta_h',
                 'dest_zone', 'transit_eta_h', 'land_stock')

    def __init__(self, ship_type: str, zone: str):
        self.ship_type      = ship_type
        self.zone           = zone
        # v21.2: 지상공격 재고(현무-3C·토마호크) — 합동 화력 층만 소비한다. 대부분의
        # 함정은 빈 dict(지상공격 능력 없음). 합동 화력 OFF면 아무도 안 건드림.
        self.land_stock     = build_land_stock(ship_type, SHIP_DB)
        self.state          = 'patrol'   # patrol / repair / resupply / transit
        self.hp_frac        = 1.0
        self.repair_eta_h   = 0
        self.ammo_frac      = 1.0        # v18.2: 탄약 잔여
        self.fuel_frac      = 1.0        # v18.2: 연료 잔여
        self.resupply_eta_h = 0
        self.dest_zone      = zone       # v18.3: 재배정 목적지 zone
        self.transit_eta_h  = 0          # v18.3: 이동 잔여 시간(틱)

    @property
    def available(self) -> bool:
        # 초계 상태만 가용 전력(수리·재보급·이동 중 제외)
        return self.state == 'patrol'


class CampaignEngine:
    """작전급 캠페인 1회 실행. 전술 엔진을 교전 해결기로 호출(즉시예측 우선)."""

    def __init__(self, cfg: dict, model=None):
        self.cfg      = dict(cfg)            # 오염 방지(전술 엔진 규약과 동일)
        self.model    = model
        self.weather  = cfg.get('weather', '맑음 (주간)')
        # 축퇴 입력(0·음수) 방어 — 빈 루프로 교전 0인데 통제도 초기값 1.0 유지→오판('win') 방지
        self.horizon_h = max(1, int(cfg.get('campaign_horizon_h', CAMPAIGN_HORIZON_H_DEFAULT)))
        seed = cfg.get('campaign_seed', cfg.get('sim_seed'))
        self.rng = random.Random(seed)

        self.ships   = self._build_force()
        self.waves   = self._build_enemy_waves()   # [{preset, zone, arrive_h, alive}]
        # v18.5: 이진 통제(True/False) → 연속 통제도(0~1). 1.0=완전 통제
        self.control = {z: 1.0 for z in SLOC_ZONES}
        self.t_h     = 0
        self.engagements = []                      # 교전 기록
        self.cost_total  = 0.0
        self._n_reassign = 0                       # v18.3: 누적 재배정 이동 횟수
        self._n_reroute  = 0                       # v18.5: 누적 우회 보급 횟수
        # v18.4 전장의 안개 — 적 위협 belief(불완전 정보) + 마지막 탐지 시각
        self.fog         = bool(cfg.get('enable_campaign_fog', False))
        self.isr_aircraft = int(cfg.get('campaign_isr_aircraft', _ISR_AIRCRAFT_DEFAULT))
        self.sat_interval_h = int(cfg.get('campaign_sat_interval_h', _SAT_INTERVAL_H))
        self.belief      = {z: 0.0 for z in SLOC_ZONES}   # zone별 추정 위협도
        self._last_seen  = {z: 0 for z in SLOC_ZONES}     # zone별 마지막 탐지 t_h
        self._n_missed   = 0                       # 안개로 실제 적>0인데 belief~0인 zone-틱 누적
        # 시계열(단일 실행용)
        self._tl_control = []   # 틱별 통제 교통로 수
        self._tl_force   = []   # 틱별 가용 전력 함정 수
        # 공군 작전급 층 — enable_air_campaign ON일 때만 생성(OFF면 v18 bit-identical).
        # v19.2부터 제공권이 해군 교전(win_p·score)에 연동됨(_tick_engagements).
        # v21.2 합동 화력 — ON이면 적 기지(EnemyBase) 소유권을 **캠페인이 갖고** 공군 층과
        # 공유한다(공군 폭격·해군 순항미사일·육군 지대지가 같은 표적을 때리므로 목록이
        # 갈리면 안 된다). OFF면 표적을 만들지도 않아 공군이 지금처럼 자기 것을 소유
        # → v20 캠페인과 bit-identical.
        #
        # ⚠ 짝 기능 3중 — 합동 화력은 아래가 **전부** 켜져야 값을 한다:
        #   ①enable_strategic_strike : OFF면 EnemyBase가 아예 없다 = 때릴 표적이 없다
        #   ②enable_air_campaign     : 기지 손상 → 적 출항능력 환산(enemy_output_factor)과
        #                              기지 재건 틱이 **공군 층 소관**이다. 공군이 없으면
        #                              표적을 때려도 결과에 반영될 통로가 없어 발동해도
        #                              관측 효과 0 — 죽은 기능이 된다.
        # 하나라도 빠지면 합동 화력을 생성하지 않는다(켜 놓고 아무 일도 안 하는 상태 금지).
        self.joint       = None
        self._joint_bases = None
        _joint_on = (bool(cfg.get('enable_joint_fires', False))
                     and bool(cfg.get('enable_strategic_strike', False))
                     and bool(cfg.get('enable_air_campaign', False)))
        if _joint_on:
            from engine_airforce import build_enemy_bases
            self._joint_bases = build_enemy_bases(self.cfg)
        self.air = None
        if bool(cfg.get('enable_air_campaign', False)):
            from engine_airforce import AirCampaign
            self.air = AirCampaign(self.cfg, bases=self._joint_bases,
                                   defer_strike=_joint_on)
        if _joint_on:
            from engine_joint import JointFires
            self.joint = JointFires(self.cfg, self._joint_bases)
        # v20.2b 지상 작전급 층 — enable_army_campaign ON일 때만 생성(OFF면 v19 bit-identical).
        # 연안 방공 포대가 ①대리모델 교전에 방공 가산 ②ASBM 구역은 전술 정밀 교전으로 강제하고
        # 4계층 요격 자산을 주입해 실측(v18.03 로직 재사용, 새 물리 없음).
        self.army = None
        if bool(cfg.get('enable_army_campaign', False)):
            from engine_army import ArmyCampaign
            self.army = ArmyCampaign(self.cfg, SLOC_ZONES)
        # A1: 정밀 교전 — ON이면 규모 큰 교전을 실제 전술 단발로 해결(OFF면 대리모델 = bit-identical).
        self.precise      = bool(cfg.get('enable_precise_engagement', False))
        self.precise_min  = int(cfg.get('campaign_precise_min_threats',
                                        _PRECISE_MIN_THREATS_DEFAULT))
        self.n_precise    = 0   # 정밀 해결된 교전 수(투명성·결과 집계)

    # ── 초기화 ────────────────────────────────────────────────────────────────
    def _build_force(self) -> list:
        """아군 함대 → CampaignShip 리스트. 교통로 3개에 순환 분산 초계."""
        custom = self.cfg.get('fleet_custom')
        if custom:
            ship_types = [s['type'] for s in custom]
        else:
            preset = FLEET_PRESETS.get(self.cfg.get('fleet_preset', '단독 작전'),
                                       FLEET_PRESETS.get('단독 작전', []))
            ship_types = fleet_ships_from_preset(preset)
        ships = []
        for i, st in enumerate(ship_types):
            if st not in SHIP_DB:
                continue
            zone = SLOC_ZONES[i % len(SLOC_ZONES)]   # 순환 분산
            ships.append(CampaignShip(st, zone))
        return ships

    def _build_enemy_waves(self) -> list:
        """적 전개 스케줄(MVP 고정). cfg enemy_schedule 있으면 사용, 없으면
        enemy_fleet_preset을 3 교통로에 시차 진입 웨이브로 생성."""
        sched = self.cfg.get('campaign_enemy_schedule')
        if sched:
            return [dict(w, alive=True) for w in sched]
        preset = self.cfg.get('enemy_fleet_preset', '')
        if preset not in ENEMY_FLEET_PRESETS:
            return []
        # 기본: 각 교통로에 전역 1/4·2/4·3/4 시점 진입(파상)
        waves = []
        for i, z in enumerate(SLOC_ZONES):
            arrive = int(self.horizon_h * (i + 1) / (len(SLOC_ZONES) + 1))
            waves.append({'preset': preset, 'zone': z, 'arrive_h': arrive, 'alive': True})
        return waves

    # ── 시간 루프 ─────────────────────────────────────────────────────────────
    def run(self) -> dict:
        for self.t_h in range(1, self.horizon_h + 1):
            self._tick_logistics()      # v18.2: 수리·재보급·이동 진행
            self._tick_fuel()           # v18.2: 초계 연료 소모 + 재보급 트리거
            self._tick_intel()          # v18.4: 적 위협 belief 갱신(탐지·감쇠)
            self._assign_missions()     # v18.3: belief 기반 동적 재배정(6h마다)
            # v20.4 도미노: 지상 → 공군 순으로 틱한다(순서가 곧 인과).
            #   지상은 **직전 틱 제공권**으로 적 SEAD 제압을 계산하고(1틱 지연 = 순환 차단),
            #   공군은 **그 결과 살아남은 연안 방공 기여**를 받아 제공권을 갱신한다.
            #   → 적 SEAD → 연안 SAM 제압 → 방공 기여 상실 → 제공권↓ → 해상 교통로 압박.
            if self.army is not None:   # v20.2b·v20.3·v20.4: 지상 층 틱 — 교전 前 갱신
                self.army.tick(
                    t_h=self.t_h,
                    control=self.control,
                    air_sups=(self.air.zone_superiority() if self.air is not None else None),
                    escorts=self._escort_counts(),
                )
            if self.air is not None:   # v19.1: 공군 제공권 격자 갱신
                # v19.2: 교전 前에 갱신 → 현재 틱 제공권이 같은 틱 교전에 연동(win_p·score 보정)
                # v19.5: 해군 지원요청(통제 붕괴 신호)을 함께 전달 → CAS 자동 요청·배정
                self.air.tick({z: self._zone_threat_truth(z) for z in SLOC_ZONES},
                              self._support_request(),
                              coastal_airdef=(self.army.air_defense()
                                              if self.army is not None else None))
            # v21.2 합동 화력 — 공군 틱 **뒤**에 둔다(순서가 곧 인과): 공군이 기지 재건을
            # 처리하고 소티를 배정한 뒤에야 그 폭격 화력을 거둬 해군·육군 화력과 합칠 수
            # 있다. 교전 前이라 이번 틱 기지 손상이 같은 틱 적 출항능력에 반영된다
            # (v19.2가 제공권을 교전 전에 갱신한 것과 같은 규약).
            if self.joint is not None:
                self.joint.tick(t_h=self.t_h, ships=self.ships,
                                air_effort=(self.air.strike_effort()
                                            if self.air is not None else 0.0),
                                army=self.army)
            self._tick_engagements()
            self._tick_sloc()
            # v18.5: 틱별 평균 통제도(0~1) 시계열(단일 실행 시각화용, v18.7)
            self._tl_control.append(round(sum(self.control.values()) / len(SLOC_ZONES), 3))
            self._tl_force.append(sum(1 for s in self.ships if s.available))
            if self._all_ships_down():
                break
        return self._compile()

    def _tick_logistics(self):
        """v18.2: 모항에서 수리(hp) / 재보급(탄약·연료) 진행. 완료 시 초계 복귀.
        v18.3: 이동(transit) 진행 + 복귀 zone을 최고위협 교통로로(결정론)."""
        for s in self.ships:
            if s.state == 'repair':
                s.repair_eta_h -= 1
                if s.repair_eta_h <= 0:
                    s.hp_frac = 1.0            # 수리 완료 = 완전 회복
                    s.state = 'patrol'
                    s.zone  = self._return_zone()   # v18.3: 최고위협 교통로 복귀
            elif s.state == 'resupply':
                s.resupply_eta_h -= 1
                if s.resupply_eta_h <= 0:
                    s.ammo_frac = 1.0
                    s.fuel_frac = 1.0
                    s.state = 'patrol'
                    s.zone  = self._return_zone()   # v18.3: 최고위협 교통로 복귀
            elif s.state == 'transit':
                s.transit_eta_h -= 1
                if s.transit_eta_h <= 0:
                    s.zone  = s.dest_zone           # v18.3: 이동 완료 → 초계 재개
                    s.state = 'patrol'

    def _tick_fuel(self):
        """v18.2: 초계 중 연료 소모. 탄약·연료가 임계 미만이면 모항 재보급 귀항.
        v18.5: 재보급 소요를 보급선 통제도로 스케일 — 함정은 가장 잘 통제되는 교통로로
        우회 보급(best_control)하므로 eta는 best_control에 반비례(통제 붕괴 시 최대 5배 지연).
        자기 교통로가 최선보다 통제 낮으면 우회 발생(n_reroute)."""
        best = max(self.control.values(), default=1.0)           # 최선 교통로 통제도(우회 보급선)
        delay_scale = 1.0 / max(best, _RESUPPLY_CONTROL_FLOOR)   # 통제 낮을수록 지연↑
        for s in self.ships:
            if s.state != 'patrol':
                continue
            s.fuel_frac = max(0.0, s.fuel_frac - _FUEL_PER_TICK)
            if s.ammo_frac < _AMMO_RESUPPLY_FRAC or s.fuel_frac < _FUEL_RESUPPLY_FRAC:
                patrol_zone = s.zone
                base = _RESUPPLY_AMMO_H if s.ammo_frac < _AMMO_RESUPPLY_FRAC \
                    else _RESUPPLY_FUEL_H
                s.resupply_eta_h = int(round(base * delay_scale))
                s.state = 'resupply'
                s.zone  = HOME_ZONE
                # v18.5: 자기 교통로가 최선 교통로보다 통제 낮으면 우회 보급으로 계측
                if patrol_zone in SLOC_ZONES and best - self.control[patrol_zone] > _REROUTE_EPS:
                    self._n_reroute += 1

    def _enemy_output_factor(self) -> float:
        """v19.4: 전략폭격 ON이면 적 출항능력 스칼라(<1, 기지 손상 누적 반영), 아니면 1.0.
        OFF(공군 없음·폭격 미사용)면 정확히 1.0 → 위협·교전 편성 불변(v19.3 bit-identical)."""
        if self.air is not None and self.air.strike_enabled:
            return self.air.enemy_output_factor()
        return 1.0

    def _active_enemy_in(self, zone: str) -> list:
        """해당 zone에 도달·생존한 적 웨이브의 편성 합(featurize용 [{preset,count}])."""
        fleet = []
        for w in self.waves:
            if w['alive'] and w['zone'] == zone and self.t_h >= w['arrive_h']:
                fleet.extend(ENEMY_FLEET_PRESETS.get(w['preset'], []))
        # v19.4: 전략폭격으로 적 출항능력↓ 시 출항 편성 비례 축소(교전 난이도↓). OFF면 불변.
        eo = self._enemy_output_factor()
        if eo < 1.0 and fleet:
            keep = max(1, int(np.ceil(len(fleet) * eo)))
            fleet = fleet[:keep]
        return fleet

    def _zone_threat_truth(self, zone: str) -> float:
        """zone 실제 위협도(truth) = 이미 도달한 웨이브 규모 + 임박(다음 재배정 주기 내
        도착) 규모×0.5. 교전·SLOC은 이 실측을 쓰고, 임무 배정은 belief를 쓴다(안개).
        v19.4: 전략폭격으로 적 출항능력↓ 시 위협도 비례 축소(→제공권↑·SLOC 압력↓). OFF면 불변."""
        now = soon = 0.0
        for w in self.waves:
            if not w['alive'] or w['zone'] != zone:
                continue
            size = len(ENEMY_FLEET_PRESETS.get(w['preset'], []))
            if self.t_h >= w['arrive_h']:
                now += size
            elif w['arrive_h'] - self.t_h <= _REASSIGN_PERIOD_H:
                soon += size * 0.5
        return (now + soon) * self._enemy_output_factor()

    def _zone_observed(self, zone: str) -> float:
        """지금 실제로 그 zone에 있는 적(도착분만). belief는 이 관측만 반영한다 —
        미래 도착 예측(soon)은 안개 세계에서 미리 알 수 없다(완전정보는 truth의 soon 사용)."""
        now = 0.0
        for w in self.waves:
            if w['alive'] and w['zone'] == zone and self.t_h >= w['arrive_h']:
                now += len(ENEMY_FLEET_PRESETS.get(w['preset'], []))
        return now

    def _support_request(self) -> dict:
        """v19.5: zone별 공군 지원 요청 우선도 = (1-통제도)×도달 적 규모. 통제가 붕괴 중이고
        적이 실제 도달한 zone일수록 높다. zone_threat(위협 규모)과 달리 control 항이 들어가
        차별화 — 위협이 커도 통제가 유지되면 요청이 낮아(공군 자원을 위기 zone에 집중)."""
        return {z: (1.0 - self.control[z]) * self._zone_observed(z) for z in SLOC_ZONES}

    def _tick_intel(self):
        """v18.4: 적 위협 belief 갱신. fog OFF면 belief=truth(완전정보, soon 예측 포함
        → v18.3 선제 배치 보존). fog ON: 관측(도착분)만 반영, 미탐지 zone은 반감기 12h로
        0(모름)으로 감쇠 → 적이 온 뒤에야 알고 대응(지연). 탐지원 3종 — 초계 함정 있는
        zone(관측)·초계기 ISR(가장 오래 못 본 zone 커버)·위성(주기 전역 저신뢰 부분 갱신).
        안개로 실제 적을 놓친 zone-틱을 계측(_n_missed)."""
        if not self.fog:
            self.belief = {z: self._zone_threat_truth(z) for z in SLOC_ZONES}  # 완전정보
            return
        obs = {z: self._zone_observed(z) for z in SLOC_ZONES}   # 관측 가능한 것=도착분만
        # 1) 탐지원: 초계 함정 있는 zone + 초계기 ISR가 커버하는 가장 오래된 zone
        seen = set(z for z in SLOC_ZONES
                   if any(s.available and s.zone == z for s in self.ships))
        if self.isr_aircraft > 0:
            order = sorted(SLOC_ZONES, key=lambda z: self._last_seen[z])
            seen.update(order[:self.isr_aircraft])
        # 2) 탐지 zone은 관측 반영·신선도 리셋
        for z in seen:
            self.belief[z] = obs[z]
            self._last_seen[z] = self.t_h
        # 3) 미탐지 zone: 정보 노후 → 반감기 12h로 0(모름)으로 감쇠
        decay = 0.5 ** (1.0 / _FOG_HALFLIFE_H)
        for z in SLOC_ZONES:
            if z not in seen:
                self.belief[z] *= decay
        # 4) 위성 주기 스캔: 미탐지 zone도 전역 저신뢰 부분 갱신(악순환 차단)
        if self.sat_interval_h > 0 and self.t_h % self.sat_interval_h == 0:
            for z in SLOC_ZONES:
                if z not in seen:
                    self.belief[z] += _SAT_TRUST * (obs[z] - self.belief[z])
        # 5) 안개 벌점 계측: 실제 적이 있는데 belief가 관측의 절반 미만이면 과소평가(무방비 위험)
        for z in SLOC_ZONES:
            if obs[z] > 0 and self.belief[z] < obs[z] * 0.5:
                self._n_missed += 1

    def _return_zone(self) -> str:
        """수리·재보급 완료 함정의 복귀 교통로 — belief 최고위협 zone(모르면 첫 교통로)."""
        if max(self.belief.values(), default=0.0) > 0:
            return max(SLOC_ZONES, key=lambda z: self.belief[z])
        return SLOC_ZONES[0]

    def _assign_missions(self):
        """v18.3: 6h마다 가용 초계 함정을 위협 기반으로 동적 재배정(그리디, 임무 2종).
        ▸방어집중: 강한 함정(max_channels)부터 '위협 대비 배치 부족'이 큰 고위협 교통로에
          위협도 비례로 배치. ▸초계: 위협 없는 교통로엔 약한 함정 1척씩 남겨 감시 유지
        (전원 집결 방지 → 동시 소진·조기 종료 완화). zone이 바뀌는 함정만 1틱 이동(transit)."""
        if (self.t_h - 1) % _REASSIGN_PERIOD_H != 0:
            return
        avail = [s for s in self.ships if s.state == 'patrol']
        if not avail:
            return
        threats = dict(self.belief)   # v18.4: 실측이 아닌 belief로 배정(안개)
        total   = sum(threats.values())
        n       = len(avail)
        avail.sort(key=lambda s: _ship_strength(s.ship_type), reverse=True)  # 강→약
        dests    = [None] * n
        assigned = {z: 0 for z in SLOC_ZONES}
        threat_zones = [z for z in SLOC_ZONES if threats[z] > 0]
        calm_zones   = [z for z in SLOC_ZONES if threats[z] <= 0]
        # 1) 방어 하한 — 위협 교통로당 강한 함정 1척씩 우선 확보(위협 큰 zone부터).
        #    함정이 희소하면 방어가 초계보다 우선(무방비 방치 방지).
        i = 0
        for z in sorted(threat_zones, key=lambda z: threats[z], reverse=True):
            if i >= n:
                break
            dests[i] = z
            assigned[z] += 1
            i += 1
        # 2) 초계 — 방어 하한을 채우고 남는 함정이 있을 때만 calm 교통로에 약한 함정 1척씩.
        wi = n - 1
        for z in calm_zones:
            if wi < i:      # 방어 하한(0..i-1)을 침범하면 잉여 없음 → 초계 생략
                break
            dests[wi] = z
            assigned[z] += 1
            wi -= 1
        # 3) 나머지 함정(강한 것부터) → 위협 비례 방어집중(위협 없으면 균등 분산)
        for k in range(n):
            if dests[k] is not None:
                continue
            if total > 0:
                dests[k] = max(threat_zones, key=lambda z: threats[z] / (assigned[z] + 1))
            else:
                dests[k] = min(SLOC_ZONES, key=lambda z: assigned[z])
            assigned[dests[k]] += 1
        # 4) 적용 — zone 변경분만 이동(transit)
        for s, dest in zip(avail, dests):
            if dest != s.zone:
                s.state         = 'transit'
                s.dest_zone     = dest
                s.transit_eta_h = _TRANSIT_H
                self._n_reassign += 1

    def _escort_counts(self) -> dict:
        """v20.3: 구역별 가용 호위 함정 수 — 상륙 단계의 함포 지원 강도."""
        out = {z: 0 for z in SLOC_ZONES}
        for s in self.ships:
            if s.available and s.zone in out:
                out[s.zone] += 1
        return out

    def _tick_engagements(self):
        # v19.2: 공군 층 ON이면 zone별 제공권을 1회 조회(교전 win_p·score 보정에 사용).
        # v19.5: CAS 피해경감(dmg 레버)도 조회 — 제공권(win_p 레버)과 직교.
        air_sups = self.air.zone_superiority() if self.air is not None else None
        cas_sup  = self.air.cas_support() if self.air is not None else None
        for zone in SLOC_ZONES:
            enemy_fleet = self._active_enemy_in(zone)
            if not enemy_fleet:
                continue
            patrol = [s for s in self.ships if s.available and s.zone == zone]
            if not patrol:
                continue   # 무방비 — SLOC 판정에서 차단 처리
            fleet_ships = [s.ship_type for s in patrol]
            # A1: 정밀 교전 — 규모 큰 교전은 실제 전술 단발로 해결(손실·요격·비용 진짜 계산).
            #   OFF거나 규모 미만이면 아래 대리모델 경로(기존과 완전 동일, rng 소비 불변).
            n_threats = sum(int(e.get('count', 1)) for e in enemy_fleet)
            # v20.2b: ASBM(대함 탄도) 구역 + 연안 포대 존재 → 규모와 무관하게 정밀 강제.
            #   대함탄도탄 요격은 확률 추상화로 뭉개지 않고 4계층 요격 로직으로 실측한다
            #   (사용자 결정: 정확도 우선). 포대가 없으면 정밀로 돌려도 함대 자체 방어뿐 →
            #   대리모델 유지(경제적). army OFF면 force_precise=False → 기존 경로 그대로.
            asbm_forced = (self.army is not None
                           and self.army.force_precise(zone, enemy_fleet))
            if asbm_forced:
                self.army.n_asbm_precise += 1
            if asbm_forced or (self.precise and n_threats >= self.precise_min):
                self._resolve_precise(zone, patrol, enemy_fleet, n_threats, air_sups, cas_sup)
                continue
            if self.model is None:
                # 모델 부재 폴백: 전력 수 기반 조악 근사(캠페인은 여전히 동작)
                win_p, score = 0.5, 0.5
                cost = 0.0
            else:
                win_p, score, cost = _predict_engagement(
                    self.model, fleet_ships, enemy_fleet, self.weather)
            # v19.2: 제공권 연동 — factor=0.6+0.8·제공권(각축 0.5=중립 1.0, 우세→유리·열세→불리).
            #   승률(win_p)과 임무점수(score) 둘 다 보정. rng.random() 소비는 불변이므로
            #   공군 OFF(air_sups=None)면 기존과 완전 동일. 사용자 합의 모델(2026-07-08).
            air_sup = None
            if air_sups is not None:
                air_sup = air_sups.get(zone, 0.5)
                factor = _AIR_ENGAGE_BASE + _AIR_ENGAGE_SLOPE * air_sup
                win_p = min(1.0, max(0.0, win_p * factor))
                score = min(1.0, max(0.0, score * factor))
            # v20.2b: 연안 방공 가산(대리모델 전용 — 정밀 경로는 실제 요격을 계산하므로 제외).
            #   ASBM 없는 통상 교전에서 포대가 함대 방공을 보강하는 효과. rng 소비 불변.
            army_bonus = 0.0
            if self.army is not None:
                army_bonus = self.army.zone_defense_bonus(zone)
                if army_bonus > 0:
                    win_p = min(1.0, win_p + army_bonus)
                    score = min(1.0, score + army_bonus)
                    # 가산을 준 만큼 요격탄도 쓴다(위협당 1발 근사) — 안 그러면 포대가 재고를
                    # 한 발도 안 쓰면서 전역 내내 최대 가산을 주는 비일관이 생긴다.
                    self.army.consume_surrogate(zone, n_threats)
            won = self.rng.random() < win_p
            # v19.5: CAS 근접 엄호 피해경감(relief=0이면 dmg 불변 = v19.4 bit-identical)
            cas_relief = cas_sup.get(zone, 0.0) if cas_sup is not None else 0.0
            self._apply_engagement(zone, patrol, enemy_fleet, won, score, cas_relief)
            self.cost_total += cost
            rec = {
                't_h': self.t_h, 'zone': zone, 'precise': False, 'win_p': round(win_p, 3),
                'won': won, 'score': round(score, 3),
                'n_friendly': len(patrol), 'n_enemy': len(enemy_fleet),
            }
            if air_sup is not None:
                rec['air_sup'] = round(air_sup, 3)   # 연동에 쓰인 제공권(투명성)
            if cas_relief > 0:
                rec['cas_relief'] = round(cas_relief, 3)   # v19.5 CAS 피해경감(투명성)
            if army_bonus > 0:
                rec['coastal_bonus'] = round(army_bonus, 3)   # v20.2b 연안 방공 가산(투명성)
            self.engagements.append(rec)

    def _apply_engagement(self, zone, patrol, enemy_fleet, won, score, cas_relief=0.0):
        """교전 결과 반영 — 승패·임무점수 기반 추상 피해(MVP). 손실 수 미추정이므로
        점수↓일수록 피해↑. v18.2: 교전당 탄약 소모 + 피해 심각도별 수리 기간 차등.
        v19.5: cas_relief만큼 피해 경감(근접 항공 지원). relief=0이면 dmg 불변(bit-identical)."""
        dmg = (1.0 - score) * (_DMG_WIN_K if won else _DMG_LOSS_K)
        dmg *= (1.0 - cas_relief)   # v19.5: CAS 근접 엄호 — 제공권(win_p)과 다른 레버(손실 경감)
        for s in patrol:
            s.ammo_frac = max(0.0, s.ammo_frac - _AMMO_PER_ENGAGEMENT)   # v18.2: 탄약 소모
            # 함정별 피해에 소량 확률 분산(결정론: rng 사용)
            s.hp_frac = max(0.0, s.hp_frac - dmg * (0.5 + self.rng.random()))
            self._retreat_if_damaged(s)
        if won:
            # 적 웨이브 격퇴(해당 zone 도달분 제거)
            for w in self.waves:
                if w['alive'] and w['zone'] == zone and self.t_h >= w['arrive_h']:
                    w['alive'] = False

    def _retreat_if_damaged(self, s):
        """hp가 귀항 임계 미만이면 모항 수리 전환 + 손상 심각도별 수리기간(1~14일) 산정.
        _apply_engagement(대리모델)·_resolve_precise(정밀) 공통. v18.2: 진입 hp(<0.4) 범위를
        손상도 0~1로 정규화 — 기존 (1-hp)는 진입 조건상 최소 8.8일로 쏠려 '경상 1일' 티어가
        도달 불가였고 72h 전역서 복귀 분기가 미발현했다(로직 감사 발견)."""
        if s.hp_frac < _HP_RETREAT_FRAC:
            s.state = 'repair'
            s.zone  = HOME_ZONE
            severity = min(1.0, max(0.0, (_HP_RETREAT_FRAC - s.hp_frac) / _HP_RETREAT_FRAC))
            days = _REPAIR_DAYS_MIN + severity * (_REPAIR_DAYS_MAX - _REPAIR_DAYS_MIN)
            s.repair_eta_h = int(round(days * 24))

    def _resolve_precise(self, zone, patrol, enemy_fleet, n_enemy, air_sups=None, cas_sup=None):
        """A1: zone 교전을 실제 전술 단발(run_v7_simulation)로 해결 — 손실·요격·비용 실측.
        전술 단발은 매번 full hp에서 시작하므로 그 교전의 실제 피해분(1-최종hp)을
        CampaignShip.hp_frac에서 차감(누적) → 대리모델의 '추상 피해'(score 기반)를 실제
        전술 결과로 대체. 승패는 요격률(방어 성공)로 판정해 웨이브 격퇴에 반영(→통제도).
        제공권(win_p) 보정은 정밀 경로에선 실제 교전이 대신하므로 생략, CAS 피해경감만 반영
        (air_campaign 기본 OFF). 부모 엔진 무수정 — run_v7_simulation은 호출만."""
        from engine_combat import run_v7_simulation, calculate_fleet_detect_ranges
        tcfg = dict(self.cfg)
        # 캠페인/전장/공군 라우팅 플래그 제거 → 순수 단발 교전으로 실행(라우터 오염 방지)
        for k in ('enable_campaign_mode', 'enable_air_campaign', 'enable_battle_mode',
                  'enable_campaign_fog', 'enable_precise_engagement'):
            tcfg.pop(k, None)
        # 아군: patrol 함정 → 임의 편성(name 유니크 '타입#i' — ship_subsystem_damage 키 충돌 방지)
        fc = [{'name': f'{s.ship_type}#{i}', 'type': s.ship_type}
              for i, s in enumerate(patrol)]
        tcfg['fleet_custom'] = fc
        tcfg['fleet_preset']     = '(직접 편성)'
        # 탐지거리: '(직접 편성)'은 FLEET_PRESETS에 없어 자동계산이 1km로 폴백(요격 불가) →
        # patrol 함정 센서 기준으로 직접 계산해 명시(detect_km_manual로 자동계산 우회).
        ranges = calculate_fleet_detect_ranges('', self.weather, fleet_list=fc)
        tcfg['detect_km']         = ranges['대공']
        tcfg['surface_detect_km'] = ranges['대함']
        tcfg['sub_detect_km']     = ranges['대잠']
        tcfg['detect_km_manual']  = True
        # 적: _active_enemy_in 반환 [{preset,count}]이 전술 fleet_cfg 원소와 형식 동일(무변환)
        tcfg['enemy_fleet_mode'] = 'custom'
        tcfg['enemy_fleet']      = [dict(e) for e in enemy_fleet]
        tcfg['weather']          = self.weather
        tcfg['mc_mode']          = True   # 로그·frames 억제
        # 결정론: 문자열 hash는 PYTHONHASHSEED로 세션마다 달라짐 → 정수 조합으로 고정
        zone_idx  = SLOC_ZONES.index(zone) if zone in SLOC_ZONES else 0
        base_seed = int(self.cfg.get('campaign_seed', self.cfg.get('sim_seed', 0)) or 0)
        tcfg['sim_seed'] = (base_seed * 100000 + self.t_h * 10 + zone_idx) & 0x7fffffff
        # v20.2b: 이 구역 연안 방공 포대의 4계층 자산을 어쇼어 자산으로 주입(잔여 재고 기준).
        #   → v18.03의 검증된 요격 로직이 ASBM·탄도를 실측한다(새 물리 없음).
        #   탄도 종말 강하도 함께 켠다 — 강하가 없으면 탄도가 중간단계 고도를 유지해
        #   종말 요격층(THAAD·L-SAM·천궁-II)이 교전창에 진입조차 못 한다(v18.03.02 규명).
        coastal = False
        if self.army is not None:
            coastal = self.army.inject_tactical(zone, tcfg)
            if coastal:
                tcfg['enable_ballistic_descent'] = True
        r = run_v7_simulation(tcfg)
        self.n_precise += 1
        if coastal:
            self.army.consume(zone, r)   # 실측 발사분만큼 포대 재고 차감(틱 간 유지)

        ssd = r.get('ship_subsystem_damage', {})
        cas_relief = cas_sup.get(zone, 0.0) if cas_sup is not None else 0.0
        for i, s in enumerate(patrol):
            info = ssd.get(f'{s.ship_type}#{i}')
            if info and info.get('max_hp'):
                hp_frac = max(0.0, min(1.0, info['hp'] / info['max_hp']))
                dmg = (1.0 - hp_frac) * (1.0 - cas_relief)   # 이번 교전 실제 피해분(CAS 경감)
                s.hp_frac = max(0.0, s.hp_frac - dmg)
            s.ammo_frac = max(0.0, s.ammo_frac - _AMMO_PER_ENGAGEMENT)
            self._retreat_if_damaged(s)
        self.cost_total += float(r.get('total_cost', 0.0))

        ir     = float(r.get('intercept_rate', 0.0))
        n_lost = int(r.get('friendly_ships_lost', 0))   # 유인함 손실만(무인정은 unmanned_lost)
        # 아군 미전멸 = 유인 전투함이 남아있음. len(patrol)엔 무인함이 섞일 수 있어 유인 수로 비교.
        n_manned = sum(1 for s in patrol
                       if not SHIP_DB.get(s.ship_type, {}).get('is_unmanned', False))
        won = (ir >= 0.5) and (n_lost < max(1, n_manned))   # 방어 성공(요격률) + 유인 미전멸
        if won:
            for w in self.waves:
                if w['alive'] and w['zone'] == zone and self.t_h >= w['arrive_h']:
                    w['alive'] = False
        rec = {
            't_h': self.t_h, 'zone': zone, 'precise': True, 'won': won,
            'intercept_rate': round(ir, 3),
            'n_friendly': len(patrol),
            'n_enemy': n_enemy,
            'friendly_lost': n_lost,
            'enemy_killed': int(r.get('enemy_ships_destroyed', 0)),
            'cost': round(float(r.get('total_cost', 0.0)), 1),
        }
        if air_sups is not None:
            rec['air_sup'] = round(air_sups.get(zone, 0.5), 3)   # 투명성(정밀은 win_p 미보정)
        if cas_relief > 0:
            rec['cas_relief'] = round(cas_relief, 3)
        if coastal:
            # v20.2b: 연안 포대가 실제로 쏜 계층별 요격탄(투명성 — 5계층 발현 확인용)
            rec['coastal'] = {
                'sm3':   int(r.get('ashore_sm3_fired', 0) or 0),
                'thaad': int(r.get('thaad_fired', 0) or 0),
                'lsam':  int(r.get('lsam_fired', 0) or 0),
                'patriot': int(r.get('patriot_fired', 0) or 0),   # v20.1 PAC-3 MSE(중층)
                'chungung': int(r.get('chungung_fired', 0) or 0),
            }
        self.engagements.append(rec)

    def _tick_sloc(self):
        """v18.5: 교통로별 연속 통제도(0~1) 갱신. target=아군전력/(아군+적전력),
        α=0.30 관성으로 서서히 수렴 → 적 우세가 지속돼야 통제 붕괴(한 틱에 안 무너짐).
        아군전력=초계 함정 방공 강도 합, 적전력=_zone_threat_truth(truth 기준).
        위협 없으면 target=1.0(회복). SLOC 판정은 truth로, 안개(belief)는 배정만(독립)."""
        for zone in SLOC_ZONES:
            friendly = sum(_ship_strength(s.ship_type)
                           for s in self.ships if s.available and s.zone == zone)
            enemy = self._zone_threat_truth(zone)
            if friendly + enemy <= 0:
                target = 1.0                       # 위협·아군 모두 없음 → 통제 회복
            else:
                target = friendly / (friendly + enemy)
            c = self.control[zone] + _CONTROL_ALPHA * (target - self.control[zone])
            self.control[zone] = min(1.0, max(0.0, c))

    def _all_ships_down(self) -> bool:
        """전력 소진 판정 — v18.5 정교화. 초계·이동 중(곧 가용)이 하나라도 있으면 유지.
        전원이 수리·재보급 중이어도 '남은 horizon 내 복귀 가능'하면 아직 소진 아님
        (일시 재보급은 복귀하므로 조기종료하면 통제→보급 피드백 루프가 죽는다).
        전원이 남은 시간 내 복귀 불가할 때만 진짜 전력 소진."""
        if not self.ships:
            return True
        if any(s.state in ('patrol', 'transit') for s in self.ships):
            return False
        remaining = self.horizon_h - self.t_h
        for s in self.ships:
            eta = s.repair_eta_h if s.state == 'repair' else \
                  s.resupply_eta_h if s.state == 'resupply' else 0
            if eta <= remaining:
                return False        # 이 함정은 horizon 내 복귀 → 계속 진행
        return True

    # ── 결과 ──────────────────────────────────────────────────────────────────
    def _compile(self) -> dict:
        surviving = sum(1 for s in self.ships if s.hp_frac > 0)
        # v18.5: 평균 연속 통제도로 승패 — ≥0.70 win / ≥0.30 draw / else loss.
        # 조기 종료여도 avg 기반(§6-C ④). 단 실제 전멸(생존 0)은 통제도 무관 loss 강제.
        mean_control = sum(self.control.values()) / len(SLOC_ZONES)
        # v20.3: 상륙 임무가 걸려 있으면 전역 목표가 '교통로 통제'만이 아니다 —
        # 교두보 확보를 승패 점수에 가중 결합한다(가중치·부분점수 규칙은 engine_army 소관).
        # 상륙 임무가 없으면 교통로 통제 그대로 → 기존 판정 bit-identical.
        score_for_outcome = (self.army.outcome_blend(mean_control)
                             if self.army is not None else mean_control)
        if surviving == 0:
            outcome = 'loss'
        elif score_for_outcome >= _CONTROL_WIN_THRESH:
            outcome = 'win'
        elif score_for_outcome >= _CONTROL_DRAW_THRESH:
            outcome = 'draw'
        else:
            outcome = 'loss'
        avail     = sum(1 for s in self.ships if s.available)
        n_repair   = sum(1 for s in self.ships if s.state == 'repair')
        n_resupply = sum(1 for s in self.ships if s.state == 'resupply')
        n_transit  = sum(1 for s in self.ships if s.state == 'transit')
        nships = len(self.ships) or 1
        result = {
            'mode':            'campaign',
            'model_loaded':    self.model is not None,   # False면 교전이 근사 폴백(승률 0.5)
            'outcome':         outcome,
            'control':         {z: round(v, 3) for z, v in self.control.items()},  # v18.5 교통로별 통제도(0~1)
            'mean_control':    round(mean_control, 3),   # v18.5 평균 통제도(승패 기준)
            'n_reroute':       self._n_reroute,          # v18.5 누적 우회 보급 횟수
            'n_sloc':          len(SLOC_ZONES),
            'horizon_h':       self.horizon_h,
            'end_h':           self.t_h,
            'n_ships':         len(self.ships),
            'surviving_ships': surviving,
            'available_ships': avail,
            'n_repair':        n_repair,       # v18.2: 수리 중 함정 수
            'n_resupply':      n_resupply,     # v18.2: 재보급 중 함정 수
            'n_transit':       n_transit,      # v18.3: 이동(재배정) 중 함정 수
            'n_reassign':      self._n_reassign,  # v18.3: 누적 재배정 이동 횟수
            'fog_enabled':     self.fog,       # v18.4: 전장의 안개 적용 여부
            'n_missed':        self._n_missed,  # v18.4: 안개로 실제 적 놓친 zone-틱 수
            'mean_ammo':       round(sum(s.ammo_frac for s in self.ships) / nships, 3),
            'mean_fuel':       round(sum(s.fuel_frac for s in self.ships) / nships, 3),
            'n_engagements':   len(self.engagements),
            'n_precise':       self.n_precise,   # A1: 실제 전술 단발로 해결된 교전 수(0=전부 대리모델)
            'engagements':     self.engagements,
            'cost_total':      round(self.cost_total, 1),
            'timeline':        {'control': self._tl_control, 'force': self._tl_force},
        }
        if self.air is not None:   # v19.1: 공군 지표 병합(제공권·소티)
            result.update(self.air.summary())
        if self.army is not None:  # v20.2b: 지상 지표 병합(연안 포대 재고·ASBM 정밀·요격탄)
            result.update(self.army.status())
        if self.joint is not None:  # v21.2: 합동 화력 지표 병합(군별 기여·협조 실적)
            result.update(self.joint.summary())
        return result


def run_campaign(cfg: dict, step_cb=None, model=None) -> dict:
    """작전급 캠페인 1회 실행. 전술 엔진 무수정 — 즉시예측 해결기 호출.
    model 미지정 시 forecast_model.pkl 로드(부재면 조악 폴백으로도 동작)."""
    if model is None:
        model = load_forecast_model()
    eng = CampaignEngine(cfg, model=model)
    result = eng.run()
    if step_cb:
        # step_cb 시그니처: (t, t_max, alive, vls, last_log:str) — 5번째는 문자열이어야 함
        step_cb(float(eng.t_h), float(eng.horizon_h),
                int(result.get('surviving_ships', 0)), 0,
                f"캠페인 종료 ({eng.t_h}h)")
    return result


# E1: 캠페인 MC 병렬화 임계 — 정밀 여부로 차등.
#   정밀 ON은 개별 캠페인이 수백ms~수초(전술 단발 반복)라 n≥8부터 병렬 이득이 크다.
#   정밀 OFF(대리모델)는 개별 ~85ms로 빨라, Windows spawn+pkl 3.1MB 워커 로드 오버헤드가
#   커서 n≥64는 돼야 병렬이 순차를 앞선다(실측: 정밀OFF n=20은 순차1.7s<병렬4.5s).
_MC_PARALLEL_MIN_PRECISE = 8    # 정밀 ON 병렬 임계
_MC_PARALLEL_MIN_PROXY   = 64   # 대리모델 병렬 임계
# 병렬 집계에 쓰는 축소 키(워커→메인 직렬화 최소화 — engagements 리스트 등 대형 필드 제외)
_MC_ACC_KEYS = ('mean_control', 'surviving_ships', 'n_engagements', 'cost_total',
                'n_reassign', 'n_reroute', 'n_missed', 'end_h', 'n_precise',
                # v20.2b: 연안 방공 — 없으면 반복 분석에서 이 지표가 통째로 소실된다
                'n_asbm_precise', 'coastal_intercepts',
                # v20.3: 상륙작전 — 교두보 확보율·평균 진척
                'amphib_success', 'amphib_progress',
                # v20.4: 도미노 — 연안 방공망 평균 제압도 + 제공권(연쇄 2단계 관측)
                'coastal_suppression', 'mean_air_superiority',
                # v21.2: 합동 화력 — 적 기지 손상·출항능력이 이 층의 최종 산출이고,
                # 발사수·협조 실적이 발현 증거다. ⚠ 스칼라만 넣는다 —
                # joint_dmg_by_service·joint_dmg_share(dict)·joint_fire_log(list)는
                # 아래 acc[k] += float(...)에서 TypeError가 난다.
                'enemy_base_damage', 'enemy_output_factor',
                'joint_navy_fired', 'joint_army_fired', 'joint_air_effort',
                'joint_deconflict', 'joint_overkill_skip')

# ProcessPoolExecutor 워커 전역 — initializer로 모델 1회 로드(태스크마다 pkl 재직렬화 방지)
_MC_WORKER_MODEL = None


def _campaign_mc_init(expect_model=True):
    """병렬 MC 워커 초기화 — forecast_model.pkl을 프로세스당 1회 로드.
    expect_model=True(메인 프로세스가 모델 로드 성공)인데 워커가 로드 실패하면 시끄럽게 중단:
    조용한 win_p=0.5 폴백으로 수백~천 회 MC가 '거짓 분포'를 내는 것보다, 환경 이상(예: exe
    워커의 _MEIPASS 경로 문제)을 즉시 드러내는 게 안전(신뢰성 우선). 메인도 모델이 없으면
    (expect_model=False) 순차 경로와 일관되게 graceful 폴백 — result['model_loaded']=False로 이미 가시화."""
    global _MC_WORKER_MODEL
    _MC_WORKER_MODEL = load_forecast_model()
    if expect_model and _MC_WORKER_MODEL is None:
        raise RuntimeError("병렬 캠페인 MC 워커가 forecast_model 로드 실패 — "
                           "조용한 win_p=0.5 폴백 방지 위해 중단(메인은 로드 성공)")


def _campaign_mc_worker(args: tuple) -> dict:
    """병렬 MC 워커 — seed 1개 캠페인 실행 후 집계에 필요한 축소 dict만 반환(직렬화 경량화).
    PyQt6 비의존 순수 함수(전술 _mc_batch_worker 선례)."""
    cfg, seed = args
    r = run_campaign(dict(cfg, campaign_seed=seed), model=_MC_WORKER_MODEL)
    out = {k: r.get(k, 0) for k in _MC_ACC_KEYS}
    out['outcome'] = r.get('outcome', 'loss')
    return out


def monte_carlo_campaign(cfg: dict, n: int, model=None, progress_cb=None) -> dict:
    """v18.6: 작전급 캠페인 N회 반복(seed 0…N-1 스윕) → outcome 분포·통제도·비용 통계.
    개별 교전이 즉시예측(~ms)이라 수백~천 회도 수초~수분. 모델을 1회 로드해 공유하고
    (3.1MB pkl 반복 로드 방지) run_campaign을 시드만 바꿔 호출한다. 전술 MC(monte_carlo_v7
    ·_mc_batch_worker·monte_carlo_lhs)와 완전 별개 — 캠페인 전용 집계."""
    if model is None:
        model = load_forecast_model()   # 판정·순차용. 병렬 워커는 initializer로 자체 재로드.
    n = max(1, int(n))
    outcomes = {'win': 0, 'draw': 0, 'loss': 0}
    acc = {k: 0.0 for k in _MC_ACC_KEYS}
    ctrl_list = []

    def _accumulate(r):
        outcomes[r['outcome']] = outcomes.get(r['outcome'], 0) + 1
        for k in _MC_ACC_KEYS:
            acc[k] += float(r.get(k, 0) or 0)
        ctrl_list.append(float(r.get('mean_control', 0.0)))

    # E1: n이 크면 멀티프로세스 병렬(seed 독립 → 순차와 집계 동일, 정밀 교전 ON 시 큰 이득).
    #     작으면 순차(spawn 오버헤드 회피). progress_cb는 완료 순서로 보고(무순 집계라 무방).
    parallel_min = (_MC_PARALLEL_MIN_PRECISE
                    if cfg.get('enable_precise_engagement', False)
                    else _MC_PARALLEL_MIN_PROXY)
    if n >= parallel_min:
        import os
        from concurrent.futures import ProcessPoolExecutor, as_completed
        n_workers = min(os.cpu_count() or 4, 8)
        done = 0
        # 메인이 모델 로드에 성공했으면 워커도 성공해야 정상 — 워커만 실패하면 시끄럽게 중단
        # (조용한 win_p=0.5 폴백으로 거짓 분포 방지). 메인도 없으면 graceful(순차와 일관).
        expect_model = model is not None
        with ProcessPoolExecutor(max_workers=n_workers,
                                 initializer=_campaign_mc_init,
                                 initargs=(expect_model,)) as pool:
            futs = [pool.submit(_campaign_mc_worker, (cfg, i)) for i in range(n)]
            try:
                for fut in as_completed(futs):
                    _accumulate(fut.result())
                    done += 1
                    if progress_cb and (done % 10 == 0 or done == n):
                        progress_cb(done, n)   # 중단 요청 시 여기서 예외(_SimCancelled 등)
            except BaseException:
                # 중단(abort)·오류로 루프를 빠져나갈 때 대기열 작업을 즉시 취소한다.
                # 기본 __exit__의 shutdown(wait=True)는 제출된 전체 완료까지 대기 → 정밀 ON
                # 대량 반복이면 중단이 수 분간 안 먹힌다. 실행 중 워커만 마무리하고 대기열은
                # 버려 중단을 반응성 있게(신뢰성·UX).
                pool.shutdown(wait=False, cancel_futures=True)
                raise
    else:
        for i in range(n):
            _accumulate(run_campaign(dict(cfg, campaign_seed=i), model=model))
            if progress_cb and (i % 10 == 0 or i == n - 1):
                progress_cb(i + 1, n)
    inv = 1.0 / n
    mean_ctrl = acc['mean_control'] * inv
    var = sum((c - mean_ctrl) ** 2 for c in ctrl_list) * inv
    return {
        'mode':            'campaign_mc',
        'model_loaded':    model is not None,
        'n_runs':          n,
        'outcomes':        outcomes,
        'win_rate':        round(outcomes['win'] * inv, 3),
        'draw_rate':       round(outcomes['draw'] * inv, 3),
        'loss_rate':       round(outcomes['loss'] * inv, 3),
        'mean_control_avg': round(mean_ctrl, 3),
        'mean_control_std': round(var ** 0.5, 3),
        'mean_control_min': round(min(ctrl_list), 3),
        'mean_control_max': round(max(ctrl_list), 3),
        'surviving_avg':   round(acc['surviving_ships'] * inv, 2),
        'n_engagements_avg': round(acc['n_engagements'] * inv, 1),
        'cost_avg':        round(acc['cost_total'] * inv, 1),
        'n_reassign_avg':  round(acc['n_reassign'] * inv, 2),
        'n_reroute_avg':   round(acc['n_reroute'] * inv, 2),
        'n_missed_avg':    round(acc['n_missed'] * inv, 2),
        'end_h_avg':       round(acc['end_h'] * inv, 1),
        'n_precise_avg':   round(acc['n_precise'] * inv, 2),   # E1/A1: 평균 정밀 교전 수
        # v20.2b: 연안 방공 — ASBM 때문에 정밀로 강제된 교전 수·포대가 쏜 요격탄(평균)
        'n_asbm_precise_avg':      round(acc['n_asbm_precise'] * inv, 2),
        'coastal_intercepts_avg':  round(acc['coastal_intercepts'] * inv, 1),
        # v20.3: 상륙 — 교두보 확보율(성공 비율)·평균 진척
        'amphib_success_rate':     round(acc['amphib_success'] * inv, 3),
        'amphib_progress_avg':     round(acc['amphib_progress'] * inv, 3),
        # v20.4: 도미노 — 연안 방공망 평균 제압도(적 SEAD 진행 정도) + 제공권(연쇄 2단계)
        'coastal_suppression_avg': round(acc['coastal_suppression'] * inv, 3),
        'air_superiority_avg':     round(acc['mean_air_superiority'] * inv, 3),
        # v21.2: 합동 화력 — 적 기지 손상·적 출항능력이 이 층의 최종 산출이고, 발사수·
        # 협조 실적이 발현 증거다. _MC_ACC_KEYS에 넣는 것만으론 누적만 되고 **결과에
        # 안 나온다** — 여기 노출까지 해야 반복 분석에서 보인다(집계와 노출은 별개).
        'enemy_base_damage_avg':   round(acc['enemy_base_damage'] * inv, 3),
        'enemy_output_factor_avg': round(acc['enemy_output_factor'] * inv, 3),
        'joint_navy_fired_avg':    round(acc['joint_navy_fired'] * inv, 1),
        'joint_army_fired_avg':    round(acc['joint_army_fired'] * inv, 1),
        'joint_air_effort_avg':    round(acc['joint_air_effort'] * inv, 2),
        'joint_deconflict_avg':    round(acc['joint_deconflict'] * inv, 2),
        'joint_overkill_skip_avg': round(acc['joint_overkill_skip'] * inv, 2),
        'horizon_h':       int(cfg.get('campaign_horizon_h', CAMPAIGN_HORIZON_H_DEFAULT)),
        'fog_enabled':     bool(cfg.get('enable_campaign_fog', False)),
        'parallel':        bool(n >= parallel_min),            # E1: 병렬 실행 여부(투명성)
    }
