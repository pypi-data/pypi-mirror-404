"""Invocation context for agent execution.

InvocationContext is a runtime object that provides access to
the current execution context. It is NOT persisted - it is built
from the persisted Invocation when execution starts.

All services (llm, tools, middleware, etc.) are accessed through
this context, enabling unified agent construction.
"""
from __future__ import annotations

import asyncio
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING, AsyncIterator

from .logging import context_logger as logger
from .types.session import generate_id

# ContextVar for emit queue - shared across entire async call chain
_emit_queue_var: ContextVar[asyncio.Queue] = ContextVar('emit_queue')

# ContextVar for current parent_id - used by middleware to group blocks
# Stores tuple of (parent_id, apply_to_kinds) where apply_to_kinds is None (all) or set of kinds
_current_parent_id: ContextVar[tuple[str | None, set[str] | None]] = ContextVar(
    'current_parent_id', default=(None, None)
)

# ContextVar for current InvocationContext - flows through entire execution
_current_ctx: ContextVar["InvocationContext"] = ContextVar('current_invocation_context')


def get_current_ctx() -> "InvocationContext":
    """Get current InvocationContext.
    
    Use this to access ctx from anywhere within agent execution,
    e.g., in Backend methods, tools, context providers.
    
    Returns:
        Current InvocationContext
        
    Raises:
        LookupError: If called outside of agent.run() context
        
    Example:
        from aury.agents.core.context import get_current_ctx
        
        ctx = get_current_ctx()
        session_id = ctx.session_id
        agent_id = ctx.agent_id
    """
    return _current_ctx.get()


def get_current_ctx_or_none() -> "InvocationContext | None":
    """Get current InvocationContext or None if not in agent context.
    
    Safe version that doesn't raise exception.
    
    Returns:
        Current InvocationContext or None
    """
    try:
        return _current_ctx.get()
    except LookupError:
        return None


def _set_current_ctx(ctx: "InvocationContext") -> object:
    """Set current InvocationContext. Returns token for reset.
    
    Internal use only - called by BaseAgent.run().
    """
    return _current_ctx.set(ctx)


def _reset_current_ctx(token: object) -> None:
    """Reset InvocationContext using token from _set_current_ctx.
    
    Internal use only - called by BaseAgent.run().
    """
    _current_ctx.reset(token)


def set_parent_id(
    parent_id: str,
    apply_to_kinds: set[str] | None = None,
) -> object:
    """Set current parent_id for block grouping.
    
    Args:
        parent_id: The parent block ID to set
        apply_to_kinds: If provided, only blocks with these kinds will inherit
                       the parent_id. If None, all blocks inherit it.
    
    Returns:
        Token for reset. Use with middleware on_request/on_response.
    
    Example:
        # All blocks inherit parent_id
        token = set_parent_id("blk_xxx")
        
        # Only thinking and text blocks inherit parent_id
        token = set_parent_id("blk_xxx", apply_to_kinds={"thinking", "text"})
        
        # ... emit blocks
        reset_parent_id(token)
    """
    return _current_parent_id.set((parent_id, apply_to_kinds))


def reset_parent_id(token: object) -> None:
    """Reset parent_id to previous value using token from set_parent_id."""
    _current_parent_id.reset(token)


def get_parent_id() -> str | None:
    """Get current parent_id (for debugging/inspection)."""
    parent_id, _ = _current_parent_id.get()
    return parent_id


def resolve_parent_id(kind: str) -> str | None:
    """Resolve parent_id for a given block kind.
    
    Checks if the kind matches the apply_to_kinds filter.
    
    Args:
        kind: The block kind (e.g., "thinking", "text", "tool_use")
        
    Returns:
        parent_id if kind matches filter, None otherwise
    """
    parent_id, apply_to_kinds = _current_parent_id.get()
    if parent_id is None:
        return None
    if apply_to_kinds is None:
        return parent_id  # No filter, apply to all
    if kind in apply_to_kinds:
        return parent_id
    return None


