"""
app_utils — app_main 런처의 비-GUI 유틸 계층.

app_main.py(12,807줄)에서 분리. 이 모듈은 **PyQt6를 import하지 않는다** — GPU/CPU 계측,
프로세스 풀, Job Object, 리소스 경로, 로그·SQLite 기록만 담당한다. GUI를 안 물고 있어야
app_main → app_utils 단방향 의존이 유지되고 순환이 생기지 않는다.

⚠ `_GLOBAL_POOL`은 이 모듈이 재할당하는 전역이다. 다른 모듈에서 `from app_utils import
_GLOBAL_POOL` 하면 import 시점의 None이 복사돼 **예열된 풀을 영영 못 본다**(조용한 성능
저하). 반드시 `app_utils._GLOBAL_POOL`로 참조할 것. `_SYS_CACHE`·`_PERF_HISTORY`는
mutate만 하므로 이름 import로도 같은 객체를 공유한다.
"""

import sys, os, io, time, threading, json, multiprocessing, subprocess as _sp, traceback
from concurrent.futures import ProcessPoolExecutor, as_completed, wait as cf_wait, FIRST_COMPLETED
import psutil

# ── GPU / CPU 온도 헬퍼 ──────────────────────────────────────────────────────
_wmi_inst = None   # lazy-init

def _get_gpu_info() -> dict:
    """nvidia-smi로 GPU 정보 수집. 실패 시 빈 dict 반환."""
    try:
        out = _sp.check_output(
            ['nvidia-smi',
             '--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu',
             '--format=csv,noheader,nounits'],
            timeout=1, stderr=_sp.DEVNULL,
            creationflags=_sp.CREATE_NO_WINDOW)
        p = [x.strip() for x in out.decode().strip().split(',')]
        return {'util': int(p[0]), 'mem_used': int(p[1]),
                'mem_total': int(p[2]), 'temp': int(p[3])}
    except Exception:
        return {}

def _get_cpu_temp() -> float:
    """CPU 온도(°C). WMI 사용. 실패 시 -1 반환."""
    global _wmi_inst
    if _wmi_inst is None:
        try:
            import wmi
            _wmi_inst = wmi.WMI(namespace="root\\wmi")
        except Exception:
            _wmi_inst = False
    if not _wmi_inst:
        return -1.0
    try:
        zones = _wmi_inst.MSAcpi_ThermalZoneTemperature()
        if zones:
            return zones[0].CurrentTemperature / 10.0 - 273.15
    except Exception:
        _wmi_inst = None
    return -1.0

# ── 글로벌 프로세스 풀 (앱 시작 시 예열, 시뮬 내내 재사용) ──────────────────
_GLOBAL_POOL: 'ProcessPoolExecutor | None' = None
_PERF_HISTORY: list = []   # 최근 시뮬 성능 기록 (최대 10개)

# 시스템 모니터 캐시 — 백그라운드 워커가 채움, 메인 스레드는 읽기만
_SYS_CACHE: dict = {
    'cpu': 0.0, 'mem_pct': 0.0, 'mem_used': 0, 'mem_total': 1,
    'gpu': {}, 'cpu_temp': -1.0, 'cores': [], 'proc_ram': 0.0,
    'worker_stats': [], 'swap_used': 0, 'thread_cnt': 0,
}

def _init_global_pool():
    """앱 시작 시 백그라운드 스레드에서 호출 — 워커 프로세스 예열."""
    global _GLOBAL_POOL
    _warmup_task = lambda _: None  # BUG-3: anim_render 의존성 제거
    n = min(os.cpu_count() or 4, 8)
    _GLOBAL_POOL = ProcessPoolExecutor(max_workers=n)
    try:
        list(_GLOBAL_POOL.map(_warmup_task, range(n), timeout=60))
    except Exception:
        pass   # 예열 실패해도 풀 자체는 사용 가능
    _set_pool_priority(_GLOBAL_POOL)  # BUG-1: 워커 프로세스 BELOW_NORMAL

