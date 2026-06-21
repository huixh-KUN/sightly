def update_group_style(group_frame, enabled):
    """This is called from core/config.py. In PySide6, styling is handled by widgets."""
    pass


def update_image_preview(*args, **kwargs):
    pass


def select_template_image(*args, **kwargs):
    pass


def save_cropped_template(*args, **kwargs):
    pass


def get_app_dir():
    import os, sys
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
