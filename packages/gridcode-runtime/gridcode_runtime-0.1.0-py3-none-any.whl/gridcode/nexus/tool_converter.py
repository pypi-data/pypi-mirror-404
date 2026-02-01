"""工具转换器 - 将 GridCode 工具转换为 LangGraph 工具格式

此模块提供将 GridCode 的 BaseTool 转换为 LangGraph 兼容的工具格式的功能。
使用 langchain_core.tools 的 @tool 装饰器创建 LangGraph 可用的工具。
"""

from collections.abc import Callable

from loguru import logger

from gridcode.tools.base import BaseTool


def convert_to_langgraph_tool(tool: BaseTool) -> Callable:
    """将 GridCode 工具转换为 LangGraph 工具格式

    Args:
        tool: GridCode BaseTool 实例

    Returns:
        LangGraph 兼容的工具函数
    """

    # 根据工具类型创建不同的包装函数
    if tool.name == "read":
        return _create_read_tool(tool)
    elif tool.name == "write":
        return _create_write_tool(tool)
    elif tool.name == "edit":
        return _create_edit_tool(tool)
    elif tool.name == "glob":
        return _create_glob_tool(tool)
    elif tool.name == "grep":
        return _create_grep_tool(tool)
    else:
        # 通用转换
        return _create_generic_tool(tool)


def _create_read_tool(tool: BaseTool) -> Callable:
    """创建 Read 工具的 LangGraph 版本"""
    from langchain_core.tools import tool as langgraph_tool

    @langgraph_tool
    async def read(
        file_path: str,
        offset: int = 0,
        limit: int | None = None,
    ) -> str:
        """Read file contents from the filesystem.

        Args:
            file_path: Path to the file to read
            offset: Line number to start reading from (default: 0)
            limit: Maximum number of lines to read (optional)

        Returns:
            File contents as string
        """
        result = await tool.execute(file_path=file_path, offset=offset, limit=limit)
        if result.success:
            return result.content
        else:
            return f"Error: {result.error}"

    return read


def _create_write_tool(tool: BaseTool) -> Callable:
    """创建 Write 工具的 LangGraph 版本"""
    from langchain_core.tools import tool as langgraph_tool

    @langgraph_tool
    async def write(
        file_path: str,
        content: str,
    ) -> str:
        """Write content to a file.

        Args:
            file_path: Path to the file to write
            content: Content to write to the file

        Returns:
            Success message or error
        """
        result = await tool.execute(file_path=file_path, content=content)
        if result.success:
            return f"Successfully wrote to {file_path}"
        else:
            return f"Error: {result.error}"

    return write


def _create_edit_tool(tool: BaseTool) -> Callable:
    """创建 Edit 工具的 LangGraph 版本"""
    from langchain_core.tools import tool as langgraph_tool

    @langgraph_tool
    async def edit(
        file_path: str,
        old_string: str,
        new_string: str,
        replace_all: bool = False,
    ) -> str:
        """Edit a file by replacing text.

        Args:
            file_path: Path to the file to edit
            old_string: Text to replace
            new_string: Replacement text
            replace_all: Whether to replace all occurrences (default: False)

        Returns:
            Success message or error
        """
        result = await tool.execute(
            file_path=file_path,
            old_string=old_string,
            new_string=new_string,
            replace_all=replace_all,
        )
        if result.success:
            return f"Successfully edited {file_path}"
        else:
            return f"Error: {result.error}"

    return edit


def _create_glob_tool(tool: BaseTool) -> Callable:
    """创建 Glob 工具的 LangGraph 版本"""
    from langchain_core.tools import tool as langgraph_tool

    @langgraph_tool
    async def glob(
        pattern: str,
        path: str = ".",
    ) -> str:
        """Find files matching a glob pattern.

        Args:
            pattern: Glob pattern to match (e.g., "**/*.py")
            path: Base directory to search in (default: current directory)

        Returns:
            List of matching file paths
        """
        result = await tool.execute(pattern=pattern, path=path)
        if result.success:
            return result.content
        else:
            return f"Error: {result.error}"

    return glob


def _create_grep_tool(tool: BaseTool) -> Callable:
    """创建 Grep 工具的 LangGraph 版本"""
    from langchain_core.tools import tool as langgraph_tool

    @langgraph_tool
    async def grep(
        pattern: str,
        path: str = ".",
        ignore_case: bool = False,
        context_lines: int = 0,
    ) -> str:
        """Search for text patterns in files.

        Args:
            pattern: Regular expression pattern to search for
            path: File or directory to search in (default: current directory)
            ignore_case: Whether to ignore case (default: False)
            context_lines: Number of context lines to show (default: 0)

        Returns:
            Matching lines with file paths and line numbers
        """
        result = await tool.execute(
            pattern=pattern,
            path=path,
            ignore_case=ignore_case,
            context_lines=context_lines,
        )
        if result.success:
            return result.content
        else:
            return f"Error: {result.error}"

    return grep


def _create_generic_tool(tool: BaseTool) -> Callable:
    """创建通用工具的 LangGraph 版本"""
    from langchain_core.tools import tool as langgraph_tool

    @langgraph_tool
    async def generic_tool(**kwargs) -> str:
        """Execute a generic tool.

        Args:
            **kwargs: Tool-specific parameters

        Returns:
            Tool execution result
        """
        result = await tool.execute(**kwargs)
        if result.success:
            return result.content
        else:
            return f"Error: {result.error}"

    # 设置工具名称和描述
    generic_tool.__name__ = tool.name
    generic_tool.__doc__ = tool.description

    return generic_tool


def convert_tools_to_langgraph(tools: list[BaseTool]) -> list[Callable]:
    """批量转换 GridCode 工具为 LangGraph 格式

    Args:
        tools: GridCode BaseTool 实例列表

    Returns:
        LangGraph 兼容的工具函数列表
    """
    converted = []
    for tool in tools:
        try:
            converted_tool = convert_to_langgraph_tool(tool)
            converted.append(converted_tool)
            logger.debug(f"Converted tool: {tool.name}")
        except Exception as e:
            logger.error(f"Failed to convert tool {tool.name}: {e}")

    logger.info(f"Converted {len(converted)} tools to LangGraph format")
    return converted
