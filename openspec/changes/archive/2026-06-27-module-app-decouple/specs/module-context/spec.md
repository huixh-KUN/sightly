## ADDED Requirements

### Requirement: ModuleContext 承载模块共享服务
系统 SHALL 提供 `ModuleContext` dataclass，统一承载模块所需的全部共享服务引用。

#### Scenario: ModuleContext 包含必要服务
- **WHEN** 创建 `ModuleContext` 实例
- **THEN** 它 SHALL 包含 `app_state`、`logger`、`input_controller`、`alarm`、`status_notifier` 五个属性

#### Scenario: ModuleContext 不可变
- **WHEN** 任意代码尝试修改 `ModuleContext` 的属性
- **THEN** 系统 SHALL 抛出 `FrozenInstanceError`

### Requirement: 模块通过 ModuleContext 访问服务
所有模块 SHALL 通过 `ModuleContext` 而非 `self.app` 访问共享服务。

#### Scenario: 模块构造函数接收 ModuleContext
- **WHEN** 创建任意模块实例（除 `input.KeyEventWorker`）
- **THEN** 构造函数 SHALL 接收 `ModuleContext` 作为第一参数，替代 `app`

#### Scenario: 模块通过 ctx 记录日志
- **WHEN** 模块需要记录日志
- **THEN** 调用 SHALL 为 `ctx.logger.debug()` / `ctx.logger.log_message()` / `ctx.logger.error()`

#### Scenario: 模块通过 ctx 获取输入服务
- **WHEN** 模块需要模拟点击或按键
- **THEN** 调用 SHALL 为 `ctx.input_controller.click()` / `ctx.input_controller.key_press()`

#### Scenario: 模块通过 ctx 获取报警服务
- **WHEN** 模块需要播放报警声音
- **THEN** 调用 SHALL 为 `ctx.alarm.play_alarm_sound()`

#### Scenario: 模块通过 ctx 获取运行状态
- **WHEN** 模块需要判断系统是否运行
- **THEN** 调用 SHALL 为 `ctx.app_state.is_running`

### Requirement: StatusNotifier 替代 UI 控件直接访问
系统 SHALL 提供 `StatusNotifier`，通过 signal 桥接模块状态输出与 UI 状态显示。

#### Scenario: 模块通过 StatusNotifier 发送状态信息
- **WHEN** 模块需要更新状态栏文本
- **THEN** 调用 SHALL 为 `ctx.status_notifier.info("消息")`，而非直接操作 UI 控件

#### Scenario: MainWindow 连接 StatusNotifier 信号
- **WHEN** MainWindow 创建模块时
- **THEN** SHALL 连接 `StatusNotifier.status_changed` 信号到 `status_label.setText()`
