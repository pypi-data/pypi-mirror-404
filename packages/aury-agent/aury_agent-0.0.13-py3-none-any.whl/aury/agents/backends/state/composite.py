"""Composite state backend that routes by namespace."""
from __future__ import annotations

from typing import Any

from .types import StateBackend


class CompositeStateBackend:
    """Routes operations to different backends by namespace.
    
    Example:
        backend = CompositeStateBackend({
            "session": FileStateBackend("./data/sessions"),
            "usage": PostgresBackend(db),
        }, default=MemoryStateBackend())
    """
    
    def __init__(
        self,
        backends: dict[str, StateBackend],
        default: StateBackend | None = None,
    ):
        self._backends = backends
        self._default = default
    
    def _get_backend(self, namespace: str) -> StateBackend:
        backend = self._backends.get(namespace, self._default)
        if backend is None:
            raise ValueError(f"No backend for namespace: {namespace}")
        return backend
    
    async def get(self, namespace: str, key: str) -> Any | None:
        return await self._get_backend(namespace).get(namespace, key)
    
    async def set(self, namespace: str, key: str, value: Any) -> None:
        await self._get_backend(namespace).set(namespace, key, value)
    
    async def delete(self, namespace: str, key: str) -> bool:
        return await self._get_backend(namespace).delete(namespace, key)
    
    async def list(self, namespace: str, prefix: str = "") -> list[str]:
        return await self._get_backend(namespace).list(namespace, prefix)
    
    async def exists(self, namespace: str, key: str) -> bool:
        return await self._get_backend(namespace).exists(namespace, key)


__all__ = ["CompositeStateBackend"]
