"""auto_improve_loop.py — 자가개선 루프 S2: Tier1 오케스트레이터 (빌드 제외 도구)

S1 약점 리포트(improve_report.py)를 읽고 **규칙기반으로 config 후보를 제안 →
학습 → 평가 → Δ 최고 채택/롤백**한다. plan 10-C 정본.

Tier1 = 엔진 코드 무수정, config(PPO 하이퍼파라미터)만 바꿈 → 완전 자동·되돌리기 쉬움.
규칙 제안기는 S3에서 로컬 LLM(Ollama)이 대체한다 — 지금은 LLM 없이 루프 배선·채택
로직을 검증한다.

  python auto_improve_loop.py [timesteps] [n_envs] [eval_seeds] [report.json]
  (기본 초소형 — 루프 메커니즘 검증용. 실제 스윕은 timesteps↑·백그라운드)

산출: _improve_loop_log.json (후보별 config·Δ·채택 여부) + 채택 모델 _rl_auto_best.zip
"""
import sys
import os
import json
import time

import numpy as np

from engine import normalize_enemy_db
from rl_env import make_env, _BALANCED_PRESETS
from improve_report import eval_baseline, eval_policy

normalize_enemy_db()


# ── Tier1 규칙 제안기 (S3에서 LLM이 대체) ──────────────────────────────────────
def propose_candidates(report):
    """S1 리포트 → config 후보 리스트. 규칙:
      · 기준선 = 현 최고 설정(ent_coef 0.01, shaping ON)
      · 지는 시나리오에 과수렴 플래그가 있으면 → 탐색 강화(ent_coef↑) 후보 추가
      · 과수렴 없으면 → 탐색 약화(ent_coef↓, 수렴 가속) 후보 추가
    각 후보에 '왜 제안했는지'(reason)를 달아 로그·후속 LLM 학습에 남긴다."""
    cands = [{'ent_coef': 0.01, 'lr': 3e-4, 'reason': '현 최고 기준선(5.5g)'}]
    over = []
    if report:
        over = [s['preset'] for s in report.get('scenarios', [])
                if s.get('overconverged_levers')]
    if over:
        cands.append({'ent_coef': 0.02, 'lr': 3e-4,
                      'reason': f'과수렴 시나리오 {over[:2]} → 탐색 강화(ent_coef 0.02)'})
    else:
        cands.append({'ent_coef': 0.005, 'lr': 3e-4,
                      'reason': '과수렴 없음 → 수렴 가속(ent_coef 0.005)'})
    return cands


# ── 학습 + 평가 ────────────────────────────────────────────────────────────────
def train_and_eval(cfg, baseline, timesteps, n_envs, eval_seeds):
    """후보 config로 PPO 학습 후 균형풀 평가 → 전체 평균 Δ(정책−baseline) 반환."""
    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import SubprocVecEnv
    venv = SubprocVecEnv([make_env(reward_shaping=True) for _ in range(n_envs)])
    model = PPO('MlpPolicy', venv, device='cpu', verbose=0, n_steps=256,
                ent_coef=cfg['ent_coef'], learning_rate=cfg['lr'])
    t0 = time.perf_counter()
    model.learn(total_timesteps=timesteps)
    dt = time.perf_counter() - t0
    venv.close()
    pol = eval_policy(model, eval_seeds)
    deltas = []
    for p in _BALANCED_PRESETS:
        pscore = float(np.mean([e['friendly_score'] for e in pol[p]]))
        deltas.append(pscore - baseline[p]['score'])
    return float(np.mean(deltas)), model, dt


def main(timesteps, n_envs, eval_seeds, report_path):
    report = None
    if os.path.exists(report_path):
        report = json.load(open(report_path, encoding='utf-8'))
        print(f'[S1 리포트] {report_path} — 최우선 {report["scenarios"][0]["preset"]}'
              f' (Δ{report["scenarios"][0]["delta"]:+.3f})', flush=True)
    else:
        print(f'[S1 리포트 없음] {report_path} — 기본 후보로 진행', flush=True)

    cands = propose_candidates(report)
    print(f'[제안] {len(cands)}개 후보:', flush=True)
    for c in cands:
        print(f"  ent_coef={c['ent_coef']} lr={c['lr']} — {c['reason']}", flush=True)

    print(f'[baseline] 균형 {len(_BALANCED_PRESETS)}시나리오 × {len(eval_seeds)}seed 평가...', flush=True)
    baseline = eval_baseline(eval_seeds)

    results = []
    for i, c in enumerate(cands, 1):
        print(f'\n[후보 {i}/{len(cands)}] 학습 {timesteps} 스텝 (ent_coef={c["ent_coef"]})...', flush=True)
        mean_delta, model, dt = train_and_eval(c, baseline, timesteps, n_envs, eval_seeds)
        print(f'  → Δ={mean_delta:+.3f}  (학습 {dt:.0f}s)', flush=True)
        results.append({'cfg': c, 'mean_delta': round(mean_delta, 3),
                        'train_s': round(dt, 1), '_model': model})

    # 채택 — Δ 최고. 단 기준선(첫 후보)보다 유의(>0.005) 높아야 교체, 아니면 기준선 유지.
    results.sort(key=lambda r: r['mean_delta'], reverse=True)
    best = results[0]
    base_cand = next(r for r in results if r['cfg'] is cands[0])
    adopt = best['cfg'] is cands[0] or (best['mean_delta'] - base_cand['mean_delta'] > 0.005)
    chosen = best if adopt else base_cand
    chosen['_model'].save('_rl_auto_best')
    print(f"\n[채택] ent_coef={chosen['cfg']['ent_coef']} (Δ{chosen['mean_delta']:+.3f})"
          f" — {'개선 채택' if adopt and chosen is not base_cand else '기준선 유지(유의 개선 없음)'}", flush=True)

    log = {'timesteps': timesteps, 'eval_seeds': list(eval_seeds),
           'candidates': [{'cfg': r['cfg'], 'mean_delta': r['mean_delta'],
                           'train_s': r['train_s']} for r in results],
           'adopted': {'cfg': chosen['cfg'], 'mean_delta': chosen['mean_delta']},
           'model': '_rl_auto_best.zip'}
    json.dump(log, open('_improve_loop_log.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=2)
    print('저장: _improve_loop_log.json · _rl_auto_best.zip', flush=True)


if __name__ == '__main__':
    ts = int(sys.argv[1]) if len(sys.argv) > 1 else 8_000      # 기본 초소형(메커니즘 검증)
    ne = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    es = range(1, (int(sys.argv[3]) if len(sys.argv) > 3 else 2) + 1)
    rp = sys.argv[4] if len(sys.argv) > 4 else '_improve_report.json'
    main(ts, ne, list(es), rp)
