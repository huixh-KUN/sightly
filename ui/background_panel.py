from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QFrame, QLineEdit,
    QSpinBox, QGridLayout,
    QFileDialog, QColorDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap

from ui.widgets import SectionTitle, GroupCard, PrimaryButton, DangerButton, InfoLabel
from ui.components import ComboBox
from ui.components import Toggle
from ui.components import TemplatePicker, KeyCaptureWidget, WindowSelector
from core.config import ConfigVar


class BackgroundPanel(QWidget):
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
        title_col.addWidget(SectionTitle("后台监控"))
        subtitle = QLabel("监控指定窗口中的 OCR、图像和颜色变化")
        subtitle.setObjectName("subtitle")
        title_col.addWidget(subtitle)
        header.addLayout(title_col)
        header.addStretch()

        add_ocr_btn = PrimaryButton("＋ OCR")
        add_ocr_btn.setCursor(Qt.PointingHandCursor)
        add_ocr_btn.clicked.connect(lambda: self.add_group("ocr"))
        header.addWidget(add_ocr_btn)

        add_img_btn = PrimaryButton("＋ 图像")
        add_img_btn.setCursor(Qt.PointingHandCursor)
        add_img_btn.clicked.connect(lambda: self.add_group("image"))
        header.addWidget(add_img_btn)

        add_color_btn = PrimaryButton("＋ 颜色")
        add_color_btn.setCursor(Qt.PointingHandCursor)
        add_color_btn.clicked.connect(lambda: self.add_group("color"))
        header.addWidget(add_color_btn)

        layout.addLayout(header)

        window_card = QFrame()
        window_card.setObjectName("windowCard")
        w_layout = QHBoxLayout(window_card)
        w_layout.setContentsMargins(20, 16, 20, 16)
        w_layout.setSpacing(12)

        self._window_selector = WindowSelector()
        self._window_selector.window_selected.connect(self._on_window_selected)
        w_layout.addWidget(self._window_selector)

        layout.addWidget(window_card)

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

    def add_group(self, monitor_type="ocr"):
        idx = len(self.groups)
        group = BackgroundGroupWidget(self.app, idx, monitor_type)
        self.scroll_layout.insertWidget(self.scroll_layout.count() - 1, group)
        self.groups.append(group)
        group.delete_requested.connect(lambda: self._delete_group(group))

    def _delete_group(self, group):
        if group in self.groups:
            self.groups.remove(group)
            self.scroll_layout.removeWidget(group)
            group.deleteLater()
            self._renumber()

    def _renumber(self):
        for i, g in enumerate(self.groups):
            g.set_title(i)

    def collect_config(self):
        return [g.collect_config() for g in self.groups]

    def _on_window_selected(self, hwnd, title):
        self.app.background_manager.set_target_window(hwnd)


