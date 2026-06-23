## Phase 1: Background 模块试点

### 1.1 基础设施
- [x] ~~1.1.1~~ 已取消 — `MouseQueue` 不必要，`run_in_executor` + `PriorityLock` 已覆盖
- [x] 1.1.2 `core/async_utils.py` — 全局 `ThreadPoolExecutor` 单例（`max_workers=4`）
- [x] 1.1.3 `core/async_utils.py` — `cancel_all_tasks(loop)` 工具函数

### 1.2 Background 模块改造
- [x] 1.2.1 `modules/background.py` — `start_all_groups()` 改为此模块 1 线程 + `asyncio.run()`
- [x] 1.2.2 `modules/background.py` — 每组 `_group_loop()` 改为 `async def` 协程
- [x] 1.2.3 `modules/background.py` — 截图/识别调用改为 `await run_in_executor()`
- [x] ~~1.2.4~~ 已取消 — 鼠标触发通过 `run_in_executor` + `ClickHandler`，无需 `mouse_queue`
- [x] 1.2.5 `modules/background.py` — 停止逻辑改为 `Task.cancel()` + 捕获 `CancelledError`
- [ ] 1.2.6 验证：背景监控各类型（OCR/图像/颜色）功能正常
- [ ] 1.2.7 验证：多组并发正常运行

## Phase 2: Number + Timed 模块扩展

### 2.1 Number 模块
- [x] 2.1.1 `modules/number.py` — 单线程 + asyncio 事件循环
- [x] 2.1.2 `modules/number.py` — 每组 `_run_group()` 改为协程
- [x] 2.1.3 `modules/number.py` — 识别/触发改为 `await run_in_executor()`
- [x] 2.1.4 `modules/number.py` — 停止逻辑改为 `Task.cancel()`

### 2.2 Timed 模块
- [x] 2.2.1 `modules/timed.py` — 单线程 + asyncio 事件循环
- [x] 2.2.2 `modules/timed.py` — 每组 `_run_tasks()` 改为协程
- [x] 2.2.3 `modules/timed.py` — 停止逻辑改为 `Task.cancel()`

### 2.3 多模块并发测试
- [ ] 2.3.1 验证 Number + Timed 同时运行正常
- [ ] 2.3.2 验证与 Background 同时运行正常
- [ ] 2.3.3 验证全部开始/全部停止功能正常

## Phase 3: OCR + Image + Color 模块统一

### 3.1 OCR 模块
- [x] 3.1.1 `modules/ocr.py` — 单线程循环 → asyncio 协程
- [x] 3.1.2 `modules/ocr.py` — OCR 识别改为 `await run_in_executor()`
- [x] 3.1.3 `modules/ocr.py` — 停止改为 `Task.cancel()`

### 3.2 Image 模块
- [x] 3.2.1 `modules/image.py` — 单线程循环 → asyncio 协程
- [x] 3.2.2 `modules/image.py` — OpenCV 匹配改为 `await run_in_executor()`
- [x] 3.2.3 `modules/image.py` — 停止改为 `Task.cancel()`

### 3.3 Color 模块
- [x] 3.3.1 `modules/color.py` — 单线程循环 → asyncio 协程
- [x] 3.3.2 `modules/color.py` — 颜色检测改为 `await run_in_executor()`
- [x] 3.3.3 `modules/color.py` — 停止改为 `Task.cancel()`

### 3.4 ThreadManager 适配
- [x] ~~3.4.1~~ 已取消 — 各模块自管理 `_thread` + `_loop`，`ThreadManager` 无调用者
- [x] ~~3.4.2~~ 已取消 — `AppState` 仅负责信号/配置分发，不直接管线程

## Phase 4: 清理与回归

### 4.1 清理
- [x] 4.1.1 移除模块中旧线程管理代码（`threading.Thread` 直接创建）
- [x] 4.1.2 协程层已统一 `Task.cancel()`（executor 内保留 `app.is_running` 作为安全守卫，合理）
- [x] 4.1.3 统一各组 `Event` 停止信号为 `CancelledError` 模式

### 4.2 回归测试
- [ ] 4.2.1 基础功能：单模块启停、全部开始/停止、工作空间切换
- [ ] 4.2.2 OCR 模块：单组识别、多组识别、识别间隔、关键词匹配
- [ ] 4.2.3 数字识别：单组识别、多组识别、阈值触发、置信度过滤
- [ ] 4.2.4 定时任务：单组定时、多组定时、不同间隔、按键触发
- [ ] 4.2.5 图像检测：模板匹配、阈值调整、暂停时间
- [ ] 4.2.6 颜色识别：颜色匹配、容差设置、脚本执行
- [ ] 4.2.7 后台监控：窗口选择、OCR/图像/颜色监控、多组监控
- [ ] 4.2.8 并发压力：20 模块 × 50 组运行 30 分钟
- [ ] 4.2.9 停止机制：单模块停止、全部停止、停止后重启、异常恢复
- [ ] 4.2.10 输入操作：鼠标点击、按键触发、多模块并发、随机偏移

### 4.3 性能基准
- [ ] 4.3.1 记录改造前后内存对比（10 组、50 组、100 组）
- [ ] 4.3.2 记录改造前后 CPU 对比（同上）
- [ ] 4.3.3 记录改造前后启动时间对比
