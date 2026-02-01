"""Base tool interface for GridCode Runtime.

This module defines the abstract base class for all tools in the system.
Tools are executable units that perform specific operations (file I/O, code analysis, etc.).
"""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    """Result of a tool execution.

    Attributes:
        success: Whether the tool execution succeeded
        content: The main content/output of the tool
        metadata: Additional metadata about the execution
        error: Error message if execution failed
    """

    success: bool
    content: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)
    error: str | None = None


class BaseTool(ABC):
    """Abstract base class for all tools.

    All tools must implement the execute method and provide
    name and description attributes.

    Attributes:
        name: Unique identifier for the tool
        description: Human-readable description of what the tool does
    """

    def __init__(self, name: str, description: str):
        """Initialize the tool.

        Args:
            name: Unique identifier for the tool
            description: Human-readable description
        """
        self.name = name
        self.description = description

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool with given parameters.

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            ToolResult: Result of the tool execution

        Raises:
            Exception: If tool execution fails
        """
        pass

    def to_dict(self) -> dict[str, Any]:
        """Convert tool to dictionary representation.

        Returns:
            Dictionary with tool name and description
        """
        return {
            "name": self.name,
            "description": self.description,
        }
