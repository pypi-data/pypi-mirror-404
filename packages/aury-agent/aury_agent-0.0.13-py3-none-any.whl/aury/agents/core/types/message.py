"""Message data structure for LLM communication.

Message is the AI layer - separate from Block (UI layer).
Messages are stored independently and linked to Blocks via invocation_id.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, TYPE_CHECKING

from .session import generate_id

if TYPE_CHECKING:
    from .artifact import ArtifactRef


class MessageRole(Enum):
    """Message role."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class MessageContent:
    """Content block within a Message.
    
    Unlike Block (UI layer), MessageContent is purely for LLM communication.
    """
    type: str  # text, image, tool_use, tool_result
    
    # text
    text: str | None = None
    
    # image
    image_url: str | None = None
    image_base64: str | None = None
    image_media_type: str | None = None
    
    # tool_use
    tool_call_id: str | None = None
    tool_name: str | None = None
    tool_arguments: dict[str, Any] | None = None
    
    # tool_result
    tool_use_id: str | None = None
    tool_output: str | None = None
    is_error: bool = False
    
    def to_llm_format(self) -> dict[str, Any]:
        """Convert to LLM API format."""
        if self.type == "text":
            return {"type": "text", "text": self.text or ""}
        
        elif self.type == "image":
            if self.image_url:
                return {
                    "type": "image",
                    "source": {"type": "url", "url": self.image_url},
                }
            elif self.image_base64:
                return {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": self.image_media_type or "image/png",
                        "data": self.image_base64,
                    },
                }
        
        elif self.type == "tool_use":
            return {
                "type": "tool_use",
                "id": self.tool_call_id or "",
                "name": self.tool_name or "",
                "input": self.tool_arguments or {},
            }
        
        elif self.type == "tool_result":
            return {
                "type": "tool_result",
                "tool_use_id": self.tool_use_id or "",
                "content": self.tool_output or "",
                "is_error": self.is_error,
            }
        
        return {"type": self.type}
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        data: dict[str, Any] = {"type": self.type}
        
        if self.text is not None:
            data["text"] = self.text
        if self.image_url is not None:
            data["image_url"] = self.image_url
        if self.image_base64 is not None:
            data["image_base64"] = self.image_base64
        if self.image_media_type is not None:
            data["image_media_type"] = self.image_media_type
        if self.tool_call_id is not None:
            data["tool_call_id"] = self.tool_call_id
        if self.tool_name is not None:
            data["tool_name"] = self.tool_name
        if self.tool_arguments is not None:
            data["tool_arguments"] = self.tool_arguments
        if self.tool_use_id is not None:
            data["tool_use_id"] = self.tool_use_id
        if self.tool_output is not None:
            data["tool_output"] = self.tool_output
        if self.is_error:
            data["is_error"] = self.is_error
        
        return data
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MessageContent":
        """Create from dictionary."""
        return cls(
            type=data["type"],
            text=data.get("text"),
            image_url=data.get("image_url"),
            image_base64=data.get("image_base64"),
            image_media_type=data.get("image_media_type"),
            tool_call_id=data.get("tool_call_id"),
            tool_name=data.get("tool_name"),
            tool_arguments=data.get("tool_arguments"),
            tool_use_id=data.get("tool_use_id"),
            tool_output=data.get("tool_output"),
            is_error=data.get("is_error", False),
        )
    
    # Factory methods
    @classmethod
    def text(cls, content: str) -> "MessageContent":
        """Create text content."""
        return cls(type="text", text=content)
    
    @classmethod
    def tool_use(cls, call_id: str, name: str, arguments: dict[str, Any]) -> "MessageContent":
        """Create tool use content."""
        return cls(
            type="tool_use",
            tool_call_id=call_id,
            tool_name=name,
            tool_arguments=arguments,
        )
    
    @classmethod
    def tool_result(cls, tool_use_id: str, output: str, is_error: bool = False) -> "MessageContent":
        """Create tool result content."""
        return cls(
            type="tool_result",
            tool_use_id=tool_use_id,
            tool_output=output,
            is_error=is_error,
        )


