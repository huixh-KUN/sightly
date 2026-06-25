## 1. 核心修改

- [x] 1.1 将 `ui/main_window.py` 第 38 行的 `self.setStyleSheet(ThemeManager.qss())` 替换为 `QApplication.instance().setStyleSheet(ThemeManager.qss())`

## 2. 验证

- [x] 2.1 确认 `GroupEditWindow` 弹出时背景为 `#121212` 而非白色
- [x] 2.2 确认 `MainWindow` 主题不受影响
- [x] 2.3 确认 `ThemeManager.switch_to("light")` 仍能正常切换主题
