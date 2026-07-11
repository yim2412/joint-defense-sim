#!/usr/bin/env bash
# _bg_launch.sh <logfile> <cmd...> — 백그라운드 작업 표준 런처(반복실수 방지).
#
# 배경: 백그라운드 작업을 던질 때 winpid·시작시각을 _bgtask.meta에 기록해야
# 폴링(_bg_wait.sh)이 '이 작업 트리 전용' CPU/RAM·경과를 박스에 첨부한다.
# 그 meta 기록을 매번 손으로 명령 앞에 붙이다 보니 몇 번 빠뜨려 리소스 격리가
# 실패했다(감사 자기개선: 반복 실수는 사람 기억이 아니라 도구로 굳힌다).
# 이 런처가 meta 기록 + 로그 리다이렉트 + 종료코드 기록을 한 번에 하여 누락을 차단한다.
#
# 사용(run_in_background=true로 호출):
#   bash _bg_launch.sh <log> python audit_pairwise.py --mode all
#   bash _bg_launch.sh <log> python -m PyInstaller app_main.spec --noconfirm
# 폴링:
#   bash _bg_wait.sh <log> "BG_EXIT" 55 4 _bgtask.meta
# 복잡한 파이프/리다이렉트가 필요하면 bash -c 로 감싸 전달:
#   bash _bg_launch.sh <log> bash -c 'A | B > C'
set -u
if [ "$#" -lt 2 ]; then
    echo "사용법: bash _bg_launch.sh <logfile> <cmd...>" >&2
    exit 2
fi
LOG="$1"; shift
# winpid(네이티브 PID)·시작 epoch 기록 — _bg_wait.sh가 트리 리소스 집계에 사용
echo "$(cat /proc/$$/winpid) $(date +%s)" > _bgtask.meta
"$@" > "$LOG" 2>&1
echo "BG_EXIT=$?" >> "$LOG"
