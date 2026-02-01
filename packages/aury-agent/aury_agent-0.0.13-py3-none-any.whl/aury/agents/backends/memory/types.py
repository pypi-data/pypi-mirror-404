"""Memory backend types and protocols."""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class MemoryBackend(Protocol):
    """Protocol for long-term memory storage.
    
    Handles persistent memory entries with semantic search capability.
    Used for RAG, knowledge recall, and conversation summaries.
    
    Example usage:
        # Add memory
        memory_id = await backend.add(
            session_id="sess_123",
            content="User prefers dark mode and Python",
            namespace="preferences",
            metadata={"importance": 0.8},
        )
        
        # Search memories
        results = await backend.search(
            session_id="sess_123",
            query="what are user preferences",
            limit=5,
        )
        
        # Delete memories from invocation (for revert)
        await backend.delete_by_invocation("sess_123", "inv_456")
    """
    
    async def add(
        self,
        session_id: str,
        content: str,
        invocation_id: str | None = None,
        namespace: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Add a memory entry.
        
        Args:
            session_id: Session ID
            content: Memory content text
            invocation_id: Optional invocation ID for grouping/revert
            namespace: Optional namespace for categorization
            metadata: Optional metadata (importance, tags, etc.)
            
        Returns:
            Generated memory entry ID
        """
        ...
    
    async def search(
        self,
        session_id: str,
        query: str,
        namespace: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Search memories by semantic relevance.
        
        Args:
            session_id: Session ID
            query: Search query
            namespace: Optional namespace filter
            limit: Max results to return
            
        Returns:
            List of memory dicts with scores, ordered by relevance:
            [{"id": str, "content": str, "score": float, "metadata": dict}, ...]
        """
        ...
    
    async def get(self, id: str) -> dict[str, Any] | None:
        """Get memory by ID.
        
        Args:
            id: Memory entry ID
            
        Returns:
            Memory dict or None if not found
        """
        ...
    
    async def delete(self, id: str) -> bool:
        """Delete a memory entry.
        
        Args:
            id: Memory entry ID
            
        Returns:
            True if deleted, False if not found
        """
        ...
    
    async def delete_by_invocation(
        self,
        session_id: str,
        invocation_id: str,
        namespace: str | None = None,
    ) -> int:
        """Delete memories by invocation (for revert).
        
        Args:
            session_id: Session ID
            invocation_id: Invocation ID to delete
            namespace: Optional namespace filter
            
        Returns:
            Number of memories deleted
        """
        ...
    
    async def list(
        self,
        session_id: str,
        namespace: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List memories for a session (without search).
        
        Args:
            session_id: Session ID
            namespace: Optional namespace filter
            limit: Max results to return
            
        Returns:
            List of memory dicts, ordered by created_at desc
        """
        ...


__all__ = ["MemoryBackend"]
