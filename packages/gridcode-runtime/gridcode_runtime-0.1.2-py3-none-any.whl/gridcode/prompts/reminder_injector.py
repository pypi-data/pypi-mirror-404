"""System Reminder Injector for GridCode Runtime.

This module provides functionality to inject context-aware system reminders
into prompts based on execution state, tool results, and other conditions.
"""

from enum import Enum
from pathlib import Path
from typing import Any

from .composer import PromptComposer


class ReminderType(Enum):
    """Types of system reminders."""

    # State reminders
    PLAN_MODE_ACTIVE = "plan-mode-active"
    LEARNING_MODE_ACTIVE = "learning-mode-active"

    # File operation reminders
    FILE_EMPTY = "file-exists-but-empty"
    FILE_TRUNCATED = "file-truncated"
    FILE_SHORTER_THAN_OFFSET = "file-shorter-than-offset"
    MALWARE_ANALYSIS = "malware-analysis-after-read"

    # Resource reminders
    TOKEN_USAGE = "token-usage"
    OUTPUT_LIMIT_EXCEEDED = "output-limit-exceeded"

    # Hook reminders
    HOOK_SUCCESS = "hook-success"
    HOOK_BLOCKING_ERROR = "hook-blocking-error"


class SystemReminderInjector:
    """Injects system reminders based on execution context."""

    def __init__(self, templates_dir: Path | None = None):
        """Initialize the reminder injector.

        Args:
            templates_dir: Directory containing reminder templates.
                          Defaults to prompts/templates/reminders/
        """
        if templates_dir is None:
            templates_dir = Path(__file__).parent / "templates" / "reminders"

        self.templates_dir = templates_dir
        self.composer = PromptComposer(templates_dir)
        self._reminder_cache: dict[ReminderType, str] = {}

    def inject_reminder(
        self, reminder_type: ReminderType, context: dict[str, Any] | None = None
    ) -> str:
        """Inject a system reminder.

        Args:
            reminder_type: Type of reminder to inject
            context: Optional context variables for the reminder

        Returns:
            Formatted system reminder wrapped in <system-reminder> tags
        """
        # Load reminder template (composer will add .md suffix)
        template_name = reminder_type.value

        # Compose reminder with context variables as static_vars
        # (reminder templates use ${VAR} syntax, not ${context.VAR})
        reminder_content = self.composer.compose(
            template_names=[template_name], static_vars=context or {}
        )

        # Wrap in system-reminder tags
        return f"<system-reminder>\n{reminder_content}\n</system-reminder>"

    def should_inject_file_empty_reminder(self, file_content: str) -> bool:
        """Check if file empty reminder should be injected.

        Args:
            file_content: Content of the file that was read

        Returns:
            True if file is empty and reminder should be shown
        """
        return len(file_content.strip()) == 0

    def should_inject_token_usage_reminder(
        self, tokens_used: int, token_limit: int, threshold: float = 0.8
    ) -> bool:
        """Check if token usage reminder should be injected.

        Args:
            tokens_used: Number of tokens used so far
            token_limit: Maximum token limit
            threshold: Threshold ratio to trigger reminder (default 0.8 = 80%)

        Returns:
            True if token usage exceeds threshold
        """
        return tokens_used / token_limit >= threshold

    def should_inject_file_shorter_reminder(self, start_line: int, total_lines: int) -> bool:
        """Check if file shorter than offset reminder should be injected.

        Args:
            start_line: The requested starting line number
            total_lines: Total lines in the file

        Returns:
            True if start_line exceeds total_lines
        """
        return start_line > total_lines
