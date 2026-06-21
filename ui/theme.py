from PySide6.QtGui import QColor
from PySide6.QtWidgets import QApplication


class _DarkColors:
    BG = "#121212"
    SURFACE = "#1E1E1E"
    SURFACE_ELEVATED = "#2C2C2C"
    CARD = "#2C2C2C"
    CARD_HOVER = "#333333"
    BORDER = "#3C4043"
    PRIMARY = "#8AB4F8"
    PRIMARY_HOVER = "#A8C7FA"
    PRIMARY_DIM = "#5E97F6"
    TEXT = "#E8EAED"
    TEXT_SECONDARY = "#9AA0A6"
    TEXT_DIM = "#5F6368"
    SUCCESS = "#81C784"
    DANGER = "#F28B82"
    WARNING = "#FDD663"
    SCROLLBAR_BG = "#1E1E1E"
    SCROLLBAR_FG = "#3C4043"
    HEADER_BG = "#1A1A1A"

    QSS = """
QMainWindow, QWidget {
    background-color: #121212;
    color: #E8EAED;
    font-family: "Microsoft YaHei", "Google Sans", "Segoe UI", "Roboto", sans-serif;
    font-size: 14px;
}
QMainWindow > QWidget { background-color: #121212; }
#headerBar { background-color: #1A1A1A; border-bottom: 1px solid #3C4043; min-height: 56px; max-height: 56px; }
#headerTitle { color: #8AB4F8; font-size: 20px; font-weight: 500; letter-spacing: -0.5px; }
#versionBadge { color: #5F6368; font-size: 11px; background-color: #2C2C2C; border: none; border-radius: 12px; padding: 2px 10px; margin-left: 8px; }
#statusDot { background-color: #81C784; border-radius: 5px; min-width: 10px; max-width: 10px; min-height: 10px; max-height: 10px; }
#statusLabel { color: #9AA0A6; font-size: 13px; margin-left: 6px; }
#sidebar { background-color: #1A1A1A; border-right: 1px solid #3C4043; min-width: 200px; max-width: 200px; }
.navItem { background-color: transparent; border: none; border-radius: 0px; padding: 12px 20px; margin: 0px; text-align: left; color: #9AA0A6; font-size: 14px; font-weight: 400; }
.navItem:hover { background-color: #2C2C2C; color: #E8EAED; }
.navItem:checked { background-color: #2C2C2C; color: #8AB4F8; font-weight: 500; border-left: 3px solid #8AB4F8; }
#contentArea { background-color: #121212; }
QScrollBar:vertical { background-color: transparent; width: 8px; border: none; }
QScrollBar::handle:vertical { background-color: #3C4043; border-radius: 4px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background-color: #5F6368; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QScrollBar:horizontal { background-color: transparent; height: 8px; border: none; }
QScrollBar::handle:horizontal { background-color: #3C4043; border-radius: 4px; min-width: 30px; }
QScrollBar::handle:horizontal:hover { background-color: #5F6368; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }
QPushButton { background-color: #2C2C2C; color: #E8EAED; border: 1px solid #3C4043; border-radius: 8px; padding: 7px 18px; font-size: 14px; font-weight: 500; }
QPushButton:hover { background-color: #353535; border-color: #5F6368; }
QPushButton:pressed { background-color: #1E1E1E; }
QPushButton#primary { background-color: #8AB4F8; color: #202124; border: none; font-weight: 500; }
QPushButton#primary:hover { background-color: #A8C7FA; }
QPushButton#primary:pressed { background-color: #5E97F6; }
QPushButton#danger { background-color: transparent; color: #F28B82; border: 1px solid #F28B82; }
QPushButton#danger:hover { background-color: #F28B82; color: #202124; }
QPushButton:disabled { background-color: #1E1E1E; color: #5F6368; border-color: #3C4043; }
QLineEdit, QTextEdit, QPlainTextEdit { background-color: #1E1E1E; color: #E8EAED; border: 1px solid #3C4043; border-radius: 8px; padding: 8px 12px; selection-background-color: #8AB4F8; selection-color: #202124; font-size: 14px; }
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus { border-color: #8AB4F8; border-width: 2px; padding: 7px 11px; }
QComboBox { background-color: #1E1E1E; color: #E8EAED; border: 1px solid #3C4043; border-radius: 8px; padding: 8px 12px; min-width: 100px; font-size: 14px; }
QComboBox:hover { border-color: #5F6368; }
QComboBox:focus { border-color: #8AB4F8; border-width: 2px; padding: 7px 11px; }
QComboBox::drop-down { border: none; width: 28px; }
QComboBox::down-arrow { image: none; border-left: 5px solid transparent; border-right: 5px solid transparent; border-top: 6px solid #9AA0A6; margin-right: 4px; }
QComboBox QAbstractItemView { background-color: #2C2C2C; color: #E8EAED; border: 1px solid #3C4043; border-radius: 8px; padding: 4px; selection-background-color: #8AB4F833; selection-color: #8AB4F8; outline: none; }
QSpinBox, QDoubleSpinBox { background-color: #1E1E1E; color: #E8EAED; border: 1px solid #3C4043; border-radius: 8px; padding: 8px; min-width: 60px; font-size: 14px; }
QSpinBox:focus, QDoubleSpinBox:focus { border-color: #8AB4F8; border-width: 2px; padding: 7px; }
QSpinBox::up-button, QDoubleSpinBox::up-button { border: none; background-color: transparent; width: 0px; }
QSpinBox::down-button, QDoubleSpinBox::down-button { border: none; background-color: transparent; width: 0px; }
QCheckBox { spacing: 10px; color: #E8EAED; font-size: 14px; }
QCheckBox::indicator { width: 18px; height: 18px; border: 2px solid #5F6368; border-radius: 4px; background-color: transparent; }
QCheckBox::indicator:checked { background-color: #8AB4F8; border-color: #8AB4F8; }
QCheckBox::indicator:hover { border-color: #9AA0A6; }
QLabel { color: #E8EAED; background-color: transparent; }
QLabel#title { font-size: 15px; font-weight: 500; color: #E8EAED; }
QLabel#subtitle { font-size: 13px; color: #9AA0A6; }
QLabel#accent { color: #8AB4F8; font-weight: 500; }
QTabWidget::pane { border: none; background-color: transparent; }
QTabBar::tab { background-color: transparent; color: #9AA0A6; border: none; padding: 8px 20px; margin-right: 2px; border-radius: 8px 8px 0 0; font-size: 14px; }
QTabBar::tab:selected { background-color: #2C2C2C; color: #8AB4F8; font-weight: 500; }
QTabBar::tab:hover:!selected { background-color: #1E1E1E; }
QToolTip { background-color: #2C2C2C; color: #E8EAED; border: 1px solid #3C4043; border-radius: 8px; padding: 6px 12px; font-size: 12px; }
QProgressBar { background-color: #1E1E1E; border: none; border-radius: 4px; text-align: center; color: #E8EAED; height: 6px; font-size: 11px; }
QProgressBar::chunk { background-color: #8AB4F8; border-radius: 4px; }
QListWidget { background-color: #1E1E1E; border: 1px solid #3C4043; border-radius: 8px; padding: 4px; outline: none; }
QListWidget::item { padding: 8px 12px; border-radius: 6px; color: #E8EAED; }
QListWidget::item:selected { background-color: #8AB4F833; color: #8AB4F8; }
QListWidget::item:hover:!selected { background-color: #2C2C2C; }
QSplitter::handle { background-color: #3C4043; width: 1px; }
Card, #card, #settingsCard, #windowCard { background-color: #1E1E1E; border: 1px solid #3C4043; border-radius: 12px; }
Card:hover, #card:hover, #settingsCard:hover, #windowCard:hover { background-color: #252525; }
GroupCard, #groupCard { background-color: #2C2C2C; border: none; border-radius: 12px; }
GroupCard:hover, #groupCard:hover { background-color: #333333; }
#moduleCard { background-color: #333333; border: 1px solid #3C4043; border-radius: 10px; }
#moduleCard:hover { background-color: #3A3A3A; }
#sectionTitle { font-size: 20px; font-weight: 500; color: #E8EAED; letter-spacing: -0.3px; padding-bottom: 4px; }
#cardTitle { font-size: 15px; font-weight: 500; color: #E8EAED; }
#infoText { color: #9AA0A6; font-size: 14px; }
#accentText { color: #8AB4F8; font-weight: 500; font-size: 14px; }
#dialogTitle { font-size: 18px; font-weight: 500; color: #8AB4F8; }
#windowIcon { font-size: 16px; }
#sidebarSeparator { background-color: #3C4043; max-height: 1px; margin: 8px 16px; }
#divider { background-color: #3C4043; max-height: 1px; margin: 4px 0; }
"""


