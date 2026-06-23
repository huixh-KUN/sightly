## Why

当前线程模型为每模块组 1 个线程（如 Number/Timed/Background 各 5 组 = 15 线程），扩展到 20 模块 × 50 组时将达到 1000+ 线程，导致内存 800MB+、CPU 30%+ 浪费在切换开销上。

关键痛点：
- **线程膨胀**：每组一个线程，1000 组 → 800MB+ 栈空间
- **停止机制不一致**：有的用 `app.is_running`，有的用 `threading.Event`，有的用 `self.is_running`
- **资源竞争复杂**：`PriorityLock` 基于 `threading.Condition`，高并发下内核态切换频繁
- **扩展性受限**：线程创建/销毁成本高，无法支撑大规模配置

## What Changes

- **每个模块 1 线程 + asyncio 事件循环**：每组变成 ~KB 级的协程，而非 ~8MB 的线程
- **CPU 密集任务 → ThreadPoolExecutor**：截图、OpenCV 匹配、OCR 识别通过 `run_in_executor` 放线程池
- **全局鼠标队列**：`asyncio.Queue` 串行执行所有模块的鼠标点击
- **统一停止机制**：`asyncio.Task.cancel()` 替代 `threading.Event` + 标志位混合模式
- **保留 PriorityLock**：协程内通过 `run_in_executor` 调用，不破坏现有优先级竞争逻辑

## Capabilities

### New Capabilities
- `async-module-groups`: 模块操作组协程化，线程 → asyncio + ThreadPoolExecutor

### Modified Capabilities
（无）

## Impact

### Phase 1 — Background 模块（试点）
- `modules/background.py`：线程 → asyncio 协程，每组独立 `asyncio.Task`
- `core/async_utils.py`：新增 asyncio 工具函数（MouseQueue、协程管理）

### Phase 2 — Number + Timed 模块（扩展）
- `modules/number.py`：线程 → asyncio 协程
- `modules/timed.py`：线程 → asyncio 协程

### Phase 3 — OCR + Image + Color 模块（统一）
- `modules/ocr.py`：单线程循环 → asyncio 协程
- `modules/image.py`：单线程循环 → asyncio 协程
- `modules/color.py`：单线程循环 → asyncio 协程
- `core/threading.py`：ThreadManager 支持 asyncio 事件循环
- `core/state.py`：启停逻辑适配 asyncio

### Phase 4 — 清理
- 移除旧的线程管理代码
- 全量回归测试
- 性能基准测试

### 不受影响
- `modules/script.py`（后续重构）
- `modules/alarm.py`（纯工具类）
- `ui/*.py`（UI 层不涉及线程模型）
- `utils/recognition.py`（纯函数）
