## memory-monitor

### Purpose

提供内存监控和自动 GC 触发功能，帮助开发者监控程序内存使用情况，并在内存占用过高时自动触发垃圾回收。

### API

```python
class MemoryMonitor:
    """内存监控工具类"""
    
    def __init__(self, gc_interval: int = 20, memory_threshold_mb: int = 300):
        """
        初始化内存监控器
        
        Args:
            gc_interval: 每 N 轮触发一次 GC
            memory_threshold_mb: 内存阈值（MB），超过此值触发 GC
        """
        pass
    
    def get_memory_usage(self) -> float:
        """
        获取当前进程内存使用（MB）
        
        Returns:
            float: 内存使用量（MB）
        """
        pass
    
    def gc_if_needed(self, frame_count: int) -> bool:
        """
        根据轮次或内存阈值触发 GC
        
        Args:
            frame_count: 当前轮次
            
        Returns:
            bool: 是否触发了 GC
        """
        pass
    
    def log_memory_status(self, tag: str) -> None:
        """
        记录内存使用日志
        
        Args:
            tag: 日志标签（如 "OCR", "NUMBER"）
        """
        pass
```

### Usage

```python
# 在模块中使用
from utils.memory import MemoryMonitor

class OCRModule:
    def __init__(self):
        self.memory_monitor = MemoryMonitor(gc_interval=20, memory_threshold_mb=300)
        self.frame_count = 0
    
    def _ocr_group_loop(self, group_index, group):
        while True:
            # ... 执行识别 ...
            
            self.frame_count += 1
            
            # 触发 GC（如果需要）
            if self.memory_monitor.gc_if_needed(self.frame_count):
                self.app.logging_manager.debug("OCR", f"识别组{group_index+1} 触发 GC")
            
            # 记录内存状态（可选）
            if self.frame_count % 100 == 0:
                self.memory_monitor.log_memory_status("OCR")
```

### Implementation Notes

- 使用 `ctypes` 调用 Windows API 获取内存信息，避免引入 `psutil` 依赖
- `gc.collect()` 在线程池中执行，不会阻塞事件循环
- GC 触发时记录日志，便于调试和监控
