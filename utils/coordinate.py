import win32gui
from typing import Optional, Tuple


class RelativeCoordinate:
    """相对比例坐标系统"""
    
    @staticmethod
    def pixel_to_ratio(region: tuple, window_size: tuple) -> Optional[tuple]:
        """
        像素坐标转比例坐标
        
        Args:
            region: (x1, y1, x2, y2) 像素坐标
            window_size: (width, height) 窗口尺寸
        
        Returns:
            tuple: (rx1, ry1, rx2, ry2) 比例坐标 (0.0-1.0)，失败返回None
        """
        if not region or not window_size:
            return None
        
        x1, y1, x2, y2 = region
        win_w, win_h = window_size
        
        if win_w <= 0 or win_h <= 0:
            return None
        
        return (
            x1 / win_w,
            y1 / win_h,
            x2 / win_w,
            y2 / win_h
        )
    
    @staticmethod
    def ratio_to_pixel(ratio_region: tuple, window_size: tuple) -> Optional[tuple]:
        """
        比例坐标转像素坐标
        
        Args:
            ratio_region: (rx1, ry1, rx2, ry2) 比例坐标
            window_size: (width, height) 窗口尺寸
        
        Returns:
            tuple: (x1, y1, x2, y2) 像素坐标，失败返回None
        """
        if not ratio_region or not window_size:
            return None
        
        rx1, ry1, rx2, ry2 = ratio_region
        win_w, win_h = window_size
        
        return (
            int(rx1 * win_w),
            int(ry1 * win_h),
            int(rx2 * win_w),
            int(ry2 * win_h)
        )


class WindowCoordinate:
    """窗口坐标系统工具类"""
    
    @staticmethod
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
        except Exception:
            return None
