"""런처 진입 화면 — SplashWindow(사이드바+홈+도움말+DB 탭)·SpecSheetPanel·부속 위젯.

app_main.py 분할 7/N. 의존은 PyQt6·app_theme·app_utils·app_engine·ui_charts뿐.
"""
import json
import os

from PyQt6.QtCore import Qt, QRectF, QSettings, pyqtSignal
from PyQt6.QtGui import (
    QColor, QFont, QPainter, QPainterPath, QPen, QPixmap,
)
from PyQt6.QtWidgets import (
    QFrame, QGraphicsDropShadowEffect, QGridLayout, QHBoxLayout, QLabel,
    QListWidget, QListWidgetItem, QPushButton, QScrollArea, QSizePolicy,
    QSplitter, QStackedWidget, QTabWidget, QVBoxLayout, QWidget,
)

from app_theme import (
    C_ACCENT, C_BG, C_BORDER, C_GREEN, C_ORANGE, C_PANEL, C_RED, C_SUBTEXT, C_TEXT,
)
from app_utils import _load_app_state, _res, _save_app_state, _write_log
from app_engine import (
    V7_AIRCRAFT_DB, V7_ENEMY_DB, V7_FRIENDLY_DB, V7_SHIP_DB,
    _SPEC_DETAIL_DB, _V7_OK, _normalize_enemy_db,
)
from ui_charts import _apply_window_geometry


# ════════════════════════════════════════════════════════════════════════════
#  SplashWindow — 런처 화면
# ════════════════════════════════════════════════════════════════════════════

TERM_TOOLTIPS: dict[str, str] = {
    'ARM':      '대방사미사일(Anti-Radiation Missile) — 적 레이더가 내뿜는 전파를 역추적해 레이더 자체를 파괴하는 미사일.',
    'CIWS':     '근접방어무기체계(Close-In Weapon System) — 함정 최후 방어선. 분당 수천 발 기관포로 수 km 내 목표를 요격.',
    'CEC':      '협동교전능력(Cooperative Engagement Capability) — 여러 함정이 탐지 정보를 실시간 공유해 단일 지휘처럼 교전.',
    'RCS':      '레이더 반사 면적(Radar Cross Section) — 값이 작을수록 레이더에 잘 안 잡힘. 스텔스 설계의 핵심 지표.',
    'ECM':      '전자방해(Electronic Countermeasure) — 적 레이더·유도장치를 전파로 교란해 탐지거리·명중률을 떨어뜨림.',
    'VLS':      '수직발사시스템(Vertical Launch System) — 함정 갑판 아래 수직으로 배치된 미사일 발사관. 전방향 즉시 발사 가능.',
    'BMD':      '탄도미사일방어(Ballistic Missile Defense) — 대기권 밖에서 재진입하는 탄도미사일을 추적·요격하는 체계.',
    'OTH':      '수평선 너머 표적(Over-The-Horizon) — 직접 시선 밖의 먼 거리 표적을 위성·헬기·데이터링크로 공격하는 방식.',
    'HGV':      '극초음속 활공체(Hypersonic Glide Vehicle) — 마하 5+ 속도로 활공하며 기동, 기존 방공망 회피에 특화.',
    'QBM':      '준탄도미사일(Quasi-Ballistic Missile) — 탄도궤도와 순항궤도를 혼합, 종말 단계에서 급기동해 요격 어렵게 설계.',
    'DEM':      '수치표고모델(Digital Elevation Model) — 지형 고도 데이터. 산·섬이 레이더를 가리는 음영 구역 계산에 활용.',
    'SM-2':     '스탠더드 미사일 2 — 함대공미사일. 유효 사거리 90~180km, 항공기·순항미사일 요격 전담.',
    'SM-3':     '스탠더드 미사일 3 — 대기권 밖에서 탄도미사일을 충돌 요격(Hit-to-Kill). BMD 핵심 무기.',
    'SM-6':     '스탠더드 미사일 6 — SM-2 후계. 수평선 너머 표적(OTH) 교전 및 탄도미사일 말단 단계 요격 겸용.',
    'RAM':      'RIM-116 롤링 에어프레임 미사일 — CIWS급 단거리 함대공미사일. 순항미사일·헬기 최후 방어에 사용.',
    'REQ':      '요구조건(Requirement) — 작전 성공 기준. 예: "요격률 85% 이상" 달성 여부로 시뮬레이션 합격·불합격 판정.',
    'CVaR':     '조건부 위험값(Conditional Value at Risk) — 최악 5% 시나리오의 평균 성과. 극단적 상황에서의 방어력 하한선.',
    'LHS':      '라틴 하이퍼큐브 샘플링 — 파라미터 불확실성 분석 기법. 전체 입력 공간을 균등하게 탐색해 편향 없는 통계 생성.',
    'Sobol':    'Sobol 민감도 분석 — 어떤 입력 파라미터가 결과에 가장 큰 영향을 미치는지 수치로 분해하는 글로벌 민감도 방법.',
    'SPY-1D':   'AN/SPY-1D — 이지스 함정의 4면 고정 위상배열 레이더. 360° 동시 탐색·추적, 빔 회전 주기 약 6초.',
    'Kh-31P':   'Kh-31P — 러시아제 대방사미사일. 마하 3.5+, 110km 사거리. 레이더 전파를 수동 추적해 직격.',
    'LD-10':    'LD-10 — 중국 PLAAF 대방사미사일. Kh-31P와 유사한 역할, J-16·JH-7 운용.',
    'Kh-58U':   'Kh-58U — 러시아제 대방사미사일. 마하 3.6, 250km 장거리. Su-24·Su-34에서 운용.',
    'YJ-21':    'YJ-21(鷹擊-21) — 중국 극초음속 대함미사일. 마하 10, 1500km 사거리. 항모 킬러.',
    'IRBM':     '중거리 탄도미사일(Intermediate-Range Ballistic Missile) — 사거리 3,000~5,500km. 북한 화성-12 등.',
    'HAD':      '항모전단 방어권(Carrier Group Air Defense) — 항모를 중심으로 호위함들이 다층 방어망을 구성하는 개념.',
    '055형':    '055형 구축함(Type 055) — 중국 최신예 대형 구축함. 1만 2천 톤급, 112셀 VLS. 미 알레이버크급 능가 설계.',
    '054A형':   '054A형 호위함(Type 054A) — 중국 4000톤급 호위함. HHQ-16 함대공미사일, 어뢰 탑재.',
    'FFX':      '차기 호위함(FFX) — 한국 해군 미래 호위함. FFX-I(인천급) → FFX-II → FFX-III로 능력 단계 향상.',
    'KDX':      '한국형 구축함(KDX) — KDX-II(충무공이순신급) 4,500t, KDX-III(세종대왕급) 1만t 이지스 구축함.',
    'C2':       '지휘통제(Command & Control) — 교전 결심·자원 배분·정보 공유를 총괄하는 지휘 체계.',
    'PNG':      '비례항법(Proportional Navigation Guidance) — 유도탄이 표적 시선각 변화율에 비례해 선회하는 표준 유도 법칙. 충돌 코스를 물리적으로 형성해 회피 기동하는 표적을 추격.',
    '비례항법':  '비례항법(PNG) — 유도탄이 표적 시선각(LOS) 변화율에 비례해 침로를 꺾는 유도 법칙. 종말 교전에서 회피 기동 표적의 명중/빗나감을 물리적으로 결정.',
    '종말 유도': '종말 유도 — 교전 마지막 단계(통상 10km 이내)에서 유도탄이 표적을 직접 추적·명중하는 구간. 표적의 회피 기동과 유도탄 기동 한계가 명중 여부를 좌우.',
    '탐색기 시야각': '탐색기 시야각(Seeker FOV) — 유도탄 탐색기가 표적을 포착할 수 있는 각도 범위. 표적이 이 범위를 벗어나면 추적 상실(lock-on 해제).',
    '기동 한계': '기동 한계(G 제한) — 유도탄이 낼 수 있는 최대 횡가속도. 함대공 미사일은 약 30G 이상, 대함미사일은 약 10G. 한계를 넘는 급기동 표적은 추격이 빗나감.',
    '소나 방정식': '소나 방정식(Sonar Equation) — 음원 준위·전달손실·주변소음·배열이득·탐지임계를 dB로 합산해 탐지 가능 여부를 계산하는 수중음향 표준식. 수동: FOM = SL − NL + AG − DT.',
    '전달손실': '전달손실(Transmission Loss, TL) — 음파가 거리를 진행하며 약해지는 정도(dB). 확산(구면/원통)·흡수·수온약층 손실의 합. 클수록 탐지거리 짧음.',
    '음원 준위': '음원 준위(Source Level, SL) — 잠수함이 방사하는 소음의 세기(dB re 1μPa@1m). 정온화된 잠수함(킬로·AIP)일수록 낮아 탐지가 어려움.',
    '주변소음': '주변소음(Noise Level, NL) — 해상상태(파고·바람)와 선박 교통으로 발생하는 배경 소음. 높을수록 표적 신호가 묻혀 탐지거리 감소.',
    '배열이득': '배열이득(Array Gain, AG) — 다수의 수중청음기를 배열해 표적 방향 신호를 강화하고 주변소음을 억제하는 이득(dB). 예인선배열이 선체소나보다 큼.',
    '표적강도': '표적강도(Target Strength, TS) — 능동 소나 음파가 잠수함 선체에 반사되어 돌아오는 세기(dB). 대형 잠수함일수록 큼.',
    '50% 탐지거리': '50% 탐지거리(R50) — 탐지 확률이 50%가 되는 거리. 소나 방정식 TL(R50)=FOM으로 산출하며, 이 거리 안쪽은 탐지 확률이 빠르게 상승.',
    '디핑 소나': '디핑 소나(Dipping Sonar) — 대잠 헬기가 호버링 상태에서 음향센서를 물속에 내려 잠수함을 탐지하는 능동/수동 소나.',
    '소노부이': '소노부이(Sonobuoy) — 해상초계기·헬기가 투하하는 부유식 음향 탐지 부표. 수동(DIFAR)·능동(DICASS)으로 잠수함을 탐지·표정.',
}

def _apply_term_tooltip(item: 'QTableWidgetItem', text: str) -> None:
    hits = [tip for kw, tip in TERM_TOOLTIPS.items() if kw in text]
    if hits:
        item.setToolTip('\n\n'.join(hits))


