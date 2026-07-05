# -*- coding: utf-8 -*-
"""
_audit_make_pdf.py — 종합 감사 보고서를 PDF(보고서 형식)로 출력 (빌드 제외 도구)

reportlab + 맑은 고딕. 군 보고서 양식으로 조판.
종합 감사를 할 때마다 이 스크립트의 BLOCK·내용을 그 블록에 맞게 갱신해
실행하면, 블록별 PDF가 `감사보고서/` 폴더에 누적된다(블록당 1개).

사용: python _audit_make_pdf.py  →  감사보고서/감사보고서_v16-2.pdf
"""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                TableStyle, HRFlowable)

ROOT = os.path.dirname(os.path.abspath(__file__))
BLOCK = 'v16.13-14'                              # 감사 블록 — 매 감사마다 갱신
REPORT_DIR = os.path.join(ROOT, '감사보고서')   # 블록별 PDF 누적 폴더
os.makedirs(REPORT_DIR, exist_ok=True)
OUT = os.path.join(REPORT_DIR, f'감사보고서_{BLOCK}.pdf')

pdfmetrics.registerFont(TTFont('Malgun', r'C:/Windows/Fonts/malgun.ttf'))
pdfmetrics.registerFont(TTFont('MalgunBd', r'C:/Windows/Fonts/malgunbd.ttf'))

NAVY = colors.HexColor('#1b2a4a')
STEEL = colors.HexColor('#2e4a6b')
LIGHT = colors.HexColor('#eef2f7')
GREEN = colors.HexColor('#1e7d34')
GREY = colors.HexColor('#5b6470')

styles = getSampleStyleSheet()
def S(name, **kw):
    base = dict(fontName='Malgun', fontSize=9.5, leading=13, textColor=colors.black)
    base.update(kw)
    return ParagraphStyle(name, **base)

st_title  = S('title', fontName='MalgunBd', fontSize=20, leading=26, alignment=TA_CENTER, textColor=NAVY)
st_sub    = S('sub', fontSize=11, leading=15, alignment=TA_CENTER, textColor=STEEL)
st_h2     = S('h2', fontName='MalgunBd', fontSize=12.5, leading=17, textColor=NAVY, spaceBefore=10, spaceAfter=4)
st_body   = S('body', fontSize=9.5, leading=14)
st_cell   = S('cell', fontSize=8.3, leading=11)
st_cellb  = S('cellb', fontName='MalgunBd', fontSize=8.6, leading=11, alignment=TA_CENTER)
st_pass   = S('pass', fontName='MalgunBd', fontSize=9, leading=11, alignment=TA_CENTER, textColor=GREEN)
st_na     = S('na', fontName='MalgunBd', fontSize=8, leading=11, alignment=TA_CENTER, textColor=GREY)
st_meta   = S('meta', fontSize=9, leading=13, textColor=colors.black)
st_foot   = S('foot', fontSize=7.5, leading=10, textColor=GREY, alignment=TA_CENTER)

def P(t, s=st_body): return Paragraph(t, s)

doc = SimpleDocTemplate(OUT, pagesize=A4,
                        leftMargin=18*mm, rightMargin=18*mm,
                        topMargin=18*mm, bottomMargin=16*mm,
                        title='종합 감사 보고서 — v16.13~16.14 블록', author='합동 통합방어 시뮬레이터')
flow = []

# ── 표제 ──
flow += [P('종 합 감 사 보 고 서', st_title),
         Spacer(1, 3*mm),
         P('v16.13~16.14 블록 — 지속전장 보급·레이저·즉시예측·직접편성', st_sub),
         Spacer(1, 4*mm),
         HRFlowable(width='100%', thickness=1.4, color=NAVY), Spacer(1, 5*mm)]

