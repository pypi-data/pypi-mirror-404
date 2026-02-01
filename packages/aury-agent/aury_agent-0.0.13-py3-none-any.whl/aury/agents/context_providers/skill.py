"""SkillContextProvider - provides skill definitions."""
from __future__ import annotations

from typing import TYPE_CHECKING

from .base import BaseContextProvider, AgentContext

if TYPE_CHECKING:
    from ..core.context import InvocationContext
    from ..skill import SkillLoader


class SkillContextProvider(BaseContextProvider):
    """Skill context provider.
    
    Provides skill definitions and formatted descriptions.
    
    Design: Provider provides skills list AND system_content.
    Agent can use skills list for further processing.
    """
    
    _name = "skills"
    
    def __init__(self, loader: "SkillLoader"):
        """Initialize SkillContextProvider.
        
        Args:
            loader: Skill loader for formatting skills
        """
        self.loader = loader
    
    async def fetch(self, ctx: "InvocationContext") -> AgentContext:
        """Fetch skill context.
        
        Returns:
            AgentContext with skills list and system_content
        """
        skills = self.loader.skills
        skills_prompt = self.loader.format_for_prompt()
        
        if not skills:
            return AgentContext.empty()
        
        return AgentContext(
            skills=list(skills),
            system_content=skills_prompt if skills_prompt else None,
        )


__all__ = ["SkillContextProvider"]
