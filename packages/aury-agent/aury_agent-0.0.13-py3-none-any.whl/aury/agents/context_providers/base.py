"""Base ContextProvider protocol and AgentContext.

ContextProvider is the unified abstraction for providing LLM context.
All context sources (memory, artifacts, skills, subagents)
are ContextProviders that implement fetch(ctx) -> AgentContext.

Design principle:
- Providers only provide DATA (content, subagents list, skills list, etc.)
- Agent consumes this data and decides how to use it (e.g., create DelegateTool)
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

if TYPE_CHECKING:
    from ..core.context import InvocationContext
    from ..core.types.tool import BaseTool
    from ..backends.subagent import AgentConfig
    from ..skill import Skill


@dataclass
class AgentContext:
    """Context provided by ContextProvider.fetch().
    
    Contains all context that a ContextProvider provides:
    - system_content: Injected into system prompt
    - user_content: Injected into user message (before User: input)
    - tools: Tools to register (from MemoryContextProvider, ArtifactContextProvider, etc.)
    - messages: History messages (from MessageContextProvider)
    - subagents: Sub-agent configs (from SubAgentContextProvider) - Agent creates DelegateTool
    - skills: Skill definitions (from SkillContextProvider)
    
    Multiple AgentContexts are merged by the Agent before LLM call.
    """
    # Content injection
    system_content: str | None = None
    user_content: str | None = None
    
    # Tools to register (paired tools from providers like MemorySearchTool)
    tools: list["BaseTool"] = field(default_factory=list)
    
    # Messages (from MessageContextProvider)
    messages: list[dict[str, Any]] = field(default_factory=list)
    
    # SubAgents (from SubAgentContextProvider) - Agent creates DelegateTool from this
    subagents: list["AgentConfig"] = field(default_factory=list)
    
    # Skills (from SkillContextProvider)
    skills: list["Skill"] = field(default_factory=list)
    
    @staticmethod
    def empty() -> "AgentContext":
        """Create an empty AgentContext."""
        return AgentContext()
    
    @staticmethod
    def merge(outputs: list["AgentContext"]) -> "AgentContext":
        """Merge multiple AgentContexts into one.
        
        - system_content: Concatenated with newlines
        - user_content: Concatenated with newlines
        - tools: Combined list (deduplicated by tool.name)
        - messages: Combined list
        - subagents: Combined list (deduplicated by key)
        - skills: Combined list (deduplicated by name)
        """
        system_parts: list[str] = []
        user_parts: list[str] = []
        all_tools: list["BaseTool"] = []
        all_messages: list[dict[str, Any]] = []
        all_subagents: list["AgentConfig"] = []
        all_skills: list["Skill"] = []
        seen_tool_names: set[str] = set()
        seen_agent_keys: set[str] = set()
        seen_skill_names: set[str] = set()
        
        for output in outputs:
            if output.system_content:
                system_parts.append(output.system_content)
            if output.user_content:
                user_parts.append(output.user_content)
            
            # Deduplicate tools by name
            for tool in output.tools:
                if tool.name not in seen_tool_names:
                    seen_tool_names.add(tool.name)
                    all_tools.append(tool)
            
            all_messages.extend(output.messages)
            
            # Deduplicate subagents by key
            for agent in output.subagents:
                if agent.key not in seen_agent_keys:
                    seen_agent_keys.add(agent.key)
                    all_subagents.append(agent)
            
            # Deduplicate skills by name
            for skill in output.skills:
                if skill.name not in seen_skill_names:
                    seen_skill_names.add(skill.name)
                    all_skills.append(skill)
        
        return AgentContext(
            system_content="\n\n".join(system_parts) if system_parts else None,
            user_content="\n\n".join(user_parts) if user_parts else None,
            tools=all_tools,
            messages=all_messages,
            subagents=all_subagents,
            skills=all_skills,
        )


@runtime_checkable
class ContextProvider(Protocol):
    """Protocol for all ContextProviders.
    
    ContextProviders provide context for LLM calls. Each ContextProvider:
    1. Has a unique name
    2. Implements fetch(ctx) to return AgentContext
    3. Provides DATA only - Agent decides how to consume it
    
    Examples:
        - MessageContextProvider: Returns messages list
        - MemoryContextProvider: Returns system_content (summary) + MemorySearchTool
        - ArtifactContextProvider: Returns system_content (index) + ReadArtifactTool
        - SubAgentContextProvider: Returns subagents list (Agent creates DelegateTool)
        - SkillContextProvider: Returns skills list
    """
    
    @property
    def name(self) -> str:
        """Unique name for this provider."""
        ...
    
    async def fetch(self, ctx: "InvocationContext") -> AgentContext:
        """Fetch context for LLM call.
        
        Called before each LLM call. Can return dynamic content
        based on current context (state, session, ctx.input, etc.).
        
        Args:
            ctx: Current invocation context (includes ctx.input with runtime vars)
            
        Returns:
            AgentContext with content and tools
        """
        ...


class BaseContextProvider(ABC):
    """Abstract base class for ContextProviders.
    
    Provides default implementation structure. Subclass and implement
    fetch() to create custom providers.
    """
    
    _name: str = "base"
    
    @property
    def name(self) -> str:
        """Provider name."""
        return self._name
    
    @abstractmethod
    async def fetch(self, ctx: "InvocationContext") -> AgentContext:
        """Fetch context. Subclasses must implement."""
        ...


__all__ = [
    "ContextProvider",
    "AgentContext",
    "BaseContextProvider",
]
