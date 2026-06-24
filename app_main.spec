# -*- mode: python ; coding: utf-8 -*-
# app_main.spec — 합동 통합방어 시뮬레이터 PyInstaller 빌드 설정
# onedir 모드: subprocess 워커가 번들 재압축해제 없이 즉시 import 가능

import os

block_cipher = None

a = Analysis(
    ['app_main.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('engine_core.py',              '.'),
        ('engine_combat.py',           '.'),
        ('db_specsheet.py',             '.'),
        ('app_changelog.json',         '.'),
        ('forecast_surrogate.json',  '.'),
        ('ai_rl_policy.npz',          '.'),
        ('jds_icon.ico',           '.'),
        ('db_ocean_acoustic.py',   '.'),
        ('db_ocean_environment.py','.'),
        ('db_terrain.py',          '.'),
        ('db_ground_threat.py',         '.'),
        ('assets/images',          'assets/images'),
        ('view_cesium_3d.html',       '.'),
    ],
    hiddenimports=[
        # RL 추론 모듈(app_main가 지연 import — 정적 분석 누락 방지). numpy만 의존.
        'ai_policy_infer',
        # PyQt6 core
        'PyQt6',
        'PyQt6.QtWidgets',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWebEngineWidgets',
        'PyQt6.QtWebEngineCore',
        'PyQt6.sip',
        # matplotlib Qt backend
        'matplotlib.backends.backend_qtagg',
        'matplotlib.backends.backend_qt',
        'matplotlib.backends.backend_agg',
        # matplotlib internals
        'matplotlib.figure',
        'matplotlib.lines',
        'matplotlib.patches',
        'matplotlib.collections',
        # numpy / scipy / openpyxl
        'numpy',
        'numpy.core._multiarray_umath',
        'scipy',
        'scipy.stats',
        'scipy.stats.qmc',
        'openpyxl',
        # SALib (Sobol 민감도 분석)
        'SALib',
        'SALib.sample',
        'SALib.sample.saltelli',
        'SALib.analyze',
        'SALib.analyze.sobol',
        'openpyxl.styles',
        'openpyxl.drawing.image',
        # psutil / wmi
        'psutil',
        'wmi',
        # 멀티프로세싱
        'multiprocessing',
        'multiprocessing.pool',
        'multiprocessing.spawn',
        'concurrent',
        'concurrent.futures',
        'concurrent.futures.process',
        # 기타 stdlib
        'json', 'io', 'math', 'random', 'copy', 'dataclasses',
        'collections', 'itertools', 'threading', 'time', 'subprocess',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter', '_tkinter',
        'wx', 'gtk',
        'PyQt5', 'PySide2', 'PySide6',
        'vispy', 'freetype',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,          # onedir: 바이너리/데이터 EXE에 포함 안 함
    name='합동_통합방어_시뮬레이터',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='jds_icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='합동_통합방어_시뮬레이터',
)
