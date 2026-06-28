import asyncio
import threading
import time
import os
from typing import Optional

import numpy as np

from PySide6.QtWidgets import QMessageBox, QFileDialog
from PySide6.QtCore import Qt, QTimer

from core.config import safe_group_get
from core.async_utils import run_in_executor, create_async_thread

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

from utils.screenshot import ScreenshotManager
from utils.recognition import ImageRecognizer
from core.click_handler import ClickHandler
from core.priority_lock import get_module_priority
from utils.memory import MemoryMonitor


class ImageDetection:
    """
    图像检测类 - 使用模板匹配（异步协程版）
    优先级: 4 (Number=6 > Timed=5 > Image=4 > OCR=3 > Color=2 > Script=1)
    """

    PRIORITY = get_module_priority('image')

    def __init__(self, app, group_index=0):
        self.app = app
        self.group_index = group_index
        self.is_running = False
        self._task = None
        self.region = None
        self.template_image = None
        self.template_path = None
        self.threshold = 0.8
        self.interval = 5.0
        self.pause = 180
        self.cycle_enabled = True
        self.commands = ""
        self.click_handler = ClickHandler(app)
        self.last_trigger_time = 0
        self.last_match_pos = None
        self.screenshot_manager = ScreenshotManager()
        self.memory_monitor = MemoryMonitor()

    def set_region(self, region):
        self.region = region

    def start_detection(self, threshold, interval, pause, commands, cycle_enabled=True):
        self.threshold = float(threshold) / 100.0
        self.interval = float(interval)
        self.pause = int(pause)
        self.cycle_enabled = cycle_enabled
        self.commands = commands
        self.last_trigger_time = 0

        if not CV2_AVAILABLE:
            self.app.logging_manager.debug("IMAGE", f"检测组{self.group_index+1} 启动失败: OpenCV 不可用")
            return
        if self.template_image is None:
            self.app.logging_manager.debug("IMAGE", f"检测组{self.group_index+1} 启动失败: 未设置模板图像")
            return
        if not self.region:
            self.app.logging_manager.debug("IMAGE", f"检测组{self.group_index+1} 启动失败: 未设置检测区域")
            return

        self.is_running = True
        self.app.logging_manager.debug("IMAGE",
            f"检测组{self.group_index+1} 启动: 阈值={self.threshold:.2f}, "
            f"间隔={self.interval}s, 暂停={self.pause}s, 模板={self.template_path}")

    def stop_detection(self):
        self.is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
            self._task = None

    async def _detect_async(self):
        """异步检测循环"""
        self.app.logging_manager.debug("IMAGE",
            f"检测组{self.group_index+1} 协程开始: 间隔={self.interval}s, "
            f"循环={'开' if self.cycle_enabled else '关'}")
        frame_count = 0
        try:
            while self.is_running:
                interval = self.interval
                if interval <= 0:
                    import random
                    interval = random.uniform(0.25, 0.3)
                await asyncio.sleep(interval)
                self.app.logging_manager.debug("IMAGE",
                    f"检测组{self.group_index+1} 开始检测循环")
                match_result = await run_in_executor(self.detect_image)
                if match_result:
                    abs_x, abs_y, score = match_result
                    self.app.logging_manager.log_message(
                        f"检测组{self.group_index+1} 匹配成功: 位置=({abs_x},{abs_y}), 得分={score:.3f}")
                    await run_in_executor(self.execute_commands, match_result)
                    self.last_trigger_time = time.time()
                    await asyncio.sleep(5)
                else:
                    self.app.logging_manager.debug("IMAGE",
                        f"检测组{self.group_index+1} 未匹配")

                if not self.cycle_enabled:
                    self.app.logging_manager.debug("IMAGE", f"检测组{self.group_index+1} 单次执行完成，退出")
                    break
                frame_count += 1
                if self.memory_monitor.gc_if_needed(frame_count):
                    self.app.logging_manager.debug("IMAGE", f"检测组{self.group_index+1} 触发 GC")
        except asyncio.CancelledError:
            self.app.logging_manager.debug("IMAGE", f"检测组{self.group_index+1} 协程取消")
            self.is_running = False

    def detect_image(self):
        if not self.region:
            self.app.logging_manager.debug("IMAGE", f"检测组{self.group_index+1} detect_image: 无区域")
            return None
        if self.template_image is None:
            self.app.logging_manager.debug("IMAGE", f"检测组{self.group_index+1} detect_image: 无模板")
            return None
        if not CV2_AVAILABLE:
            self.app.logging_manager.debug("IMAGE", f"检测组{self.group_index+1} detect_image: OpenCV 不可用")
            return None
        screenshot = None
        try:
            screenshot = self.screenshot_manager.get_region_screenshot(
                self.region, priority=self.PRIORITY)
            if not screenshot:
                self.app.logging_manager.debug("IMAGE", f"检测组{self.group_index+1} 截图为空")
                return None
            if screenshot.size[0] == 0 or screenshot.size[1] == 0:
                self.app.logging_manager.debug("IMAGE", f"检测组{self.group_index+1} 截图尺寸为零: {screenshot.size}")
                return None
            self.app.logging_manager.debug("IMAGE",
                f"检测组{self.group_index+1} 截图成功: {screenshot.size}, "
                f"区域={self.region}, 阈值={self.threshold:.2f}")
            matched, click_pos, score = ImageRecognizer.match_template(
                screenshot, self.template_image, self.threshold,
                log_func=self.app.logging_manager.log_message,
                group_index=self.group_index
            )
            self.app.logging_manager.debug("IMAGE",
                f"检测组{self.group_index+1} 匹配结果: matched={matched}, "
                f"click_pos={click_pos}, score={score}")
            if matched and click_pos:
                abs_x = self.region[0] + click_pos[0]
                abs_y = self.region[1] + click_pos[1]
                self.last_match_pos = (abs_x, abs_y)
                return (abs_x, abs_y, score)
            return None
        except Exception as e:
            self.app.logging_manager.error("IMAGE", f"图像检测失败: {e}")
            import traceback
            self.app.logging_manager.error("IMAGE", f"错误详情: {traceback.format_exc()}")
            return None
        finally:
            if screenshot is not None:
                screenshot.close()
                del screenshot

    def execute_commands(self, match_result, *, for_test=False):
        if not match_result:
            return
        if not for_test and (not self.app.is_running or getattr(self.app, 'system_stopped', False)):
            return

        abs_x, abs_y, match_score = match_result
        group = None
        if hasattr(self.app, 'image_groups') and self.group_index < len(self.app.image_groups):
            group = self.app.image_groups[self.group_index]
        if not group:
            return

        key = safe_group_get(group, "key", "")
        alarm_enabled = safe_group_get(group, "alarm", False)
        click_enabled = safe_group_get(group, "click", True)

        if click_enabled:
            offset_range = int(safe_group_get(group, "click_offset", "0"))
            self.click_handler.execute_click(
                x=abs_x, y=abs_y, priority=self.PRIORITY,
                module_name="检测组", index=self.group_index,
                offset_range=offset_range, for_test=for_test
            )

        if key:
            from modules.input import KeyEventExecutor
            delay_min = int(safe_group_get(group, "delay_min", 300))
            delay_max = int(safe_group_get(group, "delay_max", 500))
            executor = KeyEventExecutor(
                self.app.input_controller, delay_min, delay_max, self.PRIORITY)
            executor.execute_keypress(key)
            self.app.logging_manager.log_message(f"检测组{self.group_index+1}按下了 {key} 键")

        if alarm_enabled:
            try:
                self.app.alarm_module.play_alarm_sound(True)
            except Exception as e:
                self.app.logging_manager.error("IMAGE", f"播放报警声音失败: {e}")

        if self.commands:
            from modules.script import ScriptExecutor
            temp_executor = ScriptExecutor(self.app)
            temp_executor.run_script_once(self.commands)


