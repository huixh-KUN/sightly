## Why

监控组列表缺少快速验证手段和技术确认弹窗，用户无法在不启动全部监控的情况下单独测试某组配置是否有效，删除操作缺少二次确认容易误删。

## What Changes

- **GroupListItem 重构**：新增「测试」按钮，调整布局
- **ConfirmDialog 组件**：新建 `ui/components/confirm_dialog.py`，取代所有 Panel 中的 `QMessageBox.question` 风格删除确认
- **test_once 方法**：为 Image、Color、Timed、Number 模块新增单次检测方法，OCR 和 Background 暂跳过
- **信号路由**：Panel 新增 `test_group_requested` 信号，MainWindow 连接到对应模块

## Capabilities

### New Capabilities
- `group-test`: 监控组单次检测功能，提供即时验证途径
- `confirm-dialog`: 可复用的确认弹窗组件

### Modified Capabilities
<!-- 无现有 spec 变更 -->

## Impact

- `ui/components/confirm_dialog.py`: 新增文件
- `ui/widgets.py`: GroupListItem 新增 test 按钮 + 信号，delete 触发前拦截弹窗
- `ui/background_panel.py`: 新增 test_group_requested 信号
- `ui/ocr_panel.py`: 新增 test_group_requested 信号（占位）
- `ui/image_panel.py`: 新增 test_group_requested 信号
- `ui/number_panel.py`: 新增 test_group_requested 信号
- `ui/timed_panel.py`: 新增 test_group_requested 信号
- `ui/main_window.py`: 连接 test 信号到对应模块
- `modules/image.py`: 新增 `test_group(index)` 方法
- `modules/color.py`: 新增 `test_once()` 方法
- `modules/timed.py`: 新增 `execute_once(index)` 方法
- `modules/number.py`: 新增 `test_group(index)` 方法
