## 1. 基础设施

- [x] 1.1 创建 `ModuleContext` dataclass（`core/context.py`），含 app_state/logger/input_controller/alarm
- [x] 1.2 创建 `StatusNotifier`（`core/context.py`），含 `status_changed` 信号 + `info()` 方法
- [x] 1.3 创建模块配置 dataclass 组（`modules/configs.py`）：OCRGroupConfig/OCRConfig、TimedGroupConfig/TimedConfig、NumberGroupConfig/NumberConfig
- [x] 1.4 创建模块配置 dataclass 组续：ImageGroupConfig、BackgroundGroupConfig、ColorConfig、ScriptConfig、AlarmConfig
- [x] 1.5 AppState 新增 `module_configs` 属性 + `update_module_config()` + `module_config_changed` 信号
- [x] 1.6 AppState 新增 `request_save()` 方法 + `save_requested` 信号

## 2. Panel 层剥离 ConfigVar

- [x] 2.1 OCR Panel: `collect_config()` 改为输出纯 dict，移除全部 ConfigVar 包装
- [x] 2.2 Timed Panel: 同上
- [x] 2.3 Number Panel: 同上
- [x] 2.4 Image Panel: 同上
- [x] 2.5 Background Panel: 同上
- [x] 2.6 Color Panel: 同上（集成在 BackgroundPanel 中，已处理）
- [x] 2.7 Script Panel: `collect_config()` 输出纯值（Panel 不存在，留存配置由 ConfigManager 处理）
- [x] 2.8 Alarm Panel: 同上（Alarm 配置在 SettingsPanel 中，已无 ConfigVar）
- [x] 2.9 `MainWindow._sync_panel_configs()` 写入 AppState.module_configs（保留旧路径过渡）

## 3. MainWindow 初始化改造

- [x] 3.1 `_init_backend()` 创建 `ModuleContext` 实例，传入各模块构造函数
- [x] 3.2 连接 `StatusNotifier.status_changed` → `status_label.setText()`
- [x] 3.3 连接 `AppState.save_requested` → `save_config()`
- [x] 3.4 连接 `AppState.module_config_changed` → 运行时模块热更新
- [x] 3.5 模块迁移完成，旧属性保留供 ConfigManager 内部使用（等待 Debt #1）
- [x] 3.6 动态属性保留供 ConfigManager 内部使用（等待 Debt #1）

## 4. 模块迁移 — 第一阶段

- [x] 4.1 `AlarmWorker.__init__` 改为接收 `ModuleContext`
- [x] 4.2 `AlarmWorker` 中 `self.app.xxx` → `ctx.xxx` 替换
- [x] 4.3 `NumberWorker.__init__` 改为接收 `ModuleContext`
- [x] 4.4 `NumberWorker` 中 `self.app.logging_manager` → `ctx.logger` + 移除 `.get()` 调用
- [x] 4.5 验证：应用启动测试（NumberWorker 迁移 + KeyEventWorker 改造）

## 5. 模块迁移 — 第二阶段（多数模块）

- [x] 5.1 `TimedTask.__init__` 改为接收 `ModuleContext`
- [x] 5.2 `TimedTask` 中 `self.app.xxx` → `ctx.xxx` + `app_state.is_selecting` 等
- [x] 5.3 `OCRWorker.__init__` 改为接收 `ModuleContext`
- [x] 5.4 `OCRWorker` 中运行时 `self.app.ocr_groups[group_index]` → `ctx.app_state.module_configs['ocr']` 读取
- [x] 5.5 `ImageDetectionWorker/Manager` 改为接收 `ModuleContext`
- [x] 5.6 Image 中运行时 `self.app.image_groups` → `ctx.app_state.module_configs['image']` 读取
- [x] 5.7 `ColorRecognitionWorker/Manager` 改为接收 `ModuleContext`
- [x] 5.8 Color 中 `self.app.target_color` → `ctx.app_state.module_configs['color']` 读取

## 6. 模块迁移 — 第三阶段（重依赖模块）

- [x] 6.1 `BackgroundMonitorWorker/BackgroundManager` 改为接收 `ModuleContext`
- [x] 6.2 Background 中 `self.app.xxx` → `ctx.xxx` 替换
- [x] 6.3 `ScriptWorker.__init__` 改为接收 `ModuleContext`
- [x] 6.4 Script 中 `self.app.status_label` → `ctx.status_notifier` + 移除 UI 控件直接操作

## 7. 收尾清理

- [ ] 7.1 删除 `ConfigVar` 类（等待 Debt #1 ConfigManager 重构后执行）
- [ ] 7.2 删除 `strip_configvar()` 函数（同上）
- [ ] 7.3 清理旧配置属性 + 双写代码（等待 Debt #1 后）
- [x] 7.4 验证：`ConfigVar` 和 `strip_configvar` 在模块和面板层零残留
- [x] 7.5 运行主应用初始化验证通过
