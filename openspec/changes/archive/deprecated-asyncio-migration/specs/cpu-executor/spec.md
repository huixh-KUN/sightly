## ADDED Requirements

### Requirement: CPU 密集任务线程池
创建全局 `ThreadPoolExecutor`，用于执行 OpenCV 模板匹配、RapidOCR 识别等 CPU 密集任务，避免阻塞 asyncio 事件循环。

#### Scenario: 线程池配置
- **WHEN** 应用启动
- **THEN** 创建 `ThreadPoolExecutor(max_workers=4)`，作为 CPU 密集任务的执行器

#### Scenario: OpenCV 异步执行
- **WHEN** 协程需要执行 `cv2.matchTemplate`
- **THEN** 通过 `loop.run_in_executor(executor, cv2.matchTemplate, ...)` 执行，事件循环继续处理其他协程

#### Scenario: OCR 异步执行
- **WHEN** 协程需要执行 RapidOCR 识别
- **THEN** 通过 `loop.run_in_executor(executor, ocr_func, ...)` 执行，事件循环继续处理其他协程

### Requirement: 线程池复用
所有模块共享同一个 `ThreadPoolExecutor`，避免重复创建。

#### Scenario: 多模块并发识别
- **WHEN** 多个模块同时需要执行 CPU 密集任务
- **THEN** 所有任务提交到同一个线程池，线程池根据 `max_workers` 调度执行

#### Scenario: 线程池满载
- **WHEN** 线程池任务队列已满
- **THEN** 新任务等待直到有空闲线程，不创建新线程
