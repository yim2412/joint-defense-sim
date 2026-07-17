"""
ui_widgets — 런처의 재사용 위젯 계층.

app_main.py에서 분리. 스크롤 오조작 방지 콤보/스핀, 작업표시줄 진행률, 게이지·수렴·
히스토그램 위젯.

의존은 PyQt6·numpy와 app_utils._res·app_theme 색상뿐이다. **app_main을 import하지 말 것**
(즉시 순환). 새 위젯을 여기 추가할 때도 같은 규칙을 지킨다.

CLAUDE.md 규칙: 콤보박스는 항상 NoScrollComboBox를 쓴다(QComboBox 직접 사용 금지 —
스크롤 휠로 값이 의도치 않게 바뀌는 것을 방지).
"""

import sys, ctypes            # _TaskbarProgress의 Windows 작업표시줄 COM 호출용

from PyQt6.QtWidgets import (
    QWidget, QMainWindow, QLabel, QPushButton, QComboBox, QSpinBox, QLineEdit,
    QGroupBox, QProgressBar, QSlider, QScrollBar, QStatusBar, QTabBar, QTabWidget,
    QTableWidget, QHeaderView, QAbstractItemView, QToolTip,
)
from PyQt6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PyQt6.QtCore import Qt, QRectF
import numpy as np

from app_utils import _res
from app_theme import (C_BG, C_PANEL, C_BORDER, C_ACCENT, C_TEXT, C_SUBTEXT,
                       C_GREEN, C_RED, C_ORANGE)

class NoScrollSpinBox(QSpinBox):
    """마우스 휠로 값이 변하지 않는 SpinBox."""
    def wheelEvent(self, event):
        event.ignore()


class NoScrollComboBox(QComboBox):
    """마우스 휠로 항목이 바뀌지 않는 ComboBox."""
    def wheelEvent(self, event):
        event.ignore()


class _TaskbarProgress:
    """Windows 작업표시줄 진행바 (ITaskbarList3) — 창 최소화 중에도 아이콘에 진행률 표시.
    COM을 ctypes로 직접 호출. 초기화/호출 실패 시 모든 동작이 무해한 no-op."""
    _NOPROGRESS = 0
    _NORMAL     = 0x2

    def __init__(self):
        self._ok = False
        self._tbl = None
        self._set_value = None
        self._set_state = None
        if sys.platform != 'win32':
            return
        try:
            import ctypes
            from ctypes import wintypes, POINTER, c_void_p, byref

            class GUID(ctypes.Structure):
                _fields_ = [('Data1', wintypes.DWORD), ('Data2', wintypes.WORD),
                            ('Data3', wintypes.WORD), ('Data4', ctypes.c_ubyte * 8)]

            def _g(d1, d2, d3, rest):
                g = GUID(); g.Data1 = d1; g.Data2 = d2; g.Data3 = d3
                for i, b in enumerate(rest):
                    g.Data4[i] = b
                return g

            CLSID = _g(0x56FDF344, 0xFD6D, 0x11d0, (0x95, 0x8A, 0x00, 0x60, 0x97, 0xC9, 0xA0, 0x90))
            IID   = _g(0xea1afb91, 0x9e28, 0x4b86, (0x90, 0xe9, 0x9e, 0x9f, 0x8a, 0x5e, 0xef, 0xaf))
            ole32 = ctypes.windll.ole32
            ole32.CoInitialize(None)
            ptr = c_void_p()
            if ole32.CoCreateInstance(byref(CLSID), None, 1, byref(IID), byref(ptr)) != 0 or not ptr.value:
                return
            vtbl  = ctypes.cast(ptr, POINTER(c_void_p))[0]
            funcs = ctypes.cast(vtbl, POINTER(c_void_p))
            # vtable: 3=HrInit, 9=SetProgressValue, 10=SetProgressState
            ctypes.WINFUNCTYPE(ctypes.c_long, c_void_p)(funcs[3])(ptr)
            self._set_value = ctypes.WINFUNCTYPE(
                ctypes.c_long, c_void_p, wintypes.HWND, ctypes.c_ulonglong, ctypes.c_ulonglong)(funcs[9])
            self._set_state = ctypes.WINFUNCTYPE(
                ctypes.c_long, c_void_p, wintypes.HWND, ctypes.c_int)(funcs[10])
            self._tbl = ptr
            self._ok = True
        except Exception:
            self._ok = False

    def set_progress(self, hwnd: int, done: int, total: int):
        if not self._ok or not hwnd or total <= 0:
            return
        try:
            self._set_state(self._tbl, hwnd, self._NORMAL)
            self._set_value(self._tbl, hwnd, int(done), int(total))
        except Exception:
            pass

    def clear(self, hwnd: int):
        if not self._ok or not hwnd:
            return
        try:
            self._set_state(self._tbl, hwnd, self._NOPROGRESS)
        except Exception:
            pass


