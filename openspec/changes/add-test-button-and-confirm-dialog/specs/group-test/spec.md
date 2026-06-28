## ADDED Requirements

### Requirement: GroupListItem SHALL 提供测试按钮
GroupListItem SHALL 在列表项布局中新增「测试」按钮，点击后发射 test_requested 信号。

#### Scenario: 测试按钮点击
- **WHEN** 用户点击 GroupListItem 的测试按钮
- **THEN** GroupListItem 发射 test_requested(int index) 信号

### Requirement: 各 Panel SHALL 提供 test_group_requested 信号
ImagePanel、NumberPanel、TimedPanel SHALL 新增 test_group_requested 信号，连接 GroupListItem 的 test_requested。

#### Scenario: 测试请求路由
- **WHEN** GroupListItem 发射 test_requested
- **THEN** 对应 Panel 发射 test_group_requested(int index) 信号
- **THEN** MainWindow 连接到该信号并调用对应模块的 test 方法

### Requirement: 模块 SHALL 提供 test_once 方法
ImageDetectionManager、ColorRecognitionManager、TimedModule、NumberModule SHALL 新增单次检测/执行方法。

#### Scenario: Image 单次检测
- **WHEN** 调用 ImageDetectionManager.test_group(index)
- **THEN** 抓取该组配置的区域截图并进行模板匹配
- **THEN** 返回匹配结果和详情信息

#### Scenario: Color 单次检测
- **WHEN** 调用 ColorRecognitionManager.test_once()
- **THEN** 抓取屏幕截图并检测目标颜色
- **THEN** 返回匹配结果和详情信息

#### Scenario: Timed 单次执行
- **WHEN** 调用 TimedModule.execute_once(index)
- **THEN** 根据该组配置执行一次按键/点击操作
- **THEN** 返回执行结果详情

#### Scenario: Number 单次检测
- **WHEN** 调用 NumberModule.test_group(index)
- **THEN** 抓取该组区域截图并进行 OCR 数字识别
- **THEN** 返回识别结果和详情信息

### Requirement: MainWindow SHALL 路由测试请求并显示结果
MainWindow SHALL 连接各 Panel 的 test_group_requested 信号，调用模块方法后通过 QMessageBox 显示结果。

#### Scenario: 测试结果展示
- **WHEN** MainWindow 收到测试请求并完成检测
- **THEN** 系统以 QMessageBox 或日志形式显示测试结果详情
