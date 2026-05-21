# 이지스 기동전단 통합 방어 시뮬레이터 — 프로젝트 규칙

## 프로젝트 개요

한국 해군 이지스 기동전단의 다층 방어 시뮬레이터. 대공·대함·대잠 위협에 대한 교전 시뮬레이션, 몬테카를로 분석, 요구조건(REQ) 판정, Excel/PNG 보고서 생성을 수행한다.

**현재 버전: v6.8.4**

### 파일 구조

| 파일 | 역할 |
|------|------|
| `import_matplotlib_v6_8_4.py` | 시뮬레이션 엔진 (DB, 물리모델, 교전 로직, 출력) |
| `Dashboard_v6_8_4.py` | Streamlit 실시간 대시보드 |

### 실행 방법

```
# 대시보드 실행
python -m streamlit run Dashboard_v6_8_4.py

# 엔진 단독 실행
python import_matplotlib_v6_8_4.py
```

### 필수 패키지

```
pip install matplotlib numpy scipy openpyxl pillow streamlit pandas
```

---

## 버전 관리 규칙

### 버전 체계

```
v{major}.{minor}.{patch}

major : 엔진 전면 재설계 (v7.0 = 양방향 교전 엔진 + PyQt6 UI)
minor : 신기능 추가 (NEW-X 레이블)
patch : 버그 수정 전용
```

### 파일 이름 규칙

버전이 바뀌면 **파일명도 함께 변경**한다.

```
import_matplotlib_v6_8_4.py  →  import_matplotlib_v6_8_5.py
Dashboard_v6_8_4.py          →  Dashboard_v6_8_5.py
```

Dashboard는 반드시 엔진 파일과 버전을 맞춘다. Dashboard 상단 import 경로도 함께 수정한다.

```python
from import_matplotlib_v6_8_5 import (...)   # 버전 동기화
```

### 헤더 주석 규칙

엔진 파일 최상단 헤더에 변경 이력을 누적 기록한다.

```python
"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   이지스 기동전단 통합 방어 시뮬레이터  v6.8.5                              ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  [v6.8.5 — 변경 내용 한 줄 요약]                                            ║
║                                                                              ║
║  BUG-X  수정 내용                                                            ║
║  NEW-X  추가 기능                                                            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""
```

파일 맨 아래 변경 이력 주석 블록에도 해당 버전 항목을 추가한다.

```python
# ── v6.8.5 패치 ──────────────────────────────────────────────────────────────
# · BUG-X: 수정 내용
# · NEW-X: 추가 기능
```

### 레이블 규칙

| 레이블 | 의미 |
|--------|------|
| `NEW-A`, `NEW-B`, ... | 신기능 (알파벳 순서로 누적) |
| `BUG-1`, `BUG-2`, ... | 버그 수정 (버전 내 번호 재시작) |
| `미구현-N` | 발견된 미구현 항목 (수정 시 헤더에 명시) |
| `DEAD-N` | 데드코드 정리 |

### Git 커밋 규칙

버전이 완성될 때마다 커밋한다.

```
커밋 메시지 형식:
v6.8.5: [변경 내용 한 줄 요약]

예시:
v6.8.5: 양방향 교전 초기 구현 (적 SM-2 요격 로직)
v6.8.5 patch: HeloEvent.xxx 오류 수정
```

작업 중간 상태는 커밋하지 않는다. 기능 단위로 완성 후 커밋한다.

---

## 코드 규칙

### DB 구조 원칙

- `ENEMY_DB` : 적군 32종. 신규 추가 시 `normalize_enemy_db()`가 누락 필드를 자동 보완하므로 필수 필드만 정의해도 된다.
- `FRIENDLY_DB` : 아군 무기 8종. `pk_dist`는 Beta 분포 파라미터(`alpha`, `beta`, `mean`).
- `SHIP_DB` / `FLEET_PRESETS` : 아군 함정·편대 스펙. 실제 한국 해군 함명 사용.
- `FRIENDLY_AIRCRAFT_DB` : 함재 헬기·해상초계기. `base_type='ship'` 또는 `'land'` 구분.

### 신기능 추가 시 체크리스트

1. `ENEMY_DB` / `FRIENDLY_DB` 등 DB 수정이 있으면 `normalize_enemy_db()` 확인
2. 새 이벤트 클래스(HeloEvent 등) 추가 시 `_id_counter` 리셋 로직 필수 (`run_single_sim` 진입부)
3. `HeloEvent`에 접근하는 모든 속성은 `getattr(ev, 'attr', default)` 패턴 사용 (ThreatEvent와 인터페이스 혼용 환경)
4. 신기능은 `enable_xxx` 플래그로 ON/OFF 가능하게 만든다 (하위 호환 유지)
5. Dashboard import 목록에 새 심볼 추가

### 하위 호환 원칙

- `enable_fleet=False` 시 기존 단독함 엔진이 100% 그대로 동작해야 한다.
- 전역 DB(`ENEMY_DB` 등)를 시뮬레이션 실행 중 직접 수정하지 않는다. 대신 로컬 사본(`dict(enemy_info)`)을 만들어 사용한다 (BUG-3 선례).

### 물리 모델 주요 함수

| 함수 | 역할 |
|------|------|
| `dynamic_kinematic_pk()` | 운동학적 Pk 보정 (ECM·종말회피·HGV·QBM 포함) |
| `calculate_detect_range_by_rcs()` | RCS 기반 탐지거리 계산 |
| `max_allowed_cd()` | 최대 허용 C&D 시간 계산 |
| `normalize_enemy_db()` | ENEMY_DB 누락 필드 자동 설정 (파일 로드 시 1회 실행) |

---

## 향후 계획

| 순위 | 버전 | 계획 | 난이도 |
|------|------|------|--------|
| 1 | v7.0 | 완전 양방향 교전 엔진 (적도 아군 미사일 요격) | 매우 높음 |
| 2 | v7.0 | PyQt6 네이티브 UI 전환 (런처·애니메이션·CPU/RAM 모니터링) | 매우 높음 |
| 3 | v7.x | 지형·해상 환경 모델 (DEM/수온층 데이터 연동) | 높음 |

**전환 전략**: v6.x는 Streamlit 유지 + 엔진 개발 집중. 양방향 엔진 완성 시점에 PyQt6 UI 병행 개발 시작.
