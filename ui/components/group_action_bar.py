from PySide6.QtWidgets import QWidget, QHBoxLayout
from PySide6.QtCore import Qt, Signal, QRectF
from PySide6.QtGui import QPainter, QColor, QBrush, QPen

from ui.components.switch_button import SwitchButton
from ui.components.icon_tool_button import IconToolButton
from ui.theme import ThemeManager


class GroupActionBar(QWidget):
    """监控组操作坞：圆角容器 + 图标按钮 + 开关。"""

    test_clicked = Signal()
    toggled = Signal(bool)
    edit_clicked = Signal()
    delete_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("groupActionDock")
        self.setFixedHeight(40)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 4, 6, 4)
        layout.setSpacing(2)

        self._test_btn = IconToolButton("play", "testBtn", "执行一次测试")
        self._test_btn.clicked.connect(self.test_clicked.emit)
        layout.addWidget(self._test_btn)

        self._switch = SwitchButton(compact=True)
        self._switch.setObjectName("groupSwitch")
        self._switch.setToolTip("启用 / 禁用此组")
        self._switch.stateChanged.connect(self.toggled.emit)
        layout.addWidget(self._switch, 0, Qt.AlignmentFlag.AlignVCenter)

        self._edit_btn = IconToolButton("edit", "groupActionBtn", "编辑配置")
        self._edit_btn.clicked.connect(self.edit_clicked.emit)
        layout.addWidget(self._edit_btn)

        self._delete_btn = IconToolButton("delete", "dangerAction", "删除此组")
        self._delete_btn.clicked.connect(self.delete_clicked.emit)
        layout.addWidget(self._delete_btn)

    @property
    def switch(self):
        return self._switch

    def isChecked(self):
        return self._switch.isChecked()

    def setChecked(self, checked):
        self._switch.setChecked(checked)

    @property
    def stateChanged(self):
        return self._switch.stateChanged

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)

        c = ThemeManager.current()
        bg = QColor(c.SURFACE_ELEVATED)
        border = QColor(c.BORDER)

        rect = QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5)
        p.setPen(QPen(border, 1))
        p.setBrush(QBrush(bg))
        p.drawRoundedRect(rect, 10, 10)
        p.end()
