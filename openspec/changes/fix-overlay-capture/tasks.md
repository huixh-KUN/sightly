## 1. 修复 CaptureOverlayBase

- [x] 1.1 `__init__`: 窗口标志改回 `Qt.Tool`，加回 `WA_ShowWithoutActivating`
- [x] 1.2 `show_overlay()`: 用 `showFullScreen()` 替代 `show()` + `setGeometry()` + `grabKeyboard()` + `grabMouse()`
- [x] 1.3 保留 `eventFilter` ESC 全局拦截作为冗余保障
- [x] 1.4 清理 `_release_capture()` 中不再需要的 `releaseKeyboard()`/`releaseMouse()`

## 2. 验证

- [ ] 2.1 手动测试 ESC 退出
- [ ] 2.2 手动测试右键退出
- [ ] 2.3 手动测试拖拽选区内释放后关闭
- [x] 2.4 确认 `python -c "from ui.components.capture_overlay_base import CaptureOverlayBase"` import 正常
