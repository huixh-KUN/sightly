## Context

每个模块一个 dedicated 线程，模块内每组再一个线程。Number/Timed/Background 等模块用户可配置 N 组，导致 N 个线程并行运行。典型场景 15 线程，扩展到 1000+ 线程时内存和 CPU 不可接受。

核心架构变化：
```
当前: 模块线程 → 每组一个线程 → PriorityLock → 截图/识别/点击
目标: 模块线程 → asyncio 事件循环 → 协程组 → run_in_executor → ThreadPoolExecutor → 鼠标队列
```

## Goals / Non-Goals

**Goals:**
- 每个模块 1 个线程 + asyncio 事件循环，每组变成协程（~KB 级）
- CPU 密集任务（截图、OpenCV、OCR）通过 `run_in_executor` 放 `ThreadPoolExecutor`
- 鼠标点击通过 `asyncio.Queue` 全局串行执行
- 统一停止机制为 `asyncio.Task.cancel()`
- 保留 `PriorityLock` 及现有优先级竞争逻辑（通过 `run_in_executor` 调用）
- 分阶段改造，每个阶段可独立测试和验证

**Non-Goals:**
- 不改动 `modules/script.py`（后续重构）
- 不改动 `modules/alarm.py`（纯工具类，无线程逻辑）
- 不改动 `ui/*.py`（UI 层不涉及线程模型）
- 不改变现有配置格式和 UI 交互
- 不引入第三方 asyncio 框架（仅用标准库）

## Decisions

### D1: 每模块独立事件循环

每个模块在自己的线程中运行一个独立的 asyncio 事件循环，而不是全局共享一个事件循环。

```
class NumberModule:
    def start(self):
        def _run():
            asyncio.run(self._run_all_groups())
        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()
    
    async def _run_all_groups(self):
        tasks = [self._group_loop(i, g) for i, g in enumerate(self.groups) if g["enabled"]]
        await asyncio.gather(*tasks)
```

**理由：**
- 模块之间天然隔离，一个模块的协程异常不影响其他模块
- 无需全局事件循环的线程安全问题
- 停止单个模块只需 `asyncio.all_tasks(loop).cancel()` + 关闭 loop
- 保持现有 `ThreadManager` 的线程生命周期管理不变

### D2: CPU 密集任务放 ThreadPoolExecutor

截图 (`PIL.ImageGrab.grab`)、OpenCV 模板匹配 (`cv2.matchTemplate`)、OCR 识别 (`rapidocr`) 等 CPU/阻塞操作通过 `run_in_executor` 放线程池。

```python
async def _screenshot(self, region, priority):
    return await asyncio.get_event_loop().run_in_executor(
        self._executor, self.screenshot_manager.get_region_screenshot, region, priority
    )

async def _recognize(self, image, template):
    return await asyncio.get_event_loop().run_in_executor(
        self._executor, cv2.matchTemplate, image, template, cv2.TM_CCOEFF_NORMED
    )
```

**全局 `ThreadPoolExecutor(max_workers=4)`**：共享给所有模块，避免每个模块独立创建线程池。

### D3: 鼠标操作 via asyncio.Queue 串行

全局 `MouseQueue` 用 `asyncio.Queue` 排队所有模块的鼠标点击请求，一个 worker 协程串行执行。

```python
class MouseQueue:
    def __init__(self):
        self._queue = asyncio.Queue()
    
    async def worker(self):
        while True:
            x, y, button = await self._queue.get()
            await asyncio.get_event_loop().run_in_executor(
                None, self._input_controller.click, x, y
            )
            await asyncio.sleep(0.05)
    
    async def put(self, x, y, button='left'):
        await self._queue.put((x, y, button))
```

### D4: PriorityLock 适配

`threading.Condition` 不能在协程内直接调用。保留 PriorityLock 的现有实现，协程内通过 `run_in_executor` 包装。

```python
async def get_screenshot(self, region, priority):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        self._executor,
        lambda: self.screenshot_manager.get_region_screenshot(region, priority)
    )
```

### D5: 协程生命周期管理

每个模块的 `_run_all_groups()` 创建 N 个 `asyncio.Task`（每组一个）。停止时：

```python
def stop(self):
    if self._thread and self._thread.is_alive():
        for task in asyncio.all_tasks(loop=self._loop):
            task.cancel()
        self._loop.call_soon_threadsafe(self._loop.stop)
```

- `cancel()` 会触发 `asyncio.CancelledError`，协程内需捕获并优雅退出
- 每组独立 Task，停止单个组时只需 `task.cancel()`，不影响其他组

### D6: 模块间信号/UI 通信

协程内不能直接 emit PySide6 信号。统一通过 `loop.call_soon_threadsafe()` 在主线程调度。

```python
def _on_match(self, group_index):
    self.app.logging_manager.log_message(f"组 {group_index} 匹配成功")
```

所有 UI 更新和日志都在协程之外（或通过线程安全方式）调用。

### D7: 分阶段实施

| 阶段 | 模块 | 目的 |
|------|------|------|
| 1 | Background | 试点，组最多，问题最明显 |
| 2 | Number + Timed | 扩展，同类 N 组 1 线程模式 |
| 3 | OCR + Image + Color | 统一，单线程循环改造 |
| 4 | 清理 | 移除旧代码 + 回归 |

每个阶段产出可独立合并和测试。

## Risks / Trade-offs

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| PriorityLock 协程兼容 | 协程内不能直接 `threading.Lock` | 通过 `run_in_executor` 调用，保留原逻辑 |
| PySide6 信号集成 | 协程内不能直接 `emit` | 用 `loop.call_soon_threadsafe()` 在 UI 线程调度 |
| 第三方库同步 API | pyautogui/pynput 阻塞 | 统一 `run_in_executor` 包装 |
| 调试难度 | asyncio 调试比线程复杂 | 使用 `asyncio.run(debug=True)`；保留详细日志 |
| 协程泄露 | Task 未正确清理 | 模块停止时遍历 `asyncio.all_tasks()` 确保全部取消 |
| ThreadPoolExecutor 饱和 | 4 worker 不够时任务排队 | 可配置 `max_workers`；观察 CPU 利用率动态调整 |
| 协程内 sleep 精度 | `asyncio.sleep` 可能不准 | 短 sleep 用 `asyncio.sleep`，长 sleep 用循环检查 |
| 旧配置兼容 | 旧 config.json 无新字段 | 字段可选，默认值兼容旧版行为 |
