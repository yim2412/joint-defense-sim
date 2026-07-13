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
BLOCK = 'v20'                                    # 감사 블록 — 매 감사마다 갱신
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
st_find_hdr = S('findhdr', fontName='MalgunBd', fontSize=8.3, leading=11, alignment=TA_CENTER, textColor=colors.HexColor('#b25e00'))
st_foot   = S('foot', fontSize=7.5, leading=10, textColor=GREY, alignment=TA_CENTER)

def P(t, s=st_body): return Paragraph(t, s)

doc = SimpleDocTemplate(OUT, pagesize=A4,
                        leftMargin=18*mm, rightMargin=18*mm,
                        topMargin=18*mm, bottomMargin=16*mm,
                        title='종합 감사 보고서 — v20 지상군 블록', author='합동 통합방어 시뮬레이터')
flow = []

# ── 표제 ──
flow += [P('종 합 감 사 보 고 서', st_title),
         Spacer(1, 3*mm),
         P('v20 지상군 블록 — 연안 방공망·한국형 BMD 5계층·해상 상륙작전·도미노', st_sub),
         Spacer(1, 4*mm),
         HRFlowable(width='100%', thickness=1.4, color=NAVY), Spacer(1, 5*mm)]

# ── 개요(메타) 표 ──
meta_rows = [
    [P('감사 일자', st_cellb), P('2026-07-13', st_cell), P('판정', st_cellb), P('통과 (9영역 PASS/해당없음)', st_pass)],
    [P('대상 범위', st_cellb), P('v18.03.01 ~ v18.04.06, 커밋 63dd2cb..HEAD (v20 블록 전체). 한국형 BMD 4계층·탄도탄 종말 강하·지상 사격통제 분리(v20.2a) + 연안 방공망 캠페인 층(v20.2b) + 해상 상륙작전(v20.3) + 도미노 연쇄(v20.4) + 전력 DB 확충·편성 반영(v20.1)', st_cell), P('발견 항목', st_cellb), P('7 건 (전부 수정)<br/>+ 판단필요 5건', st_find_hdr)],
    [P('변경 규모', st_cellb), P('engine_army.py 신설(CoastalSAMSite·AmphibiousForce·ArmyCampaign) · engine_combat.py(L-SAM·천궁-II·패트리엇 요격층·탄도 강하·지상 사격통제 분리) · engine_campaign/airforce(도미노 접합) · engine_core(KDDX·054B·KC-330 DB) · app_main(지상 토글 3종세트·결과 블록)', st_cell), P('트리거', st_cellb), P('① major 전환 (v20 블록 완료)', st_cell)],
    [P('감사 방식', st_cellb), P('무인 모드 — 착수 승인=9영역 포괄동의. 발견 항목은 그 자리 수정·재감사. 밸런스·설계 판단이 갈리는 5건만 강행하지 않고 남김', st_cell), P('근거 규칙', st_cellb), P('CLAUDE.md 종합 감사 9영역', st_cell)],
    [P('소요/특성', st_cellb), P('빌드 EXIT=0 · GUI 스모크 3종 RESULT_CODE=0(단발·캠페인·시나리오, 연안 방공·상륙 배너 exe 렌더 확인) · 대규모 MC(OFF n=300 / ON n=200) 기준값 일치 · NaN/Inf 0 · 성능 회귀가드 1.5배 이내', st_cell), P('무인/수동', st_cellb), P('100% 무인 · 사용자 개입 0회', st_cell)],
    [P('점검 규모', st_cellb), P('회귀 <b>골든 24→28</b>케이스 × 29지표 · audit_static_scan 45/45 · 불변식 45케이스 · fuzz(단발·전장·<b>캠페인 신설</b>) · pairwise 10토글 45쌍 · engine_army 공개 메서드 22개 호출처 전수', st_cell), P('재감사', st_cellb), P('발견 7건 수정 후 재감사 PASS', st_pass)],
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
    ('①', '코드·로직', '발견 6', '<b>[높음] 무방비·재고소진 구역 지상 BMD 누출</b> — 세척(scrub_ground_bmd)이 inject_into 안에 있는데 inject_tactical이 포대 없는 구역(site=None)이면 세척 전에 return → 사용자의 단발 BMD 토글이 전술 cfg로 새어 <b>유령 요격탄 발사</b>(비용 $1.46B→$3.21B, 2.2배). v20.2b 핵심 가치("재고 소진→방어 저하")가 조용히 무력화돼 있었다 → 세척을 site 유무와 분리(연안방공 OFF면 기존 동작 유지=하위호환). · [중] 지상군 지표 15종 UI 소비 0(결과 화면 블록 신설) · [중] 제압 포대가 대리모델 경로서 요격 없이 재고만 소모 · [낮] 교전기록 패트리엇 누락 · [낮] stale 주석(4계층→5계층). <b>AmphibiousForce.lift 죽은 필드는 판단 필요로 남김</b>'),
    ('②', 'DB·수치', '발견 1(HIGH)', '<b>[HIGH] 054B형이 ENEMY_SHIP_SAM_LOADOUT에 없어 SAM·CIWS 0발</b> — DB·changelog·스펙시트가 "054A보다 방공이 강한 발전형"이라 선언한 함정이 실제 교전에선 054A(32발)보다 약한 <b>정체성 역전</b> → HHQ-16 32발·HHQ-10 24발·Type 1130 부여. · [중] <b>YJ-21 is_asbm 누락</b> — 이름·주석이 대함 탄도인데 플래그만 빠져 YJ-21만 있는 구역은 연안 포대가 있어도 정밀 라우팅 미발동 → is_asbm=True. 나머지 수치 정정(SM-2·RAM 단가, KN-23 고도)은 <b>판단 필요</b>'),
    ('③', '회귀', 'PASS', '28케이스 × 29지표 골든 일치. ⚠ <b>수정 후 회귀가 bit-identical이었다 = 고친 버그들이 발현되는 시나리오가 골든에 없었다</b>(사각). 골든이 사각을 못 지키면 조용히 재발한다 → 신규 3케이스로 봉인(골든 24→28): 연안방공-무방비구역(누출을 A/B로 binding 실증)·연안방공-YJ21라우팅(ASBM 강제 3회)·054B-차세대전투단(적 능동방어)'),
    ('④', '통합 MC + 성능', 'PASS', '대규모 MC — 정밀 OFF n=300 win=1.0 surviving=6.0 / 정밀 ON n=200 win=1.0 surviving=5.8 n_precise_avg=3.0 → <b>기준값 메모리(project-baseline-campaign-precise)와 정확히 일치</b>. NaN/Inf 0·확률[0,1]·승무패 합=1.0. 성능 회귀가드 전 경로(단발·전장·캠페인) 기준 대비 1.5배 이내'),
    ('⑤', 'exe·빌드', 'PASS (발견 1 수정)', '빌드 EXIT=0. GUI 스모크 3종 RESULT_CODE=0(단발·캠페인·시나리오) — 🛡 연안 방공·🏖 상륙 배너 exe 렌더 확인. <b>강화한 스모크가 진짜 결함을 잡음</b>: 지상군 배너를 교전분석 패널에만 넣었더니 exe에 안 뜸 — 그 패널은 <b>UIA 접근 밖</b>이라 스모크로 검증 불가(v18 교훈 재확인) → 상태줄에도 요약 추가. 엔진 직접호출 우회 없음(실제 exe 버튼 클릭)'),
    ('⑥', '위생', 'PASS', '정적 45/45 · <b>engine_army 공개 메서드 22개 전부 호출처 있음</b>(죽은 코드 0) · README 프리셋 수 자동검출 정정(44→46) · .gitignore가 _bgtask.meta만 커버해 폴링 메타 파일이 미추적으로 새던 것 → _bg*.meta로 확장 · changelog·_PLANS 코드명 잔류 0'),
    ('⑦', '하위호환', 'PASS', '신규 키가 전무한 구버전 cfg로 단발·캠페인 정상 실행 — 지상군 키 미부착(OFF면 v19 결과와 동일). 신규 플래그 전부 cfg.get(..., False) 패턴 · 지상 BMD 세척 분리도 연안방공 OFF면 기존 동작 보존'),
    ('⑧', '수치·단위', 'PASS', 'property 45케이스 불변식 위반 0(확률[0,1]·합=1·NaN/Inf 0·outcome 유효) · fuzz 단발/전장/<b>캠페인(신설)</b> 극단값에서 크래시·NaN·범위위반 0 · mean_suppression 빈 포대 가드·readiness init≤0 가드 확인'),
    ('⑨', '리소스 누수', 'PASS', '신설 엔진 3종(army·coastal·amphib)에 frames 누적·matplotlib figure·_log 없음 · v20에서 UI figure/canvas 추가 없음 · _record_frame mc_mode 가드 정적 PASS · 캠페인 MC 병렬 풀은 with 컨텍스트 자동 정리(워커 잔존 0)'),
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
         P('감사 범위 주석 — v20 지상군 블록(v18.03.01~v18.04.06). 별도 engine_army.py를 신설해 캠페인 위에 지상 층을 얹었다: 구역별 연안 방공 포대(한국형 BMD 5계층 자산·재고 틱 간 추적·ASBM 정밀 라우팅, v20.2b) · 해상 상륙작전(수송→엄호→상륙 3단계 곱연산, v20.3) · 적 SEAD 도미노(방공망 제압→제공권 상실→해상 교통로 압박, v20.4) · 전력 DB 확충과 편성 반영(패트리엇·KDDX·054B·KC-330, v20.1). 전술 엔진에는 L-SAM·천궁-II·패트리엇 요격층과 탄도탄 종말 강하·지상 사격통제 분리를 추가(v20.2a). 지상 토글 3종 전부 기본 OFF → OFF면 v19 bit-identical.', st_foot),
         Spacer(1, 6*mm)]

