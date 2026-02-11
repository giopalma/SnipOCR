"""Settings dialog for SnipOCR configuration."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtCore import QObject, Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from ..config import load_model, load_token, save_config
from ..constants import APP_DISPLAY_NAME, AVAILABLE_MODELS, LOCAL_MODEL_NAME
from ..icon_utils import get_icon
from ..model_downloader import (
    delete_models,
    format_size,
    get_model_size,
    is_model_downloaded,
)

if TYPE_CHECKING:
    from ..updater import UpdateChecker


class ModelDownloadWorker(QThread):
    """Background thread for downloading models."""

    progress = pyqtSignal(int, int)  # current, total
    finished = pyqtSignal(bool)  # success
    error = pyqtSignal(str)  # error message

    def run(self) -> None:
        """Download models in background thread."""
        try:
            from ..model_downloader import download_models

            success = download_models(
                progress_callback=lambda current, total: self.progress.emit(
                    current, total
                )
            )
            self.finished.emit(success)
        except Exception as e:
            self.error.emit(str(e))
            self.finished.emit(False)


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
            self.error.emit(str(e))


class SettingsDialog(QDialog):
    """Comprehensive settings dialog with tabs for all configuration.

    Provides tabs for OCR model configuration, update management, and general settings.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        update_checker: UpdateChecker | None = None,
    ) -> None:
        """Initialize the settings dialog.

        Args:
            parent: Optional parent widget.
            update_checker: Optional UpdateChecker instance for updates tab.
        """
        super().__init__(parent)
        icon = get_icon()
        if icon:
            self.setWindowIcon(icon)
        self.setWindowTitle(f"{APP_DISPLAY_NAME} - Settings")
        self.setMinimumWidth(550)
        self.setMinimumHeight(400)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        self.update_checker = update_checker
        self.update_file: Path | None = None
        self.download_thread: QThread | None = None
        self.update_download_thread: QThread | None = None

        # Create main layout
        main_layout = QVBoxLayout(self)

        # Create tab widget
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Create tabs
        self._create_model_tab()
        self._create_updates_tab()

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        main_layout.addWidget(buttons)

    def _create_model_tab(self) -> None:
        """Create the OCR Model configuration tab."""
        model_tab = QWidget()
        layout = QVBoxLayout(model_tab)

        # Model selection group
        model_group = QGroupBox("OCR Model Selection")
        model_layout = QFormLayout()

        # Model dropdown
        self.model_combo = QComboBox()
        self.model_combo.addItems(AVAILABLE_MODELS)
        current_model = load_model()
        if current_model in AVAILABLE_MODELS:
            self.model_combo.setCurrentText(current_model)
        model_layout.addRow("Model:", self.model_combo)

        # GitHub Token
        self.token_input = QLineEdit()
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.token_input.setPlaceholderText("ghp_xxxxxxxxxxxx")
        current_token = load_token()
        if current_token:
            self.token_input.setText(current_token)
        model_layout.addRow("GitHub Token:", self.token_input)

        # Info label
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("color: gray;")
        model_layout.addRow("", self.info_label)

        model_group.setLayout(model_layout)
        layout.addWidget(model_group)

        # Local model management group
        self.local_model_group = QGroupBox("Local Model Management")
        local_layout = QVBoxLayout()

        # Status label
        self.model_status_label = QLabel()
        self.model_status_label.setWordWrap(True)
        local_layout.addWidget(self.model_status_label)

        # Size label
        self.model_size_label = QLabel()
        local_layout.addWidget(self.model_size_label)

        # Progress bar
        self.model_progress_bar = QProgressBar()
        self.model_progress_bar.setVisible(False)
        local_layout.addWidget(self.model_progress_bar)

        # Buttons
        self.download_button = QPushButton("Download Models")
        self.download_button.clicked.connect(self._on_download_models)
        local_layout.addWidget(self.download_button)

        self.delete_button = QPushButton("Delete Models")
        self.delete_button.clicked.connect(self._on_delete_models)
        local_layout.addWidget(self.delete_button)

        # Info text
        info_text = QLabel(
            "Local models enable offline OCR (~150 MB download required).\n"
            "Models include text detection, recognition, and angle correction."
        )
        info_text.setWordWrap(True)
        info_text.setStyleSheet("color: gray; font-size: 9pt;")
        local_layout.addWidget(info_text)

        self.local_model_group.setLayout(local_layout)
        layout.addWidget(self.local_model_group)

        self._update_model_status()

        # Connect signal AFTER all widgets are created
        self.model_combo.currentTextChanged.connect(self._on_model_changed)
        # Set initial visibility based on current model
        self._on_model_changed(current_model)

        layout.addStretch()
        self.tabs.addTab(model_tab, "OCR Model")

    def _create_updates_tab(self) -> None:
        """Create the Updates tab."""
        updates_tab = QWidget()
        layout = QVBoxLayout(updates_tab)

        # Update info group
        info_group = QGroupBox("Application Updates")
        info_layout = QVBoxLayout()

        # Current version
        from .. import __commit__

        current_commit = __commit__ if __commit__ else "Unknown"
        self.current_version_label = QLabel(
            f"<b>Current Version:</b> {current_commit[:7]}"
        )
        info_layout.addWidget(self.current_version_label)

        # Available version
        self.available_version_label = QLabel("<b>Status:</b> Checking...")
        info_layout.addWidget(self.available_version_label)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # Update actions group
        actions_group = QGroupBox("Update Actions")
        actions_layout = QVBoxLayout()

        # Check button
        self.check_updates_button = QPushButton("Check for Updates")
        self.check_updates_button.clicked.connect(self._on_check_updates)
        actions_layout.addWidget(self.check_updates_button)

        # Progress bar
        self.update_progress_bar = QProgressBar()
        self.update_progress_bar.setVisible(False)
        actions_layout.addWidget(self.update_progress_bar)

        # Status label
        self.update_status_label = QLabel()
        self.update_status_label.setWordWrap(True)
        actions_layout.addWidget(self.update_status_label)

        # Download/Install button
        self.download_update_button = QPushButton("Download and Install Update")
        self.download_update_button.setVisible(False)
        self.download_update_button.clicked.connect(self._on_download_update)
        actions_layout.addWidget(self.download_update_button)

        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)

        layout.addStretch()
        self.tabs.addTab(updates_tab, "Updates")

        # Initial check if update_checker provided
        if self.update_checker:
            self._check_for_updates()

    def _on_model_changed(self, model: str) -> None:
        """Handle model selection change.

        Args:
            model: Selected model name.
        """
        if model == LOCAL_MODEL_NAME:
            self.info_label.setText("ℹ️ No API key required for local model")
            self.token_input.setEnabled(False)
            self.local_model_group.setVisible(True)
        else:
            self.info_label.setText("ℹ️ API key required for cloud models")
            self.token_input.setEnabled(True)
            self.local_model_group.setVisible(False)

    def _update_model_status(self) -> None:
        """Update the local model status display."""
        if is_model_downloaded():
            self.model_status_label.setText(
                "✅ <b>Models Downloaded</b><br>Local OCR is ready to use."
            )
            self.model_status_label.setStyleSheet("color: green;")
            self.download_button.setEnabled(False)
            self.delete_button.setEnabled(True)

            size = get_model_size()
            self.model_size_label.setText(f"Models size: {format_size(size)}")
        else:
            self.model_status_label.setText(
                "⚠️ <b>Models Not Downloaded</b><br>"
                "Download models to use local OCR."
            )
            self.model_status_label.setStyleSheet("color: orange;")
            self.download_button.setEnabled(True)
            self.delete_button.setEnabled(False)
            self.model_size_label.setText("")

    def _on_download_models(self) -> None:
        """Handle model download button click."""
        reply = QMessageBox.question(
            self,
            "Download Models",
            "This will download ~150 MB of OCR models.\nDo you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        self.download_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        self.model_progress_bar.setVisible(True)
        self.model_progress_bar.setValue(0)
        self.model_status_label.setText("Downloading models...")
        self.model_status_label.setStyleSheet("")

        self.download_thread = ModelDownloadWorker()
        self.download_thread.progress.connect(self._on_model_progress)
        self.download_thread.finished.connect(self._on_model_download_finished)
        self.download_thread.error.connect(self._on_model_download_error)
        self.download_thread.start()

    def _on_model_progress(self, current: int, total: int) -> None:
        """Handle model download progress.

        Args:
            current: Current progress value.
            total: Total progress value.
        """
        if total > 0:
            percentage = (current * 100) // total
            self.model_progress_bar.setValue(percentage)

    def _on_model_download_finished(self, success: bool) -> None:
        """Handle model download completion.

        Args:
            success: Whether download was successful.
        """
        self.model_progress_bar.setVisible(False)

        if success:
            QMessageBox.information(
                self,
                "Download Complete",
                "Models downloaded successfully!\nYou can now use local OCR.",
            )
        else:
            QMessageBox.warning(
                self,
                "Download Failed",
                "Failed to download models.\n"
                "Please check your internet connection and try again.",
            )

        self._update_model_status()

    def _on_model_download_error(self, error_msg: str) -> None:
        """Handle model download error.

        Args:
            error_msg: Error message.
        """
        self.model_progress_bar.setVisible(False)
        QMessageBox.critical(
            self, "Download Error", f"An error occurred:\n{error_msg}"
        )
        self._update_model_status()

    def _on_delete_models(self) -> None:
        """Handle model deletion button click."""
        reply = QMessageBox.question(
            self,
            "Delete Models",
            "This will delete downloaded models.\n"
            "You will need to download them again to use local OCR.\n"
            "Do you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        if delete_models():
            QMessageBox.information(
                self, "Models Deleted", "Models deleted successfully."
            )
        else:
            QMessageBox.warning(self, "Delete Failed", "Failed to delete models.")

        self._update_model_status()

    def _check_for_updates(self) -> None:
        """Check for updates silently."""
        if not self.update_checker:
            self.available_version_label.setText(
                "<b>Status:</b> Update checker not available"
            )
            return

        try:
            if self.update_checker.check_for_updates():
                commit = self.update_checker.latest_commit
                if commit:
                    commit = commit[:7]
                self.available_version_label.setText(
                    f"<b>Available Version:</b> {commit}<br>"
                    "<b>Status:</b> ✅ Update available!"
                )
                self.available_version_label.setStyleSheet("color: green;")
                self.download_update_button.setVisible(True)
            else:
                self.available_version_label.setText(
                    "<b>Status:</b> ✅ You are up to date"
                )
                self.available_version_label.setStyleSheet("color: green;")
                self.download_update_button.setVisible(False)
        except Exception as e:
            self.available_version_label.setText(
                f"<b>Status:</b> ⚠️ Check failed: {str(e)}"
            )
            self.available_version_label.setStyleSheet("color: orange;")

    def _on_check_updates(self) -> None:
        """Handle check for updates button click."""
        self.check_updates_button.setEnabled(False)
        self.available_version_label.setText("<b>Status:</b> Checking...")
        self.available_version_label.setStyleSheet("")

        try:
            self._check_for_updates()
        finally:
            self.check_updates_button.setEnabled(True)

    def _on_download_update(self) -> None:
        """Handle download update button click."""
        if not self.update_checker:
            return

        reply = QMessageBox.question(
            self,
            "Download Update",
            "This will download and install the latest version.\n"
            "Do you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply != QMessageBox.StandardButton.Yes:
            return

        self.download_update_button.setEnabled(False)
        self.check_updates_button.setEnabled(False)
        self.update_progress_bar.setVisible(True)
        self.update_progress_bar.setValue(0)
        self.update_status_label.setText("Downloading update...")

        self.update_download_thread = QThread()
        self.update_downloader = UpdateDownloader(self.update_checker)
        self.update_downloader.moveToThread(self.update_download_thread)

        self.update_download_thread.started.connect(self.update_downloader.run)
        self.update_downloader.progress.connect(self._on_update_progress)
        self.update_downloader.finished.connect(self._on_update_download_finished)
        self.update_downloader.error.connect(self._on_update_download_error)

        self.update_downloader.finished.connect(self.update_download_thread.quit)
        self.update_downloader.error.connect(self.update_download_thread.quit)
        self.update_download_thread.finished.connect(
            self.update_downloader.deleteLater
        )
        self.update_download_thread.finished.connect(
            self.update_download_thread.deleteLater
        )

        self.update_download_thread.start()

    def _on_update_progress(self, downloaded: int, total: int) -> None:
        """Handle update download progress.

        Args:
            downloaded: Bytes downloaded.
            total: Total bytes.
        """
        if total > 0:
            percentage = int((downloaded / total) * 100)
            self.update_progress_bar.setValue(percentage)
            downloaded_mb = downloaded / (1024 * 1024)
            total_mb = total / (1024 * 1024)
            self.update_status_label.setText(
                f"Downloaded: {downloaded_mb:.1f} MB / {total_mb:.1f} MB"
            )

    def _on_update_download_finished(self, update_file: Path | None) -> None:
        """Handle update download completion.

        Args:
            update_file: Path to downloaded file or None.
        """
        self.update_progress_bar.setVisible(False)

        if update_file:
            self.update_file = update_file
            reply = QMessageBox.question(
                self,
                "Install Update",
                "Update downloaded successfully!\n"
                "Do you want to install it now?\n\n"
                "The application will close and the installer will start.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )

            if reply == QMessageBox.StandardButton.Yes:
                if self.update_checker.install_update(update_file):
                    self.update_status_label.setText(
                        "Installing... The application will close."
                    )
                    self.accept()  # Close with Accept to signal installation
                else:
                    QMessageBox.warning(
                        self,
                        "Installation Failed",
                        "Failed to start installer.\n"
                        "Please install manually from the downloaded file.",
                    )
        else:
            QMessageBox.warning(
                self, "Download Failed", "Failed to download update."
            )

        self.download_update_button.setEnabled(True)
        self.check_updates_button.setEnabled(True)

    def _on_update_download_error(self, error_msg: str) -> None:
        """Handle update download error.

        Args:
            error_msg: Error message.
        """
        self.update_progress_bar.setVisible(False)
        QMessageBox.critical(
            self, "Download Error", f"An error occurred:\n{error_msg}"
        )
        self.download_update_button.setEnabled(True)
        self.check_updates_button.setEnabled(True)

    def _on_save(self) -> None:
        """Handle save button click."""
        token = self.token_input.text().strip()
        model = self.model_combo.currentText()

        # Token is not required for local model
        if not token and model != LOCAL_MODEL_NAME:
            QMessageBox.warning(
                self,
                "Invalid Token",
                "Please enter a valid GitHub token for cloud models.",
            )
            return

        if save_config(token=token if token else None, model=model):
            self.accept()
        else:
            QMessageBox.critical(
                self,
                "Error",
                "Failed to save settings. Please check permissions.",
            )

    def get_token(self) -> str:
        """Get the configured token.

        Returns:
            The token string.
        """
        return self.token_input.text().strip()

    def get_model(self) -> str:
        """Get the selected model.

        Returns:
            The model name.
        """
        return self.model_combo.currentText()
