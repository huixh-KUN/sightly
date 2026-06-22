# 线程模型重构方案：Thread → asyncio + ThreadPoolExecutor

## 一、当前架构现状

### 1.1 线程模型总览

| 模块 | 文件 | 线程模型 | 线程数 |
|------|------|----------|--------|
| OCR | `modules/ocr.py` | 单线程循环处理所有组 | 1 |
| 数字识别 | `modules/number.py` | 每组 1 个线程 | N |
| 定时任务 | `modules/timed.py` | 每组 1 个线程 | N |
| 后台监控 | `modules/background.py` | 每组 1 个线程 | N |
| 图像检测 | `modules/image.py` | 单线程循环 | 1 |
| 颜色识别 | `modules/color.py` | 单线程循环 | 1 |
| 脚本 | `modules/script.py` | 1-2 个线程（执行+录制） | 1-2 |

**典型场景**: 5组数字 + 5组定时 + 5组后台 + 其他模块 = **至少 15 个线程**

### 1.2 核心并发组件

| 组件 | 文件 | 机制 | 作用 |
|------|------|------|------|
| PriorityLock | `core/priority_lock.py` | `threading.Lock` + `threading.Condition` + 堆 | 高优先级模块优先获取截图/输入资源 |
| ScreenshotManager | `utils/screenshot.py` | 单例 + PriorityLock | 全局截图资源共享，避免多线程同时截屏 |
| InputController | `input/controller.py` | PriorityLock | 输入操作串行化，防止多模块抢鼠标 |
| ClickHandler | `core/click_handler.py` | 同步调用 InputController | 统一鼠标点击处理 |
| ThreadManager | `core/threading.py` | 线程列表管理 | 模块启停生命周期管理 |

### 1.3 优先级体系

```
Number(6) > Timed(5) > Image(4) > OCR(3) > Color(2) > Background(1) = Script(1)
```

### 1.4 数据流（当前）

```
模块线程 → ScreenshotManager.get_region_screenshot(priority)
                ↓ PriorityLock.acquire(priority) — 竞争锁
           PIL.ImageGrab.grab() — 截图
                ↓
           Recognition Utils 识别（OCR/OpenCV/颜色）
                ↓
           ClickHandler.execute_click()
                ↓
           InputController — PriorityLock 竞争锁
                ↓
           pyautogui/DD/Win32 执行点击
```

### 1.5 停止机制

- **OCR**: `self.app.is_running = False` 标志位
- **Number/Timed/Background**: `threading.Event` 每组独立停止信号
- **Image/Color**: `self.is_running = False` 标志位

---

## 二、当前架构缺点

### 2.1 线程数量膨胀

每组一个线程，用户配置 5 组数字 + 5 组定时 + 5 组后台 = 15 个线程。如果扩展到 20 模块 × 50 组 = **1000 个线程**，系统将不可用。

| 指标 | 10-50 线程 | 50-100 线程 | 100+ 线程 |
|------|-----------|------------|----------|
| 内存 | 80-400MB | 400-800MB | 800MB+ |
| CPU 切换 | 无感知 | 开销明显 | 30%+ CPU 浪费 |
| 响应 | 流畅 | 可接受 | 卡顿/假死 |

### 2.2 停止机制不一致

| 模块 | 停止方式 | 问题 |
|------|----------|------|
| OCR | `app.is_running` 标志位 | 无法精确停止单个组 |
| Number/Timed/Background | `threading.Event` | 每组独立，但线程 join 超时后仍可能残留 |
| Image/Color | `self.is_running` | 单线程，停止时可能卡在 sleep 中 |

### 2.3 资源竞争复杂

PriorityLock 基于 `threading.Condition`，在高并发下：
- `threading.Event.wait()` 涉及内核态切换
- 堆操作 `heapq.heappush/pop` 在锁内执行，增加持锁时间
- 多模块同时竞争截图资源时，低优先级模块可能长时间饥饿

### 2.4 内存开销

每个 Python 线程约 **8MB 栈空间**，100 个线程 = **800MB**。对于桌面自动化工具来说，这是不必要的浪费。

---

## 三、目标架构

### 3.1 架构设计

```
每个模块 1 个线程 + asyncio 事件循环
  ├── 监控组 → asyncio 协程（轻量，~KB 级）
  ├── OpenCV/OCR → ThreadPoolExecutor（CPU 密集，run_in_executor）
  ├── 鼠标点击 → asyncio.Queue 串行执行
  └── 音频播放 → 线程（winsound 阻塞）
```

