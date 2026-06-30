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
BLOCK = 'v16-3'                                  # 감사 블록 — 매 감사마다 갱신
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
                        title='종합 감사 보고서 — v16 블록', author='합동 통합방어 시뮬레이터')
flow = []

# ── 표제 ──
flow += [P('종 합 감 사 보 고 서', st_title),
         Spacer(1, 3*mm),
         P('v16 블록 — 전장 도메인 확장 (DMO·C-RAM·전자좌표기만·기뢰전·항만방어)', st_sub),
         Spacer(1, 4*mm),
         HRFlowable(width='100%', thickness=1.4, color=NAVY), Spacer(1, 5*mm)]

# ── 개요(메타) 표 ──
meta_rows = [
    [P('감사 일자', st_cellb), P('2026-06-30', st_cell), P('판정', st_cellb), P('통과 (9영역 PASS)', st_pass)],
    [P('대상 범위', st_cellb), P('v16.06.01 ~ v16.11.02 (직전 v16.05 감사 756840e 이후 9커밋). 신기능 5종·적 밸런스 2종', st_cell), P('발견 항목', st_cellb), P('2 건 (⑥위생: 완료 plan 아카이브·승격 레이블)', st_cellb)],
    [P('변경 규모', st_cellb), P('engine_combat.py +173(DMO·좌표기만·기뢰·항만방어 로직) · engine_core.py +110(USV·해안포대·적편대) · app_main.py +121(토글·시나리오·_PLANS) · db_specsheet.py +112', st_cell), P('트리거', st_cellb), P('① v16→v17 major 전환 직전', st_cell)],
    [P('감사 방식', st_cellb), P('무인 모드 — 착수 승인=9영역 포괄동의. 각 마이너 shift-left(개별 리뷰) 후 누적 상호작용·통합 점검 중심', st_cell), P('근거 규칙', st_cellb), P('CLAUDE.md 종합 감사 9영역', st_cell)],
    [P('소요/특성', st_cellb), P('빌드 exit0 · GUI 스모크 RESULT_CODE=0 · 전 신규토글 ON 조합 NaN 0 · 입체포화 MC40 0.785±0.067', st_cell), P('무인/수동', st_cellb), P('100% 무인 · 사용자 개입 0회', st_cell)],
    [P('점검 규모', st_cellb), P('회귀 8케이스×26지표 bit-identical · audit_static_scan 20/20 · MC40 안정성·성능 · 구버전 cfg 하위호환 · 전토글 ON 조합', st_cell), P('재감사', st_cellb), P('⑥발견 2건 조치 후 정적 재PASS', st_cell)],
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
    ('①', '코드·로직', 'PASS', '신기능 8항목: enable 3종세트 4종(dmo·coord_deception·mine_threat·minesweeping) 무결 · 신규 stats(mines_struck·ships_lost_to_mine) MC 3경로(monte_carlo_v7·_mc_batch_worker·monte_carlo_lhs) 전부 집계 · normalize is_suicide setdefault · db_specsheet 동기화. 전역 DB mutate 0 · cfg=dict(cfg) 유지 · 부모무수정(_pick_target threat_pos 기본인자 추가·BattleEngine 오버라이드 없음) · OFF no-op=회귀 bit-identical · 죽은코드 0'),
    ('②', 'DB·수치', 'PASS', 'db_specsheet 112 = 엔티티 DB 합(ENEMY 68+FRIENDLY 14+SHIP 23+AIRCRAFT 7) · 누락 0. 신규 자폭 무인수상정(USV) 수치(speed 14m/s·hp 1·rcs 5)가 자폭 무인보트로 합리적. 적편대 교리규모(v16.05~06 검증분) · DB키 일관(항만 침투 복합 preset 키 전부 ENEMY_DB 존재)'),
    ('③', '회귀', 'PASS', 'audit_verify_regression.py — 8케이스 × 26지표 bit-identical. 신규 토글 전부 OFF no-op·골든 무영향. is_suicide setdefault·_pick_target threat_pos 기본인자가 RNG 순서 미변경(결정론 보존)'),
    ('④', '통합 MC + 성능', 'PASS', '이지스 기동전단 vs 입체포화 MC40 mean_intercept 0.785±0.067 · VLS소진율 0.925 · NaN/Inf 0 · MC40 wall 14.0s. 단발 wall(입체포화·항만침투복합) 정상(<수초)·이전 블록 대비 급증 없음'),
    ('⑤', 'exe·빌드', 'PASS', '빌드 exit 0 · GUI 스모크 PASS(홈→앱→시뮬→요격률 표시→정상종료, RESULT_CODE=0) · 번들무결(스모크 간접) · MC 워커풀·abort 경로 무변경(Job Object 구조해결 유지)'),
    ('⑥', '위생', '발견2', '발견1: 구현완료 plan_v16_4~v16_8 5개 루트 잔존 → _archive/plans/ 이동. 발견2: DMO·전자좌표기만 검증완료인데 ‘실험적’ 레이블 stale → 정규 승격(레이블 제거·기본 OFF 유지). 둘 다 v16.11.02 조치. _PLANS 미래형 잔류 0·정적 20/20(신규 chk_completed_plans 포함)·죽은코드 0'),
    ('⑦', '하위호환', 'PASS', '신규 토글 4종 전부 누락한 구버전 cfg dict로 run_v7_simulation 정상 실행(요격률 0.095·NaN 0). DB 키 구조 무변경 → 저장 시나리오 호환'),
    ('⑧', '수치·단위', 'PASS', '전 신규 토글 ON 조합(DMO+coord_decep+mine+sweep 동시) 실행 OK·intercept_rate 0.686 · NaN/Inf 0 · 확률값(요격률·Pk) [0,1] clamp 위반 0'),
    ('⑨', '리소스 누수', 'PASS', '기뢰 _log(_apply_mine_exposure)는 if not self._mc_mode 가드 내부 · 이번 블록 frames/figure 누적 변경 없음 · 결과 히스토리 상한 무변경'),
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
         P('감사 범위 주석 — v16 전장 도메인 확장 블록. 신기능 5종(분산해양작전 DMO·해안 C-RAM/SAM 포대·전자 좌표 기만·기뢰전 MIW·항만 거점 방어[자폭 무인수상정 USV]) + 적 밸런스 2종(항모 킬 체인·전면전 포화 규모화). 각 마이너가 shift-left(개별 code-review·정적스캔)를 거쳐 종합 감사는 누적 상호작용·통합 상태 점검에 집중. v16.x 도메인 소진 — v17(군수·미래전장) 진입 준비 완료.', st_foot),
         Spacer(1, 6*mm)]

