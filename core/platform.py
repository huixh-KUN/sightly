import os


class PlatformAdapter:
    """Windows平台适配器"""
    def __init__(self, app):
        self.app = app
        self.platform = "Windows"
        self.app_name = "灵眸"
        self._init_adapters()

    def _init_adapters(self):
        self.input = WindowsInputAdapter(self.app)
        self.recorder = WindowsRecorderAdapter(self.app)
        self.permission = WindowsPermissionAdapter()

    def start_recording(self):
        return self.recorder.start()
    
    def check_permissions(self):
        return self.permission.check()
    
    def get_config_dir(self):
        """获取配置文件目录"""
        return os.path.join(os.environ.get("APPDATA"), self.app_name)
    
    def get_log_file_path(self):
        """获取日志文件路径"""
        project_root = os.path.abspath('.')
        return os.path.join(project_root, "logs", "sightly.log")


class WindowsInputAdapter:
    """Windows输入适配器"""
    def __init__(self, app):
        self.app = app
    
    def press_key(self, key, delay):
        self.app.input_controller.press_key(key, delay)
    
    def key_down(self, key):
        self.app.input_controller.key_down(key)
    
    def key_up(self, key):
        self.app.input_controller.key_up(key)
    
    def click(self, x, y):
        self.app.input_controller.click(x, y)


class WindowsRecorderAdapter:
    """Windows录制器适配器"""
    def __init__(self, app):
        self.app = app
    
    def start(self):
        pass


class WindowsPermissionAdapter:
    """Windows权限适配器"""
    def check(self):
        return True
