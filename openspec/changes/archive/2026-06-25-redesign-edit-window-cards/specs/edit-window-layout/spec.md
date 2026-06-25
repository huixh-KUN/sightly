## ADDED Requirements

### Requirement: GroupEditWindow SHALL use card-based layout
系统 SHALL 将 `GroupEditWindow` 的布局从平铺网格改为 `ConfigCard` 卡片分组。

#### Scenario: OCR group shows 4 cards
- **WHEN** 双击 OCR 监控组
- **THEN** 弹出窗口中包含 📍区域、⚙️触发、🔔报警、🎯匹配条件 四张卡片

#### Scenario: Timed group shows 3 cards
- **WHEN** 双击定时监控组
- **THEN** 弹出窗口中包含 ⚙️触发、📍位置、🔔报警 三张卡片

#### Scenario: Number group shows 3 cards
- **WHEN** 双击数字识别监控组
- **THEN** 弹出窗口中包含 📍区域、⚙️触发、🔔报警 三张卡片

#### Scenario: Image group shows 4 cards
- **WHEN** 双击图像检测监控组
- **THEN** 弹出窗口中包含 📍区域、🖼️模板、⚙️触发、🔔报警 四张卡片

#### Scenario: Background group shows 4 cards
- **WHEN** 双击后台监控组
- **THEN** 弹出窗口中包含 📍区域、🎯检测、⚙️触发、🔔报警 四张卡片
- **THEN** 🎯检测卡片内容按子类型（ocr/image/color）动态显示

### Requirement: GroupEditWindow SHALL have adequate default size
系统 SHALL 将 `GroupEditWindow` 默认尺寸调整为 680×600，最小尺寸 640×500。

#### Scenario: Window opens at 680x600
- **WHEN** 双击监控组打开编辑窗口
- **THEN** 窗口初始尺寸为 680×600

### Requirement: GroupEditWindow SHALL enable horizontal scroll when needed
系统 SHALL 将水平滚动策略从 `ScrollBarAlwaysOff` 改为 `ScrollBarAsNeeded`。

#### Scenario: Horizontal scroll appears on overflow
- **WHEN** 窗口宽度小于内容所需宽度
- **THEN** 水平滚动条自动出现

### Requirement: Delete button SHALL be removed from GroupEditWindow
系统 SHALL 移除 `GroupEditWindow` 头部的删除按钮。

#### Scenario: No delete button in edit window
- **WHEN** 打开编辑窗口
- **THEN** 头部没有删除按钮
