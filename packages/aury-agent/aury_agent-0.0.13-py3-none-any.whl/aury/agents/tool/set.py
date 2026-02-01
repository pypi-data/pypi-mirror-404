"""ToolSet - A collection of tools."""
from __future__ import annotations

from typing import Any, Callable

from ..core.types.tool import BaseTool, ToolInfo
from ..core.logging import tool_logger as logger


class ToolSet:
    """A collection of tools with lookup, filtering, and merging capabilities.
    
    ToolSet provides:
    - Fast lookup by tool ID
    - Lazy instantiation with caching
    - Filtering (include/exclude)
    - Merging multiple sets
    
    Usage:
        # From list
        tools = ToolSet.from_list([tool1, tool2])
        
        # Manual construction
        tools = ToolSet()
        tools.add(my_tool)
        
        # Filtering
        subset = tools.filtered(include=["read_file", "write_file"])
        
        # Merging
        combined = tools.merge(other_tools)
    """
    
    def __init__(self) -> None:
        self._tools: dict[str, Callable[[], BaseTool]] = {}
        self._instances: dict[str, BaseTool] = {}  # Cached instances
    
    @classmethod
    def from_list(cls, tools: list[BaseTool]) -> "ToolSet":
        """Create ToolSet from a list of tools.
        
        Args:
            tools: List of tool instances
            
        Returns:
            New ToolSet containing all tools
        """
        logger.debug(f"ToolSet.from_list creating with {len(tools)} tools")
        ts = cls()
        for tool in tools:
            ts.add(tool)
        logger.debug(f"ToolSet.from_list completed, total tools={len(ts)}")
        return ts
    
    def add(
        self,
        tool: BaseTool | Callable[[], BaseTool],
        replace: bool = False,
    ) -> None:
        """Add a tool to the set.
        
        Args:
            tool: Tool instance or factory function
            replace: Allow replacing existing tool
        """
        # If it's a BaseTool instance, wrap it in a lambda
        if isinstance(tool, BaseTool):
            tool_name = tool.name
            factory: Callable[[], BaseTool] = lambda t=tool: t
        else:
            # It's a factory, call it once to get the name
            instance = tool()
            tool_name = instance.name
            factory = tool
        
        if tool_name in self._tools and not replace:
            logger.warning(f"ToolSet.add: tool already registered, tool={tool_name}")
            raise ValueError(f"Tool already registered: {tool_name}")
        
        logger.debug(f"ToolSet.add: adding tool, tool={tool_name}, replace={replace}, total_before={len(self._tools)}")
        self._tools[tool_name] = factory
        # Clear cached instance
        if tool_name in self._instances:
            del self._instances[tool_name]
        logger.debug(f"ToolSet.add: tool added, tool={tool_name}, total_after={len(self._tools)}")
    
    def remove(self, tool_id: str) -> bool:
        """Remove a tool from the set.
        
        Args:
            tool_id: Tool identifier to remove
            
        Returns:
            True if tool was removed, False if not found
        """
        if tool_id in self._tools:
            logger.debug(f"ToolSet.remove: removing tool, tool={tool_id}")
            del self._tools[tool_id]
            if tool_id in self._instances:
                del self._instances[tool_id]
            logger.debug(f"ToolSet.remove: tool removed, tool={tool_id}, total={len(self._tools)}")
            return True
        logger.debug(f"ToolSet.remove: tool not found, tool={tool_id}")
        return False
    
    def get(self, tool_id: str, cached: bool = True) -> BaseTool:
        """Get a tool instance.
        
        Args:
            tool_id: Tool identifier
            cached: Whether to use cached instance
            
        Returns:
            BaseTool instance
            
        Raises:
            KeyError: If tool not found
        """
        if tool_id not in self._tools:
            logger.warning(f"ToolSet.get: tool not found, tool={tool_id}")
            raise KeyError(f"Tool not found: {tool_id}")
        
        if cached and tool_id in self._instances:
            logger.debug(f"ToolSet.get: returning cached instance, tool={tool_id}")
            return self._instances[tool_id]
        
        logger.debug(f"ToolSet.get: instantiating tool, tool={tool_id}, cached={cached}")
        instance = self._tools[tool_id]()
        if cached:
            self._instances[tool_id] = instance
        
        return instance
    
    def has(self, tool_id: str) -> bool:
        """Check if tool is registered."""
        return tool_id in self._tools
    
    def all(self, cached: bool = True) -> list[BaseTool]:
        """Get all registered tools.
        
        Args:
            cached: Whether to use cached instances
        """
        return [self.get(tid, cached=cached) for tid in self._tools]
    
    def all_info(self) -> list[ToolInfo]:
        """Get info for all registered tools."""
        return [tool.get_info() for tool in self.all()]
    
    def ids(self) -> list[str]:
        """Get all registered tool IDs."""
        return list(self._tools.keys())
    
    def filtered(
        self,
        include: list[str] | None = None,
        exclude: list[str] | None = None,
    ) -> "ToolSet":
        """Create a filtered copy of this set.
        
        Args:
            include: Only include these tools (None = all)
            exclude: Exclude these tools
            
        Returns:
            New ToolSet with filtered tools
        """
        logger.debug(f"ToolSet.filtered: creating filtered set, include={include}, exclude={exclude}, total_before={len(self._tools)}")
        filtered = ToolSet()
        excluded_count = 0
        
        for tool_id, factory in self._tools.items():
            # Check include filter
            if include is not None and tool_id not in include:
                excluded_count += 1
                continue
            
            # Check exclude filter
            if exclude is not None and tool_id in exclude:
                excluded_count += 1
                continue
            
            filtered._tools[tool_id] = factory
        
        logger.debug(f"ToolSet.filtered: filtered set created, total_after={len(filtered._tools)}, excluded={excluded_count}")
        return filtered
    
    def merge(self, other: "ToolSet", replace: bool = False) -> "ToolSet":
        """Merge another ToolSet into this one.
        
        Args:
            other: ToolSet to merge
            replace: Allow replacing existing tools
            
        Returns:
            Self for chaining
        """
        logger.debug(f"ToolSet.merge: merging, other_size={len(other)}, total_before={len(self._tools)}, replace={replace}")
        merged_count = 0
        for tool_id, factory in other._tools.items():
            if tool_id not in self._tools or replace:
                merged_count += 1
                self._tools[tool_id] = factory
        logger.debug(f"ToolSet.merge: merge completed, merged={merged_count}, total_after={len(self._tools)}")
        return self
    
    def copy(self) -> "ToolSet":
        """Create a copy of this set."""
        logger.debug(f"ToolSet.copy: copying set, size={len(self._tools)}")
        new = ToolSet()
        new._tools = dict(self._tools)
        return new
    
    def clear(self) -> None:
        """Clear all tools."""
        logger.debug(f"ToolSet.clear: clearing set, total={len(self._tools)}")
        self._tools.clear()
        self._instances.clear()
    
    def __len__(self) -> int:
        return len(self._tools)
    
    def __contains__(self, tool_id: str) -> bool:
        return tool_id in self._tools
    
    def __iter__(self):
        return iter(self.all())
