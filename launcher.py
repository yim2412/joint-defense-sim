"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   이지스 기동전단 통합 방어 시뮬레이터  v11.11 — PyQt6 런처                ║
╠══════════════════════════════════════════════════════════════════════════════╣
║  [v11.11 — 항공 자산 7종 스펙시트 설명 보강 + 문서 정합]                     ║
║  NEW-A  DB 탭 항공 7종 상세 제원 등록 (KF-21·F-35A·FA-50·와일드캣·시호크·   ║
║         P-3C·P-8A) — 그간 스펙시트가 비어 있던 항공 자산 채움             ║
║  [v11.10 — DB 탭 사진 전 항목 보강 + FA-50 명칭 정정]                        ║
║  NEW-A  사진 없던 8개 항목 실사진 등록 (F-35A·KF-21·FA-50·J-16D·현무 등)     ║
║  NEW-B  표기 불일치 4종 파일 정합 (해성-I·신포급·하푼·SM-6) — DB 누락 0건    ║
║  BUG-1  FA-50 별칭 골든이글 → 파이팅이글 정정 (T-50이 골든이글)              ║
║  [v11.9 — 패치 내역 탭 시각화: 유형 색상 배지 + 최신 강조]                   ║
║  NEW-A  추가/수정/삭제 항목에 색상 알약 배지 (초록/주황/빨강)                ║
║  NEW-B  최신 버전이 맨 위로 + ⭐ 강조, 표시 순서 최신→과거로 전환            ║
║  [v11.8 patch — 메인 창 제목 버전 표기 고정 버그 수정]                       ║
║  BUG-1  창 제목이 v9.11에 고정 → APP_VERSION 단일 상수로 통합 (자동 반영)    ║
║  [v11.8 — 로드맵 확장: 현대전 4개 영역 추가]                                ║
║  NEW-A  무인 수상/수중정·기뢰전·항만 방어·보급 병참 향후 계획 등록          ║
║  [v11.7 — 작전 시나리오 라이브러리]                                         ║
║  NEW-A  교리 기반 작전 시나리오 4종 — 선택 시 편대·해역·날씨 자동 설정      ║
║  BUG-1  실행 기록 복원 시 적군 교전 모드 미복원 문제 해결                   ║
║  [v11.6 — 과거 패치 내역 용어 정리]                                         ║
║  정리   과거 패치 201개 항목의 코드 명칭을 군사 용어·자연어로 통일          ║
║  [v11.4 — 분석 속도 4.5배 향상]                                             ║
║  NEW-A  거리 계산을 평면 근사로 전환 — haversine 삼각함수 제거 (주 병목 해소)║
║  NEW-B  MC 경량 모드(mc_mode) — 로그·프레임 기록 비활성화                   ║
║  NEW-C  LHS 분석 멀티프로세싱 — CPU 코어 수만큼 병렬 실행                   ║
║  NEW-D  _mc_batch_worker·monte_carlo_v7 mc_mode 자동 적용                   ║
║  [v11.1 — 기준 시나리오 MC 500회 검증 + ECM 버그 수정]                      ║
║  BUG-1  적 항공기 ECM 재밍 강도 속성 미할당 → 시뮬 중단 오류 해결           ║
║  검증   기동전단 기본 vs 랴오닝 항모전단 MC 500회 완료                       ║
║         요격률 11.5%±4.0% / 교전 비용 $18.6M / 아군 전멸률 100%             ║
║  [v10.31 — 향후 계획 순서 최적화: 3개 항목 재배치]                          ║
║  UPD-A  v15.2(다전장 연동) → v18.6으로 이동 (작전급 완성 후 연동이 맞음)   ║
║  UPD-B  v16.1(군수·보급) 삭제 → v17.2 전력 관리에 흡수                     ║
║  UPD-C  v16.3(멀티플레이어) → v20 이후 선택 트랙으로 이동                  ║
║  [v10.30 — 향후 계획 충돌·중복 조정 (v11.3·v12.2·v13.3·v15.1)]             ║
║  UPD-A  v11.3: 설정 패널 구조 유지 정책으로 변경 (분리 구현 완료)           ║
║  UPD-B  v12.2: 수온약층·해역 보정 완료분 제외, 미구현 고도화만 명시          ║
║  UPD-C  v13.3: 기본 통계 완료분 제외, 상세 지표 확장만 명시                  ║
║  UPD-D  v15.1: ECM 완료분 제외, ESM 역탐지·ARM 대응만 명시                  ║
║  [v10.29 — git 파일 정비: DB 4종 등록, 폐기 파일 4종 제거]                  ║
║  NEW-A  해양음향·해양환경·지형 DB 3종 git 등록 (엔진 실사용 중)             ║
║  NEW-B  한반도 군사배치 DB git 등록 (v17~v19 작전급 선행 자료)              ║
║  DEL-A  폐기 파일 4종 git 제거 (애니메이션·대시보드·구버전 보고서 2종)      ║
║  [v10.28 — 향후 계획에 '🔧 정비' 항목 추가]                                 ║
║  [v10.22 — 로드맵 48개 항목 3차원(구현·군사·범위) 현실성 검토]              ║
║  [v10.15 — 3단계 감사 수치 수정 9건]                                         ║
║  PHY-6   산둥 항모 self_defense_pk 0.47→0.45 / enemy_ciws_pk 0.42→0.40     ║
║  PHY-7   푸젠 항모 self_defense_pk 0.50→0.48 / enemy_ciws_pk 0.45→0.43     ║
║  PHY-8   홍상어 cost_usd $500K→$1.8M (실제 단가)                            ║
║  PHY-9   ESSM Block II cost_usd $1.5M→$2.2M                                ║
║  PHY-10  해성-II cost_usd $1.2M→$2.2M (KF-21 strike cost 연동)             ║
║  PHY-11  현무-3C cost_usd $2M→$6M                                           ║
║  PHY-12  현무-4 cost_usd $3.5M→$8M                                          ║
║  [v10.14 — 수치·물리 모델 현실성 수정 6건]                                   ║
║  PHY-1  SM-3 range 500→650km / Pk 0.900→0.850 (실효 요격거리·실전 Pk)       ║
║  PHY-2  YJ-18 speed 1000→1250m/s / range 500→540km (종말 Mach3.5·실 사거리) ║
║  PHY-3  KF-21 cap_aam_range 80→120km (AIM-120C 중심 설계)                   ║
║  PHY-4  FA-50 cap_aam_range 35→45km (AIM-9X BVR 35~50km 중앙값)             ║
║  PHY-5  Damage Control: 레이더 15→25% / 추진 20→15% (포클랜드전 피탄 통계)  ║
║  [v10.13 — 코드 감사 버그 수정 5건]                                          ║
║  BUG-1  _tactical_max_salvo: 위협별 최솟값 보장 후 살보 상한 적용             ║
║  BUG-2  _set_region_ref() run() 호출 → __init__() 초반으로 이동              ║
║  BUG-3  히트맵 fallback cfg 구버전 키(enable_cec_preassign) + 항공자산 True  ║
║  BUG-4  _primary() friendly_ships 빈 리스트 IndexError → 명시적 예외         ║
║  BUG-5  _select_defense_wpn() range_km 기본값 0 → 500 (우선무기 미발사 방지) ║
║  [v10.12 — v10.8 좌표계 완전 전환: Vec2→LatLon + Haversine + 해류 연동]     ║
║  NEW-A  LatLon 클래스: lat/lon 저장, x/y 프로퍼티로 시각화 코드 자동 호환   ║
║  NEW-B  Vec2 → LatLon.from_xy() 11개소 전환, Vec2=LatLon 별칭 유지          ║
║  NEW-C  dist_to(): Haversine 거리 / move_toward(): lat·lon 갱신              ║
║  NEW-D  _set_region_ref(): 해역별 기준점 (동해·서해·대한해협) 자동 설정      ║
║  NEW-E  해류 연동 (enable_current): ocean_environment_db 해류 벡터 적용      ║
║  DEL-A  _PLANS v10.8(좌표계 전환) + v10.2(Phase A 잔여) 삭제 — 구현 완료   ║
║  [v10.11 — v10.7 전술 의사결정 모드: 30s 구간 일시정지 + 무기 선택]         ║
║  NEW-A  TacticalState 데이터클래스 + run() 루프 내 30s 구간 훅               ║
║  NEW-B  run_v7_simulation(): tactical_cb 파라미터 → SimV7 훅 주입           ║
║  NEW-C  SimWorker.tactical_pause 시그널 + resume_tactical() 메서드          ║
║  NEW-D  TacticalDialog: 위협·함정 현황 + 무기 우선순위·살보 선택 패널        ║
║  NEW-E  설정 패널 '전술 의사결정 모드' 체크박스 (기본 OFF, 단일 시뮬 전용)  ║
║  DEL-A  _PLANS v10.7(전술 의사결정) 삭제 — 구현 완료                        ║
║  [v10.10 — v10.6 항모 타격 작전: 항모 우선 집중 + KF-21 해성-II + 격침 판정]║
║  NEW-A  KF-21 cap_strike_wpn=해성-II (200km·Pk0.55·2발) 공대함 모드 추가   ║
║  NEW-B  _aircraft_aas(): KF-21 해성-II 공대함 공격 로직 (항모 우선·90s CD) ║
║  NEW-C  _friendly_strike(): 항모(high_value_target) 우선 정렬 + 살보 6발   ║
║  NEW-D  _compile(): carrier_status — 항모 격침/전투불능/정상 판정 키 추가   ║
║  NEW-E  공격 결과 탭: 항모 HP·상태 (🔴격침/🟡전투불능/🟢정상) 표시         ║
║  DEL-A  _PLANS v10.6(항모 타격) 삭제 — 구현 완료                           ║
║  [v10.9 — v10.5 한국 공군 CAP: F-35A·KF-21·FA-50 BVR 교전]                ║
║  NEW-A  FRIENDLY_AIRCRAFT_DB: F-35A·KF-21·FA-50 CAP 항공기 3종 추가        ║
║  NEW-B  _CAP_WX: CAP 전투기 날씨 제한 (태풍·황사새벽만 출격 불가)           ║
║  NEW-C  _aircraft_cap(): 적 항공기 BVR 요격 로직 (즉시 Pk, 60s cooldown)    ║
║  NEW-D  _build_aircraft(): F-35A/KF-21/FA-50 enable 플래그 추가             ║
║  NEW-E  설정 패널 CAP 체크박스 3개 추가 (항공 자산 그룹에 통합)              ║
║  DEL-A  _PLANS v10.5(CAP/SEAD) 삭제 — 구현 완료                            ║
║  [v10.8 — v10.4 CEC 협동 교전: 탐지 커버리지 통합 + 중계 Pk 패널티]        ║
║  NEW-A  per-ship 탐지거리 체크: 자체 탐지 불가 함정은 CEC 없이 교전 불가    ║
║  NEW-B  CEC 중계 교전 MissileObj.cec_relay 플래그 + Pk ×0.90 패널티        ║
║  NEW-C  chk_cec → enable_cec 매핑 수정 (기존 항상 ON 버그 수정)            ║
║  NEW-D  chk_cec 기본값 True, 툴팁 "CEC 협동 교전 (탐지 커버리지 통합)" 갱신 ║
║  DEL-A  _PLANS v10.3(Damage Control)·v10.4(CEC) 삭제 — 구현 완료           ║
║  [v10.7 — v10.1 완성: ICAO ISA 대기 테이블 + 4계절×5고도층 라디오존데]      ║
║  NEW-A  isa_atmosphere(): ICAO 표준 대기 대류권 함수 (고도→기온·압력·밀도)  ║
║  NEW-B  4계절 확장 — EVAP_DUCT_DB·WIND_CEP_FACTOR·TROPOSCATTER_DB 봄/가을 ║
║  NEW-C  ISA_RADIOSONDE_DB → (region, season, alt_layer) 3-tuple 5고도층    ║
║  NEW-D  _isa_refraction_factor(): alt≥100m 고도층별 보간 (기존 ≥500m 단일)  ║
║  NEW-E  UI 계절 선택 4계절 확장 (봄 3~5월 / 가을 10~11월 추가)              ║
║  [v10.6 — 향후 계획 v10.8 설계 확정: LatLon 완전 전환 + 해류 연동]          ║
║  UPD-A  _PLANS v10.8: 실제 지리 기반 LatLon 완전 교체 설계 반영             ║
║  [v10.5 — Damage Control: 피격 위치 비율 재조정 + VLS 탄약 손실]             ║
║  BUG-1  피격 위치 비율 재조정: 레이더 15%·추진 20%·VLS 25%·선체 40%         ║
║  BUG-2  엔진 피격 speed_factor 배율 0.70→0.60                               ║
║  NEW-A  VLS 피탄 시 탄약 25% 직접 손실 + _vls_depleted 플래그 갱신          ║
║  NEW-B  어뢰 피탄 서브시스템 분포 별도 처리 (추진 40%·선체 45% 위주)        ║
║  NEW-C  피격 로그에 '선체 직격' 케이스 메시지 추가                          ║
║  [v10.4 — 완전 양방향 교전 Phase C: 적 Anti-SAM 방어 로직]                  ║
║  NEW-A  _enemy_anti_sam(): 아군 SAM 접근 시 적 CIWS(2km Pk0.30)·SAM 요격   ║
║  NEW-B  SAM 탐지거리: rcs_m2 기반 계산 (최대 50km), anti-SAM Pk × 0.35     ║
║  NEW-C  설정 패널 '적 Anti-SAM 방어 적용' 체크박스 (기본 OFF)               ║
║  [v10.3 — 완전 양방향 교전 Phase B: 아군 SAM rcs_m2 속성 추가]              ║
║  NEW-A  _SAM_RCS: 무기별 RCS 상수 딕셔너리 (SM-3·SM-6·ESSM·해궁 등 8종)    ║
║  NEW-B  _launch_friendly_sam() / _fire_ground_sam(): sam.rcs_m2 설정 추가   ║
║  [v10.2 — 완전 양방향 교전 Phase D: 적 미사일 분산 타겟팅]                  ║
║  NEW-A  _pick_target(): 생존 함정 max_hp 가중 랜덤 타겟 선택 (어뢰→기함 우선)║
║  NEW-B  enemy_strike 4개 발사점 target=primary → _pick_target() 교체        ║
║  NEW-C  ship_subsystem_damage에 hits_taken 필드 추가                        ║
║  NEW-D  서브시스템 피해 탭 '피격' 컬럼 추가 (함정별 명중 횟수 표시)          ║
║  [v10.1 — 정밀 대기 모델: ISA 굴절 + 트로포스캐터]                          ║
║  NEW-A  ISA_RADIOSONDE_DB: 기상청 라디오존데 계절별 굴절 지수 보정 (6개 해역×계절)║
║  NEW-B  TROPOSCATTER_DB: 수평선 너머 고고도 표적 탐지거리 +7~16%            ║
║  NEW-C  _isa_refraction_factor(): 중고도(≥500m) 표적 굴절 보정             ║
║  NEW-D  _troposcatter_factor(): 고고도(≥1000m) BF6 미만 조건 산란 보정     ║
║  NEW-E  설정 패널 '정밀 대기 모델(ISA+트로포스캐터)' 체크박스 추가          ║
║  [v9.15 — 향후 계획 탭 v10.x 세부 계획 갱신]                                ║
║  UPD-A  _PLANS: v10.1~v10.8 항목 세분화 (정밀 대기·양방향교전·DC·CEC·CAP 등) ║
║  [v9.14 — 해협 통과 방어 시나리오: 방위 제한 + 협착 기동 패널티 + 전용 프리셋] ║
║  NEW-A  STRAIT_BEARING: 해협 유형별 위협 접근 방위 제한 (동/서/양방향 ±30°) ║
║  NEW-B  _spawn_threats(): 대한해협 선택 시 협착 방위로 자동 전환             ║
║  NEW-C  _update_positions(): STRAITS_DB 폭 기반 동적 회피 기동 패널티        ║
║  NEW-D  잠수함 스폰 수심 STRAITS_DB sill_m으로 자동 cap (서수도130m/동수도115m)║
║  NEW-E  ENEMY_FLEET_PRESETS: 이어도·대한해협·쓰시마 봉쇄 전용 프리셋 3개   ║
║  NEW-F  설정 패널 '해협 진입로' 콤보박스 — 대한해협 선택 시 자동 표시       ║
║  [v9.13 — 대기·해양 환경 센서 물리 모델: Beaufort 클러터 + 덕팅 + CEP 바람]  ║
║  NEW-A  WEATHER_BEAUFORT_MAP: 날씨 → Beaufort 매핑, radar/sonar_factor 물리화 ║
║  NEW-B  _make_physics_wx(): ocean_environment_db 클러터·소음 데이터 자동 적용 ║
║  NEW-C  _evap_duct_factor(): 증발 덕팅 — 저고도 표적 탐지거리 증가           ║
║  NEW-D  _wind_cep_factor(): 고층 바람 CEP — 순항미사일 탄착 오차 증가        ║
║  NEW-E  설정 패널 '증발 덕팅 적용' 체크박스 추가                             ║
║  [v9.12 — 지형·해상 환경 반영: WOA18 수온약층 + 지형 레이더 음영]            ║
║  NEW-A  ocean_acoustic_db WOA18 실측값 → _thermocline_factor() 해역·계절별  ║
║  NEW-B  TERRAIN_RADAR_PENALTY — 태백(3.4°)·소백(0.9°)·낭림(0.4°) 음영각    ║
║  NEW-C  _terrain_penalty() 신규: 해역+고도 기반 레이더 탐지거리 보정        ║
║  NEW-D  설정 패널 — 작전 해역·계절 드롭다운 + 지형 음영 체크박스 추가       ║
║  [v9.11 — 이지스 어쇼어 + THAAD 지상 BMD 연동]                              ║
║  NEW-A  이지스 어쇼어 SM-3: 탄도/HGV 중간단계 선제 요격 (고도 ≥ 40km)      ║
║  NEW-B  THAAD: 탄도/HGV 종말고고도 요격 (고도 10~150km, hit-to-kill)        ║
║  NEW-C  _select_defense_wpn: 어쇼어 활성 시 함정 SM-3 최후 백업으로 하락    ║
║  NEW-D  취약점 진단: 지상 BMD 탄약 고갈 경고 추가                           ║
║  [v9.10 — 교전 후 브리핑 자동 생성: REQ 탭 하단 + Excel 브리핑 시트]        ║
║  NEW-A  engine_v7: generate_briefing() — 서술형 군사 보고서 자동 생성       ║
║  NEW-B  REQ 판정 탭 하단 접이식 브리핑 패널 (복사·TXT 저장 버튼)            ║
║  NEW-C  Excel 보고서 Sheet4 '교전 후 브리핑' 자동 포함                      ║
║  [v9.9 — 전자전 강화: 적 ECM 에어리어 재밍 + 채프/플레어/DRFM 세분화]       ║
║  NEW-A  J-16D 전자전기 추가 (ENEMY_DB) — 강력한 재밍 파드, 편대 전체 엄호   ║
║  NEW-B  적 ECM → 아군 레이더 탐지거리 감소 (수상함·대함 탐지에만 적용)      ║
║  NEW-C  SHIP_DB eccm_factor — 이지스함(0.65~0.75) ~ 소형함(0.20) 재밍 상쇄  ║
║  NEW-D  채프/플레어/DRFM 세분화 — seeker 유형별 자체 방어 효과 분리          ║
║  [v9.8 — 헬기 대잠 현실화 + P-8A 탐지 모델]                                ║
║  NEW-A  FriendlyAircraftObj 탐지 상태 머신 (idle/hovering/cooldown)         ║
║  NEW-B  헬기(AW-159/MH-60R): 디핑소나 — 호버링→탐지확률→재탐색 흐름       ║
║  NEW-C  초계기(P-3C/P-8A): 소노부이 — 탐지확률 판정 + 재투하               ║
║  NEW-D  탐지 확률 = base_prob × 수온층 계수 × 날씨 계수                    ║
║  NEW-E  최대 재탐색 횟수 초과 시 표적 포기 로그                             ║
║  [v9.7 — UI 개편: 아코디언 사이드바 + 시뮬 진행 팝업 상세화]                ║
║  NEW-A  AccordionSidebar: 26개 항목을 5개 카테고리로 분류 + 검색·배지·      ║
║         마지막 탭 기억 (QSettings)                                           ║
║  NEW-B  FloatingMonitor 전면 재설계 — 단일 시뮬: 진행 바+위협/VLS+로그 스트림║
║         MC 분석: 단계별 타이밍 바+수렴 감지+이전 실행 델타 비교             ║
║  NEW-C  중단 버튼 (■ 중단) → SimWorker.requestInterruption() 연결           ║
║  NEW-D  engine_v7: 단계별 소요시간 측정(phase_times) + step_cb 콜백         ║
║  NEW-E  SimWorker: step_update·phase_update 시그널 추가                     ║
║  [v9.6 — 북한 잠수함 선제 기습: 은닉 → 어뢰+해성-3 동시 발사]               ║
║  NEW-A  engine.py: 신포급 잠수함 (기습) DB — is_ambush·dual_weapon 필드     ║
║  NEW-B  engine.py: 북한 잠수함 선제 기습·기습(소형) 프리셋 2종 추가         ║
║  NEW-C  engine_v7: EnemyThreatObj hidden_until·ambush_revealed 속성          ║
║  NEW-D  engine_v7: _build_enemies — 기습 잠수함 20km 스폰, hidden_until 설정║
║  NEW-E  engine_v7: _enemy_fire — 은닉 중 발사 금지 + dual_weapon 동시 발사  ║
║  NEW-F  engine_v7: ASW/_aircraft_asw — 은닉 중 탐지 불가                    ║
║  NEW-G  engine_v7: _step — 은닉 해제 시 '기습 탐지!' 로그                   ║
║  [v8.25 patch — 코드 감사 + 패치 내역 버전 표기 개선]                        ║
║  DEL-A  engine.py 데드코드 1,951줄 제거 (v6 시뮬 코드 — HeloEvent 등)       ║
║  DEL-B  낡은 메모리 파일 7개 삭제 (v7.x 계획 등 완료된 항목)                ║
║  NEW-A  패치 내역 탭: 버전 필드 숫자 → v7.xx/v8.xx 문자열로 변환            ║
║  NEW-B  CLAUDE.md 전면 갱신 (v8.25 현재 구조 반영)                          ║
║                                                                              ║
║  [v8.25 — 향후 계획 대기 목록 9종 정식 등록]                                ║
║  NEW-A  v9.x 계획: 야간·악천후 / VLS 고갈 / 현무-4 / 생존성 히트맵         ║
║  NEW-B  v9.x 계획: 헬기 대잠 강화 / P-8A / 채프·플레어 / 이지스 어쇼어     ║
║  NEW-C  v9.x 계획: 교전 후 브리핑 자동 생성                                 ║
║                                                                              ║
║  [v8.24 — v9.x/v10.x 계획 재정립]                                           ║
║  NEW-A  v9.x 6개 항목 구현 현황(%) 및 남은 작업 명시                        ║
║  NEW-B  v10.x: 완전 양방향 교전(40%구현)·항모 타격(20%)·의사결정 모드 상세화║
║                                                                              ║
║  [v8.23 — DB 설명 7종 추가 + v9.x/v10.x 장기 계획 수립]                    ║
║  NEW-A  spec_db: 랴오닝·산둥·푸젠 항모 상세 스펙 추가                       ║
║  NEW-B  spec_db: Kh-31P·LD-10·Kh-58U 대방사미사일 상세 스펙 추가            ║
║  NEW-C  spec_db: 해궁(K-SAAM) 상세 스펙 추가                                ║
║  NEW-D  향후 계획: v9.x 6개 + v10.x 3개 초안 수립                          ║
║                                                                              ║
║  [v8.22 — 교전 분석 탭 완전 동작 + Gantt 이름 잘림 수정]                     ║
║  NEW-A  engine_v7 _build_active_events(): MissileObj→EngagementAnalysis 어댑터║
║  NEW-B  _compile()에 active_events 키 추가 — Funnel/테이블/Gantt 전부 표시   ║
║  BUG-1  Gantt xlim 동적 조정 — 위협 이름 잘림 해소                           ║
║                                                                              ║
║  [v8.21 — DB 수치 3종 수정 + anim_render 의존성 제거]                        ║
║  BUG-1  폭풍 radar_factor 0.82→0.55 (태풍보다 높던 역전 현상 해소)           ║
║  BUG-2  J-35 백상어 speed_ms 450→640 m/s (Mach 1.3→1.9, 5세대기 기준 수정)  ║
║  BUG-3  _warmup_task: anim_render import 제거 → dummy lambda로 교체           ║
║                                                                              ║
║  [v8.20 — 대규모 감사: 침묵 버그 4종 + DB 수치 6종 수정]                    ║
║  BUG-1  '093형 잠수함 (위안급)' → DB 없는 이름: 3개 프리셋+랜덤풀 잠수함 스폰 안 됨║
║  BUG-2  푸젠 항모 carrier_aircraft='J-35 (스텔스 함재기)' → DB 불일치, 함재기 0회 출격║
║  BUG-3  CG-47 대공 탐지 850km → 450km (SPY-1B 기준, SPY-6 수준 과대 설정 수정)║
║  BUG-4  KDX-II 대공 탐지 120km → 250km (SM-2 사거리 170km보다 짧던 비정상 해소) ║
║  BUG-5  우달로이/슬라바 missile_speed_ms 2000 → 824 (P-800 Mach2.4배 과대 수정) ║
║  BUG-6  KDX-III-B1/B2 대공 800→900km / DDG-51 850→1000km / 해궁 15→20km   ║
║                                                                              ║
║  [v8.19 — 전체 감사: _page_dirty 탭 21·23 누락 수정]                        ║
║  BUG-1  _page_dirty에 탭 21(최적 조합)·23(CEC 비교) 누락 → 시뮬 후 미갱신  ║
║                                                                              ║
║  [v8.18 — 실행 로그 크래시 수정 + 탑재 기능 최신화]                         ║
║  BUG-1  SimLogDialog._records 미초기화 → textChanged 즉시 AttributeError 팅김║
║  NEW-A  탑재 기능 탭: 전장 애니메이션 → 교전 분석 항목으로 교체              ║
║                                                                              ║
║  [v8.17 — 전장 애니메이션 → 교전 분석 탭 교체]                              ║
║  NEW-A  EngagementAnalysisTab: 방어 Funnel / 위협 추적 테이블 / Gantt 타임라인║
║  DEL-A  AnimationTab·FrameRenderWorker 삭제 (2.5D 등각투영 폐기)            ║
║                                                                              ║
║  [v8.10 — SAM 살보·Pk 경고·VLS 소진 추적 3종 패치]                         ║
║  NEW-A  SAM 살보 로직: HGV→3발, 탄도탄·QBM·초음속→2발, 기타→1발            ║
║         항공기도 동일 기준 세분화 / CEC +1발 / CEC 두절 1발 고정            ║
║  NEW-B  Pk 추정값 경고: 적군·아군 DB 탭 + 결과 카드 영역에 ±15~20% 고지   ║
║  NEW-C  VLS 소진 추적: MC별 소진률 집계 → 결과 화면에 경고(≥20%) 표시      ║
║                                                                              ║
║  [v8.09 — 위협 임박도 정렬 개선]                                            ║
║  NEW-A  _urgency 공식 개선: speed/dist → speed/(dist−floor)                 ║
║         탄도탄 floor=150km, QBM=20km, 대함/항공=5km                         ║
║         탄도탄이 SM-3 교전창 하한 근접 시 임박도 급증 → 역전 현상 해소      ║
║                                                                              ║
║  [v8.08 — A/B 편대 구성 비교 탭 추가]                                       ║
║  NEW-A  ⚖ A/B 편대 비교 탭 — 현재 편대(A) vs 다른 프리셋(B) MC 대비        ║
║  NEW-B  ABCompareWorker — 비차단 백그라운드 실행                             ║
║  NEW-C  Δ 요격률·Δ 비용 강조 + 무기별 잔여 재고 대조 테이블                 ║
║                                                                              ║
║  [v8.07 — REQ 체계 개선]                                                    ║
║  NEW-A  REQ-03 삭제 — MC 평균 > 0% 는 항상 PASS, 무의미한 기준 제거        ║
║  NEW-B  REQ-01 단일 시뮬 → MC 평균 요격률 ≥ 95% (운 배제, 실력 판정)      ║
║  NEW-C  REQ-05 단일 시뮬 → MC 무피격 비율 ≥ 85%                            ║
║  NEW-D  REQ-07 잔여 ≥ 1발 → 주요 SAM 잔여 ≥ 초기 재고 20%                 ║
║                                                                              ║
║  [v8.06 — 코드 안정성 3종 수정]                                             ║
║  BUG-1  plot_v7() fig.clf() 누락 → 장기 사용 시 RAM 지속 증가 수정         ║
║  BUG-2  SimWorker 좀비 — 재실행 전 이전 워커 종료 보장                      ║
║  BUG-3  REQ 평가·DB 저장 except → _write_log로 에러 기록                   ║
║                                                                              ║
║  [v8.05 — 향후 계획에 코드 안정성 감사 항목 추가]                           ║
║                                                                              ║
║  [v8.04 — 향후 계획 전면 개편: 교정 항목 추가 + 16개 재정렬]                ║
║  NEW-A  교정 4종 신규 추가: REQ 체계·위협 임박도·SAM 살보·Pk 경고 UI       ║
║  NEW-B  해협 통과 v9.x 이동, 완전 양방향 교전 내용 재정의                   ║
║  NEW-C  5개→16개 전면 재편 (교정/개선→전술→시나리오→v9.x 순)               ║
║                                                                              ║
║  [v8.00 — 도움말/튜토리얼 탭 추가]                                          ║
║  NEW-A  런처 스플래시에 도움말 탭 추가 (용어 설명 / 실행 순서 / FAQ)        ║
║  NEW-B  최초 실행 시 도움말 탭 자동 선택, 이후엔 마지막 탭 위치 복원        ║
║                                                                              ║
║  [v7.50 — 용어 툴팁 추가]                                                   ║
║  NEW-A  향후 계획·탑재 기능 탭에 군사·기술 용어 마우스오버 툴팁 (~35종)     ║
║                                                                              ║
║  [v7.42 — 분석 고도화 + 시뮬레이션 모드 선택 UI]                            ║
║  NEW-A  시뮬레이션 모드 선택 (빠름 5,000회 / 표준 10,000회 / 정밀 100,000회)║
║  NEW-B  LHS 샘플링 + CVaR(최악 5%) 카드 — 불확실 파라미터 5종 반영          ║
║  NEW-C  스트레스 테스트 탭 — 채널 감소 × 레이더 성능 감소 2D 히트맵         ║
║  NEW-D  Sobol 민감도 분석 탭 — 정밀 모드 전용 (~32,768회)                   ║
║                                                                              ║
║  [v7.41 — DB 탭 개편 + 설명 텍스트 간소화]                                  ║
║  NEW-A  적군/아군 DB 탭을 전투기·함정·무기·잠수함·항공 세부 탭으로 분리      ║
║  NEW-B  무기 탭 내 대공·대함·대잠 색상 구분 범례 추가                        ║
║  NEW-C  기능 목록·향후 계획 설명 텍스트 전문용어 없이 쉬운 말로 재작성       ║
║                                                                              ║
║  [v7.38 — 함정 DB Batch 세분화]                                               ║
║  NEW-A  KDX-III → Batch I (세종대왕급, SM-3 없음) / Batch II (정조대왕급)    ║
║  NEW-B  FFX → Batch I (인천급) / Batch II (대구급, 해궁 추가) / Batch III    ║
║  NEW-C  FRIENDLY_DB: 해궁 (K-SAAM) 추가                                      ║
║  NEW-D  FLEET_PRESETS 전 프리셋 타입 키 갱신 + 전 이지스 기동전단 프리셋 추가║
║  NEW-E  spec_db: KDX-III-B1/B2, FFX-I/II/III 상세 스펙 각각 분리             ║
║                                                                              ║
║  [v7.37 — 전체 차트 고화질 + 폰트 확대]                                      ║
║  NEW-A  CHART_DPI 자동 감지: 화면 크기 기반 min 150 ~ max 300 DPI 설정       ║
║  NEW-B  정적 차트 13종 fontsize +3 일괄 증가 (8→11, 9→12, 11→14 등)          ║
║  NEW-C  MC 통계(plot_v7) fontsize +3, suptitle 13→16                         ║
║  NEW-D  애니메이션 프레임 dpi 120→150, 레이블·범례 폰트 +2                   ║
║  NEW-E  REQ 판정 탭: 요구조건 상단 / 취약점 진단 하단 배치 + 카드 크게       ║
║                                                                              ║
║  [v7.36 — 애니메이션 자막 진동 수정]                                         ║
║  BUG-1  lbl_events setWordWrap → setFixedHeight(28): 텍스트 변경 시           ║
║         캔버스 크기 변동(진동) 방지                                           ║
║                                                                              ║
║  [v7.35 — 종합 버그 감사 수정]                                               ║
║  BUG-1  PDF 보고서 MC 차트 누락: 삭제된 tmp 파일 참조 → _raw_bytes 직접 사용 ║
║  BUG-2  _on_frame_ready: idx 범위 초과 방어 코드 추가                        ║
║  BUG-3  load_frames: 재생 중 새 시뮬 로드 시 타이머·플래그 미초기화 수정     ║
║  BUG-4  _stop_sys_data_worker: None 중복 할당 제거                           ║
║                                                                              ║
║  [v7.34 — 전장 애니메이션 렉·프리즈 수정]                                   ║
║  BUG-1  _start_render_worker: cancel 후 wait() → 메인 스레드 블로킹 수정    ║
║         세대 카운터(_render_gen)로 구식 frame_ready 신호 필터링              ║
║  BUG-2  FrameRenderWorker: 10프레임마다 msleep(12) → 신호 폭주 방지         ║
║  BUG-3  _draw_frame: 재생 중 FastTransformation, 정지 시 Smooth             ║
║                                                                              ║
║  [v7.33 — 차트 렌더링 전면 최적화 (메인 스레드 matplotlib 제거)]             ║
║  BUG-1  tab_sensitivity·tab_min_stock: MplCanvas(메인스레드) →               ║
║         ChartPageWidget(백그라운드) + 순수 렌더 함수 분리                    ║
║  BUG-2  SysMonitorTab: 숨김 상태서 matplotlib 렌더 스킵 + showEvent 즉시 갱신║
║  BUG-3  시스템 모니터 타이머 1초 → 2초 (메인 스레드 matplotlib 부하 감소)   ║
║  BUG-4  _fill_log: processEvents() 제거 (setUpdatesEnabled 배치로 충분)      ║
║                                                                              ║
║  [v7.32 — 창 닫기 시 좀비 프로세스 완전 제거]                               ║
║  BUG-1  ChartRenderWorker 11개 closeEvent 미처리 → stop_worker() 추가       ║
║  BUG-2  WeatherWorker closeEvent 누락 → 날씨 비교 중 닫아도 즉시 종료       ║
║  BUG-3  ProcessPool shutdown 순서: None 먼저 설정 → 새 작업 제출 차단       ║
║  BUG-4  _stop_sys_data_worker: terminate 폴백 + closeEvent 직접 호출         ║
║                                                                              ║
║  [v7.31 — 결과 화면 탭 전환 시 UI 프리즈 수정]                              ║
║  BUG-1  SensitivityWorker·MinStockWorker 즉시 기동 → GIL 독점으로 프리즈    ║
║         → lazy-start: 감도 분석·최소 재고 탭 방문 시에만 워커 시작          ║
║  BUG-2  MC 통계 차트 이중 렌더(plot_v7→PNG→Figure→PNG) → bytes 직접 반환   ║
║                                                                              ║
║  [v7.30 — 결과 패널 MC 통계 미표시 버그 수정]                               ║
║  BUG-1  사이드바 row 1 유지 시 setCurrentRow(1) 신호 미발화 → 수동 트리거   ║
║                                                                              ║
║  [v7.29 — DB 스펙 패널 폰트 확대]                                           ║
║  NEW-1  SpecSheetPanel 제목 14→16px, 부제·카테고리·레이블·값 11→13px,       ║
║         비고 12→14px, 행간격 확대                                            ║
║                                                                              ║
║  [v7.28 — 시스템 모니터 버그 수정 + 향후 계획·changelog 갱신]              ║
║  BUG-1  시뮬 실행 중 오버레이 미표시 수정 (_sim_start_idx→벽시계 기반)      ║
║  BUG-2  코어별 퍼센트 폰트 크기 10px→12px (가독성 개선)                    ║
║  NEW-1  changelog.json v28 항목 추가                                        ║
║  NEW-2  향후 계획 탭 — 완료된 아군 잠수함 항목 제거 (v7.27 구현 완료)       ║
║                                                                              ║
║  [v7.27 — 아군 잠수함 추가 (KSS-I/II/III)]                                  ║
║  NEW-A  SHIP_DB: KSS-I 장보고급·KSS-II 류관순급·KSS-III 도산안창호급 추가  ║
║  NEW-B  engine_v7: 아군 잠수함 공격 로직 (수상함·적잠수함 어뢰/미사일)      ║
║  NEW-C  FRIENDLY_STRIKE_DB: 현무-3C 순항미사일 추가 (KSS-III VLS 전용)      ║
║  NEW-D  FLEET_PRESETS: 대잠전단 프리셋 (KDX-III + FFX×2 + KSS-II×2) 추가  ║
║  NEW-E  spec_db: KSS-I/II/III 상세 스펙 + 아군 DB 탭 사진 표시              ║
║                                                                              ║
║  [v7.26 — DB 탭 스펙 설명창 폰트 크기 확대]                                 ║
║  NEW-A  카테고리 헤더·레이블·값 9px → 11px, 비고 10px → 12px               ║
║                                                                              ║
║  [v7.25 — 설정 패널 정리: 고정값 전환 + 프로필·시나리오 기능 삭제]          ║
║  DEL-A  설정 프로필 섹션 완전 삭제 (UI + 메서드 6개)                        ║
║  DEL-B  시나리오 저장/불러오기 섹션 완전 삭제 (UI + 메서드 2개)             ║
║  NEW-A  함정 위치 랜덤 배치 항상 활성화 고정 (반경 10km)                    ║
║  NEW-B  C&D 시간 10초·확인 3초 하드코딩 / MC 1000회 고정                   ║
║                                                                              ║
║  [v7.24 — 향후 계획 탭 재정렬 + 아군 잠수함 항목 추가]                      ║
║  NEW-A  아군 잠수함 (KSS-I/II/III) 항목 신규 추가 — 1순위                  ║
║  NEW-B  12개 항목 최적 우선순위 재정렬                                       ║
║                                                                              ║
║  [v7.23 — DB 탭 필터 버튼 동작 + 좌우 분할 레이아웃 + 가로 사진]           ║
║  NEW-A  대공·대함·대잠 필터 토글 버튼 — 실시간 목록 필터링 + N종 카운터   ║
║  NEW-B  DB 탭 좌우 분할 (230px 이름 목록 + 우측 스펙 패널)                 ║
║  NEW-C  SpecSheetPanel 가로 사진 (전폭 175px 고정 높이)                     ║
║                                                                              ║
║  [v7.22 — spec_db 전 항목(85종) categories 구조 변환 완료]                  ║
║  NEW-A  아군 무기 13종: 5카테고리 (기본정보/물리적제원/성능/추진/유도·탄두) ║
║  NEW-B  아군 함정 15종: 6카테고리 (기본정보/제원/성능/추진/무장/센서)       ║
║  NEW-C  적군 전 항목 57종: 카테고리 구조 통일 (미사일·항공기·함정·잠수함)  ║
║                                                                              ║
║  [v7.21 — 아군 무기 스펙 상세화 + exe 이미지 번들 수정]                     ║
║  BUG-1  exe 빌드 시 assets/images 미포함 → launcher.spec 수정               ║
║  BUG-2  이미지 경로 _res() 함수 미사용 → exe 환경 경로 오류 수정            ║
║  NEW-A  spec_db: 아군 무기 13종 필드 4→6개 확장 (교전고도·탄두중량 등)     ║
║                                                                              ║
║  [v7.20 — 드론 DB 제거 + 창 레이아웃 개선 + normalize_enemy_db 연결 수정]  ║
║  DEL-A  소형 자폭 드론·드론 떼 전 파일 제거 (engine/engine_v7/spec_db)      ║
║  BUG-3  engine_v7: normalize_enemy_db import 누락 수정                      ║
║  BUG-4  설정 패널 수평 스크롤 제거 (430px 고정 + ScrollBarAlwaysOff)        ║
║                                                                              ║
║  [v7.18 — 미확인 전력 4종 DB 제거]                                          ║
║  DEL-A  095형·039C형 잠수함, CM-302, 수중자폭드론 — 실전 배치 미확인        ║
║                                                                              ║
║  [v7.17 — DB 탭 스펙시트 패널: 적군 63종·아군 15함정·13무기 상세 카드]     ║
║  NEW-A  spec_db.py: 91개 유닛 상세 스펙 DB (제원·원산국·비고)              ║
║  NEW-B  SpecSheetPanel: 사진/아이콘 + 제원 그리드 (고정 172px 하단 패널)   ║
║  NEW-C  적군 DB 탭: QSplitter + SpecSheetPanel (유닛 선택 시 즉시 표시)    ║
║  NEW-D  아군 DB 탭: 무기·함정 서브탭 각각 SpecSheetPanel 적용              ║
║                                                                              ║
║  [v7.16 — DB 대규모 확장 1차: 적군 19종·미군 7함정·3무기·한미연합 3프리셋]  ║
║  NEW-A  적군 DB 43→63종: 중국 7종·러시아 8종·북한 4종 신규 추가            ║
║  NEW-B  아군 SHIP_DB: DDG-51/CG-47/CVN/LPD/SSN + LST/AO 7함정 추가        ║
║  NEW-C  FRIENDLY_DB: ESSM Block II·SM-6 Block IB·Tomahawk Block V 추가     ║
║  NEW-D  한미 연합 프리셋 3종: 기본·강화·항모전단 지원                       ║
║  NEW-E  엔진: ESSM/SM-6IB 무기 선택 레이어 + Tomahawk 대함 타격 지원       ║
║                                                                              ║
║  [v7.15 — 자동 취약점 진단 카드]                                            ║
║  NEW-A  diagnose_vulnerabilities_v7(): 6종 규칙 기반 취약점 자동 탐지      ║
║  NEW-B  REQ 판정 탭 상단에 진단 카드 패널 (HIGH/MED/LOW/OK 색상 구분)      ║
║  NEW-C  개선 제안 자동 생성: 소진 무기→재고 증량, 채널 포화→CEC 활성화 등  ║
║                                                                              ║
║  [v7.14 — REQ 달성 최소 재고 역산 + '🔬 최소 재고' 탭 신설]               ║
║  NEW-A  find_min_stock_v7(): 이진 탐색으로 무기별 최소 함정당 재고 계산    ║
║  NEW-B  MinStockWorker: 백그라운드 역산 + 진행상황 상태바 표시             ║
║  NEW-C  '🔬 최소 재고' 탭: 현재/최소 비교 수평 막대 차트 (절약·부족 구분) ║
║                                                                              ║
║  [v7.13 — 드론 떼(Swarm) 전술 세부화 + 자폭 피격 수정]                     ║
║  NEW-A  '드론 떼 (Swarm-12)' DB 추가: 12기 그룹, RAM 1발 = 2~5기 제압     ║
║  NEW-B  자폭 드론 피격 수정: 200m 이내 도달 시 함정 피격 처리              ║
║  NEW-C  스웜 전용 무기 선택: RAM/CIWS 우선, SAM 낭비 금지                  ║
║                                                                              ║
║  [v7.12 — 혼합 공격 시나리오 7종 + 파도별 지연 스폰]                       ║
║  NEW-A  MIXED_ATTACK_SCENARIOS 7종: 순항+탄도+드론, 러시아 살라미, 북한 등 ║
║  NEW-B  파도 타이밍(wave_offset_s): 위협이 delay_s 시점에 순차 출현        ║
║  NEW-C  launcher 혼합 시나리오 모드 UI: 드롭다운 + 파도 구성 미리보기      ║
║                                                                              ║
║  [v7.11 — 한국 해군 함정 8종 추가 + 현실 기반 편대 프리셋 5종 신설]       ║
║                                                                              ║
║  NEW-1  시뮬 seed numpy 동시 고정 (random + np.random.seed) — 완전 재현    ║
║  NEW-2  결과 화면 사용된 시드 표시 — 재현 시 동일 값 입력 안내             ║
║  NEW-3  YJ-21 극초음속 대함탄도미사일 추가 (Mach 10+, 1500km, HGV)        ║
║  NEW-4  YJ-18 초음속 대함미사일 시나리오 교체 (항모 킬 체인 3파)          ║
║  NEW-5  해성-3 잠수함발사 순항미사일 추가 (북한 SLCM, 1500km+)            ║
║  BUG-1  날씨 비교 UI 프리즈 수정: WeatherWorker(QThread) 비차단 실행       ║
║  BUG-2  update_status 조건 오류 수정: or "/" → or "/" in msg               ║
║  BUG-3  요격률 레이블 너비 52→68px (100.0% 텍스트 잘림 방지)              ║
║  DEAD-1 _draw_tactical / _draw_topdown 데드코드 제거                        ║
║                                                                              ║
║  [v7.8 — 결과 차트 UI 프리즈 완전 해결]                                    ║
║                                                                              ║
║  NEW-1  ChartRenderWorker(QThread): 차트 13개를 백그라운드에서 PNG 렌더     ║
║  NEW-2  ChartPageWidget: 로딩 → 이미지 전환, 리사이즈 자동 스케일          ║
║  BUG-1  render_map 인덱스 오류 수정 (12~17 → 12~16, 방위각~이전비교)       ║
║  BUG-2  _page_dirty에서 없는 인덱스 17 제거                                ║
║  BUG-3  감도 분석 draw() → draw_idle() 전환                                ║
║                                                                              ║
║  [v7.7 — 향후 계획 탭 전면 업데이트 (20개 항목)]                           ║
║                                                                              ║
║  NEW-1  향후 계획 탭: 2개 → 20개 항목으로 확장                             ║
║         P2~P21 전체 로드맵 반영 (차트 프리즈, 코드 감사, 적 DB,            ║
║         seed 고정, 랜덤 배치, 도움말, 기록 DB, REQ 역산,                   ║
║         취약점 진단, 최적 조합, Swarm, ARM, 혼합 시나리오,                 ║
║         중국 항모전단, 연합 작전, 해협 방어, 피해 세분화, 레이더 모드,    ║
║         양방향 교전, 지형·해상 환경)                                        ║
║                                                                              ║
║  [v7.6 — FloatingMonitor 개선]                                              ║
║                                                                              ║
║  NEW-1  단계 표시: "1/2 단일 시뮬 실행 중…" → "2/2 MC 분석 중…"            ║
║  NEW-2  경과 시간 타이머 (show() 시점 기준 실시간 카운트업)                 ║
║  NEW-3  라이브 요격률 게이지 — 배치마다 색상 변화 (빨강↔주황↔초록)         ║
║  NEW-4  격추/피격 평균 카운터 실시간 표시                                   ║
║  NEW-5  배치 스파크라인 — 12칸 컬러 사각형 수렴 추이                        ║
║  NEW-6  워커 프로세스 수 표시 (_SYS_CACHE 기반)                             ║
║  NEW-7  시뮬 시작 시 시스템 모니터 탭 자동 전환                             ║
║  NEW-8  rate_update 시그널 (SimWorker → FloatingMonitor) 연결               ║
║                                                                              ║
║  [v7.5 — CPU 우선순위 조정]                                                 ║
║                                                                              ║
║  BUG-1  _set_pool_priority(): 워커 프로세스 BELOW_NORMAL (psutil)           ║
║         글로벌 풀 예열 후 + 인라인 풀 생성 시 즉시 적용                    ║
║  BUG-2  SimWorker / SensitivityWorker / FrameRenderWorker                   ║
║         QThread.Priority.LowPriority 로 시작                                ║
║                                                                              ║
║  [v7.4 — Freeze/응답없음 수정]                                              ║
║  BUG-1  canvas.draw() → draw_idle() 전체 교체 (UI 스레드 블로킹 제거)      ║
║  BUG-2  로그 테이블 최대 300행 제한 + setUpdatesEnabled + processEvents     ║
║  BUG-3  탭 전환 200ms 디바운스 (QTimer, 빠른 연속 클릭 시 마지막만 렌더)   ║
║  BUG-4  차트 캐시 — 동일 result 객체 재렌더 스킵 (id 기반)                 ║
║                                                                              ║
║  [6단계 — PyQt6 네이티브 UI / 포팅 A+B]                                    ║
║                                                                              ║
║  NEW-A  MainWindow: 좌/우 분할 레이아웃 (설정 패널 + 결과 탭)               ║
║  NEW-B  ConfigPanel: 엔진 선택·적군 편대·아군 편대·무기 재고·MC 설정        ║
║  NEW-C  SimWorker(QThread): 백그라운드 시뮬 (UI 블로킹 없음)                ║
║  NEW-D  전장 애니메이션 탭: matplotlib 2.5D 등각투영 + QSlider 재생         ║
║  NEW-E  MC 통계 탭: plot_v7 차트 임베드                                     ║
║  NEW-F  교전 로그 탭: QTableWidget 시각별 이벤트                            ║
║  NEW-G  시스템 모니터 탭: CPU·RAM·스레드 실시간 (psutil + QTimer)           ║
║  NEW-H  포팅 A — 방어 무기 재고 UI (SM-3~Mk.46·기만기)                     ║
║  NEW-I  포팅 A — 적군 모드 선택 (커스텀/프리셋/랜덤) + 프리셋·난이도 UI    ║
║  NEW-J  포팅 B — 전술 옵션 토글 (ECM·회피·기만기·자체방어 QCheckBox)       ║
║  NEW-K  포팅 C — 항공 자산 토글 (AW-159·P-3C·P-8A QCheckBox, 대잠 전용)   ║
║                                                                              ║
║  실행: python launcher.py                                                    ║
║  패키지: pip install PyQt6 psutil matplotlib numpy openpyxl                 ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import sys, os, io, time, threading, json, multiprocessing, subprocess as _sp, traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
import psutil

# 앱 표시 버전 — 패치 시 헤더 주석과 함께 이 값만 갱신하면 창 제목 등에 일괄 반영
APP_VERSION = "v11.11"

# ── GPU / CPU 온도 헬퍼 ──────────────────────────────────────────────────────
_wmi_inst = None   # lazy-init

def _get_gpu_info() -> dict:
    """nvidia-smi로 GPU 정보 수집. 실패 시 빈 dict 반환."""
    try:
        out = _sp.check_output(
            ['nvidia-smi',
             '--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu',
             '--format=csv,noheader,nounits'],
            timeout=1, stderr=_sp.DEVNULL,
            creationflags=_sp.CREATE_NO_WINDOW)
        p = [x.strip() for x in out.decode().strip().split(',')]
        return {'util': int(p[0]), 'mem_used': int(p[1]),
                'mem_total': int(p[2]), 'temp': int(p[3])}
    except Exception:
        return {}

def _get_cpu_temp() -> float:
    """CPU 온도(°C). WMI 사용. 실패 시 -1 반환."""
    global _wmi_inst
    if _wmi_inst is None:
        try:
            import wmi
            _wmi_inst = wmi.WMI(namespace="root\\wmi")
        except Exception:
            _wmi_inst = False
    if not _wmi_inst:
        return -1.0
    try:
        zones = _wmi_inst.MSAcpi_ThermalZoneTemperature()
        if zones:
            return zones[0].CurrentTemperature / 10.0 - 273.15
    except Exception:
        _wmi_inst = None
    return -1.0

# ── 글로벌 프로세스 풀 (앱 시작 시 예열, 시뮬 내내 재사용) ──────────────────
_GLOBAL_POOL: 'ProcessPoolExecutor | None' = None
_PERF_HISTORY: list = []   # 최근 시뮬 성능 기록 (최대 10개)

# 시스템 모니터 캐시 — 백그라운드 워커가 채움, 메인 스레드는 읽기만
_SYS_CACHE: dict = {
    'cpu': 0.0, 'mem_pct': 0.0, 'mem_used': 0, 'mem_total': 1,
    'gpu': {}, 'cpu_temp': -1.0, 'cores': [], 'proc_ram': 0.0,
    'worker_stats': [], 'swap_used': 0, 'thread_cnt': 0,
}

def _init_global_pool():
    """앱 시작 시 백그라운드 스레드에서 호출 — 워커 프로세스 예열."""
    global _GLOBAL_POOL
    _warmup_task = lambda _: None  # BUG-3: anim_render 의존성 제거
    n = min(os.cpu_count() or 4, 8)
    _GLOBAL_POOL = ProcessPoolExecutor(max_workers=n)
    try:
        list(_GLOBAL_POOL.map(_warmup_task, range(n), timeout=60))
    except Exception:
        pass   # 예열 실패해도 풀 자체는 사용 가능
    _set_pool_priority(_GLOBAL_POOL)  # BUG-1: 워커 프로세스 BELOW_NORMAL

def _shutdown_global_pool():
    global _GLOBAL_POOL
    if _GLOBAL_POOL is None:
        return
    pool, _GLOBAL_POOL = _GLOBAL_POOL, None   # None 먼저 → 새 작업 제출 차단
    try:
        pool.shutdown(wait=False, cancel_futures=True)
    except Exception:
        try:
            pool.shutdown(wait=False)
        except Exception:
            pass
    # 풀 프로세스가 아직 살아 있으면 즉시 kill
    try:
        procs = getattr(pool, '_processes', {})
        pids = list(procs.keys()) if isinstance(procs, dict) else []
        for pid in pids:
            try:
                psutil.Process(pid).kill()
            except Exception:
                pass
    except Exception:
        pass

def _set_pool_priority(pool):
    """워커 프로세스 우선순위를 BELOW_NORMAL로 낮춤 — 시뮬 중 UI·다른 앱 응답성 유지."""
    # Windows: BELOW_NORMAL_PRIORITY_CLASS / Unix: nice=5
    _nice = getattr(psutil, 'BELOW_NORMAL_PRIORITY_CLASS', 5)
    try:
        # _processes는 ProcessPoolExecutor 내부 속성 — 없으면 자식 프로세스로 폴백
        procs = getattr(pool, '_processes', None) or {}
        pids  = list(procs.keys()) if isinstance(procs, dict) else []
        if not pids:
            pids = [c.pid for c in psutil.Process().children()]
        for pid in pids:
            try:
                psutil.Process(pid).nice(_nice)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except Exception:
        pass

def _res(filename: str) -> str:
    """PyInstaller exe 및 일반 실행 모두에서 리소스 파일 경로 반환."""
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, filename)


# ════════════════════════════════════════════════════════════════════════════
#  실행 로그 (sim_history.log 텍스트 + sim_history.json 구조화)
# ════════════════════════════════════════════════════════════════════════════
def _log_base() -> str:
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def _log_path()  -> str: return os.path.join(_log_base(), 'sim_history.log')
def _json_log_path() -> str: return os.path.join(_log_base(), 'sim_history.json')
def _app_state_path() -> str: return os.path.join(_log_base(), 'app_state.json')


def _load_app_state() -> dict:
    try:
        with open(_app_state_path(), encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def _save_app_state(state: dict):
    try:
        with open(_app_state_path(), 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _write_log(line: str):
    try:
        with open(_log_path(), 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except Exception:
        pass


def _load_json_log() -> list:
    try:
        with open(_json_log_path(), encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return []


def _save_json_log(records: list):
    try:
        with open(_json_log_path(), 'w', encoding='utf-8') as f:
            json.dump(records, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _write_sim_log(cfg: dict, result: dict, mc: dict):
    from datetime import datetime
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    enemy_parts = [f"{e.get('preset','?')} ×{e.get('count',1)}"
                   for e in cfg.get('enemy_fleet', [])]
    enemy_str = ', '.join(enemy_parts) if enemy_parts else cfg.get('enemy_fleet_preset', '?')
    n = max(mc.get('n', 1), 1)
    avg_hits  = sum(mc.get('friendly_hits',  [])) / n
    avg_edest = sum(mc.get('enemy_destroyed', [])) / n

    # ── 텍스트 로그 ──────────────────────────────────────────────────────
    lines = [
        '=' * 80,
        f'[{now}]  시뮬레이션 완료',
        '-' * 80,
        f'  편대       : {cfg.get("fleet_preset", "?")}',
        f'  날씨       : {cfg.get("weather", "?")}',
        f'  MC 횟수    : {mc.get("n", 0)}회',
        f'  적군 구성  : {enemy_str}',
        '',
        f'  총 위협    : {result.get("total_threats", 0)}발/기',
        f'  요격률     : {mc.get("mean_intercept", 0):.1%}  (±{mc.get("std_intercept", 0):.1%})',
        f'  완전요격   : {mc.get("full_pass_rate", 0):.1%}',
        f'  아군 피격  : {avg_hits:.1f}회 (평균)',
        f'  적 격침    : {avg_edest:.1f}기/척 (평균)',
        f'  총 비용    : ${result.get("total_cost", 0):,.0f}',
        '=' * 80, '',
    ]
    try:
        with open(_log_path(), 'a', encoding='utf-8') as f:
            f.write('\n'.join(lines) + '\n')
    except Exception:
        pass

    # ── JSON 로그 ─────────────────────────────────────────────────────────
    record = {
        'datetime':       now,
        'fleet':          cfg.get('fleet_preset', '?'),
        'weather':        cfg.get('weather', '?'),
        'mc_n':           mc.get('n', 0),
        'enemy':          enemy_str,
        'total_threats':  result.get('total_threats', 0),
        'mean_intercept': round(mc.get('mean_intercept', 0), 4),
        'std_intercept':  round(mc.get('std_intercept', 0), 4),
        'full_pass_rate': round(mc.get('full_pass_rate', 0), 4),
        'avg_friendly_hits':    round(avg_hits,  2),
        'avg_enemy_destroyed':  round(avg_edest, 2),
        'total_cost':     result.get('total_cost', 0),
    }
    records = _load_json_log()
    records.append(record)
    _save_json_log(records)


_SIM_MODE_NAMES = {0: '빠름', 1: '표준', 2: '정밀'}


def _db_path() -> str:
    return os.path.join(_log_base(), 'sim_history.db')


def _ensure_db():
    import sqlite3
    con = sqlite3.connect(_db_path())
    con.execute('''CREATE TABLE IF NOT EXISTS sim_history (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        datetime         TEXT    NOT NULL,
        fleet            TEXT,
        weather          TEXT,
        mc_n             INTEGER,
        sim_mode         TEXT,
        enemy            TEXT,
        total_threats    INTEGER,
        mean_intercept   REAL,
        std_intercept    REAL,
        full_pass_rate   REAL,
        cvar             REAL,
        avg_friendly_hits   REAL,
        avg_enemy_destroyed REAL,
        total_cost       REAL,
        req_pass         INTEGER,
        cfg_json         TEXT
    )''')
    con.commit()
    con.close()


def _write_sim_db(cfg: dict, result: dict, mc: dict, sim_mode_idx: int = 1):
    import sqlite3
    from datetime import datetime as _dt
    _ensure_db()
    now = _dt.now().strftime('%Y-%m-%d %H:%M:%S')
    enemy_parts = [f"{e.get('preset','?')} ×{e.get('count',1)}"
                   for e in cfg.get('enemy_fleet', [])]
    enemy_str = ', '.join(enemy_parts) if enemy_parts else cfg.get('enemy_fleet_preset', '?')
    n = max(mc.get('n', 1), 1)
    avg_hits  = sum(mc.get('friendly_hits',  [])) / n
    avg_edest = sum(mc.get('enemy_destroyed', [])) / n
    cvar_val  = mc.get('cvar', None)
    # REQ 전체 통과 여부 (평가 실패 시 None)
    req_pass = None
    try:
        from engine_v7 import evaluate_req_v7, REQ_ITEMS_V7
        verdicts, _ = evaluate_req_v7(result, mc, cfg)
        req_pass = int(all(verdicts))
    except Exception:
        _write_log(f'[WARN] evaluate_req_v7 실패: {traceback.format_exc()}')
    # cfg 저장: enemy_fleet 리스트는 enemy_str 컬럼에 이미 있으므로 제외
    safe_cfg = {k: v for k, v in cfg.items() if k != 'enemy_fleet'}
    try:
        con = sqlite3.connect(_db_path())
        con.execute('''INSERT INTO sim_history
            (datetime, fleet, weather, mc_n, sim_mode, enemy, total_threats,
             mean_intercept, std_intercept, full_pass_rate, cvar,
             avg_friendly_hits, avg_enemy_destroyed, total_cost, req_pass, cfg_json)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',
            (now,
             cfg.get('fleet_preset', '?'),
             cfg.get('weather', '?'),
             mc.get('n', 0),
             _SIM_MODE_NAMES.get(sim_mode_idx, '표준'),
             enemy_str,
             result.get('total_threats', 0),
             round(mc.get('mean_intercept', 0), 4),
             round(mc.get('std_intercept', 0), 4),
             round(mc.get('full_pass_rate', 0), 4),
             round(cvar_val, 4) if cvar_val is not None else None,
             round(avg_hits, 2),
             round(avg_edest, 2),
             result.get('total_cost', 0),
             req_pass,
             json.dumps(safe_cfg, ensure_ascii=False)))
        con.commit()
        con.close()
    except Exception:
        _write_log(f'[WARN] sim_history DB 저장 실패: {traceback.format_exc()}')


def _load_sim_db(limit: int = 500) -> list:
    import sqlite3
    _ensure_db()
    try:
        con = sqlite3.connect(_db_path())
        con.row_factory = sqlite3.Row
        rows = con.execute(
            'SELECT * FROM sim_history ORDER BY id DESC LIMIT ?', (limit,)
        ).fetchall()
        con.close()
        return [dict(r) for r in rows]
    except Exception:
        return []


def _clear_sim_db():
    import sqlite3
    _ensure_db()
    try:
        con = sqlite3.connect(_db_path())
        con.execute('DELETE FROM sim_history')
        con.commit()
        con.close()
    except Exception:
        pass


from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QDialog, QSplitter,
    QVBoxLayout, QHBoxLayout, QFormLayout, QScrollArea,
    QGridLayout, QFrame,
    QLabel, QPushButton, QComboBox, QSpinBox, QTabWidget,
    QTableWidget, QTableWidgetItem, QSlider, QProgressBar,
    QGroupBox, QStatusBar, QMessageBox, QHeaderView,
    QSizePolicy, QCheckBox, QFileDialog, QLineEdit,
    QListWidget, QListWidgetItem, QStackedWidget,
)
from PyQt6.QtGui import QFont, QColor, QPalette, QShortcut, QKeySequence, QPixmap
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSettings

import matplotlib
matplotlib.use('QtAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
import numpy as np


# ── 엔진 import ──────────────────────────────────────────────────────────────
try:
    from engine_v7 import (
        run_v7_simulation, monte_carlo_v7, plot_v7, save_excel_report_v7,
        FLEET_PRESETS as V7_FLEET_PRESETS,
        ENEMY_DB as V7_ENEMY_DB,
        WEATHER_DB,
        ENEMY_FLEET_PRESETS as V7_ENEMY_FLEET_PRESETS,
        ENEMY_FLEET_RANDOM_CFG as V7_RANDOM_CFG,
        MIXED_ATTACK_SCENARIOS as V7_MIXED_SCENARIOS,
        evaluate_req_v7, REQ_ITEMS_V7,
        find_all_min_stocks_v7,
        diagnose_vulnerabilities_v7,
        scenario_comparison_v7,
        calculate_fleet_detect_ranges,
        save_json_report_v7,
        _mc_batch_worker, _mc_lhs_batch_worker,
        FRIENDLY_DB as V7_FRIENDLY_DB,
        SHIP_DB as V7_SHIP_DB,
        FRIENDLY_AIRCRAFT_DB as V7_AIRCRAFT_DB,
        normalize_enemy_db as _normalize_enemy_db,
        monte_carlo_lhs, stress_test_grid, sobol_analysis, compute_cvar,
        _LHS_PARAM_DEFS, STRESS_DIMS,
        optimize_weapon_loadout_v7,
        compare_ab_v7,
        cec_comparison_v7,
        generate_briefing,
    )
    _V7_OK = True
except ImportError as e:
    _V7_OK = False
    _V7_ERR = str(e)
    V7_ENEMY_FLEET_PRESETS = {}
    V7_RANDOM_CFG          = {}
    V7_MIXED_SCENARIOS     = {}

# ── 스펙 DB import ────────────────────────────────────────────────────────────
try:
    from spec_db import SPEC_DETAIL_DB as _SPEC_DETAIL_DB
    _SPEC_DB_OK = True
except ImportError:
    _SPEC_DETAIL_DB = {}
    _SPEC_DB_OK = False

# ── 색상 팔레트 ──────────────────────────────────────────────────────────────
C_BG      = '#0d1117'
C_PANEL   = '#161b22'
C_BORDER  = '#30363d'
C_ACCENT  = '#3498db'
C_TEXT    = '#e6edf3'
C_SUBTEXT = '#7d8590'
C_GREEN   = '#2ecc71'
C_RED     = '#e74c3c'
C_ORANGE  = '#f39c12'

# 차트 렌더 DPI — main()에서 화면 크기 기반으로 갱신 (min 150, max 300)
CHART_DPI: int = 150


class NoScrollSpinBox(QSpinBox):
    """마우스 휠로 값이 변하지 않는 SpinBox."""
    def wheelEvent(self, event):
        event.ignore()


class NoScrollComboBox(QComboBox):
    """마우스 휠로 항목이 바뀌지 않는 ComboBox."""
    def wheelEvent(self, event):
        event.ignore()

STYLE_MAIN = f"""
QMainWindow, QWidget {{
    background-color: {C_BG};
    color: {C_TEXT};
    font-family: 'Malgun Gothic', 'Segoe UI', sans-serif;
    font-size: 17px;
}}
QGroupBox {{
    border: 1px solid {C_BORDER};
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 8px;
    font-weight: bold;
    color: {C_ACCENT};
    font-size: 17px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 4px;
    font-family: 'Malgun Gothic', 'Segoe UI', sans-serif;
}}
QComboBox, QSpinBox {{
    background-color: {C_PANEL};
    border: 1px solid {C_BORDER};
    border-radius: 4px;
    padding: 6px 12px;
    color: {C_TEXT};
    font-size: 17px;
}}
QComboBox::drop-down {{ border: none; }}
QComboBox QAbstractItemView {{
    background-color: {C_PANEL};
    color: {C_TEXT};
    selection-background-color: {C_ACCENT};
    font-size: 17px;
}}
QPushButton {{
    background-color: {C_ACCENT};
    color: white;
    border: none;
    border-radius: 6px;
    padding: 10px 20px;
    font-weight: bold;
    font-size: 17px;
}}
QPushButton:hover  {{ background-color: #2980b9; }}
QPushButton:pressed {{ background-color: #1a6fa3; }}
QPushButton:disabled {{ background-color: {C_BORDER}; color: {C_SUBTEXT}; }}
QTabWidget::pane {{
    border: 1px solid {C_BORDER};
    background: {C_BG};
}}
QTabBar::tab {{
    background: {C_PANEL};
    color: {C_SUBTEXT};
    border: 1px solid {C_BORDER};
    padding: 9px 20px;
    margin-right: 2px;
    font-size: 16px;
}}
QTabBar::tab:selected {{
    background: {C_BG};
    color: {C_ACCENT};
    border-bottom: 2px solid {C_ACCENT};
}}
QTableWidget {{
    background-color: {C_PANEL};
    gridline-color: {C_BORDER};
    color: {C_TEXT};
    border: none;
    font-size: 16px;
}}
QTableWidget QHeaderView::section {{
    background-color: {C_BG};
    color: {C_ACCENT};
    border: 1px solid {C_BORDER};
    padding: 6px;
    font-weight: bold;
    font-size: 16px;
}}
QScrollBar:vertical {{
    background: {C_PANEL};
    width: 8px;
}}
QScrollBar::handle:vertical {{
    background: {C_BORDER};
    border-radius: 4px;
}}
QSlider::groove:horizontal {{
    background: {C_BORDER};
    height: 4px;
    border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {C_ACCENT};
    width: 14px; height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}}
QProgressBar {{
    background: {C_PANEL};
    border: 1px solid {C_BORDER};
    border-radius: 4px;
    text-align: center;
    color: {C_TEXT};
}}
QProgressBar::chunk {{ background: {C_ACCENT}; border-radius: 3px; }}
QLabel {{ color: {C_TEXT}; }}
QStatusBar {{ background: {C_PANEL}; color: {C_SUBTEXT}; border-top: 1px solid {C_BORDER}; }}
QToolTip {{
    background-color: #1a2535;
    color: #e6edf3;
    border: 1px solid {C_ACCENT};
    border-radius: 5px;
    padding: 8px 12px;
    font-size: 14px;
    font-family: 'Malgun Gothic', 'Segoe UI', sans-serif;
}}
"""


# ════════════════════════════════════════════════════════════════════════════
#  플로팅 모니터 창 (시뮬 중 팝업)
# ════════════════════════════════════════════════════════════════════════════
class FloatingMonitor(QWidget):
    """시뮬레이션 실행 중 팝업 (v8.26 재설계)
    · 1/2 단일 시뮬: 진행 바 + 위협/VLS 상태 + 로그 스트림
    · 2/2 MC 분석:  MC 진행 바 + 단계별 타이밍 바 + 수렴 감지 + 이전 비교
    · 시스템 자원 행 (CPU/RAM/GPU) + 중단 버튼
    """

    stop_requested = pyqtSignal()
    _SPARK_N = 10

    def __init__(self, parent=None):
        super().__init__(parent,
                         Qt.WindowType.Window |
                         Qt.WindowType.FramelessWindowHint |
                         Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(480, 590)
        self._show_time: float  = 0.0
        self._mc_t0: float      = 0.0
        self._mc_done: int      = 0
        self._batch_rates: list = []
        self._phase_acc: dict   = {}   # 누적 단계 타이밍
        self._rates_history: list = [] # 수렴 감지용
        self._drag_pos = None
        self.setStyleSheet("* { font-family: 'Malgun Gothic', 'Segoe UI', sans-serif; }")
        self._timer = QTimer(self)
        self._timer.setInterval(800)
        self._timer.timeout.connect(self._refresh_tick)
        self._build_ui()

    # ── UI 구성 ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)

        self._card = QWidget(self)
        self._card.setObjectName('fmon_card')
        self._card.setStyleSheet(f"""
            #fmon_card {{
                background: rgba(13,17,23,242);
                border: 1px solid {C_ACCENT};
                border-radius: 10px;
            }}
        """)
        inner = QVBoxLayout(self._card)
        inner.setContentsMargins(16, 10, 16, 10)
        inner.setSpacing(4)

        # ── 제목 행 ──────────────────────────────────────────────────────────
        title_row = QHBoxLayout()
        self._lbl_title = QLabel("⚙  1/2  단일 시뮬 실행 중…")
        self._lbl_title.setStyleSheet(f"color:{C_ACCENT}; font-size:15px; font-weight:bold;")
        self._lbl_elapsed = QLabel("경과  0:00")
        self._lbl_elapsed.setStyleSheet(f"color:{C_SUBTEXT}; font-size:12px;")
        title_row.addWidget(self._lbl_title)
        title_row.addStretch()
        title_row.addWidget(self._lbl_elapsed)
        inner.addLayout(title_row)

        inner.addWidget(self._sep())

        # ── 단일 시뮬 구역 (QStackedWidget 인덱스 0) ─────────────────────────
        self._stack_mode = QStackedWidget()

        single_w = QWidget()
        sv = QVBoxLayout(single_w)
        sv.setContentsMargins(0, 0, 0, 0); sv.setSpacing(4)

        # 시뮬 진행 바 (시간)
        sp_row = QHBoxLayout()
        self._lbl_sim_t = QLabel("시뮬 시간  0s / —s")
        self._lbl_sim_t.setStyleSheet(f"color:{C_TEXT}; font-size:13px;")
        sp_row.addWidget(self._lbl_sim_t); sp_row.addStretch()
        sv.addLayout(sp_row)
        self._prog_sim = QProgressBar()
        self._prog_sim.setRange(0, 1000); self._prog_sim.setValue(0)
        self._prog_sim.setFixedHeight(7); self._prog_sim.setTextVisible(False)
        self._prog_sim.setStyleSheet(self._bar_css(C_ACCENT))
        sv.addWidget(self._prog_sim)

        # 위협 / VLS 상태 행
        status_row = QHBoxLayout(); status_row.setSpacing(16)
        self._lbl_alive = self._tag_lbl("위협", "— 개")
        self._lbl_vls   = self._tag_lbl("VLS 잔여", "— 발")
        status_row.addWidget(self._lbl_alive)
        status_row.addWidget(self._lbl_vls)
        status_row.addStretch()
        sv.addLayout(status_row)

        # 교전 로그 스트림 (최근 5줄)
        sv.addWidget(self._sep())
        log_hdr = QLabel("교전 로그")
        log_hdr.setStyleSheet(f"color:{C_SUBTEXT}; font-size:11px;")
        sv.addWidget(log_hdr)
        self._log_labels = []
        for _ in range(5):
            lbl = QLabel("")
            lbl.setStyleSheet(f"color:{C_TEXT}; font-size:12px; padding-left:4px;")
            lbl.setWordWrap(True)
            sv.addWidget(lbl)
            self._log_labels.append(lbl)
        self._log_buf: list = []

        self._stack_mode.addWidget(single_w)   # index 0

        # ── MC 구역 (QStackedWidget 인덱스 1) ────────────────────────────────
        mc_w = QWidget()
        mv = QVBoxLayout(mc_w)
        mv.setContentsMargins(0, 0, 0, 0); mv.setSpacing(4)

        # MC 진행 바
        mc_top = QHBoxLayout()
        self._lbl_mc  = QLabel("MC  0 / 0")
        self._lbl_mc.setStyleSheet(f"color:{C_TEXT}; font-size:14px;")
        self._lbl_eta = QLabel("잔여 —")
        self._lbl_eta.setStyleSheet(f"color:{C_SUBTEXT}; font-size:12px;")
        mc_top.addWidget(self._lbl_mc); mc_top.addStretch(); mc_top.addWidget(self._lbl_eta)
        mv.addLayout(mc_top)
        self._prog_mc = QProgressBar()
        self._prog_mc.setRange(0, 100); self._prog_mc.setValue(0)
        self._prog_mc.setFixedHeight(8); self._prog_mc.setTextVisible(False)
        self._prog_mc.setStyleSheet(self._bar_css(C_ACCENT))
        mv.addWidget(self._prog_mc)

        # 요격률 게이지 + 스파크라인
        rate_row = QHBoxLayout(); rate_row.setSpacing(6)
        lbl_rt = QLabel("요격률")
        lbl_rt.setStyleSheet(f"color:{C_SUBTEXT}; font-size:11px;"); lbl_rt.setFixedWidth(38)
        self._prog_rate = QProgressBar()
        self._prog_rate.setRange(0, 100); self._prog_rate.setValue(0)
        self._prog_rate.setFixedHeight(9); self._prog_rate.setTextVisible(False)
        self._prog_rate.setStyleSheet(self._bar_css('#2ecc71'))
        self._lbl_rate_val = QLabel("—%")
        self._lbl_rate_val.setStyleSheet(f"color:{C_TEXT}; font-size:14px; font-weight:bold;")
        self._lbl_rate_val.setFixedWidth(52)
        rate_row.addWidget(lbl_rt); rate_row.addWidget(self._prog_rate, 1)
        rate_row.addWidget(self._lbl_rate_val)
        self._spark_boxes = []
        for _ in range(self._SPARK_N):
            sq = QLabel(); sq.setFixedSize(10, 13)
            sq.setStyleSheet(f"background:{C_BORDER}; border-radius:2px;")
            rate_row.addWidget(sq); self._spark_boxes.append(sq)
        mv.addLayout(rate_row)

        # 격추 / 피격 / 속도
        kpi_row = QHBoxLayout(); kpi_row.setSpacing(16)
        self._lbl_ed  = QLabel("격추 —")
        self._lbl_fh  = QLabel("피격 —")
        self._lbl_spd = QLabel("— 회/s")
        for l in (self._lbl_ed, self._lbl_fh, self._lbl_spd):
            l.setStyleSheet(f"color:{C_TEXT}; font-size:12px;")
        kpi_row.addWidget(self._lbl_ed); kpi_row.addWidget(self._lbl_fh)
        kpi_row.addStretch(); kpi_row.addWidget(self._lbl_spd)
        mv.addLayout(kpi_row)

        mv.addWidget(self._sep())

        # 단계별 타이밍 바 (6개)
        phase_hdr = QLabel("단계별 평균 소요시간")
        phase_hdr.setStyleSheet(f"color:{C_SUBTEXT}; font-size:11px;")
        mv.addWidget(phase_hdr)

        _PHASE_LABELS = ['대공방어', '아군공격', '대잠', '적방어', '위치갱신', '교전판정']
        _PHASE_KEYS   = ['대공방어', '아군공격', '대잠', '적방어', '위치갱신', '교전판정']
        self._phase_bars: dict = {}   # key → (bar, val_lbl)
        for key, label in zip(_PHASE_KEYS, _PHASE_LABELS):
            row = QHBoxLayout(); row.setSpacing(4)
            name_lbl = QLabel(label)
            name_lbl.setFixedWidth(58)
            name_lbl.setStyleSheet(f"color:{C_TEXT}; font-size:11px;")
            bar = QProgressBar()
            bar.setRange(0, 1000); bar.setValue(0)
            bar.setFixedHeight(6); bar.setTextVisible(False)
            bar.setStyleSheet(self._bar_css('#3498db'))
            val_lbl = QLabel("0ms")
            val_lbl.setFixedWidth(44)
            val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            val_lbl.setStyleSheet(f"color:{C_SUBTEXT}; font-size:10px;")
            row.addWidget(name_lbl); row.addWidget(bar, 1); row.addWidget(val_lbl)
            mv.addLayout(row)
            self._phase_bars[key] = (bar, val_lbl)

        mv.addWidget(self._sep())

        # 수렴 감지 + 이전 실행 델타
        self._lbl_converge = QLabel("수렴  분석 중…")
        self._lbl_converge.setStyleSheet(f"color:{C_SUBTEXT}; font-size:11px;")
        self._lbl_delta    = QLabel("")
        self._lbl_delta.setStyleSheet(f"color:{C_SUBTEXT}; font-size:11px;")
        conv_row = QHBoxLayout()
        conv_row.addWidget(self._lbl_converge)
        conv_row.addStretch()
        conv_row.addWidget(self._lbl_delta)
        mv.addLayout(conv_row)

        self._stack_mode.addWidget(mc_w)   # index 1

        inner.addWidget(self._stack_mode)
        inner.addWidget(self._sep())

        # ── 시스템 자원 행 ────────────────────────────────────────────────────
        sys_row = QHBoxLayout(); sys_row.setSpacing(0)
        self._sys_cpu  = self._stat_cell("CPU",   "—%")
        self._sys_ram  = self._stat_cell("RAM",   "— GB")
        self._sys_gpu  = self._stat_cell("GPU",   "—%")
        self._sys_vram = self._stat_cell("VRAM",  "—")
        self._sys_wkr  = self._stat_cell("워커",  "—")
        for w in (self._sys_cpu, self._sys_ram, self._sys_gpu,
                  self._sys_vram, self._sys_wkr):
            sys_row.addWidget(w, 1)
        inner.addLayout(sys_row)

        # ── 하단: 중단 버튼 + 드래그 안내 ────────────────────────────────────
        bot_row = QHBoxLayout()
        tip = QLabel("드래그로 이동")
        tip.setStyleSheet(f"color:#444d56; font-size:10px;")
        btn_stop = QPushButton("■  중단")
        btn_stop.setFixedHeight(24)
        btn_stop.setStyleSheet(
            f"QPushButton {{ background:#3d1010; color:#e74c3c; border:1px solid #5a1a1a;"
            f" border-radius:4px; font-size:12px; padding:0 10px; }}"
            f"QPushButton:hover {{ background:#5a1a1a; }}"
        )
        btn_stop.clicked.connect(self.stop_requested)
        bot_row.addWidget(tip)
        bot_row.addStretch()
        bot_row.addWidget(btn_stop)
        inner.addLayout(bot_row)

        outer.addWidget(self._card)

    # ── 헬퍼 ─────────────────────────────────────────────────────────────────
    def _sep(self) -> QLabel:
        s = QLabel(); s.setFixedHeight(1)
        s.setStyleSheet(f"background:{C_BORDER};")
        return s

    @staticmethod
    def _bar_css(color: str) -> str:
        return (f"QProgressBar {{ background:#161b22; border-radius:3px; border:1px solid #21262d; }}"
                f"QProgressBar::chunk {{ background:{color}; border-radius:2px; }}")

    def _tag_lbl(self, title: str, init: str) -> QWidget:
        w = QWidget()
        h = QHBoxLayout(w); h.setContentsMargins(0, 0, 0, 0); h.setSpacing(4)
        t = QLabel(title); t.setStyleSheet(f"color:{C_SUBTEXT}; font-size:11px;")
        v = QLabel(init);  v.setStyleSheet(f"color:{C_TEXT}; font-size:13px; font-weight:bold;")
        v.setObjectName(f'tag_{title}')
        h.addWidget(t); h.addWidget(v)
        return w

    def _stat_cell(self, title: str, init: str) -> QWidget:
        w = QWidget()
        v = QVBoxLayout(w); v.setContentsMargins(0, 2, 0, 2); v.setSpacing(1)
        t = QLabel(title); t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t.setStyleSheet(f"color:{C_SUBTEXT}; font-size:10px;")
        val = QLabel(init); val.setAlignment(Qt.AlignmentFlag.AlignCenter)
        val.setStyleSheet(f"color:{C_TEXT}; font-size:13px; font-weight:bold;")
        val.setObjectName(f'sys_{title}')
        v.addWidget(t); v.addWidget(val)
        return w

    def _find_sys(self, key: str) -> QLabel:
        return self.findChild(QLabel, f'sys_{key}')

    def _find_tag(self, key: str) -> QLabel:
        return self.findChild(QLabel, f'tag_{key}')

    @staticmethod
    def _rate_color(r: float) -> str:
        return '#2ecc71' if r >= 0.80 else ('#f39c12' if r >= 0.60 else '#e74c3c')

    # ── 시스템 / 경과 타이머 ─────────────────────────────────────────────────
    def _refresh_tick(self):
        # 경과 시간
        if self._show_time:
            el = int(time.time() - self._show_time)
            m, s = divmod(el, 60)
            self._lbl_elapsed.setText(f"경과  {m}:{s:02d}")
        # 처리 속도 (MC 모드)
        if self._mc_t0 and self._mc_done:
            elapsed = time.time() - self._mc_t0
            spd = self._mc_done / elapsed if elapsed > 0 else 0.0
            self._lbl_spd.setText(f"{spd:.0f} 회/s")
        # 시스템
        c   = _SYS_CACHE
        gpu = c['gpu']
        self._find_sys('CPU' ).setText(f"{c['cpu']:.0f}%")
        self._find_sys('RAM' ).setText(f"{c.get('mem_used',0)/1024**3:.1f}G")
        self._find_sys('GPU' ).setText(f"{gpu['util']}%" if 'util' in gpu else "—")
        mu = gpu.get('mem_used')
        self._find_sys('VRAM').setText(f"{mu}M" if mu is not None else "—")
        wn = len(c.get('worker_stats', []))
        self._find_sys('워커').setText(str(wn) if wn else "—")

    # ── 외부 시그널 핸들러 ────────────────────────────────────────────────────
    def update_status(self, msg: str):
        if "MC" in msg and ("분석" in msg or "/" in msg):
            self._lbl_title.setText("⚙  2/2  MC 분석 중…")
            self._stack_mode.setCurrentIndex(1)
        elif "시뮬레이션 실행" in msg or "실행 중" in msg:
            self._lbl_title.setText("⚙  1/2  단일 시뮬 실행 중…")
            self._stack_mode.setCurrentIndex(0)

    def update_step(self, t: float, t_max: float, alive: int, vls: int, last_log: str):
        """단일 시뮬 타임스텝 콜백."""
        pct = int(t / t_max * 1000) if t_max > 0 else 0
        self._prog_sim.setValue(pct)
        self._lbl_sim_t.setText(f"시뮬 시간  {int(t)}s / {int(t_max)}s")
        self._find_tag('위협').setText(f"{alive} 개")
        self._find_tag('VLS 잔여').setText(f"{vls} 발")
        if last_log:
            self._log_buf.append(last_log)
            recent = self._log_buf[-5:]
            for i, lbl in enumerate(self._log_labels):
                lbl.setText(recent[i] if i < len(recent) else "")

    def update_mc(self, done: int, total: int, eta: float):
        if done == 1:
            per = eta / max(total - done, 1)
            self._mc_t0 = time.time() - per
        self._mc_done = done
        self._lbl_mc.setText(f"MC  {done:,} / {total:,}")
        pct = int(done * 100 / total) if total > 0 else 0
        self._prog_mc.setValue(pct)
        if eta > 0:
            m, s = divmod(int(eta), 60)
            self._lbl_eta.setText(f"잔여 {m}:{s:02d}" if m else f"잔여 {s}초")
        else:
            self._lbl_eta.setText("잔여 계산 중…")

    def update_rate(self, mean_rate: float, avg_ed: float, avg_fh: float):
        pct = int(mean_rate * 100)
        color = self._rate_color(mean_rate)
        self._prog_rate.setValue(pct)
        self._prog_rate.setStyleSheet(self._bar_css(color))
        self._lbl_rate_val.setText(f"{mean_rate:.1%}")
        self._lbl_rate_val.setStyleSheet(f"color:{color}; font-size:14px; font-weight:bold;")
        self._lbl_ed.setText(f"격추 {avg_ed:.1f}")
        self._lbl_fh.setText(f"피격 {avg_fh:.2f}")
        # 스파크라인
        self._batch_rates.append(mean_rate)
        recent = self._batch_rates[-self._SPARK_N:]
        for i, sq in enumerate(self._spark_boxes):
            if i < len(recent):
                sq.setStyleSheet(f"background:{self._rate_color(recent[i])}; border-radius:2px;")
            else:
                sq.setStyleSheet(f"background:{C_BORDER}; border-radius:2px;")
        # 수렴 감지 (최근 100개 vs 이전 100개 표준편차)
        self._rates_history.append(mean_rate)
        h = self._rates_history
        if len(h) >= 20:
            import numpy as _np
            std = _np.std(h[-20:]) * 100
            if std < 0.5:
                self._lbl_converge.setText(f"📊 수렴 안정 ±{std:.1f}%p  ✅")
                self._lbl_converge.setStyleSheet("color:#2ecc71; font-size:11px;")
            else:
                self._lbl_converge.setText(f"📊 수렴 진행 중 ±{std:.1f}%p")
                self._lbl_converge.setStyleSheet(f"color:{C_SUBTEXT}; font-size:11px;")
        # 이전 실행 델타
        prev = SimWorker._last_intercept_rate
        if prev >= 0 and len(self._rates_history) >= 5:
            import numpy as _np
            cur = _np.mean(self._rates_history[-5:])
            diff = (cur - prev) * 100
            sign = "↑" if diff > 0 else "↓"
            col  = '#2ecc71' if diff > 0 else '#e74c3c'
            self._lbl_delta.setText(f"이전 대비 {sign}{abs(diff):.1f}%p")
            self._lbl_delta.setStyleSheet(f"color:{col}; font-size:11px;")

    def update_phases(self, phase_times: dict):
        """MC 배치 완료마다 단계별 타이밍 바 갱신."""
        if not phase_times:
            return
        total_t = sum(phase_times.values()) or 1.0
        for key, (bar, val_lbl) in self._phase_bars.items():
            v = phase_times.get(key, 0.0)
            bar.setValue(int(v / total_t * 1000))
            ms = v * 1000
            val_lbl.setText(f"{ms:.1f}ms" if ms < 1000 else f"{v:.2f}s")
            # 병목(가장 느린 단계) 강조
            is_bottleneck = (v == max(phase_times.values()))
            bar.setStyleSheet(self._bar_css('#e74c3c' if is_bottleneck else '#3498db'))

    # ── show / close ─────────────────────────────────────────────────────────
    def show(self):
        super().show()
        self._show_time = time.time()
        self._batch_rates.clear()
        self._rates_history.clear()
        self._log_buf.clear()
        self._mc_done = 0
        self._mc_t0   = 0.0
        self._stack_mode.setCurrentIndex(0)
        for sq in self._spark_boxes:
            sq.setStyleSheet(f"background:{C_BORDER}; border-radius:2px;")
        for lbl in self._log_labels:
            lbl.setText("")
        self._lbl_converge.setText("수렴  분석 중…")
        self._lbl_converge.setStyleSheet(f"color:{C_SUBTEXT}; font-size:11px;")
        self._lbl_delta.setText("")
        self._timer.start()
        self._refresh_tick()

    def close(self):
        self._timer.stop()
        super().close()

    # ── 드래그 이동 ──────────────────────────────────────────────────────────
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None


# ════════════════════════════════════════════════════════════════════════════
#  실행 로그 뷰어 다이얼로그
# ════════════════════════════════════════════════════════════════════════════
#  v10.7: 전술 의사결정 다이얼로그
# ════════════════════════════════════════════════════════════════════════════
class TacticalDialog(QDialog):
    """전술 의사결정 — 시뮬 일시정지 시 위협 현황 + 무기 선택 패널."""

    def __init__(self, state: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"⚔️  전술 의사결정  —  T={state['t']:.0f}s")
        self.setMinimumWidth(520)
        self.setModal(True)
        self._choice = {}

        layout = QVBoxLayout(self)
        layout.setSpacing(8)

        # ── 현황 요약 ─────────────────────────────────────────────────────────
        hdr = QLabel(f"<b>T = {state['t']:.0f}s</b>  |  "
                     f"요격 {state['intercepted']}/{state['total_threats']}  |  "
                     f"발사 {state['shots_fired']}발")
        hdr.setStyleSheet(f"color:{C_ACCENT}; font-size:14px; padding:4px;")
        layout.addWidget(hdr)

        # 위협 목록
        threats = state.get('threats', [])
        if threats:
            tlbl = QLabel(f"현존 위협 {len(threats)}개:")
            tlbl.setStyleSheet(f"color:{C_TEXT}; font-size:12px;")
            layout.addWidget(tlbl)
            tbl = QTableWidget(len(threats), 4)
            tbl.setHorizontalHeaderLabels(["명칭", "유형", "HP", "거리(km)"])
            tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            tbl.setColumnWidth(1, 70); tbl.setColumnWidth(2, 40); tbl.setColumnWidth(3, 70)
            tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            tbl.setMaximumHeight(120)
            for r, t in enumerate(threats):
                for c, v in enumerate([t['name'], t['type'], str(t['hp']), str(t['dist_km'])]):
                    item = QTableWidgetItem(v)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    tbl.setItem(r, c, item)
            layout.addWidget(tbl)

        # 아군 함정 상태
        ships = state.get('ships', [])
        if ships:
            slbl = QLabel("아군 함정 상태:")
            slbl.setStyleSheet(f"color:{C_TEXT}; font-size:12px;")
            layout.addWidget(slbl)
            stbl = QTableWidget(len(ships), 4)
            stbl.setHorizontalHeaderLabels(["함정", "HP", "레이더", "속도"])
            stbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
            stbl.setColumnWidth(1, 40); stbl.setColumnWidth(2, 60); stbl.setColumnWidth(3, 60)
            stbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
            stbl.setMaximumHeight(100)
            for r, s in enumerate(ships):
                alive_mark = "✅" if s['alive'] else "❌"
                for c, v in enumerate([f"{alive_mark} {s['name']}",
                                        f"{s['hp']}/{s['max_hp']}",
                                        f"{s['radar']:.0%}",
                                        f"{s['speed']:.0%}"]):
                    item = QTableWidgetItem(v)
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    stbl.setItem(r, c, item)
            layout.addWidget(stbl)

        # ── 전술 선택 ─────────────────────────────────────────────────────────
        sep = QFrame(); sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)

        opt_lbl = QLabel("다음 구간 무기 우선순위:")
        opt_lbl.setStyleSheet(f"color:{C_TEXT}; font-weight:bold;")
        layout.addWidget(opt_lbl)

        self._wpn_group = QButtonGroup(self)
        wpn_row = QHBoxLayout()
        for label, val in [("자동 (기본)", "auto"), ("SM-2", "SM-2 Block IIIB"),
                            ("SM-6", "SM-6"), ("ESSM", "ESSM Block II")]:
            rb = QRadioButton(label)
            rb.setStyleSheet(f"color:{C_TEXT};")
            rb.setProperty("wpn_val", val)
            if val == "auto":
                rb.setChecked(True)
            self._wpn_group.addButton(rb)
            wpn_row.addWidget(rb)
        layout.addLayout(wpn_row)

        salvo_row = QHBoxLayout()
        _salvo_lbl = QLabel("살보 수:")
        _salvo_lbl.setToolTip(
            "다음 구간 최대 살보 수 설정.\n"
            "HGV·탄도탄 등 고위협 표적은 위협별 최솟값(2~3발)이\n"
            "자동으로 보장됩니다 (설정값이 최솟값보다 낮아도 무시)."
        )
        salvo_row.addWidget(_salvo_lbl)
        self._spn_salvo = QSpinBox()
        self._spn_salvo.setRange(1, 3)
        self._spn_salvo.setValue(1)
        self._spn_salvo.setFixedWidth(60)
        self._spn_salvo.setToolTip(
            "1: 탄약 절약 (저위협 상황)\n"
            "2: 표준 (Shoot-Look-Shoot)\n"
            "3: 최대 화력 (HGV·포화공격 대응)\n"
            "※ HGV는 자동으로 최소 3발 보장"
        )
        salvo_row.addWidget(self._spn_salvo)
        salvo_row.addStretch()
        layout.addLayout(salvo_row)

        # ── 버튼 ──────────────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_cont = QPushButton("▶  계속 진행")
        btn_cont.setStyleSheet(
            f"background:{C_ACCENT}; color:white; font-weight:bold; padding:6px 20px;")
        btn_cont.clicked.connect(self._on_continue)
        btn_row.addStretch(); btn_row.addWidget(btn_cont)
        layout.addLayout(btn_row)

    def _on_continue(self):
        checked = self._wpn_group.checkedButton()
        self._choice = {
            'weapon_priority': checked.property("wpn_val") if checked else 'auto',
            'max_salvo':       self._spn_salvo.value(),
        }
        self.accept()

    def get_choice(self) -> dict:
        return self._choice


# ════════════════════════════════════════════════════════════════════════════
class SimLogDialog(QDialog):
    """sim_history.db (SQLite)를 읽어 테이블로 표시하는 독립 창."""

    restore_requested = pyqtSignal(dict)   # cfg_json 딕셔너리 emit

    _COLS = [
        ('날짜/시각',    'datetime',           180),
        ('편대',         'fleet',              140),
        ('날씨',         'weather',            110),
        ('모드',         'sim_mode',            55),
        ('MC',           'mc_n',                55),
        ('총 위협',      'total_threats',       70),
        ('요격률',       'mean_intercept',      80),
        ('±',            'std_intercept',       60),
        ('완전요격',     'full_pass_rate',      75),
        ('CVaR',         'cvar',                70),
        ('REQ',          'req_pass',            50),
        ('아군 피격',    'avg_friendly_hits',   75),
        ('비용 ($M)',    'total_cost',          90),
        ('적군 구성',    'enemy',                0),   # 0 = stretch
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._records: list = []   # BUG-1: textChanged가 _load() 전에 발화하면 AttributeError
        self.setWindowTitle("실행 로그 뷰어")
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, True)
        self.resize(1300, 620)
        self.setStyleSheet(
            f"QWidget {{ background:{C_BG}; color:{C_TEXT}; "
            f"font-family:'Malgun Gothic','Segoe UI'; font-size:13px; }}"
            f"QHeaderView::section {{ background:{C_PANEL}; color:{C_ACCENT}; "
            f"border:none; padding:5px; font-size:13px; }}"
            f"QTableWidget {{ background:{C_PANEL}; gridline-color:{C_BORDER}; border:none; }}"
            f"QScrollBar:vertical {{ width:6px; background:{C_BG}; }}"
            f"QScrollBar::handle:vertical {{ background:{C_BORDER}; border-radius:3px; }}"
            f"QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}"
        )
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(8)

        # ── 상단 툴바 ──────────────────────────────────────────────────────
        bar = QHBoxLayout()
        bar.setSpacing(8)

        self._search = QLineEdit()
        self._search.setPlaceholderText("🔍  날짜·편대·날씨·적군 검색…")
        self._search.setFixedHeight(28)
        self._search.setStyleSheet(
            f"background:{C_PANEL}; color:{C_TEXT}; border:1px solid {C_BORDER};"
            f" border-radius:4px; padding:0 8px;"
        )
        self._search.textChanged.connect(self._apply_filter)

        btn_refresh = QPushButton("새로고침")
        btn_refresh.setFixedHeight(28)
        btn_refresh.setStyleSheet(
            f"QPushButton {{ background:{C_PANEL}; color:{C_SUBTEXT}; border:1px solid {C_BORDER};"
            f" border-radius:4px; padding:0 12px; }}"
            f"QPushButton:hover {{ color:{C_TEXT}; }}"
        )
        btn_refresh.clicked.connect(self._load)

        btn_csv = QPushButton("CSV 내보내기")
        btn_csv.setFixedHeight(28)
        btn_csv.setStyleSheet(btn_refresh.styleSheet())
        btn_csv.clicked.connect(self._export_csv)

        self._btn_restore = QPushButton("⬅  설정 복원")
        self._btn_restore.setFixedHeight(28)
        self._btn_restore.setEnabled(False)
        self._btn_restore.setStyleSheet(
            f"QPushButton {{ background:{C_PANEL}; color:{C_ACCENT}; border:1px solid #1a3a5c;"
            f" border-radius:4px; padding:0 12px; }}"
            f"QPushButton:hover {{ background:#0a1a2a; }}"
            f"QPushButton:disabled {{ color:{C_SUBTEXT}; border-color:{C_BORDER}; }}"
        )
        self._btn_restore.clicked.connect(self._restore_selected)

        btn_clear = QPushButton("로그 초기화")
        btn_clear.setFixedHeight(28)
        btn_clear.setStyleSheet(
            f"QPushButton {{ background:{C_PANEL}; color:#e74c3c; border:1px solid #5c1a1a;"
            f" border-radius:4px; padding:0 12px; }}"
            f"QPushButton:hover {{ background:#2a1010; }}"
        )
        btn_clear.clicked.connect(self._clear_log)

        self._lbl_count = QLabel("")
        self._lbl_count.setStyleSheet(f"color:{C_SUBTEXT}; font-size:12px;")

        bar.addWidget(self._search, stretch=1)
        bar.addWidget(btn_refresh)
        bar.addWidget(self._btn_restore)
        bar.addWidget(btn_csv)
        bar.addWidget(btn_clear)
        bar.addWidget(self._lbl_count)
        root.addLayout(bar)

        # ── 테이블 ─────────────────────────────────────────────────────────
        self._tbl = QTableWidget()
        self._tbl.setColumnCount(len(self._COLS))
        self._tbl.setHorizontalHeaderLabels([c[0] for c in self._COLS])
        self._tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._tbl.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._tbl.setAlternatingRowColors(True)
        self._tbl.verticalHeader().setDefaultSectionSize(26)
        self._tbl.verticalHeader().setVisible(False)
        self._tbl.setStyleSheet(
            f"QTableWidget {{ alternate-background-color: #111720; }}"
            f"QTableWidget::item:selected {{ background:{C_ACCENT}33; color:{C_TEXT}; }}"
        )
        hh = self._tbl.horizontalHeader()
        hh.setSortIndicatorShown(True)
        hh.setSectionsClickable(True)
        for i, (_, _, w) in enumerate(self._COLS):
            if w == 0:
                hh.setSectionResizeMode(i, QHeaderView.ResizeMode.Stretch)
            else:
                hh.setSectionResizeMode(i, QHeaderView.ResizeMode.Interactive)
                self._tbl.setColumnWidth(i, w)
        self._tbl.setSortingEnabled(True)

        # ── 하단 상세 패널 ─────────────────────────────────────────────────
        self._detail = QLabel("← 행을 선택하면 상세 정보가 표시됩니다.")
        self._detail.setWordWrap(True)
        self._detail.setStyleSheet(
            f"background:{C_PANEL}; color:{C_SUBTEXT}; font-size:13px;"
            f" border:1px solid {C_BORDER}; border-radius:4px; padding:8px 12px;"
        )
        self._detail.setFixedHeight(72)

        self._tbl.currentRowChanged.connect(self._show_detail)
        self._tbl.currentRowChanged.connect(
            lambda row: self._btn_restore.setEnabled(row >= 0))

        root.addWidget(self._tbl, stretch=1)
        root.addWidget(self._detail)

    # ── 데이터 처리 ────────────────────────────────────────────────────────
    def _load(self):
        self._records = _load_sim_db()   # SQLite — 이미 최신순(DESC)
        self._apply_filter(self._search.text())

    def _apply_filter(self, text: str):
        kw = text.strip().lower()
        filtered = [
            r for r in self._records
            if not kw or any(kw in str(v).lower() for v in r.values())
        ]
        self._fill_table(filtered)
        self._lbl_count.setText(f"총 {len(filtered)}건")

    def _fill_table(self, records: list):
        tbl = self._tbl
        tbl.setSortingEnabled(False)
        tbl.setUpdatesEnabled(False)
        try:
            tbl.setRowCount(len(records))
            for row, rec in enumerate(records):
                cvar = rec.get('cvar')
                req  = rec.get('req_pass')
                values = [
                    rec.get('datetime', ''),
                    rec.get('fleet', ''),
                    rec.get('weather', ''),
                    rec.get('sim_mode', '—'),
                    str(rec.get('mc_n', '')),
                    str(rec.get('total_threats', '')),
                    f"{rec.get('mean_intercept', 0):.1%}",
                    f"±{rec.get('std_intercept', 0):.1%}",
                    f"{rec.get('full_pass_rate', 0):.1%}",
                    f"{cvar:.1%}" if cvar is not None else '—',
                    ('✅' if req == 1 else '❌' if req == 0 else '—'),
                    f"{rec.get('avg_friendly_hits', 0):.1f}",
                    f"{rec.get('total_cost', 0) / 1e6:.1f}",
                    rec.get('enemy', ''),
                ]
                last_col = len(self._COLS) - 1
                for col, val in enumerate(values):
                    item = QTableWidgetItem(val)
                    item.setTextAlignment(
                        Qt.AlignmentFlag.AlignCenter
                        if col != last_col
                        else Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
                    if col == 6:
                        rate = rec.get('mean_intercept', 0)
                        item.setForeground(QColor(
                            C_GREEN if rate >= 0.8 else
                            '#f39c12' if rate >= 0.5 else
                            '#e74c3c'))
                    if col == 9 and cvar is not None:
                        item.setForeground(QColor(
                            C_GREEN if cvar >= 0.7 else
                            '#f39c12' if cvar >= 0.4 else
                            '#e74c3c'))
                    tbl.setItem(row, col, item)
                tbl.item(row, 0).setData(Qt.ItemDataRole.UserRole, rec)
        finally:
            tbl.setUpdatesEnabled(True)
            tbl.setSortingEnabled(True)

    def _show_detail(self, row: int):
        if row < 0:
            return
        item = self._tbl.item(row, 0)
        if not item:
            return
        rec = item.data(Qt.ItemDataRole.UserRole)
        if not rec:
            return
        cvar = rec.get('cvar')
        req  = rec.get('req_pass')
        cvar_str = f"{cvar:.1%}" if cvar is not None else '—'
        req_str  = ('✅ PASS' if req == 1 else '❌ FAIL' if req == 0 else '—')
        self._detail.setText(
            f"<b>{rec.get('datetime','')}</b> &nbsp;|&nbsp; "
            f"편대: <b>{rec.get('fleet','')}</b> &nbsp;|&nbsp; "
            f"날씨: {rec.get('weather','')} &nbsp;|&nbsp; "
            f"모드: {rec.get('sim_mode','—')} / MC: {rec.get('mc_n','')}회 &nbsp;|&nbsp; "
            f"위협: {rec.get('total_threats','')}발/기<br>"
            f"요격률: <b>{rec.get('mean_intercept',0):.1%}</b> "
            f"(±{rec.get('std_intercept',0):.1%}) &nbsp;|&nbsp; "
            f"완전요격: {rec.get('full_pass_rate',0):.1%} &nbsp;|&nbsp; "
            f"CVaR: {cvar_str} &nbsp;|&nbsp; REQ: {req_str} &nbsp;|&nbsp; "
            f"비용: ${rec.get('total_cost',0):,.0f}<br>"
            f"<span style='color:{C_SUBTEXT}'>적군: {rec.get('enemy','')}</span>"
        )

    def _restore_selected(self):
        row = self._tbl.currentRow()
        if row < 0:
            return
        item = self._tbl.item(row, 0)
        if not item:
            return
        rec = item.data(Qt.ItemDataRole.UserRole)
        if not rec:
            return
        cfg_str = rec.get('cfg_json', '')
        if not cfg_str:
            QMessageBox.warning(self, "복원 불가", "이 기록에는 설정 정보가 없습니다.")
            return
        try:
            cfg = json.loads(cfg_str)
        except Exception:
            QMessageBox.warning(self, "복원 오류", "설정 JSON 파싱 실패.")
            return
        self.restore_requested.emit(cfg)
        self.accept()

    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "CSV 저장", "sim_history.csv", "CSV (*.csv)")
        if not path:
            return
        try:
            import csv
            with open(path, 'w', newline='', encoding='utf-8-sig') as f:
                w = csv.DictWriter(f, fieldnames=list(self._records[0].keys()) if self._records else [])
                w.writeheader()
                w.writerows(list(reversed(self._records)))
            QMessageBox.information(self, "내보내기 완료", f"저장됨:\n{path}")
        except Exception as e:
            QMessageBox.warning(self, "오류", str(e))

    def _clear_log(self):
        if QMessageBox.question(
            self, "로그 초기화",
            "모든 실행 기록을 삭제하시겠습니까?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        ) != QMessageBox.StandardButton.Yes:
            return
        _clear_sim_db()
        # 레거시 JSON/텍스트 로그도 함께 초기화
        _save_json_log([])
        try:
            open(_log_path(), 'w', encoding='utf-8').close()
        except Exception:
            pass
        self._load()


# ════════════════════════════════════════════════════════════════════════════
#  백그라운드 시뮬레이션 워커
# ════════════════════════════════════════════════════════════════════════════
class SensitivityWorker(QThread):
    """감도 분석 MC를 백그라운드에서 실행 후 결과 전달."""
    finished = pyqtSignal(list, list, list, float)  # (labels, lows, highs, base_rate)
    error    = pyqtSignal(str)

    def __init__(self, cfg: dict, mc_n: int):
        super().__init__()
        self.cfg  = cfg
        self.mc_n = max(50, mc_n // 5)

    def run(self):
        if not _V7_OK:
            return
        try:
            params = [
                ('C&D 시간',  'cd_time_s',      5, 20),
                ('확인 시간', 'confirm_time_s',  1, 10),
                ('시뮬 시드', 'sim_seed',         1, 42),
            ]
            base_mc   = monte_carlo_v7(self.cfg, self.mc_n)
            base_rate = base_mc['mean_intercept']
            labels, lows, highs = [], [], []
            for name, key, lo_val, hi_val in params:
                r_lo = monte_carlo_v7({**self.cfg, key: lo_val}, self.mc_n)['mean_intercept']
                r_hi = monte_carlo_v7({**self.cfg, key: hi_val}, self.mc_n)['mean_intercept']
                labels.append(f"{name}\n({lo_val}→{hi_val})")
                lows.append(r_lo - base_rate)
                highs.append(r_hi - base_rate)
            self.finished.emit(labels, lows, highs, base_rate)
        except Exception as e:
            self.error.emit(str(e))


class MinStockWorker(QThread):
    """REQ 달성 최소 재고 역산을 백그라운드에서 실행."""
    progress = pyqtSignal(int, int, str)    # (i, total, weapon_name)
    finished = pyqtSignal(dict, float)      # (results_dict, target_rate)
    error    = pyqtSignal(str)

    def __init__(self, cfg: dict, mc_n: int, target_rate: float = 0.90):
        super().__init__()
        self.cfg         = cfg
        self.mc_n        = max(20, mc_n // 8)  # 속도 우선 — 근사치 허용
        self.target_rate = target_rate

    def run(self):
        if not _V7_OK:
            return
        try:
            def _cb(i, total, name):
                self.progress.emit(i, total, name)
            results = find_all_min_stocks_v7(
                self.cfg, self.target_rate, self.mc_n, _cb)
            self.finished.emit(results, self.target_rate)
        except Exception as e:
            self.error.emit(str(e))


class OptimizeWorker(QThread):
    """최적 무기 조합 탐색을 백그라운드에서 실행."""
    progress = pyqtSignal(int, int, str)   # (done, total, phase)
    finished = pyqtSignal(list)            # results list
    error    = pyqtSignal(str)

    def __init__(self, cfg: dict, budget: int = 64, step: int = 16):
        super().__init__()
        self.cfg    = cfg
        self.budget = budget
        self.step   = step

    def run(self):
        if not _V7_OK:
            return
        try:
            def _cb(i, total, phase):
                self.progress.emit(i, total, phase)
            results = optimize_weapon_loadout_v7(
                self.cfg, budget=self.budget, step=self.step,
                coarse_n=20, fine_n=200, progress_cb=_cb)
            self.finished.emit(results)
        except Exception as e:
            self.error.emit(str(e))


class WeatherWorker(QThread):
    """날씨별 비교 MC를 백그라운드에서 실행."""
    finished = pyqtSignal(dict)
    error    = pyqtSignal(str)

    def __init__(self, cfg: dict, n: int = 1000):
        super().__init__()
        self.cfg = cfg
        self.n   = n

    def run(self):
        if not _V7_OK:
            return
        try:
            sc = scenario_comparison_v7(self.cfg, n=self.n)
            self.finished.emit(sc)
        except Exception as e:
            self.error.emit(str(e))


class ABCompareWorker(QThread):
    """A/B 편대 비교 MC를 백그라운드에서 실행."""
    finished = pyqtSignal(dict)
    error    = pyqtSignal(str)

    def __init__(self, cfg_a: dict, cfg_b: dict, n: int = 500):
        super().__init__()
        self.cfg_a = cfg_a
        self.cfg_b = cfg_b
        self.n     = n

    def run(self):
        if not _V7_OK:
            return
        try:
            result = compare_ab_v7(self.cfg_a, self.cfg_b, n=self.n)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class CECCompareWorker(QThread):
    """CEC ON/OFF/두절 3종 비교 MC를 백그라운드에서 실행."""
    finished = pyqtSignal(dict)
    error    = pyqtSignal(str)

    def __init__(self, cfg: dict, n: int = 500):
        super().__init__()
        self.cfg = cfg
        self.n   = n

    def run(self):
        if not _V7_OK:
            return
        try:
            result = cec_comparison_v7(self.cfg, n=self.n)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class HeatmapWorker(QThread):
    """편대 × 위협 2D 생존성 히트맵 MC — 각 셀마다 monte_carlo_lhs 실행."""
    cell_done = pyqtSignal(int, int, float)   # (row, col, mean_intercept)
    finished  = pyqtSignal(list)              # list[list[float]]  rows×cols
    error     = pyqtSignal(str)

    def __init__(self, base_cfg: dict, fleet_presets: list[str],
                 enemy_presets: list[str], n: int = 200):
        super().__init__()
        self.base_cfg      = base_cfg
        self.fleet_presets = fleet_presets   # Y 축 (행)
        self.enemy_presets = enemy_presets   # X 축 (열)
        self.n             = n

    def run(self):
        if not _V7_OK:
            return
        try:
            rows, cols = len(self.fleet_presets), len(self.enemy_presets)
            grid = [[0.0] * cols for _ in range(rows)]
            for r, fp in enumerate(self.fleet_presets):
                for c, ep in enumerate(self.enemy_presets):
                    if self.isInterruptionRequested():
                        return
                    cfg = dict(self.base_cfg)
                    cfg['fleet_preset']       = fp
                    cfg['enemy_fleet_mode']   = 'preset'
                    cfg['enemy_fleet_preset'] = ep
                    mc = monte_carlo_lhs(cfg, n=self.n)
                    val = float(mc.get('mean_intercept', 0.0))
                    grid[r][c] = val
                    self.cell_done.emit(r, c, val)
            self.finished.emit(grid)
        except Exception as e:
            self.error.emit(str(e))


class SimWorker(QThread):
    progress        = pyqtSignal(str)
    progress_detail = pyqtSignal(int, int, float)  # (현재, 전체, ETA초)
    finished        = pyqtSignal(dict, dict)
    error           = pyqtSignal(str)
    sim_started     = pyqtSignal()
    sim_ended       = pyqtSignal()
    batch_done      = pyqtSignal(int, int)         # (완료배치, 전체배치)
    rate_update     = pyqtSignal(float, float, float)  # (mean_rate, avg_e_dest, avg_f_hits)
    # v8.26: 진행 팝업 상세화
    step_update     = pyqtSignal(float, float, int, int, str)  # (t, t_max, alive, vls, last_log) — 단일 시뮬
    phase_update     = pyqtSignal(dict)                         # 단계별 평균 타이밍 — MC 배치 완료마다
    # v10.7: 전술 의사결정 모드
    tactical_pause   = pyqtSignal(dict)                         # TacticalState 스냅샷 → 다이얼로그 표시

    _last_intercept_rate: float = -1.0   # 이전 실행 결과 캐시 (클래스 변수)

    def __init__(self, cfg: dict, mc_n: int, precision_mode: bool = False,
                 sobol_npp: int = 3, sim_mode_idx: int = 1):
        super().__init__()
        self.cfg            = cfg
        self.mc_n           = mc_n
        self.precision_mode = precision_mode
        self.sobol_npp      = sobol_npp
        self.sim_mode_idx   = sim_mode_idx
        # v10.7: 전술 모드 동기화 객체
        import threading, queue as _queue
        self._tactical_event  = threading.Event()
        self._tactical_queue  = _queue.Queue()

    def _tactical_pause_cb(self, state) -> dict:
        """엔진 훅 — 워커 스레드에서 호출. 메인 스레드에 상태 전달 후 블록."""
        import dataclasses
        snap = dataclasses.asdict(state)
        self._tactical_event.clear()
        self.tactical_pause.emit(snap)     # queued signal → main thread
        self._tactical_event.wait()        # block until user confirms
        choice = self._tactical_queue.get_nowait() if not self._tactical_queue.empty() else {}
        return choice

    def resume_tactical(self, choice: dict):
        """메인 스레드에서 호출 — 사용자 선택 전달 후 워커 재개."""
        self._tactical_queue.put(choice)
        self._tactical_event.set()

    def run(self):
        try:
            self.sim_started.emit()
            self.progress.emit("시뮬레이션 실행 중...")

            def _step_cb(t, t_max, alive, vls, last_log):
                self.step_update.emit(t, t_max, alive, vls, last_log)

            # v10.7: 전술 모드 훅 주입
            _tactical_hook = None
            if self.cfg.get('tactical_mode', False):
                _tactical_hook = self._tactical_pause_cb

            result = run_v7_simulation(self.cfg, step_cb=_step_cb,
                                       tactical_cb=_tactical_hook)
            self.progress.emit(f"MC {self.mc_n}회 분석 중...")
            t0 = time.time()

            def _cb(done, total):
                elapsed = time.time() - t0
                eta = (elapsed / done * (total - done)) if done > 0 else 0.0
                self.progress_detail.emit(done, total, eta)
                self.progress.emit(f"MC {done}/{total}회 | 잔여 약 {eta:.0f}초")

            n_cores = min(os.cpu_count() or 1, 8)
            if not _V7_OK or self.mc_n < 100 or n_cores <= 1:
                # 소규모 or 단일코어 — 순차 실행
                try:
                    mc = monte_carlo_v7(self.cfg, n=self.mc_n, progress_cb=_cb)
                except TypeError:
                    mc = monte_carlo_v7(self.cfg, n=self.mc_n)
            else:
                # 멀티프로세싱 병렬 MC
                batch_size = max(10, self.mc_n // n_cores)
                batches, seed_offset = [], 0
                while seed_offset < self.mc_n:
                    actual = min(batch_size, self.mc_n - seed_offset)
                    batches.append((self.cfg, actual, seed_offset))
                    seed_offset += actual

                all_rates, all_f_hits, all_e_dest = [], [], []
                all_f_lost, all_costs = [], []
                all_weapon: dict = {}
                all_ship:   dict = {}
                all_wzero:  dict = {}
                done_count = 0

                pool = _GLOBAL_POOL or ProcessPoolExecutor(max_workers=n_cores)
                _own = _GLOBAL_POOL is None
                if _own:
                    _set_pool_priority(pool)  # BUG-1: 인라인 풀도 BELOW_NORMAL
                batch_done_n = 0
                _phase_acc: dict = {}   # v8.26: 배치별 단계 타이밍 누적
                futs = {pool.submit(_mc_batch_worker, b): b for b in batches}
                for fut in as_completed(futs):
                    if self.isInterruptionRequested():
                        for f in futs:
                            f.cancel()
                        if _own:
                            pool.shutdown(wait=False)
                        return
                    rates, fh, ed, fl, cs, wu, sh, wz, pt = fut.result()
                    all_rates.extend(rates);  all_f_hits.extend(fh)
                    all_e_dest.extend(ed);    all_f_lost.extend(fl)
                    all_costs.extend(cs)
                    for k, v in wu.items(): all_weapon.setdefault(k, []).extend(v)
                    for k, v in sh.items(): all_ship.setdefault(k, []).extend(v)
                    for k, v in wz.items(): all_wzero[k] = all_wzero.get(k, 0) + v
                    for k, v in pt.items(): _phase_acc[k] = _phase_acc.get(k, 0.0) + v
                    done_count += len(rates)
                    batch_done_n += 1
                    self.batch_done.emit(batch_done_n, len(batches))
                    _cb(done_count, self.mc_n)
                    if all_rates:
                        self.rate_update.emit(
                            float(np.mean(all_rates)),
                            float(np.mean(all_e_dest)) if all_e_dest else 0.0,
                            float(np.mean(all_f_hits)) if all_f_hits else 0.0,
                        )
                    if _phase_acc:
                        _n_b = max(batch_done_n, 1)
                        self.phase_update.emit({k: v / _n_b for k, v in _phase_acc.items()})
                if _own:
                    pool.shutdown(wait=False)

                arr = np.array(all_rates)
                _n_total = max(len(all_rates), 1)
                mc = {
                    'intercept_rates':         all_rates,
                    'friendly_hits':           all_f_hits,
                    'enemy_destroyed':         all_e_dest,
                    'friendly_lost':           all_f_lost,
                    'total_costs':             all_costs,
                    'weapon_avg_remaining':    {k: float(np.mean(v)) for k, v in all_weapon.items()},
                    'weapon_exhaustion_rates': {k: v / _n_total for k, v in all_wzero.items()},
                    'ship_avg_hits':           {k: float(np.mean(v)) for k, v in all_ship.items()},
                    'mean_intercept':          float(arr.mean()),
                    'std_intercept':           float(arr.std()),
                    'full_pass_rate':          float((arr == 1.0).mean()),
                    'n':                       len(all_rates),
                }

            # ── CVaR: 기존 MC rates에서 직접 계산 (추가 시뮬 불필요) ─────────
            if _V7_OK:
                try:
                    mc['cvar'] = compute_cvar(mc.get('intercept_rates', []))
                except Exception:
                    mc['cvar'] = 0.0

            # ── LHS 파라미터 불확실성 분석 (중간 규모, 병렬 MC와 별개) ────────
            # 빠름=1,000  표준=2,000  정밀=10,000
            lhs_result = {}
            if _V7_OK:
                lhs_n_map  = {5_000: 1_000, 10_000: 2_000, 100_000: 10_000}
                lhs_n      = lhs_n_map.get(self.mc_n, 2_000)
                self.progress.emit(f"LHS 파라미터 불확실성 분석 중... ({lhs_n:,}회)")
                lhs_t0 = time.time()

                def _lhs_cb(done, total):
                    if done % max(1, total // 10) == 0:
                        ela = time.time() - lhs_t0
                        eta = ela / done * (total - done) if done > 0 else 0
                        self.progress.emit(f"LHS {done:,}/{total:,} | 잔여 {eta:.0f}초")

                try:
                    lhs_result = monte_carlo_lhs(self.cfg, n=lhs_n, progress_cb=_lhs_cb)
                except Exception as ex:
                    lhs_result = {'error': str(ex)}

            # ── 스트레스 테스트 (모든 모드, n_per_cell 가변) ─────────────────
            stress_result = {}
            if _V7_OK:
                n_cell_map = {5_000: 300, 10_000: 500, 100_000: 3_000}
                n_per_cell = n_cell_map.get(self.mc_n, 500)
                total_stress = len(STRESS_DIMS['channel_degrade']['values']) * \
                               len(STRESS_DIMS['radar_degrade']['values'])
                self.progress.emit(f"스트레스 테스트 중... (셀당 {n_per_cell}회, 총 {total_stress}셀)")

                def _stress_cb(done, total):
                    self.progress.emit(f"스트레스 테스트 {done}/{total} 셀 완료")

                try:
                    stress_result = stress_test_grid(
                        self.cfg, n_per_cell=n_per_cell, progress_cb=_stress_cb)
                except Exception as ex:
                    stress_result = {'error': str(ex)}

            # ── Sobol 민감도 분석 (정밀 모드 전용) ──────────────────────────
            sobol_result = {}
            if _V7_OK and self.precision_mode:
                npp        = self.sobol_npp
                total_est  = 32_768 * npp
                self.progress.emit(
                    f"Sobol 민감도 분석 중... (포인트당 {npp}회, 총 ~{total_est:,}회, 수 분 소요)")
                sobol_t0 = time.time()

                def _sobol_cb(done, total):
                    if done % max(1, total // 20) == 0:
                        ela = time.time() - sobol_t0
                        eta = ela / done * (total - done) if done > 0 else 0
                        self.progress.emit(
                            f"Sobol {done:,}/{total:,} 포인트 | 잔여 {eta:.0f}초")

                try:
                    sobol_result = sobol_analysis(
                        self.cfg, n_sobol=4096, n_per_point=npp,
                        progress_cb=_sobol_cb)
                except Exception as ex:
                    sobol_result = {'error': str(ex)}

            mc['lhs']    = lhs_result
            mc['stress'] = stress_result
            mc['sobol']  = sobol_result

            elapsed = time.time() - t0
            rate    = self.mc_n / elapsed if elapsed > 0 else 0.0
            _PERF_HISTORY.append({
                'time':     time.time(),
                'mc_n':     self.mc_n,
                'duration': elapsed,
                'rate':     rate,
            })
            if len(_PERF_HISTORY) > 10:
                _PERF_HISTORY.pop(0)
            # v8.26: 이전 실행 결과 캐싱 (델타 비교용)
            SimWorker._last_intercept_rate = mc.get('mean_intercept', -1.0)
            self.sim_ended.emit()
            self.finished.emit(result, mc)
        except Exception as e:
            self.sim_ended.emit()
            self.error.emit(str(e))


# ════════════════════════════════════════════════════════════════════════════
#  시스템 데이터 백그라운드 워커 (블로킹 I/O를 메인 스레드에서 분리)
# ════════════════════════════════════════════════════════════════════════════
class _SysDataWorker(QThread):
    """nvidia-smi·WMI 등 블로킹 I/O를 1초마다 백그라운드에서 수집, _SYS_CACHE 갱신."""

    def run(self):
        while not self.isInterruptionRequested():
            try:
                cpu   = psutil.cpu_percent(interval=None)
                cores = psutil.cpu_percent(percpu=True, interval=None) or []
                mem   = psutil.virtual_memory()
                swap  = psutil.swap_memory()
                gpu   = _get_gpu_info()      # subprocess — 메인 스레드 블로킹 제거
                ctemp = _get_cpu_temp()      # WMI — 메인 스레드 블로킹 제거
                proc  = psutil.Process()
                proc_ram = proc.memory_info().rss / 1024**2
                stats: list = []
                try:
                    for c in proc.children(recursive=True):
                        try:
                            stats.append({
                                'pid':    c.pid,
                                'cpu':    c.cpu_percent(interval=None),
                                'ram':    c.memory_info().rss / 1024**2,
                                'status': c.status(),
                            })
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass
                except Exception:
                    pass
                _SYS_CACHE.update({
                    'cpu': cpu, 'mem_pct': mem.percent,
                    'mem_used': mem.used, 'mem_total': mem.total,
                    'gpu': gpu, 'cpu_temp': ctemp,
                    'cores': list(cores), 'proc_ram': proc_ram,
                    'worker_stats': stats, 'swap_used': swap.used,
                    'thread_cnt': threading.active_count(),
                })
            except Exception:
                pass
            self.msleep(1000)


_SYS_DATA_WORKER: '_SysDataWorker | None' = None


def _start_sys_data_worker():
    global _SYS_DATA_WORKER
    _SYS_DATA_WORKER = _SysDataWorker()
    _SYS_DATA_WORKER.start()


def _stop_sys_data_worker():
    global _SYS_DATA_WORKER
    if _SYS_DATA_WORKER is not None:
        _SYS_DATA_WORKER.requestInterruption()
        _SYS_DATA_WORKER.quit()
        if not _SYS_DATA_WORKER.wait(1500):
            _SYS_DATA_WORKER.terminate()
            _SYS_DATA_WORKER.wait(300)
        _SYS_DATA_WORKER = None


# ════════════════════════════════════════════════════════════════════════════
#  Matplotlib Canvas 래퍼
# ════════════════════════════════════════════════════════════════════════════
class MplCanvas(FigureCanvas):
    def __init__(self, figsize=(8, 6), facecolor=C_BG):
        self.fig = Figure(figsize=figsize, facecolor=facecolor)
        super().__init__(self.fig)
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Expanding)


# ════════════════════════════════════════════════════════════════════════════
#  차트 백그라운드 렌더 워커 + 위젯 (UI 프리즈 방지)
# ════════════════════════════════════════════════════════════════════════════
class ChartRenderWorker(QThread):
    """matplotlib Figure를 백그라운드 스레드에서 PNG bytes로 렌더링."""
    finished = pyqtSignal(bytes)
    error    = pyqtSignal(str)

    def __init__(self, fn, args, kwargs):
        super().__init__()
        self._fn     = fn
        self._args   = args
        self._kwargs = kwargs

    def run(self):
        try:
            result = self._fn(*self._args, **self._kwargs)
            if isinstance(result, (bytes, bytearray)):
                # 함수가 PNG bytes를 직접 반환 (이중 렌더 없음)
                self.finished.emit(bytes(result))
                return
            fig = result
            buf = io.BytesIO()
            fig.savefig(buf, format='png', bbox_inches='tight',
                        facecolor=fig.get_facecolor(), dpi=CHART_DPI)
            from matplotlib import pyplot as _plt
            _plt.close(fig)
            self.finished.emit(buf.getvalue())
        except Exception as e:
            self.error.emit(str(e))


class ChartPageWidget(QWidget):
    """결과 차트 탭: 로딩 안내 → 렌더 완료 이미지 전환."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._worker: 'ChartRenderWorker | None' = None
        self._raw_pix: 'QPixmap | None' = None
        self._raw_bytes: bytes = b''

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._pane = QStackedWidget()

        # 0 — 로딩
        loading = QWidget()
        loading.setStyleSheet(f"background:{C_BG};")
        ll = QVBoxLayout(loading)
        ll.addStretch()
        self._loading_lbl = QLabel("  차트 렌더링 중…")
        self._loading_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._loading_lbl.setStyleSheet(
            f"color:{C_SUBTEXT}; font-size:15px; font-family:'Malgun Gothic';")
        ll.addWidget(self._loading_lbl)
        ll.addStretch()
        self._pane.addWidget(loading)

        # 1 — 이미지 (비율 유지 스케일)
        self._img_lbl = QLabel()
        self._img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._img_lbl.setStyleSheet(f"background:{C_BG};")
        self._img_lbl.setSizePolicy(QSizePolicy.Policy.Expanding,
                                    QSizePolicy.Policy.Expanding)
        self._pane.addWidget(self._img_lbl)

        layout.addWidget(self._pane)
        self._pane.setCurrentIndex(0)
        self.setSizePolicy(QSizePolicy.Policy.Expanding,
                           QSizePolicy.Policy.Expanding)

    def start_render(self, fn, *args, **kwargs):
        if self._worker and self._worker.isRunning():
            try:
                self._worker.finished.disconnect()
                self._worker.error.disconnect()
            except Exception:
                pass
            self._worker.requestInterruption()
            self._worker.quit()
        self._raw_pix = None
        self._raw_bytes = b''
        self._loading_lbl.setText("  차트 렌더링 중…")
        self._pane.setCurrentIndex(0)
        self._worker = ChartRenderWorker(fn, args, kwargs)
        self._worker.finished.connect(self._on_done)
        self._worker.error.connect(self._on_error)
        self._worker.start(QThread.Priority.LowPriority)

    def stop_worker(self):
        """창 닫기 시 백그라운드 렌더 스레드 정리."""
        w = self._worker
        if w and w.isRunning():
            try:
                w.finished.disconnect()
                w.error.disconnect()
            except Exception:
                pass
            w.requestInterruption()
            w.quit()
            if not w.wait(800):
                w.terminate()
                w.wait(300)

    def _on_done(self, png_bytes: bytes):
        self._raw_bytes = png_bytes
        pix = QPixmap()
        pix.loadFromData(png_bytes)
        self._raw_pix = pix
        self._update_display()
        self._pane.setCurrentIndex(1)

    def _on_error(self, msg: str):
        self._loading_lbl.setText(f"  렌더링 실패: {msg}")

    def _update_display(self):
        if not self._raw_pix or self._raw_pix.isNull():
            return
        w, h = self.width(), self.height()
        if w > 10 and h > 10:
            self._img_lbl.setPixmap(
                self._raw_pix.scaled(w, h,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_display()


# ════════════════════════════════════════════════════════════════════════════
#  교전 분석 렌더 함수
# ════════════════════════════════════════════════════════════════════════════

_LAYER_ORDER = ['SM-3', 'SM-6', 'SM-2', 'ESSM', '해궁', 'RAM', 'CIWS',
                '홍상어', '청상어', 'Mk.46', '기만/회피']

def _classify_weapon(wpn: str) -> str:
    if not wpn:
        return '기타'
    for layer in _LAYER_ORDER:
        if layer in wpn:
            return layer
    if '기만' in wpn or '회피' in wpn:
        return '기만/회피'
    return wpn.split(' ')[0]

def _render_engagement_funnel(active_events: list) -> 'Figure':
    from matplotlib.figure import Figure as _Fig
    fig = _Fig(figsize=(10, 6), facecolor=C_BG)
    ax  = fig.add_subplot(111, facecolor='#0a0e1a')

    if not active_events:
        ax.text(0.5, 0.5, '교전 데이터 없음', ha='center', va='center',
                color=C_SUBTEXT, fontsize=13, transform=ax.transAxes)
        fig.tight_layout()
        return fig

    total = len([e for e in active_events if e.is_active])
    layer_counts: dict = {}
    missed = 0
    for ev in active_events:
        if not ev.is_active:
            continue
        if not ev.intercepted:
            missed += 1
        else:
            key = _classify_weapon(ev.intercept_weapon or '')
            layer_counts[key] = layer_counts.get(key, 0) + 1

    # 레이어 순서대로 정렬
    ordered = [(l, layer_counts[l]) for l in _LAYER_ORDER if l in layer_counts]
    for k, v in layer_counts.items():
        if k not in _LAYER_ORDER:
            ordered.append((k, v))

    labels  = [l for l, _ in ordered] + (['미격추'] if missed else [])
    counts  = [c for _, c in ordered] + ([missed]  if missed else [])
    colors  = [('#2ecc71' if l != '미격추' else '#e74c3c') for l in labels]

    remaining = total
    bar_data   = []
    for lbl, cnt, col in zip(labels, counts, colors):
        bar_data.append((lbl, remaining, cnt, col))
        remaining -= cnt if lbl != '미격추' else 0

    # 가로 Funnel 바
    y_pos = list(range(len(bar_data)))
    for i, (lbl, rem, cnt, col) in enumerate(bar_data):
        ax.barh(i, rem, color='#1e2a3a', height=0.6, edgecolor='none')
        ax.barh(i, cnt, left=rem - cnt, color=col, height=0.6,
                edgecolor='none', alpha=0.85)
        ax.text(rem - cnt / 2, i, f'{cnt}건',
                ha='center', va='center', color='white',
                fontsize=11, fontweight='bold',
                fontfamily='Malgun Gothic')

    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, color=C_TEXT, fontsize=12,
                       fontfamily='Malgun Gothic')
    ax.set_xlabel('위협 수', color=C_SUBTEXT, fontsize=11,
                  fontfamily='Malgun Gothic')
    ax.set_title(f'방어 레이어별 격추 Funnel  (총 {total}건)',
                 color=C_TEXT, fontsize=14, fontfamily='Malgun Gothic')
    ax.tick_params(colors=C_SUBTEXT, labelsize=10)
    ax.set_xlim(0, total + 1)
    for sp in ax.spines.values():
        sp.set_color('#1e2a3a')
    ax.grid(axis='x', color='#1e2a3a', lw=0.5)
    ax.invert_yaxis()
    fig.tight_layout()
    return fig


def _render_engagement_gantt(active_events: list) -> 'Figure':
    from matplotlib.figure import Figure as _Fig
    evs = [e for e in active_events if e.is_active and e.gantt_bars]
    fig_h = max(4, len(evs) * 0.45 + 1.5)
    fig = _Fig(figsize=(14, fig_h), facecolor=C_BG)
    ax  = fig.add_subplot(111, facecolor='#0a0e1a')

    if not evs:
        ax.text(0.5, 0.5, '교전 데이터 없음', ha='center', va='center',
                color=C_SUBTEXT, fontsize=13, transform=ax.transAxes)
        fig.tight_layout()
        return fig

    color_legend = {
        '#2ecc71': '요격 성공', '#e74c3c': '피격/통과',
        '#f39c12': '채널 없음', '#95a5a6': '교전 불가',
        '#16A085': '기만/회피', '#808080': '탐지 중',
    }
    seen_colors: set = set()

    for yi, ev in enumerate(evs):
        for (lbl, t_s, t_e, col) in ev.gantt_bars:
            dur = max(t_e - t_s, 0.5)
            ax.barh(yi, dur, left=t_s, height=0.55, color=col,
                    edgecolor='white', linewidth=0.5, alpha=0.88)
            seen_colors.add(col)
        # 위협 이름 왼쪽 표시
        ax.text(-0.5, yi, ev.label[:18], ha='right', va='center',
                color=C_TEXT, fontsize=8, fontfamily='Malgun Gothic')

    ax.set_yticks(range(len(evs)))
    ax.set_yticklabels([''] * len(evs))
    # B-1: 이름 텍스트가 잘리지 않도록 x축 왼쪽 여백을 이름 최대 길이 기준으로 확보
    max_t = max((max(t_e for _, _, t_e, _ in ev.gantt_bars) for ev in evs), default=100)
    label_chars = max((len(ev.label[:18]) for ev in evs), default=10)
    x_margin = label_chars * 1.2   # 글자당 약 1.2초 여유
    ax.set_xlim(-x_margin, max_t * 1.05)
    ax.set_xlabel('시뮬 시각 (초)', color=C_SUBTEXT, fontsize=11,
                  fontfamily='Malgun Gothic')
    ax.set_title('교전 타임라인 (위협별 교전 구간)',
                 color=C_TEXT, fontsize=14, fontfamily='Malgun Gothic')
    ax.tick_params(colors=C_SUBTEXT, labelsize=10)
    for sp in ax.spines.values():
        sp.set_color('#1e2a3a')
    ax.grid(axis='x', color='#1e2a3a', lw=0.5)
    ax.invert_yaxis()

    handles = [
        __import__('matplotlib.patches', fromlist=['Patch']).Patch(
            facecolor=col, label=lbl, alpha=0.88)
        for col, lbl in color_legend.items()
        if col in seen_colors
    ]
    if handles:
        ax.legend(handles=handles, fontsize=9, facecolor='#0a0e1a',
                  labelcolor=C_TEXT, edgecolor='#1e2a3a',
                  loc='lower right', ncol=3,
                  prop={'family': 'Malgun Gothic', 'size': 9})
    fig.tight_layout()
    return fig


# ════════════════════════════════════════════════════════════════════════════
#  교전 분석 탭
# ════════════════════════════════════════════════════════════════════════════

class EngagementAnalysisTab(QWidget):
    """교전 분석 탭: 방어 Funnel / 위협 추적 테이블 / 교전 타임라인 Gantt"""

    _COL_HEADERS = ["위협명", "유형", "탐지거리(km)", "결과", "격추무기", "격추거리(km)", "격추시각(s)"]
    _TBL_STYLE = (
        "QTableWidget { background:#0d1117; color:#e6edf3; "
        "gridline-color:#21262d; border:none; font-size:13px; "
        "font-family:'Malgun Gothic'; }"
        "QTableWidget::item { padding:4px 8px; }"
        "QHeaderView::section { background:#161b22; color:#7d8590; "
        "font-size:12px; padding:4px; border:none; "
        "border-bottom:1px solid #30363d; font-family:'Malgun Gothic'; }"
        "QTableWidget::item:selected { background:#1f3a5f; }"
    )

    def __init__(self):
        super().__init__()
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)

        tabs = QTabWidget()
        tabs.setStyleSheet(
            f"QTabWidget::pane {{ border:1px solid #30363d; background:{C_BG}; }}"
            f"QTabBar::tab {{ background:#161b22; color:#7d8590; "
            f"padding:6px 14px; font-size:14px; font-family:'Malgun Gothic'; }}"
            f"QTabBar::tab:selected {{ background:{C_BG}; color:{C_ACCENT}; "
            f"border-bottom:2px solid {C_ACCENT}; }}"
        )

        # ── Sub-tab 1: Funnel ──────────────────────────────────────────────
        self._tab_funnel = ChartPageWidget()
        tabs.addTab(self._tab_funnel, "🔻  방어 Funnel")

        # ── Sub-tab 2: 위협 추적 테이블 ────────────────────────────────────
        tbl_widget = QWidget()
        tbl_layout = QVBoxLayout(tbl_widget)
        tbl_layout.setContentsMargins(4, 4, 4, 4)
        self._table = QTableWidget(0, len(self._COL_HEADERS))
        self._table.setHorizontalHeaderLabels(self._COL_HEADERS)
        self._table.setStyleSheet(self._TBL_STYLE)
        self._table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.ResizeToContents)
        self._table.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.ResizeMode.Stretch)
        self._table.verticalHeader().setVisible(False)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows)
        self._table.setAlternatingRowColors(True)
        self._table.setStyleSheet(self._TBL_STYLE +
            "QTableWidget { alternate-background-color:#0f1620; }")
        tbl_layout.addWidget(self._table)
        tabs.addTab(tbl_widget, "📋  위협 추적")

        # ── Sub-tab 3: Gantt ───────────────────────────────────────────────
        self._tab_gantt = ChartPageWidget()
        tabs.addTab(self._tab_gantt, "⏱  교전 타임라인")

        layout.addWidget(tabs)

        # 초기 안내
        self._lbl_empty = QLabel("시뮬레이션을 실행하면 교전 분석이 표시됩니다.")
        self._lbl_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._lbl_empty.setStyleSheet(
            f"color:{C_SUBTEXT}; font-size:14px; font-family:'Malgun Gothic';")
        layout.addWidget(self._lbl_empty)
        tabs.hide()
        self._tabs_widget = tabs

    def load_result(self, result: dict):
        active_events = result.get('active_events', [])
        self._lbl_empty.hide()
        self._tabs_widget.show()

        # Funnel & Gantt — 백그라운드 렌더
        self._tab_funnel.start_render(_render_engagement_funnel, active_events)
        self._tab_gantt.start_render(_render_engagement_gantt, active_events)

        # 위협 추적 테이블 — 메인 스레드 직접 채움
        self._fill_table(active_events)

    def _fill_table(self, active_events: list):
        evs = [e for e in active_events if e.is_active]
        self._table.setRowCount(len(evs))
        for row, ev in enumerate(evs):
            ok      = ev.intercepted
            result_str = '✅ 요격' if ok else '❌ 피격'
            bg      = QColor('#1a3a2a') if ok else QColor('#3a1a1a')

            cells = [
                ev.label,
                ev.enemy_info.get('type', '?'),
                f"{ev.detect_m / 1000:.0f}",
                result_str,
                ev.intercept_weapon or '—',
                f"{ev.intercept_km:.1f}" if ev.intercept_km else '—',
                f"{ev.t_intercepted:.0f}" if ev.t_intercepted else '—',
            ]
            for col, text in enumerate(cells):
                item = QTableWidgetItem(text)
                item.setBackground(bg)
                item.setForeground(QColor(C_TEXT))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self._table.setItem(row, col, item)
        self._table.resizeRowsToContents()

    def stop_worker(self):
        self._tab_funnel.stop_worker()
        self._tab_gantt.stop_worker()


# ════════════════════════════════════════════════════════════════════════════
#  아코디언 사이드바 (v8.26)
# ════════════════════════════════════════════════════════════════════════════
class AccordionSidebar(QWidget):
    """카테고리별 접이식 사이드바 — 검색·배지·마지막 탭 기억 지원."""

    item_selected = pyqtSignal(int)   # 스택 인덱스 emit

    _CATEGORIES = [
        ("⚔", "교전 분석", [
            (0,  "📊  교전 분석"),
            (4,  "📜  교전 로그"),
            (10, "⏱  교전 타임라인"),
            (15, "📊  위협 유형별"),
            (16, "⏰  취약 시간대"),
            (13, "🧭  방위각 취약점"),
        ]),
        ("📊", "통계 / MC", [
            (1,  "📊  MC 통계"),
            (9,  "📈  MC 신뢰구간"),
            (11, "🌪  감도 분석"),
            (19, "🎛  Sobol 민감도"),
            (18, "🔥  스트레스 테스트"),
        ]),
        ("✅", "성능 평가", [
            (2,  "✅  REQ 판정"),
            (14, "🎯  REQ 충족률"),
            (7,  "💰  비용 효과"),
            (21, "🔧  최적 조합 추천"),
            (22, "⚖  A/B 편대 비교"),
        ]),
        ("🖥", "시스템", [
            (6,  "🖥  시스템 모니터"),
            (20, "🛡  서브시스템 피해"),
            (5,  "📡  채널 포화도"),
            (8,  "🔫  탄약 소모"),
            (12, "🔬  최소 재고"),
        ]),
        ("🎯", "작전 결과", [
            (24, "⚔  공격 결과"),
            (25, "🗺  생존성 히트맵"),
            (3,  "🌤  날씨 비교"),
            (23, "🔗  CEC 효과 비교"),
            (17, "🔄  이전 비교"),
        ]),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_idx   = -1
        self._settings      = QSettings("AegisSim", "Sidebar")
        self._item_btns:  dict = {}   # stack_idx → QPushButton
        self._cat_badges: dict = {}   # cat_name  → QLabel (● 배지)
        self._cat_frames: dict = {}   # cat_name  → QFrame (접이식 바디)
        self._cat_headers: dict = {}  # cat_name  → QPushButton (헤더)
        self._build_ui()
        self._restore_state()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        self.setStyleSheet(f"background:{C_BG};")

        # 검색 박스
        self._search = QLineEdit()
        self._search.setPlaceholderText("🔍  검색…")
        self._search.setFixedHeight(30)
        self._search.setStyleSheet(
            f"QLineEdit {{ background:#1c2128; color:{C_TEXT}; border:none;"
            f" border-bottom:1px solid {C_BORDER}; padding:0 8px; font-size:13px; }}"
        )
        self._search.textChanged.connect(self._on_search)
        root.addWidget(self._search)

        # 스크롤 영역
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"QScrollArea {{ border:none; background:{C_BG}; }}")

        content = QWidget()
        content.setStyleSheet(f"background:{C_BG};")
        self._content_layout = QVBoxLayout(content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(0)

        for cat_icon, cat_name, items in self._CATEGORIES:
            self._build_category(cat_icon, cat_name, items)

        self._content_layout.addStretch()
        scroll.setWidget(content)
        root.addWidget(scroll, stretch=1)

    def _build_category(self, icon: str, name: str, items: list):
        # ── 헤더 버튼 ────────────────────────────────────────────────────────
        hdr_w = QWidget()
        hdr_w.setStyleSheet(f"background:#1c2128; border-bottom:1px solid {C_BORDER};")
        hdr_h = QHBoxLayout(hdr_w)
        hdr_h.setContentsMargins(10, 0, 8, 0)
        hdr_h.setSpacing(4)

        arrow = QLabel("▾")
        arrow.setStyleSheet(f"color:{C_SUBTEXT}; font-size:11px;")
        arrow.setFixedWidth(12)

        title_lbl = QLabel(f"{icon}  {name}")
        title_lbl.setStyleSheet(
            f"color:{C_TEXT}; font-size:13px; font-weight:bold; padding:8px 0;")

        badge = QLabel("●")
        badge.setStyleSheet("color:#3498db; font-size:9px;")
        badge.setVisible(False)

        hdr_h.addWidget(arrow)
        hdr_h.addWidget(title_lbl, 1)
        hdr_h.addWidget(badge)

        # 클릭 이벤트 — hdr_w 전체
        hdr_w.mousePressEvent = lambda e, n=name: self._toggle_cat(n)
        hdr_w.setCursor(Qt.CursorShape.PointingHandCursor)

        self._content_layout.addWidget(hdr_w)
        self._cat_headers[name] = (hdr_w, arrow)
        self._cat_badges[name]  = badge

        # ── 아이템 프레임 ─────────────────────────────────────────────────────
        frame = QFrame()
        frame.setStyleSheet(f"QFrame {{ background:{C_BG}; border:none; }}")
        fl = QVBoxLayout(frame)
        fl.setContentsMargins(0, 0, 0, 0)
        fl.setSpacing(0)

        for stack_idx, label in items:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setFixedHeight(34)
            btn.setStyleSheet(self._item_style(False))
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, idx=stack_idx: self._select(idx))
            fl.addWidget(btn)
            self._item_btns[stack_idx] = btn

        self._content_layout.addWidget(frame)
        self._cat_frames[name] = frame

    def _toggle_cat(self, name: str):
        frame = self._cat_frames.get(name)
        if frame is None:
            return
        visible = not frame.isVisible()
        frame.setVisible(visible)
        _, arrow = self._cat_headers.get(name, (None, None))
        if arrow:
            arrow.setText("▾" if visible else "▸")
        self._settings.setValue(f"cat_open_{name}", visible)

    def _select(self, stack_idx: int):
        # 이전 항목 해제
        if self._current_idx in self._item_btns:
            self._item_btns[self._current_idx].setChecked(False)
            self._item_btns[self._current_idx].setStyleSheet(self._item_style(False))
        self._current_idx = stack_idx
        btn = self._item_btns.get(stack_idx)
        if btn:
            btn.setChecked(True)
            btn.setStyleSheet(self._item_style(True))
        # 해당 카테고리 배지 제거 (읽었으니)
        for _, cat_name, items in self._CATEGORIES:
            if any(idx == stack_idx for idx, _ in items):
                b = self._cat_badges.get(cat_name)
                if b:
                    b.setVisible(False)
        self._settings.setValue("last_idx", stack_idx)
        self.item_selected.emit(stack_idx)

    def mark_new_data(self, stack_indices: list):
        """시뮬 완료 시 호출 — 해당 스택 인덱스가 속한 카테고리에 배지 표시."""
        for _, cat_name, items in self._CATEGORIES:
            cat_set = {idx for idx, _ in items}
            if cat_set & set(stack_indices):
                b = self._cat_badges.get(cat_name)
                if b:
                    b.setVisible(True)

    def set_current_index(self, stack_idx: int):
        """외부에서 직접 인덱스 지정 (시스템 모니터 자동 전환 등)."""
        if stack_idx in self._item_btns:
            # 해당 카테고리가 닫혀 있으면 펼침
            for _, cat_name, items in self._CATEGORIES:
                if any(idx == stack_idx for idx, _ in items):
                    frame = self._cat_frames.get(cat_name)
                    if frame and not frame.isVisible():
                        self._toggle_cat(cat_name)
            self._select(stack_idx)

    def _on_search(self, text: str):
        q = text.strip().lower()
        for _, cat_name, items in self._CATEGORIES:
            has_visible = False
            for stack_idx, label in items:
                btn = self._item_btns.get(stack_idx)
                if btn is None:
                    continue
                show = (not q) or (q in label.lower())
                btn.setVisible(show)
                if show:
                    has_visible = True
            # 검색 중에는 항목이 있는 카테고리 자동 펼침
            frame = self._cat_frames.get(cat_name)
            if frame:
                if q:
                    frame.setVisible(has_visible)
                    _, arrow = self._cat_headers.get(cat_name, (None, None))
                    if arrow:
                        arrow.setText("▾" if has_visible else "▸")

    def _restore_state(self):
        # 카테고리 열림/닫힘 복원
        for _, cat_name, _ in self._CATEGORIES:
            open_ = self._settings.value(f"cat_open_{cat_name}", True, type=bool)
            frame = self._cat_frames.get(cat_name)
            if frame:
                frame.setVisible(open_)
            _, arrow = self._cat_headers.get(cat_name, (None, None))
            if arrow:
                arrow.setText("▾" if open_ else "▸")
        # 마지막 선택 탭 복원
        last = self._settings.value("last_idx", 0, type=int)
        if last in self._item_btns:
            self._select(last)
        else:
            self._select(0)

    @staticmethod
    def _item_style(selected: bool) -> str:
        if selected:
            return (
                f"QPushButton {{ background:#0d1117; color:#3498db;"
                f" border:none; border-left:3px solid #3498db;"
                f" text-align:left; padding-left:20px; font-size:13px; font-weight:bold; }}"
            )
        return (
            f"QPushButton {{ background:{C_BG}; color:#7d8590;"
            f" border:none; border-left:3px solid transparent;"
            f" text-align:left; padding-left:20px; font-size:13px; }}"
            f"QPushButton:hover {{ background:#1c2128; color:#e6edf3; }}"
        )


# ════════════════════════════════════════════════════════════════════════════
#  시스템 모니터 탭
# ════════════════════════════════════════════════════════════════════════════
class SysMonitorTab(QWidget):
    """실시간 시스템 모니터 — CPU/RAM/GPU/프로세스/코어/성능 기록."""

    def __init__(self):
        super().__init__()
        self._cpu_hist      = [0.0] * 60
        self._ram_hist      = [0.0] * 60
        self._gpu_hist      = [0.0] * 60
        self._core_pcts     = [0.0] * (os.cpu_count() or 4)
        self._worker_stats  = []
        self._sim_ranges     = []   # list of (start_wall_time, end_wall_time)
        self._sim_start_time = None  # wall-clock time when current sim started
        self._batch_done    = 0
        self._batch_total   = 0
        self._sim_speed     = 0.0
        self._sim_t0        = None
        self._sim_done      = 0
        self._build_ui()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update)
        self._timer.start(2000)   # 2초 간격 — 1초에서 낮춤 (메인 스레드 matplotlib 부하 감소)

    # ── 외부 슬롯 ────────────────────────────────────────────────────────────
    def mark_sim_start(self):
        self._sim_start_time = time.time()
        self._sim_t0   = time.time()
        self._sim_done = 0
        self._sim_speed = 0.0

    def mark_sim_end(self):
        if self._sim_start_time is not None:
            self._sim_ranges.append((self._sim_start_time, time.time()))
            self._sim_ranges = self._sim_ranges[-3:]
            self._sim_start_time = None
        self._batch_done = 0
        self._batch_total = 0
        self._prog_batch.setValue(0)
        self._lbl_batch.setText("배치 진행  대기 중")

    def on_batch_done(self, done: int, total: int):
        self._batch_done  = done
        self._batch_total = total
        self._prog_batch.setMaximum(max(total, 1))
        self._prog_batch.setValue(done)
        self._lbl_batch.setText(f"배치 진행  {done} / {total}")

    def on_progress_detail(self, done: int, total: int, eta: float):
        if self._sim_t0 and done > 0:
            elapsed = time.time() - self._sim_t0
            self._sim_speed = done / elapsed if elapsed > 0 else 0.0
            self._sim_done  = done

    # ── UI 빌더 ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(6)

        # 카드 행 1: 핵심 지표
        r1 = QHBoxLayout()
        self._c_cpu   = self._card("CPU 전체",  "0 %")
        self._c_ram   = self._card("RAM",       "0 %")
        self._c_thr   = self._card("스레드",     "0")
        self._c_gpu   = self._card("GPU",       "— %")
        self._c_ctemp = self._card("CPU 온도",   "— °C")
        self._c_speed = self._card("처리 속도",  "— 회/s")
        for c in (self._c_cpu, self._c_ram, self._c_thr,
                  self._c_gpu, self._c_ctemp, self._c_speed):
            r1.addWidget(c[0])
        root.addLayout(r1)

        # 카드 행 2: 메모리/GPU 상세
        r2 = QHBoxLayout()
        self._c_vram  = self._card("VRAM",      "— MB")
        self._c_gtemp = self._card("GPU 온도",   "— °C")
        self._c_phram = self._card("물리 RAM",   "— GB")
        self._c_vtram = self._card("가상 메모리", "— GB")
        self._c_prram = self._card("프로세스",   "— MB")
        for c in (self._c_vram, self._c_gtemp, self._c_phram,
                  self._c_vtram, self._c_prram):
            r2.addWidget(c[0])
        root.addLayout(r2)

        # 배치 진행 바
        br = QHBoxLayout()
        self._lbl_batch = QLabel("배치 진행  대기 중")
        self._lbl_batch.setStyleSheet(f"color:{C_SUBTEXT}; font-size:12px;")
        self._prog_batch = QProgressBar()
        self._prog_batch.setRange(0, 1); self._prog_batch.setValue(0)
        self._prog_batch.setFixedHeight(12)
        self._prog_batch.setStyleSheet(f"""
            QProgressBar {{ background:{C_PANEL}; border-radius:4px; border:1px solid {C_BORDER}; }}
            QProgressBar::chunk {{ background:{C_ACCENT}; border-radius:3px; }}
        """)
        br.addWidget(self._lbl_batch)
        br.addWidget(self._prog_batch, 1)
        root.addLayout(br)

        # 내부 탭
        self._inner = QTabWidget()
        self._inner.addTab(self._build_sys_tab(),  "📊  시스템")
        self._inner.addTab(self._build_proc_tab(), "⚙️  프로세스")
        self._inner.addTab(self._build_gpu_tab(),  "🎮  GPU")
        self._inner.addTab(self._build_hist_tab(), "📈  성능 기록")
        root.addWidget(self._inner)

    def _card(self, title: str, init: str):
        box = QGroupBox(title)
        box.setFixedHeight(68)
        lay = QVBoxLayout(box)
        lay.setContentsMargins(4, 2, 4, 2)
        lbl = QLabel(init)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setFont(QFont('Malgun Gothic', 14, QFont.Weight.Bold))
        lbl.setStyleSheet(f"color:{C_ACCENT};")
        lay.addWidget(lbl)
        return box, lbl

    def _build_sys_tab(self) -> QWidget:
        w = QWidget(); lay = QHBoxLayout(w); lay.setContentsMargins(0, 6, 0, 0)
        self._sys_canvas = MplCanvas(figsize=(6, 3))
        lay.addWidget(self._sys_canvas, 3)
        # 코어별 바
        scroll = QScrollArea(); scroll.setWidgetResizable(True)
        inner = QWidget(); inner.setStyleSheet(f"background:{C_BG};")
        cl = QVBoxLayout(inner); cl.setSpacing(2); cl.setContentsMargins(6, 6, 6, 6)
        self._core_bars = []
        for i in range(os.cpu_count() or 4):
            row = QHBoxLayout()
            lbl = QLabel(f"C{i:02d}"); lbl.setFixedWidth(32)
            lbl.setStyleSheet(f"color:{C_SUBTEXT}; font-size:12px;")
            bar = QProgressBar(); bar.setRange(0, 100); bar.setValue(0)
            bar.setFixedHeight(14); bar.setTextVisible(False)
            bar.setStyleSheet(f"""
                QProgressBar {{ background:{C_PANEL}; border-radius:3px; border:none; }}
                QProgressBar::chunk {{ background:{C_ACCENT}; border-radius:2px; }}
            """)
            plbl = QLabel("0%"); plbl.setFixedWidth(42)
            plbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            plbl.setStyleSheet(f"color:{C_TEXT}; font-size:12px; font-weight:bold;")
            row.addWidget(lbl); row.addWidget(bar, 1); row.addWidget(plbl)
            cl.addLayout(row)
            self._core_bars.append((bar, plbl))
        cl.addStretch(); scroll.setWidget(inner)
        lay.addWidget(scroll, 2)
        return w

    def _build_proc_tab(self) -> QWidget:
        w = QWidget(); lay = QVBoxLayout(w); lay.setContentsMargins(0, 6, 0, 0)
        lbl = QLabel("워커 프로세스 (ProcessPoolExecutor 자식 프로세스)")
        lbl.setStyleSheet(f"color:{C_SUBTEXT}; font-size:11px;")
        lay.addWidget(lbl)
        self._proc_tbl = QTableWidget(0, 4)
        self._proc_tbl.setHorizontalHeaderLabels(["PID", "CPU %", "RAM (MB)", "상태"])
        hh = self._proc_tbl.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._proc_tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._proc_tbl.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self._proc_tbl.verticalHeader().setVisible(False)
        self._proc_tbl.setStyleSheet(f"background:{C_BG};")
        lay.addWidget(self._proc_tbl)
        return w

    def _build_gpu_tab(self) -> QWidget:
        w = QWidget(); lay = QVBoxLayout(w); lay.setContentsMargins(0, 6, 0, 0)
        self._gpu_canvas = MplCanvas(figsize=(8, 3))
        lay.addWidget(self._gpu_canvas)
        return w

    def _build_hist_tab(self) -> QWidget:
        w = QWidget(); lay = QVBoxLayout(w); lay.setContentsMargins(0, 6, 0, 0)
        lbl = QLabel("최근 시뮬레이션 실행 기록 (최대 10회)")
        lbl.setStyleSheet(f"color:{C_SUBTEXT}; font-size:11px;")
        lay.addWidget(lbl)
        self._hist_tbl = QTableWidget(0, 4)
        self._hist_tbl.setHorizontalHeaderLabels(["실행 시각", "MC 횟수", "소요 시간", "처리 속도"])
        hh = self._hist_tbl.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._hist_tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._hist_tbl.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self._hist_tbl.verticalHeader().setVisible(False)
        self._hist_tbl.setStyleSheet(f"background:{C_BG};")
        lay.addWidget(self._hist_tbl)
        self._hist_canvas = MplCanvas(figsize=(8, 2))
        lay.addWidget(self._hist_canvas)
        return w

    # ── 업데이트 루프 ─────────────────────────────────────────────────────────
    def _update(self):
        # 블로킹 호출 없음 — _SysDataWorker가 채운 캐시만 읽음
        c        = _SYS_CACHE
        cpu      = c['cpu']
        cores    = c.get('cores', [])
        mem_pct  = c['mem_pct']
        gpu      = c['gpu']
        ctemp    = c['cpu_temp']
        proc_ram = c['proc_ram']
        self._worker_stats = c.get('worker_stats', [])

        self._cpu_hist = self._cpu_hist[1:] + [cpu]
        self._ram_hist = self._ram_hist[1:] + [mem_pct]
        self._gpu_hist = self._gpu_hist[1:] + [float(gpu.get('util', 0))]
        if cores:
            self._core_pcts = list(cores)

        # 카드 행 1
        self._c_cpu[1].setText(f"{cpu:.0f} %")
        self._c_ram[1].setText(f"{mem_pct:.0f} %")
        self._c_thr[1].setText(str(c.get('thread_cnt', threading.active_count())))
        self._c_gpu[1].setText(f"{gpu['util']} %" if 'util' in gpu else "— %")
        self._c_ctemp[1].setText(f"{ctemp:.0f} °C" if ctemp >= 0 else "— °C")
        self._c_speed[1].setText(f"{self._sim_speed:.0f} 회/s" if self._sim_speed > 0 else "— 회/s")

        # 카드 행 2
        mu, mt = gpu.get('mem_used'), gpu.get('mem_total')
        self._c_vram[1].setText(f"{mu}/{mt} MB" if mu is not None else "— MB")
        self._c_gtemp[1].setText(f"{gpu['temp']} °C" if 'temp' in gpu else "— °C")
        mem_used_gb  = c.get('mem_used', 0) / 1024**3
        mem_total_gb = c.get('mem_total', 1) / 1024**3
        self._c_phram[1].setText(f"{mem_used_gb:.1f}/{mem_total_gb:.0f} GB")
        self._c_vtram[1].setText(f"{c.get('swap_used', 0)/1024**3:.1f} GB")
        self._c_prram[1].setText(f"{proc_ram:.0f} MB")

        # 코어별 바
        for i, (bar, plbl) in enumerate(self._core_bars):
            pct = int(self._core_pcts[i]) if i < len(self._core_pcts) else 0
            bar.setValue(pct); plbl.setText(f"{pct}%")

        # 탭별 차트 갱신 — 화면에 표시 중일 때만 렌더 (숨겨진 탭은 스킵)
        if self.isVisible():
            self._refresh_active_chart()

    def showEvent(self, event):
        """사이드바에서 이 탭으로 전환될 때 즉시 차트 갱신 (타이머 대기 불필요)."""
        super().showEvent(event)
        self._refresh_active_chart()

    def _refresh_active_chart(self):
        idx = self._inner.currentIndex()
        if idx == 0:
            self._draw_sys_chart()
        elif idx == 1:
            self._update_proc_table()
        elif idx == 2:
            self._draw_gpu_chart()
        elif idx == 3:
            self._draw_hist_tab()

    def _draw_sys_chart(self):
        fig = self._sys_canvas.fig; fig.clear()
        fig.patch.set_facecolor(C_BG)
        ax = fig.add_subplot(111, facecolor='#0a0e1a')
        ax.tick_params(colors='#aab', labelsize=8)
        for sp in ax.spines.values(): sp.set_color('#1e2a3a')
        ax.set_ylim(0, 100); ax.set_xlim(0, 59)
        ax.set_xlabel('경과 (초)', color='#aab', fontsize=8)
        ax.set_ylabel('사용률 (%)', color='#aab', fontsize=8)
        ax.set_title('CPU / RAM (최근 60초)', color='#dde', fontsize=9, fontweight='bold')
        ax.grid(color='#1e2a3a', linewidth=0.5)
        ax.plot(self._cpu_hist, color=C_ACCENT, lw=1.5, label='CPU')
        ax.plot(self._ram_hist, color=C_ORANGE, lw=1.5, label='RAM')
        now = time.time()
        for st, et in self._sim_ranges:
            # x=59 is now, older data is further left
            sx = max(0, 59 - int(now - st))
            ex = min(59, 59 - int(now - et))
            if sx <= 59 and ex >= 0:
                ax.axvspan(sx, max(sx + 1, ex), color='#f1c40f', alpha=0.12, zorder=0)
        if self._sim_start_time is not None:
            sx = max(0, 59 - int(now - self._sim_start_time))
            ax.axvspan(sx, 59, color='#f1c40f',
                       alpha=0.18, zorder=0, label='시뮬 실행 중')
        ax.legend(fontsize=8, facecolor='#0a0e1a', labelcolor='white', edgecolor='#1e2a3a')
        self._sys_canvas.draw_idle()   # BUG-1: draw_idle()로 UI 블로킹 방지

    def _draw_gpu_chart(self):
        fig = self._gpu_canvas.fig; fig.clear()
        fig.patch.set_facecolor(C_BG)
        ax = fig.add_subplot(111, facecolor='#0a0e1a')
        ax.tick_params(colors='#aab', labelsize=8)
        for sp in ax.spines.values(): sp.set_color('#1e2a3a')
        ax.set_ylim(0, 100); ax.set_xlim(0, 59)
        ax.set_xlabel('경과 (초)', color='#aab', fontsize=8)
        ax.set_ylabel('GPU 사용률 (%)', color='#aab', fontsize=8)
        ax.set_title('GPU 사용률 (최근 60초)', color='#dde', fontsize=9, fontweight='bold')
        ax.grid(color='#1e2a3a', linewidth=0.5)
        ax.plot(self._gpu_hist, color='#2ecc71', lw=1.5, label='GPU')
        ax.legend(fontsize=8, facecolor='#0a0e1a', labelcolor='white', edgecolor='#1e2a3a')
        self._gpu_canvas.draw_idle()   # BUG-1

    def _update_proc_table(self):
        self._proc_tbl.setRowCount(0)
        for w in self._worker_stats:
            r = self._proc_tbl.rowCount(); self._proc_tbl.insertRow(r)
            vals = [str(w['pid']), f"{w['cpu']:.1f}%",
                    f"{w['ram']:.0f} MB", w['status']]
            for col, txt in enumerate(vals):
                item = QTableWidgetItem(txt)
                if col == 1 and w['cpu'] > 50:
                    item.setForeground(QColor(C_ACCENT))
                self._proc_tbl.setItem(r, col, item)

    def _draw_hist_tab(self):
        from datetime import datetime
        self._hist_tbl.setRowCount(0)
        for rec in _PERF_HISTORY:
            r = self._hist_tbl.rowCount(); self._hist_tbl.insertRow(r)
            ts = datetime.fromtimestamp(rec['time']).strftime('%H:%M:%S')
            for col, txt in enumerate([
                ts, str(rec.get('mc_n', '—')),
                f"{rec.get('duration', 0):.1f}초",
                f"{rec.get('rate', 0):.1f} 회/s"
            ]):
                self._hist_tbl.setItem(r, col, QTableWidgetItem(txt))
        if _PERF_HISTORY:
            fig = self._hist_canvas.fig; fig.clear()
            fig.patch.set_facecolor(C_BG)
            ax = fig.add_subplot(111, facecolor='#0a0e1a')
            rates = [rec.get('rate', 0) for rec in _PERF_HISTORY]
            ax.bar(range(len(rates)), rates, color=C_ACCENT, alpha=0.8)
            ax.set_ylabel('회/초', color='#aab', fontsize=8)
            ax.set_title('처리 속도 추이', color='#dde', fontsize=9, fontweight='bold')
            ax.tick_params(colors='#aab', labelsize=8)
            for sp in ax.spines.values(): sp.set_color('#1e2a3a')
            ax.grid(color='#1e2a3a', linewidth=0.5, axis='y')
            self._hist_canvas.draw_idle()   # BUG-1


# ════════════════════════════════════════════════════════════════════════════
#  차트 순수 렌더 함수 (백그라운드 스레드에서 호출, Figure 반환)
# ════════════════════════════════════════════════════════════════════════════

def _render_sensitivity_chart(labels: list, lows: list, highs: list, base_rate: float) -> Figure:
    """감도 분석 Tornado chart — 백그라운드 스레드에서 호출."""
    fig = Figure(figsize=(12, 6), facecolor=C_BG)
    fig.patch.set_facecolor('#0a0e1a')
    ax = fig.add_subplot(111, facecolor='#0a0e1a')
    y = list(range(len(labels)))
    ax.barh(y, lows,  color='#e74c3c', alpha=0.8, label='낮은값')
    ax.barh(y, highs, color='#2ecc71', alpha=0.8, label='높은값')
    ax.axvline(0, color=C_TEXT, lw=1)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, color=C_TEXT, fontsize=12)
    ax.set_xlabel('요격률 변화 (기준 대비)', color=C_SUBTEXT, fontsize=12)
    ax.set_title(f'감도 분석 — Tornado chart  (기준 요격률 {base_rate:.1%})',
                 color=C_TEXT, fontsize=14)
    ax.tick_params(colors=C_SUBTEXT, labelsize=11)
    from matplotlib.ticker import FuncFormatter
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:+.1%}"))
    for sp in ax.spines.values(): sp.set_color('#1e2a3a')
    ax.legend(fontsize=11, facecolor='#0a0e1a', labelcolor=C_TEXT, edgecolor='#1e2a3a')
    fig.tight_layout()
    return fig


def _render_min_stock_chart(results: dict, target_rate: float) -> Figure:
    """최소 재고 역산 수평 막대 차트 — 백그라운드 스레드에서 호출."""
    fig = Figure(figsize=(13, 6), facecolor=C_BG)
    fig.patch.set_facecolor('#0a0e1a')
    ax = fig.add_subplot(111, facecolor='#0a0e1a')
    short_names = {
        'SM-3 Block IIA':   'SM-3 IIA',
        'SM-6':             'SM-6',
        'SM-2 Block IIIB':  'SM-2 IIIB',
        'RIM-116 RAM':      'RIM-116 RAM',
        '홍상어 (대잠)':    '홍상어',
        '청상어 (경어뢰)':  '청상어',
    }
    wpn_names = list(results.keys())
    labels   = [short_names.get(w, w) for w in wpn_names]
    currents = [results[w]['current_stock'] for w in wpn_names]
    mins     = [results[w]['min_stock']     for w in wpn_names]
    achieves = [results[w]['achievable']    for w in wpn_names]
    y = list(range(len(wpn_names)))
    ax.barh(y, currents, color='#2a3545', height=0.55, label='현재 재고')
    for i, (mn, cur, ach) in enumerate(zip(mins, currents, achieves)):
        if not ach:
            color, bar_val = '#e74c3c', cur
        elif mn == 0:
            color, bar_val = '#3498db', 0
        elif mn <= cur:
            color, bar_val = '#2ecc71', mn
        else:
            color, bar_val = '#e67e22', mn
        ax.barh(i, bar_val, color=color, height=0.55, alpha=0.9)
        if not ach:
            txt = '달성 불가'
        elif mn == 0:
            txt = '불필요'
        else:
            saving = cur - mn
            txt = f'최소 {mn}발  ({"▼ " + str(saving) + "발 절약" if saving > 0 else ("▲ " + str(-saving) + "발 부족" if saving < 0 else "현재 최적")})'
        ax.text(max(cur, mn) + 0.5, i, txt, va='center', color=C_TEXT, fontsize=11)
    ax.set_yticks(y)
    ax.set_yticklabels(labels, color=C_TEXT, fontsize=13)
    ax.set_xlabel('재고 수량 (함정당)', color=C_SUBTEXT, fontsize=12)
    ax.set_title(
        f'REQ 달성 최소 재고 역산  (목표: 완전 요격 성공률 ≥ {target_rate:.0%})\n'
        '■ 현재 재고  ■ 최소 필요  (녹색=절약 가능 / 주황=부족 / 파랑=불필요)',
        color=C_TEXT, fontsize=13, pad=10,
    )
    max_x = max(currents + [m for m in mins if m >= 0], default=50)
    ax.set_xlim(0, max_x * 1.35)
    ax.tick_params(colors=C_SUBTEXT, labelsize=11)
    for sp in ax.spines.values(): sp.set_color('#1e2a3a')
    ax.legend(fontsize=11, facecolor='#0a0e1a', labelcolor=C_TEXT,
              edgecolor='#1e2a3a', loc='lower right')
    fig.tight_layout()
    return fig


def _render_cec_compare(cec_results: dict) -> Figure:
    """CEC ON/OFF/두절 3종 비교 차트."""
    fig = Figure(figsize=(13, 6), facecolor=C_BG)
    fig.patch.set_facecolor(C_BG)

    if not cec_results:
        ax = fig.add_subplot(111, facecolor='#0a0e1a')
        ax.text(0.5, 0.5, '데이터 없음', ha='center', va='center',
                color=C_SUBTEXT, fontsize=14, transform=ax.transAxes)
        return fig

    labels   = list(cec_results.keys())
    rates    = [cec_results[l].get('mean_intercept', 0) * 100 for l in labels]
    stds     = [cec_results[l].get('std_intercept',  0) * 100 for l in labels]
    costs    = [cec_results[l].get('mean_cost',       0)       for l in labels]
    clrs     = ['#2ecc71', '#3498db', '#e74c3c']

    gs  = fig.add_gridspec(1, 2, wspace=0.38)
    ax1 = fig.add_subplot(gs[0], facecolor='#0a0e1a')
    ax2 = fig.add_subplot(gs[1], facecolor='#0a0e1a')

    # 왼쪽: 요격률 막대
    x = list(range(len(labels)))
    bars = ax1.bar(x, rates, color=clrs[:len(labels)], width=0.5,
                   yerr=stds, capsize=5,
                   error_kw={'elinewidth': 1.5, 'ecolor': '#ffffff60'})
    ax1.set_xticks(x)
    ax1.set_xticklabels(labels, color=C_TEXT, fontsize=11)
    ax1.set_ylabel('요격률 (%)', color=C_SUBTEXT, fontsize=12)
    ax1.set_ylim(0, 110)
    ax1.set_title('CEC 설정별 요격률 비교  (±1σ)', color=C_TEXT, fontsize=13)
    ax1.tick_params(colors=C_SUBTEXT, labelsize=11)
    for sp in ax1.spines.values():
        sp.set_color('#1e2a3a')
    for bar, rate, std in zip(bars, rates, stds):
        ax1.text(bar.get_x() + bar.get_width() / 2,
                 rate + std + 1.5,
                 f'{rate:.1f}%', ha='center', color=C_TEXT, fontsize=11)

    # 오른쪽: 비용 막대
    _KRW = 1_350
    cost_krw = [c * _KRW / 1e8 for c in costs]
    bars2 = ax2.bar(x, cost_krw, color=clrs[:len(labels)], width=0.5, alpha=0.8)
    ax2.set_xticks(x)
    ax2.set_xticklabels(labels, color=C_TEXT, fontsize=11)
    ax2.set_ylabel('평균 교전 비용 (억 원)', color=C_SUBTEXT, fontsize=12)
    ax2.set_title('CEC 설정별 교전 비용 비교', color=C_TEXT, fontsize=13)
    ax2.tick_params(colors=C_SUBTEXT, labelsize=11)
    for sp in ax2.spines.values():
        sp.set_color('#1e2a3a')
    for bar, krw in zip(bars2, cost_krw):
        ax2.text(bar.get_x() + bar.get_width() / 2,
                 bar.get_height() + 0.2,
                 f'{krw:.1f}억', ha='center', color=C_TEXT, fontsize=11)

    # CEC 효과 요약 텍스트
    if len(rates) >= 2:
        delta = rates[0] - rates[1]
        sign  = '+' if delta >= 0 else ''
        fig.text(0.5, 0.02,
                 f"CEC ON vs OFF: 요격률 {sign}{delta:.1f}%p 차이  ·  "
                 "⚠  단가 개략 추정 ±30%",
                 ha='center', color='#e67e22', fontsize=10)

    fig.tight_layout(rect=[0, 0.05, 1, 1])
    return fig


def _render_optimize_chart(results: list) -> Figure:
    """최적 무기 조합 수평 막대 차트 (백그라운드 렌더링)."""
    _KRW = 1_350
    fig = Figure(figsize=(14, 7), facecolor='#0a0e1a')
    fig.patch.set_facecolor('#0a0e1a')
    ax = fig.add_subplot(111, facecolor='#0a0e1a')

    if not results:
        ax.text(0.5, 0.5, '탐색 결과 없음', transform=ax.transAxes,
                ha='center', va='center', color=C_TEXT, fontsize=14)
        return fig

    labels, rates, stds, clrs, costs = [], [], [], [], []
    for i, r in enumerate(results):
        c = r['combo']
        parts = []
        for wpn, key in [('SM-3', 'SM-3 Block IIA'), ('SM-6', 'SM-6'),
                         ('SM-2', 'SM-2 Block IIIB'), ('RAM', 'RIM-116 RAM')]:
            if c.get(key, 0) > 0:
                parts.append(f'{wpn}×{c[key]}')
        total = r['total']
        labels.append(f"{'  |  '.join(parts)}   [{total}발]")
        rates.append(r['rate'] * 100)
        stds.append(r['std'] * 100)
        clrs.append('#2ecc71' if i == 0 else '#3498db')
        costs.append(r.get('combo_cost', 0))

    y = list(range(len(results)))
    ax.barh(y, rates, xerr=stds, color=clrs, height=0.55,
            error_kw={'elinewidth': 1.5, 'ecolor': '#ffffff50', 'capsize': 4})

    max_std = max(stds) if stds else 0
    for i, (rate, std, cost) in enumerate(zip(rates, stds, costs)):
        cost_krw = cost * _KRW / 1e8
        cost_lbl = f"  {cost_krw:.0f}억원" if cost_krw > 0 else ""
        ax.text(rate + max_std + 1.0, i,
                f'{rate:.1f}% ± {std:.1f}%{cost_lbl}',
                va='center', color=C_TEXT, fontsize=10.5)

    ax.set_yticks(y)
    ax.set_yticklabels(labels, color=C_TEXT, fontsize=11)
    ax.set_xlabel('요격률 (%)', color=C_SUBTEXT, fontsize=12)
    ax.set_title(
        '최적 무기 조합 추천  (상위 5개 — 정밀 검증 완료)\n'
        '■ 최적 조합 (녹색)  ■ 차선 조합 (파랑)  |  오차막대 = ±1σ  ·  비용은 조달 단가 기반 개략 추정 ±30%',
        color=C_TEXT, fontsize=12, pad=10,
    )
    ax.set_xlim(0, 120)
    ax.tick_params(colors=C_SUBTEXT, labelsize=11)
    for sp in ax.spines.values():
        sp.set_color('#1e2a3a')
    if rates:
        ax.axvline(rates[0], color='#2ecc71', linestyle='--', alpha=0.25, linewidth=1)
    fig.tight_layout()
    return fig


def _render_mc_chart(result: dict, mc: dict, cfg: dict) -> bytes:
    """MC 통계: plot_v7 PNG를 bytes로 직접 반환 (이중 렌더 제거)."""
    import tempfile, uuid as _uuid
    img_path = os.path.join(tempfile.gettempdir(),
                            f'mc_chart_{_uuid.uuid4().hex}.png')
    try:
        plot_v7(result, mc, cfg, img_path=img_path)
        if os.path.exists(img_path):
            with open(img_path, 'rb') as f:
                return f.read()
    finally:
        try:
            os.remove(img_path)
        except Exception:
            pass
    return b''


def _render_channel_heatmap(result: dict) -> Figure:
    frames = result.get('frames', [])
    fig = Figure(figsize=(12, 5), facecolor=C_BG)
    if not frames or not getattr(frames[0], 'ship_channels', None):
        ax = fig.add_subplot(111, facecolor='#0a0e1a')
        ax.text(0.5, 0.5, '채널 데이터 없음\n(시뮬레이션 재실행 필요)',
                ha='center', va='center', color='#7d8590',
                fontsize=12, transform=ax.transAxes)
        return fig
    ship_names = [sc[0] for sc in frames[0].ship_channels]
    times = [f.t for f in frames]
    usage = np.zeros((len(ship_names), len(frames)))
    for fi, frame in enumerate(frames):
        for si, sc in enumerate(frame.ship_channels):
            _, ch_used, ch_max = sc
            usage[si, fi] = ch_used / ch_max if ch_max > 0 else 0.0
    ax = fig.add_subplot(111, facecolor='#0a0e1a')
    im = ax.imshow(usage, aspect='auto',
                   extent=[times[0], times[-1], -0.5, len(ship_names) - 0.5],
                   origin='lower', cmap='RdYlGn_r', vmin=0, vmax=1,
                   interpolation='nearest')
    ax.set_yticks(range(len(ship_names)))
    ax.set_yticklabels(ship_names, color='#aab', fontsize=12)
    ax.set_xlabel('시간 (s)', color='#aab', fontsize=12)
    ax.set_title('채널 포화도  (빨강=포화, 초록=여유)', color='#dde', fontsize=14)
    ax.tick_params(colors='#aab', labelsize=11)
    for sp in ax.spines.values():
        sp.set_color('#1e2a3a')
    cbar = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cbar.ax.tick_params(colors='#aab', labelsize=10)
    cbar.set_label('채널 사용률', color='#aab', fontsize=11)
    fig.tight_layout()
    return fig


def _render_cost_effect(result: dict, mc: dict) -> Figure:
    _KRW_PER_USD = 1_350          # 원/달러 환율 (개략)
    _COST_FACTOR  = 0.30          # ±30% 단가 불확실성
    fig = Figure(figsize=(12, 6), facecolor=C_BG)
    costs     = mc.get('total_costs', [])
    e_dest    = mc.get('enemy_destroyed', [])
    mean_cost = float(np.mean(costs)) if costs else 0.0
    mean_kill = float(np.mean(e_dest)) if e_dest else 0.0
    cost_per_kill = mean_cost / mean_kill if mean_kill > 0 else float('inf')

    cost_lo  = mean_cost * (1 - _COST_FACTOR)
    cost_hi  = mean_cost * (1 + _COST_FACTOR)
    cpk_lo   = cost_per_kill * (1 - _COST_FACTOR)
    cpk_hi   = cost_per_kill * (1 + _COST_FACTOR)

    wpn_rem = mc.get('weapon_avg_remaining', {})
    kor_shots = result.get('kor_shots', 0)
    usa_shots = result.get('usa_shots', 0)
    has_alliance = (kor_shots + usa_shots > 0) and usa_shots > 0

    if has_alliance:
        gs  = fig.add_gridspec(1, 3, wspace=0.42)
        ax1 = fig.add_subplot(gs[0], facecolor='#0a0e1a')
        ax2 = fig.add_subplot(gs[1], facecolor='#0a0e1a')
        ax3 = fig.add_subplot(gs[2], facecolor='#0a0e1a')
    else:
        gs  = fig.add_gridspec(1, 2, wspace=0.38)
        ax1 = fig.add_subplot(gs[0], facecolor='#0a0e1a')
        ax2 = fig.add_subplot(gs[1], facecolor='#0a0e1a')
        ax3 = None

    # ── 왼쪽: 비용 수치 ──────────────────────────────────────────────────────
    ax1.axis('off')
    ax1.set_facecolor('#0a0e1a')

    ax1.text(0.5, 0.92, '격추 1건당 평균 비용', ha='center', va='top',
             color=C_TEXT, fontsize=13, transform=ax1.transAxes)

    if cost_per_kill == float('inf'):
        ax1.text(0.5, 0.72, 'N/A', ha='center', va='center',
                 color=C_SUBTEXT, fontsize=28, transform=ax1.transAxes)
    else:
        ax1.text(0.5, 0.72, f"${cost_per_kill:,.0f}",
                 ha='center', va='center', color=C_GREEN, fontsize=30,
                 fontweight='bold', transform=ax1.transAxes)
        cpk_krw_lo = cpk_lo * _KRW_PER_USD / 1e8
        cpk_krw_hi = cpk_hi * _KRW_PER_USD / 1e8
        ax1.text(0.5, 0.56,
                 f"범위  ${cpk_lo:,.0f} ~ ${cpk_hi:,.0f}  "
                 f"({cpk_krw_lo:.1f}억 ~ {cpk_krw_hi:.1f}억 원)",
                 ha='center', va='center', color=C_SUBTEXT, fontsize=10.5,
                 transform=ax1.transAxes)

    ax1.axhline(y=0.46, xmin=0.08, xmax=0.92, color='#2a3a4a', linewidth=0.8,
                transform=ax1.transAxes)

    krw_lo  = cost_lo  * _KRW_PER_USD / 1e8
    krw_hi  = cost_hi  * _KRW_PER_USD / 1e8
    krw_avg = mean_cost * _KRW_PER_USD / 1e8
    ax1.text(0.5, 0.38, f"총 소모 비용 평균  ${mean_cost:,.0f}  ({krw_avg:.1f}억 원)",
             ha='center', va='center', color=C_SUBTEXT, fontsize=11.5,
             transform=ax1.transAxes)
    ax1.text(0.5, 0.27,
             f"추정 범위  {krw_lo:.1f}억 ~ {krw_hi:.1f}억 원  ·  평균 격침 {mean_kill:.1f}척",
             ha='center', va='center', color='#7d8590', fontsize=10.5,
             transform=ax1.transAxes)
    ax1.text(0.5, 0.10,
             "⚠  단가는 공개 자료 기반 개략 추정 ±30%  —  실제 조달 비용과 상이할 수 있음",
             ha='center', va='center', color='#e67e22', fontsize=9.5,
             transform=ax1.transAxes)

    # ── 오른쪽: 잔여 재고 막대 ───────────────────────────────────────────────
    ax2.set_facecolor('#0a0e1a')
    if wpn_rem:
        names = list(wpn_rem.keys())
        vals  = [wpn_rem[n] for n in names]
        colors = [C_GREEN if v > 5 else C_ORANGE if v > 0 else C_RED for v in vals]
        y = list(range(len(names)))
        ax2.barh(y, vals, color=colors, height=0.6)
        ax2.set_yticks(y)
        ax2.set_yticklabels(names, color=C_TEXT, fontsize=11)
        ax2.set_xlabel('평균 잔여 재고 (발)', color=C_SUBTEXT, fontsize=12)
        ax2.set_title('무기별 평균 잔여 재고', color=C_TEXT, fontsize=13)
        ax2.tick_params(colors=C_SUBTEXT, labelsize=11)
        for sp in ax2.spines.values():
            sp.set_color('#1e2a3a')
    else:
        ax2.axis('off')
        ax2.text(0.5, 0.5, '잔여 재고 데이터 없음',
                 ha='center', va='center', color=C_SUBTEXT,
                 fontsize=12, transform=ax2.transAxes)

    # ── 오른쪽: 한미 기여도 (한미 연합 편대 선택 시에만) ─────────────────────
    if ax3 is not None:
        ax3.set_facecolor('#0a0e1a')
        kor_cost = result.get('kor_cost', 0)
        usa_cost = result.get('usa_cost', 0)
        nations  = ['한국 (KOR)', '미국 (USA)']
        shots    = [kor_shots, usa_shots]
        costs_k  = [kor_cost * _KRW_PER_USD / 1e8, usa_cost * _KRW_PER_USD / 1e8]
        clrs     = ['#3498db', '#e74c3c']

        x = [0, 1]
        bars = ax3.bar(x, shots, color=clrs, width=0.5, alpha=0.85)
        ax3.set_xticks(x)
        ax3.set_xticklabels(nations, color=C_TEXT, fontsize=11)
        ax3.set_ylabel('발사 발수', color=C_SUBTEXT, fontsize=11)
        ax3.set_title('한미 연합 기여도', color=C_TEXT, fontsize=13)
        ax3.tick_params(colors=C_SUBTEXT, labelsize=10)
        for sp in ax3.spines.values():
            sp.set_color('#1e2a3a')
        for bar, n, c in zip(bars, shots, costs_k):
            ax3.text(bar.get_x() + bar.get_width() / 2,
                     bar.get_height() + 0.3,
                     f'{n}발\n({c:.1f}억원)',
                     ha='center', color=C_TEXT, fontsize=10)

    fig.tight_layout()
    return fig


def _render_ammo_curve(mc: dict) -> Figure:
    fig = Figure(figsize=(12, 5), facecolor=C_BG)
    ax = fig.add_subplot(111, facecolor='#0a0e1a')
    wpn_rem = mc.get('weapon_avg_remaining', {})
    if not wpn_rem:
        ax.text(0.5, 0.5, '데이터 없음\n(시뮬레이션 재실행 필요)',
                ha='center', va='center', color=C_SUBTEXT,
                fontsize=12, transform=ax.transAxes)
        fig.tight_layout()
        return fig
    names = list(wpn_rem.keys())
    vals  = [wpn_rem[n] for n in names]
    y     = np.arange(len(names))
    bars  = ax.barh(y, vals, color=C_ACCENT, height=0.55, alpha=0.85)
    for bar, val in zip(bars, vals):
        ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height() / 2,
                f'{val:.1f}', va='center', color=C_TEXT, fontsize=11)
    ax.set_yticks(y)
    ax.set_yticklabels(names, color=C_TEXT, fontsize=12)
    ax.set_xlabel('MC 평균 잔여 재고 (발)', color=C_SUBTEXT, fontsize=12)
    ax.set_title('무기별 평균 잔여 재고 (MC 전체 평균)', color=C_TEXT, fontsize=13)
    ax.tick_params(colors=C_SUBTEXT, labelsize=11)
    for sp in ax.spines.values():
        sp.set_color('#1e2a3a')
    fig.tight_layout()
    return fig


def _render_ci_chart(mc: dict) -> Figure:
    fig = Figure(figsize=(12, 5), facecolor=C_BG)
    rates = mc.get('intercept_rates', [])
    if not rates:
        ax = fig.add_subplot(111, facecolor='#0a0e1a')
        ax.text(0.5, 0.5, '데이터 없음', ha='center', va='center',
                color=C_SUBTEXT, fontsize=12, transform=ax.transAxes)
        fig.tight_layout()
        return fig
    arr   = np.array(rates)
    mean  = float(arr.mean())
    std   = float(arr.std())
    ci_lo = max(0.0, mean - 1.96 * std / np.sqrt(len(arr)))
    ci_hi = min(1.0, mean + 1.96 * std / np.sqrt(len(arr)))
    gs = fig.add_gridspec(1, 2, wspace=0.35)
    ax1 = fig.add_subplot(gs[0], facecolor='#0a0e1a')
    ax2 = fig.add_subplot(gs[1], facecolor='#0a0e1a')
    ax1.hist(arr, bins=20, color=C_ACCENT, alpha=0.75, edgecolor='#1e2a3a')
    ax1.axvline(mean,  color=C_GREEN,  lw=2, label=f'평균 {mean:.1%}')
    ax1.axvline(ci_lo, color=C_ORANGE, lw=1.5, ls='--', label=f'CI 하한 {ci_lo:.1%}')
    ax1.axvline(ci_hi, color=C_ORANGE, lw=1.5, ls='--', label=f'CI 상한 {ci_hi:.1%}')
    ax1.set_xlabel('요격률', color=C_SUBTEXT, fontsize=12)
    ax1.set_ylabel('빈도', color=C_SUBTEXT, fontsize=12)
    ax1.set_title(f'요격률 분포 (n={len(arr)})', color=C_TEXT, fontsize=13)
    ax1.legend(fontsize=11, facecolor='#0a0e1a', labelcolor=C_TEXT, edgecolor='#1e2a3a')
    ax1.tick_params(colors=C_SUBTEXT, labelsize=11)
    for sp in ax1.spines.values():
        sp.set_color('#1e2a3a')
    ship_hits = mc.get('ship_avg_hits', {})
    if ship_hits:
        snames = list(ship_hits.keys())
        shvals = [ship_hits[s] for s in snames]
        y      = np.arange(len(snames))
        clrs   = [C_RED if v > 1 else C_ORANGE if v > 0 else C_GREEN for v in shvals]
        ax2.barh(y, shvals, color=clrs, height=0.55)
        ax2.set_yticks(y)
        ax2.set_yticklabels(snames, color=C_TEXT, fontsize=11)
        ax2.set_xlabel('평균 피격 횟수', color=C_SUBTEXT, fontsize=12)
        ax2.set_title('함정별 평균 피격', color=C_TEXT, fontsize=13)
        ax2.tick_params(colors=C_SUBTEXT, labelsize=11)
        for sp in ax2.spines.values():
            sp.set_color('#1e2a3a')
    else:
        ax2.axis('off')
        ax2.text(0.5, 0.5, '피격 데이터 없음', ha='center', va='center',
                 color=C_SUBTEXT, fontsize=10, transform=ax2.transAxes)
    fig.tight_layout()
    return fig


def _render_timeline(result: dict) -> Figure:
    fig = Figure(figsize=(14, 5), facecolor=C_BG)
    ax = fig.add_subplot(111, facecolor='#0a0e1a')
    log = result.get('log', [])
    if not log:
        ax.text(0.5, 0.5, '로그 데이터 없음', ha='center', va='center',
                color=C_SUBTEXT, fontsize=12, transform=ax.transAxes)
        fig.tight_layout()
        return fig
    _CAT = [
        ('[방어]',     C_GREEN,  '방어 발사',  0),
        ('[대공 방어]', C_ACCENT, '대공 발사',  1),
        ('[공격]',     '#e67e22','대함 공격',  2),
        ('[대잠 공격]', '#9b59b6','대잠 공격',  3),
        ('[피격]',     C_RED,    '피격',       4),
        ('[경고]',     C_ORANGE, '경고',       5),
        ('[적 발사]',  '#c0392b','적 발사',    6),
    ]
    events = []
    for t, msg in log:
        for tag, color, label, yi in _CAT:
            if tag in msg:
                events.append((t, yi, color, label, msg[:60]))
                break
    if not events:
        ax.text(0.5, 0.5, '분류 가능한 이벤트 없음', ha='center', va='center',
                color=C_SUBTEXT, fontsize=12, transform=ax.transAxes)
        fig.tight_layout()
        return fig
    y_labels = ['방어 발사', '대공 발사', '대함 공격', '대잠 공격', '피격', '경고', '적 발사']
    for t, yi, color, label, msg in events:
        ax.scatter(t, yi, c=color, s=30, zorder=3, alpha=0.8)
    ax.set_yticks(range(len(y_labels)))
    ax.set_yticklabels(y_labels, color=C_TEXT, fontsize=12)
    ax.set_xlabel('시뮬 시각 (초)', color=C_SUBTEXT, fontsize=12)
    ax.set_title('교전 이벤트 타임라인', color=C_TEXT, fontsize=14)
    ax.tick_params(colors=C_SUBTEXT, labelsize=11)
    ax.set_ylim(-0.8, len(y_labels) - 0.2)
    for sp in ax.spines.values():
        sp.set_color('#1e2a3a')
    ax.grid(axis='x', color='#1e2a3a', lw=0.5)
    handles = [plt.Line2D([0], [0], marker='o', color='w',
                           markerfacecolor=c, markersize=9, label=l)
               for _, c, l, _ in _CAT]
    ax.legend(handles=handles, fontsize=10, facecolor='#0a0e1a',
              labelcolor=C_TEXT, edgecolor='#1e2a3a',
              loc='upper right', ncol=4)
    fig.tight_layout()
    return fig


def _render_bearing_vulnerability(result: dict) -> Figure:
    fig = Figure(figsize=(8, 8), facecolor='#0a0e1a')
    ax = fig.add_subplot(111, polar=True)
    ax.set_facecolor('#0a0e1a')
    log = result.get('log', [])
    N = 8
    hit_counts  = [0] * N
    kill_counts = [0] * N
    for _, msg in log:
        bearing_deg = None
        if '방위' in msg:
            try:
                bearing_deg = float(msg.split('방위')[1].split('°')[0])
            except Exception:
                pass
        if bearing_deg is None:
            bearing_deg = hash(msg) % 360
        sector = int((bearing_deg % 360) / (360 / N))
        if '[피격]' in msg:
            hit_counts[sector]  += 1
        elif '[격추]' in msg or '[요격]' in msg:
            kill_counts[sector] += 1
    angles   = np.linspace(0, 2 * np.pi, N, endpoint=False)
    hit_arr  = np.array(hit_counts,  dtype=float)
    kill_arr = np.array(kill_counts, dtype=float)
    max_val  = max(hit_arr.max(), kill_arr.max(), 1)
    hit_arr  /= max_val
    kill_arr /= max_val
    angles_c = np.concatenate([angles, [angles[0]]])
    hit_c    = np.concatenate([hit_arr,  [hit_arr[0]]])
    kill_c   = np.concatenate([kill_arr, [kill_arr[0]]])
    sector_labels = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    ax.plot(angles_c, kill_c, 'o-', color='#2ecc71', lw=1.5, label='요격')
    ax.fill(angles_c, kill_c, alpha=0.2, color='#2ecc71')
    ax.plot(angles_c, hit_c,  'o-', color='#e74c3c', lw=1.5, label='피격')
    ax.fill(angles_c, hit_c,  alpha=0.2, color='#e74c3c')
    ax.set_xticks(angles)
    ax.set_xticklabels(sector_labels, color=C_TEXT, fontsize=12)
    ax.set_yticklabels([])
    ax.set_title('방위각 취약점 분석', color=C_TEXT, fontsize=14, pad=15)
    ax.tick_params(colors=C_SUBTEXT)
    ax.spines['polar'].set_color('#1e2a3a')
    ax.grid(color='#1e2a3a')
    ax.legend(loc='upper right', fontsize=11, facecolor='#0a0e1a',
              labelcolor=C_TEXT, edgecolor='#1e2a3a',
              bbox_to_anchor=(1.25, 1.1))
    fig.tight_layout()
    return fig


def _render_req_radar(result: dict, mc: dict, cfg: dict = None) -> Figure:
    fig = Figure(figsize=(8, 8), facecolor='#0a0e1a')
    if not _V7_OK:
        ax = fig.add_subplot(111)
        ax.text(0.5, 0.5, 'v7 엔진 미로드', ha='center', va='center',
                color=C_SUBTEXT, fontsize=12, transform=ax.transAxes)
        return fig
    try:
        verdicts, _ = evaluate_req_v7(result, mc, cfg)
    except Exception:
        return fig
    ax = fig.add_subplot(111, polar=True)
    ax.set_facecolor('#0a0e1a')
    labels = [r['id'] for r in REQ_ITEMS_V7]
    N = len(labels)
    if N == 0:
        return fig
    vals     = [1.0 if v else 0.0 for v in verdicts]
    angles   = np.linspace(0, 2 * np.pi, N, endpoint=False)
    vals_c   = np.concatenate([vals,   [vals[0]]])
    angles_c = np.concatenate([angles, [angles[0]]])
    ax.plot(angles_c, vals_c, 'o-', color=C_ACCENT, lw=2)
    ax.fill(angles_c, vals_c, alpha=0.3, color=C_ACCENT)
    ax.set_xticks(angles)
    ax.set_xticklabels(labels, color=C_TEXT, fontsize=12)
    ax.set_yticks([0, 0.5, 1.0])
    ax.set_yticklabels(['FAIL', '', 'PASS'], color=C_SUBTEXT, fontsize=10)
    ax.set_ylim(0, 1.2)
    pass_cnt = sum(verdicts)
    ax.set_title(f'REQ 충족률  {pass_cnt}/{N}  ({pass_cnt/N:.0%})',
                 color=C_TEXT, fontsize=14, pad=15)
    ax.spines['polar'].set_color('#1e2a3a')
    ax.grid(color='#1e2a3a')
    fig.tight_layout()
    return fig


def _render_threat_type(result: dict, mc: dict) -> Figure:
    fig = Figure(figsize=(12, 5), facecolor=C_BG)
    ax = fig.add_subplot(111, facecolor='#0a0e1a')
    if not _V7_OK:
        ax.text(0.5, 0.5, 'v7 엔진 미로드', ha='center', va='center',
                color=C_SUBTEXT, fontsize=12, transform=ax.transAxes)
        return fig
    log = result.get('log', [])
    categories = {
        '항공기':     {'intercept': 0, 'total': 0},
        '탄도탄':     {'intercept': 0, 'total': 0},
        '순항미사일': {'intercept': 0, 'total': 0},
        '잠수함':     {'intercept': 0, 'total': 0},
        '기타':       {'intercept': 0, 'total': 0},
    }
    def _classify(msg: str) -> str:
        for kw, cat in [
            ('항공', '항공기'), ('KH-', '항공기'), ('Su-', '항공기'),
            ('화성', '탄도탄'), ('SM-3', '탄도탄'), ('탄도', '탄도탄'),
            ('순항', '순항미사일'), ('Kh-', '순항미사일'), ('화살', '순항미사일'),
            ('지르콘', '순항미사일'), ('킨잘', '순항미사일'),
            ('잠수함', '잠수함'), ('어뢰', '잠수함'), ('수중', '잠수함'),
        ]:
            if kw in msg:
                return cat
        return '기타'
    for _, msg in log:
        if '[요격]' in msg or '[격추]' in msg:
            cat = _classify(msg)
            categories[cat]['total']     += 1
            categories[cat]['intercept'] += 1
        elif '[피격]' in msg or '[통과]' in msg:
            cat = _classify(msg)
            categories[cat]['total'] += 1
    labels = [k for k, v in categories.items() if v['total'] > 0]
    if not labels:
        ax.text(0.5, 0.5, '데이터 없음', ha='center', va='center',
                color=C_SUBTEXT, fontsize=12, transform=ax.transAxes)
        return fig
    rates  = [categories[l]['intercept'] / max(categories[l]['total'], 1)
              for l in labels]
    totals = [categories[l]['total'] for l in labels]
    colors = ['#3498db', '#e74c3c', '#f39c12', '#2ecc71', '#9b59b6']
    bars = ax.bar(labels, rates,
                  color=colors[:len(labels)], alpha=0.85, edgecolor='#1e2a3a')
    for bar, t, r in zip(bars, totals, rates):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.02,
                f'{r:.0%}\n(n={t})',
                ha='center', va='bottom', color=C_TEXT, fontsize=12)
    ax.set_ylim(0, 1.2)
    ax.set_ylabel('요격률', color=C_SUBTEXT, fontsize=12)
    ax.set_title('위협 유형별 요격률', color=C_TEXT, fontsize=14)
    ax.tick_params(colors=C_SUBTEXT, labelsize=12)
    for sp in ax.spines.values():
        sp.set_color('#1e2a3a')
    ax.axhline(0.9, color='#2ecc71', lw=1, ls='--', alpha=0.5, label='목표 90%')
    ax.legend(fontsize=11, facecolor='#0a0e1a', labelcolor=C_TEXT, edgecolor='#1e2a3a')
    fig.tight_layout()
    return fig


def _render_vuln_time(result: dict) -> Figure:
    fig = Figure(figsize=(12, 5), facecolor=C_BG)
    ax = fig.add_subplot(111, facecolor='#0a0e1a')
    log = result.get('log', [])
    hit_times  = [t for t, msg in log if '[피격]' in msg]
    kill_times = [t for t, msg in log if '[요격]' in msg or '[격추]' in msg]
    max_t = max((result.get('sim_time', 300),
                 max(hit_times or [0]),
                 max(kill_times or [0]))) + 10
    bins = np.arange(0, max_t + 10, 10)
    if kill_times:
        ax.hist(kill_times, bins=bins, color='#2ecc71', alpha=0.7,
                label='요격/격추', edgecolor='#0a0e1a')
    if hit_times:
        ax.hist(hit_times, bins=bins, color='#e74c3c', alpha=0.7,
                label='피격', edgecolor='#0a0e1a')
    if hit_times:
        h, b = np.histogram(hit_times, bins=bins)
        peak_start = b[np.argmax(h)]
        ax.axvspan(peak_start, peak_start + 10, alpha=0.25, color='#e74c3c',
                   label=f'최다 피격 구간 ({peak_start:.0f}~{peak_start+10:.0f}s)')
    ax.set_xlabel('시뮬 시각 (초)', color=C_SUBTEXT, fontsize=12)
    ax.set_ylabel('이벤트 수', color=C_SUBTEXT, fontsize=12)
    ax.set_title('취약 시간대 분석 (10초 구간)', color=C_TEXT, fontsize=14)
    ax.tick_params(colors=C_SUBTEXT, labelsize=11)
    for sp in ax.spines.values():
        sp.set_color('#1e2a3a')
    ax.legend(fontsize=11, facecolor='#0a0e1a', labelcolor=C_TEXT, edgecolor='#1e2a3a')
    ax.grid(axis='y', color='#1e2a3a', lw=0.5)
    fig.tight_layout()
    return fig


def _render_history_compare(history: list) -> Figure:
    fig = Figure(figsize=(12, 5), facecolor='#0a0e1a')
    if not history:
        ax = fig.add_subplot(111, facecolor='#0a0e1a')
        ax.text(0.5, 0.5, '이전 실행 결과 없음\n(2회 이상 실행 후 비교 표시)',
                ha='center', va='center', color=C_SUBTEXT, fontsize=11,
                transform=ax.transAxes)
        return fig
    axes = fig.subplots(1, 3, facecolor='#0a0e1a')
    metrics = [
        ('요격률',         'mean_intercept', True,  '%'),
        ('완전 요격 비율', 'full_pass_rate',  True,  '%'),
        ('평균 비용',      'mean_cost',       False, '$'),
    ]
    cmap = ['#3498db', '#2ecc71', '#f39c12', '#e74c3c', '#9b59b6']
    for ax, (title, key, higher_better, unit) in zip(axes, metrics):
        ax.set_facecolor('#0a0e1a')
        vals = [h.get(key, 0) for h in history]
        cols = [cmap[i % len(cmap)] for i in range(len(history))]
        bars = ax.bar(range(len(history)), vals, color=cols, alpha=0.85,
                      edgecolor='#1e2a3a')
        for bar, v in zip(bars, vals):
            label = f"{v:.1%}" if unit == '%' else f"${v:,.0f}"
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + max(vals) * 0.02,
                    label, ha='center', va='bottom',
                    color=C_TEXT, fontsize=11)
        ax.set_title(title, color=C_TEXT, fontsize=13)
        ax.set_xticks(range(len(history)))
        ax.set_xticklabels([f'#{i+1}' for i in range(len(history))],
                           color=C_SUBTEXT, fontsize=11)
        ax.tick_params(colors=C_SUBTEXT, labelsize=11)
        for sp in ax.spines.values():
            sp.set_color('#1e2a3a')
        ax.yaxis.set_major_formatter(
            plt.FuncFormatter(lambda v, _: f"{v:.0%}" if unit == '%'
                              else f"${v/1e6:.1f}M"))
    fig.text(0.5, 0.01,
             '  |  '.join(f'#{i+1}: {h["label"]}' for i, h in enumerate(history)),
             ha='center', va='bottom', color=C_SUBTEXT, fontsize=10)
    fig.suptitle('이전 실행 결과 비교', color=C_TEXT, fontsize=14)
    fig.tight_layout(rect=[0, 0.06, 1, 1])
    return fig


def _render_stress_test(stress: dict) -> Figure:
    """스트레스 테스트 2D 히트맵 — 채널 감소 × 레이더 성능 감소 → 요격률."""
    fig = Figure(figsize=(13, 6), facecolor='#0a0e1a')
    if not stress or 'error' in stress:
        ax = fig.add_subplot(111, facecolor='#0a0e1a')
        msg = stress.get('error', '스트레스 테스트 결과 없음') if stress else '스트레스 테스트 결과 없음'
        ax.text(0.5, 0.5, msg, ha='center', va='center',
                color=C_SUBTEXT, fontsize=11, transform=ax.transAxes)
        return fig

    import numpy as _np
    grid      = _np.array(stress['grid'])
    cvar_grid = _np.array(stress.get('cvar_grid', grid))
    ch_vals   = stress['ch_vals']
    rad_vals  = stress['rad_vals']

    axes = fig.subplots(1, 2)
    titles = ['평균 요격률', 'CVaR (하위 5%)']
    for ax, data, title in zip(axes, [grid, cvar_grid], titles):
        ax.set_facecolor('#0a0e1a')
        im = ax.imshow(data, cmap='RdYlGn', aspect='auto',
                       vmin=0.0, vmax=1.0, origin='lower')
        ax.set_xticks(range(len(rad_vals)))
        ax.set_xticklabels([f'{v}%' for v in rad_vals], color=C_SUBTEXT, fontsize=11)
        ax.set_yticks(range(len(ch_vals)))
        ax.set_yticklabels([f'{v}%' for v in ch_vals], color=C_SUBTEXT, fontsize=11)
        ax.set_xlabel(stress.get('rad_label', '레이더 성능 감소'), color=C_SUBTEXT, fontsize=11)
        ax.set_ylabel(stress.get('ch_label', '유도 채널 감소'), color=C_SUBTEXT, fontsize=11)
        ax.set_title(title, color=C_TEXT, fontsize=13)
        for sp in ax.spines.values():
            sp.set_color('#1e2a3a')
        ax.tick_params(colors=C_SUBTEXT)
        for i in range(data.shape[0]):
            for j in range(data.shape[1]):
                val = data[i, j]
                txt_col = 'black' if val > 0.5 else C_TEXT
                ax.text(j, i, f'{val:.0%}', ha='center', va='center',
                        color=txt_col, fontsize=12, fontweight='bold')
        fig.colorbar(im, ax=ax, format='%.0%%')

    n_cell = stress.get('n_per_cell', '?')
    fig.suptitle(f'스트레스 테스트 — 셀당 {n_cell}회 시뮬레이션',
                 color=C_TEXT, fontsize=14, y=0.98)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    return fig


def _render_sobol_chart(sobol: dict) -> Figure:
    """Sobol 1차·전체 민감도 지수 수평 막대 차트."""
    fig = Figure(figsize=(12, 6), facecolor='#0a0e1a')
    ax  = fig.add_subplot(111, facecolor='#0a0e1a')

    if not sobol or 'error' in sobol:
        msg = sobol.get('error', 'Sobol 분석 결과 없음\n(정밀 모드에서만 실행됩니다)') \
              if sobol else 'Sobol 분석 결과 없음\n(정밀 모드에서만 실행됩니다)'
        ax.text(0.5, 0.5, msg, ha='center', va='center',
                color=C_SUBTEXT, fontsize=12, transform=ax.transAxes)
        ax.set_facecolor('#0a0e1a')
        return fig

    import numpy as _np
    names   = sobol.get('names', [])
    S1      = _np.array(sobol.get('S1', []))
    ST      = _np.array(sobol.get('ST', []))
    S1_conf = _np.array(sobol.get('S1_conf', _np.zeros_like(S1)))
    ST_conf = _np.array(sobol.get('ST_conf', _np.zeros_like(ST)))

    y = _np.arange(len(names))
    h = 0.35
    bars1 = ax.barh(y + h/2, S1, h, xerr=S1_conf, label='S1 (1차)',
                    color='#3498db', alpha=0.85, capsize=4,
                    error_kw={'ecolor': '#7fb3e3', 'linewidth': 1.5})
    barsT = ax.barh(y - h/2, ST, h, xerr=ST_conf, label='ST (전체)',
                    color='#e74c3c', alpha=0.85, capsize=4,
                    error_kw={'ecolor': '#f1948a', 'linewidth': 1.5})

    ax.set_yticks(y)
    ax.set_yticklabels(names, color=C_TEXT, fontsize=12)
    ax.set_xlabel('민감도 지수', color=C_SUBTEXT, fontsize=12)
    ax.set_xlim(0, max(1.0, float(ST.max()) * 1.2) if len(ST) else 1.0)
    ax.tick_params(colors=C_SUBTEXT, labelsize=11)
    for sp in ax.spines.values():
        sp.set_color('#1e2a3a')
    ax.legend(fontsize=11, facecolor='#1c2128', labelcolor=C_TEXT,
              edgecolor='#444c56')
    ax.grid(axis='x', color='#1e2a3a', linewidth=0.7, alpha=0.6)

    n_runs = sobol.get('n_runs', '?')
    npp_str = f'  •  포인트당 {sobol.get("n_per_point",1)}회 평균' if sobol.get('n_per_point',1) > 1 else ''
    ax.set_title(f'Sobol 파라미터 민감도 분석  (총 {n_runs:,}회{npp_str})',
                 color=C_TEXT, fontsize=14)
    fig.tight_layout()
    return fig


def _render_strike_chart(mc: dict) -> Figure:
    """v9.3: MC 적 격침 수 분포 히스토그램 + 평균선."""
    fig = Figure(figsize=(12, 5), facecolor='#0a0e1a')
    ax  = fig.add_subplot(111, facecolor='#0a0e1a')

    e_dest = mc.get('enemy_destroyed', [])
    if not e_dest or all(v == 0 for v in e_dest):
        ax.text(0.5, 0.5,
                "공격 임무 비활성화 또는\n적 수상함 없음",
                ha='center', va='center', color=C_SUBTEXT,
                fontsize=13, transform=ax.transAxes)
        ax.set_facecolor('#0a0e1a')
        return fig

    import numpy as _np
    arr   = _np.array(e_dest, dtype=float)
    mean  = arr.mean()
    mx    = int(arr.max())
    bins  = _np.arange(-0.5, mx + 1.5, 1)
    counts, edges = _np.histogram(arr, bins=bins)
    centers = (edges[:-1] + edges[1:]) / 2

    bars = ax.bar(centers, counts / len(arr) * 100,
                  width=0.7, color='#e74c3c', alpha=0.80,
                  edgecolor='#c0392b', linewidth=0.8)
    ax.axvline(mean, color='#f1c40f', lw=2, ls='--',
               label=f'평균 {mean:.2f}척')

    ax.set_xlabel('격침 적 함정 수', color=C_SUBTEXT, fontsize=12)
    ax.set_ylabel('비율 (%)',       color=C_SUBTEXT, fontsize=12)
    ax.set_title(f'MC 적 격침 수 분포  (n={len(arr)}회)',
                 color=C_TEXT, fontsize=13, pad=8)
    ax.set_xticks(range(mx + 2))
    ax.tick_params(colors=C_SUBTEXT)
    ax.spines[:].set_color('#21262d')
    ax.legend(fontsize=11, facecolor='#161b22', labelcolor=C_TEXT)
    fig.tight_layout()
    return fig


# ════════════════════════════════════════════════════════════════════════════
#  메인 윈도우
# ════════════════════════════════════════════════════════════════════════════
# ── 작전 시나리오 라이브러리 (v11.5) ──────────────────────────────────────────
# 교리 기반 시나리오: 편대·적편대·해역·날씨·계절을 한 번에 세팅. _restore_cfg로 적용.
SCENARIO_LIBRARY = {
    '서해 차단작전': {
        'desc': '북한의 서해 NLL 도발·기습 상륙 시도를 2함대가 차단한다. '
                '연평·백령 협수로 환경에서 북한 수상함·잠수함 복합 위협에 대응.',
        'recommend': '서해 해역방어 (2함대) · 박무 주간 · 대잠 경계 강화',
        'cfg': {
            'fleet_preset': '서해 해역방어 (2함대)',
            'fleet_region': '서해',
            'weather': '흐림 (박무)',
            'season': 'summer',
            'enemy_fleet_mode': 'preset',
            'enemy_fleet_preset': '북한 입체 공격',
        },
    },
    '독도 방어': {
        'desc': '동해 영유권 분쟁 격화 시 독도 근해로 접근하는 적 수상함 편대를 '
                '1함대가 저지한다. 거친 해상 상태에서의 함대 방공·대함전.',
        'recommend': '동해 해역방어 (1함대) · 풍랑 · 함대 분산 배치',
        'cfg': {
            'fleet_preset': '동해 해역방어 (1함대)',
            'fleet_region': '동해 중부',
            'weather': '풍랑 (7~8등급)',
            'season': 'autumn',
            'enemy_fleet_mode': 'preset',
            'enemy_fleet_preset': '수상함 편대전',
        },
    },
    '항모전단 요격': {
        'desc': '중국 랴오닝 항모전단이 동해 북부로 진입한다. 전 이지스 기동전단이 '
                'SM-3/SM-6 다층 방공망으로 함재기·대함미사일 포화를 요격.',
        'recommend': '전 이지스 기동전단 · 맑음 주간 · CEC 협동 교전',
        'cfg': {
            'fleet_preset': '전 이지스 기동전단',
            'fleet_region': '동해 북부',
            'weather': '맑음 (주간)',
            'season': 'summer',
            'enemy_fleet_mode': 'preset',
            'enemy_fleet_preset': '랴오닝 항모전단',
        },
    },
    '북한 포화도발': {
        'desc': '북한이 야간에 단거리 탄도미사일·방사포 40여 발을 동시 발사하는 '
                '포화 공격. BMD 중점 편대가 SM-3/SM-6/해궁 다층 요격으로 대응.',
        'recommend': 'BMD 중점 편대 · 야간 · 이지스 어쇼어·THAAD 연동 권장',
        'cfg': {
            'fleet_preset': 'BMD 중점',
            'fleet_region': '서해',
            'weather': '맑음 (야간)',
            'season': 'winter',
            'enemy_fleet_mode': 'preset',
            'enemy_fleet_preset': '북한 포화 공격 (40발)',
        },
    },
}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"이지스 기동전단 통합 방어 시뮬레이터  {APP_VERSION}")
        self.resize(1800, 1060)
        self._worker         = None
        self._weather_worker = None
        self._result = None
        self._mc     = None
        self._t0     = 0.0
        self._history: list = []  # 이전 실행 결과 히스토리 (최대 5개)
        self._float_mon = FloatingMonitor()

        # ── BUG-1: 탭 전환 디바운스 (200ms) ────────────────────────────────
        self._page_pending_idx: int = -1
        self._page_debounce_timer = QTimer(self)
        self._page_debounce_timer.setSingleShot(True)
        self._page_debounce_timer.setInterval(200)
        self._page_debounce_timer.timeout.connect(self._render_current_page)
        # BUG-1: 차트 캐시 — 동일 result 객체면 재렌더 스킵
        self._page_render_cache: dict = {}   # {page_idx: id(result)}

        self._build_ui()
        self._apply_style()

    # ── UI 구성 ──────────────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setHandleWidth(2)
        root.addWidget(splitter)

        splitter.addWidget(self._build_config_panel())
        splitter.addWidget(self._build_result_panel())
        splitter.setSizes([430, 1070])

        # 상태바
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self._lbl_status = QLabel("준비")
        self._prog       = QProgressBar()
        self._prog.setFixedWidth(180)
        self._prog.setRange(0, 0)
        self._prog.setVisible(False)
        self.status.addWidget(self._lbl_status)
        self.status.addPermanentWidget(self._prog)

        btn_log = QPushButton("📋 실행 로그")
        btn_log.setFixedHeight(22)
        btn_log.setStyleSheet(
            f"QPushButton {{ background:{C_PANEL}; color:{C_SUBTEXT}; border:1px solid {C_BORDER};"
            f" border-radius:3px; padding:0 8px; font-size:12px; }}"
            f"QPushButton:hover {{ color:{C_TEXT}; }}"
        )
        btn_log.clicked.connect(self._open_log_file)
        self.status.addPermanentWidget(btn_log)


    def _open_log_file(self):
        try:
            alive = (hasattr(self, '_log_dialog')
                     and self._log_dialog is not None
                     and self._log_dialog.isVisible())
        except RuntimeError:
            alive = False
        if not alive:
            self._log_dialog = SimLogDialog(self)
            self._log_dialog.restore_requested.connect(self._restore_cfg)
            self._log_dialog.show()
            self._log_dialog.raise_()
            self._log_dialog.activateWindow()
            # 창이 그려진 뒤 데이터 로드 (메인 스레드 블로킹 방지)
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, self._log_dialog._load)
        else:
            self._log_dialog.show()
            self._log_dialog.raise_()
            self._log_dialog.activateWindow()
            from PyQt6.QtCore import QTimer
            QTimer.singleShot(0, self._log_dialog._load)

    def _restore_cfg(self, cfg: dict):
        """실행 기록에서 설정을 복원한다 — 편대·날씨·적군 모드 복원."""
        # 아군 편대
        fleet = cfg.get('fleet_preset', '')
        if fleet and hasattr(self, 'cmb_fleet'):
            idx = self.cmb_fleet.findText(fleet)
            if idx >= 0:
                self.cmb_fleet.setCurrentIndex(idx)
        # 날씨
        weather = cfg.get('weather', '')
        if weather and hasattr(self, 'cmb_weather'):
            idx = self.cmb_weather.findText(weather)
            if idx >= 0:
                self.cmb_weather.setCurrentIndex(idx)
        # v9.12: 작전 해역
        region = cfg.get('fleet_region', '')
        if region and hasattr(self, 'cmb_region'):
            idx = self.cmb_region.findText(region)
            if idx >= 0:
                self.cmb_region.setCurrentIndex(idx)
        # v9.12: 계절 (v10.7: 4계절 확장)
        season = cfg.get('season', '')
        if season and hasattr(self, 'cmb_season'):
            _rmap = {'spring': '봄 (3~5월)', 'summer': '여름 (6~9월)',
                     'autumn': '가을 (10~11월)', 'winter': '겨울 (12~2월)'}
            target = _rmap.get(season, '여름 (6~9월)')
            idx = self.cmb_season.findText(target)
            if idx >= 0:
                self.cmb_season.setCurrentIndex(idx)
        # v9.12: 지형 음영
        if hasattr(self, 'chk_terrain'):
            self.chk_terrain.setChecked(cfg.get('enable_terrain', False))
        if hasattr(self, 'chk_current'):
            self.chk_current.setChecked(cfg.get('enable_current', False))
        # v9.13: 증발 덕팅
        if hasattr(self, 'chk_evap_duct'):
            self.chk_evap_duct.setChecked(cfg.get('enable_evap_duct', False))
        if hasattr(self, 'chk_anti_sam'):
            self.chk_anti_sam.setChecked(cfg.get('enable_anti_sam', False))
        if hasattr(self, 'chk_isa'):
            self.chk_isa.setChecked(cfg.get('enable_isa', False))
        # v9.14: 해협 진입로
        strait_type = cfg.get('strait_type', '')
        if strait_type and hasattr(self, 'cmb_strait_type'):
            reverse = {'korea_west': '서수도 (서→동)',
                       'korea_east': '동수도 (동→서)',
                       'bilateral':  '양방향 협공'}
            label = reverse.get(strait_type, '')
            if label:
                idx = self.cmb_strait_type.findText(label)
                if idx >= 0:
                    self.cmb_strait_type.setCurrentIndex(idx)
        # 적군 모드 — preset / random / manual
        enemy_mode = cfg.get('enemy_fleet_mode', '')
        mode_reverse = {'preset': '프리셋', 'mixed': '혼합 시나리오', 'random': '랜덤'}
        mode_label = mode_reverse.get(enemy_mode, '')
        if mode_label and hasattr(self, 'cmb_enemy_mode'):
            idx = self.cmb_enemy_mode.findText(mode_label)
            if idx >= 0:
                self.cmb_enemy_mode.setCurrentIndex(idx)
        # 적군 프리셋
        enemy_preset = cfg.get('enemy_fleet_preset', '')
        if enemy_preset and hasattr(self, 'cmb_fleet_preset_e'):
            idx = self.cmb_fleet_preset_e.findText(enemy_preset)
            if idx >= 0:
                self.cmb_fleet_preset_e.setCurrentIndex(idx)
        # 전술 체크박스
        if hasattr(self, 'chk_cec'):
            self.chk_cec.setChecked(cfg.get('enable_cec', cfg.get('enable_cec_preassign', True)))
        if hasattr(self, 'chk_multibearing'):
            self.chk_multibearing.setChecked(cfg.get('enable_multibearing', False))
        if hasattr(self, 'chk_cec_jammed'):
            self.chk_cec_jammed.setChecked(cfg.get('enable_cec_jammed', False))
        if hasattr(self, 'chk_ship_evasion'):
            self.chk_ship_evasion.setChecked(cfg.get('enable_ship_evasion', False))
        if hasattr(self, 'chk_radar_off'):
            self.chk_radar_off.setChecked(cfg.get('enable_radar_off', True))
        # 항공 자산 복원
        for attr, key in [('chk_helo','enable_helo'),('chk_p3c','enable_p3c'),
                          ('chk_p8a','enable_p8a'),('chk_f35a','enable_f35a'),
                          ('chk_kf21','enable_kf21'),('chk_fa50','enable_fa50')]:
            if hasattr(self, attr):
                getattr(self, attr).setChecked(cfg.get(key, False))
        self._lbl_status.setText("✅ 설정 복원 완료")


    def _on_scenario_changed(self, name: str):
        """시나리오 선택 시 설명 표시 + 적용 버튼 활성화."""
        sc = SCENARIO_LIBRARY.get(name)
        if sc:
            self.lbl_scenario_desc.setText(sc['desc'] + '\n▸ 권장: ' + sc['recommend'])
            self.btn_apply_scenario.setEnabled(True)
        else:
            self.lbl_scenario_desc.setText('')
            self.btn_apply_scenario.setEnabled(False)

    def _apply_scenario(self):
        """선택한 시나리오 설정을 UI에 일괄 적용 (편대·해역·날씨·계절·적 편대)."""
        name = self.cmb_scenario.currentText()
        sc = SCENARIO_LIBRARY.get(name)
        if not sc:
            return
        self._restore_cfg(sc['cfg'])
        self._lbl_status.setText(f"🎯 '{name}' 시나리오 적용 완료")

    def _build_config_panel(self) -> QWidget:
        # 컨테이너: 스크롤(위) + 고정 하단(모드·실행버튼)으로 구성
        container = QWidget()
        container.setFixedWidth(430)
        container.setStyleSheet(f"background: {C_PANEL};")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"QScrollArea {{ border: none; background: {C_PANEL}; }}")

        inner = QWidget()
        inner.setStyleSheet(f"background: {C_PANEL};")
        layout = QVBoxLayout(inner)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(5)

        # 타이틀
        title = QLabel("⚓ 이지스 기동전단\n통합 방어 시뮬레이터")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont('Malgun Gothic', 17, QFont.Weight.Bold))
        title.setStyleSheet(f"color:{C_ACCENT}; padding: 8px 0;")
        layout.addWidget(title)

        # ── 작전 시나리오 (v11.5) ────────────────────────────────────────
        grp_sc = QGroupBox("🎯 작전 시나리오")
        scl = QVBoxLayout(grp_sc)
        scl.setSpacing(4)
        self.cmb_scenario = NoScrollComboBox()
        self.cmb_scenario.addItems(['— 선택 안 함 —'] + list(SCENARIO_LIBRARY.keys()))
        self.cmb_scenario.setToolTip(
            "교리 기반 작전 시나리오 — 선택 후 '적용'을 누르면 "
            "편대·해역·날씨·계절·적 편대가 한 번에 설정됩니다.")
        self.cmb_scenario.currentTextChanged.connect(self._on_scenario_changed)
        scl.addWidget(self.cmb_scenario)
        self.lbl_scenario_desc = QLabel()
        self.lbl_scenario_desc.setStyleSheet(
            f"color:{C_SUBTEXT}; font-size:14px; padding:2px 0;")
        self.lbl_scenario_desc.setWordWrap(True)
        scl.addWidget(self.lbl_scenario_desc)
        self.btn_apply_scenario = QPushButton("▶ 시나리오 적용")
        self.btn_apply_scenario.setEnabled(False)
        self.btn_apply_scenario.clicked.connect(self._apply_scenario)
        scl.addWidget(self.btn_apply_scenario)
        layout.addWidget(grp_sc)

        # ── 아군 편대 ──────────────────────────────────────────────────────
        grp_f = QGroupBox("🔵 아군 편대")
        fl = QFormLayout(grp_f)
        fl.setSpacing(4)

        self.cmb_fleet   = NoScrollComboBox()
        self.cmb_fleet.addItems(list(V7_FLEET_PRESETS.keys()) if _V7_OK else [])
        if _V7_OK:
            for _i, _n in enumerate(V7_FLEET_PRESETS.keys()):
                self.cmb_fleet.setItemData(_i, self._friendly_preset_tooltip(_n),
                                           Qt.ItemDataRole.ToolTipRole)
        self.cmb_weather = NoScrollComboBox()
        self.cmb_weather.addItems(list(WEATHER_DB.keys()) if _V7_OK else [])
        self.lbl_fleet_detail = QLabel()
        self.lbl_fleet_detail.setStyleSheet(
            f"color:{C_SUBTEXT}; font-size:15px; padding:2px 0;")
        self.lbl_fleet_detail.setWordWrap(True)
        self.cmb_fleet.currentTextChanged.connect(self._update_fleet_detail)

        self.lbl_detect_info = QLabel()
        self.lbl_detect_info.setStyleSheet(
            f"color:{C_ACCENT}; font-size:15px; padding:2px 0;")
        self.lbl_detect_info.setWordWrap(True)
        self.cmb_fleet.currentTextChanged.connect(self._update_detect_info)
        self.cmb_weather.currentTextChanged.connect(self._update_detect_info)

        # v9.12: 작전 해역 / 계절 드롭다운
        self.cmb_region = NoScrollComboBox()
        self.cmb_region.addItems(['동해 북부', '동해 중부', '서해', '대한해협'])
        self.cmb_region.setToolTip(
            "작전 해역 선택 — 소나 탐지(수온약층)·레이더 음영(지형) 보정에 반영됩니다.\n"
            "동해 북부: 쓰시마 난류 약화, 북한한류 영향권, 수온약층 강\n"
            "동해 중부: 쓰시마 난류 주류, 여름 수온약층 최강\n"
            "서해: 평균수심 44m, 여름 냉수괴(YSCBW), 수온약층 10m부터\n"
            "대한해협: 쓰시마 난류 통과로 연중 수온약층 존재"
        )
        self.cmb_season = NoScrollComboBox()
        self.cmb_season.addItems(['봄 (3~5월)', '여름 (6~9월)', '가을 (10~11월)', '겨울 (12~2월)'])
        self.cmb_season.setCurrentIndex(1)  # 기본값: 여름
        self.cmb_season.setToolTip(
            "계절 선택 — 수온약층·대기 굴절·증발 덕팅·고층 바람 CEP에 영향.\n"
            "봄 (3~5월): 황사 시즌, 수온약층 약함, 제트기류 북상 중\n"
            "여름 (6~9월): 수온약층 최강, 쿠로시오 수증기 → ISA 굴절 최대\n"
            "가을 (10~11월): 수온약층 감소 시작, 제트기류 남하 시작\n"
            "겨울 (12~2월): 수온약층 소멸(서해)/약화(동해), 대륙성 한기 → 굴절 최소"
        )
        self.chk_terrain = QCheckBox("지형 음영 적용")
        self.chk_terrain.setToolTip(
            "해역별 산맥 레이더 차폐 효과 적용.\n"
            "동해: 태백·설악(3.4~8.1°) — 저고도 위협 탐지 최대 22% 감소\n"
            "서해: 낭림산맥 원거리(0.4°) — 미약 (~4%)\n"
            "대한해협: 소백산맥(0.9°) — 중간 (~10%)\n"
            "기본값 OFF — 기존 결과와 동일"
        )
        self.chk_terrain.setChecked(False)

        # v10.8: 해류 연동
        self.chk_current = QCheckBox("해류 연동  (ocean_environment_db 해류 벡터 적용)")
        self.chk_current.setChecked(False)
        self.chk_current.setToolTip(
            "v10.8 — 해역별 해류 벡터를 함정·잠수함 위치에 매 tick 누적.\n"
            "동해: 동한난류 북상 (여름 최강 50cm/s)\n"
            "서해: 황해 연안류 (여름 북향·겨울 남향)\n"
            "대한해협: 대마난류 북동향 (~35cm/s)\n"
            "ocean_environment_db.py가 있어야 활성화됩니다."
        )

        self.chk_evap_duct = QCheckBox("증발 덕팅 적용")
        self.chk_evap_duct.setToolTip(
            "대기 하층 수증기 농도 역전으로 레이더 전파가 해면을 따라 굴절.\n"
            "저고도 표적(해면밀착 대함미사일 등)의 탐지거리 증가 효과.\n"
            "동해 여름: EDH 10m, 탐지 ×1.25 / 동해 겨울: EDH 6m, ×1.12\n"
            "풍랑(BF7) 이상 강풍 시 덕트 파괴 → 자동 비활성화.\n"
            "기본값 OFF — 기존 결과와 동일"
        )
        self.chk_evap_duct.setChecked(False)

        self.chk_anti_sam = QCheckBox("적 Anti-SAM 방어 적용")
        self.chk_anti_sam.setToolTip(
            "v10.4 — 적 함정이 접근하는 아군 SAM을 CIWS·SAM으로 요격하는 로직.\n"
            "CIWS (2km 이내): Pk 0.30 즉시 판정.\n"
            "SAM (탐지거리 이내, 최대 50km): 기본 Pk × 0.35 (소형 고속 표적 보정).\n"
            "기본값 OFF — 기존 결과와 동일"
        )
        self.chk_anti_sam.setChecked(False)

        self.chk_isa = QCheckBox("정밀 대기 모델 (ISA+트로포스캐터)")
        self.chk_isa.setToolTip(
            "v10.1 — ICAO 표준 대기 + 기상청 라디오존데 계절별 실측값 적용.\n"
            "중고도(≥500m) 표적: 대기 굴절 지수 증가로 탐지거리 +2~6%.\n"
            "고고도(≥1000m) 표적: 트로포스캐터 산란 추가 +7~16%.\n"
            "  예) 동해 여름 탄도미사일(고도10km): 탐지거리 최대 ×1.23\n"
            "  예) 동해 겨울 순항미사일(고도500m): ×1.03\n"
            "풍랑(BF6) 이상 강풍 시 트로포스캐터 자동 비활성화.\n"
            "기본값 OFF — 기존 결과와 동일"
        )
        self.chk_isa.setChecked(False)

        # v9.14: 해협 통과 시나리오 — 대한해협 선택 시에만 표시
        self.cmb_strait_type = NoScrollComboBox()
        self.cmb_strait_type.addItems(['서수도 (서→동)', '동수도 (동→서)', '양방향 협공'])
        self.cmb_strait_type.setToolTip(
            "해협 통과 방향 선택 — 위협 접근 방위를 동/서 방향 ±30° 이내로 제한합니다.\n"
            "서수도 (49.5 km): 서쪽(일본해)에서 동쪽으로 접근 — 기동 공간 가장 좁음\n"
            "동수도 (98 km): 동쪽(태평양)에서 서쪽으로 접근 — 기동 공간 중간\n"
            "양방향 협공: 동수도·서수도 동시 협공 — 최고 난이도\n"
            "잠수함 잠항 수심은 해협 임계수심(서수도 130m / 동수도 115m)으로 자동 제한."
        )
        self._row_strait_label = QLabel("해협 진입로")
        self._row_strait_label.setStyleSheet(f"color:{C_TEXT}; font-size:15px;")

        def _on_region_changed(txt: str):
            visible = (txt == '대한해협')
            self._row_strait_label.setVisible(visible)
            self.cmb_strait_type.setVisible(visible)
            if visible:
                self.chk_terrain.setChecked(True)   # 소백산맥 음영 자동 활성화
            else:
                self.chk_terrain.setChecked(False)

        self.cmb_region.currentTextChanged.connect(_on_region_changed)
        _on_region_changed(self.cmb_region.currentText())

        fl.addRow("편대 프리셋", self.cmb_fleet)
        fl.addRow("",            self.lbl_fleet_detail)
        fl.addRow("날씨",        self.cmb_weather)
        fl.addRow("작전 해역",   self.cmb_region)
        fl.addRow("계절",        self.cmb_season)
        fl.addRow("",            self.chk_terrain)
        fl.addRow("",            self.chk_evap_duct)
        fl.addRow("",            self.chk_anti_sam)
        fl.addRow("",            self.chk_isa)
        fl.addRow(self._row_strait_label, self.cmb_strait_type)
        fl.addRow("탐지 정보",   self.lbl_detect_info)

        # 랜덤 배치 — 항상 활성화 (반경 10km 고정)
        rp_row = QHBoxLayout()
        lbl_rp = QLabel("함정 위치 랜덤 배치  (반경 10 km 고정)")
        lbl_rp.setStyleSheet(f"color:{C_SUBTEXT}; font-size:15px;")
        rp_row.addWidget(lbl_rp)
        fl.addRow("", rp_row)
        layout.addWidget(grp_f)


        # ── 적군 편대 (포팅 A) ────────────────────────────────────────────
        grp_e = QGroupBox("🔴 적군 편대")
        el = QVBoxLayout(grp_e)
        el.setSpacing(4)

        # 모드 선택
        mode_row = QWidget(); mode_rl = QHBoxLayout(mode_row)
        mode_rl.setContentsMargins(0, 0, 0, 0)
        mode_rl.addWidget(QLabel("모드:"))
        self.cmb_enemy_mode = NoScrollComboBox()
        self.cmb_enemy_mode.addItems(['프리셋', '혼합 시나리오', '랜덤'])
        mode_rl.addWidget(self.cmb_enemy_mode, stretch=1)
        el.addWidget(mode_row)

        # 프리셋 선택 (프리셋 모드용)
        self.cmb_fleet_preset_e = NoScrollComboBox()
        self.cmb_fleet_preset_e.addItems(list(V7_ENEMY_FLEET_PRESETS.keys()) if _V7_OK else [])
        if _V7_OK:
            for _i, _n in enumerate(V7_ENEMY_FLEET_PRESETS.keys()):
                self.cmb_fleet_preset_e.setItemData(_i, self._enemy_preset_tooltip(_n),
                                                    Qt.ItemDataRole.ToolTipRole)
        self.cmb_fleet_preset_e.currentTextChanged.connect(self._update_enemy_preset_detail)
        el.addWidget(self.cmb_fleet_preset_e)

        # NEW-A: 혼합 시나리오 선택 (혼합 모드용)
        self._mixed_row = QWidget(); mixed_rl = QVBoxLayout(self._mixed_row)
        mixed_rl.setContentsMargins(0, 0, 0, 0); mixed_rl.setSpacing(3)
        self.cmb_mixed_scenario = NoScrollComboBox()
        self.cmb_mixed_scenario.addItems(list(V7_MIXED_SCENARIOS.keys()) if _V7_OK else [])
        self.cmb_mixed_scenario.currentTextChanged.connect(self._update_mixed_scenario_detail)
        mixed_rl.addWidget(self.cmb_mixed_scenario)
        self.lbl_mixed_detail = QLabel()
        self.lbl_mixed_detail.setStyleSheet(
            f"color:{C_SUBTEXT}; font-size:14px; padding:2px 0;")
        self.lbl_mixed_detail.setWordWrap(True)
        mixed_rl.addWidget(self.lbl_mixed_detail)
        el.addWidget(self._mixed_row)

        self.lbl_enemy_preset_detail = QLabel()
        self.lbl_enemy_preset_detail.setStyleSheet(
            f"color:{C_SUBTEXT}; font-size:15px; padding:2px 0;")
        self.lbl_enemy_preset_detail.setWordWrap(True)
        el.addWidget(self.lbl_enemy_preset_detail)

        # 랜덤 난이도 + 시드 (랜덤 모드용)
        self._rand_row = QWidget(); rand_rl = QHBoxLayout(self._rand_row)
        rand_rl.setContentsMargins(0, 0, 0, 0); rand_rl.setSpacing(4)
        self.cmb_difficulty = NoScrollComboBox()
        self.cmb_difficulty.addItems(list(V7_RANDOM_CFG.keys()) if _V7_OK else ['보통'])
        self.cmb_difficulty.setCurrentText('보통')
        self.cmb_difficulty.currentTextChanged.connect(self._update_difficulty_tooltip)
        self.spn_seed = NoScrollSpinBox(); self.spn_seed.setRange(0, 99999); self.spn_seed.setValue(0)
        self.spn_seed.setPrefix("씨앗: ")
        rand_rl.addWidget(self.cmb_difficulty, stretch=1)
        rand_rl.addWidget(self.spn_seed, stretch=1)
        el.addWidget(self._rand_row)

        self.cmb_enemy_mode.currentIndexChanged.connect(self._on_enemy_mode_changed)
        self._on_enemy_mode_changed(0)  # 초기 상태 적용 (기본: 프리셋)
        if _V7_OK:
            if self.cmb_fleet_preset_e.count():
                self._update_enemy_preset_detail(self.cmb_fleet_preset_e.currentText())
            if self.cmb_difficulty.count():
                self._update_difficulty_tooltip(self.cmb_difficulty.currentText())
            if self.cmb_mixed_scenario.count():
                self._update_mixed_scenario_detail(self.cmb_mixed_scenario.currentText())
        layout.addWidget(grp_e)

        # ── 전술 옵션 (포팅 B) ────────────────────────────────────────────
        grp_t = QGroupBox("⚙️ 전술 옵션")
        tl = QVBoxLayout(grp_t)
        tl.setSpacing(4)

        self.chk_ecm   = QCheckBox("ECM 재밍 (거리 반비례 Pk 감소)");  self.chk_ecm.setChecked(True)
        self.chk_eva   = QCheckBox("회피 기동 (종말·함정 어뢰)");       self.chk_eva.setChecked(True)
        self.chk_dcoy  = QCheckBox("음향 기만기 AN/SLQ-25 (어뢰)");    self.chk_dcoy.setChecked(True)
        self.chk_sd    = QCheckBox("적 자체방어 (CIWS + 채프/플레어)"); self.chk_sd.setChecked(True)

        for chk in [self.chk_ecm, self.chk_eva, self.chk_dcoy, self.chk_sd]:
            chk.setStyleSheet(f"color:{C_TEXT}; font-size:16px;")
            tl.addWidget(chk)

        grp_t.hide()
        layout.addWidget(grp_t)

        # ── 항공 자산 (포팅 C + v10.5 CAP) ──────────────────────────────────
        grp_ac = QGroupBox("✈️ 항공 자산")
        acl = QVBoxLayout(grp_ac)
        acl.setSpacing(4)

        self.chk_helo = QCheckBox("AW-159 와일드캣  (함재 헬기, 청상어 2발, 140km)")
        self.chk_p3c  = QCheckBox("P-3C 오라이온  (포항기지, Mk.46 4발, 소노부이+15km)")
        self.chk_p8a  = QCheckBox("P-8A 포세이돈  (포항기지, Mk.46 5발, 소노부이+18km)")

        # v10.5: 한국 공군 CAP
        self.chk_f35a = QCheckBox("F-35A 라이트닝 II  (청주기지, AIM-120D×4, CAP 600km)")
        self.chk_f35a.setToolTip(
            "스텔스 CAP — BVR 교전 AIM-120D (Pk 65%, 사거리 160km).\n"
            "청주기지 출격 준비 30분. 탑재 4발, 전천후 운용."
        )
        self.chk_kf21 = QCheckBox("KF-21 보라매  (대구기지, IRIS-T/AIM-120C×6, CAP 500km)")
        self.chk_kf21.setToolTip(
            "다목적 CAP — IRIS-T SL + AIM-120C 복합 탑재 (Pk 55%, 사거리 80km).\n"
            "대구기지 출격 준비 20분. 탑재 6발."
        )
        self.chk_fa50 = QCheckBox("FA-50 파이팅이글  (원주기지, AIM-9X×4, CAP 400km)")
        self.chk_fa50.setToolTip(
            "경전투 CAP — AIM-9X 단거리 (Pk 45%, 사거리 35km).\n"
            "원주기지 출격 준비 15분. 탑재 4발."
        )

        for chk in [self.chk_helo, self.chk_p3c, self.chk_p8a,
                    self.chk_f35a, self.chk_kf21, self.chk_fa50]:
            chk.setChecked(False)
            chk.setStyleSheet(f"color:{C_TEXT}; font-size:16px;")
            acl.addWidget(chk)

        grp_ac.hide()
        layout.addWidget(grp_ac)

        # ── 방어 전술 옵션 ─────────────────────────────────────────────────
        grp_def = QGroupBox("🛡️ 방어 전술")
        defl = QVBoxLayout(grp_def)
        defl.setSpacing(4)

        self.chk_layered = QCheckBox("다층 방어  (KDX-III-B2 → B1 → KDX-II → FFX 순서)")
        self.chk_layered.setChecked(True)
        self.chk_layered.setToolTip(
            "1차 교전 함정(KDX-III Batch II)이 요격 실패 시 다음 레이어(Batch I → KDX-II → FFX)가 자동 인계.\n"
            "우선순위 정렬로 최고 성능 함정이 항상 먼저 교전합니다."
        )

        self.chk_cec = QCheckBox("CEC 협동 교전  (탐지 커버리지 통합)")
        self.chk_cec.setChecked(True)   # 기본 ON — 이지스 전단 실전 운용 표준
        self.chk_cec.setToolTip(
            "v10.4 — Cooperative Engagement Capability (협동 교전 능력).\n"
            "이지스 Link-16 데이터링크로 전단 탐지 정보 공유:\n"
            "  · 탐지 커버리지 통합: 한 함이 탐지한 위협을 전 함정이 교전 가능\n"
            "    예) KDX-III(900km 탐지) → FFX-I(100km 탐지 한계 초과 교전 가능)\n"
            "  · SAM 사전 동시 배정: 1차+2차 함정 동시 발사 (살보 +1)\n"
            "  · CEC 중계 교전 Pk ×0.90 (자체 트랙 없이 데이터링크만 의존)\n"
            "OFF 시: 각 함정은 자체 탐지거리 내 위협만 교전 가능."
        )

        self.chk_multibearing = QCheckBox("다방위 공격  (여러 방향에서 동시 접근)")
        self.chk_multibearing.setChecked(False)
        self.chk_multibearing.setToolTip(
            "적 위협이 전방위(0°~360°) 무작위 방향에서 접근합니다.\n"
            "OFF 시 기본 단일 방향 접근."
        )

        self.chk_cec_jammed = QCheckBox("CEC 두절  (재밍 → 함정 독립 교전)")
        self.chk_cec_jammed.setChecked(False)
        self.chk_cec_jammed.setToolTip(
            "적 전자전으로 CEC 네트워크가 차단됩니다.\n"
            "각 함정이 독립적으로 교전 — 다층 방어 무력화.\n"
            "CEC 사전 배정이 ON이어도 강제 비활성화됩니다."
        )

        self.chk_ship_evasion = QCheckBox("함정 회피 기동  (적 미사일 15km 이내 지그재그)")
        self.chk_ship_evasion.setChecked(False)
        self.chk_ship_evasion.setToolTip(
            "적 대함미사일이 15km 이내 접근 시\n"
            "아군 함정이 지그재그 회피 기동으로 피탄율을 낮춥니다."
        )

        self.chk_radar_off = QCheckBox("레이더 OFF 전술  (ARM 탐지 시 8초 레이더 차단)")
        self.chk_radar_off.setChecked(True)
        self.chk_radar_off.setToolTip(
            "적 대방사미사일(ARM)이 탐지 범위 내 진입 시\n"
            "레이더를 8초간 꺼서 ARM의 유도 신호를 차단합니다.\n"
            "레이더 OFF 중에는 신규 위협 탐지 불가 (기존 추적은 유지).\n"
            "OFF하지 않으면 ARM이 레이더를 직격할 수 있습니다."
        )

        # v10.7: 전술 의사결정 모드
        self.chk_tactical = QCheckBox("전술 의사결정 모드  (구간마다 시뮬 일시정지)")
        self.chk_tactical.setChecked(False)
        self.chk_tactical.setToolTip(
            "v10.7 — 전술 의사결정 모드 (워게임 / 훈련용).\n"
            f"매 {30}초 구간마다 시뮬레이션이 일시 정지됩니다.\n"
            "  · 현재 위협 현황 + 아군 함정 상태 표시\n"
            "  · 다음 구간 무기 우선순위 (SM-2 / SM-6 / ESSM / 자동) 선택\n"
            "  · 살보 수 결정 (1~3발) → 확인 후 재개\n"
            "MC 분석에는 적용되지 않습니다 (단일 시뮬 전용)."
        )

        # 적 편대 전술 기동
        tactics_row = QHBoxLayout()
        lbl_tactics = QLabel("적 전술 기동:")
        lbl_tactics.setStyleSheet(f"color:{C_SUBTEXT}; font-size:15px;")
        self.cmb_enemy_tactics = NoScrollComboBox()
        self.cmb_enemy_tactics.addItems(['없음', 'V자 대형', '포위 기동'])
        self.cmb_enemy_tactics.setToolTip(
            "없음: 기본 분산 접근\n"
            "V자 대형: 선두 1기 + 양익 전개\n"
            "포위 기동: 전방위 동시 포위 (다방위 강화)"
        )
        tactics_row.addWidget(lbl_tactics)
        tactics_row.addWidget(self.cmb_enemy_tactics, stretch=1)

        # 적 전술 AI (채널 포화 / 시차 공격 / 약점 공략)
        ai_tactic_row = QHBoxLayout()
        lbl_ai_tactic = QLabel("전술 AI:")
        lbl_ai_tactic.setStyleSheet(f"color:{C_SUBTEXT}; font-size:15px;")
        self.cmb_ai_tactic = NoScrollComboBox()
        self.cmb_ai_tactic.addItems(['없음', '채널 포화', '시차 공격', '약점 공략'])
        self.cmb_ai_tactic.setToolTip(
            "없음: 기본 동시 접근\n"
            "채널 포화: 아군 교전 채널 수 ×1.5 위협 자동 증폭 — 방어망 과부하\n"
            "시차 공격: 고속(탄도·HGV) 선발 → 채널 소모 → 순항미사일 후속 (+30~60초)\n"
            "약점 공략: 모든 위협이 단일 방향 집중 접근 — 레이더 사각 공략"
        )
        ai_tactic_row.addWidget(lbl_ai_tactic)
        ai_tactic_row.addWidget(self.cmb_ai_tactic, stretch=1)

        for chk in [self.chk_layered, self.chk_cec, self.chk_multibearing,
                    self.chk_cec_jammed, self.chk_ship_evasion, self.chk_radar_off,
                    self.chk_tactical]:
            chk.setStyleSheet(f"color:{C_TEXT}; font-size:16px;")
            defl.addWidget(chk)
        defl.addLayout(tactics_row)
        defl.addLayout(ai_tactic_row)

        # 시뮬 시드
        seed_row = QHBoxLayout()
        lbl_seed = QLabel("시뮬 시드  (0=랜덤, 재현 시 동일 값 입력)")
        lbl_seed.setStyleSheet(f"color:{C_SUBTEXT}; font-size:15px;")
        self.spn_sim_seed = NoScrollSpinBox()
        self.spn_sim_seed.setRange(0, 99999)
        self.spn_sim_seed.setValue(0)
        self.spn_sim_seed.setFixedWidth(80)
        seed_row.addWidget(lbl_seed)
        seed_row.addStretch()
        seed_row.addWidget(self.spn_sim_seed)
        defl.addLayout(seed_row)

        grp_def.hide()
        layout.addWidget(grp_def)

        # ── 공격 임무 옵션 (v9.3) ─────────────────────────────────────────────
        grp_strike = QGroupBox("⚔️ 공격 임무 (아군 대함 공격)")
        strl = QFormLayout(grp_strike)
        strl.setSpacing(6)

        self.chk_strike = QCheckBox("공격 임무 활성화 (적 수상함 자동 공격)")
        self.chk_strike.setChecked(True)
        self.chk_strike.setStyleSheet(f"color:{C_TEXT}; font-size:16px;")
        self.chk_strike.setToolTip(
            "ON: 아군 함정이 탐지 범위 내 적 수상함을 해성·하푼으로 자동 공격합니다.\n"
            "OFF: 방어 전용 모드 (공격 임무 비활성화)."
        )
        strl.addRow("", self.chk_strike)

        self.spn_haesong2 = NoScrollSpinBox()
        self.spn_haesong2.setRange(0, 32); self.spn_haesong2.setValue(8)
        self.spn_haesong2.setToolTip("함정당 해성-II 재고. 기본 8발.")
        strl.addRow("해성-II 재고 (함당)", self.spn_haesong2)

        self.spn_harpoon = NoScrollSpinBox()
        self.spn_harpoon.setRange(0, 16); self.spn_harpoon.setValue(4)
        self.spn_harpoon.setToolTip("함정당 하푼 Block II 재고. 기본 4발.")
        strl.addRow("하푼 재고 (함당)", self.spn_harpoon)

        # v9.4: 현무-4 지상 발사 재고
        self.spn_hyunmoo4 = NoScrollSpinBox()
        self.spn_hyunmoo4.setRange(0, 20); self.spn_hyunmoo4.setValue(0)
        self.spn_hyunmoo4.setToolTip(
            "현무-4 ASBM 지상 발사 재고. 기본 0발 (비활성).\n"
            "사거리 800km, Mach 8~10 종말 속도 — 적 SAM 요격 극히 어려움.\n"
            "60초 간격으로 1발씩 발사 (재보급 준비 시간)."
        )
        strl.addRow("현무-4 재고 (지상 발사)", self.spn_hyunmoo4)

        grp_strike.hide()
        layout.addWidget(grp_strike)

        # v9.11: 이지스 어쇼어 + THAAD 지상 BMD
        grp_bmd = QGroupBox("🛡 지상 BMD 자산")
        bmdl = QFormLayout(grp_bmd)
        bmdl.setSpacing(6)

        self.chk_ashore = QCheckBox("이지스 어쇼어 연동")
        self.chk_ashore.setToolTip(
            "성주 해군기지 이지스 어쇼어 SM-3 Block IIA 연동.\n"
            "탄도미사일·HGV를 중간단계(고도 ≥ 40km)에서 선제 요격.\n"
            "함정 SM-3보다 먼저 교전 — 함정 SM-3은 소진 시 백업만."
        )
        bmdl.addRow("", self.chk_ashore)

        self.spn_ashore_sm3 = NoScrollSpinBox()
        self.spn_ashore_sm3.setRange(4, 48)
        self.spn_ashore_sm3.setValue(24)
        self.spn_ashore_sm3.setEnabled(False)
        self.spn_ashore_sm3.setToolTip("어쇼어 SM-3 Block IIA 재고 (기본 24발).")
        bmdl.addRow("  어쇼어 SM-3 재고", self.spn_ashore_sm3)
        self.chk_ashore.toggled.connect(self.spn_ashore_sm3.setEnabled)

        self.chk_thaad = QCheckBox("THAAD 연동 (성주 기지)")
        self.chk_thaad.setToolTip(
            "성주 기지 THAAD(終末高高度防禦) 연동 (美 육군 운용).\n"
            "탄도미사일·HGV 종말단계(고도 10~150km)를 hit-to-kill 요격.\n"
            "어쇼어 SM-3 → THAAD → 함정 SM-3 순으로 교전."
        )
        bmdl.addRow("", self.chk_thaad)

        self.spn_thaad = NoScrollSpinBox()
        self.spn_thaad.setRange(4, 48)
        self.spn_thaad.setValue(24)
        self.spn_thaad.setEnabled(False)
        self.spn_thaad.setToolTip("THAAD 요격탄 재고 (기본 24발).")
        bmdl.addRow("  THAAD 요격탄 재고", self.spn_thaad)
        self.chk_thaad.toggled.connect(self.spn_thaad.setEnabled)

        layout.addWidget(grp_bmd)


        # ── C&D 시간 설정 (고정값) ────────────────────────────────────────
        grp_cd = QGroupBox("⏱️ C&&D 시간 설정")
        cdl = QHBoxLayout(grp_cd)
        cdl.setSpacing(16)
        lbl_cd_fixed = QLabel("C&&D  10초  /  확인  3초  (고정)")
        lbl_cd_fixed.setStyleSheet(f"color:{C_SUBTEXT}; font-size:15px;")
        cdl.addWidget(lbl_cd_fixed)
        layout.addWidget(grp_cd)

        # ── 시뮬레이션 모드 선택 ─────────────────────────────────────────────
        grp_mc = QGroupBox("📊 시뮬레이션 모드")
        mcl = QVBoxLayout(grp_mc)
        mcl.setSpacing(6)
        lbl_mode = QLabel("정밀도:")
        lbl_mode.setStyleSheet(f"color:{C_SUBTEXT}; font-size:15px;")
        self.cmb_sim_mode = QComboBox()
        self.cmb_sim_mode.addItems(["⚡ 빠름  (5,000회)", "📊 표준  (10,000회)", "🔬 정밀  (100,000회)"])
        self.cmb_sim_mode.setCurrentIndex(1)
        self.cmb_sim_mode.setFixedHeight(32)
        self.cmb_sim_mode.setStyleSheet(f"""
            QComboBox {{
                background: #1c2128; color: #e6edf3;
                border: 1px solid #444c56; border-radius: 4px;
                font-size: 14px; padding: 2px 8px;
            }}
            QComboBox QAbstractItemView {{
                background: #161b22; color: #e6edf3;
                selection-background-color: #3498db;
            }}
        """)
        lbl_mode_hint = QLabel()
        lbl_mode_hint.setStyleSheet(f"color:{C_SUBTEXT}; font-size:12px;")

        # Sobol 포인트당 반복 수 (정밀 모드 전용)
        lbl_npp = QLabel("Sobol 포인트당 반복:")
        lbl_npp.setStyleSheet(f"color:{C_SUBTEXT}; font-size:13px;")
        self.spn_sobol_npp = QSpinBox()
        self.spn_sobol_npp.setRange(1, 10)
        self.spn_sobol_npp.setValue(3)
        self.spn_sobol_npp.setFixedWidth(52)
        self.spn_sobol_npp.setFixedHeight(28)
        self.spn_sobol_npp.setToolTip(
            "Sobol 분석 시 각 파라미터 조합을 몇 번 반복해 평균낼지.\n"
            "1회: 빠름 (~32,768회) / 3회: 권장 (~98,304회) / 5회: 고정밀 (~163,840회)\n"
            "확률적 시뮬레이션의 노이즈를 √K배 줄여 민감도 지수 신뢰도 향상.\n"
            "정밀 모드 선택 시에만 사용됩니다.")
        self.spn_sobol_npp.setStyleSheet(
            f"background:#1c2128; color:#e6edf3; border:1px solid #444c56; font-size:13px;")
        self.spn_sobol_npp.setEnabled(False)  # 정밀 모드일 때만 활성화

        lbl_mode_hint = QLabel()
        lbl_mode_hint.setStyleSheet(f"color:{C_SUBTEXT}; font-size:12px;")
        self._lbl_sobol_total = QLabel()
        self._lbl_sobol_total.setStyleSheet(f"color:{C_SUBTEXT}; font-size:12px;")

        def _update_sobol_total():
            npp = self.spn_sobol_npp.value()
            total = 32_768 * npp
            self._lbl_sobol_total.setText(f"(총 ~{total:,}회)")

        def _update_mode_hint(idx):
            hints = [
                "LHS 샘플링  •  CVaR 분석  •  스트레스 테스트 (셀당 300회)",
                "LHS 샘플링  •  CVaR 분석  •  스트레스 테스트 (셀당 500회)",
                "LHS 샘플링  •  CVaR  •  스트레스 (셀당 3,000회)  •  Sobol 민감도",
            ]
            lbl_mode_hint.setText(hints[idx])
            is_precision = (idx == 2)
            self.spn_sobol_npp.setEnabled(is_precision)
            lbl_npp.setStyleSheet(
                f"color:{C_TEXT if is_precision else C_SUBTEXT}; font-size:13px;")
            self._lbl_sobol_total.setVisible(is_precision)

        self.cmb_sim_mode.currentIndexChanged.connect(_update_mode_hint)
        self.spn_sobol_npp.valueChanged.connect(_update_sobol_total)
        _update_mode_hint(1)
        _update_sobol_total()

        row1 = QHBoxLayout()
        row1.addWidget(lbl_mode)
        row1.addWidget(self.cmb_sim_mode)
        row1.addStretch()
        mcl.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(lbl_npp)
        row2.addWidget(self.spn_sobol_npp)
        row2.addWidget(self._lbl_sobol_total)
        row2.addStretch()
        mcl.addLayout(row2)

        mcl.addWidget(lbl_mode_hint)
        # 초기 함대 편성 + 탐지 정보 레이블
        if _V7_OK and self.cmb_fleet.count():
            self._update_fleet_detail(self.cmb_fleet.currentText())
            self._update_detect_info()

        layout.addStretch()
        scroll.setWidget(inner)

        # ── 고정 하단 영역 (스크롤 밖 — 항상 표시) ───────────────────────
        bottom = QWidget()
        bottom.setStyleSheet(
            f"background:{C_PANEL}; border-top: 1px solid #2a3a4a;")
        bottom_layout = QVBoxLayout(bottom)
        bottom_layout.setContentsMargins(8, 6, 8, 8)
        bottom_layout.setSpacing(6)

        bottom_layout.addWidget(grp_mc)

        self.btn_run = QPushButton("🚀  시뮬레이션 실행")
        self.btn_run.setFixedHeight(44)
        self.btn_run.setFont(QFont('Malgun Gothic', 15))
        self.btn_run.clicked.connect(self._run_sim)
        bottom_layout.addWidget(self.btn_run)

        if not _V7_OK:
            err_lbl = QLabel(f"⚠️ engine_v7 로드 실패\n{_V7_ERR}")
            err_lbl.setStyleSheet(f"color:{C_RED}; font-size:15px;")
            err_lbl.setWordWrap(True)
            bottom_layout.addWidget(err_lbl)
            self.btn_run.setEnabled(False)

        container_layout.addWidget(scroll, stretch=1)
        container_layout.addWidget(bottom)
        return container

    def _build_result_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        # 핵심 지표 카드 영역
        self.card_row = QWidget()
        card_layout = QHBoxLayout(self.card_row)
        card_layout.setContentsMargins(12, 8, 12, 0)
        card_layout.setSpacing(8)

        self._cards = {}
        card_defs = [
            ('요격률 (MC)',      'intercept'),
            ('완전 요격 비율',   'full_pass'),
            ('CVaR (최악 5%)',   'cvar'),
            ('아군 피격',        'friendly_hit'),
            ('적 격침',          'enemy_dest'),
            ('총 비용',          'cost'),
            ('항공 출격',        'aircraft'),
        ]
        for label, key in card_defs:
            card = QGroupBox(label)
            card.setFixedHeight(72)
            cl = QVBoxLayout(card)
            lbl = QLabel("—")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setFont(QFont('Malgun Gothic', 17, QFont.Weight.Bold))
            lbl.setStyleSheet(f"color:{C_ACCENT};")
            cl.addWidget(lbl)
            card_layout.addWidget(card)
            self._cards[key] = lbl

        layout.addWidget(self.card_row)

        # Pk 추정값 경고 + VLS 소진 경고
        notice_row = QWidget()
        notice_rl  = QHBoxLayout(notice_row)
        notice_rl.setContentsMargins(12, 0, 12, 0)
        notice_rl.setSpacing(12)

        lbl_pk_note = QLabel(
            "⚠  Pk 수치는 공개 자료 기반 추정값 (±15~20%) — 실측 데이터 아님")
        lbl_pk_note.setStyleSheet(
            f"color:#e67e22; font-size:11px;")
        notice_rl.addWidget(lbl_pk_note)

        self._lbl_vls_warn = QLabel("")
        self._lbl_vls_warn.setStyleSheet(
            f"color:{C_RED}; font-size:11px; font-weight:bold;")
        notice_rl.addWidget(self._lbl_vls_warn)
        notice_rl.addStretch()
        layout.addWidget(notice_row)

        # 내보내기 버튼 행
        export_row = QWidget()
        export_rl  = QHBoxLayout(export_row)
        export_rl.setContentsMargins(12, 4, 12, 0)
        export_rl.setSpacing(6)
        export_rl.addStretch()
        self.btn_excel = QPushButton("📊 Excel 보고서")
        self.btn_pdf   = QPushButton("📄 PDF 보고서")
        for b in [self.btn_excel, self.btn_pdf]:
            b.setFixedHeight(28)
            b.setStyleSheet(
                f"background:{C_PANEL}; color:{C_TEXT}; "
                f"border:1px solid #3a5a7a; font-size:15px; padding:0 8px;")
        self.btn_excel.clicked.connect(self._export_excel)
        self.btn_pdf.clicked.connect(self._export_pdf)
        export_rl.addWidget(self.btn_excel)
        export_rl.addWidget(self.btn_pdf)

        # 시드 표시 레이블 (재현용)
        self._lbl_seed_used = QLabel("")
        self._lbl_seed_used.setStyleSheet(f"color:{C_SUBTEXT}; font-size:12px;")
        export_rl.addSpacing(12)
        export_rl.addWidget(self._lbl_seed_used)
        layout.addWidget(export_row)

        # ── 사이드바 + QStackedWidget ─────────────────────────────────────
        self.tab_engagement  = EngagementAnalysisTab()
        self.tab_mc_canvas   = ChartPageWidget()
        self.tab_req         = self._build_req_tab()
        self.tab_weather     = self._build_weather_tab()
        self.tab_log         = self._build_log_tab()
        self.tab_channel     = ChartPageWidget()
        self.tab_sysmon      = SysMonitorTab()
        self.tab_cost_eff    = ChartPageWidget()
        self.tab_ammo_curve  = ChartPageWidget()
        self.tab_ci          = ChartPageWidget()
        self.tab_timeline    = ChartPageWidget()
        self.tab_sensitivity = ChartPageWidget()   # 백그라운드 렌더 (MplCanvas→ChartPageWidget)
        self.tab_min_stock   = ChartPageWidget()   # 백그라운드 렌더
        self.tab_bearing     = ChartPageWidget()
        self.tab_req_radar   = ChartPageWidget()
        self.tab_threat_type = ChartPageWidget()
        self.tab_vuln_time   = ChartPageWidget()
        self.tab_history     = ChartPageWidget()
        self.tab_stress      = ChartPageWidget()   # 스트레스 테스트 히트맵
        self.tab_sobol       = ChartPageWidget()   # Sobol 민감도 분석
        self.tab_subsystem   = self._build_subsystem_tab()  # 서브시스템 피해 현황
        self.tab_optimize    = ChartPageWidget()   # 최적 무기 조합 추천
        self.tab_ab_compare  = self._build_ab_compare_tab()  # A/B 편대 비교
        self.tab_cec_compare = ChartPageWidget()   # CEC 효과 비교
        self.tab_strike      = self._build_strike_tab()  # v9.3 공격 결과
        self.tab_heatmap     = self._build_heatmap_tab()  # v9.5 생존성 히트맵

        # 사이드바 (v8.26: AccordionSidebar)
        self._sidebar = AccordionSidebar()
        self._sidebar.setFixedWidth(200)
        self._sidebar.setStyleSheet(
            f"border-right: 1px solid {C_BORDER};")

        # QStackedWidget (인덱스 0~25 유지 — AccordionSidebar와 동일 매핑)
        self._stack = QStackedWidget()
        for w in [
            self.tab_engagement,  # 0
            self.tab_mc_canvas,   # 1
            self.tab_req,         # 2
            self.tab_weather,     # 3
            self.tab_log,         # 4
            self.tab_channel,     # 5
            self.tab_sysmon,      # 6
            self.tab_cost_eff,    # 7
            self.tab_ammo_curve,  # 8
            self.tab_ci,          # 9
            self.tab_timeline,    # 10
            self.tab_sensitivity, # 11
            self.tab_min_stock,   # 12
            self.tab_bearing,     # 13
            self.tab_req_radar,   # 14
            self.tab_threat_type, # 15
            self.tab_vuln_time,   # 16
            self.tab_history,     # 17
            self.tab_stress,      # 18
            self.tab_sobol,       # 19
            self.tab_subsystem,   # 20
            self.tab_optimize,    # 21
            self.tab_ab_compare,  # 22
            self.tab_cec_compare, # 23
            self.tab_strike,      # 24
            self.tab_heatmap,     # 25
        ]:
            self._stack.addWidget(w)

        # 연결
        self._sidebar.item_selected.connect(self._stack.setCurrentIndex)
        self._sidebar.item_selected.connect(self._on_page_changed)

        # body (사이드바 + 스택)
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)
        body_layout.addWidget(self._sidebar)
        body_layout.addWidget(self._stack, stretch=1)
        layout.addWidget(body, stretch=1)

        # 지연 렌더링 dirty 집합 초기화
        self._page_dirty: set = set()

        return panel

    def _on_page_changed(self, idx: int):
        """사이드바 선택 시 200ms 디바운스 후 지연 렌더링 (BUG-1)."""
        self._page_pending_idx = idx
        self._page_debounce_timer.start()

    def _render_current_page(self):
        """디바운스 만료 후 실제 페이지 렌더링 — 동일 데이터 재렌더 스킵 (BUG-1)."""
        idx = self._page_pending_idx
        if self._result is None or idx < 0:
            return
        if idx not in self._page_dirty:
            return
        # 동일 result 객체면 재렌더 스킵
        result_id = id(self._result)
        if self._page_render_cache.get(idx) == result_id:
            self._page_dirty.discard(idx)
            return

        cfg = self._worker.cfg if self._worker else {}
        render_map = {
            1:  lambda: self._draw_mc_chart(self._result, self._mc, cfg),
            5:  lambda: self._draw_channel_heatmap(self._result),
            7:  lambda: self._draw_cost_effect(self._result, self._mc),
            8:  lambda: self._draw_ammo_curve(self._mc),
            9:  lambda: self._draw_ci_chart(self._mc),
            10: lambda: self._draw_timeline(self._result),
            11: lambda: self._lazy_start_sensitivity(),
            12: lambda: self._lazy_start_min_stock(),
            13: lambda: self._draw_bearing_vulnerability(self._result),
            14: lambda: self._draw_req_radar(self._result, self._mc),
            15: lambda: self._draw_threat_type(self._result, self._mc),
            16: lambda: self._draw_vuln_time(self._result),
            17: lambda: self._draw_history_compare(self._result, self._mc),
            18: lambda: self._draw_stress_test(self._mc),
            19: lambda: self._draw_sobol_chart(self._mc),
            20: lambda: self._draw_subsystem_damage(self._result),
            21: lambda: self._lazy_start_optimize(),
            23: lambda: self._lazy_start_cec_compare(),
            24: lambda: self._draw_strike_result(self._result, self._mc),
        }
        if idx in render_map:
            render_map[idx]()
            self._page_dirty.discard(idx)
            self._page_render_cache[idx] = result_id

    def _build_req_tab(self) -> QWidget:
        """포팅 D: REQ 판정 결과 테이블 + 자동 취약점 진단 카드."""
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # ── REQ 판정 테이블 (상단) ────────────────────────────────────────
        req_lbl = QLabel("  ✅  REQ 요구조건 판정")
        req_lbl.setStyleSheet(f"color:{C_TEXT}; font-size:13px; font-weight:bold; padding:4px 0;")
        layout.addWidget(req_lbl)

        self.req_table = QTableWidget(0, 4)
        self.req_table.setHorizontalHeaderLabels(["ID", "요구조건", "판정", "상세"])
        hh = self.req_table.horizontalHeader()
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.req_table.setColumnWidth(0, 70)
        self.req_table.setColumnWidth(1, 150)
        self.req_table.setColumnWidth(2, 60)
        self.req_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.req_table.setAlternatingRowColors(True)
        self.req_table.setStyleSheet(
            f"alternate-background-color: {C_PANEL}; background-color: {C_BG};")
        layout.addWidget(self.req_table, stretch=2)

        # ── 자동 취약점 진단 카드 영역 (하단 — 넓게) ─────────────────────
        diag_header = QLabel("  🩺  자동 취약점 진단")
        diag_header.setStyleSheet(f"color:{C_TEXT}; font-size:13px; font-weight:bold; padding:4px 0;")
        layout.addWidget(diag_header)

        self._diag_scroll = QScrollArea()
        self._diag_scroll.setWidgetResizable(True)
        self._diag_scroll.setMinimumHeight(260)
        self._diag_scroll.setStyleSheet(
            f"QScrollArea {{ background: {C_BG}; border: 1px solid #30363d; border-radius: 6px; }}"
        )
        self._diag_inner = QWidget()
        self._diag_inner.setStyleSheet(f"background: {C_BG};")
        self._diag_layout = QVBoxLayout(self._diag_inner)
        self._diag_layout.setContentsMargins(8, 8, 8, 8)
        self._diag_layout.setSpacing(7)
        _ph = QLabel("  시뮬레이션 실행 후 진단 결과가 표시됩니다.")
        _ph.setStyleSheet(f"color:{C_SUBTEXT}; font-size:12px;")
        self._diag_layout.addWidget(_ph)
        self._diag_layout.addStretch()
        self._diag_scroll.setWidget(self._diag_inner)
        layout.addWidget(self._diag_scroll, stretch=3)

        # ── 교전 후 브리핑 (접이식) ───────────────────────────────────────────
        self._brief_toggle = QPushButton("▶  📋 교전 후 브리핑 — 클릭하여 펼치기")
        self._brief_toggle.setCheckable(True)
        self._brief_toggle.setChecked(False)
        self._brief_toggle.setFixedHeight(28)
        self._brief_toggle.setStyleSheet(
            f"QPushButton {{ background:{C_PANEL}; color:{C_TEXT}; "
            f"border:1px solid #30363d; border-radius:4px; "
            f"font-size:12px; font-weight:bold; text-align:left; padding:0 8px; }}"
            f"QPushButton:checked {{ border-color:#3a5a7a; }}"
        )
        layout.addWidget(self._brief_toggle)

        self._brief_panel = QWidget()
        self._brief_panel.setVisible(False)
        brief_pl = QVBoxLayout(self._brief_panel)
        brief_pl.setContentsMargins(0, 4, 0, 0)
        brief_pl.setSpacing(4)

        self._briefing_browser = QTextBrowser()
        self._briefing_browser.setFont(QFont('Consolas', 9))
        self._briefing_browser.setMinimumHeight(260)
        self._briefing_browser.setStyleSheet(
            f"QTextBrowser {{ background:{C_BG}; color:{C_TEXT}; "
            f"border:1px solid #30363d; border-radius:6px; padding:8px; }}"
        )
        brief_pl.addWidget(self._briefing_browser)

        brief_btn_row = QWidget()
        brief_btn_layout = QHBoxLayout(brief_btn_row)
        brief_btn_layout.setContentsMargins(0, 0, 0, 0)
        brief_btn_layout.setSpacing(6)
        brief_btn_layout.addStretch()
        btn_copy = QPushButton("📋 복사")
        btn_save_brief = QPushButton("💾 TXT 저장")
        for b in [btn_copy, btn_save_brief]:
            b.setFixedHeight(26)
            b.setStyleSheet(
                f"background:{C_PANEL}; color:{C_TEXT}; "
                f"border:1px solid #3a5a7a; font-size:13px; padding:0 8px;")
        btn_copy.clicked.connect(
            lambda: QApplication.clipboard().setText(self._briefing_browser.toPlainText()))
        btn_save_brief.clicked.connect(self._save_briefing_txt)
        brief_btn_layout.addWidget(btn_copy)
        brief_btn_layout.addWidget(btn_save_brief)
        brief_pl.addWidget(brief_btn_row)

        layout.addWidget(self._brief_panel)

        def _toggle_brief(checked):
            self._brief_panel.setVisible(checked)
            arrow = '▼' if checked else '▶'
            suffix = '' if checked else ' — 클릭하여 펼치기'
            self._brief_toggle.setText(f"{arrow}  📋 교전 후 브리핑{suffix}")

        self._brief_toggle.clicked.connect(_toggle_brief)
        return w

    def _build_weather_tab(self) -> QWidget:
        """포팅 D: 날씨별 3종 비교 탭."""
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)

        btn_row = QWidget()
        btn_layout = QHBoxLayout(btn_row)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        self.btn_weather_run = QPushButton("🌤️  날씨별 비교 실행 (각 1000회 MC)")
        self.btn_weather_run.setFixedHeight(36)
        self.btn_weather_run.clicked.connect(self._run_weather_compare)
        btn_layout.addWidget(self.btn_weather_run)
        btn_layout.addStretch()
        layout.addWidget(btn_row)

        self.weather_table = QTableWidget(0, 6)
        self.weather_table.setHorizontalHeaderLabels(
            ["날씨 시나리오", "평균 요격률", "완전 성공률", "평균 비용 ($)",
             "최다 소모 무기", "가장 많이 피격된 함정"])
        hh = self.weather_table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        for col in [1, 2, 3]:
            self.weather_table.setColumnWidth(col, 110)
        self.weather_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.weather_table.setAlternatingRowColors(True)
        self.weather_table.setStyleSheet(
            f"alternate-background-color: {C_PANEL}; background-color: {C_BG};")
        layout.addWidget(self.weather_table)
        return w

    def _build_ab_compare_tab(self) -> QWidget:
        """A/B 편대 구성 비교 탭 — 두 편대를 동일 위협 조건으로 MC 비교."""
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        hdr = QLabel("  ⚖  A/B 편대 구성 비교")
        hdr.setStyleSheet(f"color:{C_TEXT}; font-size:13px; font-weight:bold; padding:4px 0;")
        layout.addWidget(hdr)

        note = QLabel(
            "  현재 시뮬레이션 설정을 A 편대 기준으로 사용합니다. "
            "B 편대는 아래에서 다른 편대 프리셋을 선택하세요. "
            "위협·날씨 조건은 A와 동일하게 적용됩니다."
        )
        note.setStyleSheet(f"color:{C_SUBTEXT}; font-size:11px;")
        note.setWordWrap(True)
        layout.addWidget(note)

        # ── B 편대 선택 행 ─────────────────────────────────────────────────
        sel_row = QWidget()
        sel_layout = QHBoxLayout(sel_row)
        sel_layout.setContentsMargins(0, 0, 0, 0)
        sel_layout.setSpacing(8)

        lbl_b = QLabel("B 편대 프리셋:")
        lbl_b.setStyleSheet(f"color:{C_TEXT}; font-size:12px;")
        sel_layout.addWidget(lbl_b)

        self._cb_ab_fleet_b = QComboBox()
        self._cb_ab_fleet_b.setMinimumWidth(220)
        self._cb_ab_fleet_b.setStyleSheet(
            f"background:{C_PANEL}; color:{C_TEXT}; border:1px solid #30363d; padding:3px;")
        sel_layout.addWidget(self._cb_ab_fleet_b)

        lbl_n = QLabel("MC 횟수:")
        lbl_n.setStyleSheet(f"color:{C_TEXT}; font-size:12px;")
        sel_layout.addWidget(lbl_n)

        self._sb_ab_n = QSpinBox()
        self._sb_ab_n.setRange(100, 2000)
        self._sb_ab_n.setSingleStep(100)
        self._sb_ab_n.setValue(500)
        self._sb_ab_n.setStyleSheet(
            f"background:{C_PANEL}; color:{C_TEXT}; border:1px solid #30363d; padding:3px;")
        sel_layout.addWidget(self._sb_ab_n)

        self.btn_ab_run = QPushButton("⚖  A/B 비교 실행")
        self.btn_ab_run.setFixedHeight(36)
        self.btn_ab_run.clicked.connect(self._run_ab_compare)
        sel_layout.addWidget(self.btn_ab_run)
        sel_layout.addStretch()
        layout.addWidget(sel_row)

        # ── 요약 비교 테이블 ────────────────────────────────────────────────
        lbl_tbl = QLabel("  비교 결과")
        lbl_tbl.setStyleSheet(f"color:{C_SUBTEXT}; font-size:11px; padding:2px 0;")
        layout.addWidget(lbl_tbl)

        self._ab_summary_table = QTableWidget(2, 6)
        self._ab_summary_table.setVerticalHeaderLabels(["A 편대", "B 편대"])
        self._ab_summary_table.setHorizontalHeaderLabels([
            "편대 프리셋", "평균 요격률", "완전 성공률",
            "평균 비용 ($)", "최다 소모 무기", "가장 많이 피격된 함정"
        ])
        hh = self._ab_summary_table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(4, QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        for col in [1, 2, 3]:
            self._ab_summary_table.setColumnWidth(col, 110)
        self._ab_summary_table.setFixedHeight(90)
        self._ab_summary_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._ab_summary_table.setAlternatingRowColors(True)
        self._ab_summary_table.setStyleSheet(
            f"alternate-background-color: {C_PANEL}; background-color: {C_BG};")
        layout.addWidget(self._ab_summary_table)

        # ── Δ 차이 레이블 ──────────────────────────────────────────────────
        self._lbl_ab_delta = QLabel("")
        self._lbl_ab_delta.setStyleSheet(
            f"color:{C_TEXT}; font-size:13px; font-weight:bold; padding:6px 4px;")
        layout.addWidget(self._lbl_ab_delta)

        # ── 세부 무기 잔여 비교 테이블 ─────────────────────────────────────
        lbl_wpn = QLabel("  무기별 평균 잔여 재고")
        lbl_wpn.setStyleSheet(f"color:{C_SUBTEXT}; font-size:11px; padding:2px 0;")
        layout.addWidget(lbl_wpn)

        self._ab_weapon_table = QTableWidget(0, 3)
        self._ab_weapon_table.setHorizontalHeaderLabels(["무기", "A 잔여 (발)", "B 잔여 (발)"])
        hh2 = self._ab_weapon_table.horizontalHeader()
        hh2.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._ab_weapon_table.setColumnWidth(1, 120)
        self._ab_weapon_table.setColumnWidth(2, 120)
        self._ab_weapon_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._ab_weapon_table.setAlternatingRowColors(True)
        self._ab_weapon_table.setStyleSheet(
            f"alternate-background-color: {C_PANEL}; background-color: {C_BG};")
        layout.addWidget(self._ab_weapon_table, stretch=1)

        return w

    def _build_heatmap_tab(self) -> QWidget:
        """v9.5 생존성 히트맵 — 편대(행) × 위협(열) 2D MC 격자."""
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        hdr = QLabel("  🗺  생존성 히트맵 — 편대 × 위협 조합별 요격률")
        hdr.setStyleSheet(f"color:{C_TEXT}; font-size:13px; font-weight:bold; padding:4px 0;")
        layout.addWidget(hdr)

        note = QLabel(
            "  아군 편대(행)와 적군 위협(열)의 모든 조합에 대해 MC를 돌려 "
            "요격률을 색상 격자로 시각화합니다. 시뮬레이션 실행 없이 독립 실행 가능합니다."
        )
        note.setStyleSheet(f"color:{C_SUBTEXT}; font-size:11px;")
        note.setWordWrap(True)
        layout.addWidget(note)

        # ── 설정 행 ────────────────────────────────────────────────────────
        ctrl_row = QWidget()
        ctrl_layout = QHBoxLayout(ctrl_row)
        ctrl_layout.setContentsMargins(0, 0, 0, 0)
        ctrl_layout.setSpacing(10)

        lbl_n = QLabel("셀당 MC:")
        lbl_n.setStyleSheet(f"color:{C_TEXT}; font-size:12px;")
        ctrl_layout.addWidget(lbl_n)

        self._hm_sb_n = QSpinBox()
        self._hm_sb_n.setRange(50, 1000)
        self._hm_sb_n.setSingleStep(50)
        self._hm_sb_n.setValue(200)
        self._hm_sb_n.setStyleSheet(
            f"background:{C_PANEL}; color:{C_TEXT}; border:1px solid #30363d; padding:3px;")
        ctrl_layout.addWidget(self._hm_sb_n)

        self.btn_hm_run = QPushButton("🗺  히트맵 실행")
        self.btn_hm_run.setFixedHeight(34)
        self.btn_hm_run.clicked.connect(self._run_heatmap)
        ctrl_layout.addWidget(self.btn_hm_run)

        self.btn_hm_save = QPushButton("💾 PNG 저장")
        self.btn_hm_save.setFixedHeight(34)
        self.btn_hm_save.setEnabled(False)
        self.btn_hm_save.clicked.connect(self._save_heatmap_png)
        ctrl_layout.addWidget(self.btn_hm_save)

        self._hm_progress_lbl = QLabel("")
        self._hm_progress_lbl.setStyleSheet(f"color:{C_SUBTEXT}; font-size:11px;")
        ctrl_layout.addWidget(self._hm_progress_lbl)
        ctrl_layout.addStretch()
        layout.addWidget(ctrl_row)

        # ── 편대 / 위협 선택 체크박스 패널 ────────────────────────────────
        sel_splitter = QSplitter(Qt.Orientation.Horizontal)
        sel_splitter.setFixedHeight(160)

        # 아군 편대 (행)
        fleet_box = QGroupBox("아군 편대 (행)")
        fleet_box.setStyleSheet(
            f"QGroupBox {{ color:{C_TEXT}; border:1px solid #30363d;"
            f" border-radius:4px; margin-top:6px; padding:4px; }}"
            f"QGroupBox::title {{ subcontrol-origin:margin; left:8px; color:{C_SUBTEXT}; }}")
        fleet_inner = QVBoxLayout(fleet_box)
        fleet_inner.setSpacing(2)
        fleet_scroll = QScrollArea()
        fleet_scroll.setWidgetResizable(True)
        fleet_scroll.setStyleSheet(
            f"QScrollArea {{ border:none; background:{C_BG}; }}")
        fleet_content = QWidget()
        fleet_content_layout = QVBoxLayout(fleet_content)
        fleet_content_layout.setSpacing(1)
        fleet_content_layout.setContentsMargins(2, 2, 2, 2)

        self._hm_fleet_checks: list[QCheckBox] = []
        default_fleets = ['단독 작전', '기동전단 기본', 'BMD 중점', '대잠 중점',
                          '이지스 기동전단', '이지스 기동전단 (강화)', '최대 편대']
        for name in (list(V7_FLEET_PRESETS.keys()) if _V7_OK else default_fleets):
            chk = QCheckBox(name)
            chk.setStyleSheet(f"color:{C_TEXT}; font-size:11px;")
            chk.setChecked(name in default_fleets[:4])
            fleet_content_layout.addWidget(chk)
            self._hm_fleet_checks.append(chk)

        fleet_scroll.setWidget(fleet_content)
        fleet_inner.addWidget(fleet_scroll)
        sel_splitter.addWidget(fleet_box)

        # 적군 위협 (열)
        enemy_box = QGroupBox("적군 위협 (열)")
        enemy_box.setStyleSheet(
            f"QGroupBox {{ color:{C_TEXT}; border:1px solid #30363d;"
            f" border-radius:4px; margin-top:6px; padding:4px; }}"
            f"QGroupBox::title {{ subcontrol-origin:margin; left:8px; color:{C_SUBTEXT}; }}")
        enemy_inner = QVBoxLayout(enemy_box)
        enemy_inner.setSpacing(2)
        enemy_scroll = QScrollArea()
        enemy_scroll.setWidgetResizable(True)
        enemy_scroll.setStyleSheet(
            f"QScrollArea {{ border:none; background:{C_BG}; }}")
        enemy_content = QWidget()
        enemy_content_layout = QVBoxLayout(enemy_content)
        enemy_content_layout.setSpacing(1)
        enemy_content_layout.setContentsMargins(2, 2, 2, 2)

        self._hm_enemy_checks: list[QCheckBox] = []
        default_enemies = ['A2/AD 항공 포화', '항모 킬 체인', '수상함 편대전',
                           '대잠 복합', 'BMD 탄도 포화', '전면전 포화']
        for name in (list(V7_ENEMY_FLEET_PRESETS.keys()) if _V7_OK else default_enemies):
            chk = QCheckBox(name)
            chk.setStyleSheet(f"color:{C_TEXT}; font-size:11px;")
            chk.setChecked(name in default_enemies)
            enemy_content_layout.addWidget(chk)
            self._hm_enemy_checks.append(chk)

        enemy_scroll.setWidget(enemy_content)
        enemy_inner.addWidget(enemy_scroll)
        sel_splitter.addWidget(enemy_box)

        sel_splitter.setSizes([400, 600])
        layout.addWidget(sel_splitter)

        # ── 히트맵 캔버스 ──────────────────────────────────────────────────
        self._hm_canvas = MplCanvas(figsize=(10, 5), facecolor=C_BG)
        layout.addWidget(self._hm_canvas, stretch=1)

        # 히트맵 데이터 보관
        self._hm_grid: list | None = None
        self._hm_fleet_labels: list[str] = []
        self._hm_enemy_labels: list[str] = []

        return w

    def _build_log_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        self.log_table = QTableWidget(0, 2)
        self.log_table.setHorizontalHeaderLabels(["시각 (s)", "이벤트"])
        self.log_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch)
        self.log_table.setColumnWidth(0, 90)
        self.log_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers)
        self.log_table.setAlternatingRowColors(True)
        self.log_table.setStyleSheet(
            f"alternate-background-color: {C_PANEL};"
            f"background-color: {C_BG};")
        layout.addWidget(self.log_table)
        return w

    def _build_subsystem_tab(self) -> QWidget:
        """서브시스템 피해 현황 탭 — 함정별 레이더/추진/무장 손상 상태 테이블."""
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        hdr = QLabel("  🛡  함정별 서브시스템 피해 현황 (단일 시뮬레이션 기준)")
        hdr.setStyleSheet(f"color:{C_TEXT}; font-size:13px; font-weight:bold; padding:4px 0;")
        layout.addWidget(hdr)

        self._subsystem_table = QTableWidget(0, 7)
        self._subsystem_table.setHorizontalHeaderLabels([
            "함정", "HP", "피격", "레이더", "추진", "채널", "비활성 무기"
        ])
        hh = self._subsystem_table.horizontalHeader()
        hh.setSectionResizeMode(6, QHeaderView.ResizeMode.Stretch)
        self._subsystem_table.setColumnWidth(0, 160)
        self._subsystem_table.setColumnWidth(1, 60)
        self._subsystem_table.setColumnWidth(2, 50)
        self._subsystem_table.setColumnWidth(3, 90)
        self._subsystem_table.setColumnWidth(4, 90)
        self._subsystem_table.setColumnWidth(5, 90)
        self._subsystem_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._subsystem_table.setAlternatingRowColors(True)
        self._subsystem_table.setStyleSheet(
            f"alternate-background-color: {C_PANEL}; background-color: {C_BG};")
        layout.addWidget(self._subsystem_table, stretch=1)

        note = QLabel("  레이더·추진·채널: 1.00=정상 / 낮을수록 손상. 빨간색=임계 손상(≤0.50)")
        note.setStyleSheet(f"color:{C_SUBTEXT}; font-size:11px; padding:2px 0;")
        layout.addWidget(note)
        return w

    def _draw_subsystem_damage(self, result: dict):
        if result is None:
            return
        data = result.get('ship_subsystem_damage', {})
        self._subsystem_table.setRowCount(0)
        for ship_name, info in data.items():
            row = self._subsystem_table.rowCount()
            self._subsystem_table.insertRow(row)
            hp_str = f"{info['hp']} / {info['max_hp']}" if info['alive'] else f"격침 (HP {info['hp']})"
            hits_str = str(info.get('hits_taken', 0))
            dis_wpns = ', '.join(info['disabled_weapons']) if info['disabled_weapons'] else '—'

            items = [
                QTableWidgetItem(ship_name),
                QTableWidgetItem(hp_str),
                QTableWidgetItem(hits_str),
                QTableWidgetItem(f"{info['radar_factor']:.2f}"),
                QTableWidgetItem(f"{info['speed_factor']:.2f}"),
                QTableWidgetItem(f"{info['channel_factor']:.2f}"),
                QTableWidgetItem(dis_wpns),
            ]
            for col, item in enumerate(items):
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                # 임계 손상(≤0.50) 또는 격침 → 빨간색 강조
                if col in (3, 4, 5):
                    try:
                        val = float(item.text())
                        if val <= 0.50:
                            item.setForeground(QColor('#ff4444'))
                        elif val <= 0.80:
                            item.setForeground(QColor('#ffaa00'))
                    except ValueError:
                        pass
                if not info['alive']:
                    item.setForeground(QColor('#ff4444'))
                self._subsystem_table.setItem(row, col, item)

    # ── v9.3: 공격 결과 탭 ───────────────────────────────────────────────────

    def _build_strike_tab(self) -> QWidget:
        """공격 결과 탭 — 격침 테이블 (상단) + MC 격침 분포 차트 (하단)."""
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        hdr = QLabel("  ⚔  아군 공격 결과 (단일 시뮬레이션 기준)")
        hdr.setStyleSheet(f"color:{C_TEXT}; font-size:13px; font-weight:bold; padding:4px 0;")
        layout.addWidget(hdr)

        # 격침 테이블
        self._strike_table = QTableWidget(0, 4)
        self._strike_table.setHorizontalHeaderLabels(["표적 함정", "사용 무기", "격침 시각(s)", "결과"])
        hh = self._strike_table.horizontalHeader()
        hh.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._strike_table.setColumnWidth(1, 140)
        self._strike_table.setColumnWidth(2, 90)
        self._strike_table.setColumnWidth(3, 70)
        self._strike_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._strike_table.setAlternatingRowColors(True)
        self._strike_table.setStyleSheet(
            f"alternate-background-color: {C_PANEL}; background-color: {C_BG};")
        layout.addWidget(self._strike_table, stretch=1)

        # MC 격침 통계 레이블 + 차트
        self._strike_mc_lbl = QLabel("  MC 격침 통계: 시뮬레이션 실행 후 표시됩니다.")
        self._strike_mc_lbl.setStyleSheet(f"color:{C_SUBTEXT}; font-size:12px; padding:2px 0;")
        layout.addWidget(self._strike_mc_lbl)

        self.tab_strike_chart = ChartPageWidget()
        layout.addWidget(self.tab_strike_chart, stretch=1)
        return w

    def _draw_strike_result(self, result: dict, mc: dict):
        """공격 결과 탭 갱신."""
        # 격침 테이블
        logs = result.get('strike_log', [])
        self._strike_table.setRowCount(0)
        if not logs:
            self._strike_table.insertRow(0)
            msg = QTableWidgetItem("공격 임무 비활성화 또는 교전 없음")
            msg.setForeground(QColor(C_SUBTEXT))
            self._strike_table.setItem(0, 0, msg)
        else:
            for entry in logs:
                row = self._strike_table.rowCount()
                self._strike_table.insertRow(row)
                sunk = entry.get('sunk', False)
                result_str = '격침' if sunk else f"손상 (HP {entry.get('hp_remaining', '?')})"
                items = [
                    QTableWidgetItem(entry.get('target', '?')),
                    QTableWidgetItem(entry.get('weapon', '?')),
                    QTableWidgetItem(str(entry.get('t', '?'))),
                    QTableWidgetItem(result_str),
                ]
                for col, item in enumerate(items):
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    if sunk:
                        item.setForeground(QColor('#2ecc71'))
                    self._strike_table.setItem(row, col, item)

        # MC 통계 레이블
        mean_dest = mc.get('mean_enemy_destroyed', 0.0)
        max_dest  = mc.get('max_enemy_destroyed', 0)
        n         = mc.get('n', 0)
        # v9.4: 현무-4 발사 수 (단일 시뮬)
        ground_rem = result.get('ground_remaining', {})
        h4_init    = getattr(self, 'spn_hyunmoo4', None)
        h4_stock   = h4_init.value() if h4_init else 0
        h4_fired   = h4_stock - ground_rem.get('현무-4 (ASBM)', h4_stock)
        h4_str     = f"  |  현무-4 발사: {h4_fired}발" if h4_stock > 0 else ""
        ashore_fired = result.get('ashore_sm3_fired', 0)
        thaad_fired  = result.get('thaad_fired', 0)
        bmd_str = ""
        if ashore_fired > 0: bmd_str += f"  |  어쇼어 SM-3: {ashore_fired}발"
        if thaad_fired  > 0: bmd_str += f"  |  THAAD: {thaad_fired}발"
        # v10.6: 항모 격침/전투불능 상태
        carrier_str = ""
        for cname, cinfo in result.get('carrier_status', {}).items():
            st  = cinfo['status']
            hp  = cinfo['hp']
            mhp = cinfo['max_hp']
            color_tag = '🔴' if st == '격침' else ('🟡' if st == '전투불능' else '🟢')
            carrier_str += f"  |  {color_tag} {cname}: {st} (HP {hp}/{mhp})"
        self._strike_mc_lbl.setText(
            f"  MC {n}회 평균 적 격침: {mean_dest:.2f}척  |  최대: {max_dest}척  |"
            f"  단일 시뮬 격침: {result.get('enemy_ships_destroyed', 0)}척{h4_str}{bmd_str}{carrier_str}"
        )

        # MC 격침 분포 차트
        self.tab_strike_chart.start_render(_render_strike_chart, mc)

    # ── 툴팁 / 편성 표시 ────────────────────────────────────────────────────

    _SHIP_DISPLAY = {
        'KDX-III-B2': '이지스 구축함 KDX-III Batch II (정조대왕급)',
        'KDX-III-B1': '이지스 구축함 KDX-III Batch I (세종대왕급)',
        'KDX-II':     '구축함 (KDX-II 충무공이순신급)',
        'FFX-I':      '호위함 FFX Batch I (인천급)',
        'FFX-II':     '호위함 FFX Batch II (대구급)',
        'FFX-III':    '호위함 FFX Batch III (충남급)',
    }

    # 아군 편대 프리셋 전술 설명 (툴팁용)
    _FRIENDLY_PRESET_TIPS = {
        '단독 작전':              '정조대왕함 1척 단독 방어. 기준 성능 평가 및 단독 교전 테스트.',
        '기동전단 기본':          '이지스 1 + 구축함 1 + 호위함 1. 균형 편성, 기본 방어력 평가.',
        'BMD 중점':               'SM-3 탑재 이지스 2척 체제. 탄도미사일·HGV 방어 특화, BMD 채널 극대화.',
        '대잠 중점':              '이지스 1 + 호위함 2. 잠수함 위협 특화 편성. 홍상어·청상어 재고 집중.',
        '대잠전단':               '이지스 1 + 호위함 2 + KSS-II × 2. 아군 잠수함 포함 입체 대잠전.',
        '최대 편대':              '이지스 2 + 구축함 2 + 호위함 2, 총 6척. 종합 방어력 최대 평가.',
        '이지스 기동전단':        '실제 교리 기반. 정조대왕함 중심 + KDX-II 2 + FFX-I/II 2 + 보급함.',
        '이지스 기동전단 (강화)': '전시 확장 편성. 이지스 2척 + KDX-II 2 + FFX 2 + 보급함.',
        '전 이지스 기동전단':     '이지스 4척 완전 편성 (B2×1 + B1×3). SM-3 채널 극대화, 최강 방공.',
        '독도함 상륙전단':        '독도함(LPH) 중심 상륙작전 편성. 헬기 대잠 특화, 연안 화력 지원.',
        '동해 해역방어 (1함대)':  '1함대 교리. KDX-II + FFX-I 2 + PKG 4 + PCC 2. 동해 연안 방어.',
        '서해 해역방어 (2함대)':  '2함대 교리. FFX-I 2 + PKG 4 + PCC 2. 서해 연안 방어.',
        '한미 기동전단 기본':     '한미 연합. KDX-III-B2 + DDG-51 × 2 + KDX-II + FFX-II + FFX-I.',
        '한미 기동전단 강화':     '한미 연합 강화. 이지스 2(한) + DDG-51 2 + CG-47 + KDX-II 2 + AOE.',
        '한미 항모전단 지원':     '한미 항모전단. CVN + DDG-51 × 3 + CG-47 + 한국 이지스 + KDX-II 2.',
    }

    # 적군 편대 프리셋 전술 설명 (툴팁용)
    _ENEMY_PRESET_TIPS = {
        'A2/AD 항공 포화':    'J-16 × 4 + H-6 × 2. 장거리 공대함미사일 포화 — SM-2·RAM 재고 소모 유도.',
        '항모 킬 체인':       'DF-21D + DF-17(HGV) + J-20(스텔스). BMD + 스텔스 복합 — SM-3 필수.',
        '수상함 편대전':      '055형 × 1 + 052D × 2 + 022형 × 4. 대함미사일 집중 — 채널 포화 테스트.',
        '대잠 복합':          '093형 + 039형 잠수함. 어뢰 + 잠수함 발사 순항미사일 동시 위협.',
        'BMD 탄도 포화':      'KN-23·DF-15·DF-21D·DF-17 혼합. SM-3 BMD 성능 집중 검증. 최고 난이도 탄도.',
        '전면전 포화':        '전 카테고리 혼합 최고 난이도. J-20·DF-17·055형·DF-21D·093형.',
        '북한 탄도 포화':     'KN-23 × 3 + 화성-15 + 화살-2. 북한 교리 기반 탄도 + 순항 병행 공격.',
        '러시아 극초음속':    '킨잘·지르콘·Kh-101. 극초음속 2종 + 스텔스 순항 — SM-3/6 연속 소진.',
        '잠수함 복합 포화':   '039형 × 3 + 093형. 다중 잠수함 동시 위협 — 대잠 전력 한계 테스트.',
    }

    def _friendly_preset_tooltip(self, name: str) -> str:
        desc  = self._FRIENDLY_PRESET_TIPS.get(name, '')
        ships = V7_FLEET_PRESETS.get(name, [])
        lines = ([desc, ''] if desc else []) + ['편성:']
        for s in ships:
            disp = self._SHIP_DISPLAY.get(s['type'], s['type'])
            lines.append(f"  • {s['name']}  ({disp})")
        return '\n'.join(lines)

    def _enemy_preset_tooltip(self, name: str) -> str:
        desc    = self._ENEMY_PRESET_TIPS.get(name, '')
        threats = V7_ENEMY_FLEET_PRESETS.get(name, [])
        lines   = ([desc, ''] if desc else []) + ['위협 구성:']
        for t in threats:
            lines.append(f"  • {t['preset']}  ×{t['count']}")
        return '\n'.join(lines)

    def _update_fleet_detail(self, preset_name: str):
        if not _V7_OK or preset_name not in V7_FLEET_PRESETS:
            self.lbl_fleet_detail.setText('')
            return
        lines = []
        for s in V7_FLEET_PRESETS[preset_name]:
            disp = self._SHIP_DISPLAY.get(s['type'], s['type'])
            lines.append(f"• {s['name']}  ({disp})")
        self.lbl_fleet_detail.setText('\n'.join(lines))
        self.cmb_fleet.setToolTip(self._friendly_preset_tooltip(preset_name))

    def _update_detect_info(self, _=None):
        if not _V7_OK:
            return
        r = calculate_fleet_detect_ranges(
            self.cmb_fleet.currentText(),
            self.cmb_weather.currentText())
        rf_pct = int(r['radar_factor'] * 100)
        sf_pct = int(r['sonar_factor'] * 100)
        self.lbl_detect_info.setText(
            f"📡 대공 {r['대공']}km  대함 {r['대함']}km  (레이더 ×{rf_pct}%)\n"
            f"🔊 대잠 {r['대잠']}km  (소나 ×{sf_pct}%)\n"
            f"기준함: {r['leading_ship']} · 데이터링크 적용"
        )

    def _update_enemy_row_tooltip(self, cmb: QComboBox, name: str):
        if not _V7_OK or name not in V7_ENEMY_DB:
            return
        cmb.setToolTip(self._enemy_tip(name))

    def _update_enemy_preset_detail(self, preset_name: str):
        if not _V7_OK or preset_name not in V7_ENEMY_FLEET_PRESETS:
            self.lbl_enemy_preset_detail.setText('')
            return
        units = V7_ENEMY_FLEET_PRESETS[preset_name]
        label_lines = []
        for e in units:
            label_lines.append(f"• {e['preset']}  ×{e['count']}")
        self.lbl_enemy_preset_detail.setText('\n'.join(label_lines))
        self.cmb_fleet_preset_e.setToolTip(self._enemy_preset_tooltip(preset_name))

    def _update_difficulty_tooltip(self, diff: str):
        if not _V7_OK or diff not in V7_RANDOM_CFG:
            return
        cfg = V7_RANDOM_CFG[diff]
        lo, hi = cfg['total_count']
        pool = ', '.join(cfg['pool'][:4]) + ('...' if len(cfg['pool']) > 4 else '')
        self.cmb_difficulty.setToolTip(
            f"[{diff}] 총 {lo}~{hi}대 | 최대 {cfg['max_types']}종\n풀: {pool}")

    @staticmethod
    def _enemy_tip(name: str) -> str:
        if not _V7_OK or name not in V7_ENEMY_DB:
            return ''
        e = V7_ENEMY_DB[name]
        mach = e['speed_ms'] / 340
        lines = [
            f"【{name}】",
            f"분류: {e.get('category','?')} | 종류: {e.get('type','?')}",
            f"속도: 마하 {mach:.1f}  |  RCS: {e['rcs_m2']}㎡",
        ]
        if e.get('missile_name'):
            lines.append(f"미사일: {e['missile_name']}")
            lines.append(f"  사거리 {e.get('missile_range_km','?')}km"
                         f"  |  속도 {e.get('missile_speed_ms','?')}m/s")
        if e.get('is_hgv'):
            lines.append("⚠ 극초음속 활공체 — SM-3만 요격 가능")
        if e.get('is_qbm'):
            lines.append("⚠ 저고도기동탄도 — SM-3 거의 무력화")
        sd = e.get('self_defense_pk', 0)
        if sd > 0:
            lines.append(f"자체방어 Pk: {sd:.0%}")
        return '\n'.join(lines)

    def _on_enemy_mode_changed(self, _idx=None):
        """적군 편대 모드 전환 시 관련 위젯 show/hide."""
        mode = self.cmb_enemy_mode.currentText()
        is_preset = mode == '프리셋'
        is_mixed  = mode == '혼합 시나리오'
        self.cmb_fleet_preset_e.setVisible(is_preset)
        self.lbl_enemy_preset_detail.setVisible(is_preset)
        self._mixed_row.setVisible(is_mixed)
        self._rand_row.setVisible(mode == '랜덤')
        if is_preset and self.cmb_fleet_preset_e.count():
            self._update_enemy_preset_detail(self.cmb_fleet_preset_e.currentText())
        if is_mixed and self.cmb_mixed_scenario.count():
            self._update_mixed_scenario_detail(self.cmb_mixed_scenario.currentText())

    def _update_mixed_scenario_detail(self, scenario_name: str):
        """NEW-A: 혼합 시나리오 설명 업데이트."""
        if not _V7_OK or scenario_name not in V7_MIXED_SCENARIOS:
            self.lbl_mixed_detail.setText('')
            return
        sc = V7_MIXED_SCENARIOS[scenario_name]
        desc = sc.get('description', '')
        wave_lines = []
        for w in sc.get('waves', []):
            d = w['delay_s']
            parts = ', '.join(f"{s['preset']} ×{s['count']}" for s in w['threats'])
            wave_lines.append(f"  +{d:>3}s  {parts}")
        self.lbl_mixed_detail.setText(desc + '\n' + '\n'.join(wave_lines))

    def _apply_style(self):
        self.setStyleSheet(STYLE_MAIN)

    # ── 시뮬 실행 ────────────────────────────────────────────────────────────

    def _run_sim(self):
        # 적군 모드 및 편대 구성 (포팅 A)
        mode_label = self.cmb_enemy_mode.currentText()
        mode_map   = {'프리셋': 'preset', '혼합 시나리오': 'mixed', '랜덤': 'random'}
        enemy_mode = mode_map.get(mode_label, 'preset')

        cfg = {
            # 아군 편대 (탐지거리는 엔진이 함대+날씨로 자동 계산)
            'fleet_preset':      self.cmb_fleet.currentText(),
            'weather':           self.cmb_weather.currentText(),
            # v9.12: 작전 해역·계절·지형 음영
            'fleet_region':      self.cmb_region.currentText(),
            'season':            {'봄': 'spring', '여름': 'summer', '가을': 'autumn', '겨울': 'winter'}.get(
                                     self.cmb_season.currentText()[:1], 'summer'),
            'enable_terrain':    self.chk_terrain.isChecked(),
            'enable_current':    self.chk_current.isChecked(),
            'enable_evap_duct':  self.chk_evap_duct.isChecked(),
            'enable_anti_sam':   self.chk_anti_sam.isChecked(),
            'enable_isa':        self.chk_isa.isChecked(),
            # v9.14: 해협 진입로 (대한해협 선택 시 유효)
            'strait_type': {'서수도 (서→동)': 'korea_west',
                            '동수도 (동→서)': 'korea_east',
                            '양방향 협공':    'bilateral'}.get(
                self.cmb_strait_type.currentText(), 'korea_west'),
            'detect_km_manual':  False,
            # 적군 (포팅 A)
            'enemy_fleet_mode':       enemy_mode,
            'enemy_fleet_preset':     self.cmb_fleet_preset_e.currentText(),
            'mixed_scenario':         self.cmb_mixed_scenario.currentText(),
            'enemy_fleet_difficulty': self.cmb_difficulty.currentText(),
            'enemy_fleet_seed':       self.spn_seed.value() or None,
            # 전술 옵션 — 항상 ON
            'enable_ecm':         True,
            'enable_evasion':     True,
            'enable_decoy':       True,
            'enable_selfdefense': True,
            # 항공 자산 — UI 체크박스 읽기
            'enable_helo':  self.chk_helo.isChecked(),
            'enable_p3c':   self.chk_p3c.isChecked(),
            'enable_p8a':   self.chk_p8a.isChecked(),
            # v10.5: 한국 공군 CAP
            'enable_f35a':  self.chk_f35a.isChecked(),
            'enable_kf21':  self.chk_kf21.isChecked(),
            'enable_fa50':  self.chk_fa50.isChecked(),
            # 방어 전술 — UI 체크박스 읽기
            'enable_layered_defense': True,
            'enable_cec':             self.chk_cec.isChecked(),
            'tactical_mode':          self.chk_tactical.isChecked(),
            'tactical_interval':      30,
            'enable_multibearing':       self.chk_multibearing.isChecked(),
            'enable_cec_jammed':         self.chk_cec_jammed.isChecked(),
            'enable_ship_evasion':       self.chk_ship_evasion.isChecked(),
            'enable_radar_off':          self.chk_radar_off.isChecked(),
            'enable_random_placement':   True,
            'random_spread_km':          10.0,
            'enemy_tactics':          {
                '없음': None, 'V자 대형': 'v_formation',
                '포위 기동': 'encirclement'
            }.get(self.cmb_enemy_tactics.currentText(), None),
            'ai_tactic': {
                '없음': None, '채널 포화': 'saturation',
                '시차 공격': 'stagger', '약점 공략': 'exploit_weakness',
            }.get(self.cmb_ai_tactic.currentText(), None),
            'sim_seed':               self.spn_sim_seed.value() or None,
            # v9.3: 공격 임무
            'enable_strike':   self.chk_strike.isChecked(),
            'haesong2_stock':  self.spn_haesong2.value(),
            'harpoon_stock':   self.spn_harpoon.value(),
            # v9.4: 현무-4 지상 발사 재고
            'hyunmoo4_stock':  self.spn_hyunmoo4.value(),
            # v9.11: 지상 BMD 자산
            'enable_ashore':   self.chk_ashore.isChecked(),
            'ashore_sm3_stock': self.spn_ashore_sm3.value() if self.chk_ashore.isChecked() else 0,
            'enable_thaad':    self.chk_thaad.isChecked(),
            'thaad_stock':     self.spn_thaad.value() if self.chk_thaad.isChecked() else 0,
            # C&D 시간
            'cd_time_s':      10,
            'confirm_time_s': 3,
        }
        mode_idx = self.cmb_sim_mode.currentIndex() if hasattr(self, 'cmb_sim_mode') else 1
        mc_n = [5_000, 10_000, 100_000][mode_idx]
        precision_mode = (mode_idx == 2)
        sobol_npp = self.spn_sobol_npp.value() if hasattr(self, 'spn_sobol_npp') else 3

        self.btn_run.setEnabled(False)
        self._prog.setVisible(True)
        self._t0 = time.time()
        self._lbl_status.setText("실행 중...")

        # BUG-1: 이전 워커가 살아 있으면 종료 후 교체
        if self._worker and self._worker.isRunning():
            self._worker.requestInterruption()
            self._worker.quit()
            if not self._worker.wait(2000):
                self._worker.terminate()
                self._worker.wait(500)

        self._worker = SimWorker(cfg, mc_n, precision_mode=precision_mode,
                                 sobol_npp=sobol_npp, sim_mode_idx=mode_idx)
        self._worker.progress.connect(self._on_progress)
        self._worker.progress_detail.connect(self._on_progress_detail)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.sim_started.connect(self.tab_sysmon.mark_sim_start)
        self._worker.sim_ended.connect(self.tab_sysmon.mark_sim_end)
        self._worker.batch_done.connect(self.tab_sysmon.on_batch_done)
        self._worker.progress_detail.connect(self.tab_sysmon.on_progress_detail)
        # 플로팅 모니터 연결 (v8.26: step_update / phase_update 추가)
        self._worker.sim_started.connect(self._show_float_mon)
        self._worker.sim_ended.connect(self._float_mon.close)
        self._worker.progress_detail.connect(self._float_mon.update_mc)
        self._worker.progress.connect(self._float_mon.update_status)
        self._worker.rate_update.connect(self._float_mon.update_rate)
        self._worker.step_update.connect(self._float_mon.update_step)
        self._worker.phase_update.connect(self._float_mon.update_phases)
        self._float_mon.stop_requested.connect(self._stop_worker)
        # v10.7: 전술 의사결정 모드 — 워커 일시정지 시 다이얼로그 표시
        self._worker.tactical_pause.connect(self._on_tactical_pause)
        self._worker.start(QThread.Priority.LowPriority)  # BUG-1

    def _on_tactical_pause(self, state: dict):
        """v10.7: 전술 의사결정 — 워커 일시정지 시 메인 스레드에서 다이얼로그 표시."""
        dlg = TacticalDialog(state, parent=self)
        dlg.exec()
        choice = dlg.get_choice()
        if self._worker:
            self._worker.resume_tactical(choice)

    def _show_float_mon(self):
        """플로팅 모니터를 메인 창 오른쪽 하단에 배치 후 표시. sysmon 탭 자동 전환."""
        geo = self.geometry()
        mon = self._float_mon
        x = geo.right()  - mon.width()  - 20
        y = geo.bottom() - mon.height() - 60
        mon.move(x, y)
        mon.show()
        self._sidebar.set_current_index(6)  # 시스템 모니터 탭으로 자동 전환

    def _stop_worker(self):
        """플로팅 모니터 중단 버튼 → 워커 인터럽트."""
        if self._worker and self._worker.isRunning():
            self._worker.requestInterruption()
            self._lbl_status.setText("중단 요청 중…")

    def _on_progress(self, msg: str):
        self._lbl_status.setText(msg)

    def _on_progress_detail(self, done: int, total: int, eta: float):
        eta_str = f" | 잔여 {eta:.0f}s" if eta > 0 else ""
        self._lbl_status.setText(f"MC {done}/{total}{eta_str}")

    def _on_finished(self, result: dict, mc: dict):
        elapsed = time.time() - self._t0
        self._result = result
        self._mc     = mc

        self.btn_run.setEnabled(True)
        self._prog.setVisible(False)
        cvar_str = f" | CVaR {mc.get('cvar', 0):.1%}" if mc.get('cvar') is not None else ''
        self._lbl_status.setText(
            f"완료 ({elapsed:.1f}s) | "
            f"요격률 {mc['mean_intercept']:.1%}{cvar_str} | "
            f"MC {mc['n']}회")

        self._update_cards(result, mc)
        self._update_vls_warning(mc)
        self.tab_engagement.load_result(result)
        self._fill_req(result, mc)
        self._fill_log(result.get('log', []))
        cfg  = self._worker.cfg  if self._worker else {}
        self._fill_diagnosis(result, mc, cfg)
        self._fill_briefing(result, mc, cfg)
        mc_n = self._worker.mc_n if self._worker and hasattr(self._worker, 'mc_n') else 100
        # BUG-1: 감도 분석·최소 재고 워커를 즉시 기동하면 GIL 독점으로 UI 프리즈
        # → 해당 탭 방문 시점까지 lazy-start로 연기
        self._pending_cfg  = cfg
        self._pending_mc_n = mc_n

        # 모든 차트 페이지를 dirty로 표시 (11·12는 탭 방문 시 워커 기동)
        self._page_dirty = {1, 5, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 23, 24}

        # 히스토리 저장 (최대 5개)
        self._history.append({
            'mean_intercept': mc['mean_intercept'],
            'full_pass_rate': mc.get('full_pass_rate', 0),
            'mean_cost':      mc.get('mean_cost', result.get('total_cost', 0)),
            'label': f"#{len(self._history)+1}  {cfg.get('weather','?')} / "
                     f"{cfg.get('mixed_scenario') or cfg.get('enemy_fleet_preset') or cfg.get('enemy_fleet_mode','?')}",
        })
        if len(self._history) > 5:
            self._history.pop(0)

        # A/B 탭 B 편대 콤보박스 갱신
        if _V7_OK:
            current_preset = cfg.get('fleet_preset', '')
            all_presets = list(V7_FLEET_PRESETS.keys())
            self._cb_ab_fleet_b.blockSignals(True)
            prev = self._cb_ab_fleet_b.currentText()
            self._cb_ab_fleet_b.clear()
            for p in all_presets:
                if p != current_preset:
                    self._cb_ab_fleet_b.addItem(p)
            if prev and self._cb_ab_fleet_b.findText(prev) >= 0:
                self._cb_ab_fleet_b.setCurrentText(prev)
            self._cb_ab_fleet_b.blockSignals(False)

        # v8.26: 아코디언 사이드바 배지 표시 + MC 통계 탭으로 전환
        self._sidebar.mark_new_data(list(range(26)))
        self._sidebar.set_current_index(1)
        self._on_page_changed(1)       # BUG-1: 이미 인덱스 1이면 item_selected 미발화 → 수동 트리거
        sim_mode_idx = getattr(self._worker, 'sim_mode_idx', 1)
        _write_sim_log(cfg, result, mc)
        _write_sim_db(cfg, result, mc, sim_mode_idx)

    def _fill_req(self, result: dict, mc: dict):
        """포팅 D: REQ 판정 테이블 채우기."""
        if not _V7_OK:
            return
        verdicts, details = evaluate_req_v7(result, mc, self._worker.cfg if self._worker else None)
        self.req_table.setRowCount(0)
        for req, v, d in zip(REQ_ITEMS_V7, verdicts, details):
            row = self.req_table.rowCount()
            self.req_table.insertRow(row)
            for col, text in enumerate([req['id'], req['name'],
                                        'PASS' if v else 'FAIL', d]):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter
                                      if col != 3 else Qt.AlignmentFlag.AlignLeft
                                      | Qt.AlignmentFlag.AlignVCenter)
                if col == 2:
                    item.setForeground(QColor('#2ecc71' if v else '#e74c3c'))
                self.req_table.setItem(row, col, item)

    def _fill_diagnosis(self, result: dict, mc: dict, cfg: dict):
        """자동 취약점 진단 카드를 REQ 탭 상단 패널에 채운다."""
        if not _V7_OK:
            return
        # 기존 카드 초기화
        while self._diag_layout.count():
            item = self._diag_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        cards = diagnose_vulnerabilities_v7(result, mc, cfg)

        _SEV_COLOR = {
            'HIGH': ('#e74c3c', '🔴 위험'),
            'MED':  ('#e67e22', '🟡 경고'),
            'LOW':  ('#3498db', '🔵 주의'),
            'OK':   ('#2ecc71', '🟢 양호'),
        }

        for card in cards:
            sev   = card['severity']
            color, badge = _SEV_COLOR.get(sev, ('#95a5a6', sev))

            frame = QFrame()
            frame.setStyleSheet(
                f"QFrame {{ background: #161b22; border-left: 5px solid {color};"
                f" border-radius: 5px; padding: 6px; }}"
            )
            fl = QVBoxLayout(frame)
            fl.setContentsMargins(10, 6, 10, 6)
            fl.setSpacing(4)

            # 제목줄
            title_lbl = QLabel(f"{badge}  {card['title']}")
            title_lbl.setStyleSheet(f"color:{color}; font-size:13px; font-weight:bold; border:none;")
            fl.addWidget(title_lbl)

            # 상세
            if card.get('detail'):
                det = QLabel(card['detail'])
                det.setStyleSheet(f"color:{C_TEXT}; font-size:12px; border:none;")
                det.setWordWrap(True)
                fl.addWidget(det)

            # 개선 제안
            if card.get('suggestion'):
                sugg = QLabel(card['suggestion'])
                sugg.setStyleSheet(f"color:{C_SUBTEXT}; font-size:11px; border:none;")
                sugg.setWordWrap(True)
                fl.addWidget(sugg)

            self._diag_layout.addWidget(frame)

        self._diag_layout.addStretch()

    def _fill_briefing(self, result: dict, mc: dict, cfg: dict):
        """교전 후 브리핑 텍스트를 REQ 탭 하단 패널에 채운다."""
        if not _V7_OK:
            return
        text = generate_briefing(result, mc, cfg)
        self._briefing_browser.setPlainText(text)

    def _save_briefing_txt(self):
        """브리핑 텍스트를 TXT 파일로 저장."""
        text = self._briefing_browser.toPlainText()
        if not text.strip():
            QMessageBox.information(self, "안내", "먼저 시뮬레이션을 실행하세요.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "브리핑 저장", "briefing.txt", "Text (*.txt)")
        if not path:
            return
        with open(path, 'w', encoding='utf-8') as f:
            f.write(text)
        QMessageBox.information(self, "저장 완료", f"브리핑 저장:\n{path}")

    def _run_weather_compare(self):
        """포팅 D: 날씨별 3종 비교 실행 (WeatherWorker 비차단)."""
        if not _V7_OK or not hasattr(self, '_result'):
            QMessageBox.information(self, "안내", "먼저 시뮬레이션을 실행하세요.")
            return
        cfg = self._worker.cfg if self._worker else {}
        if not cfg:
            return
        self.btn_weather_run.setEnabled(False)
        self.btn_weather_run.setText("실행 중... (약 30~60초)")
        self._weather_worker = WeatherWorker(cfg, n=1000)
        self._weather_worker.finished.connect(self._on_weather_done)
        self._weather_worker.error.connect(self._on_weather_error)
        self._weather_worker.start()

    def _on_weather_done(self, sc: dict):
        self.weather_table.setRowCount(0)
        for label, res in sc.items():
            row = self.weather_table.rowCount()
            self.weather_table.insertRow(row)

            # 최다 소모 무기 (잔여 재고 가장 적은 것)
            wpn_rem = res.get('weapon_avg_remaining', {})
            if wpn_rem:
                top_wpn = min(wpn_rem, key=lambda k: wpn_rem[k])
                top_wpn_str = f"{top_wpn} ({wpn_rem[top_wpn]:.1f}발 잔여)"
            else:
                top_wpn_str = "—"

            # 가장 많이 피격된 함정
            ship_h = res.get('ship_avg_hits', {})
            if ship_h and max(ship_h.values()) > 0:
                top_ship = max(ship_h, key=lambda k: ship_h[k])
                top_ship_str = f"{top_ship} ({ship_h[top_ship]:.2f}회)"
            else:
                top_ship_str = "없음"

            values = [label,
                      f"{res['mean_intercept']:.1%}",
                      f"{res['full_pass_rate']:.1%}",
                      f"${res['mean_cost']:,.0f}",
                      top_wpn_str,
                      top_ship_str]
            for col, text in enumerate(values):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if col == 1:
                    item.setForeground(
                        QColor('#2ecc71' if res['mean_intercept'] >= 0.9 else '#e74c3c'))
                self.weather_table.setItem(row, col, item)
        self.btn_weather_run.setEnabled(True)
        self.btn_weather_run.setText("🌤️  날씨별 비교 실행 (각 1000회 MC)")
        self._sidebar.setCurrentRow(3)

    def _update_vls_warning(self, mc: dict):
        """MC 결과에서 VLS 주요 무기 소진률 + 고갈 확률·시각 확인 후 경고 레이블 갱신."""
        key_wpns = ['SM-3 Block IIA', 'SM-6', 'SM-2 Block IIIB']
        rates = mc.get('weapon_exhaustion_rates', {})
        critical, caution = [], []
        for w in key_wpns:
            r = rates.get(w, 0.0)
            if r >= 0.5:
                critical.append(f"{w} {r:.0%}")
            elif r >= 0.2:
                caution.append(f"{w} {r:.0%}")

        # v9.4: VLS 완전 고갈 확률 + 평균 고갈 시각
        dep_rate = mc.get('vls_depletion_rate', 0.0)
        dep_t    = mc.get('vls_depletion_t_mean', None)
        dep_suffix = ''
        if dep_rate > 0:
            dep_suffix = f"  |  VLS 완전 고갈 {dep_rate:.0%}"
            if dep_t is not None:
                dep_suffix += f" (평균 {dep_t:.0f}s)"

        if critical:
            self._lbl_vls_warn.setText(
                f"🔴 VLS 소진 경고: {' · '.join(critical)}{dep_suffix}")
            self._lbl_vls_warn.setStyleSheet(
                f"color:{C_RED}; font-size:11px; font-weight:bold;")
        elif caution:
            self._lbl_vls_warn.setText(
                f"🟠 VLS 소진 주의: {' · '.join(caution)}{dep_suffix}")
            self._lbl_vls_warn.setStyleSheet(
                f"color:{C_ORANGE}; font-size:11px; font-weight:bold;")
        elif dep_suffix:
            self._lbl_vls_warn.setText(f"🟡{dep_suffix.strip()}")
            self._lbl_vls_warn.setStyleSheet(
                f"color:{C_ORANGE}; font-size:11px;")
        else:
            self._lbl_vls_warn.setText("")

    def _on_weather_error(self, msg: str):
        QMessageBox.critical(self, "날씨 비교 오류", msg)
        self.btn_weather_run.setEnabled(True)
        self.btn_weather_run.setText("🌤️  날씨별 비교 실행 (각 1000회 MC)")

    def _run_ab_compare(self):
        """A/B 편대 비교 실행 (ABCompareWorker 비차단)."""
        if not _V7_OK or not hasattr(self, '_result'):
            QMessageBox.information(self, "안내", "먼저 시뮬레이션을 실행하세요.")
            return
        cfg_a = self._worker.cfg if self._worker else {}
        if not cfg_a:
            return
        preset_b = self._cb_ab_fleet_b.currentText()
        if not preset_b or preset_b == cfg_a.get('fleet_preset', ''):
            QMessageBox.information(self, "안내",
                "B 편대를 A 편대와 다른 프리셋으로 선택하세요.")
            return
        cfg_b = dict(cfg_a)
        cfg_b['fleet_preset'] = preset_b
        n = self._sb_ab_n.value()
        self.btn_ab_run.setEnabled(False)
        self.btn_ab_run.setText(f"실행 중... (각 {n}회 MC)")
        self._ab_worker = ABCompareWorker(cfg_a, cfg_b, n=n)
        self._ab_worker.finished.connect(self._on_ab_done)
        self._ab_worker.error.connect(self._on_ab_error)
        self._ab_worker.start()

    def _on_ab_done(self, result: dict):
        mc_a = result['a']
        mc_b = result['b']
        cfg_a = self._worker.cfg if self._worker else {}
        preset_a = cfg_a.get('fleet_preset', 'A')
        preset_b = self._cb_ab_fleet_b.currentText()

        def _top_wpn(mc):
            rem = mc.get('weapon_avg_remaining', {})
            if rem:
                k = min(rem, key=lambda x: rem[x])
                return f"{k} ({rem[k]:.1f}발 잔여)"
            return "—"

        def _top_ship(mc):
            sh = mc.get('ship_avg_hits', {})
            if sh and max(sh.values(), default=0) > 0:
                k = max(sh, key=lambda x: sh[x])
                return f"{k} ({sh[k]:.2f}회)"
            return "없음"

        rows = [
            (0, preset_a, mc_a),
            (1, preset_b, mc_b),
        ]
        for row, preset, mc in rows:
            vals = [
                preset,
                f"{mc['mean_intercept']:.1%}",
                f"{mc.get('full_pass_rate', 0):.1%}",
                f"${float(__import__('numpy').mean(mc['total_costs'])):,.0f}",
                _top_wpn(mc),
                _top_ship(mc),
            ]
            for col, text in enumerate(vals):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if col == 1:
                    item.setForeground(
                        QColor('#2ecc71' if mc['mean_intercept'] >= 0.9 else '#e74c3c'))
                self._ab_summary_table.setItem(row, col, item)

        d_int = result['delta_intercept']
        d_cost = result['delta_cost']
        sign_int  = "▲" if d_int  >= 0 else "▼"
        sign_cost = "▲" if d_cost >= 0 else "▼"
        color_int  = '#2ecc71' if d_int  >= 0 else '#e74c3c'
        color_cost = '#e74c3c' if d_cost >= 0 else '#2ecc71'  # 비용은 증가가 불리
        self._lbl_ab_delta.setText(
            f"  Δ 요격률 (B−A): "
            f"<span style='color:{color_int};'>{sign_int} {abs(d_int):.1%}</span>"
            f"    Δ 비용 (B−A): "
            f"<span style='color:{color_cost};'>{sign_cost} ${abs(d_cost):,.0f}</span>"
        )
        self._lbl_ab_delta.setTextFormat(Qt.TextFormat.RichText)

        # 무기 잔여 비교 테이블
        wpn_a = mc_a.get('weapon_avg_remaining', {})
        wpn_b = mc_b.get('weapon_avg_remaining', {})
        all_wpns = sorted(set(wpn_a) | set(wpn_b))
        self._ab_weapon_table.setRowCount(0)
        for wpn in all_wpns:
            r = self._ab_weapon_table.rowCount()
            self._ab_weapon_table.insertRow(r)
            va = wpn_a.get(wpn, 0.0)
            vb = wpn_b.get(wpn, 0.0)
            for col, (val, is_b) in enumerate([(wpn, False), (va, False), (vb, True)]):
                text = f"{val:.1f}" if isinstance(val, float) else str(val)
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                if is_b and isinstance(vb, float) and isinstance(va, float):
                    if vb < va:
                        item.setForeground(QColor('#e74c3c'))
                    elif vb > va:
                        item.setForeground(QColor('#2ecc71'))
                self._ab_weapon_table.setItem(r, col, item)

        self.btn_ab_run.setEnabled(True)
        self.btn_ab_run.setText("⚖  A/B 비교 실행")
        self._sidebar.setCurrentRow(22)

    def _on_ab_error(self, msg: str):
        QMessageBox.critical(self, "A/B 비교 오류", msg)
        self.btn_ab_run.setEnabled(True)
        self.btn_ab_run.setText("⚖  A/B 비교 실행")

    # ── 생존성 히트맵 ────────────────────────────────────────────────────────

    def _run_heatmap(self):
        """HeatmapWorker 시작."""
        fleet_sel = [c.text() for c in self._hm_fleet_checks if c.isChecked()]
        enemy_sel = [c.text() for c in self._hm_enemy_checks if c.isChecked()]
        if len(fleet_sel) < 1 or len(enemy_sel) < 1:
            QMessageBox.information(self, "안내", "편대와 위협을 각각 1개 이상 선택하세요.")
            return

        # base_cfg: 현재 시뮬 설정 or 기본값
        if self._worker and self._worker.cfg:
            base_cfg = dict(self._worker.cfg)
        else:
            base_cfg = {
                'weather': '맑음 (주간)', 'detect_km_manual': False,
                'enemy_fleet_mode': 'preset', 'enemy_fleet_preset': fleet_sel[0],
                'enemy_fleet_difficulty': '보통', 'enemy_fleet_seed': None,
                'enable_ecm': True, 'enable_evasion': True,
                'enable_decoy': True, 'enable_selfdefense': True,
                # BUG-3 fix: 항공 자산 기본 OFF (체크박스 반영), CEC 키 신버전으로 통일
                'enable_helo': False, 'enable_p3c': False, 'enable_p8a': False,
                'enable_f35a': False, 'enable_kf21': False, 'enable_fa50': False,
                'enable_layered_defense': True, 'enable_cec': True,
                'enable_multibearing': False, 'enable_cec_jammed': False,
                'enable_ship_evasion': True, 'enable_radar_off': True,
                'enable_random_placement': True, 'random_spread_km': 10.0,
                'enemy_tactics': None, 'ai_tactic': None,
                'sim_seed': None, 'enable_strike': False,
                'haesong2_stock': 8, 'harpoon_stock': 4, 'hyunmoo4_stock': 2,
                'cd_time_s': 10, 'confirm_time_s': 3,
            }

        n = self._hm_sb_n.value()
        total = len(fleet_sel) * len(enemy_sel)

        self._hm_fleet_labels = fleet_sel
        self._hm_enemy_labels = enemy_sel
        self._hm_done_count   = 0
        self._hm_total        = total

        self.btn_hm_run.setEnabled(False)
        self.btn_hm_run.setText("실행 중...")
        self.btn_hm_save.setEnabled(False)
        self._hm_progress_lbl.setText(f"0 / {total} 셀 완료")

        self._hm_worker = HeatmapWorker(base_cfg, fleet_sel, enemy_sel, n=n)
        self._hm_worker.cell_done.connect(self._on_heatmap_cell)
        self._hm_worker.finished.connect(self._on_heatmap_done)
        self._hm_worker.error.connect(self._on_heatmap_error)
        self._hm_worker.start()

    def _on_heatmap_cell(self, r: int, c: int, val: float):
        """셀 하나 완료 — 진행률 갱신."""
        self._hm_done_count += 1
        self._hm_progress_lbl.setText(
            f"{self._hm_done_count} / {self._hm_total} 셀 완료")

    def _on_heatmap_done(self, grid: list):
        """모든 셀 완료 — matplotlib 히트맵 렌더링."""
        import numpy as np
        import matplotlib.colors as mcolors

        self._hm_grid = grid
        rows = self._hm_fleet_labels
        cols = self._hm_enemy_labels
        data = np.array(grid)   # shape (len(rows), len(cols))

        fig = self._hm_canvas.figure
        fig.clf()
        ax = fig.add_subplot(111)
        fig.patch.set_facecolor(C_BG)
        ax.set_facecolor(C_BG)

        # 0=적색, 0.5=주황, 1=녹색 커스텀 컬러맵
        cmap = mcolors.LinearSegmentedColormap.from_list(
            'surv', ['#e74c3c', '#e67e22', '#f1c40f', '#2ecc71'])
        im = ax.imshow(data, cmap=cmap, vmin=0.0, vmax=1.0,
                       aspect='auto', interpolation='nearest')

        # 셀 텍스트 오버레이
        for r_i, row_data in enumerate(data):
            for c_i, val in enumerate(row_data):
                color = 'white' if val < 0.65 else '#0d1117'
                ax.text(c_i, r_i, f"{val:.0%}",
                        ha='center', va='center',
                        fontsize=9, color=color, fontweight='bold')

        ax.set_xticks(range(len(cols)))
        ax.set_yticks(range(len(rows)))
        ax.set_xticklabels(cols, rotation=30, ha='right',
                           fontsize=9, color=C_TEXT)
        ax.set_yticklabels(rows, fontsize=9, color=C_TEXT)
        ax.set_xlabel("적군 위협 프리셋", color=C_SUBTEXT, fontsize=10)
        ax.set_ylabel("아군 편대", color=C_SUBTEXT, fontsize=10)
        ax.set_title("생존성 히트맵  (요격률 — 녹색 = 높음 / 적색 = 낮음)",
                     color=C_TEXT, fontsize=11, pad=10)
        ax.tick_params(colors=C_TEXT)
        for spine in ax.spines.values():
            spine.set_edgecolor(C_BORDER)

        cbar = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
        cbar.ax.yaxis.set_tick_params(color=C_SUBTEXT)
        cbar.set_label("요격률", color=C_SUBTEXT, fontsize=9)
        plt.setp(cbar.ax.yaxis.get_ticklabels(), color=C_SUBTEXT, fontsize=8)

        fig.tight_layout()
        self._hm_canvas.draw()

        self.btn_hm_run.setEnabled(True)
        self.btn_hm_run.setText("🗺  히트맵 실행")
        self.btn_hm_save.setEnabled(True)
        self._hm_progress_lbl.setText(
            f"완료 — {len(rows)}×{len(cols)} 셀")
        self._sidebar.setCurrentRow(25)

    def _on_heatmap_error(self, msg: str):
        QMessageBox.critical(self, "히트맵 오류", msg)
        self.btn_hm_run.setEnabled(True)
        self.btn_hm_run.setText("🗺  히트맵 실행")
        self._hm_progress_lbl.setText("오류")

    def _save_heatmap_png(self):
        """히트맵 PNG로 저장."""
        path, _ = QFileDialog.getSaveFileName(
            self, "히트맵 저장", "heatmap.png", "PNG (*.png)")
        if path:
            self._hm_canvas.figure.savefig(
                path, dpi=150, bbox_inches='tight',
                facecolor=C_BG)
            QMessageBox.information(self, "저장 완료", f"저장됨: {path}")

    def _on_error(self, msg: str):
        self.btn_run.setEnabled(True)
        self._prog.setVisible(False)
        self._lbl_status.setText("오류 발생")
        QMessageBox.critical(self, "시뮬레이션 오류", msg)

    def closeEvent(self, event):
        # SimWorker 중단 (MC 분석 실행 중이면 배치 루프에서 중단 신호 감지)
        if self._worker and self._worker.isRunning():
            self._worker.requestInterruption()
            self._worker.quit()
            if not self._worker.wait(2000):
                self._worker.terminate()
                self._worker.wait(500)
        # SensitivityWorker 중단
        sens = getattr(self, '_sens_worker', None)
        if sens and sens.isRunning():
            sens.requestInterruption()
            sens.quit()
            if not sens.wait(1000):
                sens.terminate()
                sens.wait(500)
        # MinStockWorker 중단
        ms = getattr(self, '_ms_worker', None)
        if ms and ms.isRunning():
            ms.requestInterruption()
            ms.quit()
            if not ms.wait(1000):
                ms.terminate()
                ms.wait(500)
        # OptimizeWorker 중단
        opt = getattr(self, '_opt_worker', None)
        if opt and opt.isRunning():
            opt.requestInterruption()
            opt.quit()
            if not opt.wait(1000):
                opt.terminate()
                opt.wait(500)
        # WeatherWorker 중단
        ww = getattr(self, '_weather_worker', None)
        if ww and ww.isRunning():
            ww.requestInterruption()
            ww.quit()
            if not ww.wait(800):
                ww.terminate()
                ww.wait(300)
        # ABCompareWorker 중단
        ab = getattr(self, '_ab_worker', None)
        if ab and ab.isRunning():
            ab.requestInterruption()
            ab.quit()
            if not ab.wait(800):
                ab.terminate()
                ab.wait(300)
        # HeatmapWorker 중단
        hm = getattr(self, '_hm_worker', None)
        if hm and hm.isRunning():
            hm.requestInterruption()
            hm.quit()
            if not hm.wait(800):
                hm.terminate()
                hm.wait(300)
        # 차트 렌더 워커 11개 중단 (ChartPageWidget._worker)
        for attr in ('tab_mc_canvas', 'tab_channel', 'tab_cost_eff',
                     'tab_ammo_curve', 'tab_ci', 'tab_timeline',
                     'tab_bearing', 'tab_req_radar', 'tab_threat_type',
                     'tab_vuln_time', 'tab_history',
                     'tab_sensitivity', 'tab_min_stock', 'tab_optimize',
                     'tab_cec_compare'):
            widget = getattr(self, attr, None)
            if widget:
                widget.stop_worker()
        # 교전 분석 탭 차트 워커 중단
        if hasattr(self, 'tab_engagement'):
            self.tab_engagement.stop_worker()
        # 글로벌 프로세스 풀 종료 (워커 프로세스 강제 kill 포함)
        _shutdown_global_pool()
        # 시스템 모니터 워커 중단 (nvidia-smi subprocess 포함)
        _stop_sys_data_worker()
        # 남은 자식 프로세스 강제 종료 (좀비 프로세스 완전 제거)
        try:
            me = psutil.Process()
            for child in me.children(recursive=True):
                try:
                    child.kill()
                except Exception:
                    pass
        except Exception:
            pass
        event.accept()

    # ── 결과 렌더링 ──────────────────────────────────────────────────────────

    def _update_cards(self, result: dict, mc: dict):
        self._cards['intercept'].setText(f"{mc['mean_intercept']:.1%}")
        self._cards['intercept'].setStyleSheet(
            f"color:{'#2ecc71' if mc['mean_intercept'] >= 0.9 else '#e74c3c'};")
        self._cards['full_pass'].setText(f"{mc['full_pass_rate']:.1%}")
        cvar_val = mc.get('cvar')
        if cvar_val is not None:
            self._cards['cvar'].setText(f"{cvar_val:.1%}")
            self._cards['cvar'].setStyleSheet(
                f"color:{'#2ecc71' if cvar_val >= 0.7 else '#e74c3c'};")
        else:
            self._cards['cvar'].setText("—")
        self._cards['friendly_hit'].setText(str(result['friendly_hits']))
        self._cards['friendly_hit'].setStyleSheet(
            f"color:{'#2ecc71' if result['friendly_hits'] == 0 else '#e74c3c'};")
        self._cards['enemy_dest'].setText(str(result['enemy_ships_destroyed']))
        self._cards['cost'].setText(f"${result['total_cost']:,.0f}")
        sorties = result.get('aircraft_sorties', 0)
        self._cards['aircraft'].setText(f"{sorties}회" if sorties else "—")
        # 사용된 시드 표시 (재현용)
        seed = result.get('used_seed')
        if seed:
            self._lbl_seed_used.setText(f"시드: {seed}  (재현하려면 시뮬 시드에 동일 값 입력)")
        else:
            self._lbl_seed_used.setText("시드: 랜덤  (재현 불가)")

    def _draw_mc_chart(self, result: dict, mc: dict, cfg: dict):
        self.tab_mc_canvas.start_render(_render_mc_chart, result, mc, cfg)

    def _fill_log(self, log: list):
        # BUG-1: 최대 300행 제한 + 배치 삽입 (UI 블로킹 방지)
        entries = log[-300:] if len(log) > 300 else log
        self.log_table.setUpdatesEnabled(False)
        self.log_table.setRowCount(0)
        for t, msg in entries:
            row = self.log_table.rowCount()
            self.log_table.insertRow(row)
            t_item = QTableWidgetItem(f"{t:.0f}s")
            t_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.log_table.setItem(row, 0, t_item)
            self.log_table.setItem(row, 1, QTableWidgetItem(msg))
        self.log_table.setUpdatesEnabled(True)

    def _draw_channel_heatmap(self, result: dict):
        self.tab_channel.start_render(_render_channel_heatmap, result)

    def _draw_cost_effect(self, result: dict, mc: dict):
        self.tab_cost_eff.start_render(_render_cost_effect, result, mc)

    def _draw_ammo_curve(self, mc: dict):
        self.tab_ammo_curve.start_render(_render_ammo_curve, mc)

    def _draw_ci_chart(self, mc: dict):
        self.tab_ci.start_render(_render_ci_chart, mc)

    def _draw_timeline(self, result: dict):
        self.tab_timeline.start_render(_render_timeline, result)

    def _lazy_start_sensitivity(self):
        """감도 분석 탭 첫 방문 시 SensitivityWorker 기동 (lazy-start)."""
        if not hasattr(self, '_pending_cfg'):
            return
        sens = getattr(self, '_sens_worker', None)
        if sens and sens.isRunning():
            return
        self._sensitivity_placeholder()
        self._sens_worker = SensitivityWorker(self._pending_cfg, self._pending_mc_n)
        self._sens_worker.finished.connect(self._on_sensitivity_done)
        self._sens_worker.error.connect(lambda e: self._sensitivity_error(e))
        self._sens_worker.start(QThread.Priority.LowPriority)

    def _lazy_start_min_stock(self):
        """최소 재고 탭 첫 방문 시 MinStockWorker 기동 (lazy-start)."""
        if not hasattr(self, '_pending_cfg'):
            return
        ms = getattr(self, '_ms_worker', None)
        if ms and ms.isRunning():
            return
        self._min_stock_placeholder()
        self._ms_worker = MinStockWorker(self._pending_cfg, self._pending_mc_n)
        self._ms_worker.progress.connect(self._on_min_stock_progress)
        self._ms_worker.finished.connect(self._on_min_stock_done)
        self._ms_worker.error.connect(lambda e: self._min_stock_error(e))
        self._ms_worker.start(QThread.Priority.LowPriority)

    def _sensitivity_placeholder(self):
        self.tab_sensitivity._loading_lbl.setText("  감도 분석 계산 중… ⏳")
        self.tab_sensitivity._pane.setCurrentIndex(0)

    def _sensitivity_error(self, msg: str):
        self.tab_sensitivity._loading_lbl.setText(f"  감도 분석 오류: {msg}")

    def _min_stock_placeholder(self):
        self.tab_min_stock._loading_lbl.setText("  최소 재고 역산 계산 중… ⏳")
        self.tab_min_stock._pane.setCurrentIndex(0)

    def _min_stock_error(self, msg: str):
        self.tab_min_stock._loading_lbl.setText(f"  최소 재고 계산 오류: {msg}")

    def _on_min_stock_progress(self, i: int, total: int, name: str):
        if i < total:
            self._lbl_status.setText(f"최소 재고 계산 중 ({i}/{total}) — {name}")

    def _on_min_stock_done(self, results: dict, target_rate: float):
        self.tab_min_stock.start_render(_render_min_stock_chart, results, target_rate)

    def _on_sensitivity_done(self, labels: list, lows: list, highs: list, base_rate: float):
        self.tab_sensitivity.start_render(_render_sensitivity_chart, labels, lows, highs, base_rate)

    def _lazy_start_optimize(self):
        """최적 조합 탭 첫 방문 시 OptimizeWorker 기동 (lazy-start)."""
        if not hasattr(self, '_pending_cfg'):
            return
        opt = getattr(self, '_opt_worker', None)
        if opt and opt.isRunning():
            return
        self._optimize_placeholder()
        self._opt_worker = OptimizeWorker(self._pending_cfg)
        self._opt_worker.progress.connect(self._on_optimize_progress)
        self._opt_worker.finished.connect(self._on_optimize_done)
        self._opt_worker.error.connect(lambda e: self._optimize_error(e))
        self._opt_worker.start(QThread.Priority.LowPriority)

    def _optimize_placeholder(self):
        self.tab_optimize._loading_lbl.setText(
            "  최적 조합 탐색 중… (예산 64발 / 16발 단위 그리드 서치 + 정밀 검증) ⏳")
        self.tab_optimize._pane.setCurrentIndex(0)

    def _optimize_error(self, msg: str):
        self.tab_optimize._loading_lbl.setText(f"  최적 조합 탐색 오류: {msg}")

    def _on_optimize_progress(self, done: int, total: int, phase: str):
        phase_lbl = '정밀 검증' if phase == 'fine' else '1차 탐색'
        self._lbl_status.setText(f"최적 조합 탐색 중 ({done}/{total}) — {phase_lbl}")

    def _on_optimize_done(self, results: list):
        self.tab_optimize.start_render(_render_optimize_chart, results)
        best = results[0] if results else None
        if best:
            self._lbl_status.setText(
                f"최적 조합: 요격률 {best['rate']:.1%} | "
                + '  '.join(f"{k.split()[0]}×{v}"
                            for k, v in best['combo'].items() if v > 0))

    def _lazy_start_cec_compare(self):
        """CEC 비교 탭 첫 방문 시 CECCompareWorker 기동 (lazy-start)."""
        if not _V7_OK or not self._pending_cfg:
            return
        if getattr(self, '_cec_worker', None) and self._cec_worker.isRunning():
            return
        self.tab_cec_compare._loading_lbl.setText(
            "  CEC ON/OFF/두절 3종 MC 비교 중… ⏳")
        self.tab_cec_compare._pane.setCurrentIndex(0)
        self._cec_worker = CECCompareWorker(self._pending_cfg, n=500)
        self._cec_worker.finished.connect(self._on_cec_compare_done)
        self._cec_worker.error.connect(
            lambda e: self.tab_cec_compare._loading_lbl.setText(f"  CEC 비교 오류: {e}"))
        self._cec_worker.start(QThread.Priority.LowPriority)

    def _on_cec_compare_done(self, cec_results: dict):
        self.tab_cec_compare.start_render(_render_cec_compare, cec_results)
        if cec_results:
            labels = list(cec_results.keys())
            rates  = [cec_results[l].get('mean_intercept', 0) for l in labels]
            if len(rates) >= 2:
                delta = (rates[0] - rates[1]) * 100
                sign  = '+' if delta >= 0 else ''
                self._lbl_status.setText(
                    f"CEC 비교 완료: CEC ON vs OFF {sign}{delta:.1f}%p")

    def _draw_bearing_vulnerability(self, result: dict):
        self.tab_bearing.start_render(_render_bearing_vulnerability, result)

    def _draw_req_radar(self, result: dict, mc: dict):
        cfg = self._worker.cfg if self._worker else None
        self.tab_req_radar.start_render(_render_req_radar, result, mc, cfg)

    def _draw_threat_type(self, result: dict, mc: dict):
        self.tab_threat_type.start_render(_render_threat_type, result, mc)

    def _draw_vuln_time(self, result: dict):
        self.tab_vuln_time.start_render(_render_vuln_time, result)

    def _draw_history_compare(self, result: dict, mc: dict):
        self.tab_history.start_render(_render_history_compare, list(self._history))

    def _draw_stress_test(self, mc: dict):
        self.tab_stress.start_render(_render_stress_test, mc.get('stress', {}))

    def _draw_sobol_chart(self, mc: dict):
        self.tab_sobol.start_render(_render_sobol_chart, mc.get('sobol', {}))

    # ── 보고서 내보내기 ──────────────────────────────────────────────────────

    def _export_excel(self):
        """결과를 Excel 보고서로 저장."""
        if not _V7_OK or not self._result:
            QMessageBox.information(self, "안내", "먼저 시뮬레이션을 실행하세요.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Excel 보고서 저장", "report.xlsx", "Excel (*.xlsx)")
        if not path:
            return
        try:
            cfg = self._worker.cfg if self._worker else {}
            save_excel_report_v7(self._result, self._mc, cfg, path)
            QMessageBox.information(self, "저장 완료", f"Excel 보고서 저장:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "오류", str(e))

    def _export_pdf(self):
        """결과를 PDF 보고서로 저장 (matplotlib 다중 페이지)."""
        if not _V7_OK or not self._result:
            QMessageBox.information(self, "안내", "먼저 시뮬레이션을 실행하세요.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "PDF 보고서 저장", "report.pdf", "PDF (*.pdf)")
        if not path:
            return
        try:
            self._generate_pdf_report(path)
            QMessageBox.information(self, "저장 완료", f"PDF 보고서 저장:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "오류", str(e))

    def _generate_pdf_report(self, path: str):
        """matplotlib PdfPages로 다중 페이지 PDF 생성."""
        from matplotlib.backends.backend_pdf import PdfPages
        result = self._result
        mc     = self._mc
        cfg    = self._worker.cfg if self._worker else {}

        with PdfPages(path) as pdf:
            # 1페이지: 커버 + 핵심 지표
            fig, ax = plt.subplots(figsize=(11.7, 8.3))
            fig.patch.set_facecolor('#0a0e1a')
            ax.set_facecolor('#0a0e1a')
            ax.axis('off')
            lines = [
                ("이지스 기동전단 통합 방어 시뮬레이터", 30, C_ACCENT, 'bold'),
                ("전투 분석 보고서", 20, C_TEXT, 'normal'),
                ("", 14, C_TEXT, 'normal'),
                (f"날씨: {cfg.get('weather', '—')}  |  "
                 f"적군: {cfg.get('enemy_fleet_preset', cfg.get('enemy_fleet_mode', '—'))}  |  "
                 f"MC: {mc.get('n', '—')}회", 12, C_SUBTEXT, 'normal'),
                ("", 12, C_TEXT, 'normal'),
                (f"요격률: {mc['mean_intercept']:.1%}  |  "
                 f"완전 요격: {mc.get('full_pass_rate', 0):.1%}  |  "
                 f"아군 피격: {result.get('friendly_hits', 0)}회", 14, '#2ecc71', 'bold'),
                (f"격추 비용: ${mc.get('mean_cost', 0):,.0f}  |  "
                 f"적 격침: {result.get('enemy_ships_destroyed', 0)}척", 14, C_TEXT, 'normal'),
            ]
            y = 0.85
            for text, size, color, weight in lines:
                ax.text(0.5, y, text, ha='center', va='top', color=color,
                        fontsize=size, fontweight=weight, transform=ax.transAxes)
                y -= 0.10
            pdf.savefig(fig, facecolor='#0a0e1a')
            plt.close(fig)

            # 2페이지: MC 통계 차트
            mc_bytes = getattr(self.tab_mc_canvas, '_raw_bytes', b'')
            if mc_bytes:
                import io as _io
                from matplotlib.image import imread as _mpl_imread
                fig2, ax2 = plt.subplots(figsize=(11.7, 8.3))
                fig2.patch.set_facecolor('#0a0e1a')
                ax2.set_facecolor('#0a0e1a')
                ax2.imshow(_mpl_imread(_io.BytesIO(mc_bytes)))
                ax2.axis('off')
                ax2.set_title('MC 통계', color=C_TEXT, fontsize=14, pad=10)
                pdf.savefig(fig2, facecolor='#0a0e1a')
                plt.close(fig2)

            # 3페이지: 비용 효과 + 탄약 소모
            fig3, axes3 = plt.subplots(1, 2, figsize=(11.7, 8.3))
            fig3.patch.set_facecolor('#0a0e1a')
            fig3.suptitle('비용 효과 / 탄약 소모', color=C_TEXT, fontsize=14)
            for ax3 in axes3:
                ax3.set_facecolor('#0a0e1a')

            # 비용 효과
            wpn_rem = mc.get('weapon_avg_remaining', {})
            if wpn_rem:
                wnames = list(wpn_rem.keys())
                wvals  = list(wpn_rem.values())
                axes3[0].barh(wnames, wvals, color=C_ACCENT, alpha=0.8)
                axes3[0].set_xlabel('평균 잔여 재고', color=C_SUBTEXT, fontsize=9)
                axes3[0].set_title('무기별 잔여 재고', color=C_TEXT, fontsize=10)
                axes3[0].tick_params(colors=C_SUBTEXT)
                for sp in axes3[0].spines.values(): sp.set_color('#1e2a3a')

            # 함정별 피격
            ship_hits = mc.get('ship_avg_hits', {})
            if ship_hits:
                snames = list(ship_hits.keys())
                svals  = list(ship_hits.values())
                cols   = ['#e74c3c' if v > 0.5 else '#2ecc71' for v in svals]
                axes3[1].bar(snames, svals, color=cols, alpha=0.8)
                axes3[1].set_ylabel('평균 피격 횟수', color=C_SUBTEXT, fontsize=9)
                axes3[1].set_title('함정별 평균 피격 (MC)', color=C_TEXT, fontsize=10)
                axes3[1].tick_params(colors=C_SUBTEXT, axis='x', rotation=15)
                for sp in axes3[1].spines.values(): sp.set_color('#1e2a3a')

            pdf.savefig(fig3, facecolor='#0a0e1a')
            plt.close(fig3)

            # 4페이지: 교전 로그 요약
            fig4, ax4 = plt.subplots(figsize=(11.7, 8.3))
            fig4.patch.set_facecolor('#0a0e1a')
            ax4.set_facecolor('#0a0e1a')
            ax4.axis('off')
            ax4.set_title('교전 로그 (최근 30건)', color=C_TEXT, fontsize=14, pad=10)
            log = result.get('log', [])[-30:]
            y = 0.95
            for t, msg in log:
                color = '#e74c3c' if '[피격]' in msg else (
                    '#2ecc71' if '[요격]' in msg else C_TEXT)
                ax4.text(0.02, y, f"[{t:>5.0f}s]  {msg[:90]}",
                         ha='left', va='top', color=color, fontsize=7,
                         transform=ax4.transAxes, fontfamily='monospace')
                y -= 0.03
                if y < 0.02:
                    break
            pdf.savefig(fig4, facecolor='#0a0e1a')
            plt.close(fig4)


# ════════════════════════════════════════════════════════════════════════════
#  SplashWindow — 런처 화면
# ════════════════════════════════════════════════════════════════════════════

TERM_TOOLTIPS: dict[str, str] = {
    'ARM':      '대방사미사일(Anti-Radiation Missile) — 적 레이더가 내뿜는 전파를 역추적해 레이더 자체를 파괴하는 미사일.',
    'CIWS':     '근접방어무기체계(Close-In Weapon System) — 함정 최후 방어선. 분당 수천 발 기관포로 수 km 내 목표를 요격.',
    'CEC':      '협동교전능력(Cooperative Engagement Capability) — 여러 함정이 탐지 정보를 실시간 공유해 단일 지휘처럼 교전.',
    'RCS':      '레이더 반사 면적(Radar Cross Section) — 값이 작을수록 레이더에 잘 안 잡힘. 스텔스 설계의 핵심 지표.',
    'ECM':      '전자방해(Electronic Countermeasure) — 적 레이더·유도장치를 전파로 교란해 탐지거리·명중률을 떨어뜨림.',
    'VLS':      '수직발사시스템(Vertical Launch System) — 함정 갑판 아래 수직으로 배치된 미사일 발사관. 전방향 즉시 발사 가능.',
    'BMD':      '탄도미사일방어(Ballistic Missile Defense) — 대기권 밖에서 재진입하는 탄도미사일을 추적·요격하는 체계.',
    'OTH':      '수평선 너머 표적(Over-The-Horizon) — 직접 시선 밖의 먼 거리 표적을 위성·헬기·데이터링크로 공격하는 방식.',
    'HGV':      '극초음속 활공체(Hypersonic Glide Vehicle) — 마하 5+ 속도로 활공하며 기동, 기존 방공망 회피에 특화.',
    'QBM':      '준탄도미사일(Quasi-Ballistic Missile) — 탄도궤도와 순항궤도를 혼합, 종말 단계에서 급기동해 요격 어렵게 설계.',
    'DEM':      '수치표고모델(Digital Elevation Model) — 지형 고도 데이터. 산·섬이 레이더를 가리는 음영 구역 계산에 활용.',
    'SM-2':     '스탠더드 미사일 2 — 함대공미사일. 유효 사거리 90~180km, 항공기·순항미사일 요격 전담.',
    'SM-3':     '스탠더드 미사일 3 — 대기권 밖에서 탄도미사일을 충돌 요격(Hit-to-Kill). BMD 핵심 무기.',
    'SM-6':     '스탠더드 미사일 6 — SM-2 후계. 수평선 너머 표적(OTH) 교전 및 탄도미사일 말단 단계 요격 겸용.',
    'RAM':      'RIM-116 롤링 에어프레임 미사일 — CIWS급 단거리 함대공미사일. 순항미사일·헬기 최후 방어에 사용.',
    'REQ':      '요구조건(Requirement) — 작전 성공 기준. 예: "요격률 85% 이상" 달성 여부로 시뮬레이션 합격·불합격 판정.',
    'CVaR':     '조건부 위험값(Conditional Value at Risk) — 최악 5% 시나리오의 평균 성과. 극단적 상황에서의 방어력 하한선.',
    'LHS':      '라틴 하이퍼큐브 샘플링 — 파라미터 불확실성 분석 기법. 전체 입력 공간을 균등하게 탐색해 편향 없는 통계 생성.',
    'Sobol':    'Sobol 민감도 분석 — 어떤 입력 파라미터가 결과에 가장 큰 영향을 미치는지 수치로 분해하는 글로벌 민감도 방법.',
    'SPY-1D':   'AN/SPY-1D — 이지스 함정의 4면 고정 위상배열 레이더. 360° 동시 탐색·추적, 빔 회전 주기 약 6초.',
    'Kh-31P':   'Kh-31P — 러시아제 대방사미사일. 마하 3.5+, 110km 사거리. 레이더 전파를 수동 추적해 직격.',
    'LD-10':    'LD-10 — 중국 PLAAF 대방사미사일. Kh-31P와 유사한 역할, J-16·JH-7 운용.',
    'Kh-58U':   'Kh-58U — 러시아제 대방사미사일. 마하 3.6, 250km 장거리. Su-24·Su-34에서 운용.',
    'YJ-21':    'YJ-21(鷹擊-21) — 중국 극초음속 대함미사일. 마하 10, 1500km 사거리. 항모 킬러.',
    'IRBM':     '중거리 탄도미사일(Intermediate-Range Ballistic Missile) — 사거리 3,000~5,500km. 북한 화성-12 등.',
    'HAD':      '항모전단 방어권(Carrier Group Air Defense) — 항모를 중심으로 호위함들이 다층 방어망을 구성하는 개념.',
    '055형':    '055형 구축함(Type 055) — 중국 최신예 대형 구축함. 1만 2천 톤급, 112셀 VLS. 미 알레이버크급 능가 설계.',
    '054A형':   '054A형 호위함(Type 054A) — 중국 4000톤급 호위함. HHQ-16 함대공미사일, 어뢰 탑재.',
    'FFX':      '차기 호위함(FFX) — 한국 해군 미래 호위함. FFX-I(인천급) → FFX-II → FFX-III로 능력 단계 향상.',
    'KDX':      '한국형 구축함(KDX) — KDX-II(충무공이순신급) 4,500t, KDX-III(세종대왕급) 1만t 이지스 구축함.',
    'C2':       '지휘통제(Command & Control) — 교전 결심·자원 배분·정보 공유를 총괄하는 지휘 체계.',
}

def _apply_term_tooltip(item: 'QTableWidgetItem', text: str) -> None:
    hits = [tip for kw, tip in TERM_TOOLTIPS.items() if kw in text]
    if hits:
        item.setToolTip('\n\n'.join(hits))


_FEATURES = [
    ("📊  교전 분석",
     "시뮬레이션 결과를 세 가지 차트로 분석. "
     "① 방어 Funnel: SM-3→SM-6→SM-2→ESSM→CIWS 레이어별 격추 수 시각화. "
     "② 위협 추적 테이블: 각 위협이 어느 무기·거리·시각에 격추됐는지(또는 뚫렸는지) 일람. "
     "③ 교전 타임라인: 위협별 교전 시작~종료 구간을 색상 바로 표시 (초록=요격, 빨강=피격)."),
    ("📊  반복 시뮬레이션 통계",
     "같은 시나리오를 수백~수천 번 자동 반복해 '평균적으로 몇 %를 막아내는지' 확률로 계산. "
     "결과가 운에 따라 얼마나 달라지는지 분포 그래프로 확인 가능."),
    ("⚡  시뮬레이션 모드 선택",
     "빠름(5,000회) / 표준(10,000회) / 정밀(100,000회) 중 목적에 맞게 선택. "
     "모든 모드에서 LHS 샘플링·CVaR·스트레스 테스트 자동 실행. "
     "정밀 모드는 추가로 Sobol 파라미터 민감도 분석까지 수행."),
    ("🔥  스트레스 테스트",
     "레이더 성능 저하(0~50%)와 유도 채널 감소(0~75%)를 조합한 12가지 최악 조건을 자동으로 시험. "
     "어떤 상황에서 방어 체계가 무너지는지 색상 히트맵으로 한눈에 파악."),
    ("🎛  Sobol 민감도 분석",
     "SAM 명중률·탐지거리·C&D 시간·ECM 효과·위협 속도 6가지 불확실 파라미터 중 "
     "어느 것이 요격률에 가장 큰 영향을 주는지 수치로 계산. "
     "정밀 모드 전용. 포인트당 반복 수(기본 3회) 설정으로 확률 노이즈 감소 가능."),
    ("✅  전술 요구조건 자동 판정",
     "한국 해군 전술 요구조건 8가지(응답 시간·요격률·함정 생존율 등)를 "
     "시뮬레이션 결과로 자동 통과/실패 판정. 어떤 조건이 미달인지 한눈에 확인."),
    ("🌤️  날씨 조건 비교",
     "맑음·흐림·황사·풍랑·폭풍 등 날씨 조건별로 각각 반복 시뮬레이션해 "
     "날씨가 요격률·무기 소모·피격 횟수에 얼마나 영향을 주는지 나란히 비교."),
    ("📜  교전 기록 로그",
     "미사일 발사, 요격 성공/실패, 함정 피격 등 매 초 단위로 발생한 "
     "모든 교전 사건을 시간 순서대로 전부 기록. 무엇이 언제 일어났는지 추적 가능."),
    ("📡  레이더 채널 포화도",
     "각 함정의 레이더 추적 채널이 시간대별로 얼마나 사용됐는지 색상 히트맵으로 표시. "
     "빨간색에 가까울수록 채널이 꽉 찬 상태 — 채널 포화 시 추가 요격 불가."),
    ("💰  격추 비용 효과",
     "적 1기를 격추하는 데 평균 얼마의 비용이 들었는지 달러 단위로 표시. "
     "무기별 잔여 재고도 함께 확인 가능."),
    ("🔫  탄약 소모 현황",
     "반복 시뮬레이션 기준 평균 잔여 탄약을 무기별 가로 막대그래프로 표시. "
     "어떤 무기가 가장 많이 소모됐는지 비교."),
    ("📈  요격률 신뢰 구간",
     "요격률이 몇 %~몇 % 범위 안에 들어오는지 95% 신뢰구간으로 표시. "
     "함정별 평균 피격 횟수 히스토그램도 함께 표시."),
    ("⏱️  교전 타임라인",
     "어느 시점에 어떤 교전이 발생했는지 시간축 위에 점으로 표시. "
     "언제 가장 많은 위협이 몰렸는지, 요격이 집중된 구간이 어딘지 한눈에 파악."),
    ("🌪️  설정 감도 분석",
     "재고 수량·탐지거리·날씨 등 설정값을 하나씩 바꿔가며 "
     "요격률이 얼마나 민감하게 반응하는지 분석. 백그라운드 실행이라 다른 작업에 영향 없음."),
    ("🧭  방향별 취약점",
     "북·남·동·서 각 방향에서 공격이 들어올 때 피격률과 요격률이 "
     "어떻게 달라지는지 방사형 그래프로 표시 — 어느 방향이 가장 취약한지 확인."),
    ("🎯  요구조건 충족률",
     "8가지 전술 요구조건 각각을 얼마나 충족했는지 방사형 그래프로 한눈에 비교. "
     "전체적인 방어 역량의 균형이 잡혀 있는지 시각적으로 파악."),
    ("📊  위협 유형별 요격률",
     "항공기·탄도미사일·순항미사일·잠수함 유형별로 각각 몇 %를 막아냈는지 분류해서 표시. "
     "어떤 유형의 위협에 취약한지 파악 가능."),
    ("⏰  취약 시간대 분석",
     "교전 시작 후 몇 초 구간에 피격이 집중됐는지 히스토그램으로 표시. "
     "가장 위험한 시간대를 빨간색으로 강조해 방어 집중 구간을 식별."),
    ("🔄  이전 결과 비교",
     "최대 5회 실행한 결과의 요격률과 비용을 자동으로 누적 비교. "
     "설정을 바꿔가며 어떤 조합이 더 효과적인지 히스토리로 추적."),
    ("📋  시나리오 프로필 저장",
     "적 종류·날씨·재고·편대 구성 등 시뮬레이션 설정 전체를 이름 붙여 저장하고 "
     "언제든 불러올 수 있음. 자주 쓰는 시나리오를 매번 다시 설정할 필요 없음."),
    ("📄  보고서 내보내기",
     "시뮬레이션 결과 전체를 Excel 파일과 PDF(4페이지)로 저장. "
     "요격률·비용·교전 통계·그래프가 모두 포함된 공식 분석 보고서 형태."),
    ("🖥️  시스템 모니터",
     "시뮬레이션 실행 중 CPU·RAM·GPU·코어별 사용률을 실시간으로 표시. "
     "백그라운드에서 동작해 시뮬레이션 속도에 영향을 주지 않음."),
    ("📺  실시간 진행 팝업",
     "반복 시뮬레이션 실행 중 별도 팝업 창으로 진행률·완료 횟수·예상 남은 시간·"
     "CPU/RAM/GPU 사용률·처리 속도를 실시간 표시. 창을 마우스로 자유롭게 이동 가능."),
    ("⚡  멀티코어 병렬 처리",
     "프로그램 시작 시 미리 워커 프로세스를 준비해두고, 반복 시뮬레이션 시 "
     "최대 8개 코어를 동시에 활용해 빠르게 처리. 코어가 많을수록 분석 속도 향상."),
    ("⚙️  현실적 전술 기동",
     "데이터링크 두절 상황, 함정 회피 기동, V자 편대 진형, 포위 공격, "
     "다방위 동시 공격 등 실제 해전에서 쓰이는 전술 상황을 시뮬레이션에 반영."),
    ("🌊  적군 위협 데이터베이스",
     "중국 PLA해군·공군 함정·전투기, 북한 탄도·순항·잠수함발사 미사일, "
     "러시아 극초음속 무기, YJ-21·YJ-18 신형 미사일, 드론 떼·소형 자폭 드론까지 총 43종 위협 수록."),
    ("⚓  한국 해군 함정 DB (10종+)",
     "KDX-III Batch I/II(세종대왕·정조대왕급)·KDX-II 구축함·FFX Batch I/II/III 호위함 외 "
     "PKG 윤영하급, PCC 포항급, PKX-B 참수리-II, LPH 독도함급, AOE 소양함까지 수록. "
     "Batch별 SM-3 탑재 유무·해궁 장착 여부 등 실제 제원 반영."),
    ("🏴  현실 기반 편대 프리셋 (10종)",
     "한국 해군 실 교리 기반 편대 5종 추가: 이지스 기동전단 / 이지스 기동전단(강화) / "
     "독도함 상륙전단 / 동해 해역방어(1함대) / 서해 해역방어(2함대). "
     "기존 5종(단독·기본·BMD·대잠·최대)과 합쳐 총 10종 프리셋 제공."),
]


# ════════════════════════════════════════════════════════════════════════════
#  스펙시트 패널
# ════════════════════════════════════════════════════════════════════════════
class SpecSheetPanel(QWidget):
    """선택 유닛 스펙시트 — 우측 패널 (사진 + 카테고리별 상세 스펙 + 스크롤)"""

    _TYPE_ICON = {
        '전투기': '✈', '전폭기': '✈', '폭격기': '✈',
        '탄도미사일': '🚀', '순항미사일': '🚀',
        '극초음속활공체': '🚀', '저고도기동탄도': '🚀',
        '고속정': '⚓', '초계함': '⚓', '호위함': '⚓',
        '구축함': '⚓', '상륙함': '⚓', '순양함': '⚓',
        '잠수함': '🔱',
        '_ship': '⚓', '_weapon': '💥',
    }

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(
            f"background:{C_PANEL}; border-left:1px solid {C_BORDER};"
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 8, 10, 8)
        root.setSpacing(6)

        # ── 상단: 가로 사진 박스 ──────────────────────────────────────────
        self._img_lbl = QLabel()
        self._img_lbl.setFixedHeight(220)
        self._img_lbl.setSizePolicy(
            QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed
        )
        self._img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._img_lbl.setStyleSheet(
            f"background:{C_BG}; border:1px solid {C_BORDER};"
            f" border-radius:4px; font-size:48px;"
        )
        root.addWidget(self._img_lbl)

        # ── 제목 / 부제 행 ────────────────────────────────────────────────
        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        title_row.setContentsMargins(2, 0, 2, 0)

        self._title_lbl = QLabel("← 왼쪽 목록에서 유닛을 선택하세요")
        self._title_lbl.setStyleSheet(
            f"color:{C_ACCENT}; font-size:16px; font-weight:bold;"
        )

        self._sub_lbl = QLabel()
        self._sub_lbl.setStyleSheet(f"color:{C_SUBTEXT}; font-size:14px;")
        self._sub_lbl.setAlignment(
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
        )

        title_row.addWidget(self._title_lbl)
        title_row.addStretch()
        title_row.addWidget(self._sub_lbl)
        root.addLayout(title_row)

        # 구분선
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet(f"color:{C_BORDER};")
        root.addWidget(sep)

        # ── 카테고리 스크롤 영역 ──────────────────────────────────────────
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet(
            f"QScrollArea {{ background:transparent; border:none; }}"
            f"QWidget {{ background:transparent; }}"
            f"QScrollBar:vertical {{ width:6px; background:{C_BG}; }}"
            f"QScrollBar::handle:vertical {{ background:{C_BORDER}; border-radius:3px; min-height:20px; }}"
            f"QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}"
        )

        self._scroll_w = QWidget()
        self._scroll_vbox = QVBoxLayout(self._scroll_w)
        self._scroll_vbox.setContentsMargins(0, 2, 4, 2)
        self._scroll_vbox.setSpacing(0)
        self._scroll.setWidget(self._scroll_w)

        self._note_lbl = QLabel()
        self._note_lbl.setStyleSheet(
            f"color:{C_SUBTEXT}; font-size:15px; font-style:italic; padding:2px 4px;"
        )
        self._note_lbl.setWordWrap(True)

        root.addWidget(self._scroll, stretch=1)
        root.addWidget(self._note_lbl)

    # ── 내부 헬퍼 ──────────────────────────────────────────────────────
    def _clear_scroll(self):
        while self._scroll_vbox.count():
            item = self._scroll_vbox.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

    def _add_category(self, cat_name: str, cat_fields: list):
        hdr = QLabel(f"  {cat_name.upper()}")
        hdr.setStyleSheet(
            f"color:{C_ACCENT}; font-size:14px; font-weight:bold;"
            f" background:#1a2030; padding:3px 0px; margin-top:4px;"
        )
        self._scroll_vbox.addWidget(hdr)

        gw = QWidget()
        gl = QGridLayout(gw)
        gl.setContentsMargins(4, 2, 2, 4)
        gl.setHorizontalSpacing(8)
        gl.setVerticalSpacing(3)
        gl.setColumnStretch(1, 1)

        for r, (label, value) in enumerate(cat_fields):
            lbl_w = QLabel(f"{label}:")
            lbl_w.setStyleSheet(f"color:{C_SUBTEXT}; font-size:14px;")
            lbl_w.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            val_w = QLabel(str(value))
            val_w.setStyleSheet(f"color:{C_TEXT}; font-size:14px; font-weight:600;")
            val_w.setWordWrap(True)
            val_w.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            gl.addWidget(lbl_w, r, 0)
            gl.addWidget(val_w, r, 1)

        self._scroll_vbox.addWidget(gw)

    def clear(self):
        self._img_lbl.setPixmap(QPixmap())
        self._img_lbl.setText("")
        self._title_lbl.setText("← 왼쪽 목록에서 유닛을 선택하세요")
        self._sub_lbl.setText("")
        self._note_lbl.setText("")
        self._clear_scroll()

    def show_unit(self, name: str, db_entry: dict, spec: dict, unit_type: str = 'enemy'):
        """unit_type: 'enemy' | 'ship' | 'weapon'"""
        self._title_lbl.setText(name)

        # 사진 또는 아이콘 (.jpg → .png → .webp 순서로 탐색)
        _img_base = os.path.join(_res('assets/images'), name)
        img_path = next(
            (p for p in (_img_base + ext for ext in ('.jpg', '.png', '.webp'))
             if os.path.exists(p)),
            None
        )
        if img_path:
            pix = QPixmap(img_path).scaled(
                1200, 220,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self._img_lbl.setPixmap(pix)
            self._img_lbl.setText("")
        else:
            self._img_lbl.setPixmap(QPixmap())
            if unit_type == 'ship':
                icon = '⚓'
            elif unit_type == 'weapon':
                icon = '💥'
            else:
                typ = db_entry.get('type', '')
                icon = self._TYPE_ICON.get(typ, '❓')
            self._img_lbl.setText(icon)

        # 부제목
        origin    = spec.get('origin', '')
        type_desc = spec.get('type_desc', db_entry.get('type', ''))
        self._sub_lbl.setText(
            f"{origin}  |  {type_desc}" if (origin and type_desc) else (origin or type_desc)
        )

        # 카테고리 렌더링
        self._clear_scroll()
        categories = spec.get('categories', [])
        if categories:
            for cat_name, cat_fields in categories:
                self._add_category(cat_name, cat_fields)
        else:
            fields = spec.get('fields', [])
            if fields:
                self._add_category('제원', fields)
        self._scroll_vbox.addStretch()

        # 비고
        self._note_lbl.setText(spec.get('note', ''))


class SplashWindow(QWidget):
    """프로그램 진입 런처. [시뮬레이터 시작] → MainWindow 열기."""

    launch_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        from datetime import datetime
        _write_log(f'[{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}]  앱 시작')
        self.setWindowTitle("이지스 기동전단 통합 방어 시뮬레이터")
        self.setFixedSize(1400, 960)
        self.setStyleSheet(f"""
            QWidget {{ background: {C_BG}; color: {C_TEXT};
                       font-family: 'Malgun Gothic', 'Segoe UI'; font-size: 17px; }}
            QTabWidget::pane {{ border: 1px solid {C_BORDER}; background: {C_BG}; }}
            QTabBar::tab {{ background: {C_PANEL}; color: {C_SUBTEXT};
                            padding: 10px 26px; border: 1px solid {C_BORDER}; font-size: 16px; }}
            QTabBar::tab:selected {{ background: {C_BG}; color: {C_ACCENT};
                                     border-bottom: 2px solid {C_ACCENT}; }}
            QPushButton {{ background: {C_ACCENT}; color: white; border: none;
                           padding: 14px 36px; border-radius: 6px; font-size: 18px;
                           font-family: 'Malgun Gothic', 'Segoe UI', sans-serif; }}
            QPushButton:hover {{ background: #2980b9; }}
            QTableWidget {{ background: {C_PANEL}; gridline-color: {C_BORDER};
                            border: none; font-size: 16px; }}
            QHeaderView::section {{ background: {C_PANEL}; color: {C_ACCENT};
                                    border: none; padding: 8px; font-size: 16px; }}
        """)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(12)

        title = QLabel("⚓ 이지스 기동전단 통합 방어 시뮬레이터")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont('Malgun Gothic', 26, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {C_ACCENT}; padding: 8px;")
        layout.addWidget(title)

        sub = QLabel(f"{APP_VERSION}  |  PyQt6 네이티브 UI  |  한국 해군 이지스 기동전단 다층 방어 시뮬레이터")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet(f"color: {C_SUBTEXT}; font-size: 16px;")
        layout.addWidget(sub)

        tabs = QTabWidget()
        layout.addWidget(tabs, stretch=1)
        tabs.addTab(self._build_help_tab(),         "❓  도움말")
        tabs.addTab(self._build_feature_tab(),      "📋  탑재 기능")
        tabs.addTab(self._build_changelog_tab(),   "📝  패치 내역")
        tabs.addTab(self._build_plan_tab(),        "🗓️  향후 계획")
        tabs.addTab(self._build_enemy_db_tab(),    "🔴  적군 DB")
        tabs.addTab(self._build_friendly_db_tab(), "🔵  아군 DB")

        # 최초 실행 시 도움말 탭(0); 이후엔 마지막 선택 탭 복원
        saved_tab = _load_app_state().get('splash_tab', 0)
        tabs.setCurrentIndex(saved_tab)
        tabs.currentChanged.connect(
            lambda idx: _save_app_state({**_load_app_state(), 'splash_tab': idx})
        )

        btn = QPushButton("🚀  시뮬레이터 시작")
        btn.setFixedHeight(46)
        btn.clicked.connect(self.launch_requested.emit)
        layout.addWidget(btn)

    # ── 도움말 / 튜토리얼 탭 ──────────────────────────────────────────────
    def _build_help_tab(self) -> QWidget:
        _GLOSSARY = [
            ("Pk (Kill Probability)",    "교전 1회에서 위협을 격추할 확률 (0~1). 값이 높을수록 방어 성능이 우수."),
            ("RCS (Radar Cross Section)", "레이더에 반사되는 등가 면적 (㎡). 값이 작을수록 탐지가 어려운 스텔스 표적."),
            ("CEP (Circular Error Probable)", "유도탄의 유도 오차 반경 (m). 값이 작을수록 정밀한 무기."),
            ("ECM (Electronic Counter Measures)", "전자 방해 장치. ECM 지수가 높을수록 아군 레이더·유도탄 Pk 감소."),
            ("몬테카를로 시뮬레이션",   "동일 조건을 수천~수만 회 반복해 확률 분포를 추정하는 기법."),
            ("CVaR (Conditional VaR)",   "최악 5% 시나리오의 평균 생존율. 극단 상황 대비 지표."),
            ("REQ (Requirements)",        "요구조건. 생존율·격추율 임계값을 충족하는지 판정."),
            ("SM-2 / SM-6",               "함대공 미사일. SM-2는 중거리, SM-6는 장거리 및 탄도미사일 요격 가능."),
            ("CIWS (근접 방어 체계)",     "최후 방어선. 20mm 기관포로 근거리 위협을 자동 요격."),
            ("SAM (함대공 미사일)",        "Surface-to-Air Missile. 함정에서 발사하는 대공 미사일."),
            ("이지스 (Aegis)",            "위상 배열 레이더 기반 통합 전투 체계. 동시 다수 표적 추적·교전 가능."),
            ("HGV (극초음속 활공체)",     "마하 5 이상으로 날아오는 활공 탄도체. 기동성이 높아 요격이 매우 어려움."),
            ("교전 음영구역",             "레이더 사각지대 또는 최소 교전 거리 이내의 구역."),
            ("파고 / 해상 상태",          "Sea State 0~6. 파고가 높을수록 센서·무기 명중률 저하."),
        ]

        _STEPS = [
            ("1", "시뮬레이터 시작", "이 창 하단의 [🚀 시뮬레이터 시작] 버튼을 클릭합니다."),
            ("2", "아군 함정 선택",   "좌측 패널 상단에서 단독함 또는 편대 프리셋을 선택합니다."),
            ("3", "위협 설정",        "적군 위협 종류, 공격 수, 파고·날씨 조건을 설정합니다."),
            ("4", "반복 횟수 설정",   "몬테카를로 반복 횟수를 설정합니다. (빠른 확인 1,000 / 표준 10,000 / 정밀 100,000)"),
            ("5", "시뮬레이션 실행",  "[▶ 시뮬레이션 실행] 버튼을 클릭하고 진행 바를 기다립니다."),
            ("6", "결과 확인",        "결과 탭에서 격추율, 생존율, REQ 충족 여부, CVaR 등을 확인합니다."),
            ("7", "보고서 내보내기",  "결과 탭 하단 버튼으로 Excel(.xlsx) 또는 PNG 보고서를 저장합니다."),
            ("8", "실행 기록 재사용", "실행 기록 탭에서 이전 시뮬레이션 설정을 불러와 재실행할 수 있습니다."),
        ]

        _FAQ = [
            ("몬테카를로 횟수를 얼마로 설정해야 하나요?",
             "빠른 확인 1,000회 · 표준 분석 10,000회 · 정밀 분석 100,000회를 권장합니다.\n"
             "횟수가 많을수록 결과가 안정적이나 시간이 오래 걸립니다."),
            ("Pk가 0으로 나옵니다. 왜인가요?",
             "선택한 무기의 사거리 밖이거나 RCS가 너무 작아 탐지 자체가 불가능한 경우입니다.\n"
             "위협의 접근 거리와 해당 무기의 최대 사거리를 비교해 보세요."),
            ("REQ가 빨간색(미달)으로 표시됩니다.",
             "격추율 또는 생존율이 요구조건 임계값 미만입니다.\n"
             "함정 수를 늘리거나 SM-6 등 장거리 무기 탑재 수를 늘려 보세요."),
            ("엑셀 보고서는 어디에 저장되나요?",
             "실행 파일(또는 launcher.py)과 같은 폴더에 자동 저장됩니다.\n"
             "파일명에 날짜·시각이 포함되므로 여러 번 실행해도 덮어쓰이지 않습니다."),
            ("애니메이션이 느리게 재생됩니다.",
             "반복 횟수를 줄이거나, 애니메이션 탭에서 [속도] 슬라이더를 조정하세요.\n"
             "고성능 PC에서도 100,000회 이상의 애니메이션은 부드럽지 않을 수 있습니다."),
            ("편대 모드와 단독함 모드의 차이는 무엇인가요?",
             "단독함 모드는 이지스함 1척의 방어 성능을 분석합니다.\n"
             "편대 모드는 이지스함 + 호위함 등 다중 함정이 협력해 방어하는 시나리오를 시뮬레이션합니다."),
        ]

        w = QWidget()
        outer = QVBoxLayout(w)
        outer.setContentsMargins(8, 8, 8, 8)

        inner_tabs = QTabWidget()
        outer.addWidget(inner_tabs)

        # ── 용어 설명 탭
        gw = QWidget()
        gl = QVBoxLayout(gw)
        gl.setContentsMargins(4, 4, 4, 4)
        gtbl = QTableWidget(len(_GLOSSARY), 2)
        gtbl.setHorizontalHeaderLabels(["용어", "설명"])
        gtbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        gtbl.setColumnWidth(0, 240)
        gtbl.setWordWrap(True)
        gtbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        gtbl.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        gtbl.verticalHeader().setVisible(False)
        gtbl.setAlternatingRowColors(True)
        gtbl.setStyleSheet(
            f"alternate-background-color: {C_PANEL}; background-color: {C_BG};")
        for r, (term, desc) in enumerate(_GLOSSARY):
            ti = QTableWidgetItem(term)
            ti.setForeground(QColor(C_ACCENT))
            di = QTableWidgetItem(desc)
            di.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            gtbl.setItem(r, 0, ti)
            gtbl.setItem(r, 1, di)
        gtbl.verticalHeader().setDefaultSectionSize(52)
        gl.addWidget(gtbl)
        inner_tabs.addTab(gw, "📖  용어 설명")

        # ── 실행 순서 탭
        sw = QWidget()
        sl = QVBoxLayout(sw)
        sl.setContentsMargins(4, 4, 4, 4)
        stbl = QTableWidget(len(_STEPS), 3)
        stbl.setHorizontalHeaderLabels(["단계", "항목", "안내"])
        stbl.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        stbl.setColumnWidth(0, 50)
        stbl.setColumnWidth(1, 160)
        stbl.setWordWrap(True)
        stbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        stbl.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        stbl.verticalHeader().setVisible(False)
        stbl.setAlternatingRowColors(True)
        stbl.setStyleSheet(
            f"alternate-background-color: {C_PANEL}; background-color: {C_BG};")
        for r, (step, title, desc) in enumerate(_STEPS):
            si = QTableWidgetItem(step)
            si.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            si.setForeground(QColor(C_ORANGE))
            ti = QTableWidgetItem(title)
            ti.setForeground(QColor(C_ACCENT))
            di = QTableWidgetItem(desc)
            di.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            stbl.setItem(r, 0, si)
            stbl.setItem(r, 1, ti)
            stbl.setItem(r, 2, di)
        stbl.verticalHeader().setDefaultSectionSize(52)
        sl.addWidget(stbl)
        inner_tabs.addTab(sw, "🗺️  실행 순서")

        # ── FAQ 탭
        fw = QWidget()
        fl = QVBoxLayout(fw)
        fl.setContentsMargins(4, 4, 4, 4)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(f"QScrollArea {{ border: none; background: {C_BG}; }}")
        faq_w = QWidget()
        faq_l = QVBoxLayout(faq_w)
        faq_l.setContentsMargins(8, 8, 8, 8)
        faq_l.setSpacing(10)
        for q, a in _FAQ:
            q_lbl = QLabel(f"Q.  {q}")
            q_lbl.setWordWrap(True)
            q_lbl.setStyleSheet(
                f"color: {C_ACCENT}; font-weight: bold; font-size: 15px; "
                f"padding: 6px 8px; background: {C_PANEL}; border-radius: 4px;")
            a_lbl = QLabel(a)
            a_lbl.setWordWrap(True)
            a_lbl.setStyleSheet(
                f"color: {C_TEXT}; font-size: 14px; padding: 4px 14px 10px 14px;")
            faq_l.addWidget(q_lbl)
            faq_l.addWidget(a_lbl)
        faq_l.addStretch()
        scroll.setWidget(faq_w)
        fl.addWidget(scroll)
        inner_tabs.addTab(fw, "❓  FAQ")

        return w

    # ─────────────────────────────────────────────────────────────────────────
    def _build_feature_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        tbl = QTableWidget(len(_FEATURES), 2)
        tbl.setHorizontalHeaderLabels(["탭 / 기능", "설명"])
        tbl.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        tbl.setColumnWidth(0, 280)
        tbl.setWordWrap(True)
        tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tbl.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        tbl.verticalHeader().setVisible(False)
        tbl.setAlternatingRowColors(True)
        tbl.setStyleSheet(
            f"alternate-background-color: {C_PANEL}; background-color: {C_BG};")
        for row, (name, desc) in enumerate(_FEATURES):
            ni = QTableWidgetItem(name)
            ni.setForeground(QColor(C_ACCENT))
            desc_item = QTableWidgetItem(desc)
            desc_item.setTextAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            _apply_term_tooltip(ni, name + ' ' + desc)
            _apply_term_tooltip(desc_item, desc)
            tbl.setItem(row, 0, ni)
            tbl.setItem(row, 1, desc_item)
        tbl.verticalHeader().setDefaultSectionSize(68)
        layout.addWidget(tbl)
        return w

    def _build_changelog_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        changelog = []
        cl_path = _res('changelog.json')
        if os.path.exists(cl_path):
            try:
                with open(cl_path, encoding='utf-8-sig') as f:
                    changelog = json.load(f)
            except Exception:
                pass
        if not changelog:
            layout.addWidget(QLabel("changelog.json 없음"))
            return w
        # 최신 버전이 위로 오도록 역순 표시(changelog.json은 오래된→최신 순 저장)
        latest_ver = changelog[-1].get('version', '') if changelog else ''
        changelog = list(reversed(changelog))

        tbl = QTableWidget()
        tbl.setColumnCount(2)
        tbl.setHorizontalHeaderLabels(["버전", "변경 내용"])
        hh = tbl.horizontalHeader()
        hh.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        tbl.setColumnWidth(0, 110)
        tbl.verticalHeader().setDefaultSectionSize(30)
        tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tbl.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        tbl.verticalHeader().setVisible(False)
        tbl.setShowGrid(False)
        tbl.setStyleSheet(f"background-color: {C_BG}; gridline-color: {C_PANEL};")

        prev_date = None
        for entry in changelog:
            ver   = entry.get('version', '')
            date  = entry.get('date', '')
            items = entry.get('changes', [])
            is_latest = (ver == latest_ver)
            if date != prev_date:
                # 날짜 그룹 헤더 행
                row = tbl.rowCount()
                tbl.insertRow(row)
                tbl.setRowHeight(row, 32)
                date_item = QTableWidgetItem(f"  {date}")
                date_item.setBackground(QColor(C_PANEL))
                date_item.setForeground(QColor(C_SUBTEXT))
                f = date_item.font(); f.setBold(True); date_item.setFont(f)
                tbl.setItem(row, 0, date_item)
                tbl.setItem(row, 1, QTableWidgetItem(""))
                tbl.item(row, 1).setBackground(QColor(C_PANEL))
                tbl.setSpan(row, 0, 1, 2)
                prev_date = date
            for i, item in enumerate(items):
                row = tbl.rowCount()
                tbl.insertRow(row)
                tbl.setRowHeight(row, 34)
                # 버전 셀 (그룹 첫 행에만 표기, 최신은 ⭐ 강조)
                if i == 0:
                    label = f"⭐ {ver}" if is_latest else ver
                    vi = QTableWidgetItem(label)
                    vi.setForeground(QColor(C_ORANGE if is_latest else C_ACCENT))
                    if is_latest:
                        f = vi.font(); f.setBold(True); vi.setFont(f)
                        vi.setBackground(QColor('#3a2e0a'))  # 주황 틴트 배경
                    vi.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    tbl.setItem(row, 0, vi)
                else:
                    vi = QTableWidgetItem("")
                    if is_latest:
                        vi.setBackground(QColor('#3a2e0a'))
                    tbl.setItem(row, 0, vi)
                # 변경 내용 셀 — 유형 배지 + 본문
                tbl.setCellWidget(row, 1, self._make_change_cell(item))
        layout.addWidget(tbl)
        return w

    @staticmethod
    def _make_change_cell(item: str) -> QWidget:
        """변경 항목 문자열을 '유형 배지 + 본문' 셀 위젯으로 변환."""
        s = str(item).strip()
        kind, color = None, None
        for k, c in (("추가", C_GREEN), ("수정", C_ORANGE), ("삭제", C_RED)):
            if s.startswith(k):
                kind, color, s = k, c, s[len(k):].strip()
                break
        cell = QWidget()
        cell.setStyleSheet(f"background-color: {C_BG};")
        lay = QHBoxLayout(cell)
        lay.setContentsMargins(8, 3, 8, 3)
        lay.setSpacing(9)
        if kind:
            badge = QLabel(kind)
            badge.setStyleSheet(
                f"background-color: {color}; color: #0d1117; "
                f"border-radius: 8px; padding: 1px 9px; font-weight: bold;"
            )
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setFixedHeight(20)
            lay.addWidget(badge)
        txt = QLabel(s)
        txt.setStyleSheet(f"color: {C_TEXT};")
        txt.setWordWrap(True)
        lay.addWidget(txt, 1)
        return cell

    def _build_plan_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        _PLANS = [
            # ── v10.x 완료 ───────────────────────────────────────────────────
            ("(완료)", "—", "v10.x 전체 완료 + 감사",
             "v10.1~v10.8 구현 완료 · 코드 감사(BUG-1~5) · 물리 모델 수치 수정(PHY-1~12). "
             "v10.13 버그 수정 · v10.14 SM-3/YJ-18/KF-21/FA-50/DC · "
             "v10.15 항모Pk·홍상어/해성-II/현무-3C·4/ESSM 단가."),
            ("📋 정책", "상시", "감사 체크포인트 (마이너 버전마다)",
             "모든 마이너 버전 빌드 직전, 변경 유형별 감사 1회: "
             "엔진/로직→코드감사(/code-review) · DB/수치→현실성 수치감사 · UI→회귀확인 · "
             "아키텍처전환→코드감사+로직트레이스 · 신기능→새 군사용어 사전 갱신. "
             "메이저 블록(v11·v12…) 완료 시 전체 회귀 MC + 누적 수치감사. (CLAUDE.md '감사 정책' 정본)"),
            # ── v11.x — 기반 정비 ─────────────────────────────────────────────
            # 기둥: 기준값 확정 → UI 구조 확정 → MC 속도 확보
            ("v11.2", "—", "차기 계획 수립 (완료)",
             "로드맵 상세 문서로 대체 완료 — 48개 항목을 구현·군사·범위 3가지로 검토. "
             "난이도 보정 9건·군사 교정 6건·재배치 4건 반영."),
            ("v11.3", "상시", "설정 패널 구조 유지",
             "기본/환경/방어전술/항공자산/고급 5개 묶음 분리는 완료. "
             "신규 기능 추가 시 반드시 이 5개 묶음 중 적합한 곳에 배치. "
             "묶음 간 경계가 모호해지면 재조정."),
            # ── v12.x — 물리 엔진 고도화 ──────────────────────────────────────
            ("v12.1", "매우 높음", "실제 유도 알고리즘 (PNG)",
             "즉시 명중 판정 → 비례항법(PNG)으로 미사일이 실제 표적을 추격. "
             "회피 기동이 물리적으로 반영됨. 최소 적용은 종말 10km 이내부터. "
             "【현실성】미사일 기동 한계(함대공 ~30G·대함미사일 ~10G)와 탐색기 시야각 반영 필수(무한 기동 방지). "
             "교전 결과 전면 재조정 동반."),
            ("v12.2", "매우 높음", "수중 음향 전파 모델 고도화",
             "수온약층 계수·해역별 보정은 완료. 미구현 구간만 추가: "
             "전달손실(TL) 룩업 고도화·주변소음(ambient noise)·표적강도(TS) 기반 탐지 확률 모델. "
             "【현실성】수렴지대는 동해(수심 1000m+)만 가능, 서해(평균 44m)는 물리적 불가 — 코드에 반영됨."),
            ("v12.3", "매우 높음", "함정 생존 모델 (침수·복원력)",
             "현재 정적 피해 → 침수 속도·복원력·격실 침수 시뮬. "
             "피격 위치(수선 위/아래)·함종별 격실 반영. 침몰 예상 시간 실시간 표시. "
             "【현실성】격실 배치는 기밀이라 추정 모델 — 과도한 정밀 주장 금지."),
            ("v12.4", "중간", "동적 기상 변화",
             "교전 중 태풍 접근·날씨 시간 변화. 기상청 계절 패턴 기반 확률적 전이. "
             "탐지·교전 능력 실시간 변동. 작전급(72시간)에서 진가, 전술급(700초)엔 효과 작음."),
            ("v12.5", "중간", "피아식별 오류 (IFF)",
             "피아식별 실패 확률. 식별 지연·오인식으로 아군 오사 가능. "
             "혼잡 전장에서 교전규칙 이행 지연. 다방위·혼잡 시나리오와 시너지."),
            ("v12.6", "매우 높음", "엔진 numpy 전면 재설계",
             "v12.x 물리 완성 후 객체 루프 → numpy 배열 연산으로 전환. "
             "위치·속도·거리를 numpy 배열로 일괄 계산 → 30~50배 추가 향상 목표. "
             "v12 기준값 대비 결과 오차 5% 이내 검증 필수. "
             "v14.x AI 학습 데이터 생성·v17.x 캠페인 엔진의 고속 연산 토대."),
            # ── v13.x — 시각화 & 인터페이스 ──────────────────────────────────
            ("v13.1", "매우 높음", "3D 전장 + 실제 지도",
             "실제 수심·지형 데이터 기반 3D 전장 표시. 레이더 커버리지·미사일 궤적 입체 표현. "
             "실제 좌표계와 직결. 최소 적용은 2.5D 지도 오버레이부터(3D는 비용 대비 효용 낮음). "
             "【현실성】레이더 커버리지는 수평선·지형 차폐로 비대칭."),
            ("v13.2", "중간", "지휘통신망 시각화 (C4ISR)",
             "함정·항공·지상 데이터링크 연결 상태를 그래프로 표시. "
             "함정 격침 시 연결 자동 단절·협동 교전 변화 시각화. "
             "어느 함정 먼저 격침 시 방어망 붕괴하는지 취약점 분석."),
            ("v13.3", "낮음", "실시간 전황 지표판",
             "기본 통계(요격률·비용·손상)는 결과 탭에 구현됨. 추가 구간: "
             "탄약 소모 효율·비용당 격침 비율·피아 교환비·방어 포화도 등 상세 지표 확장. "
             "전술 의사결정 모드와 직결 — 무기 교체 판단 근거 즉시 제공."),
            ("v13.4", "중간", "위성 정찰 재방문 주기",
             "정찰위성 재방문 주기(12~24시간) 시뮬. 위성 창 열릴 때만 수평선 너머 표적 지정 가능. "
             "공백 시간엔 기습 기회. 작전급에서 진가. "
             "【현실성】촬영→해석→전송 지연 반영 필수."),
            # ── v14.x — AI & 자율화 ────────────────────────────────────────────
            ("v14.1", "매우 높음", "적응형 전술 AI",
             "적 지휘관이 상황을 분석해 전술을 실시간 전환하는 AI(몬테카를로 트리탐색). "
             "포화공격 → 분산접근 → 기만 순으로 적응. 난이도로 AI 사고 깊이 조정. "
             "【현실성】완벽한 적은 비현실 → 규칙기반 적응 AI부터 시작 권장."),
            ("v14.2", "높음", "학습 기반 즉시 예측",
             "과거 분석 결과를 학습한 예측 모델. 설정 바꾸는 즉시 요격률·피해를 추정(몬테카를로 없이). "
             "작전급 캠페인의 핵심 부품(교전을 즉시 계산해 72시간을 수초로). "
             "【현실성】학습 범위 밖은 부정확 — 빠른 1차 추정용."),
            ("v14.3", "높음", "함정별 자율 교전 AI",
             "각 함정이 독립 판단하는 AI. 협동 교전망·지령 없이도 자율 탐지·사격. "
             "기함 격침 시 차순위 함정이 지휘권 인수. 자율화 수준(반자동~완전자율) 조정."),
            ("v14.4", "매우 높음", "적 무인기 군집 (Swarm)",
             "무인기·무인수상정·무인잠수정 수십~수백 대가 분산 경로로 동시 접근. "
             "개별 요격 필요 → 탄약 급소모. 군집 비행 알고리즘 기반. "
             "최소 적용은 수십 대부터. 레이저 방어와 짝."),
            ("v14.5", "매우 높음", "아군 정찰 드론 편대",
             "고정익 무인정찰기 편대 배치. 탐지 범위 확장 + 수평선 너머 표적 유도 정보 제공. "
             "드론 개별 피격·격추. 배치 비용 vs 탐지 이득 트레이드오프."),
            ("v14.6", "높음", "무인 수상/수중정 (USV·UUV)",
             "무인 수상정(USV)·무인 잠수정(UUV)을 정찰·기뢰 탐색·자율 교전에 투입. "
             "유인 함정과 협동 운용(MUM-T), 통신 두절 시 자율 모드 전환. "
             "v14.4가 적 무인군집이라면 이쪽은 아군 무인 자산 — 후속 기뢰전·항만 방어의 기반."),
            # ── v15.x — 전장 도메인 확장 ──────────────────────────────────────
            ("v15.1", "높음", "전자전 고도화 + 역탐지",
             "ECM 재밍은 구현됨. 미구현 구간만 추가: "
             "전자지원(ESM) 역탐지 — 적이 아군 레이더 신호를 수집해 대방사미사일(ARM) 역방향 발사. "
             "주파수 대역별 전자방해·기만기 연동. "
             "【현실성】레이더 방사 = 위치 노출이 현대 해전 핵심 딜레마."),
            ("v15.3", "중간", "사이버전 모듈",
             "적 사이버 공격으로 데이터링크 변조→함정 오발사, 전투정보실 마비→탐지 지연. "
             "아군 반격으로 적 레이더 교란. "
             "기존 전자전·협동 교전 두절과 차별점은 지속성·은밀성."),
            ("v15.4", "높음", "분산 해양작전 (DMO)",
             "소형 함정 분산 배치 + 개별 타격으로 집중 방어 회피(미 해군 분산치사 교리). "
             "【현실성】미 해군 원형 ≠ 한국 소형함 위주 → 한국형으로 재해석 필요."),
            ("v15.5", "높음", "해안 방어 시설 통합 (C-RAM)",
             "육상 근접방어무기·해안 미사일 포대 고정 배치. 연안 접근 미사일·드론 대응. "
             "기뢰 차단 구역 설정. 인천·부산·동해 항만 방어. 지형(v13.1) 연동 시 가치 배가."),
            ("v15.6", "중간", "전자 좌표 기만",
             "함정 전자방해 강화 시 적 레이더 화면상 표시 위치가 실제와 어긋남. "
             "적 미사일이 가짜 좌표로 유도 → 명중률 저하. "
             "기존 탐지거리 감소 전자방해와 별개인 위치 기만 수단."),
            ("v15.7", "높음", "기뢰전 (MIW)",
             "기뢰 부설·소해 작전 모델. 계류기뢰·해저기뢰·자항기뢰 3종, 소해함·UUV 소해 운용. "
             "협수로·항만 입구 기뢰원 설정과 안전 항로 개척. "
             "v15.5의 '기뢰 차단 구역'을 정식 기뢰 모델로 구체화 — 적 기뢰 위협이 기동을 제약."),
            ("v15.8", "중간", "항만·기지 방어 시나리오",
             "해군기지·항만 거점 방어. 적 침투정·자폭 보트(USV)·기뢰 복합 위협에 대응. "
             "기지별 고정 방어 자산·근접 방어망·경계 운용. "
             "v15.5(해안 고정 화력)와 달리 거점 방어 '상황' 시나리오 — 무인정·기뢰전 위협을 통합."),
            # ── v16.x — 군수·미래 전장 ────────────────────────────────────────
            ("v16.1", "중간", "보급·병참 지속성",
             "탄약·연료·보급품 지속성 모델. 군수지원함 보급 주기, 재고 고갈 시 작전 제약. "
             "전술~작전 경계의 군수 — v17.2 캠페인 재보급의 전술급 선행(중복 없이 연계)."),
            ("v16.2", "높음", "지향성 에너지 무기 (레이저)",
             "함정 레이저(60kW급)·고출력 마이크로파. 전력 한도 내에서만 연속 발사. "
             "【현실성】60kW는 드론·소형보트 한정. 초음속 탄두(현무-4급) 무력화는 메가와트급 필요 → 대상 제한 필수. "
             "적 무인기 군집(v14.4) 대응이 주 용도."),
            # ── v17.x — 작전급 시뮬레이터 ─────────────────────────────────────
            # 선행 필수: v11.4(분석속도) · v14.2(즉시예측)
            ("v17.1", "매우 높음", "캠페인 엔진 기반 설계",
             "며칠 단위 전역(캠페인)을 다루는 작전급 엔진. 1시간 단위로 진행, 72시간 캠페인이 수초 내 완료. "
             "교전이 발생할 때만 기존 전술 엔진을 불러 처리하고, 나머지는 즉시예측(v14.2)으로 빠르게 계산. "
             "전술 엔진과 분리된 별도 엔진."),
            ("v17.2", "높음", "전력 관리 모델",
             "전 함정 상태 추적: 출항·초계·귀항·수리대기·수리중·재편성. "
             "손상 함정 수리 기간(피해 심각도별 1~14일), 탄약 재보급 시간. "
             "보급함 이동·미사일 재장전·연료 소모 등 군수·보급 모델 포함. "
             "가용 전력 = 전체 − 수리중 − 귀항중."),
            ("v17.3", "높음", "임무 배정 시스템",
             "가용 전력을 여러 임무에 자동 배정: 초계·호위·타격·대잠·보급 호위. "
             "우선순위 기반 배정(이지스급 → 고위협 구역 우선), 임무 충돌 해결. "
             "최소 적용은 단순 우선순위 배정부터, 이후 전술 AI(v14.1)로 교체 가능."),
            ("v17.4", "높음", "정보 불확실성 모델 (전장의 안개)",
             "적 위치를 '확실'이 아닌 확률 범위로 관리. 위성·초계기 탐지 때마다 정보 갱신. "
             "오래된 정보일수록 위치 불확실성 반경 확대. 작전의 본질인 '적이 어디 있는지 모름' 반영. "
             "임무 배정 시 위험도로 환산."),
            ("v17.5", "중간", "해상 교통로 통제 (SLOC)",
             "한반도 주요 해상 교통로 3개(서해·대한해협·동해) 통제 상태 시뮬. "
             "적 해역 진입 → 교통로 위협도 상승 → 보급 감소 → 작전 지속 능력 하락. "
             "에너지·무역 99% 해상의존인 한국에 핵심. 캠페인 승패 판정 기준."),
            ("v17.6", "중간", "캠페인 반복 분석",
             "캠페인 전체를 여러 번 반복해 전역 결과 통계. "
             "72시간 후 잔존 전력 분포·교통로 통제 성공률·전역 비용·민감도 분석. "
             "개별 교전은 즉시예측(v14.2)으로 대체 → 1,000회 캠페인이 수분 내 완료."),
            ("v17.7", "낮음", "캠페인 보고서 & 시각화",
             "전역 타임라인: 시각별 전력 상태·임무 현황·교통로 변화 그래프. "
             "결정적 순간(전력 30% 이하, 교통로 차단) 자동 표시. "
             "3D 지도(v13.1)에 캠페인 경로 표시. 보고서 자동 생성."),
            # ── v18.x — 공군 작전급 ────────────────────────────────────────────
            # 선행 필수: v17 완성
            ("v18.1", "높음", "공군 전력 & 임무 모델",
             "한국·미국 공군 전력: KF-21·F-35A·F-15K·F-16·B-1B·B-52 등. "
             "임무 유형: 제공권 장악(CAP)·근접항공지원(CAS)·방공망 제압(SEAD)·전략폭격·정찰. "
             "작전급 전력 관리 구조를 공군용으로 확장."),
            ("v18.2", "높음", "제공권 통제 모델",
             "공중 우세 구역을 한반도 격자 지도로 시뮬. 아군 제공권 출격 밀도·적 방공망 강도로 통제 확률 계산. "
             "제공권 상실 시 해군 작전에 패널티 연동. 1시간 단위 제공권 지도 갱신."),
            ("v18.3", "높음", "방공망 제압 (SEAD/DEAD)",
             "적 방공망(SA-21·HHQ-9·S-400) 탐지·타격. 성공 시 해군 작전 구역 확대, 실패 시 함대공 수요 증가. "
             "방공망 복구 6~48시간. 해군 전자전(v15.1)과 연동. "
             "【현실성】타격 효과 평가는 역사적으로 과대평가 경향 → 보수적 계수."),
            ("v18.4", "높음", "전략 폭격 & 적 기지 타격",
             "B-1B·KF-21·현무-3C 합동으로 적 항구·비행장·레이더 타격. "
             "성공 시 적 해군 출항 능력 저하 → 해상 교통로 위협 감소. 적 재건 시간 모델. "
             "타격 효과가 캠페인 전체에 누적 반영."),
            ("v18.5", "중간", "공군 작전 캠페인 통합",
             "해군 캠페인 엔진에 공군 임무 추가. 해상 교통로 위협 상승 시 공군 근접지원·방공망제압 자동 요청. "
             "해군·공군 자산 통합 배정. 캠페인 보고서에 공군 임무 타임라인 추가."),
            ("v18.6", "높음", "다전장 연동 (공군·지상 합동 교전구역)",
             "공군 SEAD·지상 패트리엇/THAAD를 해군 캠페인 엔진과 연동. 합동 교전규칙 구역 자동 분할. "
             "v18.5 공군 통합 완료 후 지상 방공망(v19.2)과 연결되는 다전장 교전 구역 확정."),
            # ── v19.x — 육군 작전급 ────────────────────────────────────────────
            # 선행 필수: v18 완성
            ("v19.1", "매우 높음", "지상군 전력 & 기동 모델",
             "육군 전력: K2 흑표·K21·K9 자주포·천무·패트리엇·사드. "
             "지형 기반 이동 속도·시야 계산. 상륙 → 내륙 진출 경로 모델링. "
             "【범위】전면 지상전은 해전 시뮬 본령 밖 → 상륙·연안 접점에 필요한 최소 단위만."),
            ("v19.2", "높음", "지상 방공망 모델",
             "패트리엇·천궁·사드·현무-II 지대지. 지상 방공망이 해군·공군 작전 구역에 영향. "
             "적 대함탄도탄(DF-21D 등) → 해상 교통로 위협 연동. "
             "지상 방공망 손실 시 제공권·해군 피해로 연쇄 — 해·공과 진짜 연결고리."),
            ("v19.3", "높음", "해상 상륙작전 지원",
             "상륙사단 → 독도함·상륙함 수송. 해군 함포 지원 + 공군 근접지원 + 육군 상륙 순서. "
             "교두보 확보 성공 여부 → 작전 목표 달성도. 각 단계 성공 확률을 순차 곱연산."),
            ("v19.4", "중간", "육군 작전 캠페인 통합",
             "해·공 캠페인 엔진에 육군 임무 추가. 지상전 전황 → 해상 교통로·제공권 상호 영향. "
             "지상 방공망 손실 → 제공권 → 해상 교통로 도미노 반영."),
            # ── v20.x — 육해공 통합 합동작전 ──────────────────────────────────
            # 선행 필수: v17·v18·v19 전체 완성
            ("v20.1", "매우 높음", "합동작전 사령부 (JCS)",
             "육해공군 자산을 통합 지휘. 자원 충돌 해결(전투기 1대를 제공권·근접지원·방공망제압 중 어디에?). "
             "합동 교전구역 자동 분할. "
             "【현실성】완전 자동최적화는 현실에 없음(각 군 자율성) → 조정·충돌경고 수준이 현실적."),
            ("v20.2", "높음", "합동 화력 지원",
             "해군 함포·토마호크 + 공군 폭격 + 육군 천무·현무가 동일 표적에 협조 타격. "
             "아군 오사 방지. 화력 효과 누적(첫 타격 손상 → 이후 타격 효과 보정). "
             "시차 공격·동시 공격 선택."),
            ("v20.3", "중간", "합동 작전 시나리오 라이브러리",
             "육해공 통합 시나리오 3종: 한반도 전면전 72시간 · 대만해협 위기 · 독도·이어도 제한전. "
             "각 시나리오: 각 군 초기 전력 + 작전 목표 + 성공 판정 기준. 순수 군사 교육·분석 목적."),
            ("v20.4", "중간", "합동작전 통합 보고서",
             "육해공 전 전력 캠페인 결과 통합. 군별 기여도 분석(해군이 교통로 방어에 얼마나 기여? 공군 방공망제압이 해군 손실을 얼마나 줄였나?). "
             "전역 비용·손실 대비 목표 달성률. 최적 전력 구성 추천."),
            # ── 선택 트랙 — v20 완료 후 별도 판단 ────────────────────────────
            ("선택", "매우 높음", "멀티플레이어 대전",
             "한 명은 이지스 함대, 다른 한 명은 적 항모전단을 실시간 지휘. "
             "네트워크 동기화·지연보상이 핵심 난관. "
             "단일 시뮬 완성도와 별개 트랙 — v20 완료 후 분석 목적 충족도에 따라 착수 여부 판단."),
        ]

        tbl = QTableWidget(len(_PLANS), 4)
        tbl.setHorizontalHeaderLabels(["버전", "난이도", "항목", "설명"])
        hh = tbl.horizontalHeader()
        hh.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        tbl.setColumnWidth(0, 55)
        tbl.setColumnWidth(1, 70)
        tbl.verticalHeader().setVisible(False)
        tbl.setWordWrap(True)
        tbl.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        tbl.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        tbl.setShowGrid(False)
        tbl.setStyleSheet(f"background-color: {C_BG}; gridline-color: {C_PANEL};")

        diff_color = {'매우 높음': '#c0392b', '높음': '#e74c3c', '중간': C_ORANGE, '낮음': '#2ecc71'}
        for r, (ver, diff, title, desc) in enumerate(_PLANS):
            vi = QTableWidgetItem(ver)
            vi.setForeground(QColor(C_ACCENT))
            vi.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            di = QTableWidgetItem(diff)
            di.setForeground(QColor(diff_color.get(diff, C_TEXT)))
            di.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            desc_item = QTableWidgetItem(f"  {desc}")
            desc_item.setTextAlignment(
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            title_item = QTableWidgetItem(f"  {title}")
            _apply_term_tooltip(title_item, title + ' ' + desc)
            _apply_term_tooltip(desc_item, desc)
            tbl.setItem(r, 0, vi)
            tbl.setItem(r, 1, di)
            tbl.setItem(r, 2, title_item)
            tbl.setItem(r, 3, desc_item)
        tbl.verticalHeader().setDefaultSectionSize(68)

        layout.addWidget(tbl)
        return w

    # ── DB 탭 공통 헬퍼 ──────────────────────────────────────────────────────
    # 카테고리별 배경/전경색
    _CAT_BG  = {'대공': '#2a1010', '대함': '#2a1a08', '대잠': '#0a1228'}
    _CAT_FG  = {'대공': '#ff8080', '대함': '#ffaa55', '대잠': '#6699ff'}
    _LIST_SS = f"""
        QListWidget {{
            background:{C_BG}; border:none; outline:none; font-size:13px;
        }}
        QListWidget::item {{
            padding:5px 10px; border-bottom:1px solid {C_BORDER};
        }}
        QListWidget::item:selected {{
            background:{C_ACCENT}; color:#000; font-weight:bold;
        }}
        QListWidget::item:hover:!selected {{ background:{C_PANEL}; }}
    """

    def _make_list_panel(self, entries: list, mode: str,
                         cat_color: bool = False,
                         display_key: str | None = None,
                         tooltip_fn=None) -> tuple:
        """
        왼쪽 QListWidget + 오른쪽 SpecSheetPanel QSplitter를 생성해 반환.
        entries: [(key, info), ...]
        mode: 'enemy' | 'weapon' | 'ship' | 'aircraft'
        cat_color: True면 category 필드 기반 행 색상 적용
        display_key: info 안에서 표시 이름으로 쓸 키 (None이면 항목 key 사용)
        """
        name_list = QListWidget()
        name_list.setStyleSheet(self._LIST_SS)

        for key, info in entries:
            label = info.get(display_key, key) if display_key else key
            it = QListWidgetItem(f"  {label}")
            if cat_color:
                cats = info.get('category', '대공')
                # FRIENDLY_DB는 리스트, ENEMY_DB는 문자열
                c = cats[0] if isinstance(cats, list) else cats
                it.setBackground(QColor(self._CAT_BG.get(c, C_BG)))
                it.setForeground(QColor(self._CAT_FG.get(c, C_TEXT)))
            else:
                it.setForeground(QColor(C_ACCENT))
            if tooltip_fn:
                it.setToolTip(tooltip_fn(key, info))
            name_list.addItem(it)

        spec_panel = SpecSheetPanel()
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setStyleSheet(
            "QSplitter::handle { background: " + C_BORDER + "; width: 2px; }")
        splitter.addWidget(name_list)
        splitter.addWidget(spec_panel)
        splitter.setSizes([230, 9999])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        def _on_select(row):
            if row < 0 or row >= len(entries):
                spec_panel.clear()
                return
            k, e = entries[row]
            spec_panel.show_unit(k, e, _SPEC_DETAIL_DB.get(k, {}), mode)

        name_list.currentRowChanged.connect(_on_select)
        return splitter, name_list, spec_panel

    def _wrap_splitter(self, splitter) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(4)
        lay.addWidget(splitter, stretch=1)
        return w

    # ── 적군 DB 탭 ─────────────────────────────────────────────────────────
    def _build_enemy_db_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        if not _V7_OK:
            layout.addWidget(QLabel("엔진 로드 실패 — 적군 DB를 표시할 수 없습니다."))
            return w

        _normalize_enemy_db()
        db = V7_ENEMY_DB

        # 유형별 분류
        _AIRCRAFT_T = {'전투기', '폭격기', '전폭기'}
        _SHIP_T     = {'고속정', '초계함', '호위함', '구축함', '항모', '순양함', '상륙함'}
        _MISSILE_T  = {'순항미사일', '탄도미사일', '극초음속활공체', '저고도기동탄도', '대방사미사일'}
        _SUB_T      = {'잠수함'}

        def _split(types):
            return [(k, v) for k, v in db.items() if v.get('type','') in types]

        aircraft_e = _split(_AIRCRAFT_T)
        ship_e     = _split(_SHIP_T)
        missile_e  = _split(_MISSILE_T)
        sub_e      = _split(_SUB_T)

        inner_tabs = QTabWidget()
        inner_tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border:none; }}
            QTabBar::tab {{ background:{C_PANEL}; color:{C_TEXT}; padding:4px 14px; }}
            QTabBar::tab:selected {{ background:{C_ACCENT}; color:#000; }}
        """)

        # ── 전투기 탭 ─────────────────────────────────────────────────────
        sp, _, _ = self._make_list_panel(aircraft_e, 'enemy', cat_color=False)
        inner_tabs.addTab(self._wrap_splitter(sp), f"✈  전투기  ({len(aircraft_e)})")

        # ── 함정 탭 ───────────────────────────────────────────────────────
        sp, _, _ = self._make_list_panel(ship_e, 'enemy', cat_color=False)
        inner_tabs.addTab(self._wrap_splitter(sp), f"⚓  함정  ({len(ship_e)})")

        # ── 무기 탭 (카테고리 색상) ────────────────────────────────────────
        sp, nl, _ = self._make_list_panel(missile_e, 'enemy', cat_color=True)
        # 범례 행 추가
        legend = QHBoxLayout()
        legend.setSpacing(12)
        for cat, fg in self._CAT_FG.items():
            bg = self._CAT_BG[cat]
            lbl = QLabel(f"  {cat}  ")
            lbl.setStyleSheet(
                f"background:{bg}; color:{fg}; border-radius:3px;"
                f" font-size:11px; padding:1px 4px;")
            legend.addWidget(lbl)
        legend.addStretch()
        mw = QWidget()
        ml = QVBoxLayout(mw)
        ml.setContentsMargins(6, 6, 6, 6)
        ml.setSpacing(4)
        ml.addLayout(legend)
        ml.addWidget(sp, stretch=1)
        inner_tabs.addTab(mw, f"🚀  무기  ({len(missile_e)})")

        # ── 잠수함 탭 ─────────────────────────────────────────────────────
        sp, _, _ = self._make_list_panel(sub_e, 'enemy', cat_color=False)
        inner_tabs.addTab(self._wrap_splitter(sp), f"🤿  잠수함  ({len(sub_e)})")

        layout.addWidget(inner_tabs, stretch=1)

        pk_note = QLabel(
            "  ⚠  적 플랫폼별 Pk 수치는 공개 자료 기반 추정값입니다 (±15~20%). "
            "소수점 정밀도는 상대 비교를 위한 것이며 실측 데이터가 아닙니다.")
        pk_note.setStyleSheet(
            f"color:#e67e22; font-size:11px; padding:3px 4px;")
        pk_note.setWordWrap(True)
        layout.addWidget(pk_note)
        return w

    # ── 아군 DB 탭 ─────────────────────────────────────────────────────────
    def _build_friendly_db_tab(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        if not _V7_OK:
            layout.addWidget(QLabel("엔진 로드 실패 — 아군 DB를 표시할 수 없습니다."))
            return w

        inner_tabs = QTabWidget()
        inner_tabs.setStyleSheet(f"""
            QTabWidget::pane {{ border:none; }}
            QTabBar::tab {{ background:{C_PANEL}; color:{C_TEXT}; padding:4px 14px; }}
            QTabBar::tab:selected {{ background:{C_ACCENT}; color:#000; }}
        """)

        # 무기 DB (카테고리 색상)
        inner_tabs.addTab(self._build_weapon_sub_tab(), f"🚀  무기  ({len(V7_FRIENDLY_DB)})")

        # 함정 DB (잠수함 제외)
        surface_ships = [(k, v) for k, v in V7_SHIP_DB.items()
                         if not v.get('is_submarine', False)]
        inner_tabs.addTab(self._build_ship_sub_tab(surface_ships),
                          f"⚓  함정  ({len(surface_ships)})")

        # 잠수함 DB
        subs = [(k, v) for k, v in V7_SHIP_DB.items()
                if v.get('is_submarine', False)]
        inner_tabs.addTab(self._build_ship_sub_tab(subs),
                          f"🤿  잠수함  ({len(subs)})")

        # 항공 DB
        aircraft_e = list(V7_AIRCRAFT_DB.items())
        sp, _, _ = self._make_list_panel(aircraft_e, 'aircraft', cat_color=False)
        inner_tabs.addTab(self._wrap_splitter(sp),
                          f"🚁  항공  ({len(aircraft_e)})")

        layout.addWidget(inner_tabs, stretch=1)
        return w

    def _build_weapon_sub_tab(self) -> QWidget:
        wpn_entries = list(V7_FRIENDLY_DB.items())

        # 범례 행
        legend = QHBoxLayout()
        legend.setSpacing(12)
        for cat, fg in self._CAT_FG.items():
            bg = self._CAT_BG[cat]
            lbl = QLabel(f"  {cat}  ")
            lbl.setStyleSheet(
                f"background:{bg}; color:{fg}; border-radius:3px;"
                f" font-size:11px; padding:1px 4px;")
            legend.addWidget(lbl)
        legend.addStretch()

        sp, _, _ = self._make_list_panel(wpn_entries, 'weapon', cat_color=True)
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(4)
        lay.addLayout(legend)
        lay.addWidget(sp, stretch=1)
        pk_note = QLabel(
            "  ⚠  Pk 수치는 공개 자료 기반 추정값입니다 (±15~20%). 실측 데이터가 아닙니다.")
        pk_note.setStyleSheet(
            f"color:#e67e22; font-size:11px; padding:3px 4px;")
        lay.addWidget(pk_note)
        return w

    def _build_ship_sub_tab(self, ship_entries: list | None = None) -> QWidget:
        if ship_entries is None:
            ship_entries = list(V7_SHIP_DB.items())

        def _tip(key, info):
            display = info.get('display', key)
            inv = info.get('default_inventory', {})
            lines = [f"【{display} 기본 탑재】"]
            for wname, cnt in inv.items():
                lines.append(f"  • {wname}: {'무한' if cnt >= 9999 else cnt}발")
            return "\n".join(lines)

        # display 필드로 표시
        disp_entries = [(k, v) for k, v in ship_entries]
        name_list = QListWidget()
        name_list.setStyleSheet(self._LIST_SS)
        for key, info in disp_entries:
            display = info.get('display', key)
            it = QListWidgetItem(f"  {display}")
            it.setForeground(QColor(C_ACCENT))
            it.setToolTip(_tip(key, info))
            name_list.addItem(it)

        spec_panel = SpecSheetPanel()
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setStyleSheet(
            "QSplitter::handle { background: " + C_BORDER + "; width: 2px; }")
        splitter.addWidget(name_list)
        splitter.addWidget(spec_panel)
        splitter.setSizes([230, 9999])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        def _on_select(row):
            if row < 0 or row >= len(disp_entries):
                spec_panel.clear()
                return
            skey, sentry = disp_entries[row]
            spec_panel.show_unit(skey, sentry, _SPEC_DETAIL_DB.get(skey, {}), 'ship')

        name_list.currentRowChanged.connect(_on_select)
        return self._wrap_splitter(splitter)


# ════════════════════════════════════════════════════════════════════════════
#  진입점
# ════════════════════════════════════════════════════════════════════════════
def _install_crash_handler():
    """미처리 예외 발생 시 로그 기록 후 프로세스 강제 종료."""
    import traceback

    def _on_exception(exc_type, exc_value, exc_tb):
        if issubclass(exc_type, KeyboardInterrupt):
            os._exit(0)
        try:
            msg = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
            _write_log(f'[CRASH] {msg}')
        except Exception:
            pass
        os._exit(1)

    def _on_thread_exception(args):
        if args.exc_type is SystemExit:
            os._exit(0)
        _on_exception(args.exc_type, args.exc_value, args.exc_traceback)

    sys.excepthook = _on_exception
    threading.excepthook = _on_thread_exception


def main():
    global CHART_DPI
    _install_crash_handler()
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    # 화면 DPI 기반 차트 렌더 해상도 자동 설정
    screen = app.primaryScreen()
    if screen:
        px_w = int(screen.size().width() * screen.devicePixelRatio())
        # figsize 12인치 기준: 화면 너비 90%를 커버하는 DPI 계산
        CHART_DPI = max(150, min(300, px_w * 3 // 40))

    # 앱 아이콘 설정
    _icon_path = _res('aegis_icon.ico')
    if os.path.exists(_icon_path):
        from PyQt6.QtGui import QIcon
        app.setWindowIcon(QIcon(_icon_path))

    # 다크 팔레트 기본 적용
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window,        QColor(C_BG))
    palette.setColor(QPalette.ColorRole.WindowText,    QColor(C_TEXT))
    palette.setColor(QPalette.ColorRole.Base,          QColor(C_PANEL))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(C_BG))
    palette.setColor(QPalette.ColorRole.Text,          QColor(C_TEXT))
    palette.setColor(QPalette.ColorRole.Button,        QColor(C_PANEL))
    palette.setColor(QPalette.ColorRole.ButtonText,    QColor(C_TEXT))
    palette.setColor(QPalette.ColorRole.Highlight,     QColor(C_ACCENT))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor('#ffffff'))
    app.setPalette(palette)

    _main_win: list = []  # mutable closure

    def _launch():
        splash.close()
        win = MainWindow()
        _main_win.append(win)
        win.show()

    app.aboutToQuit.connect(_shutdown_global_pool)
    app.aboutToQuit.connect(_stop_sys_data_worker)

    _start_sys_data_worker()   # 블로킹 I/O 백그라운드 수집 시작

    splash = SplashWindow()
    splash.launch_requested.connect(_launch)
    splash.show()
    os._exit(app.exec())


if __name__ == '__main__':
    multiprocessing.freeze_support()   # PyInstaller exe 멀티프로세싱 필수
    # 글로벌 풀 백그라운드 예열 (스플래시 표시 중에 완료됨)
    threading.Thread(target=_init_global_pool, daemon=True).start()
    main()

