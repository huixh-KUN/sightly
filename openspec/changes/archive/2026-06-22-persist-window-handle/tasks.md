## 1. 工具函数层

- [ ] 1.1 在 `utils/window_capture.py` 中新增 `find_window_by_class_and_process(class_name, process_name)` — 枚举所有可见窗口，按 class_name 过滤，再按 process_name 过滤，返回唯一匹配的 HWND
- [ ] 1.2 在 `utils/window_capture.py` 中新增 `get_window_process_name(hwnd) -> Optional[str]` — 通过 `GetWindowThreadProcessId` + `OpenProcess` + `GetModuleBaseName` 获取进程名
- [ ] 1.3 在 `utils/window_capture.py` 中新增 `get_window_class_name(hwnd) -> str` — 封装 `win32gui.GetClassName`

## 2. BackgroundManager 增强

- [ ] 2.1 在 `BackgroundManager.__init__` 中新增 `self.window_class: Optional[str] = None` 和 `self.window_process: Optional[str] = None` 属性
- [ ] 2.2 修改 `set_target_window(hwnd)` — 调用 `get_window_class_name`、`get_window_process_name`、`get_window_title` 采集标识；增加 `(hwnd, title, class_name, process_name)` 签名
- [ ] 2.3 新增 `auto_reconnect(window_class, window_process) -> bool` — 调用 `find_window_by_class_and_process`，匹配成功则调用 `set_target_window` 并返回 True
- [ ] 2.4 新增 `window_info() -> dict` — 返回 `{window_class, window_process, window_title}`，供 `collect_config` 调用

## 3. WindowSelector 组件

- [ ] 3.1 在 `WindowSelector.__init__` 中新增 `set_window_by_class(title: str, class_name: str, process_name: str)` 方法 — 直接设置选中状态，截取预览，更新 UI，不发射信号
- [ ] 3.2 `_on_select` 中在 `emit` 之后新增采集 class_name + process_name 的逻辑（通过信号传递或由 Panel 读取 BackgroundManager）

## 4. BackgroundPanel 串联

- [ ] 4.1 修改 `_on_window_selected` — 选择窗口后自动采集 class_name + process_name 并存入 `BackgroundManager`
- [ ] 4.2 修改 `collect_config()` — 从 `self.app.background_manager.window_info()` 读取并写入 `window_class`、`window_process`、`window_title`
- [ ] 4.3 修改 `set_config(config_list)` — 加载配置后调用 `auto_reconnect()` 自动重连
- [ ] 4.4 自动重连成功后调用 `_window_selector.set_window_by_class()` 更新 UI 状态

## 5. 验证

- [ ] 5.1 手动测试：选择窗口 → 关闭应用 → 重启 → 检查是否自动重连
- [ ] 5.2 手动测试：旧版配置（无窗口标识）加载是否无异常
- [ ] 5.3 手动测试：窗口不存在时应用是否能正常启动
- [ ] 5.4 手动测试：手动重选窗口后配置是否覆盖旧标识
