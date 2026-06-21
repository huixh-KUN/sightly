from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeyEvent


class KeyCaptureWidget(QWidget):
    """触发按键捕获组件

    交互流程：
    1. 默认显示当前按键值 +「修改」+「重置」按钮
    2. 点击「修改」→ 按钮变「确定」，组件进入监听模式，捕获用户按下的键
    3. 按下任意键自动回显到标签上
    4. 点击「确定」保存并退出监听模式
    5. 点击「重置」清空按键值（不触发任何按键）
    """

    keyChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._key = ""
        self._listening = False
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self._key_label = QLabel("无")
        self._key_label.setStyleSheet(
            "color: #9AA0A6; font-size: 13px; background-color: #1E1E1E; "
            "border: 1px solid #3C4043; border-radius: 6px; padding: 5px 10px;"
        )
        layout.addWidget(self._key_label)

        self._edit_btn = QPushButton("修改")
        self._edit_btn.setCursor(Qt.PointingHandCursor)
        self._edit_btn.setFixedHeight(28)
        self._edit_btn.clicked.connect(self._on_edit_clicked)
        layout.addWidget(self._edit_btn)

        self._reset_btn = QPushButton("重置")
        self._reset_btn.setCursor(Qt.PointingHandCursor)
        self._reset_btn.setFixedHeight(28)
        self._reset_btn.clicked.connect(self._on_reset)
        layout.addWidget(self._reset_btn)

    def key(self):
        return self._key

    def setKey(self, key_str):
        self._key = key_str or ""
        self._update_display()

    def _update_display(self):
        if self._key:
            self._key_label.setText(self._key)
            self._key_label.setStyleSheet(
                "color: #8AB4F8; font-size: 13px; font-weight: 500; "
                "background-color: #1E1E1E; border: 1px solid #8AB4F8; "
                "border-radius: 6px; padding: 5px 10px;"
            )
        else:
            self._key_label.setText("无")
            self._key_label.setStyleSheet(
                "color: #9AA0A6; font-size: 13px; "
                "background-color: #1E1E1E; border: 1px solid #3C4043; "
                "border-radius: 6px; padding: 5px 10px;"
            )

    def _on_edit_clicked(self):
        if not self._listening:
            self._start_listening()
        else:
            self._stop_listening()

    def _start_listening(self):
        self._listening = True
        self._edit_btn.setText("确定")
        self._edit_btn.setStyleSheet(
            "background-color: #8AB4F8; color: #202124; border: none; "
            "border-radius: 6px; font-weight: 500;"
        )
        self._key_label.setText("请按键...")
        self._key_label.setStyleSheet(
            "color: #FDD663; font-size: 13px; font-weight: 500; "
            "background-color: #2C2C2C; border: 2px solid #8AB4F8; "
            "border-radius: 6px; padding: 5px 10px;"
        )
        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()
        self.grabKeyboard()

    def _stop_listening(self):
        self._listening = False
        self._edit_btn.setText("修改")
        self._edit_btn.setStyleSheet("")
        self.releaseKeyboard()
        self.setFocusPolicy(Qt.NoFocus)
        self._update_display()

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
        if key_name:
            self._key = key_name
            self._key_label.setText(key_name)
            self._key_label.setStyleSheet(
                "color: #8AB4F8; font-size: 13px; font-weight: 500; "
                "background-color: #1E1E1E; border: 2px solid #8AB4F8; "
                "border-radius: 6px; padding: 5px 10px;"
            )

    def _resolve_key(self, event: QKeyEvent):
        key = event.key()

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
        elif Qt.Key_A <= key <= Qt.Key_Z:
            return chr(key)
        elif Qt.Key_0 <= key <= Qt.Key_9:
            return chr(key)
        else:
            return None
