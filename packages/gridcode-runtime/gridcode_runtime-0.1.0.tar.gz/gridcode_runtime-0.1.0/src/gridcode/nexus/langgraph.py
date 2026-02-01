"""LangGraph 框架适配器

将 LangGraph 的 StateGraph 适配为统一的 Nexus 接口。
"""

from collections.abc import AsyncIterator
from typing import Any

from .base import BaseFrameworkAdapter
from .types import MessageRole, NexusAgentResult, NexusAgentState, NexusMessage


class LangGraphAdapter(BaseFrameworkAdapter):
    """LangGraph 框架适配器

    将 LangGraph 的 StateGraph 适配为统一的 Nexus 接口。
    支持工具调用、消息历史和流式执行。

    Attributes:
        api_key: API密钥
        api_provider: API提供商 ("openai" 或 "anthropic")
        model_name: 使用的模型名称
        _compiled_graph: 编译后的 StateGraph（缓存）
    """

    def __init__(
        self,
        api_key: str,
        api_provider: str = "openai",
        model_name: str | None = None,
    ):
        """初始化 LangGraph 适配器

        Args:
            api_key: API密钥 (OpenAI 或 Anthropic)
            api_provider: API提供商 ("openai" 或 "anthropic")
            model_name: 使用的模型名称。如果为None，则根据provider使用默认值。
        """
        self.api_key = api_key
        self.api_provider = api_provider

        # Set default model based on provider
        if model_name is None:
            if api_provider == "anthropic":
                self.model_name = "claude-3-5-sonnet-20241022"
            else:
                self.model_name = "gpt-3.5-turbo"
        else:
            self.model_name = model_name

        self._compiled_graph = None

    def _build_graph(self, tools: list[Any] | None = None):
        """构建 LangGraph StateGraph

        Args:
            tools: 可选的工具列表

        Returns:
            编译后的 StateGraph
        """
        from langgraph.graph import END, START, MessagesState, StateGraph
        from langgraph.prebuilt import ToolNode

        def call_model(state: MessagesState):
            """调用模型节点"""
            # Select appropriate LangChain model based on provider
            if self.api_provider == "anthropic":
                from langchain_anthropic import ChatAnthropic

                model = ChatAnthropic(
                    model=self.model_name,
                    api_key=self.api_key,
                )
            else:  # openai
                from langchain_openai import ChatOpenAI

                model = ChatOpenAI(
                    model=self.model_name,
                    api_key=self.api_key,
                )

            if tools:
                model = model.bind_tools(tools)

            response = model.invoke(state["messages"])
            return {"messages": [response]}

        def should_continue(state: MessagesState):
            """判断是否继续执行工具"""
            last_message = state["messages"][-1]
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                return "tools"
            return END

        # 构建图
        builder = StateGraph(MessagesState)
        builder.add_node("call_model", call_model)

        if tools:
            tool_node = ToolNode(tools)
            builder.add_node("tools", tool_node)
            builder.add_edge(START, "call_model")
            builder.add_conditional_edges("call_model", should_continue, ["tools", END])
            builder.add_edge("tools", "call_model")
        else:
            builder.add_edge(START, "call_model")
            builder.add_edge("call_model", END)

        return builder.compile()

    async def execute(
        self,
        prompt: str,
        state: NexusAgentState | None = None,
        tools: list[Any] | None = None,
        **kwargs: Any,
    ) -> NexusAgentResult:
        """执行 LangGraph Agent

        Args:
            prompt: 用户输入
            state: 可选的初始状态
            tools: 可选的工具列表
            **kwargs: 额外参数

        Returns:
            NexusAgentResult: 执行结果
        """
        # 构建图（如果还没有编译或工具列表变化）
        if self._compiled_graph is None or tools is not None:
            self._compiled_graph = self._build_graph(tools)

        # 构建初始状态
        initial_state = {"messages": []}

        if state and state.messages:
            initial_state["messages"] = [self.to_framework_message(m) for m in state.messages]

        # 添加用户输入
        from langchain_core.messages import HumanMessage

        initial_state["messages"].append(HumanMessage(content=prompt))

        # 执行图
        result = await self._compiled_graph.ainvoke(initial_state)

        # 转换结果
        messages = [self.to_internal_message(m) for m in result["messages"]]
        final_output = messages[-1].content if messages else ""

        # Extract token usage from the last AIMessage
        usage = self._extract_usage(result["messages"])

        return NexusAgentResult(
            output=final_output,
            messages=messages,
            usage=usage,
            metadata={"framework": "langgraph"},
        )

    async def execute_stream(
        self,
        prompt: str,
        state: NexusAgentState | None = None,
        tools: list[Any] | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[NexusMessage | NexusAgentResult]:
        """流式执行 LangGraph Agent

        Args:
            prompt: 用户输入
            state: 可选的初始状态
            tools: 可选的工具列表
            **kwargs: 额外参数

        Yields:
            NexusMessage 或 NexusAgentResult
        """
        # 构建图
        if self._compiled_graph is None or tools is not None:
            self._compiled_graph = self._build_graph(tools)

        # 构建初始状态
        initial_state = {"messages": []}

        if state and state.messages:
            initial_state["messages"] = [self.to_framework_message(m) for m in state.messages]

        # 添加用户输入
        from langchain_core.messages import HumanMessage

        initial_state["messages"].append(HumanMessage(content=prompt))

        # 流式执行
        all_messages = []
        async for chunk in self._compiled_graph.astream(initial_state):
            if "messages" in chunk:
                for msg in chunk["messages"]:
                    internal_msg = self.to_internal_message(msg)
                    all_messages.append(internal_msg)
                    yield internal_msg

        # 返回最终结果
        yield NexusAgentResult(
            output=all_messages[-1].content if all_messages else "",
            messages=all_messages,
            metadata={"framework": "langgraph"},
        )

    def _extract_usage(self, messages: list[Any]) -> dict[str, int] | None:
        """从消息列表中提取 token 使用统计

        遍历所有 AIMessage，累加 usage_metadata 中的 token 统计。

        Args:
            messages: LangGraph 消息列表

        Returns:
            Token 使用统计字典，包含 input_tokens, output_tokens, total_tokens
            如果没有 usage 信息则返回 None
        """
        from langchain_core.messages import AIMessage

        total_input = 0
        total_output = 0

        for msg in messages:
            if isinstance(msg, AIMessage) and hasattr(msg, "usage_metadata") and msg.usage_metadata:
                usage = msg.usage_metadata
                # usage_metadata is a dict with input_tokens, output_tokens, total_tokens
                total_input += usage.get("input_tokens", 0)
                total_output += usage.get("output_tokens", 0)

        if total_input == 0 and total_output == 0:
            return None

        return {
            "input_tokens": total_input,
            "output_tokens": total_output,
            "total_tokens": total_input + total_output,
        }

    def to_internal_message(self, msg: Any) -> NexusMessage:
        """将 LangGraph 消息转换为内部格式

        Args:
            msg: LangGraph 消息对象

        Returns:
            NexusMessage: 统一格式的消息
        """
        from langchain_core.messages import (
            AIMessage,
            HumanMessage,
            SystemMessage,
            ToolMessage,
        )

        # 确定角色
        if isinstance(msg, HumanMessage):
            role = MessageRole.USER
        elif isinstance(msg, AIMessage):
            role = MessageRole.ASSISTANT
        elif isinstance(msg, SystemMessage):
            role = MessageRole.SYSTEM
        elif isinstance(msg, ToolMessage):
            role = MessageRole.TOOL
        else:
            role = MessageRole.USER

        # 提取内容
        content = str(msg.content) if msg.content else ""

        # 提取工具调用
        tool_calls = None
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            tool_calls = [
                {
                    "id": tc.get("id", ""),
                    "name": tc.get("name", ""),
                    "args": tc.get("args", {}),
                }
                for tc in msg.tool_calls
            ]

        # 提取工具调用 ID
        tool_call_id = getattr(msg, "tool_call_id", None)

        return NexusMessage(
            role=role, content=content, tool_calls=tool_calls, tool_call_id=tool_call_id
        )

    def to_framework_message(self, msg: NexusMessage) -> Any:
        """将内部消息转换为 LangGraph 格式

        Args:
            msg: 统一格式的消息

        Returns:
            LangGraph 消息对象
        """
        from langchain_core.messages import (
            AIMessage,
            HumanMessage,
            SystemMessage,
            ToolMessage,
        )

        role_map = {
            MessageRole.USER: HumanMessage,
            MessageRole.ASSISTANT: AIMessage,
            MessageRole.SYSTEM: SystemMessage,
            MessageRole.TOOL: ToolMessage,
        }

        msg_class = role_map.get(msg.role, HumanMessage)

        # 构建消息参数
        msg_kwargs = {"content": msg.content}

        if msg.tool_call_id:
            msg_kwargs["tool_call_id"] = msg.tool_call_id

        return msg_class(**msg_kwargs)
