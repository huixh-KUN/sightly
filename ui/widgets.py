from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QSpinBox, QComboBox,
    QLineEdit, QWidget, QScrollArea, QGridLayout, QDialog,
)
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
        self.setStyleSheet(f"#statusDot {{ background-color: {color}; }}")


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
    test_requested = Signal(int)
    preview_requested = Signal(str)

    def __init__(self, index, group_type="image", parent=None):
        super().__init__(parent)
        self.setObjectName("groupListItem")
        self._index = index
        self._group_type = group_type
        self._data = {}
        self._template_path = ""

        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._status_strip = QFrame()
        self._status_strip.setObjectName("groupStatusStrip")
        self._status_strip.setFixedWidth(2)
        outer.addWidget(self._status_strip)

        body = QHBoxLayout()
        body.setContentsMargins(14, 12, 14, 12)
        body.setSpacing(12)

        self._icon_badge = QFrame()
        self._icon_badge.setObjectName("groupIconBadge")
        badge_layout = QHBoxLayout(self._icon_badge)
        badge_layout.setContentsMargins(0, 0, 0, 0)
        self.icon_label = QLabel(_GROUP_ICONS.get(group_type, "📋"))
        self.icon_label.setObjectName("groupIcon")
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        badge_layout.addWidget(self.icon_label)
        body.addWidget(self._icon_badge, 0, Qt.AlignmentFlag.AlignTop)

        content = QVBoxLayout()
        content.setSpacing(4)

        self.name_label = QLabel("组")
        self.name_label.setObjectName("groupName")
        content.addWidget(self.name_label)

        meta = QHBoxLayout()
        meta.setSpacing(0)

        self.params_label = QLabel("")
        self.params_label.setObjectName("groupParams")
        meta.addWidget(self.params_label)

        self._dot_region = QLabel("·")
        self._dot_region.setObjectName("groupMetaDot")
        meta.addWidget(self._dot_region)

        self.region_label = ClickableLabel("")
        self.region_label.setObjectName("groupRegion")
        self.region_label.clicked.connect(self._preview_region)
        meta.addWidget(self.region_label)

        self._dot_template = QLabel("·")
        self._dot_template.setObjectName("groupMetaDot")
        meta.addWidget(self._dot_template)

        self.template_label = ClickableLabel("")
        self.template_label.setObjectName("groupTemplate")
        self.template_label.clicked.connect(self._preview_template)
        meta.addWidget(self.template_label)

        self._dot_detail = QLabel("·")
        self._dot_detail.setObjectName("groupMetaDot")
        meta.addWidget(self._dot_detail)

        self.detail_label = QLabel("")
        self.detail_label.setObjectName("groupDetail")
        meta.addWidget(self.detail_label, 1)
        content.addLayout(meta)

        body.addLayout(content, 1)

        from ui.components.group_action_bar import GroupActionBar
        self.actions = GroupActionBar()
        self.actions.test_clicked.connect(lambda: self.test_requested.emit(self._index))
        self.actions.edit_clicked.connect(lambda: self.double_clicked.emit(self._index))
        self.actions.delete_clicked.connect(self._confirm_delete)
        self.actions.toggled.connect(self._on_toggle)
        body.addWidget(self.actions, 0, Qt.AlignmentFlag.AlignVCenter)

        outer.addLayout(body, 1)
        self.toggle = self.actions
        self._update_active_style(True)

    def _update_active_style(self, enabled):
        from ui.theme import ThemeManager
        c = ThemeManager.current()
        color = c.PRIMARY if enabled else c.BORDER
        self._status_strip.setStyleSheet(
            f"#groupStatusStrip {{ background-color: {color}; border: none; "
            f"border-top-left-radius: 11px; border-bottom-left-radius: 11px; }}"
        )
        self.setProperty("groupActive", "true" if enabled else "false")
        self.style().unpolish(self)
        self.style().polish(self)

    def _set_meta_field(self, label, _dot_before, text):
        label.setText(text)
        label.setVisible(bool(text))

    def _sync_meta_dots(self):
        ordered = [
            (self.params_label, None),
            (self.region_label, self._dot_region),
            (self.template_label, self._dot_template),
            (self.detail_label, self._dot_detail),
        ]
        prev_visible = False
        for label, dot in ordered:
            if not label.isVisible():
                if dot is not None:
                    dot.setVisible(False)
                continue
            if dot is not None:
                dot.setVisible(prev_visible)
            prev_visible = True

    def set_index(self, index):
        self._index = index

    def index(self):
        return self._index

    def _on_toggle(self, state):
        self._update_active_style(state)
        self.toggled.emit(self._index, state)

    def _confirm_delete(self):
        from ui.components import ConfirmDialog
        dlg = ConfirmDialog(
            title="删除确认",
            message=f"确定要删除「{self._data.get('name', f'组 {self._index+1}')}」吗？此操作不可恢复。",
            confirm_text="删除",
            cancel_text="取消",
            parent=self
        )
        if dlg.exec():
            self.delete_clicked.emit(self._index)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.double_clicked.emit(self._index)
        super().mouseDoubleClickEvent(event)

    def set_data(self, data: dict):
        self._data = data
        name = data.get("name", f"组 {self._index + 1}")
        self.name_label.setText(name)

        params, region, template, details = self._format_display(data)
        self._set_meta_field(self.params_label, None, params)
        self._set_meta_field(self.region_label, self._dot_region, region)
        self._set_meta_field(self.template_label, self._dot_template, template)
        self._set_meta_field(self.detail_label, self._dot_detail, details)
        self._sync_meta_dots()

        enabled = data.get("enabled", True)
        switch = self.actions.switch
        switch.blockSignals(True)
        self.actions.setChecked(enabled)
        switch.blockSignals(False)
        self._update_active_style(enabled)

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
                template = fname
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