@dataclass
class Message:
    """A message in the conversation (AI layer).
    
    Message is separate from Block:
    - Message: AI communication layer (stored for LLM context)
    - Block: UI display layer (stored for frontend rendering)
    
    They are linked via invocation_id for revert operations.
    """
    id: str = field(default_factory=lambda: generate_id("msg"))
    role: MessageRole = MessageRole.USER
    
    # Content (multiple formats supported)
    content: list[MessageContent] = field(default_factory=list)
    
    # Artifact references (full content in ArtifactStore)
    artifact_refs: list["ArtifactRef"] = field(default_factory=list)
    
    # Session context
    session_id: str = ""
    invocation_id: str = ""
    
    # Branch for sub-agent isolation
    branch: str | None = None
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    
    # Extension
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @property
    def text_content(self) -> str:
        """Get combined text content."""
        parts = []
        for c in self.content:
            if c.type == "text" and c.text:
                parts.append(c.text)
        return "".join(parts)
    
    @property
    def tool_calls(self) -> list[MessageContent]:
        """Get all tool_use content."""
        return [c for c in self.content if c.type == "tool_use"]
    
    @property
    def tool_results(self) -> list[MessageContent]:
        """Get all tool_result content."""
        return [c for c in self.content if c.type == "tool_result"]
    
    def to_llm_format(self) -> dict[str, Any]:
        """Convert to LLM API format (Anthropic-style).
        
        Returns a message dict suitable for LLM API calls.
        Artifact references are converted to text descriptions.
        """
        content_parts: list[dict[str, Any]] = []
        
        # Add regular content
        for c in self.content:
            llm_part = c.to_llm_format()
            if llm_part:
                content_parts.append(llm_part)
        
        # Add artifact references as context
        if self.artifact_refs:
            refs_text = "\n\n[Available Artifacts]\n"
            for ref in self.artifact_refs:
                refs_text += f"- [artifact:{ref.artifact_id}] {ref.title or 'Untitled'}: {ref.summary or 'No summary'}\n"
            content_parts.append({"type": "text", "text": refs_text})
        
        # Simplify if single text content
        if len(content_parts) == 1 and content_parts[0].get("type") == "text":
            return {
                "role": self.role.value,
                "content": content_parts[0]["text"],
            }
        
        return {
            "role": self.role.value,
            "content": content_parts,
        }
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "role": self.role.value,
            "content": [c.to_dict() for c in self.content],
            "artifact_refs": [r.to_dict() for r in self.artifact_refs] if self.artifact_refs else [],
            "session_id": self.session_id,
            "invocation_id": self.invocation_id,
            "branch": self.branch,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Message":
        """Create from dictionary."""
        from .artifact import ArtifactRef
        
        return cls(
            id=data["id"],
            role=MessageRole(data["role"]),
            content=[MessageContent.from_dict(c) for c in data.get("content", [])],
            artifact_refs=[ArtifactRef.from_dict(r) for r in data.get("artifact_refs", [])],
            session_id=data.get("session_id", ""),
            invocation_id=data.get("invocation_id", ""),
            branch=data.get("branch"),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            metadata=data.get("metadata", {}),
        )
    
    # Factory methods
    @classmethod
    def user(cls, text: str, session_id: str = "", invocation_id: str = "") -> "Message":
        """Create a user message."""
        return cls(
            role=MessageRole.USER,
            content=[MessageContent.text(text)],
            session_id=session_id,
            invocation_id=invocation_id,
        )
    
    @classmethod
    def assistant(cls, text: str, session_id: str = "", invocation_id: str = "") -> "Message":
        """Create an assistant message."""
        return cls(
            role=MessageRole.ASSISTANT,
            content=[MessageContent.text(text)],
            session_id=session_id,
            invocation_id=invocation_id,
        )
    
    @classmethod
    def system(cls, text: str) -> "Message":
        """Create a system message."""
        return cls(
            role=MessageRole.SYSTEM,
            content=[MessageContent.text(text)],
        )


@dataclass
class PromptInput:
    """User input for agent invocation.
    
    Attributes:
        text: User message text
        runtime_tools: Tools to add for this run only
        vars: Runtime variables (accessible by Managers via ctx.input.vars)
        attachments: Image/file attachments
        metadata: Additional metadata
    """
    text: str
    runtime_tools: list[Any] = field(default_factory=list)  # list[BaseTool]
    vars: dict[str, Any] = field(default_factory=dict)
    attachments: list[dict[str, Any]] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_message(self, session_id: str = "", invocation_id: str = "") -> Message:
        """Convert to a Message."""
        content = [MessageContent.text(self.text)]
        
        # Handle attachments (images, etc.)
        if self.attachments:
            for att in self.attachments:
                if att.get("type") == "image":
                    if "url" in att:
                        content.append(MessageContent(
                            type="image",
                            image_url=att["url"],
                        ))
                    elif "base64" in att:
                        content.append(MessageContent(
                            type="image",
                            image_base64=att["base64"],
                            image_media_type=att.get("media_type", "image/png"),
                        ))
        
        return Message(
            role=MessageRole.USER,
            content=content,
            session_id=session_id,
            invocation_id=invocation_id,
            metadata=self.metadata,
        )
