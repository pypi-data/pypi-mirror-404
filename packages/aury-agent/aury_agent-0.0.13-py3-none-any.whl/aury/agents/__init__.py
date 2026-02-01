"""Aury Agent Framework.

A framework supporting both React Agent (autonomous loop) and Workflow (DAG orchestration).

Package Structure:
    aury.agents.backends      - Backend protocols and implementations
    aury.agents.core          - Core infrastructure (types, bus, context)
    aury.agents.llm           - LLM adapters
    aury.agents.plugin        - Middleware system
    aury.agents.memory        - Memory system
    aury.agents.react         - ReactAgent
    aury.agents.workflow      - Workflow orchestration
    aury.agents.tool          - Tool system
    aury.agents.skill         - Skill system (capability bundles)
    aury.agents.sandbox       - Sandbox system (isolated execution)
    aury.agents.cli           - CLI

Quick Start:
    from aury.agents import ReactAgent, AgentConfig
    from aury.agents.core.types import Session, PromptInput
    from aury.agents.backends import MemoryStateBackend
    from aury.agents.core.event_bus import EventBus, Bus
    from aury.agents.llm import MockLLMProvider
    from aury.agents.tool import ToolSet
"""

__version__ = "0.1.0"

# Only export the most commonly used classes at top level
# For other classes, import from submodules directly
from .core.base import BaseAgent, AgentConfig, ToolInjectionMode
from .core.event_bus import EventBus, Events
from .core.context import InvocationContext
from .core.types import Session, PromptInput, generate_id
from .react import ReactAgent
from .workflow import WorkflowAgent
from .context_providers import ContextProvider, AgentContext

__all__ = [
    "__version__",
    "BaseAgent",
    "AgentConfig",
    "ToolInjectionMode",
    "EventBus",
    "Events",
    "InvocationContext",
    "Session",
    "PromptInput",
    "generate_id",
    "ReactAgent",
    "WorkflowAgent",
    # Providers
    "ContextProvider",
    "AgentContext",
]
