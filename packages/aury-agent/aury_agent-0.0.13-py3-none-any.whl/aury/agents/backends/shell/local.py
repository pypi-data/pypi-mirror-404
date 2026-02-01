"""Local shell execution backend."""
from __future__ import annotations

import asyncio
import os
import time
from typing import AsyncIterator

from .types import ShellResult


class LocalShellBackend:
    """Local shell execution backend."""
    
    def __init__(self, default_cwd: str | None = None, shell: str = "/bin/bash"):
        self.default_cwd = default_cwd
        self.shell = shell
    
    async def execute(
        self,
        command: str,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
        timeout: int = 120,
    ) -> ShellResult:
        """Execute command locally."""
        work_dir = cwd or self.default_cwd or os.getcwd()
        start_time = time.time()
        
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
                stderr=f"Command timed out after {timeout}s",
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
        
        try:
            async with asyncio.timeout(timeout):
                while True:
                    line = await proc.stdout.readline()
                    if not line:
                        break
                    yield line.decode("utf-8", errors="replace")
        except asyncio.TimeoutError:
            proc.kill()
            yield f"\n[Timeout after {timeout}s]\n"


__all__ = ["LocalShellBackend"]
