"""
ui_charts — 차트 렌더·교전 분석 탭 계층.

app_main.py에서 분리. matplotlib 캔버스, 백그라운드 차트 렌더 워커, 차트 페이지,
교전 분석 탭(3D 전장 뷰 포함)과 교전·전장·캠페인 렌더 함수.

의존은 PyQt6·matplotlib·app_theme·app_utils·app_engine(build_czml)뿐 — **app_main을
import하지 말 것**(즉시 순환).

⚠ DPI는 반드시 `app_theme.CHART_DPI`로 **모듈 경유** 참조한다. main()이 화면 크기로
재할당하므로 `from app_theme import CHART_DPI`로 받으면 150에 고정된다.

⚠ `_render_*` 함수는 `_audit_render_smoke.py`가 `getattr(app_main, ...)`으로 꺼낸다 —
app_main이 이 모듈에서 이름을 import해 재노출해야 그 감사가 계속 동작한다.
"""

import io, os, sys, json

from PyQt6.QtWidgets import (
    QWidget, QFrame, QLabel, QVBoxLayout, QSizePolicy, QStackedWidget,
    QTabWidget, QTabBar, QTableWidget, QTableWidgetItem, QHeaderView, QApplication,
)
from PyQt6.QtGui import QColor, QPixmap
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl, QSettings

# 3D 전장용 WebEngine (미설치 환경에서도 앱이 죽지 않도록 가드 — app_main과 동일 규약)
try:
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    _WEBENGINE_OK = True
except Exception:
    QWebEngineView = None
    _WEBENGINE_OK = False

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
import numpy as np

import app_theme
from app_theme import (C_BG, C_PANEL, C_BORDER, C_ACCENT, C_TEXT, C_SUBTEXT,
                       C_GREEN, C_RED, C_ORANGE)
from app_utils import _res, _token_path
from app_engine import (build_czml, plot_v7, evaluate_req_v7, evaluate_req_battle_v7,
                        REQ_ITEMS_V7, _V7_OK)

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
            # app_theme 경유 필수 — 이름 import면 main()의 화면 기반 재할당이 안 보인다
            fig.savefig(buf, format='png', bbox_inches='tight',
                        facecolor=fig.get_facecolor(), dpi=app_theme.CHART_DPI)
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
        # Ignored 정책 + 최소 1x1 — 픽스맵 크기가 레이아웃 최소 크기에 반영되어
        # 큰 화면에서 차트를 본 뒤 창이 그 밑으로 안 줄어들던(무한 증가) 버그 방지
        self._img_lbl.setMinimumSize(1, 1)
        self._img_lbl.setSizePolicy(QSizePolicy.Policy.Ignored,
                                    QSizePolicy.Policy.Ignored)
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


# ════════════════════════════════════════════════════════════════════════════
#  교전 분석 렌더 함수
# ════════════════════════════════════════════════════════════════════════════

_LAYER_ORDER = ['SM-3', 'SM-6', 'SM-2', 'ESSM', '해궁', 'RAM', 'CIWS',
                '홍상어', '청상어', 'Mk.46', '기만/회피']

def _classify_weapon(wpn: str) -> str:
    if not wpn:
        return '기타'
    for layer in _LAYER_ORDER:
        if layer in wpn:
            return layer
    if '기만' in wpn or '회피' in wpn:
        return '기만/회피'
    return wpn.split(' ')[0]

def _render_engagement_funnel(active_events: list) -> 'Figure':
    from matplotlib.figure import Figure as _Fig
    fig = _Fig(figsize=(10, 6), facecolor=C_BG)
    ax  = fig.add_subplot(111, facecolor='#0a0e1a')

    if not active_events:
        ax.text(0.5, 0.5, '교전 데이터 없음', ha='center', va='center',
                color=C_SUBTEXT, fontsize=13, transform=ax.transAxes)
        fig.tight_layout()
        return fig

    total = len([e for e in active_events if e.is_active])
    layer_counts: dict = {}
    missed = 0
    for ev in active_events:
        if not ev.is_active:
            continue
        if not ev.intercepted:
            missed += 1
        else:
            key = _classify_weapon(ev.intercept_weapon or '')
            layer_counts[key] = layer_counts.get(key, 0) + 1

    # 레이어 순서대로 정렬
    ordered = [(l, layer_counts[l]) for l in _LAYER_ORDER if l in layer_counts]
    for k, v in layer_counts.items():
        if k not in _LAYER_ORDER:
            ordered.append((k, v))

    labels  = [l for l, _ in ordered] + (['미격추'] if missed else [])
    counts  = [c for _, c in ordered] + ([missed]  if missed else [])
    colors  = [('#2ecc71' if l != '미격추' else '#e74c3c') for l in labels]

    remaining = total
    bar_data   = []
    for lbl, cnt, col in zip(labels, counts, colors):
        bar_data.append((lbl, remaining, cnt, col))
        remaining -= cnt if lbl != '미격추' else 0

    # 가로 Funnel 바
    y_pos = list(range(len(bar_data)))
    for i, (lbl, rem, cnt, col) in enumerate(bar_data):
        ax.barh(i, rem, color='#1e2a3a', height=0.6, edgecolor='none')
        ax.barh(i, cnt, left=rem - cnt, color=col, height=0.6,
                edgecolor='none', alpha=0.85)
        ax.text(rem - cnt / 2, i, f'{cnt}건',
                ha='center', va='center', color='white',
                fontsize=11, fontweight='bold',
                fontfamily='Malgun Gothic')

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, color=C_TEXT, fontsize=12,
                       fontfamily='Malgun Gothic')
    ax.set_xlabel('위협 수', color=C_SUBTEXT, fontsize=11,
                  fontfamily='Malgun Gothic')
    ax.set_title(f'방어 레이어별 격추 Funnel  (총 {total}건)',
                 color=C_TEXT, fontsize=14, fontfamily='Malgun Gothic')
    ax.tick_params(colors=C_SUBTEXT, labelsize=10)
    ax.set_xlim(0, total + 1)
    for sp in ax.spines.values():
        sp.set_color('#1e2a3a')
    ax.grid(axis='x', color='#1e2a3a', lw=0.5)
    ax.invert_yaxis()
    fig.tight_layout()
    return fig


