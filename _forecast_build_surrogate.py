# -*- coding: utf-8 -*-
"""
v15.2 즉시예측 대리모델 빌더 (빌드 제외 도구).

프리셋 앵커 + 랜덤 임의 편성 표본을 전장 MC로 돌려 (특징, 승률·임무점수·비용)을 모으고
sklearn 회귀모델 3종을 학습해 forecast_model.pkl(joblib)로 저장한다. GUI는 이 모델로
임의 편성·날씨의 예상 결과를 즉시 추론(전장 MC 없이). 프리셋 정확 룩업 json도 함께 갱신.

사용: python _forecast_build_surrogate.py            (전체: 앵커+랜덤 학습)
      python _forecast_build_surrogate.py --smoke    (소규모 스모크)
"""
import sys
import time
import json
import random
from concurrent.futures import ProcessPoolExecutor

import numpy as np

from engine_combat import monte_carlo_v7, FLEET_PRESETS
from engine_core import ENEMY_FLEET_PRESETS, WEATHER_DB, generate_random_enemy_fleet
from forecast_features import featurize, FEATURE_NAMES

N_MC        = 10
N_RANDOM    = 1600         # 랜덤 임의 편성 표본 수
MODEL_OUT   = 'forecast_model.pkl'
JSON_OUT    = 'forecast_surrogate.json'   # 프리셋 정확 룩업(맑음 주간)

# 랜덤 함대 샘플 풀 (가중치 — 전투함 위주, 지원·소형·잠수·해안·무인 소수)
_FLEET_POOL = (
    ['KDX-III-B2', 'KDX-III-B1', 'DDG-51', 'CG-47'] * 4 +
    ['KDX-II'] * 5 +
    ['FFX-I', 'FFX-II', 'FFX-III'] * 4 +
    ['PKG', 'PCC', 'PKX-B'] * 2 +
    ['LPH', 'AOE', 'AO', 'LST', 'LPD', 'CVN'] * 1 +
    ['KSS-I', 'KSS-II', 'KSS-III', 'SSN'] * 1 +
    ['CRAM', 'CSAM'] * 1 + ['USV', 'UUV'] * 1
)


