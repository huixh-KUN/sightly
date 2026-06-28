import os
import sys

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QStackedWidget, QFrame,
    QApplication, QSizePolicy, QSpacerItem, QSpinBox,
    QStyleFactory,
)
from PySide6.QtCore import Qt, QTimer, QEvent
from PySide6.QtGui import QIcon, QFont, QShortcut, QKeySequence

from core.state import AppState
from ui.theme import ThemeManager
from ui.components import ThemeSwitcher
from core.config import ConfigManager
from core.logging import LoggingManager
from input.keyboard import setup_shortcuts
from ui.widgets import StatusIndicator, NavButton, Divider
from ui.home_panel import HomePanel
from ui.ocr_panel import OCRPanel
from ui.timed_panel import TimedPanel
from ui.number_panel import NumberPanel
from ui.image_panel import ImagePanel
from ui.background_panel import BackgroundPanel
from ui.settings_panel import SettingsPanel

from input.controller import InputController


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("灵眸")
        self.setMinimumSize(1050, 650)
        self.resize(1050, 700)
        self.statusBar().setVisible(False)

        QApplication.instance().setStyleSheet(ThemeManager.qss())
        QApplication.instance().setStyle(QStyleFactory.create("Fusion"))

        self.log_file_path = os.path.abspath("logs/sightly.log")
        self.config_file_path = os.path.abspath("config/config.json")
        self._is_running = False
        self._is_paused = False
        self._is_closing = False
        self.tesseract_available = True

        self.ocr_groups = []
        self.timed_groups = []
        self.number_regions = []
        self.image_groups = []
        self.background_groups = []
        self.script_config = {}
        self.settings_config = {}

        self.app_state = AppState(self)

        self.alarm_sound_path = ""
        self.alarm_volume = 70
        self.alarm_volume_str = "70"
        self.alarm_enabled = {
            "ocr": False,
            "timed": False,
            "number": False,
            "image": False,
        }

        self._init_backend()
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
        self.app_state.set_logger(self.logging_manager)
        self.logging_manager.debug("INIT", "LoggingManager 初始化完成")
        self.input_controller = InputController(self)
        self.logging_manager.debug("INIT", "InputController 初始化完成")
        self.config_manager = ConfigManager(self)
        self.logging_manager.debug("INIT", "ConfigManager 初始化完成")
        self._migrate_old_config()

        from modules.ocr import OCRModule as _OCR
        from modules.timed import TimedModule as _Timed
        from modules.number import NumberModule as _Number
        from modules.alarm import AlarmModule as _Alarm
        from modules.color import ColorRecognitionManager as _Color
        from modules.image import ImageDetectionManager as _Image
        from modules.background import BackgroundManager as _BG

        self.ocr_module = _OCR(self)
        self.logging_manager.debug("INIT", "OCRModule 初始化完成")
        self.timed_module = _Timed(self)
        self.logging_manager.debug("INIT", "TimedModule 初始化完成")
        self.number_module = _Number(self)
        self.logging_manager.debug("INIT", "NumberModule 初始化完成")
        self.alarm_module = _Alarm(self)
        self.logging_manager.debug("INIT", "AlarmModule 初始化完成")
        self.color_manager = _Color(self)
        self.logging_manager.debug("INIT", "ColorRecognitionManager 初始化完成")
        self.image_manager = _Image(self)
        self.logging_manager.debug("INIT", "ImageDetectionManager 初始化完成")
        self.background_manager = _BG(self)
        self.logging_manager.debug("INIT", "BackgroundManager 初始化完成")

        self.modules = {
            'ocr': self.ocr_module,
            'timed': self.timed_module,
            'number': self.number_module,
            'alarm': self.alarm_module,
            'color': self.color_manager,
            'image': self.image_manager,
            'background': self.background_manager,
        }

        self.app_state.register_module("ocr", "文字识别", "监控屏幕文字，匹配关键词触发", "📝")
        self.app_state.register_module("timed", "定时功能", "按设定间隔自动执行按键操作", "⏱")
        self.app_state.register_module("number", "数字识别", "识别屏幕数字变化触发动作", "🔢")
        self.app_state.register_module("image", "图像检测", "检测屏幕图像匹配模板触发", "🖼️")
        self.app_state.register_module("background", "后台监控", "监控指定窗口的内容变化", "🖥️")
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

        self.theme_switcher = ThemeSwitcher()
        self.theme_switcher.themeChanged.connect(self._on_theme_changed)
        h_layout.addWidget(self.theme_switcher)

        h_layout.addSpacing(8)

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
        nav_keys = ['home', 'ocr', 'timed', 'number', 'image', 'background', 'settings']
        if page_id in nav_keys:
            self.nav_buttons[nav_keys.index(page_id)].setChecked(True)

    def _init_signals(self):
        self.app_state.all_start_requested.connect(self._on_start_all)
        self.app_state.all_stop_requested.connect(self._on_stop_all)
        self.app_state.record_hotkey_triggered.connect(self._on_record_hotkey)
        self.app_state.config_loaded.connect(self._on_config_loaded)
        bg = self.panels.get('background')
        if bg:
            bg.window_selected.connect(self._on_bg_window_selected)
            bg.auto_reconnect_requested.connect(self._on_bg_auto_reconnect)
        tm = self.panels.get('timed')
        if tm:
            tm.position_selection_requested.connect(self._on_timed_position_selection)
        st = self.panels.get('settings')
        if st:
            st.config_changed.connect(self._on_settings_config_changed)
            st.shortcuts_changed.connect(self._on_settings_shortcuts_changed)
        hm = self.panels.get('home')
        if hm:
            hm.config_save_requested.connect(self.save_config)
        for panel_id in ['ocr', 'timed', 'number', 'image', 'background']:
            panel = self.panels.get(panel_id)
            if panel:
                panel.test_group_requested.connect(
                    lambda idx, pid=panel_id: self._on_test_group(pid, idx)
                )
        self.logging_manager.debug("INIT", "信号连接完成: all_start_requested/all_stop_requested/record_hotkey_triggered/config_loaded")

    def _init_module_bindings(self):
        home = self.panels.get('home')
        if home and hasattr(home, 'get_toggles'):
            toggles = home.get_toggles()
            self.logging_manager.debug("INIT", f"绑定模块开关: {list(toggles.keys())}")
            for module_id, toggle in toggles.items():
                self.app_state.bind_module_switch(module_id, toggle)
        self.logging_manager.debug("INIT", "模块开关绑定完成")

    def _on_start_all(self):
        if self._is_running:
            self.logging_manager.debug("START", "已在运行中，忽略启动请求")
            return
        self._is_running = True
        self.logging_manager.debug("START", "_on_start_all 开始")
        self._sync_panel_configs()
        enabled = self.app_state.enabled_modules()
        self.logging_manager.debug("START", f"已启用模块: {enabled}")
        for module_id in enabled:
            self._start_module(module_id)
        if not enabled:
            self.logging_manager.log_message("未启用任何模块，请在首页勾选")
        self._lock_panels(True)
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
                    if isinstance(config, dict):
                        self.background_groups = config.get("groups", [])
                    else:
                        self.background_groups = config
                elif panel_id == 'settings':
                    self.settings_config = config
        self.logging_manager.debug("CONFIG", "面板配置同步完成")

    def _on_stop_all(self):
        if not self._is_running:
            self.logging_manager.debug("STOP", "未在运行中，忽略停止请求")
            return
        self._is_running = False
        self.logging_manager.debug("STOP", "_on_stop_all 开始")
        for module_id in ['ocr', 'timed', 'number', 'image', 'background']:
            self._stop_module(module_id)
        self.alarm_module.play_stop_sound()
        self._lock_panels(False)
        self._set_status("空闲", running=False)
        self.logging_manager.debug("STOP", "_on_stop_all 完成")

    def _lock_panels(self, locked):
        from ui.widgets import set_panel_view_only
        lockable = ['ocr', 'background', 'image', 'timed', 'number', 'settings']
        for pid in lockable:
            panel = self.panels.get(pid)
            if panel:
                set_panel_view_only(panel, locked)
        home = self.panels.get('home')
        if home and hasattr(home, 'set_toggles_enabled'):
            home.set_toggles_enabled(not locked)

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Wheel and isinstance(obj, QSpinBox):
            return True
        return super().eventFilter(obj, event)

    def _on_record_hotkey(self): pass

    def _on_bg_window_selected(self, hwnd, title):
        self.background_manager.set_target_window(hwnd)

    def _on_bg_auto_reconnect(self, wc, wp, wt):
        ok = self.background_manager.auto_reconnect(wc, wp, wt)
        bg = self.panels.get('background')
        if ok:
            bg.on_auto_reconnect_result(True, self.background_manager.target_hwnd, self.background_manager.target_title or "")
        else:
            bg.on_auto_reconnect_result(False, 0, "")

    def _on_timed_position_selection(self, index):
        panel = self.panels.get('timed')
        if panel and panel._edit_window and hasattr(panel._edit_window._editor, '_on_pos_selected'):
            self.timed_module.start_timed_position_selection(
                index, on_selected=panel._edit_window._editor._on_pos_selected
            )

    def _format_test_status(self, result):
        matched = result.get("matched")
        if matched is None:
            executed = result.get("executed", False)
            return "执行完成" if executed else "未配置动作"
        return "检测通过" if matched else "检测未通过"

    def _on_test_group(self, panel_id, idx):
        from PySide6.QtWidgets import QMessageBox
        from PySide6.QtCore import QTimer

        if self._is_running:
            QMessageBox.warning(self, "测试", "请先停止运行再进行测试")
            return

        wait_panels = {
            'timed': ('timed', 'interval', 10, self.timed_module.test_group),
            'image': ('image', 'interval', 5, self.image_manager.test_group),
            'ocr': ('ocr', 'interval', 3, self.ocr_module.test_group),
            'background': ('background', 'interval', 3, self.background_manager.run_once),
        }
        if panel_id in wait_panels:
            pkey, interval_key, default, run_fn = wait_panels[panel_id]
            panel = self.panels.get(pkey)
            if not panel or idx >= len(panel.groups_data):
                QMessageBox.information(self, "测试", "组索引越界")
                return
            interval = float(panel.groups_data[idx].get(interval_key, default))

            wait_box = QMessageBox(self)
            wait_box.setWindowTitle("测试")
            wait_box.setText(f"等待 {interval} 秒后执行测试动作…")
            wait_box.setStandardButtons(QMessageBox.NoButton)
            wait_box.show()

            def _do_wait_test():
                wait_box.close()
                wait_box.deleteLater()
                self._sync_panel_configs()
                try:
                    result = run_fn(idx)
                except Exception as e:
                    self.logging_manager.error("TEST", f"{pkey} 测试失败: {e}")
                    QMessageBox.critical(self, "测试失败", str(e))
                    return
                status = self._format_test_status(result)
                QMessageBox.information(
                    self, f"测试结果 - {pkey}",
                    f"{status}\n\n{result.get('detail', '')}"
                )

            QTimer.singleShot(interval * 1000, _do_wait_test)
            return

        self._sync_panel_configs()
        test_map = {
            'number': lambda: self.number_module.test_group(idx),
        }
        test_fn = test_map.get(panel_id)
        if test_fn is None:
            QMessageBox.information(self, "测试", "该模块暂不支持单次测试")
            return
        try:
            result = test_fn()
        except Exception as e:
            self.logging_manager.error("TEST", f"{panel_id} 测试失败: {e}")
            QMessageBox.critical(self, "测试失败", str(e))
            return
        status = self._format_test_status(result)
        QMessageBox.information(
            self, f"测试结果 - {panel_id}",
            f"{status}\n\n{result.get('detail', '')}"
        )

    def _on_settings_config_changed(self, config):
        alarm = config.get("alarm", {})
        if alarm.get("sound_path"):
            self.alarm_sound_path = alarm["sound_path"]
        if "volume" in alarm:
            self.alarm_volume = alarm["volume"]
            self.alarm_volume_str = str(alarm["volume"])

    def _on_settings_shortcuts_changed(self, start_key, stop_key):
        if start_key:
            self.app_state.start_shortcut = start_key
        if stop_key:
            self.app_state.stop_shortcut = stop_key
        self._register_shortcuts()

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
            self.logging_manager.debug("MODULE", f"模块 {module_id} 启动成功")
            self.logging_manager.log_message(f"  ✓ {module_id} 已启动")
        except Exception as e:
            self.logging_manager.debug("MODULE", f"模块 {module_id} 启动失败: {e}")
            self.logging_manager.error("MODULE", f"  ✗ {module_id} 启动失败: {e}")

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
            self.logging_manager.debug("MODULE", f"模块 {module_id} 停止成功")
        except Exception as e:
            self.logging_manager.error("MODULE", f"模块 {module_id} 停止失败: {e}")

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


    def _migrate_old_config(self):
        if self.app_state._wm.list_workspaces():
            return
        old_config = self.config_manager.read_config()
        if old_config:
            self.app_state.create_workspace("默认配置")
            self.app_state._wm.save("默认配置", old_config)
            # 重新加载已保存的配置，覆盖 create_workspace 发出的空 config_loaded
            self.app_state._load_workspace("默认配置")
            self.logging_manager.debug("CONFIG", "旧配置已迁移到默认工作空间")

    def _on_config_loaded(self, config):
        self.logging_manager.debug("CONFIG", f"分发配置到面板, keys={list(config.keys()) if config else 'EMPTY'}")
        for panel_id in self.panels:
            panel = self.panels[panel_id]
            if not hasattr(panel, 'set_config'):
                continue
            panel_cfg = config.get(panel_id) if config else None
            if panel_cfg is not None:
                self.logging_manager.debug("CONFIG", f"  面板 {panel_id}: set_config({type(panel_cfg).__name__})")
                panel.set_config(panel_cfg)
                if panel_id == 'settings':
                    self._apply_settings(panel_cfg)
            else:
                if panel_id == 'settings':
                    panel.set_config({})
                else:
                    panel.set_config([])
                self.logging_manager.debug("CONFIG", f"  面板 {panel_id}: set_config(empty)")
        if config:
            self.logging_manager.log_message("配置已加载")
        else:
            self.logging_manager.debug("CONFIG", "无保存的配置")

    def _on_theme_changed(self, mode):
        ThemeManager.switch_to(mode)
        self.theme_switcher.set_theme(mode)
        self.app_state.save_index(theme=mode)

    def load_saved_config(self, workspace_name=None):
        self.logging_manager.debug("CONFIG", f"开始加载保存的配置 (name={workspace_name})")
        theme = ThemeManager._current
        if workspace_name:
            self.save_config()
            self.app_state.switch_workspace(workspace_name)
        else:
            loaded, theme = self.app_state.startup_load()
            self.logging_manager.debug("CONFIG", f"startup_load 返回: {loaded!r}")
            if loaded:
                self.logging_manager.debug("CONFIG", f"工作空间已加载: {loaded}")
        if theme and theme != ThemeManager._current:
            ThemeManager.switch_to(theme)
            self.theme_switcher.set_theme(theme)

    def _apply_settings(self, settings_cfg):
        general = settings_cfg.get("general", {})
        if general.get("start_key"):
            self.app_state.start_shortcut = general["start_key"]
        if general.get("stop_key"):
            self.app_state.stop_shortcut = general["stop_key"]
        self._register_shortcuts()
        alarm = settings_cfg.get("alarm", {})
        if alarm.get("sound_path"):
            self.alarm_sound_path = alarm["sound_path"]
        if "volume" in alarm:
            self.alarm_volume = alarm["volume"]
            self.alarm_volume_str.set(str(alarm["volume"]))
        self.logging_manager.debug("CONFIG", "设置已应用")

    def save_config(self):
        self.logging_manager.debug("CONFIG", "开始保存配置")
        extra_config = {}
        for panel_id, panel in self.panels.items():
            if hasattr(panel, 'collect_config'):
                extra_config[panel_id] = panel.collect_config()
                self.logging_manager.debug("CONFIG", f"  面板 {panel_id}: {len(extra_config[panel_id])} 项")
        self._save_template_images(extra_config)
        self.app_state.save_current(extra_config)
        self.logging_manager.debug("CONFIG", f"模块启用状态: {self.app_state._module_states}")
        self.logging_manager.debug("CONFIG", "配置保存完成")

    def _save_template_images(self, config):
        def _unwrap(v):
            return v.get() if hasattr(v, 'get') else v
        try:
            if not self.app_state.current:
                return
            # 后台监控 image 类型
            bg_raw = config.get("background", [])
            bg_list = bg_raw.get("groups", bg_raw) if isinstance(bg_raw, dict) else bg_raw
            for i, g in enumerate(bg_list):
                if not isinstance(g, dict) or _unwrap(g.get("type")) != "image":
                    continue
                pixmap = _unwrap(g.get("template_image"))
                self.logging_manager.debug("CONFIG", f"  后台 image 组 {i}: template_image={'有' if pixmap and hasattr(pixmap, 'save') and not pixmap.isNull() else '无'} ref={_unwrap(g.get('reference_image', ''))}")
                if pixmap and hasattr(pixmap, "save") and not pixmap.isNull():
                    path = self.app_state.save_template("background", i, pixmap)
                    self.logging_manager.debug("CONFIG", f"  已保存模板到: {path}")
                    g["reference_image"] = path
                else:
                    ref = _unwrap(g.get("reference_image", ""))
                    if not (isinstance(ref, str) and ref and os.path.exists(ref)):
                        g.pop("reference_image", None)
            # 图像检测
            img_list = config.get("image", [])
            for i, g in enumerate(img_list):
                if not isinstance(g, dict):
                    continue
                path = _unwrap(g.get("reference_image", ""))
                if path and not os.path.exists(path):
                    g.pop("reference_image", None)
        except Exception as e:
            self.logging_manager.error("CONFIG", f"保存模板图片失败: {e}")

    def closeEvent(self, event):
        self._is_closing = True
        self.logging_manager.debug("CLOSE", "窗口关闭中...")
        try:
            self.save_config()
        except Exception as e:
            self.logging_manager.error("CLOSE", f"保存配置失败: {e}")
        try:
            self.app_state.save_index(theme=ThemeManager._current)
        except Exception as e:
            self.logging_manager.error("CLOSE", f"保存索引失败: {e}")
        self._shutdown_all_modules()
        super().closeEvent(event)

    def _shutdown_all_modules(self):
        self.logging_manager.debug("CLOSE", "停止所有模块...")
        if hasattr(self, 'number_module'):
            try:
                self.number_module.stop_number_recognition()
            except Exception as e:
                self.logging_manager.error("CLOSE", f"停止 number_module 失败: {e}")
        if hasattr(self, 'timed_module'):
            try:
                self.timed_module.stop_timed_tasks()
            except Exception as e:
                self.logging_manager.error("CLOSE", f"停止 timed_module 失败: {e}")
        if hasattr(self, 'image_manager'):
            try:
                self.image_manager.stop_all_detection()
            except Exception as e:
                self.logging_manager.error("CLOSE", f"停止 image_manager 失败: {e}")
        if hasattr(self, 'color_manager'):
            try:
                self.color_manager.stop_color_recognition()
            except Exception as e:
                self.logging_manager.error("CLOSE", f"停止 color_manager 失败: {e}")
        if hasattr(self, 'ocr_module'):
            try:
                self.ocr_module.stop_monitoring()
            except Exception as e:
                self.logging_manager.error("CLOSE", f"停止 ocr_module 失败: {e}")
        if hasattr(self, 'background_manager'):
            try:
                self.background_manager.stop_all_groups()
            except Exception as e:
                self.logging_manager.error("CLOSE", f"停止 background_manager 失败: {e}")
        if hasattr(self, 'global_listener') and self.global_listener:
            try:
                self.global_listener.stop()
                if hasattr(self.global_listener, 'join'):
                    self.global_listener.join(timeout=2)
            except Exception as e:
                self.logging_manager.error("CLOSE", f"停止 global_listener 失败: {e}")

        self.logging_manager.debug("CLOSE", "所有模块已停止")

    def run(self):
        self.logging_manager.debug("RUN", "run() 开始执行")
        QApplication.instance().installEventFilter(self)
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
        if hasattr(self, '_q_shortcuts'):
            for sc in self._q_shortcuts:
                sc.setEnabled(False)
                sc.deleteLater()
        self._q_shortcuts = []
        sc_start = QShortcut(QKeySequence(self.app_state.start_shortcut), self)
        sc_start.activated.connect(lambda: self._on_start_all() if not self._is_running else None)
        self._q_shortcuts.append(sc_start)
        sc_stop = QShortcut(QKeySequence(self.app_state.stop_shortcut), self)
        sc_stop.activated.connect(lambda: self._on_stop_all() if self._is_running else None)
        self._q_shortcuts.append(sc_stop)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("灵眸")

    if hasattr(sys, '_MEIPASS'):
        icon_path = os.path.join(sys._MEIPASS, "icon", "sightly.png")
    else:
        icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "icon", "sightly.png")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = MainWindow()
    window.run()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
