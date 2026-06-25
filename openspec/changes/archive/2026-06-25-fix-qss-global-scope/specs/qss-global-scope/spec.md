## ADDED Requirements

### Requirement: QSS SHALL be applied application-wide
应用启动时，系统 SHALL 通过 `QApplication.instance().setStyleSheet()` 而非 `MainWindow.setStyleSheet()` 应用 QSS 样式表，确保所有 QWidget 窗口继承当前主题。

#### Scenario: GroupEditWindow inherits dark theme
- **WHEN** 用户双击监控组打开 `GroupEditWindow`
- **THEN** 该窗口背景色为 `#121212`（深色主题），与主窗口一致

#### Scenario: ThemeManager.switch_to() consistency
- **WHEN** 应用启动完成
- **THEN** QSS 的初始设置方式与 `ThemeManager.switch_to()` 使用的 `app.setStyleSheet()` 一致
