"""Base classes for System Reminders.

This module defines the core abstractions for the reminder system:
- SystemReminder: Abstract base class for all reminders
- ReminderRegistry: Central registry for managing and triggering reminders
"""

from abc import ABC, abstractmethod
from typing import Any

from loguru import logger
from pydantic import BaseModel, ConfigDict


class SystemReminder(BaseModel, ABC):
    """Abstract base class for system reminders.

    Each reminder defines:
    - name: Unique identifier for the reminder
    - priority: Higher values = more important (determines render order)
    - should_trigger(): Checks if the reminder should be activated
    - render(): Generates the reminder content

    Example:
        class EmptyFileReminder(SystemReminder):
            name: str = "empty_file"
            priority: int = 10

            def should_trigger(self, context: dict) -> bool:
                return context.get("file_empty", False)

            def render(self, context: dict) -> str:
                return "<system-reminder>The file exists but is empty.</system-reminder>"
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    name: str
    priority: int = 0

    @abstractmethod
    def should_trigger(self, context: dict[str, Any]) -> bool:
        """Check if this reminder should be triggered based on context.

        Args:
            context: Dictionary containing execution context information

        Returns:
            True if the reminder should be shown
        """
        pass

    @abstractmethod
    def render(self, context: dict[str, Any]) -> str:
        """Render the reminder content.

        Args:
            context: Dictionary containing execution context information

        Returns:
            Formatted reminder string (should include <system-reminder> tags)
        """
        pass

    def __hash__(self) -> int:
        return hash(self.name)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, SystemReminder):
            return self.name == other.name
        return False


class ReminderRegistry:
    """Registry for managing and triggering system reminders.

    The registry maintains a sorted list of reminders by priority.
    Higher priority reminders are rendered first.

    Example:
        registry = ReminderRegistry()
        registry.register(EmptyFileReminder())
        registry.register(PlanModeReminder())

        # Get all triggered reminders
        reminders = registry.get_triggered_reminders({"file_empty": True})
    """

    def __init__(self) -> None:
        """Initialize an empty reminder registry."""
        self._reminders: list[SystemReminder] = []
        self._reminder_map: dict[str, SystemReminder] = {}

    def register(self, reminder: SystemReminder) -> None:
        """Register a new reminder.

        Args:
            reminder: SystemReminder instance to register

        Note:
            If a reminder with the same name already exists, it will be replaced.
        """
        # Remove existing reminder with same name if present
        if reminder.name in self._reminder_map:
            old = self._reminder_map[reminder.name]
            self._reminders.remove(old)
            logger.debug(f"Replacing existing reminder: {reminder.name}")

        self._reminders.append(reminder)
        self._reminder_map[reminder.name] = reminder
        # Sort by priority (descending)
        self._reminders.sort(key=lambda r: r.priority, reverse=True)
        logger.debug(f"Registered reminder: {reminder.name} (priority={reminder.priority})")

    def unregister(self, name: str) -> bool:
        """Unregister a reminder by name.

        Args:
            name: Name of the reminder to remove

        Returns:
            True if the reminder was found and removed
        """
        if name in self._reminder_map:
            reminder = self._reminder_map.pop(name)
            self._reminders.remove(reminder)
            logger.debug(f"Unregistered reminder: {name}")
            return True
        return False

    def get(self, name: str) -> SystemReminder | None:
        """Get a reminder by name.

        Args:
            name: Name of the reminder

        Returns:
            The reminder if found, None otherwise
        """
        return self._reminder_map.get(name)

    def get_triggered_reminders(self, context: dict[str, Any]) -> list[str]:
        """Get all reminders that should trigger for the given context.

        Args:
            context: Dictionary containing execution context

        Returns:
            List of rendered reminder strings (sorted by priority)
        """
        triggered = []
        for reminder in self._reminders:
            try:
                if reminder.should_trigger(context):
                    content = reminder.render(context)
                    triggered.append(content)
                    logger.debug(f"Reminder triggered: {reminder.name}")
            except Exception as e:
                logger.error(f"Error checking reminder {reminder.name}: {e}")
        return triggered

    def get_triggered_reminder_names(self, context: dict[str, Any]) -> list[str]:
        """Get names of all reminders that would trigger.

        Args:
            context: Dictionary containing execution context

        Returns:
            List of reminder names that would trigger
        """
        names = []
        for reminder in self._reminders:
            try:
                if reminder.should_trigger(context):
                    names.append(reminder.name)
            except Exception as e:
                logger.error(f"Error checking reminder {reminder.name}: {e}")
        return names

    def list_reminders(self) -> list[str]:
        """List all registered reminder names.

        Returns:
            List of reminder names (sorted by priority)
        """
        return [r.name for r in self._reminders]

    def __len__(self) -> int:
        return len(self._reminders)

    def __contains__(self, name: str) -> bool:
        return name in self._reminder_map


def create_default_registry() -> ReminderRegistry:
    """Create a registry with all default reminders.

    Returns:
        ReminderRegistry populated with standard reminders
    """
    from gridcode.prompts.reminders.context_reminders import (
        GitStatusReminder,
        SecurityWarningReminder,
        WorkingDirectoryReminder,
    )
    from gridcode.prompts.reminders.file_operations import (
        EmptyFileReminder,
        FileOpenedInIDEReminder,
        FileShorterThanOffsetReminder,
        MalwareAnalysisReminder,
        TruncatedContentReminder,
    )
    from gridcode.prompts.reminders.git_operations import (
        GitModifiedByUserReminder,
        GitRepoDirtyReminder,
    )
    from gridcode.prompts.reminders.hooks import (
        HookAdditionalContextReminder,
        HookBlockingErrorReminder,
        HookStoppedContinuationReminder,
        HookSuccessReminder,
    )
    from gridcode.prompts.reminders.learning_mode import (
        FeedbackRecordedReminder,
        ImprovementSuggestionReminder,
        LearningContextReminder,
        LearningSessionSummaryReminder,
        PatternIdentifiedReminder,
    )
    from gridcode.prompts.reminders.mcp_resources import (
        MCPResourceNoContentReminder,
        MCPResourceNoDisplayableContentReminder,
    )
    from gridcode.prompts.reminders.mode_status import (
        DelegateModeReminder,
        ExitedDelegateModeReminder,
        ExitedPlanModeReminder,
        IterativePlanModeReminder,
        LearningModeReminder,
        PlanModeReEntryReminder,
        PlanModeReminder,
        PlanModeSubagentReminder,
        SessionContinuationReminder,
    )
    from gridcode.prompts.reminders.permissions import (
        BashPermissionDeniedReminder,
        EditPermissionDeniedReminder,
        WritePermissionDeniedReminder,
    )
    from gridcode.prompts.reminders.resource_limits import (
        BudgetHardLimitReminder,
        BudgetSoftLimitReminder,
        OutputLimitExceededReminder,
        TokenUsageReminder,
        USDBudgetReminder,
    )
    from gridcode.prompts.reminders.task_management import (
        TaskStatusReminder,
        TaskToolsReminder,
        TodoListChangedReminder,
        TodoListEmptyReminder,
        TodoWriteReminder,
    )

    registry = ReminderRegistry()

    # File operations (priority 6-10)
    registry.register(EmptyFileReminder())
    registry.register(TruncatedContentReminder())
    registry.register(FileShorterThanOffsetReminder())
    registry.register(MalwareAnalysisReminder())
    registry.register(FileOpenedInIDEReminder())  # NEW

    # Mode status (priority 13-15)
    registry.register(PlanModeReminder())
    registry.register(LearningModeReminder())
    registry.register(ExitedPlanModeReminder())
    registry.register(PlanModeSubagentReminder())
    registry.register(SessionContinuationReminder())
    registry.register(IterativePlanModeReminder())
    registry.register(PlanModeReEntryReminder())
    registry.register(DelegateModeReminder())  # NEW
    registry.register(ExitedDelegateModeReminder())  # NEW

    # Learning mode specific (priority 7-12)
    registry.register(FeedbackRecordedReminder())
    registry.register(PatternIdentifiedReminder())
    registry.register(ImprovementSuggestionReminder())
    registry.register(LearningSessionSummaryReminder())
    registry.register(LearningContextReminder())

    # Resource limits (priority 11-13)
    registry.register(TokenUsageReminder())
    registry.register(OutputLimitExceededReminder())
    registry.register(USDBudgetReminder())
    registry.register(BudgetSoftLimitReminder())  # NEW
    registry.register(BudgetHardLimitReminder())  # NEW

    # Hooks (priority 5-14)
    registry.register(HookSuccessReminder())
    registry.register(HookBlockingErrorReminder())
    registry.register(HookAdditionalContextReminder())
    registry.register(HookStoppedContinuationReminder())  # NEW

    # Task management (priority 3-6)
    registry.register(TaskStatusReminder())
    registry.register(TaskToolsReminder())
    registry.register(TodoListChangedReminder())
    registry.register(TodoListEmptyReminder())
    registry.register(TodoWriteReminder())

    # MCP resources (priority 7)
    registry.register(MCPResourceNoContentReminder())
    registry.register(MCPResourceNoDisplayableContentReminder())  # NEW

    # Git operations (priority 10-13)
    registry.register(GitModifiedByUserReminder())  # NEW
    registry.register(GitRepoDirtyReminder())  # NEW

    # Context (priority 3)
    registry.register(GitStatusReminder())
    registry.register(WorkingDirectoryReminder())

    # Permissions (priority 14)
    registry.register(BashPermissionDeniedReminder())  # NEW
    registry.register(EditPermissionDeniedReminder())  # NEW
    registry.register(WritePermissionDeniedReminder())  # NEW

    # Security (priority 16)
    registry.register(SecurityWarningReminder())

    return registry