# ── 종합 판정 ──
flow += [P('2. 종합 판정', st_h2)]
verdict = Table([[P('통과', S('v', fontName='MalgunBd', fontSize=13, alignment=TA_CENTER, textColor=colors.white)),
                  P('9개 영역 전부 PASS — 발견 7건은 v18.04.05~06에서 그 자리 수정·재감사 완료. 최대 소득은 <b>무방비·재고소진 구역의 지상 BMD 누출</b>(포대가 없거나 재고가 바닥난 구역에서도 요격탄이 발사돼 v20.2b의 핵심 가치가 무력화돼 있었다)과 <b>054B 정체성 역전</b>(발전형이 원형보다 약했다). 두 버그 모두 <b>수정 후에도 회귀가 bit-identical</b>이었다 = 발현 시나리오가 골든에 없던 사각이었고, 골든 3케이스로 봉인해 영구 감시로 전환했다. 감사 도구 자체의 빈틈 2건(fuzz 캠페인 모드 부재·pairwise가 engine_army 미추출)도 함께 닫았다. <b>판단 필요 5건</b>은 밸런스·설계 결정이라 무인 강행하지 않고 사용자 판단 대기(아래 5절)', st_cell)]],
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
         P('• <b>audit_verify_regression.py</b> — 골든 <b>24→28케이스</b> × 29지표 PASS. 신규 3케이스가 이번 감사에서 고친 버그를 영구 봉인: 연안방공-무방비구역(BMD 누출을 A/B로 binding 실증)·연안방공-YJ21라우팅(ASBM 정밀 강제)·054B-차세대전투단(적 능동방어).', st_body),
         P('• <b>audit_static_scan.py</b> — 정적 점검 45/45 PASS(지상 토글 3종세트 자동등록·chk_plans_stale·readme 프리셋 수·file명). audit_property 불변식 45케이스 · audit_perf 성능 회귀가드.', st_body),
         P('• <b>audit_fuzz.py — 캠페인 모드 신설</b> — v20 지상군 수치 키가 한 번도 fuzzing된 적 없던 빈틈을 닫음. 수치키 추출을 경로별 엔진 파일로 분리해, 새 엔진을 추가하면 파일 등록만으로 자동 커버되게 구조화.', st_body),
         P('• <b>audit_pairwise.py — engine_army 추출 추가</b> — v20 핵심 토글 3개(연안 방공·상륙·적 방공망 제압)가 통째로 미검사(7개·21쌍만 돌고 있었다) → 10개·45쌍.', st_body),
         P('• <b>GUI 스모크 3종(단발 + 캠페인 + 시나리오)</b> — 전부 RESULT_CODE=0. 캠페인 스모크에 지상군 배너 검증을 추가했고, <b>그 강화가 실제로 결함을 잡아냈다</b>(UIA 밖 패널에만 배너를 넣어 exe에 안 뜨던 문제). 엔진 직접호출 우회 없음(실제 exe 버튼 클릭).', st_body),
         P('• <b>감사보고서.md</b> — 텍스트 감사 보고서에 v20 블록 섹션 기록(최신순 누적).', st_body),
         Spacer(1, 5*mm)]

