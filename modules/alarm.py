import os
import sys
import winsound

from PySide6.QtWidgets import QFileDialog
from PySide6.QtCore import QObject, Signal, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput


def select_alarm_sound(controller):
    filetypes = "音频文件 (*.mp3 *.wav *.ogg *.flac);;所有文件 (*.*)"
    filename, _ = QFileDialog.getOpenFileName(
        None, "选择全局报警声音", "", filetypes
    )
    if filename:
        controller.alarm_module.sound_path = filename
        controller.logging_manager.log_message(f"已选择全局报警声音: {os.path.basename(filename)}")


class AlarmManager(QObject):
    """报警播放模块。WAV 文件直接 winsound 播放（任意线程）；
    非 WAV 文件通过信号投递到主线程用 QtMultimedia 播放。"""
    _qt_play_requested = Signal(str, float)

    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.sound_path = ""
        self.volume = 70
        self.volume_str = "70"
        self.enabled = {
            "ocr": False,
            "timed": False,
            "number": False,
            "image": False,
        }
        self._player = None
        self._audio = None
        self._qt_play_requested.connect(self._play_with_qt)

    def start(self):
        pass

    def stop(self):
        self.play_stop_sound()

    def set_config(self, config):
        if isinstance(config, dict):
            alarm = config.get("alarm", {})
            if alarm.get("sound_path"):
                self.sound_path = alarm["sound_path"]
            if "volume" in alarm:
                self.volume = alarm["volume"]
                self.volume_str = str(alarm["volume"])

    def collect_config(self):
        return {}

    def get_default_alarm_sound_path(self):
        if hasattr(sys, '_MEIPASS'):
            app_root = sys._MEIPASS
        else:
            app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        alarm_path = os.path.join(app_root, "voice", "alarm.mp3")
        alarm_path = os.path.normpath(alarm_path)
        return alarm_path

    def _play_file(self, filepath, volume=0.7):
        if getattr(self.controller, '_is_closing', False):
            return
        if not filepath or not os.path.exists(filepath):
            self.controller.logging_manager.error("ALARM", f"声音文件不存在: {filepath}")
            return
        try:
            if filepath.lower().endswith('.wav'):
                winsound.PlaySound(filepath, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
            else:
                self._qt_play_requested.emit(filepath, volume)
        except Exception as e:
            self.controller.logging_manager.error("ALARM", f"播放声音失败: {str(e)}")

    def _play_with_qt(self, filepath, volume):
        if getattr(self.controller, '_is_closing', False):
            return
        try:
            self._player = QMediaPlayer()
            self._audio = QAudioOutput()
            self._player.setAudioOutput(self._audio)
            self._player.setSource(QUrl.fromLocalFile(filepath))
            self._audio.setVolume(volume)
            self._player.play()
        except Exception as e:
            self.controller.logging_manager.error("ALARM", f"Qt播放声音失败: {str(e)}")

    def play_alarm_sound(self, alarm_var):
        if not alarm_var:
            return
        sound_file = self.sound_path
        if not sound_file or not os.path.exists(sound_file):
            self.controller.logging_manager.error("ALARM", "未设置有效的全局报警声音文件")
            return
        volume = max(0.0, min(1.0, self.volume / 100))
        self._play_file(sound_file, volume)
        self.controller.logging_manager.log_message("报警声音已播放")

    def play_start_sound(self):
        self._play_file(self.get_default_alarm_sound_path(), 0.7)

    def play_stop_sound(self):
        if hasattr(sys, '_MEIPASS'):
            app_root = sys._MEIPASS
        else:
            app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        reversed_file = os.path.normpath(os.path.join(app_root, "voice", "temp_reversed.mp3"))
        if os.path.exists(reversed_file):
            self._play_file(reversed_file, 0.7)
        else:
            self._play_file(self.get_default_alarm_sound_path(), 0.7)
