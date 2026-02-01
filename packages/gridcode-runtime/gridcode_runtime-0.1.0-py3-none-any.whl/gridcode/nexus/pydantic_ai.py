"""Pydantic-AI 框架适配器

将 Pydantic-AI 的 Agent 适配为统一的 Nexus 接口。
"""

from collections.abc import AsyncIterator
from typing import Any

from loguru import logger

from .base import BaseFrameworkAdapter
from .types import MessageRole, NexusAgentResult, NexusAgentState, NexusMessage


class PydanticAIAdapter(BaseFrameworkAdapter):
    """Pydantic-AI 框架适配器

    将 Pydantic-AI 的 Agent 适配为统一的 Nexus 接口。
    支持工具调用、结构化输出和流式执行。

    Attributes:
        model_name: 使用的模型名称
        instructions: Agent 系统指令
        output_type: 输出类型（默认为 str）
    """

    def __init__(
        self,
        model_name: str = "anthropic:claude-3-5-sonnet-20241022",
        instructions: str | None = None,
        output_type: type | None = None,
    ):
        """初始化 Pydantic-AI 适配器

        Args:
            model_name: 使用的模型名称，格式为 provider:model
            instructions: Agent 系统指令
            output_type: 输出类型（默认为 str）
        """
        self.model_name = model_name
        self.instructions = instructions
        self.output_type = output_type or str
        self._agent = None
        self._tools: list[Any] = []

    def _create_agent(self, tools: list[Any] | None = None):
        """创建 Pydantic-AI Agent

        Args:
            tools: 可选的工具列表

        Returns:
            Pydantic-AI Agent 实例
        """
        from pydantic_ai import Agent

        # 构建 Agent 参数
        agent_kwargs = {
            "model": self.model_name,
        }

        if self.instructions:
            agent_kwargs["instructions"] = self.instructions

        if self.output_type and self.output_type is not str:
            agent_kwargs["output_type"] = self.output_type

        # 创建 Agent
        agent = Agent(**agent_kwargs)

        # 注册工具
        if tools:
            for tool in tools:
                self._register_tool(agent, tool)

        return agent

    def _register_tool(self, agent: Any, tool: Any):
        """注册工具到 Agent

        Args:
            agent: Pydantic-AI Agent 实例
            tool: 工具定义（可以是 GridCode BaseTool 或函数）
        """
        from gridcode.tools.base import BaseTool

        if isinstance(tool, BaseTool):
            # 将 GridCode 工具转换为 Pydantic-AI 格式
            converted_tool = convert_to_pydantic_ai_tool(tool)
            agent.tool(converted_tool)
        elif callable(tool):
            # 直接注册函数工具
            agent.tool(tool)
        else:
            logger.warning(f"Unknown tool type: {type(tool)}")

    async def execute(
        self,
        prompt: str,
        state: NexusAgentState | None = None,
        tools: list[Any] | None = None,
        **kwargs: Any,
    ) -> NexusAgentResult:
        """执行 Pydantic-AI Agent

        Args:
            prompt: 用户输入
            state: 可选的初始状态
            tools: 可选的工具列表
            **kwargs: 额外参数（如 deps）

        Returns:
            NexusAgentResult: 执行结果
        """
        # 创建 Agent
        agent = self._create_agent(tools)

        # 构建消息历史
        message_history = None
        if state and state.messages:
            message_history = [self.to_framework_message(m) for m in state.messages]

        # 执行 Agent
        try:
            # 准备执行参数
            run_kwargs = {}
            if "deps" in kwargs:
                run_kwargs["deps"] = kwargs["deps"]
            if message_history:
                run_kwargs["message_history"] = message_history

            result = await agent.run(prompt, **run_kwargs)

            # 转换结果
            output = str(result.output) if result.output else ""

            # 构建消息历史
            messages = []
            if state and state.messages:
                messages.extend(state.messages)

            # 添加用户消息
            messages.append(NexusMessage(role=MessageRole.USER, content=prompt))

            # 添加助手响应
            messages.append(NexusMessage(role=MessageRole.ASSISTANT, content=output))

            # 获取 usage 信息
            usage = None
            if hasattr(result, "usage") and result.usage:
                usage = {
                    "input_tokens": getattr(result.usage, "input_tokens", 0),
                    "output_tokens": getattr(result.usage, "output_tokens", 0),
                }

            return NexusAgentResult(
                output=output,
                messages=messages,
                usage=usage,
                metadata={"framework": "pydantic-ai", "model": self.model_name},
            )

        except Exception as e:
            logger.error(f"Pydantic-AI execution failed: {e}")
            raise

    async def execute_stream(
        self,
        prompt: str,
        state: NexusAgentState | None = None,
        tools: list[Any] | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[NexusMessage | NexusAgentResult]:
        """流式执行 Pydantic-AI Agent

        Args:
            prompt: 用户输入
            state: 可选的初始状态
            tools: 可选的工具列表
            **kwargs: 额外参数

        Yields:
            NexusMessage 或 NexusAgentResult
        """
        # 创建 Agent
        agent = self._create_agent(tools)

        # 构建消息历史
        message_history = None
        if state and state.messages:
            message_history = [self.to_framework_message(m) for m in state.messages]

        # 准备执行参数
        run_kwargs = {}
        if "deps" in kwargs:
            run_kwargs["deps"] = kwargs["deps"]
        if message_history:
            run_kwargs["message_history"] = message_history

        # 流式执行
        all_messages = []

        # 添加用户消息
        user_msg = NexusMessage(role=MessageRole.USER, content=prompt)
        all_messages.append(user_msg)
        yield user_msg

        try:
            async with agent.run_stream(prompt, **run_kwargs) as run:
                accumulated_text = ""
                async for text_chunk in run.stream_text():
                    # 发送增量文本作为消息
                    delta_msg = NexusMessage(
                        role=MessageRole.ASSISTANT,
                        content=text_chunk,
                        metadata={"type": "delta"},
                    )
                    yield delta_msg
                    accumulated_text = text_chunk  # Pydantic-AI stream_text 返回累积文本

                # 获取最终结果
                result = await run.get_result()
                output = str(result.output) if result.output else accumulated_text

                # 添加最终助手消息
                final_msg = NexusMessage(role=MessageRole.ASSISTANT, content=output)
                all_messages.append(final_msg)

                # 获取 usage 信息
                usage = None
                if hasattr(result, "usage") and result.usage:
                    usage = {
                        "input_tokens": getattr(result.usage, "input_tokens", 0),
                        "output_tokens": getattr(result.usage, "output_tokens", 0),
                    }

                # 返回最终结果
                yield NexusAgentResult(
                    output=output,
                    messages=all_messages,
                    usage=usage,
                    metadata={"framework": "pydantic-ai", "model": self.model_name},
                )

        except Exception as e:
            logger.error(f"Pydantic-AI stream execution failed: {e}")
            raise

    def to_internal_message(self, msg: Any) -> NexusMessage:
        """将 Pydantic-AI 消息转换为内部格式

        Args:
            msg: Pydantic-AI 消息对象

        Returns:
            NexusMessage: 统一格式的消息
        """
        # Pydantic-AI 使用 ModelMessage 类型
        # 根据消息类型确定角色
        if hasattr(msg, "role"):
            role_str = str(msg.role).lower()
            if "user" in role_str:
                role = MessageRole.USER
            elif "assistant" in role_str or "model" in role_str:
                role = MessageRole.ASSISTANT
            elif "system" in role_str:
                role = MessageRole.SYSTEM
            elif "tool" in role_str:
                role = MessageRole.TOOL
            else:
                role = MessageRole.USER
        else:
            role = MessageRole.USER

        # 提取内容
        content = ""
        if hasattr(msg, "content"):
            content = str(msg.content) if msg.content else ""
        elif hasattr(msg, "parts"):
            # Pydantic-AI 消息可能包含多个 parts
            parts_content = []
            for part in msg.parts:
                if hasattr(part, "content"):
                    parts_content.append(str(part.content))
            content = "\n".join(parts_content)

        # 提取工具调用
        tool_calls = None
        if hasattr(msg, "parts"):
            tool_calls = []
            for part in msg.parts:
                if hasattr(part, "tool_name"):
                    tool_calls.append(
                        {
                            "id": getattr(part, "tool_call_id", ""),
                            "name": part.tool_name,
                            "args": getattr(part, "args", {}),
                        }
                    )
            if not tool_calls:
                tool_calls = None

        # 提取工具调用 ID
        tool_call_id = getattr(msg, "tool_call_id", None)
        if tool_call_id is not None and not isinstance(tool_call_id, str):
            tool_call_id = str(tool_call_id) if tool_call_id else None

        return NexusMessage(
            role=role,
            content=content,
            tool_calls=tool_calls,
            tool_call_id=tool_call_id,
        )

    def to_framework_message(self, msg: NexusMessage) -> Any:
        """将内部消息转换为 Pydantic-AI 格式

        Args:
            msg: 统一格式的消息

        Returns:
            Pydantic-AI 消息对象
        """
        from pydantic_ai.messages import (
            ModelRequest,
            ModelResponse,
            TextPart,
            UserPromptPart,
        )

        if msg.role == MessageRole.USER:
            return ModelRequest(parts=[UserPromptPart(content=msg.content)])
        elif msg.role == MessageRole.ASSISTANT:
            return ModelResponse(parts=[TextPart(content=msg.content)])
        elif msg.role == MessageRole.SYSTEM:
            # Pydantic-AI 使用 instructions 而不是 system message
            return ModelRequest(parts=[UserPromptPart(content=f"[System] {msg.content}")])
        elif msg.role == MessageRole.TOOL:
            # 工具消息需要特殊处理
            return ModelRequest(parts=[UserPromptPart(content=f"[Tool Result] {msg.content}")])
        else:
            return ModelRequest(parts=[UserPromptPart(content=msg.content)])


def convert_to_pydantic_ai_tool(tool: Any) -> Any:
    """将 GridCode 工具转换为 Pydantic-AI 工具格式

    Args:
        tool: GridCode BaseTool 实例

    Returns:
        Pydantic-AI 兼容的工具函数
    """

    from gridcode.tools.base import BaseTool

    if not isinstance(tool, BaseTool):
        raise ValueError(f"Expected BaseTool, got {type(tool)}")

    # 根据工具类型创建不同的包装函数
    if tool.name == "read":
        return _create_read_tool_pydantic(tool)
    elif tool.name == "write":
        return _create_write_tool_pydantic(tool)
    elif tool.name == "edit":
        return _create_edit_tool_pydantic(tool)
    elif tool.name == "glob":
        return _create_glob_tool_pydantic(tool)
    elif tool.name == "grep":
        return _create_grep_tool_pydantic(tool)
    else:
        return _create_generic_tool_pydantic(tool)


def _create_read_tool_pydantic(tool: Any):
    """创建 Read 工具的 Pydantic-AI 版本"""

    async def read(
        ctx: Any,
        file_path: str,
        offset: int = 0,
        limit: int | None = None,
    ) -> str:
        """Read file contents from the filesystem.

        Args:
            ctx: RunContext (unused but required by Pydantic-AI)
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

    read.__name__ = "read"
    return read


def _create_write_tool_pydantic(tool: Any):
    """创建 Write 工具的 Pydantic-AI 版本"""

    async def write(
        ctx: Any,
        file_path: str,
        content: str,
    ) -> str:
        """Write content to a file.

        Args:
            ctx: RunContext (unused but required by Pydantic-AI)
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

    write.__name__ = "write"
    return write


def _create_edit_tool_pydantic(tool: Any):
    """创建 Edit 工具的 Pydantic-AI 版本"""

    async def edit(
        ctx: Any,
        file_path: str,
        old_string: str,
        new_string: str,
        replace_all: bool = False,
    ) -> str:
        """Edit a file by replacing text.

        Args:
            ctx: RunContext (unused but required by Pydantic-AI)
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

    edit.__name__ = "edit"
    return edit


def _create_glob_tool_pydantic(tool: Any):
    """创建 Glob 工具的 Pydantic-AI 版本"""

    async def glob(
        ctx: Any,
        pattern: str,
        path: str = ".",
    ) -> str:
        """Find files matching a glob pattern.

        Args:
            ctx: RunContext (unused but required by Pydantic-AI)
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

    glob.__name__ = "glob"
    return glob


def _create_grep_tool_pydantic(tool: Any):
    """创建 Grep 工具的 Pydantic-AI 版本"""

    async def grep(
        ctx: Any,
        pattern: str,
        path: str = ".",
        ignore_case: bool = False,
        context_lines: int = 0,
    ) -> str:
        """Search for text patterns in files.

        Args:
            ctx: RunContext (unused but required by Pydantic-AI)
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

    grep.__name__ = "grep"
    return grep


def _create_generic_tool_pydantic(tool: Any):
    """创建通用工具的 Pydantic-AI 版本"""

    async def generic_tool(ctx: Any, **kwargs) -> str:
        """Execute a generic tool.

        Args:
            ctx: RunContext (unused but required by Pydantic-AI)
            **kwargs: Tool-specific parameters

        Returns:
            Tool execution result
        """
        result = await tool.execute(**kwargs)
        if result.success:
            return result.content
        else:
            return f"Error: {result.error}"

    generic_tool.__name__ = tool.name
    generic_tool.__doc__ = tool.description
    return generic_tool


def convert_tools_to_pydantic_ai(tools: list[Any]) -> list[Any]:
    """批量转换 GridCode 工具为 Pydantic-AI 格式

    Args:
        tools: GridCode BaseTool 实例列表

    Returns:
        Pydantic-AI 兼容的工具函数列表
    """
    converted = []
    for tool in tools:
        try:
            converted_tool = convert_to_pydantic_ai_tool(tool)
            converted.append(converted_tool)
            logger.debug(f"Converted tool to Pydantic-AI: {tool.name}")
        except Exception as e:
            logger.error(f"Failed to convert tool {tool.name}: {e}")

    logger.info(f"Converted {len(converted)} tools to Pydantic-AI format")
    return converted
