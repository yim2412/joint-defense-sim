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
BLOCK = 'v18'                                    # 감사 블록 — 매 감사마다 갱신
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
         P('v18 캠페인 블록 — 작전급 해군 캠페인 엔진', st_sub),
         Spacer(1, 4*mm),
         HRFlowable(width='100%', thickness=1.4, color=NAVY), Spacer(1, 5*mm)]

# ── 개요(메타) 표 ──
meta_rows = [
    [P('감사 일자', st_cellb), P('2026-07-07', st_cell), P('판정', st_cellb), P('통과 (9영역 PASS/해당없음)', st_pass)],
    [P('대상 범위', st_cellb), P('v17.01.01 ~ v17.01.08 (직전 v16 종합감사 c3032b1 이후). 작전급 캠페인 엔진 v18.1~v18.7 — 코어 루프·전력 관리·임무 배정·전장의 안개·SLOC 연속 통제도·캠페인 MC·분석 리포트', st_cell), P('발견 항목', st_cellb), P('2 건 (즉시 수정)', st_pass)],
    [P('변경 규모', st_cellb), P('engine_campaign.py 신설(559줄, 전술 엔진 무수정 호출) · app_main.py(+332: SimWorker 캠페인 분기·MC 라우팅·캠페인 분석 서브탭) · app_main.spec(engine_campaign datas) · ai_policy_infer.py(_MEIPASS 절대경로) · _audit_campaign_smoke.py 신설', st_cell), P('트리거', st_cellb), P('① v16→v17 major 전환', st_cell)],
    [P('감사 방식', st_cellb), P('무인 모드 — 착수 승인=9영역 포괄동의. 각 마이너 shift-left(v18.5·18.6·18.7 개별 code-review 정확성 0건) 후 종합은 engine_campaign 전체 통합 리뷰(에이전트)·상호작용·하위호환 중심', st_cell), P('근거 규칙', st_cellb), P('CLAUDE.md 종합 감사 9영역', st_cell)],
    [P('소요/특성', st_cellb), P('빌드 성공 · GUI 스모크 RESULT_CODE=0(단발 + 캠페인 MC + 안개) · abort 전파 OK · 캠페인 MC 1000회 약 42초 · NaN/Inf 0 · outcome 합=1.0', st_cell), P('무인/수동', st_cellb), P('100% 무인 · 사용자 개입 0회', st_cell)],
    [P('점검 규모', st_cellb), P('회귀 8케이스×26지표 bit-identical(전술 엔진 무수정) · audit_static_scan 28/28(캠페인 3종세트 2종 추가) · 엔진 정밀리뷰 8집중영역 · 구버전 cfg 하위호환', st_cell), P('재감사', st_cellb), P('발견 2건 → v17.01.09 수정·재PASS', st_cell)],
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
    ('①', '코드·로직', '발견1', 'engine_campaign 전체 정밀리뷰(에이전트) 8집중영역 버그 0 — 나눗셈/NaN·경계/off-by-one·빈컬렉션·상태머신·전역DB mutate·cfg오염·rng결정론·카운터. 3종세트(enable_campaign_mode·enable_campaign_fog) 무결·전역 DB mutate 0(.get 읽기전용)·부모(engine_combat) 무수정=회귀 bit-identical. <b>발견: horizon_h≤0 축퇴 입력→빈 루프로 교전 0인데 outcome "win" 오판</b> → v17.01.09 max(1,...) 클램프'),
    ('②', 'DB·수치', '해당없음', '신규 무기 제원 없음(기존 SHIP_DB·FLEET_PRESETS·ENEMY_FLEET_PRESETS 재사용). 새 수치는 추상 계수(수리 1~14일·교전당 탄약 0.28·연료 0.01/틱·통제 관성 α=0.3)로 교리적 값 — 공개제원 대조 대상 아님. db_specsheet 항목수=DB합 정적 PASS'),
    ('③', '회귀', 'PASS', 'audit_verify_regression.py — 8케이스 × 26지표 bit-identical. engine_campaign이 전술 엔진을 무수정 호출(호출만)해 단발·전장 골든 무영향. horizon 클램프 수정 후 재PASS'),
    ('④', '통합 MC + 성능', 'PASS', '캠페인 MC 1000회 약 42초(단발 0.043초, 단일 프로세스 순차로 충분) · NaN/Inf 0 · outcome 합=1.0 · 평균 통제도 [0,1] clamp·min≤max. 웨이브 편향 진단: outcome이 편성 강도와 정합 분리(CVN 승90% ~ 소형함 무승부 지배), 72→168h 완만한 낙관 편향은 초장기 336h에 연료·손실 누적으로 반전=단조 낙관 아님'),
    ('⑤', 'exe·빌드', 'PASS', '빌드 성공 · 번들(engine_campaign datas·_MEIPASS 경유 forecast_model 로드) · 단발 GUI 스모크 RESULT_CODE=0 · 캠페인 스모크(MC+안개) RESULT_CODE=0(예측모델 적용·안개 배너 확인) · abort 전파 OK(progress_cb 예외→SimWorker except _SimCancelled). 재빌드 후 재PASS'),
    ('⑥', '위생', '발견1', '캠페인 3종세트 무결·죽은코드 0(monte_carlo_campaign·_render_campaign_report·run_campaign 호출처 존재)·보안(키 없음)·정적 28/28·_PLANS v18 완료분 정리(v19 진입 청산). <b>발견: CLAUDE.md 파일구조 표에 engine_campaign.py 누락</b> → v17.01.09 추가. 로드맵_상세 문서 major 라벨(v17해군=현v18) 매핑 주석 추가'),
    ('⑦', '하위호환', 'PASS', '캠페인 키(enable_campaign_fog·campaign_horizon_h·campaign_isr_aircraft) 없는 구버전 cfg·빈 cfg로 run_campaign 정상 실행 · 구버전 cfg로 run_v7_simulation(요격률 1.0)·run_battle_simulation(outcome win) 정상 · self.cfg=dict(cfg) 오염 차단'),
    ('⑧', '수치·단위', 'PASS', '전력비 target(friendly+enemy≤0 가드)·mean_control(len=3 상수 분모)·best_control(default 지정)·MC inv=1/n(n≥1) 0나눗셈 가드 · 확률/통제도 [0,1] clamp · 비용 /1e6 단위 일관 · horizon 클램프(①과 교차)'),
    ('⑨', '리소스 누수', 'PASS', '캠페인 frames 미사용(리스트 지표만) · MC가 각 run 결과 dict 미축적(반복마다 GC, ctrl_list는 float만) · figure는 ChartPageWidget 관리(stop_worker 정리 추가) · 엔진 _log/print 없음 · forecast_model 1회 로드 공유(3.1MB pkl 반복 로드 방지)'),
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
         P('감사 범위 주석 — v18 캠페인 블록(v17.01.01~09). 별도 engine_campaign.py 신설로 며칠 단위 전역을 1시간 틱으로 진행하고 교전은 즉시예측(forecast_model)으로 해결. 전술 엔진(engine_combat)은 무수정 호출 → 단발·전장 회귀 bit-identical. 신규 토글 2종(enable_campaign_mode·enable_campaign_fog, 기본 OFF·실험적). 각 마이너가 shift-left(개별 code-review)를 거쳐 종합 감사는 통합 상태·상호작용·하위호환 점검에 집중. v18 해군 캠페인 완성 — v19 공군 작전급 진입 준비 완료.', st_foot),
         Spacer(1, 6*mm)]

