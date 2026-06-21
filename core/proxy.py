"""
代理类模块，按功能分组管理代理方法
(迁移到 PySide6 后，多数方法保留为桩函数以保持兼容)
"""


class OCRProxy:
    """OCR功能代理类"""
    
    def __init__(self, app):
        self.app = app
    
    def create_tab(self, parent):
        self.app.logging_manager.log_message("[DEPRECATED] OCRProxy.create_tab")
    
    def create_group(self, index):
        self.app.logging_manager.log_message("[DEPRECATED] OCRProxy.create_group")
    
    def add_group(self):
        self.app.logging_manager.log_message("[DEPRECATED] OCRProxy.add_group")
    
    def delete_group(self, index, confirm=True):
        self.app.logging_manager.log_message("[DEPRECATED] OCRProxy.delete_group")
    
    def renumber_groups(self):
        self.app.logging_manager.log_message("[DEPRECATED] OCRProxy.renumber_groups")
    
    def start_region_selection(self, index):
        self.app.logging_manager.log_message("[DEPRECATED] OCRProxy.start_region_selection")
    
    def start_monitoring(self):
        """开始监控"""
        self.app.ocr_module.start_monitoring()
    
    def stop_monitoring(self):
        """停止监控"""
        self.app.ocr_module.stop_monitoring()


class TimedProxy:
    """定时功能代理类"""
    
    def __init__(self, app):
        self.app = app
    
    def create_tab(self, parent):
        self.app.logging_manager.log_message("[DEPRECATED] TimedProxy.create_tab")
    
    def create_group(self, index):
        self.app.logging_manager.log_message("[DEPRECATED] TimedProxy.create_group")
    
    def add_group(self):
        self.app.logging_manager.log_message("[DEPRECATED] TimedProxy.add_group")
    
    def delete_group(self, index, confirm=True):
        self.app.logging_manager.log_message("[DEPRECATED] TimedProxy.delete_group")
    
    def renumber_groups(self):
        self.app.logging_manager.log_message("[DEPRECATED] TimedProxy.renumber_groups")
    
    def start_tasks(self):
        """启动定时任务"""
        self.app.timed_module.start_timed_tasks()
    
    def stop_tasks(self):
        """停止定时功能"""
        self.app.timed_module.stop_timed_tasks()


class NumberProxy:
    """数字识别代理类"""
    
    def __init__(self, app):
        self.app = app
    
    def create_tab(self, parent):
        self.app.logging_manager.log_message("[DEPRECATED] NumberProxy.create_tab")
    
    def create_region(self, index):
        self.app.logging_manager.log_message("[DEPRECATED] NumberProxy.create_region")
    
    def add_region(self):
        self.app.logging_manager.log_message("[DEPRECATED] NumberProxy.add_region")
    
    def delete_region(self, index, confirm=True):
        self.app.logging_manager.log_message("[DEPRECATED] NumberProxy.delete_region")
    
    def renumber_regions(self):
        self.app.logging_manager.log_message("[DEPRECATED] NumberProxy.renumber_regions")
    
    def start_region_selection(self, region_index):
        self.app.logging_manager.log_message("[DEPRECATED] NumberProxy.start_region_selection")
    
    def start_recognition(self):
        """开始数字识别"""
        self.app.number_module.start_number_recognition()
    
    def stop_recognition(self):
        """停止数字识别"""
        self.app.number_module.stop_number_recognition()


class ScriptProxy:
    """脚本功能代理类"""
    
    def __init__(self, app):
        self.app = app
    
    def create_tab(self, parent):
        self.app.logging_manager.log_message("[DEPRECATED] ScriptProxy.create_tab")
    
    def start(self, start_color_recognition=True):
        """启动脚本"""
        self.app.script_module.start_script(start_color_recognition)
    
    def stop(self, stop_color_recognition=True):
        """停止脚本执行"""
        self.app.script_module.stop_script(stop_color_recognition)
    
    def start_recording(self):
        """开始录制脚本"""
        self.app.script_module.start_recording()
    
    def stop_recording(self):
        """停止录制脚本"""
        self.app.script_module.stop_recording()


