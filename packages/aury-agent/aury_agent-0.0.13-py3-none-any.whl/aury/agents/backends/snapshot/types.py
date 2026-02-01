"""Snapshot backend types and protocols."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass
class Patch:
    """File change record."""
    files: list[str]
    additions: int = 0
    deletions: int = 0
    diff: str = ""
    
    def to_dict(self) -> dict:
        return {
            "files": self.files,
            "additions": self.additions,
            "deletions": self.deletions,
            "diff": self.diff,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> Patch:
        return cls(
            files=data.get("files", []),
            additions=data.get("additions", 0),
            deletions=data.get("deletions", 0),
            diff=data.get("diff", ""),
        )


@runtime_checkable
class SnapshotBackend(Protocol):
    """Protocol for file state tracking."""
    
    async def track(self) -> str:
        """Record current state, return snapshot ID."""
        ...
    
    async def restore(self, snapshot_id: str) -> None:
        """Fully restore to snapshot state."""
        ...
    
    async def revert(self, patches: list[Patch]) -> None:
        """Revert specific files based on patches."""
        ...
    
    async def diff(self, snapshot_id: str) -> str:
        """Get diff between current state and snapshot."""
        ...
    
    async def patch(self, snapshot_id: str) -> Patch:
        """Get changed files since snapshot."""
        ...


__all__ = ["Patch", "SnapshotBackend"]
