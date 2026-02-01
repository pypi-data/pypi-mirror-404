"""Base classes for human-in-the-loop interactions.

This module defines the core abstractions for user interactions:
- UserQuestion: Represents a question to ask the user
- UserResponse: Represents the user's response
- InteractionHandler: Abstract interface for interaction implementations
"""

from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel, ConfigDict


class UserQuestion(BaseModel):
    """A question to ask the user.

    Example:
        question = UserQuestion(
            question="Which framework should we use?",
            options=["LangGraph", "Pydantic-AI"],
            allow_free_text=True,
            context={"task": "framework_selection"}
        )
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    question: str
    """The question text to display to the user."""

    options: list[str] | None = None
    """Optional list of predefined options for the user to choose from."""

    allow_free_text: bool = True
    """Whether to allow free-text input in addition to options."""

    default: str | None = None
    """Default value if the user doesn't provide input."""

    timeout: float | None = None
    """Optional timeout in seconds for the response."""

    context: dict[str, Any] | None = None
    """Optional context information for the question."""

    multi_select: bool = False
    """Whether multiple options can be selected."""

    required: bool = True
    """Whether a response is required."""


class UserResponse(BaseModel):
    """User's response to a question.

    Example:
        response = UserResponse(
            answer="LangGraph",
            selected_option=0,
            metadata={"response_time": 2.5}
        )
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    answer: str
    """The user's answer text."""

    selected_option: int | None = None
    """Index of the selected option (if options were provided)."""

    selected_options: list[int] | None = None
    """Indices of selected options (if multi_select was True)."""

    timed_out: bool = False
    """Whether the response timed out."""

    cancelled: bool = False
    """Whether the user cancelled the question."""

    metadata: dict[str, Any] = {}
    """Additional metadata about the response."""


class InteractionHandler(ABC):
    """Abstract handler for user interactions.

    Implementations of this interface handle the actual communication
    with users through different channels (console, GUI, web, etc.).

    Example:
        class MyInteractionHandler(InteractionHandler):
            async def ask_question(self, question: UserQuestion) -> UserResponse:
                # Implementation
                pass

            async def request_confirmation(self, message: str) -> bool:
                # Implementation
                pass
    """

    @abstractmethod
    async def ask_question(self, question: UserQuestion) -> UserResponse:
        """Ask the user a question and wait for response.

        Args:
            question: The question to ask

        Returns:
            The user's response

        Raises:
            InteractionError: If the interaction fails
        """
        pass

    @abstractmethod
    async def request_confirmation(self, message: str, default: bool = False) -> bool:
        """Request user confirmation for an action.

        Args:
            message: The confirmation message to display
            default: Default value if the user just presses Enter

        Returns:
            True if the user confirms, False otherwise

        Raises:
            InteractionError: If the interaction fails
        """
        pass

    async def notify(self, message: str, level: str = "info") -> None:
        """Send a notification to the user.

        This is a one-way communication that doesn't require a response.

        Args:
            message: The message to display
            level: The notification level (info, warning, error, success)
        """
        # Default implementation does nothing
        # Subclasses can override to provide notifications
        pass

    async def show_progress(self, message: str, progress: float | None = None) -> None:
        """Show progress information to the user.

        Args:
            message: The progress message
            progress: Optional progress percentage (0-100)
        """
        # Default implementation does nothing
        # Subclasses can override to show progress
        pass


class InteractionError(Exception):
    """Exception raised for interaction errors."""

    def __init__(self, message: str, recoverable: bool = True):
        """Initialize the error.

        Args:
            message: Error message
            recoverable: Whether the error is recoverable
        """
        super().__init__(message)
        self.recoverable = recoverable
