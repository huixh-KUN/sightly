## Context

应用全局运行状态目前分散在三层：

1. **MainWindow**: `_is_running` / `_is_paused`（property）
2. **各 Worker 类**: `self.is_running`（线程循环守卫）
3. **AppState**: 不参与运行状态，仅管理模块开关

另有 `system_stopped` 幽灵变量（6处 getattr 检查，0处赋值）、`_is_paused` 僵尸变量（有定义无使用）、以及 `input/keyboard.py` 绕过 property 直接访问 `app._is_running`。

## Goals / Non-Goals

**Goals:**
- AppState 成为 `is_running` / `is_paused` 的唯一数据源
- 删除所有 `system_stopped` 死检查
- 删除未使用的 `MainWindow._is_paused`
- 删除未连接的 `start_requested` / `stop_requested` 信号
- 统一所有模块通过 `app.app_state.is_running` 读取运行状态
- 修复绕过 property 直接访问私有属性的问题

**Non-Goals:**
- 不改动各 Worker 内部的 `self.is_running` — 那是线程级状态，属于不同抽象层
- 不重构 `ScriptTask.is_paused` — 那是脚本执行暂停，非全局暂停
- 不改动 `_shutdown_all_modules` 的关闭逻辑

## Decisions

### 1. AppState 新增字段

```python
class AppState(QObject):
    # 新增信号
    running_state_changed = Signal(bool)    # True=运行, False=停止
    paused_state_changed = Signal(bool)     # True=暂停, False=恢复

    # 新增字段
    _is_running: bool = False
    _is_paused: bool = False

    # 新增方法
    def is_running(self) -> bool
    def is_paused(self) -> bool
    def set_running(self, running: bool)
    def set_paused(self, paused: bool)
```

### 2. 删除内容

| 内容 | 理由 |
|------|------|
| `MainWindow._is_running` + property | 迁移到 AppState |
| `MainWindow._is_paused` + property | 从未使用 |
| `AppState.start_requested` Signal | 未连接 |
| `AppState.stop_requested` Signal | 未连接 |
| `system_stopped` 6处死检查 | 幽灵变量 |

### 3. 替换 `app.is_running` 为 `app.app_state.is_running`

所有模块中 `self.app.is_running` 替换为 `self.app.app_state.is_running`。因 `MainWindow` 原本通过 property 暴露 `is_running`，需要保持兼容。改为统一的 AppState 路径。

### 4. 删除 `system_stopped` 守卫点

删除以下文件中的 `getattr(self.app, 'system_stopped', False)` 代码：

- `modules/script.py`（2处）
- `modules/ocr.py`（2处）
- `modules/image.py`（1处）
- `core/click_handler.py`（1处）

### 5. `input/keyboard.py` 修复

将 `app._is_running` 改为 `app.app_state.is_running`

### 6. `ui/main_window.py` 内部访问修复

| 位置 | 当前代码 | 修复方式 |
|------|---------|---------|
| 第 523 行 | `self.app_state._wm.list_workspaces()` | `self.app_state.workspace_list` (已有 property) |
| 第 528 行 | `self.app_state._wm.save(...)` | 改用 `self.app_state.save_current(extra_config)` 或新增公开方法 |
| 第 601 行 | `self.app_state._module_states` | `self.app_state.enabled_modules()` |

## Risks / Trade-offs

- **[风险] 遗漏引用** → 全文搜索 `app.is_running`（不含 `.app_state`）确保全部替换
- **[风险] 外部代码使用 property** → `MainWindow.is_running` property 保留但不更新，内部逻辑全部走 AppState
- **[决策] 保留 `MainWindow.is_running` property 作为委托** → 可以保持对 MainWindow 的完全兼容
