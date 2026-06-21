import requests
import json
import os
import threading
import time
import webbrowser

from PySide6.QtWidgets import (
    QMessageBox, QDialog, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QApplication
)
from PySide6.QtCore import Qt, QTimer


def open_bilibili():
    webbrowser.open('https://space.bilibili.com/1951697426')


def open_tool_intro():
    webbrowser.open('https://my.feishu.cn/wiki/GqoWwddPMizkLYkogn8cdoynn3c?from=from_copylink')


def compare_versions(version1, version2):
    parts1 = list(map(int, version1.split('.')))
    parts2 = list(map(int, version2.split('.')))
    max_len = max(len(parts1), len(parts2))
    parts1.extend([0] * (max_len - len(parts1)))
    parts2.extend([0] * (max_len - len(parts2)))
    for v1, v2 in zip(parts1, parts2):
        if v1 < v2:
            return -1
        elif v1 > v2:
            return 1
    return 0


class UpdateNotificationDialog(QDialog):
    def __init__(self, app, latest_version, release_date_str, changelog_summary, download_url):
        super().__init__()
        self.app = app
        self.latest_version = latest_version
        self.download_url = download_url
        self.setWindowTitle("发现新版本")
        self.setFixedSize(450, 400)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel(f"发现新版本: v{latest_version}")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title)

        date_label = QLabel(f"发布日期: {release_date_str}")
        layout.addWidget(date_label)

        changelog_label = QLabel("更新内容:")
        changelog_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(changelog_label)

        self.changelog_text = QTextEdit()
        self.changelog_text.setPlainText(changelog_summary)
        self.changelog_text.setReadOnly(True)
        self.changelog_text.setFixedHeight(160)
        layout.addWidget(self.changelog_text)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        view_btn = QPushButton("查看更新")
        view_btn.clicked.connect(self._open_update_link)
        btn_layout.addWidget(view_btn)

        later_btn = QPushButton("稍后提醒")
        later_btn.clicked.connect(self.accept)
        btn_layout.addWidget(later_btn)

        ignore_btn = QPushButton("忽略此版本")
        ignore_btn.clicked.connect(self._ignore_version)
        btn_layout.addWidget(ignore_btn)

        layout.addLayout(btn_layout)

    def _open_update_link(self):
        webbrowser.open(self.download_url)

    def _ignore_version(self):
        try:
            config_file_path = getattr(self.app, 'config_file_path', None)
            if config_file_path:
                os.makedirs(os.path.dirname(config_file_path), exist_ok=True)
                config = {}
                if os.path.exists(config_file_path):
                    try:
                        with open(config_file_path, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                    except json.JSONDecodeError:
                        config = {}
                if 'update' not in config:
                    config['update'] = {}
                config['update']['ignored_version'] = self.latest_version
                with open(config_file_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False, default=str)
                try:
                    self.app.logging_manager.log_message(f"已忽略版本: {self.latest_version}")
                except Exception:
                    print(f"已忽略版本: {self.latest_version}")
        except Exception as e:
            try:
                self.app.logging_manager.log_message(f"忽略版本失败: {str(e)}")
            except Exception:
                print(f"忽略版本失败: {str(e)}")
        self.accept()


class VersionChecker:
    def __init__(self, app):
        self.app = app
        self.ignored_version = None
        self._load_ignored_version()

    def _load_ignored_version(self):
        try:
            config_file_path = getattr(self.app, 'config_file_path', None)
            if config_file_path and os.path.exists(config_file_path):
                with open(config_file_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.ignored_version = config.get('update', {}).get('ignored_version')
        except Exception as e:
            self.app.logging_manager.error("VERSION", f"加载忽略版本配置失败: {e}")

    def get_current_version(self):
        return "1.0.0"

    def check_for_updates(self):
        """检查更新，返回最新版本号和下载链接"""
        try:
            response = requests.get(
                'https://api.github.com/repos/wdhq4261761/autodoor/releases/latest',
                timeout=10
            )
            if response.status_code != 200:
                return None, None, None, None

            data = response.json()
            latest_version = data.get('tag_name', '').lstrip('v')
            release_date = data.get('published_at', '')
            if not latest_version:
                return None, None, None, None

            current_version = self.get_current_version()
            if compare_versions(current_version, latest_version) >= 0:
                return None, None, None, None

            if latest_version == self.ignored_version:
                return None, None, None, None

            changelog = data.get('body', '')
            changelog_summary = changelog[:500] + '...' if len(changelog) > 500 else changelog

            release_date_str = release_date
            if release_date:
                try:
                    from datetime import datetime
                    release_date_obj = datetime.fromisoformat(release_date.replace('Z', '+00:00'))
                    release_date_str = release_date_obj.strftime('%Y-%m-%d')
                except Exception as e:
                    self.app.logging_manager.error("VERSION", f"解析发布日期失败: {e}")

            download_url = 'https://my.feishu.cn/wiki/GqoWwddPMizkLYkogn8cdoynn3c?from=from_copylink'

            return latest_version, release_date_str, changelog_summary, download_url

        except requests.RequestException:
            return None, None, None, None

    def show_update_notification(self, latest_version, release_date_str, changelog_summary, download_url):
        dialog = UpdateNotificationDialog(
            self.app, latest_version, release_date_str,
            changelog_summary, download_url
        )
        dialog.exec()

    def show_no_update_notification(self):
        QMessageBox.information(None, "检查更新", "当前已是最新版本！")
