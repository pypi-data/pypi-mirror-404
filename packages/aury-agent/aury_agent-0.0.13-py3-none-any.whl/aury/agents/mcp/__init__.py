"""MCP (Model Context Protocol) module.

TODO: Implement MCP protocol support.

This module will provide:
- MCPToolset: Connect to external MCP servers and use their tools
- MCPServer: Expose Aury tools as MCP server
- MCPClient: Low-level MCP client for discovery

Reference: Model Context Protocol
https://modelcontextprotocol.io/
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from ..tool import BaseTool


# =============================================================================
# Connection Parameters
# =============================================================================

@dataclass
class StdioServerParams:
    """Parameters for connecting to MCP server via stdio.
    
    TODO: Implement stdio transport.
    """
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)


@dataclass
class HttpServerParams:
    """Parameters for connecting to MCP server via HTTP.
    
    TODO: Implement HTTP transport.
    """
    url: str
    headers: dict[str, str] = field(default_factory=dict)


# =============================================================================
# TODO: MCP Toolset
# =============================================================================

class MCPToolset:
    """Connect to external MCP servers and use their tools.
    
    TODO: Implement MCP toolset.
    
    Usage:
        mcp_tools = MCPToolset(
            connection_params=StdioServerParams(
                command="npx",
                args=["-y", "@modelcontextprotocol/server-filesystem", "/path"],
            ),
            tool_filter=["read_file", "list_directory"],
        )
        agent = ReactAgent.create(llm=llm, tools=[mcp_tools])
    """
    
    def __init__(
        self,
        connection_params: StdioServerParams | HttpServerParams,
        tool_filter: list[str] | None = None,
    ):
        self.connection_params = connection_params
        self.tool_filter = tool_filter
        raise NotImplementedError("TODO: MCP toolset not yet implemented")
    
    async def connect(self) -> None:
        """Connect to MCP server."""
        raise NotImplementedError("TODO: MCP connect not yet implemented")
    
    async def get_tools(self) -> list[Any]:
        """Get tools from MCP server."""
        raise NotImplementedError("TODO: MCP get_tools not yet implemented")


# =============================================================================
# TODO: MCP Server
# =============================================================================

class MCPServer:
    """Expose Aury tools as MCP server.
    
    TODO: Implement MCP server.
    
    Usage:
        server = MCPServer(
            name="my_service",
            tools=[my_tool1, my_tool2],
            transport="http",
            port=8000,
        )
        await server.start()
    """
    
    def __init__(
        self,
        name: str,
        tools: list["BaseTool"],
        transport: str = "stdio",
        host: str = "0.0.0.0",
        port: int = 8000,
    ):
        self.name = name
        self.tools = tools
        self.transport = transport
        self.host = host
        self.port = port
        raise NotImplementedError("TODO: MCP server not yet implemented")
    
    async def start(self) -> None:
        """Start MCP server."""
        raise NotImplementedError("TODO: MCP server not yet implemented")
    
    async def stop(self) -> None:
        """Stop MCP server."""
        raise NotImplementedError("TODO: MCP server not yet implemented")


# =============================================================================
# TODO: MCP Client
# =============================================================================

class MCPClient:
    """Low-level MCP client for discovery.
    
    TODO: Implement MCP client.
    """
    
    def __init__(self, url: str):
        self.url = url
        raise NotImplementedError("TODO: MCP client not yet implemented")
    
    async def discover(self) -> Any:
        """Discover MCP server capabilities."""
        raise NotImplementedError("TODO: MCP discover not yet implemented")


__all__ = [
    "StdioServerParams",
    "HttpServerParams",
    "MCPToolset",
    "MCPServer",
    "MCPClient",
]
