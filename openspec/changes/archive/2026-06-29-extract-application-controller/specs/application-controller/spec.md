## ADDED Requirements

### Requirement: ApplicationController 接管后端装配
系统 SHALL 提供一个 `ApplicationController` 类（位于 `core/application_controller.py`），负责实例化 `LoggingManager`、`InputController`、`ConfigManager` 和所有功能模块（OCR/Timed/Number/Alarm/Color/Image/Background），并维护 `self.modules` 注册表。`MainWindow` SHALL NOT 直接实例化后端模块，仅通过 `self.controller` 访问。

#### Scenario: 启动时后端装配
- **WHEN** 应用启动并创建 `MainWindow`
- **THEN** `ApplicationController.__init__` 完成所有后端实例化和模块注册，`MainWindow` 只持有 Controller 引用

#### Scenario: 模块注册表访问
- **WHEN** Controller 或其他组件需要按 ID 访问模块
- **THEN** `self.modules` 字典提供 `{'ocr','timed','number','alarm','color','image','background'}` 到模块实例的映射

### Requirement: MainWindow 退化为纯 UI 外壳
`MainWindow` SHALL 只保留 UI 外壳职责：`_init_ui/_create_header/_create_sidebar/_create_content/_navigate_to/eventFilter/closeEvent/_set_status/_on_theme_changed/log_message`。所有业务协调（模块启停、配置同步、Panel-manager 中转）SHALL 移交 `ApplicationController`。

#### Scenario: MainWindow 不含业务方法
- **WHEN** 检查 `MainWindow` 源码
- **THEN** 不存在 `_on_start_all/_on_stop_all/_start_module/_stop_module/_sync_panel_configs/save_config/load_saved_config/_on_test_group` 等业务方法，这些方法位于 `ApplicationController`

### Requirement: 模块构造参数为 Controller
所有模块和基础设施类 SHALL 接收 `ApplicationController` 实例作为构造参数（参数名 `controller`），SHALL NOT 接收 `MainWindow`。模块内部 SHALL 通过 `self.controller` 访问依赖，SHALL NOT 反向引用 UI 层。

#### Scenario: 模块不持有 MainWindow
- **WHEN** 检查任意模块（`OCRWorker`/`TimedWorker`/`NumberWorker`/`AlarmManager`/`ImageDetectionManager`/`BackgroundManager`/`ClickWorker` 等）的构造签名
- **THEN** 参数名为 `controller`，类型为 `ApplicationController`，无 `main_window`/`app`/`main` 参数

#### Scenario: 模块不访问 UI 层符号
- **WHEN** 检查模块内部代码
- **THEN** 不存在 `self.main_window.xxx` 或 `self.app.xxx` 形式的 UI 层访问，依赖通过 `self.controller` 或经 AppState 信号获取

### Requirement: 统一模块接口
每个功能模块 SHALL 实现统一接口方法：`start()`、`stop()`、`test_group(idx) -> dict`、`set_config(cfg)`、`collect_config() -> list|dict`。`ApplicationController` SHALL 通过 `self.modules[id].start()` 形式调用，SHALL NOT 使用 if-elif 分支按模块 ID 选择启动方法。

#### Scenario: Controller 启动所有已启用模块
- **WHEN** 用户点击启动且多个模块已启用
- **THEN** Controller 遍历 `app_state.enabled_modules()`，对每个 ID 调用 `self.modules[id].start()`，无 if-elif 分支

#### Scenario: 新增模块无需改 Controller
- **WHEN** 新增一个功能模块
- **THEN** 只需在 `self.modules` 注册表添加条目，无需修改 `_start_module/_stop_module` 等方法体

#### Scenario: 单组测试
- **WHEN** 用户在面板点击某组的测试按钮
- **THEN** Controller 调用 `self.modules[panel_id].test_group(idx)`，返回 `{"matched": bool, "executed": bool, "detail": str}` 形式结果

### Requirement: Worker+Manager 双层结构
OCR/Timed/Number 模块 SHALL 拆分为 `*Worker`（执行单元，跑线程/协程循环）+ `*Manager`（生命周期管理，持有组列表和 Worker 实例字典）。Alarm SHALL 为单 `AlarmManager`（无 Worker）。Image SHALL 为 `ImageDetectionWorker` + `ImageDetectionManager`。Color SHALL 为 `ColorRecognitionManager` 调用 `ColorRecognizer`（无状态识别服务）。

#### Scenario: OCR 模块拆分
- **WHEN** 检查 `modules/ocr.py`
- **THEN** 存在 `OCRWorker`（执行 OCR 识别循环）和 `OCRManager`（管理组列表和 Worker 实例），不存在 `OCRModule` 类

#### Scenario: Alarm 不拆分
- **WHEN** 检查 `modules/alarm.py`
- **THEN** 存在 `AlarmManager`（QObject，信号+声音播放），不存在 `AlarmWorker` 或 `AlarmModule`