_FEATURES = [
    ("📊  교전 분석",
     "시뮬레이션 결과를 세 가지 차트로 분석. "
     "① 방어 Funnel: SM-3→SM-6→SM-2→ESSM→CIWS 레이어별 격추 수 시각화. "
     "② 위협 추적 테이블: 각 위협이 어느 무기·거리·시각에 격추됐는지(또는 뚫렸는지) 일람. "
     "③ 교전 타임라인: 위협별 교전 시작~종료 구간을 색상 바로 표시 (초록=요격, 빨강=피격)."),
    ("🌐  3D 전장",
     "교전 결과를 실제 위성 지도 위 3D 전장으로 재생. "
     "아군 함정·적함·미사일 궤적·교전 지점을 실제 좌표 위에 입체로 표시하고 타임라인으로 시간순 재생. "
     "마우스 줌·회전으로 어디서 어떻게 교전이 벌어졌는지 한눈에 확인하고, "
     "위협 발수 카운터로 발사·비행 중·처리된 미사일 수도 함께 표시. (교전 분석 탭 안)"),
    ("📊  반복 시뮬레이션 통계",
     "같은 시나리오를 수백~수천 번 자동 반복해 '평균적으로 몇 %를 막아내는지' 확률로 계산. "
     "결과가 운에 따라 얼마나 달라지는지 분포 그래프로 확인 가능."),
    ("⚡  시뮬레이션 모드 선택",
     "빠름(5,000회) / 표준(10,000회) / 정밀(100,000회) 중 목적에 맞게 선택. "
     "모든 모드에서 LHS 샘플링·CVaR·스트레스 테스트 자동 실행. "
     "정밀 모드는 추가로 Sobol 파라미터 민감도 분석까지 수행."),
    ("🔥  스트레스 테스트",
     "레이더 성능 저하(0~50%)와 유도 채널 감소(0~75%)를 조합한 12가지 최악 조건을 자동으로 시험. "
     "어떤 상황에서 방어 체계가 무너지는지 색상 히트맵으로 한눈에 파악."),
    ("🎛  Sobol 민감도 분석",
     "SAM 명중률·탐지거리·C&D 시간·ECM 효과·위협 속도 6가지 불확실 파라미터 중 "
     "어느 것이 요격률에 가장 큰 영향을 주는지 수치로 계산. "
     "정밀 모드 전용. 포인트당 반복 수(기본 3회) 설정으로 확률 노이즈 감소 가능."),
    ("✅  전술 요구조건 자동 판정",
     "한국 해군 전술 요구조건 8가지(응답 시간·요격률·함정 생존율 등)를 "
     "시뮬레이션 결과로 자동 통과/실패 판정. 어떤 조건이 미달인지 한눈에 확인."),
    ("📜  교전 기록 로그",
     "미사일 발사, 요격 성공/실패, 함정 피격 등 매 초 단위로 발생한 "
     "모든 교전 사건을 시간 순서대로 전부 기록. 무엇이 언제 일어났는지 추적 가능."),
    ("📡  레이더 채널 포화도",
     "각 함정의 레이더 추적 채널이 시간대별로 얼마나 사용됐는지 색상 히트맵으로 표시. "
     "빨간색에 가까울수록 채널이 꽉 찬 상태 — 채널 포화 시 추가 요격 불가."),
    ("💰  격추 비용 효과",
     "적 1기를 격추하는 데 평균 얼마의 비용이 들었는지 달러 단위로 표시. "
     "무기별 잔여 재고도 함께 확인 가능."),
    ("🔫  탄약 소모 현황",
     "반복 시뮬레이션 기준 평균 잔여 탄약을 무기별 가로 막대그래프로 표시. "
     "어떤 무기가 가장 많이 소모됐는지 비교."),
    ("📈  요격률 신뢰 구간",
     "요격률이 몇 %~몇 % 범위 안에 들어오는지 95% 신뢰구간으로 표시. "
     "함정별 평균 피격 횟수 히스토그램도 함께 표시."),
    ("📋  시나리오 프로필 저장",
     "적 종류·날씨·재고·편대 구성 등 시뮬레이션 설정 전체를 이름 붙여 저장하고 "
     "언제든 불러올 수 있음. 자주 쓰는 시나리오를 매번 다시 설정할 필요 없음."),
    ("📄  보고서 내보내기",
     "시뮬레이션 결과 전체를 Excel 파일과 PDF(4페이지)로 저장. "
     "요격률·비용·교전 통계·그래프가 모두 포함된 공식 분석 보고서 형태."),
    ("📺  실시간 진행 팝업",
     "시뮬레이션 실행 중 별도 팝업 창으로 진행률·완료 횟수·예상 남은 시간과 "
     "CPU/RAM/GPU 사용률·처리 속도를 실시간 표시. 창을 마우스로 자유롭게 이동 가능."),
    ("⚡  멀티코어 병렬 처리",
     "프로그램 시작 시 미리 워커 프로세스를 준비해두고, 반복 시뮬레이션 시 "
     "최대 8개 코어를 동시에 활용해 빠르게 처리. 코어가 많을수록 분석 속도 향상."),
    ("⚙️  현실적 전술 기동",
     "데이터링크 두절 상황, 함정 회피 기동, V자 편대 진형, 포위 공격, "
     "다방위 동시 공격 등 실제 해전에서 쓰이는 전술 상황을 시뮬레이션에 반영."),
    ("🌊  적군 위협 데이터베이스",
     "중국 PLA해군·공군 함정·전투기, 북한 탄도·순항·잠수함발사 미사일, "
     "러시아 극초음속 무기, YJ-21·YJ-18 신형 미사일, 드론 떼·소형 자폭 드론까지 총 43종 위협 수록."),
    ("⚓  한국 해군 함정 DB (10종+)",
     "KDX-III Batch I/II(세종대왕·정조대왕급)·KDX-II 구축함·FFX Batch I/II/III 호위함 외 "
     "PKG 윤영하급, PCC 포항급, PKX-B 참수리-II, LPH 독도함급, AOE 소양함까지 수록. "
     "Batch별 SM-3 탑재 유무·해궁 장착 여부 등 실제 제원 반영."),
    ("🏴  현실 기반 편대 프리셋 (10종)",
     "한국 해군 실 교리 기반 편대 5종 추가: 이지스 기동전단 / 이지스 기동전단(강화) / "
     "독도함 상륙전단 / 동해 해역방어(1함대) / 서해 해역방어(2함대). "
     "기존 5종(단독·기본·BMD·대잠·최대)과 합쳐 총 10종 프리셋 제공."),
]


# ════════════════════════════════════════════════════════════════════════════
#  스펙시트 패널
# ════════════════════════════════════════════════════════════════════════════
class _RoundPhoto(QWidget):
    """사진을 비율 유지(contain) + 둥근 모서리로 그리는 위젯. 사진 없으면 아이콘 표시."""

    def __init__(self, height: int = 210):
        super().__init__()
        self._pix: 'QPixmap | None' = None
        self._icon = ""
        self.setFixedHeight(height)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_photo(self, pix: QPixmap):
        self._pix = pix if (pix and not pix.isNull()) else None
        self._icon = ""
        self.update()

    def set_icon(self, text: str):
        self._pix = None
        self._icon = text
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        path = QPainterPath()
        path.addRoundedRect(r, 8, 8)
        p.setClipPath(path)
        p.fillRect(self.rect(), QColor(C_BG))
        if self._pix is not None:
            sp = self._pix.scaled(
                self.size(), Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            x = (self.width() - sp.width()) // 2
            y = (self.height() - sp.height()) // 2
            p.drawPixmap(x, y, sp)
        elif self._icon:
            p.setPen(QColor(C_SUBTEXT))
            f = p.font(); f.setPointSize(44); p.setFont(f)
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, self._icon)
        p.setClipping(False)
        pen = QPen(QColor(C_BORDER)); pen.setWidth(1)
        p.setPen(pen); p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(r, 8, 8)


# 스펙시트 카테고리 카드 좌측 accent 색 (카테고리 이름 키워드 매칭)
_CAT_CARD_ACCENT = {
    '기본':   '#3498db',   # 청색
    '물리':   '#7d8590',   # 회색
    '성능':   '#2ecc71',   # 녹색
    '추진':   '#1abc9c',   # 청록
    '무장':   '#e6a23c',   # 주황
    '센서':   '#9b59b6',   # 보라
    '유도':   '#c0504d',   # 적색
    '탄두':   '#c0504d',
    '전자전': '#9b59b6',
    '시스템': '#5b9bd5',
    '보급':   '#1abc9c',
    '전술':   '#e74c3c',
    '항공':   '#5b9bd5',
}


def _cat_accent(cat_name: str) -> str:
    for key, color in _CAT_CARD_ACCENT.items():
        if key in cat_name:
            return color
    return C_ACCENT


# ── 하이라이트 카드 값 빌더 (관점별: 적=위협 / 아군=방어) ──────────────────
_MISSILE_TYPES = {'순항미사일', '탄도미사일', '극초음속활공체', '저고도기동탄도', '대방사미사일'}
_AIRCRAFT_TYPES = {'전투기', '폭격기', '전폭기'}
_SURFACE_TYPES = {'고속정', '초계함', '호위함', '구축함', '항모', '순양함', '상륙함'}


def _hl_mach(ms):
    return f"Mach {ms / 343:.1f}" if ms else "—"


def _hl_kt(ms):
    return f"{round(ms * 1.94384)} kt" if ms else "—"


def _hl_rcs(v):
    if v is None:
        return "—"
    return f"{v:.0f} ㎡" if v >= 100 else f"{v:g} ㎡"


def _hl_alt(m):
    if m is None:
        return "—"
    return f"{m} m" if m < 1000 else f"{m / 1000:.0f} km"


def _hl_wpn(name):
    return name.split()[0] if name else "—"


def _hl_clean(s):
    """괄호 주석 제거 ('11,000 톤 (Batch I 대비 증설)' → '11,000 톤')."""
    s = str(s)
    i = s.find('(')
    if i != -1:
        s = s[:i]
    return s.strip()


