"""Update progress dialog."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import QObject, Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from ..constants import APP_DISPLAY_NAME

if TYPE_CHECKING:
    from ..updater import UpdateChecker

logger = logging.getLogger(__name__)


class UpdateDownloader(QObject):
    """Worker for downloading updates in background thread."""

    progress = pyqtSignal(int, int)  # bytes_downloaded, total_bytes
    finished = pyqtSignal(object)  # Path or None
    error = pyqtSignal(str)

    def __init__(self, update_checker: UpdateChecker) -> None:
        """Initialize the downloader.

        Args:
            update_checker: UpdateChecker instance with download info.
        """
        super().__init__()
        self.update_checker = update_checker

    def run(self) -> None:
        """Download the update file."""
        try:
            update_file = self.update_checker.download_update(
                progress_callback=lambda downloaded, total: self.progress.emit(
                    downloaded, total
                )
            )
            self.finished.emit(update_file)
        except Exception as e:
            logger.error(f"Update download failed: {e}")
            self.error.emit(str(e))


class UpdateDialog(QDialog):
    """Dialog showing update download and installation progress."""

    def __init__(
        self, update_checker: UpdateChecker, parent: QWidget | None = None
    ) -> None:
        """Initialize the update dialog.

        Args:
            update_checker: UpdateChecker instance with update info.
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self.update_checker = update_checker
        self.update_file: Path | None = None

        self.setWindowTitle(f"{APP_DISPLAY_NAME} - Update")
        self.setMinimumWidth(400)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        layout = QVBoxLayout(self)

        # Info label
        self.info_label = QLabel(
            f"Downloading update v{update_checker.latest_version}..."
        )
        layout.addWidget(self.info_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("Preparing download...")
        layout.addWidget(self.status_label)

        # Buttons
        self.buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Cancel)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)

        # Start download
        self._start_download()

    def _start_download(self) -> None:
        """Start the download process in a background thread."""
        self.thread = QThread()
        self.downloader = UpdateDownloader(self.update_checker)
        self.downloader.moveToThread(self.thread)

        self.thread.started.connect(self.downloader.run)
        self.downloader.progress.connect(self._on_progress)
        self.downloader.finished.connect(self._on_download_finished)
        self.downloader.error.connect(self._on_download_error)

        self.downloader.finished.connect(self.thread.quit)
        self.downloader.error.connect(self.thread.quit)
        self.thread.finished.connect(self.downloader.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def _on_progress(self, downloaded: int, total: int) -> None:
        """Update progress bar.

        Args:
            downloaded: Bytes downloaded so far.
            total: Total bytes to download.
        """
        if total > 0:
            percentage = int((downloaded / total) * 100)
            self.progress_bar.setValue(percentage)

            # Format sizes in MB
            downloaded_mb = downloaded / (1024 * 1024)
            total_mb = total / (1024 * 1024)
            self.status_label.setText(
                f"Downloaded: {downloaded_mb:.1f} MB / {total_mb:.1f} MB"
            )

    def _on_download_finished(self, update_file: Path | None) -> None:
        """Handle download completion.

        Args:
            update_file: Path to downloaded file, or None if failed.
        """
        if update_file:
            self.update_file = update_file
            self.info_label.setText("Download complete!")
            self.status_label.setText("Ready to install update.")

            # Replace Cancel with Install button
            self.buttons.clear()
            self.buttons.addButton(
                "Install Now", QDialogButtonBox.ButtonRole.AcceptRole
            )
            self.buttons.addButton(
                "Install Later", QDialogButtonBox.ButtonRole.RejectRole
            )

            self.buttons.accepted.connect(self._install_update)
            self.buttons.rejected.connect(self.reject)
        else:
            self.info_label.setText("Download failed!")
            self.status_label.setText("Please try again later.")
            self.buttons.clear()
            self.buttons.addButton(QDialogButtonBox.StandardButton.Close)
            self.buttons.rejected.connect(self.reject)

    def _on_download_error(self, error_msg: str) -> None:
        """Handle download error.

        Args:
            error_msg: Error message.
        """
        self.info_label.setText("Download error!")
        self.status_label.setText(error_msg)
        self.buttons.clear()
        self.buttons.addButton(QDialogButtonBox.StandardButton.Close)
        self.buttons.rejected.connect(self.reject)

    def _install_update(self) -> None:
        """Install the downloaded update."""
        if self.update_file:
            if self.update_checker.install_update(self.update_file):
                self.info_label.setText("Installing update...")
                self.status_label.setText(
                    "The installer will start. You can close this application."
                )
                self.accept()
            else:
                self.info_label.setText("Installation failed!")
                self.status_label.setText(
                    "Please install manually from the downloaded file."
                )
