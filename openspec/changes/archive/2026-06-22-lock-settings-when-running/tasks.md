## 1. 核心锁定/解锁逻辑

- [x] 1.1 `ui/home_panel.py` 新增 `set_toggles_enabled(enabled)` 方法，遍历 `self._cards` 调用 `card._toggle.setEnabled(enabled)`
- [x] 1.2 `ui/main_window.py` 的 `_on_start_all` 末尾：遍历 `self.panels` 调用 `panel.set_enabled(False)`（需要锁定面板） + 调用 `home.set_toggles_enabled(False)`
- [x] 1.3 `ui/main_window.py` 的 `_on_stop_all` 末尾：遍历相同面板调用 `set_enabled(True)` + `home.set_toggles_enabled(True)`

## 2. 各面板添加 set_enabled 方法

- [x] 2.1 `ui/ocr_panel.py` 新增 `set_enabled(disabled)`：调用 `super().setEnabled(disabled)` 禁用整个面板
- [x] 2.2 `ui/background_panel.py` 新增 `set_enabled(disabled)`：同上
- [x] 2.3 `ui/image_panel.py` 新增 `set_enabled(disabled)`：同上
- [x] 2.4 `ui/timed_panel.py` 新增 `set_enabled(disabled)`：同上
- [x] 2.5 `ui/number_panel.py` 新增 `set_enabled(disabled)`：同上（如存在）
- [x] 2.6 `ui/settings_panel.py` 新增 `set_enabled(disabled)`：同上

## 3. 验证

- [x] 3.1 启动后检查首页开关不可点击
- [x] 3.2 启动后切到各监控面板检查新增按钮和编辑控件是否禁用
- [x] 3.3 启动后切到设置页检查快捷键「修改」按钮是否禁用
- [x] 3.4 停止后检查所有控件是否恢复可编辑
