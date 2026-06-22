from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QLineEdit,
    QSpinBox, QCheckBox, QGroupBox,
    QGridLayout, QSizePolicy, QButtonGroup
)
from PySide6.QtCore import Qt, Signal

from ui.theme import Colors
from ui.widgets import SectionTitle, GroupCard, PrimaryButton, DangerButton, Divider, InfoLabel, TextButton
from ui.components import ComboBox
from ui.components import Toggle
from ui.components import KeyCaptureWidget
from core.config import ConfigVar


class OCRPanel(QWidget):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.groups = []
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(20)

        header = QHBoxLayout()
        header.setSpacing(16)

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
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(12)
        self.scroll_layout.addStretch()
        self.scroll.setWidget(scroll_content)
        layout.addWidget(self.scroll, 1)

        self.add_group()
        self.add_group()

    def add_group(self):
        idx = len(self.groups)
        group = OCRGroupWidget(self.app, idx)
        self.scroll_layout.insertWidget(self.scroll_layout.count() - 1, group)
        self.groups.append(group)
        group.delete_requested.connect(lambda: self._delete_group(group))

    def _delete_group(self, group):
        if group in self.groups:
            self.groups.remove(group)
            self.scroll_layout.removeWidget(group)
            group.setParent(None)
            group.deleteLater()
            self._renumber()

    def _renumber(self):
        for i, g in enumerate(self.groups):
            g.set_title(i)

    def collect_config(self):
        return [g.collect_config() for g in self.groups]

    def set_enabled(self, enabled):
        super().setEnabled(enabled)

    def set_config(self, config_list):
        for g in self.groups[:]:
            self._delete_group(g)
        for cfg in config_list:
            self.add_group()
            self.groups[-1].set_config(cfg)


class OCRGroupWidget(GroupCard):
    delete_requested = Signal()

    def __init__(self, app, index, parent=None):
        super().__init__(parent)
        self.app = app
        self.index = index

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(20)

        # Header row
        header = QHBoxLayout()
        self.title_label = QLabel(f"识别组 {index + 1}")
        self.title_label.setObjectName("cardTitle")
        header.addWidget(self.title_label)

        header.addStretch()

        self.toggle = Toggle("启用")
        header.addWidget(self.toggle)

        del_btn = DangerButton("删除")
        del_btn.setCursor(Qt.PointingHandCursor)
        del_btn.clicked.connect(self.delete_requested.emit)
        header.addWidget(del_btn)

        layout.addLayout(header)

        # Grid content
        grid = QGridLayout()
        grid.setSpacing(16)
        grid.setColumnStretch(1, 1)

        # Region
        grid.addWidget(QLabel("识别区域"), 0, 0)
        self.region_label = InfoLabel("未选择")
        grid.addWidget(self.region_label, 0, 1)
        region_btn = TextButton("选择区域")
        region_btn.clicked.connect(self._select_region)
        grid.addWidget(region_btn, 0, 2)

        # Keywords
        grid.addWidget(QLabel("关键词"), 1, 0)
        self.keywords_input = QLineEdit()
        self.keywords_input.setPlaceholderText("多个关键词用 , 分隔")
        grid.addWidget(self.keywords_input, 1, 1, 1, 2)

        # Row 2: Language + Interval side by side
        row2 = QHBoxLayout()
        row2.setSpacing(16)
        row2.addWidget(QLabel("语言"))
        self.lang_combo = ComboBox(items=["简体中文", "繁体中文", "英文"])
        row2.addWidget(self.lang_combo)
        row2.addSpacing(8)
        row2.addWidget(QLabel("间隔(秒)"))
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 999)
        self.interval_spin.setValue(3)
        self.interval_spin.setFixedWidth(70)
        row2.addWidget(self.interval_spin)
        row2.addStretch()
        grid.addLayout(row2, 2, 0, 1, 3)

        # Row 3: Pause + Delay side by side
        row3 = QHBoxLayout()
        row3.setSpacing(16)
        row3.addWidget(QLabel("暂停(秒)"))
        self.pause_spin = QSpinBox()
        self.pause_spin.setRange(0, 999)
        self.pause_spin.setValue(3)
        self.pause_spin.setFixedWidth(70)
        row3.addWidget(self.pause_spin)
        row3.addSpacing(8)
        row3.addWidget(QLabel("延迟(秒)"))
        self.delay_min_spin = QSpinBox()
        self.delay_min_spin.setRange(0, 10)
        self.delay_min_spin.setValue(1)
        self.delay_min_spin.setFixedWidth(70)
        row3.addWidget(self.delay_min_spin)
        row3.addWidget(QLabel("~"))
        self.delay_max_spin = QSpinBox()
        self.delay_max_spin.setRange(0, 10)
        self.delay_max_spin.setValue(3)
        self.delay_max_spin.setFixedWidth(70)
        row3.addWidget(self.delay_max_spin)
        row3.addStretch()
        grid.addLayout(row3, 3, 0, 1, 3)

        # Key
        grid.addWidget(QLabel("触发按键"), 4, 0)
        self.key_input = KeyCaptureWidget()
        grid.addWidget(self.key_input, 4, 1)

        # Toggles row
        toggles = QHBoxLayout()
        toggles.setSpacing(24)
        self.click_toggle = Toggle("识别后点击")
        toggles.addWidget(self.click_toggle)
        toggles.addWidget(QLabel("偏移"))
        self.offset_spin = QSpinBox()
        self.offset_spin.setRange(0, 200)
        self.offset_spin.setValue(0)
        self.offset_spin.setSuffix("px")
        self.offset_spin.setFixedWidth(70)
        self.offset_spin.setToolTip("点击位置随机偏移范围（像素），0=关闭")
        toggles.addWidget(self.offset_spin)
        self.alarm_toggle = Toggle("触发时响铃")
        toggles.addWidget(self.alarm_toggle)
        toggles.addStretch()
        grid.addLayout(toggles, 5, 0, 1, 3)

        layout.addLayout(grid)

        # Config data
        self.region = None
        self.keywords = ""
        self.language = "chi_sim"

    def collect_config(self):
        return {
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
            self.key_input.set_key(key)
        self.keywords_input.setText(cfg.get("keywords", ""))
        lang = cfg.get("language", "简体中文")
        idx = self.lang_combo.findText(lang)
        if idx >= 0:
            self.lang_combo.setCurrentIndex(idx)
        self.click_toggle.setChecked(cfg.get("click", False))
        self.alarm_toggle.setChecked(cfg.get("alarm", False))

    def set_title(self, index):
        self.index = index
        self.title_label.setText(f"识别组 {index + 1}")

    def _select_region(self):
        from ui.components.region_overlay import RegionOverlay
        self.overlay = RegionOverlay("ocr")
        self.overlay.region_selected.connect(self._on_region_selected)
        self.overlay.show()

    def _on_region_selected(self, x1, y1, x2, y2):
        self.region = (x1, y1, x2, y2)
        self.region_label.setText(f"({x1}, {y1}) → ({x2}, {y2})")
        self.region_label.setStyleSheet("color: #8AB4F8; font-weight: 500; font-size: 13px;")
