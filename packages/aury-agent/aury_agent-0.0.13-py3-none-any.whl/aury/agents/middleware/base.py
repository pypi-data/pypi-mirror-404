"""Middleware protocol and base implementation.

Middleware can access InvocationContext via get_current_ctx_or_none() for:
- session_id, invocation_id, agent_id, agent_name
- backends, metadata, etc.

Middleware should use self._xxx for internal state between hooks.
"""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable, TYPE_CHECKING

from .types import HookResult, MiddlewareConfig

if TYPE_CHECKING:
    from ..core.types.tool import BaseTool, ToolResult


@runtime_checkable
class Middleware(Protocol):
    """Middleware protocol for request/response processing.
    
    Includes both LLM request/response hooks and agent lifecycle hooks.
    Use get_current_ctx_or_none() to access InvocationContext.
    """
    
    @property
    def config(self) -> MiddlewareConfig:
        """Get middleware configuration."""
        ...
    
    # ========== LLM Request/Response Hooks ==========
    
    async def on_request(
        self,
        request: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Process request before LLM call.
        
        Args:
            request: The request to process
            
        Returns:
            Modified request, or None to skip further processing
        """
        ...
    
    async def on_response(
        self,
        response: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Process response after LLM call.
        
        Args:
            response: The response to process
            
        Returns:
            Modified response, or None to skip further processing
        """
        ...
    
    async def on_error(
        self,
        error: Exception,
    ) -> Exception | None:
        """Handle errors.
        
        Args:
            error: The exception that occurred
            
        Returns:
            Modified exception, or None to suppress
        """
        ...
    
    async def on_text_stream(
        self,
        chunk: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Process text streaming chunk.
        
        Args:
            chunk: The text chunk with {"delta": str}
            
        Returns:
            Modified chunk, or None to skip
        """
        ...
    
    async def on_text_stream_end(self) -> dict[str, Any] | None:
        """Called when text stream ends.
        
        Use this to flush any buffered text content.
        
        Returns:
            Optional dict with {"delta": str} to emit final content,
            or None if no additional content.
        """
        ...
    
    async def on_thinking_stream(
        self,
        chunk: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Process thinking stream chunk.
        
        Args:
            chunk: The thinking chunk with {"delta": str}
            
        Returns:
            Modified chunk, or None to skip
        """
        ...
    
    async def on_thinking_stream_end(self) -> dict[str, Any] | None:
        """Called when thinking stream ends.
        
        Use this to flush any buffered thinking content.
        
        Returns:
            Optional dict with {"delta": str} to emit final thinking content,
            or None if no additional content.
        """
        ...
    
    # ========== Agent Lifecycle Hooks ==========
    
    async def on_agent_start(
        self,
        input_data: Any,
    ) -> HookResult:
        """Called when agent starts processing.
        
        Use get_current_ctx_or_none() to access agent_id, session_id, etc.
        
        Args:
            input_data: Input to the agent
            
        Returns:
            HookResult controlling execution flow
        """
        ...
    
    async def on_agent_end(
        self,
        result: Any,
    ) -> HookResult:
        """Called when agent completes processing.
        
        Use get_current_ctx_or_none() to access agent_id, session_id, etc.
        
        Args:
            result: Agent's result
            
        Returns:
            HookResult (only CONTINUE/STOP meaningful here)
        """
        ...
    
    async def on_tool_call(
        self,
        tool: "BaseTool",
        params: dict[str, Any],
    ) -> HookResult:
        """Called before tool execution.
        
        Args:
            tool: The tool to be called
            params: Tool parameters
            
        Returns:
            HookResult - SKIP to skip tool, RETRY to modify params
        """
        ...
    
    async def on_tool_call_delta(
        self,
        call_id: str,
        tool_name: str,
        delta: dict[str, Any],
        accumulated_args: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Called during streaming tool argument generation.
        
        Only triggered for tools with stream_arguments=True.
        Receives incremental updates as LLM generates tool parameters.
        
        Args:
            call_id: Tool call identifier
            tool_name: Name of the tool being called
            delta: Incremental parameter update (e.g. {"content": "more text"})
            accumulated_args: Current accumulated arguments state
            
        Returns:
            Modified delta, or None to skip emitting this delta
        """
        ...
    
    async def on_tool_end(
        self,
        tool: "BaseTool",
        result: "ToolResult",
    ) -> HookResult:
        """Called after tool execution.
        
        Args:
            tool: The tool that was called
            result: Tool execution result
            
        Returns:
            HookResult - RETRY to re-execute tool
        """
        ...
    
    async def on_subagent_start(
        self,
        parent_agent_id: str,
        child_agent_id: str,
        mode: str,  # "embedded" or "delegated"
    ) -> HookResult:
        """Called when delegating to a sub-agent.
        
        Args:
            parent_agent_id: Parent agent identifier
            child_agent_id: Child agent identifier
            mode: Delegation mode
            
        Returns:
            HookResult - SKIP to skip delegation
        """
        ...
    
    async def on_subagent_end(
        self,
        parent_agent_id: str,
        child_agent_id: str,
        result: Any,
    ) -> HookResult:
        """Called when sub-agent completes.
        
        Args:
            parent_agent_id: Parent agent identifier
            child_agent_id: Child agent identifier
            result: Sub-agent's result
            
        Returns:
            HookResult (for post-processing)
        """
        ...
    
    async def on_message_save(
        self,
        message: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Called before saving a message to history.
        
        Allows middlewares to transform, filter, or block messages
        before they are persisted.
        
        Args:
            message: Message dict with 'role', 'content', etc.
            
        Returns:
            Modified message, or None to skip saving
        """
        ...


class BaseMiddleware:
    """Base middleware implementation with sensible defaults.
    
    Subclass and override specific hooks as needed.
    All hooks have sensible pass-through defaults.
    
    Use get_current_ctx_or_none() to access InvocationContext.
    Use self._xxx for internal state between hooks.
    """
    
    _config: MiddlewareConfig = MiddlewareConfig()
    
    @property
    def config(self) -> MiddlewareConfig:
        return self._config
    
    # ========== LLM Request/Response Hooks ==========
    
    async def on_request(
        self,
        request: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Default: pass through."""
        return request
    
    async def on_response(
        self,
        response: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Default: pass through."""
        return response
    
    async def on_error(
        self,
        error: Exception,
    ) -> Exception | None:
        """Default: re-raise error."""
        return error
    
    async def on_text_stream(
        self,
        chunk: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Default: pass through."""
        return chunk
    
    async def on_text_stream_end(self) -> dict[str, Any] | None:
        """Default: no additional content."""
        return None
    
    async def on_thinking_stream(
        self,
        chunk: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Default: pass through."""
        return chunk
    
    async def on_thinking_stream_end(self) -> dict[str, Any] | None:
        """Default: no additional content."""
        return None
    
    # ========== Agent Lifecycle Hooks ==========
    
    async def on_agent_start(
        self,
        input_data: Any,
    ) -> HookResult:
        """Default: continue."""
        return HookResult.proceed()
    
    async def on_agent_end(
        self,
        result: Any,
    ) -> HookResult:
        """Default: continue."""
        return HookResult.proceed()
    
    async def on_tool_call(
        self,
        tool: "BaseTool",
        params: dict[str, Any],
    ) -> HookResult:
        """Default: continue."""
        return HookResult.proceed()
    
    async def on_tool_call_delta(
        self,
        call_id: str,
        tool_name: str,
        delta: dict[str, Any],
        accumulated_args: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Default: pass through."""
        return delta
    
    async def on_tool_end(
        self,
        tool: "BaseTool",
        result: "ToolResult",
    ) -> HookResult:
        """Default: continue."""
        return HookResult.proceed()
    
    async def on_subagent_start(
        self,
        parent_agent_id: str,
        child_agent_id: str,
        mode: str,
    ) -> HookResult:
        """Default: continue."""
        return HookResult.proceed()
    
    async def on_subagent_end(
        self,
        parent_agent_id: str,
        child_agent_id: str,
        result: Any,
    ) -> HookResult:
        """Default: continue."""
        return HookResult.proceed()
    
    async def on_message_save(
        self,
        message: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Default: pass through."""
        return message


__all__ = [
    "Middleware",
    "BaseMiddleware",
]
