"""
rl_env.py — 지속 전장 엔진(BattleEngine)의 gymnasium 래퍼 (Phase 4 RL, 1단계).

엔진(engine_v7.py)은 한 줄도 고치지 않는다. 엔진의 _tactical_pause_cb(원래 사람 GUI
입력을 기다리며 블록되는 전술 의사결정 훅)에 RL 행동을 주입하는 방식.
  · 엔진을 백그라운드 스레드로 run_battle_simulation 실행
  · cb(엔진 스레드)는 관측(state)을 obs 큐에 넣고 action 큐를 블록 대기
  · env.step(action)이 action 큐에 넣어 엔진을 다음 결정 지점까지 진행시킴

1단계(파이프라인 검증)는 기존 레버만 행동으로 쓴다: 방공 무기 우선순위 + 최대 살보.
관측은 집계 9피처, 보상은 종료 시 friendly_score(중간 shaping은 다음 단계).
정본 설계: plan_battle_engine.md 10절.
"""
from __future__ import annotations

import numpy as np
import gymnasium as gym
from gymnasium import spaces

from engine import normalize_enemy_db, FRIENDLY_DB  # noqa: F401
from engine_v7 import BattleEngine, BATTLE_HORIZON_S, calculate_fleet_detect_ranges

normalize_enemy_db()

# Phase 5.5c: _simulate() yield 유발용 truthy sentinel(실제 호출 안 됨 — RL이 직접 send 구동)
_TACTICAL_SENTINEL = object()

# 행동: 방공 무기 우선순위(요격 시 우선 사용할 SAM) — 'auto'는 엔진 기본 선택.
# 공격·대잠 무기는 미사일 방어와 무관해 제외. 잘못된 이름이어도 available()==0으로 자동 폴백.
_WPN_PRIORITY = [
    'auto',
    'SM-3 Block IIA',     # 외기권 BMD
    'SM-6',               # 장거리
    'SM-2 Block IIIB',    # 중거리
    'ESSM Block II',      # 중·단거리
    '해궁 (K-SAAM)',      # 단거리 점방어
    'RIM-116 RAM',        # 점방어
    'CIWS-II (Phalanx)',  # 최후 근접
]
_SALVO_OPTS = [1, 2, 3, 4]
# 레이더 자세: on=자동(ARM 회피는 엔진 자동 유지) / off=능동 차단(ARM 회피 ↔ 탐지 손실).
_RADAR_OPTS = ['on', 'off']
# 표적 우선순위: auto=임박도(기본) / nearest=최근접 / fastest=고속 / leakers=탄도·HGV 우선.
_TARGET_OPTS = ['auto', 'nearest', 'fastest', 'leakers']
# 함대 기동 자세: passive=회피안함(연료↓·생존risk) / normal=현행 / aggressive=조기·대폭(생존↑·연료↑).
_MANEUVER_OPTS = ['passive', 'normal', 'aggressive']
# CAP 전개 자세: forward=공세(멀리·자주, AAM조기소진) / normal=현행 / defensive=AAM절약(가까이·드물게).
_CAP_OPTS = ['forward', 'normal', 'defensive']
# ECM 자세: off=미사용 / normal=현행(적미사일 Pk -30%) / strong=강(-45%). 탄도·HGV·ARM엔 무효.
_ECM_OPTS = ['off', 'normal', 'strong']

_N_FEAT = 14   # 관측 피처 수 (집계 9 + 위협구성·자원 5)

# 균형 학습 시나리오 풀 — 행동 민감도 진단으로 선별.
# score가 중간대(0.1~0.7)면서 약↔강 정책에 따라 outcome/score가 실제로 갈리는
# 매치업만. 항모전단(0.0~0.05 전패)·BMD/극초음속(0.9+ 전승)은 구배가 없어 제외.
# reset마다 이 풀에서 무작위 추출 → 단일 국면 과적합 방지 + 강건한 정책 학습.
_BALANCED_PRESETS = [
    '전면전 포화',          # 약 win ↔ 강 loss (승패 갈림)
    '중국 3축 동시 공격',   # draw ↔ win
    '러시아 해군 입체',     # 큰 민감도
    '쓰시마 봉쇄 돌파',     # win ↔ draw
    '북한 포화 공격 (40발)',  # 경계
    '수상함 편대전',        # 민감도 최대(약↔강 +0.106)
]

