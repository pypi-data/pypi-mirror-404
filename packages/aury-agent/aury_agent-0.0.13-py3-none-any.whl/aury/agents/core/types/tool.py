"""Tool-related type definitions."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Awaitable, Callable

from .session import generate_id


@dataclass
class ToolInfo:
    """Tool metadata for LLM."""
    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema
    
    def to_llm_schema(self) -> dict[str, Any]:
        """Convert to LLM API format."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.parameters,
        }


@dataclass
class ToolContext:
    """Context passed to tool execution."""
    session_id: str
    invocation_id: str
    block_id: str
    call_id: str
    agent: str
    abort_signal: asyncio.Event
    update_metadata: Callable[[dict[str, Any]], Awaitable[None]]
    
    # Optional usage tracker
    usage: Any | None = None  # UsageTracker
    
    # Branch for sub-agent isolation
    branch: str | None = None
    
    # Caller's middleware chain (for sub-agent inheritance)
    middleware: Any | None = None  # MiddlewareChain
    
    async def emit(self, block: Any) -> None:
        """Emit a block event.
        
        Uses the global emit function via ContextVar.
        Works automatically when called within agent.run() context.
        
        Args:
            block: BlockEvent to emit
        """
        from ..context import emit as global_emit
        
        # Fill in IDs if not set
        if hasattr(block, 'session_id') and not block.session_id:
            block.session_id = self.session_id
        if hasattr(block, 'invocation_id') and not block.invocation_id:
            block.invocation_id = self.invocation_id
        
        await global_emit(block)
    
    async def emit_hitl(self, hitl_id: str, data: dict[str, Any]) -> None:
        """Emit a HITL block.
        
        Convenience method for tools that need user interaction.
        The data format is flexible - can be anything the frontend understands:
        - Choice selection (choices, radio, checkbox)
        - Text input (text, textarea, number)
        - Confirmation (yes/no, approve/reject)
        - Rich content (product cards, file selection, etc.)
        
        Args:
            hitl_id: Unique ID for this HITL request
            data: Arbitrary data dict for frontend to render.
                  Common fields: type, question, choices, default, context
        """
        from .block import BlockEvent, BlockKind
        
        await self.emit(BlockEvent(
            kind=BlockKind.HITL,
            data={"hitl_id": hitl_id, **data},
        ))


@dataclass
class ToolResult:
    """Tool execution result for LLM.
    
    This is the text result returned to LLM. For frontend rendering,
    tools should use ctx.emit(BlockEvent(...)) to PATCH the TOOL_USE block
    with structured data during execution.
    
    Fields:
    - output: Complete text output for LLM
    - truncated_output: Shortened output for context window management
    
    Example (image generation tool):
        # During execution, PATCH block with structured data for frontend
        await ctx.emit(BlockEvent(
            block_id=ctx.block_id,
            kind=BlockKind.TOOL_USE,
            op=BlockOp.PATCH,
            data={"images": [{"url": "..."}], "progress": 100},
        ))
        
        # Return text for LLM
        return ToolResult.success("已生成4张图片")
    """
    output: str  # Text output for LLM
    is_error: bool = False
    truncated_output: str | None = None  # Shortened output for LLM context window
    
    def __post_init__(self):
        # Default truncated to output if not provided
        if self.truncated_output is None:
            self.truncated_output = self.output
    
    @classmethod
    def success(
        cls,
        output: str,
        *,
        truncated_output: str | None = None,
    ) -> ToolResult:
        """Create a successful result.
        
        Args:
            output: Text output for LLM
            truncated_output: Shortened output for LLM context (defaults to output)
        """
        return cls(
            output=output,
            is_error=False,
            truncated_output=truncated_output,
        )
    
    @classmethod
    def error(cls, message: str) -> ToolResult:
        """Create an error result."""
        return cls(output=message, is_error=True)


