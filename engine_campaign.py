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
                 'dest_zone', 'transit_eta_h')

    def __init__(self, ship_type: str, zone: str):
        self.ship_type      = ship_type
        self.zone           = zone
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
        # v19.1 공군 작전급 층 — enable_air_campaign ON일 때만 생성(OFF면 v18 bit-identical).
        # v19.1은 제공권을 산출만 하고 해군 교전엔 무영향(연동은 v19.2).
        self.air = None
        if bool(cfg.get('enable_air_campaign', False)):
            from engine_airforce import AirCampaign
            self.air = AirCampaign(self.cfg)

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
            self._tick_engagements()
            self._tick_sloc()
            if self.air is not None:   # v19.1: 공군 제공권 격자 갱신(해군 outcome 무영향)
                self.air.tick({z: self._zone_threat_truth(z) for z in SLOC_ZONES})
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

    def _active_enemy_in(self, zone: str) -> list:
        """해당 zone에 도달·생존한 적 웨이브의 편성 합(featurize용 [{preset,count}])."""
        fleet = []
        for w in self.waves:
            if w['alive'] and w['zone'] == zone and self.t_h >= w['arrive_h']:
                fleet.extend(ENEMY_FLEET_PRESETS.get(w['preset'], []))
        return fleet

    def _zone_threat_truth(self, zone: str) -> float:
        """zone 실제 위협도(truth) = 이미 도달한 웨이브 규모 + 임박(다음 재배정 주기 내
        도착) 규모×0.5. 교전·SLOC은 이 실측을 쓰고, 임무 배정은 belief를 쓴다(안개)."""
        now = soon = 0.0
        for w in self.waves:
            if not w['alive'] or w['zone'] != zone:
                continue
            size = len(ENEMY_FLEET_PRESETS.get(w['preset'], []))
            if self.t_h >= w['arrive_h']:
                now += size
            elif w['arrive_h'] - self.t_h <= _REASSIGN_PERIOD_H:
                soon += size * 0.5
        return now + soon

    def _zone_observed(self, zone: str) -> float:
        """지금 실제로 그 zone에 있는 적(도착분만). belief는 이 관측만 반영한다 —
        미래 도착 예측(soon)은 안개 세계에서 미리 알 수 없다(완전정보는 truth의 soon 사용)."""
        now = 0.0
        for w in self.waves:
            if w['alive'] and w['zone'] == zone and self.t_h >= w['arrive_h']:
                now += len(ENEMY_FLEET_PRESETS.get(w['preset'], []))
        return now

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

    def _tick_engagements(self):
        for zone in SLOC_ZONES:
            enemy_fleet = self._active_enemy_in(zone)
            if not enemy_fleet:
                continue
            patrol = [s for s in self.ships if s.available and s.zone == zone]
            if not patrol:
                continue   # 무방비 — SLOC 판정에서 차단 처리
            fleet_ships = [s.ship_type for s in patrol]
            if self.model is None:
                # 모델 부재 폴백: 전력 수 기반 조악 근사(캠페인은 여전히 동작)
                win_p, score = 0.5, 0.5
                cost = 0.0
            else:
                win_p, score, cost = _predict_engagement(
                    self.model, fleet_ships, enemy_fleet, self.weather)
            won = self.rng.random() < win_p
            self._apply_engagement(zone, patrol, enemy_fleet, won, score)
            self.cost_total += cost
            self.engagements.append({
                't_h': self.t_h, 'zone': zone, 'win_p': round(win_p, 3),
                'won': won, 'score': round(score, 3),
                'n_friendly': len(patrol), 'n_enemy': len(enemy_fleet),
            })

    def _apply_engagement(self, zone, patrol, enemy_fleet, won, score):
        """교전 결과 반영 — 승패·임무점수 기반 추상 피해(MVP). 손실 수 미추정이므로
        점수↓일수록 피해↑. v18.2: 교전당 탄약 소모 + 피해 심각도별 수리 기간 차등."""
        dmg = (1.0 - score) * (_DMG_WIN_K if won else _DMG_LOSS_K)
        for s in patrol:
            s.ammo_frac = max(0.0, s.ammo_frac - _AMMO_PER_ENGAGEMENT)   # v18.2: 탄약 소모
            # 함정별 피해에 소량 확률 분산(결정론: rng 사용)
            s.hp_frac = max(0.0, s.hp_frac - dmg * (0.5 + self.rng.random()))
            if s.hp_frac < _HP_RETREAT_FRAC:
                s.state = 'repair'
                s.zone  = HOME_ZONE
                # v18.2: 피해 심각도별 수리 기간 1~14일 (hp 낮을수록 길게)
                days = _REPAIR_DAYS_MIN + (1.0 - s.hp_frac) * (_REPAIR_DAYS_MAX - _REPAIR_DAYS_MIN)
                s.repair_eta_h = int(round(days * 24))
        if won:
            # 적 웨이브 격퇴(해당 zone 도달분 제거)
            for w in self.waves:
                if w['alive'] and w['zone'] == zone and self.t_h >= w['arrive_h']:
                    w['alive'] = False

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
        if surviving == 0:
            outcome = 'loss'
        elif mean_control >= _CONTROL_WIN_THRESH:
            outcome = 'win'
        elif mean_control >= _CONTROL_DRAW_THRESH:
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
            'engagements':     self.engagements,
            'cost_total':      round(self.cost_total, 1),
            'timeline':        {'control': self._tl_control, 'force': self._tl_force},
        }
        if self.air is not None:   # v19.1: 공군 지표 병합(제공권·소티)
            result.update(self.air.summary())
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


def monte_carlo_campaign(cfg: dict, n: int, model=None, progress_cb=None) -> dict:
    """v18.6: 작전급 캠페인 N회 반복(seed 0…N-1 스윕) → outcome 분포·통제도·비용 통계.
    개별 교전이 즉시예측(~ms)이라 수백~천 회도 수초~수분. 모델을 1회 로드해 공유하고
    (3.1MB pkl 반복 로드 방지) run_campaign을 시드만 바꿔 호출한다. 전술 MC(monte_carlo_v7
    ·_mc_batch_worker·monte_carlo_lhs)와 완전 별개 — 캠페인 전용 집계."""
    if model is None:
        model = load_forecast_model()
    n = max(1, int(n))
    outcomes = {'win': 0, 'draw': 0, 'loss': 0}
    _acc_keys = ('mean_control', 'surviving_ships', 'n_engagements', 'cost_total',
                 'n_reassign', 'n_reroute', 'n_missed', 'end_h')
    acc = {k: 0.0 for k in _acc_keys}
    ctrl_list = []
    for i in range(n):
        r = run_campaign(dict(cfg, campaign_seed=i), model=model)
        outcomes[r['outcome']] = outcomes.get(r['outcome'], 0) + 1
        for k in _acc_keys:
            acc[k] += float(r.get(k, 0) or 0)
        ctrl_list.append(float(r.get('mean_control', 0.0)))
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
        'horizon_h':       int(cfg.get('campaign_horizon_h', CAMPAIGN_HORIZON_H_DEFAULT)),
        'fog_enabled':     bool(cfg.get('enable_campaign_fog', False)),
    }
