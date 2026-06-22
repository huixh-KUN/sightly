# 项目架构分析

## 目录结构

```
autodoor/
├── main.py                    # 入口
├── core/                      # 核心基础设施层
│   ├── state.py               # AppState — 集中状态管理（信号驱动）
│   ├── workspace.py           # WorkspaceManager — 工作空间文件 I/O
│   ├── config.py              # ConfigManager + ConfigVar（含 tkinter 兼容）
│   ├── logging.py             # LoggingManager — 三级日志
│   ├── controller.py          # ModuleController — 旧版启停控制
│   ├── events.py              # EventManager — 优先级事件队列
│   ├── threading.py           # ThreadManager — 线程生命周期管理
│   ├── priority_lock.py       # PriorityLock — 优先级互斥锁
│   ├── click_handler.py       # ClickHandler — 统一鼠标点击
│   └── platform.py            # PlatformAdapter — Windows 平台适配
│
├── modules/                   # 后端功能模块层
│   ├── ocr.py                 # OCRModule (优先级3)
│   ├── timed.py               # TimedModule (优先级5)
│   ├── number.py              # NumberModule (优先级6)
│   ├── image.py               # ImageDetection + Manager (优先级4)
│   ├── color.py               # ColorRecognition + Manager (优先级2)
│   ├── background.py          # BackgroundMonitor + Manager (优先级1)
│   ├── script.py              # ScriptModule + ScriptExecutor (优先级1)
│   ├── alarm.py               # AlarmModule
│   ├── input.py               # KeyEventExecutor
│   └── recorder.py            # RecorderBase（录制基类）
│
├── input/                     # 输入后端层（策略模式）
│   ├── base.py                # BaseInputController（抽象基类）
│   ├── controller.py          # InputController（工厂/兼容层）
│   ├── dd_input.py            # DD 虚拟键盘实现
│   ├── pyautogui_input.py     # PyAutoGUI 实现
│   └── win32_input.py         # Win32 API 实现
│
├── utils/                     # 通用工具层
│   ├── screenshot.py          # ScreenshotManager（单例+缓存+优先级锁）
│   ├── recognition.py         # OCR/Image/Color/Number 识别器
│   ├── window_capture.py      # 窗口截取（win32gui）
│   ├── quick_switch.py        # 窗口快速切换
│   ├── coordinate.py          # 坐标转换
│   └── image.py               # 图像预处理
│
├── ui/                        # UI 层（PySide6）
│   ├── main_window.py         # MainWindow — 主窗口（组装点）
│   ├── home_panel.py          # 首页面板（模块卡片+启停+日志）
│   ├── ocr_panel.py           # OCR 配置面板
│   ├── timed_panel.py         # 定时配置面板
│   ├── number_panel.py        # 数字识别配置面板
│   ├── image_panel.py         # 图像检测配置面板
│   ├── background_panel.py    # 后台监控配置面板
│   ├── script_panel.py        # 脚本编辑面板
│   ├── settings_panel.py      # 设置面板
│   ├── theme.py               # 主题管理（暗色/亮色 QSS）
│   └── components/            # 可复用组件库
│       ├── switch_button.py   # SwitchButton — 自绘制开关
│       ├── toggle.py          # Toggle — 开关+标签
│       ├── module_card.py     # ModuleCard — 模块卡片
│       ├── combo_box.py       # ComboBox — 自绘制下拉框
│       ├── log_viewer.py      # LogViewer — 日志查看器
│       ├── key_capture.py     # KeyCaptureWidget — 按键捕获
│       ├── window_selector.py # WindowSelector — 窗口选择器
│       ├── region_overlay.py  # RegionOverlay — 区域选择
│       ├── screenshot.py      # ScreenCaptureOverlay — 截图覆盖
│       ├── template_picker.py # TemplatePicker — 模板选择器
│       ├── script_commands.py # Key/Delay/MouseCommandCard
│       └── settings_cards.py  # GeneralSettings/AlarmSettings/AboutCard
│
├── config/                    # 运行时配置
├── workspace/                 # 工作空间数据
├── logs/                      # 日志文件
├── voice/                     # 报警音频
├── icon/                      # 应用图标
└── drivers/                   # 驱动文件（DD虚拟键盘等）
```

