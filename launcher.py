"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   이지스 기동전단 통합 방어 시뮬레이터  v7.0 — PyQt6 런처                  ║
╠══════════════════════════════════════════════════════════════════════════════╣
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

import sys, os, time, threading, json
import psutil

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QSplitter,
    QVBoxLayout, QHBoxLayout, QFormLayout, QScrollArea,
    QGridLayout,
    QLabel, QPushButton, QComboBox, QSpinBox, QTabWidget,
    QTableWidget, QTableWidgetItem, QSlider, QProgressBar,
    QGroupBox, QStatusBar, QMessageBox, QHeaderView,
    QSizePolicy, QCheckBox, QFileDialog, QLineEdit,
)
from PyQt6.QtGui import QFont, QColor, QPalette, QShortcut
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QKeySequence

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
        save_json_report_v7,
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
    progress        = pyqtSignal(str)           # 진행 메시지
    progress_detail = pyqtSignal(int, int, float) # (현재, 전체, ETA초)
    finished        = pyqtSignal(dict, dict)    # (result, mc)
    error           = pyqtSignal(str)
    sim_started     = pyqtSignal()
    sim_ended       = pyqtSignal()

    def __init__(self, cfg: dict, mc_n: int):
        super().__init__()
        self.cfg  = cfg
        self.mc_n = mc_n

    def run(self):
        try:
            self.sim_started.emit()
            self.progress.emit("시뮬레이션 실행 중...")
            result = run_v7_simulation(self.cfg)
            self.progress.emit(f"MC {self.mc_n}회 분석 중...")
            t0 = time.time()
            # MC 진행률 콜백 지원 (monte_carlo_v7가 progress_cb를 지원할 경우)
            def _cb(done, total):
                elapsed = time.time() - t0
                eta = (elapsed / done * (total - done)) if done > 0 else 0.0
                self.progress_detail.emit(done, total, eta)
                self.progress.emit(f"MC {done}/{total}회 | 잔여 약 {eta:.0f}초")
            try:
                mc = monte_carlo_v7(self.cfg, n=self.mc_n, progress_cb=_cb)
            except TypeError:
                mc = monte_carlo_v7(self.cfg, n=self.mc_n)
            self.sim_ended.emit()
            self.finished.emit(result, mc)
        except Exception as e:
            self.sim_ended.emit()
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
#  전장 애니메이션 탭 (matplotlib 2.5D 등각투영)
# ════════════════════════════════════════════════════════════════════════════
class AnimationTab(QWidget):
    """
    2.5D 등각투영(isometric) 전장 애니메이션.
    matplotlib 2D 위에 등각투영 좌표 변환으로 고도를 시각화.
    탄도탄 포물선 호, 항공기·잠수함 고도가 수직 오프셋으로 표현됨.
    """

    # 엔티티 유형 → (matplotlib marker, 크기, 색상, zorder)
    _ENT_CFG = {
        'friendly': ('^', 140, '#2ecc71',  8),
        'aircraft':  ('*', 170, '#ff6b6b',  7),
        'ship':      ('s',  90, '#ff8c8c',  7),
        'sub':       ('D',  75, '#e74c3c',  7),
        'em_bm':    ('^',  55, '#ff2222',  9),
        'em_cm':    ('o',  30, '#ff8888',  9),
        'sam':       ('^',  30, '#55ff99', 10),
        'fstk':      ('o',  30, '#55aaff', 10),
        'esam':      ('v',  22, '#e67e22',  9),
    }

    # 등각투영 파라미터
    _ISO_COS      = np.cos(np.radians(30))   # ≈ 0.866
    _ISO_SIN      = np.sin(np.radians(30))   # ≈ 0.500
    _ALT_SCALE    = 0.50   # 고도 1km → 화면 0.5단위
    _MAX_DISP_ALT = 200.0  # 탄도탄 고도 표시 상한(km)

    def __init__(self):
        super().__init__()
        self.frames = []
        self._display_range = 350.0
        self._cur_idx = 0
        self._zoom = 1.0
        self._kill_frames = []
        self._play_interval = 80
        self._build_ui()

    # ── 등각투영 좌표 변환 ────────────────────────────────────────────────
    def _iso(self, xk: float, yk: float, ak: float = 0.0):
        """월드 좌표(km) → 등각투영 화면 좌표 (sx, sy)."""
        ak_c = min(ak, self._MAX_DISP_ALT)
        sx = (xk - yk) * self._ISO_COS
        sy = (xk + yk) * self._ISO_SIN + ak_c * self._ALT_SCALE
        return sx, sy

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # ── matplotlib 캔버스 ─────────────────────────────────────────────
        self._fig = Figure(figsize=(8, 6), facecolor='#0d1117')
        self.canvas = FigureCanvas(self._fig)
        self.canvas.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.ax = self._fig.add_axes([0.01, 0.01, 0.98, 0.98],
                                      facecolor='#0d1117')
        self.ax.set_aspect('equal')
        self.ax.axis('off')
        layout.addWidget(self.canvas)

        # 스크롤 줌 이벤트 연결
        self.canvas.mpl_connect('scroll_event', self._on_scroll)

        # ── 옵션 행 ──────────────────────────────────────────────────────
        opt_row = QHBoxLayout()
        self.chk_labels = QCheckBox("이름 표시")
        self.chk_labels.setChecked(True)
        self.chk_labels.setStyleSheet(f"color:{C_TEXT}; font-size:11px;")
        self.chk_labels.stateChanged.connect(lambda _: self._redraw_current())

        self.chk_altitude = QCheckBox("고도선 표시")
        self.chk_altitude.setChecked(True)
        self.chk_altitude.setStyleSheet(f"color:{C_TEXT}; font-size:11px;")
        self.chk_altitude.stateChanged.connect(lambda _: self._redraw_current())

        _bs = (f"background:{C_PANEL}; color:{C_TEXT}; "
               f"border:1px solid #3a5a7a; font-size:11px; padding:2px 7px;")

        # 재생 속도 버튼
        lbl_spd = QLabel("속도:")
        lbl_spd.setStyleSheet(f"color:{C_SUBTEXT}; font-size:11px;")
        self._spd_btns = []
        for label, ms in [("0.5x", 160), ("1x", 80), ("2x", 40), ("4x", 20)]:
            b = QPushButton(label)
            b.setFixedHeight(24); b.setFixedWidth(36)
            b.setStyleSheet(_bs)
            b.clicked.connect(lambda _, m=ms: self._set_speed(m))
            self._spd_btns.append(b)
            opt_row.addWidget(b) if label != "0.5x" else None

        opt_row.addWidget(self.chk_labels)
        opt_row.addWidget(self.chk_altitude)
        opt_row.addWidget(lbl_spd)
        for b in self._spd_btns:
            opt_row.addWidget(b)

        # 스크린샷 버튼
        btn_shot = QPushButton("📷")
        btn_shot.setFixedHeight(24); btn_shot.setFixedWidth(30)
        btn_shot.setStyleSheet(_bs)
        btn_shot.setToolTip("현재 프레임 PNG 저장")
        btn_shot.clicked.connect(self._save_screenshot)
        opt_row.addWidget(btn_shot)

        lbl_hint = QLabel("  휠:줌  2.5D 등각투영")
        lbl_hint.setStyleSheet(f"color:{C_SUBTEXT}; font-size:10px;")
        opt_row.addWidget(lbl_hint)
        opt_row.addStretch()
        layout.addLayout(opt_row)

        # ── 재생 컨트롤 ───────────────────────────────────────────────────
        ctrl = QHBoxLayout()
        self.lbl_time = QLabel("t = 0s")
        self.lbl_time.setStyleSheet(
            f"color:{C_ACCENT}; font-weight:bold; font-size:14px;")
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0); self.slider.setMaximum(0)
        self.slider.valueChanged.connect(self._on_slider)
        self.btn_play = QPushButton("▶ 재생")
        self.btn_play.setFixedWidth(90)
        self.btn_play.clicked.connect(self._toggle_play)

        # 격추 이벤트 이동 버튼
        self.btn_prev_kill = QPushButton("◀ 격추")
        self.btn_next_kill = QPushButton("격추 ▶")
        for b in [self.btn_prev_kill, self.btn_next_kill]:
            b.setFixedWidth(65); b.setFixedHeight(26)
            b.setStyleSheet(_bs)
        self.btn_prev_kill.clicked.connect(self._prev_kill)
        self.btn_next_kill.clicked.connect(self._next_kill)

        self.lbl_events = QLabel("")
        self.lbl_events.setStyleSheet(f"color:{C_SUBTEXT}; font-size:11px;")
        self.lbl_events.setWordWrap(True)
        ctrl.addWidget(self.btn_prev_kill)
        ctrl.addWidget(self.btn_next_kill)
        ctrl.addWidget(self.lbl_time)
        ctrl.addWidget(self.slider, stretch=1)
        ctrl.addWidget(self.btn_play)
        layout.addLayout(ctrl)
        layout.addWidget(self.lbl_events)

        self._play_timer = QTimer()
        self._play_timer.timeout.connect(self._step_play)
        self._playing = False

    # ── 공개 API ──────────────────────────────────────────────────────────
    def load_frames(self, frames):
        self.frames = frames
        self._display_range = self._calc_range(frames)
        self._zoom = 1.0
        # 격추 이벤트 발생 프레임 인덱스 추출
        self._kill_frames = [
            i for i, f in enumerate(frames)
            if any('격추' in e or '요격' in e or '파괴' in e
                   for e in (f.events or []))
        ]
        if not frames:
            return
        self.slider.setMaximum(len(frames) - 1)
        self.slider.setValue(0)
        self._draw_frame(0)

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

    def _redraw_current(self):
        if self.frames:
            self._draw_frame(self._cur_idx)

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

    def _on_scroll(self, event):
        """마우스 휠 줌인/줌아웃."""
        if event.button == 'up':
            self._zoom *= 0.85
        elif event.button == 'down':
            self._zoom *= 1.15
        self._zoom = max(0.2, min(5.0, self._zoom))
        self._redraw_current()

    def _set_speed(self, ms: int):
        """재생 속도 변경."""
        self._play_interval = ms
        if self._playing:
            self._play_timer.setInterval(ms)

    def _prev_kill(self):
        """이전 격추 이벤트 프레임으로 이동."""
        if not self._kill_frames:
            return
        cur = self._cur_idx
        prev = [f for f in self._kill_frames if f < cur]
        if prev:
            self.slider.setValue(prev[-1])

    def _next_kill(self):
        """다음 격추 이벤트 프레임으로 이동."""
        if not self._kill_frames:
            return
        cur = self._cur_idx
        nxt = [f for f in self._kill_frames if f > cur]
        if nxt:
            self.slider.setValue(nxt[0])

    def _save_screenshot(self):
        """현재 프레임을 PNG로 저장."""
        path, _ = QFileDialog.getSaveFileName(
            self, "스크린샷 저장",
            f"전장_{self._cur_idx:04d}.png",
            "PNG (*.png)")
        if path:
            self._fig.savefig(path, dpi=150,
                              bbox_inches='tight',
                              facecolor='#0d1117')

    def _draw_grid(self, R: float):
        """등각투영 해수면 격자 + 거리 링."""
        ax = self.ax
        step = max(50, int(R / 5) // 10 * 10)
        gc = '#0c2640'

        r_int = int(R) + step
        vals = range(-r_int, r_int + step, step)
        for v in vals:
            x1, y1 = self._iso(-R, v);  x2, y2 = self._iso(R, v)
            ax.plot([x1, x2], [y1, y2], color=gc, lw=0.55, zorder=1)
            x1, y1 = self._iso(v, -R);  x2, y2 = self._iso(v, R)
            ax.plot([x1, x2], [y1, y2], color=gc, lw=0.55, zorder=1)

        for ring_r in [r for r in [100, 200, 300, 400, 500, 700] if r < R * 1.05]:
            θ = np.linspace(0, 2 * np.pi, 80)
            rxs = ring_r * np.cos(θ); rys = ring_r * np.sin(θ)
            sxs = [(x - y) * self._ISO_COS for x, y in zip(rxs, rys)]
            sys_ = [(x + y) * self._ISO_SIN for x, y in zip(rxs, rys)]
            ax.plot(sxs, sys_, color='#152e48', lw=0.85, ls='--', zorder=1)
            lx, ly = self._iso(ring_r * 0.72, ring_r * (-0.72))
            ax.text(lx, ly, f'{ring_r}km',
                    color='#2a4e72', fontsize=7, va='center', zorder=2)

    # ── 핵심: 프레임 렌더링 ──────────────────────────────────────────────
    def _draw_frame(self, idx: int):
        self._cur_idx = idx
        frame = self.frames[idx]
        self.lbl_time.setText(f"t = {frame.t:.0f}s")

        ax = self.ax
        ax.cla()
        ax.set_facecolor('#0d1117')
        ax.axis('off')
        ax.set_aspect('equal')

        R  = self._display_range
        km = lambda v: v / 1000.0
        show_labels    = self.chk_labels.isChecked()
        show_alt_lines = self.chk_altitude.isChecked()

        self._draw_grid(R)

        # 화면 범위 확정 (등각투영 기준 + zoom 적용)
        cx = R * self._ISO_COS
        cy_gnd = R * self._ISO_SIN
        cy_alt = self._MAX_DISP_ALT * self._ALT_SCALE
        x_span  = cx * 1.10 * self._zoom
        y_bot   = -cy_gnd * 0.40 * self._zoom   # 하단 여유 확대
        y_top   = (cy_gnd + cy_alt * 0.60) * self._zoom
        ax.set_xlim(-x_span, x_span)
        ax.set_ylim(y_bot, y_top)

        # ── 적 위협 ───────────────────────────────────────────────────────
        for item in frame.enemy_ships:
            euid, epname, ex, ey, ealive, ehp = item[:6]
            ealt = item[6] if len(item) > 6 else 0.0
            xk, yk, ak = km(ex), km(ey), km(ealt)

            gx, gy = self._iso(xk, yk, 0)
            px, py = self._iso(xk, yk, ak)

            if ak > 0.5 and show_alt_lines:
                ax.plot([gx, px], [gy, py],
                        color='#ff6b6b', lw=0.9, alpha=0.40, zorder=5)
                ax.scatter([gx], [gy], s=10, c='#ff4444',
                           marker='o', alpha=0.22, zorder=5, edgecolors='none')

            if ak < -0.02:
                key = 'sub'
            elif ak > 0.5:
                key = 'aircraft'
            else:
                key = 'ship'
            mk, sz, col, zo = self._ENT_CFG[key]
            ec = '#ff0000' if not ealive else 'none'
            lw = 2.0   if not ealive else 0
            ax.scatter([px], [py], s=sz, c=col, marker=mk,
                       edgecolors=ec, linewidths=lw, zorder=zo)
            if show_labels and ealive:
                ax.text(px + R * 0.02, py + R * 0.015, epname[:10],
                        color='#ffaaaa', fontsize=7,
                        ha='left', va='bottom', zorder=12)

        # ── 아군 함정 ─────────────────────────────────────────────────────
        for sname, sx_, sy_, salive, shp in frame.friendly_ships:
            xk, yk = km(sx_), km(sy_)
            px, py = self._iso(xk, yk, 0)
            mk, sz, col, zo = self._ENT_CFG['friendly']
            ec = '#ff0000' if not salive else 'none'
            lw = 2.5   if not salive else 0
            ax.scatter([px], [py], s=sz, c=col, marker=mk,
                       edgecolors=ec, linewidths=lw, zorder=zo)
            if show_labels:
                ax.text(px + R * 0.02, py + R * 0.015, sname[:9],
                        color='#aaffcc', fontsize=7,
                        ha='left', va='bottom', zorder=12)

        # ── 미사일 ────────────────────────────────────────────────────────
        for item in frame.missiles:
            muid, mx_, my_, mtype, mname = item[:5]
            malt = item[5] if len(item) > 5 else 0.0
            xk, yk, ak = km(mx_), km(my_), km(malt)

            gx, gy = self._iso(xk, yk, 0)
            px, py = self._iso(xk, yk, ak)

            if mtype == 'enemy_strike':
                key = 'em_bm' if malt > 5000 else 'em_cm'
            elif mtype == 'friendly_sam':
                key = 'sam'
            elif mtype == 'friendly_strike':
                key = 'fstk'
            elif mtype == 'enemy_sam':
                key = 'esam'
            else:
                continue

            mk, sz, col, zo = self._ENT_CFG[key]
            if ak > 0.5 and show_alt_lines:
                ax.plot([gx, px], [gy, py],
                        color=col, lw=0.7, alpha=0.38, zorder=6)
            ax.scatter([px], [py], s=sz, c=col, marker=mk,
                       edgecolors='none', zorder=zo)
            # 미사일 이름 표시
            if show_labels and mname:
                short = mname[:8]
                lbl_col = '#aaffaa' if mtype == 'friendly_sam' else \
                          '#aaaaff' if mtype == 'friendly_strike' else '#ffaaaa'
                ax.text(px + R * 0.015, py + R * 0.01, short,
                        color=lbl_col, fontsize=6,
                        ha='left', va='bottom', zorder=12)

        # ── 타이틀 ────────────────────────────────────────────────────────
        ylim_top = ax.get_ylim()[1]
        ax.text(0, ylim_top * 0.975,
                f"전장 상황   t = {frame.t:.0f}s",
                color='#dde8ff', fontsize=11, fontweight='bold',
                ha='center', va='top', zorder=15)

        # ── 범례 ─────────────────────────────────────────────────────────
        legend_items = [
            ('▲ 아군 함정',  '#2ecc71'),
            ('★ 적 항공기',  '#ff6b6b'),
            ('■ 적 수상함',  '#ff8c8c'),
            ('◆ 적 잠수함',  '#e74c3c'),
            ('▲ 아군 SAM',   '#55ff99'),
            ('● 적 미사일',  '#ff2222'),
            ('▲ 적 탄도탄',  '#ff4444'),
        ]
        lx_leg = cx * 0.90
        ly_leg = ylim_top * 0.95
        row_h  = (ylim_top - ax.get_ylim()[0]) * 0.055
        for i, (lbl, col) in enumerate(legend_items):
            ax.text(lx_leg, ly_leg - i * row_h,
                    lbl, color=col, fontsize=7,
                    ha='center', va='top', zorder=15)

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
        self._sim_ranges = []   # [(start_idx, end_idx)] 시뮬 구간
        self._sim_start_idx = None

    def mark_sim_start(self):
        self._sim_start_idx = len(self._cpu_hist) - 1

    def mark_sim_end(self):
        if self._sim_start_idx is not None:
            end = len(self._cpu_hist) - 1
            self._sim_ranges.append((self._sim_start_idx, end))
            self._sim_start_idx = None
            # 최근 3구간만 유지
            self._sim_ranges = self._sim_ranges[-3:]

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
        # 시뮬 실행 구간 하이라이트
        for s, e in self._sim_ranges:
            ax.axvspan(s, min(e, 59), color='#f1c40f', alpha=0.12, zorder=0)
        if self._sim_start_idx is not None:
            ax.axvspan(self._sim_start_idx, 59,
                       color='#f1c40f', alpha=0.18, zorder=0,
                       label='시뮬 실행 중')
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

        # 단축키
        QShortcut(QKeySequence(Qt.Key.Key_Space), self,
                  activated=self._shortcut_play_pause)
        QShortcut(QKeySequence(Qt.Key.Key_Left), self,
                  activated=self._shortcut_prev_frame)
        QShortcut(QKeySequence(Qt.Key.Key_Right), self,
                  activated=self._shortcut_next_frame)

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


        # ── 적군 편대 (포팅 A) ────────────────────────────────────────────
        grp_e = QGroupBox("🔴 적군 편대")
        el = QVBoxLayout(grp_e)
        el.setSpacing(4)

        # 모드 선택
        mode_row = QWidget(); mode_rl = QHBoxLayout(mode_row)
        mode_rl.setContentsMargins(0, 0, 0, 0)
        mode_rl.addWidget(QLabel("모드:"))
        self.cmb_enemy_mode = NoScrollComboBox()
        self.cmb_enemy_mode.addItems(['프리셋', '랜덤'])
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

        self.cmb_enemy_mode.currentIndexChanged.connect(self._on_enemy_mode_changed)
        self._on_enemy_mode_changed(0)  # 초기 상태 적용 (기본: 프리셋)
        if _V7_OK:
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
            chk.setStyleSheet(f"color:{C_TEXT}; font-size:12px;")
            acl.addWidget(chk)

        grp_ac.hide()
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
        lbl_tactics.setStyleSheet(f"color:{C_SUBTEXT}; font-size:11px;")
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
            chk.setStyleSheet(f"color:{C_TEXT}; font-size:12px;")
            defl.addWidget(chk)
        defl.addLayout(tactics_row)

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

        grp_def.hide()
        layout.addWidget(grp_def)

        # ── C&D 시간 설정 ──────────────────────────────────────────────────
        grp_cd = QGroupBox("⏱️ C&&D 시간 설정")
        cdl = QVBoxLayout(grp_cd)
        cdl.setSpacing(6)

        # cd_time_s
        cd_row1 = QHBoxLayout()
        lbl_cd_name = QLabel("C&&D 시간 (초)")
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
        self.spn_mc_n.setRange(50, 5000)
        self.spn_mc_n.setValue(1000)
        self.spn_mc_n.setSingleStep(50)
        mcl.addRow("반복 횟수", self.spn_mc_n)
        layout.addWidget(grp_mc)

        # ── 설정 프로필 저장/불러오기 ─────────────────────────────────────────
        grp_prof = QGroupBox("📋 설정 프로필")
        profl = QVBoxLayout(grp_prof)
        profl.setSpacing(4)

        # 프로필 선택 콤보박스
        prof_sel_row = QHBoxLayout()
        lbl_prof = QLabel("프로필:")
        lbl_prof.setStyleSheet(f"color:{C_SUBTEXT}; font-size:11px;")
        lbl_prof.setFixedWidth(42)
        self.cmb_profile = NoScrollComboBox()
        self.cmb_profile.setMinimumWidth(120)
        prof_sel_row.addWidget(lbl_prof)
        prof_sel_row.addWidget(self.cmb_profile, stretch=1)
        profl.addLayout(prof_sel_row)

        # 새 프로필 이름 입력
        prof_name_row = QHBoxLayout()
        lbl_pname = QLabel("이름:")
        lbl_pname.setStyleSheet(f"color:{C_SUBTEXT}; font-size:11px;")
        lbl_pname.setFixedWidth(42)
        self.edt_profile_name = QLineEdit()
        self.edt_profile_name.setPlaceholderText("새 프로필 이름 입력")
        self.edt_profile_name.setStyleSheet(
            f"background:{C_PANEL}; color:{C_TEXT}; border:1px solid #3a5a7a; "
            f"font-size:11px; padding:2px 4px;")
        prof_name_row.addWidget(lbl_pname)
        prof_name_row.addWidget(self.edt_profile_name, stretch=1)
        profl.addLayout(prof_name_row)

        # 버튼 행
        prof_btn_row = QHBoxLayout()
        prof_btn_row.setSpacing(4)
        btn_prof_save = QPushButton("저장")
        btn_prof_load = QPushButton("불러오기")
        btn_prof_del  = QPushButton("삭제")
        for b in [btn_prof_save, btn_prof_load, btn_prof_del]:
            b.setFixedHeight(26)
            b.setStyleSheet(
                f"background:{C_PANEL}; color:{C_TEXT}; border:1px solid #3a5a7a; font-size:11px;")
            prof_btn_row.addWidget(b)
        btn_prof_save.clicked.connect(self._save_profile)
        btn_prof_load.clicked.connect(self._load_profile)
        btn_prof_del.clicked.connect(self._delete_profile)
        profl.addLayout(prof_btn_row)

        layout.addWidget(grp_prof)
        self._refresh_profile_list()

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

        self.tab_channel = MplCanvas(figsize=(12, 5))
        self.tabs.addTab(self.tab_channel,   "📡  채널 포화도")

        self.tab_sysmon = SysMonitorTab()
        self.tabs.addTab(self.tab_sysmon,    "🖥️  시스템 모니터")

        # ── 3단계 분석 탭 ──────────────────────────────────────────────────
        self.tab_cost_eff = MplCanvas(figsize=(12, 5))
        self.tabs.addTab(self.tab_cost_eff, "💰  비용 효과")

        self.tab_ammo_curve = MplCanvas(figsize=(12, 5))
        self.tabs.addTab(self.tab_ammo_curve, "🔫  탄약 소모")

        self.tab_ci = MplCanvas(figsize=(12, 5))
        self.tabs.addTab(self.tab_ci,       "📈  MC 신뢰구간")

        self.tab_timeline = MplCanvas(figsize=(14, 5))
        self.tabs.addTab(self.tab_timeline, "⏱️  교전 타임라인")

        self.tab_sensitivity = MplCanvas(figsize=(12, 6))
        self.tabs.addTab(self.tab_sensitivity, "🌪️  감도 분석")

        self.tab_bearing = MplCanvas(figsize=(8, 8))
        self.tabs.addTab(self.tab_bearing, "🧭  방위각 취약점")

        self.tab_req_radar = MplCanvas(figsize=(8, 8))
        self.tabs.addTab(self.tab_req_radar, "🎯  REQ 충족률")

        self.tab_threat_type = MplCanvas(figsize=(12, 5))
        self.tabs.addTab(self.tab_threat_type, "📊  위협 유형별")

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
        if is_preset and self.cmb_fleet_preset_e.count():
            self._update_enemy_preset_detail(self.cmb_fleet_preset_e.currentText())

    def _apply_style(self):
        self.setStyleSheet(STYLE_MAIN)

    # ── 시뮬 실행 ────────────────────────────────────────────────────────────

    def _run_sim(self):
        # 적군 모드 및 편대 구성 (포팅 A)
        mode_label = self.cmb_enemy_mode.currentText()
        mode_map   = {'프리셋': 'preset', '랜덤': 'random'}
        enemy_mode = mode_map.get(mode_label, 'preset')

        cfg = {
            # 아군 편대 (탐지거리는 엔진이 함대+날씨로 자동 계산)
            'fleet_preset':      self.cmb_fleet.currentText(),
            'weather':           self.cmb_weather.currentText(),
            'detect_km_manual':  False,
            # 적군 (포팅 A)
            'enemy_fleet_mode':       enemy_mode,
            'enemy_fleet_preset':     self.cmb_fleet_preset_e.currentText(),
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
            'enable_multibearing':    self.chk_multibearing.isChecked(),
            'enable_cec_jammed':      self.chk_cec_jammed.isChecked(),
            'enable_ship_evasion':    self.chk_ship_evasion.isChecked(),
            'enemy_tactics':          {
                '없음': None, 'V자 대형': 'v_formation',
                '포위 기동': 'encirclement'
            }.get(self.cmb_enemy_tactics.currentText(), None),
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
        self._worker.progress_detail.connect(self._on_progress_detail)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.sim_started.connect(self.tab_sysmon.mark_sim_start)
        self._worker.sim_ended.connect(self.tab_sysmon.mark_sim_end)
        self._worker.start()

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
        self._draw_channel_heatmap(result)
        self._draw_cost_effect(result, mc)
        self._draw_ammo_curve(mc)
        self._draw_ci_chart(mc)
        self._draw_timeline(result)
        self._draw_bearing_vulnerability(result)
        self._draw_req_radar(result, mc)
        self._draw_threat_type(result, mc)
        # 감도 분석은 백그라운드 MC가 필요하므로 현재 cfg 저장 후 별도 실행
        cfg = self._worker.cfg if self._worker else {}
        mc_n = self._worker.mc_n if self._worker and hasattr(self._worker, 'mc_n') else 100
        QTimer.singleShot(500, lambda: self._draw_sensitivity(cfg, mc_n))

        self.tabs.setCurrentIndex(1)  # MC 통계 탭으로 자동 전환

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
            sc = scenario_comparison_v7(cfg, n=1000)
        except Exception as e:
            QMessageBox.critical(self, "오류", str(e))
            self.btn_weather_run.setEnabled(True)
            self.btn_weather_run.setText("🌤️  날씨별 비교 실행 (각 1000회 MC)")
            return
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

    # ── 설정 프로필 저장/불러오기 ────────────────────────────────────────────

    def _profiles_dir(self) -> str:
        base = os.path.dirname(os.path.abspath(__file__))
        d = os.path.join(base, 'profiles')
        os.makedirs(d, exist_ok=True)
        return d

    def _refresh_profile_list(self):
        d = self._profiles_dir()
        names = sorted(
            os.path.splitext(f)[0]
            for f in os.listdir(d) if f.endswith('.json')
        )
        self.cmb_profile.blockSignals(True)
        self.cmb_profile.clear()
        self.cmb_profile.addItems(names)
        self.cmb_profile.blockSignals(False)

    def _ui_to_profile(self) -> dict:
        return {
            'fleet_preset':       self.cmb_fleet.currentText(),
            'weather':            self.cmb_weather.currentText(),
            'enemy_mode':         self.cmb_enemy_mode.currentText(),
            'enemy_fleet_preset': self.cmb_fleet_preset_e.currentText(),
            'difficulty':         self.cmb_difficulty.currentText(),
            'enemy_seed':         self.spn_seed.value(),
            'sim_seed':           self.spn_sim_seed.value(),
            'cd_time_s':          self.sld_cd.value(),
            'confirm_time_s':     self.sld_confirm.value(),
            'mc_n':               self.spn_mc_n.value(),
            'multibearing':       self.chk_multibearing.isChecked(),
            'cec_jammed':         self.chk_cec_jammed.isChecked(),
            'ship_evasion':       self.chk_ship_evasion.isChecked(),
            'enemy_tactics':      self.cmb_enemy_tactics.currentText(),
        }

    def _profile_to_ui(self, p: dict):
        def _set_cmb(cmb, val):
            idx = cmb.findText(val)
            if idx >= 0:
                cmb.setCurrentIndex(idx)

        _set_cmb(self.cmb_fleet,          p.get('fleet_preset', ''))
        _set_cmb(self.cmb_weather,        p.get('weather', ''))
        _set_cmb(self.cmb_enemy_mode,     p.get('enemy_mode', ''))
        _set_cmb(self.cmb_fleet_preset_e, p.get('enemy_fleet_preset', ''))
        _set_cmb(self.cmb_difficulty,     p.get('difficulty', ''))
        _set_cmb(self.cmb_enemy_tactics,  p.get('enemy_tactics', '없음'))
        self.spn_seed.setValue(p.get('enemy_seed', 0))
        self.spn_sim_seed.setValue(p.get('sim_seed', 0))
        self.sld_cd.setValue(p.get('cd_time_s', 10))
        self.sld_confirm.setValue(p.get('confirm_time_s', 3))
        self.spn_mc_n.setValue(p.get('mc_n', 1000))
        self.chk_multibearing.setChecked(p.get('multibearing', False))
        self.chk_cec_jammed.setChecked(p.get('cec_jammed', False))
        self.chk_ship_evasion.setChecked(p.get('ship_evasion', False))

    def _save_profile(self):
        name = self.edt_profile_name.text().strip()
        if not name:
            name = self.cmb_profile.currentText().strip()
        if not name:
            QMessageBox.warning(self, "프로필 저장", "저장할 프로필 이름을 입력하세요.")
            return
        import re
        safe = re.sub(r'[\\/:*?"<>|]', '_', name)
        path = os.path.join(self._profiles_dir(), f"{safe}.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self._ui_to_profile(), f, ensure_ascii=False, indent=2)
        self._refresh_profile_list()
        idx = self.cmb_profile.findText(safe)
        if idx >= 0:
            self.cmb_profile.setCurrentIndex(idx)
        self.edt_profile_name.clear()
        self._lbl_status.setText(f"프로필 저장: {safe}")

    def _load_profile(self):
        name = self.cmb_profile.currentText().strip()
        if not name:
            QMessageBox.warning(self, "프로필 불러오기", "불러올 프로필을 선택하세요.")
            return
        path = os.path.join(self._profiles_dir(), f"{name}.json")
        if not os.path.exists(path):
            QMessageBox.warning(self, "프로필 불러오기", f"파일 없음: {path}")
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                p = json.load(f)
            self._profile_to_ui(p)
            self._lbl_status.setText(f"프로필 불러옴: {name}")
        except Exception as e:
            QMessageBox.critical(self, "오류", str(e))

    def _delete_profile(self):
        name = self.cmb_profile.currentText().strip()
        if not name:
            return
        reply = QMessageBox.question(
            self, "프로필 삭제", f"'{name}' 프로필을 삭제하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return
        path = os.path.join(self._profiles_dir(), f"{name}.json")
        if os.path.exists(path):
            os.remove(path)
        self._refresh_profile_list()
        self._lbl_status.setText(f"프로필 삭제: {name}")

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
            for uid, epname, ex, ey, ealive, ehp, *_ in frame.enemy_ships:
                dist = ((ex - px0)**2 + (ey - py0)**2)**0.5 / 1000
                if uid not in enemy_tracks:
                    enemy_tracks[uid] = {'name': epname, 'pts': []}
                enemy_tracks[uid]['pts'].append((t, dist))
            for uid, mx, my, mtype, mname, *_ in frame.missiles:
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
            for uid, mx, my, mtype, mname, *_ in frame.missiles:
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

    def _draw_cost_effect(self, result: dict, mc: dict):
        """💰 비용 대비 효과: 격추 1건당 평균 비용, 무기별 평균 잔여 재고 막대."""
        fig = self.tab_cost_eff.fig
        fig.clear()
        fig.patch.set_facecolor(C_BG)

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

        # 왼쪽: 격추당 비용 텍스트 카드
        ax1.axis('off')
        lbl = f"${cost_per_kill:,.0f}" if cost_per_kill != float('inf') else "N/A"
        ax1.text(0.5, 0.6, lbl, ha='center', va='center',
                 color=C_GREEN, fontsize=26, fontweight='bold',
                 transform=ax1.transAxes)
        ax1.text(0.5, 0.35, '격추 1건당 평균 비용', ha='center', va='center',
                 color=C_TEXT, fontsize=11, transform=ax1.transAxes)
        ax1.text(0.5, 0.20, f"총 평균 비용 ${mean_cost:,.0f}  |  평균 격침 {mean_kill:.1f}척",
                 ha='center', va='center', color=C_SUBTEXT, fontsize=9,
                 transform=ax1.transAxes)
        ax1.set_facecolor('#0a0e1a')

        # 오른쪽: 무기별 평균 잔여 재고
        if ax2 and wpn_rem:
            names = list(wpn_rem.keys())
            vals  = [wpn_rem[n] for n in names]
            colors = [C_GREEN if v > 5 else C_ORANGE if v > 0 else C_RED for v in vals]
            y = range(len(names))
            ax2.barh(list(y), vals, color=colors, height=0.6)
            ax2.set_yticks(list(y))
            ax2.set_yticklabels(names, color=C_TEXT, fontsize=8)
            ax2.set_xlabel('평균 잔여 재고 (발)', color=C_SUBTEXT, fontsize=9)
            ax2.set_title('무기별 평균 잔여 재고', color=C_TEXT, fontsize=10)
            ax2.tick_params(colors=C_SUBTEXT, labelsize=8)
            for sp in ax2.spines.values():
                sp.set_color('#1e2a3a')

        fig.tight_layout()
        self.tab_cost_eff.draw()

    def _draw_ammo_curve(self, mc: dict):
        """🔫 탄약 소모: 무기별 평균 잔여 재고 vs 초기 재고 비교."""
        fig = self.tab_ammo_curve.fig
        fig.clear()
        fig.patch.set_facecolor(C_BG)
        ax = fig.add_subplot(111, facecolor='#0a0e1a')

        wpn_rem = mc.get('weapon_avg_remaining', {})
        if not wpn_rem:
            ax.text(0.5, 0.5, '데이터 없음\n(시뮬레이션 재실행 필요)',
                    ha='center', va='center', color=C_SUBTEXT,
                    fontsize=12, transform=ax.transAxes)
            fig.tight_layout()
            self.tab_ammo_curve.draw()
            return

        names = list(wpn_rem.keys())
        vals  = [wpn_rem[n] for n in names]
        y     = np.arange(len(names))
        bars  = ax.barh(y, vals, color=C_ACCENT, height=0.55, alpha=0.85)
        for bar, val in zip(bars, vals):
            ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
                    f'{val:.1f}', va='center', color=C_TEXT, fontsize=8)
        ax.set_yticks(y)
        ax.set_yticklabels(names, color=C_TEXT, fontsize=8)
        ax.set_xlabel('MC 평균 잔여 재고 (발)', color=C_SUBTEXT, fontsize=9)
        ax.set_title('무기별 평균 잔여 재고 (MC 전체 평균)', color=C_TEXT, fontsize=10)
        ax.tick_params(colors=C_SUBTEXT, labelsize=8)
        for sp in ax.spines.values():
            sp.set_color('#1e2a3a')
        fig.tight_layout()
        self.tab_ammo_curve.draw()

    def _draw_ci_chart(self, mc: dict):
        """📈 MC 95% 신뢰구간: 요격률 분포 히스토그램 + CI 표시."""
        fig = self.tab_ci.fig
        fig.clear()
        fig.patch.set_facecolor(C_BG)

        rates = mc.get('intercept_rates', [])
        if not rates:
            ax = fig.add_subplot(111, facecolor='#0a0e1a')
            ax.text(0.5, 0.5, '데이터 없음', ha='center', va='center',
                    color=C_SUBTEXT, fontsize=12, transform=ax.transAxes)
            fig.tight_layout()
            self.tab_ci.draw()
            return

        arr   = np.array(rates)
        mean  = float(arr.mean())
        std   = float(arr.std())
        ci_lo = max(0.0, mean - 1.96 * std / np.sqrt(len(arr)))
        ci_hi = min(1.0, mean + 1.96 * std / np.sqrt(len(arr)))

        gs = fig.add_gridspec(1, 2, wspace=0.35)
        ax1 = fig.add_subplot(gs[0], facecolor='#0a0e1a')
        ax2 = fig.add_subplot(gs[1], facecolor='#0a0e1a')

        # 히스토그램
        ax1.hist(arr, bins=20, color=C_ACCENT, alpha=0.75, edgecolor='#1e2a3a')
        ax1.axvline(mean,  color=C_GREEN,  lw=2, label=f'평균 {mean:.1%}')
        ax1.axvline(ci_lo, color=C_ORANGE, lw=1.5, ls='--', label=f'CI 하한 {ci_lo:.1%}')
        ax1.axvline(ci_hi, color=C_ORANGE, lw=1.5, ls='--', label=f'CI 상한 {ci_hi:.1%}')
        ax1.set_xlabel('요격률', color=C_SUBTEXT, fontsize=9)
        ax1.set_ylabel('빈도', color=C_SUBTEXT, fontsize=9)
        ax1.set_title(f'요격률 분포 (n={len(arr)})', color=C_TEXT, fontsize=10)
        ax1.legend(fontsize=8, facecolor='#0a0e1a', labelcolor=C_TEXT, edgecolor='#1e2a3a')
        ax1.tick_params(colors=C_SUBTEXT, labelsize=8)
        for sp in ax1.spines.values(): sp.set_color('#1e2a3a')

        # 함정별 평균 피격
        ship_hits = mc.get('ship_avg_hits', {})
        if ship_hits:
            snames = list(ship_hits.keys())
            shvals = [ship_hits[s] for s in snames]
            y      = np.arange(len(snames))
            clrs   = [C_RED if v > 1 else C_ORANGE if v > 0 else C_GREEN for v in shvals]
            ax2.barh(y, shvals, color=clrs, height=0.55)
            ax2.set_yticks(y)
            ax2.set_yticklabels(snames, color=C_TEXT, fontsize=8)
            ax2.set_xlabel('평균 피격 횟수', color=C_SUBTEXT, fontsize=9)
            ax2.set_title('함정별 평균 피격', color=C_TEXT, fontsize=10)
            ax2.tick_params(colors=C_SUBTEXT, labelsize=8)
            for sp in ax2.spines.values(): sp.set_color('#1e2a3a')
        else:
            ax2.axis('off')
            ax2.text(0.5, 0.5, '피격 데이터 없음', ha='center', va='center',
                     color=C_SUBTEXT, fontsize=10, transform=ax2.transAxes)

        fig.tight_layout()
        self.tab_ci.draw()

    def _draw_timeline(self, result: dict):
        """⏱️ 교전 타임라인: 무기 발사/요격/피격 이벤트 Gantt형 시각화."""
        log = result.get('log', [])
        fig = self.tab_timeline.fig
        fig.clear()
        fig.patch.set_facecolor(C_BG)
        ax = fig.add_subplot(111, facecolor='#0a0e1a')

        if not log:
            ax.text(0.5, 0.5, '로그 데이터 없음', ha='center', va='center',
                    color=C_SUBTEXT, fontsize=12, transform=ax.transAxes)
            fig.tight_layout()
            self.tab_timeline.draw()
            return

        # 이벤트 분류: (시각, 카테고리, 텍스트)
        _CAT = [
            ('[방어]',     C_GREEN,  '방어 발사',   0),
            ('[대공 방어]', C_ACCENT, '대공 발사',   1),
            ('[공격]',     '#e67e22','대함 공격',   2),
            ('[대잠 공격]', '#9b59b6','대잠 공격',   3),
            ('[피격]',     C_RED,    '피격',        4),
            ('[경고]',     C_ORANGE, '경고',        5),
            ('[적 발사]',  '#c0392b','적 발사',     6),
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
            self.tab_timeline.draw()
            return

        y_labels = ['방어 발사', '대공 발사', '대함 공격', '대잠 공격', '피격', '경고', '적 발사']
        for t, yi, color, label, msg in events:
            ax.scatter(t, yi, c=color, s=30, zorder=3, alpha=0.8)

        ax.set_yticks(range(len(y_labels)))
        ax.set_yticklabels(y_labels, color=C_TEXT, fontsize=9)
        ax.set_xlabel('시뮬 시각 (초)', color=C_SUBTEXT, fontsize=9)
        ax.set_title('교전 이벤트 타임라인', color=C_TEXT, fontsize=11)
        ax.tick_params(colors=C_SUBTEXT, labelsize=8)
        ax.set_ylim(-0.8, len(y_labels) - 0.2)
        for sp in ax.spines.values(): sp.set_color('#1e2a3a')
        ax.grid(axis='x', color='#1e2a3a', lw=0.5)

        # 범례
        handles = [plt.Line2D([0], [0], marker='o', color='w',
                               markerfacecolor=c, markersize=7, label=l)
                   for _, c, l, _ in _CAT]
        ax.legend(handles=handles, fontsize=7, facecolor='#0a0e1a',
                  labelcolor=C_TEXT, edgecolor='#1e2a3a',
                  loc='upper right', ncol=4)
        fig.tight_layout()
        self.tab_timeline.draw()

    def _draw_sensitivity(self, base_cfg: dict, mc_n: int):
        """감도 분석 — 파라미터별 요격률 변화 Tornado chart."""
        if not _V7_OK:
            return
        fig = self.tab_sensitivity.fig
        fig.clear()
        ax = fig.add_subplot(111)
        ax.set_facecolor('#0a0e1a')
        fig.patch.set_facecolor('#0a0e1a')

        params = [
            ('C&D 시간',   'cd_time_s',      5, 20, 10),
            ('확인 시간',  'confirm_time_s',  1, 10,  3),
            ('MC 시드',    'sim_seed',         1, 42,  0),
        ]

        base_mc = monte_carlo_v7(base_cfg, mc_n // 5 or 50)
        base_rate = base_mc['mean_intercept']

        labels, lows, highs = [], [], []
        for name, key, lo_val, hi_val, _ in params:
            cfg_lo = {**base_cfg, key: lo_val}
            cfg_hi = {**base_cfg, key: hi_val}
            try:
                r_lo = monte_carlo_v7(cfg_lo, mc_n // 5 or 50)['mean_intercept']
                r_hi = monte_carlo_v7(cfg_hi, mc_n // 5 or 50)['mean_intercept']
            except Exception:
                r_lo = r_hi = base_rate
            labels.append(f"{name}\n({lo_val}→{hi_val})")
            lows.append(r_lo - base_rate)
            highs.append(r_hi - base_rate)

        y = range(len(labels))
        bars_lo = ax.barh(list(y), lows,  color='#e74c3c', alpha=0.8, label='낮은값')
        bars_hi = ax.barh(list(y), highs, color='#2ecc71', alpha=0.8, label='높은값')
        ax.axvline(0, color=C_TEXT, lw=1)
        ax.set_yticks(list(y))
        ax.set_yticklabels(labels, color=C_TEXT, fontsize=9)
        ax.set_xlabel('요격률 변화 (기준 대비)', color=C_SUBTEXT, fontsize=9)
        ax.set_title(f'감도 분석 — Tornado chart  (기준 요격률 {base_rate:.1%})',
                     color=C_TEXT, fontsize=11)
        ax.tick_params(colors=C_SUBTEXT)
        ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:+.1%}"))
        for sp in ax.spines.values(): sp.set_color('#1e2a3a')
        ax.legend(fontsize=8, facecolor='#0a0e1a', labelcolor=C_TEXT,
                  edgecolor='#1e2a3a')
        fig.tight_layout()
        self.tab_sensitivity.draw()

    def _draw_bearing_vulnerability(self, result: dict):
        """방위각 취약점 — 방향별 피격/요격률 레이더차트."""
        if not _V7_OK:
            return
        fig = self.tab_bearing.fig
        fig.clear()
        ax = fig.add_subplot(111, polar=True)
        ax.set_facecolor('#0a0e1a')
        fig.patch.set_facecolor('#0a0e1a')

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

        angles = np.linspace(0, 2 * np.pi, N, endpoint=False)
        hit_arr  = np.array(hit_counts,  dtype=float)
        kill_arr = np.array(kill_counts, dtype=float)
        max_val  = max(hit_arr.max(), kill_arr.max(), 1)
        hit_arr  /= max_val
        kill_arr /= max_val
        angles_c = np.concatenate([angles, [angles[0]]])
        hit_c    = np.concatenate([hit_arr, [hit_arr[0]]])
        kill_c   = np.concatenate([kill_arr,[kill_arr[0]]])
        sector_labels = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']

        ax.plot(angles_c, kill_c, 'o-', color='#2ecc71', lw=1.5, label='요격')
        ax.fill(angles_c, kill_c, alpha=0.2, color='#2ecc71')
        ax.plot(angles_c, hit_c,  'o-', color='#e74c3c', lw=1.5, label='피격')
        ax.fill(angles_c, hit_c,  alpha=0.2, color='#e74c3c')
        ax.set_xticks(angles)
        ax.set_xticklabels(sector_labels, color=C_TEXT, fontsize=9)
        ax.set_yticklabels([])
        ax.set_title('방위각 취약점 분석', color=C_TEXT, fontsize=11, pad=15)
        ax.tick_params(colors=C_SUBTEXT)
        ax.spines['polar'].set_color('#1e2a3a')
        ax.grid(color='#1e2a3a')
        ax.legend(loc='upper right', fontsize=8, facecolor='#0a0e1a',
                  labelcolor=C_TEXT, edgecolor='#1e2a3a',
                  bbox_to_anchor=(1.25, 1.1))
        fig.tight_layout()
        self.tab_bearing.draw()

    def _draw_req_radar(self, result: dict, mc: dict):
        """REQ 충족률 레이더 차트 — 요구조건별 충족도 방사형."""
        if not _V7_OK:
            return
        try:
            verdicts, _ = evaluate_req_v7(result, mc)
        except Exception:
            return

        fig = self.tab_req_radar.fig
        fig.clear()
        ax = fig.add_subplot(111, polar=True)
        ax.set_facecolor('#0a0e1a')
        fig.patch.set_facecolor('#0a0e1a')

        labels = [r['id'] for r in REQ_ITEMS_V7]
        N = len(labels)
        if N == 0:
            return
        vals = [1.0 if v else 0.0 for v in verdicts]
        angles = np.linspace(0, 2 * np.pi, N, endpoint=False)
        vals_c   = np.concatenate([vals,   [vals[0]]])
        angles_c = np.concatenate([angles, [angles[0]]])

        ax.plot(angles_c, vals_c, 'o-', color=C_ACCENT, lw=2)
        ax.fill(angles_c, vals_c, alpha=0.3, color=C_ACCENT)
        ax.set_xticks(angles)
        ax.set_xticklabels(labels, color=C_TEXT, fontsize=9)
        ax.set_yticks([0, 0.5, 1.0])
        ax.set_yticklabels(['FAIL', '', 'PASS'], color=C_SUBTEXT, fontsize=7)
        ax.set_ylim(0, 1.2)
        pass_cnt = sum(verdicts)
        ax.set_title(f'REQ 충족률  {pass_cnt}/{N}  ({pass_cnt/N:.0%})',
                     color=C_TEXT, fontsize=11, pad=15)
        ax.spines['polar'].set_color('#1e2a3a')
        ax.grid(color='#1e2a3a')
        fig.tight_layout()
        self.tab_req_radar.draw()

    def _draw_threat_type(self, result: dict, mc: dict):
        """위협 유형별 요격률 — 항공기·탄도탄·순항미사일·잠수함 분류."""
        if not _V7_OK:
            return
        fig = self.tab_threat_type.fig
        fig.clear()
        ax = fig.add_subplot(111)
        ax.set_facecolor('#0a0e1a')
        fig.patch.set_facecolor('#0a0e1a')

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
            self.tab_threat_type.draw()
            return

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
                    ha='center', va='bottom', color=C_TEXT, fontsize=9)
        ax.set_ylim(0, 1.2)
        ax.set_ylabel('요격률', color=C_SUBTEXT, fontsize=9)
        ax.set_title('위협 유형별 요격률', color=C_TEXT, fontsize=11)
        ax.tick_params(colors=C_SUBTEXT)
        for sp in ax.spines.values(): sp.set_color('#1e2a3a')
        ax.axhline(0.9, color='#2ecc71', lw=1, ls='--', alpha=0.5, label='목표 90%')
        ax.legend(fontsize=8, facecolor='#0a0e1a', labelcolor=C_TEXT,
                  edgecolor='#1e2a3a')
        fig.tight_layout()
        self.tab_threat_type.draw()


# ════════════════════════════════════════════════════════════════════════════
#  SplashWindow — 런처 화면
# ════════════════════════════════════════════════════════════════════════════

_FEATURES = [
    ("🗺️  전장 애니메이션",    "2.5D 등각투영, 줌/속도 조절, 격추 북마크, 스크린샷"),
    ("📊  MC 통계",           "N회 몬테카를로 분석, 요격률 분포, 비용 통계"),
    ("✅  REQ 판정",           "REQ-01~08 요구조건 자동 판정"),
    ("🌤️  날씨 비교",          "맑음/흐림/폭풍 3종 MC 비교, 무기 소모·피격 통계"),
    ("🆚  A vs B",            "두 시나리오 MC 결과 자동 비교 (Δ요격률·Δ비용)"),
    ("📜  교전 로그",          "시각별 발사·요격·피격 이벤트 전체 기록"),
    ("📡  채널 포화도",         "함정별 채널 사용률 시계열 히트맵"),
    ("💰  비용 효과",          "격추당 비용 ($) + 무기별 잔여 재고"),
    ("🔫  탄약 소모",          "MC 평균 잔여 재고 가로 막대"),
    ("📈  MC 신뢰구간",        "95%CI 히스토그램 + 함정별 피격 횟수"),
    ("🖥️  시스템 모니터",       "CPU·RAM 실시간 + 시뮬 구간 하이라이트"),
    ("⚙️  엔진 현실성",         "C&D 딜레이·VLS 간격·부분 피해·SM-6 대함·Mk.45"),
]


class SplashWindow(QWidget):
    """프로그램 진입 런처. [시뮬레이터 시작] → MainWindow 열기."""

    launch_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("이지스 기동전단 통합 방어 시뮬레이터")
        self.setFixedSize(820, 600)
        self.setStyleSheet(f"""
            QWidget {{ background: {C_BG}; color: {C_TEXT};
                       font-family: 'Malgun Gothic', 'Segoe UI'; font-size: 13px; }}
            QTabWidget::pane {{ border: 1px solid {C_BORDER}; background: {C_BG}; }}
            QTabBar::tab {{ background: {C_PANEL}; color: {C_SUBTEXT};
                            padding: 6px 18px; border: 1px solid {C_BORDER}; }}
            QTabBar::tab:selected {{ background: {C_BG}; color: {C_ACCENT};
                                     border-bottom: 2px solid {C_ACCENT}; }}
            QPushButton {{ background: {C_ACCENT}; color: white; border: none;
                           padding: 10px 28px; border-radius: 5px; font-size: 14px; }}
            QPushButton:hover {{ background: #2980b9; }}
            QTableWidget {{ background: {C_PANEL}; gridline-color: {C_BORDER};
                            border: none; font-size: 11px; }}
            QHeaderView::section {{ background: {C_PANEL}; color: {C_ACCENT};
                                    border: none; padding: 4px; font-size: 11px; }}
        """)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        title = QLabel("⚓ 이지스 기동전단 통합 방어 시뮬레이터")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont('Malgun Gothic', 16, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {C_ACCENT}; padding: 4px;")
        layout.addWidget(title)

        sub = QLabel("v7.0  |  PyQt6 네이티브 UI  |  한국 해군 이지스 기동전단 다층 방어 시뮬레이터")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet(f"color: {C_SUBTEXT}; font-size: 11px;")
        layout.addWidget(sub)

        tabs = QTabWidget()
        layout.addWidget(tabs, stretch=1)
        tabs.addTab(self._build_feature_tab(),   "📋  탑재 기능")
        tabs.addTab(self._build_changelog_tab(), "📝  패치 내역")

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
        tbl.setColumnWidth(0, 180)
        tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tbl.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        tbl.verticalHeader().setVisible(False)
        tbl.setAlternatingRowColors(True)
        tbl.setStyleSheet(
            f"alternate-background-color: {C_PANEL}; background-color: {C_BG};")
        for row, (name, desc) in enumerate(_FEATURES):
            ni = QTableWidgetItem(name)
            ni.setForeground(QColor(C_ACCENT))
            tbl.setItem(row, 0, ni)
            tbl.setItem(row, 1, QTableWidgetItem(desc))
        layout.addWidget(tbl)
        return w

    def _build_changelog_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        changelog = []
        cl_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'changelog.json')
        if os.path.exists(cl_path):
            try:
                with open(cl_path, encoding='utf-8') as f:
                    changelog = json.load(f)
            except Exception:
                pass
        if not changelog:
            layout.addWidget(QLabel("changelog.json 없음"))
            return w
        tbl = QTableWidget()
        tbl.setColumnCount(3)
        tbl.setHorizontalHeaderLabels(["버전", "날짜", "변경 내용"])
        hh = tbl.horizontalHeader()
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        tbl.setColumnWidth(0, 160)
        tbl.setColumnWidth(1, 100)
        tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tbl.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        tbl.verticalHeader().setVisible(False)
        tbl.setAlternatingRowColors(True)
        tbl.setStyleSheet(
            f"alternate-background-color: {C_PANEL}; background-color: {C_BG};")
        for entry in reversed(changelog):
            ver   = entry.get('version', '')
            date  = entry.get('date', '')
            items = entry.get('changes', [])
            for i, item in enumerate(items):
                row = tbl.rowCount()
                tbl.insertRow(row)
                if i == 0:
                    vi = QTableWidgetItem(ver)
                    vi.setForeground(QColor(C_ACCENT))
                    tbl.setItem(row, 0, vi)
                    di = QTableWidgetItem(date)
                    di.setForeground(QColor(C_SUBTEXT))
                    tbl.setItem(row, 1, di)
                else:
                    tbl.setItem(row, 0, QTableWidgetItem(""))
                    tbl.setItem(row, 1, QTableWidgetItem(""))
                tbl.setItem(row, 2, QTableWidgetItem(item))
        layout.addWidget(tbl)
        return w


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

    _main_win: list = []  # mutable closure

    def _launch():
        splash.close()
        win = MainWindow()
        _main_win.append(win)
        win.show()

    splash = SplashWindow()
    splash.launch_requested.connect(_launch)
    splash.show()
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
