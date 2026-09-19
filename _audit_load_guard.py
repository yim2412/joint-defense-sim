# -*- coding: utf-8 -*-
"""
_audit_load_guard.py — 감사·스모크가 사용자의 다른 작업(게임 등)에 양보하게 하는 가드.

**왜 있나**: 캠페인 스모크는 워커 22개·CPU 합산 700%·RAM 3.7GB를 쓴다(2026-09-19 실측).
우선순위는 이미 BELOW_NORMAL로 낮추고 있지만(`app_utils._set_pool_priority`), 우선순위만
낮추면 코어는 여전히 전부 점유한다 — 게임처럼 지연에 민감한 작업은 캐시·메모리 대역폭
경쟁만으로도 프레임이 흔들린다. 그래서 **쓸 코어 수 자체를 줄인다.**

**무엇을 보고 판단하나**: 내 작업 트리 **밖**에서 CPU를 쓰는 프로세스들의 합산 점유율.
게임 이름을 알 필요가 없다 — '내가 아닌 누군가가 CPU를 많이 쓰고 있다'만 알면 된다.

사용:
    from _audit_load_guard import apply_guard
    apply_guard(log)            # 스크립트 진입부에서 1회

    from _audit_load_guard import external_load
    busy, top, pct = external_load()   # 판단만 하고 직접 처리
"""
import os
import sys

try:
    import psutil
except ImportError:                                  # psutil 없으면 가드는 조용히 비활성
    psutil = None

# 외부 합산 CPU가 이 값을 넘으면 '사용자가 무언가 돌리는 중'으로 본다(전체 대비 %).
# **오판 비용이 비대칭이라 일부러 낮게 잡는다.** 양보를 안 해야 하는데 했으면 스모크가
# 조금 느려질 뿐이지만(31s→40s 수준), 해야 하는데 안 하면 사용자의 게임이 끊긴다.
# 실측(2026-09-19): 같은 게임이 33.7% → 21.9%로 오르내렸다 — 로딩·메뉴 대기 구간에서
# 낮게 찍히고, 그때 IDLE로 보고 무겁게 돌리면 정작 게임이 바빠질 때 정면 충돌한다.
BUSY_PCT = 12.0
# 양보 시 남겨 둘 코어 비율(내 작업이 쓸 몫). 0.5 = 절반만 쓴다.
YIELD_RATIO = 0.5
# 양보해도 이 수보다 적게는 안 내려간다(너무 줄이면 스모크가 상한 시간에 걸린다).
MIN_CORES = 2
_SAMPLE_S = 1.0


def _my_tree_pids() -> set:
    """내 프로세스와 그 자손 — '외부'를 가르는 기준."""
    if psutil is None:
        return set()
    me = psutil.Process(os.getpid())
    pids = {me.pid}
    try:
        pids |= {c.pid for c in me.children(recursive=True)}
    except Exception:
        pass
    return pids


def external_load(sample_s: float = _SAMPLE_S) -> tuple:
    """(busy, 최대 소비 프로세스명, 외부 합산 CPU%) — 전체 코어 대비 백분율.

    JDS_YIELD=1이면 재지 않고 무조건 BUSY로 본다(게임을 켜 두고 작업할 때 쓰는 스위치).
    JDS_YIELD=0이면 무조건 IDLE(양보 금지 — 빨리 끝내야 할 때).
    """
    forced = os.environ.get('JDS_YIELD')
    if forced == '1':
        return (True, '(JDS_YIELD=1 강제)', 100.0)
    if forced == '0':
        return (False, '(JDS_YIELD=0 강제)', 0.0)
    if psutil is None:
        return (False, None, 0.0)
    mine = _my_tree_pids()
    procs = []
    for p in psutil.process_iter(['pid', 'name']):
        if p.info['pid'] in mine or p.info['pid'] == 0:
            continue
        try:
            p.cpu_percent(None)                       # 1차 호출 = 기준점
            procs.append(p)
        except Exception:
            pass
    import time
    time.sleep(sample_s)
    ncpu = psutil.cpu_count() or 1
    total, top_name, top_pct = 0.0, None, 0.0
    for p in procs:
        try:
            pct = p.cpu_percent(None) / ncpu          # 코어 합산 → 전체 대비로 환산
        except Exception:
            continue
        if pct <= 0:
            continue
        total += pct
        if pct > top_pct:
            top_pct, top_name = pct, p.info.get('name')
    return (total >= BUSY_PCT, top_name, total)


def apply_guard(log=print, sample_s: float = _SAMPLE_S) -> dict:
    """외부 부하를 재고, 무거우면 이 프로세스 트리를 저우선순위 + 코어 절반으로 묶는다.

    반환 dict의 'cores'는 이후 워커 수를 정할 때 쓰라고 함께 돌려준다.
    자식(스모크가 띄우는 exe)에게는 환경변수 JDS_MAX_WORKERS로 전달된다.
    """
    ncpu = (psutil.cpu_count() if psutil else os.cpu_count()) or 1
    if psutil is None:
        log("[guard] psutil 없음 — 양보 가드 비활성")
        return {'busy': False, 'cores': ncpu, 'external_pct': 0.0}

    busy, top, pct = external_load(sample_s)
    if not busy:
        log(f"[guard] 외부 부하 {pct:.0f}% (기준 {BUSY_PCT:.0f}%) — 양보 없이 전체 {ncpu}코어 사용")
        return {'busy': False, 'cores': ncpu, 'external_pct': pct}

    cores = max(MIN_CORES, int(ncpu * YIELD_RATIO))
    log(f"[guard] 외부 부하 {pct:.0f}% (최대 소비: {top}) — 양보: {ncpu}→{cores}코어 · 저우선순위")
    me = psutil.Process(os.getpid())
    targets = [me]
    try:
        targets += me.children(recursive=True)
    except Exception:
        pass
    low = getattr(psutil, 'BELOW_NORMAL_PRIORITY_CLASS', 5)
    # 마지막 코어들을 비워 준다 — 게임이 쓰던 코어를 그대로 두는 편이 캐시에 유리하다.
    affinity = list(range(cores))
    for p in targets:
        try:
            p.nice(low)
        except Exception:
            pass
        try:
            p.cpu_affinity(affinity)
        except Exception:
            pass
    # 자식 프로세스(스모크가 띄우는 exe)가 워커 수를 줄이도록 전달
    os.environ['JDS_MAX_WORKERS'] = str(cores)
    return {'busy': True, 'cores': cores, 'external_pct': pct, 'top': top}


if __name__ == '__main__':
    busy, top, pct = external_load(float(sys.argv[1]) if len(sys.argv) > 1 else _SAMPLE_S)
    ncpu = (psutil.cpu_count() if psutil else os.cpu_count()) or 1
    print(f"외부 합산 CPU {pct:.1f}%  (코어 {ncpu}개 기준)")
    print(f"최대 소비 프로세스: {top}")
    print(f"판정: {'BUSY — 양보 필요' if busy else 'IDLE — 양보 불필요'} (기준 {BUSY_PCT}%)")
