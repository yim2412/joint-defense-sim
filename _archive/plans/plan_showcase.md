# 설계 — 실험적 기능 쇼케이스 탭 + ON/OFF 비교 뷰

## 목적
"토글 켰는데 변화 0" 최대 신뢰도 이슈([[project-user-feedback-backlog]] 1번) 직격.
각 실험적 기능마다 **효과가 극명히 드러나는 시나리오를 원클릭 로드** + **토글 ON vs OFF 나란히 비교**.

## 결정 (사용자 합의 2026-07-03)
- **배치**: 새 탭 `🎬 쇼케이스` (`_main_stack`에 index 2 페이지 신설, 홈/설정에서 진입 버튼)
- **비교 방식**: **하이브리드** — 카드엔 사전측정 baseline을 '예상 효과'로 즉시 표시 + `▶ 직접 비교 실행` 버튼으로 실제 ON/OFF MC 2회 돌려 델타 표시

## 수정 파일
- `app_main.py` 단독 (엔진·DB 무변경 → 회귀 자명 PASS)

## 핵심 변경
### 1. 쇼케이스 카드 데이터 — 모듈 상수 `_SHOWCASES: list[dict]`
각 항목:
```python
{
  'key': 'drone_swarm',
  'title': '적 무인기 군집 (자폭 드론 포화)',
  'desc': '무장 없는 드론이 다방위로 돌진 → 요격 채널·요격탄 포화',
  'toggle': 'enable_drone_swarm',       # ON/OFF 비교 대상
  'scenario': {                          # 로드 시 설정 세팅
      'fleet': '이지스 기동전단',
      'enemy_mode': '프리셋',
      'enemy_preset': '무인기 군집 포화',
      'weather': '맑음 (주간)',
      'extra_toggles': {'enable_multibearing': True},  # 시나리오 필수 병용 토글
  },
  'expected': '요격률 0.97 → 0.34 · 피격 0.05 → 1.38 (드론 80대)',  # baseline 즉시표시
  'metrics': ['intercept_rate', 'friendly_hits', 'friendly_ships_lost', 'cost'],
}
```
초기 카드 5종(baseline 측정 완료분): 무인기 군집·UUV 소해·ARM 역탐지·C-RAM 연안·DMO.

### 2. 새 페이지 `_build_showcase_page()` → `_main_stack.addWidget` (index 2)
- 상단: 제목 + "실험적 기능의 효과를 미리 정의된 시나리오로 확인" 안내
- 카드 그리드: 각 카드 = QGroupBox(제목·설명·예상효과 라벨·버튼 2개)
- `[시나리오 로드]`: 콤보/체크박스를 scenario대로 세팅 후 `_main_stack.setCurrentIndex(0)` (설정 화면으로)
- `[▶ 직접 비교 실행]`: 아래 워커 기동 → 결과를 카드 하단 라벨에 인라인 표시

### 3. 진입 동선
- 홈 화면 또는 설정 화면 상단에 `🎬 쇼케이스` 버튼 → `_main_stack.setCurrentIndex(2)`
- 쇼케이스 페이지에 `← 설정으로` 버튼

### 4. ON/OFF 비교 워커 `ShowcaseCompareWorker(QThread)`
- 입력: base_cfg(시나리오 반영), toggle_key, mc_n(기본 30~40)
- `cfg_off = {**base, toggle: False}`, `cfg_on = {**base, toggle: True}`
- `monte_carlo_v7(cfg_off, n)` → `monte_carlo_v7(cfg_on, n)` 순차
- finished(dict off, dict on) → 카드에 `요격률 OFF% → ON% (Δ)` 등 metrics 델타 표시
- 진행 중 카드 버튼 비활성 + "비교 중..." 표시. 중복 실행 방지(단일 워커).

## 하위호환·감사
- 순수 UI 추가. 기존 cfg 빌드·MC 경로·엔진 무변경 → **회귀 bit-identical 자명**.
- 신규 `enable_xxx` 없음(기존 토글 재사용) · 신규 `stats` 키 없음 → 3종세트·MC 3경로 plumbing 불요.
- 감사 유형 = **UI·시각화 변경** → 회귀 확인 + 빌드 성공 + 스모크(사용자/GUI 자동화).
- 정적 스캔 `audit_static_scan.py` 통과 · `NoScrollComboBox` 준수 · matplotlib 미사용(라벨 텍스트만이면 figure 누수 없음).

## 버전
- 트랙 C용 `v16.12.04`는 예약됨 → 쇼케이스는 **새 minor `v16.13.01`** (near-term 사용성 UI 묶음).

## 체크리스트 (패치 완료 시)
- [ ] app_main.py 헤더 + APP_VERSION → v16.13.01
- [ ] app_changelog.json 추가 (`추가  실험적 기능 쇼케이스 탭 — 원클릭 시나리오 + ON/OFF 효과 비교`)
- [ ] _changelog_export.py 재실행
- [ ] _PLANS 갱신 (해당 시) + 빌드
- [ ] README (새 도메인 아니라 불필요, 판단)
- [ ] 전체 빌드 + 스모크
- [ ] git push
