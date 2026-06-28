## Why

`项目命名规范.md` 已正式发布（649行），覆盖类/函数/变量/常量/文件命名规则。现有代码库 93 个类中有 21 个违反规范，包括规范中明确列为错误示例的 `ImageDetection`、`BackgroundMonitor`、`MemoryMonitor`。不一致的命名降低代码可读性，也让新开发者难以建立正确的命名直觉。本次变更加速修复所有违规，使代码库与规范完全对齐。

## What Changes

- 将所有执行类（`*Module`/`*Detection`/`*Recognition`/`*Executor`/`*Handler`）重命名为 `*Worker` 或 `*Task`
- 将 `BackgroundMonitor` 重命名为 `BackgroundMonitorWorker`（规范明确指明不应是 Monitor）
- 将 `MemoryMonitor` 重命名为 `MemoryManager`（规范明确指明是管理类）
- 将 `InputController` 重命名为 `InputManager`（管理类应使用 `*Manager`）
- 将 `RelativeCoordinate`/`WindowCoordinate` 重命名为 `*Converter`（转换类后缀）
- 更新所有 import 引用和内部使用
- 修复方法/变量/常量的次要违规

## Capabilities

### New Capabilities
- `naming-conventions`: 代码命名规范约束，定义全项目的类/函数/变量/常量/文件命名规则

### Modified Capabilities
- 无（首次引入命名规范，无既有 spec 被修改）

## Impact

- **modules/**：6 个类改名，波及 ~30 处 import
- **core/**：`ClickHandler` → `ClickWorker`，波及 ~5 处
- **utils/**：`MemoryMonitor` → `MemoryManager`，`RelativeCoordinate` → `RelativeCoordinateConverter`，`WindowCoordinate` → `WindowCoordinateConverter`，波及 ~10 处
- **input/**：`InputController` → `InputManager`，`BaseInputController` → `BaseInputManager`，波及 ~8 处
- 纯重命名变更，无行为逻辑修改
- **BREAKING**: 所有重命名类的 import 路径和类名需要调用方同步更新
