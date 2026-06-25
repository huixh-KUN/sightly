from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt

from ui.components.switch_button import SwitchButton


class Toggle(QWidget):
    """开关 + 标签组合控件

    左侧 SwitchButton + 右侧文字标签，直接暴露 stateChanged 信号。
    """

    def __init__(self, text="", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        self._switch = SwitchButton()
        self._label = QLabel(text)
        layout.addWidget(self._switch)
        layout.addWidget(self._label)

    def isChecked(self):
        return self._switch.isChecked()

    def setChecked(self, checked):
        self._switch.setChecked(checked)

    @property
    def stateChanged(self):
        return self._switch.stateChanged
