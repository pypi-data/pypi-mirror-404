"""MCP Plugin for GridCode Runtime.

This plugin provides MCP (Model Context Protocol) integration, allowing
GridCode to connect to MCP servers and use their tools, resources, and prompts.

Example:
    from gridcode.plugins.mcp import MCPPlugin
    from gridcode.mcp import MCPServerConfig

    # Create plugin with server config
    config = MCPServerConfig(
        name="my-server",
        command="uv",
        args=["run", "my-mcp-server"],
    )
    plugin = MCPPlugin(config)

    # Load plugin into runtime
    await runtime.plugin_manager.load_plugin(plugin)
"""

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from loguru import logger

from gridcode.mcp.client import MCPClient, MCPServerConfig, MCPTool
from gridcode.plugins.base import Plugin, PluginType

if TYPE_CHECKING:
    from gridcode.core.runtime import GridCodeRuntime


class MCPPlugin(Plugin):
    """Plugin for MCP server integration.

    This plugin connects to an MCP server and registers its tools
    with the GridCode runtime's tool registry.

    Attributes:
        name: Plugin name (derived from server config name)
        version: Plugin version
        plugin_type: PluginType.TOOL
        provides: ["mcp-integration", "mcp-tools"]
    """

    version: str = "1.0.0"
    description: str = "MCP server integration plugin"
    author: str = "GridCode"
    plugin_type: PluginType = PluginType.TOOL
    provides: list[str] = ["mcp-integration", "mcp-tools"]

    def __init__(self, config: MCPServerConfig, auto_connect: bool = True):
        """Initialize the MCP plugin.

        Args:
            config: MCP server configuration
            auto_connect: Whether to automatically connect on load
        """
        super().__init__()
        self.config = config
        self.auto_connect = auto_connect
        self._client: MCPClient | None = None
        self._registered_tools: list[str] = []

        # Set plugin name from config
        self.name = f"mcp-{config.name}"
        self.description = f"MCP integration for {config.name} server"

    @property
    def client(self) -> MCPClient:
        """Get the MCP client.

        Raises:
            RuntimeError: If not connected
        """
        if self._client is None:
            raise RuntimeError("MCP client not connected")
        return self._client

    @property
    def is_connected(self) -> bool:
        """Check if connected to the MCP server."""
        return self._client is not None and self._client.is_connected

    async def on_load(self, runtime: "GridCodeRuntime") -> None:
        """Load the plugin and connect to the MCP server.

        This method:
        1. Creates an MCP client
        2. Connects to the server
        3. Discovers available tools
        4. Registers tools with the runtime

        Args:
            runtime: The GridCodeRuntime instance
        """
        logger.info(f"Loading MCP plugin for server: {self.config.name}")

        # Create client
        self._client = MCPClient(self.config)

        # Connect if auto_connect is enabled
        if self.auto_connect:
            await self.connect()
            await self._register_tools(runtime)

    async def on_unload(self) -> None:
        """Unload the plugin and disconnect from the MCP server.

        This method:
        1. Unregisters all MCP tools from the runtime
        2. Disconnects from the server
        """
        logger.info(f"Unloading MCP plugin: {self.name}")

        # Unregister tools
        await self._unregister_tools()

        # Disconnect
        if self._client:
            await self._client.disconnect()
            self._client = None

    async def connect(self) -> None:
        """Connect to the MCP server.

        This can be called manually if auto_connect is False.
        """
        if self._client is None:
            self._client = MCPClient(self.config)

        if not self._client.is_connected:
            await self._client.connect()
            logger.info(f"Connected to MCP server: {self.config.name}")

    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        if self._client and self._client.is_connected:
            await self._client.disconnect()
            logger.info(f"Disconnected from MCP server: {self.config.name}")

    async def _register_tools(self, runtime: "GridCodeRuntime") -> None:
        """Register MCP tools with the runtime.

        Args:
            runtime: The GridCodeRuntime instance
        """
        if not self._client:
            return

        tools = await self._client.list_tools()
        logger.info(f"Registering {len(tools)} tools from MCP server: {self.config.name}")

        for tool in tools:
            # Create a wrapper function for the MCP tool
            tool_func = self._create_tool_wrapper(tool)

            # Register with the runtime
            tool_name = f"mcp_{self.config.name}_{tool.name}"
            runtime.tool_registry.register_tool(
                name=tool_name,
                func=tool_func,
                description=tool.description,
                schema=tool.input_schema,
            )
            self._registered_tools.append(tool_name)
            logger.debug(f"Registered MCP tool: {tool_name}")

    async def _unregister_tools(self) -> None:
        """Unregister all MCP tools from the runtime."""
        if not self._runtime:
            return

        for tool_name in self._registered_tools:
            if self._runtime.tool_registry.has_tool(tool_name):
                self._runtime.tool_registry.unregister_tool(tool_name)
                logger.debug(f"Unregistered MCP tool: {tool_name}")

        self._registered_tools.clear()

    def _create_tool_wrapper(self, tool: MCPTool) -> Callable[..., Any]:
        """Create a wrapper function for an MCP tool.

        The wrapper function calls the MCP server to execute the tool.

        Args:
            tool: MCP tool definition

        Returns:
            Async function that calls the MCP tool
        """

        async def mcp_tool_wrapper(**kwargs: Any) -> dict[str, Any]:
            """Wrapper for MCP tool invocation."""
            if not self._client:
                raise RuntimeError("MCP client not connected")

            result = await self._client.call_tool(tool.name, kwargs)

            # Return structured content if available, otherwise text content
            if result.structured_content:
                return result.structured_content

            # Extract text from content
            for item in result.content:
                if item.get("type") == "text":
                    return {"result": item.get("text", "")}

            return {"content": result.content, "is_error": result.is_error}

        # Set function metadata
        mcp_tool_wrapper.__name__ = f"mcp_{tool.name}"
        mcp_tool_wrapper.__doc__ = tool.description

        return mcp_tool_wrapper

    async def list_tools(self) -> list[MCPTool]:
        """List available MCP tools.

        Returns:
            List of MCP tools
        """
        if not self._client:
            return []
        return await self._client.list_tools()

    async def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> Any:
        """Call an MCP tool directly.

        Args:
            name: Tool name (without prefix)
            arguments: Tool arguments

        Returns:
            Tool result
        """
        if not self._client:
            raise RuntimeError("MCP client not connected")
        return await self._client.call_tool(name, arguments)

    async def list_resources(self) -> list[Any]:
        """List available MCP resources.

        Returns:
            List of MCP resources
        """
        if not self._client:
            return []
        return await self._client.list_resources()

    async def read_resource(self, uri: str) -> str:
        """Read an MCP resource.

        Args:
            uri: Resource URI

        Returns:
            Resource content
        """
        if not self._client:
            raise RuntimeError("MCP client not connected")
        return await self._client.read_resource(uri)

    async def list_prompts(self) -> list[Any]:
        """List available MCP prompts.

        Returns:
            List of MCP prompts
        """
        if not self._client:
            return []
        return await self._client.list_prompts()

    async def get_prompt(
        self, name: str, arguments: dict[str, str] | None = None
    ) -> list[dict[str, Any]]:
        """Get an MCP prompt.

        Args:
            name: Prompt name
            arguments: Prompt arguments

        Returns:
            Prompt messages
        """
        if not self._client:
            raise RuntimeError("MCP client not connected")
        return await self._client.get_prompt(name, arguments)


