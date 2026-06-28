from PySide6.QtWidgets import QHBoxLayout, QLabel, QWidget, QDoubleSpinBox, QMessageBox
from ui.components.switch_button import SwitchButton
from ui.widgets import TextButton


class CycleControlWidget(QWidget):
    """循环检测开关 + 条件显示间隔 spinbox + 高级按钮"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._spin = QDoubleSpinBox()
        self._spin.setRange(0, 99.9)
        self._spin.setSingleStep(0.1)
        self._spin.setDecimals(1)
        self._spin.setValue(0)
        self._spin.setSuffix(" 秒")
        self._spin.setFixedWidth(72)
        self._spin.setToolTip("0 = 250-300ms 最快响应")

        self._toggle = SwitchButton(compact=True)
        self._toggle.setChecked(True)
        self._toggle.stateChanged.connect(self._on_toggle)

        self._adv_btn = TextButton("⚙️ 高级")
        self._adv_btn.setObjectName("templateAction")
        self._adv_btn.clicked.connect(
            lambda: QMessageBox.information(self, "高级", "暂未开发"))

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(QLabel("循环检测"))
        layout.addWidget(self._toggle)
        layout.addSpacing(12)
        layout.addWidget(QLabel("每"))
        layout.addWidget(self._spin)
        layout.addWidget(QLabel("秒"))
        layout.addStretch()
        layout.addWidget(self._adv_btn)

    def _on_toggle(self, checked: bool):
        self._spin.setVisible(checked)

    def is_cycle_enabled(self) -> bool:
        return self._toggle.isChecked()

    def set_cycle_enabled(self, enabled: bool):
        self._toggle.setChecked(enabled)
        self._spin.setVisible(enabled)

    def interval_value(self) -> float:
        return self._spin.value()

    def set_interval_value(self, value: float):
        self._spin.setValue(value)
