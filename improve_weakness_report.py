"""improve_weakness_report.py — 자가개선 루프 S1: 약점 분석 리포트 (빌드 제외 도구)

학습된 RL 정책을 균형 6시나리오 × N seed로 평가하고, baseline 대비 *어디서·왜
지는지*를 숫자로 구조화한다. plan 10-C 정본. **LLM 불요** — 약점을 숫자로 정의하는
이 분석이 자가개선 루프에서 가장 중요·어려운 부품(LLM은 이 리포트를 읽고 제안할 뿐).

산출 지표:
  A. 최악 시나리오 랭킹     — Δ(정책−baseline) 최저
  B. 원인 귀속              — 최저 progress 목표 + 자원 소진율 + 누출률
  C. 과수렴 플래그          — 지는 시나리오의 레버 분포 엔트로피≈0 (5.5e 붕괴 검출)
  D. 레버-승패 상관         — 시나리오별 어떤 레버값이 승/패와 묶이나

사용:  python improve_weakness_report.py [model.zip] [seeds]
       기본 모델 = 최고 체크포인트(_rl_ckpt/ppo_shaped_ent0.01_1000000_steps.zip)
출력:  _improve_report.json (기계용) + 콘솔 사람용 요약
"""
import sys
import os
import glob
import json
import math
from collections import Counter, defaultdict

import numpy as np

from engine_core import normalize_enemy_db
from engine_combat import run_battle_simulation
from ai_rl_env import (BattleEnv, _BALANCED_PRESETS, _DEFAULT_CFG,
                    _WPN_PRIORITY, _SALVO_OPTS, _RADAR_OPTS, _TARGET_OPTS,
                    _MANEUVER_OPTS, _CAP_OPTS, _ECM_OPTS)

normalize_enemy_db()

# 레버 이름 ↔ 선택지 (히스토그램·엔트로피용)
_LEVERS = [
    ('weapon_priority', _WPN_PRIORITY), ('max_salvo', _SALVO_OPTS),
    ('radar', _RADAR_OPTS), ('target_priority', _TARGET_OPTS),
    ('maneuver', _MANEUVER_OPTS), ('cap_posture', _CAP_OPTS), ('ecm', _ECM_OPTS),
]


def _base_cfg(preset, seed):
    return dict(_DEFAULT_CFG, enemy_fleet_preset=preset, sim_seed=seed,
                enable_ship_evasion=True)


def _default_model_path():
    cands = sorted(glob.glob('_rl_ckpt/ppo_shaped_ent0.01_*_steps.zip'),
                   key=lambda f: int(''.join(filter(str.isdigit,
                                    os.path.basename(f).split('_steps')[0].split('_')[-1])) or 0))
    if cands:
        return cands[-1]
    for f in ('_rl_ppo_model_shaped.zip', '_rl_ppo_model_shaped_ent0.01.zip'):
        if os.path.exists(f):
            return f
    return None


def _shannon_entropy(counts):
    """선택 분포의 정규화 섀넌 엔트로피 [0,1]. 0=한 값에 과수렴, 1=균등."""
    total = sum(counts.values())
    if total == 0 or len(counts) <= 1:
        return 0.0
    h = -sum((c / total) * math.log(c / total) for c in counts.values() if c)
    return h / math.log(len(counts))


def _friendly_objectives(result):
    """result['objectives']에서 아군 목표 {type: progress} 추출."""
    return {ob.get('type'): ob.get('progress')
            for ob in result.get('objectives', [])
            if ob.get('side') == 'friendly' and ob.get('progress') is not None}


def eval_baseline(seeds):
    """전부 기본값 고정 정책 — run_battle_simulation 직접(full result).
    점수뿐 아니라 목표별 progress도 평균해 정책과의 목표 Δ 비교에 쓴다."""
    cb = lambda s: {'weapon_priority': 'auto', 'max_salvo': 2, 'radar': 'on',
                    'target_priority': 'auto', 'maneuver': 'normal',
                    'cap_posture': 'normal', 'ecm': 'normal'}
    out = {}
    for p in _BALANCED_PRESETS:
        scores, obj_acc = [], defaultdict(list)
        for s in seeds:
            r = run_battle_simulation(_base_cfg(p, s), tactical_cb=cb)
            scores.append(r.get('friendly_score', 0.0))
            for k, v in _friendly_objectives(r).items():
                obj_acc[k].append(v)
        out[p] = {'score': float(np.mean(scores)),
                  'objectives': {k: float(np.mean(v)) for k, v in obj_acc.items()}}
    return out


