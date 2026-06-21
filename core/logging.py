import datetime
import os
import threading
from collections import deque

from PySide6.QtCore import QTimer, Qt


class LoggingManager:
    MAX_LOG_LINES = 500
    GUI_UPDATE_INTERVAL = 50

    def __init__(self, app):
        self.app = app
        self._log_buffer = deque(maxlen=self.MAX_LOG_LINES)
        self._gui_update_pending = False
        self._pending_logs = []
        self._update_lock = threading.Lock()
        self.log_callback = None
        self.error_callback = None
        self.clear_callback = None
        self._flush_timer = QTimer()
        self._flush_timer.setSingleShot(True)
        self._flush_timer.timeout.connect(self._flush_gui_updates)

        log_dir = os.path.dirname(self.app.log_file_path)
        os.makedirs(log_dir, exist_ok=True)
        self._debug_log_path = os.path.join(log_dir, "sightly_debug.log")
        self._debug_lock = threading.Lock()
        self._error_log_path = os.path.join(log_dir, "sightly_error.log")
        self._error_lock = threading.Lock()
    
    def debug(self, tag, message):
        """写入调试日志文件（仅文件，不显示在控制台/UI）"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        debug_entry = f"[{timestamp}] [{tag}] {message}\n"
        try:
            with self._debug_lock:
                with open(self._debug_log_path, 'a', encoding='utf-8') as f:
                    f.write(debug_entry)
        except Exception as exc:
            print(f"[LOGGING] 写入调试日志失败: {exc}")

    def error(self, tag, message):
        """记录错误日志（写入 error 日志文件 + 主日志文件 + GUI 红色显示）"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        entry = f"[{timestamp}] [{tag}] {message}\n"
        try:
            with self._error_lock:
                with open(self._error_log_path, 'a', encoding='utf-8') as f:
                    f.write(entry)
        except Exception as exc:
            print(f"[LOGGING] 写入错误日志失败: {exc}")
        try:
            with open(self.app.log_file_path, 'a', encoding='utf-8') as f:
                f.write(entry)
        except Exception as exc:
            print(f"[LOGGING] 写入主日志失败: {exc}")
        if self.error_callback:
            QTimer.singleShot(0, lambda: self.error_callback(entry.rstrip('\n')))
    
    def log_message(self, message):
        """
        记录日志信息（线程安全）
        Args:
            message: 要记录的日志消息
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"

        try:
            with open(self.app.log_file_path, 'a', encoding='utf-8') as f:
                f.write(log_entry)
        except Exception as e:
            print(f"写入日志文件失败: {str(e)}")

        with self._update_lock:
            self._log_buffer.append(log_entry)
            self._pending_logs.append(log_entry)
            
            if not self._gui_update_pending:
                self._gui_update_pending = True
                self._flush_timer.start(self.GUI_UPDATE_INTERVAL)
    
    def _flush_gui_updates(self):
        """
        批量刷新GUI日志（合并多次更新为一次）
        """
        with self._update_lock:
            logs_to_write = self._pending_logs.copy()
            self._pending_logs.clear()
            self._gui_update_pending = False
        
        if not logs_to_write:
            return
        
        # 使用 log_callback 更新 UI（已通过 QTimer.singleShot 保证线程安全）
        if self.log_callback:
            for log_entry in logs_to_write:
                self.log_callback(log_entry.rstrip('\n'))
    
    def clear_log(self):
        """清除日志"""
        with self._update_lock:
            self._log_buffer.clear()
            self._pending_logs.clear()
        
        if self.clear_callback:
            self.clear_callback()
