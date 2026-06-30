## Context

`MainWindow`（`ui/main_window.py`，742 行）当前承担 5 类职责：UI 外壳、后端装配、模块生命周期、配置同步、Panel↔manager 中转。7 个模块（OCR/Timed/Number/Alarm/Color/Image/Background）和 3 个基础设施（Logging/InputController/Config）在 `_init_backend` 实例化，全部传 `self`（MainWindow），模块因此反向持有 MainWindow 并调用其属性。新增模块需在 `_start_module/_stop_module/_shutdown_all_modules/_sync_panel_configs/_on_test_group` 5 处加 if-elif 分支。

命名层面，`项目命名规范.md` 有多处违规：`*Module`/`*Executor` 后缀已废弃但仍在用；`ClickHandler` 架构文档写 `ClickWorker` 但实现是 `ClickHandler`；模块构造参数 `app` 是缩写；`main_window.py` 用 `_OCR`/`_Timed` import 别名；`utils/image.py` 与 `modules/image.py` 跨目录同名。

项目无自动化测试（codegraph 报告 ⚠️ no covering tests），验证靠手动冒烟。

## Goals / Non-Goals

**Goals:**
- MainWindow 退化为纯 UI 外壳（~200 行），只保留 `_init_ui/_create_*/_navigate_to/eventFilter/closeEvent/_set_status/_on_theme_changed/log_message`
- 新建 `ApplicationController`（`core/application_controller.py`）接管所有业务协调
- 模块构造参数从 MainWindow 改为 Controller，切断 UI 层符号泄漏
- 每个模块统一 `start()/stop()/test_group(idx)/set_config(cfg)/collect_config()` 接口，Controller 用注册表调用，消灭 if-elif
- Worker+Manager 双层拆分：OCR/Timed/Number 拆为 Worker+Manager，Alarm 保留 Manager，Image 已有 Worker+Manager 仅重命名
- 命名整改：`ClickHandler→ClickWorker`、`*Executor→*Worker`、`ColorRecognition` 合并到 `ColorRecognizer`、输入后端统一 `*Backend` 后缀
- 业务数据迁各模块，MainWindow 不再当数据中转站
- 同步更新 `项目命名规范.md` 补全缺失后缀/前缀

**Non-Goals:**
- 不引入 `BackendContext` 协议抽象（模块直接接收 Controller，YAGNI）
- 不改 Panel 之间、Panel 与 AppState 的信号流结构（只改连接目标从 MainWindow 到 Controller）
- 不改工作空间/配置持久化的存储格式
- 不新增自动化测试框架
- 不改 `input/keyboard.py` 的 `setup_shortcuts` 函数式 API（仅文件名问题留独立 change）

## Decisions

### D1: 新建 ApplicationController 而非塞进 AppState
**选择：** 独立 `ApplicationController` 类（`core/application_controller.py`）。
**理由：** AppState 是纯状态广播中枢（Signal），塞协调逻辑会让它变胖成"状态+协调器"混合职责。Controller 作为协调器持有 AppState 并驱动模块，职责边界清晰。
**备选：** (a) 塞进 AppState——拒绝，职责混合；(b) 只抽 ModuleCoordinator（只管启停）——拒绝，MainWindow 仍偏胖，配置同步和中转 slot 仍留 UI 层。

### D2: 文件位置 `core/application_controller.py` 而非 `core/controller.py`
**选择：** `application_controller.py`。
**理由：** `input/controller.py` 已存在（含 `InputController`），`core/controller.py` 跨目录同名，违反规范「跨目录避免同名」。
**备选：** `core/controller.py`——拒绝，同名冲突。

### D3: 模块构造参数 `app` → `controller`，不引入 BackendContext 协议
**选择：** 直接传 Controller 实例，模块内部 `self.controller.xxx`。
**理由：** 协议抽象当前只有一个实现（Controller），YAGNI。模块真正需要的方法（logger/input/state/screenshot）通过 Controller 暴露的属性访问。后续若要解耦再加协议。
**备选：** 定义 `BackendContext` 协议（`logger/input/state/screenshot` 访问器）——拒绝，单实现的接口是过度抽象。

### D4: 渐进式迁移，MainWindow `__getattr__` 过渡转发
**选择：** Part B 脚手架阶段，MainWindow 保留 `__getattr__` 转发到 Controller，让模块的 `self.app.xxx` 暂时仍能用；Part D 切断反向引用后删除。
**理由：** 一次性改完构造签名+所有内部引用风险大，渐进式保证每步可运行可冒烟。
**备选：** 一次性大爆炸式重构——拒绝，无测试覆盖下风险过高。

### D5: 统一模块接口 `start()/stop()/test_group(idx)/set_config(cfg)/collect_config()`
**选择：** 每个模块定义统一 5 方法，Controller 用 `self.modules[id].start()` 调用，旧方法名删除。
**理由：** 消灭 5 处 if-elif 分支，新增模块只改 `self.modules` 注册表。方法名按规范前缀表：`start_*`/`stop_*`（已在表）、`test_*`/`collect_*`/`set_*`（规范已补）。
**备选：** 保留旧方法名作 alias 过渡——拒绝，alias 是技术债，一次性删干净。
**取舍：** 方法名变更破坏外部引用，但项目内部全量替换可控。

### D6: Worker+Manager 拆分按架构文档
**选择：** OCR/Timed/Number 拆为 Worker（执行单元，跑线程/协程）+ Manager（生命周期+组列表）；Alarm 保留单 `AlarmManager`（QObject 信号+声音，无执行单元）；Image 已有 `ImageDetection`+`ImageDetectionManager`，仅重命名为 `ImageDetectionWorker`。
**理由：** 符合架构文档「Worker+Manager 双层」和命名规范。Alarm 实质是单类，强行拆 Worker 是画蛇添足。
**备选：** 保留单类改后缀 `*Controller`——拒绝，架构文档已定 Worker+Manager 双层。

