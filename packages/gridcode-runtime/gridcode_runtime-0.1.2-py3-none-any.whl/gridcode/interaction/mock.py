"""Mock interaction handler for testing.

This module provides a programmable mock handler for unit tests,
allowing tests to run without actual user input.
"""

from gridcode.interaction.base import (
    InteractionError,
    InteractionHandler,
    UserQuestion,
    UserResponse,
)


class MockInteractionHandler(InteractionHandler):
    """Mock interaction handler for testing.

    This handler allows pre-programming responses for testing
    without requiring actual user input.

    Example:
        handler = MockInteractionHandler()
        handler.add_response("test answer")
        handler.add_confirmation(True)

        response = await handler.ask_question(
            UserQuestion(question="Test question?")
        )
        assert response.answer == "test answer"
    """

    def __init__(self):
        """Initialize the mock handler."""
        self._responses: list[UserResponse | str] = []
        self._confirmations: list[bool] = []
        self._notifications: list[tuple[str, str]] = []
        self._progress: list[tuple[str, float | None]] = []
        self._questions_asked: list[UserQuestion] = []
        self._confirmations_requested: list[str] = []

    def add_response(
        self,
        answer: str | UserResponse,
        selected_option: int | None = None,
    ) -> None:
        """Add a response to return for the next ask_question call.

        Args:
            answer: The answer string or full UserResponse
            selected_option: Optional selected option index
        """
        if isinstance(answer, str):
            response = UserResponse(answer=answer, selected_option=selected_option)
        else:
            response = answer
        self._responses.append(response)

    def add_confirmation(self, confirm: bool) -> None:
        """Add a confirmation response for the next request_confirmation call.

        Args:
            confirm: Whether to confirm
        """
        self._confirmations.append(confirm)

    async def ask_question(self, question: UserQuestion) -> UserResponse:
        """Return the next pre-programmed response.

        Args:
            question: The question (stored for verification)

        Returns:
            The next pre-programmed response

        Raises:
            InteractionError: If no response is available
        """
        self._questions_asked.append(question)

        if not self._responses:
            raise InteractionError("No mock response available")

        response = self._responses.pop(0)
        if isinstance(response, str):
            return UserResponse(answer=response)
        return response

    async def request_confirmation(self, message: str, default: bool = False) -> bool:
        """Return the next pre-programmed confirmation.

        Args:
            message: The confirmation message (stored for verification)
            default: Default value if no confirmation programmed

        Returns:
            The next pre-programmed confirmation or default
        """
        self._confirmations_requested.append(message)

        if not self._confirmations:
            return default

        return self._confirmations.pop(0)

    async def notify(self, message: str, level: str = "info") -> None:
        """Store the notification for verification.

        Args:
            message: The notification message
            level: The notification level
        """
        self._notifications.append((message, level))

    async def show_progress(self, message: str, progress: float | None = None) -> None:
        """Store the progress for verification.

        Args:
            message: The progress message
            progress: The progress percentage
        """
        self._progress.append((message, progress))

    # Verification methods

    @property
    def questions_asked(self) -> list[UserQuestion]:
        """Get all questions that were asked."""
        return self._questions_asked

    @property
    def confirmations_requested(self) -> list[str]:
        """Get all confirmation messages that were requested."""
        return self._confirmations_requested

    @property
    def notifications_sent(self) -> list[tuple[str, str]]:
        """Get all notifications that were sent."""
        return self._notifications

    @property
    def progress_updates(self) -> list[tuple[str, float | None]]:
        """Get all progress updates that were shown."""
        return self._progress

    def reset(self) -> None:
        """Reset all state for a fresh test."""
        self._responses.clear()
        self._confirmations.clear()
        self._notifications.clear()
        self._progress.clear()
        self._questions_asked.clear()
        self._confirmations_requested.clear()

    def verify_question_asked(self, question_text: str) -> bool:
        """Verify that a specific question was asked.

        Args:
            question_text: The question text to look for

        Returns:
            True if the question was asked
        """
        return any(q.question == question_text for q in self._questions_asked)

    def verify_confirmation_requested(self, message: str) -> bool:
        """Verify that a specific confirmation was requested.

        Args:
            message: The message to look for

        Returns:
            True if the confirmation was requested
        """
        return message in self._confirmations_requested
