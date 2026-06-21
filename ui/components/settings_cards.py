import os
import sys

from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QGridLayout, QPushButton, QFileDialog, QDialog
)
from PySide6.QtCore import Qt, Signal
import webbrowser

from ui.components.key_capture import KeyCaptureWidget
from ui.components.combo_box import ComboBox


class GeneralSettingsCard(QFrame):
    """通用设置卡片"""

    config_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("settingsCard")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 20)
        layout.setSpacing(16)

        title = QLabel("通用设置")
        title.setObjectName("cardTitle")
        layout.addWidget(title)

        grid = QGridLayout()
        grid.setSpacing(12)
        grid.setColumnStretch(1, 1)

        grid.addWidget(QLabel("界面语言"), 0, 0)
        self._lang_combo = ComboBox(items=["简体中文", "繁体中文", "英文"])
        self._lang_combo.currentIndexChanged.connect(lambda idx: self.config_changed.emit())
        grid.addWidget(self._lang_combo, 0, 1)

        grid.addWidget(QLabel("启动快捷键"), 1, 0)
        self._start_key = KeyCaptureWidget()
        grid.addWidget(self._start_key, 1, 1)

        grid.addWidget(QLabel("停止快捷键"), 2, 0)
        self._stop_key = KeyCaptureWidget()
        grid.addWidget(self._stop_key, 2, 1)

        layout.addLayout(grid)

    def get_config(self):
        return {
            "language": self._lang_combo.currentText(),
            "start_key": self._start_key.key(),
            "stop_key": self._stop_key.key(),
        }

    def set_config(self, cfg):
        if "language" in cfg:
            idx = self._lang_combo.findText(cfg["language"])
            if idx >= 0:
                self._lang_combo.setCurrentIndex(idx)
        if "start_key" in cfg:
            self._start_key.setKey(cfg["start_key"])
        if "stop_key" in cfg:
            self._stop_key.setKey(cfg["stop_key"])


class AlarmSettingsCard(QFrame):
    """警报设置卡片"""

    config_changed = Signal()
    preview_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("settingsCard")
        self._default_path = self._resolve_default_sound()
        self._sound_file = self._default_path
        self._setup_ui()

    def _resolve_default_sound(self):
        if hasattr(sys, '_MEIPASS'):
            root = sys._MEIPASS
        else:
            root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        path = os.path.join(root, "voice", "alarm.mp3")
        return os.path.normpath(path)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 20)
        layout.setSpacing(16)

        title = QLabel("警报设置")
        title.setObjectName("cardTitle")
        layout.addWidget(title)

        row = QHBoxLayout()
        row.setSpacing(12)
        row.addWidget(QLabel("警报音效"))
        self._sound_path = QLabel(os.path.basename(self._sound_file))
        self._sound_path.setStyleSheet("color: #8AB4F8; font-weight: 500;")
        row.addWidget(self._sound_path, 1)
        browse_btn = QPushButton("浏览")
        browse_btn.setCursor(Qt.PointingHandCursor)
        browse_btn.clicked.connect(self._browse_sound)
        row.addWidget(browse_btn)
        preview_btn = QPushButton("试听")
        preview_btn.setCursor(Qt.PointingHandCursor)
        preview_btn.clicked.connect(self._preview_sound)
        row.addWidget(preview_btn)
        layout.addLayout(row)

    def _preview_sound(self):
        self.preview_requested.emit(self._sound_file)

    def _browse_sound(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "选择警报音效", "",
            "Audio Files (*.mp3 *.wav *.ogg)"
        )
        if path:
            self._sound_path.setText(path.split("/")[-1].split("\\")[-1])
            self._sound_path.setStyleSheet("color: #8AB4F8; font-weight: 500;")
            self._sound_file = path
            self.config_changed.emit()

    def get_config(self):
        return {"sound_path": getattr(self, '_sound_file', '')}

    def set_config(self, cfg):
        if "sound_path" in cfg and cfg["sound_path"]:
            self._sound_file = cfg["sound_path"]
            self._sound_path.setText(cfg["sound_path"].split("/")[-1].split("\\")[-1])
            self._sound_path.setStyleSheet("color: #8AB4F8; font-weight: 500;")


class AboutCard(QFrame):
    """关于卡片"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("settingsCard")
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 20)
        layout.setSpacing(16)

        title = QLabel("关于")
        title.setObjectName("cardTitle")
        layout.addWidget(title)

        row = QHBoxLayout()
        row.setSpacing(12)
        info = QLabel("灵眸 Sightly - 屏幕自动化识别系统")
        info.setStyleSheet("color: #9AA0A6;")
        row.addWidget(info)
        row.addStretch()
        about_btn = QPushButton("关于灵眸")
        about_btn.setObjectName("primary")
        about_btn.setCursor(Qt.PointingHandCursor)
        about_btn.clicked.connect(self._show_about_dialog)
        row.addWidget(about_btn)
        layout.addLayout(row)

    def _show_about_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("关于灵眸")
        dlg.setFixedSize(480, 400)
        dlg.setStyleSheet(self.styleSheet())

        layout = QVBoxLayout(dlg)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        title = QLabel("灵眸 Sightly")
        title.setObjectName("dialogTitle")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        version = QLabel("版本: 0.0.1")
        version.setAlignment(Qt.AlignCenter)
        version.setStyleSheet("color: #9AA0A6;")
        layout.addWidget(version)

        layout.addSpacing(8)

        desc = QLabel("基于 RapidOCR 引擎的屏幕自动化识别系统\n仅供个人学习研究使用")
        desc.setAlignment(Qt.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)

        layout.addSpacing(12)

        credits_title = QLabel("特别鸣谢")
        credits_title.setObjectName("cardTitle")
        credits_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(credits_title)

        credits = [
            "本程序基于 AutoDoor OCR 二次开发",
            "原作者: Flown王砖家",
            "原项目: https://github.com/wdhq4261761/autodoor",
        ]
        for t in credits:
            lbl = QLabel(t)
            lbl.setWordWrap(True)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("color: #9AA0A6; font-size: 13px;")
            layout.addWidget(lbl)

        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        view_btn = QPushButton("查看原项目")
        view_btn.setObjectName("primary")
        view_btn.setCursor(Qt.PointingHandCursor)
        view_btn.clicked.connect(lambda: webbrowser.open("https://github.com/wdhq4261761/autodoor"))
        btn_row.addWidget(view_btn)
        close_btn = QPushButton("关闭")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.clicked.connect(dlg.accept)
        btn_row.addWidget(close_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        dlg.exec()
