"""In-memory message backend implementation."""
from __future__ import annotations

from datetime import datetime
from typing import Any


class InMemoryMessageBackend:
    """In-memory implementation of MessageBackend.
    
    Simple in-memory storage for testing and single-process use cases.
    """
    
    def __init__(self) -> None:
        # Key format: "{session_id}" or "{session_id}:{namespace}"
        # Value: list of message dicts
        self._messages: dict[str, list[dict[str, Any]]] = {}
    
    def _make_key(self, session_id: str, namespace: str | None) -> str:
        if namespace:
            return f"{session_id}:{namespace}"
        return session_id
    
    async def add(
        self,
        session_id: str,
        message: dict[str, Any],
        agent_id: str | None = None,
        namespace: str | None = None,
        invocation_id: str | None = None,
    ) -> None:
        """Add a message."""
        key = self._make_key(session_id, namespace)
        
        if key not in self._messages:
            self._messages[key] = []
        
        # Add metadata
        msg = {
            **message,
            "agent_id": agent_id,
            "invocation_id": invocation_id,
            "created_at": datetime.now().isoformat(),
        }
        self._messages[key].append(msg)
    
    async def get(
        self,
        session_id: str,
        agent_id: str | None = None,
        namespace: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Get messages."""
        key = self._make_key(session_id, namespace)
        messages = self._messages.get(key, [])
        
        # Filter by agent_id if specified
        if agent_id:
            messages = [m for m in messages if m.get("agent_id") == agent_id]
        
        # Apply limit (return last N messages)
        if limit:
            messages = messages[-limit:]
        
        return messages.copy()
    
    async def delete_by_invocation(
        self,
        session_id: str,
        invocation_id: str,
        namespace: str | None = None,
    ) -> int:
        """Delete messages by invocation."""
        key = self._make_key(session_id, namespace)
        
        if key not in self._messages:
            return 0
        
        original = self._messages[key]
        self._messages[key] = [m for m in original if m.get("invocation_id") != invocation_id]
        return len(original) - len(self._messages[key])
    
    async def clear(
        self,
        session_id: str,
        namespace: str | None = None,
    ) -> int:
        """Clear all messages for a session."""
        key = self._make_key(session_id, namespace)
        
        if key not in self._messages:
            return 0
        
        deleted = len(self._messages[key])
        del self._messages[key]
        return deleted


__all__ = ["InMemoryMessageBackend"]