# ── 종합 판정 ──
flow += [P('2. 종합 판정', st_h2)]
verdict = Table([[P('통과', S('v', fontName='MalgunBd', fontSize=13, alignment=TA_CENTER, textColor=colors.white)),
                  P('9개 영역 전부 PASS/해당없음 · 발견 2건(경미) 즉시 수정 · 판단필요 0건 — 작전급 캠페인 엔진(engine_campaign 신설)이 전술 엔진을 무수정 호출해 회귀 bit-identical을 보존하고, 엔진 정밀리뷰 8집중영역에서 버그 0건. 발견은 horizon_h≤0 축퇴 클램프·CLAUDE.md 파일표 누락 2건뿐으로 v17.01.09에서 즉시 수정·재감사 통과. 캠페인 계열은 MVP 근사(웨이브 유한·손실 미추정)라 실험적 유지가 정직. v18 해군 캠페인 완성, v19 공군 작전급 진입 준비 완료', st_cell)]],
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
         P('• <b>audit_verify_regression.py</b> — 8케이스×26지표 골든 bit-identical. engine_campaign이 전술 엔진을 호출만(무수정)해 단발·전장 골든 무영향. horizon 클램프 수정 후 재PASS.', st_body),
         P('• <b>audit_static_scan.py</b> — 정적 점검 28/28 PASS. 메타회고로 캠페인 3종세트(enable_campaign_mode·enable_campaign_fog) 자동검사를 소비처 명시 방식으로 추가(26→28항목).', st_body),
         P('• <b>GUI 스모크(단발 + 캠페인)</b> — 단발 _audit_gui_smoke.py RESULT_CODE=0 · 캠페인 _audit_campaign_smoke.py RESULT_CODE=0(캠페인 모드+안개 토글→시뮬→예측모델 적용·안개 배너 확인). abort 전파 헤드리스 확인. 엔진 직접호출 우회 없음.', st_body),
         P('• <b>엔진 정밀리뷰(general-purpose 에이전트)</b> — engine_campaign.py 559줄 8집중영역(나눗셈·경계·빈컬렉션·상태머신·전역DB·cfg·rng·카운터) 정밀 추적. 명백한 정확성 버그 0건, horizon 축퇴만 소견.', st_body),
         P('• <b>통합 MC · 하위호환</b> — 캠페인 MC 1000회 약 42초 NaN 0·outcome 합=1.0. 구버전 cfg(캠페인 키 없음)·빈 cfg run_campaign 정상. 웨이브 편향 정량 진단(편성 강도 정합·초장기 반전).', st_body),
         P('• <b>감사보고서.md</b> — 텍스트 감사 보고서에 v18 캠페인 블록 섹션 기록(최신순 누적).', st_body),
         Spacer(1, 5*mm)]

