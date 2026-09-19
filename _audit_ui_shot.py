# -*- coding: utf-8 -*-
"""
_audit_ui_shot.py — UI 시각 감사 (화면을 점유하지 않고 검사·캡처).

**왜 있나**: BLIND_SPOTS의 "UI 시각적 깨짐"은 오랫동안 *사람 눈 몫*이었다. 그런데
2026-09-19 묶음 C·A·B에서 이 방식으로 **QLabel `&&` 표기, 버튼 세로 잘림, 스크롤바가
글자를 덮는 문제, 정밀도 안내 문구 stale, 실험적 레이블 수 오카운트**를 전부 잡았다.
같은 1회용 프로브를 다섯 번 쓴 뒤라 도구로 굳힌다.

**핵심 기법**: `WA_DontShowOnScreen` + `widget.grab()`.
창을 만들되 **화면에 띄우지 않고** 렌더 결과만 받는다 → 사용자가 다른 모니터에서
작업·게임 중이어도 방해하지 않는다. (3D 탭은 QWebEngine이라 실제 창이 필요해 제외.)

**주의(실측 교훈)**: 오프스크린 플랫폼(`-platform offscreen`)을 쓰면 폰트 DB가 비어
이모지가 두부(□)로 보인다 — 실제 앱은 정상인데 두 번 오판할 뻔했다. 그래서 이 도구는
**기본 플랫폼**을 쓰고 `WA_DontShowOnScreen`으로만 화면 점유를 피한다.

사용:
    python _audit_ui_shot.py            # 검사만(종료코드 0/1)
    python _audit_ui_shot.py --shot DIR # 검사 + 전체 화면 캡처 저장
"""
import re
import sys

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QCheckBox, QLabel, QPushButton

# 잘림 판정 여유(px). 이모지 폰트 대체로 sizeHint가 과대 보고되는 경우가 있어
# 0으로 두면 오탐이 난다(2026-09-19: 시나리오 버튼 2건이 그 사례였다).
_SLACK_W = 2
_SLACK_H = 12


def _visible_text_widgets(win):
    for cls in (QLabel, QCheckBox, QPushButton):
        for w in win.findChildren(cls):
            try:
                if w.isVisible() and w.text().strip():
                    yield w
            except Exception:
                continue


def audit(win) -> list:
    """(카테고리, 설명) 목록 — 비어 있으면 통과."""
    issues = []

    # ① QLabel의 '&&' — QGroupBox와 달리 QLabel은 &를 이스케이프하지 않는다.
    #    화면에 && 두 글자가 그대로 나온다(v21.07.01 실제 사례).
    for w in win.findChildren(QLabel):
        try:
            t = w.text()
        except Exception:
            continue
        if '&&' in t:
            issues.append(('QLabel &&', f"'{t[:40]}' — QLabel은 &를 이스케이프하지 않는다"))

    # ② 텍스트 잘림 — sizeHint가 실제 폭·높이를 넘는 위젯
    for w in _visible_text_widgets(win):
        try:
            sh = w.sizeHint()
            if w.property('wordWrap') or getattr(w, 'wordWrap', lambda: False)():
                continue          # 줄바꿈 위젯은 폭 초과가 정상이다
            if sh.width() > w.width() + _SLACK_W:
                issues.append(('가로 잘림', f"'{w.text()[:32]}' 폭 {w.width()}<{sh.width()}"))
            elif sh.height() > w.height() + _SLACK_H:
                issues.append(('세로 잘림', f"'{w.text()[:32]}' 높이 {w.height()}<{sh.height()}"))
        except Exception:
            continue

    # ③ 너무 작은 글씨 — 판단 근거가 가장 작은 글씨로 적혀 있던 문제(v21.07.10)
    for w in _visible_text_widgets(win):
        try:
            m = re.search(r'font-size:\s*(\d+)px', w.styleSheet() or '')
            if m and int(m.group(1)) < 12:
                issues.append(('작은 글씨', f"'{w.text()[:28]}' {m.group(1)}px < 12px"))
        except Exception:
            continue
    return issues


def main() -> int:
    app = QApplication(sys.argv)
    import app_main
    win = app_main.MainWindow(app_main.APP_VERSION)
    win.setAttribute(Qt.WidgetAttribute.WA_DontShowOnScreen, True)
    win.resize(1800, 1060)
    win.show()
    app.processEvents()

    issues = audit(win)
    n_chk = len(win.findChildren(QCheckBox))
    n_exp = sum(1 for c in win.findChildren(QCheckBox) if '(실험적)' in c.text())
    print(f"[ui-shot] 체크박스 {n_chk}개 · '(실험적)' {n_exp}개 "
          f"(정적 정규식은 여러 줄 문자열을 놓치므로 이 실행 기반 카운트가 정본)")

    if '--shot' in sys.argv:
        out = sys.argv[sys.argv.index('--shot') + 1]
        win.grab().save(f"{out}/ui_main.png")
        print(f"[ui-shot] 캡처 저장 → {out}/ui_main.png")

    if issues:
        print(f"[ui-shot] ⚠ 발견 {len(issues)}건")
        for cat, desc in issues[:40]:
            print(f"    [{cat}] {desc}")
        return 1
    print("[ui-shot] ✅ PASS — QLabel && 0 · 잘림 0 · 12px 미만 글씨 0")
    return 0


if __name__ == '__main__':
    sys.exit(main())