# ── 판단 필요 ──
flow += [P('4. 판단 필요 5건 (무인 강행하지 않고 남긴 항목 — 사용자 결정 대기)', st_h2),
         P('전부 <b>밸런스·설계 결정</b>이라 정답이 하나로 정해지지 않는다. 착수 시 각각 회귀 골든 영향과 기준값 메모리 재측정이 따라온다.', st_body)]
jud_rows = [[P('#', st_cellb), P('항목', st_cellb), P('쟁점', st_cellb)]]
for n, item, issue in [
    ('1', 'KN-23 정점고도 2,000m', '공개값은 30~50km인데 2km는 순항미사일 수준. <b>다만</b> 코드에 「QBM: SM-3 거의 무력화」라는 설계 의도가 명시돼 있고 저고도가 곧 그 메커니즘이다. 30,000m로 올려도 SM-3 무력화는 유지되고 THAAD 교전창엔 들어온다 → <b>현실성 우선(수정) vs 설계 의도 유지(보존)</b>'),
    ('2', '공중급유기 제공권 승수', '대당 ×0.15 선형·상한 없음 → 4대면 CAP 전력 ×1.6, 조기경보기(×1.3)와 곱해 <b>×2.08</b>. 상한이나 대당 체감 도입 검토. 단 실측 제공권 이동은 0.58→0.69로 과격하진 않아 <b>과대인지 판단 필요</b>'),
    ('3', '함대공 단가 과소', 'SM-2 Block IIIB <b>$400K</b>(공개 $0.77~2.53M) · RIM-116 RAM <b>$150K</b>(공개 ~$950K) → 비용 지표가 낙관 편향. 정정 시 <b>비용 기준값 메모리 전부 재측정</b>. 해궁도 과소 의심이나 국산 단가 비공개라 보류'),
    ('4', '상륙 규모가 결과에 미반영', '수송 능력이 죽은 필드 — LST 1척과 LPH 3+LPD 2척이 <b>동일한 교두보 진척</b>을 낸다. 반영하려면 진척률에 규모 스케일을 곱하는 <b>새 모델을 정해야</b> 함(설계 결정). 현재 상륙 함정 수가 UI에서 설정 불가라 실사용 영향은 0'),
    ('5', '「BMD 탄도 포화」 프리셋 DF-17 1발', '다층 요격이 발현되지 않는 규모. 실제 교리는 다축 대량 동시 포화 → 4발+ 상향 검토. ARM·극초음속에서 반복된 <b>정밀무기 1발 편성</b> 패턴'),
]:
    jud_rows.append([P(n, st_cellb), P(item, st_cell), P(issue, st_cell)])
