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

# 감사 도구 자체 결함 방지: cp949 콘솔에서 ⚠✅🔴 등 유니코드 로그가 UnicodeEncodeError로
# 크래시하면 return 경로가 막혀 판정이 BLOCKED로 오염된다 → stdout을 utf-8로 고정.
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

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

        # 캠페인 + 전장의 안개(v18.4) 토글 — '안개'는 캠페인 하위 옵션이라 함께 켜서
        # 안개 ON GUI 경로(belief 배정·배너 표시)까지 실제로 태운다.
        chk = fog = air = sead = strike = precise = army = coastal = None
        for c in main_w.descendants(control_type='CheckBox'):
            t = _txt(c)
            if '안개' in t:            fog = c
            elif '공군' in t:           air = c      # v19.1 공군 작전급(제공권)
            elif 'SEAD' in t:           sead = c     # v19.3 방공망 제압
            elif '전략' in t:           strike = c   # v19.4 전략 폭격 & 기지 타격
            elif '정밀' in t:           precise = c  # A1 정밀 교전(실측 손실·요격)
            elif '지상 작전급' in t:    army = c     # v20.2b 지상 층(연안 방공망)
            elif '연안 방공 포대' in t: coastal = c  # v20.2b 포대 실제 배치
            elif '캠페인' in t:         chk = c
        if chk is None:
            log("캠페인 체크박스 미포착(BLOCKED)"); return 2
        log(f"캠페인 체크박스: {_txt(chk)!r} → 체크"); _act(chk); time.sleep(1)
        if fog is not None:
            log(f"안개 체크박스: {_txt(fog)!r} → 체크"); _act(fog); time.sleep(1)
        else:
            log("⚠ 안개 체크박스 미포착 — 캠페인만 검증(v18.4 GUI 경로 미확인)")
        # v19.1: 공군 작전급 토글 — 캠페인 하위 옵션이라 함께 켜서 제공권 산출·배너 GUI 경로를 태운다.
        if air is not None:
            log(f"공군 체크박스: {_txt(air)!r} → 체크"); _act(air); time.sleep(1)
        else:
            log("⚠ 공군 체크박스 미포착 — 캠페인만 검증(v19.1 GUI 경로 미확인)")
        # v19.3: 방공망 제압(SEAD) 토글 — 공군 하위 옵션이라 함께 켜서 방공망·SEAD GUI 경로를 태운다.
        if sead is not None:
            log(f"SEAD 체크박스: {_txt(sead)!r} → 체크"); _act(sead); time.sleep(1)
        else:
            log("⚠ SEAD 체크박스 미포착 — 공군만 검증(v19.3 GUI 경로 미확인)")
        # v19.4: 전략 폭격 토글 — 공군 하위 옵션이라 함께 켜서 적 기지·전략폭격 GUI 경로를 태운다.
        if strike is not None:
            log(f"전략폭격 체크박스: {_txt(strike)!r} → 체크"); _act(strike); time.sleep(1)
        else:
            log("⚠ 전략폭격 체크박스 미포착 — 공군만 검증(v19.4 GUI 경로 미확인)")
        # A1: 정밀 교전 토글 — 캠페인 교전을 실제 전술 단발로 해결하는 GUI 경로를 태운다
        # (헤드리스가 못 잡는 exe 전용 버그 방지). 정밀은 내부적으로 공군 플래그를 제거하나
        # 공군 층 tick은 별개라 제공권 배너는 그대로 떠야 한다.
        if precise is not None:
            log(f"정밀교전 체크박스: {_txt(precise)!r} → 체크"); _act(precise); time.sleep(1)
        else:
            log("⚠ 정밀교전 체크박스 미포착 — 대리모델만 검증(A1 GUI 경로 미확인)")
        # v20.2b: 지상 작전급(연안 방공망) — 캠페인 하위 옵션. 포대 배치까지 함께 켜서
        # ASBM 정밀 라우팅·4계층 자산 주입·재고 차감의 exe 경로를 실제로 태운다.
        if army is not None:
            log(f"지상작전급 체크박스: {_txt(army)!r} → 체크"); _act(army); time.sleep(1)
        else:
            log("⚠ 지상작전급 체크박스 미포착 — v20.2b GUI 경로 미확인")
        if coastal is not None:
            log(f"연안포대 체크박스: {_txt(coastal)!r} → 체크"); _act(coastal); time.sleep(1)
        else:
            log("⚠ 연안포대 체크박스 미포착 — v20.2b GUI 경로 미확인")
        try:
            _st = f"캠페인={chk.get_toggle_state()}"
            if fog is not None: _st += f" 안개={fog.get_toggle_state()}"
            if air is not None: _st += f" 공군={air.get_toggle_state()}"
            if sead is not None: _st += f" SEAD={sead.get_toggle_state()}"
            if strike is not None: _st += f" 전략폭격={strike.get_toggle_state()}"
            if precise is not None: _st += f" 정밀교전={precise.get_toggle_state()}"
            if army is not None: _st += f" 지상작전급={army.get_toggle_state()}"
            if coastal is not None: _st += f" 연안포대={coastal.get_toggle_state()}"
            log(f"   토글 상태: {_st} (1=ON)")
        except Exception as e:
            log(f"   토글 상태 확인 실패: {e}")

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
                if '평균 통제도' in blob or '캠페인:' in blob:
                    if '⚠ 예측모델 미적용' in blob:
                        log("🔴 캠페인 결과는 떴으나 예측모델 미적용(폴백) — exe 모델 로드 실패"); return 1
                    if fog is not None and '안개' not in blob:
                        frag = [t for t in (_txt(c) for c in main_w.descendants())
                                if any(k in t for k in ('수리', '재배정', '탄약', '교통로'))]
                        log(f"🔴 안개 ON인데 배너에 안개 상태 미표시 — 배너 조각: {frag[:4]}"); return 1
                    # v19.1: 공군 ON이면 제공권 배너·상태줄이 떠야 한다(GUI 경로 검증)
                    if air is not None and '제공권' not in blob:
                        frag = [t for t in (_txt(c) for c in main_w.descendants())
                                if any(k in t for k in ('통제도', '교통로', '전역', '캠페인'))]
                        log(f"🔴 공군 ON인데 배너에 제공권 미표시 — 배너 조각: {frag[:4]}"); return 1
                    # v19.3: SEAD ON이면 방공망 제압 상태가 배너에 떠야 한다
                    if sead is not None and '방공망' not in blob:
                        frag = [t for t in (_txt(c) for c in main_w.descendants())
                                if any(k in t for k in ('제공권', '통제도', '전역'))]
                        log(f"🔴 SEAD ON인데 배너에 방공망 미표시 — 배너 조각: {frag[:4]}"); return 1
                    # v19.4: 전략폭격 ON이면 적 기지 손상 상태가 배너에 떠야 한다(폭격기 없어도 0%로 표시)
                    if strike is not None and '기지' not in blob:
                        frag = [t for t in (_txt(c) for c in main_w.descendants())
                                if any(k in t for k in ('제공권', '방공망', '전역'))]
                        log(f"🔴 전략폭격 ON인데 배너에 적 기지 미표시 — 배너 조각: {frag[:4]}"); return 1
                    _fogmsg = " + 🌫 안개 배너 확인" if fog is not None else ""
                    _airmsg = " + ✈ 제공권 배너 확인" if air is not None else ""
                    _seadmsg = " + 🎯 방공망 배너 확인" if sead is not None else ""
                    _strmsg = " + 💥 적 기지 배너 확인" if strike is not None else ""
                    # v19.5: CAS는 조건부(통제 붕괴 시 요청 발동) — 필수 아님. 발현되면 배너
                    # 형식만 확인, 미발현은 정상(기본 시나리오에서 통제 유지 시 요청 0).
                    _casmsg = " + 🛩 근접지원 배너 확인(발현)" if '근접지원' in blob else ""
                    # 사각⑤: 정밀교전 ON이면 캠페인 MC(반복 분석) 분포 배너가 실제로 떠야 한다.
                    # 'campaign MC (N회)'는 monte_carlo_campaign이 끝까지 실행돼야만 렌더되므로,
                    # 이 텍스트 존재 = 캠페인 MC 병렬 경로가 frozen exe에서 end-to-end 실행됐다는
                    # 증거(정밀 ON은 임계 8, camp_n≥10이라 병렬). freeze_support 미비 시 여기서 실패.
                    _precmsg = ""
                    if precise is not None:
                        if '캠페인 MC' not in blob:
                            frag = [t for t in (_txt(c) for c in main_w.descendants())
                                    if any(k in t for k in ('통제도', '승', '전역', 'MC'))]
                            log(f"🔴 정밀교전 ON인데 캠페인 MC 분포 배너 미표시 — MC 미실행/폴백? 조각: {frag[:4]}"); return 1
                        import re as _re
                        # UIA 텍스트 조각화·공백 변형에 견디게 유연 매칭('MC ... N회')
                        _m = _re.search(r'MC\D*(\d+)\s*회', blob)
                        _n = _m.group(1) if _m else '?'
                        _precmsg = f" + 🎯 정밀교전 ON·캠페인 MC 병렬 {_n}회 실행 확인(exe end-to-end)"
                    log(f"✅ 캠페인 결과 정상 표시(예측모델 적용){_fogmsg}{_airmsg}{_seadmsg}{_strmsg}{_casmsg}{_precmsg}"); return 0
            except Exception: pass
            if i in (15, 30): log(f"  …대기 {i+1}s")
        # 진단: UIA가 실제로 보는 텍스트에서 캠페인/상태 관련 조각 덤프
        try:
            blob = ' | '.join(_txt(c) for c in main_w.descendants() if _txt(c))
            hits = [t for t in blob.split(' | ') if any(k in t for k in ('캠페인', '통제', '완료', '전역', 'h/'))]
            log(f"⚠ 캠페인 결과 마커 미검출(40s) — UIA 관련 텍스트: {hits[:8]}")
        except Exception as e:
            log(f"⚠ 캠페인 결과 마커 미검출(40s) — 덤프 실패: {e}")
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
    log(f"RESULT_CODE={code}  (0=PASS,1=결과미검출/폴백,2=BLOCKED)")
    sys.exit(code)
