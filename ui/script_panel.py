from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QPlainTextEdit,
    QTabWidget, QFileDialog, QMessageBox, QSplitter
)
from PySide6.QtCore import Qt

from ui.widgets import SectionTitle
from ui.components import KeyCommandCard, DelayCommandCard, MouseCommandCard


class ScriptPanel(QWidget):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(20)

        header = QVBoxLayout()
        header.setSpacing(4)
        header.addWidget(SectionTitle("脚本运行"))
        subtitle = QLabel("编辑、录制和运行自动化按键脚本")
        subtitle.setObjectName("subtitle")
        header.addWidget(subtitle)
        layout.addLayout(header)

        splitter = QSplitter(Qt.Horizontal)

        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 12, 0)
        left_layout.setSpacing(10)

        self._key_card = KeyCommandCard()
        self._key_card.command_inserted.connect(self._insert_text)
        left_layout.addWidget(self._key_card)

        self._delay_card = DelayCommandCard()
        self._delay_card.command_inserted.connect(self._insert_text)
        left_layout.addWidget(self._delay_card)

        self._mouse_card = MouseCommandCard()
        self._mouse_card.command_inserted.connect(self._insert_text)
        left_layout.addWidget(self._mouse_card)

        control_card = QFrame()
        control_card.setObjectName("card")
        c_layout = QVBoxLayout(control_card)
        c_layout.setContentsMargins(20, 12, 20, 12)
        c_layout.setSpacing(8)
        c_layout.addWidget(QLabel("脚本控制"))
        c_row = QHBoxLayout()
        clear_btn = QPushButton("清空")
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.clicked.connect(lambda: self._current_editor().clear())
        c_row.addWidget(clear_btn)
        import_btn = QPushButton("导入")
        import_btn.setCursor(Qt.PointingHandCursor)
        import_btn.clicked.connect(self._import_script)
        c_row.addWidget(import_btn)
        export_btn = QPushButton("导出")
        export_btn.setObjectName("primary")
        export_btn.setCursor(Qt.PointingHandCursor)
        export_btn.clicked.connect(self._export_script)
        c_row.addWidget(export_btn)
        c_row.addStretch()
        c_layout.addLayout(c_row)

        rec_row = QHBoxLayout()
        rec_row.setSpacing(12)
        self._record_btn = QPushButton("●  开始录制")
        self._record_btn.setStyleSheet("font-weight: bold;")
        self._record_btn.setCursor(Qt.PointingHandCursor)
        self._record_btn.clicked.connect(self._start_recording)
        rec_row.addWidget(self._record_btn)
        self._stop_record_btn = QPushButton("■  停止录制")
        self._stop_record_btn.setCursor(Qt.PointingHandCursor)
        self._stop_record_btn.clicked.connect(self._stop_recording)
        self._stop_record_btn.setEnabled(False)
        rec_row.addWidget(self._stop_record_btn)
        rec_row.addStretch()
        c_layout.addLayout(rec_row)

        left_layout.addWidget(control_card)
        left_layout.addStretch()

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(12, 0, 0, 0)
        right_layout.setSpacing(0)

        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)

        editor_tab = QWidget()
        editor_layout = QVBoxLayout(editor_tab)
        editor_layout.setContentsMargins(0, 8, 0, 0)
        self._script_editor = QPlainTextEdit()
        self._script_editor.setPlaceholderText("在此编辑脚本...")
        self._script_editor.setStyleSheet("font-family: 'Consolas', 'Courier New', monospace; font-size: 12px;")
        editor_layout.addWidget(self._script_editor)

        color_tab = QWidget()
        color_layout = QVBoxLayout(color_tab)
        color_layout.setContentsMargins(16, 16, 16, 16)
        color_layout.setSpacing(12)
        color_layout.addWidget(QLabel("颜色识别命令区域"))
        info = QLabel("在此输入颜色识别相关的触发命令")
        info.setStyleSheet("font-size: 13px;")
        color_layout.addWidget(info)
        self._color_editor = QPlainTextEdit()
        self._color_editor.setPlaceholderText("颜色识别命令...")
        self._color_editor.setStyleSheet("font-family: 'Consolas', 'Courier New', monospace; font-size: 12px;")
        color_layout.addWidget(self._color_editor)

        self._tabs.addTab(editor_tab, "脚本编辑")
        self._tabs.addTab(color_tab, "颜色识别")
        right_layout.addWidget(self._tabs)

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([350, 500])
        splitter.setHandleWidth(1)

        layout.addWidget(splitter, 1)

    def _insert_text(self, text):
        self._current_editor().insertPlainText(text)

    def _current_editor(self):
        return self._script_editor if self._tabs.currentIndex() == 0 else self._color_editor

    def _import_script(self):
        path, _ = QFileDialog.getOpenFileName(self, "导入脚本", "", "Text Files (*.txt);;All Files (*)")
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    self._current_editor().setPlainText(f.read())
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导入失败: {e}")

    def _export_script(self):
        path, _ = QFileDialog.getSaveFileName(self, "导出脚本", "", "Text Files (*.txt);;All Files (*)")
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(self._current_editor().toPlainText())
            except Exception as e:
                QMessageBox.critical(self, "错误", f"导出失败: {e}")

    def _start_recording(self):
        self.app.script_module.start_recording()
        self._record_btn.setEnabled(False)
        self._stop_record_btn.setEnabled(True)

    def _stop_recording(self):
        self.app.script_module.stop_recording()
        self._record_btn.setEnabled(True)
        self._stop_record_btn.setEnabled(False)

    def collect_config(self):
        return {
            "script_content": self._script_editor.toPlainText(),
            "color_commands": self._color_editor.toPlainText(),
        }

    def set_config(self, cfg):
        if "script_content" in cfg:
            self._script_editor.setPlainText(cfg["script_content"])
        if "color_commands" in cfg:
            self._color_editor.setPlainText(cfg["color_commands"])

    def get_script_content(self):
        return self._script_editor.toPlainText()

    def get_color_commands(self):
        return self._color_editor.toPlainText()
