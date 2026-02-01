"""In-memory state backend for testing."""
from __future__ import annotations

from typing import Any


class MemoryStateBackend:
    """In-memory state backend for testing."""
    
    def __init__(self) -> None:
        self._data: dict[str, dict[str, Any]] = {}
        self._messages: dict[str, list[dict[str, Any]]] = {}  # session_id -> messages
    
    async def get(self, namespace: str, key: str) -> Any | None:
        return self._data.get(namespace, {}).get(key)
    
    async def set(self, namespace: str, key: str, value: Any) -> None:
        if namespace not in self._data:
            self._data[namespace] = {}
        self._data[namespace][key] = value
    
    async def delete(self, namespace: str, key: str) -> bool:
        if namespace in self._data and key in self._data[namespace]:
            del self._data[namespace][key]
            return True
        return False
    
    async def list(self, namespace: str, prefix: str = "") -> list[str]:
        if namespace not in self._data:
            return []
        return [k for k in self._data[namespace] if k.startswith(prefix)]
    
    async def exists(self, namespace: str, key: str) -> bool:
        return namespace in self._data and key in self._data[namespace]
    
    async def add_message(self, session_id: str, message: dict[str, Any]) -> None:
        """Add a message to session history."""
        if session_id not in self._messages:
            self._messages[session_id] = []
        self._messages[session_id].append(message)
    
    async def get_messages(self, session_id: str) -> list[dict[str, Any]]:
        """Get all messages for a session."""
        return self._messages.get(session_id, [])
    
    def clear(self) -> None:
        """Clear all data (for testing)."""
        self._data.clear()
        self._messages.clear()


__all__ = ["MemoryStateBackend"]
