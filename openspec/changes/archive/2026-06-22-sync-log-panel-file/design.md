## Context

当前日志架构：

```
log_message(msg)
  ├─ 写入 sightly.log（立即）
  ├─ 追加到 _pending_logs（线程安全锁）
  └─ 启动 _flush_timer（50ms 后调用 _flush_gui_updates）
       └─ _flush_gui_updates 通过 log_callback 写入 LogViewer
```

问题根因：

1. **`_flush_timer` 线程不安全**：`LoggingManager` 在主线程创建（`self._flush_timer = QTimer()`），而 `log_message()` 可从任意后台线程调用（如 OCR/Background 模块线程）。`QTimer.start()` 在非所属线程调用属未定义行为，可能导致定时器不触发或调度混乱。
2. **`_gui_update_pending` 竞态条件**：当 `_flush_gui_updates` 正在清空 `_pending_logs` 的同时有新的 `log_message` 写入，可能出现在 `_pending_logs.clear()` 之后、`_gui_update_pending = False` 之前插入新日志，导致该批日志无定时器驱动，永久滞留在 `_pending_logs` 中。
3. **无历史回填**：LogViewer 只显示启动后收到的日志，启动前存入 `_log_buffer` 的日志无法在面板回溯。

## Goals / Non-Goals

**Goals:**
- `sightly.log` 中的每条日志条目都出现在 GUI 日志面板
- 支持从后台线程安全调用
- 启动时可回填历史缓冲区至面板
- 保持现有 API 不变（`log_message`、`debug`、`error`）

**Non-Goals:**
- 不改变文件日志格式
- 不改变日志分级体系
- 不引入第三方日志库

## Decisions

### Decision 1: 用 `QTimer.singleShot` 替代 `_flush_timer` 实例

- `QTimer.singleShot(0, slot)` 从任意线程调用均安全：它通过 `QMetaObject.invokeMethod` 在底层将调用 post 到目标对象所在线程的事件队列
- 去掉 `_flush_timer` 成员变量，消除跨线程调用 `QTimer.start()` 的风险
- 去掉 `_gui_update_pending` 标志，每次 `log_message` 都 `singleShot(0, _flush_gui_updates)`，由 `_pending_logs` 非空判断决定是否实际刷新
  - 优化：如果 `_pending_logs` 在 `singleShot` 触发前已累积多条，`_flush_gui_updates` 一次性批量处理

### Decision 2: 启动时回填 `_log_buffer`

- LogViewer 新增 `append_batch(lines)` 方法，一次性追加多条日志（比逐条 append 快）
- `home_panel.py` 设置完 `log_callback` 后，遍历 `logging_manager._log_buffer` 回填

### Decision 3: 保留 `_log_buffer` 作为历史缓存

- 环形缓冲区（`deque(maxlen=500)`）保留最近 500 条记录
- `clear_log()` 清空缓冲区 + 面板

## Risks / Trade-offs

- **高频日志场景性能**：每次 `log_message` 都 `singleShot` 可能产生过多 QTimer 事件 → 风险低，因为 `_flush_gui_updates` 会检查 `_pending_logs` 非空才执行，且 QTimer 零延迟事件批量处理后只产生一次 UI 更新
- **`QTimer.singleShot` 的延迟**：零延迟定时器在事件队列中仍有一次事件循环的延迟（微秒级） → 可接受
