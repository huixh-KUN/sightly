## ADDED Requirements

### Requirement: AppState 存储模块配置数据
AppState SHALL 提供 `module_configs` 属性，存储各模块的配置数据。

#### Scenario: 模块配置写⼊
- **WHEN** 任意代码调⽤ `app_state.update_module_config(name, config)`
- **THEN** AppState SHALL 更新 `module_configs[name]` 为提供的配置对象

#### Scenario: 模块配置读取
- **WHEN** 模块需要获取最新配置
- **THEN** 查询 SHALL 通过 `app_state.module_configs.get(name)` 获取

#### Scenario: 模块配置变更发射信号
- **WHEN** `module_configs` 中任意模块的配置更新
- **THEN** AppState SHALL 发射 `module_config_changed(name)` 信号

### Requirement: AppState 提供 save_request 信号
AppState SHALL 提供 `save_requested` 信号，替代模块直接调⽤ `self.app.save_config()`。

#### Scenario: 模块请求保存配置
- **WHEN** 模块因内部状态变更（⾮⽤⼾操作）需要持久化配置
- **THEN** 调⽤ SHALL 为 `ctx.app_state.request_save()`

#### Scenario: MainWindow 响应保存请求
- **WHEN** `save_requested` 信号被发射
- **THEN** MainWindow SHALL 执⾏配置保存流程

## MODIFIED Requirements

### Requirement: AppState manages global running state
AppState SHALL 统⼀管理全局运⾏状态 `is_running` / `is_paused`。

#### Scenario: 查询运⾏状态
- **WHEN** 任何代码需要判断系统是否在运⾏
- **THEN** 查询 SHALL 通过 `app_state.is_running` 获取（模块通过 `ctx.app_state.is_running`）

#### Scenario: 查询暂停状态
- **WHEN** 任何代码需要判断系统是否暂停
- **THEN** 查询 SHALL 通过 `app_state.is_paused` 获取（模块通过 `ctx.app_state.is_paused`）

#### Scenario: 状态变更发射信号
- **WHEN** `is_running` 或 `is_paused` 状态变化
- **THEN** AppState SHALL 发射 `running_state_changed` 或 `paused_state_changed` 信号

### Requirement: Direct private access fix
系统 SHALL 修复所有直接访问内部对象私有属性的问题。

#### Scenario: 修复 app._is_running 访问
- **WHEN** 代码直接访问 `app._is_running`
- **THEN** 该访问 SHALL 改为 `ctx.app_state.is_running`

#### Scenario: 修复 app_state._wm 访问
- **WHEN** 代码直接访问 `app_state._wm`
- **THEN** 该访问 SHALL 改为通过 AppState 公开⽅法

#### Scenario: 修复 app_state._module_states 访问
- **WHEN** 代码直接访问 `app_state._module_states`
- **THEN** 该访问 SHALL 改为通过公开⽅法 `app_state.enabled_modules()`
