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
BLOCK = 'v16.12-13'                              # 감사 블록 — 매 감사마다 갱신
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
                        title='종합 감사 보고서 — v16.12~16.13 블록', author='합동 통합방어 시뮬레이터')
flow = []

# ── 표제 ──
flow += [P('종 합 감 사 보 고 서', st_title),
         Spacer(1, 3*mm),
         P('v16.12~16.13 블록 — 무인·자율 자산 (트랙 A·B·C) + 쇼케이스', st_sub),
         Spacer(1, 4*mm),
         HRFlowable(width='100%', thickness=1.4, color=NAVY), Spacer(1, 5*mm)]

# ── 개요(메타) 표 ──
meta_rows = [
    [P('감사 일자', st_cellb), P('2026-07-03', st_cell), P('판정', st_cellb), P('통과 (9영역 PASS)', st_pass)],
    [P('대상 범위', st_cellb), P('v16.12.01 ~ v16.13.02 (직전 v16.11.02 감사 9aad354 이후 7커밋). 무인·자율 4블록', st_cell), P('발견 항목', st_cellb), P('0 건', st_pass)],
    [P('변경 규모', st_cellb), P('engine_combat.py(자율교전·CEC 지휘저하·정찰/무인함정 로직) · app_main.py(쇼케이스 탭·신규 토글 3종·cfg 빌드 리팩터) · engine_core.py(신규 DB: 정찰 드론 2·USV/UUV·자폭 드론 군집)', st_cell), P('트리거', st_cellb), P('① v16→v17 major 전환 직전', st_cell)],
    [P('감사 방식', st_cellb), P('무인 모드 — 착수 승인=9영역 포괄동의. 각 트랙 shift-left(개별 리뷰, 트랙 C는 high) 후 누적 상호작용·통합·하위호환 점검 중심', st_cell), P('근거 규칙', st_cellb), P('CLAUDE.md 종합 감사 9영역', st_cell)],
    [P('소요/특성', st_cellb), P('빌드 exit0 · GUI 스모크 RESULT_CODE=0 · autonomous×타 신기능 8종 조합 NaN 0 · 기준 단발 0.21s', st_cell), P('무인/수동', st_cellb), P('100% 무인 · 사용자 개입 0회', st_cell)],
    [P('점검 규모', st_cellb), P('회귀 8케이스×26지표 bit-identical(CEC 저하 골든 갱신) · audit_static_scan 23/23 · 조합 스윕 8종 · 구버전 cfg 하위호환', st_cell), P('재감사', st_cellb), P('발견 0 — 조치 불요', st_cell)],
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
    ('①', '코드·로직', 'PASS', 'autonomous × 타 신기능 8종(cec_jammed·dmo·다방위·좌표기만·drone_swarm·무인함정·정찰드론·CEC저하) 조합 스윕 전부 NaN/범위 OK. 신기능 3종세트(autonomous·unmanned_assets 정적 자동검사) · 신규 stats(recon_losses·unmanned_lost) MC 3경로 집계 · shift-left 개별리뷰(트랙 C 코드리뷰 high 버그 0·효율 클린업 1건 _primary 재사용 수정). OFF no-op=회귀 bit-identical'),
    ('②', 'DB·수치', 'PASS', '신규 제원 공개값 정합 — 자폭 드론 군집(Shahed-136급 50m/s) · RQ-101 송골매(42m/s) · MQ-9B 시가디언(90m/s) · 자폭 USV(14m/s) · UUV(is_minesweeper). 각 트랙 baseline서 공개제원 대조 완료 · db_specsheet 항목수=DB 합(정적 PASS)'),
    ('③', '회귀', 'PASS', 'audit_verify_regression.py — 8케이스 × 26지표 bit-identical. 자율교전 신규 토글 OFF no-op. CEC 지휘저하(기본 동작)는 랴오닝-기본#3만 변경(기함 격침 시 원거리 요격탄 덜 소비) → 의도된 변경으로 골든 갱신·재PASS'),
    ('④', '통합 MC + 성능', 'PASS', 'autonomous×타 신기능 조합 스윕 NaN/Inf 0 · 기준 단발(이지스 vs 입체포화) 0.21s — 자율교전은 _friendly_defense에 경량 조건 추가라 이전 블록 대비 wall-time 급증 없음'),
    ('⑤', 'exe·빌드', 'PASS', '빌드 exit 0 · GUI 스모크 PASS(홈→앱→시뮬→요격률 표시→정상종료, RESULT_CODE=0, 쇼케이스 페이지 빌드 포함) · MC 워커풀·abort 경로 무변경'),
    ('⑥', '위생', 'PASS', '정적 23/23(autonomous·unmanned 3종세트 자동검사 추가) · 완료 plan 2종(track_c·unmanned_autonomy) _archive/plans/ 이동 · _PLANS v15.3 삭제 · README 단계 v16.13 · changelog·변경이력 정합 · 죽은코드 0'),
    ('⑦', '하위호환', 'PASS', '신규 플래그(autonomous·recon·unmanned·drone_swarm) 전부 누락한 구버전 cfg dict로 run_v7_simulation 정상 실행(요격률 0.167·NaN 0). DB 키 구조 무변경 → 저장 시나리오 호환'),
    ('⑧', '수치·단위', 'PASS', '조합 스윕 8종 전부 NaN/Inf/범위오류 0 · 확률값(요격률·Pk) [0,1] clamp 위반 0 · 자율교전 신규 나눗셈 없음(시간 비교·정수 salvo_bonus·self.t+45 덧셈)'),
    ('⑨', '리소스 누수', 'PASS', '자율교전 지휘권 인수 _log는 if not self._mc_mode 가드 내부 · 쇼케이스 ShowcaseCompareWorker closeEvent 정리·중복실행 방지 · frames/figure 누적 변경 없음(쇼케이스는 라벨 텍스트만)'),
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
         P('감사 범위 주석 — v16.12~16.13 무인·자율 블록. 트랙 A-1 정찰 드론 ISR·A-2 무인 함정 USV/UUV·B 적 무인기 군집·쇼케이스 탭·C 함정 자율 교전(지휘 강건성 + CEC 지휘 저하). 각 트랙이 shift-left(개별 code-review, 트랙 C는 high)를 거쳐 종합 감사는 누적 상호작용·통합·하위호환 점검에 집중. v15 무인·자율 로드맵 소진 — v17(군수·미래전장) 진입 준비 완료.', st_foot),
         Spacer(1, 6*mm)]

