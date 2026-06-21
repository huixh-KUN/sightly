from PySide6.QtCore import QObject, Signal


class ModuleStateController(QObject):
    """Central module state manager.
    
    Decouples UI panels from backend logic.
    Panels emit signals to this controller; controller drives the backend.
    """

    module_enabled_changed = Signal(str, bool)
    start_requested = Signal(str)
    stop_requested = Signal(str)
    all_start_requested = Signal()
    all_stop_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._states = {}
        self._module_info = {}
        self._debug_logger = None

    def set_debug_logger(self, logger):
        """设置调试日志器"""
        self._debug_logger = logger

    def _debug(self, tag, message):
        """写入调试日志"""
        if self._debug_logger:
            self._debug_logger.debug(tag, message)

    def register(self, module_id, name, description="", icon=""):
        self._debug("MODULE_STATE", f"注册模块: {module_id} ({name})")
        self._module_info[module_id] = {
            "id": module_id,
            "name": name,
            "description": description,
            "icon": icon,
        }
        if module_id not in self._states:
            self._states[module_id] = False

    def set_enabled(self, module_id, enabled):
        if module_id not in self._states:
            return
        self._states[module_id] = enabled
        self._debug("MODULE_STATE", f"模块 {module_id} 状态变为: {enabled}")
        self.module_enabled_changed.emit(module_id, enabled)

    def is_enabled(self, module_id):
        return self._states.get(module_id, False)

    def enabled_modules(self):
        modules = [mid for mid, en in self._states.items() if en]
        self._debug("MODULE_STATE", f"已启用模块: {modules}")
        return modules

    def module_info(self, module_id):
        return self._module_info.get(module_id)

    @property
    def modules(self):
        return dict(self._module_info)

    def bind_switch(self, module_id, switch_button):
        self._debug("MODULE_STATE", f"绑定模块 {module_id} 的开关")
        switch_button.stateChanged.connect(
            lambda checked: self.set_enabled(module_id, checked)
        )
        self.module_enabled_changed.connect(
            lambda mid, enabled: switch_button.setChecked(enabled) if mid == module_id else None
        )

    def request_start(self, module_id):
        self._debug("MODULE_STATE", f"请求启动模块: {module_id}")
        self.start_requested.emit(module_id)

    def request_stop(self, module_id):
        self._debug("MODULE_STATE", f"请求停止模块: {module_id}")
        self.stop_requested.emit(module_id)

    def request_start_all(self):
        self._debug("MODULE_STATE", "请求启动所有模块")
        self.all_start_requested.emit()

    def request_stop_all(self):
        self._debug("MODULE_STATE", "请求停止所有模块")
        self.all_stop_requested.emit()
