## Context

当前所有识别模块（OCR/Number/Image/Color/Background）都在无限循环中运行，每轮循环创建：
1. PIL Image（截图、预处理后的图像）— 持有底层 GDI 句柄，仅靠 `del`/GC 无法回收
2. numpy 数组（cv2 处理的中间结果）
3. ONNX 推理张量（RapidOCR 内部）

这些对象创建后没有显式释放，完全依赖 Python GC。在高频循环场景下，GC 无法及时触发。更严重的是 PIL Image 的底层 GDI 资源必须通过 `.close()` 显式释放，`del` 只减少 Python 引用计数，无法归还 GDI 句柄。

此前已实施 `del` 释放（Phase 1）和 `gc.collect()` 触发（部分 Phase 2），但**两项关键修复遗漏**：
- `ScreenshotManager` 缓存 `last_full_screenshot` 切换时从未调用 PIL `.close()` — 这是最大泄漏源
- 各模块拿到截图后只 `del` 不 `.close()` — GDI 句柄持续增长

## Goals / Non-Goals

**Goals:**
- 消除图像资源泄漏（含 PIL GDI 句柄），内存占用稳定在合理范围（<300MB）
- 提供内存监控工具，便于开发和调试
- 最小化性能影响（GC 耗时 <50ms/次）

**Non-Goals:**
- 不引入新的外部依赖（如 psutil）
- 不改变现有架构和模块职责
- 不优化 RapidOCR 内部内存管理（超出范围）

## Decisions

### 1. 采用四层修复策略

```
Layer 0: 截图管理器层（根因修复）
  utils/screenshot.py - PIL .close() 释放缓存，新旧切换关闭旧对象

Layer 1: 工具函数层（自动释放临时对象）
  utils/image.py      - del gray, enhanced, denoised
  utils/recognition.py - del img_array, screenshot_cv

Layer 2: 模块循环层（释放截图和预处理图像 + GDI 句柄）
  modules/*.py - finally 块释放 + screenshot.close()

Layer 3: 内存监控层（定期 GC + 告警）
  utils/memory.py - MemoryMonitor 类
```

**理由**：四层各司其职，从截图产生的源头到使用末端全覆盖。Layer 0 是本次新增的根因修复，没有它其余三层无法阻止 GDI 句柄泄漏。

### 2. PIL `.close()` 契约

```python
# ScreenshotManager 内部：新旧缓存切换时关闭旧对象
old = self.last_full_screenshot
self.last_full_screenshot = ImageGrab.grab(all_screens=True)
if old is not None:
    old.close()

# 模块调用方：使用完毕后关闭
screenshot = self.screenshot_manager.get_region_screenshot(...)
try:
    # 处理逻辑
finally:
    screenshot.close()
    del screenshot
```

PIL `Image.close()` 释放底层 GDI 资源（DC/位图句柄），这是 `del` 做不到的。只 `del` 不 `.close()` = GDI 泄漏。

### 3. GC 时机：轮次触发 + 内存阈值

```python
# 每 20 轮触发一次 GC
if frame_count % 20 == 0:
    gc.collect()

# 内存超过 300MB 时触发 GC（可选，需要 ctypes 调用 Windows API）
```

**理由**：轮次触发简单可靠，不引入外部依赖；内存阈值作为补充机制，可在后续迭代中添加。

### 4. gc.collect() 在线程池中执行

所有识别逻辑都通过 `run_in_executor` 在线程池中执行，`gc.collect()` 也在其中，不会阻塞事件循环。

```
事件循环 (asyncio)          线程池 (ThreadPoolExecutor)
     │                              │
     │  await run_in_executor()     │
     │ ─────────────────────────▶  │
     │                              │  执行识别
     │                              │  gc.collect()  ← 阻塞在线程池，不影响事件循环
     │ ◀─────────────────────────  │
     │  返回结果                    │
```

### 5. 资源释放顺序

```python
def process_frame(screenshot):
    try:
        processed = _preprocess_image(screenshot)
        result = OCRRecognizer.get_text(processed)
        return result
    finally:
        if processed is not None:
            del processed
        if screenshot is not None:
            screenshot.close()
            del screenshot
```

**理由**：先释放处理后的图像（numpy 数组），再关闭原始截图（PIL GDI 句柄），最后 `del` 清理引用。

### 6. `cv2.imread` 显式释放

```python
cv_template = cv2.imread(tmp)
# 使用完毕后
os.remove(tmp)
# cv_template 用完需要显式 del
```

OpenCV 的 `imread` 返回的 numpy 数组底层绑定 C++ Mat 内存，`del` 确保 C++ 内存尽早归还。

## Risks / Trade-offs

- [性能影响] → gc.collect() 耗时 10-100ms，每 20 轮触发一次，对识别频率影响 <5%
- [过度释放] → del 只是减少引用计数，如果对象被其他引用持有，不会立即释放
- [内存监控精度] → 不使用 psutil，通过 ctypes 调用 Windows API 获取内存信息，精度略低
- [兼容性] → PIL `.close()` 从 PIL 6.0+ 支持，当前依赖 10.0+ 无兼容问题

## Implementation Plan

### Phase 0: 截图管理器层（高风险—根因修复）
- 重构 `utils/screenshot.py`：新旧缓存切换时调用 `.close()`
- `clear_cache()` 释放旧缓存后再置 None
- 返回 PIL 对象的使用方契约文档化

### Phase 1: 工具函数层（低风险）✅ 已完成
- 修改 `utils/image.py`：添加临时变量释放
- 修改 `utils/recognition.py`：添加临时变量释放

### Phase 2: 模块循环层 + GDI 释放（中风险）
- 修改 `modules/ocr.py`：添加 finally 块 + PIL `.close()`
- 修改 `modules/number.py`：添加 finally 块 + PIL `.close()`
- 修改 `modules/image.py`：添加 finally 块 + PIL `.close()`
- 修改 `modules/color.py`：添加 finally 块 + PIL `.close()`
- 修改 `modules/background.py`：添加 finally 块 + `cv2.imread` 释放

### Phase 3: 内存监控层（低风险）⚠️ 此前标记完成但实际未实现
- 新建 `utils/memory.py`：MemoryMonitor 类
- 在各模块中集成 MemoryMonitor

### Phase 4: 验证
- 运行程序 2 小时，观察内存占用趋势
- 检查日志确认 GC 触发和内存释放