def _render_engagement_gantt(active_events: list) -> 'Figure':
    from matplotlib.figure import Figure as _Fig
    evs = [e for e in active_events if e.is_active and e.gantt_bars]
    fig_h = max(4, len(evs) * 0.45 + 1.5)
    fig = _Fig(figsize=(14, fig_h), facecolor=C_BG)
    ax  = fig.add_subplot(111, facecolor='#0a0e1a')

    if not evs:
        ax.text(0.5, 0.5, '교전 데이터 없음', ha='center', va='center',
                color=C_SUBTEXT, fontsize=13, transform=ax.transAxes)
        fig.tight_layout()
        return fig

    color_legend = {
        '#2ecc71': '요격 성공', '#e74c3c': '피격/통과',
        '#f39c12': '채널 없음', '#95a5a6': '교전 불가',
        '#16A085': '기만/회피', '#808080': '탐지 중',
    }
    seen_colors: set = set()

    for yi, ev in enumerate(evs):
        for (lbl, t_s, t_e, col) in ev.gantt_bars:
            dur = max(t_e - t_s, 0.5)
            ax.barh(yi, dur, left=t_s, height=0.55, color=col,
                    edgecolor='white', linewidth=0.5, alpha=0.88)
            seen_colors.add(col)
        # 위협 이름 왼쪽 표시
        ax.text(-0.5, yi, ev.label[:18], ha='right', va='center',
                color=C_TEXT, fontsize=8, fontfamily='Malgun Gothic')

    ax.set_yticks(range(len(evs)))
    ax.set_yticklabels([''] * len(evs))
    # B-1: 이름 텍스트가 잘리지 않도록 x축 왼쪽 여백을 이름 최대 길이 기준으로 확보
    max_t = max((max(t_e for _, _, t_e, _ in ev.gantt_bars) for ev in evs), default=100)
    label_chars = max((len(ev.label[:18]) for ev in evs), default=10)
    x_margin = label_chars * 1.2   # 글자당 약 1.2초 여유
    ax.set_xlim(-x_margin, max_t * 1.05)
    ax.set_xlabel('시뮬 시각 (초)', color=C_SUBTEXT, fontsize=11,
                  fontfamily='Malgun Gothic')
    ax.set_title('교전 타임라인 (위협별 교전 구간)',
                 color=C_TEXT, fontsize=14, fontfamily='Malgun Gothic')
    ax.tick_params(colors=C_SUBTEXT, labelsize=10)
    for sp in ax.spines.values():
        sp.set_color('#1e2a3a')
    ax.grid(axis='x', color='#1e2a3a', lw=0.5)
    ax.invert_yaxis()

    handles = [
        __import__('matplotlib.patches', fromlist=['Patch']).Patch(
            facecolor=col, label=lbl, alpha=0.88)
        for col, lbl in color_legend.items()
        if col in seen_colors
    ]
    if handles:
        ax.legend(handles=handles, fontsize=9, facecolor='#0a0e1a',
                  labelcolor=C_TEXT, edgecolor='#1e2a3a',
                  loc='lower right', ncol=3,
                  prop={'family': 'Malgun Gothic', 'size': 9})
    fig.tight_layout()
    return fig


def _render_battle_timeline(result: dict) -> 'Figure':
    """지속 전장 작전 시계열 — 돌파선 침투·전력비·자원 잔여 3종(공통 시간축)."""
    from matplotlib.figure import Figure as _Fig
    tl    = result.get('timeline', {}) or {}
    front = tl.get('frontline_km', [])
    force = tl.get('force_ratio', [])
    res   = tl.get('resource_min', [])
    fig = _Fig(figsize=(14, 9), facecolor=C_BG)

    if not (front or force or res):
        ax = fig.add_subplot(111, facecolor='#0a0e1a')
        ax.text(0.5, 0.5, '작전 시계열은 지속 전장 모드 단일 시뮬에서 표시됩니다',
                ha='center', va='center', color=C_SUBTEXT, fontsize=13,
                transform=ax.transAxes, fontfamily='Malgun Gothic')
        ax.axis('off')
        return fig

    def _style(ax, title, ylabel):
        ax.set_facecolor('#0a0e1a')
        ax.set_title(title, color=C_TEXT, fontsize=13, fontfamily='Malgun Gothic', loc='left')
        ax.set_ylabel(ylabel, color=C_SUBTEXT, fontsize=11, fontfamily='Malgun Gothic')
        ax.tick_params(colors=C_SUBTEXT, labelsize=9)
        for sp in ax.spines.values():
            sp.set_color('#1e2a3a')
        ax.grid(True, color='#1e2a3a', lw=0.5)

    axes = fig.subplots(3, 1, sharex=True)

    # 1. 해역 통제 — 적 최대 침투 (높을수록 기함 근접 = 위험)
    ax = axes[0]
    if front:
        t  = [x[0] for x in front]; km = [x[1] for x in front]
        ax.plot(t, km, color='#e74c3c', lw=1.6)
        ax.fill_between(t, km, color='#e74c3c', alpha=0.15)
    _style(ax, '해역 통제 — 적 최대 침투 (높을수록 위험)', '돌파 침투 (km)')

    # 2. 소모전 — 양측 전력 잔여비
    ax = axes[1]
    if force:
        t = [x[0] for x in force]
        ax.plot(t, [x[1] for x in force], color='#2ecc71', lw=1.6, label='아군')
        ax.plot(t, [x[2] for x in force], color='#e67e22', lw=1.6, label='적')
        ax.set_ylim(0, 1.05)
        ax.legend(fontsize=9, facecolor='#0a0e1a', labelcolor=C_TEXT,
                  edgecolor='#1e2a3a', loc='lower left',
                  prop={'family': 'Malgun Gothic', 'size': 9})
    _style(ax, '소모전 — 양측 전력 잔여', '전력 잔여비')

    # 3. 자원 지속성 — 탄약·연료 잔여비
    ax = axes[2]
    if res:
        t = [x[0] for x in res]
        ax.plot(t, [x[1] for x in res], color='#3498db', lw=1.6, label='탄약')
        ax.plot(t, [x[2] for x in res], color='#f1c40f', lw=1.6, label='연료')
        ax.set_ylim(0, 1.05)
        ax.legend(fontsize=9, facecolor='#0a0e1a', labelcolor=C_TEXT,
                  edgecolor='#1e2a3a', loc='lower left',
                  prop={'family': 'Malgun Gothic', 'size': 9})
    _style(ax, '자원 지속성 — 탄약·연료 잔여', '잔여비')

    axes[2].set_xlabel('작전 시각 (초)', color=C_SUBTEXT, fontsize=11,
                       fontfamily='Malgun Gothic')
    fig.tight_layout()
    return fig


