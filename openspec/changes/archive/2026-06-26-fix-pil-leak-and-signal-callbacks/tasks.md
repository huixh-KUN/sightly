## 1. PIL 泄漏修复

- [x] 1.1 `modules/image.py:257` 删除死代码 `Image.open(image_path)` + 移除 `from PIL import Image`
- [x] 1.2 `utils/window_capture.py` 在 `capture_window_region()` 中 `full_image.crop()` 后加 `full_image.close()`（finally 块）
- [x] 1.3 `utils/screenshot.py` 在 `get_region_screenshot()` 中 `full_screenshot.crop()`/使用后加 `full_screenshot.close()`（finally 块）

## 2. 信号回调移除

- [x] 2.1 `background_panel.py`：`auto_reconnect_requested` 改为 `Signal(str, str, str)`；`on_auto_reconnect_result` 改为 public
- [x] 2.2 `timed_panel.py`：`TimedGroupWidget` 和 `TimedPanel` 的 `position_selection_requested` 改为 `Signal(int)`
- [x] 2.3 `main_window.py`：`_on_bg_auto_reconnect` 直接调 `panel.on_auto_reconnect_result()`；`_on_timed_position_selection` 直接取 editor 的 `_on_pos_selected` 回调传给 timed_module
