"""
app_theme — 런처 UI의 색상 팔레트·체크박스 스타일 헬퍼.

app_main.py에서 분리. 모든 UI 모듈(app_main·ui_widgets 등)이 이 모듈을 참조하므로
**여기서 다른 앱 모듈을 import하면 즉시 순환**이 된다 — PyQt6 외 의존을 두지 말 것.

⚠ `CHART_DPI`는 일부러 app_main.py에 남겼다. main()이 화면 크기로 **재할당**하는 전역이라,
여기로 옮겨 이름 import하면 150에 고정돼 DPI 자동 감지가 조용히 죽는다.
(같은 함정: app_utils._GLOBAL_POOL — 이름 import 금지, 모듈 경유 참조)
"""

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

def _wire_chk_color(chk, font_size: int = 13) -> None:
    """체크 여부에 따라 라벨 색상 변경(체크=흰색/미체크=빨간색) + 인디케이터 스타일."""
    # 체크 여부 구별: 미체크=어두운 빈 칸/회색 테두리, 체크=녹색 채움/흰 테두리(ON 신호)
    _IND = (
        f"QCheckBox::indicator{{width:18px;height:18px;"
        f"border:2px solid #5a6b7a;border-radius:4px;background:#0d1117;}}"
        f"QCheckBox::indicator:checked{{background:{C_GREEN};border:2px solid #ffffff;}}"
        f"QCheckBox::indicator:hover{{border-color:#a0c0d8;background:#1c2733;}}"
        f"QCheckBox::indicator:checked:hover{{background:#27ae60;border:2px solid #ffffff;}}"
    )
    def _upd(state: int):
        color = C_TEXT if state else C_RED
        # QCheckBox{...} 블록으로 감싸야 함 — 인라인 속성 뒤에 selector 블록을 붙이면
        # QSS 파서가 indicator 블록을 무시해 indicator 스타일이 적용되지 않았음(버그)
        chk.setStyleSheet(
            f"QCheckBox{{color:{color};font-size:{font_size}px;}}" + _IND)
    chk.stateChanged.connect(_upd)
    _upd(2 if chk.isChecked() else 0)