def _shutdown_global_pool():
    global _GLOBAL_POOL
    if _GLOBAL_POOL is None:
        return
    pool, _GLOBAL_POOL = _GLOBAL_POOL, None   # None 먼저 → 새 작업 제출 차단
    try:
        pool.shutdown(wait=False, cancel_futures=True)
    except Exception:
        try:
            pool.shutdown(wait=False)
        except Exception:
            pass
    # 풀 프로세스가 아직 살아 있으면 즉시 kill
    try:
        procs = getattr(pool, '_processes', {})
        pids = list(procs.keys()) if isinstance(procs, dict) else []
        for pid in pids:
            try:
                psutil.Process(pid).kill()
            except Exception:
                pass
    except Exception:
        pass

def _pool_map(fn, iterable):
    """글로벌 풀로 fn을 iterable에 병렬 적용 (순서 보존, 결과는 지연 yield).
    풀 없으면 직렬 map 폴백. 무거운 분석(스트레스·Sobol·최적조합·최소재고)의
    독립 시뮬을 8코어로 분산. 지연 반환이라 소비측에서 진행률을 점진 갱신 가능."""
    items = list(iterable)
    pool = _GLOBAL_POOL
    if pool is None or len(items) <= 1:
        return map(fn, items)
    try:
        n_workers = getattr(pool, '_max_workers', 4) or 4
        chunksize = max(1, len(items) // (n_workers * 4))
        return pool.map(fn, items, chunksize=chunksize)
    except Exception:
        return map(fn, items)

_JOB_HANDLE = None   # Windows Job Object 핸들 — 프로세스 수명 동안 열어둠


def _setup_job_object():
    """Windows Job Object에 현재 프로세스를 묶어, 메인이 어떤 식으로 종료되든
    (정상·크래시·강제종료) 자식 워커 프로세스를 OS가 자동으로 함께 종료시킨다.
    closeEvent/aboutToQuit 정리가 안 돌아도 고아 워커가 남지 않도록 OS 수준에서 보장."""
    global _JOB_HANDLE
    if sys.platform != 'win32':
        return
    try:
        import ctypes
        from ctypes import wintypes
        k32 = ctypes.WinDLL('kernel32', use_last_error=True)
        # 64비트 HANDLE이 기본 int(32비트)로 잘리지 않도록 모든 시그니처를 명시한다.
        k32.CreateJobObjectW.restype           = wintypes.HANDLE
        k32.CreateJobObjectW.argtypes          = [wintypes.LPVOID, wintypes.LPCWSTR]
        k32.GetCurrentProcess.restype          = wintypes.HANDLE
        k32.GetCurrentProcess.argtypes         = []
        k32.SetInformationJobObject.restype    = wintypes.BOOL
        k32.SetInformationJobObject.argtypes   = [wintypes.HANDLE, ctypes.c_int,
                                                  wintypes.LPVOID, wintypes.DWORD]
        k32.AssignProcessToJobObject.restype   = wintypes.BOOL
        k32.AssignProcessToJobObject.argtypes  = [wintypes.HANDLE, wintypes.HANDLE]
        job = k32.CreateJobObjectW(None, None)
        if not job:
            return

        JobObjectExtendedLimitInformation = 9
        JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x2000

        class _BASIC(ctypes.Structure):
            _fields_ = [('PerProcessUserTimeLimit', wintypes.LARGE_INTEGER),
                        ('PerJobUserTimeLimit',     wintypes.LARGE_INTEGER),
                        ('LimitFlags',              wintypes.DWORD),
                        ('MinimumWorkingSetSize',   ctypes.c_size_t),
                        ('MaximumWorkingSetSize',   ctypes.c_size_t),
                        ('ActiveProcessLimit',      wintypes.DWORD),
                        ('Affinity',                ctypes.POINTER(wintypes.ULONG)),
                        ('PriorityClass',           wintypes.DWORD),
                        ('SchedulingClass',         wintypes.DWORD)]

        class _IO(ctypes.Structure):
            _fields_ = [('ReadOperationCount',  ctypes.c_ulonglong),
                        ('WriteOperationCount', ctypes.c_ulonglong),
                        ('OtherOperationCount', ctypes.c_ulonglong),
                        ('ReadTransferCount',   ctypes.c_ulonglong),
                        ('WriteTransferCount',  ctypes.c_ulonglong),
                        ('OtherTransferCount',  ctypes.c_ulonglong)]

        class _EXT(ctypes.Structure):
            _fields_ = [('BasicLimitInformation', _BASIC),
                        ('IoInfo',                _IO),
                        ('ProcessMemoryLimit',    ctypes.c_size_t),
                        ('JobMemoryLimit',        ctypes.c_size_t),
                        ('PeakProcessMemoryUsed', ctypes.c_size_t),
                        ('PeakJobMemoryUsed',     ctypes.c_size_t)]

        info = _EXT()
        info.BasicLimitInformation.LimitFlags = JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not k32.SetInformationJobObject(job, JobObjectExtendedLimitInformation,
                                           ctypes.byref(info), ctypes.sizeof(info)):
            return
        if not k32.AssignProcessToJobObject(job, k32.GetCurrentProcess()):
            return
        # 핸들을 전역으로 보관해 프로세스 종료 전까지 열어둔다.
        # (핸들이 닫히면 KILL_ON_JOB_CLOSE가 발동되므로 GC로 닫히지 않게 유지)
        _JOB_HANDLE = job
    except Exception:
        pass


def _kill_child_processes():
    """현재 프로세스의 모든 자식(워커 풀·subprocess 등) 강제 종료 — 좀비 방지.
    어떤 창을 X로 닫든·앱이 어떻게 종료되든 자식이 안 남도록 모든 종료 경로에서 호출.
    (Job Object가 1차 보장, 이 함수는 종료 전 즉시 정리용 2차 안전망.)"""
    try:
        me = psutil.Process()
        children = me.children(recursive=True)
        for child in children:
            try:
                child.kill()
            except Exception:
                pass
        # kill 신호 후 잠깐 회수 (좀비 남지 않도록)
        psutil.wait_procs(children, timeout=1.5)
    except Exception:
        pass

def _set_pool_priority(pool):
    """워커 프로세스 우선순위를 BELOW_NORMAL로 낮춤 — 시뮬 중 UI·다른 앱 응답성 유지."""
    # Windows: BELOW_NORMAL_PRIORITY_CLASS / Unix: nice=5
    _nice = getattr(psutil, 'BELOW_NORMAL_PRIORITY_CLASS', 5)
    try:
        # _processes는 ProcessPoolExecutor 내부 속성 — 없으면 자식 프로세스로 폴백
        procs = getattr(pool, '_processes', None) or {}
        pids  = list(procs.keys()) if isinstance(procs, dict) else []
        if not pids:
            pids = [c.pid for c in psutil.Process().children()]
        for pid in pids:
            try:
                psutil.Process(pid).nice(_nice)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except Exception:
        pass

def _res(filename: str) -> str:
    """PyInstaller exe 및 일반 실행 모두에서 리소스 파일 경로 반환."""
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, filename)


