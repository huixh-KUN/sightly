## ADDED Requirements

### Requirement: 模块事件循环
每个监控模块必须在独立线程中运行 asyncio 事件循环，管理该模块所有监控组协程。

#### Scenario: 模块启动
- **WHEN** 调用模块的 start 方法
- **THEN** 创建一个 daemon 线程，在线程内启动 asyncio 事件循环，将所有已启用的监控组作为协程提交到事件循环

#### Scenario: 模块停止
- **WHEN** 调用模块的 stop 方法
- **THEN** 取消所有组协程（`Task.cancel()`），等待协程完成清理，线程自然退出

### Requirement: 组协程生命周期
每个监控组作为独立的 asyncio.Task 运行，支持单独取消。

#### Scenario: 单组启动
- **WHEN** 模块事件循环启动
- **THEN** 为每个已启用的监控组创建一个 asyncio.Task，所有 Task 通过 `asyncio.gather()` 并发运行

#### Scenario: 单组停止
- **WHEN** 取消某个组的 Task
- **THEN** 该组协程停止，其他组协程不受影响继续运行

#### Scenario: 异常隔离
- **WHEN** 某个组协程抛出异常
- **THEN** 异常被记录到日志，其他组协程继续运行，不影响模块整体

### Requirement: 协程内同步调用
协程内调用同步阻塞函数（截图、识别、输入）必须通过 `run_in_executor` 放入线程池。

#### Scenario: 截图操作
- **WHEN** 协程需要截取屏幕区域
- **THEN** 通过 `loop.run_in_executor(executor, screenshot_func)` 异步执行，不阻塞事件循环

#### Scenario: OpenCV 匹配
- **WHEN** 协程需要执行模板匹配
- **THEN** 通过 `loop.run_in_executor(executor, cv2.matchTemplate, ...)` 异步执行

#### Scenario: OCR 识别
- **WHEN** 协程需要执行文字识别
- **THEN** 通过 `loop.run_in_executor(executor, ocr_func, ...)` 异步执行
