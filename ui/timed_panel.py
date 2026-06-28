from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QScrollArea, QFrame,
    QSpinBox, QGridLayout
)
from PySide6.QtCore import Qt, Signal

from ui.widgets import (
    SectionTitle, PrimaryButton,
    TextButton, ClickableLabel,
    GroupListItem, GroupEditWindow,
)
from ui.components import SwitchButton, CycleControlWidget
from ui.components import KeyCaptureWidget
from ui.components import ConfigCard
from ui.components import GroupEditHeader, ValueChip
from ui.components.form_rows import spin_range_row



class TimedPanel(QWidget):
    position_selection_requested = Signal(int)
    test_group_requested = Signal(int)

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.groups_data = []
        self.list_items = []
        self._view_only = False
        self._edit_window = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QHBoxLayout()
        header.setSpacing(16)
        header.setContentsMargins(32, 28, 32, 16)

        title_col = QVBoxLayout()
        title_col.setSpacing(4)
        title_col.addWidget(SectionTitle("定时功能"))
        subtitle = QLabel("按设定时间间隔自动执行按键操作")
        subtitle.setObjectName("subtitle")
        title_col.addWidget(subtitle)
        header.addLayout(title_col)
        header.addStretch()

        add_btn = PrimaryButton("＋ 新增定时组")
        add_btn.setCursor(Qt.PointingHandCursor)
        add_btn.clicked.connect(self.add_group)
        header.addWidget(add_btn)

        layout.addLayout(header)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(scroll_content)
        self.scroll_layout.setContentsMargins(32, 0, 32, 28)
        self.scroll_layout.setSpacing(6)
        self.scroll_layout.addStretch()
        self.scroll.setWidget(scroll_content)
        layout.addWidget(self.scroll, 1)

        self.add_group()

    def _default_config(self, idx):
        return {
            "name": f"定时组 {idx + 1}",
            "enabled": True,
            "interval": "10",
            "key": "",
            "delay_min": "300",
            "delay_max": "500",
            "alarm": False,
            "click_enabled": False,
            "click_offset": "0",
            "position_x": "0",
            "position_y": "0",
            "position": "0,0",
        }

    def add_group(self):
        idx = len(self.groups_data)
        default = self._default_config(idx)
        self.groups_data.append(default)
        self._add_list_item(idx, default)

    def _add_list_item(self, idx, data):
        item = GroupListItem(idx, "timed", parent=self)
        item.set_data(data)
        item.toggled.connect(self._on_toggle)
        item.double_clicked.connect(self._open_edit)
        item.delete_clicked.connect(self._delete_group)
        item.test_requested.connect(self._test_group)
        self.scroll_layout.insertWidget(self.scroll_layout.count() - 1, item)
        self.list_items.append(item)

    def _delete_group(self, idx):
        if 0 <= idx < len(self.list_items):
            item = self.list_items.pop(idx)
            self.scroll_layout.removeWidget(item)
            item.setParent(None)
            item.deleteLater()
            self.groups_data.pop(idx)
            self._renumber()

    def _test_group(self, idx):
        self.test_group_requested.emit(idx)

    def _renumber(self):
        for i, item in enumerate(self.list_items):
            item.set_index(i)
            item.set_data(self.groups_data[i])

    def _on_toggle(self, idx, state):
        if 0 <= idx < len(self.groups_data):
            self.groups_data[idx]["enabled"] = bool(state)

    def _open_edit(self, idx):
        if self._view_only:
            return
        if self._edit_window:
            try:
                self._edit_window.close()
            except RuntimeError:
                self.app.logging_manager.error("UI", "编辑窗口已被销毁")
            self._edit_window = None
        if 0 <= idx < len(self.groups_data):
            self._edit_window = GroupEditWindow(
                self.groups_data[idx], idx, "timed", panel=self,
            )
            if hasattr(self._edit_window._editor, 'position_selection_requested'):
                self._edit_window._editor.position_selection_requested.connect(
                    self.position_selection_requested.emit
                )
            self._edit_window.show()

    def set_enabled(self, enabled):
        self._view_only = not enabled

    def collect_config(self):
        return list(self.groups_data)

    def set_config(self, config_list):
        for item in self.list_items:
            self.scroll_layout.removeWidget(item)
            item.deleteLater()
        self.list_items.clear()
        self.groups_data.clear()
        for cfg in config_list:
            self.groups_data.append(dict(cfg))
            self._add_list_item(len(self.list_items), cfg)
        if not self.list_items:
            self.add_group()


