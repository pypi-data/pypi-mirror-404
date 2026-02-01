"""ToolContextProvider - example of dynamic tool discovery.

NOTE: This provider is commented out as an EXAMPLE.
In most cases, tools should be passed directly to ReactAgent.create(tools=[...]).

This provider is useful for:
- Dynamic tool discovery (MCP, database, etc.)
- Permission-based tool filtering
- Runtime tool injection

Usage:
    class MCPToolContextProvider(BaseContextProvider):
        async def fetch(self, ctx):
            # Discover tools from MCP server
            tools = await self.mcp_client.list_tools()
            return AgentContext(tools=tools)
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from .base import BaseContextProvider, AgentContext

if TYPE_CHECKING:
    from ..core.context import InvocationContext
    from ..core.types.tool import BaseTool


# =============================================================================
# ToolContextProvider - Example (commented out)
# =============================================================================
# 
# class ToolContextProvider(BaseContextProvider):
#     """Tool context provider - for dynamic tool discovery.
#     
#     NOTE: Static tools should be passed directly to Agent.
#     This provider is for DYNAMIC tool discovery only.
#     
#     Example use cases:
#     1. MCP server - discover tools at runtime
#     2. Permission-based - filter tools by user permissions
#     3. Database - load tools from database
#     
#     Usage:
#         class MCPToolContextProvider(ToolContextProvider):
#             async def discover(self, ctx):
#                 return await self.mcp_client.list_tools()
#     """
#     
#     _name = "tools"
#     
#     async def fetch(self, ctx: "InvocationContext") -> AgentContext:
#         """Fetch tools dynamically."""
#         discovered = await self.discover(ctx)
#         return AgentContext(tools=discovered)
#     
#     async def discover(self, ctx: "InvocationContext") -> list["BaseTool"]:
#         """Override this for custom discovery logic.
#         
#         Examples:
#         - Fetch from MCP server
#         - Filter by user permissions
#         - Load from database
#         """
#         return []


__all__: list[str] = []  # No exports - this is an example file