### Requirement: 命名整改对齐规范
类名、文件名、方法名、变量名 SHALL 对齐 `项目命名规范.md`。具体：`ClickHandler→ClickWorker`（文件 `click_handler.py→click_worker.py`）、`ScriptExecutor→ScriptWorker`、`KeyEventExecutor→KeyEventWorker`（文件 `modules/input.py→modules/key_event_worker.py`）、`ColorRecognition` 合并到 `ColorRecognizer`、`DDVirtualInput→DDInputBackend`、`PyAutoGUIInput→PyAutoGUIInputBackend`。`*Module`/`*Executor` 后缀 SHALL NOT 出现在新代码中。

#### Scenario: ClickHandler 不存在
- **WHEN** 检查 `core/click_handler.py`
- **THEN** 文件已改名为 `core/click_worker.py`，类名为 `ClickWorker`，全项目无 `ClickHandler` 引用

#### Scenario: 输入后端后缀统一
- **WHEN** 检查 `input/dd_input.py`、`input/pyautogui_input.py`、`input/win32_input.py`
- **THEN** 类名分别为 `DDInputBackend`、`PyAutoGUIInputBackend`、`Win32InputBackend`，无 `DDVirtualInput`/`PyAutoGUIInput` 旧名

### Requirement: 业务数据归属各模块
`ocr_groups/timed_groups/number_regions/image_groups/background_groups` SHALL 存储在对应模块（`OCRManager.groups` 等），SHALL NOT 存储在 `MainWindow` 实例变量。`alarm_sound_path/alarm_volume/alarm_enabled` SHALL 存储在 `AlarmManager`。`settings_config` SHALL 存储在 `AppState`。Panel `collect_config()` SHALL 经 Controller 直接喂给对应模块，SHALL NOT 经 MainWindow 实例变量中转。

#### Scenario: MainWindow 不含业务数据实例变量
- **WHEN** 检查 `MainWindow.__init__`
- **THEN** 不存在 `self.ocr_groups/self.timed_groups/self.number_regions/self.image_groups/self.background_groups/self.alarm_sound_path/self.alarm_volume` 等业务数据变量

#### Scenario: 配置同步直接喂模块
- **WHEN** Controller 同步面板配置
- **THEN** `OCRPanel.collect_config()` 的结果直接赋给 `ocr_manager.set_config(config)`，不经 MainWindow 实例变量

### Requirement: test_group UI 反馈走信号
`ApplicationController.test_group` SHALL 不直接操作 `QMessageBox` 等 widget。Controller SHALL 发出 `test_result_ready(panel_id, status, detail)` 信号，`MainWindow` SHALL 连接该信号并弹出 `QMessageBox` 展示结果。

#### Scenario: Controller 不碰 widget
- **WHEN** 检查 `ApplicationController.test_group`
- **THEN** 方法体内无 `QMessageBox`/`QDialog`/`QWidget` 等 UI 类的引用，只发出 `test_result_ready` 信号

#### Scenario: MainWindow 弹窗展示结果
- **WHEN** Controller 发出 `test_result_ready('ocr', '检测通过', '...')`
- **THEN** MainWindow 连接的 slot 弹出 `QMessageBox` 显示状态和详情

### Requirement: Panel 业务信号直连 Controller
Panel 的业务信号（`test_group_requested`、`window_selected`、`auto_reconnect_requested`、`position_selection_requested`、`config_changed`、`shortcuts_changed`、`config_save_requested`）SHALL 直接连接到 `ApplicationController` 的 slot，SHALL NOT 经 MainWindow 中转。`config_loaded/workspace_changed` 仍走 AppState 广播到 `Panel.set_config`。

#### Scenario: Panel 不经 MainWindow 调业务
- **WHEN** 用户在 `BackgroundPanel` 选择窗口
- **THEN** `window_selected` 信号直接连接到 `Controller.on_bg_window_selected`，不经过 `MainWindow._on_bg_window_selected`

#### Scenario: 配置加载仍走 AppState
- **WHEN** 工作空间加载完成
- **THEN** `AppState.config_loaded` 信号广播到所有 Panel 的 `set_config`，不经过 Controller 中转

### Requirement: 命名规范文档补全
`项目命名规范.md` SHALL 补全后缀表：`*Controller` `*Worker` `*Recognizer` `*Backend` `*Monitor` `*Picker` `*Selector` `*Switcher` `*Viewer` `*Notifier` `*Context` `*Proxy`。SHALL 标记 `*Executor` `*Module` 为已废弃后缀（归并说明）。SHALL 补全前缀表：`create_*/delete_*/register_*/bind_*/request_*/apply_*/collect_*/load_*/save_*/detect_*/test_*/select_*/switch_*`。SHALL 补「跨目录避免同名」「文件名与主类名一致」文件命名规则。

#### Scenario: 规范覆盖现状后缀
- **WHEN** 检查 `项目命名规范.md` 类命名后缀表
- **THEN** 包含 `*Controller` `*Worker` `*Recognizer` `*Backend` `*Monitor` `*Picker` `*Selector` `*Switcher` `*Viewer` `*Notifier` `*Context` `*Proxy` 条目，且有「已废弃后缀」说明 `*Executor→*Worker`、`*Module→*Worker/*Manager`

#### Scenario: 规范覆盖现状前缀
- **WHEN** 检查 `项目命名规范.md` 函数/方法命名表
- **THEN** 包含 `create_*/delete_*/register_*/bind_*/request_*/apply_*/collect_*/load_*/save_*/detect_*/test_*/select_*/switch_*` 条目
