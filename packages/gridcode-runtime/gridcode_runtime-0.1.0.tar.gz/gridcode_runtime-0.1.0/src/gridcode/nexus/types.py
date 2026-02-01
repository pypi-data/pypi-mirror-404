"""Nexus Engine 统一类型定义

定义框架无关的消息、状态和结果类型。
"""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """消息角色枚举"""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class NexusMessage(BaseModel):
    """统一消息抽象

    用于在不同框架之间传递消息，提供框架无关的消息表示。

    Attributes:
        role: 消息角色（user, assistant, system, tool）
        content: 消息内容
        tool_calls: 工具调用列表（如果有）
        tool_call_id: 工具调用 ID（用于工具响应）
        metadata: 额外的元数据
    """

    role: MessageRole
    content: str
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class NexusAgentState(BaseModel):
    """统一 Agent 状态

    封装 Agent 执行过程中的状态信息。

    Attributes:
        messages: 消息历史
        custom_state: 自定义状态数据
        metadata: 额外的元数据
    """

    messages: list[NexusMessage] = Field(default_factory=list)
    custom_state: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class NexusAgentResult(BaseModel):
    """统一 Agent 执行结果

    封装 Agent 执行的最终结果。

    Attributes:
        output: 最终输出内容
        messages: 完整的消息历史
        usage: Token 使用统计（如果有）
        metadata: 额外的元数据
    """

    output: str
    messages: list[NexusMessage] = Field(default_factory=list)
    usage: dict[str, int] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
