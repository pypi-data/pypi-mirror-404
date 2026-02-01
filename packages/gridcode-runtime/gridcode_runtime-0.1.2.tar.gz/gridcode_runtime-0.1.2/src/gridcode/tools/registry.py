"""Tool Registry for GridCode Runtime.

This module provides a centralized registry for managing and executing tools.
It integrates with ToolResultEnhancer to automatically enhance tool results.
"""

from typing import Any

from loguru import logger

from ..prompts.tool_result_enhancer import (
    EnhancedToolResult,
)
from ..prompts.tool_result_enhancer import ToolResult as EnhancerToolResult
from ..prompts.tool_result_enhancer import (
    ToolResultEnhancer,
    ToolType,
)
from .base import BaseTool


class ToolRegistry:
    """Central registry for tool management and execution.

    The ToolRegistry manages tool registration, lookup, and execution.
    It automatically enhances tool results using ToolResultEnhancer.

    Example:
        >>> registry = ToolRegistry()
        >>> registry.register_tool(ReadTool())
        >>> result = await registry.execute_tool("read", file_path="/path/to/file")
    """

    def __init__(self, result_enhancer: ToolResultEnhancer | None = None):
        """Initialize the tool registry.

        Args:
            result_enhancer: Optional ToolResultEnhancer instance.
                           If not provided, a new one will be created.
        """
        self._tools: dict[str, BaseTool] = {}
        self._result_enhancer = result_enhancer or ToolResultEnhancer()
        logger.info("ToolRegistry initialized")

    def register_tool(self, tool: BaseTool) -> None:
        """Register a tool in the registry.

        Args:
            tool: Tool instance to register

        Raises:
            ValueError: If a tool with the same name is already registered
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")

        self._tools[tool.name] = tool
        logger.info(f"Registered tool: {tool.name}")

    def get_tool(self, name: str) -> BaseTool | None:
        """Get a tool by name.

        Args:
            name: Name of the tool to retrieve

        Returns:
            Tool instance if found, None otherwise
        """
        return self._tools.get(name)

    def unregister_tool(self, name: str) -> bool:
        """Unregister a tool from the registry.

        Args:
            name: Name of the tool to unregister

        Returns:
            True if tool was unregistered, False if not found
        """
        if name not in self._tools:
            logger.warning(f"Tool '{name}' not found in registry")
            return False

        del self._tools[name]
        logger.info(f"Unregistered tool: {name}")
        return True

    def has_tool(self, name: str) -> bool:
        """Check if a tool is registered.

        Args:
            name: Name of the tool to check

        Returns:
            True if tool is registered
        """
        return name in self._tools

    def list_tools(self) -> list[dict[str, Any]]:
        """List all registered tools.

        Returns:
            List of tool dictionaries with name and description
        """
        return [tool.to_dict() for tool in self._tools.values()]

    async def execute_tool(
        self,
        name: str,
        context: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> EnhancedToolResult:
        """Execute a tool and enhance its result.

        Args:
            name: Name of the tool to execute
            context: Optional execution context for result enhancement
            **kwargs: Tool-specific parameters

        Returns:
            EnhancedToolResult: Enhanced tool execution result

        Raises:
            ValueError: If tool is not found
            Exception: If tool execution fails
        """
        tool = self.get_tool(name)
        if tool is None:
            raise ValueError(f"Tool '{name}' not found in registry")

        logger.debug(f"Executing tool: {name} with kwargs: {kwargs}")

        try:
            # Execute the tool
            result = await tool.execute(**kwargs)

            # Convert to enhancer format
            tool_type = self._map_tool_type(name)
            enhancer_result = EnhancerToolResult(
                tool_type=tool_type,
                success=result.success,
                content=result.content,
                metadata=result.metadata,
                error=result.error,
            )

            # Enhance the result
            enhanced = self._result_enhancer.enhance(enhancer_result, context)

            logger.debug(
                f"Tool '{name}' executed successfully, "
                f"injected {len(enhanced.injected_reminders)} reminders"
            )

            return enhanced

        except Exception as e:
            logger.error(f"Tool '{name}' execution failed: {e}")
            # Create error result
            error_result = EnhancerToolResult(
                tool_type=self._map_tool_type(name),
                success=False,
                content="",
                metadata=kwargs,
                error=str(e),
            )
            # Enhance error result
            return self._result_enhancer.enhance(error_result, context)

    def _map_tool_type(self, tool_name: str) -> ToolType:
        """Map tool name to ToolType enum.

        Args:
            tool_name: Name of the tool

        Returns:
            Corresponding ToolType enum value
        """
        tool_type_map = {
            "read": ToolType.READ,
            "write": ToolType.WRITE,
            "edit": ToolType.EDIT,
            "glob": ToolType.GLOB,
            "grep": ToolType.GREP,
            "bash": ToolType.BASH,
            "task": ToolType.TASK,
        }
        return tool_type_map.get(tool_name.lower(), ToolType.READ)
