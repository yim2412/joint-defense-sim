# 세션 로그 (SESSION_LOG)

> **목적**: 세션이 의도치 않게 **완전히 닫혀도**(크래시·한도·창 닫힘) 새 세션이 이어가게 하는
> "판단 맥락" 저장소. git 커밋/plan이 담는 *결과*가 아니라 **왜 그렇게 정했나·다음에 뭘 하려
> 했나·미커밋 주의**를 남긴다. 세션 매듭마다 **최신이 위로** 누적.
>
> **재개 3층 방어**: ①새 세션 SessionStart 브리핑이 `git status`(미커밋)+`git log`+이 파일을
> 읽어 자동 복원 ②이 파일이 판단 맥락 보존 ③`audit_static_scan.chk_session_log_fresh`가
> 최신 항목 `HEAD:` 해시와 실제 git HEAD 거리를 검사해 저널 갱신 밀림을 자동 경고(stale 방어).
>
> **작성 규칙**: 각 항목 첫 줄에 `(HEAD: <짧은해시>)`. 코드·결정으로 이미 git/plan에 남은 건
> 중복 기록 말고 **왜/다음/주의**에 집중. 한 세션에 여러 매듭이면 append.

---

## [2026-07-12] 중단 반응성 v18.02.05 (신뢰성 하드닝 계속)  (HEAD: 커밋대기)

- **무엇을**: "더 개선?" → 조용한 폴백 클래스 전체 스캔(engine·app_main) = clean 확인(app_main
  except:pass는 GPU온도·풀예열 등 정당한 선택기능, 캠페인 모델 폴백은 이미 model_loaded로 가시화).
  스캔 중 발견한 **진짜 1건 수정**: 병렬 캠페인 MC 도중 중단 시 `ProcessPoolExecutor.__exit__`
  기본 `shutdown(wait=True)`가 제출된 전체 완료까지 대기 → 정밀 ON 대량 반복이면 중단이 수 분
  안 먹힘. `try/except BaseException → shutdown(wait=False, cancel_futures=True)`로 대기열 즉시
  취소(실행 중 워커만 마무리).
- **검증**: 헤드리스 중단까지 3.6s(전량 대기 대비 대폭 단축)·회귀14 정상경로 무영향·빌드 EXIT0
  (4분49초)·exe 캠페인 스모크 PASS. APP_VERSION/헤더/changelog/변경이력 v18.02.05.
