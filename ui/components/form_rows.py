"""表单行辅助：多字段同行、透明容器、无右侧色块。"""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QSizePolicy


def _transparent(widget: QWidget, object_name: str) -> QWidget:
    widget.setObjectName(object_name)
    widget.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
    widget.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
    return widget


def _field_group(label: str, widget: QWidget) -> QWidget:
    group = _transparent(QWidget(), "fieldGroup")
    layout = QHBoxLayout(group)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(8)
    lbl = QLabel(label)
    lbl.setObjectName("inlineFieldLabel")
    lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
    layout.addWidget(lbl)
    layout.addWidget(widget)
    return group


def fields_row(*items: tuple[str, QWidget]) -> QWidget:
    """多个「标签+控件」横排，宽度随内容收缩。"""
    wrap = _transparent(QWidget(), "fieldsRow")
    layout = QHBoxLayout(wrap)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(28)
    for label, widget in items:
        layout.addWidget(_field_group(label, widget))
    return wrap


def spin_range_row(min_spin, max_spin, separator="~") -> QWidget:
    wrap = _transparent(QWidget(), "spinRangeRow")
    layout = QHBoxLayout(wrap)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(8)
    layout.addWidget(min_spin)
    sep = QLabel(separator)
    sep.setObjectName("rangeSep")
    sep.setAlignment(Qt.AlignCenter)
    sep.setFixedWidth(14)
    layout.addWidget(sep)
    layout.addWidget(max_spin)
    return wrap


def click_offset_row(toggle, offset_spin) -> QWidget:
    return fields_row(("点击", toggle), ("偏移", offset_spin))
