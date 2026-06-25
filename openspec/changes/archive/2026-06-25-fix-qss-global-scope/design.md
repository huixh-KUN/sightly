## Context

当前 QSS 仅在 `MainWindow.__init__` 通过 `self.setStyleSheet()` 设置，作用域限于 MainWindow 及其子控件树。`GroupEditWindow` 等独立弹窗不在该树中，继承系统默认白色背景。

`ThemeManager.switch_to()` 已使用 `QApplication.instance().setStyleSheet()` 全局设置 QSS——说明基础设施已支持全局 QSS，仅初始加载路径未对齐。

## Goals / Non-Goals

**Goals:**
- 应用启动时 QSS 全局生效，所有窗口（含独立弹窗）继承当前主题
- 与 `ThemeManager.switch_to()` 的全局设置方式保持一致

**Non-Goals:**
- 不修改现有主题系统（`_DarkColors`/`_LightColors`/`ThemeManager`）
- 不添加主题切换 UI（那是另一个功能）
- 不对现有控件做特殊适配——全局 QSS 的 `QWidget` 选择器覆盖率已够用

## Decisions

- **方式**：将 `main_window.py` 的 `self.setStyleSheet(QSS)` 替换为 `QApplication.instance().setStyleSheet(QSS)`
- **理由**：
  - `ThemeManager.switch_to()` 已使用相同模式，一致性好
  - 所有弹窗自动继承主题，无需逐个设置
  - 改动量最小（1 行）
- **备选**：在 `GroupEditWindow` 内手动调用 `self.setStyleSheet(ThemeManager.qss())` → 每增加一个弹窗都要重复，脆弱

## Risks / Trade-offs

- [低风险] 全局 QSS 的 `QMainWindow, QWidget` 选择器优先级问题——与现有 `switch_to()` 行为一致，已在生产中使用
- [低风险] `app.setStyleSheet()` 覆盖所有窗口——这正是需要的效果