async def emit(event: "BlockEvent | ActionEvent") -> None:
    """Global emit function - emits to current run's queue via ContextVar.
    
    Use this when you don't have access to InvocationContext,
    e.g., in tool execute() methods.
    
    For BlockEvent: automatically fills parent_id and actor from ContextVar if not set.
    ActionEvent does not have parent_id or actor.
    
    Args:
        event: BlockEvent or ActionEvent to emit
    """
    try:
        # Get current context for auto-fill
        ctx = get_current_ctx_or_none()
        
        # Auto-fill parent_id from ContextVar if not explicitly set (BlockEvent only)
        if hasattr(event, 'parent_id') and event.parent_id is None:
            from .types.block import BlockKind
            kind = event.kind.value if isinstance(event.kind, BlockKind) else event.kind
            event.parent_id = resolve_parent_id(kind)
        
        # Auto-fill actor from context if not explicitly set (BlockEvent only)
        if hasattr(event, 'actor') and event.actor is None and ctx:
            from .types.block import ActorInfo
            event.actor = ActorInfo(
                id=ctx.agent_id,
                role="assistant",
                name=ctx.agent_name,
            )
        
        queue = _emit_queue_var.get()
        await queue.put(event)
        # Yield control to event loop to allow consumer to process the queue
        # This ensures streaming output is truly streaming, not buffered
        await asyncio.sleep(0)
    except LookupError:
        # Log warning if called outside of agent.run() context
        pass

if TYPE_CHECKING:
    from .types.session import Session, Invocation
    from .types.message import Message
    from .types.block import BlockEvent
    from .types.action import ActionEvent
    from .event_bus import EventBus, Events
    from ..backends import Backends
    from ..backends.state import StateBackend
    from ..backends.snapshot import SnapshotBackend
    from ..llm import LLMProvider
    from ..tool import ToolSet, BaseTool, ToolResult
    from ..middleware import MiddlewareChain, HookAction
    from ..memory import MemoryManager
    from ..usage import UsageTracker
    from .state import State


