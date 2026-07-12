# -*- coding: utf-8 -*-
"""
_audit_make_pdf.py — 종합 감사 보고서를 PDF(보고서 형식)로 출력 (빌드 제외 도구)

reportlab + 맑은 고딕. 군 보고서 양식으로 조판.
종합 감사를 할 때마다 이 스크립트의 BLOCK·내용을 그 블록에 맞게 갱신해
실행하면, 블록별 PDF가 `감사보고서/` 폴더에 누적된다(블록당 1개).

사용: python _audit_make_pdf.py  →  감사보고서/감사보고서_v18.pdf
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
BLOCK = 'v18.02'                                 # 감사 블록 — 매 감사마다 갱신
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
                        title='종합 감사 보고서 — v18 캠페인 블록', author='합동 통합방어 시뮬레이터')
flow = []

# ── 표제 ──
flow += [P('종 합 감 사 보 고 서', st_title),
         Spacer(1, 3*mm),
         P('v18.02 블록 — 캠페인 정밀 교전·병렬 MC·시나리오 저장 (v20 착수 직전)', st_sub),
         Spacer(1, 4*mm),
         HRFlowable(width='100%', thickness=1.4, color=NAVY), Spacer(1, 5*mm)]

# ── 개요(메타) 표 ──
meta_rows = [
    [P('감사 일자', st_cellb), P('2026-07-12', st_cell), P('판정', st_cellb), P('통과 (9영역 PASS/해당없음)', st_pass)],
    [P('대상 범위', st_cellb), P('v18.01.08 ~ v18.02.03 (직전 v19 종합감사 6569fc6 이후 23커밋). 깊은 로직감사 8건(v18.01.08~15)·CAP 공대공 정상화(18)·IFF 정규승격(19)·크래시 수정(16) + A1 캠페인 정밀 교전(v18.02.01, 교전 해결 아키텍처 변경)·E1 병렬 MC(02)·시나리오 저장/불러오기(03)', st_cell), P('발견 항목', st_cellb), P('0 건', st_pass)],
    [P('변경 규모', st_cellb), P('engine_campaign.py(_resolve_precise 정밀 교전·monte_carlo_campaign 병렬화) · engine_combat.py(calculate_fleet_detect_ranges fleet_list 파라미터) · app_main.py(precise 3종세트·시나리오 저장/불러오기 UI) · _audit_scenario_smoke.py 신설 · 누적 diff 36파일 +2151/-873', st_cell), P('트리거', st_cellb), P('① v20 major 착수 직전', st_cell)],
    [P('감사 방식', st_cellb), P('무인 모드 — 착수 승인=9영역 포괄동의. 각 마이너 shift-left(A1·E1·시나리오 개별 code-review 정확성 0건) 후 종합은 통합 상태·상호작용·하위호환 중심. 앞 세션 검증 실패(테스트 스크립트 결함)를 정확한 감사로 재실증', st_cell), P('근거 규칙', st_cellb), P('CLAUDE.md 종합 감사 9영역', st_cell)],
    [P('소요/특성', st_cellb), P('빌드: 소스 무변경으로 지난 v18.02.03 빌드(EXIT0) 현행 유효 · GUI 스모크 3종 RESULT_CODE=0(단발·캠페인 6배너·시나리오 82키 왕복) · 정밀 ON 병렬 MC NaN/Inf 0 · outcome 합=1.0 · 성능 campaign 57ms', st_cell), P('무인/수동', st_cellb), P('100% 무인 · 사용자 개입 0회', st_cell)],
    [P('점검 규모', st_cellb), P('회귀 12케이스×26지표 bit-identical(A1/E1 OFF 하위호환) · audit_static_scan 41/41 · 불변식 45케이스 · 죽은토글 7개 · 구버전 cfg 하위호환 · _audit_compat.py(⑦+④)', st_cell), P('재감사', st_cellb), P('발견 0건 — 재감사 불요', st_cell)],
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
    ('①', '코드·로직', 'PASS', 'A1 정밀 교전 라우팅 플래그 5종(campaign·battle·air·fog·precise) tcfg.pop 완전(라우터 오염 방지)·cfg deep copy 미오염·detect 폴백 수정(fleet_list 파라미터)·hp/max_hp 0나눗셈 가드·won 무인함 경계(n_manned)·E1 워커 축소dict 반환·seed 독립집계. <b>신기능 8항목</b>: precise 3종세트 완비(체크박스·cfg빌드 isChecked·cfg로드 hasattr)·신규 stats키(n_precise→_compile→MC집계→n_precise_avg·parallel) 소비처 완비·import 정상'),
    ('②', 'DB·수치', '해당없음', 'A1·E1·시나리오 모두 DB(ENEMY_DB·SHIP_DB·FRIENDLY_DB) mutate 0 — engine_campaign은 DB를 import만(읽기전용 .get). 신규 무기 제원·수치 변경 없음. db_specsheet 동기화 대상 아님'),
    ('③', '회귀', 'PASS', 'audit_verify_regression.py — 12케이스 × 26지표 bit-identical. A1/E1은 기본 OFF로 대리모델 경로 완전 보존(정밀 미발동)·시나리오는 순수 UI라 엔진 무영향 → 골든 무변화'),
    ('④', '통합 MC + 성능', 'PASS', '구버전 cfg MC n=20 승/무/패 합=1.0(순차, proxy 임계 64 미만) · 정밀 ON MC n=16 win=1.0 surviving=5.69 n_precise_avg=3.0 parallel=True NaN/Inf 0 · 순차=병렬 집계 bit-identical(seed 독립) · 성능 battle 86ms·campaign 57ms(기준 대비 1.5배 이내, 오히려 개선)'),
    ('⑤', 'exe·빌드', 'PASS', '빌드: 소스 .py 무변경(6dec261 이후 0), 지난 v18.02.03 빌드 EXIT0·exe가 전 소스보다 최신=현행 유효(동일 소스 재빌드 신호 없음, 생략 정당). GUI 스모크 3종 RESULT_CODE=0 — 단발(요격률 표시)·캠페인(안개·제공권·SEAD·기지·정밀교전 6배너)·시나리오(cfg 82키 저장→불러오기 왕복). 크래시 0'),
    ('⑥', '위생', 'PASS', '정적 41/41(chk_plans_stale·readme·file명 자동클린)·죽은토글 7개 효과확인·changelog/​_PLANS 코드명 잔류 0. 1회용 <b>_audit_compat_tmp.py를 _audit_compat.py로 정식 편입</b>(⑦+④ 재사용 가치·__main__ 가드·정확한 프리셋 키)'),
    ('⑦', '하위호환', 'PASS', '구버전 cfg(precise/parallel 키 없음)로 캠페인 단발 n_precise=0(정밀 미발동·기존 결과 보존)·단발 교전 IR 1.0([0,1] 범위)·캠페인 MC n=20 정상. self.cfg=dict(cfg) 오염 차단 유지'),
    ('⑧', '수치·단위', 'PASS', '불변식 45케이스 위반 0(확률[0,1]·승무패 합=1·NaN/Inf 0·outcome 유효) · hp_frac·win_p·intercept_rate [0,1] clamp · hp/max_hp 0나눗셈 가드(truthy) · MC inv=1/n(n≥1) · cost raw USD 일관'),
    ('⑨', '리소스 누수', 'PASS', 'E1 <b>with ProcessPoolExecutor</b> 컨텍스트 자동 정리(워커 잔존 0)·워커 축소dict 반환(직렬화 경량, 대형 필드 제외)·_resolve_precise mc_mode=True(frames·_log 억제)·forecast_model 워커당 1회 로드(pkl 반복 직렬화 방지)'),
]
st_find = S('find', fontName='MalgunBd', fontSize=8, leading=11, alignment=TA_CENTER, textColor=colors.HexColor('#b25e00'))
data = [hdr]
for num, area, verdict, detail in rows:
    if verdict == 'PASS':
        vs, vt = st_pass, 'PASS'
    elif verdict == '해당없음':
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
         P('감사 범위 주석 — v18.02 블록(v18.01.08~v18.02.03, v20 major 착수 직전). 핵심은 A1 캠페인 정밀 교전(v18.02.01) — 캠페인 zone 교전을 학습 대리모델 근사 대신 실제 전술 단발(run_v7_simulation)로 해결해 함정별 실측 손상·요격탄 비용·요격률을 반영(하이브리드: 적 규모≥3만 정밀). E1(v18.02.02)은 캠페인 MC를 멀티프로세스 병렬화(seed 독립→순차와 집계 bit-identical). 시나리오 저장/불러오기(v18.02.03)는 순수 UI. 모두 기본 OFF·실험적 → OFF면 v18 bit-identical. 각 마이너가 shift-left(개별 code-review)를 거쳐 종합은 통합 상태·상호작용·하위호환에 집중. v20 지상군 작전급 진입 준비 완료.', st_foot),
         Spacer(1, 6*mm)]

# ── 종합 판정 ──
flow += [P('2. 종합 판정', st_h2)]
verdict = Table([[P('통과', S('v', fontName='MalgunBd', fontSize=13, alignment=TA_CENTER, textColor=colors.white)),
                  P('9개 영역 전부 PASS/해당없음 · 발견 0건 · 판단필요 0건 — A1 정밀 교전이 부모 전술 엔진(run_v7_simulation)을 무수정 호출하고 기본 OFF로 대리모델 경로를 완전 보존해 회귀 bit-identical. E1 병렬 MC는 seed 독립으로 순차와 집계가 완전 일치(정밀 ON n=16 실증). 앞 세션의 즉석 검증 실패(A1 n_precise=0·E1 BrokenProcessPool)는 테스트 스크립트 결함(오타 프리셋 이름·__main__ 가드 누락)이었고, 정확한 감사(_audit_compat.py)로 A1 발현·E1 병렬 실작동을 실증. A1/E1은 실험적 유지가 정직(정밀 MC는 병렬 필수·다운스트림 소비 미완). v20 지상군 작전급 진입 준비 완료', st_cell)]],
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
         P('• <b>audit_verify_regression.py</b> — 12케이스×26지표 골든 bit-identical. A1/E1 기본 OFF로 대리모델 경로 완전 보존·시나리오 순수 UI → 골든 무변화.', st_body),
         P('• <b>audit_static_scan.py</b> — 정적 점검 41/41 PASS(precise 3종세트 자동등록·chk_plans_stale·readme·file명). audit_property 불변식 45케이스·audit_effect 죽은토글 7개·audit_perf 성능 회귀가드.', st_body),
         P('• <b>GUI 스모크 3종(단발 + 캠페인 + 시나리오)</b> — _audit_gui_smoke.py(단발 요격률)·_audit_campaign_smoke.py(캠페인 6배너: 안개·제공권·SEAD·기지·정밀교전)·_audit_scenario_smoke.py(cfg 82키 저장→불러오기 왕복) 전부 RESULT_CODE=0. 엔진 직접호출 우회 없음(실제 exe 버튼 클릭).', st_body),
         P('• <b>_audit_compat.py(정식 편입)</b> — ⑦ 하위호환(구버전 cfg 캠페인 단발·단발 교전·MC) + ④ 통합 MC(정밀 ON 병렬 n=16 수치 안정성). 1회용 임시에서 정본 감사 스크립트로 승격(정확한 프리셋 키·__main__ 가드).', st_body),
         P('• <b>감사보고서.md</b> — 텍스트 감사 보고서에 v18.02 블록 섹션 기록(최신순 누적).', st_body),
         Spacer(1, 5*mm)]

# ── 메타 회고 ──
flow += [P('4. 메타 회고 (감사 절차 자체 개선)', st_h2),
         P('이번 감사에서 식별·이행한 절차 개선:', st_body),
         P('• <b>_audit_compat.py 정본화(즉시 반영)</b> — 앞 세션의 즉석 검증 스크립트가 ▸틀린 프리셋 이름(\'중국 항모전단\'=미존재→단독 작전 폴백→교전 0) ▸if __name__==\'__main__\' 가드 누락(Windows spawn 자식 재import→BrokenProcessPool)으로 헛되이 FAIL을 냈다. 정확한 프리셋 키·main()+가드를 갖춘 _audit_compat.py를 ⑦+④ 정본 감사로 승격 → 캠페인/MC 검증 재발 방지.', st_body),
         P('• <b>빌드 스킵 판단 근거 명시</b> — 소스 .py 무변경 + 지난 빌드 EXIT0 + exe가 전 소스보다 최신이면 동일 소스 재빌드는 신호가 없어 생략(6분 절약). 대신 현행 exe에 GUI 스모크 3종을 돌려 번들 무결성을 실증. 스킵 근거를 ⑤ 판정에 기록.', st_body),
         P('다음 숙제(지속) — exe에서 캠페인 MC 병렬 실행은 여전히 헤드리스로만 실증(전술 MC ProcessPoolExecutor 선례로 낮은 리스크). 필요 시 캠페인 MC 전용 GUI 스모크 신설. GUI abort(중단 클릭) 실제 자동화도 미해소.', st_meta),
         Spacer(1, 6*mm)]

# ── 환경·커밋 정보 (재현성) ──
flow += [P('5. 환경 · 커밋 정보 (재현성)', st_h2)]
env_rows = [
    [P('HEAD 커밋', st_cellb), P('6dec261 (v18.02.03 시나리오 저장)', st_cell), P('Python', st_cellb), P('3.14', st_cell)],
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
flow += [P('차기 종합 감사 — v20 지상군 작전급 아키텍처 전환 완료 시 또는 다음 major 전환 직전(트리거 ①/②). PDF는 감사보고서/감사보고서_{블록}.pdf로 누적.', st_meta),
         Spacer(1, 6*mm),
         HRFlowable(width='100%', thickness=0.6, color=GREY), Spacer(1, 2*mm),
         P('합동 통합방어 시뮬레이터 · 종합 감사 보고서 · 자동 생성(_audit_make_pdf.py) · 2026-07-12', st_foot)]

doc.build(flow)
print('생성 완료:', OUT)
