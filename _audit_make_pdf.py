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
BLOCK = 'v16.05'                                 # 감사 블록 — 매 감사마다 갱신
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
                        title='종합 감사 보고서 — v16.05 블록', author='합동 통합방어 시뮬레이터')
flow = []

# ── 표제 ──
flow += [P('종 합 감 사 보 고 서', st_title),
         Spacer(1, 3*mm),
         P('v16.05 블록 — 함정 재고·편성 현실화 · 적 포화 증강', st_sub),
         Spacer(1, 4*mm),
         HRFlowable(width='100%', thickness=1.4, color=NAVY), Spacer(1, 5*mm)]

# ── 개요(메타) 표 ──
meta_rows = [
    [P('감사 일자', st_cellb), P('2026-06-28', st_cell), P('판정', st_cellb), P('통과 (9영역 PASS/해당없음)', st_pass)],
    [P('대상 범위', st_cellb), P('v16.05.01 ~ v16.05.05 (직전 v16 2차 감사 0848ad7 이후 3 작업커밋 + 감사규칙 보강 + 본 감사 발견수정)', st_cell), P('발견 항목', st_cellb), P('1 건 (②DB 표기-실제 불일치)', st_cellb)],
    [P('변경 규모', st_cellb), P('engine_core.py DB 65줄(VLS 셀·편대 프리셋·호위함 무장) · audit_regression_golden.json 골든 58줄 · app_main(헤더·버전) · app_changelog.json · CLAUDE.md(감사규칙). engine_combat.py 무변경=교전 로직 0', st_cell), P('트리거', st_cellb), P('① 재고·편성 현실화 묶음 일단락', st_cell)],
    [P('감사 방식', st_cellb), P('무인 모드 — 착수 승인=9영역 포괄동의. DB 수치 블록이라 ②현실성·③회귀·④MC 중심, exe는 GUI 자동화(pywinauto)', st_cell), P('근거 규칙', st_cellb), P('CLAUDE.md 종합 감사 9영역', st_cell)],
    [P('소요/특성', st_cellb), P('빌드 exit0 · GUI 스모크 RESULT_CODE=0 · MC60×3시나리오 NaN/Inf 0 · SEAD 24발 SM-3/SM-6 소진율 1.0(재고 현실화 효과 입증)', st_cell), P('무인/수동', st_cellb), P('100% 무인 · 사용자 개입 0회', st_cell)],
    [P('점검 규모', st_cellb), P('회귀 8케이스×26지표(208 대조, 수정 전·후 2회) · audit_static_scan 19/19 · MC60×3시나리오 안정성·성능 · 구버전 cfg 하위호환', st_cell), P('재감사', st_cellb), P('②발견 수정 후 회귀 재PASS', st_cell)],
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
    ('①', '코드·로직', 'PASS', 'engine_combat.py 무변경 = 교전 로직 변화 0. app_main.py는 헤더·APP_VERSION만 갱신. 신규 enable_xxx·신규 클래스·신규 stats 키 0 → 3종세트·MC 3경로 영향 없음(정적 19/19). 변경은 전부 DB dict 값(SHIP_DB 재고·ENEMY_FLEET_PRESETS 편성)'),
    ('②', 'DB·수치', '발견1', 'VLS 셀 준수 정합 — KDX-III-B2 Mk.41 48셀=SM-3 16+SM-6 12+SM-2 20 정확 / DDG-51 96셀=SM류 72+ESSM quad 8셀+토마호크 8=88≤96 / CG-47 122셀=SM류 104+ESSM quad 6셀=110≤122(토마호크 16은 inventory 외·시뮬 무영향=경미·비채택). FFX-I/II/III SM-2 제거 현실 정합. 발견1: SEAD 프리셋 ARM 합이 표기(24발)와 달리 실제 20발 → v16.05.05에서 12+8+4=24로 정정(비율 3:2:1 유지)'),
    ('③', '회귀', 'PASS', 'audit_verify_regression.py — 8케이스 × 26지표 골든 일치(수정 전·후 2회 PASS). 적 증강·미함 재고는 골든 편대 미포함이라 무영향, 아군 호위함/KDX-III 골든은 갱신분 일치. engine_combat 무변경으로 RNG 순서 완전 보존'),
    ('④', '통합 MC + 성능', 'PASS', '입체포화/SEAD/A2AD MC60 각각 NaN/Inf 0. SEAD 24발: 요격률 0.971±0.030·SM-3/SM-6 소진율 1.0·VLS 고갈 0.175 — 재고 현실화가 요격탄 소진을 실제로 유발(적 위협 증강 지렛대를 수치로 입증). wall-time 정상(단발 0.43s·MC60 21~56s, 급증 없음)'),
    ('⑤', 'exe·빌드', 'PASS', '빌드 exit 0 · GUI 스모크 PASS(홈→앱→시뮬→요격률 표시→정상종료, RESULT_CODE=0) · 종료 후 잔존 프로세스 0 · DB만 변경이라 번들 데이터파일 무변경'),
    ('⑥', '위생', 'PASS', '정적스캔 19/19(버전정합 v16.05.05·_PLANS stale 0·db_specsheet 정합·파일명 stale 0) · changelog 연속(v16.05.01~05)·헤더·APP_VERSION 정합 · ②발견 수정으로 표기-실제 일치화 · 죽은코드 0'),
    ('⑦', '하위호환', 'PASS', '신규 키 없는 구버전 cfg dict로 단발 정상 실행(요격률 0.095 반환). DB 키 구조 무변경 → 저장 시나리오 호환. 신규 토글 없어 3종세트 추가분 없음'),
    ('⑧', '수치·단위', 'PASS', 'DB 값 전부 정수 재고·셀 수(km↔m·마하 환산 등 단위 혼동 무관) · MC 결과 NaN/Inf 0 · 확률값(요격률·소진율) 구조적 [0,1]'),
    ('⑨', '리소스 누수', 'NA', '엔진·시각화 무변경(DB dict 값만 변경) → frames/figure/_log 경로 전부 무관. 해당없음'),
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
         P('감사 범위 주석 — DB 수치·편성 변경 위주 블록(신규 토글·클래스 0). 아군 VLS 셀 준수(KDX-III-B2·미 DDG-51/CG-47·ESSM quad-pack)·한국 호위함 SM-2 미탑재 정정·적 포화 교리화(SEAD ARM·A2/AD 항공)가 핵심. 교훈: 재고 현실화 효과는 작은 편대·포화 시나리오에서 드러나고(SM-3/SM-6 완전 소진), 대편대는 함정 수로 압도 — 신기능 발현의 진짜 지렛대는 적 위협 증강.', st_foot),
         Spacer(1, 6*mm)]

