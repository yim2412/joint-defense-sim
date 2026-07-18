"""MainWindow mixin — 쇼케이스 탭(원클릭 비교 시연) + 퀵스타트 배너.

app_main.py 분할 8/N (MainWindow mixin 분할). 의존은 PyQt6·app_theme·app_utils·
app_workers·scenarios뿐.
"""
from PyQt6.QtCore import Qt, QThread
from PyQt6.QtWidgets import (
    QGroupBox, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

from app_theme import C_ACCENT, C_BG, C_BORDER, C_PANEL, C_SUBTEXT, C_TEXT
from app_utils import _SHOWCASE_METRICS, _SHOWCASES, _load_app_state, _save_app_state, _write_log
from app_workers import ShowcaseCompareWorker
from scenarios import SCENARIO_LIBRARY


class ShowcaseMixin:
    def _build_showcase_page(self) -> QWidget:
        """실험적 기능별 쇼케이스 카드 목록. 원클릭 시나리오 로드 + ON/OFF 실측 비교."""
        page = QWidget()
        page.setStyleSheet(f"background:{C_BG};")
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # 상단 바: 뒤로가기 + 제목
        top = QWidget()
        top.setStyleSheet(f"background:{C_PANEL}; border-bottom:2px solid {C_ACCENT};")
        tl = QHBoxLayout(top)
        tl.setContentsMargins(10, 6, 10, 6)
        btn_back = QPushButton("←  설정으로")
        btn_back.setFixedHeight(28)
        btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_back.setStyleSheet(
            f"QPushButton {{ background:{C_PANEL}; color:{C_SUBTEXT}; border:1px solid {C_BORDER};"
            f" border-radius:4px; padding:0 12px; font-size:12px; }}"
            f"QPushButton:hover {{ color:{C_TEXT}; background:#1f2d40; }}"
        )
        btn_back.clicked.connect(lambda: self._main_stack.setCurrentIndex(0))
        tl.addWidget(btn_back)
        title = QLabel("🎬  실험적 기능 쇼케이스")
        title.setStyleSheet(f"color:{C_ACCENT}; font-size:15px; font-weight:bold; letter-spacing:1px;")
        tl.addWidget(title)
        tl.addStretch()
        outer.addWidget(top)

        # 안내 문구
        guide = QLabel(
            "각 실험적 기능의 효과가 극명히 드러나는 시나리오입니다. "
            "[시나리오 로드]로 설정에 한 번에 적용하거나, [직접 비교 실행]으로 "
            "그 기능을 끈 경우(OFF)와 켠 경우(ON)를 실제 몬테카를로로 대조해 보세요.")
        guide.setWordWrap(True)
        guide.setStyleSheet(f"color:{C_SUBTEXT}; font-size:12px; padding:10px 14px;")
        outer.addWidget(guide)

        # 카드 스크롤 영역
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea {{ border:none; background:{C_BG}; }}")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        holder = QWidget()
        holder.setStyleSheet(f"background:{C_BG};")
        hl = QVBoxLayout(holder)
        hl.setContentsMargins(14, 4, 14, 14)
        hl.setSpacing(12)

        self._showcase_cards: dict = {}
        for sc in _SHOWCASES:
            hl.addWidget(self._build_showcase_card(sc))
        hl.addStretch()

        scroll.setWidget(holder)
        outer.addWidget(scroll, stretch=1)
        return page
    def _build_showcase_card(self, sc: dict) -> QWidget:
        """쇼케이스 카드 1장 — 제목·설명·예상효과·버튼2 + 결과 라벨."""
        box = QGroupBox(sc['title'])
        box.setStyleSheet(
            f"QGroupBox {{ background:{C_PANEL}; border:1px solid {C_BORDER}; border-radius:6px;"
            f" margin-top:10px; padding:10px 12px 12px 12px; }}"
            f"QGroupBox::title {{ subcontrol-origin:margin; left:12px; padding:0 6px;"
            f" color:{C_ACCENT}; font-size:13px; font-weight:bold; }}"
        )
        v = QVBoxLayout(box)
        v.setSpacing(6)

        desc = QLabel(sc['desc'])
        desc.setWordWrap(True)
        desc.setStyleSheet(f"color:{C_TEXT}; font-size:12px;")
        v.addWidget(desc)

        exp = QLabel(f"📊 예상 효과 :  {sc['expected']}")
        exp.setWordWrap(True)
        exp.setStyleSheet(f"color:{C_SUBTEXT}; font-size:11px; font-style:italic;")
        v.addWidget(exp)

        # 버튼 행
        row = QHBoxLayout()
        row.setSpacing(8)
        btn_load = QPushButton("⚙  시나리오 로드")
        btn_load.setFixedHeight(30)
        btn_load.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_load.setStyleSheet(
            f"QPushButton {{ background:#1f2d40; color:{C_TEXT}; border:1px solid {C_BORDER};"
            f" border-radius:4px; padding:0 14px; font-size:12px; }}"
            f"QPushButton:hover {{ background:#26364d; }}"
        )
        btn_load.clicked.connect(lambda _, s=sc: self._load_showcase_scenario(s))
        row.addWidget(btn_load)

        btn_cmp = QPushButton("▶  직접 비교 실행 (ON/OFF)")
        btn_cmp.setFixedHeight(30)
        btn_cmp.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_cmp.setStyleSheet(
            f"QPushButton {{ background:{C_ACCENT}; color:#0b1220; border:none;"
            f" border-radius:4px; padding:0 14px; font-size:12px; font-weight:bold; }}"
            f"QPushButton:hover {{ background:#4db8ff; }}"
            f"QPushButton:disabled {{ background:{C_BORDER}; color:{C_SUBTEXT}; }}"
        )
        btn_cmp.clicked.connect(lambda _, s=sc: self._run_showcase_compare(s))
        row.addWidget(btn_cmp)
        row.addStretch()
        v.addLayout(row)

        result = QLabel("")
        result.setWordWrap(True)
        result.setTextFormat(Qt.TextFormat.RichText)
        result.setStyleSheet("font-size:12px; padding:2px;")
        result.hide()
        v.addWidget(result)

        self._showcase_cards[sc['key']] = {'btn': btn_cmp, 'result': result, 'sc': sc}
        return box
    def _load_showcase_scenario(self, sc: dict):
        """시나리오를 설정 UI에 세팅(대상 기능 ON) 후 설정 화면으로 전환."""
        cfg = dict(sc['scenario'])
        cfg[sc['toggle']] = True   # 로드 시 그 기능을 켠 상태로 — 바로 실행 가능
        self._restore_cfg(cfg)
        self._main_stack.setCurrentIndex(0)
        self._lbl_status.setText(f"🎬 '{sc['title']}' 시나리오 로드 완료 — 실행 버튼을 누르세요")
    def _run_showcase_compare(self, sc: dict):
        """대상 토글만 OFF↔ON으로 바꿔 MC 2회 비교 실행."""
        if getattr(self, '_showcase_worker', None) and self._showcase_worker.isRunning():
            return   # 중복 실행 방지
        # 현재 UI 기반 완전 cfg + 시나리오 override (UI는 건드리지 않음)
        base_cfg = self._build_cfg_from_ui()
        base_cfg.update(sc['scenario'])
        card = self._showcase_cards[sc['key']]
        card['btn'].setEnabled(False)
        card['result'].show()
        card['result'].setText(
            f"<span style='color:{C_SUBTEXT}'>⏳ 비교 분석 준비 중… "
            f"(OFF·ON 각 40회 몬테카를로)</span>")
        self._showcase_worker = ShowcaseCompareWorker(sc['toggle'], base_cfg, mc_n=40)
        self._showcase_worker.progress.connect(
            lambda msg, k=sc['key']: self._showcase_cards[k]['result'].setText(
                f"<span style='color:{C_SUBTEXT}'>⏳ {msg}</span>"))
        self._showcase_worker.done.connect(self._on_showcase_done)
        self._showcase_worker.failed.connect(self._on_showcase_failed)
        self._showcase_worker.start(QThread.Priority.LowPriority)
    def _on_showcase_done(self, key: str, mc_off: dict, mc_on: dict):
        card = self._showcase_cards.get(key)
        if not card:
            return
        card['btn'].setEnabled(True)
        sc = card['sc']
        rows = ["<table cellspacing='0' cellpadding='4' style='font-size:12px;'>"
                "<tr>"
                f"<td style='color:{C_SUBTEXT};'>지표</td>"
                f"<td style='color:{C_SUBTEXT};' align='right'>OFF</td>"
                f"<td style='color:{C_SUBTEXT};' align='center'>→</td>"
                f"<td style='color:{C_SUBTEXT};' align='right'>ON</td>"
                f"<td style='color:{C_SUBTEXT};' align='right'>변화</td></tr>"]
        for mk in sc['metrics']:
            if mk not in _SHOWCASE_METRICS:
                continue
            name, extract, unit, direction = _SHOWCASE_METRICS[mk]
            try:
                v_off = float(extract(mc_off)); v_on = float(extract(mc_on))
            except Exception:
                continue
            d = v_on - v_off

            def _fmt(v):
                if unit == '%':   return f"{v:.1f}%"
                if unit == 'M$':  return f"${v:.1f}M"
                return f"{v:.2f}{unit}"

            # 방향에 따른 개선/악화 색
            if direction == '+':
                good = d > 1e-9
            elif direction == '-':
                good = d < -1e-9
            else:
                good = None
            if abs(d) < 1e-9 or good is None:
                dcolor = C_SUBTEXT
            else:
                dcolor = '#2ecc71' if good else '#e74c3c'
            sign = '+' if d > 0 else ('' if d == 0 else '−')
            dtxt = f"{sign}{_fmt(abs(d))}" if unit != '%' else f"{sign}{abs(d):.1f}%p"
            rows.append(
                f"<tr><td style='color:{C_TEXT};'>{name}</td>"
                f"<td align='right' style='color:{C_TEXT};'>{_fmt(v_off)}</td>"
                f"<td align='center' style='color:{C_SUBTEXT};'>→</td>"
                f"<td align='right' style='color:{C_TEXT}; font-weight:bold;'>{_fmt(v_on)}</td>"
                f"<td align='right' style='color:{dcolor}; font-weight:bold;'>{dtxt}</td></tr>")
        rows.append("</table>")
        rows.append(
            f"<div style='color:{C_SUBTEXT}; font-size:10px; margin-top:2px;'>"
            f"토글 외 조건 동일 · OFF·ON 각 40회 MC · 시드/편차로 예상 효과와 다를 수 있음</div>")
        card['result'].setText(''.join(rows))
    def _on_showcase_failed(self, key: str, err: str):
        card = self._showcase_cards.get(key)
        if not card:
            return
        card['btn'].setEnabled(True)
        card['result'].setText(
            f"<span style='color:#e74c3c'>⚠ 비교 실행 실패 — 로그를 확인하세요.</span>")
        _write_log(f'[ERROR] 쇼케이스 비교 실패({key}): {err}')
    def _build_quickstart_banner(self) -> QWidget:
        """처음 사용자용 추천 시나리오 원클릭 배너 (기존 SCENARIO_LIBRARY 재사용).
        클릭 시 함정·위협·해역·날씨를 일괄 설정하고 실행 버튼으로 유도한다."""
        banner = QWidget()
        banner.setStyleSheet(
            f"background: qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            f" stop:0 #16324a, stop:1 {C_PANEL});"
            f" border-bottom:1px solid {C_BORDER}; border-left:4px solid {C_ACCENT};")
        bl = QVBoxLayout(banner)
        bl.setContentsMargins(14, 8, 14, 10)
        bl.setSpacing(6)

        head = QHBoxLayout(); head.setSpacing(8)
        title = QLabel("🚀  처음이신가요?  추천 시나리오로 바로 시작하세요")
        title.setStyleSheet(f"color:{C_TEXT}; font-size:13px; font-weight:bold;")
        head.addWidget(title)
        head.addStretch()
        btn_close = QPushButton("✕ 접기")
        btn_close.setFixedHeight(22)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet(
            f"QPushButton {{ background:transparent; color:{C_SUBTEXT};"
            f" border:1px solid {C_BORDER}; border-radius:3px; padding:0 8px; font-size:11px; }}"
            f"QPushButton:hover {{ color:{C_TEXT}; }}")
        btn_close.clicked.connect(lambda: self._toggle_quickstart_banner(False, remember=True))
        head.addWidget(btn_close)
        bl.addLayout(head)

        hint = QLabel("아래 상황을 누르면 함정·위협·해역·날씨가 한 번에 설정됩니다. "
                      "그다음 우측 [▶ 시뮬레이션 실행]만 누르면 결과를 볼 수 있습니다.")
        hint.setWordWrap(True)
        hint.setStyleSheet(f"color:{C_SUBTEXT}; font-size:11px;")
        bl.addWidget(hint)

        row = QHBoxLayout(); row.setSpacing(6)
        for name, d in SCENARIO_LIBRARY.items():
            b = QPushButton(name)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.setFixedHeight(30)
            b.setToolTip(f"{d.get('desc','')}\n\n권장: {d.get('recommend','')}")
            b.setStyleSheet(
                f"QPushButton {{ background:{C_ACCENT}; color:#0b1220; border:none;"
                f" border-radius:15px; padding:0 16px; font-size:12px; font-weight:bold; }}"
                f"QPushButton:hover {{ background:#4db8ff; }}")
            b.clicked.connect(lambda _, n=name: self._load_quickstart(n))
            row.addWidget(b)
        row.addStretch()
        bl.addLayout(row)
        return banner
    def _load_quickstart(self, name: str):
        """추천 시나리오를 설정 UI에 일괄 적용 (온보딩 원클릭). SCENARIO_LIBRARY 재사용."""
        sc = SCENARIO_LIBRARY.get(name)
        if not sc:
            return
        # 작전 시나리오 라디오 그룹도 동기화(숨김 콤보 경유)
        if hasattr(self, 'cmb_scenario'):
            idx = self.cmb_scenario.findText(name)
            if idx >= 0:
                self.cmb_scenario.setCurrentIndex(idx)
        self._restore_cfg(sc['cfg'])
        self._lbl_status.setText(
            f"🎯 '{name}' 시나리오 적용 완료 — 우측 [▶ 시뮬레이션 실행]을 누르세요")
    def _toggle_quickstart_banner(self, show=None, remember: bool = False):
        """온보딩 배너 표시/숨김. show=None이면 토글. remember=True면 app_state 저장."""
        if not hasattr(self, '_quickstart_banner'):
            return
        if show is None:
            show = not self._quickstart_banner.isVisible()
        self._quickstart_banner.setVisible(show)
        if remember:
            st = _load_app_state()
            st['quickstart_banner_hidden'] = (not show)
            _save_app_state(st)
