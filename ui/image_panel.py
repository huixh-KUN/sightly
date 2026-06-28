from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QLineEdit,
    QSpinBox, QGridLayout, QFileDialog
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
import os


class ImagePanel(QWidget):
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
        title_col.addWidget(SectionTitle("图像检测"))
        subtitle = QLabel("检测屏幕中指定图像的匹配，满足阈值时触发按键")
        subtitle.setObjectName("subtitle")
        title_col.addWidget(subtitle)
        header.addLayout(title_col)
        header.addStretch()

        add_btn = PrimaryButton("＋ 新增检测组")
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
            "name": f"检测组 {idx + 1}",
            "enabled": True,
            "region": None,
            "reference_image": "",
            "threshold": "80",
            "interval": "5",
            "pause": "180",
            "key": "",
            "delay_min": "300",
            "delay_max": "500",
            "alarm": False,
            "click": False,
            "click_offset": "0",
        }

    def _add_list_item(self, idx, data):
        item = GroupListItem(idx, "image", parent=self)
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
                self.groups_data[idx], idx, "image", panel=self,
                app_state=self.app.app_state,
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


class ImageGroupWidget(QFrame):

    def __init__(self, index, parent=None, app_state=None):
        super().__init__(parent)
        self._app_state = app_state
        self.index = index
        self.region = None
        self.template_path = None
        self._enabled = True

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 16)
        layout.setSpacing(14)

        self.header = GroupEditHeader(f"检测组 {index + 1}")
        self.header.title_edit.setText(f"检测组 {index + 1}")
        layout.addWidget(self.header)

        # 📍 区域
        region_card = ConfigCard("📍", "区域")
        self.region_chip = ValueChip("未选择")
        region_btn = TextButton("选择区域")
        region_btn.setObjectName("regionAction")
        region_btn.clicked.connect(self._select_region)
        region_card.add_action_row("", self.region_chip, region_btn)
        layout.addWidget(region_card)

        # 🖼️ 模板
        template_card = ConfigCard("🖼️", "模板")
        self.template_chip = ValueChip("未选择")
        template_btn = TextButton("选择图片")
        template_btn.setObjectName("templateAction")
        template_btn.clicked.connect(self._select_template)
        screenshot_btn = TextButton("截图")
        screenshot_btn.setObjectName("templateAction")
        screenshot_btn.clicked.connect(self._capture_template)
        template_card.add_action_row("", self.template_chip, template_btn, screenshot_btn)
        layout.addWidget(template_card)

        # 🎯 检测
        detect_card = ConfigCard("🎯", "检测")
        self.threshold_spin = QSpinBox()
        self.threshold_spin.setRange(50, 100)
        self.threshold_spin.setValue(80)
        self.threshold_spin.setSuffix("%")
        self.threshold_spin.setFixedWidth(58)
        detect_card.add_row("阈值", self.threshold_spin)
        self.cycle_widget = CycleControlWidget()
        detect_card.add_row("", self.cycle_widget, stretch=1)
        layout.addWidget(detect_card)

        # ⚙️ 触发
        trigger_card = ConfigCard("⚙️", "触发")
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
            "按键",
            ("", self.key_input),
            ("时长", spin_range_row(self.delay_min_spin, self.delay_max_spin)),
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
        self._connect_preview()

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
        ref = cfg.get("reference_image", "")
        if ref and os.path.exists(ref):
            self.template_path = ref
            self.template_chip.set_text(ref.split("/")[-1].split("\\")[-1], accent=True)
        try:
            self.threshold_spin.setValue(int(cfg.get("threshold", 80)))
            self.cycle_widget.set_interval_value(float(cfg.get("interval", 3)))
            cycle = cfg.get("cycle_enabled", True)
            if isinstance(cycle, str):
                cycle = cycle.lower() in ("true", "1")
            self.cycle_widget.set_cycle_enabled(bool(cycle))
            self.delay_min_spin.setValue(int(cfg.get("delay_min", 300)))
            self.delay_max_spin.setValue(int(cfg.get("delay_max", 500)))
            self.offset_spin.setValue(int(cfg.get("click_offset", 0)))
        except (ValueError, TypeError):
            pass
        key = cfg.get("key", "")
        self.key_input.setKey(key)
        self.click_toggle.setChecked(cfg.get("click", False))
        self.alarm_toggle.setChecked(cfg.get("alarm", False))

    def set_title(self, index):
        self.index = index
        self.header.title_edit.setText(f"检测组 {index + 1}")

    def collect_config(self):
        return {
            "name": self.header.title_edit.text(),
            "enabled": self._enabled,
            "region": self.region,
            "reference_image": self.template_path or "",
            "threshold": str(self.threshold_spin.value()),
            "interval": str(self.cycle_widget.interval_value()),
            "cycle_enabled": self.cycle_widget.is_cycle_enabled(),
            "key": self.key_input.key(),
            "delay_min": str(self.delay_min_spin.value()),
            "delay_max": str(self.delay_max_spin.value()),
            "alarm": self.alarm_toggle.isChecked(),
            "click": self.click_toggle.isChecked(),
            "click_offset": str(self.offset_spin.value()),
        }

    def _hide_windows(self):
        from ui.widgets import hide_for_capture
        hide_for_capture(self)

    def _show_windows(self):
        from ui.widgets import show_after_capture
        show_after_capture(self)

    def _select_region(self):
        from ui.components.region_overlay import RegionOverlay
        self.overlay = RegionOverlay("image")
        self.overlay.region_selected.connect(self._on_region_selected)
        self.overlay.closed.connect(self._show_windows)
        self._hide_windows()
        self.overlay.show()

    def _on_region_selected(self, x1, y1, x2, y2):
        self.region = (x1, y1, x2, y2)
        self.region_chip.set_text(f"({x1}, {y1}) → ({x2}, {y2})", accent=True)
        self._show_windows()

    def _select_template(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择模板图片", "", "Image Files (*.png *.jpg *.bmp)")
        if path:
            self.template_chip.set_text(path.split("/")[-1].split("\\")[-1], accent=True)
            ws_path = self._save_template_to_workspace(path)
            self.template_path = ws_path or path

    def _capture_template(self):
        from ui.components.screenshot import ScreenCaptureOverlay
        self._capture_overlay = ScreenCaptureOverlay()
        self._capture_overlay.region_captured.connect(self._on_template_captured)
        self._capture_overlay.closed.connect(self._show_windows)
        self._hide_windows()
        self._capture_overlay.show()

    def _on_template_captured(self, pixmap):
        ws_path = self._save_template_to_workspace(pixmap)
        if ws_path:
            self.template_chip.set_text(f"截图 ({pixmap.width()}x{pixmap.height()})", accent=True)
            self.template_path = ws_path
        self._show_windows()

    def _save_template_to_workspace(self, pixmap_or_path):
        if self._app_state and self._app_state.current is not None:
            return self._app_state.save_template("image", self.index, pixmap_or_path)
        return None

    def _preview_template(self):
        if self.template_path and os.path.exists(self.template_path):
            os.startfile(self.template_path)
        else:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(None, "提示", "未设置模板图片")

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

    def _connect_preview(self):
        self.region_chip.label.clicked.connect(self._preview_region)
        self.template_chip.label.clicked.connect(self._preview_template)
