## 1. GroupListItem 列表项组件

- [ ] 1.1 在 `ui/widgets.py` 创建 `GroupListItem`（QFrame, 固定高 36-40px, QHBoxLayout）
- [ ] 1.2 实现：类型图标 + 组名 + 关键参数摘要 + Toggle 开关 + 实时状态文字
- [ ] 1.3 关键参数按类型动态显示（image→阈值/模板, ocr→关键词, timed→间隔/按键, number→阈值, color→颜色/容差, background→类型/关键词）
- [ ] 1.4 双击信号 `double_clicked(index)` 发射
- [ ] 1.5 运行时模式：Toggle 保持可用，双击不打开编辑窗口

## 2. GroupEditWindow 编辑窗口

- [ ] 2.1 在 `ui/widgets.py` 创建 `GroupEditWindow`（QWidget, Qt.Window 标志, 非模态）
- [ ] 2.2 实现单窗口限制：全局只允许同时打开一个编辑窗口
- [ ] 2.3 将当前各 panel 中 GroupWidget（如 ImageGroupWidget）的配置控件移入编辑窗口
- [ ] 2.4 截图/选区协调：点击按钮时隐藏 主窗口+编辑窗口，完成后恢复
- [ ] 2.5 运行时只读：编辑窗口内全部控件 setEnabled(False)
- [ ] 2.6 配置即改即同步：控件变更发射 config_changed 信号

## 3. 面板重构：列表视图

- [ ] 3.1 image_panel.py — `_setup_ui` 改为列表布局，组卡片替换为 GroupListItem
- [ ] 3.2 ocr_panel.py — 同上
- [ ] 3.3 timed_panel.py — 同上
- [ ] 3.4 number_panel.py — 同上
- [ ] 3.5 background_panel.py — 同上
- [ ] 3.6 各 panel 的 `add_group()` 创建 GroupListItem 而非 GroupCard
- [ ] 3.7 各 panel 的 `collect_config()` 遍历 GroupListItem 收集配置（格式不变）
- [ ] 3.8 各 panel 的 `set_config()` 更新列表项状态
- [ ] 3.9 移除废弃的 GroupCard 及旧布局代码

## 4. 主窗口适配

- [ ] 4.1 `set_panel_view_only` 适配新的列表结构
- [ ] 4.2 `_lock_panels` / `_on_start_all` 处理编辑窗口关闭
- [ ] 4.3 截图协调信号链：编辑窗口 → MainWindow → hide/show

## 5. 验证

- [ ] 5.1 启动验证 6 个面板显示为紧凑列表
- [ ] 5.2 验证双击打开编辑窗口，窗口不阻塞主窗口
- [ ] 5.3 验证编辑窗口选区/截图时自动隐藏并恢复
- [ ] 5.4 验证配置修改即改即同步到列表项
- [ ] 5.5 验证运行时只读模式
- [ ] 5.6 验证 collect_config 输出格式与之前一致（向后兼容）
