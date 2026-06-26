from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QPushButton, QScrollArea, QSizePolicy,
)
from PySide6.QtCore import Qt, Signal, QRect, QRectF, QPoint, QEvent
from PySide6.QtGui import QPainter, QColor, QPen, QFontMetrics

from shiboken6 import isValid

from ui.theme import ThemeManager

def _elide_right(font, text, max_width):
    if max_width <= 0:
        return text
    return QFontMetrics(font).elidedText(text, Qt.TextElideMode.ElideRight, max_width)


class _ComboPopup(QFrame):
    """轻量弹出面板，Qt.Popup 自动处理外部点击关闭"""

    RADIUS = 10
    ITEM_HEIGHT = 36
    PAD = 6
    MAX_VISIBLE_ITEMS = 10

    itemActivated = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint)
        self.setObjectName("comboPopup")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(self.PAD, self.PAD, self.PAD, self.PAD)
        outer.setSpacing(2)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll.setStyleSheet("background: transparent; border: none;")

        self._body = QWidget()
        self._body.setObjectName("comboPopupBody")
        self._list = QVBoxLayout(self._body)
        self._list.setContentsMargins(0, 0, 0, 0)
        self._list.setSpacing(2)
        self._scroll.setWidget(self._body)
        outer.addWidget(self._scroll)

        self._buttons: list[QPushButton] = []
        self._selected = -1

    def _panel_bg(self):
        palette = ThemeManager.current()
        return palette.SURFACE_ELEVATED if ThemeManager.is_dark() else "#FFFFFF"

    def apply_theme(self):
        palette = ThemeManager.current()
        bg = self._panel_bg()
        self._scroll.setStyleSheet(
            f"QScrollArea {{ background: transparent; border: none; }}"
            f"QScrollBar:vertical {{ width: 6px; background: transparent; }}"
            f"QScrollBar::handle:vertical {{ background: {palette.BORDER}; border-radius: 3px; min-height: 24px; }}"
            f"QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}"
        )
        self._body.setStyleSheet("background: transparent;")
        btn_style = (
            f"QPushButton#comboOption {{"
            f"  background: transparent; border: none; border-radius: 6px;"
            f"  text-align: left; padding: 0 14px; color: {palette.TEXT};"
            f"  font-size: 14px; min-height: {self.ITEM_HEIGHT}px;"
            f"}}"
            f"QPushButton#comboOption:hover {{ background: {palette.CARD_HOVER}; }}"
            f"QPushButton#comboOption[active=\"true\"] {{"
            f"  background: {palette.PRIMARY}33; color: {palette.PRIMARY}; font-weight: 500;"
            f"}}"
        )
        for btn in self._buttons:
            btn.setStyleSheet(btn_style)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        palette = ThemeManager.current()
        bg = QColor(self._panel_bg())
        border = QColor(palette.BORDER)
        area = QRectF(self.rect())

        if not ThemeManager.is_dark():
            shadow = QColor(0, 0, 0, 28)
            painter.setBrush(shadow)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(area.adjusted(2, 3, -2, -1), self.RADIUS, self.RADIUS)

        painter.setBrush(bg)
        painter.setPen(QPen(border, 1))
        painter.drawRoundedRect(area.adjusted(0, 0, -1, -2 if not ThemeManager.is_dark() else -1), self.RADIUS, self.RADIUS)
        painter.end()

    def set_items(self, items, selected_index, label_width):
        font = self.font()
        while self._list.count():
            item = self._list.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self._buttons.clear()

        for i, text in enumerate(items):
            label = _elide_right(font, text, label_width - 28)
            btn = QPushButton(label)
            btn.setObjectName("comboOption")
            btn.setProperty("active", i == selected_index)
            btn.setToolTip(text)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setFlat(True)
            btn.setFixedHeight(self.ITEM_HEIGHT)
            btn.clicked.connect(lambda _=False, idx=i: self.itemActivated.emit(idx))
            self._list.addWidget(btn)
            self._buttons.append(btn)

        self._selected = selected_index
        visible = min(len(items), self.MAX_VISIBLE_ITEMS)
        body_h = visible * self.ITEM_HEIGHT + max(0, visible - 1) * self._list.spacing()
        self._scroll.setFixedHeight(body_h)
        self.apply_theme()

    def set_selected(self, index):
        self._selected = index
        for i, btn in enumerate(self._buttons):
            btn.setProperty("active", i == index)
            btn.style().unpolish(btn)
            btn.style().polish(btn)