def _spec_pick(spec, keys, prefer=None):
    """db_specsheet 카테고리에서 label에 keys 중 하나가 든 필드 검색.
    값이 'A / B'면 기본 첫 토막, prefer 지정 시 label 토막 순서로 해당 위치 토막 반환."""
    if isinstance(keys, str):
        keys = [keys]
    for _cat, fields in spec.get('categories', []):
        for label, value in fields:
            if any(k in label for k in keys):
                parts = [p.strip() for p in str(value).split('/')]
                if prefer:
                    ltoks = label.replace('(', ' ').replace(')', ' ').split('/')
                    idx = next((i for i, lt in enumerate(ltoks) if prefer in lt), None)
                    if idx is not None and idx < len(parts):
                        return _hl_clean(parts[idx])
                return _hl_clean(parts[0])
    return None


def _build_highlights(name: str, db: dict, spec: dict, unit_type: str):
    """종류별 핵심수치 4개 [(value, label), ...] 반환. 데이터 없으면 None."""
    db = db or {}
    if unit_type == 'weapon':          # 아군 요격탄
        pk = (db.get('pk_dist') or {}).get('mean')
        return [
            (f"{db.get('range_km', '—')} km", "사거리"),
            (_hl_mach(db.get('speed_ms')), "요격속도"),
            (f"{pk:.2f}" if pk else "—", "명중확률 Pk"),
            (f"{db.get('stock', '—')} 발", "재고"),
        ]
    if unit_type == 'aircraft':        # 아군 항공기
        return [
            (f"{db.get('range_km', '—')} km", "작전반경"),
            (_hl_kt(db.get('speed_ms')), "순항속도"),
            (_hl_wpn(db.get('payload_wpn')), "탑재무장"),
            (f"{db.get('payload_cnt', '—')} 발", "탑재량"),
        ]
    if unit_type == 'ship':            # 아군 함정/잠수함
        sensor = db.get('sensor_km', {}) or {}
        if db.get('is_submarine'):
            inv = db.get('default_strike_inventory') or db.get('default_inventory') or {}
            wpn = next(iter(inv), None)
            return [
                (_spec_pick(spec, '최고 속도', prefer='수중') or "—", "수중속력"),
                (_spec_pick(spec, '심도') or "—", "잠항심도"),
                (f"{sensor.get('대잠', '—')} km", "대잠탐지"),
                (_hl_wpn(wpn), "주무장"),
            ]
        return [
            (_spec_pick(spec, '배수량', prefer='만재') or "—", "만재배수량"),
            (_spec_pick(spec, ['최고 속도', '속도']) or "—", "최대속력"),
            (f"{sensor.get('대공', '—')} km", "대공탐지"),
            (f"{db.get('max_channels', '—')} 표적", "동시교전"),
        ]
    # 적군 (unit_type == 'enemy') — type으로 세분
    typ = db.get('type', '')
    if typ in _MISSILE_TYPES:
        return [
            (f"{db.get('missile_range_km') or db.get('range_km', '—')} km", "사거리"),
            (_hl_mach(db.get('speed_ms')), "종말속도"),
            (_hl_rcs(db.get('rcs_m2')), "RCS"),
            (_hl_alt(db.get('altitude_m')), "비행고도"),
        ]
    if typ in _AIRCRAFT_TYPES:
        return [
            (_spec_pick(spec, ['행동반경', '작전반경', '전투 행동']) or "—", "작전반경"),
            (_hl_mach(db.get('speed_ms')), "최대속도"),
            (_hl_rcs(db.get('rcs_m2')), "RCS"),
            (_hl_wpn(db.get('missile_name')), "주무장"),
        ]
    if typ == '잠수함':
        d = db.get('altitude_m')
        return [
            (_hl_kt(db.get('speed_ms')), "수중속력"),
            (f"{abs(d):.0f} m" if d is not None else "—", "잠항심도"),
            (f"{db.get('missile_range_km', '—')} km", "사거리"),
            (_hl_wpn(db.get('missile_name')), "주무장"),
        ]
    if typ in _SURFACE_TYPES:
        return [
            (_spec_pick(spec, '배수량', prefer='만재') or "—", "만재배수량"),
            (_hl_kt(db.get('speed_ms')), "최대속력"),
            (_hl_rcs(db.get('rcs_m2')), "RCS"),
            (_hl_wpn(db.get('missile_name')), "주무장"),
        ]
    return None


class SpecSheetPanel(QWidget):
    """선택 유닛 스펙시트 — 우측 패널 (사진 + 카테고리별 상세 스펙 + 스크롤)"""

    _TYPE_ICON = {
        '전투기': '✈', '전폭기': '✈', '폭격기': '✈',
        '탄도미사일': '🚀', '순항미사일': '🚀',
        '극초음속활공체': '🚀', '저고도기동탄도': '🚀',
        '고속정': '⚓', '초계함': '⚓', '호위함': '⚓',
        '구축함': '⚓', '상륙함': '⚓', '순양함': '⚓',
        '잠수함': '🔱',
        '_ship': '⚓', '_weapon': '💥',
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"background:{C_PANEL}; border-left:1px solid {C_BORDER};"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 8, 10, 8)
        root.setSpacing(6)

        # ── 상단: 가로 사진 박스 (비율 유지 + 둥근 모서리) ─────────────────
        self._photo = _RoundPhoto(height=210)
        root.addWidget(self._photo)

        # ── 제목 / 부제 행 ────────────────────────────────────────────────
        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        title_row.setContentsMargins(2, 0, 2, 0)

        self._title_lbl = QLabel("← 왼쪽 목록에서 유닛을 선택하세요")
        self._title_lbl.setStyleSheet(
            f"color:{C_ACCENT}; font-size:16px; font-weight:bold;"
        )

        self._sub_lbl = QLabel()
        self._sub_lbl.setStyleSheet(f"color:{C_SUBTEXT}; font-size:14px;")
        self._sub_lbl.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        title_row.addWidget(self._title_lbl)
        title_row.addStretch()
        title_row.addWidget(self._sub_lbl)
        root.addLayout(title_row)

        # 구분선
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color:{C_BORDER};")
        root.addWidget(sep)

        # ── 하이라이트 카드 행 (사진 아래 핵심수치) ───────────────────────
        self._hl_wrap = QWidget()
        self._hl_lay = QHBoxLayout(self._hl_wrap)
        self._hl_lay.setContentsMargins(0, 2, 0, 2)
        self._hl_lay.setSpacing(6)
        self._hl_wrap.hide()
        root.addWidget(self._hl_wrap)

        # ── 카테고리 스크롤 영역 ──────────────────────────────────────────
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet(
            f"QScrollArea {{ background:transparent; border:none; }}"
            f"QWidget {{ background:transparent; }}"
            f"QScrollBar:vertical {{ width:6px; background:{C_BG}; }}"
            f"QScrollBar::handle:vertical {{ background:{C_BORDER}; border-radius:3px; min-height:20px; }}"
            f"QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}"
        )

        self._scroll_w = QWidget()
        self._scroll_vbox = QVBoxLayout(self._scroll_w)
        self._scroll_vbox.setContentsMargins(0, 2, 4, 2)
        self._scroll_vbox.setSpacing(0)
        self._scroll.setWidget(self._scroll_w)

        self._note_lbl = QLabel()
        self._note_lbl.setStyleSheet(
            f"color:{C_SUBTEXT}; font-size:15px; font-style:italic; padding:2px 4px;"
        )
        self._note_lbl.setWordWrap(True)

        root.addWidget(self._scroll, stretch=1)
        root.addWidget(self._note_lbl)

    # ── 내부 헬퍼 ──────────────────────────────────────────────────────
    def _clear_scroll(self):
        while self._scroll_vbox.count():
            item = self._scroll_vbox.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _add_category(self, cat_name: str, cat_fields: list):
        accent = _cat_accent(cat_name)
        card = QFrame()
        card.setStyleSheet(
            f"QFrame {{ background:{C_PANEL}; border:1px solid {C_BORDER};"
            f" border-left:3px solid {accent}; border-radius:6px; }}"
        )
        cv = QVBoxLayout(card)
        cv.setContentsMargins(11, 7, 11, 8)
        cv.setSpacing(4)

        hdr = QLabel(cat_name.upper())
        hdr.setStyleSheet(
            f"color:{accent}; font-size:13px; font-weight:bold;"
            f" border:none; background:transparent;"
        )
        cv.addWidget(hdr)

        gw = QWidget()
        gw.setStyleSheet("background:transparent; border:none;")
        gl = QGridLayout(gw)
        gl.setContentsMargins(0, 0, 0, 0)
        gl.setHorizontalSpacing(10)
        gl.setVerticalSpacing(3)
        gl.setColumnStretch(1, 1)

        for r, (label, value) in enumerate(cat_fields):
            lbl_w = QLabel(str(label))
            lbl_w.setStyleSheet(
                f"color:{C_SUBTEXT}; font-size:13px; border:none; background:transparent;"
            )
            lbl_w.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            val_w = QLabel(str(value))
            val_w.setStyleSheet(
                f"color:{C_TEXT}; font-size:13px; font-weight:600;"
                f" border:none; background:transparent;"
            )
            val_w.setWordWrap(True)
            val_w.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            gl.addWidget(lbl_w, r, 0)
            gl.addWidget(val_w, r, 1)

        cv.addWidget(gw)
        self._scroll_vbox.addWidget(card)
        self._scroll_vbox.addSpacing(6)

    # ── 하이라이트 카드 (사진 아래 핵심수치 4개) ─────────────────────────
    _HL_PALETTE = ['#3498db', '#e6a23c', '#c0504d', '#2ecc71']

    def _clear_highlights(self):
        while self._hl_lay.count():
            item = self._hl_lay.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _set_highlights(self, highlights):
        """highlights: [(value, label), ...] 최대 4개. 없으면 영역 숨김."""
        self._clear_highlights()
        if not highlights:
            self._hl_wrap.hide()
            return
        self._hl_wrap.show()
        for i, (value, label) in enumerate(highlights[:4]):
            accent = self._HL_PALETTE[i % len(self._HL_PALETTE)]
            card = QFrame()
            card.setStyleSheet(
                f"QFrame {{ background:{C_PANEL}; border:1px solid {C_BORDER};"
                f" border-top:3px solid {accent}; border-radius:6px; }}"
            )
            cv = QVBoxLayout(card)
            cv.setContentsMargins(10, 7, 10, 7)
            cv.setSpacing(1)
            v = QLabel(str(value))
            v.setStyleSheet(
                f"color:{C_TEXT}; font-size:18px; font-weight:bold;"
                f" border:none; background:transparent;"
            )
            l = QLabel(str(label))
            l.setStyleSheet(
                f"color:{C_SUBTEXT}; font-size:12px; border:none; background:transparent;"
            )
            cv.addWidget(v)
            cv.addWidget(l)
            self._hl_lay.addWidget(card, 1)

    def clear(self):
        self._photo.set_icon("")
        self._set_highlights(None)
        self._title_lbl.setText("← 왼쪽 목록에서 유닛을 선택하세요")
        self._sub_lbl.setText("")
        self._note_lbl.setText("")
        self._clear_scroll()

    def show_unit(self, name: str, db_entry: dict, spec: dict, unit_type: str = 'enemy'):
        """unit_type: 'enemy' | 'ship' | 'weapon'"""
        self._title_lbl.setText(name)

        # 사진 또는 아이콘 (.jpg → .png → .webp 순서로 탐색)
        _img_base = os.path.join(_res('assets/images'), name)
        img_path = next(
            (p for p in (_img_base + ext for ext in ('.jpg', '.png', '.webp'))
             if os.path.exists(p)),
            None
        )
        if img_path:
            self._photo.set_photo(QPixmap(img_path))
        else:
            if unit_type == 'ship':
                icon = '⚓'
            elif unit_type == 'weapon':
                icon = '💥'
            else:
                typ = db_entry.get('type', '')
                icon = self._TYPE_ICON.get(typ, '❓')
            self._photo.set_icon(icon)

        # 부제목
        origin    = spec.get('origin', '')
        type_desc = spec.get('type_desc', db_entry.get('type', ''))
        self._sub_lbl.setText(
            f"{origin}  |  {type_desc}" if (origin and type_desc) else (origin or type_desc)
        )

        # 하이라이트 카드 (핵심수치 4개) — spec에 명시 override 있으면 우선
        hl = spec.get('highlight') or _build_highlights(name, db_entry, spec, unit_type)
        self._set_highlights(hl)

        # 카테고리 렌더링
        self._clear_scroll()
        categories = spec.get('categories', [])
        if categories:
            for cat_name, cat_fields in categories:
                self._add_category(cat_name, cat_fields)
        else:
            fields = spec.get('fields', [])
            if fields:
                self._add_category('제원', fields)
        self._scroll_vbox.addStretch()

        # 비고
        self._note_lbl.setText(spec.get('note', ''))


