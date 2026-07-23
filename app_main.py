"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   합동 통합방어 시뮬레이터  v21.03.01 — PyQt6 런처                          ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  [v21.03.01 — 합동작전 사령부(JCS) 자원 충돌 경고 (v21.1)]                  ║
║  NEW-A  각 군이 독립 배정한 결과의 충돌을 지휘부가 경고로 표면화한다 —      ║
║         상시 관찰층(토글 없음, 교전 결과 무변경). 3종 경고: ①동시 타격      ║
║         협조 미비(유인 폭격 소티 취소) ②육군 지대지 화력 편성했으나 지상    ║
║         작전급 미가동(미참여) ③완파 표적 화력 중복(잔여 표적 재분배).       ║
║         engine_campaign._jcs_warnings — 각 층 지표를 지휘부 관점에서 읽어    ║
║         명명한다(자동 최적화 아님 = _PLANS '조정·충돌경고 수준' 사양).      ║
║  NEW-B  jcs_warning_count MC 집계·노출(반복 캠페인 평균 경고 수).           ║
║         배너: 협조 미비·육군 미참여 중복 표기를 JCS 세그먼트로 통합.        ║
║  ⚠ 설계 판단: '임무 과부하(가용기<수요)' 경고는 배정 시스템이 자기제한적    ║
║     (SEAD 제압 시 수요 소멸·CAS 희소)이라 realistic 무대서 미발동 → 죽은    ║
║     가지로 제외([[project-dead-feature-prevention]]). 사양의 두 충돌(표적    ║
║     겹침=overkill·자산 충돌=deconflict)은 나머지로 커버.                     ║
║                                                                              ║
║  실행: python app_main.py                                                    ║
║  패키지: pip install PyQt6 psutil matplotlib numpy openpyxl                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

# ⚠ 이전 버전 이력은 헤더에서 정리(2026-07-19) — 전체 변경이력은 git log·SESSION_LOG.md·app_changelog.json·`변경이력/` 폴더 참조.
# (CLAUDE.md 헤더 주석 규칙: 헤더엔 현재 버전 + 최근 변경만 남긴다.)

import sys, os, io, time, threading, json, multiprocessing, subprocess as _sp, traceback
from concurrent.futures import ProcessPoolExecutor, as_completed, wait as cf_wait, FIRST_COMPLETED
import psutil

# 앱 표시 버전 — 패치 시 헤더 주석과 함께 이 값만 갱신하면 창 제목 등에 일괄 반영
APP_VERSION = "v21.03.01"

# ── 유틸 계층(app_utils.py로 분리) ─────────────────────────────────────────────
# _GLOBAL_POOL은 app_utils가 재할당하는 전역 → 이름 import 금지(None이 복사돼 예열
# 된 풀을 못 본다). 반드시 app_utils._GLOBAL_POOL로 참조할 것.
import app_utils
from app_utils import (
    _get_gpu_info, _get_cpu_temp, _init_global_pool, _shutdown_global_pool,
    _pool_map, _setup_job_object, _kill_child_processes, _set_pool_priority,
    _res, _token_path, _load_surrogate, _load_forecast_model,
    _SHOWCASE_WEATHER, _SHOWCASES, _SHOWCASE_METRICS, _log_base,
    _log_path, _json_log_path, _app_state_path, _load_app_state,
    _save_app_state, _write_log, _load_json_log, _save_json_log,
    _write_sim_log, _SIM_MODE_NAMES, _db_path, _ensure_db,
    _write_sim_db, _load_sim_db, _clear_sim_db, _PERF_HISTORY,
    _SYS_CACHE, _crash_log_path,
)