class ToolInvocationState(Enum):
    """Tool invocation state machine."""
    PARTIAL_CALL = "partial-call"  # Arguments streaming
    CALL = "call"  # Arguments complete, ready to execute
    RESULT = "result"  # Execution complete (deprecated, use SUCCESS/FAILED/ABORTED)
    # Execution result states
    SUCCESS = "success"  # Execution successful
    FAILED = "failed"  # Execution failed (including timeout)
    ABORTED = "aborted"  # User aborted


@dataclass
class ToolInvocation:
    """Tool invocation tracking (state machine)."""
    tool_call_id: str
    tool_name: str
    block_id: str = ""  # Associated TOOL_USE block ID
    state: ToolInvocationState = ToolInvocationState.PARTIAL_CALL
    args: dict[str, Any] = field(default_factory=dict)
    args_raw: str = ""  # Raw JSON string for streaming
    result: str | None = None
    truncated_result: str | None = None  # Shortened result for context window
    is_error: bool = False
    
    # Timing
    time: dict[str, datetime | None] = field(
        default_factory=lambda: {"start": None, "end": None}
    )
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def mark_call_complete(self) -> None:
        """Mark arguments as complete."""
        self.state = ToolInvocationState.CALL
        self.time["start"] = datetime.now()
    
    def mark_result(
        self,
        result: str,
        is_error: bool = False,
        truncated_result: str | None = None,
        status: ToolInvocationState | None = None,
    ) -> None:
        """Mark execution complete.
        
        Args:
            result: Complete result (raw)
            is_error: Whether this is an error result
            truncated_result: Shortened result for context window (defaults to result)
            status: Explicit status (SUCCESS/FAILED/ABORTED). If not provided,
                    automatically inferred from is_error flag.
        """
        # Set state based on explicit status or infer from is_error
        if status:
            self.state = status
        elif is_error:
            self.state = ToolInvocationState.FAILED
        else:
            self.state = ToolInvocationState.SUCCESS
        
        self.result = result
        self.truncated_result = truncated_result if truncated_result is not None else result
        self.is_error = is_error
        self.time["end"] = datetime.now()
    
    @property
    def duration_ms(self) -> int | None:
        """Get execution duration."""
        if self.time["start"] and self.time["end"]:
            return int((self.time["end"] - self.time["start"]).total_seconds() * 1000)
        return None


