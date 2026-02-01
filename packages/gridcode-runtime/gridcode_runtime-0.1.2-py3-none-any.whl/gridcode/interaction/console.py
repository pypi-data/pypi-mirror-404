"""Console-based interaction handler.

This module provides a simple console-based implementation of
InteractionHandler for CLI applications.
"""

import asyncio

from loguru import logger

from gridcode.interaction.base import (
    InteractionError,
    InteractionHandler,
    UserQuestion,
    UserResponse,
)


class ConsoleInteractionHandler(InteractionHandler):
    """Console-based interaction handler.

    This handler uses standard input/output for user interactions,
    suitable for CLI applications.

    Example:
        handler = ConsoleInteractionHandler()

        response = await handler.ask_question(
            UserQuestion(
                question="Which framework?",
                options=["LangGraph", "Pydantic-AI"]
            )
        )
        print(f"You selected: {response.answer}")
    """

    def __init__(self, prompt_prefix: str = "> "):
        """Initialize the console handler.

        Args:
            prompt_prefix: Prefix for input prompts
        """
        self.prompt_prefix = prompt_prefix

    async def ask_question(self, question: UserQuestion) -> UserResponse:
        """Ask the user a question via console.

        Args:
            question: The question to ask

        Returns:
            The user's response
        """
        try:
            # Display the question
            print(f"\n{question.question}")

            # Display options if provided
            if question.options:
                for i, opt in enumerate(question.options, 1):
                    print(f"  {i}. {opt}")

                if question.allow_free_text:
                    print("  (or enter your own response)")

            # Get input with timeout if specified
            if question.timeout:
                answer = await self._get_input_with_timeout(
                    self.prompt_prefix,
                    question.timeout,
                    question.default,
                )
            else:
                answer = await self._get_input(self.prompt_prefix, question.default)

            # Handle timed out or cancelled
            if answer is None:
                if not question.required:
                    return UserResponse(
                        answer="",
                        timed_out=question.timeout is not None,
                        cancelled=question.timeout is None,
                    )
                raise InteractionError("No response provided and question is required")

            # Parse option selection
            selected_option = None
            selected_options = None

            if question.options:
                # Try to parse as option number
                try:
                    option_num = int(answer.strip())
                    if 1 <= option_num <= len(question.options):
                        selected_option = option_num - 1
                        answer = question.options[selected_option]
                except ValueError:
                    # Not a number, use as free text
                    pass

            logger.debug(f"User response: {answer}")

            return UserResponse(
                answer=answer,
                selected_option=selected_option,
                selected_options=selected_options,
            )

        except KeyboardInterrupt:
            return UserResponse(answer="", cancelled=True)
        except Exception as e:
            logger.error(f"Error getting user input: {e}")
            raise InteractionError(f"Failed to get user input: {e}")

    async def request_confirmation(self, message: str, default: bool = False) -> bool:
        """Request user confirmation via console.

        Args:
            message: The confirmation message
            default: Default value if user presses Enter

        Returns:
            True if confirmed, False otherwise
        """
        try:
            default_hint = "[Y/n]" if default else "[y/N]"
            print(f"\n{message} {default_hint}")

            answer = await self._get_input(self.prompt_prefix, "")

            if not answer:
                return default

            return answer.lower() in ("y", "yes")

        except KeyboardInterrupt:
            return False
        except Exception as e:
            logger.error(f"Error getting confirmation: {e}")
            raise InteractionError(f"Failed to get confirmation: {e}")

    async def notify(self, message: str, level: str = "info") -> None:
        """Display a notification to the console.

        Args:
            message: The message to display
            level: The notification level
        """
        prefixes = {
            "info": "[INFO]",
            "warning": "[WARNING]",
            "error": "[ERROR]",
            "success": "[SUCCESS]",
        }
        prefix = prefixes.get(level, "[INFO]")
        print(f"{prefix} {message}")

    async def show_progress(self, message: str, progress: float | None = None) -> None:
        """Show progress information.

        Args:
            message: The progress message
            progress: Optional progress percentage
        """
        if progress is not None:
            print(f"[{progress:.1f}%] {message}")
        else:
            print(f"[...] {message}")

    async def _get_input(self, prompt: str, default: str | None) -> str | None:
        """Get input from the user.

        Args:
            prompt: The input prompt
            default: Default value if empty input

        Returns:
            The user's input or default
        """
        # Run input() in a thread pool to not block the event loop
        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(None, input, prompt)
            return result if result else default
        except EOFError:
            return default

    async def _get_input_with_timeout(
        self,
        prompt: str,
        timeout: float,
        default: str | None,
    ) -> str | None:
        """Get input with a timeout.

        Args:
            prompt: The input prompt
            timeout: Timeout in seconds
            default: Default value on timeout

        Returns:
            The user's input, default on timeout, or None on error
        """
        try:
            return await asyncio.wait_for(
                self._get_input(prompt, None),
                timeout=timeout,
            )
        except TimeoutError:
            print(f"\n(Timed out, using default: {default})")
            return default
