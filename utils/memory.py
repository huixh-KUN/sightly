import gc
import ctypes
from ctypes import wintypes


class MemoryMonitor:
    def __init__(self, gc_interval=20, memory_threshold_mb=300, log_func=None):
        self.gc_interval = gc_interval
        self.memory_threshold_mb = memory_threshold_mb
        self._log = log_func

    @staticmethod
    def get_memory_usage():
        try:
            kernel32 = ctypes.windll.kernel32
            PROCESS_MEMORY_COUNTERS = (ctypes.c_ulong * 18)()
            pid = ctypes.windll.kernel32.GetCurrentProcess()
            handle = kernel32.OpenProcess(0x0400 | 0x0010, False, pid)
            if handle:
                kernel32.GetProcessMemoryInfo(handle, ctypes.byref(PROCESS_MEMORY_COUNTERS),
                                              ctypes.sizeof(PROCESS_MEMORY_COUNTERS))
                kernel32.CloseHandle(handle)
                return PROCESS_MEMORY_COUNTERS[8] / (1024 * 1024)
            return 0.0
        except Exception:
            return 0.0

    def gc_if_needed(self, frame_count):
        if frame_count % self.gc_interval == 0:
            gc.collect()
            return True
        usage = self.get_memory_usage()
        if usage > self.memory_threshold_mb:
            gc.collect()
            return True
        return False

    def log_memory_status(self, tag):
        usage = self.get_memory_usage()
        if self._log:
            self._log(tag, f"内存使用: {usage:.1f}MB")
