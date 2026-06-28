## 方案

将现有 `interval` + `pause` 两个参数替换为更简洁的模型。

### 旧 UI → 新 UI

```
        旧 UI                         新 UI
┌─────────────────────┐    ┌───────────────────────────┐
│ 间隔   暂停          │    │ 🎯 检测                   │
│ [3秒] [180秒]       │    │ 关键词 [____________]      │
│                      │    │ 语言 [简体中文]            │
│ 用户总在纠结          │    │                           │
│ 哪个管什么           │    │ 循环检测 [开] 每 [0.0秒]   │
│                      │    │         ↑开关     ↑仅开时显示│
│                      │    │ [⚙️ 高级]                  │
└─────────────────────┘    └───────────────────────────┘
```

### 核心变化

| 旧 | 新 |
|----|----|
| `interval` 整秒 | `interval` 浮点(步长0.1), 0=兜底250-300ms |
| `pause` 独立参数 | 去掉。interval 已控制下次检测时间 |
| — | 新增 `cycle_enabled` 开关 |

### 循环检测控件

新增 `CycleControlWidget` 通用组件，包含：

```
┌──────────────────────────────────────┐
│ 循环检测 [开/关]  每 [0.0秒]  [⚙️]  │
└──────────────────────────────────────┘
         ↑ SwitchButton   ↑ QDoubleSpinBox(仅开时可见)
         cycle_enabled      interval
```

**行为：**
- 切换开关 → interval spinbox 显示/隐藏
- 组件提供 `is_cycle_enabled()` / `set_cycle_enabled()` / `interval_value()` / `set_interval_value()` 接口

**各面板检测卡使用此控件替换原有 interval/pause 行。**

| 面板 | 检测卡原有内容 | 新增控件位置 |
|------|---------------|------------|
| OCR | 关键词 + 语言 | 语言行下方 |
| Image | 模板 + 阈值 | 阈值行下方 |
| Background OCR | 关键词 + 语言 | 语言行下方 |
| Background Image | 模板 + 阈值 | 阈值行下方 |
| Background Color | 颜色 + 容差 | 容差行下方 |
| Number | 阈值 + 置信度 | 置信度行下方 |
| Timed | 间隔 | 间隔行下方（仅开关，无间隔输入联动） |

**Timed 模块特殊：** 只有"循环执行"开关，间隔始终显示。

### 行为

| 循环检测 | 间隔显示 | 行为 |
|---------|---------|------|
| 开 | 显示 | 持续扫描，每次间隔 interval 秒 |
| 关 | 隐藏 | 扫描一次，执行后组停用 |

### 数据字段

| 字段 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `interval` | float | 0 | 0=兜底250-300ms |
| `cycle_enabled` | bool | true | 新增 |
| `pause` | int | — | 保留不用，兼容旧配置 |

### 改动范围

| 文件 | 改动 |
|------|------|
| `ui/components/cycle_control.py` | **新增** CycleControlWidget |
| `ui/components/__init__.py` | 导出 CycleControlWidget |
| `ui/ocr_panel.py` | 匹配卡→检测卡, 使用 CycleControlWidget |
| `ui/image_panel.py` | 同上 |
| `ui/background_panel.py` | 同上（覆盖3种类型） |
| `ui/number_panel.py` | 同上（新增interval+cycle字段） |
| `ui/timed_panel.py` | 间隔行下方加循环执行开关 |
| `modules/number.py` | 循环读interval/cycle_enabled, 替代hardcoded sleep(1) |
| `modules/timed.py` | 循环判断cycle_enabled |