# 표준 학습 시나리오 (enemy_fleet_preset 미지정 → reset이 풀에서 무작위 추출).
_DEFAULT_CFG = dict(
    fleet_region='동해 북부', season='summer', weather='맑음 (주간)',
    enable_munition_limit=True, enable_battle_mode=True,
    enable_ship_evasion=True,  # 함대 기동 자세 레버 작동 전제 (회피 ON)
    enemy_fleet_mode='preset', fleet_preset='이지스 기동전단',
    n_threads=4, cd_time_s=10, confirm_time_s=3,
)


class BattleEnv(gym.Env):
    """지속 전장 1 에피소드 = 1 전장. 행동은 _tactical_interval초마다 1회."""

    metadata = {'render_modes': []}

    def __init__(self, cfg: dict | None = None, tactical_interval: int = 60,
                 reward_shaping: bool = False):
        # Phase 5.5: interval 30→60 — horizon 7200(5.1)에서 결정 240→~120으로 비용·영향력 균형.
        # reward_shaping 기본 OFF: 현 짧은 전장에선 중간보상이 종료보상을 희석해
        # 오히려 평균 하락(+0.037→+0.022). 토글은 유지 — 작전급 긴 전장(진짜 전장)서 재시도.
        super().__init__()
        self.reward_shaping = reward_shaping
        self.base_cfg = dict(cfg or _DEFAULT_CFG)
        self.base_cfg['enable_battle_mode'] = True
        self.base_cfg['tactical_interval'] = int(tactical_interval)
        # Phase 5.5: 관측 진행도 정규화 분모 — horizon 연동(5.1 7200 상향 반영)
        self._horizon = float(self.base_cfg.get('battle_horizon_s', BATTLE_HORIZON_S))
        # enemy_fleet_preset 직접 지정 시 고정, 아니면 균형 풀에서 매 에피소드 추출.
        self._fixed_preset = self.base_cfg.get('enemy_fleet_preset')
        self._ep_preset = self._fixed_preset or _BALANCED_PRESETS[0]

        self.action_space = spaces.MultiDiscrete(
            [len(_WPN_PRIORITY), len(_SALVO_OPTS), len(_RADAR_OPTS),
             len(_TARGET_OPTS), len(_MANEUVER_OPTS), len(_CAP_OPTS),
             len(_ECM_OPTS)])
        self.observation_space = spaces.Box(
            low=-1.0, high=np.inf, shape=(_N_FEAT,), dtype=np.float32)

        # Phase 5.5c: 스레드/큐 제거 — 엔진 _simulate() 제너레이터를 동기 구동
        self._engine = None
        self._gen = None
        self._result: dict | None = None
        self._last_state = None

    # ── 엔진 구동(동기·제너레이터) ────────────────────────────────────────────
    @staticmethod
    def _action_to_choice(action):
        """MultiDiscrete 행동 → 엔진 전술 choice dict."""
        a = np.asarray(action).ravel()
        wi, si, ri, ti, mi, ci, ei = (int(a[0]), int(a[1]), int(a[2]),
                                      int(a[3]), int(a[4]), int(a[5]), int(a[6]))
        return {'weapon_priority': _WPN_PRIORITY[wi], 'max_salvo': _SALVO_OPTS[si],
                'radar': _RADAR_OPTS[ri], 'target_priority': _TARGET_OPTS[ti],
                'maneuver': _MANEUVER_OPTS[mi], 'cap_posture': _CAP_OPTS[ci],
                'ecm': _ECM_OPTS[ei]}

    def _build_engine(self):
        """BattleEngine 생성(run_battle_simulation 전처리 복제 — 탐지거리 자동계산)."""
        cfg = dict(self.base_cfg)
        cfg['enemy_fleet_preset'] = self._ep_preset
        if not cfg.get('detect_km_manual', False):
            r = calculate_fleet_detect_ranges(
                cfg.get('fleet_preset', '단독 작전'), cfg.get('weather', '맑음 (주간)'))
            cfg['detect_km'], cfg['surface_detect_km'], cfg['sub_detect_km'] = \
                r['대공'], r['대함'], r['대잠']
        eng = BattleEngine(cfg)
        eng._tactical_pause_cb = _TACTICAL_SENTINEL   # yield 유발(호출 안 됨 — send로 구동)
        return eng

    # ── 관측·보상 ────────────────────────────────────────────────────────────
    def _featurize(self, state) -> np.ndarray:
        if state is None:
            return np.zeros(_N_FEAT, dtype=np.float32)
        threats = state.threats or []
        ships = state.ships or []
        dists = [t['dist_km'] for t in threats] or [999.0]
        hp_sum = float(sum(t.get('hp', 0) for t in threats))
        alive_ships = [s for s in ships if s.get('alive')]
        fleet_max = float(sum(s.get('max_hp', 0) for s in ships)) or 1.0
        fleet_hp = float(sum(s.get('hp', 0) for s in alive_ships))
        tot = state.total_threats or 0
        irate = (state.intercepted / tot) if tot else 0.0
        ex = getattr(state, 'extra', None) or {}
        feats = [
            len(threats) / 20.0,               # 생존 위협 수
            min(dists) / 500.0,                # 최근접 거리
            (sum(dists) / len(dists)) / 500.0,  # 평균 거리
            hp_sum / 100.0,                    # 위협 총 HP
            len(alive_ships) / 10.0,           # 생존 함정 수
            fleet_hp / fleet_max,              # 함대 HP 비
            irate,                             # 요격률
            (state.shots_fired or 0) / 100.0,  # 발사 수
            (state.t or 0.0) / self._horizon,  # 진행도(horizon 연동 — 0~1 유지)
            # 위협 구성·자원 (전장 모드 extra — 레버 상황 적응용)
            ex.get('leaker_frac', 0.0),        # 탄도·HGV 비율(ECM 무효)
            ex.get('asm_inflight', 0.0),       # 비행 중 대함미사일 수(ECM 유효 표적)
            ex.get('aircraft_frac', 0.0),      # 항공 위협 비율(CAP·표적)
            ex.get('ammo_frac', 1.0),          # 탄약 잔여비(살보·절약)
            ex.get('fuel_frac', 1.0),          # 연료 잔여비(기동 적극도)
        ]
        return np.asarray(feats, dtype=np.float32)

    @staticmethod
    def _fleet_hp(state) -> float:
        """함대 생존 HP 합(정규화 분모 없이 절대량) — 피해 델타 계산용."""
        if state is None:
            return 0.0
        return float(sum(s.get('hp', 0) for s in (state.ships or []) if s.get('alive')))

    def _shaping_reward(self, prev, cur) -> float:
        """포텐셜 기반 중간 보상 — 종료 보상(friendly_score)을 왜곡하지 않게 작게.
        신규 요격(+)·함대 피해(−)만. 한 에피소드 합이 ±0.2 이내가 되도록 계수 보수적."""
        if not self.reward_shaping or prev is None or cur is None:
            return 0.0
        d_intc = max(0, (cur.intercepted or 0) - (prev.intercepted or 0))
        d_hp   = self._fleet_hp(cur) - self._fleet_hp(prev)   # 피해면 음수
        # 요격 1건 +0.01, 함대 HP 1단위 손실 -0.02 (피해 회피를 요격보다 중시)
        r = 0.01 * d_intc + 0.02 * min(0.0, d_hp)
        # 단일 스텝 보상 클립(폭주 방지) — 종료 보상 대비 작게 유지
        return float(max(-0.05, min(0.05, r)))

    # ── gym API ──────────────────────────────────────────────────────────────
    def _finish(self):
        """에피소드 종료 — friendly_score 종료 보상 + info. (제너레이터 StopIteration 후)

        info에 약점 분석(improve_report.py S1)용 분해를 함께 노출한다 — 목표별
        progress·자원·누출. info 추가일 뿐 RNG·엔진을 건드리지 않아 결정론·회귀 안전."""
        r = self._result or {}
        fscore = float(r.get('friendly_score', 0.0))
        obs = self._featurize(self._last_state)
        # 목표별 progress(어느 임무가 점수를 깎나) — 아군 목표만 {otype: progress}
        objectives = {ob.get('type'): ob.get('progress')
                      for ob in r.get('objectives', [])
                      if ob.get('side') == 'friendly'}
        st = self._last_state
        ex = (getattr(st, 'extra', None) or {}) if st is not None else {}
        tot = (st.total_threats if st is not None else 0) or 0
        info = {'outcome': r.get('outcome'),
                'friendly_score': fscore,
                'enemy_score': float(r.get('enemy_score', 0.0)),
                'preset': self._ep_preset,
                # ── S1 약점 분석 분해 ──
                'objectives': objectives,                       # 목표별 progress
                'ammo_frac': float(ex.get('ammo_frac', 1.0)),   # 탄약 잔여비(0=소진)
                'fuel_frac': float(ex.get('fuel_frac', 1.0)),   # 연료 잔여비
                'leaker_frac': float(ex.get('leaker_frac', 0.0)),  # 탄도·HGV 비율
                'intercept_rate': ((st.intercepted / tot) if (st is not None and tot) else 0.0),
                'total_threats': tot}
        return obs, fscore, True, False, info

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        # 고정 모드가 아니면 균형 풀에서 이번 에피소드 적 편대 추출(seed 결정론).
        if not self._fixed_preset:
            i = int(self.np_random.integers(len(_BALANCED_PRESETS)))
            self._ep_preset = _BALANCED_PRESETS[i]
        # Phase 5.5c: 엔진 제너레이터 동기 구동 — 스레드/큐 없음.
        if self._gen is not None:
            self._gen.close()
        self._result = None
        self._last_state = None
        self._engine = self._build_engine()
        self._gen = self._engine._simulate()
        try:
            state = next(self._gen)          # 첫 결정 지점
        except StopIteration as e:           # 결정 없이 종료(0결정 전장)
            self._result = e.value or {}
            self._gen = None                 # 소진 — step이 보관된 _result로 즉시 done
            state = None
        self._last_state = state
        return self._featurize(state), {}

    def step(self, action):
        if self._gen is None:                # 이미 종료된 에피소드(0결정 등) — 즉시 done
            return self._finish()
        choice = self._action_to_choice(action)
        try:
            nxt = self._gen.send(choice)
        except StopIteration as e:           # 에피소드 종료
            self._result = e.value or {}
            self._gen = None
            return self._finish()
        shaped = self._shaping_reward(self._last_state, nxt)  # 중간 진행 신호(작게)
        self._last_state = nxt
        return self._featurize(nxt), shaped, False, False, {}

    def close(self):
        if self._gen is not None:
            self._gen.close()
            self._gen = None


