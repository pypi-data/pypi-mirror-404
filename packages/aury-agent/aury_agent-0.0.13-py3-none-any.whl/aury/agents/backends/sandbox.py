"""Sandbox-based backend implementations.

Provides ShellBackend and CodeBackend implementations that execute
commands and code in isolated sandbox environments.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, AsyncIterator

from .shell import ShellBackend, ShellResult
from .code import CodeBackend, CodeResult

if TYPE_CHECKING:
    from ..sandbox import Sandbox, SandboxProvider, SandboxConfig


class SandboxShellBackend:
    """Shell backend that executes commands in a sandbox.
    
    Commands are executed in an isolated container environment,
    providing security isolation from the host system.
    
    Usage:
        provider = LocalSandboxProvider()
        backend = SandboxShellBackend(provider)
        
        result = await backend.execute("ls -la")
    """
    
    def __init__(
        self,
        provider: "SandboxProvider",
        config: "SandboxConfig | None" = None,
        reuse_sandbox: bool = True,
    ) -> None:
        """Initialize sandbox shell backend.
        
        Args:
            provider: Sandbox provider for creating sandboxes
            config: Optional sandbox configuration
            reuse_sandbox: If True, reuse sandbox across commands (default)
        """
        self.provider = provider
        self.config = config
        self.reuse_sandbox = reuse_sandbox
        self._sandbox: "Sandbox | None" = None
    
    async def _get_sandbox(self) -> "Sandbox":
        """Get or create sandbox instance."""
        if self._sandbox is None or not self.reuse_sandbox:
            self._sandbox = await self.provider.create(self.config)
        return self._sandbox
    
    async def execute(
        self,
        command: str,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
        timeout: int = 120,
    ) -> ShellResult:
        """Execute a shell command in the sandbox.
        
        Args:
            command: Shell command to execute
            cwd: Working directory (relative to sandbox workdir)
            env: Environment variables
            timeout: Timeout in seconds
            
        Returns:
            ShellResult with stdout, stderr, exit_code
        """
        sandbox = await self._get_sandbox()
        
        result = await sandbox.execute(
            command,
            workdir=cwd,
            env=env,
            timeout=timeout,
        )
        
        return ShellResult(
            stdout=result.stdout,
            stderr=result.stderr,
            exit_code=result.exit_code,
            command=command,
            cwd=cwd or "",
            duration_ms=result.duration_ms,
        )
    
    async def execute_stream(
        self,
        command: str,
        cwd: str | None = None,
        env: dict[str, str] | None = None,
        timeout: int = 120,
    ) -> AsyncIterator[str]:
        """Execute command with streaming output.
        
        Note: Basic implementation - executes and yields result.
        Full streaming requires sandbox API support.
        """
        result = await self.execute(command, cwd, env, timeout)
        if result.stdout:
            yield result.stdout
        if result.stderr:
            yield result.stderr
    
    async def cleanup(self) -> None:
        """Cleanup sandbox resources."""
        if self._sandbox:
            await self._sandbox.destroy()
            self._sandbox = None


class SandboxCodeBackend:
    """Code backend that executes code in a sandbox.
    
    Supports multiple programming languages by writing code
    to files and executing with appropriate interpreters.
    
    Usage:
        provider = LocalSandboxProvider()
        backend = SandboxCodeBackend(provider)
        
        result = await backend.execute("print('hello')", language="python")
    """
    
    # Language configurations
    LANGUAGE_CONFIG = {
        "python": {
            "extension": ".py",
            "command": "python3",
        },
        "python3": {
            "extension": ".py", 
            "command": "python3",
        },
        "javascript": {
            "extension": ".js",
            "command": "node",
        },
        "js": {
            "extension": ".js",
            "command": "node",
        },
        "typescript": {
            "extension": ".ts",
            "command": "npx ts-node",
        },
        "ts": {
            "extension": ".ts",
            "command": "npx ts-node",
        },
        "bash": {
            "extension": ".sh",
            "command": "bash",
        },
        "sh": {
            "extension": ".sh",
            "command": "sh",
        },
        "ruby": {
            "extension": ".rb",
            "command": "ruby",
        },
        "php": {
            "extension": ".php",
            "command": "php",
        },
        "go": {
            "extension": ".go",
            "command": "go run",
        },
        "rust": {
            "extension": ".rs",
            "command": "rustc -o /tmp/out && /tmp/out",  # Compile and run
        },
    }
    
    def __init__(
        self,
        provider: "SandboxProvider",
        config: "SandboxConfig | None" = None,
        reuse_sandbox: bool = True,
    ) -> None:
        """Initialize sandbox code backend.
        
        Args:
            provider: Sandbox provider for creating sandboxes
            config: Optional sandbox configuration
            reuse_sandbox: If True, reuse sandbox across executions (default)
        """
        self.provider = provider
        self.config = config
        self.reuse_sandbox = reuse_sandbox
        self._sandbox: "Sandbox | None" = None
        self._exec_counter = 0
    
    @property
    def supported_languages(self) -> list[str]:
        """List of supported programming languages."""
        return list(self.LANGUAGE_CONFIG.keys())
    
    async def _get_sandbox(self) -> "Sandbox":
        """Get or create sandbox instance."""
        if self._sandbox is None or not self.reuse_sandbox:
            self._sandbox = await self.provider.create(self.config)
        return self._sandbox
    
    async def execute(
        self,
        code: str,
        language: str = "python",
        timeout: int = 120,
    ) -> CodeResult:
        """Execute code in the sandbox.
        
        Args:
            code: Source code to execute
            language: Programming language
            timeout: Timeout in seconds
            
        Returns:
            CodeResult with output, error, exit_code
        """
        # Normalize language name
        lang_lower = language.lower()
        if lang_lower not in self.LANGUAGE_CONFIG:
            return CodeResult(
                output="",
                error=f"Unsupported language: {language}. "
                      f"Supported: {', '.join(self.supported_languages)}",
                exit_code=1,
                language=language,
            )
        
        lang_config = self.LANGUAGE_CONFIG[lang_lower]
        sandbox = await self._get_sandbox()
        
        # Generate unique filename
        self._exec_counter += 1
        filename = f"code_{self._exec_counter}{lang_config['extension']}"
        filepath = f"/workspace/{filename}"
        
        # Write code to sandbox
        await sandbox.write_file(filepath, code)
        
        # Build execution command
        command = f"{lang_config['command']} {filepath}"
        
        # Execute
        result = await sandbox.execute(
            command,
            timeout=timeout,
        )
        
        return CodeResult(
            output=result.stdout,
            error=result.stderr,
            exit_code=result.exit_code,
            language=language,
            duration_ms=result.duration_ms,
        )
    
    async def cleanup(self) -> None:
        """Cleanup sandbox resources."""
        if self._sandbox:
            await self._sandbox.destroy()
            self._sandbox = None


__all__ = [
    "SandboxShellBackend",
    "SandboxCodeBackend",
]
