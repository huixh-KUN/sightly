## Context

当前每个监控组（image/ocr/timed/number/background/script）由 `GroupCard` 包裹，内部是大量 QGridLayout 配置控件。卡片 padding 20px、spacing 16px，导致一张面板最多放 3~4 组。用户需要双击编辑名称，但更重要的是让主面板**紧凑化**，把配置编辑放到独立窗口。

## Goals / Non-Goals

**Goals:**
- 主面板组列表紧凑显示：一行展示图标 + 组名 + 关键参数 + 启停状态 + 实时运行数据
- 双击组打开独立非模态编辑窗口，包含全部配置控件
- 编辑窗口截图/选区时，自动隐藏主窗口和编辑窗口
- 配置结构与现有格式兼容

**Non-Goals:**
- 不改后端模块逻辑（`collect_config`、`set_config` 接口保持兼容）
- 不涉及工作空间切换、导入导出等面板无关功能

## Decisions

### 1. 架构总览

```
┌──────────────────────────────────────────┐
│  MainWindow                               │
│  ┌──────────────────────────────────────┐ │
│  │  ImagePanel (列表视图)               │ │
│  │  ┌────────────────────────────    ┐  │ │
│  │  │ 🖼️ 检测组 1  | 阈值:80% 模板:a │ │ │  ← GroupListItem
│  │  │ [启用] 区域:(x,y)→(x,y) ✅92%  │ │ │
│  │  ├────────────────────────────    ┤  │ │
│  │  │ ...                            │ │ │
│  │  └────────────────────────────────┘  │ │
│  │  [+ 添加组]                           │ │
│  └──────────────────────────────────────┘ │
│                                           │
│  ┌──────────────────────────────────────┐ │
│  │  GroupEditWindow (独立, 非模态)      │ │
│  │  ┌─────────────────────────    ┐    │ │
│  │  │  名称: [检测组 1       ]   │    │ │
│  │  │  区域: [截图选取]  ...     │    │ │
│  │  │  模板: [预览] [选取]       │    │ │
│  │  │  ... 全部配置控件 ...      │    │ │
│  │  └─────────────────────────    ┘    │ │
│  └──────────────────────────────────────┘ │
└──────────────────────────────────────────┘
```

### 2. GroupListItem 组件

每行固定高度 ~36-40px，用 QFrame + QHBoxLayout：

```
┌─────────────────────────────────────────────────┐
│ 🖼️  检测组 1 │ 阈值:80% │ 模板:a.png │ [启用]  │  ← 36-40px
│               │ 区域:x-x  │ ✅ 92%    │         │
└─────────────────────────────────────────────────┘
```

- 左侧：类型图标 + 可编辑组名（Label，双击打开编辑窗口）
- 中间：关键参数（按类型不同：ocr 显示关键词、timed 显示间隔/按键、image 显示阈值/模板…）
- 右侧：Toggle 启停开关 + 实时状态文字（颜色/置信度/倒计时）
- 鼠标悬停：浅底色高亮

### 3. GroupEditWindow 组件

```python
class GroupEditWindow(QWidget):
    config_changed = Signal()  # 配置变更时发射

    def __init__(self, app, group_config, group_index, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)
        self.setWindowTitle(f"编辑组 {group_index + 1}")

        # 非模态，不阻塞主窗口
        # 关闭时自动发射 config_changed 通知 main panel 刷新
```

关键设计要点：
- **非模态**：`setWindowModality(Qt.NonModal)`，不阻塞主窗口
- **窗口置顶**可选：`Qt.WindowStaysOnTopHint`，或交给用户自由拖放
- **截图遮罩协调**：编辑窗口点击"选区"时，发射信号让 MainWindow 关闭窗口并截图；截图完成后自动恢复
- **实时保存**：控件值变更即发射 `config_changed`，主面板列表行即时同步文本更新

### 4. 截图/选区协调

当前 `ScreenCaptureOverlay` 和 `RegionOverlay` 在全屏展示时没有任何窗口遮挡。

编辑窗口点"选区"或"截图"时：
1. 编辑窗口发射 `capture_requested` 信号
2. MainWindow 收到后调用 `self.hide()` + `edit_window.hide()`
3. 启动覆盖层
4. 覆盖层完成后恢复到 show

```python
# MainWindow
def _on_capture_requested(self):
    self.hide()
    self._current_edit_window.hide()
    QApplication.processEvents()
    self._overlay.show()
    # 覆盖层完成信号中: self.show(); self._current_edit_window.show()
```

### 5. 列表项数据结构

每一行对应一个 group dict（与现有配置格式一致）：

```python
{
    "name": "检测组 1",
    "enabled": True,
    "type": "image",
    "region": [0, 0, 800, 600],
    "threshold": 80,
    "reference_image": "path/to/template.png",
    "interval": 3,
    "pause": 180,
    "click_enabled": True,
    "click_offset": 5,
    "key": "F5",
    ...
}
```

`collect_config()` 遍历所有 GroupListItem 返回 list[dict]，格式与现在一致，**向后兼容**。

### 6. 运行时只读模式

- 列表中的 Toggle 开关保持可用（用户期望运行时仍可启停单组）
- 列表文本只读（双击不打开编辑窗口，或打开后控件全 disabled）
- 编辑窗口内控件全部 `setEnabled(False)`，但保留查看能力

## Risks / Trade-offs

- [中] 大重构涉及 6 个面板，需保证每个面板的 collect_config / set_config 接口返回格式不变
- [低] 编辑窗口数量限制：防止用户无限打开，限制同时只能打开 1 个（打开第 2 个时替换）
- [低] 截图协调：hide/show 时序需处理好，防止闪屏或截到空白
- [低] 实时状态推送需要模块→AppState→Panel 的信号链，目前 `module_state_changed` 信号已存在，可复用
