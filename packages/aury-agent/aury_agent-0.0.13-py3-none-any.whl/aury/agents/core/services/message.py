"""Message service protocol."""
from __future__ import annotations

from abc import abstractmethod
from typing import Any, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from ..types.block import BlockEvent, PersistedBlock
    from ..types.message import Message


class MessageService(Protocol):
    """Protocol for message/block management.
    
    Handles message and block persistence.
    """
    
    @abstractmethod
    async def append(
        self,
        session_id: str,
        invocation_id: str,
        block: "BlockEvent",
    ) -> "PersistedBlock":
        """Append a block to the message history."""
        ...
    
    @abstractmethod
    async def list_blocks(
        self,
        session_id: str,
        invocation_id: str | None = None,
        limit: int = 100,
    ) -> list["PersistedBlock"]:
        """List blocks for a session/invocation."""
        ...
    
    @abstractmethod
    async def update_block(
        self,
        block_id: str,
        data: dict[str, Any],
    ) -> None:
        """Update a block's data."""
        ...
    
    @abstractmethod
    async def get_block(self, block_id: str) -> "PersistedBlock | None":
        """Get a specific block."""
        ...


__all__ = ["MessageService"]
