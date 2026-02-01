"""Tool Result Enhancer for GridCode Runtime.

This module enhances tool execution results by injecting context-aware system reminders
based on the tool type, result content, and execution context.

Design Pattern (from Claude Code):
- Tool results are analyzed after execution
- System reminders are dynamically injected based on conditions
- Reminders are wrapped in <system-reminder> tags
- Multiple reminders can be injected for a single tool result
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any

from .reminder_injector import ReminderType, SystemReminderInjector


class ToolType(Enum):
    """Types of tools that can have enhanced results."""

    READ = "read"
    WRITE = "write"
    EDIT = "edit"
    GLOB = "glob"
    GREP = "grep"
    BASH = "bash"
    TASK = "task"


@dataclass
class ToolResult:
    """Represents a tool execution result."""

    tool_type: ToolType
    success: bool
    content: str
    metadata: dict[str, Any]
    error: str | None = None


@dataclass
class EnhancedToolResult:
    """Tool result with injected system reminders."""

    original_result: ToolResult
    enhanced_content: str
    injected_reminders: list[str]


class ToolResultEnhancer:
    """Enhances tool results with context-aware system reminders.

    This class analyzes tool execution results and injects appropriate
    system reminders based on the tool type, result content, and execution context.

    Example:
        >>> enhancer = ToolResultEnhancer()
        >>> result = ToolResult(
        ...     tool_type=ToolType.READ,
        ...     success=True,
        ...     content="",
        ...     metadata={"file_path": "/path/to/file.txt"}
        ... )
        >>> enhanced = enhancer.enhance(result)
        >>> print(enhanced.enhanced_content)
        <system-reminder>Warning: the file exists but the contents are empty.</system-reminder>
    """

    def __init__(self, reminder_injector: SystemReminderInjector | None = None):
        """Initialize the tool result enhancer.

        Args:
            reminder_injector: Optional SystemReminderInjector instance.
                             If not provided, a new one will be created.
        """
        self.reminder_injector = reminder_injector or SystemReminderInjector()

    def enhance(
        self, result: ToolResult, context: dict[str, Any] | None = None
    ) -> EnhancedToolResult:
        """Enhance a tool result with system reminders.

        Args:
            result: The tool execution result to enhance
            context: Optional execution context for reminder injection

        Returns:
            Enhanced tool result with injected reminders
        """
        context = context or {}
        reminders: list[str] = []

        # Analyze result and collect applicable reminders
        if result.tool_type == ToolType.READ:
            reminders.extend(self._analyze_read_result(result, context))
        elif result.tool_type == ToolType.WRITE:
            reminders.extend(self._analyze_write_result(result, context))
        elif result.tool_type == ToolType.EDIT:
            reminders.extend(self._analyze_edit_result(result, context))

        # Build enhanced content
        enhanced_content = self._build_enhanced_content(result, reminders)

        return EnhancedToolResult(
            original_result=result, enhanced_content=enhanced_content, injected_reminders=reminders
        )

    def _analyze_read_result(self, result: ToolResult, context: dict[str, Any]) -> list[str]:
        """Analyze Read tool result and return applicable reminders.

        Args:
            result: Read tool execution result
            context: Execution context

        Returns:
            List of reminder strings to inject
        """
        reminders = []

        # Check for empty file
        if result.success and self.reminder_injector.should_inject_file_empty_reminder(
            result.content
        ):
            reminder = self.reminder_injector.inject_reminder(ReminderType.FILE_EMPTY, context)
            reminders.append(reminder)

        # Check for file truncation
        if result.metadata.get("truncated", False):
            reminder_context = {
                "filename": result.metadata.get("file_path", "unknown"),
                "max_lines": str(
                    result.metadata.get("shown_lines", result.metadata.get("lines_read", 0))
                ),
                "read_tool_name": "Read",
            }
            reminder = self.reminder_injector.inject_reminder(
                ReminderType.FILE_TRUNCATED, {**context, **reminder_context}
            )
            reminders.append(reminder)

        # Always inject malware analysis reminder after reading files
        reminder = self.reminder_injector.inject_reminder(ReminderType.MALWARE_ANALYSIS, context)
        reminders.append(reminder)

        return reminders

    def _analyze_write_result(self, result: ToolResult, context: dict[str, Any]) -> list[str]:
        """Analyze Write tool result and return applicable reminders.

        Args:
            result: Write tool execution result
            context: Execution context

        Returns:
            List of reminder strings to inject
        """
        reminders = []
        # Write tool typically doesn't need reminders in Phase 1
        # Future: Add reminders for file permissions, disk space, etc.
        return reminders

    def _analyze_edit_result(self, result: ToolResult, context: dict[str, Any]) -> list[str]:
        """Analyze Edit tool result and return applicable reminders.

        Args:
            result: Edit tool execution result
            context: Execution context

        Returns:
            List of reminder strings to inject
        """
        reminders = []
        # Edit tool typically doesn't need reminders in Phase 1
        # Future: Add reminders for edit conflicts, formatting issues, etc.
        return reminders

    def _build_enhanced_content(self, result: ToolResult, reminders: list[str]) -> str:
        """Build enhanced content by combining original result with reminders.

        Args:
            result: Original tool result
            reminders: List of reminder strings to inject

        Returns:
            Enhanced content string with reminders appended
        """
        parts = []

        # Add original content if present
        if result.content:
            parts.append(result.content)

        # Add error message if present
        if result.error:
            parts.append(f"Error: {result.error}")

        # Add all reminders
        parts.extend(reminders)

        return "\n".join(parts)
