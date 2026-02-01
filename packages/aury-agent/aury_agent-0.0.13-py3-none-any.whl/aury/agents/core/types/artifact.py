"""Artifact data structures.

Artifacts are independent generated objects that:
- Are stored separately (ArtifactStore by developer)
- Are referenced in Messages by ID + summary
- Can be previewed, downloaded, edited by users
- Have different frontend rendering than ToolResult

Artifact can be:
- Single file (code, markdown, etc.)
- Package/directory (project with multiple files)
- Page list (PPT, PDF pages)
- Item list (search results, resource list)
- External reference (S3, URLs, etc.)

Framework only defines structure, developer implements storage.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .session import generate_id


@dataclass
class Artifact:
    """An artifact (generated content/file/data).
    
    Simple structure - framework doesn't dictate storage details.
    Developer implements ArtifactStore to handle persistence.
    
    Examples:
        # Single file
        Artifact(kind="file", title="main.py", data={"content": "...", "language": "python"})
        
        # Package/directory
        Artifact(kind="package", title="my_project", data={"root": "/path", "files": [...]})
        
        # Search results (structured list)
        Artifact(kind="search_results", data=[{"title": "...", "summary": "...", "url": "..."}])
        
        # PPT slides
        Artifact(kind="slides", data={"pages": [...], "page_count": 10})
        
        # External reference
        Artifact(kind="external", data={"ref": "s3://...", "type": "s3"})
    """
    id: str = field(default_factory=lambda: generate_id("art"))
    kind: str = "file"                   # Content type (developer-defined)
    renderer: str | None = None          # Override default renderer
    title: str | None = None
    summary: str | None = None           # For LLM context
    data: Any = None                     # Content (structure depends on kind)
    session_id: str = ""
    invocation_id: str = ""
    
    # Nesting structure (tree relationship)
    parent_artifact_id: str | None = None  # Parent artifact (for nested artifacts)
    root_artifact_id: str | None = None    # Root artifact of the tree
    
    def to_ref(self) -> "ArtifactRef":
        """Create a reference to this artifact."""
        return ArtifactRef(
            artifact_id=self.id,
            kind=self.kind,
            title=self.title,
            summary=self.summary,
        )
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "kind": self.kind,
            "renderer": self.renderer,
            "title": self.title,
            "summary": self.summary,
            "data": self.data,
            "session_id": self.session_id,
            "invocation_id": self.invocation_id,
            "parent_artifact_id": self.parent_artifact_id,
            "root_artifact_id": self.root_artifact_id,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Artifact":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            kind=data.get("kind", "file"),
            renderer=data.get("renderer"),
            title=data.get("title"),
            summary=data.get("summary"),
            data=data.get("data"),
            session_id=data.get("session_id", ""),
            invocation_id=data.get("invocation_id", ""),
            parent_artifact_id=data.get("parent_artifact_id"),
            root_artifact_id=data.get("root_artifact_id"),
        )


@dataclass
class ArtifactRef:
    """Reference to an artifact (used in Message).
    
    Contains only summary info for LLM context.
    Full content fetched from ArtifactStore when needed.
    """
    artifact_id: str
    kind: str = "file"
    title: str | None = None
    summary: str | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "artifact_id": self.artifact_id,
            "kind": self.kind,
            "title": self.title,
            "summary": self.summary,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ArtifactRef":
        """Create from dictionary."""
        return cls(
            artifact_id=data["artifact_id"],
            kind=data.get("kind", "file"),
            title=data.get("title"),
            summary=data.get("summary"),
        )


__all__ = ["Artifact", "ArtifactRef"]
