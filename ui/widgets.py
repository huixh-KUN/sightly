from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt

class Card(QFrame):
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        if title:
            header = QHBoxLayout()
            title_label = QLabel(title)
            title_label.setObjectName("cardTitle")
            header.addWidget(title_label)
            header.addStretch()
            layout.addLayout(header)
            self._content_layout = layout


class SectionTitle(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setObjectName("sectionTitle")


class GroupCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("groupCard")


class InfoLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setObjectName("infoText")


class AccentLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setObjectName("accentText")


class PrimaryButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setObjectName("primary")


class DangerButton(QPushButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setObjectName("danger")


class NavButton(QPushButton):
    def __init__(self, text="", icon_text="", parent=None):
        super().__init__(text, parent)
        self.setProperty("class", "navItem")
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(40)


class StatusIndicator(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("statusDot")
        self.setFixedSize(10, 10)
        self._running = False

    @property
    def running(self):
        return self._running

    @running.setter
    def running(self, value):
        self._running = value
        color = "#00e676" if value else "#555577"
        self.setStyleSheet(f"#statusDot {{ background-color: {color}; border-radius: 5px; min-width: 10px; max-width: 10px; min-height: 10px; max-height: 10px; }}")


class Divider(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("divider")
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)
