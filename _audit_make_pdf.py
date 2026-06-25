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
BLOCK = 'v16-2'                                  # 감사 블록 — 매 감사마다 갱신
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
                        title='종합 감사 보고서 — v16 블록 2차', author='합동 통합방어 시뮬레이터')
flow = []

# ── 표제 ──
flow += [P('종 합 감 사 보 고 서', st_title),
         Spacer(1, 3*mm),
         P('v16 블록 2차 — 사이버전 · 극초음속 활공 궤적 · 대잠 접촉 단절', st_sub),
         Spacer(1, 4*mm),
         HRFlowable(width='100%', thickness=1.4, color=NAVY), Spacer(1, 5*mm)]

# ── 개요(메타) 표 ──
meta_rows = [
    [P('감사 일자', st_cellb), P('2026-06-25', st_cell), P('판정', st_cellb), P('통과 (9영역 PASS)', st_pass)],
    [P('대상 범위', st_cellb), P('v16.02.04 ~ v16.04.04 (직전 v16 감사 425f378 이후 6커밋)', st_cell), P('발견 항목', st_cellb), P('1 건 (낮음·잠재)', st_cellb)],
    [P('변경 규모', st_cellb), P('engine_combat.py +142줄 중심 · engine_core.py +7(극초음속 편대) · app_main(체크박스 2종·헤더·_PLANS) · audit_static_scan(+2 플래그·오탐수정). 신규 토글 2종(cyber_warfare·hgv_glide) + sonar_emcon 접촉단절 구조', st_cell), P('트리거', st_cellb), P('① v16.1~v16.3 기능 묶음 완성', st_cell)],
    [P('감사 방식', st_cellb), P('무인 모드 — 착수 승인=9영역 포괄동의. ① 누적 diff 백그라운드 에이전트, exe는 GUI 자동화(pywinauto)', st_cell), P('근거 규칙', st_cellb), P('CLAUDE.md 종합 감사 9영역', st_cell)],
    [P('소요/특성', st_cellb), P('빌드 exit0(2회) · GUI 스모크 RESULT_CODE=0(재시도) · MC100 NaN/Inf 0 · 신기능 오버헤드 1.18배', st_cell), P('무인/수동', st_cellb), P('100% 무인 · 사용자 개입 0회', st_cell)],
    [P('점검 규모', st_cellb), P('회귀 8케이스×26지표(208 대조) · audit_static_scan 19/19 · ① 누적 diff 에이전트 · 구버전 cfg 하위호환(단발+전장) · MC100 안정성·성능', st_cell), P('재감사', st_cellb), P('1회 (낮음 1건 v16.04.04 수정 후)', st_cell)],
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
    ('①', '코드·로직', 'PASS', '누적 diff(425f378..HEAD) 에이전트 리뷰 — 치명/높음/중간 0건. 플래그 3종(cyber·hgv_glide·sonar_emcon) OFF no-op(random 미소비) 실증 · SoA _et_contact_lost_until 3곳(프록시·정의·append) 정합 · 부모 TimeStepEngine 무시그니처변경 · 3기능 동시 ON 충돌 없음(CIC 탐지배율↔HGV 미사일고도 독립축). 낮음 1건: _hgv_glide_alt 정점<2km 활공체 종말 고도 역전(현 DB 미발현)'),
    ('②', 'DB·수치', 'PASS', 'DF-17 마하8.7·사거리2500km·정점60km / YJ-21 마하9.9·1500km·40km — 공개 제원 정합. db_specsheet 둘 다 정합(편성만 신규, 제원 무변경). 신규 시나리오 ‘극초음속 포화 공격’(DF-17 12+YJ-21 8=20발)은 중국 로켓군 여단+055형 최대규모 일제로 타당'),
    ('③', '회귀', 'PASS', 'audit_verify_regression.py — 8케이스 × 26지표 골든 일치. 신규 random 호출(사이버 침투·HGV 갱신·능동핑 회피)은 전부 플래그 ON 경로 한정 → 기본 OFF에서 RNG 순서 불변·bit-identical'),
    ('④', '통합 MC + 성능', 'PASS', '입체 포화 100회 — 요격률 NaN/범위이상 0건. v16 신기능 순수 오버헤드 1.18배(230→272ms, 1.5배 미만 정상). 첫 측정 1.64배는 sonar_equation(기존 환경물리) 포함 불공정 → 분리 측정으로 규명 완료'),
    ('⑤', 'exe·빌드', 'PASS', '빌드 exit 0(2회) · 번들 무결성(신규 데이터파일 0·spec 무변경) · GUI 스모크 PASS(홈→앱→시뮬→요격률 표시, 첫 BLOCKED는 앱 진입 타이밍·재시도 RESULT_CODE=0) · MC abort 경로 미변경'),
    ('⑥', '위생', 'PASS', '정적스캔 19/19(chk_plans_stale 오탐수정 포함) · APP_VERSION=헤더=changelog 정합 · _PLANS v16.2/16.3 삭제 확인 · plan_v16_2_hgv_glide 구현완료→_archive/plans 이동 · 죽은코드 0 · 상수 정합'),
    ('⑦', '하위호환', 'PASS', '신규 키(cyber_warfare·hgv_glide) 없는 구버전 cfg dict로 단발·전장 둘 다 정상 실행(NaN 없음·cfg.get 폴백) · enable 3종세트(체크박스+isChecked+load) 완비'),
    ('⑧', '수치·단위', 'PASS', '_hgv_glide_alt 경계 15케이스(정점 0/10/60km × p 0~1) 전부 유한·비음수 · 사이버 계수(DL0.7·CIC0.6·JAM0.75·HGV0.85) 전부 [0,1] · 회피 점프 좌표 NaN 불가 · 접촉단절 상수 유효'),
    ('⑨', '리소스 누수', 'PASS', '신규 메서드(_cyber_update·_hgv_glide_update·_hgv_glide_alt) _log/frames 무관(상태 계산만) · 접촉단절 로그 2곳 모두 if not _mc_mode 가드 완비 · figure 신규 0'),
]
data = [hdr]
for num, area, verdict, detail in rows:
    vs = st_pass if verdict == 'PASS' else st_na
    vt = 'PASS' if verdict == 'PASS' else '해당없음'
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
         P('감사 범위 주석 — 신규 토글 2종(cyber_warfare·hgv_glide)·sonar_emcon 접촉단절 구조 모두 기본 OFF·실험적. 세 기능 공통 특성: 메커니즘은 단위검증으로 입증되나 실 시나리오 결과 효과는 적 편성·밸런스에 의존(ARM·능동소나 선례와 동일 패턴). 대잠 EMCON은 구조 변경(접촉 단절)에도 적격침 불변 — 근본 병목은 ASW 탐지가 아니라 아군 대잠 압도(별도 후속).', st_foot),
         Spacer(1, 6*mm)]

