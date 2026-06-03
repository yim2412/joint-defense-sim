# =============================================================================
#  military_db.py — 한반도 군사 배치 데이터베이스 (공개 자료 기반)
#  출처: GlobalSecurity, CSIS Missile Threat, FAS, Wikipedia, ArmyRecognition,
#        MilitaryWatchMagazine, RAND RRA619-1, latitude.to, Wikimapia
#  수집일: 2026-06-01
#  주의: 모든 좌표·수치는 공개 출판물 기준. 실제 군사 작전에 사용 불가.
# =============================================================================

import math

# =============================================================================
#  Part 1. 북한 포병·장사정포 (DPRK_ARTILLERY_DB)
# =============================================================================

DPRK_ARTILLERY_DB = {

    # ─────────────────────────────────────────────────────────────────────────
    # 170mm 자주포 (곡산 / Koksan)
    # ─────────────────────────────────────────────────────────────────────────
    "M1978_Koksan": {
        "name": "M-1978 곡산 170mm 자주포",
        "caliber_mm": 170,
        "type": "SP_GUN",
        "range_km": {"he": 40, "rap": 60, "confirmed_test": 45},
        "cep_m": 500,          # 추정 — 무유도 포탄 [RAND]
        "rate_of_fire_rpm": 0.2,
        "rounds_onboard": 12,
        "inventory_est": 500,
        "deployment_note": "DMZ 이북 5km 내외 갱도 진지. 서울까지 41~61km [GlobalSecurity]",
        "sources": ["https://www.globalsecurity.org/military/world/dprk/m-1978-170.htm"],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 240mm 방사포
    # ─────────────────────────────────────────────────────────────────────────
    "M1985_240mm": {
        "name": "M-1985 240mm 방사포",
        "caliber_mm": 240,
        "type": "MLRS",
        "tubes": 12,
        "range_km": {"standard": 43, "extended_claim": 80},
        "warhead_kg": 90,
        "cep_m": 300,
        "guidance": "무유도(스핀안정식)",
        "salvo_time_s": 45,
        "reload_min": 10,
        "sources": ["https://missilethreat.csis.org/missile/m1985m1991-mlrs/"],
    },

    "M1991_240mm": {
        "name": "M-1991 240mm 방사포 (주체 100)",
        "caliber_mm": 240,
        "type": "MLRS",
        "tubes": 22,
        "range_km": {"standard": 60, "extended_claim": 120},
        "warhead_kg": 90,
        "warhead_types": ["HE-FRAG", "연막", "소이", "화학(추정)"],
        "cep_m": 300,
        "guidance": "무유도(스핀안정식), M-2024 개량형은 유도장치 추가",
        "sources": ["https://missilethreat.csis.org/missile/m1985m1991-mlrs/"],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # KN-09 300mm 유도 방사포
    # ─────────────────────────────────────────────────────────────────────────
    "KN09_300mm": {
        "name": "KN-09 300mm 유도 방사포",
        "caliber_mm": 300,
        "type": "GUIDED_MLRS",
        "tubes": 8,
        "range_km": {"standard": 200, "max_reported": 250},
        "warhead_kg": 190,
        "cep_m": {"unguided": 100, "gnss_aided": 35},
        "guidance": "위성항법(GNSS) 유도",
        "launcher": "6×6 트럭 TEL",
        "deployment_note": "서울뿐 아니라 평택·오산 미군기지 타격 사거리",
        "sources": [
            "https://en.wikipedia.org/wiki/KN-09_(multiple_rocket_launcher)",
            "https://missilethreat.csis.org/missile/kn-09-kn-ss-x-9/",
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # KN-25 초대형 방사포 (~600mm)
    # ─────────────────────────────────────────────────────────────────────────
    "KN25": {
        "name": "KN-25 초대형 방사포",
        "caliber_mm": 600,     # USFK 추정
        "type": "SUPER_LARGE_MLRS",
        "tubes": 4,
        "range_km": 380,       # 실증 사거리
        "launch_weight_kg": 3000,
        "cep_m": 100,          # 추정
        "guidance": "미확인",
        "propulsion": "단단 고체연료",
        "deployment_note": "한반도 전역 + 오키나와 사거리",
        "sources": [
            "https://missilethreat.csis.org/missile/kn-25/",
            "https://en.wikipedia.org/wiki/KN-25",
        ],
    },
}


# =============================================================================
#  Part 2. 북한 해안포 및 해안 대함 미사일 (DPRK_COASTAL_DB)
# =============================================================================

DPRK_COASTAL_DB = {

    "M1992_130mm": {
        "name": "M-1992 130mm 해안 자주포",
        "caliber_mm": 130,
        "type": "SP_COASTAL_GUN",
        "range_m": 29_500,
        "role": "해안 방어 / 상륙 저지",
        "sources": ["Wikipedia List of equipment of the KPA Ground Force"],
    },

    "M1975_130mm": {
        "name": "M-1975 130mm 자주포 (M-46 파생)",
        "caliber_mm": 130,
        "type": "SP_COASTAL_GUN",
        "range_m": 27_150,
        "sources": ["Wikipedia List of equipment of the KPA Ground Force"],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # KN-01 해안 대함 순항미사일 (실크웜 개량형)
    # ─────────────────────────────────────────────────────────────────────────
    "KN01": {
        "name": "KN-01 해안 발사 대함 순항미사일",
        "type": "ASCM_COASTAL",
        "origin": "소련 P-15 Styx → 중국 HY-1 실크웜 → 북한 개량",
        "range_km": {"baseline": 85, "extended": 160, "turbojet_claim": 300},
        "warhead_kg": 500,
        "guidance": "능동 레이더 호밍 + 관성항법 추정",
        "launcher": "도로이동형(TEL) + 해안 고정 발사대",
        "deployment": {
            "west_sea": {
                "areas": ["옹진반도", "초도", "남포 인근"],
                "threat_targets": ["인천 근해", "백령도 인근"],
            },
            "east_sea": {
                "areas": ["원산", "마양도", "차호"],
                "threat_targets": ["속초", "양양 인근"],
            },
        },
        "sources": [
            "https://missilethreat.csis.org/missile/kn-01/",
            "https://www.globalsecurity.org/wmd/world/dprk/kn-1.htm",
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # 금성-3 (KN-19) 해안 방어 순항미사일
    # ─────────────────────────────────────────────────────────────────────────
    "Kumsong3": {
        "name": "금성-3 (KN-19) 해안 방어 순항미사일",
        "type": "ASCM_COASTAL",
        "range_km": 250,
        "guidance": "능동 레이더 호밍 + 터미널 유도 추정",
        "launcher": "도로이동형(TEL)",
        "test": {"date": "2017-06", "result": "4발 중 3발 명중 (원산→마양도)"},
        "deployment": {"areas": ["원산 일대", "동해안 기지 연계"]},
        "sources": [
            "https://militarywatchmagazine.com/article/kumsong-3-why-north-korea-s-adversaries-fear-its-mobile-new-coastal-defence-missile-batteries",
        ],
    },
}


# =============================================================================
#  Part 3. 한국 해군 기지 (ROK_NAVAL_BASES)
# =============================================================================

ROK_NAVAL_BASES = {

    "Jinhae": {
        "name": "진해 해군기지",
        "lat": 35.133, "lon": 128.633,
        "role": "해군 조선소·군수 중심. 미 해군 CFA Chinhae 병용",
        "icao": "K-10",
        "sources": ["https://www.globalsecurity.org/military/world/rok/jinhae.htm"],
    },
    "Busan": {
        "name": "부산 해군기지 (해군작전사령부)",
        "lat": 35.0967, "lon": 129.1039,
        "role": "해군작전사 본부. 미 해군 CNFK 주둔",
        "capacity": "최대 30척 동시 수용, 항모 입항 가능",
        "ships": ["독도함(강습상륙함)", "세종대왕급 이지스 구축함"],
        "sources": ["https://en.wikipedia.org/wiki/Busan_Naval_Base"],
    },
    "Jeju": {
        "name": "제주 해군기지 (강정마을)",
        "lat": 33.2281, "lon": 126.4839,
        "operational_since": "2016-02-26",
        "role": "제7기동전단(전략기동함대) 모항. 이지스 구축함·잠수함 전진 배치",
        "fleet": "제7기동전단",
        "ships": ["KDX-III 이지스 구축함", "Type-214 잠수함"],
        "sources": ["https://en.wikipedia.org/wiki/Jeju_Civilian-Military_Complex_Port_for_Beautiful_Tourism"],
    },
    "Pyeongtaek_2nd": {
        "name": "평택 해군기지 (제2함대 사령부, 서해)",
        "lat": 36.9964, "lon": 126.8125,
        "fleet": "제2함대",
        "sources": ["Wikimapia 18694114"],
    },
    "Donghae_1st": {
        "name": "동해 해군기지 (제1함대 사령부, 동해)",
        "lat": 37.514, "lon": 129.114,
        "fleet": "제1함대",
        "city": "강원도 동해시",
        "sources": ["Wikimapia 19182591"],
    },
    "Mokpo_3rd": {
        "name": "목포 해군기지 (제3함대 사령부, 남해·서해 남부)",
        "lat": 34.7957, "lon": 126.4286,
        "fleet": "제3함대",
        "icao": "K-15",
        "sources": ["https://www.globalsecurity.org/military/world/rok/navy-fac.htm"],
    },
    "Pohang_Marines": {
        "name": "포항 해병대기지 (캠프 무적)",
        "lat": 36.019, "lon": 129.365,
        "role": "해병 제1사단. 상륙훈련 기지. 주한 유일 미 해병대 기지",
        "sources": ["https://www.globalsecurity.org/military/facility/pohang.htm"],
    },
    "Incheon": {
        "name": "인천 해군기지",
        "lat": 37.456, "lon": 126.608,
        "role": "해역방어사령부 — 서울 인근 해역 방어",
    },
    "Baengnyeongdo": {
        "name": "백령도 해군기지",
        "lat": 37.973, "lon": 124.631,
        "role": "서해 최북단 전진기지. NLL 방어",
        "note": "북한 황해도 해안포 직접 위협권",
    },
}


# =============================================================================
#  Part 4. 한국·미군 공군 기지 (AIRBASE_DB)
# =============================================================================

AIRBASE_DB = {

    # 주한미군 공군 기지
    "Osan": {
        "name": "오산 공군기지 (K-55)",
        "icao": "RKSO",
        "lat": 37.0877, "lon": 127.0245,
        "operator": "미 공군 제51전투비행단 (51 FW)",
        "aircraft": ["F-16C/D Block 40", "A-10C"],
        "role": "주한미공군 주력기지. 7공군 사령부 위치",
        "sources": ["https://en.wikipedia.org/wiki/Osan_Air_Base"],
    },
    "Kunsan": {
        "name": "군산 공군기지 (K-8)",
        "icao": "RKJK",
        "lat": 35.9022, "lon": 126.6095,
        "operator": "미 공군 제8전투비행단 (8 FW 'Wolf Pack')",
        "aircraft": ["F-16C/D"],
        "role": "서해 방어, 지상 공격",
        "sources": ["https://en.wikipedia.org/wiki/Kunsan_Air_Base"],
    },

    # 한국 공군 기지
    "Suwon": {
        "name": "수원 공군기지 (K-13)",
        "icao": "RKSW",
        "lat": 37.2386, "lon": 127.0069,
        "operator": "공군 제10전투비행단",
        "aircraft": ["KF-5E/F"],
        "us_unit": "6th Bn, 52nd ADA Regiment — 패트리어트",
        "runways": "15L/33R, 15R/33L (각 9,000ft)",
        "sources": ["https://en.wikipedia.org/wiki/Suwon_Air_Base"],
    },
    "Cheongju": {
        "name": "청주 공군기지 (K-59)",
        "icao": "RKTU",
        "lat": 36.717, "lon": 127.499,
        "operator": "공군 제17전투비행단",
        "aircraft": ["F-35A"],
        "note": "F-35A 스텔스 전투기 주력 기지",
        "sources": ["https://www.globalsecurity.org/military/facility/cheongju.htm"],
    },
    "Gimhae": {
        "name": "김해 공군기지 (K-1)",
        "icao": "RKPK",
        "lat": 35.1743, "lon": 128.9363,
        "operator": "공군 제5공중기동비행단",
        "aircraft": ["C-130H", "CN-235", "UH-60P"],
        "role": "전술 공수 및 대잠 지원",
        "sources": ["https://en.wikipedia.org/wiki/Gimhae_Air_Base"],
    },
    "Seongnam": {
        "name": "서울 공군기지 성남 (K-16)",
        "icao": "RKSS",
        "lat": 37.4408, "lon": 127.1083,
        "operator": "공군 제15특수임무비행단",
        "role": "VIP 수송, 특수임무",
    },
}


# =============================================================================
#  Part 5. 주한미군 주요 지상 기지 (USFK_BASES)
# =============================================================================

USFK_BASES = {

    "Camp_Humphreys": {
        "name": "캠프 험프리스 (평택)",
        "lat": 36.967, "lon": 127.033,
        "city": "경기도 평택시 팽성읍",
        "area_acres": 3454,
        "area_ha": 1398,
        "personnel_approx": 42_000,
        "role": "주한미군 통합기지. 미8군 사령부. 미국 최대 해외 군사기지",
        "airfield": "Desiderio 육군 비행장 (ICAO: RKSG), 활주로 2,476m",
        "sources": ["https://en.wikipedia.org/wiki/Camp_Humphreys"],
    },
    "Camp_Casey": {
        "name": "캠프 케이시 (동두천)",
        "lat": 37.9219, "lon": 127.0856,
        "city": "경기도 동두천시",
        "distance_seoul_km": 64,
        "area_acres": 3500,
        "units": ["2nd Infantry Division elements", "210th Field Artillery Brigade"],
        "sources": ["https://en.wikipedia.org/wiki/Camp_Casey,_South_Korea"],
    },
    "Camp_Walker": {
        "name": "캠프 워커 (대구)",
        "lat": 35.8364, "lon": 128.5903,
        "city": "대구광역시 남구",
        "role": "주한미군 대구 지원 기지",
        "sources": ["https://en.wikipedia.org/wiki/Camp_Walker"],
    },
    "Busan_Support": {
        "name": "부산 지원시설",
        "lat": 35.0967, "lon": 129.1039,
        "role": "유엔사 후방기지. 미 해군 CNFK. 군수지원",
    },
}


# =============================================================================
#  Part 6. 주요 DMZ 이북 북한 포병 전진 진지 (추정, 공개자료 기반)
# =============================================================================

DPRK_FORWARD_ARTY_POSITIONS = {
    # 좌표는 공개 문헌 기반 추정값 (실제 갱도 진지 위치 기밀)
    "west_kaesong_north": {
        "lat": 38.03, "lon": 126.55,
        "desc": "서부 전선 개성 북방 ~5km 추정",
        "systems": ["M1978_Koksan", "M1991_240mm"],
        "note": "서울 직선거리 약 55km",
    },
    "center_chorwon": {
        "lat": 38.25, "lon": 127.18,
        "desc": "중부 철원 북방",
        "systems": ["M1985_240mm", "M1991_240mm"],
    },
    "east_kumgangsan": {
        "lat": 38.55, "lon": 128.15,
        "desc": "동부 금강산 인근",
        "systems": ["M1985_240mm"],
    },
}


# =============================================================================
#  편의 함수
# =============================================================================

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """두 좌표 간 거리 (km)"""
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlam/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


def get_artillery_max_range(system_key: str) -> float:
    """장사정포 최대 사거리(km) 반환"""
    sys = DPRK_ARTILLERY_DB.get(system_key, {})
    r = sys.get("range_km", {})
    if isinstance(r, dict):
        return max(r.values())
    return float(r) if r else 0.0


def get_base_coords(db_name: str, key: str) -> tuple[float, float]:
    """(lat, lon) 반환. db_name: 'navy'|'airbase'|'usfk'"""
    mapping = {"navy": ROK_NAVAL_BASES, "airbase": AIRBASE_DB, "usfk": USFK_BASES}
    entry = mapping.get(db_name, {}).get(key, {})
    return (entry.get("lat", 0.0), entry.get("lon", 0.0))


# 서울 좌표 (위협 판정 기준점)
SEOUL_COORD = (37.5665, 126.9780)

if __name__ == "__main__":
    for pos_key, pos in DPRK_FORWARD_ARTY_POSITIONS.items():
        d = haversine_km(pos["lat"], pos["lon"], *SEOUL_COORD)
        print(f"\n{pos['desc']} → 서울: {d:.0f}km")
        for sys_key in pos["systems"]:
            max_r = get_artillery_max_range(sys_key)
            can_hit = "O" if max_r >= d else "X"
            name = DPRK_ARTILLERY_DB[sys_key]["name"]
            print(f"  [{can_hit}] {name} (최대 {max_r}km)")
