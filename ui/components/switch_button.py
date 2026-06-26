from PySide6.QtWidgets import QWidget, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QApplication
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, Property, QRectF
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QFont

from ui.theme import ThemeManager


class SwitchButton(QWidget):
    """极简扁平化开关按钮，支持动画、禁用、尺寸自适应"""

    stateChanged = Signal(bool)

    def __init__(self, parent=None, compact=False):
        super().__init__(parent)
        self._checked = False
        self._hovered = False
        self._disabled = False
        self._anim_progress = 0.0
        self._compact = compact

        if compact:
            self.setFixedSize(40, 24)
        else:
            self.setFixedSize(48, 28)
        self.setCursor(Qt.PointingHandCursor)

        self._anim = QPropertyAnimation(self, b"anim_progress", self)
        self._anim.setDuration(180)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._pressed = False

    @Property(float)
    def anim_progress(self):
        return self._anim_progress

    @anim_progress.setter
    def anim_progress(self, value):
        self._anim_progress = value
        self.update()

    def isChecked(self):
        return self._checked

    def setChecked(self, checked):
        if checked == self._checked:
            return
        self._checked = checked
        self._start_animation()
        self.stateChanged.emit(checked)

    def toggle(self):
        self.setChecked(not self._checked)

    def setEnabled(self, enabled):
        super().setEnabled(enabled)
        self._disabled = not enabled
        self.setCursor(Qt.ArrowCursor if not enabled else Qt.PointingHandCursor)
        self.update()

    def _start_animation(self):
        self._anim.stop()
        self._anim.setStartValue(self._anim_progress)
        self._anim.setEndValue(1.0 if self._checked else 0.0)
        self._anim.start()

    def enterEvent(self, event):
        self._hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hovered = False
        self.update()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not self._disabled:
            self._pressed = True
            self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not self._disabled:
            self._pressed = False
            if self.rect().contains(event.position().toPoint()):
                self.toggle()
            self.update()
        super().mouseReleaseEvent(event)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        track_h = max(14, h * 0.5)
        track_y = (h - track_h) / 2
        knob_size = max(16, h - 4)
        knob_y = (h - knob_size) / 2
        track_radius = track_h / 2

        progress = self._anim_progress

        palette = ThemeManager.current()
        track_off = QColor(palette.SWITCH_TRACK_OFF)
        track_on = QColor(palette.SWITCH_TRACK_ON)
        track_disabled = QColor(palette.SWITCH_TRACK_DISABLED)
        knob_color = QColor(palette.SWITCH_KNOB)
        knob_disabled = QColor(palette.SWITCH_KNOB_DISABLED)
        knob_shadow = QColor(0, 0, 0, palette.SWITCH_KNOB_SHADOW_ALPHA)

        track_color = self._blend_colors(track_off, track_on, progress)
        if self._disabled:
            track_color = track_disabled
        elif self._hovered and not self._pressed:
            if ThemeManager.is_dark():
                track_color = track_color.lighter(108)
            elif progress > 0.5:
                track_color = QColor(palette.PRIMARY_HOVER)
            else:
                track_color = track_color.darker(105)

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(track_color))
        p.drawRoundedRect(QRectF(2, track_y, w - 4, track_h), track_radius, track_radius)

        min_x = 2
        max_x = w - knob_size - 2
        knob_x = min_x + (max_x - min_x) * progress

        shadow = QRectF(knob_x, knob_y + 1, knob_size, knob_size)
        p.setBrush(QBrush(knob_shadow))
        p.drawEllipse(shadow)

        current_knob = knob_color if not self._disabled else knob_disabled

        knob_border = getattr(palette, "SWITCH_KNOB_BORDER", None)
        if knob_border and not self._disabled and not ThemeManager.is_dark():
            p.setPen(QPen(QColor(knob_border), 1))
        else:
            p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(current_knob))
        p.drawEllipse(QRectF(knob_x, knob_y, knob_size, knob_size))

        p.end()

    def _blend_colors(self, c1, c2, t):
        r = int(c1.red() + (c2.red() - c1.red()) * t)
        g = int(c1.green() + (c2.green() - c1.green()) * t)
        b = int(c1.blue() + (c2.blue() - c1.blue()) * t)
        return QColor(r, g, b)

    def sizeHint(self):
        return self.minimumSizeHint()

    def minimumSizeHint(self):
        return self.size()
