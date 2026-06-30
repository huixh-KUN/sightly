## Why

`MainWindow`（742 行）混了 UI 外壳、后端装配、模块生命周期、配置同步、Panel-manager 中转 5 类职责，新增模块要改 5 处 if-elif 分支。模块构造接收 `MainWindow` 并反向调用，UI 层符号泄漏到后端。同时项目命名规范有多处违规（`*Module`/`*Executor` 后缀已废弃、`ClickHandler` 应为 `ClickWorker`、构造参数 `app` 是缩写、import 别名、文件跨目录同名）。借此抽离一次性还债。

## What Changes

- **新建 `ApplicationController`**（`core/application_controller.py`）：接管后端装配、模块生命周期协调、配置同步与持久化、Panel↔manager 中转。`MainWindow` 退化为纯 UI 外壳。
- **切断模块反向引用**：所有模块构造参数 `app` → `controller`，内部 `self.app` → `self.controller`。删除 MainWindow `__getattr__` 转发过渡。
- **统一模块接口**（**BREAKING**）：每个模块定义 `start() / stop() / test_group(idx) / set_config(cfg) / collect_config()`，Controller 用 `self.modules[id].start()` 调用，消灭 `_start_module/_stop_module` 的 if-elif 分支。旧方法名 `start_monitoring / start_timed_tasks / start_number_recognition / start_all_detection / start_all_groups` 等删除。
- **Worker+Manager 拆分**（**BREAKING**）：
  - `OCRModule` → `OCRWorker` + `OCRManager`
  - `TimedModule` → `TimedWorker` + `TimedManager`
  - `NumberModule` → `NumberWorker` + `NumberManager`
  - `AlarmModule` → `AlarmManager`（无 Worker，QObject 信号+声音）
  - `ImageDetection` → `ImageDetectionWorker`（`ImageDetectionManager` 保留）
- **命名整改**（**BREAKING**）：
  - `ClickHandler` → `ClickWorker`（文件 `click_handler.py` → `click_worker.py`）
  - `ScriptExecutor` → `ScriptWorker`
  - `KeyEventExecutor` → `KeyEventWorker`（文件 `modules/input.py` → `modules/key_event_worker.py`）
  - `ColorRecognition` 合并到 `ColorRecognizer`（utils/recognition.py），`ColorRecognitionManager` 调用它
  - `DDVirtualInput` → `DDInputBackend`，`PyAutoGUIInput` → `PyAutoGUIInputBackend`
- **业务数据迁各模块**：`ocr_groups/timed_groups/number_regions/image_groups/background_groups/alarm_*/settings_config` 从 MainWindow 实例变量迁到对应模块和 AppState。Panel `collect_config()` 经 Controller 直接喂对应模块。
- **`_on_test_group` UI 反馈改信号**：Controller 发 `test_result_ready(panel_id, status, detail)` 信号，MainWindow 连接弹 `QMessageBox`，Controller 不碰 widget。
- **更新 `项目命名规范.md`**：补全 `*Controller` `*Worker` `*Recognizer` `*Backend` `*Monitor` `*Picker` `*Selector` `*Switcher` `*Viewer` `*Notifier` `*Context` `*Proxy` 后缀；标记 `*Executor` `*Module` 为已废弃；补全 `create_*/delete_*/register_*/bind_*/request_*/apply_*/collect_*/load_*/save_*/detect_*/test_*/select_*/switch_*` 前缀；补「跨目录避免同名」「文件名与主类名一致」规则。

## Capabilities

### New Capabilities
- `application-controller`: 业务协调中枢，接管后端装配、模块生命周期、配置同步、Panel-manager 中转，与 MainWindow UI 外壳解耦

### Modified Capabilities
（无现有 spec，首期建仓）

## Impact

- **核心代码**：`ui/main_window.py`（大幅瘦身）、`core/application_controller.py`（新增）、`core/state.py`（Panel 信号连接目标转移）、所有 `modules/*.py`（拆类+重命名+改构造签名+统一接口）、`core/click_handler.py`→`click_worker.py`、`input/*.py`（后端重命名）、`utils/recognition.py`（吸收 ColorRecognition）、所有 `ui/*_panel.py`（Panel 构造改拿 Controller 引用，业务信号直连 Controller slot）
- **命名规范**：`项目命名规范.md` 同步更新
- **架构文档**：`架构文档.md` 描述与实现对齐（`ClickWorker` 等）
- **外部依赖**：无新增
- **破坏性**：模块类名、方法名、构造签名全部变更，任何外部引用旧名的代码需同步更新（项目内部全量替换）
- **测试覆盖**：项目无自动化测试，全靠手动冒烟（启动/启停/保存加载/各模块单测）
