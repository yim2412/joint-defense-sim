# -*- mode: python ; coding: utf-8 -*-
# launcher.spec — 이지스 기동전단 시뮬레이터 PyInstaller 빌드 설정
# onedir 모드: subprocess 워커가 번들 재압축해제 없이 즉시 import 가능

import os

block_cipher = None

a = Analysis(
    ['launcher.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('engine.py',      '.'),
        ('engine_v7.py',   '.'),
        ('anim_render.py', '.'),
        ('spec_db.py',     '.'),
        ('changelog.json', '.'),
        ('aegis_icon.ico', '.'),
        ('assets/images',  'assets/images'),
    ],
    hiddenimports=[
        # PyQt6 core
        'PyQt6',
        'PyQt6.QtWidgets',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
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
    name='이지스_기동전단_시뮬레이터',
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
    icon='aegis_icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='이지스_기동전단_시뮬레이터',
)
