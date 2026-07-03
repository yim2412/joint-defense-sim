# v17.1 — 지속 전장 RAS 탄약 재보급 설계

> **상태**: 설계 확정(2026-07-03), 구현 대기(다음 세션). 정본.
> **버전 예정**: v16.13.05 계열 or v17.01.01 (구현 착수 시 결정 — major 전환은 지속 전장 갈래B 컷오버 시점이므로 v17.1도 당분간 v16.13 계열 seq 가능. 착수 시 단조·README 정합 우선).

## 배경 — 설계 전 진단 (왜 이 범위인가)

exe `_PLANS` v17.1 = "보급·병참 지속성". 착수 전 진단에서 **상당 부분이 이미 지속 전장(BattleEngine)에 구현**돼 있음을 확인:
- ✅ 연료 모델(`fuel`/`_fuel_burn_per_s`/회피 추가소모/원자력 무제한)
- ✅ 해상급유 RAS(`_ras_update`, 군수지원함 AOE·AO `ras_reserve` 화물 연료 — v15.09.03)
- ✅ 탄약 재장전 쿨다운(`_reload_delay`), 탄약 유한화(`enable_munition_limit`), VLS 소진 경고(`vls_depletion_t`)

그리고 `로드맵_상세_v11-v20.md`가 **"군수·보급은 전술급 700초엔 무의미, 캠페인(작전급)에서 진가, 독립 전술 기능 효용 낮음"** 명시.

**→ 결론(사용자 확정)**: 전술급 신규 보급 모델은 저ROI(Phase 1 편성 규모화와 동형 함정). 대신 **유일한 실질 공백 = "RAS가 연료만 보급, 탄약(VLS 미사일) 재보급 없음"**을 채운다. 지속 전장 전용, 기존 RAS 인프라 재활용.

## 콘셉트

장기 전장에서 군수지원함(AOE·AO)이 **소강기에** 전투함의 소진된 주요 SAM을 재장전 → 지속 전장에 **"재고 소진 → 재보급" 트레이드오프**가 생긴다. 격전 중엔 불가(위협 접근 시 중단), 화물 유한(무한 아님).

## 수정 파일

| 파일 | 변경 |
|------|------|
| `engine_combat.py` | RAS 로직 확장(`_ras_update`)·함정 초기재고 저장·지원함 탄약 화물·플래그 로드·stats 키 |
| `app_main.py` | `enable_ras_rearm` 3종세트(체크박스 + cfg 빌드 `isChecked()` + `_restore_cfg` `hasattr`) + stats 키 MC 3경로 |

새 DB 항목 없음 → `db_specsheet.py` 무관.

## 핵심 변경 (engine_combat.py)

### 새 상수 (RAS 연료 상수 `_RAS_RESERVE` 옆)
```python
_RAS_AMMO_RESERVE  = {'AOE': 40, 'AO': 15}   # 지원함 탄약 화물(재보급 가능 주요 SAM 발수)
_RAS_REARM_PER_S   = 0.05                     # 초당 재보급 속도(느림 — VERTREP/CONREP 반영)
_RAS_REARM_TRIGGER = 0.30                     # 주요 SAM 합이 초기 재고의 30% 미만인 함정만 대상
_RAS_REARM_TARGET  = 0.80                     # 초기 재고의 80%까지만 보충(완전 만재 안 함)
```

### 함정 초기화 (`_build_friendly` 또는 FriendlyShipObj __init__ 재고 확정 직후)
- 전투함: `s._initial_defense_stock = dict(s.inventory)` — 재보급 상한·트리거 기준(발사로 줄어드는 `s.inventory`와 별개 고정본)
- 지원함: `s.ras_ammo_reserve = _RAS_AMMO_RESERVE.get(s.type_or_class, 0.0)` — 연료 `ras_reserve`와 **별도** 화물

> 주의: 초기 재고 저장은 **항상**(플래그 무관) 해도 무해(bit-identical). `ras_ammo_reserve`도 기본 0이면 무영향. 단 안전히 플래그 게이트 안에서만 소비.

