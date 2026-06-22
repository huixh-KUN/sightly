## Context

当前后台监控在每次启动后都需要用户手动「选择窗口」，因为 HWND（窗口句柄）每次进程重启都会变化。窗口类名（如 `UnityWndClass`、`Qt515QWindowIcon`）和进程名（如 `MuMuPlayer.exe`）在跨会话时是稳定的，窗口标题虽然变化但通常包含不变的关键词。

核心流的四个阶段：
```
选择窗口 → collect_config() → save_current() → config.json
加载配置 → startup_load() → config_loaded → set_config() → auto_reconnect() → 设置窗口
```

## Goals / Non-Goals

**Goals:**
- 选择窗口时自动收集 `class_name` + `process_name` + `title`
- 配置保存时将窗口标识写入 `config.json`（`window_class`、`window_process`、`window_title`）
- 配置加载时自动尝试通过 class_name + process_name 恢复连接
- `WindowSelector` 支持通过类名+进程名恢复选中状态
- 保留用户手动重新选择的覆盖能力（配置始终用最新选择覆盖）

**Non-Goals:**
- 不处理多显示器场景的窗口定位（region 坐标暂时不跟随窗口移动）
- 不实现窗口自动跟随（窗口移动后监控区域不自动平移）
- 不修改现有的窗口列表弹窗 UI

## Decisions

### D1: 匹配策略 — class_name + process_name 主匹配，title 关键词回退

```
保存: {
  window_class: "Qt515QWindowIcon",       # win32gui.GetClassName(hwnd)
  window_process: "MuMuPlayer.exe",       # process_name (不含路径)
  window_title: "MuMu模拟器"              # 原始标题，仅作日志/UI 展示
}

恢复流程:
  1. EnumWindows → 获取所有可见窗口
  2. 过滤出 class_name == saved_class 的窗口
  3. 对每个候选窗口查 GetWindowThreadProcessId → OpenProcess → GetModuleBaseName
  4. 过滤出 process_name == saved_process 的候选
  5. 如果唯一匹配 → 自动选中 ✓
  6. 如果多个 → 选第一个匹配的（大概率是同一个窗口）
  7. 如果零个 → 状态显示「窗口未找到，请重新选择」，不阻塞启动
```

**为什么不用 title 做主匹配？** 标题频繁变化（游戏内切换场景、副本进/出），而 class_name + process_name 组合几乎唯一。

**为什么不用 HWND 持久化？** HWND 每次重启都被系统重新分配，持久化无意义。

### D2: 通过进程名识别窗口，而非 PID

进程名（`MuMuPlayer.exe`）比 PID 更稳定（PID 每次重启变化，进程名固定）。使用 `GetModuleBaseName` 获取进程名，不含路径。

### D3: 工具函数独立封装

新增 `find_window_by_class_and_process(class_name, process_name) -> Optional[int]` 放入 `utils/window_capture.py`，与现有的 `find_window_by_title` 同级。不修改现有函数签名。

### D4: 配置向后兼容

旧 config.json 不含 `window_class`/`window_process` → 加载时跳过自动重连，显示「未选择窗口」（与当前行为一致）。不破坏现有工作空间。

### D5: collect_config() 收集窗口标识

`BackgroundPanel.collect_config()` 现在额外收集 `self.app.background_manager` 的窗口标识：

```python
cfg = {
    # ... 现有字段
}
bg_manager = self.app.background_manager
cfg["window_class"] = bg_manager.window_class
cfg["window_process"] = bg_manager.window_process
cfg["window_title"] = bg_manager.target_title
```

### D6: WindowSelector 新增恢复方法

`WindowSelector.set_window_by_class(title, class_name, process_name)` — 直接设置选中状态（截取预览、更新 UI），不发射信号（由 Panel 在加载完成后统一触发重连）。

## Risks / Trade-offs

| 风险 | 缓解措施 |
|------|---------|
| 类名匹配到多个同进程窗口（如多个 MuMu 实例） | 首次自动选第一个，用户可手动重新选择覆盖 |
| 窗口未找到时监控组仍然启动（无目标窗口） | `start_all_groups()` 已校验 `target_hwnd`，空则跳过 |
| 第三方窗口关闭后类名+进程名被回收给其他窗口 | 加载时验证窗口有效性（`IsWindow`），无效则重置为未选择 |
| 进程名在不同系统语言下可能不同（如中文版 taskmgr.exe） | 保持英文进程名，这是 Windows 标准行为 |
| 配置加载早于 backend 初始化 | 通过信号机制确保 `AppState.config_loaded` 在 `_init_backend` 完成后触发 |
