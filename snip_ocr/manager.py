"""Main application manager for SnipOCR."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING

import pyperclip
from pynput import keyboard
from PyQt6.QtCore import QObject, QThread, pyqtSignal
from PyQt6.QtGui import QAction, QActionGroup, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QMenu,
    QMessageBox,
    QStyle,
    QSystemTrayIcon,
)

from .config import load_model, load_token
from .constants import (
    APP_DISPLAY_NAME,
    ENDPOINT,
    HOTKEY_SHORTCUT,
    LANGUAGE_MAP,
    SYSTEM_PROMPT_TEMPLATE,
)
from .ui.settings_dialog import SettingsDialog
from .ui.snipper import Snipper
from .ui.update_dialog import UpdateDialog
from .updater import UpdateChecker
from .worker import AIWorker

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class Manager(QObject):
    """Main application manager.

    Coordinates the system tray, hotkey listener, screen capture,
    AI processing workflow, and automatic updates.

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

        # Load configuration
        self.github_token = load_token()
        self.selected_model = load_model()
        self.model_config = {
            "model": self.selected_model,
            "temperature": 0.1,
            "max_tokens": 2048,
        }

        # Update checker
        self.update_checker = UpdateChecker()
        self.update_available = False
        self.update_action: QAction | None = None

        self.hotkey = keyboard.GlobalHotKeys({"<ctrl>+<shift>+s": self.trigger.emit})
        self.hotkey.start()

        self._setup_tray()

        # Check for updates on startup
        self._check_for_updates()

        # Show settings dialog on first run if no token configured
        if not self.github_token:
            self._show_first_run_dialog()
        else:
            # Show startup notification for subsequent runs
            self._show_tray_message(
                APP_DISPLAY_NAME,
                f"{APP_DISPLAY_NAME} is ready!\n"
                f"Press {HOTKEY_SHORTCUT} to capture.",
                QSystemTrayIcon.MessageIcon.Information,
                3000,
            )

        logger.info(
            "%s started. Press %s to capture.", APP_DISPLAY_NAME, HOTKEY_SHORTCUT
        )

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
            base_path = Path(__file__).parent.parent

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
            icon = QIcon(str(icon_path))
        else:
            icon = self.app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)

        self.tray = QSystemTrayIcon(icon, self.app)
        self.tray.setToolTip(f"{APP_DISPLAY_NAME} - {HOTKEY_SHORTCUT}")

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

        # Update action (initially hidden)
        self.update_action = QAction("Update Available...", self.app)
        self.update_action.triggered.connect(self._show_update_dialog)
        self.update_action.setVisible(False)

        menu.addAction(action_snip)
        menu.addSeparator()
        menu.addAction(action_it)
        menu.addAction(action_en)
        menu.addSeparator()
        menu.addAction(self.update_action)
        menu.addAction(action_settings)
        menu.addSeparator()
        menu.addAction(action_quit)

        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._on_tray_click)
        self.tray.messageClicked.connect(self._on_notification_clicked)

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

    def _check_for_updates(self) -> None:
        """Check for available updates in background."""
        try:
            if self.update_checker.check_for_updates():
                self.update_available = True
                if self.update_action:
                    self.update_action.setVisible(True)
                
                # Show notification
                self._show_tray_message(
                    "Update Available",
                    f"Version {self.update_checker.latest_version} is available.\n"
                    "Click to download and install.",
                    QSystemTrayIcon.MessageIcon.Information,
                    8000,
                )
        except Exception as e:
            logger.warning(f"Failed to check for updates: {e}")

    def _on_notification_clicked(self) -> None:
        """Handle notification click."""
        if self.update_available:
            self._show_update_dialog()

    def _show_update_dialog(self) -> None:
        """Show the update download and installation dialog."""
        if not self.update_available:
            return
        
        dialog = UpdateDialog(self.update_checker)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # User chose to install now
            self._show_tray_message(
                APP_DISPLAY_NAME,
                "Installing update... The application will close.",
                QSystemTrayIcon.MessageIcon.Information,
                3000,
            )
            # Give time for notification to show
            self.app.processEvents()
            # Quit the application
            self.app.quit()

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
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Reload configuration
            self.github_token = dialog.get_token()
            self.selected_model = dialog.get_model()
            self.model_config["model"] = self.selected_model

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
            # Reload configuration
            self.github_token = dialog.get_token()
            self.selected_model = dialog.get_model()
            self.model_config["model"] = self.selected_model
            
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
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(target_language=target_language)

        self.active_thread = QThread()
        self.active_worker = AIWorker(
            b64_data,
            target_language,
            ENDPOINT,
            self.github_token or "",
            self.model_config,
            system_prompt,
        )
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
