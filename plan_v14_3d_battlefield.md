# v14.1 — 3D 전장 + 실제 지도 (CesiumJS) 설계

> 상태: **설계 합의 완료 + 코드 검증 완료 (2026-06-11), 구현 미착수**
> 난이도: 매우 높음 · 모델: Opus 4.8 · 코드리뷰: `/code-review high`

---

## 1. 목표 & 확정 방향

시뮬레이션 결과를 **실제 위성 지구본 위에서 시간순 리플레이**로 보여주는 '3D 전장' 탭 신설.

| 항목 | 결정 |
|------|------|
| 렌더링 | **CesiumJS** (실제 위성영상 지구본 + 실측 지형) |
| 지형 소스 | **Cesium ion 무료 티어** (API 키 필요, Bing 위성영상 + World Terrain) |
| PyQt6 통합 | **`QWebEngineView`** 임베드 → 기존 결과 탭 스택에 '3D 전장' 페이지 추가 (별도 앱 아님) |
| 온라인 | **인터넷 연결 허용** (지형 타일 온라인 의존 OK) |
| 재생 방식 | **리플레이** — 시뮬 종료 후 CZML로 타임라인 스크럽 재생 (실시간 스트리밍 아님) |
| 데이터 연동 | 시뮬 결과 `frames` → **CZML(JSON)** 변환 → JS(Cesium)에 전달, 시간 동역학 재생 |

