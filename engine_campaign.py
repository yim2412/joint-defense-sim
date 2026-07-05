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
_REPAIR_H_FULL    = 24                              # hp 0→1 완전 수리 소요(시간, MVP 고정 근사)
_HP_RETREAT_FRAC  = 0.4                             # 이 아래로 손상되면 귀항→수리
_DMG_WIN_K        = 0.30                            # 승리 시 아군 피해 계수 (× (1-score))
_DMG_LOSS_K       = 0.60                            # 패배 시 아군 피해 계수


def load_forecast_model(path: str = 'forecast_model.pkl'):
    """즉시예측 대리모델 로드. 부재/의존성 없으면 None(호출측이 처리)."""
    try:
        import joblib
        return joblib.load(path)
    except Exception:
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
    """캠페인 함정 상태 — 전술 FriendlyShipObj의 작전급 추상(물리 필드 아님)."""
    __slots__ = ('ship_type', 'zone', 'state', 'hp_frac', 'repair_eta_h')

    def __init__(self, ship_type: str, zone: str):
        self.ship_type    = ship_type
        self.zone         = zone
        self.state        = 'patrol'   # patrol / transit / repair
        self.hp_frac      = 1.0
        self.repair_eta_h = 0

    @property
    def available(self) -> bool:
        return self.state == 'patrol'


class CampaignEngine:
    """작전급 캠페인 1회 실행. 전술 엔진을 교전 해결기로 호출(즉시예측 우선)."""

    def __init__(self, cfg: dict, model=None):
        self.cfg      = dict(cfg)            # 오염 방지(전술 엔진 규약과 동일)
        self.model    = model
        self.weather  = cfg.get('weather', '맑음 (주간)')
        self.horizon_h = int(cfg.get('campaign_horizon_h', CAMPAIGN_HORIZON_H_DEFAULT))
        seed = cfg.get('campaign_seed', cfg.get('sim_seed'))
        self.rng = random.Random(seed)

        self.ships   = self._build_force()
        self.waves   = self._build_enemy_waves()   # [{preset, zone, arrive_h, alive}]
        self.sloc    = {z: True for z in SLOC_ZONES}  # True=통제 유지
        self.t_h     = 0
        self.engagements = []                      # 교전 기록
        self.cost_total  = 0.0
        # 시계열(단일 실행용)
        self._tl_control = []   # 틱별 통제 교통로 수
        self._tl_force   = []   # 틱별 가용 전력 함정 수

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
            self._tick_repairs()
            self._tick_engagements()
            self._tick_sloc()
            self._tl_control.append(sum(self.sloc.values()))
            self._tl_force.append(sum(1 for s in self.ships if s.available))
            if self._all_ships_down():
                break
        return self._compile()

    def _tick_repairs(self):
        for s in self.ships:
            if s.state == 'repair':
                s.repair_eta_h -= 1
                s.hp_frac = min(1.0, s.hp_frac + 1.0 / _REPAIR_H_FULL)
                if s.repair_eta_h <= 0:
                    s.hp_frac = 1.0
                    s.state = 'patrol'
                    s.zone  = SLOC_ZONES[self.rng.randrange(len(SLOC_ZONES))]

    def _active_enemy_in(self, zone: str) -> list:
        """해당 zone에 도달·생존한 적 웨이브의 편성 합(featurize용 [{preset,count}])."""
        fleet = []
        for w in self.waves:
            if w['alive'] and w['zone'] == zone and self.t_h >= w['arrive_h']:
                fleet.extend(ENEMY_FLEET_PRESETS.get(w['preset'], []))
        return fleet

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
        점수↓일수록 피해↑. hp 임계 미만 함정은 귀항→수리."""
        dmg = (1.0 - score) * (_DMG_WIN_K if won else _DMG_LOSS_K)
        for s in patrol:
            # 함정별 피해에 소량 확률 분산(결정론: rng 사용)
            s.hp_frac = max(0.0, s.hp_frac - dmg * (0.5 + self.rng.random()))
            if s.hp_frac < _HP_RETREAT_FRAC:
                s.state = 'repair'
                s.zone  = HOME_ZONE
                s.repair_eta_h = int(_REPAIR_H_FULL * (1.0 - s.hp_frac)) + 1
        if won:
            # 적 웨이브 격퇴(해당 zone 도달분 제거)
            for w in self.waves:
                if w['alive'] and w['zone'] == zone and self.t_h >= w['arrive_h']:
                    w['alive'] = False

    def _tick_sloc(self):
        """교통로 통제 갱신 — 적 존재 + 아군 초계 부재면 차단, 아군 초계 있으면 유지."""
        for zone in SLOC_ZONES:
            enemy = self._active_enemy_in(zone)
            patrol = any(s.available and s.zone == zone for s in self.ships)
            if enemy and not patrol:
                self.sloc[zone] = False
            elif not enemy:
                self.sloc[zone] = True   # 위협 소멸 시 통제 회복

    def _all_ships_down(self) -> bool:
        return all(s.state == 'repair' for s in self.ships) if self.ships else True

    # ── 결과 ──────────────────────────────────────────────────────────────────
    def _compile(self) -> dict:
        controlled = sum(self.sloc.values())
        n = len(SLOC_ZONES)
        if controlled >= n - 0:      # 전 교통로 유지
            outcome = 'win'
        elif controlled >= 1:
            outcome = 'draw'
        else:
            outcome = 'loss'
        # 조기 전멸(전 함정 수리불능 상태로 종료) → loss 우선
        if self._all_ships_down() and self.t_h < self.horizon_h:
            outcome = 'loss'
        surviving = sum(1 for s in self.ships if s.hp_frac > 0)
        avail     = sum(1 for s in self.ships if s.available)
        return {
            'mode':            'campaign',
            'outcome':         outcome,
            'sloc_control':    dict(self.sloc),
            'n_controlled':    controlled,
            'n_sloc':          n,
            'horizon_h':       self.horizon_h,
            'end_h':           self.t_h,
            'n_ships':         len(self.ships),
            'surviving_ships': surviving,
            'available_ships': avail,
            'n_engagements':   len(self.engagements),
            'engagements':     self.engagements,
            'cost_total':      round(self.cost_total, 1),
            'timeline':        {'control': self._tl_control, 'force': self._tl_force},
        }


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
