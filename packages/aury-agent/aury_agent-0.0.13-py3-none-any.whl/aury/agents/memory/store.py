"""Memory store protocol and implementations."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol, runtime_checkable


@dataclass
class MemoryEntry:
    """A memory entry."""
    id: str
    content: str
    session_id: str | None = None
    invocation_id: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "content": self.content,
            "session_id": self.session_id,
            "invocation_id": self.invocation_id,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MemoryEntry:
        return cls(
            id=data["id"],
            content=data["content"],
            session_id=data.get("session_id"),
            invocation_id=data.get("invocation_id"),
            created_at=datetime.fromisoformat(data["created_at"])
            if "created_at" in data else datetime.now(),
            metadata=data.get("metadata", {}),
        )
    
    @property
    def content_hash(self) -> str:
        """Get hash of content for deduplication."""
        return hashlib.sha256(self.content.encode()).hexdigest()[:16]


@dataclass
class ScoredEntry:
    """Memory entry with relevance score."""
    entry: MemoryEntry
    score: float
    source: str = "default"


@runtime_checkable
class MemoryStore(Protocol):
    """Memory store protocol."""
    
    async def add(self, entry: MemoryEntry) -> str:
        """Add entry, return ID."""
        ...
    
    async def search(
        self,
        query: str,
        filter: dict[str, Any] | None = None,
        limit: int = 10,
    ) -> list[ScoredEntry]:
        """Search for relevant entries."""
        ...
    
    async def get(self, entry_id: str) -> MemoryEntry | None:
        """Get entry by ID."""
        ...
    
    async def remove(self, entry_id: str) -> None:
        """Remove entry."""
        ...
    
    async def revert(
        self,
        session_id: str,
        after_invocation_id: str,
    ) -> list[str]:
        """Remove entries after specified invocation.
        
        Returns list of deleted IDs.
        """
        ...


class InMemoryStore:
    """Simple in-memory store for testing."""
    
    def __init__(self) -> None:
        self._entries: dict[str, MemoryEntry] = {}
        self._content_hashes: dict[str, str] = {}  # hash -> entry_id
    
    async def add(self, entry: MemoryEntry) -> str:
        """Add entry with deduplication."""
        content_hash = entry.content_hash
        
        # Check for duplicate
        if content_hash in self._content_hashes:
            return self._content_hashes[content_hash]
        
        self._entries[entry.id] = entry
        self._content_hashes[content_hash] = entry.id
        return entry.id
    
    async def search(
        self,
        query: str,
        filter: dict[str, Any] | None = None,
        limit: int = 10,
    ) -> list[ScoredEntry]:
        """Simple keyword search."""
        filter = filter or {}
        results = []
        
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        for entry in self._entries.values():
            # Apply filters
            if filter:
                skip = False
                for key, value in filter.items():
                    entry_value = getattr(entry, key, None) or entry.metadata.get(key)
                    if entry_value != value:
                        skip = True
                        break
                if skip:
                    continue
            
            # Calculate simple relevance score
            content_lower = entry.content.lower()
            content_words = set(content_lower.split())
            
            # Word overlap score
            overlap = len(query_words & content_words)
            if overlap > 0:
                score = overlap / len(query_words)
                results.append(ScoredEntry(entry=entry, score=score, source="memory"))
            elif query_lower in content_lower:
                # Substring match
                results.append(ScoredEntry(entry=entry, score=0.5, source="memory"))
        
        # Sort by score and limit
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]
    
    async def get(self, entry_id: str) -> MemoryEntry | None:
        return self._entries.get(entry_id)
    
    async def remove(self, entry_id: str) -> None:
        if entry_id in self._entries:
            entry = self._entries[entry_id]
            content_hash = entry.content_hash
            self._content_hashes.pop(content_hash, None)
            del self._entries[entry_id]
    
    async def revert(
        self,
        session_id: str,
        after_invocation_id: str,
    ) -> list[str]:
        """Remove entries for invocations after specified one."""
        # Simple implementation: compare invocation IDs lexicographically
        # In production, use timestamps or sequence numbers
        to_delete = []
        
        for entry_id, entry in self._entries.items():
            if entry.session_id == session_id:
                if entry.invocation_id and entry.invocation_id > after_invocation_id:
                    to_delete.append(entry_id)
        
        for entry_id in to_delete:
            await self.remove(entry_id)
        
        return to_delete
    
    def clear(self) -> None:
        """Clear all entries."""
        self._entries.clear()
        self._content_hashes.clear()