class _HomeBg(QWidget):
    """홈 배경 — 위성 합성 이미지를 영역에 꽉 차게(cover) 그린다."""

    def __init__(self, pixmap: QPixmap):
        super().__init__()
        self._pix = pixmap

    def paintEvent(self, e):
        p = QPainter(self)
        if self._pix and not self._pix.isNull():
            scaled = self._pix.scaled(
                self.size(),
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation)
            x = (scaled.width() - self.width()) // 2
            y = (scaled.height() - self.height()) // 2
            p.drawPixmap(-x, -y, scaled)
        else:
            p.fillRect(self.rect(), QColor('#0a1426'))
        p.fillRect(self.rect(), QColor(7, 13, 24, 55))   # 가독성용 살짝 어둡게


class SplashWindow(QWidget):
    """프로그램 진입 런처. [시뮬레이터 시작] → MainWindow 열기."""

    launch_requested = pyqtSignal()

    def __init__(self, app_version: str = ""):
        super().__init__()
        self._app_version = app_version
        from datetime import datetime
        _write_log(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]  앱 시작')
        self.setWindowTitle("합동 통합방어 시뮬레이터")
        # 고정 크기 → 자유 리사이즈 (최소 크기만 지정)
        self.setMinimumSize(1000, 680)
        self.setStyleSheet(f"""
            QWidget {{ background: {C_BG}; color: {C_TEXT};
                       font-family: 'Malgun Gothic', 'Segoe UI'; font-size: 17px; }}
            QTabWidget::pane {{ border: 1px solid {C_BORDER}; background: {C_BG}; }}
            QTabBar::tab {{ background: {C_PANEL}; color: {C_SUBTEXT};
                            padding: 10px 26px; border: 1px solid {C_BORDER}; font-size: 16px; }}
            QTabBar::tab:selected {{ background: {C_BG}; color: {C_ACCENT};
                                     border-bottom: 2px solid {C_ACCENT}; }}
            QPushButton {{ background: {C_ACCENT}; color: white; border: none;
                           padding: 14px 36px; border-radius: 6px; font-size: 18px;
                           font-family: 'Malgun Gothic', 'Segoe UI', sans-serif; }}
            QPushButton:hover {{ background: #2980b9; }}
            QTableWidget {{ background: {C_PANEL}; gridline-color: {C_BORDER};
                            border: none; font-size: 16px; }}
            QHeaderView::section {{ background: {C_PANEL}; color: {C_ACCENT};
                                    border: none; padding: 8px; font-size: 16px; }}
        """)
        self._build_ui()
        # 저장된 창 위치·크기 복원 (없으면 화면 중앙, 화면보다 크면 클램프)
        _apply_window_geometry(self, "SplashWin", 1400, 960)

    def closeEvent(self, event):
        # 창 위치·크기 저장 (다음 실행 시 같은 자리에서 복원)
        try:
            QSettings("AegisSim", "SplashWin").setValue("geometry", self.saveGeometry())
        except Exception:
            pass
        super().closeEvent(event)

    def _build_ui(self):
        h = QHBoxLayout(self)
        h.setContentsMargins(0, 0, 0, 0)
        h.setSpacing(0)
        self._content = QStackedWidget()
        h.addWidget(self._build_sidebar())
        h.addWidget(self._content, 1)
        # 콘텐츠 페이지: 0 홈 · 1~6 정보/DB 탭 (사이드바 메뉴 순서와 일치)
        for builder in (
            self._build_home_page,
            self._build_help_tab, self._build_feature_tab,
            self._build_changelog_tab, self._build_plan_tab,
            self._build_enemy_db_tab, self._build_friendly_db_tab):
            self._content.addWidget(builder())
        self._nav_select(0)   # 시작 시 항상 홈(표지) 화면

    # ── 좌측 사이드바 (Paradox 스타일 세로 메뉴) ──────────────────────────
    def _build_sidebar(self) -> QWidget:
        bar = QWidget()
        bar.setObjectName("sidebar")
        bar.setFixedWidth(252)
        bar.setStyleSheet(f"""
            QWidget#sidebar {{ background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                                   stop:0 #0e1828, stop:1 #0a1119);
                               border-right: 1px solid #1c2b3e; }}
            QWidget#sidebar QLabel {{ background: transparent; }}
            QPushButton#nav {{ text-align: left; padding: 11px 17px;
                border: none; border-left: 3px solid transparent;
                background: transparent; color: #9fb0c3; font-size: 15px; }}
            QPushButton#nav:hover {{ background: rgba(52,152,219,0.13);
                color: #eaf2ff; border-left: 3px solid rgba(52,152,219,0.55); }}
            QPushButton#nav:checked {{ background: rgba(52,152,219,0.20);
                color: {C_ACCENT}; border-left: 3px solid {C_ACCENT};
                font-weight: bold; }}
        """)
        v = QVBoxLayout(bar)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        # 상단 로고 (아이콘 + 앱 이름)
        logo = QHBoxLayout()
        logo.setContentsMargins(20, 22, 20, 18)
        logo.setSpacing(12)
        icon = QLabel()
        icon.setPixmap(QPixmap(_res("assets/images/app_emblem.png")).scaled(
            42, 42, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation))
        logo.addWidget(icon)
        names = QVBoxLayout()
        names.setSpacing(0)
        n1 = QLabel("합동 통합방어")
        n1.setFont(QFont('Malgun Gothic', 15, QFont.Weight.Bold))
        n1.setStyleSheet("color: #eaf2ff;")
        n2 = QLabel("시뮬레이터")
        n2.setStyleSheet(f"color: {C_SUBTEXT}; font-size: 12px;")
        names.addWidget(n1)
        names.addWidget(n2)
        logo.addLayout(names)
        logo.addStretch(1)
        v.addLayout(logo)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color: {C_BORDER};")
        sep.setFixedHeight(1)
        v.addWidget(sep)
        v.addSpacing(8)

        # 네비게이션 버튼 (클릭 시 우측 콘텐츠 전환)
        self._nav_btns = []
        items = [("🏠  홈", 0), ("❓  도움말", 1), ("🛠  탑재 기능", 2),
                 ("📜  패치 내역", 3), ("🧭  향후 계획", 4),
                 ("🔴  적군 DB", 5), ("🔵  아군 DB", 6)]
        for label, idx in items:
            b = QPushButton(label)
            b.setObjectName("nav")
            b.setCheckable(True)
            b.setFixedHeight(44)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            b.clicked.connect(lambda _=False, i=idx: self._nav_select(i))
            v.addWidget(b)
            self._nav_btns.append(b)

        v.addStretch(1)

        sep2 = QFrame()
        sep2.setFrameShape(QFrame.Shape.HLine)
        sep2.setStyleSheet(f"color: {C_BORDER};")
        sep2.setFixedHeight(1)
        v.addWidget(sep2)

        foot = QVBoxLayout()
        foot.setContentsMargins(20, 12, 20, 16)
        foot.setSpacing(2)
        ver = QLabel(self._app_version)
        ver.setStyleSheet(f"color: {C_TEXT}; font-size: 13px; font-weight: bold;")
        dt = QLabel("2026.6  ·  PyQt6 네이티브 UI")
        dt.setStyleSheet(f"color: {C_SUBTEXT}; font-size: 11px;")
        foot.addWidget(ver)
        foot.addWidget(dt)
        v.addLayout(foot)
        return bar

    def _nav_select(self, idx: int):
        self._content.setCurrentIndex(idx)
        for i, b in enumerate(self._nav_btns):
            b.setChecked(i == idx)
        _save_app_state({**_load_app_state(), 'splash_tab': idx})

    # ── 홈 화면 (표지 + 시작 버튼) ────────────────────────────────────────
    def _build_home_page(self) -> QWidget:
        page = _HomeBg(QPixmap(_res("assets/images/home_bg.jpg")))
        page.setObjectName("home")
        page.setStyleSheet(f"""
            QWidget#home QLabel {{ background: transparent; }}
            QWidget#home QPushButton {{
                font-size: 20px; font-weight: bold; color: #f3f6fa;
                padding: 16px 52px; border-radius: 10px;
                border: 1px solid rgba(255,255,255,0.40);
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(46,58,74,0.92), stop:1 rgba(24,32,44,0.95));
            }}
            QWidget#home QPushButton:hover {{
                border: 1px solid rgba(255,255,255,0.75);
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(66,82,102,0.96), stop:1 rgba(36,48,64,0.97));
            }}
        """)
        v = QVBoxLayout(page)
        v.setContentsMargins(50, 20, 50, 42)
        v.setSpacing(2)

        # ── 상단(하늘 영역): 엠블럼 + 타이틀, 좌측 정렬 ──
        emblem = QLabel()
        emblem.setPixmap(QPixmap(_res("assets/images/app_emblem.png")).scaled(
            60, 60, Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation))
        v.addWidget(emblem, alignment=Qt.AlignmentFlag.AlignLeft)

        t1 = QLabel("합동 통합방어 시뮬레이터")
        t1.setFont(QFont('Malgun Gothic', 33, QFont.Weight.Bold))
        t1.setStyleSheet("color: #ffffff;")
        v.addWidget(t1, alignment=Qt.AlignmentFlag.AlignLeft)
        v.addSpacing(10)

        en = QLabel("J O I N T   D E F E N S E   S I M U L A T O R")
        en.setStyleSheet("color: #c2cdd9; font-size: 14px; font-weight: bold;")
        v.addWidget(en, alignment=Qt.AlignmentFlag.AlignLeft)
        v.addSpacing(7)

        desc = QLabel("한국 해군 이지스 기동전단 다층 방어 시뮬레이터")
        desc.setStyleSheet("color: #d6dee8; font-size: 16px;")
        v.addWidget(desc, alignment=Qt.AlignmentFlag.AlignLeft)

        # 사진 배경 위 가독성 — 텍스트에 검정 그림자
        for _lbl in (emblem, t1, en, desc):
            _e = QGraphicsDropShadowEffect()
            _e.setColor(QColor(0, 0, 0, 255))
            _e.setBlurRadius(26)
            _e.setOffset(0, 3)
            _lbl.setGraphicsEffect(_e)

        v.addStretch(1)   # 전투기가 보이는 가운데 공간

        # ── 하단 우측: 시뮬레이터 시작 버튼 ──
        btn_start = QPushButton("🚀  시뮬레이터 시작")
        btn_start.setFixedHeight(58)
        btn_start.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_start.clicked.connect(self.launch_requested.emit)
        glow = QGraphicsDropShadowEffect()
        glow.setColor(QColor(0, 0, 0, 210))
        glow.setBlurRadius(28)
        glow.setOffset(0, 3)
        btn_start.setGraphicsEffect(glow)
        btn_box = QHBoxLayout()
        btn_box.addStretch(1)
        btn_box.addWidget(btn_start)
        v.addLayout(btn_box)
        return page

    # ── 도움말 / 튜토리얼 탭 ──────────────────────────────────────────────
    def _build_help_tab(self) -> QWidget:
        _GLOSSARY = [
            ("Pk (Kill Probability)",    "교전 1회에서 위협을 격추할 확률 (0~1). 값이 높을수록 방어 성능이 우수."),
            ("RCS (Radar Cross Section)", "레이더에 반사되는 등가 면적 (㎡). 값이 작을수록 탐지가 어려운 스텔스 표적."),
            ("CEP (Circular Error Probable)", "유도탄의 유도 오차 반경 (m). 값이 작을수록 정밀한 무기."),
            ("ECM (Electronic Counter Measures)", "전자 방해 장치. ECM 지수가 높을수록 아군 레이더·유도탄 Pk 감소."),
            ("몬테카를로 시뮬레이션",   "동일 조건을 수천~수만 회 반복해 확률 분포를 추정하는 기법."),
            ("CVaR (Conditional VaR)",   "최악 5% 시나리오의 평균 생존율. 극단 상황 대비 지표."),
            ("REQ (Requirements)",        "요구조건. 생존율·격추율 임계값을 충족하는지 판정."),
            ("SM-2 / SM-6",               "함대공 미사일. SM-2는 중거리, SM-6는 장거리 및 탄도미사일 요격 가능."),
            ("CIWS (근접 방어 체계)",     "최후 방어선. 20mm 기관포로 근거리 위협을 자동 요격."),
            ("SAM (함대공 미사일)",        "Surface-to-Air Missile. 함정에서 발사하는 대공 미사일."),
            ("이지스 (Aegis)",            "위상 배열 레이더 기반 통합 전투 체계. 동시 다수 표적 추적·교전 가능."),
            ("HGV (극초음속 활공체)",     "마하 5 이상으로 날아오는 활공 탄도체. 기동성이 높아 요격이 매우 어려움."),
            ("교전 음영구역",             "레이더 사각지대 또는 최소 교전 거리 이내의 구역."),
            ("파고 / 해상 상태",          "Sea State 0~6. 파고가 높을수록 센서·무기 명중률 저하."),
        ]

        _STEPS = [
            ("1", "시뮬레이터 시작", "이 창 하단의 [🚀 시뮬레이터 시작] 버튼을 클릭합니다."),
            ("2", "아군 함정 선택",   "좌측 패널 상단에서 단독함 또는 편대 프리셋을 선택합니다."),
            ("3", "위협 설정",        "적군 위협 종류, 공격 수, 파고·날씨 조건을 설정합니다."),
            ("4", "반복 횟수 설정",   "몬테카를로 반복 횟수를 설정합니다. (빠른 확인 1,000 / 표준 10,000 / 정밀 100,000)"),
            ("5", "시뮬레이션 실행",  "[▶ 시뮬레이션 실행] 버튼을 클릭하고 진행 바를 기다립니다."),
            ("6", "결과 확인",        "결과 탭에서 격추율, 생존율, REQ 충족 여부, CVaR 등을 확인합니다."),
            ("7", "보고서 내보내기",  "결과 탭 하단 버튼으로 Excel(.xlsx) 또는 PNG 보고서를 저장합니다."),
            ("8", "실행 기록 재사용", "실행 기록 탭에서 이전 시뮬레이션 설정을 불러와 재실행할 수 있습니다."),
        ]

        _FAQ = [
            ("몬테카를로 횟수를 얼마로 설정해야 하나요?",
             "빠른 확인 1,000회 · 표준 분석 10,000회 · 정밀 분석 100,000회를 권장합니다.\n"
             "횟수가 많을수록 결과가 안정적이나 시간이 오래 걸립니다."),
            ("Pk가 0으로 나옵니다. 왜인가요?",
             "선택한 무기의 사거리 밖이거나 RCS가 너무 작아 탐지 자체가 불가능한 경우입니다.\n"
             "위협의 접근 거리와 해당 무기의 최대 사거리를 비교해 보세요."),
            ("REQ가 빨간색(미달)으로 표시됩니다.",
             "격추율 또는 생존율이 요구조건 임계값 미만입니다.\n"
             "함정 수를 늘리거나 SM-6 등 장거리 무기 탑재 수를 늘려 보세요."),
            ("엑셀 보고서는 어디에 저장되나요?",
             "실행 파일(또는 app_main.py)과 같은 폴더에 자동 저장됩니다.\n"
             "파일명에 날짜·시각이 포함되므로 여러 번 실행해도 덮어쓰이지 않습니다."),
            ("3D 전장은 어떻게 보나요?",
             "시뮬레이션을 한 번 실행한 뒤 '교전 분석' 탭에서 '🌐 3D 전장' 서브탭을 누르세요.\n"
             "실제 위성 지도 위에 함정·미사일 궤적·교전 지점이 시간순으로 재생됩니다. "
             "마우스 휠로 줌, 드래그로 회전할 수 있으며 인터넷 연결이 필요합니다."),
            ("편대 모드와 단독함 모드의 차이는 무엇인가요?",
             "단독함 모드는 이지스함 1척의 방어 성능을 분석합니다.\n"
             "편대 모드는 이지스함 + 호위함 등 다중 함정이 협력해 방어하는 시나리오를 시뮬레이션합니다."),
        ]

        w = QWidget()
        outer = QVBoxLayout(w)
        outer.setContentsMargins(0, 0, 0, 0)
        inner_tabs = QTabWidget()
        outer.addWidget(inner_tabs)

        def _scroll():
            sc = QScrollArea()
            sc.setWidgetResizable(True)
            sc.setStyleSheet(f"QScrollArea {{ border: none; background: {C_BG}; }}")
            iw = QWidget()
            iw.setStyleSheet(f"background: {C_BG};")
            lay = QVBoxLayout(iw)
            lay.setContentsMargins(14, 12, 14, 12)
            lay.setSpacing(7)
            return sc, iw, lay

        def _card(stripe):
            c = QFrame()
            c.setObjectName("card")
            c.setStyleSheet(f"""
                QFrame#card {{ background: #161d2a; border-radius: 8px;
                    border-left: 4px solid {stripe}; }}
                QFrame#card QLabel {{ background: transparent; }}
            """)
            cl = QVBoxLayout(c)
            cl.setContentsMargins(14, 9, 14, 11)
            cl.setSpacing(5)
            return c, cl

        # ── 용어 설명 (좌측 띠 = 파랑)
        sc, iw, lay = _scroll()
        for term, desc in _GLOSSARY:
            c, cl = _card(C_ACCENT)
            t = QLabel(term); t.setWordWrap(True)
            t.setStyleSheet(f"color: {C_ACCENT}; font-weight: bold; font-size: 15px;")
            d = QLabel(desc); d.setWordWrap(True)
            d.setStyleSheet(f"color: {C_SUBTEXT}; font-size: 14px;")
            cl.addWidget(t); cl.addWidget(d)
            lay.addWidget(c)
        lay.addStretch(1); sc.setWidget(iw)
        inner_tabs.addTab(sc, "📖  용어 설명")

        # ── 실행 순서 (좌측 띠 = 주황, 단계 번호 배지)
        sc, iw, lay = _scroll()
        for step, title, desc in _STEPS:
            c, cl = _card(C_ORANGE)
            top = QHBoxLayout(); top.setSpacing(9)
            num = QLabel(step)
            num.setFixedSize(24, 24)
            num.setAlignment(Qt.AlignmentFlag.AlignCenter)
            num.setStyleSheet(
                f"background-color: {C_ORANGE}; color: #0d1117; "
                f"border-radius: 12px; font-weight: bold;")
            top.addWidget(num)
            ti = QLabel(title)
            ti.setStyleSheet(f"color: {C_ACCENT}; font-weight: bold; font-size: 15px;")
            top.addWidget(ti); top.addStretch(1)
            cl.addLayout(top)
            d = QLabel(desc); d.setWordWrap(True)
            d.setStyleSheet(f"color: {C_SUBTEXT}; font-size: 14px;")
            cl.addWidget(d)
            lay.addWidget(c)
        lay.addStretch(1); sc.setWidget(iw)
        inner_tabs.addTab(sc, "🗺️  실행 순서")

        # ── FAQ (좌측 띠 = 초록)
        sc, iw, lay = _scroll()
        for q, a in _FAQ:
            c, cl = _card(C_GREEN)
            ql = QLabel(f"Q.  {q}"); ql.setWordWrap(True)
            ql.setStyleSheet(f"color: {C_ACCENT}; font-weight: bold; font-size: 15px;")
            al = QLabel(a); al.setWordWrap(True)
            al.setStyleSheet(f"color: {C_TEXT}; font-size: 14px;")
            cl.addWidget(ql); cl.addWidget(al)
            lay.addWidget(c)
        lay.addStretch(1); sc.setWidget(iw)
        inner_tabs.addTab(sc, "❓  FAQ")

        return w

    # ─────────────────────────────────────────────────────────────────────────
    def _build_feature_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea {{ border: none; background: {C_BG}; }}")
        inner = QWidget()
        inner.setStyleSheet(f"background: {C_BG};")
        v = QVBoxLayout(inner)
        v.setContentsMargins(14, 12, 14, 12)
        v.setSpacing(7)
        for name, desc in _FEATURES:
            card = QFrame()
            card.setObjectName("card")
            card.setStyleSheet(f"""
                QFrame#card {{ background: #161d2a; border-radius: 8px;
                    border-left: 4px solid {C_ACCENT}; }}
                QFrame#card QLabel {{ background: transparent; }}
            """)
            cl = QVBoxLayout(card)
            cl.setContentsMargins(14, 9, 14, 11)
            cl.setSpacing(5)
            nlbl = QLabel(name)
            nlbl.setWordWrap(True)
            nlbl.setStyleSheet(f"color: {C_ACCENT}; font-weight: bold; font-size: 15px;")
            dlbl = QLabel(desc)
            dlbl.setWordWrap(True)
            dlbl.setStyleSheet(f"color: {C_SUBTEXT}; font-size: 14px;")
            cl.addWidget(nlbl)
            cl.addWidget(dlbl)
            _apply_term_tooltip(nlbl, name + ' ' + desc)
            _apply_term_tooltip(dlbl, desc)
            v.addWidget(card)
        v.addStretch(1)
        scroll.setWidget(inner)
        layout.addWidget(scroll)
        return w

    def _build_changelog_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(0, 0, 0, 0)
        changelog = []
        cl_path = _res('app_changelog.json')
        if os.path.exists(cl_path):
            try:
                with open(cl_path, encoding='utf-8-sig') as f:
                    changelog = json.load(f)
            except Exception:
                pass
        if not changelog:
            layout.addWidget(QLabel("app_changelog.json 없음"))
            return w
        # 최신 버전이 위로 오도록 역순 표시(app_changelog.json은 오래된→최신 순 저장)
        latest_ver = changelog[-1].get('version', '') if changelog else ''
        changelog = list(reversed(changelog))

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea {{ border: none; background: {C_BG}; }}")
        inner = QWidget()
        inner.setStyleSheet(f"background: {C_BG};")
        v = QVBoxLayout(inner)
        v.setContentsMargins(14, 10, 14, 12)
        v.setSpacing(7)

        # minor 계열(major.minor)별 좌측 색 띠 — 같은 작업 묶음을 시각적으로 그룹화
        _PAL = ['#5b9bd5', '#70ad47', '#e6a23c', '#c0504d',
                '#8e7cc3', '#4bacc6', '#d9846c', '#9bbb59']
        series = {}

        def _color(ver):
            p = ver.lstrip('v').split('.')
            key = (p[0], p[1]) if len(p) >= 2 else (ver,)
            if key not in series:
                series[key] = _PAL[len(series) % len(_PAL)]
            return series[key]

        prev_date = None
        for entry in changelog:
            ver = entry.get('version', '')
            date = entry.get('date', '')
            items = entry.get('changes', [])
            is_latest = (ver == latest_ver)
            if date != prev_date:
                if prev_date is not None:
                    v.addSpacing(8)   # 날짜 그룹 사이 여백
                drow = QHBoxLayout()
                dh = QLabel(f"📅   {date}")
                dh.setStyleSheet(
                    f"color: #eaf2ff; font-weight: bold; font-size: 14px; "
                    f"background: #16403a; border-radius: 6px; "
                    f"border-left: 4px solid {C_ACCENT}; padding: 7px 14px;")
                drow.addWidget(dh)
                drow.addStretch(1)        # 날짜 칩을 내용 크기로(좌측 정렬)
                v.addLayout(drow)
                prev_date = date
            col = _color(ver)
            for item in items:
                v.addWidget(self._make_change_card(ver, item, col, is_latest))
        v.addStretch(1)
        scroll.setWidget(inner)
        layout.addWidget(scroll)
        return w

    @staticmethod
    def _make_change_card(ver: str, item: str, color: str, is_latest: bool) -> QWidget:
        """변경 1건을 카드(버전·유형 배지 + 본문, 좌측 계열 색 띠)로 변환."""
        s = str(item).strip()
        kind, badge_color = None, None
        for k, c in (("추가", C_GREEN), ("수정", C_ORANGE), ("삭제", C_RED)):
            if s.startswith(k):
                kind, badge_color, s = k, c, s[len(k):].strip()
                break
        card = QFrame()
        card.setObjectName("card")
        bg = '#2a2512' if is_latest else '#161d2a'
        card.setStyleSheet(f"""
            QFrame#card {{ background: {bg}; border-radius: 8px;
                border-left: 4px solid {color}; }}
            QFrame#card QLabel {{ background: transparent; }}
        """)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(14, 9, 14, 10)
        cl.setSpacing(5)
        top = QHBoxLayout()
        top.setSpacing(9)
        vlabel = QLabel(f"⭐ {ver}" if is_latest else ver)
        vlabel.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 14px;")
        top.addWidget(vlabel)
        if kind:
            badge = QLabel(kind)
            badge.setStyleSheet(
                f"background-color: {badge_color}; color: #0d1117; "
                f"border-radius: 8px; padding: 1px 10px; font-weight: bold;")
            badge.setFixedHeight(20)
            top.addWidget(badge)
        top.addStretch(1)
        cl.addLayout(top)
        body = QLabel(s)
        body.setWordWrap(True)
        body.setStyleSheet(f"color: {C_TEXT}; font-size: 14px;")
        cl.addWidget(body)
        return card

    def _build_plan_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        _PLANS = [
            # ── 상시 — 정책·유지 규칙 (버전 무관, 항상 적용) ──────────────────
            ("📋 정책", "상시", "감사 체크포인트 (마이너 버전마다)",
             "모든 마이너 버전 빌드 직전, 변경 유형별 감사 1회: "
             "엔진/로직→코드감사(/code-review) · DB/수치→현실성 수치감사 · UI→회귀확인 · "
             "아키텍처전환→코드감사+로직트레이스 · 신기능→새 군사용어 사전 갱신. "
             "메이저 블록(v11·v12…) 완료 시 전체 회귀 MC + 누적 수치감사. (CLAUDE.md '감사 정책' 정본)"),
            ("📋 정책", "상시", "설정 패널 구조 유지",
             "기본/환경/방어전술/항공자산/고급 5개 묶음 분리는 완료. "
             "신규 기능 추가 시 반드시 이 5개 묶음 중 적합한 곳에 배치. "
             "묶음 간 경계가 모호해지면 재조정."),
            # ── v15.x — AI & 자율화: v15.2 학습 즉시예측 구현 완료(v16.14.01),
            #    작전급 캠페인의 핵심 부품으로 연동 완료 → _PLANS에서 제거(이력은 changelog).
            # ── v20.5 기능 유효성 재점검 = 트랙 전체 완료(B-1~B-5·C) → 제거.
            #    성과는 changelog·감사보고서에 있다(SM-3 외기권 문턱 정정으로 하위 BMD
            #    계층 순증분 9배 회수 · 표적 난이도·HGV 활공·탄도 강하 정규 승격 ·
            #    레이더 침묵↔회피 기동 짝 규명 · 스탠드오프 교전 기본 ON · 레이저는
            #    음성 확정 종결). 남은 잔여(대잠 균형)는 아래 v16.1로 계속 추적.
            # ── v16.x — 전장 도메인 확장 (아래 v16.1은 미완) ──────────────────
            ("v16.1", "중간", "대잠전 균형 (능동 소나 EMCON — 딜레마 성립, 피해 규모는 잔여)",
             "능동 소나 역탐지의 효과가 결과에 드러나지 않던 문제의 뿌리를 규명해 해결했다(대잠 접촉 유지). "
             "원인은 재탐색 횟수가 아니라 그 앞단이었다 — 잠수함의 추정 위치 오차를 1.5km로 고정해 둬서 "
             "대잠 항공기가 잠수함이 어디 있는지 항상 아는 셈이었고, 그래서 탐지 확률이 97%로 사실상 고정돼 "
             "탐지가 보장됐다. 탐지가 보장되면 잠수함이 핑을 역탐지해 도주해도 아무 이득이 없어 "
             "EMCON 딜레마가 성립할 수 없다. 이제 접촉이 끊긴 시간만큼 수색 구역이 넓어져(잠수함 속도 × 경과 시간), "
             "도주가 실제 생존으로 이어진다. "
             "【남은 과제】딜레마는 성립했으나 효과의 절대 크기가 아직 작다 — 위협 잠수함이 원거리에서 발사한 뒤 "
             "이탈해 애초에 아군 피해 규모 자체가 작기 때문이다. 잠수함의 교전 방식(접근·재공격·매복)을 "
             "손대야 대잠전이 실제 균형을 갖는다."),
            # ── v17.x — 군수·미래 전장 ────────────────────────────────────────
            # v17.2 지향성 에너지 무기(레이저) = v20.5에서 **최종 판정 종결**(v18.05.08).
            #   재측정(표적 난이도·회피 기동 기본 ON 상태, 3시나리오×15시드): 레이저 격추 0.00 —
            #   드론이 함대에 도달조차 못 하고(피격 0·손실 0) 원거리 전멸해 5km 교전권에 표적이
            #   들어오지 않는다. SM-3·HGV와 달리 **판정이 뒤집히지 않았다**(물리 오류가 아니라
            #   교리의 문제이고, 현실의 함정 레이저도 아직 드론 방어 주력이 아니다 = 음성이 곧
            #   현실 반영). 메커니즘은 실험적 기능으로 보존. 근거 정본 = 막다른 길 메모리.
            #   → 향후 계획에서 제거(계획 탭은 '앞으로 할 일'만 — 판정 끝난 항목은 이력으로).
            # ── v18.x — 작전급 해군 캠페인: v18.1~18.7 전부 구현 완료(v17.01.01~09).
            #    완료 항목은 _PLANS에서 제거(향후 계획만 유지) — 이력은 changelog·감사보고서.md.
            # ── v19.x — 공군 작전급 (v18 해군 캠페인 완성 → 다음 메이저) ────────
            # 선행 필수: v18 캠페인 완성 (완료)
            # v19.1 공군 전력 & 임무 모델 = 구현 완료(v18.01.01) — 제거.
            # v19.2 제공권 통제 모델(격자·해군 교전 연동) = 구현 완료(v18.01.02) — 제거.
            # v19.3 방공망 제압 SEAD/DEAD = 구현 완료(v18.01.03) — 제거.
            # v19.4 전략 폭격 & 적 기지 타격 = 구현 완료(v18.01.04) — 제거.
            # v19.5 공군 작전 캠페인 통합(CAS 자동 요청·타임라인) = 구현 완료(v18.01.05~06) — 제거.
            # ── v20.x — 육군 작전급 ────────────────────────────────────────────
            # 선행 필수: v18 완성
            # ── v21.x — 육해공 통합 합동작전 ──────────────────────────────────
            # 선행 필수: v17·v18·v19 전체 완성
            # v21.1 합동작전 사령부(JCS) 자원 충돌 경고 = 구현 완료(v21.03.01) — 제거.
            #   각 군 독립 배정의 충돌(협조 미비·육군 미참여·화력 중복)을 지휘부가 경고로
            #   표면화하는 상시 관찰층(교전 무영향, 조정·경고 수준).
            # v21.2 합동 화력 지원 = 구현 완료(v21.01.01) — 제거.
            ("v21.3", "중간", "합동 작전 시나리오 라이브러리",
             "육해공 통합 시나리오 3종: 한반도 전면전 72시간 · 대만해협 위기 · 독도·이어도 제한전. "
             "각 시나리오: 각 군 초기 전력 + 작전 목표 + 성공 판정 기준. 순수 군사 교육·분석 목적."),
            # v21.4 합동작전 통합 보고서 = 구현 완료(v21.02.01) — 제거.
            #   군별 기여도는 각 군을 뺀 전역을 실제로 재실행해 분해(순서 의존 없는 평균).
            #   ⚠ 남은 한계 2가지는 v21.4의 결함이 아니라 하위 층의 성질이라 여기 안 남긴다:
            #     ①손실 지표가 편성 전반에서 둔감해 '손실을 얼마나 줄였나'가 0에 가깝다
            #     ②캠페인 플래그가 아군·적을 함께 켜는 '도메인' 성격이라 방공망 제압은
            #       기여도로 분해할 수 없다(분리 스위치 신설은 별도 seq).
            # ── 선택 트랙 — v20 완료 후 별도 판단 ────────────────────────────
            ("선택", "중간", "육해공 전력 DB 심화 확충",
             "육군 작전급(v20)까지 로드맵 완성 후, 각 도메인 전력 DB를 실측 제원 기준으로 확충. "
             "공군: 적 공군 기종(J-20·J-16·Su-35 등)·아군 공중급유기·전자전기·무인기 추가로 제공권 모델 정교화. "
             "해군·육군: 실측 교전에서 효과가 발현하는 항목 위주(무작정 규모 확대는 중복 시나리오만 늘어 지양). "
             "각 도메인 층이 완성된 뒤 통합 상태에서 한 번에 현실성 확충하는 게 효율적."),
            ("선택", "높음", "자율 학습 전술 AI 심화 (자가개선·공진화)",
             "지속 전장 강화학습·적 지휘 AI 동시 학습(self-play)·자가개선 루프는 메커니즘까지 "
             "구축 완료(학습 정책이 기본 전술을 일관되게 능가). 남은 것은 선택적 심화 — "
             "자가개선 루프의 장기 실전 운영과, 더 깊은 전장·넓은 행동공간 위에서의 공진화 심화. "
             "당장의 정규 로드맵이 아니라 여력 있을 때 선택적으로 밀어붙이는 트랙."),
            ("선택", "매우 높음", "멀티플레이어 대전",
             "한 명은 이지스 함대, 다른 한 명은 적 항모전단을 실시간 지휘. "
             "네트워크 동기화·지연보상이 핵심 난관. "
             "단일 시뮬 완성도와 별개 트랙 — v20 완료 후 분석 목적 충족도에 따라 착수 여부 판단."),
        ]

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea {{ border: none; background: {C_BG}; }}")
        inner = QWidget()
        inner.setStyleSheet(f"background: {C_BG};")
        v = QVBoxLayout(inner)
        v.setContentsMargins(14, 12, 14, 12)
        v.setSpacing(7)

        # 좌측 색 띠·배지 = 난이도 (이 탭의 핵심 정보)
        diff_color = {'매우 높음': '#c0392b', '높음': '#e74c3c', '중간': C_ORANGE,
                      '낮음': '#2ecc71', '상시': '#5b9bd5'}

        def _section_header(text: str) -> QLabel:
            hl = QLabel(text)
            hl.setStyleSheet(
                f"color:{C_SUBTEXT}; font-size:12px; font-weight:bold;"
                f" letter-spacing:1px; padding:6px 2px 2px 2px;")
            return hl

        _seen_policy = _seen_roadmap = False
        for ver, diff, title, desc in _PLANS:
            # 상시(정책) 블록과 버전 로드맵 블록 사이에 섹션 헤더
            if diff == '상시' and not _seen_policy:
                v.addWidget(_section_header("■  상시 · 정책 / 유지 규칙"))
                _seen_policy = True
            elif diff != '상시' and not _seen_roadmap:
                v.addWidget(_section_header("■  버전 로드맵"))
                _seen_roadmap = True
            col = diff_color.get(diff, '#7f8c9a')
            card = QFrame()
            card.setObjectName("card")
            card.setStyleSheet(f"""
                QFrame#card {{ background: #161d2a; border-radius: 8px;
                    border-left: 4px solid {col}; }}
                QFrame#card QLabel {{ background: transparent; }}
            """)
            cl = QVBoxLayout(card)
            cl.setContentsMargins(14, 9, 14, 11)
            cl.setSpacing(5)
            top = QHBoxLayout()
            top.setSpacing(9)
            vlabel = QLabel(ver)
            vlabel.setStyleSheet(f"color: {C_ACCENT}; font-weight: bold; font-size: 14px;")
            top.addWidget(vlabel)
            badge = QLabel(diff)
            badge.setStyleSheet(
                f"background-color: {col}; color: #0d1117; "
                f"border-radius: 8px; padding: 1px 10px; font-weight: bold;")
            badge.setFixedHeight(20)
            top.addWidget(badge)
            top.addStretch(1)
            cl.addLayout(top)
            title_lbl = QLabel(title)
            title_lbl.setWordWrap(True)
            title_lbl.setStyleSheet("color: #eaf2ff; font-weight: bold; font-size: 15px;")
            cl.addWidget(title_lbl)
            desc_lbl = QLabel(desc)
            desc_lbl.setWordWrap(True)
            desc_lbl.setStyleSheet(f"color: {C_SUBTEXT}; font-size: 14px;")
            cl.addWidget(desc_lbl)
            _apply_term_tooltip(title_lbl, title + ' ' + desc)
            _apply_term_tooltip(desc_lbl, desc)
            v.addWidget(card)
        v.addStretch(1)
        scroll.setWidget(inner)
        layout.addWidget(scroll)
        return w

    # ── DB 탭 공통 헬퍼 ──────────────────────────────────────────────────────
    # 카테고리별 배경/전경색
    _CAT_BG  = {'대공': '#2a1010', '대함': '#2a1a08', '대잠': '#0a1228'}
    _CAT_FG  = {'대공': '#ff8080', '대함': '#ffaa55', '대잠': '#6699ff'}
    _LIST_SS = f"""
        QListWidget {{
            background:{C_BG}; border:none; outline:none; font-size:13px;
        }}
        QListWidget::item {{
            padding:5px 10px; border-bottom:1px solid {C_BORDER};
        }}
        QListWidget::item:selected {{
            background:{C_ACCENT}; color:#000; font-weight:bold;
        }}
        QListWidget::item:hover:!selected {{ background:{C_PANEL}; }}
    """

    # 종류별 목록 좌측 색 띠 (대공=적·대함=주황·대잠=청)
    _STRIPE = {'대공': '#c0504d', '대함': '#e6a23c', '대잠': '#5b9bd5'}

    def _make_list_panel(self, entries: list, mode: str,
                         cat_color: bool = False,
                         display_key: str | None = None,
                         tooltip_fn=None,
                         stripe_color: str | None = None) -> tuple:
        """
        왼쪽 QListWidget + 오른쪽 SpecSheetPanel QSplitter를 생성해 반환.
        entries: [(key, info), ...]
        mode: 'enemy' | 'weapon' | 'ship' | 'aircraft'
        cat_color: True면 category 필드 기반 행 색상 적용
        display_key: info 안에서 표시 이름으로 쓸 키 (None이면 항목 key 사용)
        stripe_color: 지정 시 모든 항목 좌측에 색 띠 (단일 종류 탭용)
        """
        name_list = QListWidget()
        ss = self._LIST_SS
        if stripe_color:
            ss = ss.replace(
                "border-bottom:1px solid",
                f"border-left:4px solid {stripe_color}; border-bottom:1px solid",
            )
        name_list.setStyleSheet(ss)

        for key, info in entries:
            label = info.get(display_key, key) if display_key else key
            it = QListWidgetItem(f"  {label}")
            if cat_color:
                cats = info.get('category', '대공')
                # FRIENDLY_DB는 리스트, ENEMY_DB는 문자열
                c = cats[0] if isinstance(cats, list) else cats
                it.setBackground(QColor(self._CAT_BG.get(c, C_BG)))
                it.setForeground(QColor(self._CAT_FG.get(c, C_TEXT)))
            else:
                it.setForeground(QColor(C_ACCENT))
            if tooltip_fn:
                it.setToolTip(tooltip_fn(key, info))
            name_list.addItem(it)

        spec_panel = SpecSheetPanel()
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setStyleSheet(
            "QSplitter::handle { background: " + C_BORDER + "; width: 2px; }")
        splitter.addWidget(name_list)
        splitter.addWidget(spec_panel)
        splitter.setSizes([230, 9999])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        def _on_select(row):
            if row < 0 or row >= len(entries):
                spec_panel.clear()
                return
            k, e = entries[row]
            spec_panel.show_unit(k, e, _SPEC_DETAIL_DB.get(k, {}), mode)

        name_list.currentRowChanged.connect(_on_select)
        return splitter, name_list, spec_panel

    def _wrap_splitter(self, splitter) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(4)
        lay.addWidget(splitter, stretch=1)
        return w

    # ── 적군 DB 탭 ─────────────────────────────────────────────────────────
    def _build_enemy_db_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        if not _V7_OK:
            layout.addWidget(QLabel("엔진 로드 실패 — 적군 DB를 표시할 수 없습니다."))
            return w

        _normalize_enemy_db()
        db = V7_ENEMY_DB

        # 유형별 분류
        _AIRCRAFT_T = {'전투기', '폭격기', '전폭기'}
        _SHIP_T     = {'고속정', '초계함', '호위함', '구축함', '항모', '순양함', '상륙함'}
        _MISSILE_T  = {'순항미사일', '탄도미사일', '극초음속활공체', '저고도기동탄도', '대방사미사일'}
        _SUB_T      = {'잠수함'}

        def _split(types):
            return [(k, v) for k, v in db.items() if v.get('type','') in types]

        aircraft_e = _split(_AIRCRAFT_T)
        ship_e     = _split(_SHIP_T)
        missile_e  = _split(_MISSILE_T)
        sub_e      = _split(_SUB_T)

        inner_tabs = QTabWidget()
        inner_tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border:none; }}
            QTabBar::tab {{ background:{C_PANEL}; color:{C_TEXT}; padding:4px 14px; }}
            QTabBar::tab:selected {{ background:{C_ACCENT}; color:#000; }}
        """)

        # ── 전투기 탭 ─────────────────────────────────────────────────────
        sp, _, _ = self._make_list_panel(aircraft_e, 'enemy', cat_color=False,
                                         stripe_color=self._STRIPE['대공'])
        inner_tabs.addTab(self._wrap_splitter(sp), f"✈  전투기  ({len(aircraft_e)})")

        # ── 함정 탭 ───────────────────────────────────────────────────────
        sp, _, _ = self._make_list_panel(ship_e, 'enemy', cat_color=False,
                                         stripe_color=self._STRIPE['대함'])
        inner_tabs.addTab(self._wrap_splitter(sp), f"⚓  함정  ({len(ship_e)})")

        # ── 무기 탭 (카테고리 색상) ────────────────────────────────────────
        sp, nl, _ = self._make_list_panel(missile_e, 'enemy', cat_color=True)
        # 범례 행 추가
        legend = QHBoxLayout()
        legend.setSpacing(12)
        for cat, fg in self._CAT_FG.items():
            bg = self._CAT_BG[cat]
            lbl = QLabel(f"  {cat}  ")
            lbl.setStyleSheet(
                f"background:{bg}; color:{fg}; border-radius:3px;"
                f" font-size:11px; padding:1px 4px;")
            legend.addWidget(lbl)
        legend.addStretch()
        mw = QWidget()
        ml = QVBoxLayout(mw)
        ml.setContentsMargins(6, 6, 6, 6)
        ml.setSpacing(4)
        ml.addLayout(legend)
        ml.addWidget(sp, stretch=1)
        inner_tabs.addTab(mw, f"🚀  무기  ({len(missile_e)})")

        # ── 잠수함 탭 ─────────────────────────────────────────────────────
        sp, _, _ = self._make_list_panel(sub_e, 'enemy', cat_color=False,
                                         stripe_color=self._STRIPE['대잠'])
        inner_tabs.addTab(self._wrap_splitter(sp), f"🤿  잠수함  ({len(sub_e)})")

        layout.addWidget(inner_tabs, stretch=1)

        pk_note = QLabel(
            "  ⚠  적 플랫폼별 Pk 수치는 공개 자료 기반 추정값입니다 (±15~20%). "
            "소수점 정밀도는 상대 비교를 위한 것이며 실측 데이터가 아닙니다.")
        pk_note.setStyleSheet(
            f"color:#e67e22; font-size:11px; padding:3px 4px;")
        pk_note.setWordWrap(True)
        layout.addWidget(pk_note)
        return w

    # ── 아군 DB 탭 ─────────────────────────────────────────────────────────
    def _build_friendly_db_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        if not _V7_OK:
            layout.addWidget(QLabel("엔진 로드 실패 — 아군 DB를 표시할 수 없습니다."))
            return w

        inner_tabs = QTabWidget()
        inner_tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border:none; }}
            QTabBar::tab {{ background:{C_PANEL}; color:{C_TEXT}; padding:4px 14px; }}
            QTabBar::tab:selected {{ background:{C_ACCENT}; color:#000; }}
        """)

        # 무기 DB (카테고리 색상)
        inner_tabs.addTab(self._build_weapon_sub_tab(), f"🚀  무기  ({len(V7_FRIENDLY_DB)})")

        # 함정 DB (잠수함 제외)
        surface_ships = [(k, v) for k, v in V7_SHIP_DB.items()
                         if not v.get('is_submarine', False)]
        inner_tabs.addTab(self._build_ship_sub_tab(surface_ships,
                          stripe_color=self._STRIPE['대함']),
                          f"⚓  함정  ({len(surface_ships)})")

        # 잠수함 DB
        subs = [(k, v) for k, v in V7_SHIP_DB.items()
                if v.get('is_submarine', False)]
        inner_tabs.addTab(self._build_ship_sub_tab(subs,
                          stripe_color=self._STRIPE['대잠']),
                          f"🤿  잠수함  ({len(subs)})")

        # 항공 DB
        aircraft_e = list(V7_AIRCRAFT_DB.items())
        sp, _, _ = self._make_list_panel(aircraft_e, 'aircraft', cat_color=False,
                                         stripe_color=self._STRIPE['대공'])
        inner_tabs.addTab(self._wrap_splitter(sp),
                          f"🚁  항공  ({len(aircraft_e)})")

        layout.addWidget(inner_tabs, stretch=1)
        return w

    def _build_weapon_sub_tab(self) -> QWidget:
        wpn_entries = list(V7_FRIENDLY_DB.items())

        # 범례 행
        legend = QHBoxLayout()
        legend.setSpacing(12)
        for cat, fg in self._CAT_FG.items():
            bg = self._CAT_BG[cat]
            lbl = QLabel(f"  {cat}  ")
            lbl.setStyleSheet(
                f"background:{bg}; color:{fg}; border-radius:3px;"
                f" font-size:11px; padding:1px 4px;")
            legend.addWidget(lbl)
        legend.addStretch()

        sp, _, _ = self._make_list_panel(wpn_entries, 'weapon', cat_color=True)
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(4)
        lay.addLayout(legend)
        lay.addWidget(sp, stretch=1)
        pk_note = QLabel(
            "  ⚠  Pk 수치는 공개 자료 기반 추정값입니다 (±15~20%). 실측 데이터가 아닙니다.")
        pk_note.setStyleSheet(
            f"color:#e67e22; font-size:11px; padding:3px 4px;")
        lay.addWidget(pk_note)
        return w

    def _build_ship_sub_tab(self, ship_entries: list | None = None,
                            stripe_color: str | None = None) -> QWidget:
        if ship_entries is None:
            ship_entries = list(V7_SHIP_DB.items())

        def _tip(key, info):
            display = info.get('display', key)
            inv = info.get('default_inventory', {})
            lines = [f"【{display} 기본 탑재】"]
            for wname, cnt in inv.items():
                lines.append(f"  • {wname}: {'무한' if cnt >= 9999 else cnt}발")
            return "\n".join(lines)

        # display 필드로 표시
        disp_entries = [(k, v) for k, v in ship_entries]
        name_list = QListWidget()
        _ss = self._LIST_SS
        if stripe_color:
            _ss = _ss.replace(
                "border-bottom:1px solid",
                f"border-left:4px solid {stripe_color}; border-bottom:1px solid",
            )
        name_list.setStyleSheet(_ss)
        for key, info in disp_entries:
            display = info.get('display', key)
            it = QListWidgetItem(f"  {display}")
            it.setForeground(QColor(C_ACCENT))
            it.setToolTip(_tip(key, info))
            name_list.addItem(it)

        spec_panel = SpecSheetPanel()
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setStyleSheet(
            "QSplitter::handle { background: " + C_BORDER + "; width: 2px; }")
        splitter.addWidget(name_list)
        splitter.addWidget(spec_panel)
        splitter.setSizes([230, 9999])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        def _on_select(row):
            if row < 0 or row >= len(disp_entries):
                spec_panel.clear()
                return
            skey, sentry = disp_entries[row]
            spec_panel.show_unit(skey, sentry, _SPEC_DETAIL_DB.get(skey, {}), 'ship')

        name_list.currentRowChanged.connect(_on_select)
        return self._wrap_splitter(splitter)

