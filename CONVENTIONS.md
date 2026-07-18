# CONVENTIONS.md — 로컬 모델(aider)용 압축 규칙

정본은 `CLAUDE.md`(46KB, 64k 컨텍스트의 70%를 먹어 로컬엔 못 먹인다). 이 파일은
**작업 중 실수로 이어지는 규칙만** 추린 3~4KB 버전. 판단이 필요한 결정(설계·감사
승인·버전 승격)은 하지 말고 사용자에게 물을 것 — 이 파일은 "어떻게 고치나"만 다룬다.

## 버전 표기
- `vX.YY.ZZ` (minor·seq는 두 자리, 한 자리면 0 채움). 변경 **1건 = 버전 1개**.
- `'patch'`라는 단어는 쓰지 않는다.
- `app_main.py`의 `APP_VERSION` 상수 + 파일 최상단 헤더 주석 버전을 **항상 같이** 갱신.
- `app_changelog.json` 배열 마지막에 `{"version","date","title","changes":[...]}` 추가.
  `changes` 항목은 `"추가  ..."` / `"수정  ..."` / `"삭제  ..."` + 군사용어(함수명·변수명 금지).

## 절대 규칙 (어기면 게이트가 다 PASS인데 기능만 죽는다)
1. **재할당 전역은 이름 import 금지 — 모듈 경유.** `global X`로 재대입되는 전역을
   `from mod import X` 하면 import 시점 값이 복사돼 재할당이 안 보인다.
   예: `app_utils._GLOBAL_POOL`, `app_theme.CHART_DPI`는 항상 `app_utils.` / `app_theme.`
   접두로 읽고 쓸 것. 옮기기 전에 `grep "global X"`로 재할당 여부 확인.
2. **모듈 의존은 단방향**: `app_main.py` → 하위 모듈(`app_engine`·`app_utils`·`app_theme`·
   `ui_widgets`·`ui_charts`·`ui_dialogs`·`app_workers`·`scenarios`·`ui_monitor`·
   `app_launcher`·`mixin_*`). **하위 모듈이 app_main을 import하면 즉시 순환** — ImportError나
   NameError로 즉시 드러나진 않아도(부분 초기화 순서 우연히 맞아도) 원칙 위반. 필요한 값은
   생성자 인자로 넘긴다(예: `SplashWindow(app_version)`, `MainWindow(APP_VERSION)`).
3. **PyQt6 클래스는 QtCore/QtGui/QtWidgets 배치를 확인하고 import**. 흔한 실수:
   `QShortcut`·`QKeySequence`는 **QtGui**(QtWidgets 아님), `QGraphicsDropShadowEffect`는
   **QtWidgets**(QtGui 아님). 잘못 넣으면 ImportError로 앱이 통째로 안 뜬다.
4. **전역 DB를 직접 수정하지 않는다.** 로컬 사본(`dict(enemy_info)`)을 만들어 쓴다.
   `run_v7_simulation()` 등 진입부는 항상 `cfg = dict(cfg)`.
5. **`self._log()` 호출은 `if not self._mc_mode:` 가드 필수** (MC 1000회 반복 시 과출력 방지).
6. **콤보박스는 `NoScrollComboBox`만** (`QComboBox` 직접 사용 금지 — 스크롤 오조작 방지).

## 신기능(`enable_xxx` 토글) 추가 시 체크리스트
플래그명은 한 번 정하면 바꾸지 않는다(저장된 시나리오 cfg 호환).
1. 체크박스(UI) + cfg 빌드(`isChecked()`) + cfg 로드(`hasattr` 패턴) **3종 세트** 전부.
2. `engine_combat.py`에 새 심볼 추가 시 `app_engine.py`(또는 해당 mixin)의 import 목록 갱신.
3. 새 `stats` 키는 MC 3경로(`monte_carlo_v7`·`_mc_batch_worker`·`monte_carlo_lhs`) 모두 추가.
4. DB(`ENEMY_DB` 등) 수정 시 `normalize_enemy_db()` 확인, `db_specsheet.py`에 설명 추가.
5. 새 클래스 추가 시 `run_v7_simulation` 진입부 `_id_counter` 리셋 로직 확인.
6. **신규 `enable_*`는 효과 프로브(`audit_effect.py`) 없이 커밋 불가**(pre-commit이 막는다) —
   프로브를 못 만들겠으면 사용자에게 물을 것, 임의로 화이트리스트에 추가하지 않는다.

