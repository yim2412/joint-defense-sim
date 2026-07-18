"""MainWindow mixin — ConfigPanelMixin의 환경 설정 섹션 분리(_build_config_panel 1,565줄 중 환경섹션 513줄).

app_main.py 분할 9/N. mixin_configpanel.py가 로컬 편집 예산(num_ctx 32768)을 초과해
가장 큰 단일 섹션을 떼어냈다. 의존은 PyQt6·app_engine·app_theme·ui_widgets뿐.
"""
from PyQt6.QtWidgets import (
    QCheckBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QVBoxLayout,
)

from app_engine import ARMY_FIRE_PRESETS, COASTAL_SAM_PRESETS, SLOC_ZONES
from app_theme import C_SUBTEXT, C_TEXT, _wire_chk_color
from ui_widgets import NoScrollComboBox, NoScrollSpinBox


class ConfigPanelExtraMixin:
    def _build_env_section(self) -> QGroupBox:
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
        return grp_env


    def _build_defense_section(self):
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
        return grp_def, grp_bmd
