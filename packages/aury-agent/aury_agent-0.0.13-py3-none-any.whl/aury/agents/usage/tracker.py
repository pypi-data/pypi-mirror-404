"""Usage tracking for LLM and other services."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field, asdict
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any

from ..core.event_bus import EventBus, Events

# Alias for backward compatibility
Bus = EventBus


class UsageType(Enum):
    """Types of usage to track."""
    LLM_INPUT = "llm_input"
    LLM_OUTPUT = "llm_output"
    LLM_CACHE_READ = "llm_cache_read"
    LLM_CACHE_WRITE = "llm_cache_write"
    EMBEDDING = "embedding"
    IMAGE_GEN = "image_gen"
    SPEECH = "speech"
    SEARCH = "search"
    EXTERNAL_API = "external_api"


@dataclass
class UsageEntry:
    """A single usage record."""
    id: str
    type: UsageType
    provider: str
    model: str | None = None
    units: int = 0
    unit_type: str = "tokens"  # tokens, requests, characters, etc.
    cost: Decimal | None = None
    
    # Context
    session_id: str | None = None
    invocation_id: str | None = None
    tool_id: str | None = None
    step: int | None = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type.value,
            "provider": self.provider,
            "model": self.model,
            "units": self.units,
            "unit_type": self.unit_type,
            "cost": float(self.cost) if self.cost else None,
            "session_id": self.session_id,
            "invocation_id": self.invocation_id,
            "tool_id": self.tool_id,
            "step": self.step,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }


class UsageTracker:
    """Track usage of LLM and other services.
    
    Provides methods for recording usage, computing costs,
    and generating summaries.
    """
    
    def __init__(self, bus: Bus | None = None):
        self.bus = bus
        self._entries: list[UsageEntry] = []
        self._lock = asyncio.Lock()
        self._counter = 0
    
    def _generate_id(self) -> str:
        self._counter += 1
        return f"usage_{self._counter:06d}"
    
    async def record(self, entry: UsageEntry) -> None:
        """Record a usage entry."""
        async with self._lock:
            self._entries.append(entry)
        
        if self.bus:
            await self.bus.publish(Events.USAGE_RECORDED, entry.to_dict())
    
    async def record_llm(
        self,
        provider: str,
        model: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        cache_read_tokens: int = 0,
        cache_write_tokens: int = 0,
        session_id: str | None = None,
        invocation_id: str | None = None,
        step: int | None = None,
        **metadata: Any,
    ) -> None:
        """Convenience method for recording LLM usage."""
        base = {
            "provider": provider,
            "model": model,
            "unit_type": "tokens",
            "session_id": session_id,
            "invocation_id": invocation_id,
            "step": step,
            "metadata": metadata,
        }
        
        if input_tokens > 0:
            await self.record(UsageEntry(
                id=self._generate_id(),
                type=UsageType.LLM_INPUT,
                units=input_tokens,
                **base,
            ))
        
        if output_tokens > 0:
            await self.record(UsageEntry(
                id=self._generate_id(),
                type=UsageType.LLM_OUTPUT,
                units=output_tokens,
                **base,
            ))
        
        if cache_read_tokens > 0:
            await self.record(UsageEntry(
                id=self._generate_id(),
                type=UsageType.LLM_CACHE_READ,
                units=cache_read_tokens,
                **base,
            ))
        
        if cache_write_tokens > 0:
            await self.record(UsageEntry(
                id=self._generate_id(),
                type=UsageType.LLM_CACHE_WRITE,
                units=cache_write_tokens,
                **base,
            ))
    
    async def record_embedding(
        self,
        provider: str,
        model: str,
        tokens: int,
        session_id: str | None = None,
        **metadata: Any,
    ) -> None:
        """Record embedding usage."""
        await self.record(UsageEntry(
            id=self._generate_id(),
            type=UsageType.EMBEDDING,
            provider=provider,
            model=model,
            units=tokens,
            unit_type="tokens",
            session_id=session_id,
            metadata=metadata,
        ))
    
    def summarize(
        self,
        session_id: str | None = None,
        invocation_id: str | None = None,
    ) -> dict[str, Any]:
        """Generate usage summary."""
        entries = self._entries
        
        if session_id:
            entries = [e for e in entries if e.session_id == session_id]
        if invocation_id:
            entries = [e for e in entries if e.invocation_id == invocation_id]
        
        by_type: dict[str, int] = {}
        by_provider: dict[str, int] = {}
        by_model: dict[str, int] = {}
        total_cost = Decimal(0)
        
        for e in entries:
            by_type[e.type.value] = by_type.get(e.type.value, 0) + e.units
            by_provider[e.provider] = by_provider.get(e.provider, 0) + e.units
            if e.model:
                by_model[e.model] = by_model.get(e.model, 0) + e.units
            if e.cost:
                total_cost += e.cost
        
        return {
            "total_cost": float(total_cost),
            "by_type": by_type,
            "by_provider": by_provider,
            "by_model": by_model,
            "entry_count": len(entries),
            "total_tokens": sum(by_type.values()),
        }
    
    def get_entries(
        self,
        session_id: str | None = None,
        invocation_id: str | None = None,
        type_filter: UsageType | None = None,
    ) -> list[UsageEntry]:
        """Get filtered usage entries."""
        entries = self._entries
        
        if session_id:
            entries = [e for e in entries if e.session_id == session_id]
        if invocation_id:
            entries = [e for e in entries if e.invocation_id == invocation_id]
        if type_filter:
            entries = [e for e in entries if e.type == type_filter]
        
        return entries
    
    def clear(self, session_id: str | None = None) -> int:
        """Clear usage entries.
        
        Returns:
            Number of entries cleared
        """
        if session_id:
            original = len(self._entries)
            self._entries = [e for e in self._entries if e.session_id != session_id]
            return original - len(self._entries)
        
        count = len(self._entries)
        self._entries.clear()
        return count
