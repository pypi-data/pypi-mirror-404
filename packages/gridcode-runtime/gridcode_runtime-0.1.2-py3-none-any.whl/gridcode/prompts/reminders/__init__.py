"""System Reminders module for GridCode Runtime.

This module provides a flexible system for context-aware reminders that can be
injected into prompts based on execution state, tool results, and other conditions.

This module uses lazy loading to improve startup time - reminder classes are only
imported when first accessed through the ReminderRegistry.

Usage:
    from gridcode.prompts.reminders import ReminderRegistry, SystemReminder
    from gridcode.prompts.reminders.file_operations import EmptyFileReminder

    registry = ReminderRegistry()
    registry.register(EmptyFileReminder())

    # Get triggered reminders based on context
    reminders = registry.get_triggered_reminders({"file_empty": True})
"""

# Import only the base classes that are always needed
from gridcode.prompts.reminders.base import (
    ReminderRegistry,
    SystemReminder,
    create_default_registry,
)

__all__ = [
    # Base classes
    "SystemReminder",
    "ReminderRegistry",
    "create_default_registry",
    # File operations (lazy-loaded)
    "EmptyFileReminder",
    "TruncatedContentReminder",
    "FileShorterThanOffsetReminder",
    "MalwareAnalysisReminder",
    # Mode status (lazy-loaded)
    "PlanModeReminder",
    "LearningModeReminder",
    "ExitedPlanModeReminder",
    "PlanModeSubagentReminder",
    "SessionContinuationReminder",
    "IterativePlanModeReminder",
    "PlanModeReEntryReminder",
    # Learning mode specific (lazy-loaded)
    "FeedbackRecordedReminder",
    "PatternIdentifiedReminder",
    "ImprovementSuggestionReminder",
    "LearningSessionSummaryReminder",
    "LearningContextReminder",
    # Resource limits (lazy-loaded)
    "TokenUsageReminder",
    "OutputLimitExceededReminder",
    "USDBudgetReminder",
    # Hooks (lazy-loaded)
    "HookSuccessReminder",
    "HookBlockingErrorReminder",
    "HookAdditionalContextReminder",
    # Context (lazy-loaded)
    "GitStatusReminder",
    "WorkingDirectoryReminder",
    "SecurityWarningReminder",
    # Task management (lazy-loaded)
    "TaskStatusReminder",
    "TaskToolsReminder",
    "TodoListChangedReminder",
    "TodoListEmptyReminder",
    "TodoWriteReminder",
    # MCP resources (lazy-loaded)
    "MCPResourceNoContentReminder",
]

# Lazy loading module map - imports occur on first access
_LAZY_MODULES = {
    # File operations
    "EmptyFileReminder": ("gridcode.prompts.reminders.file_operations", "EmptyFileReminder"),
    "TruncatedContentReminder": (
        "gridcode.prompts.reminders.file_operations",
        "TruncatedContentReminder",
    ),
    "FileShorterThanOffsetReminder": (
        "gridcode.prompts.reminders.file_operations",
        "FileShorterThanOffsetReminder",
    ),
    "MalwareAnalysisReminder": (
        "gridcode.prompts.reminders.file_operations",
        "MalwareAnalysisReminder",
    ),
    # Mode status
    "PlanModeReminder": ("gridcode.prompts.reminders.mode_status", "PlanModeReminder"),
    "LearningModeReminder": ("gridcode.prompts.reminders.mode_status", "LearningModeReminder"),
    "ExitedPlanModeReminder": ("gridcode.prompts.reminders.mode_status", "ExitedPlanModeReminder"),
    "PlanModeSubagentReminder": (
        "gridcode.prompts.reminders.mode_status",
        "PlanModeSubagentReminder",
    ),
    "SessionContinuationReminder": (
        "gridcode.prompts.reminders.mode_status",
        "SessionContinuationReminder",
    ),
    "IterativePlanModeReminder": (
        "gridcode.prompts.reminders.mode_status",
        "IterativePlanModeReminder",
    ),
    "PlanModeReEntryReminder": (
        "gridcode.prompts.reminders.mode_status",
        "PlanModeReEntryReminder",
    ),
    # Learning mode specific
    "FeedbackRecordedReminder": (
        "gridcode.prompts.reminders.learning_mode",
        "FeedbackRecordedReminder",
    ),
    "PatternIdentifiedReminder": (
        "gridcode.prompts.reminders.learning_mode",
        "PatternIdentifiedReminder",
    ),
    "ImprovementSuggestionReminder": (
        "gridcode.prompts.reminders.learning_mode",
        "ImprovementSuggestionReminder",
    ),
    "LearningSessionSummaryReminder": (
        "gridcode.prompts.reminders.learning_mode",
        "LearningSessionSummaryReminder",
    ),
    "LearningContextReminder": (
        "gridcode.prompts.reminders.learning_mode",
        "LearningContextReminder",
    ),
    # Resource limits
    "TokenUsageReminder": ("gridcode.prompts.reminders.resource_limits", "TokenUsageReminder"),
    "OutputLimitExceededReminder": (
        "gridcode.prompts.reminders.resource_limits",
        "OutputLimitExceededReminder",
    ),
    "USDBudgetReminder": ("gridcode.prompts.reminders.resource_limits", "USDBudgetReminder"),
    # Hooks
    "HookSuccessReminder": ("gridcode.prompts.reminders.hooks", "HookSuccessReminder"),
    "HookBlockingErrorReminder": ("gridcode.prompts.reminders.hooks", "HookBlockingErrorReminder"),
    "HookAdditionalContextReminder": (
        "gridcode.prompts.reminders.hooks",
        "HookAdditionalContextReminder",
    ),
    # Context
    "GitStatusReminder": ("gridcode.prompts.reminders.context_reminders", "GitStatusReminder"),
    "WorkingDirectoryReminder": (
        "gridcode.prompts.reminders.context_reminders",
        "WorkingDirectoryReminder",
    ),
    "SecurityWarningReminder": (
        "gridcode.prompts.reminders.context_reminders",
        "SecurityWarningReminder",
    ),
    # Task management
    "TaskStatusReminder": ("gridcode.prompts.reminders.task_management", "TaskStatusReminder"),
    "TaskToolsReminder": ("gridcode.prompts.reminders.task_management", "TaskToolsReminder"),
    "TodoListChangedReminder": (
        "gridcode.prompts.reminders.task_management",
        "TodoListChangedReminder",
    ),
    "TodoListEmptyReminder": (
        "gridcode.prompts.reminders.task_management",
        "TodoListEmptyReminder",
    ),
    "TodoWriteReminder": ("gridcode.prompts.reminders.task_management", "TodoWriteReminder"),
    # MCP resources
    "MCPResourceNoContentReminder": (
        "gridcode.prompts.reminders.mcp_resources",
        "MCPResourceNoContentReminder",
    ),
}

# Cache for lazy-loaded modules to avoid repeated imports
_LAZY_CACHE = {}


def __getattr__(name: str):
    """Lazy load reminder classes on first access."""
    if name in _LAZY_MODULES:
        if name not in _LAZY_CACHE:
            module_name, class_name = _LAZY_MODULES[name]
            module = __import__(module_name, fromlist=[class_name])
            _LAZY_CACHE[name] = getattr(module, class_name)
        return _LAZY_CACHE[name]
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
