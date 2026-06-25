# v16.2 — 극초음속 활공 궤적 고도화 (설계)

## 배경 / 문제
v16.02.01에서 HGV 다층 요격(고고도 SM-3 / 저고도 SM-6 Block IB)을 도입했으나,
`m.altitude_m`이 **DB 고정값**으로 비행 내내 불변 → `_select_defense_wpn`이 각 HGV를
항상 같은 층으로만 판정한다(DF-17 60km=항상 SM-3, 지르콘 10km=항상 SM-6 Block IB).
실제 HGV는 마하 5+로 **활공하며 고도를 낮추고 종말에 급강하**하므로, 다층 방어의 진짜
의미(고고도 SM-3 시도 → 누출 시 저고도 SM-6 Block IB 재교전)가 발현되지 않는다.

## HGV DB 고도(정점)
DF-17 60km · YJ-21 40km · 킨잘 20km · 지르콘 10km (모두 `is_hgv=True`).
핵심 가치 = **고고도 HGV(DF-17·YJ-21)가 활공→종말 강하하며 SM-3→SM-6 Block IB로 요격 층 전환**.

## 설계
`enable_hgv_glide` 플래그(3종 세트, 기본 OFF·실험적, 단발+전장 공통). OFF면 altitude_m
고정(현행) → 회귀 bit-identical. ON이면 비행 진행도(p=1-rem/_init_dist)에 따라 매 틱
`m.altitude_m`을 활공 프로파일로 갱신 → `_select_defense_wpn`이 자동으로 단계별 층 선택.
요격 SAM이 빗나가면 미사일이 살아 저고도로 내려와 다음 틱 다른 무기로 **재교전**(자연 발현).

### 고도 프로파일 `_hgv_glide_alt(p, peak)`
교전 구간은 활공~종말(부스트 상승은 사거리 밖에서 종료 → 스폰점=활공 정점).
- 활공(p<0.65): peak에서 완만히 하강 → 0.65·peak (계수 `_HGV_GLIDE_DESCENT`=0.35)
- 종말(p≥0.65): 0.65·peak → 종말 침투고도 `_HGV_TERMINAL_ALT_M`=2000m 급강하
- DF-17(60km): 활공 60→39km(전반 SM-3), 종말 39→2km(SM-6 Block IB 전환). 다층 재교전 실현.

### 기동 회피
활공·종말 횡기동 → 활공 HGV 요격 시 아군 SAM Pk ×`_HGV_GLIDE_EVADE`(0.85). 종말
회피(`terminal_evasion_factor`, 10km 이내)는 기존대로 누적.

## 변경 파일
- engine_combat.py: 상수 4종, `__init__` `_hgv_glide`, `_hgv_glide_alt`/`_hgv_glide_update`,
  `_update_positions` 호출(미사일 이동 후), `_check_hits` friendly_sam HGV Pk 페널티,
  `_missile_disp_alt` 시각화 일관(ON이면 실제 altitude_m).
- app_main.py: 체크박스 + cfg 빌드/로드 + 헤더 + APP_VERSION.
- app_changelog.json, audit_static_scan.py(flags 추가).

## 부모 무수정 / 회귀
부모 TimeStepEngine에 OFF-가드 메서드 추가(esm_arm·cyber 선례). OFF면 `random` 미소비·
altitude_m 고정 → 골든 bit-identical. ON 효과는 ON/OFF MC로 측정(다층 재교전·SM-3→SM-6
Block IB 전환 확인). 검증 게이트=회귀 PASS + ON/OFF 효과 + code-review high.