class ColorProxy:
    """颜色识别代理类"""
    
    def __init__(self, app):
        self.app = app
    
    def select_region(self):
        """选择颜色识别区域"""
        self.app.color_recognition_manager.select_color_region()
    
    def select_color(self):
        """选择颜色"""
        self.app.color_recognition_manager.select_color()
    
    def start_recognition(self):
        """开始颜色识别"""
        self.app.color_recognition_manager.start_color_recognition()
    
    def stop_recognition(self):
        """停止颜色识别"""
        self.app.color_recognition_manager.stop_color_recognition()


class ImageDetectionProxy:
    """图像检测代理类"""
    
    def __init__(self, app):
        self.app = app
    
    def create_tab(self, parent):
        self.app.logging_manager.log_message("[DEPRECATED] ImageDetectionProxy.create_tab")
    
    def create_group(self, index):
        self.app.logging_manager.log_message("[DEPRECATED] ImageDetectionProxy.create_group")
    
    def add_group(self):
        self.app.logging_manager.log_message("[DEPRECATED] ImageDetectionProxy.add_group")
    
    def delete_group(self, index, confirm=True):
        self.app.logging_manager.log_message("[DEPRECATED] ImageDetectionProxy.delete_group")
    
    def renumber_groups(self):
        self.app.logging_manager.log_message("[DEPRECATED] ImageDetectionProxy.renumber_groups")
    
    def start_region_selection(self, index):
        self.app.logging_manager.log_message("[DEPRECATED] ImageDetectionProxy.start_region_selection")
    
    def select_reference_image(self, index):
        self.app.logging_manager.log_message("[DEPRECATED] ImageDetectionProxy.select_reference_image")
    
    def start_detection(self):
        """开始图像检测"""
        self.app.image_detection_manager.start_all_detection()
    
    def stop_detection(self):
        """停止图像检测"""
        self.app.image_detection_manager.stop_all_detection()


class UIProxy:
    """UI工具代理类"""
    
    def __init__(self, app):
        self.app = app
    
    def create_home_tab(self, parent):
        self.app.logging_manager.log_message("[DEPRECATED] UIProxy.create_home_tab")
    
    def create_basic_tab(self, parent):
        self.app.logging_manager.log_message("[DEPRECATED] UIProxy.create_basic_tab")
    
    def show_message(self, title, message):
        try:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.information(None, title, message)
        except ImportError:
            pass
    
    def show_progress(self, message):
        if hasattr(self.app, 'status_var'):
            self.app.status_var.set(message)
        if hasattr(self.app, 'root') and self.app.root:
            try:
                self.app.root.update_idletasks()
            except Exception:
                pass
    
    def hide_progress(self):
        if hasattr(self.app, 'status_var'):
            self.app.status_var.set("")
        if hasattr(self.app, 'root') and self.app.root:
            try:
                self.app.root.update_idletasks()
            except Exception:
                pass


class BackgroundProxy:
    """后台监控代理类"""
    
    def __init__(self, app):
        self.app = app
    
    def create_tab(self, parent):
        self.app.logging_manager.log_message("[DEPRECATED] BackgroundProxy.create_tab")
    
    def create_group(self, index, monitor_type="ocr"):
        self.app.logging_manager.log_message("[DEPRECATED] BackgroundProxy.create_group")
    
    def add_group(self, monitor_type="ocr"):
        self.app.logging_manager.log_message("[DEPRECATED] BackgroundProxy.add_group")
    
    def delete_group(self, index, confirm=True):
        self.app.logging_manager.log_message("[DEPRECATED] BackgroundProxy.delete_group")
    
    def start_region_selection(self, index):
        self.app.logging_manager.log_message("[DEPRECATED] BackgroundProxy.start_region_selection")
    
    def select_template_image(self, index):
        self.app.logging_manager.log_message("[DEPRECATED] BackgroundProxy.select_template_image")
    
    def select_color(self, index):
        self.app.logging_manager.log_message("[DEPRECATED] BackgroundProxy.select_color")
    
    def find_window(self):
        self.app.logging_manager.log_message("[DEPRECATED] BackgroundProxy.find_window")
    
    def start_monitoring(self):
        """开始后台监控"""
        self.app.background_manager.start_all_groups()
    
    def stop_monitoring(self):
        """停止后台监控"""
        self.app.background_manager.stop_all_groups()
