## ADDED Requirements

### Requirement: AppState manages global running state
AppState SHALL 统一管理全局运行状态 `is_running` / `is_paused`。

#### Scenario: 查询运行状态
- **WHEN** 任何代码需要判断系统是否在运行
- **THEN** 查询 SHALL 通过 `app.app_state.is_running` 获取

#### Scenario: 查询暂停状态
- **WHEN** 任何代码需要判断系统是否暂停
- **THEN** 查询 SHALL 通过 `app.app_state.is_paused` 获取

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

### Requirement: Direct private access fix
系统 SHALL 修复所有直接访问内部对象私有属性的问题。

#### Scenario: 修复 app._is_running 访问
- **WHEN** 代码直接访问 `app._is_running`
- **THEN** 该访问 SHALL 改为 `app.app_state.is_running`

#### Scenario: 修复 app_state._wm 访问
- **WHEN** 代码直接访问 `app_state._wm`（WorkspaceManager 内部对象）
- **THEN** 该访问 SHALL 改为通过 AppState 公开方法（如 `app_state.workspace_list` 等）

#### Scenario: 修复 app_state._module_states 访问
- **WHEN** 代码直接访问 `app_state._module_states` 用于日志
- **THEN** 该访问 SHALL 改为通过公开方法 `app_state.enabled_modules()`
