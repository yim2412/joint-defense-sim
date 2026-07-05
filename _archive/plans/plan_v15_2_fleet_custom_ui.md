# v16.14.02 — 아군 임의 편성 UI (v15.2 로드맵: 임의 편성 UI 확장)

## 1. 목표
아군 함대를 프리셋 외에 **직접 편성**할 수 있는 GUI를 추가한다.
엔진(`engine_combat.py:1548 _build_friendly`)은 이미 `cfg['fleet_custom']`(list of `{name,type}`)을
우선 소비하도록 구현·회귀 검증 완료(v15.2 ①단계). **이번 작업은 순수 GUI + 배선.**
방금 만든 학습 대리모델이 자유편성도 즉시 추정하도록 예상전황 카드도 소폭 확장한다.

## 2. 수정 파일
- `app_main.py` — 유일. 다이얼로그 클래스 + 진입 버튼 + cfg 빌드/복원 + 예상전황 확장.
- `engine_combat.py` / `engine_core.py` — **무변경**(엔진 이미 지원).

## 3. UI — 편성 다이얼로그 (B안 확정)
아군 편대 셀(`app_main.py:6511`, 프리셋 버튼 그리드) **아래**에 `[ ✏️ 직접 편성… ]` 버튼 추가.

### 3-1. 다이얼로그 (`FleetCustomDialog(QDialog)`, 신규 클래스)
- **함정 추가 행**: `NoScrollComboBox`(SHIP_DB `display` 표기) + `[+ 담기]` 버튼.
- **현재 편성 리스트**: 함정별 행 = `display명` + 척수 `[− N +]` 스피너 + 삭제. 내부는 `{type: count}` dict로 관리.
- **하단**: `[취소]` / `[확정]`. 확정 시 `{type:count}` → `fleet_custom` 리스트로 펼침
  (`name`은 SHIP_DB `display`, 2척 이상이면 `"정조대왕급 #1/#2"` 식 번호 부여 — 엔진은 name을 표시용으로만 사용).
- **검증**: 편성 0척이면 `[확정]` 비활성. 최소 1척 강제.
- 상단 import에 `QDialog`, `QSpinBox`(또는 `± 버튼`) 누락 여부 확인 → **누락 시 추가**(체크리스트 8: exe NameError 방지).

### 3-2. 상태 보관·표시
- `self._fleet_custom`(dict `{type:count}` 또는 None) — 다이얼로그 확정 결과 보관.
- 프리셋 버튼을 다시 누르면 `self._fleet_custom = None`(프리셋 모드 복귀).
- 아군 편대 레이블/버튼에 `직접 편성 (N척)` 표시(활성 상태 가시화).

## 4. cfg 빌드 (`_build_cfg_from_ui`, `app_main.py:8837`)
```python
if getattr(self, '_fleet_custom', None):
    cfg['fleet_custom'] = _expand_custom(self._fleet_custom)  # [{name,type}, ...]
    cfg['fleet_preset'] = '(직접 편성)'   # 표시·기록용
else:
    cfg['fleet_preset'] = self.cmb_fleet.currentText()   # 기존 경로 (fleet_custom 키 없음)
```
- **무기 재고**: 기존 전역 재고 위젯 그대로 공유(엔진이 각 함정 채움). 함정별 개별 재고는 범위 밖.
- `_run_sim`·쇼케이스 비교가 이 함수 공유 → 자동 반영.

## 5. cfg 복원 (`_restore_cfg`, `app_main.py:6305`)
```python
custom = cfg.get('fleet_custom')
if custom:
    self._fleet_custom = _collapse_custom(custom)   # [{name,type}] → {type:count}
    # 레이블 '직접 편성 (N척)' 갱신
else:
    self._fleet_custom = None
    # 기존 프리셋 복원 경로 (현행 유지)
```

## 6. 예상전황 카드 연동 (`_forecast_predict`, `app_main.py:8765`)
현재 `fleet_ships = [s['type'] for s in V7_FLEET_PRESETS.get(fleet, [])]`.
→ 직접 편성 시 `self._fleet_custom`을 type 리스트로 펼쳐 넘김.
`_update_forecast_card`(`:8723`)는 프리셋 문자열 키(`f'{fleet}|{enemy}'`)로 룩업하는데,
직접 편성은 룩업 테이블에 없으므로 **자동으로 ② 대리모델 추정 경로**로 빠짐(featurize는 함급 리스트 기반이라 그대로 동작).
- 카드 라벨에 "직접 편성 · 추정" 표기.
- 적 편대 '프리셋' 모드 조건은 유지(혼합·랜덤 적은 비결정이라 카드 제외 — 현행 그대로).

## 7. 하위호환 · 회귀
- `fleet_custom` 미사용(프리셋 모드) 시 cfg에 `fleet_custom` 키 없음 → 엔진 기존 경로 → **bit-identical**.
- 저장된 구버전 cfg(=fleet_custom 없음)도 정상 로드(§5 else 경로).
- `audit_verify_regression.py` 8×26 PASS 예상(엔진 무변경·순수 표시/UI).

## 8. 감사 · 빌드 · 위생 (변경 유형: UI·신기능)
- **회귀 확인**: `python audit_verify_regression.py` PASS.
- **정적 스캔**: `python audit_static_scan.py`.
- **신기능 체크리스트**: 3종세트 해당 없음(토글 아님). 신규 위젯 import 확인(8번). 예상전황 확장은 표시 전용.
- **빌드 + GUI 스모크**: `_PLANS` 텍스트는 이미 v15.2 "다음: 임의 편성 UI 확장" 언급 → 완료 반영(문구 갱신). `.py` 변경이므로 전체 빌드 필수.
- **버전**: `APP_VERSION`·헤더 `v16.14.02`, changelog 1건(추가), `_changelog_export.py` 재생성.
- **README**: DB 항목수 무변경, 새 도메인 아님 → `chk_readme_counts`가 APP_VERSION 정합만 확인.
- **커밋·푸시**: joint-defense-sim.

## 9. 구현 순서
1. `FleetCustomDialog` 클래스 + `_expand_custom`/`_collapse_custom` 헬퍼.
2. 아군 편대 셀에 진입 버튼 + `self._fleet_custom` 상태 + 레이블 표시.
3. `_build_cfg_from_ui` / `_restore_cfg` 배선.
4. `_forecast_predict` 직접 편성 지원.
5. 회귀·정적·빌드·GUI 스모크·버전·changelog·푸시.

## 10. 리스크
- UI 위젯 자잘함(추가/삭제/척수 검증·빈 편성 방지)이 코딩 비중 최대.
- 신규 PyQt6 위젯 import 누락 → exe NameError 창 소실(체크리스트 8, 빌드 후 스모크로 검증).
- 예상전황 카드가 직접 편성서 추정 정상 표출되는지 확인(혼합·랜덤 제외 조건과 충돌 없게).