class GroupEditWindow(QDialog):

    def __init__(self, group_data: dict, group_index: int, group_type: str, panel=None, parent=None,
                 logging_manager=None, target_hwnd=0, app_state=None):
        super().__init__(parent)
        self.setObjectName("groupEditWindow")
        self.setWindowTitle(f"编辑 - {group_data.get('name', f'组 {group_index+1}')}")
        self.setMinimumSize(580, 480)
        self.resize(640, 640)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowModality(Qt.ApplicationModal)
        self.setModal(True)
        self._group_index = group_index
        self._panel = panel
        self._capture_suspended = False
        self._saved_modality = Qt.ApplicationModal
        self._owner_was_visible = False

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        if group_type == "image":
            from ui.image_panel import ImageGroupWidget
            self._editor = ImageGroupWidget(group_index, parent=self, app_state=app_state)
        elif group_type == "ocr":
            from ui.ocr_panel import OCRGroupWidget
            self._editor = OCRGroupWidget(group_index, parent=self)
        elif group_type == "timed":
            from ui.timed_panel import TimedGroupWidget
            self._editor = TimedGroupWidget(group_index, parent=self)
        elif group_type == "number":
            from ui.number_panel import NumberGroupWidget
            self._editor = NumberGroupWidget(group_index, parent=self)
        elif group_type in ("background", "ocr_bg", "image_bg", "color_bg"):
            from ui.background_panel import BackgroundGroupWidget
            mt = group_type.replace("_bg", "")
            self._editor = BackgroundGroupWidget(logging_manager, target_hwnd, group_index, mt, parent=self)
        else:
            raise ValueError(f"Unknown group type: {group_type}")

        self._editor.set_config(group_data)
        self._editor.setObjectName("groupEditBody")

        scroll = QScrollArea()
        scroll.setObjectName("groupEditScroll")
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setWidget(self._editor)
        layout.addWidget(scroll, 1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_row.addStretch()

        self._save_btn = QPushButton("保存")
        self._save_btn.setObjectName("primary")
        self._save_btn.clicked.connect(self._on_save)
        btn_row.addWidget(self._save_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.close)
        btn_row.addWidget(cancel_btn)

        layout.addLayout(btn_row)

        self._is_running = False

    def set_running(self, running):
        self._is_running = running
        from ui.widgets import set_panel_view_only
        set_panel_view_only(self._editor, running)

    def suspend_for_capture(self):
        """全屏选区/截图时暂时解除模态并隐藏窗口。"""
        if self._capture_suspended:
            return
        self._capture_suspended = True
        self._saved_modality = self.windowModality()
        self.setWindowModality(Qt.NonModal)
        self.hide()
        owner = self.parentWidget()
        self._owner_was_visible = owner.isVisible() if owner else False
        if owner:
            owner.hide()

    def resume_after_capture(self):
        """全屏操作结束后恢复模态编辑框。"""
        if not self._capture_suspended:
            return
        self._capture_suspended = False
        owner = self.parentWidget()
        if owner and self._owner_was_visible:
            owner.show()
        self.setWindowModality(self._saved_modality)
        self.show()
        self.raise_()
        self.activateWindow()

    def _on_save(self):
        cfg = self._editor.collect_config()
        if self._panel:
            if 0 <= self._group_index < len(self._panel.groups_data):
                plain = dict(cfg)
                plain["enabled"] = self._panel.groups_data[self._group_index].get("enabled", True)
                self._panel.groups_data[self._group_index] = plain
                if self._group_index < len(self._panel.list_items):
                    self._panel.list_items[self._group_index].set_data(plain)
            self._panel._edit_window = None
            if hasattr(self._panel, 'app') and hasattr(self._panel.app, 'save_config'):
                self._panel.app.save_config()
        self.close()

    def closeEvent(self, event):
        if self._panel:
            self._panel._edit_window = None
        super().closeEvent(event)


def suspend_group_edit_capture(host_widget):
    w = host_widget.window()
    if isinstance(w, GroupEditWindow):
        w.suspend_for_capture()


def resume_group_edit_capture(host_widget):
    w = host_widget.window()
    if isinstance(w, GroupEditWindow):
        w.resume_after_capture()


def hide_for_capture(host_widget):
    """隐藏 GroupEditWindow 供全屏选区使用，不改 modality（避免 Windows 句柄重建）。"""
    w = host_widget.window()
    if isinstance(w, GroupEditWindow):
        if w.isVisible():
            w.hide()
            return True
    return False


def show_after_capture(host_widget):
    """恢复被 hide_for_capture 隐藏的 GroupEditWindow。"""
    w = host_widget.window()
    if isinstance(w, GroupEditWindow):
        w.show()
        w.raise_()
        w.activateWindow()


def set_panel_view_only(panel, view_only):
    """将面板设为只读（保留滚动查看，禁用编辑控件）"""
    from ui.components.combo_box import ComboBox
    for t in (QSpinBox, QComboBox, QLineEdit, ComboBox):
        for child in panel.findChildren(t):
            child.setEnabled(not view_only)
    for child in panel.findChildren(QPushButton):
        name = child.objectName()
        if name in ("regionAction", "templateAction", "dangerAction", "testBtn"):
            child.setEnabled(True)
        else:
            child.setEnabled(not view_only)
    for child in panel.findChildren(QWidget):
        name = child.objectName()
        if name in ("testBtn", "dangerAction"):
            child.setEnabled(True)
    from ui.components import KeyCaptureWidget
    for child in panel.findChildren(KeyCaptureWidget):
        child.setEnabled(not view_only)
    for child in panel.findChildren(GroupEditWindow):
        child.set_running(view_only)
