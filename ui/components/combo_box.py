from PySide6.QtWidgets import QComboBox, QStyle, QStylePainter, QStyleOptionComboBox
from PySide6.QtCore import Qt, QRect, QRectF
from PySide6.QtGui import QPainter, QColor, QPen, QFont


class ComboBox(QComboBox):
    """统一下拉选择控件

    QComboBox 子类，自绘制下拉箭头，避免平台 QSS 兼容问题。
    预设最小宽度 / 固定高度 / 指示手型光标。
    """

    BG = "#1E1E1E"
    BORDER = "#3C4043"
    BORDER_HOVER = "#5F6368"
    BORDER_ACTIVE = "#8AB4F8"
    TEXT = "#E8EAED"
    ARROW = "#9AA0A6"
    ARROW_HOVER = "#E8EAED"
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

        # ── 背景 + 边框 ──
        bg = QColor(self.BG)
        state = opt.state
        border_color = QColor(
            self.BORDER_ACTIVE if (state & QStyle.StateFlag.State_On)
            else self.BORDER_HOVER if (state & QStyle.StateFlag.State_MouseOver)
            else self.BORDER
        )
        painter.setBrush(bg)
        painter.setPen(QPen(border_color, 1))
        painter.drawRoundedRect(QRectF(rect.adjusted(1, 1, -1, -1)), self.RADIUS, self.RADIUS)

        # ── 文本 ──
        text_rect = rect.adjusted(12, 0, -32, 0)
        painter.setPen(QColor(self.TEXT))
        label = self.currentText() if self.currentText() else ""
        if not label:
            label = self.placeholderText() or ""
        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            label,
        )

        # ── 下拉箭头 ──
        arrow_rect = QRect(rect.right() - 28, rect.top(), 28, rect.height())
        arrow_color = QColor(
            self.TEXT if (state & QStyle.StateFlag.State_On)
            else self.ARROW_HOVER if (state & QStyle.StateFlag.State_MouseOver)
            else self.ARROW
        )
        painter.setPen(arrow_color)
        arrow_font = QFont()
        arrow_font.setPixelSize(10)
        painter.setFont(arrow_font)
        painter.drawText(arrow_rect, Qt.AlignmentFlag.AlignCenter, "▼")

        painter.end()