class TimedGroupWidget(QFrame):
    position_selection_requested = Signal(int)

    def __init__(self, index, parent=None):
        super().__init__(parent)
        self.index = index
        self._pos_x = 0
        self._pos_y = 0
        self._enabled = True

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 16)
        layout.setSpacing(14)

        self.header = GroupEditHeader(f"定时组 {index + 1}")
        self.header.title_edit.setText(f"定时组 {index + 1}")
        layout.addWidget(self.header)

        # 📍 位置
        pos_card = ConfigCard("📍", "位置")
        self.pos_chip = ValueChip("未选择")
        pos_btn = TextButton("选择位置")
        pos_btn.setObjectName("regionAction")
        pos_btn.clicked.connect(self._select_position)
        pos_card.add_action_row("", self.pos_chip, pos_btn)
        self.pos_chip.label.clicked.connect(self._preview_position)
        layout.addWidget(pos_card)

        # ⚙️ 触发
        trigger_card = ConfigCard("⚙️", "触发")
        self.cycle_widget = CycleControlWidget()
        trigger_card.add_row("", self.cycle_widget, stretch=1)
        self.key_input = KeyCaptureWidget()
        self.delay_min_spin = QSpinBox()
        self.delay_min_spin.setRange(0, 9999)
        self.delay_min_spin.setValue(300)
        self.delay_min_spin.setSuffix(" ms")
        self.delay_min_spin.setFixedWidth(56)
        self.delay_max_spin = QSpinBox()
        self.delay_max_spin.setRange(0, 9999)
        self.delay_max_spin.setValue(500)
        self.delay_max_spin.setSuffix(" ms")
        self.delay_max_spin.setFixedWidth(56)
        self.click_toggle = SwitchButton(compact=True)
        self.offset_spin = QSpinBox()
        self.offset_spin.setRange(0, 200)
        self.offset_spin.setValue(0)
        self.offset_spin.setSuffix(" px")
        self.offset_spin.setFixedWidth(58)
        self.offset_spin.setToolTip("点击位置随机偏移范围（像素），0=关闭")
        self.alarm_toggle = SwitchButton(compact=True)
        trigger_card.add_segments_row(
            "时长",
            ("", spin_range_row(self.delay_min_spin, self.delay_max_spin)),
        )
        trigger_card.add_segments_row("按键", ("", self.key_input))
        trigger_card.add_segments_row(
            "偏移",
            ("", self.offset_spin),
            ("是否点击", self.click_toggle),
            ("是否报警", self.alarm_toggle),
        )
        self.click_toggle.stateChanged.connect(self.offset_spin.setEnabled)
        self.offset_spin.setEnabled(self.click_toggle.isChecked())
        layout.addWidget(trigger_card)

        layout.addStretch()

    def set_config(self, cfg):
        self._enabled = cfg.get("enabled", True)
        name = cfg.get("name", "")
        if name:
            self.header.title_edit.setText(name)
        try:
            self.cycle_widget.set_interval_value(float(cfg.get("interval", 10)))
            cycle = cfg.get("cycle_enabled", True)
            if isinstance(cycle, str):
                cycle = cycle.lower() in ("true", "1")
            self.cycle_widget.set_cycle_enabled(bool(cycle))
            self.delay_min_spin.setValue(int(cfg.get("delay_min", 300)))
            self.delay_max_spin.setValue(int(cfg.get("delay_max", 500)))
            self.offset_spin.setValue(int(cfg.get("click_offset", 0)))
            self._pos_x = int(cfg.get("position_x", 0))
            self._pos_y = int(cfg.get("position_y", 0))
        except (ValueError, TypeError):
            pass
        if self._pos_x or self._pos_y:
            self.pos_chip.set_text(f"({self._pos_x}, {self._pos_y})", accent=True)
        key = cfg.get("key", "")
        self.key_input.setKey(key)
        self.click_toggle.setChecked(cfg.get("click_enabled", False))
        self.alarm_toggle.setChecked(cfg.get("alarm", False))

    def set_title(self, index):
        self.index = index
        self.header.title_edit.setText(f"定时组 {index + 1}")

    def collect_config(self):
        return {
            "name": self.header.title_edit.text(),
            "enabled": self._enabled,
            "interval": str(self.cycle_widget.interval_value()),
            "pause": "0",
            "cycle_enabled": self.cycle_widget.is_cycle_enabled(),
            "key": self.key_input.key(),
            "delay_min": str(self.delay_min_spin.value()),
            "delay_max": str(self.delay_max_spin.value()),
            "alarm": self.alarm_toggle.isChecked(),
            "click_enabled": self.click_toggle.isChecked(),
            "click_offset": str(self.offset_spin.value()),
            "position_x": str(self._pos_x),
            "position_y": str(self._pos_y),
            "position": f"{self._pos_x},{self._pos_y}",
        }

    def _select_position(self):
        from ui.widgets import hide_for_capture
        hide_for_capture(self)
        self.position_selection_requested.emit(self.index)

    def _on_pos_selected(self, x, y):
        self._pos_x = x
        self._pos_y = y
        self.pos_chip.set_text(f"({x}, {y})", accent=True)
        from ui.widgets import show_after_capture
        show_after_capture(self)

    def _preview_position(self):
        if self._pos_x or self._pos_y:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(
                None, "位置坐标",
                f"X: {self._pos_x}\nY: {self._pos_y}"
            )
        else:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(None, "提示", "未选择位置")
