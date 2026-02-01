"""Shell backend types and protocols."""
from __future__ import annotations

from dataclasses import dataclass
from typing import AsyncIterator, Protocol, runtime_checkable


@dataclass
class ShellResult:
    """Result of shell command execution."""
    stdout: str
    stderr: str
    exit_code: int
    command: str = ""
    cwd: str = ""
    duration_ms: int = 0
    
    @property
    def success(self) -> bool:
        return self.exit_code == 0
    
    @property
    def output(self) -> str:
        """Combined output."""
        if self.success:
            return self.stdout
        return f"{self.stdout}\n{self.stderr}".strip()


@runtime_checkable
class ShellBackend(Protocol):
    """Protocol for shell command execution."""
    
    async def execute(
        self,
        command: str,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
        timeout: int = 120,
    ) -> ShellResult:
        """Execute a shell command."""
        ...
    
    async def execute_stream(
        self,
        command: str,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
        timeout: int = 120,
    ) -> AsyncIterator[str]:
        """Execute command with streaming output."""
        ...


__all__ = ["ShellResult", "ShellBackend"]