### 게임 엔진을 안 쓰는 이유 (재논의 방지)
언어·런타임 단절(C++/C#), PyQt6 임베드 불가(별도 창), 빌드 파이프라인 이중화, 유지보수 2배.
파이썬 분석 엔진이 본질이고 3D는 표현 레이어 → 임베드 가능한 웹 스택(Cesium)이 정답.
PyVista 탈락 = 오프라인 자립이 불필요해짐(온라인 허용)에 따라 실제 위성 지구본 품질을 택함.

---

## 2. 단계 배분 (MVP 우선)

| 버전 | 범위 |
|------|------|
| **v14.1 (MVP)** | 지구본 + 함정·항공기 위치 + 미사일 궤적 + **교전 이벤트 마커** + 타임라인 리플레이 |
| v14.2 | 레이더·SAM 커버리지 돔 (반투명 돔/원뿔, 지형 차폐) |
| v14.3 | 고도화 — 3D 함정 모델, 카메라 프리셋, 지형 차폐 정밀화 |

---

## 3. ⭐ 코드 검증 결과 (2026-06-11) — 데이터 파이프라인 이미 90% 존재

깊이 조사 결과, **v14.1에 필요한 데이터가 엔진에 거의 다 준비돼 있다.** 당초 "위치 히스토리 기록을 새로 추가"가 핵심 작업일 줄 알았으나 **이미 있음** → 엔진 신규 작업 최소화 = 회귀 위험 최소.

| 필요 요소 | 코드 현황 | 위치 |
|-----------|-----------|------|
| 시간별 위치 히스토리 | ✅ **`frames`(`SimFrame` 리스트) 이미 완비.** 매 틱 `_record_frame()` 기록 | `engine_v7.py:3853`, `_compile` 반환 키 `frames` |
| MC 메모리 가드 | ✅ **`if not self._mc_mode:` 안에서만 기록** — 단일 시뮬만 누적(정확히 필요한 동작). `enable_track_history` 플래그 **불필요** | `engine_v7.py:4087` |
| 미사일 탄도 곡선 고도 | ✅ **`_missile_disp_alt()` "3D 시각화용" 함수가 이미 존재** (탄도·HGV 포물선 보간 `4·peak·p·(1-p)`). frames에 이 값 저장됨 | `engine_v7.py:3875` |
| 좌표 → 실제 위경도 | ✅ `LatLon.from_xy(x,y)` + 실제 한반도 해역 기준점 | `engine_v7.py:693`, `_REGION_REF`(동해/서해/대한해협) |
| 객체 식별자 | ✅ `M0001`(미사일)·`ET001`(적) uid 체계, `_id_counter` 리셋 로직 존재 | `engine_v7.py:764,903` |
| 시간 해상도 | ✅ `DT=1.0`초 (Cesium 시간보간으로 충분히 부드러움) | `engine_v7.py:137` |

### SimFrame 구조 (CZML 변환 입력)
```
frame.t              : float (시각, 초)
frame.friendly_ships : [(name, x, y, alive, hp, radar_f, speed_f, disabled수)]   # 함정 고도=해수면 0
frame.enemy_ships    : [(uid, preset, x, y, alive, hp, alt_m)]
frame.missiles       : [(uid, x, y, mtype, name, disp_alt_m)]                     # disp_alt=탄도 포물선 반영
frame.events         : [str]                                                       # 틱 이벤트(문자열)
```

---

## 4. ⭐ 진짜 작업·리스크 = QtWebEngine 통합/빌드 (무게중심 이동)

엔진 데이터가 준비돼 있으므로 난이도의 무게중심이 **"엔진 생성"이 아니라 "웹 통합·빌드"** 로 이동. 좋은 소식(회귀 위험 격리)이자, 동시에 **최대 관문**.

### 🚨 핵심 리스크: QtWebEngine
- **현재 미설치**: `from PyQt6.QtWebEngineWidgets import QWebEngineView` → `ModuleNotFoundError`. PyQt6 6.11.0은 있으나 **`PyQt6-WebEngine` 별도 설치 필요** (`pip install PyQt6-WebEngine`).
- **PyInstaller 번들링이 악명 높게 까다로움**: `QtWebEngineProcess.exe`, `resources/*.pak`, `locales/`, ICU(`icudtl.dat`) 누락 시 **exe에서 지구본 빈 화면**. `launcher.spec`에 datas/binaries/hiddenimports 보강 필수.
- **exe 용량 +수백 MB** (사용자 합의: "무거워도 제대로").
- **검증 필수**: 빌드 후 반드시 **스모크 실행으로 지구본 타일 로드 확인** (개발 중 `python launcher.py`는 떠도 exe는 빈 화면 가능 — 번들링 누락 전형).

---

## 5. 수정/추가 파일 목록

| 파일 | 변경 | 비고 |
|------|------|------|
| `launcher.py` | '3D 전장' 탭(`QWebEngineView`) 추가 · `_build_czml(result)` 변환 함수 · 결과→`runJavaScript` 전달 · import에 `QWebEngineView` 추가 | 주작업 |
| `cesium_view.html` (신규) | CesiumJS 뷰어. `Cesium.Viewer` + `CzmlDataSource` + 타임라인·카메라 | 신규 |
| `launcher.spec` | `cesium_view.html` datas + **QtWebEngine 번들링 보강**(hiddenimports·data) | 빌드 핵심 |
| `engine_v7.py` | **변경 거의 없음** — `frames` 그대로 사용. (필요 시 frame.events에 위치 동반하도록 소폭 보강 검토) | 회귀 위험 최소 |
| 필수 패키지 문서 | `PyQt6-WebEngine` 추가 (CLAUDE.md 필수 패키지·pip 목록) | |

> ⚠️ `engine_v7.py`를 건드리면 `verify_regression.py` 변경 전 PASS → 변경 후 재실행. frames 사용은 순수 읽기라 회귀 영향 없어야 정상.

---

## 6. `_build_czml()` 변환 구조 (개략)

```
result['frames']  (SimFrame 리스트)
   │  uid별로 시계열 재구성:  uid → [(t, x, y, alt, alive), ...]
   │  x,y → LatLon.from_xy → (lon, lat),  alt = disp_alt_m
   ▼
CZML packets:
  - document packet { clock: {interval, currentTime, multiplier} }   ← 타임라인/스크럽
  - 함정/항공기: position(시간보간 cartographicDegrees) + billboard/label + path(궤적)
  - 미사일:      position + polyline(궤적, mtype별 색) + 끝점 이벤트 마커
                 · 마커 위치 = 해당 uid가 마지막 alive였던 프레임의 (x,y)
                 · 색/아이콘 = intercepted(녹) / 명중(적) / 자멸 — _build_active_events 또는 미사일 상태로 판정
   ▼
QWebEngineView.page().runJavaScript(f"loadCzml({json.dumps(czml)})")
   ▼
cesium_view.html:  viewer.dataSources.add(Cesium.CzmlDataSource.load(czml))
```

---

## 7. 미해결 / 착수 전 확정 사항

- [ ] **Cesium ion API 키 발급** (사용자) — [cesium.com/ion](https://cesium.com/ion) 무료 티어. 키 저장 위치: 하드코드 vs 설정 파일 (결정 필요)
- [ ] **이벤트 마커 데이터 경로** 확정: frame.events(문자열)엔 위치 없음 → frames의 미사일 alive→dead 전이 위치 + intercepted 플래그로 마커 생성 (엔진 보강 없이 가능할 듯)
- [ ] **잠수함·어뢰 음수 고도**(수심) 표현 방식 — Cesium 해수면 아래는 가시성 낮음. 수면 투영 vs 반투명 vs 생략 판단
- [ ] **카메라 초기 위치** — 시나리오 해역(`_REGION_REF`) 중심으로 자동 줌
- [ ] PyInstaller QtWebEngine 번들링 실검증 (소형 PoC exe로 먼저 타일 로드 확인 권장)

---

## 8. 권장 착수 순서 (리스크 선행 격리)

1. **PoC: QtWebEngine 빌드 검증** — `pip install PyQt6-WebEngine` → 빈 Cesium 페이지를 QWebEngineView에 띄우는 최소 exe를 먼저 빌드해 **타일 로드 확인**. (최대 리스크를 가장 먼저 제거)
2. `_build_czml()` 변환 + cesium_view.html (개발 모드 `python launcher.py`에서 함정·궤적·마커 재생 확인)
3. '3D 전장' 탭 통합 + 타임라인 UI
4. 전체 빌드 + 스모크 실행(지구본 타일 로드 필수 확인) + `verify_regression.py`(엔진 보강 시)
