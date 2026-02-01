"""MCP (Model Context Protocol) integration module.

This module provides MCP client functionality for connecting to MCP servers
and discovering/invoking tools, resources, and prompts.

Key components:
- MCPClient: High-level client for MCP server interaction
- MCPTransport: Transport layer abstraction (Stdio, HTTP)
- MCPServerConfig: Server configuration model

Example:
    from gridcode.mcp import MCPClient, MCPServerConfig

    config = MCPServerConfig(
        name="my-server",
        command="uv",
        args=["run", "my-mcp-server"],
    )

    async with MCPClient(config) as client:
        tools = await client.list_tools()
        result = await client.call_tool("my_tool", {"arg": "value"})

Note: This module uses lazy loading to improve startup time. MCP classes are only
imported when first accessed, allowing faster startup for applications that don't
use the MCP system.
"""

__all__ = [
    "MCPClient",
    "MCPServerConfig",
    "MCPTool",
    "MCPToolResult",
    "MCPResource",
    "MCPPrompt",
    "TransportType",
    "create_mcp_client",
]

# Lazy loading module map
_LAZY_MODULES = {
    "MCPClient": ("gridcode.mcp.client", "MCPClient"),
    "MCPServerConfig": ("gridcode.mcp.client", "MCPServerConfig"),
    "MCPTool": ("gridcode.mcp.client", "MCPTool"),
    "MCPToolResult": ("gridcode.mcp.client", "MCPToolResult"),
    "MCPResource": ("gridcode.mcp.client", "MCPResource"),
    "MCPPrompt": ("gridcode.mcp.client", "MCPPrompt"),
    "TransportType": ("gridcode.mcp.client", "TransportType"),
    "create_mcp_client": ("gridcode.mcp.client", "create_mcp_client"),
}

# Cache for lazy-loaded modules
_LAZY_CACHE = {}


def __getattr__(name: str):
    """Lazy load MCP classes on first access."""
    if name in _LAZY_MODULES:
        if name not in _LAZY_CACHE:
            module_name, class_name = _LAZY_MODULES[name]
            module = __import__(module_name, fromlist=[class_name])
            _LAZY_CACHE[name] = getattr(module, class_name)
        return _LAZY_CACHE[name]
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
