# Joint Defense Simulator — 육해공 통합 방어 시뮬레이터

![License](https://img.shields.io/badge/license-PolyForm%20Noncommercial%201.0.0-blue)
![Python](https://img.shields.io/badge/Python-3-3776AB?logo=python&logoColor=white)
![PyQt6](https://img.shields.io/badge/GUI-PyQt6-41CD52)
![CesiumJS](https://img.shields.io/badge/3D-CesiumJS-6CADDF)
![Platform](https://img.shields.io/badge/platform-Windows-0078D6)
![Status](https://img.shields.io/badge/status-in%20development-yellow)

🇰🇷 한국어 (기본) · [🇺🇸 English](#-english)

육·해·공 전력을 아우르는 **통합 방어 시뮬레이터**를 목표로 하는 프로젝트입니다.
대공·대함·대잠 위협에 대한 교전 시뮬레이션, 몬테카를로 분석, 요구조건(REQ) 판정, Excel/PNG 보고서 생성을 수행합니다.

> **현재 단계:** 해군 — 이지스 기동전단 통합 방어 + 공군 작전급 (v18.02)
> **진행 중:** **작전급 캠페인 엔진** — 며칠 단위 전역을 1시간 단위로 진행, 교전은 학습된 예측 모델로 즉시 계산해 72시간 전역을 수초에 (해상 교통로 통제로 승패 판정)
> **장기 목표:** 육·해·공 합동작전(Joint Operations)을 포괄하는 통합 방어 시뮬레이션

---

## 목차

- [비전 — 육해공 통합](#비전--육해공-통합)
- [주요 기능 (현재 해군 단계)](#주요-기능-현재-해군-단계)
- [실행 방법](#실행-방법)
- [필수 패키지](#필수-패키지)
- [파일 구조](#파일-구조)
- [사용 흐름](#사용-흐름)
- [프로젝트 성격 · 라이선스](#프로젝트-성격--라이선스)
- [피드백 · 의견](#피드백--의견)
- [🇺🇸 English](#-english)

---

## 비전 — 육해공 통합

현재는 **해군 이지스 기동전단의 다층 방어**를 정밀하게 구현하고 있으며, 이를 토대로 단계적으로 전력 영역을 넓혀갑니다.

| 영역 | 상태 | 내용 |
|------|------|------|
| 🌊 **해군 (Naval)** | ✅ 구현 중 | 이지스 기동전단 대공·대함·대잠 다층 방어 |
| ✈️ **공군 (Air)** | 🔜 계획 | 제공권 교전·CAP·SEAD 등 항공 작전 통합 |
| 🪖 **육군 (Land)** | 🔜 계획 | 지상 방공·해안 방어 등 지상 전력 연동 |

---

## 주요 기능 (현재 해군 단계)

- **시간 스텝 기반 양방향 교전 엔진** — 탐지·추적·요격·반격을 초 단위로 시뮬레이션
- **다층 방어 모델** — SAM(SM-3/SM-2/ESSM/해궁) · CIWS(Phalanx/RAM) · 전자전(ECM) · 채프/플레어
- **대함·대잠전** — 함정·잠수함의 대함 타격(해성·하푼·현무-3C) + 함재 헬기·해상초계기(P-8A 등)의 어뢰 교전
- **공군 자산 연동** — CAP 전투기 BVR 요격 · 해성-II 대함 공격 · ARM 회피 레이더 OFF 전술
- **정밀 물리 모델** — RCS 기반 탐지 · 소나 방정식(수동·능동) · 동적 침수·복원력 · 미사일 비례항법(PNG) · 지형/수평선 차폐
- **적응형 전술 AI** — 적이 방어 포화도를 평가해 살보 집중 ↔ 분산 ↔ 기만 침투를 점진 전환
- **전자전·EMCON·사이버전** — ARM 역탐지(레이더 방사 딜레마) · 능동 소나 핑 역탐지 · 전자 좌표 기만 · 사이버 침투(데이터링크 변조·CIC 마비)
- **극초음속·미래 위협 대응** — HGV 활공 궤적 다층 요격(외기권 SM-3 ↔ 대기권 SM-6) · 무인기 군집(Swarm) 포화 소모전 · 자폭 무인수상정(USV) · 기뢰전(MIW)
- **분산·연안 작전** — 분산해양작전(DMO) · 해안 C-RAM/SAM 연안 방어 · 항만 거점 복합 방어
- **무인·자율 자산** — 무인 정찰 드론(수평선 너머 OTH 탐지 확장) · 무인 수상/수중정(USV·UUV — 소해·전방 피켓·무인 점방어)
- **지속 전장 모드** (실험적) — 양측이 작전 목표(자산 방어·해역 통제 등)를 두고 시간 지평까지 겨루는 승/패 판정 엔진
- **3D 전장 시각화** — CesiumJS 위성 지구본 위에 함정·항공기·미사일 궤적·교전 이벤트를 재생(리플레이)
- **몬테카를로 분석** — 표준 MC + LHS 고속 샘플링(멀티프로세싱 병렬) · 스트레스/Sobol 민감도/A·B 비교
- **방대한 무기 체계 DB** — 적군 69종 · 아군 방어 14종 · 대함 타격 8종 · 함정 25종 · 항공 자산 9종 · 편대 프리셋 44종(아군 16 · 적군 28)
- **작전 시나리오 라이브러리 · 적정 편대 추천** — 교리 기반 시나리오 자동 설정 + 비용 대비 성능 편대 순위
- **보고서 출력** — 교전 결과를 Excel(.xlsx) · PNG로 내보내기

---

## 실행 방법

### 개발 환경에서 실행

```powershell
python app_main.py
```

### 실행 파일(exe) 빌드

```powershell
python -m PyInstaller app_main.spec --noconfirm
```

빌드 결과물은 `dist/이지스_기동전단_시뮬레이터/` 폴더에 생성됩니다.

---

## 필수 패키지

```
pip install matplotlib numpy scipy openpyxl pillow pandas PyQt6 PyQt6-WebEngine psutil SALib
```

> `PyQt6-WebEngine`은 3D 전장(CesiumJS) 탭, `SALib`는 Sobol 민감도 분석에 필요합니다.

---

## 파일 구조

> 명명 규칙: 접두 없는 `.py` = 앱이 import·번들하는 **핵심/런타임 모듈**(이름 변경 시 빌드 영향). `_` 접두 = **빌드에서 제외되는 1회용·개발 도구**(수동 실행).

### 핵심 앱·엔진 (exe 번들)
| 파일 | 역할 |
|------|------|
| `app_main.py` | PyQt6 런처 — UI, 시뮬 워커, 결과·DB·계획 탭 등 전체 앱 |
| `engine_core.py` | 핵심 DB(적/아군/함정), 물리 모델, 탐지·교전 로직 |
| `engine_combat.py` | 시간 스텝 기반 양방향 교전 엔진 (아군 공격 무기 DB 포함). ※`v7`은 도입 당시 명칭이며 현재 주 엔진 |
| `engine_campaign.py` | 작전급 캠페인 엔진 — 며칠 단위 전역을 1시간 단위로 진행 (전술 엔진을 교전 해결기로 호출) |
| `engine_airforce.py` | 공군 작전급 층 — 한반도 격자 제공권 + 공군 전력 관리 (캠페인 엔진이 호출) |
| `db_specsheet.py` | DB 탭 스펙시트용 상세 설명 |
| `ai_policy_infer.py` | 학습된 AI 전술 정책을 numpy만으로 추론 (exe 탑재) |
| `forecast_features.py` | 예상 전황 특징화 — 편성·적·날씨를 학습 모델 입력 벡터로 변환 (exe 탑재) |
| `view_cesium_3d.html` | 3D 전장 탭 — CesiumJS 위성 지구본 뷰 |

### DB 데이터 모듈 (exe 번들)
| 파일 | 역할 |
|------|------|
| `db_ground_threat.py` | 북 장사정포·해안포·비행장 등 지상 위협 DB |
| `db_ocean_acoustic.py` | 수온·염분·음속층·해저 음향 DB (소나 방정식용) |
| `db_ocean_environment.py` | 해역 환경(해류·기상 등) DB |
| `db_terrain.py` | 수심·지형·해협 제원 DB |

### 데이터·설정 파일
| 파일 | 역할 |
|------|------|
| `app_changelog.json` | 패치 이력 |
| `audit_regression_golden.json` | 회귀 검증 기준값 (고정 시나리오 결과) |
| `audit_perf_baseline.json` | 성능 회귀 가드 기준값 (경로별 실행시간) |
| `forecast_surrogate.json` | 실행 전 예상 전황 룩업 테이블 |
| `ai_rl_policy.npz` | 학습된 AI 전술 정책 가중치 |
| `app_main.spec` | PyInstaller 빌드 스펙 |

### 회귀·감사 도구 (수동 실행)
| 파일 | 역할 |
|------|------|
| `audit_verify_regression.py` | 회귀 검증 (엔진 동작 무결성 자동 점검 — 자기참조 오라클) |
| `audit_static_scan.py` | 정적 위생 감사 스캐너 (자동추출·vacuous 가드·커버리지 리포트) |
| `audit_property.py` | 속성 기반 감사 — 불변식(확률[0,1]·합=1·NaN 0·보존식·경계) 랜덤 검증 (독립 오라클) |
| `audit_effect.py` | 토글 효과 검증 — 효과 입증 시나리오에서 ON/OFF 델타로 죽은 토글 탐지 |
| `audit_fuzz.py` | 수치 cfg 키 경계값 fuzzing — 극단값(0·음수·거대값) 자동 주입으로 크래시·NaN·확률범위 위반 탐지 |
| `audit_pairwise.py` | 토글 쌍(pairwise) 조합 상호작용 감사 — 엔진 소비 토글 전수 쌍을 ON으로 단발·전장·캠페인 실행해 크래시·NaN·보존식 위반 탐지 |
| `audit_perf.py` | 실행시간 회귀 가드 — 단발·전장·캠페인 실행시간을 기준 대비 측정해 급증(1.5배+) 탐지 |
| `_audit_nightly.sh` | 야간 자동 감사 러너 — 정적+회귀+속성+fuzz+pairwise+성능을 순차 실행해 로그 누적 (schtasks 등록) |
| `_bg_launch.sh` | 백그라운드 작업 표준 런처 — winpid·시작시각 자동 기록(리소스 격리) |
| `_audit_dashboard.html` | 감사 그물 현황판 소스 (6층 감사·성능 기준선·3층 구조 한 페이지 요약) |
| `_audit_roundtrip.py` | 설정 저장/복원 round-trip 런타임 감사 (offscreen Qt, 복원 누락 근본 차단) |
| `_audit_render_smoke.py` | 결과 탭 렌더 크래시 테스트 (헤드리스, 9개 차트 함수 실제+엣지 데이터) |
| `_audit_gui_smoke.py` | exe GUI 스모크 자동화 — 단발 교전 (감사용) |
| `_audit_campaign_smoke.py` | exe GUI 스모크 자동화 — 작전급 캠페인 모드 (감사용) |
| `_audit_scenario_smoke.py` | exe GUI 스모크 자동화 — 시나리오 저장·불러오기 왕복 (감사용) |
| `_audit_compat.py` | 종합감사 ⑦ 하위호환 + ④ 통합 MC 수치 안정성 (구버전 cfg·정밀 병렬 MC, 감사용) |
| `_audit_make_pdf.py` | 감사 보고서 PDF 생성기 |

### 강화학습(RL)·self-play (수동 실행)
| 파일 | 역할 |
|------|------|
| `ai_rl_env.py` | 지속 전장 RL 학습 환경 |
| `ai_selfplay_env.py` · `ai_selfplay_loop.py` | 적 지휘 AI 동시 학습(self-play) 환경·루프 |
| `_ai_selfplay_train.py` · `_ai_rl_train_eval.py` | self-play·RL 학습/평가 스크립트 |
| `_ai_export_policy.py` | 학습 정책 → `ai_rl_policy.npz` 변환 |
| `_ai_smoke_rl.py` | RL 토글 GUI 스모크 |

### LLM 자가개선 루프 (수동 실행)
| 파일 | 역할 |
|------|------|
| `improve_auto_loop.py` | 약점 분석→제안→검증 자동 루프 |
| `improve_llm_propose.py` · `improve_llm_patch.py` | LLM 전술 제안기·코드 패치기 |
| `improve_weakness_report.py` | 개선 약점 리포트 생성 |
| `_forecast_build_surrogate.py` | 예상 전황 룩업(`forecast_surrogate.json`) 빌더 |

### 개발 유틸 (수동 실행, 빌드 제외)
| 파일 | 역할 |
|------|------|
| `_asset_make_bg.py` | 홈 배경 이미지 생성 |
| `_changelog_export.py` | app_changelog.json → `변경이력/` 유형별 정리 문서 생성 |
| `asset_download_images.py` | DB 장비 사진 일괄 수집 |
| `_bg_wait.sh` · `_bg_res.py` | 백그라운드 작업 1분 진행 보고 헬퍼(타임박스 폴링 + 작업 트리 전용 CPU/RAM 격리 측정) |

### 디렉터리
| 경로 | 역할 |
|------|------|
| `assets/images/` | DB 항목별 장비 사진 |
| `감사보고서/` | 블록별 종합 감사 PDF |
| `_archive/plans/` | 구현 완료된 과거 설계 문서 보관 |

---

## 사용 흐름

1. 시뮬레이터 시작 화면에서 **[🚀 시뮬레이터 시작]** 클릭
2. 설정 패널에서 아군 편대·적 위협·해역·날씨 등 구성
3. **[▶ 시뮬레이션 실행]** 또는 몬테카를로 분석 실행
4. 결과 탭에서 요격률·비용·손상 등 확인
5. Excel/PNG 보고서 내보내기

---

## 프로젝트 성격 · 라이선스

이 저장소는 **취미로 개발하는 비상업·개인 학습용 프로젝트**입니다. 상업적 목적이 전혀 없으며,
관심 있는 분들의 **피드백·제안을 환영**합니다.

- **라이선스**: [PolyForm Noncommercial License 1.0.0](LICENSE.md) — 비상업 목적의 사용·수정·공유는 자유, 상업적 이용은 금지됩니다.
- 무기 체계 제원·수치는 공개된 자료를 바탕으로 한 **학습용 근사치**이며, 실제 군사 운용 데이터가 아닙니다.

## 피드백 · 의견

- 🐛 **버그 신고**는 [Issues](../../issues) — 버그 신고 템플릿을 이용해주세요.
- 💡 **기능 제안**도 [Issues](../../issues)의 기능 제안 템플릿으로 남겨주세요.
- 💬 **자유로운 의견·질문·토론**은 [Discussions](../../discussions)에 남겨주세요.
- **한국어·영어 모두 환영**합니다. 편한 언어로 자유롭게 작성해주세요.

---
---

## 🇺🇸 English

A project aiming to be a **joint air–land–sea integrated defense simulator**.
It performs engagement simulation against air, surface, and subsurface threats, Monte Carlo analysis,
requirement (REQ) evaluation, and Excel/PNG report generation.

> **Current stage:** Navy — Aegis task force integrated defense + air-force operational layer (v18.02)
> **In progress:** Architecture transition from single-salvo engagement → a **persistent battle engine** (both sides pursue operational objectives, win/loss adjudication, aiming toward reinforcement-learning-based self-play)
> **Long-term goal:** an integrated defense simulation covering joint air–land–sea operations

### Vision — Air–Land–Sea Integration

The project currently models the **multi-layered defense of a naval Aegis task force** in detail, and will
expand to other force domains step by step.

| Domain | Status | Scope |
|--------|--------|-------|
| 🌊 **Naval** | ✅ In development | Aegis task force multi-layer air/surface/subsurface defense |
| ✈️ **Air** | 🔜 Planned | Air superiority engagements, CAP, SEAD integration |
| 🪖 **Land** | 🔜 Planned | Ground-based air defense, coastal defense integration |

### Key Features (current — Naval stage)

- **Time-step bidirectional engagement engine** — detection, tracking, interception, and counterstrike simulated per second
- **Multi-layer defense model** — SAM (SM-3 / SM-2 / ESSM / K-SAAM) · CIWS (Phalanx / RAM) · electronic warfare (ECM) · chaff/flares
- **Anti-surface & anti-submarine warfare** — ship/submarine surface strikes (Haeseong, Harpoon, Hyunmoo-3C) + torpedo engagements by shipborne helicopters and maritime patrol aircraft (P-8A, etc.)
- **Air asset integration** — CAP fighter BVR interception · Haeseong-II anti-ship strikes · ARM-evasion radar-off tactics
- **Detailed physics models** — RCS-based detection · sonar equation (passive/active) · dynamic flooding & stability · missile proportional navigation (PNG) · terrain/horizon masking
- **Adaptive tactical AI** — the enemy evaluates defensive saturation and gradually shifts among salvo concentration ↔ dispersion ↔ deception penetration
- **Electronic warfare · EMCON · cyber** — ARM counter-detection (radar-emission dilemma) · active-sonar ping counter-detection · electronic coordinate deception · cyber intrusion (datalink corruption, CIC blinding)
- **Hypersonic & emerging threats** — layered interception of HGV glide trajectories (exo-atmospheric SM-3 ↔ endo-atmospheric SM-6) · drone-swarm saturation attrition · suicide unmanned surface vessels (USV) · mine warfare (MIW)
- **Distributed & littoral operations** — Distributed Maritime Operations (DMO) · shore-based C-RAM/SAM littoral defense · combined harbor-stronghold defense
- **Unmanned & autonomous assets** — unmanned reconnaissance drones (over-the-horizon detection extension) · unmanned surface/undersea vehicles (USV·UUV — minesweeping, forward picket, unmanned point defense)
- **Persistent battle mode** (experimental) — a win/loss engine where both sides pursue operational objectives (asset defense, sea control, etc.) over a time horizon
- **3D battlefield visualization** — ships, aircraft, missile trajectories, and engagement events replayed on a CesiumJS satellite globe
- **Monte Carlo analysis** — standard MC + LHS fast sampling (multiprocessing) · stress / Sobol sensitivity / A·B comparison
- **Extensive weapon-system DB** — 69 enemy threats · 14 friendly defenses · 8 surface-strike weapons · 25 ship classes · 9 air assets · 44 fleet presets (16 friendly · 28 enemy)
- **Operational scenario library & fleet recommendation** — doctrine-based scenario auto-setup + cost-effectiveness fleet ranking
- **Report export** — engagement results to Excel (.xlsx) and PNG

### Running

```powershell
# Run in a development environment
python app_main.py

# Build the executable (exe)
python -m PyInstaller app_main.spec --noconfirm
```

Build output is generated under `dist/이지스_기동전단_시뮬레이터/`.

### Requirements

```
pip install matplotlib numpy scipy openpyxl pillow pandas PyQt6 PyQt6-WebEngine psutil SALib
```

> `PyQt6-WebEngine` is needed for the 3D battlefield (CesiumJS) tab; `SALib` for Sobol sensitivity analysis.

### File Structure

| File | Role |
|------|------|
| `engine_core.py` | Core DBs (enemy/friendly/ships), physics models, detection & engagement logic |
| `engine_combat.py` | Time-step bidirectional engagement engine_core |
| `engine_campaign.py` | Operational campaign engine — multi-day theater in 1-hour ticks (calls the tactical engine as an engagement solver) |
| `engine_airforce.py` | Air-force operational layer — Korean-theater air-superiority grid + air fleet management (called by the campaign engine) |
| `app_main.py` | PyQt6 app_main — UI, sim workers, result/DB/plan tabs, the whole app |
| `db_specsheet.py` | Detailed spec-sheet descriptions for the DB tab |
| `app_changelog.json` | Patch history |
| `app_main.spec` | PyInstaller build spec |
| `assets/images/` | Equipment photos per DB entry |

### Usage Flow

1. Click **[🚀 Start Simulator]** on the start screen
2. Configure friendly fleet, enemy threats, sea area, weather, etc. in the settings panel
3. Run **[▶ Run Simulation]** or a Monte Carlo analysis
4. Review interception rate, cost, damage, etc. in the result tabs
5. Export Excel/PNG reports

### Project Nature · License

This repository is a **non-commercial, personal hobby/learning project**. There is no commercial intent,
and **feedback and suggestions are welcome**.

- **License**: [PolyForm Noncommercial License 1.0.0](LICENSE.md) — non-commercial use, modification, and sharing are free; commercial use is prohibited.
- Weapon-system specifications and figures are **learning-purpose approximations** based on publicly available sources, and are **not** real operational military data.

### Feedback

- 🐛 **Bug reports** → [Issues](../../issues) (bug report template)
- 💡 **Feature requests** → [Issues](../../issues) (feature request template)
- 💬 **Open-ended ideas, questions, discussion** → [Discussions](../../discussions)
- **Both Korean and English are welcome** — write in whichever language is comfortable.

> Note: the in-app text, changelog, and roadmap are maintained in Korean, as the project is built around
> Republic of Korea Navy/military systems. This English section mirrors the Korean documentation above.
