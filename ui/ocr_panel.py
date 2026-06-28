from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QLineEdit,
    QSpinBox, QGridLayout
)
from PySide6.QtCore import Qt, Signal

from ui.widgets import (
    SectionTitle, PrimaryButton,
    TextButton, ClickableLabel,
    GroupListItem, GroupEditWindow,
)
from ui.components import SwitchButton, CycleControlWidget
from ui.components import ComboBox
from ui.components import KeyCaptureWidget
from ui.components import ConfigCard
from ui.components import GroupEditHeader, ValueChip
from ui.components.form_rows import spin_range_row



class OCRPanel(QWidget):
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
        title_col.addWidget(SectionTitle("文字识别 OCR"))
        subtitle = QLabel("配置 OCR 识别区域和触发规则")
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
            "interval": "3",
            "pause": "3",
            "key": "",
            "delay_min": "1",
            "delay_max": "3",
            "alarm": False,
            "click": False,
            "click_offset": "0",
            "keywords": "",
            "language": "简体中文",
        }

    def _add_list_item(self, idx, data):
        item = GroupListItem(idx, "ocr", parent=self)
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
                self.groups_data[idx], idx, "ocr", panel=self,
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


class OCRGroupWidget(QFrame):

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
        self.keywords_input = QLineEdit()
        self.keywords_input.setPlaceholderText("多个关键词用 , 分隔")
        detect_card.add_row("关键词", self.keywords_input, stretch=1)
        self.lang_combo = ComboBox(items=["简体中文", "繁体中文", "英文"], width=100)
        detect_card.add_row("语言", self.lang_combo)
        self.cycle_widget = CycleControlWidget()
        detect_card.add_row("", self.cycle_widget, stretch=1)
        layout.addWidget(detect_card)

        # ⚙️ 触发
        trigger_card = ConfigCard("⚙️", "触发")
        self.key_input = KeyCaptureWidget()
        self.delay_min_spin = QSpinBox()
        self.delay_min_spin.setRange(0, 10)
        self.delay_min_spin.setValue(1)
        self.delay_min_spin.setSuffix(" 秒")
        self.delay_min_spin.setFixedWidth(56)
        self.delay_max_spin = QSpinBox()
        self.delay_max_spin.setRange(0, 10)
        self.delay_max_spin.setValue(3)
        self.delay_max_spin.setSuffix(" 秒")
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
            "按键",
            ("", self.key_input),
            ("延迟", spin_range_row(self.delay_min_spin, self.delay_max_spin)),
        )
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

    def collect_config(self):
        return {
            "name": self.header.title_edit.text(),
            "enabled": self._enabled,
            "region": self.region,
            "interval": str(self.cycle_widget.interval_value()),
            "cycle_enabled": self.cycle_widget.is_cycle_enabled(),
            "key": self.key_input.key(),
            "delay_min": str(self.delay_min_spin.value()),
            "delay_max": str(self.delay_max_spin.value()),
            "alarm": self.alarm_toggle.isChecked(),
            "click": self.click_toggle.isChecked(),
            "click_offset": str(self.offset_spin.value()),
            "keywords": self.keywords_input.text(),
            "language": self.lang_combo.currentText(),
        }

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
            self.cycle_widget.set_interval_value(float(cfg.get("interval", 0)))
            cycle = cfg.get("cycle_enabled", True)
            if isinstance(cycle, str):
                cycle = cycle.lower() in ("true", "1")
            self.cycle_widget.set_cycle_enabled(bool(cycle))
            self.delay_min_spin.setValue(int(cfg.get("delay_min", 1)))
            self.delay_max_spin.setValue(int(cfg.get("delay_max", 3)))
            self.offset_spin.setValue(int(cfg.get("click_offset", 0)))
        except (ValueError, TypeError):
            pass
        key = cfg.get("key", "")
        self.key_input.setKey(key)
        self.keywords_input.setText(cfg.get("keywords", ""))
        lang = cfg.get("language", "简体中文")
        idx = self.lang_combo.findText(lang)
        if idx >= 0:
            self.lang_combo.setCurrentIndex(idx)
        self.click_toggle.setChecked(cfg.get("click", False))
        self.alarm_toggle.setChecked(cfg.get("alarm", False))

    def set_title(self, index):
        self.index = index
        self.header.title_edit.setText(f"识别组 {index + 1}")

    def _select_region(self):
        from ui.components.region_overlay import RegionOverlay
        self.overlay = RegionOverlay("ocr")
        self.overlay.region_selected.connect(self._on_region_selected)
        self.overlay.closed.connect(self._show_after_capture)
        w = self.window()
        if w and isinstance(w, GroupEditWindow):
            w.hide()
        self.overlay.show()

    def _show_after_capture(self):
        w = self.window()
        if w and isinstance(w, GroupEditWindow):
            w.show()
            w.raise_()
            w.activateWindow()

    def _on_region_selected(self, x1, y1, x2, y2):
        self.region = (x1, y1, x2, y2)
        self.region_chip.set_text(f"({x1}, {y1}) → ({x2}, {y2})", accent=True)
        self._show_after_capture()

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
