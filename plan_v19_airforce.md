# v19 공군 작전급 — 설계 문서 (Phase 0)

> v18에서 완성한 **해군 작전급 캠페인 엔진**(72h 전역·1h 틱·교전 즉시예측) 위에
> **공군 작전 층**을 얹는다. 핵심 가치 = **제공권(air superiority)이 해상 교통로(SLOC) 통제와 연동**.
> 정본 = 이 문서. `_PLANS`가 버전 정본(로드맵_상세 문서는 이 계열을 'v18 공군'으로 표기 = 한 칸 stale).

---

## 0. 사용자 합의 사항 (2026-07-08)
- **아키텍처**: 별도 `engine_airforce.py` — AirForcePool·제공권 격자·SEAD 자료구조를 별도 파일에.
  `CampaignEngine`(engine_campaign.py)이 import해 **얇은 접합**으로 공군 틱을 호출. v18이 engine_combat를 무수정 호출한 철학 계승.
- **제공권 모델**: **한반도 격자 지도**(_PLANS 원안 채택 — v18의 추상 노드와 달리 격자 선택).
  격자 셀별 제공권 0~1, 셀 그룹이 SLOC zone(서해·대한해협·동해)에 매핑 → SLOC 피드백.
- **범위**: v19.1부터 마이너 1개씩 순차(v18 방식). 각 단계 회귀·code-review high·GUI 스모크.

## 1. 목적 · 배경
현재 캠페인 엔진(v18)은 **해군 자산만** 다룬다. 실제 해상 작전은 상공의 제공권에 종속 —
제공권을 잃으면 함대는 적 항공·대함미사일에 노출된다. 공군 층을 얹어:
▸제공권 장악(CAP)·근접지원(CAS)·방공망 제압(SEAD)·전략폭격·정찰 임무를 작전급으로 운용
▸제공권 지도가 해상 교통로 통제에 연동(제공권 상실 → 해군 교전 즉시예측 패널티)
▸적 방공망·기지 타격이 캠페인 전체에 누적 반영.

## 2. 범위 · 끝 상태
- **별도 `engine_airforce.py`** — 공군 전용 자료구조·틱 로직. `engine_campaign.CampaignEngine`이 조합(compose).
  전술 엔진(engine_combat.py) **무수정** 유지 → 단발·전장 회귀 8×26 bit-identical.
- 제공권 = **한반도 격자**(coarse, 예: 위도·경도 6×8 셀), 셀별 0~1, 1h 틱 갱신.
- 공군 자산 = AirForcePool(v18 CampaignShip 상태머신 복제·항공 특화: 기지·소티·재무장·정비).
- `enable_air_campaign` 3종세트 기본 OFF·실험적. OFF면 v18 캠페인과 bit-identical(공군 층 미활성).

## 3. 재사용 vs 신규
| 그대로 재사용 | 신규(engine_airforce) |
|---|---|
| `CampaignEngine` 1h 틱 루프·시간 모델 | 제공권 격자(AirSuperiorityGrid) |
| v18 ForcePool 상태머신 패턴 | AirForcePool(소티·재무장·정비 상태머신) |
| `forecast_model`(교전 즉시예측) | `AIR_FORCE_DB`·임무 해결 모델 |
| SLOC 통제도(self.control)·zone 구조 | 격자↔zone 매핑·제공권→SLOC 패널티 |
| `_predict_engagement` | SEAD/전략폭격 성공확률·누적효과 |

## 4. 핵심 데이터 구조 (v19.1 MVP)

### 4.1 AIR_FORCE_DB (engine_core.py 또는 engine_airforce.py)
공개 제원 기반. 한국·미국 공군 기체:
```
KF-21·F-35A·F-15K·F-16(KF-16)·B-1B·B-52·E-737(조기경보)·RQ-4(정찰)
```
필드: 기체명·소속(ROK/US)·주임무·전투행동반경(km)·순항속도·무장(AAM·JDAM·ARM·순항미사일)·소티율.

### 4.2 격자 제공권 지도 (AirSuperiorityGrid)
- 한반도 전역 coarse 격자(위경도 셀). MVP는 작은 격자(예 6×8=48셀) — false precision 경계.
- 셀별 `superiority[cell] ∈ [0,1]`. 매 틱: 아군 제공권 출격 밀도 vs 적 방공망 강도 → target → 관성 갱신
  (`control += α(target-control)`, v18 SLOC 선례 재사용).
