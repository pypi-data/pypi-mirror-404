"""ReactAgent - Autonomous agent with think-act-observe loop.

ReactAgent uses the unified BaseAgent constructor:
    __init__(self, ctx: InvocationContext, config: AgentConfig | None = None)

All services (llm, tools, storage, etc.) are accessed through ctx.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any, AsyncIterator, ClassVar, Literal, TYPE_CHECKING

from ..core.base import AgentConfig, BaseAgent
from ..core.context import InvocationContext
from ..core.logging import react_logger as logger
from ..core.event_bus import Events
from ..context_providers import AgentContext
from ..core.types.block import BlockEvent, BlockKind, BlockOp
from ..llm import LLMMessage
from ..middleware import HookAction
from ..core.types import (
    Invocation,
    InvocationState,
    PromptInput,
    ToolInvocation,
    generate_id,
)
from ..core.signals import SuspendSignal

# Import helper modules
from . import context as ctx_helpers
from . import step as step_helpers
from . import tools as tool_helpers
from . import persistence as persist_helpers
from . import pause as pause_helpers
from .factory import SessionNotFoundError, create_react_agent, restore_react_agent

if TYPE_CHECKING:
    from ..llm import LLMProvider
    from ..tool import ToolSet
    from ..core.types.tool import BaseTool
    from ..core.types.session import Session
    from ..backends import Backends
    from ..backends.snapshot import SnapshotBackend
    from ..backends.subagent import AgentConfig as SubAgentConfig
    from ..core.event_bus import Bus
    from ..middleware import MiddlewareChain, Middleware
    from ..memory import MemoryManager
    from ..context_providers import ContextProvider


class ReactAgent(BaseAgent):
    """ReAct Agent - Autonomous agent with tool calling loop.

    Implements the think-act-observe pattern:
    1. Think: LLM generates reasoning and decides on actions
    2. Act: Execute tool calls
    3. Observe: Process tool results
    4. Repeat until done or max steps reached

    Two ways to create:
    
    1. Simple (recommended for most cases):
        agent = ReactAgent.create(llm=llm, tools=tools, config=config)
    
    2. Advanced (for custom Session/Backends/Bus):
        ctx = InvocationContext(session=session, backends=backends, bus=bus, llm=llm, tools=tools)
        agent = ReactAgent(ctx, config)
    """

    # Class-level config
    agent_type: ClassVar[Literal["react", "workflow"]] = "react"
    
    # ========== Factory methods (delegate to factory.py) ==========
    
    @classmethod
    def create(
        cls,
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
        context_providers: "list[ContextProvider] | None" = None,
        enable_history: bool = True,
        history_limit: int = 50,
        delegate_tool_class: "type[BaseTool] | None" = None,
        context_metadata: dict | None = None,
    ) -> "ReactAgent":
        """Create ReactAgent with minimal boilerplate. See factory.create_react_agent for details."""
        return create_react_agent(
            llm=llm,
            tools=tools,
            config=config,
            backends=backends,
            session=session,
            bus=bus,
            middlewares=middlewares,
            subagents=subagents,
            memory=memory,
            snapshot=snapshot,
            context_providers=context_providers,
            enable_history=enable_history,
            history_limit=history_limit,
            delegate_tool_class=delegate_tool_class,
            context_metadata=context_metadata,
        )
    
    @classmethod
    async def restore(
        cls,
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
        """Restore agent from persisted state. See factory.restore_react_agent for details."""
        return await restore_react_agent(
            session_id=session_id,
            llm=llm,
            backends=backends,
            tools=tools,
            config=config,
            bus=bus,
            middleware=middleware,
            memory=memory,
            snapshot=snapshot,
        )

    def __init__(
        self,
        ctx: InvocationContext,
        config: AgentConfig | None = None,
    ):
        """Initialize ReactAgent.

        Args:
            ctx: InvocationContext with llm, tools, storage, bus, session
            config: Agent configuration

        Raises:
            ValueError: If ctx.llm is None
        """
        super().__init__(ctx, config)

        # Validate required services
        if ctx.llm is None:
            raise ValueError("ReactAgent requires ctx.llm (LLMProvider)")

        # Current execution state
        self._current_invocation: Invocation | None = None
        self._current_step: int = 0
        self._message_history: list[LLMMessage] = []
        self._text_buffer: str = ""
        self._thinking_buffer: str = ""
        self._tool_invocations: list[ToolInvocation] = []
        
        # Block ID tracking for streaming (ensures consecutive deltas use same block_id)
        self._current_text_block_id: str | None = None
        self._current_thinking_block_id: str | None = None
        
        # Tool call tracking for streaming arguments
        self._call_id_to_tool: dict[str, str] = {}  # call_id -> tool_name
        self._tool_call_blocks: dict[str, str] = {}  # call_id -> block_id

        # Pause/resume support
        self._paused = False
        
        # Restore support
        self._restored_invocation: "Invocation | None" = None
        self._state: "Any | None" = None  # State object for checkpoint
        
        # Direct tools (passed to create())
        self._tools: list["BaseTool"] = []
        
        # ContextProviders for context engineering
        self._context_providers: list["ContextProvider"] = []
        
        # DelegateTool class and middleware for dynamic subagent handling
        self._delegate_tool_class: type | None = None
        self._middleware_chain: "MiddlewareChain | None" = None
        
        # Current AgentContext from providers (set by _fetch_agent_context)
        self._agent_context: AgentContext | None = None
    
    # ========== Suspension properties ==========
    
    @property
    def is_suspended(self) -> bool:
        """Check if agent is suspended (waiting for HITL input)."""
        if self._restored_invocation:
            return self._restored_invocation.state == InvocationState.SUSPENDED
        return False
    
    @property
    def state(self) -> "Any | None":
        """Get session state (for checkpoint/restore)."""
        return self._state
    
    # ========== Service accessors ==========

    @property
    def llm(self) -> "LLMProvider":
        """Get LLM provider (runtime override or context default)."""
        # Check runtime override first
        if self._run_config.get("llm") is not None:
            return self._run_config["llm"]
        return self._ctx.llm  # type: ignore (validated in __init__)

    @property
    def snapshot(self):
        """Get snapshot backend from context."""
        return self._ctx.snapshot
    
    # ========== Runtime config helpers ==========
    
    def _get_enable_thinking(self) -> bool:
        """Get enable_thinking (runtime override or config default)."""
        if self._run_config.get("enable_thinking") is not None:
            return self._run_config["enable_thinking"]
        return self.config.enable_thinking
    
    def _get_reasoning_effort(self) -> str | None:
        """Get reasoning_effort (runtime override or config default)."""
        if self._run_config.get("reasoning_effort") is not None:
            return self._run_config["reasoning_effort"]
        return self.config.reasoning_effort
    
    def _get_stream_thinking(self) -> bool:
        """Get stream_thinking (runtime override or config default)."""
        if self._run_config.get("stream_thinking") is not None:
            return self._run_config["stream_thinking"]
        return self.config.stream_thinking

    # ========== Main execution ==========

    async def _execute(self, input: PromptInput | str) -> None:
        """Execute the React loop.

        Args:
            input: User prompt input (PromptInput or str)
        """
        # Normalize input
        if isinstance(input, str):
            input = PromptInput(text=input)
        
        self.reset()
        self._running = True

        logger.info(
            "Starting ReactAgent run",
            extra={
                "session_id": self.session.id,
                "agent_id": self.ctx.agent_id,
            }
        )

        try:
            # Create new invocation using ctx.invocation_id
            self._current_invocation = Invocation(
                id=self.ctx.invocation_id,
                session_id=self.session.id,
                agent_id=self.ctx.agent_id,
                state=InvocationState.RUNNING,
                started_at=datetime.now(),
            )

            logger.info("Created invocation", extra={"invocation_id": self._current_invocation.id})

            # Persist invocation immediately (so we have record even if agent fails)
            if self.ctx.backends and self.ctx.backends.invocation:
                await self.ctx.backends.invocation.create(
                    self._current_invocation.id,
                    self.session.id,
                    self._current_invocation.to_dict(),
                    agent_id=self.ctx.agent_id,
                )

            # === Middleware: on_agent_start ===
            if self.middleware:
                logger.info(
                    "Calling middleware: on_agent_start",
                    extra={"invocation_id": self._current_invocation.id},
                )
                hook_result = await self.middleware.process_agent_start(input)
                if hook_result.action == HookAction.STOP:
                    logger.warning("Agent stopped by middleware on_agent_start", extra={"invocation_id": self._current_invocation.id})
                    await self.ctx.emit(BlockEvent(
                        kind=BlockKind.ERROR,
                        op=BlockOp.APPLY,
                        data={"message": hook_result.message or "Stopped by middleware"},
                    ))
                    return
                elif hook_result.action == HookAction.SKIP:
                    logger.warning("Agent skipped by middleware on_agent_start", extra={"invocation_id": self._current_invocation.id})
                    return

            await self.bus.publish(
                Events.INVOCATION_START,
                {
                    "invocation_id": self._current_invocation.id,
                    "session_id": self.session.id,
                },
            )

            # Fetch context from providers
            logger.info("Fetching agent context", extra={"invocation_id": self._current_invocation.id})
            self._agent_context = await ctx_helpers.fetch_agent_context(
                self._ctx,
                input,
                self._context_providers,
                self._tools,
                self._delegate_tool_class,
                self._middleware_chain,
            )
            
            # Build initial messages
            logger.info("Building message history", extra={"invocation_id": self._current_invocation.id})
            self._message_history = await ctx_helpers.build_messages(
                input,
                self._agent_context,
                self.config.system_prompt,
            )
            self._current_step = 0
            logger.info(
                "Built message history",
                extra={
                    "invocation_id": self._current_invocation.id,
                    "message_count": len(self._message_history),
                },
            )
            
            # Save user message (real-time persistence)
            logger.info("Saving user message", extra={"invocation_id": self._current_invocation.id})
            await persist_helpers.save_user_message(self, input)

            # Main loop
            finish_reason = None

            while not await self._check_abort():
                self._current_step += 1
                logger.info(
                    "Starting step",
                    extra={
                        "invocation_id": self._current_invocation.id,
                        "step": self._current_step,
                    },
                )

                # Check step limit
                if self._current_step > self.config.max_steps:
                    logger.warning(
                        "Max steps exceeded",
                        extra={
                            "max_steps": self.config.max_steps,
                            "invocation_id": self._current_invocation.id,
                        },
                    )
                    await self.ctx.emit(BlockEvent(
                        kind=BlockKind.ERROR,
                        op=BlockOp.APPLY,
                        data={"message": f"Max steps ({self.config.max_steps}) exceeded"},
                    ))
                    break

                # Re-fetch context from providers (providers decide whether to update)
                logger.debug(
                    "Re-fetching agent context for step",
                    extra={
                        "invocation_id": self._current_invocation.id,
                        "step": self._current_step,
                    },
                )
                self._agent_context = await ctx_helpers.fetch_agent_context(
                    self._ctx,
                    input,
                    self._context_providers,
                    self._tools,
                    self._delegate_tool_class,
                    self._middleware_chain,
                )
                
                # Update system message with new context (in case providers updated system_content)
                if self._message_history and self._message_history[0].role == "system":
                    # Rebuild system message using helper
                    final_system_prompt = ctx_helpers.build_system_message(
                        self._agent_context,
                        self.config.system_prompt,
                        input,
                    )
                    
                    # Log if context was injected
                    if self._agent_context.system_content:
                        logger.info(
                            f"Updated system message with context (length: {len(self._agent_context.system_content)})",
                            extra={"invocation_id": self._current_invocation.id, "step": self._current_step},
                        )
                    
                    # Update the system message
                    self._message_history[0] = LLMMessage(role="system", content=final_system_prompt)

                # Take snapshot before step
                snapshot_id = None
                if self.snapshot:
                    snapshot_id = await self.snapshot.track()

                # Execute step
                logger.info(
                    "Executing LLM request",
                    extra={
                        "invocation_id": self._current_invocation.id,
                        "step": self._current_step,
                    },
                )
                finish_reason = await step_helpers.execute_step(self)
                logger.info(
                    "LLM response received",
                    extra={
                        "invocation_id": self._current_invocation.id,
                        "step": self._current_step,
                        "finish_reason": finish_reason,
                        "tool_count": len(self._tool_invocations),
                    },
                )
                
                # Save assistant message (real-time persistence)
                await persist_helpers.save_assistant_message(self)
                
                # Save message_history to state and checkpoint
                if self._state:
                    persist_helpers.save_messages_to_state(self)
                    await self._state.checkpoint()

                # Check if we should exit
                if finish_reason == "end_turn" and not self._tool_invocations:
                    break

                # Process tool results and continue
                if self._tool_invocations:
                    logger.info(
                        "Processing tool invocations",
                        extra={
                            "invocation_id": self._current_invocation.id,
                            "step": self._current_step,
                            "tool_count": len(self._tool_invocations),
                            "tools": ", ".join([inv.tool_name for inv in self._tool_invocations]),
                        },
                    )
                    await tool_helpers.process_tool_results(self)
                    logger.info(
                        "Tool results processed",
                        extra={
                            "invocation_id": self._current_invocation.id,
                            "step": self._current_step,
                        },
                    )
                    
                    # Save tool messages (real-time persistence)
                    await persist_helpers.save_tool_messages(self)
                    
                    self._tool_invocations.clear()
                    
                    # Save message_history to state and checkpoint
                    if self._state:
                        persist_helpers.save_messages_to_state(self)
                        await self._state.checkpoint()

            # Check if aborted
            is_aborted = self.is_cancelled
            
            # Complete invocation
            if is_aborted:
                # Save current buffer content before marking as aborted
                if self._text_buffer or self._thinking_buffer or self._tool_invocations:
                    await persist_helpers.save_assistant_message(self)
                # Save completed tool results
                if self._tool_invocations:
                    await persist_helpers.save_tool_messages(self)
                # Mark invocation as aborted
                self._current_invocation.state = InvocationState.ABORTED
                logger.info(
                    "Invocation aborted by user",
                    extra={
                        "invocation_id": self._current_invocation.id,
                        "steps": self._current_step,
                    },
                )
            else:
                self._current_invocation.state = InvocationState.COMPLETED
                logger.info(
                    "Invocation completed successfully",
                    extra={
                        "invocation_id": self._current_invocation.id,
                        "steps": self._current_step,
                        "finish_reason": finish_reason,
                    },
                )
            self._current_invocation.finished_at = datetime.now()
            
            # Save to invocation backend
            if self.ctx.backends and self.ctx.backends.invocation:
                await self.ctx.backends.invocation.update(
                    self._current_invocation.id,
                    self._current_invocation.to_dict(),
                )

            duration_ms = self._current_invocation.duration_ms or 0
            logger.info(
                f"ReactAgent run {'aborted' if is_aborted else 'completed'}",
                extra={
                    "invocation_id": self._current_invocation.id,
                    "steps": self._current_step,
                    "duration_ms": duration_ms,
                    "finish_reason": "aborted" if is_aborted else finish_reason,
                },
            )

            # === Middleware: on_agent_end ===
            if self.middleware:
                await self.middleware.process_agent_end(
                    {"steps": self._current_step, "finish_reason": finish_reason},
                )

            await self.bus.publish(
                Events.INVOCATION_END,
                {
                    "invocation_id": self._current_invocation.id,
                    "steps": self._current_step,
                    "state": self._current_invocation.state.value,
                },
            )
            
            # Clear message_history from State after successful completion
            persist_helpers.clear_messages_from_state(self)
            if self._state:
                await self._state.checkpoint()

        except SuspendSignal as e:
            # HITL/Suspend signal - invocation waits for user input
            logger.warning(
                "Agent suspended (HITL)",
                extra={
                    "invocation_id": self._current_invocation.id if self._current_invocation else None,
                    "signal_type": type(e).__name__,
                    "request_type": getattr(e, "request_type", None),
                    "request_id": getattr(e, "request_id", None),
                },
            )
            
            if self._current_invocation:
                self._current_invocation.state = InvocationState.SUSPENDED
                
                # Save agent_state for resume (only if persist_hitl_state is enabled)
                if self.config.persist_hitl_state:
                    self._current_invocation.agent_state = {
                        "step": self._current_step,
                        "message_history": [
                            {"role": m.role, "content": m.content} for m in self._message_history
                        ],
                        "text_buffer": self._text_buffer,
                    }
                    self._current_invocation.step_count = self._current_step
                
                # Save invocation state
                if self.ctx.backends and self.ctx.backends.invocation:
                    await self.ctx.backends.invocation.update(
                        self._current_invocation.id,
                        self._current_invocation.to_dict(),
                    )
            
            # Save pending_request to execution state
            if self._state:
                self._state.execution["pending_request"] = e.to_dict()
                persist_helpers.save_messages_to_state(self)
                await self._state.checkpoint()
            
            return
        
        except Exception as e:
            logger.error(
                "ReactAgent run failed",
                extra={
                    "error": str(e),
                    "invocation_id": self._current_invocation.id if self._current_invocation else None,
                },
                exc_info=True,
            )

            # === Middleware: on_error ===
            if self.middleware:
                processed_error = await self.middleware.process_error(e)
                if processed_error is None:
                    logger.warning(
                        "Error suppressed by middleware",
                        extra={"invocation_id": self._current_invocation.id if self._current_invocation else None},
                    )
                    return

            if self._current_invocation:
                self._current_invocation.state = InvocationState.FAILED
                self._current_invocation.finished_at = datetime.now()

            await self.ctx.emit(BlockEvent(
                kind=BlockKind.ERROR,
                op=BlockOp.APPLY,
                data={"message": str(e)},
            ))
            raise

        finally:
            self._running = False
            self._restored_invocation = None

    # ========== Pause/resume (delegate to pause.py) ==========

    async def pause(self) -> str:
        """Pause execution and return invocation ID for later resume."""
        return await pause_helpers.pause_agent(self)

    async def resume(self, invocation_id: str) -> AsyncIterator[BlockEvent]:
        """Resume paused execution."""
        async for block in pause_helpers.resume_agent(self, invocation_id):
            yield block

    # ========== Helper methods used by other modules ==========
    
    def _get_tool(self, tool_name: str) -> "BaseTool | None":
        """Get tool by name from agent context."""
        return tool_helpers.get_tool(self, tool_name)
    
    async def _save_tool_messages(self) -> None:
        """Trigger save for tool result messages."""
        await persist_helpers.save_tool_messages(self)

    async def _noop_update_metadata(self, metadata: dict[str, Any]) -> None:
        """No-op metadata updater."""
        pass