def _render_campaign_report(result: dict) -> 'Figure':
    """v18.7 작전급 캠페인 분석 리포트 — 전역 결과 분포(승/무/패)·교통로별 통제·
    대표 전역 통제도 시계열(승리/무승부 임계선·통제 붕괴 시점). campaign_mc 반복 분포 사용."""
    from matplotlib.figure import Figure as _Fig
    mc   = result.get('campaign_mc') or {}
    tl   = (result.get('timeline', {}) or {}).get('control', []) or []
    ctrl = result.get('control', {}) or {}
    fig = _Fig(figsize=(14, 9), facecolor=C_BG)

    if result.get('mode') != 'campaign':
        ax = fig.add_subplot(111, facecolor='#0a0e1a')
        ax.text(0.5, 0.5, '캠페인 분석은 작전급 캠페인 모드에서 표시됩니다',
                ha='center', va='center', color=C_SUBTEXT, fontsize=13,
                transform=ax.transAxes, fontfamily='Malgun Gothic')
        ax.axis('off')
        return fig

    def _style(ax, title, ylabel='', grid_axis='y'):
        ax.set_facecolor('#0a0e1a')
        ax.set_title(title, color=C_TEXT, fontsize=12.5, fontfamily='Malgun Gothic', loc='left')
        if ylabel:
            ax.set_ylabel(ylabel, color=C_SUBTEXT, fontsize=10.5, fontfamily='Malgun Gothic')
        ax.tick_params(colors=C_SUBTEXT, labelsize=9)
        for sp in ax.spines.values():
            sp.set_color('#1e2a3a')
        ax.grid(True, color='#1e2a3a', lw=0.5, axis=grid_axis)

    axd = fig.subplot_mosaic([['dist', 'zones'], ['ts', 'ts']],
                             gridspec_kw={'height_ratios': [1.0, 1.1]})

    # A) 전역 결과 분포 (N회 반복)
    ax = axd['dist']
    n_runs = mc.get('n_runs', 0)
    rates  = [mc.get('win_rate', 0) * 100, mc.get('draw_rate', 0) * 100,
              mc.get('loss_rate', 0) * 100]
    bars = ax.bar(['승리', '무승부', '패배'], rates,
                  color=['#2ecc71', '#f1c40f', '#e74c3c'], width=0.6)
    for b, r in zip(bars, rates):
        ax.text(b.get_x() + b.get_width() / 2, r + 1.5, f'{r:.0f}%',
                ha='center', color=C_TEXT, fontsize=11, fontfamily='Malgun Gothic')
    ax.set_ylim(0, 108)
    for lbl in ax.get_xticklabels():
        lbl.set_fontfamily('Malgun Gothic')
    _style(ax, f'전역 결과 분포 ({n_runs}회 반복)', '비율 (%)')

    # B) 교통로별 최종 통제도 (대표 전역)
    ax = axd['zones']
    if ctrl:
        zs = list(ctrl.keys())
        vs = [ctrl[z] * 100 for z in zs]
        bcol = ['#2ecc71' if v >= 70 else '#f1c40f' if v >= 30 else '#e74c3c' for v in vs]
        bars = ax.barh(zs, vs, color=bcol, height=0.55)
        for b, v in zip(bars, vs):
            ax.text(min(v + 2, 90), b.get_y() + b.get_height() / 2, f'{v:.0f}%',
                    va='center', color=C_TEXT, fontsize=10, fontfamily='Malgun Gothic')
        ax.set_xlim(0, 108)
        ax.axvline(70, color='#2ecc71', ls='--', lw=0.8, alpha=0.5)
        ax.axvline(30, color='#e74c3c', ls='--', lw=0.8, alpha=0.5)
        for lbl in ax.get_yticklabels():
            lbl.set_fontfamily('Malgun Gothic')
    _style(ax, '교통로별 통제도 (대표 전역)', '', grid_axis='x')

    # C) 대표 전역(seed 0) 통제도 시계열 + 임계선 + 통제 붕괴 시점
    ax = axd['ts']
    if tl:
        hrs = list(range(1, len(tl) + 1))
        pct = [v * 100 for v in tl]
        ax.plot(hrs, pct, color='#3498db', lw=1.8)
        ax.fill_between(hrs, pct, color='#3498db', alpha=0.12)
        ax.axhline(70, color='#2ecc71', ls='--', lw=0.9, alpha=0.6)
        ax.axhline(30, color='#e74c3c', ls='--', lw=0.9, alpha=0.6)
        ax.text(hrs[-1], 71, '승리선 70% ', color='#2ecc71', fontsize=8.5,
                va='bottom', ha='right', fontfamily='Malgun Gothic')
        ax.text(hrs[-1], 31, '무승부선 30% ', color='#e74c3c', fontsize=8.5,
                va='bottom', ha='right', fontfamily='Malgun Gothic')
        crit = next((h for h, v in zip(hrs, tl) if v < 0.3), None)
        if crit is not None:
            ax.axvline(crit, color='#e67e22', lw=1.2, alpha=0.85)
            ax.text(crit, 99, f' 통제 붕괴 {crit}h', color='#e67e22', fontsize=9,
                    va='top', fontfamily='Malgun Gothic')
        ax.set_ylim(0, 104)
        ax.set_xlim(1, max(hrs[-1], 2))
    ax.set_xlabel('전역 시각 (시간)', color=C_SUBTEXT, fontsize=10.5, fontfamily='Malgun Gothic')
    mc_txt = (f"   ·   MC 평균 통제도 {mc.get('mean_control_avg', 0)*100:.0f}%"
              f"±{mc.get('mean_control_std', 0)*100:.0f} "
              f"({mc.get('mean_control_min', 0)*100:.0f}~{mc.get('mean_control_max', 0)*100:.0f})") if mc else ''
    _style(ax, '대표 전역(seed 0) 교통로 통제도 추이' + mc_txt, '평균 통제도 (%)')

    fig.tight_layout()
    return fig


# ════════════════════════════════════════════════════════════════════════════
#  교전 분석 탭
# ════════════════════════════════════════════════════════════════════════════

