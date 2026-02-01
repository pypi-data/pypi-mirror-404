"""Nexus Engine 适配器基类

定义所有框架适配器必须实现的接口。
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any

from .types import NexusAgentResult, NexusAgentState, NexusMessage


class BaseFrameworkAdapter(ABC):
    """框架适配器抽象基类

    定义所有框架适配器必须实现的接口，用于将不同的 AI 框架
    （如 LangGraph, Pydantic-AI）适配为统一的 Nexus 接口。
    """

    @abstractmethod
    async def execute(
        self,
        prompt: str,
        state: NexusAgentState | None = None,
        **kwargs: Any,
    ) -> NexusAgentResult:
        """执行 Agent 并返回结果

        Args:
            prompt: 用户输入提示
            state: 可选的初始状态（包含消息历史等）
            **kwargs: 框架特定的参数

        Returns:
            NexusAgentResult: 执行结果

        Raises:
            Exception: 执行失败时抛出异常
        """
        pass

    @abstractmethod
    async def execute_stream(
        self,
        prompt: str,
        state: NexusAgentState | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[NexusMessage | NexusAgentResult]:
        """流式执行 Agent

        Args:
            prompt: 用户输入提示
            state: 可选的初始状态
            **kwargs: 框架特定的参数

        Yields:
            NexusMessage: 中间消息
            NexusAgentResult: 最终结果

        Raises:
            Exception: 执行失败时抛出异常
        """
        pass

    @abstractmethod
    def to_internal_message(self, msg: Any) -> NexusMessage:
        """将框架特定的消息转换为内部格式

        Args:
            msg: 框架特定的消息对象

        Returns:
            NexusMessage: 统一格式的消息
        """
        pass

    @abstractmethod
    def to_framework_message(self, msg: NexusMessage) -> Any:
        """将内部消息转换为框架特定格式

        Args:
            msg: 统一格式的消息

        Returns:
            框架特定的消息对象
        """
        pass
