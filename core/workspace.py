import datetime
import json
import os
import shutil


class WorkspaceManager:
    """工作空间文件管理器。仅负责目录和文件读写，不含运行时状态。"""

    def __init__(self, base_dir=None):
        if base_dir is None:
            base_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "workspace"
            )
        self._base_dir = base_dir
        os.makedirs(self._base_dir, exist_ok=True)

    @property
    def base_dir(self):
        return self._base_dir

    def list_workspaces(self):
        if not os.path.exists(self._base_dir):
            return []
        return sorted([
            d for d in os.listdir(self._base_dir)
            if os.path.isdir(os.path.join(self._base_dir, d))
            and not d.startswith(".")
        ])

    def create_workspace(self, name):
        path = self._workspace_path(name)
        if os.path.exists(path):
            return path
        os.makedirs(os.path.join(path, "templates"), exist_ok=True)
        meta = {
            "name": name,
            "created_at": datetime.datetime.now().isoformat(),
            "last_used_at": datetime.datetime.now().isoformat(),
        }
        with open(os.path.join(path, "workspace.json"), "w", encoding="utf-8") as f:
            json.dump(meta, f, indent=2, ensure_ascii=False)
        with open(os.path.join(path, "config.json"), "w", encoding="utf-8") as f:
            json.dump({}, f, indent=2, ensure_ascii=False)
        return path

    def delete_workspace(self, name):
        path = self._workspace_path(name)
        if os.path.exists(path):
            shutil.rmtree(path)

    def load(self, name):
        if not name:
            return {}
        path = self._workspace_path(name)
        config_file = os.path.join(path, "config.json")
        if not os.path.exists(config_file):
            return {}
        with open(config_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def save(self, name, config_dict):
        if not name:
            return False
        path = self._workspace_path(name)
        os.makedirs(path, exist_ok=True)
        config_file = os.path.join(path, "config.json")
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)
        meta_file = os.path.join(path, "workspace.json")
        if os.path.exists(meta_file):
            with open(meta_file, "r", encoding="utf-8") as f:
                meta = json.load(f)
            meta["last_used_at"] = datetime.datetime.now().isoformat()
            with open(meta_file, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)
        return True

    def save_template_image(self, workspace_name, panel_id, group_index, pixmap_or_path):
        if not workspace_name:
            return None
        templates_dir = os.path.join(self._workspace_path(workspace_name), "templates")
        os.makedirs(templates_dir, exist_ok=True)
        filename = f"{panel_id}_{group_index}.png"
        filepath = os.path.join(templates_dir, filename)
        if hasattr(pixmap_or_path, "save"):
            pixmap_or_path.save(filepath)
        else:
            shutil.copy2(pixmap_or_path, filepath)
        return filepath

    def get_template_path(self, workspace_name, panel_id, group_index):
        if not workspace_name:
            return None
        path = os.path.join(
            self._workspace_path(workspace_name),
            "templates",
            f"{panel_id}_{group_index}.png",
        )
        return path if os.path.exists(path) else None

    def _workspace_path(self, name):
        return os.path.join(self._base_dir, name)
