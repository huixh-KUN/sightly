## 1. ConfirmDialog 组件

- [x] 1.1 新建 `ui/components/confirm_dialog.py`，ConfirmDialog(QDialog) 带 accepted 信号、自定义标题/消息/按钮文字
- [x] 1.2 在 `ui/components/__init__.py` 中导出 ConfirmDialog

## 2. GroupListItem 重构

- [x] 2.1 GroupListItem 新增 `test_requested = Signal(int)` 信号
- [x] 2.2 GroupListItem 新增「🔍测试」按钮，布局调整为 Row1 右侧（测试+开关）、Row2 右侧（编辑+删除）
- [x] 2.3 GroupListItem 删除按钮改为先弹出 ConfirmDialog，确认后 emit delete_clicked

## 3. 模块 test_group / run_once 方法

- [x] 3.1 `ImageDetectionManager.test_group` 改为 detect + `execute_commands(for_test=True)` 单路径
- [x] 3.2 `TimedModule.test_group` 抽取 `_execute_group_actions`，`matched=None`
- [x] 3.3 `NumberModule.test_group` 补充阈值预判 detail，不触发动作
- [x] 3.4 `OCRModule` 拆 `recognize_group_once` + `execute_group_actions`，新增 `test_group`
- [x] 3.5 `BackgroundManager` 拆 `recognize_once` + `trigger_actions`，新增 `run_once`

## 4. Panel 信号 + MainWindow 路由

- [x] 4.1 各 Panel 新增 `test_group_requested = Signal(int)` 信号
- [x] 4.2 各 Panel 的 `_add_list_item` 连接 `item.test_requested → self._test_group`
- [x] 4.3 各 Panel 新增 `_test_group(idx)` 方法，发射 `test_group_requested.emit(idx)`
- [x] 4.4 `main_window.py` 的 `_init_signals` 连接各 Panel 的 test_group_requested
- [x] 4.5 `main_window.py` `_on_test_group`：`_is_running` 守卫 + 表驱动路由五模块 + 分类型结果文案

## 5. 验证

- [ ] 5.1 运行中点测试 → 弹窗「请先停止运行」
- [ ] 5.2 Image：测试点击与循环走同一 `execute_commands`
- [ ] 5.3 Timed：弹窗显示「执行完成」或「未配置动作」
- [ ] 5.4 Number：显示数值 + 阈值预判，无 alarm/key 触发
- [ ] 5.5 OCR：关键词匹配可触发动作；imagehash 不影响测试
- [ ] 5.6 Background：三子类型各测；无目标窗口错误明确
- [ ] 5.7 `python -c "from ui.main_window import MainWindow"` 导入通过