def _token_path() -> str:
    """Cesium ion 토큰(개인키, 빌드 제외) — exe는 실행파일 옆, 개발은 스크립트 옆에서 읽음."""
    if getattr(sys, 'frozen', False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, 'cesium_token.txt')


def _load_surrogate() -> dict | None:
    """실행 전 '예상 전황' 룩업 테이블(forecast_surrogate.json) 로드.
    없거나 깨지면 None 반환 → 기능 자동 비활성(하위호환). 번들 리소스라 _res 경로."""
    try:
        with open(_res('forecast_surrogate.json'), encoding='utf-8') as f:
            data = json.load(f)
        if isinstance(data, dict) and isinstance(data.get('table'), dict):
            return data
    except Exception:
        pass
    return None


def _load_forecast_model() -> dict | None:
    """v15.2 대리모델(forecast_model.pkl) 로드 — 임의 날씨·미룩업 조합 즉시 추정용.
    없거나 joblib/sklearn 부재면 None → 룩업 폴백(하위호환). 번들 리소스라 _res 경로."""
    try:
        import joblib
        data = joblib.load(_res('forecast_model.pkl'))
        if isinstance(data, dict) and data.get('models'):
            return data
    except Exception:
        pass
    return None


# ════════════════════════════════════════════════════════════════════════════
#  쇼케이스 — 실험적 기능별 효과 시연 시나리오 + ON/OFF 비교 (near-term 사용성)
# ════════════════════════════════════════════════════════════════════════════
# 각 카드: 그 기능의 효과가 극명히 드러나는 사전 정의 시나리오. [시나리오 로드]로
# 설정에 한 번에 세팅하거나, [직접 비교 실행]으로 토글 OFF↔ON MC를 실측 대조한다.
# scenario dict는 _restore_cfg가 읽는 cfg 키를 그대로 사용(콤보·체크박스 세팅).
_SHOWCASE_WEATHER = '맑음 (주간)'

