"""Nexus Agent Engine - 框架无关的智能体执行抽象

Nexus Engine 提供统一的接口来执行不同框架（LangGraph, Pydantic-AI）的智能体。
通过 Strategy + Adapter 模式实现框架解耦。
"""

from .base import BaseFrameworkAdapter
from .langgraph import LangGraphAdapter
from .pydantic_ai import (
    PydanticAIAdapter,
    convert_to_pydantic_ai_tool,
    convert_tools_to_pydantic_ai,
)
from .tool_converter import (
    convert_to_langgraph_tool,
    convert_tools_to_langgraph,
)
from .types import (
    MessageRole,
    NexusAgentResult,
    NexusAgentState,
    NexusMessage,
)

__all__ = [
    "BaseFrameworkAdapter",
    "LangGraphAdapter",
    "PydanticAIAdapter",
    "MessageRole",
    "NexusMessage",
    "NexusAgentState",
    "NexusAgentResult",
    "convert_to_langgraph_tool",
    "convert_tools_to_langgraph",
    "convert_to_pydantic_ai_tool",
    "convert_tools_to_pydantic_ai",
]
