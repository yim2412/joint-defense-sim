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
}
