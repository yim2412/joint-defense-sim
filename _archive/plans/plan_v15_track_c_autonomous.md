# 설계 — 트랙 C 함정별 자율 교전 (v15.3) · 지휘 강건성 중심

정본: [[plan_v15_unmanned_autonomy]] 트랙 C. v15 무인·자율 블록 마지막.
사용자 합의(2026-07-03): 지휘 강건성 중심 · 단순 ON/OFF · **CEC 저하 기본 도입 + 골든 갱신**.

## 개념 (2모델)

### 1. CEC 지휘 저하 — 기본 동작 개선 (상시 ON, 토글 없음)
현행 CEC는 기함(지휘 노드)이 격침돼도 relay 커버리지가 그대로 유지되는 비현실적 모델.
→ **기함 격침 시 CEC relay 일시 저하 + 차순위 지휘권 인수 지연** 추가.
- 기함(`_primary`) 교체 감지 시 `_cec_degraded_until = t + _CEC_HANDOVER_DELAY_S`(45s).
- 그 구간 CEC relay 중단(자체 탐지 함정만 교전) → 이후 차순위가 지휘 노드 승계, relay 복구.
- **골든 갱신 필요**: 회귀 골든 4케이스 중 기함(KDX-III-B2)이 격침되는 랴오닝-기본·공격+CAP은
  결과가 바뀜(확인됨). 입체포화·잠수함복합은 무영향 예상. 의도된 현실성 개선 → `--update`.

### 2. enable_autonomous_engagement — 실험적 토글 (기본 OFF·3종세트)
ON 시 함대가 **자율 분산 교전**: 각 함정이 CEC 중앙 조율 없이 자기 센서·사거리 내 위협을
독립 교전. relay 없음(협동 엄호 X)이나 **살보는 정상(`_base`)** — cec_jammed의 강제 1발 저하와 구분.
→ CEC 지휘 저하에 **면역**(애초에 relay·지휘 노드 안 씀).
- **트레이드오프**: 평시(기함 생존) = CEC가 우위(relay+협동 살보). 고강도(기함 조기 격침) =
  autonomous가 우위(CEC는 지휘 저하, 자율은 면역). "지휘 강건성" 실측 발현.

## 3-way(+저하) 관계 최종
| 모드 | relay | 살보 | 기함 격침 시 |
|------|-------|------|-------------|
| CEC ON(기본) | O | _base+1 | **relay 저하 45s → 차순위 인수(신규)** |
| CEC jammed | X | 강제 1 | 무관(이미 독립) |
| autonomous(신규) | X | _base | **면역** |

## 수정 파일
- `engine_combat.py`: 상태 2개·저하 감지·`_friendly_defense` cec 분기
- `app_main.py`: 체크박스 3종세트
- `audit_regression_golden.json`: `--update` 재기록

## 핵심 변경 (engine_combat.py)
1. 모듈 상수 `_CEC_HANDOVER_DELAY_S = 45.0`
2. `__init__` 상태: `self._cec_degraded_until = 0.0` · `self._prev_primary_id = None` · `self._command_handovers = 0`
3. `_friendly_defense` 진입부 — 기존 `cec` 계산 대체:
```python
autonomous = self.cfg.get('enable_autonomous_engagement', False)
cec_jammed = self.cfg.get('enable_cec_jammed', False)
cec_base   = self.cfg.get('enable_cec', self.cfg.get('enable_cec_preassign', True)) and not cec_jammed
cur_primary = self._primary()
if self._prev_primary_id is not None and id(cur_primary) != self._prev_primary_id:
    self._command_handovers += 1
    if cec_base and not autonomous:
        self._cec_degraded_until = self.t + _CEC_HANDOVER_DELAY_S
        if not self._mc_mode:
            self._log(f"⚠[지휘권 인수] 기함 격침 — CEC 지휘 저하 {_CEC_HANDOVER_DELAY_S:.0f}s")
self._prev_primary_id = id(cur_primary)
if autonomous:
    cec = False                                   # 자율 분산 (relay X, 살보 _base 유지)
elif cec_base and self.t < self._cec_degraded_until:
    cec = False                                   # 지휘 인수 중 relay 저하
else:
    cec = cec_base
```
- `layered`는 현행 유지(`enable_layered_defense and not cec_jammed`) — autonomous도 중앙 우선순위 배정은 유지, relay만 제거(최소 침습). `max_sams`: cec_jammed면 1, 그 외 `_base + (1 if cec else 0)` → autonomous는 cec=False라 _base(✓ cec_jammed와 구분).

## 하위호환·회귀
- autonomous OFF·기함 생존 시: 완전 현행(저하 미발동). 
- autonomous OFF·기함 격침 시: **CEC 저하 발동(신규 기본 동작)** → 골든 갱신.
- autonomous ON: OFF bit-identical 아님(신기능) — 골든은 OFF 기준이라 무관.
- 신규 DB·stats 키 없음(`_command_handovers`는 인스턴스 카운터·로그/probe용, stats dict 미포함 → MC 3경로 불요).

## 검증
1. 변경 전 회귀 PASS 확인 → 변경 후: 기함 격침 케이스 FAIL 예상 → 의도 확인 후 `--update`.
2. 4조합(cec × autonomous) 동작·NaN 점검.
3. 단위검증 `_autonomy_probe.py`: 고강도서 기함 격침 → 지휘권 인수 로그·저하 발동 확인 + autonomous ON 면역 확인.
4. ON/OFF 기준값(고강도=입체포화·전면전 포화, 기함 격침 잦은): autonomous ON이 OFF 대비 우위 발현? 기준값 메모리 `project-baseline-autonomous`.
5. **코드리뷰 high**(가장 침습적).

## 버전 / 체크리스트
- 번호 **v16.12.04**(트랙 C 예약분).
- 헤더·APP_VERSION·changelog·_changelog_export·_PLANS(v15.3 삭제)·빌드·스모크·push.
- 모델 Opus·리뷰 high.
