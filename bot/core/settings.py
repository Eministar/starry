import os
import json
import yaml
import asyncio
from copy import deepcopy

class SettingsManager:
    def __init__(self, config_path: str, override_path: str):
        self.config_path = config_path
        self.override_path = override_path
        self._lock = asyncio.Lock()
        self._base = {}
        self._override = {}
        self._merged = {}
        self._override_mtime = 0.0
        self._guild_overrides = {}
        self._guild_cache = {}

    async def load(self):
        async with self._lock:
            self._base = self._load_yaml(self.config_path)
            self._override = self._load_json(self.override_path)
            self._merged = self._merge(deepcopy(self._base), deepcopy(self._override))
            self._override_mtime = self._get_mtime(self.override_path)

    async def reload_if_changed(self) -> bool:
        mtime = self._get_mtime(self.override_path)
        if mtime <= 0:
            return False
        if mtime == self._override_mtime:
            return False
        await self.load()
        return True

    async def set_override(self, path: str, value):
        async with self._lock:
            self._override = self._load_json(self.override_path)
            self._set_path(self._override, path, value)
            os.makedirs(os.path.dirname(self.override_path), exist_ok=True)
            with open(self.override_path, "w", encoding="utf-8") as f:
                json.dump(self._override, f, ensure_ascii=False, indent=2)
            self._merged = self._merge(deepcopy(self._base), deepcopy(self._override))
            self._override_mtime = self._get_mtime(self.override_path)

    async def replace_overrides(self, data: dict):
        async with self._lock:
            os.makedirs(os.path.dirname(self.override_path), exist_ok=True)
            with open(self.override_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self._override = data
            self._merged = self._merge(deepcopy(self._base), deepcopy(self._override))
            self._override_mtime = self._get_mtime(self.override_path)

    def dump(self) -> dict:
        return deepcopy(self._merged)

    def dump_guild(self, guild_id: int) -> dict:
        return deepcopy(self._get_guild_merged(guild_id))

    def dump_guild_overrides(self, guild_id: int) -> dict:
        return deepcopy(self._guild_overrides.get(int(guild_id), {}))

    def get(self, dotted: str, default=None):
        node = self._merged
        for part in dotted.split("."):
            if not isinstance(node, dict):
                return default
            if part not in node:
                return default
            node = node[part]
        return node

    def get_int(self, dotted: str, default: int = 0) -> int:
        v = self.get(dotted, default)
        try:
            return int(v)
        except Exception:
            return default

    def get_bool(self, dotted: str, default: bool = False) -> bool:
        v = self.get(dotted, default)
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in {"true", "1", "yes", "on"}
        return bool(v)

    def get_guild(self, guild_id: int, dotted: str, default=None):
        if not guild_id:
            return self.get(dotted, default)
        node = self._get_guild_merged(int(guild_id))
        for part in dotted.split("."):
            if not isinstance(node, dict):
                return default
            if part not in node:
                return default
            node = node[part]
        return node

    def get_guild_int(self, guild_id: int, dotted: str, default: int = 0) -> int:
        v = self.get_guild(guild_id, dotted, default)
        try:
            return int(v)
        except Exception:
            return default

    def get_guild_bool(self, guild_id: int, dotted: str, default: bool = False) -> bool:
        v = self.get_guild(guild_id, dotted, default)
        if isinstance(v, bool):
            return v
        if isinstance(v, str):
            return v.lower() in {"true", "1", "yes", "on"}
        return bool(v)

    async def load_guild_overrides(self, db, guild_id: int | None = None):
        if guild_id:
            rows = await db.list_guild_configs(int(guild_id))
        else:
            rows = await db.list_all_guild_configs()
        overrides = {} if not guild_id else self._guild_overrides
        if not guild_id:
            self._guild_overrides = {}
        for row in rows:
            gid = int(row[0]) if not guild_id else int(guild_id)
            key = row[1] if not guild_id else row[0]
            value_json = row[2] if not guild_id else row[1]
            try:
                value = json.loads(value_json)
            except Exception:
                value = value_json
            node = overrides.get(gid, {})
            self._set_path(node, key, value)
            overrides[gid] = node
        if guild_id:
            self._guild_overrides[int(guild_id)] = overrides.get(int(guild_id), {})
        else:
            self._guild_overrides = overrides
        self._guild_cache = {}

    async def set_guild_override(self, db, guild_id: int, path: str, value):
        async with self._lock:
            await db.set_guild_config(int(guild_id), str(path), json.dumps(value, ensure_ascii=False))
            node = self._guild_overrides.get(int(guild_id), {})
            self._set_path(node, path, value)
            self._guild_overrides[int(guild_id)] = node
            self._guild_cache.pop(int(guild_id), None)

    async def replace_guild_overrides(self, db, guild_id: int, data: dict):
        async with self._lock:
            await db.delete_guild_configs(int(guild_id))
            flat = self._flatten(data)
            for key, value in flat.items():
                await db.set_guild_config(int(guild_id), str(key), json.dumps(value, ensure_ascii=False))
            self._guild_overrides[int(guild_id)] = data
            self._guild_cache.pop(int(guild_id), None)

    def _load_yaml(self, path: str) -> dict:
        if not os.path.exists(path):
            return {}
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        return data

    def _load_json(self, path: str) -> dict:
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f) or {}
        except Exception:
            return {}

    def _merge(self, base: dict, override: dict) -> dict:
        for k, v in override.items():
            if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                base[k] = self._merge(base[k], v)
            else:
                base[k] = v
        return base

    def _set_path(self, root: dict, dotted: str, value):
        parts = dotted.split(".")
        node = root
        for p in parts[:-1]:
            if p not in node or not isinstance(node[p], dict):
                node[p] = {}
            node = node[p]
        node[parts[-1]] = value

    def _get_guild_merged(self, guild_id: int) -> dict:
        gid = int(guild_id)
        cached = self._guild_cache.get(gid)
        if cached is not None:
            return cached
        merged = self._merge(deepcopy(self._base), deepcopy(self._guild_overrides.get(gid, {})))
        self._guild_cache[gid] = merged
        return merged

    def _flatten(self, root: dict, prefix: str = "") -> dict:
        out = {}
        for key, value in (root or {}).items():
            dotted = f"{prefix}.{key}" if prefix else str(key)
            if isinstance(value, dict):
                out.update(self._flatten(value, dotted))
            else:
                out[dotted] = value
        return out

    def _get_mtime(self, path: str) -> float:
        try:
            return os.path.getmtime(path)
        except Exception:
            return 0.0
