import asyncio
import ctypes
import threading
import time
from typing import Optional, Dict, Any

from core.async_utils import run_in_executor

from utils.window_capture import (
    capture_window_region, find_window_by_title,
    find_window_by_class_and_process,
    get_window_rect, get_window_title,
    get_window_class_name, get_window_process_name,
)
from utils.quick_switch import QuickSwitchBackend
from utils.coordinate import RelativeCoordinate, WindowCoordinate
from utils.recognition import OCRRecognizer, ImageRecognizer, ColorRecognizer
from utils.image import _preprocess_image
from core.priority_lock import get_module_priority
from utils.memory import MemoryMonitor
from core.click_handler import ClickHandler, execute_combo_key
from core.config import ConfigVar

# 虚拟点击 WM_ 消息常量
WM_MOUSEMOVE = 0x0200
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_RBUTTONDOWN = 0x0204
WM_RBUTTONUP = 0x0205
WM_MBUTTONDOWN = 0x0207
WM_MBUTTONUP = 0x0208
MK_LBUTTON = 0x0001
MK_RBUTTON = 0x0002
MK_MBUTTON = 0x0010

_MOUSE_BUTTON_MAP = {
    "left":   (WM_LBUTTONDOWN, WM_LBUTTONUP, MK_LBUTTON),
    "right":  (WM_RBUTTONDOWN, WM_RBUTTONUP, MK_RBUTTON),
    "middle": (WM_MBUTTONDOWN, WM_MBUTTONUP, MK_MBUTTON),
}


def _find_content_hwnd(parent_hwnd):
    """查找父窗口中最可能的内容子窗口（递归）"""
    import ctypes
    from ctypes import wintypes

    candidates = []

    def enum_proc(hwnd, lparam):
        if ctypes.windll.user32.IsWindowVisible(hwnd):
            rect = wintypes.RECT()
            ctypes.windll.user32.GetClientRect(hwnd, ctypes.byref(rect))
            w = rect.right
            h = rect.bottom
            if w > 50 and h > 50:
                candidates.append((w * h, hwnd))
        return True

    callback = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)(enum_proc)
    ctypes.windll.user32.EnumChildWindows(parent_hwnd, callback, 0)

    if not candidates:
        return parent_hwnd

    candidates.sort(key=lambda x: -x[0])
    return candidates[0][1]


def _safe_get(group, key, default):
    """Safe dict.get() that avoids tkinter variable creation when no tk root exists."""
    if key in group:
        val = group[key]
        return val.get() if hasattr(val, 'get') else val
    return default

