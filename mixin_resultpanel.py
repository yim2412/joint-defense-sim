"""MainWindow mixin — 결과 탭 렌더(REQ·상태보드·로그·카드·등급·캠페인 보고).

app_main.py 분할 8/N (MainWindow mixin 분할). 의존은 PyQt6·matplotlib·app_theme·
app_utils·app_engine·ui_charts·ui_widgets뿐.
"""
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QApplication, QFileDialog, QFrame, QGridLayout, QGroupBox, QHBoxLayout,
    QHeaderView, QLabel, QMessageBox, QPushButton, QScrollArea, QStackedWidget,
    QTableWidget, QTableWidgetItem, QTextBrowser, QVBoxLayout, QWidget,
)

from app_engine import (
    REQ_ITEMS_V7, _V7_OK, diagnose_vulnerabilities_v7, evaluate_req_battle_v7,
    evaluate_req_v7, generate_briefing,
)
from app_theme import (
    C_ACCENT, C_BG, C_BORDER, C_ORANGE, C_PANEL, C_RED, C_SUBTEXT, C_TEXT,
)
from app_utils import _SIM_MODE_NAMES
from ui_charts import (
    ChartPageWidget, EngagementAnalysisTab, _LOG_CAT_COLOR, _classify_log_event,
    _plot_req_radar, _render_ci_chart, _render_mc_chart, _render_sobol_chart,
    _render_stress_test,
)
from ui_widgets import AccordionSidebar, GaugeWidget


