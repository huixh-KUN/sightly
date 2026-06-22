## Why

运行中修改模块开关、监控组配置或快捷键可能导致状态不一致或意外行为。用户应在启动后无法修改配置，停止后恢复可编辑状态。

## What Changes

- 全部启动后禁用首页模块开关（`SwitchButton`）
- 全部启动后禁用 OCR/Background/Image/Timed/Number 各面板的「新增组」按钮及所有现有组内的编辑控件（输入框、下拉框、按键捕获、删除按钮等）
- 全部启动后禁用设置页的快捷键捕获组件（`KeyCaptureWidget` 的「修改」按钮）
- 全部停止后恢复以上所有控件为可编辑状态

## Capabilities

### New Capabilities
- `lock-config-when-running`: 运行时锁定所有配置编辑入口，停止后解锁

### Modified Capabilities
（无）

## Impact

- `ui/main_window.py`：`_on_start_all` / `_on_stop_all` 新增锁定/解锁调用
- `ui/home_panel.py`：提供 `set_toggles_enabled(bool)` 方法
- 各监控面板（`ocr_panel.py`、`background_panel.py`、`image_panel.py`、`timed_panel.py`、`number_panel.py`）：新增 `set_enabled(bool)` 方法
- `ui/settings_panel.py`：新增 `set_enabled(bool)` 方法
