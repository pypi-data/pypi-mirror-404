"""HITL backend types and protocols."""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class HITLBackend(Protocol):
    """Protocol for HITL (Human-in-the-Loop) persistence.
    
    Stores HITL requests and user responses for:
    - ask_user, confirm, permission requests
    - External auth callbacks
    - Workflow human tasks
    
    Example usage:
        # Create HITL request
        await backend.create(
            hitl_id="hitl_123",
            hitl_type="ask_user",
            session_id="sess_456",
            invocation_id="inv_789",
            data={"message": "What do you want?", "options": ["A", "B"]},
        )
        
        # Get HITL
        hitl = await backend.get("hitl_123")
        
        # Respond
        await backend.respond("hitl_123", {"answer": "A"})
    """
    
    async def create(
        self,
        *,
        hitl_id: str,
        hitl_type: str,
        session_id: str,
        invocation_id: str,
        data: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        block_id: str | None = None,
        resume_mode: str = "response",
        tool_state: dict[str, Any] | None = None,
        checkpoint_id: str | None = None,
        tool_name: str | None = None,
        tool_call_id: str | None = None,
        node_id: str | None = None,
        expires_at: int | None = None,
    ) -> None:
        """Create a new HITL record.
        
        Args:
            hitl_id: Unique HITL identifier
            hitl_type: Type of HITL (ask_user, confirm, permission, etc.)
            session_id: Parent session ID
            invocation_id: Parent invocation ID
            data: Type-specific data (message, options, etc.)
            metadata: Additional metadata
            block_id: Associated UI block ID
            resume_mode: How to resume ("response" or "continuation")
            tool_state: Tool internal state for continuation
            checkpoint_id: Checkpoint ID for continuation
            tool_name: Tool that triggered HITL
            tool_call_id: Tool call ID
            node_id: Workflow node ID
            expires_at: Expiration timestamp (unix)
        """
        ...
    
    async def get(self, hitl_id: str) -> dict[str, Any] | None:
        """Get HITL record by ID.
        
        Args:
            hitl_id: HITL identifier
            
        Returns:
            HITL data dict or None if not found
        """
        ...
    
    async def respond(
        self,
        hitl_id: str,
        user_response: dict[str, Any],
    ) -> None:
        """Record user response to HITL.
        
        Args:
            hitl_id: HITL identifier
            user_response: User's response data
        """
        ...
    
    async def cancel(self, hitl_id: str) -> None:
        """Cancel a pending HITL request.
        
        Args:
            hitl_id: HITL identifier
        """
        ...
    
    async def get_pending_by_session(
        self,
        session_id: str,
    ) -> list[dict[str, Any]]:
        """Get all pending HITL for a session.
        
        Args:
            session_id: Session ID
            
        Returns:
            List of pending HITL records
        """
        ...
    
    async def get_pending_by_invocation(
        self,
        invocation_id: str,
    ) -> list[dict[str, Any]]:
        """Get all pending HITL for an invocation.
        
        Args:
            invocation_id: Invocation ID
            
        Returns:
            List of pending HITL records
        """
        ...


__all__ = ["HITLBackend"]
