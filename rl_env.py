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

import queue
import threading

import numpy as np
import gymnasium as gym
from gymnasium import spaces

from engine import normalize_enemy_db, FRIENDLY_DB  # noqa: F401
from engine_v7 import run_battle_simulation

normalize_enemy_db()

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

_N_FEAT = 9   # 관측 피처 수 (집계)

# 균형 학습 시나리오 풀 — 행동 민감도 진단(_rl_scenario_probe.py)으로 선별.
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
    enemy_fleet_mode='preset', fleet_preset='이지스 기동전단',
    n_threads=4, cd_time_s=10, confirm_time_s=3,
)


class _EnvAbort(Exception):
    """reset/close 시 진행 중인 엔진 스레드를 즉시 종료시키는 신호."""


class BattleEnv(gym.Env):
    """지속 전장 1 에피소드 = 1 전장. 행동은 _tactical_interval초마다 1회."""

    metadata = {'render_modes': []}

    def __init__(self, cfg: dict | None = None, tactical_interval: int = 30):
        super().__init__()
        self.base_cfg = dict(cfg or _DEFAULT_CFG)
        self.base_cfg['enable_battle_mode'] = True
        self.base_cfg['tactical_interval'] = int(tactical_interval)
        # enemy_fleet_preset 직접 지정 시 고정, 아니면 균형 풀에서 매 에피소드 추출.
        self._fixed_preset = self.base_cfg.get('enemy_fleet_preset')
        self._ep_preset = self._fixed_preset or _BALANCED_PRESETS[0]

        self.action_space = spaces.MultiDiscrete(
            [len(_WPN_PRIORITY), len(_SALVO_OPTS), len(_RADAR_OPTS)])
        self.observation_space = spaces.Box(
            low=-1.0, high=np.inf, shape=(_N_FEAT,), dtype=np.float32)

        self._obs_q: queue.Queue | None = None
        self._act_q: queue.Queue | None = None
        self._thread: threading.Thread | None = None
        self._result: dict | None = None
        self._last_state = None

    # ── 엔진 스레드 측 ───────────────────────────────────────────────────────
    def _tactical_cb(self, state):
        """엔진 스레드에서 호출 — 관측 송출 후 행동 대기(블록)."""
        self._obs_q.put(state)
        action = self._act_q.get()           # env.step()이 넣을 때까지 블록
        if action is None:                   # reset/close 신호
            raise _EnvAbort()
        wi, si, ri = action
        return {'weapon_priority': _WPN_PRIORITY[wi], 'max_salvo': _SALVO_OPTS[si],
                'radar': _RADAR_OPTS[ri]}

    def _run_engine(self):
        cfg = dict(self.base_cfg)
        cfg['enemy_fleet_preset'] = self._ep_preset
        try:
            self._result = run_battle_simulation(
                cfg, tactical_cb=self._tactical_cb)
        except _EnvAbort:
            self._result = None
            return
        self._obs_q.put(None)                # 에피소드 종료 센티넬

    def _stop_thread(self):
        if self._thread and self._thread.is_alive():
            try:
                self._act_q.put(None)        # cb 언블록 → _EnvAbort
            except Exception:
                pass
            self._thread.join(timeout=3.0)

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
        feats = [
            len(threats) / 20.0,               # 생존 위협 수
            min(dists) / 500.0,                # 최근접 거리
            (sum(dists) / len(dists)) / 500.0,  # 평균 거리
            hp_sum / 100.0,                    # 위협 총 HP
            len(alive_ships) / 10.0,           # 생존 함정 수
            fleet_hp / fleet_max,              # 함대 HP 비
            irate,                             # 요격률
            (state.shots_fired or 0) / 100.0,  # 발사 수
            (state.t or 0.0) / 1800.0,         # 진행도
        ]
        return np.asarray(feats, dtype=np.float32)

    # ── gym API ──────────────────────────────────────────────────────────────
    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        # 고정 모드가 아니면 균형 풀에서 이번 에피소드 적 편대 추출(seed 결정론).
        if not self._fixed_preset:
            i = int(self.np_random.integers(len(_BALANCED_PRESETS)))
            self._ep_preset = _BALANCED_PRESETS[i]
        self._stop_thread()
        self._obs_q = queue.Queue()
        self._act_q = queue.Queue()
        self._result = None
        self._last_state = None
        self._thread = threading.Thread(target=self._run_engine, daemon=True)
        self._thread.start()
        state = self._obs_q.get()            # 첫 결정 지점 (또는 결정 없이 종료=None)
        self._last_state = state
        return self._featurize(state), {}

    def step(self, action):
        a = np.asarray(action).ravel()
        self._act_q.put((int(a[0]), int(a[1]), int(a[2])))
        nxt = self._obs_q.get()
        if nxt is None:                      # 에피소드 종료
            r = self._result or {}
            fscore = float(r.get('friendly_score', 0.0))
            obs = self._featurize(self._last_state)
            info = {'outcome': r.get('outcome'),
                    'friendly_score': fscore,
                    'enemy_score': float(r.get('enemy_score', 0.0)),
                    'preset': self._ep_preset}
            return obs, fscore, True, False, info   # 종료 보상 = friendly_score
        self._last_state = nxt
        return self._featurize(nxt), 0.0, False, False, {}   # 중간 보상 0 (1단계)

    def close(self):
        self._stop_thread()


def make_env(cfg: dict | None = None, tactical_interval: int = 30):
    """SubprocVecEnv용 env 팩토리 (모듈 레벨 — Windows spawn 재import 시 picklable)."""
    def _init():
        return BattleEnv(cfg, tactical_interval)
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
