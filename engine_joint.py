# -*- coding: utf-8 -*-
"""
engine_joint.py — 합동 화력 지원 층 (v21.2)

v18 해군 캠페인(engine_campaign) + v19 공군 층(engine_airforce) + v20 지상 층(engine_army)
위에 얹는 **합동 화력 층**. CampaignEngine이 `enable_joint_fires` ON일 때만 조합한다.

핵심 가치: **육해공 화력이 같은 표적(적 항구·비행장)을 협조 타격**한다.
  - 표적은 새로 만들지 않는다 — v19.4의 `EnemyBase`(출항분담·누적손상·재건)를 **공유**한다.
    지금까지 이 표적을 때리는 건 공군 전략폭격 **하나뿐**이었고, 해군 순항미사일·육군
    지대지 화력은 적 기지에 닿는 경로가 아예 없었다.
  - 협조의 이득은 두 가지: ①이미 반파된 표적에 화력을 낭비하지 않고 **잔여 표적으로 넘김**
    ②동시 타격으로 적 방공망을 분산.

아키텍처 규약(v19·v20 계승):
  - CampaignEngine이 이 모듈을 **조합**(compose)만 한다. 전술 엔진(engine_combat) 무수정.
  - `enable_joint_fires` OFF면 생성조차 안 됨 → v20 캠페인과 bit-identical.
    (표적 소유권도 OFF면 AirCampaign이 그대로 자기 것을 갖는다 — `bases=None` 기본인자)
  - **결정론**: rng 미사용. v19.3 SEAD·v19.4 전략폭격과 동형(보수적 BDA 계수).

⚠ 짝 기능 — `enable_strategic_strike`가 OFF면 `EnemyBase`가 **아예 존재하지 않아** 합동
화력은 **원리상 발동 0**이다. 표적이 없는데 화력만 켜는 건 의미가 없다. UI 툴팁·효과
프로브 모두에 이 짝을 명시한다([[project-dead-feature-prevention]] — "토글 켰는데 변화 0"의
원인은 거의 다 짝 기능이 꺼져 있어서였다).

정본 = plan_v21_joint.md.
"""
from __future__ import annotations

# ⚠ engine_combat(FRIENDLY_STRIKE_DB)은 **최상위에서 import하지 않는다** — engine_campaign이
# 이 모듈을 최상위 import하므로, 여기서 engine_combat(8586줄)을 끌어오면 캠페인이 전술
# 엔진을 지연 import(engine_campaign._resolve_precise)하는 설계가 무력화된다. 대리모델만
# 쓰는 캠페인·MC 워커 spawn마다 불필요한 로드 비용이 붙는다. pk_base가 실제로 필요한
# _navy_effort 안에서만 지연 import한다.

# ── 화력원 ────────────────────────────────────────────────────────────────────
# 해군 함정이 적 기지를 때릴 수 있는 지상공격 무기. 대함 무기(해성·하푼)는 여기 없다 —
# 표적이 항구·비행장이므로 지상공격 순항미사일만 유효하다.
#   현무-3C(1500km, KVLS)  · Tomahawk Block V(1700km, Mk.41·VPM)
# 둘 다 사거리가 전역(한반도 격자) 전체를 덮으므로 zone 제약을 두지 않는다.
LAND_ATTACK_WEAPONS: tuple[str, ...] = ('현무-3C', 'Tomahawk Block V')

# ── 튜닝 상수 (보수적 — ON/OFF 기준값 측정 후 조정) ───────────────────────────
# 전부 v19.4 전략폭격 계수(_STRIKE_DMG_PER_EFFORT=0.030/소티율)에 **앵커링**한다.
# 새 척도를 발명하면 기존 공군 밸런스와 어긋나므로, 공군 화력을 기준자로 삼아 해군·육군을
# 그 위에 얹는다.
#
# 앵커: 「B-1B 2대의 1일 소티(소티율 합 1.0) ≈ 순항미사일 살보 4발」
#   → 0.030 ≈ 4발 × _NAVY_DMG_PER_MISSILE / (pk 0.8) → 발당 약 0.009.
# 탄두 중량 등가(B-1B 재래식 탑재 vs 450kg급 순항미사일 탄두)의 **거친 근사**이며,
# 공개 교리에 정밀 등가표가 없다. 그래서 보수적으로 잡고 ON/OFF 실측으로 검증한다.
_NAVY_DMG_PER_MISSILE = 0.009   # 지상공격 순항미사일 1발당 기지 손상(× pk_base)
_NAVY_SALVO_PER_TICK  = 4       # 함정 1척이 1시간 틱에 쏘는 최대 살보(연속 난사 방지)

