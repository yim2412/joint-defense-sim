# -*- coding: utf-8 -*-
"""
_audit_smoke_util.py — GUI 스모크 공통 유틸 (빌드 제외 도구)

**스모크 창은 보조 모니터에서만 띄운다**(사용자 규칙 2026-09-12).
감사 스모크가 주 모니터를 점유하면 그 동안 사용자가 아무것도 못 한다 —
무인 감사는 수 분~수십 분 걸리고 pywinauto가 `set_focus()`로 포그라운드를
계속 뺏는다. 보조 화면으로 밀어 두면 감사가 도는 동안 주 화면은 자유롭다.

좌표를 상수로 박지 않는다 — 모니터 구성(해상도·배치·개수)이 바뀌면
조용히 화면 밖으로 창을 던지게 된다. 매번 EnumDisplayMonitors로 실측한다.
"""
import ctypes
from ctypes import wintypes

_MONITORINFOF_PRIMARY = 1


class _MONITORINFO(ctypes.Structure):
    _fields_ = [('cbSize', wintypes.DWORD),
                ('rcMonitor', wintypes.RECT),
                ('rcWork', wintypes.RECT),
                ('dwFlags', wintypes.DWORD)]


def enum_monitors():
    """[(rcWork, is_primary), ...] — 작업 영역(작업표시줄 제외) 기준."""
    found = []
    proc_t = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_ulong, ctypes.c_ulong,
                                ctypes.POINTER(wintypes.RECT), ctypes.c_double)

    def _cb(hmon, hdc, lprect, data):
        mi = _MONITORINFO()
        mi.cbSize = ctypes.sizeof(_MONITORINFO)
        if ctypes.windll.user32.GetMonitorInfoW(hmon, ctypes.byref(mi)):
            found.append((mi.rcWork, bool(mi.dwFlags & _MONITORINFOF_PRIMARY)))
        return 1

    ctypes.windll.user32.EnumDisplayMonitors(0, 0, proc_t(_cb), 0)
    return found


def secondary_rect():
    """보조(비주) 모니터 작업영역 (left, top, width, height). 없으면 None."""
    for rc, is_primary in enum_monitors():
        if not is_primary:
            return (rc.left, rc.top, rc.right - rc.left, rc.bottom - rc.top)
    return None


def place_on_secondary(win, log=print, margin=40):
    """pywinauto 윈도우를 보조 모니터로 이동. 보조가 없으면 주 모니터 유지(스모크 계속).

    반환: 실제로 옮겼으면 True.
    """
    rc = secondary_rect()
    if rc is None:
        log("보조 모니터 없음 — 주 모니터에서 진행")
        return False
    left, top, w, h = rc
    try:
        # ⚠ `win.move_window()` 를 쓰지 말 것 — pywinauto **win32 backend 전용**이라
        #   UIA backend wrapper 에는 없다("Neither GUI element nor wrapper method
        #   'move_window' were found"). 스모크는 backend='uia' 로 돈다.
        #   UIA wrapper 도 `.handle`(HWND)은 주므로 Win32 SetWindowPos 를 직접 부른다.
        hwnd = win.handle
        if not hwnd:
            log("보조 모니터 이동 생략: HWND 없음")
            return False
        SWP_NOZORDER, SWP_NOACTIVATE, SWP_SHOWWINDOW = 0x0004, 0x0010, 0x0040
        ok = ctypes.windll.user32.SetWindowPos(
            int(hwnd), 0,
            left + margin // 2, top + margin // 2,
            max(800, w - margin), max(600, h - margin),
            SWP_NOZORDER | SWP_NOACTIVATE | SWP_SHOWWINDOW)
        if not ok:
            log(f"보조 모니터 이동 실패(무시하고 진행): SetWindowPos err="
                f"{ctypes.windll.kernel32.GetLastError()}")
            return False
        # 반환값만 믿지 않는다 — 실제 창 좌표를 되읽어 그 모니터 안에 있는지 확인.
        # (SetWindowPos 가 성공을 반환해도 DPI 스케일·최대화 상태에서 어긋날 수 있다)
        got = wintypes.RECT()
        ctypes.windll.user32.GetWindowRect(int(hwnd), ctypes.byref(got))
        inside = (left <= got.left < left + w) and (top - 50 <= got.top < top + h)
        log(f"창을 보조 모니터로 이동: 지시=({left},{top}) {w}x{h} · "
            f"실제=({got.left},{got.top}) · 모니터 내부={'예' if inside else '아니오'}")
        return bool(inside)
    except Exception as e:
        # 이동 실패가 스모크 판정을 오염시키면 안 된다 — 경고만 남기고 계속.
        log(f"보조 모니터 이동 실패(무시하고 진행): {e}")
        return False
