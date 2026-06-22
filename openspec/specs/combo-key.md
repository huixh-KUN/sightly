# 组合键支持

## 需求

当前按键监听/触发只支持单按键。需要扩展为支持组合键——最多三个按键同时按下。

- 只按一个键 = 单按键（与现有行为一致）
- 同时按两个键 = 双键组合
- 同时按三个键 = 三键组合

## 改动范围

### 1. `ui/components/key_capture.py` — KeyCaptureWidget
- 当前：只捕获单个按键
- 改为：支持多按键同时按下，按顺序记录最多 3 个键
- 显示格式：`Ctrl+F1`、`Alt+Shift+F1`
- 信号：`keyChanged(str)` 不变，但字符串包含组合键

### 2. `input/key_mapping.py` — 键名映射
- 当前：仅单键映射表
- 改为：确保修饰键（Ctrl、Alt、Shift、Win）有正确映射

### 3. 各模块的 `trigger_key` 属性
- 当前：每个模块的 `trigger_key` 只存单键字符串
- 改为：存储组合键字符串，解析时拆分
- 涉及模块：
  - OCR 模块
  - 图像检测模块
  - 定时任务模块
  - 后台监控模块
  - 脚本模块

### 4. `modules/script.py` — ScriptExecutor
- 脚本命令 `KeyDown "f1", 1` → 需支持组合键格式
- 执行时按顺序依次按下，释放时反向释放

### 5. 配置文件向后兼容
- 现有配置里 `trigger_key = "f1"` 仍有效
- 新格式 `trigger_key = "ctrl+f1"` 自动识别

### 6. 全局快捷键（启动/停止）
- 当前：`start_shortcut`、`stop_shortcut`、`record_hotkey` 均为单键
- 改为：支持组合键，格式与其他模块一致（如 `ctrl+f10`）
- 解析：监听器中识别修饰键状态，匹配组合字符串
- 涉及文件：`input/keyboard.py`、`core/state.py`

## 不涉及

- 不修改 `InputController` 的 `key_down` / `key_up` 接口（已支持单键）
- 不修改 `ScriptExecutor` 的循环执行逻辑

## 优先级

中。
