"""SubAgentContextProvider - provides sub-agent configurations."""
from __future__ import annotations

from typing import TYPE_CHECKING

from .base import BaseContextProvider, AgentContext

if TYPE_CHECKING:
    from ..core.context import InvocationContext
    from ..backends.subagent import SubAgentBackend


class SubAgentContextProvider(BaseContextProvider):
    """Sub-agent context provider.
    
    Provides sub-agent configurations. Agent creates DelegateTool from this.
    
    Design: Provider only provides DATA (subagents list).
    Agent decides how to use it (create DelegateTool).
    """
    
    _name = "subagents"
    
    def __init__(self, backend: "SubAgentBackend"):
        """Initialize SubAgentContextProvider.
        
        Args:
            backend: Sub-agent backend for listing available agents
        """
        self.backend = backend
    
    async def fetch(self, ctx: "InvocationContext") -> AgentContext:
        """Fetch sub-agent configurations.
        
        Returns:
            AgentContext with subagents list (NOT DelegateTool)
        """
        agents = await self.backend.list()
        if not agents:
            return AgentContext.empty()
        
        # Return subagents list - Agent will create DelegateTool
        return AgentContext(subagents=list(agents))


__all__ = ["SubAgentContextProvider"]
