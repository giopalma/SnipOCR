"""Utility helpers for application icons."""

from __future__ import annotations

import sys
from pathlib import Path

from PyQt6.QtGui import QIcon


def get_icon() -> QIcon | None:
    """Return the application icon if available."""
    icon_path = get_icon_path()
    if icon_path:
        return QIcon(str(icon_path))
    return None


def get_icon_path() -> Path | None:
    """Return the application icon path if available."""
    if getattr(sys, "frozen", False):
        base_path = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    else:
        base_path = Path(__file__).parent.parent

    icon_path = base_path / "icon.png"
    if icon_path.exists():
        return icon_path
    return None
