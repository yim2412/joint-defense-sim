"""
지속 전장 모드 surrogate 룩업 테이블 빌더 (빌드 제외 도구).

(편대 × 적 편대 × 날씨) 프리셋 조합을 전장 MC로 미리 돌려 결과를 forecast_surrogate.json에
저장한다. GUI는 이 테이블을 조회해 "실행 전 예상 결과"를 즉시 표시(전장 MC ~45배 느림 회피).
조합 단위로 ProcessPoolExecutor 병렬. monte_carlo_v7는 내부 직렬이라 중첩 풀 없음.

사용: python _forecast_build_surrogate.py          (전체 수집)
      python _forecast_build_surrogate.py --smoke  (2조합 스모크)
"""
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor

from engine_combat import monte_carlo_v7, FLEET_PRESETS
from engine_core import ENEMY_FLEET_PRESETS

N_MC    = 15
WEATHER = '맑음 (주간)'
OUT     = 'forecast_surrogate.json'


def eval_combo(args):
    """조합 1개 전장 MC → 집계 dict (top-level: pickle 안전)."""
    fleet, enemy = args
    cfg = {'enemy_fleet_mode': 'preset', 'enemy_fleet_preset': enemy,
           'fleet_preset': fleet, 'weather': WEATHER, 'enable_battle_mode': True}
    mc = monte_carlo_v7(dict(cfg), n=N_MC)
    costs = mc.get('total_costs', []) or [0]
    mean_cost = sum(costs) / len(costs)
    wr = mc.get('win_rate', 0.0)
    return (fleet, enemy, {
        'win_rate':            round(wr, 4),
        'draw_rate':           round(mc.get('draw_rate', 0.0), 4),
        'loss_rate':           round(mc.get('loss_rate', 0.0), 4),
        'mean_friendly_score': round(mc.get('mean_friendly_score', 0.0), 4),
        'mean_cost':           round(mean_cost, 1),
        'cost_per_win':        round(mean_cost / wr, 1) if wr > 0 else None,
        'n':                   N_MC,
    })


def main(smoke=False):
    fleets  = list(FLEET_PRESETS.keys())
    enemies = list(ENEMY_FLEET_PRESETS.keys())
    combos  = [(f, e) for f in fleets for e in enemies]
    if smoke:
        combos = combos[:2]
    total = len(combos)
    print(f'조합 {total}개 (편대 {len(fleets)} × 적 {len(enemies)}), n={N_MC}, 날씨={WEATHER}')
    t0 = time.time()
    table = {}
    done = 0
    with ProcessPoolExecutor() as ex:
        for fleet, enemy, rec in ex.map(eval_combo, combos):
            table[f'{fleet}|{enemy}'] = rec
            done += 1
            if done % 10 == 0 or done == total:
                el = time.time() - t0
                eta = el / done * (total - done)
                print(f'  {done}/{total}  ({el:.0f}s 경과, ETA {eta:.0f}s)', flush=True)
    payload = {'weather': WEATHER, 'n': N_MC, 'fleets': fleets,
               'enemies': enemies, 'table': table}
    out = OUT if not smoke else '_battle_surrogate_smoke.json'
    json.dump(payload, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(f'저장: {out}  ({len(table)}조합, {time.time()-t0:.0f}s)')


if __name__ == '__main__':
    main(smoke='--smoke' in sys.argv)
