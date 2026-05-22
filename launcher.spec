# -*- mode: python ; coding: utf-8 -*-
# launcher.spec — 이지스 기동전단 시뮬레이터 PyInstaller 빌드 설정

import os

block_cipher = None

a = Analysis(
    ['launcher.py'],
    pathex=['.'],
    binaries=[],
    datas=[
        ('engine.py',      '.'),
        ('engine_v7.py',   '.'),
        ('changelog.json', '.'),
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
        # matplotlib internals (자동 감지 실패 방지)
        'matplotlib.figure',
        'matplotlib.lines',
        'matplotlib.patches',
        'matplotlib.collections',
        # numpy / scipy / openpyxl
        'numpy',
        'numpy.core._multiarray_umath',
        'scipy',
        'scipy.stats',
        'openpyxl',
        'openpyxl.styles',
        'openpyxl.drawing.image',
        # psutil
        'psutil',
        # 기타 stdlib
        'json', 'math', 'random', 'copy', 'dataclasses',
        'collections', 'itertools', 'threading', 'time',
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='이지스_기동전단_시뮬레이터',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,          # GUI 앱 — 콘솔 창 숨김
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon=None,            # 아이콘 없을 경우 주석 유지
)
