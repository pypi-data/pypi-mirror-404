"""ArtifactContextProvider - provides artifacts context and tools.

Features:
- Artifact index in system_content
- ReadArtifactTool for LLM to read artifact content
- Pluggable Loader system for different artifact types
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from .base import BaseContextProvider, AgentContext
from ..core.types.tool import BaseTool, ToolResult, ToolContext

if TYPE_CHECKING:
    from ..core.context import InvocationContext
    from ..backends.artifact import ArtifactBackend, StoredArtifact


# ============================================================
# Loader Protocol and Registry
# ============================================================

@runtime_checkable
class ArtifactLoader(Protocol):
    """Protocol for loading artifact content.
    
    Implement this to support custom artifact types.
    """
    
    async def load(self, artifact: "StoredArtifact") -> str:
        """Load artifact content.
        
        Args:
            artifact: Stored artifact with metadata and data
            
        Returns:
            String content for LLM context
        """
        ...


class DefaultLoader:
    """Default loader - returns summary or data as string."""
    
    async def load(self, artifact: "StoredArtifact") -> str:
        # Try summary first
        if artifact.summary:
            return artifact.summary
        
        # Try data
        if artifact.data:
            import json
            return json.dumps(artifact.data, ensure_ascii=False, indent=2)
        
        return "No content"


class SearchResultsLoader:
    """Loader for search_results artifacts."""
    
    async def load(self, artifact: "StoredArtifact") -> str:
        data = artifact.data or {}
        query = data.get("query", "")
        results = data.get("results", [])
        
        if not results:
            return f"Search `{query}` returned no results"
        
        lines = [f"Search: {query}", f"Total {len(results)} results:", ""]
        for i, r in enumerate(results, 1):
            lines.append(f"{i}. {r.get('title', 'Untitled')}")
            snippet = r.get('snippet', '')[:150]
            if snippet:
                lines.append(f"   {snippet}")
            url = r.get('url', '')
            if url:
                lines.append(f"   URL: {url}")
            lines.append("")
        
        return "\n".join(lines)


class FileLoader:
    """Loader for file-based artifacts (file:// URLs)."""
    
    async def load(self, artifact: "StoredArtifact") -> str:
        data = artifact.data or {}
        url = data.get("url")
        
        if not url:
            return artifact.summary or "No content"
        
        # Load from file:// URL
        if url.startswith("file://"):
            file_path = url[7:]  # Remove "file://"
            try:
                import aiofiles
                async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
                    return await f.read()
            except ImportError:
                # Fallback to sync read
                with open(file_path, "r", encoding="utf-8") as f:
                    return f.read()
            except Exception as e:
                return artifact.summary or f"Failed to read file: {file_path} ({e})"
        
        return artifact.summary or f"Unsupported URL scheme: {url}"


# Global loader registry
_LOADERS: dict[str, ArtifactLoader] = {
    "search_results": SearchResultsLoader(),
    "report": FileLoader(),
    "file": FileLoader(),
}

_DEFAULT_LOADER = DefaultLoader()


def register_loader(kind: str, loader: ArtifactLoader) -> None:
    """Register a custom loader for artifact kind.
    
    Args:
        kind: Artifact kind (e.g., "pdf", "image")
        loader: Loader instance implementing ArtifactLoader protocol
        
    Example:
        class PDFLoader:
            async def load(self, artifact):
                # Custom PDF loading logic
                return extracted_text
        
        register_loader("pdf", PDFLoader())
    """
    _LOADERS[kind] = loader


def get_loader(kind: str) -> ArtifactLoader:
    """Get loader for artifact kind.
    
    Returns registered loader or default loader if not found.
    """
    return _LOADERS.get(kind, _DEFAULT_LOADER)


# ============================================================
# ReadArtifactTool
# ============================================================

class ReadArtifactTool(BaseTool):
    """Tool for reading artifact content.
    
    Uses registered loaders to load content based on artifact kind.
    """
    
    _name = "read_artifact"
    _description = """Read the full content of an artifact.

Use this to get detailed content of artifacts like search results, reports, etc.
"""
    
    _parameters: dict[str, Any] = {
        "type": "object",
        "properties": {
            "artifact_id": {
                "type": "string",
                "description": "Artifact ID to read",
            },
        },
        "required": ["artifact_id"],
    }
    
    def __init__(self, backend: "ArtifactBackend") -> None:
        """Initialize with artifact backend.
        
        Args:
            backend: Backend for artifact storage/retrieval
        """
        self._backend = backend
    
    async def execute(self, params: dict[str, Any], ctx: ToolContext) -> ToolResult:
        artifact_id = params.get("artifact_id")
        if not artifact_id:
            return ToolResult.error("artifact_id is required")
        
        # Fetch artifact
        stored = await self._backend.get(artifact_id)
        if not stored:
            return ToolResult.error(f"Artifact not found: {artifact_id}")
        
        # Load content using appropriate loader
        loader = get_loader(stored.kind)
        try:
            content = await loader.load(stored)
        except Exception as e:
            return ToolResult.error(f"Failed to load artifact: {e}")
        
        return ToolResult.success(output=content)


# ============================================================
# ArtifactContextProvider
# ============================================================

class ArtifactContextProvider(BaseContextProvider):
    """Artifact context provider.
    
    Provides:
    - system_content: Artifact index for LLM awareness
    - tools: ReadArtifactTool for reading artifact content
    
    Example:
        provider = ArtifactContextProvider(
            backend=my_artifact_backend,
            max_summary_items=10,
        )
        
        # Register custom loader
        register_loader("pdf", MyPDFLoader())
    """
    
    _name = "artifacts"
    
    def __init__(
        self,
        backend: "ArtifactBackend",
        max_summary_items: int = 10,
        enable_tools: bool = True,
    ):
        """Initialize ArtifactContextProvider.
        
        Args:
            backend: Artifact storage backend
            max_summary_items: Max artifacts to show in summary
            enable_tools: Whether to provide ReadArtifactTool
        """
        self.backend = backend
        self.max_summary_items = max_summary_items
        self.enable_tools = enable_tools
    
    async def fetch(self, ctx: "InvocationContext") -> AgentContext:
        """Fetch artifact context.
        
        Returns:
            AgentContext with system_content (index) and ReadArtifactTool
        """
        # Get artifacts for session
        artifacts = await self.backend.list(session_id=ctx.session.id)
        
        if not artifacts:
            # No artifacts, but still provide tool if enabled
            tools: list[BaseTool] = []
            if self.enable_tools:
                tools = [ReadArtifactTool(self.backend)]
            return AgentContext(tools=tools) if tools else AgentContext.empty()
        
        # Build summary (artifact index)
        summary = self._build_summary(artifacts[:self.max_summary_items])
        
        # Build tools
        tools = []
        if self.enable_tools:
            tools = [ReadArtifactTool(self.backend)]
        
        return AgentContext(
            system_content=summary,
            tools=tools,
        )
    
    def _build_summary(self, artifacts: list[Any]) -> str:
        """Build artifact summary for LLM context."""
        lines = ["## Available Artifacts", ""]
        for a in artifacts:
            title = getattr(a, 'title', 'Untitled')
            summary = getattr(a, 'summary', None)
            artifact_id = getattr(a, 'id', 'unknown')
            kind = getattr(a, 'kind', 'unknown')
            
            line = f"- [{artifact_id}] ({kind}) {title}"
            if summary:
                line += f": {summary[:100]}"
            lines.append(line)
        
        lines.append("")
        lines.append("Use `read_artifact` tool to get full content.")
        return "\n".join(lines)


__all__ = [
    "ArtifactContextProvider",
    "ArtifactLoader",
    "ReadArtifactTool",
    "register_loader",
    "get_loader",
    "DefaultLoader",
    "SearchResultsLoader",
    "FileLoader",
]