# 육군 지대지: 현무-2 계열 탄도미사일. 순항미사일보다 탄두가 크고 요격이 어려우나
# 정밀도·재장전에서 불리 → 발당 손상은 순항미사일과 같은 급으로 보수적으로 둔다.
_ARMY_DMG_PER_ROUND   = 0.009

# 협조 이득 — 동시 타격 시 적 방공망 분산. 보수적(협조가 화력을 2배로 만들진 않는다).
_SIMULTANEOUS_BONUS   = 1.15
# 동시 타격의 대가 — 화력지원 협조수단(FSCM) 없이 유인 폭격기가 미사일 궤적과 같은
# 표적·같은 틱에 들어가면 소티를 접는다. **확률이 아니라 결정론적 취소**다:
# 작전급 오사 확률값은 공개 교리에 근거가 없어, 지어낸 확률을 넣으면 모델 부채가 된다
# (engine_airforce `_TANKER_MULT_PER` 주석 선례 — 근거 없는 수식은 넣지 않는다).
_DECONFLICT_SORTIE_LOSS = 0.35   # 동시 모드에서 취소되는 유인 폭격 화력 비율


def build_land_stock(ship_type: str, ship_db: dict) -> dict:
    """함정 1척의 지상공격 재고 — SHIP_DB에서 지상공격 무기만 추출.
    없으면 빈 dict(대부분의 함정은 지상공격 능력이 없다).

    수상함은 지상공격 순항미사일을 default_inventory에 두고(KDX-III 현무-3C 등), 잠수함은
    default_strike_inventory에 둔다(KSS-III 현무-3C — 어뢰관/VLS 발사). **둘 다** 봐야
    KSS-III의 현무-3C가 합동 화력 지상공격으로 잡힌다. 잠수함의 현무-3C는 대함이 아니라
    지상공격 전용이므로(_select_sub_strike_wpn에서 제외됨) 이 경로가 유일한 소비처다.
    ⚠ 이중계상 없음: 수상함은 default_strike_inventory 키가 없고(=빈 dict), 잠수함은
    default_inventory에 지상공격 무기가 없다 — 같은 무기가 두 dict에 겹치지 않는다."""
    src = ship_db.get(ship_type) or {}
    inv    = src.get('default_inventory', {}) or {}
    strike = src.get('default_strike_inventory', {}) or {}
    return {w: int(inv.get(w, 0)) + int(strike.get(w, 0))
            for w in LAND_ATTACK_WEAPONS
            if int(inv.get(w, 0)) + int(strike.get(w, 0)) > 0}


