# -*- mode: python ; coding: utf-8 -*-
"""Windows onefile PyInstaller spec for Y-Proxy (official CPython only)."""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

from PyInstaller.building.api import EXE, PYZ
from PyInstaller.building.build_main import Analysis
from PyInstaller.building.datastruct import TOC
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

SPECPATH = Path(SPECPATH).resolve()  # noqa: F821 — dir containing this .spec
ROOT = SPECPATH.parent  # y-proxy/
APP_NAME = "Y-Proxy"
STAMP = datetime.now().strftime("%Y%m%d-%H%M%S")
ICON = SPECPATH / "y-proxy.ico"

_prefix = sys.base_prefix.lower().replace("/", "\\")
if any(x in _prefix for x in ("\\miniconda", "\\anaconda", "\\conda\\")):
    raise SystemExit(f"Refuse conda interpreter: {sys.base_prefix}")

hidden = collect_submodules("qfluentwidgets") + collect_submodules("app")
hidden += [
    "PyQt6",
    "PyQt6.QtCore",
    "PyQt6.QtGui",
    "PyQt6.QtWidgets",
    "PyQt6.QtSvg",
    "PyQt6.QtNetwork",
    "darkdetect",
    "qframelesswindow",
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
    runtime_hooks=[str(SPECPATH / "rthook_dll.py")],
    excludes=[
        "tkinter",
        "matplotlib",
        "numpy",
        "pandas",
        "PyQt6.QtWebEngine",
        "PyQt6.QtWebEngineCore",
        "PyQt6.QtWebEngineWidgets",
        "PyQt6.QtBluetooth",
        "PyQt6.QtNfc",
        "PyQt6.QtMultimedia",
        "PyQt6.QtMultimediaWidgets",
        "PyQt6.QtPositioning",
        "PyQt6.QtLocation",
        "PyQt6.QtSensors",
        "PyQt6.QtSerialPort",
        "PyQt6.QtTest",
    ],
    noarchive=False,
)


def _ship(item) -> bool:
    name = item[0].replace("\\", "/").rsplit("/", 1)[-1].lower()
    src = (item[1] if len(item) > 1 else "").replace("\\", "/").lower()
    if name.startswith("api-ms-win-") or name == "ucrtbase.dll":
        return False
    if any(part in src for part in ("miniconda", "anaconda", "/conda/")):
        return False
    return True


a.binaries = TOC([item for item in a.binaries if _ship(item)])
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=f"{APP_NAME}-{STAMP}",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    exclude_binaries=False,
    icon=str(ICON) if ICON.is_file() else None,
)