jt = Table(jud_rows, colWidths=[8*mm, 36*mm, 130*mm], repeatRows=1)
jt.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#8a5a12')),
    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
    ('FONTNAME', (0,0), (-1,0), 'MalgunBd'),
    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#d8c8ae')),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#faf5ec')]),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('LEFTPADDING', (0,0), (-1,-1), 4), ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
]))
flow += [jt, Spacer(1, 1.5*mm),
         P('권장 — 1·3·5는 DB 현실성(②영역) 계열이라 한 번에 정정 후 골든·기준값을 일괄 갱신하는 편이 효율적. 2·4는 모델 설계 결정이라 별도로 다룬다.', st_foot),
         Spacer(1, 6*mm)]

# ── 메타 회고 ──
flow += [P('5. 메타 회고 (감사 절차 자체 개선)', st_h2),
         P('<b>이번 감사의 최대 교훈: "수정했는데 회귀가 bit-identical이면, 그건 안심이 아니라 골든 사각의 신호다."</b>', st_body),
         P('실제로 이번에 고친 버그 3건(BMD 누출·054B SAM 0발·YJ-21 라우팅)이 전부 골든에 안 잡혔다. 회귀가 통과했다는 사실 자체가 "그 코드 경로를 아무 케이스도 밟지 않는다"는 증거였는데, 그 신호를 읽지 못했다면 조용히 재발했을 것이다.', st_body),
         P('더 나아가 <b>감사 도구마저 v20 경로를 보고 있지 않았다</b> — fuzz는 캠페인 모드가 없어 지상군 수치 키를 한 번도 흔들어보지 않았고, pairwise는 engine_army.py를 토글 추출 대상에서 빠뜨려 v20 핵심 토글 3개를 통째로 건너뛰고 있었다. 새 엔진 파일이 늘어날 때 도구의 대상 목록이 따라가지 않는 구조적 빈틈이다.', st_body),
         P('<b>즉시 반영(도구에 박음)</b> — 골든 3케이스 추가(24→28) · fuzz 캠페인 모드 신설(수치키 추출을 엔진 파일별로 분리) · pairwise engine_army 추출 · 캠페인 스모크에 지상군 배너 검증. 다음 블록부터는 이 경로들이 자동 감시된다.', st_body),
         P('다음 숙제 — 신규 엔진 파일을 추가할 때 감사 도구 3종(fuzz·pairwise·smoke)의 대상 목록에 등록하는 것을 체크리스트로 강제할 것. 사람 기억이 아니라 규칙에 박아야 같은 빈틈을 두 번 겪지 않는다.', st_meta),
         Spacer(1, 6*mm)]

# ── 환경·커밋 정보 (재현성) ──
flow += [P('6. 환경 · 커밋 정보 (재현성)', st_h2)]
env_rows = [
    [P('HEAD 커밋', st_cellb), P('ecee7a3 (v18.04.06 종합 감사 수정)', st_cell), P('Python', st_cellb), P('3.14', st_cell)],
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
flow += [P('차기 종합 감사 — 다음 major 전환 직전(트리거 ①) 또는 아키텍처 전환 시(②). 그전까지 마이너 묶음 완료는 경량 점검(정적 스캔 + 회귀 + 빌드·스모크)으로 처리한다. PDF는 감사보고서/감사보고서_{블록}.pdf로 누적.', st_meta),
         Spacer(1, 6*mm),
         HRFlowable(width='100%', thickness=0.6, color=GREY), Spacer(1, 2*mm),
         P('합동 통합방어 시뮬레이터 · 종합 감사 보고서 · 자동 생성(_audit_make_pdf.py) · 2026-07-13', st_foot)]

doc.build(flow)
print('생성 완료:', OUT)
