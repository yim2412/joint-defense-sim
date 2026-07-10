#!/usr/bin/env bash
# _bg_wait.sh — 백그라운드 작업의 "1분 타임박스 대기" 헬퍼 (개발 워크플로우 도구, 빌드 제외)
#
# 배경: Claude Code엔 주기 타이머 훅이 없고(bg_reminder.py는 시작 시점 리마인더일 뿐),
# foreground 단독 `sleep`은 하네스가 차단한다. 그래서 과거 `sleep 55; tail` 1분 틱 패턴이
# 무효화됐다. 완료를 한 번에 기다리는 blocking until-loop는 중간 보고를 못 낸다.
# → 이 헬퍼로 "짧은 상한(기본 55s) + 조기종료 조건" until-loop를 돌려, 매 호출이 55초 안에
#   반환하게 한다. 호출자(Claude)는 반환 때마다 박스 UI로 진행 보고 후, RUNNING이면 재호출한다.
#   (until-loop 내부 sleep은 허용되므로 동작한다.)
#
# 사용: bash _bg_wait.sh <logfile> <done_regex> [max_sec=55] [tail_n=4] [metafile]
#   done_regex : 완료를 뜻하는 로그 패턴(예: "Build complete|Traceback|RESULT_CODE")
#   metafile   : "<root_pid> <start_epoch>" (있으면 작업 트리 CPU/RAM·경과를 함께 출력)
# 출력 마지막 줄: STATUS=DONE (완료 패턴 감지) 또는 STATUS=RUNNING (상한 경과, 아직 진행 중)
set -u
log="${1:?logfile 필요}"; pat="${2:?done_regex 필요}"; max="${3:-55}"; tn="${4:-4}"; meta="${5:-_bgtask.meta}"
i=0; step=5; status=RUNNING
while [ "$i" -lt "$max" ]; do
  if [ -s "$log" ] && grep -qiE "$pat" "$log" 2>/dev/null; then status=DONE; break; fi
  sleep "$step"; i=$((i + step))
done
# 상한 직전 한 번 더 확인(마지막 step 동안 완료됐을 수 있음)
if [ "$status" = RUNNING ] && [ -s "$log" ] && grep -qiE "$pat" "$log" 2>/dev/null; then status=DONE; fi
# 이 작업 트리(부모+자식) 전용 CPU/RAM·경과 — metafile 있을 때만
if [ -f "$meta" ]; then
  echo "--- 리소스(이 작업 트리 전용) ---"
  python _bg_res.py "$meta" 2>/dev/null || echo "(리소스 측정 실패)"
fi
echo "--- tail($tn) @ ${i}s ---"
tail -n "$tn" "$log" 2>/dev/null || echo "(로그 없음/미출력)"
echo "STATUS=$status"
