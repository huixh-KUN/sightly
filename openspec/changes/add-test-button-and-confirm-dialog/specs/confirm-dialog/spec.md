## ADDED Requirements

### Requirement: 系统 SHALL 提供 ConfirmDialog 组件
ConfirmDialog SHALL 是一个 QWidget 子类，用于通用的确认弹窗场景，替代直接使用 QMessageBox。

#### Scenario: 显示确认弹窗
- **WHEN** 用户点击需要确认的操作（如删除按钮）
- **THEN** 系统显示 ConfirmDialog，包含标题、消息文本、确认按钮和取消按钮

#### Scenario: 用户确认
- **WHEN** 用户在 ConfirmDialog 中点击确认按钮
- **THEN** ConfirmDialog 发射 accepted 信号并关闭

#### Scenario: 用户取消
- **WHEN** 用户在 ConfirmDialog 中点击取消按钮或关闭窗口
- **THEN** ConfirmDialog 不发射 accepted 信号并关闭

### Requirement: GroupListItem SHALL 在删除前显示 ConfirmDialog
GroupListItem 的删除按钮 SHALL 先弹出 ConfirmDialog 确认后才发射 delete_clicked 信号。

#### Scenario: 删除按钮点击
- **WHEN** 用户点击 GroupListItem 的删除按钮
- **THEN** 系统显示 ConfirmDialog，消息中包含该组的名称
- **THEN** 用户确认后发射 delete_clicked 信号，取消则不发射

### Requirement: ConfirmDialog SHALL 支持自定义文案
ConfirmDialog SHALL 支持通过构造参数自定义标题、消息、确认按钮和取消按钮的文字。

#### Scenario: 自定义参数
- **WHEN** 调用方传入 title、message、confirm_text、cancel_text
- **THEN** 弹窗显示相应的标题、消息和按钮文字
