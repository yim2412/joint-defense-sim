"""MainWindow mixin — 결과 내보내기(Excel·PDF 보고서).

app_main.py 분할 8/N (MainWindow mixin 분할). 의존은 PyQt6·matplotlib·app_theme·
app_engine뿐.
"""
import matplotlib.pyplot as plt
from PyQt6.QtWidgets import QFileDialog, QMessageBox

from app_engine import _V7_OK, save_excel_report_v7
from app_theme import C_ACCENT, C_SUBTEXT, C_TEXT


class ExportMixin:
    def _export_excel(self):
        """결과를 Excel 보고서로 저장."""
        if not _V7_OK or not self._result:
            QMessageBox.information(self, "안내", "먼저 시뮬레이션을 실행하세요.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Excel 보고서 저장", "report.xlsx", "Excel (*.xlsx)")
        if not path:
            return
        try:
            cfg = self._worker.cfg if self._worker else {}
            save_excel_report_v7(self._result, self._mc, cfg, path)
            QMessageBox.information(self, "저장 완료", f"Excel 보고서 저장:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "오류", str(e))
    def _export_pdf(self):
        """결과를 PDF 보고서로 저장 (matplotlib 다중 페이지)."""
        if not _V7_OK or not self._result:
            QMessageBox.information(self, "안내", "먼저 시뮬레이션을 실행하세요.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "PDF 보고서 저장", "report.pdf", "PDF (*.pdf)")
        if not path:
            return
        try:
            self._generate_pdf_report(path)
            QMessageBox.information(self, "저장 완료", f"PDF 보고서 저장:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "오류", str(e))
    def _generate_pdf_report(self, path: str):
        """matplotlib PdfPages로 다중 페이지 PDF 생성."""
        from matplotlib.backends.backend_pdf import PdfPages
        result = self._result
        mc     = self._mc
        cfg    = self._worker.cfg if self._worker else {}

        with PdfPages(path) as pdf:
            # 1페이지: 커버 + 핵심 지표
            fig, ax = plt.subplots(figsize=(11.7, 8.3))
            fig.patch.set_facecolor('#0a0e1a')
            ax.set_facecolor('#0a0e1a')
            ax.axis('off')
            lines = [
                ("합동 통합방어 시뮬레이터", 30, C_ACCENT, 'bold'),
                ("전투 분석 보고서", 20, C_TEXT, 'normal'),
                ("", 14, C_TEXT, 'normal'),
                (f"날씨: {cfg.get('weather', '—')}  |  "
                 f"적군: {cfg.get('enemy_fleet_preset', cfg.get('enemy_fleet_mode', '—'))}  |  "
                 f"MC: {mc.get('n', '—')}회", 12, C_SUBTEXT, 'normal'),
                ("", 12, C_TEXT, 'normal'),
                (f"요격률: {mc['mean_intercept']:.1%}  |  "
                 f"완전 요격: {mc.get('full_pass_rate', 0):.1%}  |  "
                 f"아군 피격: {result.get('friendly_hits', 0)}회", 14, '#2ecc71', 'bold'),
                (f"격추 비용: ${mc.get('mean_cost', 0):,.0f}  |  "
                 f"적 격침: {result.get('enemy_ships_destroyed', 0)}척", 14, C_TEXT, 'normal'),
            ]
            y = 0.85
            for text, size, color, weight in lines:
                ax.text(0.5, y, text, ha='center', va='top', color=color,
                        fontsize=size, fontweight=weight, transform=ax.transAxes)
                y -= 0.10
            pdf.savefig(fig, facecolor='#0a0e1a')
            plt.close(fig)

            # 2페이지: MC 통계 차트
            mc_bytes = getattr(self.tab_mc_canvas, '_raw_bytes', b'')
            if mc_bytes:
                import io as _io
                from matplotlib.image import imread as _mpl_imread
                fig2, ax2 = plt.subplots(figsize=(11.7, 8.3))
                fig2.patch.set_facecolor('#0a0e1a')
                ax2.set_facecolor('#0a0e1a')
                ax2.imshow(_mpl_imread(_io.BytesIO(mc_bytes)))
                ax2.axis('off')
                ax2.set_title('MC 통계', color=C_TEXT, fontsize=14, pad=10)
                pdf.savefig(fig2, facecolor='#0a0e1a')
                plt.close(fig2)

            # 3페이지: 비용 효과 + 탄약 소모
            fig3, axes3 = plt.subplots(1, 2, figsize=(11.7, 8.3))
            fig3.patch.set_facecolor('#0a0e1a')
            fig3.suptitle('비용 효과 / 탄약 소모', color=C_TEXT, fontsize=14)
            for ax3 in axes3:
                ax3.set_facecolor('#0a0e1a')

            # 비용 효과
            wpn_rem = mc.get('weapon_avg_remaining', {})
            if wpn_rem:
                wnames = list(wpn_rem.keys())
                wvals  = list(wpn_rem.values())
                axes3[0].barh(wnames, wvals, color=C_ACCENT, alpha=0.8)
                axes3[0].set_xlabel('평균 잔여 재고', color=C_SUBTEXT, fontsize=9)
                axes3[0].set_title('무기별 잔여 재고', color=C_TEXT, fontsize=10)
                axes3[0].tick_params(colors=C_SUBTEXT)
                for sp in axes3[0].spines.values(): sp.set_color('#1e2a3a')

            # 함정별 피격
            ship_hits = mc.get('ship_avg_hits', {})
            if ship_hits:
                snames = list(ship_hits.keys())
                svals  = list(ship_hits.values())
                cols   = ['#e74c3c' if v > 0.5 else '#2ecc71' for v in svals]
                axes3[1].bar(snames, svals, color=cols, alpha=0.8)
                axes3[1].set_ylabel('평균 피격 횟수', color=C_SUBTEXT, fontsize=9)
                axes3[1].set_title('함정별 평균 피격 (MC)', color=C_TEXT, fontsize=10)
                axes3[1].tick_params(colors=C_SUBTEXT, axis='x', rotation=15)
                for sp in axes3[1].spines.values(): sp.set_color('#1e2a3a')

            pdf.savefig(fig3, facecolor='#0a0e1a')
            plt.close(fig3)

            # 4페이지: 교전 로그 요약
            fig4, ax4 = plt.subplots(figsize=(11.7, 8.3))
            fig4.patch.set_facecolor('#0a0e1a')
            ax4.set_facecolor('#0a0e1a')
            ax4.axis('off')
            ax4.set_title('교전 로그 (최근 30건)', color=C_TEXT, fontsize=14, pad=10)
            log = result.get('log', [])[-30:]
            y = 0.95
            for t, msg in log:
                color = '#e74c3c' if '[피격]' in msg else (
                    '#2ecc71' if '[요격]' in msg else C_TEXT)
                ax4.text(0.02, y, f"[{t:>5.0f}s]  {msg[:90]}",
                         ha='left', va='top', color=color, fontsize=7,
                         transform=ax4.transAxes, fontfamily='monospace')
                y -= 0.03
                if y < 0.02:
                    break
            pdf.savefig(fig4, facecolor='#0a0e1a')
            plt.close(fig4)
