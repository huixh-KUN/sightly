# async-module-groups Specification

## Purpose
将模块的线程模型从「每组一个线程」重构为「每模块 1 线程 + asyncio 事件循环 + ThreadPoolExecutor」，降低内存/CPU 开销，提升扩展性，统一停止机制。

## Requirements

### Requirement: 每模块独立事件循环

每个模块 SHALL 在自己的线程中运行一个独立的 asyncio 事件循环。

#### Scenario: 启动事件循环
- **WHEN** 模块 `start()` 被调用
- **THEN** 模块创建一个 daemon 线程
- **THEN** 线程内调用 `asyncio.run(self._run_all_groups())`
- **THEN** `_run_all_groups()` 为每个已启用的组创建一个 `asyncio.Task`
- **THEN** `await asyncio.gather(*tasks)` 等待所有协程

#### Scenario: 停止事件循环
- **WHEN** 模块 `stop()` 被调用
- **THEN** 调用 `asyncio.all_tasks(loop).cancel()` 取消所有协程
- **THEN** 每个协程捕获 `CancelledError` 并清理资源
- **THEN** 线程 join（超时 3 秒）

#### Scenario: 协程异常
- **WHEN** 某个组的协程抛出未捕获异常
- **THEN** 其他组的协程不受影响（`asyncio.gather(return_exceptions=True)`）
- **THEN** 记录错误日志
- **THEN** 该组停止运行

---

### Requirement: CPU 密集任务放 ThreadPoolExecutor

截图、OpenCV 模板匹配、OCR 识别等 CPU 密集/阻塞操作 SHALL 通过 `run_in_executor` 放全局 `ThreadPoolExecutor`。

#### Scenario: 截图操作
- **WHEN** 协程需要截图
- **THEN** 调用 `await loop.run_in_executor(executor, screenshot_manager.get_region_screenshot, region, priority)`
- **THEN** `screenshot_manager.get_region_screenshot` 在线程池中执行
- **THEN** 协程在截图完成前让出事件循环（不阻塞其他协程）

#### Scenario: OpenCV 模板匹配
- **WHEN** 协程需要匹配图像
- **THEN** 调用 `await loop.run_in_executor(executor, cv2.matchTemplate, image, template, method)`
- **THEN** 匹配结果返回协程继续处理

#### Scenario: 全局 ThreadPoolExecutor 配置
- **GIVEN** 默认 `max_workers=4`
- **WHEN** 多个模块同时提交 CPU 任务
- **THEN** 任务在 `ThreadPoolExecutor` 中排队执行
- **THEN** 执行器在所有模块间共享

---

### Requirement: 鼠标操作串行队列

所有模块的鼠标点击操作 SHALL 通过全局 `asyncio.Queue` 串行执行。

#### Scenario: 鼠标点击流程
- **WHEN** 协程需要执行鼠标点击
- **THEN** 创建 `(x, y, button)` 指令
- **THEN** `await mouse_queue.put(x, y, button)` 将指令放入队列
- **THEN** `mouse_queue.worker()` 协程从队列取出指令
- **THEN** 通过 `run_in_executor` 调用 `InputController.click()`
- **THEN** 执行完毕后 `asyncio.sleep(0.05)` 防止操作过快

#### Scenario: 多模块并发点击
- **WHEN** 多个模块同时触发鼠标点击
- **THEN** 所有点击指令进入同一队列
- **THEN** 按入队顺序依次串行执行
- **THEN** 两个点击之间至少有 50ms 间隔

---

### Requirement: 统一停止机制

所有模块 SHALL 统一使用 `asyncio.Task.cancel()` 停止协程，替代现有的标志位/Event 混合模式。

#### Scenario: 单个模块停止
- **WHEN** 用户点击某个模块的停止按钮
- **THEN** 模块遍历 `asyncio.all_tasks(loop)`（排除当前协程）
- **THEN** 调用 `task.cancel()`
- **THEN** 每个协程在 `await` 点触发 `CancelledError`
- **THEN** 协程在 `except CancelledError` 中清理资源并退出

