"""Message store protocol and implementations.

Note: For production use, prefer MessageBackend (backends/message/).
This module provides a simple protocol and in-memory implementation for testing.
"""
from __future__ import annotations

from typing import Protocol, runtime_checkable

from .types import Message


@runtime_checkable
class MessageStore(Protocol):
    """Protocol for message storage.
    
    Note: For production, use MessageBackend instead.
    This protocol is kept for backward compatibility.
    """
    
    async def add(
        self,
        session_id: str,
        message: Message,
        namespace: str | None = None,
    ) -> None:
        """Add a message to session history."""
        ...
    
    async def get_all(
        self,
        session_id: str,
        namespace: str | None = None,
    ) -> list[Message]:
        """Get all messages for a session."""
        ...
    
    async def get_recent(
        self,
        session_id: str,
        limit: int,
        namespace: str | None = None,
    ) -> list[Message]:
        """Get recent messages for a session."""
        ...
    
    async def delete_by_invocation(
        self,
        session_id: str,
        invocation_id: str,
        namespace: str | None = None,
    ) -> int:
        """Delete messages by invocation ID."""
        ...


class InMemoryMessageStore:
    """In-memory message store for testing."""
    
    def __init__(self) -> None:
        # Key format: "session_id" or "session_id:namespace"
        self._messages: dict[str, list[Message]] = {}
    
    def _make_key(self, session_id: str, namespace: str | None) -> str:
        if namespace:
            return f"{session_id}:{namespace}"
        return session_id
    
    async def add(
        self,
        session_id: str,
        message: Message,
        namespace: str | None = None,
    ) -> None:
        from ..core.logging import storage_logger as logger
        
        key = self._make_key(session_id, namespace)
        if key not in self._messages:
            self._messages[key] = []
        self._messages[key].append(message)
        
        logger.debug(
            "Message stored",
            extra={
                "session_id": session_id,
                "invocation_id": getattr(message, "invocation_id", None),
                "role": getattr(message, "role", None),
                "namespace": namespace,
            },
        )
    
    async def get_all(
        self,
        session_id: str,
        namespace: str | None = None,
    ) -> list[Message]:
        key = self._make_key(session_id, namespace)
        return self._messages.get(key, []).copy()
    
    async def get_recent(
        self,
        session_id: str,
        limit: int,
        namespace: str | None = None,
    ) -> list[Message]:
        key = self._make_key(session_id, namespace)
        messages = self._messages.get(key, [])
        return messages[-limit:] if limit else messages.copy()
    
    async def delete_by_invocation(
        self,
        session_id: str,
        invocation_id: str,
        namespace: str | None = None,
    ) -> int:
        from ..core.logging import storage_logger as logger
        
        key = self._make_key(session_id, namespace)
        if key not in self._messages:
            return 0
        
        original = self._messages[key]
        self._messages[key] = [
            m for m in original if m.invocation_id != invocation_id
        ]
        deleted_count = len(original) - len(self._messages[key])
        
        if deleted_count > 0:
            logger.debug(
                "Messages deleted by invocation",
                extra={
                    "session_id": session_id,
                    "invocation_id": invocation_id,
                    "count": deleted_count,
                },
            )
        
        return deleted_count


__all__ = [
    "MessageStore",
    "InMemoryMessageStore",
]
