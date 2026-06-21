import os
import sys

from PySide6.QtWidgets import QFileDialog
from PySide6.QtCore import QUrl

try:
    from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
    MEDIA_AVAILABLE = True
except ImportError:
    MEDIA_AVAILABLE = False


def select_alarm_sound(app):
    filetypes = "音频文件 (*.mp3 *.wav *.ogg *.flac);;所有文件 (*.*)"
    filename, _ = QFileDialog.getOpenFileName(
        None, "选择全局报警声音", "", filetypes
    )
    if filename:
        if hasattr(app, 'alarm_sound_path'):
            try:
                app.alarm_sound_path.set(filename)
            except Exception:
                app.alarm_sound_path = filename
        app.logging_manager.log_message(f"已选择全局报警声音: {os.path.basename(filename)}")
        if hasattr(app, 'save_config') and callable(app.save_config):
            try:
                app.save_config()
            except Exception:
                pass


class AlarmModule:
    def __init__(self, app):
        self.app = app
        self._player = None

    def get_default_alarm_sound_path(self):
        if hasattr(sys, '_MEIPASS'):
            app_root = sys._MEIPASS
        else:
            app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        alarm_path = os.path.join(app_root, "voice", "alarm.mp3")
        alarm_path = os.path.normpath(alarm_path)
        return alarm_path

    def _play_file(self, filepath, volume=0.7):
        if not MEDIA_AVAILABLE:
            self.app.logging_manager.error("ALARM", "QtMultimedia 不可用，无法播放声音")
            return
        if not filepath or not os.path.exists(filepath):
            self.app.logging_manager.error("ALARM", f"声音文件不存在: {filepath}")
            return
        try:
            player = QMediaPlayer()
            audio_output = QAudioOutput()
            player.setAudioOutput(audio_output)
            player.setSource(QUrl.fromLocalFile(filepath))
            audio_output.setVolume(volume)
            player.play()
            self._player = player
        except Exception as e:
            self.app.logging_manager.error("ALARM", f"播放声音失败: {str(e)}")

    def play_alarm_sound(self, alarm_var):
        if not alarm_var.get():
            return
        sound_file = self.app.alarm_sound_path.get()
        if not sound_file or not os.path.exists(sound_file):
            self.app.logging_manager.error("ALARM", "未设置有效的全局报警声音文件")
            return
        volume = max(0.0, min(1.0, self.app.alarm_volume.get() / 100))
        self._play_file(sound_file, volume)
        self.app.logging_manager.log_message("报警声音已播放")

    def play_start_sound(self):
        sound_file = self.get_default_alarm_sound_path()
        self._play_file(sound_file, 0.7)

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
