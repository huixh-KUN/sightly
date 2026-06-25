from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QFrame, QGridLayout, QScrollArea,
    QInputDialog, QMessageBox
)
from PySide6.QtCore import Qt

from ui.widgets import SectionTitle, PrimaryButton, InfoLabel, TextButton
from ui.components import LogViewer, ModuleCard, ComboBox


class HomePanel(QWidget):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.app = app
        self.app_state = app.app_state
        self._cards = {}
        self._ws_switching = False
        self._setup_ui()
        self._connect_signals()

    def _connect_signals(self):
        self.app_state.module_enabled_changed.connect(self._on_module_state)
        self.start_btn.clicked.connect(self.app_state.request_start_all)
        self.stop_btn.clicked.connect(self.app_state.request_stop_all)
        self.app.logging_manager.log_callback = self.log_viewer.log
        self.app.logging_manager.error_callback = self.log_viewer.log_error
        self.app.logging_manager.clear_callback = self.log_viewer.clear
        buffer = list(self.app.logging_manager._log_buffer)
        if buffer:
            self.log_viewer.append_batch([line.rstrip('\n') for line in buffer])
        self.ws_combo.currentTextChanged.connect(self._on_ws_selected)
        self.app.logging_manager.debug("HOME", "HomePanel 信号连接完成")

    def _on_module_state(self, module_id, enabled):
        if module_id in self._cards:
            self._cards[module_id].set_status(enabled)

    def get_toggles(self):
        return {mid: card._toggle for mid, card in self._cards.items()}

    def set_toggles_enabled(self, enabled):
        for card in self._cards.values():
            card._toggle.setEnabled(enabled)

    def _setup_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(32, 28, 32, 28)
        layout.setSpacing(16)

        header = QVBoxLayout()
        header.setSpacing(4)
        header.addWidget(SectionTitle("首页"))
        layout.addLayout(header)

        controls = QFrame()
        controls.setObjectName("card")
        c_layout = QHBoxLayout(controls)
        c_layout.setContentsMargins(24, 16, 24, 16)
        c_layout.setSpacing(16)

        info_col = QVBoxLayout()
        info_col.setSpacing(2)
        info_col.addWidget(QLabel("运行控制"))
        info_col.addWidget(InfoLabel("勾选模块 → 点击「全部启动」"))
        c_layout.addLayout(info_col)
        c_layout.addStretch()

        self.start_btn = PrimaryButton("▶  全部启动")
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.setFixedHeight(36)
        self.start_btn.setMinimumWidth(130)
        c_layout.addWidget(self.start_btn)

        self.stop_btn = PrimaryButton("⏹  全部停止")
        self.stop_btn.setCursor(Qt.PointingHandCursor)
        self.stop_btn.setFixedHeight(36)
        self.stop_btn.setMinimumWidth(130)
        c_layout.addWidget(self.stop_btn)

        layout.addWidget(controls)

        ws_card = QFrame()
        ws_card.setObjectName("card")
        ws_layout = QHBoxLayout(ws_card)
        ws_layout.setContentsMargins(24, 12, 24, 12)
        ws_layout.setSpacing(12)

        ws_layout.addWidget(QLabel("工作空间"))
        self.ws_combo = ComboBox()
        self._refresh_ws_list()
        ws_layout.addWidget(self.ws_combo, 1)

        new_ws_btn = TextButton("新建")
        new_ws_btn.clicked.connect(self._create_workspace)
        ws_layout.addWidget(new_ws_btn)
        del_ws_btn = TextButton("删除")
        del_ws_btn.clicked.connect(self._delete_workspace)
        ws_layout.addWidget(del_ws_btn)
        layout.addWidget(ws_card)

        modules = QFrame()
        modules.setObjectName("card")
        m_layout = QVBoxLayout(modules)
        m_layout.setContentsMargins(16, 12, 16, 16)
        m_layout.setSpacing(10)

        m_header = QLabel("功能模块")
        m_header.setObjectName("cardTitle")
        m_layout.addWidget(m_header)

        module_list = [
            ("ocr", "📝", "文字识别", "监控屏幕文字，匹配关键词触发"),
            ("timed", "⏱", "定时功能", "按设定间隔自动执行按键操作"),
            ("number", "🔢", "数字识别", "识别屏幕数字变化触发动作"),
            ("image", "🖼️", "图像检测", "检测屏幕图像匹配模板触发"),
            ("background", "🖥️", "后台监控", "监控指定窗口的内容变化"),
            ("script", "📜", "脚本运行", "录制和执行按键脚本"),
        ]

        grid = QGridLayout()
        grid.setSpacing(8)

        for idx, (key, icon, name, desc) in enumerate(module_list):
            card = ModuleCard(icon, name, desc)
            grid.addWidget(card, idx // 2, idx % 2)
            self._cards[key] = card

        m_layout.addLayout(grid)
        layout.addWidget(modules)

        log_card = QFrame()
        log_card.setObjectName("card")
        l_layout = QVBoxLayout(log_card)
        l_layout.setContentsMargins(16, 12, 16, 16)
        l_layout.setSpacing(8)

        l_header = QHBoxLayout()
        l_header.addWidget(QLabel("运行日志"))
        l_header.addStretch()
        clear_btn = TextButton("清除")
        clear_btn.clicked.connect(self._clear_log)
        l_header.addWidget(clear_btn)
        l_layout.addLayout(l_header)

        self.log_viewer = LogViewer()
        self.log_viewer.setMinimumHeight(120)
        l_layout.addWidget(self.log_viewer, 1)

        layout.addWidget(log_card)
        layout.addStretch()

        scroll.setWidget(container)
        outer.addWidget(scroll)

    def _refresh_ws_list(self):
        self._ws_switching = True
        current = self.app_state.current
        self.ws_combo.clear()
        self.ws_combo.addItems(self.app_state.workspace_list)
        if current:
            idx = self.ws_combo.findText(current)
            if idx >= 0:
                self.ws_combo.setCurrentIndex(idx)
        self._ws_switching = False

    
    def _create_workspace(self):
        name, ok = QInputDialog.getText(self, "新建工作空间", "工作空间名称:")
        if ok and name.strip():
            self.app.logging_manager.debug("HOME", f"_create_workspace({name.strip()!r})")
            self.app_state.create_workspace(name.strip())
            self._refresh_ws_list()
            self.app.logging_manager.log_message(f"已创建并切换到工作空间: {name.strip()}")

    def _delete_workspace(self):
        name = self.ws_combo.currentText()
        if not name:
            return
        if len(self.app_state.workspace_list) <= 1:
            self.app.logging_manager.log_message("至少保留一个工作空间")
            return
        ret = QMessageBox.question(
            self, "确认删除",
            f"确定要删除工作空间「{name}」吗？\n该操作不可恢复。",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if ret != QMessageBox.Yes:
            return
        self.app.logging_manager.debug("HOME", f"_delete_workspace({name!r})")
        self.app_state.delete_workspace(name)
        self._refresh_ws_list()
        self.app.logging_manager.log_message(f"已删除工作空间: {name}")

    def _on_ws_selected(self, name):
        if self._ws_switching or not name:
            return
        if self.app_state.current == name:
            return
        self.app.logging_manager.debug("HOME", f"_on_ws_selected: {self.app_state.current!r} -> {name!r}")
        self.app.save_config()
        self.app_state.switch_workspace(name)
        self.app.logging_manager.log_message(f"已切换到工作空间: {name}")

    def _clear_log(self):
        self.app.logging_manager.debug("HOME", "清除日志")
        self.app.logging_manager.clear_log()
