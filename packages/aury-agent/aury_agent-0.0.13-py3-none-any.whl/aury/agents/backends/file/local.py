"""Local file system backend."""
from __future__ import annotations

from pathlib import Path

import aiofiles


class LocalFileBackend:
    """Local file system backend."""
    
    def __init__(self, base_path: str | None = None):
        """Initialize with optional base path for relative paths."""
        self.base_path = Path(base_path) if base_path else None
    
    def _resolve(self, path: str) -> Path:
        """Resolve path (handle relative paths if base_path set)."""
        p = Path(path)
        if not p.is_absolute() and self.base_path:
            return self.base_path / p
        return p
    
    async def read(self, path: str) -> str:
        """Read file content."""
        async with aiofiles.open(self._resolve(path), "r", encoding="utf-8") as f:
            return await f.read()
    
    async def write(self, path: str, content: str) -> None:
        """Write content to file."""
        p = self._resolve(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(p, "w", encoding="utf-8") as f:
            await f.write(content)
    
    async def append(self, path: str, content: str) -> None:
        """Append content to file."""
        p = self._resolve(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        async with aiofiles.open(p, "a", encoding="utf-8") as f:
            await f.write(content)
    
    async def delete(self, path: str) -> bool:
        """Delete file."""
        p = self._resolve(path)
        if p.exists():
            p.unlink()
            return True
        return False
    
    async def exists(self, path: str) -> bool:
        """Check if file exists."""
        return self._resolve(path).exists()
    
    async def list(self, path: str, pattern: str = "*") -> list[str]:
        """List files matching pattern."""
        p = self._resolve(path)
        if not p.exists():
            return []
        return [str(f) for f in p.glob(pattern) if f.is_file()]
    
    async def mkdir(self, path: str, parents: bool = True) -> None:
        """Create directory."""
        self._resolve(path).mkdir(parents=parents, exist_ok=True)


__all__ = ["LocalFileBackend"]