class GaugeWidget(QWidget):
    """0~100% 값을 반원 아크 게이지로 표시 — matplotlib 없이 QPainter로 경량 렌더.
    임계값 색상(≥90% 녹색·≥60% 주황·미만 적색)으로 헤드라인 지표를 한눈에."""
    def __init__(self, title: str = "요격률", parent=None):
        super().__init__(parent)
        self._value = None     # 0.0~1.0 또는 None(미실행)
        self._title = title
        self.setMinimumSize(132, 80)
        self.setMaximumWidth(160)

    def setValue(self, v):
        self._value = None if v is None else float(v)
        self.update()

    @staticmethod
    def _color(v: float) -> QColor:
        if v >= 0.90:
            return QColor('#2ecc71')
        if v >= 0.60:
            return QColor('#f39c12')
        return QColor('#e74c3c')

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        base_y = h - 16          # 반원 평평한 변(직경)의 y
        d = min(w - 16, (base_y) * 2 - 6)   # 반원 지름
        rect = QRectF((w - d) / 2, base_y - d / 2, d, d)

        # 배경 아크 (윗 반원 180°)
        bg = QPen(QColor('#1e2a3a'), 9)
        bg.setCapStyle(Qt.PenCapStyle.RoundCap)
        p.setPen(bg)
        p.drawArc(rect, 0, 180 * 16)

        if self._value is not None:
            v = max(0.0, min(1.0, self._value))
            fg = QPen(self._color(v), 9)
            fg.setCapStyle(Qt.PenCapStyle.RoundCap)
            p.setPen(fg)
            # 좌(180°)에서 값만큼 시계방향으로 채움
            p.drawArc(rect, 180 * 16, -int(180 * v * 16))
            p.setPen(QColor('#e6edf3'))
            p.setFont(QFont('Malgun Gothic', 16, QFont.Weight.Bold))
            p.drawText(QRectF(0, base_y - d * 0.42, w, d * 0.38),
                       Qt.AlignmentFlag.AlignCenter, f"{v:.0%}")
        else:
            p.setPen(QColor('#7d8590'))
            p.setFont(QFont('Malgun Gothic', 13, QFont.Weight.Bold))
            p.drawText(QRectF(0, base_y - d * 0.42, w, d * 0.38),
                       Qt.AlignmentFlag.AlignCenter, "—")

        p.setPen(QColor('#7d8590'))
        p.setFont(QFont('Malgun Gothic', 9))
        p.drawText(QRectF(0, h - 15, w, 14), Qt.AlignmentFlag.AlignCenter, self._title)
        p.end()

