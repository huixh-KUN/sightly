import sys
import os
import re

from PySide6.QtCore import QTimer

PYINPUT_AVAILABLE = False
try:
    from pynput import keyboard as pynput_keyboard
    PYINPUT_AVAILABLE = True
except ImportError:
    pass

_MODIFIER_MAP = {
    "ctrl": "Ctrl",
    "alt": "Alt",
    "shift": "Shift",
    "win": "Win",
    "cmd": "Win",
}

_PYNPUT_MODIFIERS = {
    pynput_keyboard.Key.ctrl_l: "Ctrl",
    pynput_keyboard.Key.ctrl_r: "Ctrl",
    pynput_keyboard.Key.alt_l: "Alt",
    pynput_keyboard.Key.alt_r: "Alt",
    pynput_keyboard.Key.shift_l: "Shift",
    pynput_keyboard.Key.shift_r: "Shift",
    pynput_keyboard.Key.cmd_l: "Win",
    pynput_keyboard.Key.cmd_r: "Win",
}


def _parse_combo(combo_str):
    """解析组合键字符串，返回 (修饰键集合, 主键名)"""
    parts = combo_str.lower().split("+")
    mods = set()
    main_key = None
    for p in parts:
        normalized = _MODIFIER_MAP.get(p, p)
        if normalized in ("Ctrl", "Alt", "Shift", "Win"):
            mods.add(normalized)
        else:
            main_key = p
    return mods, main_key


def _pynput_key_name(key):
    """将 pynput 按键对象转为统一名称（小写）"""
    if hasattr(key, 'name'):
        return key.name
    if hasattr(key, 'char') and key.char:
        return key.char
    if hasattr(key, 'vk'):
        vk = key.vk
        if 48 <= vk <= 57:
            return chr(vk)
        if 65 <= vk <= 90:
            return chr(vk).lower()
        if 112 <= vk <= 123:
            return f"f{vk - 111}"
    return str(key)


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
    if hasattr(app, '_listener_health_timer') and app._listener_health_timer:
        try:
            app._listener_health_timer.stop()
        except Exception as e:
            app.logging_manager.error("HOTKEY", f"停止健康检查定时器失败: {e}")
    if hasattr(app, 'global_listener') and app.global_listener:
        try:
            app.global_listener.stop()
            app.logging_manager.log_message("旧的全局键盘监听器已停止")
        except Exception as e:
            app.logging_manager.log_message(f"停止旧的全局键盘监听器时出错: {str(e)}")


def get_key_name(key):
    """获取按键名称"""
    return _pynput_key_name(key).upper()


def _build_combo_str(mods, main_key):
    """从修饰键集合和主键名构建组合键字符串"""
    sorted_mods = sorted(mods, key=lambda m: ["Ctrl", "Alt", "Shift", "Win"].index(m))
    parts = sorted_mods + [main_key]
    return "+".join(parts)


def _match_shortcut(app, key_name, pressed_mods):
    """检查当前按下的键+修饰键是否匹配任何全局快捷键"""
    ks = app.app_state

    shortcuts = [
        (ks.start_shortcut, lambda: not app._is_running, ks.all_start_requested),
        (ks.stop_shortcut, lambda: app._is_running, ks.all_stop_requested),
    ]

    for shortcut_str, condition, action_signal in shortcuts:
        if not shortcut_str:
            continue
        target_mods, target_key = _parse_combo(shortcut_str)
        target_key_upper = target_key.upper() if target_key else ""
        match = (pressed_mods == target_mods and key_name == target_key_upper)
        app.logging_manager.debug("HOTKEY", f"  match {shortcut_str!r}: mods_match={pressed_mods==target_mods} key_match={key_name==target_key_upper} cond={condition() if match else '?'}")
        if match:
            if condition():
                action_signal.emit()
                return True

    # record_hotkey
    record_s = ks.record_hotkey
    if record_s:
        target_mods, target_key = _parse_combo(record_s)
        target_key_upper = target_key.upper() if target_key else ""
        match = (pressed_mods == target_mods and key_name == target_key_upper)
        app.logging_manager.debug("HOTKEY", f"  match record_hotkey {record_s!r}: mods_match={pressed_mods==target_mods} key_match={key_name==target_key_upper}")
        if match:
            ks.record_hotkey_triggered.emit()
            return True
    return False


def handle_global_key_press(app, key, pressed_mods=None):
    """处理全局按键事件"""
    try:
        raw_name = _pynput_key_name(key)
        key_name = raw_name.upper()

        # 如果是修饰键，更新状态但不触发
        if raw_name.lower() in ("ctrl_l", "ctrl_r", "alt_l", "alt_r", "shift_l", "shift_r", "cmd_l", "cmd_r"):
            return

        if pressed_mods is None:
            pressed_mods = set()

        _match_shortcut(app, key_name, pressed_mods)
    except Exception as e:
        app.logging_manager.error("HOTKEY", f"全局快捷键处理错误: {e}")


def setup_global_shortcuts(app):
    """设置全局快捷键"""
    if PYINPUT_AVAILABLE:
        try:
            from pynput import keyboard as pynput_keyboard

            pressed_mods = set()

            def on_press(key):
                raw = _pynput_key_name(key).lower()
                mod_name = _PYNPUT_MODIFIERS.get(key)
                if mod_name:
                    pressed_mods.add(mod_name)
                    return
                try:
                    key_name = raw.upper()
                    app.logging_manager.debug("HOTKEY", f"on_press key={key_name!r} mods={pressed_mods}")
                    _match_shortcut(app, key_name, pressed_mods.copy())
                except Exception as e:
                    app.logging_manager.error("HOTKEY", f"全局快捷键处理错误: {e}")

            def on_release(key):
                mod_name = _PYNPUT_MODIFIERS.get(key)
                if mod_name:
                    pressed_mods.discard(mod_name)

            app.global_listener = pynput_keyboard.Listener(on_press=on_press, on_release=on_release)
            app.global_listener.start()

            def _check_listener():
                try:
                    alive = app.global_listener.running
                except Exception as e:
                    app.logging_manager.error("HOTKEY", f"健康检查读取 listener.running 失败: {e}")
                    alive = False
                app.logging_manager.debug("HOTKEY", f"健康检查: listener_alive={alive}")
                if not alive:
                    app.logging_manager.error("HOTKEY", "全局快捷键监听已停止，正在重启...")
                    setup_shortcuts(app)

            app._listener_health_timer = QTimer()
            app._listener_health_timer.setInterval(10000)
            app._listener_health_timer.timeout.connect(_check_listener)
            app._listener_health_timer.start()
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
