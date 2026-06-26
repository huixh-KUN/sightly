from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QScrollArea, QFrame,
    QSpinBox, QDoubleSpinBox, QGridLayout
)
from PySide6.QtCore import Qt, Signal

from ui.widgets import (
    SectionTitle, PrimaryButton,
    TextButton, ClickableLabel,
    GroupListItem, GroupEditWindow,
)
from ui.components import SwitchButton
from ui.components import KeyCaptureWidget
from ui.components import ConfigCard
from ui.components import GroupEditHeader, ValueChip
from ui.components.form_rows import spin_range_row
from core.config import ConfigVar


class NumberPanel(QWidget):
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
        title_col.addWidget(SectionTitle("数字识别"))
        subtitle = QLabel("识别屏幕中的数字变化，满足条件时触发动作")
        subtitle.setObjectName("subtitle")
        title_col.addWidget(subtitle)
        header.addLayout(title_col)
        header.addStretch()

        add_btn = PrimaryButton("＋ 新增识别组")
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

    def add_group(self):
        idx = len(self.groups_data)
        default = self._default_config(idx)
        self.groups_data.append(default)
        self._add_list_item(idx, default)

    def _default_config(self, idx):
        return {
            "name": f"识别组 {idx + 1}",
            "enabled": True,
            "region": None,
            "threshold": "500",
            "confidence_threshold": "0.3",
            "key": "",
            "delay_min": "100",
            "delay_max": "200",
            "alarm": False,
        }

    def _add_list_item(self, idx, data):
        item = GroupListItem(idx, "number", parent=self)
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
            self._edit_window.close()
            self._edit_window = None
        if 0 <= idx < len(self.groups_data):
            self._edit_window = GroupEditWindow(
                self.groups_data[idx], idx, "number", panel=self,
                parent=self.window(),
            )
            self._edit_window.exec()
            self._edit_window = None

    def _on_edit_window_closed(self, idx, editor):
        if 0 <= idx < len(self.groups_data):
            cfg = editor.collect_config()
            plain = {k: (v.get() if hasattr(v, 'get') else v) for k, v in cfg.items()}
            plain["enabled"] = self.groups_data[idx].get("enabled", True)
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


class NumberGroupWidget(QFrame):

    def __init__(self, index, parent=None):
        super().__init__(parent)
        self.index = index
        self.region = None
        self._enabled = True

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 16)
        layout.setSpacing(14)

        self.header = GroupEditHeader(f"识别组 {index + 1}")
        self.header.title_edit.setText(f"识别组 {index + 1}")
        layout.addWidget(self.header)

        # 📍 区域
        region_card = ConfigCard("📍", "区域")
        self.region_chip = ValueChip("未选择")
        region_btn = TextButton("选择区域")
        region_btn.setObjectName("regionAction")
        region_btn.clicked.connect(self._select_region)
        region_card.add_action_row("", self.region_chip, region_btn)
        self.region_chip.label.clicked.connect(self._preview_region)
        layout.addWidget(region_card)

        # 🎯 检测
        detect_card = ConfigCard("🎯", "检测")
        self.threshold_spin = QSpinBox()
        self.threshold_spin.setRange(1, 9999)
        self.threshold_spin.setValue(500)
        self.threshold_spin.setSuffix(" 数值")
        self.threshold_spin.setFixedWidth(64)
        self.confidence_spin = QDoubleSpinBox()
        self.confidence_spin.setRange(0.0, 1.0)
        self.confidence_spin.setSingleStep(0.05)
        self.confidence_spin.setValue(0.3)
        self.confidence_spin.setDecimals(2)
        self.confidence_spin.setFixedWidth(58)
        self.confidence_spin.setToolTip("OCR 置信度低于此值的结果被丢弃（0=关闭）")
        detect_card.add_segments_row(
            "阈值",
            ("", self.threshold_spin),
            ("置信度", self.confidence_spin),
        )
        layout.addWidget(detect_card)

        # ⚙️ 触发
        trigger_card = ConfigCard("⚙️", "触发")
        self.key_input = KeyCaptureWidget()
        self.delay_min_spin = QSpinBox()
        self.delay_min_spin.setRange(0, 9999)
        self.delay_min_spin.setValue(100)
        self.delay_min_spin.setSuffix(" ms")
        self.delay_min_spin.setFixedWidth(62)
        self.delay_max_spin = QSpinBox()
        self.delay_max_spin.setRange(0, 9999)
        self.delay_max_spin.setValue(200)
        self.delay_max_spin.setSuffix(" ms")
        self.delay_max_spin.setFixedWidth(62)
        self.alarm_toggle = SwitchButton(compact=True)
        trigger_card.add_segments_row(
            "按键",
            ("", self.key_input),
            ("时长", spin_range_row(self.delay_min_spin, self.delay_max_spin)),
        )
        trigger_card.add_row("是否报警", self.alarm_toggle)
        layout.addWidget(trigger_card)

        layout.addStretch()

    def set_config(self, cfg):
        self._enabled = cfg.get("enabled", True)
        name = cfg.get("name", "")
        if name:
            self.header.title_edit.setText(name)
        region = cfg.get("region")
        if region:
            self.region = tuple(region)
            x1, y1, x2, y2 = self.region
            self.region_chip.set_text(f"({x1}, {y1}) → ({x2}, {y2})", accent=True)
        try:
            self.threshold_spin.setValue(int(cfg.get("threshold", 500)))
            self.confidence_spin.setValue(float(cfg.get("confidence_threshold", 0.3)))
            self.delay_min_spin.setValue(int(cfg.get("delay_min", 100)))
            self.delay_max_spin.setValue(int(cfg.get("delay_max", 200)))
        except (ValueError, TypeError):
            pass
        key = cfg.get("key", "")
        if key:
            self.key_input.setKey(key)
        self.alarm_toggle.setChecked(cfg.get("alarm", False))

    def set_title(self, index):
        self.index = index
        self.header.title_edit.setText(f"识别组 {index + 1}")

    def collect_config(self):
        return {
            "name": self.header.title_edit.text(),
            "enabled": ConfigVar(self._enabled),
            "region": self.region,
            "threshold": ConfigVar(str(self.threshold_spin.value())),
            "confidence_threshold": ConfigVar(str(self.confidence_spin.value())),
            "key": ConfigVar(self.key_input.key()),
            "delay_min": ConfigVar(str(self.delay_min_spin.value())),
            "delay_max": ConfigVar(str(self.delay_max_spin.value())),
            "alarm": ConfigVar(self.alarm_toggle.isChecked()),
        }

    def _select_region(self):
        from ui.components.region_overlay import RegionOverlay
        self.overlay = RegionOverlay("number")
        self.overlay.region_selected.connect(self._on_region_selected)
        from ui.widgets import suspend_group_edit_capture, resume_group_edit_capture
        suspend_group_edit_capture(self)
        self.overlay.show()

    def _on_region_selected(self, x1, y1, x2, y2):
        self.region = (x1, y1, x2, y2)
        self.region_chip.set_text(f"({x1}, {y1}) → ({x2}, {y2})", accent=True)
        from ui.widgets import resume_group_edit_capture
        resume_group_edit_capture(self)

    def _preview_region(self):
        if self.region:
            from PySide6.QtWidgets import QMessageBox
            x1, y1, x2, y2 = self.region
            QMessageBox.information(
                None, "区域坐标",
                f"左上: ({x1}, {y1})\n右下: ({x2}, {y2})\n尺寸: {x2-x1} × {y2-y1}"
            )
        else:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(None, "提示", "未设置检测区域")