class BackgroundGroupWidget(GroupCard):
    delete_requested = Signal()

    def __init__(self, app, index, monitor_type="ocr", parent=None):
        super().__init__(parent)
        self.app = app
        self.index = index
        self.monitor_type = monitor_type
        self.region = None
        self.region_ratio = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(20)

        # Header
        header = QHBoxLayout()
        type_names = {"ocr": "OCR", "image": "图像", "color": "颜色"}
        type_icons = {"ocr": "📝", "image": "🖼️", "color": "🎨"}
        icon = type_icons.get(monitor_type, "📋")
        self.title_label = QLabel(f"{icon}  组 {index + 1} - {type_names.get(monitor_type, monitor_type)}")
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

        grid = QGridLayout()
        grid.setSpacing(16)
        grid.setColumnStretch(1, 1)

        # Region
        grid.addWidget(QLabel("监控区域"), 0, 0)
        self.region_label = InfoLabel("未选择")
        grid.addWidget(self.region_label, 0, 1)
        region_btn = QPushButton("选择区域")
        region_btn.setFixedWidth(90)
        region_btn.setCursor(Qt.PointingHandCursor)
        region_btn.clicked.connect(self._select_region)
        grid.addWidget(region_btn, 0, 2)

        if monitor_type == "ocr":
            # Keywords
            grid.addWidget(QLabel("关键词:"), 1, 0)
            self.keywords_input = QLineEdit()
            self.keywords_input.setPlaceholderText("多个关键词用 | 分隔")
            grid.addWidget(self.keywords_input, 1, 1, 1, 2)

            # Language
            lang_row = QHBoxLayout()
            lang_row.setSpacing(16)
            lang_row.addWidget(QLabel("语言"))
            self.lang_combo = ComboBox(items=["简体中文", "繁体中文", "英文"])
            lang_row.addWidget(self.lang_combo)
            lang_row.addStretch()
            grid.addLayout(lang_row, 2, 0, 1, 3)

        elif monitor_type == "image":
            grid.addWidget(QLabel("模板图像"), 1, 0)
            self.template_picker = TemplatePicker()
            self.template_picker.template_selected.connect(self._on_template_picked)
            grid.addWidget(self.template_picker, 1, 1, 1, 2)

            img_row = QHBoxLayout()
            img_row.setSpacing(16)
            img_row.addWidget(QLabel("匹配阈值"))
            self.threshold_spin = QSpinBox()
            self.threshold_spin.setRange(50, 100)
            self.threshold_spin.setValue(80)
            self.threshold_spin.setSuffix("%")
            img_row.addWidget(self.threshold_spin)
            img_row.addStretch()
            grid.addLayout(img_row, 2, 0, 1, 3)

        elif monitor_type == "color":
            grid.addWidget(QLabel("目标颜色"), 1, 0)
            color_layout = QHBoxLayout()
            self.color_hex = QLineEdit()
            self.color_hex.setPlaceholderText("#RRGGBB")
            self.color_hex.setMaxLength(7)
            color_layout.addWidget(self.color_hex)
            color_btn = QPushButton("取色")
            color_btn.setFixedWidth(60)
            color_btn.setCursor(Qt.PointingHandCursor)
            color_btn.clicked.connect(self._pick_color)
            color_layout.addWidget(color_btn)
            grid.addLayout(color_layout, 1, 1, 1, 2)

            color_row = QHBoxLayout()
            color_row.setSpacing(16)
            color_row.addWidget(QLabel("容差"))
            self.tolerance_spin = QSpinBox()
            self.tolerance_spin.setRange(0, 255)
            self.tolerance_spin.setValue(30)
            color_row.addWidget(self.tolerance_spin)
            color_row.addStretch()
            grid.addLayout(color_row, 2, 0, 1, 3)

        # Common fields
        common_row = QHBoxLayout()
        common_row.setSpacing(12)

        common_row.addWidget(QLabel("触发按键"))
        self.key_input = KeyCaptureWidget()
        common_row.addWidget(self.key_input, 1)

        self.click_toggle = Toggle("点击")
        common_row.addWidget(self.click_toggle)
        common_row.addWidget(QLabel("偏移"))
        self.offset_spin = QSpinBox()
        self.offset_spin.setRange(0, 200)
        self.offset_spin.setValue(0)
        self.offset_spin.setSuffix("px")
        self.offset_spin.setFixedWidth(70)
        self.offset_spin.setToolTip("点击位置随机偏移范围（像素），0=关闭")
        common_row.addWidget(self.offset_spin)

        self.alarm_toggle = Toggle("报警")
        common_row.addWidget(self.alarm_toggle)

        common_row.addStretch()
        grid.addLayout(common_row, 3, 0, 1, 3)

        # Interval and pause
        timing_row = QHBoxLayout()
        timing_row.setSpacing(12)
        timing_row.addWidget(QLabel("间隔(秒)"))
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 99)
        self.interval_spin.setValue(3)
        self.interval_spin.setFixedWidth(70)
        timing_row.addWidget(self.interval_spin)
        timing_row.addWidget(QLabel("暂停(秒)"))
        self.pause_spin = QSpinBox()
        self.pause_spin.setRange(0, 9999)
        self.pause_spin.setValue(180)
        self.pause_spin.setFixedWidth(70)
        timing_row.addWidget(self.pause_spin)
        timing_row.addStretch()
        grid.addLayout(timing_row, 4, 0, 1, 3)

        layout.addLayout(grid)

    def set_title(self, index):
        self.index = index
        type_names = {"ocr": "OCR", "image": "图像", "color": "颜色"}
        type_icons = {"ocr": "📝", "image": "🖼️", "color": "🎨"}
        icon = type_icons.get(self.monitor_type, "📋")
        self.title_label.setText(f"{icon}  组 {index + 1} - {type_names.get(self.monitor_type, self.monitor_type)}")

    def collect_config(self):
        region_ratio = None
        if self.region and hasattr(self.app, 'background_manager'):
            hwnd = self.app.background_manager.target_hwnd
            if hwnd:
                try:
                    from utils.window_capture import get_window_size
                    from utils.coordinate import RelativeCoordinate
                    window_size = get_window_size(hwnd)
                    if window_size:
                        region_ratio = RelativeCoordinate.pixel_to_ratio(self.region, window_size)
                except Exception:
                    pass

        cfg = {
            "enabled": ConfigVar(self.toggle.isChecked()),
            "type": self.monitor_type,
            "region": self.region,
            "region_ratio": region_ratio,
            "key": ConfigVar(self.key_input.key()),
            "alarm": ConfigVar(self.alarm_toggle.isChecked()),
            "click_enabled": ConfigVar(self.click_toggle.isChecked()),
            "click_offset": ConfigVar(str(self.offset_spin.value())),
            "delay_min": ConfigVar("100"),
            "delay_max": ConfigVar("200"),
            "interval": ConfigVar(str(self.interval_spin.value())),
            "pause": ConfigVar(str(self.pause_spin.value())),
        }
        if self.monitor_type == "ocr":
            cfg["keywords"] = ConfigVar(self.keywords_input.text())
            cfg["language"] = ConfigVar(self.lang_combo.currentText())
        elif self.monitor_type == "image":
            cfg["threshold"] = ConfigVar(str(self.threshold_spin.value()))
            cfg["reference_image"] = getattr(self, 'template_pixmap', None)
            cfg["template_image"] = getattr(self, 'template_pixmap', None)
        elif self.monitor_type == "color":
            hex_text = self.color_hex.text().strip()
            if hex_text.startswith("#") and len(hex_text) == 7:
                try:
                    r = int(hex_text[1:3], 16)
                    g = int(hex_text[3:5], 16)
                    b = int(hex_text[5:7], 16)
                    cfg["target_color"] = (r, g, b)
                except ValueError:
                    cfg["target_color"] = None
            else:
                cfg["target_color"] = None
            cfg["tolerance"] = ConfigVar(str(self.tolerance_spin.value()))
        return cfg

    def _select_region(self):
        from ui.components.region_overlay import RegionOverlay
        self.overlay = RegionOverlay("bg")
        self.overlay.region_selected.connect(self._on_region_selected)
        self.overlay.show()

    def _on_region_selected(self, x1, y1, x2, y2):
        hwnd = self.app.background_manager.target_hwnd if hasattr(self.app, 'background_manager') else None
        if hwnd:
            try:
                import win32gui
                win_rect = win32gui.GetWindowRect(hwnd)
                win_left, win_top = win_rect[0], win_rect[1]
                x1 -= win_left
                y1 -= win_top
                x2 -= win_left
                y2 -= win_top
            except Exception:
                pass
        self.region = (x1, y1, x2, y2)
        self.region_label.setText(f"({x1}, {y1}) → ({x2}, {y2})")
        self.region_label.setStyleSheet("color: #8AB4F8; font-weight: 500;")

    def _on_template_picked(self, pixmap):
        if pixmap and not pixmap.isNull():
            self.template_pixmap = pixmap

    def _pick_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.color_hex.setText(color.name())
