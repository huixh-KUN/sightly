## 1. AppState 核心改造

- [x] 1.1 `core/state.py` — 新增 `_is_running` / `_is_paused` 字段 + property 方法
- [x] 1.2 `core/state.py` — 新增 `running_state_changed` / `paused_state_changed` 信号
- [x] 1.3 `core/state.py` — 新增 `set_running()` / `set_paused()` 方法（设值+发信号）
- [x] 1.4 `core/state.py` — 删除未使用的 `start_requested` / `stop_requested` 信号

## 2. MainWindow 迁移

- [x] 2.1 `ui/main_window.py` — 删除 `_is_running` 字段 + property，改用 `self.app_state.is_running`
- [x] 2.2 `ui/main_window.py` — 删除 `_is_paused` 字段 + property（从未使用）
- [x] 2.3 `ui/main_window.py` — `_on_start_all/_on_stop_all` 中通过 `self.app_state.set_running()` 设状态
- [x] 2.4 `ui/main_window.py` — 所有 `self._is_running` 引用改为 `self.app_state.is_running`

## 3. 删除幽灵变量 system_stopped

- [x] 3.1 `modules/script.py` — 删除 `getattr(self.app, 'system_stopped', False)` 检查（2处）
- [x] 3.2 `modules/ocr.py` — 删除 `getattr(self.app, 'system_stopped', False)` 检查（2处）
- [x] 3.3 `modules/image.py` — 删除 `getattr(self.app, 'system_stopped', False)` 检查（1处）
- [x] 3.4 `core/click_handler.py` — 删除 `getattr(self.app, 'system_stopped', False)` 检查（1处）

## 4. 统一模块状态检查路径

- [x] 4.1 `modules/ocr.py` — `self.app.is_running` → `self.app.app_state.is_running`
- [x] 4.2 `modules/image.py` — `self.app.is_running` → `self.app.app_state.is_running`
- [x] 4.3 `modules/background.py` — `self.app.is_running` → `self.app.app_state.is_running`
- [x] 4.4 `modules/script.py` — `self.app.is_running` → `self.app.app_state.is_running`
- [x] 4.5 `core/click_handler.py` — `self.app.is_running` → `self.app.app_state.is_running`

## 5. 修复直接访问私有属性

- [x] 5.1 `input/keyboard.py` — `app._is_running` → `app.app_state.is_running`
- [x] 5.2 `ui/main_window.py` — `self.app_state._wm.list_workspaces()` → `self.app_state.workspace_list`
- [x] 5.3 `ui/main_window.py` — `self.app_state._wm.save(...)` → 改用公开方法保存配置
- [x] 5.4 `ui/main_window.py` — 日志中 `self.app_state._module_states` → `self.app_state.enabled_modules()`

## 6. 验证

- [x] 6.1 全文搜索 `app.is_running`（非 `.app_state`）确认无遗漏
- [x] 6.2 全文搜索 `system_stopped` 确认已全部删除
- [x] 6.3 全文搜索 `_is_paused` 确认 MainWindow 中已删除
- [x] 6.4 全文搜索 `\._wm\.` 和 `\._module_states` 确认已修复
- [x] 6.5 运行 main.py 验证启动/停止/工作空间切换功能正常
