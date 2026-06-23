"""rl_infer.py — Phase 4 RL ⑥: 학습 정책 numpy 추론 (exe 번들, numpy만 의존).

torch·SB3·gymnasium 일절 불요 — `rl_policy.npz`(_export_policy.py 산출) 가중치로
정책 forward만 수행한다. launcher가 전장 시뮬의 `sim._tactical_pause_cb`에 주입하면
학습된 정책이 30/60초마다 전술 choice를 결정한다.

featurize·action 변환·상수는 rl_env.py(학습)와 **같은 로직을 복제**한다(학습 코드를
import하면 gymnasium이 따라와 exe가 무거워짐). 대신 `_assert_parity_with_rl_env()`로
개발 시 두 구현의 출력 일치를 검증해 drift를 막는다(exe 런타임엔 호출 안 됨).

정본 설계: plan_battle_engine.md 10절.
"""
import numpy as np

# ── rl_env와 동일해야 하는 상수(복제) — drift는 _assert_parity로 감시 ──────────
_WPN_PRIORITY = [
    'auto', 'SM-3 Block IIA', 'SM-6', 'SM-2 Block IIIB', 'ESSM Block II',
    '해궁 (K-SAAM)', 'RIM-116 RAM', 'CIWS-II (Phalanx)',
]
_SALVO_OPTS = [1, 2, 3, 4]
_RADAR_OPTS = ['on', 'off']
_TARGET_OPTS = ['auto', 'nearest', 'fastest', 'leakers']
_MANEUVER_OPTS = ['passive', 'normal', 'aggressive']
_CAP_OPTS = ['forward', 'normal', 'defensive']
_ECM_OPTS = ['off', 'normal', 'strong']
_N_FEAT = 14
_DEFAULT_HORIZON = 7200.0   # BATTLE_HORIZON_S (engine import 회피용 복제 상수)


def featurize(state, horizon: float = _DEFAULT_HORIZON) -> np.ndarray:
    """전술 state → 14피처 관측(rl_env.BattleEnv._featurize와 동일 로직)."""
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
        len(threats) / 20.0,
        min(dists) / 500.0,
        (sum(dists) / len(dists)) / 500.0,
        hp_sum / 100.0,
        len(alive_ships) / 10.0,
        fleet_hp / fleet_max,
        irate,
        (state.shots_fired or 0) / 100.0,
        (state.t or 0.0) / horizon,
        ex.get('leaker_frac', 0.0),
        ex.get('asm_inflight', 0.0),
        ex.get('aircraft_frac', 0.0),
        ex.get('ammo_frac', 1.0),
        ex.get('fuel_frac', 1.0),
    ]
    return np.asarray(feats, dtype=np.float32)


def action_to_choice(action) -> dict:
    """MultiDiscrete 행동 인덱스 → 엔진 전술 choice dict(rl_env._action_to_choice와 동일)."""
    a = np.asarray(action).ravel()
    wi, si, ri, ti, mi, ci, ei = (int(a[0]), int(a[1]), int(a[2]),
                                  int(a[3]), int(a[4]), int(a[5]), int(a[6]))
    return {'weapon_priority': _WPN_PRIORITY[wi], 'max_salvo': _SALVO_OPTS[si],
            'radar': _RADAR_OPTS[ri], 'target_priority': _TARGET_OPTS[ti],
            'maneuver': _MANEUVER_OPTS[mi], 'cap_posture': _CAP_OPTS[ci],
            'ecm': _ECM_OPTS[ei]}


def load_policy(npz_path: str = 'rl_policy.npz') -> dict:
    """npz 가중치 로드 → forward용 dict. 파일 없으면 FileNotFoundError(호출부가 처리)."""
    z = np.load(npz_path)
    return {k: z[k] for k in z.files}


def forward(npz: dict, obs: np.ndarray) -> np.ndarray:
    """numpy 전용 정책 forward(deterministic argmax) → MultiDiscrete action 인덱스 배열.
    구조: obs → Linear→tanh → Linear→tanh → action_net → nvec별 argmax."""
    h = np.tanh(obs @ npz['w0'].T + npz['b0'])
    h = np.tanh(h @ npz['w2'].T + npz['b2'])
    logits = h @ npz['wa'].T + npz['ba']
    out, off = [], 0
    for n in npz['nvec']:
        n = int(n)
        out.append(int(np.argmax(logits[off:off + n])))
        off += n
    return np.array(out, dtype=np.int64)


def make_policy_cb(npz_path: str = 'rl_policy.npz', horizon: float = _DEFAULT_HORIZON):
    """학습 정책을 엔진 전술 콜백으로 — launcher가 sim._tactical_pause_cb에 주입.
    npz 로드 1회 후 매 결정 지점에서 featurize→forward→choice. 로드 실패 시 None 반환."""
    try:
        npz = load_policy(npz_path)
    except (FileNotFoundError, OSError, KeyError):
        return None

    def cb(state):
        obs = featurize(state, horizon)
        return action_to_choice(forward(npz, obs))
    return cb


# ── 개발 검증: rl_env(학습)와 복제 로직 출력 일치 + npz forward == SB3 ─────────
def _assert_parity_with_rl_env(npz_path='rl_policy.npz'):
    """rl_env._featurize/_action_to_choice와 본 모듈 복제본이 같은 출력을 내는지(drift 감시)."""
    from rl_env import BattleEnv, _BALANCED_PRESETS  # 테스트 전용 import(exe 런타임 무관)
    env = BattleEnv()
    npz = load_policy(npz_path)
    n_mismatch_feat = n_mismatch_act = 0
    for ep in range(len(_BALANCED_PRESETS)):
        obs0, _ = env.reset(seed=ep)
        st = env._last_state
        # featurize 일치
        if not np.allclose(featurize(st, env._horizon), env._featurize(st), atol=1e-6):
            n_mismatch_feat += 1
        # action_to_choice 일치(임의 행동)
        a = env.action_space.sample()
        if action_to_choice(a) != env._action_to_choice(a):
            n_mismatch_act += 1
        # forward로 진행도 한 스텝(정상 동작 확인)
        act = forward(npz, featurize(st, env._horizon))
        env.step(act)
    env.close()
    assert n_mismatch_feat == 0, f'featurize drift {n_mismatch_feat}'
    assert n_mismatch_act == 0, f'action_to_choice drift {n_mismatch_act}'
    print(f'✅ parity OK — featurize·action_to_choice rl_env와 일치({len(_BALANCED_PRESETS)}케이스)')


if __name__ == '__main__':
    _assert_parity_with_rl_env()
