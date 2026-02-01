"""Message backend types and protocols."""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class MessageBackend(Protocol):
    """Protocol for message storage.
    
    Simple interface for message persistence.
    Storage details (raw/truncated handling) are left to the application layer.
    
    Example usage:
        await backend.add(
            session_id="sess_123",
            message={"role": "user", "content": "Hello"},
        )
        
        messages = await backend.get("sess_123", limit=50)
    """
    
    async def add(
        self,
        session_id: str,
        message: dict[str, Any],
        agent_id: str | None = None,
        namespace: str | None = None,
        invocation_id: str | None = None,
    ) -> None:
        """Add a message.
        
        Args:
            session_id: Session ID
            message: Message dict (role, content, tool_call_id, etc.)
            agent_id: Optional agent ID
            namespace: Optional namespace for sub-agent isolation
            invocation_id: Optional invocation ID for grouping
        """
        ...
    
    async def get(
        self,
        session_id: str,
        agent_id: str | None = None,
        namespace: str | None = None,
        limit: int | None = None,
    ) -> list[dict[str, Any]]:
        """Get messages.
        
        Args:
            session_id: Session ID
            agent_id: Optional filter by agent
            namespace: Optional namespace filter
            limit: Max messages to return (None = all)
            
        Returns:
            List of message dicts in chronological order
        """
        ...
    
    async def delete_by_invocation(
        self,
        session_id: str,
        invocation_id: str,
        namespace: str | None = None,
    ) -> int:
        """Delete messages by invocation (for revert).
        
        Args:
            session_id: Session ID
            invocation_id: Invocation ID to delete
            namespace: Optional namespace filter
            
        Returns:
            Number of messages deleted
        """
        ...
    
    async def clear(
        self,
        session_id: str,
        namespace: str | None = None,
    ) -> int:
        """Clear all messages for a session.
        
        Args:
            session_id: Session ID
            namespace: Optional namespace filter
            
        Returns:
            Number of messages deleted
        """
        ...


__all__ = ["MessageBackend"]
