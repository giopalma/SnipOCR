"""Automatic update checker and installer for SnipOCR."""

from __future__ import annotations

import logging
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

import requests

from . import __commit__
from .constants import GITHUB_REPO_NAME, GITHUB_REPO_OWNER

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class UpdateChecker:
    """Checks for application updates from GitHub releases."""

    def __init__(self) -> None:
        """Initialize the update checker."""
        self.current_commit = __commit__
        self.latest_version: str | None = None
        self.latest_commit: str | None = None
        self.download_url: str | None = None
        self.release_notes: str | None = None

    def check_for_updates(self) -> bool:
        """Check if a new version is available.

        Returns:
            True if an update is available, False otherwise.
        """
        try:
            # Try to get the latest non-prerelease first
            url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/releases/latest"

            response = requests.get(url, timeout=10)
            
            # If /latest returns 404, it might be because only prereleases exist
            # Try to get the first release from the list instead
            if response.status_code == 404:
                url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/releases"
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                releases = response.json()
                
                if not releases:
                    logger.info(
                        "No releases found in repository. Update checking will work "
                        "once the first release is published."
                    )
                    return False
                
                # Get the first release (most recent)
                release_data = releases[0]
            else:
                response.raise_for_status()
                release_data = response.json()
            
            self.latest_version = release_data.get("tag_name", "").lstrip("v")
            self.release_notes = release_data.get("body") or ""
            self.latest_commit = self._extract_commit_sha(self.release_notes)
            if not self.latest_commit:
                self.latest_commit = self._extract_commit_sha_from_target(
                    release_data.get("target_commitish")
                )

            # Find the appropriate asset for the current platform
            assets = release_data.get("assets", [])
            for asset in assets:
                name = asset.get("name", "").lower()
                if (sys.platform == "win32" and name.endswith((".exe", ".msi"))) or (
                    sys.platform == "darwin" and name.endswith(".dmg")
                ):
                    self.download_url = asset.get("browser_download_url")
                    break

            # Compare commits
            if self.latest_commit and self._is_newer_commit(
                self.latest_commit, self.current_commit
            ):
                logger.info(
                    "Update available: %s -> %s", self.current_commit, self.latest_commit
                )
                return True

            logger.info(
                "No updates available. Current commit: %s", self.current_commit
            )
            return False

        except requests.exceptions.HTTPError as e:
            logger.warning(f"Failed to check for updates: {e}")
            return False
        except Exception as e:
            logger.warning(f"Failed to check for updates: {e}")
            return False

    def _is_newer_commit(self, latest: str, current: str) -> bool:
        """Compare commit hashes.

        Args:
            latest: Latest commit hash (e.g., "f8f53f1...").
            current: Current commit hash (e.g., "a1b2c3d...").

        Returns:
            True if the commit hashes differ or current is unknown.
        """
        if not current or current == "unknown":
            logger.info("Current commit unknown; treating latest as update.")
            return bool(latest)
        return latest != current

    def _extract_commit_sha(self, body: str) -> str | None:
        """Extract commit hash from release notes."""
        for line in body.splitlines():
            if "Built from commit:" in line:
                result = line.split("Built from commit:", 1)[1].strip()
                return result if result else None
        return None

    def _extract_commit_sha_from_target(self, target: object) -> str | None:
        """Extract commit hash from target_commitish when it looks like a SHA."""
        if isinstance(target, str) and len(target) >= 7 and all(
            ch in "0123456789abcdef" for ch in target.lower()
        ):
            return target
        return None

    def download_update(self, progress_callback=None) -> Path | None:
        """Download the update file.

        Args:
            progress_callback: Optional callback function(bytes_downloaded,
                total_bytes).

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
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
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
                # On Windows, launch the installer without shell=True for security
                subprocess.Popen([str(update_file)])
                return True
            elif sys.platform == "darwin":
                # On macOS, open the DMG
                subprocess.Popen(["open", str(update_file)])
                return True
            else:
                logger.warning(
                    f"Auto-update not supported on platform: {sys.platform}"
                )
                return False
        except Exception as e:
            logger.error(f"Failed to install update: {e}")
            return False
