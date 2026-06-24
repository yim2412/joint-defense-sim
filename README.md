# Joint Defense Simulator — 육해공 통합 방어 시뮬레이터

🇰🇷 한국어 (기본) · [🇺🇸 English](#-english)

육·해·공 전력을 아우르는 **통합 방어 시뮬레이터**를 목표로 하는 프로젝트입니다.
대공·대함·대잠 위협에 대한 교전 시뮬레이션, 몬테카를로 분석, 요구조건(REQ) 판정, Excel/PNG 보고서 생성을 수행합니다.

> **현재 단계:** 해군 — 이지스 기동전단 통합 방어 (v15.06)
> **진행 중:** 단발 살보 교전 → **지속 전장 엔진**으로 아키텍처 전환 (양측 작전 목표·승패 판정·강화학습 기반 자가 대전 지향)
> **장기 목표:** 육·해·공 합동작전(Joint Operations)을 포괄하는 통합 방어 시뮬레이션

---

## 비전 — 육해공 통합

현재는 **해군 이지스 기동전단의 다층 방어**를 정밀하게 구현하고 있으며, 이를 토대로 단계적으로 전력 영역을 넓혀갑니다.

| 영역 | 상태 | 내용 |
|------|------|------|
| 🌊 **해군 (Naval)** | ✅ 구현 중 | 이지스 기동전단 대공·대함·대잠 다층 방어 |
| ✈️ **공군 (Air)** | 🔜 계획 | 제공권 교전·CAP·SEAD 등 항공 작전 통합 |
| 🪖 **육군 (Land)** | 🔜 계획 | 지상 방공·해안 방어 등 지상 전력 연동 |

---

## 주요 기능 (현재 — 해군 단계)

- **시간 스텝 기반 양방향 교전 엔진** — 탐지·추적·요격·반격을 초 단위로 시뮬레이션
- **다층 방어 모델** — SAM(SM-3/SM-2/ESSM/해궁) · CIWS(Phalanx/RAM) · 전자전(ECM) · 채프/플레어
- **대함·대잠전** — 함정·잠수함의 대함 타격(해성·하푼·현무-3C) + 함재 헬기·해상초계기(P-8A 등)의 어뢰 교전
- **공군 자산 연동** — CAP 전투기 BVR 요격 · 해성-II 대함 공격 · ARM 회피 레이더 OFF 전술
- **정밀 물리 모델** — RCS 기반 탐지 · 소나 방정식(수동·능동) · 동적 침수·복원력 · 미사일 비례항법(PNG) · 지형/수평선 차폐
- **적응형 전술 AI** — 적이 방어 포화도를 평가해 살보 집중 ↔ 분산 ↔ 기만 침투를 점진 전환
- **지속 전장 모드** (실험적) — 양측이 작전 목표(자산 방어·해역 통제 등)를 두고 시간 지평까지 겨루는 승/패 판정 엔진
- **3D 전장 시각화** — CesiumJS 위성 지구본 위에 함정·항공기·미사일 궤적·교전 이벤트를 재생(리플레이)
- **몬테카를로 분석** — 표준 MC + LHS 고속 샘플링(멀티프로세싱 병렬) · 스트레스/Sobol 민감도/A·B 비교
- **방대한 무기 체계 DB** — 적군 65종 · 아군 방어 14종 · 대함 타격 8종 · 함정 21종 · 항공 자산 7종 · 편대 프리셋 38종
- **작전 시나리오 라이브러리 · 적정 편대 추천** — 교리 기반 시나리오 자동 설정 + 비용 대비 성능 편대 순위
- **보고서 출력** — 교전 결과를 Excel(.xlsx) · PNG로 내보내기

---

## 실행 방법

### 개발 환경에서 실행

```powershell
python launcher.py
```

### 실행 파일(exe) 빌드

```powershell
python -m PyInstaller launcher.spec --noconfirm
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

| 파일 | 역할 |
|------|------|
| `engine.py` | 핵심 DB(적/아군/함정), 물리 모델, 탐지·교전 로직 |
| `engine_v7.py` | 시간 스텝 기반 양방향 교전 엔진 (아군 공격 무기 DB 포함) |
| `launcher.py` | PyQt6 런처 — UI, 시뮬 워커, 결과·DB·계획 탭 등 전체 앱 |
| `spec_db.py` | DB 탭 스펙시트용 상세 설명 |
| `military_db.py` | 북 장사정포·해안포·비행장 등 지상 위협 DB |
| `ocean_acoustic_db.py` | 수온·염분·음속층·해저 음향 DB (소나 방정식용) |
| `ocean_environment_db.py` | 해역 환경(해류·기상 등) DB |
| `terrain_db.py` | 수심·지형·해협 제원 DB |
| `changelog.json` | 패치 이력 |
| `launcher.spec` | PyInstaller 빌드 스펙 |
| `verify_regression.py` | 회귀 검증 (엔진 동작 무결성 자동 점검) |
| `audit_scan.py` | 정적 위생 감사 스캐너 |
| `assets/images/` | DB 항목별 장비 사진 |
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

> **Current stage:** Navy — Aegis task force integrated defense (v15.06)
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
- **Persistent battle mode** (experimental) — a win/loss engine where both sides pursue operational objectives (asset defense, sea control, etc.) over a time horizon
- **3D battlefield visualization** — ships, aircraft, missile trajectories, and engagement events replayed on a CesiumJS satellite globe
- **Monte Carlo analysis** — standard MC + LHS fast sampling (multiprocessing) · stress / Sobol sensitivity / A·B comparison
- **Extensive weapon-system DB** — 65 enemy threats · 14 friendly defenses · 8 surface-strike weapons · 21 ship classes · 7 air assets · 38 fleet presets
- **Operational scenario library & fleet recommendation** — doctrine-based scenario auto-setup + cost-effectiveness fleet ranking
- **Report export** — engagement results to Excel (.xlsx) and PNG

### Running

```powershell
# Run in a development environment
python launcher.py

# Build the executable (exe)
python -m PyInstaller launcher.spec --noconfirm
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
| `engine.py` | Core DBs (enemy/friendly/ships), physics models, detection & engagement logic |
| `engine_v7.py` | Time-step bidirectional engagement engine |
| `launcher.py` | PyQt6 launcher — UI, sim workers, result/DB/plan tabs, the whole app |
| `spec_db.py` | Detailed spec-sheet descriptions for the DB tab |
| `changelog.json` | Patch history |
| `launcher.spec` | PyInstaller build spec |
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
