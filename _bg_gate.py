#!/usr/bin/env python
"""_bg_gate.py — 백그라운드 진행 보고를 '조언'이 아니라 '관문'으로 강제하는 훅.

왜 필요한가 (2026-07-17 v21.4 세션):
  1분 박스 보고 누락이 06-23 이후 **여섯 번** 반복됐다. 그때마다 처방이 같은 종류였다 —
  "나에게 보내는 더 강한 메모"(feedback-verbose-background ⑨→⑭). 여섯 번 다 실패했다.
  결정적 증거: `bg_reminder.py`(PreToolUse)는 **정상 작동**해 매 Bash마다 `_bg_wait.sh`
  사용법까지 정확히 주입했는데도 무시됐다. 가장 강한 기존 장치조차 '조언 텍스트'라 실패했다.
  → 조언을 관문으로 바꾼다. 이 프로젝트가 죽은 기능을 `chk_effect_coverage` **커밋 게이트**로
    이긴 것과 같은 처방("사람 기억이 아니라 도구에 박는다").

두 관문:
  ① pre  (PreToolUse/Bash) — run_in_background인데 `_bgtask.meta` 프리픽스가 없으면 **거부**.
     프리픽스가 없으면 리소스를 작업 트리로 격리할 수 없고(⑬), ②가 잡을 근거도 사라진다.
  ② stop (Stop) — 백그라운드 작업이 **살아 있는데 턴을 끝내려 하면 차단**.
     차단당하면 `_bg_wait.sh`를 부를 수밖에 없고, 그게 55초 뒤 턴을 돌려준다 →
     **1분 폴링 루프가 의지가 아니라 구조로 성립**한다. Claude Code엔 주기 타이머 훅이
     없다는 게 ⑫의 3원인 중 하나였는데, '턴 종료 차단'이 그 타이머를 대신한다.

자기 해제(무한 차단 방지):
  ▸meta의 root PID가 죽어 있으면 = 작업 끝 → meta 지우고 통과(다음 턴부터 정상).
  ▸PID가 살아 있어도 MAX_BLOCKS회 넘게 막았으면 통과 — 게이트가 사용자를 가두지 않는다.
"""
import json
import os
import sys

_ROOT = os.path.dirname(os.path.abspath(__file__))   # meta는 프로젝트 루트에 쓰인다
META = os.path.join(_ROOT, '_bgtask.meta')
BLOCKS = os.path.join(_ROOT, '_bgtask.blocks')
# 55초 × 60 ≈ 55분. 이보다 오래 도는 작업(대규모 MC·RL)이면 사용자가 직접 판단하도록 놓아준다.
MAX_BLOCKS = 60


def _emit(obj):
    # cp949 콘솔에서 한글·기호가 깨지거나 크래시한다(⑬의 알려진 함정). 읽을 수 없는
    # 안내는 관문이 아니라 소음이므로 utf-8로 고정한 뒤 내보낸다.
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass
    print(json.dumps(obj, ensure_ascii=False))
    sys.exit(0)


def _allow():
    sys.exit(0)          # 출력 없음 = 통과


def _pid_alive(pid: int) -> bool:
    try:
        import psutil
        return psutil.pid_exists(pid)
    except Exception:
        # psutil이 없으면 막지 않는다 — 게이트 고장이 작업을 막는 것보다 통과가 안전.
        return False


def _read_meta():
    """meta = '<네이티브 root PID> <시작 epoch>'. 못 읽으면 None."""
    try:
        with open(META, encoding='utf-8') as f:
            parts = f.read().split()
        return int(parts[0]), int(parts[1])
    except Exception:
        return None


def _clear():
    for p in (META, BLOCKS):
        try:
            os.remove(p)
        except OSError:
            pass


def mode_pre():
    try:
        data = json.load(sys.stdin)
    except Exception:
        _allow()
    ti = data.get('tool_input') or {}
    if not ti.get('run_in_background'):
        _allow()                      # 포그라운드는 이 관문의 대상이 아니다
    cmd = ti.get('command') or ''
    if '_bgtask.meta' in cmd:
        _allow()                      # 프리픽스 있음 = 규약 준수
    _emit({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "백그라운드 실행에 _bgtask.meta 프리픽스가 없다. 이게 없으면 리소스를 "
                "'이 작업 트리 전용'으로 격리할 수 없고(시스템 전체 수치는 오해를 부른다), "
                "Stop 게이트가 진행 중인 작업을 인식하지 못해 1분 폴링 루프가 성립하지 않는다.\n"
                "명령 맨 앞에 붙일 것:\n"
                "  WINPID=$(cat /proc/$$/winpid); echo \"$WINPID $(date +%s)\" > _bgtask.meta; "
                "<원래 명령> > _x.log 2>&1; echo \"EXIT=$?\" >> _x.log\n"
                "그다음 foreground로: bash _bg_wait.sh _x.log '<완료패턴|Traceback|Error>' 55 4 _bgtask.meta\n"
                "정본 규칙: feedback-verbose-background ⑫⑬⑭"
            ),
        }
    })


def mode_stop():
    meta = _read_meta()
    if meta is None:
        _clear()
        _allow()                      # 진행 중인 백그라운드 작업 없음
    pid, _started = meta
    if not _pid_alive(pid):
        _clear()                      # 작업 종료 → 게이트 자동 해제
        _allow()
    try:
        n = int(open(BLOCKS, encoding='utf-8').read().strip()) + 1
    except Exception:
        n = 1
    if n > MAX_BLOCKS:
        _clear()
        _emit({"systemMessage": "백그라운드 폴링 게이트: 상한 도달 — 통과시킴(작업은 계속 중)."})
    with open(BLOCKS, 'w', encoding='utf-8') as f:
        f.write(str(n))
    _emit({
        "decision": "block",
        "reason": (
            f"백그라운드 작업(PID {pid})이 아직 살아 있는데 턴을 끝내려 했다. "
            "완료 통지를 기다리는 것은 진행 보고가 아니다 — 사용자는 그동안 화면이 멈춘 것으로 본다.\n"
            "지금 할 일: foreground로 다음을 호출하고(55초 안에 반환) 반환값으로 박스를 그린다.\n"
            "  bash _bg_wait.sh <로그> '<완료패턴|Traceback|Error|FAILED>' 55 4 _bgtask.meta\n"
            "STATUS=RUNNING이면 박스 보고 후 재호출, STATUS=DONE이면 결과 보고. "
            "박스는 10필드 고정(작업·시작·경과·예상총·ETA·진행바·현재단계·리소스·최근로그·판정). "
            "경과·진행률은 반드시 로그 실측으로 — 추측 금지. 정본: feedback-verbose-background ⑬⑭"
        ),
    })


if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'stop'
    (mode_pre if mode == 'pre' else mode_stop)()