class _LightColors:
    BG = "#FFFFFF"
    SURFACE = "#F5F5F5"
    SURFACE_ELEVATED = "#EEEEEE"
    CARD = "#FFFFFF"
    CARD_HOVER = "#F5F5F5"
    BORDER = "#E0E0E0"
    PRIMARY = "#1976D2"
    PRIMARY_HOVER = "#1565C0"
    PRIMARY_DIM = "#64B5F6"
    TEXT = "#212121"
    TEXT_SECONDARY = "#757575"
    TEXT_DIM = "#BDBDBD"
    SUCCESS = "#4CAF50"
    DANGER = "#E53935"
    WARNING = "#FF9800"
    SCROLLBAR_BG = "#F5F5F5"
    SCROLLBAR_FG = "#C0C0C0"
    HEADER_BG = "#FAFAFA"

    QSS = """
QMainWindow, QWidget {
    background-color: #FFFFFF;
    color: #212121;
    font-family: "Microsoft YaHei", "Google Sans", "Segoe UI", "Roboto", sans-serif;
    font-size: 14px;
}
QMainWindow > QWidget { background-color: #FFFFFF; }
#headerBar { background-color: #FAFAFA; border-bottom: 1px solid #E0E0E0; min-height: 56px; max-height: 56px; }
#headerTitle { color: #1976D2; font-size: 20px; font-weight: 500; letter-spacing: -0.5px; }
#versionBadge { color: #BDBDBD; font-size: 11px; background-color: #F5F5F5; border: none; border-radius: 12px; padding: 2px 10px; margin-left: 8px; }
#statusDot { background-color: #4CAF50; border-radius: 5px; min-width: 10px; max-width: 10px; min-height: 10px; max-height: 10px; }
#statusLabel { color: #757575; font-size: 13px; margin-left: 6px; }
#sidebar { background-color: #FAFAFA; border-right: 1px solid #E0E0E0; min-width: 200px; max-width: 200px; }
.navItem { background-color: transparent; border: none; border-radius: 0px; padding: 12px 20px; margin: 0px; text-align: left; color: #757575; font-size: 14px; font-weight: 400; }
.navItem:hover { background-color: #EEEEEE; color: #212121; }
.navItem:checked { background-color: #EEEEEE; color: #1976D2; font-weight: 500; border-left: 3px solid #1976D2; }
#contentArea { background-color: #FFFFFF; }
QScrollBar:vertical { background-color: transparent; width: 8px; border: none; }
QScrollBar::handle:vertical { background-color: #C0C0C0; border-radius: 4px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background-color: #A0A0A0; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QScrollBar:horizontal { background-color: transparent; height: 8px; border: none; }
QScrollBar::handle:horizontal { background-color: #C0C0C0; border-radius: 4px; min-width: 30px; }
QScrollBar::handle:horizontal:hover { background-color: #A0A0A0; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }
QPushButton { background-color: #F5F5F5; color: #212121; border: 1px solid #E0E0E0; border-radius: 8px; padding: 7px 18px; font-size: 14px; font-weight: 500; }
QPushButton:hover { background-color: #EEEEEE; border-color: #C0C0C0; }
QPushButton:pressed { background-color: #E0E0E0; }
QPushButton#primary { background-color: #1976D2; color: #FFFFFF; border: none; font-weight: 500; }
QPushButton#primary:hover { background-color: #1565C0; }
QPushButton#primary:pressed { background-color: #0D47A1; }
QPushButton#danger { background-color: transparent; color: #E53935; border: 1px solid #E53935; }
QPushButton#danger:hover { background-color: #E53935; color: #FFFFFF; }
QPushButton:disabled { background-color: #F5F5F5; color: #BDBDBD; border-color: #E0E0E0; }
QLineEdit, QTextEdit, QPlainTextEdit { background-color: #FFFFFF; color: #212121; border: 1px solid #E0E0E0; border-radius: 8px; padding: 8px 12px; selection-background-color: #1976D2; selection-color: #FFFFFF; font-size: 14px; }
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus { border-color: #1976D2; border-width: 2px; padding: 7px 11px; }
QComboBox { background-color: #FFFFFF; color: #212121; border: 1px solid #E0E0E0; border-radius: 8px; padding: 8px 12px; min-width: 100px; font-size: 14px; }
QComboBox:hover { border-color: #C0C0C0; }
QComboBox:focus { border-color: #1976D2; border-width: 2px; padding: 7px 11px; }
QComboBox::drop-down { border: none; width: 28px; }
QComboBox::down-arrow { image: none; border-left: 5px solid transparent; border-right: 5px solid transparent; border-top: 6px solid #757575; margin-right: 4px; }
QComboBox QAbstractItemView { background-color: #FFFFFF; color: #212121; border: 1px solid #E0E0E0; border-radius: 8px; padding: 4px; selection-background-color: #1976D233; selection-color: #1976D2; outline: none; }
QSpinBox, QDoubleSpinBox { background-color: #FFFFFF; color: #212121; border: 1px solid #E0E0E0; border-radius: 8px; padding: 8px; min-width: 60px; font-size: 14px; }
QSpinBox:focus, QDoubleSpinBox:focus { border-color: #1976D2; border-width: 2px; padding: 7px; }
QSpinBox::up-button, QDoubleSpinBox::up-button { border: none; background-color: transparent; width: 0px; }
QSpinBox::down-button, QDoubleSpinBox::down-button { border: none; background-color: transparent; width: 0px; }
QCheckBox { spacing: 10px; color: #212121; font-size: 14px; }
QCheckBox::indicator { width: 18px; height: 18px; border: 2px solid #BDBDBD; border-radius: 4px; background-color: transparent; }
QCheckBox::indicator:checked { background-color: #1976D2; border-color: #1976D2; }
QCheckBox::indicator:hover { border-color: #757575; }
QLabel { color: #212121; background-color: transparent; }
QLabel#title { font-size: 15px; font-weight: 500; color: #212121; }
QLabel#subtitle { font-size: 13px; color: #757575; }
QLabel#accent { color: #1976D2; font-weight: 500; }
QTabWidget::pane { border: none; background-color: transparent; }
QTabBar::tab { background-color: transparent; color: #757575; border: none; padding: 8px 20px; margin-right: 2px; border-radius: 8px 8px 0 0; font-size: 14px; }
QTabBar::tab:selected { background-color: #EEEEEE; color: #1976D2; font-weight: 500; }
QTabBar::tab:hover:!selected { background-color: #F5F5F5; }
QToolTip { background-color: #FFFFFF; color: #212121; border: 1px solid #E0E0E0; border-radius: 8px; padding: 6px 12px; font-size: 12px; }
QProgressBar { background-color: #F5F5F5; border: none; border-radius: 4px; text-align: center; color: #212121; height: 6px; font-size: 11px; }
QProgressBar::chunk { background-color: #1976D2; border-radius: 4px; }
QListWidget { background-color: #FFFFFF; border: 1px solid #E0E0E0; border-radius: 8px; padding: 4px; outline: none; }
QListWidget::item { padding: 8px 12px; border-radius: 6px; color: #212121; }
QListWidget::item:selected { background-color: #1976D233; color: #1976D2; }
QListWidget::item:hover:!selected { background-color: #F5F5F5; }
QSplitter::handle { background-color: #E0E0E0; width: 1px; }
Card, #card, #settingsCard, #windowCard { background-color: #F5F5F5; border: 1px solid #E0E0E0; border-radius: 12px; }
Card:hover, #card:hover, #settingsCard:hover, #windowCard:hover { background-color: #EEEEEE; }
GroupCard, #groupCard { background-color: #FFFFFF; border: none; border-radius: 12px; }
GroupCard:hover, #groupCard:hover { background-color: #F5F5F5; }
#moduleCard { background-color: #FFFFFF; border: 1px solid #E0E0E0; border-radius: 10px; }
#moduleCard:hover { background-color: #F5F5F5; }
#sectionTitle { font-size: 20px; font-weight: 500; color: #212121; letter-spacing: -0.3px; padding-bottom: 4px; }
#cardTitle { font-size: 15px; font-weight: 500; color: #212121; }
#infoText { color: #757575; font-size: 14px; }
#accentText { color: #1976D2; font-weight: 500; font-size: 14px; }
#dialogTitle { font-size: 18px; font-weight: 500; color: #1976D2; }
#windowIcon { font-size: 16px; }
#sidebarSeparator { background-color: #E0E0E0; max-height: 1px; margin: 8px 16px; }
#divider { background-color: #E0E0E0; max-height: 1px; margin: 4px 0; }
"""


class ThemeManager:
    _current = "dark"
    _themes = {
        "dark": _DarkColors,
        "light": _LightColors,
    }

    @classmethod
    def current(cls):
        return cls._themes[cls._current]

    @classmethod
    def qss(cls):
        return cls.current().QSS

    @classmethod
    def switch_to(cls, mode):
        if mode not in cls._themes:
            return
        cls._current = mode
        app = QApplication.instance()
        if app:
            app.setStyleSheet(cls.qss())

    @classmethod
    def is_dark(cls):
        return cls._current == "dark"

    @classmethod
    def register_theme(cls, name, colors_class):
        cls._themes[name] = colors_class

    @classmethod
    def theme_names(cls):
        return list(cls._themes.keys())


class _ColorsProxy:
    def __getattr__(self, name):
        return getattr(ThemeManager.current(), name)


Colors = _ColorsProxy()
QSS = ThemeManager.qss()
