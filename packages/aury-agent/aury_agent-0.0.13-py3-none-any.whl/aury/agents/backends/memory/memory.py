"""In-memory memory backend implementation."""
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime
from typing import Any


class InMemoryMemoryBackend:
    """In-memory implementation of MemoryBackend.
    
    Uses simple keyword matching for search.
    Suitable for testing and simple use cases.
    For production, use vector database backends.
    """
    
    def __init__(self) -> None:
        self._entries: dict[str, dict[str, Any]] = {}
        # Index: session_id -> list of entry_ids
        self._session_entries: dict[str, list[str]] = {}
        # Content hash for deduplication
        self._content_hashes: dict[str, str] = {}
    
    def _make_key(self, session_id: str, namespace: str | None) -> str:
        if namespace:
            return f"{session_id}:{namespace}"
        return session_id
    
    def _content_hash(self, content: str) -> str:
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    async def add(
        self,
        session_id: str,
        content: str,
        invocation_id: str | None = None,
        namespace: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Add a memory entry with deduplication."""
        content_hash = self._content_hash(content)
        key = self._make_key(session_id, namespace)
        
        # Check for duplicate
        hash_key = f"{key}:{content_hash}"
        if hash_key in self._content_hashes:
            return self._content_hashes[hash_key]
        
        entry_id = f"mem_{uuid.uuid4().hex[:12]}"
        entry = {
            "id": entry_id,
            "session_id": session_id,
            "content": content,
            "invocation_id": invocation_id,
            "namespace": namespace,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat(),
        }
        
        self._entries[entry_id] = entry
        self._content_hashes[hash_key] = entry_id
        
        if key not in self._session_entries:
            self._session_entries[key] = []
        self._session_entries[key].append(entry_id)
        
        return entry_id
    
    async def search(
        self,
        session_id: str,
        query: str,
        namespace: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Simple keyword search."""
        key = self._make_key(session_id, namespace)
        entry_ids = self._session_entries.get(key, [])
        
        results = []
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        for entry_id in entry_ids:
            entry = self._entries.get(entry_id)
            if not entry:
                continue
            
            content_lower = entry["content"].lower()
            content_words = set(content_lower.split())
            
            # Calculate simple relevance score
            overlap = len(query_words & content_words)
            if overlap > 0:
                score = overlap / len(query_words)
            elif query_lower in content_lower:
                score = 0.5
            else:
                continue
            
            results.append({
                "id": entry["id"],
                "content": entry["content"],
                "score": score,
                "metadata": entry["metadata"],
                "invocation_id": entry.get("invocation_id"),
            })
        
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]
    
    async def get(self, id: str) -> dict[str, Any] | None:
        """Get memory by ID."""
        return self._entries.get(id)
    
    async def delete(self, id: str) -> bool:
        """Delete a memory entry."""
        if id not in self._entries:
            return False
        
        entry = self._entries.pop(id)
        session_id = entry["session_id"]
        namespace = entry.get("namespace")
        key = self._make_key(session_id, namespace)
        
        if key in self._session_entries:
            self._session_entries[key] = [
                eid for eid in self._session_entries[key] if eid != id
            ]
        
        # Remove from content hash
        content_hash = self._content_hash(entry["content"])
        hash_key = f"{key}:{content_hash}"
        self._content_hashes.pop(hash_key, None)
        
        return True
    
    async def delete_by_invocation(
        self,
        session_id: str,
        invocation_id: str,
        namespace: str | None = None,
    ) -> int:
        """Delete memories by invocation."""
        key = self._make_key(session_id, namespace)
        entry_ids = self._session_entries.get(key, [])
        
        to_delete = [
            eid for eid in entry_ids
            if self._entries.get(eid, {}).get("invocation_id") == invocation_id
        ]
        
        for eid in to_delete:
            await self.delete(eid)
        
        return len(to_delete)
    
    async def list(
        self,
        session_id: str,
        namespace: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List memories for a session."""
        key = self._make_key(session_id, namespace)
        entry_ids = self._session_entries.get(key, [])
        
        entries = [
            self._entries[eid]
            for eid in entry_ids
            if eid in self._entries
        ]
        
        entries.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return entries[:limit]


__all__ = ["InMemoryMemoryBackend"]
