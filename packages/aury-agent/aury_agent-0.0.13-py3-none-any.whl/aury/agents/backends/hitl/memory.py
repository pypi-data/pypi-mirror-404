"""In-memory HITL backend implementation."""
from __future__ import annotations

import time
from typing import Any


class InMemoryHITLBackend:
    """In-memory HITL backend for development/testing."""
    
    def __init__(self) -> None:
        self._records: dict[str, dict[str, Any]] = {}
    
    async def create(
        self,
        *,
        hitl_id: str,
        hitl_type: str,
        session_id: str,
        invocation_id: str,
        data: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        block_id: str | None = None,
        resume_mode: str = "response",
        tool_state: dict[str, Any] | None = None,
        checkpoint_id: str | None = None,
        tool_name: str | None = None,
        tool_call_id: str | None = None,
        node_id: str | None = None,
        expires_at: int | None = None,
    ) -> None:
        """Create a new HITL record."""
        now = int(time.time())
        self._records[hitl_id] = {
            "hitl_id": hitl_id,
            "hitl_type": hitl_type,
            "session_id": session_id,
            "invocation_id": invocation_id,
            "data": data or {},
            "metadata": metadata or {},
            "block_id": block_id,
            "status": "pending",
            "resume_mode": resume_mode,
            "tool_state": tool_state,
            "checkpoint_id": checkpoint_id,
            "tool_name": tool_name,
            "tool_call_id": tool_call_id,
            "node_id": node_id,
            "expires_at": expires_at,
            "user_response": None,
            "responded_at": None,
            "created_at": now,
            "updated_at": now,
        }
    
    async def get(self, hitl_id: str) -> dict[str, Any] | None:
        """Get HITL record by ID."""
        return self._records.get(hitl_id)
    
    async def respond(
        self,
        hitl_id: str,
        user_response: dict[str, Any],
    ) -> None:
        """Record user response to HITL."""
        if hitl_id in self._records:
            now = int(time.time())
            self._records[hitl_id]["status"] = "completed"
            self._records[hitl_id]["user_response"] = user_response
            self._records[hitl_id]["responded_at"] = now
            self._records[hitl_id]["updated_at"] = now
    
    async def cancel(self, hitl_id: str) -> None:
        """Cancel a pending HITL request."""
        if hitl_id in self._records:
            self._records[hitl_id]["status"] = "cancelled"
            self._records[hitl_id]["updated_at"] = int(time.time())
    
    async def get_pending_by_session(
        self,
        session_id: str,
    ) -> list[dict[str, Any]]:
        """Get all pending HITL for a session."""
        return [
            r for r in self._records.values()
            if r["session_id"] == session_id and r["status"] == "pending"
        ]
    
    async def get_pending_by_invocation(
        self,
        invocation_id: str,
    ) -> list[dict[str, Any]]:
        """Get all pending HITL for an invocation."""
        return [
            r for r in self._records.values()
            if r["invocation_id"] == invocation_id and r["status"] == "pending"
        ]


__all__ = ["InMemoryHITLBackend"]