class EngagementAnalysisTab(QWidget):
    """교전 분석 탭: 방어 Funnel / 위협 추적 테이블 / 교전 타임라인 Gantt"""

    _COL_HEADERS = ["위협명", "유형", "탐지거리(km)", "결과", "격추무기", "격추거리(km)", "격추시각(s)"]
    _TBL_STYLE = (
        "QTableWidget { background:#0d1117; color:#e6edf3; "
        "gridline-color:#21262d; border:none; font-size:13px; "
        "font-family:'Malgun Gothic'; }"
        "QTableWidget::item { padding:4px 8px; }"
        "QHeaderView::section { background:#161b22; color:#7d8590; "
        "font-size:12px; padding:4px; border:none; "
        "border-bottom:1px solid #30363d; font-family:'Malgun Gothic'; }"
        "QTableWidget::item:selected { background:#1f3a5f; }"
    )

    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        # ── 작전 결과 배너 (지속 전장 모드 전용 — 승/패 + 목표 달성판) ────────
        self._battle_panel = QFrame()
        self._battle_panel.setObjectName("battlePanel")
        bp = QVBoxLayout(self._battle_panel)
        bp.setContentsMargins(14, 10, 14, 12)
        bp.setSpacing(6)
        self._bp_outcome = QLabel()
        bp.addWidget(self._bp_outcome)
        self._bp_score = QLabel()
        self._bp_score.setStyleSheet(f"color:{C_SUBTEXT}; font-size:14px; font-family:'Malgun Gothic';")
        bp.addWidget(self._bp_score)
        self._bp_obj = QLabel()
        self._bp_obj.setWordWrap(True)
        self._bp_obj.setStyleSheet("color:#e6edf3; font-size:14px; font-family:'Malgun Gothic';")
        bp.addWidget(self._bp_obj)
        self._battle_panel.hide()
        layout.addWidget(self._battle_panel)

        tabs = QTabWidget()
        tabs.setStyleSheet(
            f"QTabWidget::pane {{ border:1px solid #30363d; background:{C_BG}; }}"
            f"QTabBar::tab {{ background:#161b22; color:#7d8590; "
            f"padding:6px 14px; font-size:14px; font-family:'Malgun Gothic'; }}"
            f"QTabBar::tab:selected {{ background:{C_BG}; color:{C_ACCENT}; "
            f"border-bottom:2px solid {C_ACCENT}; }}"
        )

        # ── Sub-tab 1: Funnel ──────────────────────────────────────────────
        self._tab_funnel = ChartPageWidget()
        tabs.addTab(self._tab_funnel, "🔻  방어 Funnel")

        # ── Sub-tab 2: 위협 추적 테이블 ────────────────────────────────────
        tbl_widget = QWidget()
        tbl_layout = QVBoxLayout(tbl_widget)
        tbl_layout.setContentsMargins(4, 4, 4, 4)
        self._table = QTableWidget(0, len(self._COL_HEADERS))
        self._table.setHorizontalHeaderLabels(self._COL_HEADERS)
        self._table.setStyleSheet(self._TBL_STYLE)
        self._table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeMode.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.setStyleSheet(self._TBL_STYLE +
            "QTableWidget { alternate-background-color:#0f1620; }")
        tbl_layout.addWidget(self._table)
        tabs.addTab(tbl_widget, "📋  위협 추적")

        # ── Sub-tab 3: Gantt ───────────────────────────────────────────────
        self._tab_gantt = ChartPageWidget()
        tabs.addTab(self._tab_gantt, "⏱  교전 타임라인")

        # ── Sub-tab 4: 작전 시계열 (지속 전장 — 돌파선·전력비·자원) ─────────
        self._tab_btimeline = ChartPageWidget()
        tabs.addTab(self._tab_btimeline, "📈  작전 시계열")

        # ── Sub-tab 5: 캠페인 분석 (v18.7 — 전역 결과 분포·통제도 추이) ──────
        self._tab_campaign = ChartPageWidget()
        tabs.addTab(self._tab_campaign, "🗺  캠페인 분석")

        # ── Sub-tab 6: 3D 전장 (CesiumJS) ──────────────────────────────────
        tabs.addTab(self._build_3d_tab(), "🌐  3D 전장")

        layout.addWidget(tabs)

        # 초기 안내
        self._lbl_empty = QLabel("시뮬레이션을 실행하면 교전 분석이 표시됩니다.")
        self._lbl_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_empty.setStyleSheet(
            f"color:{C_SUBTEXT}; font-size:14px; font-family:'Malgun Gothic';")
        layout.addWidget(self._lbl_empty)
        tabs.hide()
        self._tabs_widget = tabs

    # ── 3D 전장 (CesiumJS) ─────────────────────────────────────────────────
    def _build_3d_tab(self) -> QWidget:
        """CesiumJS 3D 전장 서브탭. 시뮬 결과를 CZML로 변환해 시간순 리플레이."""
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 0, 0, 0)
        self._web3d = None
        self._web3d_ready = False
        self._czml_pending = None

        if not _WEBENGINE_OK:
            lbl = QLabel("3D 전장은 PyQt6-WebEngine 설치가 필요합니다.\n"
                         "pip install PyQt6-WebEngine")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(f"color:{C_SUBTEXT}; font-size:14px; font-family:'Malgun Gothic';")
            lay.addWidget(lbl)
            return w

        token = ''
        try:
            with open(_token_path(), encoding='utf-8') as f:
                token = f.read().strip()
        except Exception:
            pass
        try:
            with open(_res('view_cesium_3d.html'), encoding='utf-8') as f:
                html = f.read().replace('__CESIUM_ION_TOKEN__', token)
        except Exception:
            html = ("<html><body style='background:#0b1a2b;color:#ddd;font-family:sans-serif'>"
                    "view_cesium_3d.html 로드 실패</body></html>")

        self._web3d = QWebEngineView()

        def _on_load(ok):
            self._web3d_ready = bool(ok)
            if ok and self._czml_pending is not None:
                self._inject_czml(self._czml_pending)
                self._czml_pending = None

        self._web3d.loadFinished.connect(_on_load)
        self._web3d.setHtml(html, QUrl("https://localhost/"))
        lay.addWidget(self._web3d)
        return w

    def _inject_czml(self, czml: list):
        if self._web3d is None:
            return
        payload = json.dumps(czml, ensure_ascii=False)
        self._web3d.page().runJavaScript(f"loadCzml({payload})")

    def _load_3d(self, result: dict):
        """시뮬 결과 → CZML 주입. 페이지 로드 전이면 보류 후 loadFinished에서 주입."""
        if self._web3d is None:
            return
        try:
            czml = build_czml(result)
        except Exception:
            return
        if self._web3d_ready:
            self._inject_czml(czml)
        else:
            self._czml_pending = czml

    def load_result(self, result: dict):
        active_events = result.get('active_events', [])
        self._lbl_empty.hide()
        self._tabs_widget.show()
        self._fill_battle_panel(result)

        # Funnel & Gantt — 백그라운드 렌더
        self._tab_funnel.start_render(_render_engagement_funnel, active_events)
        self._tab_gantt.start_render(_render_engagement_gantt, active_events)

        # 작전 시계열 — 전장 모드 timeline(돌파선·전력비·자원). 단발/MC는 안내문 표시
        self._tab_btimeline.start_render(_render_battle_timeline, result)

        # v18.7: 캠페인 분석 — 전역 결과 분포·통제도 추이(캠페인 모드만, 그 외 안내문)
        self._tab_campaign.start_render(_render_campaign_report, result)

        # 3D 전장 — frames → CZML 주입 (단일 시뮬만, MC는 frames 없어 document만)
        self._load_3d(result)

        # 위협 추적 테이블 — 메인 스레드 직접 채움
        self._fill_table(active_events)

    def _fill_battle_panel(self, result: dict):
        """지속 전장 모드 — 작전 결과(승/패) + 목표 달성판. 단발 모드면 숨김."""
        outcome = result.get('outcome')
        if not outcome:
            self._battle_panel.hide()
            return
        _map = {'win': ('🟢 승리', '#2ecc71'), 'loss': ('🔴 패배', '#e74c3c'),
                'draw': ('🟡 무승부', '#f1c40f')}
        label, color = _map.get(outcome, (outcome, C_SUBTEXT))
        self._battle_panel.setStyleSheet(
            f"QFrame#battlePanel {{ background:#161d2a; border-radius:8px;"
            f" border-left:5px solid {color}; }}"
            f"QFrame#battlePanel QLabel {{ background:transparent; }}")

        # v18.1: 작전급 캠페인 요약(교통로 통제·교전·생존). 전장 목표판과 다른 지표.
        # v18.6: campaign_mc가 있으면 N회 반복 분포(승/무/패)+평균 지표로 표시.
        if result.get('mode') == 'campaign':
            # v19.1: 공군 제공권 요약(공군 층 ON일 때만) — 대표 전역 zone별 제공권
            _air_txt = ''
            if result.get('air_enabled'):
                _as = result.get('air_superiority', {})
                _al = [f"{'🟢' if v >= 0.6 else '🟠' if v >= 0.4 else '🔴'} {z} {v*100:.0f}%"
                       for z, v in _as.items()]
                _air_txt = ('        ✈ 제공권: ' + '  '.join(_al) +
                            f"  (소티 {result.get('air_sorties', 0)}회)")
                if result.get('sead_enabled'):   # v19.3: 방공망 제압 상태
                    _air_txt += (f"  ·  🎯 방공망 {result.get('n_ad_sites', 0)}개 "
                                 f"제압 {result.get('ad_suppression', 0)*100:.0f}%")
                if result.get('strike_enabled'):   # v19.4: 전략폭격 적 기지 손상
                    _air_txt += (f"  ·  💥 적 기지 {result.get('n_enemy_bases', 0)}개 "
                                 f"손상 {result.get('enemy_base_damage', 0)*100:.0f}% "
                                 f"(출항 {result.get('enemy_output_factor', 1)*100:.0f}%)")
                if result.get('n_cas_requests', 0) > 0:   # v19.5: 근접 항공 지원(CAS)
                    _air_txt += (f"  ·  🛩 근접지원 {result.get('air_cas_sorties', 0)}소티 "
                                 f"/ 요청 {result.get('n_cas_requests', 0)}건")
            # v20: 지상군 층 요약(연안 방공망·상륙작전) — 공군 블록과 대칭.
            #   이 지표들이 결과에 안 보이면 연안 요격탄 소모·교두보 확보 여부를 사용자가
            #   전혀 알 수 없다(승패 숫자만 간접적으로 움직임).
            _army_txt = ''
            _csites = result.get('coastal_sites') or {}
            if _csites:
                _rd = [f"{'🟢' if v['readiness'] >= 0.6 else '🟠' if v['readiness'] >= 0.3 else '🔴'}"
                       f" {z} {v['readiness']*100:.0f}%" for z, v in _csites.items()]
                _army_txt = ('        🛡 연안 방공: ' + '  '.join(_rd) +
                             f"  (요격탄 {result.get('coastal_intercepts', 0)}발"
                             f" · ASBM 정밀교전 {result.get('n_asbm_precise', 0)}회)")
                _sup = result.get('coastal_suppression', 0) or 0
                if _sup > 0.01:   # 적 SEAD 도미노가 실제로 작동했을 때만
                    _army_txt += f"  ·  ⚠ 적 SEAD 제압 {_sup*100:.0f}%"
            if result.get('amphib_enabled'):
                _st = {'embark': '⚓ 승선', 'transit': '🚢 항해', 'assault': '🔥 상륙 중',
                       'beachhead': '🚩 교두보 확보', 'failed': '❌ 상륙 실패'}
                _amp = _st.get(result.get('amphib_state', ''), result.get('amphib_state', ''))
                _army_txt += (f"        🏖 상륙({result.get('amphib_zone', '')}): {_amp}"
                              f"  진척 {result.get('amphib_progress', 0)*100:.0f}%")
            # v21.4: 군별 기여도(반사실 분해). 각 군을 뺀 전역을 실제로 다시 돌린 결과라
            #   '누가 몇 발 쐈나'(직접 계상)와 다른 값이다 — 여기 안 띄우면 사용자는
            #   무엇이 전역을 이겼는지 끝내 알 수 없다.
            _joint_txt = ''
            _rep = result.get('joint_report') or {}
            if _rep:
                _lbl = {'strike': '💥 전략폭격', 'army': '🎖 지상 작전급'}
                _shp, _base, _gr = _rep.get('shapley', {}), _rep.get('navy_baseline', {}), _rep.get('grand', {})
                _parts = [f"{_lbl.get(p, p)} 승률 {v.get('win_rate', 0)*100:+.0f}%p"
                          f"(통제 {v.get('mean_control', 0)*100:+.0f}%p)"
                          for p, v in _shp.items()]
                _joint_txt = (f"        📊 군별 기여도 (n={_rep.get('n_runs_per_coalition', 0)}"
                              f"×{_rep.get('n_coalitions', 0)}연합):  "
                              f"해군 단독 승률 {_base.get('win_rate', 0)*100:.0f}%"
                              f" → 합동 {_gr.get('win_rate', 0)*100:.0f}%  ·  " + '  ·  '.join(_parts))
                _sd = _rep.get('sead_domain_effect') or {}
                if _sd:
                    # 기여도 절과 분리해 표기 — 적 방공망을 함께 생성하는 토글이라 성격이 다르다
                    _joint_txt += (f"        ⚠ 방공망 제압 {_sd.get('win_rate', 0)*100:+.0f}%p"
                                   f" (통제 {_sd.get('mean_control', 0)*100:+.0f}%p) —"
                                   f" 적 방공망 동반 생성이라 기여도가 아닌 전장 효과")
            mc = result.get('campaign_mc')
            if mc:
                self._bp_outcome.setText(f"🗺 캠페인 MC ({mc.get('n_runs', 0)}회):  "
                    f"🟢승 {mc.get('win_rate', 0)*100:.0f}%  "
                    f"🟡무 {mc.get('draw_rate', 0)*100:.0f}%  "
                    f"🔴패 {mc.get('loss_rate', 0)*100:.0f}%")
                self._bp_outcome.setStyleSheet(
                    f"color:{color}; font-size:20px; font-weight:bold; font-family:'Malgun Gothic';")
                self._bp_score.setText(
                    f"평균 통제도 {mc.get('mean_control_avg', 0)*100:.0f}%±{mc.get('mean_control_std', 0)*100:.0f}"
                    f" ({mc.get('mean_control_min', 0)*100:.0f}~{mc.get('mean_control_max', 0)*100:.0f})  ·  "
                    f"평균 교전 {mc.get('n_engagements_avg', 0):.1f}회  ·  "
                    f"평균 생존 {mc.get('surviving_avg', 0):.1f}/{result.get('n_ships', 0)}  ·  "
                    f"전역 {result.get('horizon_h', 72)}h  ·  "
                    f"평균 비용 ${mc.get('cost_avg', 0)/1e6:.0f}M")
                _logi = (f"🔀 평균 재배정 {mc.get('n_reassign_avg', 0):.1f}회  ·  "
                         f"🔁 평균 우회보급 {mc.get('n_reroute_avg', 0):.1f}회")
                if mc.get('fog_enabled'):
                    _logi += f"  ·  🌫 안개 ON (평균 과소평가 {mc.get('n_missed_avg', 0):.1f}회)"
                # 대표 전역(seed 0) 교통로별 통제 병기
                _sc = result.get('control', {})
                _sl = [f"{'🟢' if v >= 0.7 else '🟠' if v >= 0.3 else '🔴'} {z} {v*100:.0f}%"
                       for z, v in _sc.items()]
                self._bp_obj.setText(_logi + '        대표 전역(seed 0): ' + '  '.join(_sl)
                                     + _air_txt + _army_txt + _joint_txt)
                self._battle_panel.show()
                return
            self._bp_outcome.setText(f"🗺 캠페인 결과:  {label}")
            self._bp_outcome.setStyleSheet(
                f"color:{color}; font-size:20px; font-weight:bold; font-family:'Malgun Gothic';")
            self._bp_score.setText(
                f"평균 통제도 {result.get('mean_control', 0.0)*100:.0f}%  ·  "
                f"교전 {result.get('n_engagements', 0)}회  ·  "
                f"생존 함정 {result.get('surviving_ships', 0)}/{result.get('n_ships', 0)}  ·  "
                f"전역 {result.get('end_h', 0)}h / {result.get('horizon_h', 72)}h  ·  "
                f"누적 비용 ${result.get('cost_total', 0)/1e6:.0f}M")
            # v18.5: 교통로별 연속 통제도(0~1) — 🟢≥70 · 🟠≥30 · 🔴 미만
            _sc = result.get('control', {})
            _sl = [f"{'🟢' if v >= 0.7 else '🟠' if v >= 0.3 else '🔴'} {z} {v*100:.0f}%"
                   for z, v in _sc.items()]
            # v18.2: 전력 관리 상태(수리·재보급·평균 탄약/연료) + v18.3: 재배정 + v18.5: 우회 보급
            _logi = (f"🔧 수리 {result.get('n_repair', 0)}척  ·  "
                     f"⛽ 재보급 {result.get('n_resupply', 0)}척  ·  "
                     f"🔀 재배정 {result.get('n_reassign', 0)}회  ·  "
                     f"🔁 우회보급 {result.get('n_reroute', 0)}회  ·  "
                     f"탄약 {result.get('mean_ammo', 1.0)*100:.0f}%  ·  "
                     f"연료 {result.get('mean_fuel', 1.0)*100:.0f}%")
            # v18.4: 전장의 안개 상태(적용 시에만)
            if result.get('fog_enabled'):
                _logi += f"  ·  🌫 안개 ON (적 위치 과소평가 {result.get('n_missed', 0)}회)"
            self._bp_obj.setText('      '.join(_sl) + '        ' + _logi + _air_txt + _army_txt)
            self._battle_panel.show()
            return

        self._bp_outcome.setText(f"⚔ 작전 결과:  {label}")
        self._bp_outcome.setStyleSheet(
            f"color:{color}; font-size:20px; font-weight:bold; font-family:'Malgun Gothic';")
        self._bp_score.setText(
            f"아군 임무 점수 {result.get('friendly_score', 0.0):.0%}  ·  "
            f"적 임무 점수 {result.get('enemy_score', 0.0):.0%}  ·  "
            f"작전 시간 {result.get('sim_time', 0):.0f}s / 지평 {int(result.get('battle_horizon_s', 0))}s")
        _otype = {'defend_asset': '자산 방어', 'destroy_asset': '자산 격침',
                  'sea_control': '해역 통제', 'attrition': '소모전', 'sustainment': '작전 지속성'}
        _ost = {'달성': '✅', '실패': '❌', '진행': '◾'}
        lines = []
        for ob in result.get('objectives', []):
            if ob.get('side') != 'friendly':   # 방어 시뮬 — 아군 목표만 표시
                continue
            nm = _otype.get(ob.get('type'), ob.get('type'))
            st = ob.get('status', '진행')
            lines.append(f"{_ost.get(st, '◾')} {nm} — 달성도 {ob.get('progress', 0):.0%} ({st})")
        self._bp_obj.setText('      '.join(lines))
        self._battle_panel.show()

    def _fill_table(self, active_events: list):
        evs = [e for e in active_events if e.is_active]
        self._table.setRowCount(len(evs))
        for row, ev in enumerate(evs):
            ok      = ev.intercepted
            result_str = '✅ 요격' if ok else '❌ 피격'
            bg      = QColor('#1a3a2a') if ok else QColor('#3a1a1a')

            cells = [
                ev.label,
                ev.enemy_info.get('type', '?'),
                f"{ev.detect_m / 1000:.0f}",
                result_str,
                ev.intercept_weapon or '—',
                f"{ev.intercept_km:.1f}" if ev.intercept_km else '—',
                f"{ev.t_intercepted:.0f}" if ev.t_intercepted else '—',
            ]
            for col, text in enumerate(cells):
                item = QTableWidgetItem(text)
                item.setBackground(bg)
                item.setForeground(QColor(C_TEXT))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._table.setItem(row, col, item)
        self._table.resizeRowsToContents()

    def stop_worker(self):
        self._tab_funnel.stop_worker()
        self._tab_gantt.stop_worker()
        self._tab_btimeline.stop_worker()
        self._tab_campaign.stop_worker()


