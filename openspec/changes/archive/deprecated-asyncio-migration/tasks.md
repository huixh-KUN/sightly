## 1. 基础设施

- [ ] 1.1 创建 `core/async_utils.py` — asyncio 工具模块，包含 `MouseQueue` 类和辅助函数
- [ ] 1.2 创建 `MouseQueue` 类 — 基于 `asyncio.Queue` 的鼠标串行队列，含 `worker()` 协程和 `put()` 方法
- [ ] 1.3 创建 `run_in_executor` 辅助函数 — 封装 `loop.run_in_executor()` 调用，简化协程内同步调用
- [ ] 1.4 修改 `core/threading.py` — ThreadManager 添加 `start_async()` 方法，支持 asyncio 事件循环线程

## 2. Background 模块试点

- [ ] 2.1 重构 `BackgroundMonitor` — 将 `monitor_thread` 改为 asyncio 事件循环线程
- [ ] 2.2 实现 `_monitor_loop()` 协程 — 替代原 `_monitor_loop()` 线程函数
- [ ] 2.3 截图调用适配 — `capture_window_region()` 通过 `run_in_executor` 异步执行
- [ ] 2.4 识别调用适配 — OCR/Image/Color 识别通过 `run_in_executor` 异步执行
- [ ] 2.5 点击调用适配 — `ClickHandler.execute_click()` 通过 `MouseQueue` 异步执行
- [ ] 2.6 停止机制统一 — 用 `Task.cancel()` 替代 `stop_event.set()`
- [ ] 2.7 重构 `BackgroundManager` — 管理所有组的协程生命周期

## 3. Number + Timed 模块

- [ ] 3.1 重构 `NumberModule` — 每组线程改为 asyncio 协程
- [ ] 3.2 实现 `_group_loop()` 协程 — 替代原 `number_recognition_loop()` 线程函数
- [ ] 3.3 截图/识别适配 — 通过 `run_in_executor` 异步执行
- [ ] 3.4 重构 `TimedModule` — 每组线程改为 asyncio 协程
- [ ] 3.5 实现 `_group_loop()` 协程 — 替代原 `timed_task_loop()` 线程函数
- [ ] 3.6 停止机制统一 — 用 `Task.cancel()` 替代 `threading.Event`

## 4. OCR + Image + Color 模块

- [ ] 4.1 重构 `OCRModule` — 单线程循环改为 asyncio 协程
- [ ] 4.2 实现 `_ocr_loop()` 协程 — 替代原 `ocr_loop()` 线程函数
- [ ] 4.3 重构 `ImageDetection` — 单线程循环改为 asyncio 协程
- [ ] 4.4 实现 `_detect_loop()` 协程 — 替代原 `detect()` 线程函数
- [ ] 4.5 重构 `ColorRecognition` — 单线程循环改为 asyncio 协程
- [ ] 4.6 实现 `_recognize_loop()` 协程 — 替代原 `recognize()` 线程函数

## 5. 全局集成

- [ ] 5.1 修改 `core/state.py` — AppState 启停逻辑适配 asyncio
- [ ] 5.2 创建全局 `ThreadPoolExecutor` — 在 MainWindow 初始化时创建，传入各模块
- [ ] 5.3 创建全局 `MouseQueue` — 在 MainWindow 初始化时创建，传入各模块
- [ ] 5.4 修改 `core/controller.py` — ModuleController 适配 asyncio 启停

## 6. 清理与测试

- [ ] 6.1 移除旧线程管理代码 — 删除 `threading.Event`、`thread.join()` 等旧逻辑
- [ ] 6.2 统一日志 tag — 所有模块使用统一的 `MODULE` tag
- [ ] 6.3 回归测试 — 按 MIGRATION-ASYNC.md 第七节测试清单逐项验证
- [ ] 6.4 性能测试 — 验证内存、CPU、扩展性指标