def eval_policy(model, seeds):
    """학습 정책 — 에피소드별 full 분해(info 보강) + 레버 선택 히스토그램 포착."""
    from ai_rl_env import BattleEnv  # 지연 import (SB3 의존 격리)
    per_preset = {}
    for p in _BALANCED_PRESETS:
        eps = []
        for seed in seeds:
            env = BattleEnv(_base_cfg(p, seed))
            obs, _ = env.reset(seed=seed)
            done = False
            info = {}
            lever_hist = {name: Counter() for name, _ in _LEVERS}
            while not done:
                a, _ = model.predict(obs, deterministic=True)
                choice = BattleEnv._action_to_choice(a)
                for name, _opts in _LEVERS:
                    lever_hist[name][choice[name]] += 1
                obs, r, term, trunc, info = env.step(a)
                done = term or trunc
            env.close()
            eps.append({
                'seed': seed,
                'friendly_score': float(info.get('friendly_score', 0.0)),
                'outcome': info.get('outcome'),
                'objectives': info.get('objectives', {}),
                'ammo_frac': float(info.get('ammo_frac', 1.0)),
                'fuel_frac': float(info.get('fuel_frac', 1.0)),
                'leaker_frac': float(info.get('leaker_frac', 0.0)),
                'intercept_rate': float(info.get('intercept_rate', 0.0)),
                'levers': {n: dict(c) for n, c in lever_hist.items()},
            })
        per_preset[p] = eps
    return per_preset


def build_report(model_path, seeds):
    from stable_baselines3 import PPO
    print(f'[1/3] baseline 평가 ({len(_BALANCED_PRESETS)}시나리오 × {len(seeds)}seed)...', flush=True)
    base = eval_baseline(seeds)
    print(f'[2/3] 정책 평가: {os.path.basename(model_path)} ...', flush=True)
    model = PPO.load(model_path, device='cpu')
    pol = eval_policy(model, seeds)

    print('[3/3] 약점 지표 산출...', flush=True)
    scenarios = []
    for p in _BALANCED_PRESETS:
        eps = pol[p]
        pscore = float(np.mean([e['friendly_score'] for e in eps]))
        bscore = base[p]['score']
        base_obj = base[p]['objectives']
        delta = pscore - bscore
        # B. 원인 귀속 — 목표별 평균 progress + baseline 대비 Δ
        obj_acc = defaultdict(list)
        for e in eps:
            for k, v in (e['objectives'] or {}).items():
                if v is not None:
                    obj_acc[k].append(v)
        obj_mean = {k: round(float(np.mean(v)), 3) for k, v in obj_acc.items()}
        # 절대 최저 목표(구조적으로 늘 낮은 sea_control 등 포함)
        worst_obj = min(obj_mean, key=obj_mean.get) if obj_mean else None
        # 정책 Δ 최저 목표 — 정책이 baseline 대비 *특히 더 못하는* 목표(정책 특유 약점)
        obj_delta = {k: round(obj_mean[k] - base_obj.get(k, obj_mean[k]), 3)
                     for k in obj_mean}
        worst_obj_delta = min(obj_delta, key=obj_delta.get) if obj_delta else None
        ammo_exhaust = float(np.mean([1.0 if e['ammo_frac'] < 0.05 else 0.0 for e in eps]))
        fuel_exhaust = float(np.mean([1.0 if e['fuel_frac'] < 0.05 else 0.0 for e in eps]))
        leaker = float(np.mean([e['leaker_frac'] for e in eps]))
        # C. 과수렴 — 레버별 선택 엔트로피(시나리오 통합)
        merged = {name: Counter() for name, _ in _LEVERS}
        for e in eps:
            for name, c in e['levers'].items():
                merged[name].update(c)
        lever_entropy = {name: round(_shannon_entropy(c), 3) for name, c in merged.items()}
        lever_mode = {name: (c.most_common(1)[0][0] if c else None) for name, c in merged.items()}
        outcomes = Counter(e['outcome'] for e in eps)
        losing = (pscore < 0.4) or (outcomes.get('loss', 0) >= outcomes.get('win', 0))
        # 과수렴 플래그: 지는 시나리오인데 레버가 한 값에 박힘(엔트로피<0.2)
        overconverged = [n for n, h in lever_entropy.items() if losing and h < 0.2]
        scenarios.append({
            'preset': p,
            'policy_score': round(pscore, 3), 'baseline_score': round(bscore, 3),
            'delta': round(delta, 3),
            'outcomes': dict(outcomes),
            'objective_mean': obj_mean, 'worst_objective': worst_obj,
            'objective_delta': obj_delta, 'worst_objective_delta': worst_obj_delta,
            'ammo_exhaust_rate': round(ammo_exhaust, 2),
            'fuel_exhaust_rate': round(fuel_exhaust, 2),
            'leaker_frac': round(leaker, 3),
            'lever_entropy': lever_entropy, 'lever_mode': lever_mode,
            'overconverged_levers': overconverged,
        })

    scenarios.sort(key=lambda s: s['delta'])   # A. 최악(Δ 최저) 먼저
    report = {
        'model': os.path.basename(model_path),
        'seeds': list(seeds),
        'mean_delta': round(float(np.mean([s['delta'] for s in scenarios])), 3),
        'scenarios': scenarios,
    }
    return report


