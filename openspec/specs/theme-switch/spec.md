# 主题切换

## Purpose

提供深色/浅色主题切换功能，用户可通过标题栏开关实时切换并持久化偏好。

## Requirements

### Requirement: User can switch theme

系统 SHALL 在标题栏右侧提供主题切换开关，用户在深色/浅色主题之间切换。

#### Scenario: Toggle from header bar

- **WHEN** 用户点击主题切换 Toggle
- **THEN** 系统 SHALL 立即通过 ThemeManager.switch_to() 刷新全局 QSS
- **THEN** Toggle 的标签文字 SHALL 同步更新（"深色" / "浅色"）

### Requirement: Theme preference persists

系统 SHALL 将用户选择的主题偏好保存到 config.json，并在启动时自动恢复。

#### Scenario: Preference survives restart

- **WHEN** 用户切换主题后关闭应用
- **THEN** config.json 中 SHALL 保存 theme 字段（"dark" / "light"）
- **WHEN** 应用再次启动
- **THEN** MainWindow SHALL 读取 theme 字段并调用 ThemeManager.switch_to()
- **THEN** 主题 Toggle SHALL 同步到正确状态

### Requirement: Toggle remains visible in both themes

切换开关自身的文字和图标 SHALL 在任何主题下保持可见，不受全局 QSS 覆盖。

#### Scenario: Light theme also shows toggle

- **WHEN** 当前为浅色主题
- **THEN** 主题切换 Toggle 的文字 SHALL 可读（颜色与亮色背景对比度足够）
- **WHEN** 当前为深色主题
- **THEN** 主题切换 Toggle 的文字 SHALL 可读（颜色与暗色背景对比度足够）
