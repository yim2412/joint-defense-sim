"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   이지스 기동전단 통합 방어 시뮬레이터  v7.42 — PyQt6 런처                 ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  [v7.42 — 분석 고도화 + 시뮬레이션 모드 선택 UI]                            ║
║  NEW-A  시뮬레이션 모드 선택 (빠름 5,000회 / 표준 10,000회 / 정밀 100,000회)║
║  NEW-B  LHS 샘플링 + CVaR(최악 5%) 카드 — 불확실 파라미터 5종 반영          ║
║  NEW-C  스트레스 테스트 탭 — 채널 감소 × 레이더 성능 감소 2D 히트맵         ║
║  NEW-D  Sobol 민감도 분석 탭 — 정밀 모드 전용 (~32,768회)                   ║
║                                                                              ║
║  [v7.41 — DB 탭 개편 + 설명 텍스트 간소화]                                  ║
║  NEW-A  적군/아군 DB 탭을 전투기·함정·무기·잠수함·항공 세부 탭으로 분리      ║
║  NEW-B  무기 탭 내 대공·대함·대잠 색상 구분 범례 추가                        ║
║  NEW-C  기능 목록·향후 계획 설명 텍스트 전문용어 없이 쉬운 말로 재작성       ║
║                                                                              ║
║  [v7.38 — 함정 DB Batch 세분화]                                               ║
║  NEW-A  KDX-III → Batch I (세종대왕급, SM-3 없음) / Batch II (정조대왕급)    ║
║  NEW-B  FFX → Batch I (인천급) / Batch II (대구급, 해궁 추가) / Batch III    ║
║  NEW-C  FRIENDLY_DB: 해궁 (K-SAAM) 추가                                      ║
║  NEW-D  FLEET_PRESETS 전 프리셋 타입 키 갱신 + 전 이지스 기동전단 프리셋 추가║
║  NEW-E  spec_db: KDX-III-B1/B2, FFX-I/II/III 상세 스펙 각각 분리             ║
║                                                                              ║
║  [v7.37 — 전체 차트 고화질 + 폰트 확대]                                      ║
║  NEW-A  CHART_DPI 자동 감지: 화면 크기 기반 min 150 ~ max 300 DPI 설정       ║
║  NEW-B  정적 차트 13종 fontsize +3 일괄 증가 (8→11, 9→12, 11→14 등)          ║
║  NEW-C  MC 통계(plot_v7) fontsize +3, suptitle 13→16                         ║
║  NEW-D  애니메이션 프레임 dpi 120→150, 레이블·범례 폰트 +2                   ║
║  NEW-E  REQ 판정 탭: 요구조건 상단 / 취약점 진단 하단 배치 + 카드 크게       ║
║                                                                              ║
║  [v7.36 — 애니메이션 자막 진동 수정]                                         ║
║  BUG-1  lbl_events setWordWrap → setFixedHeight(28): 텍스트 변경 시           ║
║         캔버스 크기 변동(진동) 방지                                           ║
║                                                                              ║
║  [v7.35 — 종합 버그 감사 수정]                                               ║
║  BUG-1  PDF 보고서 MC 차트 누락: 삭제된 tmp 파일 참조 → _raw_bytes 직접 사용 ║
║  BUG-2  _on_frame_ready: idx 범위 초과 방어 코드 추가                        ║
║  BUG-3  load_frames: 재생 중 새 시뮬 로드 시 타이머·플래그 미초기화 수정     ║
║  BUG-4  _stop_sys_data_worker: None 중복 할당 제거                           ║
║                                                                              ║
║  [v7.34 — 전장 애니메이션 렉·프리즈 수정]                                   ║
║  BUG-1  _start_render_worker: cancel 후 wait() → 메인 스레드 블로킹 수정    ║
║         세대 카운터(_render_gen)로 구식 frame_ready 신호 필터링              ║
║  BUG-2  FrameRenderWorker: 10프레임마다 msleep(12) → 신호 폭주 방지         ║
║  BUG-3  _draw_frame: 재생 중 FastTransformation, 정지 시 Smooth             ║
║                                                                              ║
║  [v7.33 — 차트 렌더링 전면 최적화 (메인 스레드 matplotlib 제거)]             ║
║  BUG-1  tab_sensitivity·tab_min_stock: MplCanvas(메인스레드) →               ║
║         ChartPageWidget(백그라운드) + 순수 렌더 함수 분리                    ║
║  BUG-2  SysMonitorTab: 숨김 상태서 matplotlib 렌더 스킵 + showEvent 즉시 갱신║
║  BUG-3  시스템 모니터 타이머 1초 → 2초 (메인 스레드 matplotlib 부하 감소)   ║
║  BUG-4  _fill_log: processEvents() 제거 (setUpdatesEnabled 배치로 충분)      ║
║                                                                              ║
║  [v7.32 — 창 닫기 시 좀비 프로세스 완전 제거]                               ║
║  BUG-1  ChartRenderWorker 11개 closeEvent 미처리 → stop_worker() 추가       ║
║  BUG-2  WeatherWorker closeEvent 누락 → 날씨 비교 중 닫아도 즉시 종료       ║
║  BUG-3  ProcessPool shutdown 순서: None 먼저 설정 → 새 작업 제출 차단       ║
║  BUG-4  _stop_sys_data_worker: terminate 폴백 + closeEvent 직접 호출         ║
║                                                                              ║
║  [v7.31 — 결과 화면 탭 전환 시 UI 프리즈 수정]                              ║
║  BUG-1  SensitivityWorker·MinStockWorker 즉시 기동 → GIL 독점으로 프리즈    ║
║         → lazy-start: 감도 분석·최소 재고 탭 방문 시에만 워커 시작          ║
║  BUG-2  MC 통계 차트 이중 렌더(plot_v7→PNG→Figure→PNG) → bytes 직접 반환   ║
║                                                                              ║
║  [v7.30 — 결과 패널 MC 통계 미표시 버그 수정]                               ║
║  BUG-1  사이드바 row 1 유지 시 setCurrentRow(1) 신호 미발화 → 수동 트리거   ║
║                                                                              ║
║  [v7.29 — DB 스펙 패널 폰트 확대]                                           ║
║  NEW-1  SpecSheetPanel 제목 14→16px, 부제·카테고리·레이블·값 11→13px,       ║
║         비고 12→14px, 행간격 확대                                            ║
║                                                                              ║
║  [v7.28 — 시스템 모니터 버그 수정 + 향후 계획·changelog 갱신]              ║
║  BUG-1  시뮬 실행 중 오버레이 미표시 수정 (_sim_start_idx→벽시계 기반)      ║
║  BUG-2  코어별 퍼센트 폰트 크기 10px→12px (가독성 개선)                    ║
║  NEW-1  changelog.json v28 항목 추가                                        ║
║  NEW-2  향후 계획 탭 — 완료된 아군 잠수함 항목 제거 (v7.27 구현 완료)       ║
║                                                                              ║
║  [v7.27 — 아군 잠수함 추가 (KSS-I/II/III)]                                  ║
║  NEW-A  SHIP_DB: KSS-I 장보고급·KSS-II 류관순급·KSS-III 도산안창호급 추가  ║
║  NEW-B  engine_v7: 아군 잠수함 공격 로직 (수상함·적잠수함 어뢰/미사일)      ║
║  NEW-C  FRIENDLY_STRIKE_DB: 현무-3C 순항미사일 추가 (KSS-III VLS 전용)      ║
║  NEW-D  FLEET_PRESETS: 대잠전단 프리셋 (KDX-III + FFX×2 + KSS-II×2) 추가  ║
║  NEW-E  spec_db: KSS-I/II/III 상세 스펙 + 아군 DB 탭 사진 표시              ║
║                                                                              ║
║  [v7.26 — DB 탭 스펙 설명창 폰트 크기 확대]                                 ║
║  NEW-A  카테고리 헤더·레이블·값 9px → 11px, 비고 10px → 12px               ║
║                                                                              ║
║  [v7.25 — 설정 패널 정리: 고정값 전환 + 프로필·시나리오 기능 삭제]          ║
║  DEL-A  설정 프로필 섹션 완전 삭제 (UI + 메서드 6개)                        ║
║  DEL-B  시나리오 저장/불러오기 섹션 완전 삭제 (UI + 메서드 2개)             ║
║  NEW-A  함정 위치 랜덤 배치 항상 활성화 고정 (반경 10km)                    ║
║  NEW-B  C&D 시간 10초·확인 3초 하드코딩 / MC 1000회 고정                   ║
║                                                                              ║
║  [v7.24 — 향후 계획 탭 재정렬 + 아군 잠수함 항목 추가]                      ║
║  NEW-A  아군 잠수함 (KSS-I/II/III) 항목 신규 추가 — 1순위                  ║
║  NEW-B  12개 항목 최적 우선순위 재정렬                                       ║
║                                                                              ║
║  [v7.23 — DB 탭 필터 버튼 동작 + 좌우 분할 레이아웃 + 가로 사진]           ║
║  NEW-A  대공·대함·대잠 필터 토글 버튼 — 실시간 목록 필터링 + N종 카운터   ║
║  NEW-B  DB 탭 좌우 분할 (230px 이름 목록 + 우측 스펙 패널)                 ║
║  NEW-C  SpecSheetPanel 가로 사진 (전폭 175px 고정 높이)                     ║
║                                                                              ║
║  [v7.22 — spec_db 전 항목(85종) categories 구조 변환 완료]                  ║
║  NEW-A  아군 무기 13종: 5카테고리 (기본정보/물리적제원/성능/추진/유도·탄두) ║
║  NEW-B  아군 함정 15종: 6카테고리 (기본정보/제원/성능/추진/무장/센서)       ║
║  NEW-C  적군 전 항목 57종: 카테고리 구조 통일 (미사일·항공기·함정·잠수함)  ║
║                                                                              ║
║  [v7.21 — 아군 무기 스펙 상세화 + exe 이미지 번들 수정]                     ║
║  BUG-1  exe 빌드 시 assets/images 미포함 → launcher.spec 수정               ║
║  BUG-2  이미지 경로 _res() 함수 미사용 → exe 환경 경로 오류 수정            ║
║  NEW-A  spec_db: 아군 무기 13종 필드 4→6개 확장 (교전고도·탄두중량 등)     ║
║                                                                              ║
║  [v7.20 — 드론 DB 제거 + 창 레이아웃 개선 + normalize_enemy_db 연결 수정]  ║
║  DEL-A  소형 자폭 드론·드론 떼 전 파일 제거 (engine/engine_v7/spec_db)      ║
║  BUG-3  engine_v7: normalize_enemy_db import 누락 수정                      ║
║  BUG-4  설정 패널 수평 스크롤 제거 (430px 고정 + ScrollBarAlwaysOff)        ║
║                                                                              ║
║  [v7.18 — 미확인 전력 4종 DB 제거]                                          ║
║  DEL-A  095형·039C형 잠수함, CM-302, 수중자폭드론 — 실전 배치 미확인        ║
║                                                                              ║
║  [v7.17 — DB 탭 스펙시트 패널: 적군 63종·아군 15함정·13무기 상세 카드]     ║
║  NEW-A  spec_db.py: 91개 유닛 상세 스펙 DB (제원·원산국·비고)              ║
║  NEW-B  SpecSheetPanel: 사진/아이콘 + 제원 그리드 (고정 172px 하단 패널)   ║
║  NEW-C  적군 DB 탭: QSplitter + SpecSheetPanel (유닛 선택 시 즉시 표시)    ║
║  NEW-D  아군 DB 탭: 무기·함정 서브탭 각각 SpecSheetPanel 적용              ║
║                                                                              ║
║  [v7.16 — DB 대규모 확장 1차: 적군 19종·미군 7함정·3무기·한미연합 3프리셋]  ║
║  NEW-A  적군 DB 43→63종: 중국 7종·러시아 8종·북한 4종 신규 추가            ║
║  NEW-B  아군 SHIP_DB: DDG-51/CG-47/CVN/LPD/SSN + LST/AO 7함정 추가        ║
║  NEW-C  FRIENDLY_DB: ESSM Block II·SM-6 Block IB·Tomahawk Block V 추가     ║
║  NEW-D  한미 연합 프리셋 3종: 기본·강화·항모전단 지원                       ║
║  NEW-E  엔진: ESSM/SM-6IB 무기 선택 레이어 + Tomahawk 대함 타격 지원       ║
║                                                                              ║
║  [v7.15 — 자동 취약점 진단 카드]                                            ║
║  NEW-A  diagnose_vulnerabilities_v7(): 6종 규칙 기반 취약점 자동 탐지      ║
║  NEW-B  REQ 판정 탭 상단에 진단 카드 패널 (HIGH/MED/LOW/OK 색상 구분)      ║
║  NEW-C  개선 제안 자동 생성: 소진 무기→재고 증량, 채널 포화→CEC 활성화 등  ║
║                                                                              ║
║  [v7.14 — REQ 달성 최소 재고 역산 + '🔬 최소 재고' 탭 신설]               ║
║  NEW-A  find_min_stock_v7(): 이진 탐색으로 무기별 최소 함정당 재고 계산    ║
║  NEW-B  MinStockWorker: 백그라운드 역산 + 진행상황 상태바 표시             ║
║  NEW-C  '🔬 최소 재고' 탭: 현재/최소 비교 수평 막대 차트 (절약·부족 구분) ║
║                                                                              ║
║  [v7.13 — 드론 떼(Swarm) 전술 세부화 + 자폭 피격 수정]                     ║
║  NEW-A  '드론 떼 (Swarm-12)' DB 추가: 12기 그룹, RAM 1발 = 2~5기 제압     ║
║  NEW-B  자폭 드론 피격 수정: 200m 이내 도달 시 함정 피격 처리              ║
║  NEW-C  스웜 전용 무기 선택: RAM/CIWS 우선, SAM 낭비 금지                  ║
║                                                                              ║
║  [v7.12 — 혼합 공격 시나리오 7종 + 파도별 지연 스폰]                       ║
║  NEW-A  MIXED_ATTACK_SCENARIOS 7종: 순항+탄도+드론, 러시아 살라미, 북한 등 ║
║  NEW-B  파도 타이밍(wave_offset_s): 위협이 delay_s 시점에 순차 출현        ║
║  NEW-C  launcher 혼합 시나리오 모드 UI: 드롭다운 + 파도 구성 미리보기      ║
║                                                                              ║
║  [v7.11 — 한국 해군 함정 8종 추가 + 현실 기반 편대 프리셋 5종 신설]       ║
║                                                                              ║
║  NEW-1  시뮬 seed numpy 동시 고정 (random + np.random.seed) — 완전 재현    ║
║  NEW-2  결과 화면 사용된 시드 표시 — 재현 시 동일 값 입력 안내             ║
║  NEW-3  YJ-21 극초음속 대함탄도미사일 추가 (Mach 10+, 1500km, HGV)        ║
║  NEW-4  YJ-18 초음속 대함미사일 시나리오 교체 (항모 킬 체인 3파)          ║
║  NEW-5  해성-3 잠수함발사 순항미사일 추가 (북한 SLCM, 1500km+)            ║
║  BUG-1  날씨 비교 UI 프리즈 수정: WeatherWorker(QThread) 비차단 실행       ║
║  BUG-2  update_status 조건 오류 수정: or "/" → or "/" in msg               ║
║  BUG-3  요격률 레이블 너비 52→68px (100.0% 텍스트 잘림 방지)              ║
║  DEAD-1 _draw_tactical / _draw_topdown 데드코드 제거                        ║
║                                                                              ║
║  [v7.8 — 결과 차트 UI 프리즈 완전 해결]                                    ║
║                                                                              ║
║  NEW-1  ChartRenderWorker(QThread): 차트 13개를 백그라운드에서 PNG 렌더     ║
║  NEW-2  ChartPageWidget: 로딩 → 이미지 전환, 리사이즈 자동 스케일          ║
║  BUG-1  render_map 인덱스 오류 수정 (12~17 → 12~16, 방위각~이전비교)       ║
║  BUG-2  _page_dirty에서 없는 인덱스 17 제거                                ║
║  BUG-3  감도 분석 draw() → draw_idle() 전환                                ║
║                                                                              ║
║  [v7.7 — 향후 계획 탭 전면 업데이트 (20개 항목)]                           ║
║                                                                              ║
║  NEW-1  향후 계획 탭: 2개 → 20개 항목으로 확장                             ║
║         P2~P21 전체 로드맵 반영 (차트 프리즈, 코드 감사, 적 DB,            ║
║         seed 고정, 랜덤 배치, 도움말, 기록 DB, REQ 역산,                   ║
║         취약점 진단, 최적 조합, Swarm, ARM, 혼합 시나리오,                 ║
║         중국 항모전단, 연합 작전, 해협 방어, 피해 세분화, 레이더 모드,    ║
║         양방향 교전, 지형·해상 환경)                                        ║
║                                                                              ║
║  [v7.6 — FloatingMonitor 개선]                                              ║
║                                                                              ║
║  NEW-1  단계 표시: "1/2 단일 시뮬 실행 중…" → "2/2 MC 분석 중…"            ║
║  NEW-2  경과 시간 타이머 (show() 시점 기준 실시간 카운트업)                 ║
║  NEW-3  라이브 요격률 게이지 — 배치마다 색상 변화 (빨강↔주황↔초록)         ║
║  NEW-4  격추/피격 평균 카운터 실시간 표시                                   ║
║  NEW-5  배치 스파크라인 — 12칸 컬러 사각형 수렴 추이                        ║
║  NEW-6  워커 프로세스 수 표시 (_SYS_CACHE 기반)                             ║
║  NEW-7  시뮬 시작 시 시스템 모니터 탭 자동 전환                             ║
║  NEW-8  rate_update 시그널 (SimWorker → FloatingMonitor) 연결               ║
║                                                                              ║
║  [v7.5 — CPU 우선순위 조정]                                                 ║
║                                                                              ║
║  BUG-1  _set_pool_priority(): 워커 프로세스 BELOW_NORMAL (psutil)           ║
║         글로벌 풀 예열 후 + 인라인 풀 생성 시 즉시 적용                    ║
║  BUG-2  SimWorker / SensitivityWorker / FrameRenderWorker                   ║
║         QThread.Priority.LowPriority 로 시작                                ║
║                                                                              ║
║  [v7.4 — Freeze/응답없음 수정]                                              ║
║  BUG-1  canvas.draw() → draw_idle() 전체 교체 (UI 스레드 블로킹 제거)      ║
║  BUG-2  로그 테이블 최대 300행 제한 + setUpdatesEnabled + processEvents     ║
║  BUG-3  탭 전환 200ms 디바운스 (QTimer, 빠른 연속 클릭 시 마지막만 렌더)   ║
║  BUG-4  차트 캐시 — 동일 result 객체 재렌더 스킵 (id 기반)                 ║
║                                                                              ║
║  [6단계 — PyQt6 네이티브 UI / 포팅 A+B]                                    ║
║                                                                              ║
║  NEW-A  MainWindow: 좌/우 분할 레이아웃 (설정 패널 + 결과 탭)               ║
║  NEW-B  ConfigPanel: 엔진 선택·적군 편대·아군 편대·무기 재고·MC 설정        ║
║  NEW-C  SimWorker(QThread): 백그라운드 시뮬 (UI 블로킹 없음)                ║
║  NEW-D  전장 애니메이션 탭: matplotlib 2.5D 등각투영 + QSlider 재생         ║
║  NEW-E  MC 통계 탭: plot_v7 차트 임베드                                     ║
║  NEW-F  교전 로그 탭: QTableWidget 시각별 이벤트                            ║
║  NEW-G  시스템 모니터 탭: CPU·RAM·스레드 실시간 (psutil + QTimer)           ║
║  NEW-H  포팅 A — 방어 무기 재고 UI (SM-3~Mk.46·기만기)                     ║
║  NEW-I  포팅 A — 적군 모드 선택 (커스텀/프리셋/랜덤) + 프리셋·난이도 UI    ║
║  NEW-J  포팅 B — 전술 옵션 토글 (ECM·회피·기만기·자체방어 QCheckBox)       ║
║  NEW-K  포팅 C — 항공 자산 토글 (AW-159·P-3C·P-8A QCheckBox, 대잠 전용)   ║
║                                                                              ║
║  실행: python launcher.py                                                    ║
║  패키지: pip install PyQt6 psutil matplotlib numpy openpyxl                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import sys, os, io, time, threading, json, multiprocessing, subprocess as _sp
from concurrent.futures import ProcessPoolExecutor, as_completed
import psutil

# ── GPU / CPU 온도 헬퍼 ──────────────────────────────────────────────────────
_wmi_inst = None   # lazy-init

def _get_gpu_info() -> dict:
    """nvidia-smi로 GPU 정보 수집. 실패 시 빈 dict 반환."""
    try:
        out = _sp.check_output(
            ['nvidia-smi',
             '--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu',
             '--format=csv,noheader,nounits'],
            timeout=1, stderr=_sp.DEVNULL,
            creationflags=_sp.CREATE_NO_WINDOW)
        p = [x.strip() for x in out.decode().strip().split(',')]
        return {'util': int(p[0]), 'mem_used': int(p[1]),
                'mem_total': int(p[2]), 'temp': int(p[3])}
    except Exception:
        return {}

def _get_cpu_temp() -> float:
    """CPU 온도(°C). WMI 사용. 실패 시 -1 반환."""
    global _wmi_inst
    if _wmi_inst is None:
        try:
            import wmi
            _wmi_inst = wmi.WMI(namespace="root\\wmi")
        except Exception:
            _wmi_inst = False
    if not _wmi_inst:
        return -1.0
    try:
        zones = _wmi_inst.MSAcpi_ThermalZoneTemperature()
        if zones:
            return zones[0].CurrentTemperature / 10.0 - 273.15
    except Exception:
        _wmi_inst = None
    return -1.0

# ── 글로벌 프로세스 풀 (앱 시작 시 예열, 시뮬 내내 재사용) ──────────────────
_GLOBAL_POOL: 'ProcessPoolExecutor | None' = None
_PERF_HISTORY: list = []   # 최근 시뮬 성능 기록 (최대 10개)

# 시스템 모니터 캐시 — 백그라운드 워커가 채움, 메인 스레드는 읽기만
_SYS_CACHE: dict = {
    'cpu': 0.0, 'mem_pct': 0.0, 'mem_used': 0, 'mem_total': 1,
    'gpu': {}, 'cpu_temp': -1.0, 'cores': [], 'proc_ram': 0.0,
    'worker_stats': [], 'swap_used': 0, 'thread_cnt': 0,
}

def _init_global_pool():
    """앱 시작 시 백그라운드 스레드에서 호출 — 워커 프로세스 예열."""
    global _GLOBAL_POOL
    from anim_render import _warmup_task
    n = min(os.cpu_count() or 4, 8)
    _GLOBAL_POOL = ProcessPoolExecutor(max_workers=n)
    try:
        list(_GLOBAL_POOL.map(_warmup_task, range(n), timeout=60))
    except Exception:
        pass   # 예열 실패해도 풀 자체는 사용 가능
    _set_pool_priority(_GLOBAL_POOL)  # BUG-1: 워커 프로세스 BELOW_NORMAL

def _shutdown_global_pool():
    global _GLOBAL_POOL
    if _GLOBAL_POOL is None:
        return
    pool, _GLOBAL_POOL = _GLOBAL_POOL, None   # None 먼저 → 새 작업 제출 차단
    try:
        pool.shutdown(wait=False, cancel_futures=True)
    except Exception:
        try:
            pool.shutdown(wait=False)
        except Exception:
            pass
    # 풀 프로세스가 아직 살아 있으면 즉시 kill
    try:
        procs = getattr(pool, '_processes', {})
        pids = list(procs.keys()) if isinstance(procs, dict) else []
        for pid in pids:
            try:
                psutil.Process(pid).kill()
            except Exception:
                pass
    except Exception:
        pass

def _set_pool_priority(pool):
    """워커 프로세스 우선순위를 BELOW_NORMAL로 낮춤 — 시뮬 중 UI·다른 앱 응답성 유지."""
    # Windows: BELOW_NORMAL_PRIORITY_CLASS / Unix: nice=5
    _nice = getattr(psutil, 'BELOW_NORMAL_PRIORITY_CLASS', 5)
    try:
        # _processes는 ProcessPoolExecutor 내부 속성 — 없으면 자식 프로세스로 폴백
        procs = getattr(pool, '_processes', None) or {}
        pids  = list(procs.keys()) if isinstance(procs, dict) else []
        if not pids:
            pids = [c.pid for c in psutil.Process().children()]
        for pid in pids:
            try:
                psutil.Process(pid).nice(_nice)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except Exception:
        pass

def _res(filename: str) -> str:
    """PyInstaller exe 및 일반 실행 모두에서 리소스 파일 경로 반환."""
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, filename)


# ════════════════════════════════════════════════════════════════════════════
#  실행 로그 (sim_history.log 텍스트 + sim_history.json 구조화)
# ════════════════════════════════════════════════════════════════════════════
def _log_base() -> str:
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def _log_path()  -> str: return os.path.join(_log_base(), 'sim_history.log')
def _json_log_path() -> str: return os.path.join(_log_base(), 'sim_history.json')


