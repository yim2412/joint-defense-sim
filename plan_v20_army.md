# v20 지상군 작전급 — 설계 문서 (Phase 0, 착수 전)

> v18 **해군 작전급 캠페인**(72h 전역·1h 틱·교전 즉시예측) + v19 **공군 작전 층**(제공권 격자) 위에
> **지상군 작전 층**을 얹는다. 핵심 가치 = **연안 방공망·상륙작전이 해상 교통로(SLOC) 통제와 연동**.
> 정본 = 이 문서. `_PLANS`가 버전 정본(로드맵_상세 문서는 이 계열을 'v19 육군'으로 표기 = 한 칸 stale, [[project-airforce-campaign]] 매핑과 동일).

---

## 0. 아키텍처 결정 (v18·v19 철학 계승)

- **별도 `engine_army.py`** — 지상군 전용 자료구조·틱 로직. `engine_campaign.CampaignEngine`이 import해
  **얇은 접합**(compose)으로 지상 틱을 호출. v18이 engine_combat를, v19가 engine_airforce를 무수정
  조합한 방식 그대로. **전술 엔진(engine_combat) 무수정** 유지 → 단발·전장 회귀 bit-identical.
- **`enable_army_campaign` 3종세트 기본 OFF·실험적**. OFF면 v19 캠페인과 **bit-identical**(지상 층 미활성).
  하위 옵션 `enable_coastal_sam`·`enable_amphibious`도 army_campaign 종속.
- **범위 = 로드맵 지침대로 대폭 축소**: 전면 지상전은 **별 프로젝트로 보류**. 해상작전 시뮬의
  **접점(연안 방공·상륙·교두보)만** 최소 단위로. 지형 기동 모델·전차 교전은 도입하지 않는다.

---

## 1. 목적 · 배경

현재 캠페인(v18+v19)은 **해군·공군 자산**만 다룬다. 실제 해상 작전은 연안 지상 자산과 밀결합:
- 연안 방공 포대(패트리엇·천궁)가 함대 상공·대함탄도탄(DF-21D)을 방어 — **해군의 우산**.
- 상륙작전은 해·공·지상 3군 협조(수송→항공 엄호→교두보 확보)의 정점.
지상 층을 얹어 ▸연안 SAM이 함대 방공·ASBM 요격에 기여 ▸상륙작전을 작전급 임무체인으로 운용
▸지상 방공 상실이 도미노(제공권↓→SLOC 압박)로 캠페인 전체에 파급.

---

## 2. 범위 · 끝 상태

- **별도 `engine_army.py`** — `ArmyPool`·`CoastalSAMSite`·`AmphibiousForce`. CampaignEngine이 조합.
- 지상 자산 = **연안 고정 포대(불침·기동 없음)** + **상륙군 부대(수송함에 적재→해안 상륙)** 최소 단위.
  전차·야포·지상 기동전은 **범위 밖**(해전 본령 아님).
- `enable_army_campaign` OFF → v19 bit-identical. ON → 지상 층이 SLOC·제공권·교전에 연동.

---

## 3. 재사용 vs 신규 (재사용 최대화 — 위험 축소)

| 요소 | 재사용 원천 | 신규 |
|------|-------------|------|
| 연안 SAM 포대 | **v18 `EnemyADSite`**(적 방공)·**v16 C-RAM 해안 포대**(고정·불침) | 아군판 `CoastalSAMSite`(ASBM 요격 특화) |
| 상륙 임무체인 | **v19.5 CAS 임무체인**(요청→배정→효과) | 수송→엄호→상륙 3단계 |
| 상륙군 부대 | **v18 `CampaignShip` 상태머신**(대기·이동·수리) 복제 | 적재/상륙/교두보 상태 |
| 도미노 연동 | **v19 제공권→SLOC 피드백** 구조 | 지상방공 상실→제공권↓ 경로 |
| ASBM 위협 | 기존 DF-21D(대함탄도탄) ENEMY_DB | 연안 SAM 요격 대상 편입 |

