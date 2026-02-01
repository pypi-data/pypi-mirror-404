"""ActionEvent for framework-level state and result passing.

Unlike BlockEvent (for UI streaming), ActionEvent is used for:
- State changes (state_delta)
- Result passing between agents
- Framework-level signals

ActionEvents can be internal (not sent to external API) or external.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from .session import generate_id


class ActionType(str, Enum):
    """Built-in action types."""
    
    # State management
    STATE_DELTA = "state_delta"      # Update state with delta
    SET_RESULT = "set_result"        # Set agent result (text + structured)
    
    # Control flow
    TRANSFER = "transfer"            # Transfer to another agent
    END_AGENT = "end_agent"          # Agent finished
    
    # Progress (can be external)
    PROGRESS = "progress"            # Progress update


@dataclass
class ActionEvent:
    """Action event for framework-level operations.
    
    Emitted via ctx.emit() alongside BlockEvents.
    Framework collects these for state management and result passing.
    
    Attributes:
        action: Action type (ActionType enum or custom string)
        data: Action payload
        branch: Branch identifier for parallel execution isolation
        internal: If True, not sent to external API (default: True)
        event_id: Unique event identifier
        timestamp: Event timestamp in milliseconds
    
    Example:
        # Internal action - framework only
        await ctx.emit(ActionEvent(
            action=ActionType.SET_RESULT,
            data={"text": "报告已完成", "artifact_id": "xxx"},
            branch="report_writer",
        ))
        
        # External action - also sent to API
        await ctx.emit(ActionEvent(
            action=ActionType.PROGRESS,
            data={"percent": 50, "message": "生成中..."},
            internal=False,
        ))
    """
    
    action: ActionType | str
    data: dict[str, Any] = field(default_factory=dict)
    branch: str | None = None
    internal: bool = True  # Default: not sent to external API
    
    # Protocol fields
    event_id: str = field(default_factory=lambda: generate_id("act"))
    timestamp: int = field(default_factory=lambda: int(datetime.now().timestamp() * 1000))
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        action_value = self.action.value if isinstance(self.action, ActionType) else self.action
        return {
            "type": "action",  # Distinguish from BlockEvent
            "action": action_value,
            "data": self.data,
            "branch": self.branch,
            "internal": self.internal,
            "event_id": self.event_id,
            "timestamp": self.timestamp,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ActionEvent:
        """Create from dictionary."""
        action_str = data["action"]
        try:
            action = ActionType(action_str)
        except ValueError:
            action = action_str  # Custom action string
        return cls(
            action=action,
            data=data.get("data", {}),
            branch=data.get("branch"),
            internal=data.get("internal", True),
            event_id=data.get("event_id", ""),
            timestamp=data.get("timestamp", 0),
        )


@dataclass
class ActionCollector:
    """Collects ActionEvents during agent execution.
    
    Used by framework to aggregate actions from agent and sub-agents.
    Supports branch-based isolation for parallel execution.
    """
    
    def __init__(self):
        self._actions: list[ActionEvent] = []
        self._branch_results: dict[str, dict[str, Any]] = {}
        self._state_delta: dict[str, Any] = {}
    
    def collect(self, event: ActionEvent) -> None:
        """Collect an action event."""
        self._actions.append(event)
        
        # Handle specific action types
        if event.action == ActionType.STATE_DELTA:
            self._merge_state_delta(event.data)
        elif event.action == ActionType.SET_RESULT:
            branch = event.branch or "_default"
            self._branch_results[branch] = event.data
    
    def _merge_state_delta(self, delta: dict[str, Any]) -> None:
        """Merge state delta into accumulated state."""
        for key, value in delta.items():
            if isinstance(value, dict) and isinstance(self._state_delta.get(key), dict):
                # Deep merge dicts
                self._state_delta[key] = {**self._state_delta[key], **value}
            else:
                self._state_delta[key] = value
    
    @property
    def state_delta(self) -> dict[str, Any]:
        """Get accumulated state delta."""
        return self._state_delta
    
    @property
    def branch_results(self) -> dict[str, dict[str, Any]]:
        """Get results by branch."""
        return self._branch_results
    
    @property
    def actions(self) -> list[ActionEvent]:
        """Get all collected actions."""
        return self._actions
    
    def get_results(self) -> list[dict[str, Any]]:
        """Get all SET_RESULT actions as array.
        
        Returns list of raw result data, caller handles formatting.
        """
        return list(self._branch_results.values())
    
    def get_result(self, branch: str = "_default") -> dict[str, Any] | None:
        """Get result for specific branch."""
        return self._branch_results.get(branch)
    
    def clear(self) -> None:
        """Clear all collected actions."""
        self._actions.clear()
        self._branch_results.clear()
        self._state_delta.clear()


__all__ = [
    "ActionType",
    "ActionEvent",
    "ActionCollector",
]
