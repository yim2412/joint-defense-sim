# v16.6 전자 좌표 기만 (설계)

## 개념
아군 전자방해(ECM) 강화 시 적 레이더 화면상 함정 표시 위치가 실제와 어긋난다.
적 대함미사일이 **가짜 좌표로 종말 유도**되어 실제 함정과 이격된 채 돌입 → 명중률 저하.
기존 ECM(탐지거리 감소·Pk 30% 감소)과 **별개인 위치 기만** 수단(_PLANS v16.6).

## 핵심 — ARM 인프라 재활용
ARM은 이미 `arm_aim_pos`(stale/기만 조준 좌표)로 유도되고, `_check_hits`(engine_combat:4238)
에서 실제 표적과의 이격 `miss_d`만큼 Pk를 지수 감쇠(`pk_eff = pk_base * exp(-miss_d/SCALE)`)
한다. 전자 좌표 기만은 이 메커니즘을 **일반 레이더 유도 대함미사일로 일반화**한다.

## 구현
1. **MissileObj.decoy_aim_pos** 필드(`arm_aim_pos` 옆, 기본 None).
2. **update()**(884): 유도 좌표 우선순위 `arm_aim_pos > decoy_aim_pos > target.pos`.
   - `_aim = self.arm_aim_pos or self.decoy_aim_pos or self.target.pos`(None 체크).
3. **종말 기만 적용**(미사일 update 또는 종말 진입 훅): `enable_coord_deception` ON +
   표적 함정이 ECM 보유(AN/SLQ-32 등) + 레이더 유도 미사일(탄도/HGV/ARM/어뢰 제외) 일 때,
   표적 종말권(예: ≤ 15km) 진입 시 **확률적**(`coord_deception_rate`, 예 0.5)으로
   `decoy_aim_pos = target.pos + 기만 오프셋`(방위 랜덤·거리 `coord_deception_offset_m`, 예 250m).
   1회만 설정(이미 설정됐으면 유지).
4. **_check_hits**(4275 일반 대함 분기, ECM 30% 감소 블록 부근): `decoy_aim_pos`가 있으면
   ARM stale과 동형으로 이격 `miss_d = decoy_aim_pos.dist_to(tgt.pos)`만큼 Pk 추가 감쇠
   (`pk *= exp(-miss_d/_DECEPTION_SCALE_M)`). 큰 이격이면 명백히 빗나감 처리.
5. **app_main 3종세트**: 체크박스 "전자 좌표 기만 (실험적)" + cfg 빌드/로드. 기본 OFF.

## 적용 대상 / 제외
- 적용: 레이더 유도 대함미사일(순항·아음속·초음속 대함).
- 제외: 탄도·HGV(레이더 유도 아님·관성/GPS)·ARM(자체 stale 모델)·어뢰(음향). ECM 무효 항목과 동일.

## 하위호환 / 회귀
- 기본 OFF → `decoy_aim_pos` 항상 None → update `_aim` 기존과 동일·Pk 감쇠 미적용.
  **회귀 8×26 OFF bit-identical 필수**. 신규 `random` 호출은 ON 경로에만(OFF 시 RNG 불변).
- 플래그명 고정(`enable_coord_deception`·`coord_deception_rate`·`coord_deception_offset_m`).

## 검증 (전술 옵션 유형)
- 회귀 PASS(OFF bit-identical).
- ON/OFF MC: 레이더 유도 대함 위협(예: 랴오닝·전면전 포화) 상대 요격률·아군 피격 변화로
  기만 효과 입증(역효과 없음). 탄도/HGV 위협엔 무효 확인. 기준값 메모리.
- `/code-review medium`.

## 미결(구현 중 확정)
- `coord_deception_offset_m`(기만 이격)·`_DECEPTION_SCALE_M`(Pk 감쇠 스케일)·`coord_deception_rate`
  (성공률) — ON/OFF 측정으로 효과가 과하지 않게(난공불락化 방지) 튜닝.
- ECM 보유 판정: 전 함정 공통(AN/SLQ-32 가정) vs 특정 자산. 1차는 전 수상함 공통.
