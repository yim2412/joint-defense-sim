"""_selfplay_train.py — Phase 5.6.2 검증: 적만 학습이 enemy_score를 올리는지 (빌드 제외 도구).

아군=rl_policy.npz 고정. 적 PPO 학습 → 랜덤 적 baseline 대비 균형 6시나리오 enemy_score 비교.
학습 적이 일관 상회하면 self-play의 한 면(적 학습) 성립.

  python _selfplay_train.py [timesteps] [n_envs] [seeds]
"""
import sys
import numpy as np

from engine import normalize_enemy_db
from selfplay_env import make_enemy_env, _eval_enemy, _BALANCED_PRESETS

normalize_enemy_db()


def main(timesteps, n_envs, n_seeds):
    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import SubprocVecEnv
    seeds = list(range(1, n_seeds + 1))

    print(f'[baseline] 랜덤 적 enemy_score — 균형 {len(_BALANCED_PRESETS)}시나리오 × {n_seeds}seed...',
          flush=True)
    base = _eval_enemy(None, seeds)

    print(f'[학습] 적 PPO {timesteps} 스텝 ({n_envs}env, 아군 고정)...', flush=True)
    venv = SubprocVecEnv([make_enemy_env() for _ in range(n_envs)])
    model = PPO('MlpPolicy', venv, device='cpu', verbose=1, n_steps=256, ent_coef=0.01)
    model.learn(total_timesteps=timesteps)
    venv.close()
    model.save('_selfplay_enemy')

    print('[평가] 학습 적 enemy_score...', flush=True)
    pol = _eval_enemy(model, seeds)

    print('\n=== 적 enemy_score (랜덤 → 학습) ===', flush=True)
    for p in _BALANCED_PRESETS:
        print(f'  {p}: {base[p]:.3f} → {pol[p]:.3f}  (Δ{pol[p]-base[p]:+.3f})', flush=True)
    mb, mp = np.mean(list(base.values())), np.mean(list(pol.values()))
    print(f'  전체 평균: {mb:.3f} → {mp:.3f}  (Δ{mp-mb:+.3f})', flush=True)
    print(f"\n판정: {'✅ 적 학습 유효(enemy_score 상회)' if mp - mb > 0.01 else '△ 차이 미미'}", flush=True)


if __name__ == '__main__':
    ts = int(sys.argv[1]) if len(sys.argv) > 1 else 100_000
    ne = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    ns = int(sys.argv[3]) if len(sys.argv) > 3 else 3
    main(ts, ne, ns)
