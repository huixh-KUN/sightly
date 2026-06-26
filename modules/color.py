import asyncio
import threading
import time
from typing import Optional

import numpy as np
import imagehash

from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import QTimer

from utils.screenshot import ScreenshotManager
from utils.recognition import ColorRecognizer
from core.priority_lock import get_module_priority
from core.async_utils import run_in_executor
from utils.memory import MemoryMonitor


class ColorRecognition:
    """
    颜色识别类（异步协程版）
    优先级: 2 (Number=6 > Timed=5 > Image=4 > OCR=3 > Color=2 > Script=1)
    """

    PRIORITY = get_module_priority('color')

    def __init__(self, app):
        self.app = app
        self.is_running = False
        self._task = None
        self.region = None
        self.target_color = None
        self.tolerance = 10
        self.interval = 5.0
        self.commands = ""

        self.last_image_hash = None
        self.screenshot_manager = ScreenshotManager()
        self.memory_monitor = MemoryMonitor()

    def set_region(self, region):
        self.region = region

    def start_recognition(self, target_color, tolerance, interval, commands):
        self.target_color = target_color
        self.tolerance = int(tolerance)
        self.interval = float(interval)
        self.commands = commands
        self.is_running = True

    def stop_recognition(self):
        self.is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
            self._task = None

    async def _recognize_async(self):
        """异步颜色识别循环"""
        self.app.logging_manager.debug("COLOR", f"颜色识别协程开始: 目标={self.target_color}, 容差={self.tolerance}, 间隔={self.interval}s")
        frame_count = 0
        try:
            while self.is_running:
                await asyncio.sleep(self.interval)
                self.app.logging_manager.debug("COLOR", "开始颜色检测")
                matched = await run_in_executor(self.recognize_color)
                if matched:
                    self.app.logging_manager.log_message("颜色匹配成功，执行命令")
                    await run_in_executor(self.execute_commands)
                    await asyncio.sleep(self.interval)
                else:
                    self.app.logging_manager.debug("COLOR", "颜色未匹配")
                
                frame_count += 1
                if self.memory_monitor.gc_if_needed(frame_count):
                    self.app.logging_manager.debug("COLOR", "触发 GC")
        except asyncio.CancelledError:
            self.app.logging_manager.debug("COLOR", "颜色识别协程取消")
            self.is_running = False

    def recognize_color(self):
        if not self.region:
            self.app.logging_manager.debug("COLOR", "recognize_color: 未设置识别区域")
            return False
        screenshot = None
        try:
            screenshot = self.screenshot_manager.get_region_screenshot(
                self.region, priority=self.PRIORITY)
            if not screenshot:
                self.app.logging_manager.debug("COLOR", "recognize_color: 截图为空")
                return False
            if screenshot.size[0] == 0 or screenshot.size[1] == 0:
                self.app.logging_manager.debug("COLOR", f"recognize_color: 截图尺寸为零 {screenshot.size}")
                return False
            self.app.logging_manager.debug("COLOR", f"截图成功: {screenshot.size}, 区域={self.region}")
            current_hash = imagehash.average_hash(screenshot.resize((32, 32)))
            self.last_image_hash = current_hash
            matched, click_pos, match_pixels = ColorRecognizer.match_color(
                screenshot, self.target_color, self.tolerance,
                log_func=self.app.logging_manager.log_message
            )
            self.app.logging_manager.debug("COLOR", f"颜色匹配结果: matched={matched}, pixels={match_pixels}")
            if matched:
                self.app.logging_manager.log_message(f"识别到目标颜色，匹配像素: {match_pixels}")
                return True
            return False
        except Exception as e:
            self.app.logging_manager.error("COLOR", f"颜色识别错误: {str(e)}")
            import traceback
            self.app.logging_manager.error("COLOR", f"错误详情: {traceback.format_exc()}")
            return False
        finally:
            if screenshot is not None:
                screenshot.close()
                del screenshot

    def execute_commands(self):
        if not self.commands:
            return
        from modules.script import ScriptExecutor
        temp_executor = ScriptExecutor(self.app)
        temp_executor.run_script_once(self.commands)


class ColorRecognitionManager:
    """颜色识别管理器类（异步协程版）"""

    def __init__(self, app):
        self.app = app
        self.color_recognition: Optional[ColorRecognition] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self.screenshot_manager = ScreenshotManager()

    def select_color_region(self):
        self.app.logging_manager.log_message("开始选择颜色识别区域...")
        from utils.region import _start_selection
        _start_selection(self.app, "color", 0)

    def select_color(self):
        def on_color_selected(color):
            r, g, b = color
            self.app.target_color = color
            if hasattr(self.app, 'color_var'):
                self.app.color_var.set(f"RGB({r}, {g}, {b})")
            if hasattr(self.app, 'color_display'):
                try:
                    color_hex = f"#{r:02x}{g:02x}{b:02x}"
                    self.app.color_display.setStyleSheet(f"background-color: {color_hex}; border-radius: 4px;")
                except Exception as e:
                    self.app.logging_manager.error("COLOR", f"更新颜色显示失败: {e}")

    def start_color_recognition(self):
        if not self.color_recognition:
            self.color_recognition = ColorRecognition(self.app)
        try:
            if hasattr(self.app, 'target_color') and self.app.target_color:
                target_color = self.app.target_color
            else:
                QMessageBox.warning(None, "警告", "请先选择目标颜色！")
                return
            tolerance = int(getattr(getattr(self.app, 'tolerance_var', None), 'get', lambda: 10)())
            interval = float(getattr(getattr(self.app, 'interval_var', None), 'get', lambda: 5.0)())
            commands = ""
            if hasattr(self.app, 'color_commands'):
                try:
                    commands = self.app.color_commands
                except Exception:
                    commands = ""
        except ValueError:
            QMessageBox.warning(None, "警告", "颜色设置参数格式错误，请检查！")
            return

        if not hasattr(self.app, 'color_recognition_region') or not self.app.color_recognition_region:
            QMessageBox.warning(None, "警告", "请先选择颜色识别区域！")
            return

        self.color_recognition.set_region(self.app.color_recognition_region)
        self.color_recognition.start_recognition(target_color, tolerance, interval, commands)

        if self.color_recognition.is_running:
            self._thread = threading.Thread(target=self._run_async, daemon=True)
            self._thread.start()
            _set_status_text(self.app, "颜色识别中...")

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
        if self.color_recognition and self.color_recognition.is_running:
            t = asyncio.create_task(self.color_recognition._recognize_async())
            self.color_recognition._task = t
            try:
                await asyncio.gather(t, return_exceptions=True)
            except asyncio.CancelledError:
                pass

    def stop_color_recognition(self):
        if self.color_recognition:
            self.color_recognition.stop_recognition()
        if self._loop and self._loop.is_running():
            for task in asyncio.all_tasks(loop=self._loop):
                if not task.done():
                    task.cancel()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)
        _set_status_text(self.app, "颜色识别已停止")


def _set_status_text(app, text):
    if hasattr(app, 'status_label') and app.status_label:
        QTimer.singleShot(0, lambda: app.status_label.setText(text))
