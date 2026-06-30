import os
import sys

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QStackedWidget, QFrame,
    QApplication, QSizePolicy, QSpacerItem, QSpinBox,
    QStyleFactory, QMessageBox,
)
from PySide6.QtCore import Qt, QTimer, QEvent
from PySide6.QtGui import QIcon, QFont, QShortcut, QKeySequence

from core.application_controller import ApplicationController
from ui.theme import ThemeManager
from ui.components import ThemeSwitcher
from input.keyboard import setup_shortcuts
from ui.widgets import StatusIndicator, NavButton, Divider
from ui.home_panel import HomePanel
from ui.ocr_panel import OCRPanel
from ui.timed_panel import TimedPanel
from ui.number_panel import NumberPanel
from ui.image_panel import ImagePanel
from ui.background_panel import BackgroundPanel
from ui.settings_panel import SettingsPanel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("灵眸")
        self.setMinimumSize(1050, 650)
        self.resize(1050, 700)
        self.statusBar().setVisible(False)

        QApplication.instance().setStyleSheet(ThemeManager.qss())
        QApplication.instance().setStyle(QStyleFactory.create("Fusion"))

        self._is_running = False
        self._is_paused = False
        self._is_closing = False
        self._test_wait_box = None
        self.is_tesseract_available = True

        self.controller = ApplicationController(self)
        self.app_state = self.controller.app_state

        self.controller.migrate_old_config()
        self.logging_manager.debug("INIT", "MainWindow.__init__ 完成")
        self._init_ui()
        self.logging_manager.debug("INIT", "_init_ui 完成")
        self.controller.wire_signals()
        self.logging_manager.debug("INIT", "wire_signals 完成")

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

    def __getattr__(self, name):
        controller = self.__dict__.get('controller')
        if controller is not None:
            return getattr(controller, name)
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

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

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Wheel and isinstance(obj, QSpinBox):
            return True
        return super().eventFilter(obj, event)

    def _set_status(self, text, running=None):
        self.status_label.setText(text)
        if running is not None:
            self.status_dot.running = running
            self._is_running = running

    def log_message(self, message):
        self.logging_manager.log_message(message)

    def _on_theme_changed(self, mode):
        ThemeManager.switch_to(mode)
        self.theme_switcher.set_theme(mode)
        self.app_state.save_index(theme=mode)

    def closeEvent(self, event):
        self._is_closing = True
        self.logging_manager.debug("CLOSE", "窗口关闭中...")
        try:
            self.controller.save_config()
        except Exception as e:
            self.logging_manager.error("CLOSE", f"保存配置失败: {e}")
        try:
            self.app_state.save_index(theme=ThemeManager._current)
        except Exception as e:
            self.logging_manager.error("CLOSE", f"保存索引失败: {e}")
        self.controller.shutdown_all()
        super().closeEvent(event)

    def run(self):
        self.logging_manager.debug("RUN", "run() 开始执行")
        QApplication.instance().installEventFilter(self)
        self.controller.load_config()
        self.logging_manager.debug("RUN", "配置加载完成")
        self._navigate_to('home')
        self.logging_manager.debug("RUN", "导航到首页")
        self._register_shortcuts()
        self.logging_manager.debug("RUN", "快捷键注册完成")
        setup_shortcuts(self)
        self.logging_manager.debug("RUN", "全局快捷键设置完成")
        self.show()
        self.logging_manager.debug("RUN", "窗口显示完成")
        self._wire_test_signals()

    def _wire_test_signals(self):
        self.controller.test_result_ready.connect(self._on_test_result)
        self.controller.test_message.connect(self._on_test_message)
        self.controller.test_wait_start.connect(self._on_test_wait_start)
        self.controller.test_wait_end.connect(self._on_test_wait_end)

    def _on_test_result(self, panel_id, status, detail):
        QMessageBox.information(self, f"测试结果 - {panel_id}", f"{status}\n\n{detail}")

    def _on_test_message(self, msg_type, title, text):
        if msg_type == "warning":
            QMessageBox.warning(self, title, text)
        elif msg_type == "critical":
            QMessageBox.critical(self, title, text)
        else:
            QMessageBox.information(self, title, text)

    def _on_test_wait_start(self, message):
        self._test_wait_box = QMessageBox(self)
        self._test_wait_box.setWindowTitle("测试")
        self._test_wait_box.setText(message)
        self._test_wait_box.setStandardButtons(QMessageBox.NoButton)
        self._test_wait_box.show()

    def _on_test_wait_end(self):
        if self._test_wait_box:
            self._test_wait_box.close()
            self._test_wait_box.deleteLater()
            self._test_wait_box = None

    def _register_shortcuts(self):
        if hasattr(self, '_q_shortcuts'):
            for sc in self._q_shortcuts:
                sc.setEnabled(False)
                sc.deleteLater()
        self._q_shortcuts = []
        sc_start = QShortcut(QKeySequence(self.app_state.start_shortcut), self)
        sc_start.activated.connect(lambda: self.controller.start_all() if not self._is_running else None)
        self._q_shortcuts.append(sc_start)
        sc_stop = QShortcut(QKeySequence(self.app_state.stop_shortcut), self)
        sc_stop.activated.connect(lambda: self.controller.stop_all() if self._is_running else None)
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