# ── 개요(메타) 표 ──
meta_rows = [
    [P('감사 일자', st_cellb), P('2026-07-05', st_cell), P('판정', st_cellb), P('통과 (9영역 PASS)', st_pass)],
    [P('대상 범위', st_cellb), P('v16.13.03 ~ v16.14.02 (직전 v16.12~13 감사 904cbb6 이후 15커밋). 지속전장 보급·레이저·즉시예측·직접편성', st_cell), P('발견 항목', st_cellb), P('0 건', st_pass)],
    [P('변경 규모', st_cellb), P('engine_combat.py(RAS 탄약 재보급·레이저 DEW+SHIP_POWER 전력모델, 전장 전용) · app_main.py(온보딩·해석 배너·반사실 토글영향 워커·예상전황 학습 대리모델·아군 직접 편성 다이얼로그) · engine_core.py(신규 DB: SHIP_POWER)', st_cell), P('트리거', st_cellb), P('① v16→v17 major 전환 직전', st_cell)],
    [P('감사 방식', st_cellb), P('무인 모드 — 착수 승인=9영역 포괄동의. 각 마이너 shift-left(개별 리뷰, RAS medium·레이저 high) 후 누적 상호작용·통합·하위호환 점검 중심', st_cell), P('근거 규칙', st_cellb), P('CLAUDE.md 종합 감사 9영역', st_cell)],
    [P('소요/특성', st_cellb), P('빌드 성공 · GUI 스모크 RESULT_CODE=0(직접편성 전 경로) · 신규 토글 조합 전장 MC NaN 0 · 전장 5.0s/run 정상', st_cell), P('무인/수동', st_cellb), P('100% 무인 · 사용자 개입 0회', st_cell)],
    [P('점검 규모', st_cellb), P('회귀 8케이스×26지표 bit-identical(엔진 신규 전부 기본 OFF) · audit_static_scan 25/25 · 신규 토글 조합 MC · 구버전 cfg 하위호환', st_cell), P('재감사', st_cellb), P('발견 0 — 조치 불요', st_cell)],
]
mt = Table(meta_rows, colWidths=[22*mm, 78*mm, 20*mm, 54*mm])
mt.setStyle(TableStyle([
    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#c2ccd8')),
    ('BACKGROUND', (0,0), (0,-1), LIGHT),
    ('BACKGROUND', (2,0), (2,-1), LIGHT),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('LEFTPADDING', (0,0), (-1,-1), 5), ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
]))
flow += [mt, Spacer(1, 6*mm)]

# ── 9영역 판정표 ──
flow += [P('1. 9개 영역 점검 결과', st_h2)]
hdr = [P('#', st_cellb), P('영역', st_cellb), P('판정', st_cellb), P('점검 내용 · 근거', st_cellb)]
rows = [
    ('①', '코드·로직', 'PASS', '신기능 체크리스트 무결 — 3종세트(enable_ras_rearm·enable_laser_dew 각각 체크박스+cfg빌드 isChecked+cfg로드 setChecked/엔진 cfg.get) · 신규 stats laser_kills MC 3경로 완비(monte_carlo_v7·_mc_batch_worker·monte_carlo_lhs) · db_specsheet 정합(정적) · import 빌드검증 · 부모 무수정(레이저·RAS는 BattleEngine/전장 전용, OFF bit-identical 회귀PASS) · shift-left 개별리뷰(RAS medium·레이저 high)'),
    ('②', 'DB·수치', 'PASS', 'SHIP_POWER 전력값 공개값 정합 — KDX-III 발전 9MW급(가스터빈 함정 정합) · 레이저 유효 5km(HELIOS 실측 근거 주석) · B2(정조대왕급 최신)만 laser_kw 100kW 탑재 · radar/prop 상대비율 합리. 승격 2종(기뢰·USV)은 레이블만 · 즉시예측/직접편성 DB 무변경'),
    ('③', '회귀', 'PASS', 'audit_verify_regression.py — 8케이스 × 26지표 bit-identical. 엔진 신규(RAS·레이저)는 전부 기본 OFF·전장 전용 → 단발 골든 무영향. 즉시예측·직접편성은 순수 표시/UI'),
    ('④', '통합 MC + 성능', 'PASS', '신규 토글 조합(레이저+RAS+무인+DMO+기뢰+직접편성) 전장 MC n=20: NaN/Inf 0 · win/draw/loss=0.65/0.2/0.15(합 1.0) · 범위 [0,1] OK · 전장 5.0s/run 정상(단발의 약 45배=1800틱, 급증 없음) · laser_kills=0은 레이저 효능 음성 결론과 일치(버그 아님)'),
    ('⑤', 'exe·빌드', 'PASS', '빌드 성공(v16.14.02, joblib/sklearn 서브모듈 포함) · GUI 스모크 RESULT_CODE=0(직접 편성 버튼→모달 다이얼로그→담기×2→확정→"적용 중" 레이블→시뮬 실행→요격률 표시 전 경로) · 워커 잔존 0(closeEvent 정리)'),
    ('⑥', '위생', 'PASS', '정적 25/25(신규 3종세트 2개 반영 후) · 완료 설계문서 2종(forecast·fleet_custom) _archive/plans/ 이동 · README forecast_features.py 기재·단계 v16.14 · changelog·변경이력 정합 · 죽은코드 0'),
    ('⑦', '하위호환', 'PASS', '신규 플래그(ras_rearm·laser_dew·fleet_custom) 전부 누락한 구버전 cfg dict로 run_v7_simulation(요격률 0.32)·run_battle_simulation(outcome loss·score 0.001) 정상 실행·NaN 0·laser_kills 기본 0. DB 키 구조 무변경 → 저장 시나리오 호환'),
    ('⑧', '수치·단위', 'PASS', '레이저 dwell max(dist_m,1.0) 0나눗셈 가드·도달출력 min 상한·거리>사거리 시 리셋 · forecast 예측 win/score clip[0,1]·cost expm1 역변환·승리당비용 win>0 가드 · 직접편성 척수 정수 sum · 확률값 clamp 위반 0'),
    ('⑨', '리소스 누수', 'PASS', '신규 워커 ShowcaseCompareWorker·CounterfactualWorker closeEvent에서 requestInterruption→quit→wait→terminate 정리 · 차트 figure plt.close · FleetCustomDialog는 모달 QDialog(QThread 아님)라 exec 후 자동 정리 · frames/_log mc_mode 가드 무변경'),
]
st_find = S('find', fontName='MalgunBd', fontSize=8, leading=11, alignment=TA_CENTER, textColor=colors.HexColor('#b25e00'))
data = [hdr]
for num, area, verdict, detail in rows:
    if verdict == 'PASS':
        vs, vt = st_pass, 'PASS'
    elif verdict == 'NA':
        vs, vt = st_na, '해당없음'
    else:  # '발견1' 등
        vs, vt = st_find, verdict
    data.append([P(num, st_cellb), P(area, st_cell), P(vt, vs), P(detail, st_cell)])
