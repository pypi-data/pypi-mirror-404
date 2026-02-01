"""Base agent abstract class.

All agents (ReactAgent, WorkflowAgent) inherit from BaseAgent and use
the same constructor signature:

    def __init__(self, ctx: InvocationContext, config: AgentConfig | None = None)

This enables:
- Unified agent creation via AgentFactory
- WorkflowAgent as SubAgent of ReactAgent and vice versa
- Consistent service access through InvocationContext
"""
from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, AsyncIterator, Callable, ClassVar, Literal, TYPE_CHECKING

from .logging import logger


class ToolInjectionMode(Enum):
    """How tools are provided to LLM.
    
    FUNCTION_CALL: Use native LLM function calling (tools parameter)
    PROMPT: Inject tool schemas as text in system prompt
    """
    FUNCTION_CALL = "function_call"
    PROMPT = "prompt"

if TYPE_CHECKING:
    from .context import InvocationContext
    from .types.block import BlockEvent, BlockKind, Persistence
    from .types.action import ActionEvent, ActionCollector
    from .types.session import Session
    from .event_bus import EventBus, Bus, Events
    from ..backends.state import StateBackend
    from ..middleware import MiddlewareChain


@dataclass
class AgentConfig:
    """Agent configuration.
    
    Used by both ReactAgent and WorkflowAgent.
    
    Note: LLM parameters (temperature, max_tokens, timeout, retries) are
    configured on LLMProvider, not here. Tool timeout is configured on
    each tool's ToolConfig, not here.
    
    Agent identity fields (for ActorInfo):
    - id: Database ID or unique identifier (e.g. "1", "agent_123")
    - code: Agent code/type (e.g. "super_assistant", "researcher")
    - name: Display name (e.g. "超级助理", "Researcher Agent")
    """
    # Agent identity
    id: str | None = None  # Database ID
    code: str | None = None  # Agent code (used as fallback for id)
    name: str | None = None  # Display name
    
    max_steps: int = 50
    
    # System prompt configuration
    system_prompt: str | None = None
    
    # Thinking configuration (for models that support extended thinking)
    enable_thinking: bool = False  # Whether to request thinking output from LLM
    reasoning_effort: str | None = None  # Reasoning effort: "low", "medium", "high", "max", "auto"
    stream_thinking: bool = True  # Whether to stream thinking in real-time
    
    # Tool execution configuration
    parallel_tool_execution: bool = True  # Execute multiple tools in parallel
    
    # Tool injection mode
    tool_mode: ToolInjectionMode = ToolInjectionMode.FUNCTION_CALL
    
    # HITL state persistence (for resume support)
    # If True, save agent_state when suspended for later resume
    # If False, skip state persistence (lighter weight, but can't resume)
    persist_hitl_state: bool = False
    
    # Extra metadata for agent-specific config
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "max_steps": self.max_steps,
            "system_prompt": self.system_prompt,
            "enable_thinking": self.enable_thinking,
            "reasoning_effort": self.reasoning_effort,
            "stream_thinking": self.stream_thinking,
            "parallel_tool_execution": self.parallel_tool_execution,
            "tool_mode": self.tool_mode.value,
            "metadata": self.metadata,
        }