def _write_log(line: str):
    try:
        with open(_log_path(), 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except Exception:
        pass


def _load_json_log() -> list:
    try:
        with open(_json_log_path(), encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


def _save_json_log(records: list):
    try:
        with open(_json_log_path(), 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _write_sim_log(cfg: dict, result: dict, mc: dict):
    from datetime import datetime
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    enemy_parts = [f"{e.get('preset','?')} ×{e.get('count',1)}"
                   for e in cfg.get('enemy_fleet', [])]
    enemy_str = ', '.join(enemy_parts) if enemy_parts else cfg.get('enemy_fleet_preset', '?')
    n = max(mc.get('n', 1), 1)
    avg_hits  = sum(mc.get('friendly_hits',  [])) / n
    avg_edest = sum(mc.get('enemy_destroyed', [])) / n

    # ── 텍스트 로그 ──────────────────────────────────────────────────────
    lines = [
        '=' * 80,
        f'[{now}]  시뮬레이션 완료',
        '-' * 80,
        f'  편대       : {cfg.get("fleet_preset", "?")}',
        f'  날씨       : {cfg.get("weather", "?")}',
        f'  MC 횟수    : {mc.get("n", 0)}회',
        f'  적군 구성  : {enemy_str}',
        '',
        f'  총 위협    : {result.get("total_threats", 0)}발/기',
        f'  요격률     : {mc.get("mean_intercept", 0):.1%}  (±{mc.get("std_intercept", 0):.1%})',
        f'  완전요격   : {mc.get("full_pass_rate", 0):.1%}',
        f'  아군 피격  : {avg_hits:.1f}회 (평균)',
        f'  적 격침    : {avg_edest:.1f}기/척 (평균)',
        f'  총 비용    : ${result.get("total_cost", 0):,.0f}',
        '=' * 80, '',
    ]
    try:
        with open(_log_path(), 'a', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')
    except Exception:
        pass

    # ── JSON 로그 ─────────────────────────────────────────────────────────
    record = {
        'datetime':       now,
        'fleet':          cfg.get('fleet_preset', '?'),
        'weather':        cfg.get('weather', '?'),
        'mc_n':           mc.get('n', 0),
        'enemy':          enemy_str,
        'total_threats':  result.get('total_threats', 0),
        'mean_intercept': round(mc.get('mean_intercept', 0), 4),
        'std_intercept':  round(mc.get('std_intercept', 0), 4),
        'full_pass_rate': round(mc.get('full_pass_rate', 0), 4),
        'avg_friendly_hits':    round(avg_hits,  2),
        'avg_enemy_destroyed':  round(avg_edest, 2),
        'total_cost':     result.get('total_cost', 0),
    }
    records = _load_json_log()
    records.append(record)
    _save_json_log(records)


from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDialog, QSplitter,
    QVBoxLayout, QHBoxLayout, QFormLayout, QScrollArea,
    QGridLayout, QFrame,
    QLabel, QPushButton, QComboBox, QSpinBox, QTabWidget,
    QTableWidget, QTableWidgetItem, QSlider, QProgressBar,
    QGroupBox, QStatusBar, QMessageBox, QHeaderView,
    QSizePolicy, QCheckBox, QFileDialog, QLineEdit,
    QListWidget, QListWidgetItem, QStackedWidget,
)
from PyQt6.QtGui import QFont, QColor, QPalette, QShortcut, QKeySequence, QPixmap
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer

import matplotlib
matplotlib.use('QtAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
import numpy as np


# ── 엔진 import ──────────────────────────────────────────────────────────────
try:
    from engine_v7 import (
        run_v7_simulation, monte_carlo_v7, plot_v7, save_excel_report_v7,
        FLEET_PRESETS as V7_FLEET_PRESETS,
        ENEMY_DB as V7_ENEMY_DB,
        WEATHER_DB,
        ENEMY_FLEET_PRESETS as V7_ENEMY_FLEET_PRESETS,
        ENEMY_FLEET_RANDOM_CFG as V7_RANDOM_CFG,
        MIXED_ATTACK_SCENARIOS as V7_MIXED_SCENARIOS,
        evaluate_req_v7, REQ_ITEMS_V7,
        find_all_min_stocks_v7,
        diagnose_vulnerabilities_v7,
        scenario_comparison_v7,
        calculate_fleet_detect_ranges,
        save_json_report_v7,
        _mc_batch_worker,
        FRIENDLY_DB as V7_FRIENDLY_DB,
        SHIP_DB as V7_SHIP_DB,
        FRIENDLY_AIRCRAFT_DB as V7_AIRCRAFT_DB,
        normalize_enemy_db as _normalize_enemy_db,
        monte_carlo_lhs, stress_test_grid, sobol_analysis, compute_cvar,
        _LHS_PARAM_DEFS, STRESS_DIMS,
    )
    _V7_OK = True
except ImportError as e:
    _V7_OK = False
    _V7_ERR = str(e)
    V7_ENEMY_FLEET_PRESETS = {}
    V7_RANDOM_CFG          = {}
    V7_MIXED_SCENARIOS     = {}

# ── 스펙 DB import ────────────────────────────────────────────────────────────
try:
    from spec_db import SPEC_DETAIL_DB as _SPEC_DETAIL_DB
    _SPEC_DB_OK = True
except ImportError:
    _SPEC_DETAIL_DB = {}
    _SPEC_DB_OK = False

# ── 색상 팔레트 ──────────────────────────────────────────────────────────────
C_BG      = '#0d1117'
C_PANEL   = '#161b22'
C_BORDER  = '#30363d'
C_ACCENT  = '#3498db'
C_TEXT    = '#e6edf3'
C_SUBTEXT = '#7d8590'
C_GREEN   = '#2ecc71'
C_RED     = '#e74c3c'
C_ORANGE  = '#f39c12'

# 차트 렌더 DPI — main()에서 화면 크기 기반으로 갱신 (min 150, max 300)
CHART_DPI: int = 150


class NoScrollSpinBox(QSpinBox):
    """마우스 휠로 값이 변하지 않는 SpinBox."""
    def wheelEvent(self, event):
        event.ignore()


class NoScrollComboBox(QComboBox):
    """마우스 휠로 항목이 바뀌지 않는 ComboBox."""
    def wheelEvent(self, event):
        event.ignore()

STYLE_MAIN = f"""
QMainWindow, QWidget {{
    background-color: {C_BG};
    color: {C_TEXT};
    font-family: 'Malgun Gothic', 'Segoe UI', sans-serif;
    font-size: 17px;
}}
QGroupBox {{
    border: 1px solid {C_BORDER};
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 8px;
    font-weight: bold;
    color: {C_ACCENT};
    font-size: 17px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
    font-family: 'Malgun Gothic', 'Segoe UI', sans-serif;
}}
QComboBox, QSpinBox {{
    background-color: {C_PANEL};
    border: 1px solid {C_BORDER};
    border-radius: 4px;
    padding: 6px 12px;
    color: {C_TEXT};
    font-size: 17px;
}}
QComboBox::drop-down {{ border: none; }}
QComboBox QAbstractItemView {{
    background-color: {C_PANEL};
    color: {C_TEXT};
    selection-background-color: {C_ACCENT};
    font-size: 17px;
}}
QPushButton {{
    background-color: {C_ACCENT};
    color: white;
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
    font-weight: bold;
    font-size: 17px;
}}
QPushButton:hover  {{ background-color: #2980b9; }}
QPushButton:pressed {{ background-color: #1a6fa3; }}
QPushButton:disabled {{ background-color: {C_BORDER}; color: {C_SUBTEXT}; }}
QTabWidget::pane {{
    border: 1px solid {C_BORDER};
    background: {C_BG};
}}
QTabBar::tab {{
    background: {C_PANEL};
    color: {C_SUBTEXT};
    border: 1px solid {C_BORDER};
    padding: 9px 20px;
    margin-right: 2px;
    font-size: 16px;
}}
QTabBar::tab:selected {{
    background: {C_BG};
    color: {C_ACCENT};
    border-bottom: 2px solid {C_ACCENT};
}}
QTableWidget {{
    background-color: {C_PANEL};
    gridline-color: {C_BORDER};
    color: {C_TEXT};
    border: none;
    font-size: 16px;
}}
QTableWidget QHeaderView::section {{
    background-color: {C_BG};
    color: {C_ACCENT};
    border: 1px solid {C_BORDER};
    padding: 6px;
    font-weight: bold;
    font-size: 16px;
}}
QScrollBar:vertical {{
    background: {C_PANEL};
    width: 8px;
}}
QScrollBar::handle:vertical {{
    background: {C_BORDER};
    border-radius: 4px;
}}
QSlider::groove:horizontal {{
    background: {C_BORDER};
    height: 4px;
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {C_ACCENT};
    width: 14px; height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}}
QProgressBar {{
    background: {C_PANEL};
    border: 1px solid {C_BORDER};
    border-radius: 4px;
    text-align: center;
    color: {C_TEXT};
}}
QProgressBar::chunk {{ background: {C_ACCENT}; border-radius: 3px; }}
QLabel {{ color: {C_TEXT}; }}
QStatusBar {{ background: {C_PANEL}; color: {C_SUBTEXT}; border-top: 1px solid {C_BORDER}; }}
QToolTip {{
    background-color: #1a2535;
    color: #e6edf3;
    border: 1px solid {C_ACCENT};
    border-radius: 5px;
    padding: 8px 12px;
    font-size: 14px;
    font-family: 'Malgun Gothic', 'Segoe UI', sans-serif;
}}
"""


# ════════════════════════════════════════════════════════════════════════════
#  플로팅 모니터 창 (시뮬 중 팝업)
# ════════════════════════════════════════════════════════════════════════════
class FloatingMonitor(QWidget):
    """시뮬레이션 실행 중 팝업 — 단계·경과·MC 진행·요격률 게이지·스파크라인·시스템 자원."""

    _SPARK_N = 12   # 스파크라인 칸 수

    def __init__(self, parent=None):
        super().__init__(parent,
                         Qt.WindowType.Window |
                         Qt.WindowType.FramelessWindowHint |
                         Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(400, 370)
        self._mc_t0: float    = 0.0
        self._show_time: float = 0.0
        self._batch_rates: list = []
        self.setStyleSheet("* { font-family: 'Malgun Gothic', 'Segoe UI', sans-serif; }")
        self._drag_pos = None
        self._timer = QTimer(self)
        self._timer.setInterval(800)
        self._timer.timeout.connect(self._refresh_sys)
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        card = QWidget(self)
        card.setObjectName('fmon_card')
        card.setStyleSheet(f"""
            #fmon_card {{
                background: rgba(13,17,23,235);
                border: 1px solid {C_ACCENT};
                border-radius: 10px;
            }}
        """)
        inner = QVBoxLayout(card)
        inner.setContentsMargins(16, 12, 16, 12)
        inner.setSpacing(5)

        # ── 제목 + 경과 시간 ────────────────────────────────────────────────
        title_row = QHBoxLayout()
        self._lbl_title = QLabel("⚙  1/2  단일 시뮬 실행 중…")
        self._lbl_title.setStyleSheet(f"color:{C_ACCENT}; font-size:15px; font-weight:bold;")
        self._lbl_elapsed = QLabel("경과  0:00")
        self._lbl_elapsed.setStyleSheet(f"color:{C_SUBTEXT}; font-size:13px;")
        title_row.addWidget(self._lbl_title)
        title_row.addStretch()
        title_row.addWidget(self._lbl_elapsed)
        inner.addLayout(title_row)

        # ── MC 진행률 ────────────────────────────────────────────────────────
        mc_row = QHBoxLayout()
        self._lbl_mc  = QLabel("MC  0 / 0")
        self._lbl_mc.setStyleSheet(f"color:{C_TEXT}; font-size:15px;")
        self._lbl_eta = QLabel("잔여 —초")
        self._lbl_eta.setStyleSheet(f"color:{C_SUBTEXT}; font-size:13px;")
        mc_row.addWidget(self._lbl_mc)
        mc_row.addStretch()
        mc_row.addWidget(self._lbl_eta)
        inner.addLayout(mc_row)

        self._prog_mc = QProgressBar()
        self._prog_mc.setRange(0, 100)
        self._prog_mc.setValue(0)
        self._prog_mc.setFixedHeight(8)
        self._prog_mc.setStyleSheet(f"""
            QProgressBar {{ background:{C_PANEL}; border-radius:3px; border:1px solid {C_BORDER}; }}
            QProgressBar::chunk {{ background:{C_ACCENT}; border-radius:2px; }}
        """)
        inner.addWidget(self._prog_mc)

        # ── 구분선 ───────────────────────────────────────────────────────────
        inner.addWidget(self._make_sep())

        # ── 요격률 게이지 ────────────────────────────────────────────────────
        rate_row = QHBoxLayout()
        lbl_rt = QLabel("요격률")
        lbl_rt.setStyleSheet(f"color:{C_SUBTEXT}; font-size:12px;")
        lbl_rt.setFixedWidth(40)
        self._prog_rate = QProgressBar()
        self._prog_rate.setRange(0, 100)
        self._prog_rate.setValue(0)
        self._prog_rate.setFixedHeight(10)
        self._prog_rate.setTextVisible(False)
        self._prog_rate.setStyleSheet(self._rate_bar_css(0.0))
        self._lbl_rate_val = QLabel("  —%")
        self._lbl_rate_val.setStyleSheet(f"color:{C_TEXT}; font-size:15px; font-weight:bold;")
        self._lbl_rate_val.setFixedWidth(68)
        rate_row.addWidget(lbl_rt)
        rate_row.addWidget(self._prog_rate, 1)
        rate_row.addWidget(self._lbl_rate_val)
        inner.addLayout(rate_row)

        # ── 격추/피격 카운터 + 스파크라인 ────────────────────────────────────
        stats_row = QHBoxLayout()
        stats_row.setSpacing(8)
        self._lbl_ed = QLabel("격추  —")
        self._lbl_fh = QLabel("피격  —")
        for lbl in (self._lbl_ed, self._lbl_fh):
            lbl.setStyleSheet(f"color:{C_TEXT}; font-size:13px;")
        stats_row.addWidget(self._lbl_ed)
        stats_row.addWidget(self._lbl_fh)
        stats_row.addStretch()

        # 스파크라인 (12칸 컬러 사각형)
        lbl_sp = QLabel("추이")
        lbl_sp.setStyleSheet(f"color:{C_SUBTEXT}; font-size:11px;")
        stats_row.addWidget(lbl_sp)
        self._spark_boxes = []
        for _ in range(self._SPARK_N):
            sq = QLabel()
            sq.setFixedSize(11, 14)
            sq.setStyleSheet(f"background:{C_BORDER}; border-radius:2px;")
            stats_row.addWidget(sq)
            self._spark_boxes.append(sq)
        inner.addLayout(stats_row)

        # ── 구분선 ───────────────────────────────────────────────────────────
        inner.addWidget(self._make_sep())

        # ── 시스템 자원 행 1: CPU / RAM / GPU ────────────────────────────────
        grid1 = QWidget(); gl1 = QHBoxLayout(grid1)
        gl1.setContentsMargins(0, 0, 0, 0); gl1.setSpacing(0)
        self._lbl_cpu = self._make_stat_lbl("CPU",  "—%")
        self._lbl_ram = self._make_stat_lbl("RAM",  "— GB")
        self._lbl_gpu = self._make_stat_lbl("GPU",  "—%")
        for w in (self._lbl_cpu, self._lbl_ram, self._lbl_gpu):
            gl1.addWidget(w, 1)
        inner.addWidget(grid1)

        # ── 시스템 자원 행 2: VRAM / GPU°C / 속도 / 워커 ────────────────────
        grid2 = QWidget(); gl2 = QHBoxLayout(grid2)
        gl2.setContentsMargins(0, 0, 0, 0); gl2.setSpacing(0)
        self._lbl_vram    = self._make_stat_lbl("VRAM",  "— MB")
        self._lbl_gtemp   = self._make_stat_lbl("GPU°C", "—")
        self._lbl_spd     = self._make_stat_lbl("속도",  "— 회/s")
        self._lbl_workers = self._make_stat_lbl("워커",  "—")
        for w in (self._lbl_vram, self._lbl_gtemp, self._lbl_spd, self._lbl_workers):
            gl2.addWidget(w, 1)
        inner.addWidget(grid2)

        # ── 드래그 안내 ──────────────────────────────────────────────────────
        tip = QLabel("드래그로 이동")
        tip.setStyleSheet(f"color:{C_SUBTEXT}; font-size:10px;")
        tip.setAlignment(Qt.AlignmentFlag.AlignCenter)
        inner.addWidget(tip)

        outer.addWidget(card)

    # ── 헬퍼 ────────────────────────────────────────────────────────────────
    def _make_sep(self) -> QLabel:
        sep = QLabel()
        sep.setFixedHeight(1)
        sep.setStyleSheet(f"background:{C_BORDER};")
        return sep

    def _make_stat_lbl(self, title: str, init: str) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w)
        v.setContentsMargins(0, 2, 0, 2)
        v.setSpacing(1)
        t = QLabel(title)
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t.setStyleSheet(f"color:{C_SUBTEXT}; font-size:10px;")
        val = QLabel(init)
        val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        val.setStyleSheet(f"color:{C_TEXT}; font-size:14px; font-weight:bold;")
        val.setObjectName(f'stat_{title}')
        v.addWidget(t)
        v.addWidget(val)
        return w

    @staticmethod
    def _rate_bar_css(rate: float) -> str:
        if rate >= 0.80:
            color = '#2ecc71'   # 초록
        elif rate >= 0.60:
            color = '#f39c12'   # 주황
        else:
            color = '#e74c3c'   # 빨강
        bg = '#161b22'
        return (f"QProgressBar {{ background:{bg}; border-radius:4px; border:1px solid #30363d; }}"
                f"QProgressBar::chunk {{ background:{color}; border-radius:3px; }}")

    # ── 시스템 새로고침 ──────────────────────────────────────────────────────
    def _refresh_sys(self):
        def _find(parent, name):
            return parent.findChild(QLabel, f'stat_{name}')
        c   = _SYS_CACHE
        gpu = c['gpu']

        # 경과 시간
        if self._show_time:
            el = int(time.time() - self._show_time)
            m, s = divmod(el, 60)
            self._lbl_elapsed.setText(f"경과  {m}:{s:02d}")

        # 처리 속도
        if self._mc_t0 and hasattr(self, '_mc_done'):
            elapsed = time.time() - self._mc_t0
            rate = self._mc_done / elapsed if elapsed > 0 else 0.0
            _find(self._lbl_spd, '속도').setText(f"{rate:.0f} 회/s")

        _find(self._lbl_cpu,  'CPU' ).setText(f"{c['cpu']:.0f}%")
        _find(self._lbl_ram,  'RAM' ).setText(f"{c.get('mem_used', 0)/1024**3:.1f} GB")
        _find(self._lbl_gpu,  'GPU' ).setText(f"{gpu['util']}%" if 'util' in gpu else "—%")
        mu, mt = gpu.get('mem_used'), gpu.get('mem_total')
        _find(self._lbl_vram,  'VRAM' ).setText(f"{mu}MB" if mu is not None else "— MB")
        _find(self._lbl_gtemp, 'GPU°C').setText(f"{gpu['temp']}°C" if 'temp' in gpu else "—")
        # 워커 프로세스 수
        wn = len(c.get('worker_stats', []))
        _find(self._lbl_workers, '워커').setText(str(wn) if wn else "—")

    # ── 외부 시그널 핸들러 ───────────────────────────────────────────────────
    def update_status(self, msg: str):
        """progress 시그널 텍스트로 단계 표시 갱신."""
        if "MC" in msg and ("분석" in msg or "/" in msg):
            self._lbl_title.setText("⚙  2/2  MC 분석 중…")
        elif "시뮬레이션 실행" in msg or "실행 중" in msg:
            self._lbl_title.setText("⚙  1/2  단일 시뮬 실행 중…")

    def update_mc(self, done: int, total: int, eta: float):
        if done == 1:
            # 첫 배치 완료 시점 기준으로 경과 시간 역산하여 실제 시작 시각 보정
            per_batch = eta / max(total - done, 1)
            self._mc_t0 = time.time() - per_batch
        self._mc_done = done
        self._lbl_mc.setText(f"MC  {done} / {total}")
        pct = int(done * 100 / total) if total > 0 else 0
        self._prog_mc.setValue(pct)
        self._lbl_eta.setText(f"잔여 약 {eta:.0f}초" if eta > 0 else "잔여 계산 중…")

    def update_rate(self, mean_rate: float, avg_ed: float, avg_fh: float):
        """배치 완료마다 호출 — 요격률 게이지·격추/피격·스파크라인 갱신."""
        pct = int(mean_rate * 100)
        self._prog_rate.setValue(pct)
        self._prog_rate.setStyleSheet(self._rate_bar_css(mean_rate))
        self._lbl_rate_val.setText(f"  {mean_rate:.1%}")
        color = '#2ecc71' if mean_rate >= 0.80 else ('#f39c12' if mean_rate >= 0.60 else '#e74c3c')
        self._lbl_rate_val.setStyleSheet(f"color:{color}; font-size:15px; font-weight:bold;")

        self._lbl_ed.setText(f"격추  {avg_ed:.1f}")
        self._lbl_fh.setText(f"피격  {avg_fh:.2f}")

        # 스파크라인 갱신
        self._batch_rates.append(mean_rate)
        recent = self._batch_rates[-self._SPARK_N:]
        for i, sq in enumerate(self._spark_boxes):
            if i < len(recent):
                r = recent[i]
                if r >= 0.80:
                    c = '#2ecc71'
                elif r >= 0.60:
                    c = '#f39c12'
                else:
                    c = '#e74c3c'
                sq.setStyleSheet(f"background:{c}; border-radius:2px;")
            else:
                sq.setStyleSheet(f"background:{C_BORDER}; border-radius:2px;")

    def show(self):
        super().show()
        self._show_time = time.time()
        self._batch_rates.clear()
        self._mc_done = 0
        # 스파크라인 초기화
        for sq in self._spark_boxes:
            sq.setStyleSheet(f"background:{C_BORDER}; border-radius:2px;")
        self._timer.start()
        self._refresh_sys()

    def close(self):
        self._timer.stop()
        super().close()

    # ── 드래그 이동 ──────────────────────────────────────────────────────────
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None


# ════════════════════════════════════════════════════════════════════════════
#  실행 로그 뷰어 다이얼로그
# ════════════════════════════════════════════════════════════════════════════
class SimLogDialog(QDialog):
    """sim_history.json 을 읽어 테이블로 표시하는 독립 창."""

    _COLS = [
        ('날짜/시각',    'datetime',           180),
        ('편대',         'fleet',              140),
        ('날씨',         'weather',            110),
        ('MC',           'mc_n',                55),
        ('총 위협',      'total_threats',       70),
        ('요격률',       'mean_intercept',      80),
        ('±',            'std_intercept',       60),
        ('완전요격',     'full_pass_rate',      75),
        ('아군 피격',    'avg_friendly_hits',   75),
        ('비용 ($M)',    'total_cost',          90),
        ('적군 구성',    'enemy',                0),   # 0 = stretch
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("실행 로그 뷰어")
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, True)
        self.resize(1300, 620)
        self.setStyleSheet(
            f"QWidget {{ background:{C_BG}; color:{C_TEXT}; "
            f"font-family:'Malgun Gothic','Segoe UI'; font-size:13px; }}"
            f"QHeaderView::section {{ background:{C_PANEL}; color:{C_ACCENT}; "
            f"border:none; padding:5px; font-size:13px; }}"
            f"QTableWidget {{ background:{C_PANEL}; gridline-color:{C_BORDER}; border:none; }}"
            f"QScrollBar:vertical {{ width:6px; background:{C_BG}; }}"
            f"QScrollBar::handle:vertical {{ background:{C_BORDER}; border-radius:3px; }}"
            f"QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}"
        )
        self._build_ui()
        self._load()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        # ── 상단 툴바 ──────────────────────────────────────────────────────
        bar = QHBoxLayout()
        bar.setSpacing(8)

        self._search = QLineEdit()
        self._search.setPlaceholderText("🔍  날짜·편대·날씨·적군 검색…")
        self._search.setFixedHeight(28)
        self._search.setStyleSheet(
            f"background:{C_PANEL}; color:{C_TEXT}; border:1px solid {C_BORDER};"
            f" border-radius:4px; padding:0 8px;"
        )
        self._search.textChanged.connect(self._apply_filter)

        btn_refresh = QPushButton("새로고침")
        btn_refresh.setFixedHeight(28)
        btn_refresh.setStyleSheet(
            f"QPushButton {{ background:{C_PANEL}; color:{C_SUBTEXT}; border:1px solid {C_BORDER};"
            f" border-radius:4px; padding:0 12px; }}"
            f"QPushButton:hover {{ color:{C_TEXT}; }}"
        )
        btn_refresh.clicked.connect(self._load)

        btn_csv = QPushButton("CSV 내보내기")
        btn_csv.setFixedHeight(28)
        btn_csv.setStyleSheet(btn_refresh.styleSheet())
        btn_csv.clicked.connect(self._export_csv)

        btn_clear = QPushButton("로그 초기화")
        btn_clear.setFixedHeight(28)
        btn_clear.setStyleSheet(
            f"QPushButton {{ background:{C_PANEL}; color:#e74c3c; border:1px solid #5c1a1a;"
            f" border-radius:4px; padding:0 12px; }}"
            f"QPushButton:hover {{ background:#2a1010; }}"
        )
        btn_clear.clicked.connect(self._clear_log)

        self._lbl_count = QLabel("")
        self._lbl_count.setStyleSheet(f"color:{C_SUBTEXT}; font-size:12px;")

        bar.addWidget(self._search, stretch=1)
        bar.addWidget(btn_refresh)
        bar.addWidget(btn_csv)
        bar.addWidget(btn_clear)
        bar.addWidget(self._lbl_count)
        root.addLayout(bar)

        # ── 테이블 ─────────────────────────────────────────────────────────
        self._tbl = QTableWidget()
        self._tbl.setColumnCount(len(self._COLS))
        self._tbl.setHorizontalHeaderLabels([c[0] for c in self._COLS])
        self._tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._tbl.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._tbl.setAlternatingRowColors(True)
        self._tbl.verticalHeader().setDefaultSectionSize(26)
        self._tbl.verticalHeader().setVisible(False)
        self._tbl.setStyleSheet(
            f"QTableWidget {{ alternate-background-color: #111720; }}"
            f"QTableWidget::item:selected {{ background:{C_ACCENT}33; color:{C_TEXT}; }}"
        )
        hh = self._tbl.horizontalHeader()
        hh.setSortIndicatorShown(True)
        hh.setSectionsClickable(True)
        for i, (_, _, w) in enumerate(self._COLS):
            if w == 0:
                hh.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:
                hh.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
                self._tbl.setColumnWidth(i, w)
        self._tbl.setSortingEnabled(True)

        # ── 하단 상세 패널 ─────────────────────────────────────────────────
        self._detail = QLabel("← 행을 선택하면 상세 정보가 표시됩니다.")
        self._detail.setWordWrap(True)
        self._detail.setStyleSheet(
            f"background:{C_PANEL}; color:{C_SUBTEXT}; font-size:13px;"
            f" border:1px solid {C_BORDER}; border-radius:4px; padding:8px 12px;"
        )
        self._detail.setFixedHeight(72)

        self._tbl.currentRowChanged.connect(self._show_detail)

        root.addWidget(self._tbl, stretch=1)
        root.addWidget(self._detail)

    # ── 데이터 처리 ────────────────────────────────────────────────────────
    def _load(self):
        self._records = list(reversed(_load_json_log()))   # 최신순
        self._apply_filter(self._search.text())

    def _apply_filter(self, text: str):
        kw = text.strip().lower()
        filtered = [
            r for r in self._records
            if not kw or any(kw in str(v).lower() for v in r.values())
        ]
        self._fill_table(filtered)
        self._lbl_count.setText(f"총 {len(filtered)}건")

    def _fill_table(self, records: list):
        self._tbl.setSortingEnabled(False)
        self._tbl.setRowCount(0)
        for rec in records:
            row = self._tbl.rowCount()
            self._tbl.insertRow(row)
            values = [
                rec.get('datetime', ''),
                rec.get('fleet', ''),
                rec.get('weather', ''),
                str(rec.get('mc_n', '')),
                str(rec.get('total_threats', '')),
                f"{rec.get('mean_intercept', 0):.1%}",
                f"±{rec.get('std_intercept', 0):.1%}",
                f"{rec.get('full_pass_rate', 0):.1%}",
                f"{rec.get('avg_friendly_hits', 0):.1f}",
                f"{rec.get('total_cost', 0) / 1e6:.1f}",
                rec.get('enemy', ''),
            ]
            for col, val in enumerate(values):
                item = QTableWidgetItem(val)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter
                                      if col != len(self._COLS) - 1
                                      else Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                # 요격률 컬러
                if col == 5:
                    rate = rec.get('mean_intercept', 0)
                    item.setForeground(QColor(
                        C_GREEN if rate >= 0.8 else
                        '#f39c12' if rate >= 0.5 else
                        '#e74c3c'
                    ))
                self._tbl.setItem(row, col, item)
            self._tbl.item(row, 0).setData(Qt.ItemDataRole.UserRole, rec)
        self._tbl.setSortingEnabled(True)

    def _show_detail(self, row: int):
        if row < 0:
            return
        item = self._tbl.item(row, 0)
        if not item:
            return
        rec = item.data(Qt.ItemDataRole.UserRole)
        if not rec:
            return
        self._detail.setText(
            f"<b>{rec.get('datetime','')}</b> &nbsp;|&nbsp; "
            f"편대: <b>{rec.get('fleet','')}</b> &nbsp;|&nbsp; "
            f"날씨: {rec.get('weather','')} &nbsp;|&nbsp; "
            f"MC: {rec.get('mc_n','')}회 &nbsp;|&nbsp; "
            f"위협: {rec.get('total_threats','')}발/기<br>"
            f"요격률: <b>{rec.get('mean_intercept',0):.1%}</b> "
            f"(±{rec.get('std_intercept',0):.1%}) &nbsp;|&nbsp; "
            f"완전요격: {rec.get('full_pass_rate',0):.1%} &nbsp;|&nbsp; "
            f"아군 피격: {rec.get('avg_friendly_hits',0):.1f}회 &nbsp;|&nbsp; "
            f"비용: ${rec.get('total_cost',0):,.0f}<br>"
            f"<span style='color:{C_SUBTEXT}'>적군: {rec.get('enemy','')}</span>"
        )

    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "CSV 저장", "sim_history.csv", "CSV (*.csv)")
        if not path:
            return
        try:
            import csv
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                w = csv.DictWriter(f, fieldnames=list(self._records[0].keys()) if self._records else [])
                w.writeheader()
                w.writerows(list(reversed(self._records)))
            QMessageBox.information(self, "내보내기 완료", f"저장됨:\n{path}")
        except Exception as e:
            QMessageBox.warning(self, "오류", str(e))

    def _clear_log(self):
        if QMessageBox.question(
            self, "로그 초기화",
            "모든 실행 기록을 삭제하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) != QMessageBox.StandardButton.Yes:
            return
        _save_json_log([])
        try:
            open(_log_path(), 'w', encoding='utf-8').close()
        except Exception:
            pass
        self._load()


# ════════════════════════════════════════════════════════════════════════════
#  백그라운드 시뮬레이션 워커
# ════════════════════════════════════════════════════════════════════════════
class SensitivityWorker(QThread):
    """감도 분석 MC를 백그라운드에서 실행 후 결과 전달."""
    finished = pyqtSignal(list, list, list, float)  # (labels, lows, highs, base_rate)
    error    = pyqtSignal(str)

    def __init__(self, cfg: dict, mc_n: int):
        super().__init__()
        self.cfg  = cfg
        self.mc_n = max(50, mc_n // 5)

    def run(self):
        if not _V7_OK:
            return
        try:
            params = [
                ('C&D 시간',  'cd_time_s',      5, 20),
                ('확인 시간', 'confirm_time_s',  1, 10),
                ('시뮬 시드', 'sim_seed',         1, 42),
            ]
            base_mc   = monte_carlo_v7(self.cfg, self.mc_n)
            base_rate = base_mc['mean_intercept']
            labels, lows, highs = [], [], []
            for name, key, lo_val, hi_val in params:
                r_lo = monte_carlo_v7({**self.cfg, key: lo_val}, self.mc_n)['mean_intercept']
                r_hi = monte_carlo_v7({**self.cfg, key: hi_val}, self.mc_n)['mean_intercept']
                labels.append(f"{name}\n({lo_val}→{hi_val})")
                lows.append(r_lo - base_rate)
                highs.append(r_hi - base_rate)
            self.finished.emit(labels, lows, highs, base_rate)
        except Exception as e:
            self.error.emit(str(e))


class MinStockWorker(QThread):
    """REQ 달성 최소 재고 역산을 백그라운드에서 실행."""
    progress = pyqtSignal(int, int, str)    # (i, total, weapon_name)
    finished = pyqtSignal(dict, float)      # (results_dict, target_rate)
    error    = pyqtSignal(str)

    def __init__(self, cfg: dict, mc_n: int, target_rate: float = 0.90):
        super().__init__()
        self.cfg         = cfg
        self.mc_n        = max(20, mc_n // 8)  # 속도 우선 — 근사치 허용
        self.target_rate = target_rate

    def run(self):
        if not _V7_OK:
            return
        try:
            def _cb(i, total, name):
                self.progress.emit(i, total, name)
            results = find_all_min_stocks_v7(
                self.cfg, self.target_rate, self.mc_n, _cb)
            self.finished.emit(results, self.target_rate)
        except Exception as e:
            self.error.emit(str(e))


class WeatherWorker(QThread):
    """날씨별 비교 MC를 백그라운드에서 실행."""
    finished = pyqtSignal(dict)
    error    = pyqtSignal(str)

    def __init__(self, cfg: dict, n: int = 1000):
        super().__init__()
        self.cfg = cfg
        self.n   = n

    def run(self):
        if not _V7_OK:
            return
        try:
            sc = scenario_comparison_v7(self.cfg, n=self.n)
            self.finished.emit(sc)
        except Exception as e:
            self.error.emit(str(e))


class SimWorker(QThread):
    progress        = pyqtSignal(str)
    progress_detail = pyqtSignal(int, int, float)  # (현재, 전체, ETA초)
    finished        = pyqtSignal(dict, dict)
    error           = pyqtSignal(str)
    sim_started     = pyqtSignal()
    sim_ended       = pyqtSignal()
    batch_done      = pyqtSignal(int, int)         # (완료배치, 전체배치)
    rate_update     = pyqtSignal(float, float, float)  # (mean_rate, avg_e_dest, avg_f_hits)

    def __init__(self, cfg: dict, mc_n: int, precision_mode: bool = False,
                 sobol_npp: int = 3):
        super().__init__()
        self.cfg            = cfg
        self.mc_n           = mc_n
        self.precision_mode = precision_mode
        self.sobol_npp      = sobol_npp

    def run(self):
        try:
            self.sim_started.emit()
            self.progress.emit("시뮬레이션 실행 중...")
            result = run_v7_simulation(self.cfg)
            self.progress.emit(f"MC {self.mc_n}회 분석 중...")
            t0 = time.time()

            def _cb(done, total):
                elapsed = time.time() - t0
                eta = (elapsed / done * (total - done)) if done > 0 else 0.0
                self.progress_detail.emit(done, total, eta)
                self.progress.emit(f"MC {done}/{total}회 | 잔여 약 {eta:.0f}초")

            n_cores = min(os.cpu_count() or 1, 8)
            if not _V7_OK or self.mc_n < 100 or n_cores <= 1:
                # 소규모 or 단일코어 — 순차 실행
                try:
                    mc = monte_carlo_v7(self.cfg, n=self.mc_n, progress_cb=_cb)
                except TypeError:
                    mc = monte_carlo_v7(self.cfg, n=self.mc_n)
            else:
                # 멀티프로세싱 병렬 MC
                batch_size = max(10, self.mc_n // n_cores)
                batches, seed_offset = [], 0
                while seed_offset < self.mc_n:
                    actual = min(batch_size, self.mc_n - seed_offset)
                    batches.append((self.cfg, actual, seed_offset))
                    seed_offset += actual

                all_rates, all_f_hits, all_e_dest = [], [], []
                all_f_lost, all_costs = [], []
                all_weapon: dict = {}
                all_ship: dict = {}
                done_count = 0

                pool = _GLOBAL_POOL or ProcessPoolExecutor(max_workers=n_cores)
                _own = _GLOBAL_POOL is None
                if _own:
                    _set_pool_priority(pool)  # BUG-1: 인라인 풀도 BELOW_NORMAL
                batch_done_n = 0
                futs = {pool.submit(_mc_batch_worker, b): b for b in batches}
                for fut in as_completed(futs):
                    if self.isInterruptionRequested():
                        for f in futs:
                            f.cancel()
                        if _own:
                            pool.shutdown(wait=False)
                        return
                    rates, fh, ed, fl, cs, wu, sh = fut.result()
                    all_rates.extend(rates);  all_f_hits.extend(fh)
                    all_e_dest.extend(ed);    all_f_lost.extend(fl)
                    all_costs.extend(cs)
                    for k, v in wu.items(): all_weapon.setdefault(k, []).extend(v)
                    for k, v in sh.items(): all_ship.setdefault(k, []).extend(v)
                    done_count += len(rates)
                    batch_done_n += 1
                    self.batch_done.emit(batch_done_n, len(batches))
                    _cb(done_count, self.mc_n)
                    if all_rates:
                        self.rate_update.emit(
                            float(np.mean(all_rates)),
                            float(np.mean(all_e_dest)) if all_e_dest else 0.0,
                            float(np.mean(all_f_hits)) if all_f_hits else 0.0,
                        )
                if _own:
                    pool.shutdown(wait=False)

                arr = np.array(all_rates)
                mc = {
                    'intercept_rates':      all_rates,
                    'friendly_hits':        all_f_hits,
                    'enemy_destroyed':      all_e_dest,
                    'friendly_lost':        all_f_lost,
                    'total_costs':          all_costs,
                    'weapon_avg_remaining': {k: float(np.mean(v)) for k, v in all_weapon.items()},
                    'ship_avg_hits':        {k: float(np.mean(v)) for k, v in all_ship.items()},
                    'mean_intercept':       float(arr.mean()),
                    'std_intercept':        float(arr.std()),
                    'full_pass_rate':       float((arr == 1.0).mean()),
                    'n':                    len(all_rates),
                }

            # ── CVaR: 기존 MC rates에서 직접 계산 (추가 시뮬 불필요) ─────────
            if _V7_OK:
                try:
                    mc['cvar'] = compute_cvar(mc.get('intercept_rates', []))
                except Exception:
                    mc['cvar'] = 0.0

            # ── LHS 파라미터 불확실성 분석 (중간 규모, 병렬 MC와 별개) ────────
            # 빠름=1,000  표준=2,000  정밀=10,000
            lhs_result = {}
            if _V7_OK:
                lhs_n_map  = {5_000: 1_000, 10_000: 2_000, 100_000: 10_000}
                lhs_n      = lhs_n_map.get(self.mc_n, 2_000)
                self.progress.emit(f"LHS 파라미터 불확실성 분석 중... ({lhs_n:,}회)")
                lhs_t0 = time.time()

                def _lhs_cb(done, total):
                    if done % max(1, total // 10) == 0:
                        ela = time.time() - lhs_t0
                        eta = ela / done * (total - done) if done > 0 else 0
                        self.progress.emit(f"LHS {done:,}/{total:,} | 잔여 {eta:.0f}초")

                try:
                    lhs_result = monte_carlo_lhs(self.cfg, n=lhs_n, progress_cb=_lhs_cb)
                except Exception as ex:
                    lhs_result = {'error': str(ex)}

            # ── 스트레스 테스트 (모든 모드, n_per_cell 가변) ─────────────────
            stress_result = {}
            if _V7_OK:
                n_cell_map = {5_000: 300, 10_000: 500, 100_000: 3_000}
                n_per_cell = n_cell_map.get(self.mc_n, 500)
                total_stress = len(STRESS_DIMS['channel_degrade']['values']) * \
                               len(STRESS_DIMS['radar_degrade']['values'])
                self.progress.emit(f"스트레스 테스트 중... (셀당 {n_per_cell}회, 총 {total_stress}셀)")

                def _stress_cb(done, total):
                    self.progress.emit(f"스트레스 테스트 {done}/{total} 셀 완료")

                try:
                    stress_result = stress_test_grid(
                        self.cfg, n_per_cell=n_per_cell, progress_cb=_stress_cb)
                except Exception as ex:
                    stress_result = {'error': str(ex)}

            # ── Sobol 민감도 분석 (정밀 모드 전용) ──────────────────────────
            sobol_result = {}
            if _V7_OK and self.precision_mode:
                npp        = self.sobol_npp
                total_est  = 32_768 * npp
                self.progress.emit(
                    f"Sobol 민감도 분석 중... (포인트당 {npp}회, 총 ~{total_est:,}회, 수 분 소요)")
                sobol_t0 = time.time()

                def _sobol_cb(done, total):
                    if done % max(1, total // 20) == 0:
                        ela = time.time() - sobol_t0
                        eta = ela / done * (total - done) if done > 0 else 0
                        self.progress.emit(
                            f"Sobol {done:,}/{total:,} 포인트 | 잔여 {eta:.0f}초")

                try:
                    sobol_result = sobol_analysis(
                        self.cfg, n_sobol=4096, n_per_point=npp,
                        progress_cb=_sobol_cb)
                except Exception as ex:
                    sobol_result = {'error': str(ex)}

            mc['lhs']    = lhs_result
            mc['stress'] = stress_result
            mc['sobol']  = sobol_result

            elapsed = time.time() - t0
            rate    = self.mc_n / elapsed if elapsed > 0 else 0.0
            _PERF_HISTORY.append({
                'time':     time.time(),
                'mc_n':     self.mc_n,
                'duration': elapsed,
                'rate':     rate,
            })
            if len(_PERF_HISTORY) > 10:
                _PERF_HISTORY.pop(0)
            self.sim_ended.emit()
            self.finished.emit(result, mc)
        except Exception as e:
            self.sim_ended.emit()
            self.error.emit(str(e))


# ════════════════════════════════════════════════════════════════════════════
#  시스템 데이터 백그라운드 워커 (블로킹 I/O를 메인 스레드에서 분리)
# ════════════════════════════════════════════════════════════════════════════
class _SysDataWorker(QThread):
    """nvidia-smi·WMI 등 블로킹 I/O를 1초마다 백그라운드에서 수집, _SYS_CACHE 갱신."""

    def run(self):
        while not self.isInterruptionRequested():
            try:
                cpu   = psutil.cpu_percent(interval=None)
                cores = psutil.cpu_percent(percpu=True, interval=None) or []
                mem   = psutil.virtual_memory()
                swap  = psutil.swap_memory()
                gpu   = _get_gpu_info()      # subprocess — 메인 스레드 블로킹 제거
                ctemp = _get_cpu_temp()      # WMI — 메인 스레드 블로킹 제거
                proc  = psutil.Process()
                proc_ram = proc.memory_info().rss / 1024**2
                stats: list = []
                try:
                    for c in proc.children(recursive=True):
                        try:
                            stats.append({
                                'pid':    c.pid,
                                'cpu':    c.cpu_percent(interval=None),
                                'ram':    c.memory_info().rss / 1024**2,
                                'status': c.status(),
                            })
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                except Exception:
                    pass
                _SYS_CACHE.update({
                    'cpu': cpu, 'mem_pct': mem.percent,
                    'mem_used': mem.used, 'mem_total': mem.total,
                    'gpu': gpu, 'cpu_temp': ctemp,
                    'cores': list(cores), 'proc_ram': proc_ram,
                    'worker_stats': stats, 'swap_used': swap.used,
                    'thread_cnt': threading.active_count(),
                })
            except Exception:
                pass
            self.msleep(1000)


_SYS_DATA_WORKER: '_SysDataWorker | None' = None


def _start_sys_data_worker():
    global _SYS_DATA_WORKER
    _SYS_DATA_WORKER = _SysDataWorker()
    _SYS_DATA_WORKER.start()


def _stop_sys_data_worker():
    global _SYS_DATA_WORKER
    if _SYS_DATA_WORKER is not None:
        _SYS_DATA_WORKER.requestInterruption()
        _SYS_DATA_WORKER.quit()
        if not _SYS_DATA_WORKER.wait(1500):
            _SYS_DATA_WORKER.terminate()
            _SYS_DATA_WORKER.wait(300)
        _SYS_DATA_WORKER = None


# ════════════════════════════════════════════════════════════════════════════
#  Matplotlib Canvas 래퍼
# ════════════════════════════════════════════════════════════════════════════
class MplCanvas(FigureCanvas):
    def __init__(self, figsize=(8, 6), facecolor=C_BG):
        self.fig = Figure(figsize=figsize, facecolor=facecolor)
        super().__init__(self.fig)
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Expanding)


# ════════════════════════════════════════════════════════════════════════════
#  차트 백그라운드 렌더 워커 + 위젯 (UI 프리즈 방지)
# ════════════════════════════════════════════════════════════════════════════
class ChartRenderWorker(QThread):
    """matplotlib Figure를 백그라운드 스레드에서 PNG bytes로 렌더링."""
    finished = pyqtSignal(bytes)
    error    = pyqtSignal(str)

    def __init__(self, fn, args, kwargs):
        super().__init__()
        self._fn     = fn
        self._args   = args
        self._kwargs = kwargs

    def run(self):
        try:
            result = self._fn(*self._args, **self._kwargs)
            if isinstance(result, (bytes, bytearray)):
                # 함수가 PNG bytes를 직접 반환 (이중 렌더 없음)
                self.finished.emit(bytes(result))
                return
            fig = result
            buf = io.BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight',
                        facecolor=fig.get_facecolor(), dpi=CHART_DPI)
            from matplotlib import pyplot as _plt
            _plt.close(fig)
            self.finished.emit(buf.getvalue())
        except Exception as e:
            self.error.emit(str(e))


class ChartPageWidget(QWidget):
    """결과 차트 탭: 로딩 안내 → 렌더 완료 이미지 전환."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker: 'ChartRenderWorker | None' = None
        self._raw_pix: 'QPixmap | None' = None
        self._raw_bytes: bytes = b''

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._pane = QStackedWidget()

        # 0 — 로딩
        loading = QWidget()
        loading.setStyleSheet(f"background:{C_BG};")
        ll = QVBoxLayout(loading)
        ll.addStretch()
        self._loading_lbl = QLabel("  차트 렌더링 중…")
        self._loading_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._loading_lbl.setStyleSheet(
            f"color:{C_SUBTEXT}; font-size:15px; font-family:'Malgun Gothic';")
        ll.addWidget(self._loading_lbl)
        ll.addStretch()
        self._pane.addWidget(loading)

        # 1 — 이미지 (비율 유지 스케일)
        self._img_lbl = QLabel()
        self._img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._img_lbl.setStyleSheet(f"background:{C_BG};")
        self._img_lbl.setSizePolicy(QSizePolicy.Policy.Expanding,
                                    QSizePolicy.Policy.Expanding)
        self._pane.addWidget(self._img_lbl)

        layout.addWidget(self._pane)
        self._pane.setCurrentIndex(0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Expanding)

    def start_render(self, fn, *args, **kwargs):
        if self._worker and self._worker.isRunning():
            try:
                self._worker.finished.disconnect()
                self._worker.error.disconnect()
            except Exception:
                pass
            self._worker.requestInterruption()
            self._worker.quit()
        self._raw_pix = None
        self._raw_bytes = b''
        self._loading_lbl.setText("  차트 렌더링 중…")
        self._pane.setCurrentIndex(0)
        self._worker = ChartRenderWorker(fn, args, kwargs)
        self._worker.finished.connect(self._on_done)
        self._worker.error.connect(self._on_error)
        self._worker.start(QThread.Priority.LowPriority)

    def stop_worker(self):
        """창 닫기 시 백그라운드 렌더 스레드 정리."""
        w = self._worker
        if w and w.isRunning():
            try:
                w.finished.disconnect()
                w.error.disconnect()
            except Exception:
                pass
            w.requestInterruption()
            w.quit()
            if not w.wait(800):
                w.terminate()
                w.wait(300)

    def _on_done(self, png_bytes: bytes):
        self._raw_bytes = png_bytes
        pix = QPixmap()
        pix.loadFromData(png_bytes)
        self._raw_pix = pix
        self._update_display()
        self._pane.setCurrentIndex(1)

    def _on_error(self, msg: str):
        self._loading_lbl.setText(f"  렌더링 실패: {msg}")

    def _update_display(self):
        if not self._raw_pix or self._raw_pix.isNull():
            return
        w, h = self.width(), self.height()
        if w > 10 and h > 10:
            self._img_lbl.setPixmap(
                self._raw_pix.scaled(w, h,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_display()


# 서브프로세스 안전 렌더 함수: anim_render.py에서 임포트 (launcher.py는 QtAgg 백엔드 사용)
from anim_render import _render_anim_frame


# ════════════════════════════════════════════════════════════════════════════
#  전장 애니메이션 프레임 사전 렌더 워커
# ════════════════════════════════════════════════════════════════════════════
class FrameRenderWorker(QThread):
    frame_ready = pyqtSignal(int, bytes)
    all_done    = pyqtSignal()

    def __init__(self, frame_data, display_range, show_labels, show_alt):
        super().__init__()
        self._frame_data    = frame_data
        self._display_range = display_range
        self._show_labels   = show_labels
        self._show_alt      = show_alt
        self._cancelled     = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        n = len(self._frame_data)
        if n == 0:
            self.all_done.emit()
            return
        n_workers = min(os.cpu_count() or 4, 8)
        args_list = [
            (i, fd['t'], fd['enemy_ships'], fd['friendly_ships'],
             fd['missiles'], fd['events'],
             self._display_range, self._show_labels, self._show_alt)
            for i, fd in enumerate(self._frame_data)
        ]
        ex   = _GLOBAL_POOL or ProcessPoolExecutor(max_workers=n_workers)
        _own = _GLOBAL_POOL is None
        futs = {ex.submit(_render_anim_frame, a): a[0] for a in args_list}
        emit_count = 0
        for fut in as_completed(futs):
            if self._cancelled:
                for f in futs:
                    f.cancel()
                if _own:
                    ex.shutdown(wait=False)
                return
            try:
                idx, png = fut.result()
                self.frame_ready.emit(idx, png)
                emit_count += 1
                if emit_count % 10 == 0:
                    self.msleep(12)  # 10프레임마다 12ms 대기 → 메인 스레드 QPixmap 처리 시간 확보
            except Exception:
                pass
        if _own:
            ex.shutdown(wait=False)
        if not self._cancelled:
            self.all_done.emit()


# ════════════════════════════════════════════════════════════════════════════
#  전장 애니메이션 탭 (QPixmap 사전 렌더링 방식)
# ════════════════════════════════════════════════════════════════════════════
class AnimationTab(QWidget):
    """
    2.5D 등각투영 전장 애니메이션.
    FrameRenderWorker가 모든 프레임을 PNG→QPixmap으로 사전 렌더링하고,
    재생 시 QLabel.setPixmap() 으로 즉시 표시한다.
    """

    def __init__(self):
        super().__init__()
        self.frames            = []
        self._display_range    = 350.0
        self._cur_idx          = 0
        self._zoom             = 1.0
        self._kill_frames      = []
        self._play_interval    = 80
        self._pixmaps: list    = []   # list[Optional[QPixmap]]
        self._rendered_count   = 0
        self._render_worker    = None
        self._render_gen       = 0    # 세대 카운터 — 구식 frame_ready 신호 필터링
        self._playing          = False
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # ── QLabel 디스플레이 (FigureCanvas 대체) ─────────────────────────
        self._lbl_canvas = QLabel()
        self._lbl_canvas.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_canvas.setStyleSheet("background: #0d1117;")
        self._lbl_canvas.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._lbl_canvas.installEventFilter(self)
        layout.addWidget(self._lbl_canvas)

        # 사전 렌더 진행률 바
        self._prog_render = QProgressBar()
        self._prog_render.setFixedHeight(6)
        self._prog_render.setRange(0, 100)
        self._prog_render.setValue(0)
        self._prog_render.setTextVisible(False)
        self._prog_render.setStyleSheet(
            f"QProgressBar {{ background:{C_PANEL}; border:none; border-radius:3px; }}"
            f"QProgressBar::chunk {{ background:{C_ACCENT}; border-radius:3px; }}")
        self._prog_render.hide()
        layout.addWidget(self._prog_render)

        # ── 옵션 행 ──────────────────────────────────────────────────────
        _bs = (f"background:{C_PANEL}; color:{C_TEXT}; "
               f"border:1px solid #3a5a7a; font-size:15px; padding:2px 7px;")
        opt_row = QHBoxLayout()

        self.chk_labels = QCheckBox("이름 표시")
        self.chk_labels.setChecked(True)
        self.chk_labels.setStyleSheet(f"color:{C_TEXT}; font-size:15px;")
        self.chk_labels.stateChanged.connect(self._restart_render)

        self.chk_altitude = QCheckBox("고도선 표시")
        self.chk_altitude.setChecked(True)
        self.chk_altitude.setStyleSheet(f"color:{C_TEXT}; font-size:15px;")
        self.chk_altitude.stateChanged.connect(self._restart_render)

        lbl_spd = QLabel("속도:")
        lbl_spd.setStyleSheet(f"color:{C_SUBTEXT}; font-size:15px;")
        self._spd_btns = []
        for label, ms in [("0.5x", 160), ("1x", 80), ("2x", 40), ("4x", 20)]:
            b = QPushButton(label)
            b.setFixedHeight(24); b.setFixedWidth(36)
            b.setStyleSheet(_bs)
            b.clicked.connect(lambda _, m=ms: self._set_speed(m))
            self._spd_btns.append(b)

        btn_shot = QPushButton("📷")
        btn_shot.setFixedHeight(24); btn_shot.setFixedWidth(30)
        btn_shot.setStyleSheet(_bs)
        btn_shot.setToolTip("현재 프레임 PNG 저장")
        btn_shot.clicked.connect(self._save_screenshot)

        lbl_zoom = QLabel("  줌:")
        lbl_zoom.setStyleSheet(f"color:{C_SUBTEXT}; font-size:15px;")
        self._btn_zout  = QPushButton("−")
        self._btn_zin   = QPushButton("+")
        self._btn_zreset = QPushButton("1:1")
        for b, tip, fn in [
            (self._btn_zout,  "줌 아웃 (휠 아래)", lambda: self._zoom_step(1.15)),
            (self._btn_zin,   "줌 인 (휠 위)",     lambda: self._zoom_step(0.85)),
            (self._btn_zreset,"줌 초기화",          self._reset_zoom),
        ]:
            b.setFixedHeight(24); b.setFixedWidth(36)
            b.setStyleSheet(_bs)
            b.setToolTip(tip)
            b.clicked.connect(fn)

        lbl_hint = QLabel("  2.5D 등각투영")
        lbl_hint.setStyleSheet(f"color:{C_SUBTEXT}; font-size:10px;")

        opt_row.addWidget(self.chk_labels)
        opt_row.addWidget(self.chk_altitude)
        opt_row.addWidget(lbl_spd)
        for b in self._spd_btns:
            opt_row.addWidget(b)
        opt_row.addWidget(btn_shot)
        opt_row.addWidget(lbl_zoom)
        opt_row.addWidget(self._btn_zout)
        opt_row.addWidget(self._btn_zin)
        opt_row.addWidget(self._btn_zreset)
        opt_row.addWidget(lbl_hint)
        opt_row.addStretch()
        layout.addLayout(opt_row)

        # ── 재생 컨트롤 ───────────────────────────────────────────────────
        ctrl = QHBoxLayout()
        self.lbl_time = QLabel("t = 0s")
        self.lbl_time.setStyleSheet(
            f"color:{C_ACCENT}; font-weight:bold; font-size:16px;")
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0); self.slider.setMaximum(0)
        self.slider.valueChanged.connect(self._on_slider)
        self.btn_play = QPushButton("▶ 재생")
        self.btn_play.setFixedWidth(90)
        self.btn_play.clicked.connect(self._toggle_play)
        self.btn_play.setEnabled(False)

        self.btn_prev_kill = QPushButton("◀ 격추")
        self.btn_next_kill = QPushButton("격추 ▶")
        for b in [self.btn_prev_kill, self.btn_next_kill]:
            b.setFixedWidth(65); b.setFixedHeight(26)
            b.setStyleSheet(_bs)
        self.btn_prev_kill.clicked.connect(self._prev_kill)
        self.btn_next_kill.clicked.connect(self._next_kill)

        self.lbl_events = QLabel("")
        self.lbl_events.setStyleSheet(f"color:{C_SUBTEXT}; font-size:15px;")
        self.lbl_events.setFixedHeight(28)  # 고정 높이 — 텍스트 변경 시 캔버스 크기 변동(진동) 방지

        ctrl.addWidget(self.btn_prev_kill)
        ctrl.addWidget(self.btn_next_kill)
        ctrl.addWidget(self.lbl_time)
        ctrl.addWidget(self.slider, stretch=1)
        ctrl.addWidget(self.btn_play)
        layout.addLayout(ctrl)
        layout.addWidget(self.lbl_events)

        self._play_timer = QTimer()
        self._play_timer.timeout.connect(self._step_play)

    # ── 이벤트 필터 (휠 줌) ──────────────────────────────────────────────
    def eventFilter(self, obj, event):
        from PyQt6.QtCore import QEvent
        if obj is self._lbl_canvas and event.type() == QEvent.Type.Wheel:
            delta = event.angleDelta().y()
            self._zoom_step(0.85 if delta > 0 else 1.15)
            return True
        return super().eventFilter(obj, event)

    def _zoom_step(self, factor: float):
        self._zoom *= factor
        self._zoom = max(0.2, min(5.0, self._zoom))
        self._draw_frame(self._cur_idx)

    def _reset_zoom(self):
        self._zoom = 1.0
        self._draw_frame(self._cur_idx)

    # ── 공개 API ──────────────────────────────────────────────────────────
    _MAX_ANIM_FRAMES = 300  # 초과 시 서브샘플링 — 메인 스레드 시그널 폭주 방지

    def load_frames(self, frames):
        if len(frames) > self._MAX_ANIM_FRAMES:
            step = len(frames) / self._MAX_ANIM_FRAMES
            frames = [frames[int(i * step)] for i in range(self._MAX_ANIM_FRAMES)]
        self.frames = frames
        self._display_range = self._calc_range(frames)
        self._zoom = 1.0
        self._kill_frames = [
            i for i, f in enumerate(frames)
            if any('격추' in e or '요격' in e or '파괴' in e
                   for e in (f.events or []))
        ]
        if not frames:
            self._pixmaps = []
            return
        # 재생 중이었으면 중단 후 버튼/플래그 초기화
        if self._playing:
            self._play_timer.stop()
            self._playing = False
            self.btn_play.setText("▶ 재생")
        self.slider.setMaximum(len(frames) - 1)
        self.slider.setValue(0)
        self.btn_play.setEnabled(False)
        self._lbl_canvas.setText("렌더링 준비 중…")
        self._lbl_canvas.setStyleSheet(
            f"background:#0d1117; color:{C_SUBTEXT}; font-size:16px;")
        self._start_render_worker()

    # ── 내부 헬퍼 ─────────────────────────────────────────────────────────
    def _calc_range(self, frames) -> float:
        if not frames:
            return 350.0
        max_r = 150.0
        f = frames[0]
        for item in f.enemy_ships:
            max_r = max(max_r, abs(item[2]) / 1000, abs(item[3]) / 1000)
        for item in f.missiles:
            max_r = max(max_r, abs(item[1]) / 1000, abs(item[2]) / 1000)
        return max_r * 1.12

    def _start_render_worker(self):
        if not self.frames:
            return
        # 이전 워커 취소 — wait() 금지 (메인 스레드 블로킹 위험)
        # 세대 카운터를 올려 구식 frame_ready 신호를 _on_frame_ready에서 필터링
        self._render_gen += 1
        if self._render_worker and self._render_worker.isRunning():
            try:
                self._render_worker.frame_ready.disconnect()
                self._render_worker.all_done.disconnect()
            except Exception:
                pass
            self._render_worker.cancel()
            # wait() 제거 — cancel 플래그만 세우고 비동기 종료
        n = len(self.frames)
        self._pixmaps = [None] * n
        self._rendered_count = 0
        self._prog_render.setMaximum(n)
        self._prog_render.setValue(0)
        self._prog_render.show()
        frame_data = [
            {'t': f.t,
             'enemy_ships':   list(f.enemy_ships),
             'friendly_ships': list(f.friendly_ships),
             'missiles':      list(f.missiles),
             'events':        list(f.events or [])}
            for f in self.frames
        ]
        gen = self._render_gen
        self._render_worker = FrameRenderWorker(
            frame_data, self._display_range,
            self.chk_labels.isChecked(), self.chk_altitude.isChecked())
        self._render_worker.frame_ready.connect(
            lambda idx, png: self._on_frame_ready(idx, png, gen))
        self._render_worker.all_done.connect(self._on_all_done)
        self._render_worker.start(QThread.Priority.LowPriority)

    def _restart_render(self):
        if self.frames:
            self._start_render_worker()

    def _on_frame_ready(self, idx: int, png_bytes: bytes, gen: int):
        if gen != self._render_gen:
            return   # 이전 세대 신호 — 무시
        if idx < 0 or idx >= len(self._pixmaps):
            return   # 범위 초과 방어
        pm = QPixmap()
        pm.loadFromData(png_bytes, 'PNG')
        self._pixmaps[idx] = pm
        self._rendered_count += 1
        if self._rendered_count % 10 == 0 or self._rendered_count == len(self._pixmaps):
            self._prog_render.setValue(self._rendered_count)
        if idx == 0 or idx == self._cur_idx:
            self._draw_frame(idx)

    def _on_all_done(self):
        self._prog_render.hide()
        self.btn_play.setEnabled(True)
        self._lbl_canvas.setStyleSheet("background: #0d1117;")
        self._draw_frame(self._cur_idx)

    def _draw_frame(self, idx: int):
        self._cur_idx = idx
        if 0 <= idx < len(self.frames):
            f = self.frames[idx]
            self.lbl_time.setText(f"t = {f.t:.0f}s")
            self.lbl_events.setText('  |  '.join((f.events or [])[:4]))
        if not self._pixmaps or idx >= len(self._pixmaps):
            return
        pm = self._pixmaps[idx]
        if pm is None:
            self._lbl_canvas.setText(
                f"렌더링 중… ({self._rendered_count}/{len(self._pixmaps)})")
            return

        lw = max(1, self._lbl_canvas.width())
        lh = max(1, self._lbl_canvas.height())

        # 재생 중: FastTransformation(nearest-neighbor) — 속도 우선
        # 정지 시: SmoothTransformation(bilinear) — 품질 우선
        xform = (Qt.TransformationMode.FastTransformation if self._playing
                 else Qt.TransformationMode.SmoothTransformation)

        # 기본 fit (label 크기에 비율 유지하며 맞춤)
        fitted = pm.scaled(lw, lh, Qt.AspectRatioMode.KeepAspectRatio, xform)
        if abs(self._zoom - 1.0) < 0.02:
            self._lbl_canvas.setPixmap(fitted)
            return

        # 줌 적용: 1/zoom 배율로 fitted 재스케일
        sf  = 1.0 / self._zoom
        zw  = max(1, int(fitted.width()  * sf))
        zh  = max(1, int(fitted.height() * sf))
        zoomed = fitted.scaled(zw, zh,
                               Qt.AspectRatioMode.IgnoreAspectRatio, xform)
        if self._zoom < 1.0:
            # 줌인: 중앙 크롭
            fw, fh = fitted.width(), fitted.height()
            cx = max(0, (zoomed.width()  - fw) // 2)
            cy = max(0, (zoomed.height() - fh) // 2)
            zoomed = zoomed.copy(cx, cy,
                                 min(fw, zoomed.width()),
                                 min(fh, zoomed.height()))
        self._lbl_canvas.setPixmap(zoomed)

    def _toggle_play(self):
        if self._playing:
            self._play_timer.stop(); self._playing = False
            self.btn_play.setText("▶ 재생")
        else:
            self._play_timer.start(self._play_interval); self._playing = True
            self.btn_play.setText("⏸ 일시정지")

    def _step_play(self):
        v = self.slider.value()
        if v < self.slider.maximum():
            self.slider.setValue(v + 1)
        else:
            self._play_timer.stop(); self._playing = False
            self.btn_play.setText("▶ 재생")

    def _on_slider(self, val):
        if self.frames:
            self._draw_frame(val)

    def _set_speed(self, ms: int):
        self._play_interval = ms
        if self._playing:
            self._play_timer.setInterval(ms)

    def _prev_kill(self):
        if not self._kill_frames:
            return
        prev = [f for f in self._kill_frames if f < self._cur_idx]
        if prev:
            self.slider.setValue(prev[-1])

    def _next_kill(self):
        if not self._kill_frames:
            return
        nxt = [f for f in self._kill_frames if f > self._cur_idx]
        if nxt:
            self.slider.setValue(nxt[0])

    def _save_screenshot(self):
        pm = (self._pixmaps[self._cur_idx]
              if self._pixmaps and 0 <= self._cur_idx < len(self._pixmaps)
              else None)
        if pm is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "스크린샷 저장",
            f"전장_{self._cur_idx:04d}.png",
            "PNG (*.png)")
        if path:
            pm.save(path, 'PNG')


# ════════════════════════════════════════════════════════════════════════════
#  시스템 모니터 탭
# ════════════════════════════════════════════════════════════════════════════
class SysMonitorTab(QWidget):
    """실시간 시스템 모니터 — CPU/RAM/GPU/프로세스/코어/성능 기록."""

    def __init__(self):
        super().__init__()
        self._cpu_hist      = [0.0] * 60
        self._ram_hist      = [0.0] * 60
        self._gpu_hist      = [0.0] * 60
        self._core_pcts     = [0.0] * (os.cpu_count() or 4)
        self._worker_stats  = []
        self._sim_ranges     = []   # list of (start_wall_time, end_wall_time)
        self._sim_start_time = None  # wall-clock time when current sim started
        self._batch_done    = 0
        self._batch_total   = 0
        self._sim_speed     = 0.0
        self._sim_t0        = None
        self._sim_done      = 0
        self._build_ui()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update)
        self._timer.start(2000)   # 2초 간격 — 1초에서 낮춤 (메인 스레드 matplotlib 부하 감소)

    # ── 외부 슬롯 ────────────────────────────────────────────────────────────
    def mark_sim_start(self):
        self._sim_start_time = time.time()
        self._sim_t0   = time.time()
        self._sim_done = 0
        self._sim_speed = 0.0

    def mark_sim_end(self):
        if self._sim_start_time is not None:
            self._sim_ranges.append((self._sim_start_time, time.time()))
            self._sim_ranges = self._sim_ranges[-3:]
            self._sim_start_time = None
        self._batch_done = 0
        self._batch_total = 0
        self._prog_batch.setValue(0)
        self._lbl_batch.setText("배치 진행  대기 중")

    def on_batch_done(self, done: int, total: int):
        self._batch_done  = done
        self._batch_total = total
        self._prog_batch.setMaximum(max(total, 1))
        self._prog_batch.setValue(done)
        self._lbl_batch.setText(f"배치 진행  {done} / {total}")

    def on_progress_detail(self, done: int, total: int, eta: float):
        if self._sim_t0 and done > 0:
            elapsed = time.time() - self._sim_t0
            self._sim_speed = done / elapsed if elapsed > 0 else 0.0
            self._sim_done  = done

    # ── UI 빌더 ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(6)

        # 카드 행 1: 핵심 지표
        r1 = QHBoxLayout()
        self._c_cpu   = self._card("CPU 전체",  "0 %")
        self._c_ram   = self._card("RAM",       "0 %")
        self._c_thr   = self._card("스레드",     "0")
        self._c_gpu   = self._card("GPU",       "— %")
        self._c_ctemp = self._card("CPU 온도",   "— °C")
        self._c_speed = self._card("처리 속도",  "— 회/s")
        for c in (self._c_cpu, self._c_ram, self._c_thr,
                  self._c_gpu, self._c_ctemp, self._c_speed):
            r1.addWidget(c[0])
        root.addLayout(r1)

        # 카드 행 2: 메모리/GPU 상세
        r2 = QHBoxLayout()
        self._c_vram  = self._card("VRAM",      "— MB")
        self._c_gtemp = self._card("GPU 온도",   "— °C")
        self._c_phram = self._card("물리 RAM",   "— GB")
        self._c_vtram = self._card("가상 메모리", "— GB")
        self._c_prram = self._card("프로세스",   "— MB")
        for c in (self._c_vram, self._c_gtemp, self._c_phram,
                  self._c_vtram, self._c_prram):
            r2.addWidget(c[0])
        root.addLayout(r2)

        # 배치 진행 바
        br = QHBoxLayout()
        self._lbl_batch = QLabel("배치 진행  대기 중")
        self._lbl_batch.setStyleSheet(f"color:{C_SUBTEXT}; font-size:12px;")
        self._prog_batch = QProgressBar()
        self._prog_batch.setRange(0, 1); self._prog_batch.setValue(0)
        self._prog_batch.setFixedHeight(12)
        self._prog_batch.setStyleSheet(f"""
            QProgressBar {{ background:{C_PANEL}; border-radius:4px; border:1px solid {C_BORDER}; }}
            QProgressBar::chunk {{ background:{C_ACCENT}; border-radius:3px; }}
        """)
        br.addWidget(self._lbl_batch)
        br.addWidget(self._prog_batch, 1)
        root.addLayout(br)

        # 내부 탭
        self._inner = QTabWidget()
        self._inner.addTab(self._build_sys_tab(),  "📊  시스템")
        self._inner.addTab(self._build_proc_tab(), "⚙️  프로세스")
        self._inner.addTab(self._build_gpu_tab(),  "🎮  GPU")
        self._inner.addTab(self._build_hist_tab(), "📈  성능 기록")
        root.addWidget(self._inner)

    def _card(self, title: str, init: str):
        box = QGroupBox(title)
        box.setFixedHeight(68)
        lay = QVBoxLayout(box)
        lay.setContentsMargins(4, 2, 4, 2)
        lbl = QLabel(init)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setFont(QFont('Malgun Gothic', 14, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color:{C_ACCENT};")
        lay.addWidget(lbl)
        return box, lbl

    def _build_sys_tab(self) -> QWidget:
        w = QWidget(); lay = QHBoxLayout(w); lay.setContentsMargins(0, 6, 0, 0)
        self._sys_canvas = MplCanvas(figsize=(6, 3))
        lay.addWidget(self._sys_canvas, 3)
        # 코어별 바
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        inner = QWidget(); inner.setStyleSheet(f"background:{C_BG};")
        cl = QVBoxLayout(inner); cl.setSpacing(2); cl.setContentsMargins(6, 6, 6, 6)
        self._core_bars = []
        for i in range(os.cpu_count() or 4):
            row = QHBoxLayout()
            lbl = QLabel(f"C{i:02d}"); lbl.setFixedWidth(32)
            lbl.setStyleSheet(f"color:{C_SUBTEXT}; font-size:12px;")
            bar = QProgressBar(); bar.setRange(0, 100); bar.setValue(0)
            bar.setFixedHeight(14); bar.setTextVisible(False)
            bar.setStyleSheet(f"""
                QProgressBar {{ background:{C_PANEL}; border-radius:3px; border:none; }}
                QProgressBar::chunk {{ background:{C_ACCENT}; border-radius:2px; }}
            """)
            plbl = QLabel("0%"); plbl.setFixedWidth(42)
            plbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            plbl.setStyleSheet(f"color:{C_TEXT}; font-size:12px; font-weight:bold;")
            row.addWidget(lbl); row.addWidget(bar, 1); row.addWidget(plbl)
            cl.addLayout(row)
            self._core_bars.append((bar, plbl))
        cl.addStretch(); scroll.setWidget(inner)
        lay.addWidget(scroll, 2)
        return w

    def _build_proc_tab(self) -> QWidget:
        w = QWidget(); lay = QVBoxLayout(w); lay.setContentsMargins(0, 6, 0, 0)
        lbl = QLabel("워커 프로세스 (ProcessPoolExecutor 자식 프로세스)")
        lbl.setStyleSheet(f"color:{C_SUBTEXT}; font-size:11px;")
        lay.addWidget(lbl)
        self._proc_tbl = QTableWidget(0, 4)
        self._proc_tbl.setHorizontalHeaderLabels(["PID", "CPU %", "RAM (MB)", "상태"])
        hh = self._proc_tbl.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._proc_tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._proc_tbl.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self._proc_tbl.verticalHeader().setVisible(False)
        self._proc_tbl.setStyleSheet(f"background:{C_BG};")
        lay.addWidget(self._proc_tbl)
        return w

    def _build_gpu_tab(self) -> QWidget:
        w = QWidget(); lay = QVBoxLayout(w); lay.setContentsMargins(0, 6, 0, 0)
        self._gpu_canvas = MplCanvas(figsize=(8, 3))
        lay.addWidget(self._gpu_canvas)
        return w

    def _build_hist_tab(self) -> QWidget:
        w = QWidget(); lay = QVBoxLayout(w); lay.setContentsMargins(0, 6, 0, 0)
        lbl = QLabel("최근 시뮬레이션 실행 기록 (최대 10회)")
        lbl.setStyleSheet(f"color:{C_SUBTEXT}; font-size:11px;")
        lay.addWidget(lbl)
        self._hist_tbl = QTableWidget(0, 4)
        self._hist_tbl.setHorizontalHeaderLabels(["실행 시각", "MC 횟수", "소요 시간", "처리 속도"])
        hh = self._hist_tbl.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._hist_tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._hist_tbl.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self._hist_tbl.verticalHeader().setVisible(False)
        self._hist_tbl.setStyleSheet(f"background:{C_BG};")
        lay.addWidget(self._hist_tbl)
        self._hist_canvas = MplCanvas(figsize=(8, 2))
        lay.addWidget(self._hist_canvas)
        return w

    # ── 업데이트 루프 ─────────────────────────────────────────────────────────
    def _update(self):
        # 블로킹 호출 없음 — _SysDataWorker가 채운 캐시만 읽음
        c        = _SYS_CACHE
        cpu      = c['cpu']
        cores    = c.get('cores', [])
        mem_pct  = c['mem_pct']
        gpu      = c['gpu']
        ctemp    = c['cpu_temp']
        proc_ram = c['proc_ram']
        self._worker_stats = c.get('worker_stats', [])

        self._cpu_hist = self._cpu_hist[1:] + [cpu]
        self._ram_hist = self._ram_hist[1:] + [mem_pct]
        self._gpu_hist = self._gpu_hist[1:] + [float(gpu.get('util', 0))]
        if cores:
            self._core_pcts = list(cores)

        # 카드 행 1
        self._c_cpu[1].setText(f"{cpu:.0f} %")
        self._c_ram[1].setText(f"{mem_pct:.0f} %")
        self._c_thr[1].setText(str(c.get('thread_cnt', threading.active_count())))
        self._c_gpu[1].setText(f"{gpu['util']} %" if 'util' in gpu else "— %")
        self._c_ctemp[1].setText(f"{ctemp:.0f} °C" if ctemp >= 0 else "— °C")
        self._c_speed[1].setText(f"{self._sim_speed:.0f} 회/s" if self._sim_speed > 0 else "— 회/s")

        # 카드 행 2
        mu, mt = gpu.get('mem_used'), gpu.get('mem_total')
        self._c_vram[1].setText(f"{mu}/{mt} MB" if mu is not None else "— MB")
        self._c_gtemp[1].setText(f"{gpu['temp']} °C" if 'temp' in gpu else "— °C")
        mem_used_gb  = c.get('mem_used', 0) / 1024**3
        mem_total_gb = c.get('mem_total', 1) / 1024**3
        self._c_phram[1].setText(f"{mem_used_gb:.1f}/{mem_total_gb:.0f} GB")
        self._c_vtram[1].setText(f"{c.get('swap_used', 0)/1024**3:.1f} GB")
        self._c_prram[1].setText(f"{proc_ram:.0f} MB")

        # 코어별 바
        for i, (bar, plbl) in enumerate(self._core_bars):
            pct = int(self._core_pcts[i]) if i < len(self._core_pcts) else 0
            bar.setValue(pct); plbl.setText(f"{pct}%")

        # 탭별 차트 갱신 — 화면에 표시 중일 때만 렌더 (숨겨진 탭은 스킵)
        if self.isVisible():
            self._refresh_active_chart()

    def showEvent(self, event):
        """사이드바에서 이 탭으로 전환될 때 즉시 차트 갱신 (타이머 대기 불필요)."""
        super().showEvent(event)
        self._refresh_active_chart()

    def _refresh_active_chart(self):
        idx = self._inner.currentIndex()
        if idx == 0:
            self._draw_sys_chart()
        elif idx == 1:
            self._update_proc_table()
        elif idx == 2:
            self._draw_gpu_chart()
        elif idx == 3:
            self._draw_hist_tab()

    def _draw_sys_chart(self):
        fig = self._sys_canvas.fig; fig.clear()
        fig.patch.set_facecolor(C_BG)
        ax = fig.add_subplot(111, facecolor='#0a0e1a')
        ax.tick_params(colors='#aab', labelsize=8)
        for sp in ax.spines.values(): sp.set_color('#1e2a3a')
        ax.set_ylim(0, 100); ax.set_xlim(0, 59)
        ax.set_xlabel('경과 (초)', color='#aab', fontsize=8)
        ax.set_ylabel('사용률 (%)', color='#aab', fontsize=8)
        ax.set_title('CPU / RAM (최근 60초)', color='#dde', fontsize=9, fontweight='bold')
        ax.grid(color='#1e2a3a', linewidth=0.5)
        ax.plot(self._cpu_hist, color=C_ACCENT, lw=1.5, label='CPU')
        ax.plot(self._ram_hist, color=C_ORANGE, lw=1.5, label='RAM')
        now = time.time()
        for st, et in self._sim_ranges:
            # x=59 is now, older data is further left
            sx = max(0, 59 - int(now - st))
            ex = min(59, 59 - int(now - et))
            if sx <= 59 and ex >= 0:
                ax.axvspan(sx, max(sx + 1, ex), color='#f1c40f', alpha=0.12, zorder=0)
        if self._sim_start_time is not None:
            sx = max(0, 59 - int(now - self._sim_start_time))
            ax.axvspan(sx, 59, color='#f1c40f',
                       alpha=0.18, zorder=0, label='시뮬 실행 중')
        ax.legend(fontsize=8, facecolor='#0a0e1a', labelcolor='white', edgecolor='#1e2a3a')
        self._sys_canvas.draw_idle()   # BUG-1: draw_idle()로 UI 블로킹 방지

    def _draw_gpu_chart(self):
        fig = self._gpu_canvas.fig; fig.clear()
        fig.patch.set_facecolor(C_BG)
        ax = fig.add_subplot(111, facecolor='#0a0e1a')
        ax.tick_params(colors='#aab', labelsize=8)
        for sp in ax.spines.values(): sp.set_color('#1e2a3a')
        ax.set_ylim(0, 100); ax.set_xlim(0, 59)
        ax.set_xlabel('경과 (초)', color='#aab', fontsize=8)
        ax.set_ylabel('GPU 사용률 (%)', color='#aab', fontsize=8)
        ax.set_title('GPU 사용률 (최근 60초)', color='#dde', fontsize=9, fontweight='bold')
        ax.grid(color='#1e2a3a', linewidth=0.5)
        ax.plot(self._gpu_hist, color='#2ecc71', lw=1.5, label='GPU')
        ax.legend(fontsize=8, facecolor='#0a0e1a', labelcolor='white', edgecolor='#1e2a3a')
        self._gpu_canvas.draw_idle()   # BUG-1

    def _update_proc_table(self):
        self._proc_tbl.setRowCount(0)
        for w in self._worker_stats:
            r = self._proc_tbl.rowCount(); self._proc_tbl.insertRow(r)
            vals = [str(w['pid']), f"{w['cpu']:.1f}%",
                    f"{w['ram']:.0f} MB", w['status']]
            for col, txt in enumerate(vals):
                item = QTableWidgetItem(txt)
                if col == 1 and w['cpu'] > 50:
                    item.setForeground(QColor(C_ACCENT))
                self._proc_tbl.setItem(r, col, item)

    def _draw_hist_tab(self):
        from datetime import datetime
        self._hist_tbl.setRowCount(0)
        for rec in _PERF_HISTORY:
            r = self._hist_tbl.rowCount(); self._hist_tbl.insertRow(r)
            ts = datetime.fromtimestamp(rec['time']).strftime('%H:%M:%S')
            for col, txt in enumerate([
                ts, str(rec.get('mc_n', '—')),
                f"{rec.get('duration', 0):.1f}초",
                f"{rec.get('rate', 0):.1f} 회/s"
            ]):
                self._hist_tbl.setItem(r, col, QTableWidgetItem(txt))
        if _PERF_HISTORY:
            fig = self._hist_canvas.fig; fig.clear()
            fig.patch.set_facecolor(C_BG)
            ax = fig.add_subplot(111, facecolor='#0a0e1a')
            rates = [rec.get('rate', 0) for rec in _PERF_HISTORY]
            ax.bar(range(len(rates)), rates, color=C_ACCENT, alpha=0.8)
            ax.set_ylabel('회/초', color='#aab', fontsize=8)
            ax.set_title('처리 속도 추이', color='#dde', fontsize=9, fontweight='bold')
            ax.tick_params(colors='#aab', labelsize=8)
            for sp in ax.spines.values(): sp.set_color('#1e2a3a')
            ax.grid(color='#1e2a3a', linewidth=0.5, axis='y')
            self._hist_canvas.draw_idle()   # BUG-1


# ════════════════════════════════════════════════════════════════════════════
#  차트 순수 렌더 함수 (백그라운드 스레드에서 호출, Figure 반환)
# ════════════════════════════════════════════════════════════════════════════

def _render_sensitivity_chart(labels: list, lows: list, highs: list, base_rate: float) -> Figure:
    """감도 분석 Tornado chart — 백그라운드 스레드에서 호출."""
    fig = Figure(figsize=(12, 6), facecolor=C_BG)
    fig.patch.set_facecolor('#0a0e1a')
    ax = fig.add_subplot(111, facecolor='#0a0e1a')
    y = list(range(len(labels)))
    ax.barh(y, lows,  color='#e74c3c', alpha=0.8, label='낮은값')
    ax.barh(y, highs, color='#2ecc71', alpha=0.8, label='높은값')
    ax.axvline(0, color=C_TEXT, lw=1)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, color=C_TEXT, fontsize=12)
    ax.set_xlabel('요격률 변화 (기준 대비)', color=C_SUBTEXT, fontsize=12)
    ax.set_title(f'감도 분석 — Tornado chart  (기준 요격률 {base_rate:.1%})',
                 color=C_TEXT, fontsize=14)
    ax.tick_params(colors=C_SUBTEXT, labelsize=11)
    from matplotlib.ticker import FuncFormatter
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:+.1%}"))
    for sp in ax.spines.values(): sp.set_color('#1e2a3a')
    ax.legend(fontsize=11, facecolor='#0a0e1a', labelcolor=C_TEXT, edgecolor='#1e2a3a')
    fig.tight_layout()
    return fig


def _render_min_stock_chart(results: dict, target_rate: float) -> Figure:
    """최소 재고 역산 수평 막대 차트 — 백그라운드 스레드에서 호출."""
    fig = Figure(figsize=(13, 6), facecolor=C_BG)
    fig.patch.set_facecolor('#0a0e1a')
    ax = fig.add_subplot(111, facecolor='#0a0e1a')
    short_names = {
        'SM-3 Block IIA':   'SM-3 IIA',
        'SM-6':             'SM-6',
        'SM-2 Block IIIB':  'SM-2 IIIB',
        'RIM-116 RAM':      'RIM-116 RAM',
        '홍상어 (대잠)':    '홍상어',
        '청상어 (경어뢰)':  '청상어',
    }
    wpn_names = list(results.keys())
    labels   = [short_names.get(w, w) for w in wpn_names]
    currents = [results[w]['current_stock'] for w in wpn_names]
    mins     = [results[w]['min_stock']     for w in wpn_names]
    achieves = [results[w]['achievable']    for w in wpn_names]
    y = list(range(len(wpn_names)))
    ax.barh(y, currents, color='#2a3545', height=0.55, label='현재 재고')
    for i, (mn, cur, ach) in enumerate(zip(mins, currents, achieves)):
        if not ach:
            color, bar_val = '#e74c3c', cur
        elif mn == 0:
            color, bar_val = '#3498db', 0
        elif mn <= cur:
            color, bar_val = '#2ecc71', mn
        else:
            color, bar_val = '#e67e22', mn
        ax.barh(i, bar_val, color=color, height=0.55, alpha=0.9)
        if not ach:
            txt = '달성 불가'
        elif mn == 0:
            txt = '불필요'
        else:
            saving = cur - mn
            txt = f'최소 {mn}발  ({"▼ " + str(saving) + "발 절약" if saving > 0 else ("▲ " + str(-saving) + "발 부족" if saving < 0 else "현재 최적")})'
        ax.text(max(cur, mn) + 0.5, i, txt, va='center', color=C_TEXT, fontsize=11)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, color=C_TEXT, fontsize=13)
    ax.set_xlabel('재고 수량 (함정당)', color=C_SUBTEXT, fontsize=12)
    ax.set_title(
        f'REQ 달성 최소 재고 역산  (목표: 완전 요격 성공률 ≥ {target_rate:.0%})\n'
        '■ 현재 재고  ■ 최소 필요  (녹색=절약 가능 / 주황=부족 / 파랑=불필요)',
        color=C_TEXT, fontsize=13, pad=10,
    )
    max_x = max(currents + [m for m in mins if m >= 0], default=50)
    ax.set_xlim(0, max_x * 1.35)
    ax.tick_params(colors=C_SUBTEXT, labelsize=11)
    for sp in ax.spines.values(): sp.set_color('#1e2a3a')
    ax.legend(fontsize=11, facecolor='#0a0e1a', labelcolor=C_TEXT,
              edgecolor='#1e2a3a', loc='lower right')
    fig.tight_layout()
    return fig


def _render_mc_chart(result: dict, mc: dict, cfg: dict) -> bytes:
    """MC 통계: plot_v7 PNG를 bytes로 직접 반환 (이중 렌더 제거)."""
    import tempfile, uuid as _uuid
    img_path = os.path.join(tempfile.gettempdir(),
                            f'mc_chart_{_uuid.uuid4().hex}.png')
    try:
        plot_v7(result, mc, cfg, img_path=img_path)
        if os.path.exists(img_path):
            with open(img_path, 'rb') as f:
                return f.read()
    finally:
        try:
            os.remove(img_path)
        except Exception:
            pass
    return b''


def _render_channel_heatmap(result: dict) -> Figure:
    frames = result.get('frames', [])
    fig = Figure(figsize=(12, 5), facecolor=C_BG)
    if not frames or not getattr(frames[0], 'ship_channels', None):
        ax = fig.add_subplot(111, facecolor='#0a0e1a')
        ax.text(0.5, 0.5, '채널 데이터 없음\n(시뮬레이션 재실행 필요)',
                ha='center', va='center', color='#7d8590',
                fontsize=12, transform=ax.transAxes)
        return fig
    ship_names = [sc[0] for sc in frames[0].ship_channels]
    times = [f.t for f in frames]
    usage = np.zeros((len(ship_names), len(frames)))
    for fi, frame in enumerate(frames):
        for si, sc in enumerate(frame.ship_channels):
            _, ch_used, ch_max = sc
            usage[si, fi] = ch_used / ch_max if ch_max > 0 else 0.0
    ax = fig.add_subplot(111, facecolor='#0a0e1a')
    im = ax.imshow(usage, aspect='auto',
                   extent=[times[0], times[-1], -0.5, len(ship_names) - 0.5],
                   origin='lower', cmap='RdYlGn_r', vmin=0, vmax=1,
                   interpolation='nearest')
    ax.set_yticks(range(len(ship_names)))
    ax.set_yticklabels(ship_names, color='#aab', fontsize=12)
    ax.set_xlabel('시간 (s)', color='#aab', fontsize=12)
    ax.set_title('채널 포화도  (빨강=포화, 초록=여유)', color='#dde', fontsize=14)
    ax.tick_params(colors='#aab', labelsize=11)
    for sp in ax.spines.values():
        sp.set_color('#1e2a3a')
    cbar = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cbar.ax.tick_params(colors='#aab', labelsize=10)
    cbar.set_label('채널 사용률', color='#aab', fontsize=11)
    fig.tight_layout()
    return fig


def _render_cost_effect(result: dict, mc: dict) -> Figure:
    fig = Figure(figsize=(12, 5), facecolor=C_BG)
    costs     = mc.get('total_costs', [])
    e_dest    = mc.get('enemy_destroyed', [])
    mean_cost = float(np.mean(costs)) if costs else 0.0
    mean_kill = float(np.mean(e_dest)) if e_dest else 0.0
    cost_per_kill = mean_cost / mean_kill if mean_kill > 0 else float('inf')
    wpn_rem = mc.get('weapon_avg_remaining', {})
    if wpn_rem:
        gs = fig.add_gridspec(1, 2, wspace=0.35)
        ax1 = fig.add_subplot(gs[0], facecolor='#0a0e1a')
        ax2 = fig.add_subplot(gs[1], facecolor='#0a0e1a')
    else:
        ax1 = fig.add_subplot(111, facecolor='#0a0e1a')
        ax2 = None
    ax1.axis('off')
    lbl = f"${cost_per_kill:,.0f}" if cost_per_kill != float('inf') else "N/A"
    ax1.text(0.5, 0.6, lbl, ha='center', va='center',
             color=C_GREEN, fontsize=30, fontweight='bold',
             transform=ax1.transAxes)
    ax1.text(0.5, 0.35, '격추 1건당 평균 비용', ha='center', va='center',
             color=C_TEXT, fontsize=14, transform=ax1.transAxes)
    ax1.text(0.5, 0.20, f"총 평균 비용 ${mean_cost:,.0f}  |  평균 격침 {mean_kill:.1f}척",
             ha='center', va='center', color=C_SUBTEXT, fontsize=12,
             transform=ax1.transAxes)
    ax1.set_facecolor('#0a0e1a')
    if ax2 and wpn_rem:
        names = list(wpn_rem.keys())
        vals  = [wpn_rem[n] for n in names]
        colors = [C_GREEN if v > 5 else C_ORANGE if v > 0 else C_RED for v in vals]
        y = range(len(names))
        ax2.barh(list(y), vals, color=colors, height=0.6)
        ax2.set_yticks(list(y))
        ax2.set_yticklabels(names, color=C_TEXT, fontsize=11)
        ax2.set_xlabel('평균 잔여 재고 (발)', color=C_SUBTEXT, fontsize=12)
        ax2.set_title('무기별 평균 잔여 재고', color=C_TEXT, fontsize=13)
        ax2.tick_params(colors=C_SUBTEXT, labelsize=11)
        for sp in ax2.spines.values():
            sp.set_color('#1e2a3a')
    fig.tight_layout()
    return fig


def _render_ammo_curve(mc: dict) -> Figure:
    fig = Figure(figsize=(12, 5), facecolor=C_BG)
    ax = fig.add_subplot(111, facecolor='#0a0e1a')
    wpn_rem = mc.get('weapon_avg_remaining', {})
    if not wpn_rem:
        ax.text(0.5, 0.5, '데이터 없음\n(시뮬레이션 재실행 필요)',
                ha='center', va='center', color=C_SUBTEXT,
                fontsize=12, transform=ax.transAxes)
        fig.tight_layout()
        return fig
    names = list(wpn_rem.keys())
    vals  = [wpn_rem[n] for n in names]
    y     = np.arange(len(names))
    bars  = ax.barh(y, vals, color=C_ACCENT, height=0.55, alpha=0.85)
    for bar, val in zip(bars, vals):
        ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                f'{val:.1f}', va='center', color=C_TEXT, fontsize=11)
    ax.set_yticks(y)
    ax.set_yticklabels(names, color=C_TEXT, fontsize=12)
    ax.set_xlabel('MC 평균 잔여 재고 (발)', color=C_SUBTEXT, fontsize=12)
    ax.set_title('무기별 평균 잔여 재고 (MC 전체 평균)', color=C_TEXT, fontsize=13)
    ax.tick_params(colors=C_SUBTEXT, labelsize=11)
    for sp in ax.spines.values():
        sp.set_color('#1e2a3a')
    fig.tight_layout()
    return fig


def _render_ci_chart(mc: dict) -> Figure:
    fig = Figure(figsize=(12, 5), facecolor=C_BG)
    rates = mc.get('intercept_rates', [])
    if not rates:
        ax = fig.add_subplot(111, facecolor='#0a0e1a')
        ax.text(0.5, 0.5, '데이터 없음', ha='center', va='center',
                color=C_SUBTEXT, fontsize=12, transform=ax.transAxes)
        fig.tight_layout()
        return fig
    arr   = np.array(rates)
    mean  = float(arr.mean())
    std   = float(arr.std())
    ci_lo = max(0.0, mean - 1.96 * std / np.sqrt(len(arr)))
    ci_hi = min(1.0, mean + 1.96 * std / np.sqrt(len(arr)))
    gs = fig.add_gridspec(1, 2, wspace=0.35)
    ax1 = fig.add_subplot(gs[0], facecolor='#0a0e1a')
    ax2 = fig.add_subplot(gs[1], facecolor='#0a0e1a')
    ax1.hist(arr, bins=20, color=C_ACCENT, alpha=0.75, edgecolor='#1e2a3a')
    ax1.axvline(mean,  color=C_GREEN,  lw=2, label=f'평균 {mean:.1%}')
    ax1.axvline(ci_lo, color=C_ORANGE, lw=1.5, ls='--', label=f'CI 하한 {ci_lo:.1%}')
    ax1.axvline(ci_hi, color=C_ORANGE, lw=1.5, ls='--', label=f'CI 상한 {ci_hi:.1%}')
    ax1.set_xlabel('요격률', color=C_SUBTEXT, fontsize=12)
    ax1.set_ylabel('빈도', color=C_SUBTEXT, fontsize=12)
    ax1.set_title(f'요격률 분포 (n={len(arr)})', color=C_TEXT, fontsize=13)
    ax1.legend(fontsize=11, facecolor='#0a0e1a', labelcolor=C_TEXT, edgecolor='#1e2a3a')
    ax1.tick_params(colors=C_SUBTEXT, labelsize=11)
    for sp in ax1.spines.values():
        sp.set_color('#1e2a3a')
    ship_hits = mc.get('ship_avg_hits', {})
    if ship_hits:
        snames = list(ship_hits.keys())
        shvals = [ship_hits[s] for s in snames]
        y      = np.arange(len(snames))
        clrs   = [C_RED if v > 1 else C_ORANGE if v > 0 else C_GREEN for v in shvals]
        ax2.barh(y, shvals, color=clrs, height=0.55)
        ax2.set_yticks(y)
        ax2.set_yticklabels(snames, color=C_TEXT, fontsize=11)
        ax2.set_xlabel('평균 피격 횟수', color=C_SUBTEXT, fontsize=12)
        ax2.set_title('함정별 평균 피격', color=C_TEXT, fontsize=13)
        ax2.tick_params(colors=C_SUBTEXT, labelsize=11)
        for sp in ax2.spines.values():
            sp.set_color('#1e2a3a')
    else:
        ax2.axis('off')
        ax2.text(0.5, 0.5, '피격 데이터 없음', ha='center', va='center',
                 color=C_SUBTEXT, fontsize=10, transform=ax2.transAxes)
    fig.tight_layout()
    return fig


def _render_timeline(result: dict) -> Figure:
    fig = Figure(figsize=(14, 5), facecolor=C_BG)
    ax = fig.add_subplot(111, facecolor='#0a0e1a')
    log = result.get('log', [])
    if not log:
        ax.text(0.5, 0.5, '로그 데이터 없음', ha='center', va='center',
                color=C_SUBTEXT, fontsize=12, transform=ax.transAxes)
        fig.tight_layout()
        return fig
    _CAT = [
        ('[방어]',     C_GREEN,  '방어 발사',  0),
        ('[대공 방어]', C_ACCENT, '대공 발사',  1),
        ('[공격]',     '#e67e22','대함 공격',  2),
        ('[대잠 공격]', '#9b59b6','대잠 공격',  3),
        ('[피격]',     C_RED,    '피격',       4),
        ('[경고]',     C_ORANGE, '경고',       5),
        ('[적 발사]',  '#c0392b','적 발사',    6),
    ]
    events = []
    for t, msg in log:
        for tag, color, label, yi in _CAT:
            if tag in msg:
                events.append((t, yi, color, label, msg[:60]))
                break
    if not events:
        ax.text(0.5, 0.5, '분류 가능한 이벤트 없음', ha='center', va='center',
                color=C_SUBTEXT, fontsize=12, transform=ax.transAxes)
        fig.tight_layout()
        return fig
    y_labels = ['방어 발사', '대공 발사', '대함 공격', '대잠 공격', '피격', '경고', '적 발사']
    for t, yi, color, label, msg in events:
        ax.scatter(t, yi, c=color, s=30, zorder=3, alpha=0.8)
    ax.set_yticks(range(len(y_labels)))
    ax.set_yticklabels(y_labels, color=C_TEXT, fontsize=12)
    ax.set_xlabel('시뮬 시각 (초)', color=C_SUBTEXT, fontsize=12)
    ax.set_title('교전 이벤트 타임라인', color=C_TEXT, fontsize=14)
    ax.tick_params(colors=C_SUBTEXT, labelsize=11)
    ax.set_ylim(-0.8, len(y_labels) - 0.2)
    for sp in ax.spines.values():
        sp.set_color('#1e2a3a')
    ax.grid(axis='x', color='#1e2a3a', lw=0.5)
    handles = [plt.Line2D([0], [0], marker='o', color='w',
                           markerfacecolor=c, markersize=9, label=l)
               for _, c, l, _ in _CAT]
    ax.legend(handles=handles, fontsize=10, facecolor='#0a0e1a',
              labelcolor=C_TEXT, edgecolor='#1e2a3a',
              loc='upper right', ncol=4)
    fig.tight_layout()
    return fig


def _render_bearing_vulnerability(result: dict) -> Figure:
    fig = Figure(figsize=(8, 8), facecolor='#0a0e1a')
    ax = fig.add_subplot(111, polar=True)
    ax.set_facecolor('#0a0e1a')
    log = result.get('log', [])
    N = 8
    hit_counts  = [0] * N
    kill_counts = [0] * N
    for _, msg in log:
        bearing_deg = None
        if '방위' in msg:
            try:
                bearing_deg = float(msg.split('방위')[1].split('°')[0])
            except Exception:
                pass
        if bearing_deg is None:
            bearing_deg = hash(msg) % 360
        sector = int((bearing_deg % 360) / (360 / N))
        if '[피격]' in msg:
            hit_counts[sector]  += 1
        elif '[격추]' in msg or '[요격]' in msg:
            kill_counts[sector] += 1
    angles   = np.linspace(0, 2 * np.pi, N, endpoint=False)
    hit_arr  = np.array(hit_counts,  dtype=float)
    kill_arr = np.array(kill_counts, dtype=float)
    max_val  = max(hit_arr.max(), kill_arr.max(), 1)
    hit_arr  /= max_val
    kill_arr /= max_val
    angles_c = np.concatenate([angles, [angles[0]]])
    hit_c    = np.concatenate([hit_arr,  [hit_arr[0]]])
    kill_c   = np.concatenate([kill_arr, [kill_arr[0]]])
    sector_labels = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    ax.plot(angles_c, kill_c, 'o-', color='#2ecc71', lw=1.5, label='요격')
    ax.fill(angles_c, kill_c, alpha=0.2, color='#2ecc71')
    ax.plot(angles_c, hit_c,  'o-', color='#e74c3c', lw=1.5, label='피격')
    ax.fill(angles_c, hit_c,  alpha=0.2, color='#e74c3c')
    ax.set_xticks(angles)
    ax.set_xticklabels(sector_labels, color=C_TEXT, fontsize=12)
    ax.set_yticklabels([])
    ax.set_title('방위각 취약점 분석', color=C_TEXT, fontsize=14, pad=15)
    ax.tick_params(colors=C_SUBTEXT)
    ax.spines['polar'].set_color('#1e2a3a')
    ax.grid(color='#1e2a3a')
    ax.legend(loc='upper right', fontsize=11, facecolor='#0a0e1a',
              labelcolor=C_TEXT, edgecolor='#1e2a3a',
              bbox_to_anchor=(1.25, 1.1))
    fig.tight_layout()
    return fig


def _render_req_radar(result: dict, mc: dict) -> Figure:
    fig = Figure(figsize=(8, 8), facecolor='#0a0e1a')
    if not _V7_OK:
        ax = fig.add_subplot(111)
        ax.text(0.5, 0.5, 'v7 엔진 미로드', ha='center', va='center',
                color=C_SUBTEXT, fontsize=12, transform=ax.transAxes)
        return fig
    try:
        verdicts, _ = evaluate_req_v7(result, mc)
    except Exception:
        return fig
    ax = fig.add_subplot(111, polar=True)
    ax.set_facecolor('#0a0e1a')
    labels = [r['id'] for r in REQ_ITEMS_V7]
    N = len(labels)
    if N == 0:
        return fig
    vals     = [1.0 if v else 0.0 for v in verdicts]
    angles   = np.linspace(0, 2 * np.pi, N, endpoint=False)
    vals_c   = np.concatenate([vals,   [vals[0]]])
    angles_c = np.concatenate([angles, [angles[0]]])
    ax.plot(angles_c, vals_c, 'o-', color=C_ACCENT, lw=2)
    ax.fill(angles_c, vals_c, alpha=0.3, color=C_ACCENT)
    ax.set_xticks(angles)
    ax.set_xticklabels(labels, color=C_TEXT, fontsize=12)
    ax.set_yticks([0, 0.5, 1.0])
    ax.set_yticklabels(['FAIL', '', 'PASS'], color=C_SUBTEXT, fontsize=10)
    ax.set_ylim(0, 1.2)
    pass_cnt = sum(verdicts)
    ax.set_title(f'REQ 충족률  {pass_cnt}/{N}  ({pass_cnt/N:.0%})',
                 color=C_TEXT, fontsize=14, pad=15)
    ax.spines['polar'].set_color('#1e2a3a')
    ax.grid(color='#1e2a3a')
    fig.tight_layout()
    return fig


def _render_threat_type(result: dict, mc: dict) -> Figure:
    fig = Figure(figsize=(12, 5), facecolor=C_BG)
    ax = fig.add_subplot(111, facecolor='#0a0e1a')
    if not _V7_OK:
        ax.text(0.5, 0.5, 'v7 엔진 미로드', ha='center', va='center',
                color=C_SUBTEXT, fontsize=12, transform=ax.transAxes)
        return fig
    log = result.get('log', [])
    categories = {
        '항공기':     {'intercept': 0, 'total': 0},
        '탄도탄':     {'intercept': 0, 'total': 0},
        '순항미사일': {'intercept': 0, 'total': 0},
        '잠수함':     {'intercept': 0, 'total': 0},
        '기타':       {'intercept': 0, 'total': 0},
    }
    def _classify(msg: str) -> str:
        for kw, cat in [
            ('항공', '항공기'), ('KH-', '항공기'), ('Su-', '항공기'),
            ('화성', '탄도탄'), ('SM-3', '탄도탄'), ('탄도', '탄도탄'),
            ('순항', '순항미사일'), ('Kh-', '순항미사일'), ('화살', '순항미사일'),
            ('지르콘', '순항미사일'), ('킨잘', '순항미사일'),
            ('잠수함', '잠수함'), ('어뢰', '잠수함'), ('수중', '잠수함'),
        ]:
            if kw in msg:
                return cat
        return '기타'
    for _, msg in log:
        if '[요격]' in msg or '[격추]' in msg:
            cat = _classify(msg)
            categories[cat]['total']     += 1
            categories[cat]['intercept'] += 1
        elif '[피격]' in msg or '[통과]' in msg:
            cat = _classify(msg)
            categories[cat]['total'] += 1
    labels = [k for k, v in categories.items() if v['total'] > 0]
    if not labels:
        ax.text(0.5, 0.5, '데이터 없음', ha='center', va='center',
                color=C_SUBTEXT, fontsize=12, transform=ax.transAxes)
        return fig
    rates  = [categories[l]['intercept'] / max(categories[l]['total'], 1)
              for l in labels]
    totals = [categories[l]['total'] for l in labels]
    colors = ['#3498db', '#e74c3c', '#f39c12', '#2ecc71', '#9b59b6']
    bars = ax.bar(labels, rates,
                  color=colors[:len(labels)], alpha=0.85, edgecolor='#1e2a3a')
    for bar, t, r in zip(bars, totals, rates):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.02,
                f'{r:.0%}\n(n={t})',
                ha='center', va='bottom', color=C_TEXT, fontsize=12)
    ax.set_ylim(0, 1.2)
    ax.set_ylabel('요격률', color=C_SUBTEXT, fontsize=12)
    ax.set_title('위협 유형별 요격률', color=C_TEXT, fontsize=14)
    ax.tick_params(colors=C_SUBTEXT, labelsize=12)
    for sp in ax.spines.values():
        sp.set_color('#1e2a3a')
    ax.axhline(0.9, color='#2ecc71', lw=1, ls='--', alpha=0.5, label='목표 90%')
    ax.legend(fontsize=11, facecolor='#0a0e1a', labelcolor=C_TEXT, edgecolor='#1e2a3a')
    fig.tight_layout()
    return fig


def _render_vuln_time(result: dict) -> Figure:
    fig = Figure(figsize=(12, 5), facecolor=C_BG)
    ax = fig.add_subplot(111, facecolor='#0a0e1a')
    log = result.get('log', [])
    hit_times  = [t for t, msg in log if '[피격]' in msg]
    kill_times = [t for t, msg in log if '[요격]' in msg or '[격추]' in msg]
    max_t = max((result.get('sim_time', 300),
                 max(hit_times or [0]),
                 max(kill_times or [0]))) + 10
    bins = np.arange(0, max_t + 10, 10)
    if kill_times:
        ax.hist(kill_times, bins=bins, color='#2ecc71', alpha=0.7,
                label='요격/격추', edgecolor='#0a0e1a')
    if hit_times:
        ax.hist(hit_times, bins=bins, color='#e74c3c', alpha=0.7,
                label='피격', edgecolor='#0a0e1a')
    if hit_times:
        h, b = np.histogram(hit_times, bins=bins)
        peak_start = b[np.argmax(h)]
        ax.axvspan(peak_start, peak_start + 10, alpha=0.25, color='#e74c3c',
                   label=f'최다 피격 구간 ({peak_start:.0f}~{peak_start+10:.0f}s)')
    ax.set_xlabel('시뮬 시각 (초)', color=C_SUBTEXT, fontsize=12)
    ax.set_ylabel('이벤트 수', color=C_SUBTEXT, fontsize=12)
    ax.set_title('취약 시간대 분석 (10초 구간)', color=C_TEXT, fontsize=14)
    ax.tick_params(colors=C_SUBTEXT, labelsize=11)
    for sp in ax.spines.values():
        sp.set_color('#1e2a3a')
    ax.legend(fontsize=11, facecolor='#0a0e1a', labelcolor=C_TEXT, edgecolor='#1e2a3a')
    ax.grid(axis='y', color='#1e2a3a', lw=0.5)
    fig.tight_layout()
    return fig


def _render_history_compare(history: list) -> Figure:
    fig = Figure(figsize=(12, 5), facecolor='#0a0e1a')
    if not history:
        ax = fig.add_subplot(111, facecolor='#0a0e1a')
        ax.text(0.5, 0.5, '이전 실행 결과 없음\n(2회 이상 실행 후 비교 표시)',
                ha='center', va='center', color=C_SUBTEXT, fontsize=11,
                transform=ax.transAxes)
        return fig
    axes = fig.subplots(1, 3, facecolor='#0a0e1a')
    metrics = [
        ('요격률',         'mean_intercept', True,  '%'),
        ('완전 요격 비율', 'full_pass_rate',  True,  '%'),
        ('평균 비용',      'mean_cost',       False, '$'),
    ]
    cmap = ['#3498db', '#2ecc71', '#f39c12', '#e74c3c', '#9b59b6']
    for ax, (title, key, higher_better, unit) in zip(axes, metrics):
        ax.set_facecolor('#0a0e1a')
        vals = [h.get(key, 0) for h in history]
        cols = [cmap[i % len(cmap)] for i in range(len(history))]
        bars = ax.bar(range(len(history)), vals, color=cols, alpha=0.85,
                      edgecolor='#1e2a3a')
        for bar, v in zip(bars, vals):
            label = f"{v:.1%}" if unit == '%' else f"${v:,.0f}"
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + max(vals) * 0.02,
                    label, ha='center', va='bottom',
                    color=C_TEXT, fontsize=11)
        ax.set_title(title, color=C_TEXT, fontsize=13)
        ax.set_xticks(range(len(history)))
        ax.set_xticklabels([f'#{i+1}' for i in range(len(history))],
                           color=C_SUBTEXT, fontsize=11)
        ax.tick_params(colors=C_SUBTEXT, labelsize=11)
        for sp in ax.spines.values():
            sp.set_color('#1e2a3a')
        ax.yaxis.set_major_formatter(
            plt.FuncFormatter(lambda v, _: f"{v:.0%}" if unit == '%'
                              else f"${v/1e6:.1f}M"))
    fig.text(0.5, 0.01,
             '  |  '.join(f'#{i+1}: {h["label"]}' for i, h in enumerate(history)),
             ha='center', va='bottom', color=C_SUBTEXT, fontsize=10)
    fig.suptitle('이전 실행 결과 비교', color=C_TEXT, fontsize=14)
    fig.tight_layout(rect=[0, 0.06, 1, 1])
    return fig


def _render_stress_test(stress: dict) -> Figure:
    """스트레스 테스트 2D 히트맵 — 채널 감소 × 레이더 성능 감소 → 요격률."""
    fig = Figure(figsize=(13, 6), facecolor='#0a0e1a')
    if not stress or 'error' in stress:
        ax = fig.add_subplot(111, facecolor='#0a0e1a')
        msg = stress.get('error', '스트레스 테스트 결과 없음') if stress else '스트레스 테스트 결과 없음'
        ax.text(0.5, 0.5, msg, ha='center', va='center',
                color=C_SUBTEXT, fontsize=11, transform=ax.transAxes)
        return fig

    import numpy as _np
    grid      = _np.array(stress['grid'])
    cvar_grid = _np.array(stress.get('cvar_grid', grid))
    ch_vals   = stress['ch_vals']
    rad_vals  = stress['rad_vals']

    axes = fig.subplots(1, 2)
    titles = ['평균 요격률', 'CVaR (하위 5%)']
    for ax, data, title in zip(axes, [grid, cvar_grid], titles):
        ax.set_facecolor('#0a0e1a')
        im = ax.imshow(data, cmap='RdYlGn', aspect='auto',
                       vmin=0.0, vmax=1.0, origin='lower')
        ax.set_xticks(range(len(rad_vals)))
        ax.set_xticklabels([f'{v}%' for v in rad_vals], color=C_SUBTEXT, fontsize=11)
        ax.set_yticks(range(len(ch_vals)))
        ax.set_yticklabels([f'{v}%' for v in ch_vals], color=C_SUBTEXT, fontsize=11)
        ax.set_xlabel(stress.get('rad_label', '레이더 성능 감소'), color=C_SUBTEXT, fontsize=11)
        ax.set_ylabel(stress.get('ch_label', '유도 채널 감소'), color=C_SUBTEXT, fontsize=11)
        ax.set_title(title, color=C_TEXT, fontsize=13)
        for sp in ax.spines.values():
            sp.set_color('#1e2a3a')
        ax.tick_params(colors=C_SUBTEXT)
        for i in range(data.shape[0]):
            for j in range(data.shape[1]):
                val = data[i, j]
                txt_col = 'black' if val > 0.5 else C_TEXT
                ax.text(j, i, f'{val:.0%}', ha='center', va='center',
                        color=txt_col, fontsize=12, fontweight='bold')
        fig.colorbar(im, ax=ax, format='%.0%%')

    n_cell = stress.get('n_per_cell', '?')
    fig.suptitle(f'스트레스 테스트 — 셀당 {n_cell}회 시뮬레이션',
                 color=C_TEXT, fontsize=14, y=0.98)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    return fig


def _render_sobol_chart(sobol: dict) -> Figure:
    """Sobol 1차·전체 민감도 지수 수평 막대 차트."""
    fig = Figure(figsize=(12, 6), facecolor='#0a0e1a')
    ax  = fig.add_subplot(111, facecolor='#0a0e1a')

    if not sobol or 'error' in sobol:
        msg = sobol.get('error', 'Sobol 분석 결과 없음\n(정밀 모드에서만 실행됩니다)') \
              if sobol else 'Sobol 분석 결과 없음\n(정밀 모드에서만 실행됩니다)'
        ax.text(0.5, 0.5, msg, ha='center', va='center',
                color=C_SUBTEXT, fontsize=12, transform=ax.transAxes)
        ax.set_facecolor('#0a0e1a')
        return fig

    import numpy as _np
    names   = sobol.get('names', [])
    S1      = _np.array(sobol.get('S1', []))
    ST      = _np.array(sobol.get('ST', []))
    S1_conf = _np.array(sobol.get('S1_conf', _np.zeros_like(S1)))
    ST_conf = _np.array(sobol.get('ST_conf', _np.zeros_like(ST)))

    y = _np.arange(len(names))
    h = 0.35
    bars1 = ax.barh(y + h/2, S1, h, xerr=S1_conf, label='S1 (1차)',
                    color='#3498db', alpha=0.85, capsize=4,
                    error_kw={'ecolor': '#7fb3e3', 'linewidth': 1.5})
    barsT = ax.barh(y - h/2, ST, h, xerr=ST_conf, label='ST (전체)',
                    color='#e74c3c', alpha=0.85, capsize=4,
                    error_kw={'ecolor': '#f1948a', 'linewidth': 1.5})

    ax.set_yticks(y)
    ax.set_yticklabels(names, color=C_TEXT, fontsize=12)
    ax.set_xlabel('민감도 지수', color=C_SUBTEXT, fontsize=12)
    ax.set_xlim(0, max(1.0, float(ST.max()) * 1.2) if len(ST) else 1.0)
    ax.tick_params(colors=C_SUBTEXT, labelsize=11)
    for sp in ax.spines.values():
        sp.set_color('#1e2a3a')
    ax.legend(fontsize=11, facecolor='#1c2128', labelcolor=C_TEXT,
              edgecolor='#444c56')
    ax.grid(axis='x', color='#1e2a3a', linewidth=0.7, alpha=0.6)

    n_runs = sobol.get('n_runs', '?')
    npp_str = f'  •  포인트당 {sobol.get("n_per_point",1)}회 평균' if sobol.get('n_per_point',1) > 1 else ''
    ax.set_title(f'Sobol 파라미터 민감도 분석  (총 {n_runs:,}회{npp_str})',
                 color=C_TEXT, fontsize=14)
    fig.tight_layout()
    return fig


# ════════════════════════════════════════════════════════════════════════════
#  메인 윈도우
# ════════════════════════════════════════════════════════════════════════════
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("이지스 기동전단 통합 방어 시뮬레이터  v7.21")
        self.resize(1800, 1060)
        self._worker         = None
        self._weather_worker = None
        self._result = None
        self._mc     = None
        self._t0     = 0.0
        self._history: list = []  # 이전 실행 결과 히스토리 (최대 5개)
        self._float_mon = FloatingMonitor()

        # ── BUG-1: 탭 전환 디바운스 (200ms) ────────────────────────────────
        self._page_pending_idx: int = -1
        self._page_debounce_timer = QTimer(self)
        self._page_debounce_timer.setSingleShot(True)
        self._page_debounce_timer.setInterval(200)
        self._page_debounce_timer.timeout.connect(self._render_current_page)
        # BUG-1: 차트 캐시 — 동일 result 객체면 재렌더 스킵
        self._page_render_cache: dict = {}   # {page_idx: id(result)}

        self._build_ui()
        self._apply_style()

    # ── UI 구성 ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(2)
        root.addWidget(splitter)

        splitter.addWidget(self._build_config_panel())
        splitter.addWidget(self._build_result_panel())
        splitter.setSizes([430, 1070])

        # 상태바
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self._lbl_status = QLabel("준비")
        self._prog       = QProgressBar()
        self._prog.setFixedWidth(180)
        self._prog.setRange(0, 0)
        self._prog.setVisible(False)
        self.status.addWidget(self._lbl_status)
        self.status.addPermanentWidget(self._prog)

        btn_log = QPushButton("📋 실행 로그")
        btn_log.setFixedHeight(22)
        btn_log.setStyleSheet(
            f"QPushButton {{ background:{C_PANEL}; color:{C_SUBTEXT}; border:1px solid {C_BORDER};"
            f" border-radius:3px; padding:0 8px; font-size:12px; }}"
            f"QPushButton:hover {{ color:{C_TEXT}; }}"
        )
        btn_log.clicked.connect(self._open_log_file)
        self.status.addPermanentWidget(btn_log)

        # 단축키
        QShortcut(QKeySequence(Qt.Key.Key_Space), self,
                  activated=self._shortcut_play_pause)
        QShortcut(QKeySequence(Qt.Key.Key_Left), self,
                  activated=self._shortcut_prev_frame)
        QShortcut(QKeySequence(Qt.Key.Key_Right), self,
                  activated=self._shortcut_next_frame)

    def _open_log_file(self):
        try:
            alive = (hasattr(self, '_log_dialog')
                     and self._log_dialog is not None
                     and self._log_dialog.isVisible())
        except RuntimeError:
            alive = False
        if not alive:
            self._log_dialog = SimLogDialog(self)
        else:
            self._log_dialog._load()
        self._log_dialog.show()
        self._log_dialog.raise_()
        self._log_dialog.activateWindow()

    def _shortcut_play_pause(self):
        if hasattr(self, 'tab_anim'):
            self.tab_anim._toggle_play()

    def _shortcut_prev_frame(self):
        if hasattr(self, 'tab_anim'):
            v = self.tab_anim.slider.value()
            self.tab_anim.slider.setValue(max(0, v - 1))

    def _shortcut_next_frame(self):
        if hasattr(self, 'tab_anim'):
            v = self.tab_anim.slider.value()
            self.tab_anim.slider.setValue(
                min(self.tab_anim.slider.maximum(), v + 1))

    def _build_config_panel(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedWidth(430)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"QScrollArea {{ border: none; background: {C_PANEL}; }}")

        inner = QWidget()
        inner.setStyleSheet(f"background: {C_PANEL};")
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(5)

        # 타이틀
        title = QLabel("⚓ 이지스 기동전단\n통합 방어 시뮬레이터")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont('Malgun Gothic', 17, QFont.Weight.Bold))
        title.setStyleSheet(f"color:{C_ACCENT}; padding: 8px 0;")
        layout.addWidget(title)

        # ── 아군 편대 ──────────────────────────────────────────────────────
        grp_f = QGroupBox("🔵 아군 편대")
        fl = QFormLayout(grp_f)
        fl.setSpacing(4)

        self.cmb_fleet   = NoScrollComboBox()
        self.cmb_fleet.addItems(list(V7_FLEET_PRESETS.keys()) if _V7_OK else [])
        if _V7_OK:
            for _i, _n in enumerate(V7_FLEET_PRESETS.keys()):
                self.cmb_fleet.setItemData(_i, self._friendly_preset_tooltip(_n),
                                           Qt.ItemDataRole.ToolTipRole)
        self.cmb_weather = NoScrollComboBox()
        self.cmb_weather.addItems(list(WEATHER_DB.keys()) if _V7_OK else [])
        self.lbl_fleet_detail = QLabel()
        self.lbl_fleet_detail.setStyleSheet(
            f"color:{C_SUBTEXT}; font-size:15px; padding:2px 0;")
        self.lbl_fleet_detail.setWordWrap(True)
        self.cmb_fleet.currentTextChanged.connect(self._update_fleet_detail)

        self.lbl_detect_info = QLabel()
        self.lbl_detect_info.setStyleSheet(
            f"color:{C_ACCENT}; font-size:15px; padding:2px 0;")
        self.lbl_detect_info.setWordWrap(True)
        self.cmb_fleet.currentTextChanged.connect(self._update_detect_info)
        self.cmb_weather.currentTextChanged.connect(self._update_detect_info)

        fl.addRow("편대 프리셋", self.cmb_fleet)
        fl.addRow("",            self.lbl_fleet_detail)
        fl.addRow("날씨",        self.cmb_weather)
        fl.addRow("탐지 정보",   self.lbl_detect_info)

        # 랜덤 배치 — 항상 활성화 (반경 10km 고정)
        rp_row = QHBoxLayout()
        lbl_rp = QLabel("함정 위치 랜덤 배치  (반경 10 km 고정)")
        lbl_rp.setStyleSheet(f"color:{C_SUBTEXT}; font-size:15px;")
        rp_row.addWidget(lbl_rp)
        fl.addRow("", rp_row)
        layout.addWidget(grp_f)


        # ── 적군 편대 (포팅 A) ────────────────────────────────────────────
        grp_e = QGroupBox("🔴 적군 편대")
        el = QVBoxLayout(grp_e)
        el.setSpacing(4)

        # 모드 선택
        mode_row = QWidget(); mode_rl = QHBoxLayout(mode_row)
        mode_rl.setContentsMargins(0, 0, 0, 0)
        mode_rl.addWidget(QLabel("모드:"))
        self.cmb_enemy_mode = NoScrollComboBox()
        self.cmb_enemy_mode.addItems(['프리셋', '혼합 시나리오', '랜덤'])
        mode_rl.addWidget(self.cmb_enemy_mode, stretch=1)
        el.addWidget(mode_row)

        # 프리셋 선택 (프리셋 모드용)
        self.cmb_fleet_preset_e = NoScrollComboBox()
        self.cmb_fleet_preset_e.addItems(list(V7_ENEMY_FLEET_PRESETS.keys()) if _V7_OK else [])
        if _V7_OK:
            for _i, _n in enumerate(V7_ENEMY_FLEET_PRESETS.keys()):
                self.cmb_fleet_preset_e.setItemData(_i, self._enemy_preset_tooltip(_n),
                                                    Qt.ItemDataRole.ToolTipRole)
        self.cmb_fleet_preset_e.currentTextChanged.connect(self._update_enemy_preset_detail)
        el.addWidget(self.cmb_fleet_preset_e)

        # NEW-A: 혼합 시나리오 선택 (혼합 모드용)
        self._mixed_row = QWidget(); mixed_rl = QVBoxLayout(self._mixed_row)
        mixed_rl.setContentsMargins(0, 0, 0, 0); mixed_rl.setSpacing(3)
        self.cmb_mixed_scenario = NoScrollComboBox()
        self.cmb_mixed_scenario.addItems(list(V7_MIXED_SCENARIOS.keys()) if _V7_OK else [])
        self.cmb_mixed_scenario.currentTextChanged.connect(self._update_mixed_scenario_detail)
        mixed_rl.addWidget(self.cmb_mixed_scenario)
        self.lbl_mixed_detail = QLabel()
        self.lbl_mixed_detail.setStyleSheet(
            f"color:{C_SUBTEXT}; font-size:14px; padding:2px 0;")
        self.lbl_mixed_detail.setWordWrap(True)
        mixed_rl.addWidget(self.lbl_mixed_detail)
        el.addWidget(self._mixed_row)

        self.lbl_enemy_preset_detail = QLabel()
        self.lbl_enemy_preset_detail.setStyleSheet(
            f"color:{C_SUBTEXT}; font-size:15px; padding:2px 0;")
        self.lbl_enemy_preset_detail.setWordWrap(True)
        el.addWidget(self.lbl_enemy_preset_detail)

        # 랜덤 난이도 + 시드 (랜덤 모드용)
        self._rand_row = QWidget(); rand_rl = QHBoxLayout(self._rand_row)
        rand_rl.setContentsMargins(0, 0, 0, 0); rand_rl.setSpacing(4)
        self.cmb_difficulty = NoScrollComboBox()
        self.cmb_difficulty.addItems(list(V7_RANDOM_CFG.keys()) if _V7_OK else ['보통'])
        self.cmb_difficulty.setCurrentText('보통')
        self.cmb_difficulty.currentTextChanged.connect(self._update_difficulty_tooltip)
        self.spn_seed = NoScrollSpinBox(); self.spn_seed.setRange(0, 99999); self.spn_seed.setValue(0)
        self.spn_seed.setPrefix("씨앗: ")
        rand_rl.addWidget(self.cmb_difficulty, stretch=1)
        rand_rl.addWidget(self.spn_seed, stretch=1)
        el.addWidget(self._rand_row)

        self.cmb_enemy_mode.currentIndexChanged.connect(self._on_enemy_mode_changed)
        self._on_enemy_mode_changed(0)  # 초기 상태 적용 (기본: 프리셋)
        if _V7_OK:
            if self.cmb_fleet_preset_e.count():
                self._update_enemy_preset_detail(self.cmb_fleet_preset_e.currentText())
            if self.cmb_difficulty.count():
                self._update_difficulty_tooltip(self.cmb_difficulty.currentText())
            if self.cmb_mixed_scenario.count():
                self._update_mixed_scenario_detail(self.cmb_mixed_scenario.currentText())
        layout.addWidget(grp_e)

        # ── 전술 옵션 (포팅 B) ────────────────────────────────────────────
        grp_t = QGroupBox("⚙️ 전술 옵션")
        tl = QVBoxLayout(grp_t)
        tl.setSpacing(4)

        self.chk_ecm   = QCheckBox("ECM 재밍 (거리 반비례 Pk 감소)");  self.chk_ecm.setChecked(True)
        self.chk_eva   = QCheckBox("회피 기동 (종말·함정 어뢰)");       self.chk_eva.setChecked(True)
        self.chk_dcoy  = QCheckBox("음향 기만기 AN/SLQ-25 (어뢰)");    self.chk_dcoy.setChecked(True)
        self.chk_sd    = QCheckBox("적 자체방어 (CIWS + 채프/플레어)"); self.chk_sd.setChecked(True)

        for chk in [self.chk_ecm, self.chk_eva, self.chk_dcoy, self.chk_sd]:
            chk.setStyleSheet(f"color:{C_TEXT}; font-size:16px;")
            tl.addWidget(chk)

        grp_t.hide()
        layout.addWidget(grp_t)

        # ── 항공 자산 (포팅 C) ────────────────────────────────────────────
        grp_ac = QGroupBox("🚁 항공 자산 (대잠 전용)")
        acl = QVBoxLayout(grp_ac)
        acl.setSpacing(4)

        self.chk_helo = QCheckBox("AW-159 와일드캣  (함재 헬기, 청상어 2발, 140km)")
        self.chk_p3c  = QCheckBox("P-3C 오라이온  (포항기지, Mk.46 4발, 소노부이+15km)")
        self.chk_p8a  = QCheckBox("P-8A 포세이돈  (포항기지, Mk.46 5발, 소노부이+18km)")

        for chk in [self.chk_helo, self.chk_p3c, self.chk_p8a]:
            chk.setChecked(False)
            chk.setStyleSheet(f"color:{C_TEXT}; font-size:16px;")
            acl.addWidget(chk)

        grp_ac.hide()
        layout.addWidget(grp_ac)

        # ── 방어 전술 옵션 ─────────────────────────────────────────────────
        grp_def = QGroupBox("🛡️ 방어 전술")
        defl = QVBoxLayout(grp_def)
        defl.setSpacing(4)

        self.chk_layered = QCheckBox("다층 방어  (KDX-III-B2 → B1 → KDX-II → FFX 순서)")
        self.chk_layered.setChecked(True)
        self.chk_layered.setToolTip(
            "1차 교전 함정(KDX-III Batch II)이 요격 실패 시 다음 레이어(Batch I → KDX-II → FFX)가 자동 인계.\n"
            "우선순위 정렬로 최고 성능 함정이 항상 먼저 교전합니다."
        )

        self.chk_cec = QCheckBox("CEC 사전 동시 배정  (1차+2차 함정 동시 발사)")
        self.chk_cec.setChecked(False)
        self.chk_cec.setToolTip(
            "위협 탐지 시 1차(KDX-III-B2)+2차(KDX-III-B1/KDX-II) 함정이 동시에 SAM을 발사합니다.\n"
            "1차 성공 시 2차 SAM은 표적 소멸로 자동 종료.\n"
            "탄약 소비 증가 / 동시 다수 위협에 효과적."
        )

        self.chk_multibearing = QCheckBox("다방위 공격  (여러 방향에서 동시 접근)")
        self.chk_multibearing.setChecked(False)
        self.chk_multibearing.setToolTip(
            "적 위협이 전방위(0°~360°) 무작위 방향에서 접근합니다.\n"
            "OFF 시 기본 단일 방향 접근."
        )

        self.chk_cec_jammed = QCheckBox("CEC 두절  (재밍 → 함정 독립 교전)")
        self.chk_cec_jammed.setChecked(False)
        self.chk_cec_jammed.setToolTip(
            "적 전자전으로 CEC 네트워크가 차단됩니다.\n"
            "각 함정이 독립적으로 교전 — 다층 방어 무력화.\n"
            "CEC 사전 배정이 ON이어도 강제 비활성화됩니다."
        )

        self.chk_ship_evasion = QCheckBox("함정 회피 기동  (적 미사일 15km 이내 지그재그)")
        self.chk_ship_evasion.setChecked(False)
        self.chk_ship_evasion.setToolTip(
            "적 대함미사일이 15km 이내 접근 시\n"
            "아군 함정이 지그재그 회피 기동으로 피탄율을 낮춥니다."
        )

        # 적 편대 전술 기동
        tactics_row = QHBoxLayout()
        lbl_tactics = QLabel("적 전술 기동:")
        lbl_tactics.setStyleSheet(f"color:{C_SUBTEXT}; font-size:15px;")
        self.cmb_enemy_tactics = NoScrollComboBox()
        self.cmb_enemy_tactics.addItems(['없음', 'V자 대형', '포위 기동'])
        self.cmb_enemy_tactics.setToolTip(
            "없음: 기본 분산 접근\n"
            "V자 대형: 선두 1기 + 양익 전개\n"
            "포위 기동: 전방위 동시 포위 (다방위 강화)"
        )
        tactics_row.addWidget(lbl_tactics)
        tactics_row.addWidget(self.cmb_enemy_tactics, stretch=1)

        for chk in [self.chk_layered, self.chk_cec, self.chk_multibearing,
                    self.chk_cec_jammed, self.chk_ship_evasion]:
            chk.setStyleSheet(f"color:{C_TEXT}; font-size:16px;")
            defl.addWidget(chk)
        defl.addLayout(tactics_row)

        # 시뮬 시드
        seed_row = QHBoxLayout()
        lbl_seed = QLabel("시뮬 시드  (0=랜덤, 재현 시 동일 값 입력)")
        lbl_seed.setStyleSheet(f"color:{C_SUBTEXT}; font-size:15px;")
        self.spn_sim_seed = NoScrollSpinBox()
        self.spn_sim_seed.setRange(0, 99999)
        self.spn_sim_seed.setValue(0)
        self.spn_sim_seed.setFixedWidth(80)
        seed_row.addWidget(lbl_seed)
        seed_row.addStretch()
        seed_row.addWidget(self.spn_sim_seed)
        defl.addLayout(seed_row)

        grp_def.hide()
        layout.addWidget(grp_def)

        # ── C&D 시간 설정 (고정값) ────────────────────────────────────────
        grp_cd = QGroupBox("⏱️ C&&D 시간 설정")
        cdl = QHBoxLayout(grp_cd)
        cdl.setSpacing(16)
        lbl_cd_fixed = QLabel("C&&D  10초  /  확인  3초  (고정)")
        lbl_cd_fixed.setStyleSheet(f"color:{C_SUBTEXT}; font-size:15px;")
        cdl.addWidget(lbl_cd_fixed)
        layout.addWidget(grp_cd)

        # ── 시뮬레이션 모드 선택 ─────────────────────────────────────────────
        grp_mc = QGroupBox("📊 시뮬레이션 모드")
        mcl = QHBoxLayout(grp_mc)
        mcl.setSpacing(12)
        lbl_mode = QLabel("정밀도:")
        lbl_mode.setStyleSheet(f"color:{C_SUBTEXT}; font-size:15px;")
        self.cmb_sim_mode = QComboBox()
        self.cmb_sim_mode.addItems(["⚡ 빠름  (5,000회)", "📊 표준  (10,000회)", "🔬 정밀  (100,000회)"])
        self.cmb_sim_mode.setCurrentIndex(1)
        self.cmb_sim_mode.setFixedHeight(32)
        self.cmb_sim_mode.setStyleSheet(f"""
            QComboBox {{
                background: #1c2128; color: #e6edf3;
                border: 1px solid #444c56; border-radius: 4px;
                font-size: 14px; padding: 2px 8px;
            }}
            QComboBox QAbstractItemView {{
                background: #161b22; color: #e6edf3;
                selection-background-color: #3498db;
            }}
        """)
        lbl_mode_hint = QLabel()
        lbl_mode_hint.setStyleSheet(f"color:{C_SUBTEXT}; font-size:12px;")

        # Sobol 포인트당 반복 수 (정밀 모드 전용)
        lbl_npp = QLabel("Sobol 포인트당 반복:")
        lbl_npp.setStyleSheet(f"color:{C_SUBTEXT}; font-size:13px;")
        self.spn_sobol_npp = QSpinBox()
        self.spn_sobol_npp.setRange(1, 10)
        self.spn_sobol_npp.setValue(3)
        self.spn_sobol_npp.setFixedWidth(52)
        self.spn_sobol_npp.setFixedHeight(28)
        self.spn_sobol_npp.setToolTip(
            "Sobol 분석 시 각 파라미터 조합을 몇 번 반복해 평균낼지.\n"
            "1회: 빠름 (~32,768회) / 3회: 권장 (~98,304회) / 5회: 고정밀 (~163,840회)\n"
            "확률적 시뮬레이션의 노이즈를 √K배 줄여 민감도 지수 신뢰도 향상.\n"
            "정밀 모드 선택 시에만 사용됩니다.")
        self.spn_sobol_npp.setStyleSheet(
            f"background:#1c2128; color:#e6edf3; border:1px solid #444c56; font-size:13px;")
        self.spn_sobol_npp.setEnabled(False)  # 정밀 모드일 때만 활성화

        lbl_mode_hint = QLabel()
        lbl_mode_hint.setStyleSheet(f"color:{C_SUBTEXT}; font-size:12px;")
        self._lbl_sobol_total = QLabel()
        self._lbl_sobol_total.setStyleSheet(f"color:{C_SUBTEXT}; font-size:12px;")

        def _update_sobol_total():
            npp = self.spn_sobol_npp.value()
            total = 32_768 * npp
            self._lbl_sobol_total.setText(f"(총 ~{total:,}회)")

        def _update_mode_hint(idx):
            hints = [
                "LHS 샘플링  •  CVaR 분석  •  스트레스 테스트 (셀당 300회)",
                "LHS 샘플링  •  CVaR 분석  •  스트레스 테스트 (셀당 500회)",
                "LHS 샘플링  •  CVaR  •  스트레스 (셀당 3,000회)  •  Sobol 민감도",
            ]
            lbl_mode_hint.setText(hints[idx])
            is_precision = (idx == 2)
            self.spn_sobol_npp.setEnabled(is_precision)
            lbl_npp.setStyleSheet(
                f"color:{C_TEXT if is_precision else C_SUBTEXT}; font-size:13px;")
            self._lbl_sobol_total.setVisible(is_precision)

        self.cmb_sim_mode.currentIndexChanged.connect(_update_mode_hint)
        self.spn_sobol_npp.valueChanged.connect(_update_sobol_total)
        _update_mode_hint(1)
        _update_sobol_total()

        mcl.addWidget(lbl_mode)
        mcl.addWidget(self.cmb_sim_mode)
        mcl.addSpacing(16)
        mcl.addWidget(lbl_npp)
        mcl.addWidget(self.spn_sobol_npp)
        mcl.addSpacing(4)
        mcl.addWidget(self._lbl_sobol_total)
        mcl.addSpacing(8)
        mcl.addWidget(lbl_mode_hint)
        mcl.addStretch()
        layout.addWidget(grp_mc)


        # ── 실행 버튼 ─────────────────────────────────────────────────────
        self.btn_run = QPushButton("🚀  시뮬레이션 실행")
        self.btn_run.setFixedHeight(44)
        self.btn_run.setFont(QFont('Malgun Gothic', 15))
        self.btn_run.clicked.connect(self._run_sim)
        layout.addWidget(self.btn_run)

        if not _V7_OK:
            err_lbl = QLabel(f"⚠️ engine_v7 로드 실패\n{_V7_ERR}")
            err_lbl.setStyleSheet(f"color:{C_RED}; font-size:15px;")
            err_lbl.setWordWrap(True)
            layout.addWidget(err_lbl)
            self.btn_run.setEnabled(False)

        # 초기 함대 편성 + 탐지 정보 레이블
        if _V7_OK and self.cmb_fleet.count():
            self._update_fleet_detail(self.cmb_fleet.currentText())
            self._update_detect_info()

        layout.addStretch()
        scroll.setWidget(inner)
        return scroll

    def _build_result_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        # 핵심 지표 카드 영역
        self.card_row = QWidget()
        card_layout = QHBoxLayout(self.card_row)
        card_layout.setContentsMargins(12, 8, 12, 0)
        card_layout.setSpacing(8)

        self._cards = {}
        card_defs = [
            ('요격률 (MC)',      'intercept'),
            ('완전 요격 비율',   'full_pass'),
            ('CVaR (최악 5%)',   'cvar'),
            ('아군 피격',        'friendly_hit'),
            ('적 격침',          'enemy_dest'),
            ('총 비용',          'cost'),
            ('항공 출격',        'aircraft'),
        ]
        for label, key in card_defs:
            card = QGroupBox(label)
            card.setFixedHeight(72)
            cl = QVBoxLayout(card)
            lbl = QLabel("—")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFont(QFont('Malgun Gothic', 17, QFont.Weight.Bold))
            lbl.setStyleSheet(f"color:{C_ACCENT};")
            cl.addWidget(lbl)
            card_layout.addWidget(card)
            self._cards[key] = lbl

        layout.addWidget(self.card_row)

        # 내보내기 버튼 행
        export_row = QWidget()
        export_rl  = QHBoxLayout(export_row)
        export_rl.setContentsMargins(12, 4, 12, 0)
        export_rl.setSpacing(6)
        export_rl.addStretch()
        self.btn_excel = QPushButton("📊 Excel 보고서")
        self.btn_pdf   = QPushButton("📄 PDF 보고서")
        for b in [self.btn_excel, self.btn_pdf]:
            b.setFixedHeight(28)
            b.setStyleSheet(
                f"background:{C_PANEL}; color:{C_TEXT}; "
                f"border:1px solid #3a5a7a; font-size:15px; padding:0 8px;")
        self.btn_excel.clicked.connect(self._export_excel)
        self.btn_pdf.clicked.connect(self._export_pdf)
        export_rl.addWidget(self.btn_excel)
        export_rl.addWidget(self.btn_pdf)

        # 시드 표시 레이블 (재현용)
        self._lbl_seed_used = QLabel("")
        self._lbl_seed_used.setStyleSheet(f"color:{C_SUBTEXT}; font-size:12px;")
        export_rl.addSpacing(12)
        export_rl.addWidget(self._lbl_seed_used)
        layout.addWidget(export_row)

        # ── 사이드바 + QStackedWidget ─────────────────────────────────────
        self.tab_anim        = AnimationTab()
        self.tab_mc_canvas   = ChartPageWidget()
        self.tab_req         = self._build_req_tab()
        self.tab_weather     = self._build_weather_tab()
        self.tab_log         = self._build_log_tab()
        self.tab_channel     = ChartPageWidget()
        self.tab_sysmon      = SysMonitorTab()
        self.tab_cost_eff    = ChartPageWidget()
        self.tab_ammo_curve  = ChartPageWidget()
        self.tab_ci          = ChartPageWidget()
        self.tab_timeline    = ChartPageWidget()
        self.tab_sensitivity = ChartPageWidget()   # 백그라운드 렌더 (MplCanvas→ChartPageWidget)
        self.tab_min_stock   = ChartPageWidget()   # 백그라운드 렌더
        self.tab_bearing     = ChartPageWidget()
        self.tab_req_radar   = ChartPageWidget()
        self.tab_threat_type = ChartPageWidget()
        self.tab_vuln_time   = ChartPageWidget()
        self.tab_history     = ChartPageWidget()
        self.tab_stress      = ChartPageWidget()   # 스트레스 테스트 히트맵
        self.tab_sobol       = ChartPageWidget()   # Sobol 민감도 분석

        # 사이드바 (QListWidget)
        self._sidebar = QListWidget()
        self._sidebar.setFixedWidth(190)
        self._sidebar.setStyleSheet("""
            QListWidget {
                background: #161b22;
                border: none;
                border-right: 1px solid #30363d;
                font-size: 15px;
                font-family: 'Malgun Gothic', 'Segoe UI';
            }
            QListWidget::item {
                color: #7d8590;
                padding: 10px 12px;
                border-bottom: 1px solid #21262d;
            }
            QListWidget::item:selected {
                background: #0d1117;
                color: #3498db;
                border-left: 3px solid #3498db;
                font-weight: bold;
            }
            QListWidget::item:hover:!selected {
                background: #1c2128;
                color: #e6edf3;
            }
        """)
        for label in [
            "🗺  전장 애니메이션", "📊  MC 통계", "✅  REQ 판정",
            "🌤  날씨 비교", "📜  교전 로그", "📡  채널 포화도",
            "🖥  시스템 모니터", "💰  비용 효과", "🔫  탄약 소모",
            "📈  MC 신뢰구간", "⏱  교전 타임라인", "🌪  감도 분석",
            "🔬  최소 재고",
            "🧭  방위각 취약점", "🎯  REQ 충족률", "📊  위협 유형별",
            "⏰  취약 시간대", "🔄  이전 비교",
            "🔥  스트레스 테스트", "🎛  Sobol 민감도",
        ]:
            self._sidebar.addItem(label)
        self._sidebar.setCurrentRow(0)

        # QStackedWidget (사이드바와 동일 순서)
        self._stack = QStackedWidget()
        for w in [
            self.tab_anim,        # 0
            self.tab_mc_canvas,   # 1
            self.tab_req,         # 2
            self.tab_weather,     # 3
            self.tab_log,         # 4
            self.tab_channel,     # 5
            self.tab_sysmon,      # 6
            self.tab_cost_eff,    # 7
            self.tab_ammo_curve,  # 8
            self.tab_ci,          # 9
            self.tab_timeline,    # 10
            self.tab_sensitivity, # 11
            self.tab_min_stock,   # 12
            self.tab_bearing,     # 13
            self.tab_req_radar,   # 14
            self.tab_threat_type, # 15
            self.tab_vuln_time,   # 16
            self.tab_history,     # 17
            self.tab_stress,      # 18
            self.tab_sobol,       # 19
        ]:
            self._stack.addWidget(w)

        # 연결
        self._sidebar.currentRowChanged.connect(self._stack.setCurrentIndex)
        self._sidebar.currentRowChanged.connect(self._on_page_changed)

        # body (사이드바 + 스택)
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)
        body_layout.addWidget(self._sidebar)
        body_layout.addWidget(self._stack, stretch=1)
        layout.addWidget(body, stretch=1)

        # 지연 렌더링 dirty 집합 초기화
        self._page_dirty: set = set()

        return panel

    def _on_page_changed(self, idx: int):
        """사이드바 선택 시 200ms 디바운스 후 지연 렌더링 (BUG-1)."""
        self._page_pending_idx = idx
        self._page_debounce_timer.start()

    def _render_current_page(self):
        """디바운스 만료 후 실제 페이지 렌더링 — 동일 데이터 재렌더 스킵 (BUG-1)."""
        idx = self._page_pending_idx
        if self._result is None or idx < 0:
            return
        if idx not in self._page_dirty:
            return
        # 동일 result 객체면 재렌더 스킵
        result_id = id(self._result)
        if self._page_render_cache.get(idx) == result_id:
            self._page_dirty.discard(idx)
            return

        cfg = self._worker.cfg if self._worker else {}
        render_map = {
            1:  lambda: self._draw_mc_chart(self._result, self._mc, cfg),
            5:  lambda: self._draw_channel_heatmap(self._result),
            7:  lambda: self._draw_cost_effect(self._result, self._mc),
            8:  lambda: self._draw_ammo_curve(self._mc),
            9:  lambda: self._draw_ci_chart(self._mc),
            10: lambda: self._draw_timeline(self._result),
            11: lambda: self._lazy_start_sensitivity(),
            12: lambda: self._lazy_start_min_stock(),
            13: lambda: self._draw_bearing_vulnerability(self._result),
            14: lambda: self._draw_req_radar(self._result, self._mc),
            15: lambda: self._draw_threat_type(self._result, self._mc),
            16: lambda: self._draw_vuln_time(self._result),
            17: lambda: self._draw_history_compare(self._result, self._mc),
            18: lambda: self._draw_stress_test(self._mc),
            19: lambda: self._draw_sobol_chart(self._mc),
        }
        if idx in render_map:
            render_map[idx]()
            self._page_dirty.discard(idx)
            self._page_render_cache[idx] = result_id

    def _build_req_tab(self) -> QWidget:
        """포팅 D: REQ 판정 결과 테이블 + 자동 취약점 진단 카드."""
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # ── REQ 판정 테이블 (상단) ────────────────────────────────────────
        req_lbl = QLabel("  ✅  REQ 요구조건 판정")
        req_lbl.setStyleSheet(f"color:{C_TEXT}; font-size:13px; font-weight:bold; padding:4px 0;")
        layout.addWidget(req_lbl)

        self.req_table = QTableWidget(0, 4)
        self.req_table.setHorizontalHeaderLabels(["ID", "요구조건", "판정", "상세"])
        hh = self.req_table.horizontalHeader()
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.req_table.setColumnWidth(0, 70)
        self.req_table.setColumnWidth(1, 150)
        self.req_table.setColumnWidth(2, 60)
        self.req_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.req_table.setAlternatingRowColors(True)
        self.req_table.setStyleSheet(
            f"alternate-background-color: {C_PANEL}; background-color: {C_BG};")
        layout.addWidget(self.req_table, stretch=2)

        # ── 자동 취약점 진단 카드 영역 (하단 — 넓게) ─────────────────────
        diag_header = QLabel("  🩺  자동 취약점 진단")
        diag_header.setStyleSheet(f"color:{C_TEXT}; font-size:13px; font-weight:bold; padding:4px 0;")
        layout.addWidget(diag_header)

        self._diag_scroll = QScrollArea()
        self._diag_scroll.setWidgetResizable(True)
        self._diag_scroll.setMinimumHeight(260)
        self._diag_scroll.setStyleSheet(
            f"QScrollArea {{ background: {C_BG}; border: 1px solid #30363d; border-radius: 6px; }}"
        )
        self._diag_inner = QWidget()
        self._diag_inner.setStyleSheet(f"background: {C_BG};")
        self._diag_layout = QVBoxLayout(self._diag_inner)
        self._diag_layout.setContentsMargins(8, 8, 8, 8)
        self._diag_layout.setSpacing(7)
        _ph = QLabel("  시뮬레이션 실행 후 진단 결과가 표시됩니다.")
        _ph.setStyleSheet(f"color:{C_SUBTEXT}; font-size:12px;")
        self._diag_layout.addWidget(_ph)
        self._diag_layout.addStretch()
        self._diag_scroll.setWidget(self._diag_inner)
        layout.addWidget(self._diag_scroll, stretch=3)
        return w

    def _build_weather_tab(self) -> QWidget:
        """포팅 D: 날씨별 3종 비교 탭."""
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)

        btn_row = QWidget()
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        self.btn_weather_run = QPushButton("🌤️  날씨별 비교 실행 (각 1000회 MC)")
        self.btn_weather_run.setFixedHeight(36)
        self.btn_weather_run.clicked.connect(self._run_weather_compare)
        btn_layout.addWidget(self.btn_weather_run)
        btn_layout.addStretch()
        layout.addWidget(btn_row)

        self.weather_table = QTableWidget(0, 6)
        self.weather_table.setHorizontalHeaderLabels(
            ["날씨 시나리오", "평균 요격률", "완전 성공률", "평균 비용 ($)",
             "최다 소모 무기", "가장 많이 피격된 함정"])
        hh = self.weather_table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        for col in [1, 2, 3]:
            self.weather_table.setColumnWidth(col, 110)
        self.weather_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.weather_table.setAlternatingRowColors(True)
        self.weather_table.setStyleSheet(
            f"alternate-background-color: {C_PANEL}; background-color: {C_BG};")
        layout.addWidget(self.weather_table)
        return w

    def _build_log_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        self.log_table = QTableWidget(0, 2)
        self.log_table.setHorizontalHeaderLabels(["시각 (s)", "이벤트"])
        self.log_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch)
        self.log_table.setColumnWidth(0, 90)
        self.log_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers)
        self.log_table.setAlternatingRowColors(True)
        self.log_table.setStyleSheet(
            f"alternate-background-color: {C_PANEL};"
            f"background-color: {C_BG};")
        layout.addWidget(self.log_table)
        return w

    # ── 툴팁 / 편성 표시 ────────────────────────────────────────────────────

    _SHIP_DISPLAY = {
        'KDX-III-B2': '이지스 구축함 KDX-III Batch II (정조대왕급)',
        'KDX-III-B1': '이지스 구축함 KDX-III Batch I (세종대왕급)',
        'KDX-II':     '구축함 (KDX-II 충무공이순신급)',
        'FFX-I':      '호위함 FFX Batch I (인천급)',
        'FFX-II':     '호위함 FFX Batch II (대구급)',
        'FFX-III':    '호위함 FFX Batch III (충남급)',
    }

    # 아군 편대 프리셋 전술 설명 (툴팁용)
    _FRIENDLY_PRESET_TIPS = {
        '단독 작전':              '정조대왕함 1척 단독 방어. 기준 성능 평가 및 단독 교전 테스트.',
        '기동전단 기본':          '이지스 1 + 구축함 1 + 호위함 1. 균형 편성, 기본 방어력 평가.',
        'BMD 중점':               'SM-3 탑재 이지스 2척 체제. 탄도미사일·HGV 방어 특화, BMD 채널 극대화.',
        '대잠 중점':              '이지스 1 + 호위함 2. 잠수함 위협 특화 편성. 홍상어·청상어 재고 집중.',
        '대잠전단':               '이지스 1 + 호위함 2 + KSS-II × 2. 아군 잠수함 포함 입체 대잠전.',
        '최대 편대':              '이지스 2 + 구축함 2 + 호위함 2, 총 6척. 종합 방어력 최대 평가.',
        '이지스 기동전단':        '실제 교리 기반. 정조대왕함 중심 + KDX-II 2 + FFX-I/II 2 + 보급함.',
        '이지스 기동전단 (강화)': '전시 확장 편성. 이지스 2척 + KDX-II 2 + FFX 2 + 보급함.',
        '전 이지스 기동전단':     '이지스 4척 완전 편성 (B2×1 + B1×3). SM-3 채널 극대화, 최강 방공.',
        '독도함 상륙전단':        '독도함(LPH) 중심 상륙작전 편성. 헬기 대잠 특화, 연안 화력 지원.',
        '동해 해역방어 (1함대)':  '1함대 교리. KDX-II + FFX-I 2 + PKG 4 + PCC 2. 동해 연안 방어.',
        '서해 해역방어 (2함대)':  '2함대 교리. FFX-I 2 + PKG 4 + PCC 2. 서해 연안 방어.',
        '한미 기동전단 기본':     '한미 연합. KDX-III-B2 + DDG-51 × 2 + KDX-II + FFX-II + FFX-I.',
        '한미 기동전단 강화':     '한미 연합 강화. 이지스 2(한) + DDG-51 2 + CG-47 + KDX-II 2 + AOE.',
        '한미 항모전단 지원':     '한미 항모전단. CVN + DDG-51 × 3 + CG-47 + 한국 이지스 + KDX-II 2.',
    }

    # 적군 편대 프리셋 전술 설명 (툴팁용)
    _ENEMY_PRESET_TIPS = {
        'A2/AD 항공 포화':    'J-16 × 4 + H-6 × 2. 장거리 공대함미사일 포화 — SM-2·RAM 재고 소모 유도.',
        '항모 킬 체인':       'DF-21D + DF-17(HGV) + J-20(스텔스). BMD + 스텔스 복합 — SM-3 필수.',
        '수상함 편대전':      '055형 × 1 + 052D × 2 + 022형 × 4. 대함미사일 집중 — 채널 포화 테스트.',
        '대잠 복합':          '093형 + 039형 잠수함. 어뢰 + 잠수함 발사 순항미사일 동시 위협.',
        'BMD 탄도 포화':      'KN-23·DF-15·DF-21D·DF-17 혼합. SM-3 BMD 성능 집중 검증. 최고 난이도 탄도.',
        '전면전 포화':        '전 카테고리 혼합 최고 난이도. J-20·DF-17·055형·DF-21D·093형.',
        '북한 탄도 포화':     'KN-23 × 3 + 화성-15 + 화살-2. 북한 교리 기반 탄도 + 순항 병행 공격.',
        '러시아 극초음속':    '킨잘·지르콘·Kh-101. 극초음속 2종 + 스텔스 순항 — SM-3/6 연속 소진.',
        '잠수함 복합 포화':   '039형 × 3 + 093형. 다중 잠수함 동시 위협 — 대잠 전력 한계 테스트.',
    }

    def _friendly_preset_tooltip(self, name: str) -> str:
        desc  = self._FRIENDLY_PRESET_TIPS.get(name, '')
        ships = V7_FLEET_PRESETS.get(name, [])
        lines = ([desc, ''] if desc else []) + ['편성:']
        for s in ships:
            disp = self._SHIP_DISPLAY.get(s['type'], s['type'])
            lines.append(f"  • {s['name']}  ({disp})")
        return '\n'.join(lines)

    def _enemy_preset_tooltip(self, name: str) -> str:
        desc    = self._ENEMY_PRESET_TIPS.get(name, '')
        threats = V7_ENEMY_FLEET_PRESETS.get(name, [])
        lines   = ([desc, ''] if desc else []) + ['위협 구성:']
        for t in threats:
            lines.append(f"  • {t['preset']}  ×{t['count']}")
        return '\n'.join(lines)

    def _update_fleet_detail(self, preset_name: str):
        if not _V7_OK or preset_name not in V7_FLEET_PRESETS:
            self.lbl_fleet_detail.setText('')
            return
        lines = []
        for s in V7_FLEET_PRESETS[preset_name]:
            disp = self._SHIP_DISPLAY.get(s['type'], s['type'])
            lines.append(f"• {s['name']}  ({disp})")
        self.lbl_fleet_detail.setText('\n'.join(lines))
        self.cmb_fleet.setToolTip(self._friendly_preset_tooltip(preset_name))

    def _update_detect_info(self, _=None):
        if not _V7_OK:
            return
        r = calculate_fleet_detect_ranges(
            self.cmb_fleet.currentText(),
            self.cmb_weather.currentText())
        rf_pct = int(r['radar_factor'] * 100)
        sf_pct = int(r['sonar_factor'] * 100)
        self.lbl_detect_info.setText(
            f"📡 대공 {r['대공']}km  대함 {r['대함']}km  (레이더 ×{rf_pct}%)\n"
            f"🔊 대잠 {r['대잠']}km  (소나 ×{sf_pct}%)\n"
            f"기준함: {r['leading_ship']} · 데이터링크 적용"
        )

    def _update_enemy_row_tooltip(self, cmb: QComboBox, name: str):
        if not _V7_OK or name not in V7_ENEMY_DB:
            return
        cmb.setToolTip(self._enemy_tip(name))

    def _update_enemy_preset_detail(self, preset_name: str):
        if not _V7_OK or preset_name not in V7_ENEMY_FLEET_PRESETS:
            self.lbl_enemy_preset_detail.setText('')
            return
        units = V7_ENEMY_FLEET_PRESETS[preset_name]
        label_lines = []
        for e in units:
            label_lines.append(f"• {e['preset']}  ×{e['count']}")
        self.lbl_enemy_preset_detail.setText('\n'.join(label_lines))
        self.cmb_fleet_preset_e.setToolTip(self._enemy_preset_tooltip(preset_name))

    def _update_difficulty_tooltip(self, diff: str):
        if not _V7_OK or diff not in V7_RANDOM_CFG:
            return
        cfg = V7_RANDOM_CFG[diff]
        lo, hi = cfg['total_count']
        pool = ', '.join(cfg['pool'][:4]) + ('...' if len(cfg['pool']) > 4 else '')
        self.cmb_difficulty.setToolTip(
            f"[{diff}] 총 {lo}~{hi}대 | 최대 {cfg['max_types']}종\n풀: {pool}")

    @staticmethod
    def _enemy_tip(name: str) -> str:
        if not _V7_OK or name not in V7_ENEMY_DB:
            return ''
        e = V7_ENEMY_DB[name]
        mach = e['speed_ms'] / 340
        lines = [
            f"【{name}】",
            f"분류: {e.get('category','?')} | 종류: {e.get('type','?')}",
            f"속도: 마하 {mach:.1f}  |  RCS: {e['rcs_m2']}㎡",
        ]
        if e.get('missile_name'):
            lines.append(f"미사일: {e['missile_name']}")
            lines.append(f"  사거리 {e.get('missile_range_km','?')}km"
                         f"  |  속도 {e.get('missile_speed_ms','?')}m/s")
        if e.get('is_hgv'):
            lines.append("⚠ 극초음속 활공체 — SM-3만 요격 가능")
        if e.get('is_qbm'):
            lines.append("⚠ 저고도기동탄도 — SM-3 거의 무력화")
        sd = e.get('self_defense_pk', 0)
        if sd > 0:
            lines.append(f"자체방어 Pk: {sd:.0%}")
        return '\n'.join(lines)

    def _on_enemy_mode_changed(self, _idx=None):
        """적군 편대 모드 전환 시 관련 위젯 show/hide."""
        mode = self.cmb_enemy_mode.currentText()
        is_preset = mode == '프리셋'
        is_mixed  = mode == '혼합 시나리오'
        self.cmb_fleet_preset_e.setVisible(is_preset)
        self.lbl_enemy_preset_detail.setVisible(is_preset)
        self._mixed_row.setVisible(is_mixed)
        self._rand_row.setVisible(mode == '랜덤')
        if is_preset and self.cmb_fleet_preset_e.count():
            self._update_enemy_preset_detail(self.cmb_fleet_preset_e.currentText())
        if is_mixed and self.cmb_mixed_scenario.count():
            self._update_mixed_scenario_detail(self.cmb_mixed_scenario.currentText())

    def _update_mixed_scenario_detail(self, scenario_name: str):
        """NEW-A: 혼합 시나리오 설명 업데이트."""
        if not _V7_OK or scenario_name not in V7_MIXED_SCENARIOS:
            self.lbl_mixed_detail.setText('')
            return
        sc = V7_MIXED_SCENARIOS[scenario_name]
        desc = sc.get('description', '')
        wave_lines = []
        for w in sc.get('waves', []):
            d = w['delay_s']
            parts = ', '.join(f"{s['preset']} ×{s['count']}" for s in w['threats'])
            wave_lines.append(f"  +{d:>3}s  {parts}")
        self.lbl_mixed_detail.setText(desc + '\n' + '\n'.join(wave_lines))

    def _apply_style(self):
        self.setStyleSheet(STYLE_MAIN)

    # ── 시뮬 실행 ────────────────────────────────────────────────────────────

    def _run_sim(self):
        # 적군 모드 및 편대 구성 (포팅 A)
        mode_label = self.cmb_enemy_mode.currentText()
        mode_map   = {'프리셋': 'preset', '혼합 시나리오': 'mixed', '랜덤': 'random'}
        enemy_mode = mode_map.get(mode_label, 'preset')

        cfg = {
            # 아군 편대 (탐지거리는 엔진이 함대+날씨로 자동 계산)
            'fleet_preset':      self.cmb_fleet.currentText(),
            'weather':           self.cmb_weather.currentText(),
            'detect_km_manual':  False,
            # 적군 (포팅 A)
            'enemy_fleet_mode':       enemy_mode,
            'enemy_fleet_preset':     self.cmb_fleet_preset_e.currentText(),
            'mixed_scenario':         self.cmb_mixed_scenario.currentText(),
            'enemy_fleet_difficulty': self.cmb_difficulty.currentText(),
            'enemy_fleet_seed':       self.spn_seed.value() or None,
            # 전술 옵션 — 항상 ON
            'enable_ecm':         True,
            'enable_evasion':     True,
            'enable_decoy':       True,
            'enable_selfdefense': True,
            # 항공 자산 — 항상 ON
            'enable_helo': True,
            'enable_p3c':  True,
            'enable_p8a':  True,
            # 방어 전술 — 항상 ON (UI 체크박스 읽기)
            'enable_layered_defense': True,
            'enable_cec_preassign':   True,
            'enable_multibearing':       self.chk_multibearing.isChecked(),
            'enable_cec_jammed':         self.chk_cec_jammed.isChecked(),
            'enable_ship_evasion':       self.chk_ship_evasion.isChecked(),
            'enable_random_placement':   True,
            'random_spread_km':          10.0,
            'enemy_tactics':          {
                '없음': None, 'V자 대형': 'v_formation',
                '포위 기동': 'encirclement'
            }.get(self.cmb_enemy_tactics.currentText(), None),
            'sim_seed':               self.spn_sim_seed.value() or None,
            # C&D 시간
            'cd_time_s':      10,
            'confirm_time_s': 3,
        }
        mode_idx = self.cmb_sim_mode.currentIndex() if hasattr(self, 'cmb_sim_mode') else 1
        mc_n = [5_000, 10_000, 100_000][mode_idx]
        precision_mode = (mode_idx == 2)
        sobol_npp = self.spn_sobol_npp.value() if hasattr(self, 'spn_sobol_npp') else 3

        self.btn_run.setEnabled(False)
        self._prog.setVisible(True)
        self._t0 = time.time()
        self._lbl_status.setText("실행 중...")

        self._worker = SimWorker(cfg, mc_n, precision_mode=precision_mode,
                                 sobol_npp=sobol_npp)
        self._worker.progress.connect(self._on_progress)
        self._worker.progress_detail.connect(self._on_progress_detail)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.sim_started.connect(self.tab_sysmon.mark_sim_start)
        self._worker.sim_ended.connect(self.tab_sysmon.mark_sim_end)
        self._worker.batch_done.connect(self.tab_sysmon.on_batch_done)
        self._worker.progress_detail.connect(self.tab_sysmon.on_progress_detail)
        # 플로팅 모니터 연결
        self._worker.sim_started.connect(self._show_float_mon)
        self._worker.sim_ended.connect(self._float_mon.close)
        self._worker.progress_detail.connect(self._float_mon.update_mc)
        self._worker.progress.connect(self._float_mon.update_status)
        self._worker.rate_update.connect(self._float_mon.update_rate)
        self._worker.start(QThread.Priority.LowPriority)  # BUG-1

    def _show_float_mon(self):
        """플로팅 모니터를 메인 창 오른쪽 하단에 배치 후 표시. sysmon 탭 자동 전환."""
        geo = self.geometry()
        mon = self._float_mon
        x = geo.right()  - mon.width()  - 20
        y = geo.bottom() - mon.height() - 60
        mon.move(x, y)
        mon.show()
        self._sidebar.setCurrentRow(6)  # 시스템 모니터 탭으로 자동 전환

    def _on_progress(self, msg: str):
        self._lbl_status.setText(msg)

    def _on_progress_detail(self, done: int, total: int, eta: float):
        eta_str = f" | 잔여 {eta:.0f}s" if eta > 0 else ""
        self._lbl_status.setText(f"MC {done}/{total}{eta_str}")

    def _on_finished(self, result: dict, mc: dict):
        elapsed = time.time() - self._t0
        self._result = result
        self._mc     = mc

        self.btn_run.setEnabled(True)
        self._prog.setVisible(False)
        cvar_str = f" | CVaR {mc.get('cvar', 0):.1%}" if mc.get('cvar') is not None else ''
        self._lbl_status.setText(
            f"완료 ({elapsed:.1f}s) | "
            f"요격률 {mc['mean_intercept']:.1%}{cvar_str} | "
            f"MC {mc['n']}회")

        self._update_cards(result, mc)
        self.tab_anim.load_frames(result.get('frames', []))
        self._fill_req(result, mc)
        self._fill_log(result.get('log', []))
        cfg  = self._worker.cfg  if self._worker else {}
        self._fill_diagnosis(result, mc, cfg)
        mc_n = self._worker.mc_n if self._worker and hasattr(self._worker, 'mc_n') else 100
        # BUG-1: 감도 분석·최소 재고 워커를 즉시 기동하면 GIL 독점으로 UI 프리즈
        # → 해당 탭 방문 시점까지 lazy-start로 연기
        self._pending_cfg  = cfg
        self._pending_mc_n = mc_n

        # 모든 차트 페이지를 dirty로 표시 (11·12는 탭 방문 시 워커 기동)
        self._page_dirty = {1, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19}

        # 히스토리 저장 (최대 5개)
        self._history.append({
            'mean_intercept': mc['mean_intercept'],
            'full_pass_rate': mc.get('full_pass_rate', 0),
            'mean_cost':      mc.get('mean_cost', result.get('total_cost', 0)),
            'label': f"#{len(self._history)+1}  {cfg.get('weather','?')} / "
                     f"{cfg.get('mixed_scenario') or cfg.get('enemy_fleet_preset') or cfg.get('enemy_fleet_mode','?')}",
        })
        if len(self._history) > 5:
            self._history.pop(0)

        self._sidebar.setCurrentRow(1)  # MC 통계로 자동 전환
        self._on_page_changed(1)       # BUG-1: 이미 row 1이면 currentRowChanged 미발화 → 수동 트리거
        _write_sim_log(cfg, result, mc)

    def _fill_req(self, result: dict, mc: dict):
        """포팅 D: REQ 판정 테이블 채우기."""
        if not _V7_OK:
            return
        verdicts, details = evaluate_req_v7(result, mc)
        self.req_table.setRowCount(0)
        for req, v, d in zip(REQ_ITEMS_V7, verdicts, details):
            row = self.req_table.rowCount()
            self.req_table.insertRow(row)
            for col, text in enumerate([req['id'], req['name'],
                                        'PASS' if v else 'FAIL', d]):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter
                                      if col != 3 else Qt.AlignmentFlag.AlignLeft
                                      | Qt.AlignmentFlag.AlignVCenter)
                if col == 2:
                    item.setForeground(QColor('#2ecc71' if v else '#e74c3c'))
                self.req_table.setItem(row, col, item)

    def _fill_diagnosis(self, result: dict, mc: dict, cfg: dict):
        """자동 취약점 진단 카드를 REQ 탭 상단 패널에 채운다."""
        if not _V7_OK:
            return
        # 기존 카드 초기화
        while self._diag_layout.count():
            item = self._diag_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        cards = diagnose_vulnerabilities_v7(result, mc, cfg)

        _SEV_COLOR = {
            'HIGH': ('#e74c3c', '🔴 위험'),
            'MED':  ('#e67e22', '🟡 경고'),
            'LOW':  ('#3498db', '🔵 주의'),
            'OK':   ('#2ecc71', '🟢 양호'),
        }

        for card in cards:
            sev   = card['severity']
            color, badge = _SEV_COLOR.get(sev, ('#95a5a6', sev))

            frame = QFrame()
            frame.setStyleSheet(
                f"QFrame {{ background: #161b22; border-left: 5px solid {color};"
                f" border-radius: 5px; padding: 6px; }}"
            )
            fl = QVBoxLayout(frame)
            fl.setContentsMargins(10, 6, 10, 6)
            fl.setSpacing(4)

            # 제목줄
            title_lbl = QLabel(f"{badge}  {card['title']}")
            title_lbl.setStyleSheet(f"color:{color}; font-size:13px; font-weight:bold; border:none;")
            fl.addWidget(title_lbl)

            # 상세
            if card.get('detail'):
                det = QLabel(card['detail'])
                det.setStyleSheet(f"color:{C_TEXT}; font-size:12px; border:none;")
                det.setWordWrap(True)
                fl.addWidget(det)

            # 개선 제안
            if card.get('suggestion'):
                sugg = QLabel(card['suggestion'])
                sugg.setStyleSheet(f"color:{C_SUBTEXT}; font-size:11px; border:none;")
                sugg.setWordWrap(True)
                fl.addWidget(sugg)

            self._diag_layout.addWidget(frame)

        self._diag_layout.addStretch()

    def _run_weather_compare(self):
        """포팅 D: 날씨별 3종 비교 실행 (WeatherWorker 비차단)."""
        if not _V7_OK or not hasattr(self, '_result'):
            QMessageBox.information(self, "안내", "먼저 시뮬레이션을 실행하세요.")
            return
        cfg = self._worker.cfg if self._worker else {}
        if not cfg:
            return
        self.btn_weather_run.setEnabled(False)
        self.btn_weather_run.setText("실행 중... (약 30~60초)")
        self._weather_worker = WeatherWorker(cfg, n=1000)
        self._weather_worker.finished.connect(self._on_weather_done)
        self._weather_worker.error.connect(self._on_weather_error)
        self._weather_worker.start()

    def _on_weather_done(self, sc: dict):
        self.weather_table.setRowCount(0)
        for label, res in sc.items():
            row = self.weather_table.rowCount()
            self.weather_table.insertRow(row)

            # 최다 소모 무기 (잔여 재고 가장 적은 것)
            wpn_rem = res.get('weapon_avg_remaining', {})
            if wpn_rem:
                top_wpn = min(wpn_rem, key=lambda k: wpn_rem[k])
                top_wpn_str = f"{top_wpn} ({wpn_rem[top_wpn]:.1f}발 잔여)"
            else:
                top_wpn_str = "—"

            # 가장 많이 피격된 함정
            ship_h = res.get('ship_avg_hits', {})
            if ship_h and max(ship_h.values()) > 0:
                top_ship = max(ship_h, key=lambda k: ship_h[k])
                top_ship_str = f"{top_ship} ({ship_h[top_ship]:.2f}회)"
            else:
                top_ship_str = "없음"

            values = [label,
                      f"{res['mean_intercept']:.1%}",
                      f"{res['full_pass_rate']:.1%}",
                      f"${res['mean_cost']:,.0f}",
                      top_wpn_str,
                      top_ship_str]
            for col, text in enumerate(values):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if col == 1:
                    item.setForeground(
                        QColor('#2ecc71' if res['mean_intercept'] >= 0.9 else '#e74c3c'))
                self.weather_table.setItem(row, col, item)
        self.btn_weather_run.setEnabled(True)
        self.btn_weather_run.setText("🌤️  날씨별 비교 실행 (각 1000회 MC)")
        self._sidebar.setCurrentRow(3)

    def _on_weather_error(self, msg: str):
        QMessageBox.critical(self, "날씨 비교 오류", msg)
        self.btn_weather_run.setEnabled(True)
        self.btn_weather_run.setText("🌤️  날씨별 비교 실행 (각 1000회 MC)")

    def _on_error(self, msg: str):
        self.btn_run.setEnabled(True)
        self._prog.setVisible(False)
        self._lbl_status.setText("오류 발생")
        QMessageBox.critical(self, "시뮬레이션 오류", msg)

    def closeEvent(self, event):
        # SimWorker 중단 (MC 분석 실행 중이면 배치 루프에서 중단 신호 감지)
        if self._worker and self._worker.isRunning():
            self._worker.requestInterruption()
            self._worker.quit()
            if not self._worker.wait(2000):
                self._worker.terminate()
                self._worker.wait(500)
        # SensitivityWorker 중단
        sens = getattr(self, '_sens_worker', None)
        if sens and sens.isRunning():
            sens.requestInterruption()
            sens.quit()
            if not sens.wait(1000):
                sens.terminate()
                sens.wait(500)
        # MinStockWorker 중단
        ms = getattr(self, '_ms_worker', None)
        if ms and ms.isRunning():
            ms.requestInterruption()
            ms.quit()
            if not ms.wait(1000):
                ms.terminate()
                ms.wait(500)
        # WeatherWorker 중단
        ww = getattr(self, '_weather_worker', None)
        if ww and ww.isRunning():
            ww.requestInterruption()
            ww.quit()
            if not ww.wait(800):
                ww.terminate()
                ww.wait(300)
        # 차트 렌더 워커 11개 중단 (ChartPageWidget._worker)
        for attr in ('tab_mc_canvas', 'tab_channel', 'tab_cost_eff',
                     'tab_ammo_curve', 'tab_ci', 'tab_timeline',
                     'tab_bearing', 'tab_req_radar', 'tab_threat_type',
                     'tab_vuln_time', 'tab_history',
                     'tab_sensitivity', 'tab_min_stock'):   # ChartPageWidget으로 전환된 탭 추가
            widget = getattr(self, attr, None)
            if widget:
                widget.stop_worker()
        # 애니메이션 렌더 워커 중단
        rw = getattr(self.tab_anim, '_render_worker', None)
        if rw and rw.isRunning():
            rw.cancel()
            if not rw.wait(1000):
                rw.terminate()
                rw.wait(500)
        # 글로벌 프로세스 풀 종료 (워커 프로세스 강제 kill 포함)
        _shutdown_global_pool()
        # 시스템 모니터 워커 중단 (nvidia-smi subprocess 포함)
        _stop_sys_data_worker()
        # 남은 자식 프로세스 강제 종료 (좀비 프로세스 완전 제거)
        try:
            me = psutil.Process()
            for child in me.children(recursive=True):
                try:
                    child.kill()
                except Exception:
                    pass
        except Exception:
            pass
        event.accept()

    # ── 결과 렌더링 ──────────────────────────────────────────────────────────

    def _update_cards(self, result: dict, mc: dict):
        self._cards['intercept'].setText(f"{mc['mean_intercept']:.1%}")
        self._cards['intercept'].setStyleSheet(
            f"color:{'#2ecc71' if mc['mean_intercept'] >= 0.9 else '#e74c3c'};")
        self._cards['full_pass'].setText(f"{mc['full_pass_rate']:.1%}")
        cvar_val = mc.get('cvar')
        if cvar_val is not None:
            self._cards['cvar'].setText(f"{cvar_val:.1%}")
            self._cards['cvar'].setStyleSheet(
                f"color:{'#2ecc71' if cvar_val >= 0.7 else '#e74c3c'};")
        else:
            self._cards['cvar'].setText("—")
        self._cards['friendly_hit'].setText(str(result['friendly_hits']))
        self._cards['friendly_hit'].setStyleSheet(
            f"color:{'#2ecc71' if result['friendly_hits'] == 0 else '#e74c3c'};")
        self._cards['enemy_dest'].setText(str(result['enemy_ships_destroyed']))
        self._cards['cost'].setText(f"${result['total_cost']:,.0f}")
        sorties = result.get('aircraft_sorties', 0)
        self._cards['aircraft'].setText(f"{sorties}회" if sorties else "—")
        # 사용된 시드 표시 (재현용)
        seed = result.get('used_seed')
        if seed:
            self._lbl_seed_used.setText(f"시드: {seed}  (재현하려면 시뮬 시드에 동일 값 입력)")
        else:
            self._lbl_seed_used.setText("시드: 랜덤  (재현 불가)")

    def _draw_mc_chart(self, result: dict, mc: dict, cfg: dict):
        self.tab_mc_canvas.start_render(_render_mc_chart, result, mc, cfg)

    def _fill_log(self, log: list):
        # BUG-1: 최대 300행 제한 + 배치 삽입 (UI 블로킹 방지)
        entries = log[-300:] if len(log) > 300 else log
        self.log_table.setUpdatesEnabled(False)
        self.log_table.setRowCount(0)
        for t, msg in entries:
            row = self.log_table.rowCount()
            self.log_table.insertRow(row)
            t_item = QTableWidgetItem(f"{t:.0f}s")
            t_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.log_table.setItem(row, 0, t_item)
            self.log_table.setItem(row, 1, QTableWidgetItem(msg))
        self.log_table.setUpdatesEnabled(True)

    def _draw_channel_heatmap(self, result: dict):
        self.tab_channel.start_render(_render_channel_heatmap, result)

    def _draw_cost_effect(self, result: dict, mc: dict):
        self.tab_cost_eff.start_render(_render_cost_effect, result, mc)

    def _draw_ammo_curve(self, mc: dict):
        self.tab_ammo_curve.start_render(_render_ammo_curve, mc)

    def _draw_ci_chart(self, mc: dict):
        self.tab_ci.start_render(_render_ci_chart, mc)

    def _draw_timeline(self, result: dict):
        self.tab_timeline.start_render(_render_timeline, result)

    def _lazy_start_sensitivity(self):
        """감도 분석 탭 첫 방문 시 SensitivityWorker 기동 (lazy-start)."""
        if not hasattr(self, '_pending_cfg'):
            return
        sens = getattr(self, '_sens_worker', None)
        if sens and sens.isRunning():
            return
        self._sensitivity_placeholder()
        self._sens_worker = SensitivityWorker(self._pending_cfg, self._pending_mc_n)
        self._sens_worker.finished.connect(self._on_sensitivity_done)
        self._sens_worker.error.connect(lambda e: self._sensitivity_error(e))
        self._sens_worker.start(QThread.Priority.LowPriority)

    def _lazy_start_min_stock(self):
        """최소 재고 탭 첫 방문 시 MinStockWorker 기동 (lazy-start)."""
        if not hasattr(self, '_pending_cfg'):
            return
        ms = getattr(self, '_ms_worker', None)
        if ms and ms.isRunning():
            return
        self._min_stock_placeholder()
        self._ms_worker = MinStockWorker(self._pending_cfg, self._pending_mc_n)
        self._ms_worker.progress.connect(self._on_min_stock_progress)
        self._ms_worker.finished.connect(self._on_min_stock_done)
        self._ms_worker.error.connect(lambda e: self._min_stock_error(e))
        self._ms_worker.start(QThread.Priority.LowPriority)

    def _sensitivity_placeholder(self):
        self.tab_sensitivity._loading_lbl.setText("  감도 분석 계산 중… ⏳")
        self.tab_sensitivity._pane.setCurrentIndex(0)

    def _sensitivity_error(self, msg: str):
        self.tab_sensitivity._loading_lbl.setText(f"  감도 분석 오류: {msg}")

    def _min_stock_placeholder(self):
        self.tab_min_stock._loading_lbl.setText("  최소 재고 역산 계산 중… ⏳")
        self.tab_min_stock._pane.setCurrentIndex(0)

    def _min_stock_error(self, msg: str):
        self.tab_min_stock._loading_lbl.setText(f"  최소 재고 계산 오류: {msg}")

    def _on_min_stock_progress(self, i: int, total: int, name: str):
        if i < total:
            self._lbl_status.setText(f"최소 재고 계산 중 ({i}/{total}) — {name}")

    def _on_min_stock_done(self, results: dict, target_rate: float):
        self.tab_min_stock.start_render(_render_min_stock_chart, results, target_rate)

    def _on_sensitivity_done(self, labels: list, lows: list, highs: list, base_rate: float):
        self.tab_sensitivity.start_render(_render_sensitivity_chart, labels, lows, highs, base_rate)

    def _draw_bearing_vulnerability(self, result: dict):
        self.tab_bearing.start_render(_render_bearing_vulnerability, result)

    def _draw_req_radar(self, result: dict, mc: dict):
        self.tab_req_radar.start_render(_render_req_radar, result, mc)

    def _draw_threat_type(self, result: dict, mc: dict):
        self.tab_threat_type.start_render(_render_threat_type, result, mc)

    def _draw_vuln_time(self, result: dict):
        self.tab_vuln_time.start_render(_render_vuln_time, result)

    def _draw_history_compare(self, result: dict, mc: dict):
        self.tab_history.start_render(_render_history_compare, list(self._history))

    def _draw_stress_test(self, mc: dict):
        self.tab_stress.start_render(_render_stress_test, mc.get('stress', {}))

    def _draw_sobol_chart(self, mc: dict):
        self.tab_sobol.start_render(_render_sobol_chart, mc.get('sobol', {}))

    # ── 보고서 내보내기 ──────────────────────────────────────────────────────

    def _export_excel(self):
        """결과를 Excel 보고서로 저장."""
        if not _V7_OK or not self._result:
            QMessageBox.information(self, "안내", "먼저 시뮬레이션을 실행하세요.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Excel 보고서 저장", "report.xlsx", "Excel (*.xlsx)")
        if not path:
            return
        try:
            cfg = self._worker.cfg if self._worker else {}
            save_excel_report_v7(self._result, self._mc, cfg, path)
            QMessageBox.information(self, "저장 완료", f"Excel 보고서 저장:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "오류", str(e))

    def _export_pdf(self):
        """결과를 PDF 보고서로 저장 (matplotlib 다중 페이지)."""
        if not _V7_OK or not self._result:
            QMessageBox.information(self, "안내", "먼저 시뮬레이션을 실행하세요.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "PDF 보고서 저장", "report.pdf", "PDF (*.pdf)")
        if not path:
            return
        try:
            self._generate_pdf_report(path)
            QMessageBox.information(self, "저장 완료", f"PDF 보고서 저장:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "오류", str(e))

    def _generate_pdf_report(self, path: str):
        """matplotlib PdfPages로 다중 페이지 PDF 생성."""
        from matplotlib.backends.backend_pdf import PdfPages
        result = self._result
        mc     = self._mc
        cfg    = self._worker.cfg if self._worker else {}

        with PdfPages(path) as pdf:
            # 1페이지: 커버 + 핵심 지표
            fig, ax = plt.subplots(figsize=(11.7, 8.3))
            fig.patch.set_facecolor('#0a0e1a')
            ax.set_facecolor('#0a0e1a')
            ax.axis('off')
            lines = [
                ("이지스 기동전단 통합 방어 시뮬레이터", 30, C_ACCENT, 'bold'),
                ("전투 분석 보고서", 20, C_TEXT, 'normal'),
                ("", 14, C_TEXT, 'normal'),
                (f"날씨: {cfg.get('weather', '—')}  |  "
                 f"적군: {cfg.get('enemy_fleet_preset', cfg.get('enemy_fleet_mode', '—'))}  |  "
                 f"MC: {mc.get('n', '—')}회", 12, C_SUBTEXT, 'normal'),
                ("", 12, C_TEXT, 'normal'),
                (f"요격률: {mc['mean_intercept']:.1%}  |  "
                 f"완전 요격: {mc.get('full_pass_rate', 0):.1%}  |  "
                 f"아군 피격: {result.get('friendly_hits', 0)}회", 14, '#2ecc71', 'bold'),
                (f"격추 비용: ${mc.get('mean_cost', 0):,.0f}  |  "
                 f"적 격침: {result.get('enemy_ships_destroyed', 0)}척", 14, C_TEXT, 'normal'),
            ]
            y = 0.85
            for text, size, color, weight in lines:
                ax.text(0.5, y, text, ha='center', va='top', color=color,
                        fontsize=size, fontweight=weight, transform=ax.transAxes)
                y -= 0.10
            pdf.savefig(fig, facecolor='#0a0e1a')
            plt.close(fig)

            # 2페이지: MC 통계 차트
            mc_bytes = getattr(self.tab_mc_canvas, '_raw_bytes', b'')
            if mc_bytes:
                import io as _io
                from matplotlib.image import imread as _mpl_imread
                fig2, ax2 = plt.subplots(figsize=(11.7, 8.3))
                fig2.patch.set_facecolor('#0a0e1a')
                ax2.set_facecolor('#0a0e1a')
                ax2.imshow(_mpl_imread(_io.BytesIO(mc_bytes)))
                ax2.axis('off')
                ax2.set_title('MC 통계', color=C_TEXT, fontsize=14, pad=10)
                pdf.savefig(fig2, facecolor='#0a0e1a')
                plt.close(fig2)

            # 3페이지: 비용 효과 + 탄약 소모
            fig3, axes3 = plt.subplots(1, 2, figsize=(11.7, 8.3))
            fig3.patch.set_facecolor('#0a0e1a')
            fig3.suptitle('비용 효과 / 탄약 소모', color=C_TEXT, fontsize=14)
            for ax3 in axes3:
                ax3.set_facecolor('#0a0e1a')

            # 비용 효과
            wpn_rem = mc.get('weapon_avg_remaining', {})
            if wpn_rem:
                wnames = list(wpn_rem.keys())
                wvals  = list(wpn_rem.values())
                axes3[0].barh(wnames, wvals, color=C_ACCENT, alpha=0.8)
                axes3[0].set_xlabel('평균 잔여 재고', color=C_SUBTEXT, fontsize=9)
                axes3[0].set_title('무기별 잔여 재고', color=C_TEXT, fontsize=10)
                axes3[0].tick_params(colors=C_SUBTEXT)
                for sp in axes3[0].spines.values(): sp.set_color('#1e2a3a')

            # 함정별 피격
            ship_hits = mc.get('ship_avg_hits', {})
            if ship_hits:
                snames = list(ship_hits.keys())
                svals  = list(ship_hits.values())
                cols   = ['#e74c3c' if v > 0.5 else '#2ecc71' for v in svals]
                axes3[1].bar(snames, svals, color=cols, alpha=0.8)
                axes3[1].set_ylabel('평균 피격 횟수', color=C_SUBTEXT, fontsize=9)
                axes3[1].set_title('함정별 평균 피격 (MC)', color=C_TEXT, fontsize=10)
                axes3[1].tick_params(colors=C_SUBTEXT, axis='x', rotation=15)
                for sp in axes3[1].spines.values(): sp.set_color('#1e2a3a')

            pdf.savefig(fig3, facecolor='#0a0e1a')
            plt.close(fig3)

            # 4페이지: 교전 로그 요약
            fig4, ax4 = plt.subplots(figsize=(11.7, 8.3))
            fig4.patch.set_facecolor('#0a0e1a')
            ax4.set_facecolor('#0a0e1a')
            ax4.axis('off')
            ax4.set_title('교전 로그 (최근 30건)', color=C_TEXT, fontsize=14, pad=10)
            log = result.get('log', [])[-30:]
            y = 0.95
            for t, msg in log:
                color = '#e74c3c' if '[피격]' in msg else (
                    '#2ecc71' if '[요격]' in msg else C_TEXT)
                ax4.text(0.02, y, f"[{t:>5.0f}s]  {msg[:90]}",
                         ha='left', va='top', color=color, fontsize=7,
                         transform=ax4.transAxes, fontfamily='monospace')
                y -= 0.03
                if y < 0.02:
                    break
            pdf.savefig(fig4, facecolor='#0a0e1a')
            plt.close(fig4)


# ════════════════════════════════════════════════════════════════════════════
#  SplashWindow — 런처 화면
# ════════════════════════════════════════════════════════════════════════════

_FEATURES = [
    ("🗺️  전장 애니메이션",
     "전투 상황을 입체적인 2.5D 영상으로 재생. 마우스 휠·버튼으로 줌인/줌아웃, "
     "재생 속도 0.5×~4× 조절, 격추·피격 장면으로 바로 이동(북마크), 화면 캡처 저장 가능."),
    ("📊  반복 시뮬레이션 통계",
     "같은 시나리오를 수백~수천 번 자동 반복해 '평균적으로 몇 %를 막아내는지' 확률로 계산. "
     "결과가 운에 따라 얼마나 달라지는지 분포 그래프로 확인 가능."),
    ("✅  전술 요구조건 자동 판정",
     "한국 해군 전술 요구조건 8가지(응답 시간·요격률·함정 생존율 등)를 "
     "시뮬레이션 결과로 자동 통과/실패 판정. 어떤 조건이 미달인지 한눈에 확인."),
    ("🌤️  날씨 조건 비교",
     "맑음·흐림·황사·풍랑·폭풍 등 날씨 조건별로 각각 반복 시뮬레이션해 "
     "날씨가 요격률·무기 소모·피격 횟수에 얼마나 영향을 주는지 나란히 비교."),
    ("📜  교전 기록 로그",
     "미사일 발사, 요격 성공/실패, 함정 피격 등 매 초 단위로 발생한 "
     "모든 교전 사건을 시간 순서대로 전부 기록. 무엇이 언제 일어났는지 추적 가능."),
    ("📡  레이더 채널 포화도",
     "각 함정의 레이더 추적 채널이 시간대별로 얼마나 사용됐는지 색상 히트맵으로 표시. "
     "빨간색에 가까울수록 채널이 꽉 찬 상태 — 채널 포화 시 추가 요격 불가."),
    ("💰  격추 비용 효과",
     "적 1기를 격추하는 데 평균 얼마의 비용이 들었는지 달러 단위로 표시. "
     "무기별 잔여 재고도 함께 확인 가능."),
    ("🔫  탄약 소모 현황",
     "반복 시뮬레이션 기준 평균 잔여 탄약을 무기별 가로 막대그래프로 표시. "
     "어떤 무기가 가장 많이 소모됐는지 비교."),
    ("📈  요격률 신뢰 구간",
     "요격률이 몇 %~몇 % 범위 안에 들어오는지 95% 신뢰구간으로 표시. "
     "함정별 평균 피격 횟수 히스토그램도 함께 표시."),
    ("⏱️  교전 타임라인",
     "어느 시점에 어떤 교전이 발생했는지 시간축 위에 점으로 표시. "
     "언제 가장 많은 위협이 몰렸는지, 요격이 집중된 구간이 어딘지 한눈에 파악."),
    ("🌪️  설정 감도 분석",
     "재고 수량·탐지거리·날씨 등 설정값을 하나씩 바꿔가며 "
     "요격률이 얼마나 민감하게 반응하는지 분석. 백그라운드 실행이라 다른 작업에 영향 없음."),
    ("🧭  방향별 취약점",
     "북·남·동·서 각 방향에서 공격이 들어올 때 피격률과 요격률이 "
     "어떻게 달라지는지 방사형 그래프로 표시 — 어느 방향이 가장 취약한지 확인."),
    ("🎯  요구조건 충족률",
     "8가지 전술 요구조건 각각을 얼마나 충족했는지 방사형 그래프로 한눈에 비교. "
     "전체적인 방어 역량의 균형이 잡혀 있는지 시각적으로 파악."),
    ("📊  위협 유형별 요격률",
     "항공기·탄도미사일·순항미사일·잠수함 유형별로 각각 몇 %를 막아냈는지 분류해서 표시. "
     "어떤 유형의 위협에 취약한지 파악 가능."),
    ("⏰  취약 시간대 분석",
     "교전 시작 후 몇 초 구간에 피격이 집중됐는지 히스토그램으로 표시. "
     "가장 위험한 시간대를 빨간색으로 강조해 방어 집중 구간을 식별."),
    ("🔄  이전 결과 비교",
     "최대 5회 실행한 결과의 요격률과 비용을 자동으로 누적 비교. "
     "설정을 바꿔가며 어떤 조합이 더 효과적인지 히스토리로 추적."),
    ("📋  시나리오 프로필 저장",
     "적 종류·날씨·재고·편대 구성 등 시뮬레이션 설정 전체를 이름 붙여 저장하고 "
     "언제든 불러올 수 있음. 자주 쓰는 시나리오를 매번 다시 설정할 필요 없음."),
    ("📄  보고서 내보내기",
     "시뮬레이션 결과 전체를 Excel 파일과 PDF(4페이지)로 저장. "
     "요격률·비용·교전 통계·그래프가 모두 포함된 공식 분석 보고서 형태."),
    ("🖥️  시스템 모니터",
     "시뮬레이션 실행 중 CPU·RAM·GPU·코어별 사용률을 실시간으로 표시. "
     "백그라운드에서 동작해 시뮬레이션 속도에 영향을 주지 않음."),
    ("📺  실시간 진행 팝업",
     "반복 시뮬레이션 실행 중 별도 팝업 창으로 진행률·완료 횟수·예상 남은 시간·"
     "CPU/RAM/GPU 사용률·처리 속도를 실시간 표시. 창을 마우스로 자유롭게 이동 가능."),
    ("⚡  멀티코어 병렬 처리",
     "프로그램 시작 시 미리 워커 프로세스를 준비해두고, 반복 시뮬레이션 시 "
     "최대 8개 코어를 동시에 활용해 빠르게 처리. 코어가 많을수록 분석 속도 향상."),
    ("⚙️  현실적 전술 기동",
     "데이터링크 두절 상황, 함정 회피 기동, V자 편대 진형, 포위 공격, "
     "다방위 동시 공격 등 실제 해전에서 쓰이는 전술 상황을 시뮬레이션에 반영."),
    ("🌊  적군 위협 데이터베이스",
     "중국 PLA해군·공군 함정·전투기, 북한 탄도·순항·잠수함발사 미사일, "
     "러시아 극초음속 무기, YJ-21·YJ-18 신형 미사일, 드론 떼·소형 자폭 드론까지 총 43종 위협 수록."),
    ("⚓  한국 해군 함정 DB (10종+)",
     "KDX-III Batch I/II(세종대왕·정조대왕급)·KDX-II 구축함·FFX Batch I/II/III 호위함 외 "
     "PKG 윤영하급, PCC 포항급, PKX-B 참수리-II, LPH 독도함급, AOE 소양함까지 수록. "
     "Batch별 SM-3 탑재 유무·해궁 장착 여부 등 실제 제원 반영."),
    ("🏴  현실 기반 편대 프리셋 (10종)",
     "한국 해군 실 교리 기반 편대 5종 추가: 이지스 기동전단 / 이지스 기동전단(강화) / "
     "독도함 상륙전단 / 동해 해역방어(1함대) / 서해 해역방어(2함대). "
     "기존 5종(단독·기본·BMD·대잠·최대)과 합쳐 총 10종 프리셋 제공."),
]


# ════════════════════════════════════════════════════════════════════════════
#  스펙시트 패널
# ════════════════════════════════════════════════════════════════════════════
class SpecSheetPanel(QWidget):
    """선택 유닛 스펙시트 — 우측 패널 (사진 + 카테고리별 상세 스펙 + 스크롤)"""

    _TYPE_ICON = {
        '전투기': '✈', '전폭기': '✈', '폭격기': '✈',
        '탄도미사일': '🚀', '순항미사일': '🚀',
        '극초음속활공체': '🚀', '저고도기동탄도': '🚀',
        '고속정': '⚓', '초계함': '⚓', '호위함': '⚓',
        '구축함': '⚓', '상륙함': '⚓', '순양함': '⚓',
        '잠수함': '🔱',
        '_ship': '⚓', '_weapon': '💥',
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"background:{C_PANEL}; border-left:1px solid {C_BORDER};"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 8, 10, 8)
        root.setSpacing(6)

        # ── 상단: 가로 사진 박스 ──────────────────────────────────────────
        self._img_lbl = QLabel()
        self._img_lbl.setFixedHeight(220)
        self._img_lbl.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self._img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._img_lbl.setStyleSheet(
            f"background:{C_BG}; border:1px solid {C_BORDER};"
            f" border-radius:4px; font-size:48px;"
        )
        root.addWidget(self._img_lbl)

        # ── 제목 / 부제 행 ────────────────────────────────────────────────
        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        title_row.setContentsMargins(2, 0, 2, 0)

        self._title_lbl = QLabel("← 왼쪽 목록에서 유닛을 선택하세요")
        self._title_lbl.setStyleSheet(
            f"color:{C_ACCENT}; font-size:16px; font-weight:bold;"
        )

        self._sub_lbl = QLabel()
        self._sub_lbl.setStyleSheet(f"color:{C_SUBTEXT}; font-size:14px;")
        self._sub_lbl.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        title_row.addWidget(self._title_lbl)
        title_row.addStretch()
        title_row.addWidget(self._sub_lbl)
        root.addLayout(title_row)

        # 구분선
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color:{C_BORDER};")
        root.addWidget(sep)

        # ── 카테고리 스크롤 영역 ──────────────────────────────────────────
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet(
            f"QScrollArea {{ background:transparent; border:none; }}"
            f"QWidget {{ background:transparent; }}"
            f"QScrollBar:vertical {{ width:6px; background:{C_BG}; }}"
            f"QScrollBar::handle:vertical {{ background:{C_BORDER}; border-radius:3px; min-height:20px; }}"
            f"QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}"
        )

        self._scroll_w = QWidget()
        self._scroll_vbox = QVBoxLayout(self._scroll_w)
        self._scroll_vbox.setContentsMargins(0, 2, 4, 2)
        self._scroll_vbox.setSpacing(0)
        self._scroll.setWidget(self._scroll_w)

        self._note_lbl = QLabel()
        self._note_lbl.setStyleSheet(
            f"color:{C_SUBTEXT}; font-size:15px; font-style:italic; padding:2px 4px;"
        )
        self._note_lbl.setWordWrap(True)

        root.addWidget(self._scroll, stretch=1)
        root.addWidget(self._note_lbl)

    # ── 내부 헬퍼 ──────────────────────────────────────────────────────
    def _clear_scroll(self):
        while self._scroll_vbox.count():
            item = self._scroll_vbox.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _add_category(self, cat_name: str, cat_fields: list):
        hdr = QLabel(f"  {cat_name.upper()}")
        hdr.setStyleSheet(
            f"color:{C_ACCENT}; font-size:14px; font-weight:bold;"
            f" background:#1a2030; padding:3px 0px; margin-top:4px;"
        )
        self._scroll_vbox.addWidget(hdr)

        gw = QWidget()
        gl = QGridLayout(gw)
        gl.setContentsMargins(4, 2, 2, 4)
        gl.setHorizontalSpacing(8)
        gl.setVerticalSpacing(3)
        gl.setColumnStretch(1, 1)

        for r, (label, value) in enumerate(cat_fields):
            lbl_w = QLabel(f"{label}:")
            lbl_w.setStyleSheet(f"color:{C_SUBTEXT}; font-size:14px;")
            lbl_w.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            val_w = QLabel(str(value))
            val_w.setStyleSheet(f"color:{C_TEXT}; font-size:14px; font-weight:600;")
            val_w.setWordWrap(True)
            val_w.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            gl.addWidget(lbl_w, r, 0)
            gl.addWidget(val_w, r, 1)

        self._scroll_vbox.addWidget(gw)

    def clear(self):
        self._img_lbl.setPixmap(QPixmap())
        self._img_lbl.setText("")
        self._title_lbl.setText("← 왼쪽 목록에서 유닛을 선택하세요")
        self._sub_lbl.setText("")
        self._note_lbl.setText("")
        self._clear_scroll()

    def show_unit(self, name: str, db_entry: dict, spec: dict, unit_type: str = 'enemy'):
        """unit_type: 'enemy' | 'ship' | 'weapon'"""
        self._title_lbl.setText(name)

        # 사진 또는 아이콘 (.jpg → .png → .webp 순서로 탐색)
        _img_base = os.path.join(_res('assets/images'), name)
        img_path = next(
            (p for p in (_img_base + ext for ext in ('.jpg', '.png', '.webp'))
             if os.path.exists(p)),
            None
        )
        if img_path:
            pix = QPixmap(img_path).scaled(
                1200, 220,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._img_lbl.setPixmap(pix)
            self._img_lbl.setText("")
        else:
            self._img_lbl.setPixmap(QPixmap())
            if unit_type == 'ship':
                icon = '⚓'
            elif unit_type == 'weapon':
                icon = '💥'
            else:
                typ = db_entry.get('type', '')
                icon = self._TYPE_ICON.get(typ, '❓')
            self._img_lbl.setText(icon)

        # 부제목
        origin    = spec.get('origin', '')
        type_desc = spec.get('type_desc', db_entry.get('type', ''))
        self._sub_lbl.setText(
            f"{origin}  |  {type_desc}" if (origin and type_desc) else (origin or type_desc)
        )

        # 카테고리 렌더링
        self._clear_scroll()
        categories = spec.get('categories', [])
        if categories:
            for cat_name, cat_fields in categories:
                self._add_category(cat_name, cat_fields)
        else:
            fields = spec.get('fields', [])
            if fields:
                self._add_category('제원', fields)
        self._scroll_vbox.addStretch()

        # 비고
        self._note_lbl.setText(spec.get('note', ''))


class SplashWindow(QWidget):
    """프로그램 진입 런처. [시뮬레이터 시작] → MainWindow 열기."""

    launch_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        from datetime import datetime
        _write_log(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]  앱 시작')
        self.setWindowTitle("이지스 기동전단 통합 방어 시뮬레이터")
        self.setFixedSize(1400, 960)
        self.setStyleSheet(f"""
            QWidget {{ background: {C_BG}; color: {C_TEXT};
                       font-family: 'Malgun Gothic', 'Segoe UI'; font-size: 17px; }}
            QTabWidget::pane {{ border: 1px solid {C_BORDER}; background: {C_BG}; }}
            QTabBar::tab {{ background: {C_PANEL}; color: {C_SUBTEXT};
                            padding: 10px 26px; border: 1px solid {C_BORDER}; font-size: 16px; }}
            QTabBar::tab:selected {{ background: {C_BG}; color: {C_ACCENT};
                                     border-bottom: 2px solid {C_ACCENT}; }}
            QPushButton {{ background: {C_ACCENT}; color: white; border: none;
                           padding: 14px 36px; border-radius: 6px; font-size: 18px;
                           font-family: 'Malgun Gothic', 'Segoe UI', sans-serif; }}
            QPushButton:hover {{ background: #2980b9; }}
            QTableWidget {{ background: {C_PANEL}; gridline-color: {C_BORDER};
                            border: none; font-size: 16px; }}
            QHeaderView::section {{ background: {C_PANEL}; color: {C_ACCENT};
                                    border: none; padding: 8px; font-size: 16px; }}
        """)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        title = QLabel("⚓ 이지스 기동전단 통합 방어 시뮬레이터")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont('Malgun Gothic', 26, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {C_ACCENT}; padding: 8px;")
        layout.addWidget(title)

        sub = QLabel("v7.21  |  PyQt6 네이티브 UI  |  한국 해군 이지스 기동전단 다층 방어 시뮬레이터")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet(f"color: {C_SUBTEXT}; font-size: 16px;")
        layout.addWidget(sub)

        tabs = QTabWidget()
        layout.addWidget(tabs, stretch=1)
        tabs.addTab(self._build_feature_tab(),      "📋  탑재 기능")
        tabs.addTab(self._build_changelog_tab(),   "📝  패치 내역")
        tabs.addTab(self._build_plan_tab(),        "🗓️  향후 계획")
        tabs.addTab(self._build_enemy_db_tab(),    "🔴  적군 DB")
        tabs.addTab(self._build_friendly_db_tab(), "🔵  아군 DB")

        btn = QPushButton("🚀  시뮬레이터 시작")
        btn.setFixedHeight(46)
        btn.clicked.connect(self.launch_requested.emit)
        layout.addWidget(btn)

    def _build_feature_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        tbl = QTableWidget(len(_FEATURES), 2)
        tbl.setHorizontalHeaderLabels(["탭 / 기능", "설명"])
        tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        tbl.setColumnWidth(0, 280)
        tbl.setWordWrap(True)
        tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tbl.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        tbl.verticalHeader().setVisible(False)
        tbl.setAlternatingRowColors(True)
        tbl.setStyleSheet(
            f"alternate-background-color: {C_PANEL}; background-color: {C_BG};")
        for row, (name, desc) in enumerate(_FEATURES):
            ni = QTableWidgetItem(name)
            ni.setForeground(QColor(C_ACCENT))
            desc_item = QTableWidgetItem(desc)
            desc_item.setTextAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            tbl.setItem(row, 0, ni)
            tbl.setItem(row, 1, desc_item)
        tbl.verticalHeader().setDefaultSectionSize(68)
        layout.addWidget(tbl)
        return w

    def _build_changelog_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        changelog = []
        cl_path = _res('changelog.json')
        if os.path.exists(cl_path):
            try:
                with open(cl_path, encoding='utf-8-sig') as f:
                    changelog = json.load(f)
            except Exception:
                pass
        if not changelog:
            layout.addWidget(QLabel("changelog.json 없음"))
            return w
        tbl = QTableWidget()
        tbl.setColumnCount(2)
        tbl.setHorizontalHeaderLabels(["버전", "변경 내용"])
        hh = tbl.horizontalHeader()
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        tbl.setColumnWidth(0, 60)
        tbl.verticalHeader().setDefaultSectionSize(28)
        tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tbl.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        tbl.verticalHeader().setVisible(False)
        tbl.setShowGrid(False)
        tbl.setStyleSheet(f"background-color: {C_BG}; gridline-color: {C_PANEL};")

        prev_date = None
        for entry in changelog:
            ver   = entry.get('version', '')
            date  = entry.get('date', '')
            items = entry.get('changes', [])
            if date != prev_date:
                # 날짜 그룹 헤더 행
                row = tbl.rowCount()
                tbl.insertRow(row)
                tbl.setRowHeight(row, 32)
                date_item = QTableWidgetItem(f"  {date}")
                date_item.setBackground(QColor(C_PANEL))
                date_item.setForeground(QColor(C_SUBTEXT))
                f = date_item.font(); f.setBold(True); date_item.setFont(f)
                tbl.setItem(row, 0, date_item)
                tbl.setItem(row, 1, QTableWidgetItem(""))
                tbl.item(row, 1).setBackground(QColor(C_PANEL))
                tbl.setSpan(row, 0, 1, 2)
                prev_date = date
            for i, item in enumerate(items):
                row = tbl.rowCount()
                tbl.insertRow(row)
                if i == 0:
                    vi = QTableWidgetItem(ver)
                    vi.setForeground(QColor(C_ACCENT))
                    vi.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    tbl.setItem(row, 0, vi)
                else:
                    tbl.setItem(row, 0, QTableWidgetItem(""))
                tbl.setItem(row, 1, QTableWidgetItem(f"  {item}"))
        layout.addWidget(tbl)
        return w

    def _build_plan_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        _PLANS = [
            ("v7.x", "높음", "레이더 역할 세분화",
             "현재는 레이더 하나가 '찾기·추적·미사일 유도'를 동시에 담당. "
             "앞으로는 세 역할을 분리해 각 단계마다 처리 시간을 부여. "
             "적이 레이더 전파를 따라 날아오는 대방사미사일에 대응해 "
             "레이더를 껐다 켜는 전술이 실제로 효과 있게 작동."),
            ("v7.x", "중간", "실행 기록 저장",
             "시뮬레이션을 돌릴 때마다 날짜·설정·결과를 자동으로 파일에 저장. "
             "나중에 과거 기록을 다시 보거나 설정을 그대로 불러와서 재사용 가능. "
             "CSV 파일로 내보내기 지원."),
            ("v7.x", "높음", "최적 무기 조합 추천",
             "탑재할 수 있는 미사일 수 제한 안에서 가장 높은 요격률을 내는 무기 조합을 자동으로 찾아줌. "
             "수백 가지 조합을 자동 비교해 최적 구성과 예상 요격률을 결과로 표시."),
            ("v8.x", "높음", "중국 항모전단 시나리오",
             "중국 랴오닝·산둥·푸젠 항모전단(항모 + 대형 구축함 + 호위함 + 잠수함) 시나리오 추가. "
             "전단 내 함정들이 서로를 방어하고, 함재기 공격과 대함미사일 공격 시나리오 모두 지원."),
            ("v8.x", "중간", "해협 통과 방어 시나리오",
             "아군 함정이 좁은 해협을 통과하는 동안 방어하는 시나리오. "
             "위협이 특정 방향에서 집중 출현하고, 섬이나 지형이 레이더를 가리는 효과 반영. "
             "이어도·대한해협·쓰시마 해협 프리셋 제공."),
            ("v8.x", "높음", "한미 연합 작전",
             "한미 연합 작전 시 미 해군은 탄도미사일, 한국 해군은 순항미사일을 각각 담당하는 임무 분담 구현. "
             "결과 화면에 한국·미국 기여도를 분리해서 표시."),
            ("v8.x", "낮음", "도움말 / 튜토리얼 탭",
             "처음 쓰는 사람도 바로 따라할 수 있도록 탭 추가. "
             "주요 용어 설명, 시뮬레이션 실행 순서 안내, 자주 묻는 질문(FAQ) 포함. "
             "처음 실행 시 이 탭이 자동으로 열림."),
            ("v9.x", "매우 높음", "완전 양방향 교전",
             "현재는 아군만 미사일을 막지만, 앞으로는 적 함정·항공기도 "
             "아군 미사일을 자체 방공으로 요격. "
             "공격과 방어가 동시에 이뤄지는 실제 해전 구현. 시뮬레이션 구조 전면 재설계 필요."),
            ("v9.x", "높음", "지형·해상 환경 반영",
             "실제 지형 데이터를 적용해 산이나 섬 뒤에 있으면 레이더가 탐지 못하는 음영 구역 구현. "
             "바닷속 수온층 데이터를 적용해 수온에 따라 음파 탐지 거리가 달라지는 현실적 대잠 환경 구현."),
            ("v7.x", "낮음", "용어 툴팁",
             "향후 계획·기능 목록에 등장하는 군사·기술 용어에 마우스를 올리면 "
             "쉬운 말로 설명하는 작은 창이 뜨도록 추가."),
        ]

        tbl = QTableWidget(len(_PLANS), 4)
        tbl.setHorizontalHeaderLabels(["버전", "난이도", "항목", "설명"])
        hh = tbl.horizontalHeader()
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        tbl.setColumnWidth(0, 55)
        tbl.setColumnWidth(1, 70)
        tbl.verticalHeader().setVisible(False)
        tbl.setWordWrap(True)
        tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tbl.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        tbl.setShowGrid(False)
        tbl.setStyleSheet(f"background-color: {C_BG}; gridline-color: {C_PANEL};")

        diff_color = {'매우 높음': '#c0392b', '높음': '#e74c3c', '중간': C_ORANGE, '낮음': '#2ecc71'}
        for r, (ver, diff, title, desc) in enumerate(_PLANS):
            vi = QTableWidgetItem(ver)
            vi.setForeground(QColor(C_ACCENT))
            vi.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            di = QTableWidgetItem(diff)
            di.setForeground(QColor(diff_color.get(diff, C_TEXT)))
            di.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            desc_item = QTableWidgetItem(f"  {desc}")
            desc_item.setTextAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            tbl.setItem(r, 0, vi)
            tbl.setItem(r, 1, di)
            tbl.setItem(r, 2, QTableWidgetItem(f"  {title}"))
            tbl.setItem(r, 3, desc_item)
        tbl.verticalHeader().setDefaultSectionSize(68)

        layout.addWidget(tbl)
        return w

    # ── DB 탭 공통 헬퍼 ──────────────────────────────────────────────────────
    # 카테고리별 배경/전경색
    _CAT_BG  = {'대공': '#2a1010', '대함': '#2a1a08', '대잠': '#0a1228'}
    _CAT_FG  = {'대공': '#ff8080', '대함': '#ffaa55', '대잠': '#6699ff'}
    _LIST_SS = f"""
        QListWidget {{
            background:{C_BG}; border:none; outline:none; font-size:13px;
        }}
        QListWidget::item {{
            padding:5px 10px; border-bottom:1px solid {C_BORDER};
        }}
        QListWidget::item:selected {{
            background:{C_ACCENT}; color:#000; font-weight:bold;
        }}
        QListWidget::item:hover:!selected {{ background:{C_PANEL}; }}
    """

    def _make_list_panel(self, entries: list, mode: str,
                         cat_color: bool = False,
                         display_key: str | None = None,
                         tooltip_fn=None) -> tuple:
        """
        왼쪽 QListWidget + 오른쪽 SpecSheetPanel QSplitter를 생성해 반환.
        entries: [(key, info), ...]
        mode: 'enemy' | 'weapon' | 'ship' | 'aircraft'
        cat_color: True면 category 필드 기반 행 색상 적용
        display_key: info 안에서 표시 이름으로 쓸 키 (None이면 항목 key 사용)
        """
        name_list = QListWidget()
        name_list.setStyleSheet(self._LIST_SS)

        for key, info in entries:
            label = info.get(display_key, key) if display_key else key
            it = QListWidgetItem(f"  {label}")
            if cat_color:
                cats = info.get('category', '대공')
                # FRIENDLY_DB는 리스트, ENEMY_DB는 문자열
                c = cats[0] if isinstance(cats, list) else cats
                it.setBackground(QColor(self._CAT_BG.get(c, C_BG)))
                it.setForeground(QColor(self._CAT_FG.get(c, C_TEXT)))
            else:
                it.setForeground(QColor(C_ACCENT))
            if tooltip_fn:
                it.setToolTip(tooltip_fn(key, info))
            name_list.addItem(it)

        spec_panel = SpecSheetPanel()
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setStyleSheet(
            "QSplitter::handle { background: " + C_BORDER + "; width: 2px; }")
        splitter.addWidget(name_list)
        splitter.addWidget(spec_panel)
        splitter.setSizes([230, 9999])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        def _on_select(row):
            if row < 0 or row >= len(entries):
                spec_panel.clear()
                return
            k, e = entries[row]
            spec_panel.show_unit(k, e, _SPEC_DETAIL_DB.get(k, {}), mode)

        name_list.currentRowChanged.connect(_on_select)
        return splitter, name_list, spec_panel

    def _wrap_splitter(self, splitter) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(4)
        lay.addWidget(splitter, stretch=1)
        return w

    # ── 적군 DB 탭 ─────────────────────────────────────────────────────────
    def _build_enemy_db_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        if not _V7_OK:
            layout.addWidget(QLabel("엔진 로드 실패 — 적군 DB를 표시할 수 없습니다."))
            return w

        _normalize_enemy_db()
        db = V7_ENEMY_DB

        # 유형별 분류
        _AIRCRAFT_T = {'전투기', '폭격기', '전폭기'}
        _SHIP_T     = {'고속정', '초계함', '호위함', '구축함'}
        _MISSILE_T  = {'순항미사일', '탄도미사일', '극초음속활공체', '저고도기동탄도', '대방사미사일'}
        _SUB_T      = {'잠수함'}

        def _split(types):
            return [(k, v) for k, v in db.items() if v.get('type','') in types]

        aircraft_e = _split(_AIRCRAFT_T)
        ship_e     = _split(_SHIP_T)
        missile_e  = _split(_MISSILE_T)
        sub_e      = _split(_SUB_T)

        inner_tabs = QTabWidget()
        inner_tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border:none; }}
            QTabBar::tab {{ background:{C_PANEL}; color:{C_TEXT}; padding:4px 14px; }}
            QTabBar::tab:selected {{ background:{C_ACCENT}; color:#000; }}
        """)

        # ── 전투기 탭 ─────────────────────────────────────────────────────
        sp, _, _ = self._make_list_panel(aircraft_e, 'enemy', cat_color=False)
        inner_tabs.addTab(self._wrap_splitter(sp), f"✈  전투기  ({len(aircraft_e)})")

        # ── 함정 탭 ───────────────────────────────────────────────────────
        sp, _, _ = self._make_list_panel(ship_e, 'enemy', cat_color=False)
        inner_tabs.addTab(self._wrap_splitter(sp), f"⚓  함정  ({len(ship_e)})")

        # ── 무기 탭 (카테고리 색상) ────────────────────────────────────────
        sp, nl, _ = self._make_list_panel(missile_e, 'enemy', cat_color=True)
        # 범례 행 추가
        legend = QHBoxLayout()
        legend.setSpacing(12)
        for cat, fg in self._CAT_FG.items():
            bg = self._CAT_BG[cat]
            lbl = QLabel(f"  {cat}  ")
            lbl.setStyleSheet(
                f"background:{bg}; color:{fg}; border-radius:3px;"
                f" font-size:11px; padding:1px 4px;")
            legend.addWidget(lbl)
        legend.addStretch()
        mw = QWidget()
        ml = QVBoxLayout(mw)
        ml.setContentsMargins(6, 6, 6, 6)
        ml.setSpacing(4)
        ml.addLayout(legend)
        ml.addWidget(sp, stretch=1)
        inner_tabs.addTab(mw, f"🚀  무기  ({len(missile_e)})")

        # ── 잠수함 탭 ─────────────────────────────────────────────────────
        sp, _, _ = self._make_list_panel(sub_e, 'enemy', cat_color=False)
        inner_tabs.addTab(self._wrap_splitter(sp), f"🤿  잠수함  ({len(sub_e)})")

        layout.addWidget(inner_tabs, stretch=1)
        return w

    # ── 아군 DB 탭 ─────────────────────────────────────────────────────────
    def _build_friendly_db_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        if not _V7_OK:
            layout.addWidget(QLabel("엔진 로드 실패 — 아군 DB를 표시할 수 없습니다."))
            return w

        inner_tabs = QTabWidget()
        inner_tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border:none; }}
            QTabBar::tab {{ background:{C_PANEL}; color:{C_TEXT}; padding:4px 14px; }}
            QTabBar::tab:selected {{ background:{C_ACCENT}; color:#000; }}
        """)

        # 무기 DB (카테고리 색상)
        inner_tabs.addTab(self._build_weapon_sub_tab(), f"🚀  무기  ({len(V7_FRIENDLY_DB)})")

        # 함정 DB (잠수함 제외)
        surface_ships = [(k, v) for k, v in V7_SHIP_DB.items()
                         if not v.get('is_submarine', False)]
        inner_tabs.addTab(self._build_ship_sub_tab(surface_ships),
                          f"⚓  함정  ({len(surface_ships)})")

        # 잠수함 DB
        subs = [(k, v) for k, v in V7_SHIP_DB.items()
                if v.get('is_submarine', False)]
        inner_tabs.addTab(self._build_ship_sub_tab(subs),
                          f"🤿  잠수함  ({len(subs)})")

        # 항공 DB
        aircraft_e = list(V7_AIRCRAFT_DB.items())
        sp, _, _ = self._make_list_panel(aircraft_e, 'aircraft', cat_color=False)
        inner_tabs.addTab(self._wrap_splitter(sp),
                          f"🚁  항공  ({len(aircraft_e)})")

        layout.addWidget(inner_tabs, stretch=1)
        return w

    def _build_weapon_sub_tab(self) -> QWidget:
        wpn_entries = list(V7_FRIENDLY_DB.items())

        # 범례 행
        legend = QHBoxLayout()
        legend.setSpacing(12)
        for cat, fg in self._CAT_FG.items():
            bg = self._CAT_BG[cat]
            lbl = QLabel(f"  {cat}  ")
            lbl.setStyleSheet(
                f"background:{bg}; color:{fg}; border-radius:3px;"
                f" font-size:11px; padding:1px 4px;")
            legend.addWidget(lbl)
        legend.addStretch()

        sp, _, _ = self._make_list_panel(wpn_entries, 'weapon', cat_color=True)
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(4)
        lay.addLayout(legend)
        lay.addWidget(sp, stretch=1)
        return w

    def _build_ship_sub_tab(self, ship_entries: list | None = None) -> QWidget:
        if ship_entries is None:
            ship_entries = list(V7_SHIP_DB.items())

        def _tip(key, info):
            display = info.get('display', key)
            inv = info.get('default_inventory', {})
            lines = [f"【{display} 기본 탑재】"]
            for wname, cnt in inv.items():
                lines.append(f"  • {wname}: {'무한' if cnt >= 9999 else cnt}발")
            return "\n".join(lines)

        # display 필드로 표시
        disp_entries = [(k, v) for k, v in ship_entries]
        name_list = QListWidget()
        name_list.setStyleSheet(self._LIST_SS)
        for key, info in disp_entries:
            display = info.get('display', key)
            it = QListWidgetItem(f"  {display}")
            it.setForeground(QColor(C_ACCENT))
            it.setToolTip(_tip(key, info))
            name_list.addItem(it)

        spec_panel = SpecSheetPanel()
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setStyleSheet(
            "QSplitter::handle { background: " + C_BORDER + "; width: 2px; }")
        splitter.addWidget(name_list)
        splitter.addWidget(spec_panel)
        splitter.setSizes([230, 9999])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        def _on_select(row):
            if row < 0 or row >= len(disp_entries):
                spec_panel.clear()
                return
            skey, sentry = disp_entries[row]
            spec_panel.show_unit(skey, sentry, _SPEC_DETAIL_DB.get(skey, {}), 'ship')

        name_list.currentRowChanged.connect(_on_select)
        return self._wrap_splitter(splitter)


# ════════════════════════════════════════════════════════════════════════════
#  진입점
# ════════════════════════════════════════════════════════════════════════════
def main():
    global CHART_DPI
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # 화면 DPI 기반 차트 렌더 해상도 자동 설정
    screen = app.primaryScreen()
    if screen:
        px_w = int(screen.size().width() * screen.devicePixelRatio())
        # figsize 12인치 기준: 화면 너비 90%를 커버하는 DPI 계산
        CHART_DPI = max(150, min(300, px_w * 3 // 40))

    # 앱 아이콘 설정
    _icon_path = _res('aegis_icon.ico')
    if os.path.exists(_icon_path):
        from PyQt6.QtGui import QIcon
        app.setWindowIcon(QIcon(_icon_path))

    # 다크 팔레트 기본 적용
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window,        QColor(C_BG))
    palette.setColor(QPalette.ColorRole.WindowText,    QColor(C_TEXT))
    palette.setColor(QPalette.ColorRole.Base,          QColor(C_PANEL))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(C_BG))
    palette.setColor(QPalette.ColorRole.Text,          QColor(C_TEXT))
    palette.setColor(QPalette.ColorRole.Button,        QColor(C_PANEL))
    palette.setColor(QPalette.ColorRole.ButtonText,    QColor(C_TEXT))
    palette.setColor(QPalette.ColorRole.Highlight,     QColor(C_ACCENT))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor('#ffffff'))
    app.setPalette(palette)

    _main_win: list = []  # mutable closure

    def _launch():
        splash.close()
        win = MainWindow()
        _main_win.append(win)
        win.show()

    app.aboutToQuit.connect(_shutdown_global_pool)
    app.aboutToQuit.connect(_stop_sys_data_worker)

    _start_sys_data_worker()   # 블로킹 I/O 백그라운드 수집 시작

    splash = SplashWindow()
    splash.launch_requested.connect(_launch)
    splash.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    multiprocessing.freeze_support()   # PyInstaller exe 멀티프로세싱 필수
    # 글로벌 풀 백그라운드 예열 (스플래시 표시 중에 완료됨)
    threading.Thread(target=_init_global_pool, daemon=True).start()
    main()

