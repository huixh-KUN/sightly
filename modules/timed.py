import threading
import time

from PySide6.QtCore import QTimer

from core.priority_lock import get_module_priority
from core.click_handler import ClickHandler
from core.config import ConfigVar


class TimedModule:
    """
    定时任务模块
    优先级: 5 (Number=6 > Timed=5 > Image=4 > OCR=3 > Color=2 > Script=1)
    """
    
    PRIORITY = get_module_priority('timed')
    
    def __init__(self, app):
        self.app = app
        self.click_handler = ClickHandler(app)
    
    def start_timed_tasks(self):
        def start_func():
            start_count = 0
            groups = getattr(self.app, 'timed_groups', [])
            for i, group in enumerate(groups):
                if group["enabled"].get():
                    try:
                        interval = int(group["interval"].get())
                    except (ValueError, TypeError):
                        interval = 10
                    key = group["key"].get()
                    stop_event = threading.Event()
                    stop_events = getattr(self.app, 'timed_stop_events', {})
                    stop_events[i] = stop_event
                    if not hasattr(self.app, 'timed_stop_events'):
                        self.app.timed_stop_events = stop_events
                    else:
                        self.app.timed_stop_events[i] = stop_event
                    threads = getattr(self.app, 'timed_threads', [])
                    thread = threading.Thread(
                        target=self.timed_task_loop,
                        args=(i, interval, key, stop_event), daemon=True
                    )
                    threads.append(thread)
                    if not hasattr(self.app, 'timed_threads'):
                        self.app.timed_threads = threads
                    else:
                        self.app.timed_threads.append(thread)
                    thread.start()
                    start_count += 1
            return start_count

        start_func()

    def stop_timed_tasks(self):
        for stop_event in getattr(self.app, 'timed_stop_events', {}).values():
            stop_event.set()
        if hasattr(self.app, 'timed_threads'):
            for t in self.app.timed_threads:
                if t.is_alive():
                    t.join(timeout=1)
            self.app.timed_threads.clear()
        if hasattr(self.app, 'timed_stop_events'):
            self.app.timed_stop_events.clear()

    def timed_task_loop(self, group_index, interval, key, stop_event):
        groups = getattr(self.app, 'timed_groups', [])
        while not stop_event.is_set():
            if group_index >= len(groups) or not groups[group_index]["enabled"].get():
                break
            try:
                for _ in range(int(interval)):
                    if stop_event.is_set():
                        return
                    time.sleep(1)
                if stop_event.is_set():
                    return
                if group_index >= len(groups):
                    break
                group = groups[group_index]
                if stop_event.is_set():
                    return
                self.app.alarm_module.play_alarm_sound(group["alarm"])
                if stop_event.is_set():
                    return
                    if group["click_enabled"].get():
                        if stop_event.is_set():
                            return
                        pos_x = group["position_x"].get()
                        pos_y = group["position_y"].get()
                        if pos_x != 0 or pos_y != 0:
                            try:
                                offset_range = int(group.get("click_offset", ConfigVar("0")).get())
                            except (ValueError, TypeError):
                                offset_range = 0
                            self.click_handler.execute_click(
                                x=pos_x, y=pos_y, priority=self.PRIORITY,
                                module_name="定时任务", index=group_index, delay=0.5,
                                offset_range=offset_range
                            )
                    if stop_event.is_set():
                        return
                if key:
                    if stop_event.is_set():
                        return
                    import platform
                    plat = platform.system()
                    self.app.logging_manager.log_message(
                        f"[{plat}] 定时任务{group_index+1}触发按键: {key}"
                    )
                    from modules.input import KeyEventExecutor
                    delay_min_var = group["delay_min"]
                    delay_max_var = group["delay_max"]
                    executor = KeyEventExecutor(
                        self.app.input_controller, delay_min_var, delay_max_var, self.PRIORITY
                    )
                    executor.execute_keypress(key)
                    self.app.logging_manager.log_message(
                        f"定时任务{group_index+1}按下了 {key} 键"
                    )
                else:
                    import platform
                    plat = platform.system()
                    self.app.logging_manager.log_message(
                        f"[{plat}] 定时任务{group_index+1}按键配置为空"
                    )
            except Exception as e:
                import platform
                plat = platform.system()
                self.app.logging_manager.error("TIMED",
                    f"[{plat}] 定时任务{group_index+1}错误: {str(e)}"
                )
                break

    def start_timed_position_selection(self, group_index, on_selected=None):
        self.app.logging_manager.log_message(
            f"开始定时组{group_index+1}屏幕位置选择..."
        )
        self.app.is_selecting = True
        self.app.current_timed_group = group_index
        self._pos_callback = on_selected

        from PySide6.QtWidgets import QWidget, QApplication
        from PySide6.QtCore import Qt, QTimer
        from PySide6.QtGui import QPainter, QColor, QPen

        class _ClickOverlay(QWidget):
            def __init__(self, module, group_idx):
                super().__init__()
                self.module = module
                self.group_idx = group_idx
                self.setWindowFlags(
                    Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
                )
                self.setAttribute(Qt.WA_TranslucentBackground)
                self.setCursor(Qt.CrossCursor)
                self.showFullScreen()

            def mousePressEvent(self, event):
                pos_x = int(event.globalX())
                pos_y = int(event.globalY())
                self.module._on_position_selected(self.group_idx, pos_x, pos_y)
                self.close()

            def keyPressEvent(self, event):
                if event.key() == Qt.Key_Escape:
                    self.module._cancel_selection()
                    self.close()

            def paintEvent(self, event):
                painter = QPainter(self)
                screen = QApplication.primaryScreen()
                geo = screen.geometry()
                painter.fillRect(geo, QColor(0, 0, 0, 80))
                painter.setPen(QPen(QColor(255, 255, 255), 2))
                painter.drawText(
                    geo, Qt.AlignCenter,
                    "点击选择点击位置 (按 Esc 取消)"
                )

        self._overlay = _ClickOverlay(self, group_index)

    def _on_position_selected(self, group_index, pos_x, pos_y):
        self.app.logging_manager.log_message(
            f"定时组{group_index+1}已选择位置: {pos_x},{pos_y}"
        )
        groups = getattr(self.app, 'timed_groups', [])
        if 0 <= group_index < len(groups):
            group = groups[group_index]
            group["position_x"].set(pos_x)
            group["position_y"].set(pos_y)
            group["position_var"].set(f"{pos_x},{pos_y}")
            if hasattr(self.app, 'save_config') and callable(self.app.save_config):
                try:
                    self.app.save_config()
                except Exception as e:
                    self.app.logging_manager.error("TIMED", f"保存定时配置失败: {e}")
        if hasattr(self, '_pos_callback') and self._pos_callback:
            try:
                self._pos_callback(pos_x, pos_y)
            except Exception as e:
                self.app.logging_manager.error("TIMED", f"位置回调失败: {e}")
            self._pos_callback = None
        self._cancel_selection()

    def _cancel_selection(self):
        if hasattr(self.app, 'cancel_selection') and callable(self.app.cancel_selection):
            try:
                self.app.cancel_selection()
            except Exception as e:
                self.app.logging_manager.error("TIMED", f"取消选择失败: {e}")
        self.app.is_selecting = False
