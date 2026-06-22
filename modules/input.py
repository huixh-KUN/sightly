import time
import random

from core.click_handler import parse_combo_key


class KeyEventExecutor:
    """
    统一按键执行器类，支持单键和组合键
    
    执行流程：按下修饰键+主键 -> 等待(delay) -> 反向释放
    delay_min/max 表示按键按住的时长范围（毫秒）
    """
    
    def __init__(self, input_controller, delay_min_var, delay_max_var, priority=0):
        self.input_controller = input_controller
        self.delay_min_var = delay_min_var
        self.delay_max_var = delay_max_var
        self.priority = priority
    
    def execute_keypress(self, key):
        delay_min = max(1, int(self.delay_min_var.get()))
        delay_max = max(delay_min, int(self.delay_max_var.get()))
        
        hold_delay = random.randint(delay_min, delay_max) / 1000
        
        mods, main_key = parse_combo_key(key)
        all_keys = mods + [main_key]
        
        for k in all_keys:
            self.input_controller.key_down(k, priority=self.priority)
        time.sleep(hold_delay)
        for k in reversed(all_keys):
            self.input_controller.key_up(k, priority=self.priority)