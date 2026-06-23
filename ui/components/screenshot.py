from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import Qt, Signal, QRect
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QPixmap


class ScreenCaptureOverlay(QWidget):
    """Fullscreen overlay for selecting a screen region via mouse drag.

    Emits region_captured(QPixmap) with the captured image on mouse release.
    Independent component with no external dependencies.
    """

    region_captured = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.setMouseTracking(True)
        self.showFullScreen()

        self._start = None
        self._end = None
        self._drawing = False

    def mousePressEvent(self, event):
        self._start = event.globalPosition().toPoint()
        self._end = self._start
        self._drawing = True
        self.update()

    def mouseMoveEvent(self, event):
        if self._drawing:
            self._end = event.globalPosition().toPoint()
            self.update()

    def mouseReleaseEvent(self, event):
        if not self._drawing:
            return
        self._drawing = False
        self._end = event.globalPosition().toPoint()

        rect = self._normalized_rect()
        if rect.width() > 10 and rect.height() > 10:
            self.hide()
            QApplication.processEvents()
            screen = QApplication.primaryScreen()
            pixmap = screen.grabWindow(0, rect.x(), rect.y(), rect.width(), rect.height())
            self.region_captured.emit(pixmap)
        self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        screen = QApplication.primaryScreen()
        geo = screen.geometry()

        overlay_color = QColor(0, 0, 0, 100)
        painter.fillRect(geo, overlay_color)

        if self._drawing and self._start and self._end:
            rect = self._normalized_rect()
            painter.setCompositionMode(QPainter.CompositionMode_Source)
            painter.fillRect(rect, QColor(0, 0, 0, 0))
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

            pen = QPen(QColor("#8AB4F8"), 2)
            painter.setPen(pen)
            painter.setBrush(QBrush(QColor(138, 180, 248, 30)))
            painter.drawRect(rect)

            info = f"{rect.width()} x {rect.height()}"
            painter.setPen(QColor("#8AB4F8"))
            painter.drawText(rect.x() + 6, rect.y() - 8, info)
        painter.end()

    def _normalized_rect(self):
        x1 = min(self._start.x(), self._end.x())
        y1 = min(self._start.y(), self._end.y())
        x2 = max(self._start.x(), self._end.x())
        y2 = max(self._start.y(), self._end.y())
        return QRect(x1, y1, x2 - x1, y2 - y1)