- **격자↔zone 매핑**: 각 SLOC zone(서해·대한해협·동해)이 격자 셀 집합에 대응 → zone 제공권 = 그 셀들 평균.

### 4.3 AirForcePool — 공군 자산
```
AirUnit: { aircraft_type, side, role, missions, sortie_rate, zone, mission }
```
- **v19.1(MVP)**: 지속 CAP 제공권을 **소티율 가중 airpower**로 모델링 — 각 CAP기가 매 틱
  sortie_rate 만큼 제공권에 기여, 누적 소티는 sortie_rate/24로 집계(실제 일일 출격수 규모).
- **정비·재무장 downtime 상태머신(ready/sortie/rearm/maint)은 v19.2 정교화 대상**.
  (v19.1 초안의 일일 소티 예산·재무장 상태는 지속 CAP엔 무기능이라 code-review에서 제거 —
  예산이 정확히 24틱분이고 일일 리셋이 재무장을 즉시 해제해 downtime이 발현 안 됨.)

### 4.4 임무 5종 (v19.1은 CAP·정찰 최소, 나머지 후속 마이너)
| 임무 | 효과 | 도입 |
|------|------|------|
| CAP(제공권 장악) | 해당 격자 제공권↑ | v19.1~19.2 |
| 정찰(ISR) | 격자 belief 갱신(전장의 안개) | v19.1 |
| CAS(근접지원) | 해군 교전 즉시예측 아군 보정 | v19.2 |
| SEAD/DEAD | 적 방공망 사이트 무력화 | v19.3 |
| 전략폭격 | 적 기지·항구 누적 손상 | v19.4 |

## 5. 인터페이스 (v19.1)
```python
# engine_airforce.py
class AirSuperiorityGrid: ...      # 격자 상태·갱신
class AirForcePool: ...            # 공군 자산 상태머신
def tick_air(grid, pool, cfg, hour): ...   # 1h 공군 틱 (CampaignEngine이 호출)
```
- `CampaignEngine.__init__`: `enable_air_campaign` 시 grid·pool 생성.
- `CampaignEngine.run()` 루프에 `_tick_air()` 삽입(제공권 갱신 → SLOC 패널티 반영).
- 결과 dict에 `air_superiority`(zone별)·`air_sorties`·`air_missions` 등 추가.

## 6. Phase 분할 (마이너 순차 = v18 방식)
| 버전 | 내용 | 산출 |
|---|---|---|
| **v19.1** | 공군 전력 & 임무 모델 MVP | AIR_FORCE_DB·AirForcePool·격자 스켈레톤·CAP/정찰·`enable_air_campaign` 3종세트. **캠페인 무영향(OFF bit-identical)** |
| v19.2 | 제공권 통제 모델 | 격자 갱신 정교화·제공권↔SLOC 연동(해군 교전 패널티)·CAS |
| v19.3 | SEAD/DEAD | EnemyADSite·타격/복구(6~48h)·BDA 보수 계수 |
| v19.4 | 전략폭격 & 기지 타격 | EnemyBase·누적 손상→적 출항능력→SLOC 위협 감소 |
| v19.5 | 공군 캠페인 통합 | 위협 상승 시 공군 임무 자동 요청·해공 통합 배정·보고서 타임라인 |
| v19.6 | 다전장 연동 | 공군 SEAD + 지상 방공망 교전구역 분할(v20 접점, 후순위) |

## 7. UI (v19.1 최소)
- 설정에 `enable_air_campaign` 토글(실험적, 캠페인 모드 하위). 캠페인 ON + 공군 ON 시 공군 층 활성.
- 결과: 캠페인 배너에 zone별 제공권 요약 추가. 격자 시각화는 v19.2~보고서 단계.

## 8. 하위호환 · 회귀
- 전술 엔진(engine_combat.py) **무수정** → 단발·전장 8×26 bit-identical.
- `enable_air_campaign` OFF(기본) → v18 캠페인 완전 무영향(공군 틱 미호출).
- 구버전 cfg(air 키 없음) 정상. 캠페인 3종세트 자동검사(chk_flag_triplet)에 소비처 명시 등록.

## 9. 리스크
- **격자 false precision**: 제공권 격자가 실제보다 정밀해 보일 위험 → coarse 격자·"확률장" 명시, 연동계수 보수적.
- **BDA 과대평가**: SEAD·전략폭격 효과는 역사적으로 과대평가 → 보수적 계수(로드맵 경고).
- **제공권→SLOC 연동계수**: 추정값 → 명시적 파라미터·민감도로 관리.
- 난이도 매우 높음 → **Opus/high·code-review high·설계 먼저 합의·마이너마다 GUI 스모크**.
- APP_VERSION = **major 전환 v18.01.01**(v18 캠페인이 APP_VERSION v17이었던 선례 — 로드맵 라벨 v19 ≠ APP_VERSION major).

