import threading
import time
import re

from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import QTimer

from core.priority_lock import get_module_priority


pynput_to_pyautogui_map = {
    'page_up': 'pageup',
    'page_down': 'pagedown',
    'ctrl_l': 'ctrlleft',
    'ctrl_r': 'ctrlright',
    'shift_l': 'shiftleft',
    'shift_r': 'shiftright',
    'alt_l': 'altleft',
    'alt_r': 'altright',
    'cmd': 'command',
    'cmd_l': 'command',
    'cmd_r': 'command',
    'win_l': 'winleft',
    'win_r': 'winright',
}

_SKIP_TOGGLE = object()

def _get_script_text(app):
    """统一获取脚本文本，兼容 PySide6 和 tkinter 两套面板"""
    # PySide6 面板
    panel = getattr(app, 'panels', {}).get('script')
    if panel and hasattr(panel, '_script_editor'):
        try:
            return panel._script_editor.toPlainText()
        except Exception:
            pass
    # tkinter 旧面板
    if hasattr(app, 'script_text'):
        try:
            return app.script_text
        except Exception:
            pass
    return ""


def _set_status_text(app, text):
    if hasattr(app, 'status_label') and app.status_label:
        QTimer.singleShot(0, lambda: app.status_label.setText(text))


class ScriptModule:
    PRIORITY = get_module_priority('script')

    def __init__(self, app):
        self.app = app

    def start(self, start_color_recognition=True):
        if getattr(self.app, 'system_stopped', False):
            self.app.logging_manager.log_message("系统已完全停止，拒绝执行启动命令")
            return
        if not hasattr(self.app, 'script_executor'):
            self.app.script_executor = ScriptExecutor(self.app)
        script_content = _get_script_text(self.app)
        if not script_content.strip():
            self.app.logging_manager.log_message("脚本内容为空，跳过执行")
            return
        self.app.script_executor.run_script(script_content)
        self.app.logging_manager.log_message("脚本已启动")
        if start_color_recognition:
            try:
                if self.app.app_state.is_module_enabled('color'):
                    self.app.color_manager.start_color_recognition()
            except Exception:
                pass

    def stop(self, stop_color_recognition=True):
        executor = getattr(self.app, 'script_executor', None)
        if executor and getattr(executor, 'is_running', False):
            executor.stop_script()
        self.app.logging_manager.log_message("脚本已停止")
        if stop_color_recognition:
            try:
                self.app.color_manager.stop_color_recognition()
            except Exception:
                pass

    def start_script(self, start_color_recognition=True):
        if getattr(self.app, 'system_stopped', False):
            self.app.logging_manager.log_message("系统已完全停止，拒绝执行StartScript命令")
            return
        if not hasattr(self.app, 'script_executor'):
            self.app.script_executor = ScriptExecutor(self.app)
        script_content = _get_script_text(self.app)
        if not script_content.strip():
            QMessageBox.warning(None, "警告", "脚本内容为空，请先编写脚本！")
            return
        self.app.script_executor.run_script(script_content)
        _set_status_text(self.app, "脚本执行中...")
        self.app.logging_manager.log_message("脚本已启动")
        if start_color_recognition:
            try:
                if self.app.app_state.is_module_enabled('color'):
                    self.app.color_manager.start_color_recognition()
                    self.app.logging_manager.log_message("颜色识别已自动启动")
            except Exception:
                pass

    def stop_script(self, stop_color_recognition=True):
        executor = getattr(self.app, 'script_executor', None)
        if executor and getattr(executor, 'is_running', False):
            executor.stop_script()
            _set_status_text(self.app, "脚本已停止")
        if stop_color_recognition:
            try:
                self.app.color_manager.stop_color_recognition()
            except Exception:
                pass

    def start_recording(self):
        if not hasattr(self.app, 'script_executor'):
            self.app.script_executor = ScriptExecutor(self.app)
        self.app.script_executor.start_recording()
        _set_status_text(self.app, "录制中...")
        self.app.alarm_module.play_start_sound()

    def stop_recording(self):
        if hasattr(self.app, 'script_executor'):
            self.app.script_executor.stop_recording()
            _set_status_text(self.app, "录制已停止")
            self.app.alarm_module.play_stop_sound()


