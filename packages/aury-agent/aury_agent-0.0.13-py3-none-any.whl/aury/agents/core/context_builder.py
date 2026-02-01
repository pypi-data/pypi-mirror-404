"""Context builder for LLM communication.

ContextBuilder constructs the full context to send to LLM, combining:
- System prompt
- Knowledge (user-defined, via Middleware)
- Summary (compressed history)
- Recalls (session key points)
- Recent messages
- Current input

Context is runtime-built, not stored.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from .types.message import Message, PromptInput
    from .types.recall import Recall, Summary
    from ..backends.state import StateBackend


@dataclass
class ContextConfig:
    """Configuration for context building."""

    # Token limits
    max_tokens: int = 8000

    # Message control
    max_recent_messages: int = 50

    # Memory control
    include_summary: bool = True
    include_recalls: bool = True
    recall_limit: int = 20

    # Knowledge control (user-defined via Middleware)
    include_knowledge: bool = True
    knowledge_limit: int = 10

    # Compression
    enable_compression: bool = True
    compression_threshold: int = 6000


@dataclass
class LLMContext:
    """Context prepared for LLM.

    This is the final object sent to LLM, not stored.
    """

    # Final messages (LLM API format)
    messages: list[dict[str, Any]] = field(default_factory=list)

    # Sources (for debugging/tracing)
    source_summary: "Summary | None" = None
    source_recalls: list["Recall"] = field(default_factory=list)
    source_knowledge: list[dict[str, Any]] = field(default_factory=list)  # User-defined structure
    source_messages: list["Message"] = field(default_factory=list)

    # Token stats
    estimated_tokens: int = 0

    def to_llm_messages(self) -> list[dict[str, Any]]:
        """Get messages in LLM API format."""
        return self.messages


class ContextBuilder(Protocol):
    """Protocol for context building.

    Users can implement custom builders for specialized context management.
    """

    async def build(
        self,
        session_id: str,
        invocation_id: str,
        current_input: "PromptInput",
        branch: str | None = None,
        config: ContextConfig | None = None,
    ) -> LLMContext:
        """Build context for LLM.

        Args:
            session_id: Current session ID
            invocation_id: Current invocation ID
            current_input: User input for this turn
            branch: SubAgent branch (for isolation)
            config: Context configuration

        Returns:
            LLMContext ready for LLM API call
        """
        ...


class DefaultContextBuilder:
    """Default implementation of context builder.

    Build order:
    1. System prompt
    2. Knowledge (injected via Middleware)
    3. Summary (compressed history)
    4. Recalls (key points)
    5. Recent messages
    6. Current input
    """

    def __init__(
        self,
        storage: "StateBackend",
        system_prompt: str | None = None,
    ):
        """Initialize context builder.

        Args:
            storage: State backend for loading messages/recalls
            system_prompt: System prompt template (can include {var} for state.vars)
        """
        self._storage = storage
        self._system_prompt = system_prompt

    async def build(
        self,
        session_id: str,
        invocation_id: str,
        current_input: "PromptInput",
        branch: str | None = None,
        config: ContextConfig | None = None,
        *,
        state_vars: dict[str, Any] | None = None,
    ) -> LLMContext:
        """Build context for LLM.

        Args:
            session_id: Current session ID
            invocation_id: Current invocation ID
            current_input: User input for this turn
            branch: SubAgent branch (for isolation)
            config: Context configuration
            state_vars: Variables for prompt formatting (from state.vars)
        """
        from .types.message import Message, MessageRole
        from .types.recall import Recall, Summary

        cfg = config or ContextConfig()
        context = LLMContext()
        messages: list[dict[str, Any]] = []

        # 1. System prompt
        if self._system_prompt:
            system_text = self._system_prompt
            if state_vars:
                try:
                    system_text = system_text.format(**state_vars)
                except KeyError:
                    pass  # Ignore missing vars
            messages.append(
                {
                    "role": "system",
                    "content": system_text,
                }
            )

        # 2. Summary (compressed history)
        if cfg.include_summary:
            summary = await self._load_summary(session_id)
            if summary:
                context.source_summary = summary
                messages.append(
                    {
                        "role": "system",
                        "content": f"[Previous Conversation Summary]\n{summary.content}",
                    }
                )

        # 3. Recalls (key points)
        if cfg.include_recalls:
            recalls = await self._load_recalls(session_id, branch, cfg.recall_limit)
            if recalls:
                context.source_recalls = recalls
                recalls_text = "\n".join([f"- {r.content}" for r in recalls])
                messages.append(
                    {
                        "role": "system",
                        "content": f"[Key Information]\n{recalls_text}",
                    }
                )

        # 4. Recent messages
        recent_messages = await self._load_messages(
            session_id,
            branch,
            cfg.max_recent_messages,
        )
        context.source_messages = recent_messages

        for msg in recent_messages:
            llm_msg = msg.to_llm_format()
            messages.append(llm_msg)

        # 5. Current input
        input_msg = current_input.to_message(session_id, invocation_id)
        messages.append(input_msg.to_llm_format())

        context.messages = messages
        context.estimated_tokens = self._estimate_tokens(messages)

        return context

    async def _load_summary(self, session_id: str) -> "Summary | None":
        """Load session summary."""
        from .types.recall import Summary

        data = await self._storage.get("summaries", session_id)
        if data:
            return Summary.from_dict(data)
        return None

    async def _load_recalls(
        self,
        session_id: str,
        branch: str | None,
        limit: int,
    ) -> list["Recall"]:
        """Load session recalls."""
        from .types.recall import Recall

        # Load all recalls for session
        keys = await self._storage.list("recalls", prefix=session_id)
        recalls: list[Recall] = []

        for key in keys[: limit * 2]:  # Load extra to filter by branch
            data = await self._storage.get("recalls", key)
            if data:
                recall = Recall.from_dict(data)
                # Filter by branch
                if branch is None or recall.branch is None or recall.branch == branch:
                    recalls.append(recall)
                    if len(recalls) >= limit:
                        break

        # Sort by importance
        recalls.sort(key=lambda r: r.importance, reverse=True)
        return recalls[:limit]

    async def _load_messages(
        self,
        session_id: str,
        branch: str | None,
        limit: int,
    ) -> list["Message"]:
        """Load recent messages."""
        from .types.message import Message

        # Load all message keys for session
        keys = await self._storage.list("messages", prefix=session_id)
        messages: list[Message] = []

        # Load in reverse (most recent first)
        for key in reversed(keys):
            if len(messages) >= limit:
                break

            data = await self._storage.get("messages", key)
            if data:
                msg = Message.from_dict(data)
                # Filter by branch
                if branch is None or msg.branch is None or msg.branch == branch:
                    messages.append(msg)

        # Reverse to chronological order
        messages.reverse()
        return messages

    def _estimate_tokens(self, messages: list[dict[str, Any]]) -> int:
        """Estimate token count (rough approximation)."""
        total_chars = 0
        for msg in messages:
            content = msg.get("content", "")
            if isinstance(content, str):
                total_chars += len(content)
            elif isinstance(content, list):
                for part in content:
                    if isinstance(part, dict):
                        text = part.get("text", "") or part.get("content", "")
                        total_chars += len(str(text))

        # Rough estimate: 4 chars per token
        return total_chars // 4


__all__ = [
    "ContextConfig",
    "LLMContext",
    "ContextBuilder",
    "DefaultContextBuilder",
]
