## Context

上一次命名重构将 `InputController` → `InputManager`，认为它是"管理类"。但 `项目命名规范.md` 的 `*Controller` 章节明确将 `InputController` 列为正确示例，且其职责描述与控制器的语义完全匹配。

## Goals / Non-Goals

**Goals:**
- `InputManager` → `InputController`（input/controller.py）
- `BaseInputManager` → `BaseInputController`（input/base.py）
- 同步更新所有 import 和引用

**Non-Goals:**
- 不修改类的内部实现逻辑
- 不修改 API 行为
- 不修改 `项目命名规范.md`
- 不处理其他命名违规

## Decisions

| 决策 | 选择 | 理由 |
|------|------|------|
| `*Manager` → `*Controller` | `InputController` | 命名规范明确将其列为 `*Controller` 正确示例；职责是主动控制输入流程（工厂选择 + 优先级锁 + API 协调），非被动处理 |
| `BaseInputManager` → `BaseInputController` | `BaseInputController` | 与管理类一致 |

## Risks / Trade-offs

- **[风险] 上游依赖需同步** → 仅 5 个文件受影响（core/context.py、ui/main_window.py、input/__init__.py、input/*.py），逐一验证即可
