## Context

ThemeManager 已内建 `_DarkColors` / `_LightColors` 两套完整 QSS 和 `switch_to()` 方法，但入口为零。当前 `ui/main_window.py:38` 在 `__init__` 中调用 `ThemeManager.qss()` 仅应用暗色主题。用户需手动修改代码才能切换。

## Goals / Non-Goals

**Goals:**
- 在顶部标题栏右侧添加一个主题切换 Toggle（"🌙/☀️"）
- 切换即时全局刷新 QSS
- 偏好持久化到 config.json，启动时自动恢复
- Toggle 自身引用自绘控件不受 QSS 颜色覆盖

**Non-Goals:**
- 不支持自定义主题（仅 dark/light）
- 不涉及每个模块面板的独立主题覆写

## Decisions

1. **Toggle 放在标题栏而非设置页** — 主题是视觉偏好，切换应即时可见、触手可及。放设置页需要跳转才能看到效果，体验差。
2. **复用现有 Toggle 组件** — `ui/components/toggle.py` 已经提供自绘开关，且自带文字副标签。文本内容为"深色/浅色"足够示意，无需添加额外 emoji。
3. **使用 ConfigManager 持久化** — 主题偏好作为 `theme` 字段写入 config.json，在 `MainWindow._on_config_loaded` 中读取并调用 `ThemeManager.switch_to()`。
4. **Toggle 互锁** — 切换后 Toggle 自身需要通过 `setStyleSheet` 明确前景色，避免被全局 QSS 覆盖不可见。

## Risks / Trade-offs

- [QSS 刷新闪烁] → 切换瞬间 widget 重绘，QSS 长度约 230 行，实测无感
- [Toggle 在亮色主题下不可见] → Toggle 前景色固定为 `#E8EAED` 和 `#212121` 在各自主题下均可见，无需额外处理
