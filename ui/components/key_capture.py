import datetime

from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QFrame, QSizePolicy
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent


_MODIFIER_NAMES = [
    (Qt.ControlModifier, "Ctrl"),
    (Qt.AltModifier, "Alt"),
    (Qt.ShiftModifier, "Shift"),
    (Qt.MetaModifier, "Win"),
]


class KeyCaptureWidget(QWidget):
    """触发按键捕获：键值展示条 + 右侧紧凑操作按钮。"""

    keyChanged = Signal(str)

    def __init__(self, parent=None, logging_manager=None):
        super().__init__(parent)
        self._key = ""
        self._listening = False
        self._log = logging_manager
        self._setup_ui()

    def _debug(self, msg):
        if self._log:
            self._log.debug("KEYCAPTURE", msg)
        else:
            print(f"[KEYCAPTURE] {msg}")

    def _setup_ui(self):
        self.setObjectName("keyCaptureRoot")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self._btn_width = 56

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._chip = QFrame()
        self._chip.setObjectName("keyChip")
        self._chip.setFixedSize(88, 32)
        chip_layout = QHBoxLayout(self._chip)
        chip_layout.setContentsMargins(10, 0, 10, 0)
        chip_layout.setSpacing(0)
        self._key_label = QLabel("无")
        self._key_label.setObjectName("keyChipValue")
        self._key_label.setAlignment(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft)
        chip_layout.addWidget(self._key_label, 0)
        layout.addWidget(self._chip, 0)

        self._edit_btn = QPushButton("修改")
        self._edit_btn.setObjectName("keyCaptureBtn")
        self._edit_btn.setProperty("keyCaptureRole", "edit")
        self._edit_btn.setProperty("keyCaptureActive", "false")
        self._edit_btn.setCursor(Qt.PointingHandCursor)
        self._edit_btn.setFixedSize(self._btn_width, 32)
        self._edit_btn.clicked.connect(self._on_edit_clicked)
        layout.addWidget(self._edit_btn)

        self._reset_btn = QPushButton("重置")
        self._reset_btn.setObjectName("keyCaptureBtn")
        self._reset_btn.setProperty("keyCaptureRole", "reset")
        self._reset_btn.setCursor(Qt.PointingHandCursor)
        self._reset_btn.setFixedSize(self._btn_width, 32)
        self._reset_btn.clicked.connect(self._on_reset)
        layout.addWidget(self._reset_btn)

        self.setFixedWidth(88 + 4 + self._btn_width + 4 + self._btn_width)

    def key(self):
        return self._key

    def setKey(self, key_str):
        self._key = key_str or ""
        self._update_display()

    def _update_display(self):
        if self._listening:
            return
        self._key_label.setText(self._key if self._key else "无")

    def _on_edit_clicked(self):
        if not self._listening:
            self._start_listening()
        else:
            self._stop_listening()

    def _refresh_edit_btn_style(self):
        self._edit_btn.style().unpolish(self._edit_btn)
        self._edit_btn.style().polish(self._edit_btn)

    def _start_listening(self):
        self._listening = True
        self._edit_btn.setText("确定")
        self._edit_btn.setProperty("keyCaptureActive", "true")
        self._refresh_edit_btn_style()
        self._key_label.setText("请按键…")
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()
        self.grabKeyboard()
        self._debug("开始监听按键")

    def _stop_listening(self):
        self._listening = False
        self._edit_btn.setText("修改")
        self._edit_btn.setProperty("keyCaptureActive", "false")
        self._refresh_edit_btn_style()
        self.releaseKeyboard()
        self.setFocusPolicy(Qt.NoFocus)
        self._update_display()
        self._debug(f"停止监听，捕获按键: {self._key!r}")
        self.keyChanged.emit(self._key)

    def _on_reset(self):
        self._key = ""
        if self._listening:
            self._stop_listening()
        else:
            self._update_display()
        self.keyChanged.emit("")

    def keyPressEvent(self, event: QKeyEvent):
        if not self._listening:
            return super().keyPressEvent(event)

        key_name = self._resolve_key(event)
        self._debug(
            f"监听中捕获按键: raw_key={event.key()} mods={event.modifiers()} "
            f"resolved={key_name!r}"
        )
        if key_name:
            self._key = key_name
            self._key_label.setText(key_name)

    def _resolve_key(self, event: QKeyEvent):
        key = event.key()
        modifiers = event.modifiers()

        named_key = self._named_key(key)
        if named_key is None:
            return None

        mods = []
        for flag, name in _MODIFIER_NAMES:
            if modifiers & flag:
                mods.append(name)

        if not mods:
            return named_key

        return "+".join(mods + [named_key])

    @staticmethod
    def _named_key(key):
        key_map = {
            Qt.Key_F1: "F1", Qt.Key_F2: "F2", Qt.Key_F3: "F3", Qt.Key_F4: "F4",
            Qt.Key_F5: "F5", Qt.Key_F6: "F6", Qt.Key_F7: "F7", Qt.Key_F8: "F8",
            Qt.Key_F9: "F9", Qt.Key_F10: "F10", Qt.Key_F11: "F11", Qt.Key_F12: "F12",
            Qt.Key_Return: "Enter", Qt.Key_Enter: "Enter",
            Qt.Key_Space: "Space", Qt.Key_Tab: "Tab",
            Qt.Key_Escape: "Escape", Qt.Key_Backspace: "Backspace",
            Qt.Key_Delete: "Delete", Qt.Key_Insert: "Insert",
            Qt.Key_Home: "Home", Qt.Key_End: "End",
            Qt.Key_PageUp: "PageUp", Qt.Key_PageDown: "PageDown",
            Qt.Key_Up: "Up", Qt.Key_Down: "Down",
            Qt.Key_Left: "Left", Qt.Key_Right: "Right",
        }

        if key in key_map:
            return key_map[key]
        if Qt.Key_A <= key <= Qt.Key_Z:
            return chr(key)
        if Qt.Key_0 <= key <= Qt.Key_9:
            return chr(key)
        return None
