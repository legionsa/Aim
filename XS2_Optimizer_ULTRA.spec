# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['D:\\Users\\kalvi\\AppData\\Local\\Programs\\XS2\\Aim\\xs2_ultra.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['psutil', 'pystray', 'PIL', 'keyboard', 'win32api', 'win32con'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='XS2_Optimizer_ULTRA',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
