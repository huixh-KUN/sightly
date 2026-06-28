## Why

程序长时间运行（1-2小时）后内存持续增长（100M→800M→2GB），最终导致卡顿、闪退。根本原因是图像资源（PIL Image、numpy 数组、ONNX 推理张量）在循环识别过程中不断创建但从未主动释放，完全依赖 Python GC 回收，而 GC 在高频循环场景下无法及时触发。

## What Changes

- **截图管理器层（新增）**：重构 `ScreenshotManager`，新旧缓存切换时显式调用 PIL `.close()` 释放 GDI 资源，`clear_cache()` 同样释放
- **工具函数层**：在 `utils/image.py` 和 `utils/recognition.py` 中添加临时变量显式释放
- **模块循环层**：在所有识别模块（OCR/Number/Image/Color/Background）的循环中添加 `finally` 块释放截图和预处理图像，并对 PIL Image 调用 `.close()`
- **`cv2.imread` 释放**：后台监控模板加载后显式 `del` 释放 OpenCV Mat
- **内存监控层**：新增 `utils/memory.py` 提供 MemoryMonitor 工具类，定期触发 GC 并记录内存使用情况

## Capabilities

### New Capabilities
- `memory-monitor`: 内存监控工具，提供定期 GC 触发和内存使用日志

### Modified Capabilities
- `screenshot-manager`: 截图管理器添加 PIL `.close()` 释放逻辑，消除 GDI 资源泄漏
- `ocr-recognition`: OCR 识别循环添加资源释放 + PIL `.close()`
- `number-recognition`: 数字识别循环添加资源释放 + PIL `.close()`
- `image-detection`: 图像检测循环添加资源释放 + PIL `.close()`
- `color-recognition`: 颜色识别循环添加资源释放 + PIL `.close()`
- `background-monitor`: 后台监控循环添加资源释放 + `cv2.imread` 释放

## Impact

- `utils/screenshot.py`: 重构缓存切换逻辑，添加 PIL `.close()`，`clear_cache()` 释放缓存
- `utils/image.py`: 添加 `del` 释放临时 numpy 数组
- `utils/recognition.py`: 添加 `del` 释放临时 numpy 数组和 PIL 转换副本
- `utils/memory.py`: 新建 MemoryMonitor 类
- `modules/ocr.py`: 循环内添加 `finally` 块 + PIL `.close()`
- `modules/number.py`: 循环内添加 `finally` 块 + PIL `.close()`
- `modules/image.py`: 循环内添加 `finally` 块 + PIL `.close()`
- `modules/color.py`: 循环内添加 `finally` 块 + PIL `.close()`
- `modules/background.py`: 循环内添加 `finally` 块 + `cv2.imread` 释放
