#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
_audit_roundtrip.py — 설정 저장/복원 round-trip 런타임 감사 (빌드 제외 도구)

정적 정규식(audit_static_scan.chk_flag_restore_auto)은 복원 코드의 '형태'를 보지만
정규식 자체가 취약하다(3-튜플 for-루프에서 오탐 겪음). 이 도구는 **실제로 실행**한다:
offscreen Qt로 MainWindow를 헤드리스 생성 → 모든 토글을 기본과 반대로 뒤집은 cfg를
_restore_cfg로 복원 → 다시 _build_cfg_from_ui → **뒤집은 값이 그대로 반영됐는지** 대조.

복원이 누락된 토글은 뒤집어도 기본값으로 되돌아오므로 불일치로 100% 잡힌다
(정규식 형태와 무관 — strike·thaad·ashore 복원 누락을 근본 차단). 이것이 정적 감사의
'런타임 속성' 보강이다.

사용:  python _audit_roundtrip.py     # 불일치 있으면 exit 1
"""
import os, sys
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass


def main():
    try:
        from PyQt6.QtWidgets import QApplication
        import app_main
    except Exception as e:
        print(f"BLOCKED — Qt/app_main import 실패: {e!r}")
        return 2

    app = QApplication.instance() or QApplication(sys.argv)
    try:
        w = app_main.MainWindow()
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"BLOCKED — MainWindow 헤드리스 생성 실패: {e!r}")
        return 2

    # 체크박스 없는 상시 ON 내부 기능(cfg에 리터럴 True로 빌드, 뒤집기 불가) — round-trip 제외.
    # audit_static_scan.chk_flag_consume_auto의 ALWAYS_ON과 동일 경계(문서화된 내부 기본값).
    ALWAYS_ON = {'enable_cec_preassign', 'enable_subsystem_damage', 'enable_decoy',
                 'enable_ecm', 'enable_evasion', 'enable_layered_defense',
                 'enable_random_placement', 'enable_selfdefense'}
    base = w._build_cfg_from_ui()
    enable_keys = [k for k in base if k.startswith('enable_')
                   and isinstance(base[k], bool) and k not in ALWAYS_ON]
    # 모든 토글을 기본과 반대로 뒤집은 cfg
    flipped = dict(base)
    for k in enable_keys:
        flipped[k] = not base[k]

    w._restore_cfg(dict(flipped))
    rebuilt = w._build_cfg_from_ui()

    missing = []
    for k in enable_keys:
        if rebuilt.get(k) != flipped[k]:
            missing.append((k, f"기대 {flipped[k]} 실제 {rebuilt.get(k)}"))

    print(f"round-trip 감사 — 토글 {len(enable_keys)}개 뒤집기→복원→재빌드 대조")
    if missing:
        print(f"\n❌ 복원 반영 안 됨 {len(missing)}개 (시나리오 로드 시 초기화되는 실제 버그):")
        for k, d in missing:
            print(f"  {k}: {d}")
        return 1
    print("\n✅ PASS — 모든 토글이 복원 후 값 그대로 반영(복원 누락 0)")
    return 0


if __name__ == '__main__':
    sys.exit(main())
