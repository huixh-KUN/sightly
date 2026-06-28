## Why

两处高优资源/架构问题：PIL Image 对象打开后不 close 导致资源泄漏；自动重连和位置选择信号传递可调用对象（lambda），违反 Qt 信号类型安全。

## What Changes

- **PIL 泄漏修复**：`modules/image.py:257` 移除未使用的 `Image.open` 调用；`utils/window_capture.py:248`、`utils/screenshot.py:118` 补上 `.close()`
- **信号回调改为 int hwnd 传递**：`background_panel.py` 的 `auto_reconnect_requested` 信号第 4 个参数从 `callable callback` 改为 `int hwnd`（0=失败），MainWindow 同步执行后通过 slot 返回值而非回调
- **TimedGroupWidget 位置选择改为中间信号**：`TimedPanel` 拦截 `position_selection_requested`，MainWindow 处理后通过 Panel 的 slot 回调 widget

## Capabilities

### New Capabilities
<!-- 无新能力，纯修复 -->

### Modified Capabilities
<!-- 无 spec 级行为变更 -->

## Impact

- `modules/image.py`: 移除死代码 `Image.open`
- `utils/window_capture.py`: `capture_window_region()` 中 `full_image.close()`
- `utils/screenshot.py`: `get_region_screenshot()` 中 `full_screenshot.close()`
- `ui/background_panel.py`: `auto_reconnect_requested` 信号签名变更
- `ui/timed_panel.py`: `position_selection_requested` 信号签名简化
- `ui/main_window.py`: 对应 slot 调整
