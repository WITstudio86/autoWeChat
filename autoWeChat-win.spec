# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

root = Path(SPECPATH)  # SPECPATH = directory of this .spec file

a = Analysis(
    [str(root / "run.py")],
    pathex=[str(root)],
    binaries=[],
    datas=[
        (str(root / "app" / "templates"), "app/templates"),
        (str(root / "app" / "static"), "app/static"),
        (str(root / "VERSION"), "."),
    ],
    hiddenimports=[
        "app",
        "app.config",
        "app.api_client",
        "app.middleware",
        "app.routes",
        "app.routes.auth",
        "app.routes.admin",
        "app.routes.dashboard",
        "app.routes.courses",
        "app.routes.students",
        "app.routes.templates",
        "app.routes.send",
        "app.routes.public",
        "app.services",
        "app.services.ai_generator",
        "app.services.message_renderer",
        "app.services.screenshot",
        "app.services.wechat_sender",
        "app.gui",
        "app.update_checker",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["matplotlib", "numpy", "pandas"],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="autoWeChat",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # --windowed: no terminal window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,  # auto-detect (x86_64 or arm64)
    codesign_identity=None,
    entitlements_file=None,
    icon=str(root / "logo.ico") if (root / "logo.ico").exists() else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="autoWeChat",
)