## 작업 순서 (매번)
```
1. 코드 수정
2. python audit_local_edit.py      # 실제 diff 기준으로 필요한 게이트를 알아서 골라 돌림
3. git add <수정한 파일만>   # dist/build/ 제외
4. git commit  (pre-commit 훅이 정적·회귀를 다시 돌린다 — FAIL이면 원인 고치고 재시도)
```
- `audit_local_edit.py`가 "실제로 바뀐 파일 0개"라고 하면 **아무것도 한 게 없는 것이다.**
  스스로 "수정했다"고 말했더라도 git diff가 비어 있으면 그 보고는 거짓이다 — 다시 시도하거나
  왜 안 됐는지 사용자에게 그대로 보고한다. 안 되는 걸 됐다고 보고하는 게 가장 위험한 실수다
  (plan_local_llm.md §1-e 실측 — 도구 호출 0회로 "4가지 수정했다"고 보고한 사례).
- FAIL이 나오면 **`--no-verify`로 우회하지 않는다.** 원인을 고치거나, 못 고치겠으면 사용자에게 보고.
- 의도된 엔진 변경으로 골든이 달라졌으면 `python audit_verify_regression.py --update` 후
  왜 달라졌는지 커밋 메시지에 한 줄 남긴다.
- **`audit_local_edit.py`가 전부 PASS라고 나와도 "맞게 만들었다"는 증명이 아니다.** 게이트는
  "기존을 안 깨뜨렸나"만 본다. 상태 플래그(`self.X = True`)를 추가했다면 **되돌리는 경로가
  있는지**(매 틱 재대입인지, 한 번 세팅 후 영원히 True인지) 직접 diff를 눈으로 확인할 것 —
  이건 게이트가 원리상 못 잡는다(과거 실측: 패턴을 절반만 베껴 플래그가 영구 True로 박힌
  사례, py_compile·정적51·회귀38×29 전부 PASS인데 버그였다).

## 하지 말 것 (사용자/Claude 판단 영역)
- 종합 9영역 감사, `/code-review`, 아키텍처 설계 변경 — 이런 건 시도하지 말고 그대로 보고한다.
- 여러 파일에 걸친 대규모 리팩터(모듈 분할 등)는 먼저 계획을 사용자에게 제시하고 승인 후 진행.
- `app_changelog.json`·`_PLANS`(`app_launcher.py` 안 `_build_plan_tab`)에 함수명·클래스명·
  변수명을 쓰지 않는다(exe에 노출되는 텍스트라 군사용어만 — 정본 CLAUDE.md '용어 작성 규칙').

## 파일이 어디 있는지 (헷갈리면 여기부터)
`app_main.py`(런처 진입점, 얇음) · `mixin_*.py`(MainWindow 기능별 6조각) ·
`app_launcher.py`(SplashWindow) · `ui_monitor.py`(실행 모니터) · `ui_widgets.py`(재사용 위젯) ·
`ui_charts.py`(차트 렌더) · `ui_dialogs.py`(모달) · `app_workers.py`(백그라운드 QThread) ·
`app_engine.py`(엔진 import 계층) · `app_utils.py`(비-GUI 유틸) · `app_theme.py`(색상) ·
`scenarios.py`(시나리오 프리셋) · `engine_core.py`/`engine_combat.py`(엔진 본체) ·
`engine_campaign.py`/`engine_airforce.py`/`engine_army.py`/`engine_joint.py`(작전급 층).
전체 표·역할 설명은 `CLAUDE.md` 상단 참조(필요하면 그 부분만 읽어달라고 요청).
