import time
import random
import re


_COMBO_MODIFIERS = {"ctrl", "alt", "shift", "win"}


def parse_combo_key(combo_str):
    """解析组合键字符串，返回 (修饰键列表, 主键)

    >>> parse_combo_key("Ctrl+F1")
    (['ctrl'], 'f1')
    >>> parse_combo_key("Alt+Shift+F1")
    (['alt', 'shift'], 'f1')
    >>> parse_combo_key("F1")
    ([], 'f1')
    """
    parts = combo_str.lower().split("+")
    mods = [p for p in parts if p in _COMBO_MODIFIERS]
    main = [p for p in parts if p not in _COMBO_MODIFIERS]
    main_key = main[0] if main else parts[-1]
    return mods, main_key


def execute_combo_key(controller, combo_str, priority=0, hold_delay=0.15):
    """执行组合键：按顺序按下修饰键+主键，等待，反向释放

    Args:
        controller: 应用控制器实例（含 input_controller）
        combo_str: 组合键字符串，如 "Ctrl+F1" 或 "F1"
        priority: 输入优先级
        hold_delay: 按住延迟（秒）
    """
    mods, main_key = parse_combo_key(combo_str)
    all_keys = mods + [main_key]

    if hasattr(controller, 'logging_manager'):
        controller.logging_manager.debug("INPUT", f"组合键按下: {combo_str} → keys={all_keys}")
    for k in all_keys:
        controller.input_controller.key_down(k, priority=priority)
    time.sleep(hold_delay)
    for k in reversed(all_keys):
        controller.input_controller.key_up(k, priority=priority)
    if hasattr(controller, 'logging_manager'):
        controller.logging_manager.debug("INPUT", f"组合键释放: {combo_str}")


class ClickWorker:
    """统一的鼠标点击处理器
    
    提供统一的鼠标点击接口，封装优先级处理、异常处理、日志记录等功能。
    """
    
    def __init__(self, controller):
        self.controller = controller
    
    @staticmethod
    def _apply_random_offset(x, y, offset_range):
        if offset_range <= 0:
            return x, y
        return x + random.randint(-offset_range, offset_range), y + random.randint(-offset_range, offset_range)

    def execute_click(self, x, y, priority=0, module_name="", index=0, delay=None, offset_range=0, *, for_test=False):
        """
        执行鼠标点击
        
        Args:
            x: 点击x坐标
            y: 点击y坐标
            priority: 优先级（默认0，数值越大优先级越高）
            module_name: 模块名称（用于日志）
            index: 组索引（用于日志，从0开始）
            delay: 点击后延迟时间（秒），None则使用app.click_delay
            offset_range: 随机偏移范围（像素），0=关闭
        
        Returns:
            bool: 是否执行成功
        """
        self.controller.logging_manager.debug("INPUT",
            f"execute_click: ({x},{y}), module={module_name}{index+1}, offset={offset_range}")
        if not for_test and not self._validate_running_state():
            self.controller.logging_manager.debug("INPUT", "execute_click: 运行状态无效，跳过")
            return False
        
        x, y = self._apply_random_offset(x, y, offset_range)
        self.controller.logging_manager.debug("INPUT", f"execute_click: 偏移后 ({x},{y})")
        
        if not self._validate_coordinates(x, y):
            self.controller.logging_manager.debug("INPUT", "execute_click: 坐标无效")
            return False
        
        try:
            self.controller.input_controller.move_to(x, y, priority=priority)
            self.controller.input_controller.mouse_down(x=x, y=y, button='left', priority=priority)
            time.sleep(0.1)
            self.controller.input_controller.mouse_up(x=x, y=y, button='left', priority=priority)
            self._log_click_success(x, y, module_name, index)
            self._wait_delay(delay)
            return True
        except Exception as e:
            self._log_click_error(e, module_name, index)
            return False
    
    def calculate_region_center(self, region):
        """
        计算区域中心点
        
        Args:
            region: 区域坐标 (x1, y1, x2, y2)
        
        Returns:
            tuple: (center_x, center_y) 或 (None, None)
        """
        if not region:
            return None, None
        
        try:
            x1, y1, x2, y2 = region
            center_x = (x1 + x2) // 2
            center_y = (y1 + y2) // 2
            return center_x, center_y
        except (ValueError, TypeError):
            return None, None
    
    def _validate_running_state(self):
        """验证运行状态"""
        if not self.controller.is_running or getattr(self.controller, 'system_stopped', False):
            return False
        return True
    
    def _validate_coordinates(self, x, y):
        """验证坐标有效性"""
        if x is None or y is None:
            return False
        return True
    
    def _log_click_success(self, x, y, module_name, index):
        """记录点击成功日志"""
        if module_name:
            platform = getattr(self.controller, 'platform_adapter', None)
            platform_name = platform.platform if platform else ""
            self.controller.logging_manager.log_message(
                f"[{platform_name}] {module_name}{index+1}执行鼠标点击: ({x}, {y})"
            )
    
    def _log_click_error(self, error, module_name, index):
        """记录点击错误日志"""
        if module_name:
            self.controller.logging_manager.log_message(
                f"{module_name}{index+1}鼠标点击失败: {str(error)}"
            )
    
    def _wait_delay(self, delay):
        """等待延迟时间"""
        if delay is not None:
            time.sleep(delay)
        elif hasattr(self.controller, 'click_delay'):
            time.sleep(self.controller.click_delay)
        else:
            time.sleep(0.1)
