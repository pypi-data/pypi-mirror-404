"""Invocation backend types and protocols."""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class InvocationBackend(Protocol):
    """Protocol for invocation management.
    
    An invocation represents a single user turn / agent execution cycle.
    Each session can contain multiple invocations.
    
    Example usage:
        # Create invocation
        await backend.create(
            id="inv_123",
            session_id="sess_456",
            data={"state": "running", "agent_id": "react_agent"},
        )
        
        # Get invocation
        inv = await backend.get("inv_123")
        
        # Update state
        await backend.update("inv_123", {"state": "completed"})
        
        # List by session
        invocations = await backend.list_by_session("sess_456")
    """
    
    async def create(
        self,
        id: str,
        session_id: str,
        data: dict[str, Any],
        agent_id: str | None = None,
    ) -> None:
        """Create a new invocation.
        
        Args:
            id: Invocation ID
            session_id: Parent session ID
            data: Invocation data (state, metadata, etc.)
            agent_id: Optional agent ID
        """
        ...
    
    async def get(self, id: str) -> dict[str, Any] | None:
        """Get invocation by ID.
        
        Args:
            id: Invocation ID
            
        Returns:
            Invocation data dict or None if not found
        """
        ...
    
    async def update(self, id: str, data: dict[str, Any]) -> None:
        """Update invocation data.
        
        Args:
            id: Invocation ID
            data: Fields to update (partial update)
        """
        ...
    
    async def delete(self, id: str) -> bool:
        """Delete an invocation.
        
        Args:
            id: Invocation ID
            
        Returns:
            True if deleted, False if not found
        """
        ...
    
    async def list_by_session(
        self,
        session_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List invocations for a session.
        
        Args:
            session_id: Session ID to filter by
            limit: Max invocations to return
            offset: Offset for pagination
            
        Returns:
            List of invocation data dicts, ordered by created_at desc
        """
        ...
    
    async def get_latest(self, session_id: str) -> dict[str, Any] | None:
        """Get the latest invocation for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            Latest invocation data or None
        """
        ...


__all__ = ["InvocationBackend"]
