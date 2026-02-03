# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('src', 'src'), ('assets', 'assets'), ('i18n', 'i18n'), ('icons', 'icons'), ('configs', 'configs')],
    hiddenimports=['uuid', 'uuid._uuid', 'PySide6', 'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets', 'qfluentwidgets', 'cv2', 'numpy', 'onnxruntime', 'scikit-learn', 'scipy', 'pillow', 'pkg_resources', 'pkgutil', 'importlib.metadata', 'importlib_metadata', 'packaging', 'packaging.version', 'sqlite3'],
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
    name='ok-QRSL',
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
    icon=['icons\\icon.png'],
)