# ── 종합 판정 ──
flow += [P('2. 종합 판정', st_h2)]
verdict = Table([[P('통과', S('v', fontName='MalgunBd', fontSize=13, alignment=TA_CENTER, textColor=colors.white)),
                  P('9개 영역 전부 PASS · 발견 1건(낮음·잠재)은 v16.04.04에서 그 자리 수정·재감사 PASS — v16 블록 2차 종료 선언 가능', st_cell)]],
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
         P('• <b>① 누적 diff 에이전트 리뷰</b> — working tree clean(병합 후 빈 diff) 빈틈을 누적 diff(425f378..HEAD) 직접 투입으로 해소(general-purpose 에이전트, 치명/높음/중간 0건·낮음 1건).', st_body),
         P('• <b>audit_static_scan.py</b> — 정적 점검 19항목 19/19 PASS. 이번 블록에 cyber_warfare·hgv_glide 3종세트 검사 추가(17→19), chk_plans_stale 오탐 수정.', st_body),
         P('• <b>_audit_gui_smoke.py</b> — GUI 자동화 스모크(홈→앱→시뮬→요격률 표시) RESULT_CODE=0. 엔진 직접호출 우회 없이 GUI 워커 경로 무인 검증.', st_body),
         P('• <b>감사보고서.md</b> — 텍스트 감사 보고서에 v16 2차 블록 섹션 기록(최신순 누적).', st_body),
         Spacer(1, 5*mm)]

# ── 메타 회고 ──
flow += [P('4. 메타 회고 (감사 절차 자체 개선)', st_h2),
         P('이번 감사에서 식별·이행한 절차 개선:', st_body),
         P('• <b>chk_plans_stale 오탐 수정(즉시 반영)</b> — APP_VERSION seq(v16.04=극초음속 활공)와 _PLANS 로드맵 번호(v16.4=분산 해양작전)가 ‘v16.4’로 번호만 충돌해 stale 오탐을 냈다. 정적스캐너가 changelog 제목과 _PLANS 항목 제목의 핵심어 교집합을 비교하도록 보강 — 내용이 무관하면 미래 로드맵 항목으로 인정해 오탐 차단. (v16.3부터 구현 순서≠로드맵 순서로 어긋난 것이 원인)', st_body),
         P('• <b>cyber_warfare·hgv_glide 3종세트 정적스캔 편입</b> — 신규 2토글의 3종세트를 chk_flag_triplet 목록에 추가(17→19 항목)해 다음 감사부터 자동 검증.', st_body),
         P('다음 숙제 — ① GUI abort(MC 중단 후 워커 잔존) 시나리오를 _audit_gui_smoke.py에 추가(이번엔 abort 경로 미변경으로 ‘기존 보장’ 처리). ② wall-time 측정이 단발 무장소진 장기화로 자주 타임아웃 — 경량 고정틱 벤치 시나리오 마련.', st_meta),
         Spacer(1, 6*mm)]

# ── 환경·커밋 정보 (재현성) ──
flow += [P('5. 환경 · 커밋 정보 (재현성)', st_h2)]
env_rows = [
    [P('HEAD 커밋', st_cellb), P('edfa442 (+v16.04.04 감사 수정)', st_cell), P('Python', st_cellb), P('3.14', st_cell)],
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
flow += [P('차기 종합 감사 — 다음 큰 묶음 완료 시 또는 v17 major 전환 직전(트리거 ①/②). PDF는 감사보고서/감사보고서_v17.pdf로 누적.', st_meta),
         Spacer(1, 6*mm),
         HRFlowable(width='100%', thickness=0.6, color=GREY), Spacer(1, 2*mm),
         P('합동 통합방어 시뮬레이터 · 종합 감사 보고서 · 자동 생성(_audit_make_pdf.py) · 2026-06-25', st_foot)]

doc.build(flow)
print('생성 완료:', OUT)