class BaseTool:
    """Base class for tools with common functionality.
    
    Tools can operate in two modes:
    
    1. Standard mode (default):
       - Implement execute() method
       - Tool runs to completion or raises HITLSuspend
       - If HITLSuspend raised, user response becomes tool result
    
    2. Continuation mode:
       - Set supports_continuation = True
       - Implement execute_resumable() method
       - Tool can pause mid-execution with HITLSuspend(resume_mode="continuation")
       - When user responds, tool resumes from checkpoint
       - Useful for OAuth, payment, multi-step wizards
    
    Emit support:
        Tools can emit BlockEvents using self.emit(). The emitter is automatically
        set when the tool is executed via the agent framework. If no emitter is
        available (e.g., standalone testing), emit calls are silently skipped.
        
        Example:
            async def execute(self, params, ctx):
                await self.emit(BlockEvent(...))
                return ToolResult.success("done")
    
    Example (continuation mode):
        class OAuthTool(BaseTool):
            _name = "oauth_connect"
            supports_continuation = True
            
            async def execute_resumable(
                self,
                params: dict[str, Any],
                ctx: ToolContext,
                checkpoint: "ToolCheckpoint | None" = None,
            ) -> ToolResult:
                if checkpoint:
                    # Resume from checkpoint
                    token = checkpoint.user_response["access_token"]
                    return await self._complete_oauth(token, params)
                
                # First execution - generate auth URL
                auth_url = self._build_auth_url(params)
                raise HITLSuspend(
                    request_id=generate_id("hitl"),
                    request_type="external_auth",
                    resume_mode="continuation",
                    tool_state={"step": "awaiting_callback"},
                    metadata={"auth_url": auth_url, "callback_id": "..."},
                )
    """
    
    _name: str = "base_tool"
    _display_name: str | None = None  # Optional display name for UI
    _description: str = "Base tool"
    _parameters: dict[str, Any] = {
        "type": "object",
        "properties": {},
        "required": [],
    }
    _config: ToolConfig | None = None
    
    # Continuation mode support
    supports_continuation: bool = False
    
    # Runtime context (set during execution)
    _ctx: ToolContext | None = None
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def display_name(self) -> str:
        """Get display name for UI. Falls back to name if not set."""
        return self._display_name or self._name
    
    @property
    def description(self) -> str:
        return self._description
    
    @property
    def parameters(self) -> dict[str, Any]:
        return self._parameters
    
    @property
    def config(self) -> ToolConfig:
        """Get tool config. Returns default config if not set."""
        return self._config or ToolConfig()
    
    @property
    def ctx(self) -> ToolContext | None:
        """Get current execution context."""
        return self._ctx
    
    def _set_ctx(self, ctx: ToolContext | None) -> None:
        """Set execution context. Called by framework before execute()."""
        self._ctx = ctx
    
    async def emit(self, block: Any) -> None:
        """Emit a BlockEvent.
        
        Uses the current ToolContext's emit function if available.
        Silently skips if no context is set (e.g., standalone testing).
        
        Args:
            block: BlockEvent to emit
        """
        if self._ctx is not None:
            await self._ctx.emit(block)
        # If no ctx, silently skip - allows standalone testing
    
    async def emit_hitl(self, hitl_id: str, data: dict[str, Any]) -> None:
        """Emit a HITL block.
        
        Convenience method for tools that need user interaction.
        Silently skips if no context is set.
        
        Args:
            hitl_id: Unique ID for this HITL request
            data: Arbitrary data dict for frontend to render.
        """
        if self._ctx is not None:
            await self._ctx.emit_hitl(hitl_id, data)
    
    async def execute(self, params: dict[str, Any], ctx: ToolContext) -> ToolResult:
        """Execute tool (standard mode).
        
        Override this method for standard tools.
        For continuation-capable tools, override execute_resumable() instead.
        """
        raise NotImplementedError("Subclass must implement execute()")
    
    async def execute_resumable(
        self,
        params: dict[str, Any],
        ctx: ToolContext,
        checkpoint: Any | None = None,  # ToolCheckpoint, use Any to avoid circular import
    ) -> ToolResult:
        """Execute tool with continuation support.
        
        Override this method for tools that need to pause mid-execution
        and resume later (e.g., OAuth, payment, external callbacks).
        
        Args:
            params: Tool parameters from LLM
            ctx: Tool execution context
            checkpoint: If resuming, contains saved state and user response.
                       None on first execution.
        
        Returns:
            ToolResult on completion
            
        Raises:
            HITLSuspend: To pause and wait for user/callback.
                        Set resume_mode="continuation" and provide tool_state.
        
        Example:
            async def execute_resumable(self, params, ctx, checkpoint=None):
                if checkpoint:
                    # Resuming - use checkpoint.user_response
                    return await self._continue(checkpoint)
                
                # First run - do initial work, then suspend
                partial_result = await self._step_one(params)
                raise HITLSuspend(
                    request_id=generate_id("hitl"),
                    resume_mode="continuation",
                    tool_state={"partial": partial_result},
                    ...
                )
        """
        # Default: delegate to standard execute()
        # Tools that support continuation should override this
        return await self.execute(params, ctx)
    
    def get_info(self) -> ToolInfo:
        """Get tool info."""
        return ToolInfo(
            name=self.name,
            description=self.description,
            parameters=self.parameters,
        )


@dataclass
class ToolConfig:
    """Tool configuration."""
    is_resumable: bool = False  # Supports pause/resume
    timeout: float | None = None  # Execution timeout in seconds
    requires_permission: bool = False  # Needs HITL approval
    permission_message: str | None = None
    stream_arguments: bool = False  # Stream tool arguments to client
    require_purpose: bool = False  # Generate purpose via middleware (async LLM call)
    
    
    # Retry configuration
    max_retries: int = 0  # 0 = no retry
    retry_delay: float = 1.0  # Base delay between retries (seconds)
    retry_backoff: float = 2.0  # Exponential backoff multiplier