@dataclass
class InvocationContext:
    """Runtime context for an invocation.
    
    This is the central object passed to all agents, providing access to:
    - Core services: storage, bus, snapshot
    - AI services: llm, tools
    - Plugins: middleware
    - Memory: memory manager
    - Session info: session, invocation IDs
    
    All agents (ReactAgent, WorkflowAgent) use the same constructor:
        def __init__(self, ctx: InvocationContext, config: AgentConfig | None = None)
    
    Attributes:
        session: Current session object
        invocation_id: Current invocation ID
        agent_id: Current executing agent ID
        backends: Backends container (new unified approach)
        storage: State backend for persistence (legacy, prefer backends.state)
        bus: Event bus for pub/sub
        llm: LLM provider for AI calls
        tools: Tool registry
        middleware: Middleware chain
        memory: Memory manager (optional)
        snapshot: Snapshot backend for file tracking (optional)
        parent_invocation_id: Parent invocation (for SubAgent)
        mode: ROOT or DELEGATED
        step: Current step number (mutable)
        abort_self: Event to abort only this invocation
        abort_chain: Event to abort entire invocation chain (shared)
        config: Configuration options
        metadata: Additional context data
    """
    # Core identifiers
    session: "Session"
    invocation_id: str
    agent_id: str
    agent_name: str | None = None  # Agent display name (for ActorInfo)
    
    # Backends container (unified backend access)
    backends: "Backends | None" = None
    
    # Core services (required)
    bus: "EventBus | None" = None
    
    # AI services (required for ReactAgent, optional for WorkflowAgent)
    llm: "LLMProvider | None" = None
    tools: "ToolSet | None" = None
    
    # Plugin services
    middleware: "MiddlewareChain | None" = None
    
    # Memory
    memory: "MemoryManager | None" = None
    
    # Usage tracking
    usage: "UsageTracker | None" = None
    
    # Optional services
    snapshot: "SnapshotBackend | None" = None
    
    # State management (with checkpoint support)
    state: "State | None" = None
    
    # Current run input (set by agent.run(), accessible by Managers)
    input: Any = None  # PromptInput
    
    # Current step's context (set before each LLM call, contains merged Manager outputs)
    agent_context: Any = None  # AgentContext
    
    # Hierarchy
    parent_invocation_id: str | None = None
    mode: str = "root"  # root or delegated
    step: int = 0
    
    # Tool execution context (set when executing a tool)
    tool_call_id: str | None = None
    tool_block_id: str | None = None
    
    # Abort signals
    abort_self: asyncio.Event = field(default_factory=asyncio.Event)
    abort_chain: asyncio.Event = field(default_factory=asyncio.Event)
    
    # Config
    config: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    # Block schema versions mapping: kind -> schema_version
    # External can register different schema versions for the same kind
    block_schema_versions: dict[str, str] = field(default_factory=dict)
    
    # Depth tracking (for max depth enforcement)
    _depth: int = 0
    
    @property
    def session_id(self) -> str:
        """Get session ID (convenience property)."""
        return self.session.id
    
    @property
    def depth(self) -> int:
        """Get current invocation depth (0 = root)."""
        return self._depth
    
    @property
    def is_aborted(self) -> bool:
        """Check if this invocation should stop."""
        return self.abort_self.is_set() or self.abort_chain.is_set()
    
    @classmethod
    def create(
        cls,
        agent_id: str = "agent",
        session_id: str | None = None,
        invocation_id: str | None = None,
        backends: "Backends | None" = None,
        bus: "EventBus | None" = None,
        llm: "LLMProvider | None" = None,
        tools: "ToolSet | None" = None,
        middleware: "MiddlewareChain | None" = None,
        memory: "MemoryManager | None" = None,
    ) -> "InvocationContext":
        """Create InvocationContext with auto-created defaults.
        
        This is a convenience method for simple use cases.
        Session and Bus are auto-created if not provided.
        
        Args:
            agent_id: Agent ID (default "agent")
            session_id: Session ID (auto-generated if None)
            invocation_id: Invocation ID (auto-generated if None)
            backends: Backends container (recommended, auto-created if None)
            bus: Event bus (auto-created if None)
            llm: LLM provider (optional)
            tools: Tool registry (optional)
            middleware: Middleware chain (optional)
            memory: Memory manager (optional)
            
        Returns:
            Configured InvocationContext
        """
        from .types.session import Session, generate_id
        from .event_bus import EventBus
        from ..backends import Backends
        
        # Auto-create backends if not provided
        if backends is None:
            backends = Backends.create_default()
        
        if bus is None:
            bus = EventBus()
        
        session = Session(
            id=session_id or generate_id("sess"),
            root_agent_id=agent_id,
        )
        
        return cls(
            session=session,
            invocation_id=invocation_id or generate_id("inv"),
            agent_id=agent_id,
            backends=backends,
            bus=bus,
            llm=llm,
            tools=tools,
            middleware=middleware,
            memory=memory,
        )
    
    @classmethod
    def from_invocation(
        cls,
        inv: "Invocation",
        session: "Session",
        backends: "Backends | None" = None,
        bus: "EventBus | None" = None,
        llm: "LLMProvider | None" = None,
        tools: "ToolSet | None" = None,
        middleware: "MiddlewareChain | None" = None,
        memory: "MemoryManager | None" = None,
        snapshot: "SnapshotBackend | None" = None,
    ) -> "InvocationContext":
        """Build context from persisted invocation.
        
        Args:
            inv: Persisted invocation
            session: Session object
            backends: Backends container (recommended, auto-created if None)
            bus: Event bus
            llm: LLM provider (required for ReactAgent)
            tools: Tool registry (required for ReactAgent)
            middleware: Middleware chain
            memory: Memory manager
            snapshot: Snapshot backend
        """
        from .event_bus import EventBus
        from ..backends import Backends
        
        # Auto-create backends if not provided
        if backends is None:
            backends = Backends.create_default()
        
        if bus is None:
            bus = EventBus()
            
        return cls(
            session=session,
            invocation_id=inv.id,
            agent_id=inv.agent_id,
            backends=backends,
            bus=bus,
            llm=llm,
            tools=tools,
            middleware=middleware,
            memory=memory,
            snapshot=snapshot,
            parent_invocation_id=inv.parent_invocation_id,
            mode=inv.mode.value if hasattr(inv.mode, 'value') else str(inv.mode),
        )
    
    def create_child(
        self,
        agent_id: str,
        agent_name: str | None = None,
        mode: str = "delegated",
        inherit_config: bool = True,
        llm: "LLMProvider | None" = None,
        tools: "ToolSet | None" = None,
        middleware: "MiddlewareChain | None" = None,
        parent_block_id: str | None = None,
    ) -> "InvocationContext":
        """Create child context for sub-agent execution.
        
        Child context inherits services from parent by default.
        LLM, tools, and middleware can be overridden for specialized sub-agents.
        
        Args:
            agent_id: Sub-agent ID
            agent_name: Sub-agent display name (optional)
            mode: Execution mode (delegated)
            inherit_config: Whether to copy config
            llm: Override LLM provider (None = inherit from parent)
            tools: Override tool registry (None = inherit from parent)
            middleware: Override middleware (None = inherit from parent)
            parent_block_id: Parent block ID for nesting child's blocks.
                           If provided, sets _current_parent_id ContextVar
                           so all child's emitted blocks inherit this parent.
            
        Returns:
            New InvocationContext for child
            
        Raises:
            MaxDepthExceededError: If max depth exceeded
        """
        max_depth = self.config.get("max_sub_agent_depth", 5)
        if self._depth >= max_depth:
            logger.warning(
                "Max sub-agent depth exceeded",
                extra={"max_depth": max_depth, "agent_id": agent_id}
            )
            raise MaxDepthExceededError(f"Max sub-agent depth {max_depth} exceeded")
        
        logger.debug(
            "Creating child context",
            extra={
                "parent_inv": self.invocation_id,
                "child_agent": agent_id,
                "mode": mode,
                "depth": self._depth + 1,
                "parent_block_id": parent_block_id,
            }
        )
        
        # If parent_block_id provided, set ContextVar so child's blocks inherit it
        # This is done here (not in child ctx) because ContextVar is task-local
        if parent_block_id:
            set_parent_id(parent_block_id)
        
        return InvocationContext(
            session=self.session,
            invocation_id=generate_id("inv"),
            agent_id=agent_id,
            agent_name=agent_name,
            backends=self.backends,  # Inherit backends
            bus=self.bus,
            llm=llm if llm is not None else self.llm,
            tools=tools if tools is not None else self.tools,
            middleware=middleware if middleware is not None else self.middleware,
            memory=self.memory,
            usage=self.usage,  # Share usage tracker
            snapshot=self.snapshot,
            parent_invocation_id=self.invocation_id,
            mode=mode,
            step=0,
            abort_self=asyncio.Event(),  # Child has own abort_self
            abort_chain=self.abort_chain,  # Shared abort_chain
            config=self.config.copy() if inherit_config else {},
            metadata={"parent_block_id": parent_block_id} if parent_block_id else {},
            block_schema_versions=self.block_schema_versions.copy() if inherit_config else {},
            _depth=self._depth + 1,
        )
    
    def with_step(self, step: int) -> "InvocationContext":
        """Create new context with updated step."""
        return InvocationContext(
            session=self.session,
            invocation_id=self.invocation_id,
            agent_id=self.agent_id,
            agent_name=self.agent_name,
            backends=self.backends,  # Inherit backends
            bus=self.bus,
            llm=self.llm,
            tools=self.tools,
            middleware=self.middleware,
            memory=self.memory,
            snapshot=self.snapshot,
            parent_invocation_id=self.parent_invocation_id,
            mode=self.mode,
            step=step,
            abort_self=self.abort_self,
            abort_chain=self.abort_chain,
            config=self.config,
            metadata=self.metadata.copy(),
            block_schema_versions=self.block_schema_versions,
            _depth=self._depth,
        )
    
    def fork(
        self,
        *,
        tool_call_id: str | None = None,
        step: int | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> "InvocationContext":
        """Create a forked context for parallel execution (e.g., tool calls).
        
        Unlike create_child(), fork() creates a shallow copy with the same
        invocation_id but different execution-specific fields. Use this for:
        - Parallel tool execution (each tool gets its own tool_call_id)
        - Step-specific context
        
        The forked context shares:
        - session, invocation_id, agent_id (same invocation)
        - All services (storage, bus, llm, etc.)
        - abort signals (shared)
        
        The forked context has its own:
        - tool_call_id (for tool-specific context)
        - metadata (merged with parent)
        
        Args:
            tool_call_id: Tool call ID for this fork
            step: Step number (None = inherit from parent)
            metadata: Additional metadata (merged with parent)
            **kwargs: Additional fields to override
            
        Returns:
            Forked InvocationContext
            
        Example:
            # Parallel tool execution
            async def execute_tool(tool, args):
                tool_ctx = ctx.fork(tool_call_id=tool.call_id)
                token = _set_current_ctx(tool_ctx)
                try:
                    return await tool.execute(args)
                finally:
                    _reset_current_ctx(token)
        """
        from dataclasses import replace
        
        # Build override dict
        overrides: dict[str, Any] = {}
        
        if tool_call_id is not None:
            overrides["tool_call_id"] = tool_call_id
        if step is not None:
            overrides["step"] = step
        if metadata:
            merged = self.metadata.copy()
            merged.update(metadata)
            overrides["metadata"] = merged
        
        overrides.update(kwargs)
        
        return replace(self, **overrides)
    
    # ========== Core Helper Methods ==========
    
    async def emit(self, block: "BlockEvent") -> None:
        """Emit a block event to the current run's queue.
        
        This is the unified way to send streaming output from anywhere:
        - ReactAgent LLM responses
        - WorkflowAgent node outputs
        - Tool outputs
        - BlockHandle operations
        
        The block's session_id, invocation_id, parent_id, actor, and schema_version 
        are automatically filled. Uses ContextVar to find the queue set by 
        BaseAgent.run(). Parent_id respects the apply_to_kinds filter set 
        via set_parent_id().
        
        Args:
            block: BlockEvent to emit
        """
        from .types.block import BlockKind, ActorInfo
        kind = block.kind.value if isinstance(block.kind, BlockKind) else block.kind
        
        # Fill in IDs if not set
        if not block.session_id:
            block.session_id = self.session_id
        if not block.invocation_id:
            block.invocation_id = self.invocation_id
        # Auto-fill parent_id from ContextVar if not explicitly set
        # Uses resolve_parent_id to respect apply_to_kinds filter
        if block.parent_id is None:
            block.parent_id = resolve_parent_id(kind)
        
        # Auto-fill actor if not explicitly set
        # Actor represents the agent that emitted this block
        if block.actor is None:
            block.actor = ActorInfo(
                id=self.agent_id,
                role="assistant",
                name=self.agent_name,
            )
        
        # Auto-fill schema_version from config if not explicitly set
        if block.schema_version is None and kind in self.block_schema_versions:
            block.schema_version = self.block_schema_versions[kind]
        
        # Put into the current run's queue (via ContextVar)
        try:
            queue = _emit_queue_var.get()
            await queue.put(block)
            # Yield control to event loop to allow consumer to process the queue
            # This ensures streaming output is truly streaming, not buffered
            await asyncio.sleep(0)
        except LookupError:
            # Fallback: if no queue set, log warning (shouldn't happen in normal use)
            logger.warning("emit() called outside of agent.run() context")
    
    async def call_llm(
        self,
        messages: list["Message"],
        llm: "LLMProvider | None" = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> Any | AsyncIterator[Any]:
        """Call LLM with automatic middleware support.
        
        Supports temporarily using a different LLM provider.
        Automatically triggers on_request/on_response middleware hooks.
        
        Args:
            messages: Messages to send to LLM
            llm: Override LLM provider (None = use ctx.llm)
            stream: Whether to stream the response
            **kwargs: Additional LLM parameters
            
        Returns:
            LLM response (or async iterator if streaming)
            
        Raises:
            ValueError: If no LLM available
        """
        provider = llm or self.llm
        if provider is None:
            raise ValueError("No LLM provider available")
        
        # Build request
        request = {
            "messages": messages,
            "stream": stream,
            **kwargs,
        }
        
        # Process through middleware (on_request)
        if self.middleware:
            processed = await self.middleware.process_request(request)
            if processed is None:
                logger.debug("Request blocked by middleware")
                return None
            request = processed
        
        try:
            # Call LLM
            if stream:
                return self._stream_llm_with_middleware(provider, request)
            else:
                response = await provider.generate(
                    messages=request["messages"],
                    **{k: v for k, v in request.items() if k not in ("messages", "stream")}
                )
                
                # Process through middleware (on_response)
                if self.middleware:
                    response_dict = {"response": response}
                    processed = await self.middleware.process_response(response_dict)
                    if processed is None:
                        return None
                    response = processed.get("response", response)
                
                return response
                
        except Exception as e:
            if self.middleware:
                processed_error = await self.middleware.process_error(e)
                if processed_error is None:
                    return None
                raise processed_error
            raise
    
    async def _stream_llm_with_middleware(
        self,
        provider: "LLMProvider",
        request: dict[str, Any],
    ) -> AsyncIterator[Any]:
        """Stream LLM response with middleware processing."""
        if self.middleware:
            self.middleware.reset_stream_state()
        
        try:
            async for chunk in provider.stream(
                messages=request["messages"],
                **{k: v for k, v in request.items() if k not in ("messages", "stream")}
            ):
                if self.middleware:
                    chunk_dict = {"delta": chunk}
                    processed = await self.middleware.process_text_stream(chunk_dict)
                    if processed is None:
                        continue
                    chunk = processed.get("delta", chunk)
                yield chunk
                
        except Exception as e:
            if self.middleware:
                processed_error = await self.middleware.process_error(e)
                if processed_error is None:
                    return
                raise processed_error
            raise
    
    async def execute_tool(
        self,
        tool: "BaseTool",
        arguments: dict[str, Any],
    ) -> "ToolResult":
        """Execute a tool with automatic middleware support.
        
        Allows manual tool execution with custom arguments.
        Automatically triggers on_tool_call/on_tool_end middleware hooks.
        
        Args:
            tool: The tool to execute
            arguments: Tool arguments (manual input)
            
        Returns:
            Tool execution result
        """
        from ..middleware import HookAction
        
        current_args = arguments
        
        # Process through middleware (on_tool_call)
        if self.middleware:
            result = await self.middleware.process_tool_call(tool, current_args)
            if result.action == HookAction.SKIP:
                logger.debug(f"Tool {tool.name} skipped by middleware")
                from ..tool import ToolResult
                return ToolResult(
                    output=result.message or "Skipped by middleware",
                    is_error=False,
                )
            elif result.action == HookAction.RETRY and result.modified_data:
                current_args = result.modified_data
            elif result.action == HookAction.STOP:
                logger.debug(f"Tool {tool.name} stopped by middleware")
                from ..tool import ToolResult
                return ToolResult(
                    output=result.message or "Stopped by middleware",
                    is_error=True,
                )
        
        # Execute tool
        tool_result = await tool.execute(**current_args)
        
        # Process through middleware (on_tool_end)
        if self.middleware:
            result = await self.middleware.process_tool_end(tool, tool_result)
            if result.action == HookAction.RETRY and result.modified_data:
                # Re-execute with modified args
                tool_result = await tool.execute(**result.modified_data)
        
        return tool_result


class MaxDepthExceededError(Exception):
    """Raised when sub-agent nesting exceeds max depth."""
    pass


__all__ = [
    "InvocationContext",
    "MaxDepthExceededError",
    # Current context access
    "get_current_ctx",
    "get_current_ctx_or_none",
    # Emit function
    "emit",
    # Parent ID management for block grouping
    "set_parent_id",
    "reset_parent_id",
    "get_parent_id",
    "resolve_parent_id",
]
