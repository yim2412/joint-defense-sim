"""MainWindow mixin — 설정 패널(시나리오·편대·cfg 빌드/복원·예보 카드·툴팁).

app_main.py 분할 8/N (MainWindow mixin 분할). 의존은 PyQt6·matplotlib·numpy·app_theme·
app_utils·app_engine·ui_dialogs·ui_widgets·scenarios뿐.
"""
import os

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QButtonGroup, QCheckBox, QComboBox, QDialog, QFileDialog, QFormLayout,
    QFrame, QGridLayout, QGroupBox, QHBoxLayout, QLabel, QMessageBox,
    QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

from app_engine import (
    ARMY_FIRE_PRESETS, COASTAL_SAM_PRESETS, SLOC_ZONES, V7_ENEMY_DB,
    V7_ENEMY_FLEET_PRESETS, V7_FLEET_PRESETS, V7_FRIENDLY_DB,
    V7_MIXED_SCENARIOS, V7_RANDOM_CFG, V7_SHIP_DB, WEATHER_DB,
    _V7_ERR, _V7_OK, _forecast_featurize,
)
from app_theme import (
    C_ACCENT, C_BG, C_BORDER, C_PANEL, C_RED, C_SUBTEXT, C_TEXT, _wire_chk_color,
)
from app_utils import _load_app_state
from scenarios import SCENARIO_LIBRARY
from ui_dialogs import FleetCustomDialog
from ui_widgets import (
    NoScrollComboBox, NoScrollSpinBox, _CfgSectionHeader, _HoverPopup,
    _collapse_fleet_custom, _expand_fleet_custom, _install_hover,
    _install_section_popups,
)


