from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QSpinBox, QComboBox, QLineEdit, QWidget, QScrollArea, QGridLayout
from PySide6.QtCore import Qt, Signal, QEvent

class Card(QFrame):
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        if title:
            header = QHBoxLayout()
            title_label = QLabel(title)
            title_label.setObjectName("cardTitle")
            header.addWidget(title_label)
            header.addStretch()
            layout.addLayout(header)
            self._content_layout = layout


class SectionTitle(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setObjectName("sectionTitle")


class GroupCard(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("groupCard")


class InfoLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setObjectName("infoText")


class AccentLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setObjectName("accentText")


class BaseButton(QPushButton):
    """按钮基类：统一最小高度，样式由 QSS 主题控制"""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(32)


class TextButton(BaseButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setObjectName("textBtn")


class PrimaryButton(BaseButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setObjectName("primary")


class DangerButton(BaseButton):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setObjectName("danger")


class SmallButton(BaseButton):
    """小型按钮，用于紧凑空间"""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setMinimumHeight(26)


class NavButton(QPushButton):
    def __init__(self, text="", icon_text="", parent=None):
        super().__init__(text, parent)
        self.setProperty("class", "navItem")
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(40)


class StatusIndicator(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("statusDot")
        self.setFixedSize(10, 10)
        self._running = False

    @property
    def running(self):
        return self._running

    @running.setter
    def running(self, value):
        self._running = value
        color = "#00e676" if value else "#555577"
        self.setStyleSheet(f"#statusDot {{ background-color: {color}; border-radius: 5px; min-width: 10px; max-width: 10px; min-height: 10px; max-height: 10px; }}")


class Divider(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("divider")
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)


class ClickableLabel(QLabel):
    clicked = Signal()

    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, event):
        self.clicked.emit()
        super().mousePressEvent(event)


_GROUP_ICONS = {
    "ocr": "📝", "image": "🖼️", "timed": "⏰", "number": "🔢",
    "color": "🎨", "background": "🖥️",
}


class GroupListItem(QFrame):
    double_clicked = Signal(int)
    toggled = Signal(int, bool)
    delete_clicked = Signal(int)
    preview_requested = Signal(str)

    def __init__(self, index, group_type="image", parent=None):
        super().__init__(parent)
        self.setObjectName("groupListItem")
        self._index = index
        self._group_type = group_type
        self._data = {}
        self._template_path = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 10, 16, 10)
        layout.setSpacing(4)

        row1 = QHBoxLayout()
        row1.setSpacing(10)

        self.icon_label = QLabel(_GROUP_ICONS.get(group_type, "📋"))
        self.icon_label.setObjectName("groupIcon")
        row1.addWidget(self.icon_label)

        self.name_label = QLabel("组")
        self.name_label.setObjectName("groupName")
        row1.addWidget(self.name_label)

        self.region_label = ClickableLabel("")
        self.region_label.setObjectName("groupRegion")
        self.region_label.clicked.connect(self._preview_region)
        row1.addWidget(self.region_label)

        self.template_label = ClickableLabel("")
        self.template_label.setObjectName("groupTemplate")
        self.template_label.clicked.connect(self._preview_template)
        row1.addWidget(self.template_label)

        row1.addStretch()

        from ui.components import Toggle
        self.toggle = Toggle("")
        self.toggle.setObjectName("groupToggle")
        self.toggle.stateChanged.connect(self._on_toggle)
        row1.addWidget(self.toggle)

        self._delete_btn = SmallButton("删除")
        self._delete_btn.setObjectName("dangerAction")
        self._delete_btn.clicked.connect(lambda: self.delete_clicked.emit(self._index))
        row1.addWidget(self._delete_btn)

        layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.setSpacing(16)

        self.params_label = QLabel("")
        self.params_label.setObjectName("groupParams")
        row2.addWidget(self.params_label)

        self.detail_label = QLabel("")
        self.detail_label.setObjectName("groupDetail")
        row2.addWidget(self.detail_label, 1)

        row2.addStretch()

        layout.addLayout(row2)

    def set_index(self, index):
        self._index = index

    def index(self):
        return self._index

    def _on_toggle(self, state):
        self.toggled.emit(self._index, state)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.double_clicked.emit(self._index)
        super().mouseDoubleClickEvent(event)

    def set_data(self, data: dict):
        self._data = data
        name = data.get("name", f"组 {self._index + 1}")
        self.name_label.setText(name)

        params, region, template, details = self._format_display(data)
        self.params_label.setText(params)
        self.region_label.setText(region)
        self.template_label.setText(template)
        self.detail_label.setText(details)

    def _preview_template(self):
        if self._template_path:
            import os
            os.startfile(self._template_path)

    def _preview_region(self):
        r = self._data.get("region")
        if r and len(r) == 4:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(
                None, "区域坐标",
                f"左上: ({r[0]}, {r[1]})\n右下: ({r[2]}, {r[3]})\n尺寸: {r[2]-r[0]} × {r[3]-r[1]}"
            )

    def _format_display(self, data: dict) -> tuple:
        t = self._group_type
        params = ""
        region = ""
        template = ""
        details = ""
        self._template_path = ""

        if t == "image":
            th = data.get("threshold", 80)
            params = f"阈值 {th}%"
            ref = data.get("reference_image", "")
            if ref:
                self._template_path = ref
                fname = ref.split("/")[-1].split("\\")[-1]
                template = f"📷 {fname}"
        elif t == "ocr":
            kw = data.get("keywords", "")
            if kw:
                params = f"关键词 {kw}"
            interval = data.get("interval", 3)
            if params:
                params += f"  ·  间隔 {interval}s"
            else:
                params = f"间隔 {interval}s"
        elif t == "timed":
            interval = data.get("interval", 10)
            params = f"间隔 {interval}s"
        elif t == "number":
            th = data.get("threshold", 500)
            params = f"阈值 {th}"
            conf = data.get("confidence_threshold", 0.3)
            params += f"  ·  置信度 {conf}"
        elif t == "color":
            tc = data.get("target_color")
            if tc:
                params = f"颜色 #{tc[0]:02x}{tc[1]:02x}{tc[2]:02x}"
            tol = data.get("tolerance", 30)
            params += f"  ·  容差 {tol}"
        elif t == "background":
            st = data.get("type", "ocr")
            params = f"类型 {st}"
            kw = data.get("keywords", "")
            if kw:
                params += f"  ·  {kw}"

        r = data.get("region")
        if r and len(r) == 4:
            region = f"区域 ({r[0]},{r[1]})→({r[2]},{r[3]})"

        parts = []
        key = data.get("key", "")
        if key:
            parts.append(f"按键 {key}")
        pause = data.get("pause", "")
        if pause:
            parts.append(f"暂停 {pause}s")
        if data.get("click"):
            parts.append("点击 ✓")
        if data.get("alarm"):
            parts.append("报警 ✓")
        details = "  ".join(parts)

        return params, region, template, details


class GroupEditWindow(QWidget):
    config_changed = Signal(int, dict)

    def __init__(self, app, group_data: dict, group_index: int, group_type: str, panel=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"编辑 - {group_data.get('name', f'组 {group_index+1}')}")
        self.setMinimumSize(520, 400)
        self.resize(520, 500)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self._app = app
        self._group_index = group_index
        self._panel = panel

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        if group_type == "image":
            from ui.image_panel import ImageGroupWidget
            self._editor = ImageGroupWidget(app, group_index, parent=self)
        elif group_type == "ocr":
            from ui.ocr_panel import OCRGroupWidget
            self._editor = OCRGroupWidget(app, group_index, parent=self)
        elif group_type == "timed":
            from ui.timed_panel import TimedGroupWidget
            self._editor = TimedGroupWidget(app, group_index, parent=self)
        elif group_type == "number":
            from ui.number_panel import NumberGroupWidget
            self._editor = NumberGroupWidget(app, group_index, parent=self)
        elif group_type in ("background", "ocr_bg", "image_bg", "color_bg"):
            from ui.background_panel import BackgroundGroupWidget
            mt = group_type.replace("_bg", "")
            self._editor = BackgroundGroupWidget(app, group_index, mt, parent=self)
        else:
            raise ValueError(f"Unknown group type: {group_type}")

        self._editor.set_config(group_data)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(self._editor)
        layout.addWidget(scroll)

        self._is_running = False

    def set_running(self, running):
        self._is_running = running
        from ui.widgets import set_panel_view_only
        set_panel_view_only(self._editor, running)

    def closeEvent(self, event):
        if self._panel and hasattr(self._panel, '_on_edit_window_closed'):
            self._panel._on_edit_window_closed(self._group_index, self._editor)
        super().closeEvent(event)


def set_panel_view_only(panel, view_only):
    """将面板设为只读（保留滚动查看，禁用编辑控件）"""
    if not view_only:
        return
    for t in (QSpinBox, QComboBox, QLineEdit):
        for child in panel.findChildren(t):
            child.setEnabled(False)
    for child in panel.findChildren(QPushButton):
        name = child.objectName()
        if name in ("regionAction", "templateAction", "dangerAction"):
            continue
        child.setEnabled(False)
    from ui.components import KeyCaptureWidget
    for child in panel.findChildren(KeyCaptureWidget):
        child.setEnabled(False)
    for child in panel.findChildren(GroupEditWindow):
        child.set_running(True)
