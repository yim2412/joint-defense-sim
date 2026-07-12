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
| 연안 SAM 포대 | **v18 `EnemyADSite`**(고정·불침·저하/복구 상태) · 전술 어쇼어 SM-3/THAAD 요격 골격 | 아군판 `CoastalSAMSite` + **천궁-II/L-SAM 신규 요격 자산**(전술 `_bmd_asset_fire` 확장) |
| 상륙 임무체인 | **v19.5 CAS 임무체인**(요청→배정→효과) | 수송→엄호→상륙 3단계 |
| 상륙군 부대 | **v18 `CampaignShip` 상태머신**(대기·이동·수리) 복제 | 적재/상륙/교두보 상태 |
| 도미노 연동 | **v19 제공권→SLOC 피드백** 구조 | 지상방공 상실→제공권↓ 경로 |
| ASBM 위협 | 기존 DF-21D(대함탄도탄) ENEMY_DB | 연안 SAM 요격 대상 편입 |

---

## 4. 하위 단계 설계 (권장 착수 순서 = 가치·재사용·위험 기준)

> 로드맵 번호는 v20.1→v20.4이나, **실제 착수는 v20.2(연안방공)를 먼저** — 해·공과 진짜 연결고리이고
> v18 인프라 재사용이 커 위험이 낮다. v20.1(전력 DB·기동)은 매우 높음·위험 큼이라 **대폭 축소 후 후순위**.

### v20.2 연안 방공망 (착수 1순위·핵심) — 난이도 높음
> **⚠ 범위 확대(사용자 결정 2026-07-12): 천궁-II/L-SAM 신규 추가.** 전술 엔진 어쇼어 자산이
> 현재 **SM-3(이지스 어쇼어)+THAAD 2종뿐**임을 코드 확인 → 한국형 BMD 하위/상위 계층을 **신규 요격
> 로직으로 도입**해 4계층 방어로. 정확도 우선(사용자 "성능보다 확실"), 단 새 물리라 재사용 원칙 일부 완화.

**v20.2 두 부분으로 분할(위험 통제):**

**v20.2a — 어쇼어 BMD 계층 확장(전술 엔진)** — 난이도 높음
- 전술 엔진 `_bmd_asset_fire`/`_ashore_defense`에 **천궁-II(KM-SAM II)·L-SAM** 신규 요격 자산 추가
  (기존 owner_id −1=SM-3·−2=THAAD → −3=L-SAM·−4=천궁-II 확장). 각 자산 제원(pk·사거리·고도 envelope·
  비용·쿨다운·재고 cfg 키)을 **공개 제원 기준 신설**(DB 현실성 감사 대상).
  - 계층: L-SAM=상층(~150km·고고도, THAAD급 한국형) · 천궁-II=하층 종말 점방어(~40km).
  - `enable_ashore` 기존 플래그 확장 or 별도 stock(lsam_stock·chungung_stock) — 3종세트 불필요(어쇼어
    자산 재고는 스핀박스/스탯, enable 토글 아님). **회귀: 신규 자산 stock=0 기본 → 기존 골든 bit-identical.**
- **🟢 추가 재사용(검토 발견)**: 천궁-II/L-SAM을 **`is_shore_battery`(CSAM 계열) 해안 포대 타입**으로
  넣으면 고정·불침·HP 저하·회피없음이 공짜 → **정밀 교전에서 적이 해안 포대를 때려 HP 저하하는 게 자동**.
- **이 단계는 전술 단발/전장에서 바로 검증 가능**(캠페인 무관) — 회귀 골든에 천궁-II/L-SAM 발현 케이스 추가.

**v20.2b — 연안 방공 캠페인 층** — 난이도 높음
- `CoastalSAMSite`: zone별 고정 포대. 자산 로스터 = {SM-3, THAAD, **L-SAM, 천궁-II**} 중 편성.
- **ASBM 요격 = 전술엔진 정밀 전면**: ASBM(is_qbm·is_ballistic + 대함, 예 DF-21D) 위협이 있는 zone
  교전은 확률 가산이 아니라 **항상 전술 단발(run_v7_simulation)로 정밀 해결**. CoastalSAMSite를 전술
  tcfg에 어쇼어 자산(enable_ashore + 각 stock)으로 주입 → v20.2a의 요격 로직으로 실측.
