"""
Win32 API 输入控制器（纯 ctypes，无外部依赖）
使用 SendInput 模拟键盘和鼠标操作，兼容 Windows 全版本
"""
import ctypes
import ctypes.wintypes
import threading
from typing import Optional

from .base import BaseInputController

KEYEVENTF_KEYDOWN = 0x0000
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_SCANCODE = 0x0008

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004
MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP = 0x0040
MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_ABSOLUTE = 0x8000

user32 = ctypes.windll.user32


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.wintypes.LONG),
        ("dy", ctypes.wintypes.LONG),
        ("mouseData", ctypes.wintypes.DWORD),
        ("dwFlags", ctypes.wintypes.DWORD),
        ("time", ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.wintypes.WORD),
        ("wScan", ctypes.wintypes.WORD),
        ("dwFlags", ctypes.wintypes.DWORD),
        ("time", ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [
        ("uMsg", ctypes.wintypes.DWORD),
        ("wParamL", ctypes.wintypes.WORD),
        ("wParamH", ctypes.wintypes.WORD),
    ]


class INPUT_UNION(ctypes.Union):
    _fields_ = [
        ("mi", MOUSEINPUT),
        ("ki", KEYBDINPUT),
        ("hi", HARDWAREINPUT),
    ]


class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", ctypes.wintypes.DWORD),
        ("union", INPUT_UNION),
    ]


INPUT_MOUSE = 0
INPUT_KEYBOARD = 1
INPUT_HARDWARE = 2

SendInput = user32.SendInput
SendInput.argtypes = [ctypes.c_uint, ctypes.POINTER(INPUT), ctypes.c_int]
SendInput.restype = ctypes.c_uint

VK_CODE = {
    'backspace': 0x08, 'tab': 0x09, 'enter': 0x0D, 'return': 0x0D,
    'shift': 0x10, 'shift_l': 0xA0, 'shift_r': 0xA1,
    'control': 0x11, 'ctrl': 0x11, 'control_l': 0xA2, 'control_r': 0xA3,
    'alt': 0x12, 'alt_l': 0xA4, 'alt_r': 0xA5,
    'pause': 0x13, 'capslock': 0x14, 'escape': 0x1B, 'esc': 0x1B,
    'space': 0x20, 'pageup': 0x21, 'pagedown': 0x22, 'prior': 0x21, 'next': 0x22,
    'end': 0x23, 'home': 0x24, 'left': 0x25, 'up': 0x26, 'right': 0x27, 'down': 0x28,
    'printscreen': 0x2C, 'insert': 0x2D, 'delete': 0x2E,
    '0': 0x30, '1': 0x31, '2': 0x32, '3': 0x33, '4': 0x34,
    '5': 0x35, '6': 0x36, '7': 0x37, '8': 0x38, '9': 0x39,
    'a': 0x41, 'b': 0x42, 'c': 0x43, 'd': 0x44, 'e': 0x45,
    'f': 0x46, 'g': 0x47, 'h': 0x48, 'i': 0x49, 'j': 0x4A,
    'k': 0x4B, 'l': 0x4C, 'm': 0x4D, 'n': 0x4E, 'o': 0x4F,
    'p': 0x50, 'q': 0x51, 'r': 0x52, 's': 0x53, 't': 0x54,
    'u': 0x55, 'v': 0x56, 'w': 0x57, 'x': 0x58, 'y': 0x59, 'z': 0x5A,
    'win_l': 0x5B, 'win_r': 0x5C, 'win': 0x5B, 'super_l': 0x5B, 'super_r': 0x5C,
    'numlock': 0x90, 'scrolllock': 0x91,
    'numpad0': 0x60, 'numpad1': 0x61, 'numpad2': 0x62, 'numpad3': 0x63,
    'numpad4': 0x64, 'numpad5': 0x65, 'numpad6': 0x66, 'numpad7': 0x67,
    'numpad8': 0x68, 'numpad9': 0x69, 'multiply': 0x6A, 'add': 0x6B,
    'separator': 0x6C, 'subtract': 0x6D, 'decimal': 0x6E, 'divide': 0x6F,
    'f1': 0x70, 'f2': 0x71, 'f3': 0x72, 'f4': 0x73, 'f5': 0x74,
    'f6': 0x75, 'f7': 0x76, 'f8': 0x77, 'f9': 0x78, 'f10': 0x79,
    'f11': 0x7A, 'f12': 0x7B, 'f13': 0x7C, 'f14': 0x7D, 'f15': 0x7E,
    'f16': 0x7F, 'f17': 0x80, 'f18': 0x81, 'f19': 0x82, 'f20': 0x83,
    'f21': 0x84, 'f22': 0x85, 'f23': 0x86, 'f24': 0x87,
    ';': 0xBA, '=': 0xBB, 'plus': 0xBB, 'equal': 0xBB,
    ',': 0xBC, 'comma': 0xBC, '-': 0xBD, 'minus': 0xBD,
    '.': 0xBE, 'period': 0xBE, '/': 0xBF, 'slash': 0xBF,
    '`': 0xC0, 'backquote': 0xC0,
    '[': 0xDB, 'leftbrace': 0xDB,
    '\\': 0xDC, 'backslash': 0xDC,
    ']': 0xDD, 'rightbrace': 0xDD,
    "'": 0xDE, 'apostrophe': 0xDE,
}


