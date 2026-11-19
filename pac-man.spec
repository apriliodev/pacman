# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec of the packaged game.  Build with:  make package
# (the result is in dist/pac-man/, ready to be zipped and uploaded).

a = Analysis(
    ['packaging_launcher.py'],
    pathex=['.'],
    binaries=[],
    datas=[('assets', 'assets'), ('config.json', '.')],
    hiddenimports=['mazegenerator'],
    hookspath=[],
    runtime_hooks=[],
    excludes=['pytest', 'mypy', 'flake8'],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='pac-man',
    debug=False,
    strip=False,
    upx=False,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='pac-man',
)