class ConfigPanelMixin:
    def _build_setup_page(self) -> QWidget:
        """전체 화면 설정 페이지 (실행 전).
        상단(1/3): 5칸 — 아군편대·적군+시나리오·날씨계절·해역·시뮬모드+실행
        하단(2/3): 4칸 — 환경·방어전술·항공자산·고급
        """
        page = QWidget()
        page.setStyleSheet(f"background:{C_BG};")
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── 최상단 네비게이션: 쇼케이스 진입 ───────────────────────────
        nav = QWidget()
        nav.setStyleSheet(f"background:{C_PANEL}; border-bottom:1px solid {C_BORDER};")
        nav_l = QHBoxLayout(nav)
        nav_l.setContentsMargins(8, 3, 8, 3)
        nav_l.addStretch()
        btn_quickstart = QPushButton("🚀  추천 시나리오")
        btn_quickstart.setToolTip("처음 사용자를 위한 추천 상황 — 원클릭으로 함정·위협·해역·날씨를 일괄 설정")
        btn_quickstart.setFixedHeight(26)
        btn_quickstart.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_quickstart.setStyleSheet(
            f"QPushButton {{ background:{C_ACCENT}; color:#0b1220; border:none;"
            f" border-radius:4px; padding:0 12px; font-size:12px; font-weight:bold; }}"
            f"QPushButton:hover {{ background:#4db8ff; }}"
        )
        btn_quickstart.clicked.connect(lambda: self._toggle_quickstart_banner())
        nav_l.addWidget(btn_quickstart)
        btn_showcase = QPushButton("🎬  실험적 기능 쇼케이스")
        btn_showcase.setToolTip("실험적 기능의 효과를 미리 정의된 시나리오로 확인 + ON/OFF 실측 비교")
        btn_showcase.setFixedHeight(26)
        btn_showcase.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_showcase.setStyleSheet(
            f"QPushButton {{ background:#1f2d40; color:{C_ACCENT}; border:1px solid {C_BORDER};"
            f" border-radius:4px; padding:0 12px; font-size:12px; font-weight:bold; }}"
            f"QPushButton:hover {{ background:#26364d; color:{C_TEXT}; }}"
        )
        btn_showcase.clicked.connect(lambda: self._main_stack.setCurrentIndex(2))
        nav_l.addWidget(btn_showcase)
        outer.addWidget(nav)

        # ── 온보딩 배너: 추천 시나리오 원클릭 (v16.13.03) ────────────────
        # 처음 사용자가 "뭘 눌러야 할지" 모르는 이탈을 막는다. 기존 SCENARIO_LIBRARY
        # 를 눈에 띄는 배너로 승격해 원클릭 로드. 한 번 접으면 다음 실행부터 숨김.
        self._quickstart_banner = self._build_quickstart_banner()
        outer.addWidget(self._quickstart_banner)
        _qs_hidden = bool(_load_app_state().get('quickstart_banner_hidden', False))
        self._quickstart_banner.setVisible(not _qs_hidden)

        # ── 상단 바: 5칸 (전체 높이의 1/3) ─────────────────────────────
        top_bar = QWidget()
        top_bar.setStyleSheet(
            f"background:{C_PANEL}; border-bottom:2px solid {C_BORDER};")
        tbl = QHBoxLayout(top_bar)
        tbl.setContentsMargins(0, 0, 0, 0)
        tbl.setSpacing(0)

        top_labels = ["아군 편대", "적군 편대", "시나리오", "날씨 / 계절", "해역"]
        self._setup_top_cells: list = []
        for i, lbl_txt in enumerate(top_labels):
            cell = QWidget()
            cell.setStyleSheet(f"background:{C_PANEL};")
            cl = QVBoxLayout(cell)
            cl.setContentsMargins(0, 0, 0, 0)
            cl.setSpacing(0)

            hdr = QLabel(f"  {lbl_txt}")
            hdr.setFixedHeight(26)
            hdr.setStyleSheet(
                f"background:#1a2332; color:{C_ACCENT}; "
                f"font-size:11px; font-weight:bold; letter-spacing:1px; "
                f"border-bottom:1px solid {C_BORDER};")
            cl.addWidget(hdr)

            # 콘텐츠 홀더 — 스크롤 영역 안에 배치
            holder = QWidget()
            holder.setStyleSheet(f"background:{C_PANEL};")
            hl = QVBoxLayout(holder)
            hl.setContentsMargins(6, 6, 6, 6)
            hl.setSpacing(4)
            hl.addStretch()

            sc = QScrollArea()
            sc.setWidgetResizable(True)
            sc.setWidget(holder)
            sc.setStyleSheet(f"QScrollArea {{ border:none; background:{C_PANEL}; }}")
            sc.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            cl.addWidget(sc, stretch=1)

            self._setup_top_cells.append(holder)
            tbl.addWidget(cell, stretch=1)

            if i < len(top_labels) - 1:
                sep = QFrame()
                sep.setFrameShape(QFrame.Shape.VLine)
                sep.setStyleSheet(f"QFrame {{ color:{C_BORDER}; }}")
                sep.setFixedWidth(1)
                tbl.addWidget(sep)

        outer.addWidget(top_bar, stretch=1)

        # ── 하단: 4칸 (전체 높이의 2/3) ─────────────────────────────────
        split_w = QWidget()
        split_w.setStyleSheet(f"background:{C_BG};")
        split_layout = QHBoxLayout(split_w)
        split_layout.setContentsMargins(0, 0, 0, 0)
        split_layout.setSpacing(0)

        self._setup_col_pages: list = []
        col_names = ["환경", "방어전술", "항공자산", "고급"]
        for i, name in enumerate(col_names):
            col_frame = QWidget()
            col_frame.setStyleSheet(f"background:{C_BG};")
            cfl = QVBoxLayout(col_frame)
            cfl.setContentsMargins(0, 0, 0, 0)
            cfl.setSpacing(0)

            hdr = QLabel(f"  {name}")
            hdr.setFixedHeight(30)
            hdr.setStyleSheet(
                f"background:#1a2332; color:{C_ACCENT}; "
                f"font-size:12px; font-weight:bold; letter-spacing:2px; "
                f"border-bottom:2px solid {C_ACCENT};")
            cfl.addWidget(hdr)

            inner = QWidget()
            inner.setStyleSheet(f"background:{C_BG};")
            il = QVBoxLayout(inner)
            il.setContentsMargins(6, 6, 6, 6)
            il.setSpacing(4)
            il.addStretch()
            self._setup_col_pages.append(inner)

            sc = QScrollArea()
            sc.setWidgetResizable(True)
            sc.setWidget(inner)
            sc.setStyleSheet(f"QScrollArea {{ border:none; background:{C_BG}; }}")
            sc.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            cfl.addWidget(sc)

            split_layout.addWidget(col_frame, stretch=1)

            if i < len(col_names) - 1:
                sep = QFrame()
                sep.setFrameShape(QFrame.Shape.VLine)
                sep.setStyleSheet(f"QFrame {{ color:{C_BORDER}; }}")
                sep.setFixedWidth(1)
                split_layout.addWidget(sep)

        outer.addWidget(split_w, stretch=2)

        # ── 실행 버튼 홀더 (설정 모드 전용, _cfg_bottom이 이동해 옴) ─────
        self._setup_run_holder = QWidget()
        self._setup_run_holder.setStyleSheet(
            f"background:{C_PANEL}; border-top:2px solid {C_ACCENT};")
        _srhl = QVBoxLayout(self._setup_run_holder)
        _srhl.setContentsMargins(0, 0, 0, 0)
        _srhl.setSpacing(0)
        outer.addWidget(self._setup_run_holder)

        return page
    def _open_fleet_custom(self):
        """직접 편성 다이얼로그를 열어 아군 함대를 구성한다."""
        dlg = FleetCustomDialog(getattr(self, '_fleet_custom', None), self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            counts = dlg.get_counts()
            if counts:
                self._fleet_custom = counts
                self._apply_fleet_custom_label()
                self._update_forecast_card()
    def _clear_fleet_custom(self):
        """직접 편성 해제 → 프리셋 모드 복귀."""
        if getattr(self, '_fleet_custom', None) is not None:
            self._fleet_custom = None
            if hasattr(self, '_lbl_fleet_custom'):
                self._lbl_fleet_custom.hide()
            self._update_forecast_card()
    def _apply_fleet_custom_label(self):
        """직접 편성 상태 레이블 갱신."""
        counts = getattr(self, '_fleet_custom', None)
        if not counts or not hasattr(self, '_lbl_fleet_custom'):
            return
        n = sum(counts.values())
        self._lbl_fleet_custom.setText(f"✏️ 직접 편성 적용 중 ({n}척)")
        self._lbl_fleet_custom.show()
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
    def _on_scenario_changed(self, name: str):
        """시나리오 선택 시 적용 버튼 활성화."""
        self.btn_apply_scenario.setEnabled(bool(SCENARIO_LIBRARY.get(name)))
    def _apply_scenario(self):
        """선택한 시나리오 설정을 UI에 일괄 적용 (편대·해역·날씨·계절·적 편대)."""
        name = self.cmb_scenario.currentText()
        sc = SCENARIO_LIBRARY.get(name)
        if not sc:
            return
        self._restore_cfg(sc['cfg'])
        self._lbl_status.setText(f"🎯 '{name}' 시나리오 적용 완료")
    def _build_config_panel(self) -> QWidget:
        container = QWidget()
        container.setFixedWidth(430)
        container.setStyleSheet(f"background: {C_PANEL};")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"QScrollArea {{ border: none; background: {C_PANEL}; }}")

        inner = QWidget()
        inner.setStyleSheet(f"background: {C_PANEL};")
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        def _make_content(*groups) -> QWidget:
            w = QWidget()
            w.setStyleSheet(f"background:{C_PANEL};")
            cl = QVBoxLayout(w)
            cl.setContentsMargins(4, 4, 4, 8)
            cl.setSpacing(5)
            for g in groups:
                cl.addWidget(g)
            return w

        # ── 공통 스타일 ───────────────────────────────────────────────────
        _LIST_SS = f"""
            QListWidget {{
                background:#1c2128; color:{C_TEXT};
                border:1px solid {C_BORDER}; border-radius:3px;
                font-size:13px; outline:none;
            }}
            QListWidget::item {{ padding:3px 8px; }}
            QListWidget::item:selected {{ background:{C_ACCENT}; color:white; }}
            QListWidget::item:hover:!selected {{ background:#1f2d40; }}
        """
        _TOG_SS = f"""
            QPushButton {{
                background:{C_BG}; color:{C_SUBTEXT};
                border:1px solid {C_BORDER}; border-radius:8px;
                font-size:12px; padding:5px 4px;
            }}
            QPushButton:checked {{ background:{C_ACCENT}; color:white; border:1px solid {C_ACCENT}; }}
            QPushButton:hover:!checked {{ background:#1f2d40; color:{C_TEXT}; }}
        """
        def _cell_widget():
            w = QWidget(); w.setStyleSheet(f"background:{C_PANEL};")
            l = QVBoxLayout(w); l.setContentsMargins(8,8,8,8); l.setSpacing(6)
            return w, l
        def _sec_label(txt):
            l = QLabel(txt)
            l.setStyleSheet(f"color:{C_SUBTEXT}; font-size:11px; font-weight:bold;")
            return l

        # ── 아군 편대 — 2열 버튼 그리드 ─────────────────────────────────
        _fleet, _ffl = _cell_widget()
        self.cmb_fleet = NoScrollComboBox()           # 하위 호환용 숨김 콤보
        self.cmb_fleet.addItems(list(V7_FLEET_PRESETS.keys()) if _V7_OK else [])
        if _V7_OK:
            for _i, _n in enumerate(V7_FLEET_PRESETS.keys()):
                self.cmb_fleet.setItemData(_i, self._friendly_preset_tooltip(_n),
                                           Qt.ItemDataRole.ToolTipRole)
        self.cmb_fleet.hide()

        _fleet_names = list(V7_FLEET_PRESETS.keys()) if _V7_OK else []
        _fleet_bg = QButtonGroup(self); _fleet_bg.setExclusive(True)
        _fleet_grid_w = QWidget(); _fgrid = QGridLayout(_fleet_grid_w)
        _fgrid.setContentsMargins(0,0,0,0); _fgrid.setSpacing(3)
        _fleet_popup = _HoverPopup(self)
        for _i, _n in enumerate(_fleet_names):
            _b = QPushButton(_n); _b.setCheckable(True)
            _b.setStyleSheet(_TOG_SS); _b.setFixedHeight(26)
            _tip = self._friendly_preset_tooltip(_n) if _V7_OK else ""
            _install_hover(_b, _tip, _fleet_popup)
            if _i == 0: _b.setChecked(True)
            _fleet_bg.addButton(_b, _i)
            _fgrid.addWidget(_b, _i // 2, _i % 2)
        _fleet_bg.idClicked.connect(self.cmb_fleet.setCurrentIndex)
        # 프리셋 버튼을 누르면 직접 편성 모드 해제
        _fleet_bg.idClicked.connect(lambda _i: self._clear_fleet_custom())
        self.cmb_fleet.currentIndexChanged.connect(
            lambda i: _fleet_bg.button(i).setChecked(True) if _fleet_bg.button(i) else None)
        _ffl.addWidget(_fleet_grid_w)

        # ── v16.14.02: 직접 편성 진입 ────────────────────────────────────
        self._fleet_custom = None   # {type:count} 또는 None(=프리셋 모드)
        _btn_custom = QPushButton("✏️ 직접 편성…"); _btn_custom.setFixedHeight(24)
        _btn_custom.setStyleSheet(
            f"QPushButton {{ background:transparent; color:{C_ACCENT}; border:1px dashed #30363d; "
            f"border-radius:6px; font-size:11px; padding:2px; }} "
            f"QPushButton:hover {{ border-color:{C_ACCENT}; }}")
        _btn_custom.clicked.connect(self._open_fleet_custom)
        _ffl.addWidget(_btn_custom)
        self._lbl_fleet_custom = QLabel("")
        self._lbl_fleet_custom.setStyleSheet(
            f"color:{C_ACCENT}; font-size:11px; font-weight:bold;")
        self._lbl_fleet_custom.hide()
        _ffl.addWidget(self._lbl_fleet_custom)
        self._fleet_btn_group = _fleet_bg

        _ffl.addStretch()
        self._cfg_fleet = _fleet

        # ── 날씨 / 계절 — 리스트 + 토글 버튼 ────────────────────────────
        _wx, _wxl = _cell_widget()
        self.cmb_weather = NoScrollComboBox()          # 하위 호환용 숨김 콤보
        self.cmb_weather.addItems(list(WEATHER_DB.keys()) if _V7_OK else [])
        self.cmb_weather.hide()

        _wxl.addWidget(_sec_label("날씨"))
        _wx_names = list(WEATHER_DB.keys()) if _V7_OK else []
        _wx_popup_texts = {
            '맑음 (주간)':
                '☀️ 최상 전투 조건\n'
                '레이더 ×1.00  |  소나 ×1.00  |  요격 보정 ±0%\n'
                'C&D 지연 ×1.00  |  항공 출격 제한 없음\n\n'
                '전 무기체계가 교리 명세 성능으로 동작. 광학 표적 식별 가능.\n'
                '다른 기상과의 성능 비교 기준값(baseline).',
            '맑음 (야간)':
                '🌙 야간 작전 조건\n'
                '레이더 ×0.95  |  소나 ×0.98  |  요격 보정 −1%\n'
                'C&D 지연 ×1.05\n\n'
                '광학 표적 식별 불가 — IFF 판정 신뢰도 소폭 저하.\n'
                '레이더·소나 성능 경미하게 감소. 야간 항공 작전 가능.',
            '흐림 (박무)':
                '🌫️ 박무 조건\n'
                '레이더 ×0.90  |  소나 ×0.85  |  요격 보정 −3%\n'
                'C&D 지연 ×1.10\n\n'
                '해상 증발 소음 증가로 소나 탐지거리 15% 감소.\n'
                '레이더 수평선 감쇠 시작. 서해 봄·여름 빈발.',
            '황사 (봄철 황사)':
                '🟡 황사 조건 (봄철 3~5월)\n'
                '레이더 ×0.72  |  소나 ×1.00  |  요격 보정 −2%\n'
                'C&D 지연 ×1.10\n\n'
                '황사 입자가 레이더 전파를 흡수·산란 — 탐지거리 28% 감소.\n'
                '수중 소음에는 영향 없음. 서해·황해 봄철 대표 기상.',
            '풍랑 (7~8등급)':
                '🌊 강풍·풍랑 조건 (Beaufort 7~8)\n'
                '레이더 ×0.92  |  소나 ×0.60  |  요격 보정 −6%\n'
                'C&D 지연 ×1.20\n\n'
                '파고 5~7m. 해면 거품층이 소나 성능을 40% 이상 저하.\n'
                '함정 기동 제한, 헬기 대잠 작전 위험 증가.',
            '폭풍 (해상 악화)':
                '⛈️ 폭풍 조건 (Beaufort 9~10)\n'
                '레이더 ×0.55  |  소나 ×0.40  |  요격 보정 −8%\n'
                'C&D 지연 ×1.25\n\n'
                '파고 7~10m. 레이더 클러터 심각 — 저고도 표적 탐지 극히 어려움.\n'
                '함재 헬기 출격 제한, 대잠 전력 반감. 동해 겨울 폭풍.',
            '태풍 (9~12등급)':
                '🌀 태풍 조건 (Beaufort 11~12)\n'
                '레이더 ×0.62  |  소나 ×0.22  |  요격 보정 −15%\n'
                'C&D 지연 ×1.50\n\n'
                '파고 10m 이상. 소나 실질 무력화. 레이더 강우 감쇠 극심.\n'
                '항공 전면 운용 불가. 함정 안전 운항 우선. 여름 동해·남해 위협.',
            '농무 (시정 200m 이하)':
                '🌁 짙은 안개 (시정 200m 이하)\n'
                '레이더 ×0.80  |  소나 ×0.94  |  요격 보정 −3%\n'
                'C&D 지연 ×1.15\n\n'
                '시정 200m 미만 짙은 농무. 레이더 흡수·산란 심각.\n'
                '광학 시스템 완전 무력화. 서해 봄·겨울 황해 기단 영향.',
            '폭풍 (야간)':
                '🌩️ 야간 폭풍 복합 조건\n'
                '레이더 ×0.52  |  소나 ×0.40  |  요격 보정 −10%\n'
                'C&D 지연 ×1.35\n\n'
                '폭풍 + 야간 복합 악조건. 레이더·광학 모두 저하.\n'
                '교전 채널 반감, 대잠 전력 극도 제한. 최악 수준 전투 환경.',
            '태풍 (야간)':
                '🌀🌙 야간 태풍 — 최악 기상\n'
                '레이더 ×0.59  |  소나 ×0.22  |  요격 보정 −17%\n'
                'C&D 지연 ×1.60\n\n'
                '전 센서 계통 최대 저하. 교전 능력 극한 제한.\n'
                '도발 대응 시 이지스 함대 생존성 검증 최악 시나리오.',
            '농무 (야간)':
                '🌁🌙 야간 농무 복합 조건\n'
                '레이더 ×0.76  |  소나 ×0.94  |  요격 보정 −5%\n'
                'C&D 지연 ×1.20\n\n'
                '야간 + 짙은 안개. 광학 완전 불가, 레이더에 전적 의존.\n'
                '레이더도 24% 저하 — 표적 식별 지연 심화.',
            '황사 (새벽)':
                '🌅 새벽 황사 조건\n'
                '레이더 ×0.70  |  소나 ×1.00  |  요격 보정 −3%\n'
                'C&D 지연 ×1.10\n\n'
                '봄철 새벽 황사 + 저고도 안개 복합. 레이더 감쇠 심각.\n'
                '황해 봄철 전형적 기상. 야간보다 황사 영향이 지배적.',
        }
        _WX_SHORT = {'농무 (시정 200m 이하)': '농무 (200m↓)'}
        _wx_bg = QButtonGroup(self); _wx_bg.setExclusive(True)
        _wx_grid_w = QWidget(); _wgrid = QGridLayout(_wx_grid_w)
        _wgrid.setContentsMargins(0,0,0,0); _wgrid.setSpacing(3)
        _wx_popup = _HoverPopup(self)
        for _i, _wn in enumerate(_wx_names):
            _b = QPushButton(_WX_SHORT.get(_wn, _wn)); _b.setCheckable(True)
            _b.setStyleSheet(_TOG_SS); _b.setFixedHeight(26)
            _install_hover(_b, _wx_popup_texts.get(_wn, ''), _wx_popup)
            if _i == 0: _b.setChecked(True)
            _wx_bg.addButton(_b, _i)
            _wgrid.addWidget(_b, _i // 2, _i % 2)
        _wx_bg.idClicked.connect(self.cmb_weather.setCurrentIndex)
        self.cmb_weather.currentIndexChanged.connect(
            lambda i: _wx_bg.button(i).setChecked(True) if _wx_bg.button(i) else None)
        _wxl.addWidget(_wx_grid_w)

        self.cmb_season = NoScrollComboBox()           # 하위 호환용 숨김 콤보
        self.cmb_season.addItems(
            ['봄 (3~5월)', '여름 (6~9월)', '가을 (10~11월)', '겨울 (12~2월)'])
        self.cmb_season.setCurrentIndex(1)
        self.cmb_season.hide()

        _wxl.addWidget(_sec_label("계절"))
        _season_row = QWidget(); _srl = QHBoxLayout(_season_row)
        _srl.setContentsMargins(0,0,0,0); _srl.setSpacing(4)
        _season_bg = QButtonGroup(self)
        _season_bg.setExclusive(True)
        _season_popup = _HoverPopup(self)
        for _i, (_s, _tip) in enumerate([
            ('봄',
             '🌸 봄 (3~5월)\n'
             '수온약층: 약(초봄) → 중(5월)\n'
             '황사 시즌 — 레이더 감쇠 최대\n\n'
             '서해 안개 빈발, 황해 기단 황사 영향.\n'
             '잠수함 탐지: 중간(수온약층 형성 중).\n'
             'ISA 대기 굴절: 미약.'),
            ('여름',
             '☀️ 여름 (6~9월)\n'
             '수온약층: 최강 (계절 최고)\n'
             '태풍 시즌 — 최악 기상 위험\n\n'
             '수온약층 최강 → 소나 성능 가장 낮음.\n'
             'ISA 대기 굴절 최대 → 탐지거리 최대 +23%.\n'
             '여름 태풍은 작전 지속성에 최대 위협.'),
            ('가을',
             '🍂 가을 (10~11월)\n'
             '수온약층: 감소(10월) → 소멸(11월)\n'
             '제트기류 남하 — 황천 빈도 증가\n\n'
             '소나 성능 여름 대비 회복.\n'
             'ISA 대기 굴절: 중간 수준.\n'
             '북서 계절풍 시작, 동해·서해 풍랑 빈도↑.'),
            ('겨울',
             '❄️ 겨울 (12~2월)\n'
             '수온약층: 서해 소멸 / 동해 잔존\n'
             '대륙성 한기 — 북서 계절풍 강\n\n'
             '서해 소나 성능 최고(수온약층 소멸).\n'
             'ISA 굴절 감소, 트로포스캐터 비활성화 조건↑.\n'
             '북한 동계 도발 시즌. 함정 기동 제한(결빙·한랭).'),
        ]):
            _b = QPushButton(_s); _b.setCheckable(True)
            _b.setStyleSheet(_TOG_SS)
            _install_hover(_b, _tip, _season_popup)
            if _i == 1: _b.setChecked(True)
            _season_bg.addButton(_b, _i)
            _srl.addWidget(_b)
        _season_bg.idClicked.connect(self.cmb_season.setCurrentIndex)
        self.cmb_season.currentIndexChanged.connect(
            lambda i: _season_bg.button(i).setChecked(True)
            if _season_bg.button(i) else None)
        _wxl.addWidget(_season_row)
        _wxl.addStretch()
        self._cfg_weather = _wx

        # ── 해역 — 토글 버튼 + 특성 설명 ────────────────────────────────
        _reg, _regl = _cell_widget()
        self.cmb_region = NoScrollComboBox()           # 하위 호환용 숨김 콤보
        self.cmb_region.addItems(['동해 북부', '동해 중부', '서해', '대한해협'])
        self.cmb_region.hide()

        _region_info = {
            '동해 북부':
                '🌊 동해 북부 (울릉도·독도 북방)\n'
                '수심 평균 1,700m  |  최대 3,000m 이상\n'
                '북한한류 영향권  |  수온약층: 봄~가을 강\n'
                '레이더 음영: 태백·설악 최대 22% 탐지거리 감소\n\n'
                '북한 잠수함 주 활동 해역. 깊은 수심으로 잠수함 은닉 유리.\n'
                '동계 북서풍 강. 미 7함대 협력 해역.',
            '동해 중부':
                '🌊 동해 중부 (울릉도·독도 인근)\n'
                '수심 평균 2,000m  |  쓰시마 난류 주류\n'
                '수온약층: 여름 최강(6~9월)  |  레이더 음영: 약\n\n'
                '소나 성능: 여름 최저(수온약층 최강) / 겨울 최고.\n'
                '독도 방어 작전 기준 해역. 개방 해면으로 전술 기동 유리.',
            '서해':
                '🌊 서해 (황해)\n'
                '평균 수심 44m  |  최대 103m\n'
                '여름 냉수괴(YSCBW)  |  수온약층: 10m부터 형성\n'
                '레이더 음영: 낭림산맥 (미약)\n\n'
                '천해 환경 — 소나 탐지거리 급감(천해 잔향 지배).\n'
                '북한 NLL 도발 주 해역. 기뢰 위협 높음.',
            '대한해협':
                '🌊 대한해협 (쓰시마 해협)\n'
                '수심 평균 100m  |  폭 185km (서수도 49.5km)\n'
                '쓰시마 난류 통과  |  연중 수온약층 존재\n'
                '레이더 음영: 소백산맥 (중간 정도)\n\n'
                '협수로 — 위협 접근 방위 ±30° 제한, 기동 공간 좁음.\n'
                '잠수함 최대 잠항: 서수도 130m / 동수도 115m 자동 제한.\n'
                '서수도·동수도·양방향 협공 수도 선택 가능.',
        }
        _region_names = ['동해 북부', '동해 중부', '서해', '대한해협']

        _region_bg = QButtonGroup(self)
        _region_bg.setExclusive(True)
        _reg_grid = QWidget(); _rgl = QGridLayout(_reg_grid)
        _rgl.setContentsMargins(0,0,0,0); _rgl.setSpacing(4)
        _region_popup = _HoverPopup(self)
        for _i, _rn in enumerate(_region_names):
            _b = QPushButton(_rn); _b.setCheckable(True)
            _b.setStyleSheet(_TOG_SS)
            _install_hover(_b, _region_info[_rn], _region_popup)
            if _i == 0: _b.setChecked(True)
            _region_bg.addButton(_b, _i)
            _rgl.addWidget(_b, _i // 2, _i % 2)
        _regl.addWidget(_reg_grid)

        def _on_region_btn(idx):
            self.cmb_region.setCurrentText(_region_names[idx])
        _region_bg.idClicked.connect(_on_region_btn)
        self.cmb_region.currentTextChanged.connect(
            lambda t: _region_bg.button(_region_names.index(t)).setChecked(True)
            if t in _region_names else None)

        _regl.addStretch()
        self._cfg_region = _reg

        # 결과 사이드바용: 3개 위젯을 container_layout 앞에 쌓아 둠
        container_layout.addWidget(self._cfg_fleet)
        container_layout.addWidget(self._cfg_weather)
        container_layout.addWidget(self._cfg_region)

        # ── 작전 시나리오 (v11.5) ────────────────────────────────────────
        grp_sc = QGroupBox("🎯 작전 시나리오")
        scl = QVBoxLayout(grp_sc)
        scl.setSpacing(4)
        _sc_names = list(SCENARIO_LIBRARY.keys())
        _sc_items = ['— 선택 안 함 —'] + _sc_names
        self.cmb_scenario = NoScrollComboBox()         # 하위 호환용 숨김 콤보
        self.cmb_scenario.addItems(_sc_items)
        self.cmb_scenario.hide()

        _sc_bg = QButtonGroup(self); _sc_bg.setExclusive(True)
        _sc_grid = QWidget(); _sgl = QGridLayout(_sc_grid)
        _sgl.setContentsMargins(0,0,0,0); _sgl.setSpacing(3)
        _sc_popup = _HoverPopup(self)
        # "선택 안 함" 버튼
        _b0 = QPushButton('— 선택 안 함 —'); _b0.setCheckable(True); _b0.setChecked(True)
        _b0.setStyleSheet(_TOG_SS); _b0.setFixedHeight(26)
        _install_hover(_b0, '시나리오 없이 수동 설정 사용', _sc_popup)
        _sc_bg.addButton(_b0, 0)
        _sgl.addWidget(_b0, 0, 0, 1, 2)
        for _i, _sn in enumerate(_sc_names):
            _sc_d = SCENARIO_LIBRARY[_sn]
            _tip = f"{_sc_d.get('desc','')}\n\n권장: {_sc_d.get('recommend','')}"
            _b = QPushButton(_sn); _b.setCheckable(True)
            _b.setStyleSheet(_TOG_SS); _b.setFixedHeight(26)
            _install_hover(_b, _tip, _sc_popup)
            _sc_bg.addButton(_b, _i + 1)
            _sgl.addWidget(_b, (_i // 2) + 1, _i % 2)
        _sc_bg.idClicked.connect(self.cmb_scenario.setCurrentIndex)
        self.cmb_scenario.currentIndexChanged.connect(
            lambda i: _sc_bg.button(i).setChecked(True) if _sc_bg.button(i) else None)
        self.cmb_scenario.currentTextChanged.connect(self._on_scenario_changed)
        scl.addWidget(_sc_grid)
        self.btn_apply_scenario = QPushButton("▶ 시나리오 적용")
        self.btn_apply_scenario.setEnabled(False)
        self.btn_apply_scenario.clicked.connect(self._apply_scenario)
        scl.addWidget(self.btn_apply_scenario)

        # ── 환경 세부 옵션 ────────────────────────────────────────────────
        grp_env = QGroupBox("🌍 환경 세부 옵션")
        fl_env = QFormLayout(grp_env)
        fl_env.setSpacing(4)
        self.chk_terrain = QCheckBox("지형 음영 적용")
        self.chk_terrain.setToolTip(
            "해역별 산맥 레이더 차폐 효과 적용.\n"
            "동해: 태백·설악(3.4~8.1°) — 저고도 위협 탐지 최대 22% 감소\n"
            "서해: 낭림산맥 원거리(0.4°) — 미약 (~4%)\n"
            "대한해협: 소백산맥(0.9°) — 중간 (~10%)"
        )
        self.chk_terrain.setChecked(True)

        # v10.8: 해류 연동 (UI 미노출 — db_ocean_environment 필요)
        self.chk_current = QCheckBox("해류 연동  (db_ocean_environment 해류 벡터 적용)")
        self.chk_current.setChecked(False)
        self.chk_current.setToolTip(
            "v10.8 — 해역별 해류 벡터를 함정·잠수함 위치에 매 tick 누적.\n"
            "동해: 동한난류 북상 (여름 최강 50cm/s)\n"
            "서해: 황해 연안류 (여름 북향·겨울 남향)\n"
            "대한해협: 대마난류 북동향 (~35cm/s)\n"
            "db_ocean_environment.py가 있어야 활성화됩니다."
        )

        self.chk_evap_duct = QCheckBox("증발 덕팅 적용")
        self.chk_evap_duct.setToolTip(
            "대기 하층 수증기 농도 역전으로 레이더 전파가 해면을 따라 굴절.\n"
            "저고도 표적(해면밀착 대함미사일 등)의 탐지거리 증가 효과.\n"
            "동해 여름: EDH 10m, 탐지 ×1.25 / 동해 겨울: EDH 6m, ×1.12\n"
            "풍랑(BF7) 이상 강풍 시 덕트 파괴 → 자동 비활성화."
        )
        self.chk_evap_duct.setChecked(True)

        self.chk_anti_sam = QCheckBox("적 Anti-SAM 방어 적용 (종결 — 발동 안 함)")
        self.chk_anti_sam.setToolTip(
            "적 함정이 접근하는 아군 SAM을 CIWS·SAM으로 요격하는 로직.\n"
            "⚠ 종결: 아군 SAM은 대공 전용이라 적 함정을 조준하지 않습니다.\n"
            "따라서 요격 대상(적 함정을 향하는 아군 SAM)이 발생하지 않아\n"
            "이 옵션은 켜도 결과가 바뀌지 않습니다. 적 함정의 대함미사일\n"
            "방어는 '적 자체방어(CIWS·채프)' 옵션이 담당합니다."
        )
        self.chk_anti_sam.setChecked(False)

        self.chk_isa = QCheckBox("정밀 대기 모델 (ISA)")
        self.chk_isa.setToolTip(
            "v10.1 — ICAO 표준 대기 + 기상청 라디오존데 계절별 실측값 적용.\n"
            "중고도(≥500m) 표적: 대기 굴절 지수 증가로 탐지거리 +2~6%.\n"
            "고고도(≥1000m) 표적: 트로포스캐터 산란 추가 +7~16%.\n"
            "  예) 동해 여름 탄도미사일(고도10km): 탐지거리 최대 ×1.23\n"
            "  예) 동해 겨울 순항미사일(고도500m): ×1.03\n"
            "풍랑(BF6) 이상 강풍 시 트로포스캐터 자동 비활성화."
        )
        self.chk_isa.setChecked(True)

        # v12.1: 비례항법(PNG) 종말 유도
        self.chk_png = QCheckBox("비례항법(PNG) 종말 유도")
        self.chk_png.setToolTip(
            "v12.1 — 함대공 미사일이 비례항법으로 회피 기동하는 적 대함미사일을\n"
            "종말 10km 구간에서 물리적으로 추격합니다.\n"
            "기동 한계(함대공 30G·대함 10G)와 탐색기 시야각(±60°)이 추격을 제약 —\n"
            "급격히 회피하는 표적은 요격이 물리적으로 빗나갈 수 있습니다.\n"
            "기존의 종말 회피 확률 보정을 물리 추격 명중/빗나감으로 대체합니다.\n"
            "기본값 OFF — 기존 결과와 동일 (검증 완료·정규 옵션)"
        )
        self.chk_png.setChecked(False)

        # v12.3: dB 소나 방정식
        self.chk_sonar_eq = QCheckBox("dB 소나 방정식 잠수함 탐지")
        self.chk_sonar_eq.setToolTip(
            "v12.3 — 잠수함 탐지를 곱셈식 사거리 휴리스틱 대신\n"
            "수동 소나 방정식(FOM = 방사소음 − 주변소음 + 배열이득 − 탐지임계)으로 계산합니다.\n"
            "음원 준위(잠수함별)·전달손실(확산+흡수+수온약층)·주변소음(해상상태)으로\n"
            "50% 탐지거리 R50을 구하고, 신호초과 기반 정규분포 확률로 탐지를 판정합니다.\n"
            "정온화된 잠수함(킬로·위안급 AIP)은 탐지가 어렵고, 서해 천해는 탐지거리가 급감합니다."
        )
        self.chk_sonar_eq.setChecked(True)

        # v12.4: 동적 침수·복원력
        self.chk_flooding = QCheckBox("함정 침수·복원력 모델")
        self.chk_flooding.setToolTip(
            "v12.4 — 함정 피해를 즉사 HP 대신 동적 침수로 시뮬합니다.\n"
            "수선 아래 피격(어뢰 80%·대함미사일 30%)이 격실 침수를 유발하고,\n"
            "손상통제(펌프 배수)가 침수 속도와 경쟁합니다.\n"
            "침수율이 함정별 복원력 한계를 넘으면 침몰 — 침몰 예상 시간이 실시간 표시됩니다.\n"
            "함종별 배수량·격실 수·손상통제 효율을 반영(소형함은 어뢰 1발 침몰, 항모는 견딤).\n"
            "전술급(700초)에서 의미 있도록 침수 속도를 압축 — 실제 침몰은 더 느립니다."
        )
        self.chk_flooding.setChecked(True)

        # 적 무장 탑재량 한계 — 적이 실제 탑재량만큼만 공격 무장 사용, 소진 시 재무장 복귀
        self.chk_munition_limit = QCheckBox("적 무장 탑재량 한계")
        self.chk_munition_limit.setToolTip(
            "적 함정·항공기·잠수함이 실제 탑재량만큼만 공격 무장(대함미사일·어뢰)을 사용합니다.\n"
            "탑재 무장을 다 쏘면 재무장을 위해 전장에서 이탈(복귀)합니다.\n"
            "CIWS 등 방어 무장은 무제한 — 실제 교전 시간 내 거의 소진되지 않습니다.\n"
            "기본값 ON — 무한 미사일의 비현실성을 제거합니다. (아군 무장은 항상 유한)"
        )
        self.chk_munition_limit.setChecked(True)

        # 지속 전장 모드 — 단발 교전을 양측 작전 목표 기반 지속 전장으로 (아키텍처 전환·병행 구축)
        self.chk_battle = QCheckBox("지속 전장 모드 (실험적)")
        self.chk_battle.setToolTip(
            "단발 살보 교전 대신, 양측이 작전 목표(자산 방어 등)를 두고\n"
            "시간에 걸쳐 겨루는 지속 전장으로 실행합니다.\n"
            "승패는 요격률이 아니라 임무 달성(방어 자산 생존)으로 판정됩니다.\n"
            "기본값 OFF — 기존 단발 교전과 공존(병행 구축 단계). 단일 시뮬에 적용."
        )
        self.chk_battle.setChecked(False)

        # v18.1: 작전급 캠페인 모드 (실험적) — 며칠 단위 전역
        self.chk_campaign = QCheckBox("작전급 캠페인 모드 (실험적)")
        self.chk_campaign.setToolTip(
            "교전 1회 대신, 며칠 단위 전역(기본 72시간)을 1시간 단위로 진행합니다.\n"
            "함정 초계·교전·귀항·수리를 추적하고, 교전은 학습된 예측 모델로 즉시 계산해\n"
            "72시간 전역을 수초에 끝냅니다. 승패는 해상 교통로(서해·대한해협·동해) 통제로 판정.\n"
            "기본값 OFF — 기존 교전 모드와 공존 (작전급 엔진 구축 단계, 실험적)."
        )
        self.chk_campaign.setChecked(False)

        # v18.4: 전장의 안개 — 캠페인 모드에서 적 위치를 불완전 정보로 관리
        self.chk_campaign_fog = QCheckBox("전장의 안개 (적 위치 불확실성) (실험적)")
        self.chk_campaign_fog.setToolTip(
            "작전급 캠페인 모드에서 적 위치를 '확실'이 아닌 관측 기반 추정(belief)으로 관리합니다.\n"
            "초계 함정·초계기·위성이 탐지한 교통로만 실측을 알고, 못 본 교통로는 시간이 지날수록\n"
            "불확실해집니다(반감기 12시간). 적이 온 뒤에야 알고 대응하므로 자산이 부족하면\n"
            "빈 교통로가 무방비로 뚫릴 수 있습니다(임무 배정은 belief로, 실제 교전은 실측으로).\n"
            "캠페인 모드와 함께 켜야 작동합니다.\n"
            "기본값 OFF — 기존 결과와 동일 (실험적 기능)"
        )
        self.chk_campaign_fog.setChecked(False)

        # v19.1: 공군 작전급 층 — 제공권 격자 + 공군 전력 관리(캠페인 모드 하위)
        self.chk_air_campaign = QCheckBox("공군 작전급 (제공권) (실험적)")
        self.chk_air_campaign.setToolTip(
            "작전급 캠페인 모드에 공군 층을 얹습니다. 한·미 공군(KF-21·F-35A·F-15K·B-1B 등)이\n"
            "제공권 장악(CAP)·정찰 임무를 수행하고, 한반도 격자 지도로 교통로별 제공권(0~1)을 계산합니다.\n"
            "일일 소티율·재무장을 추적하며, 아군 출격 밀도 대 적 대공 위협으로 제공권이 오르내립니다.\n"
            "캠페인 모드와 함께 켜야 작동합니다(v19.1은 제공권을 산출·표시만, 해군 교전 연동은 v19.2).\n"
            "기본값 OFF — 기존 결과와 동일 (실험적 기능)"
        )
        self.chk_air_campaign.setChecked(False)

        # A1: 정밀 교전 — 캠페인 zone 교전을 대리모델 근사 대신 실제 전술 단발로 해결
        self.chk_precise_engage = QCheckBox("정밀 교전 (실측 손실·요격) (실험적)")
        self.chk_precise_engage.setToolTip(
            "작전급 캠페인의 교전을 학습 대리모델 근사 대신 실제 전술 시뮬레이션으로 해결합니다.\n"
            "규모가 큰 교전(적 3척/발 이상)마다 시간스텝 교전을 실제로 돌려 함정 손실·요격률·요격탄\n"
            "비용을 근사가 아닌 실측으로 반영합니다(소규모 교전은 속도를 위해 대리모델 유지 — 하이브리드).\n"
            "캠페인 결과의 함정 손상이 '추상 피해'가 아닌 실제 전술 교전 결과가 됩니다.\n"
            "캠페인 모드와 함께 켜야 작동하며, 단발보다 느립니다(교전 수 × 전술 시뮬).\n"
            "기본값 OFF — 기존 결과와 동일 (실험적 기능)"
        )
        self.chk_precise_engage.setChecked(False)

        # v19.3: 방공망 제압(SEAD/DEAD) — 공군 작전급 하위 옵션
        self.chk_sead = QCheckBox("방공망 제압 SEAD/DEAD (실험적)")
        self.chk_sead.setToolTip(
            "공군 작전급에서 적 방공망(S-400·HQ-9·S-300 등 IADS)이 해상 접근 공역을 방어합니다.\n"
            "활성 방공망은 제공권을 끌어내리고, SEAD 임무기(F-35A·F-15K·KF-16 등)가 이를 제압합니다.\n"
            "제압된 방공망은 6~48시간에 걸쳐 재가동하며, 제압 효과는 보수적으로 반영합니다(과대평가 방지).\n"
            "강한 공군은 방공망을 눌러 제공권을 유지하지만, 빈약한 편성은 CAP·SEAD를 동시에 못해 제압당합니다.\n"
            "공군 작전급과 함께 켜야 작동합니다(끄면 방공망 없이 제공권만 계산 = 기존과 동일).\n"
            "기본값 OFF — 기존 결과와 동일 (실험적 기능)"
        )
        self.chk_sead.setChecked(False)

        # v19.4: 전략 폭격 & 기지 타격 — 공군 작전급 하위 옵션
        # ⚠ 위젯 attr은 chk_strategic_strike(고유명). 기존 "공격 임무 활성화"가 self.chk_strike를
        #    쓰므로 이름 충돌 금지 — 같은 이름이면 나중 정의가 이겨 이 위젯이 orphan이 됨.
        self.chk_strategic_strike = QCheckBox("전략 폭격 & 기지 타격 (실험적)")
        self.chk_strategic_strike.setToolTip(
            "공군 작전급에서 전략폭격기(B-1B·B-52)가 적 항구·비행장을 타격해 적 해군 출항 능력을 떨어뜨립니다.\n"
            "기지 손상이 누적되면 적 해상 위협(웨이브 규모)이 줄어 제공권·해상 교통로 통제가 개선됩니다.\n"
            "타격받은 기지는 6~72시간에 걸쳐 재건되며, 타격 효과는 보수적으로 반영합니다(과대평가 방지).\n"
            "전략폭격은 전략폭격기 보유 편성(한미 연합 등)에서만 작동합니다 — 다중역할기는 제공권 유지에 우선 배정됩니다.\n"
            "공군 작전급과 함께 켜야 작동합니다(끄면 적 기지 없이 기존과 동일).\n"
            "기본값 OFF — 기존 결과와 동일 (실험적 기능)"
        )
        self.chk_strategic_strike.setChecked(False)

        # v21.2: 합동 화력 지원 — 육해공이 같은 적 기지를 협조 타격(캠페인 모드 하위)
        self.chk_joint_fires = QCheckBox("합동 화력 지원 (육해공 협조 타격) (실험적)")
        self.chk_joint_fires.setToolTip(
            "적 항구·비행장을 공군 전략폭격기만이 아니라 해군 순항미사일(현무-3C·토마호크)과\n"
            "육군 지대지(현무-2)가 함께 협조 타격합니다.\n"
            "공군 단독 폭격은 최우선 기지 한 곳에만 화력을 쏟아 나머지 기지를 방치하지만,\n"
            "합동 화력은 한 기지가 무력화되면 남은 화력을 다음 기지로 넘겨 낭비를 막습니다.\n"
            "전략폭격기가 없는 편성(제공권 열세)에서 특히 값합니다 — 폭격기 없이도\n"
            "해군·육군 화력만으로 적 항구를 무력화해 적 함대의 출항 능력을 떨어뜨립니다.\n"
            "전략 폭격 & 기지 타격, 공군 작전급과 **함께** 켜야 작동합니다\n"
            "(적 기지가 없으면 때릴 표적이 없고, 공군 층이 없으면 기지 손상이 적 출항 능력에\n"
            " 반영될 통로가 없습니다).\n"
            "기본값 OFF — 기존 결과와 동일 (실험적 기능)"
        )
        self.chk_joint_fires.setChecked(False)

        # v21.4: 합동작전 통합 보고서 — 군별 기여도(반사실 분해)
        self.chk_joint_report = QCheckBox("합동작전 통합 보고서 (군별 기여도) (실험적)")
        self.chk_joint_report.setToolTip(
            "각 군이 전역 결과에 얼마나 대체 불가능했는지를 분해해 보고합니다.\n"
            "전략폭격·지상 작전급을 각각 뺀 전역을 실제로 다시 돌려, 그 수단이 없었다면\n"
            "전역이 얼마나 나빠졌을지를 잽니다(단순 집계가 아니라 반사실 비교).\n"
            "넣는 순서에 따라 몫이 달라지는 단계별 비교와 달리, 모든 순서의 평균을 써\n"
            "순서 의존이 없습니다. 겹치는 공로(합동 화력 시너지)는 각 군에 공평히 나눕니다.\n"
            "⚠ 방공망 제압은 적 방공망도 함께 생성하므로 '기여도'가 아니라\n"
            "  '전장이 열렸을 때의 순효과'로 따로 표기합니다.\n"
            "캠페인 모드 전용 — 전역을 여러 번 더 돌리므로 분석 시간이 늘어납니다.\n"
            "기본값 OFF — 기존 결과와 동일 (실험적 기능)"
        )
        self.chk_joint_report.setChecked(False)

        self.cmb_joint_mode = NoScrollComboBox()
        self.cmb_joint_mode.addItems(['시차 공격', '동시 공격'])
        self.cmb_joint_mode.setToolTip(
            "시차 공격: 순항미사일과 폭격기를 시간차로 투입해 아군 오사를 피합니다.\n"
            "동시 공격: 같은 시각에 집중해 적 방공망을 분산시키지만, 화력지원 협조수단 없이\n"
            "폭격기가 미사일 궤적과 겹치면 유인 편대가 임무를 중단합니다(협조 미비 손실).\n"
            "합동 화력 지원을 켜야 적용됩니다."
        )

        self.cmb_army_fire = NoScrollComboBox()
        self.cmb_army_fire.addItems(list(ARMY_FIRE_PRESETS.keys()))
        self.cmb_army_fire.setCurrentText('없음')
        self.cmb_army_fire.setToolTip(
            "합동 화력에 참여할 육군 지대지 화력(현무-2 계열) 편성입니다.\n"
            "천무는 사거리 80km로 적 항구·비행장에 닿지 않아 편성에서 제외했습니다.\n"
            "지상 작전급·합동 화력 지원과 함께 켜야 작동합니다."
        )

        # v20.2b: 지상 작전급 층 — 연안 방공망(캠페인 모드 하위)
        self.chk_army_campaign = QCheckBox("지상 작전급 (연안 방공망) (실험적)")
        self.chk_army_campaign.setToolTip(
            "작전급 캠페인 모드에 지상 층을 얹습니다. 해상 교통로별로 연안 방공 포대를 배치해\n"
            "함대 상공을 함께 방어합니다(이지스 어쇼어 SM-3·THAAD·L-SAM·패트리엇 PAC-3·천궁-II 5계층).\n"
            "적 대함탄도탄(DF-21D 등)이 있는 교통로의 교전은 확률 근사가 아닌 실제 전술 교전으로\n"
            "해결해, 연안 포대의 요격탄이 실제로 몇 발 나가 몇 발을 막았는지 실측합니다.\n"
            "요격탄 재고는 전역 내내 이어지며(소진 시 방어 저하), 통상 교전에는 방공 보강으로 기여합니다.\n"
            "캠페인 모드와 함께 켜야 작동합니다.\n"
            "기본값 OFF — 기존 결과와 동일 (실험적 기능)"
        )
        self.chk_army_campaign.setChecked(False)

        self.chk_coastal_sam = QCheckBox("연안 방공 포대 배치 (실험적)")
        self.chk_coastal_sam.setToolTip(
            "해상 교통로(서해·대한해협·동해)마다 연안 방공 포대를 실제로 배치합니다.\n"
            "끄면 지상 층이 있어도 포대가 없어 방어 기여가 없습니다(대조군).\n"
            "지상 작전급과 함께 켜야 작동합니다.\n"
            "기본값 OFF — 기존 결과와 동일 (실험적 기능)"
        )
        self.chk_coastal_sam.setChecked(False)

        # v20.3: 해상 상륙작전 — 지상 층 하위 옵션
        self.chk_amphibious = QCheckBox("해상 상륙작전 (교두보 확보) (실험적)")
        self.chk_amphibious.setToolTip(
            "상륙 선단(독도함급 강습상륙함·상륙함)이 목표 해안으로 이동해 교두보를 확보합니다.\n"
            "적재 → 수송 → 항공 엄호 → 상륙의 순서로 진행하며, 각 단계의 성공 확률을 곱해\n"
            "그 시간의 교두보 진척이 정해집니다 — 한 단계만 무너져도 상륙이 멈춥니다.\n"
            "  · 수송: 해상 교통로 통제도 (교통로가 막히면 선단이 해안에 못 닿습니다)\n"
            "  · 엄호: 목표 구역 제공권 (공군 작전급과 함께 켜야 제공권이 계산됩니다)\n"
            "  · 상륙: 호위 함대의 함포 지원 대 적 연안 방어 강도\n"
            "교두보 확보 여부가 전역 승패 판정에 반영됩니다(교통로 통제와 함께 평가).\n"
            "지상 작전급·캠페인 모드와 함께 켜야 작동합니다.\n"
            "기본값 OFF — 기존 결과와 동일 (실험적 기능)"
        )
        self.chk_amphibious.setChecked(False)

        # v20.4: 적 방공망 제압(도미노) — 지상 층 하위 옵션
        self.chk_enemy_sead = QCheckBox("적 방공망 제압 → 도미노 (실험적)")
        self.chk_enemy_sead.setToolTip(
            "적이 제공권을 쥐면 아군 연안 방공 포대를 제압합니다(적 SEAD/DEAD).\n"
            "제압된 포대는 방공 기여를 잃고, 그만큼 제공권이 더 떨어지며,\n"
            "제공권 상실은 다시 해상 교통로 통제를 압박합니다 — 연쇄(도미노)입니다.\n"
            "  연안 방공망 제압 → 제공권 하락 → 해상 교통로 압박 → 전역 패배\n"
            "제압은 최대 85%까지만 진행되고, 적이 손을 놓으면 포대가 재전개됩니다(24시간).\n"
            "반대로 아군이 제공권을 유지하면 포대가 제압당하지 않습니다.\n"
            "지상 작전급·연안 방공 포대·공군 작전급과 함께 켜야 작동합니다.\n"
            "기본값 OFF — 기존 결과와 동일 (실험적 기능)"
        )
        self.chk_enemy_sead.setChecked(False)

        self.chk_rl_policy = QCheckBox("AI 전술 (학습된 정책) (실험적)")
        self.chk_rl_policy.setToolTip(
            "지속 전장 모드에서 강화학습으로 훈련된 방어 정책이 전술을 자동 결정합니다.\n"
            "30초마다 위협 상황을 보고 무기 우선순위·살보·레이더·표적·기동·CAP·ECM을\n"
            "국면에 맞게 전환합니다(개발 PC에서 학습한 정책 가중치를 내장, 실시간 추론).\n"
            "지속 전장 모드와 함께 켜야 작동합니다(단발 모드엔 무관).\n"
            "기본값 OFF — 기존 결과와 동일 (실험적 기능)"
        )
        self.chk_rl_policy.setChecked(False)

        self.chk_esm_arm = QCheckBox("ESM 역탐지 — 레이더 방사 시 대방사미사일 유도 (실험적)")
        self.chk_esm_arm.setToolTip(
            "전자전 EMCON 딜레마: 아군 레이더가 켜져 방사 중일 때만 적 전자지원(ESM)이 신호를\n"
            "포착해 대방사미사일(ARM)을 실시간 유도합니다. 레이더를 끄면 적은 마지막 포착 위치로만\n"
            "ARM을 유도해 명중률이 급감합니다(레이더 끄면 ARM 회피, 대신 대공 탐지·교전은 손실).\n"
            "기본값 OFF — 기존 결과와 동일 (실험적 기능)"
        )
        self.chk_esm_arm.setChecked(False)

        self.chk_target_difficulty = QCheckBox(
            "표적 난이도 — 고속·소형 표적일수록 요격 어려움")
        self.chk_target_difficulty.setToolTip(
            "요격 확률에 표적의 속도와 레이더 반사면적(RCS)을 반영합니다.\n"
            "초음속·소형 표적(대방사미사일·초음속 대함미사일 등)은 종말 유도와 근접 신관\n"
            "여유가 줄어 요격이 어려워집니다. 아음속 대함미사일급 표적이 기준(변화 없음)이며,\n"
            "그보다 크거나 느린 표적의 요격률은 낮아지지 않습니다.\n"
            "탄도·극초음속 표적은 속도 벌점에서 면제됩니다 — SM-3·THAAD 같은 요격 전용\n"
            "체계의 요격 확률은 애초에 마하 10급 탄도를 기준으로 매긴 값이기 때문입니다.\n"
            "기본값 ON — 끄면 표적의 속도·크기를 무시한 요격이 됩니다 (비교·검증용)"
        )
        self.chk_target_difficulty.setChecked(True)

        self.chk_sonar_emcon = QCheckBox("능동 소나 핑 역탐지 (실험적)")
        self.chk_sonar_emcon.setToolTip(
            "대잠전 EMCON 딜레마: 능동 소나(디핑·소노부이)로 적 잠수함을 탐지하면 잠수함도\n"
            "그 핑을 역포착해 은닉을 풀고 어뢰 반격을 앞당기며 회피 기동합니다(능동 = 탐지\n"
            "우위지만 내 위치 노출). 소나 방정식 기능과 함께 켜야 작동합니다.\n"
            "기본값 OFF — 기존 결과와 동일 (실험적 기능)"
        )
        self.chk_sonar_emcon.setChecked(False)

        self.chk_asw_contact_limit = QCheckBox(
            "대잠 접촉 유지 — 접촉이 끊기면 잠수함을 놓친다 (실험적)")
        self.chk_asw_contact_limit.setToolTip(
            "대잠 항공 탐지에 표정 오차(datum)를 반영합니다. 실제 대잠전에서 잠수함의 추정\n"
            "위치는 마지막 접촉 이후 시간이 흐를수록 넓어집니다(잠수함 속도 × 경과 시간).\n"
            "  · 접촉을 유지하는 동안은 오차가 작아 소노부이·디핑소나가 잘 찾습니다\n"
            "  · 잠수함이 잠항 도주해 접촉이 끊기면 수색 구역이 넓어져 탐지가 어려워집니다\n"
            "  · 몇 차례 실패해 표적을 포기하면 재접촉 시도까지 시간이 걸립니다\n"
            "이것이 없으면 대잠 항공기가 잠수함 위치를 늘 아는 셈이 되어 탐지가 사실상\n"
            "보장되고, 능동 소나 역탐지(EMCON)를 켜도 잠수함이 숨을 방법이 없습니다.\n"
            "능동 소나 핑 역탐지·소나 방정식과 함께 켜야 효과가 드러납니다.\n"
            "기본값 OFF — 기존 결과와 동일 (실험적 기능)"
        )
        self.chk_asw_contact_limit.setChecked(False)

        self.chk_standoff_spawn = QCheckBox(
            "스탠드오프 교전 — 적 수상함이 자기 미사일 사거리에서 발사")
        self.chk_standoff_spawn.setToolTip(
            "적 수상함이 자기 대함미사일 사거리에서 발사합니다(현대 해전의 스탠드오프 교리).\n"
            "이 항목이 없으면 적 함대의 출발 거리가 '아군 레이더 탐지거리'로 정해져,\n"
            "사거리 540km의 YJ-18을 실은 052D형이 44km까지 다가와서 쏘게 됩니다 —\n"
            "적이 어디서 싸울지가 내 레이더 성능에 좌우되는 셈이라 비현실적입니다.\n"
            "  · 적이 원거리에서 쏘므로 미사일 비행 시간이 길어져 요격 기회가 늘어납니다\n"
            "  · 대신 적 함대가 수평선 너머에 있어 눈에 보이지 않습니다 —\n"
            "    해상 초계 무인기의 광역 정찰이 비로소 값을 하게 됩니다\n"
            "기본값 ON — 끄면 적이 자기 사거리를 버리고 접근합니다 (비교·검증용)"
        )
        self.chk_standoff_spawn.setChecked(True)

        self.chk_cyber = QCheckBox("사이버전 — 데이터링크 변조·전투정보실 마비·레이더 교란 반격 (실험적)")
        self.chk_cyber.setToolTip(
            "적 사이버 공격과 아군 반격을 모델링합니다. 일정 주기마다 침투를 시도해 성공하면\n"
            "한동안 효과가 지속되며, 전자전과 달리 경고 없이 은밀하게 발현·해제됩니다.\n"
            "  · 데이터링크 변조 → 표적 데이터 오염으로 아군 요격 명중률 저하\n"
            "  · 전투정보실 마비 → 처리 지연으로 아군 탐지거리 일시 저하\n"
            "  · 레이더 교란 반격 → 적 사격통제 교란으로 적 발사 명중률 저하\n"
            "기본값 OFF — 기존 결과와 동일 (실험적 기능)"
        )
        self.chk_cyber.setChecked(False)

        self.chk_hgv_glide = QCheckBox("극초음속 활공 궤적 — 단계별 고도 변화·다층 요격 전환")
        self.chk_hgv_glide.setToolTip(
            "극초음속 활공체(HGV)가 고정 고도가 아니라 마하 5+로 활공하며 고도를 낮추고\n"
            "종말에 급강하합니다. 강하하면서 지상 방어 계층의 요격 고도창을 차례로 통과해\n"
            "L-SAM → 패트리엇 → 천궁-II로 다층 요격이 이어집니다.\n"
            "끄면 고도가 고정돼(DF-17 60km) 하위 종말 계층이 교전창에 영원히 진입하지 못합니다.\n"
            "활공·종말 횡기동으로 요격 명중률은 소폭 낮아집니다.\n"
            "기본값 ON — 극초음속의 실제 비행 물리 (끄면 비교·디버그용)"
        )
        self.chk_hgv_glide.setChecked(True)

        self.chk_asw_forward = QCheckBox("대잠 항공 전진 초계")
        self.chk_asw_forward.setToolTip(
            "대잠 헬기·초계기가 함대에 수동 대기하지 않고 전개 사거리 안의 적 잠수함 방위로\n"
            "전진해 탐지·교전합니다. 끄면 잠수함이 함대 근처(약 20km)로 접근할 때까지 기다려\n"
            "교전이 늦고 이탈 잠수함은 놓치지만, 켜면 잠수함을 일찍 적극 추적합니다.\n"
            "기본값 OFF — 기존 결과와 동일"
        )
        self.chk_asw_forward.setChecked(False)

        self.chk_weather_dyn = QCheckBox("동적 기상 변화")
        self.chk_weather_dyn.setToolTip(
            "v12.5 — 교전 중 날씨가 확률적으로 변화합니다.\n"
            "5분마다 1단계씩 악화·호전 판정. 계절·해역에 따라 확률이 달라집니다.\n"
            "  겨울 동해·서해: 북서계절풍으로 악화 확률↑\n"
            "  여름 동해·남해: 태풍 시즌으로 악화 확률↑\n"
            "탐지·요격·소나·항공 출격 능력이 실시간 변동됩니다.\n"
            "추세를 '악화'로 설정하면 태풍 접근 시나리오를 연출할 수 있습니다.\n"
            "기본값 OFF — 기존 결과와 동일 (검증 완료·정규 옵션)"
        )
        self.chk_weather_dyn.setChecked(False)

        self.cmb_weather_trend = NoScrollComboBox()
        self.cmb_weather_trend.addItems(['자동', '악화', '안정', '호전'])
        self.cmb_weather_trend.setToolTip(
            "동적 기상 변화 추세 설정 (동적 기상 변화 ON일 때만 적용).\n"
            "자동: 계절·해역 기반 확률 전이\n"
            "악화: 악화 확률을 높여 태풍 접근 시나리오 연출\n"
            "안정: 변화 확률을 줄여 기상 유지 경향\n"
            "호전: 호전 확률↑ — 기상 개선 시나리오"
        )

        def _on_weather_dyn_toggled(checked: bool):
            self.cmb_weather_trend.setEnabled(checked)
        self.chk_weather_dyn.toggled.connect(_on_weather_dyn_toggled)
        _on_weather_dyn_toggled(False)

        self.chk_iff = QCheckBox("피아식별 오류")
        self.chk_iff.setToolTip(
            "v12.6 — IFF(피아식별) 실패 확률을 교전에 반영합니다.\n"
            "C&D 결심 후 IFF 판정 실패 시 15초 재확인 대기. ECM 재밍·혼잡 교전 시 확률↑\n"
            "CAP 전투기 운용 중 IFF 실패가 누적되면 아군 오사(오인 발사) 발생 가능.\n"
            "기본값 OFF — 기존 결과와 동일"
        )
        self.chk_iff.setChecked(False)

        # v9.14: 해협 통과 시나리오 — 대한해협 선택 시에만 표시
        self.cmb_strait_type = NoScrollComboBox()
        self.cmb_strait_type.addItems(['서수도 (서→동)', '동수도 (동→서)', '양방향 협공'])
        self.cmb_strait_type.setToolTip(
            "해협 통과 방향 선택 — 위협 접근 방위를 동/서 방향 ±30° 이내로 제한합니다.\n"
            "서수도 (49.5 km): 서쪽(일본해)에서 동쪽으로 접근 — 기동 공간 가장 좁음\n"
            "동수도 (98 km): 동쪽(태평양)에서 서쪽으로 접근 — 기동 공간 중간\n"
            "양방향 협공: 동수도·서수도 동시 협공 — 최고 난이도\n"
            "잠수함 잠항 수심은 해협 임계수심(서수도 130m / 동수도 115m)으로 자동 제한."
        )
        self._row_strait_label = QLabel("해협 진입로")
        self._row_strait_label.setStyleSheet(f"color:{C_TEXT}; font-size:15px;")

        def _on_region_changed(txt: str):
            is_strait = (txt == '대한해협')
            self.cmb_strait_type.setEnabled(is_strait)
            self._row_strait_label.setStyleSheet(
                f"color:{C_TEXT if is_strait else C_SUBTEXT}; font-size:15px;")
            if is_strait:
                self.chk_terrain.setChecked(True)

        self.cmb_region.currentTextChanged.connect(_on_region_changed)
        _on_region_changed(self.cmb_region.currentText())

        for chk in [self.chk_terrain, self.chk_evap_duct, self.chk_anti_sam,
                    self.chk_isa, self.chk_png, self.chk_sonar_eq,
                    self.chk_flooding, self.chk_munition_limit,
                    self.chk_weather_dyn, self.chk_iff,
                    # 실험적/고급 토글 — 누락 시 인디케이터 스타일 미적용으로 체크박스 네모가
                    # 안 보인다(어두운 배경). 환경 그룹의 모든 체크박스는 반드시 여기 포함.
                    self.chk_battle, self.chk_campaign, self.chk_campaign_fog,
                    self.chk_air_campaign, self.chk_precise_engage,
                    self.chk_sead, self.chk_strategic_strike,
                    self.chk_army_campaign, self.chk_coastal_sam, self.chk_amphibious,
                    self.chk_enemy_sead, self.chk_joint_fires,   # v21.2
                    self.chk_joint_report,                       # v21.4
                    self.chk_rl_policy, self.chk_esm_arm, self.chk_target_difficulty,
                    self.chk_sonar_emcon, self.chk_asw_contact_limit,
                    self.chk_standoff_spawn,
                    self.chk_cyber, self.chk_hgv_glide, self.chk_asw_forward]:
            _wire_chk_color(chk, 13)

        fl_env.addRow("",            self.chk_terrain)
        fl_env.addRow("",            self.chk_evap_duct)
        fl_env.addRow("",            self.chk_anti_sam)
        fl_env.addRow("",            self.chk_isa)
        fl_env.addRow("",            self.chk_png)
        fl_env.addRow("",            self.chk_sonar_eq)
        fl_env.addRow("",            self.chk_flooding)
        fl_env.addRow("",            self.chk_munition_limit)
        fl_env.addRow("",            self.chk_battle)
        fl_env.addRow("",            self.chk_campaign)
        fl_env.addRow("",            self.chk_campaign_fog)
        fl_env.addRow("",            self.chk_air_campaign)
        fl_env.addRow("",            self.chk_precise_engage)
        fl_env.addRow("",            self.chk_sead)
        fl_env.addRow("",            self.chk_strategic_strike)
        fl_env.addRow("",            self.chk_army_campaign)
        fl_env.addRow("",            self.chk_coastal_sam)
        self.cmb_coastal_preset = NoScrollComboBox()
        self.cmb_coastal_preset.addItems(list(COASTAL_SAM_PRESETS.keys()))
        self.cmb_coastal_preset.setCurrentText('연안 방공 기본')
        self.cmb_coastal_preset.setToolTip(
            "교통로마다 배치할 연안 방공 포대의 편성입니다.\n"
            "연안 방공 기본 — 천궁-II 32발 + L-SAM 8발 (하층 위주 저비용 점방어)\n"
            "연안 방공 강화 — 4계층 완편 (어쇼어 SM-3·THAAD·L-SAM·천궁-II, 한·미 통합)\n"
            "한국형 BMD (KAMD) — L-SAM 16발 + 천궁-II 32발 (국산 계층만 자주 방어)"
        )
        fl_env.addRow("연안 포대 편성", self.cmb_coastal_preset)
        # v21.2 합동 화력 지원 — 육해공 협조 타격(전략 폭격·공군 작전급과 짝)
        fl_env.addRow("",            self.chk_joint_fires)
        fl_env.addRow("",            self.chk_joint_report)   # v21.4
        fl_env.addRow("합동 화력 방식", self.cmb_joint_mode)
        fl_env.addRow("육군 지대지 화력", self.cmb_army_fire)
        fl_env.addRow("",            self.chk_amphibious)
        self.cmb_amphib_zone = NoScrollComboBox()
        self.cmb_amphib_zone.addItems(list(SLOC_ZONES))
        self.cmb_amphib_zone.setToolTip(
            "상륙 선단이 교두보를 확보할 목표 해안(해상 교통로)입니다.\n"
            "그 교통로의 통제도·제공권·호위 함정 수가 상륙 성공을 좌우합니다."
        )
        fl_env.addRow("상륙 목표 해안", self.cmb_amphib_zone)
        fl_env.addRow("",            self.chk_enemy_sead)
        fl_env.addRow("",            self.chk_rl_policy)
        fl_env.addRow("",            self.chk_esm_arm)
        fl_env.addRow("",            self.chk_target_difficulty)
        fl_env.addRow("",            self.chk_sonar_emcon)
        fl_env.addRow("",            self.chk_asw_contact_limit)
        fl_env.addRow("",            self.chk_standoff_spawn)
        fl_env.addRow("",            self.chk_cyber)
        fl_env.addRow("",            self.chk_hgv_glide)
        fl_env.addRow("",            self.chk_asw_forward)
        fl_env.addRow("",            self.chk_weather_dyn)
        fl_env.addRow("기상 추세",   self.cmb_weather_trend)
        fl_env.addRow("",            self.chk_iff)
        fl_env.addRow(self._row_strait_label, self.cmb_strait_type)


        # ── 적군 편대 (포팅 A) ────────────────────────────────────────────
        grp_e = QGroupBox("🔴 적군 편대")
        el = QVBoxLayout(grp_e)
        el.setSpacing(4)

        # 모드 선택
        mode_row = QWidget(); mode_rl = QHBoxLayout(mode_row)
        mode_rl.setContentsMargins(0, 0, 0, 0)
        mode_rl.addWidget(QLabel("모드:"))
        self.cmb_enemy_mode = NoScrollComboBox()
        self.cmb_enemy_mode.addItems(['프리셋', '혼합 시나리오', '랜덤'])
        mode_rl.addWidget(self.cmb_enemy_mode, stretch=1)
        el.addWidget(mode_row)

        # 프리셋 선택 (프리셋 모드용) — 버튼 그리드
        _ep_names = list(V7_ENEMY_FLEET_PRESETS.keys()) if _V7_OK else []
        self.cmb_fleet_preset_e = NoScrollComboBox()        # 하위 호환용 숨김 콤보
        self.cmb_fleet_preset_e.addItems(_ep_names)
        self.cmb_fleet_preset_e.hide()
        self._ep_preset_row = QWidget()
        _eprl = QVBoxLayout(self._ep_preset_row)
        _eprl.setContentsMargins(0,0,0,0); _eprl.setSpacing(3)
        _ep_bg = QButtonGroup(self); _ep_bg.setExclusive(True)
        _ep_grid = QWidget(); _epgl = QGridLayout(_ep_grid)
        _epgl.setContentsMargins(0,0,0,0); _epgl.setSpacing(3)
        _ep_popup = _HoverPopup(self)
        for _i, _en in enumerate(_ep_names):
            _b = QPushButton(_en); _b.setCheckable(True)
            _b.setStyleSheet(_TOG_SS); _b.setFixedHeight(26)
            _tip = self._enemy_preset_tooltip(_en) if _V7_OK else ""
            _install_hover(_b, _tip, _ep_popup)
            if _i == 0: _b.setChecked(True)
            _ep_bg.addButton(_b, _i)
            _epgl.addWidget(_b, _i // 2, _i % 2)
        _ep_bg.idClicked.connect(self.cmb_fleet_preset_e.setCurrentIndex)
        self.cmb_fleet_preset_e.currentIndexChanged.connect(
            lambda i: _ep_bg.button(i).setChecked(True) if _ep_bg.button(i) else None)
        self.cmb_fleet_preset_e.currentTextChanged.connect(self._update_enemy_preset_detail)
        _eprl.addWidget(_ep_grid)
        el.addWidget(self._ep_preset_row)

        # NEW-A: 혼합 시나리오 선택 (혼합 모드용) — 버튼 그리드
        _mx_names = list(V7_MIXED_SCENARIOS.keys()) if _V7_OK else []
        _MX_SHORT = {
            '순항미사일 + 탄도탄 복합':          '순항+탄도탄 복합',
            '잠수함 어뢰 + 대함미사일 병행':      '잠수함+대함미사일',
            '항모 킬 체인 (스텔스→HGV→초음속)':  '항모 킬 체인',
            '전방위 포화 공격 (채널 포화)':       '전방위 포화 공격',
        }
        self._mixed_row = QWidget(); mixed_rl = QVBoxLayout(self._mixed_row)
        mixed_rl.setContentsMargins(0, 0, 0, 0); mixed_rl.setSpacing(3)
        self.cmb_mixed_scenario = NoScrollComboBox()        # 하위 호환용 숨김 콤보
        self.cmb_mixed_scenario.addItems(_mx_names)
        self.cmb_mixed_scenario.hide()
        _mx_bg = QButtonGroup(self); _mx_bg.setExclusive(True)
        _mx_grid = QWidget(); _mxgl = QGridLayout(_mx_grid)
        _mxgl.setContentsMargins(0,0,0,0); _mxgl.setSpacing(3)
        _mx_popup = _HoverPopup(self)
        for _i, _mn in enumerate(_mx_names):
            _b = QPushButton(_MX_SHORT.get(_mn, _mn)); _b.setCheckable(True)
            _b.setStyleSheet(_TOG_SS); _b.setFixedHeight(26)
            if _V7_OK:
                _sc = V7_MIXED_SCENARIOS[_mn]
                _mx_desc = _sc.get('description', '')
                _waves = _sc.get('waves', [])
                if _waves:
                    _wave_lines = []
                    for _w in _waves:
                        _d = _w.get('delay_s', 0)
                        _ts = ', '.join(
                            f"{_t['preset']}×{_t['count']}"
                            for _t in _w.get('threats', [])
                        )
                        _wave_lines.append(f"  +{_d:>3}s  {_ts}")
                    _mx_desc = _mx_desc + '\n\n파 구성:\n' + '\n'.join(_wave_lines)
            else:
                _mx_desc = ""
            _install_hover(_b, _mx_desc, _mx_popup)
            if _i == 0: _b.setChecked(True)
            _mx_bg.addButton(_b, _i)
            _mxgl.addWidget(_b, _i // 2, _i % 2)
        _mx_bg.idClicked.connect(self.cmb_mixed_scenario.setCurrentIndex)
        self.cmb_mixed_scenario.currentIndexChanged.connect(
            lambda i: _mx_bg.button(i).setChecked(True) if _mx_bg.button(i) else None)
        self.cmb_mixed_scenario.currentTextChanged.connect(self._update_mixed_scenario_detail)
        mixed_rl.addWidget(_mx_grid)
        el.addWidget(self._mixed_row)

        # 랜덤 난이도 + 시드 (랜덤 모드용)
        self._rand_row = QWidget(); rand_rl = QHBoxLayout(self._rand_row)
        rand_rl.setContentsMargins(0, 0, 0, 0); rand_rl.setSpacing(4)
        self.cmb_difficulty = NoScrollComboBox()
        self.cmb_difficulty.addItems(list(V7_RANDOM_CFG.keys()) if _V7_OK else ['보통'])
        self.cmb_difficulty.setCurrentText('보통')
        self.cmb_difficulty.currentTextChanged.connect(self._update_difficulty_tooltip)
        self.spn_seed = NoScrollSpinBox(); self.spn_seed.setRange(0, 99999); self.spn_seed.setValue(0)
        self.spn_seed.hide()   # 씨앗 입력 숨김 (항상 랜덤)
        rand_rl.addWidget(self.cmb_difficulty, stretch=1)
        el.addWidget(self._rand_row)

        # ── 📊 예상 전황 (참고) — surrogate 룩업 (실행 전 즉시 추정) ──────────
        self._forecast_card = QGroupBox()
        self._forecast_card.setStyleSheet(
            f"QGroupBox {{ background:#162032; border:1px solid #2a4a6a;"
            f" border-radius:6px; padding:6px; margin-top:4px; }}")
        _fcl = QVBoxLayout(self._forecast_card)
        _fcl.setContentsMargins(8, 4, 8, 6); _fcl.setSpacing(3)
        _ft = QLabel("📊  예상 전황 (참고)")
        _ft.setStyleSheet(f"color:{C_ACCENT}; font-size:10px; font-weight:bold;")
        _fcl.addWidget(_ft)
        self._prev_lbl_forecast = QLabel("—")
        self._prev_lbl_forecast.setWordWrap(True)
        self._prev_lbl_forecast.setStyleSheet(
            f"color:{C_TEXT}; font-size:11px; line-height:150%;")
        _fcl.addWidget(self._prev_lbl_forecast)
        el.addWidget(self._forecast_card)
        if self._surrogate is None:
            self._forecast_card.hide()   # JSON 없으면 카드 자체 숨김(하위호환)

        self.cmb_enemy_mode.currentIndexChanged.connect(self._on_enemy_mode_changed)
        # 예상 전황 갱신 트리거: 아군/적 편대·날씨·모드 변경 시
        self.cmb_fleet.currentTextChanged.connect(lambda _: self._update_forecast_card())
        self.cmb_fleet_preset_e.currentTextChanged.connect(lambda _: self._update_forecast_card())
        self.cmb_weather.currentTextChanged.connect(lambda _: self._update_forecast_card())
        self._on_enemy_mode_changed(0)  # 초기 상태 적용 (기본: 프리셋)
        if _V7_OK:
            if self.cmb_fleet_preset_e.count():
                self._update_enemy_preset_detail(self.cmb_fleet_preset_e.currentText())
            if self.cmb_difficulty.count():
                self._update_difficulty_tooltip(self.cmb_difficulty.currentText())
            if self.cmb_mixed_scenario.count():
                self._update_mixed_scenario_detail(self.cmb_mixed_scenario.currentText())

        # ── 적군 편대 (상단 바 cell 2) ─────────────────────────────────────
        _ew = QWidget(); _ew.setStyleSheet(f"background:{C_PANEL};")
        _ewl = QVBoxLayout(_ew)
        _ewl.setContentsMargins(4, 4, 4, 4); _ewl.setSpacing(4)
        _ewl.addWidget(grp_e); _ewl.addStretch()
        self._cfg_enemy = _ew
        container_layout.addWidget(self._cfg_enemy)

        # ── 시나리오 (상단 바 cell 3) ────────────────────────────────────────
        _sw = QWidget(); _sw.setStyleSheet(f"background:{C_PANEL};")
        _swl = QVBoxLayout(_sw)
        _swl.setContentsMargins(4, 4, 4, 4); _swl.setSpacing(4)
        _swl.addWidget(grp_sc); _swl.addStretch()
        self._cfg_scenario = _sw
        container_layout.addWidget(self._cfg_scenario)

        # 전술 옵션(ECM 재밍·회피 기동·음향 기만기·적 자체방어)은 현실 교전에서
        # 항상 작동하는 능력이므로 토글 UI 없이 항상 ON으로 고정 (cfg에서 True 하드코딩)

        # ── 항공 자산 (포팅 C + v10.5 CAP) ──────────────────────────────────
        grp_ac = QGroupBox("✈️ 항공 자산")
        acl = QGridLayout(grp_ac)
        acl.setSpacing(3)

        _ac_items = [
            ("chk_helo",  "AW-159 와일드캣",    "함재 헬기 · 청상어 2발 · 140km"),
            ("chk_p3c",   "P-3C 오라이온",      "포항기지 · Mk.46 4발 · 소노부이+15km"),
            ("chk_p8a",   "P-8A 포세이돈",      "포항기지 · Mk.46 5발 · 소노부이+18km"),
            ("chk_f35a",  "F-35A 라이트닝 II",  "청주기지 · AIM-120D×4 · CAP 600km"),
            ("chk_kf21",  "KF-21 보라매",       "대구기지 · IRIS-T/AIM-120C×6 · CAP 500km"),
            ("chk_fa50",  "FA-50 파이팅이글",   "원주기지 · AIM-9X×4 · CAP 400km"),
            ("chk_recon", "정찰 드론 MQ-9B (실험적)",
             "군산기지 · 무장 없음 · 수평선 너머(OTH) 표적 탐지 중계로 함대 탐지거리 +120km\n"
             "저생존 — 적 항공위협 존재 시 확률적 격추.\n"
             "기본값 OFF — 기존 결과와 동일 (실험적 기능)"),
        ]
        for _i, (_attr, _label, _tip) in enumerate(_ac_items):
            chk = QCheckBox(_label)
            chk.setChecked(False)
            chk.setToolTip(_tip)
            _wire_chk_color(chk, 12)
            setattr(self, _attr, chk)
            acl.addWidget(chk, _i // 2, _i % 2)

        # ── 방어 전술 옵션 ─────────────────────────────────────────────────
        grp_def = QGroupBox("🛡️ 방어 전술")
        defl = QVBoxLayout(grp_def)
        defl.setSpacing(4)

        # 다층 방어는 전단 교전 표준 교리 — 항상 ON 고정 (cfg에서 True 하드코딩)

        self.chk_cec = QCheckBox("CEC 협동 교전")
        self.chk_cec.setChecked(True)   # 기본 ON — 이지스 전단 실전 운용 표준
        self.chk_cec.setToolTip(
            "v10.4 — Cooperative Engagement Capability (협동 교전 능력).\n"
            "이지스 Link-16 데이터링크로 전단 탐지 정보 공유:\n"
            "  · 탐지 커버리지 통합: 한 함이 탐지한 위협을 전 함정이 교전 가능\n"
            "    예) KDX-III(900km 탐지) → FFX-I(100km 탐지 한계 초과 교전 가능)\n"
            "  · SAM 사전 동시 배정: 1차+2차 함정 동시 발사 (살보 +1)\n"
            "  · CEC 중계 교전 Pk ×0.90 (자체 트랙 없이 데이터링크만 의존)\n"
            "OFF 시: 각 함정은 자체 탐지거리 내 위협만 교전 가능."
        )

        self.chk_multibearing = QCheckBox("다방위 공격")
        self.chk_multibearing.setChecked(False)
        self.chk_multibearing.setToolTip(
            "적 위협이 전방위(0°~360°) 무작위 방향에서 접근합니다.\n"
            "OFF 시 기본 단일 방향 접근."
        )

        self.chk_cec_jammed = QCheckBox("CEC 두절")
        self.chk_cec_jammed.setChecked(False)
        self.chk_cec_jammed.setToolTip(
            "적 전자전으로 CEC 네트워크가 차단됩니다.\n"
            "각 함정이 독립적으로 교전 — 다층 방어 무력화.\n"
            "CEC 사전 배정이 ON이어도 강제 비활성화됩니다."
        )

        # v16.13.02 트랙 C: 함정 자율 교전
        self.chk_autonomous = QCheckBox("함정 자율 교전 (실험적)")
        self.chk_autonomous.setChecked(False)
        self.chk_autonomous.setToolTip(
            "각 함정이 CEC 중앙 조율 없이 자기 센서·사거리 내 위협을 독립 판단해 교전합니다.\n"
            "  · CEC 두절(재밍)과 달리 함정 자체 교전 능력(살보)은 온전 — 협동 엄호(원거리 중계)만 없음\n"
            "  · 지휘 노드(기함)에 의존하지 않아 기함 격침에 강건 — 지휘 저하 없이 전투 지속\n"
            "평시엔 CEC 협동이 우세하나, 기함이 조기 격침되는 고강도 포화에서 강건성이 드러납니다.\n"
            "기본값 OFF — 기존 결과와 동일 (실험적 기능)"
        )

        # v17.1: RAS 탄약 재보급 (지속 전장 전용)
        self.chk_ras_rearm = QCheckBox("RAS 탄약 재보급 (실험적)")
        self.chk_ras_rearm.setChecked(False)
        self.chk_ras_rearm.setToolTip(
            "지속 전장 모드에서 군수지원함(AOE·AO)이 소강기에 소진된 함정의 주요 SAM(SM-3/6/2)을 재장전합니다.\n"
            "  · 위협(적 대함미사일) 접근 시 중단 — 붙어서 재장전 불가, 소강기에만 발동\n"
            "  · 탄약 화물 유한 — 장기전에서 결국 소진(무한 재보급 아님)\n"
            "  · 단발 교전에는 영향 없음 — 장기 지속 전장에서만 발현\n"
            "기본값 OFF — 기존 결과와 동일 (실험적 기능)"
        )

        self.chk_ship_evasion = QCheckBox("함정 회피 기동")
        self.chk_ship_evasion.setChecked(True)
        self.chk_ship_evasion.setToolTip(
            "적 대함미사일이 15km 이내 접근 시\n"
            "아군 함정이 지그재그 회피 기동으로 침로를 바꿉니다.\n"
            "레이더 OFF 전술과 짝을 이룹니다 — 레이더를 끈 동안 함정이 이동해야\n"
            "적 대방사미사일이 낡은 조준 좌표로 유도돼 빗나갑니다(방사 중단 + 침로 변경).\n"
            "회피 기동만 켜면 교전 기하가 흐트러져 요격률이 다소 떨어집니다(기동의 대가)."
        )

        self.chk_radar_off = QCheckBox("레이더 OFF 전술")
        self.chk_radar_off.setChecked(True)
        self.chk_radar_off.setToolTip(
            "적 대방사미사일(ARM)이 탐지 범위 내 진입 시\n"
            "레이더를 8초간 꺼서 ARM의 유도 신호를 차단합니다.\n"
            "레이더 OFF 중에는 신규 위협 탐지 불가 (기존 추적은 유지).\n"
            "OFF하지 않으면 ARM이 레이더를 직격할 수 있습니다."
        )

        # v16.4: 분산해양작전(DMO)
        self.chk_dmo = QCheckBox("분산해양작전 DMO")
        self.chk_dmo.setChecked(False)
        self.chk_dmo.setToolTip(
            "함대를 광역 분산 배치(약 80km 반경)해 적의 집중 포화 표적화를 회피합니다.\n"
            "  · 이득: 적 대함미사일이 접근축 상 일부 함정에만 집중 → 멀리 분산된 함정은 안전\n"
            "  · 대가: 함정 간 거리가 멀어져 협동방어(CEC) 상호 엄호 약화 — 개별 함정 피격 위험↑\n"
            "대량 포화에는 유리하나 소수 정밀위협에는 불리한 시나리오 의존 전술입니다.\n"
            "기본값 OFF — 기존 결과와 동일 (선택 전술 옵션)"
        )

        # v16.6: 전자 좌표 기만
        self.chk_coord_decep = QCheckBox("전자 좌표 기만")
        self.chk_coord_decep.setChecked(False)
        self.chk_coord_decep.setToolTip(
            "함정 전자방해(ECM)로 적 레이더 화면상 함정 표시 위치를 교란합니다.\n"
            "적 대함미사일이 종말 단계에서 가짜 좌표로 유도돼 실제 함정과 빗나가며 명중률이 떨어집니다.\n"
            "기존 전자방해(탐지거리·Pk 감소)와 별개인 위치 기만 수단입니다.\n"
            "레이더 유도 대함미사일에만 적용(탄도·극초음속·대방사·어뢰는 무효).\n"
            "기본값 OFF — 기존 결과와 동일 (선택 전술 옵션)"
        )

        # v16.12: 적 무인기 군집(Swarm) 위협
        self.chk_drone_swarm = QCheckBox("무인기 군집 포화 (실험적)")
        self.chk_drone_swarm.setChecked(False)
        self.chk_drone_swarm.setToolTip(
            "적이 저가 자폭 드론 수십 대를 다축으로 동시 투입합니다.\n"
            "  · 개별 요격 강제 → 함대 SAM·CIWS 교전 채널·요격탄 급소모(비대칭 소모전)\n"
            "  · 요격 못한 드론은 기함으로 돌진 자폭\n"
            "  · '다방위 공격'과 병용 시 360° 포화로 효과가 극대화됩니다\n"
            "현재 적 편대에 자폭 드론 군집 약 40대를 추가합니다.\n"
            "기본값 OFF — 기존 결과와 동일 (실험적 기능)"
        )

        # v17.2: 지향성 에너지 무기(레이저·DEW)
        self.chk_laser_dew = QCheckBox("지향성 에너지 무기 레이저 (실험적)")
        self.chk_laser_dew.setChecked(False)
        self.chk_laser_dew.setToolTip(
            "레이저 장착함(정조대왕함·미 이지스·해안 C-RAM)이 근접 저속 표적을 조사(照射) 격추합니다.\n"
            "  · CIWS 동시교전 채널과 독립된 경로 — 채널 포화(드론 군집)를 별도로 완화\n"
            "  · 표적당 조사시간(dwell)이 필요해 사실상 1채널 — 동시 다표적엔 약함\n"
            "  · 대상 제한: 드론·자폭정·아음속 순항미사일만(초음속·탄도·극초음속 무효)\n"
            "  · 유효 교전거리 약 5km, 발당 비용 극소(전력만 소모)\n"
            "【검증 결과 — 켜도 결과가 거의 바뀌지 않습니다】\n"
            "저속 드론은 함포(약 23km)·함대공 미사일이 훨씬 먼 거리에서 먼저 격추해\n"
            "5km 레이저 교전권까지 도달하지 못하고, 아음속 대함미사일은 5km를 통과하는\n"
            "시간이 조사에 부족합니다. 실제 함정 레이저도 아직 드론 방어의 주력이 아니므로\n"
            "이 결과 자체가 현실에 부합합니다. 메커니즘 자체는 정확히 동작합니다.\n"
            "기본값 OFF — 기존 결과와 동일 (실험적 기능)"
        )

        # v16.7: 기뢰전(MIW)
        self.chk_mine_threat = QCheckBox("기뢰전 위협")
        self.chk_mine_threat.setChecked(False)
        self.chk_mine_threat.setToolTip(
            "작전 해역(협수로·항만 입구)의 기뢰 위협에 함정이 노출됩니다.\n"
            "진입 시 함정별로 확률적 기뢰 접촉을 판정 — 계류·해저감응·자항 3종이 차등 피해를 줍니다.\n"
            "배수량 큰 함정일수록 감응 기뢰에 취약하고, 소형함은 회피가 유리합니다.\n"
            "기본값 OFF — 기존 결과와 동일"
        )
        self.chk_minesweeping = QCheckBox("소해 지원 (기뢰 접촉 경감)")
        self.chk_minesweeping.setChecked(False)
        self.chk_minesweeping.setToolTip(
            "소해함·무인 소해정(UUV)의 소해 지원으로 안전 항로를 개척해 기뢰 접촉 확률을 약 60% 낮춥니다.\n"
            "기뢰전 위협이 켜져 있을 때만 효과가 있습니다."
        )

        # v16.12: 무인 함정(USV·UUV) 편성
        self.chk_unmanned = QCheckBox("무인 함정 USV·UUV")
        self.chk_unmanned.setChecked(False)
        self.chk_unmanned.setToolTip(
            "아군 함대에 무인 수상정(USV)·무인 잠수정(UUV)을 전방 피켓으로 편성합니다.\n"
            "  · UUV: 소해(기뢰 접촉 경감) + 전방 대잠 탐지 확장\n"
            "  · USV: RAM 근접 점방어 + 전방 대함 탐지 확장\n"
            "  · 무인이라 손실 시 인명피해 0 (아군 손실과 분리 집계)\n"
            "기본값 OFF — 기존 결과와 동일"
        )

        # v10.7: 전술 의사결정 모드
        self.chk_tactical = QCheckBox("전술 의사결정 모드")
        self.chk_tactical.setChecked(False)
        self.chk_tactical.setToolTip(
            "v10.7 — 전술 의사결정 모드 (워게임 / 훈련용).\n"
            f"매 {30}초 구간마다 시뮬레이션이 일시 정지됩니다.\n"
            "  · 현재 위협 현황 + 아군 함정 상태 표시\n"
            "  · 다음 구간 무기 우선순위 (SM-2 / SM-6 / ESSM / 자동) 선택\n"
            "  · 살보 수 결정 (1~3발) → 확인 후 재개\n"
            "MC 분석에는 적용되지 않습니다 (단일 시뮬 전용)."
        )

        # 적 편대 전술 기동
        tactics_row = QHBoxLayout()
        lbl_tactics = QLabel("적 전술 기동:")
        lbl_tactics.setStyleSheet(f"color:{C_SUBTEXT}; font-size:13px;")
        self.cmb_enemy_tactics = NoScrollComboBox()
        self.cmb_enemy_tactics.addItems(['없음', 'V자 대형', '포위 기동'])
        self.cmb_enemy_tactics.setToolTip(
            "없음: 기본 분산 접근\n"
            "V자 대형: 선두 1기 + 양익 전개\n"
            "포위 기동: 전방위 동시 포위 (다방위 강화)"
        )
        tactics_row.addWidget(lbl_tactics)
        tactics_row.addWidget(self.cmb_enemy_tactics, stretch=1)

        # 적 전술 AI (채널 포화 / 시차 공격 / 약점 공략)
        ai_tactic_row = QHBoxLayout()
        lbl_ai_tactic = QLabel("전술 AI:")
        lbl_ai_tactic.setStyleSheet(f"color:{C_SUBTEXT}; font-size:13px;")
        self.cmb_ai_tactic = NoScrollComboBox()
        self.cmb_ai_tactic.addItems(['없음', '채널 포화', '시차 공격', '약점 공략', '적응형(자동)'])
        self.cmb_ai_tactic.setToolTip(
            "없음: 기본 동시 접근\n"
            "채널 포화: 아군 교전 채널 수 ×1.5 위협 자동 증폭 — 방어망 과부하\n"
            "시차 공격: 고속(탄도·HGV) 선발 → 채널 소모 → 순항미사일 후속 (+30~60초)\n"
            "약점 공략: 모든 위협이 단일 방향 집중 접근 — 레이더 사각 공략\n"
            "적응형(자동): 적이 교전 중 요격률·채널 포화를 보고 포화↔분산을 실시간 전환"
        )
        ai_tactic_row.addWidget(lbl_ai_tactic)
        ai_tactic_row.addWidget(self.cmb_ai_tactic, stretch=1)

        for chk in [self.chk_cec, self.chk_multibearing,
                    self.chk_cec_jammed, self.chk_autonomous,
                    self.chk_ras_rearm,
                    self.chk_ship_evasion, self.chk_radar_off,
                    self.chk_dmo, self.chk_coord_decep, self.chk_drone_swarm,
                    self.chk_laser_dew,
                    self.chk_mine_threat,
                    self.chk_minesweeping, self.chk_unmanned, self.chk_tactical]:
            _wire_chk_color(chk, 13)
            defl.addWidget(chk)
        defl.addLayout(tactics_row)
        defl.addLayout(ai_tactic_row)

        # 시뮬 시드 — 숨김 (항상 랜덤)
        self.spn_sim_seed = NoScrollSpinBox()
        self.spn_sim_seed.setRange(0, 99999)
        self.spn_sim_seed.setValue(0)
        self.spn_sim_seed.hide()

        # ── 공격 임무 옵션 (v9.3) ─────────────────────────────────────────────
        # v13.06.02: 패널 숨김 — 재고는 기본값 고정 운용. 위젯 객체는 cfg 읽기용으로
        # 유지(self 참조로 GC 방지)하되 설정창에는 노출하지 않는다.
        grp_strike = QGroupBox("⚔️ 공격 임무 (아군 대함 공격)")
        self._grp_strike = grp_strike   # GC 방지 — 화면엔 추가 안 함
        strl = QFormLayout(grp_strike)
        strl.setSpacing(6)

        self.chk_strike = QCheckBox("공격 임무 활성화")
        self.chk_strike.setChecked(True)
        _wire_chk_color(self.chk_strike, 13)
        self.chk_strike.setToolTip(
            "ON: 아군 함정이 탐지 범위 내 적 수상함을 해성·하푼으로 자동 공격합니다.\n"
            "OFF: 방어 전용 모드 (공격 임무 비활성화)."
        )
        strl.addRow("", self.chk_strike)

        self.spn_haesong2 = NoScrollSpinBox()
        self.spn_haesong2.setRange(0, 32); self.spn_haesong2.setValue(8)
        self.spn_haesong2.setToolTip("함정당 해성-II 재고. 기본 8발.")
        strl.addRow("해성-II 재고 (함당)", self.spn_haesong2)

        self.spn_harpoon = NoScrollSpinBox()
        self.spn_harpoon.setRange(0, 16); self.spn_harpoon.setValue(4)
        self.spn_harpoon.setToolTip("함정당 하푼 Block II 재고. 기본 4발.")
        strl.addRow("하푼 재고 (함당)", self.spn_harpoon)

        # v9.4: 현무-4 지상 발사 재고
        self.spn_hyunmoo4 = NoScrollSpinBox()
        self.spn_hyunmoo4.setRange(0, 20); self.spn_hyunmoo4.setValue(0)
        self.spn_hyunmoo4.setToolTip(
            "현무-4 ASBM 지상 발사 재고. 기본 0발 (비활성).\n"
            "사거리 800km, Mach 8~10 종말 속도 — 적 SAM 요격 극히 어려움.\n"
            "60초 간격으로 1발씩 발사 (재보급 준비 시간)."
        )
        strl.addRow("현무-4 재고 (지상 발사)", self.spn_hyunmoo4)
        grp_strike.hide()   # v13.06.02: 패널 숨김 (재고 기본값 8/4/0 고정 운용)

        # v9.11: 이지스 어쇼어 + THAAD 지상 BMD
        grp_bmd = QGroupBox("🛡 지상 BMD 자산")
        bmdl = QFormLayout(grp_bmd)
        bmdl.setSpacing(6)

        self.chk_ashore = QCheckBox("이지스 어쇼어 연동")
        self.chk_ashore.setToolTip(
            "성주 해군기지 이지스 어쇼어 SM-3 Block IIA 연동.\n"
            "탄도미사일·HGV를 중간단계(고도 ≥ 40km)에서 선제 요격.\n"
            "함정 SM-3보다 먼저 교전 — 함정 SM-3은 소진 시 백업만."
        )
        bmdl.addRow("", self.chk_ashore)
        _wire_chk_color(self.chk_ashore, 13)


        self.chk_thaad = QCheckBox("THAAD 연동 (성주 기지)")
        self.chk_thaad.setToolTip(
            "성주 기지 THAAD(終末高高度防禦) 연동 (美 육군 운용).\n"
            "탄도미사일·HGV 종말단계(고도 10~150km)를 hit-to-kill 요격.\n"
            "어쇼어 SM-3 → THAAD → 함정 SM-3 순으로 교전."
        )
        bmdl.addRow("", self.chk_thaad)
        _wire_chk_color(self.chk_thaad, 13)

        self.chk_lsam = QCheckBox("L-SAM 연동 (실험적)")
        self.chk_lsam.setToolTip(
            "한국형 미사일방어(KAMD) 상층 요격체계 L-SAM 연동.\n"
            "탄도미사일·HGV를 종말 상층(고도 40~70km, 사거리 150km)에서 요격.\n"
            "THAAD와 PAC-3 사이를 메우는 계층 — 3단 hit-to-kill.\n"
            "기본값 OFF — 기존 결과와 동일 (실험적 기능)"
        )
        bmdl.addRow("", self.chk_lsam)
        _wire_chk_color(self.chk_lsam, 13)

        self.chk_chungung = QCheckBox("천궁-II 연동 (실험적)")
        self.chk_chungung.setToolTip(
            "한국형 미사일방어(KAMD) 하층 종말 점방어 천궁-II 연동.\n"
            "탄도미사일·HGV를 종말 하층(고도 3~20km, 사거리 20km)에서 요격.\n"
            "상층 요격을 누출한 위협에 대한 최후 방어선 — 유도탄 단가가 낮아 소모전에 유리.\n"
            "기본값 OFF — 기존 결과와 동일 (실험적 기능)"
        )
        bmdl.addRow("", self.chk_chungung)
        _wire_chk_color(self.chk_chungung, 13)

        self.chk_patriot = QCheckBox("패트리엇 PAC-3 연동 (실험적)")
        self.chk_patriot.setToolTip(
            "한·미 연합 종말 중층 요격체계 패트리엇 PAC-3 MSE 연동.\n"
            "탄도미사일·HGV를 종말 중층(고도 2~25km, 사거리 60km)에서 hit-to-kill 요격.\n"
            "L-SAM(상층)과 천궁-II(하층 점방어) 사이를 메우는 계층.\n"
            "기본값 OFF — 기존 결과와 동일 (실험적 기능)"
        )
        bmdl.addRow("", self.chk_patriot)
        _wire_chk_color(self.chk_patriot, 13)

        self.chk_bal_descent = QCheckBox("탄도탄 종말 강하")
        self.chk_bal_descent.setToolTip(
            "탄도미사일의 종말 강하 궤적을 교전에 반영.\n"
            "끄면 탄도탄이 중간단계 고도(화성-15 기준 1200km)를 유지한 채 돌입해\n"
            "종말 요격층(THAAD·L-SAM·패트리엇·천궁-II)이 교전창에 진입하지 못한다.\n"
            "켜면 정점 → 종말 급강하로 다층 방어가 단계별로 순차 교전.\n"
            "기본값 ON — 탄도탄의 실제 비행 물리 (끄면 비교·디버그용)"
        )
        self.chk_bal_descent.setChecked(True)
        bmdl.addRow("", self.chk_bal_descent)
        _wire_chk_color(self.chk_bal_descent, 13)


        # ── C&D 시간 설정 (고정값) ────────────────────────────────────────
        grp_cd = QGroupBox("⏱️ C&&D 시간 설정")
        cdl = QHBoxLayout(grp_cd)
        cdl.setSpacing(16)
        lbl_cd_fixed = QLabel("C&&D  10초  /  확인  3초  (고정)")
        lbl_cd_fixed.setStyleSheet(f"color:{C_SUBTEXT}; font-size:13px;")
        cdl.addWidget(lbl_cd_fixed)

        # ── 시뮬레이션 모드 선택 (고급 열에 포함) ────────────────────────
        grp_mc = QGroupBox("📊 시뮬레이션 모드")
        mcl = QVBoxLayout(grp_mc)
        mcl.setContentsMargins(8, 8, 8, 10)
        mcl.setSpacing(6)
        lbl_mode = QLabel("정밀도:")
        lbl_mode.setStyleSheet(f"color:{C_SUBTEXT}; font-size:13px;")
        self.cmb_sim_mode = NoScrollComboBox()
        self.cmb_sim_mode.addItems(["⚡ 빠름  (5,000회)", "📊 표준  (10,000회)", "🔬 정밀  (100,000회)"])
        self.cmb_sim_mode.setCurrentIndex(1)
        self.cmb_sim_mode.setFixedHeight(32)
        self.cmb_sim_mode.setStyleSheet(f"""
            QComboBox {{
                background: #1c2128; color: #e6edf3;
                border: 1px solid #444c56; border-radius: 4px;
                font-size: 14px; padding: 2px 8px;
            }}
            QComboBox QAbstractItemView {{
                background: #161b22; color: #e6edf3;
                selection-background-color: #3498db;
            }}
        """)
        lbl_mode_hint = QLabel()
        lbl_mode_hint.setStyleSheet(f"color:{C_SUBTEXT}; font-size:12px;")

        lbl_npp = QLabel("Sobol 포인트당 반복:")
        lbl_npp.setStyleSheet(f"color:{C_SUBTEXT}; font-size:13px;")
        self.spn_sobol_npp = NoScrollSpinBox()
        self.spn_sobol_npp.setRange(1, 10)
        self.spn_sobol_npp.setValue(3)
        self.spn_sobol_npp.setFixedWidth(72)
        self.spn_sobol_npp.setFixedHeight(28)
        self.spn_sobol_npp.setToolTip(
            "Sobol 분석 시 각 파라미터 조합을 몇 번 반복해 평균낼지.\n"
            "1회: 빠름 (~32,768회) / 3회: 권장 (~98,304회) / 5회: 고정밀 (~163,840회)\n"
            "확률적 시뮬레이션의 노이즈를 √K배 줄여 민감도 지수 신뢰도 향상.\n"
            "정밀 모드 선택 시에만 사용됩니다.")
        self.spn_sobol_npp.setStyleSheet(
            f"background:#1c2128; color:#e6edf3; border:1px solid #444c56;"
            f" font-size:13px; padding:0 18px 0 8px;")
        self.spn_sobol_npp.setEnabled(False)

        lbl_mode_hint = QLabel()
        lbl_mode_hint.setStyleSheet(f"color:{C_SUBTEXT}; font-size:12px;")
        self._lbl_sobol_total = QLabel()
        self._lbl_sobol_total.setStyleSheet(f"color:{C_SUBTEXT}; font-size:12px;")

        def _update_sobol_total():
            npp = self.spn_sobol_npp.value()
            total = 32_768 * npp
            self._lbl_sobol_total.setText(f"(총 ~{total:,}회)")

        def _update_mode_hint(idx):
            hints = [
                "LHS 샘플링  •  CVaR 분석  •  스트레스 테스트 (셀당 300회)",
                "LHS 샘플링  •  CVaR 분석  •  스트레스 테스트 (셀당 500회)",
                "LHS 샘플링  •  CVaR  •  스트레스 (셀당 3,000회)  •  Sobol 민감도",
            ]
            lbl_mode_hint.setText(hints[idx])
            is_precision = (idx == 2)
            # Sobol 반복은 정밀 모드 전용 — 표준·빠름에선 행 전체 숨김
            self.spn_sobol_npp.setEnabled(is_precision)
            lbl_npp.setVisible(is_precision)
            self.spn_sobol_npp.setVisible(is_precision)
            self._lbl_sobol_total.setVisible(is_precision)
            lbl_npp.setStyleSheet(f"color:{C_TEXT}; font-size:13px;")

        self.cmb_sim_mode.currentIndexChanged.connect(_update_mode_hint)
        self.spn_sobol_npp.valueChanged.connect(_update_sobol_total)
        _update_mode_hint(1)
        _update_sobol_total()

        row1 = QHBoxLayout()
        row1.addWidget(lbl_mode)
        row1.addWidget(self.cmb_sim_mode)
        row1.addStretch()
        mcl.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(lbl_npp)
        row2.addWidget(self.spn_sobol_npp)
        row2.addWidget(self._lbl_sobol_total)
        row2.addStretch()
        mcl.addLayout(row2)
        mcl.addWidget(lbl_mode_hint)

        self.chk_test_mode = QCheckBox("⚡ 테스트 모드 (MC 10회, 빠른 완료)")
        self.chk_test_mode.setToolTip(
            "MC 10회·LHS 10회·스트레스 셀당 3회로 단축 실행.\n"
            "동작 확인용 — 통계적 의미 없음.")
        _wire_chk_color(self.chk_test_mode)
        mcl.addWidget(self.chk_test_mode)

        self.btn_run = QPushButton("🚀  시뮬레이션 실행")
        self.btn_run.setFixedHeight(36)
        self.btn_run.setFont(QFont('Malgun Gothic', 13))
        self.btn_run.setStyleSheet(
            f"QPushButton{{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,"
            f"stop:0 #4aabe8,stop:1 {C_ACCENT});color:white;border:none;"
            f"border-radius:8px;font-weight:bold;}}"
            f"QPushButton:hover{{background:qlineargradient(x1:0,y1:0,x2:0,y2:1,"
            f"stop:0 #5bbaf0,stop:1 #2980b9);}}"
            f"QPushButton:pressed{{background:{C_ACCENT};}}"
            f"QPushButton:disabled{{background:{C_BORDER};color:{C_SUBTEXT};}}"
        )
        self.btn_run.clicked.connect(self._run_sim)
        if not _V7_OK:
            self.btn_run.setEnabled(False)
        mcl.addWidget(self.btn_run)

        # 시나리오 저장/불러오기 (사용자 백로그 4) — 현재 설정 전체를 JSON으로 저장·복원.
        # _build_cfg_from_ui/_restore_cfg 인프라 재사용(설정 재현·공유).
        _scn_row = QHBoxLayout()
        self.btn_save_scenario = QPushButton("💾 시나리오 저장")
        self.btn_load_scenario = QPushButton("📂 시나리오 불러오기")
        for _b in (self.btn_save_scenario, self.btn_load_scenario):
            _b.setFixedHeight(26)
            _b.setFont(QFont('Malgun Gothic', 10))
            _b.setStyleSheet(
                f"QPushButton{{background:{C_PANEL};color:{C_TEXT};"
                f"border:1px solid {C_BORDER};border-radius:6px;}}"
                f"QPushButton:hover{{background:{C_BORDER};}}")
            _scn_row.addWidget(_b)
        self.btn_save_scenario.setToolTip("현재 설정(편대·날씨·모든 토글)을 JSON 파일로 저장합니다.")
        self.btn_load_scenario.setToolTip("저장한 JSON 시나리오를 불러와 설정을 복원합니다.")
        self.btn_save_scenario.clicked.connect(self._save_scenario)
        self.btn_load_scenario.clicked.connect(self._load_scenario)
        mcl.addLayout(_scn_row)

        # ── 하단 섹션 hover 팝업 일괄 설치 ──────────────────────────────
        _bot_popup = _HoverPopup(self)
        for _g in [grp_env, grp_def, grp_bmd, grp_cd, grp_ac, grp_mc]:
            _install_section_popups(_g, _bot_popup)

        # ── 섹션 조립 ────────────────────────────────────────────────────
        _sections = [
            ("환경",     [grp_env],                        False),
            ("방어전술", [grp_def],                          False),
            ("항공자산", [grp_ac],                          False),
            ("고급",     [grp_bmd, grp_cd, grp_mc], False),
        ]
        self._sec_contents:   list = []
        self._sec_groups_ref: list = []
        for sec_title, groups, expanded in _sections:
            content = _make_content(*groups)
            content.setVisible(expanded)
            hdr = _CfgSectionHeader(sec_title, content, expanded)
            layout.addWidget(hdr)
            layout.addWidget(content)
            self._sec_contents.append(content)
            self._sec_groups_ref.append(list(groups))

        if _V7_OK and self.cmb_fleet.count():
            self._update_fleet_detail(self.cmb_fleet.currentText())

        layout.addStretch()
        scroll.setWidget(inner)

        # ── 고정 하단 영역 (실행 버튼만) ─────────────────────────────────
        bottom = QWidget()
        bottom.setStyleSheet(
            f"background:{C_PANEL}; border-top: 1px solid #2a3a4a;")
        bottom_layout = QVBoxLayout(bottom)
        bottom_layout.setContentsMargins(8, 6, 8, 8)
        bottom_layout.setSpacing(6)

        if not _V7_OK:
            err_lbl = QLabel(f"⚠️ engine_combat 로드 실패\n{_V7_ERR}")
            err_lbl.setStyleSheet(f"color:{C_RED}; font-size:15px;")
            err_lbl.setWordWrap(True)
            bottom_layout.addWidget(err_lbl)
            self.btn_run.setEnabled(False)

        self._cfg_bottom           = bottom
        self._cfg_container_layout = container_layout
        self._cfg_inner_layout     = layout   # 스크롤 내부 레이아웃 (설정 위젯이 여기 들어가야 함께 스크롤됨)
        container_layout.addWidget(scroll, stretch=1)
        container_layout.addWidget(bottom)
        return container
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
    _SHIP_DISPLAY = {
        'KDX-III-B2': '이지스 구축함 KDX-III Batch II (정조대왕급)',
        'KDX-III-B1': '이지스 구축함 KDX-III Batch I (세종대왕급)',
        'KDX-II':     '구축함 (KDX-II 충무공이순신급)',
        'FFX-I':      '호위함 FFX Batch I (인천급)',
        'FFX-II':     '호위함 FFX Batch II (대구급)',
        'FFX-III':    '호위함 FFX Batch III (충남급)',
    }
    _FRIENDLY_PRESET_TIPS = {
        '단독 작전':
            '정조대왕함(KDX-III-B2) 1척 단독.\n'
            'SM-3/SM-6/SM-2/ESSM/RAM/CIWS 全 탑재.\n'
            '단일 함 기준 성능 평가 및 교전 한계 측정.',
        '기동전단 기본':
            '이지스(KDX-III-B2) × 1 + 구축함(KDX-II) × 1 + 호위함(FFX-II) × 1.\n'
            '3척 균형 편성. 대공·대잠·대함 균형 방어력 기본 평가.',
        'BMD 중점':
            '이지스(KDX-III-B2) × 1 + 이지스(KDX-III-B1) × 1.\n'
            'SM-3 BMD 채널 2배 — 탄도미사일·HGV 위협 특화 방어.\n'
            '탄도 포화 시나리오와 연계 권장.',
        '대잠 중점':
            '이지스(KDX-III-B2) × 1 + 호위함(FFX-II) × 2.\n'
            '홍상어(ASROC)·청상어(경어뢰)·소나 재고 집중.\n'
            '잠수함 복합 위협 특화 편성.',
        '대잠전단':
            '이지스 × 1 + 호위함 × 2 + KSS-II 잠수함 × 2.\n'
            '아군 잠수함 포함 입체 대잠전. 수중 압박+수면 대잠 협공.',
        '최대 편대':
            '이지스 × 2 + 구축함(KDX-II) × 2 + 호위함(FFX) × 2, 총 6척.\n'
            '한국 해군 동원 가능 최대 전력 조합.\n'
            '종합 방어력 최대 평가. 항모전단급 위협과 연계 권장.',
        '이지스 기동전단':
            '정조대왕함 중심 실전 교리 기반 편성.\n'
            'KDX-III-B2 × 1 + KDX-II × 2 + FFX × 2 + AOE 보급함.\n'
            '해군 1·2함대 통합 파견 기준 편성.',
        '이지스 기동전단 (강화)':
            '전시 확장 편성.\n'
            'KDX-III-B2 × 1 + KDX-III-B1 × 1 + KDX-II × 2 + FFX × 2 + AOE.\n'
            '탄도 위협 증가 시 SM-3 채널 보강형.',
        '전 이지스 기동전단':
            '이지스 4척 완전 편성 (B2 × 1 + B1 × 3).\n'
            'SM-3 BMD 채널 최대화 — 최강 방공 체계.\n'
            '항모전단 호위 또는 탄도 포화 방어 전용.',
        '독도함 상륙전단':
            '독도함(LPH-6111) 중심 상륙작전 편성.\n'
            'UH-60 헬기 기반 대잠 특화 + 연안 화력 지원.\n'
            '함재 항공 전력(AW-159 × 4) 포함.',
        '동해 해역방어 (1함대)':
            '1함대 교리 기반 동해 연안 방어 편성.\n'
            'KDX-II × 1 + FFX-I × 2 + PKG(유도탄 고속함) × 4 + PCC × 2.\n'
            '북한 잠수함·탄도 위협 중심. 동해 수온약층 환경 연계 권장.',
        '서해 해역방어 (2함대)':
            '2함대 교리 기반 서해 연안 방어 편성.\n'
            'FFX-I × 2 + PKG × 4 + PCC × 2.\n'
            '천해(평균 44m) 환경 특화. NLL 도발 대응 기준 편성.',
        '한미 기동전단 기본':
            '한미 연합 기본 편성.\n'
            'KDX-III-B2 × 1 + DDG-51(알레이버크) × 2 + KDX-II × 1 + FFX × 2.\n'
            'SPY-1D + AN/SPY-6 이중 이지스 체계.',
        '한미 기동전단 강화':
            '한미 연합 강화 편성.\n'
            '한국 이지스 × 2 + DDG-51 × 2 + CG-47(타이콘데로가) × 1 + KDX-II × 2 + AOE.\n'
            'SM-3 BMD 채널 5개 — 항모전단 교전 대응 가능.',
        '한미 항모전단 지원':
            '한미 항모전단 완전 편성.\n'
            'CVN(니미츠급) × 1 + DDG-51 × 3 + CG-47 × 1 + 한국 이지스 × 1 + KDX-II × 2.\n'
            '항모 전력 포함 최강 연합 방어. 항모 킬 체인 방어 시나리오 권장.',
    }
    _ENEMY_PRESET_TIPS = {
        'A2/AD 항공 포화':
            'J-16 × 6 + H-6 × 4.\n'
            '장거리 공대함미사일(YJ-12·YJ-63) 포화 공격.\n'
            'SM-2·RAM 재고 소모 유도, 이지스 교전 채널 포화.',
        '항모 킬 체인':
            'DF-21D (대함 탄도) × 4 + DF-17 (HGV) × 4 + YJ-21 (극초음속 대함) × 4\n'
            '+ J-20 (스텔스) × 3.\n'
            '스텔스로 방공망 혼란 → 탄도+극초음속으로 방어 돌파.\n'
            'SM-3 BMD 필수. 중난이도~고난이도.',
        '수상함 편대전':
            '055형 × 1 + 052D × 2 + 022형 미사일 고속정 × 4.\n'
            'YJ-18 초음속 + YJ-12 대함미사일 집중 포화.\n'
            'SM-2·ESSM·CIWS 재고 한계 테스트.',
        '대잠 복합':
            '093형 (핵잠) × 1 + 039형 (재래식) × 1.\n'
            '어뢰 + 잠대함 순항미사일 동시 위협.\n'
            '대잠 헬기·패트리엇 소나 성능 검증.',
        'BMD 탄도 포화':
            'KN-23 × 6 + DF-15 × 6 + DF-21D × 4 + DF-17 × 4.\n'
            'QBM(기동)~MRBM~HGV 계층 혼합 — SM-3 채널 연속 소진.\n'
            '상층이 소진되며 하위 계층으로 누출 — BMD 다층 요격 검증.',
        '전면전 포화':
            'J-20 × 4 + J-16 × 4 + DF-21D × 4 + DF-17 × 4 + 055형 × 2 + 093형 × 2.\n'
            '공중·탄도·수상·수중 전 영역 동시 위협.\n'
            '이지스 다층 방어 한계 종합 검증.',
        '북한 탄도 포화':
            'KN-23 × 3 + 화성-15 × 1 + 화살-2 × 2.\n'
            '북한 교리 기반 탄도(QBM)+ICBM급+순항 병행 공격.\n'
            'THAAD+SM-3 BMD 연계 성능 검증.',
        '러시아 극초음속':
            '킨잘 × 2 + 지르콘 × 2 + Kh-101 × 2.\n'
            '극초음속 탄도·순항 2종 + 스텔스 순항.\n'
            'SM-3/6 연속 소진 — 재고 복합 소모 최고.',
        '잠수함 복합 포화':
            '039형 × 3 + 093형 × 1.\n'
            '다중 잠수함 동시 위협 — 대잠 전력 채널 한계 테스트.\n'
            '어뢰+잠대함 미사일 복합 압박.',
        '랴오닝 항모전단':
            '랴오닝(CV-16) + 055형 × 1 + 052D × 2 + 054A × 2 + 093형 × 1.\n'
            'PLAN 1항모전단. 함재기 Su-33/J-15 탑재.\n'
            '항모 킬 체인 실전 검증 최고 난이도.',
        '산둥 항모전단':
            '산둥(CV-17) + 055형 × 1 + 052D × 3 + 039형 × 1.\n'
            'PLAN 2항모전단. 랴오닝보다 함재기 탑재량 증가.\n'
            '전투 반경 확대, 항공 전력 더 강함.',
        '푸젠 항모전단':
            '푸젠(CV-18) + 055형 × 2 + 052D × 3 + 093형 × 2.\n'
            'PLAN 3항모전단. EMALS 전자기 사출기 탑재, 출격 주기 최단.\n'
            '중국 최강 항모전단. 방어 한계 실전 검증.',
        '북한 포화 공격 (20발)':
            'KN-23 × 8 + KN-24 × 4 + 화성-12 × 4 + 화성-15 × 4.\n'
            '중규모 포화 공격 (총 20발 동시 발사).\n'
            'SM-3·SM-2 재고 복합 소모 — 이지스 1~2척 방어 한계.',
        '북한 포화 공격 (40발)':
            'KN-23 × 16 + KN-24 × 8 + 화성-12 × 8 + 화성-15 × 4 + 화성-18 × 4.\n'
            '전면전 수준 포화 공격 (총 40발).\n'
            '채널 완전 포화 — 이지스 다층 방어 한계 실험용.',
        '중국 3축 동시 공격':
            'J-16 × 2 + 052D × 2 + 039형 × 2.\n'
            '항공·수상·수중 3축 동시 압박 (중간 난이도).\n'
            '대공·대함·대잠 전력이 동시에 요구됨.',
        '입체 포화 (최강)':
            'J-20 × 2 + DF-17 × 1 + 055형 × 1 + 093형 × 1.\n'
            '공중·HGV·수상·수중 4차원 동시 — 최고 난이도.\n'
            '방어 한계 종합 실험용.',
        '북한 입체 공격':
            'MiG-29 × 2 + KN-23 × 2 + 신포급(기습) × 1.\n'
            '항공·탄도·잠수함 3축 — 실전 교리 기반 북한 전면 도발.\n'
            '탄도 방어 + 대잠 + CAP 동시 가동.',
        '러시아 해군 입체':
            'Tu-22M3 백파이어 × 1 + 슬라바급 × 1 + 킬로급 × 1.\n'
            '수중·수상·공중 3축 러시아 극초음속 복합.\n'
            'SM-3 채널 집중 소모 — 높은 난이도.',
        '북한 잠수함 선제 기습':
            '신포급(기습) × 2 + 039형 × 3.\n'
            '수온약층 내 잠복 → 기습 어뢰+순항미사일 동시 발사.\n'
            '선제 기습 → 대잠망 노출 전 타격, 대응 시간 극히 짧음.',
        '북한 잠수함 기습 (소형)':
            '신포급(기습) × 1 + 039형 × 2.\n'
            '서해 천해 소형 잠수함 기습. 탐지 극히 어려움.\n'
            '수심 제한 해역(서해 44m 평균) 천해 대잠 테스트.',
        '이어도 방어전':
            'J-10C × 3 + 054A × 2 + 039형 × 1.\n'
            '제주 서남방 이어도 기준점 방어 — 대한해협 서수도 접근.\n'
            '중국 이어도 분쟁 시나리오. 해협 설정과 연계 권장.',
        '대한해협 통과 저지':
            '022형 고속정 × 6 + J-11B × 2 + 039형 × 1.\n'
            '동·서수도 동시 돌파 시도 — 고밀도 수상함 협착 통과.\n'
            '해협 통과 방향 설정 필수. 협착 기동 패널티 적용.',
        '쓰시마 봉쇄 돌파':
            'Tu-22M3 × 2 + 킬로급 × 2 + 슬라바급 × 1.\n'
            '러시아 동수도 강제 통과 (일본해→남해 전략 이동).\n'
            'Kh-32 고고도 초음속 + Kalibr 대함 + P-1000 복합.',
    }
    def _friendly_preset_tooltip(self, name: str) -> str:
        desc  = self._FRIENDLY_PRESET_TIPS.get(name, '')
        ships = V7_FLEET_PRESETS.get(name, [])
        lines = ([desc, ''] if desc else []) + ['편성:']
        for s in ships:
            disp = self._SHIP_DISPLAY.get(s['type'], s['type'])
            lines.append(f"  • {s['name']}  ({disp})")
        return '\n'.join(lines)
    def _enemy_preset_tooltip(self, name: str) -> str:
        desc    = self._ENEMY_PRESET_TIPS.get(name, '')
        threats = V7_ENEMY_FLEET_PRESETS.get(name, [])
        lines   = ([desc, ''] if desc else []) + ['위협 구성:']
        for t in threats:
            lines.append(f"  • {t['preset']}  ×{t['count']}")
        return '\n'.join(lines)
    def _update_fleet_detail(self, preset_name: str):
        pass  # hover 팝업으로 대체 — lbl_fleet_detail 제거됨
    def _update_enemy_row_tooltip(self, cmb: QComboBox, name: str):
        if not _V7_OK or name not in V7_ENEMY_DB:
            return
        cmb.setToolTip(self._enemy_tip(name))
    def _update_enemy_preset_detail(self, preset_name: str):
        pass  # hover 팝업으로 대체
    def _update_difficulty_tooltip(self, diff: str):
        if not _V7_OK or diff not in V7_RANDOM_CFG:
            return
        cfg = V7_RANDOM_CFG[diff]
        lo, hi = cfg['total_count']
        pool = ', '.join(cfg['pool'][:4]) + ('...' if len(cfg['pool']) > 4 else '')
        self.cmb_difficulty.setToolTip(
            f"[{diff}] 총 {lo}~{hi}대 | 최대 {cfg['max_types']}종\n풀: {pool}")
    @staticmethod
    def _enemy_tip(name: str) -> str:
        if not _V7_OK or name not in V7_ENEMY_DB:
            return ''
        e = V7_ENEMY_DB[name]
        mach = e['speed_ms'] / 340
        lines = [
            f"【{name}】",
            f"분류: {e.get('category','?')} | 종류: {e.get('type','?')}",
            f"속도: 마하 {mach:.1f}  |  RCS: {e['rcs_m2']}㎡",
        ]
        if e.get('missile_name'):
            lines.append(f"미사일: {e['missile_name']}")
            lines.append(f"  사거리 {e.get('missile_range_km','?')}km"
                         f"  |  속도 {e.get('missile_speed_ms','?')}m/s")
        if e.get('is_hgv'):
            lines.append("⚠ 극초음속 활공체 — SM-3만 요격 가능")
        if e.get('is_qbm'):
            lines.append("⚠ 저고도기동탄도 — SM-3 거의 무력화")
        sd = e.get('self_defense_pk', 0)
        if sd > 0:
            lines.append(f"자체방어 Pk: {sd:.0%}")
        return '\n'.join(lines)
    def _on_enemy_mode_changed(self, _idx=None):
        """적군 편대 모드 전환 시 관련 위젯 show/hide."""
        mode = self.cmb_enemy_mode.currentText()
        is_preset = mode == '프리셋'
        is_mixed  = mode == '혼합 시나리오'
        self._ep_preset_row.setVisible(is_preset)
        self._mixed_row.setVisible(is_mixed)
        self._rand_row.setVisible(mode == '랜덤')
        self._update_forecast_card()
    def _update_forecast_card(self):
        """'예상 전황' 카드 갱신 (실행 전 즉시 추정) — 하이브리드:
          ▸맑음 주간 + 룩업 정확값 있으면 룩업(최우선)
          ▸다른 날씨 or 룩업 없는 조합이면 학습 대리모델(forecast_model.pkl)로 날씨 반영 추정
          ▸모델 없으면 룩업 근사/데이터 없음 폴백(하위호환)
        순수 표시 — 엔진·시뮬·회귀에 영향 없음. JSON 없으면 카드 숨김."""
        if getattr(self, '_surrogate', None) is None \
                or not hasattr(self, '_prev_lbl_forecast'):
            return
        table = self._surrogate.get('table', {})
        ref_weather = self._surrogate.get('weather', '맑음 (주간)')
        n = self._surrogate.get('n', 0)

        mode = self.cmb_enemy_mode.currentText() if hasattr(self, 'cmb_enemy_mode') else ''
        # 조회 가능 조건: 적 편대 모드 == '프리셋' (혼합·랜덤은 편성 비결정)
        if mode != '프리셋':
            self._prev_lbl_forecast.setText(
                "적 편대를 '프리셋' 모드로 두면\n예상 승률·비용을 표시합니다.")
            return

        fleet  = self.cmb_fleet.currentText()          if hasattr(self, 'cmb_fleet') else ''
        enemy  = self.cmb_fleet_preset_e.currentText() if hasattr(self, 'cmb_fleet_preset_e') else ''
        weather = self.cmb_weather.currentText()        if hasattr(self, 'cmb_weather') else ''
        # v16.14.02: 직접 편성이면 프리셋 룩업 테이블에 없으므로 학습 모델 추정 경로만 사용
        # (프리셋 이름으로 우연히 룩업되는 오표시 방지).
        custom = getattr(self, '_fleet_custom', None)
        rec = None if custom else table.get(f'{fleet}|{enemy}')

        # ① 최우선: 맑음 주간 + 룩업 정확값
        if weather == ref_weather and rec is not None:
            self._render_forecast_lookup(rec, weather, ref_weather, n)
            return

        # ② 학습 대리모델 추정: 다른 날씨 또는 룩업 없는 조합 (직접 편성 포함)
        est = self._forecast_predict(fleet, enemy, weather)
        if est is not None:
            self._render_forecast_estimate(est, weather, custom=bool(custom))
            return

        # ③ 폴백: 룩업 있으면 맑음 근사, 없으면 데이터 없음
        if rec is not None:
            self._render_forecast_lookup(rec, weather, ref_weather, n)
        else:
            self._prev_lbl_forecast.setText("이 조합의 예상 데이터가 없습니다.")
    def _forecast_predict(self, fleet: str, enemy: str, weather: str) -> dict | None:
        """학습 대리모델로 (승률·임무점수·비용) 즉시 추정. 모델·특징화 부재 시 None."""
        model = getattr(self, '_forecast_model', None)
        if model is None or _forecast_featurize is None or not _V7_OK:
            return None
        try:
            # v16.14.02: 직접 편성이면 그 함급 리스트로, 아니면 프리셋에서 함급 추출.
            fc = getattr(self, '_fleet_custom', None)
            if fc:
                fleet_ships = [t for t, c in fc.items() for _ in range(int(c))]
            else:
                fleet_ships = [s['type'] for s in V7_FLEET_PRESETS.get(fleet, [])]
            if not fleet_ships:
                return None
            feat = _forecast_featurize(fleet_ships, enemy_preset=enemy,
                                       weather=weather).reshape(1, -1)
            models = model['models']
            win   = float(np.clip(models[0].predict(feat)[0], 0.0, 1.0))
            score = float(np.clip(models[1].predict(feat)[0], 0.0, 1.0))
            raw   = float(models[2].predict(feat)[0])
            cost  = float(np.expm1(raw)) if model.get('cost_is_log1p') else raw
            return {'win': win, 'score': score, 'cost': max(0.0, cost)}
        except Exception:
            return None
    def _render_forecast_lookup(self, rec: dict, weather: str, ref_weather: str, n: int):
        """프리셋 룩업(맑음 주간 MC 정확값) 렌더."""
        win  = rec.get('win_rate', 0) * 100
        draw = rec.get('draw_rate', 0) * 100
        loss = rec.get('loss_rate', 0) * 100
        score = rec.get('mean_friendly_score', 0) * 100
        cost  = rec.get('mean_cost')
        cpw   = rec.get('cost_per_win')
        cost_s = f"${cost/1e6:.1f}M" if cost else "—"
        cpw_s  = f"${cpw/1e6:.1f}M" if cpw else "승리 없음"
        lines = [
            f"승 {win:.0f}%   무 {draw:.0f}%   패 {loss:.0f}%",
            f"평균 임무점수 {score:.0f}%",
            f"평균 비용 {cost_s}  ·  승리당 {cpw_s}",
        ]
        if weather and weather != ref_weather:
            lines.append(f"※ {ref_weather} 기준 근사값")
        lines.append(f"참고 예상치 (MC {n}회·신뢰구간 없음)")
        self._prev_lbl_forecast.setText('\n'.join(lines))
    def _render_forecast_estimate(self, est: dict, weather: str, custom: bool = False):
        """학습 대리모델 추정 렌더 (승률만 예측 — 무·패는 합산 표시)."""
        win   = est['win'] * 100
        score = est['score'] * 100
        cost  = est['cost']
        cost_s = f"${cost/1e6:.1f}M" if cost else "—"
        cpw    = (cost / est['win']) if est['win'] > 0 else None
        cpw_s  = f"${cpw/1e6:.1f}M" if cpw else "승리 없음"
        src = "직접 편성 · " if custom else ""
        lines = [
            f"승 {win:.0f}%   (무·패 {100 - win:.0f}%)",
            f"평균 임무점수 {score:.0f}%",
            f"평균 비용 {cost_s}  ·  승리당 {cpw_s}",
            f"※ {src}{weather} 반영 학습 모델 추정",
        ]
        self._prev_lbl_forecast.setText('\n'.join(lines))
    def _update_mixed_scenario_detail(self, scenario_name: str):
        pass  # hover 팝업으로 대체
    def _save_scenario(self):
        """현재 설정 전체를 JSON 시나리오 파일로 저장(사용자 백로그 4). _build_cfg_from_ui 재사용 —
        편대·날씨·모든 토글이 그대로 직렬화된다(순수 dict). 설정 재현·공유용."""
        import json
        cfg = self._build_cfg_from_ui()
        path, _ = QFileDialog.getSaveFileName(
            self, "시나리오 저장", "시나리오.json", "시나리오 파일 (*.json)")
        if not path:
            return
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
            self._lbl_status.setText(f"💾 시나리오 저장됨: {os.path.basename(path)}")
        except Exception as e:
            QMessageBox.warning(self, "저장 실패", f"시나리오 저장 중 오류:\n{e}")
    def _load_scenario(self):
        """JSON 시나리오 파일을 불러와 설정 UI에 복원(_restore_cfg 재사용). 구버전 시나리오의
        누락 키는 _restore_cfg의 hasattr/get 패턴이 기본값으로 흡수(하위 호환)."""
        import json
        path, _ = QFileDialog.getOpenFileName(
            self, "시나리오 불러오기", "", "시나리오 파일 (*.json)")
        if not path:
            return
        try:
            with open(path, encoding='utf-8') as f:
                cfg = json.load(f)
            if not isinstance(cfg, dict):
                raise ValueError("올바른 시나리오 형식이 아닙니다(dict 아님)")
            self._restore_cfg(cfg)
            self._lbl_status.setText(
                f"📂 시나리오 불러옴: {os.path.basename(path)} — [🚀 시뮬레이션 실행]을 누르세요")
        except Exception as e:
            QMessageBox.warning(self, "불러오기 실패", f"시나리오 불러오기 중 오류:\n{e}")
    def _build_cfg_from_ui(self) -> dict:
        """현재 UI 위젯 상태를 완전한 시뮬 cfg dict로 조립.
        _run_sim과 쇼케이스 ON/OFF 비교가 동일 cfg 빌드를 공유한다."""
        # 적군 모드 및 편대 구성 (포팅 A)
        mode_label = self.cmb_enemy_mode.currentText()
        mode_map   = {'프리셋': 'preset', '혼합 시나리오': 'mixed', '랜덤': 'random'}
        enemy_mode = mode_map.get(mode_label, 'preset')

        cfg = {
            # 아군 편대 (탐지거리는 엔진이 함대+날씨로 자동 계산)
            'fleet_preset':      self.cmb_fleet.currentText(),
            'weather':           self.cmb_weather.currentText(),
            # v9.12: 작전 해역·계절·지형 음영
            'fleet_region':      self.cmb_region.currentText(),
            'season':            {'봄': 'spring', '여름': 'summer', '가을': 'autumn', '겨울': 'winter'}.get(
                                     self.cmb_season.currentText()[:1], 'summer'),
            'enable_terrain':    self.chk_terrain.isChecked(),
            'enable_current':    self.chk_current.isChecked(),
            'enable_evap_duct':  self.chk_evap_duct.isChecked(),
            'enable_anti_sam':   self.chk_anti_sam.isChecked(),
            'enable_isa':        self.chk_isa.isChecked(),
            'enable_png':        self.chk_png.isChecked(),   # v12.1: 비례항법 종말 유도
            'enable_sonar_equation': self.chk_sonar_eq.isChecked(),  # v12.3: dB 소나 방정식
            'enable_flooding':   self.chk_flooding.isChecked(),  # v12.4: 침수·복원력 모델
            'enable_munition_limit': self.chk_munition_limit.isChecked(),  # 적 공격 무장 유한화
            'enable_battle_mode': self.chk_battle.isChecked(),  # 지속 전장 엔진 (아키텍처 전환·병행 구축)
            'enable_campaign_mode': self.chk_campaign.isChecked(),  # v18.1 작전급 캠페인 엔진
            'enable_campaign_fog': self.chk_campaign_fog.isChecked(),  # v18.4 전장의 안개
            'enable_air_campaign': self.chk_air_campaign.isChecked(),  # v19.1 공군 작전급(제공권)
            'enable_precise_engagement': self.chk_precise_engage.isChecked(),  # A1 캠페인 교전 정밀 전술 해결(실험적)
            'enable_sead': self.chk_sead.isChecked(),  # v19.3 방공망 제압(SEAD/DEAD)
            'enable_strategic_strike': self.chk_strategic_strike.isChecked(),  # v19.4 전략 폭격 & 기지 타격
            # v20.2b 지상 작전급(연안 방공망) — ASBM 구역은 전술 정밀 교전으로 실측
            'enable_army_campaign': self.chk_army_campaign.isChecked(),
            # v21.2 합동 화력 지원 — 육해공 협조 타격
            'enable_joint_fires': self.chk_joint_fires.isChecked(),
            'enable_joint_report': self.chk_joint_report.isChecked(),   # v21.4
            'joint_fire_mode': ('simultaneous'
                                if self.cmb_joint_mode.currentText() == '동시 공격'
                                else 'sequential'),
            'army_fire_preset': self.cmb_army_fire.currentText(),
            'enable_coastal_sam':   self.chk_coastal_sam.isChecked(),
            'coastal_sam_preset':   self.cmb_coastal_preset.currentText(),
            # v20.3 해상 상륙작전(교두보 확보)
            'enable_amphibious':    self.chk_amphibious.isChecked(),
            'amphib_zone':          self.cmb_amphib_zone.currentText(),
            # v20.4 도미노(적 방공망 제압 → 제공권 → 해상 교통로)
            'enable_enemy_sead':    self.chk_enemy_sead.isChecked(),
            'enable_rl_policy': self.chk_rl_policy.isChecked(),  # 학습된 정책이 전장 전술 자동 결정(실험적)
            'enable_esm_arm': self.chk_esm_arm.isChecked(),  # v16.1: 레이더 방사↔ESM/ARM 역탐지(실험적)
            'enable_target_difficulty': self.chk_target_difficulty.isChecked(),  # v20.5: 요격 Pk에 표적 속도·RCS 반영(v18.05.07 정규·기본 ON)
            'enable_sonar_emcon': self.chk_sonar_emcon.isChecked(),  # v16.1: 능동 소나 핑 역탐지(실험적)
            'enable_asw_contact_limit': self.chk_asw_contact_limit.isChecked(),  # v20.5: 대잠 datum 성장·접촉 단절(실험적)
            'enable_standoff_spawn': self.chk_standoff_spawn.isChecked(),  # v20.5: 적 수상함 스탠드오프 발사(기본 ON)
            'enable_cyber_warfare': self.chk_cyber.isChecked(),  # v16.3: 사이버전 침투(실험적)
            'enable_hgv_glide': self.chk_hgv_glide.isChecked(),  # v16.2: 극초음속 활공 궤적(실험적)
            'enable_asw_forward': self.chk_asw_forward.isChecked(),  # v16.1: 대잠 항공 전진 초계(정규)
            'enable_weather_dynamics': self.chk_weather_dyn.isChecked(),  # v12.5: 동적 기상 변화
            'weather_trend':     self.cmb_weather_trend.currentText(),
            'enable_iff':        self.chk_iff.isChecked(),  # v12.6: 피아식별 오류
            # v9.14: 해협 진입로 (대한해협 선택 시 유효)
            'strait_type': {'서수도 (서→동)': 'korea_west',
                            '동수도 (동→서)': 'korea_east',
                            '양방향 협공':    'bilateral'}.get(
                self.cmb_strait_type.currentText(), 'korea_west'),
            'detect_km_manual':  False,
            # 적군 (포팅 A)
            'enemy_fleet_mode':       enemy_mode,
            'enemy_fleet_preset':     self.cmb_fleet_preset_e.currentText(),
            'mixed_scenario':         self.cmb_mixed_scenario.currentText(),
            'enemy_fleet_difficulty': self.cmb_difficulty.currentText(),
            'enemy_fleet_seed':       self.spn_seed.value() or None,
            # 전술 옵션 — 항상 ON
            'enable_ecm':         True,
            'enable_evasion':     True,
            'enable_decoy':       True,
            'enable_selfdefense': True,
            # 항공 자산 — UI 체크박스 읽기
            'enable_helo':  self.chk_helo.isChecked(),
            'enable_p3c':   self.chk_p3c.isChecked(),
            'enable_p8a':   self.chk_p8a.isChecked(),
            # v10.5: 한국 공군 CAP
            'enable_f35a':  self.chk_f35a.isChecked(),
            'enable_kf21':  self.chk_kf21.isChecked(),
            'enable_fa50':  self.chk_fa50.isChecked(),
            'enable_recon_drone': self.chk_recon.isChecked(),
            'recon_preset':       'MQ-9B 시가디언',
            # 방어 전술 — UI 체크박스 읽기
            'enable_layered_defense': True,
            'enable_cec':             self.chk_cec.isChecked(),
            'tactical_mode':          self.chk_tactical.isChecked(),
            'tactical_interval':      30,
            'enable_multibearing':       self.chk_multibearing.isChecked(),
            'enable_cec_jammed':         self.chk_cec_jammed.isChecked(),
            'enable_autonomous_engagement': self.chk_autonomous.isChecked(),
            'enable_ras_rearm':          self.chk_ras_rearm.isChecked(),
            'enable_ship_evasion':       self.chk_ship_evasion.isChecked(),
            'enable_radar_off':          self.chk_radar_off.isChecked(),
            'enable_dmo':                self.chk_dmo.isChecked(),
            'dmo_spread_km':             80.0,
            'enable_coord_deception':    self.chk_coord_decep.isChecked(),
            'enable_mine_threat':        self.chk_mine_threat.isChecked(),
            'mine_density':              0.3,
            'enable_minesweeping':       self.chk_minesweeping.isChecked(),
            'enable_unmanned_assets':    self.chk_unmanned.isChecked(),
            'enable_drone_swarm':        self.chk_drone_swarm.isChecked(),
            'enable_laser_dew':          self.chk_laser_dew.isChecked(),
            'enable_random_placement':   True,
            'random_spread_km':          10.0,
            'enemy_tactics':          {
                '없음': None, 'V자 대형': 'v_formation',
                '포위 기동': 'encirclement'
            }.get(self.cmb_enemy_tactics.currentText(), None),
            'ai_tactic': {
                '없음': None, '채널 포화': 'saturation',
                '시차 공격': 'stagger', '약점 공략': 'exploit_weakness',
                '적응형(자동)': 'adaptive',
            }.get(self.cmb_ai_tactic.currentText(), None),
            'sim_seed':               self.spn_sim_seed.value() or None,
            # v9.3: 공격 임무
            'enable_strike':   self.chk_strike.isChecked(),
            'haesong2_stock':  self.spn_haesong2.value(),
            'harpoon_stock':   self.spn_harpoon.value(),
            # v9.4: 현무-4 지상 발사 재고
            'hyunmoo4_stock':  self.spn_hyunmoo4.value(),
            # v9.11: 지상 BMD 자산
            'enable_ashore':   self.chk_ashore.isChecked(),
            'ashore_sm3_stock': 24 if self.chk_ashore.isChecked() else 0,
            'enable_thaad':    self.chk_thaad.isChecked(),
            'thaad_stock':     24 if self.chk_thaad.isChecked() else 0,
            # v20.2a: 한국형 BMD 계층 — 천궁-II 32발 = 발사대 4기 × 8셀(포대 편제)
            'enable_lsam':     self.chk_lsam.isChecked(),
            'lsam_stock':      16 if self.chk_lsam.isChecked() else 0,
            'enable_chungung': self.chk_chungung.isChecked(),
            'chungung_stock':  32 if self.chk_chungung.isChecked() else 0,
            # v20.1: 패트리엇 PAC-3 MSE — 발사대 4기 × 4셀(MSE는 셀당 1발) = 16발 포대 편제
            'enable_patriot':  self.chk_patriot.isChecked(),
            'patriot_stock':   16 if self.chk_patriot.isChecked() else 0,
            'enable_ballistic_descent': self.chk_bal_descent.isChecked(),
            # C&D 시간
            'cd_time_s':      10,
            'confirm_time_s': 3,
        }
        # v16.14.02: 아군 직접 편성 — 설정 시 프리셋 대신 fleet_custom 우선(엔진 소비).
        # 미설정 시 fleet_custom 키 없음 → 엔진 기존 프리셋 경로 → 회귀 bit-identical.
        _fc = getattr(self, '_fleet_custom', None)
        if _fc:
            cfg['fleet_custom'] = _expand_fleet_custom(_fc)
            cfg['fleet_preset'] = '(직접 편성)'   # 표시·기록용
        return cfg
