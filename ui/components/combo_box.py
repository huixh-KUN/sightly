from PySide6.QtWidgets import QComboBox, QStylePainter, QStyleOptionComboBox, QStyle
from PySide6.QtCore import Qt, QRect, QRectF
from PySide6.QtGui import QPainter, QColor, QPen

from ui.theme import ThemeManager


class ComboBox(QComboBox):
    """统一下拉选择控件"""

    RADIUS = 8

    def __init__(self, items=None, placeholder="", width=100, height=36, parent=None):
        super().__init__(parent)
        self.setFixedWidth(width)
        self.setFixedHeight(height)
        self.setCursor(Qt.PointingHandCursor)
        if items:
            self.addItems(items)
        if placeholder:
            self.setPlaceholderText(placeholder)

    def paintEvent(self, event):
        painter = QStylePainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        opt = QStyleOptionComboBox()
        self.initStyleOption(opt)
        rect = self.rect()

        palette = ThemeManager.current()
        state = opt.state
        hovered = bool(state & QStyle.StateFlag.State_MouseOver)

        bg = QColor(palette.SURFACE)
        border = QColor(palette.PRIMARY if hovered else palette.BORDER)
        painter.setBrush(bg)
        painter.setPen(QPen(border, 1))
        painter.drawRoundedRect(QRectF(rect.adjusted(1, 1, -1, -1)), self.RADIUS, self.RADIUS)

        text_rect = rect.adjusted(12, 0, -28, 0)
        painter.setPen(QColor(palette.TEXT))
        label = self.currentText() or self.placeholderText() or ""
        painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, label)

        arrow_rect = QRect(rect.right() - 22, rect.top(), 18, rect.height())
        painter.setPen(QColor(palette.TEXT_SECONDARY))
        font = painter.font()
        font.setPixelSize(10)
        painter.setFont(font)
        painter.drawText(arrow_rect, Qt.AlignCenter, "▼")
        painter.end()
