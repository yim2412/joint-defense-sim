"""
app_workers — 백그라운드 워커 계층(QThread).

app_main.py에서 분리. 편대 추천·쇼케이스 비교·반사실 분해·시뮬 실행(SimWorker)·시스템
계측 워커. UI를 만들지 않고 시그널만 emit한다.

의존은 app_engine(엔진 심볼)·app_utils(계측·풀·경로)·PyQt6뿐 — **app_main을 import하지
말 것**(즉시 순환). app_engine을 따로 뺀 이유가 바로 이 순환을 끊기 위해서다.

⚠ `_GLOBAL_POOL`은 반드시 `app_utils._GLOBAL_POOL`로 참조한다. 이름 import하면 예열 전
None이 복사돼 매 시뮬마다 새 풀을 파고, 예열이 통째로 무의미해진다(조용한 성능 저하).
"""

import os, sys, time, threading, traceback
from concurrent.futures import ProcessPoolExecutor, as_completed, wait as cf_wait, FIRST_COMPLETED
import psutil
import numpy as np

from PyQt6.QtCore import QThread, pyqtSignal

import app_utils
from app_utils import (_get_gpu_info, _get_cpu_temp, _pool_map, _set_pool_priority,
                       _res, _PERF_HISTORY, _SYS_CACHE)
from app_engine import (
    _V7_OK, run_v7_simulation, run_battle_simulation, monte_carlo_v7, monte_carlo_lhs,
    _mc_batch_worker, recommend_fleet_v7, stress_test_grid, sobol_analysis, compute_cvar,
    BATTLE_HORIZON_S, STRESS_DIMS, _FLEET_CANDIDATES_KR, _FLEET_CANDIDATES_COMBINED,
)

class FleetRecommendWorker(QThread):
    """적정 편대 추천 — 한국 단독·한미 연합 두 그룹을 MC 평가."""
    progress = pyqtSignal(int, int, str)   # (done, total, group)
    finished = pyqtSignal(dict)            # {'kr': [...], 'combined': [...]}
    error    = pyqtSignal(str)

    def __init__(self, cfg: dict, n: int = 150):
        super().__init__()
        self.cfg = cfg
        self.n   = n

    def run(self):
        if not _V7_OK:
            return
        try:
            groups = [('kr', _FLEET_CANDIDATES_KR), ('combined', _FLEET_CANDIDATES_COMBINED)]
            total  = sum(len(c) for _, c in groups)
            done   = 0
            out: dict = {}
            for key, cands in groups:
                def _cb(i, _tot, _phase, _base=done):
                    self.progress.emit(_base + i, total, key)
                # 후보 × n 시뮬을 글로벌 풀 병렬(map_fn). seed 고정 → 결정론.
                out[key] = recommend_fleet_v7(
                    self.cfg, cands, n=self.n, progress_cb=_cb, map_fn=_pool_map)
                done += len(cands)
            self.finished.emit(out)
        except Exception as e:
            self.error.emit(str(e))


class _SimCancelled(BaseException):
    """중단 요청 전파용 — except Exception에 잡히지 않도록 BaseException 상속."""


class ShowcaseCompareWorker(QThread):
    """쇼케이스 ON/OFF 비교 — 동일 시나리오에서 대상 토글만 OFF·ON으로 바꿔
    MC를 순차 2회 돌린 뒤 두 결과 dict를 함께 emit한다. 엔진·전역 상태 무변경."""
    progress = pyqtSignal(str)                 # 진행 안내 문구
    done     = pyqtSignal(str, dict, dict)     # (toggle_key, mc_off, mc_on)
    failed   = pyqtSignal(str, str)            # (toggle_key, 오류 메시지)

    def __init__(self, toggle_key: str, base_cfg: dict, mc_n: int = 40):
        super().__init__()
        self.toggle_key = toggle_key
        self.base_cfg   = dict(base_cfg)
        self.mc_n       = mc_n

    def run(self):
        try:
            cfg_off = dict(self.base_cfg); cfg_off[self.toggle_key] = False
            cfg_on  = dict(self.base_cfg); cfg_on[self.toggle_key]  = True
            self.progress.emit(f"토글 OFF — {self.mc_n}회 분석 중…")
            mc_off = monte_carlo_v7(cfg_off, n=self.mc_n)
            if self.isInterruptionRequested():
                return
            self.progress.emit(f"토글 ON — {self.mc_n}회 분석 중…")
            mc_on = monte_carlo_v7(cfg_on, n=self.mc_n)
            if self.isInterruptionRequested():
                return
            self.done.emit(self.toggle_key, mc_off, mc_on)
        except Exception:
            self.failed.emit(self.toggle_key, traceback.format_exc())


