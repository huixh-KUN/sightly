## 1. Part A — 规范文档更新

- [x] 1.1 更新 `项目命名规范.md` 类命名后缀表，补全 `*Controller` `*Worker` `*Recognizer` `*Backend` `*Monitor` `*Picker` `*Selector` `*Switcher` `*Viewer` `*Notifier` `*Context` `*Proxy`，新增「已废弃后缀」说明 `*Executor→*Worker`、`*Module→*Worker/*Manager`
- [x] 1.2 更新 `项目命名规范.md` 函数/方法命名前缀表，补全 `create_*/delete_*/register_*/bind_*/request_*/apply_*/collect_*/load_*/save_*/detect_*/test_*/select_*/switch_*`
- [x] 1.3 更新 `项目命名规范.md` 文件命名规则，补「跨目录避免同名」「文件名与主类名一致」「变量避免缩写（`controller` 不写 `app`/`ctrl`）」
- [x] 1.4 提交 Part A

## 2. Part B — ApplicationController 脚手架（行为不变）

- [x] 2.1 新建 `core/application_controller.py`，定义 `ApplicationController(QObject)` 类
- [x] 2.2 将 `MainWindow._init_backend` 的装配逻辑复制到 `ApplicationController.__init__`
- [x] 2.3 `MainWindow.__init__` 改为创建 `self.controller = ApplicationController(self)`，删除 `_init_backend` 调用
- [x] 2.4 MainWindow 保留 `__getattr__(self, name)` 过渡转发
- [x] 2.5 MainWindow 通过 `self.controller` 访问后端
- [x] 2.6 冒烟：启动应用、各模块启停、保存加载配置
- [x] 2.7 提交 Part B

## 3. Part C — 模块类重命名

- [x] 3.1 `core/click_handler.py` → `core/click_worker.py`，`ClickHandler` → `ClickWorker`
- [x] 3.2 `modules/script.py`：`ScriptExecutor` → `ScriptWorker`
- [x] 3.3 `modules/input.py` → `modules/key_event_worker.py`，`KeyEventExecutor` → `KeyEventWorker`
- [x] 3.4 `input/dd_input.py`：`DDVirtualInput` → `DDInputBackend`
- [x] 3.5 `input/pyautogui_input.py`：`PyAutoGUIInput` → `PyAutoGUIInputBackend`
- [x] 3.6 `modules/image.py`：`ImageDetection` → `ImageDetectionWorker`
- [x] 3.7 `modules/ocr.py`：`OCRModule` → `OCRManager`（单类改名，协程内联无需拆 Worker）
- [x] 3.8 `modules/timed.py`：`TimedModule` → `TimedManager`（单类改名）
- [x] 3.9 `modules/number.py`：`NumberModule` → `NumberManager`（单类改名）
- [x] 3.10 `modules/alarm.py`：`AlarmModule` → `AlarmManager`（无 Worker）
- [x] 3.11 `modules/color.py`：`ColorRecognition` → `ColorRecognitionWorker`（执行层，与 `ColorRecognizer` 算法层非重复，不合并）
- [x] 3.12 冒烟：各模块功能
- [x] 3.13 提交 Part C

## 4. Part D — 切断模块反向引用

- [x] 4.1 grep 所有 `modules/*.py`、`input/controller.py`、`utils/*.py` 中 `self.app.` 用法
- [x] 4.2 所有模块构造签名 `(self, app)` → `(self, controller)`
- [x] 4.3 模块内部所有 `self.app` → `self.controller`
- [x] 4.4 Controller 保留 `__getattr__` 转发到 MainWindow（MainWindow 的 `__getattr__` 也保留，用于 UI Panel 过渡）
- [x] 4.5 grep 确认后端模块无 `self.app.` 残留（UI Panel 仍通过 `self.app` 经 `__getattr__` 访问 logging_manager，过渡期可接受）
- [x] 4.6 冒烟：全套
- [x] 4.7 提交 Part D

## 5. Part E — 业务方法搬 ApplicationController

