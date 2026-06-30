import json
import os


def safe_group_get(group, key, default):
    return group.get(key, default)

class ConfigManager:
    """统一配置管理器类"""

    def __init__(self, controller):
        self.controller = controller
        self.config_file_path = controller.config_file_path

    def read_config(self):
        if not os.path.exists(self.config_file_path):
            return None
        try:
            with open(self.config_file_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            self.controller.logging_manager.log_message(f"开始加载配置: {self.config_file_path}")
            self.controller.logging_manager.debug("CONFIG", f"配置文件读取成功: {self.config_file_path}")
            return config
        except json.JSONDecodeError as e:
            self.controller.logging_manager.error("CONFIG", f"配置文件格式错误: {self.config_file_path}，错误详情: {str(e)}")
        except PermissionError:
            self.controller.logging_manager.error("CONFIG", f"没有权限读取配置文件: {self.config_file_path}")
        except IOError as e:
            self.controller.logging_manager.error("CONFIG", f"配置文件IO错误: {str(e)}")
        except Exception as e:
            self.controller.logging_manager.error("CONFIG", f"配置加载错误: {str(e)}")
        return None
