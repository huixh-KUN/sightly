## 1. 核心类定义重命名

- [x] 1.1 `input/base.py` — `BaseInputManager` → `BaseInputController`，更新所有引用
- [x] 1.2 `input/controller.py` — `InputManager` → `InputController`，更新所有引用

## 2. 实现类引用更新

- [x] 2.1 `input/dd_input.py` — import `BaseInputManager` → `BaseInputController`
- [x] 2.2 `input/pyautogui_input.py` — import `BaseInputManager` → `BaseInputController`
- [x] 2.3 `input/win32_input.py` — import `BaseInputManager` → `BaseInputController`

## 3. 对外导出和引用更新

- [x] 3.1 `input/__init__.py` — 更新 exports
- [x] 3.2 `core/context.py` — 更新 import 和类型标注
- [x] 3.3 `ui/main_window.py` — 更新 import 和引用

## 4. 验证

- [x] 4.1 全文搜索 `InputManager` / `BaseInputManager` 确认无遗漏引用
- [x] 4.2 运行 `python -c "from input.controller import InputController"` 验证 import 链
- [ ] 4.3 启动主程序验证运行正常
