## ADDED Requirements

### Requirement: Overlay captures input reliably on Windows
全屏选区覆盖层 SHALL 在 Windows 上可靠接收键盘和鼠标事件。

#### Scenario: ESC 键退出覆盖层
- **WHEN** 覆盖层处于活动状态且用户按下 ESC
- **THEN** 覆盖层 SHALL 立即关闭

#### Scenario: 右键退出覆盖层
- **WHEN** 覆盖层处于活动状态且用户点击鼠标右键
- **THEN** 覆盖层 SHALL 立即关闭

#### Scenario: 鼠标拖拽选区内释放后退出
- **WHEN** 用户拖拽选出一个大于 10×10px 的区域并释放鼠标
- **THEN** 覆盖层 SHALL 发射区域信号并关闭