_SHOWCASES: list[dict] = [
    {
        'key':    'drone_swarm',
        'title':  '적 무인기 군집 (자폭 드론 포화)',
        'desc':   '무장 없는 자폭 드론이 다방위로 돌진 → 요격 채널·요격탄이 포화되며 '
                  '요격률이 급락하는 비대칭 소모전.',
        'toggle': 'enable_drone_swarm',
        'scenario': {
            'fleet_preset':      '이지스 기동전단',
            'enemy_fleet_mode':  'preset',
            'enemy_fleet_preset':'무인기 군집 포화',
            'weather':           _SHOWCASE_WEATHER,
            'enable_multibearing': True,   # 다방위 병용해야 360° 포화가 드러남
        },
        'expected': '요격률 38% → 27% (드론 군집 다방위 투입) · 요격 채널·요격탄 포화',
        'metrics':  ['intercept', 'hits', 'lost'],
    },
    {
        'key':    'unmanned_assets',
        'title':  '아군 무인 함정 (USV·UUV 전방 피켓·소해)',
        'desc':   'UUV가 기뢰를 사전 소해하고 USV가 전방 피켓으로 나서 유인함 대신 '
                  '위험을 흡수 → 유인함 손실·기뢰 접촉이 감소(인명 손실 0).',
        'toggle': 'enable_unmanned_assets',
        'scenario': {
            'fleet_preset':      '대잠전단',
            'enemy_fleet_mode':  'preset',
            'enemy_fleet_preset':'대잠 복합',
            'weather':           _SHOWCASE_WEATHER,
            'enable_mine_threat': True,    # 기뢰가 깔려야 UUV 소해가 binding
        },
        'expected': '기뢰 접촉 0.60 → 0.30 (UUV 사전 소해) · 무인정이 유인함 대신 위험 흡수(인명 0)',
        'metrics':  ['mine_struck', 'intercept', 'unmanned'],
    },
    {
        'key':    'dmo',
        'title':  '분산 해양 작전 (DMO)',
        'desc':   '함대를 광역 분산 배치 → 대량 포화 공격의 명중을 접근축으로 분산시켜 '
                  '요격 효율을 끌어올리는 양날의 검(소수 위협엔 역효과).',
        'toggle': 'enable_dmo',
        'scenario': {
            'fleet_preset':      '이지스 기동전단',
            'enemy_fleet_mode':  'preset',
            'enemy_fleet_preset':'전면전 포화',
            'weather':           _SHOWCASE_WEATHER,
        },
        'expected': '요격률 0.28 → 0.45 · 아군 피격 감소 (전면전 포화 기준)',
        'metrics':  ['intercept', 'hits', 'lost'],
    },
    {
        'key':    'coord_deception',
        'title':  '전자 좌표 기만 (ECM 종말 유도 교란)',
        'desc':   '아군 ECM이 적 대함미사일의 종말 유도에 가짜 좌표를 주입 → 명중점을 함정 '
                  '바깥으로 밀어내 피격과 함정 손실을 크게 줄인다.',
        'toggle': 'enable_coord_deception',
        'scenario': {
            'fleet_preset':      '이지스 기동전단',
            'enemy_fleet_mode':  'preset',
            'enemy_fleet_preset':'수상함 편대전',
            'weather':           _SHOWCASE_WEATHER,
        },
        'expected': '아군 피격 19.4 → 13.5 · 유인함 손실 4.15 → 1.20 (수상함 편대전 기준)',
        'metrics':  ['hits', 'lost', 'intercept'],
    },
]

