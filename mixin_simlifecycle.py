"""MainWindow mixin — 실행 제어(초기화·시뮬 실행·완료/에러 콜백·창 수명).

app_main.py 분할 8/N (MainWindow mixin 분할). 의존은 PyQt6·app_theme·app_utils·
app_workers·ui_charts·ui_dialogs·ui_widgets·ui_monitor뿐.
`app_version`은 app_main 순환을 피하려고 생성자 인자로 주입(app_launcher.SplashWindow와
동일 패턴 — CLAUDE.md 8항).
"""
import os
import time
import traceback

from PyQt6.QtCore import QSettings, Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QDialog, QLabel, QMessageBox, QProgressBar, QPushButton,
    QStackedWidget, QStatusBar, QTextBrowser, QVBoxLayout, QWidget,
)

from app_theme import C_BG, C_BORDER, C_PANEL, C_SUBTEXT, C_TEXT
from app_utils import (
    _crash_log_path, _kill_child_processes, _load_forecast_model, _load_surrogate,
    _shutdown_global_pool, _write_log, _write_sim_db, _write_sim_log,
)
from app_workers import SimWorker, _stop_sys_data_worker
from ui_charts import _apply_window_geometry
from ui_dialogs import SimLogDialog, TacticalDialog
from ui_monitor import FloatingMonitor
from ui_widgets import STYLE_MAIN, _TaskbarProgress


