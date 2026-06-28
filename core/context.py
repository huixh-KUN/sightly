from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Signal

if TYPE_CHECKING:
    from core.logging import LoggingManager
    from core.state import AppState
    from input.controller import InputController
    from modules.alarm import AlarmWorker


class StatusNotifier(QObject):
    status_changed = Signal(str)

    def info(self, text: str):
        self.status_changed.emit(text)


@dataclass
class ModuleContext:
    app_state: AppState
    logger: LoggingManager
    input_controller: InputController
    alarm: AlarmWorker | None = None
    status_notifier: StatusNotifier | None = None
