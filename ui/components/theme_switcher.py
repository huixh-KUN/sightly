import math

from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Qt, Signal, QRectF, QPointF
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QPainterPath

from ui.theme import ThemeManager


class ThemeSwitcher(QWidget):
    """顶栏主题切换：日月图标分段控件"""

    themeChanged = Signal(str)

    _SEGMENTS = ("dark", "light")

    def __init__(self, parent=None):
        super().__init__(parent)
        self._theme = "dark" if ThemeManager.is_dark() else "light"
        self._hover = None
        self.setFixedSize(72, 32)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("切换浅色 / 深色主题")

    def current_theme(self):
        return self._theme

    def set_theme(self, theme):
        if theme not in self._SEGMENTS:
            return
        if theme == self._theme:
            self.update()
            return
        self._theme = theme
        self.update()

    def _segment_at(self, pos):
        mid = self.width() / 2
        return "dark" if pos.x() < mid else "light"

    def _segment_rect(self, side):
        pad = 3
        half_w = (self.width() - pad * 2) / 2
        x = pad if side == "dark" else pad + half_w
        return QRectF(x, pad, half_w, self.height() - pad * 2)

    def enterEvent(self, event):
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = None
        self.update()
        super().leaveEvent(event)

    def mouseMoveEvent(self, event):
        hover = self._segment_at(event.position())
        if hover != self._hover:
            self._hover = hover
            self.update()
        super().mouseMoveEvent(event)

    def mousePressEvent(self, event):
        if event.button() != Qt.MouseButton.LeftButton:
            return
        side = self._segment_at(event.position())
        if side != self._theme:
            self.themeChanged.emit(side)
        super().mousePressEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        c = ThemeManager.current()
        track = QColor(c.SURFACE_ELEVATED)
        border = QColor(c.BORDER)
        active_bg = QColor(c.PRIMARY)
        active_bg.setAlpha(40)
        hover_bg = QColor(c.TEXT)
        hover_bg.setAlpha(18)
        icon_active = QColor(c.PRIMARY)
        icon_idle = QColor(c.TEXT_SECONDARY)

        p.setPen(QPen(border, 1))
        p.setBrush(QBrush(track))
        p.drawRoundedRect(QRectF(0.5, 0.5, self.width() - 1, self.height() - 1), 8, 8)

        for side in self._SEGMENTS:
            rect = self._segment_rect(side)
            if side == self._theme:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(active_bg))
                p.drawRoundedRect(rect, 6, 6)
            elif side == self._hover:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(QBrush(hover_bg))
                p.drawRoundedRect(rect, 6, 6)

        for side, draw_fn in (("dark", self._draw_moon), ("light", self._draw_sun)):
            color = icon_active if side == self._theme else icon_idle
            center = self._segment_rect(side).center()
            draw_fn(p, center, color)

        p.end()

    def _draw_moon(self, p, center, color):
        outer = QPainterPath()
        outer.addEllipse(QRectF(center.x() - 6, center.y() - 6, 12, 12))
        inner = QPainterPath()
        inner.addEllipse(QRectF(center.x() - 2, center.y() - 7, 12, 12))
        crescent = outer.subtracted(inner)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(color))
        p.drawPath(crescent)

    def _draw_sun(self, p, center, color):
        p.setPen(QPen(color, 1.6))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawEllipse(QRectF(center.x() - 4, center.y() - 4, 8, 8))
        for i in range(8):
            angle = i * 45
            rad = angle * 3.14159 / 180
            inner = 6.0
            outer = 8.5
            x1 = center.x() + inner * math.cos(rad)
            y1 = center.y() + inner * math.sin(rad)
            x2 = center.x() + outer * math.cos(rad)
            y2 = center.y() + outer * math.sin(rad)
            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))
