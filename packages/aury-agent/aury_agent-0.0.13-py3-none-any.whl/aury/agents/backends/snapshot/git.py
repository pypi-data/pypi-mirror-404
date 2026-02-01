"""Git-based snapshot backend."""
from __future__ import annotations

import asyncio
from datetime import datetime
from pathlib import Path

from .types import Patch


class GitSnapshotBackend:
    """Git-based snapshot backend."""
    
    def __init__(self, worktree: str | Path, snapshot_dir: str | Path | None = None):
        self.worktree = Path(worktree).resolve()
        self.snapshot_dir = Path(snapshot_dir).resolve() if snapshot_dir else self.worktree / ".aury_snapshot"
        self._initialized = False
    
    async def _ensure_repo(self) -> None:
        if self._initialized:
            return
        git_dir = self.snapshot_dir / ".git" if not str(self.snapshot_dir).endswith(".git") else self.snapshot_dir
        if not git_dir.exists():
            self.snapshot_dir.mkdir(parents=True, exist_ok=True)
            proc = await asyncio.create_subprocess_exec(
                "git", "init",
                cwd=str(self.worktree),
                env={"GIT_DIR": str(self.snapshot_dir)},
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.wait()
            await self._git_config("user.email", "aury@agent.local")
            await self._git_config("user.name", "Aury Agent")
        self._initialized = True
    
    async def _git_config(self, key: str, value: str) -> None:
        proc = await asyncio.create_subprocess_exec(
            "git", "config", key, value,
            cwd=str(self.worktree),
            env={"GIT_DIR": str(self.snapshot_dir)},
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await proc.wait()
    
    async def _run_git(self, *args: str, check: bool = True) -> tuple[str, str]:
        await self._ensure_repo()
        proc = await asyncio.create_subprocess_exec(
            "git", *args,
            cwd=str(self.worktree),
            env={"GIT_DIR": str(self.snapshot_dir)},
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if check and proc.returncode != 0:
            raise RuntimeError(f"Git command failed: {stderr.decode()}")
        return stdout.decode(), stderr.decode()
    
    async def track(self) -> str:
        await self._ensure_repo()
        await self._run_git("add", "-A", check=False)
        timestamp = datetime.now().isoformat()
        await self._run_git("commit", "-m", f"snapshot_{timestamp}", "--allow-empty", check=False)
        stdout, _ = await self._run_git("rev-parse", "HEAD")
        return stdout.strip()
    
    async def restore(self, snapshot_id: str) -> None:
        await self._run_git("checkout", snapshot_id, "--", ".")
    
    async def revert(self, patches: list[Patch]) -> None:
        for patch in patches:
            for file_path in patch.files:
                await self._run_git("checkout", "HEAD~1", "--", file_path, check=False)
    
    async def diff(self, snapshot_id: str) -> str:
        stdout, _ = await self._run_git("diff", snapshot_id, "--", check=False)
        return stdout
    
    async def patch(self, snapshot_id: str) -> Patch:
        stdout, _ = await self._run_git("diff", "--stat", snapshot_id, "--", check=False)
        files = []
        additions = deletions = 0
        for line in stdout.strip().split("\n"):
            if "|" in line:
                file_path = line.split("|")[0].strip()
                files.append(file_path)
                stat_part = line.split("|")[1].strip() if "|" in line else ""
                additions += stat_part.count("+")
                deletions += stat_part.count("-")
        return Patch(files=files, additions=additions, deletions=deletions, diff=await self.diff(snapshot_id))


__all__ = ["GitSnapshotBackend"]
