## Why

模块通过 `self.app` 直接访问 MainWindow 属性（配置数据、UI 控件、共享服务），导致模块与 UI 紧耦合、无法独立测试、UI 重构时必须同步修改模块代码。同时 ConfigVar 兼容层（80+ 处使用）在模块读路径和序列化路径上都需要 strip，增加复杂度。

修这一个 debt 顺带消灭 ConfigVar 兼容层（debt #5）。

## What Changes

- 创建 `ModuleContext` dataclass，统一承载模块所需的共享服务引用，替换 `self.app` 传入方式
- 将所有 `xxx_groups` 配置数据从 MainWindow 迁移到 AppState，存储为纯 Python 类型（剥除 ConfigVar）
- 为每个模块创建对应的配置 dataclass（`OCRConfig`、`ImageConfig` 等），替代 `list[dict]` + ConfigVar 模式
- 所有 Panel 的 `collect_config()` 输出纯值，不再包装 ConfigVar
- 删除 `ConfigVar` 类和 `strip_configvar()` 函数
- 模块中所有 `self.app.xxx` 访问改为通过 `ModuleContext` 或 AppState 访问
- 模块中直接操作 UI 控件的行为（如 `status_label.setText()`）改为通过 Signal 发出

**BREAKING**: 所有模块构造函数签名变更（`app` → `ModuleContext`）

## Capabilities

### New Capabilities
- `module-context`: `ModuleContext` dataclass 定义及注入机制，统一承载模块运行时依赖

### Modified Capabilities
- `app-state`: AppState 扩展承载各模块配置数据（纯 dict/list），不再通过 MainWindow 中转

## Impact

- **modules/*.py** — 所有 8 个模块的构造函数和 `self.app` 引用
- **core/state.py** — AppState 新增配置数据字段
- **ui/main_window.py** — 移除 `xxx_groups` 属性，修改模块创建方式
- **ui/*_panel.py** — 所有 Panel 的 `collect_config()` 改为输出纯值
- **core/config.py** — 删除 `ConfigVar` 类和 `strip_configvar()` 函数
- **modules/input.py** — 已经是解耦的典范（构造注入），无需改动
