"""MCP transport implementations for connecting to MCP servers.

Security Note: All subprocess operations use asyncio.create_subprocess_exec
which is safe from command injection as it does not invoke a shell.
"""

import asyncio
from abc import ABC, abstractmethod
from typing import Any


class Transport(ABC):
    """Abstract base class for MCP transports."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the MCP server."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to the MCP server."""
        pass

    @abstractmethod
    async def send(self, message: dict[str, Any]) -> None:
        """Send a message to the MCP server.

        Args:
            message: JSON-RPC message to send
        """
        pass

    @abstractmethod
    async def receive(self) -> dict[str, Any]:
        """Receive a message from the MCP server.

        Returns:
            JSON-RPC message received from server
        """
        pass


class StdioTransport(Transport):
    """Transport for communicating with MCP servers via stdin/stdout.

    This transport spawns a subprocess and communicates with it using
    JSON-RPC messages over standard input/output streams.

    Security: Uses asyncio.create_subprocess_exec (not shell) to prevent injection.
    """

    def __init__(self, command: str, args: list[str] | None = None):
        """Initialize stdio transport.

        Args:
            command: Command to execute (e.g., "python", "node", "npx")
            args: Arguments to pass to the command
        """
        self.command = command
        self.args = args or []
        self.process: asyncio.subprocess.Process | None = None
        self._connected = False

    async def connect(self) -> None:
        """Start the subprocess and establish connection."""
        if self._connected:
            return

        # Create subprocess with stdin/stdout pipes
        # Security: Uses exec (not shell) - safe from command injection
        self.process = await asyncio.create_subprocess_exec(
            self.command,
            *self.args,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        self._connected = True

    async def disconnect(self) -> None:
        """Terminate the subprocess."""
        if not self._connected or self.process is None:
            return

        # Close stdin to signal process to exit
        if self.process.stdin:
            self.process.stdin.close()
            await self.process.stdin.wait_closed()

        # Wait for process to exit (with timeout)
        try:
            await asyncio.wait_for(self.process.wait(), timeout=5.0)
        except TimeoutError:
            # Force kill if it doesn't exit gracefully
            self.process.kill()
            await self.process.wait()

        self._connected = False
        self.process = None

    async def send(self, message: dict[str, Any]) -> None:
        """Send a JSON-RPC message to the server.

        Args:
            message: JSON-RPC message to send

        Raises:
            RuntimeError: If not connected or stdin is unavailable
        """
        if not self._connected or self.process is None or self.process.stdin is None:
            raise RuntimeError("Transport not connected")

        import json

        # Encode message as JSON and send with newline delimiter
        message_bytes = (json.dumps(message) + "\n").encode("utf-8")
        self.process.stdin.write(message_bytes)
        await self.process.stdin.drain()

    async def receive(self) -> dict[str, Any]:
        """Receive a JSON-RPC message from the server.

        Returns:
            JSON-RPC message received from server

        Raises:
            RuntimeError: If not connected or stdout is unavailable
            EOFError: If connection is closed
        """
        if not self._connected or self.process is None or self.process.stdout is None:
            raise RuntimeError("Transport not connected")

        import json

        # Read line from stdout
        line = await self.process.stdout.readline()
        if not line:
            raise EOFError("Connection closed")

        # Decode and parse JSON
        return json.loads(line.decode("utf-8"))

    @property
    def connected(self) -> bool:
        """Check if transport is connected."""
        return self._connected


class SSETransport(Transport):
    """Transport for communicating with MCP servers via Server-Sent Events.

    This transport uses HTTP with SSE for server-to-client messages
    and regular HTTP POST for client-to-server messages.
    """

    def __init__(self, url: str):
        """Initialize SSE transport.

        Args:
            url: Base URL of the MCP server
        """
        self.url = url
        self._connected = False

    async def connect(self) -> None:
        """Establish SSE connection."""
        # TODO: Implement SSE connection
        # This would use aiohttp or similar to establish an SSE stream
        raise NotImplementedError("SSE transport not yet implemented")

    async def disconnect(self) -> None:
        """Close SSE connection."""
        raise NotImplementedError("SSE transport not yet implemented")

    async def send(self, message: dict[str, Any]) -> None:
        """Send message via HTTP POST."""
        raise NotImplementedError("SSE transport not yet implemented")

    async def receive(self) -> dict[str, Any]:
        """Receive message from SSE stream."""
        raise NotImplementedError("SSE transport not yet implemented")


class WebSocketTransport(Transport):
    """Transport for communicating with MCP servers via WebSocket.

    This transport uses WebSocket for bidirectional communication.
    """

    def __init__(self, url: str):
        """Initialize WebSocket transport.

        Args:
            url: WebSocket URL of the MCP server
        """
        self.url = url
        self._connected = False

    async def connect(self) -> None:
        """Establish WebSocket connection."""
        # TODO: Implement WebSocket connection
        # This would use aiohttp or websockets library
        raise NotImplementedError("WebSocket transport not yet implemented")

    async def disconnect(self) -> None:
        """Close WebSocket connection."""
        raise NotImplementedError("WebSocket transport not yet implemented")

    async def send(self, message: dict[str, Any]) -> None:
        """Send message via WebSocket."""
        raise NotImplementedError("WebSocket transport not yet implemented")

    async def receive(self) -> dict[str, Any]:
        """Receive message from WebSocket."""
        raise NotImplementedError("WebSocket transport not yet implemented")