_SPIN_UP   = _res('assets/images/spin_up.png').replace('\\', '/')
_SPIN_DOWN = _res('assets/images/spin_down.png').replace('\\', '/')
STYLE_MAIN = f"""
QMainWindow, QWidget {{
    background-color: {C_BG};
    color: {C_TEXT};
    font-family: 'Malgun Gothic', 'Segoe UI', sans-serif;
    font-size: 17px;
}}
QGroupBox {{
    border: 1px solid {C_BORDER};
    border-radius: 8px;
    margin-top: 12px;
    padding-top: 10px;
    font-weight: bold;
    color: {C_ACCENT};
    font-size: 17px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 2px 8px;
    background: {C_PANEL};
    border-radius: 4px;
    font-family: 'Malgun Gothic', 'Segoe UI', sans-serif;
}}
QComboBox {{
    background-color: {C_PANEL};
    border: 1px solid {C_BORDER};
    border-radius: 6px;
    padding: 6px 12px;
    color: {C_TEXT};
    font-size: 17px;
}}
QSpinBox {{
    background-color: {C_PANEL};
    border: 1px solid {C_BORDER};
    border-radius: 6px;
    padding: 6px 20px 6px 10px;   /* 오른쪽 20px = 증감 버튼(16)+여유, 숫자가 버튼에 가리지 않게 */
    color: {C_TEXT};
    font-size: 17px;
}}
QComboBox::drop-down {{ border: none; width: 22px; }}
QComboBox:hover {{ border-color: #5a6b7a; }}
QComboBox:focus, QComboBox:on {{ border-color: {C_ACCENT}; }}
QComboBox QAbstractItemView {{
    background-color: {C_PANEL};
    color: {C_TEXT};
    border: 1px solid {C_ACCENT};
    border-radius: 8px;
    padding: 5px;
    outline: none;
    font-size: 17px;
}}
QComboBox QAbstractItemView::item {{
    min-height: 32px;
    padding: 4px 12px;
    border-radius: 5px;
    margin: 1px 2px;
}}
QComboBox QAbstractItemView::item:hover {{
    background-color: #1f3a5f;
    color: #ffffff;
}}
QComboBox QAbstractItemView::item:selected {{
    background-color: {C_ACCENT};
    color: #ffffff;
}}
QComboBox::drop-down:hover {{ background: #1f2733; }}
QSpinBox::up-button {{
    subcontrol-origin: border;
    subcontrol-position: top right;
    width: 16px;
    background: #1f2733;
    border-left: 1px solid {C_BORDER};
    border-bottom: 1px solid #11161d;
    border-top-right-radius: 6px;
}}
QSpinBox::down-button {{
    subcontrol-origin: border;
    subcontrol-position: bottom right;
    width: 16px;
    background: #1f2733;
    border-left: 1px solid {C_BORDER};
    border-bottom-right-radius: 6px;
}}
QSpinBox::up-button:hover, QSpinBox::down-button:hover {{ background: #2a3645; }}
QSpinBox::up-button:pressed, QSpinBox::down-button:pressed {{ background: {C_ACCENT}; }}
QSpinBox::up-arrow {{ image: url("{_SPIN_UP}"); width: 10px; height: 10px; }}
QSpinBox::down-arrow {{ image: url("{_SPIN_DOWN}"); width: 10px; height: 10px; }}
QLineEdit {{
    background-color: {C_PANEL};
    border: 1px solid {C_BORDER};
    border-radius: 6px;
    padding: 6px 10px;
    color: {C_TEXT};
    font-size: 17px;
    selection-background-color: {C_ACCENT};
}}
QLineEdit:hover {{ border-color: #5a6b7a; }}
QLineEdit:focus {{ border-color: {C_ACCENT}; }}
QPushButton {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #3ea0e0, stop:1 {C_ACCENT});
    color: white;
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 6px;
    padding: 10px 20px;
    font-weight: bold;
    font-size: 17px;
}}
QPushButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #54aee8, stop:1 #2e8bcf);
    border: 1px solid rgba(255,255,255,0.22);
}}
QPushButton:pressed {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #2980b9, stop:1 #1a6fa3);
    padding-top: 11px; padding-bottom: 9px;   /* 1px 내려앉는 눌림감 */
    border: 1px solid rgba(0,0,0,0.25);
}}
QPushButton:disabled {{
    background: #1c2128;
    color: #545d68;
    border: 1px solid {C_BORDER};
}}
QTabWidget::pane {{
    border: 1px solid {C_BORDER};
    background: {C_BG};
}}
QTabBar::tab {{
    background: {C_PANEL};
    color: {C_SUBTEXT};
    border: 1px solid {C_BORDER};
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 9px 20px;
    margin-right: 2px;
    font-size: 16px;
}}
QTabBar::tab:selected {{
    background: {C_BG};
    color: {C_ACCENT};
    border-bottom: 2px solid {C_ACCENT};
}}
QTabBar::tab:hover:!selected {{
    color: {C_TEXT};
    background: #1c2430;
}}
QTableWidget {{
    background-color: {C_PANEL};
    alternate-background-color: #1b2230;
    gridline-color: #232b35;
    color: {C_TEXT};
    border: none;
    font-size: 16px;
}}
QTableWidget::item {{
    padding: 5px 10px;
    border: none;
}}
QTableWidget::item:hover {{
    background-color: #1f3048;
}}
QTableWidget::item:selected {{
    background-color: #2563a8;
    color: #ffffff;
}}
QHeaderView::section {{
    background-color: {C_BG};
    color: {C_ACCENT};
    border: none;
    border-right: 1px solid {C_BORDER};
    border-bottom: 2px solid {C_ACCENT};
    padding: 8px 10px;
    font-weight: bold;
    font-size: 16px;
}}
QHeaderView::section:last {{
    border-right: none;
}}
QScrollBar:vertical {{
    background: transparent;
    width: 9px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: #3d4a5a;
    border-radius: 3px;
    min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{ background: {C_SUBTEXT}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background: transparent;
    height: 9px;
    margin: 0;
}}
QScrollBar::handle:horizontal {{
    background: #3d4a5a;
    border-radius: 3px;
    min-width: 20px;
}}
QScrollBar::handle:horizontal:hover {{ background: {C_SUBTEXT}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
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


class ConvergenceWidget(QWidget):
    """MC 누적 평균 요격률의 수렴 추이를 라인 그래프로 표시 (경량 QPainter).
    배치마다 set_data로 갱신 — y축 자동 스케일로 수렴 흐름을 한눈에."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: list = []
        self.setMinimumHeight(58)

    def set_data(self, data):
        self._data = list(data)
        self.update()

    def clear(self):
        self._data = []
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor('#0a0e1a'))
        w, h = self.width(), self.height()
        d = self._data
        if len(d) < 2:
            p.setPen(QColor('#7d8590'))
            p.setFont(QFont('Malgun Gothic', 9))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "수렴 그래프 (데이터 수집 중…)")
            p.end()
            return
        m = 6
        x0, y0 = m + 26, m
        pw, ph = w - 2 * m - 30, h - 2 * m - 12
        lo, hi = min(d), max(d)
        if hi - lo < 1e-6:
            lo -= 0.01; hi += 0.01
        pad = (hi - lo) * 0.15
        lo -= pad; hi += pad
        def X(i): return x0 + pw * i / (len(d) - 1)
        def Y(v): return y0 + ph * (1 - (v - lo) / (hi - lo))
        # 축
        p.setPen(QPen(QColor('#1e2a3a'), 1))
        p.drawLine(int(x0), int(y0), int(x0), int(y0 + ph))
        p.drawLine(int(x0), int(y0 + ph), int(x0 + pw), int(y0 + ph))
        # 현재값 기준선
        cur = d[-1]
        yc = Y(cur)
        p.setPen(QPen(QColor('#2ecc71'), 1, Qt.PenStyle.DashLine))
        p.drawLine(int(x0), int(yc), int(x0 + pw), int(yc))
        # 수렴 라인
        path = QPainterPath()
        path.moveTo(X(0), Y(d[0]))
        for i in range(1, len(d)):
            path.lineTo(X(i), Y(d[i]))
        p.setPen(QPen(QColor(C_ACCENT), 1.6))
        p.drawPath(path)
        # 라벨
        p.setPen(QColor('#aab'))
        p.setFont(QFont('Malgun Gothic', 8))
        p.drawText(1, int(yc) + 4, f"{cur:.0%}")
        p.drawText(int(x0), h - 1, "반복→")
        p.end()


