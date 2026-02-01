"""Code backend for code execution.

Supports executing code in various languages.
No default implementation - user must provide one.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal, Protocol, runtime_checkable


@dataclass
class CodeResult:
    """Result of code execution."""
    output: str
    error: str = ""
    exit_code: int = 0
    language: str = "python"
    duration_ms: int = 0
    
    # Optional: execution artifacts (images, files, etc.)
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    
    @property
    def success(self) -> bool:
        return self.exit_code == 0


@runtime_checkable
class CodeBackend(Protocol):
    """Protocol for code execution.
    
    No default implementation provided.
    Users can implement using:
    - Local subprocess execution
    - E2B code interpreter
    - Jupyter kernel
    - etc.
    """
    
    @property
    def supported_languages(self) -> list[str]:
        """List of supported languages."""
        ...
    
    async def execute(
        self,
        code: str,
        language: str = "python",
        timeout: int = 120,
    ) -> CodeResult:
        """Execute code.
        
        Args:
            code: Code to execute
            language: Programming language
            timeout: Timeout in seconds
            
        Returns:
            CodeResult with output, error, exit_code
        """
        ...


__all__ = ["CodeBackend", "CodeResult"]
