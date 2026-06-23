"""selfplay_env.py — Phase 5.6.2: 적 지휘 RL 환경 (EnemyEnv). 빌드 제외 RL 인프라.

self-play 교대 학습의 한 면 — **아군 정책을 numpy 고정(rl_infer)하고 적만 학습**한다.
한 번에 한 에이전트만 학습해 환경이 정적 = 안정적(plan 12절). rl_env.BattleEnv를 상속해
엔진 구동(_simulate 제너레이터 동기 send)·관측(featurize)을 재사용하고, 행동·보상만 적 측으로
바꾼다.

  · 행동: 적 전술 모드 3종(saturation/dispersal/deception) — _adaptive_mode를 통해
    _enemy_fire 살보·표적집중 결정(5.6.1 엔진 훅 enable: ai_tactic='rl').
  · 관측: 전장 상태 14피처(아군과 동일 — 전장은 대칭 관측). 적 시점 해석.
  · 보상: 종료 시 enemy_score(적 임무 점수). 아군 friendly_score의 반대 목표.
  · 아군: rl_policy.npz 고정 정책이 매 결정 7레버를 채움(choice에 enemy_mode와 합침).
"""
from __future__ import annotations

import numpy as np
import gymnasium as gym
from gymnasium import spaces

import rl_infer
from rl_env import BattleEnv, _BALANCED_PRESETS, _DEFAULT_CFG  # noqa: F401  (재export·동일 풀)

# 적 전술 모드 — 5.6.1 엔진 훅이 받는 enemy_mode 값과 일치해야 함.
_ENEMY_MODES = ['saturation', 'dispersal', 'deception']


class EnemyEnv(BattleEnv):
    """적 지휘 학습 환경. 아군=고정 numpy 정책, 적=학습. 보상=enemy_score."""

    def __init__(self, cfg: dict | None = None, tactical_interval: int = 60,
                 friendly_policy: str = 'rl_policy.npz'):
        super().__init__(cfg, tactical_interval, reward_shaping=False)
        # 5.6.1 엔진 훅 활성 — 적 전술 모드를 외부(이 env)가 주입.
        self.base_cfg['ai_tactic'] = 'rl'
        # 적 행동공간 = 전술 모드 3종. 관측은 부모(전장 14피처) 그대로.
        self.action_space = spaces.MultiDiscrete([len(_ENEMY_MODES)])
        # 아군 고정 정책(numpy 추론). 없으면 None → 아군은 엔진 기본 전술(빈 choice).
        self._friendly_cb = rl_infer.make_policy_cb(friendly_policy, self._horizon)

    def _enemy_choice(self, enemy_action, state) -> dict:
        """적 행동 + 아군 고정 정책을 한 choice dict로 합침(같은 결정 지점에 동승)."""
        c = dict(self._friendly_cb(state)) if self._friendly_cb else {}
        ei = int(np.asarray(enemy_action).ravel()[0])
        c['enemy_mode'] = _ENEMY_MODES[ei]
        return c

    def _finish_enemy(self):
        """에피소드 종료 — enemy_score 종료 보상 + info."""
        r = self._result or {}
        escore = float(r.get('enemy_score', 0.0))
        obs = self._featurize(self._last_state)
        info = {'outcome': r.get('outcome'),
                'enemy_score': escore,
                'friendly_score': float(r.get('friendly_score', 0.0)),
                'preset': self._ep_preset}
        return obs, escore, True, False, info

    def step(self, action):
        if self._gen is None:                       # 이미 종료(0결정) — 즉시 done
            return self._finish_enemy()
        choice = self._enemy_choice(action, self._last_state)
        try:
            nxt = self._gen.send(choice)
        except StopIteration as e:
            self._result = e.value or {}
            self._gen = None
            return self._finish_enemy()
        self._last_state = nxt
        return self._featurize(nxt), 0.0, False, False, {}   # 중간보상 0(MVP, 종료보상만)


def make_enemy_env(cfg: dict | None = None, tactical_interval: int = 60,
                   friendly_policy: str = 'rl_policy.npz'):
    """SubprocVecEnv용 팩토리(모듈 레벨 — Windows spawn picklable)."""
    def _init():
        return EnemyEnv(cfg, tactical_interval, friendly_policy=friendly_policy)
    return _init


# ════════════════════════════════════════════════════════════════════════════
def _smoke_random(episodes: int = 3):
    """랜덤 적 행동 롤아웃 — enemy obs/보상/done 배선 확인."""
    env = EnemyEnv()
    print(f'obs={env.observation_space.shape} action(적 모드)={env.action_space.nvec} '
          f'아군정책={"로드됨" if env._friendly_cb else "없음(기본전술)"}')
    for ep in range(episodes):
        env.reset(seed=ep)
        done = False; steps = 0
        while not done:
            _, r, term, trunc, info = env.step(env.action_space.sample())
            done = term or trunc; steps += 1
        print(f"  ep{ep}: [{info.get('preset')}] {steps}결정 enemy_score={info.get('enemy_score'):.3f} "
              f"outcome={info.get('outcome')}")
    env.close()


def _eval_enemy(model, seeds, presets=None):
    """적 정책(또는 None=랜덤) 평가 → 시나리오별 enemy_score 평균."""
    presets = presets or _BALANCED_PRESETS
    out = {}
    for p in presets:
        scs = []
        for sd in seeds:
            env = EnemyEnv(cfg=dict(_DEFAULT_CFG, enemy_fleet_preset=p))
            obs, _ = env.reset(seed=sd)
            done = False; info = {}
            while not done:
                if model is None:
                    a = env.action_space.sample()
                else:
                    a, _ = model.predict(obs, deterministic=True)
                obs, _, term, trunc, info = env.step(a)
                done = term or trunc
            scs.append(info.get('enemy_score', 0.0))
            env.close()
        out[p] = float(np.mean(scs))
    return out


if __name__ == '__main__':
    import sys
    mode = sys.argv[1] if len(sys.argv) > 1 else 'random'
    if mode == 'random':
        _smoke_random()
    elif mode == 'ppo':
        import time
        from stable_baselines3 import PPO
        env = EnemyEnv()
        model = PPO('MlpPolicy', env, device='cpu', verbose=0, n_steps=256)
        t0 = time.perf_counter()
        model.learn(total_timesteps=int(sys.argv[2]) if len(sys.argv) > 2 else 10_000)
        print(f'적 PPO 학습 OK {time.perf_counter()-t0:.0f}s')
        env.close()