# Phase 3(백로그 5번): 결과에 "이 토글이 이번 판 결과를 바꿨나"를 반사실(counterfactual)로 표시.
# 켜진 실험적/전술 토글을 각각 OFF로 되돌려 같은 고정 시드로 단발 재실행 → 요격률·피격 델타.
_IMPACT_TOGGLES = [
    ('enable_esm_arm',               'ESM→ARM 역탐지'),
    ('enable_target_difficulty',     '표적 난이도(속도·RCS)'),
    ('enable_sonar_emcon',           '능동 소나 역탐지'),
    ('enable_hgv_glide',             '극초음속 활공 다층요격'),
    ('enable_asw_forward',           '대잠 항공 전진 초계'),
    ('enable_cyber_warfare',         '사이버전'),
    ('enable_dmo',                   '분산 해양 작전(DMO)'),
    ('enable_coord_deception',       '전자 좌표 기만'),
    ('enable_mine_threat',           '기뢰 위협'),
    ('enable_minesweeping',          '소해'),
    ('enable_unmanned_assets',       '무인 함정(USV·UUV)'),
    ('enable_drone_swarm',           '적 무인기 군집'),
    ('enable_laser_dew',             '지향성 에너지 무기(레이저)'),
    ('enable_autonomous_engagement', '함정 자율 교전'),
    ('enable_ras_rearm',             'RAS 탄약 재보급'),
    ('enable_recon_drone',           '정찰 드론'),
    ('enable_png',                   'PNG 비례항법'),
    ('enable_iff',                   'IFF 식별'),
    ('enable_multibearing',          '다방위 공격'),
]
_IMPACT_SEED = 20260703   # 반사실 재현용 고정 시드(현재 설정에서 토글 유무만 대조)


class CounterfactualWorker(QThread):
    """Phase 3: 켜진 실험적/전술 토글을 각각 OFF로 되돌려 같은 시드로 단발 재실행 →
    요격률·아군 피격 델타를 계산해 '이 토글이 이번 설정 결과를 바꾸는가'를 표시.
    엔진·전역 상태 무변경(로컬 cfg 사본만). 결과 화면 표시 전용."""
    done   = pyqtSignal(list)   # [(label, d_intercept_pp, d_hits, impacted), ...]
    failed = pyqtSignal(str)

    def __init__(self, base_cfg: dict, toggles: list):
        super().__init__()
        self.base_cfg = dict(base_cfg)
        self.toggles  = list(toggles)

    def _run_one(self, cfg: dict) -> dict:
        if cfg.get('enable_battle_mode', False):
            return run_battle_simulation(cfg)
        return run_v7_simulation(cfg)

    def run(self):
        try:
            base = dict(self.base_cfg)
            base['sim_seed'] = _IMPACT_SEED
            base['mc_mode']  = True   # 로그·프레임 억제(반복 단발 오버헤드↓, 수치 동일)
            r_on  = self._run_one(base)
            ir_on = r_on.get('intercept_rate', 0.0)
            fh_on = r_on.get('friendly_hits', 0)
            out = []
            for key, label in self.toggles:
                if self.isInterruptionRequested():
                    return
                cfg_off = dict(base); cfg_off[key] = False
                r_off = self._run_one(cfg_off)
                d_ir = (ir_on - r_off.get('intercept_rate', 0.0)) * 100.0   # %p
                d_fh = fh_on - r_off.get('friendly_hits', 0)
                impacted = (abs(d_ir) >= 0.05) or (abs(d_fh) >= 1)
                out.append((label, d_ir, d_fh, impacted))
            self.done.emit(out)
        except Exception:
            self.failed.emit(traceback.format_exc())


