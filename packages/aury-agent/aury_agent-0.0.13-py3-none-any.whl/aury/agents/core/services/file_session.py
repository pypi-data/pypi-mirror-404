"""File-based session service implementation."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..logging import session_logger as logger
from ..types.session import Session, ControlFrame


class FileSessionService:
    """File-based session storage.
    
    Stores sessions as JSON files in a directory.
    Suitable for development and single-instance deployments.
    
    Directory structure:
        {base_dir}/
            {session_id}.json
    """
    
    def __init__(self, base_dir: str | Path):
        """Initialize file session service.
        
        Args:
            base_dir: Directory to store session files
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    def _session_path(self, session_id: str) -> Path:
        """Get file path for session."""
        # Sanitize ID to prevent path traversal
        safe_id = "".join(c for c in session_id if c.isalnum() or c in "-_")
        return self.base_dir / f"{safe_id}.json"
    
    async def create(self, root_agent_id: str, **kwargs) -> Session:
        """Create a new session."""
        session = Session(root_agent_id=root_agent_id, **kwargs)
        await self._save(session)
        logger.debug(f"Created session: {session.id}")
        return session
    
    async def get(self, session_id: str) -> Session | None:
        """Get session by ID."""
        path = self._session_path(session_id)
        if not path.exists():
            return None
        
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return Session.from_dict(data)
        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {e}")
            return None
    
    async def update(self, session: Session) -> None:
        """Update session."""
        await self._save(session)
        logger.debug(f"Updated session: {session.id}")
    
    async def delete(self, session_id: str) -> bool:
        """Delete session."""
        path = self._session_path(session_id)
        if path.exists():
            try:
                path.unlink()
                logger.debug(f"Deleted session: {session_id}")
                return True
            except Exception as e:
                logger.error(f"Failed to delete session {session_id}: {e}")
        return False
    
    async def list(self, limit: int = 100, offset: int = 0) -> list[Session]:
        """List sessions, ordered by updated_at descending."""
        sessions = []
        
        for path in self.base_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                sessions.append(Session.from_dict(data))
            except Exception as e:
                logger.warning(f"Failed to load session file {path}: {e}")
                continue
        
        # Sort by updated_at descending
        sessions.sort(key=lambda s: s.updated_at, reverse=True)
        
        # Apply pagination
        return sessions[offset : offset + limit]
    
    async def push_control(self, session_id: str, frame: ControlFrame) -> None:
        """Push control frame to session's control stack."""
        session = await self.get(session_id)
        if session is None:
            raise ValueError(f"Session not found: {session_id}")
        
        session.push_control(frame)
        await self._save(session)
        logger.debug(f"Pushed control frame to session {session_id}: {frame.agent_id}")
    
    async def pop_control(self, session_id: str) -> ControlFrame | None:
        """Pop control frame from session's control stack."""
        session = await self.get(session_id)
        if session is None:
            raise ValueError(f"Session not found: {session_id}")
        
        frame = session.pop_control()
        if frame:
            await self._save(session)
            logger.debug(f"Popped control frame from session {session_id}: {frame.agent_id}")
        return frame
    
    async def _save(self, session: Session) -> None:
        """Save session to file."""
        path = self._session_path(session.id)
        try:
            path.write_text(
                json.dumps(session.to_dict(), indent=2, ensure_ascii=False),
                encoding="utf-8"
            )
        except Exception as e:
            logger.error(f"Failed to save session {session.id}: {e}")
            raise
    
    async def get_by_root_agent(self, root_agent_id: str, limit: int = 100) -> list[Session]:
        """Get sessions by root agent ID."""
        all_sessions = await self.list(limit=10000)  # Get all
        return [
            s for s in all_sessions
            if s.root_agent_id == root_agent_id
        ][:limit]
    
    async def get_active(self, limit: int = 100) -> list[Session]:
        """Get active sessions."""
        all_sessions = await self.list(limit=10000)
        return [
            s for s in all_sessions
            if s.is_active
        ][:limit]


__all__ = ["FileSessionService"]
