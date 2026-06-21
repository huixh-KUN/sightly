# 灵眸 Sightly

基于 PySide6 + RapidOCR 的屏幕自动化识别系统。监控屏幕指定区域，识别文字、数字、图像和颜色，自动执行点击和按键操作。

> 本项目基于 [AutoDoor OCR](https://github.com/wdhq4261761/autodoor) 二次开发，在原项目基础上进行了 UI 框架迁移、OCR 引擎替换、架构重构等多项技术升级。

## 技术特性

- **PySide6 (Qt6)**：现代化桌面 UI 框架，支持深色/浅色主题切换
- **RapidOCR + ONNX Runtime**：内置 OCR 引擎，无需外部安装，开箱即用
- **CLAHE + 双边滤波**：图像自适应直方图均衡化 + 降噪，提升识别准确率
- **多格式数字识别**：支持整数、小数、千分位、分数，可配置置信度阈值
- **随机偏移点击**：点击位置支持随机偏移范围，避免固定坐标被检测
- **模块化 + 组件化架构**：信号槽解耦，可复用 UI 组件（开关、下拉框、卡片等）
- **DD 虚拟键盘**：支持 DirectInput 游戏兼容
- **全局快捷键**：即使窗口失焦也能控制启停

## 功能特性

### 文字识别 (OCR)
- 多区域并行监控，每组独立配置
- 支持简体中文、繁体中文、英文三种语言
- 关键词匹配触发，支持多关键词逗号分隔
- 可配置识别间隔、暂停时长、触发按键
- 识别后自动点击匹配位置，支持随机偏移

### 数字识别
- 基于 RapidOCR 的实时数字识别
- 支持整数、小数、千分位逗号、分数格式
- 可配置置信度阈值过滤低质量结果
- 阈值触发按键，支持报警

### 图像检测
- 基于 OpenCV 模板匹配
- 支持截图或导入本地图像作为模板
- 可调匹配度阈值（0-100%）
- 匹配后自动点击、按键、报警

### 颜色识别
- 屏幕颜色实时检测，可配容差
- 识别到目标颜色后执行脚本命令

### 后台监控
- 绑定目标窗口，后台运行无需置顶
- 支持文字识别、图像检测、颜色识别三种模式
- 相对坐标自适应窗口大小变化

### 定时任务
- 定时按键/鼠标点击
- 支持屏幕坐标定位
- 可配随机偏移

### 脚本运行
- 录制键盘鼠标操作
- 手动编辑脚本（按键、延迟、鼠标命令）
- 导入/导出脚本文件

## 技术栈

| 技术 | 用途 |
|------|------|
| **PySide6** | Qt6 Python 绑定，桌面 UI 框架 |
| **RapidOCR** | 基于 PaddleOCR + ONNX Runtime 的文字识别引擎 |
| **OpenCV** | 图像处理、模板匹配、CLAHE 增强、双边滤波 |
| **Pillow** | 图像格式转换和预处理 |
| **PyAutoGUI** | 跨平台鼠标键盘自动化 |
| **pynput** | 全局快捷键监听 |
| **pywin32** | Windows API 调用（窗口捕获、输入控制） |

### 关于 RapidOCR

本项目使用 [RapidOCR](https://github.com/RapidAI/RapidOCR) 作为 OCR 引擎，相比原项目使用的 Tesseract：

- **无需外部安装**：基于 ONNX Runtime，pip install 即可使用
- **开箱即用**：内置模型，不需要手动下载训练数据
- **中英文混合识别**：单引擎同时支持中英文，无需切换
- **识别精度更高**：基于 PaddleOCR 模型，在中文场景表现更优

## 安装

### 环境要求
- Python 3.10+
- Windows 10/11

### 从源码运行

```bash
# 克隆仓库
git clone https://github.com/huixh-KUN/sightly.git
cd sightly

# 创建虚拟环境（推荐）
python -m venv venv
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 启动
python main.py
```

### 依赖说明

```
pyautogui>=0.9.54       # 鼠标键盘自动化
Pillow>=10.0.0          # 图像处理
opencv-python-headless  # 图像处理 + 模板匹配
rapidocr_onnxruntime    # OCR 引擎（内置模型）
numpy>=1.21.0           # 数值计算
pynput>=1.7.6           # 全局快捷键
pywin32>=305            # Windows API
screeninfo>=0.8.1       # 屏幕信息
imagehash>=4.3.2        # 图像哈希
requests>=2.31.0        # 版本检查
```

### 打包

```bash
build_standard.bat    # 标准版（PyAutoGUI）
build_dd.bat          # DD 虚拟键盘版（DirectInput 游戏兼容）
```

打包产物在 `dist/` 目录下。

## 使用说明

1. 启动程序后，在各功能页配置监控区域和参数
2. 到首页勾选要启用的模块
3. 点击"开始运行"启动监控
4. 系统会在后台自动识别并执行预设操作
5. 使用全局快捷键（默认 F10 开始 / F12 停止）控制运行

## 项目结构

```
sightly/
├── main.py                 # 程序入口
├── core/                   # 核心模块
│   ├── config.py           # 配置管理
│   ├── controller.py       # 模块控制器
│   ├── events.py           # 事件系统
│   ├── logging.py          # 日志管理
│   └── click_handler.py    # 点击处理（含随机偏移）
├── modules/                # 功能模块
│   ├── ocr.py              # 文字识别
│   ├── number.py           # 数字识别
│   ├── image.py            # 图像检测
│   ├── color.py            # 颜色识别
│   ├── timed.py            # 定时任务
│   ├── script.py           # 脚本执行
│   ├── background.py       # 后台监控
│   └── alarm.py            # 报警模块
├── ui/                     # 用户界面
│   ├── main_window.py      # 主窗口
│   ├── theme.py            # 深色/浅色主题
│   ├── widgets.py          # 基础组件
│   └── components/         # 可复用组件
│       ├── switch_button.py    # 自绘制开关
│       ├── combo_box.py        # 统一下拉框
│       ├── key_capture.py      # 按键捕获
│       ├── module_state.py     # 模块状态控制
│       └── ...
├── utils/                  # 工具类
│   ├── recognition.py      # RapidOCR 识别器
│   ├── image.py            # CLAHE + 双边滤波预处理
│   ├── screenshot.py       # 截图管理
│   └── coordinate.py       # 坐标转换
├── input/                  # 输入控制
│   ├── win32_input.py      # Win32 API 输入
│   └── dd_input.py         # DD 虚拟键盘
├── config/                 # 配置文件
├── voice/                  # 报警音频
└── drivers/                # DD 驱动
```

## 配置文件

配置自动保存在系统目录：
- Windows：`%APPDATA%/灵眸/config.json`

## 特别鸣谢

本项目基于 [AutoDoor OCR](https://github.com/wdhq4261761/autodoor) 二次开发，感谢原作者 **Flown王砖家** 的开源贡献。

## 许可证

MIT License
