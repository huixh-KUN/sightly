from PySide6.QtWidgets import QWidget, QVBoxLayout, QPlainTextEdit, QPushButton, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer


class LogViewer(QWidget):
    """Reusable log display widget with monospace formatting.

    Can be embedded into any panel. Thread-safe append via log() method.
    """

    MAX_LINES = 500

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.text_edit = QPlainTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setMaximumBlockCount(self.MAX_LINES)
        self.text_edit.setStyleSheet("""
            QPlainTextEdit {
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                background-color: #1A1A1A;
                border: none;
                border-radius: 6px;
                padding: 8px;
                color: #E8EAED;
                selection-background-color: #8AB4F8;
                selection-color: #202124;
            }
        """)
        layout.addWidget(self.text_edit, 1)

    def log(self, message):
        QTimer.singleShot(0, lambda: self._do_log(message))

    def _do_log(self, message):
        self.text_edit.appendPlainText(message)

    def log_error(self, message):
        QTimer.singleShot(0, lambda: self._do_log_error(message))

    def _do_log_error(self, message):
        self.text_edit.appendHtml(f'<span style="color: #FF5252;">{message}</span>')

    def append_batch(self, lines):
        QTimer.singleShot(0, lambda: self._do_append_batch(lines))

    def _do_append_batch(self, lines):
        for line in lines:
            self.text_edit.appendPlainText(line)

    def clear(self):
        QTimer.singleShot(0, self.text_edit.clear)

    def set_max_lines(self, count):
        self.text_edit.setMaximumBlockCount(count)
