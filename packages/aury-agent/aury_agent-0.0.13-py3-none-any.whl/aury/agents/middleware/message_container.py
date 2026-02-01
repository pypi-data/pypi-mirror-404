"""MessageContainerMiddleware - Groups thinking and text blocks under a message container.

This middleware creates a "message" container block when LLM request starts,
and all thinking/text blocks emitted during the LLM call will have parent_id
pointing to this container.

Usage:
    from aury.agents.middleware import MessageContainerMiddleware, MiddlewareChain
    
    chain = MiddlewareChain()
    chain.use(MessageContainerMiddleware())
    
    agent = ReactAgent.create(llm=llm, middleware=chain)

Result structure:
    message (block_id: blk_abc)
    ├── thinking (parent_id: blk_abc)
    └── text (parent_id: blk_abc)
    
    tool_use (parent_id: None) - not grouped
    tool_result (parent_id: None) - not grouped
"""
from __future__ import annotations

from typing import Any, TYPE_CHECKING

from .base import BaseMiddleware
from .types import HookResult
from ..core.context import set_parent_id, reset_parent_id, emit, get_parent_id
from ..core.types.session import generate_id
from ..core.types.block import BlockEvent, BlockKind, BlockOp
from ..core.logging import middleware_logger as logger

if TYPE_CHECKING:
    from ..core.types.tool import BaseTool, ToolResult


class MessageContainerMiddleware(BaseMiddleware):
    """Groups thinking and text blocks under a message container.
    
    When an LLM request starts, creates a "message" container block and sets
    the parent_id ContextVar. Only thinking and text blocks will inherit this
    parent_id (tool_use, tool_result, etc. are not grouped).
    
    This allows frontend to group thinking + text as a single unit for display.
    
    Args:
        apply_to_kinds: Set of block kinds that should inherit the container's
                       parent_id. Defaults to {"thinking", "text"}.
    """
    
    # Default kinds that should be grouped under message container
    DEFAULT_KINDS = {"thinking", "text"}
    
    def __init__(self, apply_to_kinds: set[str] | None = None):
        """Initialize with optional custom kinds filter.
        
        Args:
            apply_to_kinds: Block kinds to group. Defaults to {"thinking", "text"}.
        """
        super().__init__()
        self.apply_to_kinds = apply_to_kinds or self.DEFAULT_KINDS
        self._token: Any = None
        self._block_id: str | None = None
    
    async def on_request(
        self,
        request: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Create message container block and set parent_id."""
        from ..core.context import get_current_ctx_or_none
        ctx = get_current_ctx_or_none()
        
        # Generate container block ID
        message_block_id = generate_id("blk")
        
        logger.debug(
            "[MessageContainerMiddleware] Creating container",
            extra={"block_id": message_block_id, "apply_to_kinds": list(self.apply_to_kinds)}
        )
        
        # Emit the container block
        await emit(BlockEvent(
            block_id=message_block_id,
            kind="message",  # Container type
            op=BlockOp.APPLY,
            data={
                "type": "llm_response",
            },
            session_id=ctx.session_id if ctx else None,
            invocation_id=ctx.invocation_id if ctx else None,
        ))
        
        # Set parent_id in ContextVar with apply_to_kinds filter
        self._token = set_parent_id(message_block_id, apply_to_kinds=self.apply_to_kinds)
        self._block_id = message_block_id
        
        return request
    
    async def on_response(
        self,
        response: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Reset parent_id to previous value."""
        if self._token is not None:
            reset_parent_id(self._token)
            self._token = None
        return response
    
    async def on_error(
        self,
        error: Exception,
    ) -> Exception | None:
        """Reset parent_id on error too."""
        if self._token is not None:
            reset_parent_id(self._token)
            self._token = None
        return error
