"""Workflow state management with branch isolation."""
from __future__ import annotations

from collections import ChainMap
from typing import Any, Callable, Iterator, Protocol


class MergeStrategy(Protocol):
    """Merge strategy protocol."""
    
    def merge(self, results: list[Any]) -> Any:
        """Merge parallel results."""
        ...


class CollectListStrategy:
    """Collect results as list."""
    
    def merge(self, results: list[Any]) -> list[Any]:
        return [r for r in results if r is not None]


class CollectDictStrategy:
    """Collect results as dict."""
    
    def __init__(self, key_fn: Callable[[Any], str] | None = None):
        self.key_fn = key_fn or (lambda x: str(id(x)))
    
    def merge(self, results: list[Any]) -> dict[str, Any]:
        return {self.key_fn(r): r for r in results if r is not None}


class FirstSuccessStrategy:
    """Take first non-None result."""
    
    def merge(self, results: list[Any]) -> Any:
        return next((r for r in results if r is not None), None)


class CustomMergeStrategy:
    """Custom merge function."""
    
    def __init__(self, merge_fn: Callable[[list[Any]], Any]):
        self.merge_fn = merge_fn
    
    def merge(self, results: list[Any]) -> Any:
        return self.merge_fn(results)


class WorkflowState:
    """Workflow state with branch isolation.
    
    Uses ChainMap for copy-on-write semantics.
    """
    
    def __init__(self, parent: WorkflowState | None = None):
        self._local: dict[str, Any] = {}
        self._parent = parent
        
        if parent:
            self._chain: ChainMap[str, Any] = ChainMap(self._local, parent._chain)
        else:
            self._chain = ChainMap(self._local)
    
    def __getitem__(self, key: str) -> Any:
        return self._chain[key]
    
    def __setitem__(self, key: str, value: Any) -> None:
        self._local[key] = value
    
    def __contains__(self, key: str) -> bool:
        return key in self._chain
    
    def __iter__(self) -> Iterator[str]:
        return iter(self._chain)
    
    def get(self, key: str, default: Any = None) -> Any:
        return self._chain.get(key, default)
    
    def keys(self) -> Any:
        return self._chain.keys()
    
    def values(self) -> Any:
        return self._chain.values()
    
    def items(self) -> Any:
        return self._chain.items()
    
    def create_branch(self) -> WorkflowState:
        """Create branch for parallel execution."""
        return WorkflowState(parent=self)
    
    def get_local_changes(self) -> dict[str, Any]:
        """Get local changes."""
        return dict(self._local)
    
    def merge_from(
        self,
        other: WorkflowState,
        strategy: str = "overwrite",
    ) -> None:
        """Merge changes from another state."""
        changes = other.get_local_changes()
        
        for key, value in changes.items():
            if strategy == "overwrite":
                self._local[key] = value
            elif strategy == "append":
                if key in self._local:
                    existing = self._local[key]
                    if isinstance(existing, list):
                        existing.append(value)
                    else:
                        self._local[key] = [existing, value]
                else:
                    self._local[key] = [value]
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to regular dict."""
        return dict(self._chain)
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "WorkflowState":
        """Create from dict."""
        state = cls()
        state._local.update(data)
        return state
    
    def clear(self) -> None:
        """Clear local state."""
        self._local.clear()


def get_merge_strategy(strategy: str, **kwargs: Any) -> MergeStrategy:
    """Get merge strategy by name."""
    match strategy:
        case "collect_list":
            return CollectListStrategy()
        case "collect_dict":
            key_fn = kwargs.get("key_fn")
            return CollectDictStrategy(key_fn=key_fn)
        case "first_success":
            return FirstSuccessStrategy()
        case _:
            return CollectListStrategy()
