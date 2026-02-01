"""File backend types and protocols."""
from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class FileBackend(Protocol):
    """Protocol for file system operations."""
    
    async def read(self, path: str) -> str:
        """Read file content."""
        ...
    
    async def write(self, path: str, content: str) -> None:
        """Write content to file."""
        ...
    
    async def append(self, path: str, content: str) -> None:
        """Append content to file."""
        ...
    
    async def delete(self, path: str) -> bool:
        """Delete file. Returns True if deleted."""
        ...
    
    async def exists(self, path: str) -> bool:
        """Check if file exists."""
        ...
    
    async def list(self, path: str, pattern: str = "*") -> list[str]:
        """List files in directory matching pattern."""
        ...
    
    async def mkdir(self, path: str, parents: bool = True) -> None:
        """Create directory."""
        ...


__all__ = ["FileBackend"]
