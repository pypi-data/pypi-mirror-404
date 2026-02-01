"""Shell backend protocol for command execution.

Supports different execution environments:
- Local shell
- Docker/nsjail sandbox
- E2B cloud sandbox
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import AsyncIterator, Literal, Protocol, runtime_checkable


@dataclass
class ShellResult:
    """Result of shell command execution."""
    stdout: str
    stderr: str
    exit_code: int
    
    # Execution metadata
    command: str = ""
    cwd: str = ""
    duration_ms: int = 0
    
    @property
    def success(self) -> bool:
        return self.exit_code == 0
    
    @property
    def output(self) -> str:
        """Combined output (stdout + stderr if error)."""
        if self.success:
            return self.stdout
        return f"{self.stdout}\n{self.stderr}".strip()
    
    def to_dict(self) -> dict:
        return {
            "stdout": self.stdout,
            "stderr": self.stderr,
            "exit_code": self.exit_code,
            "command": self.command,
            "cwd": self.cwd,
            "duration_ms": self.duration_ms,
        }


@runtime_checkable
class ShellBackend(Protocol):
    """Protocol for shell command execution.
    
    Implementations:
    - LocalShellBackend - Execute on local machine
    - SandboxShellBackend - Execute in Docker/nsjail sandbox
    - E2BShellBackend - Execute in E2B cloud sandbox
    """
    
    async def execute(
        self,
        command: str,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
        timeout: int = 120,
    ) -> ShellResult:
        """Execute a shell command.
        
        Args:
            command: Command to execute
            cwd: Working directory (optional)
            env: Environment variables (optional)
            timeout: Timeout in seconds (default: 120)
            
        Returns:
            ShellResult with stdout, stderr, exit_code
        """
        ...
    
    async def execute_stream(
        self,
        command: str,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
        timeout: int = 120,
    ) -> AsyncIterator[str]:
        """Execute command with streaming output.
        
        Args:
            command: Command to execute
            cwd: Working directory (optional)
            env: Environment variables (optional)
            timeout: Timeout in seconds (default: 120)
            
        Yields:
            Output chunks as they arrive
        """
        ...


class LocalShellBackend:
    """Local shell execution backend."""
    
    def __init__(self, default_cwd: str | None = None, default_shell: str = "/bin/bash"):
        self.default_cwd = default_cwd
        self.default_shell = default_shell
    
    async def execute(
        self,
        command: str,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
        timeout: int = 120,
    ) -> ShellResult:
        """Execute command locally."""
        import asyncio
        import os
        import time
        
        work_dir = cwd or self.default_cwd or os.getcwd()
        start_time = time.time()
        
        # Merge environment
        full_env = os.environ.copy()
        if env:
            full_env.update(env)
        
        try:
            proc = await asyncio.create_subprocess_shell(
                command,
                cwd=work_dir,
                env=full_env,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout,
            )
            
            return ShellResult(
                stdout=stdout.decode("utf-8", errors="replace"),
                stderr=stderr.decode("utf-8", errors="replace"),
                exit_code=proc.returncode or 0,
                command=command,
                cwd=work_dir,
                duration_ms=int((time.time() - start_time) * 1000),
            )
            
        except asyncio.TimeoutError:
            return ShellResult(
                stdout="",
                stderr=f"Command timed out after {timeout} seconds",
                exit_code=-1,
                command=command,
                cwd=work_dir,
                duration_ms=timeout * 1000,
            )
        except Exception as e:
            return ShellResult(
                stdout="",
                stderr=str(e),
                exit_code=-1,
                command=command,
                cwd=work_dir,
                duration_ms=int((time.time() - start_time) * 1000),
            )
    
    async def execute_stream(
        self,
        command: str,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
        timeout: int = 120,
    ) -> AsyncIterator[str]:
        """Execute with streaming output."""
        import asyncio
        import os
        
        work_dir = cwd or self.default_cwd or os.getcwd()
        
        full_env = os.environ.copy()
        if env:
            full_env.update(env)
        
        proc = await asyncio.create_subprocess_shell(
            command,
            cwd=work_dir,
            env=full_env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        
        async def read_with_timeout():
            try:
                async with asyncio.timeout(timeout):
                    while True:
                        line = await proc.stdout.readline()
                        if not line:
                            break
                        yield line.decode("utf-8", errors="replace")
            except asyncio.TimeoutError:
                proc.kill()
                yield f"\n[Timeout after {timeout} seconds]\n"
        
        async for chunk in read_with_timeout():
            yield chunk


__all__ = ["ShellBackend", "ShellResult", "LocalShellBackend"]