def print_summary(rep):
    print('\n' + '=' * 70)
    print(f"약점 분석 리포트 — {rep['model']}  (seed {rep['seeds']})")
    print(f"전체 평균 Δ(정책−baseline) = {rep['mean_delta']:+.3f}")
    print('=' * 70)
    print(f"{'시나리오':<18}{'Δ':>7}{'정책':>7}{'base':>7}  약점목표 / 자원·누출 / 과수렴")
    for s in rep['scenarios']:
        cause = []
        wod = s.get('worst_objective_delta')
        if wod and s['objective_delta'].get(wod, 0) < -0.01:
            # 정책이 baseline 대비 특히 더 못하는 목표(정책 특유 약점)
            cause.append(f"{wod}Δ{s['objective_delta'][wod]:+.2f}")
        elif s['worst_objective']:
            wo = s['worst_objective']
            cause.append(f"{wo}={s['objective_mean'].get(wo)}(구조적)")
        if s['ammo_exhaust_rate'] > 0:
            cause.append(f"탄약소진 {s['ammo_exhaust_rate']:.0%}")
        if s['fuel_exhaust_rate'] > 0:
            cause.append(f"연료소진 {s['fuel_exhaust_rate']:.0%}")
        if s['leaker_frac'] > 0.3:
            cause.append(f"누출 {s['leaker_frac']:.0%}")
        if s['overconverged_levers']:
            cause.append(f"⚠과수렴[{','.join(s['overconverged_levers'])}]")
        print(f"  {s['preset'][:16]:<16}{s['delta']:>+7.3f}{s['policy_score']:>7.3f}"
              f"{s['baseline_score']:>7.3f}  {' · '.join(cause)}")
    print('-' * 70)
    worst = rep['scenarios'][0]
    wod = worst.get('worst_objective_delta')
    print(f"최우선 개선 대상: {worst['preset']} (Δ{worst['delta']:+.3f})"
          f" — 정책 특유 약점목표 {wod}(Δ{worst['objective_delta'].get(wod, 0):+.3f})"
          + (f", 과수렴 {worst['overconverged_levers']}" if worst['overconverged_levers'] else ''))


def main():
    model_path = sys.argv[1] if len(sys.argv) > 1 else _default_model_path()
    seeds = range(1, int(sys.argv[2]) + 1) if len(sys.argv) > 2 else range(1, 9)
    if not model_path or not os.path.exists(model_path):
        print('학습된 모델을 찾을 수 없음. 사용: python improve_weakness_report.py [model.zip] [seeds]')
        print('  (먼저 _ai_rl_train_eval.py로 학습하거나 _rl_ckpt/의 체크포인트 필요)')
        sys.exit(2)
    rep = build_report(model_path, list(seeds))
    with open('_improve_report.json', 'w', encoding='utf-8') as f:
        json.dump(rep, f, ensure_ascii=False, indent=2)
    print_summary(rep)
    print('\n저장: _improve_report.json')


if __name__ == '__main__':
    main()
