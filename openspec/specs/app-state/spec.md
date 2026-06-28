# App State

## Purpose
定义 Sightly 应用全局运行状态管理规范。AppState 是 `is_running` / `is_paused` 的唯一数据源，所有模块通过 `app.app_state` 读取运行状态。

## Requirements

### Requirement: AppState manages global running state
AppState SHALL 统一管理全局运行状态 `is_running` / `is_paused`。

#### Scenario: 查询运行状态
- **WHEN** 任何代码需要判断系统是否在运行
- **THEN** 查询 SHALL 通过 `app_state.is_running` 获取（模块通过 `ctx.app_state.is_running`）

#### Scenario: 查询暂停状态
- **WHEN** 任何代码需要判断系统是否暂停
- **THEN** 查询 SHALL 通过 `app_state.is_paused` 获取（模块通过 `ctx.app_state.is_paused`）

#### Scenario: 状态变更发射信号
- **WHEN** `is_running` 或 `is_paused` 状态变化
- **THEN** AppState SHALL 发射 `running_state_changed` 或 `paused_state_changed` 信号

### Requirement: Dead code removal
系统 SHALL 移除 `system_stopped` 幽灵变量相关的所有检查。

#### Scenario: 删除 system_stopped 检查
- **WHEN** 代码中存在 `getattr(self.app, 'system_stopped', False)`
- **THEN** 该检查 SHALL 被删除，仅保留 `app.app_state.is_running` 检查

### Requirement: Unused signal removal
系统 SHALL 移除 AppState 中未连接的 `start_requested` 和 `stop_requested` 信号。

#### Scenario: 删除未连接信号
- **WHEN** AppState 中定义的 `start_requested` 或 `stop_requested` 信号没有任何连接
- **THEN** 这些信号 SHALL 被删除

### Requirement: AppState 存储模块配置数据
AppState SHALL 提供 `module_configs` 属性，存储各模块的配置数据。

#### Scenario: 模块配置写入
- **WHEN** 任意代码调用 `app_state.update_module_config(name, config)`
- **THEN** AppState SHALL 更新 `module_configs[name]` 为提供的配置对象

#### Scenario: 模块配置读取
- **WHEN** 模块需要获取最新配置
- **THEN** 查询 SHALL 通过 `app_state.module_configs.get(name)` 获取

#### Scenario: 模块配置变更发射信号
- **WHEN** `module_configs` 中任意模块的配置更新
- **THEN** AppState SHALL 发射 `module_config_changed(name)` 信号

### Requirement: AppState 提供 save_request 信号
AppState SHALL 提供 `save_requested` 信号，替代模块直接调用 `self.app.save_config()`。

#### Scenario: 模块请求保存配置
- **WHEN** 模块因内部状态变更（非用户操作）需要持久化配置
- **THEN** 调用 SHALL 为 `ctx.app_state.request_save()`

#### Scenario: MainWindow 响应保存请求
- **WHEN** `save_requested` 信号被发射
- **THEN** MainWindow SHALL 执行配置保存流程

### Requirement: Direct private access fix
系统 SHALL 修复所有直接访问内部对象私有属性的问题。

#### Scenario: 修复 app._is_running 访问
- **WHEN** 代码直接访问 `app._is_running`
- **THEN** 该访问 SHALL 改为 `ctx.app_state.is_running`

#### Scenario: 修复 app_state._wm 访问
- **WHEN** 代码直接访问 `app_state._wm`
- **THEN** 该访问 SHALL 改为通过 AppState 公开方法

#### Scenario: 修复 app_state._module_states 访问
- **WHEN** 代码直接访问 `app_state._module_states`
- **THEN** 该访问 SHALL 改为通过公开方法 `app_state.enabled_modules()`
