## Why

`GroupEditWindow` 的布局是平铺网格，520px 宽度下多控件行溢出被裁剪（水平滚动条被禁用），且缺乏视觉分组——所有配置项平铺在一起，用户难以快速定位。

## What Changes

- 新增 `ConfigCard` 可复用卡片容器组件，用于视觉分组
- 重新设计 5 个 `*GroupWidget`（OCR/Image/Timed/Number/Background）的布局，按功能划分为卡片
- `GroupEditWindow` 默认宽度从 520px 加宽至 680px
- 移除 `GroupEditWindow` 头部删除按钮（外部已提供删除入口）
- 移除 `setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)`，改为 `ScrollBarAsNeeded`

### 卡片划分

| 类型 | 卡片 |
|------|------|
| OCR | 📍区域 + ⚙️触发 + 🔔报警 + 🎯匹配条件 |
| Image | 📍区域 + 🖼️模板 + ⚙️触发 + 🔔报警 |
| Timed | ⚙️触发 + 📍位置 + 🔔报警 |
| Number | 📍区域 + ⚙️触发 + 🔔报警 |
| Background | 📍区域 + 🎯检测 + ⚙️触发 + 🔔报警 |

## Capabilities

### New Capabilities

- `config-card`: 可复用的卡片容器组件，带标题图标和一致的深色样式
- `edit-window-layout`: GroupEditWindow 宽度、滚动策略、删除按钮的调整

### Modified Capabilities

无

## Impact

- `ui/widgets.py`: 修改 `GroupEditWindow` 窗口尺寸和滚动策略
- `ui/ocr_panel.py`: 重构 `OCRGroupWidget` 布局
- `ui/image_panel.py`: 重构 `ImageGroupWidget` 布局
- `ui/timed_panel.py`: 重构 `TimedGroupWidget` 布局
- `ui/number_panel.py`: 重构 `NumberGroupWidget` 布局
- `ui/background_panel.py`: 重构 `BackgroundGroupWidget` 布局
- `ui/components/__init__.py`: 导出 `ConfigCard`
