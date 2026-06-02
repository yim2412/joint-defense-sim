# 이지스 기동전단 통합 방어 시뮬레이터 — 프로젝트 규칙

## 프로젝트 개요

한국 해군 이지스 기동전단의 다층 방어 시뮬레이터. 대공·대함·대잠 위협에 대한 교전 시뮬레이션, 몬테카를로 분석, 요구조건(REQ) 판정, Excel/PNG 보고서 생성을 수행한다.

**현재 버전: v9.11**

### 파일 구조

| 파일 | 역할 |
|------|------|
| `engine.py` | 핵심 DB (ENEMY_DB 63종·FRIENDLY_DB 14종·SHIP_DB 21종 등), 물리모델, 탐지·교전 로직 |
| `engine_v7.py` | 시간 스텝 기반 양방향 교전 엔진. engine.py DB를 import해서 사용 |
| `launcher.py` | PyQt6 런처 — UI, 시뮬 워커, 결과 탭, DB 탭, 향후 계획 탭 등 전체 앱 |
| `spec_db.py` | DB 탭 스펙시트 패널용 상세 설명 (origin, categories, note) |
| `changelog.json` | 패치 이력 (배열, 버전 번호 순서) |
| `launcher.spec` | PyInstaller 빌드 스펙 |
| `anim_render.py` | 현재 미사용 (애니메이션 탭 폐기 후 잔존, 추후 정리 예정) |

### 실행 방법

```powershell
# 런처 실행 (개발 중)
python launcher.py

# exe 빌드
python -m PyInstaller launcher.spec --noconfirm
```

### 필수 패키지

```
pip install matplotlib numpy scipy openpyxl pillow pandas PyQt6 psutil
```

---

## 버전 관리 규칙

### 버전 체계

```
v{major}.{minor} / v{major}.{minor} patch

major : 아키텍처 전환 (v7 = PyQt6 + 시간스텝 엔진, v8 = 현재 시대)
minor : 신기능 추가 또는 대규모 패치
patch : 버그 수정 전용 (기능 추가 없음)
```

### 버전 번호 갱신 규칙

`launcher.py` 최상단 헤더의 버전 번호(`v8.xx`)는 **패치 완료 시 수동으로 직접 수정**한다.

### 헤더 주석 규칙

`launcher.py` 최상단 헤더에 현재 버전과 최근 변경 내용을 기록한다.

```python
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   이지스 기동전단 통합 방어 시뮬레이터  v8.25 — PyQt6 런처                 ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  [v8.25 — 변경 내용 한 줄 요약]                                              ║
║  NEW-A  추가 기능                                                            ║
║  BUG-1  버그 수정                                                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
```

**파일 하단 패치 이력 블록은 작성하지 않는다.** 변경 이력은 git 커밋 메시지로 관리한다.

코드 내 인라인 주석은 "왜 이렇게 했는지" 비직관적인 수치·결정에만 단다.

```python
# BUG-5: SAM 근접 신관 실제 범위 (기존 2000m 과대)
INTERCEPT_DIST_M = 200
```

### 레이블 규칙

| 레이블 | 의미 |
|--------|------|
| `NEW-A`, `NEW-B`, ... | 신기능 (알파벳 순서로 누적) |
| `BUG-1`, `BUG-2`, ... | 버그 수정 (버전 내 번호 재시작) |
| `DEL-A`, `DEL-B`, ... | 코드·기능 제거 |

### Git 커밋 규칙

기능 단위로 완성 후 커밋한다. 작업 중간 상태는 커밋하지 않는다.

```
커밋 메시지 형식:
v8.26: [변경 내용 한 줄 요약]
v8.26 patch: [버그 수정 내용]
```

### 감사 정책 (마이너 버전마다 — 빌드·커밋 전 수행)

**모든 마이너 버전(vXX.Y) 완료 시, 변경 유형에 맞는 감사를 빌드 직전에 1회 수행한다.**
유형이 맞지 않는 감사는 생략한다(UI만 바꿨는데 수치 감사 금지).

| 변경 유형 | 감사 종류 | 방법 |
|-----------|-----------|------|
| 엔진 로직·새 클래스·교전 흐름 변경 | **코드/로직 감사** | `/code-review medium` (난이도 높음↑이면 high) |
| DB 수치·물리 파라미터 변경 | **현실성 수치 감사** | 공개 제원·교리와 대조 (수동 또는 Explore 에이전트) |
| UI·시각화·문서만 변경 | **회귀 확인** | 빌드 성공 + 스모크 실행만 |
| 아키텍처 전환(난이도 매우 높음) | **코드 감사 + 로직 트레이스** | `/code-review high` + 핵심 경로 수동 추적 |

**메이저 블록 완료 시(v11, v12 … 각 묶음의 마지막 마이너 직후):**
전체 회귀 MC(기준 시나리오) + 누적 수치 감사 1회 — 블록 통합 후 상호작용 버그 점검.

감사에서 발견한 항목은 **그 자리에서 수정 후 커밋**한다(별도 patch 버전). 감사 결과는 커밋 메시지에 1줄 요약.

### 패치 완료 시 필수 체크리스트 (매번 반드시 수행)

**어떤 코드를 수정하든 패치 완료 후 아래를 반드시 처리한다.**

0. **감사 수행** (위 '감사 정책' 표 — 변경 유형에 맞는 감사를 빌드 전에)

1. **launcher.py 헤더 버전 번호 갱신** (v8.xx → v8.xx+1)

2. **changelog.json 갱신**: 새 항목을 배열 마지막에 추가
   ```json
   {
     "version": "v8.26",
     "date": "YYYY-MM-DD",
     "title": "변경 내용 제목",
     "changes": ["추가  ...", "수정  ...", "삭제  ..."]
   }
   ```
   `version` 필드는 반드시 실제 패치 버전 문자열 (`v8.26`, `v8.26 patch` 등)을 사용한다.

