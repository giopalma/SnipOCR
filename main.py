"""
Snip OCR - Screenshot to Markdown Converter

A system tray application that captures screen regions and converts them
to Markdown using AI-powered OCR with LaTeX support.

Usage:
    Press Ctrl+Shift+S to capture a screen region.
    The extracted Markdown is automatically copied to clipboard.
"""

from __future__ import annotations

import base64
import json
import logging
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING

import pyperclip
import requests
from pynput import keyboard
from PyQt6.QtCore import (
    QBuffer,
    QIODevice,
    QObject,
    QPoint,
    QRect,
    Qt,
    QThread,
    pyqtSignal,
)
from PyQt6.QtGui import QAction, QActionGroup, QColor, QGuiApplication, QPainter, QPen
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QMenu,
    QMessageBox,
    QStyle,
    QSystemTrayIcon,
    QWidget,
)

if TYPE_CHECKING:
    from PyQt6.QtGui import QMouseEvent, QPaintEvent

import os

# --- Configuration ---
APP_NAME = "SnipOCR"  # Used for file paths and directories
APP_DISPLAY_NAME = "Snip OCR"  # Used for UI display
ENDPOINT: str = "https://models.inference.ai.azure.com/chat/completions"
HOTKEY_SHORTCUT = "Ctrl+Shift+S"


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


# Available models
AVAILABLE_MODELS = ["gpt-4o", "gpt-4o-mini"]

# Global token loaded from config
GITHUB_TOKEN: str | None = load_token()
SELECTED_MODEL: str = load_model()

MODEL_CONFIG: dict[str, str | float | int] = {
    "model": SELECTED_MODEL,
    "temperature": 0.1,
    "max_tokens": 2048,
}

LANGUAGE_MAP: dict[str, str] = {
    "Italiano": "Italian",
    "English": "English",
}

SYSTEM_PROMPT_TEMPLATE: str = (
    "You are a scientific transcriber. "
    "Analyze the image and convert it to faithful Markdown. "
    "Preserve headings, lists, and tables. "
    "MANDATORY: use $...$ for inline LaTeX and $$...$$ for blocks. "
    "Detect the original language of the text. "
    "If the image language does NOT match the requested output language, "
    "translate accurately to the requested language. "
    "Return ONLY the Markdown content, without preambles or code blocks. "
    "Requested output language: {target_language}."
)

# --- Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


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
            global GITHUB_TOKEN, SELECTED_MODEL
            GITHUB_TOKEN = token
            SELECTED_MODEL = model
            MODEL_CONFIG["model"] = model
            self.accept()
        else:
            QMessageBox.critical(
                self,
                "Error",
                "Failed to save settings. Please check permissions.",
            )


class AIWorker(QObject):
    """Background worker for AI API calls.

    Handles the communication with the AI endpoint in a separate thread
    to prevent UI freezing during processing.

    Signals:
        finished: Emitted with the transcribed text on success.
        error: Emitted with error message on failure.
    """

    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, img_b64: str, target_language: str) -> None:
        """Initialize the AI worker.

        Args:
            img_b64: Base64-encoded PNG image data.
            target_language: Target language for transcription/translation.
        """
        super().__init__()
        self.img_b64 = img_b64
        self.target_language = target_language
        self.cancelled = False

    def cancel(self) -> None:
        """Request cancellation of the current operation."""
        self.cancelled = True

    def run(self) -> None:
        """Execute the API call with retry logic."""
        retries = 3
        last_err = ""
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(
            target_language=self.target_language
        )

        for i in range(retries):
            if self.cancelled:
                self.error.emit("Operation cancelled.")
                return

            try:
                headers = {
                    "Authorization": f"Bearer {GITHUB_TOKEN}",
                    "Content-Type": "application/json",
                }
                payload = {
                    **MODEL_CONFIG,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": (
                                        "Transcribe accurately. "
                                        f"Output language: {self.target_language}."
                                    ),
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{self.img_b64}"
                                    },
                                },
                            ],
                        },
                    ],
                }

                response = requests.post(
                    ENDPOINT, json=payload, headers=headers, timeout=45
                )
                response.raise_for_status()

                data = response.json()
                choices = data.get("choices", [])
                if (
                    choices
                    and "message" in choices[0]
                    and "content" in choices[0]["message"]
                ):
                    content = choices[0]["message"]["content"]
                    self.finished.emit(content.strip())
                    return
                raise ValueError("Invalid JSON response format")

            except Exception as e:
                last_err = str(e)
                logger.warning("Attempt %d failed: %s", i + 1, last_err)
                time.sleep(1.5)

        self.error.emit(f"Failed after {retries} attempts. Last error: {last_err}")