### D7: ColorRecognition 合并到 ColorRecognizer
**选择：** `modules/color.py` 的 `ColorRecognition` 合并到 `utils/recognition.py` 的 `ColorRecognizer`（无状态识别服务），`ColorRecognitionManager` 调用 `ColorRecognizer`。
**理由：** 两者职责重叠，`ColorRecognizer` 符合规范 `*Recognizer`（无状态识别服务），`ColorRecognitionManager` 管生命周期。
**备选：** 保留两层改名 `ColorRecognitionWorker`——拒绝，重复实现。

### D8: `_on_test_group` UI 反馈用信号回 MainWindow
**选择：** Controller 发 `test_result_ready(panel_id, status, detail)` 信号，MainWindow 连接弹 `QMessageBox`。Controller 不碰 widget。
**理由：** 保持 Controller 不碰 UI 层 widget，符合"跨层走 Signal"。QTimer 等待逻辑留在 Controller。
**备选：** Controller 持 window 引用直接弹窗——拒绝，Controller 站到 UI 层。

### D9: Panel 业务信号直连 Controller slot
**选择：** Panel 构造时拿 Controller 引用，`test_group_requested` 等业务信号直接 `connect(Controller.xxx)`。`config_loaded/workspace_changed` 仍走 AppState 广播到 `Panel.set_config`。
**理由：** 最少中转。AppState 仍负责状态广播（配置加载/工作空间切换），Controller 负责业务协调（启停/测试/中转）。
**备选：** Panel 连 AppState，AppState 转发 Controller——拒绝，多一跳无收益。

### D10: 输入后端统一 `*Backend` 后缀
**选择：** `DDVirtualInput→DDInputBackend`、`PyAutoGUIInput→PyAutoGUIInputBackend`、`Win32InputBackend` 保留。
**理由：** 规范 `*Backend` = 策略模式后端实现，输入后端正是策略模式可替换后端。
**备选：** 统一 `*InputWorker`——拒绝，`*Backend` 更准确表达策略模式语义。

## Risks / Trade-offs

- **[改动面极大]** 30+ 文件，重命名+拆类+搬方法+改构造签名+统一接口。→ 渐进式 8 Part 迁移，每 Part 独立可运行可冒烟，建议每 Part 独立提交便于回滚。
- **[无测试覆盖]** 全靠手动冒烟，回归风险高。→ 每 Part 完成后冒烟清单：启动/启停/保存加载/各模块单测/工作空间切换。
- **[Worker+Manager 拆分暴露隐藏状态共享]** OCRModule/TimedModule/NumberModule 当前单类混合，拆分时线程/协程状态可能分布不合理。→ 拆分时先理清职责边界：Worker 只跑执行循环，Manager 持有组列表和 Worker 实例字典；若发现状态共享问题，记录到 Open Questions。
- **[ColorRecognition 合并行为变化]** 两个类方法集可能不完全一致。→ 合并前对比两者方法，逐一确认调用方，合并后冒烟颜色识别功能。
- **[旧方法名删除破坏外部引用]** `start_monitoring` 等旧名删除。→ 项目内部全量 grep 替换，无外部 SDK 调用方。
- **[closeEvent 时序]** Controller.shutdown_all 必须在 UI 销毁前完成。→ closeEvent 先调 Controller.shutdown_all 再 super().closeEvent。
- **[过渡期 `__getattr__` 性能]** Part B-D 之间每次属性访问走 `__getattr__` 转发。→ 过渡期短，Part D 完成即删除，可接受。

## Migration Plan

按 8 Part 顺序实施，每 Part 独立可运行、独立提交：

1. **Part A — 规范文档更新**：更新 `项目命名规范.md`，纯文档无代码风险。
2. **Part B — 脚手架**：建 `ApplicationController.__init__` 接管装配，MainWindow 持 Controller + `__getattr__` 转发。冒烟：启动/启停/保存加载。
3. **Part C — 模块类重命名 + Worker+Manager 拆分**：全项目 grep 替换类名和文件名引用。冒烟：各模块功能。
4. **Part D — 切断反向引用**：构造签名 `app→controller`，删 `__getattr__`。冒烟：全套。
5. **Part E — 业务方法搬 Controller**：逐个搬，每搬一个冒烟一次。
6. **Part F — 统一模块接口**：定义 5 方法，Controller 用注册表调用，删 if-elif。业务数据迁各模块。冒烟：启停/测试/配置。
7. **Part G — 变量与 import 整理**：`tesseract_available→is_tesseract_available`、删 import 别名、Panel 拿 Controller 引用。冒烟：全套。
8. **Part H — 验证**：全量冒烟 + lint/typecheck。

**回滚策略**：每 Part 独立 git commit，出问题 `git revert` 单 Part commit。Part B 脚手架是关键节点，B 之前可整体放弃。

## Open Questions

- OCRModule/TimedModule/NumberModule 拆分时，Worker 和 Manager 的具体职责边界需在实施时确认（Worker 是否持有组配置？还是 Manager 持有并传给 Worker？）——倾向 Manager 持有组列表，Worker 接收单组配置参数。
- `ColorRecognition` 与 `ColorRecognizer` 方法集对比待实施时确认。
- `modules/input.py` 改名 `key_event_worker.py` 后，`input/` 目录是否仍有命名混淆（`input/` 目录名 vs `modules/key_event_worker.py`）——当前可接受，留独立 change 评估。
