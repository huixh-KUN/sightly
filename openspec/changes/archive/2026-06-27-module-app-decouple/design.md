## Context

模块（modules/*.py）当前构造函数统一接收 `app`（MainWindow 实例），通过 `self.app.xxx` 直接访问：

| 访问内容 | 性质 | 涉及的模块数 |
|----------|------|-------------|
| `logging_manager` | 共享服务 | 全部（8个） |
| `input_controller` | 共享服务 | 6个 |
| `alarm_module` | 共享服务 | 6个 |
| `app_state.is_running` | 运行时状态 | 3个 |
| `xxx_groups`（配置数据） | 模块配置 | 6个 |
| `status_label.setText()` | UI 控件耦合 | 3个 |
| `save_config()` / `is_selecting` | MainWindow 方法/属性 | 2个 |

同时，配置数据以 `list[dict]` 形式存储，dict 值被 `ConfigVar` 包裹，导致模块读路径（`.get()`）和序列化路径（`strip_configvar()`）都需要解包。

## Goals / Non-Goals

**Goals:**
- 所有模块不再持有 `self.app` 引用，改为显式声明依赖
- 配置数据以纯 Python 类型（dataclass）在 AppState 中流动
- 模块不直接操作 UI 控件
- 删除 ConfigVar 类和 strip_configvar() 函数

**Non-Goals:**
- 不改动模块内部的业务逻辑
- 不改动模块之间的协作方式（如 alarm_module 注入）
- 不改动面板（Panel）的 UI 布局和交互方式
- 不改动 MainWindow 的非模块相关职责（导航、主题等）
- 不引入第三方依赖

## Decisions

### Decision 1: ModuleContext 代替 self.app

```
Current:  OCRWorker(app)          → self.app.logging_manager
Target:   OCRWorker(ctx)          → ctx.logger
```

`ModuleContext` 是一个只读 dataclass：

```python
@dataclass(frozen=True)
class ModuleContext:
    app_state: AppState
    logger: LoggingManager
    input_controller: InputManager
    alarm: AlarmWorker
    status_notifier: StatusNotifier  # 替代直接操作 status_label
```

**为什么不采用逐个参数注入？** 8 个模块都依赖 logger + app_state，6 个模块都依赖 input_controller + alarm。逐个参数注入会导致大量重复签名变化。一个 context 对象让签名变化最小化。

**为什么不采用 service locator 模式？** AppState 已经承担了状态管理职责，再加入服务定位会职责膨胀。Context 是纯数据容器，职责单一。

### Decision 2: 模块配置 dataclass

每个模块的配置数据从 `list[dict]` + ConfigVar 改为强类型 dataclass，定义在与模块同目录的 `configs.py` 或就近存放：

```python
# modules/configs.py（或每个模块文件内）
@dataclass
class OCRGroupConfig:
    region: tuple[int, int, int, int]
    keywords: list[str]
    language: str
    interval: float
    pause: float
    click: bool
    key: str
    alarm: bool
    enabled: bool

@dataclass
class OCRConfig:
    groups: list[OCRGroupConfig]
    tesseract_available: bool
```

**为什么放 modules/ 下而不是 core/？** 配置结构是模块自身的契约，随模块变化。放在 core/ 会造成 core ↔ modules 的循环引用。

### Decision 3: AppState 统一存储模块配置

AppState 新增 `module_configs: dict[str, Any]`，在配置加载/变更时写入，模块在 `start()` 时读取：

```
Panel 变更 → MainWindow._sync_panel_configs()
  → 剥离 ConfigVar（纯 dict）
  → 转换为 dataclass
  → AppState.update_module_config("ocr", ocr_cfg)
  → 模块在 start() 时从 AppState 读取最新配置
```

运行时自动读取配置的模块（OCR, Image）：每次循环轮询 AppState 中的最新配置。

### Decision 4: StatusNotifier 桥接模块↔UI 状态

`status_label` 是 QLabel 控件，模块不应直接持有。创建 `StatusNotifier`：

```python
class StatusNotifier(QObject):
    status_changed = pyqtSignal(str)
    
    def info(self, text: str):
        self.status_changed.emit(text)
```

ModuleContext 持有 `StatusNotifier` 实例，模块调用 `ctx.status_notifier.info("识别完成")`。MainWindow 连接信号到 `status_label.setText()`。

### Decision 5: 模块内控调用改为 Signal

当前 `self.app.is_selecting = True` / `self.app.save_config()` 等调用改为：

- `save_config()` → AppState 提供 `request_save()` 方法，MainWindow 连接其信号执行
- `is_selecting` / `cancel_selection()` → 通过 `app_state.is_selecting` 属性 + Signal 完成

### Decision 6: 逐步迁移

不一次性改所有模块。顺序：

1. **输入层**（无需改动，已解耦）
2. **NumberWorker**（读取配置最单纯，运行时不用 self.app）
3. **TimedTask**（同上）
4. **ImageDetectionWorker/Manager**（运行时读 group，需注意）
5. **ColorRecognitionWorker/Manager**（运行时读 target_color/region）
6. **OCRWorker**（运行时读 ocr_groups[group_index]）
7. **BackgroundMonitorWorker/Manager**（服务类依赖）
8. **ScriptWorker**（依赖最多，最后改）
9. **AlarmWorker**（独立，配置简单）

## Risks / Trade-offs

| 风险 | 缓解措施 |
|------|---------|
| 模块构造函数改动大，一次性 PR 影响面广 | 分批迁移，每个模块独立 PR |
| ConfigVar 在 80+ 处使用，遗漏导致运行时异常 | Panel 层先改为纯值，再全部替换 ConfigVar → plain，最后删除 ConfigVar 类 |
| 运行时读取配置的模块（OCR/Image）可能读到过时数据 | AppState 存储最新配置，模块每次循环重新读取 |
| 模块间通过 self.app 的隐式耦合（如 timed 写 is_selecting） | 改为 AppState 属性 + Signal |
| 迁移过程中部分模块用 ctx、部分用 app，不一致 | 使用过渡期：新增 ctx 作为第二参数，保持 app 向后兼容，最后统一移除 app |
