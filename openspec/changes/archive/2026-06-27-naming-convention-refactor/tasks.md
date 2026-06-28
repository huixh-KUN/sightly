## 1. 工具层重命名

- [x] 1.1 `utils/memory.py` — `MemoryMonitor` → `MemoryManager`，更新所有引用
- [x] 1.2 `utils/coordinate.py` — `RelativeCoordinate` → `RelativeCoordinateConverter`，更新所有引用
- [x] 1.3 `utils/coordinate.py` — `WindowCoordinate` → `WindowCoordinateConverter`，更新所有引用
- [x] 1.4 `utils/quick_switch.py` — `QuickSwitchBackend` → `QuickSwitchWorker`，更新所有引用

## 2. 模块层重命名

- [x] 2.1 `modules/ocr.py` — `OCRModule` → `OCRWorker`，更新所有引用
- [x] 2.2 `modules/number.py` — `NumberModule` → `NumberWorker`，更新所有引用
- [x] 2.3 `modules/timed.py` — `TimedModule` → `TimedTask`，更新所有引用
- [x] 2.4 `modules/script.py` — `ScriptModule` → `ScriptWorker`，更新所有引用
- [x] 2.5 `modules/script.py` — `ScriptExecutor` → `ScriptTask`，更新所有引用
- [x] 2.6 `modules/alarm.py` — `AlarmModule` → `AlarmWorker`，更新所有引用
- [x] 2.7 `modules/image.py` — `ImageDetection` → `ImageDetectionWorker`，更新所有引用
- [x] 2.8 `modules/color.py` — `ColorRecognition` → `ColorRecognitionWorker`，更新所有引用
- [x] 2.9 `modules/background.py` — `BackgroundMonitor` → `BackgroundMonitorWorker`，更新所有引用
- [x] 2.10 `modules/input.py` — `KeyEventExecutor` → `KeyEventWorker`，更新所有引用
- [x] 2.11 `modules/input.py` — `setKey()` → `set_key()` 方法名修正

## 3. 核心层重命名

- [x] 3.1 `core/click_handler.py` — `ClickHandler` → `ClickWorker`，更新所有引用

## 4. 输入层重命名

- [x] 4.1 `input/base.py` — `BaseInputController` → `BaseInputManager`，更新所有引用
- [x] 4.2 `input/controller.py` — `InputController` → `InputManager`，更新所有引用
- [x] 4.3 `input/win32_input.py` — `Win32InputBackend` → `Win32Input`，更新所有引用

## 5. UI 面板引用更新

- [x] 5.1 更新所有 UI 面板中对重命名类的 import 和引用
- [x] 5.2 更新 `main.py` 和 `main_window.py` 中的引用

## 6. 验证

- [x] 6.1 全文搜索所有旧类名确认无遗漏引用
- [x] 6.2 运行 `python -c "from modules.ocr import OCRWorker"` 等验证 import 链
- [x] 6.3 启动主程序验证运行正常
