"""PPO 본학습 vs baseline(전부 기본값) 검증 — 빌드 제외 도구.

전술 레버를 한 개씩 고정한 정적 측정은 효과가 약했다(±0.05). 그러나 RL은
'상황별 동적 전환'을 배우므로 정적 약신호가 곧 무용은 아니다. 이 스크립트가
판별한다: 학습 정책이 '전부 기본값 고정' baseline을 균형 시나리오에서
유의미하게 이기는가?

  python _rl_train_eval.py [timesteps] [n_envs]
"""
import sys
import time
import numpy as np

from engine import normalize_enemy_db
from engine_v7 import run_battle_simulation
from rl_env import BattleEnv, make_env, _BALANCED_PRESETS, _DEFAULT_CFG

normalize_enemy_db()

_EVAL_SEEDS = range(1, 4)   # seed 3개(엔진 if seed: 때문에 1부터). 방향 판별엔 충분


def _base_cfg(preset, seed):
    return dict(_DEFAULT_CFG, enemy_fleet_preset=preset, sim_seed=seed,
                enable_ship_evasion=True)


def eval_baseline():
    """전부 기본값 고정 정책(auto·salvo2·radar on·target auto·maneuver/cap normal)."""
    cb = lambda s: {'weapon_priority': 'auto', 'max_salvo': 2, 'radar': 'on',
                    'target_priority': 'auto', 'maneuver': 'normal',
                    'cap_posture': 'normal', 'ecm': 'normal'}
    rows = {}
    for p in _BALANCED_PRESETS:
        scores = []
        for seed in _EVAL_SEEDS:
            r = run_battle_simulation(_base_cfg(p, seed), tactical_cb=cb)
            scores.append(r.get('friendly_score', 0.0))
        rows[p] = float(np.mean(scores))
    return rows


def eval_policy(model):
    """학습 정책 — 매 결정점 deterministic 행동."""
    rows = {}
    for p in _BALANCED_PRESETS:
        scores = []
        for seed in _EVAL_SEEDS:
            env = BattleEnv(_base_cfg(p, seed))
            obs, _ = env.reset(seed=seed)
            done = False
            info = {}
            while not done:
                a, _ = model.predict(obs, deterministic=True)
                obs, r, term, trunc, info = env.step(a)
                done = term or trunc
            scores.append(float(info.get('friendly_score', 0.0)))
            env.close()
        rows[p] = float(np.mean(scores))
    return rows


def main(timesteps=200_000, n_envs=8, shaping=False):
    from stable_baselines3 import PPO
    # Phase 5.5c: 스레드 제거(엔진 _simulate 제너레이터 동기 구동)로 worker 크래시 해소 → SubprocVecEnv 복원(병렬 가속).
    from stable_baselines3.common.vec_env import SubprocVecEnv

    print(f'[1/3] baseline 평가 (전부 기본값, {len(_BALANCED_PRESETS)}시나리오 × '
          f'{len(list(_EVAL_SEEDS))}seed)...', flush=True)
    base = eval_baseline()

    print(f'[2/3] PPO 학습 {timesteps} 스텝 ({n_envs}env, shaping={shaping})...', flush=True)
    venv = SubprocVecEnv([make_env(reward_shaping=shaping) for _ in range(n_envs)])
    # verbose=1 → 롤아웃마다 진행률(스텝수·시간) 로그. log_interval=1로 매 업데이트 출력.
    model = PPO('MlpPolicy', venv, device='cpu', verbose=1, n_steps=256)
    t0 = time.perf_counter()
    model.learn(total_timesteps=timesteps, log_interval=1)
    print(f'      학습 완료 {time.perf_counter()-t0:.0f}s', flush=True)
    _tag = 'shaped' if shaping else 'base'
    model.save(f'_rl_ppo_model_{_tag}')   # 평가서 죽어도 모델 보존
    print(f'      모델 저장: _rl_ppo_model_{_tag}.zip', flush=True)
    venv.close()

    print('[3/3] 학습 정책 평가 (동일 시나리오·seed)...', flush=True)
    pol = eval_policy(model)

    print('\n===== baseline vs 학습 정책 (friendly_score) =====')
    bvals, pvals = [], []
    for p in _BALANCED_PRESETS:
        b, q = base[p], pol[p]
        bvals.append(b); pvals.append(q)
        mark = 'WIN' if q - b > 0.02 else ('LOSS' if q - b < -0.02 else '~')
        print(f'  {p[:16]:18s} base={b:.3f}  policy={q:.3f}  d={q-b:+.3f} {mark}')
    bm, pm = np.mean(bvals), np.mean(pvals)
    print(f'\n  전체 평균: base={bm:.3f}  policy={pm:.3f}  d={pm-bm:+.3f}')
    print('  → 학습 정책이 baseline을 유의미하게 이기면(Δ>0) 동적 신호 존재.')


if __name__ == '__main__':
    ts = int(sys.argv[1]) if len(sys.argv) > 1 else 200_000
    ne = int(sys.argv[2]) if len(sys.argv) > 2 else 8
    sh = (len(sys.argv) > 3 and sys.argv[3].lower() in ('1', 'on', 'shaped', 'true'))
    main(ts, ne, shaping=sh)
