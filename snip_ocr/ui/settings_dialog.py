"""Settings dialog for SnipOCR configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QWidget,
)

from ..config import load_model, load_token, save_config
from ..constants import APP_DISPLAY_NAME, AVAILABLE_MODELS
from ..icon_utils import get_icon_path

if TYPE_CHECKING:
    pass


class SettingsDialog(QDialog):
    """Dialog for configuring application settings.

    Provides a form for the user to configure GitHub token and model.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize the settings dialog.

        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent)
        icon_path = get_icon_path()
        if icon_path:
            self.setWindowIcon(QIcon(str(icon_path)))
        self.setWindowTitle(f"{APP_DISPLAY_NAME} - Settings")
        self.setMinimumWidth(400)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        layout = QFormLayout(self)

        # Token input field
        self.token_input = QLineEdit()
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.token_input.setPlaceholderText("ghp_xxxxxxxxxxxx")

        # Load existing token if available
        current_token = load_token()
        if current_token:
            self.token_input.setText(current_token)

        layout.addRow("GitHub Token:", self.token_input)

        # Model selection dropdown
        self.model_combo = QComboBox()
        self.model_combo.addItems(AVAILABLE_MODELS)
        current_model = load_model()
        if current_model in AVAILABLE_MODELS:
            self.model_combo.setCurrentText(current_model)

        layout.addRow("Model:", self.model_combo)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _on_save(self) -> None:
        """Handle save button click."""
        token = self.token_input.text().strip()
        if not token:
            QMessageBox.warning(
                self,
                "Invalid Token",
                "Please enter a valid GitHub token.",
            )
            return

        model = self.model_combo.currentText()

        if save_config(token=token, model=model):
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
