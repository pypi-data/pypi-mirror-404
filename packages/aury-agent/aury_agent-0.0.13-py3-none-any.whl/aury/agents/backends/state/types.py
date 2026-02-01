"""State backend types and protocols.

StateBackend is a simplified key-value storage for generic state.
For specific data types, use dedicated backends:
- SessionBackend: Session management
- InvocationBackend: Invocation management
- MessageBackend: Message storage
- MemoryBackend: Long-term memory
- ArtifactBackend: File/artifact storage

Architecture:
- StateStore: Low-level storage protocol (implemented by API layer)
- StateBackend: High-level interface (used by framework, wraps StateStore)
"""
from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class StateStore(Protocol):
    """Low-level storage protocol for state persistence.
    
    This is the interface that API/application layer implements.
    Provides raw key-value operations without namespace logic.
    
    Example implementations:
    - SQLAlchemyStateStore: Uses State table
    - RedisStateStore: Uses Redis
    - MemoryStateStore: In-memory dict
    """
    
    async def get(self, key: str) -> Any | None:
        """Get value by key."""
        ...
    
    async def set(self, key: str, value: Any) -> None:
        """Set value by key."""
        ...
    
    async def delete(self, key: str) -> bool:
        """Delete value by key. Returns True if deleted."""
        ...
    
    async def list(self, prefix: str = "") -> list[str]:
        """List keys with optional prefix filter."""
        ...
    
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        ...


@runtime_checkable
class StateBackend(Protocol):
    """Protocol for generic key-value state storage.
    
    Provides simple key-value storage with namespace isolation.
    Use for storing arbitrary state that doesn't fit other backends.
    
    Example namespaces:
    - "plan" - Plan state
    - "config" - Configuration
    - "cache" - Temporary cache
    - "workflow" - Workflow state
    
    Example usage:
        # Store plan state
        await backend.set("plan", "sess_123:plan", {"status": "active"})
        
        # Get plan state
        plan = await backend.get("plan", "sess_123:plan")
        
        # List all plans
        keys = await backend.list("plan")
    """
    
    async def get(self, namespace: str, key: str) -> Any | None:
        """Get value by key.
        
        Args:
            namespace: Namespace for isolation
            key: Storage key
            
        Returns:
            Stored value or None if not found
        """
        ...
    
    async def set(self, namespace: str, key: str, value: Any) -> None:
        """Set value by key.
        
        Args:
            namespace: Namespace for isolation
            key: Storage key
            value: Value to store (must be JSON-serializable)
        """
        ...
    
    async def delete(self, namespace: str, key: str) -> bool:
        """Delete value by key.
        
        Args:
            namespace: Namespace
            key: Storage key
            
        Returns:
            True if deleted, False if not found
        """
        ...
    
    async def list(self, namespace: str, prefix: str = "") -> list[str]:
        """List keys with optional prefix filter.
        
        Args:
            namespace: Namespace
            prefix: Optional key prefix filter
            
        Returns:
            List of matching keys
        """
        ...
    
    async def exists(self, namespace: str, key: str) -> bool:
        """Check if key exists.
        
        Args:
            namespace: Namespace
            key: Storage key
            
        Returns:
            True if exists
        """
        ...


class StoreBasedStateBackend:
    """StateBackend implementation that wraps a StateStore.
    
    This allows API layer to implement only the simple StateStore interface,
    while the framework provides namespace handling.
    
    Example:
        # API layer implements StateStore
        store = SQLAlchemyStateStore(session_factory, tenant_id)
        
        # Framework wraps it as StateBackend
        backend = StoreBasedStateBackend(store)
    """
    
    def __init__(self, store: StateStore):
        self._store = store
    
    def _make_key(self, namespace: str, key: str) -> str:
        """Combine namespace and key."""
        return f"{namespace}:{key}"
    
    async def get(self, namespace: str, key: str) -> Any | None:
        return await self._store.get(self._make_key(namespace, key))
    
    async def set(self, namespace: str, key: str, value: Any) -> None:
        await self._store.set(self._make_key(namespace, key), value)
    
    async def delete(self, namespace: str, key: str) -> bool:
        return await self._store.delete(self._make_key(namespace, key))
    
    async def list(self, namespace: str, prefix: str = "") -> list[str]:
        full_prefix = self._make_key(namespace, prefix)
        keys = await self._store.list(full_prefix)
        # Strip namespace prefix from results
        ns_prefix = f"{namespace}:"
        return [k[len(ns_prefix):] for k in keys if k.startswith(ns_prefix)]
    
    async def exists(self, namespace: str, key: str) -> bool:
        return await self._store.exists(self._make_key(namespace, key))


__all__ = ["StateBackend", "StateStore", "StoreBasedStateBackend"]
