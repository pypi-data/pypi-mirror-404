"""MCP Client implementation for Model Context Protocol integration.

This module provides a high-level client for connecting to MCP servers
using various transports (stdio, HTTP) and interacting with tools,
resources, and prompts.

Based on the official MCP Python SDK:
https://github.com/modelcontextprotocol/python-sdk
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from loguru import logger
from pydantic import BaseModel, Field


class TransportType(str, Enum):
    """MCP transport type."""

    STDIO = "stdio"
    HTTP = "http"
    SSE = "sse"  # Legacy, now uses streamable HTTP


class MCPServerConfig(BaseModel):
    """Configuration for an MCP server connection.

    Attributes:
        name: Human-readable server name
        transport: Transport type (stdio or http)
        command: Command to run for stdio transport
        args: Arguments for the command
        env: Environment variables for the command
        url: URL for HTTP transport
        timeout: Connection timeout in seconds
    """

    name: str = Field(description="Human-readable server name")
    transport: TransportType = Field(default=TransportType.STDIO)
    command: str | None = Field(default=None, description="Command for stdio transport")
    args: list[str] = Field(default_factory=list, description="Command arguments")
    env: dict[str, str] = Field(default_factory=dict, description="Environment variables")
    url: str | None = Field(default=None, description="URL for HTTP transport")
    timeout: float = Field(default=30.0, description="Connection timeout in seconds")


@dataclass
class MCPTool:
    """Represents an MCP tool.

    Attributes:
        name: Tool name
        description: Tool description
        input_schema: JSON schema for tool input
    """

    name: str
    description: str
    input_schema: dict[str, Any] = field(default_factory=dict)


@dataclass
class MCPToolResult:
    """Result from an MCP tool call.

    Attributes:
        content: List of content items (text, images, etc.)
        structured_content: Structured JSON content if available
        is_error: Whether the tool call resulted in an error
    """

    content: list[dict[str, Any]] = field(default_factory=list)
    structured_content: dict[str, Any] | None = None
    is_error: bool = False


@dataclass
class MCPResource:
    """Represents an MCP resource.

    Attributes:
        uri: Resource URI
        name: Resource name
        description: Resource description
        mime_type: MIME type of the resource content
    """

    uri: str
    name: str
    description: str = ""
    mime_type: str = "text/plain"


@dataclass
class MCPPrompt:
    """Represents an MCP prompt.

    Attributes:
        name: Prompt name
        description: Prompt description
        arguments: List of prompt arguments
    """

    name: str
    description: str = ""
    arguments: list[dict[str, Any]] = field(default_factory=list)


class MCPTransport(ABC):
    """Abstract base class for MCP transports."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the MCP server."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close the connection to the MCP server."""
        pass

    @abstractmethod
    async def is_connected(self) -> bool:
        """Check if the transport is connected."""
        pass

    @abstractmethod
    def get_session(self) -> Any:
        """Get the underlying ClientSession."""
        pass


class StdioTransport(MCPTransport):
    """Stdio transport for MCP communication.

    Uses subprocess stdin/stdout for communication with local MCP servers.
    """

    def __init__(self, config: MCPServerConfig):
        """Initialize stdio transport.

        Args:
            config: Server configuration
        """
        self.config = config
        self._session: Any = None
        self._read_stream: Any = None
        self._write_stream: Any = None
        self._context_manager: Any = None
        self._session_context: Any = None

    async def connect(self) -> None:
        """Connect to the MCP server via stdio."""
        try:
            from mcp import ClientSession
            from mcp.client.stdio import StdioServerParameters, stdio_client
        except ImportError as e:
            raise ImportError("MCP SDK not installed. Install with: pip install mcp") from e

        if not self.config.command:
            raise ValueError("Command is required for stdio transport")

        server_params = StdioServerParameters(
            command=self.config.command,
            args=self.config.args,
            env=self.config.env if self.config.env else None,
        )

        logger.debug(
            f"Connecting to MCP server via stdio: "
            f"{self.config.command} {' '.join(self.config.args)}"
        )

        # Enter the stdio_client context
        self._context_manager = stdio_client(server_params)
        self._read_stream, self._write_stream = await self._context_manager.__aenter__()

        # Create and initialize session
        self._session_context = ClientSession(self._read_stream, self._write_stream)
        self._session = await self._session_context.__aenter__()
        await self._session.initialize()

        logger.info(f"Connected to MCP server: {self.config.name}")

    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        if self._session_context:
            try:
                await self._session_context.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"Error closing session: {e}")
            self._session_context = None
            self._session = None

        if self._context_manager:
            try:
                await self._context_manager.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"Error closing transport: {e}")
            self._context_manager = None
            self._read_stream = None
            self._write_stream = None

        logger.info(f"Disconnected from MCP server: {self.config.name}")

    async def is_connected(self) -> bool:
        """Check if connected."""
        return self._session is not None

    def get_session(self) -> Any:
        """Get the ClientSession."""
        return self._session


class HTTPTransport(MCPTransport):
    """HTTP transport for MCP communication.

    Uses streamable HTTP for communication with remote MCP servers.
    """

    def __init__(self, config: MCPServerConfig):
        """Initialize HTTP transport.

        Args:
            config: Server configuration
        """
        self.config = config
        self._session: Any = None
        self._context_manager: Any = None
        self._session_context: Any = None

    async def connect(self) -> None:
        """Connect to the MCP server via HTTP."""
        try:
            from mcp import ClientSession
            from mcp.client.streamable_http import streamablehttp_client
        except ImportError as e:
            raise ImportError("MCP SDK not installed. Install with: pip install mcp") from e

        if not self.config.url:
            raise ValueError("URL is required for HTTP transport")

        logger.debug(f"Connecting to MCP server via HTTP: {self.config.url}")

        # Enter the HTTP client context
        self._context_manager = streamablehttp_client(self.config.url)
        read_stream, write_stream, _ = await self._context_manager.__aenter__()

        # Create and initialize session
        self._session_context = ClientSession(read_stream, write_stream)
        self._session = await self._session_context.__aenter__()
        await self._session.initialize()

        logger.info(f"Connected to MCP server: {self.config.name}")

    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        if self._session_context:
            try:
                await self._session_context.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"Error closing session: {e}")
            self._session_context = None
            self._session = None

        if self._context_manager:
            try:
                await self._context_manager.__aexit__(None, None, None)
            except Exception as e:
                logger.warning(f"Error closing transport: {e}")
            self._context_manager = None

        logger.info(f"Disconnected from MCP server: {self.config.name}")

    async def is_connected(self) -> bool:
        """Check if connected."""
        return self._session is not None

    def get_session(self) -> Any:
        """Get the ClientSession."""
        return self._session


class MCPClient:
    """High-level MCP client for interacting with MCP servers.

    Provides a unified interface for connecting to MCP servers,
    discovering tools/resources/prompts, and invoking them.

    Example:
        config = MCPServerConfig(
            name="my-server",
            command="python",
            args=["my_server.py"],
        )

        async with MCPClient(config) as client:
            # List tools
            tools = await client.list_tools()
            for tool in tools:
                print(f"Tool: {tool.name} - {tool.description}")

            # Call a tool
            result = await client.call_tool("my_tool", {"arg": "value"})
            print(f"Result: {result.content}")

            # List resources
            resources = await client.list_resources()
            for resource in resources:
                print(f"Resource: {resource.uri}")

            # Read a resource
            content = await client.read_resource("config://settings")
            print(f"Content: {content}")
    """

    def __init__(self, config: MCPServerConfig):
        """Initialize the MCP client.

        Args:
            config: Server configuration
        """
        self.config = config
        self._transport: MCPTransport | None = None
        self._tools: list[MCPTool] = []
        self._resources: list[MCPResource] = []
        self._prompts: list[MCPPrompt] = []

    def _create_transport(self) -> MCPTransport:
        """Create the appropriate transport based on config."""
        if self.config.transport == TransportType.STDIO:
            return StdioTransport(self.config)
        elif self.config.transport in (TransportType.HTTP, TransportType.SSE):
            return HTTPTransport(self.config)
        else:
            raise ValueError(f"Unsupported transport type: {self.config.transport}")

    async def connect(self) -> None:
        """Connect to the MCP server."""
        if self._transport and await self._transport.is_connected():
            logger.warning("Already connected to MCP server")
            return

        self._transport = self._create_transport()
        await self._transport.connect()

        # Discover available tools, resources, and prompts
        await self._discover_capabilities()

    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        if self._transport:
            await self._transport.disconnect()
            self._transport = None
            self._tools = []
            self._resources = []
            self._prompts = []

    async def __aenter__(self) -> "MCPClient":
        """Async context manager entry."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit."""
        await self.disconnect()

    @property
    def is_connected(self) -> bool:
        """Check if connected to the MCP server."""
        return self._transport is not None

    def _get_session(self) -> Any:
        """Get the underlying session, raising if not connected."""
        if not self._transport:
            raise RuntimeError("Not connected to MCP server")
        session = self._transport.get_session()
        if not session:
            raise RuntimeError("Session not initialized")
        return session

    async def _discover_capabilities(self) -> None:
        """Discover available tools, resources, and prompts."""
        session = self._get_session()

        # Discover tools
        try:
            tools_result = await session.list_tools()
            self._tools = [
                MCPTool(
                    name=t.name,
                    description=t.description or "",
                    input_schema=t.inputSchema if hasattr(t, "inputSchema") else {},
                )
                for t in tools_result.tools
            ]
            logger.debug(f"Discovered {len(self._tools)} tools")
        except Exception as e:
            logger.warning(f"Failed to list tools: {e}")
            self._tools = []

        # Discover resources
        try:
            resources_result = await session.list_resources()
            self._resources = [
                MCPResource(
                    uri=str(r.uri),
                    name=r.name or str(r.uri),
                    description=r.description or "",
                    mime_type=r.mimeType or "text/plain",
                )
                for r in resources_result.resources
            ]
            logger.debug(f"Discovered {len(self._resources)} resources")
        except Exception as e:
            logger.warning(f"Failed to list resources: {e}")
            self._resources = []

        # Discover prompts
        try:
            prompts_result = await session.list_prompts()
            self._prompts = [
                MCPPrompt(
                    name=p.name,
                    description=p.description or "",
                    arguments=[
                        {"name": a.name, "description": a.description or "", "required": a.required}
                        for a in (p.arguments or [])
                    ],
                )
                for p in prompts_result.prompts
            ]
            logger.debug(f"Discovered {len(self._prompts)} prompts")
        except Exception as e:
            logger.warning(f"Failed to list prompts: {e}")
            self._prompts = []

    async def list_tools(self) -> list[MCPTool]:
        """List available tools.

        Returns:
            List of available tools
        """
        return self._tools.copy()

    async def call_tool(self, name: str, arguments: dict[str, Any] | None = None) -> MCPToolResult:
        """Call an MCP tool.

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Tool result

        Raises:
            RuntimeError: If not connected
            ValueError: If tool not found
        """
        session = self._get_session()

        # Check if tool exists
        tool_names = [t.name for t in self._tools]
        if name not in tool_names:
            raise ValueError(f"Tool not found: {name}. Available tools: {tool_names}")

        logger.debug(f"Calling tool: {name} with arguments: {arguments}")

        try:
            from mcp import types
        except ImportError:
            types = None

        result = await session.call_tool(name, arguments=arguments or {})

        # Parse result content
        content_list: list[dict[str, Any]] = []
        for item in result.content:
            if types and isinstance(item, types.TextContent):
                content_list.append({"type": "text", "text": item.text})
            elif types and isinstance(item, types.ImageContent):
                content_list.append(
                    {
                        "type": "image",
                        "mime_type": item.mimeType,
                        "data": item.data,
                    }
                )
            elif types and isinstance(item, types.EmbeddedResource):
                content_list.append(
                    {
                        "type": "resource",
                        "uri": str(item.resource.uri) if hasattr(item.resource, "uri") else "",
                        "content": item.resource.text if hasattr(item.resource, "text") else "",
                    }
                )
            else:
                # Fallback for unknown types
                content_list.append({"type": "unknown", "data": str(item)})

        return MCPToolResult(
            content=content_list,
            structured_content=(
                result.structuredContent if hasattr(result, "structuredContent") else None
            ),
            is_error=result.isError if hasattr(result, "isError") else False,
        )

    async def list_resources(self) -> list[MCPResource]:
        """List available resources.

        Returns:
            List of available resources
        """
        return self._resources.copy()

    async def read_resource(self, uri: str) -> str:
        """Read a resource by URI.

        Args:
            uri: Resource URI

        Returns:
            Resource content as text

        Raises:
            RuntimeError: If not connected
            ValueError: If resource not found
        """
        session = self._get_session()

        try:
            from mcp import types
            from pydantic import AnyUrl
        except ImportError:
            raise ImportError("MCP SDK not installed")

        logger.debug(f"Reading resource: {uri}")

        result = await session.read_resource(AnyUrl(uri))

        # Extract text content
        for content in result.contents:
            if isinstance(content, types.TextContent):
                return content.text
            elif hasattr(content, "text"):
                return content.text

        return ""

    async def list_prompts(self) -> list[MCPPrompt]:
        """List available prompts.

        Returns:
            List of available prompts
        """
        return self._prompts.copy()

    async def get_prompt(
        self, name: str, arguments: dict[str, str] | None = None
    ) -> list[dict[str, Any]]:
        """Get a prompt by name.

        Args:
            name: Prompt name
            arguments: Prompt arguments

        Returns:
            List of prompt messages

        Raises:
            RuntimeError: If not connected
            ValueError: If prompt not found
        """
        session = self._get_session()

        # Check if prompt exists
        prompt_names = [p.name for p in self._prompts]
        if name not in prompt_names:
            raise ValueError(f"Prompt not found: {name}. Available prompts: {prompt_names}")

        logger.debug(f"Getting prompt: {name} with arguments: {arguments}")

        result = await session.get_prompt(name, arguments=arguments or {})

        # Parse prompt messages
        messages: list[dict[str, Any]] = []
        for msg in result.messages:
            messages.append(
                {
                    "role": msg.role,
                    "content": (
                        msg.content.text if hasattr(msg.content, "text") else str(msg.content)
                    ),
                }
            )

        return messages


@asynccontextmanager
async def create_mcp_client(config: MCPServerConfig) -> AsyncIterator[MCPClient]:
    """Create an MCP client as an async context manager.

    Args:
        config: Server configuration

    Yields:
        Connected MCPClient instance

    Example:
        async with create_mcp_client(config) as client:
            tools = await client.list_tools()
    """
    client = MCPClient(config)
    try:
        await client.connect()
        yield client
    finally:
        await client.disconnect()
