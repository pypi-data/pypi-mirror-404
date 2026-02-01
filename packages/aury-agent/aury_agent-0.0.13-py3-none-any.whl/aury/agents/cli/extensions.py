"""CLI Extension System for custom Agents and Tools.

This module provides a plugin/extension system that allows users to register
custom Agents and Tools that can be used with the CLI commands.

Usage:
    1. Create a configuration file (e.g., aury.extensions.toml):
       
       [agents]
       my_agent = "path.to.module:MyAgentClass"
       
       [tools]
       my_tool = "path.to.module:my_tool_function"
       
    2. Or programmatically:
       
       from aury.agents.cli.extensions import ExtensionRegistry
       registry = ExtensionRegistry()
       registry.register_agent("my_agent", MyAgentClass)
       registry.register_tool("my_tool", my_tool_function)
"""
from __future__ import annotations

import importlib
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, TYPE_CHECKING

from rich.console import Console

if TYPE_CHECKING:
    from aury.agents.core.base import BaseAgent
    from aury.agents.tools import BaseTool

console = Console()


@dataclass
class ExtensionInfo:
    """Information about a registered extension."""
    name: str
    module_path: str | None
    class_or_func: Any
    description: str = ""
    source: str = "programmatic"  # programmatic, config, entry_point


class ExtensionRegistry:
    """Registry for custom Agents and Tools.
    
    This class provides a central registry for custom extensions that can be
    used with the CLI commands. Extensions can be registered:
    
    1. Programmatically via register_agent() / register_tool()
    2. From configuration files (TOML/YAML)
    3. From Python entry points
    
    Example:
        >>> registry = ExtensionRegistry()
        >>> registry.register_agent("my_agent", MyAgent)
        >>> registry.register_tool("my_tool", my_tool_func)
        >>> 
        >>> # Load from config
        >>> registry.load_from_config("~/.aury/extensions.toml")
        >>> 
        >>> # Get registered extensions
        >>> agent_cls = registry.get_agent("my_agent")
        >>> tool = registry.get_tool("my_tool")
    """
    
    _instance: "ExtensionRegistry | None" = None
    
    def __new__(cls) -> "ExtensionRegistry":
        """Singleton pattern for global registry."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init()
        return cls._instance
    
    def _init(self) -> None:
        """Initialize the registry."""
        self._agents: dict[str, ExtensionInfo] = {}
        self._tools: dict[str, ExtensionInfo] = {}
        self._loaded_configs: set[str] = set()
    
    # ========== Agent Registration ==========
    
    def register_agent(
        self,
        name: str,
        agent_class: type["BaseAgent"],
        description: str = "",
    ) -> None:
        """Register a custom Agent class.
        
        Args:
            name: Unique name for the agent
            agent_class: The Agent class (must inherit from BaseAgent)
            description: Optional description
        """
        self._agents[name] = ExtensionInfo(
            name=name,
            module_path=f"{agent_class.__module__}:{agent_class.__name__}",
            class_or_func=agent_class,
            description=description or getattr(agent_class, "description", ""),
            source="programmatic",
        )
    
    def get_agent(self, name: str) -> type["BaseAgent"] | None:
        """Get a registered Agent class by name."""
        info = self._agents.get(name)
        if info:
            return info.class_or_func
        return None
    
    def list_agents(self) -> list[ExtensionInfo]:
        """List all registered Agents."""
        return list(self._agents.values())
    
    # ========== Tool Registration ==========
    
    def register_tool(
        self,
        name: str,
        tool: "BaseTool | Callable",
        description: str = "",
    ) -> None:
        """Register a custom Tool.
        
        Args:
            name: Unique name for the tool
            tool: Tool instance or function decorated with @tool
            description: Optional description
        """
        self._tools[name] = ExtensionInfo(
            name=name,
            module_path=self._get_module_path(tool),
            class_or_func=tool,
            description=description or getattr(tool, "description", ""),
            source="programmatic",
        )
    
    def get_tool(self, name: str) -> "BaseTool | Callable | None":
        """Get a registered Tool by name."""
        info = self._tools.get(name)
        if info:
            return info.class_or_func
        return None
    
    def list_tools(self) -> list[ExtensionInfo]:
        """List all registered Tools."""
        return list(self._tools.values())
    
    # ========== Config Loading ==========
    
    def load_from_config(self, config_path: str | Path) -> int:
        """Load extensions from a configuration file.
        
        Supports TOML format:
        
            [agents]
            my_agent = "mymodule.agents:MyAgent"
            
            [tools]
            my_tool = "mymodule.tools:my_tool"
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Number of extensions loaded
        """
        config_path = Path(config_path).expanduser()
        
        if not config_path.exists():
            return 0
        
        config_key = str(config_path.resolve())
        if config_key in self._loaded_configs:
            return 0
        
        self._loaded_configs.add(config_key)
        
        count = 0
        
        try:
            import tomllib
        except ImportError:
            import tomli as tomllib
        
        try:
            with open(config_path, "rb") as f:
                config = tomllib.load(f)
            
            # Load agents
            for name, path in config.get("agents", {}).items():
                try:
                    cls = self._import_from_string(path)
                    self._agents[name] = ExtensionInfo(
                        name=name,
                        module_path=path,
                        class_or_func=cls,
                        source="config",
                    )
                    count += 1
                except Exception as e:
                    console.print(f"[yellow]Warning: Failed to load agent '{name}': {e}[/yellow]")
            
            # Load tools
            for name, path in config.get("tools", {}).items():
                try:
                    func = self._import_from_string(path)
                    self._tools[name] = ExtensionInfo(
                        name=name,
                        module_path=path,
                        class_or_func=func,
                        source="config",
                    )
                    count += 1
                except Exception as e:
                    console.print(f"[yellow]Warning: Failed to load tool '{name}': {e}[/yellow]")
        
        except Exception as e:
            console.print(f"[yellow]Warning: Failed to load config {config_path}: {e}[/yellow]")
        
        return count
    
    def load_from_directory(self, directory: str | Path) -> int:
        """Load extensions from Python files in a directory.
        
        Scans for .py files and looks for:
        - Classes with `register_as_agent = True`
        - Functions decorated with `@tool`
        
        Args:
            directory: Directory to scan
            
        Returns:
            Number of extensions loaded
        """
        directory = Path(directory).expanduser()
        
        if not directory.is_dir():
            return 0
        
        count = 0
        
        for py_file in directory.glob("*.py"):
            if py_file.name.startswith("_"):
                continue
            
            try:
                count += self._load_from_file(py_file)
            except Exception as e:
                console.print(f"[yellow]Warning: Failed to load {py_file}: {e}[/yellow]")
        
        return count
    
    def load_from_entry_points(self, group: str = "aury.extensions") -> int:
        """Load extensions from Python entry points.
        
        This allows packages to declare extensions in their pyproject.toml:
        
            [project.entry-points."aury.extensions"]
            my_agent = "mypackage:MyAgent"
            my_tool = "mypackage:my_tool"
        
        Args:
            group: Entry point group name
            
        Returns:
            Number of extensions loaded
        """
        count = 0
        
        try:
            from importlib.metadata import entry_points
            
            # Python 3.10+ syntax
            eps = entry_points(group=group)
            
            for ep in eps:
                try:
                    obj = ep.load()
                    
                    # Determine if it's an Agent or Tool
                    if self._is_agent_class(obj):
                        self._agents[ep.name] = ExtensionInfo(
                            name=ep.name,
                            module_path=f"{ep.value}",
                            class_or_func=obj,
                            source="entry_point",
                        )
                        count += 1
                    elif self._is_tool(obj):
                        self._tools[ep.name] = ExtensionInfo(
                            name=ep.name,
                            module_path=f"{ep.value}",
                            class_or_func=obj,
                            source="entry_point",
                        )
                        count += 1
                except Exception as e:
                    console.print(f"[yellow]Warning: Failed to load entry point '{ep.name}': {e}[/yellow]")
        
        except Exception:
            pass  # Entry points not available
        
        return count
    
    def auto_discover(self) -> int:
        """Auto-discover extensions from common locations.
        
        Searches:
        - ~/.aury/extensions.toml
        - ./aury.extensions.toml
        - ~/.aury/extensions/
        - ./extensions/
        - Python entry points
        
        Returns:
            Total number of extensions loaded
        """
        count = 0
        
        # Config files
        count += self.load_from_config(Path.home() / ".aury" / "extensions.toml")
        count += self.load_from_config(Path.cwd() / "aury.extensions.toml")
        
        # Extension directories
        count += self.load_from_directory(Path.home() / ".aury" / "extensions")
        count += self.load_from_directory(Path.cwd() / "extensions")
        
        # Entry points
        count += self.load_from_entry_points()
        
        return count
    
    # ========== Helper Methods ==========
    
    def _import_from_string(self, path: str) -> Any:
        """Import a class or function from a string like 'module.path:ClassName'."""
        if ":" in path:
            module_path, attr_name = path.rsplit(":", 1)
        else:
            # Assume it's just a module with a default export
            module_path = path
            attr_name = None
        
        module = importlib.import_module(module_path)
        
        if attr_name:
            return getattr(module, attr_name)
        return module
    
    def _get_module_path(self, obj: Any) -> str:
        """Get module path string for an object."""
        if hasattr(obj, "__module__") and hasattr(obj, "__name__"):
            return f"{obj.__module__}:{obj.__name__}"
        elif hasattr(obj, "__module__") and hasattr(obj, "__class__"):
            return f"{obj.__module__}:{obj.__class__.__name__}"
        return "unknown"
    
    def _is_agent_class(self, obj: Any) -> bool:
        """Check if object is an Agent class."""
        from aury.agents.core.base import BaseAgent
        return isinstance(obj, type) and issubclass(obj, BaseAgent)
    
    def _is_tool(self, obj: Any) -> bool:
        """Check if object is a Tool."""
        from aury.agents.tools import BaseTool
        # Check if it's a BaseTool instance or has tool decorator attributes
        return (
            isinstance(obj, BaseTool) or
            hasattr(obj, "_tool_name") or
            hasattr(obj, "name") and hasattr(obj, "execute")
        )
    
    def _load_from_file(self, path: Path) -> int:
        """Load extensions from a Python file."""
        count = 0
        
        # Add parent directory to path
        sys.path.insert(0, str(path.parent))
        
        try:
            spec = importlib.util.spec_from_file_location(path.stem, path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Find agents and tools
            for name in dir(module):
                if name.startswith("_"):
                    continue
                
                obj = getattr(module, name)
                
                if self._is_agent_class(obj):
                    agent_name = getattr(obj, "name", name.lower())
                    self._agents[agent_name] = ExtensionInfo(
                        name=agent_name,
                        module_path=f"{path}:{name}",
                        class_or_func=obj,
                        description=getattr(obj, "description", ""),
                        source="file",
                    )
                    count += 1
                
                elif self._is_tool(obj):
                    tool_name = getattr(obj, "name", getattr(obj, "_tool_name", name.lower()))
                    self._tools[tool_name] = ExtensionInfo(
                        name=tool_name,
                        module_path=f"{path}:{name}",
                        class_or_func=obj,
                        description=getattr(obj, "description", ""),
                        source="file",
                    )
                    count += 1
        
        finally:
            sys.path.pop(0)
        
        return count
    
    def clear(self) -> None:
        """Clear all registered extensions."""
        self._agents.clear()
        self._tools.clear()
        self._loaded_configs.clear()


# Global registry instance
registry = ExtensionRegistry()


# Convenience functions
def register_agent(name: str, agent_class: type["BaseAgent"], description: str = "") -> None:
    """Register a custom Agent class globally."""
    registry.register_agent(name, agent_class, description)


def register_tool(name: str, tool: "BaseTool | Callable", description: str = "") -> None:
    """Register a custom Tool globally."""
    registry.register_tool(name, tool, description)


def get_agent(name: str) -> type["BaseAgent"] | None:
    """Get a registered Agent by name."""
    return registry.get_agent(name)


def get_tool(name: str) -> "BaseTool | Callable | None":
    """Get a registered Tool by name."""
    return registry.get_tool(name)


def auto_discover() -> int:
    """Auto-discover all extensions."""
    return registry.auto_discover()
