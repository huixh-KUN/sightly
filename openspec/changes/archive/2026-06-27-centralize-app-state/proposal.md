## Why

应用全局运行状态（is_running/is_paused）分散在 MainWindow、各 Worker 模块和 AppState 三层之间，且存在幽灵变量（system_stopped 6处检查0处赋值）、未使用变量（MainWindow._is_paused）、绕过 property 直接访问私有属性（app._is_running）等问题。AppState 作为中央状态管理器仅管理模块开关，不参与运行状态，导致模块各自为政地检查 app 属性来确认是否可执行。本次变更将运行状态统一归入 AppState，清除死代码。

## What Changes

- 将 `is_running` / `is_paused` 状态从 MainWindow 迁移到 AppState
- 删除 `system_stopped` 幽灵变量（6处死检查）
- 删除 `MainWindow._is_paused` 未使用的 property
- 统一所有模块的状态检查走 `app.app_state.is_running` / `app.app_state.is_paused`
- 删除 AppState 中未连接的 `start_requested` / `stop_requested` 信号
- 修复 `input/keyboard.py` 直接访问 `app._is_running` 的问题
- 修复 `ui/main_window.py` 直接访问 `app_state._wm` 和 `app_state._module_states` 的问题

## Capabilities

### New Capabilities
- `app-state`: 应用全局运行状态管理，包括 is_running/is_paused 的统一管理

### Modified Capabilities
- 无

## Impact

- **core/state.py**: 新增 `is_running` / `is_paused` 字段和信号，增加启停方法
- **ui/main_window.py**: 移除 `_is_running` / `_is_paused` property，改走 AppState
- **modules/***: 替换所有 `self.app.is_running` 为 `self.app.app_state.is_running`
- **modules/script.py**: 删除 `getattr(self.app, 'system_stopped', False)` 检查
- **modules/ocr.py**: 同上
- **modules/image.py**: 同上
- **modules/color.py**: 同上
- **core/click_handler.py**: 同上
- **input/keyboard.py**: 修复直接访问私有属性
- **ui/main_window.py**: 修复直接访问 `app_state._wm` 和 `app_state._module_states`