# ════════════════════════════════════════════════════════════════════════════
#  아코디언 사이드바 (v8.26)


# ── 결과 탭 차트 렌더 (app_main.py에서 이관) ─────────────────────────────────
def _render_fleet_chart(results: dict) -> Figure:
    """적정 편대 추천 — 한국 단독·한미 연합 두 그룹 성능/비용효과 차트."""
    _KRW = 1_350
    kr   = results.get('kr') or []
    comb = results.get('combined') or []

    if not kr and not comb:
        fig = Figure(figsize=(14, 8), facecolor='#0a0e1a')
        ax = fig.add_subplot(111, facecolor='#0a0e1a')
        ax.text(0.5, 0.5, '추천 결과 없음', transform=ax.transAxes,
                ha='center', va='center', color=C_TEXT, fontsize=14)
        ax.axis('off')
        return fig

    from matplotlib.gridspec import GridSpec
    n_kr, n_comb = max(len(kr), 1), max(len(comb), 1)
    fig = Figure(figsize=(15, max(7, 0.7 * (n_kr + n_comb) + 2.5)), facecolor='#0a0e1a')
    fig.patch.set_facecolor('#0a0e1a')
    gs = GridSpec(2, 1, height_ratios=[n_kr, n_comb], hspace=0.35, figure=fig)

    def _draw_group(ax, grp: list, title: str):
        ax.set_facecolor('#0a0e1a')
        if not grp:
            ax.text(0.5, 0.5, '후보 없음', transform=ax.transAxes,
                    ha='center', va='center', color=C_SUBTEXT, fontsize=12)
            ax.axis('off')
            return
        # 가성비(cost_eff) 순위 매핑
        ce_order = sorted(range(len(grp)), key=lambda i: -grp[i]['cost_eff'])
        ce_rank  = {i: r + 1 for r, i in enumerate(ce_order)}

        n = len(grp)
        y = list(range(n - 1, -1, -1))   # 위에서부터 1위
        perf = [g['perf_score'] * 100 for g in grp]
        clrs = ['#2ecc71' if i == 0 else
                ('#27ae60' if ce_rank[i] == 1 else '#3498db') for i in range(n)]
        ax.barh(y, perf, color=clrs, height=0.6)

        for i, g in enumerate(grp):
            yi = y[i]
            cost_kr = g['fleet_cost'] * _KRW / 1e8   # 억원
            cost_lbl = (f"{cost_kr/10000:.2f}조원" if cost_kr >= 10000
                        else f"{cost_kr:,.0f}억원")
            tag = '  ★가성비1위' if ce_rank[i] == 1 else f'  가성비{ce_rank[i]}위'
            if g.get('battle'):   # 전장 모드 — 승률·임무점수
                metric_lbl = f"(승률 {g['win_rate']:.0%}·임무 {g['mission_score']:.0%})"
            else:
                metric_lbl = f"(요격 {g['rate']:.0%}·생존 {g['survival']:.0%})"
            ax.text(perf[i] + 1.0, yi,
                    f"성능 {g['perf_score']*100:.0f}  {metric_lbl}  · {cost_lbl}{tag}",
                    va='center', color=C_TEXT, fontsize=9.5)
            # 추천 이유 (작은 글씨, 막대 아래)
            ax.text(0.5, yi - 0.30, g['reason'],
                    va='center', color='#8aa0b8', fontsize=7.8)

        ax.set_yticks(y)
        ax.set_yticklabels([g['preset'] for g in grp], color=C_TEXT, fontsize=10.5)
        ax.set_xlim(0, 135)
        _is_battle = bool(grp and grp[0].get('battle'))
        ax.set_xlabel('종합 성능 점수  (승률 60% + 임무점수 40%)' if _is_battle
                      else '종합 성능 점수  (요격률 60% + 함정 생존율 40%)',
                      color=C_SUBTEXT, fontsize=10)
        ax.set_title(title, color=C_TEXT, fontsize=12.5, pad=8, loc='left')
        ax.tick_params(colors=C_SUBTEXT, labelsize=10)
        for sp in ax.spines.values():
            sp.set_color('#1e2a3a')

    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])
    _draw_group(ax1, kr,   '⚓ 한국 단독 편대  (성능 순위 ▼ · ★=가성비 1위)')
    _draw_group(ax2, comb, '🤝 한미 연합 편대  (성능 순위 ▼ · ★=가성비 1위)')
    fig.suptitle('적정 편대 추천 — 현재 위협 시나리오 기준',
                 color=C_TEXT, fontsize=14, y=0.985)
    fig.subplots_adjust(left=0.16, right=0.97, top=0.93, bottom=0.06)
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


