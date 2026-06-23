## Why

当前面板中每个监控组占据一整张大卡片，空间利用率低；标题用 QLineEdit 伪装，交互粗糙，无保存反馈。需要重构为：

1. **主面板 → 紧凑缩略列表**：一行展示类型、关键参数、实时状态，一张面板能容纳更多组
2. **双击组 → 独立编辑窗口**：不阻塞主窗口，不遮挡截图选区，提供完整的配置编辑能力

## What Changes

- 6 个面板（image/ocr/timed/number/background/script）的组卡片**缩略为 1~2 行列表项**，展示类型图标、组名、关键参数、实时状态
- 双击列表项打开**独立非模态编辑窗口**，包含该组全部配置控件
- 编辑窗口打开后不影响主窗口操作；选区/截图时主窗口和编辑窗口均自动隐藏
- 移除旧的卡片式 `GroupCard` + 网格布局，替换为紧凑列表结构

## Capabilities

### New Capabilities
- `group-list-view`: 监控组缩略列表视图，紧凑展示关键信息 + 实时状态
- `group-edit-window`: 独立编辑窗口，非模态，支持全部配置编辑

### Modified Capabilities

（无）

## Impact

- `ui/*_panel.py` × 6 — 大面积重构：组卡片布局 → 列表项布局
- `ui/widgets.py` — 新增 `GroupListItem` 列表项组件、`GroupEditWindow` 编辑窗口基类
- `ui/main_window.py` — 涉及 `set_panel_view_only`、`_lock_panels` 适配
- `core/state.py` — 可能需要新增信号：`edit_window_opened/closed` 协调隐藏/恢复
- 移除或废弃当前 `GroupCard` 等卡片相关组件
