"""Control flow signals for agent execution.

These are NOT exceptions - they are control flow signals that inherit from
BaseException to avoid being caught by generic `except Exception` handlers.

Similar to KeyboardInterrupt and SystemExit, these signals control execution
flow rather than indicate errors.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class SuspendSignal(BaseException):
    """Base class for suspension signals.
    
    Signals that execution should be suspended (not failed).
    Inherits from BaseException so `except Exception` won't catch it.
    
    Usage:
        try:
            await agent.run()
        except SuspendSignal as s:
            # Handle suspension (HITL, pause, etc.)
            handle_suspend(s)
        except Exception as e:
            # Handle actual errors
            handle_error(e)
    """
    pass


@dataclass
class HITLSuspend(SuspendSignal):
    """Signal for Human-in-the-Loop suspension.
    
    Raised when agent needs human input to continue.
    Contains all information needed to:
    1. Display the request to user
    2. Resume execution after user responds
    
    Supports two resume modes:
    - "response": (Default) User response is returned to LLM as tool output.
    - "continuation": Tool execution is resumed from checkpoint,
      user response is passed to tool to continue processing.
    
    Attributes:
        hitl_id: Unique ID for matching response
        hitl_type: Type of HITL (ask_user, confirm, external_auth, etc.)
        data: Type-specific data (message, options, etc.)
        node_id: Workflow node ID if triggered from workflow
        tool_name: Tool name if triggered from tool
        block_id: Associated UI block ID
        metadata: Additional context
        resume_mode: How to resume after user responds
        tool_state: Tool internal state for continuation mode
        checkpoint_id: Unique ID for tool checkpoint
    """
    hitl_id: str
    hitl_type: str = "ask_user"
    data: dict[str, Any] = field(default_factory=dict)  # Type-specific: {message, options, ...}
    node_id: str | None = None
    tool_name: str | None = None
    block_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    # Continuation support
    resume_mode: str = "response"  # "response" | "continuation"
    tool_state: dict[str, Any] | None = None  # Internal state for continuation
    checkpoint_id: str | None = None  # Checkpoint ID for restoration
    
    def __post_init__(self):
        # Initialize BaseException with a message
        super().__init__(f"HITL suspend: {self.hitl_type} ({self.hitl_id})")
    
    @property
    def is_continuation(self) -> bool:
        """Check if this suspend requires continuation mode."""
        return self.resume_mode == "continuation"
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage/transmission."""
        return {
            "hitl_id": self.hitl_id,
            "hitl_type": self.hitl_type,
            "data": self.data,
            "node_id": self.node_id,
            "tool_name": self.tool_name,
            "block_id": self.block_id,
            "metadata": self.metadata,
            "resume_mode": self.resume_mode,
            "tool_state": self.tool_state,
            "checkpoint_id": self.checkpoint_id,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HITLSuspend":
        """Create from dictionary."""
        return cls(
            hitl_id=data["hitl_id"],
            hitl_type=data.get("hitl_type", "ask_user"),
            data=data.get("data", {}),
            node_id=data.get("node_id"),
            tool_name=data.get("tool_name"),
            block_id=data.get("block_id"),
            metadata=data.get("metadata", {}),
            resume_mode=data.get("resume_mode", "response"),
            tool_state=data.get("tool_state"),
            checkpoint_id=data.get("checkpoint_id"),
        )


class PauseSuspend(SuspendSignal):
    """Signal for manual pause (user-initiated).
    
    Raised when user requests to pause execution.
    """
    
    def __init__(self, reason: str = "User requested pause"):
        self.reason = reason
        super().__init__(reason)


__all__ = [
    "SuspendSignal",
    "HITLSuspend",
    "PauseSuspend",
]
