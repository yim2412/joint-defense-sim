"""llm_patch.py — 자가개선 루프 S4: Tier2 엔진코드 제안 + 6중 안전 게이트 (빌드 제외)

LLM이 *코드*를 제안하는 유일한 단계. plan 10-B/10-C 정본. **무인 코드수정 절대 금지.**

6중 안전 게이트(순서, 하나라도 실패 시 중단):
  1. 화이트리스트  — 허용 파일·함수만(rl_env.py 보상/관측)
  2. 정적 안전스캔 — 금지 토큰(os.system·exec·socket·while True…) 발견 시 거부
  3. 함수단위 교체 — AST로 함수를 이름 통째 교체(라인 diff 금지)
  4. 샌드박스      — git worktree 격리 사본(실트리 무손상)
  5. 자동 게이트   — import 스모크 + verify_regression PASS + 학습·평가 Δ>임계(고정seed) + 타임아웃
                     평가는 friendly_score(보상해킹 차단)
  6. 사람 승인     — review 파일 제시 → 명시적 승인에만 실트리 적용

평가가 shaped reward 아닌 friendly_score라, 보상만 부풀리는 해킹은 Δ로 자동 기각.

  제안·게이트:  python llm_patch.py [report.json] [model] [--steps N] [--seeds N]
  게이트 내부:  python llm_patch.py --gate <steps> <seeds>   (worktree서 호출)
"""
import ast
import os
import sys
import re
import json
import time
import hashlib
import shutil
import tempfile
import subprocess
import urllib.request

OLLAMA_URL = 'http://localhost:11434/api/generate'
DEFAULT_MODEL = 'qwen2.5-coder:14b'        # 코드 추론 — S3(7b)보다 큰 모델

# ── 게이트 1: 화이트리스트 (허용 파일 → 함수) ─────────────────────────────────
_ALLOWED = {'rl_env.py': ['_shaping_reward', '_featurize']}

# ── 게이트 2: 정적 안전 스캔 (금지 토큰 — 명백히 위험한 것만) ──────────────────
_FORBIDDEN = [
    r'\bos\s*\.\s*system', r'\bos\s*\.\s*popen', r'\bos\s*\.\s*remove', r'\bos\s*\.\s*rmdir',
    r'\bsubprocess\b', r'\beval\s*\(', r'\bexec\s*\(', r'\bcompile\s*\(',
    r'\bopen\s*\(', r'\bsocket\b', r'\brequests\b', r'\burllib\b', r'\bhttplib\b',
    r'__import__', r'\bimportlib\b', r'\bwhile\s+True\b', r'\bglobals\s*\(',
    r'\bshutil\b', r'\bsys\s*\.\s*exit', r'\b__\w+__\s*=',  # dunder 재정의
]

_ADOPT_MARGIN = 0.02   # Δ 임계(200k 노이즈 ±0.03 감안). S2와 동일 기준.
_GATE_TIMEOUT = 1800   # 샌드박스 학습·평가 상한(초)