class ResultPanelMixin:
    def _build_results_page(self) -> QWidget:
        """결과 화면 (실행 후): 왼쪽 설정 패널 + 오른쪽 결과."""
        page = QWidget()
        layout = QHBoxLayout(page)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 왼쪽: 설정 패널 홀더
        self._results_cfg_holder = QWidget()
        self._results_cfg_holder.setFixedWidth(430)
        rl = QVBoxLayout(self._results_cfg_holder)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(0)

        btn_back = QPushButton("← 설정 화면으로")
        btn_back.setMinimumHeight(34)   # 고정 높이에 한글 받침이 잘리던 문제 → 여유 확보
        btn_back.setStyleSheet(f"""
            QPushButton {{
                background:{C_PANEL}; color:{C_SUBTEXT};
                border:none; border-bottom:1px solid {C_BORDER};
                font-family:'Malgun Gothic'; font-size:12px;
                text-align:left; padding:4px 12px;
            }}
            QPushButton:hover {{ color:{C_TEXT}; background:#1f2d40; }}
        """)
        btn_back.clicked.connect(self._enter_setup_mode)
        rl.addWidget(btn_back)

        layout.addWidget(self._results_cfg_holder)

        # 오른쪽: 결과 패널
        layout.addWidget(self._build_result_panel(), stretch=1)

        return page
    def _build_result_panel(self) -> QWidget:
        outer = QWidget()
        outer_layout = QVBoxLayout(outer)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        self._result_outer_stack = QStackedWidget()

        # 페이지 0: 대기 화면 (결과 수신 전)
        _ph = QWidget()
        _phl = QVBoxLayout(_ph)
        _phl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        _phlbl = QLabel("시뮬레이션을 실행하면 결과가 여기에 표시됩니다")
        _phlbl.setStyleSheet(f"color:{C_SUBTEXT}; font-size:15px;")
        _phl.addWidget(_phlbl)
        self._result_outer_stack.addWidget(_ph)  # index 0

        # 페이지 1: 결과 패널
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        self._result_outer_stack.addWidget(panel)  # index 1
        # 페이지 2: 진행 모니터 임베드 (v13.06.03) — 떠다니는 창 대체
        self._result_outer_stack.addWidget(self._float_mon)  # index 2
        outer_layout.addWidget(self._result_outer_stack, stretch=1)

        # 핵심 지표 카드 영역
        self.card_row = QWidget()
        card_layout = QHBoxLayout(self.card_row)
        card_layout.setContentsMargins(12, 8, 12, 0)
        card_layout.setSpacing(8)

        # 요격률 게이지 (헤드라인 지표 시각화 — 카드 좌측)
        self._gauge = GaugeWidget("요격률 (MC)")
        self._gauge.setToolTip("몬테카를로 평균 요격률 — 녹색 ≥90% · 주황 ≥60% · 적색 미만")
        card_layout.addWidget(self._gauge)

        self._cards = {}
        self._card_deltas = {}
        card_defs = [
            ('요격률 (MC)',      'intercept'),
            ('완전 요격 비율',   'full_pass'),
            ('CVaR (최악 5%)',   'cvar'),
            ('아군 피격',        'friendly_hit'),
            ('적 격침',          'enemy_dest'),
            ('총 비용',          'cost'),
            ('항공 출격',        'aircraft'),
        ]
        card_tips = {
            'intercept':    '몬테카를로 평균 요격률 — 전체 위협 중 요격 성공 비율의 MC 평균.\n90% 이상이면 녹색.',
            'full_pass':    '완전 요격 비율 — 위협을 하나도 놓치지 않은(누수 0) 시뮬의 비율.',
            'cvar':         'CVaR(조건부 위험가치, 최악 5%) — 하위 5% 시나리오의 평균 요격률.\n방어망이 가장 나쁠 때의 성능 지표.',
            'friendly_hit': '아군 피격 횟수 — 대표 단일 시뮬에서 아군 함정이 받은 명중 수.',
            'enemy_dest':   '격침한 적 수상함 수 — 대표 단일 시뮬 기준.',
            'cost':         '총 교전 비용 — 대표 단일 시뮬의 소모 미사일·탄약 비용 합계(백만 달러).',
            'aircraft':     '항공 출격 횟수 — 대표 단일 시뮬의 CAP·대잠 등 항공 출격 수.',
        }
        for label, key in card_defs:
            card = QGroupBox(label)
            card.setFixedHeight(80)
            card.setMinimumWidth(90)
            card.setToolTip(card_tips.get(key, ''))
            cl = QVBoxLayout(card)
            cl.setContentsMargins(6, 4, 6, 4)
            cl.setSpacing(0)
            lbl = QLabel("—")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFont(QFont('Malgun Gothic', 18, QFont.Weight.Bold))
            lbl.setStyleSheet(f"color:{C_ACCENT};")
            # 결과 수치 마우스로 선택·복사 가능
            lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            cl.addWidget(lbl)
            # 이전 실행 대비 변화량 (delta) — 첫 실행 시 빈칸
            dl = QLabel("")
            dl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            dl.setStyleSheet(f"color:{C_SUBTEXT}; font-size:10px;")
            cl.addWidget(dl)
            card_layout.addWidget(card)
            self._cards[key] = lbl
            self._card_deltas[key] = dl

        layout.addWidget(self.card_row)

        # 결과 해석 배너 (v16.13.04) — 핵심 지표를 등급+한 줄 해석으로 풀어
        # "이 숫자가 좋은가?"에 답한다. REQ 임계값과 대조. 표시 전용.
        self._lbl_result_grade = QLabel("")
        self._lbl_result_grade.setTextFormat(Qt.TextFormat.RichText)
        self._lbl_result_grade.setWordWrap(True)
        self._lbl_result_grade.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse)
        self._lbl_result_grade.setVisible(False)
        layout.addWidget(self._lbl_result_grade)

        # Phase 3(백로그 5번): 활성 토글 반사실 영향 — "이 토글을 끄면 이번 판이
        # 어떻게 달라지나"를 고정 시드 단발 비교로 표시. "토글 켰는데 변화 0" 오해 해소.
        self._lbl_toggle_impact = QLabel("")
        self._lbl_toggle_impact.setTextFormat(Qt.TextFormat.RichText)
        self._lbl_toggle_impact.setWordWrap(True)
        self._lbl_toggle_impact.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse)
        self._lbl_toggle_impact.setStyleSheet(f"font-size:11px; padding:2px 14px;")
        self._lbl_toggle_impact.setVisible(False)
        layout.addWidget(self._lbl_toggle_impact)

        # 실행 설정 요약 — 어떤 시나리오·날씨·MC로 돌렸는지 한눈에
        self._lbl_run_summary = QLabel("")
        self._lbl_run_summary.setStyleSheet(
            f"color:{C_SUBTEXT}; font-size:11px; padding:1px 14px;")
        self._lbl_run_summary.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self._lbl_run_summary)

        # 침수·IFF 사고 요약 (관련 수치 있을 때만 표시)
        self._lbl_flood_iff = QLabel("")
        self._lbl_flood_iff.setStyleSheet(
            f"color:#d98880; font-size:11px; padding:0 14px 2px;")
        self._lbl_flood_iff.setVisible(False)
        layout.addWidget(self._lbl_flood_iff)

        # Pk 경고 + VLS 경고 + Export 버튼 + 시드 레이블 (한 행)
        notice_row = QWidget()
        notice_rl  = QHBoxLayout(notice_row)
        notice_rl.setContentsMargins(12, 2, 12, 0)
        notice_rl.setSpacing(12)

        lbl_pk_note = QLabel(
            "⚠  Pk 수치는 공개 자료 기반 추정값 (±15~20%) — 실측 데이터 아님")
        lbl_pk_note.setStyleSheet(
            f"color:#e67e22; font-size:11px;")
        notice_rl.addWidget(lbl_pk_note)

        self._lbl_vls_warn = QLabel("")
        self._lbl_vls_warn.setStyleSheet(
            f"color:{C_RED}; font-size:11px; font-weight:bold;")
        notice_rl.addWidget(self._lbl_vls_warn)
        notice_rl.addStretch()

        self.btn_excel = QPushButton("📊 Excel 보고서")
        self.btn_pdf   = QPushButton("📄 PDF 보고서")
        for b in [self.btn_excel, self.btn_pdf]:
            b.setFixedHeight(26)
            b.setStyleSheet(
                f"background:{C_PANEL}; color:{C_TEXT}; "
                f"border:1px solid #3a5a7a; font-size:14px; padding:0 8px;")
        self.btn_excel.clicked.connect(self._export_excel)
        self.btn_pdf.clicked.connect(self._export_pdf)
        notice_rl.addWidget(self.btn_excel)
        notice_rl.addWidget(self.btn_pdf)

        self._lbl_seed_used = QLabel("")   # 하위 호환용 (숨김)

        layout.addWidget(notice_row)

        # ── 사이드바 + QStackedWidget ─────────────────────────────────────
        self.tab_engagement  = EngagementAnalysisTab()
        self.tab_mc_canvas   = ChartPageWidget()
        self.tab_req         = self._build_req_tab()
        self.tab_log         = self._build_log_tab()
        self.tab_channel     = QWidget()   # v15.08.02 제거(채널 포화도)
        # 결과 탭 간소화로 제거된 항목들 — 스택 인덱스 매핑(0~25) 유지를 위해 빈 placeholder만 둠.
        #  v13.04.01: 시스템 모니터6·타임라인10·감도11·방위각13·위협유형15·취약시간16·이전비교17·날씨3
        #  v15.08.02: 채널 포화도5·비용 효과7·탄약 소모8·최소 재고12·서브시스템20·A/B22·공격결과24·히트맵25
        self.tab_sysmon      = QWidget()
        self.tab_cost_eff    = QWidget()   # v15.08.02 제거(비용 효과)
        self.tab_ammo_curve  = QWidget()   # v15.08.02 제거(탄약 소모)
        self.tab_ci          = ChartPageWidget()
        self.tab_timeline    = QWidget()
        self.tab_sensitivity = QWidget()
        self.tab_min_stock   = QWidget()   # v15.08.02 제거(최소 재고)
        self.tab_bearing     = QWidget()
        self.tab_req_radar   = QWidget()   # REQ 충족률은 REQ 판정 탭(2)에 통합 — 인덱스 유지용 placeholder
        self.tab_threat_type = QWidget()
        self.tab_vuln_time   = QWidget()
        self.tab_history     = QWidget()
        self.tab_weather     = QWidget()
        self.tab_stress      = ChartPageWidget()   # 스트레스 테스트 히트맵
        self.tab_sobol       = ChartPageWidget()   # Sobol 민감도 분석
        self.tab_subsystem   = QWidget()   # v15.08.02 제거(서브시스템 피해)
        self.tab_optimize    = ChartPageWidget()   # 최적 무기 조합 추천
        self.tab_ab_compare  = QWidget()   # v15.08.02 제거(A/B 편대 비교)
        self.tab_status_board = self._build_status_board_tab()  # v13.3 전황 지표판
        self.tab_strike      = QWidget()   # v15.08.02 제거(공격 결과)
        self.tab_heatmap     = QWidget()   # v15.08.02 제거(생존성 히트맵)

        # 사이드바 (v8.26: AccordionSidebar)
        self._sidebar = AccordionSidebar()
        self._sidebar.setFixedWidth(200)
        self._sidebar.setStyleSheet(
            f"border-right: 1px solid {C_BORDER};")

        # QStackedWidget (인덱스 0~25 유지 — AccordionSidebar와 동일 매핑)
        self._stack = QStackedWidget()
        for w in [
            self.tab_engagement,  # 0
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
            self.tab_subsystem,   # 20
            self.tab_optimize,    # 21
            self.tab_ab_compare,  # 22
            self.tab_status_board, # 23
            self.tab_strike,      # 24
            self.tab_heatmap,     # 25
        ]:
            self._stack.addWidget(w)

        # 연결
        self._sidebar.item_selected.connect(self._stack.setCurrentIndex)
        self._sidebar.item_selected.connect(self._on_page_changed)

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

        return outer
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
            9:  lambda: self._draw_ci_chart(self._mc),
            18: lambda: self._draw_stress_test(self._mc),
            19: lambda: self._draw_sobol_chart(self._mc),
            21: lambda: self._lazy_start_optimize(),
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

        # ── REQ 판정 & 충족률 (상단: 좌 radar 개요 + 우 판정 상세표) ──────────
        req_lbl = QLabel("  ✅  REQ 요구조건 판정 & 충족률")
        req_lbl.setStyleSheet(f"color:{C_TEXT}; font-size:13px; font-weight:bold; padding:4px 0;")
        layout.addWidget(req_lbl)

        top_row = QWidget()
        top_h = QHBoxLayout(top_row)
        top_h.setContentsMargins(0, 0, 0, 0)
        top_h.setSpacing(8)

        # 좌: 충족률 radar (PASS/FAIL 한눈에)
        self._req_radar_fig    = Figure(figsize=(4.2, 4), facecolor=C_BG)
        self._req_radar_canvas = FigureCanvas(self._req_radar_fig)
        self._req_radar_canvas.setMinimumWidth(300)
        self._req_radar_canvas.setMaximumWidth(400)
        _plot_req_radar(self._req_radar_fig, None, None, None)
        top_h.addWidget(self._req_radar_canvas)

        # 우: 판정 상세 테이블
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
        top_h.addWidget(self.req_table, stretch=1)

        layout.addWidget(top_row, stretch=2)

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

        # ── 교전 후 브리핑 (접이식) ───────────────────────────────────────────
        self._brief_toggle = QPushButton("▶  📋 교전 후 브리핑 — 클릭하여 펼치기")
        self._brief_toggle.setCheckable(True)
        self._brief_toggle.setChecked(False)
        self._brief_toggle.setFixedHeight(28)
        self._brief_toggle.setStyleSheet(
            f"QPushButton {{ background:{C_PANEL}; color:{C_TEXT}; "
            f"border:1px solid #30363d; border-radius:4px; "
            f"font-size:12px; font-weight:bold; text-align:left; padding:0 8px; }}"
            f"QPushButton:checked {{ border-color:#3a5a7a; }}"
        )
        layout.addWidget(self._brief_toggle)

        self._brief_panel = QWidget()
        self._brief_panel.setVisible(False)
        brief_pl = QVBoxLayout(self._brief_panel)
        brief_pl.setContentsMargins(0, 4, 0, 0)
        brief_pl.setSpacing(4)

        self._briefing_browser = QTextBrowser()
        self._briefing_browser.setFont(QFont('Consolas', 9))
        self._briefing_browser.setMinimumHeight(260)
        self._briefing_browser.setStyleSheet(
            f"QTextBrowser {{ background:{C_BG}; color:{C_TEXT}; "
            f"border:1px solid #30363d; border-radius:6px; padding:8px; }}"
        )
        brief_pl.addWidget(self._briefing_browser)

        brief_btn_row = QWidget()
        brief_btn_layout = QHBoxLayout(brief_btn_row)
        brief_btn_layout.setContentsMargins(0, 0, 0, 0)
        brief_btn_layout.setSpacing(6)
        brief_btn_layout.addStretch()
        btn_copy = QPushButton("📋 복사")
        btn_save_brief = QPushButton("💾 TXT 저장")
        for b in [btn_copy, btn_save_brief]:
            b.setFixedHeight(26)
            b.setStyleSheet(
                f"background:{C_PANEL}; color:{C_TEXT}; "
                f"border:1px solid #3a5a7a; font-size:13px; padding:0 8px;")
        btn_copy.clicked.connect(
            lambda: QApplication.clipboard().setText(self._briefing_browser.toPlainText()))
        btn_save_brief.clicked.connect(self._save_briefing_txt)
        brief_btn_layout.addWidget(btn_copy)
        brief_btn_layout.addWidget(btn_save_brief)
        brief_pl.addWidget(brief_btn_row)

        layout.addWidget(self._brief_panel)

        def _toggle_brief(checked):
            self._brief_panel.setVisible(checked)
            arrow = '▼' if checked else '▶'
            suffix = '' if checked else ' — 클릭하여 펼치기'
            self._brief_toggle.setText(f"{arrow}  📋 교전 후 브리핑{suffix}")

        self._brief_toggle.clicked.connect(_toggle_brief)
        return w
    _SB_CARD_DEFS = [
        ('ammo_eff',      '🎯  탄약 소모 효율',
         '요격 성공 ÷ 발사 미사일. 높을수록 한 발도 헛되이 쓰지 않은 정밀 교전.'),
        ('cost_per_kill', '💵  요격당 비용',
         '총 교전 비용 ÷ 요격 성공 수. 위협 1기를 막는 데 든 평균 비용(낮을수록 경제적).'),
        ('exchange',      '⚔  피아 교환비',
         '적 무력화(요격+격침) ÷ 아군 피격. 1 초과면 가한 피해가 입은 피해보다 큼.'),
        ('saturation',    '📡  방어 포화도',
         '동시 위협 ÷ 총 교전 채널. 1 이상이면 채널 한계 초과 — 누수 위험 급증.'),
    ]
    def _build_status_board_tab(self) -> QWidget:
        """전황 지표판 — 핵심 파생 지표를 한 화면 카드 그리드로 (대표 단일 시뮬 기준)."""
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        hdr = QLabel("  📋  전황 지표판 — 전술 판단용 핵심 파생 지표")
        hdr.setStyleSheet(f"color:{C_TEXT}; font-size:13px; font-weight:bold; padding:4px 0;")
        layout.addWidget(hdr)
        note = QLabel("  대표 단일 시뮬 기준. 무기 교체·편대 보강 판단의 즉시 근거로 활용하세요.")
        note.setStyleSheet(f"color:{C_SUBTEXT}; font-size:11px;")
        layout.addWidget(note)

        grid_w = QWidget()
        grid = QGridLayout(grid_w)
        grid.setContentsMargins(0, 6, 0, 6)
        grid.setSpacing(12)
        self._sb_cards: dict = {}
        self._sb_subs:  dict = {}
        self._sb_boxes: dict = {}   # groupbox 참조 — 전장 모드 제목 동적 변경용
        self._sb_card_tips = {key: tip for key, _, tip in self._SB_CARD_DEFS}
        for i, (key, title, tip) in enumerate(self._SB_CARD_DEFS):
            card = QGroupBox(title)
            card.setMinimumHeight(120)
            card.setToolTip(tip)
            self._sb_boxes[key] = card
            card.setStyleSheet(
                f"QGroupBox {{ background:{C_PANEL}; border:1px solid {C_BORDER};"
                f" border-radius:8px; margin-top:8px; padding:10px;"
                f" color:{C_TEXT}; font-size:13px; font-weight:bold; }}"
                f"QGroupBox::title {{ subcontrol-origin:margin; left:12px; padding:0 4px; }}")
            cl = QVBoxLayout(card)
            cl.setSpacing(2)
            val = QLabel("—")
            val.setAlignment(Qt.AlignmentFlag.AlignCenter)
            val.setFont(QFont('Malgun Gothic', 26, QFont.Weight.Bold))
            val.setStyleSheet(f"color:{C_ACCENT};")
            val.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            cl.addWidget(val)
            sub = QLabel("")
            sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
            sub.setWordWrap(True)
            sub.setStyleSheet(f"color:{C_SUBTEXT}; font-size:10px;")
            cl.addWidget(sub)
            grid.addWidget(card, i // 2, i % 2)
            self._sb_cards[key] = val
            self._sb_subs[key]  = sub
        layout.addWidget(grid_w)

        # 자동 해석 패널
        interp_box = QGroupBox("  🧭  자동 해석")
        interp_box.setStyleSheet(
            f"QGroupBox {{ background:#11202e; border:1px solid #1e3a4a; border-radius:8px;"
            f" margin-top:8px; padding:8px; color:{C_TEXT}; font-size:12px; font-weight:bold; }}"
            f"QGroupBox::title {{ subcontrol-origin:margin; left:12px; padding:0 4px; }}")
        ibl = QVBoxLayout(interp_box)
        self._sb_interp = QLabel("시뮬레이션을 실행하면 전황 해석이 표시됩니다.")
        self._sb_interp.setWordWrap(True)
        self._sb_interp.setStyleSheet(f"color:{C_SUBTEXT}; font-size:12px; font-weight:normal;")
        ibl.addWidget(self._sb_interp)
        layout.addWidget(interp_box)
        layout.addStretch()
        return w
    def _update_status_board(self, result: dict, mc: dict):
        """전황 지표판 4개 카드 + 자동 해석 갱신.
        단발: 대표 단일 시뮬 기준 / 지속 전장: MC 집계 기준(승률·임무점수·승리당 비용)."""
        GOOD, WARN, BAD = '#2ecc71', '#f39c12', '#e74c3c'

        def _set(key, text, color, sub):
            self._sb_cards[key].setText(text)
            self._sb_cards[key].setStyleSheet(f"color:{color};")
            self._sb_subs[key].setText(sub)

        def _retitle(key, title, tip):
            self._sb_boxes[key].setTitle(title)
            self._sb_boxes[key].setToolTip(tip)

        if result.get('outcome'):   # ── 지속 전장 모드 — MC 집계 기준 ──
            self._update_status_board_battle(result, mc, _set, _retitle, (GOOD, WARN, BAD))
            return

        # ── 단발 교전 모드 — 대표 단일 시뮬 기준 (카드 제목 원복) ──
        for key, title, tip in self._SB_CARD_DEFS:
            _retitle(key, title, tip)
        fired = result.get('total_missiles_fired', 0)
        intc  = result.get('intercepted_threats', 0)
        tot   = result.get('total_threats', 0)
        edst  = result.get('enemy_ships_destroyed', 0)
        fhit  = result.get('friendly_hits', 0)
        chan  = result.get('total_channels', 0)
        cost  = result.get('total_cost', 0.0)

        # 1) 탄약 소모 효율 = 요격 / 발사
        if fired > 0:
            eff = intc / fired
            _set('ammo_eff', f"{eff:.0%}",
                 GOOD if eff >= 0.5 else WARN if eff >= 0.3 else BAD,
                 f"요격 {intc} / 발사 {fired}발")
        else:
            _set('ammo_eff', "—", C_SUBTEXT, "발사 없음")

        # 2) 요격당 비용 ($M)
        if intc > 0:
            cpk = cost / intc / 1_000_000
            _set('cost_per_kill', f"${cpk:.2f}M",
                 GOOD if cpk <= 5 else WARN if cpk <= 15 else BAD,
                 f"총 ${cost/1_000_000:.1f}M / 요격 {intc}")
        else:
            _set('cost_per_kill', "—", C_SUBTEXT, "요격 없음")

        # 3) 피아 교환비 = (요격+격침) / 아군 피격
        gained = intc + edst
        if fhit == 0:
            _set('exchange', "무손실", GOOD, f"아군 피격 0 · 적 무력화 {gained}")
        else:
            ex = gained / fhit
            _set('exchange', f"{ex:.1f} : 1",
                 GOOD if ex >= 5 else WARN if ex >= 1 else BAD,
                 f"적 무력화 {gained} / 아군 피격 {fhit}")

        # 4) 방어 포화도 = 동시 위협 / 총 채널
        if chan > 0:
            sat = tot / chan
            _set('saturation', f"{sat:.2f}",
                 GOOD if sat < 0.7 else WARN if sat < 1.0 else BAD,
                 f"위협 {tot} / 채널 {chan}")
        else:
            _set('saturation', "—", C_SUBTEXT, "채널 정보 없음")

        # 자동 해석
        msgs = []
        if chan > 0 and tot / chan >= 1.0:
            msgs.append("⚠ 채널 포화 — 동시 위협이 교전 채널 한계를 넘어섰습니다. 추가 함정 편입 또는 CEC 활성화로 채널을 분산하세요.")
        if fhit > 0 and gained / fhit < 1.0:
            msgs.append("⚠ 교환비 열세 — 입은 피해가 가한 피해보다 큽니다. 외곽 요격(장사정 SAM) 비중을 높이세요.")
        if fired > 0 and intc / fired < 0.3:
            msgs.append("⚠ 탄약 효율 저조 — 요격당 소비 탄이 많습니다. 발사 교리(살보 수)·표적 배정을 점검하세요.")
        if intc > 0 and (cost / intc / 1_000_000) > 15:
            msgs.append("⚠ 고비용 교전 — 요격당 비용이 높습니다. 저가 무기(ESSM·CIWS) 계층 활용을 검토하세요.")
        if not msgs:
            msgs.append("✅ 주요 지표 양호 — 채널 여유·교환비 우세·탄약 효율 정상 범위입니다.")
        self._sb_interp.setText("\n".join(msgs))
    def _update_status_board_battle(self, result: dict, mc: dict, _set, _retitle, colors):
        """지속 전장 모드 전황 지표판 — MC 집계 기반 작전 지표.
        단일 시뮬은 승/패 하나의 확률 결과라, 비용효과는 MC 집계로 평가."""
        GOOD, WARN, BAD = colors
        wr   = mc.get('win_rate')
        dr   = mc.get('draw_rate', 0.0)
        lr   = mc.get('loss_rate', 0.0)
        mfs  = mc.get('mean_friendly_score')
        costs = mc.get('total_costs', []) or []
        mean_cost = (sum(costs) / len(costs)) if costs else result.get('total_cost', 0.0)
        tot  = result.get('total_threats', 0)
        chan = result.get('total_channels', 0)
        n    = mc.get('n', 0)

        # 카드 제목을 전장 의미로 교체 (기존 4칸 재활용)
        _retitle('ammo_eff',     '🏆  작전 승률',
                 'MC 반복에서 작전 승리(임무 달성) 비율. 높을수록 안정적으로 임무를 완수.')
        _retitle('cost_per_kill','💵  승리당 비용',
                 'MC 평균 교전 비용 ÷ 승률. 작전 1회 승리에 드는 기대 비용(낮을수록 경제적).')
        _retitle('exchange',     '🎖  평균 임무 점수',
                 'MC 평균 아군 임무 점수(0~100%). 자산 방어·해역 통제 등 작전 목표 종합 달성도.')
        _retitle('saturation',   '📡  방어 포화도',
                 '동시 위협 ÷ 총 교전 채널. 1 이상이면 채널 한계 초과 — 누수 위험 급증.')

        # 1) 작전 승률
        if wr is not None:
            _set('ammo_eff', f"{wr:.0%}",
                 GOOD if wr >= 0.5 else WARN if wr >= 0.2 else BAD,
                 f"승 {wr:.0%} / 무 {dr:.0%} / 패 {lr:.0%}  (MC {n}회)")
        else:
            _set('ammo_eff', "—", C_SUBTEXT, "MC 집계 없음")

        # 2) 승리당 비용 = MC 평균 비용 / 승률
        if wr and wr > 0:
            cpw = mean_cost / wr / 1_000_000
            _set('cost_per_kill', f"${cpw:.1f}M",
                 GOOD if cpw <= 30 else WARN if cpw <= 80 else BAD,
                 f"평균 ${mean_cost/1_000_000:.1f}M / 승률 {wr:.0%}")
        else:
            _set('cost_per_kill', "승리 없음", BAD,
                 f"평균 ${mean_cost/1_000_000:.1f}M / 승률 0%")

        # 3) 평균 임무 점수
        if mfs is not None:
            _set('exchange', f"{mfs:.0%}",
                 GOOD if mfs >= 0.5 else WARN if mfs >= 0.3 else BAD,
                 f"MC {n}회 평균 작전 목표 달성도")
        else:
            _set('exchange', "—", C_SUBTEXT, "MC 집계 없음")

        # 4) 방어 포화도 = 동시 위협 / 총 채널 (단일 시뮬 기준)
        if chan > 0:
            sat = tot / chan
            _set('saturation', f"{sat:.2f}",
                 GOOD if sat < 0.7 else WARN if sat < 1.0 else BAD,
                 f"위협 {tot} / 채널 {chan}")
        else:
            _set('saturation', "—", C_SUBTEXT, "채널 정보 없음")

        # 자동 해석 (전장 버전)
        msgs = []
        if wr is not None and wr < 0.5:
            msgs.append("⚠ 작전 승률 미달 — 편대 보강·방어 전술 조정이 필요합니다. 시계열·목표 달성판에서 취약 국면을 확인하세요.")
        if chan > 0 and tot / chan >= 1.0:
            msgs.append("⚠ 채널 포화 — 동시 위협이 교전 채널 한계를 넘어섰습니다. 추가 함정 편입 또는 CEC 활성화로 채널을 분산하세요.")
        if mfs is not None and mfs < 0.3:
            msgs.append("⚠ 임무 점수 저조 — 핵심 작전 목표(자산 방어 등) 달성도가 낮습니다. 판정 탭에서 미달 목표를 점검하세요.")
        if not msgs:
            msgs.append("✅ 작전 지표 양호 — 승률·임무 점수·채널 여유가 정상 범위입니다.")
        self._sb_interp.setText("\n".join(msgs))
    def _build_log_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # 교전 이벤트 로그 — 시각별 상세 표 (유형별 색상)
        hdr = QLabel("  📜  교전 이벤트 로그")
        hdr.setStyleSheet(f"color:{C_TEXT}; font-size:13px; font-weight:bold; padding:4px 0;")
        layout.addWidget(hdr)

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
        layout.addWidget(self.log_table, stretch=1)
        return w
    def _render_campaign_result(self, result: dict, elapsed: float):
        """v18.1 작전급 캠페인 결과 요약 렌더 (요격률·전술 MC 무관). 교전 분석 탭 배너 재사용.
        v18.6: campaign_mc(N회 반복 분포)가 있으면 상태줄을 MC 분포 요약으로 표시."""
        warn = '' if result.get('model_loaded', True) else '  ⚠ 예측모델 미적용(근사)'
        # v21.1 JCS 충돌 경고 — 각 군 독립 배정의 충돌을 지휘부가 알린다(관찰 only, 교전 무영향).
        #   지표를 결과에 넣기만 하고 화면에서 안 보여주면 v20 연안 방공처럼 '있어도 못 보는' 꼴이
        #   된다 → 여기서 소비. 경고 없으면 세그먼트 자체가 안 뜬다.
        _jcs = result.get('jcs_warnings') or []
        if _jcs:
            _ico = {'crit': '🔴', 'warn': '⚠', 'info': 'ℹ'}
            _seg = ' / '.join(f"{_ico.get(w['severity'], '·')}{w['msg']}" for w in _jcs)
            warn += f"  ⚖ JCS 충돌 경고 {len(_jcs)}건: {_seg}"
        fog = ' · 🌫 안개' if result.get('fog_enabled') else ''
        # v19.1: 공군 층 ON이면 평균 제공권 표시
        air = (f" · ✈ 제공권 {result.get('mean_air_superiority', 0)*100:.0f}%"
               if result.get('air_enabled') else '')
        # v19.3: SEAD ON이면 방공망 제압률 표시(air 세그먼트 뒤)
        sead = (f" · 🎯 방공망 제압 {result.get('ad_suppression', 0)*100:.0f}%"
                if result.get('sead_enabled') else '')
        # v19.4: 전략폭격 ON이면 적 기지 손상·출항능력 표시
        strike = (f" · 💥 적 기지 손상 {result.get('enemy_base_damage', 0)*100:.0f}% "
                  f"(출항 {result.get('enemy_output_factor', 1)*100:.0f}%)"
                  if result.get('strike_enabled') else '')
        # v19.5: CAS 근접 항공 지원 발동 시 소티·요청 표시
        cas = (f" · 🛩 근접지원 {result.get('air_cas_sorties', 0)}소티"
               if result.get('n_cas_requests', 0) > 0 else '')
        # v20: 연안 방공망·상륙작전 — 교전 분석 탭 배너는 UIA 밖이라 스모크로 검증할 수 없다.
        #   상태줄에도 요약을 띄워야 사용자에게 보이고 GUI 스모크가 감시할 수 있다(v18 교훈).
        _csites = result.get('coastal_sites') or {}
        coastal = ''
        if _csites:
            _rdy = (sum(v['readiness'] for v in _csites.values()) / len(_csites)) if _csites else 0.0
            coastal = (f" · 🛡 연안 방공 {_rdy*100:.0f}%"
                       f" (요격탄 {result.get('coastal_intercepts', 0)}발)")
            _sup = result.get('coastal_suppression', 0) or 0
            if _sup > 0.01:
                coastal += f" · ⚠ 적 SEAD 제압 {_sup*100:.0f}%"
        amphib = ''
        if result.get('amphib_enabled'):
            _st = {'embark': '승선', 'transit': '항해', 'assault': '상륙 중',
                   'beachhead': '교두보 확보', 'failed': '상륙 실패'}
            amphib = (f" · 🏖 상륙 {_st.get(result.get('amphib_state', ''), '-')}"
                      f" {result.get('amphib_progress', 0)*100:.0f}%")
        # v21.2: 합동 화력 ON이면 군별 기여도(누가 적 기지를 얼마나 무력화했나)를 띄운다.
        #   지표를 결과 dict에 넣기만 하고 화면에서 소비하지 않으면 사용자는 협조 타격이
        #   실제로 일어났는지 볼 수 없다 — v20 연안 방공이 겪은 그 문제(위 주석)를 반복 않는다.
        joint = ''
        if result.get('joint_fires'):
            _sh = result.get('joint_dmg_share') or {}
            joint = (f" · 🤝 합동 화력 (공군 {_sh.get('air', 0)*100:.0f}%"
                     f"/해군 {_sh.get('navy', 0)*100:.0f}%"
                     f"/육군 {_sh.get('army', 0)*100:.0f}%)"
                     f" 순항 {result.get('joint_navy_fired', 0)}발"
                     f"·지대지 {result.get('joint_army_fired', 0)}발")
            # 협조 미비·육군 미참여 경고는 v21.1 JCS 충돌 경고 세그먼트(위 warn)로 통합 —
            # 여기서 중복 표기하지 않는다(지휘부 관점 경고는 한 곳에서).
        mc = result.get('campaign_mc')
        if mc:
            # v18.6: N회 반복 → outcome 분포·평균 통제도 요약
            # v20: 연안 방공·상륙은 대표 전역이 아니라 MC 평균으로 표시(요격탄 평균·교두보 확보율).
            _mc_coastal = ''
            if _csites:
                _mc_coastal = (f" · 🛡 연안 방공 요격탄 {mc.get('coastal_intercepts_avg', 0):.0f}발"
                               f" (제압 {mc.get('coastal_suppression_avg', 0)*100:.0f}%)")
            _mc_amphib = ''
            if result.get('amphib_enabled'):
                _mc_amphib = (f" · 🏖 상륙 교두보 확보율 {mc.get('amphib_success_rate', 0)*100:.0f}%"
                              f" (평균 진척 {mc.get('amphib_progress_avg', 0)*100:.0f}%)")
            # v21.2: 합동 화력도 대표 전역이 아니라 MC 평균으로(순항·지대지 평균 발사수).
            _mc_joint = ''
            if result.get('joint_fires'):
                _mc_joint = (f" · 🤝 합동 화력 순항 {mc.get('joint_navy_fired_avg', 0):.0f}발"
                             f"·지대지 {mc.get('joint_army_fired_avg', 0):.0f}발"
                             f" (적 출항 {mc.get('enemy_output_factor_avg', 1)*100:.0f}%)"
                             # v21.4: 직접 계상(누가 실제로 표적을 때렸나)의 MC 평균.
                             #   반사실 기여도와 별개 값이라 나란히 둔다.
                             f" 타격분담 공군 {mc.get('joint_share_air_avg', 0)*100:.0f}%"
                             f"/해군 {mc.get('joint_share_navy_avg', 0)*100:.0f}%"
                             f"/육군 {mc.get('joint_share_army_avg', 0)*100:.0f}%")
            # v21.4: 반사실 기여도 요약. 상태줄에 띄워야 GUI 스모크가 감시할 수 있다
            #   (교전 분석 탭 배너는 UIA 밖 — v20 교훈, 위 주석과 같은 사유).
            _mc_report = ''
            _rp = result.get('joint_report') or {}
            if _rp:
                _s = _rp.get('shapley', {})
                _mc_report = (f" · 📊 군별 기여도 해군단독 "
                              f"{_rp.get('navy_baseline', {}).get('win_rate', 0)*100:.0f}%"
                              f"→합동 {_rp.get('grand', {}).get('win_rate', 0)*100:.0f}%"
                              f" (전략폭격 {_s.get('strike', {}).get('win_rate', 0)*100:+.0f}%p"
                              f"·지상 {_s.get('army', {}).get('win_rate', 0)*100:+.0f}%p)")
            self._lbl_status.setText(
                f"완료 ({elapsed:.1f}s) | 🗺 캠페인 MC {mc.get('n_runs', 0)}회: "
                f"🟢승 {mc.get('win_rate', 0)*100:.0f}% · "
                f"🟡무 {mc.get('draw_rate', 0)*100:.0f}% · "
                f"🔴패 {mc.get('loss_rate', 0)*100:.0f}% | "
                f"평균 통제도 {mc.get('mean_control_avg', 0)*100:.0f}%±{mc.get('mean_control_std', 0)*100:.0f} · "
                f"생존 {mc.get('surviving_avg', 0):.1f}/{result.get('n_ships', 0)} · "
                f"평균 비용 ${mc.get('cost_avg', 0)/1e6:.0f}M · "
                f"전역 {result.get('horizon_h', 72)}h"
                f"{fog}{air}{sead}{strike}{cas}{_mc_coastal}{_mc_amphib}{_mc_joint}{_mc_report}{warn}")
        else:
            oc = {'win': '🟢 승리', 'loss': '🔴 패배', 'draw': '🟡 무승부'}.get(
                result.get('outcome'), result.get('outcome', '—'))
            self._lbl_status.setText(
                f"완료 ({elapsed:.1f}s) | 🗺 캠페인: {oc} | "
                f"평균 통제도 {result.get('mean_control', 0.0)*100:.0f}% · "
                f"교전 {result.get('n_engagements', 0)}회 · "
                f"생존 함정 {result.get('surviving_ships', 0)}/{result.get('n_ships', 0)} · "
                f"전역 {result.get('end_h', 0)}h/{result.get('horizon_h', 72)}h"
                f"{fog}{air}{sead}{strike}{cas}{coastal}{amphib}{joint}{warn}")
        # 교전 분석 탭 배너(_fill_battle_panel이 campaign 분기 렌더) + 해당 탭 착지
        self.tab_engagement.load_result(result)
        self._sidebar.mark_new_data([0])
        self._sidebar.set_current_index(0)
        self._on_page_changed(0)   # 동일 인덱스면 item_selected 미발화 → 수동 트리거
    def _fill_req(self, result: dict, mc: dict):
        """포팅 D: REQ 판정 테이블 + 충족률 radar 채우기."""
        if not _V7_OK:
            return
        cfg = self._worker.cfg if self._worker else None
        # 충족률 radar (개요) 갱신
        try:
            _plot_req_radar(self._req_radar_fig, result, mc, cfg)
            self._req_radar_canvas.draw_idle()
        except Exception:
            pass
        if result.get('outcome'):   # 지속 전장 모드 — 목표 기반 REQ(동적 항목)
            items, verdicts, details = evaluate_req_battle_v7(result, mc, cfg)
        else:
            verdicts, details = evaluate_req_v7(result, mc, cfg)
            items = REQ_ITEMS_V7
        self.req_table.setRowCount(0)
        _fail_bg = QColor(231, 76, 60, 38)   # 실패 행 옅은 적색 배경 — 한눈에 식별
        for req, v, d in zip(items, verdicts, details):
            row = self.req_table.rowCount()
            self.req_table.insertRow(row)
            for col, text in enumerate([req['id'], req['name'],
                                        '✅ PASS' if v else '❌ FAIL', d]):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter
                                      if col != 3 else Qt.AlignmentFlag.AlignLeft
                                      | Qt.AlignmentFlag.AlignVCenter)
                if col == 2:
                    item.setForeground(QColor('#2ecc71' if v else '#e74c3c'))
                    f = item.font(); f.setBold(True); item.setFont(f)
                if not v:
                    item.setBackground(_fail_bg)   # 실패 행 전체 강조
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
    def _fill_briefing(self, result: dict, mc: dict, cfg: dict):
        """교전 후 브리핑 텍스트를 REQ 탭 하단 패널에 채운다."""
        if not _V7_OK:
            return
        text = generate_briefing(result, mc, cfg)
        self._briefing_browser.setPlainText(text)
    def _save_briefing_txt(self):
        """브리핑 텍스트를 TXT 파일로 저장."""
        text = self._briefing_browser.toPlainText()
        if not text.strip():
            QMessageBox.information(self, "안내", "먼저 시뮬레이션을 실행하세요.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "브리핑 저장", "briefing.txt", "Text (*.txt)")
        if not path:
            return
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)
        QMessageBox.information(self, "저장 완료", f"브리핑 저장:\n{path}")
    def _update_vls_warning(self, mc: dict):
        """MC 결과에서 VLS 주요 무기 소진률 + 고갈 확률·시각 확인 후 경고 레이블 갱신."""
        key_wpns = ['SM-3 Block IIA', 'SM-6', 'SM-2 Block IIIB']
        rates = mc.get('weapon_exhaustion_rates', {})
        critical, caution = [], []
        for w in key_wpns:
            r = rates.get(w, 0.0)
            if r >= 0.5:
                critical.append(f"{w} {r:.0%}")
            elif r >= 0.2:
                caution.append(f"{w} {r:.0%}")

        # v9.4: VLS 완전 고갈 확률 + 평균 고갈 시각
        dep_rate = mc.get('vls_depletion_rate', 0.0)
        dep_t    = mc.get('vls_depletion_t_mean', None)
        dep_suffix = ''
        if dep_rate > 0:
            dep_suffix = f"  |  VLS 완전 고갈 {dep_rate:.0%}"
            if dep_t is not None:
                dep_suffix += f" (평균 {dep_t:.0f}s)"

        if critical:
            self._lbl_vls_warn.setText(
                f"🔴 VLS 소진 경고: {' · '.join(critical)}{dep_suffix}")
            self._lbl_vls_warn.setStyleSheet(
                f"color:{C_RED}; font-size:11px; font-weight:bold;")
        elif caution:
            self._lbl_vls_warn.setText(
                f"🟠 VLS 소진 주의: {' · '.join(caution)}{dep_suffix}")
            self._lbl_vls_warn.setStyleSheet(
                f"color:{C_ORANGE}; font-size:11px; font-weight:bold;")
        elif dep_suffix:
            self._lbl_vls_warn.setText(f"🟡{dep_suffix.strip()}")
            self._lbl_vls_warn.setStyleSheet(
                f"color:{C_ORANGE}; font-size:11px;")
        else:
            self._lbl_vls_warn.setText("")
    def _update_run_summary(self, cfg):
        """결과 상단에 실행 설정 요약(아군·적 편대 / 날씨·해역 / MC 모드·횟수 / 시드) 표시."""
        if not cfg:
            self._lbl_run_summary.setText("")
            return
        fleet = cfg.get('fleet_preset', '—')
        if cfg.get('enemy_fleet_mode') == 'random':
            enemy = '랜덤 적편대'
        else:
            enemy = cfg.get('enemy_fleet_preset') or cfg.get('enemy_mode') or '—'
        wx     = cfg.get('weather', '—')
        region = cfg.get('fleet_region', '')
        mode_idx = getattr(self._worker, 'sim_mode_idx', cfg.get('sim_mode_idx', 1))
        mode   = _SIM_MODE_NAMES.get(mode_idx, '표준')
        mc_n   = getattr(self._worker, 'mc_n', None)
        seed   = cfg.get('sim_seed')
        parts = [f"🎯 {fleet}  vs  {enemy}",
                 f"🌤 {wx}" + (f" · {region}" if region else ""),
                 f"📊 {mode} MC {mc_n:,}회" if mc_n else f"📊 {mode}"]
        if seed is not None:
            parts.append(f"🎲 시드 {seed}")
        self._lbl_run_summary.setText("      |      ".join(parts))
    def _update_flood_iff_summary(self, mc: dict):
        """침수·IFF 통계를 관련 수치가 있을 때만 한 줄 표시 (없으면 숨김)."""
        parts = []
        f_sunk = mc.get('mean_ships_sunk_by_flood', 0.0)
        f_on   = mc.get('mean_ships_flooding', 0.0)
        if f_sunk > 0.005 or f_on > 0.005:
            seg = f"🌊 침수 침몰 평균 {f_sunk:.2f}척"
            if f_on > 0.005:
                seg += f" · 침수 발생 {f_on:.2f}척"
            parts.append(seg)
        i_fail = mc.get('mean_iff_failures', 0.0)
        i_frat = mc.get('mean_iff_fratricide', 0.0)
        if i_fail > 0.005 or i_frat > 0.005:
            seg = "🪪 IFF"
            if i_frat > 0.005:
                seg += f" 오인 발사 {i_frat:.2f}건"
            if i_fail > 0.005:
                seg += f"{' ·' if i_frat > 0.005 else ''} 식별 실패 {i_fail:.2f}건"
            parts.append(seg)
        if parts:
            self._lbl_flood_iff.setText("      |      ".join(parts))
            self._lbl_flood_iff.setVisible(True)
        else:
            self._lbl_flood_iff.setVisible(False)
    def _update_cards(self, result: dict, mc: dict):
        self._result_outer_stack.setCurrentIndex(1)
        if not self._in_results_mode:
            self._enter_results_mode()
        self._update_run_summary(self._worker.cfg if self._worker else None)
        self._update_flood_iff_summary(mc)
        # 비정상값 방어: 요격률·완전요격은 0~100% 범위를 벗어나면 경고색(주황)으로 표시
        m_int = mc['mean_intercept']
        _abn  = (m_int < 0.0 or m_int > 1.0)
        self._gauge.setValue(None if _abn else m_int)   # 요격률 게이지 갱신
        self._cards['intercept'].setText(f"{m_int:.1%}" + (" ⚠" if _abn else ""))
        self._cards['intercept'].setStyleSheet(
            f"color:{'#f39c12' if _abn else ('#2ecc71' if m_int >= 0.9 else '#e74c3c')};")
        f_pass = mc['full_pass_rate']
        _abn_fp = (f_pass < 0.0 or f_pass > 1.0)
        self._cards['full_pass'].setText(f"{f_pass:.1%}" + (" ⚠" if _abn_fp else ""))
        if _abn_fp:
            self._cards['full_pass'].setStyleSheet("color:#f39c12;")
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
        # 비용은 백만 달러($M) 단위로 표기 — 자릿수 긴 원달러 대신 보고서 관례에 맞춤
        self._cards['cost'].setText(f"${result['total_cost'] / 1_000_000:.1f}M")
        sorties = result.get('aircraft_sorties', 0)
        self._cards['aircraft'].setText(f"{sorties}회" if sorties else "—")
        # 이전 실행 대비 변화량(delta) 표시 — 직전 기록과 비교
        self._update_card_deltas(result, mc)
        # 결과 해석 배너 — "이 숫자가 좋은가?"에 등급+한 줄로 답
        self._update_result_grade(result, mc)
        # Phase 3: 활성 토글 반사실 영향 분석(비동기) — "이 토글이 이번 판을 바꿨나"
        if self._worker is not None:
            self._start_toggle_impact(self._worker.cfg)
    def _update_result_grade(self, result: dict, mc: dict):
        """결과 해석 배너 — 핵심 지표를 등급(우수/양호/미흡)+한 줄 해석으로 풀어
        "이 숫자가 좋은가?"에 답한다. 등급 경계는 요격률 게이지(90/60)와 일관,
        REQ 임계값(요격률 95%·전장 승률 50%)과 대조. 표시 전용(회귀 무관)."""
        lbl = getattr(self, '_lbl_result_grade', None)
        if lbl is None:
            return

        def _band(color, tag, text):
            lbl.setText(
                f"<span style='color:{color}; font-weight:bold;'>{tag}</span>"
                f"<span style='color:{C_SUBTEXT};'> — {text}</span>")
            lbl.setStyleSheet(
                f"font-size:12px; padding:5px 12px; margin:3px 12px 0;"
                f" background:{C_PANEL}; border-left:4px solid {color}; border-radius:4px;")
            lbl.setVisible(True)

        # ── 지속 전장 모드: 승률·임무점수 기준 ──────────────────────────
        wr = mc.get('win_rate')
        outcome = result.get('outcome')
        if wr is not None or outcome:
            if wr is not None:
                fs = mc.get('friendly_score')
                score_txt = f" · 임무점수 {fs:.0%}" if isinstance(fs, (int, float)) else ""
                if wr >= 0.70:
                    _band('#2ecc71', '🟢 작전 우세',
                          f"MC 작전 승률 {wr:.0%}{score_txt} — 작전 목표를 안정적으로 달성합니다.")
                elif wr >= 0.50:
                    _band('#f39c12', '🟡 우열 백중',
                          f"MC 작전 승률 {wr:.0%}{score_txt} — 승패가 갈리는 접전입니다. "
                          f"편성·전술을 보강하면 우세로 전환할 여지가 있습니다.")
                else:
                    _band('#e74c3c', '🔴 작전 열세',
                          f"MC 작전 승률 {wr:.0%}{score_txt} — 작전 목표 달성이 어렵습니다. "
                          f"전력 증강 또는 목표 재설정이 필요합니다.")
            else:
                _m = {'win':  ('#2ecc71', '🟢 작전 승리', '단일 작전에서 임무를 달성했습니다.'),
                      'draw': ('#f39c12', '🟡 작전 무승부',
                               '결판이 나지 않았습니다. 반복(MC) 분석으로 승률을 확인하세요.'),
                      'loss': ('#e74c3c', '🔴 작전 패배', '단일 작전에서 임무를 달성하지 못했습니다.')}
                c, t, d = _m.get(outcome, ('#95a5a6', '작전 종료', ''))
                _band(c, t, d)
            return

        # ── 단발 교전 모드: 요격률 중심 ──────────────────────────────────
        m_int = mc.get('mean_intercept', 0.0)
        if m_int < 0.0 or m_int > 1.0:
            lbl.setVisible(False)   # 비정상값은 카드 ⚠로 이미 표시
            return
        f_pass = mc.get('full_pass_rate', 0.0)
        hits = mc.get('friendly_hits', [])
        zero_hit = (sum(1 for h in hits if h == 0) / len(hits)) if hits else None
        req_txt = ("REQ 요격률 95% 충족" if m_int >= 0.95
                   else f"REQ 요격률 95% 기준 대비 {(0.95 - m_int) * 100:.0f}%p 미달")
        sub = f"완전요격 {f_pass:.0%}"
        if zero_hit is not None:
            sub += f" · 무피격 {zero_hit:.0%}"
        if m_int >= 0.90:
            _band('#2ecc71', '🟢 우수',
                  f"평균 요격률 {m_int:.0%} — 위협을 안정적으로 요격합니다. {req_txt}. ({sub})")
        elif m_int >= 0.60:
            _band('#f39c12', '🟡 양호',
                  f"평균 요격률 {m_int:.0%} — 상당수 요격하나 일부 누수가 있습니다. "
                  f"장거리 SAM(SM-6)·함정 수를 보강하면 향상 여지가 있습니다. {req_txt}. ({sub})")
        else:
            _band('#e74c3c', '🔴 미흡',
                  f"평균 요격률 {m_int:.0%} — 위협 다수가 방어망을 돌파합니다. "
                  f"편대 규모·요격 무기 재고를 재검토하세요. {req_txt}. ({sub})")
    def _update_card_deltas(self, result: dict, mc: dict):
        """직전 실행(_history[-1]) 대비 주요 지표 변화량을 카드 하단에 표시.
        요격률·완전요격은 상승=녹색(좋음), 비용은 상승=적색(나쁨)."""
        deltas = getattr(self, '_card_deltas', None)
        if not deltas:
            return
        prev = self._history[-1] if getattr(self, '_history', None) else None
        if not prev:
            for dl in deltas.values():
                dl.setText("")
            return

        def _fmt(dl, cur, old, unit, higher_is_good):
            if old is None:
                dl.setText("")
                return
            d = cur - old
            if abs(d) < 1e-9:
                dl.setText("± 0")
                dl.setStyleSheet(f"color:{C_SUBTEXT}; font-size:10px;")
                return
            arrow = "▲" if d > 0 else "▼"
            good  = (d > 0) == higher_is_good
            color = '#2ecc71' if good else '#e74c3c'
            dl.setText(f"{arrow} {d:+.1f}{unit} vs 직전")
            dl.setStyleSheet(f"color:{color}; font-size:10px;")

        _fmt(deltas['intercept'], mc['mean_intercept'] * 100,
             prev.get('mean_intercept', 0) * 100, "%p", True)
        _fmt(deltas['full_pass'], mc['full_pass_rate'] * 100,
             prev.get('full_pass_rate', 0) * 100, "%p", True)
        if 'total_cost' in prev:
            _fmt(deltas['cost'], result['total_cost'] / 1_000_000,
                 prev['total_cost'] / 1_000_000, "M", False)
        # 비교 데이터 없는 카드는 비움
        for k in ('cvar', 'friendly_hit', 'enemy_dest', 'aircraft'):
            deltas[k].setText("")
    def _draw_mc_chart(self, result: dict, mc: dict, cfg: dict):
        self.tab_mc_canvas.start_render(_render_mc_chart, result, mc, cfg)
    def _fill_log(self, log: list):
        # 교전 로그 — 최대 1000행(대규모전 591줄 여유) + 유형별 색상
        entries = log[-1000:] if len(log) > 1000 else log
        self.log_table.setUpdatesEnabled(False)
        self.log_table.setRowCount(0)
        for t, msg in entries:
            row = self.log_table.rowCount()
            self.log_table.insertRow(row)
            t_item = QTableWidgetItem(f"{t:.0f}s")
            t_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.log_table.setItem(row, 0, t_item)
            ev_item = QTableWidgetItem(msg)
            ev_item.setForeground(QColor(_LOG_CAT_COLOR[_classify_log_event(msg)]))
            self.log_table.setItem(row, 1, ev_item)
        self.log_table.setUpdatesEnabled(True)
    def _draw_ci_chart(self, mc: dict):
        self.tab_ci.start_render(_render_ci_chart, mc)
    def _draw_stress_test(self, mc: dict):
        self.tab_stress.start_render(_render_stress_test, mc.get('stress', {}))
    def _draw_sobol_chart(self, mc: dict):
        self.tab_sobol.start_render(_render_sobol_chart, mc.get('sobol', {}))
