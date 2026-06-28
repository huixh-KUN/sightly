## Why

`capture_overlay_base.py` 重构时将旧版的 `showFullScreen()` + `Qt.Tool` + `WA_ShowWithoutActivating` 方案替换为 `show()` + `grabKeyboard()/grabMouse()` + `Qt.Window`。`grabKeyboard()` 在 Windows 上因 `AttachThreadInput` 静默失败导致键盘/鼠标事件送不到 overlay，ESC/右键无法退出，拖拽选区不可用。

## What Changes

- `CaptureOverlayBase.__init__`: 窗口标志改回 `Qt.Tool`，加回 `WA_ShowWithoutActivating`
- `CaptureOverlayBase.show_overlay()`: 改回 `showFullScreen()`，去掉 `grabKeyboard()/grabMouse()` 依赖
- 保留 `eventFilter` 作为 ESC 的冗余保障
- 无 API 变更，纯内部实现修正

## Capabilities

### New Capabilities
- *（无新能力）*

### Modified Capabilities
- *（无 spec 级变更）*

## Impact

- `ui/components/capture_overlay_base.py`：核心修复
- `ui/components/region_overlay.py`、`screenshot.py`：无改动（继承基类行为）