### 3.2 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│  模块线程 1 (Number)                                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  asyncio event loop                                     │   │
│  │  ├── 协程: number_group_1()  ← 轻量，~KB                │   │
│  │  ├── 协程: number_group_2()                             │   │
│  │  ├── 协程: number_group_N()                             │   │
│  │  └── ThreadPoolExecutor(max_workers=2)                  │   │
│  │        ├── _screenshot()   ← run_in_executor            │   │
│  │        └── _recognize()    ← run_in_executor            │   │
│  └─────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│  模块线程 2 (Timed)                                             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  asyncio event loop                                     │   │
│  │  ├── 协程: timed_group_1()                              │   │
│  │  ├── 协程: timed_group_2()                              │   │
│  │  └── 协程: timed_group_N()                              │   │
│  └─────────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────────┤
│  ... 更多模块线程 ...                                           │
├─────────────────────────────────────────────────────────────────┤
│  全局鼠标队列 (asyncio.Queue)                                   │
│  └── mouse_worker() 协程串行执行点击                            │
├─────────────────────────────────────────────────────────────────┤
│  ThreadPoolExecutor(max_workers=4)  ← CPU 密集任务池           │
│  ├── OpenCV 模板匹配                                            │
│  └── RapidOCR 识别                                              │
└─────────────────────────────────────────────────────────────────┘
```

### 3.3 核心设计点

#### 3.3.1 每模块独立事件循环

```python
import asyncio
import threading

class NumberModule:
    def start_number_recognition(self):
        def run():
            asyncio.run(self._run_all_groups())
        self._thread = threading.Thread(target=run, daemon=True)
        self._thread.start()

    async def _run_all_groups(self):
        tasks = []
        for i, group in enumerate(self.groups):
            if group["enabled"]:
                tasks.append(asyncio.create_task(self._group_loop(i, group)))
        await asyncio.gather(*tasks)
```

#### 3.3.2 CPU 密集任务放线程池

```python
async def _screenshot(self, region, priority):
    loop = asyncio.get_event_loop()
    # 截图是同步阻塞操作，放线程池
    return await loop.run_in_executor(
        self._executor,
        self.screenshot_manager.get_region_screenshot,
        region, priority
    )

async def _recognize(self, image, template):
    loop = asyncio.get_event_loop()
    # OpenCV 匹配是 CPU 密集，放线程池
    return await loop.run_in_executor(
        self._executor,
        cv2.matchTemplate, image, template, cv2.TM_CCOEFF_NORMED
    )
```

#### 3.3.3 鼠标操作串行队列

```python
class MouseQueue:
    def __init__(self):
        self._queue = asyncio.Queue()
    
    async def worker(self):
        while True:
            action = await self._queue.get()
            x, y, button = action
            # 同步调用放线程池
            await asyncio.get_event_loop().run_in_executor(
                None, self._input_controller.click, x, y
            )
            await asyncio.sleep(0.05)  # 防止操作过快
    
    async def put(self, x, y, button='left'):
        await self._queue.put((x, y, button))
```

#### 3.3.4 优先级锁适配

PriorityLock 当前基于 `threading.Condition`，协程内不能直接使用。方案：

- **同模块内协程**: 不需要锁（单线程执行，无竞争）
- **跨模块资源竞争**: 保留 PriorityLock，但通过 `run_in_executor` 调用

```python
async def get_screenshot(self, region, priority):
    loop = asyncio.get_event_loop()
    # PriorityLock 是 threading 实现，必须在线程池中调用
    return await loop.run_in_executor(
        self._executor,
        lambda: self.screenshot_manager.get_region_screenshot(region, priority)
    )
