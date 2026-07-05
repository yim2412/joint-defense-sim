# -*- coding: utf-8 -*-
"""
_audit_campaign_smoke.py — 작전급 캠페인 모드 GUI 스모크 (빌드 제외 감사 도구)

exe를 띄워 '작전급 캠페인 모드' 토글을 켜고 시뮬을 실행해 캠페인 결과 배너가
정상 표시되는지 확인한다. 헤드리스 회귀가 못 잡는 GUI/exe 전용 버그를 발현시킨다:
  ▸step_cb 시그널 타입 오류(v17.01.01에서 발견) ▸예측모델 상대경로 폴백(v17.01.02)
_audit_gui_smoke.py(단발)와 짝 — 캠페인은 독립 exe 세션으로 검사(화면 상태 오염 회피).

조작은 invoke/toggle 우선(커서 이동 없음) → 전체화면 게임이 포그라운드여도 동작한다.
엔진 직접호출 우회 금지([[feedback-smoke-run]]) — GUI 워커 경로를 실제로 태운다.
종료는 app.kill(soft=True)=CloseMainWindow 정상 종료(강제종료 금지).
"""
import sys, time, os

EXE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   'dist', '합동_통합방어_시뮬레이터', '합동_통합방어_시뮬레이터.exe')

def log(m): print(f"[campaign-smoke] {m}", flush=True)

def _txt(c):
    try: return c.window_text() or ''
    except Exception: return ''

def _act(w):
    """커서 이동 없는 조작(invoke/toggle) 우선 — 전체화면 게임 포그라운드에도 동작."""
    for m in ('invoke', 'toggle'):
        try:
            getattr(w, m)(); return True
        except Exception:
            pass
    try:
        w.click_input(); return True
    except Exception:
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
                if w.exists() and w.is_visible(): win = w; break
            except Exception: pass
            time.sleep(1)
        if win is None:
            log("메인 윈도우 미표시"); return 2
        log("홈 표시됨"); win.set_focus(); time.sleep(2)

        # 홈 → 앱 진입
        for b in win.descendants(control_type='Button'):
            if '시뮬레이터 시작' in _txt(b):
                log("홈 시작(invoke)"); _act(b); time.sleep(4); break
        main_w = win
        try:
            mw = app.window(title_re='.*합동 통합방어 시뮬레이터\\s+v.*')
            if mw.exists(): main_w = mw; main_w.set_focus()
        except Exception: pass
        time.sleep(2)

        # 캠페인 토글
        chk = None
        for c in main_w.descendants(control_type='CheckBox'):
            if '캠페인' in _txt(c): chk = c; break
        if chk is None:
            log("캠페인 체크박스 미포착(BLOCKED)"); return 2
        log(f"캠페인 체크박스: {_txt(chk)!r} → 체크"); _act(chk); time.sleep(1)

        # 시뮬 실행
        target = None
        for b in main_w.descendants(control_type='Button'):
            if '시뮬레이션 실행' in _txt(b): target = b; break
        if target is None:
            log("실행 버튼 미포착(BLOCKED)"); return 2
        log("시뮬레이션 실행(invoke)"); _act(target)

        # 결과/에러 대기
        for i in range(40):
            time.sleep(1)
            try:
                for w in app.windows():
                    wt = _txt(w)
                    if wt and any(k in wt for k in ('오류', 'Error', 'Exception', 'unexpected type')):
                        log(f"🔴 에러창 감지: {wt!r}"); return 1
                blob = ' '.join(_txt(c) for c in main_w.descendants() if _txt(c))
                if '교통로 통제' in blob or '캠페인:' in blob:
                    if '⚠ 예측모델 미적용' in blob:
                        log("🔴 캠페인 결과는 떴으나 예측모델 미적용(폴백) — exe 모델 로드 실패"); return 1
                    log("✅ 캠페인 결과 정상 표시(예측모델 적용)"); return 0
            except Exception: pass
            if i in (15, 30): log(f"  …대기 {i+1}s")
        log("⚠ 캠페인 결과 마커 미검출(40s)"); return 1
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
    log(f"RESULT_CODE={code}  (0=PASS,1=결과미검출/폴백,2=BLOCKED)")
    sys.exit(code)
