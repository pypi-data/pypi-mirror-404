"""Memory compaction manager.

Handles automatic compaction of conversation history when token count
exceeds threshold. Ejected messages are summarized and stored in memory.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol, Callable
from abc import abstractmethod

from ..core.logging import memory_logger as logger

if TYPE_CHECKING:
    from .manager import MemoryManager


class TokenCounter(Protocol):
    """Protocol for counting tokens in content."""
    
    @abstractmethod
    def count(self, content: str) -> int:
        """Count tokens in content."""
        ...
    
    @abstractmethod
    def count_messages(self, messages: list[dict[str, Any]]) -> int:
        """Count tokens in messages."""
        ...


class SimpleTokenCounter:
    """Simple word-based token estimator.
    
    Approximates 1 token ≈ 4 characters for English text.
    Good enough for threshold checking, not for billing.
    """
    
    def __init__(self, chars_per_token: float = 4.0):
        self.chars_per_token = chars_per_token
    
    def count(self, content: str) -> int:
        return int(len(content) / self.chars_per_token)
    
    def count_messages(self, messages: list[dict[str, Any]]) -> int:
        total = 0
        for msg in messages:
            # Base overhead for role, etc
            total += 4
            
            content = msg.get("content", "")
            if isinstance(content, str):
                total += self.count(content)
            elif isinstance(content, list):
                # Multi-part content
                for part in content:
                    if isinstance(part, dict):
                        if part.get("type") == "text":
                            total += self.count(part.get("text", ""))
                        elif part.get("type") == "image_url":
                            total += 85  # Rough estimate for image token
        return total


class Summarizer(Protocol):
    """Protocol for summarizing content."""
    
    @abstractmethod
    async def summarize(
        self,
        messages: list[dict[str, Any]],
        existing_summary: str | None = None,
    ) -> str:
        """Summarize messages, optionally incorporating existing summary."""
        ...


class SimpleSummarizer:
    """Simple extractive summarizer.
    
    Extracts key information without LLM call.
    For production, replace with LLM-based summarizer.
    """
    
    def __init__(self, max_length: int = 500):
        self.max_length = max_length
    
    async def summarize(
        self,
        messages: list[dict[str, Any]],
        existing_summary: str | None = None,
    ) -> str:
        parts = []
        
        # Include existing summary
        if existing_summary:
            parts.append(f"Previous: {existing_summary}")
        
        # Extract key points from messages
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            
            if isinstance(content, list):
                # Extract text parts
                text_parts = [
                    p.get("text", "")
                    for p in content
                    if isinstance(p, dict) and p.get("type") == "text"
                ]
                content = " ".join(text_parts)
            
            # Skip empty content
            if not content.strip():
                continue
            
            # Truncate long content
            if len(content) > 200:
                content = content[:200] + "..."
            
            parts.append(f"{role}: {content}")
        
        result = "\n".join(parts)
        
        # Final truncation
        if len(result) > self.max_length:
            result = result[:self.max_length] + "..."
        
        return result


@dataclass
class CompactionConfig:
    """Configuration for compaction behavior."""
    
    # Token thresholds
    token_threshold: int = 8000  # Start compaction when exceeded
    target_tokens: int = 4000  # Target after compaction
    
    # Message handling
    keep_system: bool = True  # Always keep system messages
    keep_recent: int = 4  # Always keep N most recent messages
    
    # Summary behavior
    update_summary: bool = True  # Update session summary
    store_ejected: bool = True  # Store ejected messages in memory
    
    # Extra configuration
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CompactionResult:
    """Result of a compaction operation."""
    
    compacted: bool  # Whether compaction occurred
    messages_before: int
    messages_after: int
    tokens_before: int
    tokens_after: int
    ejected_count: int
    summary: str | None = None
    error: str | None = None
    
    @classmethod
    def no_action(cls, messages: int, tokens: int) -> "CompactionResult":
        """Create result for no compaction needed."""
        return cls(
            compacted=False,
            messages_before=messages,
            messages_after=messages,
            tokens_before=tokens,
            tokens_after=tokens,
            ejected_count=0,
        )
    
    @classmethod
    def with_error(cls, error: str, messages: int, tokens: int) -> "CompactionResult":
        """Create result for error case."""
        return cls(
            compacted=False,
            messages_before=messages,
            messages_after=messages,
            tokens_before=tokens,
            tokens_after=tokens,
            ejected_count=0,
            error=error,
        )


class CompactionManager:
    """Manages compaction of conversation history.
    
    When token count exceeds threshold:
    1. Identifies messages to eject (keeping system + recent)
    2. Summarizes ejected messages
    3. Stores ejected content in memory
    4. Returns compacted message list with summary injected
    
    Usage:
        compaction = CompactionManager(
            config=CompactionConfig(token_threshold=8000),
            memory_manager=memory,
        )
        
        # Check and compact if needed
        result, messages = await compaction.check_and_compact(
            messages=messages,
            session_id=session_id,
            invocation_id=invocation_id,
        )
        
        if result.compacted:
            print(f"Compacted {result.ejected_count} messages")
    """
    
    def __init__(
        self,
        config: CompactionConfig | None = None,
        memory_manager: MemoryManager | None = None,
        token_counter: TokenCounter | None = None,
        summarizer: Summarizer | None = None,
    ):
        self.config = config or CompactionConfig()
        self.memory = memory_manager
        self.token_counter = token_counter or SimpleTokenCounter()
        self.summarizer = summarizer or SimpleSummarizer()
    
    async def check_and_compact(
        self,
        messages: list[dict[str, Any]],
        session_id: str | None = None,
        invocation_id: str | None = None,
    ) -> tuple[CompactionResult, list[dict[str, Any]]]:
        """Check if compaction needed and perform if so.
        
        Args:
            messages: Current message list
            session_id: Session ID for memory storage
            invocation_id: Invocation ID for tracking
            
        Returns:
            Tuple of (result, possibly_compacted_messages)
        """
        tokens_before = self.token_counter.count_messages(messages)
        messages_before = len(messages)
        
        # Check threshold
        if tokens_before <= self.config.token_threshold:
            return CompactionResult.no_action(messages_before, tokens_before), messages
        
        logger.info(
            f"Compaction triggered: {tokens_before} tokens > {self.config.token_threshold}"
        )
        
        try:
            # Perform compaction
            compacted, ejected, summary = await self._compact(
                messages,
                session_id,
                invocation_id,
            )
            
            tokens_after = self.token_counter.count_messages(compacted)
            
            result = CompactionResult(
                compacted=True,
                messages_before=messages_before,
                messages_after=len(compacted),
                tokens_before=tokens_before,
                tokens_after=tokens_after,
                ejected_count=len(ejected),
                summary=summary,
            )
            
            return result, compacted
            
        except Exception as e:
            logger.error(f"Compaction failed: {e}")
            return CompactionResult.with_error(str(e), messages_before, tokens_before), messages
    
    async def _compact(
        self,
        messages: list[dict[str, Any]],
        session_id: str | None,
        invocation_id: str | None,
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], str | None]:
        """Perform compaction.
        
        Returns:
            Tuple of (compacted_messages, ejected_messages, summary)
        """
        # Separate system messages
        system_msgs = []
        non_system_msgs = []
        
        for msg in messages:
            if msg.get("role") == "system" and self.config.keep_system:
                system_msgs.append(msg)
            else:
                non_system_msgs.append(msg)
        
        # Determine what to keep vs eject
        keep_recent = self.config.keep_recent
        
        if len(non_system_msgs) <= keep_recent:
            # Nothing to eject
            return messages, [], None
        
        # Calculate how many to eject to reach target
        target_eject = 0
        cumulative_tokens = self.token_counter.count_messages(system_msgs)
        
        # Start from most recent and work backwards to find cut point
        kept_msgs = []
        to_eject = []
        
        # We need to keep at least keep_recent messages
        for i, msg in enumerate(reversed(non_system_msgs)):
            msg_tokens = self.token_counter.count_messages([msg])
            
            if i < keep_recent:
                # Always keep recent messages
                kept_msgs.insert(0, msg)
                cumulative_tokens += msg_tokens
            elif cumulative_tokens + msg_tokens > self.config.target_tokens:
                # Eject this message
                to_eject.insert(0, msg)
            else:
                # Can still fit, keep it
                kept_msgs.insert(0, msg)
                cumulative_tokens += msg_tokens
        
        if not to_eject:
            return messages, [], None
        
        # Get existing summary for incremental update
        existing_summary = None
        if self.memory and self.config.update_summary:
            summary_obj = await self.memory.get_summary(session_id) if session_id else None
            existing_summary = summary_obj.content if summary_obj else None
        
        # Summarize ejected messages
        summary = await self.summarizer.summarize(to_eject, existing_summary)
        
        # Store ejected messages in memory
        if self.memory and self.config.store_ejected and session_id:
            await self.memory.on_compress(
                session_id=session_id,
                invocation_id=invocation_id or "",
                ejected_messages=to_eject,
            )
            
            # Update session summary
            if self.config.update_summary:
                await self.memory.update_summary(
                    session_id=session_id,
                    content=summary,
                    last_invocation_id=invocation_id or "",
                )
        
        # Build compacted messages
        # Inject summary as a system message
        compacted = list(system_msgs)
        
        if summary:
            compacted.append({
                "role": "system",
                "content": f"[Conversation history summary]\n{summary}",
            })
        
        compacted.extend(kept_msgs)
        
        return compacted, to_eject, summary
    
    def should_compact(self, messages: list[dict[str, Any]]) -> bool:
        """Quick check if compaction might be needed."""
        tokens = self.token_counter.count_messages(messages)
        return tokens > self.config.token_threshold
    
    def estimate_tokens(self, messages: list[dict[str, Any]]) -> int:
        """Estimate token count for messages."""
        return self.token_counter.count_messages(messages)


__all__ = [
    "TokenCounter",
    "SimpleTokenCounter",
    "Summarizer",
    "SimpleSummarizer",
    "CompactionConfig",
    "CompactionResult",
    "CompactionManager",
]
