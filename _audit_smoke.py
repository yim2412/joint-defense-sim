# -*- coding: utf-8 -*-
"""
_audit_smoke.py — 종합 감사 ⑤ GUI 자동화 스모크 (빌드 제외 도구)

exe를 실제로 띄워 '시뮬레이션 실행' 버튼을 클릭하고 결과가 뜨는지 확인한다.
엔진 직접 호출 우회 금지([[feedback-smoke-run]]) — GUI 워커 경로(step_cb·시그널)를
실제로 태운다. 자동화 실패 시 exit 2(BLOCKED)로 보고하고 그 영역만 막힌다.

종료는 close()(=CloseMainWindow)로 정상 종료 — Stop-Process -Force 금지
(워커 풀 예열 중 강제종료하면 멀티프로세싱 자식 WinError 87 에러창).
"""
import sys, time, os

EXE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   'dist', '합동_통합방어_시뮬레이터', '합동_통합방어_시뮬레이터.exe')

def log(m): print(f"[smoke] {m}", flush=True)

def main():
    if not os.path.exists(EXE):
        log(f"exe 없음: {EXE}"); return 2
    try:
        from pywinauto.application import Application
        from pywinauto import timings
    except Exception as e:
        log(f"pywinauto import 실패: {e}"); return 2

    app = None
    try:
        log("exe 시작…")
        app = Application(backend='uia').start(f'"{EXE}"', timeout=20)
        # 메인 윈도우 대기 (워커 풀 예열로 첫 표시까지 시간 걸림)
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
        win.set_focus()
        time.sleep(2)

        # 1) 홈 화면 '시뮬레이터 시작' 클릭 → MainWindow 진입
        home_btn = None
        for b in win.descendants(control_type='Button'):
            try: t = b.window_text() or ''
            except Exception: t = ''
            if '시뮬레이터 시작' in t:
                home_btn = b; break
        if home_btn is not None:
            log("홈 '시뮬레이터 시작' 클릭 → 앱 진입")
            home_btn.click_input()
            time.sleep(4)
        else:
            log("홈 시작 버튼 없음 — 이미 메인일 수 있음, 계속 진행")

        # 2) MainWindow(버전 포함 타이틀)에서 '시뮬레이션 실행' 탐색
        main = win
        try:
            mw = app.window(title_re='.*합동 통합방어 시뮬레이터\\s+v.*')
            if mw.exists():
                main = mw; main.set_focus(); log("MainWindow(버전 타이틀) 포착")
        except Exception:
            pass
        time.sleep(2)

        target = None
        for b in main.descendants(control_type='Button'):
            try:
                t = (b.window_text() or '')
            except Exception:
                t = ''
            if '시뮬레이션 실행' in t:
                target = b; break
        win = main  # 이후 결과 폴링은 MainWindow 기준
        if target is None:
            log("'시뮬레이션 실행' 버튼 못 찾음 — 버튼 목록:")
            for b in win.descendants(control_type='Button')[:25]:
                try: log("   btn: " + repr(b.window_text()))
                except Exception: pass
            return 2
        log("버튼 클릭")
        target.click_input()

        # 결과 대기 — 결과 탭/배너의 텍스트 출현 폴링(요격률·작전 결과·전멸 등)
        markers = ['요격률', '작전 결과', '승률', '임무 점수', '교전', '결과', '전멸', '생존']
        found = None
        for i in range(90):  # 최대 90s (단발 시뮬 + 렌더)
            time.sleep(1)
            try:
                texts = []
                for c in win.descendants():
                    try:
                        wt = c.window_text()
                        if wt: texts.append(wt)
                    except Exception:
                        pass
                blob = ' '.join(texts)
                hit = [m for m in markers if m in blob]
                # 시작 직후에도 일부 마커는 늘 존재 → 시뮬 후 새로 뜨는 '결과/요격률/승률' 위주 판정
                strong = [m for m in ('요격률', '작전 결과', '승률', '임무 점수') if m in blob]
                if strong:
                    found = strong; break
            except Exception:
                pass
            if i in (20, 40, 60, 80):
                log(f"  …대기 {i+1}s")
        if found:
            log(f"결과 표시 확인: {found}")
            rc = 0
        else:
            log("결과 마커 미검출 (90s) — 시뮬 미완 또는 결과 미표시")
            rc = 1
        return rc
    except Exception as e:
        import traceback; log("예외:"); traceback.print_exc(); return 2
    finally:
        try:
            if app is not None:
                # 정상 종료 (CloseMainWindow) — 강제종료 금지
                app.kill(soft=True)
                log("정상 종료 요청(soft)")
        except Exception as e:
            log(f"종료 처리 예외: {e}")

if __name__ == '__main__':
    code = main()
    log(f"RESULT_CODE={code}  (0=PASS,1=결과미검출,2=BLOCKED)")
    sys.exit(code)
