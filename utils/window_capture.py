import ctypes
import logging
import win32gui
import win32ui
import win32con
from PIL import Image
from typing import Optional, List, Tuple


def find_window_by_title(keyword: str) -> Optional[int]:
    """
    通过标题关键字查找窗口
    
    Args:
        keyword: 窗口标题关键字（不区分大小写）
    
    Returns:
        int: 窗口句柄，未找到返回None
    """
    if not keyword:
        return None
    
    keyword_lower = keyword.lower()
    found_hwnd = None
    
    def enum_windows_callback(hwnd, _):
        nonlocal found_hwnd
        if found_hwnd is not None:
            return False
        
        if not win32gui.IsWindowVisible(hwnd):
            return True
        
        title = win32gui.GetWindowText(hwnd)
        if keyword_lower in title.lower():
            found_hwnd = hwnd
            return False
        
        return True
    
    try:
        win32gui.EnumWindows(enum_windows_callback, None)
        return found_hwnd
    except Exception as e:
        logging.getLogger(__name__).error(f"find_window_by_title 失败: {e}")
        return None


def find_all_windows_by_title(keyword: str) -> List[Tuple[int, str]]:
    """
    通过标题关键字查找所有匹配的窗口
    
    Args:
        keyword: 窗口标题关键字（不区分大小写）
    
    Returns:
        list: [(hwnd, title), ...] 窗口句柄和标题列表
    """
    if not keyword:
        return []
    
    keyword_lower = keyword.lower()
    results = []
    
    def enum_windows_callback(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return True
        
        title = win32gui.GetWindowText(hwnd)
        if keyword_lower in title.lower():
            results.append((hwnd, title))
        
        return True
    
    try:
        win32gui.EnumWindows(enum_windows_callback, None)
        return results
    except Exception as e:
        logging.getLogger(__name__).error(f"find_all_windows_by_title 失败: {e}")
        return []


def get_window_rect(hwnd: int) -> Optional[tuple]:
    """
    获取窗口矩形区域
    
    Args:
        hwnd: 窗口句柄
    
    Returns:
        tuple: (left, top, right, bottom)，失败返回None
    """
    try:
        return win32gui.GetWindowRect(hwnd)
    except Exception as e:
        logging.getLogger(__name__).error(f"get_window_rect 失败: {e}")
        return None


def get_window_title(hwnd: int) -> Optional[str]:
    """
    获取窗口标题
    
    Args:
        hwnd: 窗口句柄
    
    Returns:
        str: 窗口标题，失败返回None
    """
    try:
        return win32gui.GetWindowText(hwnd)
    except Exception as e:
        logging.getLogger(__name__).error(f"get_window_title 失败: {e}")
        return None


def is_window_minimized(hwnd: int) -> bool:
    """
    检查窗口是否最小化
    
    Args:
        hwnd: 窗口句柄
    
    Returns:
        bool: 是否最小化
    """
    try:
        return win32gui.IsIconic(hwnd)
    except Exception as e:
        logging.getLogger(__name__).error(f"is_window_minimized 失败: {e}")
        return True


def restore_window(hwnd: int) -> bool:
    """
    恢复最小化的窗口
    
    Args:
        hwnd: 窗口句柄
    
    Returns:
        bool: 是否成功
    """
    try:
        if win32gui.IsIconic(hwnd):
            win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        return True
    except Exception as e:
        logging.getLogger(__name__).error(f"restore_window 失败: {e}")
        return False


def capture_window(hwnd: int) -> Optional[Image.Image]:
    """
    后台截图 - 使用PrintWindow API
    
    Args:
        hwnd: 窗口句柄
    
    Returns:
        PIL.Image: 截图图像，失败返回None
    """
    if not hwnd:
        return None
    
    hwndDC = None
    mfcDC = None
    saveDC = None
    saveBitMap = None
    old_bitmap = None
    
    try:
        rect = win32gui.GetWindowRect(hwnd)
        left, top, right, bottom = rect
        width = right - left
        height = bottom - top
        
        if width <= 0 or height <= 0:
            return None
        
        hwndDC = win32gui.GetWindowDC(hwnd)
        if not hwndDC:
            return None
        
        mfcDC = win32ui.CreateDCFromHandle(hwndDC)
        if not mfcDC:
            return None
        
        saveDC = mfcDC.CreateCompatibleDC()
        if not saveDC:
            return None
        
        saveBitMap = win32ui.CreateBitmap()
        saveBitMap.CreateCompatibleBitmap(mfcDC, width, height)
        old_bitmap = saveDC.SelectObject(saveBitMap)
        
        result = ctypes.windll.user32.PrintWindow(hwnd, saveDC.GetSafeHdc(), 2)
        if not result:
            return None
        
        bmpinfo = saveBitMap.GetInfo()
        bmpstr = saveBitMap.GetBitmapBits(True)
        
        img = Image.frombuffer(
            'RGB',
            (bmpinfo['bmWidth'], bmpinfo['bmHeight']),
            bmpstr, 'raw', 'BGRX', 0, 1
        )
        
        return img

    except Exception as e:
        logging.getLogger(__name__).error(f"capture_window 失败: {e}")
        return None

    finally:
        # 先恢复原对象，保证 DeleteObject 成功
        if saveDC and old_bitmap:
            try:
                saveDC.SelectObject(old_bitmap)
            except Exception:
                pass
        
        try:
            if saveBitMap:
                win32gui.DeleteObject(saveBitMap.GetHandle())
        except Exception:
            pass
        
        try:
            if saveDC:
                saveDC.DeleteDC()
        except Exception:
            pass
        
        try:
            if mfcDC:
                mfcDC.DeleteDC()
        except Exception:
            pass
        
        try:
            if hwndDC:
                win32gui.ReleaseDC(hwnd, hwndDC)
        except Exception:
            pass


def capture_window_region(hwnd: int, region: tuple) -> Optional[Image.Image]:
    """
    后台截图指定区域
    
    Args:
        hwnd: 窗口句柄
        region: 区域坐标 (x1, y1, x2, y2)，窗口相对坐标
    
    Returns:
        PIL.Image: 区域截图，失败返回None
    """
    if not hwnd or not region:
        return None
    
    full_image = capture_window(hwnd)
    if full_image is None:
        return None
    
    try:
        x1, y1, x2, y2 = region
        
        x1 = max(0, int(x1))
        y1 = max(0, int(y1))
        x2 = min(full_image.width, int(x2))
        y2 = min(full_image.height, int(y2))
        
        if x2 <= x1 or y2 <= y1:
            return None
        
        return full_image.crop((x1, y1, x2, y2))

    except Exception as e:
        logging.getLogger(__name__).error(f"capture_window_region 失败: {e}")
        return None
    finally:
        full_image.close()


def get_window_size(hwnd: int) -> Optional[Tuple[int, int]]:
    """
    获取窗口尺寸
    
    Args:
        hwnd: 窗口句柄
    
    Returns:
        tuple: (width, height)，失败返回None
    """
    try:
        rect = win32gui.GetWindowRect(hwnd)
        return (rect[2] - rect[0], rect[3] - rect[1])
    except Exception as e:
        logging.getLogger(__name__).error(f"get_window_size 失败: {e}")
        return None


def get_window_class_name(hwnd: int) -> Optional[str]:
    """
    获取窗口类名

    Args:
        hwnd: 窗口句柄

    Returns:
        str: 类名，失败返回 None
    """
    try:
        return win32gui.GetClassName(hwnd)
    except Exception as e:
        logging.getLogger(__name__).error(f"get_window_class_name 失败: {e}")
        return None


def get_window_process_name(hwnd: int) -> Optional[str]:
    """
    获取窗口所属进程名（不含路径）

    通过 GetWindowThreadProcessId + OpenProcess + GetModuleBaseName 获取。
    优先用 PROCESS_QUERY_LIMITED_INFORMATION（Vista+），失败回退到 CreateToolhelp32Snapshot。

    Args:
        hwnd: 窗口句柄

    Returns:
        str: 进程名（如 "MuMuPlayer.exe"），失败返回 None
    """
    from ctypes import wintypes

    try:
        pid = wintypes.DWORD()
        ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if not pid.value:
            return None

        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        handle = ctypes.windll.kernel32.OpenProcess(
            PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value
        )
        if handle:
            try:
                exe_name = ctypes.create_unicode_buffer(260)
                size = wintypes.DWORD(260)
                psapi = ctypes.windll.psapi
                if psapi.GetModuleBaseNameW(handle, None, exe_name, size):
                    return exe_name.value
            finally:
                ctypes.windll.kernel32.CloseHandle(handle)

        # 回退：通过 CreateToolhelp32Snapshot 枚举进程
        return _get_process_name_by_pid(pid.value)
    except Exception as e:
        logging.getLogger(__name__).error(f"get_window_process_name 失败: {e}")
        return None


def _get_process_name_by_pid(pid: int) -> Optional[str]:
    """通过 CreateToolhelp32Snapshot 按 PID 查进程名"""
    from ctypes import wintypes

    TH32CS_SNAPPROCESS = 0x00000002
    MAX_PATH = 260

    class PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD),
            ("cntUsage", wintypes.DWORD),
            ("th32ProcessID", wintypes.DWORD),
            ("th32DefaultHeapID", ctypes.POINTER(wintypes.ULONG)),
            ("th32ModuleID", wintypes.DWORD),
            ("cntThreads", wintypes.DWORD),
            ("th32ParentProcessID", wintypes.DWORD),
            ("pcPriClassBase", wintypes.LONG),
            ("dwFlags", wintypes.DWORD),
            ("szExeFile", wintypes.CHAR * MAX_PATH),
        ]

    try:
        snapshot = ctypes.windll.kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
        if snapshot == ctypes.c_void_p(-1).value:
            return None

        try:
            pe = PROCESSENTRY32W()
            pe.dwSize = ctypes.sizeof(PROCESSENTRY32W)
            if not ctypes.windll.kernel32.Process32FirstW(snapshot, ctypes.byref(pe)):
                return None

            while True:
                if pe.th32ProcessID == pid:
                    return pe.szExeFile.decode("utf-8", errors="replace")
                if not ctypes.windll.kernel32.Process32NextW(snapshot, ctypes.byref(pe)):
                    break
            return None
        finally:
            ctypes.windll.kernel32.CloseHandle(snapshot)
    except Exception as e:
        logging.getLogger(__name__).error(f"_get_process_name_by_pid 失败: {e}")
        return None


def find_window_by_class_and_process(class_name: str, process_name: str) -> Optional[int]:
    """
    通过类名+进程名查找窗口

    枚举所有可见窗口，先按类名过滤，再按进程名过滤。
    返回第一个匹配的窗口句柄。

    Args:
        class_name: 窗口类名
        process_name: 进程名（不含路径）

    Returns:
        int: 窗口句柄，未找到返回 None
    """
    if not class_name:
        return None

    candidates = []

    def enum_callback(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return True

        cls = win32gui.GetClassName(hwnd)
        if cls and cls.lower() == class_name.lower():
            if process_name:
                proc = get_window_process_name(hwnd)
                if proc and proc.lower() == process_name.lower():
                    candidates.append(hwnd)
                    return False  # 找到即停
            else:
                candidates.append(hwnd)
                return False
        return True

    try:
        win32gui.EnumWindows(enum_callback, None)
    except Exception as e:
        logging.getLogger(__name__).error(f"find_window_by_class_and_process 失败: {e}")
        return None

    return candidates[0] if candidates else None
