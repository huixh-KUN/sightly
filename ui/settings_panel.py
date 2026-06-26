import os
import winsound

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal

from ui.widgets import SectionTitle
from ui.components import GeneralSettingsCard, AlarmSettingsCard, AboutCard


class SettingsPanel(QWidget):
    config_changed = Signal(dict)
    shortcuts_changed = Signal(str, str)

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self._setup_ui()
        self._connect_signals()

    def _connect_signals(self):
        self._general.config_changed.connect(self._on_config_changed)
        self._alarm.config_changed.connect(self._on_config_changed)
        self._alarm.preview_requested.connect(self._preview_sound)

    def _preview_sound(self, path):
        if not path or not os.path.exists(path):
            self.app.logging_manager.log_message(f"音频文件不存在: {path}")
            return
        try:
            winsound.PlaySound(path, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
        except Exception as e:
            self.app.logging_manager.error("ALARM", f"试听失败: {e}")

    def _on_config_changed(self):
        general = self._general.get_config()
        alarm_cfg = self._alarm.get_config()
        self.shortcuts_changed.emit(general.get("start_key", ""), general.get("stop_key", ""))
        self.config_changed.emit({"general": general, "alarm": alarm_cfg})

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(20)

        title_col = QVBoxLayout()
        title_col.setSpacing(4)
        title_col.addWidget(SectionTitle("设置"))
        subtitle = QLabel("配置应用参数和快捷键")
        subtitle.setObjectName("subtitle")
        title_col.addWidget(subtitle)
        layout.addLayout(title_col)

        self._general = GeneralSettingsCard(logging_manager=self.app.logging_manager)
        layout.addWidget(self._general)

        self._alarm = AlarmSettingsCard()
        layout.addWidget(self._alarm)

        layout.addWidget(AboutCard())
        layout.addStretch()

    def set_enabled(self, enabled):
        super().setEnabled(enabled)

    def collect_config(self):
        return {
            "general": self._general.get_config(),
            "alarm": self._alarm.get_config(),
        }

    def set_config(self, cfg):
        if "general" in cfg:
            self._general.set_config(cfg["general"])
        if "alarm" in cfg:
            self._alarm.set_config(cfg["alarm"])
