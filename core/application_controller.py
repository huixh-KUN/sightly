import os

from PySide6.QtCore import QObject, Signal, QTimer

from core.state import AppState
from core.config import ConfigManager
from core.logging import LoggingManager
from input.controller import InputController
from ui.theme import ThemeManager


class ApplicationController(QObject):
    """应用业务协调中枢，接管后端装配与模块生命周期管理。"""

    test_result_ready = Signal(str, str, str)
    test_message = Signal(str, str, str)
    test_wait_start = Signal(str)
    test_wait_end = Signal()

    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window

        self.log_file_path = os.path.abspath("logs/sightly.log")
        self.config_file_path = os.path.abspath("config/config.json")

        self.app_state = AppState(self)

        self._init_backend()

    def __getattr__(self, name):
        main_window = self.__dict__.get('main_window')
        if main_window is not None:
            try:
                return object.__getattribute__(main_window, name)
            except AttributeError:
                pass
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    @property
    def panels(self):
        return self.main_window.panels

    def _init_backend(self):
        self.logging_manager = LoggingManager(self)
        self.app_state.set_logger(self.logging_manager)
        self.logging_manager.debug("INIT", "LoggingManager 初始化完成")

        self.input_controller = InputController(self)
        self.logging_manager.debug("INIT", "InputController 初始化完成")

        self.config_manager = ConfigManager(self)
        self.logging_manager.debug("INIT", "ConfigManager 初始化完成")

        from modules.ocr import OCRManager
        from modules.timed import TimedManager
        from modules.number import NumberManager
        from modules.alarm import AlarmManager
        from modules.color import ColorRecognitionManager
        from modules.image import ImageDetectionManager
        from modules.background import BackgroundManager

        self.ocr_module = OCRManager(self)
        self.logging_manager.debug("INIT", "OCRManager 初始化完成")

        self.timed_module = TimedManager(self)
        self.logging_manager.debug("INIT", "TimedManager 初始化完成")

        self.number_module = NumberManager(self)
        self.logging_manager.debug("INIT", "NumberManager 初始化完成")

        self.alarm_module = AlarmManager(self)
        self.logging_manager.debug("INIT", "AlarmManager 初始化完成")

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

    def migrate_old_config(self):
        if self.app_state._wm.list_workspaces():
            return
        old_config = self.config_manager.read_config()
        if old_config:
            self.app_state.create_workspace("默认配置")
            self.app_state._wm.save("默认配置", old_config)
            self.app_state._load_workspace("默认配置")
            self.logging_manager.debug("CONFIG", "旧配置已迁移到默认工作空间")

    def wire_signals(self):
        self.app_state.all_start_requested.connect(self.start_all)
        self.app_state.all_stop_requested.connect(self.stop_all)
        self.app_state.record_hotkey_triggered.connect(self.on_record_hotkey)
        self.app_state.config_loaded.connect(self.on_config_loaded)
        self.app_state.workspace_changed.connect(self.on_workspace_changed)
        bg = self.panels.get('background')
        if bg:
            bg.window_selected.connect(self.on_bg_window_selected)
            bg.auto_reconnect_requested.connect(self.on_bg_auto_reconnect)
        tm = self.panels.get('timed')
        if tm:
            tm.position_selection_requested.connect(self.on_timed_position_selection)
        st = self.panels.get('settings')
        if st:
            st.config_changed.connect(self.on_settings_config_changed)
            st.shortcuts_changed.connect(self.on_settings_shortcuts_changed)
        hm = self.panels.get('home')
        if hm:
            hm.config_save_requested.connect(self.save_config)
        for panel_id in ['ocr', 'timed', 'number', 'image', 'background']:
            panel = self.panels.get(panel_id)
            if panel:
                panel.test_group_requested.connect(
                    lambda idx, pid=panel_id: self.test_group(pid, idx)
                )
        home = self.panels.get('home')
        if home and hasattr(home, 'get_toggles'):
            toggles = home.get_toggles()
            self.logging_manager.debug("INIT", f"绑定模块开关: {list(toggles.keys())}")
            for module_id, toggle in toggles.items():
                self.app_state.bind_module_switch(module_id, toggle)
        self.logging_manager.debug("INIT", "信号连接完成")

    def start_all(self):
        if self.main_window._is_running:
            self.logging_manager.debug("START", "已在运行中，忽略启动请求")
            return
        self.main_window._is_running = True
        self.logging_manager.debug("START", "start_all 开始")
        self.sync_panel_configs()
        enabled = self.app_state.enabled_modules()
        self.logging_manager.debug("START", f"已启用模块: {enabled}")
        for module_id in enabled:
            self._start_module(module_id)
        if not enabled:
            self.logging_manager.log_message("未启用任何模块，请在首页勾选")
        self._lock_panels(True)
        self.main_window._set_status("运行中", running=True)
        self.logging_manager.debug("START", "start_all 完成")

    def stop_all(self):
        if not self.main_window._is_running:
            self.logging_manager.debug("STOP", "未在运行中，忽略停止请求")
            return
        self.main_window._is_running = False
        self.logging_manager.debug("STOP", "stop_all 开始")
        for module_id in ['ocr', 'timed', 'number', 'image', 'background']:
            self._stop_module(module_id)
        self.alarm_module.play_stop_sound()
        self._lock_panels(False)
        self.main_window._set_status("空闲", running=False)
        self.logging_manager.debug("STOP", "stop_all 完成")

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

    def _start_module(self, module_id):
        module = self.modules.get(module_id)
        if module is None:
            return
        try:
            self.logging_manager.debug("MODULE", f"启动模块: {module_id}")
            module.start()
            self.logging_manager.debug("MODULE", f"模块 {module_id} 启动成功")
            self.logging_manager.log_message(f"  ✓ {module_id} 已启动")
        except Exception as e:
            self.logging_manager.debug("MODULE", f"模块 {module_id} 启动失败: {e}")
            self.logging_manager.error("MODULE", f"  ✗ {module_id} 启动失败: {e}")

    def _stop_module(self, module_id):
        module = self.modules.get(module_id)
        if module is None:
            return
        try:
            self.logging_manager.debug("MODULE", f"停止模块: {module_id}")
            module.stop()
            self.logging_manager.debug("MODULE", f"模块 {module_id} 停止成功")
        except Exception as e:
            self.logging_manager.error("MODULE", f"模块 {module_id} 停止失败: {e}")

    def start_module(self, module_name, start_func):
        start_func()

    def on_record_hotkey(self):
        pass

    def on_bg_window_selected(self, hwnd, title):
        self.background_manager.set_target_window(hwnd)

    def on_bg_auto_reconnect(self, wc, wp, wt):
        ok = self.background_manager.auto_reconnect(wc, wp, wt)
        bg = self.panels.get('background')
        if ok:
            bg.on_auto_reconnect_result(True, self.background_manager.target_hwnd, self.background_manager.target_title or "")
        else:
            bg.on_auto_reconnect_result(False, 0, "")

    def on_timed_position_selection(self, index):
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

    def test_group(self, panel_id, idx):
        if self.main_window._is_running:
            self.test_message.emit("warning", "测试", "请先停止运行再进行测试")
            return

        module = self.modules.get(panel_id)
        if module is None or not hasattr(module, 'test_group'):
            self.test_message.emit("info", "测试", "该模块暂不支持单次测试")
            return

        panel = self.panels.get(panel_id)
        if panel and hasattr(panel, 'groups_data') and idx >= len(panel.groups_data):
            self.test_message.emit("info", "测试", "组索引越界")
            return

        wait_modules = {'timed', 'image', 'ocr', 'background'}
        if panel_id in wait_modules:
            interval_key = 'interval'
            default = {'timed': 10, 'image': 5, 'ocr': 3, 'background': 3}[panel_id]
            if panel and hasattr(panel, 'groups_data') and idx < len(panel.groups_data):
                interval = float(panel.groups_data[idx].get(interval_key, default))
            else:
                interval = default

            self.test_wait_start.emit(f"等待 {interval} 秒后执行测试动作…")

            def _do_wait_test():
                self.test_wait_end.emit()
                self.sync_panel_configs()
                try:
                    result = module.test_group(idx)
                except Exception as e:
                    self.logging_manager.error("TEST", f"{panel_id} 测试失败: {e}")
                    self.test_message.emit("critical", "测试失败", str(e))
                    return
                status = self._format_test_status(result)
                self.test_result_ready.emit(panel_id, status, result.get('detail', ''))

            QTimer.singleShot(int(interval * 1000), _do_wait_test)
            return

        self.sync_panel_configs()
        try:
            result = module.test_group(idx)
        except Exception as e:
            self.logging_manager.error("TEST", f"{panel_id} 测试失败: {e}")
            self.test_message.emit("critical", "测试失败", str(e))
            return
        status = self._format_test_status(result)
        self.test_result_ready.emit(panel_id, status, result.get('detail', ''))

    def on_settings_config_changed(self, config):
        alarm = config.get("alarm", {})
        if alarm.get("sound_path"):
            self.alarm_module.sound_path = alarm["sound_path"]
        if "volume" in alarm:
            self.alarm_module.volume = alarm["volume"]
            self.alarm_module.volume_str = str(alarm["volume"])

    def on_settings_shortcuts_changed(self, start_key, stop_key):
        if start_key:
            self.app_state.start_shortcut = start_key
        if stop_key:
            self.app_state.stop_shortcut = stop_key
        self.main_window._register_shortcuts()

    def sync_panel_configs(self):
        self.logging_manager.debug("CONFIG", "开始同步面板配置")
        for panel_id, panel in self.panels.items():
            if hasattr(panel, 'collect_config'):
                config = panel.collect_config()
                size = len(config) if isinstance(config, (list, dict)) else 0
                self.logging_manager.debug("CONFIG", f"面板 {panel_id} 配置: {size} 项")
                module = self.modules.get(panel_id)
                if module:
                    module.set_config(config)
                elif panel_id == 'settings':
                    self.main_window.settings_config = config
        self.logging_manager.debug("CONFIG", "面板配置同步完成")

    def on_config_loaded(self, config):
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
                    self.apply_settings(panel_cfg)
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
        self.sync_panel_configs()

    def on_workspace_changed(self, name):
        self.logging_manager.debug("STATE", f"工作空间切换到: {name!r}")
        if self.main_window._is_running:
            self.logging_manager.log_message("切换工作空间，自动停止所有模块")
            self.stop_all()

    def apply_settings(self, settings_cfg):
        general = settings_cfg.get("general", {})
        if general.get("start_key"):
            self.app_state.start_shortcut = general["start_key"]
        if general.get("stop_key"):
            self.app_state.stop_shortcut = general["stop_key"]
        self.main_window._register_shortcuts()
        alarm = settings_cfg.get("alarm", {})
        if alarm.get("sound_path"):
            self.alarm_module.sound_path = alarm["sound_path"]
        if "volume" in alarm:
            self.alarm_module.volume = alarm["volume"]
            self.alarm_module.volume_str = str(alarm["volume"])
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
            return v
        try:
            if not self.app_state.current:
                return
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
            img_list = config.get("image", [])
            for i, g in enumerate(img_list):
                if not isinstance(g, dict):
                    continue
                path = _unwrap(g.get("reference_image", ""))
                if path and not os.path.exists(path):
                    g.pop("reference_image", None)
        except Exception as e:
            self.logging_manager.error("CONFIG", f"保存模板图片失败: {e}")

    def load_config(self, workspace_name=None):
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
            self.main_window.theme_switcher.set_theme(theme)

    def shutdown_all(self):
        self.logging_manager.debug("CLOSE", "停止所有模块...")
        for module_id in ['number', 'timed', 'image', 'color', 'ocr', 'background']:
            module = self.modules.get(module_id)
            if module:
                try:
                    module.stop()
                except Exception as e:
                    self.logging_manager.error("CLOSE", f"停止 {module_id} 失败: {e}")
        if hasattr(self.main_window, 'global_listener') and self.main_window.global_listener:
            try:
                self.main_window.global_listener.stop()
                if hasattr(self.main_window.global_listener, 'join'):
                    self.main_window.global_listener.join(timeout=2)
            except Exception as e:
                self.logging_manager.error("CLOSE", f"停止 global_listener 失败: {e}")
        self.logging_manager.debug("CLOSE", "所有模块已停止")
