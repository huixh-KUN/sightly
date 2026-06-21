from PySide6.QtCore import QObject, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFileDialog


class TemplateManager(QObject):
    """Unified template image management.

    Supports two sources:
      1. Load from local file (load_from_file)
      2. Capture from screen region (capture_from_screen)

    Both paths produce a QPixmap. Callers get the template via current_template()
    and listen to template_changed signal. No need to know the source.
    """

    template_changed = Signal(object)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._pixmap = None
        self._source_path = None

    def current_template(self):
        return self._pixmap

    def source_path(self):
        return self._source_path

    def has_template(self):
        return self._pixmap is not None and not self._pixmap.isNull()

    def load_from_file(self, parent_widget=None):
        path, _ = QFileDialog.getOpenFileName(
            parent_widget, "选择模板图片", "",
            "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if not path:
            return False
        pixmap = QPixmap(path)
        if pixmap.isNull():
            return False
        self._pixmap = pixmap
        self._source_path = path
        self.template_changed.emit(pixmap)
        return True

    def load_from_pixmap(self, pixmap, source_name="截图"):
        if pixmap is None or pixmap.isNull():
            return False
        self._pixmap = pixmap
        self._source_path = source_name
        self.template_changed.emit(pixmap)
        return True

    def clear(self):
        self._pixmap = None
        self._source_path = None
        self.template_changed.emit(None)
