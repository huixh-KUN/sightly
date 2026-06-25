from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel,
    QPushButton, QListWidget, QListWidgetItem, QDialog
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap


class WindowSelector(QWidget):
    """窗口选择器组件

    点击「选择窗口」→ 弹出所有窗口列表 → 双击选中 → 截取快照预览。
    通过 window_selected(hwnd, title) 信号通知外部。
    """

    window_selected = Signal(int, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._hwnd = None
        self._title = ""
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        self._preview = QLabel()
        self._preview.setFixedSize(100, 70)
        self._preview.setAlignment(Qt.AlignCenter)
        self._preview.setText("预览")
        layout.addWidget(self._preview)

        icon = QLabel("🖥️")
        icon.setObjectName("windowIcon")
        layout.addWidget(icon)

        layout.addWidget(QLabel("目标窗口"))

        self._status = QLabel("未选择窗口")
        layout.addWidget(self._status, 1)

        select_btn = QPushButton("选择窗口")
        select_btn.setObjectName("primary")
        select_btn.setCursor(Qt.PointingHandCursor)
        select_btn.clicked.connect(self._open_window_list)
        layout.addWidget(select_btn)

    def hwnd(self):
        return self._hwnd

    def title(self):
        return self._title

    def set_window_by_hwnd(self, hwnd: int) -> None:
        """按句柄设置窗口（恢复用），不发射信号"""
        try:
            import win32gui
            title = win32gui.GetWindowText(hwnd)
        except Exception:
            title = ""
        self._hwnd = hwnd
        self._title = title
        self._status.setText(f"已选择: {title}")
        self._status.setStyleSheet("font-weight: 500;")
        self._capture_preview(hwnd)

    def _open_window_list(self):
        try:
            import win32gui
        except ImportError:
            return

        windows = []
        def enum_callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title:
                    windows.append((hwnd, title))
        win32gui.EnumWindows(enum_callback, None)

        dlg = QDialog(self)
        dlg.setWindowTitle("选择目标窗口")
        dlg.setFixedSize(500, 400)

        dlg_layout = QVBoxLayout(dlg)
        dlg_layout.setContentsMargins(16, 16, 16, 16)
        dlg_layout.setSpacing(12)

        hint = QLabel("双击窗口即可选中")
        hint.setStyleSheet("font-size: 12px;")
        dlg_layout.addWidget(hint)

        list_widget = QListWidget()
        for hwnd, title in windows:
            item = QListWidgetItem(f"[{hwnd}] {title}")
            item.setData(Qt.UserRole, (hwnd, title))
            list_widget.addItem(item)
        dlg_layout.addWidget(list_widget)

        list_widget.itemDoubleClicked.connect(lambda item: self._on_select(dlg, item))

        dlg.exec()

    def _on_select(self, dlg, item):
        hwnd, title = item.data(Qt.UserRole)
        self._hwnd = hwnd
        self._title = title
        self._status.setText(f"已选择: {title}")
        self._status.setStyleSheet("font-weight: 500;")
        self._capture_preview(hwnd)
        self.window_selected.emit(hwnd, title)
        dlg.accept()

    def _capture_preview(self, hwnd):
        try:
            from utils.window_capture import capture_window
            from PySide6.QtGui import QImage
            img = capture_window(hwnd)
            if img:
                data = img.tobytes("raw", "RGB")
                qimg = QImage(data, img.width, img.height, 3 * img.width, QImage.Format_RGB888)
                pixmap = QPixmap.fromImage(qimg)
                scaled = pixmap.scaled(
                    100, 70, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
                self._preview.setPixmap(scaled)
            else:
                self._preview.setText("截取失败")
        except Exception:
            self._preview.setText("截取失败")