### `_ras_update` 확장 — 연료 급유 블록 뒤에 탄약 재보급 블록
```python
# (기존 연료 급유 로직 끝)
if not self._ras_rearm:          # cfg.get('enable_ras_rearm', False)
    return
suppliers_a = [s for s in self.friendly_ships if s.alive and s.ras_ammo_reserve > 0.0]
if not suppliers_a:
    return
_MAJOR = ('SM-3 Block IIA', 'SM-6', 'SM-2 Block IIIB')
def _sam_frac(s):
    init = sum(s._initial_defense_stock.get(w, 0) for w in _MAJOR)
    cur  = sum(s.inventory.get(w, 0) for w in _MAJOR)
    return (cur / init) if init > 0 else 1.0
needy = sorted(
    (s for s in self.friendly_ships
     if s.alive and _sam_frac(s) < _RAS_REARM_TRIGGER),
    key=_sam_frac)
for sup in suppliers_a:
    for s in needy[:_RAS_STATIONS]:
        # 가장 소진된 주요 SAM부터 초기 80%까지, 초당 속도·화물 한도 내로 재장전
        # (float 누적 → 정수 발수 변환: s._rearm_acc 컬럼에 누적 후 1.0 넘으면 1발 지급)
        ...  # 부족 무기 선택 → 지급 → sup.ras_ammo_reserve -= 지급, stats 누적
```

### stats 키 (선택 확정 = 추가함)
- `ras_missiles_resupplied` — 재보급된 총 SAM 발수. `_compile()` 반환에 추가 + **MC 3경로 동시 추가 필수**(`monte_carlo_v7`·`_mc_batch_worker`·`monte_carlo_lhs`). 효과 측정·향후 쇼케이스 카드용.

## 트레이드오프 (현실성)
- 재보급 중 위협(적 대함미사일) 접근 시 중단 — 기존 연료 RAS와 조건 공유(`_ras_update` 진입부 `return`). 격전 중 재장전 불가.
- 화물 유한(`ras_ammo_reserve`) → 장기전서 결국 소진. 무한 재보급 아님.
- 느린 속도 → 격전 중엔 못 채우고 **소강기에만** 발동.

## 의존성·하위호환
- `enable_ras_rearm` **3종세트·기본 OFF·실험적** → **회귀 bit-identical**. 플래그명 이후 변경 금지(저장 시나리오 호환).
- **BattleEngine 전용** — 부모(단발 TimeStepEngine)는 `ras_ammo_reserve` 미설정(0)·플래그 OFF → 완전 무영향. 부모 `_ras_update`가 없으면 BattleEngine에만 존재(단발엔 RAS 자체가 지속 전장 기능).
- 새 stats `ras_missiles_resupplied`는 MC 3경로 없으면 MC 모드서 소실 → 반드시 3경로 동시.
- `_id_counter`·`normalize_enemy_db` 무관(적 DB 무변경).

## 검증 계획
1. **회귀**: `audit_verify_regression.py` PASS (OFF bit-identical — 8케이스 단발이라 자동 무영향, 그래도 확인).
2. **ON/OFF 기준값**: 지속 전장(전면전 포화 등 장기 소모전) 모드로 MC — 재고 소진→재보급 발동 확인, 아군 생존·작전 지속성 지표 ON/OFF 델타. 기준값 `project-baseline-ras-rearm` 메모리 보존.
3. **단위 검증**: 소강기 재보급 발동 로그·화물 소진·정수 발수 변환 정확성(float 누적).
4. **코드 감사**: `/code-review medium`(엔진 로직 추가) + 정적 스캔 3종세트.
5. **빌드 + GUI 스모크**.

## 구현 체크리스트 (신기능 8항목)
- [ ] `enable_ras_rearm` 3종세트 (체크박스·cfg빌드·_restore_cfg)
- [ ] stats `ras_missiles_resupplied` MC 3경로
- [ ] 신규 심볼 app_main import 불요(엔진 내부) — 확인만
- [ ] 새 클래스 없음 → `_id_counter` 무관
- [ ] 죽은 코드 없음 (호출처 = `_ras_update`)
- [ ] `s._initial_defense_stock`·`ras_ammo_reserve` 초기화 위치 정확
- [ ] float 누적 → 정수 발수 변환 (재고 반개 방지)
- [ ] BattleEngine 전용 게이트 (단발 무영향)

## 미결(구현 시 판단)
- 재보급 대상 = **주요 SAM(SM-3/6/2)만** 확정. RAM·어뢰·공격무기(해성) 제외(복잡·저효용).
- float→정수 변환: `s._rearm_acc` 함정별 누적 컬럼 방식(초당 0.05씩 누적, 1.0 넘으면 1발 + `-=1.0`).
- 지원함 화물 수치(AOE 40·AO 15)는 구현 후 ON/OFF 측정으로 튜닝(장기전서 유의미하되 무한 아니게).