class JointFires:
    """합동 화력 층 — 공유 표적(EnemyBase)에 육해공 화력을 협조 타격.

    CampaignEngine이 매 틱 tick()을 호출한다. 표적 목록은 캠페인이 소유해 공군 층과
    **공유**한다(공군의 전략폭격도 같은 기지를 때리므로 목록이 갈리면 안 된다)."""

    def __init__(self, cfg: dict, bases: list):
        self.cfg   = dict(cfg)
        self.bases = bases            # 캠페인 소유 EnemyBase 목록(공군 층과 공유)
        # 'sequential'(시차) = 오사 없음 · 'simultaneous'(동시) = 분산 이득 + 소티 취소
        self.mode  = str(cfg.get('joint_fire_mode', 'sequential'))
        # 누적 실적(투명성·발현 증거)
        self.n_navy_fired   = 0       # 해군이 발사한 지상공격 미사일 총수
        self.n_army_fired   = 0       # 육군이 발사한 지대지 탄 총수
        self.n_air_effort   = 0.0     # 공군 전략폭격 누적 소티율
        self.n_deconflict   = 0       # 협조 미비로 취소된 유인 폭격 건수(동시 모드)
        # (화력원, 표적) 쌍 단위로 센다 — 한 틱에 기지 1곳이 상한에 닿으면 화력원 수만큼
        # 오른다. '넘김 사건 수'가 아니라 '넘김이 걸린 배분 횟수'이므로 협조 이득의 크기를
        # 이 값으로 재지 말 것(진단용).
        self.n_overkill_skip = 0
        self.army_fire_unused = False  # 육군 화력 편성했으나 지상 층 OFF라 미참여(짝 경고)
        self.dmg_by_service = {'air': 0.0, 'navy': 0.0, 'army': 0.0}  # 군별 기여(v21.4 씨앗)
        self.fire_log: list = []      # [{'t_h','target','air','navy','army'}]

    # ── 표적 선택 ─────────────────────────────────────────────────────────
    def _priority_targets(self) -> list:
        """타격 가치 순 표적 — 아직 완파(cap)에 안 닿은 기지 중 출항분담 큰 순.
        v19.4 `_apply_strike`의 우선순위와 동일 규칙(협조해도 가치 판단은 같다)."""
        from engine_airforce import _BASE_DMG_CAP
        return sorted((b for b in self.bases if b.damage < _BASE_DMG_CAP),
                      key=lambda b: b.output_share, reverse=True)

    # ── 화력 수집 ─────────────────────────────────────────────────────────
    def _navy_effort(self, ships: list) -> float:
        """가용 함정의 지상공격 살보 → 손상 환산. 재고를 실제로 차감한다(소진되면 화력 0).
        수리·재보급·이동 중 함정은 타격 임무를 못 낸다(available 규약 준수)."""
        from engine_combat import FRIENDLY_STRIKE_DB   # 지연 import(모듈 헤더 주석 참조)
        total = 0.0
        for s in ships:
            if not s.available or not getattr(s, 'land_stock', None):
                continue
            budget = _NAVY_SALVO_PER_TICK
            for wpn in LAND_ATTACK_WEAPONS:
                have = s.land_stock.get(wpn, 0)
                if have <= 0 or budget <= 0:
                    continue
                n = min(have, budget)
                s.land_stock[wpn] = have - n
                budget -= n
                self.n_navy_fired += n
                pk = FRIENDLY_STRIKE_DB[wpn]['pk_base']
                total += n * _NAVY_DMG_PER_MISSILE * pk
        return total

    def _army_effort(self, army) -> float:
        """육군 지대지 화력 → 손상 환산. 지상 층이 없거나 화력 자산이 없으면 0.

        ⚠ 짝: 지상 작전급(enable_army_campaign)이 꺼져 있으면 army=None이라 육군 화력
        편성을 골라도 한 발도 안 나간다. 이건 조용한 무동작이므로 `army_fire_unused`로
        표면화한다(사용자는 편성표에 현무 여단이 있으면 참여 중이라고 믿는다)."""
        if army is None:
            self.army_fire_unused = bool(self.cfg.get('army_fire_preset', '없음') != '없음')
            return 0.0
        fn = getattr(army, 'fire_rounds', None)
        if fn is None:
            return 0.0
        n = fn()                      # 이번 틱 발사탄 수(재고 차감은 지상 층 소관)
        self.n_army_fired += n
        return n * _ARMY_DMG_PER_ROUND

    # ── 틱 ────────────────────────────────────────────────────────────────
    def tick(self, t_h: int, ships: list, air_effort: float, army=None) -> None:
        """1시간 합동 화력 틱.

        air_effort: 공군 전략폭격 소티율 합(AirCampaign이 제공). 합동 ON이면 공군은
        스스로 기지를 때리지 않고 **이 층에 화력을 위임**한다 → 이중 계상 방지.
        """
        from engine_airforce import _STRIKE_DMG_PER_EFFORT, _BASE_DMG_CAP

        targets = self._priority_targets()
        if not targets:
            return                    # 표적 없음(전략폭격 OFF거나 전 기지 완파) → 발동 0

        air_dmg  = air_effort * _STRIKE_DMG_PER_EFFORT
        self.n_air_effort += air_effort
        navy_dmg = self._navy_effort(ships)
        army_dmg = self._army_effort(army)

        # 협조 모드 — 이득과 대가는 **서로 다른 축**이라 따로 건다:
        #   · 분산 이득 = 여러 화력원이 같은 틱에 들어와 적 방공망이 나뉘는 것 → 화력원이
        #     2개 이상이면 성립한다(폭격기 유무와 무관 — 순항미사일+지대지도 다축이다).
        #   · 협조 미비 대가 = **유인** 폭격기가 미사일 궤적과 겹쳐 임무를 접는 것 →
        #     폭격기가 실제로 뜰 때만 성립한다.
        # 둘을 `air_dmg > 0` 하나로 묶으면, 폭격기 없는 편성(제공권 열세 = 이 기능이 가장
        # 값하는 무대)에서 동시/시차가 bit-identical이 되어 모드 선택이 죽는다.
        if self.mode == 'simultaneous':
            n_src = sum(1 for d in (air_dmg, navy_dmg, army_dmg) if d > 0)
            if air_dmg > 0 and (navy_dmg + army_dmg) > 0:
                air_dmg -= air_dmg * _DECONFLICT_SORTIE_LOSS   # 유인 편대 임무 중단
                self.n_deconflict += 1
            if n_src >= 2:
                air_dmg  *= _SIMULTANEOUS_BONUS
                navy_dmg *= _SIMULTANEOUS_BONUS
                army_dmg *= _SIMULTANEOUS_BONUS

        # 화력 배분 — 가치 순 표적에 차례로 얹되, 상한(_BASE_DMG_CAP)에 닿으면 **남은
        # 화력을 잔여 표적으로 넘긴다**. 이게 협조의 실체다: 공군 단독(v19.4 _apply_strike)은
        # 최우선 기지 하나에만 화력을 쏟아 그 기지가 완파된 뒤에도 계속 때리고 나머지
        # 기지는 방치했다. 합동이면 넘겨서 전 기지를 무력화한다.
        #
        # ⚠ 표적당 효율 체감((1-damage))은 **얹지 않는다** — `_BASE_DMG_CAP` 0.80이 이미
        # "때려도 분산·예비로 완전 파괴 불가"라는 체감을 표현하고 있어, 그 위에 또 곱하면
        # **이중 계상**이다. 실제로 처음엔 얹었다가 합동 화력이 공군 단독보다 기지를 덜
        # 부수는 역설(0.267→0.191)이 나왔다 — 화력이 상한에 점근만 하고 도달을 못 해
        # '표적 넘김' 이득 자체가 발현하지 않았다. v18.05.04(표적 난이도가 탄도에 이중
        # 벌점 → 상층이 자기 설계 표적에 벌점)와 같은 유형.
        pool = [('air', air_dmg), ('navy', navy_dmg), ('army', army_dmg)]
        applied = {'air': 0.0, 'navy': 0.0, 'army': 0.0}
        for service, dmg in pool:
            if dmg <= 0:
                continue
            for b in targets:
                if dmg <= 0:
                    break
                room = _BASE_DMG_CAP - b.damage
                if room <= 1e-9:
                    self.n_overkill_skip += 1
                    continue          # 완파 도달 → 다음 표적으로 넘김(화력 낭비 방지)
                take = min(room, dmg)
                b.damage += take
                applied[service] += take
                dmg -= take           # 상한에 막혀 못 쓴 몫만 다음 표적으로
        for k, v in applied.items():
            self.dmg_by_service[k] += v
        if sum(applied.values()) > 0:
            self.fire_log.append({
                't_h': t_h, 'mode': self.mode,
                'air':  round(applied['air'], 4),
                'navy': round(applied['navy'], 4),
                'army': round(applied['army'], 4),
            })

    # ── 산출 ──────────────────────────────────────────────────────────────
    def summary(self) -> dict:
        tot = sum(self.dmg_by_service.values())
        return {
            'joint_fires':         True,
            'joint_fire_mode':     self.mode,
            'joint_navy_fired':    self.n_navy_fired,
            'joint_army_fired':    self.n_army_fired,
            'joint_air_effort':    round(self.n_air_effort, 2),
            'joint_deconflict':    self.n_deconflict,
            'joint_overkill_skip': self.n_overkill_skip,
            # 육군 화력을 편성했는데 지상 작전급이 꺼져 한 발도 못 쏜 상태(조용한 무동작 표면화)
            'joint_army_unused':   self.army_fire_unused,
            # 군별 기여도 — v21.4 통합 보고서의 씨앗(누가 표적을 얼마나 무력화했나)
            'joint_dmg_by_service': {k: round(v, 3) for k, v in self.dmg_by_service.items()},
            'joint_dmg_share': {k: (round(v / tot, 3) if tot > 0 else 0.0)
                                for k, v in self.dmg_by_service.items()},
            # v21.4: 위 dict는 캠페인 MC 집계(_MC_ACC_KEYS)가 스칼라만 받아 반복 분석에서
            #   통째로 소실된다. 같은 값을 스칼라로도 내보내 MC 평균이 살아남게 한다.
            'joint_share_air':     (round(self.dmg_by_service.get('air', 0.0) / tot, 3)
                                    if tot > 0 else 0.0),
            'joint_share_navy':    (round(self.dmg_by_service.get('navy', 0.0) / tot, 3)
                                    if tot > 0 else 0.0),
            'joint_share_army':    (round(self.dmg_by_service.get('army', 0.0) / tot, 3)
                                    if tot > 0 else 0.0),
            'joint_fire_log':      self.fire_log,
        }