class BackgroundMonitor:
    """
    单个后台监控组
    
    优先级: 1 (最低)
    """
    
    PRIORITY = get_module_priority('background')
    
    def __init__(self, app, group_index: int = 0):
        self.app = app
        self.group_index = group_index
        self.is_running = False
        self._task = None
        
        self.hwnd = None
        self.region = None
        self.region_ratio = None
        self.recognition_type = "ocr"
        self.interval = 5.0
        self.pause = 180
        
        self.ocr_config = {}
        self.image_config = {}
        self.color_config = {}
        
        self.trigger_key = None
        self.delay_min = 100
        self.delay_max = 200
        self.trigger_click = False
        self.alarm_enabled = False
        
        self.click_offset = 0
        self.click_mode = "physical"  # "physical" | "virtual"
        self.last_trigger_time = 0
        self._last_text = None  # 缓存上次识别文本，用于日志节流
        self.memory_monitor = MemoryMonitor()
    
    def set_window(self, hwnd: int) -> None:
        """设置目标窗口"""
        self.hwnd = hwnd
    
    def set_region(self, region: tuple, save_ratio: bool = True) -> None:
        """
        设置监控区域（窗口相对坐标）
        
        Args:
            region: (x1, y1, x2, y2) 窗口相对坐标
            save_ratio: 是否保存比例坐标
        """
        self.region = region
        
        if save_ratio and self.hwnd and region:
            window_size = WindowCoordinate.get_window_size(self.hwnd)
            if window_size:
                self.region_ratio = RelativeCoordinate.pixel_to_ratio(region, window_size)
    
    def configure_ocr(self, keywords: str, language: str) -> None:
        """配置OCR识别"""
        self.ocr_config = {
            "keywords": keywords,
            "language": language
        }
    
    def configure_image(self, template_image, threshold: float) -> None:
        """配置图像识别"""
        import numpy as np

        cv_template = None
        if template_image is not None:
            if isinstance(template_image, np.ndarray):
                cv_template = template_image
            elif hasattr(template_image, 'toImage'):
                from PySide6.QtGui import QImage
                img = template_image.toImage().convertToFormat(QImage.Format_RGB888)
                bpl = img.bytesPerLine()
                ptr = img.bits()
                arr = np.frombuffer(ptr, dtype=np.uint8)
                arr = arr.reshape(img.height(), bpl)[:, :img.width() * 3]
                arr = arr.reshape(img.height(), img.width(), 3)
                cv_template = arr[:, :, ::-1].copy()
            elif hasattr(template_image, 'save'):
                import tempfile, os, cv2
                tmp = os.path.join(tempfile.gettempdir(), '_bg_template.png')
                template_image.save(tmp)
                cv_template = cv2.imread(tmp)
                os.remove(tmp)

        self.image_config = {
            "template": cv_template,
            "threshold": threshold
        }
    
    def configure_color(self, target_color: tuple, tolerance: int) -> None:
        """配置颜色识别"""
        self.color_config = {
            "target_color": target_color,
            "tolerance": tolerance
        }
    
    def start_monitoring(self) -> bool:
        """开始监控（同步接口，设置启动标志由事件循环创建任务）"""
        if self.is_running:
            return True
        if not self.hwnd:
            return False
        if not self.region and not self.region_ratio:
            return False
        self.is_running = True
        self.last_trigger_time = 0
        return True
    
    def stop_monitoring(self) -> None:
        """停止监控"""
        self.is_running = False
        self._last_text = None
        if self._task and not self._task.done():
            self._task.cancel()
            self._task = None
    
    def _get_current_region(self) -> Optional[tuple]:
        """获取当前有效的区域坐标（支持分辨率自适应）"""
        if self.region_ratio and self.hwnd:
            window_size = WindowCoordinate.get_window_size(self.hwnd)
            if window_size:
                return RelativeCoordinate.ratio_to_pixel(self.region_ratio, window_size)
        
        return self.region
    
    async def _monitor_async(self) -> None:
        """异步监控主循环"""
        self.app.logging_manager.debug("BG",
            f"组{self.group_index} 协程监控开始: type={self.recognition_type}, "
            f"interval={self.interval}s, pause={self.pause}s")
        frame_count = 0
        try:
            await asyncio.sleep(self.interval)

            while self.is_running:
                try:
                    current_time = time.time()
                    if current_time - self.last_trigger_time < self.pause:
                        await asyncio.sleep(0.5)
                        continue

                    region = self._get_current_region()
                    if not region:
                        self.app.logging_manager.debug("BG", f"组{self.group_index} 无有效区域")
                        await asyncio.sleep(self.interval)
                        continue

                    self.app.logging_manager.debug("BG",
                        f"组{self.group_index} 开始识别: region={region}, type={self.recognition_type}")
                    matched, click_position, _ = await run_in_executor(self.recognize_once)
                    self.app.logging_manager.debug("BG",
                        f"组{self.group_index} 识别结果: matched={matched}, click={click_position}")

                    if matched:
                        self.app.logging_manager.log_message(
                            f"后台监控组{self.group_index+1} 匹配成功: pos={click_position}")
                        await run_in_executor(self.trigger_actions, click_position)
                        self.last_trigger_time = current_time
                    else:
                        self.app.logging_manager.debug("BG", f"组{self.group_index} 未匹配")

                    await asyncio.sleep(self.interval)

                    frame_count += 1
                    if self.memory_monitor.gc_if_needed(frame_count):
                        self.app.logging_manager.debug("BG", f"组{self.group_index} 触发 GC")

                except asyncio.CancelledError:
                    raise
                except Exception as e:
                    self.app.logging_manager.error("BG",
                        f"后台监控组{self.group_index + 1}错误: {str(e)}"
                    )
                    await asyncio.sleep(5)

        except asyncio.CancelledError:
            self.app.logging_manager.debug("BG", f"组{self.group_index} 协程被取消")
            self.is_running = False
    
    def _capture_region(self, region: tuple):
        """截取监控区域"""
        if not self.hwnd:
            return None
        
        try:
            return capture_window_region(self.hwnd, region)
        except Exception:
            return None
    
    def _recognize(self, image) -> tuple:
        """执行识别，返回 (matched, click_position)"""
        if self.recognition_type == "ocr":
            return self._recognize_ocr(image)
        elif self.recognition_type == "image":
            return self._recognize_image(image)
        elif self.recognition_type == "color":
            return self._recognize_color(image)
        return (False, None)
    
    def _recognize_ocr(self, image) -> tuple:
        """OCR识别 - 使用与常规OCR模块相同的实现"""
        keywords = self.ocr_config.get("keywords", "")
        language = self.ocr_config.get("language", "简体中文")
        
        if not keywords:
            return (False, None)
        
        processed = _preprocess_image(image, self.group_index)
        if not processed:
            return (False, None)
        
        try:
            keyword_list = [keyword.strip().lower() for keyword in keywords.split(",") if keyword.strip()]
            if not keyword_list:
                return (False, None)
            
            text = OCRRecognizer.get_text(processed, language)
            
            if text and text.strip() != self._last_text:
                self.app.logging_manager.log_message(
                    f"后台监控组{self.group_index + 1}识别结果: '{text.strip()}'"
                )
                self._last_text = text.strip()
            
            if not text:
                return (False, None)
            
            lower_text = text.lower()
            if not any(keyword in lower_text for keyword in keyword_list):
                return (False, None)
            
            self.app.logging_manager.log_message(
                f"后台监控组{self.group_index + 1}识别到关键词: {text.strip()}"
            )
            
            click_pos = OCRRecognizer.find_keyword_position(processed, keyword_list, language)
            
            if click_pos is None:
                region = self._get_current_region()
                if region:
                    center_x = (region[0] + region[2]) // 2
                    center_y = (region[1] + region[3]) // 2
                    click_pos = (center_x, center_y)
            
            return (True, click_pos)
        finally:
            if processed is not None:
                processed.close()
                del processed
    
    def _recognize_image(self, image) -> tuple:
        """图像识别 - 使用公共识别工具类"""
        template = self.image_config.get("template")
        threshold = self.image_config.get("threshold", 0.8)
        
        if template is None:
            return (False, None)
        
        matched, click_pos, _ = ImageRecognizer.match_template(
            image, template, threshold,
            log_func=self.app.logging_manager.log_message,
            group_index=self.group_index
        )
        
        return (matched, click_pos)
    
    def _recognize_color(self, image) -> tuple:
        """颜色识别 - 使用公共识别工具类"""
        target_color = self.color_config.get("target_color")
        tolerance = self.color_config.get("tolerance", 10)
        
        if not target_color:
            return (False, None)
        
        matched, click_pos, _ = ColorRecognizer.match_color(
            image, target_color, tolerance,
            log_func=self.app.logging_manager.log_message,
            group_index=self.group_index
        )
        
        return (matched, click_pos)
    
    def recognize_once(self) -> tuple:
        """单次识别：截图 + 匹配，返回 (matched, click_pos, detail)。"""
        region = self._get_current_region()
        if not region:
            return False, None, "未设置监控区域"
        if not self.hwnd:
            return False, None, "未绑定目标窗口，无法截图"
        image = self._capture_region(region)
        if image is None:
            return False, None, "截图失败"
        try:
            matched, click_position = self._recognize(image)
            if matched and click_position:
                click_position = (
                    click_position[0] + region[0],
                    click_position[1] + region[1],
                )
            detail = self._build_recognize_detail(matched, click_position)
            return matched, click_position, detail
        finally:
            if image is not None and hasattr(image, 'close'):
                image.close()

    def _build_recognize_detail(self, matched, click_position) -> str:
        type_labels = {"ocr": "文字", "image": "图像", "color": "颜色"}
        label = type_labels.get(self.recognition_type, self.recognition_type)
        if not matched:
            return f"{label}识别：未匹配"
        pos_hint = f"，点击位置 ({click_position[0]}, {click_position[1]})" if click_position else ""
        return f"{label}识别：匹配成功{pos_hint}"

    def trigger_actions(self, click_position=None, *, for_test=False) -> None:
        """触发动作（报警、点击、按键）。"""
        self._trigger_action(click_position, for_test=for_test)

    def _trigger_action(self, click_position=None, *, for_test=False) -> None:
        """触发动作"""
        self.app.logging_manager.debug("BG", f"组{self.group_index} 触发动作: click_position={click_position}, trigger_click={self.trigger_click}, trigger_key={self.trigger_key}")
        if not for_test and not self.app.is_running:
            self.app.logging_manager.debug("BG", f"组{self.group_index} app未运行")
            return
        
        # 播放报警声音
        if self.alarm_enabled:
            try:
                temp_alarm_var = ConfigVar(True)
                self.app.alarm_module.play_alarm_sound(temp_alarm_var)
            except Exception as e:
                self.app.logging_manager.error("BG", f"播放报警声音失败: {e}")
        
        # 如果只设置了报警，无需后续操作
        if not self.trigger_click and not self.trigger_key:
            return

        self.app.logging_manager.log_message(
            f"组{self.group_index} 点击模式: {self.click_mode}, trigger_click={self.trigger_click}, trigger_key={self.trigger_key}")

        # 虚拟点击：向窗口发送鼠标消息，无需切换窗口
        if self.click_mode == "virtual" and self.trigger_click:
            try:
                target_hwnd = _find_content_hwnd(self.hwnd)
                if click_position:
                    cx, cy = ClickHandler._apply_random_offset(
                        click_position[0], click_position[1], self.click_offset
                    )
                else:
                    region = self._get_current_region()
                    if region:
                        cx = (region[0] + region[2]) // 2
                        cy = (region[1] + region[3]) // 2
                        cx, cy = ClickHandler._apply_random_offset(cx, cy, self.click_offset)
                    else:
                        cx, cy = 0, 0

                wm_down, wm_up, mk_flag = _MOUSE_BUTTON_MAP.get("left",
                    (WM_LBUTTONDOWN, WM_LBUTTONUP, MK_LBUTTON))
                lparam = (cy << 16) | (cx & 0xFFFF)

                # 先发鼠标移动（部分窗口依赖）
                ctypes.windll.user32.SendMessageW(target_hwnd, WM_MOUSEMOVE, 0, lparam)
                # 发送按下 + 抬起
                ctypes.windll.user32.SendMessageW(target_hwnd, wm_down, mk_flag, lparam)
                ctypes.windll.user32.SendMessageW(target_hwnd, wm_up, 0, lparam)

                self.app.logging_manager.log_message(
                    f"组{self.group_index} 虚拟点击: target_hwnd={target_hwnd}, pos=({cx}, {cy})")
            except Exception as e:
                self.app.logging_manager.error("BG",
                    f"组{self.group_index} 虚拟点击失败: {e}")

        # 物理点击或按键需要窗口切换
        need_switch = (self.click_mode == "physical" and self.trigger_click) or bool(self.trigger_key)
        if need_switch:
            self.app.logging_manager.log_message(
                f"组{self.group_index} 物理路径: need_switch={need_switch}, click_mode={self.click_mode}")
            quick_switch = QuickSwitchBackend(self.app)
            quick_switch.set_hwnd(self.hwnd)
            quick_switch._save_foreground_window()
            switch_success = quick_switch._switch_to_target()
            self.app.logging_manager.debug("BG", f"组{self.group_index} 窗口切换: {switch_success}")

            if switch_success:
                if self.trigger_click and self.click_mode == "physical":
                    if click_position:
                        rect = get_window_rect(self.hwnd)
                        self.app.logging_manager.debug("BG", f"组{self.group_index} 点击: hwnd={self.hwnd}, rect={rect}, click_pos={click_position}")
                        if rect:
                            abs_x = rect[0] + click_position[0]
                            abs_y = rect[1] + click_position[1]
                            abs_x, abs_y = ClickHandler._apply_random_offset(abs_x, abs_y, self.click_offset)
                            self.app.logging_manager.debug("BG", f"组{self.group_index} 执行点击: ({abs_x}, {abs_y})")
                            self.app.input_controller.click(abs_x, abs_y, priority=1)
                            self.app.logging_manager.debug("BG", f"组{self.group_index} 点击执行完成")
                        else:
                            self.app.logging_manager.debug("BG", f"组{self.group_index} 获取窗口矩形失败")
                    else:
                        region = self._get_current_region()
                        if region:
                            click_x = (region[0] + region[2]) // 2
                            click_y = (region[1] + region[3]) // 2
                            rect = get_window_rect(self.hwnd)
                            if rect:
                                abs_x = rect[0] + click_x
                                abs_y = rect[1] + click_y
                                abs_x, abs_y = ClickHandler._apply_random_offset(abs_x, abs_y, self.click_offset)
                                self.app.input_controller.click(abs_x, abs_y, priority=1)

                time.sleep(0.1)

                if self.trigger_key:
                    import random
                    hold_delay = random.randint(self.delay_min, self.delay_max) / 1000.0
                    execute_combo_key(self.app, self.trigger_key, priority=1, hold_delay=hold_delay)

                quick_switch._restore_foreground_window()
            else:
                self.app.logging_manager.error("BG",
                    f"后台监控组{self.group_index + 1}窗口切换失败，跳过操作"
                )

