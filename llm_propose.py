"""llm_propose.py — 자가개선 루프 S3: 로컬 LLM(Ollama) config 제안기 (빌드 제외 도구)

S2의 규칙 제안기(auto_improve_loop.propose_candidates)를 대체한다. S1 약점
리포트를 프롬프트로 만들어 로컬 Ollama(qwen2.5-coder)에 1회 HTTP 호출 →
Tier1 config 후보(ent_coef·lr)를 JSON으로 받아 파싱한다. plan 10-C 정본.

**Tier1만** — config 숫자만 제안(엔진 코드 무수정). 잘못된 제안이어도 학습·평가
게이트가 Δ로 거른다. Ollama 무응답·파싱 실패 시 규칙기반으로 graceful fallback.

  python llm_propose.py [report.json] [model]
"""
import sys
import os
import json
import re
import urllib.request

OLLAMA_URL = 'http://localhost:11434/api/generate'
DEFAULT_MODEL = 'qwen2.5-coder:7b'

# Tier1 탐색 가드레일 — LLM 제안을 이 범위로 강제 클램프(폭주·무효값 방지).
_ENT_RANGE = (0.0, 0.05)
_LR_RANGE = (1e-4, 1e-3)


def _summarize_report(report):
    """약점 리포트를 LLM이 읽기 좋은 간결 텍스트로."""
    lines = [f"전체 평균 Δ(정책-baseline) = {report.get('mean_delta')}",
             "시나리오별 (Δ 낮은 순):"]
    for s in report.get('scenarios', []):
        oc = s.get('overconverged_levers') or []
        wod = s.get('worst_objective_delta')
        lines.append(
            f"- {s['preset']}: Δ={s['delta']:+.3f} (정책 {s['policy_score']} vs base {s['baseline_score']}), "
            f"약점목표Δ={wod}({s.get('objective_delta', {}).get(wod)}), "
            f"탄약소진={s.get('ammo_exhaust_rate')}, 누출={s.get('leaker_frac')}, "
            f"과수렴레버={oc if oc else '없음'}")
    return "\n".join(lines)


def _build_prompt(report):
    summary = _summarize_report(report)
    return f"""너는 해군 방어 시뮬레이터의 강화학습(PPO) 하이퍼파라미터 튜닝 보조다.
아래는 현재 학습된 정책의 약점 분석 리포트다. 정책이 baseline(기본 전술)보다
약한 구간과 원인이 적혀 있다.

[약점 리포트]
{summary}

[조정 가능한 설정 — Tier1, 엔진 코드는 절대 못 바꾸고 이 두 값만 제안 가능]
- ent_coef: PPO 엔트로피 계수 (0.0~0.05). 높이면 탐색↑·과수렴↓(소수 국면 붕괴 방지),
  낮추면 수렴 가속. 과수렴 레버가 보이면 높이는 게 보통 유효하다.
- learning_rate: 학습률 (0.0001~0.001).

[지침]
- 위 약점(특히 과수렴 레버·약점목표)을 근거로 ent_coef·learning_rate 후보 2~3개를 제안하라.
- 반드시 다양하게: 최소 1개는 현 기준선(ent_coef 0.01) 부근, 나머지는 약점을 노린 변형.
- 각 후보에 한국어 reason(왜 이 값인지, 어떤 약점을 노리는지) 한 줄.

[출력 형식 — 오직 아래 JSON 배열만, 다른 텍스트 금지]
[{{"ent_coef": 0.01, "learning_rate": 0.0003, "reason": "..."}}]
"""


def _clamp(v, lo, hi, default):
    try:
        v = float(v)
    except (TypeError, ValueError):
        return default
    return max(lo, min(hi, v))


def _parse_candidates(text):
    """LLM 응답에서 JSON 배열 추출·검증·클램프."""
    m = re.search(r'\[\s*\{.*\}\s*\]', text, re.S)
    if not m:
        raise ValueError('JSON 배열 미발견')
    arr = json.loads(m.group(0))
    out = []
    for c in arr:
        out.append({
            'ent_coef': _clamp(c.get('ent_coef'), *_ENT_RANGE, 0.01),
            'lr': _clamp(c.get('learning_rate', c.get('lr')), *_LR_RANGE, 3e-4),
            'reason': f"[LLM] {str(c.get('reason', '')).strip()[:120]}",
        })
    return out or None


def llm_propose_candidates(report, model=DEFAULT_MODEL, timeout=120):
    """약점 리포트 → Ollama 호출 → config 후보 리스트. 실패 시 None(호출부가 규칙기반 fallback)."""
    payload = json.dumps({
        'model': model, 'prompt': _build_prompt(report), 'stream': False,
        'options': {'temperature': 0.2},   # 약간의 다양성, 그러나 거의 결정적
    }).encode()
    try:
        req = urllib.request.Request(OLLAMA_URL, data=payload,
                                     headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
        return _parse_candidates(data.get('response', ''))
    except Exception as e:
        print(f'[llm_propose] Ollama 실패 → 규칙기반 fallback: {e}', file=sys.stderr)
        return None


def main():
    report_path = sys.argv[1] if len(sys.argv) > 1 else '_improve_report.json'
    model = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_MODEL
    if not os.path.exists(report_path):
        print(f'리포트 없음: {report_path} (먼저 improve_report.py 실행)')
        sys.exit(2)
    report = json.load(open(report_path, encoding='utf-8'))
    print(f'[프롬프트 요약]\n{_summarize_report(report)}\n')
    print(f'[Ollama 호출] model={model} ...')
    cands = llm_propose_candidates(report, model)
    if not cands:
        print('제안 실패(호출부는 규칙기반 fallback 사용).')
        sys.exit(1)
    print(f'[LLM 제안 {len(cands)}개]')
    for c in cands:
        print(f"  ent_coef={c['ent_coef']} lr={c['lr']} — {c['reason']}")


if __name__ == '__main__':
    main()
