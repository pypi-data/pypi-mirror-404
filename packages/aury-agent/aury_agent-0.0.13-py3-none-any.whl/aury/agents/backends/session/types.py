"""Session backend types and protocols."""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable, TYPE_CHECKING

if TYPE_CHECKING:
    from ...core.context import InvocationContext


@runtime_checkable
class SessionBackend(Protocol):
    """Protocol for session management.
    
    Sessions represent a conversation scope. Each session can contain
    multiple invocations (user turns).
    
    All methods accept an optional `ctx` (InvocationContext) parameter.
    When ctx is provided, session_id/user_id can be extracted from it.
    
    Example usage:
        # With explicit params
        await backend.create("sess_123", {"root_agent_id": "agent"}, user_id="user_1")
        
        # With ctx (auto-extract session_id)
        await backend.get(ctx=ctx)  # uses ctx.session_id
        
        # List user's sessions
        sessions = await backend.list(user_id="user_1")
    """
    
    async def create(
        self,
        data: dict[str, Any],
        *,
        id: str | None = None,
        user_id: str | None = None,
        ctx: "InvocationContext | None" = None,
    ) -> str:
        """Create a new session.
        
        Args:
            data: Session data (root_agent_id, metadata, etc.)
            id: Session ID (auto-generated if None)
            user_id: Optional user ID for multi-tenant isolation
            ctx: Optional InvocationContext
            
        Returns:
            Created session ID
        """
        ...
    
    async def get(
        self,
        id: str | None = None,
        *,
        ctx: "InvocationContext | None" = None,
    ) -> dict[str, Any] | None:
        """Get session by ID.
        
        Args:
            id: Session ID (or extracted from ctx.session_id)
            ctx: Optional InvocationContext
            
        Returns:
            Session data dict or None if not found
        """
        ...
    
    async def update(
        self,
        data: dict[str, Any],
        *,
        id: str | None = None,
        ctx: "InvocationContext | None" = None,
    ) -> None:
        """Update session data.
        
        Args:
            data: Fields to update (partial update)
            id: Session ID (or extracted from ctx.session_id)
            ctx: Optional InvocationContext
        """
        ...
    
    async def delete(
        self,
        id: str | None = None,
        *,
        ctx: "InvocationContext | None" = None,
    ) -> bool:
        """Delete a session.
        
        Args:
            id: Session ID (or extracted from ctx.session_id)
            ctx: Optional InvocationContext
            
        Returns:
            True if deleted, False if not found
        """
        ...
    
    async def list(
        self,
        *,
        user_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
        ctx: "InvocationContext | None" = None,
    ) -> list[dict[str, Any]]:
        """List sessions.
        
        Args:
            user_id: Optional filter by user
            limit: Max sessions to return
            offset: Offset for pagination
            ctx: Optional InvocationContext
            
        Returns:
            List of session data dicts
        """
        ...


__all__ = ["SessionBackend"]
