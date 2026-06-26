from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt


class ConfirmDialog(QDialog):
    def __init__(self, title="确认", message="确定执行此操作？",
                 confirm_text="确定", cancel_text="取消", parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(360, 160)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(16)

        msg_label = QLabel(message)
        msg_label.setWordWrap(True)
        msg_label.setObjectName("confirmMessage")
        layout.addWidget(msg_label)

        layout.addStretch()

        btn_row = QHBoxLayout()
        btn_row.setSpacing(12)
        btn_row.addStretch()

        cancel_btn = QPushButton(cancel_text)
        cancel_btn.setObjectName("textBtn")
        cancel_btn.setFixedWidth(80)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        confirm_btn = QPushButton(confirm_text)
        confirm_btn.setObjectName("primary")
        confirm_btn.setFixedWidth(80)
        confirm_btn.setDefault(True)
        confirm_btn.clicked.connect(self.accept)
        btn_row.addWidget(confirm_btn)

        layout.addLayout(btn_row)
