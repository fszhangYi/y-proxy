# -*- mode: python ; coding: utf-8 -*-
"""Linux onedir PyInstaller spec for Y-Proxy (Ubuntu 20.04 / AppImage)."""

from __future__ import annotations

from pathlib import Path

from PyInstaller.building.api import COLLECT, EXE, PYZ
from PyInstaller.building.build_main import Analysis
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

SPECPATH = Path(SPECPATH).resolve()  # noqa: F821 — dir containing this .spec
ROOT = SPECPATH.parent  # y-proxy/
APP_NAME = "Y-Proxy"

hidden = collect_submodules("qfluentwidgets") + collect_submodules("app")
hidden += [
    "PyQt6",
    "PyQt6.QtCore",
    "PyQt6.QtGui",
    "PyQt6.QtWidgets",
    "PyQt6.QtSvg",
    "PyQt6.QtNetwork",
    "darkdetect",
]

datas = []
try:
    datas += collect_data_files("qfluentwidgets")
except Exception:
    pass
try:
    datas += collect_data_files("qframelesswindow")
except Exception:
    pass

a = Analysis(
    [str(ROOT / "run_app.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(SPECPATH / "rthook_linux_qt.py")],
    excludes=[
        "tkinter",
        "matplotlib",
        "numpy",
        "pandas",
        "PyQt6.QtWebEngine",
        "PyQt6.QtWebEngineCore",
        "PyQt6.QtWebEngineWidgets",
        "PyQt6.QtBluetooth",
        "PyQt6.QtMultimedia",
        "PyQt6.QtMultimediaWidgets",
        "PyQt6.QtPositioning",
        "PyQt6.QtSensors",
        "PyQt6.QtTest",
    ],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    contents_directory=".",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    name=APP_NAME,
    strip=False,
    upx=False,
)
