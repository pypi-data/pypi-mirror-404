"""In-memory snapshot backend for testing."""
from __future__ import annotations

from .types import Patch


class InMemorySnapshotBackend:
    """In-memory snapshot backend for testing."""
    
    def __init__(self) -> None:
        self._snapshots: dict[str, dict[str, str]] = {}
        self._files: dict[str, str] = {}
        self._counter = 0
    
    def set_file(self, path: str, content: str) -> None:
        self._files[path] = content
    
    def get_file(self, path: str) -> str | None:
        return self._files.get(path)
    
    def delete_file(self, path: str) -> None:
        self._files.pop(path, None)
    
    async def track(self) -> str:
        self._counter += 1
        snapshot_id = f"snap_{self._counter:04d}"
        self._snapshots[snapshot_id] = dict(self._files)
        return snapshot_id
    
    async def restore(self, snapshot_id: str) -> None:
        if snapshot_id not in self._snapshots:
            raise ValueError(f"Unknown snapshot: {snapshot_id}")
        self._files = dict(self._snapshots[snapshot_id])
    
    async def revert(self, patches: list[Patch]) -> None:
        snapshots = list(self._snapshots.items())
        if len(snapshots) < 2:
            return
        prev_snapshot = snapshots[-2][1]
        for patch in patches:
            for file_path in patch.files:
                if file_path in prev_snapshot:
                    self._files[file_path] = prev_snapshot[file_path]
                else:
                    self._files.pop(file_path, None)
    
    async def diff(self, snapshot_id: str) -> str:
        if snapshot_id not in self._snapshots:
            return ""
        snapshot = self._snapshots[snapshot_id]
        lines = []
        all_files = set(snapshot.keys()) | set(self._files.keys())
        for path in sorted(all_files):
            old = snapshot.get(path, "")
            new = self._files.get(path, "")
            if old != new:
                lines.append(f"--- a/{path}")
                lines.append(f"+++ b/{path}")
        return "\n".join(lines)
    
    async def patch(self, snapshot_id: str) -> Patch:
        if snapshot_id not in self._snapshots:
            return Patch(files=[])
        snapshot = self._snapshots[snapshot_id]
        files = []
        additions = deletions = 0
        for path in set(snapshot.keys()) | set(self._files.keys()):
            old = snapshot.get(path, "")
            new = self._files.get(path, "")
            if old != new:
                files.append(path)
                old_lines = len(old.split("\n")) if old else 0
                new_lines = len(new.split("\n")) if new else 0
                if new_lines > old_lines:
                    additions += new_lines - old_lines
                else:
                    deletions += old_lines - new_lines
        return Patch(files=files, additions=additions, deletions=deletions, diff=await self.diff(snapshot_id))
    
    def clear(self) -> None:
        self._snapshots.clear()
        self._files.clear()
        self._counter = 0


__all__ = ["InMemorySnapshotBackend"]
