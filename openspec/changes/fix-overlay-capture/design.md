## Context

`CaptureOverlayBase` 在重构时引入了 `grabKeyboard()/grabMouse()` 方案，但 Windows 上 `grabKeyboard()` 底层调用 `AttachThreadInput`，当调用线程不是前台窗口线程时会静默失败。旧版 `showFullScreen()` + `Qt.Tool` 不依赖 grab，全屏窗口自然接收所有输入。

## Goals / Non-Goals

**Goals:**
- 修复 ESC/右键无法退出 overlay 的问题
- 修复拖拽选框不工作的问题
- 保留统一的 `CaptureOverlayBase` 基类封装

**Non-Goals:**
- 不改动 region_overlay.py、screenshot.py（继承基类，无额外逻辑）
- 不改动 overlay_utils.py（工具函数无关）

## Decisions

| 决策 | 选择 | 理由 |
|------|------|------|
| 窗口类型 | `Qt.Tool` 而非 `Qt.Window` | 工具窗口不抢焦点、不在任务栏显示，适合 overlay |
| 激活属性 | 加回 `WA_ShowWithoutActivating` | 覆盖层不应激活/偷焦点 |
| 显示方式 | `showFullScreen()` 替代 `show()`+`grabKeyboard()` | Windows 上全屏窗口天然接收所有输入，不依赖 grab |
| 全局 ESC | 保留 `eventFilter` | 作为冗余保障，防止多屏/焦点问题 |

## Risks / Trade-offs

- **[风险] `showFullScreen()` 在多显示器下的表现** → `CaptureOverlayBase` 的 `setGeometry(virtual_desktop_geometry())` 已覆盖多屏逻辑，但 `showFullScreen()` 只在全屏当前屏幕。**考虑**：如需要跨屏遮罩，改回 `show()`+`setGeometry(虚拟桌面范围)`+`showFullScreen()`（后者会覆盖全部虚拟桌面）
