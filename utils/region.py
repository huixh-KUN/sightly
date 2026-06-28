import screeninfo

from PySide6.QtWidgets import QMessageBox
from PySide6.QtCore import QTimer, QObject, Signal


def _start_selection(app, selection_type, region_index):
    """
    通用的区域选择方法
    使用 RegionOverlay 组件替代旧的 tkinter Toplevel/Canvas 方案。
    """
    type_names = {
        "number": "数字识别区域",
        "ocr": "文字识别区域",
        "image": "图像检测区域",
        "crop": "图像裁剪区域",
        "bg_region": "后台监控区域",
        "bg_crop": "后台监控模板截图"
    }
    app.logging_manager.log_message(f"开始{type_names.get(selection_type, '')}区域选择...")
    app.is_selecting = True
    app.selection_type = selection_type

    if selection_type == "number":
        app.current_number_region_index = region_index
    elif selection_type == "ocr":
        app.current_ocr_region_index = region_index
    elif selection_type == "image":
        app.current_image_region_index = region_index
    elif selection_type == "crop":
        app.current_image_region_index = region_index
    elif selection_type == "bg_region":
        app._bg_region_group_index = region_index
    elif selection_type == "bg_crop":
        app._bg_crop_group_index = region_index

    if screeninfo is None:
        QMessageBox.critical(
            None, "错误",
            "screeninfo库未安装，无法支持多显示器选择。"
            "请运行 'pip install screeninfo' 安装该库。"
        )
        return

    from ui.components.region_overlay import RegionOverlay

    overlay = RegionOverlay(selection_type)
    overlay.region_selected.connect(
        lambda x1, y1, x2, y2: _on_region_complete(
            app, selection_type, region_index, x1, y1, x2, y2
        )
    )
    overlay.show()


def _on_region_complete(app, selection_type, region_index, x1, y1, x2, y2):
    region = (x1, y1, x2, y2)

    if abs(x2 - x1) < 10 or abs(y2 - y1) < 10:
        QMessageBox.warning(None, "警告", "选择的区域太小，请重新选择")
        app.is_selecting = False
        return

    if selection_type == 'ocr':
        if hasattr(app, 'current_ocr_region_index') and app.current_ocr_region_index is not None:
            idx = app.current_ocr_region_index
            groups = getattr(app, 'ocr_groups', [])
            if 0 <= idx < len(groups):
                groups[idx]['region'] = region
                if 'region_var' in groups[idx]:
                    groups[idx]['region_var'].set(f"{region[0]},{region[1]},{region[2]},{region[3]}")
                app.logging_manager.log_message(f"已为识别组{idx+1}选择区域: {region}")

    elif selection_type == 'image':
        if hasattr(app, 'current_image_region_index') and app.current_image_region_index is not None:
            idx = app.current_image_region_index
            groups = getattr(app, 'image_groups', [])
            if 0 <= idx < len(groups):
                groups[idx]['region'] = region
                if 'region_var' in groups[idx]:
                    groups[idx]['region_var'].set(
                        f"{region[0]},{region[1]} - {region[2]},{region[3]}"
                    )
                app.logging_manager.log_message(f"已为检测组{idx+1}选择区域: {region}")

    elif selection_type == 'crop':
        try:
            from ui.image_tab import save_cropped_image
            save_cropped_image(app, region)
        except ImportError:
            app.logging_manager.log_message("裁剪功能已迁移，请使用 TemplatePicker 组件")

    elif selection_type == 'bg_region':
        try:
            from ui.background_tab import save_bg_region
            save_bg_region(app, region)
        except ImportError:
            app.logging_manager.log_message("后台监控区域选择功能已迁移")

    elif selection_type == 'bg_crop':
        try:
            from ui.background_tab import save_bg_cropped_image
            save_bg_cropped_image(app, region)
        except ImportError:
            app.logging_manager.log_message("后台监控模板截图功能已迁移")

    elif selection_type == 'color':
        if not hasattr(app, 'color_recognition_manager'):
            from modules.color import ColorRecognitionManager
            app.color_recognition_manager = ColorRecognitionManager(app)
        app.color_recognition_manager.set_region(region)
        app.logging_manager.log_message(f"已选择颜色识别区域: {region}")

    else:
        if hasattr(app, 'region_var'):
            app.region_var.set(f"{region[0]},{region[1]},{region[2]},{region[3]}")
        app.logging_manager.log_message(f"已选择区域: {region}")

    app.is_selecting = False
