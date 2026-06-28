## Context

两个独立高优问题：

1. **PIL 泄漏**：3 处 PIL Image 打开后未 `.close()`，其中 `modules/image.py:257` 的 `Image.open()` 结果变量甚至未被使用
2. **信号传递回调**：`background_panel.py` 的 `auto_reconnect_requested(..., object)` 和 `timed_panel.py` 的 `position_selection_requested(index, object)` 传递可调用对象，违反 Qt 信号类型安全

## Decisions

### PIL 泄漏
- `modules/image.py:257`: 直接删除 `Image.open(image_path)` 这一整行（死代码）
- `utils/window_capture.py:248`: `full_image.close()` 补在 crop 之后
- `utils/screenshot.py:118`: `full_screenshot.close()` 补在 crop/使用之后

### 信号回调移除

`auto_reconnect_requested` 目前签名 `Signal(str, str, str, object)`，`object` 是 callback：
- 改为 `Signal(str, str, str)` — 只传 wc, wp, wt
- MainWindow 收到后执行 `background_manager.auto_reconnect()`，然后通过 `BackgroundPanel._on_auto_reconnect_result(ok, hwnd, title)` **直接调用**（Panel 持有 app 引用，MainWindow 可以直接调用 Panel 方法）
- 这样无需 callback 参数通过信号传递

`position_selection_requested` 同理：
- `TimedGroupWidget` 信号改为 `Signal(int)` 
- `TimedPanel` 中继该信号
- MainWindow 处理后在 slot 中通过 `TimedPanel` 调用 widget 的 `_on_pos_selected()`
