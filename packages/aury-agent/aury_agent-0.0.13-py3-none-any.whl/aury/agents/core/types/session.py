"""Session and Invocation data structures."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4


def generate_id(prefix: str = "") -> str:
    """Generate a unique ID with optional prefix."""
    uid = uuid4().hex[:12]
    return f"{prefix}_{uid}" if prefix else uid


class InvocationState(Enum):
    """Invocation execution state."""
    PENDING = "pending"
    RUNNING = "running"
    SUSPENDED = "suspended"  # HITL waiting
    PAUSED = "paused"  # User paused
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    ABORTED = "aborted"  # User stopped
    SWITCHED = "switched"  # User switched agent


class InvocationMode(Enum):
    """Invocation mode."""
    ROOT = "root"  # Root invocation
    DELEGATED = "delegated"  # Delegated sub-agent
    # Note: EMBEDDED doesn't create new Invocation, uses parent's


@dataclass
class ControlFrame:
    """Control frame for tracking delegated agent in session."""
    agent_id: str
    invocation_id: str
    entered_at: datetime = field(default_factory=datetime.now)
    parent_invocation_id: str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "invocation_id": self.invocation_id,
            "entered_at": self.entered_at.isoformat(),
            "parent_invocation_id": self.parent_invocation_id,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ControlFrame":
        return cls(
            agent_id=data["agent_id"],
            invocation_id=data["invocation_id"],
            entered_at=datetime.fromisoformat(data["entered_at"]),
            parent_invocation_id=data.get("parent_invocation_id"),
        )


@dataclass
class Session:
    """Session - container for conversations.
    
    A Session represents a conversation thread that can contain multiple
    invocations (turns). Sessions can be nested (parent_id) for sub-agent scenarios.
    """
    id: str = field(default_factory=lambda: generate_id("sess"))
    root_agent_id: str = ""  # Root agent for this session
    parent_id: str | None = None  # For forked sessions
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)  # title, etc.
    is_active: bool = True
    
    # Control stack for DELEGATED mode
    control_stack: list[ControlFrame] = field(default_factory=list)
    
    # Revert state (if currently in reverted state)
    revert: dict[str, Any] | None = None
    
    @property
    def active_agent_id(self) -> str:
        """Get the currently active agent (top of control stack or root)."""
        if self.control_stack:
            return self.control_stack[-1].agent_id
        return self.root_agent_id
    
    def push_control(self, frame: ControlFrame) -> None:
        """Push control frame when delegating to sub-agent."""
        self.control_stack.append(frame)
        self.updated_at = datetime.now()
    
    def pop_control(self) -> ControlFrame | None:
        """Pop control frame when sub-agent returns control."""
        if self.control_stack:
            self.updated_at = datetime.now()
            return self.control_stack.pop()
        return None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "root_agent_id": self.root_agent_id,
            "parent_id": self.parent_id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
            "is_active": self.is_active,
            "control_stack": [f.to_dict() for f in self.control_stack],
            "revert": self.revert,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Session":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            root_agent_id=data.get("root_agent_id", ""),
            parent_id=data.get("parent_id"),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            metadata=data.get("metadata", {}),
            is_active=data.get("is_active", True),
            control_stack=[ControlFrame.from_dict(f) for f in data.get("control_stack", [])],
            revert=data.get("revert"),
        )


@dataclass
class Invocation:
    """A single invocation (turn) within a session.
    
    An Invocation represents one user input and the agent's response,
    including all tool calls and intermediate steps.
    """
    id: str = field(default_factory=lambda: generate_id("inv"))
    session_id: str = ""
    agent_id: str = ""  # Which agent executes this invocation
    mode: InvocationMode = InvocationMode.ROOT  # ROOT or DELEGATED
    state: InvocationState = InvocationState.PENDING
    
    # Relationship (tree structure)
    parent_invocation_id: str | None = None  # Parent invocation (for DELEGATED)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    started_at: datetime | None = None
    finished_at: datetime | None = None
    
    # Agent state for resumption
    agent_state: dict[str, Any] | None = None
    pending_tool_ids: list[str] = field(default_factory=list)
    
    # Execution info
    step_count: int = 0
    snapshot_id: str | None = None  # Pre-execution snapshot for revert
    
    # Error info
    error: str | None = None
    
    # Branch (for state isolation)
    branch: str | None = None
    
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def mark_started(self) -> None:
        """Mark invocation as started."""
        self.state = InvocationState.RUNNING
        self.started_at = datetime.now()
    
    def mark_completed(self) -> None:
        """Mark invocation as completed."""
        self.state = InvocationState.COMPLETED
        self.finished_at = datetime.now()
    
    def mark_failed(self, error: str) -> None:
        """Mark invocation as failed."""
        self.state = InvocationState.FAILED
        self.error = error
        self.finished_at = datetime.now()
    
    def mark_cancelled(self) -> None:
        """Mark invocation as cancelled."""
        self.state = InvocationState.CANCELLED
        self.finished_at = datetime.now()
    
    def mark_aborted(self) -> None:
        """Mark invocation as aborted by user."""
        self.state = InvocationState.ABORTED
        self.finished_at = datetime.now()
    
    def mark_switched(self) -> None:
        """Mark invocation as ended due to agent switch."""
        self.state = InvocationState.SWITCHED
        self.finished_at = datetime.now()
    
    def mark_paused(self) -> None:
        """Mark invocation as paused."""
        self.state = InvocationState.PAUSED
    
    def mark_suspended(self) -> None:
        """Mark invocation as suspended (HITL)."""
        self.state = InvocationState.SUSPENDED
    
    @property
    def duration_ms(self) -> int | None:
        """Get execution duration in milliseconds."""
        if self.started_at and self.finished_at:
            return int((self.finished_at - self.started_at).total_seconds() * 1000)
        return None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "mode": self.mode.value,
            "state": self.state.value,
            "parent_invocation_id": self.parent_invocation_id,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "agent_state": self.agent_state,
            "pending_tool_ids": self.pending_tool_ids,
            "step_count": self.step_count,
            "snapshot_id": self.snapshot_id,
            "error": self.error,
            "branch": self.branch,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Invocation":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            session_id=data["session_id"],
            agent_id=data.get("agent_id", ""),
            mode=InvocationMode(data.get("mode", "root")),
            state=InvocationState(data["state"]),
            parent_invocation_id=data.get("parent_invocation_id"),
            created_at=datetime.fromisoformat(data["created_at"]),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            finished_at=datetime.fromisoformat(data["finished_at"]) if data.get("finished_at") else None,
            agent_state=data.get("agent_state"),
            pending_tool_ids=data.get("pending_tool_ids", []),
            step_count=data.get("step_count", 0),
            snapshot_id=data.get("snapshot_id"),
            error=data.get("error"),
            branch=data.get("branch"),
            metadata=data.get("metadata", {}),
        )
