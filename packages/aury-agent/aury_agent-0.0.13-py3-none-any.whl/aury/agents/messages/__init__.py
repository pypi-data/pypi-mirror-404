"""Message types for conversation history.

Note: Message persistence is now handled by:
- MessageBackend (backends/message/): Storage layer
- MessageBackendMiddleware (middleware/message.py): Save via on_message_save hook
- MessageContextProvider (context_providers/message.py): Fetch for context

This module provides message types used across the system.
"""
from .types import (
    MessageRole,
    Message,
)
from .store import (
    MessageStore,
    InMemoryMessageStore,
)
from .config import (
    MessageConfig,
)

__all__ = [
    # Types
    "MessageRole",
    "Message",
    # Store (protocol + in-memory for testing)
    "MessageStore",
    "InMemoryMessageStore",
    # Config
    "MessageConfig",
]