#### Scenario: 全部停止
- **WHEN** 用户点击全部停止按钮
- **THEN** 对所有已启动模块逐一调用 `stop()`
- **THEN** 每个模块的协程被取消
- **THEN** 所有线程完成 join

#### Scenario: 协程内部清理
- **WHEN** 协程收到 `CancelledError`
- **THEN** 协程记录日志「组 X 已停止」
- **THEN** 协程退出，不阻塞其他协程

---

### Requirement: PriorityLock 兼容

现有 PriorityLock SHALL 保留但通过 `run_in_executor` 从协程中间接调用。

#### Scenario: 协程内获取优先级锁
- **WHEN** 协程需要获取截图或输入资源的优先级锁
- **THEN** 调用 `await loop.run_in_executor(executor, lock.acquire, priority)`
- **THEN** `lock.acquire` 在独立线程中执行
- **THEN** 协程等待锁释放后继续
- **THEN** 释放锁操作同样通过 `run_in_executor` 调用

---

### Requirement: 配置向后兼容

改造后配置格式 SHALL 与改造前完全兼容，不引入新的必选字段。

#### Scenario: 加载旧配置
- **WHEN** 加载旧版 `config.json`
- **THEN** 所有模块按原有配置正常运行
- **THEN** 不产生任何额外错误日志

#### Scenario: 保存新配置
- **WHEN** 保存面板配置
- **THEN** 配置格式与改造前一致（不新增字段）
- **THEN** 可被改造前的代码正确加载

---

### Requirement: 分阶段实施

改造 SHALL 分四个阶段进行，每个阶段可独立合并和测试。

#### Scenario: Phase 1 验收
- **GIVEN** 仅 Background 模块完成改造
- **WHEN** 启动应用
- **THEN** Background 模块正常启动（协程模式）
- **THEN** 其他模块保持原线程模式
- **THEN** 所有模块同时运行互不干扰

#### Scenario: Phase 2 验收
- **GIVEN** Background + Number + Timed 完成改造
- **WHEN** 启动应用
- **THEN** 三个模块均以协程模式运行
- **THEN** OCR/Image/Color 保持原线程模式
- **THEN** 全部开始/停止功能正常

#### Scenario: Phase 3 验收
- **GIVEN** 所有模块完成改造
- **WHEN** 启动应用
- **THEN** 所有模块以协程模式运行
- **THEN** ThreadManager 统一管理所有模块线程
- **THEN** 内存占用较改造前降低 80%+

---

### Requirement: 性能基准

改造完成后 SHALL 进行性能基准对比。

#### Scenario: 内存对比
- **GIVEN** 10 组、50 组、100 组三种配置
- **WHEN** 全部模块启动运行 5 分钟
- **THEN** 记录内存占用（MB）
- **THEN** 100 组场景内存占用较改造前降低 80%+

#### Scenario: CPU 对比
- **GIVEN** 10 组、50 组、100 组三种配置
- **WHEN** 全部模块运行 5 分钟
- **THEN** 记录 CPU 占用率
- **THEN** 100 组场景 CPU 占用较改造前降低 50%+

#### Scenario: 启动时间对比
- **GIVEN** 10 组配置
- **WHEN** 点击全部开始
- **THEN** 启动时间较改造前降低 50%+

---

### Requirement: 不受影响的模块

以下模块 SHALL 不纳入本次改造范围。

#### Scenario: Script 模块保持原样
- **GIVEN** `modules/script.py`
- **WHEN** 改造完成后
- **THEN** 该模块的线程模型不变
- **THEN** 其功能不受改造影响

#### Scenario: Alarm 模块保持原样
- **GIVEN** `modules/alarm.py`
- **WHEN** 改造完成后
- **THEN** 该模块代码不变
- **THEN** 其功能不受改造影响