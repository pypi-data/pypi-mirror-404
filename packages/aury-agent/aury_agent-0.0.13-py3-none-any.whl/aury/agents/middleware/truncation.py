"""MessageTruncationMiddleware - truncates large message content before persistence.

This middleware intercepts on_message_save and truncates content
that exceeds configured limits, ensuring historical messages don't
consume excessive storage.

Current invocation messages remain complete in State (for recovery),
only persisted messages get truncated.
"""
from __future__ import annotations

from typing import Any

from .base import BaseMiddleware


class MessageTruncationMiddleware(BaseMiddleware):
    """Truncates large message content before persistence.
    
    Use this middleware BEFORE MessageBackendMiddleware in the chain:
    
        middleware = MiddlewareChain([
            MessageTruncationMiddleware(max_content_length=2000),
            MessageBackendMiddleware(),
        ])
    
    Features:
    - Truncates string content exceeding max_content_length
    - Truncates individual items in list content (tool_use, tool_result)
    - Adds "[truncated]" marker to truncated content
    - Configurable truncation threshold
    """
    
    def __init__(
        self,
        max_content_length: int = 2000,
        truncate_marker: str = "... [truncated]",
    ):
        """Initialize MessageTruncationMiddleware.
        
        Args:
            max_content_length: Maximum content length before truncation
            truncate_marker: Marker appended to truncated content
        """
        self.max_content_length = max_content_length
        self.truncate_marker = truncate_marker
    
    async def on_message_save(
        self,
        message: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Truncate message content before saving.
        
        Args:
            message: Message dict with 'role', 'content', etc.
            
        Returns:
            Modified message with truncated content
        """
        content = message.get("content")
        if content is None:
            return message
        
        # Create a copy to avoid mutating original
        truncated_message = message.copy()
        truncated_message["content"] = self._truncate_content(content)
        
        return truncated_message
    
    def _truncate_content(self, content: Any) -> Any:
        """Truncate content based on type.
        
        Args:
            content: String or list content
            
        Returns:
            Truncated content
        """
        if isinstance(content, str):
            return self._truncate_string(content)
        
        if isinstance(content, list):
            return self._truncate_list(content)
        
        # Unknown type, return as-is
        return content
    
    def _truncate_string(self, text: str) -> str:
        """Truncate string content."""
        if len(text) <= self.max_content_length:
            return text
        
        # Keep first part, add marker
        return text[:self.max_content_length] + self.truncate_marker
    
    def _truncate_list(self, items: list[Any]) -> list[Any]:
        """Truncate list content (tool_use, tool_result, etc.)."""
        truncated_items = []
        
        for item in items:
            if isinstance(item, dict):
                truncated_item = item.copy()
                
                # Truncate text content
                if "text" in truncated_item and isinstance(truncated_item["text"], str):
                    truncated_item["text"] = self._truncate_string(truncated_item["text"])
                
                # Truncate tool_result content
                if "content" in truncated_item and isinstance(truncated_item["content"], str):
                    truncated_item["content"] = self._truncate_string(truncated_item["content"])
                
                # Truncate tool_use input (arguments)
                if "input" in truncated_item and isinstance(truncated_item["input"], dict):
                    truncated_item["input"] = self._truncate_dict(truncated_item["input"])
                
                truncated_items.append(truncated_item)
            else:
                truncated_items.append(item)
        
        return truncated_items
    
    def _truncate_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """Truncate string values in a dict (for tool arguments)."""
        truncated = {}
        for key, value in data.items():
            if isinstance(value, str):
                truncated[key] = self._truncate_string(value)
            elif isinstance(value, dict):
                truncated[key] = self._truncate_dict(value)
            elif isinstance(value, list):
                truncated[key] = self._truncate_list(value)
            else:
                truncated[key] = value
        return truncated


__all__ = ["MessageTruncationMiddleware"]