def make_env(cfg: dict | None = None, tactical_interval: int = 60,
             reward_shaping: bool = False):
    """SubprocVecEnv용 env 팩토리 (모듈 레벨 — Windows spawn 재import 시 picklable)."""
    def _init():
        return BattleEnv(cfg, tactical_interval, reward_shaping=reward_shaping)
    return _init


# ════════════════════════════════════════════════════════════════════════════
#  스모크 / 속도 측정 (설치 후: python rl_env.py)
# ════════════════════════════════════════════════════════════════════════════
def _smoke_random(episodes: int = 3):
    """랜덤 행동 롤아웃 — env가 obs/보상/done을 제대로 돌리는지 확인."""
    env = BattleEnv()
    print(f'obs_space={env.observation_space.shape}  action_space={env.action_space.nvec}')
    for ep in range(episodes):
        obs, _ = env.reset(seed=ep)
        done = False
        steps = 0
        total_r = 0.0
        while not done:
            a = env.action_space.sample()
            obs, r, term, trunc, info = env.step(a)
            done = term or trunc
            steps += 1
            total_r += r
        print(f"  ep{ep}: [{info.get('preset')}] {steps} 결정, 보상 {total_r:.3f}, "
              f"outcome={info.get('outcome')} fscore={info.get('friendly_score'):.3f}")
    env.close()