class MultiMCPPlugin(Plugin):
    """Plugin for managing multiple MCP server connections.

    This plugin allows connecting to multiple MCP servers and managing
    them through a single interface.

    Example:
        configs = [
            MCPServerConfig(name="server1", command="uv", args=["run", "server1"]),
            MCPServerConfig(name="server2", url="http://localhost:8000/mcp"),
        ]
        plugin = MultiMCPPlugin(configs)
        await runtime.plugin_manager.load_plugin(plugin)
    """

    name: str = "multi-mcp"
    version: str = "1.0.0"
    description: str = "Multi-MCP server integration plugin"
    author: str = "GridCode"
    plugin_type: PluginType = PluginType.COMPOSITE
    provides: list[str] = ["mcp-integration", "mcp-tools", "multi-mcp"]

    def __init__(self, configs: list[MCPServerConfig], auto_connect: bool = True):
        """Initialize the multi-MCP plugin.

        Args:
            configs: List of MCP server configurations
            auto_connect: Whether to automatically connect on load
        """
        super().__init__()
        self.configs = configs
        self.auto_connect = auto_connect
        self._plugins: dict[str, MCPPlugin] = {}

    async def on_load(self, runtime: "GridCodeRuntime") -> None:
        """Load all MCP plugins.

        Args:
            runtime: The GridCodeRuntime instance
        """
        logger.info(f"Loading MultiMCPPlugin with {len(self.configs)} servers")

        for config in self.configs:
            plugin = MCPPlugin(config, auto_connect=self.auto_connect)
            try:
                await plugin.on_load(runtime)
                plugin._runtime = runtime
                self._plugins[config.name] = plugin
                logger.info(f"Loaded MCP server: {config.name}")
            except Exception as e:
                logger.error(f"Failed to load MCP server '{config.name}': {e}")

    async def on_unload(self) -> None:
        """Unload all MCP plugins."""
        logger.info("Unloading MultiMCPPlugin")

        for name, plugin in list(self._plugins.items()):
            try:
                await plugin.on_unload()
                logger.info(f"Unloaded MCP server: {name}")
            except Exception as e:
                logger.error(f"Failed to unload MCP server '{name}': {e}")

        self._plugins.clear()

    def get_plugin(self, name: str) -> MCPPlugin | None:
        """Get an MCP plugin by server name.

        Args:
            name: Server name

        Returns:
            MCPPlugin or None if not found
        """
        return self._plugins.get(name)

    @property
    def connected_servers(self) -> list[str]:
        """Get list of connected server names."""
        return [name for name, plugin in self._plugins.items() if plugin.is_connected]
