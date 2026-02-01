"""MessageContextProvider - provides conversation history messages.

This provider ONLY fetches message history for context.
Message saving is handled by Middleware (on_message_save hook).

Recovery Strategy:
- Check State for complete messages (from pending/crashed invocation)
- If found, use State messages (complete, not truncated)
- Otherwise, load from MessageBackend (truncated historical messages)
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from .base import BaseContextProvider, AgentContext

if TYPE_CHECKING:
    from ..core.context import InvocationContext
    from ..backends import MessageBackend

logger = logging.getLogger(__name__)


class MessageContextProvider(BaseContextProvider):
    """Message history context provider.
    
    Provides conversation history messages for LLM context.
    Uses ctx.backends.message directly.
    
    Features:
    - Load messages via MessageBackend
    - Priority: State (complete) > MessageBackend (truncated)
    - Turn limits handled by backend
    
    Note: Message SAVING is not done here.
    Use MessageBackendMiddleware for saving messages.
    """
    
    _name = "messages"
    
    def __init__(self, *, max_messages: int = 100):
        """Initialize MessageContextProvider.
        
        Args:
            max_messages: Max messages to fetch
        """
        self.max_messages = max_messages
    
    async def fetch(self, ctx: "InvocationContext") -> AgentContext:
        """Fetch conversation history.
        
        Priority:
        1. Check State for complete messages (from pending/crashed inv)
        2. Fall back to MessageBackend (truncated historical messages)
        
        Returns:
            AgentContext with messages list
        """
        # Try to get complete messages from State (pending/crashed recovery)
        state_messages = await self._get_messages_from_state(ctx)
        if state_messages:
            logger.debug(
                f"Loaded {len(state_messages)} messages from State (complete)",
                extra={"session_id": ctx.session.id},
            )
            return AgentContext(messages=state_messages)
        
        # Fall back to MessageBackend
        messages = await self._fetch_from_backend(ctx)
        logger.debug(
            f"Loaded {len(messages)} messages from backend (may be truncated)",
            extra={"session_id": ctx.session.id},
        )
        return AgentContext(messages=messages)
    
    async def _fetch_from_backend(self, ctx: "InvocationContext") -> list[dict[str, Any]]:
        """Fetch messages from MessageBackend."""
        if ctx.backends is not None and ctx.backends.message is not None:
            messages = await ctx.backends.message.get(
                session_id=ctx.session.id,
                limit=self.max_messages,
            )
            # Convert to LLM format (include tool_call_id for tool messages)
            result = []
            for m in messages:
                msg = {"role": m["role"], "content": m["content"]}
                if m.get("tool_call_id"):
                    msg["tool_call_id"] = m["tool_call_id"]
                result.append(msg)
            return result
        
        # No backend available
        logger.warning(
            "No message backend available for MessageContextProvider",
            extra={"session_id": ctx.session.id},
        )
        return []
    
    async def _get_messages_from_state(self, ctx: "InvocationContext") -> list[dict[str, Any]] | None:
        """Try to get complete messages from State.
        
        State stores complete (not truncated) messages during execution.
        This allows recovery from:
        - HITL suspend
        - Process crash
        - Abnormal termination
        
        Returns:
            List of message dicts if found, None otherwise
        """
        if not ctx.state:
            return None
        
        # Check if State has message_history
        messages_data = ctx.state.get("agent.message_history")
        if not messages_data:
            return None
        
        if not isinstance(messages_data, list):
            return None
        
        # Validate and convert to expected format
        messages: list[dict[str, Any]] = []
        for msg in messages_data:
            if isinstance(msg, dict) and "role" in msg:
                messages.append(msg)
        
        return messages if messages else None


__all__ = ["MessageContextProvider"]
