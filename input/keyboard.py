import sys
import os

from PySide6.QtCore import QTimer

PYINPUT_AVAILABLE = False
try:
    from pynput import keyboard as pynput_keyboard
    PYINPUT_AVAILABLE = True
except ImportError:
    pass


def get_available_keys():
    """获取可用按键列表"""
    return [
        "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s", "t", "u", "v", "w", "x", "y", "z",
        "0", "1", "2", "3", "4", "5", "6", "7", "8", "9",
        "space", "enter", "tab", "escape", "backspace", "delete", "insert",
        "equal", "plus", "minus", "asterisk", "slash", "backslash",
        "comma", "period", "semicolon", "apostrophe", "quote", "left", "right", "up", "down", "home", "end", "pageup", "pagedown",
        "f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12"
    ]


def stop_old_listener(app):
    """停止旧的全局键盘监听器（如果存在）"""
    # 停止pynput监听器
    if hasattr(app, 'global_listener') and app.global_listener:
        try:
            app.global_listener.stop()
            app.logging_manager.log_message("旧的全局键盘监听器已停止")
        except Exception as e:
            app.logging_manager.log_message(f"停止旧的全局键盘监听器时出错: {str(e)}")

def get_key_name(key):
    """获取按键名称
    Args:
        key: 按键对象
    
    Returns:
        str: 按键名称
    """
    if hasattr(key, 'name'):
        # 普通按键
        return key.name.upper()
    elif hasattr(key, 'char') and key.char:
        # 字符按键
        return key.char.upper()
    elif hasattr(key, 'vk'):
        # 特殊按键（F键等）
        if 112 <= key.vk <= 123:  # VK_F1=112, VK_F12=123
            return f"F{key.vk - 111}"  # F1=112-111=1, 依此类推
        else:
            return str(key)
    else:
        return str(key)

def handle_global_key_press(app, key):
    try:
        key_name = get_key_name(key)
        ks = app.app_state

        if key_name == ks.start_shortcut.upper() and not app.is_running:
            QTimer.singleShot(0, app._on_start_all)
        if key_name == ks.stop_shortcut.upper() and app.is_running:
            QTimer.singleShot(0, app._on_stop_all)
        if key_name == ks.record_hotkey.upper():
            QTimer.singleShot(0, lambda: (
                app.script_module.start_recording() if not hasattr(app, 'script_executor') or not getattr(app.script_executor, 'is_recording', False) else app.script_module.stop_recording()
            ))
    except Exception as e:
        app.logging_manager.error("HOTKEY", f"全局快捷键处理错误: {e}")

def setup_global_shortcuts(app):
    """设置全局快捷键
    Args:
        app: 应用实例
    Returns:
        bool: 是否设置成功
    """
    # 其他平台使用pynput
    if PYINPUT_AVAILABLE:
        try:
            from pynput import keyboard as pynput_keyboard
            # 创建并启动全局键盘监听器
            app.global_listener = pynput_keyboard.Listener(on_press=lambda key: handle_global_key_press(app, key))
            app.global_listener.start()
            app.logging_manager.log_message("全局快捷键监听已启动 (使用pynput)")
            return True
        except Exception as e:
            app.logging_manager.error("HOTKEY", f"pynput 全局快捷键设置失败: {e}")
    return False

def setup_shortcuts(app):
    stop_old_listener(app)

    if setup_global_shortcuts(app):
        app.logging_manager.log_message("全局快捷键设置成功")
    else:
        app.logging_manager.log_message("全局快捷键设置失败，快捷键功能将不可用")
