"""MainWindow mixin — 적정 편대 추천 최적화 + 토글 영향도(counterfactual) 분석.

app_main.py 분할 8/N (MainWindow mixin 분할). 의존은 PyQt6·app_theme·app_workers·
ui_charts뿐.
"""
from PyQt6.QtCore import QThread

from app_theme import C_SUBTEXT
from app_workers import CounterfactualWorker, FleetRecommendWorker, _IMPACT_TOGGLES
from ui_charts import _render_fleet_chart


class OptimizeMixin:
    def _start_toggle_impact(self, cfg: dict):
        """Phase 3: 켜진 실험적/전술 토글의 반사실 영향 분석을 비동기로 시작.
        켜진 토글이 없으면 표시 숨김."""
        active = [(k, lbl) for k, lbl in _IMPACT_TOGGLES if cfg.get(k, False)]
        lbl = getattr(self, '_lbl_toggle_impact', None)
        if lbl is None:
            return
        if not active:
            lbl.setVisible(False)
            return
        # 이전 분석이 돌고 있으면 중단
        prev = getattr(self, '_impact_worker', None)
        if prev is not None and prev.isRunning():
            prev.requestInterruption()
            prev.wait(100)
        lbl.setText(f"<span style='color:{C_SUBTEXT}'>🔬 활성 토글 영향 분석 중… "
                    f"(켜진 토글 {len(active)}종을 각각 꺼서 비교)</span>")
        lbl.setVisible(True)
        self._impact_worker = CounterfactualWorker(cfg, active)
        self._impact_worker.done.connect(self._on_toggle_impact_done)
        self._impact_worker.failed.connect(
            lambda _e: self._lbl_toggle_impact.setVisible(False))
        self._impact_worker.start(QThread.Priority.LowPriority)
    def _on_toggle_impact_done(self, results: list):
        """반사실 분석 완료 — 토글별 영향(요격률·피격 델타)을 결과 배너 아래 표시."""
        lbl = getattr(self, '_lbl_toggle_impact', None)
        if lbl is None:
            return
        if not results:
            lbl.setVisible(False)
            return
        parts = []
        for label, d_ir, d_fh, impacted in results:
            if impacted:
                bits = []
                if abs(d_ir) >= 0.05:
                    sign = '+' if d_ir > 0 else '−'
                    bits.append(f"요격률 {sign}{abs(d_ir):.1f}%p")
                if abs(d_fh) >= 1:
                    bits.append(f"피격 {d_fh:+d}발")
                parts.append(f"<span style='color:#2ecc71'>🟢 <b>{label}</b> "
                             f"{' · '.join(bits)}</span>")
            else:
                parts.append(f"<span style='color:{C_SUBTEXT}'>⚪ {label} "
                             f"영향 미미</span>")
        header = (f"<span style='color:{C_SUBTEXT}'>🔬 활성 토글 영향 "
                  f"(현재 설정·고정 시드 단발 비교 — 이 토글을 끄면 이번 판이 어떻게 달라지나):"
                  f"</span><br>")
        lbl.setText(header + " &nbsp; ".join(parts))
        lbl.setVisible(True)
    def _lazy_start_optimize(self):
        """적정 편대 추천 탭 첫 방문 시 FleetRecommendWorker 기동 (lazy-start)."""
        if not hasattr(self, '_pending_cfg'):
            return
        opt = getattr(self, '_opt_worker', None)
        if opt and opt.isRunning():
            return
        self._optimize_placeholder()
        self._opt_worker = FleetRecommendWorker(self._pending_cfg)
        self._opt_worker.progress.connect(self._on_optimize_progress)
        self._opt_worker.finished.connect(self._on_optimize_done)
        self._opt_worker.error.connect(lambda e: self._optimize_error(e))
        self._opt_worker.start(QThread.Priority.LowPriority)
    def _optimize_placeholder(self):
        self.tab_optimize._loading_lbl.setText(
            "  적정 편대 추천 분석 중… (한국 단독·한미 연합 후보 편대 몬테카를로 평가) ⏳")
        self.tab_optimize._pane.setCurrentIndex(0)
    def _optimize_error(self, msg: str):
        self.tab_optimize._loading_lbl.setText(f"  적정 편대 추천 오류: {msg}")
    def _on_optimize_progress(self, done: int, total: int, group: str):
        grp_lbl = '한미 연합' if group == 'combined' else '한국 단독'
        self._lbl_status.setText(f"적정 편대 추천 분석 중 ({done}/{total}) — {grp_lbl} 평가")
    def _on_optimize_done(self, results: dict):
        self.tab_optimize.start_render(_render_fleet_chart, results)
        kr = results.get('kr') or []
        if kr:
            best = kr[0]
            self._lbl_status.setText(
                f"추천 편대(한국 단독): {best['preset']} — "
                f"요격률 {best['rate']:.1%}·생존율 {best['survival']:.0%}")
