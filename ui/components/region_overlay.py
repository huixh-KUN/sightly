from PySide6.QtWidgets import QWidget, QApplication
from PySide6.QtCore import Qt, QRect, Signal
from PySide6.QtGui import QPainter, QPen, QColor, QBrush


class RegionOverlay(QWidget):
    """全屏区域选择覆盖层

    通过鼠标拖拽选择屏幕区域，发射 region_selected(x1, y1, x2, y2) 信号。
    独立组件，无外部依赖，支持多种选择类型标识。
    """

    region_selected = Signal(int, int, int, int)

    def __init__(self, selection_type="normal", parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        self.showFullScreen()

        self.start_x = self.start_y = 0
        self.end_x = self.end_y = 0
        self.is_drawing = False
        self.selection_type = selection_type

    def mousePressEvent(self, event):
        self.start_x = int(event.globalX())
        self.start_y = int(event.globalY())
        self.end_x = self.start_x
        self.end_y = self.start_y
        self.is_drawing = True
        self.update()

    def mouseMoveEvent(self, event):
        if self.is_drawing:
            self.end_x = int(event.globalX())
            self.end_y = int(event.globalY())
            self.update()

    def mouseReleaseEvent(self, event):
        if not self.is_drawing:
            return
        self.is_drawing = False
        screen = QApplication.primaryScreen()
        ratio = screen.devicePixelRatio()
        x1 = int(min(self.start_x, self.end_x) * ratio)
        y1 = int(min(self.start_y, self.end_y) * ratio)
        x2 = int(max(self.start_x, self.end_x) * ratio)
        y2 = int(max(self.start_y, self.end_y) * ratio)
        if x2 - x1 > 10 and y2 - y1 > 10:
            self.region_selected.emit(x1, y1, x2, y2)
        self.close()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        screen = QApplication.primaryScreen()
        geo = screen.geometry()
        ratio = screen.devicePixelRatio()

        overlay_color = QColor(0, 0, 0, 100)
        painter.fillRect(geo, overlay_color)

        if self.is_drawing:
            x = min(self.start_x, self.end_x)
            y = min(self.start_y, self.end_y)
            w = abs(self.end_x - self.start_x)
            h = abs(self.end_y - self.start_y)

            painter.setCompositionMode(QPainter.CompositionMode_Source)
            painter.fillRect(QRect(x, y, w, h), QColor(0, 0, 0, 0))
            painter.setCompositionMode(QPainter.CompositionMode_SourceOver)

            pen = QPen(QColor(0, 180, 216), 2)
            painter.setPen(pen)
            brush = QBrush(QColor(0, 180, 216, 30))
            painter.setBrush(brush)
            painter.drawRect(QRect(x, y, w, h))

            pw, ph = int(w * ratio), int(h * ratio)
            info = f"{pw} x {ph}"
            painter.setPen(QColor(0, 180, 216))
            painter.drawText(x + 4, y - 8, info)
