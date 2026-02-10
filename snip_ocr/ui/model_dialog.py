"""Model management dialog for downloading and managing local OCR models."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..icon_utils import get_icon
from ..model_downloader import (
    delete_models,
    format_size,
    get_model_size,
    is_model_downloaded,
)

if TYPE_CHECKING:
    pass


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
                progress_callback=lambda current, total: self.progress.emit(current, total)
            )
            self.finished.emit(success)
        except Exception as e:
            self.error.emit(str(e))
            self.finished.emit(False)


class ModelDialog(QDialog):
    """Dialog for managing local OCR models.

    Provides interface to download, view status, and delete models.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the model management dialog.

        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent)
        icon = get_icon()
        if icon:
            self.setWindowIcon(icon)
        self.setWindowTitle("Local OCR Models")
        self.setMinimumWidth(500)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        self.download_thread: ModelDownloadWorker | None = None
        
        self._setup_ui()
        self._update_status()

    def _setup_ui(self) -> None:
        """Set up the user interface."""
        layout = QVBoxLayout(self)

        # Status label
        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        # Size label
        self.size_label = QLabel()
        layout.addWidget(self.size_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Download button
        self.download_button = QPushButton("Download Models")
        self.download_button.clicked.connect(self._on_download)
        layout.addWidget(self.download_button)

        # Delete button
        self.delete_button = QPushButton("Delete Models")
        self.delete_button.clicked.connect(self._on_delete)
        layout.addWidget(self.delete_button)

        # Info label
        info_label = QLabel(
            "Local OCR models enable offline text recognition.\n"
            "Download size: ~150-200 MB\n\n"
            "Models include:\n"
            "• Text detection and recognition\n"
            "• Table structure analysis\n"
            "• Mathematical formula support\n"
            "• Multi-language support"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: gray; font-size: 10pt;")
        layout.addWidget(info_label)

        # Close button
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _update_status(self) -> None:
        """Update the status display."""
        if is_model_downloaded():
            self.status_label.setText(
                "✅ <b>Models Downloaded</b><br>"
                "Local OCR is ready to use."
            )
            self.status_label.setStyleSheet("color: green;")
            self.download_button.setEnabled(False)
            self.delete_button.setEnabled(True)
            
            # Show model size
            size = get_model_size()
            self.size_label.setText(f"Models size: {format_size(size)}")
        else:
            self.status_label.setText(
                "⚠️ <b>Models Not Downloaded</b><br>"
                "Download models to use local OCR."
            )
            self.status_label.setStyleSheet("color: orange;")
            self.download_button.setEnabled(True)
            self.delete_button.setEnabled(False)
            self.size_label.setText("")

    def _on_download(self) -> None:
        """Handle download button click."""
        reply = QMessageBox.question(
            self,
            "Download Models",
            "This will download ~150-200 MB of OCR models.\n"
            "Do you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # Start download
        self.download_button.setEnabled(False)
        self.delete_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Downloading models...")
        self.status_label.setStyleSheet("color: blue;")
        
        self.download_thread = ModelDownloadWorker()
        self.download_thread.progress.connect(self._on_progress)
        self.download_thread.finished.connect(self._on_download_finished)
        self.download_thread.error.connect(self._on_download_error)
        self.download_thread.start()

    def _on_progress(self, current: int, total: int) -> None:
        """Handle download progress update.

        Args:
            current: Current progress value.
            total: Total progress value.
        """
        if total > 0:
            percentage = (current * 100) // total
            self.progress_bar.setValue(percentage)

    def _on_download_finished(self, success: bool) -> None:
        """Handle download completion.

        Args:
            success: Whether download was successful.
        """
        self.progress_bar.setVisible(False)
        
        if success:
            QMessageBox.information(
                self,
                "Download Complete",
                "Models downloaded successfully!\n"
                "You can now use local OCR.",
            )
        else:
            QMessageBox.warning(
                self,
                "Download Failed",
                "Failed to download models.\n"
                "Please check your internet connection and try again.",
            )
        
        self._update_status()

    def _on_download_error(self, error_msg: str) -> None:
        """Handle download error.

        Args:
            error_msg: Error message.
        """
        self.progress_bar.setVisible(False)
        QMessageBox.critical(
            self,
            "Download Error",
            f"An error occurred during download:\n{error_msg}",
        )
        self._update_status()

    def _on_delete(self) -> None:
        """Handle delete button click."""
        reply = QMessageBox.question(
            self,
            "Delete Models",
            "This will delete all downloaded models.\n"
            "You will need to download them again to use local OCR.\n"
            "Do you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        if delete_models():
            QMessageBox.information(
                self,
                "Models Deleted",
                "Models have been deleted successfully.",
            )
        else:
            QMessageBox.warning(
                self,
                "Delete Failed",
                "Failed to delete models.",
            )
        
        self._update_status()
