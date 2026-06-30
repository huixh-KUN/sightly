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
from core.async_utils import run_in_executor, create_async_thread
from utils.memory import MemoryMonitor


class ColorRecognitionWorker:
    """
    颜色识别类（异步协程版）
    优先级: 2 (Number=6 > Timed=5 > Image=4 > OCR=3 > Color=2 > Script=1)
    """

    PRIORITY = get_module_priority('color')

    def __init__(self, controller):
        self.controller = controller
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
        self.controller.logging_manager.debug("COLOR", f"颜色识别协程开始: 目标={self.target_color}, 容差={self.tolerance}, 间隔={self.interval}s")
        frame_count = 0
        try:
            while self.is_running:
                await asyncio.sleep(self.interval)
                self.controller.logging_manager.debug("COLOR", "开始颜色检测")
                matched = await run_in_executor(self.recognize_color)
                if matched:
                    self.controller.logging_manager.log_message("颜色匹配成功，执行命令")
                    await run_in_executor(self.execute_commands)
                    await asyncio.sleep(self.interval)
                else:
                    self.controller.logging_manager.debug("COLOR", "颜色未匹配")
                
                frame_count += 1
                if self.memory_monitor.gc_if_needed(frame_count):
                    self.controller.logging_manager.debug("COLOR", "触发 GC")
        except asyncio.CancelledError:
            self.controller.logging_manager.debug("COLOR", "颜色识别协程取消")
            self.is_running = False

    def recognize_color(self):
        if not self.region:
            self.controller.logging_manager.debug("COLOR", "recognize_color: 未设置识别区域")
            return False
        screenshot = None
        try:
            screenshot = self.screenshot_manager.get_region_screenshot(
                self.region, priority=self.PRIORITY)
            if not screenshot:
                self.controller.logging_manager.debug("COLOR", "recognize_color: 截图为空")
                return False
            if screenshot.size[0] == 0 or screenshot.size[1] == 0:
                self.controller.logging_manager.debug("COLOR", f"recognize_color: 截图尺寸为零 {screenshot.size}")
                return False
            self.controller.logging_manager.debug("COLOR", f"截图成功: {screenshot.size}, 区域={self.region}")
            current_hash = imagehash.average_hash(screenshot.resize((32, 32)))
            self.last_image_hash = current_hash
            matched, click_pos, match_pixels = ColorRecognizer.match_color(
                screenshot, self.target_color, self.tolerance,
                log_func=self.controller.logging_manager.log_message
            )
            self.controller.logging_manager.debug("COLOR", f"颜色匹配结果: matched={matched}, pixels={match_pixels}")
            if matched:
                self.controller.logging_manager.log_message(f"识别到目标颜色，匹配像素: {match_pixels}")
                return True
            return False
        except Exception as e:
            self.controller.logging_manager.error("COLOR", f"颜色识别错误: {str(e)}")
            import traceback
            self.controller.logging_manager.error("COLOR", f"错误详情: {traceback.format_exc()}")
            return False
        finally:
            if screenshot is not None:
                screenshot.close()
                del screenshot

    def execute_commands(self):
        if not self.commands:
            return
        from modules.script import ScriptWorker
        temp_executor = ScriptWorker(self.controller)
        temp_executor.run_script_once(self.commands)


class ColorRecognitionManager:
    """颜色识别管理器类（异步协程版）"""

    def __init__(self, controller):
        self.controller = controller
        self.color_recognition: Optional[ColorRecognitionWorker] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self.screenshot_manager = ScreenshotManager()

    def set_config(self, config):
        pass

    def collect_config(self):
        return {}

    def start(self):
        self.start_color_recognition()

    def stop(self):
        self.stop_color_recognition()

    def set_region(self, region):
        if not self.color_recognition:
            self.color_recognition = ColorRecognitionWorker(self.controller)
        self.color_recognition.set_region(region)
        self.controller.color_recognition_region = region

    def start_color_recognition(self):
        if not self.color_recognition:
            self.color_recognition = ColorRecognitionWorker(self.controller)
        try:
            if hasattr(self.controller, 'target_color') and self.controller.target_color:
                target_color = self.controller.target_color
            else:
                QMessageBox.warning(None, "警告", "请先选择目标颜色！")
                return
            tolerance = int(getattr(getattr(self.controller, 'tolerance_var', None), 'get', lambda: 10)())
            interval = float(getattr(getattr(self.controller, 'interval_var', None), 'get', lambda: 5.0)())
            commands = ""
            if hasattr(self.controller, 'color_commands'):
                try:
                    commands = self.controller.color_commands
                except Exception as e:
                    self.controller.logging_manager.error("COLOR", f"读取 color_commands 失败: {e}")
                    commands = ""
        except ValueError:
            QMessageBox.warning(None, "警告", "颜色设置参数格式错误，请检查！")
            return

        if not hasattr(self.controller, 'color_recognition_region') or not self.controller.color_recognition_region:
            QMessageBox.warning(None, "警告", "请先选择颜色识别区域！")
            return

        self.color_recognition.set_region(self.controller.color_recognition_region)
        self.color_recognition.start_recognition(target_color, tolerance, interval, commands)

        if self.color_recognition.is_running:
            self._thread, self._loop = create_async_thread(self._async_main)
            _set_status_text(self.controller, "颜色识别中...")

    async def _async_main(self):
        if self.color_recognition and self.color_recognition.is_running:
            t = asyncio.create_task(self.color_recognition._recognize_async())
            self.color_recognition._task = t
            try:
                await asyncio.gather(t, return_exceptions=True)
            except asyncio.CancelledError:
                pass

    def test_once(self) -> dict:
        if not self.color_recognition:
            self.color_recognition = ColorRecognitionWorker(self.controller)
        cr = self.color_recognition
        if not cr.region:
            return {"matched": False, "detail": "未设置识别区域"}
        if not cr.target_color:
            return {"matched": False, "detail": "未设置目标颜色"}
        matched = cr.recognize_color()
        r, g, b = cr.target_color
        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        if matched:
            return {"matched": True, "detail": f"检测到目标颜色 {hex_color}"}
        return {"matched": False, "detail": f"未检测到目标颜色 {hex_color}（容差 {cr.tolerance}）"}

    def stop_color_recognition(self):
        if self.color_recognition:
            self.color_recognition.stop_recognition()
        if self._loop and self._loop.is_running():
            for task in asyncio.all_tasks(loop=self._loop):
                if not task.done():
                    task.cancel()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)
        _set_status_text(self.controller, "颜色识别已停止")


def _set_status_text(app, text):
    if hasattr(app, 'status_label') and app.status_label:
        QTimer.singleShot(0, lambda: app.status_label.setText(text))
