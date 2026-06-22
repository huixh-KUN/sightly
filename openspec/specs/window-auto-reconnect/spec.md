# window-auto-reconnect Specification

## Purpose
TBD - created by archiving change persist-window-handle. Update Purpose after archive.
## Requirements
### Requirement: 窗口选择时采集标识信息

当用户通过 `WindowSelector` 选择一个窗口时，系统 SHALL 自动采集该窗口的类名和进程名。

#### Scenario: 选择窗口后采集标识
- **WHEN** 用户双击窗口列表中的某个窗口
- **THEN** 系统调用 `win32gui.GetClassName(hwnd)` 获取类名
- **THEN** 系统调用 `GetWindowThreadProcessId` + `GetModuleBaseName` 获取进程名
- **THEN** 系统将 `window_class`、`window_process`、`window_title` 保存在 `BackgroundManager` 实例属性中

#### Scenario: 无法获取进程名
- **WHEN** 用户选择的窗口进程无法访问（权限不足）
- **THEN** 系统记录错误日志
- **THEN** 系统将 `window_process` 设为 `None`，自动重连时跳过进程名匹配，仅用类名匹配

---

### Requirement: 配置持久化窗口标识

系统 SHALL 在保存面板配置时将窗口标识写入 `config.json`。

#### Scenario: 保存配置包含窗口标识
- **WHEN** `BackgroundPanel.collect_config()` 被调用
- **THEN** 返回的配置列表中包含 `window_class`、`window_process`、`window_title` 字段
- **THEN** 写入 `config.json` 的 background 段的每个监控组配置中

#### Scenario: 未选择窗口时保存
- **WHEN** 从未选择过窗口时保存配置
- **THEN** `window_class`、`window_process`、`window_title` 均为 `null`

---

### Requirement: 加载配置时自动重连窗口

系统 SHALL 在加载配置后自动尝试通过窗口标识重新连接目标窗口。

#### Scenario: 完全匹配，自动重连成功
- **WHEN** `config.json` 包含 `window_class: "Qt515QWindowIcon"` 和 `window_process: "MuMuPlayer.exe"`
- **WHEN** 存在一个可见窗口同时满足类名和进程名匹配
- **THEN** 系统自动调用 `BackgroundManager.set_target_window(hwnd)`
- **THEN** `WindowSelector` 显示「已选择: {窗口标题}」并截取预览
- **THEN** 用户无需手动选择窗口

#### Scenario: 类名匹配到多个同进程窗口
- **WHEN** 存在多个可见窗口具有相同的类名和进程名
- **THEN** 系统选中第一个匹配的窗口
- **THEN** 记录日志「自动重连：找到 N 个匹配窗口，使用第一个」

#### Scenario: 无匹配窗口
- **WHEN** `config.json` 包含窗口标识
- **WHEN** 不存在任何可见窗口满足匹配条件
- **THEN** 系统记录日志「自动重连失败：未找到匹配的窗口」
- **THEN** `WindowSelector` 显示「窗口未找到，请重新选择」
- **THEN** 不阻塞应用正常启动

#### Scenario: 缺少窗口标识（旧配置）
- **WHEN** `config.json` 的 background 配置中 `window_class` 为 `null` 或不存在
- **THEN** 跳过自动重连
- **THEN** `WindowSelector` 保持「未选择窗口」状态
- **THEN** 功能与旧版本一致

---

### Requirement: 用户手动重选覆盖

用户手动通过 `WindowSelector` 重新选择窗口后，系统 SHALL 更新窗口标识配置。

#### Scenario: 手动重选后更新标识
- **WHEN** 用户从窗口列表中双击一个新窗口
- **THEN** 系统重新采集新窗口的 `class_name`、`process_name`、`title`
- **THEN** 更新 `BackgroundManager` 中的窗口标识
- **THEN** 下次保存配置时使用新标识覆盖旧数据

---

### Requirement: 向后兼容

系统 SHALL 不破坏现有工作空间配置。

#### Scenario: 加载旧版 config.json
- **WHEN** 加载旧版 `config.json`（不含 `window_class`/`window_process` 字段）
- **THEN** `BackgroundPanel.set_config()` 正常恢复所有监控组配置
- **THEN** 自动重连跳过（因无窗口标识可匹配）
- **THEN** 不产生任何错误日志

