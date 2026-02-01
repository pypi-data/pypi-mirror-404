"""In-memory artifact backend implementation."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from .types import ArtifactSource


class InMemoryArtifactBackend:
    """In-memory implementation of ArtifactBackend.
    
    Stores artifact metadata in memory.
    Suitable for testing and simple use cases.
    """
    
    def __init__(self) -> None:
        self._artifacts: dict[str, dict[str, Any]] = {}
        self._session_artifacts: dict[str, list[str]] = {}
    
    def _make_key(self, session_id: str, namespace: str | None) -> str:
        if namespace:
            return f"{session_id}:{namespace}"
        return session_id
    
    async def save(
        self,
        session_id: str,
        name: str,
        path: str,
        source: ArtifactSource | str | None = None,
        mime_type: str | None = None,
        size: int | None = None,
        invocation_id: str | None = None,
        namespace: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Save an artifact reference."""
        artifact_id = f"art_{uuid.uuid4().hex[:12]}"
        key = self._make_key(session_id, namespace)
        
        artifact = {
            "id": artifact_id,
            "session_id": session_id,
            "name": name,
            "path": path,
            "source": source,
            "mime_type": mime_type,
            "size": size,
            "invocation_id": invocation_id,
            "namespace": namespace,
            "metadata": metadata or {},
            "created_at": datetime.now().isoformat(),
        }
        
        self._artifacts[artifact_id] = artifact
        
        if key not in self._session_artifacts:
            self._session_artifacts[key] = []
        self._session_artifacts[key].append(artifact_id)
        
        return artifact_id
    
    async def get(self, id: str) -> dict[str, Any] | None:
        """Get artifact by ID."""
        return self._artifacts.get(id)
    
    async def delete(self, id: str) -> bool:
        """Delete an artifact reference."""
        if id not in self._artifacts:
            return False
        
        artifact = self._artifacts.pop(id)
        session_id = artifact["session_id"]
        namespace = artifact.get("namespace")
        key = self._make_key(session_id, namespace)
        
        if key in self._session_artifacts:
            self._session_artifacts[key] = [
                aid for aid in self._session_artifacts[key] if aid != id
            ]
        
        return True
    
    async def delete_by_invocation(
        self,
        session_id: str,
        invocation_id: str,
        namespace: str | None = None,
    ) -> int:
        """Delete artifacts by invocation."""
        key = self._make_key(session_id, namespace)
        artifact_ids = self._session_artifacts.get(key, [])
        
        to_delete = [
            aid for aid in artifact_ids
            if self._artifacts.get(aid, {}).get("invocation_id") == invocation_id
        ]
        
        for aid in to_delete:
            await self.delete(aid)
        
        return len(to_delete)
    
    async def list_by_session(
        self,
        session_id: str,
        namespace: str | None = None,
        source: ArtifactSource | str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List artifacts for a session."""
        key = self._make_key(session_id, namespace)
        artifact_ids = self._session_artifacts.get(key, [])
        
        results = []
        for aid in artifact_ids:
            artifact = self._artifacts.get(aid)
            if artifact:
                # Filter by source if specified
                if source and artifact.get("source") != source:
                    continue
                results.append(artifact)
        
        results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return results[:limit]


__all__ = ["InMemoryArtifactBackend"]