class BackgroundManager:
    """后台监控管理器"""
    def __init__(self, app):
        self.app = app
        self.monitors: Dict[int, BackgroundMonitor] = {}
        self.quick_switch = QuickSwitchBackend()
        self.target_hwnd: Optional[int] = None
        self.target_title: Optional[str] = None
        self.window_class: Optional[str] = None
        self.window_process: Optional[str] = None
        self._loop = None
        self._async_thread = None
    
    def find_target_window(self, keyword: str) -> tuple:
        """
        查找目标窗口
        
        Returns:
            tuple: (success, message)
        """
        if not keyword:
            return (False, "请输入窗口标题关键字")
        
        hwnd = find_window_by_title(keyword)
        if hwnd:
            self.target_hwnd = hwnd
            self.target_title = get_window_title(hwnd)
            return (True, self.target_title)
        
        return (False, "未找到匹配的窗口")
    
    def set_target_window(self, hwnd: int) -> None:
        """设置目标窗口，自动采集类名和进程名"""
        self.target_hwnd = hwnd
        self.target_title = get_window_title(hwnd) if hwnd else None
        self.window_class = get_window_class_name(hwnd) if hwnd else None
        self.window_process = get_window_process_name(hwnd) if hwnd else None
    
    def auto_reconnect(self, window_class: str, window_process: str = None,
                       window_title: str = None) -> bool:
        """
        按类名+进程名自动重连目标窗口

        匹配策略（逐级回退）：
          1. class_name + process_name 精确匹配
          2. class_name 仅类名匹配
          3. window_title 完整标题子串匹配（回退方案）

        Args:
            window_class: 窗口类名
            window_process: 进程名，可选
            window_title: 窗口标题，可选（用于回退匹配）

        Returns:
            bool: 是否成功重连
        """
        hwnd = find_window_by_class_and_process(window_class, window_process or "")
        if not hwnd and window_class:
            hwnd = find_window_by_class_and_process(window_class, "")
        if not hwnd and window_title:
            self._log("BG", f"auto_reconnect: 回退到标题匹配 title={window_title}")
            import win32gui
            kw = window_title.lower()
            def enum_cb(h, _):
                try:
                    if win32gui.IsWindowVisible(h) and kw in win32gui.GetWindowText(h).lower():
                        nonlocal hwnd
                        hwnd = h
                        return False
                except Exception:
                    pass
                return True
            try:
                win32gui.EnumWindows(enum_cb, None)
            except Exception:
                pass
        self._log("BG",
            f"auto_reconnect: class={window_class}, process={window_process}, "
            f"title={window_title}, found={hwnd}")
        if hwnd:
            self.set_target_window(hwnd)
            return True
        return False

    def _log(self, tag, msg):
        if hasattr(self.app, 'logging_manager'):
            self.app.logging_manager.debug(tag, msg)
    
    def window_info(self) -> Dict[str, Any]:
        """返回窗口标识信息，供配置持久化使用"""
        return {
            "window_class": self.window_class,
            "window_process": self.window_process,
            "window_title": self.target_title,
        }
    
    def _apply_group_config(self, monitor: BackgroundMonitor, group: dict) -> None:
        """从 app 配置同步到 monitor 实例。"""
        region = group.get("region")
        region_ratio = group.get("region_ratio")
        if region:
            monitor.region = region
        if region_ratio:
            monitor.region_ratio = region_ratio

        try:
            monitor.interval = float(_safe_get(group, "interval", "5"))
            monitor.pause = int(_safe_get(group, "pause", "180"))
        except (ValueError, TypeError):
            monitor.interval = 5.0
            monitor.pause = 180

        monitor_type = _safe_get(group, "type", "ocr")
        monitor.recognition_type = monitor_type

        if monitor_type == "ocr":
            keywords = _safe_get(group, "keywords", "")
            language = _safe_get(group, "language", "简体中文")
            monitor.configure_ocr(keywords, language)
        elif monitor_type == "image":
            template = group.get("template_image")
            try:
                threshold = float(_safe_get(group, "threshold", "80")) / 100.0
            except (ValueError, TypeError):
                threshold = 0.8
            monitor.configure_image(template, threshold)
        elif monitor_type == "color":
            target_color = group.get("target_color")
            try:
                tolerance = int(_safe_get(group, "tolerance", "10"))
            except (ValueError, TypeError):
                tolerance = 10
            monitor.configure_color(target_color, tolerance)

        monitor.trigger_key = _safe_get(group, "key", "")
        try:
            monitor.delay_min = int(_safe_get(group, "delay_min", "100"))
            monitor.delay_max = int(_safe_get(group, "delay_max", "200"))
        except (ValueError, TypeError):
            monitor.delay_min = 100
            monitor.delay_max = 200

        monitor.trigger_click = _safe_get(group, "click_enabled", False)
        monitor.click_offset = int(_safe_get(group, "click_offset", "0"))
        monitor.click_mode = _safe_get(group, "click_mode", "physical")
        monitor.alarm_enabled = _safe_get(group, "alarm", False)

    def run_once(self, index: int) -> dict:
        """单次测试：识别 + 执行动作。"""
        groups = getattr(self.app, 'background_groups', [])
        if index >= len(groups):
            return {"matched": False, "executed": False, "detail": "组索引越界"}
        if not self.target_hwnd:
            return {"matched": False, "executed": False, "detail": "未绑定目标窗口，无法截图"}
        group = groups[index]
        monitor = BackgroundMonitor(self.app, index)
        monitor.set_window(self.target_hwnd)
        self._apply_group_config(monitor, group)
        if not monitor.region and not monitor.region_ratio:
            return {"matched": False, "executed": False, "detail": "未设置监控区域"}
        matched, click_pos, detail = monitor.recognize_once()
        executed = False
        if matched:
            monitor.trigger_actions(click_pos, for_test=True)
            executed = True
            detail = f"{detail}；已按配置执行动作"
        return {"matched": matched, "executed": executed, "detail": detail}

    def create_group(self, index: int, monitor_type: str = "ocr") -> BackgroundMonitor:
        """创建监控组"""
        monitor = BackgroundMonitor(self.app, index)
        monitor.recognition_type = monitor_type
        
        if self.target_hwnd:
            monitor.set_window(self.target_hwnd)
        
        self.monitors[index] = monitor
        return monitor
    
    def start_group(self, group_index: int) -> bool:
        """启动单个监控组"""
        if group_index not in self.monitors:
            return False
        
        monitor = self.monitors[group_index]
        
        if not self.target_hwnd:
            return False
        
        monitor.set_window(self.target_hwnd)
        return monitor.start_monitoring()
    
    def stop_group(self, group_index: int) -> None:
        """停止单个监控组"""
        if group_index in self.monitors:
            monitor = self.monitors[group_index]
            monitor.stop_monitoring()
            if self._loop and self._loop.is_running():
                if monitor._task and not monitor._task.done():
                    monitor._task.cancel()
    
    def start_all_groups(self) -> int:
        """
        启动所有启用的监控组（同步配置 + 异步事件循环）

        Returns:
            int: 启动的监控组数量
        """
        if not self.target_hwnd:
            self.app.logging_manager.log_message("请先绑定目标窗口")
            return 0

        start_count = 0
        groups = getattr(self.app, 'background_groups', [])

        # 同步配置阶段（在主线程执行）
        for group_index, group in enumerate(groups):
            enabled = _safe_get(group, "enabled", False)
            if not enabled:
                continue

            if group_index not in self.monitors:
                monitor_type = group.get("type", "ocr")
                self.create_group(group_index, monitor_type)

            monitor = self.monitors[group_index]
            monitor.set_window(self.target_hwnd)
            self._apply_group_config(monitor, group)

            if not monitor.region and not monitor.region_ratio:
                continue

            self.app.logging_manager.debug("BG",
                f"组{group_index}: region={monitor.region}, click={monitor.trigger_click}, key={monitor.trigger_key}")

            if monitor.start_monitoring():
                start_count += 1

        if start_count == 0:
            return 0

        # 异步运行阶段（每个模块一个线程 + 事件循环）
        self._async_thread = threading.Thread(target=self._run_async, daemon=True)
        self._async_thread.start()
        return start_count

    def _run_async(self):
        """后台线程：创建事件循环并运行所有监控组协程"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._loop = loop
        try:
            loop.run_until_complete(self._async_main())
        finally:
            loop.close()
            self._loop = None

    async def _async_main(self):
        """创建所有已启用监控组的协程任务"""
        tasks = []
        for idx, monitor in self.monitors.items():
            if monitor.is_running:
                t = asyncio.create_task(monitor._monitor_async())
                monitor._task = t
                tasks.append(t)
        if tasks:
            try:
                await asyncio.gather(*tasks, return_exceptions=True)
            except asyncio.CancelledError:
                pass

    def stop_all_groups(self) -> None:
        """停止所有监控组（取消协程 + 等待线程退出）"""
        for monitor in self.monitors.values():
            monitor.stop_monitoring()

        if self._loop and self._loop.is_running():
            for task in asyncio.all_tasks(loop=self._loop):
                if not task.done():
                    task.cancel()

        if self._async_thread and self._async_thread.is_alive():
            self._async_thread.join(timeout=3)

    def get_window_info(self) -> Optional[Dict[str, Any]]:
        """获取目标窗口信息"""
        if not self.target_hwnd:
            return None
        
        rect = get_window_rect(self.target_hwnd)
        size = WindowCoordinate.get_window_size(self.target_hwnd)
        title = get_window_title(self.target_hwnd)
        
        return {
            "hwnd": self.target_hwnd,
            "title": title,
            "rect": rect,
            "size": size
        }
