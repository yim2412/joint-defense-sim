"""
ui_dialogs — 런처의 모달 다이얼로그 계층.

app_main.py에서 분리. 함대 편성 커스텀, 전술 의사결정(교전 중 일시정지), 시뮬 로그 열람.

의존은 PyQt6·app_theme·app_utils·app_engine·ui_widgets·ui_charts뿐 — **app_main을
import하지 말 것**(즉시 순환).

CLAUDE.md 규칙: 콤보박스는 항상 `NoScrollComboBox`를 쓴다(스크롤 휠 오조작 방지).
"""

import os, sys, json, traceback

from PyQt6.QtWidgets import (
    QWidget, QDialog, QFrame, QLabel, QPushButton, QLineEdit, QRadioButton,
    QButtonGroup, QListWidget, QFileDialog, QMessageBox,
    QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QScrollBar,
)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal

from app_theme import (C_BG, C_PANEL, C_BORDER, C_ACCENT, C_TEXT, C_SUBTEXT,
                       C_GREEN, C_RED, C_ORANGE, _wire_chk_color)
from app_utils import (_write_log, _log_path, _save_json_log, _load_sim_db, _clear_sim_db)
from app_engine import V7_SHIP_DB, _V7_OK
from ui_widgets import NoScrollComboBox, NoScrollSpinBox
from ui_charts import (MplCanvas, ChartPageWidget, EngagementAnalysisTab,
                       _classify_log_event)

class FleetCustomDialog(QDialog):
    """아군 함대 직접 편성 — SHIP_DB 함정을 골라 척수를 지정한다.
    결과는 {type:count} dict(get_counts). 취소 시 QDialog.Rejected."""

    def __init__(self, initial: dict | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("✏️  아군 함대 직접 편성")
        self.setMinimumWidth(440)
        self.setModal(True)
        self.setStyleSheet(f"QDialog {{ background:{C_BG}; }}")
        self._counts = dict(initial) if initial else {}   # {type: count}

        root = QVBoxLayout(self)
        root.setSpacing(8)

        hint = QLabel("함정을 골라 담고 척수를 지정하세요. "
                      "무기 재고는 설정 화면의 재고값을 함정마다 적용합니다.")
        hint.setWordWrap(True)
        hint.setStyleSheet(f"color:{C_SUBTEXT}; font-size:11px;")
        root.addWidget(hint)

        # ── 함정 추가 행 ────────────────────────────────────────────────
        add_row = QWidget(); arl = QHBoxLayout(add_row)
        arl.setContentsMargins(0, 0, 0, 0)
        _al = QLabel("함정:"); _al.setStyleSheet(f"color:{C_TEXT}; font-size:12px;")
        arl.addWidget(_al)
        self._cmb = NoScrollComboBox()
        if _V7_OK:
            for k, v in V7_SHIP_DB.items():
                mark = "🤿 " if v.get('is_submarine') else "⚓ "
                self._cmb.addItem(mark + v.get('display', k), k)
        arl.addWidget(self._cmb, stretch=1)
        btn_add = QPushButton("+ 담기"); btn_add.setFixedHeight(26)
        btn_add.setStyleSheet(
            f"QPushButton {{ background:{C_PANEL}; color:{C_TEXT}; border:1px solid #30363d; "
            f"border-radius:6px; padding:2px 12px; }} "
            f"QPushButton:hover {{ border-color:{C_ACCENT}; }}")
        btn_add.clicked.connect(self._on_add)
        arl.addWidget(btn_add)
        root.addWidget(add_row)

        # ── 현재 편성 리스트 (동적) ─────────────────────────────────────
        lbl = QLabel("현재 편성")
        lbl.setStyleSheet(f"color:{C_SUBTEXT}; font-size:11px; font-weight:bold;")
        root.addWidget(lbl)
        self._list_w = QWidget(); self._list_l = QVBoxLayout(self._list_w)
        self._list_l.setContentsMargins(0, 0, 0, 0); self._list_l.setSpacing(3)
        root.addWidget(self._list_w)

        self._empty_lbl = QLabel("(비어 있음 — 최소 1척을 담아야 확정할 수 있습니다)")
        self._empty_lbl.setStyleSheet(f"color:{C_SUBTEXT}; font-size:11px;")
        root.addWidget(self._empty_lbl)
        root.addStretch()

        # ── 하단 버튼 ───────────────────────────────────────────────────
        btn_row = QWidget(); brl = QHBoxLayout(btn_row)
        brl.setContentsMargins(0, 0, 0, 0); brl.addStretch()
        btn_cancel = QPushButton("취소"); btn_cancel.setFixedHeight(28)
        btn_cancel.setStyleSheet(
            f"QPushButton {{ background:{C_PANEL}; color:{C_TEXT}; border:1px solid #30363d; "
            f"border-radius:6px; padding:4px 16px; }}")
        btn_cancel.clicked.connect(self.reject)
        self._btn_ok = QPushButton("확정"); self._btn_ok.setFixedHeight(28)
        self._btn_ok.setStyleSheet(
            f"QPushButton {{ background:{C_ACCENT}; color:white; font-weight:bold; "
            f"border-radius:6px; padding:4px 16px; }} "
            f"QPushButton:disabled {{ background:#30363d; color:{C_SUBTEXT}; }}")
        self._btn_ok.clicked.connect(self.accept)
        brl.addWidget(btn_cancel); brl.addWidget(self._btn_ok)
        root.addWidget(btn_row)

        self._rebuild()

    def _on_add(self):
        stype = self._cmb.currentData()
        if stype:
            self._counts[stype] = self._counts.get(stype, 0) + 1
            self._rebuild()

    def _on_spin(self, stype: str, n: int):
        # 척수 조정 — dict만 갱신(리스트 재생성 안 함 → 스핀박스 포커스 유지)
        if stype in self._counts:
            self._counts[stype] = int(n)

    def _remove(self, stype: str):
        self._counts.pop(stype, None)
        self._rebuild()

    def _rebuild(self):
        while self._list_l.count():
            it = self._list_l.takeAt(0)
            w = it.widget()
            if w:
                w.deleteLater()
        for stype, cnt in self._counts.items():
            row = QWidget(); rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 0, 0, 0); rl.setSpacing(4)
            disp = V7_SHIP_DB.get(stype, {}).get('display', stype) if _V7_OK else stype
            name_lbl = QLabel(disp)
            name_lbl.setStyleSheet(f"color:{C_TEXT}; font-size:12px;")
            rl.addWidget(name_lbl, stretch=1)
            spn = NoScrollSpinBox(); spn.setRange(1, 20); spn.setValue(int(cnt))
            spn.setFixedWidth(64)
            spn.valueChanged.connect(lambda v, t=stype: self._on_spin(t, v))
            rl.addWidget(spn)
            btn_del = QPushButton("✕"); btn_del.setFixedSize(24, 24)
            btn_del.setStyleSheet(
                f"QPushButton {{ background:transparent; color:{C_SUBTEXT}; border:none; }} "
                f"QPushButton:hover {{ color:#e05252; }}")
            btn_del.clicked.connect(lambda _, t=stype: self._remove(t))
            rl.addWidget(btn_del)
            self._list_l.addWidget(row)
        has = bool(self._counts)
        self._empty_lbl.setVisible(not has)
        self._btn_ok.setEnabled(has)

    def get_counts(self) -> dict:
        """확정된 편성 {type:count}. 삽입 순서 보존."""
        return dict(self._counts)