---

## 核心架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                          main.py                                │
│                          └── MainWindow                         │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────────────┐ │
│  │  AppState    │  │LoggingManager│  │    ConfigManager        │ │
│  │  (信号中枢)   │  │  (三级日志)   │  │   (配置读写)             │ │
│  └──────┬──────┘  └──────────────┘  └─────────────────────────┘ │
│         │ Signal                                                 │
├─────────┼───────────────────────────────────────────────────────┤
│  ┌──────▼──────┐                                                │
│  │ UI Panels   │  HomePanel / OCRPanel / TimedPanel / ...      │
│  │ (PySide6)   │  组件: SwitchButton, Toggle, ModuleCard, ...  │
│  └──────┬──────┘                                                │
│         │ collect_config() / set_config()                       │
├─────────┼───────────────────────────────────────────────────────┤
│  ┌──────▼──────┐                                                │
│  │   Modules   │  OCR / Timed / Number / Image / Color /       │
│  │  (功能模块)  │  Background / Script / Alarm                   │
│  └──────┬──────┘                                                │
│         │ 优先级锁                                               │
├─────────┼───────────────────────────────────────────────────────┤
│  ┌──────▼──────┐  ┌──────────────┐  ┌─────────────────────────┐ │
│  │InputController│ │ScreenshotManager││ Recognition Utils     │ │
│  │  (输入后端)   │ │ (截图管理器)    │ │ OCR/Image/Color/Number│ │
│  │ DD/PyAutoGUI │ │ (单例+缓存)    │ │ (RapidOCR/OpenCV)     │ │
│  └─────────────┘  └──────────────┘  └─────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  PriorityLock (Number:6 > Timed:5 > Image:4 > OCR:3 > Color:2 > BG:1)
└─────────────────────────────────────────────────────────────────┘
```

---

## 数据流

```
UI 控件 → Signal → AppState → Signal → MainWindow → Module.start()
                                                    ↓
Module 循环 → ScreenshotManager.get_region_screenshot(priority)
                  ↓ PriorityLock 竞争
             Recognition Utils 识别
                  ↓
             KeyEventExecutor / ClickHandler / AlarmModule
