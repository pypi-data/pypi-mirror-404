"""Core module - shared infrastructure for agents."""
from .base import AgentConfig, BaseAgent, ToolInjectionMode
from .context import InvocationContext, MaxDepthExceededError
from .factory import AgentFactory
from .isolator import StateIsolator, ChainMapIsolator
from .logging import logger
from .runner import Runner
from .event_bus import EventBus, Events
from .signals import SuspendSignal, HITLSuspend, PauseSuspend
from .parallel import (
    merge_agent_runs,
    run_agents_parallel,
    ParallelSubAgentContext,
)
from .types import (
    Session,
    Invocation,
    InvocationState,
    InvocationMode,
    ControlFrame,
    generate_id,
    PromptInput,
    Message,
    MessageRole,
    BlockEvent,
    BlockKind,
    BlockOp,
    BlockHandle,
    ToolContext,
    ToolResult,
    ToolInfo,
    BaseTool,
)

__all__ = [
    # Base
    "AgentConfig",
    "BaseAgent",
    "ToolInjectionMode",
    # Context
    "InvocationContext",
    "MaxDepthExceededError",
    # Factory
    "AgentFactory",
    # Isolator
    "StateIsolator",
    "ChainMapIsolator",
    # Logging
    "logger",
    # Runner
    "Runner",
    "EventBus",
    "Events",
    # Signals
    "SuspendSignal",
    "HITLSuspend",
    "PauseSuspend",
    # Parallel
    "merge_agent_runs",
    "run_agents_parallel",
    "ParallelSubAgentContext",
    # Types - Session
    "Session",
    "Invocation",
    "InvocationState",
    "InvocationMode",
    "ControlFrame",
    "generate_id",
    # Types - Message
    "PromptInput",
    "Message",
    "MessageRole",
    # Types - Block
    "BlockEvent",
    "BlockKind",
    "BlockOp",
    "BlockHandle",
    # Types - Tool
    "ToolContext",
    "ToolResult",
    "ToolInfo",
    "BaseTool",
]
