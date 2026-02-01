"""In-memory invocation backend implementation."""
from __future__ import annotations

from datetime import datetime
from typing import Any


class InMemoryInvocationBackend:
    """In-memory implementation of InvocationBackend.
    
    Suitable for testing and simple single-process use cases.
    """
    
    def __init__(self) -> None:
        self._invocations: dict[str, dict[str, Any]] = {}
        self._session_invocations: dict[str, list[str]] = {}
    
    async def create(
        self,
        id: str,
        session_id: str,
        data: dict[str, Any],
        agent_id: str | None = None,
    ) -> None:
        """Create a new invocation."""
        invocation_data = {
            "id": id,
            "session_id": session_id,
            "agent_id": agent_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            **data,
        }
        self._invocations[id] = invocation_data
        
        if session_id not in self._session_invocations:
            self._session_invocations[session_id] = []
        self._session_invocations[session_id].append(id)
    
    async def get(self, id: str) -> dict[str, Any] | None:
        """Get invocation by ID."""
        return self._invocations.get(id)
    
    async def update(self, id: str, data: dict[str, Any]) -> None:
        """Update invocation data."""
        if id in self._invocations:
            self._invocations[id].update(data)
            self._invocations[id]["updated_at"] = datetime.now().isoformat()
    
    async def delete(self, id: str) -> bool:
        """Delete an invocation."""
        if id not in self._invocations:
            return False
        
        inv = self._invocations.pop(id)
        session_id = inv.get("session_id")
        if session_id and session_id in self._session_invocations:
            self._session_invocations[session_id] = [
                iid for iid in self._session_invocations[session_id] if iid != id
            ]
        return True
    
    async def list_by_session(
        self,
        session_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List invocations for a session."""
        inv_ids = self._session_invocations.get(session_id, [])
        invocations = [self._invocations[iid] for iid in inv_ids if iid in self._invocations]
        invocations.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return invocations[offset:offset + limit]
    
    async def get_latest(self, session_id: str) -> dict[str, Any] | None:
        """Get the latest invocation for a session."""
        invocations = await self.list_by_session(session_id, limit=1)
        return invocations[0] if invocations else None


__all__ = ["InMemoryInvocationBackend"]
