from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QScrollArea, QFrame,
    QSpinBox, QGridLayout
)
from PySide6.QtCore import Qt, Signal

from ui.theme import Colors
from ui.widgets import (
    SectionTitle, PrimaryButton,
    DangerButton, TextButton, ClickableLabel,
    GroupListItem, GroupEditWindow,
)
from ui.components import Toggle
from ui.components import KeyCaptureWidget
from ui.components import ConfigCard
from core.config import ConfigVar


class TimedPanel(QWidget):
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
            self._edit_window.close()
            self._edit_window = None
        if 0 <= idx < len(self.groups_data):
            self._edit_window = GroupEditWindow(
                self.app, self.groups_data[idx], idx, "timed", panel=self
            )
            self._edit_window.show()

    def _on_edit_window_closed(self, idx, editor):
        if 0 <= idx < len(self.groups_data):
            cfg = editor.collect_config()
            plain = {k: (v.get() if hasattr(v, 'get') else v) for k, v in cfg.items()}
            self.groups_data[idx] = plain
            if idx < len(self.list_items):
                self.list_items[idx].set_data(plain)
        self._edit_window = None

    def set_enabled(self, enabled):
        self._view_only = not enabled

    def collect_config(self):
        return [{k: ConfigVar(v) for k, v in g.items()} for g in self.groups_data]

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

    def __init__(self, app, index, parent=None):
        super().__init__(parent)
        self.app = app
        self.index = index
        self._pos_x = 0
        self._pos_y = 0

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        self.title_edit = QLineEdit(f"定时组 {index + 1}")
        self.title_edit.setStyleSheet("font-size: 16px; font-weight: 600; background: transparent; border: none; color: #E8EAED;")
        header.addWidget(self.title_edit)
        header.addStretch()
        self.toggle = Toggle("启用")
        header.addWidget(self.toggle)
        layout.addLayout(header)

        # ⚙️ 触发
        trigger_card = ConfigCard("⚙️", "触发")
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 9999)
        self.interval_spin.setValue(10)
        self.interval_spin.setSuffix(" 秒")
        self.interval_spin.setFixedWidth(120)
        trigger_card.add_row("执行间隔", self.interval_spin)
        self.key_input = KeyCaptureWidget()
        trigger_card.add_row("按键", self.key_input)
        delay_row = QHBoxLayout()
        self.delay_min_spin = QSpinBox()
        self.delay_min_spin.setRange(0, 9999)
        self.delay_min_spin.setValue(300)
        self.delay_min_spin.setSuffix(" ms")
        self.delay_min_spin.setFixedWidth(80)
        delay_row.addWidget(self.delay_min_spin)
        delay_row.addWidget(QLabel("~"))
        self.delay_max_spin = QSpinBox()
        self.delay_max_spin.setRange(0, 9999)
        self.delay_max_spin.setValue(500)
        self.delay_max_spin.setSuffix(" ms")
        self.delay_max_spin.setFixedWidth(80)
        delay_row.addWidget(self.delay_max_spin)
        delay_row.addStretch()
        trigger_card.add_row("按键时长", delay_row)
        click_row = QHBoxLayout()
        self.click_toggle = Toggle("点击触发")
        click_row.addWidget(self.click_toggle)
        click_row.addWidget(QLabel("偏移"))
        self.offset_spin = QSpinBox()
        self.offset_spin.setRange(0, 200)
        self.offset_spin.setValue(0)
        self.offset_spin.setSuffix("px")
        self.offset_spin.setFixedWidth(70)
        self.offset_spin.setToolTip("点击位置随机偏移范围（像素），0=关闭")
        click_row.addWidget(self.offset_spin)
        click_row.addStretch()
        trigger_card.add_widget_row(click_row)
        layout.addWidget(trigger_card)

        # 📍 位置
        pos_card = ConfigCard("📍", "位置")
        pos_row = QHBoxLayout()
        self.pos_label = ClickableLabel("未选择")
        self.pos_label.setObjectName("infoText")
        pos_row.addWidget(self.pos_label)
        pos_btn = TextButton("选择位置")
        pos_btn.setObjectName("regionAction")
        pos_btn.clicked.connect(self._select_position)
        pos_row.addWidget(pos_btn)
        pos_row.addStretch()
        pos_card.add_widget_row(pos_row)
        self.pos_label.clicked.connect(self._preview_position)
        layout.addWidget(pos_card)

        # 🔔 报警
        alarm_card = ConfigCard("🔔", "报警")
        self.alarm_toggle = Toggle("触发时响铃")
        alarm_card.set_content(self.alarm_toggle)
        layout.addWidget(alarm_card)

        layout.addStretch()

    def set_config(self, cfg):
        self.toggle.setChecked(cfg.get("enabled", False))
        name = cfg.get("name", "")
        if name:
            self.title_edit.setText(name)
        try:
            self.interval_spin.setValue(int(cfg.get("interval", 10)))
            self.delay_min_spin.setValue(int(cfg.get("delay_min", 300)))
            self.delay_max_spin.setValue(int(cfg.get("delay_max", 500)))
            self.offset_spin.setValue(int(cfg.get("click_offset", 0)))
            self._pos_x = int(cfg.get("position_x", 0))
            self._pos_y = int(cfg.get("position_y", 0))
        except (ValueError, TypeError):
            pass
        if self._pos_x or self._pos_y:
            self.pos_label.setText(f"({self._pos_x}, {self._pos_y})")
            self.pos_label.setStyleSheet("color: #8AB4F8; font-weight: 500;")
        key = cfg.get("key", "")
        if key:
            self.key_input.setKey(key)
        self.click_toggle.setChecked(cfg.get("click_enabled", False))
        self.alarm_toggle.setChecked(cfg.get("alarm", False))

    def set_title(self, index):
        self.index = index
        self.title_edit.setText(f"定时组 {index + 1}")

    def collect_config(self):
        return {
            "name": self.title_edit.text(),
            "enabled": ConfigVar(self.toggle.isChecked()),
            "interval": ConfigVar(str(self.interval_spin.value())),
            "key": ConfigVar(self.key_input.key()),
            "delay_min": ConfigVar(str(self.delay_min_spin.value())),
            "delay_max": ConfigVar(str(self.delay_max_spin.value())),
            "alarm": ConfigVar(self.alarm_toggle.isChecked()),
            "click_enabled": ConfigVar(self.click_toggle.isChecked()),
            "click_offset": ConfigVar(str(self.offset_spin.value())),
            "position_x": ConfigVar(str(self._pos_x)),
            "position_y": ConfigVar(str(self._pos_y)),
            "position": f"{self._pos_x},{self._pos_y}",
        }

    def _select_position(self):
        w = self.window()
        if w and isinstance(w, GroupEditWindow):
            w.hide()
            pw = w.parent()
            if pw:
                pw.hide()
        self.app.timed_module.start_timed_position_selection(
            self.index,
            on_selected=lambda x, y: self._on_pos_selected(x, y)
        )

    def _on_pos_selected(self, x, y):
        self._pos_x = x
        self._pos_y = y
        self.pos_label.setText(f"({x}, {y})")
        self.pos_label.setStyleSheet("color: #8AB4F8; font-weight: 500;")
        w = self.window()
        if w and isinstance(w, GroupEditWindow):
            pw = w.parent()
            if pw:
                pw.show()
            w.show()

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
