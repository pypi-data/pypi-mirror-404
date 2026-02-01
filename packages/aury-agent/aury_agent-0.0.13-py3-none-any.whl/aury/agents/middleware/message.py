"""Message persistence middleware.

Uses backends.message directly to persist messages.

Usage:
    middleware = MessageBackendMiddleware()
    
    agent = ReactAgent.create(
        llm=llm,
        middlewares=[middleware],
    )
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .base import BaseMiddleware

if TYPE_CHECKING:
    from ..backends import MessageBackend


class MessageBackendMiddleware(BaseMiddleware):
    """Middleware that persists messages via MessageBackend.
    
    Simple middleware that passes messages to the backend.
    Storage details (raw/truncated handling) are left to the application layer.
    
    Example:
        agent = ReactAgent.create(
            llm=llm,
            middlewares=[MessageBackendMiddleware()],
        )
    """
    
    async def on_message_save(
        self,
        message: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Save message via backends.message.
        
        Args:
            message: Message dict with 'role', 'content', etc.
            
        Returns:
            The message (pass through to other middlewares)
        """
        from ..core.context import get_current_ctx_or_none
        
        # Get MessageBackend from context
        ctx = get_current_ctx_or_none()
        if ctx is None or ctx.backends is None or ctx.backends.message is None:
            # No backend available, pass through
            return message
        
        session_id = ctx.session_id or ""
        if not session_id:
            return message
        
        backend = ctx.backends.message
        invocation_id = ctx.invocation_id or ""
        agent_id = ctx.agent_id
        
        # Save message
        await backend.add(
            session_id=session_id,
            message=message,
            agent_id=agent_id,
            invocation_id=invocation_id,
        )
        
        # Pass through to other middlewares
        return message


__all__ = ["MessageBackendMiddleware"]
