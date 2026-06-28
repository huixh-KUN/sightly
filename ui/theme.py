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
    SWITCH_TRACK_OFF = "#5F6368"
    SWITCH_TRACK_ON = "#8AB4F8"
    SWITCH_TRACK_DISABLED = "#3C4043"
    SWITCH_KNOB = "#FFFFFF"
    SWITCH_KNOB_DISABLED = "#9AA0A6"
    SWITCH_KNOB_SHADOW_ALPHA = 36
    SWITCH_KNOB_BORDER = None

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
QScrollArea { border: none; background: transparent; }
QPushButton { background-color: #2C2C2C; color: #E8EAED; border: 1px solid #3C4043; border-radius: 8px; padding: 7px 18px; font-size: 14px; font-weight: 500; }
QPushButton:hover { background-color: #353535; border-color: #5F6368; }
QPushButton:pressed { background-color: #1E1E1E; }
QPushButton#primary { background-color: #2C2C2C; color: #E8EAED; border: 1px solid #3C4043; font-weight: 500; }
QPushButton#primary:hover { background-color: #353535; border-color: #5F6368; }
QPushButton#primary:pressed { background-color: #1E1E1E; }
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
QComboBox QAbstractItemView::item { padding: 8px 12px; min-height: 24px; }
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
Card, #card, #settingsCard, #windowCard, #configCard { background-color: #1E1E1E; border: 1px solid #3C4043; border-radius: 12px; }
Card:hover, #card:hover, #settingsCard:hover, #windowCard:hover, #configCard:hover { background-color: #252525; }
#configCard #configCardRow, #configCard #fieldsRow, #configCard #fieldGroup, #configCard #spinRangeRow { background: transparent; }
#keyCaptureRoot { background: transparent; }
#keyCaptureRoot QPushButton#keyCaptureBtn { background-color: #2C2C2C; color: #E8EAED; border: 1px solid #5F6368; border-radius: 6px; padding: 0 4px; font-size: 13px; font-weight: 500; min-width: 56px; max-width: 56px; min-height: 32px; max-height: 32px; }
#keyCaptureRoot QPushButton#keyCaptureBtn:hover { background-color: #353535; border-color: #8AB4F8; color: #E8EAED; }
#keyCaptureRoot QPushButton#keyCaptureBtn:pressed { background-color: #1E1E1E; }
#keyCaptureRoot QPushButton#keyCaptureBtn[keyCaptureActive="true"] { background-color: #8AB4F8; color: #202124; border-color: #8AB4F8; font-weight: 600; }
#keyCaptureRoot QPushButton#keyCaptureBtn[keyCaptureActive="true"]:hover { background-color: #A8C7FA; border-color: #A8C7FA; }
#keyCaptureRoot QPushButton#keyCaptureBtn[keyCaptureRole="reset"] { color: #9AA0A6; }
#keyCaptureRoot QPushButton#keyCaptureBtn[keyCaptureRole="reset"]:hover { color: #F28B82; border-color: #F28B82; background-color: #F28B8218; }
#settingsCard QLabel#rowLabel { color: #9AA0A6; font-size: 13px; }
#rowLabel { color: #9AA0A6; font-size: 13px; }
GroupCard, #groupCard { background-color: #2C2C2C; border: none; border-radius: 12px; }
GroupCard:hover, #groupCard:hover { background-color: #333333; }
#groupListItem { background-color: #1E1E1E; border: 1px solid #3C4043; border-radius: 12px; }
#groupListItem:hover { background-color: #252525; border-color: #5F6368; }
#groupListItem[groupActive="false"] { background-color: #1A1A1A; }
#groupListItem[groupActive="false"] #groupName { color: #9AA0A6; }
#groupStatusStrip { border: none; margin: 12px 0 12px 0; }
#groupIconBadge { background-color: #2C2C2C; border: 1px solid #3C4043; border-radius: 10px; min-width: 40px; max-width: 40px; min-height: 40px; max-height: 40px; }
#groupListItem #groupIcon { font-size: 18px; min-width: 40px; max-width: 40px; }
#groupListItem #groupName { font-size: 15px; font-weight: 600; color: #E8EAED; }
#groupListItem #groupParams { color: #9AA0A6; font-size: 12px; }
#groupListItem #groupTemplate { color: #8AB4F8; font-size: 12px; }
#groupListItem #groupRegion { color: #8AB4F8; font-size: 12px; }
#groupListItem #groupDetail { color: #9AA0A6; font-size: 12px; }
#groupMetaDot { color: #5F6368; font-size: 12px; padding: 0 6px; background: transparent; }
#groupActionDock { background: transparent; }
#moduleCard { background-color: #333333; border: 1px solid #3C4043; border-radius: 10px; }
#moduleCard:hover { background-color: #3A3A3A; }
#sectionTitle { font-size: 20px; font-weight: 500; color: #E8EAED; letter-spacing: -0.3px; padding-bottom: 4px; }
#cardTitle { font-size: 15px; font-weight: 500; color: #E8EAED; }
#cardHeader { font-size: 14px; font-weight: 500; color: #E8EAED; }
#infoText { color: #9AA0A6; font-size: 14px; }
#accentText { color: #8AB4F8; font-weight: 500; font-size: 14px; }
#dialogTitle { font-size: 18px; font-weight: 500; color: #8AB4F8; }
#windowIcon { font-size: 16px; }
#sidebarSeparator { background-color: #3C4043; max-height: 1px; margin: 8px 16px; }
#divider { background-color: #3C4043; max-height: 1px; margin: 4px 0; }
#groupEditWindow { background-color: #121212; }
#groupEditScroll { border: none; background: transparent; }
#groupEditBody { background: transparent; }
#groupEditHeader { background: transparent; border-bottom: 1px solid #3C4043; padding-bottom: 4px; margin-bottom: 4px; }
#groupEditHint { font-size: 12px; color: #9AA0A6; font-weight: 500; }
#groupEditTitle { font-size: 18px; font-weight: 600; padding: 10px 14px; border: 1px solid #3C4043; border-radius: 10px; background-color: #1A1A1A; }
#groupEditTitle:focus { border-color: #8AB4F8; }
#valueChip { background-color: #1A1A1A; border: 1px solid #3C4043; border-radius: 8px; }
#valueChip:hover { border-color: #5F6368; background-color: #222222; }
#keyChip { background-color: #1A1A1A; border: 1px solid #3C4043; border-radius: 8px; min-height: 32px; max-height: 32px; }
#keyChipValue { color: #E8EAED; font-size: 13px; font-weight: 500; }
QPushButton#compactBtn { padding: 4px 8px; font-size: 13px; min-width: 0; border-radius: 6px; }
#rangeSep { color: #9AA0A6; font-size: 13px; }
#inlineFieldLabel { color: #9AA0A6; font-size: 13px; }
"""


class _LightColors:
    BG = "#F0F0F0"
    SURFACE = "#E8E8E8"
    SURFACE_ELEVATED = "#E0E0E0"
    CARD = "#F5F5F5"
    CARD_HOVER = "#EBEBEB"
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
    SWITCH_TRACK_OFF = "#BDBDBD"
    SWITCH_TRACK_ON = "#1976D2"
    SWITCH_TRACK_DISABLED = "#E0E0E0"
    SWITCH_KNOB = "#FFFFFF"
    SWITCH_KNOB_DISABLED = "#F5F5F5"
    SWITCH_KNOB_SHADOW_ALPHA = 22
    SWITCH_KNOB_BORDER = "#00000014"

    QSS = """
QMainWindow, QWidget {
    background-color: #F0F0F0;
    color: #212121;
    font-family: "Microsoft YaHei", "Google Sans", "Segoe UI", "Roboto", sans-serif;
    font-size: 14px;
}
QMainWindow > QWidget { background-color: #F0F0F0; }
#headerBar { background-color: #E8E8E8; border-bottom: 1px solid #D0D0D0; min-height: 56px; max-height: 56px; }
#headerTitle { color: #1976D2; font-size: 20px; font-weight: 500; letter-spacing: -0.5px; }
#statusDot { background-color: #4CAF50; border-radius: 5px; min-width: 10px; max-width: 10px; min-height: 10px; max-height: 10px; }
#statusLabel { color: #757575; font-size: 13px; margin-left: 6px; }
#sidebar { background-color: #E8E8E8; border-right: 1px solid #D0D0D0; min-width: 200px; max-width: 200px; }
.navItem { background-color: transparent; border: none; border-radius: 0px; padding: 12px 20px; margin: 0px; text-align: left; color: #757575; font-size: 14px; font-weight: 400; }
.navItem:hover { background-color: #E0E0E0; color: #212121; }
.navItem:checked { background-color: #E0E0E0; color: #1976D2; font-weight: 500; border-left: 3px solid #1976D2; }
#contentArea { background-color: #F0F0F0; }
QScrollBar:vertical { background-color: transparent; width: 8px; border: none; }
QScrollBar::handle:vertical { background-color: #C0C0C0; border-radius: 4px; min-height: 30px; }
QScrollBar::handle:vertical:hover { background-color: #A0A0A0; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QScrollBar:horizontal { background-color: transparent; height: 8px; border: none; }
QScrollBar::handle:horizontal { background-color: #C0C0C0; border-radius: 4px; min-width: 30px; }
QScrollBar::handle:horizontal:hover { background-color: #A0A0A0; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0px; }
QScrollArea { border: none; background: transparent; }
QPushButton { background-color: #E8E8E8; color: #212121; border: 1px solid #D0D0D0; border-radius: 8px; padding: 7px 18px; font-size: 14px; font-weight: 500; }
QPushButton:hover { background-color: #E0E0E0; border-color: #C0C0C0; }
QPushButton:pressed { background-color: #D6D6D6; }
QPushButton#primary { background-color: #E0E0E0; color: #212121; border: 1px solid #C0C0C0; font-weight: 500; }
QPushButton#primary:hover { background-color: #D6D6D6; border-color: #A0A0A0; }
QPushButton#primary:pressed { background-color: #CCCCCC; }
QPushButton#danger { background-color: transparent; color: #E53935; border: 1px solid #E53935; }
QPushButton#danger:hover { background-color: #E53935; color: #FFFFFF; }
QPushButton:disabled { background-color: #E8E8E8; color: #BDBDBD; border-color: #D0D0D0; }
QLineEdit, QTextEdit, QPlainTextEdit { background-color: #F0F0F0; color: #212121; border: 1px solid #D0D0D0; border-radius: 8px; padding: 8px 12px; selection-background-color: #1976D2; selection-color: #FFFFFF; font-size: 14px; }
QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus { border-color: #1976D2; border-width: 2px; padding: 7px 11px; }
QComboBox { background-color: #F0F0F0; color: #212121; border: 1px solid #D0D0D0; border-radius: 8px; padding: 8px 12px; min-width: 100px; font-size: 14px; }
QComboBox:hover { border-color: #C0C0C0; }
QComboBox:focus { border-color: #1976D2; border-width: 2px; }

QComboBox::drop-down { border: none; width: 28px; }
QComboBox::down-arrow { image: none; border-left: 5px solid transparent; border-right: 5px solid transparent; border-top: 6px solid #757575; margin-right: 4px; }
QComboBox QAbstractItemView { background-color: #F0F0F0; color: #212121; border: 1px solid #D0D0D0; border-radius: 8px; padding: 4px; selection-background-color: #1976D233; selection-color: #1976D2; outline: none; }
QComboBox QAbstractItemView::item { padding: 8px 12px; min-height: 24px; }
QSpinBox, QDoubleSpinBox { background-color: #F0F0F0; color: #212121; border: 1px solid #D0D0D0; border-radius: 8px; padding: 8px; min-width: 60px; font-size: 14px; }
QSpinBox:focus, QDoubleSpinBox:focus { border-color: #1976D2; border-width: 2px; }
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
QToolTip { background-color: #F0F0F0; color: #212121; border: 1px solid #D0D0D0; border-radius: 8px; padding: 6px 12px; font-size: 12px; }
QProgressBar { background-color: #E8E8E8; border: none; border-radius: 4px; text-align: center; color: #212121; height: 6px; font-size: 11px; }
QProgressBar::chunk { background-color: #1976D2; border-radius: 4px; }
QListWidget { background-color: #F0F0F0; border: 1px solid #D0D0D0; border-radius: 8px; padding: 4px; outline: none; }
QListWidget::item { padding: 8px 12px; border-radius: 6px; color: #212121; }
QListWidget::item:selected { background-color: #1976D233; color: #1976D2; }
QListWidget::item:hover:!selected { background-color: #E8E8E8; }
QSplitter::handle { background-color: #D0D0D0; width: 1px; }
Card, #card, #settingsCard, #windowCard, #configCard { background-color: #F0F0F0; border: 1px solid #D0D0D0; border-radius: 12px; }
Card:hover, #card:hover, #settingsCard:hover, #windowCard:hover, #configCard:hover { background-color: #E8E8E8; }
#configCard #configCardRow, #configCard #fieldsRow, #configCard #fieldGroup, #configCard #spinRangeRow { background: transparent; }
#keyCaptureRoot { background: transparent; }
#keyCaptureRoot QPushButton#keyCaptureBtn { background-color: #FFFFFF; color: #212121; border: 1px solid #9E9E9E; border-radius: 6px; padding: 0 4px; font-size: 13px; font-weight: 500; min-width: 56px; max-width: 56px; min-height: 32px; max-height: 32px; }
#keyCaptureRoot QPushButton#keyCaptureBtn:hover { background-color: #F5F5F5; border-color: #1976D2; color: #212121; }
#keyCaptureRoot QPushButton#keyCaptureBtn:pressed { background-color: #EEEEEE; }
#keyCaptureRoot QPushButton#keyCaptureBtn[keyCaptureActive="true"] { background-color: #1976D2; color: #FFFFFF; border-color: #1976D2; font-weight: 600; }
#keyCaptureRoot QPushButton#keyCaptureBtn[keyCaptureActive="true"]:hover { background-color: #1565C0; border-color: #1565C0; }
#keyCaptureRoot QPushButton#keyCaptureBtn[keyCaptureRole="reset"] { color: #757575; }
#keyCaptureRoot QPushButton#keyCaptureBtn[keyCaptureRole="reset"]:hover { color: #E53935; border-color: #E53935; background-color: #E5393514; }
#settingsCard QLabel#rowLabel { color: #757575; font-size: 13px; }
#rowLabel { color: #9AA0A6; font-size: 13px; }
GroupCard, #groupCard { background-color: #F5F5F5; border: none; border-radius: 12px; }
GroupCard:hover, #groupCard:hover { background-color: #EDEDED; }
#groupListItem { background-color: #F0F0F0; border: 1px solid #D0D0D0; border-radius: 12px; }
#groupListItem:hover { background-color: #E8E8E8; border-color: #C0C0C0; }
#groupListItem[groupActive="false"] { background-color: #ECECEC; }
#groupListItem[groupActive="false"] #groupName { color: #9E9E9E; }
#groupStatusStrip { border: none; margin: 12px 0 12px 0; }
#groupIconBadge { background-color: #FFFFFF; border: 1px solid #D0D0D0; border-radius: 10px; min-width: 40px; max-width: 40px; min-height: 40px; max-height: 40px; }
#groupListItem #groupIcon { font-size: 18px; min-width: 40px; max-width: 40px; }
#groupListItem #groupName { font-size: 15px; font-weight: 600; color: #212121; }
#groupListItem #groupParams { color: #757575; font-size: 12px; }
#groupListItem #groupTemplate { color: #1976D2; font-size: 12px; }
#groupListItem #groupRegion { color: #1976D2; font-size: 12px; }
#groupListItem #groupDetail { color: #757575; font-size: 12px; }
#groupMetaDot { color: #BDBDBD; font-size: 12px; padding: 0 6px; background: transparent; }
#groupActionDock { background: transparent; }
#moduleCard { background-color: #F5F5F5; border: 1px solid #D0D0D0; border-radius: 10px; }
#moduleCard:hover { background-color: #EDEDED; }
#sectionTitle { font-size: 20px; font-weight: 500; color: #212121; letter-spacing: -0.3px; padding-bottom: 4px; }
#cardTitle { font-size: 15px; font-weight: 500; color: #212121; }
#cardHeader { font-size: 14px; font-weight: 500; color: #212121; }
#infoText { color: #757575; font-size: 14px; }
#accentText { color: #1976D2; font-weight: 500; font-size: 14px; }
#dialogTitle { font-size: 18px; font-weight: 500; color: #1976D2; }
#windowIcon { font-size: 16px; }
#sidebarSeparator { background-color: #E0E0E0; max-height: 1px; margin: 8px 16px; }
#divider { background-color: #E0E0E0; max-height: 1px; margin: 4px 0; }
#groupEditWindow { background-color: #F0F0F0; }
#groupEditScroll { border: none; background: transparent; }
#groupEditBody { background: transparent; }
#groupEditHeader { background: transparent; border-bottom: 1px solid #D0D0D0; padding-bottom: 4px; margin-bottom: 4px; }
#groupEditHint { font-size: 12px; color: #757575; font-weight: 500; }
#groupEditTitle { font-size: 18px; font-weight: 600; padding: 10px 14px; border: 1px solid #D0D0D0; border-radius: 10px; background-color: #FFFFFF; }
#groupEditTitle:focus { border-color: #1976D2; }
#valueChip { background-color: #FFFFFF; border: 1px solid #D0D0D0; border-radius: 8px; }
#valueChip:hover { border-color: #B0B0B0; background-color: #FAFAFA; }
#keyChip { background-color: #FFFFFF; border: 1px solid #D0D0D0; border-radius: 8px; min-height: 32px; max-height: 32px; }
#keyChipValue { color: #212121; font-size: 13px; font-weight: 500; }
QPushButton#compactBtn { padding: 4px 8px; font-size: 13px; min-width: 0; border-radius: 6px; }
#rangeSep { color: #757575; font-size: 13px; }
#inlineFieldLabel { color: #757575; font-size: 13px; }
#rowLabel { color: #757575; font-size: 13px; }
"""


class ThemeManager:
    _current = "dark"
    _themes = {
        "dark": _DarkColors,
        "light": _LightColors,
    }
    _switch_callbacks = []

    @classmethod
    def current(cls):
        return cls._themes[cls._current]

    @classmethod
    def qss(cls):
        return cls.current().QSS

    @classmethod
    def on_switch(cls, callback):
        if callback not in cls._switch_callbacks:
            cls._switch_callbacks.append(callback)

    @classmethod
    def off_switch(cls, callback):
        try:
            cls._switch_callbacks.remove(callback)
        except ValueError:
            pass

    @classmethod
    def switch_to(cls, mode):
        if mode not in cls._themes:
            return
        cls._current = mode
        app = QApplication.instance()
        if app:
            app.setStyleSheet(cls.qss())
        for cb in list(cls._switch_callbacks):
            try:
                cb(mode)
            except RuntimeError:
                cls.off_switch(cb)

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