# ── 종합 판정 ──
flow += [P('2. 종합 판정', st_h2)]
verdict = Table([[P('통과', S('v', fontName='MalgunBd', fontSize=13, alignment=TA_CENTER, textColor=colors.white)),
                  P('9개 영역 전부 PASS · 발견 0건 · 판단필요 0건 — 무인·자율 4블록(트랙 A·B·C·쇼케이스) 통합 상태 안전 확인. 트랙 C의 CEC 지휘 저하(기본 동작 변경)가 cec_jammed·DMO·다방위 등과 조합해도 무결. v15 무인·자율 로드맵 소진, v17 진입 준비 완료', st_cell)]],
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
         P('• <b>audit_verify_regression.py</b> — 8케이스×26지표 골든 bit-identical(CEC 지휘저하 골든 갱신 후 재PASS). 자율교전 토글 OFF no-op.', st_body),
         P('• <b>audit_static_scan.py</b> — 정적 점검 23/23 PASS. 이번 블록 메타회고로 3종세트 자동검사에 enable_autonomous_engagement·unmanned_assets 추가(21→23항목).', st_body),
         P('• <b>_audit_gui_smoke.py</b> — GUI 자동화 스모크(홈→앱→시뮬→요격률 표시) RESULT_CODE=0. 쇼케이스 페이지 빌드 포함 검증. 엔진 직접호출 우회 없음.', st_body),
         P('• <b>조합 상호작용 스윕</b> — autonomous × 타 신기능 8종 조합 NaN/범위오류 0. 기준 단발 0.21s 성능 정상. 구버전 cfg 하위호환 정상.', st_body),
         P('• <b>단위검증</b> — 기함 격침 시 지휘권 인수 로그 2건·CEC 저하 발동(만료 t=85) · autonomous ON은 면역(저하 미발동) · 4조합(cec×auto) NaN 0.', st_body),
         P('• <b>감사보고서.md</b> — 텍스트 감사 보고서에 v16.12~16.13 블록 섹션 기록(최신순 누적).', st_body),
         Spacer(1, 5*mm)]

# ── 메타 회고 ──
flow += [P('4. 메타 회고 (감사 절차 자체 개선)', st_h2),
         P('이번 감사에서 식별·이행한 절차 개선:', st_body),
         P('• <b>3종세트 자동검사 확장(즉시 반영)</b> — enable_autonomous_engagement·unmanned_assets를 audit_static_scan.py의 chk_flag_triplet 목록에 추가(21→23항목). 이번 블록에서 수동 확인한 빈틈을 도구로 굳혀 다음 감사부터 자동 검출.', st_body),
         P('다음 숙제 — enable_recon_drone은 _restore_cfg가 for-루프 복원(for attr,key in [...])이라 개별 setChecked 정규식과 불일치해 오탐 FAIL → 목록서 제외(주석 명시). restore 검사가 for-루프 복원 패턴도 인식하도록 일반화하면 recon도 자동검사 가능(다음 감사 숙제). 병합 후 /code-review 빈 diff는 각 트랙 shift-left(개별 리뷰, 트랙 C high)로 대체 유지. GUI abort 시나리오 미구현도 지속 숙제.', st_meta),
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