def _read(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


# ── 게이트 3: AST 함수 추출·교체 ──────────────────────────────────────────────
def extract_function(src, name):
    """함수/메서드 소스 추출(없으면 None)."""
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return ast.get_source_segment(src, node)
    return None


def _reindent(func_src, indent):
    """함수 소스를 목표 들여쓰기로 정규화(LLM이 indent 0/4 아무거나 줘도 맞춤)."""
    lines = func_src.splitlines()
    # 첫 def 줄 기준 현재 들여쓰기
    base = len(lines[0]) - len(lines[0].lstrip())
    out = []
    for ln in lines:
        if ln.strip():
            cur = len(ln) - len(ln.lstrip())
            out.append(' ' * indent + ln[base:] if cur >= base else ' ' * indent + ln.lstrip())
        else:
            out.append('')
    return '\n'.join(out)


def replace_function(src, name, new_func_src):
    """함수를 이름으로 통째 교체(라인 span 기반, 들여쓰기 보존). 실패 시 ValueError."""
    tree = ast.parse(src)
    target = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            target = node
            break
    if target is None:
        raise ValueError(f'함수 {name} 미발견')
    # 새 함수가 파싱되는지 + 같은 이름인지 검증
    nt = ast.parse(_reindent(new_func_src, 0))
    if not (nt.body and isinstance(nt.body[0], (ast.FunctionDef, ast.AsyncFunctionDef))
            and nt.body[0].name == name):
        raise ValueError('새 코드가 같은 이름의 단일 함수가 아님')
    lines = src.splitlines(keepends=True)
    start = target.lineno - 1
    # 데코레이터가 있으면 그 위부터
    if target.decorator_list:
        start = min(d.lineno for d in target.decorator_list) - 1
    end = target.end_lineno
    indent = len(lines[start]) - len(lines[start].lstrip())
    new_block = _reindent(new_func_src, indent)
    if not new_block.endswith('\n'):
        new_block += '\n'
    return ''.join(lines[:start]) + new_block + ''.join(lines[end:])


def static_safety_scan(code):
    """금지 토큰 검사. 발견 목록 반환(빈 리스트=안전)."""
    hits = []
    for pat in _FORBIDDEN:
        if re.search(pat, code):
            hits.append(pat)
    return hits


# ── 게이트 2.5: LLM 제안 ──────────────────────────────────────────────────────
def _summarize_report(report):
    lines = [f"전체 평균 Δ = {report.get('mean_delta')}", "약점(Δ 낮은 순):"]
    for s in report.get('scenarios', [])[:3]:
        oc = s.get('overconverged_levers') or []
        lines.append(f"- {s['preset']}: Δ={s['delta']:+.3f}, 약점목표Δ="
                     f"{s.get('worst_objective_delta')}, 과수렴={oc or '없음'}")
    return "\n".join(lines)


def _build_prompt(report, file, func, current_src):
    return f"""너는 해군 방어 강화학습(PPO)의 보상/관측 함수를 개선하는 보조다.
아래 약점 리포트를 보고 `{file}`의 `{func}` 함수를 개선하라.

[약점 리포트]
{_summarize_report(report)}

[현재 {func} 함수]
```python
{current_src}
```

[사용 가능한 것 — 이것만 써라. 다른 속성/메서드는 존재하지 않음(환각 금지)]
- 인자 prev, cur 는 state 객체. 속성: cur.intercepted(누적 요격수), cur.total_threats,
  cur.shots_fired, cur.t(현재 시각), cur.threats(위협 리스트), cur.ships(함정 리스트),
  cur.extra(dict: 'leaker_frac','ammo_frac','fuel_frac','asm_inflight','aircraft_frac').
- self._fleet_hp(state) → 생존 함대 HP 합(float). self.reward_shaping(bool).
- numpy는 모듈 상단에서 np로 이미 import됨. 새 import·새 self 속성 금지.

[엄격한 제약 — 위반 시 자동 거부]
- 오직 이 함수 하나만, 같은 이름·같은 시그니처로 반환하라.
- 파일 입출력·네트워크·subprocess·exec/eval·while True·import 추가 금지.
- 보상을 인위적으로 부풀리지 마라(평가는 실제 임무점수로 하므로 무의미).
- 위 '사용 가능한 것'에 없는 속성(예: cur.defended_assets, self.env_config)은 절대 쓰지 마라.

[출력 — 오직 아래 코드블록 하나, 다른 설명 금지]
```python
<개선된 {func} 함수 전체>
```
[개선 의도 한 줄(코드블록 뒤)]: <왜 이렇게 바꿨는지>
"""


def propose_patch(report, file, func, model=DEFAULT_MODEL, timeout=180):
    """LLM에 함수 개선 제안 요청 → (새 함수 소스, 가설 텍스트). 실패 시 (None, err)."""
    current = extract_function(_read(file), func)
    if current is None:
        return None, f'{func} 추출 실패'
    payload = json.dumps({'model': model, 'prompt': _build_prompt(report, file, func, current),
                          'stream': False, 'options': {'temperature': 0.3}}).encode()
    try:
        req = urllib.request.Request(OLLAMA_URL, data=payload,
                                     headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            text = json.loads(resp.read()).get('response', '')
    except Exception as e:
        return None, f'Ollama 실패: {e}'
    m = re.search(r'```python\s*(.*?)```', text, re.S)
    if not m:
        return None, 'python 코드블록 미발견'
    new_func = m.group(1).strip()
    hypo = text[m.end():].strip()[:200]
    return new_func, hypo


# ── 게이트 5: 샌드박스(git worktree) + 자동 게이트 ────────────────────────────
def sandbox_gate(file, patched_src, steps, seeds):
    """git worktree 격리 사본에 패치 적용 → import 스모크 + 회귀 + 학습·평가 Δ.
    반환 dict: {pass, stage, delta, detail}."""
    # Windows 자식 프로세스 출력을 UTF-8로 — 한국어/이모지가 cp949 디코딩에서 깨지지 않게.
    _env = dict(os.environ, PYTHONIOENCODING='utf-8')
    _kw = dict(capture_output=True, text=True, encoding='utf-8', errors='replace', env=_env)
    wt = tempfile.mkdtemp(prefix='_patch_wt_')
    os.rmdir(wt)  # git worktree add는 비존재 경로 요구
    try:
        r = subprocess.run(['git', 'worktree', 'add', '--detach', wt, 'HEAD'], **_kw)
        if r.returncode:
            return {'pass': False, 'stage': 'worktree', 'detail': (r.stderr or '')[:300]}
        # 패치 적용(worktree 내 파일에만 — 실트리 무손상)
        with open(os.path.join(wt, file), 'w', encoding='utf-8') as f:
            f.write(patched_src)
        # 미커밋 의존(이 스크립트 자신)을 worktree에 복사 — worktree는 HEAD만 체크아웃하므로.
        shutil.copy(os.path.abspath(__file__), os.path.join(wt, 'llm_patch.py'))
        # (a) import 스모크
        r = subprocess.run([sys.executable, '-c', f'import {file[:-3]}'],
                           cwd=wt, timeout=120, **_kw)
        if r.returncode:
            return {'pass': False, 'stage': 'import', 'detail': (r.stderr or '')[-400:]}
        # (b) 회귀(엔진 물리 불변 — rl_env 패치엔 약 게이트지만 안전망)
        r = subprocess.run([sys.executable, 'verify_regression.py'], cwd=wt, timeout=600, **_kw)
        if 'PASS' not in (r.stdout or ''):
            return {'pass': False, 'stage': 'regression', 'detail': (r.stdout or '')[-400:]}
        # (c) 학습·평가 Δ (진짜 게이트) — worktree서 --gate 모드
        r = subprocess.run([sys.executable, 'llm_patch.py', '--gate', str(steps), str(seeds)],
                           cwd=wt, timeout=_GATE_TIMEOUT, **_kw)
        m = re.search(r'GATE_DELTA=([-\d.]+)', r.stdout or '')
        if not m:
            return {'pass': False, 'stage': 'eval',
                    'detail': ((r.stdout or '') + (r.stderr or ''))[-400:]}
        delta = float(m.group(1))
        return {'pass': delta > _ADOPT_MARGIN, 'stage': 'eval', 'delta': delta,
                'detail': f'Δ={delta:+.3f} (임계 {_ADOPT_MARGIN})'}
    finally:
        subprocess.run(['git', 'worktree', 'remove', '--force', wt], **_kw)


def _gate_eval(steps, seeds):
    """worktree 안에서 호출 — 패치된 rl_env로 학습 후 friendly_score Δ 출력."""
    from engine import normalize_enemy_db
    from rl_env import make_env, _BALANCED_PRESETS
    from improve_report import eval_baseline, eval_policy
    from stable_baselines3 import PPO
    from stable_baselines3.common.vec_env import DummyVecEnv
    import numpy as np
    normalize_enemy_db()
    sd = list(range(1, seeds + 1))
    base = eval_baseline(sd)
    # DummyVecEnv(단일 프로세스) — worktree 서브프로세스 안 중첩 spawn(SubprocVecEnv) 회피.
    # 게이트 학습은 짧아 병렬 불필요. 패치가 런타임 에러면 여기서 바로 명확히 raise(EOFError 마스킹 없음).
    venv = DummyVecEnv([make_env(reward_shaping=True)])
    model = PPO('MlpPolicy', venv, device='cpu', verbose=0, n_steps=256, ent_coef=0.01)
    model.learn(total_timesteps=steps)
    venv.close()
    pol = eval_policy(model, sd)
    deltas = [float(np.mean([e['friendly_score'] for e in pol[p]])) - base[p]['score']
              for p in _BALANCED_PRESETS]
    print(f'GATE_DELTA={float(np.mean(deltas)):.4f}')


# ── 게이트 6: review 파일 ─────────────────────────────────────────────────────
def write_review(file, func, new_func, hypo, gate, report):
    qdir = '_improve_queue'
    os.makedirs(qdir, exist_ok=True)
    h = hashlib.sha256(new_func.encode()).hexdigest()[:12]
    path = os.path.join(qdir, f'patch_{func}_{h}.md')
    current = extract_function(_read(file), func)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f"# Tier2 패치 제안 — {file}:{func}\n\n")
        f.write(f"- 패치 해시: `{h}`\n- 게이트: **{'통과' if gate['pass'] else '실패'}** "
                f"({gate.get('stage')}, {gate.get('detail')})\n")
        f.write(f"- LLM 가설: {hypo}\n- 약점 입력: {_summarize_report(report)}\n\n")
        f.write(f"## 현재\n```python\n{current}\n```\n\n## 제안\n```python\n{new_func}\n```\n\n")
        f.write("## 승인\n게이트 통과 + 사람 검토 후 적용하려면:\n"
                "`python llm_patch.py --apply " + path + "`\n"
                "(무인 적용 없음 — 이 명령을 사람이 실행해야 실트리에 반영)\n")
    return path, h


def apply_patch(review_path):
    """사람이 명시적으로 호출할 때만 실트리 적용 — review 파일의 제안을 함수 교체 후 커밋 안내."""
    txt = _read(review_path)
    fm = re.search(r'패치 제안 — (\S+):(\w+)', txt)
    pm = re.search(r'## 제안\s*```python\s*(.*?)```', txt, re.S)
    if not (fm and pm):
        print('review 파일 파싱 실패'); return
    file, func, new_func = fm.group(1), fm.group(2), pm.group(1).strip()
    # 적용 직전 화이트리스트·안전스캔 재확인
    if func not in _ALLOWED.get(file, []):
        print(f'거부: {file}:{func} 화이트리스트 밖'); return
    hits = static_safety_scan(new_func)
    if hits:
        print(f'거부: 금지 토큰 {hits}'); return
    patched = replace_function(_read(file), func, new_func)
    with open(file, 'w', encoding='utf-8') as f:
        f.write(patched)
    print(f'적용 완료: {file}:{func}. 검토 후 커밋하세요(패치당 1커밋 권장).')


def main():
    if len(sys.argv) > 1 and sys.argv[1] == '--gate':
        _gate_eval(int(sys.argv[2]), int(sys.argv[3]))
        return
    if len(sys.argv) > 1 and sys.argv[1] == '--apply':
        apply_patch(sys.argv[2])
        return

    args = sys.argv[1:]
    report_path = next((a for a in args if a.endswith('.json')), '_improve_report.json')
    model = next((a for a in args if a.startswith('qwen')), DEFAULT_MODEL)
    steps = int(_argval(args, '--steps', '20000'))
    seeds = int(_argval(args, '--seeds', '3'))
    if not os.path.exists(report_path):
        print(f'리포트 없음: {report_path}'); sys.exit(2)
    report = json.load(open(report_path, encoding='utf-8'))

    # MVP: 보상 함수부터(가장 leverage 큰 단일 함수)
    file, func = 'rl_env.py', '_shaping_reward'
    print(f'[게이트 1] 화이트리스트: {file}:{func} — {"허용" if func in _ALLOWED.get(file, []) else "거부"}')
    if func not in _ALLOWED.get(file, []):
        sys.exit(1)

    print(f'[제안] {model}에 {func} 개선 요청...', flush=True)
    new_func, hypo = propose_patch(report, file, func, model)
    if new_func is None:
        print(f'제안 실패: {hypo}'); sys.exit(1)
    print(f'[가설] {hypo}\n')

    print('[게이트 2] 정적 안전 스캔...', flush=True)
    hits = static_safety_scan(new_func)
    if hits:
        print(f'  거부 — 금지 토큰 {hits}'); sys.exit(1)
    print('  통과(금지 토큰 없음)')

    print('[게이트 3] 함수 단위 교체 검증...', flush=True)
    try:
        patched = replace_function(_read(file), func, new_func)
    except ValueError as e:
        print(f'  거부 — {e}'); sys.exit(1)
    print('  통과(AST 교체 성공)')

    print(f'[게이트 4-5] 샌드박스(worktree) + 회귀 + 학습·평가 (steps={steps}, seeds={seeds})...', flush=True)
    gate = sandbox_gate(file, patched, steps, seeds)
    print(f"  {gate['stage']}: {'통과' if gate['pass'] else '실패'} — {gate.get('detail')}")

    print('[게이트 6] review 파일 작성...', flush=True)
    path, h = write_review(file, func, new_func, hypo, gate, report)
    print(f'  → {path}')
    print(f"\n{'✅ 게이트 통과' if gate['pass'] else '❌ 게이트 실패'} — "
          f"{'사람 검토 후 적용 가능' if gate['pass'] else '제안 보류(기록만)'}. 무인 적용 없음.")


def _argval(args, key, default):
    if key in args:
        i = args.index(key)
        if i + 1 < len(args):
            return args[i + 1]
    return default


if __name__ == '__main__':
    main()
