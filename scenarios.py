"""
scenarios — 시나리오 라이브러리(프리셋 정의).

app_main.py에서 분리한 순수 데이터 모듈. 코드 참조가 없는 리터럴 dict라 의존이 없다.
UI 문자열이므로 CLAUDE.md의 exe 표시 텍스트 규칙을 따른다 — 군사용어는 쓰되 코드 명칭
(함수명·클래스명·필드명)은 쓰지 않는다.
"""

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
    '항만 거점 방어': {
        'desc': '해군기지·항만 거점으로 적 무인 수상정(자폭 USV)·침투 고속정이 근접 '
                '돌파하고, 항만 입구엔 기뢰가 부설된 복합 위협 상황. 함대와 해안 고정 '
                '방어 포대(C-RAM·SAM)가 협동해 거점을 방어한다.',
        'recommend': '연안 방어 전대(함정+해안 포대) · 박무 · 기뢰 위협 ON',
        'cfg': {
            'fleet_preset': '연안 방어 전대',
            'fleet_region': '서해',
            'weather': '흐림 (박무)',
            'season': 'summer',
            'enemy_fleet_mode': 'preset',
            'enemy_fleet_preset': '항만 침투 복합',
            'enable_mine_threat': True,
        },
    },
    # ── v21.3 합동 작전(캠페인) 시나리오 — 육해공 통합 전역 ────────────────────
    # 단발 전술이 아니라 작전급 캠페인. 각 시나리오는 각 군 초기 전력·작전 목표·성공 판정을
    # 서술로 담고, cfg로 캠페인 층(공군 제공권·지상 방공·합동 화력)을 함께 켠다.
    # ⚠ 공군 편성은 UI 위젯이 없어 기본 '한미 연합 공군 패키지'로 고정, 전역 길이도 기본 72h.
    '한반도 전면전 (72시간 전역)': {
        'desc': '북한의 전면 남침에 한미 연합 전력이 총력 대응하는 72시간 작전급 전역. '
                '한미 기동전단이 서해·동해 해상교통로를 지키고, 공군이 제공권 장악·방공망 '
                '제압(SEAD)·전략폭격을, 육군 지대지 화력(현무)이 적 종심 표적을 타격한다. '
                '육해공이 같은 적 기지를 협조 타격(합동 화력)하고, 연안 방공 포대가 탄도 '
                '위협을 요격한다. 【목표】전 해상교통로 평균 통제도 70% 이상 확보. '
                '【성공 판정】승리 = 평균 통제도 70%↑ · 무승부 = 30~70% · 패배 = 30% 미만 또는 함대 전멸.',
        'recommend': '한미 기동전단 강화 · 전 도메인 합동작전(공군·지상·합동 화력) · 동시 타격',
        'cfg': {
            'fleet_preset': '한미 기동전단 강화',
            'weather': '맑음 (주간)',
            'season': 'summer',
            'enemy_fleet_mode': 'preset',
            'enemy_fleet_preset': '전면전 포화',
            'enable_campaign_mode': True,
            'enable_air_campaign': True,
            'enable_sead': True,
            'enable_strategic_strike': True,
            'enable_army_campaign': True,
            'enable_joint_fires': True,
            'joint_fire_mode': 'simultaneous',
            'army_fire_preset': '현무 여단 (증강)',
            'enable_coastal_sam': True,
            'coastal_sam_preset': '한국형 BMD (KAMD)',
            'enable_enemy_sead': True,
            'enable_precise_engagement': True,
        },
    },
    '대만해협 위기': {
        'desc': '중국의 대만 침공 기도로 역내 긴장이 격화하는 상황. 한국 이지스 기동전단이 '
                '제1도련선 해상교통로를 방어하고, 중국 산둥 항모전단의 다축 킬체인(탄도·극초음속·'
                '함재기)에 맞서 공군 제공권 장악과 합동 화력으로 대응한다. 육해공이 적 항구·비행장을 '
                '협조 타격해 적 출항능력을 떨어뜨리나, 적 항모전단의 화력이 강력해 치열한 교착이 '
                '예상된다. 【목표】교통로 통제 유지 + 적 출항능력 저하. '
                '【성공 판정】승리 = 평균 통제도 70%↑ · 무승부 = 30~70% · 패배 = 30% 미만 또는 전멸.',
        'recommend': '전 이지스 기동전단 · 공군 제공권 + 전략폭격 · 합동 화력 협조 타격 (고강도)',
        'cfg': {
            'fleet_preset': '전 이지스 기동전단',
            'weather': '맑음 (주간)',
            'season': 'summer',
            'enemy_fleet_mode': 'preset',
            'enemy_fleet_preset': '산둥 항모전단',
            'enable_campaign_mode': True,
            'enable_air_campaign': True,
            'enable_sead': True,
            'enable_strategic_strike': True,
            'enable_army_campaign': True,
            'enable_joint_fires': True,
            'joint_fire_mode': 'sequential',
            'army_fire_preset': '현무 여단 (증강)',
            'enable_precise_engagement': True,
        },
    },
    '독도·이어도 제한전': {
        'desc': '독도·이어도 관할권을 둘러싼 제한적 무력 충돌. 대규모 전면전이 아닌 국지 도발로, '
                '한국 해군 기동전단과 공군이 EEZ 해상교통로를 방어한다. 상대적으로 낮은 강도이나 '
                '제공권·방공망 제압을 포함한 다도메인 대응이 요구된다(전략폭격·합동 화력은 미개시). '
                '【목표】제한 교전에서 해상교통로 통제 확보. 【성공 판정】승리 = 평균 통제도 70%↑.',
        'recommend': '한미 기동전단 기본 · 공군 제공권 + SEAD(전략폭격 없음) · 박무',
        'cfg': {
            'fleet_preset': '한미 기동전단 기본',
            'weather': '흐림 (박무)',
            'season': 'autumn',
            'enemy_fleet_mode': 'preset',
            'enemy_fleet_preset': '이어도 방어전',
            'enable_campaign_mode': True,
            'enable_air_campaign': True,
            'enable_sead': True,
            'enable_precise_engagement': True,
        },
    },
}
