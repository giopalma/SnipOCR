"""Screen region selection overlay."""

from __future__ import annotations

import base64
from typing import TYPE_CHECKING

from PyQt6.QtCore import QBuffer, QIODevice, QPoint, QRect, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QGuiApplication, QPainter, QPen
from PyQt6.QtWidgets import QWidget

if TYPE_CHECKING:
    from PyQt6.QtGui import QMouseEvent, QPaintEvent


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
