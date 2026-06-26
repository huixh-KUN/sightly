import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QLineEdit,
    QSpinBox, QGridLayout,
    QFileDialog, QColorDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap

from ui.widgets import (
    SectionTitle, PrimaryButton,
    TextButton, ClickableLabel,
    GroupListItem, GroupEditWindow,
)
from ui.components import ComboBox
from ui.components import Toggle
from ui.components import TemplatePicker, KeyCaptureWidget, WindowSelector, ConfigCard
from core.config import ConfigVar


class BackgroundPanel(QWidget):
    window_selected = Signal(int, str)
    auto_reconnect_requested = Signal(str, str, str)

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.groups_data = []
        self.list_items = []
        self._view_only = False
        self._edit_window = None
        self._target_hwnd = 0
        self._window_class = ""
        self._window_process = ""
        self._window_title = ""
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

        window_outer = QWidget()
        window_outer_layout = QHBoxLayout(window_outer)
        window_outer_layout.setContentsMargins(32, 0, 32, 0)

        window_card = QFrame()
        window_card.setObjectName("windowCard")
        w_layout = QHBoxLayout(window_card)
        w_layout.setContentsMargins(16, 12, 16, 12)
        w_layout.setSpacing(12)

        self._window_selector = WindowSelector()
        self._window_selector.window_selected.connect(self._on_window_selected)
        w_layout.addWidget(self._window_selector)

        window_outer_layout.addWidget(window_card)
        layout.addWidget(window_outer)

        layout.addSpacing(12)

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

    def add_group(self, monitor_type="ocr"):
        idx = len(self.groups_data)
        default = self._default_config(idx, monitor_type)
        self.groups_data.append(default)
        self._add_list_item(idx, default, monitor_type)

    def _default_config(self, idx, monitor_type):
        cfg = {
            "name": f"组 {idx + 1}",
            "enabled": True,
            "type": monitor_type,
            "region": None,
            "region_ratio": None,
            "key": "",
            "alarm": False,
            "click_enabled": False,
            "click_mode": "physical",
            "click_offset": "0",
            "delay_min": "100",
            "delay_max": "200",
            "interval": "3",
            "pause": "180",
        }
        if monitor_type == "ocr":
            cfg["keywords"] = ""
            cfg["language"] = "简体中文"
        elif monitor_type == "image":
            cfg["threshold"] = "80"
            cfg["reference_image"] = ""
        elif monitor_type == "color":
            cfg["target_color"] = None
            cfg["tolerance"] = "30"
        return cfg

    def _add_list_item(self, idx, data, monitor_type):
        item = GroupListItem(idx, monitor_type, parent=self)
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
            data = self.groups_data[idx]
            mt = data.get("type", "ocr")
            bg_type = f"{mt}_bg"
            self._edit_window = GroupEditWindow(
                data, idx, bg_type, panel=self,
                logging_manager=self.app.logging_manager,
                target_hwnd=self._target_hwnd,
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
        return {
            "window_class": self._window_class,
            "window_process": self._window_process,
            "window_title": self._window_title,
            "groups": [{k: ConfigVar(v) for k, v in g.items()} for g in self.groups_data],
        }

    def set_config(self, config):
        if hasattr(self.app, 'logging_manager'):
            self.app.logging_manager.debug("BG", f"set_config 收到: type={type(config).__name__}")

        if isinstance(config, list):
            groups = config
            first = groups[0] if groups else {}
            wc = first.get("window_class")
            wp = first.get("window_process")
            wt = first.get("window_title")
        else:
            wc = config.get("window_class")
            wp = config.get("window_process")
            wt = config.get("window_title")
            groups = config.get("groups", [])

        for item in self.list_items:
            self.scroll_layout.removeWidget(item)
            item.deleteLater()
        self.list_items.clear()
        self.groups_data.clear()

        if (wc or wt):
            self.auto_reconnect_requested.emit(wc, wp, wt)

        for cfg in groups:
            mon_type = cfg.get("type", "ocr")
            self.groups_data.append(dict(cfg))
            self._add_list_item(len(self.list_items), cfg, mon_type)

    def _on_window_selected(self, hwnd, title):
        self._target_hwnd = hwnd
        self._window_title = title
        try:
            import win32gui
            self._window_class = win32gui.GetClassName(hwnd)
            import win32process
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            import psutil
            self._window_process = psutil.Process(pid).name()
        except Exception:
            pass
        self.window_selected.emit(hwnd, title)
        if self._edit_window and hasattr(self._edit_window._editor, 'set_target_hwnd'):
            self._edit_window._editor.set_target_hwnd(hwnd)

    def on_auto_reconnect_result(self, ok, hwnd, title):
        if ok:
            self._target_hwnd = hwnd
            self._window_title = title
            try:
                import win32gui
                self._window_class = win32gui.GetClassName(hwnd)
                import win32process
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                import psutil
                self._window_process = psutil.Process(pid).name()
            except Exception:
                pass
            self._window_selector.set_window_by_hwnd(hwnd)


class BackgroundGroupWidget(QFrame):

    def __init__(self, logging_manager, target_hwnd, index, monitor_type="ocr", parent=None):
        super().__init__(parent)
        self._logging_manager = logging_manager
        self._target_hwnd = target_hwnd
        self.index = index
        self.monitor_type = monitor_type
        self.region = None
        self.region_ratio = None
        self.template_pixmap = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        type_names = {"ocr": "OCR", "image": "图像", "color": "颜色"}
        type_icons = {"ocr": "📝", "image": "🖼️", "color": "🎨"}
        icon = type_icons.get(monitor_type, "📋")
        type_label = type_names.get(monitor_type, monitor_type)

        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        self.title_edit = QLineEdit(f"{icon}  {type_label} 组 {index + 1}")
        self.title_edit.setStyleSheet("font-size: 16px; font-weight: 600;")
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
        region_card.add_widget_row(region_row)
        layout.addWidget(region_card)

        # 🎯 检测
        detect_card = ConfigCard("🎯", "检测")
        if monitor_type == "ocr":
            self.keywords_input = QLineEdit()
            self.keywords_input.setPlaceholderText("多个关键词用 | 分隔")
            detect_card.add_row("关键词", self.keywords_input)
            self.lang_combo = ComboBox(items=["简体中文", "繁体中文", "英文"])
            detect_card.add_row("语言", self.lang_combo)
        elif monitor_type == "image":
            self.template_picker = TemplatePicker()
            self.template_picker.template_selected.connect(self._on_template_picked)
            detect_card.add_widget_row(self.template_picker)
            self.threshold_spin = QSpinBox()
            self.threshold_spin.setRange(50, 100)
            self.threshold_spin.setValue(80)
            self.threshold_spin.setSuffix("%")
            detect_card.add_row("匹配阈值", self.threshold_spin)
        elif monitor_type == "color":
            color_row = QHBoxLayout()
            self.color_hex = QLineEdit()
            self.color_hex.setPlaceholderText("#RRGGBB")
            self.color_hex.setMaxLength(7)
            color_row.addWidget(self.color_hex)
            color_btn = TextButton("取色")
            color_btn.setObjectName("templateAction")
            color_btn.clicked.connect(self._pick_color)
            color_row.addWidget(color_btn)
            detect_card.add_widget_row(color_row)
            self.tolerance_spin = QSpinBox()
            self.tolerance_spin.setRange(0, 255)
            self.tolerance_spin.setValue(30)
            detect_card.add_row("容差", self.tolerance_spin)
        layout.addWidget(detect_card)

        # ⚙️ 触发
        trigger_card = ConfigCard("⚙️", "触发")
        self.key_input = KeyCaptureWidget()
        trigger_card.add_row("按键", self.key_input)
        click_row = QHBoxLayout()
        self.click_toggle = Toggle("点击")
        click_row.addWidget(self.click_toggle)
        self.click_mode_combo = ComboBox(items=["物理点击", "虚拟点击"], width=110)
        self.click_mode_combo.setEnabled(False)
        self.click_toggle.stateChanged.connect(self.click_mode_combo.setEnabled)
        click_row.addWidget(self.click_mode_combo)
        click_row.addWidget(QLabel("偏移"))
        self.offset_spin = QSpinBox()
        self.offset_spin.setRange(0, 200)
        self.offset_spin.setValue(0)
        self.offset_spin.setSuffix("px")
        self.offset_spin.setFixedWidth(70)
        click_row.addWidget(self.offset_spin)
        click_row.addStretch()
        trigger_card.add_widget_row(click_row)
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 99)
        self.interval_spin.setValue(3)
        self.interval_spin.setFixedWidth(70)
        trigger_card.add_row("间隔(秒)", self.interval_spin)
        self.pause_spin = QSpinBox()
        self.pause_spin.setRange(0, 9999)
        self.pause_spin.setValue(180)
        self.pause_spin.setFixedWidth(70)
        trigger_card.add_row("暂停(秒)", self.pause_spin)
        layout.addWidget(trigger_card)

        # 🔔 报警
        alarm_card = ConfigCard("🔔", "报警")
        self.alarm_toggle = Toggle("触发时报警")
        alarm_card.set_content(self.alarm_toggle)
        layout.addWidget(alarm_card)

        layout.addStretch()
        self._connect_preview()

    def _make_label_blue(self, label):
        label.setStyleSheet("font-weight: 500;")

    def _connect_preview(self):
        self.region_label.clicked.connect(self._preview_region)

    def _preview_region(self):
        if self.region:
            x1, y1, x2, y2 = self.region
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(None, "区域坐标",
                f"左上: ({x1}, {y1})\n右下: ({x2}, {y2})\n尺寸: {x2-x1} × {y2-y1}")
        else:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(None, "提示", "未设置监控区域")

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
            self._make_label_blue(self.region_label)
        try:
            self.interval_spin.setValue(int(cfg.get("interval", 3)))
            self.pause_spin.setValue(int(cfg.get("pause", 180)))
            self.offset_spin.setValue(int(cfg.get("click_offset", 0)))
        except (ValueError, TypeError):
            pass
        key = cfg.get("key", "")
        if key:
            self.key_input.setKey(key)
        self.click_toggle.setChecked(cfg.get("click_enabled", False))
        mode = cfg.get("click_mode", "physical")
        self.click_mode_combo.setCurrentIndex(0 if mode == "physical" else 1)
        self.alarm_toggle.setChecked(cfg.get("alarm", False))

        if self.monitor_type == "ocr":
            self.keywords_input.setText(cfg.get("keywords", ""))
            lang = cfg.get("language", "简体中文")
            idx = self.lang_combo.findText(lang)
            if idx >= 0:
                self.lang_combo.setCurrentIndex(idx)
        elif self.monitor_type == "image":
            try:
                self.threshold_spin.setValue(int(cfg.get("threshold", 80)))
            except (ValueError, TypeError):
                pass
            ref = cfg.get("reference_image", "")
            if ref and os.path.exists(ref):
                pixmap = QPixmap(ref)
                if not pixmap.isNull():
                    self.template_pixmap = pixmap
                    self.template_picker.set_pixmap(pixmap)
        elif self.monitor_type == "color":
            tc = cfg.get("target_color")
            if tc and len(tc) == 3:
                self.color_hex.setText(f"#{tc[0]:02x}{tc[1]:02x}{tc[2]:02x}")
            try:
                self.tolerance_spin.setValue(int(cfg.get("tolerance", 30)))
            except (ValueError, TypeError):
                pass

    def set_target_hwnd(self, hwnd):
        self._target_hwnd = hwnd

    def set_title(self, index):
        self.index = index
        type_names = {"ocr": "OCR", "image": "图像", "color": "颜色"}
        type_icons = {"ocr": "📝", "image": "🖼️", "color": "🎨"}
        icon = type_icons.get(self.monitor_type, "📋")
        self.title_edit.setText(f"{icon}  {type_names.get(self.monitor_type, self.monitor_type)} 组 {index + 1}")

    def collect_config(self):
        region_ratio = None
        if self.region and self._target_hwnd:
            try:
                from utils.window_capture import get_window_size
                from utils.coordinate import RelativeCoordinate
                window_size = get_window_size(self._target_hwnd)
                if window_size:
                    region_ratio = RelativeCoordinate.pixel_to_ratio(self.region, window_size)
            except Exception as e:
                self._logging_manager.error("BG", f"获取窗口大小失败: {e}")

        cfg = {
            "name": self.title_edit.text(),
            "enabled": ConfigVar(self.toggle.isChecked()),
            "type": self.monitor_type,
            "region": self.region,
            "region_ratio": region_ratio,
            "key": ConfigVar(self.key_input.key()),
            "alarm": ConfigVar(self.alarm_toggle.isChecked()),
            "click_enabled": ConfigVar(self.click_toggle.isChecked()),
            "click_mode": ConfigVar("physical" if self.click_mode_combo.currentIndex() == 0 else "virtual"),
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

    def _hide_windows(self):
        w = self.window()
        if w and isinstance(w, GroupEditWindow):
            w.hide()
            from PySide6.QtWidgets import QWidget as QW
            pw = w.parent()
            if isinstance(pw, QW):
                pw.hide()

    def _show_windows(self):
        w = self.window()
        if w and isinstance(w, GroupEditWindow):
            from PySide6.QtWidgets import QWidget as QW
            pw = w.parent()
            if isinstance(pw, QW):
                pw.show()
            w.show()

    def _select_region(self):
        from ui.components.region_overlay import RegionOverlay
        self._hide_windows()
        self.overlay = RegionOverlay("bg")
        self.overlay.region_selected.connect(self._on_region_selected)
        self.overlay.show()

    def _on_region_selected(self, x1, y1, x2, y2):
        if self._target_hwnd:
            try:
                import win32gui
                win_rect = win32gui.GetWindowRect(self._target_hwnd)
                win_left, win_top = win_rect[0], win_rect[1]
                x1 -= win_left
                y1 -= win_top
                x2 -= win_left
                y2 -= win_top
            except Exception as e:
                self._logging_manager.error("BG", f"坐标转换失败: {e}")
        self.region = (x1, y1, x2, y2)
        self.region_label.setText(f"({x1}, {y1}) → ({x2}, {y2})")
        self.region_label.setStyleSheet("font-weight: 500;")
        self._show_windows()

    def _on_template_picked(self, pixmap):
        if pixmap and not pixmap.isNull():
            self.template_pixmap = pixmap

    def _pick_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.color_hex.setText(color.name())
