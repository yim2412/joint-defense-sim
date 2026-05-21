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
        splitter.setSizes([340, 1060])

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
        scroll.setFixedWidth(340)
        scroll.setStyleSheet(f"QScrollArea {{ border: none; background: {C_PANEL}; }}")

        inner = QWidget()
        inner.setStyleSheet(f"background: {C_PANEL};")
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # 타이틀
        title = QLabel("⚓ 이지스 기동전단\n통합 방어 시뮬레이터")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont('Malgun Gothic', 13, QFont.Weight.Bold))
        title.setStyleSheet(f"color:{C_ACCENT}; padding: 8px 0;")
        layout.addWidget(title)

        # ── 아군 편대 ──────────────────────────────────────────────────────
        grp_f = QGroupBox("🔵 아군 편대")
        fl = QFormLayout(grp_f)
        fl.setSpacing(6)

        self.cmb_fleet   = QComboBox()
        self.cmb_fleet.addItems(list(V7_FLEET_PRESETS.keys()) if _V7_OK else [])
        self.cmb_weather = QComboBox()
        self.cmb_weather.addItems(list(WEATHER_DB.keys()) if _V7_OK else [])
        self.spn_detect  = QSpinBox()
        self.spn_detect.setRange(50, 500)
        self.spn_detect.setValue(200)
        self.spn_detect.setSuffix(" km")
        self.spn_subdet  = QSpinBox()
        self.spn_subdet.setRange(10, 100)
        self.spn_subdet.setValue(50)
        self.spn_subdet.setSuffix(" km")

        fl.addRow("편대 프리셋",     self.cmb_fleet)
        fl.addRow("날씨",            self.cmb_weather)
        fl.addRow("탐지 거리",       self.spn_detect)
        fl.addRow("대잠 탐지 거리",  self.spn_subdet)
        layout.addWidget(grp_f)

        # ── 공격 무기 재고 ────────────────────────────────────────────────
        grp_w = QGroupBox("🚀 공격 무기 재고")
        wl = QFormLayout(grp_w)
        wl.setSpacing(6)

        self.spn_hs2 = QSpinBox(); self.spn_hs2.setRange(0, 30); self.spn_hs2.setValue(8)
        self.spn_hs1 = QSpinBox(); self.spn_hs1.setRange(0, 30); self.spn_hs1.setValue(0)
        self.spn_hp  = QSpinBox(); self.spn_hp.setRange(0, 30);  self.spn_hp.setValue(4)

        wl.addRow("해성-II",       self.spn_hs2)
        wl.addRow("해성-I",        self.spn_hs1)
        wl.addRow("하푼 Block II", self.spn_hp)
        layout.addWidget(grp_w)

        # ── 방어 무기 재고 (포팅 A) ───────────────────────────────────────
        grp_d = QGroupBox("🛡️ 방어 무기 재고")
        dl = QFormLayout(grp_d)
        dl.setSpacing(5)

        def _spn(lo, hi, val, suffix=''):
            s = QSpinBox(); s.setRange(lo, hi); s.setValue(val)
            if suffix: s.setSuffix(suffix)
            return s

        self.spn_sm3   = _spn(0, 60, 24);  self.spn_sm6  = _spn(0, 60, 16)
        self.spn_sm2   = _spn(0, 90, 32);  self.spn_ram  = _spn(0, 30, 21)
        self.spn_hong  = _spn(0, 20, 3);   self.spn_chng = _spn(0, 20, 4)
        self.spn_mk46  = _spn(0, 30, 6);   self.spn_dcoy = _spn(0, 20, 4)

        dl.addRow("SM-3 Block IIA",  self.spn_sm3)
        dl.addRow("SM-6",            self.spn_sm6)
        dl.addRow("SM-2 Block IIIB", self.spn_sm2)
        dl.addRow("RIM-116 RAM",     self.spn_ram)
        dl.addRow("홍상어 (대잠)",   self.spn_hong)
        dl.addRow("청상어 (경어뢰)", self.spn_chng)
        dl.addRow("Mk.46 경어뢰",    self.spn_mk46)
        dl.addRow("기만기 재고",      self.spn_dcoy)
        layout.addWidget(grp_d)

        # ── 적군 편대 (포팅 A) ────────────────────────────────────────────
        grp_e = QGroupBox("🔴 적군 편대")
        el = QVBoxLayout(grp_e)
        el.setSpacing(4)

        # 모드 선택
        mode_row = QWidget(); mode_rl = QHBoxLayout(mode_row)
        mode_rl.setContentsMargins(0, 0, 0, 0)
        mode_rl.addWidget(QLabel("모드:"))
        self.cmb_enemy_mode = QComboBox()
        self.cmb_enemy_mode.addItems(['커스텀', '프리셋', '랜덤'])
        mode_rl.addWidget(self.cmb_enemy_mode, stretch=1)
        el.addWidget(mode_row)

        # 프리셋 선택 (프리셋 모드용)
        self.cmb_fleet_preset_e = QComboBox()
        self.cmb_fleet_preset_e.addItems(list(V7_ENEMY_FLEET_PRESETS.keys()) if _V7_OK else [])
        el.addWidget(self.cmb_fleet_preset_e)

        # 랜덤 난이도 + 시드 (랜덤 모드용)
        rand_row = QWidget(); rand_rl = QHBoxLayout(rand_row)
        rand_rl.setContentsMargins(0, 0, 0, 0); rand_rl.setSpacing(4)
        self.cmb_difficulty = QComboBox()
        self.cmb_difficulty.addItems(list(V7_RANDOM_CFG.keys()) if _V7_OK else ['보통'])
        self.cmb_difficulty.setCurrentText('보통')
        self.spn_seed = QSpinBox(); self.spn_seed.setRange(0, 99999); self.spn_seed.setValue(0)
        self.spn_seed.setPrefix("씨앗: ")
        rand_rl.addWidget(self.cmb_difficulty, stretch=1)
        rand_rl.addWidget(self.spn_seed, stretch=1)
        el.addWidget(rand_row)

        # 커스텀 5행
        self._enemy_rows = []
        for i in range(5):
            row_w = QWidget(); row_l = QHBoxLayout(row_w)
            row_l.setContentsMargins(0, 0, 0, 0); row_l.setSpacing(4)
            cmb = QComboBox()
            if _V7_OK: cmb.addItems(list(V7_ENEMY_DB.keys()))
            spn = QSpinBox(); spn.setRange(0, 8); spn.setValue(1 if i < 3 else 0)
            row_l.addWidget(cmb, stretch=3); row_l.addWidget(spn, stretch=1)
            el.addWidget(row_w)
            self._enemy_rows.append((cmb, spn))

        if _V7_OK:
            defaults = ['055형 대형 구축함', 'J-20 (위룡)',
                        'DF-21D (대함 탄도)', '052D형 구축함',
                        '095형 잠수함 (차세대 SSN)']
            keys = list(V7_ENEMY_DB.keys())
            for i, name in enumerate(defaults):
                if name in keys:
                    self._enemy_rows[i][0].setCurrentText(name)

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

        # ── MC 설정 ────────────────────────────────────────────────────────
        grp_mc = QGroupBox("📊 몬테카를로")
        mcl = QFormLayout(grp_mc)
        self.spn_mc_n = QSpinBox()
        self.spn_mc_n.setRange(50, 2000)
        self.spn_mc_n.setValue(200)
        self.spn_mc_n.setSingleStep(50)
        mcl.addRow("반복 횟수", self.spn_mc_n)
        layout.addWidget(grp_mc)

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

        self.tab_log = self._build_log_tab()
        self.tabs.addTab(self.tab_log,       "📜  교전 로그")

        self.tab_sysmon = SysMonitorTab()
        self.tabs.addTab(self.tab_sysmon,    "🖥️  시스템 모니터")

        return panel

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
            # 아군 편대
            'fleet_preset':   self.cmb_fleet.currentText(),
            'weather':        self.cmb_weather.currentText(),
            'detect_km':      self.spn_detect.value(),
            'sub_detect_km':  self.spn_subdet.value(),
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
        self._fill_log(result.get('log', []))

        self.tabs.setCurrentIndex(0)

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
