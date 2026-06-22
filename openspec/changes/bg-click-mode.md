# 后台监控点击模式

## 需求

后台监控模块的点击动作支持两种可切换的点击模式：

### 1. 物理点击（Physical）
- 当前已有的行为
- 使用 `InputController.click(x, y)` 模拟真实鼠标输入
- 通过 `SendInput` / `mouse_event` 发送到操作系统
- 窗口需要在前台/被激活才能生效

### 2. 虚拟点击（Virtual）
- 新增的信号驱动点击模式
- 通过 `PostMessage` / `SendMessage` 向目标窗口句柄（hwnd）直接发送鼠标消息
- 无需窗口置前或激活
- 后台静默点击，不干扰用户当前操作

## 改动范围

仅涉及 `modules/background.py` 中的 `BackgroundMonitor` 类：

- `_trigger_action()` 方法根据选择的模式执行物理或虚拟点击
- 新增点击模式配置项（`click_mode: str`，值为 `"physical"` 或 `"virtual"`）
- UI 上增加点击模式选择控件

## 不涉及

- 不修改 `InputController` / `ClickHandler`
- 不修改其他模块（OCR、图像、脚本等）
- 不修改脚本命令系统

## 优先级

低。无阻塞依赖。
