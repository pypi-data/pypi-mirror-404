"""Write tool implementation for GridCode Runtime.

This tool writes content to files on the filesystem.
"""

from pathlib import Path
from typing import Any

from loguru import logger

from ..base import BaseTool, ToolResult


class WriteTool(BaseTool):
    """Tool for writing file contents.

    Writes content to files on the filesystem.
    Creates parent directories if they don't exist.

    Example:
        >>> tool = WriteTool()
        >>> result = await tool.execute(
        ...     file_path="/path/to/file.txt",
        ...     content="Hello, World!"
        ... )
    """

    def __init__(self):
        """Initialize the Write tool."""
        super().__init__(name="write", description="Write content to a file on the filesystem")

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the Write tool.

        Args:
            file_path: Path to the file to write (required)
            content: Content to write to the file (required)
            create_dirs: Whether to create parent directories (optional, default: True)

        Returns:
            ToolResult indicating success or failure

        Raises:
            ValueError: If required parameters are missing
        """
        file_path = kwargs.get("file_path")
        content = kwargs.get("content")
        create_dirs = kwargs.get("create_dirs", True)

        if not file_path:
            return ToolResult(success=False, error="file_path parameter is required")

        if content is None:
            return ToolResult(success=False, error="content parameter is required")

        try:
            path = Path(file_path)

            # Create parent directories if needed
            if create_dirs and not path.parent.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Created parent directories for: {file_path}")

            # Write content to file
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info(f"Wrote {len(content)} characters to: {file_path}")

            return ToolResult(
                success=True,
                content=f"Successfully wrote to {file_path}",
                metadata={
                    "file_path": str(file_path),
                    "bytes_written": len(content.encode("utf-8")),
                    "chars_written": len(content),
                },
            )

        except PermissionError as e:
            logger.error(f"Permission denied writing to {file_path}: {e}")
            return ToolResult(
                success=False,
                error=f"Permission denied: {e}",
                metadata={"file_path": str(file_path)},
            )

        except Exception as e:
            logger.error(f"Failed to write file {file_path}: {e}")
            return ToolResult(success=False, error=str(e), metadata={"file_path": str(file_path)})
