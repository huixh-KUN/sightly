# Naming Conventions

## Purpose
定义 Sightly 项目的代码命名规范约束。所有代码命名 SHALL 遵循 `项目命名规范.md` 的完整规则。

## Requirements

### Requirement: Class naming follows `项目命名规范.md`
系统 SHALL 遵循 `项目命名规范.md` 中定义的类命名后缀约定。

#### Scenario: 管理类使用 Manager 后缀
- **WHEN** 一个类负责协调、管理多个实例或资源
- **THEN** 其类名 SHALL 以 `Manager` 结尾

#### Scenario: 执行类使用 Worker 或 Task 后缀
- **WHEN** 一个类负责执行具体任务（如 OCR 识别、图像检测、按键触发）
- **THEN** 其类名 SHALL 以 `Worker` 或 `Task` 结尾

#### Scenario: 识别器使用 Recognizer 后缀
- **WHEN** 一个类提供无状态的识别服务
- **THEN** 其类名 SHALL 以 `Recognizer` 结尾

#### Scenario: 转换器使用 Converter 后缀
- **WHEN** 一个类提供坐标系或数据格式转换
- **THEN** 其类名 SHALL 以 `Converter` 结尾

#### Scenario: 控制器使用 Controller 后缀
- **WHEN** 一个类负责主动控制流程、协调交互（如选择输入实现、管理优先级锁）
- **THEN** 其类名 SHALL 以 `Controller` 结尾

#### Scenario: 状态类使用 State 后缀
- **WHEN** 一个类管理或表示状态
- **THEN** 其类名 SHALL 以 `State` 结尾

### Requirement: Method naming follows verb-prefix convention
系统 SHALL 使用方法命名必须使用规范定义的动词前缀。

#### Scenario: 获取数据使用 get_ 前缀
- **WHEN** 方法获取或计算数据
- **THEN** 方法名 SHALL 以 `get_` 开头

#### Scenario: 启动/停止使用 start_/stop_ 前缀
- **WHEN** 方法启动或停止任务
- **THEN** 方法名 SHALL 以 `start_` 或 `stop_` 开头

#### Scenario: 布尔判断使用 is_/has_/can_ 前缀
- **WHEN** 方法返回布尔值
- **THEN** 方法名 SHALL 以 `is_`、`has_` 或 `can_` 开头

#### Scenario: 私有方法使用单下划线前缀
- **WHEN** 方法为内部私有方法
- **THEN** 方法名 SHALL 以 `_` 开头

### Requirement: Variable names avoid abbreviations
变量命名 SHALL 避免缩写，优先使用完整单词。

#### Scenario: 实例变量使用全称
- **WHEN** 定义实例变量
- **THEN** 变量名 SHALL 使用完整单词而非缩写，如 `self.screenshot_manager` 而非 `self.sr_mgr`

#### Scenario: 集合变量使用复数
- **WHEN** 变量表示多个元素的集合
- **THEN** 变量名 SHALL 使用复数形式，如 `groups`、`items`、`configs`

### Requirement: Constants use ALL_CAPS
常量的命名 SHALL 使用全大写加下划线格式。

#### Scenario: 全局常量全大写
- **WHEN** 定义模块级常量
- **THEN** 常量名 SHALL 使用全大写，如 `PRIORITY_NUMBER`、`DEFAULT_INTERVAL`

#### Scenario: 类常量全大写
- **WHEN** 定义类级别的常量
- **THEN** 常量名 SHALL 使用全大写，如 `MAX_RETRIES`、`SUPPORTED_LANGUAGES`

### Requirement: File names use lowercase with underscores
源文件命名 SHALL 使用小写字母加下划线。

#### Scenario: 模块文件小写下划线
- **WHEN** 创建 Python 源文件
- **THEN** 文件名 SHALL 使用小写字母和下划线，如 `ocr.py`、`background.py`
