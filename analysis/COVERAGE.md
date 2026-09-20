# 커버리지 대장 (COVERAGE) — 누적, 덮어쓰지 말 것

> 기준 커밋 `daa7ce8` · 0단계 생성. 상태: `전체읽음` / `발췌` / `안봄` / `해당없음`(자산).
> `안봄` 으로 남은 것은 **숨기지 않는다** — 왜 남았는지 적는다(규약 7.1).
> 분류별 집계는 `10_terrain.md` 에 있다(여기 표에 넣으면 분류명이 파일명으로 파싱된다 —
> 실제로 검사기가 '유령 항목'으로 잡았다).

| 파일 | 라인 | 상태 | 비고 |
|---|---:|---|---|
| `.githooks/pre-commit` |  | 전체읽음 |  |
| `.githooks/pre-push` |  | 전체읽음 |  |
| `.github/ISSUE_TEMPLATE/bug_report.yml` | 39 | 안봄 |  |
| `.github/ISSUE_TEMPLATE/config.yml` | 5 | 안봄 |  |
| `.github/ISSUE_TEMPLATE/feature_request.yml` | 28 | 안봄 |  |
| `.gitignore` |  | 안봄 |  |
| `BLIND_SPOTS.md` | 93 | 발췌 | 해소 선언 vs 실행 주기 — F-003 |
| `CLAUDE.md` | 610 | 발췌 | 파일 구조 표 대조 — F-001 |
| `LICENSE.md` | 75 | 안봄 |  |
| `README.md` | 380 | 안봄 |  |
| `SESSION_LOG.md` | 1805 | 안봄 |  |
| `_ai_export_policy.py` | 63 | 안봄 |  |
| `_ai_rl_train_eval.py` | 149 | 안봄 |  |
| `_ai_selfplay_train.py` | 48 | 안봄 |  |
| `_ai_smoke_rl.py` | 135 | 안봄 |  |
| `_asset_make_bg.py` | 30 | 안봄 |  |
| `_audit_campaign_smoke.py` | 354 | 안봄 |  |
| `_audit_compat.py` | 61 | 안봄 |  |
| `_audit_dashboard.html` | 265 | 안봄 |  |
| `_audit_deep_review.md` | 48 | 안봄 |  |
| `_audit_gui_smoke.py` | 197 | 안봄 |  |
| `_audit_load_guard.py` | 140 | 안봄 |  |
| `_audit_make_pdf.py` | 209 | 안봄 |  |
| `_audit_mc_stability.py` | 69 | 안봄 |  |
| `_audit_nightly.sh` | 52 | 안봄 |  |
| `_audit_render_smoke.py` | 107 | 안봄 |  |
| `_audit_roundtrip.py` | 98 | 안봄 |  |
| `_audit_scenario_smoke.py` | 139 | 안봄 |  |
| `_audit_smoke_util.py` | 117 | 안봄 |  |
| `_audit_ui_shot.py` | 112 | 안봄 |  |
| `_bg_gate.py` | 140 | 안봄 |  |
| `_bg_launch.sh` | 26 | 안봄 |  |
| `_bg_res.py` | 68 | 안봄 |  |
| `_bg_wait.sh` | 31 | 안봄 |  |
| `_build_progress.py` | 158 | 안봄 |  |
| `_changelog_export.py` | 141 | 안봄 |  |
| `_forecast_build_surrogate.py` | 160 | 안봄 |  |
| `ai_policy_infer.py` | 144 | 안봄 |  |
| `ai_rl_env.py` | 330 | 안봄 |  |
| `ai_rl_policy.npz` |  | 해당없음 | 자산(읽을 코드 아님) |
| `ai_selfplay_env.py` | 222 | 안봄 |  |
| `ai_selfplay_loop.py` | 63 | 안봄 |  |
| `app_changelog.json` | 8732 | 안봄 |  |
| `app_engine.py` | 73 | 안봄 |  |
| `app_launcher.py` | 1534 | 안봄 |  |
| `app_main.py` | 411 | 안봄 |  |
| `app_main.spec` | 166 | 안봄 |  |
| `app_theme.py` | 51 | 안봄 |  |
| `app_utils.py` | 660 | 안봄 |  |
| `app_workers.py` | 617 | 안봄 |  |
| `asset_download_images.py` | 270 | 안봄 |  |
| `assets/images/022형 미사일 고속정.jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/039형 잠수함 (송급).jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/041형 잠수함 (위안급 개량).jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/052C형 구축함 (HHQ-9).jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/052D형 구축함.jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/054A형 호위함.jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/055형 대형 구축함.webp` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/056형 초계함.jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/071형 상륙함.jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/093형 잠수함 (상급).jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/094형 잠수함 (진급).jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/AO.jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/AOE.jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/AW-159 와일드캣.webp` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/CG-47.jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/CIWS-II (Phalanx).jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/CJ-10 (순항미사일).jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/CVN.jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/DDG-51.jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/DF-11A (단거리 탄도).webp` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/DF-15 (단거리 탄도).jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/DF-17 (극초음속 활공).png` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/DF-21D (대함 탄도).jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/DF-26 (중장거리 탄도).jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/ESSM Block II.png` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/F-35A 라이트닝 II.webp` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/FA-50 파이팅이글.webp` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/FFX-I.webp` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/FFX-II.webp` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/FFX-III.webp` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/H-6 (폭격기).webp` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/H-6N (폭격기 개량).webp` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/J-10A (비맹).jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/J-10C (맹룡 개량).webp` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/J-11B (플랭커-B).webp` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/J-15 (비상어).jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/J-16 (플랭커-D).jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/J-16D (전자전기).png` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/J-20 (위룡).webp` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/J-35 (백상어).webp` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/J-7 (섬광).jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/JH-7A (날치).jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/KDX-II.jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/KDX-III-B1.jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/KDX-III-B2.webp` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/KF-21 보라매.webp` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/KN-23 (북한 이스칸데르).png` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/KN-24 (단거리 기동탄도).webp` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/KSS-I.png` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/KSS-II.jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/KSS-III.webp` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/Kalibr (3M14 순항미사일).jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/Kh-101 (스텔스 순항).jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/Kh-31A (항공기발사 대함).jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/Kh-31P 대방사미사일.jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/Kh-58U 대방사미사일.webp` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/LD-10 대방사미사일.png` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/LPD.jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/LPH.jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/LST.webp` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/MH-60R 시호크.webp` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/MiG-23 (플로거).jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/MiG-29 (풀크럼).jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/Mk.45 5인치 함포.webp` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/Mk.46 경어뢰.jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/P-3C 오라이온.webp` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/P-800 오닉스 (야혼트).jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/P-8A 포세이돈.webp` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/PCC.jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/PKG.webp` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/PKX-B.jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/RIM-116 RAM.jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/SM-2 Block IIIB.jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/SM-3 Block IIA.jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/SM-6 Block IB.png` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/SM-6 대함 모드.webp` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/SM-6.webp` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/SSN.jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/Su-35 (플랭커-E).webp` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/Su-57 (펠론).jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/Tomahawk Block V.jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/Tu-22M3 (백파이어).jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/YJ-100 (장거리 순항).png` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/YJ-12 (초음속 순항).jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/YJ-18 (초음속 대함).webp` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/YJ-21 (극초음속 대함).jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/app_emblem.png` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/home_bg.jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/spin_down.png` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/spin_up.png` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/랴오닝 (항모).webp` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/북한 순항미사일 (화살-2).webp` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/산둥 (항모).webp` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/슬라바급 순양함.webp` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/신포급 잠수함 (SLBM).jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/신포급 잠수함 (기습).jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/야센급 SSGN.webp` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/오스카-II급 SSGN.png` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/우달로이급 구축함.jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/지르콘 (극초음속 순항).jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/청상어 (경어뢰).webp` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/킨잘 (극초음속 탄도).webp` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/킬로급 잠수함 (Project 636).jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/푸젠 (항모).webp` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/하푼 Block II (AGM-84).jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/하푼 Block II.jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/해궁 (K-SAAM).webp` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/해성-3 (잠수함발사 순항).png` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/해성-I (대함순항).webp` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/해성-I.webp` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/해성-II.webp` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/현무-3C.webp` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/현무-4 (ASBM).webp` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/홍상어 (대잠).jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/화성-12 (IRBM).webp` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/화성-15 (북한 ICBM급).webp` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/화성-17 (북한 ICBM 개량).webp` |  | 해당없음 | 자산(읽을 코드 아님) |
| `assets/images/화성-18 (ICBM 고체연료).png` |  | 해당없음 | 자산(읽을 코드 아님) |
| `audit_db_consistency.py` | 161 | 안봄 |  |
| `audit_dead_toggle.py` | 201 | 발췌 | docstring 'EFFECT_DEBT 43개' stale 여부 미확인 |
| `audit_effect.py` | 222 | 안봄 |  |
| `audit_fuzz.py` | 185 | 안봄 |  |
| `audit_pairwise.py` | 138 | 발췌 | 0단계에서 직접 실행 |
| `audit_perf.py` | 147 | 안봄 |  |
| `audit_perf_baseline.json` | 14 | 안봄 |  |
| `audit_property.py` | 221 | 안봄 |  |
| `audit_regression_golden.json` | 1214 | 안봄 |  |
| `audit_static_scan.py` | 823 | 발췌 | 검사 24함수 추출 · 훅 배선 확인 |
| `audit_verify_regression.py` | 389 | 발췌 | 골든 42×32·캠페인 6케이스 확인 |
| `db_ground_threat.py` | 415 | 발췌 | F-002 — 호출처 0 확인 |
| `db_ocean_acoustic.py` | 676 | 발췌 | L-2 미배선 심볼 |
| `db_ocean_environment.py` | 817 | 발췌 | L-2 미배선 심볼 |
| `db_specsheet.py` | 3517 | 안봄 |  |
| `db_terrain.py` | 715 | 발췌 | L-2 미배선 심볼 |
| `docs/analysis/01_편대_생존_분석.md` | 180 | 안봄 |  |
| `docs/analysis/02_편성비교_지표.md` | 111 | 안봄 |  |
| `docs/analysis/03_지표_역전의_원인.md` | 76 | 안봄 |  |
| `docs/analysis/04_프리셋_난이도_전수.md` | 153 | 안봄 |  |
| `docs/index.html` | 216 | 안봄 |  |
| `docs/notes/01-a-gate-that-only-checked-nothing-broke.md` | 172 | 안봄 |  |
| `docs/notes/02-there-was-no-enemy-so-it-was-zero.md` | 154 | 안봄 |  |
| `docs/notes/03-checks-that-passed-while-looking-at-nothing.md` | 171 | 안봄 |  |
| `docs/notes/CANDIDATES.md` | 196 | 안봄 |  |
| `docs/notes/README.md` | 37 | 안봄 |  |
| `engine_airforce.py` | 488 | 안봄 |  |
| `engine_army.py` | 576 | 발췌 | F-002 판정 근거(범위 선언) |
| `engine_campaign.py` | 1163 | 안봄 |  |
| `engine_combat.py` | 8899 | 발췌 | 1단계: 전역오염·순회필터·부모계약 · F-004/005/007 |
| `engine_core.py` | 2574 | 안봄 |  |
| `engine_joint.py` | 254 | 안봄 |  |
| `forecast_features.py` | 142 | 안봄 |  |
| `forecast_model.pkl` |  | 안봄 |  |
| `forecast_surrogate.json` | 4038 | 안봄 |  |
| `improve_auto_loop.py` | 132 | 안봄 |  |
| `improve_llm_patch.py` | 422 | 안봄 |  |
| `improve_llm_propose.py` | 125 | 안봄 |  |
| `improve_weakness_report.py` | 244 | 안봄 |  |
| `jds_icon.ico` |  | 해당없음 | 자산(읽을 코드 아님) |
| `mixin_configpanel.py` | 1493 | 안봄 |  |
| `mixin_configpanel2.py` | 871 | 안봄 |  |
| `mixin_configpanel3.py` | 395 | 안봄 |  |
| `mixin_export.py` | 143 | 안봄 |  |
| `mixin_optimize.py` | 93 | 안봄 |  |
| `mixin_resultpanel.py` | 1236 | 안봄 |  |
| `mixin_showcase.py` | 293 | 안봄 |  |
| `mixin_simlifecycle.py` | 465 | 안봄 |  |
| `plan_a_defaults.md` | 184 | 안봄 |  |
| `plan_battle_engine.md` | 633 | 안봄 |  |
| `plan_dead_feature_prevention.md` | 170 | 안봄 |  |
| `plan_efficacy_audit.md` | 214 | 안봄 |  |
| `plan_precision_upgrades.md` | 118 | 안봄 |  |
| `plan_roadmap.md` | 269 | 안봄 |  |
| `plan_v18_campaign.md` | 176 | 안봄 |  |
| `plan_v19_airforce.md` | 150 | 안봄 |  |
| `plan_v21_joint.md` | 246 | 안봄 |  |
| `scenarios.py` | 152 | 안봄 |  |
| `src_kf21_source.jpg` |  | 해당없음 | 자산(읽을 코드 아님) |
| `ui_charts.py` | 1290 | 안봄 |  |
| `ui_dialogs.py` | 599 | 안봄 |  |
| `ui_monitor.py` | 774 | 안봄 |  |
| `ui_widgets.py` | 909 | 안봄 |  |
| `view_cesium_3d.html` | 166 | 안봄 |  |
| `감사보고서.md` | 395 | 안봄 |  |
| `로드맵_상세_v11-v20.md` | 351 | 안봄 |  |