## 10. 번호 정합 위생 (착수 시)
로드맵_상세_v11-v20.md가 이 계열을 'v18 공군'으로 표기 → _PLANS(v19)와 한 칸 어긋남(문서 5행에 매핑 주석 이미 존재). _PLANS가 정본.

## 11. v19.5 공군 캠페인 통합 — 상세 설계 (2026-07-08 합의, A안)

**핵심 결정**: CAS(근접 항공 지원)를 제공권과 **직교하는 레버**에 둔다. 교전은 두 레버로
결판난다 — ①`win_p·score`(성패·질) ②`dmg`(아군 손실). v19.2 제공권은 이미 ①에 factor를
곱한다. CAS를 ①에 또 붙이면 제공권과 동형(중복 = 레이저·ARM 반복 실패 패턴). 따라서
**CAS는 ②(dmg 경감)에 작용** — 제공권=이기게, CAS=이기든 지든 함정 손실을 줄이는 근접 엄호.

### 11.1 요청 신호 (해군→공군, "자동 요청")
- 캠페인이 매 틱 zone별 **지원 요청 우선도** 계산. `zone_threat`(위협 규모)과 차별화하려고
  **통제도(control) 항을 넣는다** — `req[z] = (1 - control[z]) × enemy_present[z]`.
  통제 붕괴 중이고 적이 실제 도달한 zone일수록 높음(단순 위협 규모와 다른 신호).
- `air.tick(zone_threat, support_req=None)` 신규 인자로 전달(기본값 → 하위호환·구버전 호출 정상).

### 11.2 통합 배정 (_assign에 CAS 분기 추가)
- CAS 가능 기체(missions에 'CAS' = KF-21·KF-16·F-16) 중 일부를 **요청 우선도 최고 zone**에
  차출(CAP에서 뺌 = 현실적 트레이드오프, v19.3 SEAD 차출 선례와 일관).
- 배정 우선순위: recon → aew → SEAD(방공망 zone) → **CAS(요청 최고 zone, 임계 이상일 때만)**
  → CAP → strike. CAS는 요청 임계 미만이면 미발동(평시엔 CAP로 남음).

### 11.3 CAS 효과 (dmg 경감, 결정론)
- `AirCampaign.cas_support() → {zone: relief 0~1}` 신규 메서드: zone별 CAS 소티율 합 × 보수
  계수, 상한 클램프. 캠페인 `_tick_engagements`가 조회.
- `_apply_engagement`에서 그 zone relief만큼 `dmg *= (1 - relief)`. **rng 소비 순서·횟수 불변**
  (스칼라 곱만) → CAS 없음(relief=0)이면 v19.4와 bit-identical. win_p 경로 무변.

### 11.4 보고서·타임라인 (v19.5.2)
- summary 신규 키: `air_cas_sorties`·`n_cas_requests`. `air_timeline`에 임무별 소티 시계열
  (cap/sead/strike/cas) + CAS 요청 로그(t_h·zone·relief). MC 3경로 아님(캠페인 전용 result).
- UI: 상태줄+교전분석탭 `_air_txt`에 CAS 요약 세그먼트 추가(제공권·SEAD·전략폭격 뒤).

### 11.5 버전·검증
- **v18.01.05 (v19.5.1)**: 11.1~11.3 엔진(engine_airforce·engine_campaign).
- **v18.01.06 (v19.5.2)**: 11.4 보고서 타임라인 + UI 렌더.
- 각 seq: 회귀 8×26(OFF·CAS없음 bit-identical)·정적 스캔·code-review medium·캠페인 GUI 스모크
  + CAS ON/OFF 기준값(함정 생존·수리 횟수 binding 확인). 난이도 중간(Sonnet/medium).
- **불변식**: 공군 OFF→air=None 무영향 / 공군 ON·CAS 미발동→relief=0→v19.4 동일 / rng 불변.
- **리스크(공통)**: 요청 신호가 zone_threat과 상관 높으면 배정 무변(죽은 기능) → 기준값에서
  CAS 소티·함정 생존이 실제로 움직이는지 확인, 안 움직이면 요청 공식(control 가중) 조정.
