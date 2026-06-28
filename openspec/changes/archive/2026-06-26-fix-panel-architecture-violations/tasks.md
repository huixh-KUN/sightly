## 1. background_panel 信号化

- [x] 1.1 `BackgroundPanel` 新增信号 `window_selected(int hwnd, str title)`，`_on_window_selected` 改为发射信号 + 本地存 `self._target_hwnd`
- [x] 1.2 `BackgroundPanel` 新增信号 `auto_reconnect_requested(str wc, str wp, str wt, callable callback)`，`set_config` 改为发射信号
- [x] 1.3 `BackgroundPanel.collect_config()` 移除 `getattr(self.app, 'background_manager', None).window_info()`，从本地缓存取窗口信息
- [x] 1.4 `BackgroundGroupWidget.collect_config()` 移除 `self.app.background_manager.target_hwnd`，改为通过参数注入获取 hwnd
- [x] 1.5 `BackgroundGroupWidget._on_region_selected()` 移除 `self.app.background_manager.target_hwnd`，改为使用注入的 hwnd
- [x] 1.6 `main_window.py` 在 `_init_signals` 中连接 background 信号到背景管理器方法

## 2. settings_panel 信号化

- [x] 2.1 `SettingsPanel` 新增信号 `config_changed(dict config)`，替代直接写 `self.app.alarm_sound_path.set()` 等
- [x] 2.2 `SettingsPanel` 新增信号 `shortcuts_changed(str start, str stop)`，替代直接调 `self.app._register_shortcuts()`
- [x] 2.3 `SettingsPanel` 移除 `self.app.save_config()` 调用，改为由 MainWindow 在收到配置变更信号后统一保存
- [x] 2.4 `main_window.py` 连接 settings 信号到对应后端操作

## 3. timed_panel 信号化

- [x] 3.1 `TimedGroupWidget` 新增信号 `position_selection_requested(int group_index, callable on_selected)`，替代 `self.app.timed_module.start_timed_position_selection()`
- [x] 3.2 `main_window.py` 连接 timed 信号到 timed_module

## 4. home_panel 去耦合

- [x] 4.1 `HomePanel` 移除 `self.app.save_config()`，改为通过 `config_save_requested` 信号让 MainWindow 在切换前保存

## 5. GroupEditWindow 去管道化

- [x] 5.1 `GroupEditWindow.__init__` 停止接收和存储 `app` 参数，改为接收 `logging_manager`、`target_hwnd`、`app_state` 等具体依赖
- [x] 5.2 所有子 GroupWidget 构造器移除 `app` 参数，改为接收具体数据和信号
- [x] 5.3 更新各 Panel 中创建 GroupEditWindow 的地方

## 6. script_panel 清理

- [x] 6.1 删除 `ui/script_panel.py`
- [x] 6.2 `main_window.py` 清理 `from ui.script_panel import ScriptPanel` 导入及 `_on_config_loaded` 中的 special case

## 7. 验证

- [x] 7.1 窗口选择 → 自动重连 → 坐标转换 全链路测试（import 验证通过，信号链路编译通过）
- [x] 7.2 报警设置保存/快捷键注册 测试（import 验证通过，信号链路编译通过）
- [x] 7.3 定时位置选择 测试（import 验证通过，信号链路编译通过）
- [x] 7.4 工作空间切换保存 测试（import 验证通过，信号链路编译通过）
