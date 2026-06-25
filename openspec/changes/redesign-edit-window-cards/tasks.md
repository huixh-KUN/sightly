## 1. ConfigCard 组件

- [x] 1.1 创建 `ui/components/config_card.py`，实现 `ConfigCard(QFrame)` 含标题 emoji + 文字 + 分隔线 + `set_content()` 方法
- [x] 1.2 在 `ui/components/__init__.py` 导出 `ConfigCard`

## 2. GroupEditWindow 调整

- [x] 2.1 默认窗口尺寸改为 `resize(680, 600)`，最小 640×500
- [x] 2.2 水平滚动策略从 `ScrollBarAlwaysOff` 改为 `ScrollBarAsNeeded`
- [x] 2.3 移除头部删除按钮（`DangerButton`）

## 3. OCRGroupWidget 卡片重构

- [x] 3.1 将网格布局拆为 📍区域、⚙️触发、🔔报警、🎯匹配条件 四张 `ConfigCard`
- [ ] 3.2 验证所有配置项功能正常

## 4. ImageGroupWidget 卡片重构

- [x] 4.1 将网格布局拆为 📍区域、🖼️模板、⚙️触发、🔔报警 四张 `ConfigCard`
- [ ] 4.2 验证所有配置项功能正常

## 5. TimedGroupWidget 卡片重构

- [x] 5.1 将网格布局拆为 ⚙️触发、📍位置、🔔报警 三张 `ConfigCard`
- [ ] 5.2 验证所有配置项功能正常

## 6. NumberGroupWidget 卡片重构

- [x] 6.1 将网格布局拆为 📍区域、⚙️触发、🔔报警 三张 `ConfigCard`
- [ ] 6.2 验证所有配置项功能正常

## 7. BackgroundGroupWidget 卡片重构

- [x] 7.1 将网格布局拆为 📍区域、🎯检测、⚙️触发、🔔报警 四张 `ConfigCard`
- [x] 7.2 🎯检测卡片内容按子类型动态显示
- [x] 7.3 ⚙️触发卡片的密集行拆为两行
- [ ] 7.4 验证所有配置项功能正常

## 8. 验证

- [ ] 8.1 确认所有 5 种编辑窗口内容完整可见、无溢出裁剪
- [x] 8.2 确认导入正常：`python -c "from ui.components import ConfigCard"`