class SimWorker(QThread):
    progress        = pyqtSignal(str)
    progress_detail = pyqtSignal(int, int, float)  # (현재, 전체, ETA초)
    finished        = pyqtSignal(dict, dict)
    error           = pyqtSignal(str)
    sim_started     = pyqtSignal()
    sim_ended       = pyqtSignal()
    cancelled       = pyqtSignal()                  # 중단 버튼으로 인터럽트 시
    batch_done      = pyqtSignal(int, int)         # (완료배치, 전체배치)
    rate_update     = pyqtSignal(float, float, float)  # (mean_rate, avg_e_dest, avg_f_hits)
    hist_update     = pyqtSignal(list)                 # 개별 시뮬 요격률 누적 — 분포 히스토그램용
    # v8.26: 진행 팝업 상세화
    step_update     = pyqtSignal(float, float, int, int, str)  # (t, t_max, alive, vls, last_log) — 단일 시뮬
    phase_update     = pyqtSignal(dict)                         # 단계별 평균 타이밍 — MC 배치 완료마다
    # v10.7: 전술 의사결정 모드
    tactical_pause   = pyqtSignal(dict)                         # TacticalState 스냅샷 → 다이얼로그 표시

    _last_intercept_rate: float = -1.0   # 이전 실행 결과 캐시 (클래스 변수)

    def __init__(self, cfg: dict, mc_n: int, precision_mode: bool = False,
                 sobol_npp: int = 3, sim_mode_idx: int = 1, test_mode: bool = False):
        super().__init__()
        self.cfg            = cfg
        self.mc_n           = mc_n
        self.precision_mode = precision_mode
        self.sobol_npp      = sobol_npp
        self.sim_mode_idx   = sim_mode_idx
        self.test_mode      = test_mode
        # v10.7: 전술 모드 동기화 객체
        import threading, queue as _queue
        self._tactical_event  = threading.Event()
        self._tactical_queue  = _queue.Queue()

    def _tactical_pause_cb(self, state) -> dict:
        """엔진 훅 — 워커 스레드에서 호출. 메인 스레드에 상태 전달 후 블록."""
        import dataclasses
        snap = dataclasses.asdict(state)
        self._tactical_event.clear()
        self.tactical_pause.emit(snap)     # queued signal → main thread
        self._tactical_event.wait()        # block until user confirms
        choice = self._tactical_queue.get_nowait() if not self._tactical_queue.empty() else {}
        return choice

    def resume_tactical(self, choice: dict):
        """메인 스레드에서 호출 — 사용자 선택 전달 후 워커 재개."""
        self._tactical_queue.put(choice)
        self._tactical_event.set()

    def run(self):
        try:
            self.sim_started.emit()
            self.progress.emit("시뮬레이션 실행 중...")

            def _step_cb(t, t_max, alive, vls, last_log):
                self.step_update.emit(t, t_max, alive, vls, last_log)

            # v10.7: 전술 모드 훅 주입
            _tactical_hook = None
            # 전장 모드 + AI 전술(학습된 정책) → numpy 추론 cb가 전술 자동 결정(사람 일시정지보다 우선).
            if (self.cfg.get('enable_battle_mode', False)
                    and self.cfg.get('enable_rl_policy', False)):
                try:
                    import ai_policy_infer
                    _tactical_hook = ai_policy_infer.make_policy_cb(
                        _res('ai_rl_policy.npz'),
                        self.cfg.get('battle_horizon_s', BATTLE_HORIZON_S))
                except Exception:
                    _tactical_hook = None
                if _tactical_hook is None:           # npz 없음·로드 실패 → 전술 auto 폴백
                    self.progress.emit("AI 전술 정책 로드 실패 — 기본 전술로 진행")
            elif self.cfg.get('tactical_mode', False):
                _tactical_hook = self._tactical_pause_cb

            # v18.1: 작전급 캠페인 모드 — 즉시예측 해결기로 72h 전역.
            # v18.6: 캠페인 MC — 시뮬 모드(빠른/표준/정밀)를 캠페인 전용 반복 횟수로 매핑.
            #   전술 mc_n(5000~100000)은 캠페인엔 과함(1회가 더 무거움). 대표 단발(seed 0)을
            #   배너·시계열용으로 함께 실행하고 MC 분포를 result에 임베드해 조기 반환.
            if self.cfg.get('enable_campaign_mode', False):
                from engine_campaign import (run_campaign, monte_carlo_campaign,
                                             load_forecast_model)
                camp_n = 10 if self.test_mode else [100, 300, 1000][self.sim_mode_idx]
                model = load_forecast_model()   # 1회 로드 → 대표 단발·MC 공유

                def _camp_cb(done, total):
                    if self.isInterruptionRequested():
                        raise _SimCancelled()
                    self.progress_detail.emit(done, total, 0.0)
                    self.progress.emit(f"캠페인 MC {done}/{total}회 분석 중…")

                result = run_campaign(dict(self.cfg, campaign_seed=0),
                                      step_cb=_step_cb, model=model)   # 대표 단발(배너·시계열)
                mc = monte_carlo_campaign(self.cfg, n=camp_n, model=model,
                                          progress_cb=_camp_cb)
                result['campaign_mc'] = mc     # 결과 렌더가 분포 표시에 사용
                # v21.4: 군별 기여도(반사실 분해) — 전역을 연합별로 다시 돌려야 나오므로
                #   MC 뒤에 별도로 잰다. 반복수는 MC(최대 1000회)와 달리 30회로 묶는다 —
                #   4연합+2도메인프로브 = 6배수가 곱해져 그대로 따라가면 분석이 수 분이 된다.
                if self.cfg.get('enable_joint_report', False):
                    from engine_campaign import shapley_contribution

                    def _shap_cb(done, total):
                        if self.isInterruptionRequested():
                            raise _SimCancelled()
                        self.progress_detail.emit(done, total, 0.0)
                        self.progress.emit(f"군별 기여도 분석 {done}/{total}회…")

                    shap_n = 10 if self.test_mode else min(camp_n, 30)
                    result['joint_report'] = shapley_contribution(
                        self.cfg, n=shap_n, model=model, progress_cb=_shap_cb)
                self.finished.emit(result, mc)
                return

            if self.cfg.get('enable_battle_mode', False):
                result = run_battle_simulation(self.cfg, step_cb=_step_cb,
                                               tactical_cb=_tactical_hook)
            else:
                result = run_v7_simulation(self.cfg, step_cb=_step_cb,
                                           tactical_cb=_tactical_hook)
            # 중단 기록용 스냅샷 — 중단 시 _on_cancelled가 부분 통계를 DB에 기록
            self._partial_tt = result.get('total_threats', 0)
            self._partial = None
            self.progress.emit(f"MC {self.mc_n}회 분석 중...")
            t0 = time.time()

            def _cb(done, total):
                # v13.06.04: 순차 MC 경로도 진행 콜백에서 중단 확인
                if self.isInterruptionRequested():
                    raise _SimCancelled()
                elapsed = time.time() - t0
                eta = (elapsed / done * (total - done)) if done > 0 else 0.0
                self.progress_detail.emit(done, total, eta)
                self.progress.emit(f"MC {done}/{total}회 | 잔여 약 {eta:.0f}초")

            n_cores = min(os.cpu_count() or 1, 8)
            if not _V7_OK or self.mc_n < 100 or n_cores <= 1:
                # 소규모 or 단일코어 — 순차 실행
                try:
                    mc = monte_carlo_v7(self.cfg, n=self.mc_n, progress_cb=_cb)
                except TypeError:
                    mc = monte_carlo_v7(self.cfg, n=self.mc_n)
            else:
                # 멀티프로세싱 병렬 MC
                # 배치가 작을수록 (배치 완료마다 그래프 갱신되므로) 진행 화면 동기화가
                # 잦아짐 + 취소 시 잔여 서브프로세스 최소화. 너무 작으면 디스패치
                # 오버헤드↑ → 갱신 빈도와 처리량의 절충: 코어당 ~10여 회.
                batch_size = max(4, min(8, self.mc_n // (n_cores * 12)))
                batches, seed_offset = [], 0
                while seed_offset < self.mc_n:
                    actual = min(batch_size, self.mc_n - seed_offset)
                    batches.append((self.cfg, actual, seed_offset))
                    seed_offset += actual

                all_rates, all_f_hits, all_e_dest = [], [], []
                all_f_lost, all_costs = [], []
                all_weapon: dict = {}
                all_ship:   dict = {}
                all_wzero:  dict = {}
                done_count = 0

                # app_utils 경유 필수 — 이름 import면 예열 전 None이 복사돼 매번 새 풀을 판다
                pool = app_utils._GLOBAL_POOL or ProcessPoolExecutor(max_workers=n_cores)
                _own = app_utils._GLOBAL_POOL is None
                if _own:
                    _set_pool_priority(pool)  # BUG-1: 인라인 풀도 BELOW_NORMAL
                batch_done_n = 0
                _phase_acc: dict = {}   # v8.26: 배치별 단계 타이밍 누적
                _extra_acc: dict = {}   # v12.4·v12.6: 침수·IFF 통계 누적
                _feat_acc:  dict = {}   # 죽은 기능 방지 ②: 기능별 발동 횟수 누적(dict라 별도 병합)
                # 슬라이딩 윈도우 제출 — 전체 배치를 한 번에 풀에 던지지 않고
                # 실행 중 배치를 코어×2로 제한. 중단 시 미제출 배치는 아예 돌지 않아
                # 즉시 멈춤 (글로벌 풀은 앱 공유라 shutdown으로 못 끊기 때문).
                _batch_iter = iter(batches)
                inflight = set()
                for _ in range(min(n_cores * 2, len(batches))):
                    inflight.add(pool.submit(_mc_batch_worker, next(_batch_iter)))
                # 0.5초마다 중단 체크 — as_completed()는 배치 완료까지 블로킹되어 즉시 반응 불가
                while inflight:
                    if self.isInterruptionRequested():
                        for f in inflight:
                            f.cancel()
                        if _own:
                            pool.shutdown(wait=False)
                        raise _SimCancelled()
                    done_futs, inflight = cf_wait(inflight, timeout=0.5,
                                                  return_when=FIRST_COMPLETED)
                    inflight = set(inflight)
                    for fut in done_futs:
                        rates, fh, ed, fl, cs, wu, sh, wz, pt, xs = fut.result()
                        all_rates.extend(rates);  all_f_hits.extend(fh)
                        all_e_dest.extend(ed);    all_f_lost.extend(fl)
                        all_costs.extend(cs)
                        for k, v in wu.items(): all_weapon.setdefault(k, []).extend(v)
                        for k, v in sh.items(): all_ship.setdefault(k, []).extend(v)
                        for k, v in wz.items(): all_wzero[k] = all_wzero.get(k, 0) + v
                        for k, v in pt.items(): _phase_acc[k] = _phase_acc.get(k, 0.0) + v
                        for k, v in xs.items():
                            if k == 'feature_fires':   # dict(int) — extend 금지, 키별 합산
                                for _fk, _fv in v.items(): _feat_acc[_fk] = _feat_acc.get(_fk, 0) + _fv
                            else:
                                _extra_acc.setdefault(k, []).extend(v)
                        done_count += len(rates)
                        batch_done_n += 1
                        self.batch_done.emit(batch_done_n, len(batches))
                        _cb(done_count, self.mc_n)
                        # 데이터는 매 배치 전달 — 화면은 자체 1초 타이머로 그래프를 그림
                        # (throttle은 배치 완료 타이밍에 끌려가 1초가 불규칙해지므로 제거).
                        if all_rates:
                            self.rate_update.emit(
                                float(np.mean(all_rates)),
                                float(np.mean(all_e_dest)) if all_e_dest else 0.0,
                                float(np.mean(all_f_hits)) if all_f_hits else 0.0,
                            )
                            # 개별 시뮬 요격률 분포 — 히스토그램용 (누적 평균과 별개)
                            self.hist_update.emit(list(all_rates))
                            # 중단 기록용 부분 통계 스냅샷
                            self._partial = {
                                'done': done_count,
                                'mean': float(np.mean(all_rates)),
                                'tt':   self._partial_tt,
                            }
                        if _phase_acc:
                            _n_b = max(batch_done_n, 1)
                            self.phase_update.emit({k: v / _n_b for k, v in _phase_acc.items()})
                        # 슬라이딩 윈도우: 완료된 배치만큼 다음 배치를 채워 제출
                        _nb = next(_batch_iter, None)
                        if _nb is not None:
                            inflight.add(pool.submit(_mc_batch_worker, _nb))
                if _own:
                    pool.shutdown(wait=False)

                arr = np.array(all_rates)
                _n_total = max(len(all_rates), 1)
                mc = {
                    'intercept_rates':         all_rates,
                    'friendly_hits':           all_f_hits,
                    'enemy_destroyed':         all_e_dest,
                    'friendly_lost':           all_f_lost,
                    'total_costs':             all_costs,
                    'weapon_avg_remaining':    {k: float(np.mean(v)) for k, v in all_weapon.items()},
                    'weapon_exhaustion_rates': {k: v / _n_total for k, v in all_wzero.items()},
                    'ship_avg_hits':           {k: float(np.mean(v)) for k, v in all_ship.items()},
                    'mean_intercept':          float(arr.mean()),
                    'std_intercept':           float(arr.std()),
                    'full_pass_rate':          float((arr == 1.0).mean()),
                    'n':                       len(all_rates),
                    'mean_ships_sunk_by_flood': float(np.mean(_extra_acc.get('ships_sunk_by_flood', [0]))),
                    'mean_ships_flooding':      float(np.mean(_extra_acc.get('ships_flooding', [0]))),
                    'mean_iff_failures':        float(np.mean(_extra_acc.get('iff_failures', [0]))),
                    'mean_iff_fratricide':      float(np.mean(_extra_acc.get('iff_fratricide', [0]))),
                    'mean_laser_kills':         float(np.mean(_extra_acc.get('laser_kills', [0]))),
                    'feature_fires_total':      dict(_feat_acc),   # 죽은 기능 방지 ②: 기능별 총 발동
                }
                _bo = _extra_acc.get('outcome', [])
                if _bo:   # 전장 모드 — 병렬 MC 승률 집계
                    _bn = max(len(_bo), 1)
                    mc['win_rate']  = _bo.count('win')  / _bn
                    mc['loss_rate'] = _bo.count('loss') / _bn
                    mc['draw_rate'] = _bo.count('draw') / _bn
                    mc['mean_friendly_score'] = float(np.mean(_extra_acc.get('friendly_score', [0.0])))

            # ── CVaR: 기존 MC rates에서 직접 계산 (추가 시뮬 불필요) ─────────
            if _V7_OK:
                try:
                    mc['cvar'] = compute_cvar(mc.get('intercept_rates', []))
                except Exception:
                    mc['cvar'] = 0.0

            # ── LHS 파라미터 불확실성 분석 (중간 규모, 병렬 MC와 별개) ────────
            # 빠름=1,000  표준=2,000  정밀=10,000
            lhs_result = {}
            if _V7_OK:
                if self.isInterruptionRequested():
                    raise _SimCancelled()
                lhs_n_map  = {5_000: 1_000, 10_000: 2_000, 100_000: 10_000}
                lhs_n      = 10 if self.test_mode else lhs_n_map.get(self.mc_n, 2_000)
                self.progress.emit(f"LHS 파라미터 불확실성 분석 중... ({lhs_n:,}회)")
                lhs_t0 = time.time()

                def _lhs_cb(done, total):
                    if self.isInterruptionRequested():
                        raise _SimCancelled()
                    if done % max(1, total // 10) == 0:
                        ela = time.time() - lhs_t0
                        eta = ela / done * (total - done) if done > 0 else 0
                        self.progress.emit(f"LHS {done:,}/{total:,} | 잔여 {eta:.0f}초")

                try:
                    lhs_result = monte_carlo_lhs(self.cfg, n=lhs_n, progress_cb=_lhs_cb)
                except _SimCancelled:
                    raise
                except Exception as ex:
                    lhs_result = {'error': str(ex)}

            # ── 스트레스 테스트 (모든 모드, n_per_cell 가변) ─────────────────
            stress_result = {}
            if _V7_OK:
                if self.isInterruptionRequested():
                    raise _SimCancelled()
                n_cell_map = {5_000: 300, 10_000: 500, 100_000: 3_000}
                n_per_cell = 3 if self.test_mode else n_cell_map.get(self.mc_n, 500)
                total_stress = len(STRESS_DIMS['channel_degrade']['values']) * \
                               len(STRESS_DIMS['radar_degrade']['values'])
                self.progress.emit(f"스트레스 테스트 중... (셀당 {n_per_cell}회, 총 {total_stress}셀)")

                def _stress_cb(done, total):
                    if self.isInterruptionRequested():
                        raise _SimCancelled()
                    self.progress.emit(f"스트레스 테스트 {done}/{total} 셀 완료")

                try:
                    stress_result = stress_test_grid(
                        self.cfg, n_per_cell=n_per_cell, progress_cb=_stress_cb,
                        map_fn=_pool_map)   # 글로벌 풀 8코어 병렬
                except _SimCancelled:
                    raise
                except Exception as ex:
                    stress_result = {'error': str(ex)}

            # ── Sobol 민감도 분석 (정밀 모드 전용) ──────────────────────────
            sobol_result = {}
            if _V7_OK and self.precision_mode:
                npp        = self.sobol_npp
                total_est  = 32_768 * npp
                self.progress.emit(
                    f"Sobol 민감도 분석 중... (포인트당 {npp}회, 총 ~{total_est:,}회, 수 분 소요)")
                sobol_t0 = time.time()

                def _sobol_cb(done, total):
                    # v13.06.04: Sobol 단계도 진행 콜백에서 중단 확인
                    if self.isInterruptionRequested():
                        raise _SimCancelled()
                    if done % max(1, total // 20) == 0:
                        ela = time.time() - sobol_t0
                        eta = ela / done * (total - done) if done > 0 else 0
                        self.progress.emit(
                            f"Sobol {done:,}/{total:,} 포인트 | 잔여 {eta:.0f}초")

                try:
                    sobol_result = sobol_analysis(
                        self.cfg, n_sobol=4096, n_per_point=npp,
                        progress_cb=_sobol_cb, map_fn=_pool_map)   # 글로벌 풀 8코어 병렬
                except _SimCancelled:
                    raise   # v13.06.04: 중단은 삼키지 말고 전파
                except Exception as ex:
                    sobol_result = {'error': str(ex)}

            mc['lhs']    = lhs_result
            mc['stress'] = stress_result
            mc['sobol']  = sobol_result

            elapsed = time.time() - t0
            rate    = self.mc_n / elapsed if elapsed > 0 else 0.0
            _PERF_HISTORY.append({
                'time':     time.time(),
                'mc_n':     self.mc_n,
                'duration': elapsed,
                'rate':     rate,
            })
            if len(_PERF_HISTORY) > 10:
                _PERF_HISTORY.pop(0)
            # v8.26: 이전 실행 결과 캐싱 (델타 비교용)
            SimWorker._last_intercept_rate = mc.get('mean_intercept', -1.0)
            self.finished.emit(result, mc)
        except _SimCancelled:
            self.cancelled.emit()
        except Exception as e:
            self.error.emit(str(e))
        finally:
            self.sim_ended.emit()


# ════════════════════════════════════════════════════════════════════════════
#  시스템 데이터 백그라운드 워커 (블로킹 I/O를 메인 스레드에서 분리)
# ════════════════════════════════════════════════════════════════════════════
class _SysDataWorker(QThread):
    """nvidia-smi·WMI 등 블로킹 I/O를 1초마다 백그라운드에서 수집, _SYS_CACHE 갱신."""

    def run(self):
        while not self.isInterruptionRequested():
            try:
                cpu   = psutil.cpu_percent(interval=None)
                cores = psutil.cpu_percent(percpu=True, interval=None) or []
                mem   = psutil.virtual_memory()
                swap  = psutil.swap_memory()
                gpu   = _get_gpu_info()      # subprocess — 메인 스레드 블로킹 제거
                ctemp = _get_cpu_temp()      # WMI — 메인 스레드 블로킹 제거
                proc  = psutil.Process()
                proc_ram = proc.memory_info().rss / 1024**2
                stats: list = []
                try:
                    for c in proc.children(recursive=True):
                        try:
                            stats.append({
                                'pid':    c.pid,
                                'cpu':    c.cpu_percent(interval=None),
                                'ram':    c.memory_info().rss / 1024**2,
                                'status': c.status(),
                            })
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                except Exception:
                    pass
                _SYS_CACHE.update({
                    'cpu': cpu, 'mem_pct': mem.percent,
                    'mem_used': mem.used, 'mem_total': mem.total,
                    'gpu': gpu, 'cpu_temp': ctemp,
                    'cores': list(cores), 'proc_ram': proc_ram,
                    'worker_stats': stats, 'swap_used': swap.used,
                    'thread_cnt': threading.active_count(),
                })
            except Exception:
                pass
            self.msleep(1000)


_SYS_DATA_WORKER: '_SysDataWorker | None' = None


def _start_sys_data_worker():
    global _SYS_DATA_WORKER
    _SYS_DATA_WORKER = _SysDataWorker()
    _SYS_DATA_WORKER.start()


def _stop_sys_data_worker():
    global _SYS_DATA_WORKER
    if _SYS_DATA_WORKER is not None:
        _SYS_DATA_WORKER.requestInterruption()
        _SYS_DATA_WORKER.quit()
        if not _SYS_DATA_WORKER.wait(1500):
            _SYS_DATA_WORKER.terminate()
            _SYS_DATA_WORKER.wait(300)
        _SYS_DATA_WORKER = None


# ════════════════════════════════════════════════════════════════════════════
#  Matplotlib Canvas 래퍼
