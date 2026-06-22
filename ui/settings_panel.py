import os
import winsound

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt

from ui.widgets import SectionTitle
from ui.components import GeneralSettingsCard, AlarmSettingsCard, AboutCard


class SettingsPanel(QWidget):
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
        if "start_key" in general:
            self.app.app_state.start_shortcut = general["start_key"] or ""
        if "stop_key" in general:
            self.app.app_state.stop_shortcut = general["stop_key"] or ""
        alarm_cfg = self._alarm.get_config()
        if alarm_cfg.get("sound_path"):
            self.app.alarm_sound_path.set(alarm_cfg["sound_path"])
        if "volume" in alarm_cfg:
            self.app.alarm_volume.set(alarm_cfg["volume"])
            self.app.alarm_volume_str.set(str(alarm_cfg["volume"]))
        self.app._register_shortcuts()
        if hasattr(self.app, 'save_config') and callable(self.app.save_config):
            try:
                self.app.save_config()
            except Exception as e:
                self.app.logging_manager.error("SETTINGS", f"保存配置失败: {e}")

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
