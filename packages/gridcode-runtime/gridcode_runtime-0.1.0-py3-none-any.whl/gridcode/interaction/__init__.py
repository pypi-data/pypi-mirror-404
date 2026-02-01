"""Interaction module for GridCode Runtime.

This module provides interfaces for human-in-the-loop interactions,
allowing agents to ask questions and request confirmations from users.

Usage:
    from gridcode.interaction import ConsoleInteractionHandler, UserQuestion

    handler = ConsoleInteractionHandler()
    response = await handler.ask_question(
        UserQuestion(question="Which framework?", options=["LangGraph", "Pydantic-AI"])
    )
"""

from gridcode.interaction.base import (
    InteractionError,
    InteractionHandler,
    UserQuestion,
    UserResponse,
)
from gridcode.interaction.console import ConsoleInteractionHandler
from gridcode.interaction.mock import MockInteractionHandler

__all__ = [
    "InteractionHandler",
    "UserQuestion",
    "UserResponse",
    "InteractionError",
    "ConsoleInteractionHandler",
    "MockInteractionHandler",
]
