"""Event bus for pub/sub messaging."""
from __future__ import annotations

import asyncio
from typing import Any, Callable, Awaitable
from enum import Enum

from ..logging import bus_logger as logger


class Events:
    """Predefined event types."""
    
    # Session lifecycle
    SESSION_CREATED = "session.created"
    SESSION_UPDATED = "session.updated"
    SESSION_ENDED = "session.ended"
    
    # Invocation lifecycle
    INVOCATION_START = "invocation.start"
    INVOCATION_END = "invocation.end"
    INVOCATION_ERROR = "invocation.error"
    INVOCATION_CANCELLED = "invocation.cancelled"
    
    # Unified block event (used by ctx.emit())
    BLOCK = "block"  # Main streaming event for all block outputs
    
    # Block lifecycle events (for persistence/logging)
    BLOCK_CREATED = "block.created"
    BLOCK_UPDATED = "block.updated"
    BLOCK_DELTA = "block.delta"
    BLOCK_CLOSED = "block.closed"
    
    # Tool events
    TOOL_START = "tool.start"
    TOOL_END = "tool.end"
    TOOL_ERROR = "tool.error"
    
    # Workflow node events
    NODE_START = "node.start"
    NODE_END = "node.end"
    NODE_ERROR = "node.error"
    NODE_SKIPPED = "node.skipped"
    
    # LLM events
    LLM_START = "llm.start"
    LLM_END = "llm.end"
    LLM_STREAM = "llm.stream"
    
    # Memory events
    MEMORY_ADD = "memory.add"
    MEMORY_SEARCH = "memory.search"
    
    # Usage events
    USAGE_RECORDED = "usage.recorded"
    
    # Permission events
    PERMISSION_REQUESTED = "permission.requested"
    PERMISSION_RESOLVED = "permission.resolved"
    
    # State events
    STATE_CHANGED = "state.changed"
    STATE_REVERTED = "state.reverted"


EventHandler = Callable[[str, Any], Awaitable[None]] | Callable[[str, Any], None]


class EventBus:
    """Event bus with pub/sub support.
    
    Features:
    - Async and sync handlers
    - Wildcard subscription with "*"
    - Handler errors don't block other handlers
    """
    
    def __init__(self) -> None:
        self._subscriptions: dict[str, list[EventHandler]] = {}
        self._lock = asyncio.Lock()
    
    async def publish(self, event_type: str, payload: Any) -> None:
        """Publish event to all subscribers.
        
        Args:
            event_type: Event type string
            payload: Event payload (any data)
        """
        handlers: list[EventHandler] = []
        
        async with self._lock:
            # Exact match
            handlers.extend(self._subscriptions.get(event_type, []))
            # Wildcard match
            handlers.extend(self._subscriptions.get("*", []))
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event_type, payload)
                else:
                    handler(event_type, payload)
            except Exception as e:
                logger.error(
                    "Event handler error",
                    extra={"event_type": event_type, "error": str(e)},
                    exc_info=True,
                )
    
    def subscribe(self, event_type: str, handler: EventHandler) -> Callable[[], None]:
        """Subscribe to event type.
        
        Args:
            event_type: Event type to subscribe to, or "*" for all
            handler: Callback function (async or sync)
        
        Returns:
            Unsubscribe function
        """
        if event_type not in self._subscriptions:
            self._subscriptions[event_type] = []
        
        self._subscriptions[event_type].append(handler)
        
        def unsubscribe() -> None:
            if event_type in self._subscriptions:
                try:
                    self._subscriptions[event_type].remove(handler)
                except ValueError:
                    pass
        
        return unsubscribe
    
    def on(self, event_type: str) -> Callable[[EventHandler], EventHandler]:
        """Decorator for subscribing to events.
        
        Usage:
            @bus.on("session.created")
            async def handler(event_type, payload):
                ...
        """
        def decorator(handler: EventHandler) -> EventHandler:
            self.subscribe(event_type, handler)
            return handler
        return decorator
    
    def clear(self) -> None:
        """Clear all subscriptions."""
        self._subscriptions.clear()
    
    def subscriber_count(self, event_type: str | None = None) -> int:
        """Get number of subscribers.
        
        Args:
            event_type: Specific event type, or None for total count
        """
        if event_type:
            return len(self._subscriptions.get(event_type, []))
        return sum(len(handlers) for handlers in self._subscriptions.values())


class EventCollector:
    """Collects events for testing/debugging.
    
    Usage:
        collector = EventCollector(bus)
        collector.start()
        # ... do stuff ...
        events = collector.stop()
    """
    
    def __init__(self, bus: EventBus, event_types: list[str] | None = None):
        self.bus = bus
        self.event_types = event_types  # None means all
        self.events: list[tuple[str, Any]] = []
        self._unsubscribers: list[Callable[[], None]] = []
    
    def _handler(self, event_type: str, payload: Any) -> None:
        if self.event_types is None or event_type in self.event_types:
            self.events.append((event_type, payload))
    
    def start(self) -> None:
        """Start collecting events."""
        if self.event_types:
            for event_type in self.event_types:
                unsub = self.bus.subscribe(event_type, self._handler)
                self._unsubscribers.append(unsub)
        else:
            unsub = self.bus.subscribe("*", self._handler)
            self._unsubscribers.append(unsub)
    
    def stop(self) -> list[tuple[str, Any]]:
        """Stop collecting and return events."""
        for unsub in self._unsubscribers:
            unsub()
        self._unsubscribers.clear()
        return self.events
    
    def clear(self) -> None:
        """Clear collected events."""
        self.events.clear()
