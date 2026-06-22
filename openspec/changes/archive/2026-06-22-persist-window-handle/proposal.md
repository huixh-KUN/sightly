## Why

每次启动应用后后台监控都需要重新选择目标窗口，而窗口句柄（HWND）每次会话都会变化。用户期望选择一次窗口后，下次启动自动重连，无需手动操作。

## What Changes

- 窗口选择时额外保存窗口类名（`win32gui.GetClassName`）和进程名
- 配置保存时写入 `window_class` + `window_process`（而非 HWND）
- 配置加载时按 `class_name` 枚举窗口 → 按 `process_name` 过滤 → 按 `title` 关键词回退匹配 → 自动设置目标窗口
- `WindowSelector` 支持通过类名+进程名恢复选中状态
- 保留用户手动重新选择的覆盖能力

## Capabilities

### New Capabilities
- `window-auto-reconnect`: 启动时自动按类名+进程名重连目标窗口

### Modified Capabilities
（无）

## Impact

- `ui/components/window_selector.py`：新增 `set_window_by_class(title_filter, class_name, process_name)` 恢复方法；选择时收集 class_name + process_name
- `ui/background_panel.py`：`collect_config` 写入窗口标识；`set_config` 恢复时调用自动重连
- `modules/background.py`：`set_target_window` 增强，收集类名+进程名；新增 `auto_reconnect()` 方法
- `utils/window_capture.py`：新增 `find_window_by_class_and_process(class_name, process_name)` 工具函数
- `workspace/*/config.json`：background 段新增 `window_class`、`window_process` 字段
