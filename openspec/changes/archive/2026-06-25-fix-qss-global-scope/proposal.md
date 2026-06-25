## Why

当前 QSS 样式仅通过 `MainWindow.setStyleSheet()` 应用到主窗口及其子控件树。独立弹窗（如 `GroupEditWindow`）不在 `MainWindow` 的控件树内，继承系统默认白色背景，与深色主题不一致。

`ThemeManager.switch_to()` 已正确使用 `app.setStyleSheet()` 全局应用，但初始加载走的是窗口级路径，导致应用级 QSS 从未设置。

## What Changes

- 将 `main_window.py:38` 的 `self.setStyleSheet(ThemeManager.qss())` 改为 `QApplication.instance().setStyleSheet(ThemeManager.qss())`
- `ThemeManager.switch_to()` 已在主题切换时使用 `app.setStyleSheet()`，行为一致，无需额外修改
- 后续所有独立窗口/弹窗自动继承主题，无需为每个窗口单独设置 QSS

## Capabilities

### New Capabilities

- `qss-global-scope`: 确保应用启动时 QSS 样式表全局生效，所有窗口（含独立弹窗）继承当前主题

### Modified Capabilities

无

## Impact

- `ui/main_window.py`: 修改一行代码，将 `self.setStyleSheet` 替换为 `app.setStyleSheet`
- 无新增依赖
- 向后兼容：与 `ThemeManager.switch_to()` 行为一致，无冲突
