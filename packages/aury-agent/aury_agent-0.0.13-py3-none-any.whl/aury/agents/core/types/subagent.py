"""SubAgent input/output types for agent delegation."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Literal, TypedDict, NotRequired, TYPE_CHECKING

if TYPE_CHECKING:
    from .message import Message


class SubAgentMode(Enum):
    """SubAgent execution mode."""
    EMBEDDED = "embedded"    # Embedded execution, shares parent's invocation
    DELEGATED = "delegated"  # Delegated execution, creates new invocation


class SubAgentInput(TypedDict):
    """Input for SubAgent invocation.
    
    LLM 传的输入:
    - agent: 调用哪个 agent
    - task_context: 任务上下文（用户意图、背景、要求等）
    - artifact_refs: 相关资料引用
    
    其他配置（mode, inherit_messages, summary_mode 等）
    在 AgentConfig 中定义，不由 LLM 传入。
    """
    # Required
    agent: str  # Agent key
    
    # Task context - 尽可能描述用户意图、背景信息、具体要求
    task_context: NotRequired[str]
    
    # Artifact references - 相关资料 [{id, summary}, ...]
    artifact_refs: NotRequired[list[dict[str, str]]]


@dataclass
class SubAgentMetadata:
    """Metadata about sub-agent execution."""
    child_invocation_id: str
    agent_name: str
    agent_type: str  # "react" | "workflow"
    steps: int = 0
    duration_ms: int = 0
    token_usage: dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "child_invocation_id": self.child_invocation_id,
            "agent_name": self.agent_name,
            "agent_type": self.agent_type,
            "steps": self.steps,
            "duration_ms": self.duration_ms,
            "token_usage": self.token_usage,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SubAgentMetadata":
        return cls(
            child_invocation_id=data["child_invocation_id"],
            agent_name=data["agent_name"],
            agent_type=data.get("agent_type", "react"),
            steps=data.get("steps", 0),
            duration_ms=data.get("duration_ms", 0),
            token_usage=data.get("token_usage", {}),
        )


@dataclass
class SubAgentResult:
    """Result returned by sub-agent to parent agent.
    
    Contains both text output (for LLM context) and structured data.
    """
    # Text output (summary for LLM)
    output: str
    
    # Execution status
    status: Literal["completed", "aborted", "failed", "switched"]
    
    # Structured data (optional)
    data: dict[str, Any] | None = None
    
    # State changes to merge back to parent
    state_updates: dict[str, Any] | None = None
    
    # Error info (when failed)
    error: str | None = None
    
    # Execution metadata
    metadata: SubAgentMetadata | None = None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "output": self.output,
            "status": self.status,
            "data": self.data,
            "state_updates": self.state_updates,
            "error": self.error,
            "metadata": self.metadata.to_dict() if self.metadata else None,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SubAgentResult":
        return cls(
            output=data["output"],
            status=data["status"],
            data=data.get("data"),
            state_updates=data.get("state_updates"),
            error=data.get("error"),
            metadata=SubAgentMetadata.from_dict(data["metadata"]) if data.get("metadata") else None,
        )
    
    @classmethod
    def completed(
        cls,
        output: str,
        data: dict[str, Any] | None = None,
        state_updates: dict[str, Any] | None = None,
        metadata: SubAgentMetadata | None = None,
    ) -> "SubAgentResult":
        """Create a completed result."""
        return cls(
            output=output,
            status="completed",
            data=data,
            state_updates=state_updates,
            metadata=metadata,
        )
    
    @classmethod
    def failed(cls, error: str, output: str = "") -> "SubAgentResult":
        """Create a failed result."""
        return cls(
            output=output or f"SubAgent failed: {error}",
            status="failed",
            error=error,
        )
    
    @classmethod
    def aborted(cls, output: str = "SubAgent was aborted") -> "SubAgentResult":
        """Create an aborted result."""
        return cls(output=output, status="aborted")


__all__ = [
    "SubAgentMode",
    "SubAgentInput",
    "SubAgentMetadata",
    "SubAgentResult",
]