---

## 4. 하위 단계 설계 (권장 착수 순서 = 가치·재사용·위험 기준)

> 로드맵 번호는 v20.1→v20.4이나, **실제 착수는 v20.2(연안방공)를 먼저** — 해·공과 진짜 연결고리이고
> v18 인프라 재사용이 커 위험이 낮다. v20.1(전력 DB·기동)은 매우 높음·위험 큼이라 **대폭 축소 후 후순위**.

### v20.2 연안 방공망 (착수 1순위·핵심) — 난이도 높음
- `CoastalSAMSite`(패트리엇·천궁): zone별 고정 포대, 함대 상공 방공 커버리지 + **DF-21D 대함탄도탄 요격**.
- **ASBM 요격 = 전술엔진 정밀 전면(사용자 결정 2026-07-12)**: ASBM(DF-21D 등) 위협이 있는 zone 교전은
  확률 가산이 아니라 **항상 전술 단발(run_v7_simulation)로 정밀 해결**한다. CoastalSAMSite를 전술 엔진의
  **기존 연안 SAM 포대(ashore SM-3/THAAD/천궁, v13 지상 BMD 자산)로 매핑** — 새 탄도 물리 모델 없이
  검증된 요격 로직 재사용. 무거워지지만(해당 교전 항상 정밀) 정확도 우선(사용자 방침 "성능보다 확실").
- ASBM 없는 통상 교전은 기존 즉시예측/정밀 하이브리드(A1) 유지.
- v18 EnemyADSite(적 방공 대칭)·전술 ashore SAM 재사용. **이게 v20의 핵심 가치.**

### v20.3 해상 상륙작전 지원 (착수 2순위·핵심) — 난이도 높음
- `AmphibiousForce`: 독도함 등 상륙함에 적재→목표 해안 이동→**교두보 확보** 임무체인(수송→항공 엄호→상륙).
- v19.5 CAS 임무체인 구조 재사용. 상륙 성공/실패가 캠페인 outcome에 반영.

### v20.4 지상군 캠페인 통합 (착수 3순위) — 난이도 중간
- 도미노 연쇄: **지상방공 상실 → 제공권↓ → SLOC 압박**(v19 제공권→SLOC 피드백 확장).
- 보고서에 지상 임무 타임라인 추가.

### v20.1 지상군 전력 DB & 기동 (착수 최후·대폭 축소) — 난이도 매우 높음
- **전면 지상 기동전은 보류.** v20.2·v20.3에 필요한 **최소 전력 DB**(연안 SAM 기종·상륙군 부대)만.
- K2·K9 등 전차·자주포 제원은 **도입 보류**(해전 시뮬 본령 밖, 범위 과대).

---

## 5. 데이터 구조 (engine_army.py 신규)

```
class CoastalSAMSite:   # 연안 고정 방공 포대 (불침·기동 없음)
    name, zone, sam_type('패트리엇'|'천궁'), coverage_km, intercept_pk,
    asbm_capable(bool)   # DF-21D 대함탄도탄 요격 가능 여부
    strength, recovery_h # 피격 시 저하·복구 (v18 EnemyADSite 대칭)

class AmphibiousForce:  # 상륙군 부대 (v18 CampaignShip 상태머신 복제)
    name, state('embark'|'transit'|'assault'|'beachhead'), zone,
    troops, transport_ship, progress   # 교두보 확보 진척

class ArmyCampaign:     # 얇은 접합 진입점 (v19 AirCampaign 대칭)
    def __init__(cfg): ...
    def tick(zone_threats, air_sups): ...   # 1h 틱
    def zone_defense_bonus(zone) -> float:  # 연안 SAM 방공 가산 (교전 즉시예측에 연동)
    def amphibious_status() -> dict:        # 상륙 진척 (보고서·outcome)
```

---

## 6. 캠페인 접합 (engine_campaign.py — v19 공군 접합과 동형)

