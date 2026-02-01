"""Sandbox module for isolated code execution environments.

Provides abstracted sandbox interfaces supporting:
- Local Docker-based sandboxes for CLI/development
- Remote API-based sandboxes for SaaS deployment
"""
from .types import ExecutionResult, SandboxConfig, Sandbox, SandboxProvider
from .local import LocalSandbox, LocalSandboxProvider
from .remote import RemoteSandbox, RemoteSandboxProvider

__all__ = [
    # Types
    "ExecutionResult",
    "SandboxConfig",
    "Sandbox",
    "SandboxProvider",
    # Local
    "LocalSandbox",
    "LocalSandboxProvider",
    # Remote
    "RemoteSandbox",
    "RemoteSandboxProvider",
]
