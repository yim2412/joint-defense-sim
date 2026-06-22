# 세부 계획 — surrogate 기반 "실행 전 예상 전황" GUI 연동

> 범위: surrogate 룩업 테이블(`battle_surrogate.json`) 생성 → launcher 실행 전 프리뷰 패널에 예상 승률/비용 표시.
> 향후계획 **v15.2 "학습 기반 즉시 예측"의 1차 구현**(MC 없이 미리 계산한 테이블 조회).
> 코드는 아직 안 짬 — 본 문서는 설계만. 난이도: 중간.

---

## 0. 현재 상태

- `_build_surrogate.py` 작성 완료(untracked, 미커밋). 빌더만 있고 **산출물 JSON 없음 / GUI 연동 0**.
- 끊긴 지점 = 빌더를 백그라운드로 돌려 JSON 생성하던 중. (이번엔 동의 후에만 실행)

## 1. surrogate JSON 스키마 (`_build_surrogate.py` 확정분)

```
{
  "weather": "맑음 (주간)",          # 단일 날씨만 수집 (현 빌더 한계)
  "n": 15,                           # 조합당 전장 MC 횟수
  "fleets":  [...15개...],
  "enemies": [...23개...],
  "table": {
    "<편대>|<적편대>": {
      "win_rate", "draw_rate", "loss_rate",
      "mean_friendly_score", "mean_cost",
      "cost_per_win",        # 승률 0이면 null
      "n"
    }, ...345개
  }
}
```
키 = `f'{fleet}|{enemy}'`.

## 2. 작업 단계

### A. 빌더 검증 (코드 변경 없음)
1. `python _build_surrogate.py --smoke` (2조합, 수초) — 정상 동작·스키마 확인.
2. **동의 후** 전체 빌드(`python _build_surrogate.py`, 예상 2~5분, 동의 필요) → `battle_surrogate.json` 생성.
3. JSON 무결성 확인(345키, null 처리 등).

### B. GUI 연동 (launcher.py)
연동 지점은 **이미 있는 실행 전 프리뷰 패널**:
- `_build_scenario_preview()` (launcher.py:6949) — 우측 카드 3종(편대/환경/무장).
- `_update_scenario_preview()` (:7026) — 현재 설정으로 카드 갱신.

작업:
1. **로더**: 앱 시작 시 `battle_surrogate.json` 1회 로드(없으면 `None`, 기능 비활성). 경로는 exe(_MEIPASS)/개발 양쪽 대응 — 기존 `_token_path` 패턴 참고.
2. **새 카드 1장 추가**: `_build_scenario_preview`에 `_prev_lbl_forecast`("📊 예상 전황") 카드 추가(`_make_prev_card` 재사용).
3. **갱신 로직**: `_update_scenario_preview` 끝에 surrogate 조회 추가.
   - 현재 선택값: 아군=`cmb_fleet`, 적=`cmb_fleet_preset_e`(프리셋 모드 한정), 모드=`cmb_enemy_mode`, 날씨=`cmb_weather`.
   - **조회 가능 조건**: 적 편대 모드 == '프리셋' AND 키 `f'{fleet}|{enemy}'` 존재.
   - 표시: `예상 승률 NN% · 무승부 NN% · 패배 NN% / 평균 비용 $X.XM / 승리당 $Y.YM`.
4. **fallback 문구**(조회 불가 시):
   - 랜덤/혼합 모드 → "프리셋 대전 시 예상 전황 표시".
   - 날씨 ≠ '맑음 (주간)' → "맑음(주간) 기준 근사값" 주석 병기(테이블이 단일 날씨라 명시).
   - JSON 없음 → 카드 자체 숨김(하위호환, 기존 동작 보존).
5. 갱신 트리거: 콤보 변경 시 `_update_scenario_preview`가 이미 호출되는지 확인 → 적 편대 콤보에도 연결 누락 시 추가.

### C. 빌드·배포
1. `launcher.spec` `datas`에 `('battle_surrogate.json', '.')` 추가.
2. 전체 빌드(`.py` 변경이므로) → exe 스모크: 프리뷰에 예상 전황 카드 표시 확인.

### D. 캐시 무효화 / 신선도 (중요)
surrogate는 **엔진·DB가 바뀌면 stale**. 자동 재생성은 비싸므로:
- JSON에 메타(`engine_ver`/생성일) 기록 → 로드 시 현재 버전과 불일치면 카드에 "⚠ 예상치(구버전 기준)" 표기.
- 재생성은 수동(`_build_surrogate.py` 재실행) — 빌더 헤더에 "엔진/DB 변경 시 재빌드" 주석.
- (선택) `regression_golden.json`처럼 repo 커밋 여부 결정 필요 → §5 미결정.

## 3. 주의 / 하위호환

- JSON 없거나 깨져도 **앱 정상 동작**(카드만 숨김). 기능 OFF가 기본 안전망.
- 프리뷰는 **순수 표시** — 엔진/시뮬/회귀에 영향 0. 회귀 검증 불필요(엔진 미변경), 빌드+스모크만.
- 적 편대 변수 확인됨: `cmb_fleet_preset_e.currentText()`(launcher.py:7771). 아군=`cmb_fleet`.
- `_PLANS`에서 v15.2 항목 상태 갱신(완료 아님 — 1차 구현 표기) + changelog 1건.

## 4. 산출 버전 (예상)

- v15.13.05  실행 전 예상 전황 카드(surrogate 룩업 조회) 추가
  (단일 변경이면 1건. 빌더 커밋 포함 시 .05/.06 분리 가능.)

## 5. 미결정 사항 (착수 전 합의 필요)

1. **`battle_surrogate.json`을 repo에 커밋?** (생성 비용 vs 용량 — 345키 JSON 소형이라 커밋 권장).
2. **날씨 차원**: 지금은 '맑음(주간)' 단일. 다른 날씨도 근사 표시만 할지 / 빌더를 날씨별로 확장할지(조합 ×N배 시간↑).
3. **표시 톤**: "예상"임을 어디까지 강조할지(MC 15회 기반이라 신뢰구간 없음 — 참고치 명시).