t = Table(data, colWidths=[8*mm, 26*mm, 14*mm, 126*mm], repeatRows=1)
t.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), NAVY),
    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
    ('FONTNAME', (0,0), (-1,0), 'MalgunBd'),
    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#c2ccd8')),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, LIGHT]),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('LEFTPADDING', (0,0), (-1,-1), 4), ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
]))
flow += [t, Spacer(1, 1.5*mm),
         P('범례 — PASS: 점검 통과 · 해당없음: 블록과 무관해 생략 · 발견N: N건 발견(그 자리 수정·재감사). 9영역 전부 PASS/해당없음이어야 블록 종료 선언.', st_foot),
         P('감사 범위 주석 — v16.13~16.14 블록. 지속 전장 RAS 탄약 재보급·지향성 에너지 무기(레이저 DEW)+SHIP_POWER 전력모델(엔진, 전장 전용·기본 OFF)·온보딩/해석/토글 실제영향 배너(UI)·예상전황 학습 대리모델·아군 함대 직접 편성(UI)·기뢰전/무인 함정 정규 승격(레이블). 각 마이너가 shift-left(개별 code-review, RAS medium·레이저 high)를 거쳐 종합 감사는 누적 상호작용·통합·하위호환 점검에 집중. v16.x 도메인 소진 — v17/v18(작전급 캠페인) 진입 준비 완료.', st_foot),
         Spacer(1, 6*mm)]

# ── 종합 판정 ──
flow += [P('2. 종합 판정', st_h2)]
verdict = Table([[P('통과', S('v', fontName='MalgunBd', fontSize=13, alignment=TA_CENTER, textColor=colors.white)),
                  P('9개 영역 전부 PASS · 발견 0건 · 판단필요 0건 — 지속전장 보급·레이저·즉시예측·직접편성 15커밋의 통합 상태 안전 확인. 엔진 신규(RAS·레이저)는 전부 기본 OFF·전장 전용으로 OFF bit-identical 보장, 신규 토글 조합 MC도 NaN 0·범위 OK. 직접 편성 UI는 GUI 스모크 전 경로 검증. v16.x 소진, 작전급 캠페인(v18) 진입 준비 완료', st_cell)]],
                colWidths=[24*mm, 150*mm])
verdict.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (0,0), GREEN),
    ('BACKGROUND', (1,0), (1,0), colors.HexColor('#e7f3ea')),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#bcd4c2')),
    ('LEFTPADDING', (0,0), (-1,-1), 8), ('TOPPADDING', (0,0), (-1,-1), 7), ('BOTTOMPADDING', (0,0), (-1,-1), 7),
]))
flow += [verdict, Spacer(1, 6*mm)]