# ════════════════════════════════════════════════════════════════════════════
#  v10.7: 전술 의사결정 다이얼로그
# ════════════════════════════════════════════════════════════════════════════
class TacticalDialog(QDialog):
    """전술 의사결정 — 시뮬 일시정지 시 위협 현황 + 무기 선택 패널."""

    def __init__(self, state: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"⚔️  전술 의사결정  —  T={state['t']:.0f}s")
        self.setMinimumWidth(520)
        self.setModal(True)
        self._choice = {}

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # ── 현황 요약 ─────────────────────────────────────────────────────────
        hdr = QLabel(f"<b>T = {state['t']:.0f}s</b>  |  "
                     f"요격 {state['intercepted']}/{state['total_threats']}  |  "
                     f"발사 {state['shots_fired']}발")
        hdr.setStyleSheet(f"color:{C_ACCENT}; font-size:14px; padding:4px;")
        layout.addWidget(hdr)

        # 위협 목록
        threats = state.get('threats', [])
        if threats:
            tlbl = QLabel(f"현존 위협 {len(threats)}개:")
            tlbl.setStyleSheet(f"color:{C_TEXT}; font-size:12px;")
            layout.addWidget(tlbl)
            tbl = QTableWidget(len(threats), 4)
            tbl.setHorizontalHeaderLabels(["명칭", "유형", "HP", "거리(km)"])
            tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            tbl.setColumnWidth(1, 70); tbl.setColumnWidth(2, 40); tbl.setColumnWidth(3, 70)
            tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            tbl.setMaximumHeight(120)
            for r, t in enumerate(threats):
                for c, v in enumerate([t['name'], t['type'], str(t['hp']), str(t['dist_km'])]):
                    item = QTableWidgetItem(v)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    tbl.setItem(r, c, item)
            layout.addWidget(tbl)

        # 아군 함정 상태
        ships = state.get('ships', [])
        if ships:
            slbl = QLabel("아군 함정 상태:")
            slbl.setStyleSheet(f"color:{C_TEXT}; font-size:12px;")
            layout.addWidget(slbl)
            stbl = QTableWidget(len(ships), 4)
            stbl.setHorizontalHeaderLabels(["함정", "HP", "레이더", "속도"])
            stbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            stbl.setColumnWidth(1, 40); stbl.setColumnWidth(2, 60); stbl.setColumnWidth(3, 60)
            stbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            stbl.setMaximumHeight(100)
            for r, s in enumerate(ships):
                alive_mark = "✅" if s['alive'] else "❌"
                for c, v in enumerate([f"{alive_mark} {s['name']}",
                                        f"{s['hp']}/{s['max_hp']}",
                                        f"{s['radar']:.0%}",
                                        f"{s['speed']:.0%}"]):
                    item = QTableWidgetItem(v)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    stbl.setItem(r, c, item)
            layout.addWidget(stbl)

        # ── 전술 선택 ─────────────────────────────────────────────────────────
        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)

        opt_lbl = QLabel("다음 구간 무기 우선순위:")
        opt_lbl.setStyleSheet(f"color:{C_TEXT}; font-weight:bold;")
        layout.addWidget(opt_lbl)

        self._wpn_group = QButtonGroup(self)
        wpn_row = QHBoxLayout()
        for label, val in [("자동 (기본)", "auto"), ("SM-2", "SM-2 Block IIIB"),
                            ("SM-6", "SM-6"), ("ESSM", "ESSM Block II")]:
            rb = QRadioButton(label)
            rb.setStyleSheet(f"color:{C_TEXT};")
            rb.setProperty("wpn_val", val)
            if val == "auto":
                rb.setChecked(True)
            self._wpn_group.addButton(rb)
            wpn_row.addWidget(rb)
        layout.addLayout(wpn_row)

        salvo_row = QHBoxLayout()
        _salvo_lbl = QLabel("살보 수:")
        _salvo_lbl.setToolTip(
            "다음 구간 최대 살보 수 설정.\n"
            "HGV·탄도탄 등 고위협 표적은 위협별 최솟값(2~3발)이\n"
            "자동으로 보장됩니다 (설정값이 최솟값보다 낮아도 무시)."
        )
        salvo_row.addWidget(_salvo_lbl)
        self._spn_salvo = NoScrollSpinBox()
        self._spn_salvo.setRange(1, 3)
        self._spn_salvo.setValue(1)
        self._spn_salvo.setFixedWidth(60)
        self._spn_salvo.setToolTip(
            "1: 탄약 절약 (저위협 상황)\n"
            "2: 표준 (Shoot-Look-Shoot)\n"
            "3: 최대 화력 (HGV·포화공격 대응)\n"
            "※ HGV는 자동으로 최소 3발 보장"
        )
        salvo_row.addWidget(self._spn_salvo)
        salvo_row.addStretch()
        layout.addLayout(salvo_row)

        # ── 버튼 ──────────────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_cont = QPushButton("▶  계속 진행")
        btn_cont.setStyleSheet(
            f"background:{C_ACCENT}; color:white; font-weight:bold; padding:6px 20px;")
        btn_cont.clicked.connect(self._on_continue)
        btn_row.addStretch(); btn_row.addWidget(btn_cont)
        layout.addLayout(btn_row)

    def _on_continue(self):
        checked = self._wpn_group.checkedButton()
        self._choice = {
            'weapon_priority': checked.property("wpn_val") if checked else 'auto',
            'max_salvo':       self._spn_salvo.value(),
        }
        self.accept()

    def get_choice(self) -> dict:
        return self._choice


