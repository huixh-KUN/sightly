from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QSpinBox
)
from PySide6.QtCore import Qt, Signal

from ui.components.combo_box import ComboBox


class KeyCommandCard(QFrame):
    """按键命令卡片"""

    command_inserted = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(8)
        layout.addWidget(QLabel("按键命令"))

        row = QHBoxLayout()
        row.addWidget(QLabel("按键"))
        self._key_input = QLineEdit()
        self._key_input.setPlaceholderText("F1")
        self._key_input.setMaximumWidth(60)
        row.addWidget(self._key_input)
        row.addWidget(QLabel("类型"))
        self._type_combo = ComboBox(items=["KeyDown", "KeyUp"], width=110)
        row.addWidget(self._type_combo)
        row.addWidget(QLabel("次数"))
        self._count_spin = QSpinBox()
        self._count_spin.setRange(1, 999)
        self._count_spin.setValue(1)
        self._count_spin.setFixedWidth(60)
        row.addWidget(self._count_spin)
        insert_btn = QPushButton("插入")
        insert_btn.setObjectName("primary")
        insert_btn.setCursor(Qt.PointingHandCursor)
        insert_btn.clicked.connect(self._on_insert)
        row.addWidget(insert_btn)
        row.addStretch()
        layout.addLayout(row)

    def _on_insert(self):
        key = self._key_input.text().strip()
        if not key:
            return
        kt = self._type_combo.currentText()
        cnt = self._count_spin.value()
        self.command_inserted.emit(f'{kt} "{key}", {cnt}\n')


class DelayCommandCard(QFrame):
    """延迟命令卡片"""

    command_inserted = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(8)
        layout.addWidget(QLabel("延迟命令"))

        row = QHBoxLayout()
        row.addWidget(QLabel("延迟时间"))
        self._delay_spin = QSpinBox()
        self._delay_spin.setRange(1, 99999)
        self._delay_spin.setValue(250)
        self._delay_spin.setSuffix(" ms")
        row.addWidget(self._delay_spin)
        insert_btn = QPushButton("插入")
        insert_btn.setObjectName("primary")
        insert_btn.setCursor(Qt.PointingHandCursor)
        insert_btn.clicked.connect(self._on_insert)
        row.addWidget(insert_btn)
        row.addStretch()
        layout.addLayout(row)

    def _on_insert(self):
        ms = self._delay_spin.value()
        self.command_inserted.emit(f"Delay {ms}\n")


class MouseCommandCard(QFrame):
    """鼠标命令卡片"""

    command_inserted = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(8)
        layout.addWidget(QLabel("鼠标命令"))

        row = QHBoxLayout()
        row.addWidget(QLabel("按键"))
        self._btn_combo = ComboBox(items=["Left", "Right", "Middle"], width=90)
        row.addWidget(self._btn_combo)
        row.addSpacing(8)
        row.addWidget(QLabel("操作"))
        self._action_combo = ComboBox(items=["Down", "Up", "Click"], width=90)
        row.addWidget(self._action_combo)
        row.addWidget(QLabel("次数"))
        self._count_spin = QSpinBox()
        self._count_spin.setRange(1, 999)
        self._count_spin.setValue(1)
        row.addWidget(self._count_spin)
        insert_btn = QPushButton("插入")
        insert_btn.setObjectName("primary")
        insert_btn.setCursor(Qt.PointingHandCursor)
        insert_btn.clicked.connect(self._on_insert)
        row.addWidget(insert_btn)
        row.addStretch()
        layout.addLayout(row)

    def _on_insert(self):
        btn = self._btn_combo.currentText()
        action = self._action_combo.currentText()
        cnt = self._count_spin.value()
        self.command_inserted.emit(f"{btn}{action} {cnt}\n")
