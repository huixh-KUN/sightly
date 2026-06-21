import threading
import time
from collections import OrderedDict
from PIL import Image
from input.permissions import PermissionManager
from utils.screenshot import ScreenshotManager
from utils.recognition import NumberRecognizer
from utils.image import _preprocess_image
from core.priority_lock import get_module_priority


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
    
    def start_number_recognition(self):
        def start_func():
            start_count = 0
            regions = getattr(self.app, 'number_regions', [])
            for i, region_config in enumerate(regions):
                if region_config["enabled"].get():
                    region = region_config["region"]
                    if not region:
                        continue
                    try:
                        threshold = int(region_config["threshold"].get())
                    except (ValueError, TypeError):
                        threshold = 500
                    try:
                        confidence_threshold = float(region_config["confidence_threshold"].get())
                    except (ValueError, TypeError, KeyError):
                        confidence_threshold = 0.3
                    key = region_config["key"].get()
                    stop_event = threading.Event()
                    stop_events = getattr(self.app, 'number_stop_events', {})
                    stop_events[i] = stop_event
                    if not hasattr(self.app, 'number_stop_events'):
                        self.app.number_stop_events = stop_events
                    else:
                        self.app.number_stop_events[i] = stop_event
                    threads = getattr(self.app, 'number_threads', [])
                    thread = threading.Thread(
                        target=self.number_recognition_loop,
                        args=(i, region, threshold, confidence_threshold, key, stop_event), daemon=True
                    )
                    threads.append(thread)
                    if not hasattr(self.app, 'number_threads'):
                        self.app.number_threads = threads
                    else:
                        self.app.number_threads.append(thread)
                    thread.start()
                    start_count += 1
            return start_count

        start_func()

    def stop_number_recognition(self):
        stop_events = getattr(self.app, 'number_stop_events', {})
        for stop_event in stop_events.values():
            stop_event.set()
        if hasattr(self.app, 'number_threads'):
            for t in self.app.number_threads:
                if t.is_alive():
                    t.join(timeout=1)
            self.app.number_threads.clear()
        if hasattr(self.app, 'number_stop_events'):
            self.app.number_stop_events.clear()
        self._last_results.clear()
        self._number_cache.clear()

    def number_recognition_loop(self, region_index, region, threshold,
                                 confidence_threshold, key, stop_event):
        while not stop_event.is_set():
            regions = getattr(self.app, 'number_regions', [])
            if region_index >= len(regions) or not regions[region_index]["enabled"].get():
                break
            if not getattr(self.app, 'is_running', True):
                break
            try:
                time.sleep(1)
                if stop_event.is_set():
                    return
                screenshot = self.take_screenshot(region)
                if screenshot is None:
                    continue
                text = self.ocr_number(screenshot, confidence_threshold)
                number = NumberRecognizer.parse_number(text, self._number_cache)
                if number is not None:
                    last_result = self._last_results.get(region_index)
                    if number != last_result:
                        self.app.logging_manager.log_message(
                            f"数字识别{region_index+1}解析结果: {number}"
                        )
                        self._last_results[region_index] = number

                    if number < threshold:
                        alarm_val = regions[region_index]["alarm"] \
                            if region_index < len(regions) else None
                        if alarm_val is not None:
                            self.app.alarm_module.play_alarm_sound(alarm_val)

                        if key:
                            self.app.logging_manager.log_message(
                                f"数字识别{region_index+1}触发按键: {key}"
                            )
                            from modules.input import KeyEventExecutor
                            if region_index < len(regions):
                                delay_min_var = regions[region_index]["delay_min"]
                                delay_max_var = regions[region_index]["delay_max"]
                                executor = KeyEventExecutor(
                                    self.app.input_controller,
                                    delay_min_var, delay_max_var, self.PRIORITY
                                )
                                executor.execute_keypress(key)
                                delay_min = int(delay_min_var.get())
                                delay_max = int(delay_max_var.get())
                                self.app.logging_manager.log_message(
                                    f"数字识别{region_index+1}按下了 {key} 键，"
                                    f"按住时长范围: {delay_min}-{delay_max} 毫秒"
                                )
                        else:
                            self.app.logging_manager.log_message(
                                f"数字识别{region_index+1}按键配置为空，仅执行报警操作"
                            )
                else:
                    last_result = self._last_results.get(region_index)
                    if text != last_result:
                        self.app.logging_manager.log_message(
                            f"数字识别{region_index+1}结果: '{text}'"
                        )
                        self._last_results[region_index] = text
            except Exception as e:
                self.app.logging_manager.error("NUMBER",
                    f"数字识别{region_index+1}错误: {str(e)}"
                )
                time.sleep(5)

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