# ── 메타 회고 ──
flow += [P('4. 메타 회고 (감사 절차 자체 개선)', st_h2),
         P('이번 감사에서 식별·이행한 절차 개선:', st_body),
         P('• <b>캠페인 3종세트 자동검사 추가(즉시 반영)</b> — chk_flag_triplet의 engread가 engine_combat만 봐서 소비처가 engine_campaign(fog)·app_main 라우팅(mode)인 캠페인 플래그를 오탐→①에서 수동 확인해야 했다. 소비처를 명시한 캠페인 계열 별도 검사를 추가(정적 26→28). 다음 새 실행 모드/엔진 파일 토글도 소비처 명시로 등록.', st_body),
         P('• <b>병합 후 code-review 빈 diff 대체법 확립</b> — 연속 커밋이라 git diff가 빈 diff → 신설 엔진 파일(engine_campaign.py)을 general-purpose 에이전트에 통째로 주고 8집중영역 정밀 리뷰시켜 code-review high를 대체(버그 0 확인). 마이너마다 shift-left(직접 리뷰)를 이미 했으면 종합은 이 통합 리뷰로 충분.', st_body),
         P('다음 숙제(지속) — GUI abort(중단 클릭) 실제 자동화 미해소(전파는 헤드리스로 확인). 프리셋명 오타 조용한 폴백(_build_force가 잘못된 fleet_preset을 단독 작전으로 폴백 → 진단 테스트 오염 발견) → repr 대조 습관 유지.', st_meta),
         Spacer(1, 6*mm)]

# ── 환경·커밋 정보 (재현성) ──
flow += [P('5. 환경 · 커밋 정보 (재현성)', st_h2)]
env_rows = [
    [P('HEAD 커밋', st_cellb), P('fe085ab (v17.01.09 감사 수정)', st_cell), P('Python', st_cellb), P('3.14', st_cell)],
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
flow += [P('차기 종합 감사 — v19 공군 작전급 아키텍처 전환 완료 시 또는 다음 major 전환 직전(트리거 ①/②). PDF는 감사보고서/감사보고서_{블록}.pdf로 누적.', st_meta),
         Spacer(1, 6*mm),
         HRFlowable(width='100%', thickness=0.6, color=GREY), Spacer(1, 2*mm),
         P('합동 통합방어 시뮬레이터 · 종합 감사 보고서 · 자동 생성(_audit_make_pdf.py) · 2026-07-07', st_foot)]

doc.build(flow)
print('생성 완료:', OUT)
