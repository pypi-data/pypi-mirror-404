"""Middleware chain for sequential processing."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TYPE_CHECKING

from ..core.logging import middleware_logger as logger
from .types import TriggerMode, HookAction, HookResult
from .base import Middleware

if TYPE_CHECKING:
    from ..core.types.tool import BaseTool, ToolResult


@dataclass
class MiddlewareEntry:
    """Entry in middleware chain with inherit override."""
    middleware: Middleware
    inherit: bool  # Effective inherit value (config default or overridden)


class MiddlewareChain:
    """Chain of middlewares for sequential processing."""
    
    def __init__(self, middlewares: list[Middleware] | None = None) -> None:
        self._entries: list[MiddlewareEntry] = []
        self._token_buffer: str = ""
        self._token_count: int = 0
        
        # Add initial middlewares if provided
        if middlewares:
            logger.debug(f"MiddlewareChain init with {len(middlewares)} middlewares")
            for mw in middlewares:
                self.use(mw)
    
    @property
    def _middlewares(self) -> list[Middleware]:
        """Get middleware list."""
        return [e.middleware for e in self._entries]
    
    def use(
        self,
        middleware: Middleware,
        *,
        inherit: bool | None = None,
    ) -> "MiddlewareChain":
        """Add middleware to chain.
        
        Args:
            middleware: The middleware to add
            inherit: Override inherit setting (None = use middleware's config default)
        
        Maintains sorted order by priority.
        """
        effective_inherit = inherit if inherit is not None else middleware.config.inherit
        entry = MiddlewareEntry(middleware=middleware, inherit=effective_inherit)
        self._entries.append(entry)
        self._entries.sort(key=lambda e: e.middleware.config.priority)
        logger.debug(f"Added middleware to chain, priority={middleware.config.priority}, inherit={effective_inherit}, total={len(self._entries)}")
        return self
    
    def remove(self, middleware: Middleware) -> "MiddlewareChain":
        """Remove middleware from chain."""
        self._entries = [e for e in self._entries if e.middleware != middleware]
        return self
    
    def clear(self) -> "MiddlewareChain":
        """Clear all middlewares."""
        self._entries.clear()
        return self
    
    def get_inheritable(self) -> list[MiddlewareEntry]:
        """Get entries that should be inherited by sub-agents."""
        return [e for e in self._entries if e.inherit]
    
    def merge(self, other: "MiddlewareChain | None") -> "MiddlewareChain":
        """Merge this chain's inheritable middlewares with another chain.
        
        Creates a new chain with:
        - This chain's inheritable middlewares
        - All of other chain's middlewares
        
        Args:
            other: Chain to merge with (sub-agent's own middlewares)
            
        Returns:
            New merged MiddlewareChain
        """
        merged = MiddlewareChain()
        
        # Add inheritable from this chain
        for entry in self.get_inheritable():
            merged._entries.append(MiddlewareEntry(
                middleware=entry.middleware,
                inherit=entry.inherit,
            ))
        
        # Add all from other chain
        if other:
            for entry in other._entries:
                # Avoid duplicates (same middleware instance)
                if entry.middleware not in [e.middleware for e in merged._entries]:
                    merged._entries.append(MiddlewareEntry(
                        middleware=entry.middleware,
                        inherit=entry.inherit,
                    ))
        
        # Re-sort by priority
        merged._entries.sort(key=lambda e: e.middleware.config.priority)
        return merged
    
    async def process_request(
        self,
        request: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Process request through all middlewares."""
        current = request
        logger.debug(f"Processing request through {len(self._middlewares)} middlewares")
        
        for i, mw in enumerate(self._middlewares):
            result = await mw.on_request(current)
            if result is None:
                logger.info(f"Middleware #{i} blocked request")
                return None
            current = result
        
        logger.debug("Request processing completed")
        return current
    
    async def process_response(
        self,
        response: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Process response through all middlewares (reverse order)."""
        current = response
        logger.debug(f"Processing response through {len(self._middlewares)} middlewares (reverse order)")
        
        for i, mw in enumerate(reversed(self._middlewares)):
            result = await mw.on_response(current)
            if result is None:
                logger.info(f"Middleware #{i} blocked response")
                return None
            current = result
        
        logger.debug("Response processing completed")
        return current
    
    async def process_error(
        self,
        error: Exception,
    ) -> Exception | None:
        """Process error through all middlewares."""
        current = error
        logger.debug(f"Processing error {type(error).__name__} through {len(self._middlewares)} middlewares")
        
        for i, mw in enumerate(self._middlewares):
            result = await mw.on_error(current)
            if result is None:
                logger.info(f"Middleware #{i} suppressed error")
                return None
            current = result
        
        logger.debug("Error processing completed")
        return current
    
    async def process_text_stream(
        self,
        chunk: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Process text streaming chunk through middlewares based on trigger mode."""
        text = chunk.get("delta", "")
        self._token_buffer += text
        self._token_count += 1
        
        current = chunk
        
        for i, mw in enumerate(self._middlewares):
            should_trigger = self._should_trigger(mw, text)
            
            if should_trigger:
                result = await mw.on_text_stream(current)
                if result is None:
                    return None
                current = result
        
        # Log only every 50 tokens to reduce noise
        if self._token_count % 50 == 0:
            logger.debug(f"Text stream progress: token_count={self._token_count}")
        
        return current
    
    async def process_thinking_stream(
        self,
        chunk: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Process thinking streaming chunk through all middlewares."""
        current = chunk
        
        for i, mw in enumerate(self._middlewares):
            result = await mw.on_thinking_stream(current)
            if result is None:
                return None
            current = result
        
        return current
    
    async def process_tool_call_delta(
        self,
        call_id: str,
        tool_name: str,
        delta: dict[str, Any],
        accumulated_args: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Process tool call delta through all middlewares.
        
        Args:
            call_id: Tool call identifier
            tool_name: Name of the tool being called
            delta: Incremental parameter update
            accumulated_args: Current accumulated arguments state
            
        Returns:
            Modified delta, or None to skip emitting
        """
        current = delta
        logger.debug(f"Processing tool_call_delta for {tool_name} (call_id={call_id}) through {len(self._middlewares)} middlewares")
        
        for i, mw in enumerate(self._middlewares):
            result = await mw.on_tool_call_delta(call_id, tool_name, current, accumulated_args)
            if result is None:
                logger.info(f"Middleware #{i} blocked tool_call_delta")
                return None
            current = result
        
        logger.debug("Tool call delta processing completed")
        return current
    
    def _should_trigger(self, middleware: Middleware, text: str) -> bool:
        """Check if middleware should be triggered."""
        mode = middleware.config.trigger_mode
        
        if mode == TriggerMode.EVERY_TOKEN:
            return True
        elif mode == TriggerMode.EVERY_N_TOKENS:
            return self._token_count % middleware.config.trigger_n == 0
        elif mode == TriggerMode.ON_BOUNDARY:
            return self._is_boundary(text)
        
        return True
    
    def _is_boundary(self, text: str) -> bool:
        """Check if text ends with a sentence/paragraph boundary."""
        boundaries = (".", "。", "\n", "!", "?", "！", "？", ";", "；")
        return text.rstrip().endswith(boundaries)
    
    async def process_text_stream_end(self) -> list[dict[str, Any]]:
        """Process text stream end through all middlewares.
        
        Called when text stream ends, before on_response.
        Allows middlewares to flush any buffered content.
        
        Returns:
            List of final chunks to emit (may be empty)
        """
        final_chunks: list[dict[str, Any]] = []
        logger.debug(f"Processing text_stream_end through {len(self._middlewares)} middlewares")
        
        for i, mw in enumerate(self._middlewares):
            if hasattr(mw, 'on_text_stream_end'):
                result = await mw.on_text_stream_end()
                if result is not None:
                    logger.debug(f"Middleware #{i} returned final chunk on text_stream_end")
                    final_chunks.append(result)
        
        logger.debug(f"Text stream end processing completed, {len(final_chunks)} final chunks")
        return final_chunks
    
    async def process_thinking_stream_end(self) -> list[dict[str, Any]]:
        """Process thinking stream end through all middlewares.
        
        Called when thinking stream ends.
        Allows middlewares to flush any buffered thinking content.
        
        Returns:
            List of final thinking chunks to emit (may be empty)
        """
        final_chunks: list[dict[str, Any]] = []
        logger.debug(f"Processing thinking_stream_end through {len(self._middlewares)} middlewares")
        
        for i, mw in enumerate(self._middlewares):
            if hasattr(mw, 'on_thinking_stream_end'):
                result = await mw.on_thinking_stream_end()
                if result is not None:
                    logger.debug(f"Middleware #{i} returned final chunk on thinking_stream_end")
                    final_chunks.append(result)
        
        logger.debug(f"Thinking stream end processing completed, {len(final_chunks)} final chunks")
        return final_chunks
    
    def reset_stream_state(self) -> None:
        """Reset streaming state (call at start of new stream)."""
        logger.debug("Resetting stream state")
        self._token_buffer = ""
        self._token_count = 0
    
    @property
    def middlewares(self) -> list[Middleware]:
        """Get list of middlewares (read-only)."""
        return list(self._middlewares)
    
    # ========== Lifecycle Hook Processing ==========
    
    async def process_agent_start(
        self,
        input_data: Any,
    ) -> HookResult:
        """Process agent start through all middlewares.
        
        Returns:
            First non-CONTINUE result, or CONTINUE if all pass
        """
        logger.debug(f"Processing agent_start, {len(self._middlewares)} middlewares")
        for i, mw in enumerate(self._middlewares):
            if hasattr(mw, 'on_agent_start'):
                result = await mw.on_agent_start(input_data)
                if result.action != HookAction.CONTINUE:
                    logger.info(f"Middleware #{i} returned {result.action} on agent_start")
                    return result
        logger.debug("Agent start processing completed, all middlewares passed")
        return HookResult.proceed()
    
    async def process_agent_end(
        self,
        result: Any,
    ) -> HookResult:
        """Process agent end through all middlewares (reverse order)."""
        logger.debug(f"Processing agent_end, {len(self._middlewares)} middlewares (reverse order)")
        for i, mw in enumerate(reversed(self._middlewares)):
            if hasattr(mw, 'on_agent_end'):
                hook_result = await mw.on_agent_end(result)
                if hook_result.action != HookAction.CONTINUE:
                    logger.info(f"Middleware #{i} returned {hook_result.action} on agent_end")
                    return hook_result
        logger.debug("Agent end processing completed, all middlewares passed")
        return HookResult.proceed()
    
    async def process_tool_call(
        self,
        tool: "BaseTool",
        params: dict[str, Any],
    ) -> HookResult:
        """Process tool call through all middlewares.
        
        Returns:
            SKIP to skip tool, RETRY with modified_data to change params
        """
        logger.debug(f"Processing tool_call for tool={tool.name}, {len(self._middlewares)} middlewares")
        for i, mw in enumerate(self._middlewares):
            if hasattr(mw, 'on_tool_call'):
                result = await mw.on_tool_call(tool, params)
                if result.action != HookAction.CONTINUE:
                    logger.info(f"Middleware #{i} returned {result.action} on tool_call for tool={tool.name}")
                    return result
        logger.debug("Tool call processing completed, all middlewares passed")
        return HookResult.proceed()
    
    async def process_tool_end(
        self,
        tool: "BaseTool",
        result: "ToolResult",
    ) -> HookResult:
        """Process tool end through all middlewares (reverse order)."""
        logger.debug(f"Processing tool_end for tool={tool.name}, {len(self._middlewares)} middlewares (reverse order)")
        for i, mw in enumerate(reversed(self._middlewares)):
            if hasattr(mw, 'on_tool_end'):
                hook_result = await mw.on_tool_end(tool, result)
                if hook_result.action != HookAction.CONTINUE:
                    logger.info(f"Middleware #{i} returned {hook_result.action} on tool_end for tool={tool.name}")
                    return hook_result
        logger.debug("Tool end processing completed, all middlewares passed")
        return HookResult.proceed()
    
    async def process_subagent_start(
        self,
        parent_agent_id: str,
        child_agent_id: str,
        mode: str,
    ) -> HookResult:
        """Process sub-agent start through all middlewares."""
        logger.debug(f"Processing subagent_start, parent={parent_agent_id}, child={child_agent_id}, mode={mode}, {len(self._middlewares)} middlewares")
        for i, mw in enumerate(self._middlewares):
            if hasattr(mw, 'on_subagent_start'):
                result = await mw.on_subagent_start(
                    parent_agent_id, child_agent_id, mode
                )
                if result.action != HookAction.CONTINUE:
                    logger.info(f"Middleware #{i} returned {result.action} on subagent_start")
                    return result
        logger.debug("Subagent start processing completed, all middlewares passed")
        return HookResult.proceed()
    
    async def process_subagent_end(
        self,
        parent_agent_id: str,
        child_agent_id: str,
        result: Any,
    ) -> HookResult:
        """Process sub-agent end through all middlewares (reverse order)."""
        logger.debug(f"Processing subagent_end, parent={parent_agent_id}, child={child_agent_id}, {len(self._middlewares)} middlewares (reverse order)")
        for i, mw in enumerate(reversed(self._middlewares)):
            if hasattr(mw, 'on_subagent_end'):
                hook_result = await mw.on_subagent_end(
                    parent_agent_id, child_agent_id, result
                )
                if hook_result.action != HookAction.CONTINUE:
                    logger.info(f"Middleware #{i} returned {hook_result.action} on subagent_end")
                    return hook_result
        logger.debug("Subagent end processing completed, all middlewares passed")
        return HookResult.proceed()
    
    async def process_message_save(
        self,
        message: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Process message save through all middlewares.
        
        Args:
            message: Message to be saved
            
        Returns:
            Modified message, or None to skip saving
        """
        current = message
        logger.debug(f"Processing message_save, role={message.get('role')}, {len(self._middlewares)} middlewares")
        
        for i, mw in enumerate(self._middlewares):
            if hasattr(mw, 'on_message_save'):
                result = await mw.on_message_save(current)
                if result is None:
                    logger.info(f"Middleware #{i} blocked message save for role={message.get('role')}")
                    return None
                current = result
        
        logger.debug("Message save processing completed, all middlewares passed")
        return current


__all__ = ["MiddlewareChain"]
