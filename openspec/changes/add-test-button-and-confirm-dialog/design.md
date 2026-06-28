## Context

当前 GroupListItem 只有编辑和删除操作，缺少快速验证手段。删除操作直接 emit 信号，无二次确认。5 个 Panel 代码中有 4 个模块的单次检测能力已经就绪或只需简单封装。

## Goals / Non-Goals

**Goals:**
- GroupListItem 新增测试按钮和删除确认弹窗
- 为 Image/Color/Timed/Number 模块提供 test_once 方法
- 所有 Panel 通过信号路由测试请求，MainWindow 统一调度并显示结果

**Non-Goals:**
- OC R 和 Background 模块的测试能力 — 检测逻辑与循环状态耦合，后续单独处理
- test 结果的高级展示（进度条、实时预览） — 只做 QMessageBox 弹窗

## Decisions

### 1. ConfirmDialog 作为独立组件而非工具函数

风格 2：QDialog 子类，发射 accepted 信号。与项目组件化规范一致，调用方通过 `.accepted.connect()` 响应确认，而非阻塞式 `exec()`。

### 2. GroupListItem 内部拦截删除事件

删除按钮点击 → 弹出 ConfirmDialog → 确认后 emit delete_clicked。Panel 端的 `_delete_group` 完全不用改。GroupListItem 从 `self._data["name"]` 获取组名填入弹窗消息。

### 3. test 结果通过 QMessageBox 而非信号回传

测试是同步操作（虽然实际检测可能是异步的，但结果最终在主线程显示），MainWindow 在模块方法返回后直接弹窗。不需要设计复杂的 result 信号回路。

### 4. test_once 统一返回 dict

```python
def test_group(self, index) -> dict:
    return {"matched": bool, "detail": str}
```

- Image: `{"matched": True/False, "detail": "匹配成功 置信度 87%" / "未匹配到模板"}`
- Color: `{"matched": True/False, "detail": "检测到颜色 #FF0000" / "未检测到目标颜色"}`
- Timed: `{"matched": True, "detail": "已执行按键: F5"}`
- Number: `{"matched": True/False, "detail": "当前数值: 1520" / "识别失败"}`

### 5. GroupListItem 布局

```
Row1: [icon] [name_label]                              [stretch] [🔍测试] [toggle]
Row2: [params_label] [region_label] [template_label]   [stretch] [编辑]   [删除]
```

### 6. 信号链

```
GroupListItem.test_requested(int)
  → Panel._test_group(int)
  → Panel.test_group_requested.emit(int)
  → MainWindow._on_test_group(panel_id, int)
  → module.test_group(int) → dict
  → QMessageBox(detail)
```

Panel 不直接持有模块引用，全部通过 MainWindow 路由。

## Risks / Trade-offs

- [异步] 截图和 OCR 可能耗时，同步弹窗会阻塞 UI → 测试场景单次执行约 200-500ms，可接受
- [OCR/Background 跳过] 这两个模块的用户暂时无法使用测试功能 → 后续补充，GroupListItem 中的测试按钮对所有类型都显示，但跳过类型不做特殊处理（信号发射后 MainWindow 检测到无对应模块时提示"暂不支持"）
