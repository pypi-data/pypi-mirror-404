"""State backend for framework internal storage.

Used for storing session state, plan data, invocation records, messages, etc.
This is NOT for user file operations - use FileBackend for that.

Architecture:
- StateStore: Low-level protocol for API layer to implement
- StateBackend: High-level protocol with namespace support
- StoreBasedStateBackend: Wraps StateStore as StateBackend

Default implementations: SQLiteStateBackend, MemoryStateBackend
"""
from .types import StateBackend, StateStore, StoreBasedStateBackend
from .sqlite import SQLiteStateBackend
from .memory import MemoryStateBackend
from .file import FileStateBackend
from .composite import CompositeStateBackend

__all__ = [
    # Protocols
    "StateBackend",
    "StateStore",
    # Implementations
    "StoreBasedStateBackend",  # Wraps StateStore
    "SQLiteStateBackend",  # Default
    "MemoryStateBackend",  # For testing
    "FileStateBackend",
    "CompositeStateBackend",
]