# ── 산출물 ──
flow += [P('3. 산출물 · 검증 경로', st_h2),
         P('• <b>audit_verify_regression.py</b> — 8케이스×26지표 골든 bit-identical. 엔진 신규(RAS·레이저)는 전부 기본 OFF·전장 전용이라 단발 골든 무영향.', st_body),
         P('• <b>audit_static_scan.py</b> — 정적 점검 25/25 PASS. 이번 블록 메타회고로 3종세트 자동검사에 enable_ras_rearm·enable_laser_dew 추가(23→25항목).', st_body),
         P('• <b>GUI 스모크(직접 편성 경로)</b> — 직접 편성 버튼→모달 다이얼로그→함정 담기×2→확정→"적용 중" 레이블→시뮬 실행→요격률 표시. RESULT_CODE=0. 엔진 직접호출 우회 없음. 모달 QDialog는 Desktop(uia) 계층에서 포착.', st_body),
         P('• <b>조합 상호작용 MC</b> — 레이저+RAS+무인+DMO+기뢰+직접편성 전장 MC n=20 NaN/범위오류 0. 전장 5.0s/run 성능 정상. 구버전 cfg 하위호환(단발·전장) 정상.', st_body),
         P('• <b>단위검증</b> — SHIP_POWER 전력값 공개제원 대조 · 레이저 dwell 0나눗셈 가드 · forecast 예측 clip[0,1]·expm1 · laser_kills MC 3경로 집계.', st_body),
         P('• <b>감사보고서.md</b> — 텍스트 감사 보고서에 v16.13~16.14 블록 섹션 기록(최신순 누적).', st_body),
         Spacer(1, 5*mm)]

# ── 메타 회고 ──
flow += [P('4. 메타 회고 (감사 절차 자체 개선)', st_h2),
         P('이번 감사에서 식별·이행한 절차 개선:', st_body),
         P('• <b>3종세트 자동검사 확장(즉시 반영)</b> — enable_ras_rearm·enable_laser_dew를 audit_static_scan.py의 chk_flag_triplet 목록에 추가(23→25항목). 이번 블록 신규 토글 2종이 자동검사 목록에서 빠져 ①에서 수동 확인한 빈틈을 도구로 굳혀 다음 감사부터 자동 검출.', st_body),
         P('다음 숙제(지속) — 병합/커밋열 감사에서 /code-review 타깃 빈 diff는 각 마이너 shift-left(개별 리뷰, RAS medium·레이저 high)로 대체 유지. GUI abort(중단 클릭) 시나리오 미자동화. enable_recon_drone은 _restore_cfg for-루프 복원이라 정규식 불일치로 여전히 제외(restore 검사 일반화 숙제).', st_meta),
         Spacer(1, 6*mm)]

# ── 환경·커밋 정보 (재현성) ──
flow += [P('5. 환경 · 커밋 정보 (재현성)', st_h2)]
env_rows = [
    [P('HEAD 커밋', st_cellb), P('6aaaade (v16.14.02 직접 편성 UI)', st_cell), P('Python', st_cellb), P('3.14', st_cell)],
    [P('OS', st_cellb), P('Windows 11', st_cell), P('numpy', st_cellb), P('2.x (CPU)', st_cell)],
    [P('PyQt6 / WebEngine', st_cellb), P('6.x', st_cell), P('matplotlib', st_cellb), P('3.10.x', st_cell)],
    [P('pywinauto', st_cellb), P('0.6.9', st_cell), P('reportlab', st_cellb), P('4.5.x', st_cell)],
]
et = Table(env_rows, colWidths=[32*mm, 44*mm, 34*mm, 64*mm])
et.setStyle(TableStyle([
    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#c2ccd8')),
    ('BACKGROUND', (0,0), (0,-1), LIGHT), ('BACKGROUND', (2,0), (2,-1), LIGHT),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('LEFTPADDING', (0,0), (-1,-1), 5), ('RIGHTPADDING', (0,0), (-1,-1), 5),
    ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
]))
flow += [et, Spacer(1, 6*mm)]

# ── 차기 감사 ──
flow += [P('차기 종합 감사 — 작전급 캠페인 엔진(v18) 아키텍처 전환 완료 시 또는 다음 major 전환 직전(트리거 ①/②). PDF는 감사보고서/감사보고서_{블록}.pdf로 누적.', st_meta),
         Spacer(1, 6*mm),
         HRFlowable(width='100%', thickness=0.6, color=GREY), Spacer(1, 2*mm),
         P('합동 통합방어 시뮬레이터 · 종합 감사 보고서 · 자동 생성(_audit_make_pdf.py) · 2026-07-05', st_foot)]

doc.build(flow)
print('생성 완료:', OUT)
