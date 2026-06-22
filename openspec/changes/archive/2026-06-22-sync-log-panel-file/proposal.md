## Why

日志面板与 `logs/sightly.log` 文件内容不同步：多条日志在文件中正常写入，但 GUI 日志面板未显示。用户希望面板与文件实时保持一致，避免排查问题时遗漏信息。

## What Changes

- 修复 `LoggingManager.log_message()` 的 GUI 刷新机制，确保每条写入文件的日志都能到达 LogViewer 组件
- 日志面板改为直接从 `LoggingManager` 的环形缓冲区（`_log_buffer`）读取历史日志，启动时回填启动前的缓冲区内容
- 消除 `_flush_timer` + `_gui_update_pending` 机制中可能丢失日志的竞态条件或线程不安全路径

## Capabilities

### New Capabilities
- `log-panel-sync`: GUI 日志面板与日志文件实时同步，无遗漏

### Modified Capabilities
（无现有 spec 变更）

## Impact

- `core/logging.py`：LoggingManager 的 GUI 刷新逻辑
- `ui/components/log_viewer.py`：LogViewer 可能需要支持批量回填
- `ui/home_panel.py`：`log_callback` 的设置位置
