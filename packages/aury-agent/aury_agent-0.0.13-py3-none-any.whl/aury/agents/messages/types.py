"""Message type definitions.

Core types for the message system:
- Message: A single message in conversation history
- MessageRole: User/Assistant/Tool/System
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class MessageRole(Enum):
    """Message role types."""
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    SYSTEM = "system"


@dataclass
class Message:
    """A message in conversation history.
    
    Attributes:
        role: Message role (user/assistant/tool/system)
        content: Message content (string or content parts)
        invocation_id: Which invocation this message belongs to
        tool_call_id: Tool call ID (for tool messages)
        created_at: When the message was created
        metadata: Additional metadata
    """
    role: str
    content: str | list[dict[str, Any]]
    invocation_id: str = ""
    tool_call_id: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dict for storage."""
        result = {
            "role": self.role,
            "content": self.content,
            "invocation_id": self.invocation_id,
            "created_at": self.created_at.isoformat(),
        }
        if self.tool_call_id:
            result["tool_call_id"] = self.tool_call_id
        if self.metadata:
            result["metadata"] = self.metadata
        return result
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Message":
        """Create from dict."""
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now()
        
        return cls(
            role=data["role"],
            content=data["content"],
            invocation_id=data.get("invocation_id", ""),
            tool_call_id=data.get("tool_call_id"),
            created_at=created_at,
            metadata=data.get("metadata", {}),
        )
    
    def to_llm_format(self) -> dict[str, Any]:
        """Convert to LLM message format."""
        result: dict[str, Any] = {
            "role": self.role,
            "content": self.content,
        }
        if self.tool_call_id:
            result["tool_call_id"] = self.tool_call_id
        return result


__all__ = [
    "MessageRole",
    "Message",
]
