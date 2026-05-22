"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   이지스 기동전단 통합 방어 시뮬레이터  v7.0 — PyQt6 런처                  ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  [6단계 — PyQt6 네이티브 UI / 포팅 A+B]                                    ║
║                                                                              ║
║  NEW-A  MainWindow: 좌/우 분할 레이아웃 (설정 패널 + 결과 탭)               ║
║  NEW-B  ConfigPanel: 엔진 선택·적군 편대·아군 편대·무기 재고·MC 설정        ║
║  NEW-C  SimWorker(QThread): 백그라운드 시뮬 (UI 블로킹 없음)                ║
║  NEW-D  전장 애니메이션 탭: matplotlib canvas + QSlider 재생                ║
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

import sys, os, time, threading
import psutil

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QSplitter,
    QVBoxLayout, QHBoxLayout, QFormLayout, QScrollArea,
    QGridLayout,
    QLabel, QPushButton, QComboBox, QSpinBox, QTabWidget,
    QTableWidget, QTableWidgetItem, QSlider, QProgressBar,
    QGroupBox, QStatusBar, QMessageBox, QHeaderView,
    QSizePolicy, QCheckBox,
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QColor, QPalette

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
        evaluate_req_v7, REQ_ITEMS_V7,
        scenario_comparison_v7, compare_ab_v7,
        save_scenario_v7, load_scenario_v7,
        calculate_fleet_detect_ranges,
    )
    _V7_OK = True
