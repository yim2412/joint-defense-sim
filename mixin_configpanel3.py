"""MainWindow mixin - ConfigPanelMixin cfg restore + scenario preview cluster.

app_main.py split 9/N (mixin_configpanel size reduction for local-model context budget).
Deps: PyQt6, matplotlib, numpy, app_theme, app_engine, ui_widgets only.
"""
import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtWidgets import QFrame, QGroupBox, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from app_engine import V7_FLEET_PRESETS, V7_FRIENDLY_DB, V7_SHIP_DB, _V7_OK
from app_theme import C_BG, C_BORDER, C_PANEL, C_SUBTEXT, C_TEXT
from ui_widgets import _collapse_fleet_custom


class ConfigPanelExtra2Mixin:
    def _restore_cfg(self, cfg: dict):
        """실행 기록에서 설정을 복원한다 — 편대·날씨·적군 모드 복원."""
        # 아군 편대 — v16.14.02: 직접 편성이 저장돼 있으면 우선 복원, 없으면 프리셋 경로.
        custom = cfg.get('fleet_custom')
        if custom:
            self._fleet_custom = _collapse_fleet_custom(custom)
            self._apply_fleet_custom_label()
        else:
            self._clear_fleet_custom()
            fleet = cfg.get('fleet_preset', '')
            if fleet and hasattr(self, 'cmb_fleet'):
                idx = self.cmb_fleet.findText(fleet)
                if idx >= 0:
                    self.cmb_fleet.setCurrentIndex(idx)
        # 날씨
        weather = cfg.get('weather', '')
        if weather and hasattr(self, 'cmb_weather'):
            idx = self.cmb_weather.findText(weather)
            if idx >= 0:
                self.cmb_weather.setCurrentIndex(idx)
        # v9.12: 작전 해역
        region = cfg.get('fleet_region', '')
        if region and hasattr(self, 'cmb_region'):
            idx = self.cmb_region.findText(region)
            if idx >= 0:
                self.cmb_region.setCurrentIndex(idx)
        # v9.12: 계절 (v10.7: 4계절 확장)
        season = cfg.get('season', '')
        if season and hasattr(self, 'cmb_season'):
            _rmap = {'spring': '봄 (3~5월)', 'summer': '여름 (6~9월)',
                     'autumn': '가을 (10~11월)', 'winter': '겨울 (12~2월)'}
            target = _rmap.get(season, '여름 (6~9월)')
            idx = self.cmb_season.findText(target)
            if idx >= 0:
                self.cmb_season.setCurrentIndex(idx)
        # v9.12: 지형 음영
        if hasattr(self, 'chk_terrain'):
            self.chk_terrain.setChecked(cfg.get('enable_terrain', False))
        if hasattr(self, 'chk_current'):
            self.chk_current.setChecked(cfg.get('enable_current', False))
        # v9.13: 증발 덕팅
        if hasattr(self, 'chk_evap_duct'):
            self.chk_evap_duct.setChecked(cfg.get('enable_evap_duct', False))
        if hasattr(self, 'chk_anti_sam'):
            self.chk_anti_sam.setChecked(cfg.get('enable_anti_sam', False))
        if hasattr(self, 'chk_isa'):
            self.chk_isa.setChecked(cfg.get('enable_isa', False))
        if hasattr(self, 'chk_png'):
            self.chk_png.setChecked(cfg.get('enable_png', False))
        if hasattr(self, 'chk_sonar_eq'):
            self.chk_sonar_eq.setChecked(cfg.get('enable_sonar_equation', False))
        if hasattr(self, 'chk_flooding'):
            self.chk_flooding.setChecked(cfg.get('enable_flooding', False))
        if hasattr(self, 'chk_munition_limit'):
            self.chk_munition_limit.setChecked(cfg.get('enable_munition_limit', True))
        if hasattr(self, 'chk_battle'):
            self.chk_battle.setChecked(cfg.get('enable_battle_mode', False))
        if hasattr(self, 'chk_campaign'):
            self.chk_campaign.setChecked(cfg.get('enable_campaign_mode', False))
        if hasattr(self, 'chk_campaign_fog'):
            self.chk_campaign_fog.setChecked(cfg.get('enable_campaign_fog', False))
        if hasattr(self, 'chk_air_campaign'):
            self.chk_air_campaign.setChecked(cfg.get('enable_air_campaign', False))
        if hasattr(self, 'chk_precise_engage'):
            self.chk_precise_engage.setChecked(cfg.get('enable_precise_engagement', False))
        if hasattr(self, 'chk_sead'):
            self.chk_sead.setChecked(cfg.get('enable_sead', False))
        # v20.2b 지상 작전급(연안 방공망)
        if hasattr(self, 'chk_army_campaign'):
            self.chk_army_campaign.setChecked(cfg.get('enable_army_campaign', False))
        if hasattr(self, 'chk_joint_fires'):   # v21.2 합동 화력 지원
            self.chk_joint_fires.setChecked(cfg.get('enable_joint_fires', False))
        if hasattr(self, 'chk_joint_report'):   # v21.4 통합 보고서(군별 기여도)
            self.chk_joint_report.setChecked(cfg.get('enable_joint_report', False))
        if hasattr(self, 'cmb_joint_mode'):
            self.cmb_joint_mode.setCurrentText(
                '동시 공격' if cfg.get('joint_fire_mode') == 'simultaneous' else '시차 공격')
        if hasattr(self, 'cmb_army_fire') and cfg.get('army_fire_preset'):
            self.cmb_army_fire.setCurrentText(cfg['army_fire_preset'])
        if hasattr(self, 'chk_coastal_sam'):
            self.chk_coastal_sam.setChecked(cfg.get('enable_coastal_sam', False))
        if hasattr(self, 'cmb_coastal_preset') and cfg.get('coastal_sam_preset'):
            self.cmb_coastal_preset.setCurrentText(cfg['coastal_sam_preset'])
        if hasattr(self, 'chk_amphibious'):
            self.chk_amphibious.setChecked(cfg.get('enable_amphibious', False))
        if hasattr(self, 'chk_enemy_sead'):
            self.chk_enemy_sead.setChecked(cfg.get('enable_enemy_sead', False))
        if hasattr(self, 'cmb_amphib_zone') and cfg.get('amphib_zone'):
            self.cmb_amphib_zone.setCurrentText(cfg['amphib_zone'])
        if hasattr(self, 'chk_strategic_strike'):
            self.chk_strategic_strike.setChecked(cfg.get('enable_strategic_strike', False))
        if hasattr(self, 'chk_rl_policy'):
            self.chk_rl_policy.setChecked(cfg.get('enable_rl_policy', False))
        if hasattr(self, 'chk_esm_arm'):
            self.chk_esm_arm.setChecked(cfg.get('enable_esm_arm', False))
        if hasattr(self, 'chk_target_difficulty'):
            # v18.05.07 기본 ON 승격 — 구버전 시나리오 파일(키 없음)도 정규 동작으로 로드
            self.chk_target_difficulty.setChecked(cfg.get('enable_target_difficulty', True))
        if hasattr(self, 'chk_sonar_emcon'):
            self.chk_sonar_emcon.setChecked(cfg.get('enable_sonar_emcon', False))
        if hasattr(self, 'chk_asw_contact_limit'):
            self.chk_asw_contact_limit.setChecked(cfg.get('enable_asw_contact_limit', False))
        if hasattr(self, 'chk_standoff_spawn'):
            # v18.05.11 기본 ON 승격 — 구버전 시나리오(키 없음)도 정규 동작으로 로드
            self.chk_standoff_spawn.setChecked(cfg.get('enable_standoff_spawn', True))
        if hasattr(self, 'chk_cyber'):
            self.chk_cyber.setChecked(cfg.get('enable_cyber_warfare', False))
        if hasattr(self, 'chk_hgv_glide'):
            self.chk_hgv_glide.setChecked(cfg.get('enable_hgv_glide', True))   # v20.5: 기본 ON 승격
        if hasattr(self, 'chk_asw_forward'):
            self.chk_asw_forward.setChecked(cfg.get('enable_asw_forward', False))
        if hasattr(self, 'chk_weather_dyn'):
            self.chk_weather_dyn.setChecked(cfg.get('enable_weather_dynamics', False))
        if hasattr(self, 'cmb_weather_trend'):
            idx = self.cmb_weather_trend.findText(cfg.get('weather_trend', '자동'))
            if idx >= 0:
                self.cmb_weather_trend.setCurrentIndex(idx)
        if hasattr(self, 'chk_iff'):
            self.chk_iff.setChecked(cfg.get('enable_iff', False))
        # v9.14: 해협 진입로
        strait_type = cfg.get('strait_type', '')
        if strait_type and hasattr(self, 'cmb_strait_type'):
            reverse = {'korea_west': '서수도 (서→동)',
                       'korea_east': '동수도 (동→서)',
                       'bilateral':  '양방향 협공'}
            label = reverse.get(strait_type, '')
            if label:
                idx = self.cmb_strait_type.findText(label)
                if idx >= 0:
                    self.cmb_strait_type.setCurrentIndex(idx)
        # 적군 모드 — preset / random / manual
        enemy_mode = cfg.get('enemy_fleet_mode', '')
        mode_reverse = {'preset': '프리셋', 'mixed': '혼합 시나리오', 'random': '랜덤'}
        mode_label = mode_reverse.get(enemy_mode, '')
        if mode_label and hasattr(self, 'cmb_enemy_mode'):
            idx = self.cmb_enemy_mode.findText(mode_label)
            if idx >= 0:
                self.cmb_enemy_mode.setCurrentIndex(idx)
        # 적군 프리셋
        enemy_preset = cfg.get('enemy_fleet_preset', '')
        if enemy_preset and hasattr(self, 'cmb_fleet_preset_e'):
            idx = self.cmb_fleet_preset_e.findText(enemy_preset)
            if idx >= 0:
                self.cmb_fleet_preset_e.setCurrentIndex(idx)
        # 전술 체크박스
        if hasattr(self, 'chk_cec'):
            self.chk_cec.setChecked(cfg.get('enable_cec', cfg.get('enable_cec_preassign', True)))
        if hasattr(self, 'chk_multibearing'):
            self.chk_multibearing.setChecked(cfg.get('enable_multibearing', False))
        if hasattr(self, 'chk_cec_jammed'):
            self.chk_cec_jammed.setChecked(cfg.get('enable_cec_jammed', False))
        if hasattr(self, 'chk_autonomous'):
            self.chk_autonomous.setChecked(cfg.get('enable_autonomous_engagement', False))
        if hasattr(self, 'chk_ras_rearm'):
            self.chk_ras_rearm.setChecked(cfg.get('enable_ras_rearm', False))
        if hasattr(self, 'chk_ship_evasion'):
            self.chk_ship_evasion.setChecked(cfg.get('enable_ship_evasion', True))  # v20.5: 기본 ON 승격
        if hasattr(self, 'chk_radar_off'):
            self.chk_radar_off.setChecked(cfg.get('enable_radar_off', True))
        if hasattr(self, 'chk_dmo'):
            self.chk_dmo.setChecked(cfg.get('enable_dmo', False))
        if hasattr(self, 'chk_coord_decep'):
            self.chk_coord_decep.setChecked(cfg.get('enable_coord_deception', False))
        if hasattr(self, 'chk_mine_threat'):
            self.chk_mine_threat.setChecked(cfg.get('enable_mine_threat', False))
        if hasattr(self, 'chk_minesweeping'):
            self.chk_minesweeping.setChecked(cfg.get('enable_minesweeping', False))
        if hasattr(self, 'chk_unmanned'):
            self.chk_unmanned.setChecked(cfg.get('enable_unmanned_assets', False))
        if hasattr(self, 'chk_drone_swarm'):
            self.chk_drone_swarm.setChecked(cfg.get('enable_drone_swarm', False))
        if hasattr(self, 'chk_laser_dew'):
            self.chk_laser_dew.setChecked(cfg.get('enable_laser_dew', False))
        # 항공 자산 복원
        for attr, key in [('chk_helo','enable_helo'),('chk_p3c','enable_p3c'),
                          ('chk_p8a','enable_p8a'),('chk_f35a','enable_f35a'),
                          ('chk_kf21','enable_kf21'),('chk_fa50','enable_fa50'),
                          ('chk_recon','enable_recon_drone')]:
            if hasattr(self, attr):
                getattr(self, attr).setChecked(cfg.get(key, False))
        # 공격 임무·BMD 자산 복원 — 체크박스는 있으나 복원이 누락돼 있던 3종(감사 자동검사로 발견)
        for attr, key, dflt in [('chk_strike', 'enable_strike', True),
                                ('chk_thaad',  'enable_thaad',  False),
                                ('chk_ashore', 'enable_ashore', False),
                                ('chk_lsam',     'enable_lsam',     False),
                                ('chk_chungung', 'enable_chungung', False),
                                ('chk_patriot',  'enable_patriot',  False),
                                ('chk_bal_descent', 'enable_ballistic_descent', True)]:   # v20.5: 기본 ON 승격
            if hasattr(self, attr):
                getattr(self, attr).setChecked(cfg.get(key, dflt))
        # 전술 모드·적/AI 전술·난이도·혼합 시나리오 복원 — 빌드엔 있으나 복원 누락됐던 5종(로직 감사 발견, 재현성)
        if hasattr(self, 'chk_tactical'):
            self.chk_tactical.setChecked(cfg.get('tactical_mode', False))
        if hasattr(self, 'cmb_difficulty') and cfg.get('enemy_fleet_difficulty'):
            self.cmb_difficulty.setCurrentText(cfg['enemy_fleet_difficulty'])
        if hasattr(self, 'cmb_mixed_scenario') and cfg.get('mixed_scenario'):
            self.cmb_mixed_scenario.setCurrentText(cfg['mixed_scenario'])
        if hasattr(self, 'cmb_enemy_tactics'):
            self.cmb_enemy_tactics.setCurrentText(
                {None: '없음', 'v_formation': 'V자 대형', 'encirclement': '포위 기동'}
                .get(cfg.get('enemy_tactics'), '없음'))
        if hasattr(self, 'cmb_ai_tactic'):
            self.cmb_ai_tactic.setCurrentText(
                {None: '없음', 'saturation': '채널 포화', 'stagger': '시차 공격',
                 'exploit_weakness': '약점 공략', 'adaptive': '적응형(자동)'}
                .get(cfg.get('ai_tactic'), '없음'))
        self._lbl_status.setText("✅ 설정 복원 완료")


    def _build_scenario_preview(self) -> QWidget:
        """실행 전 시나리오 개요: 방어권역 다이어그램 + 편대·환경·무장 요약."""
        w = QWidget()
        w.setStyleSheet(f"background:{C_BG};")
        outer = QVBoxLayout(w)
        outer.setContentsMargins(16, 12, 16, 12)
        outer.setSpacing(10)

        hdr = QHBoxLayout()
        t = QLabel("  방어권역 개요")
        t.setStyleSheet(f"color:{C_TEXT}; font-size:14px; font-weight:bold; letter-spacing:1px;")
        hdr.addWidget(t)
        hdr.addStretch()
        hint = QLabel("시뮬레이션을 실행하면 결과가 표시됩니다")
        hint.setStyleSheet(f"color:{C_SUBTEXT}; font-size:12px; font-style:italic;")
        hdr.addWidget(hint)
        outer.addLayout(hdr)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color:{C_BORDER};")
        outer.addWidget(sep)

        body = QHBoxLayout()
        body.setSpacing(16)

        self._preview_fig = Figure(facecolor=C_BG)
        self._preview_canvas = FigureCanvas(self._preview_fig)
        self._preview_canvas.setMinimumSize(320, 280)
        body.addWidget(self._preview_canvas, stretch=3)

        right = QVBoxLayout()
        right.setSpacing(8)
        self._prev_lbl_fleet = self._make_prev_card(right, "🛥  아군 편대", "—")
        self._prev_lbl_env   = self._make_prev_card(right, "🌤  교전 환경", "—")
        self._prev_lbl_wpn   = self._make_prev_card(right, "🚀  대공 무장", "—")

        guide = QGroupBox()
        guide.setStyleSheet(
            f"QGroupBox {{ background:#162416; border:1px solid #2a4a2a;"
            f" border-radius:6px; padding:8px; }}")
        gl = QVBoxLayout(guide)
        gl.setSpacing(4)
        for line in [
            "설정을 확인한 뒤 시뮬레이션을 실행하세요.",
            "MC 분석: 10,000회 반복으로 통계 신뢰도 확보.",
            "CVaR은 최악 5% 시나리오의 평균 요격률입니다.",
        ]:
            ql = QLabel(line)
            ql.setWordWrap(True)
            ql.setStyleSheet(f"color:#4caf50; font-size:11px;")
            gl.addWidget(ql)
        right.addWidget(guide)
        right.addStretch()

        body.addLayout(right, stretch=2)
        outer.addLayout(body, stretch=1)
        return w
    def _make_prev_card(self, layout: QVBoxLayout, title: str, value: str) -> QLabel:
        card = QGroupBox()
        card.setStyleSheet(
            f"QGroupBox {{ background:{C_PANEL}; border:1px solid {C_BORDER};"
            f" border-radius:6px; padding:6px; }}")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(8, 4, 8, 6)
        cl.setSpacing(3)
        t_lbl = QLabel(title)
        t_lbl.setStyleSheet(f"color:{C_SUBTEXT}; font-size:10px; font-weight:bold;")
        cl.addWidget(t_lbl)
        v_lbl = QLabel(value)
        v_lbl.setWordWrap(True)
        v_lbl.setStyleSheet(f"color:{C_TEXT}; font-size:12px; line-height:160%;")
        cl.addWidget(v_lbl)
        layout.addWidget(card)
        return v_lbl
    def _update_scenario_preview(self):
        """방어권역 다이어그램 및 요약 카드를 현재 설정으로 갱신."""
        if not hasattr(self, '_preview_fig') or not hasattr(self, '_preview_canvas'):
            return
        import matplotlib.patches as _mp

        fleet_name = self.cmb_fleet.currentText()   if hasattr(self, 'cmb_fleet')   else '—'
        region     = self.cmb_region.currentText()  if hasattr(self, 'cmb_region')  else '—'
        weather    = self.cmb_weather.currentText() if hasattr(self, 'cmb_weather') else '—'
        season     = self.cmb_season.currentText()  if hasattr(self, 'cmb_season')  else '—'

        # ── 다이어그램 ──────────────────────────────────────────────────────
        fig = self._preview_fig
        fig.clear()
        ax = fig.add_axes([0.0, 0.0, 1.0, 1.0])
        ax.set_facecolor('#0d1117')
        ax.set_aspect('equal')

        # 방어 레이어 (시각 반지름 / 실제 km 표기)
        layers = [
            (185, '#1565c0', 0.10, '#5b9bd5', 'SM-6  370 km'),
            (130, '#1a6b3a', 0.16, '#4caf50', 'SM-2  170 km'),
            ( 70, '#7b5a00', 0.22, '#f39c12', 'ESSM/해궁  50 km'),
            ( 22, '#7b1500', 0.38, '#e74c3c', 'CIWS  9 km'),
        ]
        for r, fc, fa, lc, label in layers:
            ax.add_patch(_mp.Circle((0, 0), r, color=fc, fill=True, alpha=fa))
            ax.add_patch(_mp.Circle((0, 0), r, color=lc, fill=False,
                                     linewidth=1.2, linestyle='--', alpha=0.7))
            ax.text(r * 0.695 + 3, r * 0.695 + 3, label,
                    color=lc, fontsize=7.5, alpha=0.9, ha='left', va='bottom')

        ax.scatter([0], [0], marker='^', s=110, color='white', zorder=10)
        ax.text(0, -10, '기동전단', color='white', ha='center', va='top', fontsize=9)

        _dirs = {
            '동해 북부': [330, 0, 30],
            '동해':      [0, 30, 60],
            '황해':      [240, 270, 300],
            '남해':      [160, 200, 240],
            '독도':      [300, 330, 0],
            '대한해협':  [220, 260, 300, 340],
        }
        for deg in _dirs.get(region, [0, 90, 180, 270]):
            rad = np.radians(90 - deg)
            cx, cy = np.cos(rad), np.sin(rad)
            ax.annotate('',
                xy=(cx * 195, cy * 195), xytext=(cx * 215, cy * 215),
                arrowprops=dict(arrowstyle='->', color='#e74c3c', lw=1.8, alpha=0.8))

        for ang, lbl in [(90, 'N'), (0, 'E'), (-90, 'S'), (180, 'W')]:
            r = np.radians(ang)
            ax.text(np.cos(r) * 228, np.sin(r) * 228, lbl,
                    color='#555e6b', ha='center', va='center', fontsize=9, alpha=0.7)

        ax.set_xlim(-240, 240)
        ax.set_ylim(-240, 240)
        ax.axis('off')
        self._preview_canvas.draw()

        # ── 요약 카드 ───────────────────────────────────────────────────────
        if _V7_OK and fleet_name in V7_FLEET_PRESETS:
            ship_list = V7_FLEET_PRESETS[fleet_name]   # list of {'name':..,'type':..}
            total = len(ship_list)
            lines = [f"{s['name']}  ({s['type']})" for s in ship_list]
            self._prev_lbl_fleet.setText(f"{fleet_name}  ({total}척)\n" + '\n'.join(lines[:6]))
        else:
            self._prev_lbl_fleet.setText('—')

        self._prev_lbl_env.setText(
            f"날씨:  {weather}\n계절:  {season}\n해역:  {region}")

        # 대공 무장: 편대 내 모든 함정의 default_inventory 합산
        wpn_lines = []
        if _V7_OK and fleet_name in V7_FLEET_PRESETS:
            aa_total: dict[str, int] = {}
            for s in V7_FLEET_PRESETS[fleet_name]:
                stype = s.get('type', '')
                if stype in V7_SHIP_DB:
                    inv = V7_SHIP_DB[stype].get('default_inventory', {})
                    for k, v in inv.items():
                        if k in V7_FRIENDLY_DB and '대공' in V7_FRIENDLY_DB[k].get('category', []):
                            aa_total[k] = aa_total.get(k, 0) + v
            for k, v in list(aa_total.items())[:5]:
                rng = V7_FRIENDLY_DB[k].get('range_km', 0)
                wpn_lines.append(f"{k}  {v}발  ({rng} km)")
        self._prev_lbl_wpn.setText('\n'.join(wpn_lines) if wpn_lines else '—')

