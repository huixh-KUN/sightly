import asyncio
import threading
import time
from collections import OrderedDict
from typing import Optional


from utils.screenshot import ScreenshotManager
from utils.recognition import NumberRecognizer
from utils.image import _preprocess_image
from core.priority_lock import get_module_priority
from core.async_utils import run_in_executor


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


class NumberModule:
    """数字识别模块 - 优先级最高(6)"""

    PRIORITY = get_module_priority('number')

    def __init__(self, app):
        self.app = app
        self.screenshot_manager = ScreenshotManager()
        self._last_results = {}
        self._number_cache = _LRUCacheDict(maxsize=200)
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None

    def start_number_recognition(self):
        groups = []
        regions = getattr(self.app, 'number_regions', [])
        for i, rc in enumerate(regions):
            if not rc["enabled"].get():
                continue
            region = rc["region"]
            if not region:
                continue
            try:
                threshold = int(rc["threshold"].get())
            except (ValueError, TypeError):
                threshold = 500
            try:
                conf = rc.get("confidence_threshold")
                confidence_threshold = float(conf.get())
            except (ValueError, TypeError, KeyError, AttributeError):
                confidence_threshold = 0.3
            groups.append({
                "index": i,
                "region": region,
                "threshold": threshold,
                "confidence_threshold": confidence_threshold,
                "key": rc["key"].get(),
                "alarm": rc["alarm"].get(),
                "delay_min": rc["delay_min"].get(),
                "delay_max": rc["delay_max"].get(),
            })
        if not groups:
            return

        self._groups_data = groups
        self._thread = threading.Thread(target=self._run_async, daemon=True)
        self._thread.start()

    def stop_number_recognition(self):
        if self._loop and self._loop.is_running():
            for task in asyncio.all_tasks(loop=self._loop):
                if not task.done():
                    task.cancel()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)
        self._last_results.clear()
        self._number_cache.clear()

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
            t = asyncio.create_task(self._number_group_loop(g))
            tasks.append(t)
        if tasks:
            try:
                await asyncio.gather(*tasks, return_exceptions=True)
            except asyncio.CancelledError:
                pass

    async def _number_group_loop(self, g):
        self.app.logging_manager.debug("NUMBER",
            f"数字识别组{g['index']+1} 协程开始: 阈值={g['threshold']}, "
            f"置信度={g['confidence_threshold']}, key={g['key']!r}")
        try:
            while not (self._loop and self._loop.is_closed()):
                if not self._check_group_enabled(g["index"]):
                    self.app.logging_manager.debug("NUMBER", f"数字识别组{g['index']+1} 已禁用，退出")
                    break
                try:
                    await asyncio.sleep(1)
                    self.app.logging_manager.debug("NUMBER", f"数字识别组{g['index']+1} 截图")
                    screenshot = await run_in_executor(self.take_screenshot, g["region"])
                    if screenshot is None:
                        self.app.logging_manager.debug("NUMBER", f"数字识别组{g['index']+1} 截图为空")
                        continue
                    self.app.logging_manager.debug("NUMBER", f"数字识别组{g['index']+1} 开始OCR")
                    text = await run_in_executor(
                        self.ocr_number, screenshot, g["confidence_threshold"]
                    )
                    number = NumberRecognizer.parse_number(text, self._number_cache)
                    self.app.logging_manager.debug("NUMBER",
                        f"数字识别组{g['index']+1} raw='{text}', parsed={number}")
                    if number is not None:
                        last = self._last_results.get(g["index"])
                        if number != last:
                            self.app.logging_manager.log_message(
                                f"数字识别{g['index']+1}解析结果: {number}"
                            )
                            self._last_results[g["index"]] = number

                        if number < g["threshold"]:
                            self.app.logging_manager.debug("NUMBER",
                                f"数字识别组{g['index']+1} 低于阈值 {g['threshold']}, 触发动作")
                            alarm = self._safe_get_alarm(g["index"])
                            if alarm:
                                await run_in_executor(self.app.alarm_module.play_alarm_sound, alarm)
                            if g["key"]:
                                await run_in_executor(
                                    self._execute_keypress, g["key"], g["index"],
                                    g["delay_min"], g["delay_max"]
                                )
                    else:
                        last = self._last_results.get(g["index"])
                        if text != last:
                            self.app.logging_manager.log_message(
                                f"数字识别{g['index']+1}结果: '{text}'"
                            )
                            self._last_results[g["index"]] = text
                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    self.app.logging_manager.error("NUMBER",
                        f"数字识别{g['index']+1}错误: {str(e)}"
                    )
                    await asyncio.sleep(5)
        except asyncio.CancelledError:
            self.app.logging_manager.debug("NUMBER", f"数字识别组{g['index']+1} 协程取消")

    def _check_group_enabled(self, index):
        regions = getattr(self.app, 'number_regions', [])
        if index >= len(regions):
            return False
        try:
            return bool(regions[index]["enabled"].get())
        except Exception:
            return False

    def _safe_get_alarm(self, index):
        regions = getattr(self.app, 'number_regions', [])
        if index < len(regions):
            try:
                return regions[index]["alarm"].get()
            except Exception:
                pass
        return False

    def _execute_keypress(self, key, group_index, delay_min, delay_max):
        self.app.logging_manager.log_message(
            f"数字识别{group_index+1}触发按键: {key}"
        )
        from modules.input import KeyEventExecutor
        delay_min_var = type("", (), {"get": lambda: str(delay_min)})()
        delay_max_var = type("", (), {"get": lambda: str(delay_max)})()
        executor = KeyEventExecutor(
            self.app.input_controller, delay_min_var, delay_max_var, self.PRIORITY
        )
        executor.execute_keypress(key)
        self.app.logging_manager.log_message(
            f"数字识别{group_index+1}按下了 {key} 键，"
            f"按住时长范围: {delay_min}-{delay_max} 毫秒"
        )

    def take_screenshot(self, region):
        try:
            return self.screenshot_manager.get_region_screenshot(
                region, priority=self.PRIORITY
            )
        except Exception as e:
            self.app.logging_manager.error("NUMBER",
                f"数字识别错误: 屏幕截图失败 - {str(e)}"
            )
            return None

    def ocr_number(self, image, confidence_threshold=0.0):
        processed_image = _preprocess_image(image, group_index=None)
        if processed_image is None:
            processed_image = image.convert('L')
        return NumberRecognizer.recognize(processed_image,
                                          confidence_threshold=confidence_threshold)