- **다음**: v20.1 지상군. 신뢰성 남은 저값: cfg per-task 피클(#1 순수성능)·GUI abort 실클릭 자동화.
- **미커밋 주의**: 이 커밋으로 반영. engine_campaign.py·app_main.py 변경→빌드 완료·dist 갱신.

## [2026-07-12] 신뢰성 하드닝 v18.02.04 (사용자 "성능보다 확실·실수없이")  (HEAD: 3630bc5)

- **무엇을**: v20 전 신뢰성 우선 개선 — "조용히 틀림 → 시끄럽게 실패". code-review #2·#3 실제 해소.
  ▸병렬 캠페인 MC 워커가 예측모델 로드 실패 시 조용한 win_p=0.5 폴백 대신 `RuntimeError` 중단
  (`_campaign_mc_init(expect_model)`: 메인 성공했는데 워커만 실패=진짜 이상만 중단, 메인도
  없으면 graceful=순차와 일관·model_loaded=False로 가시화). ▸대리모델 교전 rec에 `precise:False`
  추가(정밀/대리 rec 스키마 자기기술화, 미래 소비자 KeyError 예방).
- **검증**: 회귀 14 bit-identical(precise:False 무영향)·병렬MC 정상(initargs)·정적41·가드 로직
  직접 검증(True→예외/False→graceful)·빌드 EXIT0(8분37초)·exe 캠페인 스모크 PASS(MC 병렬 10회
  실행 확인, #5 정규식 수정도 실전 검증). APP_VERSION/헤더/changelog/변경이력 v18.02.04.
- **다음**: v20.1 지상군. 남은 저값 note: cfg per-task 피클(#1 성능)·GUI abort 자동화(오래된 숙제).
- **미커밋 주의**: 이 커밋으로 반영. engine_campaign.py·app_main.py 변경→빌드 완료·dist 갱신.

## [2026-07-12] 종합감사 사각 5개 실제 보완 (사용자 "허점이 있다면?")  (HEAD: d97b57c→f90f8e4)

- **무엇을**: 1차 종합감사(바로 아래 항목)가 ①코드로직을 `/code-review` 없이 수동 Grep만·
  ④통합MC를 n=16/20 소규모만 돌리고 "전부 PASS" 선언한 것을 사용자 질문이 드러냄 → 스스로
  규칙 대비 축소 수행 인정하고 5개 사각 실제로 닫음.
- **닫은 사각**: ①`/code-review high`를 누적 diff(6569fc6..HEAD range 지정)에 실제 실행
  (correctness0·경미5건, #4골든3자리·#5스모크정규식 즉시수정, #1~3 note) · ③정밀ON 회귀
  골든 2케이스 봉인(골든 12→14, `_resolve_precise` 미래 회귀 감시) · ④대규모 MC(OFF n=300·
  ON n=200 병렬, NaN0, 기준값 [[project-baseline-campaign-precise]] OFF surv6.0/ON surv5.8) ·
  ⑤exe 캠페인 MC 병렬 스모크 하드어서션(MC N회 분포 배너 실제 표시=frozen exe 병렬 실증).
- **신규 감사도구**: `_audit_mc_stability.py`(대규모 안정성·기준값). 회귀 도구에 CAMPAIGN_CASES
  추가(정밀ON 결정론 봉인). 캠페인 스모크 MC 어서션 강화.
- **교훈**([[feedback-audit-self-improve]]): 종합감사 ①은 /code-review 실제 실행(수동 대체
  금지), ④는 대규모 MC. 자기평가 관대화를 사용자 질문이 교정.
- **미커밋 주의**: 이 커밋으로 사각 보완 반영. 소스 엔진 무변경(감사 도구·골든·문서만).

## [2026-07-12] 종합 9영역 감사 완료·통과 (v18.02 블록, v20 착수 직전)  (HEAD: 커밋대기)

- **무엇을**: 앞 세션 중단된 종합감사를 **처음부터** 재수행(범위 6569fc6..6dec261, v18.01.08~
  v18.02.03 23커밋, A1 캠페인 정밀 교전 아키텍처 변경 포함). **9영역 전부 PASS/해당없음,
  발견 0건, 종합 통과.**
- **결과**: ①코드로직(A1 라우팅·E1 워커·3종세트·신규stats키 완비)·②DB(해당없음, mutate0)·
  ③회귀12×26·④통합MC(정밀ON병렬n=16 win=1.0 n_precise_avg=3.0)+성능(campaign57ms)·⑤빌드
  (소스무변경=현행유효)+GUI스모크3종·⑥위생(정적41/41)·⑦하위호환(구버전cfg n_precise=0)·
  ⑧불변식45케이스·⑨누수(with풀 자동정리).
- **핵심 규명**: 사용자가 "기능 정상작동?" 물어 재검증 중 앞 세션의 즉석 검증 실패(A1
  n_precise=0·E1 BrokenProcessPool)가 **테스트 스크립트 결함**임을 밝힘 — ▸틀린 프리셋
  이름('중국 항모전단'=미존재→단독작전 폴백→교전0) ▸`__main__` 가드 누락(spawn 자식 재import).
  정확한 감사(`_audit_compat.py`)로 A1 발현·E1 병렬 실작동 **실증**. 엔진은 정상.
- **메타 회고(즉시반영)**: 1회용 `_audit_compat_tmp.py`→`_audit_compat.py` 정식 편입(⑦+④
  정본, 정확한 프리셋 키·main가드). 빌드 스킵 근거 명시(소스 무변경+지난 EXIT0+exe 최신).
  숙제: exe 캠페인 MC 병렬은 헤드리스로만 실증(낮은 리스크).
- **산출물**: 감사보고서.md v18.02 섹션(최신순) + 감사보고서/감사보고서_v18.02.pdf(131KB).
- **다음**: **v20.1 지상군 전력·기동 모델**(로드맵 다음 major, 별도 엔진, 난이도 매우 높음
  →Opus/high). 착수 시 설계 먼저 합의. 영어화·릴리스exe는 장기/외부노출보류로 별개.
- **미커밋 주의**: 이 커밋으로 감사 반영(_audit_compat.py 편입·보고서·PDF·SESSION_LOG).
  소스 .py 무변경(감사는 read-only, 발견 0). `_bgtask.meta`는 bg 헬퍼 산출물(gitignore 대상).

## [2026-07-12] 종합 9영역 감사 착수→중단 (다음 세션 처음부터)  (HEAD: 6dec261)

- **무엇을**: v20(major) 착수 전 종합 9영역 감사 시작(범위 6569fc6..HEAD=v18.01.07 이후
  23커밋, A1 캠페인 아키텍처 변경 포함). **분류기 일시 불가(claude-opus-4-8 temporarily
  unavailable)로 Bash 실행 막혀 중단** → 사용자 "다음에 처음부터 다시 돌린다".
- **중단 시점 진행(참고용, 다음엔 처음부터)**: 7/9 통과 확인 — ①코드로직(수동)·③회귀12×26·
  ④성능(single425·battle67·campaign35ms)·⑥정적41/41·⑧불변식45케이스·⑨누수·②DB해당없음.
  **미완=⑦하위호환+④통합MC(스크립트 `_audit_compat_tmp.py` 작성됨, 미실행)·⑤단발GUI스모크**.
  캠페인·시나리오 스모크는 이미 PASS.
- **다음**: 종합감사 **처음부터** 재수행(트리거=v20 major 직전). `_audit_compat_tmp.py`는
  1회용 임시파일 → **삭제하고 시작**(또는 감사 절차에 정식 편입 판단). 감사보고서.md·PDF 미작성.
- **미커밋 주의**: 소스 변경 없음(감사는 read-only 점검). `_audit_compat_tmp.py`만 워킹트리
  잔존(untracked) — 정리 필요.

## [2026-07-12] ⑥ 시나리오 저장/불러오기 (v18.02.03) — v20 전 트랙 전부 소진  (HEAD: 6dec261)

- **무엇을**: 사용자 백로그 4번. 현재 설정 전체를 JSON 저장·복원(_build_cfg_from_ui/
  _restore_cfg 재사용). 실행 버튼 아래 [저장][불러오기]. 과거 v7.25 DEL-B로 삭제됐으나
  당시 UI 단순화(기능결함 아님)라 재구현 정당.
- **왜/검증**: _build_cfg_from_ui 반환 전부 JSON serializable 정적확인. offscreen 헤드리스는
  QWebEngine(Cesium) offscreen 미지원으로 MainWindow 생성이 하드크래시(RC127)→불가 판명.
  대신 **exe 왕복 스모크 신설**(_audit_scenario_smoke.py): 저장버튼→파일다이얼로그 타이핑→
  JSON 82키 생성→불러오기→상태줄 확인, RESULT_CODE=0. 감사 자기개선 숙제(QFileDialog 자동화)
  를 그 자리서 해소. 순수 UI라 회귀 bit-identical.
- **다음**: **v20 전 열린 6트랙(①감사인프라 ②CAP ③IFF승격 ④위생 ⑤정밀화A1 ⑥시나리오) 전부
  완료.** E1(병렬MC)도 완료. → **v20.1 지상군 전력·기동 모델**(로드맵 다음 major, 별도 엔진,
  매우 높음 난이도 → Opus/high). 영어화·릴리스exe는 장기/외부노출보류로 별개.
- **미커밋 주의**: 이 커밋으로 ⑥ 반영. dist 재빌드 완료(EXIT0)·왕복 스모크 PASS.

## [2026-07-12] E1 캠페인 MC 병렬화 (v18.02.02)  (HEAD: 92cfe05)

- **무엇을**: monte_carlo_campaign을 멀티프로세스 병렬화(ProcessPoolExecutor, 워커
  initializer로 forecast_model.pkl 1회 로드). A1 정밀 MC 실용화가 목적. seed 독립이라
  순차와 집계 bit-identical 검증 완료. 임계 차등: 정밀 ON n≥8·OFF n≥64(정밀 OFF는 개별
  ~85ms라 spawn 오버헤드로 병렬이 오히려 느림을 실측 발견 → 차등화).
- **왜**: "v20 전 남은 것 다" 지시. A1(⑤) 후속. run_campaign 무수정(MC 집계만)이라 회귀 무영향.
- **다음**: **⑥ 사용자 백로그 — 시나리오 저장/불러오기**. 과거 v7.25 DEL-B로 삭제됐으나
  당시 UI 단순화 결정(기능결함 아님), 지금 _build_cfg_from_ui·_restore_cfg 인프라 완비라
  견고 재구현. 영어화·릴리스exe는 v20전 마무리서 제외(장기·외부노출보류).
- **미검증**: exe 캠페인 MC 병렬(전술 MC ProcessPoolExecutor 선례로 낮은 리스크)=감사개선 숙제.
- **미커밋 주의**: 이 커밋으로 E1 반영. dist 재빌드 완료(EXIT0)·스모크 PASS.

## [2026-07-12] 트랙 ⑤ 정밀화 A1 — 캠페인 정밀 교전 (v18.02.01)  (HEAD: b7449cd)

- **무엇을**: 캠페인 교전을 학습 대리모델 근사 대신 **실제 전술 단발(run_v7_simulation)로
  해결**(하이브리드: 적 규모≥3만 정밀·소규모 대리모델). `enable_precise_engagement` 3종세트
  기본OFF·실험적. 함정별 실측 손상(ship_subsystem_damage hp→hp_frac 차감)·실측 요격탄
  비용·요격률 승패 → '추상 피해' 제거. 새 minor v18.02 계열 시작.
- **왜/발견**: 사용자 "네 최선으로" 위임. **버그 1건**: '(직접 편성)'이 FLEET_PRESETS에 없어
  detect range 1km 폴백→요격0·cost0 발견 → calculate_fleet_detect_ranges에 fleet_list
  파라미터 추가(하위호환)+정밀 tcfg서 명시. code-review medium 4건(correctness 버그0,
  #2무인함경계·#3repair복붙헬퍼추출·#4중복계산 수정, #1손상함정full-hp재시작=A6보류 plan기록).
- **검증**: OFF bit-identical(전술 12케이스 골든+캠페인 대리모델 $1391M 동일)·정밀 발현
  (이지스vs항모킬체인 n_precise3, KDX-II 0.5/0.75 차등손상)·정적41/41(precise 3종세트 자동
  등록)·빌드 EXIT0·**GUI 스모크 PASS**(6토글 ON exe 실클릭, 캠페인 배너 정상). 스모크에
  정밀 토글 추가(감사 자기개선).
- **다음**: **E1(병렬 캠페인 MC)** — 정밀 MC는 병렬 필수. 그다음 ⑥ 사용자 백로그 → v20 지상군.
- **미커밋 주의**: 이 커밋으로 트랙⑤ A1 반영. dist 재빌드 완료(EXIT0).

## [2026-07-12] 트랙 ④ 위생 정리 완료  (HEAD: 커밋대기)

- **무엇을**: 6트랙 중 ④위생. 정적 스캔 40/40 PASS로 자동 위생(stale·readme·파일명)은 클린.
  수동 점검: _PLANS/changelog 코드명 잔류 0·완료 minor stale 0. 유일 정리 =
  `plan_workflow_upgrades.md`(트랙① 완료) 아카이브 이동 — 정적 chk가 `plan_v<N>_<M>`
  패턴만 봐 비버전 plan은 못 잡아 수동으로 처리.
- **왜**: 위생은 자동화가 대부분 흡수해 실제 수동 정리가 적은 게 정상. 순수 파일 이동이라
  코드·버전·빌드 무변경.
- **다음**: **⑤ 정밀화 A1**(캠페인 교전을 정밀 전술엔진으로, 손실 미추정 제거 — 정본
  plan_precision_upgrades.md 높음 항목). TaskList #3 완료→#4. 밸런스 변화=골든갱신 동반.
- **미커밋 주의**: 이 커밋으로 트랙④ 반영(파일 이동만).

## [2026-07-11] 트랙 ③ IFF 정규 승격 완료 (v18.01.19)  (HEAD: 커밋대기)

- **무엇을**: 트랙③ 실험적 승격 정리. PNG·동적기상은 이미 승격됨(레이블 없음, 할일0) →
  **IFF만 미정리**. 재검증: 과거 "차이 0"은 오진(고강도 다축 포화를 IFF ON으로 안 돌림,
  오사는 CAP 교전 아닌 근접 아군기 존재만 필요=헬기로도 발현). '중국 3축 vs 이지스+CAP'
  n=250: 요격률 76→65%·오사 1.52 → 승격 게이트 충족. UI '(실험적)' 레이블 제거·기본 OFF.
- **왜**: ②CAP 정상화가 오사 노출을 증폭(헬기만5→CAP+헬기11)하나 필요조건은 아니었음 —
  진짜 관건은 측정 시나리오였다. 정직하게 귀속 규명 후 승격.
- **다음**: **④ 위생 정리**(_PLANS·changelog 코드명·완료항목 잔류). TaskList #2 완료→#3.
  사용자 "실험적 승격 정리 완료하면 말해달라, 마무리" → ③ 커밋·푸시 후 완료 보고 지점.
- **미커밋 주의**: 이 커밋으로 트랙③ 반영. dist 재빌드 완료(EXIT0).

## [2026-07-11] 트랙 ② CAP 공대공 정상화 완료 (v18.01.18)  (HEAD: ac5e3ee)

- **무엇을**: 사용자 "대기 트랙 차례대로" → 6트랙 중 **②CAP 공대공 완료**. CAP 3기종이 전시 발진
  오버라이드에 누락돼 공대공이 죽은 경로였던 것을 상시 공중초계 60s로 살림 + BVR 출격 계상.
  code-review medium이 "하드코딩 목록" altitude 지적 → **role=='cap' 기반 일반화**로 미래 기종
  재발 방지. 골든 10→12(CAP 발현 봉인), 기준값 [[project-baseline-cap]] 신설(적기격침 +0.54).
- **왜**: 밸런스 변경이라 트랙①(감사인프라) 먼저 닫은 뒤 착수. 요격률 영향 미세한 건 항공요격이
  대함미사일 SAM 요격률과 직교하기 때문(정상) — 생존효과는 3축 고밀도 케이스서 뚜렷.
- **다음**: **③ 실험적 승격 정리** — CAP 정상화로 IFF 재검증 선행조건 충족. PNG·동적기상 레이블.
  TaskList #1 완료, #2(③)부터. 순서 ③→④→⑤→⑥.
- **미커밋 주의**: 이 커밋으로 트랙② 전부 반영. dist 재빌드 완료(EXIT0).

## [2026-07-11] v20 착수 전 열린 트랙 전부 소진 착수 — 트랙 ① 감사·워크플로우 인프라 완료  (HEAD: 6268ac4)

- **무엇을**:
  - 사용자 "20버전(지상군) 전 마무리 가능 작업 전부" → 범위=전부. TaskList로 6트랙 등록(①감사인프라 ②CAP ③승격정리 ④위생 ⑤정밀화A1 ⑥사용자백로그), 순서대로.
  - **트랙 ① 감사·워크플로우 인프라 6항목 전부 완료**:
    - ①-1 커버리지 확장(v18.01.17, 48772db): fuzz/pairwise 전장·캠페인 확장. **전장 fuzz가 실버그 2건 발견·수정**(exp 오버플로·점수 음수 clamp). 골든 커버리지 정적검사 추가.
    - ①-2~5(6268ac4): 작업추적 규칙·`_bg_launch.sh`·`audit_perf.py`·`_audit_nightly.sh`.
    - ①-6: `_audit_dashboard.html` + Artifact 게시.
- **왜(판단 맥락)**:
  - 큰 엔진(v20) 들어가기 전 감사 그물을 촘촘히 = 실버그 ROI 최고(전장 fuzz가 바로 2건 잡음, 취지 입증).
  - CAP(②)은 밸런스 변경이라 골든 대거 갱신 동반 → 트랙 ① 먼저 닫고 착수가 안전.
- **다음(사용자 "여기서 멈춤" 2026-07-11)**: **② CAP 공대공 정상화(B)** — `plan_cap_air_engagement.md`. 상시초계 60s 살림 + sorties 계상, 골든·기준값(project-baseline-cap) 대거 갱신. 완료 후 IFF 실험적 재검증 연쇄(③). 그 뒤 ④위생·⑤정밀화A1·⑥사용자백로그. TaskList #2~#6에 등록됨(#1 완료).
- **미커밋 주의**: 없음(트랙① 전부 커밋·푸시, git clean). 재개 지점 = TaskList #2 CAP.

## [2026-07-10] 깊은 감사 → 그물 강화 A~D → 백그라운드 박스 → 재개 인프라 → 정밀화 백로그  (HEAD: 606d78a)

- **무엇을**:
  - 깊은 로직 감사 발견 8건 전부 수정 (v18.01.08~15).
  - 자동 오류탐지 그물 강화 **A~D**: A=회귀 골든 커버리지(8→10케이스)·B=`audit_fuzz.py`(수치키 극단값)·D=`audit_pairwise.py`(토글 쌍)·C=`_audit_deep_review.md`(4팬아웃 감사 레시피).
  - 강화 중 **실크래시 발견·수정**: KF-21이 대잠 초계에 오배정돼 `IRIS-T SL` KeyError (v18.01.16).
  - 백그라운드 진행 박스 **v2 + 고정 10필드 통일**: winpid PID 트리 격리 CPU/RAM·로그단계 진행바(`_bg_res.py`·`_bg_wait.sh`), 시작 박스부터 같은 필드(작업별 라벨 흔들림 교정), 트리거=예상 1분 초과면 전부 박스.
  - CAP 공대공 요격 조사 → **B로 분리** (`plan_cap_air_engagement.md`).
  - **세션 중단 대비 3층 방어** 구축: SessionStart 브리핑에 `git status` 미커밋 감지·`SESSION_LOG.md` 신설·`chk_session_log_fresh`(정적 39항목).
  - **정밀화 개선 백로그** 전수 수집 (`plan_precision_upgrades.md`, 높음 A1·중 6·하 13, 무의미 2 제외).
- **왜(판단 맥락)**:
  - A~D는 "자동으로 찾아주는 기능 강화" 요청. 순서 A→B→D→C(즉효→도구→pairwise→큰투자).
  - CAP: `aircraft_sorties=0`이 단순 계상버그가 아니라 **CAP 공대공이 죽은 경로**(t_available 1200s+standoff)로 드러남. 살리려면 상시초계(60s) 밸런스 변경=기준값·골든 대거갱신 → 서두르지 않고 규명만 plan에 남기고 분리.
  - 재개 인프라: "세션 완전 종료 후 이어가기"는 디스크에 쓴 것만 살아남음 → git status 브리핑 감지 + 이 저널 + 도구 정합검사 3층으로.
- **다음** (전부 "다른 세션에" — 사용자 지시 2026-07-10, 이번 세션은 여기서 매듭):
  - **v20.1 지상군**(로드맵 다음 major, 별도 엔진, Opus/high).
  - **B — CAP 공대공 정상화**(`plan_cap_air_engagement.md`, 밸런스 변경).
  - **정밀화 백로그 A1**(`plan_precision_upgrades.md`, 캠페인 정밀 교전 — 유일 고가치).
  - 경미 숙제: fuzz·pairwise **전장·캠페인 경로** 미커버(단발만)·pairwise triple+.
- **미커밋 주의**: 없음(git clean·전부 푸시). CAP 착수분은 되돌렸고 규명은 `plan_cap_air_engagement.md`에.
