from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QKeyEvent, QShortcut, QKeySequence
from PySide6.QtWidgets import QApplication


def start_key_listening(app, target_var, button, is_shortcut=False):
    from PySide6.QtWidgets import QWidget

    original_text = button.text() if hasattr(button, 'text') else ""
    if hasattr(button, 'setEnabled'):
        button.setEnabled(False)

    app.status_label.setText("请按任意按键进行设置，按ESC键清空当前记录")

    _key_filter = _KeyFilter(app, target_var, button, is_shortcut, original_text)
    app._key_filter = _key_filter
    QApplication.instance().installEventFilter(_key_filter)


class _KeyFilter:
    def __init__(self, app, target_var, button, is_shortcut, original_text):
        self.app = app
        self.target_var = target_var
        self.button = button
        self.is_shortcut = is_shortcut
        self.original_text = original_text

    def eventFilter(self, obj, event):
        if event.type() != QKeyEvent.Type.KeyPress:
            return False

        key = event.key()
        text = event.text()

        if key == Qt.Key.Key_Escape:
            _set_target_value(self.target_var, "")
            _restore_button_state(self.button)
            self._cleanup()
            return True

        key_name = _qt_key_to_name(key, text)
        if key_name is None:
            return True

        _set_target_value(self.target_var, key_name)
        if self.is_shortcut:
            self.app.update_hotkey()

        _restore_button_state(self.button)
        self._cleanup()
        return True

    def _cleanup(self):
        QApplication.instance().removeEventFilter(self)
        if hasattr(self.app, '_key_filter'):
            del self.app._key_filter
        if hasattr(self.app, 'status_label'):
            self.app.status_label.setText("空闲")


def _qt_key_to_name(key, text):
    special_map = {
        Qt.Key_Insert: "Insert", Qt.Key_Delete: "Delete",
        Qt.Key_Home: "Home", Qt.Key_End: "End",
        Qt.Key_PageUp: "PageUp", Qt.Key_PageDown: "PageDown",
        Qt.Key_Up: "Up", Qt.Key_Down: "Down",
        Qt.Key_Left: "Left", Qt.Key_Down: "Down",
        Qt.Key_Return: "Enter", Qt.Key_Enter: "Enter",
        Qt.Key_Space: "Space", Qt.Key_Escape: "Escape",
        Qt.Key_Tab: "Tab", Qt.Key_Backspace: "Backspace",
        Qt.Key_Control: "Control_L", Qt.Key_Shift: "Shift_L",
        Qt.Key_Alt: "Alt_L",
    }

    if key in special_map:
        return special_map[key]

    if Qt.Key_F1 <= key <= Qt.Key_F12:
        return f"F{key - Qt.Key_F1 + 1}"

    if text and len(text) == 1 and text.isprintable():
        return text

    return None


def _set_target_value(target_var, value):
    if hasattr(target_var, 'set'):
        target_var.set(value)
    elif hasattr(target_var, 'setText'):
        target_var.setText(value)


def _restore_button_state(button):
    if hasattr(button, 'setEnabled'):
        button.setEnabled(True)
