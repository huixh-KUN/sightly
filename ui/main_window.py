import os
import sys

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QStackedWidget, QFrame,
    QApplication, QSizePolicy, QSpacerItem
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QFont, QShortcut, QKeySequence

from ui.components import ModuleStateController

from ui.theme import Colors, ThemeManager
from ui.widgets import StatusIndicator, NavButton, Divider
from ui.home_panel import HomePanel
from ui.ocr_panel import OCRPanel
from ui.timed_panel import TimedPanel
from ui.number_panel import NumberPanel
from ui.image_panel import ImagePanel
from ui.background_panel import BackgroundPanel
from ui.script_panel import ScriptPanel
from ui.settings_panel import SettingsPanel

from core.config import ConfigManager, ConfigVar
from core.logging import LoggingManager
from input.keyboard import setup_shortcuts
from input.controller import InputController
from core.threading import ThreadManager
from core.events import EventManager
from core.platform import PlatformAdapter
from core.controller import ModuleController
from modules.ocr import OCRModule
from modules.timed import TimedModule
from modules.number import NumberModule
from modules.alarm import AlarmModule
from modules.script import ScriptModule
from modules.color import ColorRecognitionManager
from modules.image import ImageDetectionManager
from modules.background import BackgroundManager


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("灵眸")
        self.setMinimumSize(1050, 650)
        self.resize(1050, 700)
        self.statusBar().setVisible(False)

        self.setStyleSheet(ThemeManager.qss())

        self.config_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config")
        self.config_file_path = os.path.join(self.config_dir, "config.json")
        self.log_file_path = os.path.abspath("autodoor.log")
        os.makedirs(self.config_dir, exist_ok=True)
        self._is_running = False
        self._is_paused = False
        self.tesseract_available = True

        self.ocr_groups = []
        self.timed_groups = []
        self.number_regions = []
        self.image_groups = []
        self.background_groups = []
        self.script_config = {}
        self.settings_config = {}

        self.start_shortcut_var = ConfigVar("F10")
        self.stop_shortcut_var = ConfigVar("F12")
        self.record_hotkey_var = ConfigVar("F11")

        self.module_state = ModuleStateController(self)

        self._init_backend()
        self.module_state.set_debug_logger(self.logging_manager)
        self.logging_manager.debug("INIT", "ModuleStateController 初始化完成")
        self.logging_manager.debug("INIT", "MainWindow.__init__ 完成")
        self._init_ui()
        self.logging_manager.debug("INIT", "_init_ui 完成")
        self._init_signals()
        self.logging_manager.debug("INIT", "_init_signals 完成")
        self._init_module_bindings()
        self.logging_manager.debug("INIT", "_init_module_bindings 完成")

    @property
    def is_running(self):
        return self._is_running

    @is_running.setter
    def is_running(self, value):
        self._is_running = value

    @property
    def is_paused(self):
        return self._is_paused

    @is_paused.setter
    def is_paused(self, value):
        self._is_paused = value

    def _init_backend(self):
        self.logging_manager = LoggingManager(self)
        self.logging_manager.debug("INIT", "LoggingManager 初始化完成")
        self.input_controller = InputController(self)
        self.logging_manager.debug("INIT", "InputController 初始化完成")
        self.thread_manager = ThreadManager(self)
        self.logging_manager.debug("INIT", "ThreadManager 初始化完成")
        self.event_manager = EventManager(self)
        self.logging_manager.debug("INIT", "EventManager 初始化完成")
        self.config_manager = ConfigManager(self)
        self.logging_manager.debug("INIT", "ConfigManager 初始化完成")
        self.platform_adapter = PlatformAdapter(self)
        self.logging_manager.debug("INIT", "PlatformAdapter 初始化完成")

        self.ocr_module = OCRModule(self)
        self.logging_manager.debug("INIT", "OCRModule 初始化完成")
        self.timed_module = TimedModule(self)
        self.logging_manager.debug("INIT", "TimedModule 初始化完成")
        self.number_module = NumberModule(self)
        self.logging_manager.debug("INIT", "NumberModule 初始化完成")
        self.alarm_module = AlarmModule(self)
        self.logging_manager.debug("INIT", "AlarmModule 初始化完成")
        self.script_module = ScriptModule(self)
        self.logging_manager.debug("INIT", "ScriptModule 初始化完成")
        self.color_manager = ColorRecognitionManager(self)
        self.logging_manager.debug("INIT", "ColorRecognitionManager 初始化完成")
        self.image_manager = ImageDetectionManager(self)
        self.logging_manager.debug("INIT", "ImageDetectionManager 初始化完成")
        self.background_manager = BackgroundManager(self)
        self.logging_manager.debug("INIT", "BackgroundManager 初始化完成")

        self.modules = {
            'ocr': self.ocr_module,
            'timed': self.timed_module,
            'number': self.number_module,
            'alarm': self.alarm_module,
            'script': self.script_module,
            'color': self.color_manager,
            'image': self.image_manager,
            'background': self.background_manager,
        }

        self.module_controller = ModuleController(self)
        self.logging_manager.debug("INIT", "ModuleController 初始化完成")

        self.module_state.register("ocr", "文字识别", "监控屏幕文字，匹配关键词触发", "📝")
        self.module_state.register("timed", "定时功能", "按设定间隔自动执行按键操作", "⏱")
        self.module_state.register("number", "数字识别", "识别屏幕数字变化触发动作", "🔢")
        self.module_state.register("image", "图像检测", "检测屏幕图像匹配模板触发", "🖼️")
        self.module_state.register("background", "后台监控", "监控指定窗口的内容变化", "🖥️")
        self.module_state.register("script", "脚本运行", "录制和执行按键脚本", "📜")
        self.logging_manager.debug("INIT", "所有模块注册完成")

    def _init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self._create_header(main_layout)

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)

        self._create_sidebar(body_layout)
        self._create_content(body_layout)
        main_layout.addWidget(body, 1)

    def _create_header(self, parent_layout):
        header = QFrame()
        header.setObjectName("headerBar")
        h_layout = QHBoxLayout(header)
        h_layout.setContentsMargins(24, 0, 24, 0)

        title = QLabel("灵眸 Sightly")
        title.setObjectName("headerTitle")
        h_layout.addWidget(title)

        h_layout.addStretch()

        self.status_dot = StatusIndicator()
        h_layout.addWidget(self.status_dot)

        self.status_label = QLabel("空闲")
        self.status_label.setObjectName("statusLabel")
        h_layout.addWidget(self.status_label)

        h_layout.addSpacing(16)

        parent_layout.addWidget(header)

    def _create_sidebar(self, parent_layout):
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")

        s_layout = QVBoxLayout(sidebar)
        s_layout.setContentsMargins(0, 0, 0, 0)
        s_layout.setSpacing(0)

        s_layout.addSpacing(8)

        self.nav_buttons = []
        nav_items = [
            ("home", "🏠", "首页"),
            ("ocr", "📝", "文字识别"),
            ("timed", "⏱", "定时功能"),
            ("number", "🔢", "数字识别"),
            ("image", "🖼️", "图像检测"),
            ("background", "🖥️", "后台监控"),
            ("script", "📜", "脚本运行"),
            ("settings", "⚙️", "设置"),
        ]

        for page_id, icon, label in nav_items:
            btn = NavButton(f" {icon}  {label}")
            btn.clicked.connect(lambda checked, pid=page_id: self._navigate_to(pid))
            s_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        s_layout.addStretch()

        parent_layout.addWidget(sidebar)

    def _create_content(self, parent_layout):
        content = QFrame()
        content.setObjectName("contentArea")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack)

        self.panels = {}
        panel_order = [
            ('home', HomePanel),
            ('ocr', OCRPanel),
            ('timed', TimedPanel),
            ('number', NumberPanel),
            ('image', ImagePanel),
            ('background', BackgroundPanel),
            ('script', ScriptPanel),
            ('settings', SettingsPanel),
        ]
        for panel_id, PanelClass in panel_order:
            self.panels[panel_id] = PanelClass(self)
            self.stack.addWidget(self.panels[panel_id])

        parent_layout.addWidget(content, 1)

    def _navigate_to(self, page_id):
        idx = list(self.panels.keys()).index(page_id)
        self.stack.setCurrentIndex(idx)
        for btn in self.nav_buttons:
            btn.setChecked(False)
        nav_keys = ['home', 'ocr', 'timed', 'number', 'image', 'background', 'script', 'settings']
        if page_id in nav_keys:
            self.nav_buttons[nav_keys.index(page_id)].setChecked(True)

    def _init_signals(self):
        self.module_state.all_start_requested.connect(self._on_start_all)
        self.module_state.all_stop_requested.connect(self._on_stop_all)
        self.logging_manager.debug("INIT", "信号连接完成: all_start_requested/all_stop_requested")

    def _init_module_bindings(self):
        home = self.panels.get('home')
        if home and hasattr(home, 'get_toggles'):
            toggles = home.get_toggles()
            self.logging_manager.debug("INIT", f"绑定模块开关: {list(toggles.keys())}")
            for module_id, toggle in toggles.items():
                self.module_state.bind_switch(module_id, toggle)
        self.logging_manager.debug("INIT", "模块开关绑定完成")

    def _on_start_all(self):
        if self._is_running:
            self.logging_manager.debug("START", "已在运行中，忽略启动请求")
            return
        self._is_running = True
        self.logging_manager.debug("START", "_on_start_all 开始")
        self._sync_panel_configs()
        enabled = self.module_state.enabled_modules()
        self.logging_manager.debug("START", f"已启用模块: {enabled}")
        for module_id in enabled:
            self._start_module(module_id)
        if not enabled:
            self.logging_manager.log_message("未启用任何模块，请在首页勾选")
        self._set_status("运行中", running=True)
        self.logging_manager.debug("START", "_on_start_all 完成")

    def _sync_panel_configs(self):
        self.logging_manager.debug("CONFIG", "开始同步面板配置")
        for panel_id, panel in self.panels.items():
            if hasattr(panel, 'collect_config'):
                config = panel.collect_config()
                size = len(config) if isinstance(config, (list, dict)) else 0
                self.logging_manager.debug("CONFIG", f"面板 {panel_id} 配置: {size} 项")
                if panel_id == 'ocr':
                    self.ocr_groups = config
                elif panel_id == 'timed':
                    self.timed_groups = config
                elif panel_id == 'number':
                    self.number_regions = config
                elif panel_id == 'image':
                    self.image_groups = config
                elif panel_id == 'background':
                    self.background_groups = config
                elif panel_id == 'script':
                    self.script_config = config
                elif panel_id == 'settings':
                    self.settings_config = config
        self.logging_manager.debug("CONFIG", "面板配置同步完成")

    def _on_stop_all(self):
        if not self._is_running:
            self.logging_manager.debug("STOP", "未在运行中，忽略停止请求")
            return
        self._is_running = False
        self.logging_manager.debug("STOP", "_on_stop_all 开始")
        for module_id in ['ocr', 'timed', 'number', 'image', 'background', 'script']:
            self._stop_module(module_id)
        self.alarm_module.play_stop_sound()
        self._set_status("空闲", running=False)
        self.logging_manager.debug("STOP", "_on_stop_all 完成")

    def _start_module(self, module_id):
        try:
            self.logging_manager.debug("MODULE", f"启动模块: {module_id}")
            if module_id == 'ocr':
                self.ocr_module.start_monitoring()
            elif module_id == 'timed':
                self.timed_module.start_timed_tasks()
            elif module_id == 'number':
                self.number_module.start_number_recognition()
            elif module_id == 'image':
                self.image_manager.start_all_detection()
            elif module_id == 'background':
                self.background_manager.start_all_groups()
            elif module_id == 'script':
                self.script_module.start()
            self.logging_manager.debug("MODULE", f"模块 {module_id} 启动成功")
            self.logging_manager.log_message(f"  ✓ {module_id} 已启动")
        except Exception as e:
            self.logging_manager.debug("MODULE", f"模块 {module_id} 启动失败: {e}")
            self.logging_manager.log_message(f"  ✗ {module_id} 启动失败: {e}")

    def _stop_module(self, module_id):
        try:
            self.logging_manager.debug("MODULE", f"停止模块: {module_id}")
            if module_id == 'ocr':
                self.ocr_module.stop_monitoring()
            elif module_id == 'timed':
                self.timed_module.stop_timed_tasks()
            elif module_id == 'number':
                self.number_module.stop_number_recognition()
            elif module_id == 'image':
                self.image_manager.stop_all_detection()
            elif module_id == 'background':
                self.background_manager.stop_all_groups()
            elif module_id == 'script':
                self.script_module.stop()
            self.logging_manager.debug("MODULE", f"模块 {module_id} 停止成功")
        except Exception:
            self.logging_manager.debug("MODULE", f"模块 {module_id} 停止异常")
            pass

    def start_module(self, module_name, start_func):
        """Called by modules (ocr.py, etc.) to start their worker thread."""
        start_func()

    def _set_status(self, text, running=None):
        self.status_label.setText(text)
        if running is not None:
            self.status_dot.running = running
            self._is_running = running

    def log_message(self, message):
        self.logging_manager.log_message(message)

    def _collect_module_config(self):
        return {mid: self.module_state.is_enabled(mid) for mid in self.module_state.modules}

    def _apply_module_config(self, config_dict):
        for mid, enabled in config_dict.items():
            self.module_state.set_enabled(mid, enabled)

    def load_saved_config(self):
        self.logging_manager.debug("CONFIG", "开始加载保存的配置")
        config = self.config_manager.read_config()
        if config:
            module_enabled = config.get("module_enabled", {})
            self.logging_manager.debug("CONFIG", f"模块启用状态: {module_enabled}")
            self._apply_module_config(module_enabled)

            script_cfg = config.get("script", {})
            if script_cfg and 'script' in self.panels:
                self.panels['script'].set_config(script_cfg)
                self.logging_manager.debug("CONFIG", "脚本内容已恢复")

            settings_cfg = config.get("settings", {})
            if settings_cfg and 'settings' in self.panels:
                self.panels['settings'].set_config(settings_cfg)
                self.logging_manager.debug("CONFIG", "设置已恢复")
                self._apply_settings(settings_cfg)

            self.logging_manager.log_message("配置已加载")
        else:
            self.logging_manager.debug("CONFIG", "无保存的配置")

    def _apply_settings(self, settings_cfg):
        general = settings_cfg.get("general", {})
        if general.get("start_key"):
            self.start_shortcut_var.set(general["start_key"])
        if general.get("stop_key"):
            self.stop_shortcut_var.set(general["stop_key"])
        self._register_shortcuts()
        self.logging_manager.debug("CONFIG", "设置已应用")

    def save_config(self):
        self.logging_manager.debug("CONFIG", "开始保存配置")
        config = self.config_manager.read_config() or {}
        config["module_enabled"] = self._collect_module_config()

        if 'script' in self.panels:
            config["script"] = self.panels['script'].collect_config()
        if 'settings' in self.panels:
            config["settings"] = self.panels['settings'].collect_config()

        self.logging_manager.debug("CONFIG", f"模块启用状态: {config.get('module_enabled', {})}")
        self.config_manager.save_config(config)
        self.logging_manager.debug("CONFIG", "配置保存完成")

    def closeEvent(self, event):
        self.logging_manager.debug("CLOSE", "窗口关闭中...")
        self.save_config()
        self._shutdown_all_modules()
        super().closeEvent(event)

    def _shutdown_all_modules(self):
        self.logging_manager.debug("CLOSE", "停止所有模块...")
        try:
            if hasattr(self, 'script_module'):
                self.script_module.stop(stop_color_recognition=False)
            if hasattr(self, 'number_module'):
                self.number_module.stop_number_recognition()
            if hasattr(self, 'timed_module'):
                self.timed_module.stop_timed_tasks()
            if hasattr(self, 'image_manager'):
                self.image_manager.stop_all_detection()
            if hasattr(self, 'color_manager'):
                self.color_manager.stop_color_recognition()
            if hasattr(self, 'ocr_module'):
                self.ocr_module.stop_monitoring()
            if hasattr(self, 'background_manager'):
                self.background_manager.stop_all_groups()
            if hasattr(self, 'event_manager'):
                self.event_manager.stop_event_thread()
            if hasattr(self, 'global_listener') and self.global_listener:
                try:
                    self.global_listener.stop()
                    if hasattr(self.global_listener, 'join'):
                        self.global_listener.join(timeout=2)
                except Exception:
                    pass
            # 清理延迟创建的 script_executor
            script_exec = getattr(self, 'script_executor', None) or getattr(self, 'script_module', None)
            if hasattr(script_exec, 'is_running') and script_exec.is_running:
                script_exec.stop_script()
            self.logging_manager.debug("CLOSE", "所有模块已停止")
        except Exception as e:
            self.logging_manager.debug("CLOSE", f"停止模块时出错: {e}")

    def run(self):
        self.logging_manager.debug("RUN", "run() 开始执行")
        self.load_saved_config()
        self.logging_manager.debug("RUN", "配置加载完成")
        self._navigate_to('home')
        self.logging_manager.debug("RUN", "导航到首页")
        self._register_shortcuts()
        self.logging_manager.debug("RUN", "快捷键注册完成")
        setup_shortcuts(self)
        self.logging_manager.debug("RUN", "全局快捷键设置完成")
        self.show()
        self.logging_manager.debug("RUN", "窗口显示完成")

    def _register_shortcuts(self):
        QShortcut(QKeySequence(self.start_shortcut_var.get()), self).activated.connect(
            lambda: self._on_start_all() if not self._is_running else None
        )
        QShortcut(QKeySequence(self.stop_shortcut_var.get()), self).activated.connect(
            lambda: self._on_stop_all() if self._is_running else None
        )


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("灵眸")

    window = MainWindow()
    window.run()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