# 비교 뷰 지표 정의: 키 → (표시명, 추출 lambda(mc_dict), 단위, 방향 '+'좋을수록↑ / '-'낮을수록↓)
_SHOWCASE_METRICS: dict = {
    'intercept': ('요격률',      lambda m: m.get('mean_intercept', 0.0) * 100,                     '%',  '+'),
    'hits':      ('아군 피격',   lambda m: float(np.mean(m['friendly_hits'])) if m.get('friendly_hits') else 0.0, '발', '-'),
    'lost':      ('유인함 손실', lambda m: float(np.mean(m['friendly_lost'])) if m.get('friendly_lost') else 0.0, '척', '-'),
    'unmanned':  ('무인정 손실', lambda m: m.get('mean_unmanned_lost', 0.0),                       '척', '~'),
    'mine_struck':('기뢰 접촉',  lambda m: m.get('mean_mines_struck', 0.0),                        '회', '-'),
    'mine':      ('기뢰 피해',   lambda m: m.get('mean_ships_lost_to_mine', 0.0),                  '척', '-'),
    'cost':      ('교전 비용',   lambda m: float(np.mean(m['total_costs']))/1e6 if m.get('total_costs') else 0.0, 'M$', '-'),
}


# ════════════════════════════════════════════════════════════════════════════
#  실행 로그 (sim_history.log 텍스트 + sim_history.json 구조화)
# ════════════════════════════════════════════════════════════════════════════
def _log_base() -> str:
    # v13.06.14: 실행 로그·크래시 로그·DB를 재빌드·재설치에도 보존되는 사용자
    # 영구 폴더(%LOCALAPPDATA%\AegisSim)에 저장. exe 폴더는 빌드 시 갈아엎혀 유실됨.
    try:
        root = os.environ.get('LOCALAPPDATA') or os.path.expanduser('~')
        base = os.path.join(root, 'AegisSim')
        os.makedirs(base, exist_ok=True)
        return base
    except Exception:
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
        return os.path.dirname(os.path.abspath(__file__))

def _log_path()  -> str: return os.path.join(_log_base(), 'sim_history.log')
def _json_log_path() -> str: return os.path.join(_log_base(), 'sim_history.json')
def _app_state_path() -> str: return os.path.join(_log_base(), 'app_state.json')


