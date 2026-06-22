## Context

当前 `_on_start_all` / `_on_stop_all` 只负责启停模块，不涉及 UI 锁定。用户在脚本运行时仍可：
- 开关模块（SwitchButton）
- 增删改监控组
- 修改快捷键

这可能导致运行中配置错乱或用户困惑。

## Goals / Non-Goals

**Goals:**
- 全部启动后首页模块 SwitchButton 变为 disabled，不可点击
- 全部启动后各监控面板（OCR/Background/Image/Timed/Number）的「新增组」按钮和所有现有组的编辑控件禁用
- 全部启动后设置页 GeneralSettingsCard 的快捷键 KeyCaptureWidget「修改」按钮禁用
- 全部停止后恢复所有控件为可编辑状态

**Non-Goals:**
- 不改变模块内部运行逻辑
- 不涉及日志面板、工作空间选择等其他 UI 区域

## Decisions

### Decision 1: 统一通过 `QWidget.setEnabled(bool)` 实现

Qt 原生 `setEnabled(False)` 会递归禁用所有子控件，无需逐个遍历子 widget。面板级别的禁用/启用只需一行调用。

### Decision 2: 在 `MainWindow._on_start_all` / `_on_stop_all` 末尾操作

锁定和解锁放在启停流程的最后，确保配置已同步后再禁用编辑。

- `_on_start_all` 末尾：遍历 `self.panels` 中需要锁定的面板调用 `setEnabled(False)`，同时禁用首页开关
- `_on_stop_all` 末尾：遍历相同面板调用 `setEnabled(True)`，恢复首页开关

### Decision 3: 需单独禁用首页开关

面板用 `QWidget.setEnabled` 不能影响 StackedWidget 中其他页面。首页的 ModuleCard 内的 SwitchButton 需单独遍历 `get_toggles()` 禁用。

## Risks / Trade-offs

- **`QWidget.setEnabled(False)` 会影响所有子控件**：包括滚动条、布局间距等 → 不影响，滚动条禁用不影响查看内容，用户仍可阅读配置
- **禁用期间信号累积**：`SwitchButton` 禁用后 `setChecked` 仍可被程序调用（`app_state.set_module_enabled`）→ 使用 `setEnabled(bool)` 合理，禁用后用户不可点击但代码仍可修改状态
