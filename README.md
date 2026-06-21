# 灵眸 Sightly

基于 PySide6 + RapidOCR 的屏幕自动化识别系统。监控屏幕区域，识别文字/图像/颜色，自动执行点击和按键操作。

## 功能特性

### 核心能力
- **文字识别 (OCR)**：多区域文字监控，关键词触发，支持中英文
- **数字识别**：屏幕数字实时识别，阈值触发
- **图像检测**：OpenCV 模板匹配，支持截图/本地图片
- **颜色识别**：屏幕颜色检测，容差匹配
- **后台监控**：绑定窗口后台运行，无需置顶
- **定时任务**：定时按键/点击，支持坐标定位
- **脚本运行**：录制/编辑自动化脚本，支持鼠标键盘操作

### 技术特性
- PySide6 现代 UI，支持深色/浅色主题
- 模块化架构，组件化开发
- RapidOCR 内置引擎，无需外部安装
- 图像预处理增强（CLAHE + 双边滤波）
- DD 虚拟键盘支持（DirectInput 游戏兼容）
- 全局快捷键控制

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

### 打包

```bash
# Windows 打包
build_standard.bat    # 标准版
build_dd.bat          # DD 虚拟键盘版
```

打包产物在 `dist/` 目录下。

## 项目结构

```
sightly/
├── main.py                 # 程序入口
├── core/                   # 核心模块
│   ├── config.py           # 配置管理
│   ├── controller.py       # 模块控制器
│   ├── events.py           # 事件系统
│   ├── logging.py          # 日志管理
│   └── click_handler.py    # 点击处理
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
│   ├── home_panel.py       # 首页
│   ├── ocr_panel.py        # 文字识别页
│   ├── timed_panel.py      # 定时功能页
│   ├── number_panel.py     # 数字识别页
│   ├── image_panel.py      # 图像检测页
│   ├── script_panel.py     # 脚本运行页
│   ├── background_panel.py # 后台监控页
│   ├── settings_panel.py   # 设置页
│   ├── theme.py            # 主题配置
│   ├── widgets.py          # 基础组件
│   └── components/         # 可复用组件
├── utils/                  # 工具类
│   ├── recognition.py      # OCR 识别器
│   ├── screenshot.py       # 截图管理
│   ├── image.py            # 图像处理
│   └── version.py          # 版本检查
├── input/                  # 输入控制
│   ├── controller.py       # 控制器工厂
│   ├── win32_input.py      # Win32 输入
│   └── dd_input.py         # DD 虚拟键盘
├── config/                 # 配置文件
├── voice/                  # 音频资源
└── drivers/                # 驱动文件
```

## 使用说明

1. 启动程序后，在各功能页配置监控区域和参数
2. 到首页勾选要启用的模块
3. 点击"开始运行"启动监控
4. 系统会在后台自动识别并执行预设操作

## 配置文件

配置自动保存在系统目录：
- Windows：`%APPDATA%/灵眸/config.json`

## 特别鸣谢

本项目基于 [AutoDoor OCR](https://github.com/wdhq4261761/autodoor) 二次开发，感谢原作者 **Flown王砖家** 的开源贡献。

## 许可证

MIT License