class Snipper(QWidget):
    """Full-screen overlay widget for screen region selection.

    Provides a semi-transparent overlay that allows users to click and drag
    to select a rectangular region of the screen for capture.

    Signals:
        snip_done: Emitted with base64-encoded PNG data when capture is complete.
    """

    snip_done = pyqtSignal(str)

    def __init__(self) -> None:
        """Initialize the snipper overlay."""
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.begin = QPoint()
        self.end = QPoint()

    def start(self) -> None:
        """Show the overlay and prepare for capture."""
        primary = QGuiApplication.primaryScreen()
        if not primary:
            return

        # Use virtualGeometry which should span all screens
        virtual_geo = primary.virtualGeometry()

        # Force the widget size using setFixedSize + move
        self.setFixedSize(virtual_geo.width(), virtual_geo.height())
        self.move(virtual_geo.x(), virtual_geo.y())

        self.show()
        self.raise_()
        self.activateWindow()

    def paintEvent(self, event: QPaintEvent) -> None:
        """Render the overlay with selection rectangle."""
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 160))
        if not self.begin.isNull() and not self.end.isNull():
            rect = QRect(self.begin, self.end).normalized()
            painter.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
            painter.fillRect(rect, Qt.GlobalColor.white)
            painter.setCompositionMode(
                QPainter.CompositionMode.CompositionMode_SourceOver
            )
            painter.setPen(QPen(QColor(0, 255, 255), 2))
            painter.drawRect(rect)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press to start selection."""
        self.begin = event.pos()
        self.end = event.pos()
        self.update()

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle mouse move to update selection."""
        self.end = event.pos()
        self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Handle mouse release to complete selection and capture."""
        rect = QRect(self.begin, self.end).normalized()
        self.hide()
        if rect.width() > 10 and rect.height() > 10:
            # Convert local widget coordinates to global screen coordinates
            global_begin = self.mapToGlobal(rect.topLeft())
            global_rect = QRect(global_begin, rect.size())

            # Find the screen at the selection's top-left corner
            screen = (
                QGuiApplication.screenAt(global_begin)
                or QGuiApplication.primaryScreen()
            )
            screen_geo = screen.geometry()

            # Calculate the position relative to the target screen
            rel_rect = QRect(
                global_rect.x() - screen_geo.x(),
                global_rect.y() - screen_geo.y(),
                global_rect.width(),
                global_rect.height(),
            )

            pixmap = screen.grabWindow(
                0, rel_rect.x(), rel_rect.y(), rel_rect.width(), rel_rect.height()
            )

            buffer = QBuffer()
            buffer.open(QIODevice.OpenModeFlag.ReadWrite)
            pixmap.save(buffer, "PNG")
            b64 = base64.b64encode(buffer.data()).decode("utf-8")
            buffer.close()

            self.snip_done.emit(b64)

        self.begin = QPoint()
        self.end = QPoint()


class Manager(QObject):
    """Main application manager.

    Coordinates the system tray, hotkey listener, screen capture,
    and AI processing workflow.

    Signals:
        trigger: Emitted when capture should be initiated.
    """

    trigger = pyqtSignal()

    def __init__(self) -> None:
        """Initialize the application manager."""
        super().__init__()
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        self.snipper = Snipper()
        self.trigger.connect(self.snipper.start)
        self.snipper.snip_done.connect(self.process)

        self.active_thread: QThread | None = None
        self.active_worker: AIWorker | None = None
        self.tray: QSystemTrayIcon | None = None

        self.output_language = "Italiano"

        self.hotkey = keyboard.GlobalHotKeys({"<ctrl>+<shift>+s": self.trigger.emit})
        self.hotkey.start()

        self._setup_tray()

        # Show settings dialog on first run if no token configured
        if not GITHUB_TOKEN:
            self._show_first_run_dialog()

        logger.info("Snip OCR started. Press %s to capture.", HOTKEY_SHORTCUT)

    def _get_icon_path(self) -> Path | None:
        """Get the path to the application icon.

        Checks multiple locations for the icon file:
        1. PyInstaller bundle directory (when running as exe)
        2. Script directory (when running as script)

        Returns:
            Path to icon.png if found, None otherwise.
        """
        # Check if running as PyInstaller bundle
        if getattr(sys, "frozen", False):
            base_path = Path(sys._MEIPASS)  # type: ignore[attr-defined]
        else:
            base_path = Path(__file__).parent

        icon_path = base_path / "icon.png"
        if icon_path.exists():
            return icon_path
        return None

    def _setup_tray(self) -> None:
        """Configure the system tray icon and context menu."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.warning("System tray not available on this system.")
            return

        # Try to load custom icon, fallback to system default
        icon_path = self._get_icon_path()
        if icon_path and icon_path.exists():
            from PyQt6.QtGui import QIcon

            icon = QIcon(str(icon_path))
        else:
            icon = self.app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)

        self.tray = QSystemTrayIcon(icon, self.app)
        self.tray.setToolTip(f"Snip OCR - {HOTKEY_SHORTCUT}")

        menu = QMenu()

        # Language selection
        lang_group = QActionGroup(self.app)
        lang_group.setExclusive(True)

        action_it = QAction("Italiano", self.app, checkable=True)
        action_en = QAction("English", self.app, checkable=True)
        action_it.setChecked(True)

        lang_group.addAction(action_it)
        lang_group.addAction(action_en)

        action_it.triggered.connect(lambda: self._set_language("Italiano"))
        action_en.triggered.connect(lambda: self._set_language("English"))

        action_snip = QAction("Capture", self.app)
        action_settings = QAction("Settings...", self.app)
        action_quit = QAction("Quit", self.app)

        action_snip.triggered.connect(self.trigger.emit)
        action_settings.triggered.connect(self._show_settings)
        action_quit.triggered.connect(self.app.quit)

        menu.addAction(action_snip)
        menu.addSeparator()
        menu.addAction(action_it)
        menu.addAction(action_en)
        menu.addSeparator()
        menu.addAction(action_settings)
        menu.addSeparator()
        menu.addAction(action_quit)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_click)

        # Show the tray icon
        self.tray.show()

        # On Windows, ensure notifications are not suppressed and check support
        self._ensure_tray_visible_on_windows()

    def _ensure_tray_visible_on_windows(self) -> None:
        """Ensure tray icon is visible on Windows platform.

        On Windows, explicitly setting visibility can help prevent
        notification suppression issues. Also logs notification support status.
        """
        if sys.platform == "win32" and self.tray:
            self.tray.setVisible(True)
            # Make sure the message balloon is supported
            if self.tray.supportsMessages():
                logger.info("System tray notifications are supported.")
            else:
                logger.warning(
                    "System tray notifications may not be supported on this system."
                )

    def _show_tray_message(
        self,
        title: str,
        message: str,
        icon: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.MessageIcon.Information,
        duration: int = 3000,
    ) -> None:
        """Show a system tray notification with fallback handling.

        Args:
            title: Notification title.
            message: Notification message.
            icon: Notification icon type.
            duration: Duration in milliseconds.
        """
        if not self.tray:
            logger.warning("Tray icon not available for notification.")
            return

        # On Windows, ensure tray is properly shown before sending message
        self._ensure_tray_visible_on_windows()

        # Send the notification
        self.tray.showMessage(title, message, icon, duration)

        # Log the notification for debugging
        logger.info("Notification: %s - %s", title, message)

    def _set_language(self, lang: str) -> None:
        """Update the output language preference."""
        self.output_language = lang
        self._show_tray_message(
            "Output Language",
            f"Selected: {lang}",
            QSystemTrayIcon.MessageIcon.Information,
            1500,
        )

    def _show_settings(self) -> None:
        """Show the settings dialog."""
        dialog = SettingsDialog()
        dialog.exec()

    def _show_first_run_dialog(self) -> None:
        """Show welcome dialog on first run."""
        QMessageBox.information(
            None,
            f"Welcome to {APP_DISPLAY_NAME}",
            "Please configure your GitHub Token to use this application.\n\n"
            "You can get a token from GitHub Settings > Developer settings > "
            "Personal access tokens.",
        )
        dialog = SettingsDialog()
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # User successfully configured token, show tray notification
            self._show_tray_message(
                APP_DISPLAY_NAME,
                f"{APP_DISPLAY_NAME} is now running in the system tray!\n\n"
                f"Press {HOTKEY_SHORTCUT} to capture or "
                "right-click the tray icon for options.",
                QSystemTrayIcon.MessageIcon.Information,
                8000,
            )
        else:
            # User cancelled, show warning
            self._show_tray_message(
                APP_DISPLAY_NAME,
                "No token configured. Capture will not work until configured.",
                QSystemTrayIcon.MessageIcon.Warning,
                5000,
            )

    def _on_tray_click(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Handle tray icon click events."""
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.trigger.emit()

    def process(self, b64_data: str) -> None:
        """Process a captured screenshot through the AI pipeline."""
        self._show_tray_message(
            APP_DISPLAY_NAME,
            "Image captured. Processing...",
            QSystemTrayIcon.MessageIcon.Information,
            2000,
        )

        if self.active_worker is not None:
            self.active_worker.cancel()

        target_language = LANGUAGE_MAP.get(self.output_language, "Italian")

        self.active_thread = QThread()
        self.active_worker = AIWorker(b64_data, target_language)
        self.active_worker.moveToThread(self.active_thread)

        self.active_thread.started.connect(self.active_worker.run)
        self.active_worker.finished.connect(self._on_success)
        self.active_worker.error.connect(self._on_error)

        self.active_worker.finished.connect(self.active_thread.quit)
        self.active_worker.error.connect(self.active_thread.quit)
        self.active_thread.finished.connect(self.active_worker.deleteLater)
        self.active_thread.finished.connect(self.active_thread.deleteLater)

        self.active_thread.start()

    def _on_success(self, text: str) -> None:
        """Handle successful AI response."""
        clean = text.strip()
        # Remove markdown code block wrappers if present
        if clean.startswith("```"):
            lines = clean.splitlines()
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            clean = "\n".join(lines).strip()

        pyperclip.copy(clean)

        self._show_tray_message(
            APP_DISPLAY_NAME,
            "Done! Markdown copied to clipboard.",
            QSystemTrayIcon.MessageIcon.Information,
            2000,
        )

        logger.info("Copied to clipboard:\n%s", clean)

    def _on_error(self, err_msg: str) -> None:
        """Handle AI processing error."""
        self._show_tray_message(
            f"{APP_DISPLAY_NAME} Error",
            err_msg,
            QSystemTrayIcon.MessageIcon.Critical,
            3000,
        )
        logger.error("Critical error: %s", err_msg)

    def run(self) -> int:
        """Start the application event loop."""
        return self.app.exec()


def main() -> None:
    """Application entry point."""
    # Disable Qt's High DPI scaling to ensure 1:1 pixel mapping
    # This prevents coordinate mismatches on multi-monitor setups with different scaling
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "0"
    os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"
    os.environ["QT_SCALE_FACTOR"] = "1"

    sys.exit(Manager().run())


if __name__ == "__main__":
    main()
