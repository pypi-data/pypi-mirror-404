"""Task management reminders.

Reminders about task tracking and progress:
- Task status updates
- Task tools usage hints
- TODO list management
"""

import json
from typing import Any

from gridcode.prompts.reminders.base import SystemReminder


class TaskStatusReminder(SystemReminder):
    """Reminder about task output availability."""

    name: str = "task_status"
    priority: int = 6  # Medium priority - informational

    def should_trigger(self, context: dict[str, Any]) -> bool:
        """Trigger when a background task is running."""
        return context.get("has_background_task", False)

    def render(self, context: dict[str, Any]) -> str:
        """Render task status reminder."""
        return """<system-reminder>
You can check its output using the TaskOutput tool.
</system-reminder>"""


class TaskToolsReminder(SystemReminder):
    """Reminder to use task tracking tools."""

    name: str = "task_tools_reminder"
    priority: int = 4  # Low priority - gentle reminder

    def should_trigger(self, context: dict[str, Any]) -> bool:
        """Trigger when task tools haven't been used recently."""
        return context.get("task_tools_inactive", False)

    def render(self, context: dict[str, Any]) -> str:
        """Render task tools reminder."""
        return """<system-reminder>
The task tools haven't been used recently. If you're working on tasks that would benefit from tracking progress, consider using TaskCreate to add new tasks and TaskUpdate to update task status (set to in_progress when starting, completed when done). Also consider cleaning up the task list if it has become stale. Only use these if relevant to the current work. This is just a gentle reminder - ignore if not applicable. Make sure that you NEVER mention this reminder to the user
</system-reminder>"""  # noqa: E501


class TodoListChangedReminder(SystemReminder):
    """Reminder when todo list has changed."""

    name: str = "todo_list_changed"
    priority: int = 5  # Medium priority - informational

    def should_trigger(self, context: dict[str, Any]) -> bool:
        """Trigger when todo_list_changed is True."""
        return context.get("todo_list_changed", False)

    def render(self, context: dict[str, Any]) -> str:
        """Render todo list changed reminder."""
        todo_content = context.get("todo_content", [])
        try:
            content_str = json.dumps(todo_content, indent=2)
        except (TypeError, ValueError):
            content_str = str(todo_content)

        return f"""<system-reminder>
Your todo list has changed. DO NOT mention this explicitly to the user. Here are the latest contents of your todo list:

{content_str}

Continue on with the tasks at hand if applicable.
</system-reminder>"""  # noqa: E501


class TodoListEmptyReminder(SystemReminder):
    """Reminder when todo list is empty."""

    name: str = "todo_list_empty"
    priority: int = 3  # Low priority - gentle reminder

    def should_trigger(self, context: dict[str, Any]) -> bool:
        """Trigger when todo_list_empty is True."""
        return context.get("todo_list_empty", False)

    def render(self, context: dict[str, Any]) -> str:
        """Render todo list empty reminder."""
        return """<system-reminder>
This is a reminder that your todo list is currently empty. DO NOT mention this to the user explicitly because they are already aware. If you are working on tasks that would benefit from a todo list please use the TodoWrite tool to create one. If not, please feel free to ignore. Again do not mention this message to the user.
</system-reminder>"""  # noqa: E501


class TodoWriteReminder(SystemReminder):
    """Reminder to use TodoWrite tool for task tracking."""

    name: str = "todowrite_reminder"
    priority: int = 3  # Low priority - gentle reminder

    def should_trigger(self, context: dict[str, Any]) -> bool:
        """Trigger when todowrite_inactive is True."""
        return context.get("todowrite_inactive", False)

    def render(self, context: dict[str, Any]) -> str:
        """Render TodoWrite reminder."""
        return """<system-reminder>
The TodoWrite tool hasn't been used recently. If you're working on tasks that would benefit from tracking progress, consider using the TodoWrite tool to track progress. Also consider cleaning up the todo list if has become stale and no longer matches what you are working on. Only use it if it's relevant to the current work. This is just a gentle reminder - ignore if not applicable. Make sure that you NEVER mention this reminder to the user
</system-reminder>"""  # noqa: E501
