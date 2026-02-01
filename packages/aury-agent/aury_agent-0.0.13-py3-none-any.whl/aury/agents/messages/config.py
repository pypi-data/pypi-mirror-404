"""Message storage configuration.

Configures how messages are stored and retrieved.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


@dataclass
class MessageConfig:
    """Configuration for message storage.
    
    Controls raw message storage and recall behavior.
    
    Attributes:
        enable_raw_store: Whether to store complete messages in RawMessageStore.
                         Required for HITL recovery and full-context recall.
        persist_raw: Whether to keep raw messages after invocation completes.
                    False = clean up after invocation (default, saves space)
                    True = keep forever (for audit/recall)
        recall_mode: How to build context for LLM recall.
                    "mixed" = previous invocations truncated + current invocation raw
                    "raw" = all raw messages (requires persist_raw=True or current inv only)
    
    Example:
        # Default: raw for recovery, clean up after
        config = MessageConfig()
        
        # Keep all raw messages for full recall
        config = MessageConfig(persist_raw=True, recall_mode="raw")
        
        # Disable raw storage (no HITL recovery)
        config = MessageConfig(enable_raw_store=False)
    """
    enable_raw_store: bool = True
    persist_raw: bool = False
    recall_mode: Literal["mixed", "raw"] = "mixed"
    
    def __post_init__(self):
        # Validate: raw recall mode requires raw storage
        if self.recall_mode == "raw" and not self.enable_raw_store:
            raise ValueError("recall_mode='raw' requires enable_raw_store=True")


__all__ = ["MessageConfig"]
