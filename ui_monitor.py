"""실행 모니터 UI — FloatingMonitor(시뮬 진행 팝업)·SysMonitorTab(시스템 자원 탭).

app_main.py 분할 7/N. 의존은 PyQt6·matplotlib·app_theme·app_utils·app_workers·ui_widgets·ui_charts뿐.
"""
import os
import threading
import time

from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QGroupBox, QHBoxLayout, QHeaderView, QLabel, QProgressBar, QPushButton,
    QScrollArea, QStackedWidget, QTableWidget, QTableWidgetItem, QTabWidget,
    QVBoxLayout, QWidget,
)

from app_theme import C_ACCENT, C_BG, C_BORDER, C_ORANGE, C_PANEL, C_SUBTEXT, C_TEXT
from app_utils import _PERF_HISTORY, _SYS_CACHE
from app_workers import SimWorker
from ui_charts import MplCanvas
from ui_widgets import ConvergenceWidget, RateHistogramWidget


class FloatingMonitor(QWidget):
    """시뮬레이션 실행 중 팝업 (v8.26 재설계)
    · 1/2 단일 시뮬: 진행 바 + 위협/VLS 상태 + 로그 스트림
    · 2/2 MC 분석:  MC 진행 바 + 단계별 타이밍 바 + 수렴 감지 + 이전 비교
    · 시스템 자원 행 (CPU/RAM/GPU) + 중단 버튼
    """

    stop_requested = pyqtSignal()
    _SPARK_N = 10

    def __init__(self, parent=None):
        # v13.06.03: 떠다니는 창 → 결과영역 임베드 페이지. 창 플래그·고정크기 제거.
        super().__init__(parent)
        self.setMinimumSize(480, 590)
        self._show_time: float  = 0.0
        self._mc_t0: float      = 0.0
        self._mc_done: int      = 0
        self._eta_target: float = 0.0   # 마지막 배치 갱신 시 ETA(초)
        self._eta_set_t: float  = 0.0   # 그 ETA를 받은 시각 — 틱마다 부드럽게 카운트다운
        self._batch_rates: list = []
        self._phase_acc: dict   = {}   # 누적 단계 타이밍
        self._rates_history: list = [] # 수렴 감지용
        self._pending_hist: list  = [] # 히스토그램 최신 데이터 (1초 타이머가 그림)
        self.setStyleSheet("* { font-family: 'Malgun Gothic', 'Segoe UI', sans-serif; }")
        self._timer = QTimer(self)
        self._timer.setInterval(300)    # 0.3초 — 진행 그래프·ETA 갱신 주기 (동기화 가속)
        self._timer.timeout.connect(self._refresh_tick)
        self._build_ui()

    # ── UI 구성 ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self._card = QWidget(self)
        self._card.setObjectName('fmon_card')
        self._card.setStyleSheet(f"""
            #fmon_card {{
                background: rgba(13,17,23,242);
                border: 1px solid {C_ACCENT};
                border-radius: 10px;
            }}
        """)
        inner = QVBoxLayout(self._card)
        inner.setContentsMargins(16, 10, 16, 10)
        inner.setSpacing(4)

        # ── 제목 행 ──────────────────────────────────────────────────────────
        title_row = QHBoxLayout()
        self._lbl_title = QLabel("⚙  1/2  단일 시뮬 실행 중…")
        self._lbl_title.setStyleSheet(f"color:{C_ACCENT}; font-size:18px; font-weight:bold;")
        self._lbl_elapsed = QLabel("경과  0:00")
        self._lbl_elapsed.setStyleSheet(f"color:{C_SUBTEXT}; font-size:14px;")
        title_row.addWidget(self._lbl_title)
        title_row.addStretch()
        title_row.addWidget(self._lbl_elapsed)
        inner.addLayout(title_row)

        inner.addWidget(self._sep())

        # ── 단일 시뮬 구역 (QStackedWidget 인덱스 0) ─────────────────────────
        self._stack_mode = QStackedWidget()

        single_w = QWidget()
        sv = QVBoxLayout(single_w)
        sv.setContentsMargins(0, 0, 0, 0); sv.setSpacing(4)

        # 시뮬 진행 바 (시간)
        sp_row = QHBoxLayout()
        self._lbl_sim_t = QLabel("모사 시간  0s / —s")
        self._lbl_sim_t.setStyleSheet(f"color:{C_TEXT}; font-size:16px;")
        self._lbl_sim_t.setToolTip(
            "모사된 교전 내 시간(시뮬 시각)입니다. 실제 계산에 걸리는 시간이 아닙니다.\n"
            "예: 40분(2400초)짜리 교전을 컴퓨터가 수 초 만에 계산합니다.")
        sp_row.addWidget(self._lbl_sim_t); sp_row.addStretch()
        sv.addLayout(sp_row)
        self._prog_sim = QProgressBar()
        self._prog_sim.setRange(0, 1000); self._prog_sim.setValue(0)
        self._prog_sim.setFixedHeight(7); self._prog_sim.setTextVisible(False)
        self._prog_sim.setStyleSheet(self._bar_css(C_ACCENT))
        sv.addWidget(self._prog_sim)

        # 위협 / VLS 상태 행
        status_row = QHBoxLayout(); status_row.setSpacing(16)
        self._lbl_alive = self._tag_lbl("위협", "— 개")
        self._lbl_vls   = self._tag_lbl("VLS 잔여", "— 발")
        status_row.addWidget(self._lbl_alive)
        status_row.addWidget(self._lbl_vls)
        status_row.addStretch()
        sv.addLayout(status_row)

        # 교전 로그 스트림 (최근 5줄)
        sv.addWidget(self._sep())
        log_hdr = QLabel("교전 로그")
        log_hdr.setStyleSheet(f"color:{C_SUBTEXT}; font-size:13px;")
        sv.addWidget(log_hdr)
        self._log_labels = []
        for _ in range(5):
            lbl = QLabel("")
            lbl.setStyleSheet(f"color:{C_TEXT}; font-size:14px; padding-left:4px;")
            lbl.setWordWrap(True)
            sv.addWidget(lbl)
            self._log_labels.append(lbl)
        self._log_buf: list = []

        self._stack_mode.addWidget(single_w)   # index 0

        # ── MC 구역 (QStackedWidget 인덱스 1) ────────────────────────────────
        mc_w = QWidget()
        mv = QVBoxLayout(mc_w)
        mv.setContentsMargins(0, 0, 0, 0); mv.setSpacing(4)

        # MC 진행 바
        mc_top = QHBoxLayout()
        self._lbl_mc  = QLabel("MC  0 / 0")
        self._lbl_mc.setStyleSheet(f"color:{C_TEXT}; font-size:17px;")
        self._lbl_eta = QLabel("잔여 —")
        self._lbl_eta.setStyleSheet(f"color:{C_TEXT}; font-size:16px; font-weight:bold;")
        mc_top.addWidget(self._lbl_mc); mc_top.addStretch(); mc_top.addWidget(self._lbl_eta)
        mv.addLayout(mc_top)
        self._prog_mc = QProgressBar()
        self._prog_mc.setRange(0, 100); self._prog_mc.setValue(0)
        self._prog_mc.setFixedHeight(8); self._prog_mc.setTextVisible(False)
        self._prog_mc.setStyleSheet(self._bar_css(C_ACCENT))
        mv.addWidget(self._prog_mc)

        # 요격률 게이지 + 스파크라인
        rate_row = QHBoxLayout(); rate_row.setSpacing(6)
        lbl_rt = QLabel("요격률")
        lbl_rt.setStyleSheet(f"color:{C_SUBTEXT}; font-size:13px;"); lbl_rt.setFixedWidth(38)
        self._prog_rate = QProgressBar()
        self._prog_rate.setRange(0, 100); self._prog_rate.setValue(0)
        self._prog_rate.setFixedHeight(9); self._prog_rate.setTextVisible(False)
        self._prog_rate.setStyleSheet(self._bar_css('#2ecc71'))
        self._lbl_rate_val = QLabel("—%")
        self._lbl_rate_val.setStyleSheet(f"color:{C_TEXT}; font-size:17px; font-weight:bold;")
        self._lbl_rate_val.setFixedWidth(52)
        rate_row.addWidget(lbl_rt); rate_row.addWidget(self._prog_rate, 1)
        rate_row.addWidget(self._lbl_rate_val)
        self._spark_boxes = []
        for _ in range(self._SPARK_N):
            sq = QLabel(); sq.setFixedSize(10, 13)
            sq.setStyleSheet(f"background:{C_BORDER}; border-radius:2px;")
            rate_row.addWidget(sq); self._spark_boxes.append(sq)
        mv.addLayout(rate_row)

        # 격추 / 피격 / 속도
        kpi_row = QHBoxLayout(); kpi_row.setSpacing(16)
        self._lbl_ed  = QLabel("격추 —")
        self._lbl_fh  = QLabel("피격 —")
        self._lbl_spd = QLabel("— 회/s")
        for l in (self._lbl_ed, self._lbl_fh, self._lbl_spd):
            l.setStyleSheet(f"color:{C_TEXT}; font-size:14px;")
        kpi_row.addWidget(self._lbl_ed); kpi_row.addWidget(self._lbl_fh)
        kpi_row.addStretch(); kpi_row.addWidget(self._lbl_spd)
        mv.addLayout(kpi_row)

        # v13.06.06: 단계별 평균 소요시간 바(개발자용 계측치) 제거 → 그 자리에
        # 요격률 분포 히스토그램 배치. 빈 dict 유지로 update_phases는 안전한 no-op.
        self._phase_bars: dict = {}

        hist_hdr = QLabel("요격률 분포 (MC 표본)")
        hist_hdr.setStyleSheet(f"color:{C_SUBTEXT}; font-size:13px;")
        mv.addWidget(hist_hdr)
        self._rate_hist = RateHistogramWidget()
        mv.addWidget(self._rate_hist)

        mv.addWidget(self._sep())

        # 수렴 감지 + 이전 실행 델타
        self._lbl_converge = QLabel("수렴  분석 중…")
        self._lbl_converge.setStyleSheet(f"color:{C_SUBTEXT}; font-size:13px;")
        self._lbl_delta    = QLabel("")
        self._lbl_delta.setStyleSheet(f"color:{C_SUBTEXT}; font-size:13px;")
        conv_row = QHBoxLayout()
        conv_row.addWidget(self._lbl_converge)
        conv_row.addStretch()
        conv_row.addWidget(self._lbl_delta)
        mv.addLayout(conv_row)

        # ③ 실시간 수렴 라인 그래프 (누적 평균 요격률 추이)
        self._conv_graph = ConvergenceWidget()
        mv.addWidget(self._conv_graph)

        self._stack_mode.addWidget(mc_w)   # index 1

        inner.addWidget(self._stack_mode)
        inner.addWidget(self._sep())

        # ── 시스템 자원 행 ────────────────────────────────────────────────────
        sys_row = QHBoxLayout(); sys_row.setSpacing(0)
        self._sys_cpu  = self._stat_cell("CPU",   "—%")
        self._sys_ram  = self._stat_cell("RAM",   "— GB")
        self._sys_gpu  = self._stat_cell("GPU",   "—%")
        self._sys_vram = self._stat_cell("VRAM",  "—")
        self._sys_wkr  = self._stat_cell("워커",  "—")
        for w in (self._sys_cpu, self._sys_ram, self._sys_gpu,
                  self._sys_vram, self._sys_wkr):
            sys_row.addWidget(w, 1)
        inner.addLayout(sys_row)

        # ── 하단: 중단 버튼 ──────────────────────────────────────────────────
        # v13.06.06: '드래그로 이동' 안내 제거 — 임베드로 드래그 기능 없어진 잔재
        bot_row = QHBoxLayout()
        btn_stop = QPushButton("■  중단")
        btn_stop.setFixedHeight(24)
        btn_stop.setStyleSheet(
            f"QPushButton {{ background:#3d1010; color:#e74c3c; border:1px solid #5a1a1a;"
            f" border-radius:4px; font-size:14px; padding:0 10px; }}"
            f"QPushButton:hover {{ background:#5a1a1a; }}"
        )
        btn_stop.clicked.connect(self.stop_requested)
        bot_row.addStretch()
        bot_row.addWidget(btn_stop)
        inner.addLayout(bot_row)

        outer.addWidget(self._card)

    # ── 헬퍼 ─────────────────────────────────────────────────────────────────
    def _sep(self) -> QLabel:
        s = QLabel(); s.setFixedHeight(1)
        s.setStyleSheet(f"background:{C_BORDER};")
        return s

    @staticmethod
    def _bar_css(color: str) -> str:
        return (f"QProgressBar {{ background:#161b22; border-radius:3px; border:1px solid #21262d; }}"
                f"QProgressBar::chunk {{ background:{color}; border-radius:2px; }}")

    def _tag_lbl(self, title: str, init: str) -> QWidget:
        w = QWidget()
        h = QHBoxLayout(w); h.setContentsMargins(0, 0, 0, 0); h.setSpacing(4)
        t = QLabel(title); t.setStyleSheet(f"color:{C_SUBTEXT}; font-size:13px;")
        v = QLabel(init);  v.setStyleSheet(f"color:{C_TEXT}; font-size:16px; font-weight:bold;")
        v.setObjectName(f'tag_{title}')
        h.addWidget(t); h.addWidget(v)
        return w

    def _stat_cell(self, title: str, init: str) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w); v.setContentsMargins(0, 2, 0, 2); v.setSpacing(1)
        t = QLabel(title); t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t.setStyleSheet(f"color:{C_SUBTEXT}; font-size:12px;")
        val = QLabel(init); val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        val.setStyleSheet(f"color:{C_TEXT}; font-size:16px; font-weight:bold;")
        val.setObjectName(f'sys_{title}')
        v.addWidget(t); v.addWidget(val)
        return w

    def _find_sys(self, key: str) -> QLabel:
        return self.findChild(QLabel, f'sys_{key}')

    def _find_tag(self, key: str) -> QLabel:
        return self.findChild(QLabel, f'tag_{key}')

    @staticmethod
    def _rate_color(r: float) -> str:
        return '#2ecc71' if r >= 0.80 else ('#f39c12' if r >= 0.60 else '#e74c3c')

    # ── 시스템 / 경과 타이머 ─────────────────────────────────────────────────
    def _refresh_tick(self):
        # 경과 시간
        if self._show_time:
            el = int(time.time() - self._show_time)
            m, s = divmod(el, 60)
            self._lbl_elapsed.setText(f"경과  {m}:{s:02d}")
        # 처리 속도 (MC 모드)
        if self._mc_t0 and self._mc_done:
            elapsed = time.time() - self._mc_t0
            spd = self._mc_done / elapsed if elapsed > 0 else 0.0
            self._lbl_spd.setText(f"{spd:.0f} 회/s")
        # 잔여 시간 부드러운 카운트다운 (배치 갱신 사이에도 매끄럽게) — _eta_target 기준 보간
        if self._eta_target > 0:
            rem = self._eta_target - (time.time() - self._eta_set_t)
            self._set_eta_label(max(0.0, rem))
        # 시스템
        c   = _SYS_CACHE
        gpu = c['gpu']
        self._find_sys('CPU' ).setText(f"{c['cpu']:.0f}%")
        self._find_sys('RAM' ).setText(f"{c.get('mem_used',0)/1024**3:.1f}G")
        self._find_sys('GPU' ).setText(f"{gpu['util']}%" if 'util' in gpu else "—")
        mu = gpu.get('mem_used')
        self._find_sys('VRAM').setText(f"{mu}M" if mu is not None else "—")
        wn = len(c.get('worker_stats', []))
        self._find_sys('워커').setText(str(wn) if wn else "—")
        # 진행 그래프는 여기서 1초 주기로 그림 — 데이터(배치 완료) 타이밍과 무관하게 규칙적
        if self._rates_history:
            self._conv_graph.set_data(self._rates_history)
        if self._pending_hist:
            self._rate_hist.set_data(self._pending_hist)

    # ── 외부 시그널 핸들러 ────────────────────────────────────────────────────
    def update_status(self, msg: str):
        if "MC" in msg and ("분석" in msg or "/" in msg):
            self._lbl_title.setText("⚙  2/2  MC 분석 중…")
            self._stack_mode.setCurrentIndex(1)
        elif "시뮬레이션 실행" in msg or "실행 중" in msg:
            self._lbl_title.setText("⚙  1/2  단일 시뮬 실행 중…")
            self._stack_mode.setCurrentIndex(0)

    def update_step(self, t: float, t_max: float, alive: int, vls: int, last_log: str):
        """단일 시뮬 타임스텝 콜백."""
        pct = int(t / t_max * 1000) if t_max > 0 else 0
        self._prog_sim.setValue(pct)
        self._lbl_sim_t.setText(f"모사 시간  {int(t)}s / {int(t_max)}s")
        self._find_tag('위협').setText(f"{alive} 개")
        self._find_tag('VLS 잔여').setText(f"{vls} 발")
        if last_log:
            self._log_buf.append(last_log)
            recent = self._log_buf[-5:]
            for i, lbl in enumerate(self._log_labels):
                lbl.setText(recent[i] if i < len(recent) else "")

    def _set_eta_label(self, eta: float):
        if eta > 0:
            m, s = divmod(int(eta), 60)
            self._lbl_eta.setText(f"잔여 {m}:{s:02d}" if m else f"잔여 {s}초")
        else:
            self._lbl_eta.setText("잔여 계산 중…")

    def update_mc(self, done: int, total: int, eta: float):
        if done == 1:
            per = eta / max(total - done, 1)
            self._mc_t0 = time.time() - per
        self._mc_done = done
        self._lbl_mc.setText(f"MC  {done:,} / {total:,}")
        pct = int(done * 100 / total) if total > 0 else 0
        self._prog_mc.setValue(pct)
        # 배치 완료 시 ETA 재동기화 — 틱마다 _refresh_tick이 이 값을 부드럽게 깎아 표시
        self._eta_target = eta
        self._eta_set_t  = time.time()
        self._set_eta_label(eta)

    def update_rate(self, mean_rate: float, avg_ed: float, avg_fh: float):
        pct = int(mean_rate * 100)
        color = self._rate_color(mean_rate)
        self._prog_rate.setValue(pct)
        self._prog_rate.setStyleSheet(self._bar_css(color))
        self._lbl_rate_val.setText(f"{mean_rate:.1%}")
        self._lbl_rate_val.setStyleSheet(f"color:{color}; font-size:17px; font-weight:bold;")
        self._lbl_ed.setText(f"격추 {avg_ed:.1f}")
        self._lbl_fh.setText(f"피격 {avg_fh:.2f}")
        # 스파크라인
        self._batch_rates.append(mean_rate)
        recent = self._batch_rates[-self._SPARK_N:]
        for i, sq in enumerate(self._spark_boxes):
            if i < len(recent):
                sq.setStyleSheet(f"background:{self._rate_color(recent[i])}; border-radius:2px;")
            else:
                sq.setStyleSheet(f"background:{C_BORDER}; border-radius:2px;")
        # 수렴 감지 (최근 100개 vs 이전 100개 표준편차)
        self._rates_history.append(mean_rate)   # ③ 수렴 라인은 _refresh_tick(1초)이 그림
        h = self._rates_history
        if len(h) >= 20:
            import numpy as _np
            std = _np.std(h[-20:]) * 100
            if std < 0.5:
                self._lbl_converge.setText(f"📊 수렴 안정 ±{std:.1f}%p  ✅")
                self._lbl_converge.setStyleSheet("color:#2ecc71; font-size:13px;")
            else:
                self._lbl_converge.setText(f"📊 수렴 진행 중 ±{std:.1f}%p")
                self._lbl_converge.setStyleSheet(f"color:{C_SUBTEXT}; font-size:13px;")
        # 이전 실행 델타
        prev = SimWorker._last_intercept_rate
        if prev >= 0 and len(self._rates_history) >= 5:
            import numpy as _np
            cur = _np.mean(self._rates_history[-5:])
            diff = (cur - prev) * 100
            sign = "↑" if diff > 0 else "↓"
            col  = '#2ecc71' if diff > 0 else '#e74c3c'
            self._lbl_delta.setText(f"이전 대비 {sign}{abs(diff):.1f}%p")
            self._lbl_delta.setStyleSheet(f"color:{col}; font-size:13px;")

    def update_histogram(self, rates: list):
        """개별 시뮬 요격률 누적 분포 — 데이터만 저장, 그리기는 _refresh_tick(1초)."""
        self._pending_hist = rates

    def update_phases(self, phase_times: dict):
        """MC 배치 완료마다 단계별 타이밍 바 갱신."""
        if not phase_times:
            return
        total_t = sum(phase_times.values()) or 1.0
        for key, (bar, val_lbl) in self._phase_bars.items():
            v = phase_times.get(key, 0.0)
            bar.setValue(int(v / total_t * 1000))
            ms = v * 1000
            val_lbl.setText(f"{ms:.1f}ms" if ms < 1000 else f"{v:.2f}s")
            # 병목(가장 느린 단계) 강조
            is_bottleneck = (v == max(phase_times.values()))
            bar.setStyleSheet(self._bar_css('#e74c3c' if is_bottleneck else '#3498db'))

    # ── show / close ─────────────────────────────────────────────────────────
    def show(self):
        super().show()
        self._show_time = time.time()
        self._batch_rates.clear()
        self._rates_history.clear()
        self._conv_graph.clear()
        self._rate_hist.clear()
        self._pending_hist = []
        self._log_buf.clear()
        self._mc_done = 0
        self._mc_t0   = 0.0
        self._eta_target = 0.0
        self._eta_set_t  = 0.0
        self._stack_mode.setCurrentIndex(0)
        for sq in self._spark_boxes:
            sq.setStyleSheet(f"background:{C_BORDER}; border-radius:2px;")
        for lbl in self._log_labels:
            lbl.setText("")
        self._lbl_converge.setText("수렴  분석 중…")
        self._lbl_converge.setStyleSheet(f"color:{C_SUBTEXT}; font-size:13px;")
        self._lbl_delta.setText("")
        self._timer.start()
        self._refresh_tick()

    def stop_monitor(self):
        """v13.06.03: 진행 종료 시 갱신 타이머만 정지 (임베드 위젯이라 close 불필요)."""
        self._timer.stop()



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



