"""Sandbox types and protocols."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Protocol, runtime_checkable


@dataclass
class ExecutionResult:
    """Result of command execution in sandbox."""
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    timed_out: bool = False
    
    @property
    def success(self) -> bool:
        return self.exit_code == 0 and not self.timed_out
    
    @property
    def output(self) -> str:
        """Combined output for display."""
        if self.success:
            return self.stdout
        return f"{self.stdout}\n{self.stderr}".strip()


@dataclass
class SandboxConfig:
    """Configuration for sandbox creation."""
    image: str = "python:3.11-slim"
    timeout: int = 300  # seconds
    memory_limit: str = "512m"
    cpu_limit: float = 1.0
    network: bool = False
    volumes: dict[str, str] = field(default_factory=dict)
    env: dict[str, str] = field(default_factory=dict)
    workdir: str = "/workspace"


@runtime_checkable
class Sandbox(Protocol):
    """Protocol for sandbox instances.
    
    A sandbox provides an isolated environment for executing
    commands and managing files safely.
    """
    
    @property
    def id(self) -> str:
        """Unique sandbox identifier."""
        ...
    
    @property
    def status(self) -> Literal["creating", "running", "stopped", "failed"]:
        """Current sandbox status."""
        ...
    
    async def execute(
        self,
        command: str | list[str],
        *,
        timeout: int | None = None,
        stdin: str | None = None,
        env: dict[str, str] | None = None,
        workdir: str | None = None,
    ) -> ExecutionResult:
        """Execute a command in the sandbox."""
        ...
    
    async def write_file(self, path: str, content: str | bytes) -> None:
        """Write a file to the sandbox."""
        ...
    
    async def read_file(self, path: str) -> bytes:
        """Read a file from the sandbox."""
        ...
    
    async def upload(self, local_path: Path, remote_path: str) -> None:
        """Upload a file or directory to the sandbox."""
        ...
    
    async def download(self, remote_path: str, local_path: Path) -> None:
        """Download a file or directory from the sandbox."""
        ...
    
    async def stop(self) -> None:
        """Stop the sandbox (can be restarted)."""
        ...
    
    async def destroy(self) -> None:
        """Destroy the sandbox permanently."""
        ...


@runtime_checkable
class SandboxProvider(Protocol):
    """Protocol for sandbox providers.
    
    Creates and manages sandbox instances.
    """
    
    async def create(self, config: SandboxConfig | None = None) -> Sandbox:
        """Create a new sandbox instance."""
        ...


__all__ = [
    "ExecutionResult",
    "SandboxConfig",
    "Sandbox",
    "SandboxProvider",
]
