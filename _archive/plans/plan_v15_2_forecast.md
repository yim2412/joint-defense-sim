# v15.2 즉시예측 확장 — 학습 기반 대리모델(surrogate) 설계

**상태**: 설계 합의(2026-07-04, 사용자 '학습 대리모델 전체' 선택) → 구현
**난이도**: 높음. Opus. v18 캠페인 엔진의 선행 부품(임의 편성 교전을 즉시 추정).

## 0. 목표·현 한계
- 현: `forecast_surrogate.json` 룩업 = (프리셋 편대 × 프리셋 적) × **맑음 주간 1종**. 임의 편성 불가.
- 확장: **날씨 + 임의 편성 + 학습 회귀 추론**. v18은 손상·수리로 변하는 임의 함대의 교전 결과를 즉시 추정해야 함 → 룩업 불가, 특징 기반 회귀 필요.

## 1. 아키텍처
특징(함대·적·환경) → sklearn 회귀모델 → (승률·임무점수·비용) 즉시 예측. 알려진 프리셋 조합은 정확 룩업(json) 유지, 임의 편성은 모델 추론 = **하이브리드**.

## 2. 신규/변경 파일
| 파일 | 역할 | 빌드 |
|------|------|------|
| `forecast_features.py` (신규) | 특징화 함수 `featurize(fleet_ships, enemy_cfg, weather, region)` → np.ndarray. 빌더·GUI 공유 | **번들**(exe 추론) |
| `_forecast_build_surrogate.py` (재작성) | 표본 생성(프리셋+랜덤) → 전장 MC → 특징·타깃 → sklearn 학습 → `forecast_model.pkl` + 검증 리포트 | 제외(오프라인) |
| `forecast_model.pkl` (산출물) | 학습된 3타깃 회귀모델(joblib) | **번들**(spec datas) |
| `engine_combat.py` | `fleet_custom` cfg 지원(임의 함대) | 빌드 |
| `app_main.py` | 모델 로드·추론 연동, 카드에 정확도 표기 | 빌드 |

## 3. 엔진 변경 — `fleet_custom` (하위호환)
`_build_friendly`: `cfg.get('fleet_custom')`(list of {name,type})가 있으면 프리셋 대신 사용. 없으면 기존 프리셋 경로 → **회귀 bit-identical**. 적군은 기존 'random'/'custom' 모드 재사용.

## 4. 특징 벡터 (featurize)
- **함대**: 함급 tier별 수(이지스/구축/호위/소형/지원/잠수함/해안/무인), 총 교전채널, 총 SAM재고(SM-3/6/2·ESSM·해궁·RAM 합), BMD 보유(SM-3>0), 최대 대공센서, 총 HP, 미 함정 수(연합), 총 대함 타격재고.
- **적**: 총 위협수, 유형별 수(미사일/항공/수상/잠수), 초음속(≥600)·탄도·HGV 수, 총 살보, 최대 속도, 항모 유무.
- **환경**: 날씨 수치인자(WEATHER_DB 탐지·해상 factor — one-hot 대신 수치로 일반화), 해역·계절(경미, 선택).
- 고정: 전술 cfg는 기본값(카드가 기본 전술 기준 예측). 향후 전술 특징 확장 여지.

## 5. 타깃·모델
- 타깃 3: `win_rate`(0~1)·`mean_friendly_score`(0~1)·`mean_cost`(log 변환 후 회귀).
- 모델: `HistGradientBoostingRegressor` × 3(타깃별). joblib 저장.
- 검증(승격 게이트): 홀드아웃 R²·MAE. 프리셋 조합에서 예측 vs 실제 MC 비교. 카드에 근사 신뢰구간(±MAE) 표기.

## 6. 표본 생성
- **앵커**: 448 프리셋 조합 × 대표 날씨 4~5종(맑음주간/야간·폭풍우·안개·황사) ≈ 2200.
- **랜덤**: 랜덤 함대(fleet_custom: SHIP_DB에서 현실적 수 샘플) × 랜덤 적(random 모드 난이도·seed) × 랜덤 날씨/해역 ≈ 2000.
- 각 표본 전장 MC n=12. 8코어 병렬. 예상 ~30~60분(오프라인, 사용자 동의 완료).

## 7. GUI 추론
`_update_forecast_card`: 현재 UI(임의 편성 포함)를 featurize → model.predict → 즉시 카드. 프리셋 정확 조합은 json 룩업 우선(정확), 그 외 모델. 모델·pkl 없으면 기존 json 폴백 → 하위호환.

## 8. 구현 순서
1. `fleet_custom` 엔진 지원 + 회귀 PASS.
2. `forecast_features.py` 특징화(+단위검증).
3. `_forecast_build_surrogate.py` 재작성(표본생성+학습+검증 리포트).
4. 오프라인 학습 실행(백그라운드·동의 완료) → `forecast_model.pkl` + 검증.
5. GUI 추론 연동 + 카드 정확도 표기.
6. spec datas 번들 + 빌드 + 스모크 + 회귀 + 커밋.

## 9. 검증·리스크
- 회귀 bit-identical(fleet_custom 미사용 시).
- 모델 정확도 게이트: 홀드아웃 R² 합리적(≥0.7 목표)·프리셋 예측이 룩업과 근접. 미달 시 표본↑·특징↑.
- exe 번들: `forecast_model.pkl`·`forecast_features.py`·sklearn hiddenimports 확인(누락 시 추론 실패→json 폴백으로 graceful).
- 결정론: 학습은 오프라인(런타임 무관), 추론은 순수 함수(회귀 무관).
