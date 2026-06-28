## Why

上一次命名重构（2026-06-27）将 `InputController` → `InputManager`，但 `项目命名规范.md:600-603` 明确将 `InputController` 列为 `*Controller` 的正确示例，其职责描述"控制多种输入实现（DD/PyAutoGUI/Win32等）"与当前 `InputManager` 完全一致。当前命名与规范相悖，需修正。

## What Changes

- `input/controller.py`: `InputManager` → `InputController`
- `input/base.py`: `BaseInputManager` → `BaseInputController`
- 同步更新所有 import 和引用（~10 处）
- 纯重命名变更，无行为逻辑修改
- **BREAKING**: 所有引用旧类名的外部代码需同步更新

## Capabilities

### New Capabilities
- *（无新能力）*

### Modified Capabilities
- `naming-conventions`: 无 spec 级行为变更（本次仅代码对齐已存在的规范）

## Impact

- **input/**：`InputManager` → `InputController`，`BaseInputManager` → `BaseInputController`，波及 ~10 处引用
- **core/context.py**：1 处 import + 1 处类型标注
- **ui/main_window.py**：1 处 import + 2 处引用
- **input/base.py**、**input/controller.py**、**input/__init__.py**：类定义 + __init__ exports
- **input/dd_input.py**、**input/pyautogui_input.py**、**input/win32_input.py**：import BaseInputController
