"""Automatic update checker and installer for SnipOCR."""

from __future__ import annotations

import json
import logging
import sys
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import requests

from . import __version__
from .constants import GITHUB_REPO_NAME, GITHUB_REPO_OWNER

if TYPE_CHECKING:
    from typing import Dict, Optional

logger = logging.getLogger(__name__)


class UpdateChecker:
    """Checks for application updates from GitHub releases."""

    def __init__(self) -> None:
        """Initialize the update checker."""
        self.current_version = __version__
        self.latest_version: str | None = None
        self.download_url: str | None = None
        self.release_notes: str | None = None

    def check_for_updates(self) -> bool:
        """Check if a new version is available.

        Returns:
            True if an update is available, False otherwise.
        """
        try:
            # GitHub API endpoint for latest release
            url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/releases/latest"
            
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            
            release_data = response.json()
            self.latest_version = release_data.get("tag_name", "").lstrip("v")
            self.release_notes = release_data.get("body", "")
            
            # Find the appropriate asset for the current platform
            assets = release_data.get("assets", [])
            for asset in assets:
                name = asset.get("name", "").lower()
                if sys.platform == "win32" and name.endswith((".exe", ".msi")):
                    self.download_url = asset.get("browser_download_url")
                    break
                elif sys.platform == "darwin" and name.endswith(".dmg"):
                    self.download_url = asset.get("browser_download_url")
                    break
            
            # Compare versions
            if self.latest_version and self._is_newer_version(self.latest_version, self.current_version):
                logger.info(f"Update available: {self.current_version} -> {self.latest_version}")
                return True
            
            logger.info(f"No updates available. Current version: {self.current_version}")
            return False
            
        except Exception as e:
            logger.warning(f"Failed to check for updates: {e}")
            return False

    def _is_newer_version(self, latest: str, current: str) -> bool:
        """Compare version strings.

        Args:
            latest: Latest version string (e.g., "0.2.0").
            current: Current version string (e.g., "0.1.0").

        Returns:
            True if latest is newer than current.
        """
        try:
            # Simple version comparison for semver
            latest_parts = [int(x) for x in latest.split(".")]
            current_parts = [int(x) for x in current.split(".")]
            
            # Pad to same length
            max_len = max(len(latest_parts), len(current_parts))
            latest_parts += [0] * (max_len - len(latest_parts))
            current_parts += [0] * (max_len - len(current_parts))
            
            return latest_parts > current_parts
        except (ValueError, AttributeError):
            return False

    def download_update(self, progress_callback=None) -> Path | None:
        """Download the update file.

        Args:
            progress_callback: Optional callback function(bytes_downloaded, total_bytes).

        Returns:
            Path to the downloaded file, or None if download failed.
        """
        if not self.download_url:
            logger.error("No download URL available")
            return None

        try:
            response = requests.get(self.download_url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get("content-length", 0))
            
            # Create temporary file
            suffix = ".exe" if sys.platform == "win32" else ".dmg"
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
            temp_path = Path(temp_file.name)
            
            downloaded = 0
            with open(temp_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback:
                            progress_callback(downloaded, total_size)
            
            logger.info(f"Update downloaded to: {temp_path}")
            return temp_path
            
        except Exception as e:
            logger.error(f"Failed to download update: {e}")
            return None

    def install_update(self, update_file: Path) -> bool:
        """Install the downloaded update.

        Args:
            update_file: Path to the downloaded installer.

        Returns:
            True if installation started successfully.
        """
        try:
            if sys.platform == "win32":
                # On Windows, launch the installer
                import subprocess
                subprocess.Popen([str(update_file)], shell=True)
                return True
            elif sys.platform == "darwin":
                # On macOS, open the DMG
                import subprocess
                subprocess.Popen(["open", str(update_file)])
                return True
            else:
                logger.warning(f"Auto-update not supported on platform: {sys.platform}")
                return False
        except Exception as e:
            logger.error(f"Failed to install update: {e}")
            return False
