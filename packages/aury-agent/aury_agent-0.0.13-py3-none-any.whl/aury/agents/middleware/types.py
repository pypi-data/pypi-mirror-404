"""Middleware types and data classes."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class TriggerMode(Enum):
    """Middleware trigger mode for streaming."""
    EVERY_TOKEN = "every_token"  # Trigger on every token
    EVERY_N_TOKENS = "every_n_tokens"  # Trigger every N tokens
    ON_BOUNDARY = "on_boundary"  # Trigger on sentence/paragraph boundaries


class HookAction(Enum):
    """Control flow action returned by lifecycle hooks.
    
    CONTINUE: Proceed with normal execution
    SKIP: Skip the current operation (tool call, etc.)
    RETRY: Retry the current operation (with modified params)
    STOP: Stop the agent execution entirely
    """
    CONTINUE = "continue"
    SKIP = "skip"
    RETRY = "retry"
    STOP = "stop"


@dataclass
class HookResult:
    """Result from a lifecycle hook.
    
    Attributes:
        action: Control flow action
        modified_data: Modified data (for RETRY action)
        message: Optional message explaining the action
        metadata: Additional metadata
    """
    action: HookAction = HookAction.CONTINUE
    modified_data: Any = None
    message: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def proceed(cls) -> "HookResult":
        """Continue with normal execution."""
        return cls(action=HookAction.CONTINUE)
    
    @classmethod
    def skip(cls, message: str | None = None) -> "HookResult":
        """Skip the current operation."""
        return cls(action=HookAction.SKIP, message=message)
    
    @classmethod
    def retry(cls, modified_data: Any = None, message: str | None = None) -> "HookResult":
        """Retry with optional modified data."""
        return cls(action=HookAction.RETRY, modified_data=modified_data, message=message)
    
    @classmethod
    def stop(cls, message: str | None = None) -> "HookResult":
        """Stop agent execution."""
        return cls(action=HookAction.STOP, message=message)


@dataclass
class MiddlewareConfig:
    """Middleware configuration."""
    trigger_mode: TriggerMode = TriggerMode.EVERY_TOKEN
    trigger_n: int = 10  # For EVERY_N_TOKENS mode
    async_mode: bool = True  # Execute asynchronously
    priority: int = 0  # Lower priority runs first
    inherit: bool = True  # Whether to pass to sub-agents (can be overridden at use() time)


__all__ = [
    "TriggerMode",
    "HookAction",
    "HookResult",
    "MiddlewareConfig",
]
