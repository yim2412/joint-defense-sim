"""
v14.1 PoC — QtWebEngine + CesiumJS 빌드 검증 (3D 전장 착수 1단계)

목적: QWebEngineView가 (1) 개발 모드와 (2) PyInstaller exe 모두에서
      CesiumJS(WebGL)를 렌더링하고 온라인 타일을 로드하는지 확인.
      이게 v14.1 최대 리스크 — 통과하면 나머지(CZML 변환·탭 통합)는 수월.

실행:  python poc_cesium.py            (개발 모드)
       python poc_cesium.py --selftest (5초 후 자동 종료, 콘솔 로그만 확인)

토큰:  cesium_token.txt 에 Cesium ion 액세스 토큰을 한 줄로 저장 (gitignore됨).
       없어도 기본 지구본은 뜸 — WebGL 자체 검증은 토큰 불필요.
"""
import sys
from pathlib import Path

# Windows 콘솔(cp949)에서 한글·유니코드 로그 print 시 UnicodeEncodeError 방지
for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from PyQt6.QtWidgets import QApplication, QMainWindow
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage
from PyQt6.QtCore import QUrl, QTimer

# PyInstaller onefile/onedir 양쪽에서 동작하는 리소스 경로
BASE = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))


class _LoggingPage(QWebEnginePage):
    """JS console.* 메시지를 파이썬 stdout으로 중계 — exe 디버깅 핵심."""
    def javaScriptConsoleMessage(self, level, message, line, source):
        print(f"  [JS] {message}  (line {line})", flush=True)


def _load_token() -> str:
    f = BASE / "cesium_token.txt"
    if not f.exists():
        print("!! cesium_token.txt 없음 — 토큰을 한 줄로 저장하세요 (없어도 지구본은 뜸).", flush=True)
        return ""
    tok = f.read_text(encoding="utf-8").strip()
    if not tok:
        print("!! cesium_token.txt 비어 있음.", flush=True)
    return tok


def main():
    selftest = "--selftest" in sys.argv
    app = QApplication(sys.argv)

    token = _load_token()
    html = (BASE / "cesium_view.html").read_text(encoding="utf-8")
    html = html.replace("__CESIUM_ION_TOKEN__", token)

    win = QMainWindow()
    win.setWindowTitle("Cesium PoC — v14.1 3D 전장 빌드 검증")
    win.resize(1180, 780)

    view = QWebEngineView()
    view.setPage(_LoggingPage(view))
    # https baseUrl → secure context로 취급되어 CDN(https)·WebGL 정상 로드
    view.setHtml(html, QUrl("https://localhost/"))
    win.setCentralWidget(view)
    win.show()

    if selftest:
        # 콘솔 로그만 수집하고 자동 종료 (창 시각 확인은 사람이)
        QTimer.singleShot(5000, app.quit)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
