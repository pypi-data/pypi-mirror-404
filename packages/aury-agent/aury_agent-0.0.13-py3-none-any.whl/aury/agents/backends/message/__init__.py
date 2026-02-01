"""Message backend."""
from .types import MessageBackend
from .memory import InMemoryMessageBackend

__all__ = [
    "MessageBackend",
    "InMemoryMessageBackend",
]