```

---

## 配置持久化

```
保存: Panel.collect_config() → AppState.save_current() → WorkspaceManager.save() → workspace/{name}/config.json
加载: WorkspaceManager.load() → AppState._load_workspace() → config_loaded Signal → Panel.set_config()
```

---

## 核心类职责

### 核心基础设施 (core/)

| 类 | 文件 | 职责 |
|---|---|---|
| **AppState** | `state.py` | 集中状态管理器。管理模块启用/禁用状态、工作空间切换、配置加载/保存。通过 Qt Signal 广播状态变化。 |
| **WorkspaceManager** | `workspace.py` | 纯文件 I/O 层。管理 `workspace/` 目录下的工作空间文件夹。 |
| **ConfigManager** | `config.py` | 旧版配置管理器（tkinter 遗留）。负责从 JSON 读写完整配置。 |
| **LoggingManager** | `logging.py` | 三级日志：`debug()` → 仅文件、`log_message()` → 文件+GUI、`error()` → 三路输出。 |
| **EventManager** | `events.py` | 基于 `PriorityQueue` 的事件队列，支持模块优先级调度。 |
| **ThreadManager** | `threading.py` | 统一线程生命周期管理。 |
| **PriorityLock** | `priority_lock.py` | 基于堆的优先级互斥锁，确保高优先级模块优先获取截图/输入资源。 |
| **ClickHandler** | `click_handler.py` | 统一鼠标点击处理器，封装随机偏移、坐标验证、日志记录。 |

### 功能模块 (modules/)

| 类 | 优先级 | 职责 |
|---|---|---|
| **OCRModule** | 3 | 截屏 → RapidOCR 识别文字 → 关键词匹配 → 触发按键/点击/报警 |
| **TimedModule** | 5 | 按固定间隔触发按键操作（每组独立线程） |
| **NumberModule** | 6 | 截屏 → OCR 识别数字 → 低于阈值时触发动作 |
| **ImageDetection** | 4 | 模板匹配检测（OpenCV matchTemplate） |
| **ColorRecognition** | 2 | 像素级颜色匹配 |
| **BackgroundMonitor** | 1 | 监控后台窗口区域变化（OCR/图像/颜色三种模式） |
| **ScriptModule** | 1 | 脚本引擎：解析自定义语法，支持录制和循环执行 |
| **AlarmModule** | — | 报警音播放 |

### UI 组件 (ui/components/)

| 组件 | 职责 |
|---|---|
| **SwitchButton** | 自绘制开关按钮，支持动画 |
| **Toggle** | SwitchButton + 标签组合 |
| **ModuleCard** | 模块卡片（图标+名称+描述+开关+状态） |
| **ComboBox** | 自绘制下拉框 |
| **LogViewer** | 日志显示组件（线程安全，QTimer 批量更新） |
| **KeyCaptureWidget** | 按键捕获组件 |
| **WindowSelector** | 窗口选择器 |
| **RegionOverlay** | 全屏区域选择覆盖层 |
| **ScreenCaptureOverlay** | 截图选择覆盖层 |
| **TemplatePicker** | 模板选择器 |

---

## 依赖关系

```
main.py
  └── MainWindow
        ├── core.state.AppState
        ├── core.logging.LoggingManager
        ├── core.config.ConfigManager
        ├── input.controller.InputController
        ├── core.threading.ThreadManager
        ├── core.events.EventManager
        │
        ├── modules.ocr.OCRModule
        │     ├── utils.screenshot.ScreenshotManager (singleton)
        │     ├── utils.recognition.OCRRecognizer
        │     ├── core.priority_lock.PriorityLock
        │     └── core.click_handler.ClickHandler
        │
        ├── modules.timed.TimedModule
        │     ├── core.priority_lock.PriorityLock
        │     └── core.click_handler.ClickHandler
        │
        ├── modules.number.NumberModule
        │     ├── utils.screenshot.ScreenshotManager
        │     └── utils.recognition.NumberRecognizer
        │
        ├── modules.image.ImageDetectionManager
        │     ├── modules.image.ImageDetection (per-group)
        │     │     ├── utils.screenshot.ScreenshotManager
        │     │     ├── utils.recognition.ImageRecognizer
        │     │     └── core.click_handler.ClickHandler
        │
        ├── modules.color.ColorRecognitionManager
        │     └── modules.color.ColorRecognition
        │           ├── utils.screenshot.ScreenshotManager
        │           └── utils.recognition.ColorRecognizer
        │
        ├── modules.background.BackgroundManager
        │     └── modules.background.BackgroundMonitor (per-group)
        │           ├── utils.window_capture.*
        │           ├── utils.quick_switch.QuickSwitchBackend
        │           ├── utils.coordinate.RelativeCoordinate/WindowCoordinate
        │           └── utils.recognition.{OCRRecognizer, ImageRecognizer, ColorRecognizer}
        │
        ├── modules.script.ScriptModule
        │     └── modules.script.ScriptExecutor
        │
        └── modules.alarm.AlarmModule
              └── winsound / QtMultimedia
```

---

## 设计模式

1. **集中状态管理 + 信号驱动通信** — AppState 作为通信中枢，通过 Qt Signal 实现松耦合
2. **工作空间系统** — 多工作空间隔离配置，支持切换和持久化
3. **优先级锁** — PriorityLock 基于堆实现，Number(6) > Timed(5) > Image(4) > OCR(3) > Color(2) > BG(1)
4. **输入后端策略模式** — InputController 工厂选择 DD/PyAutoGUI/Win32
5. **识别引擎统一化** — utils/recognition.py 提供统一的识别器类

---

## 技术债务

1. **两套代码路径并存** — core/config.py 中 ConfigManager 仍含 tkinter 风格代码，AppState 是新体系但未完全替代
2. **MainWindow 过重** — 同时承担 UI 容器、模块生命周期管理、配置协调三重职责
3. **模块与 UI 紧耦合** — 所有模块通过 self.app 直接访问 MainWindow 的全部属性
4. **线程管理不一致** — 部分模块用 app.is_running 标志，部分用 threading.Event
5. **ConfigVar 兼容层** — strip_configvar() 需递归去除包装后再序列化，增加复杂度
