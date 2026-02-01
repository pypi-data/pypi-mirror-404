"""Read tool implementation for GridCode Runtime.

This tool reads file contents from the filesystem.
"""

from pathlib import Path
from typing import Any

from loguru import logger

from ..base import BaseTool, ToolResult


class ReadTool(BaseTool):
    """Tool for reading file contents.

    Reads files from the filesystem and returns their contents.
    Supports line-based reading with offset and limit parameters.

    Example:
        >>> tool = ReadTool()
        >>> result = await tool.execute(file_path="/path/to/file.txt")
        >>> print(result.content)
    """

    def __init__(self):
        """Initialize the Read tool."""
        super().__init__(name="read", description="Read file contents from the filesystem")

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the Read tool.

        Args:
            file_path: Path to the file to read (required)
            offset: Line number to start reading from (optional, default: 0)
            limit: Maximum number of lines to read (optional, default: None)

        Returns:
            ToolResult with file contents

        Raises:
            ValueError: If file_path is not provided
            FileNotFoundError: If file does not exist
        """
        file_path = kwargs.get("file_path")
        if not file_path:
            return ToolResult(success=False, error="file_path parameter is required")

        offset = kwargs.get("offset", 0)
        limit = kwargs.get("limit")

        try:
            path = Path(file_path)

            if not path.exists():
                return ToolResult(
                    success=False,
                    error=f"File not found: {file_path}",
                    metadata={"file_path": str(file_path)},
                )

            if not path.is_file():
                return ToolResult(
                    success=False,
                    error=f"Path is not a file: {file_path}",
                    metadata={"file_path": str(file_path)},
                )

            # Read file contents
            with open(path, encoding="utf-8") as f:
                lines = f.readlines()

            total_lines = len(lines)

            # Apply offset and limit
            if offset > 0:
                lines = lines[offset:]

            truncated = False
            if limit and len(lines) > limit:
                lines = lines[:limit]
                truncated = True

            content = "".join(lines)

            logger.debug(
                f"Read file: {file_path}, "
                f"total_lines={total_lines}, "
                f"offset={offset}, "
                f"limit={limit}, "
                f"truncated={truncated}"
            )

            return ToolResult(
                success=True,
                content=content,
                metadata={
                    "file_path": str(file_path),
                    "total_lines": total_lines,
                    "lines_read": len(lines),
                    "truncated": truncated,
                    "offset": offset,
                },
            )

        except UnicodeDecodeError as e:
            logger.error(f"Failed to decode file {file_path}: {e}")
            return ToolResult(
                success=False,
                error=f"Failed to decode file (not UTF-8): {e}",
                metadata={"file_path": str(file_path)},
            )

        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return ToolResult(success=False, error=str(e), metadata={"file_path": str(file_path)})
