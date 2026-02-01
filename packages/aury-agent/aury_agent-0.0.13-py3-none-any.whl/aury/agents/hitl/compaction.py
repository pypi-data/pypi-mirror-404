"""Session compaction for context window management."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..llm import LLMProvider, LLMMessage


@dataclass
class CompactionConfig:
    """Compaction configuration."""
    # Protect recent tool outputs (tokens)
    prune_protect: int = 40_000
    # Minimum tokens to trigger prune
    prune_minimum: int = 20_000
    # Context limit threshold (0-1, fraction of model limit)
    context_threshold: float = 0.8
    # Reserve for output
    output_reserve: int = 32_000


class SessionCompaction:
    """Handle context compaction for long conversations.
    
    Implements two strategies:
    1. Prune: Remove old tool outputs beyond protection window
    2. Summarize: Use LLM to compress conversation history
    """
    
    def __init__(
        self,
        llm: LLMProvider,
        config: CompactionConfig | None = None,
    ):
        self._llm = llm
        self._config = config or CompactionConfig()
    
    def estimate_tokens(self, text: str | dict | list) -> int:
        """Estimate token count for content.
        
        Simple heuristic: ~4 characters per token.
        """
        import json
        
        if isinstance(text, (dict, list)):
            text = json.dumps(text, ensure_ascii=False)
        
        return len(text) // 4
    
    def estimate_messages_tokens(self, messages: list[LLMMessage]) -> int:
        """Estimate total tokens in message list."""
        total = 0
        for msg in messages:
            if isinstance(msg.content, str):
                total += self.estimate_tokens(msg.content)
            else:
                total += self.estimate_tokens(msg.content)
        return total
    
    async def is_overflow(
        self,
        messages: list[LLMMessage],
        context_limit: int,
    ) -> bool:
        """Check if context needs compaction."""
        total_tokens = self.estimate_messages_tokens(messages)
        usable = int(context_limit * self._config.context_threshold) - self._config.output_reserve
        return total_tokens > usable
    
    async def prune(
        self,
        messages: list[LLMMessage],
    ) -> tuple[list[LLMMessage], list[LLMMessage]]:
        """Prune old tool outputs.
        
        Keeps recent tool outputs within prune_protect window.
        Returns (pruned_messages, ejected_messages).
        """
        # Find tool result messages
        tool_results = []
        for i, msg in enumerate(messages):
            content = msg.content
            if isinstance(content, list):
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "tool_result":
                        tokens = self.estimate_tokens(part.get("content", ""))
                        tool_results.append((i, part, tokens))
        
        # Calculate which to prune (from oldest)
        total_tokens = 0
        to_prune = []
        
        # Process in reverse (newest first)
        for item in reversed(tool_results):
            total_tokens += item[2]
            if total_tokens > self._config.prune_protect:
                to_prune.append(item)
        
        # Check minimum threshold
        prune_tokens = sum(t[2] for t in to_prune)
        if prune_tokens < self._config.prune_minimum:
            return messages, []
        
        # Create pruned messages
        pruned = []
        ejected = []
        prune_indices = {t[0] for t in to_prune}
        
        for i, msg in enumerate(messages):
            if i in prune_indices:
                # Replace tool result content with placeholder
                if isinstance(msg.content, list):
                    new_content = []
                    for part in msg.content:
                        if isinstance(part, dict) and part.get("type") == "tool_result":
                            # Store original for ejection
                            ejected.append(LLMMessage(
                                role=msg.role,
                                content=[part],
                            ))
                            # Replace with placeholder
                            new_content.append({
                                **part,
                                "content": "[Old tool result content cleared]",
                            })
                        else:
                            new_content.append(part)
                    pruned.append(LLMMessage(role=msg.role, content=new_content))
                else:
                    pruned.append(msg)
            else:
                pruned.append(msg)
        
        return pruned, ejected
    
    async def summarize(
        self,
        messages: list[LLMMessage],
        max_summary_tokens: int = 4096,
    ) -> str:
        """Generate summary of conversation history."""
        import json
        
        # Build summary prompt
        prompt = self._build_compaction_prompt(messages)
        
        # Call LLM for summary
        summary_messages = [LLMMessage(role="user", content=prompt)]
        
        result_text = ""
        async for event in self._llm.complete(
            messages=summary_messages,
            max_tokens=max_summary_tokens,
        ):
            if event.type == "content" and event.delta:
                result_text += event.delta
        
        return result_text
    
    def _build_compaction_prompt(self, messages: list[LLMMessage]) -> str:
        """Build prompt for summarization."""
        import json
        
        # Format messages
        formatted = []
        for msg in messages:
            if isinstance(msg.content, str):
                formatted.append(f"[{msg.role}]: {msg.content}")
            else:
                formatted.append(f"[{msg.role}]: {json.dumps(msg.content, ensure_ascii=False)}")
        
        conversation = "\n\n".join(formatted)
        
        return f"""Please summarize the following conversation history, preserving:
- Key decisions and outcomes
- Important context and facts
- Tool execution results (summarized)
- User preferences and requirements

Conversation:
{conversation}

Summary:"""
    
    async def compact(
        self,
        messages: list[LLMMessage],
        context_limit: int,
    ) -> tuple[list[LLMMessage], dict[str, Any]]:
        """Full compaction: prune then summarize if needed.
        
        Returns:
            Tuple of (compacted_messages, compaction_info)
        """
        info = {
            "original_tokens": self.estimate_messages_tokens(messages),
            "pruned": False,
            "summarized": False,
            "ejected_count": 0,
        }
        
        # First try pruning
        pruned, ejected = await self.prune(messages)
        if ejected:
            info["pruned"] = True
            info["ejected_count"] = len(ejected)
            messages = pruned
        
        # Check if still over limit
        if await self.is_overflow(messages, context_limit):
            # Summarize older messages
            mid_point = len(messages) // 2
            old_messages = messages[:mid_point]
            recent_messages = messages[mid_point:]
            
            summary = await self.summarize(old_messages)
            
            # Replace old messages with summary
            summary_message = LLMMessage(
                role="system",
                content=f"[Conversation Summary]\n{summary}\n\n[End Summary]",
            )
            
            messages = [messages[0], summary_message] + recent_messages
            info["summarized"] = True
        
        info["final_tokens"] = self.estimate_messages_tokens(messages)
        
        return messages, info
