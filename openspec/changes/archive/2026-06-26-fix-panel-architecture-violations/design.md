## Context

当前 `ui/` 下 5 个 Panel 共 18 处绕过 AppState 信号直接调用后端。项目规范 (AGENTS.md) 要求"UI 控件 → Signal → AppState → Slot → 后端逻辑"，但实际代码大量违反。

违规分布：

```
background_panel:  8 处 ← 最严重，直接操作 background_manager 核心状态
settings_panel:    6 处 ← 直接读写 MainWindow 属性/ConfigVar
script_panel:      2 处 ← UI 已屏蔽，可删除
timed_panel:       1 处 ← GroupWidget 直接启动模块
home_panel:        1 处 ← 直接调 save_config
widgets.py:        conduit ← GroupEditWindow 透传 app 给子 widget
```

修复的本质：将 Panel 对 `self.app.xxx` 的直接依赖改为信号驱动，Panel 不需要知道后端对象的引用，只需要发射信号并接收结果。

## Goals / Non-Goals

**Goals:**
- 消除 18 处 `self.app.xxx_manager`/`xxx_module`/`MainWindow 属性` 直接调用
- 所有 Panel 通信走 Qt 信号，MainWindow 作为路由层
- GroupEditWindow 不再透传 `app` 引用

**Non-Goals:**
- 不改变后端模块的接口签名
- 不影响工作空间配置的读写流程
- 不改变 AGENTS.md 规范
- 不引入新的外部依赖

## Decisions

### 1. 信号归属：AppState vs Panel 自有信号

两种选择：

```
方案 A: Panel 发射自有信号，MainWindow 在 _init_signals 中连接
  背景面板: BackgroundPanel.window_selected → background_manager.set_target_window

方案 B: AppState 统一中转
  BackgroundPanel 发射信号 → AppState 信号 → MainWindow → 后端
```

**选择 A**，理由：
- AppState 增加背景监控专用信号会污染通用状态层
- Panel 自有信号更符合 Qt 组件规范——组件声明自己的输出接口
- MainWindow 作为唯一路由层，在 `_init_signals()` 中集中连接

### 2. 读取 target_hwnd 的替代方案

当前 `BackgroundGroupWidget` 和 `BackgroundPanel` 多处直接读 `background_manager.target_hwnd` 做坐标转换。修复方式：

```
Panel 本地存储 hwnd:
  BackgroundPanel._on_window_selected(hwnd):
    self._target_hwnd = hwnd            ← 存本地
    emit self.window_selected(hwnd)     ← 通知后端

  BackgroundGroupWidget 读 panel 属性而非 self.app:
    通过回调/属性注入获取 hwnd
```

理由：Panel 自己选择的窗口，hwnd 本来就是 Panel 先知道的。本地存一份即可，无需每次从后端读。

### 3. auto_reconnect 的双向通信

`set_config` 中 auto_reconnect 需要：调用后端 → 根据结果更新 UI。这是目前唯一真正需要双向通信的地方。

```
方案: 信号 + 回调函数
  Panel emit auto_reconnect_requested(wc, wp, wt, callback)
  MainWindow:
    hwnd = background_manager.auto_reconnect(wc, wp, wt)
    callback(hwnd)  # Panel 在 callback 里更新 UI
```

替代方案（信号回传）：
```
  Panel emit auto_reconnect_requested(wc, wp, wt)
  MainWindow 处理 → Panel.auto_reconnect_result(hwnd) 信号
```
选择前者，因为回调方式改动更小、流程更直观。

### 4. GroupEditWindow 去管道化

当前：`GroupEditWindow.__init__(self, app, data, idx, type, panel)` → 存 `self._app` → 传给子 widget。

改为：`GroupEditWindow.__init__(self, data, idx, type, panel, logging_manager)` — 只传入必要依赖。

子 widget 不再持有 `app`，需要数据/信号时通过 `panel` 参数反向获取（panel 是 GroupEditWindow 的创建者，不持有 app 引用）。

### 5. script_panel.py 的处理

UI 入口已屏蔽，文件残留。直接删除 `ui/script_panel.py` 并清理 `main_window.py` 中对应 import。

## Risks / Trade-offs

- [破坏性] 18 处信号重构涉及 5 个 panel + main_window + widgets.py，容易漏连信号 → 逐 panel 修复、每改一个 panel 运行验证
- [回归] `set_config` 的自动重连流程改动最大（信号+回调） → 单独测试自动重连场景
- [可测试性] 本次重构本身提升可测试性（Panel 不再依赖完整 app 对象）
