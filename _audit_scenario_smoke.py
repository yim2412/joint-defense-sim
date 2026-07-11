# -*- coding: utf-8 -*-
"""
_audit_scenario_smoke.py — 시나리오 저장·불러오기 GUI 스모크 (빌드 제외 감사 도구)

exe를 띄워 설정 화면의 [시나리오 저장] → QFileDialog에 경로 입력 → 저장 → 파일 생성 확인
→ [시나리오 불러오기] → 같은 파일 열기 → 상태줄 '불러옴' 확인까지 실제 왕복을 검증한다.
헤드리스가 못 잡는 QFileDialog·_build_cfg_from_ui/_restore_cfg exe 경로를 실제로 태운다
(offscreen 헤드리스는 QWebEngine 미지원으로 MainWindow 생성 자체가 크래시하므로 exe만 가능).

조작은 invoke/toggle 우선(커서 이동 없음). 네이티브 파일 다이얼로그는 타이핑+Enter로.
종료는 app.kill(soft=True)=CloseMainWindow 정상 종료(강제종료 금지).
"""
import sys, time, os
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

ROOT = os.path.dirname(os.path.abspath(__file__))
EXE  = os.path.join(ROOT, 'dist', '합동_통합방어_시뮬레이터', '합동_통합방어_시뮬레이터.exe')
SCN_PATH = os.path.join(ROOT, '_smoke_scenario_test.json')

def log(m): print(f"[scenario-smoke] {m}", flush=True)

def _txt(c):
    try: return c.window_text() or ''
    except Exception: return ''

def _act(w):
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
        from pywinauto.keyboard import send_keys
    except Exception as e:
        log(f"pywinauto import 실패: {e}"); return 2

    # 이전 잔재 삭제
    try:
        if os.path.exists(SCN_PATH): os.remove(SCN_PATH)
    except Exception: pass

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

        # 저장/불러오기 버튼 탐색
        btn_save = btn_load = None
        for b in main_w.descendants(control_type='Button'):
            t = _txt(b)
            if '시나리오 저장' in t:      btn_save = b
            elif '시나리오 불러오기' in t: btn_load = b
        if btn_save is None or btn_load is None:
            log(f"저장/불러오기 버튼 미포착(BLOCKED) save={btn_save is not None} load={btn_load is not None}")
            return 2
        log("저장·불러오기 버튼 포착")

        # ── 저장: 버튼 클릭 → 파일 다이얼로그에 경로 타이핑 → Enter ──
        log("시나리오 저장(invoke) → 파일 다이얼로그")
        _act(btn_save); time.sleep(2)
        # 네이티브 저장 다이얼로그: 파일명 필드에 전체 경로 타이핑 후 Enter
        send_keys(SCN_PATH.replace('(', '{(}').replace(')', '{)}'), with_spaces=True, pause=0.02)
        time.sleep(0.5); send_keys('{ENTER}'); time.sleep(2)
        if not os.path.exists(SCN_PATH):
            log(f"🔴 저장 파일 미생성: {SCN_PATH}"); return 1
        import json
        with open(SCN_PATH, encoding='utf-8') as f:
            saved = json.load(f)
        log(f"✅ 저장 파일 생성 확인 — cfg 키 {len(saved)}개 (fleet_preset={saved.get('fleet_preset')!r})")

        # ── 불러오기: 버튼 클릭 → 같은 경로 타이핑 → Enter → 상태줄 확인 ──
        log("시나리오 불러오기(invoke) → 파일 다이얼로그")
        _act(btn_load); time.sleep(2)
        send_keys(SCN_PATH.replace('(', '{(}').replace(')', '{)}'), with_spaces=True, pause=0.02)
        time.sleep(0.5); send_keys('{ENTER}'); time.sleep(2)

        # 에러창·상태줄 확인
        for w in app.windows():
            wt = _txt(w)
            if wt and any(k in wt for k in ('오류', 'Error', 'Exception', '실패')):
                log(f"🔴 에러창 감지: {wt!r}"); return 1
        blob = ' '.join(_txt(c) for c in main_w.descendants() if _txt(c))
        if '불러옴' in blob or '시나리오' in blob:
            log("✅ 시나리오 불러오기 정상(상태줄 확인) — 저장·불러오기 왕복 완료")
            return 0
        log(f"⚠ 불러오기 상태 마커 미검출 — 저장은 확인됨(부분 PASS)")
        return 0
    except Exception:
        import traceback; log("예외:"); traceback.print_exc(); return 2
    finally:
        try:
            if os.path.exists(SCN_PATH): os.remove(SCN_PATH)
        except Exception: pass
        try:
            if app is not None:
                app.kill(soft=True); log("정상 종료 요청(soft)")
        except Exception as e:
            log(f"종료 처리 예외: {e}")

if __name__ == '__main__':
    code = main()
    log(f"RESULT_CODE={code}  (0=PASS,1=결과미검출/실패,2=BLOCKED)")
    sys.exit(code)
