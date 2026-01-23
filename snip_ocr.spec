# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for Snip OCR - Cross-platform."""

import sys

# Platform-specific configuration
if sys.platform == 'darwin':
    # macOS
    hidden_imports = [
        'pynput.keyboard._darwin',
        'pynput.mouse._darwin',
    ]
    icon_file = 'icon.png'  # macOS can use PNG, or use .icns if available
elif sys.platform == 'win32':
    # Windows
    hidden_imports = [
        'pynput.keyboard._win32',
        'pynput.mouse._win32',
    ]
    icon_file = 'icon.ico'
else:
    # Linux
    hidden_imports = [
        'pynput.keyboard._xorg',
        'pynput.mouse._xorg',
    ]
    icon_file = 'icon.png'

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[('icon.png', '.')],
    hiddenimports=hidden_imports,
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
    name='SnipOCR',
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
    icon=icon_file,
)

# macOS app bundle (only created on macOS)
if sys.platform == 'darwin':
    app = BUNDLE(
        exe,
        name='SnipOCR.app',
        icon='icon.png',
        bundle_identifier='com.giopalma.snipocr',
        info_plist={
            'CFBundleName': 'SnipOCR',
            'CFBundleDisplayName': 'Snip OCR',
            'CFBundleVersion': '0.1.0',
            'CFBundleShortVersionString': '0.1.0',
            'NSHighResolutionCapable': True,
            'LSUIElement': True,  # Hide from Dock (menu bar app)
        },
    )