3. **향후 계획 탭 갱신** (`launcher.py` → `_build_plan_tab()` 내 `_PLANS`):
   - 구현 완료된 항목은 **즉시 삭제**한다.
   - 새 계획 생기면 추가한다.

4. **dist 폴더 갱신 (빠뜨리지 말 것)**:

   | 변경 파일 | 처리 |
   |-----------|------|
   | `.py` 파일 변경 | **전체 빌드** `python -m PyInstaller launcher.spec --noconfirm` |
   | `changelog.json`만 변경 | `_internal` 폴더에 복사만 |
   | `spec_db.py`만 변경 | `_internal` 폴더에 복사만 |
   | `.py` + json 동시 변경 | **전체 빌드** 후 복사 불필요 (빌드 시 자동 포함) |

   ```powershell
   # .py 변경 시 — 전체 빌드
   python -m PyInstaller launcher.spec --noconfirm

   # json/spec_db만 변경 시 — 복사만
   Copy-Item changelog.json "dist\이지스_기동전단_시뮬레이터\_internal\" -Force
   Copy-Item spec_db.py "dist\이지스_기동전단_시뮬레이터\_internal\" -Force
   ```

빌드 후 git 커밋은 소스 파일만 한다. `dist/`, `build/` 폴더는 커밋하지 않는다.

---

## 개발 워크플로우

### 난이도별 작업 방식

| 난이도 | 방식 |
|--------|------|
| 낮음 | 설계 없이 바로 구현 |
| 중간 이상 | 설계 먼저 → 합의 후 구현 → 설계 메모리 저장 |

### 중간 이상 설계 포함 항목

- 수정할 파일 목록
- 핵심 변경 내용 (함수명, 반환값 변경 등)
- 의존성 / 주의사항 (하위 호환 등)
- 필요 시 핵심 코드 스니펫

---

## 코드 규칙

### DB 구조 원칙

- `ENEMY_DB` (engine.py): 적군 63종. `normalize_enemy_db()` 호출 시 누락 필드 자동 보완.
- `FRIENDLY_DB` (engine.py): 아군 방어 무기 14종. `pk_dist`는 Beta 분포 파라미터.
- `FRIENDLY_STRIKE_DB` (engine_v7.py): 아군 공격 무기 (해성·하푼·현무-3C 등).
- `SHIP_DB` / `FLEET_PRESETS` (engine.py): 아군 함정 21종·편대 프리셋 15종.
- `ENEMY_FLEET_PRESETS` (engine.py): 적군 편대 프리셋 14종.
- `FRIENDLY_AIRCRAFT_DB` (engine.py): 함재 헬기·해상초계기 4종.
- `SPEC_DETAIL_DB` (spec_db.py): DB 탭 스펙시트 표시용 상세 설명.

### 신기능 추가 시 체크리스트

1. `ENEMY_DB` / `FRIENDLY_DB` 등 DB 수정 시 `normalize_enemy_db()` 확인
2. 새 클래스 추가 시 `_id_counter` 리셋 로직 필수 (`run_v7_simulation` 진입부)
3. 신기능은 `enable_xxx` 플래그로 ON/OFF 가능하게 만든다 (하위 호환 유지)
4. engine_v7.py 새 심볼은 launcher.py import 목록에 추가
5. spec_db.py에 없는 신규 DB 항목은 동시에 스펙 설명 추가

### 하위 호환 원칙

- 전역 DB를 시뮬레이션 실행 중 직접 수정하지 않는다. 로컬 사본(`dict(enemy_info)`)을 만들어 사용한다.
- `_mc_batch_worker` 반환 tuple 인덱스 변경 시 `monte_carlo_v7` / `monte_carlo_lhs` 수신부도 함께 수정한다.

### engine.py 주요 유틸 함수 (v7에서 import해서 사용)

| 함수 | 역할 |
|------|------|
| `normalize_enemy_db()` | ENEMY_DB 누락 필드 자동 설정 (파일 로드 시 1회 실행) |
| `calculate_detect_range_by_rcs()` | RCS 기반 탐지거리 계산 |
| `generate_random_enemy_fleet()` | 랜덤 적군 편대 생성 |

### engine_v7.py 주요 클래스·함수

| 항목 | 역할 |
|------|------|
| `SimV7` | 메인 시뮬레이션 클래스 |
| `_friendly_defense()` | 아군 SAM/CIWS로 적 미사일 요격 |
| `_friendly_strike()` | 아군 함정/잠수함 → 적 수상함 공격 |
| `_enemy_defense()` | 적 수상함 SAM/CIWS로 아군 미사일 요격 |
| `_aircraft_asw()` | 함재 헬기·초계기 대잠 공격 |
| `_arm_radar_off_check()` | ARM 탐지 시 레이더 OFF 전술 |
| `monte_carlo_v7()` | 표준 MC 분석 |
| `monte_carlo_lhs()` | LHS 샘플링 기반 고속 MC |
| `_compile()` | 시뮬 결과 dict 반환 |

---

## 향후 계획 요약

향후 계획 전체 목록은 `launcher.py` → `_build_plan_tab()` → `_PLANS` 리스트가 정본이다.

**v9.x** (15개): 다층위협 프리셋 → 야간악천후 → 아군공격임무 → VLS고갈 → 현무-4 → 생존성히트맵 → 잠수함기습 → 헬기대잠 → P-8A → 전자전강화 → 채프플레어 → 이지스어쇼어 → 지형환경 → 해협시나리오 → 교전후브리핑

**v10.x** (3개): 완전 양방향 교전 → 적 항모 타격 작전 → 전술 의사결정 모드
