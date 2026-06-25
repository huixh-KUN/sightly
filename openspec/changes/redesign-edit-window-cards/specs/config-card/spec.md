## ADDED Requirements

### Requirement: ConfigCard SHALL provide a reusable card container
系统 SHALL 提供一个 `ConfigCard` 组件，用于对配置项进行视觉分组，支持标题、图标和自定义内容区域。

#### Scenario: Card renders with header and body
- **WHEN** 创建 `ConfigCard` 并设置标题和内容
- **THEN** 显示标题行（emoji 图标 + 文字）
- **THEN** 显示内容区域（通过 `set_content()` 注入的 widget）
- **THEN** 卡片背景色为 `#1E1E1E`，边框 `#3C4043`，圆角 12px

#### Scenario: Card can receive optional header widget
- **WHEN** 向 `ConfigCard` 传入 `header_widget` 参数
- **THEN** 标题行右侧显示该 widget

### Requirement: ConfigCard SHALL be exported from ui/components
系统 SHALL 从 `ui.components` 包中导出 `ConfigCard` 类，供上层模块按需引用。

#### Scenario: Import from components
- **WHEN** 执行 `from ui.components import ConfigCard`
- **THEN** 导入成功，ConfigCard 为可用类
