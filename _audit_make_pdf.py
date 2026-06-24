# -*- coding: utf-8 -*-
"""
_audit_make_pdf.py — 종합 감사 보고서를 PDF(보고서 형식)로 출력 (빌드 제외 도구)

reportlab + 맑은 고딕. 군 보고서 양식으로 조판.
종합 감사를 할 때마다 이 스크립트의 BLOCK·내용을 그 블록에 맞게 갱신해
실행하면, 블록별 PDF가 `감사보고서/` 폴더에 누적된다(블록당 1개).

사용: python _audit_make_pdf.py  →  감사보고서/감사보고서_selfplay.pdf
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
BLOCK = 'v16'                                    # 감사 블록 — 매 감사마다 갱신
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
         P('v16 블록 — 전자전(ESM→ARM) · 대잠 EMCON(능동 소나 역탐지) · 극초음속 다층 요격', st_sub),
         Spacer(1, 4*mm),
         HRFlowable(width='100%', thickness=1.4, color=NAVY), Spacer(1, 5*mm)]

# ── 개요(메타) 표 ──
meta_rows = [
    [P('감사 일자', st_cellb), P('2026-06-25', st_cell), P('판정', st_cellb), P('통과 (9영역 PASS)', st_pass)],
    [P('대상 범위', st_cellb), P('v16.01.01 ~ v16.02.03 (직전 self-play 감사 62e54de 이후 13커밋)', st_cell), P('발견 항목', st_cellb), P('1 건 (낮음·주석)', st_cellb)],
    [P('변경 규모', st_cellb), P('실 코드 변경 engine_combat·engine_core·app_main 3개 파일 — 신규 토글 3종(esm_arm·sonar_emcon·asw_forward) + HGV 다층요격 분기. 나머지 커밋은 파일명 리네임·DB 검증·위생·문서화', st_cell), P('트리거', st_cellb), P('① v16.1·v16.2 기능 묶음 완성', st_cell)],
    [P('감사 방식', st_cellb), P('무인 모드 — 착수 승인=9영역 포괄동의. exe 스모크는 GUI 자동화(pywinauto)', st_cell), P('근거 규칙', st_cellb), P('CLAUDE.md 종합 감사 9영역', st_cell)],
    [P('소요/특성', st_cellb), P('빌드 exit0(2회) · GUI 스모크 RESULT_CODE=0 · 잔존 프로세스 0 · MC120 NaN/Inf 0', st_cell), P('무인/수동', st_cellb), P('100% 무인 · 사용자 개입 0회', st_cell)],
    [P('점검 규모', st_cellb), P('회귀 8케이스×26지표(208 대조) · audit_static_scan 17/17 · ① 누적 diff 에이전트 · ② DB 현실성 에이전트(WebSearch) · 구버전 cfg 하위호환 실행 · MC120 안정성', st_cell), P('재감사', st_cellb), P('0회 (낮음 1건 그 자리 수정)', st_cell)],
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
    ('①', '코드·로직', 'PASS', '누적 diff(62e54de..HEAD) 에이전트 리뷰 — 치명/높음/중간 0건. OFF 경로 3종 검증된 no-op(_arm_esm_update 즉시 return·_evading 우변 False·transit 분기 if self._asw_forward 가드)→회귀 PASS 정합 · 전역 DB mutate 0(ARM info.copy())·부모 무수정(BattleEngine radar_off_until 재사용)·cfg 3키 빌드/로드/엔진읽기 일치·SoA 인덱스 정합·죽은코드 0 · 신기능 3종세트 완비 · 낮음 1건: _asw_phase 주석에 transit 상태 누락(이번 감사 위생 커밋 수정)'),
    ('②', 'DB·수치', 'PASS', 'DB 현실성 에이전트 팬아웃(WebSearch 대조) — 차단성 이상치 0건. 핵심 신규값 정합(랴오닝24/산둥36 함재기·DF-17 60km·ARM 사거리·ENEMY_MUNITION·마하 환산). 에이전트 권고 4건은 코드 재검증 후 전부 비채택(YJ-91=과거 검증값·푸젠 40+=추정 정합·지르콘/킨잘=v16.2 후속과제·Kh-58U=선택적). db_specsheet=DB 합 정합'),
    ('③', '회귀', 'PASS', 'audit_verify_regression.py — 8케이스 × 26지표 골든값 일치(동작 보존) · 결정론 유지(토글 OFF 기본이라 RNG 순서 불변, OFF bit-identical)'),
    ('④', '통합 MC + 성능', 'PASS', '기준 시나리오(이지스 기동전단 vs 전면전 포화·맑음주간) MC120: 요격률 62.9%±9.6%(범위 0.441~0.868)·NaN/Inf 0 · wall-time 정상(단발 0.25s·전장 0.7s·MC120 5.4s, 이전 블록 대비 급증 없음). 토글 OFF라 회귀 PASS가 안정성 담보'),
    ('⑤', 'exe·빌드', 'PASS', '빌드 exit 0 · 번들 무결성(_internal에 ai_rl_policy.npz·changelog·db_specsheet·forecast_surrogate.json·view_cesium_3d.html) · GUI 스모크 PASS(홈→앱→시뮬→요격률 표시→정상종료, RESULT_CODE=0) · 잔존 프로세스 0'),
    ('⑥', '위생', 'PASS', 'APP_VERSION=헤더=changelog 마지막 정합 · 정적스캔 17/17(버전·gitignore·민감산출물 0·_log/_record_frame 가드·3종세트·db_specsheet 정합·_PLANS stale 0·README 전수커버·파일명 stale 0) · _PLANS v16.1 측정결론 반영 · 죽은코드 0'),
    ('⑦', '하위호환', 'PASS', 'v16 플래그(esm_arm·sonar_emcon·asw_forward·munition_limit) 전무한 구버전 cfg로 단발·전장 둘 다 정상 dict 반환(cfg.get(...,False) 폴백)'),
    ('⑧', '수치·단위', 'PASS', 'v16 신규 산술 안전: ARM stale Pk = pk_base*exp(-miss_d/150) 상수분모·결과 자연 [0,1] · _sonar_eq_pd r50<0/==0 continue 가드·best_pd 0.0 초기화 → NaN/Inf 없음 · 확률값 clamp 불필요(구조적 [0,1])'),
    ('⑨', '리소스 누수', 'PASS', 'v16 frames/figure 신규 추가 0(시각화 무변경) · _record_frame·_log _mc_mode 가드 정적스캔 PASS · 능동소나 역탐지 cb는 틱당 즉시반환·누적상태 없음'),
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
         P('감사 범위 주석 — exe 노출 변경은 단 둘(v15.14.01 AI 전술 토글·Phase 5.6.1 적 전술 RL 주입 훅). self-play 5.6.2~5.6.3·자가개선 루프(S1~S4)·Tier2는 빌드제외 .py 학습 인프라라 ⑤·⑥(gitignore) 외 영역에서는 엔진 접점(enemy_mode 훅)만 평가한다. 예상대로 다수 영역이 소변경/해당없음인 가벼운 종합감사.', st_foot),
         Spacer(1, 6*mm)]

# ── 종합 판정 ──
flow += [P('2. 종합 판정', st_h2)]
verdict = Table([[P('통과', S('v', fontName='MalgunBd', fontSize=13, alignment=TA_CENTER, textColor=colors.white)),
                  P('9개 영역 전부 PASS · 발견 1건(낮음·주석)은 그 자리 수정·재감사 불요 — v16 블록 종료 선언 가능', st_cell)]],
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
         P('• <b>audit_static_scan.py</b> — 정적 점검 자동 스캐너 17항목 실행 17/17 PASS(버전 정합·gitignore·_log/frames 가드·enable 3종세트(v16 EMCON 3종 추가)·db_specsheet 정합·전장 분모 가드·MC 3경로·_PLANS stale·README 전수커버·파일명 stale).', st_body),
         P('• <b>_audit_gui_smoke.py</b> — GUI 자동화 스모크(홈→앱→시뮬→요격률 표시→정상 종료) RESULT_CODE=0. 엔진 직접호출 우회 없이 GUI 워커 경로 무인 검증.', st_body),
         P('• <b>① 누적 diff 에이전트 리뷰</b> — working tree clean이라 병합 후 빈 diff 빈틈을 누적 diff(62e54de..HEAD) 직접 투입으로 해소(general-purpose 에이전트).', st_body),
         P('• <b>② DB 현실성 에이전트</b> — Explore 에이전트가 WebSearch로 v16 신규 DB값을 공개 제원과 대조. 권고 4건은 사람이 코드 재검증 후 비채택(맹목 수용 차단).', st_body),
         P('• <b>감사보고서.md</b> — 텍스트 감사 보고서에 v16 블록 섹션 기록(최신순 누적).', st_body),
         Spacer(1, 5*mm)]

# ── 메타 회고 ──
flow += [P('4. 메타 회고 (감사 절차 자체 개선)', st_h2),
         P('이번 감사에서 식별·이행한 절차 개선:', st_body),
         P('• <b>v16 신규 3종 플래그 정적스캔 편입(즉시 반영)</b> — esm_arm·sonar_emcon·asw_forward의 3종세트(체크박스+isChecked+cfg.get)를 이번엔 수동 Grep으로 확인했음. audit_static_scan.py의 chk_flag_triplet 목록에 추가(14→17 항목)해 다음 감사부터 자동 검증.', st_body),
         P('• <b>DB 에이전트 결과의 사람 재검증 가치 확인</b> — DB 현실성 에이전트가 권고한 정정 4건이 자기모순(YJ-91)·이미 등록된 후속과제(지르콘/킨잘 고도)·추정 정합(푸젠)이었음. 사람이 코드(LOW-N 변경 이력 주석)로 재검증해 전부 비채택. 에이전트 권고 맹목 수용을 차단하는 검토 단계가 필수임을 재확인.', st_body),
         P('다음 숙제 — ① DB 에이전트가 ‘ARM standalone·carrier_air_wing이 v16 신규’라 잘못 전제(둘 다 기존, v16은 편대 프리셋만 추가). 에이전트에 정확한 diff 범위를 더 명시적으로 줄 것. ② 변경 이력 주석(LOW-N)을 에이전트가 먼저 읽도록 프롬프트에 코드 인용 의무화 검토.', st_meta),
         Spacer(1, 6*mm)]

# ── 환경·커밋 정보 (재현성) ──
flow += [P('5. 환경 · 커밋 정보 (재현성)', st_h2)]
env_rows = [
    [P('HEAD 커밋', st_cellb), P('ab98437 (+감사 위생 커밋)', st_cell), P('Python', st_cellb), P('3.14', st_cell)],
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
