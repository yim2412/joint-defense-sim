# v15.1 적정 편대 추천 — 설계 (정본)

> 2026-06-13 설계 합의. 21번 탭 "최적 무기 조합 추천" → "적정 편대 추천"으로 **교체**(병행 아님).
> 무기 그리드 서치는 실용성 낮음(VLS 무장 고정) → 지휘관이 실제 고르는 단위인 편대 프리셋 추천으로 격상.

## 결정 사항 (사용자 합의)

1. **후보 분리**: 한국 단독 그룹 / 한미 연합 그룹 → 각 그룹 안에서 독립 순위.
2. **두 순위 병기**: 성능 순위 + 비용효과 순위 둘 다 표시.
3. **함정 조달가**: `SHIP_DB`에 공개 조달가 추가(별도 dict `SHIP_PROCUREMENT_USD`).
4. **성능 점수 가중**: 요격률 60% + 함정 생존율 40% (생존이 최종 결과라 비중 ↑).

## 구현

### 1. engine.py — `SHIP_PROCUREMENT_USD`
함정 type별 공개 조달가(USD). `SHIP_SURVIVABILITY` 바로 아래 위치. 출처 주석(공개 조달가, 환율 1350원/달러 환산).
편대 조달비용 = Σ(함정 조달가) + Σ(탑재 무기 재고비, default_inventory × cost_usd, CIWS 9999 제외).

### 2. engine_v7.py
- `_FLEET_CANDIDATES_KR` / `_FLEET_CANDIDATES_COMBINED`: FLEET_PRESETS 키를 두 그룹으로 분류.
- `fleet_procurement_cost(preset_name)`: 편대 조달비용 계산 유틸.
- `_fleet_metrics_worker(args)`: (preset_name, cfg, n) → MC로 요격률·생존율 산출. 생존율 = MC 평균 (생존 함정 / 전체 함정) 또는 무손실 비율. run_v7_simulation 반환 dict의 함정 손실 키 확인 후 확정.
- `recommend_fleet_v7(cfg, candidates, coarse_n, fine_n, top_k, map_fn)`: optimize 2단계 패턴 재사용.
  - 반환: `[{'preset', 'rate', 'std', 'survival', 'fleet_cost', 'perf_score', 'cost_eff', 'reason'}, ...]`
  - perf_score = rate*0.6 + survival*0.4. cost_eff = perf_score / (fleet_cost 정규화).
- `_fleet_reason(cfg, preset_name)`: 위협 구성(대잠/포화/탄도 비중) ↔ 편대 특성(대잠 헬기·채널 수·이지스 수·잠수함) 룰로 "왜 이 편대" 동적 생성.

### 3. launcher.py
- `OptimizeWorker` → `FleetRecommendWorker` (한국·한미 두 그룹 순차 실행, map_fn=_pool_map).
- `_render_optimize_chart` → `_render_fleet_chart`: 그룹별 표 형식(편대명·요격률·생존율·조달비용·성능순위·가성비순위·추천이유).
- 탭 제목 "🔧 최적 무기 조합 추천" → "⚓ 적정 편대 추천". lazy-start 흐름 동일.
- `_lazy_start_optimize` 등 핸들러 명칭 정리.

### 4. 마무리
- 시나리오 정적 `recommend` 텍스트(launcher.py:5215~)는 이번엔 건드리지 않음(별도 후속).
- 헤더·APP_VERSION·changelog·_PLANS 갱신. 회귀 검증(엔진 추가지만 기존 경로 불변→PASS 기대). 빌드·스모크·커밋·푸시.

## 주의
- 전역 DB 직접 수정 금지 → cfg 복사 패턴(HeatmapWorker가 cfg['fleet_preset']=fp 쓰는 패턴 재사용).
- 생존율 산출은 run_v7_simulation 실제 반환 키 확인 후 확정(침수 모델 enable_flooding 경로).