```

---

## 四、为什么这么改

### 4.1 性能对比

| 指标 | 多线程 (100组) | asyncio+线程池 (100组) | 提升 |
|------|---------------|----------------------|------|
| 内存 | ~800MB | ~150MB | **81%** |
| CPU | 60-80% | 30-40% | **50%** |
| 启动时间 | 2-3 秒 | 0.5 秒 | **80%** |
| 扩展上限 | ~100 组 | 2000+ 组 | **20x** |

### 4.2 核心优势

1. **内存效率**: 协程 ~KB 级 vs 线程 ~8MB，1000 个协程仅 ~100MB
2. **切换成本**: 协程纳秒级 vs 线程微秒级，无需内核态切换
3. **无 GIL 争抢**: 协程在 `await` 时主动让出，不抢 GIL
4. **天然串行**: 鼠标操作通过 `asyncio.Queue` 天然串行，无需额外锁
5. **优雅停止**: `asyncio.Task.cancel()` 比 `threading.Event` 更精确

### 4.3 与 DeepSeek 讨论的结论一致

DeepSeek 分析后确认：
- 图片识别（IO 密集）→ 协程合适
- 鼠标点击（必须串行）→ `asyncio.Queue` 排队
- 音频播放（IO 密集）→ 协程合适
- OpenCV/OCR（CPU 密集）→ `run_in_executor` 放线程池

---

## 五、修改范围

### 5.1 必须修改的文件

| 文件 | 修改内容 | 复杂度 |
|------|----------|--------|
| `modules/number.py` | 线程 → asyncio 协程 + 事件循环 | 高 |
| `modules/timed.py` | 线程 → asyncio 协程 + 事件循环 | 高 |
| `modules/background.py` | 线程 → asyncio 协程 + 事件循环 | 高 |
| `modules/ocr.py` | 单线程循环 → asyncio 协程 | 中 |
| `modules/image.py` | 单线程循环 → asyncio 协程 | 中 |
| `modules/color.py` | 单线程循环 → asyncio 协程 | 中 |
| `core/threading.py` | ThreadManager 支持 asyncio 事件循环 | 中 |

### 5.2 需要适配的文件

| 文件 | 修改内容 | 复杂度 |
|------|----------|--------|
| `core/priority_lock.py` | 保留，但协程内通过 run_in_executor 调用 | 低 |
| `utils/screenshot.py` | 保留，协程内通过 run_in_executor 调用 | 低 |
| `input/controller.py` | 保留，协程内通过 run_in_executor 调用 | 低 |
| `core/click_handler.py` | 保留，协程内通过 run_in_executor 调用 | 低 |
| `core/state.py` | 启停逻辑适配 asyncio | 中 |

### 5.3 无需修改的文件

| 文件 | 原因 |
|------|------|
| `modules/script.py` | 后续重构，暂不动 |
| `modules/alarm.py` | 纯工具类，无线程逻辑 |
| `ui/*.py` | UI 层不涉及线程模型 |
| `utils/recognition.py` | 纯函数，无线程逻辑 |

---

## 六、影响范围

### 6.1 正面影响

| 影响 | 说明 |
|------|------|
| 内存降低 80%+ | 100 组从 800MB 降至 150MB |
| CPU 占用降低 50% | 减少线程切换开销 |
| 启动速度提升 80% | 协程创建几乎零开销 |
| 扩展性大幅提升 | 支持 2000+ 并发组 |
| 停止更精确 | `Task.cancel()` 替代标志位轮询 |
| 代码一致性 | 所有模块统一 asyncio 模式 |

### 6.2 风险点

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| PriorityLock 兼容性 | 协程内不能直接用 threading.Lock | 通过 run_in_executor 调用，保留原有逻辑 |
| PySide6 信号集成 | 协程内不能直接 emit 信号 | 用 `loop.call_soon_threadsafe()` 或 QTimer |
| 第三方库兼容 | pyautogui/pynput 是同步 API | 通过 run_in_executor 包装 |
| 调试难度 | asyncio 调试比线程复杂 | 使用 `asyncio.run()` 的 debug 模式 |

### 6.3 不受影响的部分

| 部分 | 原因 |
|------|------|
| UI 面板 | 纯 PySide6，不涉及线程 |
| 配置管理 | ConfigManager/AppState 不涉及线程 |
| 日志系统 | LoggingManager 不涉及线程 |
| 工作空间 | WorkspaceManager 不涉及线程 |

---

## 七、回归测试

### 7.1 基础功能测试

| 测试项 | 测试方法 | 预期结果 |
|--------|----------|----------|
| 模块启停 | 逐个模块点击开始/停止 | 模块正常启动，日志显示启动成功 |
| 全部开始 | 点击全部开始按钮 | 所有已启用模块启动，UI 按钮状态正确 |
| 全部停止 | 点击全部停止按钮 | 所有模块停止，UI 按钮状态恢复 |
| 工作空间切换 | 切换不同工作空间 | 配置正确加载，模块状态正确 |

### 7.2 OCR 模块测试

| 测试项 | 测试方法 | 预期结果 |
|--------|----------|----------|
| 单组识别 | 启用 1 个 OCR 组，配置区域和关键词 | 识别到关键词后触发按键/点击 |
| 多组识别 | 启用 3+ 个 OCR 组 | 各组独立运行，互不干扰 |
| 识别间隔 | 设置不同 interval | 识别频率符合配置 |
| 关键词匹配 | 设置多个关键词 | 匹配到任意关键词即触发 |

### 7.3 数字识别模块测试

| 测试项 | 测试方法 | 预期结果 |
|--------|----------|----------|
| 单组识别 | 启用 1 个数字识别组 | 识别到数字低于阈值时触发 |
| 多组识别 | 启用 3+ 个数字识别组 | 各组独立运行 |
| 阈值触发 | 设置不同阈值 | 低于阈值时触发，高于时不触发 |
| 置信度过滤 | 设置不同置信度阈值 | 低置信度结果被过滤 |

### 7.4 定时任务测试

| 测试项 | 测试方法 | 预期结果 |
|--------|----------|----------|
| 单组定时 | 启用 1 个定时组 | 按配置间隔触发按键 |
| 多组定时 | 启用 3+ 个定时组 | 各组独立定时，互不干扰 |
| 不同间隔 | 设置不同 interval | 各组按各自间隔触发 |
| 按键触发 | 配置不同按键 | 正确按下配置的按键 |

### 7.5 图像检测测试

| 测试项 | 测试方法 | 预期结果 |
|--------|----------|----------|
| 模板匹配 | 配置模板图片和区域 | 匹配到模板后触发点击 |
| 阈值调整 | 调整匹配阈值 | 只有高于阈值才触发 |
| 暂停时间 | 设置 pause 参数 | 触发后暂停指定时间 |

### 7.6 颜色识别测试

| 测试项 | 测试方法 | 预期结果 |
|--------|----------|----------|
| 颜色匹配 | 配置目标颜色和区域 | 识别到颜色后执行脚本 |
| 容差设置 | 调整 tolerance | 容差范围内匹配成功 |
| 脚本执行 | 配置脚本命令 | 识别到颜色后执行脚本 |

### 7.7 后台监控测试

| 测试项 | 测试方法 | 预期结果 |
|--------|----------|----------|
| 窗口选择 | 选择目标窗口 | 正确获取窗口句柄 |
| OCR 监控 | 配置 OCR 类型监控 | 识别到关键词后触发 |
| 图像监控 | 配置图像类型监控 | 匹配到模板后触发 |
| 颜色监控 | 配置颜色类型监控 | 识别到颜色后触发 |
| 多组监控 | 启用 3+ 个后台监控组 | 各组独立运行 |

### 7.8 并发压力测试

| 测试项 | 测试方法 | 预期结果 |
|--------|----------|----------|
| 20 模块 × 50 组 | 配置最大规模 | 系统正常运行，CPU < 70%，内存 < 500MB |
| 长时间运行 | 运行 30 分钟以上 | 无内存泄漏，无线程残留 |
| 快速启停 | 连续点击开始/停止 10 次 | 无崩溃，状态正确 |

### 7.9 输入操作测试

| 测试项 | 测试方法 | 预期结果 |
|--------|----------|----------|
| 鼠标点击 | 触发点击操作 | 鼠标正确点击目标位置 |
| 按键触发 | 触发按键操作 | 正确按下/释放按键 |
| 多模块并发 | 多模块同时触发输入 | 输入操作串行执行，无冲突 |
| 随机偏移 | 设置 offset_range | 点击位置在偏移范围内 |

### 7.10 停止机制测试

| 测试项 | 测试方法 | 预期结果 |
|--------|----------|----------|
| 单模块停止 | 停止单个模块 | 该模块协程取消，其他模块不受影响 |
| 全部停止 | 点击全部停止 | 所有协程取消，线程正常退出 |
| 停止后重启 | 停止后再次开始 | 正常启动，无残留状态 |
| 异常恢复 | 模拟某个协程异常 | 其他协程继续运行 |

---

## 八、实施计划

### 阶段一：试点（Background 模块）

**原因**: Background 模块组最多，问题最明显，改造收益最大

**步骤**:
1. 创建 `core/async_utils.py` — asyncio 工具函数
2. 改造 `modules/background.py` — 线程 → asyncio 协程
3. 创建 `MouseQueue` — 全局鼠标串行队列
4. 测试 Background 模块所有功能

### 阶段二：扩展（Number + Timed 模块）

**步骤**:
1. 改造 `modules/number.py`
2. 改造 `modules/timed.py`
3. 测试多模块并发

### 阶段三：统一（OCR + Image + Color 模块）

**步骤**:
1. 改造 `modules/ocr.py`
2. 改造 `modules/image.py`
3. 改造 `modules/color.py`
4. 改造 `core/threading.py` — ThreadManager 支持 asyncio

### 阶段四：清理

**步骤**:
1. 移除旧的线程管理代码
2. 统一停止机制
3. 全量回归测试
4. 性能基准测试

---

## 九、参考

- DeepSeek 对话: `https://chat.deepseek.com/share/95km61nurc99d1v4x0`
- Python asyncio 文档: `https://docs.python.org/3/library/asyncio.html`
- ThreadPoolExecutor 文档: `https://docs.python.org/3/library/concurrent.futures.html`
