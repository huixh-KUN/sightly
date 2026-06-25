from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QFormLayout


class ConfigCard(QFrame):
    LABEL_WIDTH = 70

    def __init__(self, icon="", title="", header_widget=None, parent=None):
        super().__init__(parent)
        self.setObjectName("configCard")
        self.setStyleSheet("""
            #configCard { background-color: #1E1E1E; border: 1px solid #3C4043; border-radius: 10px; }
            #cardHeader { font-size: 14px; font-weight: 500; color: #E8EAED; }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(0)

        header = QHBoxLayout()
        self._title_label = QLabel(f"{icon} {title}")
        self._title_label.setObjectName("cardHeader")
        header.addWidget(self._title_label)
        header.addStretch()
        if header_widget:
            header.addWidget(header_widget)
        layout.addLayout(header)

        self._content_layout = QVBoxLayout()
        self._content_layout.setContentsMargins(0, 6, 0, 0)
        self._content_layout.setSpacing(8)
        layout.addLayout(self._content_layout)

        self._form = QFormLayout()
        self._form.setContentsMargins(0, 0, 0, 0)
        self._form.setSpacing(8)
        self._form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._content_layout.addLayout(self._form)

    def set_content(self, widget):
        self._content_layout.addWidget(widget)

    def add_layout(self, layout):
        self._content_layout.addLayout(layout)

    def add_row(self, label, widget):
        lbl = QLabel(label)
        lbl.setFixedWidth(self.LABEL_WIDTH)
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self._form.addRow(lbl, widget)

    def add_widget_row(self, widget):
        self._form.addRow(widget)