_LOG_CATEGORIES = [
    ('전술 전환',       '#f1c40f'),
    ('탐지',            '#1abc9c'),
    ('미사일 발사',     '#5dade2'),
    ('요격 성공',       '#3498db'),
    ('실패·회피·통과',  '#e67e22'),
    ('아군 피격',       '#e74c3c'),
    ('적함 피격·격침',  '#2ecc71'),
    ('침수·침몰',       '#9b59b6'),
    ('기타',            '#c8d4e0'),
]
_LOG_CAT_COLOR = dict(_LOG_CATEGORIES)


def _classify_log_event(msg: str) -> str:
    """로그 메시지를 _LOG_CATEGORIES 중 하나로 분류 (대괄호 접두사·키워드 기반)."""
    m = msg
    if '전술 전환' in m:
        return '전술 전환'
    if '[탐지]' in m:
        return '탐지'
    if '침몰' in m or '침수' in m:
        return '침수·침몰'
    if '오사' in m:
        return '아군 피격'
    # 실패·회피·통과·불발은 '명중' 판정보다 먼저 (예: [피격 실패]는 명중 아님)
    if ('실패' in m or '통과' in m or '회피' in m or '불발' in m or '빗나감' in m):
        return '실패·회피·통과'
    if '[적 피격' in m or '[적 CIWS]' in m:
        return '적함 피격·격침'
    if '[피격' in m:
        return '아군 피격'
    if '요격 성공' in m:
        return '요격 성공'
    if '발사' in m or 'BMD' in m or '[공격]' in m:   # [공격] = 아군 대함 미사일 발사
        return '미사일 발사'
    return '기타'


