from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget, QLayout,
)


class ConfigCard(QFrame):
    """配置卡片：固定宽左标签列，多字段同行，标签纵向对齐。"""

    LABEL_WIDTH = 72
    INLINE_LABEL_WIDTH = 56
    SEGMENT_SPACING = 12

    def __init__(self, icon="", title="", header_widget=None, parent=None):
        super().__init__(parent)
        self.setObjectName("configCard")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(0)

        header = QHBoxLayout()
        title_label = QLabel(f"{icon} {title}")
        title_label.setObjectName("cardHeader")
        header.addWidget(title_label)
        header.addStretch()
        if header_widget:
            header.addWidget(header_widget)
        layout.addLayout(header)

        self._content_layout = QVBoxLayout()
        self._content_layout.setContentsMargins(0, 10, 0, 0)
        self._content_layout.setSpacing(10)
        layout.addLayout(self._content_layout)

        self._rows = QVBoxLayout()
        self._rows.setContentsMargins(0, 0, 0, 0)
        self._rows.setSpacing(10)
        self._content_layout.addLayout(self._rows)

    def set_content(self, widget):
        self._content_layout.addWidget(widget)

    def _make_label(self, text, width=None, object_name="rowLabel"):
        lbl = QLabel(text)
        lbl.setFixedWidth(width if width is not None else self.LABEL_WIDTH)
        lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        lbl.setObjectName(object_name)
        return lbl

    def _make_row(self):
        row = QWidget()
        row.setObjectName("configCardRow")
        row.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        lay = QHBoxLayout(row)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(8)
        return row, lay

    def add_row(self, label, widget, stretch=0):
        """单行：左标签 + 单个控件。"""
        row, lay = self._make_row()
        lay.addWidget(self._make_label(label))
        lay.addWidget(widget, stretch)
        if stretch == 0:
            lay.addStretch(1)
        self._rows.addWidget(row)

    def add_segments_row(self, main_label, *segments: tuple[str, QWidget]):
        """一行多组：主标签列 + 若干 (子标签, 控件)。子标签为空则只放控件。"""
        row, lay = self._make_row()
        lay.addWidget(self._make_label(main_label))
        for i, (seg_label, widget) in enumerate(segments):
            if i > 0:
                lay.addSpacing(self.SEGMENT_SPACING)
            if seg_label:
                lay.addWidget(
                    self._make_label(seg_label, self.INLINE_LABEL_WIDTH, "inlineFieldLabel")
                )
            lay.addWidget(widget, 0)
        lay.addStretch(1)
        self._rows.addWidget(row)

    def add_action_row(self, label, *widgets):
        """操作行：左标签 + 若干控件，首个可伸展，按钮不被挤出。"""
        row, lay = self._make_row()
        lay.addWidget(self._make_label(label))
        for i, widget in enumerate(widgets):
            if i == 0 and len(widgets) > 1:
                widget.setMinimumWidth(0)
                lay.addWidget(widget, 1)
            else:
                lay.addWidget(widget, 0)
        self._rows.addWidget(row)

    def add_widget_row(self, content):
        """兼容旧 API：无左标签的横排控件。"""
        if isinstance(content, QLayout):
            wrap = QWidget()
            wrap.setObjectName("fieldsRow")
            wrap.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
            wrap.setLayout(content)
            content = wrap
        self.add_row("", content)

    def add_fields_row(self, *items: tuple[str, QWidget]):
        """兼容旧 API：多字段同行（无主标签）。"""
        self.add_segments_row("", *items)
