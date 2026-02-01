"""Factory functions for ReactAgent creation and restoration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..core.base import AgentConfig
from ..core.context import InvocationContext
from ..core.types.session import Session, generate_id

if TYPE_CHECKING:
    from ..llm import LLMProvider
    from ..tool import ToolSet
    from ..core.types.tool import BaseTool
    from ..backends import Backends
    from ..backends.snapshot import SnapshotBackend
    from ..backends.subagent import AgentConfig as SubAgentConfig
    from ..core.event_bus import Bus
    from ..middleware import MiddlewareChain, Middleware
    from ..memory import MemoryManager
    from ..context_providers import ContextProvider


class SessionNotFoundError(Exception):
    """Raised when session is not found in storage."""
    pass


def create_react_agent(
    llm: "LLMProvider",
    tools: "ToolSet | list[BaseTool] | None" = None,
    config: AgentConfig | None = None,
    *,
    backends: "Backends | None" = None,
    session: "Session | None" = None,
    bus: "Bus | None" = None,
    middlewares: "list[Middleware] | None" = None,
    subagents: "list[SubAgentConfig] | None" = None,
    memory: "MemoryManager | None" = None,
    snapshot: "SnapshotBackend | None" = None,
    # ContextProvider system
    context_providers: "list[ContextProvider] | None" = None,
    message_provider: "ContextProvider | None" = None,
    enable_history: bool = True,
    history_limit: int = 50,
    # Tool customization
    delegate_tool_class: "type[BaseTool] | None" = None,
    # Context metadata
    context_metadata: dict | None = None,
    # HITL resume support
    invocation_id: str | None = None,
) -> "ReactAgent":
    """Create ReactAgent with minimal boilerplate.
    
    This is the recommended way to create a ReactAgent for simple use cases.
    Session, Storage, and Bus are auto-created if not provided.
    
    Args:
        llm: LLM provider (required)
        tools: Tool registry or list of tools (optional)
        config: Agent configuration (optional)
        backends: Backends container (recommended, auto-created if None)
        session: Session object (auto-created if None)
        bus: Event bus (auto-created if None)
        middlewares: List of middlewares (auto-creates chain)
        subagents: List of sub-agent configs (auto-creates SubAgentManager)
        memory: Memory manager (optional)
        snapshot: Snapshot backend (optional)
        context_providers: Additional custom context providers (optional)
        message_provider: Custom message context provider (replaces default MessageContextProvider)
        enable_history: Enable message history (default True, ignored if message_provider is set)
        history_limit: Max conversation turns to keep (default 50, ignored if message_provider is set)
        delegate_tool_class: Custom DelegateTool class (optional)
        
    Returns:
        Configured ReactAgent ready to run
        
    Example:
        # Minimal
        agent = create_react_agent(llm=my_llm)
        
        # With backends
        agent = create_react_agent(
            llm=my_llm,
            backends=Backends.create_default(),
        )
        
        # With tools and middlewares
        agent = create_react_agent(
            llm=my_llm,
            tools=[tool1, tool2],
            middlewares=[MessageContainerMiddleware()],
        )
        
        # With sub-agents
        agent = create_react_agent(
            llm=my_llm,
            subagents=[
                AgentConfig(key="researcher", agent=researcher_agent),
            ],
        )
        
        # With custom context providers
        agent = create_react_agent(
            llm=my_llm,
            tools=[tool1],
            context_providers=[MyRAGProvider(), MyProjectProvider()],
        )
    """
    from .agent import ReactAgent
    from ..core.event_bus import EventBus
    from ..backends import Backends
    from ..backends.subagent import ListSubAgentBackend
    from ..tool import ToolSet
    from ..tool.builtin import DelegateTool
    from ..middleware import MiddlewareChain, MessageBackendMiddleware
    from ..context_providers import MessageContextProvider
    
    # Auto-create backends if not provided
    if backends is None:
        backends = Backends.create_default()
    
    # Auto-create missing components
    if session is None:
        session = Session(id=generate_id("sess"))
    if bus is None:
        bus = EventBus()
    
    # Create middleware chain (add MessageBackendMiddleware if history enabled)
    middleware_chain: MiddlewareChain | None = None
    if middlewares or enable_history:
        middleware_chain = MiddlewareChain()
        # Add message persistence middleware first (uses backends.message)
        if enable_history and backends.message is not None:
            middleware_chain.use(MessageBackendMiddleware())
        # Add user middlewares
        if middlewares:
            for mw in middlewares:
                middleware_chain.use(mw)
    
    # === Build tools list (direct, no provider) ===
    tool_list: list["BaseTool"] = []
    if tools is not None:
        if isinstance(tools, ToolSet):
            tool_list = list(tools.all())
        else:
            tool_list = list(tools)
    
    # Handle subagents - create DelegateTool directly
    if subagents:
        backend = ListSubAgentBackend(subagents)
        tool_cls = delegate_tool_class or DelegateTool
        delegate_tool = tool_cls(backend, middleware=middleware_chain)
        tool_list.append(delegate_tool)
    
    # === Build providers ===
    default_providers: list["ContextProvider"] = []
    
    # MessageContextProvider - for fetching history
    # Use custom message_provider if provided, otherwise use default
    if message_provider is not None:
        default_providers.append(message_provider)
    elif enable_history:
        default_message_provider = MessageContextProvider(max_messages=history_limit * 2)
        default_providers.append(default_message_provider)
    
    # Combine default + custom context_providers
    all_providers = default_providers + (context_providers or [])
    
    # Build context
    # agent_id: use config.id if provided, fallback to config.code, then "react_agent"
    # agent_name: use config.name (display name)
    agent_id = (
        config.id if config and config.id 
        else (config.code if config and config.code else "react_agent")
    )
    agent_name = config.name if config else None
    
    ctx = InvocationContext(
        session=session,
        invocation_id=generate_id("inv"),
        agent_id=agent_id,
        agent_name=agent_name,
        backends=backends,
        bus=bus,
        llm=llm,
        middleware=middleware_chain,
        memory=memory,
        snapshot=snapshot,
        metadata=context_metadata or {},
    )
    
    agent = ReactAgent(ctx, config)
    agent._tools = tool_list  # Direct tools (not from context_provider)
    agent._context_providers = all_providers
    agent._delegate_tool_class = delegate_tool_class or DelegateTool
    agent._middleware_chain = middleware_chain
    return agent


async def restore_react_agent(
    session_id: str,
    llm: "LLMProvider",
    *,
    backends: "Backends | None" = None,
    tools: "ToolSet | list[BaseTool] | None" = None,
    config: AgentConfig | None = None,
    bus: "Bus | None" = None,
    middleware: "MiddlewareChain | None" = None,
    memory: "MemoryManager | None" = None,
    snapshot: "SnapshotBackend | None" = None,
) -> "ReactAgent":
    """Restore agent from persisted state.
    
    Use this to resume an agent after:
    - Page refresh
    - Process restart
    - Cross-process recovery
    
    Args:
        session_id: Session ID to restore
        llm: LLM provider
        backends: Backends container (recommended, auto-created if None)
        tools: Tool registry or list of tools
        config: Agent configuration
        bus: Event bus (auto-created if None)
        middleware: Middleware chain
        memory: Memory manager
        snapshot: Snapshot backend
        
    Returns:
        Restored ReactAgent ready to continue
        
    Raises:
        SessionNotFoundError: If session not found
        
    Example:
        agent = await restore_react_agent(
            session_id="sess_xxx",
            backends=my_backends,
            llm=my_llm,
        )
        
        # Check if waiting for HITL response
        if agent.is_suspended:
            print(f"Waiting for: {agent.pending_request}")
        else:
            # Continue conversation
            await agent.run("Continue...")
    """
    from .agent import ReactAgent
    from ..core.event_bus import Bus
    from ..core.types.session import Session, Invocation, InvocationState, generate_id
    from ..core.state import State
    from ..tool import ToolSet
    from ..backends import Backends
    
    # Auto-create backends if not provided
    if backends is None:
        backends = Backends.create_default()
    
    # Validate storage backend is available
    if backends.state is None:
        raise ValueError("Cannot restore: no storage backend available (backends.state is None)")
    
    storage = backends.state
    
    # 1. Load session
    session_data = await storage.get("sessions", session_id)
    if not session_data:
        raise SessionNotFoundError(f"Session not found: {session_id}")
    session = Session.from_dict(session_data)
    
    # 2. Load current invocation
    invocation: Invocation | None = None
    if session_data.get("current_invocation_id"):
        inv_data = await storage.get("invocations", session_data["current_invocation_id"])
        if inv_data:
            invocation = Invocation.from_dict(inv_data)
    
    # 3. Load state
    state = State(storage, session_id)
    await state.restore()
    
    # 4. Handle tools
    tool_set: ToolSet | None = None
    if tools is not None:
        if isinstance(tools, ToolSet):
            tool_set = tools
        else:
            tool_set = ToolSet()
            for tool in tools:
                tool_set.add(tool)
    else:
        tool_set = ToolSet()
    
    # 5. Create bus if needed
    if bus is None:
        bus = Bus()
    
    # 6. Build context
    ctx = InvocationContext(
        session=session,
        invocation_id=invocation.id if invocation else generate_id("inv"),
        agent_id=config.name if config else "react_agent",
        backends=backends,
        bus=bus,
        llm=llm,
        tools=tool_set,
        middleware=middleware,
        memory=memory,
        snapshot=snapshot,
    )
    
    # 7. Create agent
    agent = ReactAgent(ctx, config)
    agent._restored_invocation = invocation
    agent._state = state
    
    return agent
