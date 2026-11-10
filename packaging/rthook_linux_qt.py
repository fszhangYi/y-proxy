"""Runtime hook: point Qt at bundled plugins inside AppImage/onedir."""

from __future__ import annotations

import os
import sys
from pathlib import Path


if getattr(sys, "frozen", False):
    base = Path(sys._MEIPASS)
    for key in ("QT_PLUGIN_PATH", "QT_QPA_PLATFORM_PLUGIN_PATH", "PYTHONPATH", "PYTHONHOME"):
        os.environ.pop(key, None)

    candidates = [
        base / "PyQt6" / "Qt6" / "plugins",
        base / "qt6" / "plugins",
    ]
    for plugin_root in candidates:
        if plugin_root.is_dir():
            os.environ["QT_PLUGIN_PATH"] = str(plugin_root)
            platforms = plugin_root / "platforms"
            if platforms.is_dir():
                os.environ["QT_QPA_PLATFORM_PLUGIN_PATH"] = str(platforms)
            break

    # Prefer xcb; allow override from environment.
    os.environ.setdefault("QT_QPA_PLATFORM", "xcb")