# ── 종합 판정 ──
flow += [P('2. 종합 판정', st_h2)]
verdict = Table([[P('통과', S('v', fontName='MalgunBd', fontSize=13, alignment=TA_CENTER, textColor=colors.white)),
                  P('9개 영역 전부 PASS · 발견 2건(⑥위생: 완료 plan 아카이브·DMO/좌표기만 정규 승격)은 v16.11.02에서 그 자리 조치·정적 재PASS · 판단필요 0건 — v16 블록 종료 선언, v17 진입 준비 완료', st_cell)]],
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
         P('• <b>audit_verify_regression.py</b> — 8케이스×26지표 골든 bit-identical. 신규 토글 전부 OFF no-op·is_suicide/_pick_target 기본인자가 RNG 순서 미변경.', st_body),
         P('• <b>audit_static_scan.py</b> — 정적 점검 20/20 PASS. 이번 블록 메타회고로 chk_completed_plans 신설(구현완료 plan_v&lt;N&gt;_&lt;M&gt; 루트 잔존 자동 경고 → _archive/plans/).', st_body),
         P('• <b>_audit_gui_smoke.py</b> — GUI 자동화 스모크(홈→앱→시뮬→요격률 표시) RESULT_CODE=0. 엔진 직접호출 우회 없이 GUI 워커 경로 무인 검증.', st_body),
         P('• <b>통합 MC 측정</b> — 입체포화 MC40 mean_intercept 0.785±0.067·NaN 0·wall 14.0s. 전 신규토글 ON 조합 단발 NaN/clamp 위반 0.', st_body),
         P('• <b>감사보고서.md</b> — 텍스트 감사 보고서에 v16 블록 섹션 기록(최신순 누적).', st_body),
         Spacer(1, 5*mm)]

# ── 메타 회고 ──
flow += [P('4. 메타 회고 (감사 절차 자체 개선)', st_h2),
         P('이번 감사에서 식별·이행한 절차 개선:', st_body),
         P('• <b>chk_completed_plans 신설(즉시 반영)</b> — 구현완료 설계문서(plan_v&lt;N&gt;_&lt;M&gt;_*.md)가 _archive/plans/ 아닌 루트에 잔존하면 경고하는 정적 검사를 audit_static_scan.py에 추가(19→20항목). 이번 블록에서 plan_v16_4~8 5개 루트 잔존을 수동 발견한 빈틈을 도구로 굳혀, 다음 감사부터 자동 검출.', st_body),
         P('다음 숙제 — 병합 후 /code-review 빈 diff는 각 마이너 shift-left(개별 리뷰)로 대체 중(알려진 빈틈 유지). GUI abort 시나리오는 워커풀 무변경이라 이번 생략했으나 _audit_gui_smoke.py에 abort 미구현 — 지속 숙제. 프리셋 편성 count 합↔표기 정합 자동검사도 자유텍스트 파싱 난도로 미해소 유지.', st_meta),
         Spacer(1, 6*mm)]

# ── 환경·커밋 정보 (재현성) ──
flow += [P('5. 환경 · 커밋 정보 (재현성)', st_h2)]
env_rows = [
    [P('HEAD 커밋', st_cellb), P('d114fb1 (+v16.11.02 감사 조치)', st_cell), P('Python', st_cellb), P('3.14', st_cell)],
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
         P('합동 통합방어 시뮬레이터 · 종합 감사 보고서 · 자동 생성(_audit_make_pdf.py) · 2026-06-30', st_foot)]

doc.build(flow)
print('생성 완료:', OUT)
