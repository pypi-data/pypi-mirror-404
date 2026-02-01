"""Recall data structures for session memory.

Recalls are key points within a session:
- Extracted from conversation (user info, preferences, decisions)
- Used for quick context retrieval
- Support revert (linked to invocation_id)
- Support SubAgent isolation (branch field)

Unlike Knowledge (cross-session, user-defined), Recalls are:
- Session-scoped
- Framework-managed
- Automatically linked to invocations for revert
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .session import generate_id


@dataclass
class Recall:
    """A recall point (session memory).
    
    Captures important information from the conversation
    for quick retrieval and context building.
    """
    id: str = field(default_factory=lambda: generate_id("rcl"))
    
    # Content
    content: str = ""
    importance: float = 0.5  # 0.0 - 1.0
    
    # Classification
    category: str | None = None  # user_info, preference, task, decision, fact...
    tags: list[str] = field(default_factory=list)
    
    # Session context (for revert)
    session_id: str = ""
    invocation_id: str = ""  # Source invocation (used for revert)
    
    # SubAgent isolation
    branch: str | None = None
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: datetime | None = None  # Optional TTL
    
    # Extension
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "content": self.content,
            "importance": self.importance,
            "category": self.category,
            "tags": self.tags,
            "session_id": self.session_id,
            "invocation_id": self.invocation_id,
            "branch": self.branch,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Recall":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            content=data.get("content", ""),
            importance=data.get("importance", 0.5),
            category=data.get("category"),
            tags=data.get("tags", []),
            session_id=data.get("session_id", ""),
            invocation_id=data.get("invocation_id", ""),
            branch=data.get("branch"),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            metadata=data.get("metadata", {}),
        )


@dataclass
class Summary:
    """Session summary (compressed history).
    
    Reduces token consumption by summarizing old messages.
    """
    id: str = field(default_factory=lambda: generate_id("sum"))
    
    # Content
    content: str = ""
    
    # Coverage
    session_id: str = ""
    covers_until_invocation: str = ""  # Summary covers up to this invocation
    compressed_message_count: int = 0
    
    # Token stats
    token_count: int = 0
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime | None = None
    
    # Extension
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "content": self.content,
            "session_id": self.session_id,
            "covers_until_invocation": self.covers_until_invocation,
            "compressed_message_count": self.compressed_message_count,
            "token_count": self.token_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Summary":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            content=data.get("content", ""),
            session_id=data.get("session_id", ""),
            covers_until_invocation=data.get("covers_until_invocation", ""),
            compressed_message_count=data.get("compressed_message_count", 0),
            token_count=data.get("token_count", 0),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
            metadata=data.get("metadata", {}),
        )


__all__ = ["Recall", "Summary"]
