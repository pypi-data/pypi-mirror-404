"""Memory manager for unified memory operations."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
from uuid import uuid4

from ..core.event_bus import Bus, Events
from ..core.logging import memory_logger as logger
from ..core.types.session import generate_id
from .types import MemorySummary, MemoryRecall, MemoryContext
from .store import MemoryEntry, ScoredEntry, MemoryStore
from .processor import WriteFilter, WriteDecision, WriteResult, MemoryProcessor, ProcessContext, WriteContext, ReadContext


class WriteTrigger(Enum):
    """When memory is written."""
    MANUAL = "manual"
    INVOCATION_END = "invocation_end"
    COMPRESS = "compress"
    EVENT = "event"


@dataclass
class RetrievalSource:
    """Configuration for a retrieval source."""
    store_name: str
    weight: float = 1.0
    filter: dict[str, Any] | None = None
    limit: int = 10


class MemoryManager:
    """Unified memory manager.
    
    Handles:
    - Multiple memory stores
    - Write pipeline (filter, process, store)
    - Read pipeline (search, merge, post-process)
    - Auto-triggers from bus events
    """
    
    def __init__(
        self,
        stores: dict[str, MemoryStore],
        retrieval_config: list[RetrievalSource] | None = None,
        write_filters: list[WriteFilter] | None = None,
        write_processors: list[MemoryProcessor] | None = None,
        read_processors: list[Any] | None = None,
        auto_triggers: set[WriteTrigger] | None = None,
        bus: Bus | None = None,
    ):
        self.stores = stores
        self.retrieval_config = retrieval_config or [
            RetrievalSource(store_name=name, limit=10)
            for name in stores
        ]
        self.write_filters = write_filters or []
        self.write_processors = write_processors or []
        self.read_processors = read_processors or []
        self.auto_triggers = auto_triggers or {WriteTrigger.INVOCATION_END}
        self.bus = bus
        
        # Register bus handlers
        if bus:
            self._register_triggers()
    
    def _register_triggers(self) -> None:
        """Register auto-trigger handlers."""
        if WriteTrigger.INVOCATION_END in self.auto_triggers:
            self.bus.subscribe(Events.INVOCATION_END, self._on_invocation_end)
    
    async def _on_invocation_end(self, event_type: str, payload: dict[str, Any]) -> None:
        """Handle invocation end event."""
        messages = payload.get("messages", [])
        if not messages:
            return
        
        logger.info(
            "Memory auto-save on invocation end",
            extra={
                "invocation_id": payload.get("invocation_id"),
                "session_id": payload.get("session_id"),
                "message_count": len(messages),
            },
        )
        
        content = self._format_messages(messages)
        
        await self.add(
            content=content,
            session_id=payload.get("session_id"),
            invocation_id=payload.get("invocation_id"),
            metadata={"type": "conversation"},
            trigger=WriteTrigger.INVOCATION_END,
        )
    
    def _format_messages(self, messages: list[dict[str, Any]]) -> str:
        """Format messages for storage."""
        parts = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            if isinstance(content, list):
                # Handle multi-part content
                text_parts = [
                    p.get("text", "") for p in content
                    if isinstance(p, dict) and p.get("type") == "text"
                ]
                content = " ".join(text_parts)
            parts.append(f"[{role}]: {content}")
        return "\n\n".join(parts)
    
    async def add(
        self,
        content: str,
        session_id: str | None = None,
        invocation_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        trigger: WriteTrigger = WriteTrigger.MANUAL,
    ) -> str | None:
        """Add content to memory.
        
        Runs through write pipeline:
        1. Filters (can skip/transform)
        2. Processors (transform)
        3. Store in all stores
        
        Returns entry ID or None if filtered out.
        """
        logger.info(
            "Adding to memory",
            extra={
                "trigger": trigger.value,
                "session_id": session_id,
                "invocation_id": invocation_id,
                "content_length": len(content),
            },
        )
        entry = MemoryEntry(
            id=str(uuid4()),
            content=content,
            session_id=session_id,
            invocation_id=invocation_id,
            metadata={**(metadata or {}), "trigger": trigger.value},
        )
        
        entries = [entry]
        write_context = WriteContext(
            trigger=trigger,
            session_id=session_id,
            invocation_id=invocation_id,
        )
        
        # 1. Apply filters
        for filter in self.write_filters:
            logger.debug(
                "Applying memory write filter",
                extra={"filter": type(filter).__name__, "invocation_id": invocation_id},
            )
            result = await filter.filter(entries, write_context)
            
            if result.decision == WriteDecision.SKIP:
                logger.debug(
                    "Memory entry skipped by filter",
                    extra={"filter": type(filter).__name__, "invocation_id": invocation_id},
                )
                return None
            elif result.decision == WriteDecision.TRANSFORM:
                entries = result.entries or []
        
        if not entries:
            return None
        
        # 2. Apply processors
        process_context = ProcessContext(session_id=session_id)
        for processor in self.write_processors:
            entries = await processor.process(entries, process_context)
        
        # 3. Store in all stores
        for entry in entries:
            for store in self.stores.values():
                await store.add(entry)
        
        if self.bus:
            await self.bus.publish(Events.MEMORY_ADD, {
                "entry_id": entries[0].id if entries else None,
                "count": len(entries),
            })
        
        return entries[0].id if entries else None
    
    async def search(
        self,
        query: str,
        filter: dict[str, Any] | None = None,
        limit: int = 10,
    ) -> list[ScoredEntry]:
        """Search memory stores.
        
        Searches all configured sources and merges results.
        """
        logger.info(
            "Searching memory",
            extra={
                "query_length": len(query),
                "limit": limit,
                "source_count": len(self.retrieval_config),
            },
        )
        
        # 1. Search all sources
        all_results: dict[str, list[ScoredEntry]] = {}
        
        for source in self.retrieval_config:
            if source.store_name not in self.stores:
                continue
            
            store = self.stores[source.store_name]
            merged_filter = {**(filter or {}), **(source.filter or {})}
            
            results = await store.search(
                query=query,
                filter=merged_filter,
                limit=source.limit,
            )
            
            # Apply source weight
            for r in results:
                r.score *= source.weight
            
            all_results[source.store_name] = results
        
        # 2. Merge results (simple dedup by ID)
        seen_ids: set[str] = set()
        merged: list[ScoredEntry] = []
        
        # Flatten and sort by score
        flat_results = []
        for results in all_results.values():
            flat_results.extend(results)
        flat_results.sort(key=lambda x: x.score, reverse=True)
        
        for result in flat_results:
            if result.entry.id not in seen_ids:
                seen_ids.add(result.entry.id)
                merged.append(result)
        
        # 3. Apply read processors
        read_context = ReadContext(limit=limit)
        for processor in self.read_processors:
            merged = await processor.process(merged, query, read_context)
        
        if self.bus:
            await self.bus.publish(Events.MEMORY_SEARCH, {
                "query": query[:100],
                "result_count": len(merged[:limit]),
            })
        
        return merged[:limit]
    
    async def revert(
        self,
        session_id: str,
        after_invocation_id: str,
    ) -> list[str]:
        """Revert memory entries after specified invocation."""
        deleted = []
        
        for store in self.stores.values():
            ids = await store.revert(session_id, after_invocation_id)
            deleted.extend(ids)
        
        return deleted
    
    async def on_compress(
        self,
        session_id: str,
        invocation_id: str,
        ejected_messages: list[dict[str, Any]],
    ) -> str | None:
        """Handle compression - save ejected messages to memory."""
        if WriteTrigger.COMPRESS not in self.auto_triggers:
            return None
        
        content = self._format_messages(ejected_messages)
        
        return await self.add(
            content=content,
            session_id=session_id,
            invocation_id=invocation_id,
            metadata={"type": "compressed"},
            trigger=WriteTrigger.COMPRESS,
        )
    
    # ========== Summary & Recall API ==========
    
    async def get_context(
        self,
        session_id: str,
        invocation_ids: list[str] | None = None,
        recall_limit: int = 10,
    ) -> MemoryContext:
        """Get memory context for LLM.
        
        Args:
            session_id: Session to get context for
            invocation_ids: Filter recalls to these invocations (for isolation)
            recall_limit: Max number of recalls to return
            
        Returns:
            MemoryContext with summary and recalls
        """
        # Get summary
        summary = await self.get_summary(session_id)
        
        # Get recalls, filtered by invocation chain if provided
        recalls = await self.get_recalls(
            session_id=session_id,
            invocation_ids=invocation_ids,
            limit=recall_limit,
        )
        
        return MemoryContext(summary=summary, recalls=recalls)
    
    async def get_summary(self, session_id: str) -> MemorySummary | None:
        """Get session summary."""
        # Look in first store that has summaries
        for store in self.stores.values():
            if hasattr(store, 'get_summary'):
                return await store.get_summary(session_id)
        
        # Fallback: search for summary entry
        results = await self.search(
            query="conversation summary",
            filter={"session_id": session_id, "type": "summary"},
            limit=1,
        )
        
        if results:
            entry = results[0].entry
            return MemorySummary(
                session_id=session_id,
                content=entry.content,
                last_invocation_id=entry.invocation_id or "",
            )
        
        return None
    
    async def get_recalls(
        self,
        session_id: str,
        invocation_ids: list[str] | None = None,
        limit: int = 10,
    ) -> list[MemoryRecall]:
        """Get recalls for session, optionally filtered by invocations."""
        filter_dict: dict[str, Any] = {"session_id": session_id, "type": "recall"}
        if invocation_ids:
            filter_dict["invocation_id"] = invocation_ids
        
        # Search for recall entries
        results = await self.search(
            query="key points recalls",
            filter=filter_dict,
            limit=limit,
        )
        
        recalls = []
        for r in results:
            entry = r.entry
            recalls.append(MemoryRecall(
                id=entry.id,
                session_id=session_id,
                invocation_id=entry.invocation_id or "",
                content=entry.content,
                importance=entry.metadata.get("importance", 0.5),
                tags=entry.metadata.get("tags", []),
            ))
        
        return recalls
    
    async def add_recall(
        self,
        session_id: str,
        invocation_id: str,
        content: str,
        importance: float = 0.5,
        tags: list[str] | None = None,
    ) -> str:
        """Add a recall entry.
        
        Returns:
            Recall ID
        """
        recall_id = generate_id("recall")
        
        await self.add(
            content=content,
            session_id=session_id,
            invocation_id=invocation_id,
            metadata={
                "type": "recall",
                "recall_id": recall_id,
                "importance": importance,
                "tags": tags or [],
            },
            trigger=WriteTrigger.MANUAL,
        )
        
        return recall_id
    
    async def update_summary(
        self,
        session_id: str,
        content: str,
        last_invocation_id: str,
    ) -> None:
        """Update session summary."""
        # Delete old summary
        for store in self.stores.values():
            if hasattr(store, 'delete_by_filter'):
                await store.delete_by_filter({
                    "session_id": session_id,
                    "type": "summary",
                })
        
        # Add new summary
        await self.add(
            content=content,
            session_id=session_id,
            invocation_id=last_invocation_id,
            metadata={"type": "summary"},
            trigger=WriteTrigger.MANUAL,
        )
    
    async def delete_by_invocation(self, invocation_id: str) -> int:
        """Delete all memory entries for an invocation (for revert).
        
        Returns:
            Number of entries deleted
        """
        count = 0
        for store in self.stores.values():
            if hasattr(store, 'delete_by_filter'):
                deleted = await store.delete_by_filter({"invocation_id": invocation_id})
                count += deleted if isinstance(deleted, int) else 0
        return count
    
    async def on_subagent_complete(
        self,
        sub_inv_id: str,
        parent_inv_id: str,
        merge_mode: str,
    ) -> None:
        """Handle SubAgent completion - merge memory based on mode.
        
        Args:
            sub_inv_id: SubAgent's invocation ID
            parent_inv_id: Parent's invocation ID
            merge_mode: "merge", "summarize", or "discard"
        """
        if merge_mode == "merge":
            # Move all recalls from sub to parent
            sub_recalls = await self.get_recalls(
                session_id="",  # Will be filtered by invocation
                invocation_ids=[sub_inv_id],
                limit=100,
            )
            for recall in sub_recalls:
                await self.add_recall(
                    session_id=recall.session_id,
                    invocation_id=parent_inv_id,
                    content=recall.content,
                    importance=recall.importance,
                    tags=recall.tags,
                )
        
        elif merge_mode == "summarize":
            # Create a summary recall in parent
            sub_recalls = await self.get_recalls(
                session_id="",
                invocation_ids=[sub_inv_id],
                limit=100,
            )
            if sub_recalls:
                combined = "\n".join([r.content for r in sub_recalls])
                await self.add_recall(
                    session_id=sub_recalls[0].session_id,
                    invocation_id=parent_inv_id,
                    content=f"[SubAgent result] {combined[:500]}...",
                    importance=0.7,
                    tags=["subagent_result"],
                )
        
        # "discard" mode: do nothing, sub's memory stays isolated
