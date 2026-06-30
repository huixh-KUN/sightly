import asyncio
import threading
import time
from collections import OrderedDict
from typing import Optional


from utils.screenshot import ScreenshotManager
from utils.recognition import NumberRecognizer
from utils.image import _preprocess_image
from core.priority_lock import get_module_priority
from core.async_utils import run_in_executor, create_async_thread
from utils.memory import MemoryMonitor


class _LRUCacheDict(OrderedDict):
    """有最大容量限制的 LRU 缓存字典"""
    def __init__(self, maxsize=200):
        super().__init__()
        self._maxsize = maxsize

    def __getitem__(self, key):
        value = super().__getitem__(key)
        self.move_to_end(key)
        return value

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        if len(self) > self._maxsize:
            self.popitem(last=False)


class NumberManager:
    """数字识别模块 - 优先级最高(6)"""

    PRIORITY = get_module_priority('number')

    def __init__(self, controller):
        self.controller = controller
        self.regions = []
        self.screenshot_manager = ScreenshotManager()
        self.memory_monitor = MemoryMonitor()
        self._last_results = {}
        self._number_cache = _LRUCacheDict(maxsize=200)
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None

    def set_config(self, config):
        self.regions = config if isinstance(config, list) else []

    def collect_config(self):
        return self.regions

    def start(self):
        self.start_number_recognition()

    def stop(self):
        self.stop_number_recognition()

    def start_number_recognition(self):
        groups = []
        regions = self.regions
        for i, rc in enumerate(regions):
            if not rc["enabled"]:
                continue
            region = rc["region"]
            if not region:
                continue
            try:
                threshold = int(rc["threshold"])
            except (ValueError, TypeError):
                threshold = 500
            try:
                confidence_threshold = float(rc.get("confidence_threshold", "0.3"))
            except (ValueError, TypeError):
                confidence_threshold = 0.3
            try:
                interval = float(rc["interval"])
            except (ValueError, TypeError):
                interval = 0
            try:
                cycle = rc["cycle_enabled"]
                if isinstance(cycle, str):
                    cycle = cycle.lower() in ("true", "1")
            except (KeyError, AttributeError):
                cycle = True
            groups.append({
                "index": i,
                "region": region,
                "threshold": threshold,
                "confidence_threshold": confidence_threshold,
                "interval": interval,
                "cycle_enabled": bool(cycle),
                "key": rc["key"],
                "alarm": rc["alarm"],
                "delay_min": rc["delay_min"],
                "delay_max": rc["delay_max"],
            })
        if not groups:
            return

        self._groups_data = groups
        self._thread, self._loop = create_async_thread(self._async_main)

    def stop_number_recognition(self):
        if self._loop and self._loop.is_running():
            for task in asyncio.all_tasks(loop=self._loop):
                if not task.done():
                    task.cancel()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)
        self._last_results.clear()
        self._number_cache.clear()

    async def _async_main(self):
        tasks = []
        for g in self._groups_data:
            t = asyncio.create_task(self._number_group_loop(g))
            tasks.append(t)
        if tasks:
            try:
                await asyncio.gather(*tasks, return_exceptions=True)
            except asyncio.CancelledError:
                pass

    async def _number_group_loop(self, g):
        self.controller.logging_manager.debug("NUMBER",
            f"数字识别组{g['index']+1} 协程开始: 阈值={g['threshold']}, "
            f"置信度={g['confidence_threshold']}, 循环={'开' if g['cycle_enabled'] else '关'}, "
            f"间隔={g['interval']}s")
        frame_count = 0
        try:
            while not (self._loop and self._loop.is_closed()):
                if not self._check_group_enabled(g["index"]):
                    self.controller.logging_manager.debug("NUMBER", f"数字识别组{g['index']+1} 已禁用，退出")
                    break
                try:
                    interval = g["interval"]
                    if interval <= 0:
                        import random
                        interval = random.uniform(0.25, 0.3)
                    await asyncio.sleep(interval)
                    self.controller.logging_manager.debug("NUMBER", f"数字识别组{g['index']+1} 截图")
                    screenshot = await run_in_executor(self.take_screenshot, g["region"])
                    if screenshot is None:
                        self.controller.logging_manager.debug("NUMBER", f"数字识别组{g['index']+1} 截图为空")
                        continue
                    self.controller.logging_manager.debug("NUMBER", f"数字识别组{g['index']+1} 开始OCR")
                    text = await run_in_executor(
                        self.ocr_number, screenshot, g["confidence_threshold"]
                    )
                    screenshot.close()
                    del screenshot
                    number = NumberRecognizer.parse_number(text, self._number_cache)
                    self.controller.logging_manager.debug("NUMBER",
                        f"数字识别组{g['index']+1} raw='{text}', parsed={number}")
                    if number is not None:
                        last = self._last_results.get(g["index"])
                        if number != last:
                            self.controller.logging_manager.log_message(
                                f"数字识别{g['index']+1}解析结果: {number}"
                            )
                            self._last_results[g["index"]] = number

                        if number < g["threshold"]:
                            self.controller.logging_manager.debug("NUMBER",
                                f"数字识别组{g['index']+1} 低于阈值 {g['threshold']}, 触发动作")
                            alarm = self._safe_get_alarm(g["index"])
                            if alarm:
                                await run_in_executor(self.controller.alarm_module.play_alarm_sound, alarm)
                            if g["key"]:
                                await run_in_executor(
                                    self._execute_keypress, g["key"], g["index"],
                                    g["delay_min"], g["delay_max"]
                                )
                    else:
                        last = self._last_results.get(g["index"])
                        if text != last:
                            self.controller.logging_manager.log_message(
                                f"数字识别{g['index']+1}结果: '{text}'"
                            )
                            self._last_results[g["index"]] = text
                    
                    if not g["cycle_enabled"]:
                        self.controller.logging_manager.debug("NUMBER", f"数字识别组{g['index']+1} 单次执行完成，退出")
                        break
                    frame_count += 1
                    if self.memory_monitor.gc_if_needed(frame_count):
                        self.controller.logging_manager.debug("NUMBER", f"数字识别组{g['index']+1} 触发 GC")
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    self.controller.logging_manager.error("NUMBER",
                        f"数字识别{g['index']+1}错误: {str(e)}"
                    )
                    await asyncio.sleep(5)
        except asyncio.CancelledError:
            self.controller.logging_manager.debug("NUMBER", f"数字识别组{g['index']+1} 协程取消")

    def _check_group_enabled(self, index):
        regions = self.regions
        if index >= len(regions):
            return False
        try:
            return bool(regions[index]["enabled"])
        except Exception as e:
            self.controller.logging_manager.error("NUMBER", f"_check_region_enabled 失败: {e}")
            return False

    def _safe_get_alarm(self, index):
        regions = self.regions
        if index < len(regions):
            try:
                return regions[index]["alarm"]
            except Exception as e:
                self.controller.logging_manager.error("NUMBER", f"_safe_get_alarm 失败: {e}")
        return False

    def _execute_keypress(self, key, group_index, delay_min, delay_max):
        self.controller.logging_manager.log_message(
            f"数字识别{group_index+1}触发按键: {key}"
        )
        from modules.key_event_worker import KeyEventWorker
        executor = KeyEventWorker(
            self.controller.input_controller, delay_min, delay_max, self.PRIORITY
        )
        executor.execute_keypress(key)
        self.controller.logging_manager.log_message(
            f"数字识别{group_index+1}按下了 {key} 键，"
            f"按住时长范围: {delay_min}-{delay_max} 毫秒"
        )

    def test_group(self, index) -> dict:
        regions = self.regions
        if index >= len(regions):
            return {"matched": False, "executed": False, "detail": "组索引越界"}
        rc = regions[index]
        region = rc.get("region")
        if not region:
            return {"matched": False, "executed": False, "detail": "未设置识别区域"}
        try:
            confidence = float(rc.get("confidence_threshold", "0.3"))
        except Exception as e:
            self.controller.logging_manager.error("NUMBER", f"置信度阈值转换失败: {e}")
            confidence = 0.3
        screenshot = self.take_screenshot(region)
        if screenshot is None:
            return {"matched": False, "executed": False, "detail": "截图失败"}
        try:
            text = self.ocr_number(screenshot, confidence)
            number = NumberRecognizer.parse_number(text, self._number_cache)
            if number is not None:
                try:
                    threshold = int(rc["threshold"])
                except (ValueError, TypeError, KeyError, AttributeError):
                    threshold = 500
                will_trigger = number < threshold
                hint = "运行时将触发" if will_trigger else "运行时不触发"
                detail = f"当前数值: {number}（{hint}，阈值 {threshold}）"
                return {"matched": True, "executed": False, "detail": detail}
            return {"matched": False, "executed": False, "detail": f"识别文本: '{text}'（无法解析为数字）"}
        finally:
            screenshot.close()
            del screenshot

    def take_screenshot(self, region):
        try:
            return self.screenshot_manager.get_region_screenshot(
                region, priority=self.PRIORITY
            )
        except Exception as e:
            self.controller.logging_manager.error("NUMBER",
                f"数字识别错误: 屏幕截图失败 - {str(e)}"
            )
            return None

    def ocr_number(self, image, confidence_threshold=0.0):
        processed_image = _preprocess_image(image, group_index=None)
        if processed_image is None:
            processed_image = image.convert('L')
        try:
            return NumberRecognizer.recognize(processed_image,
                                              confidence_threshold=confidence_threshold)
        finally:
            if processed_image is not None:
                processed_image.close()
                del processed_image
