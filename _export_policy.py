"""_export_policy.py — Phase 4 RL ⑥: 학습 정책(torch) → numpy 가중치(npz) 추출 (빌드 제외 도구)

학습은 개발 PC(torch·SB3), exe는 `rl_policy.npz` + numpy 추론만(rl_infer.py). plan 10절 정본.
SB3 PPO MlpPolicy 구조(고정): obs(14) → Linear(14→64) → tanh → Linear(64→64) → tanh
→ action_net Linear(64→27). 27 = sum(MultiDiscrete nvec [8,4,2,4,3,3,3]).

추출 후 numpy forward가 SB3 deterministic predict와 **동일 action**을 내는지 1000개 랜덤
obs로 자동 검증(불일치 0이어야 통과). 통과 시에만 npz 저장.

  python _export_policy.py [model.zip] [out.npz]
"""
import sys
import numpy as np


def _np_forward(npz, obs):
    """numpy 전용 정책 forward (rl_infer와 동일 식) → MultiDiscrete action(인덱스 배열)."""
    h = np.tanh(obs @ npz['w0'].T + npz['b0'])
    h = np.tanh(h @ npz['w2'].T + npz['b2'])
    logits = h @ npz['wa'].T + npz['ba']          # (27,)
    nvec = npz['nvec']
    out, off = [], 0
    for n in nvec:                                # 차원별 분할 후 argmax(deterministic)
        out.append(int(np.argmax(logits[off:off + n])))
        off += int(n)
    return np.array(out, dtype=np.int64)


def export(model_path, out_path):
    from stable_baselines3 import PPO
    m = PPO.load(model_path, device='cpu')
    sd = m.policy.state_dict()
    g = lambda k: sd[k].cpu().numpy().astype(np.float32)
    data = {
        'w0': g('mlp_extractor.policy_net.0.weight'), 'b0': g('mlp_extractor.policy_net.0.bias'),
        'w2': g('mlp_extractor.policy_net.2.weight'), 'b2': g('mlp_extractor.policy_net.2.bias'),
        'wa': g('action_net.weight'),                 'ba': g('action_net.bias'),
        'nvec': np.asarray(m.action_space.nvec, dtype=np.int64),
        'obs_dim': np.int64(m.observation_space.shape[0]),
    }
    # ── 검증: numpy forward == SB3 deterministic predict (랜덤 obs 1000개) ──
    rng = np.random.default_rng(0)
    n_obs = int(data['obs_dim'])
    mism = 0
    for _ in range(1000):
        obs = rng.standard_normal(n_obs).astype(np.float32)
        sb3_act, _ = m.predict(obs, deterministic=True)
        np_act = _np_forward(data, obs)
        if not np.array_equal(np.asarray(sb3_act).ravel(), np_act):
            mism += 1
    if mism:
        print(f'❌ 검증 실패 — numpy/SB3 action 불일치 {mism}/1000. npz 미저장.')
        sys.exit(1)
    np.savez(out_path, **data)
    print(f'✅ 검증 통과(불일치 0/1000) — 저장: {out_path}')
    print(f'   구조 obs={n_obs} nvec={list(data["nvec"])} '
          f'params={sum(v.size for k,v in data.items() if k.startswith(("w","b")))}')


if __name__ == '__main__':
    model = sys.argv[1] if len(sys.argv) > 1 else '_rl_ckpt/ppo_shaped_ent0.01_1000000_steps.zip'
    out = sys.argv[2] if len(sys.argv) > 2 else 'rl_policy.npz'
    export(model, out)
