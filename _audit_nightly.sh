#!/usr/bin/env bash
# _audit_nightly.sh — 야간 자동 감사 러너(정기 자동 감사, plan_workflow_upgrades ②).
#
# 모든 감사가 수동 트리거라, 밤에 자동으로 회귀·성능 급변을 감시하면 다음 날 아침
# 세션이 로그를 읽어 곧바로 보고할 수 있다. 정적+회귀+속성+fuzz(전장)+pairwise(전장·
# 캠페인)+성능을 순차 실행하고 결과를 감사야간로그/YYYY-MM-DD.log에 누적한다
# (FAIL 있으면 파일 맨 위 종합 줄에 요약 → 브리핑이 그 한 줄만 봐도 판단).
#
# Windows 작업 스케줄러 등록(사용자 1회, 컴퓨터 켜져 있으면 Claude 없이 매일 새벽 실행):
#   schtasks /create /tn "야간감사" /sc daily /st 03:00 ^
#     /tr "\"C:\Program Files\Git\bin\bash.exe\" \"C:\Users\준\Desktop\국방시스템공학\_audit_nightly.sh\""
# 수동 실행:  bash _audit_nightly.sh
set -u
cd "$(dirname "$0")" || exit 1
export PYTHONIOENCODING=utf-8

LOGDIR="감사야간로그"; mkdir -p "$LOGDIR"
LOG="$LOGDIR/$(date +%Y-%m-%d).log"
BODY="$(mktemp)"
FAILS=()

run() {
    local name="$1"; shift
    { echo ""; echo "── $name ──"; } >> "$BODY"
    if "$@" >> "$BODY" 2>&1; then
        echo "  ✅ $name PASS" >> "$BODY"
    else
        echo "  ❌ $name FAIL" >> "$BODY"
        FAILS+=("$name")
    fi
}

run "정적 스캔"                python audit_static_scan.py
run "회귀 검증"                python audit_verify_regression.py
run "속성 감사"                python audit_property.py
run "fuzz(단발·전장)"          python audit_fuzz.py --mode all
run "pairwise(단발·전장·캠페인)" python audit_pairwise.py --mode all
run "성능 가드"                python audit_perf.py

# 종합 요약을 파일 맨 위에 — 브리핑이 첫 줄만 봐도 FAIL 여부 판단
{
    echo "==== 야간 감사 $(date '+%Y-%m-%d %H:%M:%S') ===="
    if [ "${#FAILS[@]}" -eq 0 ]; then
        echo "종합: ✅ 전부 PASS"
    else
        echo "종합: ❌ FAIL ${#FAILS[@]}건 — ${FAILS[*]}"
    fi
    cat "$BODY"
} >> "$LOG"
rm -f "$BODY"

[ "${#FAILS[@]}" -eq 0 ]
