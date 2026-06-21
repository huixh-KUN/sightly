# 待办事项

---

## 需求 (Feature)

### F1. 管理员权限启动
- **描述**: 应用启动时自动请求管理员/提权（如需要管理员权限的操作）
- **实现方向**: main.py 入口处检测 `is_admin`，非管理员则通过 `shellrunas` 或 manifest 重新启动

### F2. 工作空间（Workspace）
- **描述**: 类似工作空间的概念，每个工作空间包含独立的配置集，启动时自动加载上次使用的工作空间
- **替代方案**: 若实现成本高，先确保配置完整自动保存/恢复作为兜底

  **F2 天然解决的遗留问题（无需单独修复）：**
  
  #### B1. 面板配置保存不完整（随工作空间自动修复）
  - 当前 `save_config()` / `load_saved_config()` 只保存了 `script` 和 `settings` 两个面板
  - OCR/Timed/Number/Image/Background 面板的 `collect_config()` 从未被调用
  - 工作空间需要收集**所有面板**配置一起持久化，自然覆盖
  - 涉及: `ui/main_window.py:421-433`, `ui/main_window.py:389-410`
  
  #### B2. 模板/截图路径无法持久化（随工作空间自动修复）
  - 通过截图获取的模板保存到 tempfile 临时目录，重启后文件被清理
  - 工作空间应有自己的资源目录（如 `workspaces/<name>/templates/`），截图模板存入该目录而非临时目录
  - 涉及: `ui/image_panel.py:244-250`

### F3. 日志增加 error 级别
- **描述**: `LoggingManager` 添加 `error()` 方法，配套单独的 `sightly_error.log`，用于记录运行时错误；GUI 上用红色高亮显示 error 日志
- **涉及文件**: `core/logging.py`

### F4. 日志文件名改为 sightly
- **描述**: 当前日志文件名为 `autodoor.log`、`autodoor_debug.log`，需改为 `sightly.log`、`sightly_debug.log`、`sightly_error.log`
- **涉及文件**: `ui/main_window.py:55`, `core/logging.py:38-40`
