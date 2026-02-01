"""ContextProvider system for context engineering.

ContextProviders provide a unified abstraction for fetching LLM context:
- Messages (conversation history)
- Memory (long-term memory summaries/recalls)
- Artifacts (with pluggable loaders for different types)
- SubAgents (sub-agent configurations)
- Skills (capability descriptions)

Core Design:
- Provider: ONLY responsible for FETCHING context (read)
- Middleware: Responsible for WRITING/SAVING (via hooks like on_message_save)
- Manager: Service layer providing APIs for both Provider and Middleware

- Each ContextProvider implements `fetch(ctx) -> AgentContext`
- AgentContext contains: system_content, user_content, messages, tools, subagents, skills
- Multiple AgentContexts are merged before LLM call

Usage:
    agent = ReactAgent.create(
        llm=llm,
        tools=[my_tool],
        providers=[
            ArtifactContextProvider(backend=artifact_backend),
            MemoryContextProvider(memory_manager=memory),
        ],
        enable_history=True,  # Auto-creates MessageContextProvider + MessageBackendMiddleware
    )

Built-in ContextProviders:
- MessageContextProvider: Fetch conversation history
- MemoryContextProvider: Fetch memory summaries/recalls
- ArtifactContextProvider: Artifact index with ReadArtifactTool + pluggable loaders
- SubAgentContextProvider: Provides sub-agent configurations
- SkillContextProvider: Skill descriptions in system prompt
"""
from .base import ContextProvider, AgentContext, BaseContextProvider
from .message import MessageContextProvider
from .memory import MemoryContextProvider
from .artifact import (
    ArtifactContextProvider,
    ArtifactLoader,
    ReadArtifactTool,
    register_loader,
    get_loader,
)
from .subagent import SubAgentContextProvider
from .skill import SkillContextProvider

__all__ = [
    # Base protocol
    "ContextProvider",
    "AgentContext",
    "BaseContextProvider",
    # Built-in providers
    "MessageContextProvider",
    "MemoryContextProvider",
    "ArtifactContextProvider",
    "SubAgentContextProvider",
    "SkillContextProvider",
    # Artifact utilities
    "ArtifactLoader",
    "ReadArtifactTool",
    "register_loader",
    "get_loader",
]
