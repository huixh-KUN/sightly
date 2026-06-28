## Why

当前 5 个 Panel 共 18 处越过 AppState 信号直接调用后端管理器/模块方法、读写 MainWindow 属性、访问私有方法，导致数据流不可追踪、多面板操作无协调、后端 API 变更时波及面不可控。

## What Changes

- **background_panel 信号化**：窗口选择、自动重连、属性读取从 `self.app.background_manager.xxx()` 改为 Panel 自有信号 + AppState 中转
- **settings_panel 信号化**：ConfigVar 写操作、save_config、_register_shortcuts 改为 AppState 信号 + MainWindow slot
- **timed_panel 信号化**：位置选择器启动改为 Panel 信号 + AppState 中转
- **home_panel 去耦合**：`save_config()` 改为 AppState 信号
- **widgets.py 去管道**：GroupEditWindow 不再透传 `app` 给子 widget，改为逐层传入必要的数据和信号
- **script_panel 清理**：移除已屏蔽 panel 的残留代码

## Capabilities

### New Capabilities
- `panel-backend-signaling`: 规范 Panel → AppState → MainWindow → 后端的单向信号通信路径

### Modified Capabilities
<!-- 无 spec 级行为变更，仅在实现层面重构通信方式 -->

## Impact

- `ui/background_panel.py`: 新增信号 `window_selected`, `auto_reconnect_requested`, 移除所有 `self.app.background_manager.xxx()` 调用
- `ui/settings_panel.py`: 移除 `self.app.alarm_xxx.set()`, `self.app.save_config()`, `self.app._register_shortcuts()`
- `ui/timed_panel.py`: 移除 `self.app.timed_module.start_timed_position_selection()`
- `ui/home_panel.py`: 移除 `self.app.save_config()`
- `ui/script_panel.py`: 移除文件（UI 已屏蔽）
- `ui/widgets.py`: GroupEditWindow 不再持有/传递 `app` 引用
- `ui/main_window.py`: 新增信号连接，将 Panel 信号路由到后端
- `core/state.py`: 新增信号定义（如需）
