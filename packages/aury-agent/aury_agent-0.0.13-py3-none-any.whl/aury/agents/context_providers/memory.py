"""MemoryContextProvider - provides memory context.

This provider ONLY fetches memory context (summary/recalls).
Memory writing is handled by Middleware (e.g., in on_message_save hook).
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from .base import BaseContextProvider, AgentContext

if TYPE_CHECKING:
    from ..core.context import InvocationContext
    from ..memory import MemoryManager


class MemoryContextProvider(BaseContextProvider):
    """Memory context provider.
    
    Provides:
    - system_content: Memory summary and recalls for LLM awareness
    
    Note: Memory WRITING is not done here.
    Use Middleware (on_message_save hook) to write to MemoryManager.
    
    Example:
        provider = MemoryContextProvider(
            memory_manager=my_memory_manager,
            recall_limit=10,
        )
    """
    
    _name = "memory"
    
    def __init__(
        self,
        memory_manager: "MemoryManager",
        recall_limit: int = 10,
    ):
        """Initialize MemoryContextProvider.
        
        Args:
            memory_manager: The underlying MemoryManager
            recall_limit: Max recalls to include in context
        """
        self.memory = memory_manager
        self.recall_limit = recall_limit
    
    async def fetch(self, ctx: "InvocationContext") -> AgentContext:
        """Fetch memory context.
        
        Returns:
            AgentContext with system_content (memory summary/recalls)
        """
        # Get memory context
        memory_ctx = await self.memory.get_context(
            session_id=ctx.session.id,
            recall_limit=self.recall_limit,
        )
        
        # Build system content
        if not memory_ctx or memory_ctx.is_empty:
            return AgentContext.empty()
        
        return AgentContext(
            system_content=memory_ctx.to_system_message(),
        )


__all__ = ["MemoryContextProvider"]
