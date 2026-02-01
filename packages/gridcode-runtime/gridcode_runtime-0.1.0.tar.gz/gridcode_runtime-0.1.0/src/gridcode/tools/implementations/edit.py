"""Edit tool implementation for GridCode Runtime.

This tool performs exact string replacements in files.
"""

from pathlib import Path
from typing import Any

from loguru import logger

from ..base import BaseTool, ToolResult


class EditTool(BaseTool):
    """Tool for editing file contents with exact string replacement.

    Performs exact string replacements in files.
    Supports replace_all mode for multiple replacements.

    Example:
        >>> tool = EditTool()
        >>> result = await tool.execute(
        ...     file_path="/path/to/file.txt",
        ...     old_string="old text",
        ...     new_string="new text"
        ... )
    """

    def __init__(self):
        """Initialize the Edit tool."""
        super().__init__(
            name="edit", description="Edit file contents with exact string replacement"
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the Edit tool.

        Args:
            file_path: Path to the file to edit (required)
            old_string: String to replace (required)
            new_string: Replacement string (required)
            replace_all: Replace all occurrences (optional, default: False)

        Returns:
            ToolResult indicating success or failure

        Raises:
            ValueError: If required parameters are missing
        """
        file_path = kwargs.get("file_path")
        old_string = kwargs.get("old_string")
        new_string = kwargs.get("new_string")
        replace_all = kwargs.get("replace_all", False)

        if not file_path:
            return ToolResult(success=False, error="file_path parameter is required")

        if old_string is None:
            return ToolResult(success=False, error="old_string parameter is required")

        if new_string is None:
            return ToolResult(success=False, error="new_string parameter is required")

        try:
            path = Path(file_path)

            if not path.exists():
                return ToolResult(
                    success=False,
                    error=f"File not found: {file_path}",
                    metadata={"file_path": str(file_path)},
                )

            # Read file contents
            with open(path, encoding="utf-8") as f:
                content = f.read()

            # Check if old_string exists
            if old_string not in content:
                return ToolResult(
                    success=False,
                    error=f"String not found in file: {old_string[:50]}...",
                    metadata={"file_path": str(file_path)},
                )

            # Count occurrences
            occurrences = content.count(old_string)

            # Check for ambiguity if not replace_all
            if not replace_all and occurrences > 1:
                return ToolResult(
                    success=False,
                    error=(
                        f"String appears {occurrences} times in file. "
                        "Use replace_all=True or provide more context."
                    ),
                    metadata={"file_path": str(file_path), "occurrences": occurrences},
                )

            # Perform replacement
            if replace_all:
                new_content = content.replace(old_string, new_string)
                replacements = occurrences
            else:
                # Replace only first occurrence
                new_content = content.replace(old_string, new_string, 1)
                replacements = 1

            # Write back to file
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_content)

            logger.info(
                f"Edited file: {file_path}, "
                f"replacements={replacements}, "
                f"replace_all={replace_all}"
            )

            return ToolResult(
                success=True,
                content=f"Successfully replaced {replacements} occurrence(s) in {file_path}",
                metadata={
                    "file_path": str(file_path),
                    "replacements": replacements,
                    "replace_all": replace_all,
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
            logger.error(f"Failed to edit file {file_path}: {e}")
            return ToolResult(success=False, error=str(e), metadata={"file_path": str(file_path)})
