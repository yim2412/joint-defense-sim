"""ai_selfplay_loop.py — Phase 5.6.3: 교대 공진화 학습 루프 (빌드 제외 도구).

한 번에 한 쪽만 학습(상대 고정) → 교대 반복. 환경이 정적이라 안정적(plan 12절).
  라운드마다: ① 적 학습(아군 고정) → 적 npz ② 아군 학습(적 고정) → 아군 npz
             ③ 양쪽 고정 대결 평가(friendly_score·enemy_score)
공진화 = 라운드가 진행되며 양측이 번갈아 상대를 압박하며 강해지는 곡선.

  python ai_selfplay_loop.py [rounds] [steps] [n_envs] [seeds]
산출: 라운드별 _selfplay_friendly_cur.npz·_selfplay_enemy_cur.npz + 공진화 곡선 출력.
"""
import sys
import shutil
import numpy as np

from engine_core import normalize_enemy_db
from ai_selfplay_env import (make_enemy_env, make_friendly_env, export_policy_npz,
                          eval_matchup, _BALANCED_PRESETS)

normalize_enemy_db()

F_NPZ = '_selfplay_friendly_cur.npz'   # 현재 아군 정책
E_NPZ = '_selfplay_enemy_cur.npz'      # 현재 적 정책


def _train(factory, steps, n_envs):
    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import SubprocVecEnv
    venv = SubprocVecEnv([factory for _ in range(n_envs)])
    m = PPO('MlpPolicy', venv, device='cpu', verbose=1, n_steps=256, ent_coef=0.01)
    m.learn(total_timesteps=steps)
    venv.close()
    return m


def main(rounds, steps, n_envs, seeds):
    # 시작 아군 = 기존 학습 정책(ai_rl_policy.npz). 적은 첫 라운드 학습이 생성.
    shutil.copy('ai_rl_policy.npz', F_NPZ)
    curve = []
    for rd in range(1, rounds + 1):
        print(f'\n========== 라운드 {rd}/{rounds} ==========', flush=True)
        print(f'[R{rd}] 적 학습 {steps} 스텝 (아군 고정)...', flush=True)
        m_e = _train(make_enemy_env(friendly_policy=F_NPZ), steps, n_envs)
        export_policy_npz(m_e, E_NPZ)
        print(f'[R{rd}] 아군 학습 {steps} 스텝 (적 고정)...', flush=True)
        m_f = _train(make_friendly_env(enemy_policy=E_NPZ), steps, n_envs)
        export_policy_npz(m_f, F_NPZ)
        fscore, escore = eval_matchup(F_NPZ, E_NPZ, seeds)
        curve.append((rd, fscore, escore))
        print(f'[R{rd}] 대결 평가: friendly={fscore:.3f}  enemy={escore:.3f}', flush=True)

    print('\n=== 공진화 곡선 (라운드별 양쪽 고정 대결) ===', flush=True)
    for rd, f, e in curve:
        print(f'  R{rd}: friendly={f:.3f}  enemy={e:.3f}', flush=True)
    print('해석: 교대마다 직전 상대를 겨냥해 학습 → friendly·enemy가 번갈아 우위를 '
          '주고받으면 공진화 성립(한쪽 단조 지배가 아니라 균형 추적).', flush=True)


if __name__ == '__main__':
    rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    steps  = int(sys.argv[2]) if len(sys.argv) > 2 else 100_000
    n_envs = int(sys.argv[3]) if len(sys.argv) > 3 else 8
    seeds  = list(range(1, (int(sys.argv[4]) if len(sys.argv) > 4 else 3) + 1))
    main(rounds, steps, n_envs, seeds)