class ComboBox(QWidget):
    """统一下拉选择控件（QWidget + Popup 面板，非 QComboBox）"""

    currentTextChanged = Signal(str)
    currentIndexChanged = Signal(int)

    RADIUS = 8
    POPUP_PAD = 48
    POPUP_MAX_WIDTH = 480
    TEXT_PAD_LEFT = 12
    TEXT_PAD_RIGHT = 28

    def __init__(self, items=None, placeholder="", width=100, height=36, expand=False, parent=None):
        super().__init__(parent)
        self.setObjectName("appComboBox")
        self._expand = expand
        self.setFixedHeight(height)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.set_combo_width(width, expand)

        self._items: list[str] = []
        self._index = -1
        self._placeholder = placeholder
        self._popup_open = False
        self._hovered = False

        self._popup = _ComboPopup()
        self._popup.itemActivated.connect(self._on_popup_item)
        self._popup.installEventFilter(self)

        ThemeManager.on_switch(self._on_theme_switched)
        self.destroyed.connect(self._unregister_theme)

        if items:
            self.addItems(items)

    def _unregister_theme(self, *_args):
        ThemeManager.off_switch(self._on_theme_switched)
        if isValid(self._popup):
            self._popup.hide()

    def set_combo_width(self, width, expand=None):
        """设置宽度。expand=False 固定宽度（紧凑场景）；expand=True 最小宽度并可拉伸。"""
        if expand is not None:
            self._expand = expand
        if self._expand:
            self.setMinimumWidth(width)
            self.setMaximumWidth(16777215)
            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        else:
            self.setFixedWidth(width)
            self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.update()

    def _text_area_width(self):
        return max(0, self.width() - self.TEXT_PAD_LEFT - self.TEXT_PAD_RIGHT)

    @staticmethod
    def suggest_width(items, font=None, extra=52):
        """按最长选项估算合适固定宽度。"""
        from PySide6.QtWidgets import QApplication
        f = font or QApplication.font()
        fm = QFontMetrics(f)
        max_text = max((fm.horizontalAdvance(t) for t in items), default=0)
        return max_text + extra

    def _display_label(self, font, text):
        area = self._text_area_width()
        if not text or area <= 0:
            return text
        fm = QFontMetrics(font)
        if fm.horizontalAdvance(text) <= area:
            return text
        return _elide_right(font, text, area)

    def _on_popup_item(self, index):
        self._set_index(index, emit=True)
        self._popup.hide()

    def _on_theme_switched(self, _mode=None):
        if not isValid(self):
            ThemeManager.off_switch(self._on_theme_switched)
            return
        self.update()
        if isValid(self._popup) and self._popup.isVisible():
            self._popup.apply_theme()

    def eventFilter(self, obj, event):
        if obj is self._popup and event.type() == QEvent.Type.Hide:
            if isValid(self):
                self._popup_open = False
                self.update()
        return super().eventFilter(obj, event)

    def _calc_popup_width(self):
        fm = self.fontMetrics()
        width = self.width()
        for text in self._items:
            width = max(width, fm.horizontalAdvance(text) + self.POPUP_PAD)
        return min(width, self.POPUP_MAX_WIDTH)

    def _attach_popup_to_window(self):
        host = self.window()
        if not host or not isValid(self._popup):
            return
        if self._popup.parent() is not host:
            self._popup.setParent(
                host,
                Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint,
            )
            self._popup.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

    def _open_popup(self):
        if not self._items or not self.isEnabled():
            return
        self._attach_popup_to_window()
        popup_w = self._calc_popup_width()
        self._popup.set_items(self._items, self._index, popup_w)
        self._popup.adjustSize()
        self._popup.setFixedWidth(popup_w)

        pos = self.mapToGlobal(QPoint(0, self.height() + 4))
        self._popup.move(pos)
        self._popup_open = True
        self.update()
        self._popup.show()
        self._popup.raise_()
        self._popup.activateWindow()

    def _set_index(self, index, emit=False):
        if index < 0 or index >= len(self._items):
            return
        if index == self._index and not emit:
            return
        old_index = self._index
        self._index = index
        self.update()
        if emit:
            if old_index != index:
                self.currentIndexChanged.emit(index)
            self.currentTextChanged.emit(self._items[index])

    def addItems(self, items):
        self._items.extend(items)
        if self._index < 0 and self._items:
            self._index = 0

    def clear(self):
        self._items.clear()
        self._index = -1
        self.update()

    def count(self):
        return len(self._items)

    def findText(self, text):
        try:
            return self._items.index(text)
        except ValueError:
            return -1

    def currentIndex(self):
        return self._index

    def setCurrentIndex(self, index):
        self._set_index(index, emit=False)

    def currentText(self):
        if 0 <= self._index < len(self._items):
            return self._items[self._index]
        return ""

    def setPlaceholderText(self, text):
        self._placeholder = text
        self.update()

    def placeholderText(self):
        return self._placeholder

    def setEnabled(self, enabled):
        super().setEnabled(enabled)
        self.setCursor(Qt.CursorShape.PointingHandCursor if enabled else Qt.CursorShape.ArrowCursor)
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and self.isEnabled():
            if self._popup.isVisible():
                self._popup.hide()
            else:
                self._open_popup()
            event.accept()
            return
        super().mousePressEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Space, Qt.Key.Key_Down, Qt.Key.Key_Up):
            if not self._popup.isVisible():
                self._open_popup()
            event.accept()
            return
        if event.key() == Qt.Key.Key_Escape and self._popup.isVisible():
            self._popup.hide()
            event.accept()
            return
        super().keyPressEvent(event)

    def _field_background(self, palette):
        if ThemeManager.is_dark():
            return QColor(palette.SURFACE)
        return QColor("#FFFFFF")

    def _draw_chevron(self, painter, rect, color, open_up):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        pen = QPen(color, 1.6)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        cx = rect.center().x()
        cy = rect.center().y()
        if open_up:
            painter.drawLine(cx - 4, cy + 1, cx, cy - 3)
            painter.drawLine(cx, cy - 3, cx + 4, cy + 1)
        else:
            painter.drawLine(cx - 4, cy - 1, cx, cy + 3)
            painter.drawLine(cx, cy + 3, cx + 4, cy - 1)
        painter.restore()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = self.rect()
        palette = ThemeManager.current()
        enabled = self.isEnabled()
        focused = self.hasFocus() or self._popup_open
        hovered = self._hovered and not self._popup_open and enabled

        if not enabled:
            bg = QColor(palette.SURFACE if ThemeManager.is_dark() else "#E8E8E8")
            border_color = QColor(palette.BORDER)
            text_color = QColor(palette.TEXT_DIM)
            border_width = 1
            inset = 1
        elif focused:
            bg = self._field_background(palette)
            border_color = QColor(palette.PRIMARY)
            text_color = QColor(palette.TEXT)
            border_width = 2
            inset = 1
        elif hovered:
            bg = self._field_background(palette)
            border_color = QColor(palette.TEXT_SECONDARY)
            text_color = QColor(palette.TEXT)
            border_width = 1
            inset = 1
        else:
            bg = self._field_background(palette)
            border_color = QColor(palette.BORDER)
            text_color = QColor(palette.TEXT)
            border_width = 1
            inset = 1

        inner = QRectF(rect.adjusted(inset, inset, -inset, -inset))
        painter.setBrush(bg)
        painter.setPen(QPen(border_color, border_width))
        painter.drawRoundedRect(inner, self.RADIUS, self.RADIUS)

        text_rect = rect.adjusted(self.TEXT_PAD_LEFT, 0, -self.TEXT_PAD_RIGHT, 0)
        label = self.currentText() or self._placeholder or ""
        if label:
            if not self.currentText():
                text_color = QColor(palette.TEXT_SECONDARY)
            painter.setPen(text_color if enabled else QColor(palette.TEXT_DIM))
            display = self._display_label(painter.font(), label)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, display)

        if enabled:
            arrow_rect = QRect(rect.right() - 26, rect.top(), 20, rect.height())
            self._draw_chevron(
                painter,
                arrow_rect,
                QColor(palette.PRIMARY if focused else palette.TEXT_SECONDARY),
                self._popup_open,
            )
        painter.end()

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)