- [x] 5.1 搬 `_on_start_all/_on_stop_all` → `Controller.start_all/stop_all`
- [x] 5.2 搬 `_start_module/_stop_module` → `Controller._start_module/_stop_module`
- [x] 5.3 搬 `_shutdown_all_modules` → `Controller.shutdown_all`，`closeEvent` 委托
- [x] 5.4 搬 `_sync_panel_configs` → `Controller.sync_panel_configs`
- [x] 5.5 搬 `save_config` → `Controller.save_config`
- [x] 5.6 搬 `load_saved_config` → `Controller.load_config`
- [x] 5.7 搬 `_save_template_images` → `Controller._save_template_images`
- [x] 5.8 搬 `_on_config_loaded/_apply_settings/_migrate_old_config` → `Controller.on_config_loaded/apply_settings/migrate_old_config`
- [x] 5.9 搬 `_on_bg_window_selected/_on_bg_auto_reconnect` → `Controller.on_bg_window_selected/on_bg_auto_reconnect`
- [x] 5.10 搬 `_on_timed_position_selection` → `Controller.on_timed_position_selection`
- [x] 5.11 搬 `_on_test_group` → `Controller.test_group`，新增 `test_result_ready/test_message/test_wait_start/test_wait_end` 信号
- [x] 5.12 搬 `_on_settings_config_changed/_on_settings_shortcuts_changed` → `Controller`
- [x] 5.13 搬 `_init_signals/_init_module_bindings` → `Controller.wire_signals`
- [x] 5.14 冒烟通过
- [x] 5.15 提交 Part E

## 6. Part F — 统一模块接口 + 业务数据迁移

- [x] 6.1 `OCRManager` 定义 `start()/stop()/test_group()/set_config()/collect_config()`
- [x] 6.2 `TimedManager` 定义统一 5 方法
- [x] 6.3 `NumberManager` 定义统一 5 方法
- [x] 6.4 `AlarmManager` 定义 `start()/stop()/set_config()/collect_config()`
- [x] 6.5 `ImageDetectionManager` 定义统一 5 方法
- [x] 6.6 `BackgroundManager` 定义统一 5 方法，`run_once` → `test_group`
- [x] 6.7 `Controller._start_module/_stop_module` 改用 `self.modules[id].start()/stop()`，删 if-elif
- [x] 6.8 `Controller.test_group` 改用 `self.modules[id].test_group(idx)`，删分支
- [x] 6.9 业务数据迁移：`ocr_groups → ocr_manager.groups` 等，`sync_panel_configs` 直接喂模块 `set_config()`
- [x] 6.10 `alarm_sound_path/alarm_volume/alarm_volume_str → alarm_manager.sound_path/volume/volume_str`
- [x] 6.11 `settings_config` 保留在 Controller（经 `sync_panel_configs` 处理）
- [x] 6.12 删除 `MainWindow` 业务数据实例变量
- [x] 6.13 冒烟通过
- [x] 6.14 提交 Part F

## 7. Part G — 变量与 import 整理

- [x] 7.1 `tesseract_available` → `is_tesseract_available`
- [x] 7.2 删除 Controller 内 import 别名，直接用类名
- [x] 7.3 Panel 仍通过 `self.app`（MainWindow）经 `__getattr__` 转发访问 Controller（过渡期，功能正常）
- [x] 7.4 业务信号已在 `Controller.wire_signals` 中直连 Controller slot
- [x] 7.5 `config_loaded/workspace_changed` 走 AppState 广播到 `Panel.set_config`
- [x] 7.6 冒烟通过
- [x] 7.7 提交 Part G

## 8. Part H — 验证

- [x] 8.1 全量冒烟 10 项通过（启动/启停/保存加载/同步/统一接口/数据迁移/MainWindow 瘦身/信号/关闭）
- [x] 8.2 grep 确认无残留违规类名
- [x] 8.3 MainWindow 742 行 → 241 行，无业务方法
- [x] 8.4 无 lint/typecheck 配置，冒烟验证替代
- [x] 8.5 提交 Part H

## 遗留项（后续 change）

- UI Panel 的 `self.app` → `self.controller` 直连改造（当前经 `__getattr__` 转发，功能正常）
- 模块级函数 `_set_status_text(app, text)` / `select_alarm_sound(app)` 参数名 `app` → `controller`
- `utils/image.py` 与 `modules/image.py` 跨目录同名文件
- `input/keyboard.py` 文件名与内容（快捷键设置）不符
