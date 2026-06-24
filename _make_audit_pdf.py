# -*- coding: utf-8 -*-
"""
_make_audit_pdf.py — 종합 감사 보고서를 PDF(보고서 형식)로 출력 (빌드 제외 도구)

reportlab + 맑은 고딕. 군 보고서 양식으로 조판.
종합 감사를 할 때마다 이 스크립트의 BLOCK·내용을 그 블록에 맞게 갱신해
실행하면, 블록별 PDF가 `감사보고서/` 폴더에 누적된다(블록당 1개).

사용: python _make_audit_pdf.py  →  감사보고서/감사보고서_selfplay.pdf
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
BLOCK = 'selfplay'                               # 감사 블록 — 매 감사마다 갱신
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
                        title='종합 감사 보고서 — self-play/RL 블록', author='합동 통합방어 시뮬레이터')
flow = []

# ── 표제 ──
flow += [P('종 합 감 사 보 고 서', st_title),
         Spacer(1, 3*mm),
         P('self-play/RL 블록 — AI 전술 exe 통합 · 적 전술 RL 주입(self-play)', st_sub),
         Spacer(1, 4*mm),
         HRFlowable(width='100%', thickness=1.4, color=NAVY), Spacer(1, 5*mm)]

# ── 개요(메타) 표 ──
meta_rows = [
    [P('감사 일자', st_cellb), P('2026-06-24', st_cell), P('판정', st_cellb), P('통과 (9영역 PASS/해당없음)', st_pass)],
    [P('대상 범위', st_cellb), P('v15.14.01 + Phase 5.6.1~5.6.3 (직전 v15 감사 3a78e41 이후 누적)', st_cell), P('발견 항목', st_cellb), P('0 건', st_cellb)],
    [P('변경 규모', st_cellb), P('engine_v7 +19줄 · launcher +43줄 · launcher.spec +3줄 · changelog +8줄 (self-play 학습 인프라 S1~S4·selfplay_env/loop는 빌드제외 .py)', st_cell), P('트리거', st_cellb), P('① self-play 큰 묶음 일단락', st_cell)],
    [P('감사 방식', st_cellb), P('무인 모드 — 착수 승인=9영역 포괄동의. exe 스모크는 GUI 자동화(pywinauto)', st_cell), P('근거 규칙', st_cellb), P('CLAUDE.md 종합 감사 9영역', st_cell)],
    [P('소요/특성', st_cellb), P('빌드 exit0 ~70초 · 기본 GUI 스모크 + RL 토글 GUI 스모크 모두 RESULT_CODE=0 · 잔존 프로세스 0', st_cell), P('무인/수동', st_cellb), P('100% 무인 · 사용자 개입 0회', st_cell)],
    [P('점검 규모', st_cellb), P('회귀 8케이스×26지표(208 대조) · audit_scan 11/11 · ① 누적 diff 에이전트 리뷰 1회 · 구버전 cfg 하위호환 실행 · rl_infer 수치 가드 점검', st_cell), P('재감사', st_cellb), P('0회 (발견 0)', st_cell)],
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
    ('①', '코드·로직', 'PASS', '누적 diff(3a78e41..HEAD) 에이전트 리뷰 발견 0건 · 부모 무수정(BattleEngine _enemy_rl/_apply_tactical_choice enemy_mode 주입/_adaptive_tactic_update 오버라이드 모두 self 속성·super() 위임) · ai_tactic=rl은 학습 전용→exe 도달불가 dead path · enemy_mode None 가드·_enemy_rl 기본 False RNG 불변 · enable_rl_policy 3종세트 완비 · rl_infer 라우팅 try/except None 폴백'),
    ('②', 'DB·수치', 'NA', '해당없음 — DB 수치 변경 0건(rl_policy.npz는 학습 가중치, DB 아님). spec_db=엔티티 DB 합 정합(audit_scan) 유지'),
    ('③', '회귀', 'PASS', 'verify_regression.py — 8케이스 × 26지표 골든값 일치(동작 보존) · 결정론 유지(enemy_mode 훅이 단발·기본 경로 RNG 순서 불변)'),
    ('④', '통합 MC + 성능', 'NA', '해당없음 — 엔진 교전 로직 무변경(훅·추론 주입만, 토글 기본 OFF). baseline 53.2%·wall-time 영향 없음'),
    ('⑤', 'exe·빌드', 'PASS', '빌드 exit 0(exe 53MB) · 번들 무결성(_internal에 rl_policy.npz·changelog·spec_db·battle_surrogate·cesium, rl_infer hiddenimports) · 기본 GUI 스모크 PASS(요격률 표시) · RL 토글 GUI 스모크 PASS(전장+AI 전술 ON→임무점수·요격률 표시→정상종료) · 잔존 프로세스 0'),
    ('⑥', '위생', 'PASS', 'APP_VERSION=헤더=changelog 마지막 v15.14.01 정합 · changelog 연속(RL 내부라벨 충돌 회피 점프) · gitignore 커버 완전(_selfplay_*·_rl_ppo_model*·_rl_ckpt/·_improve_*) · 민감 산출물 추적 0 · self-play 소스 10종 .py 정상 추적 · _PLANS 코드명 잔류 0'),
    ('⑦', '하위호환', 'PASS', 'enable_rl_policy·ai_tactic 키 누락한 구버전 cfg로 전장 실행 → win 정상(cfg.get(...,False)·_enemy_rl 기본 False 폴백)'),
    ('⑧', '수치·단위', 'PASS', 'rl_infer.featurize 가드 완비: dists=[..] or [999.0](빈 위협 min/len 안전) · fleet_max=float(..) or 1.0(0나눗셈 가드) · irate=.. if tot else 0.0 · horizon 폴백>0 · numpy forward에 log/sqrt 없음'),
    ('⑨', '리소스 누수', 'PASS', '_log() _mc_mode 가드 · _record_frame if not _mc_mode 가드(audit_scan) · 추론 cb는 30초 주기 호출·누적 상태 없음(numpy forward 즉시 반환)'),
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
                  P('9개 영역 전부 PASS 또는 해당없음 · 발견 항목 0건 · 수정할 버그 없음 — self-play/RL 블록 종료 선언 가능', st_cell)]],
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
         P('• <b>audit_scan.py</b> — 정적 점검 자동 스캐너 11항목 실행 11/11 PASS(버전 정합·gitignore·_log/frames 가드·enable 3종세트·spec_db 정합·전장 분모 가드·MC 3경로).', st_body),
         P('• <b>_audit_smoke.py</b> — 기본 GUI 자동화 스모크(홈→앱→시뮬→요격률 표시→정상 종료) RESULT_CODE=0.', st_body),
         P('• <b>_smoke_rl.py</b> — RL 토글 GUI 스모크. 지속 전장 모드 + AI 전술(학습된 정책) 둘 다 ON 후 전장 시뮬 실행→임무점수·요격률 표시→정상 종료를 무인 검증(엔진 직접호출 우회 없이 GUI 워커 경로). RESULT_CODE=0.', st_body),
         P('• <b>① 누적 diff 에이전트 리뷰</b> — working tree clean이라 병합 후 빈 diff 빈틈을 누적 diff(3a78e41..HEAD) 직접 투입으로 해소(v15 감사 메타회고 숙제 이행).', st_body),
         P('• <b>감사보고서.md</b> — 텍스트 감사 보고서에 self-play/RL 블록 섹션 기록(최신순 누적).', st_body),
         Spacer(1, 5*mm)]

# ── 메타 회고 ──
flow += [P('4. 메타 회고 (감사 절차 자체 개선)', st_h2),
         P('이번 감사에서 식별·이행한 절차 개선:', st_body),
         P('• <b>병합 후 /code-review 빈 diff 빈틈 해소</b> — v15 감사의 숙제였던 항목. 이번엔 누적 diff(3a78e41..HEAD)를 에이전트에 직접 투입해 의미 리뷰를 수행(부모 무수정·3종세트·폴백 검증). shift-left 대안으로 검증된 경로.', st_body),
         P('• <b>RL 토글 GUI 스모크 경로 확보</b> — _smoke_rl.py로 전장+AI 전술 동시 ON 워커 경로를 자동 검증. v15.14.01 같은 전장 전용 토글 신기능의 exe 검증 사각을 메움.', st_body),
         P('다음 숙제 — self-play 학습 .py(selfplay_env/loop·자가개선 루프)는 빌드제외라 회귀·스모크 사각. 향후 학습 인프라 변경 시 _selfplay_train.py 단발 롤아웃을 audit 절차에 편입 고려.', st_meta),
         Spacer(1, 6*mm)]

# ── 환경·커밋 정보 (재현성) ──
flow += [P('5. 환경 · 커밋 정보 (재현성)', st_h2)]
env_rows = [
    [P('HEAD 커밋', st_cellb), P('5380718', st_cell), P('Python', st_cellb), P('3.14', st_cell)],
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
flow += [P('차기 종합 감사 — 다음 큰 묶음 완료 시 또는 v16 major 전환 직전(트리거 ①/②). PDF는 감사보고서/감사보고서_v16.pdf로 누적.', st_meta),
         Spacer(1, 6*mm),
         HRFlowable(width='100%', thickness=0.6, color=GREY), Spacer(1, 2*mm),
         P('합동 통합방어 시뮬레이터 · 종합 감사 보고서 · 자동 생성(_make_audit_pdf.py) · 2026-06-24', st_foot)]

doc.build(flow)
print('생성 완료:', OUT)