class BaseAgent(ABC):
    """Abstract base class for all agents.
    
    All agents use the same constructor signature:
        __init__(self, ctx: InvocationContext, config: AgentConfig | None = None)
    
    This enables unified agent creation and interoperability:
    - ReactAgent can delegate to WorkflowAgent
    - WorkflowAgent nodes can use ReactAgent
    - AgentFactory creates any agent type uniformly
    
    Class-level attributes (override in subclasses):
        name: Agent unique identifier
        description: Human-readable description
        agent_type: "react" or "workflow"
        sub_agents: List of agent classes that can be delegated to
        user_input_block: Function returning BlockEvent for HITL input
        history_inherit_mode: How to inherit history on switch
        memory_merge_mode: How to merge memory when completing as SubAgent
    """
    
    # ========== Class-level config (override in subclasses) ==========
    name: ClassVar[str] = "base"  # Agent unique identifier
    description: ClassVar[str] = ""  # Agent description
    
    # Agent type - use any string for custom types
    # Built-in types: "react", "workflow"
    # Custom types: "custom", "data_processor", "summarizer", etc.
    agent_type: ClassVar[str] = "custom"
    
    # SubAgent configuration - list of agent classes that can be delegated to
    sub_agents: ClassVar[list[type["BaseAgent"]]] = []
    
    # HITL input block generator (called when agent needs initial input)
    user_input_block: ClassVar[Callable[[], "BlockEvent"] | None] = None
    
    # History inherit mode when switched to ("full", "summary", "none")
    history_inherit_mode: ClassVar[Literal["full", "summary", "none"]] = "summary"
    
    # Memory merge mode when completing as SubAgent ("merge", "summarize", "discard")
    memory_merge_mode: ClassVar[Literal["merge", "summarize", "discard"]] = "summarize"
    
    # ========== Instance initialization ==========
    
    def __init__(
        self,
        ctx: "InvocationContext",
        config: AgentConfig | None = None,
    ):
        """Initialize agent with context and config.
        
        Args:
            ctx: InvocationContext containing all services (storage, bus, llm, tools, etc.)
            config: Agent configuration (optional, uses defaults if not provided)
        """
        self._ctx = ctx
        self.config = config or AgentConfig()
        logger.debug(f"{self.agent_type}Agent init, name={self.config.name}, invocation_id={ctx.invocation_id}, max_steps={self.config.max_steps}")
        
        # Abort signal (delegates to ctx.abort_*)
        self._abort = asyncio.Event()
        
        # Current state
        self._running = False
        
        # Action collector for current run
        self._action_collector: "ActionCollector | None" = None
        
        # Runtime config overrides (set by run(), cleared after execution)
        self._run_config: dict[str, Any] = {}
    
    # ========== Properties for service access ==========
    
    @property
    def ctx(self) -> "InvocationContext":
        """Get invocation context."""
        return self._ctx
    
    @property
    def bus(self) -> "Bus":
        """Get event bus from context."""
        return self._ctx.bus
    
    @property
    def session(self) -> "Session":
        """Get session from context."""
        return self._ctx.session
    
    @property
    def middleware(self) -> "MiddlewareChain | None":
        """Get middleware chain from context."""
        return self._ctx.middleware
    
    async def run(
        self,
        input: Any,
        *,
        # Runtime config overrides (takes precedence over AgentConfig)
        enable_thinking: bool | None = None,
        reasoning_effort: str | None = None,
        stream_thinking: bool | None = None,
        llm: "LLMProvider | None" = None,
        # Internal
        _force_own_queue: bool = False,
    ) -> AsyncIterator["BlockEvent | ActionEvent"]:
        """Main entry point for agent execution.
        
        This is a unified wrapper that:
        1. Sets up emit queue via ContextVar (or reuses parent's if nested)
        2. Runs _execute() which uses ctx.emit() internally
        3. Yields BlockEvent and non-internal ActionEvent
        4. Collects ActionEvents for result aggregation
        
        Subclasses should implement _execute(), not run().
        Uses event-driven asyncio.wait for minimal latency streaming.
        
        Args:
            input: Input to process (usually PromptInput)
            enable_thinking: Override config.enable_thinking for this run
            reasoning_effort: Override config.reasoning_effort for this run
            stream_thinking: Override config.stream_thinking for this run
            llm: Override context LLM provider for this run
            _force_own_queue: Internal flag to force creating own queue
                            (used by delegate tool to capture events)
            
        Yields:
            BlockEvent for UI streaming
            ActionEvent (if internal=False) for external actions
        
        Example:
            # Use thinking for complex tasks
            async for event in agent.run(
                "Solve this problem...",
                enable_thinking=True,
                reasoning_effort="high",
            ):
                print(event)
            
            # Switch LLM for specific runs
            async for event in agent.run(
                "Quick task",
                llm=faster_llm_provider,
            ):
                print(event)
        """
        from .context import _emit_queue_var, _set_current_ctx, _reset_current_ctx
        from .types.block import BlockEvent
        from .types.action import ActionEvent, ActionCollector
        
        # Store runtime overrides for this run
        self._run_config = {
            "enable_thinking": enable_thinking,
            "reasoning_effort": reasoning_effort,
            "stream_thinking": stream_thinking,
            "llm": llm,
        }
        logger.info(f"{self.agent_type}Agent run start, invocation_id={self._ctx.invocation_id}, name={self.config.name}")
        
        # Auto-detect parent queue (nested agent call)
        # Skip if _force_own_queue is True (delegate tool needs to capture events)
        if not _force_own_queue:
            try:
                parent_queue = _emit_queue_var.get()
                logger.debug(f"{self.agent_type}Agent: nested call detected, reusing parent queue, invocation_id={self._ctx.invocation_id}")
                # Has parent - passthrough mode, reuse parent queue
                # Still set our ctx (child agent has its own ctx)
                ctx_token = _set_current_ctx(self._ctx)
                try:
                    await self._execute(input)
                finally:
                    _reset_current_ctx(ctx_token)
                return
            except LookupError:
                pass
        
        logger.debug(f"{self.agent_type}Agent: creating own queue for this run, invocation_id={self._ctx.invocation_id}")
        # No parent - create own queue and yield events
        queue: asyncio.Queue[BlockEvent | ActionEvent] = asyncio.Queue()
        queue_token = _emit_queue_var.set(queue)
        ctx_token = _set_current_ctx(self._ctx)
        
        # Create action collector for this run
        self._action_collector = ActionCollector()
        
        def process_event(event: BlockEvent | ActionEvent):
            """Process event: collect actions, decide if should yield."""
            if isinstance(event, ActionEvent):
                self._action_collector.collect(event)
                # Only yield non-internal actions
                return not event.internal
            return True  # Always yield BlockEvents
        
        try:
            # Start execution task
            exec_task = asyncio.create_task(self._execute(input))
            get_task: asyncio.Task | None = None
            
            # Collect and yield events (streaming)
            while True:
                # First drain any pending items from queue (non-blocking)
                while True:
                    try:
                        event = queue.get_nowait()
                        if process_event(event):
                            yield event
                    except asyncio.QueueEmpty:
                        break
                
                # Exit if task is done and queue is empty
                if exec_task.done() and queue.empty():
                    break
                
                # Create get_task if needed
                if get_task is None or get_task.done():
                    get_task = asyncio.create_task(queue.get())
                
                # Wait for EITHER: queue item OR exec_task completion
                # This is event-driven - no polling, no timeout delays
                done, _ = await asyncio.wait(
                    {get_task, exec_task},
                    return_when=asyncio.FIRST_COMPLETED,
                )
                
                if get_task in done:
                    # Got an item from queue
                    try:
                        event = get_task.result()
                        if process_event(event):
                            yield event
                        get_task = None  # Will create new one in next iteration
                    except asyncio.CancelledError:
                        pass
                # If only exec_task completed, loop will drain queue and exit
            
            # Cancel pending get_task if any
            if get_task and not get_task.done():
                get_task.cancel()
                try:
                    await get_task
                except asyncio.CancelledError:
                    pass
            
            # Final drain after task completion
            while not queue.empty():
                try:
                    event = queue.get_nowait()
                    if process_event(event):
                        yield event
                except asyncio.QueueEmpty:
                    break
            
            # Check for exceptions in execution
            await exec_task
            logger.info(f"{self.agent_type}Agent run completed successfully, invocation_id={self._ctx.invocation_id}")
            
        except Exception as e:
            logger.error(f"{self.agent_type}Agent run error, error={type(e).__name__}, invocation_id={self._ctx.invocation_id}", exc_info=True)
            raise
        finally:
            # Cancel exec_task if still running (e.g., when run() is cancelled externally)
            if exec_task and not exec_task.done():
                exec_task.cancel()
                try:
                    await exec_task
                except asyncio.CancelledError:
                    pass
            _reset_current_ctx(ctx_token)
            _emit_queue_var.reset(queue_token)
            self._run_config = {}  # Clear runtime overrides
    
    @abstractmethod
    async def _execute(self, input: Any) -> None:
        """Execute agent logic. Subclasses implement this.
        
        Use self.ctx.emit(block) to send streaming output.
        
        Args:
            input: Input to process (usually PromptInput)
        """
        pass
    
    def cancel(self, abort_chain: bool = False) -> None:
        """Cancel current execution.
        
        Args:
            abort_chain: If True, abort entire invocation chain (SubAgents too)
        """
        logger.warning(f"{self.agent_type}Agent cancel requested, abort_chain={abort_chain}, invocation_id={self._ctx.invocation_id if self._ctx else 'N/A'}")
        self._abort.set()
        if self._ctx:
            if abort_chain:
                self._ctx.abort_chain.set()
            else:
                self._ctx.abort_self.set()
    
    def reset(self) -> None:
        """Reset agent state for new execution."""
        self._abort.clear()
        self._running = False
    
    @property
    def is_running(self) -> bool:
        """Check if agent is currently running."""
        return self._running
    
    @property
    def is_cancelled(self) -> bool:
        """Check if agent has been cancelled."""
        if self._ctx and self._ctx.is_aborted:
            return True
        return self._abort.is_set()
    
    # ========== Emit Helper Methods (Syntax Sugar) ==========
    
    async def emit(self, event: "BlockEvent | ActionEvent") -> None:
        """Emit a BlockEvent or ActionEvent.
        
        Convenience method that delegates to ctx.emit().
        
        Args:
            event: BlockEvent or ActionEvent to emit
        """
        await self._ctx.emit(event)
    
    async def emit_text(
        self,
        content: str,
        block_id: str | None = None,
        delta: bool = False,
        parent_id: str | None = None,
    ) -> str:
        """Emit a text block.
        
        Args:
            content: Text content
            block_id: Optional block ID (auto-generated if not provided)
            delta: If True, emit as DELTA (append), else APPLY (create/replace)
            parent_id: Optional parent block ID for nesting
            
        Returns:
            The block_id used
            
        Example:
            # Create new text block
            block_id = await self.emit_text("Hello")
            
            # Stream append to existing block
            await self.emit_text(" World", block_id=block_id, delta=True)
        """
        from .types.block import BlockEvent, BlockKind, BlockOp
        from .types.session import generate_id
        
        bid = block_id or generate_id("blk")
        await self._ctx.emit(BlockEvent(
            block_id=bid,
            parent_id=parent_id,
            kind=BlockKind.TEXT,
            op=BlockOp.DELTA if delta else BlockOp.APPLY,
            data={"content": content},
        ))
        return bid
    
    async def emit_thinking(
        self,
        content: str,
        block_id: str | None = None,
        delta: bool = False,
    ) -> str:
        """Emit a thinking block (collapsible in UI).
        
        Args:
            content: Thinking content
            block_id: Optional block ID
            delta: If True, emit as DELTA
            
        Returns:
            The block_id used
        """
        from .types.block import BlockEvent, BlockKind, BlockOp
        from .types.session import generate_id
        
        bid = block_id or generate_id("blk")
        await self._ctx.emit(BlockEvent(
            block_id=bid,
            kind=BlockKind.THINKING,
            op=BlockOp.DELTA if delta else BlockOp.APPLY,
            data={"content": content},
        ))
        return bid
    
    async def emit_error(
        self,
        message: str,
        code: str = "error",
        recoverable: bool = True,
        block_id: str | None = None,
    ) -> str:
        """Emit an error block.
        
        Args:
            message: Error message
            code: Error code
            recoverable: Whether the error is recoverable
            block_id: Optional block ID
            
        Returns:
            The block_id used
        """
        from .types.block import BlockEvent, BlockKind, BlockOp
        from .types.session import generate_id
        
        bid = block_id or generate_id("blk")
        await self._ctx.emit(BlockEvent(
            block_id=bid,
            kind=BlockKind.ERROR,
            op=BlockOp.APPLY,
            data={
                "code": code,
                "message": message,
                "recoverable": recoverable,
            },
        ))
        return bid
    
    async def emit_artifact(
        self,
        artifact_id: str,
        title: str | None = None,
        summary: str | None = None,
        block_id: str | None = None,
    ) -> str:
        """Emit an artifact reference block.
        
        Args:
            artifact_id: ID of the artifact to reference
            title: Optional title for display
            summary: Optional summary for display
            block_id: Optional block ID
            
        Returns:
            The block_id used
        """
        from .types.block import BlockEvent, BlockKind, BlockOp
        from .types.session import generate_id
        
        bid = block_id or generate_id("blk")
        await self._ctx.emit(BlockEvent(
            block_id=bid,
            kind=BlockKind.ARTIFACT,
            op=BlockOp.APPLY,
            data={
                "artifact_id": artifact_id,
                "title": title,
                "summary": summary,
            },
        ))
        return bid
    
    @property
    def action_collector(self) -> "ActionCollector | None":
        """Get action collector from current run.
        
        Use this after run() completes to access collected actions and results.
        
        Example:
            async for event in agent.run(input):
                ...
            result = agent.action_collector.get_merged_result()
        """
        return self._action_collector
    
    async def pause(self) -> str:
        """Pause execution and return invocation ID for later resume.
        
        Returns:
            Invocation ID for resuming
            
        Raises:
            NotImplementedError: If agent doesn't support pause
        """
        raise NotImplementedError("Agent does not support pause/resume")
    
    async def resume(self, invocation_id: str) -> AsyncIterator["BlockEvent"]:
        """Resume paused execution.
        
        Args:
            invocation_id: ID from pause()
            
        Yields:
            BlockEvent streaming events
            
        Raises:
            NotImplementedError: If agent doesn't support pause
        """
        raise NotImplementedError("Agent does not support pause/resume")
    
    async def _check_abort(self) -> bool:
        """Check if execution should be aborted.
        
        Returns:
            True if should abort
        """
        if self._ctx and self._ctx.is_aborted:
            return True
        return self._abort.is_set()
