## ADDED Requirements

### Requirement: 鼠标操作串行队列
所有模块的鼠标点击操作必须通过全局 `asyncio.Queue` 串行执行，防止多协程同时操作鼠标导致乱点。

#### Scenario: 单模块点击
- **WHEN** 某个协程检测到目标并需要点击
- **THEN** 将点击坐标放入 `MouseQueue`，由专门的 `mouse_worker` 协程串行执行

#### Scenario: 多模块并发点击
- **WHEN** 多个模块的多个协程同时检测到目标
- **THEN** 所有点击请求在队列中排队，`mouse_worker` 逐个执行，每次点击间隔不少于 50ms

#### Scenario: 点击失败处理
- **WHEN** 鼠标点击操作抛出异常
- **THEN** 异常被记录到日志，队列继续处理下一个请求，不阻塞其他协程

### Requirement: 鼠标队列生命周期
鼠标队列的 `worker` 协程随应用启动，随应用退出。

#### Scenario: 应用启动
- **WHEN** 应用开始运行
- **THEN** 创建 `MouseQueue` 实例，启动 `mouse_worker` 协程

#### Scenario: 应用停止
- **WHEN** 应用停止所有模块
- **THEN** `mouse_worker` 协程在处理完队列中剩余请求后退出
