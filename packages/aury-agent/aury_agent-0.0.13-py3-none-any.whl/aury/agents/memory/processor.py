"""Memory processors for filtering and transformation."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Protocol

from .store import MemoryEntry, ScoredEntry


class WriteDecision(Enum):
    """Decision from write filter."""
    SKIP = "skip"
    PASS = "pass"
    TRANSFORM = "transform"


@dataclass
class WriteResult:
    """Result from write filter."""
    decision: WriteDecision
    entries: list[MemoryEntry] | None = None
    reason: str | None = None


@dataclass
class WriteContext:
    """Context for write operations."""
    trigger: Any  # WriteTrigger
    session_id: str | None = None
    invocation_id: str | None = None


@dataclass
class ProcessContext:
    """Context for processing operations."""
    session_id: str | None = None


@dataclass
class ReadContext:
    """Context for read operations."""
    session_id: str | None = None
    limit: int = 10


class WriteFilter(Protocol):
    """Write filter protocol."""
    
    async def filter(
        self,
        entries: list[MemoryEntry],
        context: WriteContext,
    ) -> WriteResult:
        """Filter entries before writing.
        
        Returns WriteResult with decision.
        """
        ...


class MemoryProcessor(Protocol):
    """Memory processor protocol."""
    
    async def process(
        self,
        entries: list[MemoryEntry],
        context: ProcessContext,
    ) -> list[MemoryEntry]:
        """Process entries, return transformed list."""
        ...


class ReadPostProcessor(Protocol):
    """Read post-processor protocol."""
    
    async def process(
        self,
        results: list[ScoredEntry],
        query: str,
        context: ReadContext,
    ) -> list[ScoredEntry]:
        """Post-process search results."""
        ...


class DeduplicationFilter:
    """Filter duplicate content."""
    
    def __init__(
        self,
        store: Any,  # MemoryStore
        similarity_threshold: float = 0.9,
    ):
        self.store = store
        self.similarity_threshold = similarity_threshold
    
    async def filter(
        self,
        entries: list[MemoryEntry],
        context: WriteContext,
    ) -> WriteResult:
        """Check for duplicate content."""
        for entry in entries:
            # Search for similar content
            results = await self.store.search(
                query=entry.content,
                filter={"session_id": entry.session_id} if entry.session_id else None,
                limit=1,
            )
            
            if results and results[0].score > self.similarity_threshold:
                return WriteResult(
                    decision=WriteDecision.SKIP,
                    reason=f"Duplicate found: {results[0].entry.id}",
                )
        
        return WriteResult(decision=WriteDecision.PASS)


class LengthFilter:
    """Filter entries by content length."""
    
    def __init__(self, min_length: int = 10, max_length: int = 10000):
        self.min_length = min_length
        self.max_length = max_length
    
    async def filter(
        self,
        entries: list[MemoryEntry],
        context: WriteContext,
    ) -> WriteResult:
        """Filter by content length."""
        for entry in entries:
            if len(entry.content) < self.min_length:
                return WriteResult(
                    decision=WriteDecision.SKIP,
                    reason=f"Content too short: {len(entry.content)} < {self.min_length}",
                )
            if len(entry.content) > self.max_length:
                return WriteResult(
                    decision=WriteDecision.SKIP,
                    reason=f"Content too long: {len(entry.content)} > {self.max_length}",
                )
        
        return WriteResult(decision=WriteDecision.PASS)


class TruncationProcessor:
    """Truncate long content."""
    
    def __init__(self, max_length: int = 5000):
        self.max_length = max_length
    
    async def process(
        self,
        entries: list[MemoryEntry],
        context: ProcessContext,
    ) -> list[MemoryEntry]:
        """Truncate content if too long."""
        result = []
        
        for entry in entries:
            if len(entry.content) > self.max_length:
                truncated = MemoryEntry(
                    id=entry.id,
                    content=entry.content[:self.max_length] + "... (truncated)",
                    session_id=entry.session_id,
                    invocation_id=entry.invocation_id,
                    created_at=entry.created_at,
                    metadata={**entry.metadata, "truncated": True},
                )
                result.append(truncated)
            else:
                result.append(entry)
        
        return result