- **정밀 라우팅 트리거(_tick_engagements)**: `(적 규모≥3) OR (zone에 ASBM 위협 AND CoastalSAMSite 존재)`
  이면 `_resolve_precise`. ASBM 있어도 연안 SAM 없으면 정밀 강제 무의미(함대 자체 방어만) → proxy 유지.
- **재고 추적**: CoastalSAMSite.stock을 캠페인 틱 간 유지 → 정밀 교전마다 tcfg stock으로 주입,
  전술 결과의 발사 수만큼 차감(CampaignShip.ammo 패턴). 소진 시 방어 저하.
- **배치 설정(UI)**: zone별 연안 SAM 편성을 사용자가 지정(함대 프리셋과 동일 패턴 — 기본 프리셋
  '연안 방공 강화' 제공 + 직접 편성). 미배치 zone은 CoastalSAMSite 없음(순수 함대 방어).
- ASBM 없는 통상 교전은 기존 즉시예측/정밀 하이브리드(A1) 유지.

**성능 경계(주의)**: ASBM+연안SAM zone은 항상 정밀 → MC n=1000 × ASBM 교전 수만큼 전술 단발 추가.
72h 전역서 ASBM 교전 1~3회 가정 시 MC당 +1~3 정밀 sim → E1 병렬 필수(이미 있음). 착수 시 wall-time 측정.

### v20.3 해상 상륙작전 지원 (착수 2순위·핵심) — 난이도 높음
- `AmphibiousForce`: LPH(독도함)/LPD/LST(기존 SHIP_DB 재사용)에 적재→목표 해안 이동→**교두보 확보**.
- **3단계 임무체인 + 순차 곱연산(로드맵 지침)**: `수송(transit)` → `항공 엄호(air cover)` → `상륙(assault)`.
  각 단계 성공 확률을 캠페인 상태에서 도출해 **곱**:
  - P(수송) = f(해당 zone SLOC 통제도) — 교통로 뚫려야 상륙함 도달.
  - P(엄호) = f(zone 제공권, v19 air) — 제공권 있어야 상륙 항공 엄호.
  - P(상륙) = f(호위 함대 함포지원 + 적 연안 방어 강도) — 대안(opposed landing).
  - 교두보 확보 = ∏ 단계확률 ≥ 임계 → 성공. 상태머신 embark→transit→assault→beachhead.
- v19.5 CAS 임무체인(요청→배정→효과) 구조 재사용. 상륙 성공/실패가 캠페인 outcome에 가중 반영
  (가중치 = 미결, 기준값 측정 후 튜닝).

### v20.4 지상군 캠페인 통합 (착수 3순위) — 난이도 중간
- **도미노의 실체 = 적 SEAD가 아군 연안 SAM을 전략 제압**: `CoastalSAMSite.suppression`을 적 SEAD
  소티로 증가(v19.3 아군 SEAD→EnemyADSite 제압의 **정확한 거울**, 결정론·rng 불사용, 제압 상한·복구 재사용).
  effective 방공 = assets × (1-suppression) → 연안 SAM 저하 → **제공권↓ → SLOC 압박** 연쇄
  (v19 제공권→SLOC 피드백 확장). **이게 로드맵 "지상방공 상실→제공권→해상 교통로 도미노"의 실체.**
- 보고서에 지상 임무 타임라인 추가.
- (v20.2b의 CoastalSAMSite는 suppression=0 정적 방어 자산 → v20.4에서 동적 제압으로 살아남).

