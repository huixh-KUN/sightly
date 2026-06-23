import asyncio
import threading
import time
from typing import Optional


from core.priority_lock import get_module_priority
from core.click_handler import ClickHandler
from core.config import ConfigVar
from core.async_utils import run_in_executor


def _get_val(v, default=None):
    """兼容 ConfigVar 和纯类型，安全取值"""
    if hasattr(v, 'get'):
        return v.get()
    return v if v is not None else default


class TimedModule:
    """
    定时任务模块
    优先级: 5 (Number=6 > Timed=5 > Image=4 > OCR=3 > Color=2 > Script=1)
    """

    PRIORITY = get_module_priority('timed')

    def __init__(self, app):
        self.app = app
        self.click_handler = ClickHandler(app)
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None

    def start_timed_tasks(self):
        groups = []
        app_groups = getattr(self.app, 'timed_groups', [])
        self.app.logging_manager.debug("TIMED", f"开始定时任务: 共 {len(app_groups)} 组")
        for i, g in enumerate(app_groups):
            enabled = _get_val(g["enabled"])
            self.app.logging_manager.debug("TIMED", f"  组{i+1}: enabled={enabled}")
            if not enabled:
                continue
            try:
                interval = int(_get_val(g["interval"]))
            except (ValueError, TypeError):
                interval = 10
            gd = {
                "index": i,
                "interval": interval,
                "key": _get_val(g["key"]),
                "alarm": _get_val(g["alarm"]),
                "click_enabled": _get_val(g["click_enabled"]),
                "pos_x": int(_get_val(g["position_x"], 0)),
                "pos_y": int(_get_val(g["position_y"], 0)),
                "click_offset": int(_get_val(g.get("click_offset"), 0)),
                "delay_min": int(_get_val(g["delay_min"], 100)),
                "delay_max": int(_get_val(g["delay_max"], 200)),
            }
            self.app.logging_manager.debug("TIMED",
                f"  组{i+1} 已启用: interval={interval}s, key={gd['key']!r}, "
                f"click=({gd['pos_x']},{gd['pos_y']}), alarm={gd['alarm']}")
            groups.append(gd)
        if not groups:
            self.app.logging_manager.debug("TIMED", "无启用的定时组")
            return

        self._groups_data = groups
        self._thread = threading.Thread(target=self._run_async, daemon=True)
        self._thread.start()

    def stop_timed_tasks(self):
        if self._loop and self._loop.is_running():
            for task in asyncio.all_tasks(loop=self._loop):
                if not task.done():
                    task.cancel()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)

    def _run_async(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._loop = loop
        try:
            loop.run_until_complete(self._async_main())
        finally:
            loop.close()
            self._loop = None

    async def _async_main(self):
        tasks = []
        for g in self._groups_data:
            t = asyncio.create_task(self._timed_group_loop(g))
            tasks.append(t)
        if tasks:
            try:
                await asyncio.gather(*tasks, return_exceptions=True)
            except asyncio.CancelledError:
                pass

    async def _timed_group_loop(self, g):
        self.app.logging_manager.debug("TIMED",
            f"定时组{g['index']+1} 协程开始: 间隔={g['interval']}s, "
            f"key={g['key']!r}, click=({g['pos_x']},{g['pos_y']})")
        try:
            while not (self._loop and self._loop.is_closed()):
                if not self._check_group_enabled(g["index"]):
                    self.app.logging_manager.debug("TIMED", f"定时组{g['index']+1} 已禁用，退出")
                    break
                try:
                    for _ in range(g["interval"]):
                        await asyncio.sleep(1)
                        if self._loop and self._loop.is_closed():
                            return
                    if self._loop and self._loop.is_closed():
                        return

                    self.app.logging_manager.debug("TIMED", f"定时组{g['index']+1} 触发执行")

                    # 报警
                    if g["alarm"]:
                        self.app.logging_manager.debug("TIMED", f"定时组{g['index']+1} 播放报警")
                        await run_in_executor(self.app.alarm_module.play_alarm_sound, g["alarm"])

                    # 鼠标点击
                    if g["click_enabled"] and g["pos_x"] != 0 and g["pos_y"] != 0:
                        self.app.logging_manager.debug("TIMED",
                            f"定时组{g['index']+1} 鼠标点击 ({g['pos_x']},{g['pos_y']})")
                        await run_in_executor(
                            self.click_handler.execute_click,
                            x=g["pos_x"], y=g["pos_y"], priority=self.PRIORITY,
                            module_name="定时任务", index=g["index"], delay=0.5,
                            offset_range=g["click_offset"]
                        )

                    # 按键
                    if g["key"]:
                        import platform
                        plat = platform.system()
                        self.app.logging_manager.log_message(
                            f"[{plat}] 定时任务{g['index']+1}触发按键: {g['key']}"
                        )
                        await run_in_executor(
                            self._execute_keypress, g["key"], g["index"],
                            g["delay_min"], g["delay_max"]
                        )
                    else:
                        import platform
                        plat = platform.system()
                        self.app.logging_manager.debug("TIMED",
                            f"定时组{g['index']+1} 按键配置为空")
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    import platform
                    plat = platform.system()
                    self.app.logging_manager.error("TIMED",
                        f"[{plat}] 定时任务{g['index']+1}错误: {str(e)}"
                    )
                    await asyncio.sleep(5)
        except asyncio.CancelledError:
            self.app.logging_manager.debug("TIMED", f"定时组{g['index']+1} 协程取消")

    def _check_group_enabled(self, index):
        groups = getattr(self.app, 'timed_groups', [])
        if index >= len(groups):
            return False
        try:
            return bool(groups[index]["enabled"].get())
        except Exception:
            return False

    def _execute_keypress(self, key, group_index, delay_min, delay_max):
        from modules.input import KeyEventExecutor
        delay_min_var = type("", (), {"get": lambda: str(delay_min)})()
        delay_max_var = type("", (), {"get": lambda: str(delay_max)})()
        executor = KeyEventExecutor(
            self.app.input_controller, delay_min_var, delay_max_var, self.PRIORITY
        )
        executor.execute_keypress(key)
        self.app.logging_manager.log_message(
            f"定时任务{group_index+1}按下了 {key} 键"
        )

    def start_timed_position_selection(self, group_index, on_selected=None):
        self.app.logging_manager.log_message(
            f"开始定时组{group_index+1}屏幕位置选择..."
        )
        self.app.is_selecting = True
        self.app.current_timed_group = group_index
        self._pos_callback = on_selected

        from PySide6.QtWidgets import QWidget, QApplication
        from PySide6.QtCore import Qt, QRect
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

            @staticmethod
            def _physical_pos(logical_x, logical_y):
                screens = QApplication.screens()
                for s in screens:
                    geo = s.geometry()
                    if geo.contains(logical_x, logical_y):
                        scale = s.devicePixelRatio()
                        return int(logical_x * scale), int(logical_y * scale)
                return logical_x, logical_y

            def mousePressEvent(self, event):
                pos_x, pos_y = self._physical_pos(int(event.globalX()), int(event.globalY()))
                self.module._on_position_selected(self.group_idx, pos_x, pos_y)
                self.close()

            def keyPressEvent(self, event):
                if event.key() == Qt.Key_Escape:
                    self.module._cancel_selection()
                    self.close()

            def paintEvent(self, event):
                painter = QPainter(self)
                # 覆盖整个虚拟桌面
                vd = QRect()
                for s in QApplication.screens():
                    geo = s.geometry()
                    vd = vd.united(geo)
                if vd.isNull():
                    vd = QApplication.primaryScreen().geometry()
                painter.fillRect(vd, QColor(0, 0, 0, 80))
                painter.setPen(QPen(QColor(255, 255, 255), 2))
                painter.drawText(
                    vd, Qt.AlignCenter,
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
            if "position_var" in group:
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
