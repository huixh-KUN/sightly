## 1. LoggingManager 刷新机制修复

- [x] 1.1 移除 `_flush_timer` 实例变量，改为每次 `log_message` 调用 `QTimer.singleShot(0, self._flush_gui_updates)`
- [x] 1.2 移除 `_gui_update_pending` 标志，简化竞态路径
- [x] 1.3 `_flush_gui_updates` 增加 `_pending_logs` 非空判断，避免空批次刷新

## 2. 启动历史回填

- [x] 2.1 LogViewer 新增 `append_batch(lines)` 方法（循环调用 `appendPlainText` 或优化为一次性插入）
- [x] 2.2 `home_panel.py` 设置完 `log_callback` 后，遍历 `logging_manager._log_buffer` 调用 `append_batch`

## 3. 验证与清理

- [x] 3.1 测试从后台线程调用 `log_message` 的可靠性
- [x] 3.2 确认 `sightly.log` 与面板日志完全一致
- [x] 3.3 清理调试日志代码
