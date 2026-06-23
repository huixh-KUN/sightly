from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QFrame, QLineEdit,
    QSpinBox, QGridLayout, QFileDialog
)
from PySide6.QtCore import Qt, Signal

from ui.theme import Colors
from ui.widgets import (
    SectionTitle, GroupCard, PrimaryButton,
    DangerButton, InfoLabel, TextButton, ClickableLabel
)
from ui.components import Toggle
from ui.components import KeyCaptureWidget
from core.config import ConfigVar
import os


class ImagePanel(QWidget):
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
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_layout.setSpacing(12)
        self.scroll_layout.addStretch()
        self.scroll.setWidget(scroll_content)
        layout.addWidget(self.scroll, 1)

        self.add_group()

    def add_group(self):
        idx = len(self.groups)
        group = ImageGroupWidget(self.app, idx)
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

    def set_enabled(self, enabled):
        super().setEnabled(enabled)

    def collect_config(self):
        return [g.collect_config() for g in self.groups]

    def set_config(self, config_list):
        for g in self.groups[:]:
            self._delete_group(g)
        for cfg in config_list:
            self.add_group()
            self.groups[-1].set_config(cfg)

class ImageGroupWidget(GroupCard):
    delete_requested = Signal()

    def __init__(self, app, index, parent=None):
        super().__init__(parent)
        self.app = app
        self.index = index
        self.region = None
        self.template_path = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(20)

        header = QHBoxLayout()
        self.title_edit = QLineEdit(f"检测组 {index + 1}")
        self.title_edit.setObjectName("cardTitle")
        self.title_edit.setStyleSheet("font-size: 16px; font-weight: 600; background: transparent; border: none;")
        header.addWidget(self.title_edit)
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

        grid.addWidget(QLabel("检测区域"), 0, 0)
        self.region_label = ClickableLabel("未选择")
        self.region_label.setObjectName("infoText")
        grid.addWidget(self.region_label, 0, 1)
        region_btn = TextButton("选择区域")
        region_btn.clicked.connect(self._select_region)
        grid.addWidget(region_btn, 0, 2)

        grid.addWidget(QLabel("模板图像"), 1, 0)
        template_row = QHBoxLayout()
        template_row.setSpacing(8)
        self.template_label = ClickableLabel("未选择")
        self.template_label.setObjectName("infoText")
        template_row.addWidget(self.template_label, 1)
        template_btn = TextButton("选择图片")
        template_btn.clicked.connect(self._select_template)
        template_row.addWidget(template_btn)
        screenshot_btn = TextButton("截图")
        screenshot_btn.clicked.connect(self._capture_template)
        template_row.addWidget(screenshot_btn)
        grid.addLayout(template_row, 1, 1, 1, 2)

        row2 = QHBoxLayout()
        row2.setSpacing(16)
        row2.addWidget(QLabel("匹配阈值"))
        self.threshold_spin = QSpinBox()
        self.threshold_spin.setRange(50, 100)
        self.threshold_spin.setValue(80)
        self.threshold_spin.setSuffix("%")
        row2.addWidget(self.threshold_spin)
        row2.addWidget(QLabel("检测间隔"))
        self.interval_spin = QSpinBox()
        self.interval_spin.setRange(1, 99)
        self.interval_spin.setValue(5)
        self.interval_spin.setSuffix(" 秒")
        row2.addWidget(self.interval_spin)
        row2.addStretch()
        grid.addLayout(row2, 2, 0, 1, 3)

        grid.addWidget(QLabel("暂停时长"), 3, 0)
        self.pause_spin = QSpinBox()
        self.pause_spin.setRange(0, 999)
        self.pause_spin.setValue(180)
        self.pause_spin.setSuffix(" 秒")
        grid.addWidget(self.pause_spin, 3, 1)

        key_row = QHBoxLayout()
        key_row.setSpacing(12)
        key_row.addWidget(QLabel("触发按键"))
        self.key_input = KeyCaptureWidget()
        key_row.addWidget(self.key_input, 1)
        key_row.addWidget(QLabel("按键时长"))
        self.delay_min_spin = QSpinBox()
        self.delay_min_spin.setRange(0, 9999)
        self.delay_min_spin.setValue(300)
        self.delay_min_spin.setSuffix(" ms")
        self.delay_min_spin.setFixedWidth(80)
        key_row.addWidget(self.delay_min_spin)
        key_row.addWidget(QLabel("~"))
        self.delay_max_spin = QSpinBox()
        self.delay_max_spin.setRange(0, 9999)
        self.delay_max_spin.setValue(500)
        self.delay_max_spin.setSuffix(" ms")
        self.delay_max_spin.setFixedWidth(80)
        key_row.addWidget(self.delay_max_spin)
        grid.addLayout(key_row, 4, 0, 1, 3)

        toggles = QHBoxLayout()
        toggles.setSpacing(24)
        self.click_toggle = Toggle("匹配后点击")
        toggles.addWidget(self.click_toggle)
        toggles.addWidget(QLabel("偏移"))
        self.offset_spin = QSpinBox()
        self.offset_spin.setRange(0, 200)
        self.offset_spin.setValue(0)
        self.offset_spin.setSuffix("px")
        self.offset_spin.setFixedWidth(70)
        self.offset_spin.setToolTip("点击位置随机偏移范围（像素），0=关闭")
        toggles.addWidget(self.offset_spin)
        self.alarm_toggle = Toggle("警报提醒")
        toggles.addWidget(self.alarm_toggle)
        toggles.addStretch()
        grid.addLayout(toggles, 5, 0, 1, 3)

        layout.addLayout(grid)
        self._connect_preview()

    def _make_label_blue(self, label):
        label.setStyleSheet("color: #8AB4F8; font-weight: 500;")

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
        ref = cfg.get("reference_image", "")
        if ref and os.path.exists(ref):
            self.template_path = ref
            self.template_label.setText(ref.split("/")[-1].split("\\")[-1])
            self._make_label_blue(self.template_label)
        try:
            self.threshold_spin.setValue(int(cfg.get("threshold", 80)))
            self.interval_spin.setValue(int(cfg.get("interval", 5)))
            self.pause_spin.setValue(int(cfg.get("pause", 180)))
            self.delay_min_spin.setValue(int(cfg.get("delay_min", 300)))
            self.delay_max_spin.setValue(int(cfg.get("delay_max", 500)))
            self.offset_spin.setValue(int(cfg.get("click_offset", 0)))
        except (ValueError, TypeError):
            pass
        key = cfg.get("key", "")
        if key:
            self.key_input.set_key(key)
        self.click_toggle.setChecked(cfg.get("click", False))
        self.alarm_toggle.setChecked(cfg.get("alarm", False))

    def set_title(self, index):
        self.index = index
        self.title_edit.setText(f"检测组 {index + 1}")

    def collect_config(self):
        return {
            "name": self.title_edit.text(),
            "enabled": ConfigVar(self.toggle.isChecked()),
            "region": self.region,
            "reference_image": self.template_path or "",
            "threshold": ConfigVar(str(self.threshold_spin.value())),
            "interval": ConfigVar(str(self.interval_spin.value())),
            "pause": ConfigVar(str(self.pause_spin.value())),
            "key": ConfigVar(self.key_input.key()),
            "delay_min": ConfigVar(str(self.delay_min_spin.value())),
            "delay_max": ConfigVar(str(self.delay_max_spin.value())),
            "alarm": ConfigVar(self.alarm_toggle.isChecked()),
            "click": ConfigVar(self.click_toggle.isChecked()),
            "click_offset": ConfigVar(str(self.offset_spin.value())),
        }

    def _select_region(self):
        from ui.components.region_overlay import RegionOverlay
        self.overlay = RegionOverlay("image")
        self.overlay.region_selected.connect(self._on_region_selected)
        self.overlay.show()

    def _on_region_selected(self, x1, y1, x2, y2):
        self.region = (x1, y1, x2, y2)
        self.region_label.setText(f"({x1}, {y1}) → ({x2}, {y2})")
        self._make_label_blue(self.region_label)

    def _select_template(self):
        path, _ = QFileDialog.getOpenFileName(self, "选择模板图片", "", "Image Files (*.png *.jpg *.bmp)")
        if path:
            self.template_label.setText(path.split("/")[-1].split("\\")[-1])
            self._make_label_blue(self.template_label)
            ws_path = self._save_template_to_workspace(path)
            self.template_path = ws_path or path

    def _capture_template(self):
        from ui.components.screenshot import ScreenCaptureOverlay
        self._capture_overlay = ScreenCaptureOverlay()
        self._capture_overlay.region_captured.connect(self._on_template_captured)
        self._capture_overlay.show()

    def _on_template_captured(self, pixmap):
        ws_path = self._save_template_to_workspace(pixmap)
        if ws_path:
            self.template_label.setText(f"截图 ({pixmap.width()}x{pixmap.height()})")
            self._make_label_blue(self.template_label)
            self.template_path = ws_path

    def _save_template_to_workspace(self, pixmap_or_path):
        app_state = getattr(self.app, 'app_state', None)
        if app_state and app_state.current is not None:
            return app_state.save_template("image", self.index, pixmap_or_path)
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

    # 在 __init__ 中被调用，连接点击事件
    def _connect_preview(self):
        self.region_label.clicked.connect(self._preview_region)
        self.template_label.clicked.connect(self._preview_template)
