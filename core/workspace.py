import datetime
import json
import os
import re
import shutil
import uuid


_UUID_PATTERN = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)


class WorkspaceManager:
    """工作空间文件管理器。磁盘目录使用 UUID，界面显示中文名。"""

    def __init__(self, base_dir=None):
        if base_dir is None:
            base_dir = os.path.abspath("workspace")
        self._base_dir = base_dir
        os.makedirs(self._base_dir, exist_ok=True)
        self._migrate_legacy()

    @property
    def base_dir(self):
        return self._base_dir

    def _index_path(self):
        return os.path.join(self._base_dir, "index.json")

    def _read_index(self):
        path = self._index_path()
        if not os.path.exists(path):
            return {"last_workspace": None, "workspaces": {}}
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write_index(self, data):
        with open(self._index_path(), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _migrate_legacy(self):
        """迁移旧版（目录名 = 中文名）到新版（UUID 目录）"""
        idx = self._read_index()
        workspaces = idx.setdefault("workspaces", {})
        changed = False
        for entry in os.listdir(self._base_dir):
            full = os.path.join(self._base_dir, entry)
            if not os.path.isdir(full) or entry.startswith(".") or entry == "index.json":
                continue
            if _UUID_PATTERN.match(entry):
                continue
            if entry in workspaces:
                continue
            uuid_dir = str(uuid.uuid4())
            src = full
            dst = os.path.join(self._base_dir, uuid_dir)
            os.rename(src, dst)
            workspaces[entry] = uuid_dir
            meta_file = os.path.join(dst, "workspace.json")
            if os.path.exists(meta_file):
                with open(meta_file, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                meta["name"] = entry
            else:
                meta = {"name": entry, "created_at": datetime.datetime.now().isoformat()}
            meta["last_used_at"] = datetime.datetime.now().isoformat()
            with open(meta_file, "w", encoding="utf-8") as f:
                json.dump(meta, f, indent=2, ensure_ascii=False)
            changed = True
        if changed:
            self._write_index(idx)

    def list_workspaces(self):
        idx = self._read_index()
        return sorted(idx.get("workspaces", {}).keys())

    def create_workspace(self, name):
        if name in self._read_index().get("workspaces", {}):
            return self._workspace_path(name)
        uuid_dir = str(uuid.uuid4())
        path = os.path.join(self._base_dir, uuid_dir)
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
        idx = self._read_index()
        idx.setdefault("workspaces", {})[name] = uuid_dir
        self._write_index(idx)
        return path

    def delete_workspace(self, name):
        idx = self._read_index()
        uuid_dir = idx.get("workspaces", {}).pop(name, None)
        if uuid_dir:
            self._write_index(idx)
            path = os.path.join(self._base_dir, uuid_dir)
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
        idx = self._read_index()
        uuid_dir = idx.get("workspaces", {}).get(name)
        if uuid_dir:
            return os.path.join(self._base_dir, uuid_dir)
        return os.path.join(self._base_dir, name)
