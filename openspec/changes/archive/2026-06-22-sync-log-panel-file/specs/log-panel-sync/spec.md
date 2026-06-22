## ADDED Requirements

### Requirement: Log panel displays all logs from sightly.log
The GUI log panel SHALL display every log message that is written to `sightly.log` via `LoggingManager.log_message()`.

#### Scenario: Normal log message appears in panel
- **WHEN** `logging_manager.log_message("操作完成")` is called from any thread
- **THEN** the message `操作完成` SHALL appear in the LogViewer widget within 100ms

#### Scenario: Concurrent log messages from background thread
- **WHEN** 10 `log_message` calls are made in rapid succession from a `QThread` worker
- **THEN** all 10 messages SHALL appear in the LogViewer within 500ms

#### Scenario: Log messages from multiple threads
- **WHEN** `log_message` is called simultaneously from the main thread and a background thread
- **THEN** both messages SHALL appear in the LogViewer (no lost messages due to race conditions)

### Requirement: History buffer is replayed on startup
When the application starts, the LogViewer SHALL display any log messages that were stored in `LoggingManager._log_buffer` before the `log_callback` was connected.

#### Scenario: Startup log replay
- **WHEN** application starts and `LoggingManager` is initialized before `log_callback` is set
- **THEN** after `log_callback` is connected, the LogViewer SHALL display all entries currently in `_log_buffer`

### Requirement: Thread-safe GUI update
The mechanism that delivers log entries from `LoggingManager` to `LogViewer` SHALL be safe to call from any thread without risking undefined behavior or lost messages.

#### Scenario: No QTimer on non-owner thread
- **WHEN** `log_message` is called from a background thread
- **THEN** the implementation SHALL NOT call `QTimer.start()` or `QTimer.stop()` directly on a timer owned by another thread

#### Scenario: Zero lost messages
- **WHEN** `log_message` and `_flush_gui_updates` execute concurrently
- **THEN** no log entry in `_pending_logs` SHALL be silently dropped