except ImportError as e:
    _V7_OK = False
    _V7_ERR = str(e)
    V7_ENEMY_FLEET_PRESETS = {}
    V7_RANDOM_CFG = {}

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
    font-size: 13px;
}}
QGroupBox {{
    border: 1px solid {C_BORDER};
    border-radius: 6px;
    margin-top: 8px;
    padding-top: 6px;
    font-weight: bold;
    color: {C_ACCENT};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
}}
QComboBox, QSpinBox {{
    background-color: {C_PANEL};
    border: 1px solid {C_BORDER};
    border-radius: 4px;
    padding: 4px 8px;
    color: {C_TEXT};
}}
QComboBox::drop-down {{ border: none; }}
QComboBox QAbstractItemView {{
    background-color: {C_PANEL};
    color: {C_TEXT};
    selection-background-color: {C_ACCENT};
}}
QPushButton {{
    background-color: {C_ACCENT};
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: bold;
    font-size: 13px;
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
    padding: 7px 16px;
    margin-right: 2px;
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
}}
QTableWidget QHeaderView::section {{
    background-color: {C_BG};
    color: {C_ACCENT};
    border: 1px solid {C_BORDER};
    padding: 4px;
    font-weight: bold;
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
    padding: 7px 10px;
    font-size: 13px;
    font-family: 'Malgun Gothic', 'Segoe UI', sans-serif;
}}
"""


# ════════════════════════════════════════════════════════════════════════════
#  백그라운드 시뮬레이션 워커
# ════════════════════════════════════════════════════════════════════════════
class SimWorker(QThread):
    progress  = pyqtSignal(str)          # 진행 메시지
    finished  = pyqtSignal(dict, dict)   # (result, mc)
    error     = pyqtSignal(str)

    def __init__(self, cfg: dict, mc_n: int):
        super().__init__()
        self.cfg  = cfg
        self.mc_n = mc_n

    def run(self):
        try:
            self.progress.emit("시뮬레이션 실행 중...")
            result = run_v7_simulation(self.cfg)
            self.progress.emit(f"MC {self.mc_n}회 분석 중...")
            mc = monte_carlo_v7(self.cfg, n=self.mc_n)
            self.finished.emit(result, mc)
        except Exception as e:
            self.error.emit(str(e))


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
#  전장 애니메이션 탭
# ════════════════════════════════════════════════════════════════════════════
class AnimationTab(QWidget):
    def __init__(self):
        super().__init__()
        self.frames = []
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        self.canvas = MplCanvas(figsize=(9, 8))
        layout.addWidget(self.canvas)

        ctrl = QHBoxLayout()
        self.lbl_time = QLabel("t = 0s")
        self.lbl_time.setStyleSheet(f"color:{C_ACCENT}; font-weight:bold; font-size:14px;")
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(0)
        self.slider.valueChanged.connect(self._on_slider)

        self.btn_play  = QPushButton("▶ 재생")
        self.btn_play.setFixedWidth(90)
        self.btn_play.clicked.connect(self._toggle_play)

        self.lbl_events = QLabel("")
        self.lbl_events.setStyleSheet(f"color:{C_SUBTEXT}; font-size:11px;")
        self.lbl_events.setWordWrap(True)

        ctrl.addWidget(self.lbl_time)
        ctrl.addWidget(self.slider, stretch=1)
        ctrl.addWidget(self.btn_play)
        layout.addLayout(ctrl)
        layout.addWidget(self.lbl_events)

        self._play_timer = QTimer()
        self._play_timer.timeout.connect(self._step_play)
        self._playing = False

    def load_frames(self, frames):
        self.frames = frames
        if not frames:
            return
        self.slider.setMaximum(len(frames) - 1)
        self.slider.setValue(0)
        self._draw_frame(0)

    def _toggle_play(self):
        if self._playing:
            self._play_timer.stop()
            self._playing = False
            self.btn_play.setText("▶ 재생")
        else:
            self._play_timer.start(80)
            self._playing = True
            self.btn_play.setText("⏸ 일시정지")

    def _step_play(self):
        v = self.slider.value()
        if v < self.slider.maximum():
            self.slider.setValue(v + 1)
        else:
            self._play_timer.stop()
            self._playing = False
            self.btn_play.setText("▶ 재생")

    def _on_slider(self, val):
        if self.frames:
            self._draw_frame(val)

    def _draw_frame(self, idx):
        frame = self.frames[idx]
        self.lbl_time.setText(f"t = {frame.t:.0f}s")

        fig = self.canvas.fig
        fig.clear()
        ax = fig.add_subplot(111, facecolor='#0a0e1a')
        ax.set_facecolor('#0a0e1a')
        ax.tick_params(colors='#aab', labelsize=8)
        for sp in ax.spines.values():
            sp.set_color('#1e2a3a')
        ax.set_xlim(-350_000, 350_000)
        ax.set_ylim(-350_000, 350_000)
        ax.set_xlabel('X (km)', color='#aab', fontsize=8)
        ax.set_ylabel('Y (km)', color='#aab', fontsize=8)
        ax.set_title(f'전장 상황  t = {frame.t:.0f}s', color='#dde',
                     fontsize=10, fontweight='bold')
        ax.grid(color='#1e2a3a', linewidth=0.5)
        ax.xaxis.set_major_formatter(
            plt.FuncFormatter(lambda v, _: f'{v/1000:.0f}'))
        ax.yaxis.set_major_formatter(
            plt.FuncFormatter(lambda v, _: f'{v/1000:.0f}'))

        # 아군 함정
        for sname, sx, sy, salive, shp in frame.friendly_ships:
            color = C_GREEN if salive else '#555'
            ax.scatter(sx, sy, s=160, c=color, marker='^', zorder=5)
            ax.annotate(sname, (sx, sy), xytext=(5, 5),
                        textcoords='offset points',
                        color=color, fontsize=7)

        # 적 위협
        for euid, epname, ex, ey, ealive, ehp in frame.enemy_ships:
            color = C_RED if ealive else '#555'
            ax.scatter(ex, ey, s=130, c=color, marker='v', zorder=5)
            ax.annotate(epname[:10], (ex, ey), xytext=(5, -12),
                        textcoords='offset points',
                        color=color, fontsize=7)

        # 미사일
        mtype_colors = {
            'enemy_strike':    '#ff6b6b',
            'friendly_strike': '#3498db',
            'friendly_sam':    '#2ecc71',
            'enemy_sam':       '#e67e22',
        }
        for muid, mx, my, mtype, mname in frame.missiles:
            c = mtype_colors.get(mtype, '#aaa')
            ax.scatter(mx, my, s=18, c=c, marker='o', alpha=0.85, zorder=4)

        # 범례
        legend = [
            Line2D([0],[0], marker='^', color='w', markerfacecolor=C_GREEN,
                   markersize=9, label='아군 함정'),
            Line2D([0],[0], marker='v', color='w', markerfacecolor=C_RED,
                   markersize=9, label='적 위협'),
            Line2D([0],[0], marker='o', color='w', markerfacecolor='#ff6b6b',
                   markersize=7, label='적 미사일'),
            Line2D([0],[0], marker='o', color='w', markerfacecolor=C_GREEN,
                   markersize=7, label='아군 SAM'),
            Line2D([0],[0], marker='o', color='w', markerfacecolor=C_ACCENT,
                   markersize=7, label='아군 대함'),
        ]
        ax.legend(handles=legend, loc='upper right', fontsize=7,
                  facecolor='#0a0e1a', labelcolor='white',
                  edgecolor='#1e2a3a')

        self.canvas.draw()

        events_text = '  |  '.join(frame.events[:4]) if frame.events else ''
        self.lbl_events.setText(events_text)


# ════════════════════════════════════════════════════════════════════════════
#  시스템 모니터 탭
# ════════════════════════════════════════════════════════════════════════════
class SysMonitorTab(QWidget):
    def __init__(self):
        super().__init__()
        self._build_ui()
        self._timer = QTimer()
        self._timer.timeout.connect(self._update)
        self._timer.start(1000)
        self._cpu_hist  = [0.0] * 60
        self._ram_hist  = [0.0] * 60

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 수치 레이블
        row = QHBoxLayout()
        self.lbl_cpu = self._metric_card("CPU", "0%")
        self.lbl_ram = self._metric_card("RAM", "0%")
        self.lbl_thr = self._metric_card("스레드", "0")
        self.lbl_pid = self._metric_card("PID", str(os.getpid()))
        row.addWidget(self.lbl_cpu[0])
        row.addWidget(self.lbl_ram[0])
        row.addWidget(self.lbl_thr[0])
        row.addWidget(self.lbl_pid[0])
        layout.addLayout(row)

        # 차트
        self.canvas = MplCanvas(figsize=(8, 4))
        layout.addWidget(self.canvas)
        layout.addStretch()

    def _metric_card(self, title, initial):
        card = QGroupBox(title)
        card.setFixedHeight(80)
        inner = QVBoxLayout(card)
        lbl = QLabel(initial)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setFont(QFont('Malgun Gothic', 20, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color:{C_ACCENT};")
        inner.addWidget(lbl)
        return card, lbl

    def _update(self):
        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory().percent
        thr = threading.active_count()

        self.lbl_cpu[1].setText(f"{cpu:.0f}%")
        self.lbl_ram[1].setText(f"{ram:.0f}%")
        self.lbl_thr[1].setText(str(thr))

        self._cpu_hist = self._cpu_hist[1:] + [cpu]
        self._ram_hist = self._ram_hist[1:] + [ram]

        fig = self.canvas.fig
        fig.clear()
        ax = fig.add_subplot(111, facecolor='#0a0e1a')
        ax.set_facecolor('#0a0e1a')
        ax.tick_params(colors='#aab', labelsize=8)
        for sp in ax.spines.values():
            sp.set_color('#1e2a3a')
        ax.set_ylim(0, 100)
        ax.set_xlim(0, 59)
        ax.set_xlabel('경과 (초)', color='#aab', fontsize=8)
        ax.set_ylabel('사용률 (%)', color='#aab', fontsize=8)
        ax.set_title('CPU / RAM 사용률 (최근 60초)',
                     color='#dde', fontsize=9, fontweight='bold')
        ax.grid(color='#1e2a3a', linewidth=0.5)
        ax.plot(self._cpu_hist, color=C_ACCENT, lw=1.5, label='CPU')
        ax.plot(self._ram_hist, color=C_ORANGE, lw=1.5, label='RAM')
        ax.legend(fontsize=8, facecolor='#0a0e1a', labelcolor='white',
                  edgecolor='#1e2a3a')
        self.canvas.draw()


# ════════════════════════════════════════════════════════════════════════════
#  메인 윈도우
# ════════════════════════════════════════════════════════════════════════════
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("이지스 기동전단 통합 방어 시뮬레이터  v7.0")
        self.resize(1400, 860)
        self._worker = None
        self._result = None
        self._mc     = None
        self._t0     = 0.0

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
        splitter.setSizes([380, 1020])

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

    def _build_config_panel(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedWidth(380)
        scroll.setStyleSheet(f"QScrollArea {{ border: none; background: {C_PANEL}; }}")

        inner = QWidget()
        inner.setStyleSheet(f"background: {C_PANEL};")
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(5)

        # 타이틀
        title = QLabel("⚓ 이지스 기동전단\n통합 방어 시뮬레이터")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont('Malgun Gothic', 13, QFont.Weight.Bold))
        title.setStyleSheet(f"color:{C_ACCENT}; padding: 8px 0;")
        layout.addWidget(title)

        # ── 아군 편대 ──────────────────────────────────────────────────────
        grp_f = QGroupBox("🔵 아군 편대")
        fl = QFormLayout(grp_f)
        fl.setSpacing(4)

        self.cmb_fleet   = NoScrollComboBox()
        self.cmb_fleet.addItems(list(V7_FLEET_PRESETS.keys()) if _V7_OK else [])
        self.cmb_weather = NoScrollComboBox()
        self.cmb_weather.addItems(list(WEATHER_DB.keys()) if _V7_OK else [])
        self.lbl_fleet_detail = QLabel()
        self.lbl_fleet_detail.setStyleSheet(
            f"color:{C_SUBTEXT}; font-size:11px; padding:2px 0;")
        self.lbl_fleet_detail.setWordWrap(True)
        self.cmb_fleet.currentTextChanged.connect(self._update_fleet_detail)

        self.lbl_detect_info = QLabel()
        self.lbl_detect_info.setStyleSheet(
            f"color:{C_ACCENT}; font-size:11px; padding:2px 0;")
        self.lbl_detect_info.setWordWrap(True)
        self.cmb_fleet.currentTextChanged.connect(self._update_detect_info)
        self.cmb_weather.currentTextChanged.connect(self._update_detect_info)

        fl.addRow("편대 프리셋", self.cmb_fleet)
        fl.addRow("",            self.lbl_fleet_detail)
        fl.addRow("날씨",        self.cmb_weather)
        fl.addRow("탐지 정보",   self.lbl_detect_info)
        layout.addWidget(grp_f)

        # ── 공격 무기 재고 ────────────────────────────────────────────────
        grp_w = QGroupBox("🚀 공격 무기 재고")
        wg = QGridLayout(grp_w)
        wg.setSpacing(4); wg.setContentsMargins(8, 14, 8, 6)

        self.spn_hs2 = NoScrollSpinBox(); self.spn_hs2.setRange(0, 30); self.spn_hs2.setValue(8)
        self.spn_hs1 = NoScrollSpinBox(); self.spn_hs1.setRange(0, 30); self.spn_hs1.setValue(0)
        self.spn_hp  = NoScrollSpinBox(); self.spn_hp.setRange(0, 30);  self.spn_hp.setValue(4)
        self.spn_hs2.setToolTip("해성-II 함대함 미사일\n사거리: 1,500km+ | 속도: 마하 0.9\n장거리 수상함 타격 전용 — 이지스함 VLS 탑재")
        self.spn_hs1.setToolTip("해성-I 함대함 미사일\n사거리: 180km | 속도: 마하 0.9\n단·중거리 수상함 타격")
        self.spn_hp.setToolTip("AGM-84L 하푼 Block II\n사거리: 280km | 속도: 마하 0.9\n미국제 함대함 미사일")

        _hs2_lbl = QLabel("해성-II");  _hs2_lbl.setToolTip(self.spn_hs2.toolTip())
        _hs1_lbl = QLabel("해성-I");   _hs1_lbl.setToolTip(self.spn_hs1.toolTip())
        _hp_lbl  = QLabel("하푼 B.II");_hp_lbl.setToolTip(self.spn_hp.toolTip())
        wg.addWidget(_hs2_lbl,  0, 0); wg.addWidget(self.spn_hs2, 0, 1)
        wg.addWidget(_hs1_lbl,  0, 2); wg.addWidget(self.spn_hs1, 0, 3)
        wg.addWidget(_hp_lbl,   1, 0); wg.addWidget(self.spn_hp,  1, 1)
        wg.setColumnStretch(0, 2); wg.setColumnStretch(1, 1)
        wg.setColumnStretch(2, 2); wg.setColumnStretch(3, 1)
        layout.addWidget(grp_w)

        # ── 방어 무기 재고 (포팅 A) ───────────────────────────────────────
        grp_d = QGroupBox("🛡️ 방어 무기 재고")
        dg = QGridLayout(grp_d)
        dg.setSpacing(4); dg.setContentsMargins(8, 14, 8, 6)

        def _spn(lo, hi, val):
            s = NoScrollSpinBox(); s.setRange(lo, hi); s.setValue(val)
            return s

        self.spn_sm3   = _spn(0, 60, 24);  self.spn_sm6  = _spn(0, 60, 16)
        self.spn_sm2   = _spn(0, 90, 32);  self.spn_ram  = _spn(0, 30, 21)
        self.spn_hong  = _spn(0, 20, 3);   self.spn_chng = _spn(0, 20, 4)
        self.spn_mk46  = _spn(0, 30, 6);   self.spn_dcoy = _spn(0, 20, 4)

        _tips = {
            self.spn_sm3:  ("SM-3 IIA",  "RIM-161 SM-3 Block IIA\n사거리: 2,500km | 요격 고도: 500km+\nBMD 전용 — 탄도미사일·극초음속체 요격"),
            self.spn_sm6:  ("SM-6",      "RIM-174 SM-6\n사거리: 370km | 다목적 미사일\n대공·탄도·순항미사일·대함 요격 가능"),
            self.spn_sm2:  ("SM-2 IIIB", "RIM-66 SM-2 Block IIIB\n사거리: 167km | 주력 대공\n중·고고도 항공기·순항미사일 요격"),
            self.spn_ram:  ("RAM-116",   "RIM-116 RAM (Rolling Airframe Missile)\n사거리: 9km | 최후방어선\nCIWS 보완 근거리 대공 — 포화공격 대응"),
            self.spn_hong: ("홍상어",    "홍상어 경어뢰 (K745)\n사거리: 19km | 수상함 투하\n한국형 중경어뢰 — 수상함 대잠 전용"),
            self.spn_chng: ("청상어",    "청상어 경어뢰 (K-745LW)\n사거리: 19km | 항공기·수상함 투하\n한국형 경어뢰 — 헬기·함정 공용"),
            self.spn_mk46: ("Mk.46",     "Mk.46 Mod 5 경어뢰\n사거리: 11km | 항공기 투하\n미국제 경어뢰 — P-3C·P-8A 탑재"),
            self.spn_dcoy: ("기만기",    "AN/SLQ-25 Nixie 음향 기만기\n어뢰 유도 신호 교란\n탐지된 어뢰에 대해 60% 기만 효과"),
        }
        for i, (spn, (lbl_txt, tip)) in enumerate(_tips.items()):
            r, c = divmod(i, 2)
            spn.setToolTip(tip)
            lbl_w = QLabel(lbl_txt); lbl_w.setToolTip(tip)
            dg.addWidget(lbl_w, r, c*2)
            dg.addWidget(spn,   r, c*2+1)
        dg.setColumnStretch(0, 2); dg.setColumnStretch(1, 1)
        dg.setColumnStretch(2, 2); dg.setColumnStretch(3, 1)
        layout.addWidget(grp_d)

        # ── 적군 편대 (포팅 A) ────────────────────────────────────────────
        grp_e = QGroupBox("🔴 적군 편대")
        el = QVBoxLayout(grp_e)
        el.setSpacing(4)

        # 모드 선택
        mode_row = QWidget(); mode_rl = QHBoxLayout(mode_row)
        mode_rl.setContentsMargins(0, 0, 0, 0)
        mode_rl.addWidget(QLabel("모드:"))
        self.cmb_enemy_mode = NoScrollComboBox()
        self.cmb_enemy_mode.addItems(['커스텀', '프리셋', '랜덤'])
        mode_rl.addWidget(self.cmb_enemy_mode, stretch=1)
        el.addWidget(mode_row)

        # 프리셋 선택 (프리셋 모드용)
        self.cmb_fleet_preset_e = NoScrollComboBox()
        self.cmb_fleet_preset_e.addItems(list(V7_ENEMY_FLEET_PRESETS.keys()) if _V7_OK else [])
        self.cmb_fleet_preset_e.currentTextChanged.connect(self._update_enemy_preset_detail)
        el.addWidget(self.cmb_fleet_preset_e)

        self.lbl_enemy_preset_detail = QLabel()
        self.lbl_enemy_preset_detail.setStyleSheet(
            f"color:{C_SUBTEXT}; font-size:11px; padding:2px 0;")
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

        # 커스텀 5행
        self._enemy_rows = []
        self._enemy_row_widgets = []
        for i in range(5):
            row_w = QWidget(); row_l = QHBoxLayout(row_w)
            row_l.setContentsMargins(0, 0, 0, 0); row_l.setSpacing(4)
            cmb = NoScrollComboBox()
            if _V7_OK: cmb.addItems(list(V7_ENEMY_DB.keys()))
            cmb.currentTextChanged.connect(lambda name, c=cmb: self._update_enemy_row_tooltip(c, name))
            spn = NoScrollSpinBox(); spn.setRange(0, 8); spn.setValue(1 if i < 3 else 0)
            row_l.addWidget(cmb, stretch=3); row_l.addWidget(spn, stretch=1)
            el.addWidget(row_w)
            self._enemy_rows.append((cmb, spn))
            self._enemy_row_widgets.append(row_w)

        if _V7_OK:
            defaults = ['055형 대형 구축함', 'J-20 (위룡)',
                        'DF-21D (대함 탄도)', '052D형 구축함',
                        '095형 잠수함 (차세대 SSN)']
            keys = list(V7_ENEMY_DB.keys())
            for i, name in enumerate(defaults):
                if name in keys:
                    self._enemy_rows[i][0].setCurrentText(name)

        self.cmb_enemy_mode.currentIndexChanged.connect(self._on_enemy_mode_changed)
        self._on_enemy_mode_changed(0)  # 초기 상태 적용
        # 초기 툴팁 세팅
        if _V7_OK:
            for cmb, _ in self._enemy_rows:
                self._update_enemy_row_tooltip(cmb, cmb.currentText())
            if self.cmb_fleet_preset_e.count():
                self._update_enemy_preset_detail(self.cmb_fleet_preset_e.currentText())
            if self.cmb_difficulty.count():
                self._update_difficulty_tooltip(self.cmb_difficulty.currentText())
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
            chk.setStyleSheet(f"color:{C_TEXT}; font-size:12px;")
            tl.addWidget(chk)

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
            chk.setStyleSheet(f"color:{C_TEXT}; font-size:12px;")
            acl.addWidget(chk)

        layout.addWidget(grp_ac)

        # ── 방어 전술 옵션 ─────────────────────────────────────────────────
        grp_def = QGroupBox("🛡️ 방어 전술")
        defl = QVBoxLayout(grp_def)
        defl.setSpacing(4)

        self.chk_layered = QCheckBox("다층 방어  (KDX-III → KDX-II → FFX 순서)")
        self.chk_layered.setChecked(True)
        self.chk_layered.setToolTip(
            "1차 교전 함정(KDX-III)이 요격 실패 시 다음 레이어(KDX-II→FFX)가 자동 인계.\n"
            "우선순위 정렬로 최고 성능 함정이 항상 먼저 교전합니다."
        )

        self.chk_cec = QCheckBox("CEC 사전 동시 배정  (1차+2차 함정 동시 발사)")
        self.chk_cec.setChecked(False)
        self.chk_cec.setToolTip(
            "위협 탐지 시 1차(KDX-III)+2차(KDX-II) 함정이 동시에 SAM을 발사합니다.\n"
            "1차 성공 시 2차 SAM은 표적 소멸로 자동 종료.\n"
            "탄약 소비 증가 / 동시 다수 위협에 효과적."
        )

        self.chk_multibearing = QCheckBox("다방위 공격  (여러 방향에서 동시 접근)")
        self.chk_multibearing.setChecked(False)
        self.chk_multibearing.setToolTip(
            "적 위협이 전방위(0°~360°) 무작위 방향에서 접근합니다.\n"
            "OFF 시 기본 단일 방향 접근."
        )

        for chk in [self.chk_layered, self.chk_cec, self.chk_multibearing]:
            chk.setStyleSheet(f"color:{C_TEXT}; font-size:12px;")
            defl.addWidget(chk)

        # 시뮬 시드
        seed_row = QHBoxLayout()
        lbl_seed = QLabel("시뮬 시드  (0=랜덤)")
        lbl_seed.setStyleSheet(f"color:{C_SUBTEXT}; font-size:11px;")
        self.spn_sim_seed = NoScrollSpinBox()
        self.spn_sim_seed.setRange(0, 99999)
        self.spn_sim_seed.setValue(0)
        self.spn_sim_seed.setFixedWidth(80)
        seed_row.addWidget(lbl_seed)
        seed_row.addStretch()
        seed_row.addWidget(self.spn_sim_seed)
        defl.addLayout(seed_row)

        layout.addWidget(grp_def)

        # ── C&D 시간 설정 ──────────────────────────────────────────────────
        grp_cd = QGroupBox("⏱️ C&D 시간 설정")
        cdl = QVBoxLayout(grp_cd)
        cdl.setSpacing(6)

        # cd_time_s
        cd_row1 = QHBoxLayout()
        lbl_cd_name = QLabel("C&D 시간 (초)")
        lbl_cd_name.setStyleSheet(f"color:{C_SUBTEXT}; font-size:11px;")
        self.lbl_cd_val = QLabel("10s")
        self.lbl_cd_val.setStyleSheet(f"color:{C_ACCENT}; font-size:11px; font-weight:bold;")
        self.lbl_cd_val.setFixedWidth(32)
        cd_row1.addWidget(lbl_cd_name)
        cd_row1.addStretch()
        cd_row1.addWidget(self.lbl_cd_val)
        self.sld_cd = QSlider(Qt.Orientation.Horizontal)
        self.sld_cd.setRange(0, 60)
        self.sld_cd.setValue(10)
        self.sld_cd.setTickInterval(5)
        self.sld_cd.setToolTip(
            "Command & Decision 시간 (초)\n"
            "위협 탐지 후 발사 명령까지 소요 시간.\n"
            "클수록 첫 SAM 발사가 늦어집니다."
        )
        self.sld_cd.valueChanged.connect(lambda v: self.lbl_cd_val.setText(f"{v}s"))
        cdl.addLayout(cd_row1)
        cdl.addWidget(self.sld_cd)

        # confirm_time_s
        cd_row2 = QHBoxLayout()
        lbl_cf_name = QLabel("확인 시간 (초)")
        lbl_cf_name.setStyleSheet(f"color:{C_SUBTEXT}; font-size:11px;")
        self.lbl_cf_val = QLabel("3s")
        self.lbl_cf_val.setStyleSheet(f"color:{C_ACCENT}; font-size:11px; font-weight:bold;")
        self.lbl_cf_val.setFixedWidth(32)
        cd_row2.addWidget(lbl_cf_name)
        cd_row2.addStretch()
        cd_row2.addWidget(self.lbl_cf_val)
        self.sld_confirm = QSlider(Qt.Orientation.Horizontal)
        self.sld_confirm.setRange(0, 20)
        self.sld_confirm.setValue(3)
        self.sld_confirm.setTickInterval(1)
        self.sld_confirm.setToolTip(
            "교전 확인(IFF 식별) 시간 (초)\n"
            "피아식별 절차 소요 시간. 클수록 반응이 늦어집니다."
        )
        self.sld_confirm.valueChanged.connect(lambda v: self.lbl_cf_val.setText(f"{v}s"))
        cdl.addLayout(cd_row2)
        cdl.addWidget(self.sld_confirm)

        layout.addWidget(grp_cd)

        # ── MC 설정 ────────────────────────────────────────────────────────
        grp_mc = QGroupBox("📊 몬테카를로")
        mcl = QFormLayout(grp_mc)
        self.spn_mc_n = NoScrollSpinBox()
        self.spn_mc_n.setRange(50, 2000)
        self.spn_mc_n.setValue(200)
        self.spn_mc_n.setSingleStep(50)
        mcl.addRow("반복 횟수", self.spn_mc_n)
        layout.addWidget(grp_mc)

        # ── 시나리오 저장/불러오기 (포팅 D) ──────────────────────────────────
        grp_sc = QGroupBox("💾 시나리오")
        scl = QHBoxLayout(grp_sc)
        scl.setSpacing(6)
        btn_save = QPushButton("저장")
        btn_load = QPushButton("불러오기")
        btn_save_a = QPushButton("A로 저장")
        btn_save_b = QPushButton("B로 저장")
        for b in [btn_save, btn_load, btn_save_a, btn_save_b]:
            b.setFixedHeight(28)
            b.setStyleSheet(f"background:{C_PANEL}; color:{C_TEXT}; border:1px solid #3a5a7a; font-size:11px;")
            scl.addWidget(b)
        btn_save.clicked.connect(self._save_scenario)
        btn_load.clicked.connect(self._load_scenario)
        btn_save_a.clicked.connect(lambda: self._save_ab('A'))
        btn_save_b.clicked.connect(lambda: self._save_ab('B'))
        layout.addWidget(grp_sc)

        # ── 실행 버튼 ─────────────────────────────────────────────────────
        self.btn_run = QPushButton("🚀  시뮬레이션 실행")
        self.btn_run.setFixedHeight(44)
        self.btn_run.clicked.connect(self._run_sim)
        layout.addWidget(self.btn_run)

        if not _V7_OK:
            err_lbl = QLabel(f"⚠️ engine_v7 로드 실패\n{_V7_ERR}")
            err_lbl.setStyleSheet(f"color:{C_RED}; font-size:11px;")
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

        # 탭
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.tab_anim = AnimationTab()
        self.tabs.addTab(self.tab_anim,     "🗺️  전장 애니메이션")

        self.tab_mc_canvas = MplCanvas(figsize=(12, 7))
        self.tabs.addTab(self.tab_mc_canvas, "📊  MC 통계")

        self.tab_req = self._build_req_tab()
        self.tabs.addTab(self.tab_req,       "✅  REQ 판정")

        self.tab_weather = self._build_weather_tab()
        self.tabs.addTab(self.tab_weather,   "🌤️  날씨 비교")

        self.tab_ab = self._build_ab_tab()
        self.tabs.addTab(self.tab_ab,        "🆚  A vs B")

        self.tab_log = self._build_log_tab()
        self.tabs.addTab(self.tab_log,       "📜  교전 로그")

        self.tab_tactical = MplCanvas(figsize=(12, 6))
        self.tabs.addTab(self.tab_tactical,  "📐  전술교전도")

        self.tab_topdown = MplCanvas(figsize=(12, 7))
        self.tabs.addTab(self.tab_topdown,   "🌐  Top-down 교전도")

        self.tab_channel = MplCanvas(figsize=(12, 5))
        self.tabs.addTab(self.tab_channel,   "📡  채널 포화도")

        self.tab_sysmon = SysMonitorTab()
        self.tabs.addTab(self.tab_sysmon,    "🖥️  시스템 모니터")

        return panel

    def _build_req_tab(self) -> QWidget:
        """포팅 D: REQ 판정 결과 테이블."""
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
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
        layout.addWidget(QLabel("  ※ 시뮬레이션 실행 후 결과가 표시됩니다."))
        layout.addWidget(self.req_table)
        return w

    def _build_weather_tab(self) -> QWidget:
        """포팅 D: 날씨별 3종 비교 탭."""
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)

        btn_row = QWidget()
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        self.btn_weather_run = QPushButton("🌤️  날씨별 비교 실행 (각 200회 MC)")
        self.btn_weather_run.setFixedHeight(36)
        self.btn_weather_run.clicked.connect(self._run_weather_compare)
        btn_layout.addWidget(self.btn_weather_run)
        btn_layout.addStretch()
        layout.addWidget(btn_row)

        self.weather_table = QTableWidget(0, 4)
        self.weather_table.setHorizontalHeaderLabels(
            ["날씨 시나리오", "평균 요격률", "완전 성공률", "평균 비용 ($)"])
        hh = self.weather_table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in [1, 2, 3]:
            self.weather_table.setColumnWidth(col, 120)
        self.weather_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.weather_table.setAlternatingRowColors(True)
        self.weather_table.setStyleSheet(
            f"alternate-background-color: {C_PANEL}; background-color: {C_BG};")
        layout.addWidget(self.weather_table)
        return w

    def _build_ab_tab(self) -> QWidget:
        """포팅 D: A vs B 시나리오 비교 탭."""
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)

        self._cfg_a: dict = {}
        self._cfg_b: dict = {}

        info_row = QWidget()
        info_layout = QHBoxLayout(info_row)
        info_layout.setContentsMargins(0, 0, 0, 0)
        self.lbl_ab_a = QLabel("A: 미설정")
        self.lbl_ab_b = QLabel("B: 미설정")
        for lbl in [self.lbl_ab_a, self.lbl_ab_b]:
            lbl.setStyleSheet(f"color:{C_TEXT}; font-size:12px; padding:4px;")
        info_layout.addWidget(self.lbl_ab_a)
        info_layout.addStretch()
        info_layout.addWidget(self.lbl_ab_b)
        layout.addWidget(info_row)

        self.btn_ab_run = QPushButton("🆚  A vs B 비교 실행 (각 200회 MC)")
        self.btn_ab_run.setFixedHeight(36)
        self.btn_ab_run.clicked.connect(self._run_ab_compare)
        layout.addWidget(self.btn_ab_run)

        self.ab_table = QTableWidget(0, 3)
        self.ab_table.setHorizontalHeaderLabels(["항목", "시나리오 A", "시나리오 B"])
        hh = self.ab_table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        for col in [1, 2]:
            self.ab_table.setColumnWidth(col, 150)
        self.ab_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.ab_table.setAlternatingRowColors(True)
        self.ab_table.setStyleSheet(
            f"alternate-background-color: {C_PANEL}; background-color: {C_BG};")
        layout.addWidget(self.ab_table)
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
        'KDX-III': '이지스 구축함 (KDX-III)',
        'KDX-II':  '구축함 (KDX-II 충무공이순신급)',
        'FFX':     '호위함 (FFX 인천급/대구급)',
    }

    def _update_fleet_detail(self, preset_name: str):
        if not _V7_OK or preset_name not in V7_FLEET_PRESETS:
            self.lbl_fleet_detail.setText('')
            return
        lines = []
        for s in V7_FLEET_PRESETS[preset_name]:
            disp = self._SHIP_DISPLAY.get(s['type'], s['type'])
            lines.append(f"• {s['name']}  ({disp})")
        self.lbl_fleet_detail.setText('\n'.join(lines))

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
        tip_lines = [f"【{preset_name}】"]
        for e in units:
            name = e['preset']; cnt = e['count']
            label_lines.append(f"• {name}  ×{cnt}")
            if name in V7_ENEMY_DB:
                d = V7_ENEMY_DB[name]
                mach = d['speed_ms'] / 340
                tip_line = (f"  {d.get('type','')} | 마하 {mach:.1f}"
                            + (f" | 미사일 {d['missile_range_km']}km"
                               if d.get('missile_range_km') else ''))
                tip_lines.append(f"• {name} ×{cnt}")
                tip_lines.append(tip_line)
        self.lbl_enemy_preset_detail.setText('\n'.join(label_lines))
        self.cmb_fleet_preset_e.setToolTip('\n'.join(tip_lines))

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
        self.cmb_fleet_preset_e.setVisible(is_preset)
        self.lbl_enemy_preset_detail.setVisible(is_preset)
        self._rand_row.setVisible(mode == '랜덤')
        for w in self._enemy_row_widgets:
            w.setVisible(mode == '커스텀')
        if is_preset and self.cmb_fleet_preset_e.count():
            self._update_enemy_preset_detail(self.cmb_fleet_preset_e.currentText())

    def _apply_style(self):
        self.setStyleSheet(STYLE_MAIN)

    # ── 시뮬 실행 ────────────────────────────────────────────────────────────

    def _run_sim(self):
        # 적군 모드 및 편대 구성 (포팅 A)
        mode_label = self.cmb_enemy_mode.currentText()
        mode_map   = {'커스텀': 'custom', '프리셋': 'preset', '랜덤': 'random'}
        enemy_mode = mode_map.get(mode_label, 'custom')

        enemy_fleet = []
        if enemy_mode == 'custom':
            for cmb, spn in self._enemy_rows:
                cnt = spn.value()
                if cnt > 0 and _V7_OK and cmb.currentText() in V7_ENEMY_DB:
                    enemy_fleet.append({'preset': cmb.currentText(), 'count': cnt})
            if not enemy_fleet:
                QMessageBox.warning(self, "설정 오류", "커스텀 모드에서 수량을 1 이상 설정하세요.")
                return

        cfg = {
            # 아군 편대 (탐지거리는 엔진이 함대+날씨로 자동 계산)
            'fleet_preset':      self.cmb_fleet.currentText(),
            'weather':           self.cmb_weather.currentText(),
            'detect_km_manual':  False,
            # 공격 무기
            'haesong2_stock': self.spn_hs2.value(),
            'haesong1_stock': self.spn_hs1.value(),
            'harpoon_stock':  self.spn_hp.value(),
            # 방어 무기 (포팅 A)
            'sm3_stock':          self.spn_sm3.value(),
            'sm6_stock':          self.spn_sm6.value(),
            'sm2_stock':          self.spn_sm2.value(),
            'ram_stock':          self.spn_ram.value(),
            'hongsango_stock':    self.spn_hong.value(),
            'cheongsango_stock':  self.spn_chng.value(),
            'mk46_stock':         self.spn_mk46.value(),
            'decoy_stock':        self.spn_dcoy.value(),
            # 적군 (포팅 A)
            'enemy_fleet_mode':       enemy_mode,
            'enemy_fleet':            enemy_fleet,
            'enemy_fleet_preset':     self.cmb_fleet_preset_e.currentText(),
            'enemy_fleet_difficulty': self.cmb_difficulty.currentText(),
            'enemy_fleet_seed':       self.spn_seed.value() or None,
            # 전술 옵션 (포팅 B)
            'enable_ecm':         self.chk_ecm.isChecked(),
            'enable_evasion':     self.chk_eva.isChecked(),
            'enable_decoy':       self.chk_dcoy.isChecked(),
            'enable_selfdefense': self.chk_sd.isChecked(),
            # 항공 자산 (포팅 C)
            'enable_helo': self.chk_helo.isChecked(),
            'enable_p3c':  self.chk_p3c.isChecked(),
            'enable_p8a':  self.chk_p8a.isChecked(),
            # 방어 전술 (다층 방어 / CEC / 다방위)
            'enable_layered_defense': self.chk_layered.isChecked(),
            'enable_cec_preassign':   self.chk_cec.isChecked(),
            'enable_multibearing':    self.chk_multibearing.isChecked(),
            'sim_seed':               self.spn_sim_seed.value() or None,
            # C&D 시간
            'cd_time_s':      self.sld_cd.value(),
            'confirm_time_s': self.sld_confirm.value(),
        }
        mc_n = self.spn_mc_n.value()

        self.btn_run.setEnabled(False)
        self._prog.setVisible(True)
        self._t0 = time.time()
        self._lbl_status.setText("실행 중...")

        self._worker = SimWorker(cfg, mc_n)
        self._worker.progress.connect(self._on_progress)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_progress(self, msg: str):
        self._lbl_status.setText(msg)

    def _on_finished(self, result: dict, mc: dict):
        elapsed = time.time() - self._t0
        self._result = result
        self._mc     = mc

        self.btn_run.setEnabled(True)
        self._prog.setVisible(False)
        self._lbl_status.setText(
            f"완료 ({elapsed:.1f}s) | "
            f"요격률 {mc['mean_intercept']:.1%} | "
            f"MC {mc['n']}회")

        self._update_cards(result, mc)
        self.tab_anim.load_frames(result.get('frames', []))
        self._draw_mc_chart(result, mc,
                            self._worker.cfg if self._worker else {})
        self._fill_req(result, mc)
        self._fill_log(result.get('log', []))
        self._draw_tactical(result)
        self._draw_topdown(result)
        self._draw_channel_heatmap(result)

        self.tabs.setCurrentIndex(0)

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

    def _run_weather_compare(self):
        """포팅 D: 날씨별 3종 비교 실행."""
        if not _V7_OK or not hasattr(self, '_result'):
            QMessageBox.information(self, "안내", "먼저 시뮬레이션을 실행하세요.")
            return
        cfg = self._worker.cfg if self._worker else {}
        if not cfg:
            return
        self.btn_weather_run.setEnabled(False)
        self.btn_weather_run.setText("실행 중...")
        QApplication.processEvents()
        try:
            sc = scenario_comparison_v7(cfg, n=200)
        except Exception as e:
            QMessageBox.critical(self, "오류", str(e))
            self.btn_weather_run.setEnabled(True)
            self.btn_weather_run.setText("🌤️  날씨별 비교 실행 (각 200회 MC)")
            return
        self.weather_table.setRowCount(0)
        for label, res in sc.items():
            row = self.weather_table.rowCount()
            self.weather_table.insertRow(row)
            values = [label,
                      f"{res['mean_intercept']:.1%}",
                      f"{res['full_pass_rate']:.1%}",
                      f"${res['mean_cost']:,.0f}"]
            for col, text in enumerate(values):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if col == 1:
                    item.setForeground(
                        QColor('#2ecc71' if res['mean_intercept'] >= 0.9 else '#e74c3c'))
                self.weather_table.setItem(row, col, item)
        self.btn_weather_run.setEnabled(True)
        self.btn_weather_run.setText("🌤️  날씨별 비교 실행 (각 200회 MC)")
        self.tabs.setCurrentWidget(self.tab_weather)

    def _run_ab_compare(self):
        """포팅 D: A vs B 비교 실행."""
        if not _V7_OK:
            return
        if not self._cfg_a or not self._cfg_b:
            QMessageBox.information(self, "안내",
                                    "설정 패널에서 'A로 저장'과 'B로 저장'을 먼저 눌러주세요.")
            return
        self.btn_ab_run.setEnabled(False)
        self.btn_ab_run.setText("실행 중...")
        QApplication.processEvents()
        try:
            ab = compare_ab_v7(self._cfg_a, self._cfg_b, n=200)
        except Exception as e:
            QMessageBox.critical(self, "오류", str(e))
            self.btn_ab_run.setEnabled(True)
            self.btn_ab_run.setText("🆚  A vs B 비교 실행 (각 200회 MC)")
            return
        mc_a, mc_b = ab['a'], ab['b']
        self.ab_table.setRowCount(0)
        rows = [
            ("평균 요격률",    f"{mc_a['mean_intercept']:.1%}", f"{mc_b['mean_intercept']:.1%}"),
            ("완전 성공률",    f"{mc_a['full_pass_rate']:.1%}", f"{mc_b['full_pass_rate']:.1%}"),
            ("평균 비용 ($)",  f"${sum(mc_a['total_costs'])/len(mc_a['total_costs']):,.0f}",
                               f"${sum(mc_b['total_costs'])/len(mc_b['total_costs']):,.0f}"),
            ("Δ 요격률",       "—", f"{ab['delta_intercept']:+.1%}"),
            ("Δ 비용 ($)",     "—", f"${ab['delta_cost']:+,.0f}"),
        ]
        for label, val_a, val_b in rows:
            row = self.ab_table.rowCount()
            self.ab_table.insertRow(row)
            for col, text in enumerate([label, val_a, val_b]):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.ab_table.setItem(row, col, item)
        self.btn_ab_run.setEnabled(True)
        self.btn_ab_run.setText("🆚  A vs B 비교 실행 (각 200회 MC)")
        self.tabs.setCurrentWidget(self.tab_ab)

    def _save_scenario(self):
        """포팅 D: 현재 설정을 JSON으로 저장."""
        if not _V7_OK:
            return
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getSaveFileName(
            self, "시나리오 저장", "scenario.json", "JSON (*.json)")
        if not path:
            return
        cfg = self._worker.cfg if (self._worker and hasattr(self._worker, 'cfg')) else {}
        if not cfg:
            QMessageBox.information(self, "안내", "먼저 시뮬레이션을 실행하세요.")
            return
        save_scenario_v7(cfg, path)
        QMessageBox.information(self, "저장 완료", f"저장됨: {path}")

    def _load_scenario(self):
        """포팅 D: JSON에서 설정 불러오기 (알림만, 실제 UI 반영은 수동)."""
        if not _V7_OK:
            return
        from PyQt6.QtWidgets import QFileDialog
        path, _ = QFileDialog.getOpenFileName(
            self, "시나리오 불러오기", "", "JSON (*.json)")
        if not path:
            return
        try:
            cfg = load_scenario_v7(path)
            QMessageBox.information(
                self, "불러오기 완료",
                f"불러온 시나리오: {path}\n\n"
                "※ UI 수동 설정이 필요합니다.\n"
                f"날씨: {cfg.get('weather','—')} | MC: {cfg.get('mc_n','—')}회")
        except Exception as e:
            QMessageBox.critical(self, "오류", str(e))

    def _save_ab(self, slot: str):
        """포팅 D: 현재 cfg를 A 또는 B 슬롯에 저장."""
        cfg = self._worker.cfg if (self._worker and hasattr(self._worker, 'cfg')) else {}
        if not cfg:
            QMessageBox.information(self, "안내", "먼저 시뮬레이션을 실행하세요.")
            return
        if slot == 'A':
            self._cfg_a = dict(cfg)
            self.lbl_ab_a.setText(
                f"A: {cfg.get('weather','—')} | {cfg.get('enemy_fleet_mode','—')}")
        else:
            self._cfg_b = dict(cfg)
            self.lbl_ab_b.setText(
                f"B: {cfg.get('weather','—')} | {cfg.get('enemy_fleet_mode','—')}")
        self.tabs.setCurrentWidget(self.tab_ab)

    def _on_error(self, msg: str):
        self.btn_run.setEnabled(True)
        self._prog.setVisible(False)
        self._lbl_status.setText("오류 발생")
        QMessageBox.critical(self, "시뮬레이션 오류", msg)

    # ── 결과 렌더링 ──────────────────────────────────────────────────────────

    def _update_cards(self, result: dict, mc: dict):
        self._cards['intercept'].setText(f"{mc['mean_intercept']:.1%}")
        self._cards['intercept'].setStyleSheet(
            f"color:{'#2ecc71' if mc['mean_intercept'] >= 0.9 else '#e74c3c'};")
        self._cards['full_pass'].setText(f"{mc['full_pass_rate']:.1%}")
        self._cards['friendly_hit'].setText(str(result['friendly_hits']))
        self._cards['friendly_hit'].setStyleSheet(
            f"color:{'#2ecc71' if result['friendly_hits'] == 0 else '#e74c3c'};")
        self._cards['enemy_dest'].setText(str(result['enemy_ships_destroyed']))
        self._cards['cost'].setText(f"${result['total_cost']:,.0f}")
        sorties = result.get('aircraft_sorties', 0)
        self._cards['aircraft'].setText(f"{sorties}회" if sorties else "—")

    def _draw_mc_chart(self, result: dict, mc: dict, cfg: dict):
        img_path = '_launcher_mc_tmp.png'
        plot_v7(result, mc, cfg, img_path=img_path)

        fig = self.tab_mc_canvas.fig
        fig.clear()

        if os.path.exists(img_path):
            from matplotlib.image import imread
            img = imread(img_path)
            ax = fig.add_subplot(111)
            ax.imshow(img)
            ax.axis('off')
            fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

        self.tab_mc_canvas.draw()

    def _fill_log(self, log: list):
        self.log_table.setRowCount(0)
        for t, msg in log:
            row = self.log_table.rowCount()
            self.log_table.insertRow(row)
            t_item = QTableWidgetItem(f"{t:.0f}s")
            t_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.log_table.setItem(row, 0, t_item)
            self.log_table.setItem(row, 1, QTableWidgetItem(msg))

    def _draw_tactical(self, result: dict):
        """전술교전도 (Janes 式 측면도): X=시간(s), Y=함대 거리(km)."""
        frames = result.get('frames', [])
        if not frames:
            return
        fig = self.tab_tactical.fig
        fig.clear()
        fig.patch.set_facecolor(C_BG)
        ax = fig.add_subplot(111, facecolor='#0a0e1a')
        ax.tick_params(colors='#aab', labelsize=8)
        for sp in ax.spines.values():
            sp.set_color('#1e2a3a')
        ax.set_xlabel('시간 (s)', color='#aab', fontsize=9)
        ax.set_ylabel('거리 (km)', color='#aab', fontsize=9)
        ax.set_title('전술교전도 (측면도)', color='#dde', fontsize=11, fontweight='bold')
        ax.grid(color='#1e2a3a', linewidth=0.5, alpha=0.7)

        # 아군 함대 중심점
        px0 = np.mean([s[1] for s in frames[0].friendly_ships]) if frames[0].friendly_ships else 0
        py0 = np.mean([s[2] for s in frames[0].friendly_ships]) if frames[0].friendly_ships else 0

        enemy_tracks  = {}
        missile_tracks = {}
        for frame in frames:
            t = frame.t
            for uid, epname, ex, ey, ealive, ehp in frame.enemy_ships:
                dist = ((ex - px0)**2 + (ey - py0)**2)**0.5 / 1000
                if uid not in enemy_tracks:
                    enemy_tracks[uid] = {'name': epname, 'pts': []}
                enemy_tracks[uid]['pts'].append((t, dist))
            for uid, mx, my, mtype, mname in frame.missiles:
                dist = ((mx - px0)**2 + (my - py0)**2)**0.5 / 1000
                if uid not in missile_tracks:
                    missile_tracks[uid] = {'mtype': mtype, 'pts': []}
                missile_tracks[uid]['pts'].append((t, dist))

        seen_names = set()
        for uid, info in enemy_tracks.items():
            pts = info['pts']
            if len(pts) < 2:
                continue
            ts = [p[0] for p in pts]
            ds = [p[1] for p in pts]
            lbl = info['name'] if info['name'] not in seen_names else None
            ax.plot(ts, ds, color='#e74c3c', linewidth=1.5, alpha=0.85, label=lbl)
            if lbl:
                seen_names.add(info['name'])

        for uid, info in missile_tracks.items():
            pts = info['pts']
            if len(pts) < 2:
                continue
            ts = [p[0] for p in pts]
            ds = [p[1] for p in pts]
            if info['mtype'] == 'friendly_sam':
                ax.plot(ts, ds, color='#2ecc71', linewidth=0.9, alpha=0.6, linestyle='--')
            elif info['mtype'] == 'enemy_strike':
                ax.plot(ts, ds, color='#f39c12', linewidth=0.9, alpha=0.6, linestyle=':')

        ax.axhline(0, color='#3498db', linewidth=1.5, alpha=0.5)
        handles = [
            Line2D([0],[0], color='#e74c3c', lw=1.5, label='적 위협'),
            Line2D([0],[0], color='#f39c12', lw=1, ls=':', label='적 미사일'),
            Line2D([0],[0], color='#2ecc71', lw=1, ls='--', label='아군 SAM'),
            Line2D([0],[0], color='#3498db', lw=1.5, label='아군 함대(Y=0)'),
        ]
        ax.legend(handles=handles, loc='upper right', fontsize=8,
                  facecolor='#0a0e1a', labelcolor='white', edgecolor='#1e2a3a')
        fig.tight_layout()
        self.tab_tactical.draw()

    def _draw_topdown(self, result: dict):
        """Top-down 2D 교전도: 전체 전투 미사일 궤적 정적 플롯."""
        frames = result.get('frames', [])
        if not frames:
            return
        fig = self.tab_topdown.fig
        fig.clear()
        fig.patch.set_facecolor(C_BG)
        ax = fig.add_subplot(111, facecolor='#0a0e1a')
        ax.tick_params(colors='#aab', labelsize=8)
        for sp in ax.spines.values():
            sp.set_color('#1e2a3a')
        ax.set_xlabel('X (km)', color='#aab', fontsize=9)
        ax.set_ylabel('Y (km)', color='#aab', fontsize=9)
        ax.set_title('Top-down 교전도 (전체 궤적)', color='#dde', fontsize=11, fontweight='bold')
        ax.grid(color='#1e2a3a', linewidth=0.5, alpha=0.7)
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{v/1000:.0f}'))
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f'{v/1000:.0f}'))

        traj = {}
        for frame in frames:
            for uid, mx, my, mtype, mname in frame.missiles:
                if uid not in traj:
                    traj[uid] = {'mtype': mtype, 'xs': [], 'ys': []}
                traj[uid]['xs'].append(mx)
                traj[uid]['ys'].append(my)

        mtype_color = {
            'enemy_strike':    '#ff6b6b',
            'friendly_strike': '#3498db',
            'friendly_sam':    '#2ecc71',
            'enemy_sam':       '#e67e22',
        }
        plotted = set()
        for uid, info in traj.items():
            c = mtype_color.get(info['mtype'], '#aaa')
            lbl = info['mtype'] if info['mtype'] not in plotted else None
            ax.plot(info['xs'], info['ys'], color=c, linewidth=0.8, alpha=0.55, label=lbl)
            if info['xs']:
                ax.scatter(info['xs'][-1], info['ys'][-1], s=8, c=c, zorder=4)
            if lbl:
                plotted.add(info['mtype'])

        # 아군 함정 최종 위치
        for sname, sx, sy, salive, shp in frames[-1].friendly_ships:
            c = '#2ecc71' if salive else '#555555'
            ax.scatter(sx, sy, s=180, c=c, marker='^', zorder=6)
            ax.annotate(sname, (sx, sy), xytext=(5, 5),
                        textcoords='offset points', color=c, fontsize=7)

        handles = [
            Line2D([0],[0], color='#ff6b6b', lw=1.5, label='적 미사일'),
            Line2D([0],[0], color='#2ecc71', lw=1.5, label='아군 SAM'),
            Line2D([0],[0], color='#3498db', lw=1.5, label='아군 대함'),
            Line2D([0],[0], color='#e67e22', lw=1.5, label='적 SAM'),
            Line2D([0],[0], marker='^', color='w', markerfacecolor='#2ecc71',
                   markersize=8, label='아군 함정'),
        ]
        ax.legend(handles=handles, loc='upper right', fontsize=8,
                  facecolor='#0a0e1a', labelcolor='white', edgecolor='#1e2a3a')
        fig.tight_layout()
        self.tab_topdown.draw()

    def _draw_channel_heatmap(self, result: dict):
        """채널 포화도 히트맵: 함정별 채널 사용률 시계열."""
        frames = result.get('frames', [])
        if not frames or not getattr(frames[0], 'ship_channels', None):
            fig = self.tab_channel.fig
            fig.clear()
            fig.patch.set_facecolor(C_BG)
            ax = fig.add_subplot(111, facecolor='#0a0e1a')
            ax.text(0.5, 0.5, '채널 데이터 없음\n(시뮬레이션 재실행 필요)',
                    ha='center', va='center', color='#7d8590',
                    fontsize=12, transform=ax.transAxes)
            self.tab_channel.draw()
            return

        ship_names = [sc[0] for sc in frames[0].ship_channels]
        times = [f.t for f in frames]

        usage = np.zeros((len(ship_names), len(frames)))
        for fi, frame in enumerate(frames):
            for si, sc in enumerate(frame.ship_channels):
                sname, ch_used, ch_max = sc
                usage[si, fi] = ch_used / ch_max if ch_max > 0 else 0.0

        fig = self.tab_channel.fig
        fig.clear()
        fig.patch.set_facecolor(C_BG)
        ax = fig.add_subplot(111, facecolor='#0a0e1a')

        im = ax.imshow(
            usage,
            aspect='auto',
            extent=[times[0], times[-1], -0.5, len(ship_names) - 0.5],
            origin='lower',
            cmap='RdYlGn_r',
            vmin=0, vmax=1,
            interpolation='nearest',
        )
        ax.set_yticks(range(len(ship_names)))
        ax.set_yticklabels(ship_names, color='#aab', fontsize=9)
        ax.set_xlabel('시간 (s)', color='#aab', fontsize=9)
        ax.set_title('채널 포화도  (빨강=포화, 초록=여유)', color='#dde', fontsize=11)
        ax.tick_params(colors='#aab', labelsize=8)
        for sp in ax.spines.values():
            sp.set_color('#1e2a3a')
        cbar = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
        cbar.ax.tick_params(colors='#aab', labelsize=7)
        cbar.set_label('채널 사용률', color='#aab', fontsize=8)
        fig.tight_layout()
        self.tab_channel.draw()


# ════════════════════════════════════════════════════════════════════════════
#  진입점
# ════════════════════════════════════════════════════════════════════════════
def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

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

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()


# ── 6단계 패치 (launcher.py) ──────────────────────────────────────────────────
# · NEW-A: MainWindow — QSplitter 좌(340px 설정패널) / 우(결과탭) 분할 레이아웃
# · NEW-B: ConfigPanel — 아군 편대·날씨·탐지거리·무기재고·적군5행·MC횟수 설정
# · NEW-C: SimWorker(QThread) — 백그라운드 시뮬 (UI 블로킹 없음), progress/finished/error 시그널
# · NEW-D: AnimationTab — matplotlib FigureCanvas + QSlider 80ms 자동 재생
# · NEW-E: MC 통계 탭 — plot_v7() PNG 이미지 임베드
# · NEW-F: 교전 로그 탭 — QTableWidget (시각/이벤트 2열)
# · NEW-G: SysMonitorTab — psutil CPU·RAM 1초 갱신 + 60초 히스토리 차트
# · NEW-H: 핵심 지표 카드 5개 (요격률·완전요격·피격·격침·비용)
# · NEW-I: 다크 테마 QSS + Fusion 팔레트

# ── 포팅 A 패치 (launcher.py) ─────────────────────────────────────────────────
# · NEW-J: 방어 무기 재고 QGroupBox — SM-3/SM-6/SM-2/RAM/홍상어/청상어/Mk.46/기만기 SpinBox
# · NEW-K: 적군 모드 QComboBox — 커스텀/프리셋/랜덤 3종, 각 모드별 추가 위젯
# · NEW-L: 적군 프리셋 QComboBox (V7_ENEMY_FLEET_PRESETS), 난이도+시드 SpinBox

# ── 포팅 B 패치 (launcher.py) ─────────────────────────────────────────────────
# · NEW-M: 전술 옵션 QGroupBox — ECM·회피·기만기·자체방어 QCheckBox 4개
# · NEW-N: _run_sim() — defense_inventory / enemy_fleet_mode / 전술 플래그 cfg 전달

# ── 포팅 C 패치 (launcher.py) ─────────────────────────────────────────────────
# · NEW-K: 항공 자산 QGroupBox — AW-159/P-3C/P-8A QCheckBox 3개 (기본 OFF)
# · NEW-L: _run_sim() — enable_helo / enable_p3c / enable_p8a cfg 전달
# · NEW-M: card_defs 'aircraft' 카드 추가 — _update_cards에서 aircraft_sorties 표시

# ── 포팅 D 패치 (launcher.py) ─────────────────────────────────────────────────
# · NEW-N: evaluate_req_v7 / REQ_ITEMS_V7 / scenario_comparison_v7 / compare_ab_v7 / save·load import
# · NEW-O: 시나리오 저장/불러오기 버튼 (QGroupBox) + A·B 슬롯 저장 버튼
# · NEW-P: _build_req_tab() — REQ 판정 QTableWidget 탭
# · NEW-Q: _build_weather_tab() — 날씨 3종 비교 탭 (실행 버튼 + 결과 테이블)
# · NEW-R: _build_ab_tab() — A vs B 비교 탭 (슬롯 레이블 + 실행 버튼 + 결과 테이블)
# · NEW-S: _fill_req() — _on_finished에서 REQ 결과 자동 채움
# · NEW-T: _run_weather_compare() / _run_ab_compare() / _save_scenario() / _load_scenario() / _save_ab()
