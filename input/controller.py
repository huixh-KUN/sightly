"""
输入控制器工厂
根据配置或编译参数选择具体实现
保持与现有代码的完全兼容
"""
import os
import logging
import threading
import time
from typing import Optional

from core.priority_lock import PriorityLock


USE_DD_INPUT = os.environ.get('SIGHTLY_USE_DD', '0') == '1'

_dd_input_instance = None
_pyautogui_input_instance = None


def _get_dd_input(controller=None):
    """延迟加载DD输入实例"""
    global _dd_input_instance
    if _dd_input_instance is None:
        try:
            from .dd_input import DDInputBackend
            _dd_input_instance = DDInputBackend(controller=controller)
        except Exception as e:
            controller.logging_manager.error("INPUT", f"加载DD输入模块失败: {e}")
    return _dd_input_instance


def _get_pyautogui_input(controller=None):
    """延迟加载PyAutoGUI输入实例"""
    global _pyautogui_input_instance
    if _pyautogui_input_instance is None:
        try:
            from .pyautogui_input import PyAutoGUIInputBackend
            _pyautogui_input_instance = PyAutoGUIInputBackend(controller=controller)
        except Exception as e:
            controller.logging_manager.error("INPUT", f"加载PyAutoGUI输入模块失败: {e}")
    return _pyautogui_input_instance


def _get_win32_input(controller=None):
    """延迟加载Win32 API输入实例"""
    try:
        from .win32_input import Win32InputBackend
        return Win32InputBackend(controller=controller)
    except Exception as e:
        logging.getLogger(__name__).error(f"_get_win32_input 失败: {e}")
        return None


class InputController:
    """
    输入控制器类（兼容层）
    
    保持与现有代码的完全兼容，内部委托给具体实现
    使用优先级锁确保高优先级模块优先执行输入操作。
    """
    
    def __init__(self, controller=None, method: str = None):
        """
        初始化输入控制器
        
        Args:
            controller: 应用控制器实例
            method: 输入方式，可选 'pyautogui' 或 'dd'
                   如果为None，则根据编译标志自动选择
        """
        self.controller = controller
        self.core_graphics_available = False
        self.key_lock = PriorityLock()
        self.mouse_lock = PriorityLock()
        self._method = method
        self._impl = None
        
        self._init_implementation()
    
    def _init_implementation(self):
        """初始化具体实现"""
        method = self._method
        
        if method is None:
            if USE_DD_INPUT:
                method = 'dd'
            else:
                method = 'pyautogui'
        
        if method == 'dd':
            impl = _get_dd_input(self.controller)
            if impl and impl.is_available:
                self._impl = impl
                self._method = 'dd'
                self._log(f"InputController初始化完成，使用DD虚拟键盘执行所有输入操作")
                return
        
        impl = _get_pyautogui_input(self.controller)
        if impl and impl.is_available:
            self._impl = impl
            self._method = 'pyautogui'
            self._log(f"InputController初始化完成，使用PyAutoGUI执行所有输入操作")
            return
        
        impl = _get_win32_input(self.controller)
        if impl and impl.is_available:
            self._impl = impl
            self._method = 'win32'
            self._log(f"InputController初始化完成，使用Win32 API执行所有输入操作")
            return
        
        self._log("❌ InputController初始化失败：无可用的输入方式")
    
    @property
    def method(self) -> str:
        """返回当前使用的输入方式"""
        return self._method
    
    @property
    def method_name(self) -> str:
        """返回当前输入方式的名称"""
        if self._impl:
            return self._impl.method_name
        return "Unknown"
    
    @property
    def is_available(self) -> bool:
        """返回当前输入方式是否可用"""
        if self._impl:
            return self._impl.is_available
        return False
    
    def _log(self, message: str):
        """日志输出"""
        if self.controller and hasattr(self.controller, 'logging_manager'):
            self.controller.logging_manager.log_message(message)
    
    @staticmethod
    def handle_permission_errors(func):
        """统一处理权限相关错误"""
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except Exception as e:
                error_msg = str(e).lower()
                if self.controller and ("accessibility" in error_msg or "permission" in error_msg):
                    self._log("❌ 辅助功能权限缺失，请授权后重试")
                    if hasattr(self.controller, '_guide_accessibility_setup'):
                        from PySide6.QtCore import QTimer
                        QTimer.singleShot(0, self.controller._guide_accessibility_setup)
                elif self.controller:
                    self._log(f"❌ 操作错误: {e}")
                raise
        return wrapper
    
    @handle_permission_errors
    def press_key(self, key, delay=0, priority=0):
        """单次按键"""
        with self.key_lock.acquire(priority):
            if delay > 0:
                time.sleep(delay)
            
            if self._impl:
                return self._impl.press_key(key, delay, priority)
            return False
    
    @handle_permission_errors
    def key_down(self, key, priority=0):
        """按下按键"""
        with self.key_lock.acquire(priority):
            if self._impl:
                return self._impl.key_down(key, priority)
            return False
    
    @handle_permission_errors
    def key_up(self, key, priority=0):
        """释放按键"""
        with self.key_lock.acquire(priority):
            if self._impl:
                return self._impl.key_up(key, priority)
            return False
    
    @handle_permission_errors
    def click(self, x, y, priority=0):
        """鼠标点击"""
        with self.mouse_lock.acquire(priority):
            if self._impl:
                return self._impl.mouse_move(x, y) and self._impl.mouse_click()
            return False
    
    @handle_permission_errors
    def mouse_down(self, x=None, y=None, button='left', priority=0):
        """鼠标按下"""
        with self.mouse_lock.acquire(priority):
            if self._impl:
                if x is not None and y is not None:
                    self._impl.mouse_move(x, y)
                return self._impl.mouse_down(button)
            return False
    
    @handle_permission_errors
    def mouse_up(self, x=None, y=None, button='left', priority=0):
        """鼠标释放"""
        with self.mouse_lock.acquire(priority):
            if self._impl:
                if x is not None and y is not None:
                    self._impl.mouse_move(x, y)
                return self._impl.mouse_up(button)
            return False
    
    @handle_permission_errors
    def move_to(self, x, y, priority=0):
        """移动鼠标"""
        with self.mouse_lock.acquire(priority):
            if self._impl:
                return self._impl.mouse_move(x, y)
            return False

