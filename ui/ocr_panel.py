from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QLineEdit,
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
from ui.components import ComboBox
from ui.components import KeyCaptureWidget
from ui.components import ConfigCard
from core.config import ConfigVar


class OCRPanel(QWidget):
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
                self.app, self.groups_data[idx], idx, "ocr", panel=self
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


class OCRGroupWidget(QFrame):

    def __init__(self, app, index, parent=None):
        super().__init__(parent)
        self.app = app
        self.index = index
        self.region = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        self.title_edit = QLineEdit(f"识别组 {index + 1}")
        self.title_edit.setStyleSheet("font-size: 16px; font-weight: 600; background: transparent; border: none; color: #E8EAED;")
        header.addWidget(self.title_edit)
        header.addStretch()
        self.toggle = Toggle("启用")
        header.addWidget(self.toggle)
        layout.addLayout(header)

        # 📍 区域
        region_card = ConfigCard("📍", "区域")
        region_row = QHBoxLayout()
        self.region_label = ClickableLabel("未选择")
        self.region_label.setObjectName("infoText")
        region_row.addWidget(self.region_label, 1)
        region_btn = TextButton("选择区域")
        region_btn.setObjectName("regionAction")
        region_btn.clicked.connect(self._select_region)
        region_row.addWidget(region_btn)
        self.region_label.clicked.connect(self._preview_region)
        region_card.add_widget_row(region_row)
        layout.addWidget(region_card)

        # ⚙️ 触发
        trigger_card = ConfigCard("⚙️", "触发")
        self.key_input = KeyCaptureWidget()
        trigger_card.add_row("按键", self.key_input)
        delay_row = QHBoxLayout()
        self.delay_min_spin = QSpinBox()
        self.delay_min_spin.setRange(0, 10)
        self.delay_min_spin.setValue(1)
        self.delay_min_spin.setFixedWidth(70)
        delay_row.addWidget(self.delay_min_spin)
        delay_row.addWidget(QLabel("~"))
        self.delay_max_spin = QSpinBox()
        self.delay_max_spin.setRange(0, 10)
        self.delay_max_spin.setValue(3)
        self.delay_max_spin.setFixedWidth(70)
        delay_row.addWidget(self.delay_max_spin)
        delay_row.addStretch()
        trigger_card.add_row("延迟(秒)", delay_row)
        click_row = QHBoxLayout()
        self.click_toggle = Toggle("点击")
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

        # 🔔 报警
        alarm_card = ConfigCard("🔔", "报警")
        self.alarm_toggle = Toggle("触发时响铃")
        alarm_card.set_content(self.alarm_toggle)
        layout.addWidget(alarm_card)

        # 🎯 匹配
        match_card = ConfigCard("🎯", "匹配")
        self.keywords_input = QLineEdit()
        self.keywords_input.setPlaceholderText("多个关键词用 , 分隔")
        match_card.add_row("关键词", self.keywords_input)
        self.lang_combo = ComboBox(items=["简体中文", "繁体中文", "英文"])
        match_card.add_row("语言", self.lang_combo)
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 999)
        self.interval_spin.setValue(3)
        self.interval_spin.setFixedWidth(70)
        match_card.add_row("间隔(秒)", self.interval_spin)
        self.pause_spin = QSpinBox()
        self.pause_spin.setRange(0, 999)
        self.pause_spin.setValue(3)
        self.pause_spin.setFixedWidth(70)
        match_card.add_row("暂停(秒)", self.pause_spin)
        layout.addWidget(match_card)

        layout.addStretch()

    def collect_config(self):
        return {
            "name": self.title_edit.text(),
            "enabled": ConfigVar(self.toggle.isChecked()),
            "region": self.region,
            "interval": ConfigVar(str(self.interval_spin.value())),
            "pause": ConfigVar(str(self.pause_spin.value())),
            "key": ConfigVar(self.key_input.key()),
            "delay_min": ConfigVar(str(self.delay_min_spin.value())),
            "delay_max": ConfigVar(str(self.delay_max_spin.value())),
            "alarm": ConfigVar(self.alarm_toggle.isChecked()),
            "click": ConfigVar(self.click_toggle.isChecked()),
            "click_offset": ConfigVar(str(self.offset_spin.value())),
            "keywords": ConfigVar(self.keywords_input.text()),
            "language": ConfigVar(self.lang_combo.currentText()),
        }

    def set_config(self, cfg):
        self.toggle.setChecked(cfg.get("enabled", False))
        name = cfg.get("name", "")
        if name:
            self.title_edit.setText(name)
        region = cfg.get("region")
        if region:
            self.region = tuple(region)
            x1, y1, x2, y2 = self.region
            self.region_label.setText(f"({x1}, {y1}) → ({x2}, {y2})")
            self.region_label.setStyleSheet("color: #8AB4F8; font-weight: 500;")
        try:
            self.interval_spin.setValue(int(cfg.get("interval", 3)))
            self.pause_spin.setValue(int(cfg.get("pause", 3)))
            self.delay_min_spin.setValue(int(cfg.get("delay_min", 1)))
            self.delay_max_spin.setValue(int(cfg.get("delay_max", 3)))
            self.offset_spin.setValue(int(cfg.get("click_offset", 0)))
        except (ValueError, TypeError):
            pass
        key = cfg.get("key", "")
        if key:
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
        self.title_edit.setText(f"识别组 {index + 1}")

    def _select_region(self):
        from ui.components.region_overlay import RegionOverlay
        self.overlay = RegionOverlay("ocr")
        self.overlay.region_selected.connect(self._on_region_selected)
        w = self.window()
        if w and isinstance(w, GroupEditWindow):
            w.hide()
            pw = w.parent()
            if pw:
                pw.hide()
        self.overlay.show()

    def _on_region_selected(self, x1, y1, x2, y2):
        self.region = (x1, y1, x2, y2)
        self.region_label.setText(f"({x1}, {y1}) → ({x2}, {y2})")
        self.region_label.setStyleSheet("color: #8AB4F8; font-weight: 500; font-size: 13px;")
        w = self.window()
        if w and isinstance(w, GroupEditWindow):
            pw = w.parent()
            if pw:
                pw.show()
            w.show()

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
