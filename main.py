"""
Snip OCR - Screenshot to Markdown Converter

A system tray application that captures screen regions and converts them
to Markdown using AI-powered OCR with LaTeX support.

Usage:
    Press Ctrl+Shift+S to capture a screen region.
    The extracted Markdown is automatically copied to clipboard.
"""

from __future__ import annotations

import logging
import os
import sys

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)


def main() -> None:
    """Application entry point."""
    # Disable Qt's High DPI scaling to ensure 1:1 pixel mapping
    # This prevents coordinate mismatches on multi-monitor setups with different scaling
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
    os.environ["QT_SCALE_FACTOR"] = "1"

    from snip_ocr.manager import Manager

    sys.exit(Manager().run())


if __name__ == "__main__":
    main()
