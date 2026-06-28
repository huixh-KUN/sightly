from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QFrame
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPixmap

from ui.components.template_manager import TemplateManager
from ui.components.screenshot import ScreenCaptureOverlay


class TemplatePicker(QFrame):
    """Combined template image selection widget.

    Provides two methods to pick a template image:
      1. Browse local files
      2. Capture screen region

    Displays a preview thumbnail. Emits template_selected(QPixmap) on change.
    Fully self-contained — embed into any panel that needs template selection.
    """

    template_selected = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self._manager = TemplateManager(self)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        self.setFixedHeight(120)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        preview_container = QFrame()
        preview_container.setObjectName("card")
        preview_container.setFixedSize(100, 100)
        p_layout = QVBoxLayout(preview_container)
        p_layout.setContentsMargins(2, 2, 2, 2)
        self._preview = QLabel("无模板")
        self._preview.setAlignment(Qt.AlignCenter)
        self._preview.setStyleSheet("font-size: 11px;")
        p_layout.addWidget(self._preview)
        layout.addWidget(preview_container)

        btn_panel = QVBoxLayout()
        btn_panel.setSpacing(8)

        self._file_btn = QPushButton("选择图片文件")
        self._file_btn.setCursor(Qt.PointingHandCursor)
        self._file_btn.setObjectName("primary")
        self._file_btn.setMinimumHeight(32)
        btn_panel.addWidget(self._file_btn)

        self._capture_btn = QPushButton("截图选区")
        self._capture_btn.setCursor(Qt.PointingHandCursor)
        self._capture_btn.setMinimumHeight(32)
        btn_panel.addWidget(self._capture_btn)

        self._clear_btn = QPushButton("清除模板")
        self._clear_btn.setCursor(Qt.PointingHandCursor)
        self._clear_btn.setObjectName("danger")
        self._clear_btn.setMinimumHeight(28)
        btn_panel.addWidget(self._clear_btn)

        btn_panel.addStretch()
        layout.addLayout(btn_panel, 1)

        self._info = QLabel("未选择模板")
        self._info.setStyleSheet("font-size: 12px;")
        layout.addWidget(self._info)

    def _connect_signals(self):
        self._file_btn.clicked.connect(self._on_file)
        self._capture_btn.clicked.connect(self._on_capture)
        self._clear_btn.clicked.connect(self._on_clear)
        self._manager.template_changed.connect(self._on_template_changed)

    def _on_file(self):
        if self._manager.load_from_file(self):
            self.template_selected.emit(self._manager.current_template())

    def _on_capture(self):
        self._overlay = ScreenCaptureOverlay()
        self._overlay.region_captured.connect(self._on_captured)
        self._overlay.closed.connect(self._show_after_capture)
        self._hide_for_capture()
        self._overlay.show()

    def _hide_for_capture(self):
        w = self.window()
        if w and isinstance(w, QWidget):
            w.hide()

    def _show_after_capture(self):
        w = self.window()
        if w and isinstance(w, QWidget):
            w.show()
            w.raise_()
            w.activateWindow()

    def _on_captured(self, pixmap):
        null = pixmap is None or pixmap.isNull()
        has_source = self._manager.has_template()
        print(f"[TEMPLATE_PICKER] _on_captured: pixmap_null={null}, manager_has_template={has_source}")
        if self._manager.load_from_pixmap(pixmap):
            self.template_selected.emit(self._manager.current_template())

    def _on_clear(self):
        self._manager.clear()
        self.template_selected.emit(None)

    def _on_template_changed(self, pixmap):
        if pixmap and not pixmap.isNull():
            thumb = pixmap.scaled(96, 96, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self._preview.setPixmap(thumb)
            name = getattr(self._manager, "_source_path", "截图")
            display = name.split("/")[-1].split("\\")[-1][:20]
            self._info.setText(f"当前: {display}")
            self._info.setStyleSheet("font-size: 12px;")
        else:
            self._preview.clear()
            self._preview.setText("无模板")
            self._info.setText("未选择模板")
            self._info.setStyleSheet("font-size: 12px;")

    def current_template(self):
        return self._manager.current_template()

    def has_template(self):
        return self._manager.has_template()

    def set_pixmap(self, pixmap):
        if pixmap and not pixmap.isNull():
            self._manager.load_from_pixmap(pixmap)
            self.template_selected.emit(pixmap)
