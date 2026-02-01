"""Artifact backend types and protocols."""
from __future__ import annotations

from typing import Any, Literal, Protocol, runtime_checkable


ArtifactSource = Literal["tool", "agent", "user", "system"]


@runtime_checkable
class ArtifactBackend(Protocol):
    """Protocol for artifact storage.
    
    Artifacts are file references produced during agent execution,
    such as generated images, documents, code files, etc.
    
    Note: This stores file metadata and path references, not binary data.
    Actual file storage is handled by the file system or object storage.
    
    Example usage:
        # Save artifact reference
        artifact_id = await backend.save(
            session_id="sess_123",
            name="report.pdf",
            path="/uploads/sess_123/report.pdf",
            source="tool",
            mime_type="application/pdf",
            invocation_id="inv_456",
        )
        
        # Get artifact metadata
        artifact = await backend.get(artifact_id)
        
        # List artifacts
        artifacts = await backend.list_by_session("sess_123")
    """
    
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
        """Save an artifact reference.
        
        Args:
            session_id: Session ID
            name: Display name / filename
            path: File path or URL (storage location)
            source: Origin of artifact (tool, agent, user, system)
            mime_type: MIME type (e.g., "image/png")
            size: File size in bytes
            invocation_id: Optional invocation ID for grouping
            namespace: Optional namespace for isolation
            metadata: Optional additional metadata
            
        Returns:
            Generated artifact ID
        """
        ...
    
    async def get(self, id: str) -> dict[str, Any] | None:
        """Get artifact by ID.
        
        Args:
            id: Artifact ID
            
        Returns:
            Artifact dict or None if not found:
            {"id": str, "name": str, "path": str, "source": str, ...}
        """
        ...
    
    async def delete(self, id: str) -> bool:
        """Delete an artifact reference.
        
        Note: This only deletes the metadata, not the actual file.
        File cleanup should be handled separately.
        
        Args:
            id: Artifact ID
            
        Returns:
            True if deleted, False if not found
        """
        ...
    
    async def delete_by_invocation(
        self,
        session_id: str,
        invocation_id: str,
        namespace: str | None = None,
    ) -> int:
        """Delete artifacts by invocation (for revert).
        
        Args:
            session_id: Session ID
            invocation_id: Invocation ID to delete
            namespace: Optional namespace filter
            
        Returns:
            Number of artifacts deleted
        """
        ...
    
    async def list_by_session(
        self,
        session_id: str,
        namespace: str | None = None,
        source: ArtifactSource | str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """List artifacts for a session.
        
        Args:
            session_id: Session ID
            namespace: Optional namespace filter
            source: Optional filter by source
            limit: Max results
            
        Returns:
            List of artifact dicts
        """
        ...


__all__ = ["ArtifactBackend", "ArtifactSource"]
