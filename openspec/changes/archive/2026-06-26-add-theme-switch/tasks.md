## 1. 主题开关 UI

- [x] 1.1 在 `ui/main_window.py` 的 `_create_header()` 中 status_label 右侧添加 Toggle 组件，标签文字根据当前主题显示"深色"/"浅色"
- [x] 1.2 Toggle 的 `stateChanged` 信号连接 ThemeManager.switch_to()，切换后更新 Toggle 标签文字

## 2. 持久化

- [x] 2.1 MainWindow 配置加载时读取 `theme` 字段，调用 ThemeManager.switch_to()
- [x] 2.2 主题切换时同步写入 config.json 的 `theme` 字段

## 3. 验证

- [x] 3.1 启动应用，点击主题开关，确认全局 QSS 即时切换无残留
- [x] 3.2 切换后重启应用，确认主题偏好正确恢复
