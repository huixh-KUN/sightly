## Context

代码库现有 93 个类中 21 个违反 `项目命名规范.md`。核心问题集中在：
- 执行类（`*Module`/`*Detection`/`*Recognition`/`*Executor`/`*Handler`）未使用规范要求的 `*Worker`/`*Task` 后缀
- 管理类 `InputController` 未使用 `*Manager`
- 转换类 `RelativeCoordinate`/`WindowCoordinate` 未使用 `*Converter`
- `BackgroundMonitor` 和 `MemoryMonitor` 被规范直接列为错误示例

本次变更是纯重命名操作，不改变任何行为逻辑。

## Goals / Non-Goals

**Goals:**
- 将所有违反 `项目命名规范.md` 的类名修正为规范要求的格式
- 同步更新所有 import 和引用
- 修复方法/变量/常量的次要违规（缩写、大小写等）

**Non-Goals:**
- 不修改类的内部实现逻辑
- 不修改 API 行为
- 不新增或删除功能
- 不修改 `项目命名规范.md` 本身
- 不处理规范未覆盖的后缀（UI 组件、`*Backend` 等暂不改动）

## Decisions

### 1. 重命名映射表

| 当前名 | 目标名 | 理由 |
|--------|--------|------|
| `OCRModule` | `OCRWorker` | 执行类 → `*Worker` |
| `NumberModule` | `NumberWorker` | 执行类 → `*Worker` |
| `TimedModule` | `TimedTask` | 执行类，职责是定时任务 → `*Task` |
| `ScriptModule` | `ScriptWorker` | 执行类 → `*Worker` |
| `AlarmModule` | `AlarmWorker` | 执行类 → `*Worker` |
| `ImageDetection` | `ImageDetectionWorker` | 规范明确列为错误示例 |
| `ColorRecognition` | `ColorRecognitionWorker` | 执行类 → `*Worker` |
| `BackgroundMonitor` | `BackgroundMonitorWorker` | 规范明确列为错误示例 |
| `MemoryMonitor` | `MemoryManager` | 管理类 → `*Manager` |
| `ClickHandler` | `ClickWorker` | 执行类 → `*Worker` |
| `KeyEventExecutor` | `KeyEventWorker` | 执行类 → `*Worker` |
| `ScriptExecutor` | `ScriptTask` | 执行类 → `*Task`（区别于 `ScriptWorker`） |
| `InputController` | `InputManager` | 管理类 → `*Manager` |
| `BaseInputController` | `BaseInputManager` | 与管理类一致 |
| `RelativeCoordinate` | `RelativeCoordinateConverter` | 转换类 → `*Converter` |
| `WindowCoordinate` | `WindowCoordinateConverter` | 转换类 → `*Converter` |
| `QuickSwitchBackend` | `QuickSwitchWorker` | 执行类 → `*Worker` |
| `Win32InputBackend` | `Win32Input` | 去掉 `*Backend`，与其他实现风格对齐 |

### 2. 重命名策略

- 每个类重命名走"改定义 → 改所有引用 → 验证"三步
- 先改叶子类（被依赖少的），后改依赖多的
- 使用 IDE/编辑器全局替换功能批量更新 import

### 3. 方法/变量修复范围

- `setKey()` → `set_key()`（`modules/input.py` 方法名非 snake_case）
- 检查并修复明显的缩写变量名（如 `mgr` → `manager`）
- 确保常量统一为 ALL_CAPS

### 4. 不动范围

- UI 组件类（`*Panel`/`*Card`/`*Dialog`/`*Widget`）保持不动 — 规范未定义 UI 后缀
- `ConfigVar` 保持不动 — 内部兼容层，无合适后缀
- `*Input` 后缀（`PyAutoGUIInput`、`DDVirtualInput`）保持不动
- 抽象基类 `Base*` 前缀保持不动

## Migration Plan

1. 按文件依赖顺序逐个模块重命名
2. 每个模块改完后运行 `python -c "from X import Y"` 验证 import 链
3. 全部完成后运行主程序验证启动正常
4. 无 rollback 必要 — 纯重命名，git diff 可回溯

## Risks / Trade-offs

- **[风险] 遗漏引用** → 每个改名后使用 `rg` 全文搜索旧名确保无遗漏
- **[风险] 与其他分支冲突** → 此变更应尽早合入 develop，避免长期分支
- **[决策] `ScriptModule` 和 `ScriptExecutor` 合并？** → 不合并，两者职责不同：`ScriptWorker` 管理脚本生命周期，`ScriptTask` 执行单次脚本
