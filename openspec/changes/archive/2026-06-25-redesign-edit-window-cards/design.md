## Context

当前 `GroupEditWindow` 使用单列 `QGridLayout` 平铺所有配置项，520px 宽度下水平滚动被 `ScrollBarAlwaysOff` 禁用，导致多控件行溢出被裁剪。控件间无视觉分组，用户难以快速定位所需设置项。

`*GroupWidget` 仅被 `GroupEditWindow` 使用，不参与面板列表渲染，重构范围可控。

## Goals / Non-Goals

**Goals:**
- 引入 `ConfigCard` 卡片容器，按功能对配置项进行视觉分组
- 调整窗口默认尺寸和滚动策略，确保内容完整可见
- 移除编辑窗口中的删除按钮

**Non-Goals:**
- 不修改 `*Panel` 类（列表视图不受影响）
- 不修改已有的配置字段和行为逻辑
- 不发生主题/样式体系的改动

## Decisions

### ConfigCard 组件

`ConfigCard` 是一个 `QFrame` 子类，提供：

```
┌─ ConfigCard ─────────────────────────┐
│ [emoji] 标题                          │  ← QHBoxLayout header
│──────────────────────────────────────│  ← 分隔线
│ <content>                            │  ← QVBoxLayout body
└──────────────────────────────────────┘
```

- 通过 `set_content(widget)` 注入内容
- 固定样式：深色背景 `#1E1E1E`、1px 边框 `#3C4043`、圆角 12px
- 标题行左侧 emoji + 文字，右侧可选附加控件

### 各类型卡片划分

| 类型 | 卡 1 | 卡 2 | 卡 3 | 卡 4 |
|------|------|------|------|------|
| OCR | 📍区域 | ⚙️触发 | 🔔报警 | 🎯匹配 |
| Image | 📍区域 | 🖼️模板 | ⚙️触发 | 🔔报警 |
| Timed | ⚙️触发 | 📍位置 | 🔔报警 | — |
| Number | 📍区域 | ⚙️触发 | 🔔报警 | — |
| Background | 📍区域 | 🎯检测 | ⚙️触发 | 🔔报警 |

### 窗口调整

- 默认尺寸：`resize(680, 600)`，最小 640×500
- 水平滚动策略：`ScrollBarAsNeeded`
- 删除按钮：从 `GroupEditWindow` 头部移除

## Risks / Trade-offs

- [低风险] 卡片间距增加所需垂直空间——窗口高度从 500px 加至 600px 已预留缓冲
- [低风险] `BackgroundGroupWidget` 的第三行（触发按键 + KeyCaptureWidget + 点击模式 + 偏移 + 报警）控件过多——拆到触发卡片内部两行