class SimLifecycleMixin:
    def __init__(self, app_version: str = ""):
        super().__init__()
        self._app_version = app_version
        self.setWindowTitle(f"합동 통합방어 시뮬레이터  {self._app_version}")
        # 자유 리사이즈 가능하도록 합리적 최소 크기만 지정 (세로 고정 버그 방지)
        self.setMinimumSize(1000, 680)
        self.resize(1800, 1060)
        self._worker         = None
        self._taskbar        = _TaskbarProgress()   # ⑤ 작업표시줄 진행바
        self._result = None
        self._mc     = None
        self._t0     = 0.0
        self._history: list = []  # 이전 실행 결과 히스토리 (최대 5개)
        self._float_mon = FloatingMonitor()
        # 실행 전 '예상 전황' 룩업(surrogate) — 없으면 None(기능 자동 비활성)
        self._surrogate = _load_surrogate()
        self._forecast_model = _load_forecast_model()   # v15.2 날씨 반영 즉시 추정(없으면 룩업 폴백)

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
        # 저장된 창 위치·크기 복원 (없으면 화면 중앙, 화면보다 크면 클램프)
        _apply_window_geometry(self, "MainWin", 1800, 1060)
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self._main_stack = QStackedWidget()
        root.addWidget(self._main_stack)

        # 설정 패널 위젯을 먼저 생성 (위젯 참조 저장)
        self._cfg_container = self._build_config_panel()

        self._main_stack.addWidget(self._build_setup_page())    # index 0: 설정 화면
        self._main_stack.addWidget(self._build_results_page())  # index 1: 결과 화면
        self._main_stack.addWidget(self._build_showcase_page()) # index 2: 쇼케이스

        self._in_results_mode = False
        self._enter_setup_mode()

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

        btn_crash = QPushButton("⚠ 크래시 로그")
        btn_crash.setFixedHeight(22)
        btn_crash.setStyleSheet(
            f"QPushButton {{ background:{C_PANEL}; color:{C_SUBTEXT}; border:1px solid {C_BORDER};"
            f" border-radius:3px; padding:0 8px; font-size:12px; }}"
            f"QPushButton:hover {{ color:#f39c12; }}"
        )
        btn_crash.clicked.connect(self._open_crash_log)
        self.status.addPermanentWidget(btn_crash)

        # ── 키보드 단축키 ─────────────────────────────────────────────
        # F5: 현재 설정으로 시뮬 재실행 (실행 가능 상태일 때만)
        sc_run = QShortcut(QKeySequence("F5"), self)
        sc_run.activated.connect(self._shortcut_run)
        # Ctrl+Tab / Ctrl+Shift+Tab: 결과 서브탭 순환 (결과 화면일 때만)
        sc_next = QShortcut(QKeySequence("Ctrl+Tab"), self)
        sc_next.activated.connect(lambda: self._cycle_subtab(+1))
        sc_prev = QShortcut(QKeySequence("Ctrl+Shift+Tab"), self)
        sc_prev.activated.connect(lambda: self._cycle_subtab(-1))
    def _shortcut_run(self):
        """F5 — 실행 버튼이 활성 상태일 때만 재실행 (중복 실행 방지)."""
        if hasattr(self, 'btn_run') and self.btn_run.isEnabled():
            self._run_sim()
    def _cycle_subtab(self, delta: int):
        """Ctrl+Tab — 결과 서브탭을 사이드바 표시 순서대로 순환."""
        if not getattr(self, '_in_results_mode', False):
            return
        order = self._sidebar.ordered_indices()
        if not order:
            return
        cur = self._stack.currentIndex()
        pos = order.index(cur) if cur in order else 0
        nxt = order[(pos + delta) % len(order)]
        self._sidebar.set_current_index(nxt)
    def _enter_setup_mode(self):
        """설정 전체화면으로 전환."""
        # 상단 5칸: [아군편대, 적군편대, 시나리오, 날씨계절, 해역]
        for cell, widget in zip(self._setup_top_cells,
                                [self._cfg_fleet, self._cfg_enemy,
                                 self._cfg_scenario,
                                 self._cfg_weather, self._cfg_region]):
            cell.layout().insertWidget(0, widget)
            widget.show()

        # 섹션 그룹 → 하단 컬럼
        for groups, col_page in zip(self._sec_groups_ref, self._setup_col_pages):
            cl = col_page.layout()
            for j, grp in enumerate(groups):
                cl.insertWidget(j, grp)
                grp.show()

        # 실행 버튼 → 하단 실행 홀더
        self._setup_run_holder.layout().insertWidget(0, self._cfg_bottom)
        self._cfg_bottom.show()

        self._in_results_mode = False
        self._main_stack.setCurrentIndex(0)
    def _enter_results_mode(self):
        """결과 화면으로 전환 (설정 사이드바 + 결과 패널)."""
        if self._in_results_mode:
            return

        # 섹션 그룹 → 아코디언 content 위젯
        for groups, content_w in zip(self._sec_groups_ref, self._sec_contents):
            cl = content_w.layout()
            for j, grp in enumerate(groups):
                cl.insertWidget(j, grp)
                grp.show()

        # 분리된 설정 위젯 → 스크롤 내부 최상단에 순서대로 복귀
        # (스크롤 영역 안에 둬야 작은 창에서도 압축되지 않고 아코디언과 함께 스크롤됨)
        inner_cl = self._cfg_inner_layout
        for idx, w in enumerate([self._cfg_fleet, self._cfg_enemy,
                                  self._cfg_scenario,
                                  self._cfg_weather, self._cfg_region]):
            inner_cl.insertWidget(idx, w)
            w.show()

        # 실행 버튼은 스크롤 밖 하단에 고정 (항상 접근 가능)
        self._cfg_container_layout.addWidget(self._cfg_bottom)
        self._cfg_bottom.show()

        # container → results 홀더 (최초 1회만 reparent)
        if self._cfg_container.parent() is not self._results_cfg_holder:
            self._results_cfg_holder.layout().addWidget(self._cfg_container)
        self._cfg_container.show()

        self._in_results_mode = True
        self._main_stack.setCurrentIndex(1)
    def _open_crash_log(self):
        """crash.log 내용을 텍스트 창으로 표시 (비어 있으면 안내)."""
        try:
            path = _crash_log_path()
            if os.path.exists(path) and os.path.getsize(path) > 0:
                with open(path, encoding='utf-8', errors='replace') as f:
                    content = f.read()
            else:
                content = "기록된 크래시가 없습니다. (정상)"
        except Exception as e:
            content = f"크래시 로그를 읽을 수 없습니다: {e}"
        dlg = QDialog(self)
        dlg.setWindowTitle("크래시 로그 (crash.log)")
        dlg.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, True)
        dlg.resize(960, 600)
        dlg.setStyleSheet(f"QDialog {{ background:{C_BG}; }}")
        lay = QVBoxLayout(dlg)
        lay.setContentsMargins(10, 10, 10, 10)
        txt = QTextBrowser()
        txt.setPlainText(content)
        txt.setStyleSheet(
            f"QTextBrowser {{ background:{C_PANEL}; color:{C_TEXT};"
            f" border:1px solid {C_BORDER}; font-family:'Consolas','D2Coding',monospace;"
            f" font-size:12px; }}"
        )
        lay.addWidget(txt)
        dlg.show()
    def _open_log_file(self):
        try:
            try:
                alive = (hasattr(self, '_log_dialog')
                         and self._log_dialog is not None
                         and self._log_dialog.isVisible())
            except RuntimeError:
                alive = False
            if not alive:
                self._log_dialog = SimLogDialog(self)
                self._log_dialog.restore_requested.connect(self._restore_cfg)
            self._log_dialog.show()
            self._log_dialog.raise_()
            self._log_dialog.activateWindow()
            # 창이 그려진 뒤 데이터 로드 (메인 스레드 블로킹 방지)
            QTimer.singleShot(0, self._log_dialog._load)
        except Exception:
            _write_log(f'[ERROR] 실행 로그 창 열기 실패: {traceback.format_exc()}')
            QMessageBox.warning(self, "실행 로그",
                                "실행 로그 창을 여는 중 오류가 발생했습니다.\n"
                                "sim_history.log에 상세 내용이 기록되었습니다.")
    def _apply_style(self):
        self.setStyleSheet(STYLE_MAIN)
    def _run_sim(self):
        cfg = self._build_cfg_from_ui()
        mode_idx = self.cmb_sim_mode.currentIndex() if hasattr(self, 'cmb_sim_mode') else 1
        mc_n = [5_000, 10_000, 100_000][mode_idx]
        precision_mode = (mode_idx == 2)
        sobol_npp = self.spn_sobol_npp.value() if hasattr(self, 'spn_sobol_npp') else 3
        test_mode = hasattr(self, 'chk_test_mode') and self.chk_test_mode.isChecked()
        if test_mode:
            mc_n = 10

        self.btn_run.setEnabled(False)
        self._prog.setVisible(True)
        self._t0 = time.time()
        self._lbl_status.setText("실행 중...")

        # BUG-1: 이전 워커가 살아 있으면 종료 후 교체
        if self._worker and self._worker.isRunning():
            self._worker.requestInterruption()
            self._worker.quit()
            if not self._worker.wait(2000):
                self._worker.terminate()
                self._worker.wait(500)

        self._worker = SimWorker(cfg, mc_n, precision_mode=precision_mode,
                                 sobol_npp=sobol_npp, sim_mode_idx=mode_idx,
                                 test_mode=test_mode)
        self._worker.progress.connect(self._on_progress)
        self._worker.progress_detail.connect(self._on_progress_detail)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        # 플로팅 모니터 연결 (v8.26: step_update / phase_update 추가)
        self._worker.sim_started.connect(self._show_float_mon)
        self._worker.sim_ended.connect(self._float_mon.stop_monitor)
        self._worker.progress_detail.connect(self._float_mon.update_mc)
        self._worker.progress.connect(self._float_mon.update_status)
        self._worker.rate_update.connect(self._float_mon.update_rate)
        self._worker.hist_update.connect(self._float_mon.update_histogram)
        self._worker.step_update.connect(self._float_mon.update_step)
        self._worker.phase_update.connect(self._float_mon.update_phases)
        self._worker.cancelled.connect(self._on_cancelled)
        self._float_mon.stop_requested.connect(self._stop_worker)
        # v10.7: 전술 의사결정 모드 — 워커 일시정지 시 다이얼로그 표시
        self._worker.tactical_pause.connect(self._on_tactical_pause)
        self._worker.start(QThread.Priority.LowPriority)  # BUG-1
    def _on_tactical_pause(self, state: dict):
        """v10.7: 전술 의사결정 — 워커 일시정지 시 메인 스레드에서 다이얼로그 표시."""
        dlg = TacticalDialog(state, parent=self)
        dlg.exec()
        choice = dlg.get_choice()
        if self._worker:
            self._worker.resume_tactical(choice)
    def _show_float_mon(self):
        """v13.06.03: 진행 모니터를 결과영역 임베드 페이지(index 2)로 표시.
        실행 즉시 결과 모드로 전환 → 좌측 압축 설정 + 우측 진행 화면."""
        self._enter_results_mode()
        self._float_mon.show()                       # 상태 리셋 + 갱신 타이머 시작
        self._result_outer_stack.setCurrentIndex(2)  # 우측 영역 = 진행 화면
    def _stop_worker(self):
        """플로팅 모니터 중단 버튼 → 워커 인터럽트."""
        if self._worker and self._worker.isRunning():
            self._worker.requestInterruption()
            self._lbl_status.setText("중단 요청 중…")
    def _on_cancelled(self):
        """워커 인터럽트 확정 → UI 초기화."""
        self.btn_run.setEnabled(True)
        self._prog.setVisible(False)
        self._lbl_status.setText("중단됨")
        self._taskbar.clear(int(self.winId()))
        # v13.06.03: 진행 모니터 정지. v13.06.09: 중단 시 최초 설정 화면으로 복귀
        self._float_mon.stop_monitor()
        # v13.06.13: 중단된 시뮬도 실행 로그에 '중단' 상태로 부분 통계 기록
        ws = self._worker
        snap = getattr(ws, '_partial', None) if ws else None
        cfg  = ws.cfg if ws else None
        if cfg and snap:
            try:
                _result = {'total_threats': snap['tt'], 'total_cost': 0}
                _mc = {'n': snap['done'], 'mean_intercept': snap['mean'],
                       'std_intercept': 0, 'full_pass_rate': 0,
                       'friendly_hits': [], 'enemy_destroyed': [], 'cvar': None}
                _write_sim_db(cfg, _result, _mc,
                              getattr(ws, 'sim_mode_idx', 1), status='중단')
            except Exception:
                _write_log(f'[WARN] 중단 기록 실패: {traceback.format_exc()}')
        self._result_outer_stack.setCurrentIndex(0)   # 우측 결과영역 대기화면으로 리셋
        self._enter_setup_mode()                       # 최초 설정 전체화면으로
    def _on_progress(self, msg: str):
        # 진행 상태(단계·MC 횟수·잔여시간)는 상단 진행 화면이 표시 — 좌하단 상태바 중복 제거
        pass
    def _on_progress_detail(self, done: int, total: int, eta: float):
        # MC 진행 수치는 상단 진행 화면이 표시 — 좌하단 상태바 중복 제거
        # ⑤ Windows 작업표시줄 진행바 (최소화 중에도 아이콘에 진행률)
        self._taskbar.set_progress(int(self.winId()), done, total)
    def _on_finished(self, result: dict, mc: dict):
        elapsed = time.time() - self._t0
        self._result = result
        self._mc     = mc

        self.btn_run.setEnabled(True)
        self._prog.setVisible(False)
        self._taskbar.clear(int(self.winId()))

        # v18.1: 캠페인 모드는 요격률·MC 파이프라인을 타지 않는다(전용 요약 렌더 후 반환).
        if result.get('mode') == 'campaign':
            self._render_campaign_result(result, elapsed)
            return
        cvar_str = f" | CVaR {mc.get('cvar', 0):.1%}" if mc.get('cvar') is not None else ''
        _outcome = result.get('outcome')
        if _outcome:   # 지속 전장 모드 — 승/패 중심 표시 (단일 시뮬 + MC 승률)
            _oc = {'win': '🟢 승리', 'loss': '🔴 패배', 'draw': '🟡 무승부'}.get(_outcome, _outcome)
            _wr = mc.get('win_rate')
            _mc_part = (f"MC 승률 {_wr:.0%}" if _wr is not None
                        else f"참고 MC 요격률 {mc['mean_intercept']:.1%}")
            self._lbl_status.setText(
                f"완료 ({elapsed:.1f}s) | ⚔ 전장 결과: {_oc} "
                f"(아군 임무 점수 {result.get('friendly_score', 0.0):.0%}) | {_mc_part}")
        else:
            self._lbl_status.setText(
                f"완료 ({elapsed:.1f}s) | "
                f"요격률 {mc['mean_intercept']:.1%}{cvar_str} | "
                f"MC {mc['n']}회")

        self._update_cards(result, mc)
        self._update_vls_warning(mc)
        self._update_status_board(result, mc)   # v13.3 전황 지표판
        self.tab_engagement.load_result(result)
        self._fill_req(result, mc)
        self._fill_log(result.get('log', []))
        cfg  = self._worker.cfg  if self._worker else {}
        self._fill_diagnosis(result, mc, cfg)
        self._fill_briefing(result, mc, cfg)
        mc_n = self._worker.mc_n if self._worker and hasattr(self._worker, 'mc_n') else 100
        # BUG-1: 감도 분석·최소 재고 워커를 즉시 기동하면 GIL 독점으로 UI 프리즈
        # → 해당 탭 방문 시점까지 lazy-start로 연기
        self._pending_cfg  = cfg
        self._pending_mc_n = mc_n

        # 모든 차트 페이지를 dirty로 표시 (11·12는 탭 방문 시 워커 기동)
        self._page_dirty = {1, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 23, 24}

        # 히스토리 저장 (최대 5개)
        self._history.append({
            'mean_intercept': mc['mean_intercept'],
            'full_pass_rate': mc.get('full_pass_rate', 0),
            'mean_cost':      mc.get('mean_cost', result.get('total_cost', 0)),
            'total_cost':     result.get('total_cost', 0),
            'label': f"#{len(self._history)+1}  {cfg.get('weather','?')} / "
                     f"{cfg.get('mixed_scenario') or cfg.get('enemy_fleet_preset') or cfg.get('enemy_fleet_mode','?')}",
        })
        if len(self._history) > 5:
            self._history.pop(0)

        # v8.26: 아코디언 사이드바 배지 표시 + 결과 탭으로 전환
        # 전장 모드는 교전 분석(0, 작전 결과 배너)으로, 그 외는 MC 통계(1)로 착지
        self._sidebar.mark_new_data(list(range(26)))
        _land_idx = 0 if result.get('outcome') else 1
        self._sidebar.set_current_index(_land_idx)
        self._on_page_changed(_land_idx)   # BUG-1: 동일 인덱스면 item_selected 미발화 → 수동 트리거
        sim_mode_idx = getattr(self._worker, 'sim_mode_idx', 1)
        _write_sim_log(cfg, result, mc)
        _write_sim_db(cfg, result, mc, sim_mode_idx)
    def _on_error(self, msg: str):
        self.btn_run.setEnabled(True)
        self._prog.setVisible(False)
        self._lbl_status.setText("오류 발생")
        # v13.06.03: 진행 모니터 정지 + 결과 없으면 대기 화면(index0)으로 복귀
        self._float_mon.stop_monitor()
        if self._result is None:
            self._result_outer_stack.setCurrentIndex(0)
        QMessageBox.critical(self, "시뮬레이션 오류", msg)
    def closeEvent(self, event):
        # 창 위치·크기 저장 (다음 실행 시 같은 자리에서 복원)
        try:
            QSettings("AegisSim", "MainWin").setValue("geometry", self.saveGeometry())
        except Exception:
            pass
        # SimWorker 중단 (MC 분석 실행 중이면 배치 루프에서 중단 신호 감지)
        if self._worker and self._worker.isRunning():
            self._worker.requestInterruption()
            self._worker.quit()
            if not self._worker.wait(2000):
                self._worker.terminate()
                self._worker.wait(500)
        # FleetRecommendWorker 중단
        opt = getattr(self, '_opt_worker', None)
        if opt and opt.isRunning():
            opt.requestInterruption()
            opt.quit()
            if not opt.wait(1000):
                opt.terminate()
                opt.wait(500)
        # 쇼케이스 ON/OFF 비교 워커 중단
        scw = getattr(self, '_showcase_worker', None)
        if scw and scw.isRunning():
            scw.requestInterruption()
            scw.quit()
            if not scw.wait(2000):
                scw.terminate()
                scw.wait(500)
        # Phase 3: 활성 토글 반사실 분석 워커 중단
        icw = getattr(self, '_impact_worker', None)
        if icw and icw.isRunning():
            icw.requestInterruption()
            icw.quit()
            if not icw.wait(2000):
                icw.terminate()
                icw.wait(500)
        # 차트 렌더 워커 중단 (ChartPageWidget._worker) — placeholder QWidget은 hasattr로 건너뜀
        for attr in ('tab_mc_canvas', 'tab_ci',
                     'tab_optimize', 'tab_stress', 'tab_sobol'):
            widget = getattr(self, attr, None)
            if widget is not None and hasattr(widget, 'stop_worker'):
                widget.stop_worker()
        # 교전 분석 탭 차트 워커 중단
        if hasattr(self, 'tab_engagement'):
            self.tab_engagement.stop_worker()
        # 글로벌 프로세스 풀 종료 (워커 프로세스 강제 kill 포함)
        _shutdown_global_pool()
        # 시스템 모니터 워커 중단 (nvidia-smi subprocess 포함)
        _stop_sys_data_worker()
        # 남은 자식 프로세스 강제 종료 (좀비 프로세스 완전 제거)
        _kill_child_processes()
        event.accept()
