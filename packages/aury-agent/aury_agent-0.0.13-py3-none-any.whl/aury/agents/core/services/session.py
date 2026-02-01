"""Session service protocol."""
from __future__ import annotations

from abc import abstractmethod
from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from ..types.session import Session, ControlFrame


class SessionService(Protocol):
    """Protocol for session management.
    
    Handles session CRUD and control stack operations.
    """
    
    @abstractmethod
    async def create(self, root_agent_id: str, **kwargs) -> "Session":
        """Create a new session."""
        ...
    
    @abstractmethod
    async def get(self, session_id: str) -> "Session | None":
        """Get session by ID."""
        ...
    
    @abstractmethod
    async def update(self, session: "Session") -> None:
        """Update session."""
        ...
    
    @abstractmethod
    async def delete(self, session_id: str) -> bool:
        """Delete session."""
        ...
    
    @abstractmethod
    async def list(self, limit: int = 100, offset: int = 0) -> list["Session"]:
        """List sessions."""
        ...
    
    @abstractmethod
    async def push_control(self, session_id: str, frame: "ControlFrame") -> None:
        """Push control frame to session's control stack."""
        ...
    
    @abstractmethod
    async def pop_control(self, session_id: str) -> "ControlFrame | None":
        """Pop control frame from session's control stack."""
        ...


__all__ = ["SessionService"]