def _to_vk(key_name):
    """将按键名转换为虚拟键码"""
    lower = key_name.lower().strip()
    if lower in VK_CODE:
        return VK_CODE[lower]
    if len(lower) == 1:
        return ord(lower.upper())
    return 0


def _send_key(vk_code, key_up=False):
    """发送单个键盘事件"""
    flags = KEYEVENTF_KEYUP if key_up else KEYEVENTF_KEYDOWN
    ki = KEYBDINPUT()
    ki.wVk = vk_code
    ki.dwFlags = flags
    xi = INPUT()
    xi.type = INPUT_KEYBOARD
    xi.union.ki = ki
    SendInput(1, ctypes.byref(xi), ctypes.sizeof(INPUT))


def _send_mouse_move(x, y):
    """发送鼠标移动事件"""
    sw = ctypes.windll.user32.GetSystemMetrics(0)
    sh = ctypes.windll.user32.GetSystemMetrics(1)
    dx = int(x * 65535 / sw)
    dy = int(y * 65535 / sh)
    mi = MOUSEINPUT()
    mi.dx = dx
    mi.dy = dy
    mi.dwFlags = MOUSEEVENTF_MOVE | MOUSEEVENTF_ABSOLUTE
    xi = INPUT()
    xi.type = INPUT_MOUSE
    xi.union.mi = mi
    SendInput(1, ctypes.byref(xi), ctypes.sizeof(INPUT))


def _send_mouse_button(button, down=True):
    """发送鼠标按键事件"""
    btn_map = {
        'left': (MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP),
        'right': (MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP),
        'middle': (MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP),
    }
    flags = btn_map.get(button.lower(), btn_map['left'])
    flag = flags[0] if down else flags[1]
    mi = MOUSEINPUT()
    mi.dwFlags = flag
    xi = INPUT()
    xi.type = INPUT_MOUSE
    xi.union.mi = mi
    SendInput(1, ctypes.byref(xi), ctypes.sizeof(INPUT))


class Win32InputBackend(BaseInputController):
    """纯 Windows API 输入后端，无任何外部依赖"""

    def __init__(self, app=None):
        self.app = app
        self._log("Win32InputBackend 初始化完成")

    @property
    def method_name(self) -> str:
        return "Win32API"

    @property
    def is_available(self) -> bool:
        return True

    def _log(self, message: str):
        if self.app and hasattr(self.app, 'logging_manager'):
            self.app.logging_manager.log_message(message)

    def key_down(self, key: str, priority: int = 0) -> bool:
        vk = _to_vk(key)
        if not vk:
            self._log(f"⚠️ Win32Input: 未知按键 '{key}'")
            return False
        _send_key(vk, key_up=False)
        return True

    def key_up(self, key: str, priority: int = 0) -> bool:
        vk = _to_vk(key)
        if not vk:
            return False
        _send_key(vk, key_up=True)
        return True

    def press_key(self, key: str, delay: float = 0, priority: int = 0) -> bool:
        vk = _to_vk(key)
        if not vk:
            self._log(f"⚠️ Win32Input: 未知按键 '{key}'")
            return False
        _send_key(vk, key_up=False)
        if delay > 0:
            import time
            time.sleep(delay)
        _send_key(vk, key_up=True)
        return True

    def mouse_move(self, x: int, y: int) -> bool:
        _send_mouse_move(x, y)
        return True

    def mouse_move_relative(self, dx: int, dy: int) -> bool:
        current = ctypes.wintypes.POINT()
        user32.GetCursorPos(ctypes.byref(current))
        _send_mouse_move(current.x + dx, current.y + dy)
        return True

    def mouse_click(self, button: str = 'left') -> bool:
        _send_mouse_button(button, down=True)
        import time
        time.sleep(0.05)
        _send_mouse_button(button, down=False)
        return True

    def mouse_down(self, button: str = 'left') -> bool:
        _send_mouse_button(button, down=True)
        return True

    def mouse_up(self, button: str = 'left') -> bool:
        _send_mouse_button(button, down=False)
        return True

    def mouse_scroll(self, clicks: int) -> bool:
        user32.mouse_event(0x0800, 0, 0, clicks, 0)
        return True