def _load_app_state() -> dict:
    try:
        with open(_app_state_path(), encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def _save_app_state(state: dict):
    try:
        with open(_app_state_path(), 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _write_log(line: str):
    try:
        with open(_log_path(), 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except Exception:
        pass


def _load_json_log() -> list:
    try:
        with open(_json_log_path(), encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


def _save_json_log(records: list):
    try:
        with open(_json_log_path(), 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _write_sim_log(cfg: dict, result: dict, mc: dict):
    from datetime import datetime
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    enemy_parts = [f"{e.get('preset','?')} ×{e.get('count',1)}"
                   for e in cfg.get('enemy_fleet', [])]
    enemy_str = ', '.join(enemy_parts) if enemy_parts else cfg.get('enemy_fleet_preset', '?')
    n = max(mc.get('n', 1), 1)
    avg_hits  = sum(mc.get('friendly_hits',  [])) / n
    avg_edest = sum(mc.get('enemy_destroyed', [])) / n

    # ── 텍스트 로그 ──────────────────────────────────────────────────────
    lines = [
        '=' * 80,
        f'[{now}]  시뮬레이션 완료',
        '-' * 80,
        f'  편대       : {cfg.get("fleet_preset", "?")}',
        f'  날씨       : {cfg.get("weather", "?")}',
        f'  MC 횟수    : {mc.get("n", 0)}회',
        f'  적군 구성  : {enemy_str}',
        '',
        f'  총 위협    : {result.get("total_threats", 0)}발/기',
    ]
    _outcome = result.get('outcome')
    if _outcome:   # 지속 전장 모드 — 승/패·임무 점수 중심, 요격률은 참고 지표
        _oc = {'win': '승리', 'loss': '패배', 'draw': '무승부'}.get(_outcome, _outcome)
        lines.append(f'  작전 결과  : {_oc}  (아군 임무 점수 {result.get("friendly_score", 0.0):.0%})')
        _wr = mc.get('win_rate')
        if _wr is not None:   # 전장 MC — 승률 분포
            lines.append(
                f'  MC 승률    : 승 {_wr:.0%} / 무 {mc.get("draw_rate", 0):.0%} / '
                f'패 {mc.get("loss_rate", 0):.0%}  (평균 임무 점수 {mc.get("mean_friendly_score", 0.0):.2f})')
        lines.append(f'  참고 요격률: {mc.get("mean_intercept", 0):.1%}')
    else:
        lines.append(f'  요격률     : {mc.get("mean_intercept", 0):.1%}  (±{mc.get("std_intercept", 0):.1%})')
        lines.append(f'  완전요격   : {mc.get("full_pass_rate", 0):.1%}')
    lines += [
        f'  아군 피격  : {avg_hits:.1f}회 (평균)',
        f'  적 격침    : {avg_edest:.1f}기/척 (평균)',
        f'  총 비용    : ${result.get("total_cost", 0):,.0f}',
        '=' * 80, '',
    ]
    try:
        with open(_log_path(), 'a', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')
    except Exception:
        pass

    # ── JSON 로그 ─────────────────────────────────────────────────────────
    record = {
        'datetime':       now,
        'fleet':          cfg.get('fleet_preset', '?'),
        'weather':        cfg.get('weather', '?'),
        'mc_n':           mc.get('n', 0),
        'enemy':          enemy_str,
        'total_threats':  result.get('total_threats', 0),
        'mean_intercept': round(mc.get('mean_intercept', 0), 4),
        'std_intercept':  round(mc.get('std_intercept', 0), 4),
        'full_pass_rate': round(mc.get('full_pass_rate', 0), 4),
        'avg_friendly_hits':    round(avg_hits,  2),
        'avg_enemy_destroyed':  round(avg_edest, 2),
        'total_cost':     result.get('total_cost', 0),
    }
    if result.get('outcome'):   # 전장 모드 — 승/패·임무 점수 지표 동반 기록
        record['outcome']       = result.get('outcome')
        record['friendly_score'] = round(result.get('friendly_score', 0.0), 4)
        if mc.get('win_rate') is not None:
            record['win_rate']  = round(mc.get('win_rate', 0), 4)
            record['draw_rate'] = round(mc.get('draw_rate', 0), 4)
            record['loss_rate'] = round(mc.get('loss_rate', 0), 4)
            record['mean_friendly_score'] = round(mc.get('mean_friendly_score', 0.0), 4)
    records = _load_json_log()
    records.append(record)
    _save_json_log(records)


_SIM_MODE_NAMES = {0: '빠름', 1: '표준', 2: '정밀'}


def _db_path() -> str:
    return os.path.join(_log_base(), 'sim_history.db')


def _ensure_db():
    import sqlite3
    con = sqlite3.connect(_db_path())
    con.execute('''CREATE TABLE IF NOT EXISTS sim_history (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        datetime         TEXT    NOT NULL,
        fleet            TEXT,
        weather          TEXT,
        mc_n             INTEGER,
        sim_mode         TEXT,
        enemy            TEXT,
        total_threats    INTEGER,
        mean_intercept   REAL,
        std_intercept    REAL,
        full_pass_rate   REAL,
        cvar             REAL,
        avg_friendly_hits   REAL,
        avg_enemy_destroyed REAL,
        total_cost       REAL,
        req_pass         INTEGER,
        cfg_json         TEXT,
        status           TEXT DEFAULT '완료',
        outcome          TEXT,
        win_rate         REAL,
        friendly_score   REAL
    )''')
    # 기존 DB 호환: 컬럼이 없으면 추가 (이미 있으면 무시)
    for _ddl in (
        "ALTER TABLE sim_history ADD COLUMN status TEXT DEFAULT '완료'",
        "ALTER TABLE sim_history ADD COLUMN outcome TEXT",          # 전장 모드 승/패/무
        "ALTER TABLE sim_history ADD COLUMN win_rate REAL",         # 전장 MC 승률
        "ALTER TABLE sim_history ADD COLUMN friendly_score REAL",   # 전장 아군 임무 점수
    ):
        try:
            con.execute(_ddl)
        except Exception:
            pass
    con.commit()
    con.close()


def _write_sim_db(cfg: dict, result: dict, mc: dict, sim_mode_idx: int = 1,
                  status: str = '완료'):
    import sqlite3
    from datetime import datetime as _dt
    _ensure_db()
    now = _dt.now().strftime('%Y-%m-%d %H:%M:%S')
    enemy_parts = [f"{e.get('preset','?')} ×{e.get('count',1)}"
                   for e in cfg.get('enemy_fleet', [])]
    enemy_str = ', '.join(enemy_parts) if enemy_parts else cfg.get('enemy_fleet_preset', '?')
    n = max(mc.get('n', 1), 1)
    avg_hits  = sum(mc.get('friendly_hits',  [])) / n
    avg_edest = sum(mc.get('enemy_destroyed', [])) / n
    cvar_val  = mc.get('cvar', None)
    # REQ 전체 통과 여부 (평가 실패 시 None)
    req_pass = None
    try:
        if result.get('outcome'):   # 지속 전장 모드 — 목표 기반 REQ
            from engine_combat import evaluate_req_battle_v7
            _, verdicts, _ = evaluate_req_battle_v7(result, mc, cfg)
        else:
            from engine_combat import evaluate_req_v7
            verdicts, _ = evaluate_req_v7(result, mc, cfg)
        req_pass = int(all(verdicts))
    except Exception:
        _write_log(f'[WARN] evaluate_req 실패: {traceback.format_exc()}')
    # cfg 저장: enemy_fleet 리스트는 enemy_str 컬럼에 이미 있으므로 제외
    safe_cfg = {k: v for k, v in cfg.items() if k != 'enemy_fleet'}
    try:
        con = sqlite3.connect(_db_path())
        _outcome = result.get('outcome')   # 전장 모드만 값, 단발은 None(NULL)
        _win_rate = round(mc.get('win_rate'), 4) if (_outcome and mc.get('win_rate') is not None) else None
        _f_score  = round(result.get('friendly_score', 0.0), 4) if _outcome else None
        con.execute('''INSERT INTO sim_history
            (datetime, fleet, weather, mc_n, sim_mode, enemy, total_threats,
             mean_intercept, std_intercept, full_pass_rate, cvar,
             avg_friendly_hits, avg_enemy_destroyed, total_cost, req_pass, cfg_json,
             status, outcome, win_rate, friendly_score)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (now,
             cfg.get('fleet_preset', '?'),
             cfg.get('weather', '?'),
             mc.get('n', 0),
             _SIM_MODE_NAMES.get(sim_mode_idx, '표준'),
             enemy_str,
             result.get('total_threats', 0),
             round(mc.get('mean_intercept', 0), 4),
             round(mc.get('std_intercept', 0), 4),
             round(mc.get('full_pass_rate', 0), 4),
             round(cvar_val, 4) if cvar_val is not None else None,
             round(avg_hits, 2),
             round(avg_edest, 2),
             result.get('total_cost', 0),
             req_pass,
             json.dumps(safe_cfg, ensure_ascii=False),
             status, _outcome, _win_rate, _f_score))
        con.commit()
        con.close()
    except Exception:
        _write_log(f'[WARN] sim_history DB 저장 실패: {traceback.format_exc()}')


def _load_sim_db(limit: int = 500) -> list:
    import sqlite3
    _ensure_db()
    try:
        con = sqlite3.connect(_db_path())
        con.row_factory = sqlite3.Row
        rows = con.execute(
            'SELECT * FROM sim_history ORDER BY id DESC LIMIT ?', (limit,)
        ).fetchall()
        con.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


def _clear_sim_db():
    import sqlite3
    _ensure_db()
    try:
        con = sqlite3.connect(_db_path())
        con.execute('DELETE FROM sim_history')
        con.commit()
        con.close()
    except Exception:
        pass
