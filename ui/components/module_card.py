from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt

from ui.components import SwitchButton


class ModuleCard(QFrame):
    """单个功能模块卡片组件

    独立可复用，不持有上层引用，通过 set_status() 接收状态更新。
    开关状态由 ModuleStateController.bind_switch 统一管理。
    """

    def __init__(self, icon, name, desc, parent=None):
        super().__init__(parent)
        self.setObjectName("moduleCard")
        self.setMinimumWidth(300)
        self._setup_ui(icon, name, desc)

    def _setup_ui(self, icon, name, desc):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)

        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        self._icon_label = QLabel(icon)
        self._icon_label.setFixedWidth(24)
        top_row.addWidget(self._icon_label)

        self._name_label = QLabel(name)
        self._name_label.setStyleSheet("color: #E8EAED; font-weight: 500;")
        top_row.addWidget(self._name_label, 1)

        self._toggle = SwitchButton()
        self._toggle.setFixedSize(44, 24)
        top_row.addWidget(self._toggle)
        layout.addLayout(top_row)

        self._desc_label = QLabel(desc)
        self._desc_label.setStyleSheet("color: #9AA0A6;")
        self._desc_label.setWordWrap(True)
        self._desc_label.setMinimumHeight(16)
        layout.addWidget(self._desc_label)

        self._status = QLabel("未启动")
        self._status.setStyleSheet("color: #5F6368;")
        layout.addWidget(self._status)

    def set_status(self, enabled):
        if enabled:
            self._status.setText("已启用")
            self._status.setStyleSheet("color: #81C784;")
        else:
            self._status.setText("未启动")
            self._status.setStyleSheet("color: #5F6368;")