### v20.1 지상군 전력 DB & 기동 (착수 최후·대폭 축소) — 난이도 매우 높음
- **전면 지상 기동전은 보류.** v20.2·v20.3에 필요한 **최소 전력 DB**(연안 SAM 기종·상륙군 부대)만.
- K2·K9 등 전차·자주포 제원은 **도입 보류**(해전 시뮬 본령 밖, 범위 과대).

---

## 5. 데이터 구조 (engine_army.py 신규)

```
class CoastalSAMSite:   # 연안 고정 방공 포대 (불침·기동 없음)
    name, zone,
    assets: dict         # {'SM-3': stock, 'THAAD': stock, 'L-SAM': stock, '천궁-II': stock}
                         #  (v20.2a 신규 L-SAM/천궁-II 포함 4계층) → 정밀 교전 tcfg 주입
    # 정밀 교전 실측 발사 수만큼 assets stock 차감(캠페인 틱 간 유지, CampaignShip.ammo 패턴)
    # ── v20.4 도미노 전용(v20.2엔 미사용) ──
    suppression, recovery_h  # 적 SEAD 제압도 0~1·복구(v19 EnemyADSite 거울, deterministic)
                             #  effective = assets × (1-suppression). v20.2는 suppression=0 고정.

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
- **ASBM 요격 = 전술엔진 정밀 전면**: DF-21D(is_qbm·is_ballistic+대함) 위협 zone 교전은 항상 전술
  단발로 정밀 해결(확률 추상화 아님). 무겁지만 정확도 우선(사용자 "성능보다 확실·실수 없이").
- **요격 자산 = 천궁-II/L-SAM 신규 추가**(사용자 결정 2026-07-12): 전술 엔진 어쇼어가 SM-3+THAAD
  2종뿐임을 코드 확인 → 한국형 BMD 하위(천궁-II)·상위(L-SAM) 계층을 **신규 요격 로직으로 도입**해
  4계층. 재사용 원칙 일부 완화(새 물리)하되 v20.2를 **a(전술 엔진 계층 확장)+b(캠페인 층)로 분할**해
  위험 통제. 신규 자산 stock=0 기본 → 기존 골든 bit-identical.

**남은 미결(착수 시점 확정):**
- **천궁-II·L-SAM 공개 제원 확정**: pk·사거리·고도 envelope·비용 = v20.2a 착수 시 공개 출처 대조
  ([[project-db-realism]]). 개략: 천궁-II ~40km/저고도 종말 · L-SAM ~150km/고고도(THAAD급 한국형).
- **상륙 실패의 outcome 가중**: 상륙 실패가 전역 패배에 얼마나 기여할지 = 기준값 측정 후 튜닝(v20.3).
- **난이도·에포트**: 새 엔진 + 신규 요격 자산 = **매우 높음 → Opus/high**. v20.2a→b 순차.

---

## 9. 착수 요약 (다음 세션 재개점)

1. **v20.2a 어쇼어 BMD 계층 확장부터** (전술 엔진에 천궁-II·L-SAM 신규 요격 자산 — 캠페인 무관,
   전술 단발/전장서 바로 검증). DB 현실성(공개 제원)·회귀 골든 신규 케이스·신규 자산 stock=0 기본 bit-identical.
2. → **v20.2b 연안 방공 캠페인 층**: `engine_army.py` 신설 + `CoastalSAMSite`(4계층 자산) +
   `enable_army_campaign`·`enable_coastal_sam` 3종세트 + 캠페인 접합 + **ASBM-정밀 라우팅**(트리거·재고추적).
3. → v20.3 상륙지원(LPH/LPD/LST 재사용+교두보) → v20.4 도미노 통합 → v20.1 최소 전력 DB(대폭 축소).
4. 각 단계 회귀 bit-identical(OFF/stock0)·code-review high·GUI 스모크(신규 `_audit_army_smoke.py`)·DB 현실성·기준값.
5. **major 전환(v19→v20)이므로 블록 완료 시 종합 9영역 감사** 트리거.

> 이 문서는 **설계(Phase 0)** — 구현 착수 전. 착수 시 8절 미결을 사용자와 합의 후 v20.2부터.
