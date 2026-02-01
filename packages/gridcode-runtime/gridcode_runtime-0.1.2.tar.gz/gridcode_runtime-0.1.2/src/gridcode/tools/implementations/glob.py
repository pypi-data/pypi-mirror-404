"""Glob tool implementation for GridCode Runtime.

This tool performs file pattern matching using glob patterns.
"""

from pathlib import Path
from typing import Any

from loguru import logger

from ..base import BaseTool, ToolResult


class GlobTool(BaseTool):
    """Tool for file pattern matching.

    Searches for files matching glob patterns.
    Supports recursive patterns with ** syntax.

    Example:
        >>> tool = GlobTool()
        >>> result = await tool.execute(
        ...     pattern="**/*.py",
        ...     path="/path/to/search"
        ... )
    """

    def __init__(self):
        """Initialize the Glob tool."""
        super().__init__(name="glob", description="Search for files matching glob patterns")

    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the Glob tool.

        Args:
            pattern: Glob pattern to match (required)
            path: Directory to search in (optional, default: current directory)
            max_results: Maximum number of results to return (optional, default: 1000)

        Returns:
            ToolResult with list of matching file paths

        Raises:
            ValueError: If pattern is not provided
        """
        pattern = kwargs.get("pattern")
        search_path = kwargs.get("path", ".")
        max_results = kwargs.get("max_results", 1000)

        if not pattern:
            return ToolResult(success=False, error="pattern parameter is required")

        try:
            base_path = Path(search_path)

            if not base_path.exists():
                return ToolResult(
                    success=False,
                    error=f"Search path does not exist: {search_path}",
                    metadata={"path": str(search_path)},
                )

            # Perform glob search
            matches = list(base_path.glob(pattern))

            # Sort by modification time (most recent first)
            matches.sort(key=lambda p: p.stat().st_mtime, reverse=True)

            # Limit results
            truncated = len(matches) > max_results
            if truncated:
                matches = matches[:max_results]

            # Convert to strings
            match_paths = [str(p) for p in matches]

            # Format output
            if match_paths:
                content = "\\n".join(match_paths)
            else:
                content = "No files found matching pattern"

            logger.debug(
                f"Glob search: pattern={pattern}, "
                f"path={search_path}, "
                f"matches={len(match_paths)}, "
                f"truncated={truncated}"
            )

            return ToolResult(
                success=True,
                content=content,
                metadata={
                    "pattern": pattern,
                    "path": str(search_path),
                    "matches": len(match_paths),
                    "truncated": truncated,
                    "max_results": max_results,
                },
            )

        except Exception as e:
            logger.error(f"Glob search failed: {e}")
            return ToolResult(
                success=False, error=str(e), metadata={"pattern": pattern, "path": str(search_path)}
            )
