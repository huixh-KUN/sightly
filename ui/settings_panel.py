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

    def _on_config_changed(self):
        if hasattr(self.app, 'save_config') and callable(self.app.save_config):
            try:
                self.app.save_config()
            except Exception:
                pass

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

        self._general = GeneralSettingsCard()
        layout.addWidget(self._general)

        self._alarm = AlarmSettingsCard()
        layout.addWidget(self._alarm)

        layout.addWidget(AboutCard())
        layout.addStretch()

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
