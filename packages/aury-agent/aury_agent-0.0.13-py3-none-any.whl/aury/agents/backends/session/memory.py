"""In-memory session backend implementation."""
from __future__ import annotations

from datetime import datetime
from typing import Any


class InMemorySessionBackend:
    """In-memory implementation of SessionBackend.
    
    Suitable for testing and simple single-process use cases.
    Data is lost when the process exits.
    """
    
    def __init__(self) -> None:
        self._sessions: dict[str, dict[str, Any]] = {}
        # Index: user_id -> list of session_ids
        self._user_sessions: dict[str, list[str]] = {}
    
    async def create(
        self,
        id: str,
        data: dict[str, Any],
        user_id: str | None = None,
    ) -> None:
        """Create a new session."""
        session_data = {
            "id": id,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            **data,
        }
        self._sessions[id] = session_data
        
        # Update user index
        if user_id:
            if user_id not in self._user_sessions:
                self._user_sessions[user_id] = []
            self._user_sessions[user_id].append(id)
    
    async def get(self, id: str) -> dict[str, Any] | None:
        """Get session by ID."""
        return self._sessions.get(id)
    
    async def update(self, id: str, data: dict[str, Any]) -> None:
        """Update session data."""
        if id in self._sessions:
            self._sessions[id].update(data)
            self._sessions[id]["updated_at"] = datetime.now().isoformat()
    
    async def delete(self, id: str) -> bool:
        """Delete a session."""
        if id not in self._sessions:
            return False
        
        session = self._sessions.pop(id)
        
        # Update user index
        user_id = session.get("user_id")
        if user_id and user_id in self._user_sessions:
            self._user_sessions[user_id] = [
                sid for sid in self._user_sessions[user_id] if sid != id
            ]
        
        return True
    
    async def list(
        self,
        user_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        """List sessions."""
        if user_id:
            # Filter by user
            session_ids = self._user_sessions.get(user_id, [])
            sessions = [
                self._sessions[sid]
                for sid in session_ids
                if sid in self._sessions
            ]
        else:
            sessions = list(self._sessions.values())
        
        # Sort by created_at descending (newest first)
        sessions.sort(key=lambda s: s.get("created_at", ""), reverse=True)
        
        # Apply pagination
        return sessions[offset:offset + limit]


__all__ = ["InMemorySessionBackend"]
