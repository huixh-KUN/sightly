from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class OCRGroupConfig:
    name: str = "识别组 1"
    enabled: bool = True
    region: tuple[int, int, int, int] | None = None
    interval: str = "3"
    pause: str = "3"
    key: str = ""
    delay_min: str = "1"
    delay_max: str = "3"
    alarm: bool = False
    click: bool = False
    click_offset: str = "0"
    keywords: str = ""
    language: str = "简体中文"


@dataclass
class TimedGroupConfig:
    name: str = "定时组 1"
    enabled: bool = True
    interval: str = "10"
    key: str = ""
    delay_min: str = "300"
    delay_max: str = "500"
    alarm: bool = False
    click_enabled: bool = False
    click_offset: str = "0"
    position_x: str = "0"
    position_y: str = "0"
    position: str = "0,0"


@dataclass
class NumberGroupConfig:
    name: str = "识别组 1"
    enabled: bool = True
    region: tuple[int, int, int, int] | None = None
    threshold: str = "500"
    confidence_threshold: str = "0.3"
    key: str = ""
    delay_min: str = "100"
    delay_max: str = "200"
    alarm: bool = False


@dataclass
class ImageGroupConfig:
    name: str = "检测组 1"
    enabled: bool = True
    region: tuple[int, int, int, int] | None = None
    reference_image: str = ""
    threshold: str = "80"
    interval: str = "5"
    pause: str = "180"
    key: str = ""
    delay_min: str = "300"
    delay_max: str = "500"
    alarm: bool = False
    click: bool = False
    click_offset: str = "0"


@dataclass
class BackgroundGroupConfig:
    name: str = "组 1"
    enabled: bool = True
    type: str = "ocr"
    region: tuple[int, int, int, int] | None = None
    region_ratio: tuple[float, float, float, float] | None = None
    key: str = ""
    alarm: bool = False
    click_enabled: bool = False
    click_mode: str = "physical"
    click_offset: str = "0"
    delay_min: str = "100"
    delay_max: str = "200"
    interval: str = "3"
    pause: str = "180"
    keywords: str = ""
    language: str = "简体中文"
    threshold: str = "80"
    reference_image: str = ""
    template_image: Any | None = None
    target_color: tuple[int, int, int] | None = None
    tolerance: str = "30"


@dataclass
class BackgroundPanelConfig:
    window_class: str = ""
    window_process: str = ""
    window_title: str = ""
    groups: list[BackgroundGroupConfig] = field(default_factory=list)


@dataclass
class ColorConfig:
    target_color: tuple[int, int, int] | None = None
    tolerance: str = "30"
    interval: str = "3"
    region: tuple[int, int, int, int] | None = None
    commands: str = ""


@dataclass
class ScriptConfig:
    script_text: str = ""
    record_hotkey: str = ""


@dataclass
class AlarmConfig:
    sound_path: str = ""
    volume: str = "70"