# ════════════════════════════════════════════════════════════════════════════
class SimLogDialog(QDialog):
    """sim_history.db (SQLite)를 읽어 테이블로 표시하는 독립 창."""

    restore_requested = pyqtSignal(dict)   # cfg_json 딕셔너리 emit

    _COLS = [
        ('날짜/시각',    'datetime',           180),
        ('편대',         'fleet',              140),
        ('날씨',         'weather',            110),
        ('모드',         'sim_mode',            55),
        ('상태',         'status',              60),
        ('MC',           'mc_n',                55),
        ('총 위협',      'total_threats',       70),
        ('작전결과',     'outcome',             70),   # 전장 모드 — 단발은 '—'
        ('승률',         'win_rate',            60),   # 전장 MC 승률
        ('임무점수',     'friendly_score',      70),   # 전장 아군 임무 점수
        ('요격률',       'mean_intercept',      80),
        ('± 편차',       'std_intercept',       65),
        ('완전요격',     'full_pass_rate',      75),
        ('CVaR',         'cvar',                70),
        ('REQ',          'req_pass',            50),
        ('아군 피격',    'avg_friendly_hits',   75),
        ('비용 ($M)',    'total_cost',          90),
        ('적군 구성',    'enemy',                0),   # 0 = stretch
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._records: list = []   # BUG-1: textChanged가 _load() 전에 발화하면 AttributeError
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

        self._btn_restore = QPushButton("⬅  설정 복원")
        self._btn_restore.setFixedHeight(28)
        self._btn_restore.setEnabled(False)
        self._btn_restore.setStyleSheet(
            f"QPushButton {{ background:{C_PANEL}; color:{C_ACCENT}; border:1px solid #1a3a5c;"
            f" border-radius:4px; padding:0 12px; }}"
            f"QPushButton:hover {{ background:#0a1a2a; }}"
            f"QPushButton:disabled {{ color:{C_SUBTEXT}; border-color:{C_BORDER}; }}"
        )
        self._btn_restore.clicked.connect(self._restore_selected)

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
        bar.addWidget(self._btn_restore)
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

        # QTableWidget에는 currentRowChanged가 없음(QListWidget 전용) → currentCellChanged 사용
        self._tbl.currentCellChanged.connect(
            lambda r, c, pr, pc: self._show_detail(r))
        self._tbl.currentCellChanged.connect(
            lambda r, c, pr, pc: self._btn_restore.setEnabled(r >= 0))

        root.addWidget(self._tbl, stretch=1)
        root.addWidget(self._detail)

    # ── 데이터 처리 ────────────────────────────────────────────────────────
    def _load(self):
        # QTimer.singleShot 콜백이라 여기서 예외가 새면 앱이 abort(팅김) → 반드시 방어
        try:
            self._records = _load_sim_db()   # SQLite — 이미 최신순(DESC)
            self._apply_filter(self._search.text())
        except Exception:
            _write_log(f'[ERROR] 실행 로그 로드 실패: {traceback.format_exc()}')
            self._records = []
            try:
                self._fill_table([])
                self._lbl_count.setText("로그 로드 실패 — 형식 오류 (sim_history.log 참고)")
            except Exception:
                pass

    def _apply_filter(self, text: str):
        kw = text.strip().lower()
        filtered = [
            r for r in self._records
            if not kw or any(kw in str(v).lower() for v in r.values())
        ]
        self._fill_table(filtered)
        self._lbl_count.setText(f"총 {len(filtered)}건")

    def _fill_table(self, records: list):
        tbl = self._tbl
        tbl.setSortingEnabled(False)
        tbl.setUpdatesEnabled(False)
        try:
            tbl.setRowCount(len(records))
            for row, rec in enumerate(records):
                cvar = rec.get('cvar')
                req  = rec.get('req_pass')
                # 전장 모드 컬럼 (단발은 NULL → '—')
                _oc   = rec.get('outcome')
                _ocs  = {'win': '🟢 승', 'loss': '🔴 패', 'draw': '🟡 무'}.get(_oc, '—')
                _wr   = rec.get('win_rate')
                _fs   = rec.get('friendly_score')
                # None-safe: DB 값이 NULL이면 .get(k, 0)이 None을 반환 → 포맷 시 TypeError로
                # 앱이 죽으므로 (rec.get(k) or 0) 패턴으로 강제 숫자화
                values = [
                    rec.get('datetime', '') or '',
                    rec.get('fleet', '') or '',
                    rec.get('weather', '') or '',
                    rec.get('sim_mode', '—') or '—',
                    rec.get('status', '완료') or '완료',
                    str(rec.get('mc_n', '') if rec.get('mc_n') is not None else ''),
                    str(rec.get('total_threats', '') if rec.get('total_threats') is not None else ''),
                    _ocs,
                    f"{_wr:.0%}" if _wr is not None else '—',
                    f"{_fs:.0%}" if _fs is not None else '—',
                    f"{(rec.get('mean_intercept') or 0):.1%}",
                    f"±{(rec.get('std_intercept') or 0):.1%}",
                    f"{(rec.get('full_pass_rate') or 0):.1%}",
                    f"{cvar:.1%}" if cvar is not None else '—',
                    ('✅' if req == 1 else '❌' if req == 0 else '—'),
                    f"{(rec.get('avg_friendly_hits') or 0):.1f}",
                    f"{(rec.get('total_cost') or 0) / 1e6:.1f}",
                    rec.get('enemy', '') or '',
                ]
                last_col = len(self._COLS) - 1
                for col, val in enumerate(values):
                    item = QTableWidgetItem(val)
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignCenter
                        if col != last_col
                        else Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                    if col == 4:   # 상태 — 중단은 주황으로 구분
                        if (rec.get('status') or '완료') == '중단':
                            item.setForeground(QColor('#f39c12'))
                    if col == 7 and _oc:   # 작전결과 — 승/무/패 색상
                        item.setForeground(QColor(
                            C_GREEN if _oc == 'win' else
                            '#f1c40f' if _oc == 'draw' else '#e74c3c'))
                    if col == 10:   # 요격률 (작전결과·승률·임무점수 3컬럼 삽입으로 7→10)
                        rate = rec.get('mean_intercept') or 0
                        item.setForeground(QColor(
                            C_GREEN if rate >= 0.8 else
                            '#f39c12' if rate >= 0.5 else
                            '#e74c3c'))
                    if col == 13 and cvar is not None:   # CVaR (10→13)
                        item.setForeground(QColor(
                            C_GREEN if cvar >= 0.7 else
                            '#f39c12' if cvar >= 0.4 else
                            '#e74c3c'))
                    tbl.setItem(row, col, item)
                tbl.item(row, 0).setData(Qt.ItemDataRole.UserRole, rec)
        finally:
            tbl.setUpdatesEnabled(True)
            tbl.setSortingEnabled(True)

    def _show_detail(self, row: int):
        if row < 0:
            return
        item = self._tbl.item(row, 0)
        if not item:
            return
        rec = item.data(Qt.ItemDataRole.UserRole)
        if not rec:
            return
        cvar = rec.get('cvar')
        req  = rec.get('req_pass')
        cvar_str = f"{cvar:.1%}" if cvar is not None else '—'
        req_str  = ('✅ PASS' if req == 1 else '❌ FAIL' if req == 0 else '—')
        self._detail.setText(
            f"<b>{rec.get('datetime','')}</b> &nbsp;|&nbsp; "
            f"편대: <b>{rec.get('fleet','')}</b> &nbsp;|&nbsp; "
            f"날씨: {rec.get('weather','')} &nbsp;|&nbsp; "
            f"모드: {rec.get('sim_mode','—')} / MC: {rec.get('mc_n','')}회 &nbsp;|&nbsp; "
            f"위협: {rec.get('total_threats','')}발/기<br>"
            f"요격률: <b>{(rec.get('mean_intercept') or 0):.1%}</b> "
            f"(±{(rec.get('std_intercept') or 0):.1%}) &nbsp;|&nbsp; "
            f"완전요격: {(rec.get('full_pass_rate') or 0):.1%} &nbsp;|&nbsp; "
            f"CVaR: {cvar_str} &nbsp;|&nbsp; REQ: {req_str} &nbsp;|&nbsp; "
            f"비용: ${(rec.get('total_cost') or 0):,.0f}<br>"
            f"<span style='color:{C_SUBTEXT}'>적군: {rec.get('enemy','')}</span>"
        )

    def _restore_selected(self):
        row = self._tbl.currentRow()
        if row < 0:
            return
        item = self._tbl.item(row, 0)
        if not item:
            return
        rec = item.data(Qt.ItemDataRole.UserRole)
        if not rec:
            return
        cfg_str = rec.get('cfg_json', '')
        if not cfg_str:
            QMessageBox.warning(self, "복원 불가", "이 기록에는 설정 정보가 없습니다.")
            return
        try:
            cfg = json.loads(cfg_str)
        except Exception:
            QMessageBox.warning(self, "복원 오류", "설정 JSON 파싱 실패.")
            return
        self.restore_requested.emit(cfg)
        self.accept()

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
        _clear_sim_db()
        # 레거시 JSON/텍스트 로그도 함께 초기화
        _save_json_log([])
        try:
            open(_log_path(), 'w', encoding='utf-8').close()
        except Exception:
            pass
        self._load()
