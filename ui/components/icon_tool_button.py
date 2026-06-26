from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, Signal, QRectF, QPointF
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QPainterPath

from ui.theme import ThemeManager


class IconToolButton(QWidget):
    """自绘图标按钮，用于监控组操作坞。"""

    clicked = Signal()

    def __init__(self, icon="edit", object_name="", tooltip="", parent=None):
        super().__init__(parent)
        self._icon = icon
        self._hovered = False
        self._pressed = False
        if object_name:
            self.setObjectName(object_name)
        self.setFixedSize(32, 32)
        self.setCursor(Qt.PointingHandCursor)
        if tooltip:
            self.setToolTip(tooltip)

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self._pressed = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._pressed = True
            self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            was_pressed = self._pressed
            self._pressed = False
            self.update()
            if was_pressed and self.rect().contains(event.position().toPoint()):
                self.clicked.emit()
        super().mouseReleaseEvent(event)

    def _icon_color(self, palette):
        if self._icon == "play":
            return QColor(palette.PRIMARY)
        if self._icon == "delete":
            color = QColor(palette.DANGER)
            if not self._hovered:
                color.setAlpha(220)
            return color
        color = QColor(palette.TEXT)
        if not self._hovered:
            color.setAlpha(210)
        return color

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        c = ThemeManager.current()
        center = QRectF(self.rect()).center()

        if self._hovered or self._pressed:
            hover = QColor(c.PRIMARY if self._icon == "play" else c.TEXT)
            if self._icon == "delete":
                hover = QColor(c.DANGER)
            hover.setAlpha(48 if not self._pressed else 72)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(hover))
            p.drawEllipse(center, 14, 14)

        icon_color = self._icon_color(c)
        if self._hovered and self._icon != "play":
            icon_color = QColor(c.DANGER if self._icon == "delete" else c.TEXT)

        if self._icon == "play":
            self._draw_play(p, center, icon_color)
        elif self._icon == "edit":
            self._draw_edit(p, center, icon_color)
        elif self._icon == "delete":
            self._draw_delete(p, center, icon_color)

        p.end()

    def _draw_play(self, p, center, color):
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(color))
        path = QPainterPath()
        cx, cy = center.x(), center.y()
        path.moveTo(cx - 3, cy - 5)
        path.lineTo(cx + 5, cy)
        path.lineTo(cx - 3, cy + 5)
        path.closeSubpath()
        p.drawPath(path)

    def _draw_edit(self, p, center, color):
        pen = QPen(color, 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        cx, cy = center.x(), center.y()
        body = QPainterPath()
        body.moveTo(cx + 5, cy - 5)
        body.lineTo(cx + 1, cy - 1)
        body.lineTo(cx - 1, cy - 3)
        body.lineTo(cx + 3, cy - 7)
        body.closeSubpath()
        p.drawPath(body)
        p.drawLine(QPointF(cx + 1, cy - 1), QPointF(cx - 4, cy + 4))

    def _draw_delete(self, p, center, color):
        pen = QPen(color, 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        cx, cy = center.x(), center.y()
        p.drawLine(QPointF(cx - 5, cy - 2), QPointF(cx + 5, cy - 2))
        p.drawLine(QPointF(cx - 3, cy - 2), QPointF(cx - 2.5, cy + 5))
        p.drawLine(QPointF(cx + 3, cy - 2), QPointF(cx + 2.5, cy + 5))
        p.drawLine(QPointF(cx - 2.5, cy + 5), QPointF(cx + 2.5, cy + 5))
        p.drawLine(QPointF(cx - 2, cy - 4), QPointF(cx + 2, cy - 4))
