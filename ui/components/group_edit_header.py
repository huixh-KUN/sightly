from PySide6.QtCore import Qt
from PySide6.QtGui import QFontMetrics
from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QSizePolicy

from ui.widgets import ClickableLabel


class GroupEditHeader(QFrame):
    """编辑页顶部：组名称输入，不含启用开关（列表项上已有）。"""

    def __init__(self, placeholder="组名称", parent=None):
        super().__init__(parent)
        self.setObjectName("groupEditHeader")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 4)
        layout.setSpacing(8)

        hint = QLabel("组名称")
        hint.setObjectName("groupEditHint")
        layout.addWidget(hint)

        self.title_edit = QLineEdit()
        self.title_edit.setObjectName("groupEditTitle")
        self.title_edit.setPlaceholderText(placeholder)
        layout.addWidget(self.title_edit)


class ValueChip(QFrame):
    """配置值展示条（区域坐标、模板路径等），过长文本中间省略。"""

    def __init__(self, text="未选择", parent=None):
        super().__init__(parent)
        self.setObjectName("valueChip")
        self._full_text = text
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setMinimumWidth(0)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(0)
        self.label = ClickableLabel(text)
        self.label.setObjectName("infoText")
        self.label.setMinimumWidth(0)
        self.label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        layout.addWidget(self.label, 1)

    def set_text(self, text: str, *, accent: bool = False):
        self._full_text = text
        if accent:
            self.label.setObjectName("accentText")
        else:
            self.label.setObjectName("infoText")
        self.label.style().unpolish(self.label)
        self.label.style().polish(self.label)
        self.label.setToolTip(text if text and text != "未选择" else "")
        self._update_elided()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_elided()

    def _update_elided(self):
        inner = max(40, self.width() - 24)
        elided = QFontMetrics(self.label.font()).elidedText(
            self._full_text, Qt.TextElideMode.ElideMiddle, inner
        )
        self.label.setText(elided)