from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDialog, QSplitter,
    QVBoxLayout, QHBoxLayout, QFormLayout, QScrollArea,
    QGridLayout, QFrame,
    QLabel, QPushButton, QComboBox, QSpinBox, QTabWidget,
    QTableWidget, QTableWidgetItem, QSlider, QProgressBar,
    QGroupBox, QStatusBar, QMessageBox, QHeaderView,
    QSizePolicy, QCheckBox, QFileDialog, QLineEdit,
    QListWidget, QListWidgetItem, QStackedWidget, QGraphicsDropShadowEffect,
    QTextBrowser, QButtonGroup,
)
from PyQt6.QtGui import (
    QFont, QColor, QPalette, QShortcut, QKeySequence, QPixmap, QPainter,
    QPainterPath, QPen,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSettings, QRectF, QEvent, QObject, QPoint, QUrl

# v14.1: 3D 전장용 WebEngine (미설치 환경에서도 앱이 죽지 않도록 가드)
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    _WEBENGINE_OK = True
except Exception:
    QWebEngineView = None
    _WEBENGINE_OK = False

import matplotlib
matplotlib.use('QtAgg')
# 일부 복합 레이아웃(극좌표·축 off 혼용) 차트의 무해한 tight_layout 경고 억제
import warnings as _warnings
_warnings.filterwarnings('ignore', message='.*not compatible with tight_layout.*')
_warnings.filterwarnings('ignore', message='.*Tight layout not applied.*')
import matplotlib.pyplot as plt
# 전역 한글 폰트: PDF/차트의 제목·축 레이블이 fontfamily 미지정 시 DejaVu Sans(한글 없음)로
# 떨어져 한글이 □로 깨지던 문제 방지. unicode_minus=False는 Malgun Gothic에 유니코드
# 마이너스(−) 글리프가 없어 음수 축 레이블이 깨지던 것을 ASCII 하이픈으로 대체.
plt.rcParams['font.family'] = 'Malgun Gothic'
plt.rcParams['axes.unicode_minus'] = False
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
import numpy as np

# 엔진·스펙DB import 계층 - app_engine.py로 분리(app_workers와 공유해 순환 회피)
import app_engine
from app_engine import (
    ARMY_FIRE_PRESETS, BATTLE_HORIZON_S, COASTAL_SAM_PRESETS,
    REQ_ITEMS_V7, SLOC_ZONES, STRESS_DIMS,
    V7_AIRCRAFT_DB, V7_ENEMY_DB, V7_ENEMY_FLEET_PRESETS,
    V7_FLEET_PRESETS, V7_FRIENDLY_DB, V7_MIXED_SCENARIOS,
    V7_RANDOM_CFG, V7_SHIP_DB, WEATHER_DB,
    WEATHER_INTENSITY_LADDER, WEATHER_TRANSITION_DB, _FLEET_CANDIDATES_COMBINED,
    _FLEET_CANDIDATES_KR, _LHS_PARAM_DEFS, _SPEC_DB_OK,
    _SPEC_DETAIL_DB, _V7_ERR, _V7_OK,
    _forecast_featurize, _heatmap_cell_worker, _mc_batch_worker,
    _mc_lhs_batch_worker, _normalize_enemy_db, build_czml,
    cec_comparison_v7, compare_ab_v7, compute_cvar,
    diagnose_vulnerabilities_v7, evaluate_req_battle_v7, evaluate_req_v7,
    generate_briefing, monte_carlo_lhs, monte_carlo_v7,
    plot_v7, recommend_fleet_v7, run_battle_simulation,
    run_v7_simulation, save_excel_report_v7, save_json_report_v7,
    scenario_comparison_v7, sobol_analysis, stress_test_grid,
)

# color palette + checkbox style -> app_theme.py
from app_theme import (C_BG, C_PANEL, C_BORDER, C_ACCENT, C_TEXT, C_SUBTEXT,
                       C_GREEN, C_RED, C_ORANGE, _wire_chk_color)

# 차트 렌더 DPI는 app_theme.CHART_DPI로 이동(ui_charts와 공유 → 순환 회피).
# 재할당 전역이라 이름 import 금지 — main()도 사용처도 app_theme 경유로 읽고 쓴다.
import app_theme as _theme


# 재사용 위젯 — ui_widgets.py로 분리
from ui_widgets import (NoScrollSpinBox, NoScrollComboBox, _TaskbarProgress,
                        GaugeWidget, ConvergenceWidget, RateHistogramWidget,
                        STYLE_MAIN, _SPIN_UP, _SPIN_DOWN)
# ════════════════════════════════════════════════════════════════════════════

# ════════════════════════════════════════════════════════════════════════════
#  실행 로그 뷰어 다이얼로그
# ════════════════════════════════════════════════════════════════════════════
#  v16.14.02: 아군 함대 직접 편성 다이얼로그
# ════════════════════════════════════════════════════════════════════════════
# 아코디언 사이드바·설정 패널 헬퍼(AccordionSidebar 등) - ui_widgets.py로 이관
from ui_widgets import (_expand_fleet_custom, _collapse_fleet_custom,
                        AccordionSidebar, _HoverPopup, _install_hover,
                        _install_section_popups, _WrapCheckBox, _CfgSectionHeader)

# 모달 다이얼로그 - ui_dialogs.py로 분리
from ui_dialogs import (FleetCustomDialog, SimLogDialog, TacticalDialog)

# 백그라운드 워커(QThread) - app_workers.py로 분리
from app_workers import (CounterfactualWorker, FleetRecommendWorker, ShowcaseCompareWorker,
                         SimWorker, _SimCancelled, _SysDataWorker,
                         _start_sys_data_worker, _stop_sys_data_worker)

# 차트·교전 분석 탭 - ui_charts.py로 분리
# _render_*는 _audit_render_smoke가 getattr(app_main, ...)로 꺼내므로 재노출 필수
from ui_charts import (
    ChartPageWidget, ChartRenderWorker, EngagementAnalysisTab,
    MplCanvas, _classify_weapon, _render_battle_timeline,
    _render_campaign_report, _render_engagement_funnel, _render_engagement_gantt,
)

# 실행 모니터(FloatingMonitor·SysMonitorTab) - ui_monitor.py로 분리
from ui_monitor import FloatingMonitor, SysMonitorTab

# 런처 진입 화면(SplashWindow·SpecSheetPanel) - app_launcher.py로 분리
from app_launcher import SpecSheetPanel, SplashWindow


# 결과 탭 차트 렌더 - ui_charts.py로 이관(재노출: _audit_render_smoke의 getattr 대상)
from ui_charts import (_apply_window_geometry, _center_window, _classify_log_event,
                       _plot_req_radar, _render_ci_chart, _render_fleet_chart,
                       _render_mc_chart, _render_sobol_chart, _render_stress_test)
from scenarios import SCENARIO_LIBRARY

# MainWindow 기능별 mixin - app_main.py 분할 8/N(6개) + 9/N(ConfigPanelExtraMixin)
from mixin_simlifecycle import SimLifecycleMixin
from mixin_configpanel import ConfigPanelMixin
from mixin_configpanel2 import ConfigPanelExtraMixin
from mixin_configpanel3 import ConfigPanelExtra2Mixin
from mixin_showcase import ShowcaseMixin
from mixin_resultpanel import ResultPanelMixin
from mixin_optimize import OptimizeMixin
from mixin_export import ExportMixin


class MainWindow(SimLifecycleMixin, ConfigPanelMixin, ConfigPanelExtraMixin,
                 ConfigPanelExtra2Mixin, ShowcaseMixin,
                 ResultPanelMixin, OptimizeMixin, ExportMixin, QMainWindow):
    """PyQt6 메인 윈도우 — 기능별 mixin으로 분할(app_main.py 분할 8·9/N, 각 파일 참조).
    실행 제어=SimLifecycleMixin(mixin_simlifecycle.py) · 설정 패널=ConfigPanelMixin
    (mixin_configpanel.py) · 쇼케이스=ShowcaseMixin(mixin_showcase.py) · 결과 탭
    =ResultPanelMixin(mixin_resultpanel.py) · 최적화=OptimizeMixin(mixin_optimize.py)
    · 내보내기=ExportMixin(mixin_export.py). 전부 self를 공유하는 다중상속."""


# ════════════════════════════════════════════════════════════════════════════
#  진입점
# ════════════════════════════════════════════════════════════════════════════
_CRASH_FH = None   # faulthandler 파일 핸들 — 프로세스 수명 동안 열어둠 (GC 방지)
# _crash_log_path()는 app_utils.py로 이관(SimLifecycleMixin이 순환 없이 쓰기 위함)


def _install_crash_handler():
    """미처리 예외·C 레벨 크래시를 crash.log에 기록 후 종료.
    Python 예외(슬롯 포함)는 excepthook으로, 세그폴트 등 C 레벨은 faulthandler로 캡처."""
    import traceback, faulthandler
    from datetime import datetime as _dt
    global _CRASH_FH

    path = _crash_log_path()
    # C 레벨 크래시(세그폴트·접근위반) 스택 덤프 — 파일 핸들 유지해야 유효
    try:
        _CRASH_FH = open(path, 'a', encoding='utf-8', buffering=1)
        faulthandler.enable(file=_CRASH_FH, all_threads=True)
    except Exception:
        _CRASH_FH = None

    def _record(exc_type, exc_value, exc_tb):
        try:
            msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
            with open(path, 'a', encoding='utf-8') as f:
                f.write(f"\n===== [CRASH] {_dt.now():%Y-%m-%d %H:%M:%S}  {APP_VERSION} =====\n{msg}\n")
        except Exception:
            pass
        try:
            _write_log(f'[CRASH] {exc_type.__name__}: {exc_value} (crash.log 참고)')
        except Exception:
            pass

    def _on_exception(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            os._exit(0)
        _record(exc_type, exc_value, exc_tb)
        os._exit(1)

    def _on_thread_exception(args):
        if args.exc_type is SystemExit:
            os._exit(0)
        _on_exception(args.exc_type, args.exc_value, args.exc_traceback)

    sys.excepthook = _on_exception
    threading.excepthook = _on_thread_exception


def main():
    _install_crash_handler()
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # 화면 DPI 기반 차트 렌더 해상도 자동 설정
    screen = app.primaryScreen()
    if screen:
        px_w = int(screen.size().width() * screen.devicePixelRatio())
        # figsize 12인치 기준: 화면 너비 90%를 커버하는 DPI 계산
        # app_theme 경유 대입 필수 — 여기서 지역/이름 대입하면 ui_charts가 150을 계속 본다
        _theme.CHART_DPI = max(150, min(300, px_w * 3 // 40))

    # 앱 아이콘 설정
    _icon_path = _res('jds_icon.ico')
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
        win = MainWindow(APP_VERSION)
        _main_win.append(win)
        win.show()

    app.aboutToQuit.connect(_shutdown_global_pool)
    app.aboutToQuit.connect(_stop_sys_data_worker)
    # 어떤 창을 X로 닫든 마지막 창 종료 → aboutToQuit에서 자식 프로세스 일괄 정리
    app.aboutToQuit.connect(_kill_child_processes)

    _start_sys_data_worker()   # 블로킹 I/O 백그라운드 수집 시작

    splash = SplashWindow(APP_VERSION)
    splash.launch_requested.connect(_launch)
    splash.show()
    os._exit(app.exec())


if __name__ == '__main__':
    multiprocessing.freeze_support()   # PyInstaller exe 멀티프로세싱 필수
    # Job Object로 자식 워커를 묶어 메인 종료 시 OS가 자동 정리 (풀 생성 전에 설정)
    _setup_job_object()
    # 글로벌 풀 백그라운드 예열 (스플래시 표시 중에 완료됨)
    threading.Thread(target=_init_global_pool, daemon=True).start()
    main()

