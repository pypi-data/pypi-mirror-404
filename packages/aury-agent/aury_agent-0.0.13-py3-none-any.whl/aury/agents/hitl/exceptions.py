"""HITL (Human-in-the-Loop) exceptions and signals.

These control agent execution flow when human input is needed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Re-export from core.signals
from ..core.signals import HITLSuspend, SuspendSignal


class HITLTimeoutError(Exception):
    """Raised when HITL request times out."""
    
    def __init__(self, request_id: str, timeout: float):
        self.request_id = request_id
        self.timeout = timeout
        super().__init__(f"HITL request {request_id} timed out after {timeout}s")


class HITLCancelledError(Exception):
    """Raised when HITL request is cancelled."""
    
    def __init__(self, request_id: str, reason: str = "cancelled"):
        self.request_id = request_id
        self.reason = reason
        super().__init__(f"HITL request {request_id} cancelled: {reason}")


@dataclass
class HITLRequest:
    """A pending HITL request.
    
    Stored in invocation for persistence.
    """
    hitl_id: str
    hitl_type: str  # ask_user, confirm, permission, external_auth, workflow_human
    
    # Type-specific data
    data: dict[str, Any] = field(default_factory=dict)  # {message, options, ...}
    
    # Context
    tool_name: str | None = None  # If triggered by tool
    node_id: str | None = None    # If triggered by workflow node
    block_id: str | None = None   # Associated UI block
    
    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "hitl_id": self.hitl_id,
            "hitl_type": self.hitl_type,
            "data": self.data,
            "tool_name": self.tool_name,
            "node_id": self.node_id,
            "block_id": self.block_id,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "HITLRequest":
        """Create from dictionary."""
        return cls(
            hitl_id=data["hitl_id"],
            hitl_type=data.get("hitl_type", "ask_user"),
            data=data.get("data", {}),
            tool_name=data.get("tool_name"),
            node_id=data.get("node_id"),
            block_id=data.get("block_id"),
            metadata=data.get("metadata", {}),
        )


@dataclass
class ToolCheckpoint:
    """Tool execution checkpoint for continuation mode.
    
    When a tool raises HITLSuspend with resume_mode="continuation",
    the framework creates a ToolCheckpoint to save the tool's execution
    state. When the user responds, the tool is resumed from this checkpoint.
    
    Use cases:
    - OAuth authorization flow (wait for callback)
    - Payment confirmation (wait for payment gateway)
    - Multi-step wizards with user confirmation
    - External system integration with async callbacks
    
    Storage:
    - Stored via CheckpointBackend (Redis/DB)
    - Keyed by checkpoint_id and callback_id
    - Has TTL for automatic expiration
    
    Example:
        # In tool execution:
        raise HITLSuspend(
            request_id="hitl_123",
            request_type="external_auth",
            resume_mode="continuation",
            tool_state={"step": 2, "partial_data": {...}},
            metadata={"auth_url": "https://...", "callback_id": "cb_456"},
        )
        
        # Framework creates ToolCheckpoint and saves it
        # When callback arrives, framework loads checkpoint and resumes tool
    """
    
    # Identity
    checkpoint_id: str
    callback_id: str | None = None  # For external callback matching
    
    # Association
    session_id: str | None = None
    invocation_id: str | None = None
    block_id: str | None = None  # Frontend HITL block
    
    # Tool execution context
    tool_name: str = ""
    tool_call_id: str = ""
    params: dict[str, Any] = field(default_factory=dict)  # Original params
    tool_state: dict[str, Any] = field(default_factory=dict)  # Internal state
    
    # HITL info
    hitl_id: str = ""
    hitl_type: str = ""  # ask_user, confirm, external_auth, etc.
    
    # Status
    status: str = "pending"  # pending | completed | expired | failed | cancelled
    expires_at: int | None = None  # Unix timestamp
    
    # User response (filled after callback/response)
    user_response: Any | None = None
    error: str | None = None
    
    # Timestamps
    created_at: int = 0
    updated_at: int = 0
    
    def __post_init__(self):
        import time
        now = int(time.time())
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now
    
    @property
    def is_expired(self) -> bool:
        """Check if checkpoint has expired."""
        if self.expires_at is None:
            return False
        import time
        return time.time() > self.expires_at
    
    @property
    def is_pending(self) -> bool:
        """Check if checkpoint is waiting for response."""
        return self.status == "pending" and not self.is_expired
    
    def mark_completed(self, response: Any) -> None:
        """Mark checkpoint as completed with user response."""
        import time
        self.status = "completed"
        self.user_response = response
        self.updated_at = int(time.time())
    
    def mark_failed(self, error: str) -> None:
        """Mark checkpoint as failed."""
        import time
        self.status = "failed"
        self.error = error
        self.updated_at = int(time.time())
    
    def mark_cancelled(self, reason: str = "user_cancelled") -> None:
        """Mark checkpoint as cancelled."""
        import time
        self.status = "cancelled"
        self.error = reason
        self.updated_at = int(time.time())
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "checkpoint_id": self.checkpoint_id,
            "callback_id": self.callback_id,
            "session_id": self.session_id,
            "invocation_id": self.invocation_id,
            "block_id": self.block_id,
            "tool_name": self.tool_name,
            "tool_call_id": self.tool_call_id,
            "params": self.params,
            "tool_state": self.tool_state,
            "hitl_id": self.hitl_id,
            "hitl_type": self.hitl_type,
            "status": self.status,
            "expires_at": self.expires_at,
            "user_response": self.user_response,
            "error": self.error,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ToolCheckpoint":
        """Create from dictionary."""
        return cls(
            checkpoint_id=data["checkpoint_id"],
            callback_id=data.get("callback_id"),
            session_id=data.get("session_id"),
            invocation_id=data.get("invocation_id"),
            block_id=data.get("block_id"),
            tool_name=data.get("tool_name", ""),
            tool_call_id=data.get("tool_call_id", ""),
            params=data.get("params", {}),
            tool_state=data.get("tool_state", {}),
            hitl_id=data.get("hitl_id", ""),
            hitl_type=data.get("hitl_type", ""),
            status=data.get("status", "pending"),
            expires_at=data.get("expires_at"),
            user_response=data.get("user_response"),
            error=data.get("error"),
            created_at=data.get("created_at", 0),
            updated_at=data.get("updated_at", 0),
        )
    
    @classmethod
    def from_hitl_suspend(
        cls,
        suspend: HITLSuspend,
        *,
        tool_call_id: str,
        params: dict[str, Any],
        session_id: str | None = None,
        invocation_id: str | None = None,
        block_id: str | None = None,
        expires_in: int | None = 600,  # Default 10 minutes
    ) -> "ToolCheckpoint":
        """Create checkpoint from HITLSuspend signal.
        
        Args:
            suspend: The HITLSuspend signal
            tool_call_id: Tool call ID
            params: Original tool parameters
            session_id: Session ID
            invocation_id: Invocation ID
            block_id: Frontend block ID
            expires_in: Expiration in seconds (None = no expiration)
        """
        from ..core.types.session import generate_id
        import time
        
        checkpoint_id = suspend.checkpoint_id or generate_id("ckpt")
        callback_id = suspend.metadata.get("callback_id")
        
        expires_at = None
        if expires_in is not None:
            expires_at = int(time.time()) + expires_in
        
        return cls(
            checkpoint_id=checkpoint_id,
            callback_id=callback_id,
            session_id=session_id,
            invocation_id=invocation_id,
            block_id=block_id,
            tool_name=suspend.tool_name or "",
            tool_call_id=tool_call_id,
            params=params,
            tool_state=suspend.tool_state or {},
            hitl_id=suspend.hitl_id,
            hitl_type=suspend.hitl_type,
            expires_at=expires_at,
        )


__all__ = [
    # Signals
    "SuspendSignal",
    "HITLSuspend",
    # Exceptions
    "HITLTimeoutError",
    "HITLCancelledError",
    # Types
    "HITLRequest",
    "ToolCheckpoint",
]
