"""Shell backend for command execution.

Supports different execution environments:
- Local shell
- Docker/nsjail sandbox
- E2B cloud sandbox
"""
from .types import ShellBackend, ShellResult
from .local import LocalShellBackend

__all__ = ["ShellBackend", "ShellResult", "LocalShellBackend"]
