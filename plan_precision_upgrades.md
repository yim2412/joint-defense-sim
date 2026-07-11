# 계획: 정밀화 개선 백로그 (성능 ↔ 정확도 트레이드오프)

> **목적**: "무거운 대신 조금이라도 더 정확·현실적"인 개선을 전수 수집한 백로그(2026-07-10 사용자
> 요청). 각 항목은 성능·복잡도를 더 쓰고 정확도/현실성을 얻는다. **지금 실행이 아니라 우선순위
> 판단용 목록** — v20 지상군·B(CAP) 등과 함께 순서를 정한다.
>
> **원칙**: ▸작전급(캠페인·공군)은 **추상이 설계 의도** — 무겁게 만들 땐 "설계 철학 역행 아닌지"
> 먼저 확인. ▸전술급(engine_combat)은 이미 정밀 → 여지 작음. ▸각 개선은 회귀 골든 갱신·기준값
> 재측정을 동반(대부분 밸런스/수치 변화). ▸**제외(개선이 역효과)**: B1 제공권 격자 촘촘화("없는
> 정밀도" 생성)·D1 평면거리→haversine(오차 <0.1%인데 성능만 손해).

---

## ⭐ 높음 (유일한 "확실히 더 좋은")

### A1 — 캠페인 교전을 정밀 전술 엔진으로 해결
- **현재**: `_predict_engagement`가 학습 대리모델(`forecast_model`)로 교전을 ~ms에 근사.
  **함정 손실 수를 아예 추정 못 함**(engine_campaign.py:454) → 승패 score로 "추상 피해"만.
- **개선**: 교전마다 `run_battle_simulation`(시간스텝 전술 시뮬)을 실제 실행 → 손실·무기 소모·
  요격을 진짜 계산. 전장 엔진은 이미 완성돼 있어 **연결만** 하면 됨.
- **이득**: 캠페인 결과가 근사가 아닌 실제 전술 결과 기반. 손실·비용·SLOC 정확.
- **무게**: 전역 1회 수초 → 수분~수십분(교전 수 × 전술 시뮬).
- **설계 포인트**: **하이브리드** — 핵심/대규모 교전만 정밀, 소규모는 대리모델 유지(성능 예산제).
  이걸로 A2(탄약)·A6(함정 상태)·E1(병렬)이 자연 해결/필수화됨.
- **의존**: E1(병렬 MC) 사실상 필수. A2·A6 흡수.

#### ✅ 확정 설계 (2026-07-12, 조사 완료 — 하이브리드 + A1 코어 먼저)

**교전 해결기 = `run_v7_simulation`(단발 교전), NOT `run_battle_simulation`.**
캠페인 zone 1틱 교전 = 단발 교전 1회에 해당. `run_battle_simulation`(지속 전장)은 캠페인이
이미 작전급 상위 레이어라 중첩이 부적절 — plan 본문의 "전술 시뮬"은 단발이 의미상 정확.

**cfg 매핑 (캠페인 → 전술, `_tick_engagements`의 정밀 분기)**:
- `tcfg = dict(self.cfg)` (weather 등 상속) → **캠페인 전용 플래그 제거**
  (`enable_campaign_mode`·`enable_air_campaign`·`enable_battle_mode`)로 라우터 오염 방지.
- 아군: `tcfg['fleet_custom'] = [{'name': f'{st}#{i}', 'type': st} for i,st in patrol]`
  — **name을 유니크(`타입#i`)** 로 (전술 `ship_subsystem_damage` dict 키 충돌 방지, DB조회는 type).
- 적: `tcfg['enemy_fleet_mode']='custom'`; `tcfg['enemy_fleet'] = enemy_fleet`
  — `_active_enemy_in` 반환 `[{preset,count}]`이 전술 `fleet_cfg` 원소 형식과 **정확히 동일**(무변환).
- 결정론: `tcfg['sim_seed'] = hash((campaign_seed, t_h, zone))`; `tcfg['mc_mode']=True`(로그 억제).

**결과 → 캠페인 상태 매핑 (`_apply_engagement` 정밀 분기 — "추상 피해" 제거)**:
- `r['ship_subsystem_damage'][name]['hp']/['max_hp']` → 각 `CampaignShip.hp_frac` **직접 대입**
  (patrol 순서 = fleet_custom 순서 = name `타입#i`로 1:1 매칭). 손실 미추정 완전 해소.
- `r['friendly_ships_lost']`>0 → 해당 함정 `state='repair'`(기존 hp_frac<임계 전환 로직 재사용).
- `cost += r['total_cost']`(실제 요격탄 비용). `won` = 적 격침≥1 && 아군 미전멸(실제 결과 기반).
- ammo: A2 후속(당장은 기존 `_AMMO_PER_ENGAGEMENT` 근사 유지 — 정밀 hp가 핵심 가치).

**하이브리드 임계값**: `enemy_fleet` 총 count ≥ `campaign_precise_min_threats`(기본 3)면 정밀,
미만은 대리모델. 소규모 교전은 대리모델로 성능 절약(성능 예산제의 단순형).

**3종세트 `enable_precise_engagement`**(기본 OFF·실험적): 체크박스 + cfg 빌드 + cfg 로드.
OFF면 `_predict_engagement`+추상피해 경로 그대로 → **bit-identical**(캠페인 회귀 보존).

**범위**: 이번 = A1 코어(단발 캠페인 정밀 교전). E1(병렬 MC)은 다음 마이너 — A1 검증(단발
baseline 측정)으로 "정밀이 실제로 결과를 개선하는가" 먼저 확인 후 병렬로 규모 확대.

**회귀/성능**: OFF bit-identical. ON 단발 캠페인 = 교전 3~9회 × 단발 수백ms ≈ 수초(감당 가능).
MC는 E1 전까지 대리모델 유지 권장(정밀 MC는 병렬 필수).

**알려진 근사 한계(A6에서 해소)**: 정밀 교전은 전술 단발을 매번 full hp에서 시작하므로,
캠페인에서 이미 손상된(hp_frac<1) 함정도 전술상 100% hp로 참전 → 누적 손상이 전술에 반영
안 됨(대리모델도 동일 한계). 실제 손상 함정은 더 빨리 격침돼야 정확. **A6(CampaignShip
물리필드 → 전술 객체 상태 연동)에서 초기 hp 주입으로 해소** — 지금은 부모 무수정 원칙상
run_v7_simulation에 초기 hp 인자가 없어 보류(code-review 2026-07-12 #1).

---

## 중 (현실성·정확도 소폭 개선, 손이 감)

### A2 — 교전당 탄약을 무기별 실제 소모로
- 현재 `_AMMO_PER_ENGAGEMENT=0.28` 고정 추상 → 무기별 실제 소모 집계. A1 하면 자연 해결.
### A4 — 적 전개 스케줄 동적화
- 현재 MVP 고정 웨이브(engine_campaign.py:184) → 교리/시나리오 기반 동적 스케줄(다축·시차).
### B2 — 적 대공위협을 실제 공군 전력 모델로
- 현재 `_BASE_AIR_THREAT=6.0` 상수 추상 → 적 공군 기종·규모 기반 산출(AIR_FORCE_DB 적측 확충 필요).
### C1 — Mk.46 어뢰 실제 제원
- 현재 Mk.48 ADCAP 근사(engine_core.py:1231) → 실제 Mk.46 사거리·속도. DB 현실성.
### C5 — 극초음속 단계별 속도 프로파일
- 현재 평균 `3000m/s` 근사(engine_combat.py:566) → 부스트·활공·종말 단계별 속도(HGV 일부는 v16.2서 이미).
### E1 — 캠페인 MC 병렬화 + 반복 증가
- 현재 단일프로세스 300~1000회 → 멀티프로세스(전술 MC 선례) 10,000회+. 분포 꼬리(드문 패배) 정확. A1과 결합 시 필수.

---

## 하 (미세 개선, 무게 대비 이득 작음 — 여력 있을 때)

### 캠페인 디테일
- **A3** 재배정 주기 6h 고정 → 더 촘촘 + 교통로 이동시간 정밀화(engine_campaign.py:37).
- **A5** 연료 소모 틱당 0.01 고정 → 거리·속도·기동 기반 소모.
- **A6** CampaignShip 추상(물리필드 없음) → 전술 객체 상태 연동(A1에 종속).
### 공군
- **B3** airpower 소티율 가중 지속 근사(실제 항적 아님) → 개별 소티 궤적 시뮬.
### DB 제원
- **C2** 함정 비용 현가 근사(PCC·CRAM·CSAM·USV·UUV·CG-47·CVN) → 실제 조달가 대조.
- **C3** 전력 budget 발전−추진 단일 추상(2026-07-04 설계합의) → 발전·추진 분리(설계 재논의 필요).
- **C4** HHQ-10 = AK-630 근사(engine_combat.py:626) → 실제 HHQ-10 제원.
### 전술 물리
- **D2** detect_m = 스폰거리 근사(engine_combat.py:1916) → 실제 탐지거리 모델 분리.
- **D3** RCS 폴백 BF4 근사 하드코딩(engine_combat.py:2223) → 실제 RCS 값 테이블.
- **D4** substep 해상도 더 작게(이미 폐쇄속도서 충분·정밀) → 초고속 표적 여유 마진.
- **D5** 레이저 순항속도 근사(engine_combat.py:148, 전장모드 한정) → 전장 실속도 반영.
### 샘플링
- **E2** 전술 MC LHS 근사 → 표준 MC 반복 증가(정확도↑·속도↓).

---

## 우선순위 권고
1. **A1(+E1)** — 유일한 고가치. 캠페인 근본 근사(손실 미추정) 제거. 하이브리드로 무게 조절.
2. **C1·C5** — DB 현실성 감사(종합감사 ②) 때 곁들여 처리(저비용).
3. **A2·A4·A6** — A1 진행 시 함께.
4. **B2** — 적 공군 DB 확충(로드맵 육해공 DB 심화)과 묶음.
5. 나머지 하(下) — 여력·계기 있을 때 개별.

## 주의
- 전부 **밸런스/수치 변화** → 회귀 골든 갱신 + 기준값 재측정([[project-baseline-*]]) 동반.
- 작전급 추상을 정밀화할 땐 **"작전급이 추상인 게 설계 의도"**([[project-campaign-engine]])와 충돌 여부 먼저 판단.
- 관련: [[patch-queue]] · [[project-campaign-engine]] · [[project-battle-engine]] · [[project-db-realism]].
