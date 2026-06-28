## Tasks

### Phase 0: 截图管理器层（根因修复—新增）

- [x] 0.1 重构 `utils/screenshot.py`：新旧缓存切换时释放旧 PIL 对象
  - `get_full_screenshot()`：新截图前调用 `old.close()` 释放旧 `last_full_screenshot`
  - `get_full_screenshot()`：返回 `.copy()` 而非原引用，防止调用方意外 close 破坏缓存
  - `clear_cache()`：调用 `.close()` 释放缓存后再置 None
  - `get_region_screenshot()`：文档注释标注返回的 PIL Image 需要调用方 `.close()`

### Phase 1: 工具函数层 ✅ 已完成

- [x] 1.1 修改 `utils/image.py`：在 `_preprocess_image()` 中添加临时变量释放
  - 添加 `del img_array` 释放原始图像数组
  - 添加 `del gray` 释放灰度图
  - 添加 `del enhanced` 释放增强后的图像
  - 添加 `del denoised` 释放去噪后的图像

- [x] 1.2 修改 `utils/recognition.py`：在识别器中添加临时变量释放
  - `OCRRecognizer.get_text()`：添加 `del img_array`
  - `OCRRecognizer.find_keyword_position()`：添加 `del img_array`
  - `ImageRecognizer.match_template()`：添加 `del screenshot_cv` 和 `del result`
  - `ColorRecognizer.match_color()`：添加 `del img_array` 和 `del sampled_array`
  - `NumberRecognizer.recognize()`：添加 `del img_array`

### Phase 2: 模块循环层 + GDI 释放

- [x] 2.1 修改 `modules/ocr.py`：添加 PIL `.close()`
  - `perform_ocr_for_group_optimized()`：finally 块添加 `screenshot.close()`
  - 已有 `gc.collect()` 保持

- [x] 2.2 修改 `modules/number.py`：添加 PIL `.close()`
  - `ocr_number()` / `take_screenshot()` 调用方：finally 块添加 `screenshot.close()`
  - `_number_group_loop()` L133 `del screenshot` 改为先 `.close()` 再 `del`
  - 已有 `gc.collect()` 保持

- [x] 2.3 修改 `modules/image.py`：添加 PIL `.close()`
  - `detect_image()`：finally 块添加 `screenshot.close()`
  - 已有 `gc.collect()` 保持

- [x] 2.4 修改 `modules/color.py`：添加 PIL `.close()`
  - `recognize_color()`：finally 块添加 `screenshot.close()`
  - 已有 `gc.collect()` 保持

- [x] 2.5 修改 `modules/background.py`：添加 PIL `.close()` + `cv2.imread` 释放
  - `_monitor_async()` L241 `del image` 改为先 `image.close()` 再 `del`
  - `_recognize_ocr()`：finally 块添加 `del processed`
  - `configure_image()` L161 `cv2.imread` 使用完后添加 `del cv_template`
  - `_recognize_image()` / `_recognize_color()`：释放传入的 image（调用方负责）
  - 已有 `gc.collect()` 保持

### Phase 3: 内存监控层 ⚠️ 此前标记完成但实际未实现

- [x] 3.1 新建 `utils/memory.py`：实现 MemoryMonitor 类
  - `get_memory_usage()`：获取当前进程内存使用（通过 ctypes 调用 Windows API）
  - `gc_if_needed()`：根据轮次或内存阈值触发 GC
  - `log_memory_status()`：记录内存使用日志

- [x] 3.2 在各模块中集成 MemoryMonitor
  - 在各模块的循环中调用 `MemoryMonitor.gc_if_needed()`
  - 在 GC 触发时记录日志

### Phase 4: 验证

- [ ] 4.1 运行程序 2 小时，观察内存占用趋势（含 GDI 句柄数监控）
- [ ] 4.2 检查日志确认 GC 触发和内存释放
- [ ] 4.3 验证识别功能正常工作
