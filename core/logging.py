import datetime
import os
import threading
from collections import deque

from PySide6.QtCore import QTimer


class LoggingManager:
    MAX_LOG_LINES = 500

    def __init__(self, app):
        self.app = app
        self._log_buffer = deque(maxlen=self.MAX_LOG_LINES)
        self._pending_logs = []
        self._update_lock = threading.Lock()
        self.log_callback = None
        self.error_callback = None
        self.clear_callback = None

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
            pass

    def error(self, tag, message):
        """记录错误日志（写入 error 日志文件 + 主日志文件 + GUI 红色显示）"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        entry = f"[{timestamp}] [{tag}] {message}\n"
        try:
            with self._error_lock:
                with open(self._error_log_path, 'a', encoding='utf-8') as f:
                    f.write(entry)
        except Exception as exc:
            pass
        try:
            with open(self.app.log_file_path, 'a', encoding='utf-8') as f:
                f.write(entry)
        except Exception as exc:
            pass
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
            pass

        with self._update_lock:
            self._log_buffer.append(log_entry)
            self._pending_logs.append(log_entry)

        QTimer.singleShot(0, self._flush_gui_updates)

    def _flush_gui_updates(self):
        """
        批量刷新GUI日志（QTimer.singleShot 保证在主线程执行）
        """
        with self._update_lock:
            if not self._pending_logs:
                return
            logs_to_write = self._pending_logs.copy()
            self._pending_logs.clear()

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

    def get_log_buffer(self):
        """返回日志缓冲区的快照副本"""
        with self._update_lock:
            return list(self._log_buffer)