class ImageDetectionManager:
    """图像检测管理器类（异步协程版）"""

    def __init__(self, app):
        self.app = app
        self.image_detections: dict[int, ImageDetection] = {}
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None

    def select_region(self, group_index):
        from utils.region import _start_selection
        _start_selection(self.app, "image", group_index)

    def select_reference_image(self, group_index):
        file_path, _ = QFileDialog.getOpenFileName(
            None, "选择参考图像（模板）",
            "", "图像文件 (*.png *.jpg *.jpeg *.bmp *.gif);;所有文件 (*.*)"
        )
        if not file_path:
            return
        if group_index >= len(getattr(self.app, 'image_groups', [])):
            return
        group = self.app.image_groups[group_index]
        try:
            if not CV2_AVAILABLE:
                QMessageBox.warning(None, "错误", "OpenCV未安装，无法使用图像检测功能")
                return
            template = cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), cv2.IMREAD_COLOR)
            if template is None:
                QMessageBox.warning(None, "错误", f"无法读取图像文件: {file_path}")
                return
            group["template_image"] = template
            group["reference_image"] = file_path
            if "image_preview" in group and group["image_preview"]:
                self._update_image_preview(group, file_path)
        except Exception as e:
            QMessageBox.warning(None, "错误", f"加载图像失败: {str(e)}")

    def _update_image_preview(self, group, image_path):
        try:
            if "image_preview" in group and group["image_preview"]:
                from PySide6.QtGui import QPixmap
                from PySide6.QtWidgets import QLabel
                pixmap = QPixmap(image_path)
                preview = group["image_preview"]
                if isinstance(preview, QLabel):
                    preview.setPixmap(pixmap.scaled(60, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        except Exception as e:
            self.app.logging_manager.error("IMAGE", f"更新图像预览失败: {e}")

    def _safe_get(self, group, key, default=None):
        return group.get(key, default)

    def start_detection(self, group_index):
        groups = getattr(self.app, 'image_groups', [])
        if group_index >= len(groups):
            self.app.logging_manager.debug("IMAGE", f"检测组{group_index+1} 启动: 组索引越界")
            return
        group = groups[group_index]
        if not self._safe_get(group, "enabled", False):
            self.app.logging_manager.debug("IMAGE", f"检测组{group_index+1} 启动: 未启用")
            return
        if group.get("template_image") is None:
            ref_path = self._safe_get(group, "reference_image", "")
            if ref_path and CV2_AVAILABLE and os.path.exists(ref_path):
                template = cv2.imdecode(np.fromfile(ref_path, dtype=np.uint8), cv2.IMREAD_COLOR)
                if template is not None:
                    group["template_image"] = template
                    self.app.logging_manager.debug("IMAGE",
                        f"检测组{group_index+1} 从路径加载模板: {ref_path}")
                else:
                    self.app.logging_manager.debug("IMAGE",
                        f"检测组{group_index+1} 启动: 无法加载参考图像 {ref_path}")
                    return
            else:
                self.app.logging_manager.debug("IMAGE", f"检测组{group_index+1} 启动: 未设置参考图像")
                return
        region = self._safe_get(group, "region")
        if not region:
            self.app.logging_manager.debug("IMAGE", f"检测组{group_index+1} 启动: 未设置检测区域")
            return
        if group_index not in self.image_detections:
            self.image_detections[group_index] = ImageDetection(self.app, group_index)
        detection = self.image_detections[group_index]
        detection.set_region(region)
        detection.template_image = group["template_image"]
        detection.template_path = self._safe_get(group, "reference_image", "")
        threshold = self._safe_get(group, "threshold", "80")
        interval = self._safe_get(group, "interval", "5")
        pause = self._safe_get(group, "pause", "180")
        commands = group.get("commands", "")
        cycle = self._safe_get(group, "cycle_enabled", True)
        if isinstance(cycle, str):
            cycle = cycle.lower() in ("true", "1")
        detection.start_detection(threshold, interval, pause, commands, cycle_enabled=bool(cycle))
        _set_status_text(self.app, f"图像检测组{group_index + 1}运行中...")

    def stop_detection(self, group_index):
        if group_index in self.image_detections:
            self.image_detections[group_index].stop_detection()
            del self.image_detections[group_index]
        _set_status_text(self.app, "图像检测已停止")

    def start_all_detection(self):
        has_enabled = False
        for group in getattr(self.app, 'image_groups', []):
            if self._safe_get(group, "enabled", False):
                has_enabled = True
                break
        if not has_enabled:
            QMessageBox.warning(None, "警告", "请至少启用一个检测组")
            return

        started = 0
        for i, group in enumerate(getattr(self.app, 'image_groups', [])):
            if self._safe_get(group, "enabled", False):
                if not self._safe_get(group, "region"):
                    self.app.logging_manager.debug("IMAGE", f"检测组{i+1} 跳过: 无区域")
                    continue
                self.start_detection(i)
                started += 1

        self.app.logging_manager.debug("IMAGE", f"start_all_detection: 启动了 {started} 组")

        if self.image_detections:
            self._thread, self._loop = create_async_thread(self._async_main)

    async def _async_main(self):
        tasks = []
        for det in self.image_detections.values():
            if det.is_running:
                t = asyncio.create_task(det._detect_async())
                det._task = t
                tasks.append(t)
        if tasks:
            try:
                await asyncio.gather(*tasks, return_exceptions=True)
            except asyncio.CancelledError:
                pass

    def test_group(self, index) -> dict:
        groups = getattr(self.app, 'image_groups', [])
        if index >= len(groups):
            return {"matched": False, "executed": False, "detail": "组索引越界"}
        group = groups[index]
        if not self._safe_get(group, "region"):
            return {"matched": False, "executed": False, "detail": "未设置检测区域"}
        template = self._safe_get(group, "template_image")
        if template is not None:
            pass
        else:
            ref = self._safe_get(group, "reference_image", "")
            if ref and CV2_AVAILABLE and os.path.exists(ref):
                template = cv2.imdecode(np.fromfile(ref, dtype=np.uint8), cv2.IMREAD_COLOR)
                if template is None:
                    return {"matched": False, "executed": False, "detail": f"无法加载模板图片: {ref}"}
            else:
                return {"matched": False, "executed": False, "detail": "未设置模板图片"}
        threshold = float(self._safe_get(group, "threshold", "80")) / 100.0
        det = ImageDetection(self.app, index)
        det.set_region(self._safe_get(group, "region"))
        det.template_image = template
        det.threshold = threshold
        result = det.detect_image()
        if not result:
            return {"matched": False, "executed": False, "detail": "未匹配到模板"}
        abs_x, abs_y, score = result
        det.execute_commands(result, for_test=True)
        return {
            "matched": True,
            "executed": True,
            "detail": f"匹配成功，置信度 {score:.1%}；已按配置执行动作",
        }

    def stop_all_detection(self):
        for det in self.image_detections.values():
            det.stop_detection()
        if self._loop and self._loop.is_running():
            for task in asyncio.all_tasks(loop=self._loop):
                if not task.done():
                    task.cancel()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)
        self.image_detections.clear()
        _set_status_text(self.app, "图像检测已停止")


def _set_status_text(app, text):
    if hasattr(app, 'status_label') and app.status_label:
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, lambda: app.status_label.setText(text))
