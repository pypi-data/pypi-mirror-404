"""State isolation for SubAgent execution.

Provides ChainMap-based state isolation for EMBEDDED mode SubAgents.
"""
from __future__ import annotations

from abc import abstractmethod
from collections import ChainMap
from typing import Any, Protocol


class StateIsolator(Protocol):
    """Protocol for state isolation.
    
    Used to isolate state changes in EMBEDDED SubAgent mode.
    Changes in child scope don't affect parent until merged.
    """
    
    @abstractmethod
    def create_branch(self) -> "StateIsolator":
        """Create a child branch with isolated state."""
        ...
    
    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from state."""
        ...
    
    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Set value in current scope (doesn't affect parent)."""
        ...
    
    @abstractmethod
    def get_local_changes(self) -> dict[str, Any]:
        """Get changes made in current scope only."""
        ...
    
    @abstractmethod
    def merge_to_parent(self) -> None:
        """Merge local changes to parent scope."""
        ...


class ChainMapIsolator:
    """ChainMap-based state isolator.
    
    Uses ChainMap to provide copy-on-write semantics.
    Child writes go to a new dict, reads fall through to parent.
    """
    
    def __init__(self, parent: "ChainMapIsolator | None" = None):
        self._parent = parent
        if parent is None:
            self._chain = ChainMap({})
        else:
            # New child map on top of parent's chain
            self._chain = parent._chain.new_child()
    
    def create_branch(self) -> "ChainMapIsolator":
        """Create a child branch."""
        return ChainMapIsolator(parent=self)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value, falling through to parent if not in local."""
        return self._chain.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set value in local scope."""
        self._chain.maps[0][key] = value
    
    def get_local_changes(self) -> dict[str, Any]:
        """Get only the changes made in this scope."""
        return dict(self._chain.maps[0])
    
    def merge_to_parent(self) -> None:
        """Merge local changes to parent."""
        if self._parent is not None:
            local = self.get_local_changes()
            for k, v in local.items():
                self._parent.set(k, v)
    
    def __getitem__(self, key: str) -> Any:
        return self._chain[key]
    
    def __setitem__(self, key: str, value: Any) -> None:
        self.set(key, value)
    
    def __contains__(self, key: str) -> bool:
        return key in self._chain
    
    def to_dict(self) -> dict[str, Any]:
        """Flatten to dict (for serialization)."""
        return dict(self._chain)


__all__ = ["StateIsolator", "ChainMapIsolator"]
