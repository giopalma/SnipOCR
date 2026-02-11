"""Settings dialog for SnipOCR configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QWidget,
)

from ..config import load_model, load_token, save_config
from ..constants import APP_DISPLAY_NAME, AVAILABLE_MODELS, LOCAL_MODEL_NAME
from ..icon_utils import get_icon

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
        icon = get_icon()
        if icon:
            self.setWindowIcon(icon)
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

        # Info label for local model (using QLabel as per review suggestion)
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("color: gray;")
        layout.addRow("", self.info_label)
        
        # Connect signal AFTER info_label is created to avoid AttributeError
        self.model_combo.currentTextChanged.connect(self._on_model_changed)
        
        # Update info based on initial model
        self._on_model_changed(current_model)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_save)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def _on_model_changed(self, model: str) -> None:
        """Handle model selection change.
        
        Args:
            model: Selected model name.
        """
        if model == LOCAL_MODEL_NAME:
            self.info_label.setText("ℹ️ No API key required for local model")
            self.token_input.setEnabled(False)
        else:
            self.info_label.setText("ℹ️ API key required for cloud models")
            self.token_input.setEnabled(True)

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
