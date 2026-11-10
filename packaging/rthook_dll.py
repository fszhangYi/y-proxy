"""Runtime hook: fix DLL search path before PyQt6 import (Windows onefile)."""

from __future__ import annotations

import os
import sys
from pathlib import Path


def _load_library(path: Path) -> None:
    if not path.is_file():
        return
    import ctypes

    handle = ctypes.WinDLL(str(path))  # noqa: F841


if getattr(sys, "frozen", False):
    folder = Path(sys._MEIPASS)
    os.environ["PATH"] = str(folder) + os.pathsep + os.environ.get("PATH", "")
    if hasattr(os, "add_dll_directory"):
        os.add_dll_directory(str(folder))

    for key in (
        "QT_PLUGIN_PATH",
        "QT_QPA_PLATFORM_PLUGIN_PATH",
        "PYTHONPATH",
        "PYTHONHOME",
    ):
        os.environ.pop(key, None)
    for key in list(os.environ):
        if key.startswith("CONDA_"):
            os.environ.pop(key, None)

    if sys.platform.startswith("win"):
        for name in (
            "VCRUNTIME140.dll",
            "VCRUNTIME140_1.dll",
            "MSVCP140.dll",
            "MSVCP140_1.dll",
            "MSVCP140_2.dll",
        ):
            try:
                _load_library(folder / name)
            except OSError:
                pass

        # Prefer bundled Qt plugins when present.
        plugin_root = folder / "PyQt6" / "Qt6" / "plugins"
        if plugin_root.is_dir():
            os.environ["QT_PLUGIN_PATH"] = str(plugin_root)
            platforms = plugin_root / "platforms"
            if platforms.is_dir():
                os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(platforms)
