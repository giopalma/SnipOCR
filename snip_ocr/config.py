"""Configuration management for SnipOCR application."""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path

from .constants import APP_NAME

logger = logging.getLogger(__name__)


def get_config_path() -> Path:
    """Get the path to the config directory.

    Returns:
        Path to %APPDATA%/SnipOCR/ on Windows.
    """
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base = Path.home() / ".config"
    config_dir = base / APP_NAME
    config_dir.mkdir(parents=True, exist_ok=True)
    return config_dir


def load_token() -> str | None:
    """Load the GitHub token from config file.

    Returns:
        The token string if found, None otherwise.
    """
    config_file = get_config_path() / "config.json"
    if config_file.exists():
        try:
            with config_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("github_token")
        except (json.JSONDecodeError, OSError):
            pass
    return None


def save_config(token: str | None = None, model: str | None = None) -> bool:
    """Save configuration to config file.

    Args:
        token: The GitHub token to save (optional).
        model: The model name to save (optional).

    Returns:
        True if saved successfully, False otherwise.
    """
    config_file = get_config_path() / "config.json"
    try:
        data = {}
        if config_file.exists():
            with config_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
        if token is not None:
            data["github_token"] = token
        if model is not None:
            data["model"] = model
        with config_file.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return True
    except (json.JSONDecodeError, OSError):
        return False


def load_model() -> str:
    """Load the model choice from config file.

    Returns:
        The model name, defaults to 'gpt-4o'.
    """
    config_file = get_config_path() / "config.json"
    if config_file.exists():
        try:
            with config_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("model", "gpt-4o")
        except (json.JSONDecodeError, OSError):
            pass
    return "gpt-4o"
