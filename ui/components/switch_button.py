from PySide6.QtWidgets import QWidget, QMainWindow, QVBoxLayout, QHBoxLayout, QLabel, QApplication
from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QEasingCurve, Property, QRectF
from PySide6.QtGui import QPainter, QColor, QBrush, QPen, QFont


class SwitchButton(QWidget):
    """极简扁平化开关按钮，支持动画、禁用、尺寸自适应"""

    TRACK_OFF = QColor("#D0D0D0")
    TRACK_ON = QColor("#76C4B6")
    TRACK_DISABLED = QColor("#E8E8E8")
    KNOB_OFF = QColor("#FFFFFF")
    KNOB_ON = QColor("#FFFFFF")
    KNOB_DISABLED = QColor("#F5F5F5")
    KNOB_SHADOW = QColor(0, 0, 0, 25)

    stateChanged = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._checked = False
        self._hovered = False
        self._disabled = False
        self._anim_progress = 0.0

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

        track_color = self._blend_colors(self.TRACK_OFF, self.TRACK_ON, progress)
        if self._disabled:
            track_color = self.TRACK_DISABLED
        elif self._hovered and not self._pressed:
            track_color = track_color.lighter(105)

        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QBrush(track_color))
        p.drawRoundedRect(QRectF(2, track_y, w - 4, track_h), track_radius, track_radius)

        min_x = 2
        max_x = w - knob_size - 2
        knob_x = min_x + (max_x - min_x) * progress

        shadow = QRectF(knob_x, knob_y + 1, knob_size, knob_size)
        p.setBrush(QBrush(self.KNOB_SHADOW))
        p.drawEllipse(shadow)

        knob_color = self.KNOB_ON if self._checked else self.KNOB_OFF
        if self._disabled:
            knob_color = self.KNOB_DISABLED

        p.setBrush(QBrush(knob_color))
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


class DemoWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SwitchButton Demo")
        self.setFixedSize(400, 240)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setSpacing(24)
        layout.setContentsMargins(40, 40, 40, 40)

        row1 = QHBoxLayout()
        row1.addStretch()
        label1 = QLabel("关闭")
        label1.setFont(QFont("Microsoft YaHei", 13))
        row1.addWidget(label1)

        self.switch = SwitchButton()
        row1.addWidget(self.switch)
        row1.addStretch()
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addStretch()
        label2 = QLabel("开关状态：")
        label2.setFont(QFont("Microsoft YaHei", 12))
        row2.addWidget(label2)

        self.status_label = QLabel("关闭")
        self.status_label.setFont(QFont("Microsoft YaHei", 12))
        self.status_label.setStyleSheet("color: #888888;")
        row2.addWidget(self.status_label)
        row2.addStretch()
        layout.addLayout(row2)

        self.switch.stateChanged.connect(self._on_state_changed)

    def _on_state_changed(self, checked):
        self.status_label.setText("开启" if checked else "关闭")
        self.status_label.setStyleSheet(
            "color: #76C4B6;" if checked else "color: #888888;"
        )


def run_demo():
    app = QApplication([])
    w = DemoWindow()
    w.show()
    app.exec()


if __name__ == "__main__":
    run_demo()
