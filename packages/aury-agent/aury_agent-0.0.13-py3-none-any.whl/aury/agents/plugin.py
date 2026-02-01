"""Plugin system for packaging providers, middlewares and tools.

The Plugin class provides an optional assembly layer that packages:
- ContextProviders (context sources)
- Middlewares (execution hooks)
- Tools, Skills, SubAgents (direct contributions)

Design Goals:
1. Simple case: Use plugins for packaged functionality
2. Flexible case: Use providers/middlewares directly
3. Mixed case: Combine plugins with custom providers/middlewares

Example Usage:
    # Simple: use plugins
    agent = ReactAgent.create(
        llm=llm,
        plugins=[CodePlugin()],
    )

    # Flexible: use providers/middlewares directly
    agent = ReactAgent.create(
        llm=llm,
        context_providers=[MyCustomProvider()],
        middlewares=[MyMiddleware()],
    )

    # Mixed + custom
    agent = ReactAgent.create(
        llm=llm,
        plugins=[CodePlugin()],
        context_providers=[MyRAGProvider()],
        subagents=[researcher_config],
        delegate_tool_class=MyDelegateTool,
    )

Inheritance Rules:
- Plugin.inherit: Whether this plugin should be inherited by sub-agents
- AgentConfig.inherit_plugins: Whether to inherit plugins from parent
- Both must be True for inheritance to occur
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .core.types.tool import BaseTool
    from .skill import Skill
    from .backends.subagent import AgentConfig as SubAgentConfig
    from .context_providers.base import ContextProvider
    from .middleware.base import Middleware


# =============================================================================
# Plugin class
# =============================================================================

# @dataclass
# class Plugin:
#     """Plugin packages providers, middlewares, tools, skills, and subagents.
#     
#     Attributes:
#         name: Plugin identifier
#         priority: Execution order (lower runs first, default 100)
#         inherit: Whether this plugin should be inherited by sub-agents
#         tools: Tools provided by this plugin
#         skills: Skills provided by this plugin
#         subagents: SubAgent configs provided by this plugin
#         providers: ContextProviders provided by this plugin
#         middlewares: Middlewares provided by this plugin
#     
#     Priority Guidelines:
#         0-50: Core/framework plugins (run first)
#         50-100: Standard plugins
#         100+: User plugins (run last)
#     
#     Example:
#         @dataclass
#         class CodePlugin(Plugin):
#             name: str = "code"
#             priority: int = 50
#             inherit: bool = True
#             
#             def __post_init__(self):
#                 self.tools = [
#                     FileReadTool(),
#                     FileWriteTool(),
#                     ShellTool(),
#                 ]
#                 self.providers = [
#                     ProjectContextProvider(),
#                 ]
#                 self.middlewares = [
#                     CodeReviewMiddleware(),
#                 ]
#     """
#     
#     name: str
#     priority: int = 100
#     inherit: bool = False
#     
#     tools: list["BaseTool"] = field(default_factory=list)
#     skills: list["Skill"] = field(default_factory=list)
#     subagents: list["SubAgentConfig"] = field(default_factory=list)
#     providers: list["ContextProvider"] = field(default_factory=list)
#     middlewares: list["Middleware"] = field(default_factory=list)


# =============================================================================
# PluginChain for managing multiple plugins
# =============================================================================

# class PluginChain:
#     """Chain of plugins sorted by priority.
#     
#     Provides methods to:
#     - Collect all tools from plugins
#     - Collect all providers from plugins
#     - Collect all middlewares from plugins
#     - Get inheritable plugins for sub-agents
#     """
#     
#     def __init__(self, plugins: list[Plugin] | None = None):
#         self._plugins: list[Plugin] = []
#         if plugins:
#             for p in plugins:
#                 self.add(p)
#     
#     def add(self, plugin: Plugin) -> "PluginChain":
#         """Add plugin and maintain sorted order by priority."""
#         self._plugins.append(plugin)
#         self._plugins.sort(key=lambda p: p.priority)
#         return self
#     
#     def collect_tools(self) -> list["BaseTool"]:
#         """Collect all tools from all plugins."""
#         tools = []
#         for p in self._plugins:
#             tools.extend(p.tools)
#         return tools
#     
#     def collect_providers(self) -> list["ContextProvider"]:
#         """Collect all providers from all plugins."""
#         providers = []
#         for p in self._plugins:
#             providers.extend(p.providers)
#         return providers
#     
#     def collect_middlewares(self) -> list["Middleware"]:
#         """Collect all middlewares from all plugins."""
#         middlewares = []
#         for p in self._plugins:
#             middlewares.extend(p.middlewares)
#         return middlewares
#     
#     def get_inheritable(self) -> list[Plugin]:
#         """Get plugins that should be inherited by sub-agents."""
#         return [p for p in self._plugins if p.inherit]


__all__: list[str] = []  # Classes are commented out