def _render_ci_chart(mc: dict) -> Figure:
    fig = Figure(figsize=(12, 7.5), facecolor=C_BG)
    fig.patch.set_facecolor(C_BG)
    rates = mc.get('intercept_rates', [])
    if not rates:
        ax = fig.add_subplot(111, facecolor='#0a0e1a')
        ax.text(0.5, 0.5, '데이터 없음', ha='center', va='center',
                color=C_SUBTEXT, fontsize=12, transform=ax.transAxes)
        fig.tight_layout()
        return fig
    arr   = np.array(rates, dtype=float)
    n     = len(arr)
    mean  = float(arr.mean())
    std   = float(arr.std())
    ci    = 1.96 * std / np.sqrt(n)
    ci_lo = max(0.0, mean - ci)
    ci_hi = min(1.0, mean + ci)
    p10, p50, p90 = (float(np.percentile(arr, q)) for q in (10, 50, 90))

    gs  = fig.add_gridspec(2, 2, wspace=0.28, hspace=0.42)
    ax1 = fig.add_subplot(gs[0, 0], facecolor='#0a0e1a')   # 요격률 분포
    ax2 = fig.add_subplot(gs[0, 1], facecolor='#0a0e1a')   # 수렴 추이
    ax3 = fig.add_subplot(gs[1, 0], facecolor='#0a0e1a')   # 지표별 95% CI
    ax4 = fig.add_subplot(gs[1, 1], facecolor='#0a0e1a')   # 함정별 평균 피격

    # ── ① 요격률 분포 + 평균/CI/백분위 ──────────────────────────────────────
    ax1.hist(arr, bins=20, color=C_ACCENT, alpha=0.75, edgecolor='#1e2a3a')
    ax1.axvline(mean, color=C_GREEN, lw=2, label=f'평균 {mean:.1%} (95%CI {ci_lo:.1%}~{ci_hi:.1%})')
    ax1.axvspan(ci_lo, ci_hi, color=C_GREEN, alpha=0.10)
    ax1.axvline(p50, color='#f1c40f', lw=1.5, ls='-', label=f'P50 {p50:.1%}')
    ax1.axvline(p10, color=C_ORANGE, lw=1.2, ls=':', label=f'P10 {p10:.1%}')
    ax1.axvline(p90, color=C_ORANGE, lw=1.2, ls=':', label=f'P90 {p90:.1%}')
    ax1.set_xlabel('요격률', color=C_SUBTEXT, fontsize=11)
    ax1.set_ylabel('빈도', color=C_SUBTEXT, fontsize=11)
    ax1.set_title(f'요격률 분포 (n={n})', color=C_TEXT, fontsize=12)
    ax1.legend(fontsize=8.5, facecolor='#0a0e1a', labelcolor=C_TEXT, edgecolor='#1e2a3a')
    ax1.tick_params(colors=C_SUBTEXT, labelsize=10)
    for sp in ax1.spines.values():
        sp.set_color('#1e2a3a')

    # ── ② 수렴 추이: 누적 평균 + 95% CI 밴드가 좁아지는 모습 ─────────────────
    k       = np.arange(1, n + 1)
    cum_mean = np.cumsum(arr) / k
    cum_sq   = np.cumsum(arr ** 2) / k
    cum_std  = np.sqrt(np.maximum(cum_sq - cum_mean ** 2, 0.0))
    cum_ci   = 1.96 * cum_std / np.sqrt(k)
    ax2.plot(k, cum_mean, color=C_ACCENT, lw=1.6)
    ax2.fill_between(k, np.maximum(cum_mean - cum_ci, 0), np.minimum(cum_mean + cum_ci, 1),
                     color=C_ACCENT, alpha=0.18)
    ax2.axhline(mean, color=C_GREEN, lw=1.0, ls='--', alpha=0.7)
    ax2.set_xlabel('반복 횟수', color=C_SUBTEXT, fontsize=11)
    ax2.set_ylabel('누적 평균 요격률', color=C_SUBTEXT, fontsize=11)
    ax2.set_title('수렴 추이 (누적 평균 ± 95% CI)', color=C_TEXT, fontsize=12)
    ax2.tick_params(colors=C_SUBTEXT, labelsize=10)
    from matplotlib.ticker import FuncFormatter as _FF
    ax2.yaxis.set_major_formatter(_FF(lambda v, _: f'{v:.0%}'))
    ax2.grid(color='#1e2a3a', linewidth=0.5)
    for sp in ax2.spines.values():
        sp.set_color('#1e2a3a')

    # ── ③ 지표별 95% 신뢰구간 (평균 대비 상대 폭으로 비교) ────────────────────
    costs = np.array(mc.get('total_costs', []), dtype=float)
    edest = np.array(mc.get('enemy_destroyed', []), dtype=float)
    metrics = [('요격률', arr, lambda v: f'{v:.1%}')]
    if costs.size:
        metrics.append(('평균 비용', costs, lambda v: f'${v/1e6:.1f}M'))
    if edest.size:
        metrics.append(('적 격침', edest, lambda v: f'{v:.2f}척'))
    ax3.axvline(1.0, color='#1e2a3a', lw=1.0)
    for i, (name, data, fmt) in enumerate(metrics):
        mm = float(data.mean())
        ss = float(data.std())
        cci = 1.96 * ss / np.sqrt(len(data))
        if mm > 0:
            rel_lo, rel_hi = (mm - cci) / mm, (mm + cci) / mm
        else:
            rel_lo, rel_hi = 1.0, 1.0
        ax3.errorbar([1.0], [i], xerr=[[1.0 - rel_lo], [rel_hi - 1.0]], fmt='o',
                     color=C_ACCENT, ecolor=C_GREEN, elinewidth=2.5, capsize=5, ms=7)
        ax3.text(1.0, i + 0.28,
                 f'{name}: {fmt(mm)}  [{fmt(mm-cci)} ~ {fmt(mm+cci)}]',
                 ha='center', va='bottom', color=C_TEXT, fontsize=9.5)
    ax3.set_yticks(range(len(metrics)))
    ax3.set_yticklabels([m[0] for m in metrics], color=C_TEXT, fontsize=10)
    ax3.set_ylim(-0.6, len(metrics) - 0.2)
    ax3.set_xlabel('평균 대비 비율 (95% CI 폭)', color=C_SUBTEXT, fontsize=11)
    ax3.set_title('지표별 95% 신뢰구간', color=C_TEXT, fontsize=12)
    ax3.tick_params(colors=C_SUBTEXT, labelsize=10)
    for sp in ax3.spines.values():
        sp.set_color('#1e2a3a')

    # ── ④ 함정별 평균 피격 ───────────────────────────────────────────────────
    ship_hits = mc.get('ship_avg_hits', {})
    if ship_hits:
        snames = list(ship_hits.keys())
        shvals = [ship_hits[s] for s in snames]
        y      = np.arange(len(snames))
        clrs   = [C_RED if v > 1 else C_ORANGE if v > 0 else C_GREEN for v in shvals]
        ax4.barh(y, shvals, color=clrs, height=0.55)
        ax4.set_yticks(y)
        ax4.set_yticklabels(snames, color=C_TEXT, fontsize=10)
        ax4.set_xlabel('평균 피격 횟수', color=C_SUBTEXT, fontsize=11)
        ax4.set_title('함정별 평균 피격', color=C_TEXT, fontsize=12)
        ax4.tick_params(colors=C_SUBTEXT, labelsize=10)
        for sp in ax4.spines.values():
            sp.set_color('#1e2a3a')
    else:
        ax4.axis('off')
        ax4.text(0.5, 0.5, '피격 데이터 없음', ha='center', va='center',
                 color=C_SUBTEXT, fontsize=10, transform=ax4.transAxes)

    fig.tight_layout()
    return fig