# ── 종합 판정 ──
flow += [P('2. 종합 판정', st_h2)]
verdict = Table([[P('통과', S('v', fontName='MalgunBd', fontSize=13, alignment=TA_CENTER, textColor=colors.white)),
                  P('9개 영역 PASS/해당없음 · 발견 1건(②DB 표기-실제 불일치)은 v16.05.05에서 그 자리 수정·회귀 재PASS — v16.05 재고·편성 현실화 블록 종료 선언 가능', st_cell)]],
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
         P('• <b>audit_verify_regression.py</b> — 8케이스×26지표 골든 대조, 수정 전·후 2회 PASS. SEAD 프리셋 골든 미포함이라 ARM 정정 후에도 동작 보존.', st_body),
         P('• <b>audit_static_scan.py</b> — 정적 점검 19항목 19/19 PASS. 이번 블록 메타회고로 cp949 콘솔 인코딩 깨짐(em-dash)을 stdout utf-8 재구성으로 근본 수정(수동 PYTHONIOENCODING 의존 제거).', st_body),
         P('• <b>_audit_gui_smoke.py</b> — GUI 자동화 스모크(홈→앱→시뮬→요격률 표시) RESULT_CODE=0. 엔진 직접호출 우회 없이 GUI 워커 경로 무인 검증.', st_body),
         P('• <b>통합 MC 측정</b> — 입체포화/SEAD/A2AD 각 MC60: NaN/Inf 0·SEAD 24발 SM-3/SM-6 소진율 1.0(재고 현실화 효과 입증)·wall-time 정상.', st_body),
         P('• <b>감사보고서.md</b> — 텍스트 감사 보고서에 v16.05 블록 섹션 기록(최신순 누적).', st_body),
         Spacer(1, 5*mm)]

# ── 메타 회고 ──
flow += [P('4. 메타 회고 (감사 절차 자체 개선)', st_h2),
         P('이번 감사에서 식별·이행한 절차 개선:', st_body),
         P('• <b>audit_static_scan.py 콘솔 인코딩 깨짐 근본 수정(즉시 반영)</b> — cp949 기본 콘솔(Windows)에서 ‘—’(em-dash) 출력 시 UnicodeEncodeError로 스캐너가 중단됐다(이번 첫 실행에서 발생). 스크립트 진입부에 sys.stdout.reconfigure(encoding=utf-8)를 추가해 수동 PYTHONIOENCODING 의존을 제거 — 다음 감사부터 환경변수 없이 안정 실행.', st_body),
         P('다음 숙제 — 프리셋 편성 count 합과 changelog/헤더/코드 주석 표기 수치의 정합을 자동 검사하지 못해(이번 ARM 20 vs 24 발견은 수동 산술로 잡음) 빈틈으로 남음. 자유텍스트 파싱이라 난도가 높아 patch-queue에 ‘감사 개선’ 숙제로 등록. 이전 블록 숙제(GUI abort 시나리오·경량 wall-time 벤치)는 미해소 유지.', st_meta),
         Spacer(1, 6*mm)]

# ── 환경·커밋 정보 (재현성) ──
flow += [P('5. 환경 · 커밋 정보 (재현성)', st_h2)]
env_rows = [
    [P('HEAD 커밋', st_cellb), P('fb16c64 (+v16.05.05 감사 수정)', st_cell), P('Python', st_cellb), P('3.14', st_cell)],
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
flow += [P('차기 종합 감사 — 다음 큰 묶음 완료 시 또는 v17 major 전환 직전(트리거 ①/②). PDF는 감사보고서/감사보고서_{블록}.pdf로 누적.', st_meta),
         Spacer(1, 6*mm),
         HRFlowable(width='100%', thickness=0.6, color=GREY), Spacer(1, 2*mm),
         P('합동 통합방어 시뮬레이터 · 종합 감사 보고서 · 자동 생성(_audit_make_pdf.py) · 2026-06-28', st_foot)]

doc.build(flow)
print('생성 완료:', OUT)