def _smoke_ppo(timesteps: int = 10_000):
    """초소형 PPO — SB3 학습 배선 + 정책 오버헤드 포함 실제 steps/s 측정."""
    import time
    from stable_baselines3 import PPO
    env = BattleEnv()
    model = PPO('MlpPolicy', env, device='auto', verbose=0)
    t0 = time.perf_counter()
    model.learn(total_timesteps=timesteps)
    dt = time.perf_counter() - t0
    print(f'PPO {timesteps} 스텝: {dt:.1f}s → {timesteps/dt:.0f} 스텝/s '
          f"(device={model.device})")
    env.close()


def _smoke_vec(n_envs: int = 8, timesteps: int = 40_000):
    """SubprocVecEnv 병렬 PPO — 단일 대비 가속비 측정 (Windows spawn 검증)."""
    import time
    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import SubprocVecEnv
    venv = SubprocVecEnv([make_env() for _ in range(n_envs)])
    # n_steps×n_envs = 업데이트당 롤아웃. 작게 둬 측정 중 최소 1회 업데이트 보장.
    model = PPO('MlpPolicy', venv, device='cpu', verbose=0, n_steps=256)
    t0 = time.perf_counter()
    model.learn(total_timesteps=timesteps)
    dt = time.perf_counter() - t0
    print(f'VecPPO {n_envs}env {timesteps} 스텝: {dt:.1f}s → {timesteps/dt:.0f} 스텝/s')
    venv.close()


if __name__ == '__main__':
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else 'random'
    if mode == 'random':
        _smoke_random()
    elif mode == 'ppo':
        _smoke_ppo()
    elif mode == 'vec':
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 8
        _smoke_vec(n_envs=n)
    else:
        print('usage: python rl_env.py [random|ppo|vec [n_envs]]')
