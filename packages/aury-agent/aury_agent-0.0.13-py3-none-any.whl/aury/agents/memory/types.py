"""Memory type definitions.

Core types for the memory system:
- MemorySummary: Compressed overview of conversation history
- MemoryRecall: Key points extracted from invocations
- MemoryContext: Combined context for LLM (summary + recalls)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class MemorySummary:
    """Compressed overview of conversation history.
    
    Represents the "big picture" of a session's conversation.
    Updated incrementally as invocations complete.
    """
    session_id: str
    content: str  # Summary text
    last_invocation_id: str  # Last invocation included in summary
    updated_at: datetime = field(default_factory=datetime.now)
    token_count: int = 0  # Estimated token count
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "content": self.content,
            "last_invocation_id": self.last_invocation_id,
            "updated_at": self.updated_at.isoformat(),
            "token_count": self.token_count,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MemorySummary":
        return cls(
            session_id=data["session_id"],
            content=data["content"],
            last_invocation_id=data["last_invocation_id"],
            updated_at=datetime.fromisoformat(data["updated_at"]),
            token_count=data.get("token_count", 0),
            metadata=data.get("metadata", {}),
        )


@dataclass
class MemoryRecall:
    """Key point extracted from an invocation.
    
    Represents an important piece of information that should be
    recalled when building LLM context. Linked to specific invocation
    for isolation and revert support.
    """
    id: str
    session_id: str
    invocation_id: str  # Which invocation this came from
    content: str  # Recall content
    importance: float = 0.5  # 0.0 - 1.0, higher = more important
    tags: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "invocation_id": self.invocation_id,
            "content": self.content,
            "importance": self.importance,
            "tags": self.tags,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MemoryRecall":
        return cls(
            id=data["id"],
            session_id=data["session_id"],
            invocation_id=data["invocation_id"],
            content=data["content"],
            importance=data.get("importance", 0.5),
            tags=data.get("tags", []),
            created_at=datetime.fromisoformat(data["created_at"]),
            metadata=data.get("metadata", {}),
        )


@dataclass
class MemoryContext:
    """Combined memory context for LLM.
    
    This is what gets injected into the LLM prompt to provide
    historical context. Contains:
    - summary: High-level overview of conversation
    - recalls: Specific important points
    """
    summary: MemorySummary | None = None
    recalls: list[MemoryRecall] = field(default_factory=list)
    
    def to_system_message(self) -> str:
        """Format as system message content for LLM."""
        parts = []
        
        if self.summary and self.summary.content:
            parts.append(f"## Conversation History Overview\n{self.summary.content}")
        
        if self.recalls:
            recalls_text = "\n".join([
                f"- [{', '.join(r.tags) if r.tags else 'note'}] {r.content}"
                for r in sorted(self.recalls, key=lambda x: x.importance, reverse=True)
            ])
            parts.append(f"## Key Points\n{recalls_text}")
        
        return "\n\n".join(parts) if parts else ""
    
    @property
    def is_empty(self) -> bool:
        """Check if context has any content."""
        return (not self.summary or not self.summary.content) and not self.recalls
    
    @property
    def total_recalls(self) -> int:
        """Get total number of recalls."""
        return len(self.recalls)


__all__ = [
    "MemorySummary",
    "MemoryRecall", 
    "MemoryContext",
]
