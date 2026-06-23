# -*- coding: utf-8 -*-
"""
_make_audit_pdf.py — 종합 감사 보고서를 PDF(보고서 형식)로 출력 (빌드 제외 도구)

reportlab + 맑은 고딕. 군 보고서 양식으로 조판.
종합 감사를 할 때마다 이 스크립트의 BLOCK·내용을 그 블록에 맞게 갱신해
실행하면, 블록별 PDF가 `감사보고서/` 폴더에 누적된다(블록당 1개).

사용: python _make_audit_pdf.py  →  감사보고서/감사보고서_v15.pdf
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
BLOCK = 'v15'                                    # 감사 블록 — 매 감사마다 갱신
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
st_meta   = S('meta', fontSize=9, leading=13, textColor=colors.black)
st_foot   = S('foot', fontSize=7.5, leading=10, textColor=GREY, alignment=TA_CENTER)

def P(t, s=st_body): return Paragraph(t, s)

doc = SimpleDocTemplate(OUT, pagesize=A4,
                        leftMargin=18*mm, rightMargin=18*mm,
                        topMargin=18*mm, bottomMargin=16*mm,
                        title='종합 감사 보고서 — v15 블록', author='합동 통합방어 시뮬레이터')
flow = []

# ── 표제 ──
flow += [P('종 합 감 사 보 고 서', st_title),
         Spacer(1, 3*mm),
         P('v15 블록 — 지속 전장 엔진 · 강화학습(RL) · 다운스트림 컷오버', st_sub),
         Spacer(1, 4*mm),
         HRFlowable(width='100%', thickness=1.4, color=NAVY), Spacer(1, 5*mm)]

# ── 개요(메타) 표 ──
meta_rows = [
    [P('감사 일자', st_cellb), P('2026-06-23', st_cell), P('판정', st_cellb), P('통과 (9영역 PASS)', st_pass)],
    [P('대상 범위', st_cellb), P('v15.06.01 ~ v15.13.05 (60커밋)', st_cell), P('발견 항목', st_cellb), P('0 건', st_cellb)],
    [P('변경 규모', st_cellb), P('engine_v7 +1004줄 · launcher 대규모 리팩터 · rl_env.py 신설 · engine +129줄', st_cell), P('트리거', st_cellb), P('① 큰 묶음 완료', st_cell)],
    [P('감사 방식', st_cellb), P('무인 모드 — 단계별 동의 없이 자동 수행. exe 스모크는 GUI 자동화(pywinauto)', st_cell), P('근거 규칙', st_cellb), P('CLAUDE.md 종합 감사 9영역', st_cell)],
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
    ('①', '코드·로직', 'cfg=dict(cfg) 진입부 복사 · 전역 DB mutate 0 · BattleEngine 25메서드 부모 시그니처 보존 · NoScrollComboBox 준수 · 동작없는 체크박스 0 · 신기능 8항목(3종세트·MC 3경로·_id_counter·spec_db 동기·_log/frames 가드) 충족'),
    ('②', 'DB·수치', 'spec_db 107 = 엔티티 DB 합(ENEMY65+FRIENDLY14+SHIP21+AIRCRAFT7) 정확 일치 · SHIP_ENDURANCE/PROCUREMENT 21=SHIP_DB21 · 공개제원 일치(J-16 6·055형 24·야센 32·랴오닝 $3B) · surrogate 345=15×23 누락 0'),
    ('③', '회귀', 'verify_regression.py — 8케이스 × 26지표 골든값 일치(동작 보존) · 결정론 유지'),
    ('④', '통합 MC + 성능', '단발 MC 요격률 0.749±0.078 · 전장 MC 승률 0.375·임무점수 0.552(baseline 53.2% 정합) · wall-time 단발 0.33s/전장 0.68s(이상 급증 없음) · NaN/Inf 0'),
    ('⑤', 'exe·빌드', '전체 빌드 exit 0(exe 52MB) · 번들 무결성(_internal에 battle_surrogate·changelog·spec_db·engine·cesium) · GUI 자동화 스모크 PASS(홈→앱→시뮬→요격률 표시→정상종료) · 종료 후 잔존 프로세스 0'),
    ('⑥', '위생', 'APP_VERSION=헤더=changelog 마지막 v15.13.05 정합 · gitignore 커버 완전 · 민감 산출물 추적 0 · audit_scan.py 신설(11/11 PASS)'),
    ('⑦', '하위호환', 'v15 신규 플래그 전부 누락한 구버전 cfg로 단발·전장 모두 무크래시·기본값 적용'),
    ('⑧', '수치·단위', '전장 분모 전부 가드(_fr/_en_value_init·_ammo_init=max(1.0,..)·fw/ew=or 1.0·_init_dist>0) · 승리당비용 win_rate=0 가드 · MC NaN/Inf 0'),
    ('⑨', '리소스 누수', '_log() 내부 _mc_mode 가드 · _record_frame 호출 if not _mc_mode 가드 · matplotlib figure close/clear 패턴 정상'),
]
data = [hdr]
for num, area, detail in rows:
    data.append([P(num, st_cellb), P(area, st_cell), P('PASS', st_pass), P(detail, st_cell)])
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
flow += [t, Spacer(1, 6*mm)]

# ── 종합 판정 ──
flow += [P('2. 종합 판정', st_h2)]
verdict = Table([[P('통과', S('v', fontName='MalgunBd', fontSize=13, alignment=TA_CENTER, textColor=colors.white)),
                  P('9개 영역 전부 PASS · 발견 항목 0건 · 수정할 버그 없음 — v15 블록 종료 선언 가능', st_cell)]],
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
flow += [P('3. 산출물', st_h2),
         P('• <b>audit_scan.py</b> — 종합 감사 정적 점검 자동 스캐너 11항목(버전 정합·gitignore·_log/frames 가드·enable 3종세트·spec_db 정합·전장 분모 가드·MC 3경로). 실행 결과 11/11 PASS. verify_regression.py의 짝.', st_body),
         P('• <b>_audit_smoke.py</b> — pywinauto 기반 GUI 자동화 스모크. 홈→앱 진입→시뮬레이션 실행→요격률 결과 표시→정상 종료를 무인 검증.', st_body),
         P('• <b>감사보고서.md</b> — 텍스트 감사 보고서에 v15 블록 섹션 기록(최신순 누적).', st_body),
         Spacer(1, 5*mm)]

# ── 메타 회고 ──
flow += [P('4. 메타 회고 (감사 절차 자체 개선)', st_h2),
         P('이번 감사에서 식별한 절차 약점 3건과 개선 귀속:', st_body),
         P('• <b>병합 후 /code-review 빈 diff</b> — 블록이 이미 main에 병합돼 리뷰 대상 diff 부재. 표적 수동 Grep + 회귀로 대체(에이전트 의미추적 미수행). → 다음엔 누적 diff(첫커밋^..HEAD) 직접 투입 또는 마이너마다 병합 전 리뷰(shift-left).', st_body),
         P('• <b>abort 클릭 미검증</b> — Job Object 구조 + 종료 후 잔존 0으로 대체. → _audit_smoke.py에 MC 중단 시나리오 추가 예정.', st_body),
         P('• <b>키 구조 오가정</b> — surrogate JSON 중첩(table)·DB NATO 코드명 키를 수동 추측해 헛돔. → audit_scan.py 자동 정합 점검으로 최소화 완료.', st_body),
         P('루프 제도화: CLAUDE.md 「종합 감사 6) 메타 회고」 + 메모리 feedback-audit-self-improve.', st_meta),
         Spacer(1, 6*mm),
         HRFlowable(width='100%', thickness=0.6, color=GREY), Spacer(1, 2*mm),
         P('합동 통합방어 시뮬레이터 · 종합 감사 보고서 · 자동 생성(_make_audit_pdf.py) · 2026-06-23', st_foot)]

doc.build(flow)
print('생성 완료:', OUT)