def _plot_req_radar(fig: Figure, result, mc, cfg=None):
    """주어진 Figure에 REQ 충족률 radar(PASS/FAIL 개요)를 그린다. result 없으면 안내."""
    fig.clear()
    fig.patch.set_facecolor(C_BG)
    if result is None or not _V7_OK:
        ax = fig.add_subplot(111, facecolor='#0a0e1a')
        ax.axis('off')
        ax.text(0.5, 0.5, '시뮬레이션 실행 후 표시',
                ha='center', va='center', color=C_SUBTEXT, fontsize=11,
                transform=ax.transAxes)
        return
    try:
        if result.get('outcome'):   # 지속 전장 모드 — 목표 기반 REQ 축
            items, verdicts, _ = evaluate_req_battle_v7(result, mc, cfg)
        else:
            verdicts, _ = evaluate_req_v7(result, mc, cfg)
            items = REQ_ITEMS_V7
    except Exception:
        return
    labels = [r['id'] for r in items]
    N = len(labels)
    if N == 0:
        return
    ax = fig.add_subplot(111, polar=True)
    ax.set_facecolor('#0a0e1a')
    vals     = [1.0 if v else 0.0 for v in verdicts]
    angles   = np.linspace(0, 2 * np.pi, N, endpoint=False)
    vals_c   = np.concatenate([vals,   [vals[0]]])
    angles_c = np.concatenate([angles, [angles[0]]])
    ax.plot(angles_c, vals_c, 'o-', color=C_ACCENT, lw=2)
    ax.fill(angles_c, vals_c, alpha=0.3, color=C_ACCENT)
    ax.set_xticks(angles)
    ax.set_xticklabels(labels, color=C_TEXT, fontsize=10)
    ax.set_yticks([0, 0.5, 1.0])
    ax.set_yticklabels(['FAIL', '', 'PASS'], color=C_SUBTEXT, fontsize=9)
    ax.set_ylim(0, 1.2)
    pass_cnt = sum(verdicts)
    ax.set_title(f'REQ 충족률  {pass_cnt}/{N}  ({pass_cnt/N:.0%})',
                 color=C_TEXT, fontsize=13, pad=14)
    ax.spines['polar'].set_color('#1e2a3a')
    ax.grid(color='#1e2a3a')
    fig.tight_layout()


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




def _center_window(win, scr):
    """창을 가용 화면 중앙에 배치."""
    win.move(scr.center().x() - win.width() // 2,
             scr.center().y() - win.height() // 2)


def _apply_window_geometry(win, settings_key: str, default_w: int, default_h: int):
    """저장된 창 위치·크기를 복원. 없으면 화면 중앙에 기본 크기로 배치.
    기본 크기가 화면보다 크면 가용 화면의 92%로 클램프(화면 밖으로 안 넘침)."""
    settings = QSettings("AegisSim", settings_key)
    scr = QApplication.primaryScreen().availableGeometry()
    geo = settings.value("geometry")
    if geo is not None:
        win.restoreGeometry(geo)
        # 복원된 창이 현재 화면과 겹치지 않으면(모니터 변경 등) 중앙으로 보정
        if not scr.intersects(win.frameGeometry()):
            _center_window(win, scr)
        return
    w = min(default_w, int(scr.width()  * 0.92))
    h = min(default_h, int(scr.height() * 0.92))
    win.resize(w, h)
    _center_window(win, scr)