class ScriptExecutor:
    PRIORITY = get_module_priority('script')

    def __init__(self, app):
        self.app = app
        self.resources = []
        self.is_running = False
        self.is_paused = False
        self.execution_thread = None
        self.recording_thread = None
        self.recording_events = []
        self.recording_start_time = None
        self.last_event_time = None
        self.recording_grace_period = False
        self.core_graphics_available = False

    def register_resource(self, resource, cleanup_func):
        self.resources.append((resource, cleanup_func))

    def cleanup_resources(self):
        for resource, cleanup_func in reversed(self.resources):
            try:
                cleanup_func(resource)
            except Exception as e:
                self.app.logging_manager.error("SCRIPT", f"资源清理失败: {e}")
        self.resources.clear()

    def _optimize_delay(self, command, next_command=None):
        if command["type"] != "delay" or not next_command:
            return command
        if next_command["type"] in ["keydown", "keyup", "click"]:
            optimized = command.copy()
            optimized["time"] = max(0, command["time"] - 100)
            return optimized
        return command

    def _execute_with_optimization(self, command, next_command=None):
        optimized = self._optimize_delay(command, next_command)
        self.execute_command(optimized)

    def run_script(self, script_content):
        def execute():
            self.is_running = True
            self.is_paused = False
            pressed_keys = set()
            try:
                lines = script_content.splitlines()
                commands = []
                for line in lines:
                    command = self.parse_line(line)
                    if command:
                        commands.append(command)
                if not commands:
                    self.app.logging_manager.log_message("脚本中没有有效命令！")
                    self.is_running = False
                    return
                while self.is_running:
                    for i, command in enumerate(commands):
                        if not self.is_running:
                            break
                        while self.is_paused:
                            time.sleep(0.1)
                            if not self.is_running:
                                break
                        if not self.is_running:
                            break
                        if command["type"] in ["keydown", "keyup"]:
                            key = command["key"]
                            count = int(command["count"])
                            for _ in range(count):
                                if not self.is_running:
                                    break
                                while self.is_paused:
                                    time.sleep(0.1)
                                    if not self.is_running:
                                        break
                                if not self.is_running:
                                    break
                                try:
                                    if command["type"] == "keydown":
                                        if key not in pressed_keys:
                                            self.app.input_controller.key_down(key, priority=self.PRIORITY)
                                            pressed_keys.add(key)
                                    elif command["type"] == "keyup":
                                        if key in pressed_keys:
                                            self.app.input_controller.key_up(key, priority=self.PRIORITY)
                                            pressed_keys.remove(key)
                                except Exception as e:
                                    self.app.logging_manager.error("SCRIPT", f"执行按键 {key} 时出错: {str(e)}")
                        else:
                            next_cmd = commands[i + 1] if i + 1 < len(commands) else None
                            self._execute_with_optimization(command, next_cmd)
            except Exception as e:
                error_msg = f"脚本执行出错: {str(e)}"
                self.app.logging_manager.error("SCRIPT", error_msg)
                _set_status_text(self.app, f"执行错误: {str(e)}")
            finally:
                for key in pressed_keys:
                    try:
                        self.app.input_controller.key_up(key, priority=self.PRIORITY)
                        self.app.logging_manager.log_message(f"确保抬起: {key}")
                    except Exception as e:
                        self.app.logging_manager.error("SCRIPT", f"抬起按键 {key} 时出错: {str(e)}")
                self.is_running = False

        self.execution_thread = threading.Thread(target=execute, daemon=True)
        self.execution_thread.start()

    def run_script_once(self, script_content):
        def execute():
            self.is_running = True
            self.is_paused = False
            pressed_keys = set()
            try:
                lines = script_content.splitlines()
                commands = []
                for line in lines:
                    command = self.parse_line(line)
                    if command:
                        commands.append(command)
                if not commands:
                    self.app.logging_manager.log_message("脚本中没有有效命令！")
                    self.is_running = False
                    return
                for i, command in enumerate(commands):
                    if not self.is_running:
                        break
                    while self.is_paused:
                        time.sleep(0.1)
                        if not self.is_running:
                            break
                    if not self.is_running:
                        break
                    if command["type"] in ["keydown", "keyup"]:
                        key = command["key"]
                        count = int(command["count"])
                        for _ in range(count):
                            if not self.is_running:
                                break
                            while self.is_paused:
                                time.sleep(0.1)
                                if not self.is_running:
                                    break
                            if not self.is_running:
                                break
                            if command["type"] == "keydown":
                                if key not in pressed_keys:
                                    self.app.input_controller.key_down(key, priority=self.PRIORITY)
                                    pressed_keys.add(key)
                            elif command["type"] == "keyup":
                                if key in pressed_keys:
                                    self.app.input_controller.key_up(key, priority=self.PRIORITY)
                                    pressed_keys.remove(key)
                    else:
                        next_cmd = commands[i + 1] if i + 1 < len(commands) else None
                        self._execute_with_optimization(command, next_cmd)
            except Exception as e:
                error_msg = f"脚本执行出错: {str(e)}"
                self.app.logging_manager.error("SCRIPT", error_msg)
                _set_status_text(self.app, f"执行错误: {str(e)}")
            finally:
                for key in pressed_keys:
                    try:
                        self.app.input_controller.key_up(key, priority=self.PRIORITY)
                        self.app.logging_manager.log_message(f"确保抬起: {key}")
                    except Exception as e:
                        self.app.logging_manager.error("SCRIPT", f"抬起按键 {key} 时出错: {str(e)}")
                self.is_running = False
                self.app.logging_manager.log_message("脚本执行完成")

        self.execution_thread = threading.Thread(target=execute, daemon=True)
        self.execution_thread.start()

    def parse_line(self, line):
        line = line.strip()
        if not line:
            return None

        key_pattern = re.compile(r'^(KeyDown|KeyUp)\s+["\'](.*?)["\']\s*\,\s*(\d+)$', re.IGNORECASE)
        match = key_pattern.match(line)
        if match:
            command_type = match.group(1).lower()
            key = match.group(2).lower()
            count = int(match.group(3))
            return {"type": command_type, "key": key, "count": count}

        mouse_pattern = re.compile(r'^(Left|Right|Middle)(Down|Up|Click)\s+(\d+)$', re.IGNORECASE)
        match = mouse_pattern.match(line)
        if match:
            button = match.group(1).lower()
            action = match.group(2).lower()
            count = int(match.group(3))
            if action == "click":
                return {"type": "click", "button": button, "count": count}
            return {"type": f"mouse_{action}", "button": button, "count": count}

        move_pattern = re.compile(r"^MoveTo\s+(\d+)\s*\,\s*(\d+)$", re.IGNORECASE)
        match = move_pattern.match(line)
        if match:
            x = int(match.group(1))
            y = int(match.group(2))
            return {"type": "moveto", "x": x, "y": y}

        delay_pattern = re.compile(r"^Delay\s+(\d+)$", re.IGNORECASE)
        match = delay_pattern.match(line)
        if match:
            delay_time = int(match.group(1))
            return {"type": "delay", "time": delay_time}

        if line.strip().lower() == "stopscript":
            return {"type": "stopscript"}
        elif line.strip().lower() == "startscript":
            return {"type": "startscript"}

        return None

    def execute_command(self, command):
        try:
            if command["type"] in ["keydown", "keyup"]:
                key = command["key"]
                count = int(command["count"])
                for _ in range(count):
                    if not self.is_running:
                        break
                    while self.is_paused:
                        time.sleep(0.1)
                        if not self.is_running:
                            break
                    if not self.is_running:
                        break
                    if command["type"] == "keydown":
                        self.app.input_controller.key_down(key, priority=self.PRIORITY)
                    else:
                        self.app.input_controller.key_up(key, priority=self.PRIORITY)
            elif command["type"] in ["mouse_down", "mouse_up"]:
                button = command["button"]
                count = int(command["count"])
                for _ in range(count):
                    if not self.is_running:
                        break
                    while self.is_paused:
                        time.sleep(0.1)
                        if not self.is_running:
                            break
                    if not self.is_running:
                        break
                    if command["type"] == "mouse_down":
                        self.app.input_controller.mouse_down(button=button, priority=self.PRIORITY)
                    else:
                        self.app.input_controller.mouse_up(button=button, priority=self.PRIORITY)
            elif command["type"] == "click":
                button = command["button"]
                count = int(command["count"])
                for _ in range(count):
                    if not self.is_running:
                        break
                    while self.is_paused:
                        time.sleep(0.1)
                        if not self.is_running:
                            break
                    if not self.is_running:
                        break
                    self.app.input_controller.mouse_down(button=button, priority=self.PRIORITY)
                    time.sleep(0.05)
                    self.app.input_controller.mouse_up(button=button, priority=self.PRIORITY)
            elif command["type"] == "moveto":
                x = int(command["x"])
                y = int(command["y"])
                if self.is_running and not self.is_paused:
                    self.app.input_controller.move_to(x, y, priority=self.PRIORITY)
            elif command["type"] == "delay":
                delay_time = command["time"] / 1000
                self.app.logging_manager.log_message(f"执行: 延迟 {delay_time}秒")
                start_time = time.time()
                elapsed_time = 0
                while elapsed_time < delay_time:
                    if not self.is_running:
                        break
                    while self.is_paused:
                        time.sleep(0.1)
                        if not self.is_running:
                            break
                    if not self.is_running:
                        break
                    sleep_time = min(0.1, delay_time - elapsed_time)
                    time.sleep(sleep_time)
                    elapsed_time = time.time() - start_time
            elif command["type"] == "stopscript":
                if not self.is_running:
                    return
                while self.is_paused:
                    time.sleep(0.1)
                    if not self.is_running:
                        return
                if not self.is_running:
                    return
                self.app.logging_manager.log_message("执行: 停止脚本")
                QTimer.singleShot(0, lambda: self.app.script.stop(stop_color_recognition=False))
            elif command["type"] == "startscript":
                if not self.is_running:
                    return
                while self.is_paused:
                    time.sleep(0.1)
                    if not self.is_running:
                        return
                if not self.is_running:
                    return
                self.app.logging_manager.log_message("执行: 启动脚本")
                QTimer.singleShot(0, lambda: self.app.script.start(start_color_recognition=False))
        except Exception as e:
            error_msg = f"执行命令出错: {str(e)}"
            self.app.logging_manager.error("SCRIPT", error_msg)
            import traceback
            self.app.logging_manager.error("SCRIPT", f"错误详情: {traceback.format_exc()}")
            return

    def pause_script(self):
        self.is_paused = True

    def resume_script(self):
        self.is_paused = False

    def stop_script(self):
        self.is_running = False
        self.is_paused = False

    def start_recording(self):
        self.recording_grace_period = True

        def record():
            import time
            self.is_recording = True
            self.recording_events = []
            self.recording_start_time = time.time()
            self.last_event_time = self.recording_start_time
            pressed_keys = set()
            last_mouse_position = None
            keyboard = None
            mouse = None
            keyboard_listener = None
            mouse_listener = None

            try:
                from pynput import keyboard, mouse
            except Exception as e:
                QTimer.singleShot(0, lambda: QMessageBox.information(
                    None, "提示", "无法启动录制功能，请确保pynput模块已正确安装。"
                ))
                self.is_recording = False
                self.recording_events = []
                self.generate_recorded_script()
                return

            _record_hotkey = _SKIP_TOGGLE

            def _get_record_hotkey():
                nonlocal _record_hotkey
                if _record_hotkey is _SKIP_TOGGLE:
                    val = None
                    if hasattr(self.app, 'record_hotkey_var'):
                        try:
                            val = self.app.record_hotkey_var.get()
                        except Exception:
                            pass
                    if not val:
                        val = "f6"
                    _record_hotkey = val.lower()
                return _record_hotkey

            def on_key_press(key):
                if not self.is_recording:
                    return False
                if getattr(self, 'recording_grace_period', False):
                    self.recording_grace_period = False
                    return
                try:
                    key_name = key.char
                except AttributeError:
                    key_name = key.name
                except Exception:
                    return
                key_name = pynput_to_pyautogui_map.get(key_name, key_name)
                if key_name == _get_record_hotkey():
                    return
                if key_name not in pressed_keys:
                    current_time = time.time()
                    delay = int((current_time - self.last_event_time) * 1000)
                    self.last_event_time = current_time
                    try:
                        self.recording_events.append({
                            "type": "keydown", "key": key_name, "delay": delay
                        })
                        pressed_keys.add(key_name)
                    except Exception:
                        pass

            def on_key_release(key):
                if not self.is_recording:
                    return False
                if getattr(self, 'recording_grace_period', False):
                    return
                try:
                    key_name = key.char
                except AttributeError:
                    key_name = key.name
                except Exception:
                    return
                key_name = pynput_to_pyautogui_map.get(key_name, key_name)
                if key_name == _get_record_hotkey():
                    return
                if key_name in pressed_keys:
                    current_time = time.time()
                    delay = int((current_time - self.last_event_time) * 1000)
                    self.last_event_time = current_time
                    try:
                        self.recording_events.append({
                            "type": "keyup", "key": key_name, "delay": delay
                        })
                        pressed_keys.remove(key_name)
                    except Exception:
                        pass

            def on_mouse_move(x, y):
                if not self.is_recording:
                    return False
                if getattr(self, 'recording_grace_period', False):
                    return
                nonlocal last_mouse_position
                last_mouse_position = (x, y)

            def on_mouse_click(x, y, button, pressed):
                if not self.is_recording:
                    return False
                if getattr(self, 'recording_grace_period', False):
                    return
                current_time = time.time()
                delay = int((current_time - self.last_event_time) * 1000)
                self.last_event_time = current_time
                try:
                    button_name = button.name
                except Exception:
                    return
                mouse_x, mouse_y = last_mouse_position if last_mouse_position else (x, y)
                try:
                    self.recording_events.append({
                        "type": "moveto", "x": int(mouse_x), "y": int(mouse_y), "delay": delay
                    })
                    self.recording_events.append({
                        "type": f"mouse_{'down' if pressed else 'up'}",
                        "button": button_name, "x": int(mouse_x), "y": int(mouse_y), "delay": 0
                    })
                except Exception:
                    pass

            time.sleep(0.5)
            self.recording_grace_period = False
            self.app.logging_manager.log_message("🔴 开始录制操作...")

            try:
                keyboard_listener = keyboard.Listener(on_press=on_key_press, on_release=on_key_release)
                mouse_listener = mouse.Listener(on_move=on_mouse_move, on_click=on_mouse_click)
                self.register_resource(keyboard_listener, lambda listener: listener.stop())
                self.register_resource(mouse_listener, lambda listener: listener.stop())
                keyboard_listener.start()
                mouse_listener.start()
                while self.is_recording:
                    time.sleep(0.1)
            except Exception as e:
                QTimer.singleShot(0, lambda: QMessageBox.information(
                    None, "提示", f"录制启动失败: {str(e)}"
                ))
                self.is_recording = False
            finally:
                self.cleanup_resources()
                self.generate_recorded_script()
                self.app.logging_manager.log_message("🟢 录制完成")

        self.recording_thread = threading.Thread(target=record, daemon=True)
        self.recording_thread.start()

    def stop_recording(self):
        import time
        self.recording_grace_period = True
        self.is_recording = False
        self.is_listening = False
        time.sleep(0.1)
        if hasattr(self, 'keyboard_listener') and self.keyboard_listener:
            try:
                self.keyboard_listener.stop()
                self.keyboard_listener = None
            except Exception:
                pass
        if hasattr(self, 'mouse_listener') and self.mouse_listener:
            try:
                self.mouse_listener.stop()
                self.mouse_listener = None
            except Exception:
                pass
        if hasattr(self, 'key_listener') and self.key_listener:
            try:
                self.key_listener.stop_listening()
                self.key_listener = None
            except Exception:
                pass
        self.cleanup_resources()
        start = time.time()
        while any([
            hasattr(self, 'keyboard_listener') and self.keyboard_listener,
            hasattr(self, 'mouse_listener') and self.mouse_listener,
            hasattr(self, 'key_listener') and self.key_listener,
        ]) and time.time() - start < 0.5:
            time.sleep(0.01)

    def generate_recorded_script(self):
        current_platform = getattr(self.app, 'platform_adapter', None)
        if current_platform:
            current_platform = getattr(current_platform, 'platform', 'windows')

        script_content = ""
        event_types = {"keydown": 0, "keyup": 0, "moveto": 0, "mouse_down": 0, "mouse_up": 0}

        try:
            if hasattr(self, 'recording_events'):
                for event in self.recording_events:
                    if event["delay"] > 0:
                        script_content += f"Delay {event['delay']}\n"
                    if event["type"] in ["keydown", "keyup"]:
                        script_content += f"{event['type'].capitalize()} \"{event['key']}\", 1\n"
                        event_types[event["type"]] += 1
                    elif event["type"] == "moveto":
                        script_content += f"MoveTo {event['x']}, {event['y']}\n"
                        event_types["moveto"] += 1
                    elif event["type"] in ["mouse_down", "mouse_up"]:
                        button = event["button"].capitalize()
                        action = event["type"].split('_')[1].capitalize()
                        script_content += f"{button}{action} 1\n"
                        event_types[event["type"]] += 1

            if script_content:
                panel = getattr(self.app, 'panels', {}).get('script')
                if panel and hasattr(panel, '_script_editor'):
                    QTimer.singleShot(0, lambda: panel._script_editor.insertPlainText(script_content))
                elif hasattr(self.app, 'script_text'):
                    try:
                        self.app.script_text = script_content
                    except Exception:
                        pass
        except Exception:
            pass


def _get_record_hotkey(app):
    val = None
    if hasattr(app, 'record_hotkey_var'):
        try:
            val = app.record_hotkey_var.get()
        except Exception:
            pass
    return (val or "f6").lower()
