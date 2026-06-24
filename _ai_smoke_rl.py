# -*- coding: utf-8 -*-
"""
_ai_smoke_rl.py — ④ RL 정책 exe 스모크 (빌드 제외 도구)

_audit_gui_smoke.py 기반 + '지속 전장 모드' & 'AI 전술 (학습된 정책)' 체크박스를 켠 뒤
단일 시뮬을 실행해 작전 결과(승/패·임무점수)가 뜨는지 확인한다. GUI 워커 경로를
실제로 태운다(엔진 직접호출 우회 금지 [[feedback-smoke-run]]). 실패 시 exit 2(BLOCKED).
"""
import sys, time, os

EXE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   'dist', '합동_통합방어_시뮬레이터', '합동_통합방어_시뮬레이터.exe')

def log(m): print(f"[smoke-rl] {m}", flush=True)

def _check(win, keyword):
    """텍스트에 keyword가 든 CheckBox를 찾아 체크(이미 체크면 그대로). 성공 시 True."""
    for c in win.descendants(control_type='CheckBox'):
        try:
            t = c.window_text() or ''
        except Exception:
            t = ''
        if keyword in t:
            try:
                state = c.get_toggle_state()  # 0=off 1=on 2=indeterminate
            except Exception:
                state = 0
            if state != 1:
                c.click_input()
                log(f"체크박스 ON: {t!r}")
            else:
                log(f"체크박스 이미 ON: {t!r}")
            return True
    return False

def main():
    if not os.path.exists(EXE):
        log(f"exe 없음: {EXE}"); return 2
    try:
        from pywinauto.application import Application
    except Exception as e:
        log(f"pywinauto import 실패: {e}"); return 2

    app = None
    try:
        log("exe 시작…")
        app = Application(backend='uia').start(f'"{EXE}"', timeout=20)
        win = None
        for _ in range(40):
            try:
                w = app.window(title_re='.*합동 통합방어 시뮬레이터.*')
                if w.exists() and w.is_visible():
                    win = w; break
            except Exception:
                pass
            time.sleep(1)
        if win is None:
            log("메인 윈도우 미표시 (40s)"); return 2
        log("홈 윈도우 표시됨")
        win.set_focus(); time.sleep(2)

        # 홈 '시뮬레이터 시작' → 앱 진입
        for b in win.descendants(control_type='Button'):
            try: t = b.window_text() or ''
            except Exception: t = ''
            if '시뮬레이터 시작' in t:
                log("홈 '시뮬레이터 시작' 클릭"); b.click_input(); time.sleep(4); break

        main = win
        try:
            mw = app.window(title_re='.*합동 통합방어 시뮬레이터\\s+v.*')
            if mw.exists():
                main = mw; main.set_focus(); log("MainWindow 포착")
        except Exception:
            pass
        time.sleep(2)

        # 신규 토글 2종 ON — 지속 전장 모드 + AI 전술
        if not _check(main, '지속 전장 모드'):
            log("'지속 전장 모드' 체크박스 못 찾음"); return 2
        if not _check(main, 'AI 전술'):
            log("'AI 전술' 체크박스 못 찾음 — 빌드에 신규 토글 누락 의심"); return 2
        time.sleep(1)

        # 시뮬레이션 실행
        target = None
        for b in main.descendants(control_type='Button'):
            try: t = b.window_text() or ''
            except Exception: t = ''
            if '시뮬레이션 실행' in t:
                target = b; break
        if target is None:
            log("'시뮬레이션 실행' 버튼 못 찾음"); return 2
        log("시뮬레이션 실행 클릭(전장+AI 전술)")
        target.click_input()

        # 전장 단일 시뮬은 단발보다 느림 → 최대 200s 폴링
        strong_markers = ('작전 결과', '승률', '임무 점수', '임무점수', '요격률')
        found = None
        for i in range(200):
            time.sleep(1)
            try:
                texts = []
                for c in main.descendants():
                    try:
                        wt = c.window_text()
                        if wt: texts.append(wt)
                    except Exception:
                        pass
                blob = ' '.join(texts)
                hit = [m for m in strong_markers if m in blob]
                if hit:
                    found = hit; break
            except Exception:
                pass
            if i in (30, 60, 90, 120, 160):
                log(f"  …대기 {i+1}s")
        if found:
            log(f"결과 표시 확인: {found}")
            return 0
        log("결과 마커 미검출 (200s)")
        return 1
    except Exception:
        import traceback; log("예외:"); traceback.print_exc(); return 2
    finally:
        try:
            if app is not None:
                app.kill(soft=True); log("정상 종료 요청(soft)")
        except Exception as e:
            log(f"종료 처리 예외: {e}")

if __name__ == '__main__':
    code = main()
    log(f"RESULT_CODE={code}  (0=PASS,1=결과미검출,2=BLOCKED)")
    sys.exit(code)
