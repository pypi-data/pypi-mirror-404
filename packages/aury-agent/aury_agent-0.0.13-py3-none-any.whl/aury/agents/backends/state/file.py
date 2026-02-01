"""File-based state backend."""
from __future__ import annotations

from pathlib import Path
from typing import Any


class FileStateBackend:
    """File-based state backend.
    
    Stores data as JSON files organized by namespace.
    """
    
    def __init__(self, base_path: str | Path):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _get_path(self, namespace: str, key: str) -> Path:
        ns_path = self.base_path / namespace
        ns_path.mkdir(parents=True, exist_ok=True)
        return ns_path / f"{key}.json"
    
    async def get(self, namespace: str, key: str) -> Any | None:
        import json
        import aiofiles
        path = self._get_path(namespace, key)
        if not path.exists():
            return None
        async with aiofiles.open(path, "r") as f:
            content = await f.read()
            return json.loads(content)
    
    async def set(self, namespace: str, key: str, value: Any) -> None:
        import json
        import aiofiles
        path = self._get_path(namespace, key)
        async with aiofiles.open(path, "w") as f:
            await f.write(json.dumps(value, default=str, ensure_ascii=False, indent=2))
    
    async def delete(self, namespace: str, key: str) -> bool:
        path = self._get_path(namespace, key)
        if path.exists():
            path.unlink()
            return True
        return False
    
    async def list(self, namespace: str, prefix: str = "") -> list[str]:
        ns_path = self.base_path / namespace
        if not ns_path.exists():
            return []
        return [f.stem for f in ns_path.glob("*.json") if f.stem.startswith(prefix)]
    
    async def exists(self, namespace: str, key: str) -> bool:
        return self._get_path(namespace, key).exists()


__all__ = ["FileStateBackend"]
