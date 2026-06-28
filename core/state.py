import json
import os

from PySide6.QtCore import QObject, Signal

from core.workspace import WorkspaceManager


def _tuples_to_lists(obj):
    if isinstance(obj, dict):
        return {k: _tuples_to_lists(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_tuples_to_lists(v) for v in obj]
    elif isinstance(obj, tuple):
        return list(obj)
    return obj


class AppState(QObject):
    """集中应用状态管理器。

    所有运行时状态在此统一管理，组件通过属性和信号通信。
    持久化统一由本类在启动时读取、关闭时写入。
    """

    module_enabled_changed = Signal(str, bool)
    start_requested = Signal(str)
    stop_requested = Signal(str)
    all_start_requested = Signal()
    all_stop_requested = Signal()

    workspace_changed = Signal(str)

    config_loaded = Signal(dict)
    record_hotkey_triggered = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._wm = WorkspaceManager()
        self._logger = None

        self._current = None
        self._config = {}
        self._module_states = {}
        self._module_info = {}

        self.start_shortcut = "F10"
        self.stop_shortcut = "F12"
        self.record_hotkey = "F11"

    def set_logger(self, logger):
        self._logger = logger

    def _log(self, tag, message):
        if self._logger:
            self._logger.debug(tag, message)

    # ========== 工作空间 ==========

    @property
    def current(self):
        return self._current

    @property
    def workspace_list(self):
        return self._wm.list_workspaces()

    def switch_workspace(self, name):
        self._log("STATE", f"switch_workspace({name!r}), current={self._current!r}")
        if name == self._current or not name:
            self._log("STATE", f"跳过：name={name!r}, current={self._current!r}")
            return
        self._current = name
        self._load_workspace(name)

    def create_workspace(self, name):
        self._log("STATE", f"create_workspace({name!r})")
        self._wm.create_workspace(name)
        self._current = name
        self._apply_empty_config()

    def delete_workspace(self, name):
        self._log("STATE", f"delete_workspace({name!r})")
        self._wm.delete_workspace(name)
        if self._current == name:
            ws_list = self.workspace_list
            if ws_list:
                self._load_workspace(ws_list[0])
            else:
                self._current = None
                self._apply_empty_config()

    def _load_workspace(self, name):
        self._log("STATE", f"_load_workspace({name!r})")
        config = self._wm.load(name)
        self._log("STATE", f"加载配置: {json.dumps(config, ensure_ascii=False)[:200]}")
        self._config = config
        self._current = name
        self._apply_module_states(config)
        self._log("STATE", "发出 config_loaded / workspace_changed")
        self.config_loaded.emit(config)
        self.workspace_changed.emit(name)

    def _apply_empty_config(self):
        self._log("STATE", f"_apply_empty_config, current={self._current!r}")
        self._config = {}
        for mid in self._module_states:
            self._module_states[mid] = False
            self.module_enabled_changed.emit(mid, False)
        self._log("STATE", f"发出 config_loaded({{}}) / workspace_changed({self._current!r})")
        self.config_loaded.emit({})
        self.workspace_changed.emit(self._current)

    # ========== 模块状态 ==========

    def register_module(self, module_id, name, description="", icon=""):
        self._module_info[module_id] = {
            "id": module_id,
            "name": name,
            "description": description,
            "icon": icon,
        }
        if module_id not in self._module_states:
            self._module_states[module_id] = False

    def set_module_enabled(self, module_id, enabled):
        if module_id not in self._module_states:
            return
        self._module_states[module_id] = enabled
        self.module_enabled_changed.emit(module_id, enabled)

    def is_module_enabled(self, module_id):
        return self._module_states.get(module_id, False)

    def enabled_modules(self):
        return [mid for mid, en in self._module_states.items() if en]

    @property
    def modules(self):
        return dict(self._module_info)

    def bind_module_switch(self, module_id, switch_button):
        switch_button.stateChanged.connect(
            lambda checked: self.set_module_enabled(module_id, checked)
        )
        self.module_enabled_changed.connect(
            lambda mid, enabled: switch_button.setChecked(enabled) if mid == module_id else None
        )

    def request_start(self, module_id):
        self.start_requested.emit(module_id)

    def request_stop(self, module_id):
        self.stop_requested.emit(module_id)

    def request_start_all(self):
        self.all_start_requested.emit()

    def request_stop_all(self):
        self.all_stop_requested.emit()

    # ========== 面板配置收集/应用 ==========

    def collect_module_enabled_config(self):
        return {mid: self._module_states.get(mid, False) for mid in self._module_info}

    def get_panel_config(self, panel_id):
        return self._config.get(panel_id)

    def _apply_module_states(self, config):
        me = config.get("module_enabled", {})
        for mid in self._module_info:
            enabled = me.get(mid, False)
            if self._module_states.get(mid) != enabled:
                self._module_states[mid] = enabled
                self.module_enabled_changed.emit(mid, enabled)

    # ========== 模板持久化 ==========

    def save_template(self, panel_id: str, group_index: int, pixmap_or_path) -> str | None:
        """保存模板图片到工作空间

        Args:
            panel_id: 面板标识（如 'image', 'background'）
            group_index: 组索引（从0开始）
            pixmap_or_path: QPixmap 或文件路径

        Returns:
            保存后的文件路径，失败返回 None
        """
        if not self._current:
            return None
        return self._wm.save_template_image(self._current, panel_id, group_index, pixmap_or_path)

    def get_template_path(self, panel_id: str, group_index: int) -> str | None:
        """获取工作空间中模板图片的路径

        Args:
            panel_id: 面板标识
            group_index: 组索引

        Returns:
            模板文件路径（存在时），否则 None
        """
        if not self._current:
            return None
        return self._wm.get_template_path(self._current, panel_id, group_index)

    # ========== 持久化 ==========

    def _index_path(self):
        return os.path.join(self._wm.base_dir, "index.json")

    def load_index(self):
        path = self._index_path()
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get("last_workspace"), data.get("theme", "dark")
        return None, "dark"

    def save_index(self, theme=None):
        path = self._index_path()
        data = {}
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        data["last_workspace"] = self._current
        if theme:
            data["theme"] = theme
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def save_current(self, extra_config=None):
        self._log("STATE", f"save_current, current={self._current!r}")
        if not self._current:
            self._log("STATE", "save_current: 无当前工作空间，跳过")
            return False
        config = {}
        config["module_enabled"] = self.collect_module_enabled_config()
        if extra_config:
            config.update(extra_config)
        # 转换 tuple 为 list（JSON 序列化需要）
        config = _tuples_to_lists(config)
        self._log("STATE", f"写入配置: {json.dumps(config, ensure_ascii=False)[:200]}")
        return self._wm.save(self._current, config)

    def startup_load(self):
        name, theme = self.load_index()
        self._log("STATE", f"startup_load, index_name={name!r}")
        if name:
            ws_list = self.workspace_list
            self._log("STATE", f"可用工作空间: {ws_list}")
            if name in ws_list:
                self._load_workspace(name)
                return name, theme
            if ws_list:
                self._load_workspace(ws_list[0])
                return ws_list[0], theme
        else:
            ws_list = self.workspace_list
            self._log("STATE", f"无 index, 可用工作空间: {ws_list}")
            if ws_list:
                self._load_workspace(ws_list[0])
                return ws_list[0], theme
        self._log("STATE", "无可用工作空间")
        return None, "dark"
