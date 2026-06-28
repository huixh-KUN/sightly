## ADDED Requirements

### Requirement: Controller naming follows `*Controller` suffix
系统 SHALL 遵循 `项目命名规范.md` 中定义的 `*Controller` 后缀约定，用于主动控制流程、协调交互的类。

#### Scenario: 控制输入实现的类使用 Controller 后缀
- **WHEN** 一个类负责控制多种输入实现（如 DD/PyAutoGUI/Win32 的选择、优先级锁协调）
- **THEN** 其类名 SHALL 以 `Controller` 结尾
