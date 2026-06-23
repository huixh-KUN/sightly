## Context

当前项目（灵眸/Sightly）是一个 Windows 桌面自动化工具，基于 PySide6 构建 GUI，提供 OCR 文字识别、图像检测、颜色识别、定时按键、后台窗口监控等功能。

**当前线程模型**:
- 每个监控组创建一个 `threading.Thread`
- 使用 `PriorityLock`（基于 `threading.Condition`）管理截图和输入资源竞争
- 停止机制不一致：部分用 `is_running` 标志位，部分用 `threading.Event`
- 典型场景：5 组数字 + 5 组定时 + 5 组后台 = 至少 15 个线程

**核心组件**:
- `ScreenshotManager`: 单例 + PriorityLock，全局截图资源共享
- `InputController`: PriorityLock，输入操作串行化
- `ClickHandler`: 同步调用 InputController
- `PriorityLock`: 基于堆的优先级互斥锁

## Goals / Non-Goals

**Goals:**
- 将监控模块从 `threading.Thread` 迁移到 `asyncio` 协程
- 每模块 1 线程 + asyncio 事件循环，监控组作为协程
- CPU 密集任务（OpenCV/OCR）通过 `run_in_executor` 放线程池
- 鼠标操作通过 `asyncio.Queue` 串行执行
- 内存降低 80%+，CPU 降低 50%，扩展性从 ~100 组提升至 2000+ 组
- 保持现有功能完全兼容，不影响 UI 层

**Non-Goals:**
- 不修改 `modules/script.py`（后续单独重构）
- 不修改 UI 层（`ui/*.py`）
- 不修改 `utils/recognition.py`（纯函数，无线程逻辑）
- 不引入新的第三方依赖（仅使用 Python 标准库 `asyncio`）
- 不改变优先级体系（Number:6 > Timed:5 > Image:4 > OCR:3 > Color:2 > BG:1）

## Decisions

### Decision 1: 每模块独立事件循环 vs 全局单事件循环

**选择**: 每模块独立事件循环

**理由**:
- 模块间相互独立，一个模块的异常不影响其他模块
- 每模块可独立启停，粒度更细
- 避免全局事件循环的单点故障
- 与现有 ThreadManager 的模块管理模型一致

### Decision 2: 保留 PriorityLock vs 替换为 asyncio.Lock

**选择**: 保留 PriorityLock，协程内通过 `run_in_executor` 调用

**理由**:
- PriorityLock 的优先级机制是核心功能，不能丢弃
- `asyncio.Lock` 不支持优先级
- 通过 `run_in_executor` 包装，既保留优先级又不阻塞事件循环
- 改动最小，风险最低

### Decision 3: 全局鼠标队列 vs 每模块独立队列

**选择**: 全局 `asyncio.Queue`

**理由**:
- 鼠标是全局唯一资源，必须全局串行
- 多模块同时点击会乱，必须排队
- `asyncio.Queue` 天然串行，无需额外锁
- `mouse_worker` 协程统一执行，便于管理和日志

### Decision 4: 线程池大小

**选择**: `max_workers=4`

**理由**:
- OpenCV 和 OCR 都是 CPU 密集，4 个线程足够利用多核
- 太大会增加线程切换开销
- 太小会导致任务排队等待
- 可根据实际性能测试调整

## Risks / Trade-offs

### Risk 1: PriorityLock 在协程中的兼容性
- **风险**: `threading.Condition` 在协程中使用可能导致死锁
- **缓解**: 所有 PriorityLock 调用通过 `run_in_executor` 包装，不直接在协程中使用

### Risk 2: PySide6 信号集成
- **风险**: 协程内不能直接 emit Qt 信号
- **缓解**: 使用 `loop.call_soon_threadsafe()` 或 `QTimer.singleShot()` 回到主线程

### Risk 3: 第三方库兼容性
- **风险**: `pyautogui`、`pynput` 是同步 API
- **缓解**: 通过 `run_in_executor` 包装，不直接在协程中调用

### Risk 4: 调试难度
- **风险**: asyncio 调试比线程复杂
- **缓解**: 使用 `asyncio.run()` 的 `debug=True` 模式，添加详细的日志记录

### Trade-off: 改动范围 vs 性能收益
- **改动**: 8 个文件必须修改，4 个文件需要适配
- **收益**: 内存降低 80%+，CPU 降低 50%，扩展性提升 20x
- **结论**: 收益远大于改动成本
