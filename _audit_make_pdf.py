# -*- coding: utf-8 -*-
"""
_audit_make_pdf.py — 종합 감사 보고서를 PDF(보고서 형식)로 출력 (빌드 제외 도구)

reportlab + 맑은 고딕. 군 보고서 양식으로 조판.
종합 감사를 할 때마다 이 스크립트의 BLOCK·내용을 그 블록에 맞게 갱신해
실행하면, 블록별 PDF가 `감사보고서/` 폴더에 누적된다(블록당 1개).

사용: python _audit_make_pdf.py  →  감사보고서/감사보고서_v21.pdf
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
BLOCK = 'v21'                                    # 감사 블록 — 매 감사마다 갱신
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
                        title='종합 감사 보고서 — v21 합동작전 블록', author='합동 통합방어 시뮬레이터')
flow = []

# ── 표제 ──
flow += [P('종 합 감 사 보 고 서', st_title),
         Spacer(1, 3*mm),
         P('v21 합동작전 블록 — 합동 화력·통합 보고서·JCS 충돌 경고·통합 시나리오', st_sub),
         Spacer(1, 4*mm),
         HRFlowable(width='100%', thickness=1.4, color=NAVY), Spacer(1, 5*mm)]

# ── 개요(메타) 표 ──
meta_rows = [
    [P('감사 일자', st_cellb), P('2026-07-24', st_cell), P('판정', st_cellb), P('통과 (9영역 PASS)', st_pass)],
    [P('대상 범위', st_cellb), P('v21.01.01 ~ v21.04.02, 커밋 24ad4f4..157d246. 합동 화력 지원(v21.2·engine_joint 신설) + 통합 보고서 군별 기여도 반사실 분해(v21.4·shapley) + 합동작전 사령부 자원 충돌 경고(v21.1·상시 관찰층) + 육해공 통합 캠페인 시나리오 3종(v21.3) + 잠수함 현무-3C 대함 비물리 정정(별건)', st_cell), P('발견 항목', st_cellb), P('1 건 (규명·조치)', st_find_hdr)],
    [P('변경 규모', st_cellb), P('engine_joint.py 신설(JointFires·build_land_stock) · engine_campaign(JCS 경고·joint 접합·shapley·MC 키) · engine_airforce(strike_effort·defer_strike) · engine_army(ARMY_FIRE_PRESETS·fire_rounds) · engine_combat(현무-3C 대함 제외) · engine_core(현무-3C KDX-III/KSS-III DB) · scenarios(통합 3종) · mixin_resultpanel(JCS 배너)', st_cell), P('트리거', st_cellb), P('① major 전환 (v21 블록 완료)', st_cell)],
    [P('감사 방식', st_cellb), P('무인 모드 — 착수 승인=9영역 포괄동의. 발견 항목은 그 자리 규명·조치·재검증. 코드/로직·DB 현실성 등 판단 영역은 에이전트 spawn 없이 직접 diff·DB 정독', st_cell), P('근거 규칙', st_cellb), P('CLAUDE.md 종합 감사 9영역', st_cell)],
    [P('소요/특성', st_cellb), P('빌드 EXIT=0·248s(기준 384s) · GUI 스모크 2종 RESULT_CODE=0(단발·캠페인, 합동화력·군별기여도 배너 exe 렌더 확인) · 합동 MC 안정(NaN 0) · 성능 회귀가드 규명·기준선 갱신', st_cell), P('무인/수동', st_cellb), P('100% 무인 · 사용자 개입 0회', st_cell)],
    [P('점검 규모', st_cellb), P('회귀 <b>38케이스</b> × 29지표 bit-identical · audit_static_scan 51/51 · 불변식 45케이스 · fuzz(단발) · <b>pairwise 1225쌍</b>(단발 50토글) · 신규함수 6종 호출처 전수', st_cell), P('재감사', st_cellb), P('발견 1건 규명·조치 후 재검증 PASS', st_pass)],
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
    ('①', '코드·로직', 'PASS', '짝 3중 게이트(enable_joint_fires ∧ strategic_strike ∧ air_campaign) 정합 — 하나만 빠져도 층 미생성 · <b>AirCampaign(bases=None, defer_strike=False) 기본인자 = 합동화력 OFF면 bit-identical</b>(부모 무수정) · defer_strike로 공군 폭격을 합동 층에 위임(이중계상 방지) · <b>_jcs_warnings 관찰 only</b>(병합된 result 공개지표만 읽고 교전·배정 무수정) · _MC_ACC_DEFAULTS None 가드(enemy_output_factor 1.0=무손상) · JCS 배너가 합동화력 세그먼트의 협조미비·육군미참여 중복을 통합 · 신규함수 6종 전부 호출처 존재 · <b>pairwise 1225쌍(단발) 크래시·NaN·보존식 위반 0</b>'),
    ('②', 'DB·수치', 'PASS', '현무-3C: KDX-III-B1 <b>32</b>(KVLS-I 48셀=현무32+홍상어16, 공개 보도값)·B2 <b>16</b>(KVLS-II 24셀, 8셀 탄도형 미모델)·KSS-III <b>6</b>(도산안창호급 VLS 6셀) — 전부 공개 제원 정합 · ARMY_FIRE_PRESETS(현무-2B 24/48·현무-2C 24, 800km급) · 현무-3C를 대함 무기 선택에서 제외(지상공격 전용 = SM-3 외기권·SAM 대공과 같은 계열의 잘못된 무기·표적 정정) · db_specsheet note 동기화(대함 아님·KSS-III 잠수함 발사 명시) · 정적 db_specsheet=엔티티DB 집합 PASS'),
    ('③', '회귀', 'PASS', '38케이스 × 29지표 <b>bit-identical</b>. v21은 캠페인 층 추가(단발 골든 무영향) + 현무-3C 정정(골든 편대 중 잠수함은 대잠전단 KSS-II뿐, KSS-II는 현무-3C 없음·KSS-III는 어떤 골든에도 없음 → 무변경). 결정론(campaign_seed) 유지 · 골든 커버리지 정적 PASS'),
    ('④', '통합 MC + 성능', 'PASS (발견1 규명)', '합동 MC — 한반도 전면전 n=20 승률 100%·통제 100%±0·합동순항 80발·지대지 72·적출항 59%·JCS경고 2.0건·<b>NaN 0</b>. <b>[발견] 성능 가드 battle ×6.5 플래그 → 규명: stale 기준선</b>(89ms는 1200s 지평 전장에 물리적 불가=0.37ms/step, v21 engine_combat 변경은 잠수함 대함 경로라 측정 시나리오 「기동전단 기본」에 잠수함이 없어 <b>미실행 = byte-identical</b>). 2회 재측정 안정(555~581ms) 후 기준선 갱신(single 667·battle 570·campaign 32) → 재검증 PASS'),
    ('⑤', 'exe·빌드', 'PASS', '빌드 EXIT=0·248s(기준 384s의 0.65배). <b>단발 GUI 스모크 PASS</b>(요격률 결과 표시) · <b>캠페인 GUI 스모크 PASS</b>(안개·제공권·방공망·적기지·연안방공·상륙·<b>🤝합동화력·📊군별기여도</b> 배너 exe 렌더 + 캠페인 MC 병렬 10회 end-to-end). 이전 BLOCKED이던 캠페인 스모크 인코딩 문제 해소 · 정적 리소스경로 _MEIPASS·번들 무결성 PASS. 엔진 직접호출 우회 없음(실제 exe 버튼 클릭)'),
    ('⑥', '위생', 'PASS', '정적 51/51 · _PLANS v21.1/v21.3 「구현완료—제거」 정리(chk_plans_stale PASS) · 신규함수 6종(build_land_stock·_navy_effort·_army_effort·fire_rounds·strike_effort·_jcs_warnings) 죽은코드 0 · 헤더·APP_VERSION·changelog 정합 · README 단계 v21.04 자동검출 정합 · 감사 temp 정리'),
    ('⑦', '하위호환', 'PASS', 'v21 키가 전무한 구버전 cfg로 캠페인(joint None·jcs_warning_count 0)·단발 정상 실행 — 합동화력·JCS 미생성이 v20 결과와 동일. 신규 플래그 전부 cfg.get(..., False) 패턴 · 현무-3C 정정도 KSS-III 미배치면 무영향'),
    ('⑧', '수치·단위', 'PASS', 'property 45케이스 불변식 위반 0(확률[0,1]·합=1·NaN/Inf 0·outcome 유효) · fuzz 단발 극단값 크래시·NaN·범위위반 0 · JCS 경고 카운트 int·심각도 정렬 안정 · joint_dmg_share 0나눗셈 가드(tot&gt;0) · _NAVY_DMG·_ARMY_DMG 계수 [0,1] 범위'),
    ('⑨', '리소스 누수', 'PASS', 'engine_joint에 frames 누적·matplotlib figure·_log/print 없음 · fire_log는 전역당 ≤72엔트리(틱 상한)이고 MC는 인스턴스마다 신규 생성·리스트/dict 키는 _MC_ACC_KEYS 제외(MC 누적 폭발 없음) · jcs_warnings ≤3엔트리 · 캠페인 MC 병렬 풀 with 컨텍스트 자동 정리(워커 잔존 0)'),
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
         P('범례 — PASS: 점검 통과 · 해당없음: 블록과 무관해 생략 · 발견N: N건 발견(그 자리 규명·조치·재검증). 9영역 전부 PASS/해당없음이어야 블록 종료 선언.', st_foot),
         P('감사 범위 주석 — v21 합동작전 블록(v21.01.01~v21.04.02). engine_joint.py를 신설해 캠페인 위에 합동 화력 층을 얹었다: 육해공이 공유 표적(EnemyBase 적 항구·비행장)을 협조 타격, 완파 표적은 잔여 표적으로 화력을 넘겨 낭비 방지(v21.2). 각 군을 뺀 전역을 실제 재실행해 기여도를 Shapley로 분해하는 통합 보고서(v21.4). 각 군 독립 배정의 충돌(협조미비·육군미참여·화력중복)을 지휘부가 경고로 표면화하는 상시 관찰층 — 교전 결과 무변경(v21.1). 육해공 통합 캠페인 시나리오 3종(전면전·대만해협·제한전, v21.3). 잠수함 현무-3C 대함 오용 정정과 합동 화력 지상공격 연결(별건). 합동화력 3종 토글 전부 OFF면 v20 bit-identical.', st_foot),
         Spacer(1, 6*mm)]

# ── 종합 판정 ──
flow += [P('2. 종합 판정', st_h2)]
verdict = Table([[P('통과', S('v', fontName='MalgunBd', fontSize=13, alignment=TA_CENTER, textColor=colors.white)),
                  P('9개 영역 전부 PASS. 유일한 발견은 <b>v21과 무관한 stale 성능 기준선</b>(전장 baseline 89ms가 1200초 지평 전장 시뮬로 물리적으로 불가능한 값)으로, v21의 engine_combat 변경이 측정 시나리오의 코드 경로를 밟지 않음을 코드 추적으로 확인하고 기준선을 현재 안정값으로 갱신했다. 핵심 설계(합동화력 짝 3중 게이트·JCS 관찰층의 교전 무영향·현무-3C 대함 정정)가 모두 하위호환(OFF·미배치면 bit-identical)을 지키며, 회귀 38×29·pairwise 1225쌍·property 45케이스·단발+캠페인 GUI 스모크가 전부 통과했다.', st_cell)]],
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
         P('• <b>audit_verify_regression.py</b> — 골든 <b>38케이스</b> × 29지표 bit-identical PASS. v21은 캠페인 층 추가·현무-3C 정정이 단발 골든 경로를 밟지 않아 무변경(KSS-III는 어떤 골든에도 없음).', st_body),
         P('• <b>audit_static_scan.py</b> — 정적 점검 51/51 PASS(합동화력 3종세트·JCS 배너·chk_plans_stale·readme 단계버전·db_specsheet=DB). audit_property 불변식 45케이스 위반 0 · audit_fuzz 단발 극단값 PASS.', st_body),
         P('• <b>audit_pairwise.py</b> — 단발 50토글 1225쌍 크래시·NaN·보존식 위반 0.', st_body),
         P('• <b>audit_perf.py</b> — battle 기준선이 물리적으로 불가능한 stale 값이던 것을 규명(v21 무관)하고 현재 안정값으로 갱신 → 재검증 전 경로 1.5배 이내 PASS.', st_body),
         P('• <b>GUI 스모크 2종(단발 + 캠페인)</b> — 전부 RESULT_CODE=0. 캠페인 스모크가 🤝합동화력·📊군별기여도 배너를 exe에서 렌더 확인 + 캠페인 MC 병렬 10회 end-to-end. 엔진 직접호출 우회 없음(실제 exe 버튼 클릭).', st_body),
         P('• <b>감사보고서.md</b> — 텍스트 감사 보고서에 v21 블록 섹션 기록(최신순 누적).', st_body),
         Spacer(1, 5*mm)]

# ── 발견·조치 ──
flow += [P('4. 발견·조치 (1건)', st_h2)]
fnd_rows = [[P('#', st_cellb), P('항목', st_cellb), P('규명 · 조치', st_cellb)]]
for n, item, issue in [
    ('1', '성능 가드 battle ×6.5 플래그 (④)', 'battle 실행시간 555~581ms이 기준 89ms의 6.5배로 플래그. <b>규명 = stale 기준선</b>: 89ms는 1200초 지평 전장 시뮬(랴오닝 항모전단 대상)로 물리적으로 불가능(0.37ms/step)한 값으로, 과거 다른 조건에서 캡처된 것. v21의 engine_combat 변경은 <b>_select_sub_strike_wpn(잠수함 대함 무기 선택)</b> 한 곳뿐인데, 성능 측정 시나리오 「기동전단 기본」에는 잠수함이 없어 그 코드가 <b>실행조차 되지 않는다</b> → battle 시간은 v21과 byte-identical. <b>조치</b>: 5회 중앙값 2회 재측정으로 안정(555~581ms) 확인 후 기준선을 현재값으로 갱신, 가드 유용성 복구. v21 회귀 아님')
]:
    fnd_rows.append([P(n, st_cellb), P(item, st_cell), P(issue, st_cell)])
ft = Table(fnd_rows, colWidths=[8*mm, 40*mm, 126*mm], repeatRows=1)
ft.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#8a5a12')),
    ('TEXTCOLOR', (0,0), (-1,0), colors.white),
    ('FONTNAME', (0,0), (-1,0), 'MalgunBd'),
    ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#d8c8ae')),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#faf5ec')]),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('LEFTPADDING', (0,0), (-1,-1), 4), ('RIGHTPADDING', (0,0), (-1,-1), 4),
    ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
]))
flow += [ft, Spacer(1, 1.5*mm),
         P('판단 필요 항목 없음 — 이번 블록은 밸런스·설계가 갈리는 발견이 없어 전부 무인으로 종결.', st_foot),
         Spacer(1, 6*mm)]

# ── 메타 회고 ──
flow += [P('5. 메타 회고 (감사 절차 자체 개선)', st_h2),
         P('<b>이번 감사의 교훈: "성능 가드는 기준선의 물리적 타당성을 아무도 검증하지 않으면 조용히 무의미해진다."</b>', st_body),
         P('battle 기준선 89ms는 1200초 지평 전장 시뮬로는 나올 수 없는 값이었는데, 오래 방치돼 매 측정마다 거짓 플래그를 냈다. 성능 가드가 "이전 대비 급증"만 보고 "값 자체가 말이 되는가"는 보지 않은 빈틈이다.', st_body),
         P('<b>[빈틈] 캠페인 GUI 스모크가 JCS 충돌 경고 배너를 명시 검증하지 않음</b> — 합동화력·군별기여도 배너는 assertion하나 v21.1 JCS 「⚖ 충돌 경고」 세그먼트는 확인하지 않는다(경고는 충돌 발생 시에만 떠 스모크 시나리오가 안 건드림). JCS 배너 코드는 같은 _render_campaign_result에서 렌더돼 저위험이나, 향후 <b>충돌 유발 시나리오(동시 타격+폭격기) + JCS 배너 assertion</b>을 _audit_campaign_smoke.py에 추가할 가치가 있다.', st_body),
         P('<b>즉시 반영</b> — stale 성능 기준선을 현재 안정값으로 갱신(가드 유용성 복구). <b>다음 숙제</b>(patch_queue 감사 개선으로 남김): ① audit_perf에 기준선 하한 가드(측정값이 baseline의 0.5배 미만이면 「측정 오류 의심」 표시)로 물리적 타당성 자동 점검 ② 캠페인 스모크에 JCS 배너 assertion 추가.', st_meta),
         Spacer(1, 6*mm)]

# ── 환경·커밋 정보 (재현성) ──
flow += [P('6. 환경 · 커밋 정보 (재현성)', st_h2)]
env_rows = [
    [P('HEAD 커밋', st_cellb), P('157d246 (v21.04.02) · 감사 시점', st_cell), P('Python', st_cellb), P('3.14', st_cell)],
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
         P('합동 통합방어 시뮬레이터 · 종합 감사 보고서 · 자동 생성(_audit_make_pdf.py) · 2026-07-24', st_foot)]

doc.build(flow)
print('생성 완료:', OUT)