```
# CampaignEngine.__init__: enable_army_campaign ON일 때만 생성(OFF면 v19 bit-identical)
self.army = None
if bool(cfg.get('enable_army_campaign', False)):
    from engine_army import ArmyCampaign
    self.army = ArmyCampaign(self.cfg)

# _tick_*: 지상 틱 호출 + zone 방공 가산 연동
if self.army is not None:
    self.army.tick(zone_threats, air_sups)
    # 통상 교전: self.army.zone_defense_bonus(zone) 가산(즉시예측)
    # ASBM 위협 zone: 전술엔진 정밀 강제 — _resolve_precise 경로에 CoastalSAMSite를
    #   기존 어쇼어 SAM 지원(tcfg['enable_ashore']=True + ashore_sm3_stock/천궁 제원)으로
    #   주입해 _ashore_defense()의 SM-3/THAAD 요격을 실측(검증된 로직 재사용, 새 물리 X).
```

---

## 7. 검증 계획 (각 마이너)

- **회귀**: enable_army_campaign OFF → v19 캠페인 bit-identical (신규 골든 케이스 = army ON 결정론 봉인).
- **code-review high** + **GUI 스모크 신설**(`_audit_army_smoke.py` — 지상 토글 ON→상륙/연안방공 배너 확인).
  새 실행 모드마다 전용 스모크 규칙([[feedback-smoke-run]]) 준수.
- **DB 현실성**(②): 패트리엇/천궁/독도함 제원 공개값 대조([[project-db-realism]]).
- **기준값 측정**: 연안 SAM ON/OFF ASBM 요격률·상륙 성공률 baseline → project-baseline 메모리.
- **3종세트 자동검사**: enable_army_campaign·enable_coastal_sam·enable_amphibious를 audit_static_scan
  chk_flag_triplet에 소비처 명시 등록(engine_army/engine_campaign).

---

## 8. 결정 사항 · 남은 미결 (2026-07-12 사용자 합의)

**✅ 결정됨:**
- **지형 기동 = 배제 확정**: 연안 고정 포대 + 상륙 임무체인만(기동 없음). 전차·야포 지상 기동전은
  별 프로젝트로 보류 — 범위·위험 통제(로드맵 권고 + 사용자 선택).
- **ASBM 요격 = 전술엔진 정밀 전면**: DF-21D 위협 zone 교전은 항상 전술 단발로 정밀 해결(확률 추상화
  아님). CoastalSAMSite→전술 ashore SAM(SM-3/THAAD/천궁) 매핑으로 **기존 검증 로직 재사용**(새 물리 X).
  무겁지만 정확도 우선(사용자 "성능보다 확실·실수 없이"). 4·5·6절에 반영.

**남은 미결(v20.2 착수 시점 확정):**
- **상륙 실패의 outcome 가중**: 상륙 실패가 전역 패배에 얼마나 기여할지 = 기준값 측정 후 튜닝(v20.3).
- **난이도·에포트**: 새 엔진 설계 = **매우 높음 → Opus/high**. v20.2부터 마이너 1개씩 순차.

---

## 9. 착수 요약 (다음 세션 재개점)

1. **v20.2 연안 방공망**부터 (핵심·재사용 큼·낮은 위험). `engine_army.py` 신설 + `CoastalSAMSite` +
   `enable_army_campaign`·`enable_coastal_sam` 3종세트 + 캠페인 접합(zone 방공 가산).
2. → v20.3 상륙지원 → v20.4 도미노 통합 → v20.1 최소 전력 DB(대폭 축소).
3. 각 단계 회귀 bit-identical(OFF)·code-review high·GUI 스모크·DB 현실성·기준값.
4. **major 전환(v19→v20)이므로 블록 완료 시 종합 9영역 감사** 트리거.

> 이 문서는 **설계(Phase 0)** — 구현 착수 전. 착수 시 8절 미결을 사용자와 합의 후 v20.2부터.
