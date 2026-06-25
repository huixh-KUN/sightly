## Why

当前仅支持深色主题，部分用户在明亮环境下需要浅色主题。ThemeManager 已内建暗色/亮色两套完整 QSS，只需一个 UI 切换入口即可启用。

## What Changes

- 在顶部标题栏右侧增加主题切换开关（Toggle 控件）
- 切换时通过 ThemeManager.switch_to() 即时全局生效
- 切换偏好持久化到 config.json，启动时自动加载
- 开关在不同主题下保持可见（不受自身 QSS 影响）

## Capabilities

### New Capabilities
- `theme-switch`: 用户可随时在深色/浅色主题之间切换，偏好自动保存

### Modified Capabilities

（无）

## Impact

- `ui/main_window.py`：标题栏增加 Toggle
- `ui/theme.py`：ThemeManager 增加 `toggle_instance` 绑定，切换后更新开关状态
- `core/config.py` 或 MainWindow 配置加载：新增 `theme` 字段持久化