def _anchor_weathers() -> list:
    """맑음 주간 + 탐지영향 극단 2종(가장 낮은·중간 detect_range_factor)."""
    ws = sorted(WEATHER_DB.keys(),
                key=lambda w: WEATHER_DB[w].get('detect_range_factor', 1.0))
    picks = ['맑음 (주간)']
    for w in (ws[0], ws[len(ws) // 2]):   # 최악 탐지 + 중간
        if w not in picks:
            picks.append(w)
    return picks


def _random_fleet() -> list:
    k = random.randint(1, 8)
    return [{'name': f'R{i}', 'type': random.choice(_FLEET_POOL)} for i in range(k)]


def eval_sample(args):
    """표본 1개: 전장 MC → (특징벡터 list, [win, score, cost], 룩업레코드|None)."""
    kind, fleet_ships, enemy_list, weather, cfg = args
    mc = monte_carlo_v7(dict(cfg), n=N_MC)
    costs = mc.get('total_costs', []) or [0.0]
    mean_cost = sum(costs) / len(costs)
    win   = float(mc.get('win_rate', 0.0))
    score = float(mc.get('mean_friendly_score', 0.0))
    feat  = featurize(fleet_ships, enemy_fleet=enemy_list, weather=weather).tolist()
    rec = None
    if kind == 'anchor_clear':
        rec = (cfg['fleet_preset'], cfg['enemy_fleet_preset'], {
            'win_rate': round(win, 4), 'draw_rate': round(mc.get('draw_rate', 0.0), 4),
            'loss_rate': round(mc.get('loss_rate', 0.0), 4),
            'mean_friendly_score': round(score, 4), 'mean_cost': round(mean_cost, 1),
            'cost_per_win': round(mean_cost / win, 1) if win > 0 else None, 'n': N_MC})
    return (feat, [win, score, mean_cost], rec)


def build_samples(smoke=False):
    samples = []
    anchor_wx = _anchor_weathers()
    fleets  = list(FLEET_PRESETS.keys())
    enemies = list(ENEMY_FLEET_PRESETS.keys())
    if smoke:
        fleets, enemies, anchor_wx = fleets[:2], enemies[:2], anchor_wx[:1]
    for fn in fleets:
        fleet_ships = [s['type'] for s in FLEET_PRESETS[fn]]
        for en in enemies:
            enemy_list = ENEMY_FLEET_PRESETS[en]
            for wx in anchor_wx:
                kind = 'anchor_clear' if wx == '맑음 (주간)' else 'anchor'
                cfg = {'enemy_fleet_mode': 'preset', 'enemy_fleet_preset': en,
                       'fleet_preset': fn, 'weather': wx, 'enable_battle_mode': True}
                samples.append((kind, fleet_ships, enemy_list, wx, cfg))
    n_rand = 6 if smoke else N_RANDOM
    all_wx = list(WEATHER_DB.keys())
    for i in range(n_rand):
        fleet_custom = _random_fleet()
        fleet_ships  = [s['type'] for s in fleet_custom]
        enemy_list   = generate_random_enemy_fleet(
            difficulty=random.choice(['쉬움', '보통', '어려움', '매우 어려움']), seed=1000 + i)
        wx = random.choice(all_wx)
        cfg = {'enemy_fleet_mode': 'custom', 'enemy_fleet': enemy_list,
               'fleet_custom': fleet_custom, 'weather': wx, 'enable_battle_mode': True}
        samples.append(('random', fleet_ships, enemy_list, wx, cfg))
    return samples


def main(smoke=False):
    from sklearn.ensemble import HistGradientBoostingRegressor
    from sklearn.model_selection import train_test_split
    from sklearn.metrics import r2_score, mean_absolute_error
    import joblib

    random.seed(42)
    samples = build_samples(smoke)
    total = len(samples)
    print(f'표본 {total}개 (앵커+랜덤), n={N_MC}, 특징 {len(FEATURE_NAMES)}차원')
    t0 = time.time()

    X, Y, table = [], [], {}
    done = 0
    with ProcessPoolExecutor() as ex:
        for feat, targ, rec in ex.map(eval_sample, samples):
            X.append(feat); Y.append(targ)
            if rec is not None:
                table[f'{rec[0]}|{rec[1]}'] = rec[2]
            done += 1
            if done % 50 == 0 or done == total:
                el = time.time() - t0
                eta = el / done * (total - done)
                print(f'  {done}/{total}  경과 {el:.0f}s  ETA {eta:.0f}s', flush=True)

    X = np.array(X); Y = np.array(Y)
    Y_t = np.column_stack([Y[:, 0], Y[:, 1], np.log1p(Y[:, 2])])   # cost는 log1p

    Xtr, Xte, Ytr, Yte = train_test_split(X, Y_t, test_size=0.2, random_state=0)
    models, report = [], []
    tgt_names = ['win_rate', 'friendly_score', 'log_cost']
    for j, tn in enumerate(tgt_names):
        m = HistGradientBoostingRegressor(max_iter=400, learning_rate=0.06,
                                          max_depth=6, l2_regularization=0.1,
                                          random_state=0)
        m.fit(Xtr, Ytr[:, j])
        pred = m.predict(Xte)
        r2  = r2_score(Yte[:, j], pred)
        mae = mean_absolute_error(Yte[:, j], pred)
        report.append((tn, round(float(r2), 4), round(float(mae), 5)))
        models.append(m)
        print(f'  [{tn:14s}] R²={r2:.3f}  MAE={mae:.4f}')

    joblib.dump({'models': models, 'feature_names': FEATURE_NAMES,
                 'targets': tgt_names, 'report': report, 'n_samples': total,
                 'cost_is_log1p': True}, MODEL_OUT)
    with open(JSON_OUT, 'w', encoding='utf-8') as f:
        json.dump({'weather': '맑음 (주간)', 'n': N_MC, 'table': table}, f,
                  ensure_ascii=False, indent=1)
    print(f'\n저장: {MODEL_OUT} (모델 3종) + {JSON_OUT} (룩업 {len(table)}조합)')
    print(f'총 소요 {time.time() - t0:.0f}s')


if __name__ == '__main__':
    main(smoke='--smoke' in sys.argv)
