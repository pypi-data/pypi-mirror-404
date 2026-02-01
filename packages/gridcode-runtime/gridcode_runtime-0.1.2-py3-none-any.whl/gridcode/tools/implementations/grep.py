"""Grep tool implementation for GridCode Runtime.

This tool searches for content in files using regex patterns.
"""

import re
from pathlib import Path
from typing import Any

from loguru import logger

from ..base import BaseTool, ToolResult


class GrepTool(BaseTool):
    """Tool for searching file contents with regex patterns.

    Searches for patterns in file contents using regular expressions.
    Supports case-insensitive search and context lines.

    Example:
        >>> tool = GrepTool()
        >>> result = await tool.execute(
        ...     pattern="def.*:",
        ...     path="/path/to/search"
        ... )
    """

    def __init__(self):
        """Initialize the Grep tool."""
        super().__init__(name="grep", description="Search file contents using regex patterns")

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the Grep tool.

        Args:
            pattern: Regex pattern to search for (required)
            path: File or directory to search in (optional, default: current directory)
            glob: Glob pattern to filter files (optional, e.g., "*.py")
            case_insensitive: Case-insensitive search (optional, default: False)
            context_lines: Number of context lines to show (optional, default: 0)
            max_results: Maximum number of results (optional, default: 100)

        Returns:
            ToolResult with search results

        Raises:
            ValueError: If pattern is not provided
        """
        pattern = kwargs.get("pattern")
        search_path = kwargs.get("path", ".")
        glob_pattern = kwargs.get("glob", "*")
        case_insensitive = kwargs.get("case_insensitive", False)
        context_lines = kwargs.get("context_lines", 0)
        max_results = kwargs.get("max_results", 100)

        if not pattern:
            return ToolResult(success=False, error="pattern parameter is required")

        try:
            # Compile regex pattern
            flags = re.IGNORECASE if case_insensitive else 0
            regex = re.compile(pattern, flags)

            base_path = Path(search_path)

            if not base_path.exists():
                return ToolResult(
                    success=False,
                    error=f"Search path does not exist: {search_path}",
                    metadata={"path": str(search_path)},
                )

            # Collect files to search
            if base_path.is_file():
                files = [base_path]
            else:
                files = list(base_path.rglob(glob_pattern))
                # Filter to only files
                files = [f for f in files if f.is_file()]

            # Search files
            results = []
            total_matches = 0

            for file_path in files:
                if total_matches >= max_results:
                    break

                try:
                    with open(file_path, encoding="utf-8") as f:
                        lines = f.readlines()

                    # Search for pattern
                    for line_num, line in enumerate(lines, start=1):
                        if total_matches >= max_results:
                            break

                        if regex.search(line):
                            # Format result with context
                            result_lines = [f"{file_path}:{line_num}:{line.rstrip()}"]

                            # Add context lines if requested
                            if context_lines > 0:
                                start = max(0, line_num - context_lines - 1)
                                end = min(len(lines), line_num + context_lines)

                                for ctx_num in range(start, line_num - 1):
                                    result_lines.insert(
                                        0, f"{file_path}:{ctx_num + 1}-{lines[ctx_num].rstrip()}"
                                    )

                                for ctx_num in range(line_num, end):
                                    result_lines.append(
                                        f"{file_path}:{ctx_num + 1}-{lines[ctx_num].rstrip()}"
                                    )

                            results.append("\\n".join(result_lines))
                            total_matches += 1

                except (UnicodeDecodeError, PermissionError):
                    # Skip files that can't be read
                    continue

            # Format output
            if results:
                content = "\\n\\n".join(results)
            else:
                content = "No matches found"

            truncated = total_matches >= max_results

            logger.debug(
                f"Grep search: pattern={pattern}, "
                f"path={search_path}, "
                f"matches={total_matches}, "
                f"truncated={truncated}"
            )

            return ToolResult(
                success=True,
                content=content,
                metadata={
                    "pattern": pattern,
                    "path": str(search_path),
                    "glob": glob_pattern,
                    "matches": total_matches,
                    "truncated": truncated,
                    "case_insensitive": case_insensitive,
                },
            )

        except re.error as e:
            logger.error(f"Invalid regex pattern: {e}")
            return ToolResult(
                success=False, error=f"Invalid regex pattern: {e}", metadata={"pattern": pattern}
            )

        except Exception as e:
            logger.error(f"Grep search failed: {e}")
            return ToolResult(
                success=False, error=str(e), metadata={"pattern": pattern, "path": str(search_path)}
            )