class RateHistogramWidget(QWidget):
    """MC 배치별 평균 요격률의 분포를 히스토그램으로 표시 (경량 QPainter).
    수렴 라인이 '평균이 어디로 가나'라면, 이쪽은 '결과가 얼마나 퍼져있나(리스크)'."""
    _BINS = 20

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: list = []
        self.setMinimumHeight(90)

    def set_data(self, data):
        self._data = list(data)
        self.update()

    def clear(self):
        self._data = []
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.fillRect(self.rect(), QColor('#0a0e1a'))
        w, h = self.width(), self.height()
        d = self._data
        if len(d) < 3:
            p.setPen(QColor('#7d8590'))
            p.setFont(QFont('Malgun Gothic', 9))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "요격률 분포 (데이터 수집 중…)")
            p.end()
            return
        m = 6
        x0, y0 = m + 4, m + 2
        pw, ph = w - 2 * m - 8, h - 2 * m - 14
        # 0~100% 고정 구간 binning
        bins = [0] * self._BINS
        for v in d:
            b = min(self._BINS - 1, max(0, int(v * self._BINS)))
            bins[b] += 1
        peak = max(bins) or 1
        bw = pw / self._BINS
        import numpy as _np
        mean_v = float(_np.mean(d))
        # 막대
        for i, c in enumerate(bins):
            if c == 0:
                continue
            bh = ph * c / peak
            bx = x0 + i * bw
            by = y0 + (ph - bh)
            frac = (i + 0.5) / self._BINS
            col = QColor('#2ecc71') if frac >= 0.9 else QColor('#3498db') if frac >= 0.6 else QColor('#e74c3c')
            p.fillRect(int(bx) + 1, int(by), int(bw) - 1, int(bh), col)
        # x축
        p.setPen(QPen(QColor('#1e2a3a'), 1))
        p.drawLine(int(x0), int(y0 + ph), int(x0 + pw), int(y0 + ph))
        # 평균 기준선
        mx = x0 + pw * mean_v
        p.setPen(QPen(QColor('#f3f6fa'), 1, Qt.PenStyle.DashLine))
        p.drawLine(int(mx), int(y0), int(mx), int(y0 + ph))
        # 라벨
        p.setPen(QColor('#aab'))
        p.setFont(QFont('Malgun Gothic', 8))
        p.drawText(int(x0), h - 1, "0%")
        p.drawText(int(x0 + pw) - 26, h - 1, "100%")
        p.drawText(int(min(mx + 2, x0 + pw - 60)), y0 + 9, f"평균 {mean_v:.0%}")
        p.end()


# ════════════════════════════════════════════════════════════════════════════
#  플로팅 모니터 창 (시뮬 중 팝업)
