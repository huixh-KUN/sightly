"""
模块控制器，负责统一管理各功能模块的启动和停止
（PySide6 迁移后仅用于旧版 autodoor.py 兼容路径）
"""


class ModuleController:
    """模块控制器类"""
    
    def __init__(self, app):
        """
        初始化模块控制器
        Args:
            app: 主应用实例
        """
        self.app = app
    
    def start_module(self, module_name, start_func):
        """统一启动模块
        Args:
            module_name: 模块名称
            start_func: 启动函数
        """
        if module_name in self.app.MODULES:
            config = self.app.MODULES[module_name]
            stop_func_path = config["stop_func"]
            parts = stop_func_path.split(".")
            obj = self.app
            for part in parts:
                obj = getattr(obj, part)
            stop_func = obj
            label = config["label"]
            self.app.thread_manager.start(module_name, start_func, stop_func, label)
        else:
            self.app.logging_manager.log_message(f"未知模块: {module_name}")

    @staticmethod
    def _get_check_var(var):
        """统一获取变量值，兼容 tk.BooleanVar / ConfigVar / bool"""
        return var.get() if hasattr(var, 'get') else bool(var)

    def _update_indicator(self, module_key, is_running):
        """更新模块指示灯状态"""
        if hasattr(self.app, 'module_indicators') and module_key in self.app.module_indicators:
            color = '#00e676' if is_running else '#9CA3AF'
            try:
                self.app.module_indicators[module_key].configure(text_color=color)
            except Exception:
                pass

    def start_all(self):
        """开始运行"""
        self.app.logging_manager.log_message("开始运行")

        self.app.system_stopped = False

        if hasattr(self.app, 'module_switches'):
            for switch in self.app.module_switches.values():
                try:
                    switch.configure(state="disabled")
                except Exception:
                    pass

        try:
            self.app.global_start_btn.configure(state="disabled")
        except Exception:
            pass

        try:
            self.app.global_stop_btn.configure(state="normal")
        except Exception:
            pass
        
        self._toggle_all_ui_state("disabled")

        check_vars = getattr(self.app, 'module_check_vars', {})

        if self._get_check_var(check_vars.get("ocr", False)):
            self.app.ocr.start_monitoring()
            self._update_indicator("ocr", True)

        if self._get_check_var(check_vars.get("timed", False)):
            self.app.timed_module.start_timed_tasks()
            self._update_indicator("timed", True)

        if self._get_check_var(check_vars.get("number", False)):
            self.app.number_module.start_number_recognition()
            self._update_indicator("number", True)

        if self._get_check_var(check_vars.get("image", False)):
            self.app.image_detection_manager.start_all_detection()
            self._update_indicator("image", True)

        if self._get_check_var(check_vars.get("script", False)):
            self.app.script.start()
            self._update_indicator("script", True)

        if self._get_check_var(check_vars.get("background", False)):
            self.app.background_manager.start_all_groups()
            self._update_indicator("background", True)

        self.app.alarm_module.play_start_sound()
        
        self.app.is_running = True

    def stop_all(self):
        """停止运行"""
        self.app.logging_manager.log_message("停止运行")

        self.app.system_stopped = True

        self.app.ocr.stop_monitoring()
        self._update_indicator("ocr", False)

        self.app.timed_module.stop_timed_tasks()
        self._update_indicator("timed", False)

        self.app.number_module.stop_number_recognition()
        self._update_indicator("number", False)
        
        self.app.image_detection_manager.stop_all_detection()
        self._update_indicator("image", False)
        
        self.app.script.stop(stop_color_recognition=False)
        self._update_indicator("script", False)
        
        if hasattr(self.app, 'background_manager'):
            self.app.background_manager.stop_all_groups()
            self._update_indicator("background", False)
        
        if hasattr(self.app, 'color_recognition_manager') and hasattr(self.app.color_recognition_manager, 'color_recognition'):
            cr = self.app.color_recognition_manager.color_recognition
            if cr and hasattr(cr, 'is_running') and cr.is_running:
                cr.stop_recognition()
            elif cr and hasattr(cr, 'recognition_thread') and cr.recognition_thread is not None and cr.recognition_thread.is_alive():
                cr.is_running = False
                cr.recognition_thread.join(timeout=2)

        self.app.event_manager.clear_events()

        self.app.alarm_module.play_stop_sound()

        if hasattr(self.app, 'module_switches'):
            for switch in self.app.module_switches.values():
                try:
                    switch.configure(state="normal")
                except Exception:
                    pass

        try:
            self.app.global_start_btn.configure(state="normal")
        except Exception:
            pass

        try:
            self.app.global_stop_btn.configure(state="disabled")
        except Exception:
            pass
        
        self._toggle_all_ui_state("normal")
        
        self.app.is_running = False
    
    def _toggle_all_ui_state(self, state):
        root = getattr(self.app, 'root', None)
        if root is None:
            return
        try:
            for child in root.winfo_children():
                self._toggle_widget_state(child, state)
        except Exception:
            pass
    
    def _toggle_widget_state(self, widget, state):
        stop_btn = getattr(self.app, 'global_stop_btn', None)
        start_btn = getattr(self.app, 'global_start_btn', None)
        indicators = getattr(self.app, 'module_indicators', {})
        
        if widget in (stop_btn, start_btn):
            return
        
        for indicator in indicators.values():
            if widget == indicator:
                return
        
        if hasattr(self.app, 'script_tabview') and widget == self.app.script_tabview:
            return
        
        try:
            widget.configure(state=state)
        except Exception:
            pass
        
        try:
            for child in widget.winfo_children():
                self._toggle_widget_state(child, state)
        except Exception:
            pass
